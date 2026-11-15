# SP5 — Expressions: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 6 is not written until you approve this plan.

## 1. Scope

This is the largest chapter.

| Output | Content |
|---|---|
| `spec/06-expressions.md` | Expression grammar; contextual typing of literals (bidirectional judgments); every operator's typing and evaluation; the grouping rule; evaluation order and short-circuiting; arithmetic edge cases and traps; checked and wrapping intrinsics; `convert` and `checked_convert`; indexing and `.length`; field access; array lists, `fill` and structure constructors; call expressions and the nested-call ban; where `attempt` may appear |
| `spec/annex-A-grammar.md` §A.2.4 | `Expression` and everything beneath it |
| `conformance/valid/exp-*`, `conformance/invalid/exp-*` | One test per example, plus the typing tests deferred from SP3 and SP4 |
| Register, Annex C, Annex D, 00-index | Body decisions D-333…, new issues, rule coverage, the CE-EXP index, and chapter 5's forward references to chapter 6 replaced with rule IDs |

**Out of scope:**

| Topic | Where |
|---|---|
| Statements: assignment (including destination evaluation order), `var`, control flow | Chapter 7 (SP6) |
| Parameter modes, call-site `ref`/`inout`, argument preparation, aliasing, slice typing and where slices may appear | Chapter 8 (SP7). Chapter 6 parses slices and call-site modes, and defers their meaning |
| What an outcome is, how it may be consumed, and the meaning of `attempt` | Chapter 9 (SP8). Chapter 6 types a call as `Outcome(T)` and says where `attempt` may appear (D-408) |
| The final catalog of trap kinds | Chapter 13 (SP12). Chapter 6 uses the agreed placeholder names (D-415) |

## 2. Sources

- **DN sections:** §3.2, §3.3, §3.4, §3.5, §3.7 (no nested calls in arguments), §3.11 (enum equality), §6.2, §6.5, §8.1, §8.2 (`fill` evaluated once), §8.3, §9.3.
- **Decisions:**

| Decisions | Topic |
|---|---|
| D-027 | No nested calls in arguments |
| D-058 | Overflow handling |
| D-061–D-064 | `.length`, index types, `fill`/list, no `zero` keyword |
| D-070, D-071 | Constructors |
| D-079 | `fill` |
| D-081–D-092 | Conversions, literal typing, no widening, edge cases, checked and wrapping intrinsics |
| D-101–D-104 | No truncating cast, grouping, chains, evaluation order |
| D-130 | Complete construction |
| D-408 | `attempt` positions |
| D-410 | Slice positions (parse only) |
| D-414 | Literal magnitude |
| D-415 | Trap and error placeholder names |

### 2.1 Body-only decisions to register (D-333…)

| ID | Decision | Source |
|---|---|---|
| D-333 | A typed operand supplies the expected type for an untyped literal operand, whichever side it is on. A Boolean result expectation alone does not establish integer widths. Missing or ambiguous context is an error | DN §3.3 |
| D-334 | A minimum signed value such as `-128` is accepted in an `i8` context. Negating a minimum signed runtime value traps | DN §3.0, §6.5 |
| D-335 | Equality applies to matching integer types, `bool` and the same enum. There is no automatic array or structure equality | DN §3.5, §3.11, §8.2, §9.3 |
| D-336 | Bitwise operators accept only unsigned operands of matching types. Shifts take an unsigned left operand and a `u8` count | DN §3.5 |
| D-337 | Calls, indexing and field access form operands. Unary operators need no parentheses because a binary operator is present | DN §3.5 |
| D-338 | Optimizations preserve evaluation, short-circuiting and failure behavior. Checks are removed only when proved unnecessary, and semantics do not depend on build mode | DN §3.5, §6.5 |
| D-339 | Runtime `.length` still evaluates its receiver: calls, errors and bounds checks happen | DN §8.1 |
| D-340 | `fill` needs an expected fixed-array type from context. It evaluates its argument once, copies the value into every element, and captures the original value when filling from itself | DN §8.3 |
| D-341 | Array lists must have exactly the destination's length. There is no padding or truncation | DN §8 |
| D-342 | Conversion between integers and bytes is explicit, separate from numeric conversion, and must state byte order | DN §3.4 |

