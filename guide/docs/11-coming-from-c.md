# 11. Coming from C or Java Card

Most secure applets today are written in C, for microcontrollers and TrustZone, or in Java Card, for smart cards. If you know either of them, this chapter maps what you already know onto CardLang. For each topic you'll see the familiar way briefly, then CardLang's way, and why it differs.

## At a glance

| Topic | C | Java Card | CardLang |
|---|---|---|---|
| Memory | Stack, static, and perhaps a heap | Objects in persistent memory, usually created at installation | Fixed sizes only. The compiler knows every byte the applet can use |
| Errors | Return codes, `errno` | Exceptions, such as `ISOException` | Outcomes, `Ok` or `Err`, which must be handled |
| Integer overflow | Wraps (unsigned), undefined (signed) | Wraps silently | A trap, unless you ask for wrapping or checking |
| Conversions | Implicit, in both directions | Implicit widening; casts to narrow | None implicit |
| Operator precedence | 15 levels | Java's levels | None: different operators need parentheses |
| Pointers | Raw pointers, null | References, null | `ref` and `inout`, for the length of a call; no null |
| Recursion | Allowed | Allowed | Not allowed: the stack need is known when building |
| Persistent data | Flash drivers and journaling, by hand | Fields of persistent objects; `JCSystem` transactions | `persistent` globals; atomic writes; `transaction` blocks |
| Session data | RAM, set up at reset | Transient arrays | `session` globals |
| Entry point | A function the host calls | `process(APDU)` | `command process(request, response)` |

## Memory

In C, a buffer is a local, a global, or something you `malloc`, and `malloc` can fail. In Java Card every object is created with `new`, in persistent memory. Writing persistent memory is slow and garbage collection is expensive, so applets normally create their objects once, at installation:

```java
private byte[] buffer;

private VaultApplet() {
    buffer = new byte[64];      // allocated once, in persistent memory
}
```

In CardLang every value's size is fixed when the applet is built, and nothing is allocated at all:

<!-- check: fragment -->
```cardlang
persistent buffer: u8[64];

function example() -> u8 {
    var scratch: u8[16];
    scratch[0] = buffer[0];
    return Ok(scratch[0]);
}
```

