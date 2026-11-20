# CardLang VM — Bytecode, version 0

Work package VM3. Plan: `plans_and_notes/vm-plans/VM3-bytecode-and-image.md`. Decisions: `vm/decisions.md`. Image layout: `vm/image-format.md`.

This document defines the instruction set that the VM executes: the encoding, each instruction's operands, stack effect, semantics, traps and budget charge, the calling convention, and the native numbers. Requirements are numbered `BC-n` and cite the decisions and the `VEX`, `HAL`, specification and profile rules they serve (V-9).

**Version 0 is living** (V-28). The prototype compiler (VM4) and the prototype VM (VM5) may change it. Every change is recorded in §9, until VM6 freezes a measured revision. Version 0 favours completeness and simplicity over density.

## 1. Encoding

**BC-1 Instructions.** An instruction is a one-byte opcode followed by the operands its opcode defines, in the order listed. Operands are unaligned and little-endian (V-13). Every operand has a fixed width per opcode in version 0.
*Serves: V-24.*

**BC-2 Operand kinds.**

| Kind | Width | Meaning |
|---|---:|---|
| `T` | 1 | A scalar type code (BC-3) |
| `R` | 1 | A region tag (VEX-7) |
| `b`, `h`, `w` | 1, 2, 4 | An unsigned immediate of 8, 16 or 32 bits |
| `rel` | 2 | A signed offset, in bytes, from the end of the instruction to the jump target |
| `cat` | 1 | An error category: 1 for application, 2 for platform |
| `ord` | 1 | A byte order: 0 for big-endian, 1 for little-endian |

*Serves: V-24.*

**BC-3 Type codes.** Every typed instruction takes one of six codes: `u8` = 0, `u16` = 1, `u32` = 2, `i8` = 3, `i16` = 4, `i32` = 5. `bool` and enums use `u8`, or `u16` for an enum with more than 256 variants (VEX-4). They are never used with arithmetic.
*Serves: V-25; VEX-4, TYP-6.*

**BC-4 Cells.** The operand stack holds 32-bit cells (VEX-6). A value of type `T` is held *normalized*:
- the cell holds its mathematical value;
- zero-extended for the unsigned codes, sign-extended for the signed codes.

Every instruction that produces a value produces it normalized. Equality on normalized cells is equality of values, so `EQ` and `NE` need no type.
*Serves: VEX-6.*

**BC-5 Invalid opcodes.** Opcode `0x00` and every opcode not defined here are invalid. Executing one is `trap(VM)` (VEX-41). With trusted images (V-1), nothing else about an instruction is checked at run time, except the checks its semantics define.
*Serves: V-1; VEX-41.*

**BC-6 Opcode map.**

| Range | Family | Section |
|---|---|---|
| `0x01`–`0x0F` | Constants and stack | §2.1 |
| `0x10`–`0x17` | Scalar memory, region known | §2.2 |
| `0x18`–`0x1F` | Addresses | §2.3 |
| `0x20`–`0x23` | Indirect access | §2.4 |
| `0x24`–`0x27` | Views | §2.5 |
| `0x28`–`0x3F` | Blocks | §2.6 |
| `0x40`–`0x5F` | Arithmetic, logic, comparison, conversion | §2.7 |
| `0x60`–`0x67` | Control | §2.8 |
| `0x68`–`0x73` | Calls and outcomes | §2.9 |
| `0x74`–`0x77` | Transactions | §2.10 |
| `0x78`–`0x7F` | Natives | §2.11 |
| `0x80`–`0xFF` | Unassigned, for VM6 | — |

Gaps inside a range are unassigned.

## 2. Instructions

Stack effects are written `[before → after]`, with the top of the stack on the right:
- `a` stands for an address cell;
- `v` for a value cell;
- `(a, n)` for a view, as two cells: its address and its length in elements (VEX-13).

Every instruction charges 1 to the budget (VEX-42), plus the extra charge shown, where `⌈x⌉` is `x` rounded up.

### 2.1 Constants and stack

**BC-7**

| Op | Mnemonic | Operands | Stack | Semantics |
|---|---|---|---|---|
| `01` | `PUSH.B` | `b` | `[→ v]` | Push the immediate, zero-extended |
| `02` | `PUSH.H` | `h` | `[→ v]` | Push the immediate, zero-extended |
| `03` | `PUSH.W` | `w` | `[→ v]` | Push the immediate as is. Negative constants are pushed as their 32-bit two's complement, which is their normalized form |
| `04` | `DUP` | — | `[x → x x]` | |
| `05` | `DROP` | — | `[x →]` | |
| `06` | `SWAP` | — | `[x y → y x]` | |
| `07` | `OVER` | — | `[x y → x y x]` | |
| `08` | `DUP2` | — | `[x y → x y x y]` | Duplicates a view |
| `09` | `DROP2` | — | `[x y →]` | Discards a view |

*Serves: VEX-6.*

### 2.2 Scalar memory, region known

**BC-8** The compiler knows the region of every global, constant and local. These instructions name it, and never decode a tag (VEX-11). `off` is a byte offset: from the current frame's base for `F`, and from the start of the region otherwise.

