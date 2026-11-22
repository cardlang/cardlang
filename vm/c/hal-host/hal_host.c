/*
 * hal_host.c - the host HAL (vm/hal.md), a port of the prototype's src/cardlang/pyvm/hal.py:
 * - storage with atomic updates, transactions and recovery (HAL-15 to HAL-20). Recovery is immediate: a power loss
 *   injected at a commit (the interrupt hook) undoes the transaction, then the call returns CL_FATAL, which the VM
 *   reports as "no result" (VEX-43, HAL-6);
 * - the key store (HAL-21 to HAL-23);
 * - cryptography through Mbed TLS (J2): PSA Crypto for hashes, HMAC, deterministic ECDSA (RFC 6979, as the
 *   prototype), ECDH and AES-CBC; mbedtls_hkdf for HKDF; and the bignum module to reduce generated EC scalars;
 * - the deterministic generator of the test hook: SHA-256(seed || counter), as the prototype (HAL-31);
 * - the resources of the test-only catalog (V-33).
 *
 * Every function computes its result into the HAL's own memory first, and checks the output's capacity last
 * (HAL-8, HAL-10, HAL-13).
 */
#include <string.h>
#include "hal_host.h"
#include "psa/crypto.h"
#include "mbedtls/bignum.h"
#include "mbedtls/hkdf.h"
#include "mbedtls/md.h"

#define ECDSA PSA_ALG_DETERMINISTIC_ECDSA(PSA_ALG_SHA_256)
#define HMAC PSA_ALG_HMAC(PSA_ALG_SHA_256)

bool cl_host_hal_init(cl_hal *hal) {
    memset(hal, 0, sizeof *hal);
    static const char seed[] = "cardlang-test-drbg";            /* the prototype's default seed */
    memcpy(hal->seed, seed, sizeof seed - 1); hal->seed_len = (uint32_t)(sizeof seed - 1);
    return psa_crypto_init() == PSA_SUCCESS;
}

void cl_host_create_partition(cl_hal *hal, uint32_t size) {
    memset(hal->partition, 0, sizeof hal->partition);           /* a new partition reads as zero (HAL-15) */
    memset(hal->pkeys, 0, sizeof hal->pkeys);
    hal->exists = true; hal->size = size; hal->in_txn = false; hal->update.open = false;
}

void cl_host_delete_partition(cl_hal *hal) {
    hal->exists = false; hal->size = 0; hal->in_txn = false;
    memset(hal->pkeys, 0, sizeof hal->pkeys);
}

static uint8_t *view(cl_hal *hal) { return hal->in_txn ? hal->shadow : hal->partition; }

/* ------------------------------------------------------------------ storage */
uint32_t cl_hal_storage_size(cl_hal *hal) { (void)hal; return CL_HOST_PARTITION; }
uint32_t cl_hal_atomic_capacity(cl_hal *hal) { (void)hal; return CL_HOST_ATOMIC; }

cl_status cl_hal_read(cl_hal *hal, uint32_t off, uint8_t *dst, uint32_t n) {
    if (off > CL_HOST_PARTITION || n > CL_HOST_PARTITION - off) return CL_FATAL;
    memcpy(dst, view(hal) + off, n);                            /* an open update is invisible (HAL-20) */
    return CL_OK;
}

cl_status cl_hal_update_begin(cl_hal *hal, uint32_t off, uint32_t len) {
    if (hal->update.open || off > CL_HOST_PARTITION || len > CL_HOST_PARTITION - off) return CL_FATAL;
    if (len > CL_HOST_ATOMIC) return CL_TXN_CAPACITY;
    if (hal->in_txn && hal->pending + len > CL_HOST_TXN) return CL_TXN_CAPACITY;
    hal->update.open = true; hal->update.off = off; hal->update.len = len;
    memcpy(hal->update.data, view(hal) + off, len);
    return CL_OK;
}

cl_status cl_hal_update_write(cl_hal *hal, uint32_t off, const uint8_t *src, uint32_t n) {
    if (!hal->update.open || off < hal->update.off || n > hal->update.len - (off - hal->update.off)) return CL_FATAL;
    memcpy(hal->update.data + (off - hal->update.off), src, n);
    return CL_OK;
}

