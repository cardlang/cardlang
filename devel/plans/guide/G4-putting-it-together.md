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

## 5. Progress

**`excerpt` in `guidecheck` (Q1), 2026-11-24:**
- `<!-- check: excerpt PATH -->`: the block's runs of lines, split at lines `// ...`, must appear in `PATH`, exactly and in order.
- **Injection:** a changed line, two runs out of order, and a missing file each failed.

**A fix to the example:** `get_assertion` wrapped the single write `sign_count += 1;` in a transaction of its own. A single persistent write is already atomic (STA-11), so the transaction was removed. Behaviour is unchanged: `check.py` passes on the interpreter and the Python VM. It would otherwise have contradicted chapter 6 in a quoted excerpt.

**Chapter 10, drafted 2026-11-24, waiting for the user's review (Q2):**
- **The map:** FIDO2 in a paragraph, the six files, and how to read an applet.
- **Stop 1:** the entry, with `Err(IsoError(code))` (OUT-21), `0x91`-prefixed codes, and CTAP status as data with `9000`.
- **Stop 2:** `get_assertion`, with elisions: spans, an `attempt` and `require` spine, and the counter going up before signing, with why it differs from the vault.
- **Stop 3:** non-resident credentials, `Command` keys, and `attempt … else`.
- **Stop 4:** `pin_retries` (persistent) and `pin_failures` (session); `check_pin_hash` decrementing first, and its callers' guard.
- **Testing:** `getinfo.scenario` and `check.py`.
- **Confirmed:** the callers' guards (`require pin_retries != 0`, `pin.card:210, 235`), the codes (`CtapPinInvalid = 0x9131`), and the 59 checks (the example's README).

**Chapter 10, review (user): "What guarantees that a result of an hmac is a valid p256 private key?"** Nothing did.
- **The problem:** an HMAC is `n` or more about once in 2³², and `card.key.import` refuses it with `Malformed` (BP-21). `make_credential` then failed that registration with `CtapOther`. `get_assertion` was safe, because it only sees IDs that `make_credential` issued.
- **The fix in the example (user: retry and explain):**
  - `load_credential_key` returns `bool`: `false` on `CardError.Malformed`, and `CtapOther` for anything else;
  - `make_credential` draws nonces in a loop bounded by `MAX_NONCE_DRAWS` = 4, then `require loaded`;
  - `get_assertion` does `require loaded`.

  `check.py` passes on the interpreter and the Python VM.
- **A front-end bug the fix exposed:** `outcheck.CARD_ERROR` was a stale hand-written list, without `InvalidState`, `Unsupported` and `Malformed`. The new name checker, NAM-16, rejected `Err(CardError.Malformed)` as CE-NAM-9. The list is now `set(CARD_ERROR_CODES)` from `cardlang.platform.errors`, the profile's one table. A made-up member is still CE-NAM-9. The FIDO2 example, compiled in `run_checks`, now guards it.
- **A test of the platform's rejection:** `run-019-keys` imports a private scalar equal to `n`, and one of zero, and both give `err platform Malformed`, on the interpreter, the Python VM and the C VM. The retry's own invalid branch cannot be triggered in a test, since that needs about 2³² draws. The chapter says so.
- **The chapter:** stop 3 has a new part, *Not every HMAC is a key*, with the new `load_credential_key` and the bounded loop as excerpts. Stop 2's excerpt shows `require loaded`.

**Chapter 10:** committed, with the FIDO2 retry.

**Chapter 11, drafted 2026-11-24, waiting for the user's review (Q3):**
- **A summary table,** then topics:
  - memory, errors, integers and conversions, and precedence;
  - pointers, and recursion;
  - persistence and atomicity, and session state;
  - the entry point, and what is left out.
- **Each topic:** the C or Java Card way (`c` and `java` blocks, not checked), CardLang's way (checked), and the reason.
- **The CardLang examples** are 4 fragments and 4 errors: CE-OUT-1, CE-EXP-4 (`flags & MASK == 0`), CE-TYP-5 (a view field) and CE-FUN-1. All are confirmed by the check.
- **The Java Card facts,** checked against what Java Card guarantees:
  - a single persistent field update is atomic, and `Util.arrayCopy` is atomic;
  - an open transaction is aborted by the runtime;
  - `byte` is signed, and `short` arithmetic gives `int`;
  - transient arrays use `CLEAR_ON_DESELECT`.

  These are illustrations, not compiled.

**Chapter 11, review (user):**
- **Java Card memory:** the text said "the heap is not reclaimed reliably" and "a card may never reclaim memory", which is too harsh, since modern Java Card implementations have garbage collection. It now says objects live in persistent memory, which is slow to write, and that collection is heavy, so applets usually allocate at installation.
- **The invalid examples** were not obviously invalid. Each now has a `// does not compile: …` comment. The outcome example mirrors the C mistake (`verify_pin` ignored, then `verified = true`), and is followed by the correct version with `attempt`. The precedence example is followed by the correct `(flags & MASK) == 0`.
