"""Acceptance criterion 3 (vm/decisions.md V-12): every valid, runtime and example program compiles to a version-0
image, and the image decodes cleanly (every function's code is a sequence of valid instructions).

Usage (from the repository root):
    python -I tools/vmproto/compile_all.py .
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "checkers", HERE.parent / "harness"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
import compiler, typer, isa, disasm

def decodes(image):
    h, funcs, _, _ = disasm.read_image(image)
    code = image[h["code_offset"]:h["code_offset"] + h["code_size"]]
    bounds = [f["code"] for f in funcs] + [len(code)]
    for i in range(len(funcs)):
        pc = bounds[i]
        while pc < bounds[i + 1]: pc += isa.decode(code, pc)[2]
        if pc != bounds[i + 1]: return False
    return True

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True
    for name, toks in typer.programs(repo):
        try:
            c = compiler.Compiler(toks); image = c.compile()
            problem = None if decodes(image) else "the image does not decode"
        except Exception as e:                       # a compiler limitation or bug, never a language error
            problem = f"{type(e).__name__}: {e}"[:200]
        ok &= problem is None
        print("PASS" if problem is None else "FAIL", name, "" if problem is None else "| " + problem)
    print("ALL PASS" if ok else "FAILURES")
