# 6. Expressions

CardLang Language Specification, Draft 0.2. Chapter status: **draft complete** (SP5).

This chapter defines the syntax, typing and evaluation of expressions:

- literals and their contextual types;
- operators and the grouping rule;
- arithmetic and its failures;
- the compiler intrinsics;
- conversions between integer types, and between integers and bytes;
- indexing, `.length` and field selection;
- aggregate construction;
- calls.

Several related topics are defined in other chapters:

| Topic | Chapter |
|---|---|
| Assignment, which is a statement | 7 |
| Parameter modes, call-site `ref`/`inout`, argument preparation, aliasing and slices | 8 |
| What an outcome is, and how `match`, `attempt` and forwarding returns consume it | 9 |
| The catalog of trap kinds | 13 |

Typing rules use the bidirectional judgments of chapter 1 §1.7.2. `Γ ⊢ e ⇒ T` means that `e` *synthesizes* type `T` by itself. `Γ ⊢ e ⇐ T` means that `e` *checks* against an expected type `T` supplied by its context. Wherever a rule needs `e ⇐ T` and `e` instead synthesizes some `U`, `U` must be identical to `T` (TYP-4), or the program is rejected with **CE-EXP-1**. Constant-only parts of every expression are also evaluated during compilation (chapter 5).

## 6.1 Grammar and grouping

```
Expression      ::= UnaryExpression ( BinaryOperator UnaryExpression )*
BinaryOperator  ::= '+' | '-' | '*' | '/' | '%' | '==' | '!=' | '<' | '<=' | '>' | '>='
                  | 'and' | 'or' | '&' | '|' | '^' | '<<' | '>>'
UnaryExpression ::= ( '-' | 'not' | '~' ) UnaryExpression
                  | 'attempt' PostfixExpression ( 'else' PostfixExpression )?
                  | PostfixExpression
PostfixExpression ::= PrimaryExpression PostfixPart*
PostfixPart     ::= '[' Expression ']'
                  | '[' Expression '..' Expression ']'
                  | '.' Identifier
                  | Arguments
PrimaryExpression ::= IntegerLiteral | BooleanLiteral | ByteStringLiteral | Identifier
                  | '(' Expression ')'
                  | ArrayList
                  | StructConstructor
                  | TypeArgumentCall
ArrayList       ::= '[' ( Expression ( ',' Expression )* ','? )? ']'
StructConstructor ::= Identifier '{' ( FieldInit ( ',' FieldInit )* ','? )? '}'
FieldInit       ::= Identifier ':' Expression
TypeArgumentCall ::= TypeArgumentIntrinsic '<' Type '>' Arguments
TypeArgumentIntrinsic ::= 'convert' | 'checked_convert' | 'truncate' | 'decode_be' | 'decode_le'
Arguments       ::= '(' ( Argument ( ',' Argument )* ','? )? ')'
Argument        ::= ( 'ref' | 'inout' )? Expression
ConditionExpression ::= ConditionUnary ( BinaryOperator ConditionUnary )*
ConditionUnary  ::= ( '-' | 'not' | '~' ) ConditionUnary
                  | 'attempt' ConditionPostfix ( 'else' ConditionPostfix )?
                  | ConditionPostfix
ConditionPostfix ::= ConditionPrimary PostfixPart*
ConditionPrimary ::= IntegerLiteral | BooleanLiteral | ByteStringLiteral | Identifier
                  | '(' Expression ')'
                  | ArrayList
                  | TypeArgumentCall
```

In `TypeArgumentIntrinsic`, the quoted names stand for identifier tokens with those spellings. These names are reserved (LEX-15), so `convert <` never begins a comparison.

**EXP-1 [Agreed]** Expressions are built from the following forms:

- literals;
- names;
- parenthesized expressions;
- array lists;
- structure constructors;
- calls, including intrinsic calls with a type argument;
- the postfix operations: indexing `a[i]`, slicing `a[s..e]`, field selection `x.f` and call arguments;
- the unary operators `-`, `not` and `~`;
- `attempt`;
- the binary operators.

Postfix operations apply left to right and bind more tightly than unary operators. A unary operator applies to the whole postfix expression that follows it, so `-a[i]` means `-(a[i])` and `not ready` applies to `ready` only. An expression containing a binary operator never needs parentheses just because a unary operator, call, index or field selection is present.
*Sources: D-102, D-337; DN §3.5.*

**EXP-2 [Agreed]** A *grouping level* is the sequence of operands and binary operators directly inside one of these:

- a whole expression;
- a parenthesized expression;
- an index or slice bracket;
- a call argument;
- an array-list element;
- a constructor field initializer.

All binary operators at one grouping level must be the same operator. Two different binary operators at one level is **CE-EXP-4**. There is no precedence table: write parentheses to show the intended grouping, as in `a + (b * c)`. Unary operators and assignment are not binary operators, so they never break this rule.
*Sources: D-102; DN §3.5.*

**EXP-3 [Agreed]** A chain of one repeated non-comparison operator, `a op b op c`, means `(a op b) op c`. It is evaluated left to right, and every intermediate result is checked by itself (§6.5). For example, in `a + b - c` the operators differ (CE-EXP-4). In `a - b - c`, an underflow in `a - b` is a failure even if subtracting `c` would come back in range.
*Sources: D-103, D-087; DN §3.5.*

**EXP-4 [Agreed]** Comparison operators (`==`, `!=`, `<`, `<=`, `>` and `>=`) never chain. Two comparison operators at one grouping level is **CE-EXP-5**, even when they are the same operator, as in `a == b == c`. Write each comparison as its own operand, as in `(amount > 0) and (amount < limit)`.
*Sources: D-103; DN §3.5.*

