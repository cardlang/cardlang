# SP9 — State and initialization: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 10 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/10-state-and-initialization.md` | The storage classes `persistent`, `session`, local and `const`; no initializers on mutable globals; when persistent and session state receive defaults; the language side of lifecycle handlers; atomic persistent assignment, including the size limit; session/persistent consistency |
| `spec/annex-A-grammar.md` §A.2.8 | A note: state declarations are `GlobalValueDeclaration` (§A.2.1), and chapter 10 restricts them |
| `conformance/valid/sta-*`, `conformance/invalid/sta-*` | Compile-time tests. Tests of runtime timing are listed for SP12 |
| Register, Annex C, Annex D, 00-index | Body decisions D-369…, OI-22 and the new issues, rule coverage and the CE-STA index |

**Out of scope:**

| Topic | Where |
|---|---|
| Transactions | Chapter 11 (SP10) |
| What traps do to state, and security reset as the language sees it | Chapter 13 (SP12). Chapter 10 refers to it for session preservation and clearing |
| Lifecycle events, handler scheduling, provisioning, upgrades, migration, persistent layout, and atomic-write capacities | Annex B (SP13). Chapter 10 states only the language-visible rules |

## 2. Sources

- **DN sections:** §3.9 (all), §5, §5.1, §6.4 (the session rows), §7.1, §8.2 and §8.3 (atomic aggregate writes), §9.3 (atomic structure assignment).
- **PN sections:** §3.
- **Decisions:**

| Decisions | Topic |
|---|---|
| D-004 | `persistent` and `session` are mutable |
| D-008 + D-416 | Persistent semantics; deletion, upgrade and migration belong to the platform |
| D-050 | Session state is defaulted at power-on |
| D-057 + D-419 | Atomic persistent assignment; an oversized aggregate is rejected |
| D-122 | No initializers on mutable globals |
| D-123, D-128 | Defaults (applied here for persistent and session state) |
| D-124 + D-407 | Lifecycle handlers have platform-reserved names |
| D-427 | Persistent layout is platform-defined |
| References only: D-051, D-053, D-054 | Owned by SP12 |

### 2.1 Body-only decisions to register (D-369…)

| ID | Decision | Source |
|---|---|---|
| D-369 | Persistent defaults apply once, when the persistent state is first created. They are never reapplied on reset or command | DN §3.9 |
| D-370 | Setup that writes persistent values is distinct from volatile setup. The platform decides when provisioning runs, and how interruption and activation are handled | DN §3.9; PN §3 |
| D-371 | A persistent assignment is atomic: after an interruption, the destination holds either its complete old value or its complete new value. If the right-hand side fails, there is no update, and its side effects are not undone | DN §7.1 |
| D-372 | Two persistent assignments are not atomic together without a transaction. Atomicity does not imply a single hardware write, and it does not make a command atomic | DN §7.1 |
| D-373 | Whole-structure and whole-array assignments, including `fill`, are atomic for the whole destination | DN §7.1, §8.2, §8.3, §9.3 |
| D-374 | "Global" means application-wide. Scope and lifetime are separate concepts. Session state is shared within its application | DN §5, §5.1 |

## 3. Planned rules (chapter 10)

**§10.1 Storage classes**

- **STA-1** Each storage class has a lifetime and a mutability:

| Class | Lifetime | Mutable? |
|---|---|---|
| `persistent` | Durable application state; survives resets and power loss | Yes |
| `session` | Volatile application state | Yes |
| Local (`var`) | One invocation | Yes |
| `const` | None: a compile-time value (chapter 5) | No |

  Every field and element has the storage class of the instance that contains it (TYP-16). Scope and lifetime are separate: `persistent` and `session` globals are visible everywhere in their application (NAM-13) and invisible to other applications (NAM-5) (D-004, D-374).

**§10.2 No initializers on mutable globals**

- **STA-2** A `persistent` or `session` declaration has no initializer, not even a zero or `false` one. Writing one is **CE-STA-1**. Global constants are the separate case that *requires* an initializer (CEX-1) (D-122).

**§10.3 Persistent state**

- **STA-3** When an application's persistent state is first created, every `persistent` global receives `default(T)` (TYP-22). The platform defines when that happens (installation; Annex B). The value then survives commands, traps, resets and power loss, and is never re-defaulted. Deletion, upgrades and migration are platform-defined (D-123, D-128, D-369, D-416).

**§10.4 Session state**

- **STA-4** Every `session` global receives `default(T)` at chip power-on. Session values persist across commands, and across ordinary traps (chapter 13). A security reset clears them, and the next initialization restores the defaults (chapter 13). Other session events, such as deselection or channels, are platform-defined (D-050, D-054, D-051).

**§10.5 Lifecycle handlers**

- **STA-5** Application-specific setup, such as nondefault initial values or provisioning, runs in *lifecycle handlers*. These are functions whose names and signatures the platform reserves (D-407). Which events exist, when they run, their order, and what happens when a handler fails are platform-defined (Annex B) (D-124, D-370).
- **STA-6** to **STA-8**: the language-side rules for handlers. These are decided by OI-22 and OI-38 (§4).

