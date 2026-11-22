/*
 * natives.c - the native library (HAL-3): the catalog APIs as NATIVE n executes them (vm/bytecode.md section 5).
 *
 * A port of the prototype src/cardlang/pyvm/natives.py, check for check, so that both give identical outcomes. It does
 * no cryptography (HAL-1): it takes the arguments off the operand stack (BC-34), resolves identifiers in the single
 * identifier space (PLT-20), keeps the operation table with its lifetimes (BP-14, BP-31), applies the profile's
 * checks in the error precedence of BP-8, and hands views to the HAL as descriptors (HAL-11, HAL-12). CBOR, BER-TLV
 * and DER are implemented here (V-5), without recursion: the nesting is an explicit stack of at most 16 levels.
 *
 * Convention: a function returns 0 for success, a trap code (vm_internal.h), or ERR(code) for a platform error.
 */
#include <string.h>
#include "vm_internal.h"
#ifdef CL_TEST_CATALOG
#include "cl_hal_test.h"
#endif

#define ERR(code) (0x10000 | (int)(code))
#define IS_ERR(r) (((r) & 0x10000) != 0)
#define TRY(e) do { int t_ = (e); if (t_) return t_; } while (0)
#if defined(_MSC_VER)
#define NOINLINE __declspec(noinline)
#else
#define NOINLINE __attribute__((noinline))
#endif

#define CAT_PLATFORM 2u
#define MAX_DEPTH 16u                     /* the nesting validate must support (BP-36, BP-45) */
#define M_ALL 0x1Fu
#define M_AES ((1u << CL_KEY_AES128) | (1u << CL_KEY_AES256))
#define M_PRIV (1u << CL_KEY_EC_P256_PRIVATE)
#define M_EC ((1u << CL_KEY_EC_P256_PRIVATE) | (1u << CL_KEY_EC_P256_PUBLIC))
#define M_HMAC (1u << CL_KEY_HMAC256)
enum { LIFETIME_COMMAND = 0 };

/* A HAL status as a result: 0, a platform error, or a trap (BC-37). */
static int st(cl_status s) {
    if (s == CL_OK) return 0;
    if (s < 0x0100) return ERR(s);
    return cl_hal_trap(s);
}

/* ------------------------------------------------------------------ signatures (BC-34)
 * One string per native: a character per parameter ('s' a scalar cell, 'v' a view of two cells), then the result:
 * 'n' none, 'c' a cell pushed back (u32 or bool), 'h' a struct written through an extra slot-address cell. */
static const char *const SIG[37] = {
    NULL,
    "ssn", "ssvn", "svc", "sn",                                 /* 1-4    card.key */
    "svvc", "ssvvc", "ssvvc", "ssvvc", "svvc", "svvvsvc",      /* 5-10   digest, mac, sign, verify, agree, derive */
    "ssvvvc", "ssvvvc",                                         /* 11-12  encrypt, decrypt */
    "sssn", "ssssn", "ssssn", "ssssn",                          /* 13-16  begin_* */
    "svn", "svc", "svc", "sn",                                  /* 17-20  update, finish, finish_verify, cancel */
    "vc",                                                       /* 21     card.random.fill */
    "vc", "vh", "vc", "ssvc", "svc",                            /* 22-26  card.cbor */
    "vh", "vc", "vc",                                           /* 27-29  card.tlv */
    "ssvc", "vvc", "vc",                                        /* 30-32  card.der */
    "svvc", "svc",                                              /* 33-34  cbor.write_string, write_bool */
    "ssvvc", "ssvvc",                                           /* 35-36  sign_digest, verify_digest */
};
#ifdef CL_TEST_CATALOG
static const char *const TEST_SIG[5] = {"ssn", "sn", "sc", "ssn", "svvc"};   /* 0xF000-0xF004 (V-33) */
#endif

static const char *signature(uint16_t number) {
    if (number >= 1 && number <= 36) return SIG[number];
#ifdef CL_TEST_CATALOG
    if (number >= 0xF000 && number <= 0xF004) return TEST_SIG[number - 0xF000];
#endif
    return NULL;
}

bool cl_native_known(uint16_t number, bool test_natives) {
    if (number >= 1 && number <= 36) return true;
    return test_natives && number >= 0xF000 && signature(number) != NULL;
}

/* ------------------------------------------------------------------ descriptors (HAL-11, HAL-12) */
typedef struct { cl_vm *vm; uint32_t off; } rd_ctx;

static cl_status reader(const cl_in *in, uint32_t off, uint8_t *dst, uint32_t n) {
    const rd_ctx *r = (const rd_ctx *)in->ctx;
    return cl_hal_read(r->vm->hal, r->off + off, dst, n);
}

/* An input: a pointer for RAM and CONST, a reader for PERSISTENT. */
static int in_view(cl_vm *vm, uint32_t a, uint32_t n, cl_in *in, rd_ctx *r) {
    memset(in, 0, sizeof *in); in->len = n;
    if (CL_TAG(a) == CL_R_PERSISTENT) { r->vm = vm; r->off = CL_OFF(a); in->read = reader; in->ctx = r; return 0; }
    in->ptr = cl_region(vm, a, n, false);
    return in->ptr ? 0 : CL_TRAP_VM;
}

/* A writer opens its atomic update at the HAL's first write, which comes only once the call can no longer fail
 * (HAL-8): so an error is never turned into a trap by the update. It covers the expected result length. */
typedef struct { cl_vm *vm; uint32_t off, len; bool open; } wr_ctx;

