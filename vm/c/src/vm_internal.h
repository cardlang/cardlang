/*
 * vm_internal.h - helpers shared by the interpreter (vm.c) and the native library (natives.c). Not public.
 *
 * Convention: a helper that can fail returns an int "trap code": 0 for success, a cl_trap kind for a trap, or
 * CL_TRAP_POWER_LOSS when the HAL reports CL_FATAL (a power loss or an uncontained failure: no result, VEX-43).
 */
#ifndef CL_VM_INTERNAL_H
#define CL_VM_INTERNAL_H

#include "cl_vm.h"

#define CL_TRAP_POWER_LOSS 0x100

/* Region tags (VEX-7) and addresses (VEX-11). */
enum { CL_R_CONST = 0, CL_R_PERSISTENT = 1, CL_R_SESSION = 2, CL_R_STACK = 3, CL_R_REQUEST = 4, CL_R_RESPONSE = 5 };
#define CL_ADDR(tag, off) ((((uint32_t)(tag)) << 29) | ((uint32_t)(off) & 0x1FFFFFFFu))
#define CL_TAG(a) ((a) >> 29)
#define CL_OFF(a) ((a) & 0x1FFFFFFFu)

/* Type codes (BC-3). */
enum { CL_T_U8 = 0, CL_T_U16, CL_T_U32, CL_T_I8, CL_T_I16, CL_T_I32 };

int cl_hal_trap(cl_status s);                       /* a HAL status as a trap code (BC-37) */
int cl_read(cl_vm *vm, uint32_t a, uint8_t *dst, uint32_t n);
int cl_write(cl_vm *vm, uint32_t a, const uint8_t *src, uint32_t n);
int cl_push(cl_vm *vm, uint32_t cell);
int cl_pop(cl_vm *vm, uint32_t *cell);
int cl_charge(cl_vm *vm, uint32_t n);               /* the budget (VEX-42) */
uint32_t cl_blocks(uint32_t bytes);                 /* ceil(bytes / 16), the per-byte charge (BC-35) */

/* The native library (natives.c): BC-21 and VEX-48. */
int cl_native_call(cl_vm *vm, uint16_t number);
void cl_natives_end_command(cl_vm *vm);
void cl_natives_drop_session(cl_vm *vm);
bool cl_native_known(uint16_t number, bool test_natives);

#endif
