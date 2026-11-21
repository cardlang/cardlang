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
