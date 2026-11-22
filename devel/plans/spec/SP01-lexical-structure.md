# SP1 — Lexical structure: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 2 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/02-lexical-structure.md` | Source text and encoding, line breaks, whitespace, comments, identifiers, keywords and reserved names, literals, operators and punctuators, how tokens are formed, and file boundaries |
| `spec/annex-A-grammar.md` (lexical part) | The complete lexical grammar in W3C-style EBNF, plus a placeholder section for the syntactic grammar, which later sub-plans fill in |
| `conformance/valid/lex-*`, `conformance/invalid/lex-*` | One test per chapter example |
| Register, Annex C, Annex D, 00-index | Body decisions D-301…, any new issues, the rule-coverage mapping, and the compile-error index |

**Out of scope:**

- Where tokens may appear (syntax): chapters 3–12 and the syntactic part of Annex A.
- How integer literals get their types, including accepting `-128` in an `i8` context: chapter 6 (SP5). Chapter 2 only states that there is no negative-literal token.
- Name declaration and shadowing of reserved names: chapter 3 (SP2). Chapter 2 only lists the reserved spellings.

## 2. Sources

- **DN sections:** §3.0 (all lexical subsections), §3.3 (literal forms), §3.5 (operator spellings), §3.6 (`abort` is reserved), §4.1 (file boundaries), §6.5 (no negative-literal token).
- **Decisions:**
  - D-023 and D-401: `.card`, UTF-8 source, ASCII identifiers.
  - D-024: mandatory punctuation, token side only.
  - D-036: integer literal forms.
  - D-037: no preprocessor.
  - D-404: keywords and reserved names.
  - D-414: literal prefix, digit and magnitude rules.

### 2.1 Body-only decisions to register (D-301…)

These decisions are stated in the DN body but not in the §2 decision table. They are all agreed text from DN §3.0, unless another section is noted.

| ID | Decision |
|---|---|
| D-301 | Identifiers are case-sensitive ASCII. The first character is a letter or underscore; the following characters are letters, digits or underscores |
| D-302 | `_` alone is reserved for an ignored pattern |
| D-303 | There are no escaped or Unicode identifiers. Keywords cannot be identifiers |
| D-304 | Comments may contain Unicode. Identifiers and language tokens are ASCII |
| D-305 | Spaces, tabs and line breaks separate tokens. Indentation has no meaning |
| D-306 | Line comments `//` and block comments `/* */`. Block comments do not nest, and an unterminated block comment is a compilation error |
| D-307 | Integer literals are decimal, hexadecimal or binary. A leading zero does not mean octal |
| D-308 | Numeric underscores appear only between digits: never leading, trailing, consecutive or directly after a base prefix |
| D-309 | There is no negative-literal token: negative values use unary `-` (DN §3.0, §6.5) |
| D-310 | Boolean literals are exactly `true` and `false`. There are no string, character, floating-point or null literals |
| D-311 | File and line boundaries are preserved for diagnostics, and a trailing comment or token cannot consume the next file's text (DN §3.0, §4.1) |
| D-312 | There is no automatic semicolon insertion (DN §3.0) |

## 3. Policy for derived rules

Some rules follow necessarily from agreed text. For example, "source files are UTF-8" implies that bytes which are not valid UTF-8 are not valid source. Such rules are tagged **[Agreed]** and carry a one-line *Derivation:* note naming the text they follow from. A rule that needs a choice the text does not make is not derived. It gets an open issue (§5).

## 4. Planned rules (chapter 2)

**§2.1 Source text**

- **LEX-1** A source file has the `.card` extension (D-401, D-023). The build supplies the file list (cross-reference to chapter 3).
- **LEX-2** A source file is UTF-8. A byte sequence that is not valid UTF-8 is **CE-LEX-1**. This is derived.
- **LEX-3** Characters outside the ASCII range may appear only inside comments. Elsewhere they are **CE-LEX-2**. This is derived from D-304.
- **LEX-4** Byte-order mark handling [Open → OI-23].
- **LEX-5** Which character sequences count as line breaks: LF, CR and CRLF [Open → OI-23]. Line breaks matter only for ending `//` comments and for diagnostic positions.

**§2.2 Whitespace and comments**

- **LEX-6** Whitespace is space, horizontal tab and line break. No other control character is permitted outside comments (**CE-LEX-2**, derived from D-305). Whitespace separates tokens and has no other meaning.
- **LEX-7** A `//` comment runs to the end of the line.
- **LEX-8** A `/* */` comment runs to the first `*/`. Block comments do not nest. A block comment still open at the end of the file is **CE-LEX-3**.
- **LEX-9** Comment markers inside a comment have no effect: `//` inside a block comment, and `/*` inside either kind of comment.