static cl_status writer(const cl_out *out, uint32_t off, const uint8_t *src, uint32_t n) {
    wr_ctx *w = (wr_ctx *)out->ctx;
    if (!w->open) {
        cl_status s = cl_hal_update_begin(w->vm->hal, w->off, w->len);
        if (s != CL_OK) return s;
        w->open = true; w->vm->atomic = 1;
    }
    return cl_hal_update_write(w->vm->hal, w->off + off, src, n);
}

static int out_view(cl_vm *vm, uint32_t a, uint32_t cap, uint32_t expect, cl_out *out, wr_ctx *w) {
    memset(out, 0, sizeof *out); memset(w, 0, sizeof *w); out->cap = cap;
    if (CL_TAG(a) == CL_R_PERSISTENT) {
        w->vm = vm; w->off = CL_OFF(a); w->len = expect < cap ? expect : cap;
        out->write = writer; out->ctx = w; return 0;
    }
    out->ptr = cl_region(vm, a, cap, true);
    return out->ptr ? 0 : CL_TRAP_VM;
}

/* After the HAL call: close the writer's update on success, abort it on an error (VEX-28). A trap leaves it to the
 * VM's cleanup. */
static int out_done(cl_vm *vm, wr_ctx *w, cl_status s) {
    if (w->vm != NULL && w->open) {
        if (s == CL_OK) { s = cl_hal_update_end(vm->hal); vm->atomic = 0; }
        else if (s < 0x0100) { (void)cl_hal_update_abort(vm->hal); vm->atomic = 0; }
    }
    return st(s);
}

/* Writes head (hl bytes, in C memory) then n bytes of the view at a, each XORed with x, into the output view (o, cap):
 * one atomic update into PERSISTENT. As if the source were read whole first (HAL-13). */
static int emit(cl_vm *vm, uint32_t o, uint32_t cap, const uint8_t *head, uint32_t hl, uint32_t a, uint32_t n,
                uint8_t x) {
    if ((uint64_t)hl + n > cap) return ERR(CL_ERR_CAPACITY);          /* nothing written (BP-6, BP-7) */
    uint32_t total = hl + n;
    if (CL_TAG(o) == CL_R_PERSISTENT) {
        cl_hal *hal = vm->hal;
        TRY(st(cl_hal_update_begin(hal, CL_OFF(o), total)));
        vm->atomic = 1;
        if (hl) TRY(st(cl_hal_update_write(hal, CL_OFF(o), head, hl)));
        uint8_t chunk[64];
        for (uint32_t done = 0; done < n; ) {
            uint32_t k = n - done < sizeof chunk ? n - done : (uint32_t)sizeof chunk;
            TRY(cl_read(vm, a + done, chunk, k));     /* reads do not see the open update (HAL-20) */
            for (uint32_t i = 0; i < k; i++) chunk[i] ^= x;
            TRY(st(cl_hal_update_write(hal, CL_OFF(o) + hl + done, chunk, k)));
            done += k;
        }
        memset(chunk, 0, sizeof chunk);
        TRY(st(cl_hal_update_end(hal)));
        vm->atomic = 0;
        return 0;
    }
    uint8_t *d = cl_region(vm, o, total, true);
    if (d == NULL) return CL_TRAP_VM;
    if (n) TRY(cl_read(vm, a, d + hl, n));            /* memmove from RAM, chunks from PERSISTENT */
    if (x) for (uint32_t i = 0; i < n; i++) d[hl + i] ^= x;
    if (hl) memcpy(d, head, hl);                      /* after the content, which may overlap the head's bytes */
    return 0;
}

/* ------------------------------------------------------------------ byte access for the codecs */
typedef struct {
    cl_vm *vm; const uint8_t *p; uint32_t off, len;
    int trap; bool cached; uint32_t base; uint8_t cache[32];
} src;

static int src_open(cl_vm *vm, uint32_t a, uint32_t n, src *s) {
    memset(s, 0, sizeof *s); s->vm = vm; s->len = n;
    if (CL_TAG(a) == CL_R_PERSISTENT) { s->off = CL_OFF(a); return 0; }
    s->p = cl_region(vm, a, n, false);
    return s->p ? 0 : CL_TRAP_VM;
}

/* Byte i < len. A failed persistent read is recorded in s->trap, which the caller checks first. */
static uint8_t at(src *s, uint32_t i) {
    if (s->p) return s->p[i];
    uint32_t b = i & ~31u;
    if (!s->cached || b != s->base) {
        uint32_t k = s->len - b < 32u ? s->len - b : 32u;
        int t = st(cl_hal_read(s->vm->hal, s->off + b, s->cache, k));
        if (t) { s->trap = t; return 0; }
        s->base = b; s->cached = true;
    }
    return s->cache[i - b];
}

static int src_close(src *s, int r) {
    memset(s->cache, 0, sizeof s->cache);
    return s->trap ? s->trap : r;
}

/* Python's UTF-8 decoder: shortest forms only, no surrogates, nothing above U+10FFFF. */
static bool utf8_ok(src *s, uint32_t i, uint32_t n) {
    uint32_t end = i + n;
    while (i < end) {
        uint8_t b = at(s, i), lo = 0x80, hi = 0xBF;
        uint32_t k;
        if (b < 0x80) { i++; continue; }
        if (b >= 0xC2 && b <= 0xDF) k = 1;
        else if (b >= 0xE0 && b <= 0xEF) { k = 2; if (b == 0xE0) lo = 0xA0; if (b == 0xED) hi = 0x9F; }
        else if (b >= 0xF0 && b <= 0xF4) { k = 3; if (b == 0xF0) lo = 0x90; if (b == 0xF4) hi = 0x8F; }
        else return false;
        if (k > end - i - 1) return false;
        uint8_t c = at(s, i + 1);
        if (c < lo || c > hi) return false;
        for (uint32_t j = 2; j <= k; j++) if ((at(s, i + j) & 0xC0) != 0x80) return false;
        i += k + 1;
    }
    return true;
}