| Op | Mnemonic | Operands | Stack | Semantics |
|---|---|---|---|---|
| `10` | `LDF` | `T h` | `[→ v]` | Load from the frame |
| `11` | `STF` | `T h` | `[v →]` | Store into the frame |
| `12` | `LDS` | `T w` | `[→ v]` | Load from `SESSION` |
| `13` | `STS` | `T w` | `[v →]` | Store into `SESSION` |
| `14` | `LDC` | `T w` | `[→ v]` | Load from `CONST` |
| `15` | `LDP` | `T w` | `[→ v]` | Load from `PERSISTENT`, through the HAL (VEX-26, HAL-16) |
| `16` | `STP` | `T w` | `[v →]` | Store into `PERSISTENT` as one atomic update (VEX-28, HAL-17) |

- **Loads** read `size(T)` bytes, little-endian, and normalize them.
- **Stores** write the low `size(T)` bytes of the cell.
- **Failures:** a failed persistent access ends execution with the HAL's status (HAL-7, BC-37).

*Serves: VEX-7, VEX-11, VEX-26, VEX-28, STA-11.*

### 2.3 Addresses

**BC-9**

| Op | Mnemonic | Operands | Stack | Semantics |
|---|---|---|---|---|
| `18` | `ADDR` | `R w` | `[→ a]` | The address of byte `w` of region `R`. For `STACK`, `w` is relative to the current frame's base, and the result is an absolute stack address |
| `19` | `INDEX` | `h w` | `[a i → a']` | Element `i` of a fixed array of `w` elements of `h` bytes at `a`: `a + i × h`. If `i ≥ w`, the result is `trap(BOUNDS)` |
| `1A` | `INDEXV` | `h` | `[a n i → a']` | Element `i` of the view `(a, n)` of `h`-byte elements. If `i ≥ n`, the result is `trap(BOUNDS)` |
| `1B` | `FIELD` | `h` | `[a → a']` | `a + h`: a field at offset `h` of a structure at `a` |

An index cell is compared as an unsigned 32-bit value. All index types are unsigned (EXP-39), so this is the language's check. A constant index into a fixed array is checked by the compiler (CEX-10); it uses `FIELD` with the element's offset.
*Serves: V-14; VEX-11, VEX-16, EXP-39, STM-9.*

### 2.4 Indirect access

**BC-10**

| Op | Mnemonic | Operands | Stack | Semantics |
|---|---|---|---|---|
| `20` | `LDI` | `T` | `[a → v]` | Load through the address, in whatever region its tag names |
| `21` | `STI` | `T` | `[a v →]` | Store through the address. Into `PERSISTENT`, one atomic update. The address is always evaluated before the value (STM-9) |

The compiler never stores through an address into `CONST` or `REQUEST` (VEX-12).
*Serves: VEX-12, VEX-28, STM-9, FUN-23.*

### 2.5 Views

**BC-11**

| Op | Mnemonic | Operands | Stack | Semantics |
|---|---|---|---|---|
| `24` | `VIEW` | `w` | `[a → a w]` | A fixed array of `w` elements at `a`, as a view |
| `25` | `SLICE` | `h` | `[a n s e → a' (e − s)]` | The slice `[s..e]` of the view `(a, n)` of `h`-byte elements: `a' = a + s × h`. If `s > e` or `e > n`, the result is `trap(BOUNDS)` (FUN-20) |

A slice of a fixed array is `VIEW` followed by `SLICE`. A view's `.length` is its second cell, which the compiler loads directly from the frame (EXP-40).
*Serves: V-14; VEX-13, VEX-16, FUN-18 to FUN-21, EXP-40.*

### 2.6 Blocks

**BC-12** Block instructions move or inspect `k` bytes in one go. Each charges an extra `⌈k / 16⌉`.

| Op | Mnemonic | Operands | Stack | Semantics |
|---|---|---|---|---|
| `28` | `COPY` | `w` | `[d s →]` | Copy `w` bytes from `s` to `d` |
| `29` | `COPYV` | `h` | `[d n s m →]` | Slice assignment: copy the view `(s, m)` into the view `(d, n)` of `h`-byte elements. If `n ≠ m`, the result is `trap(BOUNDS)`, and nothing is stored (FUN-24) |
| `2A` | `FILL` | `T w` | `[d v →]` | Store `v` as type `T` into each of `w` consecutive elements at `d` |
| `2B` | `FILLB` | `h w` | `[d s →]` | Copy the `h`-byte element at `s` into each of `w` consecutive elements at `d` |
| `2C` | `ZERO` | `w` | `[d →]` | Store `w` zero bytes at `d`: a default value (VEX-5) |
| `2D` | `WIPE` | `w` | `[d →]` | As `ZERO`, for a `wipe` statement. It is never removed or merged by any tool or VM (VEX-38) |
| `2E` | `WIPEV` | `h` | `[d n →]` | `wipe` of the view `(d, n)` of `h`-byte elements |
| `2F` | `EQUAL` | `h` | `[a n b m → v]` | `equal`: `1` if `n = m` and the `n × h` bytes are equal, else `0`. Its time depends only on `n`, `m` and `h` (PLT-31) |
| `30` | `COMPARE` | `T` | `[a n b m → v]` | `compare`: `-1`, `0` or `1` as an `i8`, comparing elements of type `T` by value from index 0 (EXP-54) |
| `31` | `ENCODE` | `T ord` | `[d v →]` | `encode_be` or `encode_le`: write the `size(T)` bytes of `v` at `d`, in the given order |
| `32` | `DECODE` | `T ord` | `[a n → v]` | `decode_be` or `decode_le`: if `n ≠ size(T)`, the result is `trap(BOUNDS)`; otherwise read the bytes in the given order, as `T` |

