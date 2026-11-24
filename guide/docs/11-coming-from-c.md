# 11. Coming from C or Java Card

Secure applets are usually written in C, for microcontrollers and TrustZone, or in Java Card, for smart cards. If you know either, this chapter maps what you know onto CardLang: what changes, and why. Each topic shows the familiar way briefly, then CardLang's, and the reason for the difference.

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

In C, a buffer is a local, a global, or a `malloc`, which can fail. In Java Card, every object is created with `new`, in persistent memory. Writing persistent memory is slow, and collecting garbage is a heavy operation, so applets usually create their objects once, at installation:

```java
private byte[] buffer;

private VaultApplet() {
    buffer = new byte[64];      // allocated once, in persistent memory
}
```

In CardLang, every value has a size fixed when the applet is built, and there is no allocation at all:

<!-- check: fragment -->
```cardlang
persistent buffer: u8[64];

function example() -> u8 {
    var scratch: u8[16];
    scratch[0] = buffer[0];
    return Ok(scratch[0]);
}
```

**Why:** an applet that cannot allocate cannot run out of memory halfway through a command. Since there is no recursion either, the compiler works out the applet's exact stack and storage needs, as in [chapter 9](09-testing-and-debugging.md#inside-the-image), and a device either has room for it or refuses it at installation.

## Errors

In C, an error is a return value, and nothing makes the caller look at it:

```c
if (len != PIN_LENGTH) return ERR_LENGTH;
...
verify_pin(pin, len);           /* the result is silently ignored */
```

In Java Card, an error is an exception, which jumps to whichever handler is up the stack, or to the platform, which turns it into a status word:

```java
if (len != PIN_LENGTH) ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
```

In CardLang, every call returns an outcome, and the compiler insists that each one is handled ([chapter 5](05-outcomes.md)). The mistake in the C code above does not compile:

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

The caller must say what happens on failure. Here, `attempt` passes the error on, and `verified` is set only when the PIN was checked:

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

`match`, a forwarding `return`, and an explicit `ignore` are the other ways to handle it.

**Why:** in a security applet, an unhandled failure is a vulnerability. With outcomes, every way a call can fail is visible where the call is written, and an error cannot skip past code that had to run.

## Integers and conversions

In C, unsigned arithmetic wraps silently, signed overflow is undefined, and conversions happen implicitly:

```c
uint8_t a = 250, b = 10;
uint8_t sum = a + b;            /* 4 */
```

In Java Card, `byte` is signed, arithmetic on `short` produces an `int` that must be cast back, and overflow wraps:

```java
short total = (short) (a + b);
short unsigned = (short) (buffer[i] & 0xFF);   /* bytes are signed */
```

