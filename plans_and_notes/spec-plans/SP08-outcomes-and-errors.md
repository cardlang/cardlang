# SP8 — Outcomes and errors: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 9 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/09-outcomes-and-errors.md` | Outcomes: what they are, how they are produced (`return Ok`/`Err`, forwarding) and how they must be consumed (`match`, `attempt`, forwarding return); `attempt` typing and semantics; outcome `match`; restricted error bindings; the `errors` declaration; error values and their categories; `Err` versus rollback |
| `spec/annex-A-grammar.md` §A.2.7 | `ErrorSetDeclaration` (already in §A.2.1), with a reference to the patterns in §A.2.5 |
| `conformance/valid/out-*`, `conformance/invalid/out-*` | One test per example, plus the error-code tests deferred from SP4 (D-428) |
| Register, Annex C, Annex D, 00-index | Body decisions D-360…, new issues, rule coverage and the CE-OUT index |

**Out of scope:**

| Topic | Where |
|---|---|
| `abort Err` and the transaction-boundary restrictions on `return`, `attempt` and `require` | Chapter 11 (SP10) |
| Host reporting of the four outcome categories, and status-word mapping | Chapters 12 and 13, and Annex B |
| The final catalog of `CardError` member names and codes | Annex B (SP13). Chapter 9 uses the agreed placeholders (D-415) |

## 2. Sources

- **DN sections:** §3.2 (`checked_convert` outcomes), §3.6 (match and pattern vocabulary, `return`), §3.7 (forwarding returns), §6.1, §6.2, §6.3 (all), §7.2 (Err is not an abort request).
- **Decisions:**

| Decisions | Topic |
|---|---|
| D-010, D-011, D-012 + D-418 | Results versus traps; no exceptions; every function returns an outcome |
| D-013, D-014, D-015, D-016, D-017 | `match`/`attempt`; discarding is an error; outcomes cannot be stored; `attempt` typing |
| D-018 + D-413 | At most one error set |
| D-019 | Separate categories |
| D-028 | Error bindings |
| D-107, D-108 | Explicit returns; exhaustive matching and read-only bindings |
| D-408 | `attempt` positions (applied in chapter 6) |
| D-428 | Codes are literals |

### 2.1 Body-only decisions to register (D-360…)

| ID | Decision | Source |
|---|---|---|
| D-360 | An outcome match has exactly one success arm, zero or more specific error arms, and one mandatory final catch-all (`Err(name)` or `Err(_)`). Specific errors precede the catch-all. Listing every known error does not make the catch-all optional | DN §3.6, §6.3 |
| D-361 | The pattern vocabulary is `Ok(name)`, `Ok(_)`, `Ok()`, `Err(Set.Member)`, `Err(name)` and `Err(_)`. There are no guards, alternatives, ranges, nested patterns or destructuring | DN §3.6 |
| D-362 | Success payload bindings are independent read-only copies, local to their arm | DN §3.6 |
| D-363 | `Ok` and `Err` are restricted syntax for returns, `abort` and patterns, not general constructors | DN §6.3 |
| D-364 | `attempt` propagates the error unchanged, whatever the enclosing payload type, and never catches traps | DN §6.3 |
| D-365 | Application errors carry identity only: no strings or payloads. Names and codes are unique within the error set | DN §6.3 |
| D-366 | Published error codes must not change meaning, and must not be reused after removal | DN §6.3; PN §5 |
| D-367 | Platform errors use the reserved namespace `CardError`, which applications cannot impersonate. Errors carry no application-origin field. Propagation preserves category and code | DN §6.3 |
| D-368 | Returning or propagating `Err` is not a rollback request. Earlier persistent and session changes remain | DN §6.3, §7.2 |

## 3. Planned rules (chapter 9)

**§9.1 Outcomes**

- **OUT-1** Every function, platform API call and outcome-producing intrinsic completes with exactly one outcome: `Ok(v)`, `Ok()` or `Err(e)`. Recoverable failures are `Err`. Execution faults are traps (chapter 13). There are no exceptions (D-010, D-011, D-012).
- **OUT-2** `Outcome(T)` exists only in this specification. No type can be written for an outcome. An outcome cannot be stored, passed, nested or used as a value (CE-EXP-14, EXP-48). It must be consumed immediately (D-016, D-418).

**§9.2 Producing outcomes**

- **OUT-3** In a function whose payload type is `T`, `return Ok(e);` requires `e ⇐ T`. In a function with no payload, the only success return is `return Ok();`. Any other combination is **CE-OUT-2** (D-107).
- **OUT-4** `return Err(x);` requires `x` to be either a qualified error member (application set or `CardError`, subject to OI-37) or an error binding (§9.5). Anything else is **CE-OUT-3** (D-107, D-028).
- **OUT-5** `return call;` forwards the complete outcome. The call must produce `Outcome(U)` with `U` identical to `T`, including the no-payload case. A mismatch is **CE-OUT-2** (DN §3.7).
- **OUT-6** `Ok` and `Err` appear only in `return`, in `abort` (chapter 11) and in patterns. `Ok(…)` anywhere else does not derive (CE-SYN-1) (D-363).

