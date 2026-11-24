# G3 — Applets for real: detailed sub-plan

Planned 2026-11-23, the fourth work package of the guide's plan of plans. It writes chapters 7, 8 and 9:
- talking to the host over both bindings;
- the platform's keys, signatures and randomness;
- testing and debugging.

As before, each chapter is reviewed by the user before the next is written.

## 1. What there is now

- **The vault** after chapter 6, on the raw binding:
  - commands `01` read counter, `02` increment, `20` verify, `24` change PIN, `D0` store secret, `CA` read secret;
  - a persistent PIN with tries, and a `verified` session flag;
  - error codes 1 to 7.
- **Chapter 1** introduces the platform, the two bindings, and the raw envelope. Chapter 5 shows the categories.
- **The Base Profile, §11:**
  - **ISO 7816 (BP-49 to BP-52):** the request is CLA, INS, P1, P2 and data, with SELECT handled by the platform, `on_select`, and the status words `9000`, the applet's code, `6F00` + code, and `6F00`. Application codes must lie in `6200`–`6EFF` or `9100`–`9FFF`. Deselection ends the session.
  - **Raw (BP-53):** the envelope, and opening and closing sessions.
- **The Base Profile, §7 and §8:**
  - keys: `card.key.generate`, `export_public`, `delete`, and persistent keys in transactions;
  - `card.crypto.sign_digest` with `EcdsaP256Sha256`, and `card.random.fill`.

  Signature bytes are not fixed (BP-30): no test may depend on them.
- **The scenario format** checks exact outcomes only, and has no "any 64 bytes" form. A command may be left without an `expect`.
- **A project's `cardlang.json`** lists file paths, which may point outside its folder, such as `../core.card`.
- **The PIV example** reports the tries left as `63CX` errors, one error member per count.

## 2. The work

### 2.1 Chapter 7: Talking to the host

1. **The two bindings, side by side:** the same outcome as a raw envelope and as a status word.
2. **The ISO 7816 binding in detail:**
   - the APDU in `request`: CLA, INS, P1, P2 and data;
   - SELECT, handled by the platform, and `on_select`;
   - status words;
   - the code ranges an applet's errors must use, and the build check;
   - long messages, reassembled by the platform;
   - sessions ending at deselection.
3. **A small ISO 7816 applet of its own (Q1, Q2).** The vault stays on the raw binding.
   - The new applet is a PIN-checking applet. It shows the APDU, SELECT and `on_select`, and errors as status words: `WrongPin` = `6300`, with the tries left as data, answered to an empty VERIFY.
   - An applet is written for the binding of the device it targets, and rarely needs both.
4. **Scenarios for ISO 7816:** `select`, `expect sw`, `deselect`.
5. **Why the raw binding exists:** TrustZone and microcontroller hosts, and the envelope.

### 2.2 Chapter 8: Using the platform

1. **Resources and identifiers:** keys as resources, named by `u32` identifiers. Persistent, volatile and command keys.
2. **Platform APIs are ordinary calls,** with outcomes and `CardError`s. Their output goes through `inout` views.
3. **The vault signs (Q3):**
   - `on_install` generates an ECDSA P-256 key;
   - a command answers the public key;
   - command `2A` signs a 32-byte digest, once the PIN is verified, and counts its signatures.
4. **Randomness:** `card.random.fill`, with an example of its own. The vault itself does not need it.
5. **`wipe`:** the vault wipes its secret when the PIN becomes blocked.
6. **Testing what cannot be predicted (Q4).** A new expectation, `expect ok length N`, checks that a command succeeded with exactly `N` bytes of data, whatever they are. The scenario checks the signature's length, then the signature count. It is built in this package (§2.4).

### 2.3 Chapter 9: Testing and debugging

1. **Scenarios as a test suite:**
   - one file per feature, kept beside the applet;
   - every step form, including `reset`, `session_start`, `deselect`, `seed` and `interrupt`;
   - `expect ok`, `err`, `trap`, `raw`, `sw` and `none`.
