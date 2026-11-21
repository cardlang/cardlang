/*
 * vm.c - the CardLang VM: loader, interpreter loop, memory, calls, outcomes, traps and entry points (VM7).
 *
 * A port of the prototype tools/vmproto/vm.py, instruction for instruction (bytecode version 1, vm/bytecode.md).
 * The interpreter is one loop in one function, with no recursion (VEX-19); a trap leaves the loop through a single
 * exit, never through longjmp (VEX-39). Every multi-byte value is decoded byte by byte (V-13).
 */
#include <string.h>
#include "vm_internal.h"

#define RET_NONE 0xFFFFFFFFu
#define NONE_ENTRY 0xFFFFu

/* ------------------------------------------------------------------ little-endian access */
static uint16_t le16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static void put32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}

/* ------------------------------------------------------------------ types and cells (BC-4) */
static const uint8_t WIDTH[6] = {1, 2, 4, 1, 2, 4};
static bool is_signed(unsigned t) { return t >= CL_T_I8; }

/* The normalized cell of a value of type t (zero- or sign-extended). */
static uint32_t norm(int64_t v, unsigned t) {
    unsigned bits = 8u * WIDTH[t];
    uint64_t mask = bits == 32 ? 0xFFFFFFFFu : ((1ull << bits) - 1u);
    uint64_t u = (uint64_t)v & mask;
    if (is_signed(t) && bits < 32 && (u >> (bits - 1)) & 1u) u |= ~mask;
    return (uint32_t)u;
}
/* The mathematical value of a normalized cell of type t. */
static int64_t val(uint32_t c, unsigned t) { return is_signed(t) ? (int64_t)(int32_t)c : (int64_t)c; }
static bool in_range(int64_t v, unsigned t) {
    unsigned bits = 8u * WIDTH[t];
    if (is_signed(t)) return v >= -(int64_t)(1ll << (bits - 1)) && v <= (int64_t)((1ll << (bits - 1)) - 1);
    return v >= 0 && (uint64_t)v <= ((bits == 32) ? 0xFFFFFFFFull : ((1ull << bits) - 1u));
}

/* ------------------------------------------------------------------ the budget and HAL statuses */
uint32_t cl_blocks(uint32_t bytes) { return (bytes + 15u) / 16u; }

int cl_charge(cl_vm *vm, uint32_t n) {
    if (vm->budget < n) return CL_TRAP_EXHAUSTED;
    vm->budget -= n; return 0;
}

int cl_hal_trap(cl_status s) {
    if (s == CL_OK) return 0;
    if (s == CL_TXN_CAPACITY) return CL_TRAP_TXN_CAPACITY;
    if (s == CL_COMMIT_FAILED) return CL_TRAP_COMMIT;
    if (s == CL_FATAL) return CL_TRAP_POWER_LOSS;
    return CL_TRAP_VM;
}

/* ------------------------------------------------------------------ memory (VEX-7, VEX-26 to VEX-28, VEX-34) */

/* A direct pointer to n bytes of a RAM or CONST region, or NULL for PERSISTENT or out of range. */
static uint8_t *region(cl_vm *vm, uint32_t a, uint32_t n, bool writing) {
    uint32_t off = CL_OFF(a);
    switch (CL_TAG(a)) {
    case CL_R_CONST:
        if (writing || off > vm->const_size || n > vm->const_size - off) return NULL;
        return (uint8_t *)(uintptr_t)(vm->image + vm->const_off + off);
    case CL_R_SESSION: return (off <= vm->session_size && n <= vm->session_size - off) ? vm->session + off : NULL;
    case CL_R_STACK: return (off <= vm->stack_size && n <= vm->stack_size - off) ? vm->stack + off : NULL;
    case CL_R_REQUEST:
        if (writing || vm->request == NULL || off > vm->request_len || n > vm->request_len - off) return NULL;
        return (uint8_t *)(uintptr_t)(vm->request + off);
    case CL_R_RESPONSE: return (vm->response && off <= vm->response_cap && n <= vm->response_cap - off) ? vm->response + off : NULL;
    default: return NULL;
    }
}

int cl_read(cl_vm *vm, uint32_t a, uint8_t *dst, uint32_t n) {
    if (CL_TAG(a) == CL_R_PERSISTENT) {
        /* Persistent data moves through the HAL; in chunks, as through the bounce buffer (VEX-34). */
        uint32_t done = 0;
        while (done < n) {
            uint32_t k = n - done < CL_BOUNCE ? n - done : CL_BOUNCE;
            int t = cl_hal_trap(cl_hal_read(vm->hal, CL_OFF(a) + done, vm->bounce, k));
            if (t) return t;
            memcpy(dst + done, vm->bounce, k); done += k;
        }
        memset(vm->bounce, 0, CL_BOUNCE);
        return 0;
    }
    const uint8_t *p = region(vm, a, n, false);
    if (p == NULL) return CL_TRAP_VM;
    memmove(dst, p, n);
    return 0;
}

