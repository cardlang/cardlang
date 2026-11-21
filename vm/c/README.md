# The CardLang VM in C11

VM7 of the VM plan (`plans_and_notes/vm-plans/VM7-c-vm.md`): the product VM in portable C11, a host HAL, and a shared library through which the test harness drives it. The specification is in `vm/` (execution model, HAL, bytecode version 1, image format 1). The working model is the Python prototype in `tools/vmproto/`.

## Building

From the repository root, with the project's uv environment:

```bash
uv run python -I vm/c/build.py all --clean
```

This builds with both toolchains (J1). Build trees go to `vm/c/build/<toolchain>/`, which git ignores.
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
| 3. `cl_vm.h`, the loader and the interpreter; the storage part of the host HAL | — |
| 4. The native library; the keys and crypto of the host HAL (Mbed TLS) | — |
| 5. The applets: `check_fido2` and `check_piv` on the `cvm` backend | — |
| 6. Measurement | — |
