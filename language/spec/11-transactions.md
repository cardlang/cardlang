# 11. Transactions

CardLang Language Specification, Draft 0.2. Chapter status: **draft complete**.

A *transaction* groups persistent writes so that they commit together or not at all. This chapter covers:

- the `transaction` block, and when it commits;
- which state participates;
- the rule that ordinary control transfers may not leave a transaction;
- the `abort Err` statement;
- the ban on nested transactions;
- what traps, commit failures and recovery mean for transactions, as far as the language can see.

Without a transaction, each persistent assignment is atomic on its own (chapter 10). How transactions are stored, journaled and recovered is platform-defined (Annex B). The language fixes only the guarantees in this chapter.

## 11.1 Syntax

```
TransactionStatement ::= 'transaction' Block
AbortStatement       ::= 'abort' 'Err' '(' Expression ')' ';'
```

**TXN-1 [Agreed]** A `transaction` statement may appear in the body of any function, command or lifecycle handler. While its block executes, the transaction is *active*. Every persistent write performed while a transaction is active is *pending* in it. That covers:

- writes in the block itself;
- writes in any function the block calls, directly or indirectly;
- writes through `inout` references and views into persistent storage.

*Sources: D-132, D-352; DN §7.2, §7.3.*

## 11.2 Execution and commit

**TXN-2 [Agreed]** While a transaction is active, every read observes the pending writes that come before it in evaluation order. This holds whether the read is direct, through a reference or a view, or in a called function. Pending writes are not visible outside the active transaction (TXN-14).
*Sources: D-376; DN §7.2.*

**TXN-3 [Agreed]** When the block completes normally, the transaction *commits*: all of its pending persistent writes take effect together. Execution continues after the block only after the commit has succeeded. A transaction with no persistent writes is valid, and it commits trivially. The language defines no other commit protocol.
*Sources: D-375; DN §7.2.*

**TXN-4 [Agreed]** Only persistent state participates in a transaction. Rollback never restores:

- session state;
- local variables;
- the response buffer (chapter 12);
- any other volatile state.

A platform API's effects participate only if that API's contract says so. Otherwise its contract states its behaviour inside a transaction, or prohibits use there (TXN-17, Annex B).
*Sources: D-055, D-377, D-205; DN §7.2; PN §5.*

**TXN-5 [Agreed]** A command is never implicitly a transaction, and neither is a function. Persistent writes outside any transaction are each atomic on their own (STA-11), and they are not atomic together.
*Sources: D-383, D-372; DN §4, §7.1, §7.2.*

### Examples

*Valid:* two persistent writes that commit together (DN §7.2). (conformance: `valid/txn-001-basic.card`)

```text
persistent balance: u32;
persistent sequence: u32;

function pay(amount: u32) {
    transaction {
        balance = balance - amount;
        sequence = sequence + 1;
    }
    return Ok();
}
```

*Valid:* a read that sees an earlier pending write (DN §7.2). (conformance: `valid/txn-002-read-your-writes.card`)

```text
persistent counter: u32;
persistent last_counter: u32;

function bump() {
    transaction {
        counter = counter + 1;
        last_counter = counter;
    }
    return Ok();
}
```

*Valid:* an empty transaction. (conformance: `valid/txn-003-empty.card`)

*Valid:* a callee's persistent write takes part in the caller's transaction, and the caller reads it. (conformance: `valid/txn-004-callee-writes.card`)

```text
persistent balance: u32;
persistent snapshot: u32;

function credit(amount: u32) {
    balance = balance + amount;
    return Ok();
}

function credit_and_record(amount: u32) {
    transaction {
        match credit(amount) {
            Ok() => {
                snapshot = balance;
            }
            Err(_) => {
            }
        }
    }
    return Ok();
}
```

## 11.3 Leaving a transaction

**TXN-6 [Agreed]** A *boundary-crossing transfer* is a control transfer that would leave the block of an active transaction other than by reaching its closing brace. Each of the following, written lexically inside a transaction's block in the same function or command, is a boundary-crossing transfer and is **CE-TXN-1**:

- `return …;` in any form, including a forwarding `return`;
- `break;` or `continue;` whose target loop encloses the transaction;

Transfers that stay inside the block are valid. Examples are a `break` or `continue` targeting a loop that is itself inside the transaction, and a `return` inside a called function: that `return` leaves only the callee. The caller then handles the callee's outcome without leaving its transaction, for example with `match` or `abort`. `attempt` and `require` are not boundary-crossing transfers: inside a transaction, their error path aborts the transaction (TXN-18). The only ways to leave a transaction are to reach its closing brace, `abort Err(…)`, the error path of `attempt` or `require`, or a trap.
*Sources: D-109, D-381; DN §3.6, §6.3, §7.2.*

**TXN-7 [Agreed]** `abort Err(x);` is valid only lexically inside the block of a transaction in the same function or command. Anywhere else it is **CE-TXN-2**. That includes a function called from within a transaction, which returns `Err` instead and lets the transaction's owner decide. The operand `x` must be either:

- a qualified member of the application's error set; or
- an error binding in scope (OUT-14).

Any other operand is **CE-OUT-3**, including a `CardError` member (OUT-19). `abort` is a statement and needs its semicolon. The forms `abort;`, `abort x;` and `abort Ok(…);` do not derive (**CE-SYN-1**).
*Sources: D-110, D-111, D-380, D-437 (OI-37); DN §7.2.*

**TXN-8 [Agreed]** `abort Err(x);` is executed as follows:

1. Stop executing the transaction's block. No later statement runs, either in the block or after it.
2. Roll back every pending persistent write of the transaction, including writes through references and in called functions.
3. Return `Err(x)` from the enclosing function or command, with the category and code unchanged, whatever the payload type.

Session changes made during the transaction remain. Local variables end as for any return. Persistent changes committed earlier stay committed. `abort` is not a trap: a caller receives an ordinary `Err` and may handle it. There are no savepoints, and there is no form that rolls back and then continues.
*Sources: D-110, D-379; DN §6.4, §7.2.*

**TXN-18 [Agreed]** Lexically inside the block of a transaction in the same function or command, the error path of `attempt` and of `require` aborts the transaction:

- `attempt c`, in either form, whose call produces `Err(e)`, behaves as `abort Err(e);`, and `attempt c else M` behaves as `abort Err(M);` (OUT-22);
- `require c else M;` whose condition is `false` behaves as `abort Err(M);`.

Each is executed by the steps of TXN-8: the block stops, the pending persistent writes roll back, and the error is returned unchanged. Unlike an `abort` operand, `e` may be a platform error, because `attempt` propagates an error and does not originate one (OUT-18, OUT-19). Inside a function called from the transaction, `attempt` and `require` return from that function as usual, and the caller's transaction stays active (TXN-9).
*Sources: D-445 (OI-45), D-109, D-110; DN §3.6, §6.3, §7.2.*

**TXN-9 [Agreed]** A callee that returns `Err` does not end or abort the caller's transaction. The callee's pending writes remain pending. The transaction's owner either handles the error and continues, so the writes commit at the closing brace, or uses `abort` to roll them back.
*Sources: D-378, D-368; DN §6.3, §7.2.*

### Examples

*Valid:* `abort` with an error binding (DN §7.2). (conformance: `valid/txn-006-abort-binding.card`)

```text
persistent balance: u32;
persistent last_payment: u32;

function record_payment(amount: u32) {
    last_payment = amount;
    return Ok();
}

function pay(amount: u32) {
    transaction {
        balance = balance - amount;
        match record_payment(amount) {
            Ok() => {
            }
            Err(error) => {
                abort Err(error);
            }
        }
    }
    return Ok();
}
```

*Valid:* an error handled locally, so the transaction stays active and commits (DN §7.2). (conformance: `valid/txn-005-err-handled-locally.card`)

*Valid:* `abort` with an application error member. (conformance: `valid/txn-007-abort-member.card`)

