# VM4 and VM5 — The prototype compiler and VM: detailed sub-plan

Parent: `plans_and_notes/vm-plan-of-plans.md`.
Inputs:
- `vm/execution-model.md` (VEX);
- `vm/hal.md` (HAL);
- `vm/bytecode.md` (BC) and `vm/image-format.md` (IMG), version 0;
- `vm/decisions.md` (V-1 to V-28).

Status: decisions E1 to E5 taken 2026-11-20, all as recommended (option (a)). They become V-29 to V-33 in the register.

**Stage 1 done (2026-11-20):**
- the statement parser moved to `tools/checkers/stmtparse.py`, shared with the interpreter;
- `tools/vmproto/typer.py` subclasses the full checker and records the type of every expression. It types all 151 programs (122 valid tests, 28 runtime tests, the FIDO2 applet) completely;
- it runs in `tools/run_checks.py`.

The program is accepted first by the unmodified checker, because the typer relaxes the checker's position rules for slices.

**Stage 2 done (2026-11-20):** `tools/vmproto/`:
- `isa.py`, the shared instruction table;
- `compiler.py` (layout, code generation, image writer, resource report) and `disasm.py` (first named `dis.py`), the disassembler;
- `vm.py`, the VM core, with its context of 216 bytes on the 32-bit model;
- `hal.py`, the storage part of the test HAL;
- `card.py`, the `vmproto` backend; `natives.py` is a placeholder.

**Results:**
- all 18 runtime tests without platform APIs pass, and two mutations of the VM (`INDEX` without its bounds check, `ADD` without its overflow check) are caught;
- all 151 programs already compile and decode, which meets V-12 item 3 early. `compile_all.py` runs in `run_checks`.

**Version-0 changes** (`vm/bytecode.md` §9): `ERRGET` and `ERRRAISE`; `operand_base` in IMG-6; test native numbers from `0xF000`.

**Stages 3 and 4 done (2026-11-20):**
- **The test HAL** (`hal.py`) adds the key store, with persistent keys joining transactions, and all cryptography, through the test-only implementations. It uses the same deterministic random generator as the interpreter.
- **The native library** (`natives.py`) implements all 34 Base Profile APIs and the five test APIs. Its checks follow the interpreter's order, so outcomes are identical.
- **Results:**
  - all 28 runtime tests pass on `vmproto`;
  - `check_fido2 --backend vmproto` passes all 59 checks;
  - all 151 programs compile.
- **Acceptance:** criteria 1 to 3 of V-12 now run in `run_checks`, as two new runs: the runtime scenarios and the FIDO2 check, both on `vmproto`.
- **Mutations of the native library are caught:**
  - outputs that never report `Capacity` fail four tests;
  - command-lifetime operations that never end fail one test.

**Stage 5 done (2026-11-20):** `plans_and_notes/VM5-measurements.md`, from `tools/vmproto/measure.py`. `tools/vmproto/check_state.py` (V-31) runs in `run_checks`. VM4 and VM5 are complete.

**Headline:**
- the VM context is 216 bytes;
- the FIDO2 code is 11.3 KB and its stack 1 KB;
- frame access is 38% of all code;
- frame-slot reuse is the main RAM lever, and short forms would cut about a third of the code.

## 1. Scope

VM4 and VM5 are one feedback loop: the compiler produces version-0 images, and the prototype VM runs them. Both are in Python, in `tools/vmproto/` (V-11). They become the `vmproto` backend of the harness (V-10). The work is done when the backend meets the acceptance criteria of V-12:
1. all 28 runtime tests pass;
2. `check_fido2` passes, with its 59 checks;
3. all 122 valid conformance programs compile to images;
4. the compiler and the VM report their figures.

Any change to version 0 found on the way goes into the change log of `vm/bytecode.md` (V-28).

## 2. What exists, and what does not

- **The checkers accept or reject programs, but keep no typed syntax tree.** They parse and check in one pass over the tokens. `pltcheck.PltChecker` does yield the declarations: functions with their parameters and body tokens, structures, globals, enums, constant values and the error codes.
- **The interpreter** parses statements into tuples (`parse_stmt`), and expressions with the checkers' expression parser (`expcheck.p_expr`). It types values dynamically. A compiler needs static types: the type code of every operation (V-25), and the layout of every place (V-13).
- **The tests also use a test-only catalog** (`conformance/platform/test-catalog.txt`, `card.test.*`). It has five fictional APIs, used by run-015, run-016 and two valid tests. They have no native numbers.

## 3. Design

### 3.1 The compiler (VM4)

