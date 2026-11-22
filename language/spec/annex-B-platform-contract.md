# Annex B — Platform contract

CardLang Language Specification, Draft 0.2. Annex status: **draft complete** (SP13).

The language chapters leave some matters to the *platform*: the card operating system, runtime and VM that run CardLang applications. This annex states three kinds of material about that boundary:

1. **`PLT` requirements.** Every conforming platform must meet these. They are normative.
2. **Platform-defined items** (§B.12). These are choices the language leaves open. A platform specification must answer each one.
3. **Informative guidance** (§B.11). This is the VM and target-profile material from the platform notes. It is not normative.

This annex does not design a platform. It specifies no status-word values, journaling scheme, capacity numbers or concrete platform APIs.

## B.1 Conformance

**PLT-1 [Agreed]** A platform conforms to this specification when it meets every `PLT` requirement in this annex, and its platform specification documents a choice for every platform-defined item in §B.12. A platform may add capabilities, such as APIs, `CardError` members or lifecycle events. An addition must not change the meaning of a conforming application.
*Sources: D-206, D-427; DN §12, §13; PN §1.*

## B.2 Applications and dispatch

**PLT-2 [Agreed]** A platform hosts either one application or several completely isolated ones. No application can name, call, reference, read or write anything belonging to another. Errors never pass between applications. Each application has its own resource identifier space (PLT-20).
*Sources: D-020, D-126; DN §1, §4.1; PN §1.*

**PLT-3 [Agreed]** How the host selects an application is platform-defined. Every request addressed to an application is delivered to that application's single `command` (HEP-1). The platform performs no further dispatch within the application: operation identifiers are application data (HEP-15). The PN §1 description of command identifiers and dispatch is superseded by this rule.
*Sources: D-402 (OI-2), D-041, D-042; DN §4; PN §1.*

## B.3 Command execution and isolation

**PLT-4 [Agreed]** The platform runs at most one command at a time, across all applications. A command finishes, returns `Err` or traps before any other command starts. No scheduling, callback or lifecycle activity starts a command while another is active (HEP-13).
*Sources: D-049; DN §4.*

**PLT-5 [Agreed]** No execution context can observe the pending persistent state of an active transaction, other than the transaction itself. That covers other commands, lifecycle handlers and callbacks. How the platform guarantees this is platform-defined.
*Sources: D-208; DN §7.2; PN §5.*

## B.4 Request, response and reporting

**PLT-6 [Agreed]** For each invocation, the platform supplies the request and response as separate, non-overlapping regions, valid only for that invocation (HEP-7). The following are platform-defined:

- which received bytes form the request, including the treatment of transport or APDU headers;
- framing;
- the maximum request size and the response capacity;
- length negotiation.

The host can never pass a reference into card memory.
*Sources: D-384, D-385; DN §4.*

**PLT-7 [Agreed]** At the start of an invocation, the response region contains no data from another application and no data from the platform itself. Zero-filling the region is one way to meet this. Bytes left by an earlier command of the same application are permitted.
*Sources: D-441 (OI-41); DN §4.*

**PLT-8 [Agreed]** After a command returns `Ok(count)` with `count` at most the response length, the platform transmits exactly the first `count` bytes of the response. It transmits nothing after `Err`, after a trap, or for a count larger than the response length, which is `TRAP-RESPONSE-COUNT`. Transmission happens only after the command has finished (HEP-9, HEP-10).
*Sources: D-387, D-393; DN §4, §7.4.*

**PLT-9 [Agreed]** For every command that is not ended by a security reset or a loss of power (RTF-10), the platform reports to the host exactly one of four outcome categories: success, application error, platform error or trap. The host must always be able to tell them apart. For errors, it reports the code, keeping the application category separate from the platform category even when the codes are equal. How categories and codes are encoded is platform-defined, for example the response status word on a classical smart card or a transport envelope elsewhere. Encoding a trap as an error, or an error as a trap, does not conform.
*Sources: D-019, D-043, D-390; DN §4, §6.3; PN §5.*

