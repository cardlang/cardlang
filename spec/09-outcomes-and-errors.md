# 9. Outcomes and errors

CardLang Language Specification, Draft 0.2. Chapter status: **draft complete** (SP8).

This chapter covers:

- *outcomes*, the transient success-or-error results of calls;
- how outcomes are produced and consumed;
- `attempt`;
- outcome `match`;
- error bindings;
- the application error set;
- the categories of error values.

Related topics are covered in other chapters:

| Topic | Chapter |
|---|---|
| Traps, the execution faults that are never outcomes | 13 |
| `abort Err(…)` and the transaction-boundary rules for `return`, `attempt` and `require` | 11 |
| How the host sees each outcome category | 12, and Annex B |

## 9.1 Outcomes

**OUT-1 [Agreed]** Every call completes with exactly one *outcome*:

| Outcome | Meaning |
|---|---|
| `Ok(v)` | Success with a payload `v` |
| `Ok()` | Success without a payload |
| `Err(e)` | A recoverable error `e` |

This applies to every ordinary function and platform API call, and to every call of an outcome-producing intrinsic (`checked_*` and `checked_convert`). The host entry point also completes with an outcome (chapter 12). Recoverable failures are always reported as `Err`. Execution faults are traps (chapter 13), and a trap is never an outcome. CardLang has no exceptions.
*Sources: D-010, D-011, D-012, D-418 (OI-18); DN §6.1.*

**OUT-2 [Agreed]** An outcome is not a value. The type `Outcome(T)` exists only in this specification: no CardLang type can be written for an outcome. An outcome cannot be:

- stored in a variable, constant, field or array element;
- passed as an argument;
- nested in another outcome;
- used as an operand.

Any of those is CE-EXP-14 (EXP-48). Every outcome must be consumed where it is produced (§9.3).
*Sources: D-016, D-418 (OI-18); DN §6.3.*

## 9.2 Producing outcomes

**OUT-3 [Agreed]** The successful return forms depend on whether the function has a payload:

- In a function whose successful payload type is `T`, `return Ok(e);` returns success, and `e` checks against `T` (EXP-10).
- In a function with no payload (no `->`), the only successful return is `return Ok();`.

`return Ok();` in a function with a payload, or `return Ok(e);` in a function without one, is **CE-OUT-2**. There is no implicit success (STM-21).
*Sources: D-025, D-107; DN §3.6, §3.7, §6.1.*

**OUT-4 [Agreed]** `return Err(x);` returns a recoverable error. `x` must be either:

- a qualified member of the application's error set, such as `WalletError.InsufficientFunds`; or
- an error binding introduced by an `Err(name)` pattern in an enclosing arm (OUT-14).

Any other operand is **CE-OUT-3**, for example an integer, an enum variant, a call or a constant. That includes a member of `CardError`: application code never originates a platform error (OUT-19). The error is returned whatever the function's payload type.
*Sources: D-028, D-107, D-437 (OI-37); DN §6.3.*

**OUT-5 [Agreed]** `return c;`, where `c` is a call, forwards the call's complete outcome to the caller. The call must produce `Outcome(U)` where `U` is identical to the enclosing function's payload type `T`. If neither has a payload, they also match. Otherwise it is **CE-OUT-2**. This applies to ordinary calls, platform API calls and outcome-producing intrinsics, such as `return checked_add(a, b);` in a function returning `u32`.
*Sources: D-015, D-413 (OI-13); DN §3.7, §6.3.*

**OUT-6 [Agreed]** `Ok` and `Err` are keywords. They are not constructors of storable values. They appear only:

- in `return Ok(…)` and `return Err(…)`;
- in `abort Err(…)` (chapter 11);
- in patterns.

Anywhere else they do not derive (**CE-SYN-1**).
*Sources: D-363; DN §6.3.*

### Examples

*Valid:* forwarding a call's outcome, and forwarding a checked intrinsic's outcome (DN §6.3). (conformance: `valid/out-005-forwarding.card`)

