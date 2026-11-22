# CardLang VM — Execution and memory model

Decisions: `vm/decisions.md`.

This document states how a CardLang program's values, storage, calls, outcomes and failures are represented inside the VM. It does not define instructions or their encoding (`bytecode.md`), the image layout (`image-format.md`), or HAL function signatures (`hal.md`). Requirements are numbered `VEX-n` and cite the decisions and the specification or profile rules they serve (V-9). Where this document and the specification disagree, the specification wins.

## 1. Principles

**VEX-1 Trusted bytecode.** The VM executes an image without verifying it. Every static guarantee of the language (types, definite completion, the call graph, transaction nesting, permissions of references) is established before the image reaches the device. The VM checks only the image header against its configuration (VEX-9) and whatever is cheap, such as an opcode outside the instruction set (VEX-41).
*Serves: V-1; RTF-4 (`VM`), PLT-28.*

**VEX-2 Bounded bookkeeping.** All state the VM itself keeps is in one context structure, `cl_vm`, whose size is a compile-time constant of the VM, independent of the application (VEX-50). The VM allocates no memory, keeps no C globals, and its C stack use is a constant independent of the application. That stack is VM bookkeeping too, and is measured with the context (V-47). The C VM's is at most 856 bytes on Cortex-M4 and 904 on Cortex-M0+, below the HAL's own frames.
*Serves: V-2, V-8.*

**VEX-3 One context, one application.** A context runs one application. Several contexts may coexist; they share nothing that the VM owns.
*Serves: V-8.*

## 2. Values

**VEX-4 Memory layout.** In every region, values are stored packed, unaligned and little-endian:

| Type | Bytes | Encoding |
|---|---:|---|
| `u8`, `i8` | 1 | Two's complement for signed types (TYP-6) |
| `u16`, `i16` | 2 | Little-endian |
| `u32`, `i32` | 4 | Little-endian |
| `bool` | 1 | `false` = 0, `true` = 1 |
| Enum with at most 256 variants | 1 | The variant's ordinal, from 0 in declaration order |
| Enum with more variants | 2 | The ordinal, little-endian |
| `T[N]` | `N × size(T)` | The elements in index order |
| Structure | The sum of its fields | The fields in declaration order, with no padding |

The layout is not visible to programs (TYP-9). It is fixed so that persistent contents and images do not depend on the CPU.
*Serves: V-13; TYP-9, TYP-23.*

**VEX-5 Defaults are zero.** Under VEX-4, `default(T)` is all-zero bytes for every value type (TYP-22). Applying defaults (to persistent state at install, to session state at a session start, to a local declared without an initializer) is a zero fill.
*Serves: V-13; TYP-22, STA-4, STA-5.*

**VEX-6 Operand cells.** The operand stack holds 32-bit cells. A scalar of an integer type, `bool` or enum occupies one cell, zero-extended for unsigned types, `bool` and enums, sign-extended for signed types. Addresses (VEX-11) and view lengths occupy one cell each. Structures and arrays never occupy operand cells; they stay in memory and are moved by block operations.
*Serves: V-4; TYP-6, TYP-7.*

## 3. Regions and addresses

**VEX-7 Regions.** Every byte an application can name lies in exactly one region:

| Tag | Region | Contents | Provided by | Access |
|---:|---|---|---|---|
| 0 | `CONST` | Constant data, array lists, byte strings | The image (read-only) | Direct, through the image pointer (VEX-10) |
| 1 | `PERSISTENT` | Persistent globals | The HAL's storage for this application | HAL calls only (VEX-26) |
| 2 | `SESSION` | Session globals | The platform's configuration | Direct |
| 3 | `STACK` | Frames and operand cells | The platform's configuration | Direct |
| 4 | `REQUEST` | The request of the current command | The platform, for one call | Direct, read-only |
| 5 | `RESPONSE` | The response buffer of the current command or SELECT | The platform, for one call | Direct |