/* Write n bytes from src (in RAM). Into PERSISTENT, one atomic update (VEX-28). */
int cl_write(cl_vm *vm, uint32_t a, const uint8_t *src, uint32_t n) {
    if (CL_TAG(a) == CL_R_PERSISTENT) {
        int t = cl_hal_trap(cl_hal_update_begin(vm->hal, CL_OFF(a), n));
        if (t) return t;
        vm->atomic = 1;
        for (uint32_t done = 0; done < n; ) {
            uint32_t k = n - done < CL_BOUNCE ? n - done : CL_BOUNCE;
            t = cl_hal_trap(cl_hal_update_write(vm->hal, CL_OFF(a) + done, src + done, k));
            if (t) return t;
            done += k;
        }
        t = cl_hal_trap(cl_hal_update_end(vm->hal));
        vm->atomic = 0;
        return t;
    }
    uint8_t *p = region(vm, a, n, true);
    if (p == NULL) return CL_TRAP_VM;
    memmove(p, src, n);
    return 0;
}

/* Write a pattern of w bytes, count times (FILL, ZERO, WIPE): one atomic update into PERSISTENT. */
static int write_pattern(cl_vm *vm, uint32_t a, const uint8_t *pattern, uint32_t w, uint32_t count) {
    uint64_t total64 = (uint64_t)w * count;
    if (total64 > 0x1FFFFFFFu) return CL_TRAP_VM;
    uint32_t total = (uint32_t)total64;
    if (CL_TAG(a) == CL_R_PERSISTENT) {
        int t = cl_hal_trap(cl_hal_update_begin(vm->hal, CL_OFF(a), total));
        if (t) return t;
        vm->atomic = 1;
        uint8_t chunk[64];
        uint32_t per = (uint32_t)(sizeof chunk / w) * w;
        for (uint32_t i = 0; i < per; i++) chunk[i] = pattern[i % w];
        for (uint32_t done = 0; done < total; ) {
            uint32_t k = total - done < per ? total - done : per;
            t = cl_hal_trap(cl_hal_update_write(vm->hal, CL_OFF(a) + done, chunk, k));
            if (t) return t;
            done += k;
        }
        t = cl_hal_trap(cl_hal_update_end(vm->hal));
        vm->atomic = 0;
        return t;
    }
    uint8_t *p = region(vm, a, total, true);
    if (p == NULL) return CL_TRAP_VM;
    for (uint32_t i = 0; i < total; i++) p[i] = pattern[i % w];
    return 0;
}

/* Copy n bytes, overlap-safe (VEX-15). */
static int copy(cl_vm *vm, uint32_t d, uint32_t s, uint32_t n) {
    bool dp = CL_TAG(d) == CL_R_PERSISTENT, sp = CL_TAG(s) == CL_R_PERSISTENT;
    if (dp && sp) return cl_hal_trap(cl_hal_copy(vm->hal, CL_OFF(d), CL_OFF(s), n));
    if (dp) {                                           /* RAM or CONST into PERSISTENT */
        const uint8_t *src = region(vm, s, n, false);
        return src ? cl_write(vm, d, src, n) : CL_TRAP_VM;
    }
    uint8_t *dst = region(vm, d, n, true);
    if (dst == NULL) return CL_TRAP_VM;
    return cl_read(vm, s, dst, n);                      /* memmove for RAM to RAM; chunks from PERSISTENT */
}

static int load_scalar(cl_vm *vm, uint32_t a, unsigned t, uint32_t *cell) {
    uint8_t b[4] = {0};
    int r = cl_read(vm, a, b, WIDTH[t]);
    if (r) return r;
    uint32_t raw = (uint32_t)b[0] | ((uint32_t)b[1] << 8) | ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24);
    *cell = norm((int64_t)raw, t);
    return 0;
}

static int store_scalar(cl_vm *vm, uint32_t a, unsigned t, uint32_t c) {
    uint8_t b[4]; put32(b, c);
    return cl_write(vm, a, b, WIDTH[t]);
}

/* ------------------------------------------------------------------ the operand stack (BC-23) */
int cl_push(cl_vm *vm, uint32_t cell) {
    if (vm->sp > vm->stack_size - 4u) return CL_TRAP_VM;
    put32(vm->stack + vm->sp, cell); vm->sp += 4; return 0;
}
int cl_pop(cl_vm *vm, uint32_t *cell) {
    if (vm->sp < 4u) return CL_TRAP_VM;
    vm->sp -= 4; *cell = le32(vm->stack + vm->sp); return 0;
}

/* ------------------------------------------------------------------ the image (IMG-3, IMG-6) */
typedef struct { uint32_t code, frame_size; uint8_t argc, payload; uint16_t operand_base; } func_t;

static func_t function(const cl_vm *vm, uint16_t i) {
    const uint8_t *p = vm->image + vm->func_off + 12u * i;
    func_t f = {le32(p), le32(p + 4), p[8], p[9], le16(p + 10)};
    return f;
}

/* The function whose code contains pc: code offsets increase with the index (IMG-11). */
static uint16_t function_at(const cl_vm *vm, uint32_t pc) {
    uint16_t lo = 0, hi = (uint16_t)(vm->func_count - 1u);
    while (lo < hi) {
        uint16_t mid = (uint16_t)((lo + hi + 1u) / 2u);
        if (function(vm, mid).code <= pc) lo = mid; else hi = (uint16_t)(mid - 1u);
    }
    return lo;
}