**PLT-10 [Agreed]** The platform never discloses VM internals to the host as part of an outcome, such as stack contents, internal addresses or memory layout. Which diagnostics may be reported, including whether the trap kind is reported, is platform-defined. A reset or power loss may prevent any response.
*Sources: D-391; DN §4, §6.3.*

**PLT-11 [Agreed]** The meaning of a published `CardError` code never changes, and a retired code is never reused for a different error. Applications have the same obligation for their own codes (OUT-17).
*Sources: D-209, D-366; DN §6.3; PN §5.*

## B.5 Persistence, transactions and recovery

**PLT-12 [Agreed]** The platform implements atomic persistent assignment (STA-11). After any interruption and recovery, each persistent destination holds either its complete previous value or its complete new value. The storage mechanism is platform-defined.
*Sources: D-057, D-371, D-373; DN §7.1.*

**PLT-13 [Agreed]** The platform implements transactions (chapter 11), with these guarantees:

- pending writes become durable together at commit;
- a rollback restores all of them;
- after an interruption during a transaction or its commit, recovery exposes either the whole transaction or none of it;
- execution never continues after a failed commit.

Journaling, commit records and storage geometry are platform-defined.
*Sources: D-207, D-375, D-382; DN §7.2; PN §5.*

**PLT-14 [Agreed]** The platform classifies each commit failure:

- a failure it can contain is `TRAP-COMMIT`, after the transaction's pending writes have been rolled back;
- a failure that threatens integrity requires a security reset (PLT-19).

If recovery after an interruption cannot establish integrity, the platform fails closed. It never resumes execution with partial persistent state. The classification criteria are platform-defined.
*Sources: D-207; DN §7.2; PN §5.*

**PLT-15 [Agreed]** A target profile states its limits on the size of an atomic persistent assignment and on transaction capacity. An application whose persistent assignment exceeds the atomic size limit is rejected for that target (STA-13). A transaction that exceeds the capacity at runtime is `TRAP-TXN-CAPACITY` (TXN-16). The limit values are platform-defined.
*Sources: D-419 (OI-19), D-439 (OI-39), D-206; DN §7.4.*

**PLT-16 [Agreed]** The following are platform-defined:

- the physical layout of persistent state;
- how persistent state survives an application upgrade, including enum values and structure layouts, whose declaration order is not a stable encoding (TYP-9);
- schema migration;
- rollback protection;
- deletion of an application and its state.

The language exposes no representation, so these choices cannot be observed by a program, except through upgrade behavior that the platform documents.
*Sources: D-416 (OI-16), D-427 (OI-27), D-325; DN §3.11, §5; PN §3.*

**PLT-17 [Agreed]** An object API for large persistent data, such as data too big to hold in RAM, is future platform work. It is not part of this specification.
*Sources: D-009, D-417 (OI-17); DN §5.*

## B.6 Lifecycle and reset

**PLT-18 [Agreed]** The platform defines the following:

- the lifecycle events;
- the reserved name and signature of each lifecycle handler;
- when each handler runs, and in what order;
- whether a handler is required;
- what happens when a handler returns `Err` or traps, including whether the application becomes available;
- how an interrupted installation is handled, and how provisioning is made safe to repeat;
- for each transport binding, which events start and end a session (STA-4), including whether deselection or logical channels do.

The placeholder handlers `on_install` and `on_session_start` (STA-6) are used by this specification until a platform defines its own. A platform that replaces them must document the replacement. A platform must not run a lifecycle handler while a command is active (PLT-4).
*Sources: D-124, D-370, D-407 (OI-7), D-438 (OI-38), D-459 (OI-59); DN §3.9; PN §3.*

**PLT-19 [Agreed]** The platform may issue a security reset, and it must issue one after a fatal platform failure. A security reset clears all volatile state of every application, including session state. The platform performs secure cleanup, whose method is platform-defined. It ends every application's session, and session defaults are restored at the next session start (STA-4). A security reset is never reported to an application as an `Err`. A command it interrupts has no outcome. When the platform decides to issue a security reset is platform-defined.
*Sources: D-054, D-056, D-397, D-459 (OI-59); DN §6.4; PN §3.*

