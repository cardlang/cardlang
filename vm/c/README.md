# The CardLang VM in C11

VM7 of the VM plan (`devel/plans/vm/VM7-c-vm.md`): the product VM in portable C11, a host HAL, and a shared library through which the test harness drives it. The specification is in `vm/` (execution model, HAL, bytecode version 1, image format 1). The working model is the Python prototype in `src/cardlang/pyvm/`.

## Building

From the repository root, with the project's uv environment:

```bash
uv run python -I vm/c/build.py all --clean
```

This builds with both toolchains (J1). Build trees go to `vm/c/build/<toolchain>/`, which git ignores.

The first configure downloads Mbed TLS 3.6.8 (the LTS release archive, 5.6 MB) from its GitHub releases into `vm/c/build/downloads/`, and checks it against the SHA-256 the release publishes. Both build trees share that one archive.
- **`msvc`:** MSVC from the newest Visual Studio, found with `vswhere`, with Visual Studio's CMake and Ninja.
- **`clang`:** clang from llvm-mingw, targeting 64-bit Windows (`cmake/llvm-mingw-x86_64.cmake`), with the global CMake and Ninja from the `PATH`. It needs no Visual Studio. `build.py` refreshes the `PATH` from the registry, so tools installed after the shell started are found. The folder is `CARDLANG_LLVM_MINGW`, or else the newest `llvm-mingw-*` next to the repository.

## Rules

- **C11,** warning-free on both compilers: `/W4 /WX` and `-Wall -Wextra -Wpedantic -Werror`.
- **Memory:** no dynamic allocation, no mutable globals (V-8), and no recursion (VEX-19).
- **Portability:**
  - fixed-width integer types;
  - multi-byte values decoded byte by byte, so the code does not depend on the host's endianness (V-13);
  - every `cl_status` checked.
- **No cryptography in the VM** (HAL-1). The host HAL uses Mbed TLS (J2).

## Status

| Step | Status |
|---|---|
| 1. Toolchains and the CMake project; the HAL headers compile on both compilers | Done |
| 2. `cl_vm.h`, the loader and the interpreter; the storage part of the host HAL | Done: the 18 runtime tests without natives pass on `cvm-msvc` and `cvm-clang`; `sizeof(cl_vm)` is 272 bytes on 64-bit Windows |
| 3. The native library; the keys and crypto of the host HAL (Mbed TLS) | Done: all 32 runtime tests pass on both backends |
| 4. The applets: `check_fido2` and `check_piv` on the `cvm` backend | Done with step 3: both pass on both backends; `tools/run_checks.py` runs all of it |
| 5. Measurement | Done: `devel/reports/VM7-measurements.md`, by `devel/measure/cvm_measure.py`. `cl_vm` is 252 bytes on 32-bit targets; the C stack is at most 856 bytes on Cortex-M4 (after F1); 16.3 KB of code there |
| 6. Acceptance, and freezing version 1 | Done: V-12 is met on both compilers (`devel/reports/VM7-measurements.md` §7); version 1 is frozen (V-42) and tagged `bytecode-v1` |
