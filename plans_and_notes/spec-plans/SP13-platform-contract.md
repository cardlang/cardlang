# SP13 — Annex B, the platform contract: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Annex B is not written until you approve this plan.

## 1. Scope

Annex B is the layer boundary that chapter 1 set up. It states three kinds of content:

1. **`PLT-n` requirements:** what every conforming card platform must guarantee to CardLang programs. These are normative.
2. **Platform-defined items:** choices the language leaves to the platform. This is a checklist that a platform specification must answer.
3. **Informative VM and target-profile guidance:** the PN §4 material, which is not normative.

The annex does **not** design the platform. It does not invent APIs, status-word values, journaling schemes or capacities. Where the notes give an agreed direction, that direction becomes a `PLT` requirement. Where they give nothing, the item goes on the platform-defined list.

| Output | Content |
|---|---|
| `spec/annex-B-platform-contract.md` | The annex: about 30 `PLT` rules, the platform-defined checklist and the informative guidance |
| Test-only platform catalog (decision 1) | A small, clearly fictional API catalog used by conformance tests |
| Conformance tests | The deferred CE-TXN-4 test. Tests for platform-path resolution (NAM-18) and for argument checking against catalog signatures. A runtime scenario for the resource identifier model. The **signer application** up to the API boundary (DN §13, the third representative application) |
| `tools/` | Catalog support in the checker (`pltcheck.py`, extending `hepcheck`) and in the interpreter (test-catalog behaviour) |
| Register, Annex D, 00-index | Completes the 12 decisions still pending and the partial platform items |

## 2. Sources

- **PN:** §1 to §5, all of it.
- **DN:** §4 (the transport boundary), §6.3 (host reporting), §6.4 (platform failure and reset), §7.2 and §7.4 (journaling and capacities), §11 (runtime-owned resources), §12.

### Decisions now completed

| Decision | Topic |
|---|---|
| D-009 + D-417 | Object API for large data: future platform work |
| D-125, D-126, D-127 + D-420 | Resource identifiers, the identifier space, storage strategy |
| D-135 | VM size goals (informative) |
| D-201 to D-204 | No opaque types, runtime validation, resource outcomes, identifier copy semantics |
| D-421 | Call-frame placement (informative) |

### Partial decisions completed

| Decision | Topic |
|---|---|
| D-043 | Status-word mapping |
| D-052 | Resources on trap |
| D-056 | Fatal failure leads to a security reset |
| D-133 | By-value aggregate placement |
| D-205 | Resource effects in transactions |
| D-208 | Isolation mechanism |
| D-402 | No dispatch within an application; the PN §1 row is superseded |
| D-415 | Final `CardError` and trap names |
| D-416 | Deletion, upgrade and migration |
| D-441 | No foreign data in the response |

No new body decisions are expected. PN agreed items were already registered in SP0 as D-201 to D-209.

## 3. Planned structure of Annex B

| Section | Content (`PLT` requirements unless marked) |
|---|---|
| **B.1 Status and conformance** | A platform conforms when it meets every `PLT` rule and documents every platform-defined item |
| **B.2 Applications and dispatch** | One application, or several completely isolated ones (D-020). Application selection is platform-defined. Every request for an application goes to its single command, with no further dispatch (D-402, which supersedes the PN §1 row) |
| **B.3 Command execution and isolation** | Commands never interleave (D-049). No other execution context observes pending transactional state; the mechanism is platform-defined (D-208) |
| **B.4 Request, response and reporting** | Which received bytes form the request (framing, header treatment), maximum sizes and length negotiation are platform-defined. The platform transmits exactly `response[0..count)` after success. The response region never holds data from another application or from the platform (D-441). The four outcome categories stay distinguishable; their encoding, such as status-word values, is platform-defined (D-043, D-019). Codes are stable (D-209). No VM internals are disclosed |
| **B.5 Persistence and transactions** | Atomic persistent assignment survives interruption (STA-11). Transactions are all-or-nothing after recovery, and recovery fails closed (D-207). Journaling and storage geometry are platform-defined. The limit values for atomic-write size (D-419) and transaction capacity (D-439) are platform-defined. A commit failure is classified as contained (`TRAP-COMMIT`) or as an integrity failure (security reset). Persistent layout, upgrade, migration and deletion are platform-defined (D-416, D-427). The object API for large data is future work (D-417) |
| **B.6 Lifecycle** | Lifecycle events and handler names: the placeholders `on_install` and `on_power_on` are confirmed, or replaced and extended. Scheduling and order, handler failure, interrupted installation and repeat-safe provisioning are platform-defined. Session events beyond power-on and reset, such as deselection or channels, are platform-defined. The platform may issue a security reset, and a fatal failure requires one. Secure cleanup is a platform obligation (D-056) |
| **B.7 Runtime-owned resources** | The identifier model (D-125, D-126, D-201 to D-204). The required outcome for each resource operation (D-203), with error names from B.8. No cleanup on trap (D-052). Each API defines its transaction behaviour or is marked forbidden (D-205, D-440). Storage strategy is platform-defined (D-420). Typed handles are a possible future extension |
| **B.8 Platform API catalog** | What every catalog entry must state: path, parameters with modes and types, payload type, the `CardError` members it may return, whether it is permitted in a transaction and how its effects participate, which resource kinds it uses, and what state it leaves on failure. The catalog is supplied to the build like the source-file list. Unknown paths are CE-NAM-10 |
| **B.9 `CardError` and trap catalog** | The placeholder names are confirmed: `Overflow`, `Underflow`, `DivisionByZero`, `ConversionRange`, `AlreadyExists`, `NotFound`, `WrongResourceType`, `Capacity`, plus the 12 trap kinds. Codes and reporting are platform-defined. Platforms may add `CardError` members |
| **B.10 Target profiles** | A profile must state its limits: RAM, stack, execution budget, transaction capacity, atomic-write size, request and response sizes, number of installed applications. A program that exceeds a profile is rejected at build or load time where that is computable (TYP-23, STA-13, RTF-7). Otherwise the program traps. Limits never change semantics (D-206) |
| **B.11 VM guidance (informative)** | Stack interpreter and flash-resident bytecode ideas; call-frame placement of by-value aggregates (D-133, D-421); the 2, 4 and 8 KiB goals and the 4 KiB budget table as unmeasured targets (D-135); compiler resource reports |
| **B.12 Platform-defined checklist** | One table listing every "platform-defined" reference in chapters 1–13, with a link back to its rule. A platform specification must answer every row |

