# VM7 — The C11 VM and a host HAL: detailed sub-plan

Parent: `plans_and_notes/vm-plan-of-plans.md`.
Inputs:
- the specification: `vm/execution-model.md` (VEX), `vm/hal.md` (HAL), `vm/bytecode.md` (BC, version 1), `vm/image-format.md` (IMG, format 1), and `vm/decisions.md` (V-1 to V-41);
- the measurements: `plans_and_notes/VM5-measurements.md` (§9 and §10);
- the working model: the prototype, `tools/vmproto/`.

Status: decisions taken 2026-11-21, by the user. They become V-42 to V-45 at drafting.
- **J1:** two compilers, MSVC and clang. The user installs Visual Studio 2026 first.
- **J2:** Mbed TLS, and CMake for the whole C project from the start.
- **J3:** a shared library driven through `cffi`.
- **J4, revised:** VM7 ports version 1 exactly as it is, with no new instructions. The PIV candidates (b) to (e) move to a later *version 2* step, measured with the C VM on both applets. The shared error exits, candidate (a), are compiler-only and can be done at any time; VM7 does not need them.
- **Toolchains,** given by the user:
  - Visual Studio 2026, which provides MSVC, CMake and Ninja;
  - the portable llvm-mingw toolchain in `<workspace>\llvm-mingw-20261117-ucrt-i686`, a clang for the MinGW/POSIX world.

  Together they cover both Windows and POSIX-style builds.
- **Python:** only the project's uv environment (`uv run python`). Dependencies are added with `uv add`; `cffi` is the first.

§2 to §4 are amended below; the decision table keeps the options as they were offered.

**Step 1 done (2026-11-21):**
- `vm/c/CMakeLists.txt`, `cmake/llvm-mingw-x86_64.cmake`, `build.py` and `README.md`;
- `src/header_check.c` builds into `cardlang_vm` warning-free with MSVC 19.52 and clang 23.1.6, both in strict C11;
- `cl_hal.h` and `cl_hal_test.h` compile as VM2 wrote them, with static assertions on the status codes and enum ordinals.

## 1. Scope

VM7 writes the product VM in portable C11, a host (PC) HAL to run it, and a harness backend `cvm`, so that the C VM runs the same tests as the two other backends (V-10, V-12).

- **It keeps the Python compiler.** The prototype compiler (VM4) stays the compiler; images are produced by it. V-11 asked where the compiler's long-term home is, and the answer is `tools/vmproto/` for now. A compiler in another language is not part of VM7.
- **VM7 is a pure port.** The C VM implements version 1 exactly as the prototype runs it, so every difference found by differential testing is a porting bug. Version 1 stays living only for real defects found while porting (V-41). It is frozen when the C VM is accepted. New instructions are version 2's.
- **Not in VM7:**
  - an embedded port (VM8);
  - the real-world bridge to host software (VM9, recorded 2026-11-21);
  - a production HAL for a particular chip.

## 2. The deliverables

| Path | Contents |
|---|---|
| `vm/c/include/cl_vm.h` | The VM's API to the platform: `cl_vm_load`, the entry points of VEX-45, `cl_config`, and the result codes (IMG-11) |
| `vm/c/include/cl_hal.h`, `cl_hal_test.h` | Exist (VM2). Checked by a real compiler for the first time, and corrected where needed |
| `vm/c/src/vm.c` | The loader, the interpreter loop (one function, no recursion: VEX-19), regions and addresses, frames, outcomes, traps and cleanup, and the budget |
| `vm/c/src/natives.c` | The native library (HAL-3): argument handling, the identifier space, the operation table and lifetimes, the error precedence, and CBOR, BER-TLV and DER in C. No cryptography (HAL-1) |
| `vm/c/src/iso7816.c`, `raw.c` | The binding adapters: status words (BP-51) and the raw envelope (BP-53) |
| `vm/c/hal-host/` | The host HAL: storage with a journal (atomic updates, transactions, recovery, the interrupt hook), the key store joining transactions, the crypto backend (J2), and the deterministic generator of the test hook |
| `vm/c/test/` | A shared library (`cvm`) exporting a small C interface that the Python backend calls through `cffi` (J3, user). `cffi` is a third-party package, not yet installed; installing it with `pip` is asked for when it is needed |
| `tools/harness/backends.py` | The backend `cvm`: compile with the prototype compiler, then load the image into the C VM |

