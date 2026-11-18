# WP8 step 0 — Reference reading notes

Date: 2026-11-18. Sources (local, git-ignored): `reference/ctap-spec/` (CTAP 2.1 PS with errata, June 2022) and `reference/FIDO2Applet/` (commit `dfcad19`, MIT). These notes summarize in my own words what WP8 needs. They do not reproduce the specification.

## 1. Findings that affect work already done

| # | Finding | Affects | Proposed fix |
|---|---|---|---|
| R1 | **The canonical key order in WP5 is wrong.** CTAP2's rule (CTAP 2.1 §8) is: the lower major type first, then the shorter key, then bytewise. The specification notes that, for keys of major types 0–3 and 7, this equals a plain **bytewise comparison of the encoded keys**. WP5 implemented RFC 7049's *length-first* rule instead. That order puts the text key `"z"` before the integer key `1000`; CTAP2 puts `1000` first, because its major type is lower. My W2 description ("CTAP2's: the shorter encoded key first") was wrong, and option (b), bytewise, was what CTAP2 actually requires | BP-36, `testcbor.py`, `run-021-cbor`, the WP5 sub-plan | Re-decide W2: bytewise order of the encoded keys |
| R2 | **CTAP2 forbids CBOR tags** in its messages. WP5 (W3) accepts tags structurally | BP-36 | Either the profile rejects tags (`Malformed`), or it keeps accepting them, because the profile is not CTAP-only, and CTAP applications reject them themselves |
| R3 | **SELECT needs an application-defined response.** Selecting the FIDO applet (AID `A0000006472F0001`) must return a version string in the response data. BP-50 says the platform handles SELECT and never passes it to `command`, so the application cannot supply it | BP-50, and the ISO 7816 binding | An optional handler for the ISO 7816 binding, such as `on_select(response: inout u8[]) -> u32`, whose bytes become the SELECT response. PLT-18 already lets a platform define lifecycle handlers |

## 2. The CTAP subset for WP8 (facts, summarized)

**Transport over NFC and ISO 7816** (CTAP 2.1 §11.3):
- A CTAP message is sent with INS `0x10` (NFCCTAP_MSG). Its data is the command byte followed by CBOR parameters.
- The response data is the status byte followed by CBOR, with status word `9000`. A status word of `9100` with INS `0x11` (NFCCTAP_GETRESPONSE) is a keep-alive for long operations. We do not need it, because commands run to completion before responding (BP-48).
- INS `0x12` (NFCCTAP_CONTROL) ends a CTAP session.
- Long messages use ISO 7816 chaining and GET RESPONSE, which the platform handles (BP-49).

**Commands:**

| Command | Code | Parameters used (map key) | Response (map key) |
|---|---|---|---|
| makeCredential | `0x01` | clientDataHash (1), rp (2) with `id`, user (3), pubKeyCredParams (4), excludeList (5), options (7) | fmt (1), authData (2), attStmt (3) |
| getAssertion | `0x02` | rpId (1), clientDataHash (2), allowList (3), options (5) | credential (1), authData (2), signature (3) |
| getInfo | `0x04` | — | versions (1), aaguid (3), options (4), maxMsgSize (5), pinUvAuthProtocols (6), algorithms (10) and others |
| clientPIN | `0x06` | — | — (the second step of WP8) |
| reset | `0x07` | — | — |

**Status bytes used:**

| Code | Name |
|---|---|
| `0x00` | OK |
| `0x01` | invalid command |
| `0x02` | invalid parameter |
| `0x11` | unexpected CBOR type |
| `0x12` | invalid CBOR |
| `0x14` | missing parameter |
| `0x19` | credential excluded |
| `0x26` | unsupported algorithm |
| `0x2B` | unsupported option |
| `0x2C` | invalid option |
| `0x2E` | no credentials |
| `0x7F` | other |

**Canonical CBOR** (CTAP 2.1 §8): shortest integers and lengths, definite lengths only, map keys sorted as in R1, no duplicate keys, no tags (R2). Authenticators must accept messages of at least 1024 bytes, which Base Profile 1 exceeds (1280).

**Versions.** Advertising `FIDO_2_1` makes further features mandatory (CTAP 2.1 §9): hmac-secret, credProtect, and pinUvAuthToken when PIN is supported. **WP8 advertises `FIDO_2_0`.** Whether PIN protocol 2 alone is enough for `FIDO_2_0` hosts is a question for the PIN step.

**authData** is defined in WebAuthn, not CTAP. It is `rpIdHash` (32 bytes), then the flags (1 byte: UP `0x01`, UV `0x04`, AT `0x40`), then `signCount` (4 bytes, big-endian). With AT set, it continues with `aaguid` (16), the credential ID length (2), the credential ID, and the COSE public key.

## 3. FIDO2Applet, for comparison

| Aspect | FIDO2Applet (Java Card) | The CardLang applet (planned) |
|---|---|---|
| Size and shape | About 9,200 lines in 11 files. One class is about 7,300 lines | Several small files: shared logic plus one binding-specific `command` file |
| Scope | Full CTAP 2.1: resident keys, credential management, large blobs, config, PIN | The WP8 core, then PIN |
| Non-resident credentials | The private key is *wrapped* (encrypted) into the credential ID | The private key is *derived* by HMAC, so the credential ID holds only a nonce and a tag |
| Copying | 96 calls to `arrayCopyNonAtomic` | Slice assignment (FUN-24) |
| Transient memory | Explicit `makeTransient` arrays | Locals and `session` state |
| Transactions | 13 explicit `beginTransaction` and commit pairs | `transaction { … }` blocks |
| Chaining | Hand-written response chaining (`setupChainedResponse`) | Done by the platform (BP-49) |
| CBOR | Hand-written parsing, and canned byte arrays for fixed responses | `card.cbor` (BP-34 to BP-40), plus constant byte arrays |
| SELECT | `selectingApplet()` returns the version string itself | Needs R3 |

These are the comparison points for the findings report. They are not measurements of quality: the Java applet does much more.

## 4. Decisions (2026-11-18)

- **R1:** you asked whether bytewise order is still canonical. It is. Any fixed total order on keys gives a canonical form. Bytewise order is RFC 8949's current core deterministic encoding (§4.2.1), and RFC 7049's length-first rule survives only as a legacy variant (RFC 8949 §4.2.3). For the key types CTAP uses, bytewise order is exactly CTAP2's order. **Confirmed: bytewise.** Applied to BP-36 and BP-39, `testcbor.py`, `run-021-cbor` and the WP5 sub-plan.
- **R2:** keep accepting tags. The profile is not CTAP-only, and a CTAP applet rejects tags itself.
- **R3:** an optional `on_select(response: inout u8[]) -> u32` handler for the ISO 7816 binding. Its bytes become the SELECT response data. **Applied** as BP-50a, with the build-time check in `pltcheck`, the `select` scenario step, and tests plt-011, plt-117, plt-118 and run-023.
