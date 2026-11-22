# 7. Statements and control flow

CardLang Language Specification, Draft 0.2.

This chapter defines blocks and statements:

- local variables;
- assignment;
- the control-flow statements `if`, `while`, `for`, `break`, `continue` and `match` on enums;
- the control effect of `return` and `require`;
- the completion analysis that requires every function and command to end with an explicit outcome.

Related topics are defined elsewhere:

| Topic | Chapter |
|---|---|
| The forms and typing of `return Ok`/`Err`, whole-outcome forwarding, the `attempt` statement and outcome `match` patterns | 9 |
| `transaction` and `abort`, and the rule that `return`, `break` and `continue` must not cross a transaction boundary, and that `attempt` and `require` abort a transaction on their error path | 11 |
| Writing through references | 8 |
| Atomicity of persistent assignments | 10 |

As in earlier chapters, the statement grammar (Annex A §A.2.5) accepts a few forms that rules here then reject with specific error classes. These are storage keywords, assignment targets and match patterns.

## 7.1 Blocks and statements

```
Block               ::= '{' Statement* '}'
Statement           ::= VarStatement | AssignmentStatement | ExpressionStatement
                      | IfStatement | WhileStatement | ForStatement | MatchStatement
                      | BreakStatement | ContinueStatement | ReturnStatement | RequireStatement
                      | TransactionStatement | AbortStatement | WipeStatement | IgnoreStatement
ExpressionStatement ::= Expression ';'
```

**STM-1** A *block* is a brace-delimited sequence of statements. Every body is a block, and braces are always required, even around a single statement. That covers the bodies of functions, commands, `if`, `while`, `for` and `transaction`, and every match arm. CardLang has no `switch`, fall-through, `goto`, labelled loops or multi-level exits. `if` and `match` are statements; they produce no value.
*Sources: D-106, D-343, D-344; DN §3.0, §3.6.*

**STM-2** The only statement consisting of an expression is the `attempt` statement, `attempt call;`, defined in chapter 9. Any other expression used as a statement is **CE-STM-1**, for example `a + b;` or `x;`. A bare call `f();` discards an outcome, and chapter 9 rejects it.
*Sources: D-433 (OI-33); DN §6.3.*

**STM-3** A block is not itself a statement. A standalone `{ … }` among statements does not derive, so it is **CE-SYN-1**. Nested scopes come only from the bodies of control-flow statements and match arms.
*Sources: D-434 (OI-34).*

### Examples

*Invalid:* an expression used as a statement. **CE-STM-1**. (conformance: `invalid/stm-125-expression-statement.card`)

*Invalid:* a standalone block. **CE-SYN-1**. (conformance: `invalid/stm-126-standalone-block.card`)

## 7.2 Local variables

```
VarStatement ::= StorageKeyword+ Identifier ':' Type ( '=' Expression )? ';'
```

**STM-4** A local variable is declared with `var name: T;` or `var name: T = e;`. Chapter 3 rejects any other storage keyword (NAM-10). `T` must be a value type: an unsized `T[]` is rejected by TYP-21. The initializer `e` checks against `T` (EXP-10). Local variables are mutable. Their scope and visibility follow NAM-19 to NAM-21.
*Sources: D-006; DN §3.6, §5.1.*

**STM-5** Each time execution reaches a local declaration:

- **Without an initializer**, the variable receives `default(T)` (TYP-22).
- **With an initializer**, `e` is evaluated, and the variable is created holding exactly that value. No default value is stored first, and none can be observed.
- **If evaluating `e` fails**, through `attempt` propagation or a trap, the variable is never created. No default is substituted, and side effects that happened earlier in `e` are not undone.

*Sources: D-123, D-128, D-350; DN §3.9.*

### Examples

*Valid:* locals with and without initializers. (conformance: `valid/stm-001-local-defaults-and-initializers.card`)

```text
function locals() -> u32 {
    var counter: u32;
    var working: u8[16];
    var limit: u32 = 100;
    counter = limit + 1;
    return Ok(counter);
}
```

## 7.3 Assignment