cl_status cl_hal_update_end(cl_hal *hal) {
    if (!hal->update.open) return CL_FATAL;
    memcpy(view(hal) + hal->update.off, hal->update.data, hal->update.len);
    if (hal->in_txn) hal->pending += hal->update.len;
    hal->update.open = false;
    return CL_OK;
}

cl_status cl_hal_update_abort(cl_hal *hal) { hal->update.open = false; return CL_OK; }

cl_status cl_hal_copy(cl_hal *hal, uint32_t dst_off, uint32_t src_off, uint32_t n) {
    if (src_off > CL_HOST_PARTITION || n > CL_HOST_PARTITION - src_off) return CL_FATAL;
    cl_status s = cl_hal_update_begin(hal, dst_off, n);
    if (s != CL_OK) return s;
    memmove(hal->update.data, view(hal) + src_off, n);          /* the whole source first (HAL-18) */
    return cl_hal_update_end(hal);
}

/* Persistent key changes join the transaction (HAL-19, BP-24). */
cl_status cl_hal_txn_begin(cl_hal *hal) {
    if (hal->in_txn) return CL_FATAL;
    memcpy(hal->shadow, hal->partition, CL_HOST_PARTITION);
    memcpy(hal->saved, hal->pkeys, sizeof hal->pkeys);
    hal->in_txn = true; hal->pending = 0;
    return CL_OK;
}

cl_status cl_hal_txn_abort(cl_hal *hal) {
    if (hal->in_txn) memcpy(hal->pkeys, hal->saved, sizeof hal->pkeys);
    hal->in_txn = false;
    return CL_OK;
}

cl_status cl_hal_txn_commit(cl_hal *hal) {
    if (!hal->in_txn) return CL_FATAL;
    if (hal->interrupt) {                                      /* the test hook: power loss during the commit */
        hal->interrupt = false; (void)cl_hal_txn_abort(hal);    /* ...and recovery undoes the transaction */
        return CL_FATAL;
    }
    memcpy(hal->partition, hal->shadow, CL_HOST_PARTITION);
    hal->in_txn = false;
    return CL_OK;
}

/* ------------------------------------------------------------------ descriptors and the generator */

/* An input's bytes: its pointer, or a persistent input read whole into the HAL's memory (HAL-11). */
static const uint8_t *in_bytes(cl_hal *hal, const cl_in *in, unsigned slot, cl_status *s) {
    *s = CL_OK;
    if (in->ptr != NULL) return in->ptr;
    if (in->len > CL_HOST_PARTITION) { *s = CL_FATAL; return NULL; }
    if (in->len) *s = in->read(in, 0, hal->in[slot], in->len);
    return hal->in[slot];
}

