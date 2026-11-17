# 2. Lexical structure

CardLang Language Specification, Draft 0.1. Chapter status: **draft complete** (SP1).

This chapter defines how the text of each source file is divided into tokens. It does not say where tokens may appear: that is the syntax, given in chapters 3–12 and the syntactic part of [Annex A](annex-A-grammar.md). Integer literals get their types in chapter 6. The complete lexical grammar is Annex A §A.1, and the grammar fragments in this chapter repeat parts of it.

Rule format, status tags and notation are defined in chapter 1. A rule marked *Derivation* follows necessarily from the agreed text it names (chapter 1 §1.4: such rules add no new decision).

## 2.1 Source text

**LEX-1 [Agreed]** A CardLang source file has the extension `.card`. The build configuration supplies the list of source files that make up an application (chapter 3).
*Sources: D-023, D-401; DN §3.0, §4.1.*

**LEX-2 [Agreed]** A source file is encoded in UTF-8. A file containing a byte sequence that is not valid UTF-8 is a compilation error (**CE-LEX-1**).
*Sources: D-023; DN §3.0.* *Derivation: "Source files are UTF-8" (DN §3.0).*

**LEX-3 [Agreed]** Characters outside the ASCII range (code points above `#x7F`) may appear only inside comments. Anywhere else they are a compilation error (**CE-LEX-2**). The only exception is the byte-order mark allowed by LEX-4.
*Sources: D-023, D-304; DN §3.0.* *Derivation: "Identifiers and language tokens remain ASCII"; only comments "may contain Unicode".*

**LEX-4 [Agreed]** A file may begin with a UTF-8 byte-order mark (U+FEFF, encoded as `EF BB BF`). It is ignored. A U+FEFF anywhere else is subject to LEX-3.
*Sources: D-423 (OI-23).*

**LEX-5 [Agreed]** A *line break* is a carriage return followed by a line feed (CRLF), a line feed (LF) on its own, or a carriage return (CR) on its own. CRLF counts as one line break. Line breaks end line comments (LEX-7) and separate tokens (LEX-6). Implementations count them when reporting the line of a diagnostic.
*Sources: D-423 (OI-23); D-311.*

## 2.2 Whitespace and comments

**LEX-6 [Agreed]** *Whitespace* is the space character (`#x20`), the horizontal tab (`#x09`) and line breaks. Whitespace and comments separate tokens and have no other meaning: indentation and line structure are not significant. Outside a comment, a character that is not whitespace and cannot begin a token under §2.3 is a compilation error (**CE-LEX-2**). This includes every other control character, and characters with no meaning in CardLang such as `#`, `"`, `'`, `?`, `@`, `$` and `` ` ``.
*Sources: D-305, D-312; DN §3.0.* *Derivation: whitespace is exactly "spaces, tabs and line breaks"; language tokens are the ones this chapter lists.*

**LEX-7 [Agreed]** A *line comment* starts with `//` and runs to the next line break, or to the end of the file. The line break is not part of the comment.
*Sources: D-306; DN §3.0.*

**LEX-8 [Agreed]** A *block comment* starts with `/*` and ends at the first following `*/`. Block comments do not nest. A block comment that is still open at the end of its file is a compilation error (**CE-LEX-3**).
*Sources: D-306; DN §3.0.*

**LEX-9 [Agreed]** Inside a comment, the sequences `//` and `/*` have no special meaning. A line comment can contain `/*`, and a block comment can contain `//` and `/*`. Because comments do not nest, the first `*/` always ends a block comment. In `/* a /* b */ c */`, the comment ends after `b`, and ` c */` is source text.
*Sources: D-306; DN §3.0.* *Derivation: comments run to their terminator (LEX-7, LEX-8), and block comments do not nest.*

```
Whitespace    ::= #x20 | #x09 | LineBreak
LineBreak     ::= #x0D #x0A | #x0D | #x0A
LineComment   ::= '//' [^#x0A#x0D]*
BlockComment  ::= '/*' ( [^*] | '*'+ [^*/] )* '*'+ '/'
```

### Examples

*Valid:* line and block comments, Unicode inside comments, and comment markers inside comments. (conformance: `valid/lex-002-comments.card`)

```text
// Grüße: comments may contain Unicode. /* This does not open a block comment.
/* A block comment,
   spanning lines. // This is still inside the block comment. */
const LIMIT: u32 = 100; // A line comment after a declaration.
```

*Invalid:* a block comment that is never closed. **CE-LEX-3**. (conformance: `invalid/lex-102-unterminated-block-comment.card`)

```text
const A: u32 = 1;
/* This comment is never closed.
const B: u32 = 2;
```

*Invalid:* an attempt to nest block comments. The first `*/` closes the comment, and the remaining `tail */` is source text that matches no grammar rule. **CE-SYN-1**. (conformance: `invalid/lex-103-nested-block-comment.card`)

