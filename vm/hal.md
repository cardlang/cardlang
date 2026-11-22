# CardLang VM — The HAL interface

Decisions: `vm/decisions.md`. Declarations: `vm/c/include/cl_hal.h` and `cl_hal_test.h`.

The HAL is everything the VM, and the native library that ships with it, asks of a platform. Requirements are numbered `HAL-n` and cite the decisions, the VM requirements (`VEX-n`, `vm/execution-model.md`) and the specification or profile rules they serve (V-9). Where this document and the specification or the Base Profile disagree, they win.

## 1. Principles

**HAL-1 All cryptography is in the HAL.** Every cryptographic computation of the profile is performed by the HAL: hashing, MACs, signatures, verification, key agreement, key derivation, encryption, decryption, key generation, and random generation. Neither the VM core nor the native library computes, or composes from smaller parts, anything cryptographic. Which backend implements the HAL (a software library, the PSA Crypto API, a secure element, an accelerator) is the port's choice.
*Serves: V-19; PLT-30 to PLT-33.*

**HAL-2 What is not cryptography.** These stay in the VM, because they are defined entirely over application data (EXP-52) and need no key, secret parameter or algorithm:
- the intrinsics `equal` and `compare`, including the constant-time obligation of `equal` (PLT-31, VEX-37);
- `wipe` (VEX-38);
- CBOR, BER-TLV and DER encoding and decoding (V-5).

*Serves: V-5, V-19; EXP-52 to EXP-54.*

**HAL-3 The native library's part.** For the key, crypto and random APIs, the native library does only what the catalog defines without cryptography (§5):
- it resolves identifiers in the single identifier space (PLT-20), including the operation table;
- it applies the checks the profile states over lengths and enum values, before calling the HAL;
- it keeps the error precedence of BP-8 across its own checks and the HAL's (HAL-10);
- it maps views onto data descriptors (§3);
- it wraps a persistent output in an atomic update (VEX-28).

*Serves: V-19; BP-6 to BP-8, BP-13, BP-14, PLT-20, PLT-22.*

**HAL-4 Synchronous calls.** Every HAL call returns when it has finished. No HAL call starts a VM entry point or runs application code (VEX-47). The only VM code a HAL call may run is a descriptor's reader or writer (§3), which moves bytes and nothing else.
*Serves: V-21; HEP-13, VEX-47.*

**HAL-5 One context per application.** Every call takes a `cl_hal *` that the platform has bound to one application: its persistent storage partition and its key namespace. Two applications' contexts share no storage and no keys.
*Serves: V-8; PLT-20, PLT-22.*

**HAL-6 Recovery comes first.** Before a HAL context is passed to `cl_vm_load`, the HAL has completed recovery: every interrupted atomic update and transaction, including key changes, is either complete or undone (TXN-13, RTF-10).
*Serves: VEX-43; TXN-13, RTF-10, BP-24.*

## 2. Status

**HAL-7 One status type.** Every HAL function returns a `cl_status`:

| Value | Code | Meaning | What the VM makes of it |
|---|---|---|---|
| `CL_OK` | `0x0000` | Success | — |
| `CL_ERR_*` | the `CardError` code (profile §4) | An error the profile defines | `Err(CardError.m)` (VEX-24) |
| `CL_TXN_CAPACITY` | `0x0100` | An atomic update or a transaction is too large for the platform | `trap(TXN-CAPACITY)` (VEX-29, TXN-16, BP-24) |
| `CL_COMMIT_FAILED` | `0x0101` | A commit failed, and the failure is contained: the transaction is rolled back | `trap(COMMIT)` (TXN-12) |
| `CL_FATAL` | `0x01FF` | An uncontained failure | The entry ends with no result; the platform performs a security reset (RTF-9) |

A function may return only the `CardError` codes this document lists for it.
*Serves: V-3; RTF-4, RTF-9, TXN-12, BP-6 to BP-9.*

**HAL-8 Failure changes nothing.** When a HAL function returns anything other than `CL_OK` or `CL_FATAL`:
- no output has been written;
- no key has been created, changed or deleted;
- no persistent state has changed;
- a multi-part context is as it was before the call.

