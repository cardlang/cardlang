# WP9 — Language ergonomics from the FIDO2 check: detailed sub-plan

Parent: `plans_and_notes/WP8-fido2-findings.md` (L1, L2, L4, L5, L6) and `plans_and_notes/draft-0.2-candidates.md` (items 5, 6, 8, 9, 10).
Status: decisions G1–G5 taken 2026-11-19 (§4). **Drafted 2026-11-19**: OI-53 to OI-57, rules LEX-25, EXP-55, STM-24, STM-25, OUT-21 and OUT-22, 15 tests including run-024, and the applet refactored (552 → 480 lines).

**Decided 2026-11-19.** You accepted every recommendation:

- **G1 (a):** `b"…"` byte strings, with the escapes `\"`, `\\` and `\xHH`.
- **G2 (a):** the pattern `Err(Set(code))`, which binds a `u16`.
- **G3 (a):** `attempt … else` maps every `Err`.
- **G4 (a):** `ignore` may discard payloads.
- **G5 (a):** all ten compound operators.

## 1. Scope and principle

Five language changes, chosen on 2026-11-19. L3 is deferred, and L7 dropped. **Every change must be implementable entirely in the compiler, adding nothing to the VM** (the "tiny VM" goal). Each one is rewritten into constructs that exist already:

| # | Change | Rewritten into | New tokens or keywords |
|---|---|---|---|
| L1 | Byte-string literals | A constant `u8[N]` array list | A literal form |
| L2 | Reading an application error's code | An outcome `match` over the members of the error set, with a `u16` constant per arm | None (a pattern form) |
| L4 | `attempt c else E.M` | A `match` whose `Err` arm returns or aborts with `E.M` | None (`else` exists) |
| L5 | `ignore c;` | A `match` with empty arms | The keyword `ignore` |
| L6 | Compound assignment `+=`, … | `p = p op e`, with the place evaluated once | Ten punctuators |

Each change becomes an open issue in Annex C (OI-53 to OI-57) and a decision (D-453 to D-457), with rules in the chapters, grammar in Annex A, tests, and checker and interpreter support. At the end, the FIDO2 applet is refactored to use them, and its size and the counts in the findings report are measured again.

## 2. The changes

### 2.1 L1 — Byte-string literals (G1)

```text
const KEY_ID: u8[2] = b"id";
const PUBLIC_KEY: u8[10] = b"public-key";
var version: u8[8] = b"FIDO_2_0";
```

- **Lexical rule (chapter 2).** A byte-string literal is `b"`, then characters, then `"`. A character is printable ASCII (`0x20`–`0x7E`) other than `"` and `\`, or one of the escapes `\"`, `\\` and `\xHH`. A literal may not span lines. An unterminated literal, or an invalid escape, is CE-LEX-4 or a new CE-LEX class.
- **Typing (chapter 6).** Like an array list (EXP-43), it has no type of its own. It checks against `u8[N]`, where `N` is the number of bytes. A different `N` is CE-EXP-11. No expected type is CE-EXP-10. It is a constant expression (chapter 5).
- **Positions.** It may appear wherever an array list may, including as the right side of a slice assignment (FUN-24). Passing it as a `ref` argument stays CE-FUN-3, because it is not storage. Declare a `const` instead.
- **No string type.** There is no string type, no text encoding, and no length or comparison operator of its own. The literal is just bytes.

### 2.2 L2 — The code of an application error (G2)

The original restriction (OUT-14, D-028) keeps errors from becoming storable values. **Recommendation:** a pattern that matches *any member of the application's error set*, and binds its *code*, a plain `u16`, never an error value:

```text
match ctap(ref request[4..request.length], inout response) {
    Ok(count) => { return Ok(count); }
    Err(IsoError(code)) => {            // any IsoError member; code: u16
        response[0] = truncate<u8>(code);
        return Ok(1);
    }
    Err(error) => { return Err(error); }   // platform errors propagate unchanged
}
```

- **Matching.** The pattern `Err(Set(name))` matches every member of the error set `Set`, and binds `name` as a read-only `u16` local holding the member's code. Platform errors (`CardError`) never match it.
- **Ordering.** Its position among the arms follows the existing rules (OUT-11 to OUT-13): specific members first, then the set pattern, then a catch-all.
- **OUT-14 is unchanged.** Error bindings still cannot be inspected.
- **Compiler cost.** The compiler expands it to one arm per member, each binding a constant, so the VM is unaffected.

