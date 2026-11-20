# VM6 — The measured bytecode revision: detailed sub-plan

Parent: `plans_and_notes/vm-plan-of-plans.md`. Input: `plans_and_notes/VM5-measurements.md`, §3, §6 and §8 (candidates 2 to 6, measured against the VM4b compiler).
Status: decisions taken 2026-11-20. They become V-38 to V-41 in the register.
- **G1 as recommended:** dedicated short opcodes.
- **G2, G3 and G4 differently, by the user:**
  - all five candidates are taken;
  - the unused stack opcodes stay;
  - version 1 stays living through VM7.

The sections below are amended to match.

**Drafted 2026-11-20:**
- bytecode version 1, with the short forms `80`–`8B`, and image format 1;
- the compiler selects the short forms and relaxes jumps; the VM and the disassembler decode them;
- the code of all programs fell by 29.5%, and FIDO2's by 34% (`VM5-measurements.md` §9);
- annex B of `vm/bytecode.md` is regenerated from the compiler;
- all checks pass.

## 1. Scope

VM6 revises bytecode version 0 into **version 1**, using the measurements. Version 1 is the format the C VM implements (VM7). It stays living through VM7 and is frozen when the C VM is accepted.

- **It changes** the instruction set, the image format version, the prototype compiler (instruction selection), the prototype VM and disassembler (decoding), and `vm/bytecode.md` and `vm/image-format.md`.
- **It does not change** the execution model, the HAL, or any semantics. Every new instruction is a shorter encoding of an existing one, with identical behaviour, traps and budget charges.

## 2. The candidates

**How to read the measurements.** FIDO2 and the conformance suite are one applet and a set of tests, not a sample of all applets (user, 2026-11-20).
- **What they show is used** can justify a shorter form.
- **What they show is unused** is no reason to remove anything: another applet may need it.
- **Short forms are additions.** The long forms stay, so a short form never takes anything away from a program the corpus does not represent.

**Where the bytes are.** From the VM4b baseline (all programs: 30,872 bytes of code; FIDO2: 10,646):

| # | Candidate | New instructions | Replaces | Estimate from §3 |
|---|---|---|---|---|
| 2 | Short frame access | `LDF8 T off8` and `STF8 T off8`; for `u32`, also `LDFW off8` and `STFW off8`, with no type byte | `LDF` and `STF` with an offset below 256 | About 17% of all code |
| 3 | Short stack addresses | `ADDRF off8`: a frame address, with an offset below 256 | `ADDR STACK w` (6 bytes to 2) | About 1.9 KB in all |
| 4 | Slice to end | `SLICEF h base8 start8`: the view at frame offset `base8`, from the `u32` at frame offset `start8` to the view's end | `LDF LDF LDF LDF SLICE` (19 bytes to 5) | About 1.2 KB in FIDO2 |
| 5 | Small constants | `PUSH0` and `PUSH1` | `PUSH.B 0` and `PUSH.B 1` | About 1 KB in all |
| 6 | Short jumps | `JMP8`, `JZ8`, `JNZ8` and `JERR8`, with a signed 8-bit offset | The same with a 16-bit offset, when the target is in reach | About 0.8 KB in all |

**How they are chosen.** Each new instruction is selected by the compiler whenever it applies; the long forms stay.
- **Short jumps** need *branch relaxation* in the assembler: shortening one jump can bring others into reach. The assembler starts with every jump short, lengthens those that do not reach, and repeats until nothing changes.
- **Ranges.** The new opcodes take the free range `0x80`–`0xFF` (BC-6).

**Unused opcodes (G3).** `OVER`, `DUP2` and `DROP2` are emitted by no compiler path. They stay in version 1, for a future compiler.

## 3. Method (G2)

The candidates are done one at a time, in the table's order, because they overlap: a short `LDF` makes the slice-to-end instruction worth less, since that idiom is made of frame loads. Each one goes through the same steps:

1. add it to `tools/vmproto/isa.py`;
2. select it in the compiler;
3. decode and execute it in the VM;
4. teach the disassembler;
5. measure it with `measure.py`. The step counts as done only when all checks pass.

**All five candidates are taken** (G2). Each is still measured on top of the ones before it, so that the report shows each one's effect and how much they overlap. No candidate is dropped on its figures.

**The C VM's cost.** Every new instruction is a short decode path into an existing handler. The code-size cost in the C interpreter is a few bytes per instruction. Interpreter code size is not the constraint (V-2), so no candidate is rejected on that ground. The report still records the opcode count.

## 4. Version 1 (G4)

- **The bytecode.** `vm/bytecode.md` becomes "Bytecode, version 1": tables updated, new instructions added, and the annex B listings regenerated with the compiler.
- **The image format.** `vm/image-format.md` becomes format 1, and the header's `format` field is 1. The VM accepts only format 1: version 0 was never deployed, so nothing needs reading.
- **Version 1 stays living through VM7** (G4). The C VM may still change it, and every change is recorded in the change log, as for version 0 (V-28). It is frozen at the end of VM7, when the C VM passes the acceptance criteria.
- **The change log** stays, and records every difference from version 0.

## 5. Work

1. **One candidate at a time,** in the order 2, 3, 4, 5, 6, by the method of §3. The figures go into a new §9 of `VM5-measurements.md`.
2. **Publish** version 1 (§4): the documents, the format field, the register.
3. **Regenerate** annex B of `bytecode.md` from the compiler's output: the counter and `get_info`.
4. **Run all checks, and update** the plans and the README.

## 6. Decisions

G1 was taken as recommended. G2, G3 and G4 were decided by the user, against the recommendation: all five candidates are taken, the unused opcodes stay, and version 1 stays living through VM7.

| ID | Question | Options | Recommendation |
|---|---|---|---|
| G1 | How to shorten | (a) dedicated short opcodes for the measured hot cases (§2); long forms stay, and the compiler picks the shortest; (b) a general variable-length operand encoding, such as LEB128, for every offset and constant | (a). Each short opcode decodes in one step, and the hot cases are few and known. (b) makes every decode slower and the C decoder larger, to also shorten cases that are rare |
| G2 | When a candidate is kept | (a) one at a time, kept if it saves at least 1% of all code or of FIDO2's, measured on top of those kept before; (b) take all five without measuring each | (a). The candidates overlap, and only measurement shows by how much |
| G3 | Unused stack opcodes (`OVER`, `DUP2`, `DROP2`) | (a) remove them from version 1; (b) keep them for a future compiler | (a). Nothing uses them; a later version can add them back if a compiler needs them |
| G4 | What freezing means | (a) version 1 is frozen; the VM accepts only format 1, and any later change is a new version; (b) keep version 1 living through VM7 too | (a). The C VM needs a fixed target. VM7 findings, if any, become version 2 |
