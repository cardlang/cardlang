# 10. State and initialization

CardLang Language Specification, Draft 0.1. Chapter status: **draft complete** (SP9).

This chapter defines:

- the storage classes of application state;
- when persistent and session state receive their default values;
- the language side of lifecycle handlers;
- atomic persistent assignment;
- whose job it is to keep session and persistent state consistent.

Related topics are covered elsewhere:

| Topic | Where |
|---|---|
| Transactions | Chapter 11 |
| What traps and security resets do to state | Chapter 13 |
| Lifecycle events, provisioning, upgrades, migration, persistent layout and atomic-write capacities | Annex B (the platform) |

State declarations use the `GlobalValueDeclaration` production of chapter 3 (Annex A §A.2.1, §A.2.8).

## 10.1 Storage classes

**STA-1 [Agreed]** Every value an application stores belongs to one of four storage classes:

| Class | Declared with | Lifetime | Mutable |
|---|---|---|---|
| Persistent | `persistent name: T;` at top level | Durable application state. It survives commands, traps, resets and power loss | Yes |
| Session | `session name: T;` at top level | Volatile application state (§10.3) | Yes |
| Local | `var name: T;` in a body | One execution of its declaration's scope (chapter 7) | Yes |
| Constant | `const name: T = e;` at top level | None. It is a value fixed during compilation (chapter 5) | No |

Every field and element of an instance has its instance's storage class and mutability (TYP-16). Scope and lifetime are separate concepts. "Global" means application-wide: persistent and session globals are visible throughout their own application (NAM-13). They are never visible to, or shared with, another application (NAM-5). Session state is shared by everything that runs within its application.
*Sources: D-004, D-073, D-374; DN §5, §5.1.*

## 10.2 No initializers on mutable globals

**STA-2 [Agreed]** A `persistent` or `session` declaration has no initializer. Writing `= e` on one is **CE-STA-1**, even when `e` is zero, `false`, or `fill` of a default value. There is exactly one form of mutable global declaration, and it has no `=`. Global constants are the separate case that requires an initializer (CEX-1). Nondefault values are set by lifecycle handlers (§10.4) or by ordinary code.
*Sources: D-122; DN §3.9.*

### Examples

*Valid:* persistent and session globals of each kind of type, without initializers (DN §3.9). (conformance: `valid/sta-001-global-declarations.card`)

```text
struct Account {
    balance: u32;
    identifier: u8[4];
}

enum Mode {
    Off;
    On;
}

persistent balance: u32;
persistent account: Account;
persistent history: u32[8];
session authenticated: bool;
session mode: Mode;
session scratch: u8[128];
```

*Invalid:* each of these is in its own test, and each is **CE-STA-1**.

| Code | Conformance |
|---|---|
| `persistent balance: u32 = 100;` (DN §3.9) | `invalid/sta-101-persistent-initializer.card` |
| `session scratch: u8[128] = fill(0);` (DN §3.9) | `invalid/sta-102-session-fill-initializer.card` |
| `persistent counter: u32 = 0;` | `invalid/sta-103-persistent-zero-initializer.card` |
| `session ready: bool = false;` | `invalid/sta-104-session-false-initializer.card` |

## 10.3 When defaults are applied

**STA-3 [Agreed]** Persistent state receives its default values once:

- When an application's persistent state is first created, every `persistent` global holds `default(T)` (TYP-22). The platform defines when that is, for example at installation (Annex B).
- After that, persistent values survive commands, traps, resets and power loss.
- Default values are never applied to them again.

Deleting persistent state, upgrading an application, and migrating persistent values between versions are platform-defined (Annex B).
*Sources: D-123, D-128, D-369, D-416 (OI-16); DN §3.9, §5.*

**STA-4 [Agreed]** Session state is initialized and cleared as follows:

- At every chip power-on, every `session` global holds `default(T)` before any application code runs.
- Session values persist from one command to the next.
- Session values are preserved when a command traps (chapter 13).
- A security reset clears all session state. The next initialization restores the defaults (chapter 13).
- An ordinary trap never re-initializes session state.

Whether other events affect session state, such as deselection or logical channels, is platform-defined (Annex B).
*Sources: D-050, D-051, D-054, D-123, D-128; DN §3.9, §5, §6.4.*

## 10.4 Lifecycle handlers

**STA-5 [Agreed]** Setup that needs nondefault values runs in *lifecycle handlers*. A lifecycle handler is a function whose name and signature are reserved by the platform for a lifecycle event. Examples are provisioning persistent data and preparing session state. The platform defines all of the following (Annex B):

- which lifecycle events exist;
- when each handler runs, and in what order;
- whether a handler must be defined;
- what happens if a handler returns `Err` or traps;
- how an interrupted installation is handled.

Setup that writes persistent values must be designed to run only when the platform runs it. Resetting a durable balance at every power-on, for example, would destroy existing state.
*Sources: D-124, D-370, D-407 (OI-7); DN §3.9; PN §3.*

**STA-6 [Agreed]** Until the platform catalog defines lifecycle handlers, this specification uses two placeholder handlers:

| Handler | Signature | Runs |
|---|---|---|
| `on_install` | `function on_install()`: no parameters, no payload | Once, after the application's persistent state is created |
| `on_power_on` | `function on_power_on()`: no parameters, no payload | After session defaults are applied at power-on |

Annex B confirms or replaces these names, as for the `CardError` placeholders (D-415).
*Sources: D-438 (OI-38).*

