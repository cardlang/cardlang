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

#ifdef __cplusplus
}
#endif

#endif /* CL_HAL_TEST_H */