```text
errors WalletError {
    InsufficientFunds = 1;
}

persistent balance: u32;

function debit(amount: u32) {
    transaction {
        if amount > balance {
            abort Err(WalletError.InsufficientFunds);
        }
        balance = balance - amount;
    }
    return Ok();
}
```

*Valid:* `break` and `continue` targeting a loop inside the transaction. (conformance: `valid/txn-008-loop-inside.card`)

*Valid:* checking with `require` before the transaction, and returning after it (DN §10). (conformance: `valid/txn-009-validate-then-transact.card`)

```text
errors WalletError {
    InsufficientFunds = 1;
    Unauthorized = 2;
}

persistent balance: u32;
session authenticated: bool;

function debit(amount: u32) -> u32 {
    require authenticated else WalletError.Unauthorized;
    require amount <= balance else WalletError.InsufficientFunds;
    transaction {
        balance = balance - amount;
    }
    return Ok(balance);
}
```

*Valid:* a helper that uses `attempt`, called from a transaction whose owner handles its outcome. (conformance: `valid/txn-011-helper-with-attempt.card`)

*Valid:* `attempt` inside a transaction; its error path aborts the transaction (TXN-18). (conformance: `valid/txn-012-attempt-inside.card`)

*Valid:* `require` inside a transaction; a false condition aborts the transaction (TXN-18, DN §3.6). (conformance: `valid/txn-013-require-inside.card`)

*Invalid:* each of these is in its own test.

| Code inside a transaction block | Class | Conformance |
|---|---|---|
| `return Ok();` | CE-TXN-1 | `invalid/txn-101-return-inside.card` |
| `return helper();` | CE-TXN-1 | `invalid/txn-102-forwarding-return-inside.card` |
| `break;` targeting a loop around the transaction | CE-TXN-1 | `invalid/txn-105-break-to-outer-loop.card` |
| `continue;` targeting a loop around the transaction | CE-TXN-1 | `invalid/txn-106-continue-to-outer-loop.card` |
| `return Err(error);` in a match arm | CE-TXN-1 | `invalid/txn-107-return-in-match-arm.card` |
| `abort Err(CardError.NotFound);` | CE-OUT-3 | `invalid/txn-110-abort-card-error.card` |
| `abort Err(5);` | CE-OUT-3 | `invalid/txn-111-abort-integer.card` |
| `abort;` | CE-SYN-1 | `invalid/txn-112-bare-abort.card` |
| `abort Ok();` | CE-SYN-1 | `invalid/txn-113-abort-ok.card` |

| Code outside a transaction block | Class | Conformance |
|---|---|---|
| `abort Err(WalletError.InsufficientFunds);` in a function with no transaction | CE-TXN-2 | `invalid/txn-108-abort-outside.card` |
| `abort` in a helper called from a transaction (DN §7.2) | CE-TXN-2 | `invalid/txn-109-abort-in-helper.card` |

## 11.4 No nested transactions

**TXN-10 [Agreed]** At most one transaction is ever active. It is **CE-TXN-3** if the block of a transaction contains another `transaction` statement, either:

- lexically, at any depth; or
- in the body of any function reachable from a call in the block, along the static call graph (FUN-5), at any depth.

The rule is structural and conservative. A call counts even if it is on a path that never runs, such as inside `if false`. Because call targets are static and the call graph is acyclic, every conforming implementation accepts and rejects exactly the same programs. An implementation may keep a runtime check for nesting as a safety measure (`TRAP-NESTED-TXN`, chapter 13), but no accepted program can reach it.
*Sources: D-131, D-403 (OI-3); DN §7.3.*

### Examples

*Invalid:* a transaction reached through a call from inside another (DN §7.3). **CE-TXN-3**. (conformance: `invalid/txn-115-nesting-through-call.card`)

```text
persistent value: u32;

function update() {
    transaction {
        value = 1;
    }
    return Ok();
}

function outer() {
    transaction {
        match update() {
            Ok() => {
            }
            Err(_) => {
            }
        }
    }
    return Ok();
}
```

