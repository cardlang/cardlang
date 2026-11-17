# SP14 — Consolidation: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: executed 2026-11-17. Findings and results: `plans_and_notes/SP14-consolidation-report.md`.

## 1. Purpose

SP0 to SP13 drafted every chapter and annex. SP14 turns the drafts into one consistent specification, Draft 0.1, and proves its consistency with checks rather than by assertion. It adds no new language features. Any defect it finds is fixed where it lies. If a fix would change agreed meaning, it becomes an open issue for you to decide instead.

**Survey results (2026-11-17)**

| Check | Result |
|---|---|
| Chapter grammar fragments compared with Annex A | All match |
| Annex A nonterminals | All defined. One duplicate: `FunctionDeclaration` appears in §A.2.1 and again in §A.2.6 |
| Rules cited by at least one conformance test | 196 of 287 |
| Rules not cited by any test | 91, in three groups (§3.3) |

## 2. Sources

- The whole specification and every conformance test.
- The plan of plans, which says SP14 must:
  - complete Annex A, cross-checked against every chapter;
  - finalize Annex C and Annex D;
  - check conformance completeness;
  - review consistency across chapters;
  - check whether the representative applications can be written from [Agreed] rules, and list what blocks them.

## 3. Work items

### 3.1 Annex A, the grammar

1. **Consolidate** the sections into one ordered grammar. Remove the duplicate `FunctionDeclaration`. Replace the "skeleton" status table with a contents list. Index every nonterminal and the section that defines it.
2. **Prove the grammar mechanically.** Write `tools/checkers/grammar.py`, an Earley recognizer that reads the EBNF straight from Annex A and runs over token streams. It checks that:
   - every valid test, every runtime program and every self-contained example in the design notes derives `SourceFile`;
   - every CE-SYN-1 test does **not** derive.

   Each mismatch is a real inconsistency between the grammar and a chapter. Decision 1 resolves the one already known.
3. **Fragment equality.** Keep the survey's check, that every chapter fragment matches its Annex A production, as a permanent check in `run_checks.py`.

### 3.2 Consistency review across chapters

These checks are scripted and become part of `run_checks.py`:

- every rule ID, decision ID, open-issue ID, compile-error class and trap kind that is referenced is also defined;
- every rule has exactly one status tag and a *Sources* line;
- no table has broken rows;
- every compile-error class is defined once and used at least once;
- every "platform-defined" reference appears in the B.12 checklist.

**Manual review**, of the places where several chapters say something about the same topic:

| Topic | Chapters and rules |
|---|---|
| `require` / `attempt` / `abort` / `return` across transaction boundaries | 7, 9, 11 |
| Slices and bounds | 5 CEX-10, 6 EXP-39 and EXP-42, 8 FUN-18 to FUN-21 |
| Default values | 4 TYP-22, 7 STM-5, 10 STA-3 and STA-4 |
| Reserved and predeclared names | 2 LEX-15, 3 NAM-14, 10 STA-8 |
| Reporting categories | 9 OUT-18, 12 HEP-12, 13 RTF-11, B PLT-9 |
| Capacity limits | 4 TYP-23, 10 STA-13, 11 TXN-16, 13 RTF-6 to RTF-8, B PLT-29 |
| Error classes reused across chapters | For example, CE-OUT-3 for `abort` and `require` operands |

Findings and their fixes are recorded in a consolidation report (§3.6).

### 3.3 Conformance completeness

The 91 uncited rules fall into three groups:

| Group | Treatment |
|---|---|
| **(a) Exercised but not cited**, for example STM-1 (blocks), FUN-1 (declarations) and EXP-13 (arithmetic) | Add the rule IDs to the `rule:` headers of existing tests that clearly exercise them |
| **(b) Testable but untested**, for example LEX-20 (no negative-literal token), EXP-16 (Boolean operands), EXP-35 (no cast), TYP-5 and CEX-14 | Add tests (decision 2) |
| **(c) Not testable by a conformance test**: platform obligations (most PLT rules), non-observable or informative rules (TYP-9, TXN-14, OUT-17, RTF-5, HEP-13) and build-time rejection by a target (STA-13, RTF-7) | Record them in the coverage matrix with the reason they cannot be tested |

The result is a **rule-to-tests coverage matrix**, Annex D §D.3. Every rule has either at least one test or a stated reason.

### 3.4 Representative applications

DN §13 names three representative applications. This check records which [Agreed] rules each one relies on, and what still blocks it.