## 4. Decisions needed

**Decision 1 — OI-43: a test-only platform catalog.** Several rules depend on a platform API catalog that does not exist yet:

- NAM-18 (platform paths);
- TXN-17 (APIs forbidden in transactions);
- the resource model;
- the signer application.

The notes' example calls, such as `card.crypto.hash_update`, are explicitly illustrative and TBD. Defining real APIs here would be inventing them.

| Option | Description |
|---|---|
| (a) | Annex B defines only the catalog *entry requirements* (B.8). The conformance suite gets a **test-only catalog** of clearly fictional entries under `card.test.…`, such as `card.test.resources.create(id: u32, kind: u8)`, `delete(id: u32)` and `read(id: u32) -> u32`, plus one API marked forbidden in transactions. Every entry is labelled non-normative. The checkers and the interpreter load this catalog |
| (b) | No catalog at all. The platform-dependent tests stay deferred until a real catalog exists |

**Recommendation: (a).** It lets the language rules that depend on a catalog be tested without pretending to define the platform. The `card.test.` prefix makes the entries unmistakably fictional.

**Decision 2: the signer application.** DN §13 lists a signing application covering keys, permissions and security services. A real one needs real crypto APIs.

| Option | Description |
|---|---|
| (a) | Write it **up to the API boundary**, using the test-only catalog. It would have a key identifier as a `u32` constant, a PIN-guarded state machine, request parsing and response encoding, and fictional `card.test.sign…` calls. It is marked as a skeleton, pending a real catalog |
| (b) | Defer it until a platform catalog exists |

**Recommendation: (a).** This matches the plan of plans ("signer up to the platform-API boundary"), and it exercises the resource and identifier rules.

**Decided 2026-11-17.** You accepted both recommendations.

- **Decision 1 (OI-43) is (a)**, recorded as D-443. There will be a test-only catalog under `card.test.…`, clearly marked non-normative.
- **Decision 2 is (a).** The signer is written as a skeleton up to the API boundary. This is a tooling and test choice, so it gets no D-ID.

## 5. Conformance tests (about 8)

**Compile-time**

| Test | Checks | Expected |
|---|---|---|
| A known platform path called with the right arguments | NAM-18, B.8 | ok |
| An unknown `card.test.` path | NAM-18 | CE-NAM-10 |
| A wrong argument type for a catalog entry | EXP-47 | CE-EXP-1 |
| A wrong argument count | EXP-47 | CE-EXP-16 |
| A forbidden API called directly inside a transaction | TXN-17 | CE-TXN-4 |
| A forbidden API reached through a helper called in a transaction | TXN-17 | CE-TXN-4 |

**Runtime**

- **The resource identifier model.** Create, use, duplicate create (`AlreadyExists`), unknown (`NotFound`), wrong kind (`WrongResourceType`), delete, and use after delete (`NotFound`). Copying an identifier copies only the number.
- **The signer skeleton**, if decision 2 is (a): verify the PIN, sign with a key identifier (using the fictional API), and get `Unauthorized` without the PIN.

## 6. Steps

1. Record decisions 1 and 2 (OI-43; the signer choice is tooling and has no D-ID).
2. Write Annex B.
3. Write the test-only catalog (`conformance/platform/test-catalog.txt`) and its README note.
4. Write `tools/checkers/pltcheck.py`, which resolves `card.` paths, checks signatures and transaction permission, and extends `hepcheck`. Extend the interpreter with test-catalog behaviour.
5. Write the generator and the tests. Add them to `run_checks.py`.
6. Run all checks.
7. Complete the traceability: every pending and partial platform decision is covered.

## 7. Choices made in this sub-plan

These are open for redirection:

- **No platform design.** Annex B invents no status-word values, journaling designs or capacity numbers. Each of those is a checklist item for a platform specification.
- **The B.12 checklist is generated** by scanning chapters 1–13 for "platform-defined", so nothing is missed.
- **The VM material stays informative.** It is not promoted to requirements.
