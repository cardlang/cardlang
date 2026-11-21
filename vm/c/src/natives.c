/*
 * natives.c - the native library (HAL-3): the catalog APIs as NATIVE n executes them (vm/bytecode.md section 5).
 * VM7 step 2: the numbering only. The APIs arrive in step 3, with the keys and crypto of the host HAL.
 */
#include "vm_internal.h"

/* The native numbers the VM knows (BC-32): 1 to 36, and the test-only catalog from 0xF000 in test builds (V-33). */
bool cl_native_known(uint16_t number, bool test_natives) {
    if (number >= 1 && number <= 36) return true;
    return test_natives && number >= 0xF000 && number <= 0xF004;
}

int cl_native_call(cl_vm *vm, uint16_t number) {
    (void)vm; (void)number;
    return CL_TRAP_VM;                      /* step 3 */
}

void cl_natives_end_command(cl_vm *vm) { (void)vm; }
void cl_natives_drop_session(cl_vm *vm) { (void)vm; }
