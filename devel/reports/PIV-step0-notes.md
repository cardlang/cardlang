# PIV step 0 — Reference reading notes

Date: 2026-11-20. Sources, in the git-ignored `reference/piv/`:
- NIST SP 800-73-5 Part 1 (*Namespace, Data Model, and Representation*) and Part 2 (*Card Command Interface*), July 2024;
- NIST SP 800-78-5 (*Cryptographic Algorithms and Key Sizes*).

Part 3, the middleware client API, is not needed for an applet. These notes summarise the specification; they do not reproduce it.

**Why PIV.** It is the second applet, chosen to broaden the measurement corpus beyond FIDO2. It is TLV-heavy, has large persistent objects and PIN state machines, and uses P-256 and AES.

## 1. Findings against the profile and the language

Each is a candidate for the Draft 0.3 list. A decision is needed before or while the applet is written.

| # | Finding | Kind | Detail |
|---|---|---|---|
| **P1** | **There is no signature over a given digest** | Profile | PIV signs with key `9C` (also `9A`, `9E`) through GENERAL AUTHENTICATE, and *the data to be signed is hashed off-card*: the card receives a 32-byte hash. `card.crypto.sign` (BP-29) hashes the message itself, so it would sign `SHA-256(hash)`. The profile needs an operation that signs a digest. The multi-part sign is no help, because it also hashes |
| **P2** | **Deselection is invisible to applications** | Profile | The security status of the PIN, the PUK and the administration key is *application security status*. It must become FALSE when another application is selected (Part 2 §2.4.2, §3.1.1). BP-55 says deselection is not visible to applications, and session state survives it. So a PIV applet cannot meet the rule, unless the platform resets its session state on deselection, or tells it |
| **P3** | **The interface (contact or contactless) is not visible** | Profile | PIV's access rules depend on it. Several commands must return `6A81` over contactless (Part 2, Table 2). Reading most certificates over contactless requires the virtual contact interface. The profile has no API that tells an application which interface is in use. Part 2 §2.1 lists this as a platform requirement |
| **P4** | **1280 bytes is too small for a PIV certificate** | Profile | An X.509 certificate container holds up to 1,856 bytes of certificate, plus `53` and `70`–`71`–`FE` TLV overhead. So PUT DATA sends about 1.9 KB, and GET DATA returns as much. BP-48 guarantees only 1,280 bytes for requests and responses. Fingerprints go up to 4,000 bytes, and the facial image more |
| **P5** | **The atomic capacity has no profile minimum** | Profile | A PUT DATA of a certificate is one persistent assignment of about 1.9 KB (STA-11). The profile states no minimum atomic capacity, so whether an applet like this one loads is platform-dependent (STA-13). This may be fine as it is, but the profile should say what a PIV-class platform needs |
| **L1** | **Status words that carry a count** | Language | VERIFY, CHANGE REFERENCE DATA and RESET RETRY COUNTER report `63CX`, where X is the number of retries left. Application error codes are fixed members of one error set (OUT-16). Returning `63CX` therefore needs 16 members (`63C0` to `63CF`) and a `match` or table to choose one. This works, but it is clumsy. The same holds for the `61xx` of chaining, although the platform produces that one (BP-49) |
| **L2** | **The PIN usage and the security status are per selection** | Language | This follows from P2. If deselection resets application state, CardLang has no storage class for it: `session` outlives deselection. Possible answers: a profile rule (the platform resets session state on deselection, per application or by binding); a third storage class; or an event handler `on_deselect` |