```text
/* outer /* inner */ tail */
const A: u32 = 1;
```

## 2.3 Token formation

**LEX-10 [Agreed]** The text of a file, after removing the optional byte-order mark, is divided into tokens from left to right. At each position, whitespace and comments are skipped. Then the **longest** character sequence that forms a token (an identifier, keyword, `_`, integer literal or punctuator) is taken as the next token. For example:

- `<=`, `->`, `=>`, `..`, `<<` and `>>` are each one token;
- `a<=b` is the three tokens `a`, `<=` and `b`;
- `0..16` is `0`, `..` and `16`.

A `//` or `/*` always starts a comment, never a division operator.
*Sources: D-424 (OI-24).*

**LEX-11 [Agreed]** Each source file is tokenized separately. No token or comment continues from the end of one file into the next. A line comment ends at the end of its file, and a block comment open at the end of its file is an error under LEX-8. Positions in diagnostics are reported by file and line.
*Sources: D-311; DN §3.0, §4.1.*

### Examples

*Valid:* tokens written without separating spaces. (conformance: `valid/lex-005-longest-match.card`)

```text
const LIMIT: u32 = 16;
const SMALL: bool = LIMIT<=32;
session buffer: u8[16];
function clear_buffer(){for index: u8 in 0..16{buffer[index]=0;}return Ok();}
function limit()->u32{return Ok(LIMIT);}
```

*Valid (two files):* the first file ends with a line comment and no final line break. The comment ends with the file, so the second file's declaration of `B` is not consumed. (conformance: `valid/lex-006-two-files/`)

```text
// file a.card (no line break after the comment)
const A: u32 = B; // the comment ends at the end of this file
```

```text
// file b.card
const B: u32 = 2;
```

*Invalid (two files):* a block comment opened in one file cannot be closed in the next. The first file fails under LEX-8 (**CE-LEX-3**), and the stray `*/` in the second file also fails to parse (**CE-SYN-1**). (conformance: `invalid/lex-112-comment-across-files/`)

```text
// file a.card
const A: u32 = 1;
/* opened in this file
```

```text
// file b.card
closed in this file */
const B: u32 = 2;
```

## 2.4 Identifiers, keywords and reserved names

**LEX-12 [Agreed]** An *identifier* is an ASCII letter (`A`–`Z`, `a`–`z`) or underscore, followed by zero or more ASCII letters, digits and underscores. The exceptions are a keyword (LEX-13) and a lone `_` (LEX-14). Identifiers are case-sensitive: `Account` and `account` are different identifiers. Escape sequences and non-ASCII letters are not part of identifiers (LEX-3). Naming conventions, such as capitalized type names, are style only.
*Sources: D-023, D-301, D-303; DN §3.0.*

**LEX-13 [Agreed]** The following 32 spellings are *keywords*. A keyword is never an identifier, so it cannot be used as the name of anything.

```text
abort      and        attempt    break      command    const      continue
else       enum       Err        errors     false      for        function
if         in         inout      match      not        Ok         or
persistent ref        require    return     session    struct     transaction
true       var        while      wipe
```

`true` and `false` are also the Boolean literals (LEX-21). Using a keyword where the grammar requires an identifier is **CE-SYN-1**.
*Sources: D-303, D-404 (OI-4), D-449 (OI-49); DN §3.0, §3.6.*

**LEX-14 [Agreed]** A lone underscore `_` is a token of its own, not an identifier. The syntax permits it only as the ignored pattern (chapter 9). Identifiers that merely contain or start with an underscore, such as `_x` or `__count`, are ordinary identifiers.
*Sources: D-302; DN §3.0.*

**LEX-15 [Agreed]** The following identifiers are *reserved*. Lexically they are ordinary identifiers, but chapter 3 forbids declaring or shadowing them:

- the compiler intrinsics `fill`, `convert`, `checked_convert`, `checked_add`, `checked_sub`, `checked_mul`, `checked_div`, `checked_rem`, `checked_neg`, `wrapping_add`, `wrapping_sub` and `wrapping_mul`;
- the conversion and byte-order intrinsics `truncate`, `encode_be`, `encode_le`, `decode_be` and `decode_le` (added by D-432);
- the array intrinsics `equal` and `compare` (added by D-448);
- the platform names `card` and `CardError`;
- any further platform names supplied by the platform specification (Annex B);
- the lifecycle-handler names `on_install` and `on_power_on` (added by D-422 and D-438). An application may declare a function with one of these names, which defines the handler (NAM-14, STA-7, STA-8).

`length` is not reserved and may be used as a field name.
*Sources: D-044, D-404 (OI-4), D-432 (OI-32), D-422 (OI-22), D-438 (OI-38), D-448 (OI-48); DN §4.2.*

