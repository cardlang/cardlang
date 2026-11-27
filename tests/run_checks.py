"""Run every reference checker over the conformance tests it covers.

Usage (from the repository root):
    uv run python -I tests/run_checks.py [--require-cvm]

The runs on the C VM need it built first (vm/c/README.md):
    cmake -S vm/c -B vm/c/build
    cmake --build vm/c/build
Without it, they are skipped and counted as skipped, not passed; --require-cvm (as in CI) makes them required.

Exit status 0 means every test produced its expected result.
"""
import pathlib, subprocess, sys
from cardlang import layout

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (checker, test glob or None for the checker's default, what it verifies). A checker is a module of the package, run
# with -m (a front-end module runs its chapter's conformance tests), or a script's path from the repository root.
RUNS = [
    ("cardlang.front.lexcheck", None, "lexical results of every test, and every design-note code block"),
    ("cardlang.front.namcheck", None, "chapter 3 name rules on nam-* tests"),
    ("cardlang.front.typecheck", None, "chapter 4 type rules on typ-* tests"),
    ("cardlang.front.consteval", None, "chapter 5 constant evaluation on cex-* tests"),
    ("cardlang.front.expcheck", None, "chapter 6 expression typing on exp-* tests"),
    ("cardlang.front.stmcheck", None, "chapter 7 statements on stm-* tests"),
    ("cardlang.front.funcheck", None, "chapter 8 functions and references on fun-* tests"),
    ("cardlang.front.outcheck", None, "chapter 9 outcomes and errors on out-* tests"),
    ("cardlang.front.stacheck", None, "chapter 10 state on sta-* tests"),
    ("cardlang.front.txncheck", None, "chapter 11 transactions on txn-* tests"),
    ("cardlang.front.hepcheck", None, "chapter 12 host entry point on hep-* tests"),
    ("cardlang.front.pltcheck", None, "Annex B catalog-dependent rules on plt-* tests"),
    # The full checker chain (pltcheck builds on all the others, adds the HEP-16 scaffold to
    # fragments and loads the test-only platform catalog) must accept every valid test and give the expected error for the
    # invalid tests of chapters 6 to 11.
    ("cardlang.front.pltcheck", "valid/*", "full checker on every valid test"),
    ("cardlang.front.pltcheck", "invalid/exp-*", "full checker on chapter 6 invalid tests"),
    ("cardlang.front.pltcheck", "invalid/stm-*", "full checker on chapter 7 invalid tests"),
    ("cardlang.front.pltcheck", "invalid/fun-*", "full checker on chapter 8 invalid tests"),
    ("cardlang.front.pltcheck", "invalid/out-*", "full checker on chapter 9 invalid tests"),
    ("cardlang.front.pltcheck", "invalid/sta-*", "full checker on chapter 10 invalid tests"),
    ("cardlang.front.pltcheck", "invalid/txn-*", "full checker on chapter 11 invalid tests"),
    # Diagnostics with source positions: the front end the language server and `clc` use.
    ("tests/poscheck.py", None, "diagnostics: valid programs clean; every error with its code at a position"),
    ("tests/clc_check.py", None, "clc: check, build, disasm and run on the applets and scenarios"),
    ("tests/debug_check.py", None, "debug information: lines, variables, globals, traps; never changes the code"),
    ("tests/lsp_check.py", None, "language server: a scripted editor session, diagnostics as you type"),
    ("tests/semantic_check.py", None, "semantic colouring: every identifier has a kind; a pinned sample"),
    ("tests/dap_check.py", None, "debug adapter: breakpoints, stepping, stack, variables, traps"),
    ("editors/vscode/check_extension.py", None, "VS Code extension: grammars, keywords and steps match the language"),
    ("tests/guidecheck.py", None, "the guide: every example compiles, fails as it says, or passes its scenario"),
    ("tests/guide_reference.py", "--check", "the guide's platform reference matches the catalog, the types, CardError and RTF-4"),
    # References stay correct: links, anchors and named files in every document; paths only through layout.
    ("tests/linkcheck.py", None, "links, anchors and named files in every document; repository paths only through layout"),
    # Consistency of the specification text itself.
    ("tests/speccheck.py", None, "rules and marks, references, CE classes, traps, tables, fragments, B.12, D.2, D.3, index, test marks"),
    # The CardLang Base Profile (platform/).
    ("tests/profilecheck.py", None, "Base Profile rules, CardError table, types and catalog"),
    # Annex A, checked mechanically: an Earley recognizer built from the EBNF in the annex.
    ("cardlang.front.grammar", None, "Annex A derives every test except CE-SYN-1 ones"),
    ("cardlang.front.grammar", "--notes", "Annex A derives every checker-accepted design-note block"),
    # The reference interpreter compiles each runtime test with pltcheck, then runs its scenario.
    ("cardlang.interp.interp", None, "runtime scenarios in language/conformance/runtime/"),
    # The compiler: its static typer types every expression of every program it must compile.
    ("cardlang.compiler.typer", None, "compiler typer: every valid, runtime and example program fully typed"),
    ("tests/compile_all.py", None, "compiler: every valid, runtime and example program compiles (V-12 item 3)"),
    # The compiler and the Python VM as a backend of the harness: the same scenarios (V-12).
    ("cardlang.harness.scenario", "--backend pyvm", "pyvm: runtime scenarios on the Python VM (V-12 item 1)"),
    ("tests/check_state.py", None, "pyvm: all VM state in its context, within 1 KiB (V-31, V-2)"),
    ("tests/card_check.py", None, "virtual card on pyvm: APDUs, the ISO 7816 transport, the examples behind it"),
    ("tests/fido2_client_check.py", None, "virtual card on pyvm: python-fido2's client and server against the FIDO2 applet"),
    # The C VM, as built by CMake with any C11 toolchain, through cffi: the same scenarios.
    ("tests/compile_all.py", "--backend cvm", "cvm: every compiled image loads in the C VM (V-12 item 3)"),
    ("cardlang.harness.scenario", "--backend cvm", "cvm: runtime scenarios on the C VM"),
    ("tests/card_check.py", "--backend cvm", "virtual card on cvm: the transport and the examples behind it"),
    ("tests/fido2_client_check.py", "--backend cvm", "virtual card on cvm: python-fido2's client and server against the FIDO2 applet"),
]

# The example applets: each examples/<app>/check.py checks its applet independently of the applet's own logic,
# and every example scenario must pass, on every backend (V-12 item 2). They are found, not listed, so a new applet is
# checked as soon as its folder exists.
BACKENDS = ("interp", "pyvm", "cvm")

def example_runs():
    L = layout.at(ROOT)
    for check in sorted(L.examples.glob("*/check.py")):
        app = check.parent.name
        for b in BACKENDS:
            yield (check, f"--backend {b}", f"examples/{app} on {b}: a session, checked independently")
    for b in BACKENDS:
        yield (L.tests / "example_scenarios.py", f"--backend {b}", f"every example scenario on {b}")

def label(script):
    """How a run's script is shown: a checker by its name, an applet's checker by its applet."""
    if isinstance(script, str) and not script.endswith(".py"): return script.rsplit(".", 1)[-1]
    s = pathlib.Path(script)
    if s.name == "check.py": return f"{s.parent.name}/check.py"
    return s.name

def cvm_built():
    from cardlang.harness import cvm_backend
    return cvm_backend.library_path() is not None

def main():
    require_cvm = "--require-cvm" in sys.argv
    failures = skipped = 0
    have_cvm = cvm_built()
    for script, glob, what in RUNS + list(example_runs()):
        extra = glob.split() if glob else []                 # e.g. "--backend pyvm"
        if extra[-2:] == ["--backend", "cvm"] and not have_cvm:
            if require_cvm:
                print(f"[FAILED] {label(script):13} {glob:18}    0 passed  - {what}")
                print("         the C VM is not built, and --require-cvm requires it"); failures += 1
            else:
                print(f"[skip  ] {label(script):13} {glob:18}    -          - {what}"); skipped += 1
            continue
        run = ["-m", script] if isinstance(script, str) and not script.endswith(".py") else [str(ROOT / script)]
        cmd = [sys.executable, "-I", *run, str(ROOT)] + extra
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
    if skipped:
        from cardlang.harness import cvm_backend
        print(f"{skipped} run(s) on the C VM skipped: it is not built. Build it with {cvm_backend.BUILD_HINT}.")
    print(("ALL CHECKS PASSED" + (f" ({skipped} skipped)" if skipped else "")) if failures == 0 else f"{failures} FAILURE(S)")
    return 0 if failures == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