```text
errors WalletError {
    InsufficientFunds = 1;
}

function subtract(current_balance: u32, amount: u32) -> u32 {
    require amount <= current_balance else WalletError.InsufficientFunds;
    return Ok(current_balance - amount);
}

function remaining(current_balance: u32, amount: u32) -> u32 {
    return subtract(current_balance, amount);
}

function safe_sum(a: u32, b: u32) -> u32 {
    return checked_add(a, b);
}
```

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `return Ok(1);` in a function with no payload | CE-OUT-2 | `invalid/out-103-ok-value-in-no-payload.card` |
| `return Ok();` in a function returning `u32` | CE-OUT-2 | `invalid/out-104-ok-empty-in-payload.card` |
| `return read_value();` returning `u32` from a function returning `u16` | CE-OUT-2 | `invalid/out-105-forward-mismatch.card` |
| `return Err(5);` | CE-OUT-3 | `invalid/out-106-err-integer.card` |
| `return Err(Mode.Off);` with `Mode` an enum | CE-OUT-3 | `invalid/out-107-err-enum-variant.card` |
| `return Err(CardError.NotFound);` | CE-OUT-3 | `invalid/out-108-originate-card-error.card` |

*Invalid:* `Ok` is not a constructor of a storable value (OUT-6). **CE-SYN-1**. (conformance: `invalid/out-131-ok-as-value.card`)

```text
function check() {
    var result: u32 = Ok(1);
    return Ok();
}
```

## 9.3 Consuming outcomes

**OUT-7 [Agreed]** Every outcome must be consumed by exactly one of:

- an outcome `match` (§9.5), which handles success and failure locally;
- `attempt` (§9.4), which extracts the success value or propagates the error;
- a forwarding `return` (OUT-5), which passes the complete outcome to the caller.

A call used as a statement on its own discards its outcome. That is **CE-OUT-1**, whether the call is to a function, a platform API or an outcome-producing intrinsic.
*Sources: D-015; DN §3.5, §6.3.*

### Examples

*Invalid:* a call used as a statement (DN §6.3). **CE-OUT-1**. (conformance: `invalid/out-101-bare-call-statement.card`)

*Invalid:* a checked intrinsic used as a statement. **CE-OUT-1**. (conformance: `invalid/out-102-bare-checked-statement.card`)

*Invalid:* an outcome used as an initializer (DN §6.3). **CE-EXP-14**. (conformance: `invalid/out-124-outcome-in-initializer.card`)

## 9.4 `attempt`

**OUT-8 [Agreed]** The operand of `attempt` must be a call that produces an outcome. That means a call to an ordinary function, a platform API, a `checked_*` intrinsic or `checked_convert`. Any other operand is **CE-OUT-4**, for example a variable, a direct-value intrinsic or a literal. EXP-51 governs where `attempt` may appear.
*Sources: D-014, D-408 (OI-8); DN §6.3.*

**OUT-9 [Agreed]** `attempt` has two forms:

- **Expression form.** `attempt c`, applied to a call producing `Outcome(T)`, is an expression that synthesizes exactly `T`. There is no conversion and no default value.
- **Statement form.** `attempt c;` is allowed only when `c` produces `Outcome()`.

Using the statement form with a call that has a payload is **CE-OUT-4**: a payload cannot be discarded silently. Using a call without a payload as an expression is also **CE-OUT-4**: it produces no value. To ignore a payload deliberately, use `Ok(_)` in a `match`.
*Sources: D-017; DN §6.3.*

**OUT-10 [Agreed]** `attempt c` is evaluated as follows:

1. Evaluate the call `c`.
2. If its outcome is `Ok(v)`, the result of `attempt` is `v`, as an independent copy (FUN-17). For `Ok()`, the statement simply completes.
3. If its outcome is `Err(e)`, the enclosing function or command immediately returns `Err(e)`. The category and code are unchanged. This happens whatever the enclosing function's payload type, and the rest of the enclosing expression and statement is not evaluated.