#define IN(var, desc, slot) \
    cl_status s_##var; const uint8_t *var = in_bytes(hal, (desc), (slot), &s_##var); \
    if (s_##var != CL_OK) return s_##var

/* Write a computed result: capacity last (HAL-10). */
static cl_status put_out(const cl_out *out, const uint8_t *src, uint32_t n, uint32_t *written) {
    if (n > out->cap) return CL_ERR_CAPACITY;
    if (out->ptr != NULL) memmove(out->ptr, src, n);
    else if (n) { cl_status s = out->write(out, 0, src, n); if (s != CL_OK) return s; }
    if (written) *written = n;
    return CL_OK;
}

static cl_status drbg(cl_hal *hal, uint8_t *dst, uint32_t n) {
    uint8_t block[72], h[32];
    memcpy(block, hal->seed, hal->seed_len);
    for (uint32_t done = 0; done < n; ) {
        uint64_t c = hal->counter++;
        for (int i = 0; i < 8; i++) block[hal->seed_len + (uint32_t)i] = (uint8_t)(c >> (56 - 8 * i));
        size_t len = 0;
        if (psa_hash_compute(PSA_ALG_SHA_256, block, hal->seed_len + 8u, h, sizeof h, &len) != PSA_SUCCESS) return CL_FATAL;
        uint32_t k = n - done < 32u ? n - done : 32u;
        memcpy(dst + done, h, k); done += k;
    }
    memset(h, 0, sizeof h);
    return CL_OK;
}

/* ------------------------------------------------------------------ keys (HAL-21 to HAL-23) */
static cl_host_key *find(cl_hal *hal, uint32_t id) {
    for (unsigned i = 0; i < CL_HOST_PKEYS; i++) if (hal->pkeys[i].used && hal->pkeys[i].id == id) return &hal->pkeys[i];
    for (unsigned i = 0; i < CL_HOST_VKEYS; i++) if (hal->vkeys[i].used && hal->vkeys[i].id == id) return &hal->vkeys[i];
    return NULL;
}

static cl_host_key *by_serial(cl_hal *hal, uint32_t serial) {
    for (unsigned i = 0; i < CL_HOST_PKEYS; i++) if (hal->pkeys[i].used && hal->pkeys[i].serial == serial) return &hal->pkeys[i];
    for (unsigned i = 0; i < CL_HOST_VKEYS; i++) if (hal->vkeys[i].used && hal->vkeys[i].serial == serial) return &hal->vkeys[i];
    return NULL;
}

/* The key's material as a PSA volatile key, for one use. */
static psa_status_t load(uint8_t type, const uint8_t *m, uint32_t len, psa_algorithm_t alg, psa_key_usage_t usage,
                         psa_key_id_t *id) {
    psa_key_attributes_t a = PSA_KEY_ATTRIBUTES_INIT;
    switch (type) {
    case CL_KEY_AES128: case CL_KEY_AES256: psa_set_key_type(&a, PSA_KEY_TYPE_AES); break;
    case CL_KEY_HMAC256: psa_set_key_type(&a, PSA_KEY_TYPE_HMAC); break;
    case CL_KEY_EC_P256_PRIVATE: psa_set_key_type(&a, PSA_KEY_TYPE_ECC_KEY_PAIR(PSA_ECC_FAMILY_SECP_R1)); break;
    default: psa_set_key_type(&a, PSA_KEY_TYPE_ECC_PUBLIC_KEY(PSA_ECC_FAMILY_SECP_R1)); break;
    }
    psa_set_key_bits(&a, (type == CL_KEY_EC_P256_PRIVATE || type == CL_KEY_EC_P256_PUBLIC) ? 256u : len * 8u);
    psa_set_key_algorithm(&a, alg);
    psa_set_key_usage_flags(&a, usage);
    psa_status_t s = psa_import_key(&a, m, len, id);
    psa_reset_key_attributes(&a);
    return s;
}

static cl_status store(cl_hal *hal, uint32_t id, cl_key_type type, cl_key_storage storage, const uint8_t *m, uint32_t len) {
    bool persistent = storage == CL_STORAGE_PERSISTENT;
    cl_host_key *t = persistent ? hal->pkeys : hal->vkeys, *slot = NULL;
    unsigned cap = persistent ? CL_HOST_PKEYS : CL_HOST_VKEYS;
    for (unsigned i = 0; i < cap; i++) if (!t[i].used) { slot = &t[i]; break; }
    if (slot == NULL) return CL_ERR_CAPACITY;                    /* BP-25 */
    memset(slot, 0, sizeof *slot);
    slot->used = true; slot->id = id; slot->type = (uint8_t)type; slot->storage = (uint8_t)storage;
    slot->serial = ++hal->serial; slot->len = (uint8_t)len; memcpy(slot->m, m, len);
    return CL_OK;
}

cl_status cl_hal_key_info(cl_hal *hal, uint32_t id, cl_key_type *type, cl_key_storage *storage) {
    const cl_host_key *k = find(hal, id);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    *type = (cl_key_type)k->type; *storage = (cl_key_storage)k->storage;
    return CL_OK;
}

static const uint8_t P256_N_MINUS_1[32] = {
    0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xBC, 0xE6, 0xFA, 0xAD, 0xA7, 0x17, 0x9E, 0x84, 0xF3, 0xB9, 0xCA, 0xC2, 0xFC, 0x63, 0x25, 0x50};

/* The prototype's generation: random bytes for AES and HMAC; for P-256, d = 1 + (40 random bytes mod (n - 1)).
 * The generator runs before the capacity check, as in the prototype. */
cl_status cl_hal_key_generate(cl_hal *hal, uint32_t id, cl_key_type type, cl_key_storage storage) {
    uint8_t m[40];
    uint32_t len = type == CL_KEY_AES128 ? 16u : 32u;
    cl_status s;
    if (type == CL_KEY_EC_P256_PRIVATE) {
        if ((s = drbg(hal, m, 40)) != CL_OK) return s;
        mbedtls_mpi r, q;
        mbedtls_mpi_init(&r); mbedtls_mpi_init(&q);
        int e = mbedtls_mpi_read_binary(&r, m, 40);
        if (!e) e = mbedtls_mpi_read_binary(&q, P256_N_MINUS_1, 32);
        if (!e) e = mbedtls_mpi_mod_mpi(&r, &r, &q);
        if (!e) e = mbedtls_mpi_add_int(&r, &r, 1);
        if (!e) e = mbedtls_mpi_write_binary(&r, m, 32);
        mbedtls_mpi_free(&r); mbedtls_mpi_free(&q);
        if (e) return CL_FATAL;
    } else if ((s = drbg(hal, m, len)) != CL_OK) return s;
    s = store(hal, id, type, storage, m, len);
    memset(m, 0, sizeof m);
    return s;
}

cl_status cl_hal_key_import(cl_hal *hal, uint32_t id, cl_key_type type, cl_key_storage storage, const cl_in *material) {
    IN(m, material, 0);
    if (type == CL_KEY_EC_P256_PRIVATE || type == CL_KEY_EC_P256_PUBLIC) {     /* a valid scalar or point */
        psa_key_id_t k;
        if (load((uint8_t)type, m, material->len, ECDSA, PSA_KEY_USAGE_VERIFY_HASH, &k) != PSA_SUCCESS)
            return CL_ERR_MALFORMED;
        psa_destroy_key(k);
    }
    return store(hal, id, type, storage, m, material->len);
}

/* The public point of an EC key (65 bytes) into dst. */
static cl_status public_point(const cl_host_key *k, uint8_t *dst) {
    if (k->type == CL_KEY_EC_P256_PUBLIC) { memcpy(dst, k->m, 65); return CL_OK; }
    psa_key_id_t id; size_t n = 0;
    if (load(k->type, k->m, k->len, ECDSA, 0, &id) != PSA_SUCCESS) return CL_FATAL;
    psa_status_t s = psa_export_public_key(id, dst, 65, &n);
    psa_destroy_key(id);
    return s == PSA_SUCCESS && n == 65 ? CL_OK : CL_FATAL;
}

cl_status cl_hal_key_export_public(cl_hal *hal, uint32_t id, const cl_out *out, uint32_t *written) {
    const cl_host_key *k = find(hal, id);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    cl_status s = public_point(k, hal->out);
    return s != CL_OK ? s : put_out(out, hal->out, 65, written);
}

cl_status cl_hal_key_delete(cl_hal *hal, uint32_t id) {
    cl_host_key *k = find(hal, id);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    memset(k, 0, sizeof *k);
    return CL_OK;
}

/* Volatile: every volatile and command key (the session's end). Command: the command keys (BP-14). */
cl_status cl_hal_keys_drop(cl_hal *hal, cl_key_storage storage) {
    for (unsigned i = 0; i < CL_HOST_VKEYS; i++)
        if (storage == CL_STORAGE_VOLATILE || hal->vkeys[i].storage == storage) memset(&hal->vkeys[i], 0, sizeof hal->vkeys[i]);
    return CL_OK;
}

/* ------------------------------------------------------------------ one-shot cryptography (HAL-25) */
cl_status cl_hal_digest(cl_hal *hal, cl_digest_alg alg, const cl_in *data, const cl_out *out, uint32_t *written) {
    (void)alg;
    IN(d, data, 0);
    size_t n = 0;
    if (psa_hash_compute(PSA_ALG_SHA_256, d, data->len, hal->out, 32, &n) != PSA_SUCCESS) return CL_FATAL;
    return put_out(out, hal->out, 32, written);
}

cl_status cl_hal_mac(cl_hal *hal, uint32_t key, cl_mac_alg alg, const cl_in *data, const cl_out *out, uint32_t *written) {
    (void)alg;
    const cl_host_key *k = find(hal, key);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    IN(d, data, 0);
    psa_key_id_t id; size_t n = 0;
    if (load(k->type, k->m, k->len, HMAC, PSA_KEY_USAGE_SIGN_MESSAGE, &id) != PSA_SUCCESS) return CL_FATAL;
    psa_status_t s = psa_mac_compute(id, HMAC, d, data->len, hal->out, 32, &n);
    psa_destroy_key(id);
    return s != PSA_SUCCESS ? CL_FATAL : put_out(out, hal->out, 32, written);
}

static cl_status sign(cl_hal *hal, uint32_t key, bool hashed, const cl_in *in, const cl_out *out, uint32_t *written) {
    const cl_host_key *k = find(hal, key);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    IN(d, in, 0);
    psa_key_id_t id; size_t n = 0; psa_status_t s;
    if (load(k->type, k->m, k->len, ECDSA, hashed ? PSA_KEY_USAGE_SIGN_HASH : PSA_KEY_USAGE_SIGN_MESSAGE, &id) != PSA_SUCCESS)
        return CL_FATAL;
    s = hashed ? psa_sign_hash(id, ECDSA, d, in->len, hal->out, 64, &n)
               : psa_sign_message(id, ECDSA, d, in->len, hal->out, 64, &n);
    psa_destroy_key(id);
    return s != PSA_SUCCESS || n != 64 ? CL_FATAL : put_out(out, hal->out, 64, written);
}

/* An invalid signature, of any length, verifies as false: never an error (BP-29). */
static cl_status verify(cl_hal *hal, const cl_host_key *k, bool hashed, const uint8_t *d, uint32_t len,
                        const cl_in *signature, bool *valid) {
    *valid = false;
    IN(sig, signature, 1);
    if (signature->len != 64) return CL_OK;
    psa_key_id_t id;
    if (load(k->type, k->m, k->len, ECDSA, hashed ? PSA_KEY_USAGE_VERIFY_HASH : PSA_KEY_USAGE_VERIFY_MESSAGE, &id) != PSA_SUCCESS)
        return CL_FATAL;
    psa_status_t s = hashed ? psa_verify_hash(id, ECDSA, d, len, sig, 64) : psa_verify_message(id, ECDSA, d, len, sig, 64);
    psa_destroy_key(id);
    if (s == PSA_SUCCESS) { *valid = true; return CL_OK; }
    return (s == PSA_ERROR_INVALID_SIGNATURE || s == PSA_ERROR_INVALID_ARGUMENT) ? CL_OK : CL_FATAL;
}

cl_status cl_hal_sign(cl_hal *hal, uint32_t key, cl_sig_alg alg, const cl_in *message, const cl_out *out, uint32_t *written) {
    (void)alg; return sign(hal, key, false, message, out, written);
}

cl_status cl_hal_sign_digest(cl_hal *hal, uint32_t key, cl_sig_alg alg, const cl_in *digest, const cl_out *out,
                             uint32_t *written) {
    (void)alg; return sign(hal, key, true, digest, out, written);
}

cl_status cl_hal_verify(cl_hal *hal, uint32_t key, cl_sig_alg alg, const cl_in *message, const cl_in *signature, bool *valid) {
    (void)alg;
    const cl_host_key *k = find(hal, key);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    IN(d, message, 0);
    return verify(hal, k, false, d, message->len, signature, valid);
}

cl_status cl_hal_verify_digest(cl_hal *hal, uint32_t key, cl_sig_alg alg, const cl_in *digest, const cl_in *signature,
                               bool *valid) {
    (void)alg;
    const cl_host_key *k = find(hal, key);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    IN(d, digest, 0);
    return verify(hal, k, true, d, digest->len, signature, valid);
}

cl_status cl_hal_agree(cl_hal *hal, uint32_t key, const cl_in *peer, const cl_out *out, uint32_t *written) {
    const cl_host_key *k = find(hal, key);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    IN(p, peer, 0);
    if (peer->len != 65 || p[0] != 0x04) return CL_ERR_MALFORMED;        /* an uncompressed point */
    psa_key_id_t id; size_t n = 0;
    if (load(k->type, k->m, k->len, PSA_ALG_ECDH, PSA_KEY_USAGE_DERIVE, &id) != PSA_SUCCESS) return CL_FATAL;
    psa_status_t s = psa_raw_key_agreement(PSA_ALG_ECDH, id, p, 65, hal->out, 32, &n);
    psa_destroy_key(id);
    if (s == PSA_ERROR_INVALID_ARGUMENT) return CL_ERR_MALFORMED;        /* not on the curve */
    return s != PSA_SUCCESS || n != 32 ? CL_FATAL : put_out(out, hal->out, 32, written);
}

cl_status cl_hal_derive(cl_hal *hal, cl_kdf_alg alg, const cl_in *secret, const cl_in *salt, const cl_in *info,
                        uint32_t length, const cl_out *out, uint32_t *written) {
    (void)alg;
    IN(ikm, secret, 0); IN(sa, salt, 1); IN(inf, info, 2);
    if (length > 255u * 32u) return CL_ERR_MALFORMED;
    if (mbedtls_hkdf(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), sa, salt->len, ikm, secret->len, inf, info->len,
                     hal->out, length) != 0) return CL_FATAL;
    return put_out(out, hal->out, length, written);
}

