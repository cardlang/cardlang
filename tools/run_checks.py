"""Run every reference checker over the conformance tests it covers.

Usage (from the repository root):
    python -I tools/run_checks.py

Exit status 0 means every test produced its expected result.
"""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKERS = ROOT / "tools" / "checkers"

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
    # The reference interpreter compiles each runtime test with pltcheck, then runs its scenario.
    ("../interp/interp.py", None, "runtime scenarios in conformance/runtime/"),
]

def main():
    failures = 0
    for script, glob, what in RUNS:
        cmd = [sys.executable, "-I", str(CHECKERS / script), str(ROOT)] + ([glob] if glob else [])
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        lines = out.stdout.splitlines()
        passed = sum(1 for l in lines if l.startswith("PASS"))
        failed = [l for l in lines if l.startswith("FAIL")]
        crashed = out.returncode != 0
        status = "ok" if not failed and not crashed else "FAILED"
        print(f"[{status:6}] {script:13} {glob or '(default)':18} {passed:4} passed  - {what}")
        for l in failed:
            print("         " + l)
        if crashed:
            print("         checker crashed:\n" + out.stderr)
        failures += len(failed) + (1 if crashed else 0)
    print("ALL CHECKS PASSED" if failures == 0 else f"{failures} FAILURE(S)")
    return 0 if failures == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
