# The `cardlang` package

The CardLang toolchain in Python: the front end, the compiler, the reference interpreter, the Python VM, the harness, the command line, the language server and the debug adapter. None of it is normative: when the package and `language/spec/` disagree, the specification wins, and the package is the thing to fix.

It is installed, editable, into the repository's uv environment by `uv sync`, and it works from a checkout of the repository: `cardlang.layout` finds the specification, the conformance suite and the Base Profile there. Its one dependency is `cffi`, for the C VM.

| Module | What it is |
|---|---|
| `layout` | Where the repository's parts are. Every path into the repository goes through it |
| `front/` | The lexer, the reference checker of each chapter, the Annex A grammar, and `diagnose`, which runs them all and reports errors with positions |
| `platform/` | The host side of the Base Profile: the `CardError` codes, and the test-only crypto, CBOR and TLV |
| `bytecode/` | The instruction set, the debug section and the disassembler |
| `compiler/` | The typer and the code generator. `compile_files` refuses a program that `diagnose` rejects |
| `interp/` | The reference interpreter |
| `pyvm/` | The Python VM, its test HAL and natives, and the card that the harness drives |
| `harness/` | The scenario runner and the backends: `interp`, `pyvm` and `cvm` (see its [README](harness/README.md)) |
| `cli` | `clc`: check, build, disassemble, and run a scenario |
| `lsp/`, `dap/`, `jsonrpc` | The language server and the debug adapter, and the protocol framing they share |

## Commands

`uv sync` installs three commands into the environment:

```bash
uv run clc check examples/fido2
uv run clc build examples/fido2
uv run clc run examples/fido2/getinfo.scenario --backend pyvm
```

`cardlang-lsp` and `cardlang-dap` are the language server and the debug adapter, which the editor starts. Any module with its own entry runs as `uv run python -I -m cardlang.<module>`.

## Run everything

From the repository root:

```bash
uv run python -I tests/run_checks.py
```

It runs every checker over the conformance tests it covers, and every check of the tools. It prints one line per run and exits non-zero if any test does not give its expected result. Run it after every change. The checks are described in [`tests/README.md`](../../tests/README.md).

## The reference checkers: `src/cardlang/front/`

The checkers are the front end of the `cardlang` package, installed by `uv sync`. Each checker is a small implementation of the rules of one chapter. It is written from the chapter text and checks the `expect:` line of each conformance test. Each one builds on the one before it, so the last one, `pltcheck.py`, applies every rule implemented so far.

| Script | Implements | Default tests |
|---|---|---|
| `lexcheck.py` | Chapter 2: lexical structure | Every test, plus every code block in the design notes |
| `typecheck.py` | Chapter 4: type declarations and type rules | `*/typ-*` |
| `consteval.py` | Chapter 5: constant evaluation, with the arithmetic of chapter 6 | `*/cex-*` |
| `expcheck.py` | Chapter 6: expression typing (bidirectional) | `*/exp-*` |
| `stmcheck.py` | Chapter 7: statements, completion analysis | `*/stm-*` |
| `funcheck.py` | Chapter 8: call graph, modes, references, slices | `*/fun-*` |
| `outcheck.py` | Chapter 9: outcomes, `attempt`, outcome `match`, error sets | `*/out-*` |
| `stacheck.py` | Chapter 10: initializers and lifecycle handlers | `*/sta-*` |
| `txncheck.py` | Chapter 11: transaction boundaries, `abort` and nesting | `*/txn-*` |
| `hepcheck.py` | Chapter 12: the `command` and its signature. Adds the HEP-16 scaffold to `kind: fragment` tests | `*/hep-*` |
| `pltcheck.py` | Annex B: `card.` paths, platform-call signatures, and APIs not permitted in transactions. Uses the test-only catalog plus the Base Profile catalog, and adds `platform/base-types.card` to every build (its names are predeclared) | `*/plt-*` |

Further checkers check the specification itself rather than one chapter. `grammar.py` is part of the front end, since the diagnostics use it; `profilecheck.py` and `speccheck.py` are in `tests/`:

| Script | Checks | Default |
|---|---|---|
| `grammar.py` | Annex A, mechanically. It reads the EBNF from the annex, converts it to BNF and runs an Earley recognizer. Every test must derive `SourceFile`, except tests expecting CE-SYN-1, which must not, and lexical-error tests, which are skipped. With `--notes`, every design-note code block that the full checker accepts must derive | every test |
| `profilecheck.py` | The Base Profile in `platform/`: BP rule numbering, the `CardError` table and the error precedence, `base-types.card` compiling, and every catalog block's fields, types and errors | `platform/` |
| `speccheck.py` | Consistency of `language/spec/`: rule tags and Sources lines, references, compile-error classes and their tables, trap kinds, table shapes, chapter grammar fragments against Annex A, the B.12 checklist, the D.2 reverse links, the D.3 coverage matrix and the 00-index counts | the specification |

Run a front-end checker as a module, `uv run python -I -m cardlang.front.<checker> . "<glob>"`, and a check in `tests/` by its path. For example:

```bash
uv run python -I -m cardlang.front.pltcheck . "valid/*"
uv run python -I tests/speccheck.py .
```

**Known limitations.**

- The checkers stop at the first error they find.
- They only check compile-time results. Runtime behaviour is checked by `interp/` (below).
- They do not implement every rule. For example, scope and shadowing rules (NAM-19 to NAM-21) are checked by review. `tests/poscheck.py` lists the naming tests that depend on them.
- Fragments in the design notes that use undeclared names are reported as name errors. That is expected.
- On some malformed input the checkers stop with a Python assertion instead of reporting CE-SYN-1. `grammar.py` is the authority for CE-SYN-1.
- The full chain does not report an unresolved type name in a global declaration, such as `session big: u64;`. `typecheck.py` does, and it checks the `typ-*` tests.

## `interp/`: the reference interpreter

`interp.py` runs the runtime tests in `language/conformance/runtime/`. For each test it does three things:

1. It compiles the program with the full checker chain (`pltcheck`).
2. It executes the steps in the test's `scenario.txt`.
3. It compares every host-visible result (response bytes, application or platform error, trap kind, or no outcome) with the `expect` lines.

The interpreter implements the semantics of chapters 6–13:

- typed integers with checked arithmetic and the trap kinds of RTF-4;
- references, views and slices;
- transactions, with in-place rollback;
- `abort` and `attempt`;
- the command contract;
- `install`, `power_on`, `reset`, and power loss during a commit;
- the fictional behavior of the test-only platform catalog (`language/conformance/platform/test-catalog.txt`).

```bash
uv run python -I -m cardlang.interp.interp .
```

It is not normative and not optimized. Its execution budget is a fixed number of statements, enough for the tests. A deliberately wrong expectation makes it fail, which was checked when it was written: a missing rollback, a reversed assignment order and a cleared session each made their test fail.

## The example applets' checks

Each example applet has its own checker, `examples/<app>/check.py`, beside its sources. It is described in the applet's README. `run_checks.py` finds every one and runs it on every backend, and `tests/example_scenarios.py` runs every example scenario on every backend. See [`examples/`](../../examples/README.md).
