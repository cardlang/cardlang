# SP12 — Runtime failures: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 13 is not written until you approve this plan.

## 1. Scope

SP12 has two parts. Part A is the last language chapter. Part B is the runtime half of the conformance suite, which earlier sub-plans deferred to this one.

### Part A — Chapter 13 (runtime failures)

| Output | Content |
|---|---|
| `spec/13-runtime-failures.md` | What a trap is and what it does to state; the catalog of trap kinds; execution limits; security reset as seen by the language; failures that end execution with no outcome; the four-category model, gathered in one place; session/persistent consistency (stated in chapter 10) |
| 00-index | The trap-kind index, until now empty |

### Part B — Runtime conformance

| Output | Content |
|---|---|
| `conformance/README.md` | The **runtime test format**, open since SP0: scenario steps and expected host-visible results |
| `conformance/runtime/` | The deferred runtime tests from SP5 to SP11 |
| A second application | The **wallet application**, the second representative app in DN §13 (authorization, transactions, recovery), as a compile-time test and as a runtime scenario |
| `tools/` | Optionally, a reference interpreter for the runtime tests (decision 2 below) |

**Out of scope:**

- Trap reporting codes, permitted diagnostics, and how faults are classified as contained or integrity failures. These belong to Annex B.
- Resource lifecycle on reset (the platform side of D-052). This belongs to SP13.

## 2. Sources

- **DN sections:** §3.6 (execution budget), §6.4 (all), §6.5, §7.2, §7.3, §12, §13.
- **PN sections:** §3, §4, §5.

| Decision | Content |
|---|---|
| D-051 | Traps preserve session state |
| D-053 | Consistency between session and persistent state is the application's job |
| D-054 | A security reset clears session state |
| D-056 | Fatal failure leads to a security reset (language side; the platform side goes to SP13) |
| D-206 | Limits never change semantics |
| D-209 | Error codes stay stable |
| D-415 + D-439 | The trap-kind placeholders |
| D-052 | No cleanup on trap (referenced; owned by SP13) |

### 2.1 Body decisions to register (D-394…)

| ID | Decision | Source |
|---|---|---|
| D-394 | A trap aborts the current command. Application `match` and `attempt` cannot catch it | DN §6.4 |
| D-395 | Session state may be left partly updated by a trap. This is intentional and must be visible in the specification | DN §6.4 |
| D-396 | The defined trap cases are: arithmetic failures, out-of-bounds access, invalid shift counts, exhaustion of the stack or execution budget, attempted nested transactions, and invalid VM instructions or state | DN §6.4 |
| D-397 | A security reset clears volatile state across all applications. It is never returned as a `CardError` | DN §6.4 |
| D-398 | Failures may end execution without any outcome. Persistent atomicity guarantees still hold | DN §6.4 |
| D-399 | An ordinary trap does not trigger a lifecycle reset | PN §3; DN §6.4 |

## 3. Planned rules (chapter 13)

**§13.1 Traps**

- **RTF-1** A trap ends the current command immediately.
  - Every active call frame is discarded, and its references end.
  - No outcome is produced.
  - `match` and `attempt` cannot catch it (D-394, D-010).
- **RTF-2** What a trap does to state:

| State | Effect of a trap |
|---|---|
| Active transaction | Rolled back (TXN-11) |
| Earlier commits and standalone persistent assignments | Remain |
| Session state | Preserved, possibly partly updated (D-395, D-051) |
| Locals | End |
| Runtime-owned resources | No automatic cleanup (D-052, Annex B) |
| Response payload | Not transmitted (HEP-9) |

- **RTF-3** After a trap the device and the application remain usable. Later commands may run. A trap does not trigger lifecycle handlers (D-392, D-399).

**§13.2 Trap kinds**

- **RTF-4** Each trap has a language-level kind. The catalog:

| Kind | Raised by | Rule |
|---|---|---|
| `OVERFLOW` | A result above the maximum, or the signed minimum divided by −1 | EXP-23, EXP-24 |
| `UNDERFLOW` | A result below the minimum | EXP-23 |
| `DIV-ZERO` | A zero divisor | EXP-24 |
| `NEGATION` | Negating the signed minimum | EXP-25 |
| `SHIFT` | A shift count ≥ width | EXP-26 |
| `BOUNDS` | An index, slice or `decode_*` length out of range | EXP-37, EXP-39, FUN-20, STM-9 |
| `RESPONSE-COUNT` | A count > `response.length` | HEP-9 |
| `TXN-CAPACITY` | Transaction capacity exceeded | TXN-16 |
| `COMMIT` | A commit failure that the platform contains | TXN-12 |
| `NESTED-TXN` | A runtime nesting check (unreachable in accepted programs) | TXN-10 |
| `EXHAUSTED` | The execution budget, and possibly the stack (decision 1 below) | STM-12 |
| `VM` | An invalid instruction or invalid VM state (verification safety net) | — |

  The names are the D-415 placeholders, extended by D-439. Their numeric codes and how they are reported are platform-defined (Annex B).
- **RTF-5** Traps are deterministic. The same program, state and request produce the same trap, at the same point in evaluation order (EXP-22).

**§13.3 Execution limits**

- **RTF-6** A command that exhausts its execution budget is `trap(EXHAUSTED)`. The language does not require termination to be proved. The size of the budget is platform-defined (D-347).
- **RTF-7** Stack depth. Decided by decision 1 below.
- **RTF-8** No limit ever changes semantics. Exceeding a build-time or load-time capacity rejects the application (D-206, TYP-23, STA-13).

**§13.4 Security reset**

- **RTF-9** The runtime may issue a security reset, and a fatal platform failure requires one.
  - It clears all volatile state across all applications, including session state.
  - The next initialization restores session defaults (STA-4).
  - It is never an `Err`.
  - It may interrupt a command, which then has no outcome.

  (D-054, D-056, D-397.)