| Stage | Does |
|---|---|
| **Accept** | Runs `pltcheck` with the binding check, exactly as the harness does. Only accepted programs are compiled, so later stages assume the program is valid (V-1) |
| **Parse** | Reuses `expcheck`'s expression parser and the interpreter's statement parser, which moves into a shared module (E1) |
| **Type** | A new static pass: it annotates every expression with its type, including the expected-type rules for literals (EXP-7 to EXP-11) and the outcome forms. It assumes validity, so it is much smaller than a checker. Where its result disagrees with the checker's, that is a compiler bug |
| **Lay out** | Places globals in `PERSISTENT` and `SESSION`, and constants in `CONST`. Assigns frame offsets for parameters, locals and temporaries. Computes the frame sizes and the stack need over the call graph |
| **Generate** | Emits the version-0 instructions as Annex A of `vm/bytecode.md` describes. Folds constant scalars (CEX). Makes no other optimisation (E4) |
| **Emit** | Writes the image bytes (IMG) with a debug section, and the resource report (IMG-13) |

A disassembler (`tools/vmproto/disasm.py`) prints an image as annotated listings, like Annex B of `vm/bytecode.md`.

### 3.2 The VM (VM5)

- **It runs the image bytes** (E2): it decodes the header, function table and instructions from the binary image, exactly as the C VM will. That tests the format, the encoding, and the compiler's output together.
- **It keeps all its mutable state in one context object** (E3). Each field of the object is declared with its size in C. A test checks that the VM keeps no state anywhere else. The report gives the context's size, which is the V-2 figure.
- **The regions** are byte arrays: `SESSION`, `STACK` (sized from `cl_config`), and the platform's `REQUEST` and `RESPONSE` buffers. `CONST` is a view into the image. `PERSISTENT` is reached only through the HAL.
- **The native library** implements the non-cryptographic part of the catalog: the checks, the operation table, CBOR, TLV and DER (HAL-3, V-5). It reuses the test-only CBOR, TLV and DER modules.
- **The test HAL** follows `vm/hal.md`:
  - storage is a byte array with a journal for atomic updates and transactions, recovery, and the interrupt hook;
  - the key store joins transactions;
  - all cryptography is done in the HAL, by `testcrypto.py` and `p256.py` (V-19);
  - it provides the seed hook.
- **Measurement.** The VM records, per run:
  - opcode frequencies, both static and dynamic;
  - the deepest stack actually used;
  - the budget used per command.

### 3.3 The test catalog (E5)

The five `card.test.*` APIs get native numbers in a reserved range, `0xF000` and up. Only test builds of a VM implement them: the Python native library and, later, the C test build. Base Profile numbers stay as BC-32 defines them. A production image never imports a reserved number, so a production VM rejects such an image at load (IMG-11).

### 3.4 The harness and the checks

- **`backends.py`** gains `vmproto`. Building compiles the program, and the card wraps a VM context over a test HAL. Scenarios and `check_fido2` then run unchanged.
- **`run_checks.py`** gains three runs: runtime scenarios on `vmproto`, `check_fido2` on `vmproto`, and compiling every valid test.
- **Differential testing.** For every runtime test, the outcomes of `interp` and `vmproto` must be identical. That already follows from both passing the same expectations. In addition, the harness can compare the two step by step for scenarios that have no expectation.

## 4. Stages

Each stage ends with all earlier checks still passing:

1. **Shared parser and typer.** Move the interpreter's statement parser into `tools/vmproto/front.py`, or a shared module, and point `interp.py` at it. Write the typer, and check it against all 122 valid programs plus the runtime tests and the applet: every expression gets a type, and nothing crashes.
2. **The core:** layout and code generation without natives, the image writer, the disassembler, and the VM core with the storage part of the test HAL. Done when the runtime tests that use no platform API pass.
3. **Natives:** the native library, the key and crypto part of the test HAL, and the test catalog. Done when all 28 runtime tests pass.
4. **The FIDO2 applet:** `check_fido2 --backend vmproto` passes, and all 122 valid programs compile.
5. **Measurement:** the resource reports, and a report in `plans_and_notes/VM5-measurements.md`:
   - image and code sizes per program;
   - the FIDO2 applet in detail;
   - opcode frequencies;
   - stack needs, against what is actually used;
   - the context size.

   This is VM6's input.

Version-0 changes found during stages 2 to 4 go into the change log as they happen.

## 5. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| E1 | The compiler's front end | (a) reuse the checkers (for acceptance and declarations) and the existing parsers, and add a static typing pass that assumes validity; (b) extend the reference checkers to emit a typed syntax tree; (c) write a new front end | (a). The checkers stay the authority and are not disturbed. The typer is small because it never has to reject anything |
| E2 | What the VM executes | (a) the binary image, decoded as the C VM will; (b) an in-memory structure from the compiler | (a). It tests the format and encoding now, and gives exact sizes |
| E3 | How VM state is measured | (a) one context object with declared C sizes, and a test that the VM keeps no other state; (b) estimate by inspection | (a). It turns V-2 into a checked number |
| E4 | Compiler optimisation | (a) constant folding only (CEX); measure the plain output; (b) add a peephole pass now | (a). VM6 decides on density from measurements, so the baseline must be plain. Any optimisation is added together with its measured effect |
| E5 | The test-only catalog | (a) native numbers from `0xF000`, implemented only in test builds; (b) port run-015, run-016 and the two valid tests to Base Profile APIs | (a). The tests stay as they are; production VMs reject such images at load |
