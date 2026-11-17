# CardLang Language Specification — Draft 0.1

This is the normative specification of the CardLang language. It is being written in sub-plans; see `plans_and_notes/specification-plan-of-plans.md`. Conventions, status tags and notation are defined in [chapter 1](01-scope-and-conventions.md).

## Contents and status

| File | Chapter | Sub-plan | Status |
|---|---|---|---|
| [01-scope-and-conventions.md](01-scope-and-conventions.md) | 1 Scope and conventions | SP0 | Draft complete |
| [02-lexical-structure.md](02-lexical-structure.md) | 2 Lexical structure | SP1 | Draft complete |
| [03-program-structure-and-names.md](03-program-structure-and-names.md) | 3 Program structure and names | SP2 | Draft complete |
| [04-types.md](04-types.md) | 4 Types | SP3 | Draft complete |
| [05-constant-expressions.md](05-constant-expressions.md) | 5 Constant expressions | SP4 | Draft complete |
| [06-expressions.md](06-expressions.md) | 6 Expressions | SP5 | Draft complete |
| [07-statements-and-control-flow.md](07-statements-and-control-flow.md) | 7 Statements and control flow | SP6 | Draft complete |
| [08-functions-and-references.md](08-functions-and-references.md) | 8 Functions, references and slices | SP7 | Draft complete |
| [09-outcomes-and-errors.md](09-outcomes-and-errors.md) | 9 Outcomes and errors | SP8 | Draft complete |
| [10-state-and-initialization.md](10-state-and-initialization.md) | 10 State and initialization | SP9 | Draft complete |
| [11-transactions.md](11-transactions.md) | 11 Transactions | SP10 | Draft complete |
| [12-host-entry-point.md](12-host-entry-point.md) | 12 Host entry point | SP11 | Draft complete |
| 13-runtime-failures.md | 13 Runtime failures | SP12 | Not started |
| [annex-A-grammar.md](annex-A-grammar.md) | A Grammar | SP1–SP14 | A.1 and A.2.1–A.2.10 complete; consolidation in SP14 |
| annex-B-platform-contract.md | B Platform contract | SP13 | Not started |
| [annex-C-open-issues.md](annex-C-open-issues.md) | C Open issues | SP0, then all | OI-1…OI-41 all resolved; none open |
| [annex-D-traceability.md](annex-D-traceability.md) | D Traceability | SP0, then all | Filled for chapters 1–12 |

Related files:

- `plans_and_notes/decision-register.md`: the decision IDs (`D-nnn`) cited by rules.
- `conformance/README.md`: the conformance test format.

## Rule status summary

| Chapter | Rules | [Agreed] | [Proposal] | [Open] |
|---|---|---|---|---|
| 2 Lexical structure | 24 | 24 | 0 | 0 |
| 3 Program structure and names | 22 | 22 | 0 | 0 |
| 4 Types | 23 | 23 | 0 | 0 |
| 5 Constant expressions | 14 | 14 | 0 | 0 |
| 6 Expressions | 51 | 51 | 0 | 0 |
| 7 Statements and control flow | 22 | 22 | 0 | 0 |
| 8 Functions, references and slices | 23 | 23 | 0 | 0 |
| 9 Outcomes and errors | 20 | 20 | 0 | 0 |
| 10 State and initialization | 14 | 14 | 0 | 0 |
| 11 Transactions | 17 | 17 | 0 | 0 |
| 12 Host entry point | 16 | 16 | 0 | 0 |
| **Total** | 246 | 246 | 0 | 0 |

Each sub-plan updates this table when its chapter is drafted.

## Index of compile-error classes

