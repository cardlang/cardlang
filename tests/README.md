# Checks

`run_checks.py` runs every check in the repository. From the repository root, after building the C VM:

```bash
uv run python -I vm/c/build.py all
uv run python -I tests/run_checks.py
```

It prints one line per run, with the number of tests that passed, and exits non-zero on any failure. Run it after every change. A single check runs on its own with `uv run python -I tests/<check>.py .`, or, for a module of the package, `uv run python -I -m cardlang.<module> .`.

## What it runs

**The definition, through the reference checkers.** Each front-end module of `cardlang.front` runs its chapter's conformance tests (`lexcheck`, `typecheck` and the rest, up to `pltcheck`). `pltcheck` also runs the full chain over every valid test and each chapter's invalid tests. `cardlang.front.grammar` derives every test, and the design notes' code blocks, from Annex A. The package's README describes the checkers.

**The definition itself:**

| Check | What it checks |
|---|---|
| `speccheck.py` | The specification's consistency: rule tags and sources, references, compile-error classes and trap kinds, tables, grammar fragments, the B.12 checklist, Annex D's links and coverage, and the index's counts |
| `profilecheck.py` | The Base Profile: its rule numbering, the `CardError` table, `base-types.card`, and the API catalog |
| `linkcheck.py` | Links, anchors and file paths in every document and source file, and that only `cardlang.layout` builds paths into the repository |

**Running programs:**

| Check | What it checks |
|---|---|
| `cardlang.interp.interp` | The runtime conformance tests on the reference interpreter |
| `cardlang.harness.scenario` | The same tests on the Python VM and on the C VM, built with MSVC and with clang |
| `cardlang.compiler.typer` | The typer types every valid, runtime and example program |
| `compile_all.py` | Every program compiles, and on the C VM every image loads |
| `check_state.py` | All of the Python VM's state is in its context, within 1 KiB |
| `debug_check.py` | Debug information: lines, variables, globals and traps, and that it never changes the code |
| `examples/*/check.py` | Each example applet, checked independently of its own logic, on every backend |
| `example_scenarios.py` | Every example scenario passes, on every backend |

**The tools:**

| Check | What it checks |
|---|---|
| `poscheck.py` | Diagnostics: valid programs are clean, and every error has its code at a position |
| `clc_check.py` | `clc`: check, build, disassemble and run, and that the compiler refuses an invalid program |
| `lsp_check.py` | The language server, through a scripted editor session |
| `semantic_check.py` | Semantic colouring, against a pinned sample in `testdata/`, and completion |
| `dap_check.py` | The debug adapter: breakpoints, stepping, the stack, variables and traps |
| `editors/vscode/check_extension.py` | The extension's grammars, keywords and scenario steps match the language |
