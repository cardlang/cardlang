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
