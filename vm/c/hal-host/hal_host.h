/*
 * hal_host.h - the host (PC) HAL for tests: the definition of struct cl_hal, and the platform-side calls a
 * loader makes. It follows vm/hal.md and mirrors the Python VM's test HAL, src/cardlang/pyvm/hal.py:
 * - persistent storage with atomic updates, transactions, recovery and the interrupt hook (HAL-15 to HAL-20);
 * - the key store, whose persistent keys join transactions (HAL-21 to HAL-23);
 * - every cryptographic operation, through Mbed TLS's PSA Crypto API, and the deterministic generator of the
 *   test hook (HAL-28, HAL-31);
 * - the fictional resources of the test-only catalog (V-33).
 *
 * Keys are kept as raw material and imported into PSA, as volatile keys, only for the length of one call. So a
 * transaction's snapshot of the key store is a plain copy, and every backend computes with the same keys.
 */
#ifndef CL_HAL_HOST_H
#define CL_HAL_HOST_H

#include "cl_hal.h"
#include "cl_hal_test.h"

#define CL_HOST_PARTITION 65536u     /* the application's persistent partition (HAL-15) */
#define CL_HOST_ATOMIC 4096u         /* the largest destination of one atomic update (HAL-17) */
#define CL_HOST_TXN 65536u           /* bytes of pending writes a transaction can hold (HAL-19) */
#define CL_HOST_PKEYS 8u             /* persistent keys (BP-25) */
#define CL_HOST_VKEYS 4u             /* volatile and command keys together (BP-25) */
#define CL_HOST_SCRATCH 0x11000u     /* the HAL's own memory for one result (HAL-11, HAL-13) */
#define CL_HOST_RESOURCES 4u         /* the test-only catalog's resources */

typedef struct {
    bool used;
    uint8_t type, storage, len;      /* cl_key_type, cl_key_storage, material length */
    uint32_t id, serial;             /* serial: which key this is, so an operation notices its key's deletion */
    uint8_t m[65];                   /* AES or HMAC bytes, a big-endian P-256 scalar, or an uncompressed point */
} cl_host_key;

struct cl_hal {
    uint8_t partition[CL_HOST_PARTITION];
    uint8_t shadow[CL_HOST_PARTITION];         /* the active transaction's view of the partition */
    bool exists, in_txn, interrupt;
    uint32_t size, pending;
    struct { bool open; uint32_t off, len; uint8_t data[CL_HOST_ATOMIC]; } update;
    uint8_t seed[64];
    uint32_t seed_len, counter;                 /* the deterministic generator of the test hook (HAL-31) */
    cl_host_key pkeys[CL_HOST_PKEYS], vkeys[CL_HOST_VKEYS];
    cl_host_key saved[CL_HOST_PKEYS];           /* the persistent keys as they were when the transaction began */
    uint32_t serial;
    struct { bool used; uint32_t id, kind, value; } res[CL_HOST_RESOURCES];
    uint8_t in[3][CL_HOST_PARTITION];           /* persistent inputs, read whole */
    uint8_t out[CL_HOST_SCRATCH];               /* a result, before it is written (HAL-8, HAL-13) */
};

/* The host's operation context (HAL-27) is a PSA hash or MAC operation and its bookkeeping. The build passes one
 * CL_HAL_OP_CTX_SIZE to the VM and the HAL; hal_host.c checks that it is large enough. This is its actual size. */
uint32_t cl_host_op_size(void);

/* The platform's loader (not VM calls): set up a HAL, and create or delete the application's partition. */
bool cl_host_hal_init(cl_hal *hal);             /* false if the crypto library cannot start */
void cl_host_create_partition(cl_hal *hal, uint32_t size);
void cl_host_delete_partition(cl_hal *hal);

#endif
