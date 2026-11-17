# WP3 — Keys (`card.key`): detailed sub-plan

Parent: `plans_and_notes/base-api-plan.md` (B4), and the profile conventions of WP2 (`platform/base-profile.md`).
Status: decisions K1–K5 taken 2026-11-17 (§4). **Drafted 2026-11-17.**

## 1. Scope

WP3 fills in profile §7 and adds the first entries to `platform/base-catalog.txt`. It also gives the interpreter real P-256, so key tests check real values. It covers:

- the key types and `KeySpec` (K1);
- four APIs: `generate`, `import`, `export_public` and `delete`;
- material formats, validation and errors;
- lifetimes and transactions, from B4(c) and BP-14 and BP-15;
- interpreter support and tests.

The cryptographic *use* of keys (signing, ECDH, MAC, ciphers) is WP4.

## 2. Design

### 2.1 Key types and `KeySpec` (K1)

WP2 declared `KeySpec` with `kind`, `curve`, `bits` and `storage`. That shape allows meaningless combinations, such as an AES key with a curve. And because a structure constructor needs every field (CE-EXP-12), an AES key must still name a curve. **Recommendation:** replace `kind`, `curve` and `bits` with a single enum that lists only valid key types:

```text
enum KeyType {
    Aes128;
    Aes256;
    EcP256Private;     // a P-256 key pair; the public part can be exported
    EcP256Public;      // a P-256 public key only, for example a peer's key
}

struct KeySpec {
    type: KeyType;
    storage: KeyStorage;
}
```

A new curve or size becomes a new enum value in a later profile version. `KeyKind` and `Curve` are removed from `base-types.card`.

### 2.2 APIs

| API | Parameters | Payload | Errors (BP-8 order) |
|---|---|---|---|
| `card.key.generate` | `id: u32, spec: KeySpec` | — | `AlreadyExists`, `Unsupported`, `Malformed`, `Capacity` |
| `card.key.import` | `id: u32, spec: KeySpec, material: ref u8[]` | — | `AlreadyExists`, `Unsupported`, `Malformed`, `Capacity` |
| `card.key.export_public` | `id: u32, output: inout u8[]` | `u32` | `NotFound`, `WrongResourceType`, `Capacity` |
| `card.key.delete` | `id: u32` | — | `NotFound`, `WrongResourceType` |

- **`generate`** uses the platform's random generator. `EcP256Public` cannot be generated, so it is `Unsupported`.
- **`import`** takes this material. The wrong length, or an invalid value, is `Malformed`:
  - AES keys: the raw key (16 or 32 bytes);
  - `EcP256Private`: the 32-byte big-endian private scalar `d`, with `1 ≤ d < n`; the public point is derived;
  - `EcP256Public`: a 65-byte uncompressed SEC 1 point `04 ‖ X ‖ Y`, which must lie on the curve.
- **`export_public`** writes the 65-byte uncompressed point of an `EcP256Private` or `EcP256Public` key. An AES key has no public part (K2).
- **`delete`** deletes the key and erases its material (PLT-33).
- **Identifier 0** never names a resource (PLT-20). Using or creating one is K3.
- **No secret export, no usage flags, no `exists`** (B4(b), B4(d)).

### 2.3 Lifetimes and transactions

These were decided in WP2 and B4(c), and are stated here concretely:

- **Lifetimes.** Volatile keys disappear at power-on and at security reset. Persistent keys survive both, and power loss.
- **Persistent keys in a transaction.**
  - `generate`, `import` and `delete` of a persistent key take part in an active transaction. Inside it, the change is visible at once (read-your-writes, TXN-2), and it commits or rolls back with the transaction.
  - After a rollback, a deleted key exists again with the same material, and a created key does not exist.
  - Each change counts against the platform's transaction capacity. Overflow is `trap(TXN-CAPACITY)` (TXN-16).
- **Volatile keys** are not persistent state (TXN-4). Changing them inside a transaction takes effect immediately.
- **Recovery.** After an interruption, the keys reflect all of the transaction or none of it (TXN-13).

### 2.4 Profile rules

New rules, BP-18 onwards, in profile §7:
- the key types;
- one rule per API;
- the material formats;
- transaction behaviour;
- erasure on deletion.

The catalog gains four blocks.

## 3. Interpreter and tests

- **The interpreter gets P-256**: pure Python, test-only, standard library only (B7). That covers point arithmetic, deriving a public point and validating a point. A deterministic random generator is used for tests (K4).
- **The test catalog's fictional `card.test.*` entries are untouched.** The language tests keep using them.
- **Tests** (new generator `tools/generators/wp3_tests.py`):
  - Compile time: a valid use of every API; a wrong argument type; `import` with a missing `ref`; and redeclaring `KeyType` (CE-NAM-5).
  - Runtime, a key scenario:
    - import a known private scalar (a published P-256 test vector), then export the public point and compare it with the published `X ‖ Y`;
    - generate a key pair, export its public point, and import that point as `EcP256Public`. The import validates the point is on the curve, so a broken implementation fails;
    - the error cases: duplicate identifier, unknown identifier, export of an AES key, a malformed point, and an output view too short;
    - a persistent `generate` rolled back by `abort`, and a `delete` rolled back by a trap;
    - a volatile key gone after `reset`, and a persistent one still there.
- **`profilecheck`** validates the new blocks automatically.

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| K1 | The shape of `KeySpec` | (a) `KeySpec { type: KeyType, storage: KeyStorage }`, with `KeyType` listing only valid key types (§2.1); (b) keep `kind`, `curve` and `bits`, with invalid combinations being `Unsupported` | (a) |
| K2 | The error for a key of the wrong *key type*, such as `export_public` on an AES key | (a) `WrongResourceType`, reading PLT-22's "wrong kind" to include the key type; (b) `Unsupported` | (a). It is one rule, and the same check an application already handles |
| K3 | Identifier 0 | (a) using it is `NotFound`; creating with it is `Malformed`; (b) both `NotFound` | (a). Creating with an invalid identifier is a malformed argument |
| K4 | Randomness in the interpreter | (a) a deterministic DRBG with a fixed seed, which a scenario can reset with a new `seed <hex>` step; (b) real OS randomness, with tests that never depend on generated values | (a). Runs are reproducible, and tests may still avoid depending on generated bytes |
| K5 | A key information API, `card.key.info(id) -> KeySpec` | (a) no, as for `exists` in B4(d); (b) yes, for provisioning code that checks what exists | (a). It can be added in a later version |

**Decided 2026-11-17.** You accepted every recommendation:

- **K1 (a):** `KeySpec { type: KeyType, storage: KeyStorage }`. `KeyKind` and `Curve` are removed.
- **K2 (a):** a key of the wrong key type is `WrongResourceType`.
- **K3 (a):** using identifier 0 is `NotFound`; creating with it is `Malformed`.
- **K4 (a):** the interpreter uses a deterministic DRBG, with an optional `seed <hex>` scenario step.
- **K5 (a):** there is no `card.key.info`.

## 5. Exit checklist

- Profile §7 is written. The catalog has four blocks, and `profilecheck` passes.
- `base-types.card` has the shape K1 decides, and the WP2 tests are updated.
- The interpreter's P-256 reproduces the published test vector.
- `python -I tools/run_checks.py` passes.