**EXP-5 [Agreed]** The words `and`, `or` and `not` are the Boolean operators, and `&`, `|`, `^` and `~` are the bitwise operators. The grouping rule (EXP-2) applies to both. For example, `flags & 0x03 == 0x01` mixes `&` and `==` (CE-EXP-4), while `(flags & 0x03) == 0x01` is valid.
*Sources: D-102; DN §3.5.*

**EXP-6 [Agreed]** A structure constructor must not appear unparenthesized at the outer level of any of the following, because there `{` is read as the start of the body:

- the condition of an `if` or `while`;
- a bound of a `for` range;
- the scrutinee of a `match`.

Doing so does not derive (**CE-SYN-1**): those positions use `ConditionExpression` (§6.1, Annex A §A.2.4), which excludes an unparenthesized constructor. Parenthesize the constructor instead, as in `if (Limits { low: 1, high: 2 }).high == 2 { … }`.
*Sources: D-430 (OI-30), D-444 (OI-44).*

### Examples

*Valid:* chains of one operator, explicit grouping, and unary operators next to binary operators. (conformance: `valid/exp-004-same-operator-chains.card`, `valid/exp-005-unary-with-binary.card`)

```text
function chains(a: u32, b: u32, c: u32) -> u32 {
    var sum: u32 = a + b + c;
    var difference: u32 = (a + b) - c;
    var mixed: u32 = a + (b * c);
    return Ok(sum);
}
```

*Valid:* a parenthesized constructor in an `if` condition. (conformance: `valid/exp-018-parenthesized-constructor-condition.card`)

```text
struct Limits {
    low: u16;
    high: u16;
}

function check() -> bool {
    if (Limits { low: 1, high: 2 }).high == 2 {
        return Ok(true);
    }
    return Ok(false);
}
```

*Invalid:* each of these is in its own test, inside a minimal function.

| Expression | Class | Conformance |
|---|---|---|
| `a + b * c` | CE-EXP-4 | `invalid/exp-105-mixed-arithmetic.card` |
| `a + b - c` | CE-EXP-4 | `invalid/exp-106-mixed-plus-minus.card` |
| `flags & 0x03 == 0x01` | CE-EXP-4 | `invalid/exp-107-mixed-bitwise-comparison.card` |
| `authenticated and ready or emergency` | CE-EXP-4 | `invalid/exp-108-mixed-boolean.card` |
| `0 < amount < limit` | CE-EXP-5 | `invalid/exp-109-comparison-chain.card` |
| `a == b == c` (all `bool`) | CE-EXP-5 | `invalid/exp-110-equality-chain.card` |
| `if Limits { low: 1, high: 2 }.high == 2 { … }` | CE-SYN-1 | `invalid/exp-135-unparenthesized-constructor-condition.card` |

## 6.2 Literals and contextual typing

**EXP-7 [Agreed]** An integer literal has no type of its own. It never synthesizes a type. It only checks against an expected type: `Γ ⊢ n ⇐ T` holds when `T` is an integer type and the value of `n` is in the range of `T` (TYP-6). If `T` is an integer type and the value is out of range, that is **CE-EXP-2**. If `T` is not an integer type, that is **CE-EXP-1**. This covers `var flag: bool = 1;`, and assigning a number to an enum variable. Range is checked for the literal's own value, without any implicit widening or narrowing.
*Sources: D-084, D-414 (OI-14), D-100; DN §3.3, §3.4.*

**EXP-8 [Agreed]** A unary minus applied directly to an integer literal, `-n`, checks against a signed integer type `T` when the value `−n` is in the range of `T`. This is how `-128` is accepted in an `i8` context, even though `128` alone does not fit `i8`. If the expected type is unsigned, `-n` is **CE-EXP-6** (EXP-19). This includes `-0`.
*Sources: D-334, D-090; DN §3.0, §6.5.*

**EXP-9 [Agreed]** `true` and `false` synthesize `bool`.
*Sources: D-310; DN §3.0.*

**EXP-10 [Agreed]** These positions supply an expected type:

| Position | Expected type |
|---|---|
| Initializer of a `var` or `const` | The declared type |
| Right-hand side of an assignment | The type of the destination (chapter 7) |
| An argument | The declared parameter type |
| The payload of `return Ok(e)` | The enclosing function's successful payload type |
| A `for` range bound | The declared index type |
| An array-list element, a `fill` argument | The element type of the expected array type |
| A constructor field | The declared field type |
| An index whose expression contains no typed operand | `u32` |
| A shift count | `u8` |
| A `match` scrutinee, a `.length` receiver, any other operand | None |

*Sources: D-084, D-085; DN §3.3, §8.1.* *Derivation: the assignment and shift-count rows follow from DN §3.3 ("a mismatch with the required destination … type is a compilation error") and DN §3.5 ("the count is `u8`").*

**EXP-11 [Agreed]** For a binary arithmetic, bitwise or comparison operator, and for a two-operand intrinsic in the checked or wrapping families:

1. If either operand synthesizes a type `T`, the other operand checks against `T`. This holds whichever side the typed operand is on: in `count + 1` and in `1 + count`, the literal gets `count`'s type.
2. Otherwise, for an arithmetic or bitwise operator, both operands check against the expression's expected type.
3. Otherwise, for a comparison, there is no integer context. A Boolean result expectation does not supply one. Integer literals there are **CE-EXP-3**.

An arithmetic or bitwise expression whose operands are all literals, with no expected type, is also **CE-EXP-3**. The compiler never chooses a default integer type.
*Sources: D-084, D-333; DN §3.3.*

**EXP-12 [Agreed]** A typed value is never converted to satisfy a context (TYP-5). If the synthesized type of an operand, initializer, argument or payload is not identical to the type required, that is **CE-EXP-1**. This holds even when every value of the synthesized type would fit. Convert explicitly instead (§6.7).
*Sources: D-081, D-082, D-087; DN §3.2, §3.3.*

