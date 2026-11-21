/*
 * cl_vm.h - the CardLang VM's interface to the platform (VM7; vm/execution-model.md VEX-45 to VEX-50).
 *
 * The VM is a library (V-6): the platform's main loop owns the transport and calls these entry points. One
 * context runs one application (V-8). The VM allocates nothing and keeps no global state: everything it keeps is
 * in struct cl_vm (VEX-49), whose size is a compile-time constant (VEX-50). The image is read in place (IMG-12).
 *
 * C11, freestanding-compatible: only <stdbool.h>, <stddef.h> and <stdint.h>.
 */
#ifndef CL_VM_H
#define CL_VM_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "cl_hal.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ------------------------------------------------------------------ configuration (VEX-8) */

typedef struct {
    uint8_t *session;         /* the SESSION area */
    uint32_t session_size;
    uint8_t *stack;           /* the STACK area: frames and operand cells */
    uint32_t stack_size;
    uint32_t budget;          /* instructions per entry (VEX-42) */
    uint8_t binding;          /* 1 ISO 7816, 2 raw (IMG-4) */
    bool test_natives;        /* a test build: the test-only catalog's natives from 0xF000 (V-33) */
} cl_config;

/* ------------------------------------------------------------------ loading (IMG-11) */

typedef enum {
    CL_LOAD_OK = 0,
    CL_LOAD_FORMAT,           /* magic or format version */
    CL_LOAD_PROFILE,          /* profile or binding */
    CL_LOAD_LAYOUT,           /* image size, sections, entries or function table */
    CL_LOAD_AREAS,            /* SESSION or STACK larger than the configuration */
    CL_LOAD_STORAGE,          /* PERSISTENT larger than the HAL's partition */
    CL_LOAD_ATOMIC,           /* a static persistent destination above the atomic capacity */
    CL_LOAD_NATIVE            /* an imported native the VM does not provide */
} cl_load_status;

/* ------------------------------------------------------------------ results (VEX-25) */

typedef enum {
    CL_RESULT_OK = 0,         /* Ok; count is the payload, if has_count */
    CL_RESULT_ERR,            /* Err; category and code */
    CL_RESULT_TRAP,           /* a trap; code is the cl_trap kind (0 for an unavailable application, BP-55) */
    CL_RESULT_NONE,           /* no result: a power loss or an uncontained failure (VEX-43) */
    CL_RESULT_MISUSE          /* the platform called an entry in the wrong lifecycle state */
} cl_result_kind;

typedef struct {
    uint8_t kind;             /* cl_result_kind */
    uint8_t category;         /* for Err: 1 application, 2 platform (BC-2) */
    uint16_t code;            /* for Err: the error code; for a trap: the cl_trap kind */
    bool has_count;
    uint32_t count;
} cl_result;

/* Trap kinds (RTF-4). */
typedef enum {
    CL_TRAP_NONE = 0, CL_TRAP_OVERFLOW, CL_TRAP_UNDERFLOW, CL_TRAP_DIV_ZERO, CL_TRAP_NEGATION, CL_TRAP_SHIFT,
    CL_TRAP_BOUNDS, CL_TRAP_RESPONSE_COUNT, CL_TRAP_TXN_CAPACITY, CL_TRAP_COMMIT, CL_TRAP_NESTED_TXN,
    CL_TRAP_EXHAUSTED, CL_TRAP_VM
} cl_trap;

/* ------------------------------------------------------------------ the context (VEX-49) */

#define CL_BOUNCE 128u        /* the bounce buffer (V-22) */

typedef struct cl_vm {
    const uint8_t *image;
    uint32_t image_size;
    uint32_t code_off, code_size, const_off, const_size, func_off;
    uint16_t func_count;
    uint16_t entry[4];        /* command, on_install, on_session_start, on_select; 0xFFFF if absent */
    uint8_t *session;
    uint32_t session_size;
    uint8_t *stack;
    uint32_t stack_size;
    const uint8_t *request;
    uint32_t request_len;
    uint8_t *response;
    uint32_t response_cap;
    uint32_t pc, fp, sp;
    uint16_t out_code;
    uint8_t out_cat;
    uint8_t txn, atomic, state;
    uint32_t budget, budget_cfg;
    cl_hal *hal;
    uint8_t bounce[CL_BOUNCE];
} cl_vm;

/* Lifecycle states (VEX-44). */
enum { CL_STATE_NOT_INSTALLED = 0, CL_STATE_NO_SESSION, CL_STATE_IN_SESSION, CL_STATE_UNAVAILABLE };

/* ------------------------------------------------------------------ entry points (VEX-45) */

/* Set up the context and check the image's header (IMG-11). The image stays the platform's and is read in place. */
cl_load_status cl_vm_load(cl_vm *vm, const cl_config *config, const uint8_t *image, uint32_t size, cl_hal *hal);

/* The platform has created the application's persistent partition, which reads as zero (HAL-15). On a failed
 * on_install the application is not installed, and the platform deletes the partition (BP-55). */
cl_result cl_vm_install(cl_vm *vm);
cl_result cl_vm_session_start(cl_vm *vm);
void cl_vm_session_end(cl_vm *vm);
void cl_vm_security_reset(cl_vm *vm);

/* ISO 7816: run on_select, if declared, with RESPONSE mapped onto resp (BP-50a). */
cl_result cl_vm_select(cl_vm *vm, uint8_t *resp, uint32_t cap);

/* Run the command handler with REQUEST and RESPONSE mapped onto the platform's buffers (VEX-46). */
cl_result cl_vm_command(cl_vm *vm, const uint8_t *req, uint32_t len, uint8_t *resp, uint32_t cap);

#ifdef __cplusplus
}
#endif

#endif /* CL_VM_H */