**LEX-16 [Agreed]** The language sets no maximum length for identifiers. A tool may report a limit it cannot support, but it MUST NOT silently truncate or merge identifiers.
*Sources: D-424 (OI-24).*

```
Identifier  ::= ( IdentStart IdentChar* ) - ( Keyword | '_' )
IdentStart  ::= [A-Za-z_]
IdentChar   ::= [A-Za-z0-9_]
Underscore  ::= '_'
```

### Examples

*Valid:* identifier forms, including a leading underscore and mixed case. (conformance: `valid/lex-001-identifiers.card`)

```text
const counter: u32 = 1;
const account_balance: u32 = 2;
const _x: u8 = 3;
const MAX_ACCOUNTS: u16 = 16;
```

*Invalid:* a non-ASCII letter in an identifier. **CE-LEX-2**. (conformance: `invalid/lex-101-non-ascii-identifier.card`)

```text
const café: u32 = 1;
```

*Invalid:* a keyword used as a name. **CE-SYN-1**. (conformance: `invalid/lex-110-keyword-as-identifier.card`)

```text
const match: u8 = 1;
```

*Invalid:* a lone `_` used as a name. **CE-SYN-1**. (conformance: `invalid/lex-111-underscore-as-name.card`)

```text
const _: u8 = 1;
```

*Valid:* an identifier 333 characters long is accepted and is not truncated (LEX-16). (conformance: `valid/lex-009-long-identifier.card`)

## 2.5 Literals

**LEX-17 [Agreed]** An *integer literal* has one of three forms:

- **decimal:** one or more digits `0`–`9`;
- **hexadecimal:** the prefix `0x` followed by one or more hex digits `0`–`9`, `a`–`f` or `A`–`F`;
- **binary:** the prefix `0b` followed by one or more of the digits `0` and `1`.

Prefixes are lowercase only. Hex digits may be either case. A single underscore may separate two digits. An underscore may not lead, trail, appear twice in a row, or follow the prefix directly. A leading zero has no special meaning: `007` is decimal 7, not octal.
*Sources: D-036, D-307, D-308, D-414 (OI-14); DN §3.0.*

**LEX-18 [Agreed]** When a token begins with a digit, the lexer reads the *numeric run*: the longest sequence of ASCII letters, digits and underscores starting at that position. The whole numeric run must match one of the forms in LEX-17. Otherwise it is a compilation error (**CE-LEX-4**). This rule rejects, among others:

- `1__0`, `1_` and `0x_FF` (underscore placement);
- `0x` (prefix without digits);
- `0b102` and `0xG1` (digits outside the base);
- `0XFF` (uppercase prefix);
- `12ab` and `10u8` (letters after a decimal number, so no type suffixes).

*Sources: D-424 (OI-24), D-414 (OI-14), D-036.*

**LEX-19 [Agreed]** The value of an integer literal is the mathematical integer its digits denote in its base, with underscores ignored. The lexer places no limit on its magnitude. Whether the value fits is checked when the literal is typed against its expected type (chapter 6). For example, `300` is a valid token, and `var x: u8 = 300;` is a typing error, not a lexical one.
*Sources: D-414 (OI-14), D-084; DN §3.3.*

**LEX-20 [Agreed]** There is no negative integer literal. `-128` is the unary operator `-` followed by the literal `128`. Chapter 6 defines how such an expression is accepted in a context like `i8`, where `128` alone would not fit.
*Sources: D-309; DN §3.0, §6.5.*

**LEX-21 [Agreed]** The Boolean literals are exactly the keywords `true` and `false`. CardLang has no string, character, floating-point or null literals.
*Sources: D-310; DN §3.0.*

```
IntegerLiteral ::= DecimalLiteral | HexLiteral | BinaryLiteral
DecimalLiteral ::= Digit ( '_'? Digit )*
HexLiteral     ::= '0x' HexDigit ( '_'? HexDigit )*
BinaryLiteral  ::= '0b' BinDigit ( '_'? BinDigit )*
Digit          ::= [0-9]
HexDigit       ::= [0-9a-fA-F]
BinDigit       ::= [01]
BooleanLiteral ::= 'true' | 'false'
```

### Examples

*Valid:* the literal forms, including separators, mixed-case hex digits and a leading zero. (conformance: `valid/lex-003-integer-literals.card`)

```text
const A: u32 = 123;
const B: u8 = 0xA5;
const C: u8 = 0b1010;
const D: u32 = 1_000_000;
const E: u32 = 0xDEAD_BEEF;
const F: u32 = 0xdead_beef;
const G: u8 = 007;
```

*Valid:* the Boolean literals. (conformance: `valid/lex-004-boolean-literals.card`)

```text
const ENABLED: bool = true;
const DISABLED: bool = false;
```