- **Overlap.** `COPY`, `COPYV` and `FILLB` behave as if the source were read completely before the destination is written (VEX-15).
- **Persistent destinations.**
  - A destination in `PERSISTENT` is written as one atomic update (VEX-28). When the source is also persistent, `COPY` and `COPYV` use the HAL's copy (HAL-18).
  - A destination larger than the atomic capacity is `trap(TXN-CAPACITY)` before anything is stored (VEX-29).
  - `FILL`, `ZERO` and `WIPE` into a persistent destination are a single atomic update too.
- **Equality by bytes.** `EQUAL` compares bytes. Equal values of one type have equal encodings (VEX-4), so byte equality is element equality.
- **Values first.** `FILL` and `FILLB` take their element value before writing anything (EXP-44). The compiler first places an aggregate element value in a frame temporary.

*Serves: VEX-15, VEX-28, VEX-29, VEX-36 to VEX-38, EXP-36, EXP-37, EXP-44, EXP-53, EXP-54, FUN-24, STM-23.*

### 2.7 Arithmetic, logic, comparison and conversion

**BC-13 Checked arithmetic** follows chapter 6 for the type `T`, on normalized operands `[x y → r]` (or `[x → r]` for `NEG`):

| Op | Mnemonic | Traps |
|---|---|---|
| `40` | `ADD T` | `OVERFLOW`, `UNDERFLOW` (EXP-23) |
| `41` | `SUB T` | `OVERFLOW`, `UNDERFLOW` |
| `42` | `MUL T` | `OVERFLOW`, `UNDERFLOW` |
| `43` | `DIV T` | `DIV-ZERO`; `OVERFLOW` for the minimum ÷ −1. Truncates toward zero (EXP-24) |
| `44` | `REM T` | `DIV-ZERO`. The minimum `% −1` is 0 (EXP-24) |
| `45` | `NEG T` | `NEGATION` for the minimum (EXP-25) |

The C VM computes each result in a wider type, or with explicit checks, so that the host processor's behaviour on overflow or division never shows (EXP-24).
*Serves: V-25; EXP-23 to EXP-25.*

**BC-14 Wrapping and checked intrinsics.**

| Op | Mnemonic | Stack | Semantics |
|---|---|---|---|
| `46` | `WADD T` | `[x y → r]` | `wrapping_add`: the result modulo 2^N, normalized (EXP-30) |
| `47` | `WSUB T` | `[x y → r]` | `wrapping_sub` |
| `48` | `WMUL T` | `[x y → r]` | `wrapping_mul` |
| `49` | `CADD T` | `[x y → r]` | `checked_add`: sets the outcome register (BC-30). `Ok` with `r`, or `Err` with `Overflow` or `Underflow` and `r = 0` (EXP-29) |
| `4A` | `CSUB T` | `[x y → r]` | `checked_sub` |
| `4B` | `CMUL T` | `[x y → r]` | `checked_mul` |
| `4C` | `CDIV T` | `[x y → r]` | `checked_div`: also `DivisionByZero`, and `Overflow` for the minimum ÷ −1 |
| `4D` | `CREM T` | `[x y → r]` | `checked_rem`: `DivisionByZero`; the minimum `% −1` is `Ok(0)` |
| `4E` | `CNEG T` | `[x → r]` | `checked_neg`: `Overflow` for the minimum |

*Serves: EXP-29, EXP-30, VEX-23, VEX-24.*

**BC-15 Bitwise operations and shifts** apply to unsigned types only (EXP-17, EXP-18):

| Op | Mnemonic | Stack | Semantics |
|---|---|---|---|
| `50` | `AND` | `[x y → r]` | Bitwise and |
| `51` | `OR` | `[x y → r]` | Bitwise or |
| `52` | `XOR` | `[x y → r]` | Bitwise exclusive or |
| `53` | `INV T` | `[x → r]` | `~x` within the width of `T` (EXP-27) |
| `54` | `SHL T` | `[x n → r]` | `x << n` within the width of `T`. `n ≥` the width is `trap(SHIFT)` (EXP-26) |
| `55` | `SHR T` | `[x n → r]` | `x >> n`, inserting zeros. `n ≥` the width is `trap(SHIFT)` |

On normalized unsigned operands, `AND`, `OR` and `XOR` give normalized results, so they need no type.
*Serves: EXP-17, EXP-18, EXP-26, EXP-27.*

**BC-16 Comparisons and Boolean negation** produce `1` or `0`:

| Op | Mnemonic | Stack | Semantics |
|---|---|---|---|
| `56` | `EQ` | `[x y → v]` | `x == y`, for integers, `bool` and enums (EXP-15, EXP-28) |
| `57` | `NE` | `[x y → v]` | `x != y` |
| `58` | `LT T` | `[x y → v]` | `x < y`, signed or unsigned according to `T` (EXP-14) |
| `59` | `LE T` | `[x y → v]` | `x <= y` |
| `5A` | `GT T` | `[x y → v]` | `x > y` |
| `5B` | `GE T` | `[x y → v]` | `x >= y` |
| `5C` | `BNOT` | `[x → v]` | `not x` (EXP-16) |