```
AssignmentStatement ::= Expression ( '=' | CompoundOperator ) Expression ';'
CompoundOperator    ::= '+=' | '-=' | '*=' | '/=' | '%=' | '&=' | '|=' | '^=' | '<<=' | '>>='
```

**STM-6** Assignment is a statement, never an expression. It has exactly one `=`. Consequently, none of these exist, and each fails to derive (**CE-SYN-1**):

- chained assignment, such as `a = b = 0;`;
- assignment inside a condition;
- increment and decrement, such as `count++;`.

Compound assignment, such as `x += 1;`, is defined by STM-25.
*Sources: D-105, D-349; DN §3.5.*

**STM-7** The left side of an assignment must be a *place*. A place is one of:

- the name of a local variable;
- the name of a `persistent` or `session` global;
- the name of an `inout` parameter;
- a path of field selections and index operations rooted in one of the above.

Any other left side is **CE-STM-2**. That includes:

- a constant, or any field or element of one;
- a by-value parameter;
- a `ref` parameter, or a path rooted in one (chapter 8);
- a `for` index or pattern binding;
- `.length`;
- a slice, except as the left side of a slice assignment (FUN-24);
- a function, type, enum variant or error member;
- any other expression.

Every part of a constant is immutable (TYP-16).
*Sources: D-112, D-073, D-061, D-108, D-410; DN §3.6, §3.7, §5.1, §8.1.*

**STM-8** The right side checks against the type of the place (EXP-10, EXP-12):

- For arrays, the element types must be identical and the lengths equal (TYP-4). A different length or element type is **CE-EXP-1**.
- For structures, the types must be identical, because structures are nominal.

Assignment stores a complete, independent copy, including all nested fields and elements. No sharing with the source remains.
*Sources: D-078, D-116; DN §3.8, §8.2, §9.3.*

**STM-9** An assignment is evaluated in this order:

1. Evaluate the place's path from left to right. Each index expression is evaluated exactly once, and its bounds are checked when it is reached. An out-of-bounds index is `trap(BOUNDS)`, and the right side has not yet been evaluated.
2. Evaluate the right side.
3. Store the value into the place.

Index expressions are never re-evaluated after the right side, even if the right side changed the variables they read. The right side's value is complete before the store begins. So in `buffer = fill(buffer[0])`, the original first element is copied into every element.
*Sources: D-080, D-409 (OI-9), D-340; DN §8.2, §8.3.*

**STM-10** If evaluating the right side fails, through `attempt` propagation or a trap, the store does not happen. Effects that happened earlier, while evaluating the path or the right side, are not undone. Chapter 10 defines the atomicity of stores into persistent places.
*Sources: D-080, D-057; DN §7.1, §8.2.*

```
WipeStatement ::= 'wipe' Expression ';'
```

**STM-23** `wipe p;` stores `default(T)` (TYP-22) into every element of `p`. The operand `p` must be an assignable place (STM-7), or a slice of one (FUN-24). Any other operand is **CE-STM-2**.

- **Evaluation.** As for an assignment (STM-9): the place's path, and a slice's endpoints and region, are evaluated and checked first, and then the store happens.
- **The stores are always performed.** They are never removed, merged or postponed past the end of the place's lifetime, even when nothing later reads the place. This is the one exception to EXP-22, so that secrets can be erased reliably (PLT-34). Locals are also erased when their frame ends (PLT-35), so `wipe` of a local only erases it sooner.
- **Persistence.** A `wipe` of persistent storage is a persistent assignment. It is atomic for its whole destination (STA-11), STA-13 applies to that destination, and it participates in an active transaction.
*Sources: D-449 (OI-49), D-451 (OI-51); DN §3.9.*

*Valid:* `wipe` of a local, a session global and an `inout` view. (conformance: `valid/stm-013-wipe.card`)

*Invalid:* `wipe` of a constant. **CE-STM-2**. (conformance: `invalid/stm-128-wipe-constant.card`)

### Examples

*Valid:* assignment to a local, globals, a nested field, an array element and an `inout` parameter. (conformance: `valid/stm-002-assignment-places.card`)