cl_status cl_hal_cipher(cl_hal *hal, uint32_t key, cl_cipher_alg alg, cl_direction direction, const cl_in *iv,
                        const cl_in *input, const cl_out *out, uint32_t *written) {
    (void)alg;
    const cl_host_key *k = find(hal, key);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    IN(v, iv, 0); IN(d, input, 1);
    if (iv->len != 16 || input->len % 16) return CL_ERR_MALFORMED;
    if (input->len > CL_HOST_SCRATCH) return CL_ERR_CAPACITY;
    psa_key_id_t id; size_t n1 = 0, n2 = 0;
    if (load(k->type, k->m, k->len, PSA_ALG_CBC_NO_PADDING, PSA_KEY_USAGE_ENCRYPT | PSA_KEY_USAGE_DECRYPT, &id) != PSA_SUCCESS)
        return CL_FATAL;
    psa_cipher_operation_t op = PSA_CIPHER_OPERATION_INIT;
    psa_status_t s = direction == CL_ENCRYPT ? psa_cipher_encrypt_setup(&op, id, PSA_ALG_CBC_NO_PADDING)
                                             : psa_cipher_decrypt_setup(&op, id, PSA_ALG_CBC_NO_PADDING);
    if (s == PSA_SUCCESS) s = psa_cipher_set_iv(&op, v, 16);
    if (s == PSA_SUCCESS) s = psa_cipher_update(&op, d, input->len, hal->out, CL_HOST_SCRATCH, &n1);
    if (s == PSA_SUCCESS) s = psa_cipher_finish(&op, hal->out + n1, CL_HOST_SCRATCH - n1, &n2);
    psa_cipher_abort(&op);
    psa_destroy_key(id);
    if (s != PSA_SUCCESS || n1 + n2 != input->len) return CL_FATAL;
    return put_out(out, hal->out, input->len, written);
}