## B.7 Runtime-owned resources

**PLT-20 [Agreed]** Runtime-owned resources are named by application-chosen `u32` identifiers. Examples are keys and multi-step cryptographic operations.

- **Identifier space.** Each application has one identifier space, covering all resource kinds. Different applications may use the same numbers independently.
- **Zero.** Identifier `0` is invalid and never names a resource.
- **Names, not handles.** An identifier is a name. It is not an address, a reference or an authorization. Copying it copies only the number.
- **Lookup.** Every lookup is scoped to the calling application.

*Sources: D-125, D-126, D-202, D-204; DN §11.2; PN §2.*

**PLT-21 [Agreed]** No platform API uses an opaque or hidden-layout value type. APIs use the ordinary value types and the ordinary outcome and reference rules. Configuration structures and algorithm enums supplied by the platform have complete, visible declarations, and they follow the ordinary naming rules (NAM-14). The internal representation of runtime-owned objects is never exposed in application byte arrays. Serialized data that an API defines is ordinary data.
*Sources: D-201, D-319; DN §11.1; PN §2.*

**PLT-22 [Agreed]** Every resource operation validates the identifier's existence, kind, state and permissions within the calling application's space. The required outcomes are:

| Situation | Required outcome |
|---|---|
| Create with an unused identifier | Create the resource |
| Create with an existing identifier | `Err(CardError.AlreadyExists)`. The existing resource is never replaced |
| Use or delete with an unknown identifier | `Err(CardError.NotFound)` |
| Use with the wrong kind | `Err(CardError.WrongResourceType)` |
| Insufficient capacity | `Err(CardError.Capacity)` |
| Failed creation | No usable, partially created resource exists under the identifier |

After deletion, every copy of the identifier names nothing. Reusing the identifier makes all copies name the new resource. Stale handles are not detected.
*Sources: D-203, D-204; DN §11.2; PN §2.*

**PLT-23 [Agreed]** A trap does not clean up, delete or invalidate runtime-owned resources (RTF-2). Each resource operation defines the state it leaves on failure. What happens to resources at a session start, at security reset and when an application is deleted is platform-defined. A resource's lifetime is independent of the variables that hold its identifier.
*Sources: D-052, D-204; DN §6.4, §11.2; PN §2.*

**PLT-24 [Agreed]** Each platform API states its behavior inside a transaction. It either participates in the transaction (its effects commit and roll back with it), or is permitted but does not participate (its effects are immediate), or is not permitted. A call to a not-permitted API is rejected at compile time (TXN-17). Resource storage strategy, such as fixed slots, bounded pools or a heap, is platform-defined and needs no dynamic allocation in the language.
*Sources: D-205, D-440 (OI-40), D-127, D-420 (OI-20); DN §7.2, §11.2; PN §2, §5.*

## B.8 The platform API catalog

**PLT-25 [Agreed]** The platform supplies an *API catalog* to the build, alongside the source-file list. Its entries are the targets of `card.` paths (NAM-18). Each entry states:

1. its path, such as `card.crypto.hash_update`;
2. its parameters, in order, each with a mode and type (FUN-6);
3. its successful payload type, or no payload;
4. the `CardError` members it may return;
5. its transaction behavior (PLT-24);
6. the resource kinds it creates, uses or deletes, and the state it leaves on failure;
7. any permission it requires.

Calls are checked against the entry exactly as calls to ordinary functions are: argument count (CE-EXP-16), modes (CE-FUN-2) and types (CE-EXP-1). A path not in the catalog is CE-NAM-10. Platform APIs never call application code.
*Sources: D-406 (OI-6), D-443 (OI-43), D-201; DN §4.1, §11; PN §2.*

