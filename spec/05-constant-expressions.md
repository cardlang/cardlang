# 5. Constant expressions

CardLang Language Specification, Draft 0.1. Chapter status: **draft complete** (SP4).

This chapter defines:

- global constants;
- which expressions are *constant expressions*;
- which positions require a constant expression;
- the rule that every constant-only part of any expression is evaluated during compilation, with failures reported as compilation errors;
- dependencies between constants.

Constant expressions use the ordinary expression grammar (Annex A §A.2.4). This chapter restricts them by meaning, not by syntax.

**Forward references to chapter 6.** The typing and runtime semantics of operators, literals, indexing, constructors, `fill` and `convert` are defined in chapter 6. This chapter refers to chapter 6 by section until that chapter is drafted (SP5). SP14 replaces these references with rule IDs.

## 5.1 Global constants

```
GlobalValueDeclaration ::= StorageKeyword+ Identifier ':' Type ( '=' Expression )? ';'   /* §A.2.1 */
```

**CEX-1 [Agreed]** A declaration `const name: T = e;` declares a *global constant* of value type `T`. Its value is computed during compilation. A `const` declaration without an initializer is **CE-CEX-1**. Chapter 3 governs the storage keyword itself (NAM-9).
*Sources: D-005, D-129; DN §3.9, §3.10, §5.1.*

**CEX-2 [Agreed]** The initializer of a global constant must be a constant expression (§5.2). Its type must be `T` under the typing rules of chapter 6, including contextual typing of literals. A global constant has:

- no lifetime and no writable state;
- no observable representation;
- a value that is fixed for the whole life of the application.

A constant is immutable at every depth (TYP-16). Assigning to it, or to any of its fields or elements, is rejected by chapter 7. Passing it as an `inout` argument is rejected by chapter 8. It may be passed as a `ref` argument.
*Sources: D-005, D-073, D-330; DN §3.8, §3.10, §5.1.*

### Examples

*Valid:* global constants built from literals, other constants, operators and `fill` (DN §3.10). (conformance: `valid/cex-001-basic-constants.card`)

```text
const BASE: u32 = 32;
const CAPACITY: u32 = BASE * 4;
const MASK: u8 = 0x0F;
const DEFAULT_ID: u8[4] = fill(0);
```

*Invalid:* a constant without an initializer. **CE-CEX-1**. (conformance: `invalid/cex-101-missing-initializer.card`)

```text
const LIMIT: u32;
```

## 5.2 The constant-expression subset

**CEX-3 [Agreed]** An expression is a *constant expression* when it is one of the forms below, and every subexpression it contains is also a constant expression:

| Form | Condition |
|---|---|
| An integer literal or Boolean literal | — |
| The name of a global constant | Including a constant declared later or in another file |
| A qualified enum variant, such as `OperationState.Idle` | — |
| A parenthesized expression | — |
| A unary or binary operator expression (chapter 6) | Both operands are constant |
| An explicit array list `[e1, …, en]` | — |
| A structure constructor `S { f1: e1, … }` | — |
| `fill(e)` | — |
| Indexing `a[i]` | `a` is a constant expression of fixed-array type and `i` is constant |
| Field selection `s.f` | `s` is a constant expression of structure type |
| `x.length` | Under CEX-4 |
| `convert<T>(e)` | The conversion is a guaranteed conversion under chapter 6 |

*Sources: D-094, D-095, D-326, D-327; DN §3.10, §3.11.*

**CEX-4 [Agreed]** An expression `x.length`, where `x` has a fixed-array type, is a constant expression when either:

- `x` is a *plain path*: a name of a variable, constant, global or parameter, followed by zero or more field selections. This holds whatever the storage class, because only the type of `x` is used and its contents are not read; or
- `x` is itself a constant expression.

In every other case `x.length` is not a constant expression. An example is a receiver that indexes a mutable array. At runtime its receiver is still evaluated (chapter 6).
*Sources: D-328; DN §3.10, §8.1.*

**CEX-5 [Agreed]** The following are never constant expressions, even when every operand is constant:

- reading the value of a local variable or parameter, or the contents of persistent or session state, including through indexing or field selection;
- calls to ordinary functions or platform APIs;
- the intrinsics `checked_convert`, `checked_add`, `checked_sub`, `checked_mul`, `checked_div`, `checked_rem`, `checked_neg`, `wrapping_add`, `wrapping_sub` and `wrapping_mul`;
- `attempt`, references, slices, assignments and transactions.

