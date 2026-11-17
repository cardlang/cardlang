# CardLang

CardLang is a small, statically typed, imperative language for writing smart-card applications. This repository holds its language specification, a conformance test suite, and reference tools that check the two against each other.

**Status: Draft 0.1, complete** (tag `spec-draft-0.1`). All 287 rules are agreed and every open issue is resolved. There is no compiler or VM yet. See [the consolidation report](plans_and_notes/SP14-consolidation-report.md) for what Draft 0.1 contains and what comes next.

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

This is a shortened version of the counter, one of the representative applications. The full version is `conformance/valid/hep-005-counter-application.card`. Key properties of the language:

- **Fixed-size data only.** Integers `u8`–`u32` and `i8`–`i32`, `bool`, enums, structures and fixed arrays `T[N]`. There is no heap, no strings, no floating point and no implicit conversion.
- **Explicit state.** Globals are `persistent` (survives power loss), `session` (cleared at power-on and reset) or `const`. Every assignment to persistent state is atomic, and `transaction { … }` groups several of them.
- **Outcomes, not exceptions.** Every call returns `Ok(…)` or `Err(…)`, which must be handled with `match`, `attempt`, `require` or a forwarding `return`. Execution faults, such as overflow or an out-of-range index, are deterministic *traps*.
- **References without pointers.** `ref` and `inout` parameters, and slices passed as views. References cannot be stored or returned.
- **A single entry point.** One `command` receives the request bytes and writes the response. The language has no transport, status words or dispatch of its own.
- **A static, acyclic call graph.** There is no recursion, so stack needs and transaction nesting can be checked before the program runs.

## Repository layout

| Path | Contents |
|---|---|
| [`spec/`](spec/00-index.md) | The specification: chapters 1–13, plus Annex A (grammar), B (platform contract), C (open issues) and D (traceability). Start at [`spec/00-index.md`](spec/00-index.md) |
| [`conformance/`](conformance/README.md) | 350 tests: `valid/`, `invalid/` (each naming the expected compile error) and `runtime/` scenarios, plus a fictional test-only platform API catalog |
| [`platform/`](platform/base-profile.md) | The CardLang Base Profile, a platform specification separate from the language: API conventions, platform types (`base-types.card`), `CardError` codes and the API catalog (`base-catalog.txt`). Work in progress |
| [`tools/`](tools/README.md) | Reference checkers for each chapter, an Earley grammar checker built from Annex A, a spec consistency checker, a reference interpreter for the runtime tests, and test generators |
| [`plans_and_notes/`](plans_and_notes/) | The source design notes, the decision register, the plan of plans with one sub-plan per chapter, and the SP14 consolidation report |

## How the specification is organized

- **Numbered rules.** Rules carry chapter-prefixed IDs such as `EXP-6` or `TXN-8`, and a status tag. Each one cites the decisions and design-note sections it comes from.
- **Formal rules.** Typing uses bidirectional judgments, and evaluation is given as numbered steps.
- **Named errors.** Compile errors have classes (`CE-EXP-1`). Runtime faults have trap kinds (`TRAP-BOUNDS`).
- **Separated layers.** Chapters 1–13 define only language-visible behavior. Anything a platform, VM or transport decides is a `PLT-n` requirement or a *platform-defined* item in Annex B. §B.12 lists the 31 items a platform specification must answer.
- **Traceability.** Annex D links the spec to the design notes in both directions, and maps every rule to its tests, or gives the reason no test can check it.

## Running the checks

The tools need only Python 3 and its standard library. From the repository root:

```bash
python -I tools/run_checks.py
```

This runs every checker over the conformance tests it covers, the grammar check, the specification consistency check and the runtime scenarios. It exits non-zero on any failure. Run it after every change to `spec/` or `conformance/`. The tools are not normative: when a tool and `spec/` disagree, the specification wins.

## Next steps

Work outside this specification:

- a real platform API catalog;
- a platform specification that answers Annex B §B.12;
- a compiler;
- a VM.

The details are in the consolidation report.