## 3. Key design points

1. **Bidirectional typing.** Literals only *check* against an expected type; they never synthesize one. A binary operator synthesizes its type from a typed operand when it has one, and otherwise checks against the expected type. Indexing gives `u32` context to a literal-only index. A shift count gets `u8` context. A comparison with no typed operand has no integer context, so it is **CE-EXP** (D-333).
2. **Grammar.** No precedence levels: a flat `Unary (BinaryOperator Unary)*` sequence. A rule then requires every binary operator at one grouping level to be the same, and forbids comparison chains entirely. Unary operators bind to their own operand. Each parenthesized expression, index bracket and argument list starts a new grouping level.
3. **Type-argument syntax.** `<` after `convert` or `checked_convert` opens a type argument. Both names are reserved (LEX-15), so this never conflicts with a comparison.
4. **Calls synthesize `Outcome(T)`, a specification-only type.** Operators, initializers and arguments require value types, so an outcome there is a type error. Chapter 9 defines the forms that consume outcomes.
5. **Traps use the D-415 placeholders.** Underflow versus overflow classification is OI-31.

## 4. Planned rules (chapter 6), in outline

- **§6.1 Grammar and grouping (EXP-1 to EXP-5).** Expression forms; the mixed-operator rule; same-operator chains associate left to right; comparison chains are forbidden; unary binding.
- **§6.2 Contextual typing (EXP-6 to EXP-12).**
  - Literal checking and range (D-414).
  - The negative-minimum rule.
  - Sources of expected types: initializers, arguments, `return Ok` payloads, range bounds, aggregate elements and fields, assignment destinations, indices (`u32`), shift counts (`u8`).
  - Typed operands supply the type.
  - No default type.
  - No implicit conversion (TYP-5).
- **§6.3 Operator typing (EXP-13 to EXP-19).**
  - Arithmetic.
  - Ordering comparisons.
  - Equality (D-335).
  - Boolean `and`, `or`, `not`.
  - Bitwise operators and `~`, unsigned only.
  - Shifts.
  - Unary `-`, signed only.
- **§6.4 Evaluation order (EXP-20 to EXP-22).** Left to right, each operand once; short-circuiting; optimization limits (D-338).
- **§6.5 Arithmetic semantics and traps (EXP-23 to EXP-28).**
  - Checked intermediate results and no widening.
  - Truncating division and the sign of a remainder.
  - Division or remainder by zero traps.
  - The minimum signed value divided by −1 traps, and remainder −1 gives 0.
  - Shift semantics, and a count of at least the width traps.
  - Unrepresentable negation traps.
  - Trap kinds per OI-31.
- **§6.6 Checked and wrapping intrinsics (EXP-29, EXP-30).** The checked family returns `Outcome(T)`, with placeholder `CardError` members. The wrapping family computes modulo 2^N using two's complement.
- **§6.7 Conversions (EXP-31 to EXP-33).**
  - `convert<T>` requires a source type that is known independently and fits completely; the result is a direct value.
  - `checked_convert<T>` returns `Outcome(T)` with `CardError.ConversionRange`.
  - Only integer-to-integer; no truncating cast (D-101).
- **§6.8 Indexing, `.length` and fields (EXP-34 to EXP-37).**
  - Index types; bounds checks (`TRAP-BOUNDS`).
  - `.length` is `u32`, read-only, and evaluates its receiver (D-339).
  - Field lookup is decided by the receiver's type.
  - Slices are parsed here, and their meaning is in chapter 8.
- **§6.9 Aggregate construction (EXP-38 to EXP-41).**
  - Array lists: checked against an expected type, exact length.
  - `fill` (D-340).
  - Structure constructors: named, every field once, evaluated in written order, a direct value.
  - Values are independent copies.
