"""The scenario runner shared by every CardLang execution backend (VM0, vm/decisions.md V-10).

A scenario (language/conformance/runtime/*/scenario.txt) is a list of steps and expectations. This module runs one against a
backend, a "card" built from a checked program, and compares host-visible results. The backend interface is
described in tools/harness/README.md; the backends are listed in backends.py.

Usage (from the repository root):
    python -I tools/harness/scenario.py . ["runtime/run-*"] [--backend NAME]
"""
import sys, pathlib, re
from cardlang import layout

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
from cardlang.platform.errors import CARD_ERROR_CODES          # kept importable from here

# ------------------------------------------------------------------ outcomes and the binding encodings
# An outcome is one of: ("ok", [bytes]), ("err", "app", code), ("err", "platform", CardError member name),
# ("trap", kind), or ("none",) when a power loss or a security reset leaves no response. The kind is None for a
# command to an application left unavailable by a failed on_session_start (profile BP-55).

def status_word(outcome):
    """The ISO 7816 binding's status word for an outcome (profile BP-51)."""
    if outcome is None or outcome[0] == "none": return None
    if outcome[0] == "ok": return 0x9000
    if outcome[0] == "trap": return 0x6F00
    if outcome[1] == "app": return outcome[2]
    return 0x6F00 + CARD_ERROR_CODES[outcome[2]]

def raw_envelope(outcome):
    """The raw binding's response envelope for an outcome (profile BP-53)."""
    if outcome is None or outcome[0] == "none": return None
    if outcome[0] == "ok": return [0x00, 0x00, 0x00] + outcome[1]
    if outcome[0] == "trap": return [0x03, 0x00, 0x00]
    code = outcome[2] if outcome[1] == "app" else CARD_ERROR_CODES[outcome[2]]
    return [0x01 if outcome[1] == "app" else 0x02, code >> 8, code & 0xFF]

def parse_expect(words):
    if words[0] == "sw": return ("sw", int(words[1], 16))
    if words[0] == "raw": return ("raw", [int(w, 16) for w in words[1:]])
    if words[0] == "ok": return ("ok", [int(w, 16) for w in words[1:]])
    if words[0] == "err" and words[1] == "app": return ("err", "app", int(words[2]))
    if words[0] == "err" and words[1] == "platform": return ("err", "platform", words[2])
    if words[0] == "trap": return ("trap", words[1] if len(words) > 1 else None)
    if words[0] == "none": return ("none",)
    raise ValueError(words)

# ------------------------------------------------------------------ the runner
def run_scenario(card, text, trace=None, before=None):
    """Run one scenario against a backend. Returns None on success, or a description of the first mismatch.
    trace, if given, is called after each step as trace(lineno, step, words, outcome); outcome is None for a step
    that has none, and for `expect` it is ("expect", want, got) (TL1: `clc run` and the debugger).
    before, if given, is called before each step as before(lineno, step, words): the debugger's scenario breakpoints."""
    pending = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#")[0].split()
        if not line: continue
        step = line[0]; previous = pending
        if before: before(lineno, step, line[1:])
        if step == "install": pending = card.install()                      # the outcome of on_install (BP-55)
        elif step in ("power_on", "session_start"): pending = card.session_start()   # STA-4; power_on is the ISO name
        elif step == "session_end": card.session_end()
        elif step == "reset": card.reset()
        elif step == "select": pending = card.select()
        elif step == "deselect": card.deselect()                            # another application selected (BP-56)
        elif step == "interrupt": card.interrupt_next_commit()
        elif step == "seed": card.seed(bytes.fromhex("".join(line[1:])))
        elif step == "command":
            words = line[1:]; capacity = 256
            if "capacity" in words:
                i = words.index("capacity"); capacity = int(words[i + 1]); words = words[:i]
            pending = card.command([int(w, 16) for w in words], capacity)
        elif step == "expect":
            want = parse_expect(line[1:])
            got = ("sw", status_word(pending)) if want[0] == "sw" else ("raw", raw_envelope(pending)) if want[0] == "raw" else pending
            if trace: trace(lineno, step, line[1:], ("expect", want, got))
            if got != want:
                return f"line {lineno}: expected {want}, got {got}"
            pending = None; continue
        else:
            return f"line {lineno}: unknown step {step}"
        if trace: trace(lineno, step, line[1:], pending if pending is not previous else None)
    return None

def program_files(d):
    """The source files of a test or example directory, in build order."""
    from cardlang.front import project                                      # src/cardlang/front: cardlang.json, or the .card files (TL1)
    return project.program_files(d)

def take_backend(argv, default="interp"):
    """Remove `--backend NAME` from argv; return (name, remaining arguments)."""
    argv = list(argv)
    if "--backend" in argv:
        i = argv.index("--backend"); name = argv[i + 1]; del argv[i:i + 2]
        return name, argv
    return default, argv

def main(argv, default_backend="interp"):
    import backends
    name, args = take_backend(argv, default_backend)
    repo = pathlib.Path(args[0]); glob = args[1] if len(args) > 1 else "runtime/run-*"
    ok = True
    for d in sorted((layout.at(repo).conformance).glob(glob)):
        try:
            card = backends.build(name, program_files(d))
            problem = run_scenario(card, (d / "scenario.txt").read_text(encoding="utf-8"))
        except backends.BuildError as e:
            problem = "does not compile: " + str(e)
        status = "PASS" if problem is None else "FAIL"; ok &= problem is None
        print(status, d.name, "" if problem is None else "| " + problem)
    print("ALL PASS" if ok else "FAILURES")

if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main(sys.argv[1:])