Tags 6 and 7 are reserved. Keys and multi-part operations are HAL resources, not regions (VEX-35).
*Serves: V-7, V-14; HEP-5 to HEP-7, PLT-33.*

**VEX-8 Region sizes.** The image states the sizes of `PERSISTENT`, `SESSION` and the maximum `STACK` need (VEX-17). The platform's configuration (`cl_config`) supplies the `SESSION` and `STACK` areas and their sizes; the HAL supplies the persistent storage.
*Serves: V-2; RTF-7, RTF-8, TYP-23.*

**VEX-9 Load-time checks.** When an image is loaded, the VM rejects it, and runs nothing, if:
- its header names a format version the VM does not implement;
- its `SESSION` size or `STACK` need exceeds the configured area;
- its `PERSISTENT` size exceeds what the HAL provides for the application;
- its largest persistent destination of static size exceeds the HAL's atomic capacity (VEX-29);
- it imports a native the VM does not provide.

This is the load-time rejection of RTF-8, STA-13 and TYP-23. It never changes the meaning of a program that loads.
*Serves: V-1, V-12; RTF-8, STA-13, TYP-23.*

**VEX-10 The image is memory-mapped.** The VM reads the image, code and `CONST` data alike, through a read-only pointer that stays valid while the context exists. Whether the image is in flash or RAM is the platform's choice.
*Serves: V-17.*

**VEX-11 Addresses.** An address is one 32-bit cell: the region tag (VEX-7) in bits 31 to 29, and a byte offset within the region in bits 28 to 0. Instructions whose region the compiler knows statically (globals, locals, constants) name their region in the instruction and do not decode a tag. Tags are decoded only when an address comes from a reference or a view.
*Serves: V-14.*

## 4. References and views

**VEX-12 References.** A `ref` or `inout` parameter of a value type is one address cell (VEX-11) pointing to the referenced place. The place's type, and so its size and layout, is known statically. A reference into `CONST` is only ever read: the language never allows writing through it.
*Serves: V-14; FUN-6 to FUN-12, FUN-16.*

**VEX-13 Views.** A view (`T[]`) is two cells: the address of its first element, and its length in elements. The element size is known statically. A slice `v[s..e]` of a view, after the bounds checks of FUN-20, is the view (address + `s × size(T)`, `e − s`). A slice of a fixed array is formed in the same way from the array's address and its static length.
*Serves: V-14; FUN-18 to FUN-21, TYP-21.*

**VEX-14 Lifetime.** References and views are held in frames, as parameters and temporaries, and end with the call they were passed to (FUN-16). They are application stack, not VM bookkeeping.
*Serves: V-2; FUN-16.*

**VEX-15 Aliasing.** Every block copy between places that may overlap behaves as if the source were read completely before the destination is written (as `memmove`). Copies within `PERSISTENT` are done by the HAL with the same guarantee (VEX-27).
*Serves: FUN-13, FUN-14, FUN-24.*

**VEX-16 Bounds.** Every index into, slice of, and element reference through a view or a fixed array whose index is not a constant is checked before any access. A failure is `trap(BOUNDS)`, before anything is read or written.
*Serves: EXP-37, EXP-39, STM-9, FUN-11, FUN-20, FUN-24.*

## 5. The stack and calls

**VEX-17 One stack.** The `STACK` region holds every frame of the running command or handler, in call order. The compiler computes each function's frame size and the maximum stack need over the static call graph (FUN-5); the image records the maximum (VEX-8). The VM performs no stack overflow checks.
*Serves: V-1, V-4; FUN-5, RTF-7.*

**VEX-18 Frames.** A frame consists of:
1. return information: the caller's resume address and frame position;
2. the parameters: one cell per scalar or reference, two per view, the bytes of each by-value aggregate;
3. the locals and compiler temporaries, including payload slots (VEX-21);
4. the operand area, of the function's maximum operand depth.

