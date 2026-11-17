# Base platform API and intrinsics — design plan

Status: B1–B8 decided 2026-11-17; B9 withdrawn except for feature profiles (§6, "Decided"). Where §2–§5 differ from the decisions, the decisions win; the sections are updated when each work package is drafted.

## 1. Goal

Design a **small base API** that:

- sets the look and feel of every later platform API: naming, parameters, resources, errors and transaction behaviour;
- is enough to write a **basic FIDO2 authenticator** (CTAP 2.1 over NFC/ISO 7816) in CardLang.

It is not a full platform. Everything here must stay inside the rules Draft 0.1 already set for platform APIs:

- they are reached through `card.` paths (NAM-18);
- every entry is described in a catalog (PLT-25);
- runtime objects are named by `u32` identifiers (PLT-20 to PLT-23);
- types are visible and nothing has a hidden layout (PLT-21);
- each API states its transaction behaviour (PLT-24, TXN-17).

## 2. Where each piece belongs

Draft 0.1 never wrote down where the line between an intrinsic and a platform API falls. The first deliverable is that rule (it becomes a new rule in chapter 6 and a matching `PLT` rule).

- **Intrinsic or syntax:** the language can define the operation completely, using only language values. It is deterministic and portable, fails only by a compile error or a trap, and often needs type information that only the compiler has.
- **Platform API:** the operation depends on platform state or hardware, such as keys, randomness or crypto engines. It may be missing on some platforms, fails with `CardError`, and needs stated transaction behaviour.
- **Source library:** pure byte processing that CardLang can express itself, shipped as `.card` files added to the build's source list.

Under that rule, your five items fall like this:

| Item | Layer | Notes |
|---|---|---|
| 1. Array moving and comparing | Language | Slice assignment and comparison intrinsics. The security expectations go in Annex B |
| 2. Canonical CBOR | Platform API or source library | Decision B2. There is a real tension, explained in §4.2 |
| 3. TLV | Platform API or source library | Same choice as CBOR. Decision B3 covers the TLV flavour |
| 4. Keys | Platform API | Resources under PLT-20 |
| 5. Crypto operations | Platform API | One-shot calls, and multi-part operations as resources |

**Where the work lands:**
- *Language changes* go into the Draft 0.2 chapters and Annex B.
- *The API itself* gets a new document, `platform/base-profile.md`, the **CardLang Base Platform Profile**. It is normative for any platform that claims the profile. This keeps the layers apart: the language spec still defines no real API (PLT-26).
- *The catalog* becomes a machine-readable `platform/base-catalog.txt`, in the format the checkers already read.

## 3. Language work

### 3.1 Moving arrays: slice assignment

```text
response[0..32] = rp_id_hash;            // whole fixed array into a view region
buffer[offset..offset + n] = data[0..n];
```

- **Typing.** Both sides have element type `T`. The left side is a slice, or a whole array reached through an assignable place (STM-7).
- **Lengths.** The two lengths must be equal. This is checked at compile time when both lengths are constant, and is otherwise `trap(BOUNDS)`.
- **Overlap.** The copy behaves as if the source were copied into a temporary first, like `memmove`.
- **Persistent destination.** Decision B1(c) settles whether such a copy is one atomic assignment.
- **Rule changes.** This lifts the "no whole-slice assignment" part of FUN-18. Slices are still not allowed anywhere else.

### 3.2 Comparing arrays: intrinsics

| Intrinsic | Result | Meaning |
|---|---|---|
| `equal(ref a, ref b)` | `bool` | The lengths are equal and every element is equal. Timing depends only on the lengths (a `PLT` requirement, §3.3) |
| `compare(ref a, ref b)` | `i8` | Lexicographic order, giving −1, 0 or 1. It is not constant-time. It is needed for canonical CBOR key order |

Both are value-producing intrinsics, like `convert`, so they need no `attempt`.

### 3.3 Security expectations for platforms (new Annex B section)

This section is written as obligations on a platform, not as language rules:

- **Constant time.** `equal` and every cryptographic API run in time independent of secret data.
- **Side channels.** Platforms provide protection against side channels and fault injection that is appropriate to the target, with the level stated in the target profile.
- **Key material.** Key material never appears in application-visible memory, except where an API exports it explicitly (public keys, and imported or exported secrets that the catalog marks as such).
- **Wiping memory.** Writes to memory that is about to be discarded must not be removed by optimization when the program means them as wiping. EXP-22 currently allows removing writes nobody can observe, which would allow a compiler to drop a zeroizing `fill`. **Proposed:** a `wipe(inout x)` intrinsic whose writes are never removed, plus the `PLT` obligation.

## 4. Platform API design

### 4.1 Common conventions (the "look and feel")

These conventions are written down first, because every API follows them:

- **Paths.** Paths name a family and an action: `card.key.generate`, `card.crypto.sign`, `card.random.fill`.
- **Argument order.** Resource identifier first, then configuration, then input views (`ref`), then output views (`inout`).
- **Output.** An API that writes output returns the number of bytes written as its `u32` payload. An output region that is too short is `Err(CardError.Capacity)`, and nothing is written.
- **Configuration.** Configuration is passed as platform-supplied structures and enums with visible declarations (PLT-21), for example `KeySpec` and `Curve`. There are no bit masks.
- **Errors.** Every API lists its `CardError` members. A failed verification is a result (`bool`), not an error.

### 4.2 CBOR and TLV: where to put them

These are the arguments for each option.

**A source library in CardLang** (`lib/cbor.card`, `lib/der.card`):
- It is portable, testable with the interpreter, and puts no burden on platforms.
- It is the best test of the language itself.

It also has **two blocking problems** in Draft 0.1:
1. **Error sets.** An application may have only one `errors` declaration, and a library cannot have its own. A library would have to report errors through the application's set, or through return codes instead of `Err`.
2. **Names.** There are no namespaces, so library names share the application scope. Prefixes such as `cbor_` work, but by convention only.

**A platform API** (`card.cbor.*`, `card.der.*`):
- It has neither problem: errors are `CardError.Malformed` and similar, and paths are already namespaced.
- It is native code, so it is smaller and faster on a card.
- The cost is a bigger platform, and the parser is no longer a test of the language.

My recommendation is a **platform API for decoding and encoding primitives**, built on a cursor, while application code drives the structure. This mirrors what real card stacks do, and it avoids language changes for now. Library-style error sets and namespaces stay as a later language question.

**The API shape: a reader and a writer over a byte view, with the position held in an application struct.**

```text
var reader: CborReader = card.cbor.reader(0);           // illustrative
var head: CborHead = attempt card.cbor.read_head(ref request[1..request.length], inout reader);
match head.major { … }
```

- `CborHead` holds the major type, an argument value and a length, and `CborMajor` is an enum. Both have visible declarations.
- Maps and arrays are walked by count. A `skip` operation skips a nested item, which needs no recursion.
- Integers are limited to the `i32`/`u32` range, because there is no 64-bit type. Anything larger is `Err(CardError.Unsupported)`. This is enough for CTAP: COSE labels and algorithms are small negative numbers.
- **Canonical CBOR (the CTAP2 canonical form).** The writer always produces canonical output: shortest-form integers, definite lengths, and no tags or floats. Writing map keys in order is the application's job, using `compare`. Decision B2(b) settles whether the reader rejects input that isn't canonical.

**TLV.** I partly disagree with "DER only":
- **Encoding:** DER only. FIDO2 needs it for the ECDSA signature (and attestation, which treats certificates as opaque bytes).
- **Decoding:** ISO 7816-4 **BER-TLV with definite lengths**, which covers multi-byte tags and the length forms. DER is a strict subset, so a DER parser comes for free, and the same decoder serves card protocols (GlobalPlatform, PIV, EMV-style data). Indefinite lengths are rejected.

### 4.3 Keys

Keys are resources under PLT-20, created with a `KeySpec`:

```text
struct KeySpec {             // supplied by the platform (PLT-21), shown for look and feel
    kind: KeyKind;           // Aes, EcPrivate, EcPublic
    curve: Curve;            // P256 (required), P384, Ed25519 (optional; see B4)
    bits: u16;               // AES: 128 or 256; EC: implied by curve
    storage: KeyStorage;     // Persistent, Volatile
    can_sign: bool;
    can_derive: bool;        // ECDH, KDF
    can_encrypt: bool;
    can_decrypt: bool;
    exportable: bool;        // secret export; never true for EcPrivate
}
```

