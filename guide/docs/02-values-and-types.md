# 2. Values and types

CardLang has few kinds of values, and all of them have a fixed size: integers, Booleans, arrays, structures and enums. There are no strings, no floating point, no pointers and nothing allocated at runtime. That is what lets the compiler tell you, before the applet ever runs, exactly how much memory it needs.

This chapter goes through each kind, and then uses them to give the vault a PIN.

Most short examples here sit inside a small function, because statements can only appear in one. [Chapter 3](03-functions-references-slices.md) explains functions properly. For now, read `function name() { … }` as "some code", and `return Ok(…)` as "the result".

## Integers

There are six integer types: unsigned `u8`, `u16` and `u32`, and signed `i8`, `i16` and `i32`, of 8, 16 and 32 bits. A literal can be written in decimal, hex or binary, with `_` to group digits:

<!-- check: fragment -->
```cardlang
const MAX_TRIES: u8 = 3;
const LIMIT: u32 = 0x0001_0000;
const MASK: u8 = 0b1111_0000;
const OFFSET: i16 = -200;
```

A literal has no type of its own. It takes the type it is used as, and must fit it (*EXP-10*):

<!-- check: error CE-EXP-2 -->
```cardlang
const TOO_BIG: u8 = 300;
```

### No implicit conversion

CardLang never converts between integer types by itself. An expression mixing two types is an error, even when the conversion would be safe:

<!-- check: error CE-EXP-1 -->
```cardlang
function total(small: u8, large: u32) -> u32 {
    return Ok(small + large);
}
```

Literals are the exception, and the reason this rule is bearable. A literal has no type until it meets one, so it takes the type of the other operand: if `count` is a `u8`, then `count + 1` is a `u8` addition, with no conversion to write (*EXP-7*).

Between two typed values, you convert explicitly, and the name of the conversion says what can happen:

<!-- check: fragment -->
```cardlang
function conversions(small: u8, large: u32) -> u32 {
    var widened: u32 = convert<u32>(small);     // always fits: u8 into u32
    var low: u8 = truncate<u8>(large);          // keeps the low 8 bits
    return Ok(widened + large);
}
```

- **`convert<T>(x)`** is for conversions that always fit, such as `u8` into `u32` or `u16` into `i32`. A `convert` that might not fit does not compile:

    <!-- check: error CE-EXP-8 -->
    ```cardlang
    function narrow(large: u32) -> u8 {
        return Ok(convert<u8>(large));
    }
    ```

- **`truncate<T>(x)`** keeps the low bits, and drops the rest. You use it when that is what you mean, as when splitting a number into bytes.
- **`checked_convert<T>(x)`** converts when the value fits and returns an error when it does not. It is an *outcome*, like the result of a function, which [chapter 4](04-outcomes.md) explains.

### Overflow

Ordinary arithmetic never wraps silently. If `a + b` does not fit its type, the command stops with a trap, `OVERFLOW`, as reading past the end of the request did in chapter 1 (*EXP-23*). The same goes for division by zero. When you want something else, you say so:

<!-- check: fragment -->
```cardlang
function arithmetic(a: u8, b: u8) -> u8 {
    var wrapped: u8 = wrapping_add(a, b);       // 250 + 10 is 4
    return Ok(wrapped);
}
```

`wrapping_add`, `wrapping_sub` and `wrapping_mul` wrap around, as unsigned arithmetic does in C. `checked_add` and its relatives return an error instead of trapping, so the applet can handle an overflow: they come back in [chapter 4](04-outcomes.md).

## Booleans

`bool` has two values, `true` and `false`. The logical operators are words: `and`, `or` and `not`. A condition must be a `bool`: there is no "zero means false", so an integer is never a condition (*STM-11*):

<!-- check: error CE-EXP-1 -->
```cardlang
function check(count: u8) -> bool {
    if count {
        return Ok(true);
    }
    return Ok(false);
}
```

Write `if count != 0` instead.

## Constants

