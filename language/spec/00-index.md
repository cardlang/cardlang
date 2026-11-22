# CardLang Language Specification — Draft 0.2

This is the normative specification of the CardLang language.

**Draft 0.2 (2026-11-19).** What changed since Draft 0.1 is in `language/releases/draft-0.2.md`. The CardLang Base Profile 1, a platform specification, is in `platform/`.

## Contents

| File | Chapter |
|---|---|
| [01-scope-and-conventions.md](01-scope-and-conventions.md) | 1 Scope and conventions |
| [02-lexical-structure.md](02-lexical-structure.md) | 2 Lexical structure |
| [03-program-structure-and-names.md](03-program-structure-and-names.md) | 3 Program structure and names |
| [04-types.md](04-types.md) | 4 Types |
| [05-constant-expressions.md](05-constant-expressions.md) | 5 Constant expressions |
| [06-expressions.md](06-expressions.md) | 6 Expressions |
| [07-statements-and-control-flow.md](07-statements-and-control-flow.md) | 7 Statements and control flow |
| [08-functions-and-references.md](08-functions-and-references.md) | 8 Functions, references and slices |
| [09-outcomes-and-errors.md](09-outcomes-and-errors.md) | 9 Outcomes and errors |
| [10-state-and-initialization.md](10-state-and-initialization.md) | 10 State and initialization |
| [11-transactions.md](11-transactions.md) | 11 Transactions |
| [12-host-entry-point.md](12-host-entry-point.md) | 12 Host entry point |
| [13-runtime-failures.md](13-runtime-failures.md) | 13 Runtime failures |
| [annex-A-grammar.md](annex-A-grammar.md) | A Grammar |
| [annex-B-platform-contract.md](annex-B-platform-contract.md) | B Platform contract |
| [annex-C-open-issues.md](annex-C-open-issues.md) | C Open issues |
| [annex-D-traceability.md](annex-D-traceability.md) | D Traceability |

Related files:

- `language/rationale/decision-register.md`: the decision IDs (`D-nnn`) cited by rules.
- `language/conformance/README.md`: the conformance test format.
- `src/cardlang/README.md`: the reference checkers, the reference interpreter and `run_checks.py`.

## Rules per chapter

| Chapter | Rules |
|---|---|
| 2 Lexical structure | 25 |
| 3 Program structure and names | 22 |
| 4 Types | 23 |
| 5 Constant expressions | 14 |
| 6 Expressions | 55 |
| 7 Statements and control flow | 25 |
| 8 Functions, references and slices | 24 |
| 9 Outcomes and errors | 22 |
| 10 State and initialization | 14 |
| 11 Transactions | 18 |
| 12 Host entry point | 16 |
| 13 Runtime failures | 12 |
| Annex B Platform contract | 35 |
| **Total** | 305 |