/* ------------------------------------------------------------------ CBOR (BP-34 to BP-40; src/cardlang/platform/testcbor.py) */
static int cbor_read_head(src *s, uint32_t i, uint8_t *major, uint64_t *val, uint32_t *size) {
    if (i >= s->len) return ERR(CL_ERR_MALFORMED);
    uint8_t ib = at(s, i), ai = ib & 31u;
    *major = (uint8_t)(ib >> 5);
    if (*major == 7) {
        if (ai >= 20 && ai <= 23) { *val = ai; *size = 1; return 0; }
        return ERR((ai >= 25 && ai <= 27) ? CL_ERR_UNSUPPORTED : CL_ERR_MALFORMED);   /* floats; the rest */
    }
    if (ai < 24) { *val = ai; *size = 1; return 0; }
    if (ai > 27) return ERR(CL_ERR_MALFORMED);                      /* reserved, indefinite length */
    uint32_t n = 1u << (ai - 24);
    if (n > s->len - i - 1) return ERR(CL_ERR_MALFORMED);
    uint64_t v = 0;
    for (uint32_t k = 0; k < n; k++) v = (v << 8) | at(s, i + 1 + k);
    if (v < (n == 1 ? 24u : (1ull << (4 * n)))) return ERR(CL_ERR_MALFORMED);   /* not the shortest form */
    *val = v; *size = 1 + n;
    return 0;
}

static uint64_t sat_add(uint64_t p, uint64_t v, uint64_t cap) { return (v > cap || p > cap - v) ? cap : p + v; }

static int cbor_skip(src *s, uint32_t *end) {
    /* Items still to read. Each takes at least a byte, so a count above len + 1 fails exactly as a larger one. */
    uint64_t pending = 1, cap = (uint64_t)s->len + 1;
    uint32_t pos = 0;
    while (pending) {
        uint8_t major; uint64_t val; uint32_t size;
        TRY(cbor_read_head(s, pos, &major, &val, &size));
        pos += size; pending--;
        if (major == 2 || major == 3) {
            if (val > s->len - pos) return ERR(CL_ERR_MALFORMED);
            pos += (uint32_t)val;
        } else if (major == 4) pending = sat_add(pending, val, cap);
        else if (major == 5) pending = sat_add(pending, val > cap ? cap : 2 * val, cap);
        else if (major == 6) pending = sat_add(pending, 1, cap);
    }
    *end = pos;
    return 0;
}

/* Is [a0, a1) bytewise less than [b0, b1)? */
static bool less(src *s, uint32_t a0, uint32_t a1, uint32_t b0, uint32_t b1) {
    for (; a0 < a1 && b0 < b1; a0++, b0++) {
        uint8_t x = at(s, a0), y = at(s, b0);
        if (x != y) return x < y;
    }
    return a0 == a1 && b0 < b1;
}

/* One open array, map or tag: 16 bytes, so 16 levels take 256 bytes of C stack.
 * - remaining: items still to read (pairs, for a map), saturated at len + 1. Each item takes at least a byte, so
 *   a saturated count fails exactly where the true one would, as in cbor_skip. Views are below 2^29 bytes, which
 *   leaves the top two bits for LV_MAP (a map, not an array or tag) and LV_VALUE (the map's next item is a value).
 * - key0, prev0, prev1: where the current key starts, and the previous key's range. prev1 is 0 until a map has
 *   read its first key, since every key ends after the map's head. A tag is an array of one item. */
#define LV_MAP 0x80000000u
#define LV_VALUE 0x40000000u
#define LV_COUNT 0x3FFFFFFFu
typedef struct { uint32_t remaining, key0, prev0, prev1; } cbor_level;

/* The strict check of BP-36, depth first in the order of testcbor._validate, with the nesting as a stack. */
static NOINLINE int cbor_validate(src *s, uint32_t *end) {
    cbor_level lv[MAX_DEPTH];
    uint32_t depth = 0, pos = 0, cap = s->len + 1;
    for (;;) {
        if (depth + 1 > MAX_DEPTH) return ERR(CL_ERR_UNSUPPORTED);
        if (depth && (lv[depth - 1].remaining & (LV_MAP | LV_VALUE)) == LV_MAP) lv[depth - 1].key0 = pos;
        uint8_t major; uint64_t val; uint32_t size;
        TRY(cbor_read_head(s, pos, &major, &val, &size));
        pos += size;
        if (major == 2 || major == 3) {
            if (val > s->len - pos) return ERR(CL_ERR_MALFORMED);
            if (major == 3 && !utf8_ok(s, pos, (uint32_t)val)) return ERR(CL_ERR_MALFORMED);
            pos += (uint32_t)val;
        } else if ((major == 4 || major == 5 || major == 6) && (major == 6 || val > 0)) {
            cbor_level *l = &lv[depth++];
            uint32_t count = major == 6 ? 1u : (val > cap ? cap : (uint32_t)val);
            l->remaining = count | (major == 5 ? LV_MAP : 0u); l->prev1 = 0;
            continue;
        }
        /* An item ended at pos: climb out of every container it completes. */
        while (depth) {
            cbor_level *l = &lv[depth - 1];
            if ((l->remaining & (LV_MAP | LV_VALUE)) == LV_MAP) {    /* a key ended: keys strictly increase */
                if (l->prev1 && !less(s, l->prev0, l->prev1, l->key0, pos)) return ERR(CL_ERR_MALFORMED);
                l->prev0 = l->key0; l->prev1 = pos; l->remaining |= LV_VALUE;
                break;
            }
            l->remaining &= ~LV_VALUE;
            if (--l->remaining & LV_COUNT) break;
            depth--;
        }
        if (depth == 0) { *end = pos; return 0; }
    }
}