**PLT-26 [Agreed]** This specification defines no real platform API. The names in the notes, such as `card.resources.create` and `card.crypto.hash_update`, are illustrative. The conformance suite uses a *test-only catalog* (`language/conformance/platform/test-catalog.txt`) of fictional entries under `card.test.`. It exists only to test the language rules that depend on a catalog. Its entries are non-normative, and a platform need not provide them.
*Sources: D-443 (OI-43); DN §11.2; PN §2.*

### Conformance tests for catalog-dependent rules

These tests use the test-only catalog (PLT-26):

| Test | Exercises | Expected |
|---|---|---|
| `valid/plt-001-platform-call.card` | NAM-18, PLT-25 | ok |
| `valid/plt-002-immediate-api-in-transaction.card` | TXN-17, PLT-24 | ok |
| `invalid/plt-101-unknown-platform-path.card` | NAM-18 | CE-NAM-10 |
| `invalid/plt-102-wrong-argument-type.card` | PLT-25, EXP-47 | CE-EXP-1 |
| `invalid/plt-103-wrong-argument-count.card` | PLT-25, EXP-47 | CE-EXP-16 |
| `invalid/plt-104-missing-ref-mode.card` | PLT-25, FUN-7 | CE-FUN-2 |
| `invalid/plt-105-forbidden-in-transaction.card` | TXN-17 | CE-TXN-4 |
| `invalid/plt-106-forbidden-through-helper.card` | TXN-17 | CE-TXN-4 |
| `runtime/run-015-resource-identifiers/` | PLT-20, PLT-22 | scenario |
| `runtime/run-016-signer-application/` | DN §13 signer (skeleton to the API boundary) | scenario |

**PLT-30 [Agreed]** A *platform API* is an operation that depends on platform state or hardware, such as keys, randomness, cryptographic engines, runtime-owned resources or lifecycle. Every platform API:

- is reached only through a `card.` path listed in the catalog (PLT-25);
- may be absent from a platform;
- fails with `CardError` members;
- states its transaction behaviour (PLT-24).

An operation that the language provides as an intrinsic (EXP-52) is never also offered as a platform API.
*Sources: D-446 (OI-46); PN §1.*

## B.9 `CardError` and trap catalogs

**PLT-27 [Agreed]** A platform's `CardError` set includes at least the members this specification names:

- `Overflow`, `Underflow` and `DivisionByZero` (checked arithmetic, EXP-29);
- `ConversionRange` (`checked_convert`, EXP-33);
- `AlreadyExists`, `NotFound`, `WrongResourceType` and `Capacity` (resources, PLT-22).

Their numeric codes are nonzero `u16` values, chosen by the platform. A platform may add members.
*Sources: D-415 (OI-15), D-018, D-367; DN §6.3, §6.5; PN §2.*

**PLT-28 [Agreed]** A platform raises a trap of the kinds in RTF-4 exactly when the language rules require one, and raises no others for conforming programs. The kinds `NESTED-TXN`, `VM` and the stack case of `EXHAUSTED` are safety nets that an accepted program never triggers. How trap kinds are reported, if at all, is platform-defined (PLT-10).
*Sources: D-396, D-415 (OI-15), D-439 (OI-39), D-442 (OI-42); DN §6.4.*

## B.10 Target profiles

**PLT-29 [Agreed]** A *target profile* states the platform's limits, including:

- RAM available to an application;
- stack size;
- execution budget per command;
- transaction capacity;
- maximum atomic persistent assignment size;
- request and response sizes;
- number of installed applications.

An application that needs more than a profile provides is rejected for that profile at build or load time whenever the need is computable. That covers storage sizes (TYP-23), atomic assignment size (STA-13) and stack depth (RTF-7). Limits that are not computable trap at runtime: the execution budget (RTF-6) and transaction capacity (TXN-16). No limit may change the meaning of a program (RTF-8).
*Sources: D-206, D-442 (OI-42); DN §12; PN §4.*

## B.11 VM and implementation guidance (informative)

This section is informative. It records the platform notes' implementation ideas without making them requirements. All figures are unmeasured targets, not claims.