**STA-7 [Agreed]** An application defines a handler by declaring a `function` with the handler's reserved name and exactly its reserved signature: the same parameters and modes, and the same payload type. A function with a handler's name but any other signature is **CE-STA-2**.
*Sources: D-422 (OI-22), D-438 (OI-38).*

**STA-8 [Agreed]** Handler names are reserved in every application, whether or not the application defines the handler (NAM-14). Declaring anything other than a function under a handler name is **CE-NAM-5**. Defining a handler is optional unless the platform requires it.
*Sources: D-422 (OI-22).*

**STA-9 [Agreed]** Application code never calls a lifecycle handler. Only the platform does. A call to a handler anywhere in the application is **CE-STA-3**. To share logic between a handler and other code, put it in an ordinary function that both call.
*Sources: D-422 (OI-22); DN §3.7 (by analogy with the command).*

**STA-10 [Agreed]** In every other respect a lifecycle handler is an ordinary function:

- It must end with an explicit outcome (STM-21).
- It may call ordinary functions and platform APIs.
- It is part of the call graph, so it may not be reached recursively (FUN-5).
- It follows all the rules of chapters 6 to 11.

*Sources: D-422 (OI-22).*

### Examples

*Valid:* the two placeholder handlers, one provisioning persistent state and one preparing session state. (conformance: `valid/sta-004-lifecycle-handlers.card`)

```text
persistent installed_version: u16;
session retry_limit: u8;

function on_install() {
    installed_version = 1;
    return Ok();
}

function on_power_on() {
    retry_limit = 3;
    return Ok();
}
```

*Valid:* a setup helper that sets session values from constants (DN §3.9). (conformance: `valid/sta-002-setup-helper.card`)

```text
session retry_limit: u8;
session scratch: u8[128];
const DEFAULT_RETRY_LIMIT: u8 = 3;

function example_setup() {
    retry_limit = DEFAULT_RETRY_LIMIT;
    scratch = fill(0xFF);
    return Ok();
}
```

*Invalid:* each of these is in its own test.

| Fault | Class | Conformance |
|---|---|---|
| `function on_install() -> u32 { … }` | CE-STA-2 | `invalid/sta-105-handler-with-payload.card` |
| `function on_power_on(level: u8) { … }` | CE-STA-2 | `invalid/sta-106-handler-with-parameter.card` |
| `attempt on_install();` in another function | CE-STA-3 | `invalid/sta-107-call-handler.card` |
| `const on_install: u32 = 1;` | CE-NAM-5 | `invalid/sta-108-constant-named-like-handler.card` |

## 10.5 Atomic persistent assignment

**STA-11 [Agreed]** Every assignment whose destination is persistent storage is *atomic* for its whole destination. This covers every kind of destination:

- a scalar global;
- a field or element at any depth;
- a whole structure or array, including one written with `fill` or an array list;
- a write through an `inout` reference or a view into persistent storage (FUN-23).

If execution is interrupted and the platform then recovers, the destination holds either its complete previous value or its complete new value. It never holds a mixture or a partly written value.
*Sources: D-057, D-371, D-373; DN §7.1, §8.2, §8.3, §9.3.*

**STA-12 [Agreed]** Atomicity has these limits:

- **Failed right-hand side.** If evaluating the right-hand side fails, the destination is not updated, and side effects that happened while evaluating it remain (STM-10).
- **Separate assignments.** Two persistent assignments are not atomic together. An interruption may fall between them, unless a transaction groups them (chapter 11).
- **Inside a transaction.** While a transaction is active, persistent assignments participate in it (chapter 11).
- **What atomicity is not.** Atomicity does not mean a single hardware write. It does not make a call or a command atomic as a whole.

*Sources: D-371, D-372; DN §7.1.*

**STA-13 [Agreed]** A target profile may support atomic updates only up to some size. An application containing a persistent assignment whose destination exceeds what its target can update atomically is rejected for that target at build or load time. It is never run with a non-atomic update. The limit values, and how the rejection is reported, are platform-defined (Annex B).
*Sources: D-419 (OI-19), D-206; DN §7.1, §7.4.*

### Examples

*Valid:* persistent assignments to a scalar, nested fields, an element, a whole structure and a whole array (DN §7.1). Each is atomic on its own. (conformance: `valid/sta-003-persistent-assignments.card`)

```text
struct Identity {
    identifier: u8[4];
    version: u16;
}

struct Account {
    identity: Identity;
    balance: u32;
    counters: u32[8];
}

persistent account: Account;
persistent replacement: Account;
persistent balance: u32;
persistent identifier: u8[4];

function update(amount: u32) {
    balance = balance - amount;
    account.identity.version = 2;
    account.counters[0] = account.counters[0] + 1;
    account = replacement;
    identifier = fill(0);
    return Ok();
}
```

## 10.6 Consistency between session and persistent state

**STA-14 [Agreed]** The runtime never synchronizes, repairs or invalidates session state to match persistent state. That holds when a transaction is rolled back, when a command traps, and in every other case. A session copy of a persistent value may therefore disagree with it after a failure, for example a session cache updated before an `abort`. Keeping session and persistent state logically consistent is the application's responsibility. Commands never interleave (chapter 12), but that does not remove this responsibility after a failure.
*Sources: D-053; DN §6.4.*

## 10.7 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-STA-1** | A `persistent` or `session` declaration has an initializer | STA-2 |
| **CE-STA-2** | A function with a lifecycle-handler name has the wrong signature | STA-7 |
| **CE-STA-3** | Application code calls a lifecycle handler | STA-9 |