static uint32_t cbor_head(uint8_t major, uint32_t v, uint8_t *o) {
    uint8_t m = (uint8_t)(major << 5);
    if (v < 24) { o[0] = (uint8_t)(m | v); return 1; }
    if (v < 0x100) { o[0] = m | 24; o[1] = (uint8_t)v; return 2; }
    if (v < 0x10000) { o[0] = m | 25; o[1] = (uint8_t)(v >> 8); o[2] = (uint8_t)v; return 3; }
    o[0] = m | 26; o[1] = (uint8_t)(v >> 24); o[2] = (uint8_t)(v >> 16); o[3] = (uint8_t)(v >> 8); o[4] = (uint8_t)v;
    return 5;
}

/* ------------------------------------------------------------------ BER-TLV and DER (BP-41 to BP-46; testtlv.py) */
typedef struct { uint32_t tag, length, size; uint8_t cls; bool constructed; } tlv;

/* The head of the object at [i, end). */
static int tlv_head(src *s, uint32_t i, uint32_t end, tlv *t) {
    uint32_t w = end - i, k = 1;
    if (w == 0) return ERR(CL_ERR_MALFORMED);
    uint8_t b0 = at(s, i);
    if ((b0 & 0x1F) == 0x1F) {                           /* subsequent tag bytes, bit 8 set on all but the last */
        for (;;) {
            if (k >= w) return ERR(CL_ERR_MALFORMED);
            k++;
            if (!(at(s, i + k - 1) & 0x80)) break;
        }
    }
    if (k > 4) return ERR(CL_ERR_UNSUPPORTED);
    uint32_t tag = 0;
    for (uint32_t j = 0; j < k; j++) tag = (tag << 8) | at(s, i + j);
    if (k >= w) return ERR(CL_ERR_MALFORMED);
    uint8_t l0 = at(s, i + k++);
    uint32_t length;
    if (l0 < 0x80) length = l0;
    else if (l0 == 0x80 || l0 == 0xFF) return ERR(CL_ERR_MALFORMED);   /* indefinite, reserved */
    else if (l0 > 0x84) return ERR(CL_ERR_UNSUPPORTED);              /* more than 4 length bytes */
    else {
        uint32_t n = l0 - 0x80u;
        if (n > w - k) return ERR(CL_ERR_MALFORMED);
        length = 0;
        for (uint32_t j = 0; j < n; j++) length = (length << 8) | at(s, i + k + j);
        k += n;
    }
    if (length > w - k) return ERR(CL_ERR_MALFORMED);
    t->tag = tag; t->cls = (uint8_t)(b0 >> 6); t->constructed = (b0 & 0x20) != 0; t->length = length; t->size = k;
    return 0;
}

/* testtlv._validate, with the enclosing objects' ends as a stack. */
static NOINLINE int tlv_validate(src *s, uint32_t *end) {
    uint32_t ends[MAX_DEPTH];
    uint32_t depth = 0, pos = 0, first = 0;
    for (;;) {
        if (depth + 1 > MAX_DEPTH) return ERR(CL_ERR_UNSUPPORTED);
        tlv t;
        TRY(tlv_head(s, pos, depth ? ends[depth - 1] : s->len, &t));
        if (depth == 0) first = t.size + t.length;
        if (t.constructed && t.length > 0) { ends[depth++] = pos + t.size + t.length; pos += t.size; continue; }
        pos += t.size + t.length;
        while (depth && pos == ends[depth - 1]) depth--;
        if (depth == 0) { *end = first; return 0; }
    }
}

static uint32_t der_length(uint32_t n, uint8_t *o) {
    if (n < 0x80) { o[0] = (uint8_t)n; return 1; }
    uint32_t k = n > 0xFFFFFF ? 4 : n > 0xFFFF ? 3 : n > 0xFF ? 2 : 1;
    o[0] = (uint8_t)(0x80 | k);
    for (uint32_t j = 0; j < k; j++) o[1 + j] = (uint8_t)(n >> (8 * (k - 1 - j)));
    return 1 + k;
}

static int der_head(uint32_t tag, uint32_t length, uint8_t *o, uint32_t *n) {
    if (tag == 0) return ERR(CL_ERR_MALFORMED);
    uint8_t tb[4] = {(uint8_t)(tag >> 24), (uint8_t)(tag >> 16), (uint8_t)(tag >> 8), (uint8_t)tag};
    uint32_t z = 0;
    while (tb[z] == 0) z++;
    uint32_t k = 4 - z;
    const uint8_t *t = tb + z;
    if (((t[0] & 0x1F) == 0x1F) != (k > 1)) return ERR(CL_ERR_MALFORMED);
    for (uint32_t j = 1; j + 1 < k; j++) if (!(t[j] & 0x80)) return ERR(CL_ERR_MALFORMED);
    if (k > 1 && (t[k - 1] & 0x80)) return ERR(CL_ERR_MALFORMED);
    memcpy(o, t, k);
    *n = k + der_length(length, o + k);
    return 0;
}