| Class | Meaning | Defined in |
|---|---|---|
| CE-CEX-1 | const declaration without an initializer | [5 §5.5](05-constant-expressions.md#55-errors-defined-in-this-chapter) |
| CE-CEX-2 | Non-constant expression where a constant is required | [5 §5.5](05-constant-expressions.md#55-errors-defined-in-this-chapter) |
| CE-CEX-3 | Arithmetic failure during compile-time evaluation | [5 §5.5](05-constant-expressions.md#55-errors-defined-in-this-chapter) |
| CE-CEX-4 | Bounds failure during compile-time evaluation | [5 §5.5](05-constant-expressions.md#55-errors-defined-in-this-chapter) |
| CE-CEX-5 | Dependency cycle among constants, lengths and types | [5 §5.5](05-constant-expressions.md#55-errors-defined-in-this-chapter) |
| CE-EXP-1 | Type does not match the required type | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-2 | Integer literal out of range | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-3 | Integer literal has no type context | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-4 | Different binary operators at one grouping level | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-5 | Chain of comparisons | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-6 | Operator applied to a type it does not accept | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-7 | Call or attempt inside a call argument | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-8 | Invalid conversion or byte intrinsic | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-9 | Index type is not u8, u16 or u32 | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-10 | Array list or fill without an expected array type | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-11 | Array list with the wrong number of elements | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-12 | Constructor field missing, undeclared or repeated | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-13 | Field selection the receiver does not have | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-14 | Outcome used where a value is required | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-15 | Call target is not callable | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-EXP-16 | Wrong number of arguments | [6 §6.13](06-expressions.md#613-errors-defined-in-this-chapter) |
| CE-FUN-1 | Call graph contains a cycle (recursion) | [8 §8.12](08-functions-and-references.md#812-errors-defined-in-this-chapter) |
| CE-FUN-2 | Argument mode does not match the parameter mode | [8 §8.12](08-functions-and-references.md#812-errors-defined-in-this-chapter) |
| CE-FUN-3 | ref or inout argument does not identify existing storage | [8 §8.12](08-functions-and-references.md#812-errors-defined-in-this-chapter) |
| CE-FUN-4 | inout argument is not mutable through its path | [8 §8.12](08-functions-and-references.md#812-errors-defined-in-this-chapter) |
| CE-FUN-5 | Slice in a position where slices are not allowed | [8 §8.12](08-functions-and-references.md#812-errors-defined-in-this-chapter) |
| CE-HEP-1 | The application declares no command | [12 §12.8](12-host-entry-point.md#128-errors-defined-in-this-chapter) |
| CE-HEP-2 | The application declares more than one command | [12 §12.8](12-host-entry-point.md#128-errors-defined-in-this-chapter) |
| CE-HEP-3 | The command signature is not (ref u8[], inout u8[]) -> u32 | [12 §12.8](12-host-entry-point.md#128-errors-defined-in-this-chapter) |
| CE-LEX-1 | File is not valid UTF-8 | [2 §2.8](02-lexical-structure.md#28-lexical-errors) |
| CE-LEX-2 | Character not permitted outside a comment | [2 §2.8](02-lexical-structure.md#28-lexical-errors) |
| CE-LEX-3 | Unterminated block comment | [2 §2.8](02-lexical-structure.md#28-lexical-errors) |
| CE-LEX-4 | Malformed numeric literal | [2 §2.8](02-lexical-structure.md#28-lexical-errors) |
| CE-NAM-1 | Duplicate name in the application scope | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-NAM-2 | Unresolved name | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-NAM-3 | Shadowing a visible name | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-NAM-4 | Duplicate name in one lexical scope | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-NAM-5 | Top-level declaration uses a predeclared name | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-NAM-6 | Bad top-level storage keyword | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-NAM-7 | Storage keyword other than var inside a body | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-NAM-8 | Duplicate member in a structure, enum or error set | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-NAM-9 | Unknown qualified member | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-NAM-10 | Unknown platform path | [3 §3.6](03-program-structure-and-names.md#36-errors-defined-in-this-chapter) |
| CE-TXN-1 | Control transfer would leave an active transaction | [11 §11.7](11-transactions.md#117-errors-defined-in-this-chapter) |
| CE-TXN-2 | abort not lexically inside a transaction in the same function | [11 §11.7](11-transactions.md#117-errors-defined-in-this-chapter) |
| CE-TXN-3 | Nested transaction, lexically or through the call graph | [11 §11.7](11-transactions.md#117-errors-defined-in-this-chapter) |
| CE-TXN-4 | Call to a platform API not permitted inside transactions | [11 §11.7](11-transactions.md#117-errors-defined-in-this-chapter) |
| CE-TYP-1 | Name in a type position is not a type | [4 §4.10](04-types.md#410-errors-defined-in-this-chapter) |
| CE-TYP-2 | Enum with no variants | [4 §4.10](04-types.md#410-errors-defined-in-this-chapter) |
| CE-TYP-3 | Structure with no fields | [4 §4.10](04-types.md#410-errors-defined-in-this-chapter) |
| CE-TYP-4 | Structure contains itself | [4 §4.10](04-types.md#410-errors-defined-in-this-chapter) |
| CE-TYP-5 | Unsized array type outside a ref/inout parameter | [4 §4.10](04-types.md#410-errors-defined-in-this-chapter) |
| CE-TYP-6 | Array of arrays | [4 §4.10](04-types.md#410-errors-defined-in-this-chapter) |
| CE-TYP-7 | Array length zero or not unsigned | [4 §4.10](04-types.md#410-errors-defined-in-this-chapter) |
| CE-OUT-1 | Outcome discarded by a call used as a statement | [9 §9.9](09-outcomes-and-errors.md#99-errors-defined-in-this-chapter) |
| CE-OUT-2 | Return form does not match the payload, or forwarding mismatch | [9 §9.9](09-outcomes-and-errors.md#99-errors-defined-in-this-chapter) |
| CE-OUT-3 | Err or require operand is not an application error member or error binding | [9 §9.9](09-outcomes-and-errors.md#99-errors-defined-in-this-chapter) |
| CE-OUT-4 | Invalid attempt operand or form | [9 §9.9](09-outcomes-and-errors.md#99-errors-defined-in-this-chapter) |
| CE-OUT-5 | Invalid outcome match | [9 §9.9](09-outcomes-and-errors.md#99-errors-defined-in-this-chapter) |
| CE-OUT-6 | Error binding used other than in return Err or abort Err | [9 §9.9](09-outcomes-and-errors.md#99-errors-defined-in-this-chapter) |
| CE-OUT-7 | Invalid error set | [9 §9.9](09-outcomes-and-errors.md#99-errors-defined-in-this-chapter) |
| CE-STA-1 | persistent or session declaration has an initializer | [10 §10.7](10-state-and-initialization.md#107-errors-defined-in-this-chapter) |
| CE-STA-2 | Lifecycle-handler function has the wrong signature | [10 §10.7](10-state-and-initialization.md#107-errors-defined-in-this-chapter) |
| CE-STA-3 | Application code calls a lifecycle handler | [10 §10.7](10-state-and-initialization.md#107-errors-defined-in-this-chapter) |
| CE-STM-1 | Expression other than an attempt call used as a statement | [7 §7.11](07-statements-and-control-flow.md#711-errors-defined-in-this-chapter) |
| CE-STM-2 | Assignment target is not an assignable place | [7 §7.11](07-statements-and-control-flow.md#711-errors-defined-in-this-chapter) |
| CE-STM-3 | break or continue outside a loop | [7 §7.11](07-statements-and-control-flow.md#711-errors-defined-in-this-chapter) |
| CE-STM-4 | Invalid match: missing, repeated or foreign variant, wildcard, or unmatchable scrutinee | [7 §7.11](07-statements-and-control-flow.md#711-errors-defined-in-this-chapter) |
| CE-STM-5 | Function or command body may complete normally | [7 §7.11](07-statements-and-control-flow.md#711-errors-defined-in-this-chapter) |
| CE-STM-6 | for index type is not an integer type | [7 §7.11](07-statements-and-control-flow.md#711-errors-defined-in-this-chapter) |
| CE-STM-7 | require operand is not a qualified error member | [7 §7.11](07-statements-and-control-flow.md#711-errors-defined-in-this-chapter) |
| CE-SYN-1 | No derivation of the grammar exists | [Annex A §A.0](annex-A-grammar.md#a0-syntax-errors) |

## Index of trap kinds

| Kind | Meaning | Defined in |
|---|---|---|
| — | None defined yet; chapter 13 owns the catalog | — |

## Index of rules

The full rule list is generated from the chapters during SP14. Until then, each chapter is the authority for its own rules.
