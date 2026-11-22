# PR5 — The Python package `src/cardlang/`: detailed sub-plan

Planned 2026-11-22, the fifth work package of PR0. The Python toolchain in `tools/` becomes one installable package, `cardlang`, under `src/`, and the checks of the tools and of the definition move to `tests/`. The prototype VM becomes `pyvm` (PR0 R7). Every move is a `git mv`, and each stage keeps `run_checks` passing.

## 1. What there is now

**Size:** 55 Python files, about 9,000 lines, in seven folders: `checkers`, `vmproto`, `interp`, `harness`, `lsp`, `dap` and `vscode`, plus `clc.py`, `clc_check.py` and `run_checks.py` at the top.

**How modules find each other:** by editing `sys.path`. There are 103 lines that mention it, in 84 files, counting `devel/` and the examples. `pyproject.toml` names the project, with `cffi` as its one dependency, but it has no build system, so nothing is installed.

**Layering problems the move must fix:**
- **The compiler, the Python VM's card and its natives import `harness/scenario.py`.** They use `CARD_ERROR_CODES`, which `scenario.py` reads from the Base Profile's table. `typer`, `compiler` and `disasm` also use its `program_files`. So the core depends on the test harness. <!-- linkcheck: ignore -->
- **The Python VM's HAL imports the interpreter's test crypto** (`p256`, `testcrypto`), and its natives import `testcbor` and `testtlv`. These are host-side implementations of the Base Profile's services, used by both simulators and by the applet checks. They are not part of the interpreter.
- **The language server and the debug adapter share `lsp/jsonrpc.py`.** <!-- linkcheck: ignore -->
- **The debug adapter imports `clc.py`.**
- **PR0 put `grammar.py` in `tests/`, but it cannot go there.** `diagnose` imports it, and through `diagnose` so do the language server and `clc check`. It is part of the front end.

**The checkers have two jobs.** Each checker module is both a part of the front end and, through its `main`, the runner of its chapter's conformance tests. For example, `expcheck.main` runs the `exp-*` tests.

**How the editor finds the tools.** The installed extension (0.1.1) runs `tools/clc.py`, `tools/lsp/cardlang_lsp.py` and `tools/dap/cardlang_dap.py` by path, through `uv run --project <repo>`. PR6 changes the extension.

**Data the package reads.**
- **The platform catalog and base types** in `platform/`, through `layout`. The compiler and the language server need them at run time.
- **The Base Profile's `CardError` table,** read from `platform/base-profile.md`.

## 2. The target

```
pyproject.toml              gains a build system (S1); `uv sync` installs the package, editable
src/cardlang/
  layout.py                 where the repository's parts are (was tools/checkers/layout.py)
  jsonrpc.py                the protocol framing that the language server and the debug adapter share
  cli.py                    clc (was tools/clc.py), an installed command
  front/                    lexcheck, srcpos, project, consteval, typecheck, expcheck, stmtparse, stmcheck, funcheck,
                            outcheck, stacheck, txncheck, hepcheck, pltcheck, grammar, diagnose (was tools/checkers)
  platform/                 the host side of the Base Profile: errors (CARD_ERROR_CODES, moved out of scenario.py),
                            p256, testcrypto, testcbor, testtlv (were in tools/interp)
  bytecode/                 isa, debuginfo, disasm
  compiler/                 typer, compiler
  interp/                   interp, the reference interpreter
  pyvm/                     vm, hal, natives, card (was tools/vmproto)
  harness/                  scenario, backends, cvm_backend
  lsp/                      server (was cardlang_lsp.py), complete, semantic
  dap/                      adapter (was cardlang_dap.py)
tests/
  run_checks.py             as now, running the conformance runners with `python -m cardlang.front.<checker>`
  speccheck.py  profilecheck.py  linkcheck.py  poscheck.py
  clc_check.py  lsp_check.py  semantic_check.py (+ testdata/)  dap_check.py
  debug_check.py  check_state.py  compile_all.py  example_scenarios.py
tools/vscode/               unchanged until PR6, apart from its check's imports
```

