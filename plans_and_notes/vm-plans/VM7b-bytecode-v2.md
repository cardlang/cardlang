# VM7b — The second bytecode revision: detailed sub-plan

Planned 2026-11-21. It follows VM7 and the plan of plans' entry for VM7b (`plans_and_notes/vm-plan-of-plans.md`).

**No version change and no freeze (L3, L4, user).** The project is pre-alpha, so nothing carries a compatibility burden until a public release is made. The revision changes the bytecode in place: it is still called version 1, and the image format stays 1. VM7's freeze (V-42) is withdrawn. The tag `bytecode-v1` stays, as a marker of the state VM7 accepted, not as a promise. Every change is still recorded in the change log, `vm/bytecode.md` §9.

**Goal.** A measured revision of the bytecode. Its candidates come from the second applet, PIV: `VM5-measurements.md` §10.4, (b) to (e), plus the compiler-only (a). Each candidate is measured on both applets and on the whole corpus, as in VM6. This time each is measured twice:
- the bytes it saves, in the prototype compiler;
- what it costs the C VM's decoder, in code size on Cortex-M4.

The VM's RAM stays as it is: no candidate adds state.

## 1. Scope

- **In:**
  - the four bytecode candidates and the shared error exits;
  - the new instructions in every model: the compiler, the prototype VM, the C VM, the disassembler, and `vm/bytecode.md`;
  - a measurement report.
- **Out:**
  - F2, the 64-bit arithmetic in the C VM, which stays with VM8;
  - new language or profile features;
  - anything that removes an instruction. Unused in the corpus is not unneeded (V-40, `fido2-not-universal`).

## 2. The candidates, measured on the frozen version 1

Measured 2026-11-21 with the version-1 compiler: the sites where each candidate applies, and the bytes it would save there. The candidates overlap little, but the final figures are measured cumulatively (§3).

| # | Candidate | Proposed encoding | FIDO2 (7,021 bytes) | PIV (4,505 bytes) | All programs (27,268 bytes) |
|---|---|---|---|---|---|
| a | **Shared error exits** (compiler only): within a function, repeated `J… over ERR c` for the same error become one `ERR` that the jumps reach | No new instruction | 15 sites, 60 bytes | 10 sites, 40 | 25 sites, 100 |
| b | **Compare with a small constant and branch**: `PUSH0`, `PUSH1` or `PUSH.B k`, then a comparison, then a conditional jump | Equality: `JEQI8 k s` and `JNEI8 k s` compare the top cell with `k`, sign-extended as by `PUSH.B`, pop it, and jump. 3 bytes instead of 4 or 5; sites with a long jump keep the long sequence | 57 sites, 78 bytes | 69 sites, 124 | 298 sites, 507 |
| c | **Slice a frame view from a constant start to its end** (`request[4..request.length]`) | `SLICEFK h b k`: like `SLICEF`, with the start a constant byte. 5 bytes instead of 11 to 12 | 9 sites, 48 bytes | 6 sites, 36 | 36 sites, 191 |
| d | **`ADDR` with a 16-bit offset,** for any region: persistent buffers past `ADDRF`'s 8-bit, stack-only reach | `ADDRH R h`: 4 bytes instead of 6 | 34 sites, 68 bytes | 41 sites, 82 | 162 sites, 324 |
| e | **Byte frame loads and stores without the type byte,** like `LDFW` for `u32` | `LDFB b` and `STFB b`, `u8` only: 2 bytes instead of 3 | 91 sites, 91 bytes | 116 sites, 116 | 679 sites, 679 |
| | **All five** | | **345 bytes (4.9%)** | **398 bytes (8.8%)** | **1,801 bytes (6.6%)** |

**Two estimates of §10.4 were too high:**
- **(a):** it estimated about 200 bytes in PIV. Most of PIV's 24 `6A80` exits are in different functions, and an exit can be shared only within its function.
- **(c):** it estimated up to about 60 sites. The strict pattern, a view from frame cells sliced to its own length, has 6 sites.

**Ordered comparisons are in too (L2, user).** These are `LT`, `LE`, `GT` and `GE` with a constant, then a jump: 30 sites in all, 9 in each applet. They get typed forms, `JLTI8 T k s`, `JLEI8`, `JGTI8` and `JGEI8`, each 4 bytes instead of 5 or 6. A comparison followed by `JZ8` jumps on its negation, so the compiler uses the opposite form. With equality that makes six new instructions for (b). The table above counts only equality.

