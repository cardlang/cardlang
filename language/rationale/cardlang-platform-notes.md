# CardLang: card platform and runtime notes

Date: 2026-11-14
Status: short companion to the language design notes; agreed directions and deferred platform work, not a complete platform specification.

## 1. Language/platform boundary

The language describes program behavior. The card platform supplies hardware integration, external interfaces, lifecycle events and concrete capacities.

| Language contract | Platform responsibility |
| --- | --- |
| `command` identifies a host-callable entry point | Dispatch, command identifiers, transport and request/response encoding |
| `session` is volatile application state | Session creation/clearing events, reset, power-on and deselection behavior |
| `persistent` survives ordinary resets | Durable storage, recovery and application-state management |
| Persistent assignment is atomic; explicit transactions group writes | Journaling/commit implementation, capacity and power-loss recovery |
| Results and traps have different semantics | External status mapping, diagnostics and service-specific error codes |
| Bounds, arithmetic and reference rules hold at runtime | VM verification, enforcement, target ABI and resource accounting |

Applications are single or completely isolated: no cross-application calls, references, shared application data or error propagation. Each uses its own state and permitted platform services. Platform permissions and supported APIs remain to be designed.

## 2. Runtime-owned resources: agreed interface direction

Resources such as keys and multi-step cryptographic operations are runtime-owned objects named by application-chosen `u32` identifiers. No new handle, pointer, class or opaque resource type is required in CardLang.

### API types and runtime validation

The initial language has no opaque platform value types or hidden-layout `KeyHandle`/`HashContext` declarations. APIs use ordinary supported value types and the existing result/reference rules. The platform supplies complete visible definitions for configuration structures and algorithm enums; these use existing naming rules without introducing imports, namespaces or private fields.

Resource identifiers are ordinary integers. Passing one does not transfer ownership, comparing one uses ordinary integer comparison, and no compile-time distinction separates key names from operation names. Every runtime resource operation must validate existence, kind, state and permissions in the calling application's resource space. A wrong resource kind produces a defined recoverable error. Identifiers never authorize cross-application access.

Object contents and layouts remain runtime-owned. Applications do not reserve byte arrays to hold hidden key or operation representations. Byte arrays carry defined data such as messages, signatures and encoded public keys; any serialized format must be explicitly specified by its API. Typed resource handles are a possible future extension, not an initial requirement.

### Resource naming and lifetime

```text
const SIGNING_KEY: u32 = 1;
const HASH_OPERATION: u32 = 2;
```

- Reserve identifier `0` as invalid; a default-zero variable does not accidentally name a resource.
- Each application has one identifier space covering all resource kinds. Different applications may reuse numbers.
- Lookup is always scoped to the caller. An identifier is a name, not an address, borrowing reference or authorization token.
- The runtime owns the object's representation and validates kind, state and permissions for each operation.

Illustrative APIs only; configuration types, names, signatures and error codes are TBD:

```text
attempt card.resources.create(HASH_OPERATION, configuration);
attempt card.crypto.hash_update(HASH_OPERATION, ref message);
attempt card.resources.delete(HASH_OPERATION);
```

| Operation/condition | Required behavior |
| --- | --- |
| Create unused identifier | Create requested resource |
| Create existing identifier | Recoverable AlreadyExists error; never silently replace |
| Use unknown identifier | Recoverable NotFound error |
| Use incompatible kind | Recoverable WrongResourceType error |
| Delete existing resource | Remove it under defined cleanup rules |
| Delete unknown identifier | Recoverable NotFound error |
| Insufficient capacity | Defined recoverable capacity error |

Error names above are descriptive placeholders. Failed creation must not expose a usable partially created object under that identifier. Interruption/recovery rules still need a platform specification.

Copying a resource identifier copies only a number, never its object. After deletion every copy names a nonexistent object. Reusing the number makes all copies name the replacement: there is no stale-handle detection in this naming model.

The identifier variable's lifetime is independent of the resource's lifetime. A constant may name a durable key. A persistent variable containing an ID does not make a volatile context durable. Returning from a function does not delete a resource identified by a local variable.

Creation/deletion and operation APIs return ordinary outcomes handled by match, attempt or forwarding returns. Error returns do not automatically delete prior resources. Cleanup after traps, session teardown and resets must be defined by the platform. Language transactions do not automatically specify rollback of resource-API effects; each API must define participation or prohibit use during an active transaction.

