# SP10 — Transactions: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 11 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/11-transactions.md` | The `transaction` block; pending writes and read-your-writes; commit at the closing brace; what participates; the boundary rule for `return`, `break`, `continue`, `attempt` and `require`; `abort Err`; no nesting (the structural rule, D-403); traps, commit failure and recovery as seen by the language; isolation; completion; limits |
| `spec/annex-A-grammar.md` §A.2.9 | `TransactionStatement` and `AbortStatement` |
| `conformance/valid/txn-*`, `conformance/invalid/txn-*` | Compile-time tests. Runtime behaviour tests are listed for SP12 |
| `tools/checkers/txncheck.py`, `tools/generators/sp10_tests.py` | A checker that extends `stacheck`, and the test generator. Both are added to `run_checks.py` |
| Register, Annex C, Annex D, 00-index | Body decisions D-375…, new issues, coverage and the CE-TXN index |

**Out of scope:**

| Topic | Where |
|---|---|
| Journaling, commit records, storage geometry and how failures are classified | Annex B |
| Transaction capacities, and which services may be used inside a transaction | Annex B (but see OI-39 and OI-40) |
| Response transmission relative to commit | Chapter 12 |
| The trap catalog | Chapter 13 |

## 2. Sources

- **Design notes:** §3.6 (the transaction boundary rule), §6.4 (the `abort` and trap rows), §7.1, §7.2, §7.3, §7.4.
- **Platform notes:** §5.

| Decision | Content |
|---|---|
| D-055 | A rollback affects persistent state only |
| D-109 | No `return`, `break` or `continue` across a transaction boundary |
| D-110, D-111 | `abort Err`, and where it may appear |
| D-131 + D-403 | Nested transactions are rejected by a static structural rule |
| D-132 | Persistent writes made by callees take part in the caller's transaction |
| D-207 | Commit failure is never resumed |
| D-208 | No partial state is observable (the platform side goes to SP13) |

### 2.1 Body-only decisions to register (D-375…)

| ID | Decision | Source |
|---|---|---|
| D-375 | Reaching the closing brace commits. Execution continues after the block only after a successful commit. An empty transaction is valid | DN §7.2 |
| D-376 | Within a transaction, reads see earlier writes, including through references and called functions | DN §7.2 |
| D-377 | Only persistent state participates. Session state and locals are not restored on rollback. Resource-API effects participate only where their API says so | DN §7.2; PN §5 |
| D-378 | `Err` returned by a callee is not an abort request. Pending changes remain, and they commit if execution reaches the closing brace | DN §7.2 |
| D-379 | `abort` stops the body, rolls back the pending persistent writes, and returns the error unchanged from the enclosing function or command. Session changes and earlier commits remain. The caller receives `Err` normally. There are no savepoints | DN §7.2 |
| D-380 | The operand of `abort` is a named error member or an in-scope error binding. `abort` is a statement. Bare `abort;`, `abort error;` and `abort Ok(…)` are invalid | DN §7.2 |
| D-381 | A `break` or `continue` that targets a loop entirely inside the transaction is valid. Returning from a called function does not exit the caller's transaction | DN §3.6 |
| D-382 | A trap inside a transaction rolls back its pending persistent writes and aborts the command | DN §7.2, §6.4 |
| D-383 | A command is not implicitly a transaction | DN §4, §7.2 |

## 3. Planned rules (chapter 11)

**§11.1 Syntax**

```
TransactionStatement ::= 'transaction' Block
AbortStatement       ::= 'abort' 'Err' '(' Expression ')' ';'
```

**§11.2 Execution and commit**

- **TXN-1** A transaction statement may appear in any function, command or handler body (FUN-22).
  - While its body runs, the transaction is *active*.
  - Every persistent write performed while it is active is *pending*. That includes writes made in called functions and writes through references (D-132).
- **TXN-2** Reads see pending writes, whether they are made directly, through references or in helpers (D-376).
- **TXN-3** When the body completes normally, the transaction *commits*:
  - all pending writes become durable together;
  - execution continues after the block only after the commit has succeeded.

  An empty transaction is valid (D-375).
