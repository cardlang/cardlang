"""The execution backends known to the harness (vm/decisions.md V-10).

A backend is built from a program's source files and returns a "card" object implementing the interface in
src/cardlang/harness/README.md. Building checks the program first: a program the checkers reject raises BuildError.
"""
import sys, pathlib


from cardlang.front.lexcheck import lex, header
from cardlang.front import consteval, expcheck, pltcheck

class BuildError(Exception):
    """The program does not compile: a compile error, or a profile error such as a binding mismatch."""

def tokens(files):
    return sum((lex(f.read_bytes()) for f in files), [])

def _interp(files, binding):
    from cardlang.interp import interp
    toks = tokens(files)
    pltcheck.check_binding(toks, binding)                                       # profile BP-50a, BP-52
    return interp.Card(toks)

def _pyvm(files, binding):
    from cardlang.pyvm import card
    pltcheck.check_binding(tokens(files), binding)                              # profile BP-50a, BP-52
    return card.VmCard(files, binding)

def _cvm(files, binding):
    from cardlang.harness import cvm_backend
    pltcheck.check_binding(tokens(files), binding)                              # profile BP-50a, BP-52
    return cvm_backend.CvmCard(files, binding)

BACKENDS = {
    "interp": _interp,          # the reference interpreter (src/cardlang/interp/interp.py)
    "pyvm": _pyvm,        # the compiler and the Python VM (cardlang.pyvm)
    "cvm": _cvm,                # the C VM (vm/c/), as built by CMake, through cffi
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
    except Exception as e:
        from cardlang.compiler import compiler
        if isinstance(e, compiler.InvalidProgram): raise BuildError(str(e)) from e     # the compiler refused it
        raise