**What fits without change:**
- **ECDH** returns the x-coordinate of the shared point, exactly as `card.crypto.agree` does (A.5.2).
- **P-256 keys** are generated on the card (GENERATE ASYMMETRIC KEY PAIR, algorithm `11`), with the public point returned as `04 ‖ X ‖ Y` (65 bytes), as `card.key.export_public` writes it.
- **The administration key** uses AES-128/192/256 in ECB on one 16-byte block. That is `card.crypto.encrypt` and `decrypt` (AES-CBC) with a zero IV, an application-level use of an existing API, not cryptography in the VM. 3DES (`00`, `03`) is deprecated by SP 800-78-5 and is left out.
- **ECDSA signatures** are returned DER-encoded (`Ecdsa-Sig-Value`), which `card.der.write_integer` and `card.der.write_head` produce from `r ‖ s`, as the FIDO2 applet already does.
- **Random challenges and witnesses** (16 bytes) come from `card.random.fill`. The PIN comparison uses `equal`, which is constant-time (PLT-31).
- **Chaining** (CLA `10`) and `61xx` with GET RESPONSE are the platform's (BP-48, BP-49). An interrupted GENERAL AUTHENTICATE chain must have no effect. That holds if the platform passes only whole chains to `command`.
- **SELECT** is the platform's: the full or right-truncated AID, and the default application (BP-50). The response, the application property template, comes from `on_select` (BP-50a).
- **Persistent keys:** five slots (`9A`, `9B`, `9C`, `9D`, `9E`) are within BP-16's minimum of 8. The 20 retired key-management slots (`82`–`95`) are not.

## 2. The PIV subset for the applet (facts, summarised)

**The application.**
- **The AID** is `A0 00 00 03 08 00 00 10 00 01 00`, which may be selected right-truncated as `A0 00 00 03 08 00 00 10 00`.
- **The SELECT response** is the application property template, tag `61`. It contains `4F` (the full AID) and `79` (the coexistent tag allocation authority, containing `4F`), optionally `50` (a label), and `AC` (the algorithms, each as `80` plus `06 00`).

**The commands** (Part 2, Table 2):

| Command | INS | Security condition | Notes |
|---|---|---|---|
| GET DATA | `CB` (P1P2 `3FFF`) | Per object (Part 1, Table 2) | Data `5C` with the object's tag. The response is `53` and the content, or the bare `7E` for the Discovery Object. `6A82` if absent, `6982` if not allowed |
| VERIFY | `20` | Always | P2 `80` is the PIV PIN (`00` is the global PIN, optional). The PIN is 6 to 8 ASCII digits padded with `FF` to 8 bytes. With empty data it returns the retries (`63CX`) or `9000` if already verified. P1 `FF` resets the status. `6983` when blocked. The retry counter is at most 10 |
| CHANGE REFERENCE DATA | `24` | PIN or PUK | P2 `80` or `81` (PUK). Data is the old value followed by the new one, 16 bytes |
| RESET RETRY COUNTER | `2C` | PUK | P2 `80`. Data is the PUK followed by the new PIN, 16 bytes. The PUK is any 8 bytes |
| GENERAL AUTHENTICATE | `87` | Per key | P1 is the algorithm (`11` for P-256, `08`/`0A`/`0C` for AES), P2 the key. Data is template `7C` with `80` (witness), `81` (challenge), `82` (response) and `85` (exponentiation, ECDH). Empty tags request a value. Signing: `7C {82 00, 81 hash}` returns `7C {82 DER(r,s)}`. ECDH: `7C {82 00, 85 point}` returns `7C {82 Z}`. Administration: `7C {81 00}` returns a challenge, then `7C {82 E(challenge)}`; mutual authentication uses `80` and `81` together |
| PUT DATA | `DB` (P1P2 `3FFF`) | Administration key | Data `5C` with the tag, then `53` with the content, or the bare `7E`. `6A84` if there is not enough memory |
| GENERATE ASYMMETRIC KEY PAIR | `47` | Administration key | P2 the key (`9A`, `9C`, `9D`, `9E`). Data `AC {80 11}`. Response `7F49 {86 04‖X‖Y}` |

**The keys** (Part 1, Table 5):

| Key | Role | Use over contact |
|---|---|---|
| `9A` | PIV authentication | PIN |
| `9B` | Card application administration (AES) | Always, but only to authenticate the administrator |
| `9C` | Digital signature | PIN *Always*: the PIN must be verified immediately before each signature |
| `9D` | Key management (ECDH) | PIN |
| `9E` | Card authentication | Always |

**The data objects** for the subset. Each is a `53`-wrapped TLV structure (Part 1, Tables 2, 3, 9 to 11):

