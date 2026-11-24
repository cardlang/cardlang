# The CardLang VM

This folder holds the design of the virtual machine that runs CardLang applications, and its implementation in C (`c/`). It is separate from the language specification (`language/spec/`) and from the Base Profile (`platform/`). Where a VM document and the specification or profile disagree, the specification wins.

## Goals

- **The VM trusts its bytecode** (V-1). Static guarantees come from the compiler and an off-device verifier, so the VM has no verifier.
- **Small, bounded RAM** (V-2). The VM's own bookkeeping is fixed and at most 1 KiB. Application storage is configured separately.
- **Portable C11 over a rich HAL** (V-3). Crypto, keys, randomness and persistent storage with transactions are the HAL's. The VM does no cryptography at all (V-19).
- **A stack machine** (V-4).

## Layers

```text
   host / transport (the platform's main loop)
          │  requests, session events
   ┌──────▼─────────────────────────────┐
   │ binding adapter (ISO 7816 / raw)   │  status words, raw envelope (profile BP-50 to BP-53)
   ├────────────────────────────────────┤
   │ VM core: loader, interpreter loop, │  traps, outcomes, frames, views
   │ memory regions                     │
   ├────────────────────────────────────┤
   │ native library and native table    │  card.* calls by catalog index; CBOR, TLV, DER in C (V-5)
   ├────────────────────────────────────┤
   │ HAL (cl_hal.h)                     │  storage and transactions, crypto, keys, RNG
   └────────────────────────────────────┘
```

The VM is a library (V-6): the platform calls it through `cl_vm.h` and it calls the HAL through `cl_hal.h`. One VM context runs one application (V-8).

## Documents

| Document | Content | Status |
|---|---|---|
| `decisions.md` | The decision register (V-n) | V-1 to V-52 |
| `execution-model.md` | Values, memory regions, views, frames, calls, outcomes, traps, the VM context (`VEX-n`); what the HAL must provide | VEX-1 to VEX-50 |
| `hal.md` | The HAL interface (`HAL-n`): storage, keys, all cryptography, randomness, test hooks; the catalog map. Declarations in `c/include/cl_hal.h` and `cl_hal_test.h` | HAL-1 to HAL-31 |
| `bytecode.md` | The instruction set, its encoding, the calling convention and the native numbers (`BC-n`); compiled examples | version 1: BC-1 to BC-40 (living until a public release, V-51) |
| `image-format.md` | The application image and the load-time checks (`IMG-n`) | format 1: IMG-1 to IMG-13 |
| `c/` | The product VM in C11, and a host HAL | complete: meets V-12 with MSVC and clang |

The compiler is in `src/cardlang/compiler/`. The Python VM (`src/cardlang/pyvm/`) is the working model of the C VM: it runs the same images, and meets the same acceptance criteria as the harness backend `pyvm`.

## Conventions

- **Requirements** are numbered per document and cite the decisions and the spec or profile rules they serve (V-9), for example: *Serves: RTF-2, PLT-35; V-2.*
- **C names** use the prefix `cl_` for functions and types, and `CL_` for macros and constants.

## Acceptance

Every VM backend is checked by the same harness (`src/cardlang/harness/`, V-10) against the criteria of V-12:

1. every runtime conformance test passes (`language/conformance/runtime/`);
2. each example applet's `check.py` passes;
3. every valid conformance program compiles to an image;
4. the backend reports its bytecode size, stack and frame figures, and its bookkeeping RAM.

Run a backend's scenarios with:

```bash
uv run python -I -m cardlang.harness.scenario . --backend interp
```

and the FIDO2 check with:

```bash
uv run python -I examples/fido2/check.py . --backend interp
```

The backends are `interp` (the reference interpreter), `pyvm` (the Python VM), and `cvm` (the C VM, built with any C11 compiler). `tests/run_checks.py` runs every check on all four.
