# CardLang Base Profile 1

Status: Base Profile 1, released with CardLang Draft 0.2 (2026-11-19). All sections are written (WP2–WP7, with later additions such as command keys, `write_string` and `write_bool`, the raw envelope and session events). Design decisions: `devel/plans/spec/base-api-plan.md` and `devel/plans/spec/WP2-profile-skeleton.md`.

This document is a **platform specification**. It is not part of the language specification in `language/spec/`. It defines the APIs, types and error codes that a platform must provide to claim the Base Profile, and so it answers some of the items that the language leaves to platforms (Annex B §B.12). The rules here are numbered `BP-n`.

## 1. Scope and conformance

**BP-1** A platform conforms to Base Profile 1 when it does all of the following:

- it conforms to the CardLang language specification (PLT-1);
- it provides every entry of `platform/base-catalog.txt`, with the behaviour this document states;
- it supplies the declarations of `platform/base-types.card` exactly as written;
- it uses the `CardError` members and codes of §4;
- it meets the resource minimums of §5;
- it claims at least one transport binding of §11, and meets its rules.

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
| `KeyStorage` | `Persistent`, `Volatile`, `Command` | §7 |
| `KeySpec` | A key's type and storage | §7 |
| `DigestAlgorithm` | `Sha256` | §8 |
| `MacAlgorithm` | `HmacSha256` | §8 |
| `SignatureAlgorithm` | `EcdsaP256Sha256` (ES256) | §8 |
| `KdfAlgorithm` | `HkdfSha256` | §8 |
| `CipherAlgorithm` | `AesCbcNoPadding` | §8 |
| `OperationLifetime` | `Command`, `Session` (B5) | §8 |
| `CborMajor` | The eight CBOR major types | §9 |
| `CborHead` | A decoded CBOR head: major type, argument and size | §9 |
| `TlvClass` | The four BER tag classes | §10 |
| `TlvHead` | A decoded BER-TLV head: tag, class, constructed, length and size | §10 |

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
| Volatile key | Until deleted, or the end of the session (STA-4) |
| Command key | Until deleted, or the end of the command that created it, whether it returns, returns `Err` or traps |
| Operation with `Command` lifetime | Until finished, or until the end of the command, whether it returns or traps |
| Operation with `Session` lifetime | Until finished, or the end of the session (STA-4) |

**BP-15 Transactions.** Creating or deleting a persistent key participates in an active transaction (B4(c)). It commits and rolls back with it. Every other API in the profile is `immediate` unless its entry says otherwise.

**BP-16 Minimum capacities.** A conforming platform can hold at least:

- 8 persistent keys;
- 4 volatile keys, counting command keys;
- 2 operations active at the same time.

Beyond these minimums, running out of capacity is `Err(CardError.Capacity)`.

## 6. The catalog

**BP-17** `platform/base-catalog.txt` lists every API of the profile, in the block format described at the top of that file. Each block gives all the information PLT-25 requires:

- the path, the parameters and the payload;
- the `CardError` members, in the order of BP-8;
- the transaction behaviour;
- the resources it creates, uses or deletes, and the state it leaves on failure;
- any permission it needs.

`tests/profilecheck.py` checks the catalog against this document.

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

- A `Persistent` key survives commands, traps, power loss and security reset. A `Volatile` key disappears at the end of the session (STA-4). A `Command` key disappears when the command that created it ends, however it ends (BP-14). Use it for a key needed only while one command runs, such as a derived credential key: no cleanup code is needed, and a trap cannot leave it behind.
- `generate`, `import` and `delete` of a persistent key take part in an active transaction (BP-15):
  - inside the transaction, the change is visible at once (TXN-2);
  - it commits or rolls back with the transaction. After a rollback, a deleted key exists again with the same material, and a created key does not exist;
  - after an interruption, the keys reflect all of the transaction or none of it (TXN-13);
  - each change counts against the platform's transaction capacity. Exceeding it is `trap(TXN-CAPACITY)` (TXN-16).
