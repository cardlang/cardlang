# 13. Runtime failures

CardLang Language Specification, Draft 0.1. Chapter status: **draft complete** (SP12).

This chapter collects what the language guarantees when execution fails at runtime:

- what a trap is, and what it does to each kind of state;
- the catalog of trap kinds;
- execution limits;
- security resets;
- failures that end execution without any outcome.

It also summarizes the four outcome categories and the rule on session/persistent consistency, which earlier chapters state.

Several related things are platform-defined (Annex B): how traps and categories are encoded for the host, which diagnostics may be disclosed, and how faults are classified as contained or integrity-threatening.

## 13.1 Traps

**RTF-1 [Agreed]** A *trap* is an execution fault. It immediately ends the command that is executing, and that command produces no outcome. All of the following happen:

- every active call frame of the command is discarded, and its local variables end;
- the references and views it holds end (FUN-16);
- the command's response payload is never transmitted (HEP-9).

A trap is not an error value. No application code can intercept it: `match` and `attempt` handle only `Err` outcomes, and nothing catches a trap. The host receives the trap category (§13.5).
*Sources: D-010, D-394; DN §6.1, §6.4.*

**RTF-2 [Agreed]** A trap affects state as follows:

| State | Effect of a trap |
|---|---|
| Persistent writes pending in the active transaction | Rolled back (TXN-11) |
| Persistent writes already committed, and persistent assignments made outside any transaction | Remain |
| Session state | Preserved, exactly as the command left it. It may be partly updated by the interrupted command, and that is intended |
| Local variables, references, views | End with their frames |
| Runtime-owned resources | Not cleaned up, deleted or invalidated because of the trap. Each resource operation defines the state it leaves on failure (Annex B) |
| Response payload | Not transmitted |

Keeping session state consistent with persistent state after a trap is the application's responsibility (STA-14).
*Sources: D-051, D-052, D-053, D-055, D-395; DN §6.4.*

**RTF-3 [Agreed]** After a trap, the device and the application remain usable. Once the trap has been handled, including any rollback, later commands may run (HEP-14). A trap does not reset or re-initialize session state, and it does not run lifecycle handlers.
*Sources: D-051, D-392, D-399; DN §4, §6.4; PN §3.*

## 13.2 Trap kinds

**RTF-4 [Agreed]** Every trap has one of the following language-level *kinds*:

| Kind | Raised when | Defined in |
|---|---|---|
| `OVERFLOW` | An arithmetic result is above its type's maximum, or the signed minimum is divided by −1 | EXP-23, EXP-24 |
| `UNDERFLOW` | An arithmetic result is below its type's minimum, including unsigned subtraction below zero | EXP-23 |
| `DIV-ZERO` | The divisor of `/` or `%` is zero | EXP-24 |
| `NEGATION` | The signed minimum is negated | EXP-25 |
| `SHIFT` | A shift count is at least the width of the left operand | EXP-26 |
| `BOUNDS` | An index, a slice, an element reference, or the argument length of `decode_be`/`decode_le` is out of range | EXP-37, EXP-39, STM-9, FUN-11, FUN-20 |
| `RESPONSE-COUNT` | The command returns a count larger than `response.length` | HEP-9 |
| `TXN-CAPACITY` | A transaction exceeds the target's transaction capacity | TXN-16 |
| `COMMIT` | A commit fails in a way the platform contains | TXN-12 |
| `NESTED-TXN` | A runtime nesting check fails. Accepted programs never reach this (TXN-10) | TXN-10 |
| `EXHAUSTED` | The command exhausts its execution budget, or a runtime stack check fails. Accepted programs never reach the stack case (RTF-7) | RTF-6, RTF-7 |
| `VM` | The VM finds an invalid instruction or invalid state. Verified programs never reach this | — |

These names are language-level placeholders. Annex B confirms them. The numeric codes for each kind, and how a kind is reported to the host if it is reported at all, are platform-defined (Annex B).
*Sources: D-396, D-415 (OI-15), D-439 (OI-39); DN §6.4, §6.5.*

**RTF-5 [Agreed]** Traps are deterministic. Given the same program, the same state and the same request, a trap of the same kind occurs at the same point in evaluation order. An implementation may not move, add, remove or reclassify a trap, except by proving that the operation cannot fail (EXP-22). This holds in every build mode.
*Sources: D-338; DN §3.5, §6.5.*

## 13.3 Execution limits

**RTF-6 [Agreed]** Every command runs under an *execution budget* set by the target profile. A command that exhausts its budget is `trap(EXHAUSTED)`. The language does not require termination to be proved, and `while true` is permitted (STM-12). How the budget is measured and its size are platform-defined (Annex B).
*Sources: D-347, D-206; DN §3.6; PN §4.*

