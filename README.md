<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/cardlang-logo-dark.svg">
    <img src="assets/cardlang-logo.svg" width="300" alt="CardLang">
  </picture>
</p>

CardLang is a small, statically typed, imperative language for writing secure applications that run isolated on small devices: trusted applications on microcontrollers, in a TrustZone secure world or a partition isolated by the memory protection unit, and also smart-card applets. This repository holds:
- **the language:** its specification, a conformance test suite, and the reasoning behind it;
- **a platform profile:** the APIs a platform gives programs (keys, crypto, CBOR, TLV) and its transport bindings;
- **a toolchain:** reference checkers, a compiler to a compact bytecode, a reference interpreter, and a Python VM;
- **a VM in portable C11,** which runs the same images and passes the same tests;
- **an editor extension** for VS Code, with errors as you type, completion, building and a debugger;
- **two example applets,** a FIDO2 authenticator and a PIV card application.

CardLang is under active development.

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

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length == 1 else CounterError.MalformedRequest;
    require response.length >= 4 else CounterError.ResponseTooSmall;
    var operation: u8 = request[0];
    if operation == OP_READ {
        response[0..4] = encode_be(counter);
    } else if operation == OP_INCREMENT {
        counter = counter + 1;
        response[0..4] = encode_be(counter);
    } else {
        return Err(CounterError.UnsupportedOperation);
    }
    return Ok(4);
}
```

Key properties of the language:

- **Fixed-size data only.** Integers `u8`–`u32` and `i8`–`i32`, `bool`, enums, structures and fixed arrays `T[N]`. There is no heap, no strings, no floating point and no implicit conversion.
- **Explicit state.** Globals are `persistent` (survives power loss), `session` (cleared at power-on and reset) or `const`. Every assignment to persistent state is atomic, and `transaction { … }` groups several of them.
- **Outcomes, not exceptions.** Every call returns `Ok(…)` or `Err(…)`, which must be handled with `match`, `attempt`, `require` or a forwarding `return`. Execution faults, such as overflow or an out-of-range index, are deterministic *traps*.
- **References without pointers.** `ref` and `inout` parameters, and slices passed as views. References cannot be stored or returned.
- **A single entry point.** One `command` receives the request bytes and writes the response. The language has no transport, status words or dispatch of its own.
- **A static, acyclic call graph.** There is no recursion, so stack needs and transaction nesting can be checked before the program runs.

## The VM at a glance

Applets run on the CardLang VM, small enough for deeply embedded targets: it is written in portable C, with no heap and no recursion. Roughly:

- **Code:** around 20 KB for the VM, the interpreter and its native library.
- **VM state:** around 250 bytes.
- **C stack:** a single-digit number of kilobytes, at most.
- **The applet's own needs:** its stack and its global state, which depend on the applet. They are known exactly when it is built: `clc build` reports them, so you can fit an applet to your budget.

These leave out what the device's platform supplies itself: its hardware layer, its cryptography, and the driver for its persistent storage. The VM's design is in [`vm/`](vm/README.md).

## The CardLang Guide

**[The CardLang Guide](https://cardlang.github.io/cardlang/)** teaches the language by building one applet, a small PIN-protected store for a secret, chapter by chapter: from a first counter to persistent state, transactions, signing keys, testing and debugging, and a guided reading of the FIDO2 example. Every example in it is compiled and run by the repository's checks. It ends with a chapter for readers coming from C or Java Card, and a reference of the platform's APIs.

## The VS Code extension

The CardLang extension for VS Code is the easiest way into the language:

- **Highlighting**, and colouring by meaning, for applets and scenario files.
- **Errors as you type,** across all of an applet's files, each with its code from the specification.
- **Go to definition and completion,** including the platform's APIs, with their signatures, errors and documentation.
- **Build, check and run** an applet, and its scenarios, from the editor.
- **A debugger:** breakpoints in the applet and in scenarios, stepping, the call stack, variables and persistent state, and stops on traps and failed expectations.

It needs a clone of this repository, with `uv sync` run once, and [uv](https://docs.astral.sh/uv/). Download `cardlang-<version>.vsix` from the [latest release of the extension](https://github.com/cardlang/cardlang/releases), and install it from the Extensions view. [Chapter 1 of the guide](https://cardlang.github.io/cardlang/01-getting-started/) walks through installing it, and building, running and debugging a first applet; the [extension's README](editors/vscode/README.md) covers its settings and the scenario format.

## Repository layout

| Path | Contents |
|---|---|
| [`guide/`](guide/README.md) | The CardLang Guide, which teaches the language by example; published at [cardlang.github.io/cardlang](https://cardlang.github.io/cardlang/) |
| [`language/`](language/README.md) | The language definition |
| [`language/spec/`](language/spec/00-index.md) | the specification: chapters 1–13, plus Annex A (grammar), B (platform contract), C (open issues) and D (traceability). Start at [`language/spec/00-index.md`](language/spec/00-index.md) |
| [`language/conformance/`](language/conformance/README.md) | 412 tests: `valid/`, `invalid/` (each naming the expected compile error) and `runtime/` scenarios, plus a fictional test-only platform API catalog |
| [`language/rationale/`](language/rationale/) | the design notes, the platform notes and the decision register, which the rules cite |
| [`language/releases/`](language/releases/) | the Draft 0.2 release notes, and the candidates for Draft 0.3 |
| [`platform/`](platform/README.md) | The CardLang Base Profile 1, a platform specification separate from the language: API conventions, platform types (`base-types.card`), `CardError` codes, keys, crypto, CBOR, TLV, transport bindings and the API catalog (`base-catalog.txt`) |
| [`examples/`](examples/README.md) | The example applets, each self-contained, with its sources, scenarios, its own checker and a README |
| [`examples/fido2/`](examples/fido2/README.md) | a FIDO2 (CTAP 2.0) authenticator, with PIN protocols two and one |
| [`examples/piv/`](examples/piv/README.md) | a PIV card application (NIST SP 800-73-5, contact-interface subset) |
| [`src/cardlang/`](src/cardlang/README.md) | The Python toolchain, one package installed by `uv sync`: the reference checkers (the front end), the compiler, the reference interpreter, the Python VM, the harness, the command line `clc`, the language server and the debug adapter |
| [`tests/`](tests/README.md) | `run_checks.py`, and the checks of the tools and of the definition |
| [`editors/`](editors/README.md) | The VS Code extension, in `editors/vscode/` |
| [`vm/`](vm/README.md) | The VM's design (execution model, HAL, bytecode, image format) and the C VM (`vm/c/`) |
| [`devel/`](devel/README.md) | Development aids: the plans, measurement reports and findings, test generators, and history and measurement scripts. A record of how the project was built, kept apart from the rest |

## Licence

CardLang is licensed under the [Apache License, Version 2.0](LICENSE): the specification and the other documents, the toolchain, the C VM, the editor extension and the examples. See also [`NOTICE`](NOTICE).

The repository contains no third-party code. These are fetched by the tools, each under its own licence:

| Component | Used by | Licence |
|---|---|---|
| [Mbed TLS](https://github.com/Mbed-TLS/mbedtls) 3.6.8 | the C VM's host HAL, downloaded and checked against its SHA-256 by the build | Apache-2.0 or GPL-2.0-or-later |
| [cffi](https://cffi.readthedocs.io/) | the harness, to drive the C VM from Python | MIT-0 |
| [vscode-languageclient](https://github.com/microsoft/vscode-languageserver-node) | the VS Code extension, bundled into its package | MIT |
| [@vscode/vsce](https://github.com/microsoft/vscode-vsce) | packaging the extension | MIT |