Parts 1 to 3 have sizes known statically; their layout is the compiler's and is recorded in the image.
*Serves: V-4; FUN-17, RTF-7.*

**VEX-19 Calls do not recurse in C.** A call pushes a frame and continues the same interpreter loop at the callee. A return pops the frame and resumes the caller. No CardLang call is a C call, so the C stack depth is independent of the call depth.
*Serves: V-2.*

**VEX-20 Arguments.** Arguments are evaluated and prepared left to right (EXP-50, FUN-11). Scalars, references and views are passed as cells. A by-value aggregate is copied into the callee's parameter area; the copy is independent of its source (FUN-17).
*Serves: EXP-50, FUN-11, FUN-17.*

**VEX-21 Payloads.** A scalar `Ok` payload is returned in one operand cell. For an aggregate payload, the caller reserves a slot in its own frame and passes its address; the callee writes the payload there before returning `Ok`. On `Err` the slot is not written.
*Serves: FUN-17, OUT-1 to OUT-5.*

**VEX-22 Frame erasure.** When a frame ends, by return, `Err`, `abort` or a trap, every byte of it is set to zero before anything else runs. After a trap, the whole used part of the stack is zeroed (VEX-40).
*Serves: PLT-35, PLT-34.*

## 6. Outcomes

**VEX-23 The outcome register.** The context holds one outcome register: `Ok`, or `Err` with a category (application or platform) and a 16-bit code. The application code is the member's code (OUT-16); the platform code is the `CardError` code (profile §4). A call sets the register when it returns; `attempt`, `require`, `match` on an outcome, `ignore` and forwarding returns read it.
*Serves: OUT-1 to OUT-22.*

**VEX-24 Natives report through the same register.** A native that fails sets the register to a platform error with its `CardError` code, and writes nothing (BP-7). An intrinsic that returns `Err` (the `checked_*` operations) sets it in the same way.
*Serves: BP-6, BP-7, EXP-52.*

**VEX-25 The result of an entry.** Each entry point (VEX-45) ends with exactly one result for the platform: `Ok` with a byte count, an application error with its code, a platform error with its code, a trap with its kind, or none (VEX-43). For a command, `Ok(count)` with `count` larger than the response capacity is `trap(RESPONSE-COUNT)` (HEP-9). The binding adapter turns the result into a status word or a raw envelope (BP-51, BP-53); the VM core never encodes a binding.
*Serves: V-6; HEP-9 to HEP-12, RTF-11, BP-51, BP-53.*

## 7. Persistent storage, atomicity and transactions

**VEX-26 Through the HAL only.** Every read and write of `PERSISTENT` is a HAL call. The VM keeps no copy or cache of persistent bytes, so a read always sees the latest write, including writes pending in a transaction (TXN-4).
*Serves: V-7; TXN-4.*

**VEX-27 Persistent copies.** A copy whose source and destination are both in `PERSISTENT` is one HAL operation, which handles overlap (VEX-15).
*Serves: FUN-14, FUN-24.*

**VEX-28 Atomic updates.** Every write to `PERSISTENT`, of any size, is made inside a HAL *atomic update*: the VM opens one, writes the destination's bytes in one or more chunks, and closes it. After an interruption and recovery, the destination holds either its whole previous value or its whole new value. A scalar write is an atomic update of one chunk. The VM never stages a destination in RAM. This covers assignments to globals, fields and elements, whole aggregates, `fill`, slice assignments, `wipe`, writes through `inout` references and views, and natives writing into persistent views (VEX-34).
*Serves: V-15; STA-11, STA-12, FUN-23, FUN-24, STM-23.*

**VEX-29 Atomic capacity.** The HAL states the largest destination it can update atomically. A destination of static size above it is rejected at load (VEX-9). A destination whose size is known only at runtime and is above it is `trap(TXN-CAPACITY)`, raised before anything is written.
*Serves: STA-13, RTF-4.*

