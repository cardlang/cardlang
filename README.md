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

Key properties of the language:

- **Fixed-size data only.** Integers `u8`–`u32` and `i8`–`i32`, `bool`, enums, structures and fixed arrays `T[N]`. There is no heap, no strings, no floating point and no implicit conversion.
- **Explicit state.** Globals are `persistent` (survives power loss), `session` (cleared at power-on and reset) or `const`. Every assignment to persistent state is atomic, and `transaction { … }` groups several of them.
- **Outcomes, not exceptions.** Every call returns `Ok(…)` or `Err(…)`, which must be handled with `match`, `attempt`, `require` or a forwarding `return`. Execution faults, such as overflow or an out-of-range index, are deterministic *traps*.
- **References without pointers.** `ref` and `inout` parameters, and slices passed as views. References cannot be stored or returned.
- **A single entry point.** One `command` receives the request bytes and writes the response. The language has no transport, status words or dispatch of its own.
- **A static, acyclic call graph.** There is no recursion, so stack needs and transaction nesting can be checked before the program runs.

## Getting started in VS Code

The VS Code extension is the easiest way into CardLang: open an example applet, read it with highlighting and errors as you type, build it, run it, and step through it in a debugger.

**1. Set up the repository and the extension.** You need [uv](https://docs.astral.sh/uv/) and VS Code. Clone this repository, and from its root run:

```bash
uv sync
```

`uv sync` installs the CardLang toolchain into the repository's environment. The extension runs it from there. Then download `cardlang-<version>.vsix` from the [latest release of the extension](https://github.com/cardlang/cardlang/releases), and install it:

```bash
code --install-extension cardlang-<version>.vsix
```

To build the extension yourself instead, with Node.js and npm, see its [README](editors/vscode/README.md#installing).

**2. Open the repository folder in VS Code,** then open `examples/fido2/ctap.card`, a FIDO2 authenticator's command handlers.
- **Errors as you type:** change a type or misspell a name, and the error appears at once, with its code from the specification (`CE-EXP-4`) and its message.
- **Go to definition:** F12 or Ctrl+click on any name, across the applet's files and into the platform's types.
- **Completion:** type `card.` to see the platform's APIs, with their signatures and documentation.

**3. Build the applet.** With a `.card` file of the applet open, run **CardLang: Build Applet** from the command palette, or click the package icon. It checks the whole applet, writes the compiled image to `examples/fido2/build/fido2.clvm`, and prints its size and stack need. Errors go to the Problems panel.

**4. Run it.** Open `examples/fido2/getinfo.scenario`. A scenario plays the host side: it selects the applet, sends commands, and states the responses it expects. Run **CardLang: Run Scenario** (the play icon) to see every step and its outcome.

**5. Debug it.** Set a breakpoint in `get_info` in `ctap.card`, open the scenario again, and press F5. The debugger stops in the applet. You can then:
- step by statement: over (F10), in (F11) and out (Shift+F11);
- see the call stack, the parameters and locals, the `session` and `persistent` globals, and the request and response bytes;
- turn on the **Traps** or **Failed expectations** breakpoints, in the Breakpoints panel, to stop where a trap happens or an `expect` fails.

**6. Write your own.** An applet is a folder with a `cardlang.json` that lists its files in build order:

```json
{ "name": "counter", "files": ["counter.card"], "binding": "raw" }
```

The extension's [README](editors/vscode/README.md) covers the scenario format, debugging configurations and settings. The same tools work from a terminal, as `uv run clc check`, `build`, `disasm` and `run`.

## Repository layout

| Path | Contents |
|---|---|
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