`attempt` never catches traps. Inside a transaction opened in the same function, step 3 aborts the transaction instead of returning directly (TXN-18).
*Sources: D-014, D-017, D-364; DN §6.3.*

### Examples

*Valid:* `attempt` as an initializer in a function with a different payload type, and the statement form for a call without a payload (DN §6.3). (conformance: `valid/out-004-attempt-forms.card`)

```text
function read_value() -> u32 {
    return Ok(7);
}

function authenticate() {
    return Ok();
}

function is_nonzero() -> bool {
    attempt authenticate();
    var value: u32 = attempt read_value();
    return Ok(value != 0);
}
```

*Valid:* `attempt` on `checked_convert` in an application with no error set. (conformance: `valid/out-008-no-error-set.card`)

```text
function narrow(incoming: u16) -> u8 {
    var value: u8 = attempt checked_convert<u8>(incoming);
    return Ok(value);
}
```

*Invalid:* each of these is in its own test, and each is **CE-OUT-4**.

| Code | Conformance |
|---|---|
| `var copy: u32 = attempt value;` with `value` a variable | `invalid/out-110-attempt-non-call.card` |
| `attempt read_value();` where `read_value` returns `u32` | `invalid/out-111-attempt-statement-with-payload.card` |
| `var result: u32 = attempt authenticate();` where `authenticate` has no payload | `invalid/out-112-attempt-expression-no-payload.card` |

## 9.5 Outcome `match` and error bindings

```
MatchStatement ::= 'match' ConditionExpression '{' MatchArm* '}'      /* §A.2.5 */
Pattern        ::= 'Ok' '(' ( Identifier | '_' )? ')'
                 | 'Err' '(' ( Identifier | '_' | Identifier '.' Identifier | Identifier '(' ( Identifier | '_' ) ')' ) ')'
                 | …
```

**OUT-11 [Agreed]** When the scrutinee of a `match` produces `Outcome(T)`, each arm's pattern must be one of these:

| Pattern | Meaning |
|---|---|
| `Ok(name)` | Success, binding the payload. Requires a payload |
| `Ok(_)` | Success, ignoring the payload. Requires a payload |
| `Ok()` | Success without a payload. Requires no payload |
| `Err(Set.Member)` | One specific error. `Set.Member` must name a member of the application's error set or of `CardError` (NAM-16) |
| `Err(name)` | Any error, bound to `name` (OUT-14) |
| `Err(_)` | Any error, ignored |

A pattern that does not fit the scrutinee is **CE-OUT-5**: `Ok()` against a payload, `Ok(name)` against no payload, or an enum variant pattern. There are no guards, alternatives, numeric or range patterns, nested patterns or destructuring. A nested form such as `Ok(State.Idle)` does not derive (**CE-SYN-1**). To inspect an enum payload, bind it with `Ok(value)` and `match` on `value` inside the arm.
*Sources: D-013, D-361; DN §3.6, §6.1, §6.3.*

**OUT-12 [Agreed]** An outcome `match` has exactly:

1. one success arm;
2. zero or more specific error arms `Err(Set.Member)`, each naming a different member;
3. one final catch-all arm, `Err(name)` or `Err(_)`.

The catch-all is required even when every known error is listed, because the error representation is shared by all functions. Each of the following is **CE-OUT-5**:

- a missing success arm;
- a second success arm;
- a missing catch-all;
- a repeated specific error;
- any arm after the catch-all.

The success arm may appear before or after the specific error arms, but always before the catch-all.
*Sources: D-108, D-360; DN §3.6, §6.3.*

**OUT-13 [Agreed]** The scrutinee is evaluated exactly once, and exactly one arm runs:

- On `Ok`, the success arm runs.
- On `Err(e)`, the specific arm naming `e` runs if there is one. Otherwise the catch-all runs.

