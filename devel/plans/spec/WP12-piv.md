# WP12 — A PIV applet: detailed sub-plan

Parent: `plans_and_notes/draft-0.2-candidates.md`, candidates 19 and 20.
Inputs: `plans_and_notes/PIV-step0-notes.md` (the subset, the findings, decisions Q1 to Q5), and the FIDO2 work (WP8, WP8b) as the model.
Status: decisions H1 to H4 taken 2026-11-20, all as recommended (option (a)). **Step 1 done (2026-11-20):**
- `card.crypto.sign_digest` and `verify_digest` (BP-29, catalog, natives 35 and 36, HAL-25, `cl_hal.h`, the interpreter and the prototype), with test `run-031`;
- deselection ends the session in the ISO 7816 binding (BP-55, BP-56), with the scenario step `deselect` and test `run-032`;
- both tests pass on both backends, and all checks pass.

**Step 2 done (2026-11-20):** `examples/piv/` has `constants.card`, `objects.card`, `admin.card` and `iso7816-entry.card` (354 lines):
- SELECT with the application property template;
- GET DATA and PUT DATA for eight objects, including the bare Discovery Object;
- the administration key `9B` with AES-128, both the challenge (A.1) and the mutual authentication (A.2).

`tools/piv/check_piv.py` was started early, so that the core is checked from the start. It runs 22 checks, which pass on both backends and are two runs in `run_checks`. Compiled, the core is 2,344 bytes of code, with a stack need of 281 bytes and 9,984 bytes of persistent storage.

**Findings so far,** for `WP12-piv-findings.md` in step 6:
- **The buffer is chosen with an `if` chain.** An object's buffer must be chosen by an `if` chain in every function that touches it (`read_object`, `write_object`, `object_capacity`). CardLang cannot select one of several globals as a value, or pass one of them through a variable. A 2-D array would waste space, because the objects' sizes differ.
- **`63CX` needs 11 error members** (Q5), rather than 16, because the retry counters are at most 10.

**Step 3 done (2026-11-20):** `pin.card` implements:
- VERIFY in all its P1 forms, the format checks and blocking;
- CHANGE REFERENCE DATA for the PIN (`80`) and the PUK (`81`);
- RESET RETRY COUNTER.

Each comparison spends a retry before it compares, as anti-tearing, and gives it back on a match. `check_piv.py` has 27 more checks, 49 in all, which pass on both backends. The applet is 527 lines, with 3,520 bytes of code.

**Finding:** the order of the format and match errors needs care. PIV allows `6A80` or `63CX` when both the old and the new value are bad, and the applet checks both formats first, so it never spends a retry on a malformed request.

**Step 4 done (2026-11-20):** `keys.card` implements:
- GENERATE ASYMMETRIC KEY PAIR for `9A`, `9C`, `9D` and `9E`, where the delete and the generation form one transaction;
- GENERAL AUTHENTICATE signing a given digest with `9A`, `9C` and `9E`, as DER `Ecdsa-Sig-Value`, through `card.crypto.sign_digest`. `9C` is *PIN Always*, through the `sign_ready` session flag;
- ECDH with `9D`.

`check_piv.py` has 20 more checks, 69 in all, which pass on both backends. The signatures are verified on the host over the digest, and Z is compared with the host's own ECDH. The applet is complete for the subset: 636 lines, 4,505 bytes of code, a stack need of 344 bytes, and 10,002 bytes persistent.

**A first contrast with FIDO2**, for §10 of the report: PIV's largest frame is 164 bytes (`asymmetric_authenticate`), against FIDO2's 475. PIV's stack need is 344 bytes, against 837. Its large data lives in persistent buffers, not in frames.

**Steps 5 and 6 done (2026-11-21):**
- the check is complete, with 69 checks;
- `VM5-measurements.md` §10 compares PIV with FIDO2;
- `plans_and_notes/WP12-piv-findings.md` records the findings;
- candidates 23 and 24 are added.

**WP12 is complete.**

## 1. Goals

1. **The applet.** A second realistic CardLang applet, a PIV card application, in `examples/piv/`. It covers the contact-interface subset of the step-0 notes, §2.
2. **Two profile changes,** decided in step 0:
   - signing and verifying a given digest (Q1);
   - deselection ending the session in the ISO 7816 binding (Q2).
3. **An independent check,** `tools/piv/check_piv.py`, as `check_fido2.py` is for FIDO2. It runs a host-side PIV session against the applet and checks every response with its own code. It runs on both backends.
4. **A second measurement corpus.** The VM5 report gains a section comparing PIV's figures with FIDO2's. FIDO2-specific conclusions, such as the liveness question, are re-examined there.

**Out of scope,** as in step 0:
- secure messaging and the virtual contact interface;
- on-card biometric comparison;
- the pairing code;
- the global PIN;
- retired keys;
- RSA and P-384;
- the contactless rules (Q3).

## 2. The profile changes (step 1)

### 2.1 Signing a digest (Q1)

- **New APIs:** `card.crypto.sign_digest(key, alg, ref digest, inout signature) -> u32` and `card.crypto.verify_digest(key, alg, ref digest, ref signature) -> bool`. They are as `sign` and `verify` (BP-29), except that `digest` is used as is.
- **The algorithm** is `SignatureAlgorithm.EcdsaP256Sha256`, so `digest` must be exactly 32 bytes; any other length is `Err(CardError.Malformed)`. That length rule makes a new algorithm value unnecessary.
- **Where they go:**
  - **the profile:** BP-29, with new catalog entries;
  - **the bytecode:** native numbers 35 and 36, appended in catalog order (BC-32);
  - **the HAL:** new operations `cl_hal_sign_digest` and `cl_hal_verify_digest` (HAL-25). The signing stays in the HAL (HAL-1);
  - **the implementations:** the interpreter and the prototype's test HAL.
