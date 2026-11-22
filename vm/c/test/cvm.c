/*
 * cvm.c - the shared library through which the test harness drives the C VM (VM7, J3: driven through cffi).
 *
 * It plays the platform, as src/cardlang/pyvm/card.py does for the prototype: it owns the image copy, the SESSION and
 * STACK areas and the host HAL, creates and deletes the partition, and tracks deselection (BP-56). The interface
 * uses only plain C types, so cffi's ABI mode can call it without a compiler. The declarations it exports are
 * repeated, for cffi, in src/cardlang/harness/cvm_backend.py.
 */
#include <stdlib.h>
#include <string.h>
#include "cl_vm.h"
#include "hal_host.h"

#if defined(_WIN32)
#define CVM_API __declspec(dllexport)
#else
#define CVM_API __attribute__((visibility("default")))
#endif

typedef struct cvm {
    cl_vm vm;
    cl_hal *hal;
    uint8_t *image, *session, *stack, *ops;
    uint32_t persistent_size;
    bool deselected;
} cvm;

static uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

CVM_API uint32_t cvm_context_size(void) { return (uint32_t)sizeof(cl_vm); }
CVM_API uint32_t cvm_op_context_size(void) { return cl_host_op_size(); }      /* the HAL's, not the VM's */

CVM_API void cvm_free(cvm *c) {
    if (c == NULL) return;
    free(c->hal); free(c->image); free(c->session); free(c->stack); free(c->ops); free(c);
}

CVM_API cvm *cvm_new(const uint8_t *image, uint32_t size, uint32_t budget, int binding, int *load_status) {
    *load_status = CL_LOAD_FORMAT;
    if (size < 72) return NULL;
    cvm *c = calloc(1, sizeof *c);
    if (c == NULL) return NULL;
    uint32_t session = le32(image + 16), stack = le32(image + 20);
    c->persistent_size = le32(image + 12);
    c->hal = malloc(sizeof *c->hal);
    c->image = malloc(size);
    c->session = calloc(session ? session : 1, 1);
    c->stack = calloc(stack ? stack : 1, 1);
    c->ops = malloc(CL_OP_SLOTS * CL_HAL_OP_CTX_SIZE);                 /* malloc aligns for any type (HAL-27) */
    if (!c->hal || !c->image || !c->session || !c->stack || !c->ops) { cvm_free(c); return NULL; }
    memcpy(c->image, image, size);
    if (!cl_host_hal_init(c->hal)) { cvm_free(c); return NULL; }
    cl_config cfg = {c->session, session, c->stack, stack, budget, (uint8_t)binding, true,
                     c->ops, CL_OP_SLOTS * CL_HAL_OP_CTX_SIZE};
    *load_status = (int)cl_vm_load(&c->vm, &cfg, c->image, size, c->hal);
    if (*load_status != CL_LOAD_OK) { cvm_free(c); return NULL; }
    return c;
}

CVM_API void cvm_install(cvm *c, cl_result *out) {
    cl_host_create_partition(c->hal, c->persistent_size);
    *out = cl_vm_install(&c->vm);
    if (out->kind != CL_RESULT_OK) cl_host_delete_partition(c->hal);       /* BP-55 */
}

CVM_API void cvm_session_start(cvm *c, cl_result *out) { c->deselected = false; *out = cl_vm_session_start(&c->vm); }
CVM_API void cvm_session_end(cvm *c) { cl_vm_session_end(&c->vm); }
CVM_API void cvm_reset(cvm *c) { cl_vm_security_reset(&c->vm); }
CVM_API void cvm_deselect(cvm *c) { cl_vm_session_end(&c->vm); c->deselected = true; }      /* BP-56 */

CVM_API void cvm_select(cvm *c, uint8_t *resp, uint32_t cap, cl_result *out) {
    if (c->deselected) {                                    /* the first SELECT after a deselection (BP-56) */
        c->deselected = false;
        *out = cl_vm_session_start(&c->vm);
        if (out->kind != CL_RESULT_OK) return;
    }
    *out = cl_vm_select(&c->vm, resp, cap);
}

CVM_API void cvm_command(cvm *c, const uint8_t *req, uint32_t len, uint8_t *resp, uint32_t cap, cl_result *out) {
    *out = cl_vm_command(&c->vm, req, len, resp, cap);
}

CVM_API uint32_t cvm_budget_used(cvm *c) { return c->vm.budget_cfg - c->vm.budget; }   /* by the last entry */

CVM_API int cvm_seed(cvm *c, const uint8_t *seed, uint32_t len) { return (int)cl_hal_test_seed(c->hal, seed, len); }
CVM_API void cvm_interrupt_next_commit(cvm *c) { (void)cl_hal_test_interrupt_next_commit(c->hal); }
