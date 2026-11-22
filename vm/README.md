# The CardLang VM

This folder holds the design, and later the implementation, of the virtual machine that runs CardLang applications. It is separate from the language specification (`language/spec/`) and from the Base Profile (`platform/`). Where a VM document and the specification or profile disagree, the specification wins.

The plan is in `devel/plans/vm-plan-of-plans.md`. Each work package (VM0 to VM8) has a sub-plan in `devel/plans/vm/`.

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

| Document | Content | Work package | Status |
|---|---|---|---|
| `decisions.md` | The decision register (V-n) | all | V-1 to V-41 |
| `execution-model.md` | Values, memory regions, views, frames, calls, outcomes, traps, the VM context (`VEX-n`); what the HAL must provide | VM1 | drafted: VEX-1 to VEX-50 |
| `hal.md` | The HAL interface (`HAL-n`): storage, keys, all cryptography, randomness, test hooks; the catalog map. Declarations in `c/include/cl_hal.h` and `cl_hal_test.h` | VM2 | drafted: HAL-1 to HAL-31; headers not yet compiled |
| `bytecode.md` | The instruction set, its encoding, the calling convention and the native numbers (`BC-n`); compiled examples | VM3, VM6 | version 1: BC-1 to BC-39 (living through VM7) |
| `image-format.md` | The application image and the load-time checks (`IMG-n`) | VM3, VM6 | format 1: IMG-1 to IMG-13 |
| `c/` | The product VM in C11, and a host HAL | VM7 | not started |

The prototypes (a Python compiler and VM, VM4 and VM5) live in `tools/vmproto/` (V-11). They meet acceptance criteria 1 to 3 of V-12 as the harness backend `vmproto`: all runtime tests, the FIDO2 check, and every program compiles. The measurements (criterion 4) are in `devel/reports/VM5-measurements.md`: the VM context is 216 bytes.

## Conventions

- **Requirements** are numbered per document and cite the decisions and the spec or profile rules they serve (V-9), for example: *Serves: RTF-2, PLT-35; V-2.*
- **C names** use the prefix `cl_` for functions and types, and `CL_` for macros and constants.

## Acceptance

Every VM backend is checked by the same harness (`tools/harness/`, V-10) against the criteria of V-12:

1. every runtime conformance test passes (`language/conformance/runtime/`);
2. `tools/fido/check_fido2.py` passes;
3. every valid conformance program compiles to an image;
4. the backend reports its bytecode size, stack and frame figures, and its bookkeeping RAM.

Run a backend's scenarios with:

```bash
python -I tools/harness/scenario.py . --backend interp
```

and the FIDO2 check with:

```bash
python -I tools/fido/check_fido2.py . --backend interp
```

The only backend so far is `interp`, the reference interpreter.