cl_load_status cl_vm_load(cl_vm *vm, const cl_config *cfg, const uint8_t *image, uint32_t size, cl_hal *hal) {
    memset(vm, 0, sizeof *vm);
    if (size < 72 || memcmp(image, "CLVM", 4) != 0 || le16(image + 4) != 1) return CL_LOAD_FORMAT;
    if (image[6] != 1 || (image[7] != 0 && image[7] != cfg->binding)) return CL_LOAD_PROFILE;
    uint32_t persistent = le32(image + 12), session = le32(image + 16), stack = le32(image + 20), max_atomic = le32(image + 24);
    uint16_t fcount = le16(image + 28), icount = le16(image + 38);
    uint32_t foff = le32(image + 40), ioff = le32(image + 44), coff = le32(image + 48), csize = le32(image + 52);
    uint32_t codeoff = le32(image + 56), codesize = le32(image + 60);
    if (le32(image + 8) != size || fcount == 0) return CL_LOAD_LAYOUT;
    if (foff > size || 12ull * fcount > size - foff || ioff > size || 2ull * icount > size - ioff ||
        coff > size || csize > size - coff || codeoff > size || codesize > size - codeoff) return CL_LOAD_LAYOUT;
    for (int e = 0; e < 4; e++) {
        uint16_t idx = le16(image + 30 + 2 * e);
        if (idx != NONE_ENTRY && idx >= fcount) return CL_LOAD_LAYOUT;
        vm->entry[e] = idx;
    }
    if (vm->entry[0] == NONE_ENTRY) return CL_LOAD_LAYOUT;
    if (session > cfg->session_size || stack > cfg->stack_size) return CL_LOAD_AREAS;
    if (persistent > cl_hal_storage_size(hal)) return CL_LOAD_STORAGE;
    if (max_atomic > cl_hal_atomic_capacity(hal)) return CL_LOAD_ATOMIC;
    for (uint16_t i = 0; i < icount; i++)
        if (!cl_native_known(le16(image + ioff + 2u * i), cfg->test_natives)) return CL_LOAD_NATIVE;
    vm->image = image; vm->image_size = size;
    vm->code_off = codeoff; vm->code_size = codesize; vm->const_off = coff; vm->const_size = csize; vm->func_off = foff;
    vm->func_count = fcount;
    for (uint16_t i = 0; i < fcount; i++) {
        func_t f = function(vm, i);
        if (f.code > codesize || (i > 0 && f.code < function(vm, (uint16_t)(i - 1u)).code)) return CL_LOAD_LAYOUT;
    }
    vm->session = cfg->session; vm->session_size = session;
    vm->stack = cfg->stack; vm->stack_size = cfg->stack_size;
    vm->budget_cfg = cfg->budget; vm->hal = hal;
    vm->state = CL_STATE_NOT_INSTALLED;
    return CL_LOAD_OK;
}

/* ------------------------------------------------------------------ the interpreter */

/* Instruction fetch: operands are read relative to the instruction's start. */
#define OP8(k) (code[pc + (k)])
#define OP16(k) le16(code + pc + (k))
#define OP32(k) le32(code + pc + (k))
#define TRY(expr) do { int t_ = (expr); if (t_) { trap = t_; goto trapped; } } while (0)
#define POP(v) TRY(cl_pop(vm, &(v)))
#define PUSH(v) TRY(cl_push(vm, (v)))

/* Ends the current frame (BC-26). Returns true when the entry frame ended; then *out holds the result. */
static int leave(cl_vm *vm, uint8_t cat, uint16_t code, bool has_value, uint32_t value, bool *ended, cl_result *out) {
    func_t f = function(vm, function_at(vm, vm->pc));
    if (vm->fp > vm->stack_size || f.frame_size > vm->stack_size - vm->fp) return CL_TRAP_VM;
    uint32_t ret_pc = le32(vm->stack + vm->fp), caller_fp = le32(vm->stack + vm->fp + 4);
    memset(vm->stack + vm->fp, 0, f.frame_size);                 /* erase the frame (BC-28, PLT-35) */
    vm->sp = vm->fp; vm->out_cat = cat; vm->out_code = code;
    if (ret_pc == RET_NONE) {
        *ended = true;
        out->kind = cat == 0 ? CL_RESULT_OK : CL_RESULT_ERR; out->category = cat; out->code = code;
        out->has_count = cat == 0 && has_value; out->count = value;
        return 0;
    }
    vm->fp = caller_fp; vm->pc = ret_pc;
    if (f.payload == 1) return cl_push(vm, cat == 0 ? value : 0u);
    return 0;
}

