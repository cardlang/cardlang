# WP8 step 2 — The FIDO2 PIN protocol: detailed sub-plan

Parent: `plans_and_notes/spec-plans/WP8-fido2.md` (F1: the core first, then the PIN protocol).
Status: decisions D1–D3 taken 2026-11-19 (§5). Ready to draft.

## 1. Purpose

Add `authenticatorClientPIN` and PIN-based user verification to `examples/fido2`. The goal is still the same: exercise CardLang and Base Profile 1 on a real protocol, and record what hurts. The PIN protocol is the first flow that combines everything at once:
- ECDH and HKDF (BP-29);
- AES-CBC with a random IV, and HMAC;
- key material that lives for one command (P1: `Command` keys) or for a power cycle (`Volatile` keys, session state);
- persistent counters that must survive tearing (STA-11);
- `wipe` and frame erasure (PLT-35).

This step changes neither the specification nor the profile. New findings go to the findings report, as before.

## 2. The protocol, summarized (CTAP 2.1 §6.5)

- **Key agreement.** The authenticator has a P-256 key-agreement key pair, regenerated at power-on. `getKeyAgreement` returns its public key as a COSE key. The platform sends its own public key with each request, and both sides derive a shared secret from the ECDH x-coordinate `Z`:

  | | Protocol one | Protocol two |
  |---|---|---|
  | Shared secret | `SHA-256(Z)`, 32 bytes | `HKDF(Z, "CTAP2 HMAC key") ‖ HKDF(Z, "CTAP2 AES key")`, 64 bytes |
  | Encryption | AES-256-CBC, zero IV | AES-256-CBC, random IV prepended |
  | Authentication | The first 16 bytes of HMAC-SHA-256 | All 32 bytes of HMAC-SHA-256 |

- **`setPIN`.** The platform sends `newPinEnc`, the PIN padded to 64 bytes and encrypted, and `pinUvAuthParam`, its HMAC. The authenticator verifies, decrypts, checks the PIN length (4 to 63 bytes), and stores `LEFT(SHA-256(PIN), 16)`.
- **Getting a token.** The platform sends `pinHashEnc`, the encrypted `LEFT(SHA-256(PIN), 16)`.
  - The authenticator first **decrements the retries counter**, then compares.
  - On a match, it resets the counter, and returns the `pinUvAuthToken` (32 random bytes, regenerated at power-on), encrypted.
  - Three consecutive mismatches require a power cycle (`PIN_AUTH_BLOCKED`). A counter of 0 means `PIN_BLOCKED` until `reset`.
- **Using the token.** `makeCredential` and `getAssertion` carry `pinUvAuthParam = authenticate(token, clientDataHash)`. When it verifies, the UV flag (`0x04`) is set in authData.

## 3. Design

### 3.1 State

| State | Kind | Why |
|---|---|---|
| `pin_hash: u8[16]`, `pin_set: bool` | `persistent` | The stored PIN hash |
| `pin_retries: u8` (8 when set) | `persistent` | Survives power loss. It is decremented *before* comparing, as one atomic assignment (STA-11), so pulling the card cannot save an attempt |
| `pin_failures: u8` | `session` | Consecutive mismatches since power-on. At 3, `PIN_AUTH_BLOCKED` until the next power-on |
| Key-agreement key `KA_KEY` | `Volatile` `EcP256Private` | Generated in `on_power_on`, and after 3 mismatches. Ends at power-off |
| `token: u8[32]` and `TOKEN_KEY` | `session` bytes, and a `Volatile` `Hmac256` key | The bytes are encrypted to the platform (the byte model, WP4 C1). The key verifies `pinUvAuthParam`. Both are regenerated in `on_power_on` |
| The shared secret's HMAC and AES keys | `Command` keys (P1) | Derived in each `clientPIN` command, and gone when it ends, even on a trap |

### 3.2 Subcommands (D2)

`getPINRetries` (0x01), `getKeyAgreement` (0x02), `setPIN` (0x03), `changePIN` (0x04) and `getPinToken` (0x05). `getPinToken` is CTAP 2.0's command. CTAP 2.1's `getPinUvAuthTokenUsingPinWithPermissions` (0x09) is left out, because the applet advertises `FIDO_2_0`. That decision is D1.

### 3.3 `getInfo` becomes dynamic

The `clientPin` option must be `false` before a PIN is set, and `true` after. `pinUvAuthProtocols` lists the supported protocols. The fixed `GET_INFO` constant is therefore replaced by a builder that uses `card.cbor.write_*`. That is itself a test of the writer APIs.

### 3.4 Errors

The new statuses are `0x31` PIN invalid, `0x32` PIN blocked, `0x33` PIN auth invalid, `0x34` PIN auth blocked, `0x35` PIN not set, `0x36` PIN or UV token required, and `0x02` invalid parameter. They become `IsoError.Ctap*` members, translated by the existing `Err(IsoError(code))` arm.

## 4. Checking

`check_fido2.py` gains an independent **host-side PIN implementation**, written with `hashlib`, `hmac`, `p256.py` and `testcrypto.py`'s AES and ECDH, but none of the applet's code. It:
- performs key agreement with the authenticator's COSE key, then `setPIN`, then `getPinToken`, and decrypts the token;
- computes `pinUvAuthParam`, and checks that `makeCredential` and `getAssertion` set the UV flag and still verify;
- checks a wrong `pinUvAuthParam` (`0x33`), a wrong PIN with the retries decreasing, three mismatches (`0x34` until power-on), and the block at 0 (`0x32`);
- checks that `reset` clears the PIN, that `clientPin` in `getInfo` follows the state, and `setPIN` when a PIN is already set (`0x33`);
- runs everything for both protocols, if D1 includes protocol one.

## 5. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Protocols and version | (a) protocols two and one, listed as `[2, 1]`, with `FIDO_2_0` and `getPinToken`; (b) protocol two only; (c) advertise `FIDO_2_1` too, which makes hmac-secret, credProtect and `0x09` mandatory | (a). `FIDO_2_0` platforms may only speak protocol one, and supporting both costs little: the KDF, the IV and the tag length differ |
| D2 | Subcommands | (a) `getPINRetries`, `getKeyAgreement`, `setPIN`, `changePIN` and `getPinToken`; (b) the same without `changePIN` | (a). `changePIN` reuses the same pieces |
| D3 | `makeCredential` when a PIN is set but no `pinUvAuthParam` is sent | (a) `0x36`, a token is required, the CTAP 2.0 behaviour; (b) allow it without UV | (a) |

**Decisions (2026-11-19):**

- **D1 (a), decided:** protocols two and one (`[2, 1]`), with `FIDO_2_0` and `getPinToken`. Caveat: CTAP 2.0 defined only protocol one, so this is a 2.0 authenticator with one 2.1 feature. The rule that the list must include 2 (CTAP 2.1 §9) applies only to authenticators claiming `FIDO_2_1`.
- **D3:** checked against CTAP 2.1 §6.1.2. When the authenticator is protected by user verification and does not advertise `makeCredUvNotRqd`, a `makeCredential` without `pinUvAuthParam` and without `uv` ends with `CTAP2_ERR_PUAT_REQUIRED` (`0x36`, called `PIN_REQUIRED` in 2.0). Option (a) is the spec's behaviour. `getAssertion` without a token stays allowed, with the UV flag clear. **Confirmed (a).**
- **D2:** the spec lists changing the PIN among `authenticatorClientPIN`'s purposes, but the text has no explicit "MUST implement changePIN". Including it is the safe choice. **Confirmed (a): `changePIN` is included.**