A function writes an output only once it can no longer fail, other than with `CL_FATAL`.
*Serves: BP-7, BP-31.*

**HAL-9 Errors, not traps.** The HAL never ends execution because of an argument's value. Every failure it can detect is a status.
*Serves: BP-9.*

**HAL-10 Error precedence.** Each HAL function applies the order of BP-8 among the errors it detects. The native library checks the identifier-related errors (`NotFound`, `AlreadyExists`, `WrongResourceType`) and the purely syntactic ones (`Unsupported` for a combination the profile excludes; `Malformed` for a wrong length or an out-of-range argument) *before* calling the HAL. The HAL detects:
- `Malformed` for an invalid value, such as a point not on the curve or a scalar out of range;
- `InvalidState` for an operation whose key is gone;
- `Capacity`, for a full key store or an output too small.

It checks the output size last, so that `Malformed` wins over `Capacity` (BP-8).
*Serves: BP-8.*

## 3. Data descriptors

**HAL-11 Inputs.** Every data input is a `cl_in` descriptor with a length and either:
- a pointer to contiguous bytes; or
- a *reader*: a function that copies `n` bytes starting at a given offset of the input into a buffer the HAL provides.

The native library supplies a pointer whenever the data is in a RAM region or in `CONST`, and a reader only for data in `PERSISTENT`. A HAL that needs an input whole may read it into its own memory. That memory is the HAL's, not the VM's (V-2).
*Serves: V-23; VEX-34, V-15.*

**HAL-12 Outputs.** Every data output is a `cl_out` descriptor with a capacity and either:
- a pointer to contiguous writable bytes; or
- a *writer*: a function that stores `n` bytes at a given offset of the output.

A writer stands for persistent data. The native library opens an atomic update at the writer's first call, over the result's expected length. It closes the update after `CL_OK`, or aborts it after any other status (VEX-28, HAL-8). A HAL writes only once the call can no longer fail, so the update never turns an error into a trap (V-49). Each function reports the number of bytes it wrote.
*Serves: V-23; VEX-28, BP-6, BP-7.*

**HAL-13 Overlap.** An output may overlap an input of the same call. The result is as if every input were read completely before any output is written. With writers this holds by HAL-20: reads do not see an open atomic update.
*Serves: FUN-14, BP-29.*

**HAL-14 No retained references.** After a call returns, the HAL keeps no pointer, reader or writer from its descriptors.
*Serves: BP-21; FUN-16.*

## 4. Persistent storage

**HAL-15 A byte-addressed partition.** Each application has one persistent partition of a fixed size, addressed by byte offset from 0. `cl_hal_storage_size` returns its size. A newly created partition reads as all zero bytes. That is the default of every persistent global (VEX-5), so installation writes nothing.
*Serves: V-7; VEX-5, VEX-9, STA-5.*

**HAL-16 Reading.** `cl_hal_read` copies a range of the partition into a buffer. Inside a transaction it returns the transaction's pending writes (read-your-writes, TXN-4). It takes time that does not depend on the bytes read (PLT-31, for `equal` over persistent data).
*Serves: H1; VEX-26, TXN-4, PLT-31.*

**HAL-17 Atomic updates.** An atomic update changes one destination range all at once:
- **`cl_hal_update_begin`** opens it.
- **`cl_hal_update_write`** stores bytes into it. It may be called any number of times, within the range given at the start.
- **`cl_hal_update_end`** closes it. After an interruption, the destination holds its whole previous value or its whole new value.
- **`cl_hal_update_abort`** discards it.

At most one atomic update is open at a time. A destination larger than `cl_hal_atomic_capacity` is `CL_TXN_CAPACITY` when the update is opened, and nothing is stored.
*Serves: H2; V-15; VEX-28, VEX-29, STA-11, STA-13.*

**HAL-18 Copies.** `cl_hal_copy` copies a range of the partition to another range of it, as one atomic update. The ranges may overlap: the result is as if the whole source were read first.
*Serves: H3; VEX-15, VEX-27.*

