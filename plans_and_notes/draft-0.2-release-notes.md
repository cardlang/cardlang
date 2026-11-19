# CardLang Draft 0.2 — Release notes

Date: 2026-11-19. Tag: `spec-draft-0.2`. Previous draft: `spec-draft-0.1` (2026-11-17).

Draft 0.2 is Draft 0.1 corrected and extended by its first real use: a FIDO2 authenticator (CTAP 2.0, with PIN protocols two and one), written in CardLang and checked independently. It adds the first platform profile, the CardLang Base Profile 1. Every rule is still [Agreed], and every open issue is resolved.

| | Draft 0.1 | Draft 0.2 |
|---|---|---|
| Rules | 287 | 305 |
| Open issues, all resolved | 44 | 59 |
| Conformance tests (valid / invalid / runtime) | 102 / 231 / 17 | 122 / 257 / 26 |
| Platform profile | — | Base Profile 1: 58 rules (BP-1 to BP-56, plus BP-50a and BP-53a), 34 catalog APIs |
| Example applications | Counter, wallet, signer skeleton | Plus a FIDO2 authenticator (`examples/fido2`, 778 lines) |
| `tools/run_checks.py` runs | 22 | 24 |

## 1. Language changes

Each is recorded in Annex C (open issue) and the decision register (decision).

| OI / D | Change | Rules |
|---|---|---|
| OI-45 / D-445 | Inside a transaction, the error path of `attempt` and `require` aborts the transaction | TXN-18; TXN-6, STM-19, OUT-10, EXP-51 |
| OI-46 / D-446 | What is an intrinsic, and what is a platform API | EXP-52, PLT-30 |
| OI-47 / D-447 | Slice assignment `p[s..e] = x;`, atomic into persistent storage | FUN-24; FUN-18, STM-7; CE-STM-8 |
| OI-48 / D-448 | The intrinsics `equal` (constant-time) and `compare` | EXP-53, EXP-54 |
| OI-49 / D-449 | The `wipe` statement, whose stores are never removed | STM-23; EXP-22 |
| OI-50 / D-450 | Security expectations for platforms | PLT-31 to PLT-34 (Annex B §B.13) |
| OI-51 / D-451 | The capacity model was withdrawn. A destination whose size is known only at runtime traps if it exceeds the atomic capacity | STA-13, FUN-24, STM-23, RTF-4 |
| OI-52 / D-452 | Derived secrets are application data. PLT-33 covers the material held in key resources | PLT-33 |
| OI-53 / D-453 | Byte-string literals `b"…"` | LEX-25, EXP-55; CE-LEX-5 |
| OI-54 / D-454 | The pattern `Err(Set(code))`, which binds an application error's code | OUT-21 |
| OI-55 / D-455 | `attempt c else M` | OUT-22, TXN-18 |
| OI-56 / D-456 | `ignore c;` | STM-24 (the keyword `ignore`) |
| OI-57 / D-457 | Compound assignment, with ten operators | STM-25, LEX-22, STM-6 |
| OI-58 / D-458 | A frame's locals are erased when the frame ends, traps included | PLT-35, STM-23 |
| OI-59 / D-459 | Sessions are defined by the transport binding. The handler `on_power_on` is renamed `on_session_start` | STA-4, STA-6, RTF-9, PLT-18, PLT-19 |

**Compatibility with Draft 0.1:**
- `ignore` is a new keyword, so a Draft 0.1 program that uses it as a name no longer compiles.
- `+=` and the other compound operators are now tokens, so `x += 1` is now valid; it was CE-SYN-1.
- An `attempt` or `require` inside a transaction is now valid; it was CE-TXN-1.
- `on_power_on` must be renamed `on_session_start`.

Every change except OI-50, OI-52 and OI-58 (platform obligations) is compiler-only: it is rewritten into existing constructs, and adds nothing to the VM.

## 2. The CardLang Base Profile 1 (`platform/`)

A platform specification, separate from the language specification:

- **§1–§6:** conformance and versioning; API conventions (failure changes nothing, a fixed error precedence, errors rather than traps); platform types in `base-types.card`; `CardError` with fixed codes; resource kinds, lifetimes and minimum capacities; the block catalog format.
- **§7 Keys:** `KeyType`, persistent, volatile and command-lifetime keys, `generate`, `import`, `export_public` and `delete`. Persistent key changes take part in transactions.
- **§8 Crypto:** SHA-256, HMAC-SHA-256, ES256, ECDH, HKDF and AES-CBC, one-shot and multi-part, and `card.random.fill`.
- **§9 CBOR:** a stateless, strict canonical reader with bytewise key order, and a writer (`write_head`, `write_int`, `write_string`, `write_bool`).
- **§10 TLV:** a BER-TLV reader and a DER writer, including DER ECDSA signatures.
- **§11 Transport bindings:**
  - ISO 7816: request layout, status words, the `on_select` handler;
  - raw: the response envelope, and session control;
  - session events per binding.

## 3. The FIDO2 check

`examples/fido2` implements `getInfo`, `makeCredential` (ES256, non-resident derived credentials, `"none"` attestation), `getAssertion`, `reset` and `clientPIN` (protocols two and one). `tools/fido/check_fido2.py` runs 59 checks against an independent platform-side implementation.

The findings that shaped this draft are in `plans_and_notes/WP8-fido2-findings.md`. The applet's size went from 552 to 449 lines through the language changes, then grew to 778 with the PIN protocol.

## 4. Tools

- **The reference checkers and interpreter** support every change.
- **New:**
  - `profilecheck.py`, which checks the Base Profile;
  - the test-only crypto (`p256.py`, `testcrypto.py`), CBOR (`testcbor.py`) and TLV (`testtlv.py`) implementations, self-tested against published vectors;
  - the scenario forms `select`, `seed`, `session_start`, `session_end`, `expect sw` and `expect raw`.
- **`speccheck.py`** now also checks the reverse traceability and the rule tables of every compile-error class.

## 5. Carried over to Draft 0.3

From `plans_and_notes/draft-0.2-candidates.md`:

- **2:** relaxing EXP-49. Weak evidence so far.
- **4:** a user-presence API.
- **7:** several error sets.
- **16:** `fill` in constant initializers, to be checked first.
- **17:** export of key material encrypted under another key.
- **Resident credentials** in the FIDO2 applet.

Still outside this specification: a real platform implementation and API catalog, a compiler, and a VM.