**§10.6 Atomic persistent assignment**

- **STA-9** Every assignment whose destination is persistent storage is atomic for its whole destination. This covers:
  - a scalar;
  - a field;
  - an element;
  - a whole structure or array, including one written with `fill` or an array list;
  - a write through `inout` or a slice element (FUN-23).

  After an interruption and recovery, the destination holds either its complete previous value or its complete new value (D-057, D-371, D-373).
- **STA-10** If the right-hand side fails, the destination is not updated, and earlier side effects remain (STM-10). Two persistent assignments are not atomic together unless a transaction groups them (chapter 11). Inside an active transaction, assignments participate in it. Atomicity does not imply a single hardware write, and a command is never implicitly atomic (D-372).
- **STA-11** An application containing a persistent assignment whose destination is larger than the target can update atomically is rejected at build or load time for that target. It never runs non-atomically. The limit values are platform-defined (D-419, D-206).

**§10.7 Consistency between session and persistent state**

- **STA-12** The runtime never synchronizes, repairs or invalidates session state to match persistent state. That applies after a rolled-back transaction or a trap too. Keeping them consistent is the application's responsibility (D-053, owned by SP12, stated here).

**Error classes:** CE-STA-1 (initializer on a mutable global). The handler classes CE-STA-2… depend on the OI-22 and OI-38 decisions.

## 4. Open issues to decide now

**OI-22 (open since the OI-7 decision)** is the language-side rules for lifecycle handler functions:

| # | Question | Recommendation |
|---|---|---|
| 1 | May application code call a handler directly? | No: **CE-STA-3**. This mirrors the rule that the `command` cannot be called |
| 2 | Are handlers ordinary functions in every other respect: outcomes, completion analysis, part of the call graph so no recursion through them, the same name rules? | Yes |
| 3 | Are handler names reserved even when an application does not define the handler? Is defining one optional? | Yes, reserved. Optional unless the platform requires it. Declaring anything other than a function under a handler name is CE-NAM-5. A function with a handler name but the wrong signature is **CE-STA-2** |

**OI-38 (new): placeholder handler names.** Rules and tests need concrete handler names before the platform catalog exists, just as `CardError` members did (D-415). Two placeholders are proposed:

- `on_install()`: no parameters and no payload. It runs once, after persistent state is created.
- `on_power_on()`: no parameters and no payload. It runs after session defaults are applied at power-on.

Both would be marked as placeholders. Annex B confirms or replaces them, as with D-415.

**Decided 2026-11-15:** you accepted both recommendations. OI-22 is recorded as D-422, the number reserved for it, and OI-38 as D-438.

- STA-6 to STA-8 are **[Agreed]**.
- The placeholder handlers `on_install()` and `on_power_on()` are used, and are marked as placeholders.
- `on_install` and `on_power_on` are also added to the predeclared names in NAM-14. Defining them as functions with the reserved signature is the only allowed declaration.

## 5. Conformance tests (about 14 compile-time tests)

**Valid:**

- `persistent` and `session` globals of every kind of type, without initializers (DN §3.9);
- a setup helper that writes session state from constants (DN §3.9 `example_setup`);
- whole-structure, element and `fill` assignments to persistent state (DN §7.1);
- placeholder handlers defined with the correct signature (OI-38).

**Invalid:**

| Test | Expected error |
|---|---|
| `persistent balance: u32 = 100;` (DN §3.9) | CE-STA-1 |
| `session scratch: u8[128] = fill(0);` (DN §3.9) | CE-STA-1 |
| A persistent global with a zero initializer | CE-STA-1 |
| A session `bool` initialized to `false` | CE-STA-1 |
| A handler with the wrong signature | CE-STA-2 |
| Application code calling a handler | CE-STA-3 |
| A constant named like a handler | CE-NAM-5 |

**Runtime tests** are listed now and written in SP12:

- persistent defaults applied once;
- session defaults at power-on;
- session preserved across a trap;
- session cleared by security reset;
- atomic persistent assignment under interruption, which is a platform-level fault-injection test.

## 6. Steps

1. Register D-369…D-374. Record OI-22 and OI-38.
2. Write chapter 10.
3. Add the §A.2.8 note.
4. Generate the tests, with the chapter cross-check.
5. Update the traceability. This completes D-123 and D-128, and moves D-124 and D-407 to covered.
6. Checks: extend the checker with initializer detection and the handler rules. Run it over all tests and the DN blocks.

## 7. Choices made in this sub-plan

These are open for redirection:

- Chapter 10 states STA-12 (consistency is the programmer's job) even though SP12 owns D-053, because it is about state.
- The oversized-aggregate rejection (STA-11) has no compile-error class, because it is a build or load rejection that depends on the target.
- Runtime tests are deferred to SP12.