- **Execution model ideas:**
  - a small stack-based interpreter;
  - bytecode resident in flash;
  - bounded call frames and operand storage;
  - no general application heap or garbage collector;
  - one command executing at a time;
  - compiler resource reports.
- **By-value aggregates** occupy temporary application RAM, naturally in the callee's frame, for the duration of the call (D-133, D-421). A reference needs a small descriptor rather than a copy. Physical placement may change as long as the value semantics of chapter 8 are kept.
- **Size goals:** about 2 KiB for the VM plus a small application, about 8 KiB for a complete reference card, and a 4 KiB profile to investigate (D-135). The illustrative 4 KiB budget in PN §4 is:

| Component | Bytes |
|---|---:|
| VM control and bookkeeping | 128 |
| Operand stack and application frames | 768 |
| Application globals and working buffers | 768 |
| Command and response buffer | 512 |
| Storage and transaction workspace | 384 |
| Native stack and interrupt reserve | 768 |
| Cryptographic scratch | 768 |
| **Total** | **4096** |

Cryptographic implementations, storage geometry, transport and native stacks may need more. Session state that is kept between commands must be counted. A footprint must be measured before it is claimed.
*Sources: D-133, D-135, D-421 (OI-21); PN §4.*

## B.12 Platform-defined items (checklist)

A platform specification must document a choice for every item below. Each row points to the rule that leaves the choice to the platform.

<!-- B.12 table: every "platform-defined" reference in chapters 1–13 -->

| # | Rule | Item left to the platform |
|---|---|---|
| 1 | [NAM-18](03-program-structure-and-names.md) | The catalog, including which paths exist and what they denote, is platform-defined (Annex B). |
| 2 | [TYP-9](04-types.md) | Persistent layout, and its preservation across application upgrades, are platform-defined (Annex B). |
| 3 | [EXP-29](06-expressions.md) | The `CardError` member names are placeholders, and their codes are platform-defined (Annex B). |
| 4 | [OUT-19](09-outcomes-and-errors.md) | Its member names and codes are platform-defined (Annex B). |
| 5 | [STA-3](10-state-and-initialization.md) | Deleting persistent state, upgrading an application, and migrating persistent values between versions are platform-defined (Annex B). |
| 6 | [STA-4](10-state-and-initialization.md) | Which events start and end a session, including whether deselection or logical channels do, is platform-defined, per binding (Annex B). |
| 7 | [STA-13](10-state-and-initialization.md) | The limit values, and how the rejection is reported, are platform-defined (Annex B). |
| 8 | [TXN-14](11-transactions.md) | The mechanism the platform uses to provide this isolation is platform-defined (Annex B). |
| 9 | [TXN-16](11-transactions.md) | The limit values are platform-defined (Annex B). |
| 10 | [HEP-5](12-host-entry-point.md) | Which received bytes form the request is platform-defined (Annex B), including the treatment of transport or APDU headers. |
| 11 | [HEP-6](12-host-entry-point.md) | The capacity is platform-defined (Annex B). |
| 12 | [HEP-12](12-host-entry-point.md) | How the categories and codes are encoded for the host is platform-defined (Annex B): on a classical smart card it is the response status word, and other transports use their own envelope. |
| 13 | [RTF-4](13-runtime-failures.md) | The numeric codes for each kind, and how a kind is reported to the host if it is reported at all, are platform-defined (Annex B). |
| 14 | [RTF-6](13-runtime-failures.md) | How the budget is measured and its size are platform-defined (Annex B). |
| 15 | [RTF-9](13-runtime-failures.md) | How a platform decides to issue one, and how it cleans up securely, are platform-defined (Annex B). |
| 16 | [PLT-1](annex-B-platform-contract.md) | A platform conforms to this specification when it meets every `PLT` requirement in this annex, and its platform specification documents a choice for every platform-defined item in §B.12. |
| 17 | [PLT-3](annex-B-platform-contract.md) | How the host selects an application is platform-defined. |
| 18 | [PLT-5](annex-B-platform-contract.md) | How the platform guarantees this is platform-defined. |
| 19 | [PLT-6](annex-B-platform-contract.md) | The following are platform-defined: - which received bytes form the request, including the treatment of transport or APDU headers; - framing; - the maximum request size and the response capacity; - length negotiation. |
| 20 | [PLT-9](annex-B-platform-contract.md) | How categories and codes are encoded is platform-defined, for example the response status word on a classical smart card or a transport envelope elsewhere. |
| 21 | [PLT-10](annex-B-platform-contract.md) | Which diagnostics may be reported, including whether the trap kind is reported, is platform-defined. |
| 22 | [PLT-12](annex-B-platform-contract.md) | The storage mechanism is platform-defined. |
| 23 | [PLT-13](annex-B-platform-contract.md) | Journaling, commit records and storage geometry are platform-defined. |
| 24 | [PLT-14](annex-B-platform-contract.md) | The classification criteria are platform-defined. |
| 25 | [PLT-15](annex-B-platform-contract.md) | The limit values are platform-defined. |
| 26 | [PLT-16](annex-B-platform-contract.md) | The following are platform-defined: - the physical layout of persistent state; - how persistent state survives an application upgrade, including enum values and structure layouts, whose declaration order is not a stable encoding (TYP-9); - schema migration; - rollback protection; - deletion of an application and its state. |
| 27 | [PLT-19](annex-B-platform-contract.md) | The platform performs secure cleanup, whose method is platform-defined. |
| 28 | [PLT-19](annex-B-platform-contract.md) | When the platform decides to issue a security reset is platform-defined. |
| 29 | [PLT-23](annex-B-platform-contract.md) | What happens to resources at a session start, at security reset and when an application is deleted is platform-defined. |
| 30 | [PLT-24](annex-B-platform-contract.md) | Resource storage strategy, such as fixed slots, bounded pools or a heap, is platform-defined and needs no dynamic allocation in the language. |
| 31 | [PLT-28](annex-B-platform-contract.md) | How trap kinds are reported, if at all, is platform-defined (PLT-10). |
| 32 | [PLT-32](annex-B-platform-contract.md) | The level, and how it is evaluated, are platform-defined. |
| 33 | [PLT-35](annex-B-platform-contract.md) | How the memory is erased, and whether a platform erases more, are platform-defined. |

