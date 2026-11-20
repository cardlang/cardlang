# VM4b — Compiler improvements and missing tests: detailed sub-plan

Parent: `plans_and_notes/vm-plan-of-plans.md`. Input: `plans_and_notes/VM5-measurements.md`, candidates 1, 7 and 9.
Status: decisions F1 to F4 taken 2026-11-20, all as recommended (option (a)). They become V-34 to V-37 in the register, and V-32 is amended.

**Drafted 2026-11-20:**
- the tests `run-029` and `run-030` (generator `wp13_tests.py`) pass on both backends;
- the compiler drops unreachable code, builds aggregates in place, and reuses frame slots;
- the effect is in `VM5-measurements.md` §8: FIDO2's stack need fell from 1,003 to 837 bytes, and all code fell by 6.4%;
- all checks pass.

## 1. Scope

VM4b improves the prototype compiler where the VM5 measurements showed waste, and adds the runtime tests that the measurements showed missing. It runs before VM6, so that VM6 measures its bytecode candidates against the compiler that will actually be kept.

- **It changes** the compiler, the conformance tests, and the VM5 report.
- **It does not change** any instruction, the image format, the VM, or the HAL.
- **Candidate 8 of the report** (a 64-byte bounce buffer) is dropped. The report records it as considered and not taken: the 64 bytes are insignificant against the 1 KiB bound, and 128 leaves room for intrinsics over persistent data.

**V-32 is amended.** The plain baseline is now on record in the VM5 report. From here on, the compiler may optimise, provided each optimisation is added together with its measured effect.

## 2. The changes

### 2.1 Frame-slot reuse (candidate 1; F1)

**Today.** Every declaration and every temporary gets its own frame slot for the whole function. In FIDO2 that makes 2,318 bytes of locals and temporaries over 35 functions. `make_credential`'s frame is 511 bytes.

**Proposal: stack-like allocation by scope.**
- **Blocks.** The allocation point is saved when a block starts and restored when it ends, so the locals of sibling blocks share space. Examples are the arms of an `if` or a `match`, and successive loop bodies.
- **Statements.** The allocation point is also saved when a statement starts and restored when it ends, so the temporaries of one statement are reused by the next. Temporaries are constructor and list values, `encode_*` results, call payload slots, and `for` bounds.
- **Exceptions.** A temporary that a binding outlives (a `match` arm's payload or error binding) belongs to the arm's block, not to the statement.
- **The frame size** is the high-water mark.

**Why this is safe:**
- **Every local is initialised explicitly** when its declaration is reached. A declaration without an initialiser emits its zero fill (STM-5), so a reused slot never shows an earlier value.
- **References and views cannot outlive the call they were passed to** (FUN-16), so no reference into a reused slot survives.
- **Erasure is unaffected.** Frame erasure on exit (PLT-35) still zeroes the whole frame.
- **`wipe` is unaffected.** Its stores are still performed (PLT-34).

A liveness-based allocator (graph colouring) could save more. It is worth doing only if scope-based reuse leaves a lot on the table; the measurement will show.

### 2.2 Unreachable code (candidate 7; F2)

**Proposal:** emit nothing between a terminator (`RET`, `RETV`, `ERR`, `FWD`, `ERRRAISE`, `JMP`) and the next label that some jump targets.
- **It removes** the 212 dead `JMP`s the report counted, which are the end-of-branch jumps after a branch that returned. It also removes unreachable statements, which the language permits (STM-22).
- **Those statements are still checked.** They are resolved, typed and constant-evaluated by the checker before the compiler runs, so nothing is lost.

### 2.3 Building aggregates in place (candidate 9; F3)

**Today.** A constructor, list, `fill` or `encode_*` result is built in a temporary and then copied to its destination.

**Proposal:** build it directly in the destination where that cannot be observed:
- **the initialiser of a `var`.** The new local cannot appear in its own initialiser;
- **`return Ok(aggregate)`.** The destination is the caller's payload slot, which nothing else can reach.

**Assignments keep the temporary.** In `s = S { a: s.b, b: s.a }`, building in place would overwrite `s.a` before it is read. The right side must be complete before the store (STM-9, VEX-30).

### 2.4 Missing runtime tests (F4)

**The gap.** The report found opcodes that no program exercises:
- `CDIV`, `CMUL`, `CNEG`, `WSUB` and `WMUL`, behind which are the language features `checked_div`, `checked_mul`, `checked_neg`, `wrapping_sub` and `wrapping_mul`;
- `FIELD`, a field reached through a reference;
- `FILLB`, `fill` with an aggregate element.

**The fix: new runtime tests**, written by a generator in the usual way (`tools/generators/wp13_tests.py`, with its `*_owned.txt`):

| Test | Covers |
|---|---|
| `run-029-checked-and-wrapping` | `checked_div`, `checked_mul` and `checked_neg`: `Ok`, `Overflow`, `Underflow` and `DivisionByZero`, including the minimum ÷ −1 and the negation of the minimum. `wrapping_sub` and `wrapping_mul` at the type boundaries, for signed and unsigned types |
| `run-030-fields-through-references` | Reading and writing structure fields through `ref` and `inout` parameters, nested and in persistent storage; `fill` of an array of structures; aggregate payloads forwarded through two calls |

**Both tests are run by both backends.** The interpreter is the reference: if it disagrees with the specification, the specification wins and the interpreter is fixed. The coverage table (`coverage.py`) and the index (`rule_index.py`) are regenerated.

`OVER`, `DUP2` and `DROP2` are emitted by no compiler path. Whether to keep them is a VM6 question.

## 3. Measuring

- **The figures.** After each change, `measure.py` is rerun. The VM5 report gains a section, "§8 VM4b", giving the effect of each change on code size, frame sizes and stack need, for all programs and for FIDO2 in particular.
- **The safety of slot reuse.** Every check must still pass after every change. For slot reuse, a mutation check also confirms the tests notice when it is wrong: if two simultaneously live locals are wrongly given the same slot, at least one test must fail.

## 4. Work

1. Amend V-32 in `vm/decisions.md`; record F1 to F4 as V-34 onward; mark candidate 8 as not taken in the report.
2. Write the two tests and their generator, run them on both backends, and regenerate the coverage and the index.
3. Unreachable code (§2.2); measure.
4. Building in place (§2.3); measure.
5. Slot reuse (§2.1), with the mutation check; measure.
6. Write §8 of the VM5 report; run all checks; update the plans.

The tests come first, so that the compiler changes are made against the larger suite.

## 5. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| F1 | The slot allocator | (a) stack-like by block and statement (§2.1); (b) liveness analysis and graph colouring | (a). Simple, and it uses the language's structure; (b) only if (a) leaves much unused |
| F2 | Unreachable code | (a) emit nothing until the next jump target; (b) remove only the `JMP` that follows a terminator | (a). It is no harder, and it also drops unreachable statements |
| F3 | Building in place | (a) `var` initialisers and `return Ok(aggregate)` only; (b) also assignments, when no aliasing can occur | (a). (b) needs an aliasing analysis for a small gain |
| F4 | The missing tests | (a) `run-029` and `run-030` now, as conformance tests for both backends; (b) leave them to VM6 | (a). The semantics behind these opcodes should be tested before the instruction set is frozen |