static cl_result run(cl_vm *vm, uint16_t findex, const uint32_t *cells, uint32_t ncells) {
    cl_result out = {0};
    int trap = 0;
    func_t f = function(vm, findex);
    if (f.frame_size > vm->stack_size || 8u + 4u * ncells > f.frame_size) { trap = CL_TRAP_VM; goto trapped; }
    vm->fp = 0;
    put32(vm->stack, RET_NONE); put32(vm->stack + 4, 0);
    for (uint32_t i = 0; i < ncells; i++) put32(vm->stack + 8 + 4 * i, cells[i]);
    memset(vm->stack + 8 + 4 * ncells, 0, f.frame_size - 8 - 4 * ncells);
    vm->sp = f.operand_base; vm->pc = f.code; vm->budget = vm->budget_cfg; vm->out_cat = 0; vm->out_code = 0;
    const uint8_t *code = vm->image + vm->code_off;

    for (;;) {
        uint32_t pc = vm->pc;
        if (pc >= vm->code_size) { trap = CL_TRAP_VM; goto trapped; }
        TRY(cl_charge(vm, 1));
        uint8_t op = code[pc];
        uint32_t a = 0, b = 0, c = 0, d = 0, x = 0;
        switch (op) {
        /* 2.1 constants and stack */
        case 0x01: PUSH(OP8(1)); vm->pc = pc + 2; break;
        case 0x02: PUSH(OP16(1)); vm->pc = pc + 3; break;
        case 0x03: PUSH(OP32(1)); vm->pc = pc + 5; break;
        case 0x86: PUSH(0); vm->pc = pc + 1; break;                  /* PUSH0 */
        case 0x87: PUSH(1); vm->pc = pc + 1; break;                  /* PUSH1 */
        case 0x04: POP(a); PUSH(a); PUSH(a); vm->pc = pc + 1; break; /* DUP */
        case 0x05: POP(a); vm->pc = pc + 1; break;                   /* DROP */
        case 0x06: POP(b); POP(a); PUSH(b); PUSH(a); vm->pc = pc + 1; break;
        case 0x07: POP(b); POP(a); PUSH(a); PUSH(b); PUSH(a); vm->pc = pc + 1; break;
        case 0x08: POP(b); POP(a); PUSH(a); PUSH(b); PUSH(a); PUSH(b); vm->pc = pc + 1; break;
        case 0x09: POP(a); POP(a); vm->pc = pc + 1; break;
        /* 2.2 scalar memory, region known (and the short frame forms of 2.12) */
        case 0x10: TRY(load_scalar(vm, CL_ADDR(CL_R_STACK, vm->fp + OP16(2)), OP8(1), &x)); PUSH(x); vm->pc = pc + 4; break;
        case 0x80: TRY(load_scalar(vm, CL_ADDR(CL_R_STACK, vm->fp + OP8(2)), OP8(1), &x)); PUSH(x); vm->pc = pc + 3; break;
        case 0x82: TRY(load_scalar(vm, CL_ADDR(CL_R_STACK, vm->fp + OP8(1)), CL_T_U32, &x)); PUSH(x); vm->pc = pc + 2; break;
        case 0x11: POP(x); TRY(store_scalar(vm, CL_ADDR(CL_R_STACK, vm->fp + OP16(2)), OP8(1), x)); vm->pc = pc + 4; break;
        case 0x81: POP(x); TRY(store_scalar(vm, CL_ADDR(CL_R_STACK, vm->fp + OP8(2)), OP8(1), x)); vm->pc = pc + 3; break;
        case 0x83: POP(x); TRY(store_scalar(vm, CL_ADDR(CL_R_STACK, vm->fp + OP8(1)), CL_T_U32, x)); vm->pc = pc + 2; break;
        case 0x12: TRY(load_scalar(vm, CL_ADDR(CL_R_SESSION, OP32(2)), OP8(1), &x)); PUSH(x); vm->pc = pc + 6; break;
        case 0x13: POP(x); TRY(store_scalar(vm, CL_ADDR(CL_R_SESSION, OP32(2)), OP8(1), x)); vm->pc = pc + 6; break;
        case 0x14: TRY(load_scalar(vm, CL_ADDR(CL_R_CONST, OP32(2)), OP8(1), &x)); PUSH(x); vm->pc = pc + 6; break;
        case 0x15: TRY(load_scalar(vm, CL_ADDR(CL_R_PERSISTENT, OP32(2)), OP8(1), &x)); PUSH(x); vm->pc = pc + 6; break;
        case 0x16: POP(x); TRY(store_scalar(vm, CL_ADDR(CL_R_PERSISTENT, OP32(2)), OP8(1), x)); vm->pc = pc + 6; break;
        /* 2.3 addresses */
        case 0x18: {
            uint32_t r = OP8(1), off = OP32(2);
            PUSH(CL_ADDR(r, r == CL_R_STACK ? vm->fp + off : off)); vm->pc = pc + 6; break;
        }
        case 0x84: PUSH(CL_ADDR(CL_R_STACK, vm->fp + OP8(1))); vm->pc = pc + 2; break;     /* ADDRF */
        case 0x19: POP(x); POP(a); if (x >= OP32(3)) { trap = CL_TRAP_BOUNDS; goto trapped; }
                   PUSH(a + x * OP16(1)); vm->pc = pc + 7; break;                           /* INDEX */
        case 0x1A: POP(x); POP(b); POP(a); if (x >= b) { trap = CL_TRAP_BOUNDS; goto trapped; }
                   PUSH(a + x * OP16(1)); vm->pc = pc + 3; break;                           /* INDEXV */
        case 0x1B: POP(a); PUSH(a + OP16(1)); vm->pc = pc + 3; break;                      /* FIELD */
        /* 2.4 indirect */
        case 0x20: POP(a); TRY(load_scalar(vm, a, OP8(1), &x)); PUSH(x); vm->pc = pc + 2; break;
        case 0x21: POP(x); POP(a); TRY(store_scalar(vm, a, OP8(1), x)); vm->pc = pc + 2; break;
        /* 2.5 views */
        case 0x24: PUSH(OP32(1)); vm->pc = pc + 5; break;                                  /* VIEW */
        case 0x25: case 0x85: {                                                              /* SLICE, SLICEF */
            uint32_t size = OP16(1), s, en, n, base;
            if (op == 0x25) { POP(en); POP(s); POP(n); POP(base); vm->pc = pc + 3; }
            else {
                TRY(load_scalar(vm, CL_ADDR(CL_R_STACK, vm->fp + OP8(3)), CL_T_U32, &base));
                TRY(load_scalar(vm, CL_ADDR(CL_R_STACK, vm->fp + OP8(3) + 4), CL_T_U32, &n));
                TRY(load_scalar(vm, CL_ADDR(CL_R_STACK, vm->fp + OP8(4)), CL_T_U32, &s));
                en = n; vm->pc = pc + 5;
            }
            if (s > en || en > n) { trap = CL_TRAP_BOUNDS; goto trapped; }
            PUSH(base + s * size); PUSH(en - s); break;
        }
        /* 2.6 blocks */
        case 0x28: POP(b); POP(a); TRY(cl_charge(vm, cl_blocks(OP32(1)))); TRY(copy(vm, a, b, OP32(1))); vm->pc = pc + 5; break;
        case 0x29: {                                                                         /* COPYV */
            POP(d); POP(c); POP(b); POP(a);                  /* a n=b s=c m=d */
            if (b != d) { trap = CL_TRAP_BOUNDS; goto trapped; }
            uint64_t sz = (uint64_t)b * OP16(1);
            if (sz > 0x1FFFFFFFu) { trap = CL_TRAP_VM; goto trapped; }
            TRY(cl_charge(vm, cl_blocks((uint32_t)sz)));
            if (CL_TAG(a) == CL_R_PERSISTENT && sz > cl_hal_atomic_capacity(vm->hal)) { trap = CL_TRAP_TXN_CAPACITY; goto trapped; }
            TRY(copy(vm, a, c, (uint32_t)sz)); vm->pc = pc + 3; break;
        }
        case 0x2A: {                                                                         /* FILL */
            unsigned t = OP8(1); uint32_t count = OP32(2); uint8_t pat[4];
            POP(x); POP(a); put32(pat, x);
            TRY(cl_charge(vm, cl_blocks(WIDTH[t] * count))); TRY(write_pattern(vm, a, pat, WIDTH[t], count));
            vm->pc = pc + 6; break;
        }
        case 0x2B: {                                                                         /* FILLB */
            uint32_t size = OP16(1), count = OP32(3);
            POP(b); POP(a);
            TRY(cl_charge(vm, cl_blocks(size * count)));
            for (uint32_t i = 0; i < count; i++) TRY(copy(vm, a + i * size, b, size));
            vm->pc = pc + 7; break;
        }
        case 0x2C: case 0x2D: {                                                              /* ZERO, WIPE */
            static const uint8_t zero[1] = {0};
            POP(a); TRY(cl_charge(vm, cl_blocks(OP32(1)))); TRY(write_pattern(vm, a, zero, 1, OP32(1))); vm->pc = pc + 5; break;
        }
        case 0x2E: {                                                                         /* WIPEV */
            static const uint8_t zero[1] = {0};
            POP(b); POP(a);
            uint64_t sz = (uint64_t)b * OP16(1);
            if (sz > 0x1FFFFFFFu) { trap = CL_TRAP_VM; goto trapped; }
            TRY(cl_charge(vm, cl_blocks((uint32_t)sz)));
            if (CL_TAG(a) == CL_R_PERSISTENT && sz > cl_hal_atomic_capacity(vm->hal)) { trap = CL_TRAP_TXN_CAPACITY; goto trapped; }
            TRY(write_pattern(vm, a, zero, 1, (uint32_t)sz)); vm->pc = pc + 3; break;
        }
        case 0x2F: {                                                                         /* EQUAL, constant time */
            uint32_t size = OP16(1);
            POP(d); POP(c); POP(b); POP(a);                  /* a n=b, c m=d */
            uint64_t n1 = (uint64_t)b * size, n2 = (uint64_t)d * size;
            if (n1 > 0x1FFFFFFFu || n2 > 0x1FFFFFFFu) { trap = CL_TRAP_VM; goto trapped; }
            TRY(cl_charge(vm, cl_blocks((uint32_t)n1) + cl_blocks((uint32_t)n2)));
            uint32_t common = (uint32_t)(n1 < n2 ? n1 : n2), diff = 0;
            uint8_t ba[32], bb[32];
            for (uint32_t done = 0; done < common; ) {
                uint32_t k = common - done < 32u ? common - done : 32u;
                TRY(cl_read(vm, a + done, ba, k)); TRY(cl_read(vm, c + done, bb, k));
                for (uint32_t i = 0; i < k; i++) diff |= (uint32_t)(ba[i] ^ bb[i]);   /* no early exit (PLT-31) */
                done += k;
            }
            PUSH((uint32_t)(b == d && diff == 0)); vm->pc = pc + 3; break;
        }
        case 0x30: {                                                                         /* COMPARE */
            unsigned t = OP8(1); uint32_t w = WIDTH[t];
            POP(d); POP(c); POP(b); POP(a);
            TRY(cl_charge(vm, cl_blocks(b * w) + cl_blocks(d * w)));
            int r = 0; uint32_t n = b < d ? b : d;
            for (uint32_t i = 0; i < n && r == 0; i++) {
                uint32_t xa, xb;
                TRY(load_scalar(vm, a + i * w, t, &xa)); TRY(load_scalar(vm, c + i * w, t, &xb));
                int64_t va = val(xa, t), vb = val(xb, t);
                r = va < vb ? -1 : va > vb ? 1 : 0;
            }
            if (r == 0) r = b < d ? -1 : b > d ? 1 : 0;
            PUSH(norm(r, CL_T_I8)); vm->pc = pc + 2; break;
        }
        case 0x31: {                                                                         /* ENCODE */
            unsigned t = OP8(1); bool be = OP8(2) == 0; uint32_t w = WIDTH[t]; uint8_t buf[4];
            POP(x); POP(a);
            for (uint32_t i = 0; i < w; i++) buf[be ? w - 1 - i : i] = (uint8_t)(x >> (8 * i));
            TRY(cl_write(vm, a, buf, w)); vm->pc = pc + 3; break;
        }
        case 0x32: {                                                                         /* DECODE */
            unsigned t = OP8(1); bool be = OP8(2) == 0; uint32_t w = WIDTH[t]; uint8_t buf[4];
            POP(b); POP(a);
            if (b != w) { trap = CL_TRAP_BOUNDS; goto trapped; }
            TRY(cl_read(vm, a, buf, w));
            uint32_t raw = 0;
            for (uint32_t i = 0; i < w; i++) raw |= (uint32_t)buf[be ? w - 1 - i : i] << (8 * i);
            PUSH(norm((int64_t)raw, t)); vm->pc = pc + 3; break;
        }
        /* 2.7 arithmetic */
        case 0x40: case 0x41: case 0x42: case 0x43: case 0x44:
        case 0x49: case 0x4A: case 0x4B: case 0x4C: case 0x4D: {
            unsigned t = OP8(1); bool checked = op >= 0x49; unsigned kind = (unsigned)(checked ? op - 0x49 : op - 0x40);
            POP(b); POP(a);
            int64_t xv = val(a, t), yv = val(b, t), r = 0; int err = 0;
            if (kind >= 3 && yv == 0) err = CL_TRAP_DIV_ZERO;
            else {
                if (kind == 0) r = xv + yv;
                else if (kind == 1) r = xv - yv;
                else if (kind == 2) {
                    if (is_signed(t)) r = xv * yv;
                    else { uint64_t u = (uint64_t)xv * (uint64_t)yv; r = u > 0xFFFFFFFFull ? (int64_t)0x100000000ll : (int64_t)u; }
                }
                else if (kind == 3) r = xv / yv;                     /* C truncates toward zero (EXP-24) */
                else r = xv % yv;                                    /* the sign of the dividend */
                if (!in_range(r, t)) err = r > 0 ? CL_TRAP_OVERFLOW : CL_TRAP_UNDERFLOW;
            }
            if (checked) {
                static const uint16_t codes[] = {0, 0x0001, 0x0002, 0x0003};
                if (err) { vm->out_cat = 2; vm->out_code = codes[err]; PUSH(0); }
                else { vm->out_cat = 0; vm->out_code = 0; PUSH(norm(r, t)); }
            } else {
                if (err) { trap = err; goto trapped; }
                PUSH(norm(r, t));
            }
            vm->pc = pc + 2; break;
        }
        case 0x45: case 0x4E: {                                                              /* NEG, CNEG */
            unsigned t = OP8(1); POP(a);
            int64_t r = -val(a, t);
            if (!in_range(r, t)) {
                if (op == 0x45) { trap = CL_TRAP_NEGATION; goto trapped; }
                vm->out_cat = 2; vm->out_code = 0x0001; PUSH(0);
            } else {
                if (op == 0x4E) { vm->out_cat = 0; vm->out_code = 0; }
                PUSH(norm(r, t));
            }
            vm->pc = pc + 2; break;
        }
        case 0x46: case 0x47: case 0x48: {                                                   /* WADD, WSUB, WMUL */
            unsigned t = OP8(1); POP(b); POP(a);
            uint32_t r = op == 0x46 ? a + b : op == 0x47 ? a - b : a * b;   /* modulo 2^32, then normalized */
            PUSH(norm((int64_t)r, t)); vm->pc = pc + 2; break;
        }
        case 0x50: POP(b); POP(a); PUSH(a & b); vm->pc = pc + 1; break;
        case 0x51: POP(b); POP(a); PUSH(a | b); vm->pc = pc + 1; break;
        case 0x52: POP(b); POP(a); PUSH(a ^ b); vm->pc = pc + 1; break;
        case 0x53: POP(a); PUSH(norm((int64_t)(uint32_t)~a, OP8(1))); vm->pc = pc + 2; break;
        case 0x54: case 0x55: {                                                              /* SHL, SHR */
            unsigned t = OP8(1); POP(b); POP(a);
            if (b >= 8u * WIDTH[t]) { trap = CL_TRAP_SHIFT; goto trapped; }
            PUSH(norm(op == 0x54 ? (int64_t)((uint64_t)a << b) : (int64_t)(a >> b), t)); vm->pc = pc + 2; break;
        }
        case 0x56: POP(b); POP(a); PUSH((uint32_t)(a == b)); vm->pc = pc + 1; break;
        case 0x57: POP(b); POP(a); PUSH((uint32_t)(a != b)); vm->pc = pc + 1; break;
        case 0x58: case 0x59: case 0x5A: case 0x5B: {
            unsigned t = OP8(1); POP(b); POP(a);
            int64_t xv = val(a, t), yv = val(b, t);
            bool r = op == 0x58 ? xv < yv : op == 0x59 ? xv <= yv : op == 0x5A ? xv > yv : xv >= yv;
            PUSH((uint32_t)r); vm->pc = pc + 2; break;
        }
        case 0x5C: POP(a); PUSH(a ^ 1u); vm->pc = pc + 1; break;                           /* BNOT */
        case 0x5D: {                                                                         /* CCONVERT */
            unsigned s = OP8(1), t = OP8(2); POP(a);
            int64_t v = val(a, s);
            if (in_range(v, t)) { vm->out_cat = 0; vm->out_code = 0; PUSH(norm(v, t)); }
            else { vm->out_cat = 2; vm->out_code = 0x0004; PUSH(0); }
            vm->pc = pc + 3; break;
        }
        case 0x5E: POP(a); PUSH(norm((int64_t)a, OP8(1))); vm->pc = pc + 2; break;         /* TRUNC */
        /* 2.8 control (and the 8-bit jumps of 2.12) */
        case 0x60: vm->pc = (uint32_t)((int64_t)pc + 3 + (int16_t)OP16(1)); break;
        case 0x61: case 0x62: POP(a);
            vm->pc = ((a == 0) == (op == 0x61)) ? (uint32_t)((int64_t)pc + 3 + (int16_t)OP16(1)) : pc + 3; break;
        case 0x88: vm->pc = (uint32_t)((int64_t)pc + 2 + (int8_t)OP8(1)); break;
        case 0x89: case 0x8A: POP(a);
            vm->pc = ((a == 0) == (op == 0x89)) ? (uint32_t)((int64_t)pc + 2 + (int8_t)OP8(1)) : pc + 2; break;
        case 0x63: {                                                                         /* SWITCH */
            uint32_t n = OP16(1), end = pc + 3 + 2 * n; POP(a);
            if (a >= n) { trap = CL_TRAP_VM; goto trapped; }
            vm->pc = (uint32_t)((int64_t)end + (int16_t)le16(code + pc + 3 + 2 * a)); break;
        }
        /* 2.9 calls and outcomes */
        case 0x68: {                                                                         /* CALL */
            func_t g = function(vm, OP16(1));
            uint32_t args = 4u * g.argc;
            if (vm->sp < args) { trap = CL_TRAP_VM; goto trapped; }
            uint32_t nfp = vm->sp - args;
            if (nfp > vm->stack_size || g.frame_size > vm->stack_size - nfp || 8u + args > g.frame_size) { trap = CL_TRAP_VM; goto trapped; }
            memmove(vm->stack + nfp + 8, vm->stack + nfp, args);                   /* the arguments become parameters */
            put32(vm->stack + nfp, pc + 3); put32(vm->stack + nfp + 4, vm->fp);
            memset(vm->stack + nfp + 8 + args, 0, g.frame_size - 8 - args);       /* defaults (BC-25) */
            vm->fp = nfp; vm->sp = nfp + g.operand_base; vm->pc = g.code; break;
        }
        case 0x69: case 0x6A: case 0x6B: case 0x6C: case 0x72: {                             /* RET RETV ERR FWD ERRRAISE */
            uint8_t cat = 0; uint16_t ecode = 0; bool has = false; uint32_t value = 0, cell = 0;
            if (op == 0x6A) { POP(value); has = true; }
            else if (op == 0x6B) { cat = OP8(1); ecode = OP16(2); }
            else if (op == 0x6C) { cat = vm->out_cat; ecode = vm->out_code; }
            else if (op == 0x72) { POP(cell); cat = (uint8_t)(cell >> 16); ecode = (uint16_t)cell; }
            bool ended = false;
            TRY(leave(vm, cat, ecode, has, value, &ended, &out));
            if (ended) return out;
            break;
        }
        case 0x6D: vm->pc = vm->out_cat ? (uint32_t)((int64_t)pc + 3 + (int16_t)OP16(1)) : pc + 3; break;
        case 0x8B: vm->pc = vm->out_cat ? (uint32_t)((int64_t)pc + 2 + (int8_t)OP8(1)) : pc + 2; break;
        case 0x6E: vm->pc = (vm->out_cat == OP8(1) && vm->out_code == OP16(2)) ? (uint32_t)((int64_t)pc + 6 + (int16_t)OP16(4)) : pc + 6; break;
        case 0x6F: vm->pc = vm->out_cat == OP8(1) ? (uint32_t)((int64_t)pc + 4 + (int16_t)OP16(2)) : pc + 4; break;
        case 0x70: PUSH(vm->out_code); vm->pc = pc + 1; break;                              /* ERRCODE */
        case 0x71: PUSH(((uint32_t)vm->out_cat << 16) | vm->out_code); vm->pc = pc + 1; break;   /* ERRGET */
        /* 2.10 transactions */
        case 0x74: TRY(cl_hal_trap(cl_hal_txn_begin(vm->hal))); vm->txn = 1; vm->pc = pc + 1; break;
        case 0x75: TRY(cl_hal_trap(cl_hal_txn_commit(vm->hal))); vm->txn = 0; vm->pc = pc + 1; break;
        case 0x76: TRY(cl_hal_trap(cl_hal_txn_abort(vm->hal))); vm->txn = 0; vm->pc = pc + 1; break;
        /* 2.11 natives */
        case 0x78: vm->pc = pc + 3; TRY(cl_native_call(vm, OP16(1))); break;
        default: trap = CL_TRAP_VM; goto trapped;
        }
    }

trapped:
    /* Cleanup after a trap (VEX-40). */
    if (vm->atomic) { (void)cl_hal_update_abort(vm->hal); vm->atomic = 0; }
    if (vm->txn) { (void)cl_hal_txn_abort(vm->hal); vm->txn = 0; }
    memset(vm->stack, 0, vm->stack_size);
    memset(vm->bounce, 0, CL_BOUNCE);
    if (trap == CL_TRAP_POWER_LOSS) {
        vm->state = CL_STATE_NO_SESSION;
        memset(vm->session, 0, vm->session_size);
        out.kind = CL_RESULT_NONE; return out;
    }
    out.kind = CL_RESULT_TRAP; out.code = (uint16_t)trap;
    return out;
}