```text
struct Identity {
    identifier: u8[4];
    version: u16;
}

struct Account {
    identity: Identity;
    balance: u32;
    counters: u32[8];
}

persistent account: Account;
session buffer: u8[16];

function update(target: inout u32, index: u8) {
    var local: u32 = 1;
    local = 2;
    buffer[index] = 0xFF;
    account.identity.version = 2;
    account.counters[0] = account.counters[0] + 1;
    target = local;
    return Ok();
}
```

*Valid:* whole-array assignment between identical array types (DN §8.2). (conformance: `valid/stm-003-whole-array-assignment.card`)

```text
function copy() {
    var source: u8[16];
    var destination: u8[16];
    destination = source;
    return Ok();
}
```

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `a = b = 0;` (DN §3.5) | CE-SYN-1 | `invalid/stm-101-chained-assignment.card` |
| `if ready = true { … }` | CE-SYN-1 | `invalid/stm-102-assignment-in-condition.card` |
| `count++;` | CE-SYN-1 | `invalid/stm-104-increment.card` |
| `LIMIT = 5;` with `LIMIT` a constant | CE-STM-2 | `invalid/stm-105-assign-constant.card` |
| `IDENTIFIER[0] = 9;` with `IDENTIFIER` a constant | CE-STM-2 | `invalid/stm-106-assign-constant-element.card` |
| `amount = 0;` with `amount` a by-value parameter | CE-STM-2 | `invalid/stm-107-assign-by-value-parameter.card` |
| `index = 3;` inside `for index: …` | CE-STM-2 | `invalid/stm-108-assign-for-index.card` |
| `buffer.length = 10;` (DN §8.1) | CE-STM-2 | `invalid/stm-109-assign-length.card` |
| `value = 1;` with `value` bound by `Ok(value)` | CE-STM-2 | `invalid/stm-110-assign-match-binding.card` |
| `helper = 1;` with `helper` a function | CE-STM-2 | `invalid/stm-127-assign-function.card` |

```
IgnoreStatement ::= 'ignore' PostfixExpression ';'
```

**STM-24** `ignore c;` evaluates the call `c` and discards its outcome, whether `Ok` (with or without a payload) or `Err`. `c` must be a call that produces an outcome. Anything else is **CE-OUT-4**. Traps are not affected: a trap in `c` ends the command as usual. `ignore` never leaves the enclosing block, so it is valid inside a transaction. It is the explicit form of discarding an outcome, which OUT-7 otherwise forbids.
*Sources: D-456 (OI-56).*