| API | Purpose |
|---|---|
| `card.key.generate(id, spec)` | Generate with the on-card random generator. For `EcPrivate`, this generates the key pair |
| `card.key.import(id, spec, ref material)` | Create a key from bytes: an AES key, an EC public point, or an EC private scalar |
| `card.key.export_public(id, inout output) -> u32` | The uncompressed point (or the raw Ed25519 public key) |
| `card.key.delete(id)` | Delete the key and erase its material |
| `card.key.exists(id) -> bool` | Look up without error handling (optional; decision B4) |

- **Volatile keys** are cleared at power-on and at security reset, the same lifetime as session state (STA-4).
- **Persistent keys** survive power loss, like persistent globals.
- **Transactions.** Creating or deleting a persistent key is `forbidden` inside a transaction in the first version (decision B4(c)). FIDO2 then creates the key first, then stores the credential record in a transaction, and deletes the key if that fails.

### 4.4 Crypto operations

**One-shot calls.** These cover almost all of FIDO2:

| API | FIDO2 use |
|---|---|
| `card.crypto.digest(alg, ref data, inout out) -> u32` | SHA-256 of the client data, the PIN hash |
| `card.crypto.mac(key, alg, ref data, inout out) -> u32` | HMAC-SHA-256 (PIN/UV protocol, hmac-secret, credential-ID integrity) |
| `card.crypto.sign(key, alg, ref data, inout signature) -> u32` | ES256 assertions and attestation |
| `card.crypto.verify(key, alg, ref data, ref signature) -> bool` | Completeness. Not needed by a basic authenticator |
| `card.crypto.agree(key, ref peer_point, inout secret) -> u32` | ECDH P-256 for the PIN/UV protocol |
| `card.crypto.derive(alg, ref secret, ref salt, ref info, inout out) -> u32` | HKDF-SHA-256 for PIN/UV protocol 2 |
| `card.crypto.encrypt / decrypt(key, alg, ref iv, ref input, inout output) -> u32` | AES-256-CBC without padding (PIN/UV protocols), and wrapping non-resident credential IDs |

**Multi-part operations.** These are resources under PLT-20, and always volatile:

```text
attempt card.crypto.begin(op, key, alg);     // key 0 for an unkeyed digest
attempt card.crypto.update(op, ref chunk);
var n: u32 = attempt card.crypto.finish(op, inout out);   // deletes the operation
```

- **States:** an operation is active from `begin` until `finish` or `abort_operation`. Any other use is `Err(CardError.InvalidState)`.
- **Lifetime:** every operation ends at the end of the command, unless decision B5(b) says otherwise.
- **Transactions:** all crypto calls are `immediate`, because they have no persistent effect.

**Signature format.** `sign` returns a raw, fixed-size `r‖s` (64 bytes for P-256), which fits fixed arrays. The application encodes it as DER through `card.der` (FIDO2 requires DER). This also exercises the DER encoder.

**Randomness.** `card.random.fill(inout output)` uses a DRBG of the platform's own security level. It is needed for credential IDs, key generation, the PIN/UV protocol and `authenticatorReset`.

### 4.5 New `CardError` members

| Member | When |
|---|---|
| `Unsupported` | Algorithm, curve or size not provided; CBOR value out of range |
| `InvalidState` | Multi-part operation misused |
| `NotPermitted` | Key usage not allowed by its `KeySpec` |
| `Malformed` | CBOR/TLV input that is not well-formed (or not canonical, if strict) |

These join the members Draft 0.1 already names (PLT-27): `NotFound`, `AlreadyExists`, `WrongResourceType` and `Capacity`.

## 5. What else a basic FIDO2 applet needs

