# CardLang Language Specification — Draft 0.1

This is the normative specification of the CardLang language. It is being written in sub-plans; see `plans_and_notes/specification-plan-of-plans.md`. Conventions, status tags and notation are defined in [chapter 1](01-scope-and-conventions.md).

## Contents and status

| File | Chapter | Sub-plan | Status |
|---|---|---|---|
| [01-scope-and-conventions.md](01-scope-and-conventions.md) | 1 Scope and conventions | SP0 | Draft complete |
| [02-lexical-structure.md](02-lexical-structure.md) | 2 Lexical structure | SP1 | Draft complete |
| 03-program-structure-and-names.md | 3 Program structure and names | SP2 | Not started |
| 04-types.md | 4 Types | SP3 | Not started |
| 05-constant-expressions.md | 5 Constant expressions | SP4 | Not started |
| 06-expressions.md | 6 Expressions | SP5 | Not started |
| 07-statements-and-control-flow.md | 7 Statements and control flow | SP6 | Not started |
| 08-functions-and-references.md | 8 Functions, references and slices | SP7 | Not started |
| 09-outcomes-and-errors.md | 9 Outcomes and errors | SP8 | Not started |
| 10-state-and-initialization.md | 10 State and initialization | SP9 | Not started |
| 11-transactions.md | 11 Transactions | SP10 | Not started |
| 12-host-entry-point.md | 12 Host entry point | SP11 | Not started |
| 13-runtime-failures.md | 13 Runtime failures | SP12 | Not started |
| [annex-A-grammar.md](annex-A-grammar.md) | A Grammar | SP1–SP14 | A.1 lexical complete; A.2 skeleton |
| annex-B-platform-contract.md | B Platform contract | SP13 | Not started |
| [annex-C-open-issues.md](annex-C-open-issues.md) | C Open issues | SP0, then all | OI-1…OI-21, OI-23, OI-24 resolved; OI-22 open |
| [annex-D-traceability.md](annex-D-traceability.md) | D Traceability | SP0, then all | Skeleton |

Related files:

- `plans_and_notes/decision-register.md`: the decision IDs (`D-nnn`) cited by rules.
- `conformance/README.md`: the conformance test format.

## Rule status summary

| Chapter | Rules | [Agreed] | [Proposal] | [Open] |
|---|---|---|---|---|
| 2 Lexical structure | 24 | 24 | 0 | 0 |
| **Total** | 24 | 24 | 0 | 0 |

Each sub-plan updates this table when its chapter is drafted.

## Index of compile-error classes

| Class | Meaning | Defined in |
|---|---|---|
| CE-LEX-1 | File is not valid UTF-8 | [2 §2.8](02-lexical-structure.md#28-lexical-errors) |
| CE-LEX-2 | Character not permitted outside a comment | [2 §2.8](02-lexical-structure.md#28-lexical-errors) |
| CE-LEX-3 | Unterminated block comment | [2 §2.8](02-lexical-structure.md#28-lexical-errors) |
| CE-LEX-4 | Malformed numeric literal | [2 §2.8](02-lexical-structure.md#28-lexical-errors) |
| CE-SYN-1 | No derivation of the grammar exists | [Annex A §A.0](annex-A-grammar.md#a0-syntax-errors) |

## Index of trap kinds

| Kind | Meaning | Defined in |
|---|---|---|
| — | None defined yet; chapter 13 owns the catalog | — |

## Index of rules

The full rule list is generated from the chapters during SP14. Until then, each chapter is the authority for its own rules.
