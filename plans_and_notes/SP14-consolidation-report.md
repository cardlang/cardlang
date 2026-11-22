# SP14 — Consolidation report

Date: 2026-11-17. Sub-plan: `plans_and_notes/spec-plans/SP14-consolidation.md`.

SP14 turned the drafts of SP0–SP13 into one consistent specification, **Draft 0.1**, and replaced claims of consistency with scripted checks. It added no language features. One finding needed your decision (OI-44). Every other finding was a wording, table or tooling defect, and was fixed where it lay without changing agreed meaning.

## 1. Result

| Item | State |
|---|---|
| Rules | 287, all [Agreed] |
| Open issues | OI-1…OI-44, all resolved |
| Decisions | 287 in the register; all covered in Annex D §D.2 (D-134 informative) |
| Rule coverage (Annex D §D.3) | 211 rules cited by tests, 47 exercised by tests that do not cite them, 29 with a stated reason no test can check them |
| Conformance tests | 350: 102 valid, 231 invalid, 17 runtime scenarios |
| `python -I tools/run_checks.py` | 22 runs, all pass |

## 2. Checks that were run

All of these are now permanent parts of `tools/run_checks.py`.

| Check | Tool | Result |
|---|---|---|
| Annex A derives every test file except CE-SYN-1 tests (lexical-error tests skipped) | `grammar.py` | 339 test files pass; the 17 CE-SYN-1 tests do not derive |
| Annex A derives every design-note code block that the full checker accepts | `grammar.py --notes` | 35 blocks pass (of 139; the rest are fragments, pseudo-code or invalid examples) |
| Every rule defined once, with one status tag and a Sources line | `speccheck.py` | pass |
| Every referenced rule, decision, open issue, compile-error class and trap kind is defined | `speccheck.py` | pass |
| Every compile-error class defined once, indexed, expected by a test, and its table lists every rule that raises it | `speccheck.py` | pass after fix F3 |
| Every trap kind of the index is defined in chapter 13 | `speccheck.py` | pass |
| Every Markdown table row has as many cells as its header | `speccheck.py` | pass |
| Every chapter grammar fragment equals its Annex A production (an excerpt marked `…` must show existing alternatives) | `speccheck.py` | pass: 70 chapter productions, 72 in Annex A |
| Every "platform-defined" sentence has a row in the B.12 checklist | `speccheck.py` | pass: 31 rows |
| Every decision a rule cites lists that rule in D.2 and in the register | `speccheck.py` | pass after fix F4 |
| Every rule has a row in the D.3 coverage matrix | `speccheck.py`, `coverage.py` | pass |
| The 00-index rule counts match the rules defined | `speccheck.py` | pass |
| Every chapter's tests still regenerate identically from the chapter text | `tools/generators/sp*_tests.py` | pass |

## 3. Findings and fixes

| # | Finding | Kind | Fix |
|---|---|---|---|
| F1 | EXP-6 said an unparenthesized constructor in a condition position "does not derive", but Annex A used the general `Expression` there, which derives it | Contradiction | **OI-44, decided as D-444.** New `ConditionExpression` productions in §A.2.4, used by `if`, `while`, `for` bounds and `match`. EXP-6 and the fragments of chapters 6, 7 and 9 updated. The Earley check now verifies the rule |
| F2 | `FunctionDeclaration` was defined twice in Annex A (§A.2.1 and §A.2.6) | Defect | Removed from §A.2.6. `grammar.py` now fails on any duplicate |
| F3 | In 35 rows of the chapters' compile-error tables, the *Rules* column omitted rules that raise the class, for example FUN-19 for CE-EXP-9 and TXN-7 for CE-OUT-3 | Incomplete table | Completed from the rule texts (`tools/history/sp14_ce_rules.py`). A rule's text ends at its Sources line, so the examples that follow a rule do not count |
| F4 | Annex D §D.2 and the register's *Implemented by* column missed 90 links: a rule cited a decision, but the decision's row did not list the rule | Incomplete traceability | Added (`tools/history/sp14_reverse_links.py`). D-444 changed from pending to covered |
| F5 | LEX-15, the list of reserved identifiers, omitted the lifecycle-handler names that NAM-14 and STA-8 reserve | Inconsistent wording | `on_install` and `on_power_on` added to LEX-15, with the existing exception that declaring them as functions defines the handler. Sources gain D-422 and D-438 |
| F6 | PLT-9 said that the platform reports an outcome "for every command". RTF-10 and HEP-12 say a security reset or power loss may prevent any response | Inconsistent wording | PLT-9 now applies to every command "that is not ended by a security reset or a loss of power (RTF-10)" |
| F7 | Annex C OI-44 listed only chapter 7 among the affected fragments | Incomplete entry | Lists chapters 6, 7 and 9 |
| F8 | Reference checker: in a block the checker skips, the first field of a constructor (`= Pair { left: 1 }`) was mistaken for the statement `left: 1` and reported as CE-SYN-1 | Tool defect | Fixed in `expcheck.py`, keeping the EXP-6 detection for constructors in condition positions |
| F9 | Reference checkers stop with a Python assertion, not CE-SYN-1, on some malformed input | Tool limitation | Documented in `tools/README.md`. `grammar.py` is now the authority for CE-SYN-1 |
| F10 | The full checker chain does not report an unresolved type name in a global declaration (`session big: u64;`); `typecheck.py` does | Tool limitation | Documented. `typecheck.py` checks the test; the full chain does not run over `invalid/typ-*` |