/* The DER INTEGER of an unsigned big-endian magnitude: its head (with any 0x00 byte) in head, and the content's
 * offset z into the magnitude. */
static int der_integer(src *s, uint8_t *head, uint32_t *hl, uint32_t *z) {
    uint32_t i = 0;
    while (i < s->len && at(s, i) == 0) i++;
    uint32_t m = s->len - i;
    bool pad = m == 0 || (at(s, i) & 0x80);
    head[0] = 0x02;
    uint32_t n = 1 + der_length(m + (pad ? 1u : 0u), head + 1);
    if (pad) head[n++] = 0x00;
    *hl = n; *z = i;
    return 0;
}

/* ------------------------------------------------------------------ the identifier space (PLT-20, PLT-22) */
static int op_slot(const cl_vm *vm, uint32_t id) {
    for (int i = 0; i < (int)CL_OP_SLOTS; i++) if (vm->op[i].used && vm->op[i].id == id) return i;
    return -1;
}

static bool resource_exists(cl_vm *vm, uint32_t id) {
#ifdef CL_TEST_CATALOG
    uint32_t kind, value;
    return cl_hal_test_resource_get(vm->hal, id, &kind, &value) == CL_OK;
#else
    (void)vm; (void)id; return false;
#endif
}

static bool key_exists(cl_vm *vm, uint32_t id) {
    cl_key_type t; cl_key_storage s;
    return cl_hal_key_info(vm->hal, id, &t, &s) == CL_OK;
}

static bool in_use(cl_vm *vm, uint32_t id) { return key_exists(vm, id) || op_slot(vm, id) >= 0 || resource_exists(vm, id); }

/* A key of one of the types in mask. */
static int need_key(cl_vm *vm, uint32_t id, uint32_t mask, cl_key_type *type) {
    cl_key_type t; cl_key_storage s;
    if (cl_hal_key_info(vm->hal, id, &t, &s) != CL_OK)
        return ERR(op_slot(vm, id) >= 0 || resource_exists(vm, id) ? CL_ERR_WRONG_RESOURCE : CL_ERR_NOT_FOUND);
    if (!(mask & (1u << t))) return ERR(CL_ERR_WRONG_RESOURCE);
    if (type) *type = t;
    return 0;
}

static int operation(cl_vm *vm, uint32_t id, int *slot) {
    *slot = op_slot(vm, id);
    if (*slot >= 0) return 0;
    return ERR(resource_exists(vm, id) || key_exists(vm, id) ? CL_ERR_WRONG_RESOURCE : CL_ERR_NOT_FOUND);
}

static void *op_ctx(cl_vm *vm, int slot) { return vm->ops + (uint32_t)slot * CL_HAL_OP_CTX_SIZE; }

static void op_drop(cl_vm *vm, int slot) {
    (void)cl_hal_op_abort(vm->hal, op_ctx(vm, slot));
    memset(&vm->op[slot], 0, sizeof vm->op[slot]);
}

void cl_natives_end_command(cl_vm *vm) {                        /* VEX-48 */
    for (int i = 0; i < (int)CL_OP_SLOTS; i++)
        if (vm->op[i].used && vm->op[i].lifetime == LIFETIME_COMMAND) op_drop(vm, i);
}

void cl_natives_drop_session(cl_vm *vm) {
    for (int i = 0; i < (int)CL_OP_SLOTS; i++) if (vm->op[i].used) op_drop(vm, i);
}

/* ------------------------------------------------------------------ card.key (BP-18 to BP-25) */
static int create_key(cl_vm *vm, uint32_t id, uint32_t spec, bool generate, uint32_t ma, uint32_t ml) {
    static const uint8_t want[5] = {16, 32, 32, 65, 32};       /* by KeyType ordinal */
    uint8_t ks[2];
    TRY(cl_read(vm, spec, ks, 2));
    if (ks[0] > CL_KEY_HMAC256 || ks[1] > CL_STORAGE_COMMAND) return CL_TRAP_VM;
    if (in_use(vm, id)) return ERR(CL_ERR_ALREADY_EXISTS);
    if (generate && ks[0] == CL_KEY_EC_P256_PUBLIC) return ERR(CL_ERR_UNSUPPORTED);
    if (id == 0) return ERR(CL_ERR_MALFORMED);
    if (generate) return st(cl_hal_key_generate(vm->hal, id, (cl_key_type)ks[0], (cl_key_storage)ks[1]));
    if (ml != want[ks[0]]) return ERR(CL_ERR_MALFORMED);
    cl_in in; rd_ctx r;
    TRY(in_view(vm, ma, ml, &in, &r));
    return st(cl_hal_key_import(vm->hal, id, (cl_key_type)ks[0], (cl_key_storage)ks[1], &in));
}

/* ------------------------------------------------------------------ card.crypto (BP-26 to BP-33) */
static int begin(cl_vm *vm, uint32_t op, cl_op_purpose purpose, uint32_t key, uint32_t alg, uint32_t lifetime) {
    static const uint32_t mask[4] = {0, M_HMAC, M_PRIV, M_EC};
    int e = 0;
    if (purpose != CL_OP_DIGEST) {
        e = need_key(vm, key, mask[purpose], NULL);
        if (e == ERR(CL_ERR_NOT_FOUND)) return e;
    }
    if (in_use(vm, op)) return ERR(CL_ERR_ALREADY_EXISTS);
    if (e) return e;
    if (op == 0) return ERR(CL_ERR_MALFORMED);
    int slot = -1;
    for (int i = 0; i < (int)CL_OP_SLOTS; i++) if (!vm->op[i].used) { slot = i; break; }
    if (slot < 0) return ERR(CL_ERR_CAPACITY);
    TRY(st(cl_hal_op_begin(vm->hal, op_ctx(vm, slot), purpose, key, alg)));
    vm->op[slot].used = 1; vm->op[slot].id = op;
    vm->op[slot].purpose = (uint8_t)purpose; vm->op[slot].lifetime = (uint8_t)lifetime;
    return 0;
}