`and` and `or` are compiled to jumps, so that the right operand is evaluated only when needed (EXP-21).
*Serves: EXP-14 to EXP-16, EXP-21, EXP-28.*

**BC-17 Conversions.**

| Op | Mnemonic | Operands | Stack | Semantics |
|---|---|---|---|---|
| `5D` | `CCONVERT` | `T T'` | `[x → r]` | `checked_convert<T'>` of a value of source type `T`: sets the outcome register. `Ok` with `r = x` if the value is in the range of `T'`, otherwise `Err` with `ConversionRange` and `r = 0` (EXP-33) |
| `5E` | `TRUNC` | `T` | `[x → r]` | `truncate<T>`: the low bits of the 32-bit two's complement of `x`, normalized as `T` (EXP-34) |

`convert<T>` (EXP-32) produces no instruction. It is accepted only when every source value fits `T`, and a normalized cell already holds the value.
*Serves: EXP-31 to EXP-35.*

### 2.8 Control

**BC-18**

| Op | Mnemonic | Operands | Stack | Semantics |
|---|---|---|---|---|
| `60` | `JMP` | `rel` | `[→]` | Jump |
| `61` | `JZ` | `rel` | `[v →]` | Jump if `v` is 0 |
| `62` | `JNZ` | `rel` | `[v →]` | Jump if `v` is not 0 |
| `63` | `SWITCH` | `h`, then `h` × `rel` | `[v →]` | Jump to the `v`-th offset. Each offset is relative to the end of the whole instruction. `v < h` always holds, because `v` is an enum ordinal and the table lists every variant (STM-16) |

Jumps stay inside the current function. A function body larger than a `rel` can span is rejected by the compiler in version 0. Loops, `if`, `while`, `for`, `break`, `continue`, `require` and `match` on enums all compile to these instructions (Annex A).
*Serves: STM-11 to STM-16, STM-19.*

### 2.9 Calls and outcomes

**BC-19**

| Op | Mnemonic | Operands | Stack | Semantics |
|---|---|---|---|---|
| `68` | `CALL` | `h` | `[args → payload?]` | Call function `h` (BC-25) |
| `69` | `RET` | — | `[…]` | Return `Ok` with no scalar payload |
| `6A` | `RETV` | — | `[… v]` | Return `Ok(v)` with a scalar payload |
| `6B` | `ERR` | `cat h` | `[…]` | Return `Err` with category `cat` and code `h` |
| `6C` | `FWD` | — | `[…]` | Return `Err` with the error in the outcome register: propagation and forwarding |
| `6D` | `JERR` | `rel` | `[→]` | Jump if the outcome register holds `Err` |
| `6E` | `JERRIS` | `cat h rel` | `[→]` | Jump if the outcome register holds `Err` with category `cat` and code `h` |
| `6F` | `JERRCAT` | `cat rel` | `[→]` | Jump if the outcome register holds `Err` of category `cat` |
| `70` | `ERRCODE` | — | `[→ v]` | Push the code in the outcome register, as a `u16`. Used for `Err(Set(code))` (OUT-21) |
| `71` | `ERRGET` | — | `[→ v]` | Push the whole error in the outcome register as one cell, `category << 16 \| code`. Used to save an error binding (OUT-14) |
| `72` | `ERRRAISE` | — | `[v →]` | Return `Err` with the error in the cell, as saved by `ERRGET` |

An aggregate `Ok` payload has already been written to the caller's slot when `RET` executes (BC-27). Every return erases the frame (BC-28).
*Serves: VEX-17 to VEX-23, OUT-1 to OUT-22.*

### 2.10 Transactions

**BC-20**

| Op | Mnemonic | Semantics |
|---|---|---|
| `74` | `TXN.BEGIN` | Begin the transaction (HAL-19). The compiler guarantees that none is active (TXN-10) |
| `75` | `TXN.COMMIT` | Commit. `CL_COMMIT_FAILED` is `trap(COMMIT)` (TXN-12); `CL_TXN_CAPACITY` is `trap(TXN-CAPACITY)` |
| `76` | `TXN.ABORT` | Abort, for `abort`, and for the error paths of `attempt` and `require` inside the block (TXN-18) |

A trap while a transaction is active aborts it during cleanup (VEX-40). The compiler emits no abort for traps.
*Serves: VEX-31, TXN-1 to TXN-18.*

### 2.11 Natives

**BC-21** `78` `NATIVE h`: call the catalog API with native number `h` (§5), with the arguments and results of BC-34. It charges an extra 8, plus `⌈k / 16⌉`, where `k` is the total length in bytes of its view arguments.
*Serves: V-26; VEX-33, VEX-42.*

## 3. Frames and calls

**BC-22 Frame layout.** A frame begins at an absolute stack address `fp`, and has the size the function table records (IMG-6):

| Offset | Size | Contents |
|---:|---:|---|
| 0 | 4 | The return address: the caller's code offset |
| 4 | 4 | The caller's `fp` |
| 8 | `4 × argc` | The parameter cells, in declaration order (BC-24) |
| `8 + 4 × argc` | — | Locals and temporaries, at offsets the compiler assigns |
| — | — | The operand area, up to the function's maximum depth |