- **§6.10 Calls (EXP-42 to EXP-45).**
  - Ordinary, intrinsic and platform (`card.…`) calls.
  - Positional arguments, each checked against its parameter type.
  - A call synthesizes `Outcome(T)`.
  - No calls inside arguments, including intrinsics and `attempt` (D-027).
  - `Ok`/`Err` in a return are not calls.
  - Calling the `command` is forbidden (chapter 12).
- **§6.11 `attempt` positions (EXP-46).** D-408. Its meaning is in chapter 9.
- **§6.12 Bytes and integers (EXP-47).** D-342, plus OI-32.

Error classes CE-EXP-1 to about CE-EXP-14, covering:

- type mismatch;
- literal out of range;
- missing literal context;
- mixed operators;
- comparison chain;
- operator not applicable to the type;
- nested call;
- invalid `convert`;
- invalid index type;
- `fill` without an expected type;
- wrong list length;
- constructor field errors;
- unknown field or member access;
- an outcome used as a value.

The numbers are fixed when the chapter is drafted.

## 5. New open issues

| ID | Question | Options | Recommendation |
|---|---|---|---|
| **OI-30** Structure constructor in conditions | `if ready { … }` and `if Point { … }` look alike. When `ready` is a `bool`, `{` opens the block. When the name is a structure type, `{` would start a constructor. How does the grammar decide? | (a) A structure constructor directly in the condition of `if` or `while`, in a `for` range bound, or in a `match` scrutinee must be parenthesized. Grammar only, as in Rust. (b) Decide by name resolution: `Name {` is a constructor exactly when `Name` is a structure type. This is deterministic, because names are unique and can't be shadowed | (a). Parsing stays independent of name resolution, and the restriction rarely matters, because a constructor can never be a `bool` condition anyway |
| **OI-31** Overflow versus underflow | DN §6.2 lists "proposed arithmetic failure categories": above maximum is Overflow; below minimum, including unsigned subtraction below zero, is Underflow. Adopt this for `TRAP-OVERFLOW`/`TRAP-UNDERFLOW` and for `CardError.Overflow`/`Underflow`? Where do the minimum signed value divided by −1, and unrepresentable negation, go? | (a) Adopt the DN table. The minimum divided by −1 is overflow, because the result is above the maximum. Negation of the minimum gets its own `TRAP-NEGATION`, already in D-415; `checked_neg` returns `CardError.Overflow`. (b) A single overflow kind for everything | (a) |
| **OI-32** Integer ↔ byte conversion | DN §3.4 says encoding integers as bytes is explicit, and that "encoding API names and any future deliberately lossy byte-extraction operations remain open". Without anything new, taking the low byte of a `u32` needs `checked_convert<u8>(x & 0xFF)` plus a `match` whose error arm can never run | (a) Nothing new in Draft 0.1: use shifts, masks and `checked_convert`. (b) Add a truncating intrinsic, for example `truncate<u8>(x)`, which keeps the low bits; a deliberate, named lossy operation. (c) Add byte-order intrinsics, for example `encode_be(value, inout bytes)` / `decode_be<T>(ref bytes)`, plus `_le` versions, for `u16` and `u32`. (d) Both (b) and (c) | This is a language-design choice the notes left open, so I have no firm recommendation. (b) is the smallest addition that removes the impossible error arm. (c) matters most for APDU parsing |

**Decided 2026-11-15** (to be recorded as D-430, D-431 and D-432):

- **OI-30:** a structure constructor directly in an `if`/`while` condition, a `for` range bound or a `match` scrutinee must be parenthesized. It is a grammar rule.
- **OI-31:**
  - Above the maximum is Overflow, and below the minimum is Underflow. This includes unsigned subtraction below zero.
  - The minimum signed value divided by −1 is Overflow.
  - Negating the minimum signed value is `TRAP-NEGATION`, and `checked_neg` returns `CardError.Overflow`.
- **OI-32:** add both facilities. Both are direct-value intrinsics, and both are excluded from constant expressions initially:
  - `truncate<T>(x)`: any integer type to any integer type. The source type must be known independently. The result is the low bits of `x` reinterpreted as `T`, two's complement for signed types. It never fails.
  - `encode_be(x)` and `encode_le(x)`: `T` is one of `u16`, `u32`, `i16` or `i32`. Each returns a direct `u8[N]` value, where `N` is the width of `T` in bytes.
  - `decode_be<T>(ref bytes)` and `decode_le<T>(ref bytes)`: each returns a direct `T`, and traps with `TRAP-BOUNDS` when `bytes.length != N`.

