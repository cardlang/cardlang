# SP11 — Host entry point: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 12 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/12-host-entry-point.md` | The single `command` declaration and its fixed signature; the request and response views; the outcome contract (`Ok(count)`, `Err`, trap); the four reporting categories, from the language side; how commands execute (they never interleave); the boundary between the application protocol and the platform |
| `spec/annex-A-grammar.md` §A.2.10 | `CommandDeclaration` (already in §A.2.1), plus a note on its signature restriction |
| Conformance | The first `kind: application` tests: complete small applications, including a counter, the first of the DN §13 representative applications. Invalid entry-point tests |
| `conformance/README.md` | Restates the fragment scaffold, now citing the chapter 12 rules |
| `tools/checkers/hepcheck.py`, `tools/generators/sp11_tests.py` | The checker extends `txncheck`. It adds the scaffold to fragment tests and checks the entry-point rules on application tests |
| Register, Annex C, Annex D, 00-index | Body decisions D-384…, the new issue, coverage, and the CE-HEP index |

**Out of scope (Annex B):**

- Which received bytes form `request`, including APDU header treatment and framing.
- Maximum request size, response capacity and length negotiation.
- Status-word values and how outcome categories are encoded.
- Application selection.
- Permissions.

## 2. Sources

- **DN sections:** §3.7 (the command cannot be called), §4 (all of it, including the response status, the transport boundary and command execution), §4.1 (external access), §6.3 (host reporting), §7.4 (response timing), §12.
- **PN sections:** §1, §5.

| Decisions | Topic |
|---|---|
| D-035 | The command is not callable from application code |
| D-041 | Exactly one command with a fixed signature |
| D-042 | The application owns its protocol |
| D-043 | Status-word mapping is platform-defined (the platform side goes to SP13) |
| D-049 | Commands never interleave |
| D-019 | Reporting categories |
| D-402 | No dispatch within an application (OI-2) |
| D-405 | The entry point is the single `command`, with any name |

### 2.1 Body-only decisions to register (D-384…)

| ID | Decision | Source |
|---|---|---|
| D-384 | `request.length` is the number of bytes received. `response.length` is the output capacity | DN §4 |
| D-385 | The platform supplies separate, non-overlapping request and response regions, valid only for the invocation. The application cannot resize them, and the host cannot pass references into card memory | DN §4 |
| D-386 | The application must write every response byte it includes in the count. The contract promises no initial response contents | DN §4 |
| D-387 | Response data is transmitted only after the command completes successfully and its count has been validated. A count larger than `response.length` traps, and no payload is sent. After `Err` or a trap, no partial payload is sent. Bytes beyond the count are never sent | DN §4, §6.3 |
| D-388 | `Ok` means a response was produced, not that the business operation succeeded. Protocol failures may be encoded in the payload | DN §4 |
| D-389 | There is no automatic serialization of language values, and no automatic dispatch of operation identifiers | DN §4 |
| D-390 | The returned `u32` is a byte count, not a status word. Errors keep their category and code inside CardLang, and the platform maps them to the wire status | DN §4 |
| D-391 | A reset or power loss may prevent any response. No internal VM details are disclosed to the host | DN §4, §6.3 |
| D-392 | A trap ends only the current command. Later commands may run. Serial execution does not make a command an implicit transaction | DN §4 |
| D-393 | Response transmission never happens inside a transaction. Writes to the response buffer are ordinary volatile writes, not transmissions | DN §7.4 |

## 3. Planned rules (chapter 12)

**§12.1 The command declaration**

- **HEP-1** An application declares exactly one `command`, and it may have any name (D-405).
  - Zero commands is **CE-HEP-1**.
  - More than one is **CE-HEP-2**.
- **HEP-2** The signature must be exactly `(p1: ref u8[], p2: inout u8[]) -> u32`. The parameter names are free. Anything else is **CE-HEP-3**: wrong types, wrong modes, a different number of parameters, or a missing or different return type (D-041).
- **HEP-3** The command cannot be called from application code (CE-EXP-15, EXP-47). That includes ordinary functions and lifecycle handlers. It is a node in the call graph (FUN-5). Shared logic belongs in ordinary functions (D-035).
- **HEP-4** Apart from that, the command body follows all the ordinary rules:
  - it must end with an explicit outcome (STM-21);
  - an `attempt` that propagates `Err` reports that error to the host;
  - it may contain transactions and `abort`.

  Only the command is host-callable. Functions, globals and constants are never exposed to the host (NAM-13).

**§12.2 Request and response**

- **HEP-5** `request` is a read-only view of the request bytes. Its `.length` is the number of bytes received. Which bytes those are is platform-defined: header treatment and framing are in Annex B (D-384).
- **HEP-6** `response` is a read-write view of the output capacity. Its `.length` is the capacity (D-384).
- **HEP-7** The two regions are separate and do not overlap. They are valid only during the invocation, and they cannot be resized or retained. This is part of the entry contract; it is not exclusive borrowing in general (FUN-13) (D-385).
- **HEP-8** The application must write every byte it reports in the count. The initial contents of the response region are [→ OI-41] (D-386).

**§12.3 The outcome contract**

- **HEP-9** When the command completes, the platform acts on its outcome:

| Outcome | Platform behaviour |
|---|---|
| `Ok(count)` with `count ≤ response.length` | Transmits exactly `response[0..count]`, and reports success |
| `Ok(count)` with `count > response.length` | `trap(RESPONSE-COUNT)`. No payload is transmitted |
| `Err(e)` | No payload. The platform reports `e`'s category and code |
| A trap | No payload. The platform reports the trap category |

  (D-387, D-390.)
- **HEP-10** Transmission happens only after the command has completed. A transaction in the command has therefore already committed or rolled back. Assignments to `response` transmit nothing (D-393).
- **HEP-11** `Ok` means a response was produced. An application may encode a protocol-level failure in the payload and still return `Ok`, or it may return `Err` (D-388).

**§12.4 Reporting categories**

- **HEP-12** The host can always tell four outcome categories apart: success, application error, platform error, and trap. A trap is never reported as an `Err`, and the categories are never confused even when their codes are equal (OUT-18).
  - The encoding is platform-defined: the status word on classical smart cards, or a transport envelope elsewhere (Annex B).
  - No VM internals are disclosed.
  - A reset or power loss may prevent any response.

  (D-019, D-390, D-391, D-043.)

**§12.5 Command execution**

- **HEP-13** Commands never interleave. Each command completes, returns `Err` or traps before another one starts, and no scheduling or callback starts a command while one is active. A security reset may interrupt a command (chapter 13) (D-049).
- **HEP-14** A trap ends the current command only. After trap handling, including transaction rollback, later commands may run. Serial execution is not an implicit transaction (D-392).

**§12.6 Application protocol**

- **HEP-15** Parsing the request, dispatching operations and encoding the response are application code. The language never serializes values for the host and never dispatches operation identifiers. Byte encoding is always explicit (EXP-38). ASN.1, CBOR or custom formats are application choices (D-042, D-389, D-402).

**§12.7 The fragment scaffold**

- **HEP-16** This is informative and is also stated in the conformance README. A fragment test is completed by the scaffold `command scaffold_entry(request: ref u8[], response: inout u8[]) -> u32 { return Ok(0); }`, which satisfies HEP-1 and HEP-2.

**Error classes**

| Class | Meaning |
|---|---|
| CE-HEP-1 | No command |
| CE-HEP-2 | More than one command |
| CE-HEP-3 | Wrong command signature |

## 4. New open issue

| ID | Question | Options | Recommendation |
|---|---|---|---|
| **OI-41** Initial contents of the response region | DN §4 says "no initial response-buffer contents are promised". Left unspecified, a careless application could transmit stale bytes, for example from an earlier command or from another application sharing the physical buffer. What may those initial bytes be? | (a) The language promises a zero-filled response region at every entry. (b) Unspecified for the language, but Annex B requires that the region never contains data from another application or from the platform. Leftover bytes from the same application's earlier commands are possible. (c) Unspecified, with no requirement | (b). This keeps the notes' "no contents promised" for the language, and turns the cross-application leak into a platform security requirement. Zero-filling is one way to meet it. Option (a) is safer for applications, but it adds a cost to every command and it changes the notes' decision |

**Decided 2026-11-17.** You accepted the recommendation; it is recorded as D-441. HEP-8 becomes **[Agreed]**: the initial contents of the response region are unspecified for the language. Annex B gets a platform requirement (`PLT`) that the region never holds data from another application or from the platform.

## 5. Conformance tests (about 13)

**Valid, `kind: application`**

| Test | Shows |
|---|---|
| The minimal entry point (DN §4) | |
| Any command name and parameter names | |
| Dispatch on `request[0]` to helpers, encoding a `u32` into `response` with `encode_be` | |
| A protocol status in the payload together with `Err` for an unsupported operation | HEP-11 |
| **Counter application** (DN §13, the first representative app) | Persistent counter; an increment operation inside a transaction; a read operation; the response encoded big-endian |

**Invalid**

| Test | Expected |
|---|---|
| No command (`kind: application`) | CE-HEP-1 |
| Two commands | CE-HEP-2 |
| Return type `u16` | CE-HEP-3 |
| No return type | CE-HEP-3 |
| `inout` request | CE-HEP-3 |
| A fixed-size `ref u8[16]` request | CE-HEP-3 |
| An extra parameter | CE-HEP-3 |
| A function calling the command (DN §3.7) | CE-EXP-15 |

**Runtime tests**, listed now and written in SP12:

- `count > length` traps;
- `Err` and traps suppress the payload;
- exactly `count` bytes are transmitted;
- the counter application's behaviour across commands.

## 6. Steps

1. Register D-384…D-393. Record OI-41.
2. Write chapter 12.
3. Add §A.2.10.
4. Update the conformance README.
5. Write the generator and the tests.
6. Write `hepcheck.py`: add the scaffold to fragments, count commands, check the signature, and reject calls to the command. Make it the full-chain checker in `run_checks.py`.
7. Run all checks, including every existing fragment test with the scaffold added.
8. Update the traceability. This completes D-035, D-041, D-042, D-049 and D-405, and part of D-019 and D-043.

## 7. Choices made in this sub-plan

These are open for redirection:

- Separate classes for "no command" (CE-HEP-1) and "more than one command" (CE-HEP-2).
- Calling the command reuses CE-EXP-15.
- The counter application is included here as the first complete application. The wallet waits until SP12, and the signer needs Annex B's API catalog (SP13).