The alternative is an intrinsic `code_of(e) -> u16` on an error binding. That is simpler to describe, but it relaxes OUT-14, and leaves open what it returns for a platform error.

### 2.3 L4 — `attempt c else E.M` (G3)

```text
var head: CborHead = attempt card.cbor.head(ref data[at..end]) else IsoError.CtapInvalidCbor;
attempt card.key.import(TEMP_KEY, spec, ref derived) else IsoError.CtapOther;
```

- **Meaning.** As `attempt c` (OUT-10), except that on `Err` the enclosing function returns `Err(E.M)` instead of the original error. Inside a transaction it aborts with `E.M` instead (TXN-18).
- **The operand.** `E.M` follows `require`'s operand rule (STM-19): a qualified member of the application's error set. A `CardError` member is CE-OUT-3.
- **Forms.** It has both the expression and the statement form of `attempt`. Traps are never caught.
- **What it maps** (G3): every `Err`, both application and platform errors.

### 2.4 L5 — `ignore c;` (G4)

```text
ignore card.key.delete(TEMP_KEY);
```

- **Meaning.** `ignore c;` is a statement. `c` must be a call that produces an outcome. The call is evaluated, and its outcome is discarded, whatever it is. Traps are not affected.
- **Payloads** (G4): allowed or not.
- **Placement.** It is valid anywhere a statement is, including inside a transaction, because it never leaves the block.
- **A new keyword:** `ignore`. That makes 33 keywords.

### 2.5 L6 — Compound assignment (G5)

```text
at += n;
sign_count += 1;
flags |= 0x40;
```

- **Operators** (G5): `+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `<<=` and `>>=`. They are new punctuators (LEX-22, by longest match), so `+ =` with a space stays two tokens and does not derive.
- **Meaning.** `p op= e;` evaluates the place's path once (STM-9 step 1), reads the current value, evaluates `e`, applies `op` with the usual checked semantics (overflow traps, EXP-23), and stores the result. The place is never evaluated twice, so `a[next()] += 1` calls `next()` once. Calls inside index expressions are already restricted by the existing rules.
- **Typing.** `e` checks against the place's type, as the right operand of `op` would (chapter 6).
- **Persistence.** A compound assignment to persistent storage is one atomic persistent assignment (STA-11).
- **What stays out.** It is still a statement, never an expression (STM-6), and there is no `++`.

## 3. Work steps

1. Record OI-53 to OI-57 and D-453 to D-457.
2. Write the rules:
   - chapter 2: L1 tokens, L6 punctuators, the `ignore` keyword;
   - chapter 6: L1 typing;
   - chapter 7: L5, L6;
   - chapter 9: L2, L4;
   - chapter 11: L4 in transactions;
   - Annex A.
3. Tools: `lexcheck` (tokens), `expcheck` (L1), `stmcheck` (L5, L6), `outcheck` (L2, L4), the interpreter, and `grammar.py`, which reads Annex A automatically.
4. Tests, from a new `wp9_tests.py`: valid and invalid tests for each change, plus a runtime test covering L2 translation, L4 mapping inside and outside transactions, L5 discarding an `Err`, L6 checked overflow, and single evaluation of the place.
5. Refactor `examples/fido2` to use the changes. Re-run `check_fido2.py`, and add a "before and after" section to the findings report.
6. Run all checks, and update `draft-0.2-candidates.md`.

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| G1 | Byte-string syntax | (a) `b"…"`, printable ASCII, with the escapes `\"`, `\\` and `\xHH`; (b) plain `"…"`; (c) `b"…"` without escapes | (a). The `b` keeps plain `"…"` free for a possible future text type, and `\xHH` covers non-ASCII bytes |
| G2 | The form of L2 | (a) the pattern `Err(Set(code))`, which binds a `u16`; (b) the intrinsic `code_of(e)` on an error binding | (a). OUT-14 stays intact, and the category is explicit |
| G3 | What `attempt … else` maps | (a) every `Err`; (b) only platform errors | (a) |
| G4 | `ignore` on calls with a payload | (a) allowed, so the payload is discarded too; (b) only calls without a payload | (a). Discarding is the explicit purpose of the keyword |
| G5 | The compound operators | (a) all arithmetic, bitwise and shift operators (10); (b) only `+=` and `-=` | (a) |
