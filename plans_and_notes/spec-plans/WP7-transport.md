# WP7 — Transport and environment: detailed sub-plan

Parent: `plans_and_notes/base-api-plan.md` §5 (chaining, long responses, user presence, lifecycle).
Status: decisions E1–E4 taken 2026-11-18 (§3); E1 revised into transport bindings. **Drafted 2026-11-18.** Handler-failure behaviour (BP-55) is specified but not exercised by a runtime test.

## 1. Scope

WP7 fills in profile §11. It answers, for the Base Profile, the transport and lifecycle items that the language leaves to platforms (Annex B §B.12):

- which bytes form the request (HEP-5);
- the response capacity (HEP-6);
- how outcomes reach the host (HEP-12, PLT-9);
- when the lifecycle handlers run (STA-6, PLT-18).

It also adds the one environment query a FIDO2 authenticator needs. The target is ISO/IEC 7816-4 APDUs over contact or contactless (NFC) interfaces, which is how CTAP2 reaches a smart card.

## 2. Design

### 2.1 Reassembly and long responses (E1)

**Recommendation: the platform reassembles,** so a `command` always sees one whole message:

- **Command chaining.** A command chained with CLA bit `0x10` (ISO 7816-4 §5.1.1.1) is collected by the platform until the last part arrives. The application's `command` then runs once, on the whole request.
- **Extended length.** Extended-length APDUs are accepted where the interface supports them.
- **Long responses.** A response longer than the short-APDU limit is returned with `61xx` and GET RESPONSE, or with extended length, as the host negotiates. The application just returns `Ok(count)`.
- **Minimum sizes.** A platform claiming the profile supports a request of at least 1280 bytes and a response capacity of at least 1280 bytes. CTAP2's default maximum message size is 1024 bytes, and some extensions need more.

The alternative is that the application sees every APDU and handles chaining itself. That pushes transport logic into every application, against the layer separation of chapter 1 §1.2.

### 2.2 What the request contains (E2)

**Recommendation: the request is the reassembled command APDU, without its length fields:**

```text
request[0]  CLA (with the chaining bit cleared)
request[1]  INS
request[2]  P1
request[3]  P2
request[4..request.length]   the data field, reassembled
```

The application dispatches on `INS` and `P1`/`P2`, as card applications traditionally do. The platform handles `SELECT` of the application itself, and never passes it to `command`. Le is not passed on: the response capacity (`response.length`) already says how much the application may produce.

### 2.3 Status words (E3)

The language requires only that the four outcome categories stay distinguishable (PLT-9). **Recommendation: the profile fixes the mapping**, so an application can produce the status words that card protocols require:

| Outcome | Status word |
|---|---|
| `Ok(count)` | `9000`, with the `count` response bytes. A long response is served with `61xx` as described in §2.1 |
| `Err` of an application error with code `c` | `c` itself. An application error code must therefore be a valid ISO status word in `6200`–`6EFF`, or in `9100`–`9FFF` except `9000` |
| `Err(CardError.m)` | `6F00 + code(m)`, for example `6F10` for `NotFound` (§4 codes are below `0x100`) |
| A trap | `6F00` |

- **Distinguishability.** The ranges are disjoint, so the categories are always distinguishable, as PLT-9 requires.
- **Build-time check.** An application error code outside the permitted ranges is rejected when building for the profile. This is a profile check, like CE-NAM-5 for base types, and the checker implements it.
- **Effect on FIDO2.** CTAP status codes travel inside the response data with `9000`, so FIDO2 uses `Ok` for CTAP-level errors, and the application's error set is for ISO-level failures such as an unknown `INS` (`6D00`).

The alternative (b) leaves the mapping implementation-defined, as it is today. Applications could then not produce the specific status words protocols require.

### 2.4 User presence (E4)

CTAP requires a test of user presence. On NFC, the act of presenting the card is the user-presence test. A contact interface has no button.

**Recommendation:** one environment query, `card.env.interface() -> Interface`, with `enum Interface { Contact; Contactless; }`. The application decides; for example, it requires `Contactless` for operations that need user presence. A platform with a real presence button can add an API later, in a new version.

### 2.5 Lifecycle

These confirm and complete the language placeholders (D-438, STA-6, PLT-18):

- **`on_install()`** runs once, when the application is installed, before any command.
- **`on_power_on()`** runs at every power-on, after session state and volatile keys are reset, before the first command.
- **A handler that traps or returns `Err`.** For `on_install`, installation fails, and the application is not installed. For `on_power_on`, the application stays unavailable until the next power-on: every command gets the trap status word `6F00`.
- **Deselection** and logical channels are not visible to the application in this version. Session state survives deselection until power-off or a security reset.

### 2.6 Interpreter and tests

- **Scenario format.** It stays at message level: a `command` line is the reassembled request. Only the status-word mapping is new: an `expect sw 6A80` form, alongside the existing `expect` forms, is computed from the outcome by the §2.3 table.
- **The status-word check.** The checker rejects error codes outside the permitted ranges, when the build targets the profile. Its tests: a valid range, `0x6F05`, and `0x0001`.
- **Tests:**
  - a dispatch on `INS` returning `6D00` for an unknown instruction;
  - `card.env.interface()`, with a scenario step `interface contact` or `interface contactless` (the default);
  - the handler-failure cases.

## 3. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| E1 | Chaining and long responses | (a) the platform reassembles, and serves long responses, with minimum request and response sizes of 1280 bytes; (b) the application sees every APDU | (a) |
| E2 | Request content | (a) the reassembled APDU without length fields: `CLA INS P1 P2`, then the data; (b) the data field only | (a). Applications dispatch on `INS` |
| E3 | Status words | (a) fixed by the profile (§2.3), with application error codes restricted to valid ISO status words and checked at build time; (b) implementation-defined | (a) |
| E4 | User presence | (a) `card.env.interface()`, with presence implied on `Contactless`; (b) no API, and the profile just states that presence is implied on NFC | (a) |

**Decided 2026-11-18:**

- **E1, revised at your suggestion: transport bindings.** The profile's APIs stay transport-independent. Profile §11 defines bindings, and a platform claims one or more of them. An application declares at build time which binding it is written for. In both bindings the platform reassembles messages, and supports messages of at least 1280 bytes.
  - **The ISO 7816 binding:** reassembled APDUs. E2 and E3 apply only here.
  - **The raw binding**, for example for TrustZone-M on an MCU: the request is the raw message, and the response is raw bytes. The outcome is delivered as a pair (category, 16-bit code) through the host-side interface, whose encoding is platform-defined.
- **E2 (a)**, in the ISO 7816 binding: the request is `CLA INS P1 P2`, then the data.
- **E3 (a)**, in the ISO 7816 binding: the profile fixes the status words, and application error codes are restricted to ISO status words, checked at build time.
- **E4 (b):** there is no API. The profile states that on a contactless interface, presenting the card counts as user presence; anything else is platform-defined. `card.env.interface` and `Interface` are dropped.

## 4. Exit checklist

- Profile §11 is written, and §12 (the B.12 answers) is updated.
- The catalog has `card.env.interface`, and `base-types.card` has `Interface`.
- The checker enforces the error-code ranges for the profile.
- `python -I tools/run_checks.py` passes.