A payload binding `Ok(name)` is a read-only, independent copy of the payload, local to its arm (NAM-19). It is not a reference, and assigning to it is CE-STM-2. A `match` catches no traps.
*Sources: D-108, D-362; DN §3.6.*

**OUT-14 [Agreed]** An `Err(name)` pattern introduces an *error binding*. It is read-only, local to its arm, needs no type annotation, and need not be used. Its only allowed uses are:

- `return Err(name);`
- `abort Err(name);`, inside a transaction (chapter 11).

Any other use is **CE-OUT-6**, for example copying it into a variable, comparing it, passing it as an argument, returning it as an `Ok` payload, or selecting a field of it. Using it as a `require` operand is CE-STM-7 (STM-19). The arm may run other statements before propagating, or may not propagate at all.
*Sources: D-028; DN §6.3.*

### Examples

*Valid:* handling success and failure locally (DN §6.1). (conformance: `valid/out-001-match-ok-err.card`)

```text
errors WalletError {
    InsufficientFunds = 1;
}

session balance: u32;

function subtract(current_balance: u32, amount: u32) -> u32 {
    require amount <= current_balance else WalletError.InsufficientFunds;
    return Ok(current_balance - amount);
}

function withdraw(amount: u32) {
    match subtract(balance, amount) {
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

*Valid:* `Ok()` for a call without a payload, and a specific error arm before the catch-all (DN §3.7, §6.3). (conformance: `valid/out-002-no-payload-match.card`)

```text
errors WalletError {
    InsufficientFunds = 1;
}

struct Account {
    balance: u32;
}

session account: Account;

function debit(target: inout Account, amount: u32) {
    require amount <= target.balance else WalletError.InsufficientFunds;
    target.balance = target.balance - amount;
    return Ok();
}

function pay(amount: u32) {
    match debit(inout account, amount) {
        Ok() => {
        }
        Err(WalletError.InsufficientFunds) => {
            return Ok();
        }
        Err(error) => {
            return Err(error);
        }
    }
    return Ok();
}
```

*Valid:* `Ok(_)` deliberately ignoring a payload (DN §6.3). (conformance: `valid/out-003-ignore-payload.card`)

*Valid:* an error binding that is never used. (conformance: `valid/out-006-unused-error-binding.card`)

*Valid:* matching a specific `CardError` member, and propagating any other platform error (D-437). (conformance: `valid/out-009-match-card-error.card`)

```text
session total: u32;

