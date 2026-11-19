# WP8 — The FIDO2 check: detailed sub-plan

Parent: `plans_and_notes/base-api-plan.md` §7 (WP8: "everything that hurts is recorded as input to the language").
Status: F1–F4 decided 2026-11-18 (§4). **The core was drafted 2026-11-19:** `examples/fido2/` and `tools/fido/check_fido2.py` (21 checks), with the findings in `plans_and_notes/WP8-fido2-findings.md`. The PIN protocol is next.

## 1. Purpose

WP8 is the first realistic program in CardLang. It writes the core of a CTAP2 authenticator against the reference interpreter. That tests the Draft 0.1 language and Base Profile 1 together, on the kind of application they are meant for. Its main outputs are:

1. **A working applet**, in `examples/fido2/`, which runs in the interpreter and passes an independent check of its responses (F4).
2. **A findings report**, `plans_and_notes/WP8-fido2-findings.md`. It records everything that was awkward to write, missing, ambiguous, or wrong in the language, the profile or the tools, with a proposed change for each. Those findings feed the Draft 0.2 candidate list.

WP8 changes neither the specification nor the profile. Defects it finds are fixed afterwards, through the normal open-issue process.

## 2. The applet

### 2.1 Transport

The applet uses the ISO 7816 binding (BP-49 to BP-52), as CTAP2 over NFC does:

- a CTAP message arrives as `CLA 80`, `INS 10`, `P1 00`, `P2 00`, with the data field holding the CTAP command byte followed by its CBOR parameters;
- the response data is the CTAP status byte followed by the CBOR response, with status word `9000`;
- the platform does SELECT, chaining and GET RESPONSE.

The files follow the pattern noted in the WP7 review. Shared logic goes in files that do not depend on the binding, and `iso7816-entry.card` holds the `command` that dispatches on `INS`. A raw-binding entry file could be added without touching the logic.

### 2.2 Scope (F1)

| CTAP command | Included | Notes |
|---|---|---|
| `authenticatorGetInfo` (0x04) | Yes | Fixed CBOR response: versions, the AAGUID, options and the algorithms (`-7`) |
| `authenticatorMakeCredential` (0x01) | Yes | ES256 only, and non-resident credentials (F2). Attestation per F3 |
| `authenticatorGetAssertion` (0x02) | Yes | One credential from `allowList`. A DER signature over `authData ‖ clientDataHash` (BP-45) |
| `authenticatorReset` (0x07) | Yes | Replaces the master secrets and resets the counter |
| `authenticatorClientPIN` (0x06), protocol 2 | F1 | `getKeyAgreement`, `setPIN` and `getPinUvAuthToken`, using ECDH, HKDF, AES-CBC and HMAC |
| Resident credentials, credential management, extensions | No | Later |

### 2.3 Credentials (F2)

**Recommendation: non-resident credentials with derived keys**, which is the byte model (WP4 C1):

- **Credential ID:** `nonce (32 random bytes) ‖ tag (16 bytes)`, where `tag` is the first 16 bytes of `HMAC(macKey, rpIdHash ‖ nonce)`.
- **The private key:** `d = HMAC(keyKey, rpIdHash ‖ nonce)`. It is imported as a volatile `EcP256Private` key when needed, then deleted, and the bytes are erased with `wipe`. A `Malformed` import (`d` = 0 or `d ≥ n`, with a probability of about 2^-32) is reported as a CTAP error.
- **Persistent state:** `macKey` and `keyKey` are persistent `Hmac256` keys, created in `on_install`. The signature counter is a persistent `u32`, incremented in a transaction with each assertion.

### 2.4 Attestation (F3)

**Recommendation: `"none"` attestation** (an empty `attStmt`). Packed attestation needs a provisioned certificate and key, which this check does not need in order to exercise the language. DER signatures are still exercised by every assertion.

## 3. How the applet is checked (F4)

Signatures and random values are deterministic in the interpreter (RFC 6979, and the K4 random generator), but expected bytes computed by running the applet would be circular. **Recommendation:** an independent checker, `tools/fido/check_fido2.py`:

- it runs a scripted CTAP session through the interpreter, and captures every response;
- it checks each one with its own Python code, using `hashlib`, `hmac` and `p256.py`, but none of the applet's logic. The checks are:
  - every response is canonical CBOR with the fields CTAP requires;
  - `rpIdHash` is `SHA-256(rpId)`;
  - the flags are correct;
  - the counter increases;
  - the credential public key from `makeCredential` verifies the DER signature from `getAssertion`;
  - a credential ID for another RP is rejected;
  - the PIN protocol messages decrypt and verify correctly (if F1 includes PIN);
- it is added to `run_checks.py`.

Ordinary scenario tests (`run-024`…) cover the fixed parts: `getInfo` exact bytes, error status bytes and status words.

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| F1 | Scope | (a) `getInfo`, `makeCredential`, `getAssertion` and `reset`, with `clientPIN` protocol 2 as a second step in the same work package; (b) the same without the PIN protocol; (c) everything at once | (a). The core first, so the findings start early; PIN after it, because it exercises ECDH, HKDF, AES and `wipe` |
| F2 | Credentials | (a) non-resident, with derived keys (§2.3); (b) resident, as persistent keys and records | (a). It needs no storage and uses the byte model. Resident keys would exercise persistent arrays of structures and their transactions, so they are a good follow-up |
| F3 | Attestation | (a) `"none"`; (b) packed self-attestation, signed with the credential key | (a). (b) is easy to add later |
| F4 | Verification | (a) an independent Python checker of the captured responses; (b) scenario tests with exact expected bytes only | (a) |

**Decisions so far (2026-11-18):**

- **F1 (a):** the core first, then `clientPIN` protocol 2.
- **F3 (a):** `"none"` attestation. WebAuthn's default attestation preference is `"none"`, and clients may then replace the statement with `"none"` themselves, so webauthn.io and most relying parties accept it. Packed attestation can come later.
- **F4 (a):** an independent checker.
- **F2 (a), confirmed:** non-resident credentials first. They work on webauthn.io with "discoverable credential: discouraged". Resident credentials (passkeys) are the follow-up, and exercise persistent arrays of structures.

**Added: step 0, reference reading.** Before drafting, read the CTAP 2.1 specification (fidoalliance.org) to confirm the exact message formats, and use it to check details, not as text to copy. Read the open-source Java Card applet BryanJacobs/FIDO2Applet as a comparison target, after checking its license. The findings report gets a comparison section: structure, size, and the workarounds Java Card needs that CardLang does not, or the reverse.

**Reference material (downloaded 2026-11-18, git-ignored, in `reference/`):**

- `reference/ctap-spec/fido-client-to-authenticator-protocol-v2.1-ps-errata-20220621.html`: CTAP 2.1 Proposed Standard with errata, from fidoalliance.org.
- `reference/FIDO2Applet/`: a shallow clone of github.com/BryanJacobs/FIDO2Applet (commit `dfcad19`), MIT License, about 9,200 lines of Java in 11 files.

Neither is committed, and nothing from them is run. The MIT license allows reuse with attribution, but WP8 uses the applet only as a comparison target.

**Later, outside WP8:** running against a real relying party such as webauthn.io needs a real platform, or a bridge from the interpreter to a virtual reader or HID device. The applet must not depend on anything that would prevent that.

## 5. Exit checklist

- `examples/fido2/` runs in the interpreter, and `check_fido2.py` passes. Both are part of `run_checks.py`.
- `WP8-fido2-findings.md` lists every finding, with its category (language, profile or tools) and a proposed change.
- `draft-0.2-candidates.md` item 5 points to the findings.