/* ------------------------------------------------------------------ multi-part cryptography (HAL-26, HAL-27) */
typedef struct {
    uint8_t purpose;                 /* cl_op_purpose */
    uint32_t serial;                 /* its key; 0 for a digest */
    union { psa_hash_operation_t hash; psa_mac_operation_t mac; } u;
} host_op;

_Static_assert(sizeof(host_op) <= CL_HAL_OP_CTX_SIZE, "CL_HAL_OP_CTX_SIZE holds a host operation (HAL-27)");
_Static_assert(_Alignof(host_op) <= CL_HAL_OP_CTX_ALIGN, "CL_HAL_OP_CTX_ALIGN aligns a host operation (HAL-27)");

uint32_t cl_host_op_size(void) { return (uint32_t)sizeof(host_op); }

/* Its key, or NULL once deleted, even if another key now has the same identifier (HAL-26). */
static const cl_host_key *op_key(cl_hal *hal, const host_op *o, bool *gone) {
    *gone = false;
    if (o->purpose == CL_OP_DIGEST) return NULL;
    const cl_host_key *k = by_serial(hal, o->serial);
    *gone = k == NULL;
    return k;
}

cl_status cl_hal_op_begin(cl_hal *hal, void *ctx, cl_op_purpose purpose, uint32_t key, unsigned alg) {
    (void)alg;
    host_op *o = (host_op *)ctx;
    memset(o, 0, sizeof *o);                       /* all-zero is a valid initial PSA operation */
    o->purpose = (uint8_t)purpose;
    if (purpose == CL_OP_DIGEST) return psa_hash_setup(&o->u.hash, PSA_ALG_SHA_256) == PSA_SUCCESS ? CL_OK : CL_FATAL;
    const cl_host_key *k = find(hal, key);
    if (k == NULL) return CL_ERR_NOT_FOUND;
    o->serial = k->serial;
    if (purpose != CL_OP_MAC) return psa_hash_setup(&o->u.hash, PSA_ALG_SHA_256) == PSA_SUCCESS ? CL_OK : CL_FATAL;
    psa_key_id_t id;
    if (load(k->type, k->m, k->len, HMAC, PSA_KEY_USAGE_SIGN_MESSAGE, &id) != PSA_SUCCESS) return CL_FATAL;
    psa_status_t s = psa_mac_sign_setup(&o->u.mac, id, HMAC);          /* the operation keeps what it needs */
    psa_destroy_key(id);
    return s == PSA_SUCCESS ? CL_OK : CL_FATAL;
}