- The same operations on a volatile or command key take effect immediately, even inside a transaction (TXN-4).

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
| `card.crypto.sign_digest(key, alg, ref digest, inout signature) -> u32` | `EcP256Private` | As `sign`, but `digest` is the hash itself and is not hashed again. It must be 32 bytes for `EcdsaP256Sha256`, otherwise `Err(CardError.Malformed)`. Added for PIV, which hashes off-card (WP12) |
| `card.crypto.verify_digest(key, alg, ref digest, ref signature) -> bool` | `EcP256Private`, `EcP256Public` | As `verify`, over a given digest. A `digest` that is not 32 bytes is `Err(CardError.Malformed)`; a bad signature is `false` (BP-10) |
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
- **Map keys in order.** The keys of every map are in strictly increasing *bytewise* order of their encodings. This is RFC 8949's core deterministic order (§4.2.1), and, for every key type CTAP2 uses, CTAP2's canonical order (W2 as revised by R1, WP8 step 0). Two equal keys are a duplicate, and are rejected.
- **Valid text.** Every text string is valid UTF-8 (W4).
- **Simple values.** Only `false` (20), `true` (21), `null` (22) and `undefined` (23) are allowed (W3). Floating-point values are `Err(CardError.Unsupported)`.
- **Tags.** A tag is accepted as a head followed by one item (W3).

**BP-37 `card.cbor.validate(ref data) -> u32`** checks that `data` begins with one complete data item that is well-formed and canonical (BP-36), at any depth, and returns that item's encoded length. Bytes after the item are not examined, so an application tells whether there is trailing data by comparing the result with the view's length. A platform validates items nested at least 16 levels deep, counting the outermost item as level 1. Deeper nesting may be `Err(CardError.Unsupported)` (W5).

**BP-38 `card.cbor.skip(ref data) -> u32`** returns the encoded length of the complete item at `data[0]`, including everything nested in it. It checks each head it reads as BP-36 requires, but not the order of map keys and not UTF-8. It has no depth limit. Use `validate` once on a whole message, then `head` and `skip` to walk it.

**BP-39 Writing.**

- **`card.cbor.write_head(major, value, inout out) -> u32`** writes the shortest head for `major` and `value` at `out[0]`, and returns its size. For `Simple`, `value` must be 20 to 23, otherwise `Err(CardError.Malformed)`.
- **`card.cbor.write_string(major, ref content, inout out) -> u32`** writes a complete byte string (`major` = `Bytes`) or text string (`Text`): the shortest head for `content.length`, followed by `content`. It returns the total size. Any other `major` is `Err(CardError.Malformed)`, and so is a `Text` whose content is not valid UTF-8 (BP-36).
- **`card.cbor.write_bool(value: bool, inout out) -> u32`** writes `true` (`0xF5`) or `false` (`0xF4`), and returns 1.
- **`card.cbor.write_int(value: i32, inout out) -> u32`** writes `value` as an unsigned integer if it is at least 0, and otherwise as the negative integer with argument `−1 − value`.
- **Capacity.** A head that does not fit the view is `Err(CardError.Capacity)`, and nothing is written (BP-6, BP-7).
- **The application's part.** The application copies string content with slice assignment (FUN-24), and emits map keys in canonical order. `compare` (EXP-54) on two encoded keys decides that order. `validate` on the finished output checks it.

**BP-40 Transactions.** Every CBOR API is `immediate` (BP-15). None of them changes persistent state.

## 10. DER and BER-TLV (`card.der`, `card.tlv`)

**BP-41 Pattern.** The TLV APIs follow BP-34. Each works on the start of the view it is given, keeps no state, and uses no resource. The reader accepts BER-TLV as ISO/IEC 7816-4 defines it, with definite lengths only, so it also reads DER. The writer always produces DER.

**BP-42 `card.tlv.head(ref data) -> TlvHead`** decodes the tag and length at `data[0]`:

- `tag` is the tag's raw bytes, packed big-endian into a `u32`, for example `0x30`, `0x7F49` or `0x9F38` (T1). The first byte gives `class` (bits 8 and 7) and `constructed` (bit 6). When the first byte's tag-number bits are all ones, the tag continues with subsequent bytes, each with bit 8 set except the last;
- `length` is the content length, in the short form (`00`–`7F`) or a long form (`81`–`84`, followed by 1 to 4 bytes). Non-minimal forms are accepted (T2);
- `size` is the number of bytes the tag and length occupy. A primitive object's content is `data[size .. size + length]`. A constructed object's content is a sequence of objects.

These are `Err(CardError.Malformed)`:
- the indefinite length `80`, or the length byte `FF`;
- a tag or length that is incomplete;
- content that extends beyond `data`.

A tag longer than 4 bytes, or a length longer than 4 bytes (`85`–`FE`), is `Err(CardError.Unsupported)`. Padding bytes (`00` or `FF`) between objects are not skipped. An application whose protocol uses them skips them itself.