## 3. Method

As in VM6 (G2) and V-39: all candidates are taken, each is measured cumulatively, and none is dropped on its figures (L1). The order is (e), (d), (b), (c), (a), simplest first. For each:
1. **Specify it:** a new row in a new `vm/bytecode.md` §2.13, plus its budget charge. Every new instruction charges 1, like the short forms.
2. **Compiler:** the peephole that picks the new form whenever it applies (V-32: each optimisation arrives with its measured effect).
3. **Prototype VM, disassembler and C VM,** together, so that differential testing covers each step at once.
4. **Check:**
   - `run_checks` in full;
   - a mutation of the new C decoder case, which some test must catch.

   If no test reaches a new instruction, a runtime test is added, as V-37 did.
5. **Measure:**
   - the code saved, on FIDO2, PIV and all programs;
   - the C VM's code growth on Cortex-M4 and Cortex-M0+, from `vm/c/measure.py`;
   - that `sizeof(cl_vm)` and the C stack are unchanged.

**Report:** `plans_and_notes/VM7b-measurements.md`, with one row per step and a final table against version 1.

## 4. The bytecode's status (L3, L4)

- **Opcodes:** the new instructions take free opcodes from `0x8C` on. No existing instruction changes its opcode or meaning, although nothing here would forbid it before a public release.
- **Version and format:** unchanged at 1. Images, compiler and VMs move together, and nothing keeps old images working (L3).
- **Lifecycle:** the bytecode and the image format are living, with no freeze, until a public release (L4). V-51 records this and supersedes V-42's freeze. `vm/bytecode.md`, `vm/image-format.md` and V-41/V-42 are changed to say so.

## 5. Work

1. Plan (this document), and the answers to L1 to L4.
2. (e) `LDFB` and `STFB`.
3. (d) `ADDRH`.
4. (b) `JEQI8` and `JNEI8`.
5. (c) `SLICEFK`.
6. (a) shared error exits.
7. The report and the documents: `bytecode.md` §2.13 and §9; `image-format.md` and `bytecode.md` say "living"; `decisions.md` records V-51 (no freezes and no version changes before a public release) and VM7b's decisions.

**Done when:**
- every step is in, and `run_checks` passes on every backend: the reference interpreter, the prototype and both C builds;
- `VM7b-measurements.md` has each step's saving and decoder cost;
- `sizeof(cl_vm)` and the C stack bound are unchanged.

## 6. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| L1 | Which candidates | (a) all five, measured cumulatively, none dropped on its figures, as V-39 did; (b) keep a candidate only if it saves at least 1% somewhere | (a). Together they save 5% to 9% (4.9% FIDO2, 8.8% PIV), each is a cheap decode, and dropping by corpus figures is what `fido2-not-universal` warns against |
| L2 | The compare-and-branch forms | (a) `JEQI8` and `JNEI8` only: equality with a signed byte, 8-bit jumps; (b) also the four ordered comparisons, typed (`JLTI8 T k s` and so on); (c) also a frame-operand form (`LDF8` fused in) | (a). Equality is 313 of the 343 sites. Ordered forms need a type byte and save little; a fused form doubles the operand combinations |
| L3 | Which formats the VMs accept | (a) only format 2, as V-41 did for format 1, so that the decoder has one instruction set; (b) formats 1 and 2 | (a). A VM that accepts both gains nothing: version 2 only adds instructions, and the compiler emits format 2 |
| L4 | When version 2 is frozen | (a) at the end of VM7b; (b) living through VM8, so that the first embedded port can still change it | (b). VM8 is the first time the decoder meets a real Cortex-M, and F2 may suggest changes to how arithmetic is encoded |

**Answered (user, 2026-11-21):**
- **L1 (a):** all five candidates go in.
- **L2 (b):** the ordered forms are added as well.
- **L3:** no version change at all. Quoting the user: "We at an extremely early stage of development. We should not burden ourselves with backward compatibility until a public release is made."
- **L4:** nothing is frozen. Quoting the user: "Do not freeze anything. We are pre-alfa." V-51 withdraws V-42's freeze.