### Examples

*Valid:* literals typed by declarations, assignments, arguments, `return Ok`, `for` ranges, and a typed operand on either side. (conformance: `valid/exp-001-literal-contexts.card`, `valid/exp-002-typed-operand-either-side.card`)

```text
session total: u16;

function scale(factor: u8) -> u8 {
    return Ok(factor * 2);
}

function contexts() -> u32 {
    var count: u8 = 10;
    var sum: u16 = 10 + 20;
    total = 300;
    var scaled: u8 = attempt scale(4);
    for index: u16 in 0..1000 {
        total = index;
    }
    return Ok(5);
}
```

*Valid:* the minimum signed value as a literal, and negation of a signed value. (conformance: `valid/exp-003-negative-minimum.card`)

```text
const MINIMUM: i8 = -128;

function negatives() -> i16 {
    var small: i16 = -32768;
    var value: i16 = 10;
    var negative: i16 = -value;
    return Ok(negative);
}
```

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `count + increment` with `count: u16`, `increment: u8` (DN §3.2) | CE-EXP-1 | `invalid/exp-101-operand-type-mismatch.card` |
| `var invalid: u8 = 300;` (DN §3.3) | CE-EXP-2 | `invalid/exp-102-literal-out-of-range.card` |
| `var invalid: u8 = -1;` | CE-EXP-6 | `invalid/exp-103-negative-literal-unsigned.card` |
| `var same: bool = 1 == 1;` | CE-EXP-3 | `invalid/exp-104-no-literal-context.card` |
| `var invalid: bool = 1;` (DN §3.4) | CE-EXP-1 | `invalid/exp-120-bool-from-integer.card` |
| `state = 1;` with an enum `state` (DN §3.11) | CE-EXP-1 | `invalid/exp-121-enum-from-integer.card` |
| `second = first;` with distinct structures (DN §9.3) | CE-EXP-1 | `invalid/exp-122-distinct-structures.card` |
| `const LARGE: u32 = SMALL;` with `SMALL: u8` (DN §3.10) | CE-EXP-1 | `invalid/exp-123-typed-constant-no-widening.card` |

## 6.3 Operator typing

**EXP-13 [Agreed]** *Arithmetic* `+ - * / %`: both operands have the same integer type `T` under EXP-11, and the result is `T`. Applied to any other type, it is **CE-EXP-6**.
*Sources: D-082; DN §3.2, §3.5.*

**EXP-14 [Agreed]** *Ordering* `< <= > >=`: both operands have the same integer type, and the result is `bool`. Ordering on `bool`, enums, arrays or structures is **CE-EXP-6**.
*Sources: D-082; DN §3.5, §3.11.*

**EXP-15 [Agreed]** *Equality* `== !=`: both operands have the same type, which must be an integer type, `bool` or an enum, and the result is `bool`. Equality on arrays or structures is **CE-EXP-6**. Compare their elements or fields explicitly.
*Sources: D-335; DN §3.5, §3.11, §8.2, §9.3.*

**EXP-16 [Agreed]** *Boolean* `and`, `or` and `not` accept only `bool` operands and produce `bool`. There is no numeric truthiness: an integer operand is **CE-EXP-1**.
*Sources: D-100; DN §3.4, §3.5.*

**EXP-17 [Agreed]** *Bitwise* `& | ^` take two operands of the same unsigned integer type `T`. Unary `~` takes one operand of an unsigned type `T`. The result is `T`. A signed or non-integer operand is **CE-EXP-6**.
*Sources: D-336; DN §3.5.*

**EXP-18 [Agreed]** *Shifts* `<< >>`: the left operand has an unsigned integer type `T`, which it synthesizes or receives as the expected type. The count checks against `u8`. A typed count of any type other than `u8` is **CE-EXP-1**. The result is `T`. A signed or non-integer left operand is **CE-EXP-6**. Shifts are the only binary operators whose operands have different types.
*Sources: D-336; DN §3.5.*

**EXP-19 [Agreed]** *Unary* `-` takes a signed integer operand of type `T` and produces `T`. Applied to an unsigned or non-integer operand, it is **CE-EXP-6**. No implicit signed conversion takes place.
*Sources: D-090; DN §6.5.*

### Examples

*Valid:* equality on `bool` and on an enum. (conformance: `valid/exp-007-equality-bool-enum.card`)

```text
enum Mode {
    Off;
    On;
}

session mode: Mode;
session ready: bool;

function compare() -> bool {
    var same: bool = ready == true;
    return Ok(mode != Mode.Off);
}
```

*Valid:* bitwise operators and shifts with a `u8` count. (conformance: `valid/exp-008-shifts-and-bitwise.card`)

```text
function bits(flags: u8, count: u8) -> u8 {
    var low: u8 = flags & 0x0F;
    var shifted: u8 = flags >> 2;
    var moved: u8 = flags << count;
    var check: bool = (flags & 0x03) == 0x01;
    return Ok(~low);
}
```

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `flags << count` with `count: i8` | CE-EXP-1 | `invalid/exp-115-signed-shift-count.card` |
| `x & y` with `x, y: i16` | CE-EXP-6 | `invalid/exp-116-bitwise-signed.card` |
| `ready < blocked` with `bool` operands | CE-EXP-6 | `invalid/exp-117-ordering-bool.card` |
| `first == second` with structure operands | CE-EXP-6 | `invalid/exp-118-structure-equality.card` |
| `left == right` with array operands | CE-EXP-6 | `invalid/exp-119-array-equality.card` |
| `-count` with `count: u8` (DN §6.5) | CE-EXP-6 | `invalid/exp-141-unary-minus-unsigned.card` |

