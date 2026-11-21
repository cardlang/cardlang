/*
 * hal_host.c - the host HAL: persistent storage with atomic updates, transactions and recovery, and the test hooks
 * (vm/hal.md HAL-15 to HAL-20, HAL-31). Step 2 of VM7; keys and cryptography follow in step 3.
 *
 * Recovery is immediate: a power loss injected at a commit (the interrupt hook) undoes the transaction, then the
 * call returns CL_FATAL, which the VM reports as "no result" (VEX-43, HAL-6).
 */
#include <string.h>
#include "hal_host.h"

void cl_host_hal_init(cl_hal *hal) {
    memset(hal, 0, sizeof *hal);
    static const char seed[] = "cardlang-test-drbg";            /* the prototype's default seed */
    memcpy(hal->seed, seed, sizeof seed - 1); hal->seed_len = (uint32_t)(sizeof seed - 1);
}

void cl_host_create_partition(cl_hal *hal, uint32_t size) {
    memset(hal->partition, 0, sizeof hal->partition);           /* a new partition reads as zero (HAL-15) */
    hal->exists = true; hal->size = size; hal->in_txn = false; hal->update.open = false;
}

void cl_host_delete_partition(cl_hal *hal) { hal->exists = false; hal->size = 0; hal->in_txn = false; }

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

cl_status cl_hal_txn_begin(cl_hal *hal) {
    if (hal->in_txn) return CL_FATAL;
    memcpy(hal->shadow, hal->partition, CL_HOST_PARTITION);
    hal->in_txn = true; hal->pending = 0;
    return CL_OK;
}

cl_status cl_hal_txn_commit(cl_hal *hal) {
    if (!hal->in_txn) return CL_FATAL;
    if (hal->interrupt) {                                      /* the test hook: power loss during the commit */
        hal->interrupt = false; hal->in_txn = false;            /* ...and recovery undoes the transaction */
        return CL_FATAL;
    }
    memcpy(hal->partition, hal->shadow, CL_HOST_PARTITION);
    hal->in_txn = false;
    return CL_OK;
}

cl_status cl_hal_txn_abort(cl_hal *hal) { hal->in_txn = false; return CL_OK; }

/* ------------------------------------------------------------------ keys: step 3 */
cl_status cl_hal_keys_drop(cl_hal *hal, cl_key_storage storage) { (void)hal; (void)storage; return CL_OK; }

/* ------------------------------------------------------------------ test hooks (HAL-31) */
cl_status cl_hal_test_seed(cl_hal *hal, const uint8_t *seed, uint32_t len) {
    if (len > sizeof hal->seed) return CL_ERR_CAPACITY;
    memcpy(hal->seed, seed, len); hal->seed_len = len; hal->counter = 0;
    return CL_OK;
}

cl_status cl_hal_test_interrupt_next_commit(cl_hal *hal) { hal->interrupt = true; return CL_OK; }
