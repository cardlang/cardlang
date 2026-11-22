# The CardLang VM in C11

The product VM in portable C11, a host HAL, and a shared library through which the test harness drives it. The specification is in `vm/` (execution model, HAL, bytecode version 1, image format 1). The Python VM in `src/cardlang/pyvm/` is its working model, and runs the same images.

## Building

From the repository root, with the project's uv environment:

```bash
uv run python -I vm/c/build.py all --clean
```

This builds with both toolchains. Build trees go to `vm/c/build/<toolchain>/`, which git ignores.

The first configure downloads Mbed TLS 3.6.8 (the LTS release archive, 5.6 MB) from its GitHub releases into `vm/c/build/downloads/`, and checks it against the SHA-256 the release publishes. Both build trees share that one archive.
- **`msvc`:** MSVC from the newest Visual Studio, found with `vswhere`, with Visual Studio's CMake and Ninja.
- **`clang`:** `x86_64-w64-mingw32-clang`, a clang that targets 64-bit Windows, with CMake and Ninja, all from the `PATH`. [llvm-mingw](https://github.com/mstorsjo/llvm-mingw) provides it: put its `bin` folder on the `PATH`. `CC` names another compiler. It needs no Visual Studio. `build.py` refreshes the `PATH` from the registry, so tools installed after the shell started are found.

## Rules

- **C11,** warning-free on both compilers: `/W4 /WX` and `-Wall -Wextra -Wpedantic -Werror`.
- **Memory:** no dynamic allocation, no mutable globals (V-8), and no recursion (VEX-19).
- **Portability:**
  - fixed-width integer types;
  - multi-byte values decoded byte by byte, so the code does not depend on the host's endianness (V-13);
  - every `cl_status` checked.
- **No cryptography in the VM** (HAL-1). The host HAL uses Mbed TLS.

## Status

The VM is complete, and meets V-12 with both compilers: as the backends `cvm-msvc` and `cvm-clang`, it passes every runtime test and both example applets' checks, and loads every compiled image. `tests/run_checks.py` runs all of it.

- **The context,** `cl_vm`, is 252 bytes on 32-bit targets and 296 on 64-bit hosts, within V-2's 1 KiB.
- **Its C stack** is at most 856 bytes on Cortex-M4 and 904 on Cortex-M0+.
- **Its code** is 16.3 KB on Cortex-M4.

It has not yet run on a device: these figures come from cross-compiling for the targets.