2. **Running them:**
   - from VS Code;
   - from a terminal, with `clc run`, and every file in a loop for CI;
   - on each backend: the interpreter, the Python VM, and the C VM.
3. **The debugger in depth:**
   - breakpoints, stepping into functions, the call stack, and watching `persistent` and `session` state;
   - the Traps and Failed expectations breakpoints.
4. **Finding a bug:** a planted bug in the vault, found from a failing scenario with the debugger.
5. **Looking at the image:** `clc disasm`, and the stack and size report as a budget.

### 2.4 Checks

- **Every example and scenario** passes `guidecheck`.
- **`expect ok length N` (Q4)** is added in the following places:
  - the scenario runner's parser and comparison, in `src/cardlang/harness/scenario.py`;
  - the harness README;
  - the extension's scenario grammar and its README;
  - the trace output of `clc run` and the debugger, if they print expectations.

  A conformance runtime test, or an existing signing test, uses it. It is checked by injection: a wrong length fails, and a non-`ok` outcome fails. The guide's scenario lexer needs no change, since `length` is not a step.
- **The debugger steps in chapter 9** are done by hand, or left to the user's review, as in chapter 1.

## 3. Checks

- `run_checks` passes, and so does the link check.
- `mkdocs build --strict` passes, and each chapter is viewed in the preview.
- The user reviews each chapter before the next is written.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | How the vault meets the ISO 7816 binding | (a) **Two builds, shared code.** The vault's logic moves into shared files. Each binding has its own small entry file with `process`, and its own errors file, with the same member names but codes suited to the binding: 1 to 7 for raw, and status words such as `6300` and `6982` for ISO 7816. Two folders, each with a `cardlang.json`, list the shared files and their own; (b) switch the vault to ISO 7816 for good, with ISO codes, from chapter 7 on; (c) show ISO 7816 on a separate small applet, and keep the vault raw | (a). It keeps the vault on the raw binding that the guide puts first, shows how one applet serves both kinds of device, and uses an applet's files for real. Only the entry and the error codes differ. The FIDO2 example's `iso7816-entry.card` is the same idea |
| Q2 | How the ISO 7816 vault reports a wrong PIN and the tries left | (a) `WrongPin` is one status word, `6300` ("verification failed"), and the tries left stay a data answer to an empty verify, as on the raw binding; (b) as ISO 7816 and PIV do: a wrong PIN answers `63CX`, with X the tries left. That needs one error member per count, chosen in the shared code, which then knows about ISO 7816 | (a). The shared code stays binding-neutral. (b) is left as an exercise, with a pointer to the PIV example |
| Q3 | What the vault's counter becomes in chapter 8 | (a) the counter counts signatures, and the increment command goes, as the vault's design intended; (b) keep increment, and add a separate signature counter | (a). The counter then means something, and chapter 5's overflow handling moves to the signature count |
| Q4 | How a scenario tests a signature, whose bytes are not fixed (BP-30) | (a) the scenario signs without an `expect` on the bytes, then checks the signature count, the errors, and the public key's length through other commands; (b) extend the scenario format with an "any N bytes" expectation, in the harness, the extension's grammar and the documentation | (a). It needs no new tooling. The text says plainly what the scenario cannot check, and why. (b) can come later if more applets need it |

**Decided (user, 2026-11-23):**
- **Q1 (c):** a separate small applet for ISO 7816. The vault stays raw. In the user's words, two builds "look like a complication", and "a given applet rarely would need to support both raw and iso7816. You know what you write for."
- **Q2 (a):** `WrongPin` = `6300`, with the tries left as data. This now applies to the small ISO 7816 applet.
- **Q3 (a):** the counter counts signatures, and the increment command goes.
- **Q4 (b):** extend the scenario format, as `expect ok length N` (§2.4).

## 5. Progress