/* ------------------------------------------------------------------ entry points (VEX-45) */
static cl_result misuse(void) { cl_result r = {0}; r.kind = CL_RESULT_MISUSE; return r; }
static cl_result ok_result(void) { cl_result r = {0}; r.kind = CL_RESULT_OK; return r; }

static cl_result handler(cl_vm *vm, int which) {
    if (vm->entry[which] == NONE_ENTRY) return ok_result();
    return run(vm, vm->entry[which], NULL, 0);
}

cl_result cl_vm_install(cl_vm *vm) {
    if (vm->state != CL_STATE_NOT_INSTALLED) return misuse();
    vm->state = CL_STATE_NO_SESSION;
    cl_result r = handler(vm, 1);
    if (r.kind != CL_RESULT_OK) vm->state = CL_STATE_NOT_INSTALLED;          /* BP-55 */
    return r;
}

static void end_session(cl_vm *vm) {
    memset(vm->session, 0, vm->session_size);
    (void)cl_hal_keys_drop(vm->hal, CL_STORAGE_VOLATILE);
    cl_natives_drop_session(vm);
}

cl_result cl_vm_session_start(cl_vm *vm) {
    if (vm->state == CL_STATE_NOT_INSTALLED) return misuse();
    end_session(vm); vm->state = CL_STATE_IN_SESSION;
    cl_result r = handler(vm, 2);
    if (r.kind != CL_RESULT_OK) vm->state = CL_STATE_UNAVAILABLE;            /* BP-55 */
    return r;
}