**HAL-19 Transactions.**
- **`cl_hal_txn_begin`** starts the single transaction.
- **`cl_hal_txn_commit`** makes all of its atomic updates and key changes durable together.
- **`cl_hal_txn_abort`** discards them.

While a transaction is active, every atomic update and every persistent key change joins it. A transaction that exceeds the platform's capacity is `CL_TXN_CAPACITY` at the change that exceeds it. A commit that fails but is contained is `CL_COMMIT_FAILED`, and the transaction is rolled back. After an interruption, the partition and the persistent keys reflect the whole transaction or none of it (HAL-6).
*Serves: H4, H5; VEX-31, VEX-32, TXN-1 to TXN-16, BP-15, BP-24.*

**HAL-20 An open update is invisible.** Reads, copies and other atomic updates do not see the bytes written into an atomic update that is still open. They see them once it is closed.
*Serves: HAL-13; FUN-14.*

## 5. Keys

**HAL-21 The key store.** The HAL holds every key of an application: its identifier (a `u32`, never 0), its type (`KeyType`), its storage (`KeyStorage`) and its material. Key material, and any state derived from it, never appears in memory that an application region maps, in a descriptor, or in any output except the public point (PLT-33).
*Serves: H7; VEX-35, PLT-33, BP-18, BP-19.*

**HAL-22 Key operations.**

| Function | Profile | HAL-detected errors |
|---|---|---|
| `cl_hal_key_info(id) → type, storage` | BP-19, BP-28 | `NotFound` |
| `cl_hal_key_generate(id, type, storage)` | BP-20 | `Capacity` |
| `cl_hal_key_import(id, type, storage, material)` | BP-21 | `Malformed` (an invalid value), `Capacity` |
| `cl_hal_key_export_public(id, out) → written` | BP-22 | `Capacity` |
| `cl_hal_key_delete(id)` | BP-23 | — |

- **Before each call,** the native library has already checked: identifier 0, an identifier in use by a key or an operation, the key type the API accepts, generating an `EcP256Public` key (`Unsupported`), and the length of `material`.
- **Deleting** erases the material, so that no copy remains (BP-23).
- **Persistent keys** join an active transaction (HAL-19). Volatile and command keys change immediately (BP-24).

*Serves: H7; BP-18 to BP-25, PLT-22.*

**HAL-23 Dropping keys.** `cl_hal_keys_drop(storage)` deletes every key of the application with the given storage. It is called with `Command` when a command ends, and with `Volatile` at a session end, at a session start and at a security reset.
*Serves: H8; VEX-40, VEX-45, VEX-48, BP-14, BP-24.*

**HAL-24 Informative: backends without transactions.** A backend such as the PSA Crypto API creates and destroys keys immediately. A HAL can still meet HAL-19 for persistent keys. For example, it keeps a map from the application's key identifiers to backend key identifiers in its own transactional storage, outside the application's partition. A generate or an import then creates a fresh backend key and writes the map; a delete removes the map entry. After a commit, an abort or a recovery, it destroys every backend key in the application's range that the map does not reference. This is guidance only; the requirement is HAL-19.

## 6. Cryptography

**HAL-25 One-shot operations.** One HAL function per catalog API of BP-29:

| Function | Catalog API | HAL-detected errors |
|---|---|---|
| `cl_hal_digest(alg, data, out)` | `card.crypto.digest` | `Capacity` |
| `cl_hal_mac(key, alg, data, out)` | `card.crypto.mac` | `Capacity` |
| `cl_hal_sign(key, alg, message, out)` | `card.crypto.sign` | `Capacity` |
| `cl_hal_verify(key, alg, message, signature) → valid` | `card.crypto.verify` | — (an invalid signature is `valid = false`, BP-10) |
| `cl_hal_sign_digest(key, alg, digest, out)` | `card.crypto.sign_digest` | `Capacity` |
| `cl_hal_verify_digest(key, alg, digest, signature) → valid` | `card.crypto.verify_digest` | — (as `verify`) |
| `cl_hal_agree(key, peer, out)` | `card.crypto.agree` | `Malformed` (a point not on the curve), `Capacity` |
| `cl_hal_derive(alg, secret, salt, info, length, out)` | `card.crypto.derive` | `Capacity` |
| `cl_hal_cipher(key, alg, direction, iv, input, out)` | `card.crypto.encrypt`, `card.crypto.decrypt` | `Capacity` |