- **Imports:** every module imports by package, as in `from cardlang.front import lexcheck`. No `sys.path` editing is left in `src/` or `tests/`. The examples' checkers and the scripts in `devel/` import `cardlang` too, and need no bootstrap: the package is installed.
- **The conformance runners stay where they are.** Each checker module keeps its `main` and is run as `python -m cardlang.front.expcheck <repo>`. Splitting the runners into `tests/` is a separate change, left for later. It would touch every checker for no change in behaviour.
- **The installed commands:** `clc`, `cardlang-lsp` and `cardlang-dap`, as `[project.scripts]`.
- **The package works from a repository checkout.** `layout` finds the repository from its own file, two levels up from `src/cardlang/`. The platform data stays in `platform/` and is not bundled into a wheel. Bundling it is release work, recorded in §5, and not needed for an editable install.

## 3. The stages

Each stage is one commit, ends with `run_checks` passing, and updates `layout`, `MOVED` and the current documents for what it moved. A module that has not moved yet imports the moved ones by package, which works because the package is installed from the first stage.

| Stage | Moves | Also |
|---|---|---|
| **5a** The package, `layout` and the front end | the build system (S1); `layout.py` and `tools/checkers/*` except the four checks, into `src/cardlang/` and `front/`; `speccheck`, `profilecheck`, `linkcheck` and `poscheck` into `tests/` | every importer rewritten; `layout.TOP_LEVEL` gains `src` and `tests`; `run_checks` runs the runners with `-m`; the `devel/` scripts and the examples' checkers import `cardlang.layout` |
| **5b** The platform, the bytecode and the compiler | `platform/` (with `errors.py` taking `CARD_ERROR_CODES` from `scenario.py`, and `program_files` moving to `front/project.py`); `bytecode/`; `compiler/` | **T1 (S3):** `compile_files` runs the full diagnostics first | <!-- linkcheck: ignore -->
| **5c** The interpreter, `pyvm` and the harness | `interp/`; `vmproto` to `pyvm/` (R7); `harness/`; `compile_all`, `check_state`, `debug_check` and `example_scenarios` into `tests/` | **The rename:** the backend name `vmproto` becomes `pyvm` everywhere: in `--backend`, in `run_checks`, in the DAP and in the extension's `cardlang.scenarioBackend` setting and its default. Historical reports keep `vmproto` |
| **5d** The language server, the debug adapter, the command line and `tests/` | `lsp/`, `dap/`, `jsonrpc.py` and `cli.py`; the tool checks and `run_checks.py` into `tests/` | `[project.scripts]`; the launchers at the extension's old paths (S2); `tools/README.md` becomes the package's README, and `tests/README.md` is new |

**Done when:**
- `tools/` holds only `vscode/`, and the launchers if S2 keeps them;
- `uv sync` installs `cardlang`;
- `clc`, `cardlang-lsp` and `cardlang-dap` run;
- no file in `src/`, `tests/` or `examples/` edits `sys.path`;
- `run_checks` passes;
- the extension still checks, builds, runs and debugs both applets.

## 4. Checks at every stage

- `run_checks` passes. The link check's rule that only `layout` builds repository paths moves with `layout` itself.
- The 33 generators and history scripts that ran after PR4 still run against a copy of the repository.
- A grep finds no `sys.path` lines outside `devel/history` scripts that are never re-run.
- From stage 5d: `clc check examples/fido2` works as an installed command, and the extension works with the launchers.

## 5. Recorded for later

- **A wheel** that works outside a checkout would need the Base Profile's catalog, base types and `CardError` table as package data, and `layout` to find them there. This is for a published release, PR8 or after.
- **The conformance runners** could move out of the front-end modules into `tests/`.
- **Module names:** the front end's `*check` names (S4).

