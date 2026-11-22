/*
 * cl_hal.h - the CardLang VM's hardware abstraction layer (draft).
 *
 * The HAL provides persistent storage with atomic updates and transactions, the key store, every cryptographic
 * operation of Base Profile 1, and randomness. The VM and its native library perform no cryptography (HAL-1).
 * Requirements: vm/hal.md (HAL-n). Every function is synchronous (HAL-4), takes a context bound to one
 * application (HAL-5), and returns a cl_status (HAL-7). On any status other than CL_OK or CL_FATAL, nothing has
 * changed (HAL-8).
 *
 * C11, freestanding-compatible: only <stdbool.h>, <stddef.h> and <stdint.h>.
 */
#ifndef CL_HAL_H
#define CL_HAL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ------------------------------------------------------------------ status (HAL-7) */

typedef uint16_t cl_status;

#define CL_OK                    ((cl_status)0x0000)
/* CardError codes, profile section 4. */
#define CL_ERR_OVERFLOW          ((cl_status)0x0001)
#define CL_ERR_UNDERFLOW         ((cl_status)0x0002)
#define CL_ERR_DIVISION_BY_ZERO  ((cl_status)0x0003)
#define CL_ERR_CONVERSION_RANGE  ((cl_status)0x0004)
#define CL_ERR_NOT_FOUND         ((cl_status)0x0010)
#define CL_ERR_ALREADY_EXISTS    ((cl_status)0x0011)
#define CL_ERR_WRONG_RESOURCE    ((cl_status)0x0012)
#define CL_ERR_INVALID_STATE     ((cl_status)0x0013)
#define CL_ERR_CAPACITY          ((cl_status)0x0014)
#define CL_ERR_UNSUPPORTED       ((cl_status)0x0020)
#define CL_ERR_MALFORMED         ((cl_status)0x0021)
/* Statuses that the VM turns into traps or a security reset. */
#define CL_TXN_CAPACITY          ((cl_status)0x0100)   /* trap(TXN-CAPACITY): VEX-29, TXN-16, BP-24 */
#define CL_COMMIT_FAILED         ((cl_status)0x0101)   /* trap(COMMIT), transaction rolled back: TXN-12 */
#define CL_FATAL                 ((cl_status)0x01FF)   /* no result; the platform performs a security reset */

/* ------------------------------------------------------------------ the context (HAL-5) */

/* Opaque, defined by the port, bound to one application's storage partition and key namespace. */
typedef struct cl_hal cl_hal;

/* ------------------------------------------------------------------ data descriptors (HAL-11 to HAL-14) */

typedef struct cl_in cl_in;
typedef struct cl_out cl_out;

/* An input: contiguous bytes (ptr != NULL), or a reader for data in persistent storage. */
struct cl_in {
    const uint8_t *ptr;
    uint32_t len;
    /* Copy n bytes starting at offset off of the input into dst. Used only when ptr == NULL. */
    cl_status (*read)(const cl_in *in, uint32_t off, uint8_t *dst, uint32_t n);
    void *ctx;
};

/* An output: contiguous bytes (ptr != NULL), or a writer for data in persistent storage. */
struct cl_out {
    uint8_t *ptr;
    uint32_t cap;
    /* Store n bytes at offset off of the output. Used only when ptr == NULL. */
    cl_status (*write)(const cl_out *out, uint32_t off, const uint8_t *src, uint32_t n);
    void *ctx;
};

/* ------------------------------------------------------------------ profile enums, by ordinal (HAL-30) */

typedef enum { CL_KEY_AES128 = 0, CL_KEY_AES256 = 1, CL_KEY_EC_P256_PRIVATE = 2, CL_KEY_EC_P256_PUBLIC = 3,
               CL_KEY_HMAC256 = 4 } cl_key_type;
typedef enum { CL_STORAGE_PERSISTENT = 0, CL_STORAGE_VOLATILE = 1, CL_STORAGE_COMMAND = 2 } cl_key_storage;
typedef enum { CL_DIGEST_SHA256 = 0 } cl_digest_alg;
typedef enum { CL_MAC_HMAC_SHA256 = 0 } cl_mac_alg;
typedef enum { CL_SIG_ECDSA_P256_SHA256 = 0 } cl_sig_alg;
typedef enum { CL_KDF_HKDF_SHA256 = 0 } cl_kdf_alg;
typedef enum { CL_CIPHER_AES_CBC_NO_PADDING = 0 } cl_cipher_alg;
typedef enum { CL_ENCRYPT = 0, CL_DECRYPT = 1 } cl_direction;

/* ------------------------------------------------------------------ persistent storage (HAL-15 to HAL-20) */

uint32_t  cl_hal_storage_size(cl_hal *hal);                                   /* HAL-15 */
uint32_t  cl_hal_atomic_capacity(cl_hal *hal);                                /* HAL-17 */
cl_status cl_hal_read(cl_hal *hal, uint32_t off, uint8_t *dst, uint32_t n);   /* HAL-16 */

