# The CardLang Guide

CardLang is a small, statically typed language for writing secure applications that run isolated on small devices: trusted applications on microcontrollers, in a TrustZone secure world or a partition isolated by the memory protection unit, and smart-card applets. This guide calls them all *applets*, and teaches you to write them.

It assumes you have programmed before, in C, Python, Java or something similar. You don't need to know embedded or security programming: the guide explains what matters as it comes up.

## A first look

Here is a whole applet: a counter that a host can read and increment, and that keeps its value when the device loses power.

<!-- check: program counter -->
```cardlang
errors CounterError {
    MalformedRequest = 1;
    UnsupportedOperation = 2;
    ResponseTooSmall = 3;
}

const OP_READ: u8 = 0x01;
const OP_INCREMENT: u8 = 0x02;

persistent counter: u32;

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length == 1 else CounterError.MalformedRequest;
    require response.length >= 4 else CounterError.ResponseTooSmall;
    var operation: u8 = request[0];
    if operation == OP_READ {
        response[0..4] = encode_be(counter);
    } else if operation == OP_INCREMENT {
        counter = counter + 1;
        response[0..4] = encode_be(counter);
    } else {
        return Err(CounterError.UnsupportedOperation);
    }
    return Ok(4);
}
```

A host talks to it one request at a time. This *scenario* plays the host: it installs the applet, sends requests, and states the responses it expects.

<!-- check: scenario counter -->
```scenario
install
power_on
command 01              # read: the counter starts at zero
expect ok 00 00 00 00
command 02              # increment
expect ok 00 00 00 01
command 07              # an operation the counter does not know
expect err app 2
```

Every example in this guide is checked like this one, so you can trust that it compiles and does what the text says. The compiler also catches mistakes before a program ever runs. Mixing two different operators without parentheses, for example, is an error:

<!-- check: error CE-EXP-4 -->
```cardlang
const MIXED: u32 = 1 + 2 * 3;
```

## How the guide is organised

The chapters build one applet, the *vault*: a small store for a secret, protected by a PIN, from a few lines to a complete program.

1. [Getting started](01-getting-started.md): install the tools, then build, run and debug your first applet.
2. [Values and types](02-values-and-types.md): integers without implicit conversion, arrays and slices, structures, enums, and default values.
3. [Control flow and scope](03-control-flow-and-scope.md): statements, loops, scope, and how an applet's files fit together.
4. [Functions, references and views](04-functions-references-views.md): parameters, and references that cannot outlive a call.
5. [Outcomes](05-outcomes.md): `Ok` and `Err` instead of exceptions, and how errors differ from traps.
6. [State that survives](06-state.md): persistent and session state, atomic writes, and transactions.
7. [Talking to the host](07-host.md): the raw and ISO 7816 bindings, and status words.
8. [Using the platform](08-platform.md): keys, signatures, randomness, and wiping secrets.
9. [Testing and debugging](09-testing-and-debugging.md): scenarios as tests, and the debugger.
10. [A real applet](10-a-real-applet.md): a guided reading of a FIDO2 authenticator.
11. [Coming from C or Java Card](11-coming-from-c.md): what is different, and why.

The [platform reference](reference-platform.md) lists every API of the platform, its types, its errors and the kinds of trap.

## Where to start

- **New to CardLang:** start with [chapter 1](01-getting-started.md), and read in order. Each chapter builds on the ones before.
- **Coming from C or Java Card,** and want the differences first: read [chapter 11](11-coming-from-c.md), then go back to chapter 1.
- **Looking up an API, an error or a trap kind:** go to the [platform reference](reference-platform.md).
- **Looking for an exact rule:** go to the [specification](https://github.com/cardlang/cardlang/blob/main/language/spec/00-index.md).

The guide explains; the [specification](https://github.com/cardlang/cardlang/blob/main/language/spec/00-index.md) decides. When the guide relies on a rule, it names it, as in *EXP-14*, so you can look up the exact wording. Where the two seem to disagree, the specification is right, and the guide has a bug.