function add_to_total(amount: u32) -> bool {
    match checked_add(total, amount) {
        Ok(value) => {
            total = value;
            return Ok(true);
        }
        Err(CardError.Overflow) => {
            return Ok(false);
        }
        Err(error) => {
            return Err(error);
        }
    }
}
```

*Invalid:* each of these is in its own test.

| Fault | Class | Conformance |
|---|---|---|
| No catch-all arm (DN §6.3) | CE-OUT-5 | `invalid/out-113-missing-catch-all.card` |
| No success arm | CE-OUT-5 | `invalid/out-114-missing-success-arm.card` |
| A specific arm after the catch-all (DN §3.6) | CE-OUT-5 | `invalid/out-115-specific-after-catch-all.card` |
| A specific error listed twice | CE-OUT-5 | `invalid/out-116-duplicate-specific-arm.card` |
| `Ok()` against an outcome with a payload (DN §3.6) | CE-OUT-5 | `invalid/out-117-ok-empty-against-payload.card` |
| Two success arms | CE-OUT-5 | `invalid/out-119-two-success-arms.card` |
| `Ok(State.Idle)`, a nested pattern (DN §3.6) | CE-SYN-1 | `invalid/out-118-nested-pattern.card` |
| `error == error` with an error binding | CE-OUT-6 | `invalid/out-120-compare-error-binding.card` |
| `var saved: u32 = error;` | CE-OUT-6 | `invalid/out-121-store-error-binding.card` |
| `attempt log_error(error);` | CE-OUT-6 | `invalid/out-122-pass-error-binding.card` |
| `require ready else error;` | CE-STM-7 | `invalid/out-123-error-binding-require.card` |

**OUT-21 [Agreed]** The pattern `Err(Set(name))`, where `Set` is the application's error set, matches every `Err` whose error is a member of `Set`. It binds `name` as a read-only local of type `u16` that holds the member's code (OUT-16). Platform errors never match it.

- **Arm order.** It counts as a specific arm for every member of `Set`. An arm for a member of `Set` after it, or a second `Err(Set(…))` arm, is **CE-OUT-5**.
- **No error values.** The binding is an integer, not an error value. OUT-14 is unchanged: an `Err(name)` binding still cannot be inspected.
- **`CardError`.** `Err(CardError(name))` is **CE-OUT-5**.
*Sources: D-454 (OI-54).*

**OUT-22 [Agreed]** `attempt c else M`, where `M` is a qualified member of the application's error set, is `attempt c` (OUT-9, OUT-10) with one difference: when `c` produces `Err` of any kind, the enclosing function or command returns `Err(M)` instead of the original error. Lexically inside a transaction, it aborts with `Err(M)` instead (TXN-18). It has the expression and the statement forms of `attempt`.

- **The operand.** An operand `M` that is not such a member, including a `CardError` member, is **CE-OUT-3**.
- **Traps** are never caught.
- **Parsing.** The `else` belongs to the nearest `attempt`. To use `attempt` inside the condition of a `require`, parenthesize it: `require (attempt ready()) else E.M;`.
*Sources: D-455 (OI-55).*

*Valid:* an `Err(Set(code))` arm that translates application errors, and `attempt … else` in both forms. (conformance: `valid/out-010-error-codes-and-mapping.card`)

*Invalid:* `Err(CardError(code))`. **CE-OUT-5**. (conformance: `invalid/out-132-card-error-set-pattern.card`)

*Invalid:* `attempt … else CardError.NotFound`. **CE-OUT-3**. (conformance: `invalid/out-133-attempt-else-card-error.card`)

## 9.6 The application error set

```
ErrorSetDeclaration ::= 'errors' Identifier '{' ErrorMember* '}'   /* §A.2.1 */
ErrorMember         ::= Identifier '=' Expression ';'
```

**OUT-15 [Agreed]** An `errors` declaration declares the application's error set. It is a top-level declaration (NAM-7), and its name is in the application scope (NAM-11). An application declares at most one error set, and may declare none. A second `errors` declaration is **CE-OUT-7**. An error set must declare at least one member. An empty set is **CE-OUT-7**. Enums never act as error sets (TYP-12).
*Sources: D-018, D-413 (OI-13), D-436 (OI-36); DN §6.3.*

**OUT-16 [Agreed]** Each member is written `Name = code;`. The rules for the code are:

- It must be an integer literal, typed as `u16` (EXP-7). A literal above 65 535 is CE-EXP-2.
- It must not be zero, because zero is reserved and never identifies an error.
- No two members of the set may have the same code.

A non-literal code, a zero code and a duplicate code are each **CE-OUT-7**. Member names are unique within the set (NAM-15) and are always used qualified (NAM-16). Members carry only their identity: no strings or payloads.
*Sources: D-018, D-365, D-428 (OI-28); DN §6.3.*

**OUT-17 [Agreed]** Once an application has published an error code, later versions of that application must not change the code's meaning. If an error is removed, its code must not be reused for a different error. This is an obligation on how an application evolves, and no compiler can check it.
*Sources: D-366, D-209; DN §6.3; PN §5.*

### Examples

*Valid:* an error set with explicit literal codes, and a member returned (DN §6.3). (conformance: `valid/out-007-error-set.card`)

```text
errors WalletError {
    InsufficientFunds = 1;
    AccountBlocked = 2;
    InvalidAmount = 3;
    Unauthorized = 4;
}

