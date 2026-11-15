# SP4 — Constant expressions: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 5 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/05-constant-expressions.md` | Global `const` declarations; the constant-expression subset; the positions that require one; mandatory compile-time evaluation of constant-only parts of any expression (the structural algorithm, D-411); evaluation semantics and failures; `.length` as a constant; dependencies and cycles; enums in constants |
| `spec/annex-A-grammar.md` §A.2.3 | A note: constant expressions use the ordinary expression grammar (§A.2.4), and chapter 5 restricts them by meaning, not by syntax |
| `conformance/valid/cex-*`, `conformance/invalid/cex-*` | One test per chapter example |
| Register, Annex C, Annex D, 00-index | Body decisions D-326…, new issues, rule coverage and the CE-CEX index |

**Out of scope:**

| Topic | Where |
|---|---|
| Typing of individual operators, literal context, the `convert` source-type and range rules, and the nested-call ban | Chapter 6 (SP5) |
| Runtime arithmetic semantics | Chapter 6 (SP5). Chapter 5 states that compile-time evaluation uses the same semantics, and only classifies failures |
| Passing constants by `ref` | Chapter 8 (SP7) |
| The ban on assigning to constants | Chapter 7 (SP6) |
| Validity of error-member codes (nonzero, unique) | Chapter 9 (SP8). Chapter 5 only says whether they are constant expressions (OI-28) |

**Ordering note.** SP4 comes before SP5, so chapter 5 refers to chapter 6 *by section*, for example "the operator typing rules of chapter 6". SP5 adds the rule IDs, and SP14 checks the references.

## 2. Sources

- **DN sections:** §3.3 (lengths, literal context), §3.8 (constants through `ref`), §3.10 (all), §3.11 (enum constants), §5.1 (constants have no writable state), §6.5 (intrinsics excluded from constants).
- **Decisions:**
  - D-005: a global `const` is a compile-time constant.
  - D-029: constant-only calculations are evaluated at compile time everywhere.
  - D-093, D-094, D-095, D-096: the subset, including which intrinsics are excluded and that `convert` is allowed.
  - D-097 and D-411: the structural algorithm is normative, and a constant index out of range of a known length is a compile error.
  - D-098: forward references are allowed and cycles are errors.
  - D-099: array lengths.
  - D-129: a `const` requires an initializer.

### 2.1 Body-only decisions to register (D-326…)

| ID | Decision | Source |
|---|---|---|
| D-326 | Constant evaluation is deterministic and has no side effects. There are no user-defined compile-time functions | DN §3.10 |
| D-327 | Qualified enum variants are constant expressions, and equality of constant enum values can be evaluated at compile time | DN §3.11 |
| D-328 | `.length` of a fixed array reached through a plain variable or field path is constant without reading the array's contents. A more complex receiver must itself meet the constant restrictions | DN §3.10 |
| D-329 | Compile-time evaluation preserves short-circuiting. A skipped operand is still name-resolved and type-checked | DN §3.10 |
| D-330 | Global constants need no writable state, and their physical representation is an implementation detail. A constant may be passed through `ref`, never `inout` | DN §3.8, §5.1 |
| D-331 | The nested-call ban also applies in constant expressions. Nested conversions use separately declared intermediate constants | DN §3.10 |
| D-332 | Constant expressions never read the contents of persistent or session state | DN §3.10 |

## 3. Planned rules (chapter 5)

**§5.1 Global constants**

- **CEX-1** `const name: T = e;` declares a compile-time constant of value type `T`. It has an explicit type and a required initializer. A missing initializer is **CE-CEX-1** (D-005, D-129).
- **CEX-2** The initializer must be a constant expression (§5.2) whose type is `T` under the typing rules of chapter 6. Its value is fixed at compile time. A constant has no lifetime, no writable state and no observable representation. It is immutable at every depth: chapter 7 rejects assignments to it, and chapter 8 rejects passing it `inout` (D-330, D-073).

**§5.2 The constant-expression subset**

- **CEX-3** An expression is a *constant expression* when it is built only from the forms listed below:
  - integer and Boolean literals;
  - names of global constants, including forward references;
  - qualified enum variants (D-327);
  - grouping, and the unary and binary operators of chapter 6 applied to constant operands;
  - explicit array lists and structure constructors whose components are all constant;
  - `fill(e)` where `e` is constant;
  - indexing a constant array with a constant index;
  - selecting a field of a constant structure;
  - `.length` under CEX-4;
  - `convert<T>(e)` where `e` is constant, subject to chapter 6's guaranteed-conversion rules.

  (D-094, D-095, D-326.)
- **CEX-4** `.length` is constant when its receiver is either:
  - a path of names and field selections ending in a fixed array, of any storage class (its contents are not read), or
  - itself a constant expression.

  Any other receiver, for example one that indexes a mutable array, makes `.length` non-constant (D-328).
