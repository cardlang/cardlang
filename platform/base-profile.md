# CardLang Base Profile 1

Status: draft (2026-11-18). §1–§9 are written (WP2–WP5); §10–§11 are filled in by WP6–WP7. Design decisions: `plans_and_notes/base-api-plan.md` and `plans_and_notes/spec-plans/WP2-profile-skeleton.md`.

This document is a **platform specification**. It is not part of the language specification in `spec/`. It defines the APIs, types and error codes that a platform must provide to claim the Base Profile, and so it answers some of the items that the language leaves to platforms (Annex B §B.12). The rules here are numbered `BP-n`.

## 1. Scope and conformance

**BP-1** A platform conforms to Base Profile 1 when it does all of the following:

- it conforms to the CardLang language specification (PLT-1);
- it provides every entry of `platform/base-catalog.txt`, with the behaviour this document states;
- it supplies the declarations of `platform/base-types.card` exactly as written;
- it uses the `CardError` members and codes of §4;
- it meets the resource minimums of §5.

**BP-2** A conforming platform may add APIs, types, `CardError` members and algorithms. It must not change or remove anything this profile defines. An addition must not use a name or code that this profile defines.

**BP-3** The profile is versioned. This is version 1. A later version may add entries. It changes an existing entry only by publishing a new version.

## 2. Conventions

These conventions hold for every API in the catalog, unless its entry says otherwise.

**BP-4 Paths.** Every API path has the form `card.<family>.<action>`. The families are:

| Family | Contents | Filled in by |
|---|---|---|
| `card.key` | Key creation, import, export and deletion | WP3 |
| `card.crypto` | Digests, MACs, signatures, key agreement, key derivation, ciphers, multi-part operations | WP4 |
| `card.random` | Random bytes | WP4 |
| `card.cbor` | Canonical CBOR reader and writer | WP5 |
| `card.der`, `card.tlv` | DER writer and BER-TLV reader | WP6 |

**BP-5 Argument order.** The arguments come in this order: a resource identifier, if any; configuration values (types from §3); input views (`ref`); output views (`inout`).

**BP-6 Output.** An API that writes output into an `inout` view returns the number of bytes it wrote as its `u32` payload. It writes only the first *n* bytes of the view, where *n* is that payload. If the view is too short for the result, the API returns `Err(CardError.Capacity)`.

**BP-7 Failure changes nothing.** When an API returns `Err`:

- no output view has been changed;
- no resource has been created, changed or deleted;
- no persistent state has been changed.

The application can therefore retry, or handle the error, without cleaning up.

**BP-8 Error precedence.** When more than one error applies, the API returns the first in this order: `NotFound`, `AlreadyExists`, `WrongResourceType`, `InvalidState`, `Unsupported`, `Malformed`, `Capacity`. Each catalog entry lists its errors in this order.

**BP-9 Errors, not traps.** An API never traps because of its arguments' values. Every failure it can detect is an `Err`. Traps still happen where the language requires them: preparing the arguments (FUN-11), and exceeding a runtime capacity (TXN-16, STA-13).

**BP-10 Results, not errors.** A failed verification or comparison is a `bool` result, never an `Err`.

## 3. Types

**BP-11** The platform-supplied types are declared in `platform/base-types.card`. They are ordinary enums and structures with visible declarations (PLT-21), and they follow every naming rule for predeclared names (NAM-14).

| Type | Purpose | Defined by |
|---|---|---|
| `KeyType` | `Aes128`, `Aes256`, `EcP256Private`, `EcP256Public`, `Hmac256`: every valid key type (WP3 K1, WP4) | §7 |
| `KeyStorage` | `Persistent`, `Volatile` | §7 |
| `KeySpec` | A key's type and storage | §7 |
| `DigestAlgorithm` | `Sha256` | §8 |
| `MacAlgorithm` | `HmacSha256` | §8 |
| `SignatureAlgorithm` | `EcdsaP256Sha256` (ES256) | §8 |
| `KdfAlgorithm` | `HkdfSha256` | §8 |
| `CipherAlgorithm` | `AesCbcNoPadding` | §8 |
| `OperationLifetime` | `Command`, `Session` (B5) | §8 |
| `CborMajor` | The eight CBOR major types | §9 |
| `CborHead` | A decoded CBOR head: major type, argument and size | §9 |