*Invalid:* an integer operand of `and`; there is no numeric truthiness (EXP-16). **CE-EXP-1**. (conformance: `invalid/exp-143-boolean-operator-integer.card`)

```text
function check(flags: u8) -> bool {
    return Ok(flags and true);
}
```

## 6.4 Evaluation order

**EXP-20 [Agreed]** Operands are evaluated left to right, each exactly once, before the operator is applied. This also applies to array-list elements, constructor fields in their written order, and call arguments. An index or slice is evaluated in this order: receiver, then index (or start and end), then the bounds check.
*Sources: D-104; DN §3.5, §3.7, §9.3.*

**EXP-21 [Agreed]** `a and b` evaluates `b` only if `a` is `true`. `a or b` evaluates `b` only if `a` is `false`. An operand that is not evaluated has no effects and cannot fail at runtime, although it is still type-checked.
*Sources: D-104; DN §3.5.*

**EXP-22 [Agreed]** The semantics in this chapter do not depend on build mode or optimization level. An implementation may reorder or remove operations, or omit a check, only if it has proved that doing so changes nothing observable, including which failure occurs and when. The stores of a `wipe` statement are the one exception: they are never removed (STM-23).
*Sources: D-338; DN §3.5, §6.5.*

### Examples

*Valid:* the index is used only after its bounds have been checked. (conformance: `valid/exp-015-short-circuit-index.card`)

```text
session buffer: u8[16];

function is_free(index: u8) -> bool {
    return Ok((index < 16) and (buffer[index] == 0));
}
```

## 6.5 Arithmetic semantics and failures

At runtime, an arithmetic failure *traps*: the current command terminates with the given trap kind (chapter 13). If the same failure is found during compile-time evaluation, it is a compilation error instead (CEX-9).

**EXP-23 [Agreed]** `+`, `-` and `*` compute the exact mathematical result of the operation on the operand values. If the result is in the range of the result type `T`, that is the value. Otherwise:

- a result above the maximum of `T` is `trap(OVERFLOW)`;
- a result below the minimum of `T`, including an unsigned subtraction below zero, is `trap(UNDERFLOW)`.

No wider intermediate type is ever used, and every intermediate result is checked by itself.
*Sources: D-058, D-087, D-431 (OI-31); DN §3.3, §3.5, §6.2.*

**EXP-24 [Agreed]** Division and remainder work as follows:

1. If the divisor is zero, the result is `trap(DIV-ZERO)` for both `/` and `%`.
2. `/` truncates toward zero.
3. For a signed type, the minimum value divided by −1 is `trap(OVERFLOW)`, because the exact quotient is above the maximum.
4. `a % b` equals `a − (a / b) × b`. It is zero or has the sign of `a`.
5. The minimum value `% −1` is 0. It does not trap.

An implementation must produce these results even where the processor or host language behaves differently.
*Sources: D-088, D-089, D-431 (OI-31); DN §3.5, §6.5.*

**EXP-25 [Agreed]** Unary `-x` produces the negation of `x`. If `x` is the minimum value of its signed type, the result is `trap(NEGATION)`.
*Sources: D-090, D-334, D-431 (OI-31); DN §6.5.*

**EXP-26 [Agreed]** For a shift of `x` by `n`, where `x` has unsigned type `T` of width `N` bits:

- If `n ≥ N`, the result is `trap(SHIFT)`.
- `x << n` shifts the bits left. Bits moved beyond the width are discarded, and zero bits are inserted on the right. This is not checked multiplication, so it never overflows.
- `x >> n` shifts the bits right, inserting zero bits on the left.

*Sources: D-336; DN §3.5.*

**EXP-27 [Agreed]** Bitwise operators work bit by bit on the `N`-bit unsigned value. `~x` inverts all `N` bits of `x`.
*Sources: D-336; DN §3.5.*

**EXP-28 [Agreed]** Ordering and equality compare the mathematical values of integers, the values of Booleans, and the variant identities of enums.
*Sources: D-335; DN §3.5, §3.11.*

## 6.6 Checked and wrapping intrinsics

**EXP-29 [Agreed]** The *checked arithmetic intrinsics* are:

| Intrinsic | Operands |
|---|---|
| `checked_add(a, b)` | Two operands of the same integer type `T` |
| `checked_sub(a, b)` | Two operands of the same integer type `T` |
| `checked_mul(a, b)` | Two operands of the same integer type `T` |
| `checked_div(a, b)` | Two operands of the same integer type `T` |
| `checked_rem(a, b)` | Two operands of the same integer type `T` |
| `checked_neg(a)` | One operand of a signed type `T` |

Operand types follow EXP-11. Each intrinsic synthesizes `Outcome(T)` (chapter 9). It does not trap for the conditions it checks. Instead it produces:

- `Ok(r)`, where `r` is the result of the corresponding operator (§6.5);
- `Err(CardError.Overflow)` or `Err(CardError.Underflow)` where that operator would trap with `OVERFLOW` or `UNDERFLOW`;
- `Err(CardError.DivisionByZero)` for a zero divisor;
- `Err(CardError.Overflow)` from `checked_div` for the minimum value divided by −1, and from `checked_neg` for the minimum value;
- `Ok(0)` from `checked_rem` for the minimum value `% −1`.

The `CardError` member names are placeholders, and their codes are platform-defined (Annex B). A trap while evaluating an operand still occurs normally.
*Sources: D-091, D-415 (OI-15), D-431 (OI-31); DN §6.2, §6.5.*

**EXP-30 [Agreed]** The *wrapping arithmetic intrinsics* are `wrapping_add(a, b)`, `wrapping_sub(a, b)` and `wrapping_mul(a, b)`. Both operands have the same integer type `T` under EXP-11. Each synthesizes `T`, a direct value. The result is the exact result modulo 2^N, where `N` is the width of `T`, interpreted as two's complement when `T` is signed. These intrinsics never fail. There are no wrapping division, remainder or negation intrinsics.
*Sources: D-092; DN §6.5.*