There are no user-defined compile-time functions.
*Sources: D-093, D-096, D-326, D-332; DN §3.10, §6.5.*

**CEX-6 [Agreed]** A constant expression is required in exactly two places:

- the initializer of a global constant (CEX-2);
- the length of a fixed array type (TYP-19).

Any other expression in either position is **CE-CEX-2**. Error-member codes are not constant expressions. They must be integer literals, as defined in chapter 9.
*Sources: D-094, D-099, D-428 (OI-28); DN §3.10.*

### Examples

*Valid:* a guaranteed conversion of a typed constant (DN §3.10). (conformance: `valid/cex-003-convert-typed-constant.card`)

```text
const SMALL: u8 = 32;
const LARGE: u32 = convert<u32>(SMALL);
```

*Valid:* indexing a constant array, and selecting a field of a constant structure. (conformance: `valid/cex-004-constant-aggregates.card`)

```text
struct Limits {
    low: u16;
    high: u16;
}

const IDENTIFIER: u8[4] = [1, 2, 3, 4];
const FIRST_BYTE: u8 = IDENTIFIER[0];
const LIMITS: Limits = Limits { low: 10, high: 200 };
const HIGH: u16 = LIMITS.high;
```

*Valid:* the length of a session array, which is known from its type (DN §3.10). (conformance: `valid/cex-005-length-of-session-array.card`)

```text
const BLOCK_SIZE: u32 = 32;
session buffer: u8[BLOCK_SIZE * 4];
const BUFFER_LENGTH: u32 = buffer.length;
```

*Valid:* enum constants, and equality between them. (conformance: `valid/cex-006-enum-constants.card`)

```text
enum OperationState {
    Idle;
    Receiving;
}

const INITIAL_STATE: OperationState = OperationState.Idle;
const STARTS_IDLE: bool = INITIAL_STATE == OperationState.Idle;
```

*Invalid:* reading the contents of session state (DN §3.10). **CE-CEX-2**. (conformance: `invalid/cex-102-reads-session.card`)

```text
session buffer: u8[16];
const FIRST_BYTE: u8 = buffer[0];
```

*Invalid:* a function call, through `attempt`, in a constant. **CE-CEX-2**. (conformance: `invalid/cex-103-function-call.card`)

```text
function base_value() -> u32 {
    return Ok(32);
}

const BASE: u32 = attempt base_value();
```

*Invalid:* a wrapping intrinsic, which is excluded even with constant arguments. **CE-CEX-2**. (conformance: `invalid/cex-104-wrapping-intrinsic.card`)

```text
const A: u8 = 200;
const B: u8 = 100;
const W: u8 = wrapping_add(A, B);
```

## 5.3 Mandatory compile-time evaluation

**CEX-7 [Agreed]** Every *constant-only* subexpression of every expression in the application is evaluated during compilation. That covers global initializers, array lengths, local initializers, conditions, arguments and every other runtime expression. A subexpression is constant-only when it is a constant expression under §5.2. An implementation determines and evaluates these subexpressions as follows:

1. **Resolve and type-check everything.** Resolve names and type-check every expression. This includes the operands that step 3 skips and the expressions in unreachable statements.
2. **Classify structurally.** Classify each subexpression as constant-only or runtime-dependent using only the forms of §5.2. A mutable variable is runtime-dependent even if its value could be inferred, for example a local initialized to zero and never changed. Guaranteed `convert` counts as constant-only when its operand is. The intrinsics excluded by CEX-5 never count as constant-only, even with constant operands.
3. **Evaluate maximal parts.** Evaluate each maximal constant-only subexpression with the ordinary semantics (CEX-8), including short-circuiting. A descendant that this evaluation skips is not evaluated.
4. **Recurse into runtime-dependent parts.** In a runtime-dependent expression, find and evaluate its constant-only parts the same way. A runtime-dependent guard does not prevent this. For example, in `runtime_flag and e`, a constant-only `e` is still evaluated. The only thing that suppresses evaluation of a right operand is a left operand that is *itself constant-only* and short-circuits: `false` before `and`, or `true` before `or`.
5. **Ignore reachability.** Whether a statement can be reached never suppresses evaluation. Constant-only parts of a statement inside `if false { … }`, or after a `return`, are still evaluated. Short-circuiting within an expression still applies.
6. **Keep acceptance fixed.** Additional analysis, optimization and warnings never change whether a program is accepted. An implementation must not reject a program because it predicts that a runtime-dependent expression will fail, and must not remove a required runtime check.