cl_status cl_hal_op_update(cl_hal *hal, void *ctx, const cl_in *data) {
    host_op *o = (host_op *)ctx; bool gone;
    (void)op_key(hal, o, &gone);
    if (gone) return CL_ERR_INVALID_STATE;
    IN(d, data, 0);
    psa_status_t s = o->purpose == CL_OP_MAC ? psa_mac_update(&o->u.mac, d, data->len)
                                             : psa_hash_update(&o->u.hash, d, data->len);
    return s == PSA_SUCCESS ? CL_OK : CL_FATAL;
}

cl_status cl_hal_op_abort(cl_hal *hal, void *ctx) {
    (void)hal;
    host_op *o = (host_op *)ctx;
    if (o->purpose == CL_OP_MAC) psa_mac_abort(&o->u.mac); else psa_hash_abort(&o->u.hash);
    memset(o, 0, sizeof *o);
    return CL_OK;
}

cl_status cl_hal_op_finish(cl_hal *hal, void *ctx, const cl_out *out, uint32_t *written) {
    host_op *o = (host_op *)ctx; bool gone;
    const cl_host_key *k = op_key(hal, o, &gone);
    if (gone || o->purpose == CL_OP_VERIFY) return CL_ERR_INVALID_STATE;
    uint32_t size = o->purpose == CL_OP_SIGN ? 64u : 32u;
    if (out->cap < size) return CL_ERR_CAPACITY;    /* before finishing, so the context is unchanged (HAL-26) */
    size_t n = 0; psa_status_t s;
    if (o->purpose == CL_OP_DIGEST) s = psa_hash_finish(&o->u.hash, hal->out, 32, &n);
    else if (o->purpose == CL_OP_MAC) s = psa_mac_sign_finish(&o->u.mac, hal->out, 32, &n);
    else {
        uint8_t h[32]; psa_key_id_t id = 0;
        s = psa_hash_finish(&o->u.hash, h, 32, &n);
        if (s == PSA_SUCCESS) s = load(k->type, k->m, k->len, ECDSA, PSA_KEY_USAGE_SIGN_HASH, &id);
        if (s == PSA_SUCCESS) { s = psa_sign_hash(id, ECDSA, h, 32, hal->out, 64, &n); psa_destroy_key(id); }
    }
    (void)cl_hal_op_abort(hal, ctx);
    if (s != PSA_SUCCESS || n != size) return CL_FATAL;
    return put_out(out, hal->out, size, written);
}