**Knock-on changes.** The new intrinsic names `truncate`, `encode_be`, `encode_le`, `decode_be` and `decode_le` are added to:

- the reserved names in LEX-15 and NAM-14;
- the exclusion list in CEX-5.

These are amendments to chapters 2, 3 and 5. Each is marked with a note that it was introduced by D-432.

## 6. Conformance tests (planned, about 55)

**Valid (about 20):**

- literal context from a declaration, an argument, `return Ok`, a range and an assignment;
- a typed operand on either side;
- `-128` in an `i8` context;
- same-operator chains;
- unary operators next to a binary operator;
- `convert` between every pair the notes list as guaranteed;
- equality on `bool` and on an enum;
- shifts with a `u8` count;
- a literal-only index;
- an index of type `u8` or `u16`;
- `.length` on a field;
- `fill` from a local, and from the array itself (`buffer = fill(buffer[0])`);
- a constructor with fields in a different order from the declaration;
- `wrapping_add`;
- `checked_add` inside a `match`;
- short-circuit guarded indexing.

**Invalid (about 30):**

- a type mismatch between `u16` and `u8` operands;
- literals `300` and `-1` in a `u8` context;
- `a + b * c`, `a + b - c`, `0 < x < y`, `a == b == c`, `flags & 0x03 == 0x01`, and `a and b or c`;
- `1 == 1` with no context;
- `convert` that narrows, and `convert<u32>(32)`;
- a signed index, and a `bool` index;
- an `i8` shift count;
- bitwise and unary `-` on unsigned operands where not allowed;
- ordering on `bool`;
- equality on structures and on arrays;
- `bool = 1` (from SP3);
- integer to enum (from SP3);
- assignment between two different structure types (from SP3);
- `const LARGE: u32 = SMALL` (from SP4);
- a nested `convert` (from SP4);
- nested calls in arguments (DN §3.7 examples);
- `balance + subtract(…)` (an outcome used as a value);
- a list too short and a list too long (DN §8);
- `fill` with no context;
- constructor errors: missing, unknown and duplicate fields;
- an unknown field;
- `buffer.length = 10`. This is an assignment, so it is tested in SP6 or here with an `also` field.

**Runtime tests** for traps, wrapping results, `min % -1` and short-circuiting are **listed now and written in SP12**, once the runtime test format exists.

## 7. Steps

1. Register D-333…D-342, add OI-30…OI-32, and record your decisions.
2. Write chapter 6, with grammar fragments, judgments and evaluation steps.
3. Fill in §A.2.4.
4. Generate the tests from the chapter.
5. Update the traceability, and replace chapter 5's chapter-6 references with rule IDs.
6. Run the checks:
   - Extend the scratchpad evaluator into an expression type checker: literal context, operator applicability, grouping, chains, nested calls, `convert` validity, index types, list lengths and constructor completeness.
   - Run it over all `exp-*` tests, all earlier valid tests, and every DN expression fragment that is self-contained.

## 8. Exit checklist

- Every EXP rule has a tag and sources. Every rule tied to OI-30, OI-31 or OI-32 is [Open] until you decide.
- Every DN §3.2, §3.3, §3.5, §6.5 and §8 code example maps to a test.
- The checker agrees with every test, and no earlier valid test regresses.
- Chapter 5's references to chapter 6 are resolved.

## 9. Choices made in this sub-plan

These are open for redirection:

- A flat binary grammar plus a grouping rule, rather than precedence levels.
- `Outcome(T)` as a specification-only type in typing rules.
- Shift counts get `u8` context.
- Assignment-destination context is included as a source of expected types. The DN table doesn't list it, but DN §3.3 implies it when it treats a mismatch with the destination type as an error.
- Runtime behavior tests are deferred to SP12.