*Serves: VEX-17, VEX-18.*

**BC-23 The operand area.** The operand stack of a frame starts right after the frame's fixed part. An operand cell is stored as 4 bytes, little-endian. Operand cells and the bytes of the frame share the `STACK` region (VEX-7).
*Serves: VEX-17.*

**BC-24 Parameters.** Every parameter is passed as cells:
- a scalar is one normalized cell;
- a `ref` or `inout` reference to a value type is one address cell;
- a view is two cells, the address and then the length;
- a **by-value aggregate** is one address cell, pointing to the argument's value. The callee's first instructions copy it into a local of the function (`COPY`).

The copy happens before any other code of the callee runs, so it is the independent copy of FUN-17. Later arguments cannot change the source in between, because arguments contain no calls (EXP-49). A scalar parameter stored as a cell can be loaded with `LDF T` for its own type, because the layout is little-endian (VEX-4).
*Serves: VEX-20, FUN-11, FUN-17.*

**BC-25 `CALL h`.** The function table entry `h` gives `argc` and the frame size (IMG-6).
1. Pop `argc` cells.
2. The new frame starts at the current operand position.
3. Write the return information.
4. Store the cells as the parameters.
5. Zero the rest of the frame: every local starts at its default value (VEX-5).
6. Continue at the callee's first instruction.

No C call is made (VEX-19).
*Serves: VEX-17 to VEX-20, VEX-5.*

**BC-26 Return.** `RET`, `RETV`, `ERR` and `FWD`:
1. set the outcome register (`Ok`, or `Err`);
2. erase the frame (BC-28);
3. restore the caller's `fp` and code position;
4. leave the operand position at the old frame's start.

Then `RETV` pushes its payload cell. A call to a function with a scalar payload always pushes one cell, `0` on `Err`, so that the operand depth after a call does not depend on the outcome.
*Serves: VEX-21, VEX-23.*

**BC-27 Aggregate payloads.** A function whose payload is a structure or an array has one hidden last parameter: the address of a slot that the caller reserves. The callee writes the payload there before `RET`. When a call is forwarded (`return c;`), the caller passes its own slot address on.
*Serves: VEX-21, OUT-5.*

**BC-28 Erasure.** When a frame ends, by return or `Err`, its whole extent (the frame size of IMG-6) is zeroed before the caller resumes (VEX-22). After a trap, the VM zeroes the used stack (VEX-40).
*Serves: PLT-35, VEX-22.*

**BC-29 Entry frames.** The VM starts each entry (VEX-45) by building the entry function's frame with an empty return address:
- for `command(request, response)`: the request view `(REQUEST:0, len)` and the response view `(RESPONSE:0, capacity)`, four cells;
- for `on_select(response)`: the response view, two cells;
- for `on_install` and `on_session_start`: no cells.

A return from the entry frame ends the entry with its result (VEX-25). For a command, `RETV` with a count above the response capacity is `trap(RESPONSE-COUNT)`.
*Serves: VEX-25, VEX-45, HEP-2, HEP-9, BP-50a.*

## 4. Outcomes

**BC-30 The outcome register** holds `Ok`, or `Err` with a category and a code (VEX-23). These set it:
- every return (BC-26);
- `NATIVE`;
- the checked intrinsics (BC-14);
- `CCONVERT`.

Nothing else changes it.
*Serves: VEX-23, VEX-24.*

**BC-31 Compiling outcome forms.**

| Source | Instructions |
|---|---|
| `attempt c` | `c`, then `JERR` to a `FWD` |
| `attempt c` inside a transaction of the same function | `c`, then `JERR` to `TXN.ABORT` and `FWD` (TXN-18) |
| `attempt c else M` | `c`, then `JERR` to `ERR M` (preceded by `TXN.ABORT` inside a transaction) |
| `ignore c;` | `c`, then `DROP` of a scalar payload |
| `return c;` | `c`, then `JERR` to `FWD`, else `RETV` or `RET` |
| `return Err(M);` and `abort Err(M);` | `ERR M` (preceded by `TXN.ABORT` for `abort`) |
| `return Err(e);` of an error binding | The arm saves `e` with `ERRGET` on entry; `return Err(e)` is `LDF` and `ERRRAISE`. The arm may call other functions first (OUT-14), which overwrite the register |
| `match c { Ok(x) … Err(A.M) … Err(e) … }` | `c`; `JERRIS` for each specific arm; `JERR` to the catch-all; the `Ok` arm stores the payload into `x` |
| `Err(Set(code))` | `JERRCAT app` to the arm, which stores `ERRCODE` into `code` |
| `require c else M;` | `c`, `JNZ` over `ERR M` (with `TXN.ABORT` inside a transaction) |

*Serves: OUT-5 to OUT-22, STM-19, STM-24, TXN-18.*

## 5. Natives

**BC-32 Native numbers.** Each catalog API has a fixed number. A later profile may add numbers, but never changes or reuses one (V-26):