/* A one-shot HAL call writing into an output view; the call is made between out_view and out_done. */
#define HAL_OUT(oa, ocap, expect, call)                                       \
    do {                                                                      \
        cl_out out; wr_ctx w; uint32_t n_ = 0;                                \
        TRY(out_view(vm, (oa), (ocap), (expect), &out, &w));                  \
        TRY(out_done(vm, &w, (call)));                                        \
        *res = n_;                                                            \
    } while (0)

/* Each family of natives has its own function and frame, so only one family's locals are on the C stack at a
 * time. */
/* card.key (BP-18 to BP-25) */
static NOINLINE int keys(cl_vm *vm, uint16_t number, const uint32_t *c, uint32_t *res, uint32_t slot) {
    cl_hal *hal = vm->hal;
    cl_key_type kt;
    (void)hal; (void)number; (void)res; (void)slot;
    switch (number) {
    /* card.key */
    case 1: return create_key(vm, c[0], c[1], true, 0, 0);
    case 2: return create_key(vm, c[0], c[1], false, c[2], c[3]);
    case 3:
        TRY(need_key(vm, c[0], M_ALL, &kt));
        if (!(M_EC & (1u << kt))) return ERR(CL_ERR_WRONG_RESOURCE);
        if (c[2] < 65) return ERR(CL_ERR_CAPACITY);
        HAL_OUT(c[1], c[2], 65, cl_hal_key_export_public(hal, c[0], &out, &n_));
        return 0;
    case 4: TRY(need_key(vm, c[0], M_ALL, NULL)); return st(cl_hal_key_delete(hal, c[0]));
    default: return CL_TRAP_VM;
    }
}

/* One-shot cryptography (BP-29) */
static NOINLINE int one_shot(cl_vm *vm, uint16_t number, const uint32_t *c, uint32_t *res, uint32_t slot) {
    cl_hal *hal = vm->hal;
    cl_in in, in2, in3; rd_ctx r, r2, r3;
    bool valid = false;
    (void)hal; (void)number; (void)res; (void)slot;
    switch (number) {
    /* one-shot cryptography */
    case 5:
        TRY(in_view(vm, c[1], c[2], &in, &r));
        HAL_OUT(c[3], c[4], 32, cl_hal_digest(hal, (cl_digest_alg)c[0], &in, &out, &n_));
        return 0;
    case 6:
        TRY(need_key(vm, c[0], M_HMAC, NULL)); TRY(in_view(vm, c[2], c[3], &in, &r));
        HAL_OUT(c[4], c[5], 32, cl_hal_mac(hal, c[0], (cl_mac_alg)c[1], &in, &out, &n_));
        return 0;
    case 7:
        TRY(need_key(vm, c[0], M_PRIV, NULL)); TRY(in_view(vm, c[2], c[3], &in, &r));
        HAL_OUT(c[4], c[5], 64, cl_hal_sign(hal, c[0], (cl_sig_alg)c[1], &in, &out, &n_));
        return 0;
    case 8: case 36:
        TRY(need_key(vm, c[0], M_EC, NULL));
        if (number == 36 && c[3] != 32) return ERR(CL_ERR_MALFORMED);
        TRY(in_view(vm, c[2], c[3], &in, &r)); TRY(in_view(vm, c[4], c[5], &in2, &r2));
        TRY(st(number == 8 ? cl_hal_verify(hal, c[0], (cl_sig_alg)c[1], &in, &in2, &valid)
                           : cl_hal_verify_digest(hal, c[0], (cl_sig_alg)c[1], &in, &in2, &valid)));
        *res = valid; return 0;
    case 35:
        TRY(need_key(vm, c[0], M_PRIV, NULL));
        if (c[3] != 32) return ERR(CL_ERR_MALFORMED);
        TRY(in_view(vm, c[2], c[3], &in, &r));
        HAL_OUT(c[4], c[5], 64, cl_hal_sign_digest(hal, c[0], (cl_sig_alg)c[1], &in, &out, &n_));
        return 0;
    case 9:
        TRY(need_key(vm, c[0], M_PRIV, NULL)); TRY(in_view(vm, c[1], c[2], &in, &r));
        HAL_OUT(c[3], c[4], 32, cl_hal_agree(hal, c[0], &in, &out, &n_));
        return 0;
    case 10:
        if (c[7] < 1 || c[7] > 8160) return ERR(CL_ERR_MALFORMED);
        TRY(in_view(vm, c[1], c[2], &in, &r)); TRY(in_view(vm, c[3], c[4], &in2, &r2));
        TRY(in_view(vm, c[5], c[6], &in3, &r3));
        HAL_OUT(c[8], c[9], c[7], cl_hal_derive(hal, (cl_kdf_alg)c[0], &in, &in2, &in3, c[7], &out, &n_));
        return 0;
    case 11: case 12:
        TRY(need_key(vm, c[0], M_AES, NULL));
        if (c[3] != 16 || c[5] % 16) return ERR(CL_ERR_MALFORMED);
        TRY(in_view(vm, c[2], c[3], &in, &r)); TRY(in_view(vm, c[4], c[5], &in2, &r2));
        HAL_OUT(c[6], c[7], c[5], cl_hal_cipher(hal, c[0], (cl_cipher_alg)c[1], number == 11 ? CL_ENCRYPT : CL_DECRYPT,
                                                &in, &in2, &out, &n_));
        return 0;
    default: return CL_TRAP_VM;
    }
}

