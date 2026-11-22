# 12. Host entry point

CardLang Language Specification, Draft 0.2.

Every host request to an application enters through a single declaration: the application's `command`. This chapter defines:

- the `command` declaration and its fixed signature;
- the request and response views it receives;
- what the platform does with each outcome;
- how outcome categories are reported, from the language side;
- how commands execute.

How the application interprets request bytes, dispatches operations and encodes responses is application code (§12.6).

The following are platform-defined (Annex B):

- which received bytes form the request;
- framing, maximum sizes and length negotiation;
- status-word values;
- application selection;
- permissions.

## 12.1 The command declaration

```
CommandDeclaration ::= 'command' Identifier ParameterList ReturnType? Block   /* §A.2.1 */
```

**HEP-1** An application declares exactly one `command`. It is the application's *host entry point*. Its name is chosen by the application. Each of the following is an error:

- no `command` declaration: **CE-HEP-1**;
- more than one `command` declaration, across all source files: **CE-HEP-2**.

The command's name is in the application scope like any other top-level name (NAM-11).
*Sources: D-041, D-405 (OI-5); DN §4, §4.1.*

**HEP-2** The command's signature must be exactly:

```text
command name(p1: ref u8[], p2: inout u8[]) -> u32
```

That is, exactly two parameters, in this order:

1. a `ref u8[]` request;
2. an `inout u8[]` response.

The successful payload type is `u32`. The parameter names are chosen by the application. Any other signature is **CE-HEP-3**. That includes a different number of parameters, different modes or types, a missing return type, or a return type other than `u32`.
*Sources: D-041; DN §4.*

**HEP-3** Application code never calls the command. A call to it anywhere is **CE-EXP-15** (EXP-47), including from an ordinary function or a lifecycle handler. The command is a node of the call graph (FUN-5). Logic that the command shares with other code belongs in ordinary functions.
*Sources: D-035; DN §3.7, §4.1.*

**HEP-4** Apart from HEP-1 to HEP-3, the command body follows every ordinary rule:

- it must end with an explicit outcome (STM-21);
- an `attempt` whose call returns `Err` returns that error from the command to the host (OUT-10);
- it may contain transactions and `abort` (chapter 11).

Only the command can be called by the host. Ordinary functions, globals, constants and fields are never exposed to the host, even though they are visible throughout the application (NAM-13).
*Sources: D-035, D-041; DN §4.1.*

### Examples

*Valid:* the minimal entry point (DN §4). (conformance: `valid/hep-001-minimal.card`)

```text
command process(request: ref u8[], response: inout u8[]) -> u32 {
    return Ok(0);
}
```

*Valid:* an entry point with application-chosen command and parameter names. (conformance: `valid/hep-002-any-names.card`)

```text
command handle_apdu(input: ref u8[], output: inout u8[]) -> u32 {
    if input.length == 0 {
        return Ok(0);
    }
    output[0] = input[0];
    return Ok(1);
}
```

*Invalid:* each of these is in its own test.

| Fault | Class | Conformance |
|---|---|---|
| An application with no `command` | CE-HEP-1 | `invalid/hep-101-no-command.card` |
| Two `command` declarations | CE-HEP-2 | `invalid/hep-102-two-commands.card` |
| Return type `u16` | CE-HEP-3 | `invalid/hep-103-wrong-return-type.card` |
| No return type | CE-HEP-3 | `invalid/hep-104-no-return-type.card` |
| `request: inout u8[]` | CE-HEP-3 | `invalid/hep-105-inout-request.card` |
| `request: ref u8[16]` | CE-HEP-3 | `invalid/hep-106-fixed-size-request.card` |
| A third parameter | CE-HEP-3 | `invalid/hep-107-extra-parameter.card` |
| A function that calls the command (DN §3.7) | CE-EXP-15 | `invalid/hep-108-call-command.card` |

## 12.2 Request and response

**HEP-5** The first parameter, the *request*, is a read-only view of the bytes the host sent for this invocation. Its `.length` is the number of request bytes. Which received bytes form the request is platform-defined (Annex B), including the treatment of transport or APDU headers. The application cannot write the request.
*Sources: D-384; DN §4.*

