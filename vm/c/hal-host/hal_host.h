/*
 * hal_host.h - the host (PC) HAL for tests (VM7): the definition of struct cl_hal, and the platform-side calls a
 * loader makes. It follows vm/hal.md and mirrors the prototype's test HAL, tools/vmproto/hal.py.
 *
 * VM7 step 2: persistent storage (HAL-15 to HAL-20) and the test hooks (HAL-31). The key store and the
 * cryptography (Mbed TLS) arrive in step 3.
 */
#ifndef CL_HAL_HOST_H
#define CL_HAL_HOST_H

#include "cl_hal.h"
#include "cl_hal_test.h"

#define CL_HOST_PARTITION 65536u     /* the application's persistent partition (HAL-15) */
#define CL_HOST_ATOMIC 4096u         /* the largest destination of one atomic update (HAL-17) */
#define CL_HOST_TXN 65536u           /* bytes of pending writes a transaction can hold (HAL-19) */

struct cl_hal {
    uint8_t partition[CL_HOST_PARTITION];
    uint8_t shadow[CL_HOST_PARTITION];         /* the active transaction's view of the partition */
    bool exists, in_txn, interrupt;
    uint32_t size, pending;
    struct { bool open; uint32_t off, len; uint8_t data[CL_HOST_ATOMIC]; } update;
    uint8_t seed[64];
    uint32_t seed_len, counter;                 /* the deterministic generator of the test hook (HAL-31) */
};

/* The platform's loader (not VM calls): set up a HAL, and create or delete the application's partition. */
void cl_host_hal_init(cl_hal *hal);
void cl_host_create_partition(cl_hal *hal, uint32_t size);
void cl_host_delete_partition(cl_hal *hal);

#endif