Families add their own types in WP3–WP6, for example `Algorithm`, `CborHead` and `TlvHead`.

## 4. `CardError`

**BP-12** The `CardError` set of the profile has exactly these members and codes. The codes are fixed, so host software and tests can rely on them. The categories and their encoding for the host remain as Annex B defines them (PLT-9).

| Member | Code | Raised by |
|---|---|---|
| `Overflow` | `0x0001` | Checked arithmetic (EXP-29) |
| `Underflow` | `0x0002` | Checked arithmetic (EXP-29) |
| `DivisionByZero` | `0x0003` | Checked arithmetic (EXP-29) |
| `ConversionRange` | `0x0004` | `checked_convert` (EXP-33) |
| `NotFound` | `0x0010` | Unknown resource identifier (PLT-22) |
| `AlreadyExists` | `0x0011` | Creating a resource whose identifier is in use (PLT-22) |
| `WrongResourceType` | `0x0012` | A resource of the wrong kind (PLT-22) |
| `InvalidState` | `0x0013` | A multi-part operation used out of order |
| `Capacity` | `0x0014` | Not enough resource capacity, or an output view too short (BP-6) |
| `Unsupported` | `0x0020` | An algorithm, size or value the platform does not provide |
| `Malformed` | `0x0021` | Input that is not well-formed, or not canonical where canonical form is required |

## 5. Resources

**BP-13 Resource kinds.** The profile has two resource kinds, *Key* (WP3) and *Operation* (WP4). Both are named by `u32` identifiers in the application's single identifier space (PLT-20), and both follow PLT-22 and PLT-23.

**BP-14 Lifetimes.**

| Resource | Lifetime |
|---|---|
| Persistent key | Until deleted. It survives power loss and security reset |
| Volatile key | Until deleted, the next power-on, or a security reset |
| Operation with `Command` lifetime | Until finished, or until the end of the command, whether it returns or traps |
| Operation with `Session` lifetime | Until finished, the next power-on, or a security reset |

**BP-15 Transactions.** Creating or deleting a persistent key participates in an active transaction (B4(c)). It commits and rolls back with it. Every other API in the profile is `immediate` unless its entry says otherwise.

**BP-16 Minimum capacities.** A conforming platform can hold at least:

- 8 persistent keys;
- 4 volatile keys;
- 2 operations active at the same time.

Beyond these minimums, running out of capacity is `Err(CardError.Capacity)`.

## 6. The catalog

**BP-17** `platform/base-catalog.txt` lists every API of the profile, in the block format described at the top of that file. Each block gives all the information PLT-25 requires:

- the path, the parameters and the payload;
- the `CardError` members, in the order of BP-8;
- the transaction behaviour;
- the resources it creates, uses or deletes, and the state it leaves on failure;
- any permission it needs.

`tools/checkers/profilecheck.py` checks the catalog against this document.

## 7. Keys (`card.key`)

**BP-18 Key types.** A key is a resource of kind *Key* (BP-13). Its `KeySpec` gives its type and its storage:

| `KeyType` | Material | Can be exported |
|---|---|---|
| `Aes128` | A 16-byte AES key | Nothing |
| `Aes256` | A 32-byte AES key | Nothing |
| `EcP256Private` | A P-256 key pair: the private scalar `d`, and its public point `Q = d·G` | The public point |
| `EcP256Public` | A P-256 public point `Q` only | The public point |
| `Hmac256` | A 32-byte HMAC key | Nothing |

There are no usage restrictions (B4(b)). Any key may be used by any operation that accepts its type (§8). The secret and private material of a key can never be exported (PLT-33).

**BP-19 Identifiers.** Using identifier 0, or any identifier that names no key, is `Err(CardError.NotFound)`. Creating a key with identifier 0 is `Err(CardError.Malformed)`, because 0 never names a resource (PLT-20). Using a resource that is not a key, or a key of a type the API does not accept, is `Err(CardError.WrongResourceType)`.

**BP-20 `card.key.generate(id, spec)`** creates the key `id` with fresh material from the platform's random generator. For `EcP256Private`, it generates a key pair. Generating an `EcP256Public` key is `Err(CardError.Unsupported)`. An identifier already in use is `Err(CardError.AlreadyExists)`, and the existing resource is unchanged (PLT-22).