**VEX-30 Right-hand side first.** The value assigned to a persistent destination is fully evaluated, and every check that can fail (bounds, arithmetic) is done, before the atomic update opens. A failure leaves the destination unchanged (STA-12).
*Serves: STA-12, STM-10.*

**VEX-31 Transactions.** The context has one transaction flag. A `transaction` block begins a HAL transaction; leaving it normally commits; `abort`, and the error paths of `attempt` and `require` inside it (TXN-18), abort it. Atomic updates inside a transaction join it. The HAL keeps pending writes and provides read-your-writes. A commit the HAL reports as failed but contained is `trap(COMMIT)` (TXN-12).
*Serves: TXN-1 to TXN-18.*

**VEX-32 Key changes in transactions.** Creating and deleting a persistent key joins an active transaction (BP-15). This is the HAL's: the HAL knows its own transaction state, so the call carries nothing extra (HAL-19, HAL-22).
*Serves: BP-15.*

## 8. Natives and application data

**VEX-33 Calling a native.** A catalog API is called by its index in the image's native import table. Its arguments are cells, as for a function call. Its result is the outcome register (VEX-24) and, on success, a scalar payload cell.
*Serves: V-5; PLT-30.*

**VEX-34 Data access through helpers.** A native never receives a raw pointer to application data. It reads and writes views and references through VM helpers that copy a chunk to or from the application's place, whatever its region. For `RESPONSE`, `REQUEST`, `SESSION`, `STACK` and `CONST`, a helper may hand the native a direct pointer to the region's bytes. For `PERSISTENT`:
- a HAL call receives a reader or a writer descriptor (HAL-11, HAL-12);
- the native library's own code, and the intrinsics, pass data through a bounce buffer of 128 bytes in the context.

A native's writes into a persistent view form one atomic update (VEX-28).
*Serves: V-16, V-22, V-23, V-2; FUN-23, BP-7.*

**VEX-35 Resources.** Keys and multi-part operations are identified by number.
- **Keys,** including their material (PLT-33), are held by the HAL (HAL-21).
- **Operations:** the native library keeps the table of identifiers, purposes and lifetimes. Their HAL contexts are slots in the resource area of `cl_config`, which no application region maps (HAL-27).

Neither is VM bookkeeping. Both are sized by the profile's minimum capacities (BP-16).
*Serves: V-2, V-20; PLT-33, BP-14, BP-16.*

**VEX-36 The bounce buffer is wiped.** After every native call, and after every intrinsic that used it, the bounce buffer is set to zero.
*Serves: PLT-34, PLT-35.*

**VEX-37 Intrinsics.** Intrinsics (EXP-52) are executed by the VM, not by the HAL. Those over aggregates (`fill`, `equal`, `compare`, `encode_*`, `decode_*`) read and write places through the same access paths as other instructions. `equal` takes time independent of the compared contents and of where they differ (PLT-31); when a side is persistent, it reads through the bounce buffer in fixed-size chunks.
`equal` and `compare` are comparisons of application data, not cryptography; all cryptography is in the HAL (HAL-1, HAL-2).
*Serves: EXP-52 to EXP-54, PLT-31.*

**VEX-38 `wipe`.** A `wipe` performs every one of its stores, in every region, including in a frame about to end. Nothing in the VM removes or defers them.
*Serves: STM-23, PLT-34.*

## 9. Traps

**VEX-39 Traps leave the loop.** A trap ends interpretation: the interpreter loop returns the trap kind (RTF-4). No `setjmp` or `longjmp` is used, and natives report traps by their return value.
*Serves: V-2; RTF-1.*

**VEX-40 Cleanup after a trap,** in this order:
1. abort an open atomic update, so its destination keeps its previous value;
2. abort the active transaction, if any (TXN-11);
3. zero the used part of the stack (PLT-35) and the bounce buffer;
4. end command-lifetime keys and operations (BP-14);
5. return the trap kind as the entry's result (VEX-25).

Session state, persistent writes outside a transaction, and other resources are left as they are (RTF-2).
*Serves: RTF-1, RTF-2, TXN-11, PLT-35, BP-14.*

