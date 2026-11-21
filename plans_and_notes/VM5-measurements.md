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

**What the corpus does and does not show.** The corpus is one applet, FIDO2, plus the conformance tests. It shows what is worth making shorter or faster. It is no evidence that something unused is unneeded, because other applets may rely on it (user, 2026-11-20).

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

The last five are there for language completeness, but no test exercised them. The right response was to add tests, done in VM4b, not to remove the opcodes. The same holds for the stack opcodes: unused here says nothing about other applets. `FIELD` is unused only because the compiler folds field offsets into static addresses whenever it can; a field reached through a reference would use it, and no test does.

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
- **Liveness analysis** could overlap locals whose last use comes before another's first use. That is option (b) of F1, kept for later, and worth its complexity only if the C VM's targets need it. The alternative needs no compiler work: write such functions with narrower scopes. FIDO2's shape (large top-level buffers) may not be typical, so this should be re-measured on a second applet before it is decided.

**Effect on the VM6 candidates.** The figures of §3 still hold in proportion, so VM6 measures against this compiler.

## 9. VM6: bytecode version 1 (2026-11-20)

Plan: `plans_and_notes/vm-plans/VM6-bytecode-revision.md`. The short forms are those of `vm/bytecode.md` §2.12. They are measured cumulatively, in the planned order, on the VM4b compiler, over all 153 programs:

| Step | All programs | Saved | FIDO2 | Saved |
|---|---:|---:|---:|---:|
| Version 0, with the VM4b compiler | 30,872 | — | 10,646 | — |
| + short frame access (`LDF8`, `STF8`, `LDFW`, `STFW`) | 25,316 | 5,556 (18.0%) | 8,518 | 2,128 (20.0%) |
| + `ADDRF` | 23,988 | 1,328 (4.3%) | 7,890 | 628 (5.9%) |
| + `SLICEF` | 23,526 | 462 (1.5%) | 7,506 | 384 (3.6%) |
| + `PUSH0`, `PUSH1` | 22,527 | 999 (3.2%) | 7,288 | 218 (2.0%) |
| + 8-bit jumps | 21,776 | 751 (2.4%) | 7,021 | 267 (2.5%) |
| **Version 1, total** | **21,776** | **−29.5%** | **7,021** | **−34.0%** |

The figures are bytes of code. Each saving is relative to the version-0 baseline.

**Use in FIDO2,** in its version-1 image:

| Form | Count |
|---|---:|
| `LDFW`, `STFW` | 624, 136 |
| `LDF8`, `STF8` | 49, 47 |
| `ADDRF` | 157 |
| `PUSH0`, `PUSH1` | 147, 71 |
| `SLICEF` | 64 |
| `JERR8`, `JNZ8`, `JZ8`, `JMP8` | 99, 61, 58, 49 |
| Long forms left: `LDF`, `STF`, `ADDR` | 39, 26, 34 |
| Long forms left: `JERR`, `JZ`, `JMP` | 92, 5, 2 |

**Observations:**
- **The estimates of §6 were close,** except where candidates overlap. `SLICEF` saved 462 bytes rather than the 1.2 KB estimated in FIDO2 alone, because short `LDFW`s had already shrunk the idiom it replaces. It still fires 64 times in FIDO2, not 82: a slice whose start is not a `u32` frame slot keeps the long sequence.
- **Most remaining long `JERR`s jump to the function's shared error trampoline,** at the end of the function. Placing trampolines nearer their jumps is a compiler change that could make most of them short. It is noted for later.
- **Compiled against hand-written.** `get_info` is now 502 bytes; it was 922 in version 0, by hand and compiled alike. The counter's three functions are 168 bytes, against 218 by hand in version 0.
- **Budget charges fall a little.** `SLICEF` charges 1 where its sequence charged 5 (BC-39). All tests still pass, including the budget test.
- **The rule of this report applies:** these figures come from one applet and the conformance tests. They justify the short forms, which are additions, and they say nothing against the long forms.

## 10. A second applet: PIV against FIDO2 (2026-11-21)

**What was measured.** WP12 (`plans_and_notes/spec-plans/WP12-piv.md`) added a PIV card application (`examples/piv`), chosen to broaden the corpus beyond FIDO2.
- **The code:** both applets compiled by the current compiler (VM4b, bytecode version 1).
- **The runs:** the dynamic figures come from each applet's independent check, run on `vmproto`: the 59 checks of `check_fido2` and the 69 of `check_piv`.

### 10.1 Side by side