**§2.3 Token formation**

- **LEX-10** The lexer always takes the longest possible token [Proposal → OI-24]. For example, `<=` is one token, not `<` followed by `=`; `..` is one token; and `->` is one token.
- **LEX-11** Each file is lexed separately. No token or comment spans two files (D-311).

**§2.4 Identifiers and reserved spellings**

- **LEX-12** Identifier form: an ASCII letter or `_`, followed by any number of letters, digits and `_` (D-301). Identifiers are case-sensitive.
- **LEX-13** The keyword list (D-404), including `Ok`, `Err`, `true` and `false`. A keyword is never an identifier.
- **LEX-14** `_` on its own is a separate token, not an identifier (D-302). Spellings such as `_x` are ordinary identifiers.
- **LEX-15** Reserved identifiers: the intrinsic names, `card` and `CardError` (D-404). They are lexically ordinary identifiers. Chapter 3 forbids declaring or shadowing them. Other platform-reserved names are supplied by the platform. `length` is not reserved.
- **LEX-16** Identifier length limit [Open → OI-24].

**§2.5 Literals**

- **LEX-17** Decimal, hexadecimal (`0x`) and binary (`0b`) forms, with `_` separators placed only between digits. Prefixes are lowercase; hex digits may be either case (D-414).
- **LEX-18** Numeric-run rule [Proposal → OI-24]: a numeric literal token is the longest run of ASCII letters, digits and `_` that starts with a digit. The whole run must match one of the forms in LEX-17; otherwise it is **CE-LEX-4**. This rule is how OI-14's decision is implemented: `0x`, `0b2`, `0XFF`, `1_`, `1__0`, `0x_F` and `12ab` are all errors.
- **LEX-19** The value of a literal is a mathematical integer with no lexical limit on its size. Range checking happens during typing at the literal's expected type (D-414, cross-reference to chapter 6).
- **LEX-20** There is no negative-literal token (D-309). A leading zero does not mean octal (D-307).
- **LEX-21** `true` and `false` are the only Boolean literals. There are no string, character, floating-point or null literals (D-310).

**§2.6 Operators and punctuators**

- **LEX-22** The complete token set, gathered from the notes' syntax: `{ } ( ) [ ] ; : , . .. -> => = == != < <= > >= + - * / % ~ & | ^ << >>`. SP14 checks that every later chapter uses only tokens from this list.
- **LEX-23** Semicolons are never inserted automatically. Line breaks are not tokens (D-312).

**§2.7 Lexical errors** (a summary table)

| Class | Meaning |
|---|---|
| CE-LEX-1 | Invalid UTF-8 |
| CE-LEX-2 | Character not permitted outside a comment |
| CE-LEX-3 | Unterminated block comment |
| CE-LEX-4 | Malformed numeric literal |

## 5. New open issues

| ID | Question | Recommendation |
|---|---|---|
| **OI-23** Source text details | (1) Is a UTF-8 byte-order mark at the start of a file permitted and ignored, or an error? (2) Are LF, CR and CRLF all line breaks? | (1) Permitted and ignored, because common Windows editors write one. (2) All three, with CRLF counting as one line break |
| **OI-24** Token formation and limits | (1) Adopt the longest-match rule (LEX-10)? (2) Adopt the numeric-run rule (LEX-18) as the way to implement the OI-14 decision? (3) Is there a maximum identifier length? | (1) Yes. (2) Yes. (3) No language limit. A tool may report one, but must not silently truncate |

**Decided 2026-11-15:** you accepted both recommendations in full. Step 1 records OI-23 and OI-24 as resolved, as decisions D-423 and D-424. LEX-4, LEX-5, LEX-10, LEX-16 and LEX-18 are therefore written as **[Agreed]**, citing those decisions, instead of [Open] or [Proposal].

## 6. Change to chapter 1 (SYN prefix)

Some invalid programs break the grammar without breaking any chapter rule. Examples: a keyword used as a variable name, or the stray `*/` left over when someone tries to nest block comments. These need a compile-error class. I propose a new prefix **`SYN`**, owned by Annex A: **CE-SYN-1** means "no derivation of the grammar exists". SP1 adds `SYN` to the prefix table in chapter 1 §1.5.

## 7. Grammar (Annex A, lexical part)

The productions are `Token`, `Identifier`, `Keyword`, `IntegerLiteral` (`DecimalLiteral`, `HexLiteral`, `BinaryLiteral`), `BooleanLiteral`, `Punctuator`, `Whitespace`, `LineBreak`, `LineComment` and `BlockComment`. The digit-separator rule is written into the grammar itself:

```
DecimalLiteral ::= Digit ( '_'? Digit )*
HexLiteral     ::= '0x' HexDigit ( '_'? HexDigit )*
BinaryLiteral  ::= '0b' BinDigit ( '_'? BinDigit )*
```

The syntactic part of Annex A starts as an empty skeleton, with section headers for SP2–SP11.

## 8. Examples and conformance tests

All tests use `kind: fragment` unless marked otherwise.

**Valid**

| Test | Shows |
|---|---|
| `valid/lex-001-identifiers.card` | `counter`, `account_balance`, `_x` and `MAX_ACCOUNTS` as declaration names |
| `valid/lex-002-comments.card` | A line comment, a multi-line block comment, Unicode inside a comment, and `/*` inside a line comment |
| `valid/lex-003-integer-literals.card` | `123`, `0xA5`, `0b1010`, `1_000_000`, `0xDEAD_BEEF`, `0xdead_beef`, and `007` (decimal 7) |
| `valid/lex-004-boolean-literals.card` | `true` and `false` |
| `valid/lex-005-longest-match.card` | `a<=b`, a range `0..16` and an arrow `->`, written without spaces |
| `valid/lex-006-two-files/` | Multi-file test: a line comment at the very end of file 1 does not swallow file 2's first declaration |

**Invalid**

| Test | Expected error | Shows |
|---|---|---|
| `invalid/lex-101-non-ascii-identifier.card` | CE-LEX-2 | A non-ASCII letter in an identifier |
| `invalid/lex-102-unterminated-block-comment.card` | CE-LEX-3 | A block comment never closed |
| `invalid/lex-103-nested-block-comment.card` | CE-SYN-1 | The stray `*/` left after the first `*/` |
| `invalid/lex-104-literal-double-underscore.card` | CE-LEX-4 | `1__0` |
| `invalid/lex-105-literal-trailing-underscore.card` | CE-LEX-4 | `1_` |
| `invalid/lex-106-literal-underscore-after-prefix.card` | CE-LEX-4 | `0x_FF` |
| `invalid/lex-107-empty-hex-prefix.card` | CE-LEX-4 | `0x` |
| `invalid/lex-108-binary-digit-out-of-base.card` | CE-LEX-4 | `0b102` |
| `invalid/lex-109-uppercase-prefix.card` | CE-LEX-4 | `0XFF` |
| `invalid/lex-110-keyword-as-identifier.card` | CE-SYN-1 | `var match: u8;` |
| `invalid/lex-111-underscore-as-name.card` | CE-SYN-1 | `_` used as a declaration name |
| `invalid/lex-112-comment-across-files/` | CE-LEX-3 | Multi-file test: file 1 opens a block comment that file 2 tries to close |

**Not tested here:** an out-of-range literal such as `var x: u8 = 300;` is a typing error, so its test belongs to SP5. Chapter 2 refers to it.

**Open dependency:** a fragment test still needs the harness to add a `command`. Because the entry point is now the single `command` declaration (D-405), the scaffold can be fixed now. I'll add it to `conformance/README.md` in this sub-plan:

```
command scaffold_entry(request: ref u8[], response: inout u8[]) -> u32 {
    return Ok(0);
}
```

## 9. Steps

1. Register D-301…D-312. Add OI-23 and OI-24 to Annex C. Add `SYN` to chapter 1.
2. Write chapter 2: rules, a grammar fragment per section, and examples.
3. Write the lexical part of Annex A and the syntactic skeleton.
4. Write the 18 conformance tests and fix the fragment scaffold in `conformance/README.md`.
5. Update Annex D (D-023, D-024 token side, D-036, D-037, D-301…D-312, D-401, D-404, D-414 → LEX rules), the compile-error index and the status summary in 00-index, and the register's "Implemented by" column.
6. Run the exit checklist.

## 10. Exit checklist

- Every LEX rule has a tag and a sources line. Every [Proposal] or [Open] rule cites OI-23 or OI-24.
- Each derived rule has a *Derivation:* note.
- Every example in chapter 2 has a test file with valid metadata, and every test names an existing rule and error class.
- Every lexical form used in DN §3.0 examples can be derived from the Annex A lexical grammar.
- Every token used in the DN examples appears in the LEX-22 punctuator set or is an identifier, keyword or literal. Check this by scanning the DN code blocks.
- Annex D rows for the listed decisions are updated. Nothing about typing or syntax is specified in chapter 2.

## 11. Choices made in this sub-plan

These are open for redirection:

- The derived-rule policy (§3).
- The new `SYN` prefix (§6).
- The OI-23 and OI-24 recommendations, which are shown in the chapter as [Open] or [Proposal] until you decide them.
- Fixing the fragment scaffold now rather than in SP11.
- Test numbering: 001–099 for valid tests, 101 onward for invalid tests.