**§9.3 Consuming outcomes**

- **OUT-7** Every outcome is consumed by exactly one of: an outcome `match`, `attempt`, or a forwarding `return`. A call used as a statement on its own, such as `f();` or `checked_add(a, b);`, discards its outcome and is **CE-OUT-1** (D-015).

**§9.4 `attempt`**

- **OUT-8** The operand of `attempt` must be a call that produces an outcome. Anything else is **CE-OUT-4**.
- **OUT-9** As an expression, `attempt c` has exactly the payload type `T`, with no conversion and no default. If `c` produces `Outcome()`, it can be used only in the statement form `attempt c;`. Using the expression form for it, or using the statement form with a call that has a payload, is **CE-OUT-4**. Use `Ok(_)` in a `match` to ignore a payload deliberately (D-017).
- **OUT-10** Semantics:
  1. Evaluate the call.
  2. If it produces `Ok(v)`, the result is `v`, an independent copy.
  3. If it produces `Err(e)`, the enclosing function or command immediately returns `Err(e)` unchanged — same category, same code — whatever the enclosing payload type.

  Traps are not caught. Chapter 11 forbids crossing a transaction boundary (D-014, D-364).

**§9.5 Outcome `match` and error bindings**

- **OUT-11** Patterns, checked against the scrutinee's `Outcome(T)`:
  - `Ok(name)` and `Ok(_)` require a payload;
  - `Ok()` requires no payload;
  - `Err(Set.Member)`, `Err(name)` and `Err(_)` match errors.

  An incompatible pattern, or an enum pattern, is **CE-OUT-5** (D-361).
- **OUT-12** Shape of the match:
  - exactly one success arm;
  - zero or more specific error arms, with no duplicates;
  - exactly one final catch-all, `Err(name)` or `Err(_)`, which is mandatory.

  A missing success arm or catch-all, a second success arm, a duplicate specific error, or any arm after the catch-all is **CE-OUT-5** (D-108, D-360).
- **OUT-13** Semantics: the scrutinee is evaluated once. The success arm runs on `Ok`. A matching specific arm runs on `Err`; otherwise the catch-all arm runs. A payload binding is a read-only independent copy, local to its arm (assigning to it is CE-STM-2) (D-362).
- **OUT-14** An *error binding*, introduced by `Err(name)`, is read-only and local to its arm. It needs no annotation, and it need not be used. Its only allowed uses are `return Err(name);` and, inside a transaction, `abort Err(name);`. Any other use is **CE-OUT-6**: copying, comparing, passing, returning as a payload, use as a `require` operand, or field access (D-028).

**§9.6 The application error set**

- **OUT-15** `errors Name { Member = literal; … }` is a top-level declaration. An application has zero or one error set; a second one is **CE-OUT-7**. Member count rules are subject to OI-36 (D-018, D-413).
- **OUT-16** Each code is an integer literal checked against `u16` (EXP-7). A code of zero, a duplicate code, or a code that is not a literal is **CE-OUT-7**. Member names are unique (NAM-15). A code literal above 65 535 is CE-EXP-2 (D-018, D-365, D-428).
- **OUT-17** Published codes must keep their meaning. A removed code is never reused for a different error. This obligation is on application evolution and cannot be checked by a compiler (D-366).

**§9.7 Error values and categories**

- **OUT-18** An error value has a *category*, either application or platform, and a nonzero `u16` code. It carries nothing else: no string, payload or origin field. The two categories are distinct even when their codes are equal. Propagation never changes the category or the code (D-019, D-365, D-367).
- **OUT-19** Platform errors are members of the reserved `CardError` set. Its members and codes are platform-defined; the names used in this specification are the placeholders of D-415. Applications cannot declare `CardError` (NAM-14). Whether application code may name `CardError` members in `return`, `abort` and `require` is subject to OI-37 (D-367).

**§9.8 `Err` is not rollback**

- **OUT-20** Returning or propagating `Err` undoes nothing: neither persistent nor session writes, and not writes through references. A caller's active transaction is not aborted by a callee's `Err`. Only `abort` rolls back (chapter 11) (D-368, D-356).

**Error classes**

| Class | Meaning |
|---|---|
| CE-OUT-1 | Discarded outcome |
| CE-OUT-2 | Return form or payload mismatch |
| CE-OUT-3 | Invalid `Err` operand |
| CE-OUT-4 | Invalid `attempt` |
| CE-OUT-5 | Invalid outcome match |
| CE-OUT-6 | Misused error binding |
| CE-OUT-7 | Invalid error set |