| | FIDO2 | PIV |
|---|---:|---:|
| Source lines | 778 | 636 |
| Functions | 35 | 27 |
| Code, bytes (bytes per line) | 7,021 (9.0) | 4,505 (7.1) |
| Image, bytes | 8,220 | 5,405 |
| Natives used | 22 | 13 |
| `PERSISTENT` | 22 B | 10,002 B |
| Largest persistent destination (`max_atomic`) | 16 B | 1,900 B |
| `SESSION` | 33 B | 20 B |
| Stack need / deepest observed | 837 / 745 B (89%) | 344 / 264 B (77%) |
| Frames, summed / their locals and temporaries | 3,434 / 1,862 B | 1,376 / 364 B |
| Largest frame | `make_credential`, 475 B | `asymmetric_authenticate`, 164 B |
| Frame access (all forms), share of code | 29.5% | 27.9% |
| Instructions executed by the check / entries | 96,181 / 143 | 21,650 / 101 |
| Largest budget used by one entry | 3,882 | 912 |
| `LDFW`, share of executed instructions | 24.3% | 23.4% |

### 10.2 What holds for both

- **Frame access dominates.** It is the largest share of code in both applets, at 28% to 30% even after the short forms. Short frame access (`LDFW` and the others) is the most frequent instruction in both, statically and dynamically, and it is the best-justified short form of version 1.
- **Short jumps and `PUSH0`/`PUSH1` pay off in both.**
- **The VM's own state is the same,** 216 bytes, whatever the applet. Application RAM is the frames and `SESSION`, and both stay small. PIV's 344-byte stack and FIDO2's 837 are both far from anything that would trouble a 4 KB RAM budget (Annex B §B.11).
- **The budget is generous.** The heaviest entry of either applet uses under 4,000 instructions; 20,000 remains a reasonable default for the C VM (§5).

### 10.3 What was FIDO2-specific

- **Large frames.** FIDO2 keeps big buffers as locals (`auth`, `point`, `credential_id`); PIV keeps its large data in persistent buffers. PIV's locals and temporaries total 364 bytes over 27 functions. The question left open in §8, scope-based slot reuse against liveness analysis, is therefore **not settled in favour of liveness**: in one applet of two it would gain little. It stays deferred, to be revisited if a later applet resembles FIDO2.
- **`SLICEF`.** It is FIDO2-shaped. PIV's 60 long slices almost all start at a constant (`request[4..request.length]`), so it fires only 6 times in PIV, against 64 times in FIDO2.
- **Long `JERR`s.** FIDO2 has 92, against PIV's 26.

### 10.4 What PIV shows that FIDO2 did not

These are candidates for version 1, which stays living through VM7, or for the compiler. All are additions or compiler changes, and none removes anything (`fido2-not-universal`):

| # | Observation | Candidate | Kind | Estimate (PIV) |
|---|---|---|---|---|
| a | **Error exits repeat.** PIV has 68 `ERR`s (272 bytes, 6% of its code). 24 of them are the same `6A80`, from many `require … else Sw.WrongData` | Share one error exit per error code, as the error trampolines are already shared (`JZ8` to it, instead of `JNZ8` over an `ERR`) | Compiler | About 200 bytes (4%); FIDO2 has 64 `ERR`s, so it gains too |
| b | **Comparing with a constant and branching** (`PUSH.B` `EQ` `JZ8`, and `LDF8 … PUSH.B EQ`) is a frequent sequence in both. In PIV it comes from the instruction and tag dispatch | A compare-immediate-and-branch instruction | Bytecode | To be measured on both |
| c | **Slices from a constant start** (`request[4..request.length]`) | Generalise `SLICEF` to a constant start | Bytecode | Up to about 60 × 6 bytes in PIV |
| d | **Persistent and session addresses.** 41 long `ADDR`s remain in PIV: its buffers are at persistent offsets up to 10 KB, beyond `ADDRF`'s stack-only, 8-bit reach | `ADDR` with a 16-bit offset, for any region | Bytecode | About 80 bytes |
| e | **Byte-sized frame loads.** `LDF8 u8` appears 86 times (258 bytes, 5.7%), for request bytes and flags | A `u8` form with no type byte, like `LDFW` | Bytecode | About 86 bytes |

**Where they are decided.** The bytecode candidates (b to e) belong with VM7's possible changes to version 1, and should be measured on both applets there. Candidate (a) is compiler-only and can be done at any time.

## 7. Acceptance status (V-12)

| Criterion | Status |
|---|---|
| 1. Every runtime conformance test passes | 28 of 28, in `run_checks` |
| 2. `check_fido2` passes | 59 of 59, in `run_checks` |
| 3. Every valid conformance program compiles to an image | All 151 programs, in `run_checks` |
| 4. The backend reports its figures | This report: `measure.py`, and `check_state.py`, which also runs in `run_checks` |
