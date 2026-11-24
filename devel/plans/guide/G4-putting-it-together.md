# G4 — Putting it together: detailed sub-plan

Planned 2026-11-24, the fifth work package of the guide's plan of plans. It writes the last two chapters:
- chapter 10, *A real applet*, a guided reading of part of the FIDO2 example;
- chapter 11, *Coming from C or Java Card*, the one chapter where comparisons with other languages belong.

## 1. What there is now

- **Chapters 1 to 9** teach the whole language and toolchain through the vault and two small applets, `tally` and `pincheck`.
- **`examples/fido2`** is a CTAP 2.0 authenticator over NFC, in 6 files and about 780 lines:
  - **`iso7816-entry.card`:** the ISO 7816 entry. It is the only binding-specific file, and turns CTAP errors into a one-byte status in the data, with `Err(IsoError(code))` (OUT-21, which chapter 5 left to the specification).
  - **`constants.card`:** the error set, with codes `0x91xx`, and the state: `sign_count`, the PIN hash, `pin_retries` (persistent) and `pin_failures` (session).
  - **`cbor.card`:** reading and writing CTAP's CBOR with `card.cbor`.
  - **`credentials.card`:** non-resident credentials. The credential ID is a nonce plus a MAC, and the private key is derived from it, so nothing is stored per credential.
  - **`pin.card`:** PIN protocols one and two: ECDH, HKDF, AES, and the retry logic.
  - **`ctap.card`:** dispatch, `getInfo`, `makeCredential`, `getAssertion` and `reset`.
- **The example is compiled and tested** by `run_checks`: `check.py` runs 59 independent host-side checks.
- **No chapter compares CardLang with another language.** Chapter 11 is where those comparisons were deferred, by the user's request.

## 2. The work

### 2.1 Chapter 10: A real applet

A guided reading, not a rewrite. The reader learns how a protocol applet is organised, and sees each chapter's ideas at work in code they did not write.

1. **The map:** what FIDO2 is, in a paragraph; the six files and what each holds; and the order in which to read an applet.
2. **The parts the chapter walks through (Q2).**
3. **What is new here,** shown in place:
   - `Err(Set(code))`;
   - errors carried as data for a protocol that reports its own status (BP-52);
   - command-lifetime keys;
   - `card.cbor`;
   - key derivation.
4. **How the example is tested:** `getinfo.scenario`, and `check.py`, an independent host that checks every response with its own code.
5. **What next:** reading the PIV example, and the parts of FIDO2 the chapter skipped.

### 2.2 Chapter 11: Coming from C or Java Card

For readers who know C, embedded C or Java Card. It says what is different, and why (Q3).

**The topics:**
- memory: fixed sizes, no heap, no `new`, and transient arrays;
- errors: `errno` and return codes, `ISOException`, and outcomes;
- integers: C's wrap and undefined behaviour, Java's `short` promotion and casts, and CardLang's traps and explicit conversions;
- operator precedence;
- pointers and references;
- recursion and the stack;
- persistence and atomicity: C's hand-written flash journaling, Java Card's persistent fields and `JCSystem.beginTransaction`, and CardLang's atomic writes and transactions;
- session state and transient arrays;
- the entry point: `process(APDU)` and the request and response views;
- what CardLang leaves out: objects, classes, inheritance, interfaces, strings, floating point, generics, callbacks and libraries.

**Each topic** has a short C or Java Card snippet, then the CardLang way, and the reason. The CardLang code is checked; the C and Java snippets are shown, not checked. `guidecheck` already ignores languages other than `cardlang` and `scenario`.

### 2.3 Checks

- Every CardLang block passes `guidecheck`, and every excerpt from the example is checked as Q1 decides.
- Each fact the chapters state about the example (sizes, numbers of checks, behaviour) is confirmed with the tools.
- The C and Java Card snippets are idiomatic and correct, read with care. They illustrate, and are not compiled.

## 3. Checks

- `run_checks` passes, and so does the link check.
- `mkdocs build --strict` passes, and each chapter is viewed in the preview.
- The user reviews each chapter.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | How chapter 10's excerpts of the FIDO2 example are kept correct | (a) a new check comment, `<!-- check: excerpt examples/fido2/ctap.card -->`. The block must appear, line for line, in that file, so an edit to the example that the guide no longer matches fails the check. The example itself is already compiled and tested by `run_checks`; (b) mark the excerpts `none`, and link to the files on GitHub; (c) quote no code: describe the example in prose, with links to lines | (a). The reader sees real code, and the guide cannot drift from it. It is a small addition to `guidecheck`, checked by injection |
| Q2 | Which parts of FIDO2 the chapter walks through | (a) **four stops:** the entry file (errors as data, `Err(IsoError(code))`); `getAssertion` end to end (parsing, the credential, signing, the counter); non-resident credentials (a MAC and a derived key instead of storage); the PIN retries (persistent tries and per-session failures, as in chapter 6). CBOR parsing and the PIN protocols' cryptography are pointed to, not walked through; (b) the whole applet, file by file; (c) only `getAssertion`, in depth | (a). Each stop shows something new against something the reader already knows. (b) is too long for a chapter, and (c) misses the design ideas |
| Q3 | How chapter 11 is organised | (a) **by topic,** each topic showing C, Java Card and CardLang briefly side by side, after a one-table summary; (b) two halves, "From C" and "From Java Card"; (c) a single table of differences, with links into the earlier chapters | (a). Most readers know one of the two, and a topic shows both differences in one place. The summary table serves readers who only skim |

**Decided (user, 2026-11-24):**
- Q1 (a): checked excerpts, `<!-- check: excerpt examples/fido2/<file> -->`.
- Q2 (a): four stops: the entry file, `getAssertion`, non-resident credentials, and the PIN retries.
- Q3 (a): chapter 11 is organised by topic, after a summary table.
