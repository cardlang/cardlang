# CardLang

CardLang is a small, statically typed, imperative language for writing smart-card applications. This repository holds its language specification, a conformance test suite, and reference tools that check the two against each other.

**Status: Draft 0.2** (tag `spec-draft-0.2`). All 305 rules are agreed and every open issue is resolved. See [the release notes](language/releases/draft-0.2.md) for what changed since Draft 0.1, including the first platform profile and a FIDO2 authenticator example.

Since Draft 0.2, the repository also holds:
- a compiler to a compact bytecode (`src/cardlang/compiler/compiler.py`);
- a prototype VM in Python, and the VM in portable C11 (`vm/c/`), which pass the same tests;
- a VS Code extension, with errors as you type, go to definition, completion and a debugger ([`editors/vscode/`](editors/vscode/README.md)).

## The language at a glance

```text
errors CounterError {
    MalformedRequest = 1;
    UnsupportedOperation = 2;
    ResponseTooSmall = 3;
}

const OP_READ: u8 = 0x01;
const OP_INCREMENT: u8 = 0x02;

persistent counter: u32;

function encode_counter(output: inout u8[]) -> u32 {
    require output.length >= 4 else CounterError.ResponseTooSmall;
    var bytes: u8[4] = encode_be(counter);
    for index: u32 in 0..4 {
        output[index] = bytes[index];
    }
    return Ok(4);
}

function increment() {
    transaction {
        counter = counter + 1;
    }
    return Ok();
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length == 1 else CounterError.MalformedRequest;
    var operation: u8 = request[0];
    if operation == OP_INCREMENT {
        attempt increment();
    } else if operation != OP_READ {
        return Err(CounterError.UnsupportedOperation);
    }
    return encode_counter(inout response);
}
```

This is a shortened version of the counter, one of the representative applications. The full version is `language/conformance/valid/hep-005-counter-application.card`. Key properties of the language:

- **Fixed-size data only.** Integers `u8`–`u32` and `i8`–`i32`, `bool`, enums, structures and fixed arrays `T[N]`. There is no heap, no strings, no floating point and no implicit conversion.
- **Explicit state.** Globals are `persistent` (survives power loss), `session` (cleared at power-on and reset) or `const`. Every assignment to persistent state is atomic, and `transaction { … }` groups several of them.
- **Outcomes, not exceptions.** Every call returns `Ok(…)` or `Err(…)`, which must be handled with `match`, `attempt`, `require` or a forwarding `return`. Execution faults, such as overflow or an out-of-range index, are deterministic *traps*.
- **References without pointers.** `ref` and `inout` parameters, and slices passed as views. References cannot be stored or returned.
- **A single entry point.** One `command` receives the request bytes and writes the response. The language has no transport, status words or dispatch of its own.
- **A static, acyclic call graph.** There is no recursion, so stack needs and transaction nesting can be checked before the program runs.

## Repository layout

| Path | Contents |
|---|---|
| [`language/`](language/README.md) | The language definition: |
| [`language/spec/`](language/spec/00-index.md) | the specification: chapters 1–13, plus Annex A (grammar), B (platform contract), C (open issues) and D (traceability). Start at [`language/spec/00-index.md`](language/spec/00-index.md) |
| [`language/conformance/`](language/conformance/README.md) | 350 tests: `valid/`, `invalid/` (each naming the expected compile error) and `runtime/` scenarios, plus a fictional test-only platform API catalog |
| [`language/rationale/`](language/rationale/) | the design notes, the platform notes and the decision register, which the rules cite |
| [`language/releases/`](language/releases/) | the Draft 0.2 release notes, and the candidates for Draft 0.3 |
| [`platform/`](platform/base-profile.md) | The CardLang Base Profile 1, a platform specification separate from the language: API conventions, platform types (`base-types.card`), `CardError` codes, keys, crypto, CBOR, TLV, transport bindings and the API catalog (`base-catalog.txt`) |
| [`examples/`](examples/README.md) | The example applets, each self-contained, with its sources, scenarios, its own checker and a README: |
| [`examples/fido2/`](examples/fido2/README.md) | a FIDO2 (CTAP 2.0) authenticator, with PIN protocols two and one |
| [`examples/piv/`](examples/piv/README.md) | a PIV card application (NIST SP 800-73-5, contact-interface subset) |
| [`src/cardlang/`](src/cardlang/README.md) | The Python toolchain, one package installed by `uv sync`: the reference checkers (the front end), the compiler, the reference interpreter, the Python VM, the harness, the command line `clc`, the language server and the debug adapter |
| [`tests/`](tests/README.md) | `run_checks.py`, and the checks of the tools and of the definition |
| [`editors/vscode/`](editors/vscode/README.md) | The VS Code extension |
| [`vm/`](vm/decisions.md) | The VM's design (execution model, HAL, bytecode, image format) and the C VM (`vm/c/`) |
| [`devel/`](devel/README.md) | Development aids: the plans of plans and every work-package plan, measurement reports and findings, the conformance-test generators, and the history and measurement scripts |

## How the specification is organized

- **Numbered rules.** Rules carry chapter-prefixed IDs such as `EXP-6` or `TXN-8`, and a status tag. Each one cites the decisions and design-note sections it comes from.
- **Formal rules.** Typing uses bidirectional judgments, and evaluation is given as numbered steps.
- **Named errors.** Compile errors have classes (`CE-EXP-1`). Runtime faults have trap kinds (`TRAP-BOUNDS`).
- **Separated layers.** Chapters 1–13 define only language-visible behavior. Anything a platform, VM or transport decides is a `PLT-n` requirement or a *platform-defined* item in Annex B. §B.12 lists the 31 items a platform specification must answer.
- **Traceability.** Annex D links the spec to the design notes in both directions, and maps every rule to its tests, or gives the reason no test can check it.

## Running the checks

The tools run in the repository's uv environment (`uv sync` once). The C VM is built with `vm/c/build.py` (MSVC and clang). From the repository root:

```bash
uv run python -I vm/c/build.py all
uv run python -I tests/run_checks.py
```

This runs every checker over the conformance tests it covers, the grammar check, the specification consistency check and the runtime scenarios. It exits non-zero on any failure. Run it after every change to `language/spec/` or `language/conformance/`. The tools are not normative: when a tool and `language/spec/` disagree, the specification wins.

## Next steps

The plans are in [`devel/plans/vm-plan-of-plans.md`](devel/plans/vm-plan-of-plans.md) and `devel/plans/tooling/`:

- **VM8:** the C VM on a real Cortex-M;
- **VM9:** a bridge to real host software, through a virtual smart-card reader;
- **WP13:** an OpenPGP card applet;
- **a checker for chapter 3's name rules,** which the tools do not check yet;
- **the candidates for Draft 0.3,** in `language/releases/draft-0.2-candidates.md`.