**HEP-6** The second parameter, the *response*, is a read-write view of the output capacity for this invocation. Its `.length` is the number of bytes the application may produce. The capacity is platform-defined (Annex B).
*Sources: D-384; DN §4.*

**HEP-7** The platform supplies the request and response as separate regions that do not overlap. They are valid only while the command executes. The application cannot resize either one, and cannot keep a reference to either one beyond the invocation (FUN-16). The host can never pass a reference into card memory. The separation of the two regions belongs to this entry contract only. In general, references may overlap (FUN-13).
*Sources: D-385; DN §4.*

**HEP-8** The language promises nothing about the initial contents of the response region. The application must write every byte it includes in its returned count. The platform must ensure that the region never contains data from another application or from the platform itself (Annex B). Bytes left over from an earlier command of the same application are possible. Writing to the response transmits nothing (HEP-10).
*Sources: D-386, D-441 (OI-41); DN §4.*

## 12.3 The outcome contract

**HEP-9** When the command finishes, the platform acts on its outcome as follows:

| Outcome of the command | Platform action |
|---|---|
| `Ok(count)` with `count ≤ response.length` | Transmit exactly the first `count` bytes of the response, and report success |
| `Ok(count)` with `count > response.length` | `trap(RESPONSE-COUNT)`. No response payload is transmitted |
| `Err(e)` | No response payload is transmitted. Report `e`'s category and code (§12.4) |
| A trap | No response payload is transmitted. Report the trap category (§12.4) |

Bytes beyond `count` are never transmitted. A partially written response is never transmitted after `Err` or a trap. The returned `u32` is a byte count. It is never a status word.
*Sources: D-387, D-390; DN §4, §6.3.*

**HEP-10** Transmission happens only after the command has finished. Any transaction in the command has therefore already committed, or been rolled back, before anything is transmitted. Response transmission never happens inside a transaction. Assignments to the response are ordinary volatile writes: they are not transmissions and they are not persistent changes.
*Sources: D-393; DN §7.4.*

**HEP-11** `Ok(count)` means that a response was produced. It does not mean that the requested operation succeeded. An application may report a protocol-level failure in the response bytes with `Ok`, or as an `Err`. Choosing between them is part of the application's protocol.
*Sources: D-388; DN §4.*

### Examples

*Valid:* a protocol status encoded in the payload, and an `Err` for a request with no operation byte. (conformance: `valid/hep-004-protocol-status-in-payload.card`)

```text
errors AppError {
    UnsupportedOperation = 1;
}

const STATUS_OK: u8 = 0x00;
const STATUS_REJECTED: u8 = 0x01;

command process(request: ref u8[], response: inout u8[]) -> u32 {
    if request.length == 0 {
        return Err(AppError.UnsupportedOperation);
    }
    if request[0] == 0xFF {
        response[0] = STATUS_REJECTED;
        return Ok(1);
    }
    response[0] = STATUS_OK;
    return Ok(1);
}
```

## 12.4 Reporting categories

**HEP-12** The host can always distinguish four outcome categories:

| Category | Produced by |
|---|---|
| Success | `Ok(count)`, together with the transmitted bytes |
| Application error | `Err` of a member of the application's error set |
| Platform error | `Err` of a `CardError` member |
| Trap | An execution fault |

A trap is never reported as an `Err`, and an `Err` is never reported as a trap. An application error and a platform error with the same code remain distinguishable (OUT-18). How the categories and codes are encoded for the host is platform-defined (Annex B): on a classical smart card it is the response status word, and other transports use their own envelope. No VM details are disclosed to the host. A reset or power loss may prevent any response at all.
*Sources: D-019, D-043, D-390, D-391; DN §4, §6.3; PN §5.*

## 12.5 Command execution

**HEP-13** Commands never interleave. Each command completes, returns `Err`, or traps before any other command of any application starts. No scheduling, callback or lifecycle activity starts a command while another one is active. A security reset may interrupt a command (chapter 13).
*Sources: D-049; DN §4.*