*Sources: D-029, D-097, D-411 (OI-11); DN §3.10.*

**CEX-8 [Agreed]** Compile-time evaluation uses exactly the semantics that the same expression would have at runtime (chapter 6). That covers contextual literal types, checked arithmetic on each intermediate result, division truncating toward zero, shifts, `fill`, constructors and conversion. No wider intermediate type is used, and an out-of-range intermediate result is never repaired by a later operation.
*Sources: D-029, D-087; DN §3.10, §6.5.*

**CEX-9 [Agreed]** A failure during compile-time evaluation is a compilation error, never a runtime trap:

- **CE-CEX-3** covers the arithmetic failures that chapter 6 defines as traps at runtime:
  - overflow or underflow;
  - division or remainder by zero;
  - the minimum signed value divided by −1;
  - a shift count at least the width of the left operand;
  - negation of the minimum signed value.
- **CE-CEX-4** covers an index that is out of range for a constant array.

The minimum signed value remainder −1 is not a failure. Its result is zero (chapter 6).
*Sources: D-029, D-088, D-089, D-090; DN §3.5, §3.10, §6.5.*

**CEX-10 [Agreed]** The following must be checked during compilation, even when the array is mutable state:

- an index expression that is constant-only;
- slice endpoints that are both constant-only.

This applies when the array being indexed or sliced has a fixed-array type, so its length is known from the type. Each of the following is **CE-CEX-4**:

- an index that is not less than the length;
- a slice whose end is greater than the length;
- a slice whose start is greater than its end.

Indexes and slices of unsized `T[]` parameters, whose lengths are known only at runtime, are checked at runtime (chapter 6, chapter 8).
*Sources: D-411 (OI-11), D-429 (OI-29); DN §3.10, §8.4.*

**CEX-11 [Agreed]** An operand that is skipped by short-circuiting is not evaluated, but it is still resolved and type-checked (CEX-7 step 1). Name and type errors in it are reported as usual.
*Sources: D-329; DN §3.10.*

### Examples

In these examples `ZERO` is a global `u32` constant equal to zero, and `runtime_flag` is a session `bool`.

*Valid:* the division is skipped because the left operand is the constant `false` (DN §3.10). (conformance: `valid/cex-007-short-circuit-skip.card`)

```text
const ZERO: u32 = 0;
const ENABLED: bool = false and ((10 / ZERO) == 1);
```

*Valid:* the nested constant expression `false and …` short-circuits, so the division is skipped even though the outer expression depends on runtime state (DN §3.10). (conformance: `valid/cex-008-nested-constant-guard.card`)

```text
const ZERO: u32 = 0;
session runtime_flag: bool;

function check() -> bool {
    return Ok(runtime_flag and (false and ((10 / ZERO) == 1)));
}
```

*Valid:* division by a mutable local whose value happens to be zero. The divisor is runtime-dependent, so the program compiles and the division is checked at runtime (DN §3.10). (conformance: `valid/cex-009-runtime-division.card`)

```text
function divide() -> u32 {
    var divisor: u32 = 0;
    return Ok(10 / divisor);
}
```

*Invalid:* overflow in a constant (DN §3.10). **CE-CEX-3**. (conformance: `invalid/cex-105-overflow.card`)

```text
const TOO_LARGE: u8 = 250 + 10;
```

*Invalid:* division by zero in a constant (DN §3.10). **CE-CEX-3**. (conformance: `invalid/cex-106-division-by-zero.card`)

```text
const DIV_ZERO: u32 = 10 / 0;
```

*Invalid:* a runtime guard does not stop evaluation of the constant-only right operand (DN §3.10). **CE-CEX-3**. (conformance: `invalid/cex-107-runtime-guard.card`)

```text
const ZERO: u32 = 0;
session runtime_flag: bool;

function check() -> bool {
    return Ok(runtime_flag and ((10 / ZERO) == 1));
}
```

