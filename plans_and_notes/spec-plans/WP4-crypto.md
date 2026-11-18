# WP4 — Crypto operations and randomness (`card.crypto`, `card.random`): detailed sub-plan

Parent: `plans_and_notes/base-api-plan.md` (§4.4, B5, B7), and the WP2/WP3 profile conventions.
Status: decisions C1–C6 taken 2026-11-18 (§5). **Drafted 2026-11-18.** Deviation: on Err(Capacity) from finish, the operation stays active (consistent with BP-7) instead of being deleted, so the application can retry with a larger view.

## 1. Scope

WP4 fills in profile §8 and adds the crypto and random entries to the catalog, with real implementations in the interpreter. The algorithms are what a basic FIDO2 authenticator (CTAP 2.1) needs:

| Need | Algorithm |
|---|---|
| Client data hash, PIN hash, authenticator data | SHA-256 |
| PIN/UV protocol, hmac-secret, credential-ID integrity | HMAC-SHA-256 |
| Assertion and attestation signatures (ES256) | ECDSA P-256 with SHA-256 |
| Key agreement in the PIN/UV protocol | ECDH P-256 |
| Key derivation in PIN/UV protocol 2 | HKDF-SHA-256 |
| PIN/UV protocol encryption, wrapping credential IDs | AES-128/256-CBC without padding |
| Credential IDs, salts, PIN tokens, key generation | A random generator |

## 2. The central question: where secrets live (C1)

FIDO2 computes secrets: an ECDH shared secret, HKDF outputs, a PIN token, and keys for non-resident credentials. There are two consistent ways to handle them:

- **(a) The byte model.** Derived values are ordinary bytes in application memory:
  - `agree`, `derive` and `mac` write their results into `inout` views;
  - an application that needs a derived value as a key imports it into a volatile key (WP3), and erases its copy with `wipe` (STM-23);
  - non-resident credential keys are *derived* (for example, `d = HMAC(master, rpIdHash ‖ nonce)` reduced into range, then imported), so no key wrapping API is needed.

  This needs one clarification in Annex B. PLT-33 currently says secret material never appears in application memory. It would become: the material *of a key resource* is never exposed. Values the application computes itself are its own data.
- **(b) The resource model.** Secrets never leave the platform:
  - `agree` and `derive` create key resources;
  - a PIN token is a generated key;
  - sending a token or a credential key to the host needs `card.key.wrap` and `card.key.unwrap`, which encrypt a key's material under another key.

  This is stronger against memory disclosure, but it needs more APIs, more key types and more identifiers in every flow.

**Recommendation: (a)** for the base profile. It is simple, every CTAP flow fits it, and `wipe` gives applications a reliable way to erase what they compute. (b) can be added in a later version as a hardened option.

Either way, `KeyType` gains `Hmac256`: a 32-byte HMAC key that can be generated or imported.

## 3. API design

### 3.1 Algorithms (C2)

There is one enum per family, so the type checker rejects a wrong algorithm at compile time. Each enum has one value for now, and later versions add more:

```text
enum DigestAlgorithm { Sha256; }
enum MacAlgorithm { HmacSha256; }
enum SignatureAlgorithm { EcdsaP256Sha256; }    // ES256; signs the message, hashing it internally
enum KdfAlgorithm { HkdfSha256; }
enum CipherAlgorithm { AesCbcNoPadding; }
```

### 3.2 One-shot APIs

| API | Payload | Notes |
|---|---|---|
| `card.crypto.digest(alg, ref data, inout out)` | `u32` (32) | |
| `card.crypto.mac(key, alg, ref data, inout out)` | `u32` (32) | `key` is an `Hmac256` key |
| `card.crypto.sign(key, alg, ref message, inout signature)` | `u32` (64) | `key` is an `EcP256Private` key. The output is raw `r ‖ s`, 32 bytes each, big-endian. DER is WP6 |
| `card.crypto.verify(key, alg, ref message, ref signature)` | `bool` | `key` is `EcP256Private` or `EcP256Public`. A signature of the wrong length is `false`, not an error (BP-10) |
| `card.crypto.agree(key, ref peer, inout secret)` | `u32` (32) | ECDH. `peer` is a 65-byte uncompressed point (BP-21). The output is the x-coordinate of the shared point. An invalid point is `Malformed` (C3) |
| `card.crypto.derive(alg, ref secret, ref salt, ref info, length, inout out)` | `u32` | HKDF. `length` is the number of bytes requested, between 1 and 255 × 32 |
| `card.crypto.encrypt(key, alg, ref iv, ref input, inout output)` | `u32` | `key` is an AES key. `iv` is 16 bytes. The input length must be a multiple of 16, otherwise `Malformed` |
| `card.crypto.decrypt(…)` | `u32` | As `encrypt` |

For the ciphers, `output` may overlap `input`. The result is as if the input were copied first.

### 3.3 Multi-part operations (B5)

These cover inputs that arrive in pieces: digest, MAC and signature generation or verification.

