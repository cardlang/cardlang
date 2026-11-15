# SP6 — Statements and control flow: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 7 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/07-statements-and-control-flow.md` | Blocks and the statement grammar; local variables; assignment; `if`; `while`; `for`; `break` and `continue`; `match` on enums; the control effect of `return` and `require`; completion analysis |
| `spec/annex-A-grammar.md` §A.2.5 | `Block`, `Statement` and all statement forms, plus the `MatchArm` and `Pattern` productions. Chapter 9 gives the outcome patterns their meaning |
| `conformance/valid/stm-*`, `conformance/invalid/stm-*` | One test per example |
| Register, Annex C, Annex D, 00-index | Body decisions D-343…, new issues, rule coverage and the CE-STM index |

**Out of scope:**

| Topic | Where |
|---|---|
| Typing of `return Ok`/`Err`, whole-outcome forwarding, `attempt` statements, outcome `match` patterns, error bindings | Chapter 9 (SP8). Chapter 7 gives their syntax and control effect only |
| `transaction`, `abort`, and the rules for crossing a transaction boundary | Chapter 11 (SP10). Chapter 7 refers to them |
| Writing through `ref` parameters, and argument modes | Chapter 8 (SP7) |
| Atomicity of persistent assignments | Chapter 10 (SP9) |

## 2. Sources

- **DN sections:** §3.5 (assignment), §3.6 (all), §3.7 (completion rules), §3.9 (local defaults and initializers), §3.10 (statements after `return` are allowed and checked), §3.11 (enum match), §5.1 (local `var` only), §8.2 (whole-array assignment and indexed-assignment order).
- **Decisions:**

| Decisions | Topic |
|---|---|
| D-006 | Locals use `var` only |
| D-030, D-034 | Completion analysis; no fall-through |
| D-069 | Enum match |
| D-078 | Whole-array assignment |
| D-080, D-409 | Assignment order: destination first |
| D-105 | Assignment is a statement |
| D-106 | The set of control-flow statements |
| References: D-123, D-128 | Local defaults |

### 2.1 Body-only decisions to register (D-343…)

| ID | Decision | Source |
|---|---|---|
| D-343 | Braces are mandatory on every control-flow body and match arm. Conditions must be `bool`, with no truthiness. Parentheses around a whole condition are optional | DN §3.6 |
| D-344 | No `switch`, fall-through, `goto`, labelled loops or multi-level exits. `if` and `match` are statements | DN §3.6 |
| D-345 | `for`: half-open range, bounds evaluated once left to right before the loop, zero iterations when start ≥ end, read-only index local to the body, ascending with unit step, and each endpoint must fit the index type | DN §3.6 |
| D-346 | `continue` in a `while` loop rechecks the condition; in a `for` loop it advances the index | DN §3.6 |
| D-347 | Infinite loops are written `while true`. The language need not prove termination. Exhausting the execution budget traps | DN §3.6 |
| D-348 | `require c else E;` is exactly `if not c { return Err(E); }` | DN §3.6 |
| D-349 | No chained assignment, no increment or decrement operators, and no assignment in conditions. Compound assignment (`+=`) is deferred | DN §3.5 |
| D-350 | A local's explicit initializer is not preceded by a default. A failed initializer does not fall back to the default. Locals without an initializer receive the default each time their declaration is reached | DN §3.9 |
| D-351 | Unreachable statements are permitted, and they are still checked (for example after a `return`) | DN §3.10 |

## 3. Planned rules (chapter 7)

**§7.1 Blocks and statements**

- **STM-1** A block is `{ Statement* }`. Bodies of functions, commands, control-flow statements and match arms are blocks, and braces are always required. The statement forms are:
  - `var`;
  - assignment;
  - `attempt` statement;
  - `if`, `while`, `for`, `match`;
  - `break`, `continue`, `return`, `require`;
  - `transaction` and `abort` (chapter 11).

  (D-343, D-344.)
- **STM-2** An *expression statement* is allowed only in the form `attempt call;`, which chapter 9 defines. Any other expression used as a statement is **CE-STM-1** [Open → OI-33].
- **STM-3** A standalone block statement [Open → OI-34].

