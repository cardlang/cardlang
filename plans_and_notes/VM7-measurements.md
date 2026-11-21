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
| **The VM's C stack, worst case** | **1,040 bytes** on Cortex-M4, 1,080 on Cortex-M0+, beneath the HAL's own frames | Not estimated before. See §3: a finding |
| **Code, Cortex-M4, `-Os`** | 16.2 KB of code and 262 bytes of constants (`vm.c` 9.3 KB, `natives.c` 7.0 KB) | Not a primary concern (the user's goals) |
| **Code, Cortex-M0+, `-Os`** | 19.8 KB of code and 262 bytes of constants | |
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

The HAL's frames come on top, and are the port's. On the host, Mbed TLS's ECDSA dominates them.

## 4. Code size

| Build | `vm.c` code | `natives.c` code | Constants | Data, bss |
|---|---|---|---|---|
| Host, MSVC `/O2`, with the test-only catalog | 22,582 | 17,124 | 451 | 0, 0 |
| Host, clang `-O2`, with the test-only catalog | 13,648 | 19,334 | 1,380 | 0, 0 |
| Cortex-M4, clang `-Os`, without it | 9,254 | 6,966 | 262 | 0, 0 |
| Cortex-M0+, clang `-Os`, without it | 12,738 | 7,090 | 262 | 0, 0 |

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