- **RTF-10** Interruptions such as reset or power loss may end execution with no outcome and no response. The language's persistent guarantees still hold: assignment atomicity (STA-11) and all-or-nothing transactions (TXN-13) (D-398).

**§13.5 Outcome categories and consistency**

- **RTF-11** A summary of the four categories: success, application error, platform error and trap. It cross-references HEP-12 and OUT-18. Published error codes stay stable (D-209).
- **RTF-12** A cross-reference to STA-14: the runtime never repairs session state after a failure (D-053).

## 4. Decisions needed

**Decision 1 — OI-42: stack depth.** The call graph is static and acyclic (FUN-5), and frame sizes are known at compile time (TYP-23). So an application's maximum stack need can be computed exactly at build or load time. PN §4 still says "exceeding a runtime stack … limit traps".

| Option | Meaning |
|---|---|
| (a) | The maximum stack need is computed. An application whose need exceeds the target's stack is rejected at build or load time. A runtime stack check remains only as a safety net (`EXHAUSTED`, unreachable in accepted programs) |
| (b) | Stack depth is checked only at runtime (`EXHAUSTED`) |

**Recommendation: (a).** It is deterministic, it catches the problem before deployment, and it matches D-206. Execution-budget exhaustion still traps at runtime, because loops make it unknowable.

**Decision 2: runtime test checking.** Runtime tests describe scenarios, such as "send this request, expect this response or trap". Without a runtime, nothing can execute them.

| Option | Meaning |
|---|---|
| (a) | Write a small **reference interpreter** in `tools/` covering the subset the tests use: expressions, statements, calls, references, transactions with rollback, the command contract, and power-on and reset events. All runtime tests are then actually executed |
| (b) | Write the runtime tests and their format only. They are checked by review until a real runtime exists |

**Recommendation: (a).** It is the only way to catch a wrong expected result, and the existing checkers already provide the parser pieces. The cost is a sizeable new tool, about 500 lines. It is not normative: as with the checkers, the specification wins.

**Decided 2026-11-17.** You accepted both recommendations.

- **Decision 1 (OI-42) is (a)**, recorded as D-442. RTF-7 is **[Agreed]**: an application whose computed maximum stack need exceeds the target's stack is rejected at build or load time. A runtime stack check remains only as a safety net. Execution-budget exhaustion still traps.
- **Decision 2 is (a).** The reference interpreter `tools/interp/` is built in step 5. It is a tooling choice, not a language decision, so it gets no D-ID.

## 5. Runtime test format (proposal for `conformance/README.md`)

A runtime test is a directory with these files:

- **The program:** `*.card` files, plus `files.txt` when there is more than one file.
- **`scenario.txt`:** the steps to run, one per line.

The steps:

```text
install                       # create persistent state with defaults; run on_install if defined
power_on                      # session defaults; run on_power_on if defined
command 01 02 03              # send request bytes (hex); response capacity defaults to 256
command 01 capacity 2         # explicit response capacity
expect ok 00 00 00 01         # success, with exactly these response bytes
expect err app 2              # application error with code 2
expect err platform Overflow  # CardError member (placeholder name)
expect trap OVERFLOW          # trap kind
reset                         # security reset (session cleared; persistent kept)
interrupt during-commit       # fault injection: power loss during the next commit (platform-level)
```

- **Behaviour is observed only through the host's view:** responses, errors and traps. Lines such as `check counter == 3` are not available.
- **Tests that need fault injection** (`interrupt`) are marked `requires: fault-injection`. A harness that cannot inject faults skips them.

## 6. Runtime tests (planned, about 30)

These are the tests deferred from earlier sub-plans, grouped by chapter.

| Chapter | Tests |
|---|---|
| 6 | Overflow and underflow traps; `DIV-ZERO`; minimum ÷ −1 traps; minimum % −1 = 0; `SHIFT`; `NEGATION`; wrapping results; the `decode_be` length trap; short-circuit skipping a faulting index |
| 7 | Destination path evaluated before the right-hand side; `for` over an empty range; a local's default re-initialized on each loop iteration |
| 8 | The aliasing result (`buffer[0]` is 2); arguments prepared left to right; the slice-bounds trap |
| 9 | `attempt` propagates the code unchanged; `Err` does not roll back |
| 10 | Persistent defaults applied once; session defaults after `power_on`; session preserved across a trap; session cleared by `reset` |
| 11 | A commit is visible; `abort` rolls back while session changes survive; a trap rolls back; *recovery after `interrupt`* (fault injection) |
| 12 | `count > length` traps; `Err` and traps suppress the payload; exactly `count` bytes are sent; **counter application** scenario |
| Wallet | **Wallet application**: authorize, debit, insufficient funds, a debit rolled back by `abort` |

## 7. Steps

1. Register D-394…D-399, and record decisions 1 and 2.
2. Write chapter 13, and fill the trap-kind index.
3. Write the runtime test format in `conformance/README.md`.
4. Write the runtime tests and the wallet application, both its compile-time test and its scenario.
5. If decision 2 is (a): write `tools/interp/` and add the runtime tests to `run_checks.py`.
6. Run all checks.
7. Update traceability. This completes D-051, D-053, D-054, D-206, D-209 and D-415, and the language side of D-056.

## 8. Choices made in this sub-plan

These are open for redirection:

- **Host-visible results only.** Runtime tests assert only what the host can see: responses, errors and traps. Internal state is shown indirectly, through later responses.
- **Fault-injection tests are optional** for a harness, and are marked as such.
- **Chapter 13 has no new compile-error classes**, unless decision 1 adds a build-time rejection. That rejection would be reported by the build or load tooling, like STA-13, without a CE class.