*Invalid:* each of the following is **CE-LEX-4**. Each is a separate test file.

| Literal | Reason | Conformance |
|---|---|---|
| `const A: u32 = 1__0;` | Consecutive underscores | `invalid/lex-104-literal-double-underscore.card` |
| `const A: u32 = 1_;` | Trailing underscore | `invalid/lex-105-literal-trailing-underscore.card` |
| `const A: u8 = 0x_FF;` | Underscore directly after the prefix | `invalid/lex-106-literal-underscore-after-prefix.card` |
| `const A: u8 = 0x;` | Prefix without digits | `invalid/lex-107-empty-hex-prefix.card` |
| `const A: u8 = 0b102;` | Digit outside the base | `invalid/lex-108-binary-digit-out-of-base.card` |
| `const A: u8 = 0XFF;` | Uppercase prefix | `invalid/lex-109-uppercase-prefix.card` |

## 2.6 Operators and punctuators

**LEX-22 [Agreed]** The *punctuators* are exactly the following 31 tokens:

```text
{   }   (   )   [   ]   ;   :   ,   .   ..
->  =>  =   ==  !=  <   <=  >   >=
+   -   *   /   %   ~   &   |   ^   <<  >>
```

Their uses are defined by the syntax in later chapters. In summary:

- `..` forms ranges and slices;
- `->` introduces a successful return type;
- `=>` separates a match pattern from its arm;
- `<` and `>` also enclose the type argument of the conversion intrinsics.

Sequences that are not tokens are not operators. For example, `+=` is the two tokens `+` and `=`, and `!` on its own is not a token (it cannot begin one, so it is **CE-LEX-2** under LEX-6). Boolean operators are the keywords `and`, `or` and `not`.
*Sources: D-024, D-102; DN §3.0, §3.5, §3.6, §3.7, §8.4.* *Derivation: the token set is exactly the punctuation used by the agreed syntax in the notes. Spellings the notes omit or defer, such as `?:`, `+=` and `++`, are not tokens.*

**LEX-23 [Agreed]** Line breaks are not tokens, and no semicolon is ever inserted automatically. Statements and declarations that need a semicolon must contain one (chapters 3 and 7).
*Sources: D-024, D-312; DN §3.0.*

**LEX-24 [Agreed]** CardLang has no preprocessor, macros, conditional compilation, textual inclusion or other textual substitution. Directive-like text such as `#include` has no meaning: its `#` is **CE-LEX-2** under LEX-6. Combining source files is done only through the build-supplied file list (LEX-1).
*Sources: D-037; DN §3.0.*

```
Punctuator ::= '{' | '}' | '(' | ')' | '[' | ']' | ';' | ':' | ',' | '.' | '..'
             | '->' | '=>' | '=' | '==' | '!=' | '<' | '<=' | '>' | '>='
             | '+' | '-' | '*' | '/' | '%' | '~' | '&' | '|' | '^' | '<<' | '>>'
```

### Examples

*Invalid:* a preprocessor directive. **CE-LEX-2**. (conformance: `invalid/lex-114-preprocessor-directive.card`)

```text
#include "state.card"
const A: u32 = 1;
```

*Invalid:* a line break does not end a declaration, because no semicolon is ever inserted (LEX-23). **CE-SYN-1**. (conformance: `invalid/lex-115-missing-semicolon.card`)

```text
const A: u32 = 1
const B: u32 = 2;
```

## 2.7 Byte-level examples

These tests check behavior that depends on the exact bytes of a file. They are generated as files, and their text cannot be shown faithfully in this document.

| Test | Content | Expected | Rules |
|---|---|---|---|
| `valid/lex-007-byte-order-mark.card` | A byte-order mark, then `const A: u32 = 1;` | ok | LEX-4 |
| `valid/lex-008-line-breaks.card` | Three declarations separated by CRLF, a lone LF and a lone CR. A line comment ends at the lone CR, so a later declaration that the first one refers to is not commented out | ok | LEX-5, LEX-7 |
| `invalid/lex-113-invalid-utf8.card` | A comment containing the byte `FF` | CE-LEX-1 | LEX-2 |

## 2.8 Lexical errors

| Class | Meaning | Rules |
|---|---|---|
| **CE-LEX-1** | The file is not valid UTF-8 | LEX-2 |
| **CE-LEX-2** | A character outside a comment is not permitted: non-ASCII, a control character other than whitespace, or a character that cannot begin a token | LEX-3, LEX-6, LEX-22, LEX-24 |
| **CE-LEX-3** | A block comment is still open at the end of its file | LEX-8, LEX-11 |
| **CE-LEX-4** | A numeric run does not match any integer literal form | LEX-17, LEX-18 |

Input that tokenizes successfully but matches no grammar production, such as a keyword used as a name, is **CE-SYN-1** (Annex A).
