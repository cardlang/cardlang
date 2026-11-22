# Specification tools

These scripts support the CardLang specification work. They are not a compiler, and they are not normative: when a script and `language/spec/` disagree, the specification wins, and the script is the thing to fix.

All scripts need only Python 3 and its standard library.

## Run everything

From the repository root:

```bash
python -I tools/run_checks.py
```

It runs every checker over the conformance tests it covers. It prints one line per run and exits non-zero if any test does not give its expected result. Run it after every change to `language/spec/` or `language/conformance/`.

## `checkers/`: reference checkers

Each checker is a small implementation of the rules of one chapter. It is written from the chapter text and checks the `expect:` line of each conformance test. Each one builds on the one before it, so the last one, `pltcheck.py`, applies every rule implemented so far.

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

Two further checkers check the specification itself rather than one chapter:

| Script | Checks | Default |
|---|---|---|
| `grammar.py` | Annex A, mechanically. It reads the EBNF from the annex, converts it to BNF and runs an Earley recognizer. Every test must derive `SourceFile`, except tests expecting CE-SYN-1, which must not, and lexical-error tests, which are skipped. With `--notes`, every design-note code block that the full checker accepts must derive | every test |
| `profilecheck.py` | The Base Profile in `platform/`: BP rule numbering, the `CardError` table and the error precedence, `base-types.card` compiling, and every catalog block's fields, types and errors | `platform/` |
| `speccheck.py` | Consistency of `language/spec/`: rule tags and Sources lines, references, compile-error classes and their tables, trap kinds, table shapes, chapter grammar fragments against Annex A, the B.12 checklist, the D.2 reverse links, the D.3 coverage matrix and the 00-index counts | the specification |

Run a single checker as `python -I tools/checkers/<script> . "<glob>"`. For example:

```bash
python -I tools/checkers/pltcheck.py . "valid/*"
```

**Known limitations.**

- The checkers stop at the first error they find.
- They only check compile-time results. Runtime behaviour is checked by `interp/` (below).
- They do not implement every rule. For example, scope and shadowing rules (NAM-19 to NAM-21) are checked by review. The naming tests that depend on them are listed as "by review" in the SP2 notes.
- Fragments in the design notes that use undeclared names are reported as name errors. That is expected.
- On some malformed input the checkers stop with a Python assertion instead of reporting CE-SYN-1. `grammar.py` is the authority for CE-SYN-1.
- The full chain does not report an unresolved type name in a global declaration, such as `session big: u64;`. `typecheck.py` does, and it checks the `typ-*` tests.

## `interp/`: reference interpreter

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
python -I tools/interp/interp.py .
```

It is not normative and not optimized. Its execution budget is a fixed number of statements, enough for the tests. A deliberately wrong expectation makes it fail, which was checked when it was written: a missing rollback, a reversed assignment order and a cleared session each made their test fail.

## `fido/`: the FIDO2 example check

`check_fido2.py` builds `examples/fido2` with the full checker, the Annex A grammar and the ISO 7816 binding check. It runs a scripted CTAP session through the interpreter, and checks every response with its own CBOR codec and DER parser. Only the ECDSA verification comes from `interp/testcrypto.py`. It is part of `run_checks.py`.

## Development aids

The conformance-test generators, the one-off history scripts and the measurement scripts are in [`devel/`](../devel/README.md), with the plans and reports.

