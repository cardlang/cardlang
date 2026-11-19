# WP8 — FIDO2 check: findings

Date: 2026-11-19. Scope: the WP8 core (`examples/fido2/`). That is `getInfo`, `makeCredential` (ES256, non-resident, `"none"` attestation), `getAssertion` and `reset`, over the ISO 7816 binding. The PIN protocol is the next step.

## 1. Result

- **The applet** is 552 lines in five files. One of them is binding-specific: `iso7816-entry.card`, with 78 lines.
- **It compiled under the full reference checker and the Annex A grammar check on the first attempt.** That is evidence that the rules are coherent, not proof: the checkers do not implement every rule (see `tools/README.md`).
- **`tools/fido/check_fido2.py` passes 21 independent checks.** It runs a CTAP session through the interpreter, and checks the responses with its own CBOR codec and DER parser. It covers:
  - the SELECT version string;
  - getInfo;
  - the authData and COSE key from makeCredential;
  - two assertions whose DER signatures verify with the credential's COSE key, with an increasing counter;
  - rejection of another RP's credential and of a tampered credential ID;
  - excludeList, an unsupported algorithm, `rk`, a missing parameter, non-canonical CBOR, an unknown command, an unknown INS and a short APDU;
  - reset invalidating credentials and restarting the counter;
  - credentials surviving a security reset.
- **The checker catches a broken applet.** A deliberately wrong signed-data field made both signature checks fail.
- **Comparison:** FIDO2Applet is about 9,200 lines of Java for full CTAP 2.1, so the sizes are not comparable. But the core flows here needed no `arrayCopyNonAtomic`-style copying (slice assignment covered it), no hand-written chaining (BP-49), and no hand-written CBOR parsing (`card.cbor`).

## 2. Findings

Each finding has a category, its evidence from the applet, and a proposed change. None of them is applied yet. They go to `draft-0.2-candidates.md`.

### Language

| # | Finding | Evidence | Proposal |
|---|---|---|---|
| L1 | **No byte-string literals.** Every CTAP text key and value is a hand-written byte list with a comment, for example `KEY_ID: u8[2] = [0x69, 0x64]; // "id"`. That is error-prone and hard to read | 12 constant byte arrays in `constants.card`, plus a 50-byte `GET_INFO` | A byte-string literal, such as `b"public-key"`, that checks against `u8[N]` (ASCII only, so no encoding questions) |
| L2 | **Translating errors needs one match arm per member.** CTAP errors must become status bytes, but an error binding cannot be inspected (OUT-14), so the entry point enumerates 12 members, each `Err(IsoError.X) => { return status(…); }` | A 50-line `match` in `iso7816-entry.card` | Let application code obtain an application error's code, for example a `code_of(e)` intrinsic returning `u16`, valid only for application errors. Or allow a map in the error declaration |
| L3 | **One error set mixes concerns.** The single error set (OUT-16) must hold both the binding-specific ISO status words (`WrongLength`, `InsNotSupported`) and the protocol-internal CTAP errors, so the shared `constants.card` knows about the binding | `constants.card` | Allow several error sets, or one per file group, or move the binding's status words to the binding. This relates to L2 |
| L4 | **A platform error cannot be mapped to an application error without a `match`.** `attempt` only propagates unchanged. The applet avoids most cases by validating CBOR once, but an import failure still needed a 9-line `match` | `load_credential_key`; the `validate` match in `ctap` | `attempt c else E.M`: on `Err`, return `Err(E.M)` instead, like `require` |
| L5 | **Ignoring an outcome takes five lines**: `match c { Ok() => { } Err(_) => { } }` | `load_credential_key` (the TEMP_KEY cleanup) | A short form for deliberately discarding an outcome, for example `ignore c;` |
| L6 | **No compound assignment.** `at = at + n;` appears 40 times, nearly every one after a CBOR write | `cbor.card`, `ctap.card` | `+=` (deferred in STM-6). Note that `at = at + attempt write(…)` is already allowed (EXP-51) and would halve the lines; I did not use it, which is itself a readability data point |
| L7 | **No local views.** Strings inside a message are carried as a `Span` struct `{start, length}`, and re-sliced each time, as in `params[rp_id.start..rp_id.start + rp_id.length]`. FUN-16 deliberately forbids local reference variables | 9 such slices | Keep FUN-16, but consider a block-scoped view binding, `with view = params[a..b] { … }`, that cannot escape the block |
| L8 | **EXP-49 (no calls in arguments) and the operator rule hurt little here.** About a dozen comparisons needed parentheses inside `and`/`or`, which reads fine. No nested-call workaround was needed beyond `n = attempt …` temporaries | — | No change. This is evidence for keeping both rules |
| L9 | **The counter traps at 2^32.** `sign_count + 1` is checked arithmetic, so at the maximum it traps inside the transaction, and every later assertion fails. That is correct language behaviour, but an application design point | `get_assertion` | No language change. The applet should use `checked_add` and decide a policy. Record it for the PIN step |

### Profile

| # | Finding | Evidence | Proposal |
|---|---|---|---|
| P1 | **Volatile keys outlive a trapped command.** `TEMP_KEY` must be deleted defensively before every use, because a trap between import and delete leaves it in place until power-on (BP-14) | `load_credential_key` | A third key storage, `KeyStorage.Command`, ended with the command like `OperationLifetime.Command`. That would remove the cleanup and the leak |
| P2 | **The CBOR writer is verbose for strings.** Each string takes `write_head`, then a slice copy and an offset update: four lines | `ctap.card` | `card.cbor.write_string(major, ref content, inout out) -> u32` |
| P3 | **SELECT needed an application-defined response.** Found in step 0 (R3), and fixed by BP-50a | — | Done |
| P4 | **User presence on NFC (BP-54) was enough** for the core: every command counts as user present | — | No change for NFC. See candidate 4 for other interfaces |

### Tools

| # | Finding | Fix |
|---|---|---|
| T1 | **Interpreter bug.** A whole view used as the source of a slice assignment (`material[0..32] = rp_hash;`, with `rp_hash` a view parameter) crashed the interpreter. No conformance test covered it | Fixed in `interp.py`. A regression step was added to `run-018`; it fails without the fix |
| T2 | The checker compiled the applet without complaint. Some rules (NAM-19 to NAM-21) are checked by review, not by the checker, so first-time acceptance is weaker evidence than it looks | None needed now |

## 3. What is next

- **The PIN protocol** (`clientPIN` protocol 2, F1 step 2). It exercises ECDH, HKDF, AES-CBC, HMAC, `wipe` and session state, and the open question of `FIDO_2_0` hosts and protocol 2.
- **Resident credentials** (F2 follow-up). These exercise persistent arrays of structures and transactions.
- **Decide which findings to take up for Draft 0.2.** L1, L2, L4 and P1 have the clearest payoff.