**BP-21 `card.key.import(id, spec, ref material)`** creates the key `id` from bytes:

| `KeyType` | `material` |
|---|---|
| `Aes128`, `Aes256` | The raw key: exactly 16 or 32 bytes |
| `Hmac256` | The raw key: exactly 32 bytes |
| `EcP256Private` | The private scalar `d`: 32 bytes, big-endian, with `1 ≤ d < n` (the order of the curve). The public point is derived |
| `EcP256Public` | An uncompressed SEC 1 point: 65 bytes, `04 ‖ X ‖ Y`, with `X` and `Y` big-endian. The point must lie on the curve, and must not be the point at infinity |

Material of the wrong length, or with an invalid value, is `Err(CardError.Malformed)`. The platform keeps no reference to `material` after the call.

**BP-22 `card.key.export_public(id, inout output) -> u32`** writes the public point of an `EcP256Private` or `EcP256Public` key, as a 65-byte uncompressed SEC 1 point (BP-21), and returns 65. An AES key is `Err(CardError.WrongResourceType)`. An output view shorter than 65 bytes is `Err(CardError.Capacity)`, and nothing is written (BP-6, BP-7).

**BP-23 `card.key.delete(id)`** deletes the key. Its material is erased, and no copy remains that an application or the host could recover (PLT-33). Afterwards, the identifier names nothing (PLT-22).

**BP-24 Storage and transactions.**

- A `Persistent` key survives commands, traps, power loss and security reset. A `Volatile` key disappears at the next power-on or security reset (BP-14).
- `generate`, `import` and `delete` of a persistent key take part in an active transaction (BP-15):
  - inside the transaction, the change is visible at once (TXN-2);
  - it commits or rolls back with the transaction. After a rollback, a deleted key exists again with the same material, and a created key does not exist;
  - after an interruption, the keys reflect all of the transaction or none of it (TXN-13);
  - each change counts against the platform's transaction capacity. Exceeding it is `trap(TXN-CAPACITY)` (TXN-16).
- The same operations on a volatile key take effect immediately, even inside a transaction (TXN-4).

**BP-25 Capacity.** Creating a key beyond what the platform can hold is `Err(CardError.Capacity)`. A platform holds at least 8 persistent and 4 volatile keys (BP-16).

## 8. Cryptographic operations and randomness (`card.crypto`, `card.random`)

**BP-26 Derived values are application data.** Results that an API writes into an `inout` view are ordinary bytes: digests, MACs, signatures, key-agreement secrets, derived keys and random bytes. Only the material held *inside* a key resource is protected by PLT-33. To use a derived value as a key, the application imports it into a volatile key (BP-21). It erases its own copy with `wipe` (STM-23).

**BP-27 Algorithms.** Each family has its own algorithm enum (§3), so passing an algorithm of the wrong family is a compile-time type error (CE-EXP-1). Version 1 has one algorithm per family:

| Enum value | Algorithm |
|---|---|
| `DigestAlgorithm.Sha256` | SHA-256 (FIPS 180-4) |
| `MacAlgorithm.HmacSha256` | HMAC-SHA-256 (RFC 2104) with an `Hmac256` key |
| `SignatureAlgorithm.EcdsaP256Sha256` | ECDSA over P-256, with SHA-256 of the message (ES256) |
| `KdfAlgorithm.HkdfSha256` | HKDF-SHA-256 (RFC 5869) |
| `CipherAlgorithm.AesCbcNoPadding` | AES in CBC mode, without padding, with an `Aes128` or `Aes256` key |

**BP-28 Keys and their types.** An API that takes a key returns `Err(CardError.NotFound)` when the identifier names no key, and `Err(CardError.WrongResourceType)` when it names another kind of resource, or a key of a type the API does not accept (BP-19).

**BP-29 One-shot operations.**