**§7.2 Local variables**

- **STM-4** `var name: T;` or `var name: T = e;` inside a body. `T` is a value type (TYP-21 applies). The initializer checks against `T` (EXP-10). The local is mutable (D-006).
- **STM-5** Timing of initialization:
  - Without an initializer, the local receives `default(T)` each time execution reaches the declaration.
  - With an initializer, the value is exactly that of `e`, and no default is applied first.
  - If `e` fails, by `attempt` propagation or a trap, the variable never comes into existence, and earlier effects stay.

  (D-350, D-123, D-128.)

**§7.3 Assignment**

- **STM-6** `place = e;`. Assignment is a statement, never an expression. There are no chained, compound or increment forms (D-105, D-349).
- **STM-7** *Places*: a local; a `persistent` or `session` global; an `inout` parameter; a field or element path rooted in one of those. Each of the following is **CE-STM-2**:
  - a constant, or any part of one;
  - a by-value parameter;
  - a `ref` parameter, or a path derived from one (chapter 8);
  - a `for` index or pattern binding;
  - `.length`;
  - a slice;
  - a function, type, or enum variant;
  - any other expression.
- **STM-8** Typing: `e` checks against the type of the place (EXP-10, EXP-12). Arrays require exactly the same element type and length (D-078). Assignment copies the complete value, independently.
- **STM-9** Evaluation order (D-080, D-409):
  1. Evaluate the place's path left to right. Each index is evaluated once and bounds-checked as it is reached; an out-of-bounds index is `trap(BOUNDS)`, before the right-hand side runs.
  2. Evaluate `e`.
  3. Store the value.

  The index is never re-evaluated. The value of `e` is complete before the store begins, so `buffer = fill(buffer[0])` captures the original value.
- **STM-10** If evaluating `e` fails, no store happens, and earlier side effects are not undone. Persistent atomicity is covered in chapter 10.

**§7.4 `if`**

- **STM-11** `if c { } else if c2 { } else { }`. Conditions check against `bool`. They are evaluated in order, and at most one branch runs. `else` is optional. EXP-6 applies to the conditions (D-106, D-343).

**§7.5 `while`**

- **STM-12** The condition is checked before each iteration, so the body may run zero times. `while true` is allowed. Termination is not proved; running out of the execution budget is `trap(EXHAUSTED)` (chapter 13) (D-347).

**§7.6 `for`**

- **STM-13** `for name: T in a..b { }`. `T` must be an integer type; otherwise **CE-STM-6**. Both bounds check against `T`, and each endpoint must fit `T` (EXP-7) (D-345).
- **STM-14** Semantics:
  1. Evaluate `a`, then `b`, once each.
  2. Run the body with `name` taking the values `a`, `a+1`, …, `b−1`, in order. When `a ≥ b`, the body never runs.

  The index is read-only and local to the body. The steps between consecutive values never overflow, because the last value is `b−1 < b ≤ max(T)`. The range is ascending with a step of 1; no other ranges exist (D-345).

**§7.7 `break` and `continue`**

- **STM-15** `break;` exits the nearest enclosing loop. `continue;` starts its next iteration: a `while` rechecks its condition, and a `for` advances its index. Either one outside a loop is **CE-STM-3**. Crossing a transaction boundary is forbidden by chapter 11 (D-346).

**§7.8 `match` on enums**

- **STM-16** When the scrutinee synthesizes an enum type `E`, the arms are patterns `E.Variant`. Every variant of `E` must appear exactly once. A missing variant, a duplicate, a variant of another enum, `_`, or any outcome pattern is **CE-STM-4**. The scrutinee is evaluated once and exactly one arm runs. There is no fall-through, and `match` is a statement (D-069, D-344).
- **STM-17** A scrutinee of outcome type is matched under chapter 9. A scrutinee of any other type is **CE-STM-4**, because integers, `bool`, arrays and structures cannot be matched.

**§7.9 `return` and `require` (control effect)**