**The build is CMake** (J2, user): one `vm/c/CMakeLists.txt` for the VM library, the host HAL, the `cffi`-facing shared library and the test programs. It is built with both compilers (J1):
- **MSVC:** `cl`, with `/std:c11 /W4 /WX`.
- **clang:** the llvm-mingw toolchain (MinGW targets, POSIX-style), with `-std=c11 -Wall -Wextra -Wpedantic -Werror`.

A build that warns on either compiler fails. Visual Studio's CMake and Ninja are used, so nothing else needs installing.

**Mbed TLS** (J2, user) is the host HAL's crypto backend, through its PSA Crypto API.
- **How it gets here:** CMake's `FetchContent`, pinned to a release of the 3.6 LTS branch. Whether to use the LTS or a 4.x release (whose crypto lives in TF-PSA-Crypto) is checked when it is fetched.
- **Where it goes:** into the build tree, which git ignores. It is not committed.
- **What it does:** keys, ECDSA (including signing a given digest), ECDH, HMAC, HKDF, AES-CBC and SHA-256.
- **Determinism:** the test hook seeds a deterministic generator, as in the Python test HAL, so scenarios that depend on generated keys give the same results on every backend. Private keys are generated from that generator and imported into PSA, so every backend computes the same key.

**Coding rules,** to be stated in `vm/c/README.md`:
- C11, compiled with `-std=c11 -Wall -Wextra -Wpedantic -Werror`;
- no dynamic allocation, no global mutable state (V-8), and no recursion;
- fixed-width integer types throughout;
- every multi-byte value decoded byte by byte, so the code is endianness-neutral (V-13);
- every `CL_` status checked.

## 2a. Toolchain facts (checked 2026-11-21)

| Tool | Where | Version | Notes |
|---|---|---|---|
| MSVC | Visual Studio 2026 Community (18.12.1), `VC\Tools\MSVC` | 14.52.37025 | Set up by `VC\Auxiliary\Build\vcvars64.bat`, which needs `C:\Program Files (x86)\Microsoft Visual Studio\Installer` (for `vswhere.exe`) on the path |
| CMake | Visual Studio 2026, `Common7\IDE\CommonExtensions\Microsoft\CMake` | 4.3.1-msvc1 | |
| Ninja | The same folder | 1.13.2 | |
| clang | `<workspace>\llvm-mingw-20261117-ucrt-i686` | 23.1.6 | The default target is `i686`. The DLL must be built with `x86_64-w64-mingw32-clang`, because the uv Python is 64-bit (AMD64). It also has `armv7` and `aarch64` cross-compilers |
| Global CMake and Ninja (for clang) | `C:\Program Files\CMake\bin`; Ninja in its winget package folder | 4.4.4, 1.13.2 | Installed by the user, 2026-11-21, so that the clang build needs no Visual Studio. MSVC builds keep Visual Studio's CMake and Ninja |
| Python | The project's uv environment (`.venv`, `uv run python`) | 3.13.14, 64-bit | The only Python used (user, 2026-11-21) |

**A first test passed.** A small C11 program builds warning-free with both compilers, and gives the same output: MSVC at `/std:c11 /W4 /WX`, clang at `-std=c11 -Wall -Wextra -Wpedantic -Werror`. One quirk: in this environment `cmd` does not run programs from the current folder by name, so scripts must give a path such as `.\prog.exe`.

## 3. Method

The C VM follows the prototype. Each C module is written against its specification document, with the Python module as the working model, and is accepted when the same tests pass:

**Step 2 done (2026-11-21):**
- **Written:** `include/cl_vm.h`; `src/vm.c`, the loader (IMG-11) and the interpreter for all of version 1, ported from `vm.py`; `src/natives.c`, which so far only knows the native numbers; `hal-host/`, the storage part; `test/cvm.c`, the DLL.
- **The harness:** two backends, `cvm-msvc` and `cvm-clang` (`tools/harness/cvm_backend.py`, through `cffi`, which was added with `uv add`).
- **Results:** all 18 runtime tests without natives pass on both, at their first run. The only fixes were in the Python wrapper. A mutant without the `INDEX` bounds check is caught; the C VM's defensive region check turns the out-of-range access into `trap(VM)`.
- **Size:** `sizeof(cl_vm)` is 272 bytes on 64-bit Windows with both compilers; its six pointers take 8 bytes each there.
- **Renamed:** the prototype's `dis.py` is now `disasm.py`, because it shadowed the standard `dis` module, which `cffi` imports.