A `const` is a value fixed when the applet is compiled. Its initializer can use other constants, in any order, and arithmetic on them:

<!-- check: fragment -->
```cardlang
const BLOCK_SIZE: u32 = 16;
const BUFFER_SIZE: u32 = BLOCKS * BLOCK_SIZE;
const BLOCKS: u32 = 4;
```

The compiler evaluates constants, so a constant that overflows, or divides by zero, is a compile error rather than a trap:

<!-- check: error CE-CEX-3 -->
```cardlang
const TOTAL: u8 = 200 + 100;
```

CardLang has no operator precedence. Two different binary operators cannot be mixed without parentheses (*EXP-2*), so the grouping of an expression is always written out, never inferred:

<!-- check: error CE-EXP-4 -->
```cardlang
const MIXED: u32 = 1 + 2 * 3;
```

<!-- check: fragment -->
```cardlang
const GROUPED: u32 = 1 + (2 * 3);
const CHAINED: u32 = 1 + 2 + 3;
const NEGATED: i32 = -GROUPED_SIGNED * 2;
const GROUPED_SIGNED: i32 = 7;
const IN_RANGE: bool = (CHAINED > 0) and (CHAINED < 10);
```

What still needs no parentheses:

- **A chain of one operator,** as in `1 + 2 + 3`, which is evaluated left to right.
- **A unary operator,** such as `-` or `not`: it applies to the operand right after it, so `-x * 2` is fine.

Comparisons are binary operators too, so combining them with `and` or `or` needs parentheses, as in `IN_RANGE` above. And comparisons never chain: `a < b < c` is an error even with one operator (*EXP-4*).

## Arrays

`T[N]` is an array of `N` values of type `T`. `N` is fixed when the applet is compiled: it can be a constant, but not a variable.

<!-- check: fragment -->
```cardlang
const DIGEST_SIZE: u32 = 32;

function arrays() -> u8 {
    var digest: u8[DIGEST_SIZE];                // 32 zero bytes
    var header: u8[4] = [0x01, 0x02, 0x03, 0x04];
    var padding: u8[8] = fill(0xFF);            // 8 bytes of 0xFF
    var label: u8[5] = b"vault";                // the ASCII bytes of "vault"
    digest[0] = header[3];
    return Ok(digest[0]);
}
```

- **A variable without an initializer** holds its type's *default value*: for an array of integers, all zeros. [Default values](#default-values), below, has the whole story.
- **An array list,** `[…]`, gives every element. **`fill(x)`** sets every element to `x`. **`b"…"`** is a byte string: an array of the bytes of its ASCII characters.
- **`a.length`** is the number of elements.
- **An index** is checked. An index past the end is a compile error when the compiler can see it, and otherwise the trap `BOUNDS`.

Arrays are values. Assigning one array to another copies its elements, so the two stay separate afterwards. To compare two arrays, use `equal`, which takes both by reference (the `ref` is explained in [chapter 3](03-functions-references-slices.md)):

<!-- check: fragment -->
```cardlang
const EXPECTED: u8[4] = b"1234";

function matches(given: u8[4]) -> bool {
    return Ok(equal(ref given, ref EXPECTED));
}
```

### Slices

`a[s..e]` is a *slice*: the elements of `a` from index `s` up to, but not including, `e`. A slice is not a copy. It is a view of part of `a`, and you use it in two places: to copy into part of an array, and to hand part of an array to something that takes an array, such as `equal`:

<!-- check: fragment -->
```cardlang
const MAGIC: u8[2] = [0xCA, 0xFE];

function frame() -> bool {
    var frame: u8[8];
    frame[0..2] = MAGIC;                        // copy into bytes 0 and 1
    frame[2..8] = fill(0x55);                   // set bytes 2 to 7
    return Ok(equal(ref frame[0..2], ref MAGIC));
}
```