cl_status cl_hal_op_finish_verify(cl_hal *hal, void *ctx, const cl_in *signature, bool *valid) {
    host_op *o = (host_op *)ctx; bool gone;
    const cl_host_key *k = op_key(hal, o, &gone);
    *valid = false;
    if (gone || o->purpose != CL_OP_VERIFY) return CL_ERR_INVALID_STATE;
    uint8_t h[32]; size_t n = 0;
    if (psa_hash_finish(&o->u.hash, h, 32, &n) != PSA_SUCCESS) { (void)cl_hal_op_abort(hal, ctx); return CL_FATAL; }
    (void)cl_hal_op_abort(hal, ctx);
    return verify(hal, k, true, h, 32, signature, valid);
}

/* ------------------------------------------------------------------ randomness (HAL-28) */
cl_status cl_hal_random(cl_hal *hal, const cl_out *out) {
    if (out->cap > CL_HOST_SCRATCH) return CL_ERR_CAPACITY;
    cl_status s = drbg(hal, hal->out, out->cap);
    return s != CL_OK ? s : put_out(out, hal->out, out->cap, NULL);
}

/* ------------------------------------------------------------------ test hooks (HAL-31) */
cl_status cl_hal_test_seed(cl_hal *hal, const uint8_t *seed, uint32_t len) {
    if (len > sizeof hal->seed) return CL_ERR_CAPACITY;
    memcpy(hal->seed, seed, len); hal->seed_len = len; hal->counter = 0;
    return CL_OK;
}

