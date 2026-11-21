"""The execution backends known to the harness (VM0, vm/decisions.md V-10).

A backend is built from a program's source files and returns a "card" object implementing the interface in
tools/harness/README.md. Building checks the program first: a program the checkers reject raises BuildError.
"""
import sys, pathlib

TOOLS = pathlib.Path(__file__).resolve().parents[1]
for sub in ("checkers", "interp", "harness"):
    if str(TOOLS / sub) not in sys.path: sys.path.insert(0, str(TOOLS / sub))

from lexcheck import lex, header
import consteval, expcheck, pltcheck

class BuildError(Exception):
    """The program does not compile: a compile error, or a profile error such as a binding mismatch."""

def tokens(files):
    return sum((lex(f.read_bytes()) for f in files), [])

def _interp(files, binding):
    import interp
    toks = tokens(files)
    pltcheck.check_binding(toks, binding)                                       # profile BP-50a, BP-52
    return interp.Card(toks)

def _vmproto(files, binding):
    if str(TOOLS / "vmproto") not in sys.path: sys.path.insert(0, str(TOOLS / "vmproto"))
    import card
    pltcheck.check_binding(tokens(files), binding)                              # profile BP-50a, BP-52
    return card.VmCard(files, binding)

def _cvm(toolchain):
    def build(files, binding):
        import cvm_backend
        pltcheck.check_binding(tokens(files), binding)                          # profile BP-50a, BP-52
        return cvm_backend.CvmCard(files, binding, toolchain)
    return build

BACKENDS = {
    "interp": _interp,          # the reference interpreter (tools/interp/interp.py)
    "vmproto": _vmproto,        # the prototype compiler and VM (tools/vmproto/, VM4 and VM5)
    "cvm-msvc": _cvm("msvc"),   # the C VM built with MSVC (vm/c/, VM7), through cffi
    "cvm-clang": _cvm("clang"), # the C VM built with clang from llvm-mingw
}

def build(name, files, binding=None):
    """Build a backend card. The binding defaults to the `binding:` header of the first file."""
    if name not in BACKENDS:
        raise SystemExit(f"unknown backend {name!r}; known: {', '.join(BACKENDS)}")
    try:
        if binding is None: binding = header(files[0].read_bytes()).get("binding")
        return BACKENDS[name](files, binding)
    except (expcheck.CE, consteval.CE, pltcheck.ProfileError) as e:
        raise BuildError(str(e)) from e