In CardLang, the types are exactly the ones you mean, `u8` is unsigned, and nothing converts or wraps unless you say so ([chapter 2](02-values-and-types.md#integers)):

<!-- check: fragment -->
```cardlang
function example(a: u8, b: u8, large: u32) -> u32 {
    var wrapped: u8 = wrapping_add(a, b);       // wraps, because you said so
    var widened: u32 = convert<u32>(a);         // always fits
    var low: u8 = truncate<u8>(large);          // drops the high bits, because you said so
    return Ok(widened + convert<u32>(wrapped) + convert<u32>(low));
}
```

A plain `a + b` that does not fit is a trap, and `checked_add` returns an error instead.

**Why:** arithmetic on lengths, offsets and counters is where buffer overflows begin. A silent wrap turns a bad length into a small, plausible one; a trap stops the command instead.

## Operator precedence

C and Java share a classic bug:

```c
if (flags & MASK == 0) { ... }  /* means flags & (MASK == 0) */
```

CardLang has no precedence: two different operators always need parentheses ([chapter 2](02-values-and-types.md#constants)). The same line does not compile:

<!-- check: error CE-EXP-4 -->
```cardlang
const MASK: u8 = 0x0F;

function is_clear(flags: u8) -> bool {
    return Ok(flags & MASK == 0);               // does not compile: & and == are mixed
}
```

You write the grouping you mean, and the reader sees it:

<!-- check: fragment -->
```cardlang
const MASK: u8 = 0x0F;

function is_clear(flags: u8) -> bool {
    return Ok((flags & MASK) == 0);
}
```

**Why:** nobody remembers fifteen levels of precedence, and a reviewer should not have to.

## Pointers and references

In C, a pointer can be null, can outlive what it points to, and can be advanced past the end of a buffer. In Java Card, a reference can be null, and an array index is checked, but a reference can be stored anywhere.

In CardLang, `ref` and `inout` give a function access to its caller's data for the length of the call, and no longer ([chapter 4](04-functions-references-views.md#parameter-modes)). They cannot be stored, returned or null, and every index is checked. A view type cannot even be declared anywhere but a parameter:

<!-- check: error CE-TYP-5 -->
```cardlang
struct Request {
    data: u8[];                                 // does not compile: a view cannot be stored
}
```

**Why:** without stored references, no reference can dangle, and the compiler can see every access to a piece of data from the calls that pass it.

## Recursion and the stack

Both C and Java allow recursion, and on a device with a few kilobytes of stack, a deep one overflows at runtime. CardLang rejects any cycle in the call graph:

<!-- check: error CE-FUN-1 -->
```cardlang
function walk(depth: u32) {
    if depth > 0 {
        attempt walk(depth - 1);                // does not compile: walk calls itself
    }
    return Ok();
}
```

**Why:** with no recursion, the deepest possible chain of calls is known, and so is the stack it needs. A stack overflow is impossible, rather than merely unlikely.

## Persistence and atomicity

In C, keeping data across power loss means writing it to flash yourself, and making a multi-part update safe means writing a journal or double buffering by hand.

In Java Card, the fields of applet objects are persistent, a single field update is atomic, and a transaction groups several:

```java
JCSystem.beginTransaction();
Util.arrayCopy(buffer, offset, pin, (short) 0, length);
pinLength = length;
JCSystem.commitTransaction();
```

A forgotten `commitTransaction`, an exception that escapes, or a nested `beginTransaction` is only found at runtime.

In CardLang, `persistent` globals are the persistent state, every assignment to one is atomic, and a `transaction` is a block ([chapter 6](06-state.md#transactions)):

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

The block commits at its closing brace, and there is nothing to forget. A `return` out of the middle of a transaction, and a transaction nested in another, even through a called function, are compile errors.

**Why:** atomicity is the property that keeps a PIN counter honest when the power is cut. It should not depend on remembering to call a library correctly on every path.

## Session state

In Java Card, data that must be cleared at deselection or reset lives in a *transient* array, so even a single flag is an array:

```java
private final boolean[] verified =
    JCSystem.makeTransientBooleanArray((short) 1, JCSystem.CLEAR_ON_DESELECT);
...
verified[0] = true;
```

In C, it is RAM, which your startup code must clear at the right moments. In CardLang, it is a declaration ([chapter 6](06-state.md#four-kinds-of-storage)):

<!-- check: fragment -->
```cardlang
session verified: bool;
```

The platform resets it to its default at every session start.

## The entry point

A Java Card applet receives the APDU buffer, and does part of the transport's work itself:

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

A C trusted application is typically a function the host calls with pointers into shared memory, each of which it must check before use.

A CardLang applet gets the whole request, already reassembled, as a read-only view, and a response view to write into ([chapter 7](07-host.md)). It returns how many bytes it wrote, or an error. SELECT, chaining, long responses and status words are the platform's job, and every access to the request or response is bounds-checked.

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

Each of these makes CardLang a smaller language than the one you know. The trade is deliberate: a small applet whose memory, stack and failure behaviour are known before it runs, and which a reviewer can check line by line.

## Where to go from here

- **The [specification](https://github.com/cardlang/cardlang/blob/main/language/spec/00-index.md)** has the exact rules. Every rule the guide named, such as *EXP-2*, is there.
- **The [examples](https://github.com/cardlang/cardlang/tree/main/examples)**, FIDO2 and PIV, show complete applets for two real standards.
- **Your own applet:** start from the vault, or from an empty `cardlang.json`, as in [chapter 1](01-getting-started.md#your-first-applet).