- **STM-18** `return …;` ends the enclosing function or command. Its forms, and their typing, are in chapter 9. Chapter 11 restricts `return` inside a transaction.
- **STM-19** `require c else Owner.Member;` is exactly equivalent to `if not c { return Err(Owner.Member); }`. The operand must be a named error member; anything else is **CE-STM-7**. `c` checks against `bool` (D-348).

**§7.10 Completion analysis**

- **STM-20** The normal-completion table from DN §3.7, made normative:

| Construct | May complete normally? |
|---|---|
| `return`, `abort` | Never |
| `break`, `continue` | Never, into the next statement |
| Declarations, assignments, `attempt` statements | Yes |
| `if` without `else` | Yes |
| `if` with `else` | Only if some branch can |
| `match` | Only if some arm can |
| `for`, and `while` with any other condition | Yes |
| `while true` | Only if a `break` syntactically targets it |
| A block | Only if all its statements can, in sequence |
| `transaction` | Exactly when its body can |

  Only the literal `true` counts for `while true`, with no constant folding. `require` may complete. No data-flow analysis is used. (D-030.)
- **STM-21** If a function or command body may complete normally, that is **CE-STM-5**. There is no implicit success, and a computation that is predicted to trap gives no exemption (D-034, D-030).
- **STM-22** Statements after a `return` are permitted, and they are still resolved, type-checked and constant-evaluated (CEX-7) (D-351).

**Error classes**

| Class | Meaning |
|---|---|
| CE-STM-1 | Expression statement |
| CE-STM-2 | Not assignable |
| CE-STM-3 | `break`/`continue` outside a loop |
| CE-STM-4 | Invalid enum match |
| CE-STM-5 | Body may complete normally |
| CE-STM-6 | `for` index type is not an integer type |
| CE-STM-7 | `require` operand is not an error member |

## 4. New open issues

| ID | Question | Options | Recommendation |
|---|---|---|---|
| **OI-33** Expression statements | The notes define only `attempt call;` as a statement made from an expression. A bare call `f();` discards an outcome, which is already an error. What about other expressions used as statements, such as `a + b;` or `x;`? | (a) Only the `attempt` statement form exists. Every other expression statement is CE-STM-1, and a bare call gets the outcome-discard error from chapter 9. (b) Allow expression statements that have no outcome | (a). The other forms have no useful effect |
| **OI-34** Standalone blocks | May a bare `{ … }` appear as a statement, to open a nested scope? The notes neither use nor forbid it | (a) No, it is CE-SYN-1. (b) Yes, as a nested scope | (a). Nothing in the notes needs it, and it can be added later without breaking programs |

**Decided 2026-11-15:** you accepted both recommendations, to be recorded as D-433 and D-434:

- STM-2 is **[Agreed]**: the `attempt` form is the only expression statement.
- STM-3 is **[Agreed]**: there are no standalone blocks, so one is CE-SYN-1.

## 5. Grammar (Annex A §A.2.5)

```
Block            ::= '{' Statement* '}'
Statement        ::= VarStatement | AssignmentStatement | ExpressionStatement
                   | IfStatement | WhileStatement | ForStatement | MatchStatement
                   | BreakStatement | ContinueStatement | ReturnStatement | RequireStatement
                   | TransactionStatement | AbortStatement        /* A.2.9 */
VarStatement     ::= StorageKeyword+ Identifier ':' Type ( '=' Expression )? ';'   /* NAM-10 */
AssignmentStatement ::= Expression '=' Expression ';'
ExpressionStatement ::= Expression ';'                           /* STM-2 */
IfStatement      ::= 'if' Expression Block ( 'else' 'if' Expression Block )* ( 'else' Block )?
WhileStatement   ::= 'while' Expression Block
ForStatement     ::= 'for' Identifier ':' Type 'in' Expression '..' Expression Block
MatchStatement   ::= 'match' Expression '{' MatchArm* '}'
MatchArm         ::= Pattern '=>' Block
Pattern          ::= 'Ok' '(' ( Identifier | '_' )? ')'
                   | 'Err' '(' ( Identifier | '_' | Identifier '.' Identifier ) ')'
                   | Identifier '.' Identifier
                   | '_'                                          /* rejected: STM-16, chapter 9 */
BreakStatement   ::= 'break' ';'
ContinueStatement ::= 'continue' ';'
ReturnStatement  ::= 'return' ( 'Ok' '(' Expression? ')' | 'Err' '(' Expression ')' | Expression ) ';'
RequireStatement ::= 'require' Expression 'else' Expression ';'
```