**Step 3 done (2026-11-21), and with it step 4:**
- **Mbed TLS 3.6.8 LTS** (user's choice over 4.3.0). CMake downloads the release archive once into `vm/c/build/downloads/`, checked against the published SHA-256 `bc54b818…595b`, and builds `mbedcrypto` from it with FetchContent. Its default configuration is used.
- **`src/natives.c`:** a port of `natives.py`, check for check: the argument cells (one signature string per native), the identifier space, the operation table (`CL_OP_SLOTS` = 2) with its lifetimes, and the error precedence. CBOR, BER-TLV and DER are in C, without recursion: `validate` keeps the nesting, at most 16 levels, on an explicit stack. The test-only catalog is compiled in with `CL_TEST_CATALOG`.
- **Descriptors (HAL-11, HAL-12):** RAM and `CONST` views go to the HAL as pointers, persistent views as readers and writers. A writer opens its atomic update at the HAL's first write, which comes only once the call can no longer fail. So an error is never turned into a trap, and the update covers exactly the result, as in the prototype.
- **The host HAL:** keys are kept as raw material, so a transaction's snapshot of the persistent keys is a plain copy. Each key is imported into PSA as a volatile key for one call only. The crypto is PSA (SHA-256, HMAC, deterministic ECDSA, ECDH, AES-CBC), plus `mbedtls_hkdf`, plus the bignum module for the prototype's key generation. The test hooks now include the test catalog's resources (`cl_hal_test.h`).
- **`cl_config`** gains the resource area (`ops`, `ops_size`) of HAL-27. `cl_vm` gains its pointer and the 2-entry operation table: `sizeof(cl_vm)` is now 296 bytes on 64-bit Windows, against 272 before.
- **The host's operation context is 416 bytes,** a PSA hash or MAC operation under Mbed TLS's default configuration. That is more than `cl_hal.h`'s default `CL_HAL_OP_CTX_SIZE` of 256, so the build sets it, and `hal_host.c` checks that it fits. It belongs to the platform's resource area, not to the VM's bookkeeping.
- **Results:**
  - all 32 runtime tests pass on `cvm-msvc` and `cvm-clang`, warning-free, at the first run;
  - so do `check_fido2` (59 checks) and `check_piv` (69 checks);
  - `tools/run_checks.py` now runs these six rows too, after `vm/c/build.py all`.
- **The tests reach the new code.** With the CBOR map-key order check removed, run-021 fails.
- **A gap in the corpus.** A generator mutant (the counter little-endian) passed every test: no scenario checks generated key bytes or random output beyond the first 32-byte block. An ad hoc differential check compared the prototype and both C builds instead: random streams, generated EC, AES and HMAC keys, RFC 6979 signatures, MACs and ciphertexts all came out byte-identical. A runtime test with fixed expected bytes for seeded generation would close the gap on every backend.
- **Known differences from the prototype,** both outside every test:
  - HAL-27's extra internal operation slot is not used; nothing in version 1 needs it;
  - when `finish` writes into a persistent output and that write traps with `TXN-CAPACITY`, the C HAL has already ended the operation, while the prototype keeps it.

**Step 5 done (2026-11-21):** `plans_and_notes/VM7-measurements.md`, produced by `vm/c/measure.py`.
- **Context:** `sizeof(cl_vm)` is 252 bytes on 32-bit targets and 296 on 64-bit, against the prototype's 216. The difference is the entry table, the constant section's size, and the operation table with its area pointer.
- **Code:** 16.2 KB on Cortex-M4 at `-Os`, 19.8 KB on Cortex-M0+.
- **Confirmed:** zero mutable data and bss on every target (V-8); an acyclic call graph with static frames only (VEX-19).
- **Speed:** about 250 million instructions a second on the host, against the prototype's 0.71 million. The benchmark is `vm/c/test/bench.card`, and both VMs execute exactly the same number of instructions.
- **Finding F1:** the VM's C stack, never bounded before, reaches 1,040 bytes on Cortex-M4. Most of it is `cbor_validate`'s 16-level stack (472 bytes) and the inlined `dispatch` (320 bytes). Changes to the C code alone could take it to about 600 bytes. **Fixed:** packed codec levels, and one frame per family of natives, bring it to 856 bytes on Cortex-M4 and 904 on M0+. That is above the 600 estimated: the 16 required levels alone take 256 bytes.
- **Finding F2:** 64-bit integer arithmetic brings in `__aeabi_*` helper calls, which matter most on M0+. That is for VM8.

VM7 makes no bytecode changes (J4, revised): the candidates of `VM5-measurements.md` §10.4 wait for version 2 (VM7b).

1. **Toolchain** (J1): check MSVC, CMake and Ninja from Visual Studio 2026, and clang from llvm-mingw. A first `CMakeLists.txt` builds an empty library with both: MSVC with the Ninja generator, and llvm-mingw with a CMake toolchain file.
2. **Headers and the core:** `cl_vm.h`; the loader with the IMG-11 checks; the interpreter with every instruction of version 1; the storage part of the host HAL. Done when the 18 runtime tests without natives pass on `cvm`.
3. **The native library and the rest of the host HAL:** keys, crypto, and the test catalog (V-33). Done when all 32 runtime tests pass.
4. **The applets:** `check_fido2` and `check_piv` on `cvm`.
5. **Measure,** into `plans_and_notes/VM7-measurements.md`:
   - `sizeof(cl_vm)` on the host, against the prototype's 216 bytes (V-2, VEX-50);
   - the interpreter's code size (`.text` of `vm.c` and `natives.c`) on the host and, if the toolchain can cross-compile, for a 32-bit Cortex-M at `-Os`;
   - the host's speed in instructions per second, for scale only.
6. **Accept and freeze:** with the V-12 criteria met on `cvm`, version 1 is frozen (V-41), and V-42 onward record VM7's decisions.

**Differential testing.** The three backends run the same scenarios. Any difference between the interpreter, the prototype VM and the C VM is a bug in one of them.

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| J1 | The C toolchain. Visual Studio 2022 Community is installed, with MSVC 14.38 and the Windows 10 SDK, but not on the path; there is no other compiler | (a) MSVC, as installed: `cl /std:c11 /W4 /WX`, set up through `vcvars64.bat` by the build script. Nothing to install. Cortex-M sizes wait for VM8; (b) also install LLVM (`winget install LLVM.LLVM`): clang uses the installed MSVC linker and SDK, cross-compiles for Cortex-M, and gives a second compiler for portability; (c) MSYS2 with GCC | (a) now. It needs no change to your machine, and MSVC's C11 mode is enough for this code. Add LLVM in VM8, when Cortex-M sizes are measured. A second compiler is also the cheapest portability check, so (b) is a good alternative if you don't mind the install |
| J2 | The host HAL's crypto backend. The HAL does all cryptography (V-19), and any backend may sit behind it | (a) Mbed TLS (its PSA Crypto API), vendored into a git-ignored folder: a production-grade, constant-time backend, and a real example of PSA behind the HAL; (b) small permissively licensed single-file libraries (for example micro-ecc for P-256, tiny-AES-c, a public-domain SHA-256), vendored; (c) test-only C written by us, matching the Python test crypto | (b) for VM7. It is small, builds with no build system, and is enough for a test HAL. (a) is the better example of a real backend, but brings a CMake build, so it fits VM9 better. (c) means writing and checking P-256 in C ourselves for no lasting value |
| J3 | How the harness drives the C VM | (a) a shared library with a small C interface (load, install, session start and end, select, deselect, command, test hooks), called through `ctypes`; (b) a separate executable speaking a line protocol over standard input and output | (a). It is the most direct, and needs no protocol. (b) is closer to what the VM9 bridge will need, and can be added then |
| J4 | The version-1 candidates (b) to (e) | (a) decide them in the prototype first, measured on both applets, then implement the result in C; (b) implement version 1 as it is in C, and consider them later | (a). Measuring in Python is cheap, and the C VM then implements one instruction set |

## 5. Step 6: acceptance and the freeze (planned 2026-11-21)

**Goal.** Show that the C VM meets V-12, then freeze bytecode version 1 and image format 1 (V-41). Record VM7's decisions as V-42 onward, and bring the specification documents in line with what the C VM taught us. No instruction, encoding or image field changes.

**6.1 Acceptance evidence,** in a new §7 of `VM7-measurements.md`, one row per V-12 item:

| V-12 item | Evidence on `cvm-msvc` and `cvm-clang` |
|---|---|
| Every runtime conformance test passes | `scenario.py`: 32 of 32 on each |
| `check_fido2` passes | 59 checks on each; `check_piv` too, 69 checks |
| Every valid conformance program compiles to an image | `compile_all.py`, for the compiler. New (K1): every image also *loads* in the C VM, with `cl_vm_load` returning `CL_LOAD_OK` |
| The bytecode size, stack and frame figures, and bookkeeping RAM against V-2 | `VM7-measurements.md` §1 to §5 |

**6.2 Close the gaps found in VM7, before freezing:**
- **K2: seeded generation.** No test pins generated keys or random bytes beyond the first 32-byte block of the generator. A new runtime test, `run-033-seeded-generation`, would fix the expected bytes for:
  - `random.fill` across several blocks;
  - the public keys of generated P-256 keys;
  - an RFC 6979 signature made with a generated key;
  - a MAC and a ciphertext under generated HMAC and AES keys.

  It would run on all three backends and the reference interpreter. V-37 is the precedent: tests are added before a freeze.
- **K3: `finish` followed by a trap.** If `finish` writes into a persistent output and that write traps with `TXN-CAPACITY`, the C HAL has already ended the operation, while the prototype keeps it alive. One behaviour must be specified.

**6.3 The specification documents:**
- **`vm/decisions.md`:** V-41's status becomes "frozen", and the VM7 decisions are added:

| ID | Decision |
|---|---|
| V-42 | Version 1 and image format 1 are frozen; any later change is version 2 (VM7b) |
| V-43 | The C toolchains: MSVC and llvm-mingw clang, CMake and Ninja, warnings as errors (J1) |
| V-44 | The host HAL's crypto is Mbed TLS 3.6 LTS through PSA, fetched once and pinned by SHA-256 (J2) |
| V-45 | The harness drives the C VM as a shared library through `cffi` (J3) |
| V-46 | VM7 is a pure port; the candidates wait for VM7b (J4, revised) |
| V-47 | The VM's C stack is VM bookkeeping too: it is measured on every target, and its bound recorded next to `sizeof(cl_vm)` (F1) |
| V-48 | The resource area: `CL_OP_SLOTS` = 2, and no internal slot |
| V-49 | A persistent output's atomic update opens at the HAL's first write |

- **`vm/bytecode.md` and `vm/image-format.md`:** "living" becomes "frozen", and the change log gets its freeze entry. VM7 changed no instruction.
- **`vm/hal.md`:**
  - HAL-12: the writer opens its update at the first write, which comes only once the call can no longer fail;
  - HAL-27: 2 slots, with the internal slot dropped (V-48);
  - HAL-31: the test catalog's resource hooks;
  - HAL-26: K3's answer.
- **`vm/execution-model.md`:**
  - VEX-50: the measured 252 bytes on 32-bit targets replaces the estimate;
  - VEX-2: the measured C stack bound, 856 bytes on Cortex-M4, with the method (V-47);
  - VEX-45 or `cl_config`: the resource area fields.
- **Open items, carried forward:**
  - F2, 64-bit arithmetic, to VM8;
  - the extra internal slot, should a version-2 native ever need one.

**6.4 Close VM7:** the README's status, memory, and the plan's step 6 entry. Optionally a git tag for the freeze (K4).

**Done when:** `run_checks` passes with the new load check and K2's test; the documents say "frozen"; V-42 onward are recorded; and every K decision is answered.

| ID | Question | Options | Recommendation |
|---|---|---|---|
| K1 | Check that the C VM loads every compiled image? | (a) Yes: a `--backend` option for `compile_all.py`, run for `cvm-msvc` and `cvm-clang` in `run_checks`; (b) no, the 32 runtime tests and two applets are enough | (a). It is cheap, and it exercises the loader's IMG-11 checks on all 156 compiled programs, not 34 |
| K2 | Add `run-033-seeded-generation` before the freeze? | (a) Yes, with its bytes taken from the prototype and checked against the reference interpreter; (b) later | (a). It closes the only gap found by mutation, and it binds every future backend to the same generator |
| K3 | After `finish` writes and the write traps, does the operation survive? | (a) No, it has ended: the prototype changes to match the C VM; HAL-26 says `finish` ends the operation once the result is computed, so a failed write loses it; (b) yes: the C HAL clones the PSA hash state and ends the operation only after a successful write, which a MAC operation cannot do; (c) record it as unspecified | (a). It is what a real HAL can do, and a trap already discards the command's work. (b) is impossible for MACs in PSA |
| K4 | Tag the freeze? | (a) `bytecode-v1`, like `spec-draft-0.2`; (b) no tag | (a). It names the exact sources of the frozen version |

**Answered (user, 2026-11-21):**
- **K1 (a):** every compiled image also loads in the C VM;
- **K2 (a):** `run-033-seeded-generation` is added before the freeze;
- **K3 (a):** an operation ends once `finish` has computed its result, and the prototype changes to match;
- **K4 (a):** the freeze is tagged `bytecode-v1`, locally.