| # | API | # | API | # | API |
|---:|---|---:|---|---:|---|
| 1 | `card.key.generate` | 13 | `card.crypto.begin_digest` | 25 | `card.cbor.write_head` |
| 2 | `card.key.import` | 14 | `card.crypto.begin_mac` | 26 | `card.cbor.write_int` |
| 3 | `card.key.export_public` | 15 | `card.crypto.begin_sign` | 27 | `card.tlv.head` |
| 4 | `card.key.delete` | 16 | `card.crypto.begin_verify` | 28 | `card.tlv.skip` |
| 5 | `card.crypto.digest` | 17 | `card.crypto.update` | 29 | `card.tlv.validate` |
| 6 | `card.crypto.mac` | 18 | `card.crypto.finish` | 30 | `card.der.write_head` |
| 7 | `card.crypto.sign` | 19 | `card.crypto.finish_verify` | 31 | `card.der.write_integer` |
| 8 | `card.crypto.verify` | 20 | `card.crypto.cancel` | 32 | `card.der.integer_size` |
| 9 | `card.crypto.agree` | 21 | `card.random.fill` | 33 | `card.cbor.write_string` |
| 10 | `card.crypto.derive` | 22 | `card.cbor.validate` | 34 | `card.cbor.write_bool` |
| 11 | `card.crypto.encrypt` | 23 | `card.cbor.head` | | |
| 12 | `card.crypto.decrypt` | 24 | `card.cbor.skip` | | |

Number 0 is never valid. The numbers follow the order of `platform/base-catalog.txt`. Numbers from `0xF000` are reserved for the test-only catalog of the conformance suite (`card.test.*`, V-33). Only test builds of a VM provide them, so a production VM rejects an image that imports one (IMG-11).
*Serves: V-26; PLT-25, BP-17.*

**BC-33 The VM knows each native's signature.** Argument cells and payload kind are fixed by the catalog. The VM's native table records them, so `NATIVE` carries no argument count.
*Serves: V-26.*

**BC-34 Native arguments and results.**
- **Arguments** are passed as for a function call (BC-24): scalars and enums as cells, views as two cells, and a by-value structure (`KeySpec`) as the address of its value.
- **A `u32` or `bool` payload** is pushed as one cell, which is `0` on `Err`.
- **A structure payload** (`CborHead`, `TlvHead`) is written to a slot whose address is the hidden last argument (BC-27).
- **The outcome register** receives `Ok`, or `Err` with the `CardError` code (VEX-24).

*Serves: VEX-33, VEX-34, BP-5, BP-6.*

## 6. Budget charges

**BC-35** In version 0:
- every instruction charges 1;
- block instructions add `⌈bytes / 16⌉` (BC-12);
- `NATIVE` adds 8 plus `⌈view bytes / 16⌉` (BC-21).

A charge that would take the counter below zero is `trap(EXHAUSTED)` before the instruction has any effect (VEX-42). VM6 may recalibrate these figures, but a charge always depends only on the program, its state and its inputs (RTF-5).
*Serves: V-18; VEX-42, RTF-5, RTF-6.*

## 7. Failures

**BC-36 Trap order.** Within one instruction, its checks are made before any effect, in the order this document lists them. A trapping instruction stores nothing.
*Serves: RTF-5, STA-12, VEX-30.*

**BC-37 HAL statuses.** When a HAL call made by an instruction (other than `NATIVE`) returns anything but `CL_OK`:
- `CL_TXN_CAPACITY` is `trap(TXN-CAPACITY)`;
- `CL_COMMIT_FAILED` is `trap(COMMIT)`;
- `CL_FATAL` ends the entry with no result (VEX-43, HAL-7).

For `NATIVE`, a `CardError` code sets the outcome register (BC-34). The other three statuses behave as above.
*Serves: HAL-7, VEX-29, VEX-31, VEX-43.*

## 8. What the compiler guarantees

**BC-38** A version 0 image is trusted (V-1). Its compiler guarantees, for every function:
- the operand depth at each instruction is the same along every path, and stays within the function's maximum;
- every jump lands on an instruction of the same function;
- types are used as BC-3 allows;
- stores never target `CONST` or `REQUEST`;
- no `TXN.BEGIN` executes while a transaction is active;
- every path ends in a return.

The VM relies on these, and checks none of them (VEX-1).
*Serves: V-1; VEX-1, VEX-41.*

## 9. Change log

| Date | Change | Reason |
|---|---|---|
| 2026-11-19 | Version 0 drafted (VM3) | — |
| 2026-11-20 | Added `ERRGET` (`71`) and `ERRRAISE` (`72`) to BC-19; BC-31's error-binding row uses them | VM4 stage 2: a catch-all arm may call other functions before `return Err(e)`, so the outcome register cannot be relied on (OUT-14) |
| 2026-11-20 | IMG-6: the reserved field of a function entry is now `operand_base` | VM5 stage 2: `CALL` must know where the operand area starts (BC-25), and the frame size alone does not say |
| 2026-11-20 | BC-32: numbers from `0xF000` reserved for the test-only catalog | V-33 |

## Annex A: compiling the language constructs

Each construct from the paper check of `vm/execution-model.md`, and its instruction sequence:

| Construct | Instructions |
|---|---|
| Local scalar, read or write | `LDF` / `STF` |
| Session, persistent and constant scalars | `LDS` / `STS`, `LDP` / `STP`, `LDC` (constant scalars are usually folded into `PUSH`) |
| `var x: T;` | `ZERO size(T)` on the local's address, or `PUSH 0` and `STF` for a scalar. Needed because a declaration in a loop resets each time (STM-5) |
| Array element `a[i]` | The address of `a`; `i`; `INDEX`, or `INDEXV` for a view; then `LDI` or `STI` |
| Field `s.f` | The address of `s`; `FIELD`; then `LDI` or `STI` |
| Whole aggregate assignment, constructor, array list | Build the value in a frame temporary, then `COPY` it to the destination. For a persistent destination, that is one atomic update (VEX-28, VEX-30) |
| Byte string or constant array as a value | `ADDR CONST`, then `COPY` |
| `fill(e)` | `FILL` for a scalar element; `FILLB` from a temporary for an aggregate |
| Slices, `.length` | `VIEW`, `SLICE`; the length cell |
| Slice assignment | `COPYV` |
| `ref` and `inout` arguments | The address, or the view, as cells (BC-24) |
| Compound assignment `p op= e` | The address of `p` once; `DUP`; `LDI`; `e`; the operator; `STI`. A frame or global scalar uses `LDF` and `STF` with no address |
| Arithmetic and comparison | §2.7 |
| `and`, `or` | `JZ` / `JNZ` around the right operand |
| `checked_*`, `checked_convert` | `C…` or `CCONVERT`, then the outcome forms of BC-31 |
| `wrapping_*`, `truncate`, `convert` | `W…`, `TRUNC`, nothing |
| `encode_*`, `decode_*` | `ENCODE` into a temporary or the destination; `DECODE` |
| `equal`, `compare` | `EQUAL`, `COMPARE` |
| `if`, `while`, `for`, `break`, `continue` | Jumps. A `for` keeps its bound in a temporary, evaluated once (STM-14) |
| `match` on an enum | The ordinal; `SWITCH` |
| Outcome forms | BC-31 |
| `transaction`, `abort` | `TXN.BEGIN`, `TXN.COMMIT`, `TXN.ABORT` (BC-20, BC-31) |
| `wipe p;` | `WIPE` or `WIPEV` |
| Platform APIs | `NATIVE` (§5) |

Every construct maps onto version 0. No VM state is needed beyond VEX-49.

## Annex B: hand-compiled examples

These listings were produced by a throwaway assembler for version 0, so their offsets and sizes are exact. Each line shows the code offset, the encoded bytes, and the instruction.

### B.1 The counter application (`conformance/runtime/run-011-counter-application`)

**Layout:**
- **`PERSISTENT`:** `counter` at 0 and `increments` at 4 (8 bytes).
- **Function 0, `encode_counter(output)`:** `output` is at frame offsets 8 and 12. The local `bytes: u8[4]` is at 16, and `index: u32` at 20.
- **Function 2, `process`:** `request` is at 8 and 12, `response` at 16 and 20, and `operation: u8` at 24.

```text
; function 0: encode_counter(output: inout u8[]) -> u32
0000    10 02 0c 00            LDF u32 12          ; output.length
0004    01 04                  PUSH.B 4
0006    5b 02                  GE u32
0008    62 04 00               JNZ ok1
000b    6b 01 03 00            ERR app 3           ; CounterError.ResponseTooSmall
                               ok1:
000f    18 03 10 00 00 00      ADDR STACK 16       ; &bytes
0015    15 02 00 00 00 00      LDP u32 0           ; counter
001b    31 02 00               ENCODE u32 BE       ; bytes = encode_be(counter)
001e    01 00                  PUSH.B 0
0020    11 02 14 00            STF u32 20          ; index = 0
                               loop:
0024    10 02 14 00            LDF u32 20
0028    01 04                  PUSH.B 4
002a    58 02                  LT u32
002c    61 33 00               JZ done
002f    10 02 08 00            LDF u32 8           ; output.address
0033    10 02 0c 00            LDF u32 12          ; output.length
0037    10 02 14 00            LDF u32 20          ; index
003b    1a 01 00               INDEXV 1            ; &output[index]
003e    18 03 10 00 00 00      ADDR STACK 16
0044    10 02 14 00            LDF u32 20
0048    19 01 00 04 00 00 00   INDEX 1 4           ; &bytes[index]
004f    20 00                  LDI u8
0051    21 00                  STI u8              ; output[index] = bytes[index]
0053    10 02 14 00            LDF u32 20
0057    01 01                  PUSH.B 1
0059    40 02                  ADD u32
005b    11 02 14 00            STF u32 20          ; next index
005f    60 c2 ff               JMP loop
                               done:
0062    01 04                  PUSH.B 4
0064    6a                     RETV                ; Ok(4)

; function 1: increment()
0000    74                     TXN.BEGIN
0001    15 02 00 00 00 00      LDP u32 0
0007    01 01                  PUSH.B 1
0009    40 02                  ADD u32
000b    16 02 00 00 00 00      STP u32 0           ; counter = counter + 1
0011    15 02 04 00 00 00      LDP u32 4
0017    01 01                  PUSH.B 1
0019    40 02                  ADD u32
001b    16 02 04 00 00 00      STP u32 4           ; increments = increments + 1
0021    75                     TXN.COMMIT
0022    69                     RET                 ; Ok()

; function 2: command process(request: ref u8[], response: inout u8[]) -> u32
0000    10 02 0c 00            LDF u32 12          ; request.length
0004    01 01                  PUSH.B 1
0006    56                     EQ
0007    62 04 00               JNZ ok1
000a    6b 01 01 00            ERR app 1           ; CounterError.MalformedRequest
                               ok1:
000e    10 02 08 00            LDF u32 8
0012    10 02 0c 00            LDF u32 12
0016    01 00                  PUSH.B 0
0018    1a 01 00               INDEXV 1            ; &request[0]
001b    20 00                  LDI u8
001d    11 00 18 00            STF u8 24           ; operation = request[0]
0021    10 00 18 00            LDF u8 24
0025    01 02                  PUSH.B 2            ; OP_INCREMENT, folded
0027    56                     EQ
0028    61 09 00               JZ else
002b    68 01 00               CALL 1              ; attempt increment()
002e    6d 20 00               JERR fwd
0031    60 0e 00               JMP tail
                               else:
0034    10 00 18 00            LDF u8 24
0038    01 01                  PUSH.B 1            ; OP_READ
003a    57                     NE
003b    61 04 00               JZ tail
003e    6b 01 02 00            ERR app 2           ; CounterError.UnsupportedOperation
                               tail:
0042    10 02 10 00            LDF u32 16          ; response.address
0046    10 02 14 00            LDF u32 20          ; response.length
004a    68 00 00               CALL 0              ; return encode_counter(inout response)
004d    6d 01 00               JERR fwd
0050    6a                     RETV
                               fwd:
0051    6c                     FWD
```