Notes:

- **Permissive forms.** `VarStatement` accepts any storage keywords (NAM-10), and `AssignmentStatement` accepts any expression on the left (STM-7), so the chapter rules can report the specific errors.
- **The `..` in `ForStatement`.** It is read as the range separator: a `for` bound is never a slice receiver at its outer level.
- **`Pattern '_'`.** It parses, so that STM-16 and chapter 9 can give a specific error.

## 6. Conformance tests (about 36)

**Valid (about 14):**

- local defaults and initializers;
- assignment to a local, a global, a field path, an element path and an `inout` parameter;
- whole-array assignment;
- an `if`/`else if`/`else` chain;
- `while` with `break` and `continue`;
- `for` over `u8` and over `i16` ranges, including an empty range;
- a `for` range using `.length` (DN §8.1);
- an enum match (DN §3.11);
- `require` (DN §6.1 `subtract`);
- `while true` with no `return` after it;
- `if`/`else` where every branch returns;
- statements after a `return`.

**Invalid (about 22):**

| Test | Expected error |
|---|---|
| `a = b = 0;` (DN §3.5) | CE-SYN-1 |
| An assignment inside a condition | CE-SYN-1 |
| `x += 1;` | CE-SYN-1 |
| `count++;` | CE-SYN-1 |
| Assignment to a constant | CE-STM-2 |
| Assignment to a constant's element | CE-STM-2 |
| Assignment to a by-value parameter | CE-STM-2 |
| Assignment to a `for` index | CE-STM-2 |
| Assignment to `buffer.length` (DN §8.1) | CE-STM-2 |
| Assignment to a match binding | CE-STM-2 |
| `break` outside a loop | CE-STM-3 |
| `continue` outside a loop | CE-STM-3 |
| Enum match with a missing variant | CE-STM-4 |
| Enum match with a duplicate variant | CE-STM-4 |
| Enum match with a foreign variant | CE-STM-4 |
| Enum match with `_` | CE-STM-4 |
| Matching an integer | CE-STM-4 |
| A missing final `return` | CE-STM-5 |
| `if` without `else` that returns only in one branch | CE-STM-5 |
| `while true` with a `break` and no `return` after it | CE-STM-5 |
| `for` with index type `bool` | CE-STM-6 |
| `for index: u8 in 0..256` (DN §3.6) | CE-EXP-2 |
| `require` with an integer operand | CE-STM-7 |
| A non-`bool` `if` condition | CE-EXP-1 |
| `a + b;` | CE-STM-1 (OI-33) |
| A standalone block | CE-SYN-1 (OI-34) |

**Runtime tests** for evaluation order (destination before right-hand side), loop semantics and default re-initialization are listed now, and written in SP12.

## 7. Steps

1. Register D-343…D-351, add OI-33 and OI-34, and record your decisions.
2. Write chapter 7.
3. Fill in §A.2.5.
4. Generate the tests, with the chapter cross-check.
5. Update the traceability.
6. Checks:
   - extend the scratchpad checker with a statement checker covering places, loops, enum match exhaustiveness and completion analysis;
   - run it over all tests;
   - run it over the self-contained DN blocks.

## 8. Choices made in this sub-plan

These are open for redirection:

- `for` accepts any integer type, including signed types. The notes give no restriction.
- Only the literal `true` makes a `while` non-completing, with no constant folding.
- The enum-match rules (STM-16) are kept in chapter 7, and outcome match rules go to chapter 9.
- Assignment and `var` use permissive grammar.
- `require` is defined here, and its transaction restriction is in chapter 11.