void cl_vm_session_end(cl_vm *vm) {
    if (vm->state == CL_STATE_NOT_INSTALLED) return;
    end_session(vm); vm->state = CL_STATE_NO_SESSION;
}

void cl_vm_security_reset(cl_vm *vm) { cl_vm_session_end(vm); }

cl_result cl_vm_select(cl_vm *vm, uint8_t *resp, uint32_t cap) {
    if (vm->entry[3] == NONE_ENTRY) return ok_result();
    vm->response = resp; vm->response_cap = cap;
    uint32_t cells[2] = {CL_ADDR(CL_R_RESPONSE, 0), cap};
    cl_result r = run(vm, vm->entry[3], cells, 2);
    vm->response = NULL; vm->response_cap = 0;
    return r;
}

cl_result cl_vm_command(cl_vm *vm, const uint8_t *req, uint32_t len, uint8_t *resp, uint32_t cap) {
    if (vm->state == CL_STATE_NOT_INSTALLED || vm->state == CL_STATE_NO_SESSION) return misuse();
    if (vm->state == CL_STATE_UNAVAILABLE) { cl_result r = {0}; r.kind = CL_RESULT_TRAP; return r; }   /* BP-55 */
    vm->request = req; vm->request_len = len; vm->response = resp; vm->response_cap = cap;
    uint32_t cells[4] = {CL_ADDR(CL_R_REQUEST, 0), len, CL_ADDR(CL_R_RESPONSE, 0), cap};
    cl_result r = run(vm, vm->entry[0], cells, 4);
    cl_natives_end_command(vm);                                               /* VEX-48, BP-14 */
    (void)cl_hal_keys_drop(vm->hal, CL_STORAGE_COMMAND);
    vm->request = NULL; vm->response = NULL; vm->request_len = vm->response_cap = 0;
    if (r.kind == CL_RESULT_OK && r.has_count && r.count > cap) {            /* HEP-9 */
        r.kind = CL_RESULT_TRAP; r.code = CL_TRAP_RESPONSE_COUNT; r.has_count = false;
    }
    return r;
}