### Examples

*Valid:* a wrapping intrinsic, and a checked intrinsic consumed by `match`. (conformance: `valid/exp-013-wrapping.card`, `valid/exp-014-checked-in-match.card`)

```text
session balance: u32;

function debit(amount: u32) {
    match checked_sub(balance, amount) {
        Ok(value) => {
            balance = value;
        }
        Err(error) => {
            return Err(error);
        }
    }
    return Ok();
}
```

*Invalid:* a checked intrinsic whose operands are all literals has no integer context. **CE-EXP-3**. (conformance: `invalid/exp-142-checked-no-context.card`)

*Invalid:* a wrapping intrinsic with too few arguments. **CE-EXP-16**. (conformance: `invalid/exp-138-argument-count.card`)

### Intrinsics and array comparison

**EXP-52 [Agreed]** An *intrinsic* is an operation that this specification defines completely in terms of language values. The intrinsics are `fill`, `convert`, `checked_convert`, the `checked_*` and `wrapping_*` operations, `truncate`, `encode_be`, `encode_le`, `decode_be`, `decode_le`, `equal` and `compare`. Every intrinsic:

- behaves identically on every conforming platform;
- fails only as this specification says: by a compile error, a trap, or an `Err` defined for it here (such as the `checked_*` operations);
- is reached by its predeclared name (NAM-14), never through a `card.` path.

An operation that depends on platform state or hardware is a platform API instead (PLT-30).
*Sources: D-446 (OI-46); DN §3.2.*

**EXP-53 [Agreed]** `equal(ref a, ref b)` compares two arrays element by element:

- **Arguments.** Exactly two arguments (otherwise **CE-EXP-16**), each passed with `ref` (otherwise **CE-FUN-2**). Each is a fixed array, a view or a slice (FUN-18). Their element types must be identical, otherwise **CE-EXP-1**. The element type must be one that `==` accepts: an integer type, `bool` or an enum. An aggregate element type is **CE-EXP-6**.
- **Result.** It synthesizes `bool`. The result is `true` exactly when the two lengths are equal and each pair of elements is equal under `==`.
- **Failure.** It never fails and never traps.
- **Timing.** Its execution time depends only on the two lengths, never on the contents (PLT-31).
*Sources: D-448 (OI-48); DN §3.2.*

**EXP-54 [Agreed]** `compare(ref a, ref b)` orders two arrays lexicographically:

- **Arguments.** As for `equal` (EXP-53), except that the element type must be an integer type. Any other element type is **CE-EXP-6**.
- **Result.** It synthesizes `i8`: `-1` if `a` sorts before `b`, `0` if they are equal, and `1` if `a` sorts after `b`. Elements are compared by their mathematical values from index 0. When one array is a proper prefix of the other, the shorter one sorts first.
- **Failure.** It never fails and never traps. It has no timing requirement.
*Sources: D-448 (OI-48); DN §3.2.*

*Valid:* `equal` and `compare` on whole arrays. (conformance: `valid/exp-019-equal-and-compare.card`)

*Invalid:* `equal` on arrays with different element types. **CE-EXP-1**. (conformance: `invalid/exp-145-equal-element-types.card`)

*Invalid:* `compare` on `bool` elements. **CE-EXP-6**. (conformance: `invalid/exp-146-compare-bool.card`)

*Invalid:* `equal` with by-value arguments. **CE-FUN-2**. (conformance: `invalid/exp-147-equal-by-value.card`)

## 6.7 Conversions

**EXP-31 [Agreed]** The operand of `convert`, `checked_convert` and `truncate` must synthesize an integer type `S`, its *source type*, without using the type argument. A literal-only operand has no source type and is **CE-EXP-8**. The type argument `T` must be an integer type. A non-integer source or target, such as `bool`, an enum or an aggregate, is **CE-EXP-8**.
*Sources: D-083, D-086; DN §3.2, §3.3.*

**EXP-32 [Agreed]** `convert<T>(e)` is valid only when every value of `S` is in the range of `T`. The value that `e` happens to have does not matter. Otherwise it is **CE-EXP-8**. It synthesizes `T` and yields the same numeric value. It never fails at runtime. For example, `u8` to `u16`, `i8` to `i32` and `u8` to `i16` are valid. `u16` to `i16`, `i16` to `u32` and `u32` to `u8` are not.
*Sources: D-083, D-095; DN §3.2.*

**EXP-33 [Agreed]** `checked_convert<T>(e)` synthesizes `Outcome(T)`. It produces `Ok(v)` when the value of `e` is in the range of `T`. Otherwise it produces `Err(CardError.ConversionRange)`, a placeholder name. A negative value converted to an unsigned type fails, even when the target is wider. The intrinsic never truncates, wraps or clamps.
*Sources: D-083, D-415 (OI-15); DN §3.2.*

**EXP-34 [Agreed]** `truncate<T>(e)` synthesizes `T`, a direct value. Its result is the low `N` bits of the two's-complement representation of the value of `e`, interpreted in `T`, where `N` is the width of `T`. That is the value of `e` modulo 2^N, read as two's complement when `T` is signed. It never fails. `truncate` is the only deliberately lossy integer conversion.
*Sources: D-432 (OI-32).*

**EXP-35 [Agreed]** There are no other conversions:

- no general cast;
- no conversion to or from `bool` or enums;
- no conversion between array or structure types.

To get a Boolean from an integer, write a comparison, such as `flags != 0`.
*Sources: D-100, D-101; DN §3.2, §3.4, §3.11.*

### Examples

