# The CardLang Guide

CardLang is a small, statically typed language for secure applications that run isolated on small devices. Think of a trusted application on a microcontroller, code in a TrustZone secure world or in a partition walled off by the memory protection unit, or a smart-card applet. This guide calls all of them *applets*, and shows you how to write one.

You'll need to have programmed before, in C, Python, Java or something like them. Embedded or security experience isn't required, and the guide explains what matters when it comes up.

## A first look

This is a complete applet. It keeps a counter that a host can read and increment, and the counter survives when the device loses power.

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

A host talks to the applet one request at a time. To try it without a device, you write a *scenario*, which plays the host. This one installs the applet, sends three requests and says what each answer should be.

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

Every example in the guide is checked this way, so it compiles and behaves as the text says it does. Many mistakes never get as far as running. The compiler rejects this line, for instance, because it mixes two operators without parentheses:

<!-- check: error CE-EXP-4 -->
```cardlang title="Does not compile: CE-EXP-4"
const MIXED: u32 = 1 + 2 * 3;
```

## How the guide is organised

Over the chapters you build one applet, the *vault*, a small PIN-protected store for a secret. It starts as a few lines and ends as a complete program.

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

After the chapters comes the [platform reference](reference-platform.md), with every API of the platform, its types, its errors and the kinds of trap.

## Where to start

If CardLang is new to you, start with [chapter 1](01-getting-started.md) and read the chapters in order, since each one builds on the last. Readers who know C or Java Card may prefer to begin with [chapter 11](11-coming-from-c.md), which lists the differences, and then go back to chapter 1. To look up an API, an error or a trap kind, use the [platform reference](reference-platform.md).

The guide explains the language, and the [specification](https://github.com/cardlang/cardlang/blob/main/language/spec/00-index.md) defines it. Whenever the guide relies on a rule, it gives the rule's name, such as *EXP-2*, so you can look up the exact wording. If the two ever seem to disagree, trust the specification, and treat it as a bug in the guide.
