# VM7b measurements: the second bytecode revision

The plan is `plans_and_notes/vm-plans/VM7b-bytecode-v2.md`. Each step adds forms to the bytecode in place: there is no version change, and nothing is frozen (V-51).

**How each figure is measured:**
- **Code size:** `tools/vmproto/revision.py`, which compiles every valid, runtime and example program with the steps switched on cumulatively.
- **The C VM's figures:** code size, `sizeof(cl_vm)` and the C stack bound, all from `vm/c/measure.py`, cross-compiled at `-Os`.
- **Each step's checks:**
  - `tools/run_checks.py` passes on every backend;
  - a mutant of the new C decoder case is caught.

## 1. Application code, step by step

| Step | FIDO2 | PIV | All programs | Saved here (all) |
|---|---|---|---|---|
| Version 1, as VM7 accepted it | 7,021 | 4,505 | 27,268 | — |
| (e) `LDFB`, `STFB` | 6,929 | 4,388 | 26,583 | 685 (2.5%) |
| (d) `ADDRH` | 6,861 | 4,305 | 26,257 | 326 (1.2%) |
| (b) compare and branch, six forms | 6,767 | 4,166 | 25,693 | 564 (2.1%) |
| (c) `SLICEFK` | 6,717 | 4,130 | 25,499 | 194 (0.8%) |
| (a) shared error exits | 6,687 | 4,104 | 25,443 | 56 (0.2%) |
| **VM7b in all** | **6,687 (−334, −4.8%)** | **4,104 (−401, −8.9%)** | **25,443 (−1,825, −6.7%)** | |

## 2. The C VM, step by step

| Step | `vm.c` code, Cortex-M4 | `vm.c` code, Cortex-M0+ | `sizeof(cl_vm)` (32-bit) | C stack bound, Cortex-M4 |
|---|---|---|---|---|
| Version 1, after VM7's F1 fix | 9,254 | 12,738 | 252 | 856 |
| (e) `LDFB`, `STFB` | 9,338 (+84) | 12,826 (+88) | 252 | 856 |
| (d) `ADDRH` | 9,406 (+68) | 12,902 (+76) | 252 | 856 |
| (b) compare and branch | 9,620 (+214) | 13,154 (+252) | 252 | 856 |
| (c) `SLICEFK` | 9,632 (+12) | 13,182 (+28) | 252 | 856 |
| (a) shared error exits | 9,632 (compiler only) | 13,182 | 252 | 856 |
| **VM7b in all** | **9,632 (+378, +4.1%)** | **13,182 (+444, +3.5%)** | **252** | **856** |

**In short.** Application code shrinks by 1,825 bytes over the corpus. The C VM's decoder grows by 378 bytes on Cortex-M4. The VM's RAM is unchanged: the context is still 252 bytes, and the stack bound is still 856.

The Cortex-M4 build of the whole VM (`vm.c` and `natives.c`) is now 16,718 bytes of code. Host speed is about the same: 158 million instructions a second with MSVC, 144 million with clang. The benchmark executes fewer instructions for the same work, because of (b).

## 3. Notes per step

**(e) `LDFB` and `STFB`.**
- **Saved:** 92 bytes of FIDO2 and 117 of PIV, 685 over all programs. That is slightly more than the 91, 116 and 679 estimated, because shorter code lets a few more jumps take their 8-bit form.
- **Cost:** two decoder cases, 84 bytes on Cortex-M4.
- **Check:** a mutant `LDFB` that sign-extends the byte fails `run-017` and five PIV checks.

**(d) `ADDRH`.**
- **Saved:** 68 bytes of FIDO2 and 83 of PIV, 326 over all programs, against an estimate of 68, 82 and 324.
- **Cost:** 68 bytes on Cortex-M4.
- **Check:** a mutant that reads the offset as 8 bits passes every runtime test, but fails nine FIDO2 checks and five PIV checks. Only the applets have persistent buffers past offset 255. The runtime tests reach `ADDRH` only with small offsets.

**(b) Compare and branch:** `JEQI8`, `JNEI8`, and the ordered `JLTI8`, `JLEI8`, `JGTI8`, `JGEI8` (L2, user).
- **Saved:** 94 bytes of FIDO2 and 139 of PIV, 564 over all programs. The estimate covered equality only: 78, 124 and 507.
- **How the compiler emits it:** the fused form wherever its 8-bit jump reaches, otherwise the original three instructions.
- **Use:** every form occurs in the corpus. Across all programs: `JNEI8` 238, `JEQI8` 62, `JGEI8` 17, `JLTI8` 6, `JGTI8` 5, `JLEI8` 2. `JLEI8` appears only in FIDO2.
- **Cost:** six opcodes in two decoder cases, 214 bytes on Cortex-M4.
- **Checks:**
  - a mutant that swaps equal and not-equal fails 31 runtime tests;
  - a mutant `JLTI8` that tests `<=` passes every runtime test, but fails 11 FIDO2 and 6 PIV checks.
- **Budget:** the fused form charges 1 where its three instructions charged 3. `vm/c/test/bench.card` now executes 816,306 instructions, down from 856,306, because the compare in its loop is now one instruction.

**(c) `SLICEFK`.**
- **Saved:** 50 bytes of FIDO2 and 36 of PIV, 194 over all programs, against an estimate of 48, 36 and 191. It occurs at all 36 sites, eight of them in runtime tests.
- **Cost:** 12 bytes on Cortex-M4. It shares `SLICEF`'s decoder case, and only the start differs.
- **Check:** a mutant that ignores the constant start fails 7 runtime tests, 8 FIDO2 checks and 4 PIV checks.

**(a) Shared error exits** (compiler only).
- **Saved:** 30 bytes of FIDO2 and 26 of PIV, 56 over all programs, against an estimate of 60, 40 and 100. The estimate was optimistic: the shared exit goes after the function's last instruction, so some of the jumps that reach it need their long form, and some compare-and-branch sites of (b) no longer reach it in 8 bits.
- **Check:** a mutant that keeps the original jump sense passes every runtime test, but fails 7 FIDO2 and 39 PIV checks. Only the two applets repeat an exit within one function, so the runtime tests do not exercise this rewrite.
- **Possible improvement:** place each shared exit next to the median of its jumps, rather than at the function's end.

## 4. What VM7b leaves

- **The estimates.** The plan's §2 corrected two estimates of `VM5-measurements.md` §10.4 before the work started: (a) and (c). Against the plan's figures, (e), (d) and (c) came within 2%, and (b) saved 11% more, because it also has the ordered forms. Only (a) fell short, saving 56 bytes where 100 were expected.
- **Only the applets reach some of the new code.** `ADDRH` beyond offset 255, `JLTI8` versus `JLEI8`, and the shared exits are exercised by the FIDO2 and PIV checks, not by the runtime tests. `run_checks` runs both applets on every backend, so the mutants are caught. A runtime test for each would not depend on the applets.
- **Nothing is frozen** (V-51). Further forms can be added in place as new applets show them.
