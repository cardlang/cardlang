# VM5 — Measurements of the prototype compiler and VM

Date: 2026-11-20. Work package VM5, stage 5; acceptance criterion 4 of V-12. Input to VM6.

**Reproducing the figures:**

```bash
python -I tools/vmproto/measure.py .
```

That prints every figure below as JSON. `tools/vmproto/check_state.py` checks V-31 and the context bound.

**What was measured:**
- **The code:** bytecode version 0 as the plain prototype compiler emits it. It folds constants and does nothing else (V-32).
- **The programs:** all 151 programs, which are the 122 valid tests, the 28 runtime tests and the FIDO2 applet.
- **The runs:** the 28 runtime scenarios, and the 59-check FIDO2 session of `check_fido2`.

## 1. Summary

| Figure | Value |
|---|---|
| **VM context, `cl_vm`** (V-2, the bound being 1 KiB) | **216 bytes** on the 32-bit model: 128 bytes of bounce buffer, and 88 of registers, region pointers and state. No other VM state exists (V-31, checked) |
| Code, all 151 programs | 31,442 bytes |
| FIDO2 applet: image / code / constants | 12,470 / 11,271 / 149 bytes |
| FIDO2 applet: `PERSISTENT` / `SESSION` | 22 / 33 bytes |
| FIDO2 applet: stack need / deepest observed | 1,003 / 867 bytes |
| FIDO2 session: instructions executed | 116,507 over 143 entries. The largest entry used 4,232 budget units |
| Opcodes used | 74 of the 84 defined |

**The headline.** The VM's own RAM is small and fixed, well inside the goal. The application's RAM is dominated by the **stack**, at about 1 KB for FIDO2. That is because the plain compiler never reuses frame slots (§4). On code size, a handful of short forms would cut the bytecode by roughly a third (§3).

## 2. The VM context

| Group | Fields | Bytes |
|---|---|---:|
| Image and sections | image pointer and size; code, constant and function-table offsets; code size; function count | 26 |
| Regions | `SESSION`, `STACK`, `REQUEST` and `RESPONSE`: pointers and sizes | 32 |
| Registers | `pc`, `fp`, `sp` | 12 |
| Outcome register | category and code | 3 |
| State | transaction, atomic update, lifecycle | 3 |
| Budget | counter and configured value | 8 |
| HAL | context pointer | 4 |
| Bounce buffer | V-22 | 128 |
| **Total** | | **216** |

- **Where it stands against the plan.** The estimate in VEX-50 was about 200 bytes; the measured figure is 216, with no packing or padding.
- **On a 64-bit host** the pointers double, which adds 32 bytes.
- **The bounce buffer** is the only part that could shrink much. It could return to 64 bytes now that the HAL takes descriptors (V-23): the reasons for 128 were fixed-size crypto operands, which descriptors now carry.

## 3. Code size

### 3.1 Where the bytes go

Over all 151 programs (31,442 bytes):

| Instruction | Count | Bytes | Share |
|---|---:|---:|---:|
| `LDF` | 2,362 | 9,448 | 30% |
| `ADDR` | 611 | 3,666 | 12% |
| `PUSH.B` | 1,648 | 3,296 | 10% |
| `STF` | 639 | 2,556 | 8% |
| `JERR` | 406 | 1,218 | 4% |
| `SLICE` | 271 | 813 | 3% |
| `NATIVE` | 253 | 759 | 2% |
| `COPY` | 119 | 595 | 2% |

In the FIDO2 applet (11,271 bytes, 3,255 instructions):

| Instruction | Count | Bytes |
|---|---:|---:|
| `LDF` | 967 | 3,868 |
| `ADDR` | 258 | 1,548 |
| `PUSH.B` | 430 | 860 |
| `STF` | 211 | 844 |
| `JERR` | 191 | 573 |
| `VIEW` | 109 | 545 |
| `SLICE` | 151 | 453 |
| `NATIVE` | 120 | 360 |

**Frame access alone is 38% of all code.** That is `LDF` and `STF`, at 4 bytes each.

### 3.2 Operand widths