**HEP-14** A trap ends only the current command. It does not make the device or the application unusable. After the trap has been handled, which includes rolling back any active transaction, later commands may run. Running commands one at a time does not make a command an implicit transaction: its persistent writes outside transactions are separately atomic (STA-11).
*Sources: D-392; DN §4.*

## 12.6 The application protocol

**HEP-15** These are application code, written with the ordinary features of the language:

- parsing request bytes;
- choosing the requested operation;
- encoding response bytes.

The compiler and runtime never serialize language values for the host. They never dispatch operation identifiers, and they never generate typed command bindings. Byte encoding is always explicit (EXP-38). Formats such as ASN.1, CBOR or a custom encoding are application choices. The platform delivers every request for the application to its single command and performs no further dispatch within the application.
*Sources: D-042, D-389, D-402 (OI-2); DN §4.*

### Examples

*Valid:* dispatch on the first request byte, with a `u32` result encoded big-endian. (conformance: `valid/hep-003-dispatch-and-encode.card`)

```text
errors AppError {
    UnsupportedOperation = 1;
    MalformedRequest = 2;
    ResponseTooSmall = 3;
}

persistent counter: u32;

function read_counter() -> u32 {
    return Ok(counter);
}

function write_u32(output: inout u8[], value: u32) -> u32 {
    require output.length >= 4 else AppError.ResponseTooSmall;
    var bytes: u8[4] = encode_be(value);
    for index: u32 in 0..4 {
        output[index] = bytes[index];
    }
    return Ok(4);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length >= 1 else AppError.MalformedRequest;
    var operation: u8 = request[0];
    if operation == 0x01 {
        var value: u32 = attempt read_counter();
        return write_u32(inout response, value);
    }
    return Err(AppError.UnsupportedOperation);
}
```

*Valid:* the **counter application**, the first of the three representative applications of DN §13. It has a read operation and an increment operation. The increment updates two persistent values in one transaction, and both operations reply with the counter as four big-endian bytes. (conformance: `valid/hep-005-counter-application.card`)

```text
errors CounterError {
    MalformedRequest = 1;
    UnsupportedOperation = 2;
    ResponseTooSmall = 3;
}

const OP_READ: u8 = 0x01;
const OP_INCREMENT: u8 = 0x02;

persistent counter: u32;
persistent increments: u32;

function encode_counter(output: inout u8[]) -> u32 {
    require output.length >= 4 else CounterError.ResponseTooSmall;
    var bytes: u8[4] = encode_be(counter);
    for index: u32 in 0..4 {
        output[index] = bytes[index];
    }
    return Ok(4);
}

function increment() {
    transaction {
        counter = counter + 1;
        increments = increments + 1;
    }
    return Ok();
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length == 1 else CounterError.MalformedRequest;
    var operation: u8 = request[0];
    if operation == OP_INCREMENT {
        attempt increment();
    } else if operation != OP_READ {
        return Err(CounterError.UnsupportedOperation);
    }
    return encode_counter(inout response);
}
```

When `counter` is at its maximum, an increment traps with `OVERFLOW` (EXP-23). The transaction then rolls back, and no response payload is sent. An application that must report this condition differently can use `checked_add`.

## 12.7 The conformance scaffold (informative)

**HEP-16** A conformance test with `kind: fragment` contains no `command`. The test harness completes it by adding this declaration, which satisfies HEP-1 and HEP-2:

```text
command scaffold_entry(request: ref u8[], response: inout u8[]) -> u32 {
    return Ok(0);
}
```

A fragment test must therefore not declare a `command`, and must not use the name `scaffold_entry`. Tests with `kind: application` are complete applications and get no scaffold.
*Sources: D-405 (OI-5); conformance/README.md.*

## 12.8 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-HEP-1** | The application declares no `command` | HEP-1 |
| **CE-HEP-2** | The application declares more than one `command` | HEP-1 |
| **CE-HEP-3** | The `command` signature is not `(ref u8[], inout u8[]) -> u32` | HEP-2 |

The trap kind `RESPONSE-COUNT` used in this chapter is a placeholder (D-415), cataloged in chapter 13.