Results and formats are those of BP-29 and BP-30:
- signatures are `r ‖ s`, 64 bytes;
- the agreed secret is a 32-byte x-coordinate;
- the derived output is `length` bytes;
- the cipher output is as long as its input.

The native library checks first: the identifiers, the key types, `length` from 1 to 8160, a 16-byte `iv`, and an `input` length that is a multiple of 16.
*Serves: H9; BP-26 to BP-30.*

**HAL-26 Multi-part operations.** A multi-part operation runs on a *context*, memory the caller provides (HAL-27):

| Function | Catalog API | HAL-detected errors |
|---|---|---|
| `cl_hal_op_begin(ctx, purpose, key, alg)` | `begin_digest`, `begin_mac`, `begin_sign`, `begin_verify` | `Capacity` |
| `cl_hal_op_update(ctx, data)` | `update` | `InvalidState` (its key was deleted) |
| `cl_hal_op_finish(ctx, out)` | `finish` | `InvalidState`, `Capacity` |
| `cl_hal_op_finish_verify(ctx, signature) → valid` | `finish_verify` | `InvalidState` |
| `cl_hal_op_abort(ctx)` | `cancel`, and the end of a lifetime | — |

- **Success:** `finish`, `finish_verify` and `abort` end the operation, and erase the context.
- **`finish` ends the operation once its result is computed,** before the result is written. If writing it then traps, for example with `TXN-CAPACITY` into a persistent output, the operation is gone. `finish` checks the output's capacity first, so `Capacity` leaves the operation as it was (V-50).
- **Failure:** on any error status, the context is unchanged (HAL-8), so `finish` can be repeated with a larger output (BP-31).
- **A deleted key:** an operation whose key has been deleted reports `InvalidState`, even if a new key now has the same identifier. That is why the HAL, not the native library, detects it.
- **The native library** keeps each operation's identifier, purpose and lifetime. It reports `NotFound`, `AlreadyExists`, `Malformed` (identifier 0), and `InvalidState` for a finish of the wrong purpose.

*Serves: H9; BP-31, BP-13, BP-14.*

**HAL-27 Context memory.** `cl_hal.h` defines `CL_HAL_OP_CTX_SIZE` and `CL_HAL_OP_CTX_ALIGN`: the size and the alignment of the largest context. The native library keeps its operation slots in the resource area of `cl_config`, which the platform provides with that alignment. It has `CL_OP_SLOTS` slots: 2, the minimum of BP-16. Version 1 needs no internal slot (V-48). The area belongs to no application region. A HAL whose engine keeps operation state itself may use the context as a handle to it.
*Serves: V-20; VEX-35, BP-16, PLT-33.*

**HAL-28 Randomness.** `cl_hal_random(out)` fills the output with bytes from a cryptographically secure generator (BP-32). It also supplies the randomness for key generation and for signature nonces that are not deterministic (BP-30).
*Serves: H9; BP-30, BP-32.*

**HAL-29 Constant time and confinement.** Every function of §5 and §6 takes time, and performs memory accesses, that do not depend on secret data: key material, the secret inputs of `agree` and `derive`, plaintexts, and the bytes being compared or verified. The level of side-channel and fault protection is the target profile's (PLT-32).
*Serves: PLT-31, PLT-32.*

**HAL-30 Algorithm and type codes.** `cl_hal.h` encodes each profile enum by its ordinal (VEX-4): `cl_key_type`, `cl_key_storage`, and the algorithm enums of §3 of the profile. A HAL that receives an algorithm it does not provide returns `Unsupported`. In Base Profile 1, every conforming HAL provides every algorithm (BP-27).
*Serves: V-13; BP-27.*

## 7. Test hooks