**BP-43 `card.tlv.skip(ref data) -> u32`** returns `size + length` of the object at `data[0]`, with the checks of BP-42.

**BP-44 `card.tlv.validate(ref data) -> u32`** checks the object at `data[0]` as BP-42 requires, and returns its encoded length. If the object is constructed, it checks its content too: the content must be a sequence of valid objects that exactly fills it, recursively. A platform validates at least 16 levels of nesting, counting the outermost object as level 1. Deeper nesting may be `Err(CardError.Unsupported)` (T3).

**BP-45 The DER writer.**

- **`card.der.write_head(tag, length, inout out) -> u32`** writes `tag`'s bytes, without leading zero bytes, followed by `length` in its minimal DER form, and returns the size written. A `tag` that is 0, or whose bytes are not a valid BER tag (BP-42), is `Err(CardError.Malformed)`.
- **`card.der.write_integer(ref magnitude, inout out) -> u32`** writes a complete DER INTEGER, `02`, its length and its content, for the unsigned big-endian number `magnitude`:
  - leading zero bytes are removed;
  - a `00` byte is added when the first remaining byte has its high bit set;
  - zero, including an empty `magnitude`, is written as `02 01 00`.
- **`card.der.integer_size(ref magnitude) -> u32`** returns the size that `write_integer` would write. With it, an application computes a SEQUENCE's length before writing its head (T4).
- **Capacity.** A result that does not fit the view is `Err(CardError.Capacity)`, and nothing is written (BP-6, BP-7).

A DER ECDSA signature, `SEQUENCE { INTEGER r, INTEGER s }`, is written from the raw `r ‖ s` of `card.crypto.sign` (BP-29) with `integer_size` twice, `write_head(0x30, …)` and `write_integer` twice.

**BP-46 Transactions.** Every TLV and DER API is `immediate` (BP-15).

## 11. Transport bindings and environment

The APIs of §7–§10 do not depend on the transport. How messages reach the application, and how outcomes reach the host, is defined by a *transport binding*. This version defines two.

**BP-47 Bindings.** A platform claims one or more bindings. An application is built for exactly one binding, which its build configuration names. A build for the ISO 7816 binding applies the check of BP-52. An application runs only on a platform that claims its binding.

**BP-48 Whole messages.** In every binding:
- the platform reassembles a message that the transport splits into parts, and the application's `command` runs once, on the whole request;
- the platform delivers a whole response, however the transport has to split it;
- a platform supports requests of at least 1280 bytes, and gives every command a response view of at least 1280 bytes (HEP-5, HEP-6).

### 11.1 The ISO 7816 binding

This binding carries commands as ISO/IEC 7816-4 APDUs, over contact or contactless (NFC) interfaces.

**BP-49 Chaining and length.** The platform accepts command chaining (CLA bit `0x10`) and, where the interface supports it, extended-length APDUs. It returns a long response with `61xx` and GET RESPONSE, or with extended length, as the host requests.

**BP-50 The request.** `request` is the reassembled command APDU without its length fields:
- `request[0]` is CLA, with the chaining bit cleared;
- `request[1]` is INS, and `request[2]` and `request[3]` are P1 and P2;
- `request[4 .. request.length]` is the reassembled data field.

Le is not passed: `response.length` is the capacity (HEP-6). The platform handles the SELECT of the application itself, and never passes it to `command`. The data of the SELECT response comes from `on_select` (BP-50a).

**BP-50a The `on_select` handler.** In this binding, an application may declare a handler `function on_select(response: inout u8[]) -> u32`. On every SELECT of the application, the platform runs it with a fresh response view of at least 256 bytes:
- an outcome of `Ok(count)` makes the first `count` bytes of the view the SELECT response data, with status word `9000`;
- `Err` and traps are reported as for `command` (BP-51), and the application is not selected.

Without the handler, the SELECT response has no data and status word `9000`. Like every lifecycle handler (PLT-18, STA-8), `on_select` cannot be called by application code. A declaration under that name with any other signature, or a call to it, is rejected when the application is built for the binding. CTAP uses this handler to return its version string (WP8 step 0, R3).

**BP-51 Status words.** The outcome of a command is reported as follows. The four categories map to disjoint status words, so they stay distinguishable (PLT-9):

| Outcome | Status word |
|---|---|
| `Ok(count)` | `9000`, after the `count` response bytes (BP-49 for long responses) |
| `Err` of an application error with code `c` | `c` |
| `Err(CardError.m)` | `6F00 + code(m)`, with `code(m)` from §4 |
| A trap | `6F00` |

