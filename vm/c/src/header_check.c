/*
 * header_check.c - VM7 step 1: the VM's public headers compile, warning-free, on both compilers (J1).
 * It also pins the sizes and values the interface documents (vm/hal.md HAL-7, HAL-30).
 */
#include "cl_hal.h"
#include "cl_hal_test.h"

_Static_assert(sizeof(cl_status) == 2, "cl_status is 16 bits (HAL-7)");
_Static_assert(CL_ERR_MALFORMED == 0x0021, "CardError codes follow profile section 4 (HAL-7)");
_Static_assert(CL_FATAL == 0x01FF, "the VM-level statuses (HAL-7)");
_Static_assert(CL_KEY_HMAC256 == 4, "profile enums by ordinal (HAL-30)");
_Static_assert(CL_HAL_OP_CTX_SIZE >= 1 && (CL_HAL_OP_CTX_ALIGN & (CL_HAL_OP_CTX_ALIGN - 1u)) == 0,
               "an operation context has a size and a power-of-two alignment (HAL-27)");

/* Something for the library to contain until the VM's own sources arrive. */
cl_status cl_header_check(void) { return CL_OK; }