**VEX-41 Safety-net checks.** With trusted images (V-1), the VM raises `trap(VM)` only for checks that cost almost nothing, such as an opcode outside the instruction set. `NESTED-TXN` and the stack case of `EXHAUSTED` are never checked: accepted programs cannot reach them.
*Serves: V-1; RTF-4, PLT-28.*

**VEX-42 The execution budget.** Each entry starts with the configured budget in a counter. Every instruction decrements it by one; natives and intrinsics over aggregates also charge a fixed cost per call and a cost per byte, defined in `bytecode.md`. When the counter would go below zero, the result is `trap(EXHAUSTED)`. The same program, state and request always exhaust the budget at the same point (RTF-5).
*Serves: V-18; RTF-5, RTF-6.*

**VEX-43 Interruption.** A power loss or a security reset may end an entry with no result. On the next start, the HAL's recovery completes or undoes any interrupted atomic update and transaction before the VM runs again (TXN-13, RTF-10). The VM context itself is volatile and is set up again by `cl_vm_load`.
*Serves: TXN-13, RTF-9, RTF-10.*

## 10. Lifecycle and the platform API

**VEX-44 Lifecycle state.** The context records which of these states the application is in: not installed, installed with no session, in a session, unavailable for the rest of the session (BP-55), and, for the ISO 7816 binding, whether it is selected. This is part of `cl_vm` (VEX-50).
*Serves: STA-4 to STA-10, BP-55, BP-56.*

**VEX-45 Entry points.** The VM is a library; the platform's main loop calls it (V-6). The signatures are in `vm/c/include/cl_vm.h`:

| Entry | What the VM does |
|---|---|
| `cl_vm_load(vm, config, image, size, hal)` | Sets up the context; runs the load-time checks (VEX-9, IMG-11). The configuration supplies the `SESSION` and `STACK` areas, the budget, the binding, whether test natives are allowed, and the resource area (HAL-27) |
| `cl_vm_install(vm)` | The new partition already reads as zero, which is every default (HAL-15, VEX-5); runs `on_install` if declared. If it traps or returns `Err`, installation fails and the result says so (BP-55) |
| `cl_vm_session_start(vm)` | Ends any open session; zero-fills `SESSION`; tells the HAL to drop volatile keys and session operations; runs `on_session_start` if declared. If it traps or returns `Err`, the application is unavailable until the next session start (BP-55) |
| `cl_vm_session_end(vm)` | Zero-fills `SESSION`; tells the HAL to drop volatile keys and session operations (STA-4, BP-14) |
| `cl_vm_security_reset(vm)` | As a session end, for every context (RTF-9) |
| `cl_vm_select(vm, resp, cap)` | ISO 7816 only: runs `on_select` with `RESPONSE` mapped to `resp` (BP-50a) |
| `cl_vm_command(vm, req, len, resp, cap)` | Maps `REQUEST` and `RESPONSE`; runs the command; returns its result (VEX-25). An unavailable application gets a trap result without running (BP-55) |

*Serves: V-6; HEP-1 to HEP-14, STA-4, STA-6, BP-50a, BP-55, BP-56.*

**VEX-46 Request and response stay the platform's.** `REQUEST` and `RESPONSE` are mapped onto the platform's buffers for one entry and unmapped when it ends. The VM copies neither. The response bytes are meaningful only for an `Ok` result (HEP-8, HEP-9).
*Serves: V-2; HEP-5 to HEP-9.*

**VEX-47 Commands do not interleave.** A context runs at most one entry at a time, and the VM never calls the platform back into another entry. A platform with several contexts runs one entry at a time across all of them (HEP-13).
*Serves: HEP-13, TXN-14.*

**VEX-48 Command-lifetime resources.** When a command ends, whatever its result, the VM tells the HAL to drop command-lifetime keys and operations (BP-14).
*Serves: BP-14.*

