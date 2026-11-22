# WP2 — Base profile skeleton: detailed sub-plan

Parent: `plans_and_notes/base-api-plan.md` (decisions B2–B8; B9 kept only for feature profiles).
Status: decisions D1–D5 taken 2026-11-17 (§4). **Drafted 2026-11-17.**

## 1. Scope

WP2 creates the frame that WP3–WP7 fill in. It specifies no API family itself; those are keys (WP3), crypto and randomness (WP4), CBOR (WP5) and DER/BER-TLV (WP6). Its deliverables:

| File | Contents |
|---|---|
| `platform/base-profile.md` | The **CardLang Base Profile**: conformance, conventions, types, `CardError`, resources, and empty sections for each API family |
| `platform/base-catalog.txt` | The machine-readable catalog of the profile's APIs. It starts empty and grows in WP3–WP6 |
| `platform/base-types.card` | The platform-supplied declarations: enums and structures (D2) |
| `tools/` | The checkers load the base catalog and types. A `profilecheck` run checks the catalog's format and the profile's consistency |

The language specification is not changed, except to cross-reference the profile from Annex B (informative), if needed.

## 2. The profile document's structure

1. **Scope and conformance.** A platform conforms to the Base Profile when it:
   - conforms to the language specification (PLT-1);
   - provides every catalog entry, with the stated behaviour;
   - supplies the base types exactly as declared.

   It may add APIs, `CardError` members and algorithms, but must not change those the profile defines. The profile has a version, starting at "Base Profile 1".
2. **Conventions** (from base plan §4.1, made normative):
   - **Paths:** `card.<family>.<action>`. The families are `key`, `crypto`, `random`, `cbor` and `der`/`tlv`.
   - **Argument order:** resource identifier, then configuration, then inputs (`ref`), then outputs (`inout`).
   - **Output:** an API that writes output returns the number of bytes written as its `u32` payload. An output that is too short is `Err(CardError.Capacity)`.
   - **Effect of failure:** D4.
   - **Error precedence:** D4.
   - **Failure is never a trap.** A failing API returns `Err`; it never traps, except where the language itself requires a trap: argument preparation (FUN-11), and runtime capacity (TXN-16, STA-13).
   - **Comparisons are results.** A failed verification or comparison is a `bool` result, never an `Err`.
3. **Types.** Every platform-supplied enum and structure, with its full declaration (PLT-21). WP2 declares the shared ones, and the families add theirs:
   - `KeyKind`, `Curve`, `KeyStorage`, `KeySpec` (WP3 fills in the details);
   - `Algorithm` (WP4);
   - `OperationLifetime` (B5);
   - `CborMajor`, `CborHead`, `CborReader`, `CborWriter` (WP5);
   - `TlvHead` and the DER and TLV reader and writer (WP6).
4. **`CardError`.** The complete member list of the profile, with codes (D3):
   - the existing members (PLT-27): `Overflow`, `Underflow`, `DivisionByZero`, `ConversionRange`, `AlreadyExists`, `NotFound`, `WrongResourceType` and `Capacity`;
   - the new ones: `Unsupported`, `InvalidState` and `Malformed`.
5. **Resources.** The profile has two resource kinds, *Key* and *Operation*. They share the application's single identifier space (PLT-20).
   - **Lifetimes:** a persistent key, a volatile key (until power-on or security reset), an operation with `Command` lifetime, and an operation with `Session` lifetime (B5).
   - **Transactions:** persistent key creation and deletion participate in transactions (B4(c)). Everything else is immediate.
   - **Capacity:** how many resources fit is platform-defined (`CardError.Capacity`). The profile may state a minimum count, such as "at least 8 keys" (D5).
6. **The catalog format** (D1).
7. **API families**, sections 7–11, left empty for WP3–WP6.
8. **Transport and environment requirements**, left for WP7: command chaining, user presence.
9. **Answers to the Annex B §B.12 checklist.** For each platform-defined item, the profile either answers it, as it does for the `CardError` codes, or says it is left to the implementation.

## 3. Catalog format (D1)

PLT-25 requires seven pieces of information per entry. The test-only catalog has five, as one `|`-separated line. My recommendation is a block format that has room for all seven:

```text
api card.key.generate
    params      id: u32, spec: KeySpec
    payload     -
    transaction participates          # participates | immediate | forbidden
    errors      AlreadyExists, Capacity, Unsupported
    resources   creates Key(id)        # creates | uses | deletes, with the kind
    on-failure  no resource is created
    permission  -
    summary     Generate a key from the platform's random generator.
```

The checker reads the first five fields, as it does today. The others are checked for presence and syntax by `profilecheck`. The test-only catalog stays in its current format, because it exists only for language tests.

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Catalog format | (a) the block format above; (b) extend the one-line format with more `\|` fields | (a). It is readable, has room for prose, and diffs cleanly |
| D2 | How the platform types are supplied | (a) a CardLang source file, `platform/base-types.card`, implicitly added to every build for the profile. The types are then *predeclared* names (NAM-14 item 4); (b) declarations embedded in the catalog | (a). The compiler checks them with ordinary rules, and they are readable as code |
| D3 | `CardError` codes | (a) the profile fixes numeric codes for its members, so hosts and tests can rely on them; (b) the codes stay implementation-defined | (a). The profile is a platform specification, so fixing them is within its remit (OUT-19), and portable host software needs them |
| D4 | Failure behaviour, for every API | (a) On `Err`, no output region is changed, and no resource is created or deleted. When several errors apply, a fixed precedence decides: `NotFound` → `WrongResourceType` → `InvalidState` → `Unsupported` → `Malformed` → `Capacity`. (b) Each API states its own behaviour | (a). It is deterministic (in the spirit of RTF-5), and each API description gets shorter |
| D5 | Minimum resource counts in the profile | (a) the profile states small minimums, for example 8 persistent keys, 4 volatile keys and 2 concurrent operations; (b) no minimums, only `Capacity` errors | (a). Unlike commit size, these are simple counts that a platform can guarantee, and a FIDO2 applet can rely on them |

**Decided 2026-11-17.** You accepted every recommendation:

- **D1 (a):** the block catalog format.
- **D2 (a):** the types are in `platform/base-types.card`, a prelude implicitly part of every build. Its names are predeclared.
- **D3 (a):** the profile fixes the numeric `CardError` codes.
- **D4 (a):** failure behaviour is uniform. On `Err`, nothing changes, and a fixed error precedence applies.
- **D5 (a):** the profile states small minimum resource counts.

## 5. Work steps

1. Write `platform/base-profile.md`, sections 1–6, 9, and the empty family sections.
2. Write `platform/base-types.card`, with the shared enums and structures for this stage.
3. Write `platform/base-catalog.txt`: the header, the format description, and no entries yet.
4. Tools:
   - `pltcheck` can load a catalog in the block format, and can add `base-types.card` to the build;
   - `profilecheck.py` checks the catalog's syntax and that every type it uses is declared, that every `CardError` member it lists exists in the profile's table, and that the precedence order matches;
   - both are added to `run_checks.py`.
5. Tests: `base-types.card` itself compiles under the full checker. A small valid program uses the base types. Declaring a base type name in an application is CE-NAM-5.
6. Update `platform/` cross-references in the base plan, `readme.md` and the tools README.

## 6. Exit checklist

- `platform/` exists with the three files, and the profile states every convention in §2.
- `python -I tools/run_checks.py` passes, including `profilecheck`.
- Nothing in `spec/` contradicts the profile.
