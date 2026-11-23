# G2 — The core: detailed sub-plan

Planned 2026-11-23, the third work package of the guide's plan of plans. It writes chapters 3, 4 and 5: functions and references, outcomes, and state. These are the chapters that make CardLang different from C. As in G1, each chapter is reviewed by the user before the next is written.

## 1. What there is now

- **Chapters 1 and 2** use functions, `attempt`, `Ok`/`Err`, `require`, `persistent` and slices lightly, each with a pointer to the chapter that explains it.
- **The vault:**
  - the commands `01` read, `02` increment and `20` verify, decoded into an enum;
  - a fixed PIN `b"1234"`;
  - one `command process` that does everything inside its `match`.
- **The vault's design** (`vault.md`):
  - chapter 3 adds helpers;
  - chapter 4 adds the error set and the overflowing counter;
  - chapter 5 adds a persistent PIN, retries, a session flag, `on_install` and a transaction.
- **The spec:**
  - chapter 8: functions, the call graph, modes, aliasing, views;
  - chapter 9: outcomes, `attempt`, `match`, the error set, `Err` is not rollback;
  - chapter 10: storage classes, defaults, the lifecycle handlers `on_install` and `on_session_start` (placeholder names, STA-6), atomic assignment;
  - chapter 11: transactions, `abort`, no nesting.
- **Scenarios** can test a power loss: `interrupt` loses power at the next commit.

## 2. The work

### 2.1 Chapter 3: Functions, references and slices

1. **Functions.** Declaring one; parameters; `-> T` and `return Ok(…)`; a function without a payload. Every function returns an outcome, which chapter 4 explains. Here, `attempt f(…)` simply means "call it".
2. **No recursion.** The call graph is fixed (*FUN-5*), which is how the compiler knows the stack need shown in chapter 1.
3. **Parameter modes.**
   - by value, a copy;
   - `ref`, read-only, without copying;
   - `inout`, read and write.

   The mode is written at the call too, as in `encode(inout response)`, so a reader sees what a call may change.
4. **Views.** A `u8[]` parameter accepts an array of any length, or a slice. `.length` gives the actual length.
5. **What references cannot do.**
   - They cannot be stored or returned, so they cannot outlive the call.
   - The same place cannot be passed twice where one of the two could change it (the aliasing rules).
   - A call cannot be an argument of another call (*EXP-49*).
6. **The vault, version 3 (Q1):** each command becomes a function of its own, called from `process`.

### 2.2 Chapter 4: Outcomes instead of exceptions

1. **Outcomes.** A call produces `Ok(value)` or `Err(error)`, and every outcome must be consumed, by exactly one of:
   - `attempt`, which takes the value or passes the error up;
   - `match`, which handles both;
   - `return f(…)`, which forwards the whole outcome;
   - `ignore`, which discards it deliberately.

   Dropping an outcome silently is an error.
2. **The error set.** One `errors` declaration per applet, with fixed codes, because the codes are what the host sees.
3. **Platform errors,** `CardError`. They come from the platform's APIs, and from `checked_add` and `checked_convert`.
4. **`match` on outcomes:** one success arm, specific errors, and a required catch-all.
5. **Traps are not errors.** A trap is a bug, and it ends the command. An `Err` is a result that the applet chooses. When to use which.
6. **`Err` does not undo anything** (*OUT-20*). This leads into transactions in chapter 5.
7. **The vault, version 4 (Q2):** incrementing past the counter's maximum becomes an error the host can see, instead of a trap.

### 2.3 Chapter 5: State that survives

1. **Four storage classes:** `const`, `persistent`, `session`, and locals. When each gets its defaults.
2. **No initializers on mutable globals.** Lifecycle handlers: `on_install`, and `on_session_start`.
3. **An assignment to persistent state is atomic.** A power loss leaves it either old or new, never half-written. Shown with `interrupt` in a scenario.
4. **Transactions.** Several persistent writes that succeed or fail together. `abort Err(…)`, and why `return Err` inside one is different. Transactions do not nest.
5. **The vault, version 5 (Q3, Q4):**
   - a persistent PIN of 4 to 8 bytes, with its length, and a retry counter of 3;
   - a session flag, set by a correct PIN;
   - a change PIN command `24`, whose writes run in one transaction.

   It also shows the order that resists power loss: the retry counter is decremented before the PIN is compared, and restored on success, so cutting the power during a guess does not give a free try. A scenario with `interrupt` shows it.

### 2.4 Checks

- Every example is checked by `guidecheck`. The error examples use the codes the compiler gives, confirmed one by one, as in chapter 2.
- The `interrupt` scenarios run on the interpreter and the Python VM, like every scenario.
- Any front-end problem a chapter turns up is fixed in the same package, with a conformance test, as chapter 2's was.

## 3. Checks

- `run_checks` passes, and so does the link check.
- `mkdocs build --strict` passes, and each chapter is viewed in the preview.
- The user reviews each chapter before the next is written.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | How chapter 3 reshapes the vault | (a) one function per command, such as `read_counter(inout response) -> u32` and `verify_pin(ref pin)`, with `process` decoding the request and dispatching to them; (b) keep the dispatch as it is, and pull out only small helpers, such as writing the counter | (a). It is the shape of every real applet, including the FIDO2 example, and it uses every parameter mode: `ref` for the request's data, and `inout` for the response |
| Q2 | What chapter 4 does with the counter's overflow | (a) `checked_add`, with a `match` that turns its overflow into a new `VaultError.CounterExhausted`; (b) keep the trap, and add a new error somewhere else | (a). It shows the choice between a trap and an error on the same line of code, and a platform error turned into the applet's own |
| Q3 | How a wrong PIN tells the host the tries left. An `Err` carries only its code | (a) a verify request with no PIN answers the tries left, as one byte, the way ISO 7816's VERIFY does; a wrong PIN is `Err(WrongPin)`, or `Err(Blocked)` at zero; (b) `Ok` with a status byte, success or tries left. This is legal, since `Ok` means "a response", not "success" (*HEP-11*), but it hides failures from the host's error handling; (c) a separate command for the tries left | (a). Errors stay errors, the host can still ask, and chapter 6 maps it onto ISO 7816's status words |
| Q4 | Where the first PIN comes from | (a) `on_install` sets a default PIN, `b"1234"`, and 3 tries, which the user then changes. It shows a lifecycle handler; (b) no PIN until one is set. A first change PIN command sets it without an old one. Closer to some real devices, but it adds a state to every command | (a). It keeps the vault simple and uses `on_install` for what it is for |

**Decided (user, 2026-11-23):**
- Q1 (a): one function per command, dispatched from `process`.
- Q2 (a): `checked_add`, with a `match` that maps its overflow to `VaultError.CounterExhausted`.
- Q3 (a): a verify request with no PIN answers the tries left. A wrong PIN is `Err(WrongPin)`, or `Err(Blocked)` at zero.
- Q4 (a): `on_install` sets the default PIN `b"1234"` and 3 tries.
