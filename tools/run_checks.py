"""Run every reference checker over the conformance tests it covers.

Usage (from the repository root), after building the C VM:
    uv run python -I vm/c/build.py all
    uv run python -I tools/run_checks.py

Exit status 0 means every test produced its expected result.
"""
import pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0] / "checkers"))   # find layout
import layout

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKERS = layout.at(ROOT).tools / "checkers"

# (checker, test glob or None for the checker's default, what it verifies)
RUNS = [
    ("lexcheck.py", None, "lexical results of every test, and every design-note code block"),
    ("typecheck.py", None, "chapter 4 type rules on typ-* tests"),
    ("consteval.py", None, "chapter 5 constant evaluation on cex-* tests"),
    ("expcheck.py", None, "chapter 6 expression typing on exp-* tests"),
    ("stmcheck.py", None, "chapter 7 statements on stm-* tests"),
    ("funcheck.py", None, "chapter 8 functions and references on fun-* tests"),
    ("outcheck.py", None, "chapter 9 outcomes and errors on out-* tests"),
    ("stacheck.py", None, "chapter 10 state on sta-* tests"),
    ("txncheck.py", None, "chapter 11 transactions on txn-* tests"),
    ("hepcheck.py", None, "chapter 12 host entry point on hep-* tests"),
    ("pltcheck.py", None, "Annex B catalog-dependent rules on plt-* tests"),
    # The full checker chain (pltcheck builds on all the others, adds the HEP-16 scaffold to
    # fragments and loads the test-only platform catalog) must accept every valid test and give the expected error for the
    # invalid tests of chapters 6 to 11.
    ("pltcheck.py", "valid/*", "full checker on every valid test"),
    ("pltcheck.py", "invalid/exp-*", "full checker on chapter 6 invalid tests"),
    ("pltcheck.py", "invalid/stm-*", "full checker on chapter 7 invalid tests"),
    ("pltcheck.py", "invalid/fun-*", "full checker on chapter 8 invalid tests"),
    ("pltcheck.py", "invalid/out-*", "full checker on chapter 9 invalid tests"),
    ("pltcheck.py", "invalid/sta-*", "full checker on chapter 10 invalid tests"),
    ("pltcheck.py", "invalid/txn-*", "full checker on chapter 11 invalid tests"),
    # Diagnostics with source positions (TL1): the front end the language server and `clc` use.
    ("poscheck.py", None, "diagnostics: valid programs clean; every error with its code at a position (TL1)"),
    ("../clc_check.py", None, "clc: check, build, disasm and run on the applets and scenarios (TL1)"),
    ("../vmproto/debug_check.py", None, "debug information: lines, variables, globals, traps; never changes the code (TL1)"),
    ("../lsp/lsp_check.py", None, "language server: a scripted editor session, diagnostics as you type (TL1)"),
    ("../lsp/semantic_check.py", None, "semantic colouring: every identifier has a kind; a pinned sample (TL1)"),
    ("../dap/dap_check.py", None, "debug adapter: breakpoints, stepping, stack, variables, traps (TL1)"),
    ("../vscode/check_extension.py", None, "VS Code extension: grammars, keywords and steps match the language (TL1)"),
    # References stay correct (PR1): links, anchors and named files in every document; paths only through layout.
    ("linkcheck.py", None, "links, anchors and named files in every document; repository paths only through layout (PR1)"),
    # Consistency of the specification text itself (SP14).
    ("speccheck.py", None, "rules, references, CE classes, traps, tables, fragments, B.12, D.2, D.3, index"),
    # The CardLang Base Profile (platform/), WP2.
    ("profilecheck.py", None, "Base Profile rules, CardError table, types and catalog"),
    # Annex A, checked mechanically (SP14): an Earley recognizer built from the EBNF in the annex.
    ("grammar.py", None, "Annex A derives every test except CE-SYN-1 ones"),
    ("grammar.py", "--notes", "Annex A derives every checker-accepted design-note block"),
    # The reference interpreter compiles each runtime test with pltcheck, then runs its scenario.
    ("../interp/interp.py", None, "runtime scenarios in language/conformance/runtime/"),
    # The prototype compiler (VM4): its static typer types every expression of every program it must compile.
    ("../vmproto/typer.py", None, "vmproto typer: every valid, runtime and example program fully typed"),
    ("../vmproto/compile_all.py", None, "vmproto compiler: every valid, runtime and example program compiles (V-12 item 3)"),
    # The prototype compiler and VM as a backend of the harness (VM5): the same scenarios (V-12).
    ("../harness/scenario.py", "--backend vmproto", "vmproto: runtime scenarios on the prototype VM (V-12 item 1)"),
    ("../vmproto/check_state.py", None, "vmproto: all VM state in its context, within 1 KiB (V-31, V-2)"),
    # The C VM (VM7), built by vm/c/build.py with both compilers, through cffi: the same scenarios.
    ("../vmproto/compile_all.py", "--backend cvm-msvc", "cvm-msvc: every compiled image loads in the C VM (V-12 item 3, K1)"),
    ("../vmproto/compile_all.py", "--backend cvm-clang", "cvm-clang: every compiled image loads in the C VM (V-12 item 3, K1)"),
    ("../harness/scenario.py", "--backend cvm-msvc", "cvm-msvc: runtime scenarios on the C VM, MSVC build"),
    ("../harness/scenario.py", "--backend cvm-clang", "cvm-clang: runtime scenarios on the C VM, clang build"),
]

# The example applets (PR4): each examples/<app>/check.py checks its applet independently of the applet's own logic,
# and every example scenario must pass, on every backend (V-12 item 2). They are found, not listed, so a new applet is
# checked as soon as its folder exists.
BACKENDS = ("interp", "vmproto", "cvm-msvc", "cvm-clang")

def example_runs():
    L = layout.at(ROOT)
    for check in sorted(L.examples.glob("*/check.py")):
        app = check.parent.name
        for b in BACKENDS:
            yield (check, f"--backend {b}", f"examples/{app} on {b}: a session, checked independently")
    for b in BACKENDS:
        yield (L.tools / "harness" / "example_scenarios.py", f"--backend {b}", f"every example scenario on {b}")

def label(script):
    """How a run's script is shown: a checker by its name, an applet's checker by its applet."""
    s = pathlib.Path(script)
    if s.name == "check.py": return f"{s.parent.name}/check.py"
    return s.name if s.is_absolute() else str(script)

def main():
    failures = 0
    for script, glob, what in RUNS + list(example_runs()):
        extra = glob.split() if glob else []                 # e.g. "--backend vmproto"
        cmd = [sys.executable, "-I", str(CHECKERS / script), str(ROOT)] + extra
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        lines = out.stdout.splitlines()
        passed = sum(1 for l in lines if l.startswith("PASS"))
        failed = [l for l in lines if l.startswith("FAIL")]
        crashed = out.returncode != 0
        status = "ok" if not failed and not crashed else "FAILED"
        print(f"[{status:6}] {label(script):13} {glob or '(default)':18} {passed:4} passed  - {what}")
        for l in failed:
            print("         " + l)
        if crashed:
            print("         checker crashed:\n" + out.stderr)
        failures += len(failed) + (1 if crashed else 0)
    print("ALL CHECKS PASSED" if failures == 0 else f"{failures} FAILURE(S)")
    return 0 if failures == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