| Operand | Fits a short form | Does not |
|---|---:|---:|
| `LDF` and `STF` frame offset | 2,916 below 256 | 85 |
| `LDF` and `STF` type | 2,411 are `u32` (views, indices, counts); 508 are `u8` | 82 other |
| `ADDR` offset | 572 below 256 (496 of them `STACK`) | 39 |
| Jump offset (`JMP`, `JZ`, `JNZ`, `JERR`) | 792 within ±127 | 329 |
| `PUSH.B` value | 589 zeros, 368 ones | 691 other |
| `PUSH.H`, `PUSH.W` | 6 and 14 in all | — |

### 3.3 Frequent sequences

| Sequence | Occurrences | What it is |
|---|---:|---|
| `LDF LDF LDF LDF SLICE` | 100 (82 in FIDO2) | `view[x..view.length]`: the slice of a view to its end |
| `… SLICE NATIVE JERR` | 81 | A native call with a slice argument, propagating errors |
| `LDF PUSH.B EQ JZ` | about 170 | Comparing a local with a small constant, then branching |
| A `JMP` directly after `RET`, `RETV`, `ERR` or `FWD` | 212 (25 in FIDO2) | Dead code: the `if` lowering jumps to the end after a branch that already returned |

### 3.4 Compiled against hand-written

| Function | Hand-written (VM3) | Compiled | Difference |
|---|---:|---:|---|
| FIDO2 `get_info` | 922 | 922 | The same |
| Counter `encode_counter` | 101 | 132 | The compiler puts `encode_be`'s result into a temporary and copies it, and keeps the constant loop bound in a slot |

## 4. RAM used by applications

| | FIDO2 |
|---|---:|
| `STACK` need, as the compiler computes it | 1,003 bytes |
| Deepest stack position actually reached | 867 bytes |
| `SESSION` | 33 bytes |
| `PERSISTENT` (not RAM) | 22 bytes |

**The stack need is always safe and never far off.** Over the 28 runtime tests, the deepest position reached was between 33% and 100% of the computed need, and in 15 tests exactly 100%. Over FIDO2 it was 86%.

**FIDO2's stack is made of a few large frames:**

| Function | Frame | Locals and temporaries | Operand area |
|---|---:|---:|---:|
| `make_credential` | 511 | 455 | 32 |
| `client_pin` | 469 | 409 | 36 |
| `get_assertion` | 389 | 333 | 32 |
| `derive_shared_secret` | 233 | 169 | 40 |

Locals and temporaries account for 2,318 bytes over the applet's 35 functions. The compiler gives every declaration, and every temporary, its own slot for the whole function. That includes the temporaries of constructors, of `encode_be` and of aggregate call payloads. Slots whose lifetimes do not overlap are never shared. This is the biggest RAM lever available.

## 5. Execution

| | Runtime tests (without `run-013`) | FIDO2 session |
|---|---:|---:|
| Instructions executed | 21,338 | 116,507 |
| Share that is `LDF` | 32% | 36% |
| The next most frequent | `PUSH.B`, `JZ`, `STF`, `INDEXV` | `PUSH.B`, `STF`, `ADDR`, `JERR`, `SLICE` |
| Largest budget used by one entry | 3,878 | 4,232 |

- **The budget test is left out of the first column.** `run-013`'s endless loop executes 335,000 instructions before `trap(EXHAUSTED)`, and would swamp the counts.
- **The prototype's default budget of 1,000,000 is generous.** The heaviest real entry is a FIDO2 PIN operation, at about 4,200, because the cryptography runs in the HAL and costs only a native's charge. 20,000 would be a reasonable default for the C VM.

## 6. Candidates for VM6

These are estimates from the static counts above, not measurements of an implementation. They are listed by expected effect.

| # | Change | Kind | Estimated effect |
|---|---|---|---|
| 1 | **Frame-slot reuse.** Allocate locals and temporaries by scope and lifetime, and share slots that are never live at the same time | Compiler | The largest RAM saving. FIDO2's frames are mostly locals and temporaries (2,318 bytes); a large part could be shared. To be measured |
| 2 | **Short frame access:** `LDF` and `STF` with a one-byte offset, and a form for `u32` that has no type byte | Bytecode | About 5 KB of the 31 KB (17%); about 2 KB of FIDO2's 11.3 KB |
| 3 | **Short `ADDR` for `STACK`**, with a one-byte offset (2 bytes instead of 6) | Bytecode | About 1.9 KB in all; about 1 KB in FIDO2 |
| 4 | **Slice to end:** one instruction for `view[x..view.length]` when `view` and `x` are frame slots | Bytecode | About 15 bytes per use: 1.2 KB in FIDO2 (11%) |
| 5 | **`PUSH0` and `PUSH1`** | Bytecode | About 1 KB in all |
| 6 | **Short jumps** with an 8-bit offset | Bytecode | About 0.8 KB in all |
| 7 | **No dead `JMP` after a terminator** | Compiler | 636 bytes in all, 75 in FIDO2 |
| 8 | **Bounce buffer back to 64 bytes**, now that descriptors carry the crypto operands (V-23) | VM | 64 bytes less context. **Not taken** (2026-11-20): insignificant against the 1 KiB bound, and 128 bytes leaves room for intrinsics over persistent data |
| 9 | **The `encode_*` result written straight to its destination** when the destination is a frame slot | Compiler | Small; visible in `encode_counter` |