## 6. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| S1 | The build backend | (a) `uv_build`, uv's own backend, with the `src/` layout as its default; (b) `hatchling` | (a). The project already runs on uv, and `uv_build` needs no configuration for `src/cardlang/`. Either one is a build-time download, which I would ask before fetching |
| S2 | The old paths | (a) no import shims: every importer is rewritten. Three small launchers stay at the paths the installed extension runs (`tools/clc.py`, `tools/lsp/cardlang_lsp.py`, `tools/dap/cardlang_dap.py`), each calling the package, until PR6 removes them; (b) no launchers either: the extension is broken between PR5 and PR6; (c) import shims at every old module path | (a). Pre-alpha, so nothing outside needs the old imports, but the extension you use day to day should keep working |
| S3 | T1: should `compiler.compile_files` refuse an invalid program? | (a) yes: it runs the full diagnostics first and raises with them, so every caller is safe, not only `clc build`; (b) no: callers keep calling `diagnose` themselves | (a). A compiler that accepts invalid programs is a trap for anyone who calls it directly. The cost is the diagnostics' time on each compile |
| S4 | Module names beyond the `pyvm` rename | (a) keep them: `lexcheck`, `expcheck` and the rest, plus the three entry modules as `cli`, `lsp/server` and `dap/adapter`; (b) also rename the front end, for example `lexcheck` to `lexer` | (a). A rename touches every import and every document for no change in behaviour. It can be its own small change later, once the layout is settled |

**Decided (user, 2026-11-22):** S1 (a) `uv_build`, S2 (a) three launchers and no import shims, S3 (a) the compiler refuses invalid programs, and S4 (a) keep the module names. All four are as recommended. Fetching `uv_build` at stage 5a is a download, and I will ask before it.

## 7. Done: stage 5a (2026-11-22)

- **The package:**
  - `pyproject.toml` builds with `uv_build` (0.11.x, fetched with your permission);
  - `uv sync` installs `cardlang` editable into the project's environment, and it imports under `python -I`;
  - `src/cardlang/__init__.py` and `front/__init__.py` describe the package.
- **Moved with `git mv`:**
  - `tools/checkers/layout.py` to `src/cardlang/layout.py`;
  - the 16 front-end modules to `src/cardlang/front/`;
  - `speccheck`, `profilecheck`, `linkcheck` and `poscheck` to `tests/`.

  `tools/checkers/` is gone.
- **Imports:**
  - every importer, in 81 files across `tools/`, `examples/` and `devel/`, now uses `from cardlang import layout` and `from cardlang.front import …`;
  - the `sys.path` lines that found the checkers are gone, as is `"checkers"` from every `sys.path` loop;
  - no file in `src/` or `tests/` edits `sys.path`;
  - the modules not moved yet keep their other `sys.path` lines until their stage.
- **Paths:** three front-end modules computed the repository root from their own file. These were `diagnose`, `grammar` and `pltcheck`, and they would have been off by one level after the move. They now ask `layout`.
- **`run_checks`:** it runs the front-end checkers as modules (`-m cardlang.front.lexcheck`), and the scripts by their path from the root. All 51 runs pass with the same counts as before; only the link check's count grew, with the new files.
- **`layout`:**
  - new parts `src`, `package`, `front` and `tests`;
  - `TOP_LEVEL` gains `src` and `tests`;
  - `MOVED` has the 5a rows.
- **Documents:** the current documents' paths are rewritten through `MOVED`, and `tools/README.md` says how to run a checker as a module.
- **Scripts:**
  - the 33 generators and history scripts, and `revision.py`, run against a copy as before, and the same three fail;
  - `pyvm_measure.py` had been broken since PR4, because it imported `check_fido2` from `tools/fido/`. It now loads `examples/fido2/check.py`, and it runs.

## 8. Done: stage 5b (2026-11-22)

