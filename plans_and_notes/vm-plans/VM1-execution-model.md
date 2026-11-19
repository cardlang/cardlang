# VM1 — Execution and memory model: detailed sub-plan

Parent: `plans_and_notes/vm-plan-of-plans.md`. Decisions so far: `vm/decisions.md` (V-1 to V-12).
Status: decisions B1 to B6 taken 2026-11-19, all as recommended (option (a)). They become V-13 to V-18 in the register. **Drafted 2026-11-19:** `vm/execution-model.md`, with VEX-1 to VEX-50, the HAL requirements H1 to H11 (§12), and the paper check (annex).

## 1. Scope

VM1 writes `vm/execution-model.md`: how a CardLang program's values, storage, calls, outcomes and failures look *inside* the VM, independent of how instructions are encoded.

- **VM1 decides:** value representation, memory regions and addresses, references and views, the stack, calls, outcomes, persistent access, how natives reach application data, traps and cleanup, the execution budget, the platform-facing API (`cl_vm.h`, in outline), and the VM context with its RAM bound.
- **VM1 does not decide:** opcodes and their encoding, the image layout (both VM3), or the HAL's function signatures (VM2). Where VM1 needs something from the HAL, it states the requirement and VM2 designs the call.

## 2. What the model must serve

From Draft 0.2 and Base Profile 1:

- **Values:** integers up to 32 bits, `bool`, enums, structures and fixed arrays (TYP-1 to TYP-23); defaults (TYP-22).
- **References and views:** `ref`, `inout`, `T[]`, slices, aliasing preserved (FUN-11 to FUN-21, FUN-13, FUN-14), slice assignment (FUN-24), by-value copies (FUN-17).
- **Persistent writes:** atomic per destination, including through references (STA-11, STA-12, FUN-23), the atomic capacity (STA-13).
- **Transactions:** read-your-writes, at most one, abort, traps roll back, commit failure (TXN-1 to TXN-18).
- **Outcomes:** `Ok` with any payload, `Err` with an application or platform error (chapter 9); the host categories (HEP-9 to HEP-12, RTF-11).
- **Traps:** their kinds and effects (RTF-1 to RTF-5), the budget (RTF-6), stack bounds (RTF-7, RTF-8).
- **Security:** constant-time `equal` (PLT-31), `wipe` (PLT-34), frames erased on exit (PLT-35), no key material in application memory (PLT-33).
- **Lifecycle and sessions:** `on_install`, `on_session_start`, `on_select`, session start and end, security reset (STA-4 to STA-10, BP-50a, BP-56).
- **Command-lifetime resources** end with the command (BP-14).

## 3. Proposed model

### 3.1 Values in memory (B1)

- **Packed, unaligned, little-endian.** `u8`, `i8` and `bool` take 1 byte, `u16` and `i16` 2, `u32` and `i32` 4. An enum takes 1 byte (2 if it has more than 256 variants). Structures are their fields in declaration order with no padding; arrays are their elements in order.
- **Defaults are all-zero bytes.** With this encoding, `false` is 0 and an enum's first variant is ordinal 0, so every `default(T)` (TYP-22) is zero bytes. Installing persistent state, starting a session, and declaring a local without an initializer are each a zero fill.
- **On the operand stack** every scalar is one 32-bit cell, zero- or sign-extended from its type. Aggregates are never on the operand stack.

Packing saves RAM, and the C VM reads and writes multi-byte values a byte at a time (or with `memcpy`), so alignment buys nothing portable. A fixed byte order makes persistent contents and images independent of the CPU.

### 3.2 Regions and addresses (B2)

Every byte an application can name lies in one of these regions:

| Region | Contents | Owner, size | Access |
|---|---|---|---|
| `CONST` | Constant data | The image, read-only | Direct (the image is memory-mapped, B5) |
| `PERSISTENT` | Persistent globals | The HAL; size from the image | HAL calls only (V-7) |
| `SESSION` | Session globals | The platform's configuration; size from the image | Direct |
| `STACK` | Frames and operand cells | The platform's configuration; need from the image | Direct |
| `REQUEST` | The request bytes | The platform, for one command | Direct, read-only |
| `RESPONSE` | The response buffer | The platform, for one command or SELECT | Direct |

- **An address is one 32-bit cell:** a 3-bit region tag and a 29-bit byte offset.
- **The compiler knows the region of every global and local,** so most accesses use region-specific instructions (VM3) and never inspect a tag. Tags matter only for references and views, whose region is known only at runtime.
- **Sizes are checked once, at load** (RTF-8): the image states what it needs; the platform's configuration and the HAL state what they have.