- **TXN-4** Participation:
  - only persistent writes participate (D-055, D-377);
  - session state, locals and the response buffer are not restored on rollback;
  - resource-API effects follow their API's contract (Annex B).
- **TXN-5** A command is not implicitly a transaction (D-383).

**§11.3 Leaving a transaction**

- **TXN-6** The *boundary rule*. A control transfer that would leave the active transaction's body without passing its closing brace is **CE-TXN-1**. This covers:
  - `return`, including a forwarding `return`;
  - `break` or `continue` whose target loop encloses the transaction;
  - the `Err` path of `attempt`;
  - `require`, by its expansion (STM-19).

  It is checked lexically, within the function that opened the transaction. Transfers that stay inside the transaction are valid. Called functions may return normally (D-109, D-381).
- **TXN-7** `abort Err(x);`
  - It is valid only lexically inside a transaction in the same function or command; otherwise **CE-TXN-2** (D-111).
  - `x` is an application error member or an in-scope error binding. A `CardError` member, or any other operand, is CE-OUT-3 (D-437, D-380).
- **TXN-8** Semantics of `abort`:
  1. stop the body;
  2. roll back every pending persistent write;
  3. return `Err(x)` unchanged from the enclosing function or command.

  Session changes remain. Locals are discarded as for any return. Earlier commits remain. A caller receives an ordinary `Err`. There are no savepoints, and there is no form that rolls back and continues (D-110, D-379).
- **TXN-9** A callee's `Err` does not end the transaction. The owner may handle the error and commit, or it may `abort` (D-378, OUT-20).

**§11.4 No nesting**

- **TXN-10** The structural rule (D-403). It is **CE-TXN-3** if the body of a transaction contains another transaction statement:
  - lexically; or
  - in any function reachable through the static call graph from a call in the body.

  The rule is conservative: paths that are never taken count. It is decidable because the call graph is static and acyclic (FUN-5). A runtime nesting check may remain as a VM safety net (`TRAP-NESTED-TXN`), which verified programs never reach (D-131, D-403).

**§11.5 Failure**

- **TXN-11** A trap while the transaction is active rolls back all its pending writes and terminates the command (chapter 13). Session changes remain (D-382, D-055).
- **TXN-12** Commit failure:
  - execution never continues after a failed commit;
  - a failure the platform contains is `trap(COMMIT)`;
  - an integrity failure leads to a security reset (chapter 13; Annex B classifies failures) (D-207).
- **TXN-13** After an interruption and recovery, persistent state reflects either the complete transaction or none of it. If recovery cannot establish integrity, the platform fails closed (Annex B). A later trap never undoes a committed transaction (D-207).
- **TXN-14** Isolation. No other execution context can observe partially updated transactional state (D-208; commands never interleave, chapter 12). The mechanism is platform-defined.

**§11.6 Completion and limits**

- **TXN-15** A transaction may complete normally exactly when its body may (STM-20). `abort` never completes normally.
- **TXN-16** Transaction capacity. Exceeding it at runtime [Open → OI-39]. The capacity limits themselves are platform-defined.
- **TXN-17** Services that are not allowed inside a transaction [Open → OI-40].

**Error classes**

| Class | Meaning |
|---|---|
| CE-TXN-1 | A control transfer would leave the active transaction |
| CE-TXN-2 | `abort` outside a lexical transaction |
| CE-TXN-3 | Nested transaction (the structural rule) |
| CE-TXN-4 | Reserved for OI-40 |

## 4. New open issues

| ID | Question | Options | Recommendation |
|---|---|---|---|
| **OI-39** Exceeding transaction capacity at runtime | DN §7.4 asks what limits apply to transaction size. Loops make the number of pending writes unknown at compile time, so a target may run out of transaction capacity while a transaction is executing. What happens then? | (a) A trap with a dedicated kind, `TRAP-TXN-CAPACITY`. The pending writes are rolled back, as for any trap. (b) Treat it as a commit failure (`TRAP-COMMIT`). (c) Reject at build or load time when a bound can be computed, otherwise trap | (a). A capacity trap is distinct from a commit failure, and the host can tell them apart. Build-time rejection (c) would make acceptance depend on how sophisticated the analysis is, the same problem as OI-3 |
| **OI-40** Platform services inside a transaction | DN §7.2 and PN §5 say each API must define its transaction behaviour or prohibit use during a transaction. How is a prohibited call detected? | (a) Statically, with the same structural call-graph rule as nesting: a call to an API marked "not in transactions", lexically inside a transaction or reachable from one, is **CE-TXN-4**. (b) At runtime: the API returns a defined recoverable error. (c) At runtime: a trap | (a). It is consistent with D-403 (deterministic and conservative) and catches the problem before deployment. The marking itself is part of each API's catalog entry (Annex B) |

