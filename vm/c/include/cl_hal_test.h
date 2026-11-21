/*
 * cl_hal_test.h - test hooks of a CardLang test HAL (draft, VM2; vm/hal.md HAL-31).
 *
 * Every test backend provides these, so that the same scenarios run on every VM (vm/decisions.md V-10, V-12).
 * A production HAL does not provide them.
 */
#ifndef CL_HAL_TEST_H
#define CL_HAL_TEST_H

#include "cl_hal.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Make the random generator deterministic from this seed, for every later call (the `seed` scenario step). */
cl_status cl_hal_test_seed(cl_hal *hal, const uint8_t *seed, uint32_t len);

/* Make the next commit behave as a power loss during the commit, followed by recovery (the `interrupt` step). */
cl_status cl_hal_test_interrupt_next_commit(cl_hal *hal);

/* The fictional resources of the test-only catalog (card.test.*, conformance/platform/test-catalog.txt, V-33): at
 * most 4, each with a kind (1 a counter, 2 a key) and a value. They share the identifier space (PLT-20).
 * create: CL_ERR_ALREADY_EXISTS, then CL_ERR_CAPACITY. The others: CL_ERR_NOT_FOUND. */
cl_status cl_hal_test_resource_create(cl_hal *hal, uint32_t id, uint32_t kind);
cl_status cl_hal_test_resource_get(cl_hal *hal, uint32_t id, uint32_t *kind, uint32_t *value);
cl_status cl_hal_test_resource_set(cl_hal *hal, uint32_t id, uint32_t value);
cl_status cl_hal_test_resource_delete(cl_hal *hal, uint32_t id);

#ifdef __cplusplus
}
#endif

#endif /* CL_HAL_TEST_H */
