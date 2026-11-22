# FIDO2 authenticator

A FIDO2 authenticator for CTAP 2.0 over NFC, written in CardLang against the Base Profile and its ISO 7816 binding. It is an example of a real protocol applet. It is not a certified authenticator, and its AAGUID, `CardLangExample1`, is a placeholder.

## What it implements

- **The commands:**
  - `authenticatorGetInfo`, built at runtime so that `clientPin` reflects whether a PIN is set;
  - `authenticatorMakeCredential`, with ES256 (P-256) and `"none"` attestation;
  - `authenticatorGetAssertion`, with a signature counter;
  - `authenticatorClientPIN`: `getPINRetries`, `getKeyAgreement`, `setPIN`, `changePIN` and `getPinToken`;
  - `authenticatorReset`.
- **PIN/UV auth protocols two and one,** with PIN-based user verification in `makeCredential` and `getAssertion`.
- **Non-resident credentials.** The credential ID is a nonce and a MAC, and the credential's private key is derived from it, so nothing is stored per credential.
- **SELECT** returns the version string, `FIDO_2_0`.

**Left out:**
- resident (discoverable) credentials: `rk: true` is refused with `CTAP2_ERR_UNSUPPORTED_OPTION`;
- attestation other than `"none"`;
- CTAP 2.1 additions, such as credential management and `authenticatorSelection`;
- CTAP1/U2F;
- transports other than NFC (ISO 7816). On NFC every command counts as user present (BP-54).

**Limits worth knowing:**
- The signature counter is checked arithmetic. At 2^32 it traps, and every later assertion fails.
- The PIN token is kept in `session` state, as bytes as well as a key. It is cleared at power-on and reset, but sits in application memory between commands.

## Files

In the order of `cardlang.json`:

| File | Contents |
|---|---|
| `constants.card` | Constants, the error set, persistent and session state, the AAGUID and `getInfo`'s fixed parts |
| `cbor.card` | Reading and writing the CTAP CBOR structures, using `card.cbor` |
| `credentials.card` | Non-resident credentials: making and checking credential IDs, and deriving their keys |
| `pin.card` | The PIN/UV auth protocols and `authenticatorClientPIN` |
| `ctap.card` | The CTAP commands and their dispatch |
| `iso7816-entry.card` | The ISO 7816 entry point: SELECT, and CTAP errors turned into status words. It is the only binding-specific file |

`getinfo.scenario` is a short session to run or debug: SELECT, `getInfo`, `reset`, a malformed `makeCredential`, and an unknown instruction.

## Checking, building and running

From the repository root, in the uv environment:

```bash
uv run python -I tools/clc.py check examples/fido2
uv run python -I tools/clc.py build examples/fido2
uv run python -I tools/clc.py run examples/fido2/getinfo.scenario --backend vmproto
uv run python -I examples/fido2/check.py . --backend interp
```

- `build` writes the image to `examples/fido2/build/fido2.clvm`.
- `run` accepts `--backend interp`, `vmproto`, `cvm-msvc` or `cvm-clang`.
- In VS Code, with the CardLang extension, open `getinfo.scenario` and use **CardLang: Run Scenario**, or **CardLang: Debug Scenario** to step through the applet.

## The independent check

`check.py` runs a full CTAP session, 59 checks in all, and checks every response with code of its own, without reusing any of the applet's logic. It has a CBOR codec, a DER parser, and a host-side implementation of both PIN protocols: key agreement, both KDFs, both encryption forms and both tag lengths. ECDSA verification uses the interpreter's test crypto. It covers:
- `getInfo`, and the authData and COSE key from `makeCredential`;
- assertions whose signatures verify, with an increasing counter;
- rejecting another RP's credential, a tampered credential ID, an unsupported algorithm, `rk`, a missing parameter, non-canonical CBOR, and unknown commands;
- `reset`, which invalidates credentials and restarts the counter;
- credentials surviving a security reset;
- for each PIN protocol: setting and changing the PIN, getting a token, PIN-based UV, retries and blocking.

`tools/run_checks.py` runs it on all four backends, together with the scenario.

## Background

The applet was written in work package WP8, in steps: the CTAP core first, then the PIN protocols. What it showed about the language and the profile, and what changed as a result, is in [the findings report](../../devel/reports/WP8-fido2-findings.md).