**Taken together,** items 2 to 7 would shrink the FIDO2 bytecode from about 11.3 KB to roughly 7 KB. Items 2 and 4 overlap, because the slice idiom is made of frame loads. Item 1 is the change that matters most for RAM, which is the stated priority (V-2). It touches only the compiler, so it needs no change to the VM.

**Unused opcodes.** Ten opcodes appear in no program:
- `OVER`, `DUP2`, `DROP2`, `FIELD` and `FILLB`;
- `CDIV`, `CMUL`, `CNEG`, `WSUB` and `WMUL`.

The last five are there for language completeness, but no test exercises them. VM6 should add tests rather than remove the opcodes. `FIELD` is unused only because the compiler folds field offsets into static addresses whenever it can; a field reached through a reference would use it, and no test does.

## 8. VM4b: compiler improvements (2026-11-20)

Plan: `plans_and_notes/vm-plans/VM4b-compiler-improvements.md`. These are compiler-only changes, with no change to the bytecode, the image or the VM.

**The baseline is re-measured.** The two new runtime tests (`run-029`, `run-030`) bring the corpus to 153 programs, so the baseline below is taken again, before any compiler change. They exercise seven opcodes no program used before: `CDIV`, `CMUL`, `CNEG`, `WSUB`, `WMUL`, `FIELD` and `FILLB`.

| | Baseline | No unreachable code (V-35) | Built in place (V-36) | Slot reuse (V-34) | Change |
|---|---:|---:|---:|---:|---:|
| Code, all 153 programs | 32,973 | 32,348 | 30,872 | 30,872 | −6.4% |
| Stack need, summed over all programs | 7,715 | 7,715 | 7,122 | 6,674 | −13.5% |
| FIDO2 code | 11,271 | 11,208 | 10,646 | 10,646 | −5.5% |
| FIDO2 stack need | 1,003 | 1,003 | 916 | 837 | −16.6% |
| FIDO2 frames, summed over its 35 functions | 3,914 | 3,914 | 3,619 | 3,434 | −12.3% |

All figures are in bytes.

**The two code-size changes:**
- **No unreachable code** removes the dead jumps: 625 bytes in all.
- **Building in place** removes a temporary and a `COPY` for every aggregate `var` initialiser and `return Ok(aggregate)`: 1,476 bytes of code, and the temporaries' frame space.

**Slot reuse is safe, but saves less than hoped:**
- **It is checked.** A mutant that frees a local's slot right after its declaration makes 14 of the 30 runtime tests, and the FIDO2 check, fail.
- **It saves less than §4 suggested.** The largest frames are dominated by locals declared at the top level of the function, whose scope is the whole function. `make_credential` declares 419 bytes of them: `auth` (180), `point` (65), `credential_id` (48), `p` (44), `rp_hash` (32) and smaller ones. Its frame is now 475 bytes.
- **Liveness analysis** could overlap locals whose last use comes before another's first use. That is option (b) of F1, kept for later, and worth its complexity only if the C VM's targets need it. The alternative needs no compiler work: write such functions with narrower scopes.

**Effect on the VM6 candidates.** The figures of §3 still hold in proportion, so VM6 measures against this compiler.

## 7. Acceptance status (V-12)

| Criterion | Status |
|---|---|
| 1. Every runtime conformance test passes | 28 of 28, in `run_checks` |
| 2. `check_fido2` passes | 59 of 59, in `run_checks` |
| 3. Every valid conformance program compiles to an image | All 151 programs, in `run_checks` |
| 4. The backend reports its figures | This report: `measure.py`, and `check_state.py`, which also runs in `run_checks` |