cl_status cl_hal_test_interrupt_next_commit(cl_hal *hal) { hal->interrupt = true; return CL_OK; }

static unsigned resource(cl_hal *hal, uint32_t id) {
    for (unsigned i = 0; i < CL_HOST_RESOURCES; i++) if (hal->res[i].used && hal->res[i].id == id) return i;
    return CL_HOST_RESOURCES;
}

cl_status cl_hal_test_resource_create(cl_hal *hal, uint32_t id, uint32_t kind) {
    if (resource(hal, id) < CL_HOST_RESOURCES) return CL_ERR_ALREADY_EXISTS;
    for (unsigned i = 0; i < CL_HOST_RESOURCES; i++)
        if (!hal->res[i].used) { hal->res[i].used = true; hal->res[i].id = id; hal->res[i].kind = kind; hal->res[i].value = 0; return CL_OK; }
    return CL_ERR_CAPACITY;
}

cl_status cl_hal_test_resource_get(cl_hal *hal, uint32_t id, uint32_t *kind, uint32_t *value) {
    unsigned i = resource(hal, id);
    if (i == CL_HOST_RESOURCES) return CL_ERR_NOT_FOUND;
    *kind = hal->res[i].kind; *value = hal->res[i].value;
    return CL_OK;
}

cl_status cl_hal_test_resource_set(cl_hal *hal, uint32_t id, uint32_t value) {
    unsigned i = resource(hal, id);
    if (i == CL_HOST_RESOURCES) return CL_ERR_NOT_FOUND;
    hal->res[i].value = value;
    return CL_OK;
}

cl_status cl_hal_test_resource_delete(cl_hal *hal, uint32_t id) {
    unsigned i = resource(hal, id);
    if (i == CL_HOST_RESOURCES) return CL_ERR_NOT_FOUND;
    memset(&hal->res[i], 0, sizeof hal->res[i]);
    return CL_OK;
}