**HAL-31 Test interface.** `cl_hal_test.h` declares the hooks a test HAL provides, so that every backend runs the same scenarios (V-10, V-12):
- **`cl_hal_test_seed(data)`** makes the random generator deterministic from this seed, for every later call (the `seed` step).
- **`cl_hal_test_interrupt_next_commit()`** makes the next commit behave as a power loss during the commit, followed by recovery (the `interrupt` step).
- **`cl_hal_test_resource_create`, `_get`, `_set` and `_delete`** keep the fictional resources of the test-only catalog (`card.test.*`, V-33). These are at most 4, each with a kind and a value, in the same identifier space as keys and operations (VM7).

A production HAL does not provide them.
*Serves: H10; V-10, V-12.*

## 8. Coverage

**The VM's needs** (`vm/execution-model.md` §12):

| Need | Met by |
|---|---|
| H1 Read persistent storage | HAL-16 |
| H2 Atomic updates and the atomic capacity | HAL-17 |
| H3 Overlap-safe persistent copies | HAL-18 |
| H4 Transactions with read-your-writes | HAL-16, HAL-19 |
| H5 Recovery | HAL-6, HAL-19 |
| H6 The partition size | HAL-15 |
| H7 Keys and multi-part operations, persistent keys in transactions | HAL-21, HAL-22, HAL-26, HAL-27 |
| H8 Dropping volatile, session and command resources | HAL-23; operations by the native library (HAL-26) |
| H9 Crypto and randomness, constant time | HAL-25, HAL-26, HAL-28, HAL-29 |
| H10 Test hooks | HAL-31 |
| H11 `CardError` codes | HAL-7 |

**The catalog map** (all 36 APIs):

| Catalog API | Native library (no cryptography) | HAL |
|---|---|---|
| `card.key.generate` | Identifier 0; identifier in use; `EcP256Public` is `Unsupported` | `cl_hal_key_generate` |
| `card.key.import` | Identifier 0; identifier in use; material length per type | `cl_hal_key_import` |
| `card.key.export_public` | Key exists; type is EC | `cl_hal_key_export_public` |
| `card.key.delete` | Key exists | `cl_hal_key_delete` |
| `card.crypto.digest` | — | `cl_hal_digest` |
| `card.crypto.mac` | Key exists and is `Hmac256` | `cl_hal_mac` |
| `card.crypto.sign` | Key exists and is `EcP256Private` | `cl_hal_sign` |
| `card.crypto.verify` | Key exists and is EC | `cl_hal_verify` |
| `card.crypto.sign_digest` | Key exists and is `EcP256Private`; `digest` is 32 bytes | `cl_hal_sign_digest` |
| `card.crypto.verify_digest` | Key exists and is EC; `digest` is 32 bytes | `cl_hal_verify_digest` |
| `card.crypto.agree` | Key exists and is `EcP256Private`; `peer` is 65 bytes | `cl_hal_agree` |
| `card.crypto.derive` | `length` from 1 to 8160 | `cl_hal_derive` |
| `card.crypto.encrypt`, `decrypt` | Key exists and is AES; `iv` is 16 bytes; input length is a multiple of 16 | `cl_hal_cipher` |
| `card.crypto.begin_digest`, `begin_mac`, `begin_sign`, `begin_verify` | Identifier 0; identifier in use; key type; a free slot, otherwise `Capacity` | `cl_hal_op_begin` |
| `card.crypto.update` | Operation exists | `cl_hal_op_update` |
| `card.crypto.finish` | Operation exists; purpose is not verify | `cl_hal_op_finish` |
| `card.crypto.finish_verify` | Operation exists; purpose is verify | `cl_hal_op_finish_verify` |
| `card.crypto.cancel` | Operation exists | `cl_hal_op_abort` |
| `card.random.fill` | — | `cl_hal_random` |
| `card.cbor.validate`, `head`, `skip`, `write_head`, `write_int`, `write_string`, `write_bool` | All of it: encoding, not cryptography (HAL-2) | — |
| `card.tlv.head`, `skip`, `validate` | All of it (HAL-2) | — |
| `card.der.write_head`, `write_integer`, `integer_size` | All of it (HAL-2) | — |

That is 23 APIs that call the HAL, and 13 handled entirely by the native library. A signature of the wrong length passed to `verify` or `finish_verify` is `false` (BP-10). The native library may decide that without calling the HAL, because it is a length check, not a verification.