| Gap | Why it matters | Proposal |
|---|---|---|
| **Large persistent data** | The attestation certificate is about 500–800 bytes, and resident-credential records are larger than a target's atomic-update limit (STA-13) | Decision B6. Either a persistent array written in chunks inside a transaction, or a small persistent blob object API |
| **Command chaining and long responses** | CTAP over ISO 7816 uses extended-length APDUs or chaining (`61xx`/GET RESPONSE). These are status-word mechanics the language deliberately doesn't see | Profile requirement: the platform reassembles chained commands and serves long responses, so `command` sees whole messages |
| **User presence** | CTAP needs it. On NFC, the tap itself counts; on contact cards there is no button | Out of the base profile. The profile states that presence is implied, and a platform event can be added later |
| **Lifecycle** | Provisioning the attestation key and certificate, and `authenticatorReset` | Use `on_install` and ordinary commands (personalisation). The handler-name placeholders stay |
| **Wiping secrets** | PIN tokens and shared secrets in session state | The `wipe` intrinsic (§3.3) |
| **Monotonic signature counter** | Assertions need it | Already covered by persistent `u32` and atomic assignment. No API needed |

## 6. Decisions needed

| ID | Question | Recommendation |
|---|---|---|
| B1 | Array operations: (a) slice assignment for moving; (b) `equal` and `compare` intrinsics; (c) a copy into persistent storage is one atomic assignment, subject to STA-13, or element by element | (a) yes; (b) yes; (c) atomic, the same as every persistent assignment, so large copies belong in a transaction |
| B2 | CBOR: (a) platform API or CardLang source library; (b) reader strict (reject non-canonical input) or lenient | (a) platform API; (b) lenient on order, strict on well-formedness. CTAP authenticators are expected to accept what clients send |
| B3 | TLV: DER only, or DER encoding plus BER-TLV decoding with definite lengths | DER encoding plus BER-TLV decoding |
| B4 | Keys: (a) curves: P-256 required, with P-384 and Ed25519 optional; (b) usage flags as bool fields in `KeySpec`; (c) persistent key creation forbidden in transactions; (d) include `exists` | (a) yes; (b) yes; (c) forbidden for now; (d) no, use `NotFound` |
| B5 | Multi-part operations: (a) identifiers as resources; (b) operations end with the command or survive into later commands | (a) yes; (b) end with the command. This is simpler and safer, and FIDO2 needs nothing more |
| B6 | Large persistent data: chunked writes to persistent arrays in a transaction, or a blob object API | Chunked writes plus transactions, no new API. Revisit if transaction capacity proves too small |
| B7 | Reference implementation: implement real SHA-256, HMAC, HKDF, AES and P-256 ECDSA/ECDH in the interpreter (pure Python, test-only), so CTAP test vectors can run | Yes. Hash and HMAC come from the Python standard library; AES and P-256 are small pure-Python implementations |
| B8 | Document location: the new `platform/base-profile.md` and `platform/base-catalog.txt`, separate from `spec/` | Yes |

### Decided

These decisions take precedence over the proposals in §2–§5.

- **B1 (2026-11-17):**
  - (a) slice assignment;
  - (b) the `equal` and `compare` intrinsics;
  - (c) a slice assignment into persistent storage is atomic, the same as every persistent assignment (STA-11, STA-13).
- **B2:**
  - (a) CBOR is a platform API, `card.cbor.*`;
  - (b) the reader is **strict canonical**: it rejects non-shortest encodings and map keys out of canonical order as `Err(CardError.Malformed)`. This overrides the recommendation.
- **B3:** a DER writer (always minimal) and an ISO 7816-4 BER-TLV reader with definite lengths only, which also parses DER.
- **B4:**
  - (a) **P-256 only**. Other curves come later, and `Curve` stays an enum so it can grow.
  - (b) **No usage restrictions.** `KeySpec` keeps only the kind, the size and the storage. Two consequences:
    - `NotPermitted` is dropped from the new `CardError` members;
    - there is no export of secret or private key material at all, only `export_public`.
  - (c) **Persistent key creation and deletion participate in transactions.** Platforms must journal key storage, and those writes count against transaction capacity (TXN-16). Volatile keys are not persistent state (TXN-4): creating or deleting one inside a transaction is immediate.
  - (d) no `exists`.
- **B5:**
  - (a) Multi-part operations are named by `u32` resource identifiers (PLT-20).
  - (b) **Both lifetimes are supported.** `begin` takes a platform-supplied `OperationLifetime` enum with two values:
    - `Command`: discarded when the command ends, whether it returns or traps;
    - `Session`: survives into later commands until `finish`, a security reset or power-on, like session state.

    Both kinds count against the platform's resource capacity (`CardError.Capacity`).