An applet that can't allocate can't run out of memory halfway through a command. With no recursion either, the compiler works out exactly how much stack and storage the applet needs, as you saw in [chapter 9](09-testing-and-debugging.md#inside-the-image), and a device either has room for it or refuses it at installation.

## Errors

In C an error is a return value, and nothing forces the caller to look at it:

```c
if (len != PIN_LENGTH) return ERR_LENGTH;
...
verify_pin(pin, len);           /* the result is silently ignored */
```

In Java Card an error is an exception. It jumps to whatever handler is further up the stack, or to the platform, which turns it into a status word:

```java
if (len != PIN_LENGTH) ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
```

In CardLang every call returns an outcome, and the compiler insists that you handle each one ([chapter 5](05-outcomes.md)). The mistake in the C code above won't compile:

<!-- check: error CE-OUT-1 -->
```cardlang
errors VaultError {
    WrongLength = 1;
}

session verified: bool;

function verify_pin(pin: ref u8[]) {
    require pin.length == 4 else VaultError.WrongLength;
    return Ok();
}

function unlock(pin: ref u8[]) {
    verify_pin(ref pin);                        // does not compile: the outcome is ignored
    verified = true;
    return Ok();
}
```

The caller has to say what happens on failure. Here `attempt` passes the error on, so `verified` is only set once the PIN has been checked:

<!-- check: fragment -->
```cardlang
errors VaultError {
    WrongLength = 1;
}

session verified: bool;

function verify_pin(pin: ref u8[]) {
    require pin.length == 4 else VaultError.WrongLength;
    return Ok();
}

function unlock(pin: ref u8[]) {
    attempt verify_pin(ref pin);
    verified = true;
    return Ok();
}
```

`match`, a forwarding `return` and an explicit `ignore` are the other ways to handle it. In a security applet an unhandled failure is a vulnerability. With outcomes, every way a call can fail is visible where the call is written, and an error can't skip past code that needed to run.

## Integers and conversions

In C, unsigned arithmetic wraps without a word, signed overflow is undefined, and conversions happen implicitly:

```c
uint8_t a = 250, b = 10;
uint8_t sum = a + b;            /* 4 */
```

In Java Card `byte` is signed, arithmetic on `short` gives an `int` that has to be cast back, and overflow wraps:

```java
short total = (short) (a + b);
short unsigned = (short) (buffer[i] & 0xFF);   /* bytes are signed */
```

In CardLang the types are the ones you mean, `u8` is unsigned, and nothing converts or wraps unless you ask for it ([chapter 2](02-values-and-types.md#integers)):

<!-- check: fragment -->
```cardlang
function example(a: u8, b: u8, large: u32) -> u32 {
    var wrapped: u8 = wrapping_add(a, b);       // wraps, because you said so
    var widened: u32 = convert<u32>(a);         // always fits
    var low: u8 = truncate<u8>(large);          // drops the high bits, because you said so
    return Ok(widened + convert<u32>(wrapped) + convert<u32>(low));
}
```

A plain `a + b` that doesn't fit traps, and `checked_add` returns an error instead. This matters because buffer overflows usually start with arithmetic on lengths, offsets and counters. A silent wrap turns a bad length into a small, plausible-looking one, while a trap stops the command.

## Operator precedence

C and Java share a classic bug:

```c
if (flags & MASK == 0) { ... }  /* means flags & (MASK == 0) */
```

CardLang has no precedence, and two different operators always need parentheses ([chapter 2](02-values-and-types.md#constants)). So the same line doesn't compile:

<!-- check: error CE-EXP-4 -->
```cardlang
const MASK: u8 = 0x0F;

function is_clear(flags: u8) -> bool {
    return Ok(flags & MASK == 0);               // does not compile: & and == are mixed
}
```

You write the grouping you mean, and whoever reads the code sees it too:

<!-- check: fragment -->
```cardlang
const MASK: u8 = 0x0F;

function is_clear(flags: u8) -> bool {
    return Ok((flags & MASK) == 0);
}
```

Nobody remembers fifteen levels of precedence, and a reviewer shouldn't have to.

## Pointers and references

In C a pointer can be null, can outlive what it points to, and can be pushed past the end of a buffer. In Java Card a reference can be null, and while array indexes are checked, a reference can be stored anywhere.

In CardLang, `ref` and `inout` give a function access to its caller's data for the length of the call and no longer ([chapter 4](04-functions-references-views.md#parameter-modes)). They can't be stored, returned or null, and every index is checked. A view type can't even be declared anywhere except as a parameter:

<!-- check: error CE-TYP-5 -->
```cardlang
struct Request {
    data: u8[];                                 // does not compile: a view cannot be stored
}
```

Because references are never stored, none of them can dangle, and the compiler can see every access to a piece of data in the calls that pass it along.

## Recursion and the stack

C and Java both allow recursion, and on a device with a few kilobytes of stack, a deep recursion overflows at runtime. CardLang rejects any cycle in the call graph:

<!-- check: error CE-FUN-1 -->
```cardlang
function walk(depth: u32) {
    if depth > 0 {
        attempt walk(depth - 1);                // does not compile: walk calls itself
    }
    return Ok();
}
```

Without recursion, the deepest possible chain of calls is known, and so is the stack it needs. A stack overflow becomes impossible rather than just unlikely.

## Persistence and atomicity

In C, keeping data across power loss means writing it to flash yourself, and making an update of several parts safe means writing a journal or double-buffering by hand.

In Java Card the fields of applet objects are persistent, updating a single field is atomic, and a transaction groups several updates:

```java
JCSystem.beginTransaction();
Util.arrayCopy(buffer, offset, pin, (short) 0, length);
pinLength = length;
JCSystem.commitTransaction();
```

A forgotten `commitTransaction`, an exception that escapes, or a nested `beginTransaction` only shows up at runtime.

In CardLang the persistent state is the `persistent` globals, every assignment to one of them is atomic, and a `transaction` is a block ([chapter 6](06-state.md#transactions)):

<!-- check: fragment -->
```cardlang
persistent pin: u8[8];
persistent pin_length: u32;

function store_pin(new_pin: ref u8[]) {
    transaction {
        pin = fill(0);
        pin[0..new_pin.length] = new_pin;
        pin_length = new_pin.length;
    }
    return Ok();
}
```

The block commits at its closing brace, so there's nothing to forget. Returning from the middle of a transaction is a compile error, and so is nesting one transaction inside another, even through a called function. Atomicity is what keeps a PIN counter honest when the power is cut, and it shouldn't depend on remembering to call a library correctly on every path.

## Session state

In Java Card, data that has to be cleared on deselection or reset lives in a *transient* array, so even a single flag becomes an array:

```java
private final boolean[] verified =
    JCSystem.makeTransientBooleanArray((short) 1, JCSystem.CLEAR_ON_DESELECT);
...
verified[0] = true;
```

In C it lives in RAM, and your startup code has to clear it at the right moments. In CardLang it's a declaration ([chapter 6](06-state.md#four-kinds-of-storage)), and the platform resets it to its default at every session start:

<!-- check: fragment -->
```cardlang
session verified: bool;
```

## The entry point

A Java Card applet receives the APDU buffer and does part of the transport's work itself:

```java
public void process(APDU apdu) {
    if (selectingApplet()) return;
    byte[] buf = apdu.getBuffer();
    switch (buf[ISO7816.OFFSET_INS]) {
        case INS_VERIFY:
            short length = apdu.setIncomingAndReceive();
            verify(buf, ISO7816.OFFSET_CDATA, length);
            break;
        default:
            ISOException.throwIt(ISO7816.SW_INS_NOT_SUPPORTED);
    }
}
```

A trusted application in C is usually a function the host calls with pointers into shared memory, and it has to check every one of them before using it.

A CardLang applet receives the whole request, already reassembled, as a read-only view, along with a response view to write into ([chapter 7](07-host.md)). It returns the number of bytes it wrote, or an error. SELECT, chaining, long responses and status words are all the platform's job, and every access to the request or the response is checked against its bounds.

## What CardLang leaves out

| Left out | Because |
|---|---|
| A heap, `new`, garbage collection | Memory needs must be known before the applet runs |
| Classes, inheritance, interfaces, function pointers | Every call names its target, so the call graph and the stack are known |
| Exceptions | Failures are outcomes, handled where they happen |
| Recursion | The stack need is computed, not guessed |
| Strings and floating point | Applets handle bytes and integers; text is bytes |
| Implicit conversions, operator precedence | Arithmetic should mean exactly what it says |
| A preprocessor, macros, generics | What you read is what runs |
| Undefined behaviour | Every operation either has a defined result, or traps |

Every item on that list makes CardLang smaller than the language you're used to. In exchange you get a small applet whose memory, stack and failure behaviour are known before it runs, and which a reviewer can check line by line.

## Where to go from here

The [specification](https://github.com/cardlang/cardlang/blob/main/language/spec/00-index.md) has the exact rules, including every rule this guide named, such as *EXP-2*. The [examples](https://github.com/cardlang/cardlang/tree/main/examples), FIDO2 and PIV, are complete applets for two real standards. And for an applet of your own, start from the vault, or from an empty `cardlang.json` as in [chapter 1](01-getting-started.md#your-first-applet).