## B.13 Security expectations

These rules are obligations on a platform. They are not language rules, because time, power and faults are not observable in the language.

**PLT-31 [Agreed]** `equal` (EXP-53) and every cryptographic platform API execute in time that does not depend on secret data: key material, plaintext, MAC values, and the contents compared by `equal`. Time may depend on lengths and on public parameters.
*Sources: D-450 (OI-50).*

**PLT-32 [Agreed]** A platform protects application secrets against side-channel and fault-injection attacks, at the level stated in its target profile. The level, and how it is evaluated, are platform-defined.
*Sources: D-450 (OI-50).*

**PLT-33 [Agreed]** The secret or private material held in a key resource never appears in memory that an application can read, nor in any output. The only material of a key resource that an application can obtain is a public key, through an API that exports it explicitly. Values that an application computes or receives itself, including the results of key-agreement and key-derivation APIs, are application data. The application is responsible for erasing them, for example with `wipe` (STM-23).
*Sources: D-450 (OI-50), D-452 (OI-52).*

**PLT-34 [Agreed]** A platform performs every store of a `wipe` statement (STM-23), including on volatile memory about to be released. It keeps no other copy of the wiped values that an application or the host could recover.
*Sources: D-450 (OI-50), D-449 (OI-49).*

**PLT-35 [Agreed]** When a call frame ends, a platform erases the frame's local memory. This applies to every function, command and lifecycle handler, however the frame ends: `return`, `Err`, `attempt` propagation, `abort`, or a trap (RTF-1). No later code, application or host can recover the values its locals held. Applications therefore need `wipe` (STM-23) only for state that outlives a frame, such as session and persistent state, or to erase a local sooner. How the memory is erased, and whether a platform erases more, are platform-defined.
*Sources: D-458 (OI-58).*