- **Moved with `git mv`:**
  - `p256`, `testcrypto`, `testcbor` and `testtlv` from `tools/interp/` to `src/cardlang/platform/`;
  - `isa`, `debuginfo` and `disasm` from `tools/vmproto/` to `src/cardlang/bytecode/`;
  - `typer` and `compiler` to `src/cardlang/compiler/`.

  Each subpackage has an `__init__.py` that says what it holds.
- **The layering:**
  - **`CARD_ERROR_CODES`** is now in the new `cardlang/platform/errors.py`. The compiler and the Python VM's card and natives import it from there. `scenario.py` imports it too, so it is still importable from the harness.
  - **`program_files`:** the compiler, the typer and the disassembler take it from `cardlang.front.project`, where it already lived. `scenario.program_files` remains, as a delegate.
  - Nothing in `src/` imports the harness.
- **Imports:**
  - 28 files rewritten by package, covering the moved modules, the unmoved tools, the examples' checkers and two measurement scripts;
  - every `sys.path` line in the moved modules is gone;
  - usage lines are now `python -m cardlang.compiler.compiler`, `cardlang.compiler.typer` and `cardlang.bytecode.disasm`.
- **T1 (S3):**
  - `compile_files` runs `diagnose.check` first, and raises the new `InvalidProgram` with the diagnostics;
  - `clc build` and `clc disasm` rely on it instead of checking separately;
  - `backends.build` turns `InvalidProgram` into its `BuildError`;
  - `clc_check` gained a check that `compile_files` refuses `cex-105` (CE-CEX-3) by itself.
- **`run_checks`:**
  - it runs the typer as `-m cardlang.compiler.typer`;
  - all 51 runs pass with the same counts as after 5a, and `clc_check` has 13 checks, one more.
- **`layout.MOVED`:** has the 5b rows, and the current documents were rewritten through it: the readme, the VS Code README, the VM documents and a C VM comment.
- **Scripts:**
  - the 33 generators and history scripts, and `revision.py`, run against a copy, and the same three fail;
  - both measurement scripts run.

## 9. Done: stage 5c (2026-11-22)

- **Moved with `git mv`:**
  - `tools/interp/interp.py` to `src/cardlang/interp/`;
  - `vm`, `hal`, `natives` and `card` from `tools/vmproto/` to `src/cardlang/pyvm/`;
  - `scenario`, `backends`, `cvm_backend` and the harness README to `src/cardlang/harness/`;
  - `compile_all`, `check_state`, `debug_check` and `example_scenarios` to `tests/`.

  `tools/interp/`, `tools/vmproto/` and `tools/harness/` are gone.
- **Imports:**
  - 17 files are rewritten by package;
  - every `sys.path` line in the moved modules is gone, and so are the lines in the examples' checkers and the measurement scripts;
  - no file in `src/`, `tests/` or `examples/` edits `sys.path`;
  - `cvm_backend` finds the C VM's library through `layout.at()`, where it used a root computed from its old place.
- **The rename (R7):**
  - **The backend:** `vmproto` is now `pyvm` in `backends`, `clc` (its default and choices), the DAP, `run_checks` and its labels, the checks, and the measurement scripts' backend calls. `cvm_measure`'s output keeps its `vmproto` key, as the reports have it.
  - **The extension's source:** its `cardlang.scenarioBackend` default and enum, the JavaScript default, and its README.
  - **The examples' READMEs** use the new name.
  - **The installed extension** (0.1.1) still sends `--backend vmproto`, so `clc run` accepts it as an alias of `pyvm`. PR6 drops the alias.
- **`run_checks`:** it runs the interpreter and the scenario runner as modules (`-m cardlang.interp.interp`, `-m cardlang.harness.scenario`). All 51 runs pass with the same counts.
- **`check_extension`** read `scenario.py` from its old path. It now finds it through the module.
- **`layout.MOVED`:** has the 5c rows, including the three old folders. The current documents and the C VM's comments were rewritten through it, and the command blocks were fixed by hand.
- **Scripts:**
  - the 33 generators and history scripts, and `revision.py`, run against a copy as before;
  - both measurement scripts run.
