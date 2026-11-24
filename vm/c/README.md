# The CardLang VM in C11

The product VM in portable C11, a host HAL, and a shared library through which the test harness drives it. The specification is in `vm/` (execution model, HAL, bytecode version 1, image format 1). The Python VM in `src/cardlang/pyvm/` is its working model, and runs the same images.

## Building

With CMake 3.25 or later and any C11 compiler, from the repository root:

```bash
cmake -S vm/c -B vm/c/build
cmake --build vm/c/build
```

- **CMake picks the compiler:** MSVC on Windows with Visual Studio, and gcc or clang on Linux and macOS. The VM builds warning-free on all of them, which CI checks on every push with gcc, clang and MSVC.
- **An optimised build:** generators that build one configuration, such as Ninja and Make, build `Release` by default. Visual Studio's builds `Debug` unless you add `--config Release` to the build command. The tests pass with either.
- **The output:** `cvm.dll`, `cvm.so` or `cvm.dylib`, in `vm/c/build/lib/`, which the harness's `cvm` backend loads. The library must match Python's architecture, which is 64-bit almost everywhere: a compiler that targets 32-bit gives a library the harness cannot load, and it says so.
- **Mbed TLS:** the first configure downloads Mbed TLS 3.6.8, the LTS release archive (5.6 MB), from its GitHub releases into the build tree's `downloads/`, and checks it against the SHA-256 the release publishes. `-DCARDLANG_DOWNLOADS=<folder>` keeps it elsewhere, so that several build trees share one copy.

**A second build tree,** with another compiler, is named at configure time, and chosen with `CARDLANG_CVM_BUILD`:

```bash
cmake -S vm/c -B vm/c/build-clang -DCMAKE_C_COMPILER=clang -DCARDLANG_DOWNLOADS=vm/c/build/downloads
cmake --build vm/c/build-clang
```

Then set `CARDLANG_CVM_BUILD=vm/c/build-clang`, a path from the repository root, and the `cvm` backend and every tool use that build instead. Build trees other than `vm/c/build` are named `vm/c/build-*`, which git ignores.

## Rules

- **C11,** warning-free on every compiler: `/W4 /WX` for MSVC, and `-Wall -Wextra -Wpedantic -Werror` for the others.
- **Memory:** no dynamic allocation, no mutable globals (V-8), and no recursion (VEX-19).
- **Portability:**
  - fixed-width integer types;
  - multi-byte values decoded byte by byte, so the code does not depend on the host's endianness (V-13);
  - every `cl_status` checked.
- **No cryptography in the VM** (HAL-1). The host HAL uses Mbed TLS.

## Status

The VM is complete, and meets V-12: as the backend `cvm`, it passes every runtime test and both example applets' checks, and loads every compiled image. `tests/run_checks.py` runs all of it, and CI runs it with gcc and clang on Linux and MSVC on Windows.

- **The context,** `cl_vm`, is 252 bytes on 32-bit targets and 296 on 64-bit hosts, within V-2's 1 KiB.
- **Its C stack** is at most 856 bytes on Cortex-M4 and 904 on Cortex-M0+.
- **Its code** is 16.3 KB on Cortex-M4.

It has not yet run on a device: these figures come from cross-compiling for the targets.