| Object | Tag | Read rule (contact) | Contents |
|---|---|---|---|
| Card Capability Container | `5FC107` | Always | Mandatory |
| CHUID | `5FC102` | Always | FASC-N `30`, GUID `34`, expiration date `35`, signature `3E`, EDC `FE`. Mandatory |
| PIV authentication certificate (`9A`) | `5FC105` | Always | `70` (certificate, at most 1,856 bytes), `71` (CertInfo), `FE` (EDC) |
| Digital signature certificate (`9C`) | `5FC10A` | Always | As above |
| Key management certificate (`9D`) | `5FC10B` | Always | As above |
| Card authentication certificate (`9E`) | `5FC101` | Always | As above |
| Discovery Object | `7E` | Always | `4F` (AID) and `5F2F` (PIN usage policy) |
| Security Object, fingerprints, facial image | `5FC106`, `5FC103`, `5FC108` | Always / PIN / PIN | Mandatory for a real card. In the applet they are storable objects with their read rules, with no further semantics |

**Left out of the subset:**
- secure messaging and the virtual contact interface (Part 2 §4);
- on-card biometric comparison (OCC);
- the pairing code;
- the global PIN;
- retired keys;
- RSA and P-384.

None of them is needed for a contact-interface card that OpenSC can use.

## 3. Real-world testing (later)

- **OpenSC** (`opensc-tool`, `pkcs11-tool`, `piv-tool`) speaks standard PIV:
  - `pkcs11-tool --sign` covers SELECT, GET DATA, VERIFY and GENERAL AUTHENTICATE;
  - `piv-tool -A A:9B:08 -G 9A:11` covers administrator authentication with AES-128 and key generation, and loads certificates with PUT DATA.
- **`yubico-piv-tool` uses YubiKey-specific instructions** for some operations, such as GET VERSION, SET MANAGEMENT KEY and metadata. A standard applet will not support those, so OpenSC is the first target.
- **Smartcard login** on Windows or macOS is a later end-to-end check. It needs a certificate chain the host trusts.

## 4. Decisions

Decided 2026-11-20: Q1 to Q5, all as recommended. Q4 is option (a): the profile minimums stay, and a PIV build states its needs.

**A follow-up, from the user.** Think later about a Java Card-like API for receiving and sending message data in chunks inside applets. Then large objects need not fit a whole-message buffer. This is candidate 18 in `draft-0.2-candidates.md`. The PIV findings P1 to P3 and L1 are recorded there too, as candidates 19 to 22.

**The 1.9 KB figure (Q4).** Part 1, Table 11 gives the largest values: the certificate `70` at 1,856 bytes, CertInfo `71` at 1 byte, and the EDC `FE` at 0 bytes. With the TLV headers, the container holds 1,865 bytes. The GET DATA response (`53` and the container) is then 1,869 bytes, and the PUT DATA request (`5C 03 5F C1 05` followed by that) 1,874 bytes.
- **1,856 is not a limit.** It is the recommended length; the footnote says a certificate can exceed it.
- **For P-256 it is pessimistic.** P-256 certificates are typically 500 to 900 bytes (an estimate, not a figure from the specification). They would usually fit the profile's 1,280-byte minimum, without a guarantee.

| ID | Question | Recommendation |
|---|---|---|
| Q1 | P1: signing a digest | Add `card.crypto.sign_digest(key, alg, ref digest, inout signature) -> u32` (and a matching `verify_digest`) to the profile. That needs a new native number, appended to the catalog (BC-32). It is a profile change, and the signing remains the HAL's (HAL-1) |
| Q2 | P2 and L2: deselection | A profile rule for the ISO 7816 binding: deselecting the application ends its session (STA-4, BP-56), so session state, volatile keys and session operations are reset, and `on_session_start` runs at the next SELECT. That is exactly PIV's application security status, with no language change. The alternative is an `on_deselect` handler |
| Q3 | P3: the interface | Defer it. The subset is contact-only, and a contactless rule can be added later, as a platform query (for example `card.platform.interface()`) |
| Q4 | P4 and P5: sizes | Keep the profile's minimums. A PIV build states its needs (about 2 KB of request and response, and an atomic capacity of about 2 KB), and IMG-11-style load checks reject a platform that lacks them. Record it in the profile as a note for PIV-class applications |
| Q5 | L1: `63CX` | Accept the 16 members for now, and record the finding. If a second applet hits the same need, consider a language change (an error code with a runtime part) for Draft 0.3 |