*Valid:* guaranteed conversions. (conformance: `valid/exp-006-guaranteed-conversions.card`)

```text
function widen(small: u8, signed_small: i8) -> u32 {
    var large: u16 = convert<u16>(small);
    var signed_value: i16 = convert<i16>(small);
    var wide: i32 = convert<i32>(signed_small);
    return Ok(convert<u32>(large));
}
```

*Valid:* a checked conversion consumed by `match` (DN §3.2). (conformance: `valid/exp-017-checked-convert.card`)

```text
function narrow(incoming: u16) -> u8 {
    match checked_convert<u8>(incoming) {
        Ok(value) => {
            return Ok(value);
        }
        Err(error) => {
            return Err(error);
        }
    }
}
```

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `convert<u8>(value)` with `value: u16` (DN §3.2) | CE-EXP-8 | `invalid/exp-111-convert-narrowing.card` |
| `convert<u32>(32)` (DN §3.3) | CE-EXP-8 | `invalid/exp-112-convert-unknown-source.card` |
| `truncate<u8>(300)` | CE-EXP-8 | `invalid/exp-136-truncate-unknown-source.card` |

*Invalid:* there is no conversion to `bool`; write `flags != 0` instead (EXP-35). **CE-EXP-8**. (conformance: `invalid/exp-144-convert-to-bool.card`)

```text
function check(flags: u8) -> bool {
    return Ok(convert<bool>(flags));
}
```

## 6.8 Integers and bytes

**EXP-36 [Agreed]** `encode_be(e)` and `encode_le(e)` require `e` to synthesize one of `u16`, `u32`, `i16` or `i32`. Any other type, or a literal-only operand, is **CE-EXP-8**. Each synthesizes `u8[N]`, a direct value, where `N` is 2 or 4, the width of the operand type in bytes. The array holds the two's-complement representation of the value:

- `encode_be` writes the most significant byte at index 0;
- `encode_le` writes the least significant byte at index 0.

*Sources: D-432 (OI-32), D-342; DN §3.4.*

**EXP-37 [Agreed]** `decode_be<T>(ref e)` and `decode_le<T>(ref e)` require `T` to be one of `u16`, `u32`, `i16` or `i32`. Any other `T` is **CE-EXP-8**. The single argument is passed with `ref` (chapter 8) and has the parameter type `ref u8[]`, so it may be a `u8` fixed array or a `u8` slice. Each synthesizes `T`, a direct value:

- At runtime, if the length of the argument is not the width of `T` in bytes, the result is `trap(BOUNDS)`.
- Otherwise the bytes are read in the stated order (big-endian for `_be`, little-endian for `_le`) and interpreted as two's complement when `T` is signed.

*Sources: D-432 (OI-32), D-342; DN §3.4.*

**EXP-38 [Agreed]** Integers and bytes are converted only explicitly, through EXP-34, EXP-36 and EXP-37, or through arithmetic, shifts and masks. Byte order is always stated by the intrinsic chosen. The language never encodes values implicitly, for example when they are stored, passed or returned.
*Sources: D-342, D-427; DN §3.4, §4.*

### Examples

*Valid:* `truncate` and the byte-order intrinsics. (conformance: `valid/exp-016-truncate-and-bytes.card`)

```text
function encode_amount(amount: u32, request: ref u8[]) -> u8 {
    var low: u8 = truncate<u8>(amount);
    var bytes: u8[4] = encode_be(amount);
    var parsed: u32 = decode_be<u32>(ref request);
    var little: u16 = decode_le<u16>(ref request[0..2]);
    return Ok(low);
}
```

*Invalid:* `encode_be` of a `u8`, which is not an accepted width. **CE-EXP-8**. (conformance: `invalid/exp-137-encode-unsupported-type.card`)

## 6.9 Indexing, `.length` and field selection

**EXP-39 [Agreed]** An index expression `a[i]` works as follows:

- **Receiver:** `a` must have a fixed array type `T[N]` or a view type `T[]`. It synthesizes `T`.
- **Index:** `i` must synthesize `u8`, `u16` or `u32`. An index containing no typed operand checks against `u32` (EXP-10). A typed unsigned index keeps its own type and is not converted. An index of a signed type, `bool`, an enum or an aggregate type is **CE-EXP-9**, even if its value would be valid.
- **Evaluation:** evaluate `a`, then `i`, then check that the value of `i` is less than the length of `a`. If it is not, the result is `trap(BOUNDS)`. An index is never truncated or wrapped. A constant-only index into a fixed array is checked during compilation instead (CEX-10).

*Sources: D-062, D-085; DN §3.3, §8.1.*

**EXP-40 [Agreed]** `x.length`, where `x` has a fixed array type or a view type, synthesizes `u32`. Its value is the number of elements, not bytes. For a fixed array that is `N`. For a view it is the length of the supplied region. `.length` is read-only: chapter 7 rejects assigning to it. At runtime `x` is still evaluated, so its calls, `attempt` propagation and bounds checks happen even when the length is known from the type. If `x` has another type, `.length` is a field selection under EXP-41.
*Sources: D-061, D-339; DN §8.1.*

**EXP-41 [Agreed]** A field selection `x.f`, where `x` has a structure type `S`, requires `S` to declare a field `f`. It synthesizes that field's type. A field selection on a structure without that field, or on a value that is neither a structure nor an array (`.length`), is **CE-EXP-13**. Qualified enum variants and error members are resolved by NAM-17. A qualified enum variant synthesizes its enum type.
*Sources: D-047, D-317; DN §4.2, §9.*

**EXP-42 [Agreed]** A slice `a[s..e]` is parsed by the expression grammar. Its typing, where it may appear, and its bounds checks are defined in chapter 8. A slice in any other position is rejected there.
*Sources: D-119, D-410 (OI-10); DN §8.4.*

