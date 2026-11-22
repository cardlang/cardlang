# VM3 — Bytecode and image format, version 0: detailed sub-plan

Parent: `plans_and_notes/vm-plan-of-plans.md`. Inputs: `vm/execution-model.md` (VEX-1 to VEX-50), `vm/hal.md` (HAL-1 to HAL-31), `vm/decisions.md` (V-1 to V-23).
Status: decisions D1 to D5 taken 2026-11-19, all as recommended (option (a)). They become V-24 to V-28 in the register. **Drafted 2026-11-19:**
- `vm/bytecode.md`, BC-1 to BC-38, with the construct map (annex A) and the hand-compiled counter and `get_info` (annex B, assembled exactly);
- `vm/image-format.md`, IMG-1 to IMG-13.

## 1. Scope

VM3 writes two documents:
- **`vm/bytecode.md`** (`BC-n`): the instruction set, its encoding and its semantics.
- **`vm/image-format.md`** (`IMG-n`): the layout of an application image.

**Version 0 is deliberately plain.** It aims to be complete and easy to compile to, not dense. Density comes in VM6, from measurements of the VM5 prototype on the FIDO2 applet: short forms, combined instructions, and operand widths. What VM3 must get right are the things that are expensive to change later:
- the operand model;
- how instructions name memory;
- calls and outcomes;
- natives;
- the image's sections and the load-time checks.

## 2. Design outline

### 2.1 Encoding (D1)

- **The form:** a one-byte opcode, followed by the operands that opcode defines. Each operand has a fixed width per opcode: `u8`, `u16` or `u32`, little-endian (V-13).
- **No alignment, no prefixes.** In version 0 every operand has a fixed width; VM6 may add short forms.
- **Opcode ranges:** the opcode space is divided by family, with gaps left for VM6. Opcode `0x00` is never valid, so that erased flash fails fast with `trap(VM)` (VEX-41).

### 2.2 Typed operations (D2)

Arithmetic, comparisons, shifts, conversions and scalar memory accesses act on one of the seven scalar kinds: `u8`, `u16`, `u32`, `i8`, `i16`, `i32`, and `bool`/enum (unsigned, 1 or 2 bytes). In version 0, one opcode per operation takes a one-byte *type operand*, for example `ADD u16` or `LOAD.L i32 off`. The handler dispatches on the type. VM6 may add specialised opcodes for the most frequent pairs.

Semantics follow chapter 6 exactly:
- **checked arithmetic** traps `OVERFLOW`, `UNDERFLOW`, `DIV-ZERO`, `NEGATION` or `SHIFT` (EXP-23 to EXP-26);
- **`wrapping_*`** wraps;
- **`checked_*`** sets the outcome register instead of trapping (VEX-23).

### 2.3 Instruction families

| Family | Contents | Serves |
|---|---|---|
| Constants and stack | Push an immediate of 8, 16 or 32 bits; `DUP`, `DROP`, `SWAP` | VEX-6 |
| Scalar memory, region known | `LOAD.r T off`, `STORE.r T off` for each region `r`: frame, session, constant, persistent. A persistent store is one atomic update (VEX-28) | VEX-7, VEX-11 |
| Addresses | `ADDR.r off`: a tagged address; `INDEX size length`: a bounds-checked element address; `FIELD off`: add a field offset | VEX-11, VEX-16 |
| Indirect access | `LOAD.I T`, `STORE.I T` through an address cell, dispatching on its tag | VEX-12 |
| Views | Make a view from an address and a static length; `SLICE size` with the FUN-20 checks; `LEN` | VEX-13, VEX-16 |
| Blocks | `COPY n` (address to address, overlap-safe, atomic into persistent storage); `COPY.V size` between views of equal length; `FILL`; `EQUAL`; `COMPARE`; `ENCODE`/`DECODE` with endianness and type | VEX-15, VEX-28, VEX-37, FUN-24 |
| Arithmetic and logic | `ADD`, `SUB`, `MUL`, `DIV`, `REM`, `NEG`, the bitwise operations, the shifts, comparisons, `NOT`; the wrapping and checked variants; `CONVERT`, `CHECKED_CONVERT`, `TRUNCATE` | EXP-20 to EXP-46, EXP-52 |
| Control | `JMP`, `JZ`, `JNZ` (relative offsets); `SWITCH` (a jump table, for `match` on enums) | STM, chapter 7 |
| Calls and outcomes | `CALL f`; `RET` (an `Ok`, with a scalar, none, or an aggregate already in its slot); `ERR category code`; `FWD` (forward the current error); `JERR` (branch on `Err`); `ERRCODE` (the code, for `Err(Set(code))`); a test for one error member | VEX-17 to VEX-23, chapter 9 |
| Transactions | `TXN.BEGIN`, `TXN.COMMIT`, `TXN.ABORT` | VEX-31 |
| Natives | `NATIVE n` (D3) | VEX-33 |
| Erasure | `WIPE`: the stores of a `wipe` statement, never skipped | VEX-38 |