**BP-52 Application error codes.** In an application built for this binding, every member of the application's error set (OUT-16) has a code in `6200`–`6EFF`, or in `9100`–`9FFF`. Any other code is rejected when the application is built for the binding, so no application error can be confused with `9000` or the `6Fxx` platform range. Protocols that report their own status inside the response data, as CTAP2 does, return it with `Ok`.

### 11.2 The raw binding

This binding carries messages without a card-specific framing, for example between a host and an application in a Trusted Execution Environment such as TrustZone-M on a microcontroller.

**BP-53 Messages and outcomes.** `request` is the message, exactly as the host sent it. The response the host receives is an *envelope*:

```text
category (1 byte) || code (2 bytes, big-endian) || data
```

| Outcome | `category` | `code` | `data` |
|---|---|---|---|
| `Ok(count)` | `0x00` | `0x0000` | The first `count` bytes of `response` |
| `Err` of an application error | `0x01` | The member's code (OUT-16) | Empty |
| `Err(CardError.m)` | `0x02` | `code(m)` from §4 | Empty |
| A trap | `0x03` | `0x0000` | Empty |

The four categories are distinct (PLT-9). Whether a platform reports a trap's kind, in the code field or otherwise, is platform-defined (PLT-10). A security reset or a power loss may produce no envelope at all (RTF-10). Application error codes are restricted only by OUT-16.

**BP-53a Session control.** Besides messages, the raw binding's host interface has two operations: *open session* and *close session*. Their encoding is platform-defined, because they are not messages to the application. See BP-56.

### 11.3 Environment and lifecycle

**BP-54 User presence.** On a contactless interface, presenting the card counts as a test of user presence: an application may treat every command it receives there as made with the user present. Any other means of establishing presence is platform-defined. This version has no API for it.

**BP-55 Lifecycle handlers.** The profile uses the handler names of the language placeholders (STA-6, PLT-18):

- **`on_install()`** runs once, when the application is installed, before any command. If it traps or returns `Err`, installation fails, and the application is not installed.
- **`on_session_start()`** runs at every session start (STA-4, BP-56), after session state and volatile keys have been reset, and before the first command of the session. If it traps or returns `Err`, the application stays unavailable until the next session start, and the platform reports every command to it as it reports a trap.

**Deselection ends the session** in the ISO 7816 binding (WP12, for PIV's application security status). When another application is selected, the application's session ends (STA-4): session state, volatile keys and session operations are discarded. The next SELECT of the application starts a new session; `on_session_start` runs before `on_select`. A SELECT of the application while it is already selected changes nothing. Logical channels are not visible to applications in this version.

**BP-56 Session events (STA-4).** Each binding defines its session events:

| Binding | A session starts | A session ends |
|---|---|---|
| ISO 7816 | At power-on, when the card receives its reset and sends its ATR; and at the first SELECT of the application after it was deselected | When another application is selected (deselection), at power-off, or at a security reset |
| Raw | When the host opens a session (BP-53a) | When the host closes it, at a new open session (STA-4), at power-off, or at a security reset |

In both bindings a security reset ends the session of every application (RTF-9).

## 12. Answers to the Annex B §B.12 checklist

| Item | Answer in this profile |
|---|---|
| `CardError` member names and codes (EXP-29, OUT-19) | §4 |
| Platform API catalog (NAM-18, PLT-25) | §6 and `platform/base-catalog.txt` |
| Platform-supplied types (NAM-14 item 4) | §3 and `platform/base-types.card` |
| Resource lifetimes at a session start and at security reset (PLT-23) | §5, BP-14 |
| Session events, per binding (STA-4, PLT-18) | §11, BP-56 |
| Which received bytes form the request; the response capacity (HEP-5, HEP-6) | §11, BP-48 to BP-50 and BP-53 |
| How outcome categories and codes reach the host (HEP-12, PLT-9) | §11, BP-51 (ISO 7816) and BP-53 (raw) |
| Lifecycle events and handlers (STA-6, PLT-18) | §11, BP-50a and BP-55 |
| Session state at deselection and on logical channels (STA-4) | §11, BP-55 and BP-56: deselection ends the session in the ISO 7816 binding; logical channels are not visible |
| User presence | §11, BP-54 |
| Side-channel and fault protection level (PLT-32) | Left to the implementation, which states its level |
| Every other item | Left to the implementation |