*Invalid:* each of these is in its own test, and each is **CE-TXN-3**.

| Fault | Conformance |
|---|---|
| A `transaction` inside a `transaction` block | `invalid/txn-114-lexical-nesting.card` |
| Nesting through a chain of two calls | `invalid/txn-116-nesting-two-step.card` |
| A nesting call inside `if false` | `invalid/txn-117-nesting-untaken-path.card` |

## 11.5 Failures, recovery and isolation

**TXN-11 [Agreed]** If a trap occurs while a transaction is active, all of the transaction's pending persistent writes are rolled back, and the current command terminates (chapter 13). Session changes remain. Persistent changes committed earlier stay committed.
*Sources: D-382, D-055; DN §6.4, §7.2.*

**TXN-12 [Agreed]** A failed commit never lets execution continue after the block as though it had succeeded. If the platform can contain the failure, the result is `trap(COMMIT)`. A failure that threatens integrity requires a security reset (chapter 13). Annex B defines how failures are classified.
*Sources: D-207; DN §7.2; PN §5.*

**TXN-13 [Agreed]** After an interruption, such as power loss during a transaction or its commit, and the platform's recovery, persistent state reflects either the complete transaction or none of it. It never reflects part of it. If recovery cannot establish integrity, the platform fails closed and does not resume with partial state (Annex B). A trap that happens after a commit never undoes that commit.
*Sources: D-207; DN §7.2; PN §5.*

**TXN-14 [Agreed]** No other execution context can observe the pending state of an active transaction. That includes other commands, lifecycle handlers and callbacks. Commands never interleave (chapter 12). The mechanism the platform uses to provide this isolation is platform-defined (Annex B).
*Sources: D-208, D-049; DN §4, §7.2; PN §5.*

## 11.6 Completion and limits

**TXN-15 [Agreed]** For completion analysis, a `transaction` statement may complete normally exactly when its block may (STM-20). `abort` never completes normally. A function whose transaction ends with `abort` on every path needs no `return` after it.
*Sources: D-030; DN §3.7.*

**TXN-16 [Agreed]** A target profile may limit how many pending writes a transaction can hold. That number generally cannot be known at compile time. If a running transaction would exceed the limit, the result is `trap(TXN-CAPACITY)`, and its pending writes roll back (TXN-11). The limit values are platform-defined (Annex B).
*Sources: D-439 (OI-39), D-206; DN §7.4.*

**TXN-17 [Agreed]** The platform API catalog may mark an API as not permitted inside a transaction (Annex B). A call to such an API is **CE-TXN-4** if it is either:

- lexically inside a transaction block; or
- in a function reachable from a call in such a block, along the static call graph.

The same structural rule as TXN-10 applies.
*Sources: D-440 (OI-40), D-205; DN §7.2, §7.4; PN §5.*

### Examples

*Valid:* a transaction whose block ends with `abort` on every path, so no `return` follows it. (conformance: `valid/txn-010-ends-with-abort.card`)

```text
errors WalletError {
    AccountBlocked = 1;
}

persistent blocked_attempts: u32;

function refuse() {
    transaction {
        blocked_attempts = blocked_attempts + 1;
        abort Err(WalletError.AccountBlocked);
    }
}
```

The CE-TXN-4 test uses the test-only platform API catalog (PLT-26).

## 11.7 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-TXN-1** | A control transfer inside a transaction would leave it other than at its closing brace | TXN-6 |
| **CE-TXN-2** | `abort` is not lexically inside a transaction in the same function or command | TXN-7 |
| **CE-TXN-3** | A transaction contains another transaction, lexically or through the call graph | TXN-10 |
| **CE-TXN-4** | A call to a platform API not permitted inside transactions, lexically inside one or reachable from one | TXN-17 |

The trap kinds `COMMIT`, `TXN-CAPACITY` and `NESTED-TXN` used in this chapter are placeholders (D-415, D-439). They are cataloged in chapter 13.
