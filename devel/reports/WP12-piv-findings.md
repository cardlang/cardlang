# WP12 — PIV applet: findings

Date: 2026-11-21. Plan: `plans_and_notes/spec-plans/WP12-piv.md`. Reading notes: `plans_and_notes/PIV-step0-notes.md`.

## 1. Result

- **The applet.** `examples/piv`, in 636 lines and six files, implements the contact-interface subset of SP 800-73-5 chosen in step 0:
  - SELECT, with the application property template;
  - GET DATA and PUT DATA for eight objects;
  - the AES-128 administration key, by challenge and by mutual authentication;
  - VERIFY, CHANGE REFERENCE DATA and RESET RETRY COUNTER;
  - P-256 key generation for `9A`, `9C`, `9D` and `9E`;
  - signing a given digest, with `9C` as *PIN Always*;
  - ECDH.
- **The check.** `tools/piv/check_piv.py` runs 69 independent checks. It has its own TLV codec, its own AES and P-256 verification, and host-side ECDH. All of them pass on the reference interpreter and on the prototype VM.
- **What it needed.** Two profile changes, both decided in step 0 and made in step 1:
  - signing and verifying a given digest (natives 35 and 36);
  - deselection ending the session in the ISO 7816 binding.

  With those, the applet needed no change to the language and none to the VM.
- **It went in smoothly.** Each file was accepted by the checker at its first or second compile, and every check passed on both backends at its first run.
- **Size.** 4,505 bytes of code, a stack need of 344 bytes, and 10 KB of persistent storage. See `plans_and_notes/VM5-measurements.md` §10 for the comparison with FIDO2.

**Not yet done:** testing against real host software (OpenSC, `pkcs11-tool`). That needs a bridge, or the C VM on a device (step 0 §3).

## 2. Findings

### Language

| # | Finding | Weight | Candidate |
|---|---|---|---|
| L1 | **No way to choose one of several globals.** An object's buffer must be chosen by an `if` chain in every function that touches it (`read_object`, `write_object`, `object_capacity`), because a global cannot be selected through a variable or passed on as a value outside a call. A two-dimensional array would waste space, because the buffers' sizes differ (256 bytes to 1.9 KB) | Medium: about 60 lines of the applet's 636 | Something like a *view of a global* chosen at run time, or a `match` that yields a reference. To be thought through; it touches the reference model of chapter 8 |
| L2 | **Status words that carry a count** (`63CX`): 11 error members (`63C0` to `63CA`) and a lookup function `retries_left` (PIV step 0, Q5) | Low: about 25 lines | Candidate 22. It still has a single user, so no change yet |
| L3 | **`attempt … else` maps every error to one member.** Where PIV needs two different status words from one call, the applet uses a `match`, as for `agree` (`NotFound` gives `6A88`, anything else `6A80`), or checks the input first, as for the 32-byte digest length before `sign_digest` | Low; this is the intended design (OUT-22) | None |
| L4 | **What worked well:** the anti-tearing order (spend a retry, then compare) is one persistent assignment before the comparison. The application security status is plain `session` state, which the profile rule now resets at deselection. *PIN Always* is one more session flag. All three fit the language as it is | — | — |

### Profile

| # | Finding | Status |
|---|---|---|
| P1 | No signature over a given digest | **Done** in step 1: `sign_digest` and `verify_digest` (BP-29, candidate 19) |
| P2 | Deselection was invisible to applications | **Done** in step 1: deselection ends the session in the ISO 7816 binding (BP-55, BP-56, candidate 20) |
| P3 | No query for the interface (contact or contactless) | Deferred (Q3, candidate 21). The subset is contact-only, so the applet wrongly accepts every command over contactless |
| P4 | A PIV certificate (up to about 1.9 KB) exceeds the 1,280-byte message minimum (BP-48) | Kept as it is (Q4). P-256 certificates usually fit. Applet-level chunked I/O, as in Java Card, is candidate 18 |
| P5 | **AES-ECB on one block** is spelled as AES-CBC with a zero IV (`admin.card`). It works, and it is not cryptography in the VM, but it is not obvious to a reader | Minor. An `AesEcbNoPadding` cipher value would make it explicit, and is a one-line catalog change. Not proposed yet |
| P6 | **Finding a child in a TLV template** (`find_child` over `card.tlv.head`) is written by hand. FIDO2 has the CBOR equivalent (`find_text_key`) | Minor. A `card.tlv.find(ref data, tag)` native would be a convenience, not a necessity |

### Bytecode and compiler

These are from `VM5-measurements.md` §10.4.

| # | Finding | Kind |
|---|---|---|
| B1 | Error exits repeat: 68 `ERR`s, 24 of them `6A80`. Sharing one exit per code would save about 4% | Compiler |
| B2 | Compare-with-constant-and-branch is frequent in both applets | Bytecode, to measure in VM7 |
| B3 | Slices from a constant start; `SLICEF` covers only a frame-slot start | Bytecode |
| B4 | Long `ADDR`s to `PERSISTENT` and `SESSION`, at offsets up to 10 KB | Bytecode |
| B5 | Byte-sized frame loads (`LDF8 u8`) | Bytecode |

### Tools

| # | Finding |
|---|---|
| T1 | `check_piv.py` was started in step 2 rather than step 5, and grew with each step. Checking each part as it was written caught no applet bugs, because none occurred, but it made each step's acceptance immediate. It is a better order than in WP8 |
| T2 | The applets now cover two shapes, so measurements can tell general conclusions from applet-specific ones (`VM5-measurements.md` §10.2, §10.3) |

## 3. What is next

- **Before or during VM7:** B1, a compiler-only change, at any time. B2 to B5 should be measured on both applets, as possible changes to version 1, which stays living through VM7.
- **For Draft 0.3:** L1, the hardest of these findings, joins the candidate list. P5 and P6 are recorded as minor profile ideas.
- **Real-world testing** with OpenSC waits for a bridge or a device.