## 11. The VM context

**VEX-49 What the context holds.** `cl_vm` holds only:
- the image pointer and the header fields used while running;
- the bases and sizes of `SESSION`, `STACK`, `REQUEST` and `RESPONSE`;
- the program counter, the current frame position and the operand position;
- the outcome register (VEX-23);
- the transaction flag, the atomic-update state and the lifecycle state (VEX-44);
- the budget counter (VEX-42);
- a pointer to the HAL context;
- the bounce buffer (VEX-34).

*Serves: V-2.*

**VEX-50 The bound.** `sizeof(cl_vm)` is at most 1 KiB on every target. Measured for the C VM: 252 bytes on 32-bit targets, of which 128 are the bounce buffer (V-22), and 296 on 64-bit hosts. The Python VM's context is 216 bytes.
*Serves: V-2, V-12.*

## 12. What the HAL must provide

`vm/hal.md` §8 shows which `HAL-n` requirement meets each need.

| # | Requirement | From |
|---|---|---|
| H1 | Read a range of the application's persistent storage | VEX-26 |
| H2 | Atomic updates: open, write chunks, close, abort; the atomic capacity | VEX-28, VEX-29, VEX-40 |
| H3 | Copy a range within persistent storage, overlap-safe, as one atomic update | VEX-27 |
| H4 | Transactions: begin, commit (with a contained-failure result), abort; read-your-writes | VEX-31 |
| H5 | Recovery of interrupted atomic updates and transactions before the VM runs again | VEX-43 |
| H6 | The size of the application's persistent storage | VEX-9 |
| H7 | Keys and multi-part operations as numbered resources, with transaction participation for persistent keys | VEX-32, VEX-35 |
| H8 | Dropping volatile, session and command-lifetime resources on request | VEX-45, VEX-48 |
| H9 | Crypto and randomness as in profile §8, constant-time where PLT-31 requires | VEX-33 |
| H10 | Test hooks: a seedable deterministic random generator, and power-loss injection at the next commit | V-10 |
| H11 | `CardError` codes for every failure (profile §4) | VEX-24 |

## Annex: paper check against the runtime tests and the FIDO2 applet

Every construct the 26 runtime tests and `examples/fido2` use, and where this model covers it:

| Construct | Covered by |
|---|---|
| Integer arithmetic, `checked_*`, `wrapping_*`, `convert`, `truncate` | VEX-6; intrinsics VEX-37; traps VEX-39 |
| `encode_be`, `decode_be`, `fill`, `equal`, `compare` | VEX-37 |
| Locals, structures, arrays, byte strings, array lists | VEX-4, VEX-7 (`CONST`), VEX-18 |
| Indexing and slices of arrays and views | VEX-13, VEX-16 |
| `ref` and `inout` parameters, including into persistent storage | VEX-12, VEX-28 |
| Slice assignment, including persistent and overlapping | VEX-15, VEX-27, VEX-28 |
| Function calls and aggregate payloads | VEX-17 to VEX-21 |
| `attempt`, `attempt … else`, `require`, `match` on outcomes, `Err(Set(code))`, `ignore` | VEX-23 |
| `if`, `while`, `for`, `break`, `continue`, compound assignment | Instructions; no state beyond the frame |
| Persistent and session globals | VEX-7, VEX-26, VEX-5 |
| `transaction`, `abort`, traps inside transactions, interrupted commits | VEX-31, VEX-40, VEX-43 |
| `wipe` | VEX-38 |
| Platform APIs (218 call sites: keys, crypto, CBOR, TLV, DER, random) | VEX-33 to VEX-35 |
| Command-lifetime keys ending on a trap | VEX-40, VEX-48 |
| `on_install`, `on_session_start`, `on_select`, session start and end, security reset | VEX-44, VEX-45 |
| Response count above capacity | VEX-25 |
| The execution budget | VEX-42 |

No construct needs state outside the frames, the regions and the context of VEX-49.
