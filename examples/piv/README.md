# PIV card application

A PIV card application (NIST SP 800-73-5) for the contact interface, written in CardLang against the Base Profile and its ISO 7816 binding. It is an example of a real protocol applet. It is not a certified PIV card.

## What it implements

- **SELECT,** returning the application property template.
- **GET DATA and PUT DATA** for eight data objects: CHUID, the four certificates (`9A`, `9C`, `9D`, `9E`), the Discovery Object, the Security Object, and the fingerprint and facial-image objects. The last three are stored with their access rules, with no further meaning.
- **The administration key `9B`:** AES-128, by challenge and by mutual authentication.
- **The PIN and the PUK:** VERIFY, CHANGE REFERENCE DATA and RESET RETRY COUNTER. Each attempt spends a retry before comparing, in its own atomic update, so a power loss during a wrong attempt cannot restore the counter.
- **Asymmetric keys:** P-256 key generation for `9A`, `9C`, `9D` and `9E`. Signing uses a digest computed off the card, and `9C` is *PIN Always*. `9D` does ECDH.
- **Deselection** ends the session, so the security status is reset.

**Left out:**
- the contactless interface, secure messaging and the virtual contact interface;
- on-card biometric comparison;
- the pairing code and the global PIN;
- retired keys;
- RSA, P-384 and 3DES.

**Test defaults.** `on_install` sets well-known test values, as test cards usually do:
- PIN `123456`;
- PUK `12345678`;
- administration key `01 02 03 04 05 06 07 08 01 02 03 04 05 06 07 08`.

A real issuer would personalise the card instead.

**Not yet done:** testing against real host software, such as OpenSC and `pkcs11-tool`. That needs a bridge to a virtual reader, or the C VM on a device.

## Files

In the order of `cardlang.json`:

| File | Contents |
|---|---|
| `constants.card` | Constants, the error set, persistent and session state, and the test defaults |
| `objects.card` | The data objects: GET DATA and PUT DATA |
| `admin.card` | The administration key: GENERAL AUTHENTICATE with `9B` |
| `pin.card` | The PIN and PUK: VERIFY, CHANGE REFERENCE DATA and RESET RETRY COUNTER |
| `keys.card` | GENERATE ASYMMETRIC KEY PAIR, and GENERAL AUTHENTICATE with the asymmetric keys |
| `iso7816-entry.card` | The ISO 7816 entry point: installation, SELECT and the command dispatch |

`basic.scenario` is a short session to run or debug: SELECT, GET DATA of an absent object, the PIN's retries, and an unknown instruction.

## Checking, building and running

From the repository root, in the uv environment:

```bash
uv run clc check examples/piv
uv run clc build examples/piv
uv run clc run examples/piv/basic.scenario --backend pyvm
uv run python -I examples/piv/check.py . --backend interp
```

- `build` writes the image to `examples/piv/build/piv.clvm`.
- `run` accepts `--backend interp`, `pyvm`, `cvm-msvc` or `cvm-clang`.
- In VS Code, with the CardLang extension, open `basic.scenario` and use **CardLang: Run Scenario**, or **CardLang: Debug Scenario** to step through the applet.

## The independent check

`check.py` runs a host-side PIV session, 69 checks in all, and checks every response with code of its own, without reusing any of the applet's logic. It has a BER-TLV encoder and parser, and uses the interpreter's test-only AES and P-256 for the host's side of authentication, signature verification and ECDH. `tests/run_checks.py` runs it on all four backends, together with the scenario.

## Background

The applet was written in work package WP12. The subset was chosen in its step 0, from a reading of SP 800-73-5. What it showed about the language, the profile and the compiler is in [the findings report](../../devel/reports/WP12-piv-findings.md).