/* Multi-part cryptography and randomness (BP-31, BP-32) */
static NOINLINE int multi_part(cl_vm *vm, uint16_t number, const uint32_t *c, uint32_t *res, uint32_t slot) {
    cl_hal *hal = vm->hal;
    cl_in in; rd_ctx r;
    bool valid = false;
    int op;
    (void)hal; (void)number; (void)res; (void)slot;
    switch (number) {
    /* multi-part cryptography */
    case 13: return begin(vm, c[0], CL_OP_DIGEST, 0, c[1], c[2]);
    case 14: return begin(vm, c[0], CL_OP_MAC, c[1], c[2], c[3]);
    case 15: return begin(vm, c[0], CL_OP_SIGN, c[1], c[2], c[3]);
    case 16: return begin(vm, c[0], CL_OP_VERIFY, c[1], c[2], c[3]);
    case 17:
        TRY(operation(vm, c[0], &op)); TRY(in_view(vm, c[1], c[2], &in, &r));
        return st(cl_hal_op_update(hal, op_ctx(vm, op), &in));
    case 18:
        TRY(operation(vm, c[0], &op));
        if (vm->op[op].purpose == CL_OP_VERIFY) return ERR(CL_ERR_INVALID_STATE);
        HAL_OUT(c[1], c[2], vm->op[op].purpose == CL_OP_SIGN ? 64u : 32u,
                cl_hal_op_finish(hal, op_ctx(vm, op), &out, &n_));
        memset(&vm->op[op], 0, sizeof vm->op[op]);            /* finish erased the context (HAL-26) */
        return 0;
    case 19:
        TRY(operation(vm, c[0], &op));
        if (vm->op[op].purpose != CL_OP_VERIFY) return ERR(CL_ERR_INVALID_STATE);
        TRY(in_view(vm, c[1], c[2], &in, &r));
        TRY(st(cl_hal_op_finish_verify(hal, op_ctx(vm, op), &in, &valid)));
        memset(&vm->op[op], 0, sizeof vm->op[op]);
        *res = valid; return 0;
    case 20: TRY(operation(vm, c[0], &op)); op_drop(vm, op); return 0;
    case 21: HAL_OUT(c[0], c[1], c[1], cl_hal_random(hal, &out)); *res = c[1]; return 0;
    default: return CL_TRAP_VM;
    }
}

/* CBOR, BER-TLV and DER (BP-34 to BP-46) */
static NOINLINE int codecs(cl_vm *vm, uint16_t number, const uint32_t *c, uint32_t *res, uint32_t slot) {
    cl_hal *hal = vm->hal;
    int e;
    src s;
    uint8_t buf[16];
    uint32_t n = 0, z = 0, v = 0;
    (void)hal; (void)number; (void)res; (void)slot;
    switch (number) {
    /* card.cbor */
    case 22: case 24:
        TRY(src_open(vm, c[0], c[1], &s));
        e = src_close(&s, number == 22 ? cbor_validate(&s, &n) : cbor_skip(&s, &n));
        *res = n; return e;
    case 23: {
        uint8_t major = 0; uint64_t val = 0; uint32_t size = 0;
        TRY(src_open(vm, c[0], c[1], &s));
        TRY(src_close(&s, cbor_read_head(&s, 0, &major, &val, &size)));
        if (val > 0xFFFFFFFFu) return ERR(CL_ERR_UNSUPPORTED);
        uint8_t h[9] = {major, (uint8_t)val, (uint8_t)(val >> 8), (uint8_t)(val >> 16), (uint8_t)(val >> 24),
                        (uint8_t)size, (uint8_t)(size >> 8), (uint8_t)(size >> 16), (uint8_t)(size >> 24)};
        return cl_write(vm, slot, h, sizeof h);                 /* CborHead {major, argument, size} */
    }
    case 25:
        if (c[0] == 7) {
            if (c[1] < 20 || c[1] > 23) return ERR(CL_ERR_MALFORMED);
            buf[0] = (uint8_t)(0xE0 | c[1]); n = 1;
        } else n = cbor_head((uint8_t)c[0], c[1], buf);
        TRY(emit(vm, c[2], c[3], buf, n, 0, 0, 0)); *res = n; return 0;
    case 26:
        n = (c[0] & 0x80000000u) ? cbor_head(1, ~c[0], buf) : cbor_head(0, c[0], buf);   /* -1 - v is ~v */
        TRY(emit(vm, c[1], c[2], buf, n, 0, 0, 0)); *res = n; return 0;
    case 33:
        if (c[0] != 2 && c[0] != 3) return ERR(CL_ERR_MALFORMED);
        if (c[0] == 3) {
            TRY(src_open(vm, c[1], c[2], &s));
            TRY(src_close(&s, utf8_ok(&s, 0, c[2]) ? 0 : ERR(CL_ERR_MALFORMED)));
        }
        n = cbor_head((uint8_t)c[0], c[2], buf);
        TRY(emit(vm, c[3], c[4], buf, n, c[1], c[2], 0)); *res = n + c[2]; return 0;
    case 34:
        buf[0] = c[0] ? 0xF5 : 0xF4;
        TRY(emit(vm, c[1], c[2], buf, 1, 0, 0, 0)); *res = 1; return 0;
    /* card.tlv */
    case 27: {
        tlv t;
        TRY(src_open(vm, c[0], c[1], &s));
        TRY(src_close(&s, tlv_head(&s, 0, s.len, &t)));
        uint8_t h[14] = {(uint8_t)t.tag, (uint8_t)(t.tag >> 8), (uint8_t)(t.tag >> 16), (uint8_t)(t.tag >> 24),
                         t.cls, t.constructed ? 1 : 0,
                         (uint8_t)t.length, (uint8_t)(t.length >> 8), (uint8_t)(t.length >> 16), (uint8_t)(t.length >> 24),
                         (uint8_t)t.size, (uint8_t)(t.size >> 8), (uint8_t)(t.size >> 16), (uint8_t)(t.size >> 24)};
        return cl_write(vm, slot, h, sizeof h);                 /* TlvHead {tag, class, constructed, length, size} */
    }
    case 28: {
        tlv t;
        TRY(src_open(vm, c[0], c[1], &s));
        TRY(src_close(&s, tlv_head(&s, 0, s.len, &t)));
        *res = t.size + t.length; return 0;
    }
    case 29:
        TRY(src_open(vm, c[0], c[1], &s));
        e = src_close(&s, tlv_validate(&s, &n));
        *res = n; return e;
    /* card.der */
    case 30:
        TRY(der_head(c[0], c[1], buf, &n));
        TRY(emit(vm, c[2], c[3], buf, n, 0, 0, 0)); *res = n; return 0;
    case 31: case 32:
        TRY(src_open(vm, c[0], c[1], &s));
        TRY(src_close(&s, der_integer(&s, buf, &n, &z)));
        v = n + (c[1] - z);
        if (number == 32) { *res = v; return 0; }
        TRY(emit(vm, c[2], c[3], buf, n, c[0] + z, c[1] - z, 0)); *res = v; return 0;
    default: return CL_TRAP_VM;
    }
}

