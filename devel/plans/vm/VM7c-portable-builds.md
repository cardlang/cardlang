# VM7c — Portable builds of the C VM, and CI: detailed sub-plan

Planned 2026-11-24, at the user's request. The C VM's build is tied to two toolchains, MSVC through Visual Studio's `vswhere` and `vcvars64.bat`, and llvm-mingw's `x86_64-w64-mingw32-clang`, so it builds only on a Windows machine set up like the user's. This package makes it build with whatever C toolchain CMake finds, on any system, and adds the CI that the repository has never had for its test suite.

## 1. What there is now

- **`vm/c/CMakeLists.txt` is already toolchain-neutral.** It selects warning flags with `if(MSVC)`, and fetches Mbed TLS with `FetchContent`. Plain `cmake` already works: `vm/c/build/` holds a Visual Studio tree from such a run.
- **The coupling is around it:**
  - **`vm/c/build.py`:** `vswhere`, `vcvars64.bat`, `x86_64-w64-mingw32-clang`, Ninja, and build trees in `vm/c/build/msvc` and `vm/c/build/clang`.
  - **`src/cardlang/harness/cvm_backend.py`:** it loads `vm/c/build/<toolchain>/cvm.dll`, a Windows name in a per-toolchain path.
  - **Two backend names, `cvm-msvc` and `cvm-clang`,** used by:
    - `backends.py` and `clc`'s `--backend` choices;
    - four entries of `tests/run_checks.py`, `tests/compile_all.py` and `tests/clc_check.py`;
    - the extension's `cardlang.scenarioBackend` setting;
    - the READMEs of the harness, the package, the extension, the examples and `vm/`;
    - `vm/decisions.md`.
  - **The Mbed TLS archive** is downloaded to `vm/c/build/downloads`, a path fixed in the source tree, whatever the build directory.
- **`devel/measure/cvm_measure.py`** imports `build.py`, and uses llvm-mingw's clang for its 32-bit probe and for the Cortex-M cross builds.
- **No CI runs the test suite.** The two workflows check the extension and build the guide. `run_checks`, with the conformance tests, the examples and the C VM, runs only on the user's laptop.
- **GitHub's runners** come with CMake: `ubuntu-latest` with gcc and clang, and `windows-latest` with MSVC. The harness loads the library with `cffi` in ABI mode, which works with any C compiler's shared library.

## 2. The work

### 2.1 The build: plain CMake

```
cmake -S vm/c -B vm/c/build
cmake --build vm/c/build
```

**This is the whole build,** on any system, with the compiler CMake picks: MSVC on Windows with Visual Studio, and gcc or clang on Linux and macOS.

**`CMakeLists.txt`:**
- **The library lands in one place:** the build directory's `lib/` for every configuration, so a multi-config generator, such as Visual Studio's, does not hide it in `Debug/` or `Release/`.
- **The default configuration** is `Release` where the generator has one: the tests run faster, and the figures are those of an optimised build.
- **The Mbed TLS archive** follows the build directory, not the source tree.
- **Nothing else changes.** The warning rules (`/W4 /WX`, and `-Wall -Wextra -Wpedantic -Werror`) stay.

**`build.py` is deleted (Q4).** The two commands above are the build, in the README and in CI.

### 2.2 One backend, `cvm` (Q1)

- **`cvm` means "the C VM built in `vm/c/build`".** The harness looks for `cvm.dll`, `cvm.so` or `cvm.dylib` in its `lib/` folder.
- **Another build tree,** such as a local clang build, is chosen with an environment variable, `CARDLANG_CVM_BUILD`. For example, after `cmake -S vm/c -B vm/c/build-clang -DCMAKE_C_COMPILER=clang`, set `CARDLANG_CVM_BUILD=vm/c/build-clang`.
- **`cvm-msvc` and `cvm-clang` are gone everywhere:**
  - the backends, `clc`, the tests and `run_checks`;
  - the extension's setting, with its README;
  - every README and `vm/decisions.md`.

  The project is pre-alpha, so there are no aliases.
- **The extension's setting** changes, so its next release carries it. That release is its own step.

### 2.3 `run_checks` without a built C VM (Q3)

- **Locally,** the `cvm` runs are skipped when the library is not built. A clear line says how to build it, and they count as skipped, not passed, in the summary.
- **`--require-cvm`** makes them required, for CI.

### 2.4 CI: a `checks` workflow (Q2)