*Invalid:* a constant-only failure inside an unreachable `if false` body (DN §3.10). **CE-CEX-3**. (conformance: `invalid/cex-108-unreachable-if-false.card`)

```text
const ZERO: u32 = 0;

function unreachable_branch() {
    if false {
        var result: u32 = 10 / ZERO;
    }
    return Ok();
}
```

*Invalid:* a constant-only failure after a `return` (DN §3.10). **CE-CEX-3**. (conformance: `invalid/cex-109-after-return.card`)

```text
const ZERO: u32 = 0;

function after_return() {
    return Ok();
    var result: u32 = 10 / ZERO;
}
```

*Invalid:* a constant-only overflow in a local initializer. **CE-CEX-3**. (conformance: `invalid/cex-114-local-constant-overflow.card`)

```text
function narrow() {
    var value: u8 = 250 + 10;
    return Ok();
}
```

*Invalid:* a shift count equal to the width of the left operand. **CE-CEX-3**. (conformance: `invalid/cex-115-shift-count.card`)

```text
const S: u8 = 1 << 8;
```

*Invalid:* the minimum signed value divided by −1. **CE-CEX-3**. (conformance: `invalid/cex-116-signed-minimum-division.card`)

```text
const M: i8 = -128 / -1;
```

*Invalid:* an index out of range for a constant array. **CE-CEX-4**. (conformance: `invalid/cex-110-constant-array-bounds.card`)

```text
const IDENTIFIER: u8[4] = [1, 2, 3, 4];
const BAD: u8 = IDENTIFIER[4];
```

*Invalid:* a constant index out of range for a mutable session array whose length is known from its type. **CE-CEX-4**. (conformance: `invalid/cex-111-mutable-array-constant-index.card`)

```text
session buffer: u8[128];

function write_far() {
    buffer[200] = 1;
    return Ok();
}
```

## 5.4 Dependencies

**CEX-12 [Agreed]** A constant may refer to any global constant, including one declared later in the same file or in another file. Constant evaluation has no side effects, so the order in which constants are evaluated is not defined and cannot be observed. Source-file order never matters (NAM-4).
*Sources: D-098, D-326; DN §3.10.*

**CEX-13 [Agreed]** It is **CE-CEX-5** when the value of a global constant or an array length depends on itself, directly or through any chain of:

- other constants;
- array lengths;
- `.length` expressions, which depend on the length in their receiver's type;
- types declared with such lengths.

*Sources: D-098; DN §3.10.*

**CEX-14 [Agreed]** The ban on calls inside call arguments (chapter 6) also applies inside constant expressions. In particular, one `convert` cannot be nested inside another. Each intermediate value must be declared as a separate constant.
*Sources: D-331, D-027; DN §3.7, §3.10.*

### Examples

*Valid (two files):* a constant that uses a constant declared in a later file. The test must pass for every file order (DN §3.10). (conformance: `valid/cex-002-forward-dependency/`)

```text
// a.card
const CAPACITY: u32 = BLOCK_SIZE * 4;
```

```text
// b.card
const BLOCK_SIZE: u32 = 32;
```

*Invalid:* two constants that depend on each other (DN §3.10). **CE-CEX-5**. (conformance: `invalid/cex-112-cycle.card`)

```text
const FIRST: u32 = SECOND + 1;
const SECOND: u32 = FIRST + 1;
```

*Invalid:* an array length that depends on the array's own length. **CE-CEX-5**. (conformance: `invalid/cex-113-cycle-through-length.card`)

```text
session buffer: u8[N];
const N: u32 = buffer.length;
```

## 5.5 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-CEX-1** | A `const` declaration has no initializer | CEX-1 |
| **CE-CEX-2** | A position that requires a constant expression holds a non-constant expression | CEX-2, CEX-6 |
| **CE-CEX-3** | Compile-time evaluation fails with an arithmetic failure | CEX-7, CEX-9 |
| **CE-CEX-4** | A compile-time bounds check fails: a constant array index, or a constant index or slice of an array whose length is known from its type | CEX-9, CEX-10 |
| **CE-CEX-5** | A dependency cycle among constants, array lengths and types | CEX-13 |

These related errors are defined in chapter 6:

- a typed constant used where another integer type is required, for example `const LARGE: u32 = SMALL;` with `SMALL: u8`;
- `convert` whose source type is unknown;
- a nested call.