### Examples

*Valid:* literal-only, `u8` and `u16` indices. (conformance: `valid/exp-009-index-types.card`)

```text
session buffer: u8[16];

function indices(small: u8, medium: u16) -> u8 {
    var first: u8 = buffer[0];
    var second: u8 = buffer[1 + 2];
    var third: u8 = buffer[small];
    return Ok(buffer[medium]);
}
```

*Valid:* `.length` of an array field. (conformance: `valid/exp-010-length-of-field.card`)

```text
struct Account {
    identifier: u8[4];
    balance: u32;
}

session account: Account;

function identifier_size() -> u32 {
    return Ok(account.identifier.length);
}
```

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `buffer[signed_index]` with `signed_index: i16` (DN §8.1) | CE-EXP-9 | `invalid/exp-113-signed-index.card` |
| `buffer[flag]` with `flag: bool` | CE-EXP-9 | `invalid/exp-114-bool-index.card` |
| `account.missing` | CE-EXP-13 | `invalid/exp-134-unknown-field.card` |
| `count.length` with `count: u32` | CE-EXP-13 | `invalid/exp-140-length-on-integer.card` |

## 6.10 Aggregate construction

**EXP-43 [Agreed]** An array list `[e1, …, en]` only checks against an expected fixed array type `T[N]`. It never synthesizes a type. Without an expected type it is **CE-EXP-10**. It must have exactly `N` elements. Any other count is **CE-EXP-11**: there is no padding or truncation. Each element checks against `T`. The elements are evaluated left to right, and the result is a direct array value.
*Sources: D-063, D-130, D-341; DN §8, §9.*

**EXP-44 [Agreed]** `fill(e)` only checks against an expected fixed array type `T[N]`. Without an expected type it is **CE-EXP-10**. The argument `e` checks against `T`. At runtime:

1. `e` is evaluated exactly once.
2. Its value is copied independently into each of the `N` elements.

The value is captured before any destination is written, so `buffer = fill(buffer[0])` copies the original first element. `fill` produces a direct array value, never an outcome. It allocates nothing dynamically. A fallible value must be obtained in a local first, because of the nested-call rule (EXP-49).
*Sources: D-063, D-064, D-079, D-340; DN §8, §8.2, §8.3.*

**EXP-45 [Agreed]** A structure constructor `S { f1: e1, …, fk: ek }` requires `S` to name a structure type. It synthesizes `S`. Every field of `S` must appear exactly once:

- a missing field is **CE-EXP-12**;
- a field `S` does not declare is **CE-EXP-12**;
- a field given twice is **CE-EXP-12**.

Fields may be written in any order. Each `ei` checks against its field's type. The field expressions are evaluated in written order, not declaration order. If one fails, the later ones are not evaluated and no value is produced. The result is a direct structure value. There are no field defaults and no shorthand for unspecified fields.
*Sources: D-070, D-071, D-130; DN §9.3.*

**EXP-46 [Agreed]** Every array list, `fill` result and constructor result is a complete, independent value. It shares nothing with the values it was built from (chapter 8).
*Sources: D-116; DN §3.8.*

### Examples

*Valid:* `fill` from a local, and `fill` from an element of the destination itself (DN §8.3). (conformance: `valid/exp-011-fill-forms.card`)

```text
session buffer: u8[16];

function read_byte() -> u8 {
    return Ok(0xA5);
}

function refill() {
    var next_byte: u8 = attempt read_byte();
    buffer = fill(next_byte);
    buffer = fill(buffer[0]);
    return Ok();
}
```

*Valid:* constructor fields in a different order from the declaration (DN §9.3). (conformance: `valid/exp-012-constructor-order.card`)

```text
struct Account {
    balance: u32;
    identifier: u8[4];
    counters: u32[8];
}

function build() -> Account {
    var working: Account = Account { counters: fill(0), balance: 100, identifier: [1, 2, 3, 4] };
    return Ok(working);
}
```

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `short = [1, 2];` with `short: u8[4]` (DN §8) | CE-EXP-11 | `invalid/exp-128-list-too-short.card` |
| `long = [1, 2, 3];` with `long: u8[2]` (DN §8) | CE-EXP-11 | `invalid/exp-129-list-too-long.card` |
| `fill(0).length` | CE-EXP-10 | `invalid/exp-130-fill-without-context.card` |
| A constructor missing `balance` | CE-EXP-12 | `invalid/exp-131-constructor-missing-field.card` |
| A constructor with an undeclared field | CE-EXP-12 | `invalid/exp-132-constructor-unknown-field.card` |
| A constructor with `balance` twice | CE-EXP-12 | `invalid/exp-133-constructor-duplicate-field.card` |

**EXP-55 [Agreed]** A byte-string literal (LEX-25) of `N` bytes is an array list of `N` integer literals, one per byte, in order. It has the same typing and positions as that array list (EXP-43):

- it has no type of its own;
- it checks against `u8[N]`. Another length is **CE-EXP-11**, and no expected array type is **CE-EXP-10**;
- it is a constant expression (chapter 5).

For example, `const KEY_ID: u8[2] = b"id";` is the same as `const KEY_ID: u8[2] = [0x69, 0x64];`. Like an array list, it is not storage, so passing it as a `ref` argument is **CE-FUN-3**. Declare a `const` instead.
*Sources: D-453 (OI-53).*

*Valid:* byte strings, escapes included, as constants, initializers and slice-assignment sources. (conformance: `valid/exp-020-byte-strings.card`)

*Invalid:* a byte string of 2 bytes for a `u8[3]`. **CE-EXP-11**. (conformance: `invalid/exp-148-byte-string-length.card`)

## 6.11 Calls