### 3.3 References and views

- **A reference** (`ref` or `inout` to a scalar or aggregate) is one address cell. The element type, and so the size, is known statically.
- **A view** (`T[]`) is two cells: an address and a length in elements. A slice of a view computes a new address and length after the bounds check (FUN-20).
- **References and views live in frames,** as parameters and temporaries (FUN-16), so they are application stack, not VM bookkeeping.
- **Aliasing** (FUN-13, FUN-14): copies between possibly overlapping places use move semantics (as `memmove`). A copy within `PERSISTENT` is done by the HAL, which handles overlap.

### 3.4 The stack

- **One `STACK` region holds every frame.** A frame has a fixed part (return information, parameters, locals, temporaries; its size is known statically) and an operand area (its maximum depth is known statically).
- **The maximum stack need** is the deepest path through the static call graph, computed by the compiler (RTF-7) and checked at load. The VM performs no stack overflow checks (V-1).
- **Return information** (the return address and the caller's frame) is stored in the callee's frame. It is application stack, not bookkeeping, so call depth never grows the VM context.
- **Erasure** (PLT-35): when a frame ends, its bytes are zeroed. After a trap, the whole used part of the stack is zeroed.

### 3.5 Calls and payloads

- **Arguments** are prepared left to right (FUN-11). Scalars and references go through operand cells; a by-value aggregate is copied into the callee's frame (FUN-17).
- **Payloads:** a scalar `Ok` payload is returned in an operand cell. An aggregate payload is written into a slot that the caller reserves in its own frame and passes to the callee. No aggregate is ever copied through the VM.
- **No C recursion:** a call pushes a frame and jumps. The interpreter loop is one C function whose own stack use is constant.

### 3.6 Outcomes

- **The outcome register** in the VM context holds `Ok` or `Err`, and for `Err` a category (application or platform) and a 16-bit code: the member's code (OUT-16) or the `CardError` code (profile §4).
- **`attempt`, `match` and forwarding** compile to tests of that register. An `Err` never carries a payload, so the register is all an error needs.
- **The command's outcome** goes to the binding adapter: `Ok(count)` with the response bytes, an error with its category and code, or a trap with its kind (HEP-9, RTF-11). The adapter turns it into a status word or a raw envelope (BP-51, BP-53).

### 3.7 Persistent access, atomicity and transactions (B3)

- **Reads and writes go through the HAL** (V-7). The VM never caches persistent bytes.
- **Atomicity per destination** (STA-11): every persistent write, of any size, is one *atomic update* in the HAL. For a large destination (a whole structure, a slice assignment, a native writing into a persistent view), the VM opens an atomic update, writes the bytes in chunks, and closes it. The HAL guarantees that after an interruption the destination holds the old or the new value.
  - The VM never stages a whole destination in RAM, so no RAM buffer grows with the size of persistent data.
  - Inside a transaction, the writes simply join the transaction.
  - A destination larger than the HAL's atomic capacity: rejected at load when its size is static; `trap(TXN-CAPACITY)` with nothing stored when it is known only at runtime (STA-13).
- **Transactions:** the VM keeps one flag. `transaction` calls the HAL's begin; normal exit calls commit; `abort` and every trap inside the block call abort (TXN-11). Read-your-writes and journaling are the HAL's. A commit the HAL cannot complete is `trap(COMMIT)` (TXN-12).

### 3.8 Natives and application data (B4)

A native (a catalog API, V-5) receives scalars, references and views. A view may lie in any region, including `PERSISTENT`, which has no pointer.

- **Proposal:** natives never receive raw pointers. They read and write views through VM helpers (read a chunk, write a chunk) that hide the region. A small bounce buffer in the VM context (for example 64 bytes) moves persistent data in chunks; RAM regions are passed through directly.
- **Writes into a persistent view** by a native are one atomic update (§3.7, FUN-23).
- **After each native call** the bounce buffer is zeroed, because it may have held secret data (PLT-34, PLT-35).
- **Multi-part operations** (hash or cipher contexts) and keys are HAL resources, identified by number. Their RAM is the HAL's and is sized by the profile's minimum capacities (BP-14), not by the VM.

### 3.9 Traps and cleanup

- **A trap** is a return code out of the interpreter loop, never a `longjmp`.
- **Cleanup**, in this order: abort the active transaction or atomic update, if any (TXN-11); zero the used stack (PLT-35); end command-lifetime keys and operations (BP-14); report the trap kind to the binding adapter (RTF-1, RTF-2).
- **Session state survives a trap** (RTF-2), and nothing else is reset.
- **Safety-net traps** (`VM`, `NESTED-TXN`, the stack case of `EXHAUSTED`): with trusted bytecode (V-1), the VM checks only what is cheap, such as an opcode out of range.

### 3.10 The execution budget (B6)

Every instruction decrements a counter set from the configured budget at the start of each command or handler. Natives charge a cost per call plus a cost per byte. When the counter runs out, the result is `trap(EXHAUSTED)` (RTF-6). Counting instructions makes the trap deterministic (RTF-5), which a timer would not.

### 3.11 The platform-facing API (V-6), in outline

```c
cl_status cl_vm_load(cl_vm *vm, const cl_config *cfg, const uint8_t *image, size_t size);
cl_outcome cl_vm_install(cl_vm *vm);
cl_outcome cl_vm_session_start(cl_vm *vm);
void       cl_vm_session_end(cl_vm *vm);
void       cl_vm_security_reset(cl_vm *vm);
cl_outcome cl_vm_select(cl_vm *vm, uint8_t *resp, size_t cap);
cl_outcome cl_vm_command(cl_vm *vm, const uint8_t *req, size_t len, uint8_t *resp, size_t cap);
```

The request and response buffers stay the platform's (HEP-7): the VM maps them as `REQUEST` and `RESPONSE` for the call, and copies nothing. `cl_config` names the `SESSION` and `STACK` areas and their sizes, and the budget.

### 3.12 The VM context and its RAM bound (V-2)

`cl_vm` is one struct with no pointers to VM-owned dynamic memory. Its expected contents:

| Field | Bytes (32-bit target) |
|---|---:|
| Image pointer and the header fields used at run time | about 16 |
| Region bases and sizes (`SESSION`, `STACK`, `REQUEST`, `RESPONSE`) | about 32 |
| Program counter, frame pointer, operand pointer | 12 |
| Outcome register | 4 |
| Transaction and atomic-update state, lifecycle state | 4 |
| Budget counter | 4 |
| HAL context pointer | 4 |
| Bounce buffer (B4) | 64 |
| **Total, estimated** | **about 140** |

That is far below the 1 KiB bound. VM5 measures what the prototype actually needs; VM8 measures the C VM.

## 4. Work

1. Write `vm/execution-model.md` as `VEX-n` requirements, each citing V-n and the spec or profile rules it serves (V-9), following §3 and the decisions below.
2. Add the decisions B1 to B6 to `vm/decisions.md` as V-13 onward, and any question still open to its open-questions list.
3. Collect the requirements on the HAL in one section ("what VM2 must provide"): atomic updates, transactions, overlap-safe persistent copies, resources, the test hooks from VM0.
4. Check the model against every runtime test and the FIDO2 applet on paper: each construct they use has a representation and a defined cleanup.
5. Update `vm/README.md` and the plan of plans.

## 5. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| B1 | Value layout in memory | (a) packed, unaligned, little-endian, with all-zero defaults; (b) natural alignment and the CPU's byte order | (a). Least RAM, CPU-independent persistent data, and zero fills for every default |
| B2 | Addresses | (a) one 32-bit cell: a 3-bit region tag and a 29-bit offset; region-specific instructions where the compiler knows the region; (b) separate descriptors (region, offset, length) for every reference | (a). One cell per reference, two per view |
| B3 | Atomic persistent writes | (a) a HAL *atomic update*: the VM writes a destination in chunks inside it; (b) the VM stages the whole new value in RAM, then makes one HAL write | (a). No RAM buffer that grows with persistent data; a journaling HAL needs this mechanism for transactions anyway |
| B4 | How natives reach application data | (a) through VM chunk helpers and a small bounce buffer, so persistent views work without RAM copies; (b) natives get raw pointers, and persistent views are first copied into RAM scratch | (a). Bounded RAM; (b) needs scratch as large as the largest persistent view |
| B5 | How the VM reads the image | (a) memory-mapped and read-only (flash or RAM), through a pointer; (b) through HAL calls, with a small fetch cache | (a). Simplest and fastest; (b) only for targets that cannot map flash |
| B6 | The execution budget | (a) an instruction counter, with natives charging per call and per byte; (b) a time limit from the HAL | (a). Deterministic (RTF-5) and portable |
