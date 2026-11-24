"""The `cvm` backend of the harness: the C VM, driven through cffi.

A program is compiled by the compiler (src/cardlang/compiler/compiler.py) into a version-1 image, which the C VM loads
through its shared library (vm/c/test/cvm.c): cvm.dll, cvm.so or cvm.dylib, in the lib/ folder of a CMake build tree.
The tree is vm/c/build, or the one CARDLANG_CVM_BUILD names (a relative path is taken from the repository root).
The card interface is that of src/cardlang/harness/README.md, so scenarios and the applet checks run unchanged.
Build the library first, with any C11 toolchain:
    cmake -S vm/c -B vm/c/build
    cmake --build vm/c/build
"""
import os, sys, pathlib
from cffi import FFI

from cardlang.compiler import compiler
from cardlang.bytecode import isa
from cardlang.platform.errors import CARD_ERROR_CODES
import sys, pathlib
from cardlang import layout

CDEF = """
typedef struct { uint8_t kind; uint8_t category; uint16_t code; bool has_count; uint32_t count; } cl_result;
typedef struct cvm cvm;
uint32_t cvm_context_size(void);
uint32_t cvm_op_context_size(void);
cvm *cvm_new(const uint8_t *image, uint32_t size, uint32_t budget, int binding, int *load_status);
void cvm_free(cvm *c);
void cvm_install(cvm *c, cl_result *out);
void cvm_session_start(cvm *c, cl_result *out);
void cvm_session_end(cvm *c);
void cvm_reset(cvm *c);
void cvm_deselect(cvm *c);
void cvm_select(cvm *c, uint8_t *resp, uint32_t cap, cl_result *out);
void cvm_command(cvm *c, const uint8_t *req, uint32_t len, uint8_t *resp, uint32_t cap, cl_result *out);
int cvm_seed(cvm *c, const uint8_t *seed, uint32_t len);
uint32_t cvm_budget_used(cvm *c);
void cvm_interrupt_next_commit(cvm *c);
"""
ffi = FFI(); ffi.cdef(CDEF)
_LIB = []
LIBRARY_NAMES = ("cvm.dll", "cvm.so", "cvm.dylib")
BUILD_HINT = "cmake -S vm/c -B vm/c/build, then cmake --build vm/c/build"

class NotBuilt(SystemExit):
    """The C VM's shared library is not in the build tree."""

def build_tree():
    """The CMake build tree of the C VM: CARDLANG_CVM_BUILD, or vm/c/build."""
    L = layout.at(); named = os.environ.get("CARDLANG_CVM_BUILD")
    if not named: return L.vm_c / "build"
    tree = pathlib.Path(named)
    return tree if tree.is_absolute() else L.root / tree

def library_path():
    """The C VM's shared library in the build tree, or None if it is not built."""
    return next((f for f in (build_tree() / "lib" / n for n in LIBRARY_NAMES) if f.exists()), None)

def library():
    if not _LIB:
        path = library_path()
        if path is None:
            raise NotBuilt(f"the C VM is not built in {build_tree()}: run {BUILD_HINT}")
        try:
            _LIB.append(ffi.dlopen(str(path)))
        except OSError as e:
            bits = 64 if sys.maxsize > 2**32 else 32
            raise NotBuilt(f"{path} does not load: {e}. It must be built for this Python, a {bits}-bit process, "
                           f"with a C compiler that targets the same architecture") from e
    return _LIB[0]

RESULT_OK, RESULT_ERR, RESULT_TRAP, RESULT_NONE, RESULT_MISUSE = range(5)
TRAPS = {1: "OVERFLOW", 2: "UNDERFLOW", 3: "DIV-ZERO", 4: "NEGATION", 5: "SHIFT", 6: "BOUNDS", 7: "RESPONSE-COUNT",
         8: "TXN-CAPACITY", 9: "COMMIT", 10: "NESTED-TXN", 11: "EXHAUSTED", 12: "VM"}
LOAD = ["OK", "FORMAT", "PROFILE", "LAYOUT", "AREAS", "STORAGE", "ATOMIC", "NATIVE"]
CARD_ERROR_NAMES = {v: k for k, v in CARD_ERROR_CODES.items()}

class CvmCard:
    def __init__(self, files, binding=None, budget=1_000_000, fragment=False):
        self.lib = library()
        self.image = compiler.compile_files(files, binding, fragment).image
        status = ffi.new("int *")
        c = self.lib.cvm_new(self.image, len(self.image), budget, isa.BINDINGS[binding], status)
        if c == ffi.NULL: raise RuntimeError(f"cl_vm_load failed: {LOAD[status[0]] if status[0] < len(LOAD) else status[0]}")
        self.c = ffi.gc(c, self.lib.cvm_free)

    def outcome(self, r, response=None):
        k = r.kind
        if k == RESULT_OK:
            return ("ok", list(bytes(ffi.buffer(response, r.count))) if (response is not None and r.has_count) else [])
        if k == RESULT_ERR:
            return ("err", "app", r.code) if r.category == isa.CAT_APP else ("err", "platform", CARD_ERROR_NAMES[r.code])
        if k == RESULT_TRAP: return ("trap", TRAPS.get(r.code))
        if k == RESULT_NONE: return ("none",)
        raise RuntimeError("an entry called in the wrong lifecycle state")

    def _call(self, fn, *args):
        out = ffi.new("cl_result *"); fn(self.c, *args, out); return out[0]

    def install(self): return self.outcome(self._call(self.lib.cvm_install))
    def session_start(self): return self.outcome(self._call(self.lib.cvm_session_start))
    def session_end(self): self.lib.cvm_session_end(self.c)
    def reset(self): self.lib.cvm_reset(self.c)
    def deselect(self): self.lib.cvm_deselect(self.c)
    def seed(self, data): self.lib.cvm_seed(self.c, bytes(data), len(data))
    def interrupt_next_commit(self): self.lib.cvm_interrupt_next_commit(self.c)
    def budget_used(self): return self.lib.cvm_budget_used(self.c)      # by the last entry (measurement)

    def select(self):
        resp = ffi.new("uint8_t[]", 256)
        return self.outcome(self._call(self.lib.cvm_select, resp, 256), resp)

    def command(self, request, capacity):
        req = bytes(request); resp = ffi.new("uint8_t[]", max(capacity, 1))
        r = self._call(self.lib.cvm_command, req, len(req), resp, capacity)
        return self.outcome(r, resp)

def load_status(image):
    """What cl_vm_load says of an image, by name: "OK" or the IMG-11 check that failed."""
    lib = library(); status = ffi.new("int *")
    binding = image[7] or 1                               # an image for any binding is loaded as ISO 7816
    c = lib.cvm_new(image, len(image), 1_000_000, binding, status)
    if c != ffi.NULL: lib.cvm_free(c)
    return LOAD[status[0]] if status[0] < len(LOAD) else str(status[0])

def context_size():
    return library().cvm_context_size()

def op_context_size():
    return library().cvm_op_context_size()