- **Both ends are checked,** as an index is: a slice past the end of its array is a compile error when the compiler can see it, and otherwise the trap `BOUNDS`.
- **In a slice assignment,** both sides must have the same length. Chapter 1 used one already: `response[0..4] = encode_be(counter)`.
- **A slice cannot be kept in a variable.** It only lives as long as the statement it is in:

    <!-- check: error CE-FUN-5 -->
    ```cardlang
    function head(frame: u8[8]) -> u8 {
        var first: u8[2] = frame[0..2];
        return Ok(first[0]);
    }
    ```

    To keep the bytes, declare an array and copy into it: `first = …` becomes `var first: u8[2];` followed by `first[0..2] = frame[0..2];`.

[Chapter 3](03-functions-references-slices.md) shows how functions take slices and other views as parameters.

## Structures

A `struct` groups named fields into one value:

<!-- check: fragment -->
```cardlang
struct Limits {
    min_length: u32;
    max_length: u32;
    tries: u8;
}

const PIN_LIMITS: Limits = Limits { min_length: 4, max_length: 8, tries: 3 };

function longest() -> u32 {
    var limits: Limits = PIN_LIMITS;
    limits.tries = 5;
    return Ok(limits.max_length);
}
```

A constructor names every field, in any order. Structures are values too: `limits` above is a copy, and changing it leaves `PIN_LIMITS` alone. Structures have no methods and no inheritance. A structure's fields can be arrays and other structures, but never an array of unknown size.

## Enums

An `enum` is a type whose values are a fixed list of names:

<!-- check: fragment -->
```cardlang
enum Light {
    Red;
    Amber;
    Green;
}

function next(light: Light) -> Light {
    match light {
        Light.Red => {
            return Ok(Light.Green);
        }
        Light.Amber => {
            return Ok(Light.Red);
        }
        Light.Green => {
            return Ok(Light.Amber);
        }
    }
}
```

A variant is always written with its enum's name, as in `Light.Red`. Enums can be compared with `==` and `!=`, and taken apart with `match`.

**`match` lists every variant, exactly once** (*STM-16*). There is no default arm, so when you add a variant to an enum, the compiler points at every `match` you need to update:

<!-- check: error CE-STM-4 -->
```cardlang
enum Light {
    Red;
    Amber;
    Green;
}

function stop(light: Light) -> bool {
    match light {
        Light.Red => {
            return Ok(true);
        }
        Light.Amber => {
            return Ok(true);
        }
    }
}
```

**A variant has no number** (*TYP-11*). Unlike in C, `Light.Red` is not 0, and an enum cannot be converted to or from an integer:

<!-- check: error CE-EXP-8 -->
```cardlang
enum Light {
    Red;
    Amber;
    Green;
}

const CODE: u8 = convert<u8>(Light.Red);
```

That is deliberate. The bytes a host sends are not trusted, and an enum value should only exist once those bytes have been checked. So you decode them yourself, which is exactly what the vault needs next.

## Default values

Every type has a *default value* (*TYP-22*):

| Type | Its default value |
|---|---|
| An integer type | `0` |
| `bool` | `false` |
| An enum | Its first variant |
| An array `T[N]` | `N` elements, each the default of `T` |
| A structure | Every field holding the default of its own type |

<!-- check: fragment -->
```cardlang
enum Light {
    Red;
    Amber;
    Green;
}

struct Limits {
    min_length: u32;
    max_length: u32;
    tries: u8;
}

function defaults() -> bool {
    var count: u32;                             // 0
    var seen: bool;                             // false
    var light: Light;                           // Light.Red, the first variant
    var limits: Limits;                         // every field 0
    var digest: u8[32];                         // 32 zero bytes
    return Ok(light == Light.Red);
}
```

There is no uninitialized memory in CardLang: every value starts as something you can name. Default values appear in three places:

- **A `var` without an initializer** holds the default of its type.
- **`persistent` state** holds its defaults when the applet's state is first created, at installation. It never gets them again: from then on, it keeps whatever the applet stored. That is why chapter 1's counter started at zero.
- **`session` state** gets its defaults at the start of every session, such as each time the device powers on.