**Chapter 7, drafted 2026-11-23, waiting for the user's review:**
- **The two encodings** side by side (PLT-9, BP-51, BP-53), and choosing a binding.
- **ISO 7816:** the APDU in `request`, chaining and extended length handled by the platform, status words and the BP-52 code ranges, SELECT and `on_select`, and sessions.
- **`pincheck`:** an ISO 7816 applet with VERIFY (tries before comparing, an empty VERIFY answering the tries left, `WrongPin` = `6300`), a status instruction, and `on_select`. Its scenario covers `select`, `deselect` ending the session, `expect sw`, and unknown INS and CLA. It passed on the interpreter and the Python VM as a prototype, before the chapter was written.
- **`guidecheck`:** `error CODE binding=B` checks a whole applet built for a binding. It is used for the BP-52 example. Injection: with a valid code, the check fails.
- **The 63CX exercise** points to the PIV example (Q2).

**Chapter 7, review (user):** CLA `00` is the *interindustry* class, and an applet's own commands must not be declared there. The text now explains interindustry and proprietary classes. `pincheck`'s status command was `00 CA`, the interindustry GET DATA instruction, so it moved to the proprietary `80 10`. `process` now dispatches on the class and the instruction together, and the scenario adds `80 20` → `6D00` and `A0 20` → `6E00`.

**Chapter 7:** committed after the review fix.

**`expect ok length N` (Q4), built 2026-11-23:**
- **The runner:** `parse_expect` reads `ok length N`. The runner reduces a successful outcome to `("ok-length", len)` before comparing, so `clc run` and the debugger, which compare the same pair, work unchanged.
- **The grammar:** the extension's scenario grammar gains `length`.
- **Documentation:** the conformance README's table, the extension README and the harness README.
- **Use and checks:** `run-031-digest-signatures` now checks a successful `sign_digest` with `expect ok length 64`, and passes on the interpreter, the Python VM and the C VM. By injection, length 63 fails, and an `err` outcome fails.

**Chapter 8, drafted 2026-11-23, waiting for the user's review:**
- **The platform's APIs:** families, outcomes, `inout` results, and algorithm enums. Keys are resources: identifiers, `KeySpec`, storage, PLT-33, and transactions.
- **The vault (Q3):**
  - `on_install` generates a persistent P-256 key in its transaction;
  - `30` reads the public key;
  - `2A` signs a 32-byte digest with `sign_digest`, once verified. It checks first, and stores the count only after the signature, which keeps `attempt … else CounterExhausted`;
  - `increment` and command `02` are removed (`remove=increment`).
- **Randomness:** a fragment, pointing to `seed` in chapter 9.
- **`wipe`:** `check_pin` wipes the secret and its length, in a transaction, on the last wrong try. A scenario checks blocking, since the wipe itself cannot be observed.
- **The prototype** passed on the interpreter and the Python VM before the chapter was written.

**Chapter 8:** committed.

**Chapter 9, drafted 2026-11-23, waiting for the user's review:**
- **The suite:** tables of every step and every expectation (from the harness and conformance READMEs), and one file per feature.
- **`seed`:** a `dice` applet whose seeded bytes `62 1F 46 6F` were confirmed to be the same on the interpreter, the Python VM and the C VM (clang). The conformance README defines `seed` for the reference platform.
- **Running:** VS Code, a shell loop for CI, and the backends. The vault's chapter 8 scenario passed on all four: `interp`, `pyvm`, `cvm-clang` and `cvm-msvc`.
- **A planted bug:** the digit loop starting at 1. Run against a copy of the vault, it fails as the chapter shows: `err app 4` for `err app 1`. The `pin-format` scenario is checked against the real vault. The debugger steps are written from the extension's README, and left to the user's review.
- **The image:** the `clc build` summary and a `clc disasm` excerpt, taken from the prototype vault.

**Chapter 9, first review (user):**
- The shell loop for CI is gone: the guide must not assume a host shell or system. The text now says that `clc run`'s exit code lets any script or CI job run the suite.
- No compiler names, and no C VM build pointer, in the guide. The C VM can be built with any modern toolchain, and its build process is being reworked separately.
- The advice to run on every backend is gone. The backends are tested to agree, so one is enough for an applet's tests, and the default Python VM is the natural choice. The exercise to run on all backends was removed.