**STM-25** A *compound assignment* `p op= e;`, where `op=` is one of `+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `<<=` and `>>=`, is evaluated as follows:

1. Evaluate the place `p`'s path once, and check its indices (STM-9 step 1).
2. Read the current value of `p`.
3. Evaluate `e`.
4. Apply `op` to the current value and `e`, with the semantics and checks of the binary operator (chapter 6). For example, an overflow traps (EXP-23).
5. Store the result into `p`.

The place is never evaluated twice: in `values[attempt next()] += 1;`, `next` is called once.

- **Typing.** `p` must be an assignable place (STM-7) that is not a slice. Otherwise it is **CE-STM-2**. The binary expression `p op e` must type as for the operator, with `e` as one whole operand, and its type must be the type of `p`. Otherwise it is **CE-EXP-1**.
- **Persistence.** A compound assignment to persistent storage is one atomic persistent assignment (STA-11).
- **Not an expression.** A compound assignment is a statement, never an expression (STM-6).
*Sources: D-457 (OI-57).*

*Valid:* `ignore` with and without a payload. (conformance: `valid/stm-014-ignore.card`)

*Valid:* all ten compound operators. (conformance: `valid/stm-015-compound-assignment.card`)

*Invalid:* a compound assignment to a constant. **CE-STM-2**. (conformance: `invalid/stm-129-compound-on-constant.card`)

*Invalid:* `ignore` of something that is not a call. **CE-OUT-4**. (conformance: `invalid/stm-130-ignore-non-call.card`)

## 7.4 `if`

```
IfStatement ::= 'if' ConditionExpression Block ( 'else' 'if' ConditionExpression Block )* ( 'else' Block )?
```

**STM-11** Each condition checks against `bool` (EXP-10): a condition of any other type is **CE-EXP-1**. There is no numeric truthiness. The conditions are evaluated in order, and the block of the first one that is `true` runs. If none is `true`, the final `else` block runs, if there is one. At most one block runs. Parentheses around a whole condition are optional. Mixed binary operators still need grouping (EXP-2), and a structure constructor in a condition needs parentheses (EXP-6).
*Sources: D-106, D-343; DN §3.6.*

### Examples

*Valid:* an `if`/`else if`/`else` chain in which every branch returns (DN §3.6). (conformance: `valid/stm-004-if-chain.card`)

```text
function classify(amount: u32, balance: u32) -> u8 {
    if amount == 0 {
        return Ok(0);
    } else if amount > balance {
        return Ok(1);
    } else {
        return Ok(2);
    }
}
```

*Invalid:* an integer condition. **CE-EXP-1**. (conformance: `invalid/stm-124-non-bool-condition.card`)

## 7.5 `while`

```
WhileStatement ::= 'while' ConditionExpression Block
```

**STM-12** The condition checks against `bool`. It is evaluated before each iteration, and the block runs while it is `true`, so the block may run zero times. `while true { … }` expresses a loop that ends only through `break`, `return`, `abort` or a trap. The language does not require termination to be proved. A command that runs out of the execution budget of its target is `trap(EXHAUSTED)` (chapter 13).
*Sources: D-106, D-347; DN §3.6.*

## 7.6 `for`

```
ForStatement ::= 'for' Identifier ':' Type 'in' ConditionExpression '..' ConditionExpression Block
```

**STM-13** In `for name: T in a..b { … }`, the index type `T` must be an integer type. Any other type is **CE-STM-6**. Both bounds `a` and `b` check against `T` (EXP-10), so each must fit `T`. For example, `for index: u8 in 0..256` is **CE-EXP-2**: use a wider index type.
*Sources: D-106, D-345; DN §3.6.*

**STM-14** A `for` statement runs as follows:

1. Evaluate `a`, then `b`, each exactly once, before any iteration. Later changes to the variables they read have no effect on the loop.
2. If `a ≥ b`, the block runs zero times.
3. Otherwise, the block runs once for each value `a, a + 1, …, b − 1`, in that order, with `name` bound to the value.

The binding `name` is local to the block and read-only (STM-7). Advancing the index is checked arithmetic, but it never fails, because no value exceeds `b − 1 < b`, and `b` fits `T`. Ranges are half-open and ascending, with a step of one. There are no descending ranges, other step sizes, or iteration directly over arrays.
*Sources: D-345; DN §3.6, §8.1.*

### Examples

*Valid:* `for` loops over `u8` and `i16`, an empty range, and a range bounded by `.length`. (conformance: `valid/stm-006-for-ranges.card`)

```text
session buffer: u8[16];

function ranges() -> i16 {
    var total: i16 = 0;
    for index: u8 in 0..16 {
        buffer[index] = 0;
    }
    for offset: i16 in -5..5 {
        total = total + offset;
    }
    for unused: u32 in 10..0 {
        total = 1;
    }
    for position: u32 in 0..buffer.length {
        buffer[position] = 1;
    }
    return Ok(total);
}
```

*Invalid:* an endpoint that does not fit the index type (DN §3.6). **CE-EXP-2**. (conformance: `invalid/stm-122-for-endpoint-out-of-range.card`)

*Invalid:* a `bool` index type. **CE-STM-6**. (conformance: `invalid/stm-121-for-bool-index.card`)

## 7.7 `break` and `continue`

```
BreakStatement    ::= 'break' ';'
ContinueStatement ::= 'continue' ';'
```

**STM-15** `break;` ends the nearest enclosing `while` or `for` loop. Execution continues after that loop. `continue;` ends the current iteration of the nearest enclosing loop:

- in a `while`, the condition is evaluated again;
- in a `for`, the next index value is used, or the loop ends.

`break` or `continue` outside a loop is **CE-STM-3**. Chapter 11 forbids them inside a transaction when the target loop is outside that transaction.
*Sources: D-106, D-346; DN §3.6.*

### Examples

*Valid:* a `while` loop with `continue` and `break` (DN §3.6). (conformance: `valid/stm-005-while-break-continue.card`)

```text
session buffer: u8[16];