#ifdef CL_TEST_CATALOG
/* The test-only catalog (language/conformance/platform/test-catalog.txt, V-33) */
static NOINLINE int test_catalog(cl_vm *vm, uint16_t number, const uint32_t *c, uint32_t *res, uint32_t slot) {
    cl_hal *hal = vm->hal;
    uint32_t n = 0, v = 0;
    (void)hal; (void)number; (void)res; (void)slot;
    switch (number) {
    /* the test-only catalog (language/conformance/platform/test-catalog.txt, V-33) */
    case 0xF000: return st(cl_hal_test_resource_create(hal, c[0], c[1]));
    case 0xF001: TRY(st(cl_hal_test_resource_get(hal, c[0], &n, &v))); return st(cl_hal_test_resource_delete(hal, c[0]));
    case 0xF002:
        TRY(st(cl_hal_test_resource_get(hal, c[0], &n, &v)));
        if (n != 1) return ERR(CL_ERR_WRONG_RESOURCE);
        *res = v; return 0;
    case 0xF003:
        TRY(st(cl_hal_test_resource_get(hal, c[0], &n, &v)));
        if (n != 1) return ERR(CL_ERR_WRONG_RESOURCE);
        return st(cl_hal_test_resource_set(hal, c[0], c[1]));
    case 0xF004:
        TRY(st(cl_hal_test_resource_get(hal, c[0], &n, &v)));
        if (n != 2) return ERR(CL_ERR_WRONG_RESOURCE);
        TRY(emit(vm, c[3], c[4], NULL, 0, c[1], c[2], 0x5A)); *res = c[2]; return 0;
    default: return CL_TRAP_VM;
    }
}

#endif

static int dispatch(cl_vm *vm, uint16_t number, const uint32_t *c, uint32_t *res, uint32_t slot) {
    if (number <= 4) return keys(vm, number, c, res, slot);
    if (number <= 12 || number == 35 || number == 36) return one_shot(vm, number, c, res, slot);
    if (number <= 21) return multi_part(vm, number, c, res, slot);
    if (number <= 34) return codecs(vm, number, c, res, slot);
#ifdef CL_TEST_CATALOG
    if (number >= 0xF000) return test_catalog(vm, number, c, res, slot);
#endif
    return CL_TRAP_VM;
}

/* NATIVE n (BC-21, BC-34): pop the arguments, charge the budget, run, and report the outcome through out_cat and
 * out_code, then push a cell result (0 after an error). */
int cl_native_call(cl_vm *vm, uint16_t number) {
    const char *sig = signature(number);
    if (sig == NULL) return CL_TRAP_VM;
    uint32_t np = (uint32_t)strlen(sig) - 1, cells = 0, view_bytes = 0;
    char ret = sig[np];
    for (uint32_t i = 0; i < np; i++) cells += sig[i] == 'v' ? 2u : 1u;
    if (ret == 'h') cells++;
    uint32_t c[12];
    for (uint32_t i = cells; i-- > 0; ) TRY(cl_pop(vm, &c[i]));
    for (uint32_t i = 0, k = 0; i < np; i++) {
        if (sig[i] == 'v') { view_bytes += c[k + 1]; k += 2; } else k++;
    }
    TRY(cl_charge(vm, 8 + cl_blocks(view_bytes)));
    uint32_t res = 0;
    int r = dispatch(vm, number, c, &res, ret == 'h' ? c[cells - 1] : 0);
    if (IS_ERR(r)) { vm->out_cat = CAT_PLATFORM; vm->out_code = (uint16_t)(r & 0xFFFF); res = 0; }
    else if (r) return r;
    else { vm->out_cat = 0; vm->out_code = 0; }
    if (ret == 'c') TRY(cl_push(vm, res));
    return 0;
}