**Sizes:** 101 + 35 + 82 = **218 bytes** of code.

**Frame sizes,** each the fixed part plus the operand area:

| Function | Fixed part | Operand area | Frame |
|---|---|---|---:|
| 0 | 24 bytes | 3 cells | 36 bytes |
| 1 | 8 bytes | 2 cells | 16 bytes |
| 2 | 25 bytes | 3 cells | 37 bytes |

The fixed part of `process` is 25 bytes, unaligned (V-13). The stack need is at most the deepest path: `process` calls `encode_counter`, so it is 37 + 36 = **73 bytes**. It is less in practice, because a callee's frame starts where the caller's arguments were popped (BC-25).

**Notes on the listing:**
- The loop's bound `4` is a constant, so it needs no temporary.
- The `ADD` that advances `index` can never trap (STM-14). It is still the checked instruction, because removing it would need a proof (EXP-22).

### B.2 FIDO2 `get_info` (`examples/fido2/ctap.card`)

**Layout:** `response` is at frame offsets 8 and 12, and the local `at: u32` is at 16. The constants `VERSION`, `AAGUID` and the four map keys are in `CONST`. `pin_set` is a persistent `bool`; offset `0x40` is used for illustration.

The function writes the 1-byte status and then 22 CBOR items. Every item follows the same pattern, shown here for the first two:

```text
0000    10 02 08 00            LDF u32 8
0004    10 02 0c 00            LDF u32 12
0008    01 00                  PUSH.B 0
000a    1a 01 00               INDEXV 1
000d    01 00                  PUSH.B 0
000f    21 00                  STI u8          ; response[0] = 0
0011    01 01                  PUSH.B 1
0013    11 02 10 00            STF u32 16      ; var at: u32 = 1
0017    10 02 10 00            LDF u32 16      ; at += attempt card.cbor.write_head(CborMajor.Map, 5, ...)
001b    01 05                  PUSH.B 5        ; CborMajor.Map
001d    01 05                  PUSH.B 5
001f    10 02 08 00            LDF u32 8
0023    10 02 0c 00            LDF u32 12
0027    10 02 10 00            LDF u32 16
002b    10 02 0c 00            LDF u32 12
002f    25 01 00               SLICE 1         ; response[at..response.length]
0032    78 19 00               NATIVE 25
0035    6d 61 03               JERR fwd
0038    40 02                  ADD u32
003a    11 02 10 00            STF u32 16
003e    10 02 10 00            LDF u32 16      ; at += attempt card.cbor.write_int(1, ...)
0042    01 01                  PUSH.B 1
0044    10 02 08 00            LDF u32 8
0048    10 02 0c 00            LDF u32 12
004c    10 02 10 00            LDF u32 16
0050    10 02 0c 00            LDF u32 12
0054    25 01 00               SLICE 1
0057    78 1a 00               NATIVE 26
005a    6d 3c 03               JERR fwd
005d    40 02                  ADD u32
005f    11 02 10 00            STF u32 16
        …                                      ; 20 more items in the same pattern
0394    10 02 10 00            LDF u32 16
0398    6a                     RETV            ; Ok(at)
                               fwd:
0399    6c                     FWD
```

**Sizes:**
- The function is **922 bytes**: 23 bytes of set-up, about 41 bytes per encoded item, and 6 bytes at the end.
- Its deepest operand stack is 8 cells, during a `write_string` call. With 20 bytes of fixed part, the frame is 52 bytes.

**Input for VM6:**
- **The cost.** Of the 41 bytes per item, 32 are the same boilerplate each time, from the idiom `at += attempt <native>(…, inout response[at..response.length])`.
- **The repeated part.** It is the load of `at` (4 bytes), the slice of `response` from `at` to its end (five instructions, 19 bytes), and `JERR`, `ADD` and `STF` (9 bytes).
- **The candidates.** A short-form `LDF` with a one-byte offset, and a "slice to end" instruction, would roughly halve this function. VM5 measures how common the pattern is across the applet before VM6 decides.