function scan() -> u8 {
    var index: u8 = 0;
    var found: u8 = 0;
    while index < 16 {
        if buffer[index] == 0 {
            index = index + 1;
            continue;
        }
        if buffer[index] == 0xFF {
            break;
        }
        found = found + 1;
        index = index + 1;
    }
    return Ok(found);
}
```

*Invalid:* `break` outside a loop (conformance: `invalid/stm-111-break-outside-loop.card`), and `continue` outside a loop (conformance: `invalid/stm-112-continue-outside-loop.card`). Both are **CE-STM-3**.

## 7.8 `match` on enums

```
MatchStatement ::= 'match' ConditionExpression '{' MatchArm* '}'
MatchArm       ::= Pattern '=>' Block
Pattern        ::= 'Ok' '(' ( Identifier | '_' )? ')'
                 | 'Err' '(' ( Identifier | '_' | Identifier '.' Identifier | Identifier '(' ( Identifier | '_' ) ')' ) ')'
                 | Identifier '.' Identifier
                 | '_'
```

**STM-16** If the scrutinee of a `match` synthesizes an enum type `E`, every arm's pattern must be a qualified variant `E.V` of `E`. Each variant of `E` must appear exactly once. Each of the following is **CE-STM-4**:

- a missing variant;
- a repeated variant;
- a variant of another enum;
- the wildcard `_`;
- an `Ok`/`Err` pattern.

There is no catch-all arm, so adding a variant to `E` makes every `match` on it that has not been updated an error. The scrutinee is evaluated exactly once. The arm whose variant equals the value runs, and no other arm runs. The original value is not modified.
*Sources: D-069, D-344; DN §3.6, §3.11.*

**STM-17** If the scrutinee has outcome type, the `match` is an outcome match, defined in chapter 9. A scrutinee of any other type is **CE-STM-4**, because integers, Booleans, arrays and structures cannot be matched. Write `if` statements for those.
*Sources: D-069; DN §3.6.*

### Examples

*Valid:* a `match` that lists every variant (DN §3.11). (conformance: `valid/stm-007-enum-match.card`)

```text
enum OperationState {
    Idle;
    Receiving;
    Complete;
}

session state: OperationState;

function describe() -> u8 {
    match state {
        OperationState.Idle => {
            return Ok(0);
        }
        OperationState.Receiving => {
            return Ok(1);
        }
        OperationState.Complete => {
            return Ok(2);
        }
    }
}
```

*Valid:* a `match` whose arms complete normally, followed by a `return`. (conformance: `valid/stm-012-match-arms-may-complete.card`)

*Invalid:* each of these is in its own test, and each is **CE-STM-4**.

| Fault | Conformance |
|---|---|
| A variant is missing | `invalid/stm-113-enum-match-missing.card` |
| A variant appears twice | `invalid/stm-114-enum-match-duplicate.card` |
| A variant of another enum | `invalid/stm-115-enum-match-foreign.card` |
| A `_` arm | `invalid/stm-116-enum-match-wildcard.card` |
| An integer scrutinee | `invalid/stm-117-match-integer.card` |

## 7.9 `return` and `require`

```
ReturnStatement  ::= 'return' ( 'Ok' '(' Expression? ')' | 'Err' '(' Expression ')' | Expression ) ';'
RequireStatement ::= 'require' Expression 'else' Expression ';'
```

**STM-18** A `return` statement ends execution of the enclosing function or command and delivers an outcome to its caller, or to the host for the command. Its forms and their typing are defined in chapter 9:

- `return Ok(e);`
- `return Ok();`
- `return Err(e);`
- `return call;`

Chapter 11 forbids a `return` that would leave a transaction.
*Sources: D-106, D-107; DN §3.6, §6.1.*

**STM-19** `require c else M;` behaves exactly like `if not c { return Err(M); }`, including evaluation and typing. Lexically inside a transaction, it behaves as `if not c { abort Err(M); }` instead (TXN-18). `c` checks against `bool`. `M` must be a qualified member of the application's error set (NAM-16). A member of `CardError` is **CE-OUT-3**, because application code never originates a platform error (OUT-19, amended by D-437). Any other operand is **CE-STM-7**, including an integer, an error binding or a call.
*Sources: D-348, D-028, D-437 (OI-37); DN §3.6, §6.2, §6.3.*

### Examples

*Valid:* `require` before an arithmetic step that it makes safe (DN §6.1). (conformance: `valid/stm-008-require.card`)

```text
errors WalletError {
    InsufficientFunds = 1;
}