The budget (VEX-42) is charged per instruction, and per byte by the block instructions and natives. Each charge is listed in `bytecode.md`.

### 2.4 Natives (D3)

**Numbering.** Every catalog API has a fixed *native number* (`u16`), listed in `bytecode.md` in catalog order. A later profile may add numbers, but never changes or reuses one.
- `NATIVE n` takes its arguments from the operand stack, as for a call.
- The image's import list names the numbers it uses, so the load-time check of VEX-9 can reject an image that needs a native the VM lacks.

**No load-time resolution.** Nothing is resolved at load, so no import table grows in RAM (V-2).

### 2.5 The image (IMG)

| Section | Contents |
|---|---|
| Header | Magic and format version; profile and binding; the region sizes (`PERSISTENT`, `SESSION`), the stack need, the largest static persistent destination (VEX-9); the indices of the entry functions (`command`, `on_install`, `on_session_start`, `on_select`, or none); the offset and length of each section |
| Function table | For each function: code offset, frame size, parameter size, operand depth |
| Native imports | The native numbers used (D3) |
| Constants | The bytes of the `CONST` region (VEX-7) |
| Code | All function bodies |
| Debug (optional, D4) | Source file names, a line table, function names. The device VM ignores it; tools may strip it |

Every multi-byte field is little-endian. Offsets are relative to the image start. Authenticating the image is the platform's loader's job (V-1); the header has no signature.

### 2.6 What the compiler must report

This is the resource report of the plan of plans and V-12, item 4:
- the image size, per section;
- the stack need, with the deepest call path;
- the frame size of each function;
- the `PERSISTENT` and `SESSION` sizes;
- the largest static persistent destination.

## 3. Work

1. **Write `vm/bytecode.md`:** the encoding, the type codes, every instruction with its operands, stack effect, semantics, traps and budget charge, the native number table, and the VEX and spec rules each instruction serves.
2. **Write `vm/image-format.md`:** the sections, the header fields, the load-time checks (VEX-9), and the resource report.
3. **Check on paper.** Every construct in the VM1 paper check (`vm/execution-model.md`, annex) has an instruction sequence. Write that check as an annex of `bytecode.md`. Also hand-compile two small examples into annotated bytecode: the counter application (`conformance/runtime/run-011-counter-application`), and the FIDO2 `get_info` function (`examples/fido2/ctap.card`).
4. **Update** `vm/decisions.md` (D1 to D4 become V-24 onward), `vm/README.md` and the plan of plans.

VM3 writes no code. The compiler (VM4) and the prototype VM (VM5) will find gaps. Version 0 is therefore *living*: VM4 and VM5 may change it, and record each change in `bytecode.md`'s change log, until VM6 freezes a revised version (D5).

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Instruction encoding | (a) a one-byte opcode with fixed-width operands per opcode; (b) fixed 32-bit instruction words | (a). Dense enough, and simple to decode byte by byte in portable C. (b) wastes flash for little gain in an interpreter |
| D2 | How integer types appear in instructions | (a) one opcode per operation, plus a one-byte type operand; (b) a separate opcode per operation and type, about six times more opcodes; (c) width-agnostic 32-bit operations followed by explicit range-check instructions | (a) for version 0. Easy to compile, and the opcode space stays small. VM6 specialises the frequent pairs from measurements. (c) is awkward for 32-bit overflow and for signed division |
| D3 | How natives are named | (a) fixed native numbers per catalog API, used directly by `NATIVE n`; the import list is only for the load-time check; (b) names in the image, resolved at load into a table | (a). No load-time table in RAM, and no string handling on the device |
| D4 | Debug information | (a) an optional section with source lines and function names, which the device VM ignores and tools may strip; (b) none in the image, kept in a separate file | (a). The prototypes and the conformance harness can report traps with source positions, and the device cost is nothing once it is stripped |
| D5 | How fixed version 0 is | (a) living until VM6: VM4 and VM5 may change it, with a change log; (b) frozen once VM3 is drafted | (a). The compiler and the prototype VM are where its mistakes will show |