**RTF-7 [Agreed]** An application's maximum stack need is computed at build or load time. This is possible because the call graph is static and acyclic (FUN-5) and every frame has a size known at compile time (TYP-23). An application whose stack need exceeds the stack of its target profile is rejected for that target at build or load time. An implementation may keep a runtime stack check as a safety net, reported as `EXHAUSTED`, but no accepted application can trigger it.
*Sources: D-442 (OI-42), D-206; PN §4.*

**RTF-8 [Agreed]** A capacity limit never changes the meaning of a program. A program that needs more of something than its target provides is rejected at build or load time (TYP-23, STA-13, RTF-7), or it traps at runtime (RTF-6, TXN-16). It is never silently executed with different semantics. For example, value copies are never replaced by shared references, and assignments never become non-atomic.
*Sources: D-206; DN §12; PN §4.*

## 13.4 Security reset and interruption

**RTF-9 [Agreed]** The runtime may issue a *security reset*, and a fatal platform failure requires one. A security reset clears all volatile state across all applications, including every application's session state. Session defaults are restored by the next initialization (STA-4). A security reset may interrupt a command, and that command then has no outcome. A security reset is never reported as an `Err`, whether `CardError` or any other. How a platform decides to issue one, and how it cleans up securely, are platform-defined (Annex B).
*Sources: D-054, D-056, D-397; DN §6.4.*

**RTF-10 [Agreed]** A security reset or a loss of power may end execution with no outcome and no response at all. The persistent guarantees still hold when that happens:

- every persistent assignment is atomic (STA-11);
- every transaction is all-or-nothing after recovery (TXN-13).

A platform that cannot establish integrity after an interruption fails closed (Annex B).
*Sources: D-398, D-207; DN §6.4, §7.1, §7.2.*

## 13.5 Outcome categories and consistency

**RTF-11 [Agreed]** As seen by the host, every command ends in exactly one of four categories, which always remain distinguishable (HEP-12, OUT-18):

| Category | Arises from |
|---|---|
| Success | `Ok(count)` |
| Application error | `Err` of an application error-set member |
| Platform error | `Err` of a `CardError` member |
| Trap | A trap of any kind |

A command can also produce no response at all (RTF-10). The meaning of a published error code never changes (OUT-17).
*Sources: D-019, D-209; DN §6.3; PN §5.*

**RTF-12 [Agreed]** After a trap, an `abort` or a security reset, the runtime never synchronizes, repairs or invalidates session state to match persistent state. Maintaining consistency between them is the application's responsibility (STA-14).
*Sources: D-053; DN §6.4.*

## 13.6 Runtime conformance tests

The behaviour in this chapter, and the runtime behaviour of earlier chapters, is tested by the scenario tests in `conformance/runtime/`. Their format is described in `conformance/README.md`. The reference interpreter in `tools/interp/` runs them. The following table maps each test to the rules it exercises:

| Test | Exercises |
|---|---|
| `runtime/run-001-integer-traps/` | RTF-1, RTF-4; EXP-23 to EXP-26, EXP-30 |
| `runtime/run-002-checked-and-conversions/` | EXP-29, EXP-33, EXP-34, EXP-36, EXP-37 |
| `runtime/run-003-short-circuit-and-bounds/` | EXP-21, EXP-39 |
| `runtime/run-004-assignment-order/` | STM-9, STM-10 |
| `runtime/run-005-loops-and-locals/` | STM-5, STM-14 |
| `runtime/run-006-aliasing-and-slices/` | FUN-12, FUN-14, FUN-20 |
| `runtime/run-007-outcomes/` | OUT-10, OUT-18, OUT-20 |
| `runtime/run-008-state-lifecycle/` | STA-3, STA-4, STA-6, RTF-2, RTF-9 |
| `runtime/run-009-transactions/` | TXN-2, TXN-3, TXN-8, TXN-11 |
| `runtime/run-010-response-contract/` | HEP-9 |
| `runtime/run-011-counter-application/` | HEP-15; OUT-20 (DN §13 counter) |
| `runtime/run-012-wallet-application/` | DN §13 wallet: authorization, transactions, `abort`, reset |
| `runtime/run-013-execution-budget/` | RTF-6 |
| `runtime/run-014-recovery-after-interrupt/` | TXN-13, RTF-10 (needs fault injection) |

## 13.7 Errors defined in this chapter

This chapter defines no compile-error classes. A build-time or load-time rejection under RTF-7 or RTF-8 is reported by the build or load tooling of the target, as for STA-13. Trap kinds are listed in RTF-4.