Storage strategy remains open: fixed application-declared slots, bounded pools or a heap can support this interface. The API does not require dynamic allocation. Algorithms, key roles, ECC curves, object sizes, persistence policies, enumeration, capacities and cleanup are platform decisions. Earlier typed-handle/opaque-inline-object proposals are superseded by this identifier interface.

## 3. Lifecycle, initialization and upgrades

Mutable globals have no declaration initializers. New persistent state and newly created/cleared session state receive recursive zero/false defaults. Persistent state is not defaulted again on every reset. Applications perform nondefault setup in platform lifecycle handlers, such as installation or power-on handlers.

Still to specify:

- Handler names/signatures, registration and execution order.
- Installation activation, interrupted installation and repeat-safe provisioning.
- Power-on versus reset events; session/channel ownership and clearing events.
- Command availability when setup returns an error or traps.
- Application replacement, versioning, durable schema migration, rollback protection and deletion.

An ordinary language/VM trap preserves session state and discards terminated frames; it does not trigger a lifecycle reset. Fatal platform failure triggers a whole-chip security reset clearing volatile state. Secure cleanup, persistent recovery and fail-closed behavior after failed recovery belong here. Language atomicity promises must survive the chosen recovery mechanism.

## 4. VM, capacities and implementation targets

Concrete RAM, stack, execution budgets, transaction capacity and installed-application counts belong to target profiles. Exceeding a runtime stack/execution limit traps; exceeding supported build/load capacity may reject an application. Limits must not silently change language semantics, such as replacing value copies with shared references.

Implementation ideas remain proposals: a small stack-based interpreter, flash-resident bytecode, bounded call frames/operand storage, no general application heap or garbage collector, one executing command at a time, and compiler resource reports. Exact bytecode, native ABI, verification and dynamic resource allocation strategy are not settled.

Earlier unmeasured goals were 2 KiB for VM plus a representative small application, 8 KiB for a complete reference card, and investigation of a 4 KiB profile. These are targets, not measured footprints. The illustrative 4 KiB budget was:

| Component | Bytes |
| --- | ---: |
| VM control/bookkeeping | 128 |
| Operand stack/application frames | 768 |
| Application globals/working buffers | 768 |
| Command/response buffer | 512 |
| Storage/transaction workspace | 384 |
| Native stack/interrupt reserve | 768 |
| Cryptographic scratch | 768 |
| Total | 4096 |

Cryptographic implementations, storage geometry, transport and native stacks may require more. Retained session state must be counted. Caller-owned copies are temporary application RAM; references use descriptors. Enforcement and measurements are required before claiming a footprint.

## 5. External behavior and next platform work

### Transaction execution, commit and recovery

The language commits an explicit transaction on successful completion of its closing brace. Reads within the transaction see earlier writes, including through references and ordinary helper calls. Persistent application writes commit or roll back together; volatile state and runtime-owned resource effects do not automatically participate. Each service must explicitly define participation, externally visible effects and permitted use during a transaction, or prohibit such use.

The platform must prevent another execution context, including callbacks or reentrant commands, from observing partially updated transactional state. Scheduling, serialization, callback restrictions and other isolation mechanisms remain to be specified; this requirement does not choose a particular mechanism.

Commit failure must never allow execution to resume after the block as though it succeeded. A safely contained failure terminates the command with a trap; an integrity failure triggers whole-chip security-reset handling. Durable recovery after interruption must expose either the complete transaction or none of it, never a partial commit. If integrity cannot be established, recovery must fail closed rather than resume with partial state. Journaling, commit records, storage geometry and classification of failures remain platform work.

Transaction capacity, atomic-write limits, host I/O and response timing relative to durable commit still require platform rules. Returning Err does not abort a transaction, and an ordinary trap preserves session state while rolling back the active transaction's persistent changes. Fatal platform failure clears volatile state through the security reset.

### Host reporting and next work

Host reporting distinguishes success, application error, recoverable platform error and trap. Application/platform error codes are nonzero u16 values in separate categories; published code meanings remain stable. Exact wire encoding and permitted diagnostics remain open. Power loss or reset may prevent a response.

Next work: define the API/resource catalogs and lifetimes, lifecycle callbacks, command ABI/permissions, persistent/resource recovery, transaction service restrictions, target profiles and VM format. These are not reasons to enlarge the language's type or module systems prematurely.