- **B6:** large persistent data is written in chunks within the atomic limit, and grouped in a transaction when it must land together. There is no new feature. Revisit if transaction capacity proves too small in the FIDO2 check (WP8).
- **B7:** the interpreter implements real cryptography, using only the Python standard library:
  - SHA-256, HMAC and HKDF from `hashlib` and `hmac`;
  - small pure-Python, test-only implementations of AES and P-256;
  - deterministic ECDSA (RFC 6979), so test expectations are exact.
- **B8:** the profile documents live in a new top-level `platform/` folder, separate from `spec/`:
  - `platform/base-profile.md` for the profile itself;
  - `platform/base-catalog.txt` for its machine-readable catalog.

  Feature profiles and capacity classes (B9) are documented there.
- **B9: profiles and the capacity model.** **Withdrawn 2026-11-17, except for feature profiles (OI-51, D-451).** The real commit cost cannot be known at compile time, so capacity classes, logical sizes and the footprint analysis were dropped, and the Draft 0.1 capacity model stays. Feature profiles (sets of APIs and algorithms) remain. A runtime capacity query may be considered as a platform API in WP2. The original text follows for the record. This decision was added during the discussion.
  - **Two kinds of profile.**
    - A *feature profile* says which APIs and algorithms exist, for example a base profile with P-256 only.
    - A *capacity class* states guaranteed minimums.

    A device claims one of each, an application states what it needs, and the build checks the match.
  - **Logical footprint.** Capacity is measured in language terms, never in device bytes.
    - A persistent write costs the *logical size* of its destination, computed from its type: `u8` and `bool` are 1, `u16` is 2, `u32` is 4, and structures and arrays add up. This is a measuring rule, not a representation, so TYP-9 still holds.
    - Each creation or deletion of a persistent key costs one *key unit*, whatever it really occupies. The platform absorbs the real cost.
  - **Guaranteed minimums.** A capacity class states:
    - the minimum transaction capacity, in logical bytes and key units;
    - the minimum atomic assignment size (STA-13).

    A device claiming the class must commit every transaction within those minimums. It may offer more, but an application that relies on more is not portable to the class.
  - **Static check.** The call graph is static and acyclic, so the compiler computes a transaction's maximum footprint when its loops have constant bounds:
    - if the bound is within the class minimum, the transaction is guaranteed to fit;
    - if it is above the minimum, the application is rejected for that class;
    - if no bound can be computed, the transaction is accepted, `trap(TXN-CAPACITY)` remains the safety net, and the tooling reports that it has no guarantee.

    This is the same kind of analysis RTF-7 requires for stack depth.
  - **Language work.** This adds a definition of logical size, the footprint bound analysis, and amendments to TXN-16, STA-13, PLT-15 and PLT-29 (Draft 0.2, work package WP1 or a new WP).

## 7. Work packages, in order

| WP | Output | Depends on |
|---|---|---|
| WP1 | The intrinsic/API boundary rule; slice assignment; `equal`, `compare`, `wipe`; the Annex B security-expectations section. Rules, tests, checker and interpreter (Draft 0.2 language changes) | B1 |
| WP2 | The profile skeleton: conventions (§4.1), the catalog format, new `CardError` members, the platform-supplied type declarations | B8 |
| WP3 | Keys | WP2, B4 |
| WP4 | Crypto: one-shot calls, multi-part operations, randomness. Interpreter implementations and test vectors | WP3, B5, B7 |
| WP5 | CBOR reader and writer | WP2, B2 |
| WP6 | DER writer and BER-TLV reader | WP2, B3 |
| WP7 | Large persistent data, command chaining (profile requirements) | B6 |
| WP8 | **FIDO2 check:** write the core of an authenticator in CardLang, for the interpreter. It covers `getInfo`, `makeCredential` (ES256, non-resident credentials), `getAssertion`, `clientPIN` protocol 2 and `reset`. Everything that hurts is recorded as input to the language | WP1–WP7 |

Each work package follows the usual rhythm: a sub-plan for your review, then drafting, then verification with `run_checks.py`.