function refuse() {
    return Err(WalletError.Unauthorized);
}
```

*Invalid:* each of these is in its own test.

| Fault | Class | Conformance |
|---|---|---|
| Two `errors` declarations | CE-OUT-7 | `invalid/out-125-two-error-sets.card` |
| `Missing = 0;` | CE-OUT-7 | `invalid/out-126-zero-code.card` |
| Two members with code 1 | CE-OUT-7 | `invalid/out-127-duplicate-code.card` |
| `Derived = BASE_CODE + 1;` (D-428) | CE-OUT-7 | `invalid/out-128-computed-code.card` |
| `errors Empty { }` | CE-OUT-7 | `invalid/out-129-empty-error-set.card` |
| `Huge = 70000;` | CE-EXP-2 | `invalid/out-130-code-out-of-range.card` |

## 9.7 Error values and categories

**OUT-18 [Agreed]** Every error value has two parts:

- a *category*, either *application* or *platform*;
- a nonzero `u16` code.

An error carries nothing else: no message, no payload and no field naming its source application. The two categories are distinct even when their codes are equal, so an application error and a platform error are never confused. Propagation never changes an error, whether through `attempt`, a forwarding `return`, `return Err(binding)` or `abort Err(binding)`. Applications are isolated, so no error ever crosses from one application to another.
*Sources: D-019, D-365, D-367; DN §6.3.*

**OUT-19 [Agreed]** Platform errors are the members of the reserved error set `CardError`. Applications cannot declare it (NAM-14). Its member names and codes are platform-defined (Annex B). The names used in this specification are placeholders (D-415). Application code may name a `CardError` member only in an `Err(CardError.Member)` pattern. It may propagate a platform error that it received through an error binding. It never originates one:

- `return Err(CardError.…)` is **CE-OUT-3** (OUT-4).
- `abort Err(CardError.…)` is **CE-OUT-3** (chapter 11).
- `require … else CardError.…` is **CE-OUT-3** (STM-19).

*Sources: D-367, D-415 (OI-15), D-437 (OI-37); DN §6.3.*

### Examples

*Invalid:* a `require` naming a platform error. **CE-OUT-3**. (conformance: `invalid/out-109-require-card-error.card`)

## 9.8 `Err` is not rollback

**OUT-20 [Agreed]** Returning or propagating `Err` undoes nothing. Earlier writes stay, whether they are to persistent state, to session state, or through references (FUN-23). When a callee returns `Err` inside a caller's transaction, the transaction stays active. The caller may handle the error and continue to commit. Only `abort Err(…)` rolls back a transaction's persistent writes (chapter 11). To avoid partial updates, validate before changing data.
*Sources: D-368, D-356; DN §6.3, §7.2.*

## 9.9 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-OUT-1** | An outcome is discarded by a call used as a statement | OUT-7 |
| **CE-OUT-2** | A `return` form does not match the function's payload, or a forwarded outcome has a different payload type | OUT-3, OUT-5 |
| **CE-OUT-3** | An `Err` or `require` operand that is not an application error member or error binding, including any `CardError` member | STM-19, OUT-4, OUT-19, OUT-22, TXN-7 |
| **CE-OUT-4** | An invalid `attempt` or `ignore`: its operand is not an outcome-producing call, or the `attempt` form does not match the payload | STM-24, OUT-8, OUT-9 |
| **CE-OUT-5** | An invalid outcome `match`: incompatible pattern, missing or repeated success arm, missing catch-all, repeated specific error, or an arm after the catch-all | OUT-11, OUT-12, OUT-21 |
| **CE-OUT-6** | An error binding used other than in `return Err(…)` or `abort Err(…)` | OUT-14 |
| **CE-OUT-7** | An invalid error set: more than one set, no members, or a non-literal, zero or duplicate code | OUT-15, OUT-16 |