```text
attempt card.crypto.begin_digest(op, DigestAlgorithm.Sha256, OperationLifetime.Command);
attempt card.crypto.begin_mac(op, key, MacAlgorithm.HmacSha256, lifetime);
attempt card.crypto.begin_sign(op, key, SignatureAlgorithm.EcdsaP256Sha256, lifetime);
attempt card.crypto.begin_verify(op, key, SignatureAlgorithm.EcdsaP256Sha256, lifetime);
attempt card.crypto.update(op, ref chunk);
var n: u32 = attempt card.crypto.finish(op, inout out);            // digest, MAC or signature
var ok: bool = attempt card.crypto.finish_verify(op, ref signature);
attempt card.crypto.cancel(op);
```

- **Identifiers.** An operation is a resource of kind *Operation*, in the shared identifier space (BP-13).
- **Ending.** `finish`, `finish_verify` and `cancel` delete the operation. The `finish` call that matches the operation's purpose deletes it even when it returns `Err(Capacity)`, so no operation is left half-done. Using the wrong finish for the purpose is `InvalidState`.
- **Lifetime** follows BP-14. A key deleted while an operation uses it makes the operation's next call `InvalidState`.
- **Ciphers** are one-shot only in this version.

### 3.4 Randomness

`card.random.fill(inout out) -> u32` fills the whole view from the platform's random generator and returns its length, following BP-6. The generator's quality and evaluation are platform-defined, at the security level of the target profile (PLT-32).

### 3.5 ECDSA nonces (C4)

The nonce `k` is either RFC 6979 deterministic or random from a secure generator; the platform chooses. Conformance tests therefore never expect exact signature bytes from `sign`. They check signatures with `verify`, and against a fixed public key and message. The interpreter uses RFC 6979, so its own self-test can reproduce the published vector.

### 3.6 Transactions

Every crypto and random API is `immediate` (BP-15): none of them has persistent effects. Operations are volatile resources.

## 4. Interpreter and tests

- **Implementations** (B7, standard library only):
  - SHA-256, HMAC and HKDF use `hashlib` and `hmac`;
  - AES-128 and AES-256 are pure Python, with CBC on top;
  - ECDSA uses `p256.py`, with RFC 6979 nonces;
  - ECDH uses `p256.py`.

  The new code goes in `tools/interp/testcrypto.py`, with self-tests against the published vectors: FIPS 197 (AES), RFC 4231 (HMAC), RFC 5869 (HKDF) and RFC 6979 A.2.5 (ECDSA).
- **Tests** (new generator `wp4_tests.py`):
  - Compile time: a valid use of every API; a wrong algorithm enum, such as a `MacAlgorithm` passed to `digest` (CE-EXP-1); a missing `inout`.
  - Runtime: published vectors run through a CardLang program, using `digest`, `mac` (with an imported `Hmac256` key), `derive` and `encrypt`/`decrypt`. The FIPS 197 block is used as single-block CBC with a zero IV.
  - Runtime: sign, then verify; verify a tampered message; and a multi-part sign checked with a one-shot `verify`.
  - Runtime: ECDH between two key pairs gives the same secret on both sides.
  - Runtime: the operation states — `update` after `finish` is `NotFound`, the wrong finish is `InvalidState`, and a `Command`-lifetime operation is gone in the next command while a `Session` one survives until reset.
  - Runtime: the errors `Malformed` (a bad IV length, an unaligned input, a bad peer point) and `Capacity`.
  - Runtime: `random.fill` produces the interpreter's deterministic stream after a `seed` step.

## 5. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| C1 | Where derived secrets live | (a) the byte model, with PLT-33 clarified to cover the material of key resources; (b) the resource model, with wrap and unwrap | (a) |
| C2 | How algorithms are named | (a) one enum per family; (b) one shared `Algorithm` enum; (c) the algorithm in the API name, such as `card.crypto.sha256` | (a). It is checked at compile time and can be extended |
| C3 | The ECDH peer key | (a) a raw 65-byte point argument; (b) a key identifier, so the point must be imported first | (a). One call, and the same validation as BP-21 |
| C4 | ECDSA nonces | (a) platform-defined (RFC 6979 or a secure random `k`), with tests that verify rather than compare bytes; (b) RFC 6979 required | (a) |
| C5 | HKDF output length | (a) an explicit `length` argument; (b) the output view's length | (a). It is explicit, and keeps BP-6 (a view may be larger than the result) |
| C6 | Multi-part API shape | (a) `begin_digest`, `begin_mac`, `begin_sign` and `begin_verify`, plus shared `update`, `finish`, `finish_verify` and `cancel`; (b) one `begin` with a purpose enum | (a). Each `begin` has exactly the parameters it needs |

**Decided 2026-11-18.** You accepted every recommendation:

- **C1 (a):** the byte model. PLT-33 is clarified to cover the material of key resources, and `KeyType` gains `Hmac256`.
- **C2 (a):** one algorithm enum per family.
- **C3 (a):** the ECDH peer is a raw 65-byte point.
- **C4 (a):** ECDSA nonces are platform-defined, and tests verify signatures rather than compare bytes.
- **C5 (a):** HKDF takes an explicit `length` argument.
- **C6 (a):** there is a `begin_*` call per purpose.

## 6. Exit checklist

- Profile §8 is written. The catalog has every new entry, and `profilecheck` passes.
- `testcrypto.py` passes its self-tests against the published vectors.
- `python -I tools/run_checks.py` passes.