cl_status cl_hal_update_begin(cl_hal *hal, uint32_t off, uint32_t len);       /* HAL-17; CL_TXN_CAPACITY */
cl_status cl_hal_update_write(cl_hal *hal, uint32_t off, const uint8_t *src, uint32_t n);
cl_status cl_hal_update_end(cl_hal *hal);
cl_status cl_hal_update_abort(cl_hal *hal);

cl_status cl_hal_copy(cl_hal *hal, uint32_t dst_off, uint32_t src_off, uint32_t n);   /* HAL-18 */

cl_status cl_hal_txn_begin(cl_hal *hal);                                      /* HAL-19 */
cl_status cl_hal_txn_commit(cl_hal *hal);                                     /* CL_COMMIT_FAILED */
cl_status cl_hal_txn_abort(cl_hal *hal);

/* ------------------------------------------------------------------ keys (HAL-21 to HAL-23) */

cl_status cl_hal_key_info(cl_hal *hal, uint32_t id, cl_key_type *type, cl_key_storage *storage);
cl_status cl_hal_key_generate(cl_hal *hal, uint32_t id, cl_key_type type, cl_key_storage storage);
cl_status cl_hal_key_import(cl_hal *hal, uint32_t id, cl_key_type type, cl_key_storage storage,
                            const cl_in *material);
cl_status cl_hal_key_export_public(cl_hal *hal, uint32_t id, const cl_out *out, uint32_t *written);
cl_status cl_hal_key_delete(cl_hal *hal, uint32_t id);
cl_status cl_hal_keys_drop(cl_hal *hal, cl_key_storage storage);              /* Volatile or Command */

/* ------------------------------------------------------------------ one-shot cryptography (HAL-25) */

cl_status cl_hal_digest(cl_hal *hal, cl_digest_alg alg, const cl_in *data, const cl_out *out, uint32_t *written);
cl_status cl_hal_mac(cl_hal *hal, uint32_t key, cl_mac_alg alg, const cl_in *data, const cl_out *out,
                     uint32_t *written);
cl_status cl_hal_sign(cl_hal *hal, uint32_t key, cl_sig_alg alg, const cl_in *message, const cl_out *out,
                      uint32_t *written);
cl_status cl_hal_verify(cl_hal *hal, uint32_t key, cl_sig_alg alg, const cl_in *message, const cl_in *signature,
                        bool *valid);
cl_status cl_hal_sign_digest(cl_hal *hal, uint32_t key, cl_sig_alg alg, const cl_in *digest, const cl_out *out,
                             uint32_t *written);                              /* BP-29 */
cl_status cl_hal_verify_digest(cl_hal *hal, uint32_t key, cl_sig_alg alg, const cl_in *digest,
                               const cl_in *signature, bool *valid);         /* BP-29 */
cl_status cl_hal_agree(cl_hal *hal, uint32_t key, const cl_in *peer, const cl_out *out, uint32_t *written);
cl_status cl_hal_derive(cl_hal *hal, cl_kdf_alg alg, const cl_in *secret, const cl_in *salt, const cl_in *info,
                        uint32_t length, const cl_out *out, uint32_t *written);
cl_status cl_hal_cipher(cl_hal *hal, uint32_t key, cl_cipher_alg alg, cl_direction direction, const cl_in *iv,
                        const cl_in *input, const cl_out *out, uint32_t *written);

/* ------------------------------------------------------------------ multi-part cryptography (HAL-26, HAL-27) */

/* The size and alignment of the largest operation context, defined by the port. */
#ifndef CL_HAL_OP_CTX_SIZE
#define CL_HAL_OP_CTX_SIZE  256u
#endif
#ifndef CL_HAL_OP_CTX_ALIGN
#define CL_HAL_OP_CTX_ALIGN 8u
#endif

typedef enum { CL_OP_DIGEST = 0, CL_OP_MAC = 1, CL_OP_SIGN = 2, CL_OP_VERIFY = 3 } cl_op_purpose;

/* alg is the purpose's algorithm enum, by ordinal; key is ignored for CL_OP_DIGEST. */
cl_status cl_hal_op_begin(cl_hal *hal, void *ctx, cl_op_purpose purpose, uint32_t key, unsigned alg);
cl_status cl_hal_op_update(cl_hal *hal, void *ctx, const cl_in *data);
cl_status cl_hal_op_finish(cl_hal *hal, void *ctx, const cl_out *out, uint32_t *written);
cl_status cl_hal_op_finish_verify(cl_hal *hal, void *ctx, const cl_in *signature, bool *valid);
cl_status cl_hal_op_abort(cl_hal *hal, void *ctx);

/* ------------------------------------------------------------------ randomness (HAL-28) */

cl_status cl_hal_random(cl_hal *hal, const cl_out *out);

#ifdef __cplusplus
}
#endif

#endif /* CL_HAL_H */