## 4. New open issues

| ID | Question | Options | Recommendation |
|---|---|---|---|
| **OI-36** Empty error set | May `errors E { }` declare no members? The notes only show non-empty sets. Empty enums and structures are errors (TYP-10, TYP-13) | (a) No: at least one member, CE-OUT-7. (b) Yes | (a). This is consistent with enums and structures, and an application with no errors simply declares no set (D-413) |
| **OI-37** Application use of `CardError` members | DN §6.3 allows "named error members" in `return Err`, `abort Err` and `require`, and says patterns "may name either application or platform errors". Should application code *originate* a platform error, as in `return Err(CardError.NotFound);`, or only match and propagate one it received? | (a) Patterns and propagation only. Naming a `CardError` member in `return`, `abort` or `require` is CE-OUT-3. (b) Allowed everywhere | (a). This keeps the platform category trustworthy for the host: a platform error always originates in the platform. An application signals its own failures with its own error set |

**Decided 2026-11-15:** you accepted both recommendations. They are recorded as D-436 and D-437:

- OUT-15 is **[Agreed]**: an error set must declare at least one member.
- OUT-4 and OUT-19 are **[Agreed]**: `CardError` members may be named only in patterns. Application code propagates a platform error through an error binding and never originates one.

## 5. Conformance tests (about 36)

**Valid (about 12):**

- `match` with `Ok(value)` and `Err(error)` (DN §6.1);
- `Ok()` with a no-payload call (DN §3.7);
- `Ok(_)` ignoring a payload (DN §6.3);
- specific error arms before the catch-all (DN §6.3 `debit`);
- `attempt` as an initializer, with different enclosing payload types (DN §6.3 `is_nonzero`);
- the `attempt` statement for a no-payload call;
- forwarding `return subtract(…)`;
- a checked intrinsic forwarded (D-413);
- propagation by `return Err(error)`;
- an unused error binding;
- an error set with literal codes;
- an application with no error set;
- matching a `CardError` member.

**Invalid (about 24):**

| Test | Expected error |
|---|---|
| A bare call statement (DN §6.3) | CE-OUT-1 |
| A bare checked-intrinsic statement | CE-OUT-1 |
| `Ok(1)` in a no-payload function | CE-OUT-2 |
| `Ok()` in a payload function | CE-OUT-2 |
| Forwarding a call with a different payload type | CE-OUT-2 |
| `Err(5)` | CE-OUT-3 |
| `Err` of an enum variant | CE-OUT-3 |
| `return Err(CardError.NotFound)` (if OI-37 is (a)) | CE-OUT-3 |
| `attempt` of a non-call | CE-OUT-4 |
| The statement form with a payload call | CE-OUT-4 |
| The expression form with a no-payload call | CE-OUT-4 |
| A missing catch-all (DN §6.3) | CE-OUT-5 |
| A missing success arm | CE-OUT-5 |
| A specific arm after the catch-all (DN §3.6) | CE-OUT-5 |
| A duplicate specific arm | CE-OUT-5 |
| `Ok()` against a payload outcome (DN §3.6) | CE-OUT-5 |
| `Ok(State.Idle)` nested (DN §3.6) | CE-SYN-1 |
| Comparing an error binding | CE-OUT-6 |
| Storing an error binding in a `var` | CE-OUT-6 |
| Passing an error binding | CE-OUT-6 |
| An error binding as a `require` operand | CE-OUT-6 |
| `var value: u32 = read_value();` (DN §6.3) | CE-EXP-14 |
| Two error sets | CE-OUT-7 |
| A zero code | CE-OUT-7 |
| A duplicate code | CE-OUT-7 |
| A computed code `BASE + 1` (D-428) | CE-OUT-7 |
| An empty error set (if OI-36 is (a)) | CE-OUT-7 |

**Runtime tests** for `attempt` propagation, unchanged codes and `Err` without rollback are listed now and written in SP12.

## 6. Steps

1. Register D-360…D-368. Add OI-36 and OI-37 and record your decisions.
2. Write chapter 9.
3. Add the §A.2.7 note.
4. Generate the tests, with the chapter cross-check.
5. Update the traceability. This resolves D-408, D-428 and OI-18, the last of which is closed at this review.
6. Checks: extend the checker with outcome consumption, return forms, `attempt` forms, outcome-match shape, error-binding uses and error-set validation. Run it over all tests and the DN blocks.

## 7. Choices made in this sub-plan

These are open for redirection:

- Outcome-match errors get their own class (CE-OUT-5), separate from enum-match errors (CE-STM-4).
- Code stability (OUT-17) is a normative obligation with no diagnostic.
- `attempt` must be applied to a call, not to an arbitrary expression of outcome type. The only outcome expressions are calls anyway.