- **CEX-5** The following are never constant:
  - reading a local, a parameter, or persistent or session contents;
  - calls to functions or platform APIs;
  - `checked_convert`, and the `checked_*` and `wrapping_*` intrinsics, even with constant arguments;
  - `attempt`, references, slices, mutation and transactions.

  (D-093, D-096, D-332.)
- **CEX-6** Positions that *require* a constant expression:
  - global `const` initializers;
  - array lengths;
  - error-member codes [Open → OI-28].

  A non-constant expression in one of these positions is **CE-CEX-2**.

**§5.3 Mandatory compile-time evaluation**

- **CEX-7** The structural algorithm from DN §3.10, now agreed (D-411), is written as the normative rule:
  1. Resolve names and type-check every expression, including skipped operands and unreachable statements.
  2. Identify the constant-only subexpressions *structurally*, using CEX-3 to CEX-5. A mutable variable is never constant, even if its value could be inferred.
  3. Evaluate the maximal constant-only subexpressions, using ordinary semantics and short-circuiting. Never evaluate a descendant that its enclosing constant Boolean expression skips.
  4. Inside a runtime-dependent expression, evaluate its constant-only parts. A runtime guard does not suppress this. A *structurally constant* `false` left operand of `and`, or `true` left operand of `or`, does suppress evaluation of the right operand.
  5. Statement reachability never suppresses evaluation.
  6. Optimizations and warnings never change acceptance, and never turn a required runtime check into a compile error.

  This applies to constant-only parts *anywhere*: in global initializers, lengths, local initializers and runtime expressions (D-029, D-097, D-411).
- **CEX-8** Compile-time evaluation uses exactly the runtime semantics of chapter 6. There are no wider intermediates and no different rounding (D-029; DN §3.10).
- **CEX-9** Failures during required evaluation:
  - An arithmetic failure is **CE-CEX-3**. This covers overflow, underflow, division or remainder by zero, the signed minimum divided by −1, an invalid shift count, and unrepresentable negation.
  - A bounds failure while indexing a constant array is **CE-CEX-4**.

  None of these are runtime traps (D-029).
- **CEX-10** A constant-only index (or slice endpoint [Open → OI-29]) applied to an array whose length is known from its type is checked at compile time, even when the array is in mutable storage. Out of range is **CE-CEX-4** (D-411).
- **CEX-11** Skipped short-circuit operands are still resolved and type-checked. Errors found there are reported normally (D-329).

**§5.4 Dependencies**

- **CEX-12** A constant may refer to constants declared later or in other files. Evaluation order is not defined and cannot be observed (D-098, D-326).
- **CEX-13** A direct or indirect dependency cycle among constants, array lengths and types is **CE-CEX-5**. Examples: `FIRST = SECOND + 1` together with `SECOND = FIRST + 1`, or `session buffer: u8[N]` together with `const N: u32 = buffer.length` (D-098).
- **CEX-14** The nested-call ban (chapter 6) applies inside constant expressions too. A nested conversion needs an intermediate constant (D-331).

**Error classes**

| Class | Meaning |
|---|---|
| CE-CEX-1 | `const` without an initializer |
| CE-CEX-2 | Non-constant expression where a constant is required |
| CE-CEX-3 | Arithmetic failure during compile-time evaluation |
| CE-CEX-4 | Bounds failure during compile-time evaluation |
| CE-CEX-5 | Dependency cycle |

## 4. New open issues

| ID | Question | Recommendation |
|---|---|---|
| **OI-28** Error-member code expressions | DN §6.3 shows only literal codes (`InsufficientFunds = 1;`), and the DN §3.3 table says "Application error-code literal → required u16 code type". May a code be any constant expression of type `u16`, such as `BASE_CODE + 1`, or must it be a literal? | A literal only. The notes speak only of literals, and codes are published identities that should be plain to read in the source. A literal gets `u16` context. Allowing constant expressions later would not break any program |
| **OI-29** Constant slice endpoints (decision below) | D-411 makes a constant out-of-range *index* into an array of known length a compile error. Do constant slice endpoints on a fixed array follow the same rule? This covers `end > length`, and `start > end`, when both are constant-only | Yes, for consistency with D-411: **CE-CEX-4**. A slice of an unsized `T[]` parameter is still checked at runtime |

**Decided 2026-11-15:** you accepted both recommendations. They become D-428 and D-429. As a result:

- CEX-6 lists only `const` initializers and array lengths as constant-expression positions. Chapter 9 (SP8) requires error-member codes to be integer literals with `u16` context.
- CEX-10 covers constant slice endpoints and is **[Agreed]**.

## 5. Examples and conformance tests

The source column gives the DN section each test comes from.

**Valid**