`tests/speccheck.py` checks these counts against the rules actually defined.

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
| CE-LEX-5 | Malformed byte-string literal | [2 §2.8](02-lexical-structure.md#28-lexical-errors) |
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
| CE-OUT-4 | Invalid attempt or ignore operand, or attempt form | [9 §9.9](09-outcomes-and-errors.md#99-errors-defined-in-this-chapter) |
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
| CE-STM-8 | Slice assignment lengths differ | [7 §7.11](07-statements-and-control-flow.md#711-errors-defined-in-this-chapter) |
| CE-SYN-1 | No derivation of the grammar exists | [Annex A §A.0](annex-A-grammar.md#a0-syntax-errors) |

## Index of trap kinds

| Kind | Meaning | Defined in |
|---|---|---|
| TRAP-OVERFLOW | Result above the maximum; signed minimum ÷ −1 | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-UNDERFLOW | Result below the minimum | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-DIV-ZERO | Zero divisor | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-NEGATION | Negation of the signed minimum | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-SHIFT | Shift count ≥ width | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-BOUNDS | Index, slice, element reference or decode length out of range | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-RESPONSE-COUNT | Returned count > response.length | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-TXN-CAPACITY | Transaction or atomic-update capacity exceeded | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-COMMIT | Contained commit failure | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-NESTED-TXN | Runtime nesting check (unreachable in accepted programs) | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-EXHAUSTED | Execution budget exhausted; runtime stack check (unreachable) | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |
| TRAP-VM | Invalid instruction or VM state (unreachable in verified programs) | [13 §13.2](13-runtime-failures.md#132-trap-kinds) |

## Index of rules

<!-- generated by tests/rule_index.py; do not edit by hand -->

All 305 rules, in chapter order. Each chapter is the authority for its own rules.

| Rule | Defined in |
|---|---|
| LEX-1 | [2.1 Source text](02-lexical-structure.md#21-source-text) |
| LEX-2 | [2.1 Source text](02-lexical-structure.md#21-source-text) |
| LEX-3 | [2.1 Source text](02-lexical-structure.md#21-source-text) |
| LEX-4 | [2.1 Source text](02-lexical-structure.md#21-source-text) |
| LEX-5 | [2.1 Source text](02-lexical-structure.md#21-source-text) |
| LEX-6 | [2.2 Whitespace and comments](02-lexical-structure.md#22-whitespace-and-comments) |
| LEX-7 | [2.2 Whitespace and comments](02-lexical-structure.md#22-whitespace-and-comments) |
| LEX-8 | [2.2 Whitespace and comments](02-lexical-structure.md#22-whitespace-and-comments) |
| LEX-9 | [2.2 Whitespace and comments](02-lexical-structure.md#22-whitespace-and-comments) |
| LEX-10 | [2.3 Token formation](02-lexical-structure.md#23-token-formation) |
| LEX-11 | [2.3 Token formation](02-lexical-structure.md#23-token-formation) |
| LEX-12 | [2.4 Identifiers, keywords and reserved names](02-lexical-structure.md#24-identifiers-keywords-and-reserved-names) |
| LEX-13 | [2.4 Identifiers, keywords and reserved names](02-lexical-structure.md#24-identifiers-keywords-and-reserved-names) |
| LEX-14 | [2.4 Identifiers, keywords and reserved names](02-lexical-structure.md#24-identifiers-keywords-and-reserved-names) |
| LEX-15 | [2.4 Identifiers, keywords and reserved names](02-lexical-structure.md#24-identifiers-keywords-and-reserved-names) |
| LEX-16 | [2.4 Identifiers, keywords and reserved names](02-lexical-structure.md#24-identifiers-keywords-and-reserved-names) |
| LEX-17 | [2.5 Literals](02-lexical-structure.md#25-literals) |
| LEX-18 | [2.5 Literals](02-lexical-structure.md#25-literals) |
| LEX-19 | [2.5 Literals](02-lexical-structure.md#25-literals) |
| LEX-20 | [2.5 Literals](02-lexical-structure.md#25-literals) |
| LEX-21 | [2.5 Literals](02-lexical-structure.md#25-literals) |
| LEX-25 | [2.6 Operators and punctuators](02-lexical-structure.md#26-operators-and-punctuators) |
| LEX-22 | [2.6 Operators and punctuators](02-lexical-structure.md#26-operators-and-punctuators) |
| LEX-23 | [2.6 Operators and punctuators](02-lexical-structure.md#26-operators-and-punctuators) |
| LEX-24 | [2.6 Operators and punctuators](02-lexical-structure.md#26-operators-and-punctuators) |
| NAM-1 | [3.1 Applications and compilation units](03-program-structure-and-names.md#31-applications-and-compilation-units) |
| NAM-2 | [3.1 Applications and compilation units](03-program-structure-and-names.md#31-applications-and-compilation-units) |
| NAM-3 | [3.1 Applications and compilation units](03-program-structure-and-names.md#31-applications-and-compilation-units) |
| NAM-4 | [3.1 Applications and compilation units](03-program-structure-and-names.md#31-applications-and-compilation-units) |
| NAM-5 | [3.1 Applications and compilation units](03-program-structure-and-names.md#31-applications-and-compilation-units) |
| NAM-6 | [3.2 Top-level declarations](03-program-structure-and-names.md#32-top-level-declarations) |
| NAM-7 | [3.2 Top-level declarations](03-program-structure-and-names.md#32-top-level-declarations) |
| NAM-8 | [3.2 Top-level declarations](03-program-structure-and-names.md#32-top-level-declarations) |
| NAM-9 | [3.2 Top-level declarations](03-program-structure-and-names.md#32-top-level-declarations) |
| NAM-10 | [3.2 Top-level declarations](03-program-structure-and-names.md#32-top-level-declarations) |
| NAM-11 | [3.3 The application scope](03-program-structure-and-names.md#33-the-application-scope) |
| NAM-12 | [3.3 The application scope](03-program-structure-and-names.md#33-the-application-scope) |
| NAM-13 | [3.3 The application scope](03-program-structure-and-names.md#33-the-application-scope) |
| NAM-14 | [3.3 The application scope](03-program-structure-and-names.md#33-the-application-scope) |
| NAM-15 | [3.4 Member scopes and dotted names](03-program-structure-and-names.md#34-member-scopes-and-dotted-names) |
| NAM-16 | [3.4 Member scopes and dotted names](03-program-structure-and-names.md#34-member-scopes-and-dotted-names) |
| NAM-17 | [3.4 Member scopes and dotted names](03-program-structure-and-names.md#34-member-scopes-and-dotted-names) |
| NAM-18 | [3.4 Member scopes and dotted names](03-program-structure-and-names.md#34-member-scopes-and-dotted-names) |
| NAM-19 | [3.5 Lexical scopes and visibility](03-program-structure-and-names.md#35-lexical-scopes-and-visibility) |
| NAM-20 | [3.5 Lexical scopes and visibility](03-program-structure-and-names.md#35-lexical-scopes-and-visibility) |
| NAM-21 | [3.5 Lexical scopes and visibility](03-program-structure-and-names.md#35-lexical-scopes-and-visibility) |
| NAM-22 | [3.5 Lexical scopes and visibility](03-program-structure-and-names.md#35-lexical-scopes-and-visibility) |
| TYP-1 | [4.1 Kinds of type](04-types.md#41-kinds-of-type) |
| TYP-2 | [4.1 Kinds of type](04-types.md#41-kinds-of-type) |
| TYP-3 | [4.2 Type expressions and type identity](04-types.md#42-type-expressions-and-type-identity) |
| TYP-4 | [4.2 Type expressions and type identity](04-types.md#42-type-expressions-and-type-identity) |
| TYP-5 | [4.2 Type expressions and type identity](04-types.md#42-type-expressions-and-type-identity) |
| TYP-6 | [4.3 Primitive types](04-types.md#43-primitive-types) |
| TYP-7 | [4.3 Primitive types](04-types.md#43-primitive-types) |
| TYP-8 | [4.3 Primitive types](04-types.md#43-primitive-types) |
| TYP-9 | [4.3 Primitive types](04-types.md#43-primitive-types) |
| TYP-10 | [4.4 Enums](04-types.md#44-enums) |
| TYP-11 | [4.4 Enums](04-types.md#44-enums) |
| TYP-12 | [4.4 Enums](04-types.md#44-enums) |
| TYP-13 | [4.5 Structures](04-types.md#45-structures) |
| TYP-14 | [4.5 Structures](04-types.md#45-structures) |
| TYP-15 | [4.5 Structures](04-types.md#45-structures) |
| TYP-16 | [4.5 Structures](04-types.md#45-structures) |
| TYP-17 | [4.6 Fixed arrays](04-types.md#46-fixed-arrays) |
| TYP-18 | [4.6 Fixed arrays](04-types.md#46-fixed-arrays) |
| TYP-19 | [4.6 Fixed arrays](04-types.md#46-fixed-arrays) |
| TYP-20 | [4.6 Fixed arrays](04-types.md#46-fixed-arrays) |
| TYP-21 | [4.7 Unsized array view types](04-types.md#47-unsized-array-view-types) |
| TYP-22 | [4.8 Default values](04-types.md#48-default-values) |
| TYP-23 | [4.9 Finite sizes and target capacity](04-types.md#49-finite-sizes-and-target-capacity) |
| CEX-1 | [5.1 Global constants](05-constant-expressions.md#51-global-constants) |
| CEX-2 | [5.1 Global constants](05-constant-expressions.md#51-global-constants) |
| CEX-3 | [5.2 The constant-expression subset](05-constant-expressions.md#52-the-constant-expression-subset) |
| CEX-4 | [5.2 The constant-expression subset](05-constant-expressions.md#52-the-constant-expression-subset) |
| CEX-5 | [5.2 The constant-expression subset](05-constant-expressions.md#52-the-constant-expression-subset) |
| CEX-6 | [5.2 The constant-expression subset](05-constant-expressions.md#52-the-constant-expression-subset) |
| CEX-7 | [5.3 Mandatory compile-time evaluation](05-constant-expressions.md#53-mandatory-compile-time-evaluation) |
| CEX-8 | [5.3 Mandatory compile-time evaluation](05-constant-expressions.md#53-mandatory-compile-time-evaluation) |
| CEX-9 | [5.3 Mandatory compile-time evaluation](05-constant-expressions.md#53-mandatory-compile-time-evaluation) |
| CEX-10 | [5.3 Mandatory compile-time evaluation](05-constant-expressions.md#53-mandatory-compile-time-evaluation) |
| CEX-11 | [5.3 Mandatory compile-time evaluation](05-constant-expressions.md#53-mandatory-compile-time-evaluation) |
| CEX-12 | [5.4 Dependencies](05-constant-expressions.md#54-dependencies) |
| CEX-13 | [5.4 Dependencies](05-constant-expressions.md#54-dependencies) |
| CEX-14 | [5.4 Dependencies](05-constant-expressions.md#54-dependencies) |
| EXP-1 | [6.1 Grammar and grouping](06-expressions.md#61-grammar-and-grouping) |
| EXP-2 | [6.1 Grammar and grouping](06-expressions.md#61-grammar-and-grouping) |
| EXP-3 | [6.1 Grammar and grouping](06-expressions.md#61-grammar-and-grouping) |
| EXP-4 | [6.1 Grammar and grouping](06-expressions.md#61-grammar-and-grouping) |
| EXP-5 | [6.1 Grammar and grouping](06-expressions.md#61-grammar-and-grouping) |
| EXP-6 | [6.1 Grammar and grouping](06-expressions.md#61-grammar-and-grouping) |
| EXP-7 | [6.2 Literals and contextual typing](06-expressions.md#62-literals-and-contextual-typing) |
| EXP-8 | [6.2 Literals and contextual typing](06-expressions.md#62-literals-and-contextual-typing) |
| EXP-9 | [6.2 Literals and contextual typing](06-expressions.md#62-literals-and-contextual-typing) |
| EXP-10 | [6.2 Literals and contextual typing](06-expressions.md#62-literals-and-contextual-typing) |
| EXP-11 | [6.2 Literals and contextual typing](06-expressions.md#62-literals-and-contextual-typing) |
| EXP-12 | [6.2 Literals and contextual typing](06-expressions.md#62-literals-and-contextual-typing) |
| EXP-13 | [6.3 Operator typing](06-expressions.md#63-operator-typing) |
| EXP-14 | [6.3 Operator typing](06-expressions.md#63-operator-typing) |
| EXP-15 | [6.3 Operator typing](06-expressions.md#63-operator-typing) |
| EXP-16 | [6.3 Operator typing](06-expressions.md#63-operator-typing) |
| EXP-17 | [6.3 Operator typing](06-expressions.md#63-operator-typing) |
| EXP-18 | [6.3 Operator typing](06-expressions.md#63-operator-typing) |
| EXP-19 | [6.3 Operator typing](06-expressions.md#63-operator-typing) |
| EXP-20 | [6.4 Evaluation order](06-expressions.md#64-evaluation-order) |
| EXP-21 | [6.4 Evaluation order](06-expressions.md#64-evaluation-order) |
| EXP-22 | [6.4 Evaluation order](06-expressions.md#64-evaluation-order) |
| EXP-23 | [6.5 Arithmetic semantics and failures](06-expressions.md#65-arithmetic-semantics-and-failures) |
| EXP-24 | [6.5 Arithmetic semantics and failures](06-expressions.md#65-arithmetic-semantics-and-failures) |
| EXP-25 | [6.5 Arithmetic semantics and failures](06-expressions.md#65-arithmetic-semantics-and-failures) |
| EXP-26 | [6.5 Arithmetic semantics and failures](06-expressions.md#65-arithmetic-semantics-and-failures) |
| EXP-27 | [6.5 Arithmetic semantics and failures](06-expressions.md#65-arithmetic-semantics-and-failures) |
| EXP-28 | [6.5 Arithmetic semantics and failures](06-expressions.md#65-arithmetic-semantics-and-failures) |
| EXP-29 | [6.6 Checked and wrapping intrinsics](06-expressions.md#66-checked-and-wrapping-intrinsics) |
| EXP-30 | [6.6 Checked and wrapping intrinsics](06-expressions.md#66-checked-and-wrapping-intrinsics) |
| EXP-52 | [6.6 Checked and wrapping intrinsics](06-expressions.md#66-checked-and-wrapping-intrinsics) |
| EXP-53 | [6.6 Checked and wrapping intrinsics](06-expressions.md#66-checked-and-wrapping-intrinsics) |
| EXP-54 | [6.6 Checked and wrapping intrinsics](06-expressions.md#66-checked-and-wrapping-intrinsics) |
| EXP-31 | [6.7 Conversions](06-expressions.md#67-conversions) |
| EXP-32 | [6.7 Conversions](06-expressions.md#67-conversions) |
| EXP-33 | [6.7 Conversions](06-expressions.md#67-conversions) |
| EXP-34 | [6.7 Conversions](06-expressions.md#67-conversions) |
| EXP-35 | [6.7 Conversions](06-expressions.md#67-conversions) |
| EXP-36 | [6.8 Integers and bytes](06-expressions.md#68-integers-and-bytes) |
| EXP-37 | [6.8 Integers and bytes](06-expressions.md#68-integers-and-bytes) |
| EXP-38 | [6.8 Integers and bytes](06-expressions.md#68-integers-and-bytes) |
| EXP-39 | [6.9 Indexing, `.length` and field selection](06-expressions.md#69-indexing-length-and-field-selection) |
| EXP-40 | [6.9 Indexing, `.length` and field selection](06-expressions.md#69-indexing-length-and-field-selection) |
| EXP-41 | [6.9 Indexing, `.length` and field selection](06-expressions.md#69-indexing-length-and-field-selection) |
| EXP-42 | [6.9 Indexing, `.length` and field selection](06-expressions.md#69-indexing-length-and-field-selection) |
| EXP-43 | [6.10 Aggregate construction](06-expressions.md#610-aggregate-construction) |
| EXP-44 | [6.10 Aggregate construction](06-expressions.md#610-aggregate-construction) |
| EXP-45 | [6.10 Aggregate construction](06-expressions.md#610-aggregate-construction) |
| EXP-46 | [6.10 Aggregate construction](06-expressions.md#610-aggregate-construction) |
| EXP-55 | [6.10 Aggregate construction](06-expressions.md#610-aggregate-construction) |
| EXP-47 | [6.11 Calls](06-expressions.md#611-calls) |
| EXP-48 | [6.11 Calls](06-expressions.md#611-calls) |
| EXP-49 | [6.11 Calls](06-expressions.md#611-calls) |
| EXP-50 | [6.11 Calls](06-expressions.md#611-calls) |
| EXP-51 | [6.12 Where `attempt` may appear](06-expressions.md#612-where-attempt-may-appear) |
| STM-1 | [7.1 Blocks and statements](07-statements-and-control-flow.md#71-blocks-and-statements) |
| STM-2 | [7.1 Blocks and statements](07-statements-and-control-flow.md#71-blocks-and-statements) |
| STM-3 | [7.1 Blocks and statements](07-statements-and-control-flow.md#71-blocks-and-statements) |
| STM-4 | [7.2 Local variables](07-statements-and-control-flow.md#72-local-variables) |
| STM-5 | [7.2 Local variables](07-statements-and-control-flow.md#72-local-variables) |
| STM-6 | [7.3 Assignment](07-statements-and-control-flow.md#73-assignment) |
| STM-7 | [7.3 Assignment](07-statements-and-control-flow.md#73-assignment) |
| STM-8 | [7.3 Assignment](07-statements-and-control-flow.md#73-assignment) |
| STM-9 | [7.3 Assignment](07-statements-and-control-flow.md#73-assignment) |
| STM-10 | [7.3 Assignment](07-statements-and-control-flow.md#73-assignment) |
| STM-23 | [7.3 Assignment](07-statements-and-control-flow.md#73-assignment) |
| STM-24 | [7.3 Assignment](07-statements-and-control-flow.md#73-assignment) |
| STM-25 | [7.3 Assignment](07-statements-and-control-flow.md#73-assignment) |
| STM-11 | [7.4 `if`](07-statements-and-control-flow.md#74-if) |
| STM-12 | [7.5 `while`](07-statements-and-control-flow.md#75-while) |
| STM-13 | [7.6 `for`](07-statements-and-control-flow.md#76-for) |
| STM-14 | [7.6 `for`](07-statements-and-control-flow.md#76-for) |
| STM-15 | [7.7 `break` and `continue`](07-statements-and-control-flow.md#77-break-and-continue) |
| STM-16 | [7.8 `match` on enums](07-statements-and-control-flow.md#78-match-on-enums) |
| STM-17 | [7.8 `match` on enums](07-statements-and-control-flow.md#78-match-on-enums) |
| STM-18 | [7.9 `return` and `require`](07-statements-and-control-flow.md#79-return-and-require) |
| STM-19 | [7.9 `return` and `require`](07-statements-and-control-flow.md#79-return-and-require) |
| STM-20 | [7.10 Completion analysis](07-statements-and-control-flow.md#710-completion-analysis) |
| STM-21 | [7.10 Completion analysis](07-statements-and-control-flow.md#710-completion-analysis) |
| STM-22 | [7.10 Completion analysis](07-statements-and-control-flow.md#710-completion-analysis) |
| FUN-1 | [8.1 Function declarations](08-functions-and-references.md#81-function-declarations) |
| FUN-2 | [8.1 Function declarations](08-functions-and-references.md#81-function-declarations) |
| FUN-3 | [8.1 Function declarations](08-functions-and-references.md#81-function-declarations) |
| FUN-4 | [8.2 The static call graph](08-functions-and-references.md#82-the-static-call-graph) |
| FUN-5 | [8.2 The static call graph](08-functions-and-references.md#82-the-static-call-graph) |
| FUN-6 | [8.3 Parameter modes and call-site modes](08-functions-and-references.md#83-parameter-modes-and-call-site-modes) |
| FUN-7 | [8.3 Parameter modes and call-site modes](08-functions-and-references.md#83-parameter-modes-and-call-site-modes) |
| FUN-8 | [8.3 Parameter modes and call-site modes](08-functions-and-references.md#83-parameter-modes-and-call-site-modes) |
| FUN-9 | [8.4 Reference arguments](08-functions-and-references.md#84-reference-arguments) |
| FUN-10 | [8.4 Reference arguments](08-functions-and-references.md#84-reference-arguments) |
| FUN-11 | [8.5 Argument preparation](08-functions-and-references.md#85-argument-preparation) |
| FUN-12 | [8.6 Access-path permissions and aliasing](08-functions-and-references.md#86-access-path-permissions-and-aliasing) |
| FUN-13 | [8.6 Access-path permissions and aliasing](08-functions-and-references.md#86-access-path-permissions-and-aliasing) |
| FUN-14 | [8.6 Access-path permissions and aliasing](08-functions-and-references.md#86-access-path-permissions-and-aliasing) |
| FUN-15 | [8.7 Forwarding references](08-functions-and-references.md#87-forwarding-references) |
| FUN-16 | [8.8 Lifetimes of references](08-functions-and-references.md#88-lifetimes-of-references) |
| FUN-17 | [8.9 Value semantics](08-functions-and-references.md#89-value-semantics) |
| FUN-18 | [8.10 Slices and unsized views](08-functions-and-references.md#810-slices-and-unsized-views) |
| FUN-19 | [8.10 Slices and unsized views](08-functions-and-references.md#810-slices-and-unsized-views) |
| FUN-20 | [8.10 Slices and unsized views](08-functions-and-references.md#810-slices-and-unsized-views) |
| FUN-21 | [8.10 Slices and unsized views](08-functions-and-references.md#810-slices-and-unsized-views) |
| FUN-24 | [8.10 Slices and unsized views](08-functions-and-references.md#810-slices-and-unsized-views) |
| FUN-22 | [8.11 Effects, persistence and errors through references](08-functions-and-references.md#811-effects-persistence-and-errors-through-references) |
| FUN-23 | [8.11 Effects, persistence and errors through references](08-functions-and-references.md#811-effects-persistence-and-errors-through-references) |
| OUT-1 | [9.1 Outcomes](09-outcomes-and-errors.md#91-outcomes) |
| OUT-2 | [9.1 Outcomes](09-outcomes-and-errors.md#91-outcomes) |
| OUT-3 | [9.2 Producing outcomes](09-outcomes-and-errors.md#92-producing-outcomes) |
| OUT-4 | [9.2 Producing outcomes](09-outcomes-and-errors.md#92-producing-outcomes) |
| OUT-5 | [9.2 Producing outcomes](09-outcomes-and-errors.md#92-producing-outcomes) |
| OUT-6 | [9.2 Producing outcomes](09-outcomes-and-errors.md#92-producing-outcomes) |
| OUT-7 | [9.3 Consuming outcomes](09-outcomes-and-errors.md#93-consuming-outcomes) |
| OUT-8 | [9.4 `attempt`](09-outcomes-and-errors.md#94-attempt) |
| OUT-9 | [9.4 `attempt`](09-outcomes-and-errors.md#94-attempt) |
| OUT-10 | [9.4 `attempt`](09-outcomes-and-errors.md#94-attempt) |
| OUT-11 | [9.5 Outcome `match` and error bindings](09-outcomes-and-errors.md#95-outcome-match-and-error-bindings) |
| OUT-12 | [9.5 Outcome `match` and error bindings](09-outcomes-and-errors.md#95-outcome-match-and-error-bindings) |
| OUT-13 | [9.5 Outcome `match` and error bindings](09-outcomes-and-errors.md#95-outcome-match-and-error-bindings) |
| OUT-14 | [9.5 Outcome `match` and error bindings](09-outcomes-and-errors.md#95-outcome-match-and-error-bindings) |
| OUT-21 | [9.5 Outcome `match` and error bindings](09-outcomes-and-errors.md#95-outcome-match-and-error-bindings) |
| OUT-22 | [9.5 Outcome `match` and error bindings](09-outcomes-and-errors.md#95-outcome-match-and-error-bindings) |
| OUT-15 | [9.6 The application error set](09-outcomes-and-errors.md#96-the-application-error-set) |
| OUT-16 | [9.6 The application error set](09-outcomes-and-errors.md#96-the-application-error-set) |
| OUT-17 | [9.6 The application error set](09-outcomes-and-errors.md#96-the-application-error-set) |
| OUT-18 | [9.7 Error values and categories](09-outcomes-and-errors.md#97-error-values-and-categories) |
| OUT-19 | [9.7 Error values and categories](09-outcomes-and-errors.md#97-error-values-and-categories) |
| OUT-20 | [9.8 `Err` is not rollback](09-outcomes-and-errors.md#98-err-is-not-rollback) |
| STA-1 | [10.1 Storage classes](10-state-and-initialization.md#101-storage-classes) |
| STA-2 | [10.2 No initializers on mutable globals](10-state-and-initialization.md#102-no-initializers-on-mutable-globals) |
| STA-3 | [10.3 When defaults are applied](10-state-and-initialization.md#103-when-defaults-are-applied) |
| STA-4 | [10.3 When defaults are applied](10-state-and-initialization.md#103-when-defaults-are-applied) |
| STA-5 | [10.4 Lifecycle handlers](10-state-and-initialization.md#104-lifecycle-handlers) |
| STA-6 | [10.4 Lifecycle handlers](10-state-and-initialization.md#104-lifecycle-handlers) |
| STA-7 | [10.4 Lifecycle handlers](10-state-and-initialization.md#104-lifecycle-handlers) |
| STA-8 | [10.4 Lifecycle handlers](10-state-and-initialization.md#104-lifecycle-handlers) |
| STA-9 | [10.4 Lifecycle handlers](10-state-and-initialization.md#104-lifecycle-handlers) |
| STA-10 | [10.4 Lifecycle handlers](10-state-and-initialization.md#104-lifecycle-handlers) |
| STA-11 | [10.5 Atomic persistent assignment](10-state-and-initialization.md#105-atomic-persistent-assignment) |
| STA-12 | [10.5 Atomic persistent assignment](10-state-and-initialization.md#105-atomic-persistent-assignment) |
| STA-13 | [10.5 Atomic persistent assignment](10-state-and-initialization.md#105-atomic-persistent-assignment) |
| STA-14 | [10.6 Consistency between session and persistent state](10-state-and-initialization.md#106-consistency-between-session-and-persistent-state) |
| TXN-1 | [11.1 Syntax](11-transactions.md#111-syntax) |
| TXN-2 | [11.2 Execution and commit](11-transactions.md#112-execution-and-commit) |
| TXN-3 | [11.2 Execution and commit](11-transactions.md#112-execution-and-commit) |
| TXN-4 | [11.2 Execution and commit](11-transactions.md#112-execution-and-commit) |
| TXN-5 | [11.2 Execution and commit](11-transactions.md#112-execution-and-commit) |
| TXN-6 | [11.3 Leaving a transaction](11-transactions.md#113-leaving-a-transaction) |
| TXN-7 | [11.3 Leaving a transaction](11-transactions.md#113-leaving-a-transaction) |
| TXN-8 | [11.3 Leaving a transaction](11-transactions.md#113-leaving-a-transaction) |
| TXN-18 | [11.3 Leaving a transaction](11-transactions.md#113-leaving-a-transaction) |
| TXN-9 | [11.3 Leaving a transaction](11-transactions.md#113-leaving-a-transaction) |
| TXN-10 | [11.4 No nested transactions](11-transactions.md#114-no-nested-transactions) |
| TXN-11 | [11.5 Failures, recovery and isolation](11-transactions.md#115-failures-recovery-and-isolation) |
| TXN-12 | [11.5 Failures, recovery and isolation](11-transactions.md#115-failures-recovery-and-isolation) |
| TXN-13 | [11.5 Failures, recovery and isolation](11-transactions.md#115-failures-recovery-and-isolation) |
| TXN-14 | [11.5 Failures, recovery and isolation](11-transactions.md#115-failures-recovery-and-isolation) |
| TXN-15 | [11.6 Completion and limits](11-transactions.md#116-completion-and-limits) |
| TXN-16 | [11.6 Completion and limits](11-transactions.md#116-completion-and-limits) |
| TXN-17 | [11.6 Completion and limits](11-transactions.md#116-completion-and-limits) |
| HEP-1 | [12.1 The command declaration](12-host-entry-point.md#121-the-command-declaration) |
| HEP-2 | [12.1 The command declaration](12-host-entry-point.md#121-the-command-declaration) |
| HEP-3 | [12.1 The command declaration](12-host-entry-point.md#121-the-command-declaration) |
| HEP-4 | [12.1 The command declaration](12-host-entry-point.md#121-the-command-declaration) |
| HEP-5 | [12.2 Request and response](12-host-entry-point.md#122-request-and-response) |
| HEP-6 | [12.2 Request and response](12-host-entry-point.md#122-request-and-response) |
| HEP-7 | [12.2 Request and response](12-host-entry-point.md#122-request-and-response) |
| HEP-8 | [12.2 Request and response](12-host-entry-point.md#122-request-and-response) |
| HEP-9 | [12.3 The outcome contract](12-host-entry-point.md#123-the-outcome-contract) |
| HEP-10 | [12.3 The outcome contract](12-host-entry-point.md#123-the-outcome-contract) |
| HEP-11 | [12.3 The outcome contract](12-host-entry-point.md#123-the-outcome-contract) |
| HEP-12 | [12.4 Reporting categories](12-host-entry-point.md#124-reporting-categories) |
| HEP-13 | [12.5 Command execution](12-host-entry-point.md#125-command-execution) |
| HEP-14 | [12.5 Command execution](12-host-entry-point.md#125-command-execution) |
| HEP-15 | [12.6 The application protocol](12-host-entry-point.md#126-the-application-protocol) |
| HEP-16 | [12.7 The conformance scaffold (informative)](12-host-entry-point.md#127-the-conformance-scaffold-informative) |
| RTF-1 | [13.1 Traps](13-runtime-failures.md#131-traps) |
| RTF-2 | [13.1 Traps](13-runtime-failures.md#131-traps) |
| RTF-3 | [13.1 Traps](13-runtime-failures.md#131-traps) |
| RTF-4 | [13.2 Trap kinds](13-runtime-failures.md#132-trap-kinds) |
| RTF-5 | [13.2 Trap kinds](13-runtime-failures.md#132-trap-kinds) |
| RTF-6 | [13.3 Execution limits](13-runtime-failures.md#133-execution-limits) |
| RTF-7 | [13.3 Execution limits](13-runtime-failures.md#133-execution-limits) |
| RTF-8 | [13.3 Execution limits](13-runtime-failures.md#133-execution-limits) |
| RTF-9 | [13.4 Security reset and interruption](13-runtime-failures.md#134-security-reset-and-interruption) |
| RTF-10 | [13.4 Security reset and interruption](13-runtime-failures.md#134-security-reset-and-interruption) |
| RTF-11 | [13.5 Outcome categories and consistency](13-runtime-failures.md#135-outcome-categories-and-consistency) |
| RTF-12 | [13.5 Outcome categories and consistency](13-runtime-failures.md#135-outcome-categories-and-consistency) |
| PLT-1 | [B.1 Conformance](annex-B-platform-contract.md#b1-conformance) |
| PLT-2 | [B.2 Applications and dispatch](annex-B-platform-contract.md#b2-applications-and-dispatch) |
| PLT-3 | [B.2 Applications and dispatch](annex-B-platform-contract.md#b2-applications-and-dispatch) |
| PLT-4 | [B.3 Command execution and isolation](annex-B-platform-contract.md#b3-command-execution-and-isolation) |
| PLT-5 | [B.3 Command execution and isolation](annex-B-platform-contract.md#b3-command-execution-and-isolation) |
| PLT-6 | [B.4 Request, response and reporting](annex-B-platform-contract.md#b4-request-response-and-reporting) |
| PLT-7 | [B.4 Request, response and reporting](annex-B-platform-contract.md#b4-request-response-and-reporting) |
| PLT-8 | [B.4 Request, response and reporting](annex-B-platform-contract.md#b4-request-response-and-reporting) |
| PLT-9 | [B.4 Request, response and reporting](annex-B-platform-contract.md#b4-request-response-and-reporting) |
| PLT-10 | [B.4 Request, response and reporting](annex-B-platform-contract.md#b4-request-response-and-reporting) |
| PLT-11 | [B.4 Request, response and reporting](annex-B-platform-contract.md#b4-request-response-and-reporting) |
| PLT-12 | [B.5 Persistence, transactions and recovery](annex-B-platform-contract.md#b5-persistence-transactions-and-recovery) |
| PLT-13 | [B.5 Persistence, transactions and recovery](annex-B-platform-contract.md#b5-persistence-transactions-and-recovery) |
| PLT-14 | [B.5 Persistence, transactions and recovery](annex-B-platform-contract.md#b5-persistence-transactions-and-recovery) |
| PLT-15 | [B.5 Persistence, transactions and recovery](annex-B-platform-contract.md#b5-persistence-transactions-and-recovery) |
| PLT-16 | [B.5 Persistence, transactions and recovery](annex-B-platform-contract.md#b5-persistence-transactions-and-recovery) |
| PLT-17 | [B.5 Persistence, transactions and recovery](annex-B-platform-contract.md#b5-persistence-transactions-and-recovery) |
| PLT-18 | [B.6 Lifecycle and reset](annex-B-platform-contract.md#b6-lifecycle-and-reset) |
| PLT-19 | [B.6 Lifecycle and reset](annex-B-platform-contract.md#b6-lifecycle-and-reset) |
| PLT-20 | [B.7 Runtime-owned resources](annex-B-platform-contract.md#b7-runtime-owned-resources) |
| PLT-21 | [B.7 Runtime-owned resources](annex-B-platform-contract.md#b7-runtime-owned-resources) |
| PLT-22 | [B.7 Runtime-owned resources](annex-B-platform-contract.md#b7-runtime-owned-resources) |
| PLT-23 | [B.7 Runtime-owned resources](annex-B-platform-contract.md#b7-runtime-owned-resources) |
| PLT-24 | [B.7 Runtime-owned resources](annex-B-platform-contract.md#b7-runtime-owned-resources) |
| PLT-25 | [B.8 The platform API catalog](annex-B-platform-contract.md#b8-the-platform-api-catalog) |
| PLT-26 | [B.8 The platform API catalog](annex-B-platform-contract.md#b8-the-platform-api-catalog) |
| PLT-30 | [B.8 The platform API catalog](annex-B-platform-contract.md#b8-the-platform-api-catalog) |
| PLT-27 | [B.9 `CardError` and trap catalogs](annex-B-platform-contract.md#b9-carderror-and-trap-catalogs) |
| PLT-28 | [B.9 `CardError` and trap catalogs](annex-B-platform-contract.md#b9-carderror-and-trap-catalogs) |
| PLT-29 | [B.10 Target profiles](annex-B-platform-contract.md#b10-target-profiles) |
| PLT-31 | [B.13 Security expectations](annex-B-platform-contract.md#b13-security-expectations) |
| PLT-32 | [B.13 Security expectations](annex-B-platform-contract.md#b13-security-expectations) |
| PLT-33 | [B.13 Security expectations](annex-B-platform-contract.md#b13-security-expectations) |
| PLT-34 | [B.13 Security expectations](annex-B-platform-contract.md#b13-security-expectations) |
| PLT-35 | [B.13 Security expectations](annex-B-platform-contract.md#b13-security-expectations) |
