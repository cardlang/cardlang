"""Code size per step of a bytecode revision (VM7b; plans_and_notes/VM7b-measurements.md).

Compiles every valid, runtime and example program with the compiler's short forms switched on cumulatively, step
by step, and prints the code bytes for FIDO2, PIV and all programs at each step. The names are those of
Compiler.shorten. Usage (from the repository root):
    uv run python -I devel/measure/revision.py .
"""
import sys, pathlib, json
HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools" / d) for d in ("vmproto", "harness")]   # moved to devel/ in PR2
from cardlang.compiler import compiler, typer

VERSION_1 = ["frame", "addr", "slice", "push", "jump"]             # VM6 (V-38)
STEPS = [("version 1", VERSION_1), ("(e) LDFB, STFB", ["byte"]), ("(d) ADDRH", ["addr16"]), ("(b) compare and branch", ["cmpjump"]), ("(c) SLICEFK", ["slicek"]), ("(a) shared error exits", ["errexit"])]   # VM7b steps, in order (VM7b plan §3)

def sizes(repo, shorten):
    out = {"examples/fido2": 0, "examples/piv": 0, "all": 0}
    for name, toks in typer.programs(repo):
        c = compiler.Compiler(toks); c.shorten = set(shorten); c.compile()
        n = c.report["code"]; out["all"] += n
        if name in out: out[name] = n
    return out

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]).resolve(); on, rows = [], []
    for label, names in STEPS:
        on += names; rows.append({"step": label, **sizes(repo, on)})
    print(json.dumps(rows, indent=1))