**EXP-47 [Agreed]** A call `f(a1, …, an)` names its target directly. The target is one of:

- an ordinary function;
- a compiler intrinsic;
- a platform API, written as a `card.` path (NAM-18).

Any other target is **CE-EXP-15**. That includes a constant, a variable, a type, or the `command` (chapter 12). Function values do not exist. The number of arguments must equal the number of parameters, or it is **CE-EXP-16**. Each argument checks against its parameter type (EXP-10). Its mode (`ref`, `inout` or none) must match the parameter's mode under chapter 8.
*Sources: D-026, D-031, D-035, D-406; DN §3.7, §4.1.*

**EXP-48 [Agreed]** A call synthesizes `Outcome(T)` when it is any of:

- a call to an ordinary function or platform API whose successful payload type is `T`;
- a call to a checked intrinsic (EXP-29);
- a call to `checked_convert` (EXP-33).

A call with no successful payload synthesizes `Outcome()`. An outcome is not a value. An expression of outcome type may appear only where chapter 9 allows it to be consumed:

- as the scrutinee of `match`;
- as the operand of `attempt`;
- as the operand of a whole-outcome `return`.

Anywhere else it is **CE-EXP-14**: for example as an operand, an initializer, an argument, an index, a receiver or a payload. The intrinsics `convert`, `truncate`, `wrapping_*`, `fill`, `encode_*` and `decode_*` synthesize direct values instead.
*Sources: D-012, D-015, D-016; DN §3.5, §6.1, §6.3.*

**EXP-49 [Agreed]** An argument of any call must not contain a call or an `attempt` anywhere inside it, including inside an index, a constructor or another nested expression. Violating this is **CE-EXP-7**. It applies to calls to ordinary functions, platform APIs and every intrinsic, whether it produces a value or an outcome. It also applies in constant expressions (CEX-14). Evaluate the inner call into a local first. `Ok(…)`, and `Err(…)` in `return` and `abort`, are not calls, so `return Ok(attempt read_value());` is valid.
*Sources: D-027, D-331; DN §3.7.*

**EXP-50 [Agreed]** The arguments of a call are evaluated left to right, and all of them are evaluated before the callee starts. Chapter 8 defines how reference and slice arguments are prepared and bounds-checked before entry.
*Sources: D-104; DN §3.7.*

### Examples

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `const X: u32 = convert<u32>(convert<u16>(SMALL));` (DN §3.10) | CE-EXP-7 | `invalid/exp-124-nested-convert.card` |
| `attempt process_value(convert<u32>(small));` (DN §3.7) | CE-EXP-7 | `invalid/exp-125-intrinsic-in-argument.card` |
| `attempt process(inout counter, attempt next_value());` (DN §3.7) | CE-EXP-7 | `invalid/exp-126-attempt-in-argument.card` |
| `var result: u32 = balance + subtract(balance, amount);` (DN §3.5) | CE-EXP-14 | `invalid/exp-127-outcome-as-value.card` |
| `attempt LIMIT();` with `LIMIT` a constant | CE-EXP-15 | `invalid/exp-139-call-non-function.card` |

## 6.12 Where `attempt` may appear

**EXP-51 [Agreed]** `attempt e` may appear as an expression in any runtime expression position, except:

- inside a call argument (EXP-49);
- in a constant expression (CEX-5).

Inside a transaction, its failure path aborts the transaction (TXN-18).

When `attempt` is in the right operand of `and` or `or`, it is evaluated only if that operand is evaluated (EXP-21). The typing and behavior of `attempt`, and its statement form for calls with no payload, are defined in chapter 9.
*Sources: D-014, D-408 (OI-8); DN §6.3, §8.1, §9.3.*

## 6.13 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-EXP-1** | A type does not match the type required by its context, including a literal checked against a non-integer type | EXP-7, EXP-12, EXP-16, EXP-18, EXP-53, STM-8, STM-11, STM-25, FUN-8, FUN-24 |
| **CE-EXP-2** | An integer literal is out of range for its expected type | EXP-7, STM-13 |
| **CE-EXP-3** | An integer literal has no type context | EXP-11, EXP-29 |
| **CE-EXP-4** | Different binary operators at one grouping level | EXP-2, EXP-5 |
| **CE-EXP-5** | A chain of comparisons | EXP-4 |
| **CE-EXP-6** | An operator applied to a type it does not accept | EXP-8, EXP-13–EXP-15, EXP-17–EXP-19, EXP-53, EXP-54 |
| **CE-EXP-7** | A call or `attempt` inside a call argument | EXP-49 |
| **CE-EXP-8** | An invalid conversion or byte intrinsic: unknown source type, non-integer type, conversion not guaranteed, or unsupported width | EXP-31, EXP-32, EXP-36, EXP-37 |
| **CE-EXP-9** | An index whose type is not `u8`, `u16` or `u32` | EXP-39, FUN-19 |
| **CE-EXP-10** | An array list or `fill` with no expected array type | EXP-43, EXP-44, EXP-55, FUN-24 |
| **CE-EXP-11** | An array list with the wrong number of elements | EXP-43, EXP-55 |
| **CE-EXP-12** | A constructor field that is missing, undeclared or repeated | EXP-45 |
| **CE-EXP-13** | A field selection the receiver does not have | EXP-41 |
| **CE-EXP-14** | An outcome used where a value is required | EXP-48 |
| **CE-EXP-15** | A call whose target is not callable | EXP-47, HEP-3 |
| **CE-EXP-16** | A call with the wrong number of arguments | EXP-47, EXP-53 |

The trap kinds `OVERFLOW`, `UNDERFLOW`, `DIV-ZERO`, `NEGATION`, `SHIFT` and `BOUNDS` used in this chapter are the agreed placeholder names (D-415). Chapter 13 catalogs them.