[Chapter 5](05-state.md) covers the last two, and how to set up state that should start with another value. The order of an enum's variants matters only here: moving a variant to the top makes it the default.

## The vault gets a PIN

The vault now learns a third command, `20`, which verifies a PIN: a request of `20` followed by four PIN bytes. The PIN is fixed for now. [Chapter 5](05-state.md) makes it one the user can change.

First, the commands become an enum, with a function that decodes a command byte into one. Add these to `vault.card`, and replace the two command constants from chapter 1 with them:

<!-- check: program vault remove=READ_COUNTER,INCREMENT -->
```cardlang
enum Command {
    ReadCounter;
    Increment;
    VerifyPin;
}

function decode(code: u8) -> Command {
    if code == 0x01 {
        return Ok(Command.ReadCounter);
    } else if code == 0x02 {
        return Ok(Command.Increment);
    } else if code == 0x20 {
        return Ok(Command.VerifyPin);
    }
    return Err(VaultError.UnsupportedCommand);
}
```

The byte values now appear in one place, `decode`, and nowhere else. Then the PIN, and an error for a wrong one, added to `VaultError`:

<!-- check: program vault -->
```cardlang
errors VaultError {
    MalformedRequest = 1;
    UnsupportedCommand = 2;
    ResponseTooSmall = 3;
    WrongPin = 4;
}

const PIN: u8[4] = b"1234";
```

Finally, `process` decodes the first byte and dispatches with a `match`:

<!-- check: program vault -->
```cardlang
command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length >= 1 else VaultError.MalformedRequest;
    require response.length >= 4 else VaultError.ResponseTooSmall;
    var operation: Command = attempt decode(request[0]);
    match operation {
        Command.ReadCounter => {
            require request.length == 1 else VaultError.MalformedRequest;
            response[0..4] = encode_be(counter);
            return Ok(4);
        }
        Command.Increment => {
            require request.length == 1 else VaultError.MalformedRequest;
            counter = counter + 1;
            response[0..4] = encode_be(counter);
            return Ok(4);
        }
        Command.VerifyPin => {
            require request.length == (1 + PIN.length) else VaultError.MalformedRequest;
            require equal(ref request[1..request.length], ref PIN) else VaultError.WrongPin;
            return Ok(0);
        }
    }
}
```

- **`attempt decode(request[0])`** calls `decode`. If it returns an error, `process` returns that same error at once; otherwise `operation` gets the decoded command. [Chapter 4](04-outcomes.md) is about `attempt` and its relatives.
- **Each arm checks its own request length.** A verify request is 1 byte of command and `PIN.length` bytes of PIN. The parentheses in `request.length == (1 + PIN.length)` are needed: `==` and `+` are two different operators too.
- **`request[1..request.length]`** is the slice of the request after its command byte. `equal` compares it with `PIN`.
- **`return Ok(0)`** answers with no bytes: success is the whole answer.

Add these steps to the end of `vault.scenario`:

<!-- check: scenario vault -->
```scenario
install
power_on
command 20 31 32 33 34  # verify "1234"
expect ok
command 20 31 32 33 35  # verify "1235"
expect err app 4
command 20 31 32 33     # too short
expect err app 1
command 01              # reading the counter still works
expect ok 00 00 00 00
command 07
expect err app 2
```

The PIN bytes are the ASCII codes of the digits: `31` is "1". Run it, and every step passes.

## What next

- Add a command `03` that answers the vault's version, as a constant `u8[2]`. You need a variant, a line in `decode`, and an arm in the `match`. Try leaving out the arm first, and read the error.
- Make the wrong-PIN error happen for a PIN of the wrong length too, instead of `MalformedRequest`. Which is better for the host to see?
- In `decode`, a `match` is not possible, because `code` is an integer. Why does CardLang allow `match` only on enums and outcomes? [Chapter 4](04-outcomes.md) gives part of the answer.