function subtract(current_balance: u32, amount: u32) -> u32 {
    require amount <= current_balance else WalletError.InsufficientFunds;
    return Ok(current_balance - amount);
}
```

*Invalid:* a `require` whose operand is an integer. **CE-STM-7**. (conformance: `invalid/stm-123-require-integer-operand.card`)

## 7.10 Completion analysis

**STM-20** Whether a statement *may complete normally* (continue to the next statement) is decided structurally by this table. No other analysis is used: no constant folding, no data-flow analysis and no prediction of traps.

| Construct | May complete normally |
|---|---|
| `return …;`, `abort …;` | Never |
| `break;`, `continue;` | Never (control goes to the loop) |
| A `var`, assignment or `attempt` statement; `require` | Always |
| `if` without a final `else` | Always |
| `if` … `else` | Only if at least one of its blocks may complete normally |
| `match` | Only if at least one of its arms may complete normally |
| `for`, and `while` whose condition is anything other than the literal `true` | Always |
| `while true` | Only if its body contains a `break` that targets this loop. Breaks that target nested loops do not count. A break counts even if the compiler could prove it is never reached |
| A block | Only if every statement in it may complete normally |
| `transaction { … }` | Only if its block may complete normally (chapter 11) |

*Sources: D-030; DN §3.7.*

**STM-21** The body of every function and command must not complete normally under STM-20. A body that may complete normally is **CE-STM-5**. The compiler never inserts an implicit success. This includes a no-payload function, which must end with an explicit `return Ok();`. A computation predicted to trap does not count as ending the body.
*Sources: D-030, D-034; DN §3.6, §3.7.*

**STM-22** Statements that can never be reached are permitted, for example statements after a `return`. They are still resolved, type-checked and constant-evaluated (CEX-7).
*Sources: D-351; DN §3.10.*

### Examples

*Valid:* `while true` without a `break` needs no following `return`. (conformance: `valid/stm-009-while-true-no-return.card`)

```text
function forever() -> u32 {
    while true {
    }
}
```

*Valid:* a `return` inside `while true`. (conformance: `valid/stm-011-while-true-with-return-inside.card`)

```text
session ready: bool;

function wait_ready() {
    while true {
        if ready {
            return Ok();
        }
    }
}
```

*Valid:* a statement after a `return`. (conformance: `valid/stm-010-statements-after-return.card`)

```text
function early() -> u32 {
    return Ok(1);
    var unused: u32 = 2;
}
```

*Invalid:* each of these is in its own test, and each is **CE-STM-5**.

| Fault | Conformance |
|---|---|
| No final `return` | `invalid/stm-118-missing-return.card` |
| An `if` without `else` that returns in its block only | `invalid/stm-119-if-without-else-return.card` |
| A `while true` with a `break`, and no `return` after the loop | `invalid/stm-120-while-true-with-break.card` |

## 7.11 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-STM-1** | An expression other than an `attempt` call used as a statement | STM-2 |
| **CE-STM-2** | The left side of an assignment is not an assignable place | STM-7, STM-23, STM-25, FUN-24 |
| **CE-STM-3** | `break` or `continue` outside a loop | STM-15 |
| **CE-STM-4** | An invalid `match`: missing, repeated or foreign variant; wildcard arm; or a scrutinee that cannot be matched | STM-16, STM-17 |
| **CE-STM-5** | A function or command body may complete normally | STM-21 |
| **CE-STM-6** | A `for` index type that is not an integer type | STM-13 |
| **CE-STM-7** | A `require` operand that is not a qualified error member | STM-19 |
| **CE-STM-8** | The two lengths of a slice assignment differ, and both are known at compile time | FUN-24 |