| API | Accepted key types | Result |
|---|---|---|
| `card.crypto.digest(alg, ref data, inout out) -> u32` | — | The 32-byte digest of `data` |
| `card.crypto.mac(key, alg, ref data, inout out) -> u32` | `Hmac256` | The 32-byte MAC of `data` |
| `card.crypto.sign(key, alg, ref message, inout signature) -> u32` | `EcP256Private` | The 64-byte signature `r ‖ s`, each 32 bytes big-endian. The message is hashed by the API |
| `card.crypto.verify(key, alg, ref message, ref signature) -> bool` | `EcP256Private`, `EcP256Public` | `true` exactly when `signature` is a valid 64-byte signature of `message`. Any other signature, including one of the wrong length, is `false` (BP-10) |
| `card.crypto.agree(key, ref peer, inout secret) -> u32` | `EcP256Private` | ECDH: the 32-byte x-coordinate of `d · peer`. `peer` is a 65-byte uncompressed point that must lie on the curve, otherwise `Err(CardError.Malformed)` |
| `card.crypto.derive(alg, ref secret, ref salt, ref info, length, inout out) -> u32` | — | The first `length` bytes of HKDF output. `length` must be between 1 and 8160, otherwise `Err(CardError.Malformed)`. An empty `salt` means the default salt of RFC 5869 |
| `card.crypto.encrypt(key, alg, ref iv, ref input, inout output) -> u32` | `Aes128`, `Aes256` | The CBC encryption of `input`, the same length as `input` |
| `card.crypto.decrypt(key, alg, ref iv, ref input, inout output) -> u32` | `Aes128`, `Aes256` | The CBC decryption of `input`, the same length as `input` |

- **The cipher inputs.** For `encrypt` and `decrypt`, `iv` must be 16 bytes, and the length of `input` must be a multiple of 16. Anything else is `Err(CardError.Malformed)`.
- **Overlapping views.** `output` may overlap `input`. The result is as if the input were read completely before any output is written.
- **Output size.** A result that does not fit its output view is `Err(CardError.Capacity)`, and nothing is written (BP-6, BP-7).

**BP-30 Signature nonces.** The ECDSA nonce is derived deterministically as in RFC 6979, or drawn from the platform's secure random generator. Which one is platform-defined. Applications and conformance tests must not depend on the exact bytes of a signature, only on its validity.

**BP-31 Multi-part operations.** A multi-part operation is a resource of kind *Operation* (BP-13). It computes a digest, a MAC, a signature or a signature verification over data supplied in pieces:

| API | Purpose |
|---|---|
| `card.crypto.begin_digest(op, alg, lifetime)` | Start a digest |
| `card.crypto.begin_mac(op, key, alg, lifetime)` | Start a MAC with an `Hmac256` key |
| `card.crypto.begin_sign(op, key, alg, lifetime)` | Start a signature with an `EcP256Private` key |
| `card.crypto.begin_verify(op, key, alg, lifetime)` | Start a verification with an `EcP256Private` or `EcP256Public` key |
| `card.crypto.update(op, ref data)` | Add `data` to the operation's input |
| `card.crypto.finish(op, inout out) -> u32` | End a digest, MAC or signature operation, and write its result as the one-shot API would |
| `card.crypto.finish_verify(op, ref signature) -> bool` | End a verification operation, with the result of `verify` |
| `card.crypto.cancel(op)` | End an operation without a result |

- **The result.** The data supplied by `update` calls, concatenated in order, is the input. The result is the same as the one-shot API's on that input.
- **Starting.** `begin_*` creates the operation `op`. An identifier in use is `Err(CardError.AlreadyExists)`, and creating with identifier 0 is `Err(CardError.Malformed)` (as BP-19).
- **Ending.** `finish`, `finish_verify` and `cancel` delete the operation when they succeed. On `Err`, the operation remains as it was (BP-7). For example, after `Err(CardError.Capacity)` from `finish`, the application can call `finish` again with a larger view.
- **States.** Using an identifier that names no operation is `Err(CardError.NotFound)`. The finish that does not match the operation's purpose is `Err(CardError.InvalidState)`. So is any call on an operation whose key has been deleted.
- **Lifetime.** `lifetime` is `Command` or `Session` (BP-14).

**BP-32 Randomness.** `card.random.fill(inout out) -> u32` fills the whole view with bytes from the platform's random generator, and returns its length. The generator is cryptographically secure. Its design and evaluation are platform-defined, at the security level of the target profile (PLT-32).

**BP-33 Transactions.** Every API in this section is `immediate` (BP-15). None of them changes persistent state, and multi-part operations are volatile resources.

## 9. CBOR (`card.cbor`)