**Decided 2026-11-17.** You accepted both recommendations. They are recorded as D-439 and D-440:

- **TXN-16 is [Agreed].** Exceeding transaction capacity at runtime is `trap(TXN-CAPACITY)`, and the pending writes roll back. The new trap kind is added to the trap list in D-415 and goes into the chapter 13 catalog.
- **TXN-17 is [Agreed], with class CE-TXN-4.** A call to a platform API marked "not in transactions" is a compile error when it is lexically inside a transaction or reachable from one. The marking is part of each API's catalog entry (Annex B). The test waits for the catalog format (SP13).

## 5. Conformance tests (about 26 compile-time tests)

**Valid**

- the basic transaction (DN §7.2);
- read-your-writes (DN §7.2 `last_counter`);
- an empty transaction;
- a callee writing persistent state inside a transaction;
- `Err` handled locally in a transaction (DN §7.2);
- `abort Err(error)` in a match arm (DN §7.2);
- `abort` with an application member;
- `break` and `continue` targeting a loop inside the transaction;
- validating before the transaction, then `return` after it (DN §10 `debit`);
- a transaction body that ends with `abort` on every path (completion);
- a helper that contains `attempt` or `return`, called from a transaction.

**Invalid**

| Test | Expected class |
|---|---|
| `return` inside a transaction | CE-TXN-1 |
| A forwarding `return` inside | CE-TXN-1 |
| `attempt` with an `Err` path inside | CE-TXN-1 |
| `require` inside (DN §3.6) | CE-TXN-1 |
| `break` to an outer loop | CE-TXN-1 |
| `continue` to an outer loop | CE-TXN-1 |
| `return` inside a match arm inside | CE-TXN-1 |
| `abort` outside a transaction | CE-TXN-2 |
| `abort` in a helper called from a transaction (DN §7.2) | CE-TXN-2 |
| `abort Err(CardError.NotFound)` | CE-OUT-3 |
| `abort Err(5)` | CE-OUT-3 |
| `abort;` | CE-SYN-1 |
| `abort Ok();` | CE-SYN-1 |
| A lexically nested transaction | CE-TXN-3 |
| Nesting through a call (DN §7.3) | CE-TXN-3 |
| Nesting through a two-step call chain | CE-TXN-3 |
| Nesting on a path that is never taken (conservative) | CE-TXN-3 |
| A call to an API marked not-in-transaction | CE-TXN-4, if OI-40 is decided as (a). A placeholder is needed. **I propose deferring this test to SP13**, when the catalog format exists |

**Runtime tests**, listed for SP12:

- commit visibility;
- rollback on `abort`;
- rollback on a trap;
- session changes surviving an `abort`;
- recovery after interruption, which needs fault injection.

## 6. Steps

1. Register D-375…D-383. Record OI-39 and OI-40.
2. Write chapter 11.
3. Add §A.2.9.
4. Write `tools/generators/sp10_tests.py` and generate the tests.
5. Write `tools/checkers/txncheck.py`: boundary tracking, `abort` placement, structural nesting over the call graph, and completion. Add it to `run_checks.py`.
6. Run all checks.
7. Update traceability. This completes D-055, D-109 to D-111, D-131, D-132 and D-207.

## 7. Choices made in this sub-plan

These are open for redirection:

- **The boundary rule is lexical and per function.** A helper may freely `return`, `attempt` and `require`; only the transaction owner's body is restricted. This is what DN §3.6 says.
- **`abort` operand errors reuse CE-OUT-3** instead of adding a new class.
- **The OI-40 test is deferred** until the platform catalog format exists (SP13).
