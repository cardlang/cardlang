# VM2 — The HAL interface: detailed sub-plan

Parent: `plans_and_notes/vm-plan-of-plans.md`. Inputs: `vm/execution-model.md` §12 (H1 to H11), Base Profile 1 §4 and §7 to §8, `vm/decisions.md` (V-1 to V-18).

Status: decisions taken 2026-11-19.
- **C1, from the user:** all cryptography happens in the HAL. The VM and its native library do nothing that could be treated as cryptography. A port may implement the HAL over any backend, for example the PSA Crypto API.
- **C2, C4 and C5:** as recommended.
- **C6:** the proposal of §2.4, confirmed when the user asked to draft VM2.

**Drafted 2026-11-19:**
- `vm/hal.md` (HAL-1 to HAL-31, with the catalog map);
- `vm/c/include/cl_hal.h` and `cl_hal_test.h`;
- V-19 to V-23;
- VEX-32, VEX-34, VEX-35, VEX-37, VEX-45 and VEX-50 amended.

No C compiler was available, so compiling the headers waits for VM7.

## 1. Scope

VM2 writes `vm/hal.md` (requirements `HAL-n`) and a draft `vm/c/include/cl_hal.h`: everything the VM, and the native library that ships with it (V-5), may ask of a platform.

- **In the HAL:**
  - persistent storage, with atomic updates, transactions and recovery;
  - the key store, including key changes joining transactions;
  - every cryptographic operation of the profile, and randomness;
  - the test hooks.
- **Not in the HAL:**
  - transport and I/O (V-6);
  - CBOR, TLV and DER (V-5), which are encodings, not cryptography;
  - installing and authenticating images: the platform's loader does this, before `cl_vm_load` (V-1);
  - time and scheduling.

## 2. Design

### 2.1 Division of work (C1)

| Layer | Does | Never does |
|---|---|---|
| **HAL** | Storage and transactions. Keys: generate, import, export the public part, delete, and type queries. Digest, MAC, sign and verify, each one-shot and multi-part. Key agreement. Key derivation (HKDF). Encryption and decryption (AES-CBC). Randomness. Constant-time behaviour (PLT-31). Keeping key material out of application memory (PLT-33) | Interpret CardLang values, or know the catalog's argument rules |
| **Native library** (portable C, in the VM) | The catalog's non-cryptographic semantics: argument and output-size checks, the fixed error precedence (BP-6, BP-7), the table of operation identifiers with `AlreadyExists`, `InvalidState` and lifetimes (BP-14), mapping CardLang views onto HAL data descriptors (§2.4), and atomic updates when an output is persistent (VEX-28) | Any cryptographic computation or composition. For example, it never hashes before signing and never builds HKDF from HMAC |
| **VM core** | VEX-1 to VEX-50 | Ditto |

**The HAL's crypto interface follows the catalog,** so the native library is a thin layer of checks:

| Catalog family | HAL operations |
|---|---|
| `card.key.*` (4) | generate, import, export public, delete, query type and storage |
| One-shot crypto (7) | digest, mac, sign, verify, agree, derive, encrypt and decrypt |
| Multi-part crypto (8) | setup per purpose (digest, mac, sign, verify), update, finish, finish-verify, abort, on caller-provided contexts (§2.2) |
| `card.random.fill` | fill |

**Keys and transactions** (BP-15, BP-24) are the HAL's. Creating or deleting a persistent key inside a transaction commits and rolls back with the transaction's storage changes, recovery included.
- A HAL over a backend without transactions, such as PSA, can meet this itself. For example, it can keep a map from CardLang key IDs to backend key IDs in its transactional storage, and destroy unmapped backend keys after an abort or a recovery.
- `hal.md` records this as informative guidance, not a requirement.

### 2.2 Contexts in a configured area (C2)

- **Sizes:** the HAL publishes the size of each multi-part context as a compile-time constant, for example `CL_HAL_DIGEST_CTX_SIZE`.
- **Slots:** the native library keeps the operation slots in a *resource area* supplied by `cl_config`:
  - at least 2 slots (BP-16), each as large as the largest context;
  - one more slot, used when a one-shot operation's input must be streamed (§2.4).
- **Visibility:** the area is not an application region, so applications can't read it. Its contents are opaque to the VM.
- **What counts as what:**
  - the resource area is configured platform RAM, not VM bookkeeping (V-2);
  - the key store is entirely the HAL's.

### 2.3 Calls and errors (C5)

- **Synchronous calls.** Every HAL call returns when it has finished. The budget counts instructions, not time (V-18).
- **No re-entry.** No HAL call ever re-enters a VM entry point (VEX-47).
- **One status type.** Every call returns `cl_status`:

| Value | Meaning |
|---|---|
| `CL_OK` | Success |
| A `CardError` code (profile §4) | Passed to the application as `Err` |
| `CL_ATOMIC_CAPACITY` | The destination is too large to update atomically. It becomes `trap(TXN-CAPACITY)` (VEX-29) |
| `CL_COMMIT_FAILED` | The commit failed, but the failure is contained. It becomes `trap(COMMIT)` (TXN-12) |
| `CL_FATAL` | An uncontained failure. The VM stops with no result, and the platform performs a security reset (RTF-9) |

### 2.4 Passing data to the HAL (C6, proposal)

**The problem.** An operand may lie in any region, including `PERSISTENT`, which has no pointer (V-7). The VM must not stage large values in RAM (V-15). Some operations can't be streamed by the caller: HKDF takes its secret, salt and info whole.

**The proposal.** Every HAL data argument is a *descriptor*:
- an input is either a contiguous pointer and length, or a *reader*: a VM-supplied function that copies a range of the operand into a buffer the HAL provides;
- an output is either a contiguous pointer and capacity, or a *writer*, which the VM turns into chunks of one atomic update (VEX-28).

**How the parties use it.**
- **The native library** passes a pointer whenever the operand is in a RAM region or `CONST`, which is the common case: the FIDO2 applet keeps its crypto operands in locals. It passes a reader or a writer only for persistent operands.
- **A HAL** that needs an input whole can read it into its own buffer. That buffer is the HAL's own RAM, the same kind a backend such as PSA needs anyway.
- **Readers and writers** only move bytes. They never run application code, so this is not re-entry.

**The 128-byte bounce buffer (C4)** then serves writers and intrinsics such as `equal` over persistent data. Fixed-size inputs no longer need it.

### 2.5 Binding to an application

- `cl_vm_load` receives a HAL context pointer that is already bound to one application: its storage partition and its key namespace.
- Separating applications is the platform's job (V-8).

### 2.6 Deliverables

1. **`vm/hal.md`:**
   - the `HAL-n` requirements by group;
   - the status mapping;
   - the constant-time and key-confinement obligations;
   - the data descriptors;
   - the informative guidance on backends without transactions.
2. **The catalog map:** for each of the 34 APIs, either its native-library checks and HAL operation, or "native library, non-cryptographic" for CBOR, TLV and DER. It checks that nothing is missing, and that nothing cryptographic is left outside the HAL.
3. **`vm/c/include/cl_hal.h` and `cl_hal_test.h`:** C11 declarations, with comments that point to the `HAL-n` requirements. They are compiled with `-std=c11 -Wall -Wextra -pedantic`, if a C compiler is available.
4. **Register updates:**
   - C1, C2, C4, C5 and C6 become V-19 to V-23;
   - V-16 is amended (128 bytes; the bounce buffer no longer carries crypto inputs);
   - VEX-34, VEX-37 and VEX-50 are updated to match.

**Not in VM2:**
- the Python HAL for the prototype (VM5);
- the C host HAL and its crypto backend (VM7). An established library behind the HAL, such as Mbed TLS with PSA, is the natural choice there.

## 3. Work

1. Write `vm/hal.md` and the catalog map.
2. Write the two headers, and check that they compile.
3. Check coverage. Each of H1 to H11, and every VEX requirement that names the HAL, must be met by a `HAL-n` requirement.
4. Check the VM documents for crypto. Nothing in `vm/execution-model.md` or the native-library description may compute or compose cryptography. VEX-37 (`equal`) is a constant-time comparison of application data, not cryptography; `hal.md` says so explicitly.
5. Update `vm/decisions.md`, `vm/README.md`, `vm/execution-model.md` and the plan of plans.

## 4. Decisions

| ID | Question | Decision |
|---|---|---|
| C1 | How much the HAL does | All cryptography is in the HAL, at the level of the catalog's operations. The VM and the native library do nothing cryptographic. The backend behind the HAL (PSA or any other) is the port's choice (user, 2026-11-19) |
| C2 | Memory for operation contexts | The HAL publishes context sizes. The native library keeps the slots in a resource area from `cl_config` (as recommended) |
| C3 | — | Storage with transactions in the HAL was already decided (V-3, V-7, V-15) |
| C4 | Bounce buffer | 128 bytes (as recommended) |
| C5 | Synchronous or asynchronous | Synchronous (as recommended) |
| C6 | Passing data to the HAL | Descriptors that are either a pointer or a reader or writer (§2.4) |