| Test | Shows |
|---|---|
| `valid/cex-001-basic-constants.card` | `BASE`, `CAPACITY`, `MASK` and `DEFAULT_ID = fill(0)` (DN §3.10) |
| `valid/cex-002-forward-dependency/` | `CAPACITY` uses `BLOCK_SIZE`, which is declared in a later file. Must pass in any file order |
| `valid/cex-003-convert-typed-constant.card` | `LARGE = convert<u32>(SMALL)` (DN §3.10) |
| `valid/cex-004-constant-aggregates.card` | `IDENTIFIER[0]`, and a field of a constant structure |
| `valid/cex-005-length-of-session-array.card` | `BUFFER_LENGTH = buffer.length` (DN §3.10) |
| `valid/cex-006-enum-constants.card` | `INITIAL_STATE`, and an equality between constant enum values |
| `valid/cex-007-short-circuit-skip.card` | `false and ((10 / ZERO) == 1)` (DN §3.10) |
| `valid/cex-008-nested-constant-guard.card` | `runtime_flag and (false and ((10 / ZERO) == 1))` (DN §3.10 table) |
| `valid/cex-009-runtime-division.card` | `10 / divisor` with a mutable local: compiles. The runtime trap is checked in SP5 and SP12 |

**Invalid**

| Test | Expected error | Shows |
|---|---|---|
| `invalid/cex-101-missing-initializer.card` | CE-CEX-1 | `const LIMIT: u32;` |
| `invalid/cex-102-reads-session.card` | CE-CEX-2 | `const FIRST_BYTE: u8 = buffer[0];` (DN §3.10) |
| `invalid/cex-103-function-call.card` | CE-CEX-2 | A call in a `const` initializer |
| `invalid/cex-104-wrapping-intrinsic.card` | CE-CEX-2 | `wrapping_add` with constant arguments |
| `invalid/cex-105-overflow.card` | CE-CEX-3 | `const TOO_LARGE: u8 = 250 + 10;` |
| `invalid/cex-106-division-by-zero.card` | CE-CEX-3 | `const DIV_ZERO: u32 = 10 / 0;` |
| `invalid/cex-107-runtime-guard.card` | CE-CEX-3 | `runtime_flag and ((10 / ZERO) == 1)` (DN §3.10 table) |
| `invalid/cex-108-unreachable-if-false.card` | CE-CEX-3 | `10 / ZERO` inside an `if false` body |
| `invalid/cex-109-after-return.card` | CE-CEX-3 | `10 / ZERO` after a `return` |
| `invalid/cex-110-constant-array-bounds.card` | CE-CEX-4 | `IDENTIFIER[4]` on `u8[4]` |
| `invalid/cex-111-mutable-array-constant-index.card` | CE-CEX-4 | `buffer[200] = 1;` on a `u8[128]` session array (D-411) |
| `invalid/cex-112-cycle.card` | CE-CEX-5 | `FIRST` and `SECOND` (DN §3.10) |
| `invalid/cex-113-cycle-through-length.card` | CE-CEX-5 | A length that depends on its own array |
| `invalid/cex-114-local-constant-overflow.card` | CE-CEX-3 | `var value: u8 = 250 + 10;` inside a function (D-029) |
| `invalid/cex-115-shift-count.card` | CE-CEX-3 | `const S: u8 = 1 << 8;` |
| `invalid/cex-116-signed-minimum-division.card` | CE-CEX-3 | `const M: i8 = -128 / -1;` |

**Deferred tests:**

- To SP5: `const LARGE: u32 = SMALL;` (an implicit conversion), `convert<u32>(32)` (unknown source type), and a nested `convert` call. They are typing errors in chapter 6.
- To SP7: constant slice bounds (OI-29), which need the slice syntax.
- To SP8: error-code expressions (OI-28).

## 6. Steps

1. Register D-326…D-332, add OI-28 and OI-29, and record your decisions.
2. Write chapter 5, citing chapter 6 by section.
3. Add the §A.2.3 note.
4. Write the 25 tests, generated from the chapter examples.
5. Update Annex D, the register, Annex C (OI-11 and its resolution-log row) and the index.
6. Run the checks:
   - lexical and type scans of all tests;
   - a small constant evaluator, written in the scratchpad from chapter 5 and the arithmetic rules in DN §3.5 and §6.5. It runs over the `const` declarations in every test and confirms each expected CE-CEX-3, CE-CEX-4 and CE-CEX-5, and that the valid tests evaluate cleanly.

## 7. Exit checklist

- Every CEX rule has a tag and a sources line. Every [Open] rule cites OI-28 or OI-29 until they are decided.
- Every row of the DN §3.10 acceptance table has a test.
- The constant evaluator agrees with every CE-CEX expectation.
- Every reference resolves. References to chapter 6 are listed for SP5 to turn into rule IDs.

## 8. Choices made in this sub-plan

These are open for redirection:

- Chapter 6 is cited by section until SP5 exists.
- `.length` constant-ness is defined by the shape of its receiver (CEX-4).
- Bounds failures (CE-CEX-4) are kept separate from arithmetic failures (CE-CEX-3).
- Four typing tests are deferred to SP5.