- **Tests:** a runtime test, and the catalog and profile checks.

### 2.2 Deselection ends the session (Q2)

- **BP-55 and BP-56 change for the ISO 7816 binding.** When the application is deselected, because another application is selected, its session ends (STA-4). The next SELECT of the application starts a new session, and `on_session_start` runs before `on_select`.
- **The raw binding is unchanged.**
- **The harness** gains a `deselect` scenario step: another application is selected. Both backends implement it.
- **A runtime test** shows that session state is reset by a deselection, and survives a re-SELECT of the same application.

## 3. The applet

Files in `examples/piv/`, in build order, following the FIDO2 layout:

| File | Contents |
|---|---|
| `constants.card` | The AID; the tags, key references and algorithm identifiers; the error set of status words, including `63C0`–`63CF` (Q5) |
| `objects.card` | The data objects: one persistent buffer and length per object (H1); GET DATA and PUT DATA |
| `pin.card` | The PIN and PUK: format checks, retry counters, VERIFY (all P1 forms), CHANGE REFERENCE DATA, RESET RETRY COUNTER; the security status in `session` state |
| `admin.card` | The administration key `9B`: AES-128 challenge-response and mutual authentication through GENERAL AUTHENTICATE (H3) |
| `keys.card` | GENERATE ASYMMETRIC KEY PAIR; GENERAL AUTHENTICATE for signing (`sign_digest`, DER-encoded) and for ECDH (`agree`); the key access rules, including *PIN Always* for `9C` |
| `iso7816-entry.card` | `on_install` (the defaults, H2), `on_select` (the application property template), and the command dispatch |

**Persistence and atomicity.**
- PIN and PUK changes, retry counters and object writes are persistent assignments.
- A retry counter is decremented, in its own atomic update, before the comparison. So a power loss during a wrong attempt cannot leave the counter undecremented: the standard anti-tearing order.
- A PUT DATA of a whole object is one atomic update of its buffer and length, inside a transaction.

## 4. The check (`tools/piv/check_piv.py`)

**An independent host side.** It has a small BER-TLV encoder and parser of its own, DER signature parsing, and P-256 verification (from `p256.py`). It drives a session like this:

1. SELECT by full and by truncated AID; check the application property template.
2. GET DATA of the CHUID and the Discovery Object; `6A82` for an object that is absent.
3. VERIFY: wrong PINs count down (`63C2`, `63C1`), then a block (`6983`), then RESET RETRY COUNTER with the PUK; a format error (`6A80`); P1 `FF`; the empty form.
4. Administrator authentication with AES-128: a wrong response, then the correct one.
5. GENERATE ASYMMETRIC KEY PAIR for `9A`, `9C` and `9D`, then PUT DATA of a certificate of about 900 bytes. GET DATA of it must give the same bytes.
6. GENERAL AUTHENTICATE:
   - sign a SHA-256 digest with `9C` and verify it with the returned public key;
   - check that `9C` needs the PIN before each signature;
   - ECDH with `9D` against a host key, comparing Z.
7. Security status: verify the PIN, deselect, re-SELECT; the status must be reset (Q2).

The check runs on `interp` and on `vmproto` (`--backend`), and becomes two runs in `run_checks.py`.

## 5. Measurement (step 6)

- Add `examples/piv` to `typer.programs()`, so that the typer, the compiler check and `measure.py` include it automatically.
- Add §10 to the VM5 report: PIV's code size, frames and stack need, and its most-used opcodes and sequences, against FIDO2's.
- Say which of the VM6 and VM4b conclusions hold for both applets and which were FIDO2-specific. That includes slot reuse against liveness.

## 6. Steps

1. The profile changes (§2), with their tests, on both backends.
2. The applet core: `constants`, `objects` and the entry point (SELECT, GET DATA, PUT DATA), and the administration key.
3. The PIN and PUK.
4. The keys and GENERAL AUTHENTICATE.
5. `check_piv.py`, on both backends.
6. Measurement (§5). Record findings, as `WP8-fido2-findings.md` did for FIDO2, in `plans_and_notes/WP12-piv-findings.md`.

## 7. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| H1 | Data-object storage | (a) a fixed persistent buffer per object, of the object's largest size (about 2 KB per certificate, so about 9 KB in all), with its length; (b) one shared persistent area with allocation | (a). Simple, and PUT DATA stays one atomic update. (b) needs an allocator and fragmentation handling for little gain in a test applet |
| H2 | Initial credentials | (a) well-known test defaults set by `on_install`: PIN `123456`, PUK `12345678`, administration key `01 02 … 08` twice (AES-128), documented as test-only; (b) no defaults, with a personalisation command | (a). It matches common practice for test cards, so OpenSC works out of the box. A real issuer would personalise |
| H3 | Administration key algorithms | (a) AES-128 (`08`) only, for the subset; (b) AES-128, -192 and -256 | (a). The others need only a key-size switch, and can be added later |
| H4 | Signing for `9A` and `9E` too | (a) GENERAL AUTHENTICATE signs with `9A`, `9C` and `9E`, each with its own access rule; (b) only `9C` | (a). OpenSC authenticates with `9A`; `9E` needs no PIN. It is the same code with a different rule |