`.github/workflows/checks.yml` runs on every push and pull request:
- a matrix of `ubuntu-latest` with gcc, `ubuntu-latest` with clang (`CC=clang`), and `windows-latest` with MSVC;
- each runner does `uv sync --locked`, builds the C VM with the two `cmake` commands, and runs `tests/run_checks.py --require-cvm`;
- the Mbed TLS archive is cached between runs, keyed by its version and hash, so a run does not download it again.

The two existing workflows stay as they are.

### 2.5 Documentation

- **`vm/c/README.md`:** building with CMake, any C11 compiler, a second build tree with a named compiler, and `CARDLANG_CVM_BUILD`. No toolchain is named as a requirement.
- **The other READMEs and the guide** say `cvm`. The guide names no backend of the C VM today, so it needs no change, and `guidecheck` confirms it.
- **`vm/decisions.md`:** a decision recording that the C VM builds with any C11 toolchain through plain CMake, and that CI covers several compilers.

### 2.6 The measuring script (Q5)

`devel/measure/cvm_measure.py` takes its host figures from the plain build, and its 32-bit and Cortex-M figures from the cross compiler named by `CARDLANG_CROSS_CC`, a clang that accepts `--target`. Without it, the script measures the host build only, and says so.

## 3. Checks

- **Locally (Windows, MSVC by default):**
  - `cmake -S vm/c -B vm/c/build` and `cmake --build vm/c/build`, from a clean tree, with no `vcvars`, no `build.py` and no environment set up;
  - then `run_checks`, with the `cvm` runs.
- **A second local tree with clang,** named explicitly, run through `CARDLANG_CVM_BUILD`, if the user wants it.
- **CI:** the new workflow passes on every runner of the matrix. The C VM is warning-free with gcc on Linux, a compiler it has not met before; if gcc finds anything, it is fixed in the C code, not silenced.
- **Injection:** a deliberate warning in `vm.c` fails the build; a broken `cvm` library path fails `run_checks` with a clear message.
- **The link check** passes, and no `cvm-msvc` or `cvm-clang` remains outside `devel/` history.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | How tools name the C VM | (a) one backend, `cvm`, for the build in `vm/c/build`, with `CARDLANG_CVM_BUILD` to use another tree; (b) `cvm` plus a `cvm:<dir>` form of `--backend` for other trees; (c) keep a name per compiler, found from the build | (a). The compiler stops being part of the name, and one setting covers every tool, including the extension and the debugger, which run `clc` underneath. (b) puts paths into backend names, which the extension's setting cannot list |
| Q2 | What CI runs | (a) a new `checks` workflow, running all of `run_checks` on a matrix: Linux with gcc, Linux with clang, and Windows with MSVC, on every push and pull request; (b) the same, but only Linux with gcc; (c) build the C VM and run only its own checks, not all of `run_checks` | (a). The whole suite gets run somewhere other than the laptop for the first time, and three compilers stand guard over the C VM's portability. That replaces the second compiler the laptop provided. Public repositories have free Actions minutes |
| Q3 | `run_checks` when the C VM has not been built | (a) locally, skip the `cvm` runs with a clear "build the C VM first" line, and count them as skipped, not passed. In CI, a `--require-cvm` flag makes them required; (b) always fail until it is built; (c) build it automatically | (a). A fresh clone can run every other check at once, and CI cannot pass by skipping. (c) would download Mbed TLS during a test run, which should be a deliberate step |
| Q4 | `vm/c/build.py` | (a) delete it. The two `cmake` commands are the build, in the README and in CI; (b) keep a thin `build.py` that runs those two commands, as a one-line convenience | (a). A script that only repeats two commands hides them, and invites toolchain logic to creep back in |
| Q5 | `devel/measure/cvm_measure.py`, the development tool for the size and stack figures | (a) adapt it: host figures from the plain build, and the 32-bit and Cortex-M figures from a cross compiler named by an environment variable (`CARDLANG_CROSS_CC`, a clang that accepts `--target`); (b) leave it for now, and note that it still assumes llvm-mingw | (a). It stays usable on any machine with a clang. The README's figures stay as they are |

**Decided (user, 2026-11-24):**
- Q1 (a): one backend, `cvm`, with `CARDLANG_CVM_BUILD` for another tree.
- Q2 (a): a `checks` workflow running all of `run_checks` on Linux with gcc, Linux with clang, and Windows with MSVC.
- Q3 (a): skipped locally when the C VM is not built, and required in CI with `--require-cvm`.
- Q4 (a): `build.py` is deleted.
- Q5 (a): the measuring script is adapted, with `CARDLANG_CROSS_CC`.