Twelve D.2 rows list a rule that implements the decision but does not cite it in its Sources line, for example D-024 → FUN-1. These links are correct and harmless. They are left as they are.

## 4. Manual review across chapters

| Topic | Rules read | Result |
|---|---|---|
| `require`, `attempt`, `abort` and `return` at transaction boundaries | STM-12, STM-19, OUT-9, OUT-10, OUT-20, TXN-1–TXN-17 | Consistent. TXN-6 lists every boundary-crossing form, and STM-19 and OUT-10 point to it |
| Slices and bounds | CEX-10, EXP-39, EXP-42, FUN-18–FUN-21 | Consistent: compile-time checks only for fixed arrays with constant-only indices or endpoints, runtime `BOUNDS` otherwise |
| Default values | TYP-22, STM-5, STA-3, STA-4 | Consistent |
| Reserved and predeclared names | LEX-15, NAM-14, STA-8 | F5 |
| Reporting categories | OUT-18, HEP-12, RTF-11, PLT-9 | F6 |
| Capacity limits | TYP-23, STA-13, TXN-16, RTF-6–RTF-8, PLT-29 | Consistent. Computable needs are rejected at build or load time; others trap; no limit changes meaning |
| Compile-error classes reused across chapters | all chapter tables | F3. The reuse is intended, for example CE-OUT-3 for `require` and `abort` operands (D-437), and CE-EXP-9 for slice endpoints |

## 5. Conformance completeness

The 76 rules that no test cited before SP14 were sorted into three groups. Annex D §D.3 records the result, generated by `tools/generators/coverage.py`.

- **Exercised but not cited (47 rules).** Existing tests clearly depend on them, for example STM-1 (blocks) and FUN-1 (declarations). They are mapped to those tests in the matrix rather than by editing test headers, because the generators would overwrite such edits.
- **New tests (9 tests plus one extension), written by `tools/generators/sp14_tests.py`:**
  - `valid/lex-009-long-identifier.card` (LEX-16);
  - `invalid/lex-115-missing-semicolon.card` (LEX-23);
  - `invalid/nam-122-application-wrapper.card` (NAM-8);
  - `invalid/typ-115-no-64-bit.card` (TYP-8);
  - `invalid/exp-143-boolean-operator-integer.card` (EXP-16);
  - `invalid/exp-144-convert-to-bool.card` (EXP-35);
  - `invalid/fun-122-reference-variable.card` (FUN-16);
  - `invalid/out-131-ok-as-value.card` (OUT-6);
  - `runtime/run-017-evaluation-and-copies`: evaluation order of `attempt` operands, independent copies, runtime bitwise and shift results, argument preparation trapping before the callee runs, an `inout` write rolled back by `abort`, no implicit command transaction, and separate request and response (EXP-20, EXP-27, EXP-46, EXP-50, FUN-11, FUN-17, FUN-23, TXN-5, HEP-7);
  - `runtime/run-015-resource-identifiers` gained a step showing that a trap does not delete a resource it created (PLT-23).

  Writing run-017 also confirmed EXP-2 in practice: the first draft's `order * 4 + 1` was rejected as CE-EXP-4 and had to be parenthesized. A deliberately wrong expectation (right-to-left order) made run-017 fail, as it should.
- **Not testable (29 rules).** Each has a reason in the matrix. They are:
  - platform obligations, checked by a platform's own conformance (13 PLT rules);
  - target-profile limits, which are platform-defined (TYP-23, STA-13, TXN-16, RTF-7, RTF-8);
  - properties that are not observable by definition (TYP-9, EXP-22, TXN-14, HEP-13);
  - rules outside a single program (NAM-3, NAM-5, OUT-17);
  - cases the scenario format cannot produce (TXN-12, HEP-8, HEP-10);
  - informative material (PLT-17).

## 6. Representative applications (DN §13)

| Application | Tests | Status |
|---|---|---|
| Counter | `valid/hep-005-counter-application.card`, `runtime/run-011-counter-application` | Written using only [Agreed] rules. Nothing blocks it |
| Wallet | `runtime/run-012-wallet-application` | Written using only [Agreed] rules: authorization, transactions, `abort`, reset. Nothing blocks it |
| Signer | `runtime/run-016-signer-application` | Written up to the platform-API boundary, against the fictional `card.test.sign`. It is blocked only by the absence of a real platform API catalog for keys and signing, which is platform work outside this specification |

## 7. Follow-up work outside this specification

1. **A real platform API catalog** (PLT-25): keys, cryptography, resources and lifecycle events, with transaction behaviour and `CardError` members. It unblocks the signer.
2. **A platform specification** that answers each of the 31 items of the Annex B §B.12 checklist, including status-word mapping, capacities and target profiles, the persistent layout, and the handler names that replace the placeholders `on_install` and `on_power_on`.
3. **A compiler**, using this specification and the conformance suite as its acceptance test. The reference checkers are not a compiler.
4. **A VM and its bytecode format**, guided by the informative Annex B §B.11, together with fault injection for TXN-12 and a target-profile mode for the capacity rules that the suite cannot check today.
