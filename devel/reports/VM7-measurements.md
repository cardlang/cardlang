# VM7 measurements: the C VM

VM7 step 5, measured 2026-11-21 on top of `08ed0fe`, with `vm/c/measure.py`. It sets the C VM of `vm/c/` against the Python prototype's figures in `VM5-measurements.md`. Reproduce with:

```bash
uv run python -I vm/c/build.py all
uv run python -I vm/c/measure.py > measurements.json
```

## 1. Summary

| Measure | Result | Against |
|---|---|---|
| **VM context, `sizeof(cl_vm)`** | **252 bytes** on 32-bit targets; 296 on 64-bit Windows | The prototype's 216 bytes; V-2's bound of 1 KiB |
| **The VM's C stack, worst case** | **856 bytes** on Cortex-M4, 904 on Cortex-M0+, beneath the HAL's own frames; 1,040 and 1,080 before the F1 fix | Not estimated before. See §3 |
| **Code, Cortex-M4, `-Os`** | 16.3 KB of code and 262 bytes of constants (`vm.c` 9.3 KB, `natives.c` 7.1 KB) | Not a primary concern (the user's goals) |
| **Code, Cortex-M0+, `-Os`** | 20.0 KB of code and 262 bytes of constants | |
| **Mutable data and bss** | **0 bytes** in every build, on every target | V-8: no global state |
| **Recursion, dynamic stack frames** | **None**: the call graph is acyclic, and every frame is static | VEX-19 |
| **Speed on the host** | 253 million instructions a second (MSVC), 229 million (clang) | The prototype's 0.71 million: about 350 times faster |

## 2. The VM's context

`cl_vm` holds every piece of the VM's state (V-31). Its 252 bytes on 32-bit targets are the prototype's 216 plus 36:

| Field | Bytes | Why the prototype did not have it |
|---|---|---|
| `const_size` | 4 | The prototype checked constant reads against the Python `bytes` object |
| `entry[4]` | 8 | The prototype's platform kept the entry indices outside the context |
| `ops`, the resource area's pointer | 4 | The prototype kept operations in a Python dictionary |
| `op[2]`, the operation table: identifier, purpose and lifetime | 16 | The same |
| Alignment padding | 4 | The prototype counted fields without padding |
| **Total** | **36** | |

The 128-byte bounce buffer is still the largest part, at half the context.

On 64-bit Windows the context is 296 bytes, the same with both compilers: its seven pointers take 8 bytes each there.

**Memory outside the context.**
- **The resource area:** the platform provides it (HAL-27), like `SESSION` and `STACK`. It holds `CL_OP_SLOTS` × `CL_HAL_OP_CTX_SIZE` bytes. On the host that is 2 × 416 bytes, because a PSA hash or MAC operation under Mbed TLS's default configuration is 416 bytes on 64-bit. On a card it is whatever the card's HAL needs.
- **`cl_config`:** 32 bytes on 32-bit targets, read only by `cl_vm_load`.

## 3. The C stack

The VM runs on the platform's C stack, below the HAL's own frames. Nothing in the specification bounded it until now. `measure.py` adds clang's `-fstack-usage` frames along the longest call path from each entry point, through the VM's own functions only. This is an upper bound: a tail call is counted as a call.

| Entry point | Cortex-M4 | Cortex-M0+ |
|---|---|---|
| `cl_vm_command` | **1,040** | 1,080 |
| `cl_vm_install`, `cl_vm_session_start`, `cl_vm_select` | 1,024 | 1,064 to 1,072 |
| `cl_vm_load` | 80 | 232 |
| `cl_vm_session_end` | 40 | 40 |

**The deepest path** is `cl_vm_command` → `run` → `cl_native_call` → `cbor_validate` → `cbor_read_head` → `at`. Two frames account for most of it:

| Function | Cortex-M4 frame | Why |
|---|---|---|
| `cbor_validate` | 472 bytes | Its explicit stack of 16 nesting levels (BP-36), 24 bytes each: a 64-bit item count, three positions and three flags |
| `cl_native_call` | 320 bytes | `dispatch` is inlined into it, so the locals of every native share one frame: three input descriptors, an output descriptor, the codec reader with its 32-byte cache, and the 12 argument cells |
| `run` | 144 bytes | The interpreter loop |
| `tlv_validate` | 120 bytes | Its stack of 16 ends |

**Finding (F1).** The VM's bookkeeping is the context plus this stack: about 1.3 KB on Cortex-M4. That is inside the goal of "low single-digit KB", but the stack is four times the context, and most of it is avoidable. These are changes to C code only, with no bytecode change, so they fit VM7's pure port. Two candidates:
- **(a) Smaller codec levels.** A level needs no 64-bit count: once a count exceeds the bytes that remain, every value fails the same way. That is the saturation argument `cbor_skip` already uses. Positions and counts then fit in 16 bytes, so 16 levels take 256 bytes instead of 472.
- **(b) One frame per native family.** Give the families separate functions, not inlined into `cl_native_call`: keys, one-shot crypto, multi-part, codecs, test. Only one family's locals are then live at a time.

The two together should bring the worst path to about 600 bytes.

**F1, fixed (2026-11-21).** Both changes are made, in `natives.c` only:
- a codec level is now 16 bytes: a saturated 30-bit count with the two flags in its top bits, plus three positions;
- `keys`, `one_shot`, `multi_part`, `codecs` and `test_catalog` are separate functions that are never inlined, and so are `cbor_validate` and `tlv_validate`.

| Entry point | Cortex-M4, before | Cortex-M4, after | Cortex-M0+, before | Cortex-M0+, after |
|---|---|---|---|---|
| `cl_vm_command` | 1,040 | **856** | 1,080 | **904** |
| `cl_vm_install`, `cl_vm_session_start`, `cl_vm_select` | 1,024 | 840 | 1,064 to 1,072 | 888 to 896 |

The deepest path is still the CBOR check:

| Frame on that path (Cortex-M4) | Before | After |
|---|---|---|
| `cl_native_call` | 320, with `dispatch` inlined | 96 |
| `codecs` | — | 168 |
| `cbor_validate` | 472 | 344 |

The estimate of 600 bytes was not reached, for two reasons. The 16 levels the profile requires take 256 bytes at 16 bytes each, which is the floor for a check that remembers each map's previous key. And every frame on the path carries its own saved registers and locals.

Code grew by 120 bytes on Cortex-M4 and 154 on Cortex-M0+. All checks still pass on both backends. Two further checks:
- with the map-key order check removed, run-021 still fails;
- a differential fuzz of `cbor.validate`, `cbor.skip`, `tlv.validate` and `tlv.skip` found no difference between the C VM and the prototype in 3,782 inputs. The inputs were nested, truncated and random, with counts up to 2^64−1, and covered `ok`, `Malformed` and `Unsupported` for all four calls.

The HAL's frames come on top, and are the port's. On the host, Mbed TLS's ECDSA dominates them.

## 4. Code size

| Build | `vm.c` code | `natives.c` code | Constants | Data, bss |
|---|---|---|---|---|
| Host, MSVC `/O2`, with the test-only catalog | 22,582 | 17,124 | 451 | 0, 0 |
| Host, clang `-O2`, with the test-only catalog | 13,648 | 19,334 | 1,380 | 0, 0 |
| Cortex-M4, clang `-Os`, without it | 9,254 | 6,966 (7,086 after the F1 fix) | 262 | 0, 0 |
| Cortex-M0+, clang `-Os`, without it | 12,738 | 7,090 (7,244 after the F1 fix) | 262 | 0, 0 |

The cross builds are freestanding. A shim declares the five `<string.h>` functions the VM calls: `memcpy`, `memmove`, `memset`, `memcmp` and `strlen`.

**Finding (F2).** The VM does its integer arithmetic in 64 bits (`norm`, `val` and the range checks, ported from Python), so the compiler emits helper calls:
- `__aeabi_ldivmod` on Cortex-M4, for `DIV` and `MOD`;
- on Cortex-M0+, also `__aeabi_lmul`, `__aeabi_llsl` and `__aeabi_llsr`.

Every value fits 32 bits, so 32-bit arithmetic with explicit overflow checks would avoid them. That makes the code smaller and faster, and matters most on M0+. It is an optimisation for VM8, when the VM meets a real Cortex-M.

## 5. Speed

`vm/c/test/bench.card` is a loop of locals, arithmetic, array reads and writes, and a small copy, with no natives. The budget used therefore equals the instructions executed, and the C VM's count matches the prototype's exactly: 856,306.

| Backend | Time per run | Instructions per second |
|---|---|---|
| Prototype (Python) | 1.21 s | 0.71 million |
| C VM, MSVC | 3.4 ms | 253 million |
| C VM, clang | 3.7 ms | 229 million |

These are for scale only: a desktop CPU, through `cffi`. A smart-card CPU at tens of MHz should be two to three orders of magnitude slower.

## 6. What the measurements confirm

- **No mutable globals** (V-8): every object file of the VM has zero bytes of `.data` and `.bss`, on every target.
- **No recursion, no dynamic frames** (VEX-19): the call graph from every entry point is acyclic, and clang reports every frame as static.
- **Same work** as the prototype: for the benchmark, both the result and the instruction count are identical.
- **Endianness** (V-13): not checked by running, because there is no big-endian target to run on. The code decodes every multi-byte value byte by byte.

## 7. Acceptance (V-12), and the freeze

VM7 step 6, 2026-11-21. The C VM meets every item of V-12 with both compilers. Every figure comes from `tools/run_checks.py`, which passes in full.

| V-12 item | Evidence on `cvm-msvc` | Evidence on `cvm-clang` |
|---|---|---|
| Every runtime conformance test passes | 33 of 33 | 33 of 33 |
| `check_fido2` passes | 59 checks | 59 checks |
| (also) `check_piv` passes | 69 checks | 69 checks |
| Every valid conformance program compiles to an image, and the C VM loads it (K1) | 157 of 157 images load | 157 of 157 |
| The bytecode size, stack and frame figures, and bookkeeping RAM against V-2 | §1 to §5 | §1 to §5 |

**Added before the freeze:**
- **The load check (K1):** `compile_all.py --backend cvm-…` loads every compiled image with `cl_vm_load`, not only the 34 that the tests run.
- **`run-033-seeded-generation` (K2):** it pins the exact bytes of seeded generation:
  - random data over four generator blocks;
  - two generated P-256 public keys;
  - an RFC 6979 signature and a digest signature;
  - an AES-CBC ciphertext and an HMAC under generated keys.

  It passes on all four backends: the reference interpreter, the prototype and both C builds. The generator mutant that every earlier test missed now fails it.
- **`finish` (K3):** the operation ends once the result is computed (V-50). The prototype and the reference interpreter were changed to match the C VM.

**The freeze.** Bytecode version 1 and image format 1 are frozen (V-42). The C VM needed no change to either: every difference found while porting was in the Python harness wrapper or in the HAL's behaviour, never in the instruction set. VM7's decisions are V-42 to V-50. The freeze is tagged `bytecode-v1`.

**Carried forward:**
- **F2,** 64-bit arithmetic and the helper calls it brings in, to VM8;
- **an internal operation slot,** should a version-2 native need one (V-48);
- **the version-2 candidates,** to VM7b.