**BP-34 A stateless API over views.** Every CBOR API works on the *start* of the view it is given. The application keeps its own position, and moves forward by slicing (FUN-18), for example `card.cbor.head(ref request[at..end])`. No CBOR API keeps state between calls, and none uses a resource.

**BP-35 Heads.** `card.cbor.head(ref data) -> CborHead` decodes the head at `data[0]`:

- `major` is the major type;
- `argument` is the head's argument: the value of an unsigned integer, `n` for the negative integer `−1 − n`, the length in bytes of a byte or text string, the number of items of an array, the number of pairs of a map, the tag number, or the simple value;
- `size` is the number of bytes the head occupies.

A string's content is `data[size .. size + argument]`. An argument above the `u32` range is `Err(CardError.Unsupported)`. A negative integer is representable as `i32` when `argument ≤ 2147483647`.

**BP-36 Canonical form.** CBOR in this profile is canonical. An encoding is well-formed and canonical when all of the following hold. Anything else is `Err(CardError.Malformed)`, except where `Unsupported` is stated:

- **Complete.** Every head and string lies within the data.
- **No indefinite lengths.** The additional-information values 28 to 31 do not occur.
- **Shortest form.** Every argument uses the shortest head: a value below 24 in the initial byte, below 256 in one following byte, below 65536 in two, and below 2^32 in four.
- **Map keys in order.** The keys of every map are in strictly increasing *canonical order*: a shorter encoded key comes first, and keys of equal length are ordered bytewise. This is the order of CTAP2 and RFC 7049 §3.9 (W2). Two equal keys are a duplicate, and are rejected.
- **Valid text.** Every text string is valid UTF-8 (W4).
- **Simple values.** Only `false` (20), `true` (21), `null` (22) and `undefined` (23) are allowed (W3). Floating-point values are `Err(CardError.Unsupported)`.
- **Tags.** A tag is accepted as a head followed by one item (W3).

**BP-37 `card.cbor.validate(ref data) -> u32`** checks that `data` begins with one complete data item that is well-formed and canonical (BP-36), at any depth, and returns that item's encoded length. Bytes after the item are not examined, so an application tells whether there is trailing data by comparing the result with the view's length. A platform validates items nested at least 16 levels deep, counting the outermost item as level 1. Deeper nesting may be `Err(CardError.Unsupported)` (W5).

**BP-38 `card.cbor.skip(ref data) -> u32`** returns the encoded length of the complete item at `data[0]`, including everything nested in it. It checks each head it reads as BP-36 requires, but not the order of map keys and not UTF-8. It has no depth limit. Use `validate` once on a whole message, then `head` and `skip` to walk it.

**BP-39 Writing.**

- **`card.cbor.write_head(major, value, inout out) -> u32`** writes the shortest head for `major` and `value` at `out[0]`, and returns its size. For `Simple`, `value` must be 20 to 23, otherwise `Err(CardError.Malformed)`.
- **`card.cbor.write_int(value: i32, inout out) -> u32`** writes `value` as an unsigned integer if it is at least 0, and otherwise as the negative integer with argument `−1 − value`.
- **Capacity.** A head that does not fit the view is `Err(CardError.Capacity)`, and nothing is written (BP-6, BP-7).
- **The application's part.** The application copies string content with slice assignment (FUN-24), and emits map keys in canonical order. `compare` (EXP-54) and the key lengths decide that order. `validate` on the finished output checks it.

**BP-40 Transactions.** Every CBOR API is `immediate` (BP-15). None of them changes persistent state.

## 10. DER and BER-TLV (`card.der`, `card.tlv`)

To be written in WP6.

## 11. Transport and environment

To be written in WP7: command chaining and long responses, and user presence.

## 12. Answers to the Annex B §B.12 checklist

| Item | Answer in this profile |
|---|---|
| `CardError` member names and codes (EXP-29, OUT-19) | §4 |
| Platform API catalog (NAM-18, PLT-25) | §6 and `platform/base-catalog.txt` |
| Platform-supplied types (NAM-14 item 4) | §3 and `platform/base-types.card` |
| Resource lifetimes at power-on and security reset (PLT-23) | §5, BP-14 |
| Side-channel and fault protection level (PLT-32) | Left to the implementation, which states its level |
| Every other item | Left to the implementation |