| Application | Status |
|---|---|
| Counter | `hep-005` and `run-011` exist. Uses only [Agreed] rules. Nothing blocks it |
| Wallet | `run-012` exists. Uses only [Agreed] rules. Nothing blocks it |
| Signer | `run-016` exists, as a skeleton. It is blocked only by the absence of a real platform API catalog (keys and signing). That is platform work, outside this specification |

This is written up in the consolidation report and summarized in 00-index.

### 3.5 Final annexes and index

- **Annex C:** confirm that all 43 issues are resolved with complete entries. Fix any issue that decision 1 adds.
- **Annex D:**
  - §D.1, the forward table, is finalized;
  - §D.2, the reverse table, is confirmed: 285 decisions covered and D-134 informative;
  - a new §D.3 is the rule coverage matrix.
- **00-index:**
  - a generated index of all rules, giving ID, title phrase and chapter;
  - final rule counts;
  - the status of every file;
  - status "Draft 0.1 — complete".

### 3.6 Consolidation report

`plans_and_notes/SP14-consolidation-report.md` records:

- every check that was run;
- every defect found, and how it was fixed;
- the representative-applications assessment;
- a list of follow-up work outside this specification: a real platform API catalog, a platform specification answering the B.12 checklist, a compiler, and a VM.

## 4. Decisions needed

**Decision 1 — OI-44: how EXP-6 appears in the grammar.**

EXP-6 says that a structure constructor directly in an `if` or `while` condition, a `for` range bound or a `match` scrutinee "does not derive (CE-SYN-1)". However, Annex A's `IfStatement ::= 'if' Expression Block` uses the general `Expression`, which includes `StructConstructor`. The Annex A grammar alone therefore does not exclude the form: it is ambiguous there. The written grammar and the rule disagree.

| Option | Meaning |
|---|---|
| (a) | **Encode it in the grammar.** Add restricted nonterminals for those four positions, such as `ConditionExpression`, in which `PrimaryExpression` has no unparenthesized `StructConstructor`. A parenthesized constructor stays allowed through `'(' Expression ')'`. Annex A then states the rule completely, and the Earley check can verify it |
| (b) | **Keep the grammar general** and state EXP-6 as a syntactic restriction in §A.0, applied after parsing. EXP-6's wording changes from "does not derive" to "is CE-SYN-1" |

**Recommendation: (a).** It makes Annex A self-sufficient and testable, and the meaning stays as decided in D-430. The grammar grows by about five productions.

**Decision 2: tests for testable rules that have none** (group (b) in §3.3).

| Option | Meaning |
|---|---|
| (a) | Write the missing tests now. They are small, and the checkers verify them |
| (b) | Only record the gaps in the coverage matrix |

**Recommendation: (a).** A complete matrix is the point of SP14.

**Decision 3: marking Draft 0.1.**

| Option | Meaning |
|---|---|
| (a) | Mark Draft 0.1 as complete in 00-index and the plan of plans, and create a local annotated git tag `spec-draft-0.1` on the final commit. Nothing is pushed |
| (b) | Mark it in the documents only, with no tag |

**Recommendation: (a).** A tag gives a fixed reference point for later drafts. It stays local until you choose to push.

**Decided 2026-11-17.** You accepted all three recommendations:

- **Decision 1 (OI-44): option (a)**, recorded as D-444. EXP-6 is encoded in Annex A with restricted nonterminals for condition positions.
- **Decision 2: option (a).** The missing tests for testable rules are written now.
- **Decision 3: option (a).** Draft 0.1 is marked complete, and a local annotated tag `spec-draft-0.1` is created once you ask for the final commit.

## 5. Steps

1. Record the decisions.
2. Consolidate Annex A, including the decision 1 change.
3. Write `grammar.py` (the Earley recognizer) and run it. Fix every mismatch it finds.
4. Run the scripted consistency checks and add them to `run_checks.py`. Do the manual review and fix what it finds.
5. Fill in the citations for group (a), write the tests for group (b), and build the coverage matrix (§D.3).
6. Finalize Annexes C and D and the index.
7. Write the consolidation report.
8. Run all checks.
9. Commit and tag, when you ask.

## 6. Exit checklist

- Every valid and runtime program derives from Annex A, and every CE-SYN-1 test does not.
- All scripted consistency checks pass, and they are part of `run_checks.py`.
- Every rule has at least one test, or a stated reason why none is possible.
- Annex D covers every decision and every rule.
- The consolidation report lists every finding and its fix.
