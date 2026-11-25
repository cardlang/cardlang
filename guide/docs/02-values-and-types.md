# 2. Values and types

CardLang has five kinds of value: integers, Booleans, arrays, structures and enums. Every one of them has a fixed size. There are no strings, no floating-point numbers and no pointers, and nothing is ever allocated while the applet runs. Because of that, the compiler knows how much memory an applet needs before it ever runs.

We'll go through the kinds one at a time, and then use them to give the vault a PIN. Most of the short examples sit inside a small function, because statements can only appear inside one. Functions get their own chapter, [chapter 4](04-functions-references-views.md). Until then, read `function name() { … }` as "some code" and `return Ok(…)` as "the result".

## Integers

There are six integer types. `u8`, `u16` and `u32` are unsigned, and `i8`, `i16` and `i32` are signed, with 8, 16 and 32 bits. Literals can be written in decimal, hex or binary, and `_` groups the digits:

<!-- check: fragment -->
```cardlang
const MAX_TRIES: u8 = 3;
const LIMIT: u32 = 0x0001_0000;
const MASK: u8 = 0b1111_0000;
const OFFSET: i16 = -200;
```

A literal has no type of its own. It takes the type of the place it's used in, and it has to fit there (*EXP-7*, *EXP-10*), so this is an error:

<!-- check: error CE-EXP-2 -->
```cardlang
const TOO_BIG: u8 = 300;
```

### No implicit conversion

CardLang never converts from one integer type to another unless you ask. Mixing two types in one expression is an error, even where the conversion would be harmless:

<!-- check: error CE-EXP-1 -->
```cardlang
function total(small: u8, large: u32) -> u32 {
    return Ok(small + large);
}
```

Literals are what make this bearable. Since a literal has no type until it meets one, it takes the type of the other operand. If `count` is a `u8`, `count + 1` is simply a `u8` addition, and there's nothing to convert (*EXP-7*).

Between two typed values you convert explicitly, and you choose a conversion that says what may happen to the value:

<!-- check: fragment -->
```cardlang
function conversions(small: u8, large: u32) -> u32 {
    var widened: u32 = convert<u32>(small);     // always fits: u8 into u32
    var low: u8 = truncate<u8>(large);          // keeps the low 8 bits
    return Ok(widened + large);
}
```

`convert<T>(x)` is for conversions that always fit, such as `u8` to `u32` or `u16` to `i32`. If the value might not fit, `convert` won't compile:

<!-- check: error CE-EXP-8 -->
```cardlang
function narrow(large: u32) -> u8 {
    return Ok(convert<u8>(large));
}
```

`truncate<T>(x)` keeps the low bits and throws the rest away, which is what you want when you split a number into bytes. `checked_convert<T>(x)` converts when the value fits and returns an error when it doesn't. Its result is an *outcome*, the same as a function's, and [chapter 5](05-outcomes.md) explains how to handle one.

### Overflow

Arithmetic never wraps around silently. If the result of `a + b` doesn't fit its type, the command stops with an `OVERFLOW` trap, just as reading past the end of the request did in chapter 1 (*EXP-23*). Dividing by zero traps too. If you want wrap-around, you say so:

<!-- check: fragment -->
```cardlang
function arithmetic(a: u8, b: u8) -> u8 {
    var wrapped: u8 = wrapping_add(a, b);       // 250 + 10 is 4
    return Ok(wrapped);
}
```

`wrapping_add`, `wrapping_sub` and `wrapping_mul` wrap around. Their relatives `checked_add` and so on return an error rather than trapping, which lets the applet deal with an overflow itself. They come back in [chapter 5](05-outcomes.md).

## Booleans

`bool` has the two values `true` and `false`, and the logical operators are the words `and`, `or` and `not`. A condition has to be a `bool`. Zero doesn't mean false, and an integer is never a condition (*STM-11*):

<!-- check: error CE-EXP-1 -->
```cardlang
function check(count: u8) -> bool {
    if count {
        return Ok(true);
    }
    return Ok(false);
}
```

You'd write `if count != 0` instead.

## Constants

A `const` gets its value when the applet is compiled. Its initializer can do arithmetic on other constants, declared in any order:

<!-- check: fragment -->
```cardlang
const BLOCK_SIZE: u32 = 16;
const BUFFER_SIZE: u32 = BLOCKS * BLOCK_SIZE;
const BLOCKS: u32 = 4;
```

The compiler works out every constant itself, so a constant that overflows or divides by zero is a compile error, not a trap:

<!-- check: error CE-CEX-3 -->
```cardlang
const TOTAL: u8 = 200 + 100;
```

There's no operator precedence in CardLang. You can't mix two different binary operators without parentheses (*EXP-2*), so the way an expression groups is always visible in the code:

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

A chain of the same operator, like `1 + 2 + 3`, is fine without parentheses and is worked out from left to right. Unary operators such as `-` and `not` don't count either, because they apply to the operand right after them, so `-x * 2` is allowed. Comparisons, though, are binary operators like any other. Combining two of them with `and` or `or` needs parentheses, as in `IN_RANGE`, and comparisons never chain, so even `a < b < c` is an error (*EXP-4*).

## Arrays

`T[N]` is an array of `N` values of type `T`. `N` has to be known when the applet is compiled, so it can be a constant but not a variable.

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

A variable declared without an initializer, like `digest`, holds its type's *default value*, which for an array of integers means all zeros. There's more about defaults [below](#default-values). To give the elements values, list them all in `[…]`, set them all to one value with `fill(x)`, or write a byte string, `b"…"`, which holds the ASCII codes of its characters. `a.length` is the number of elements. Every index is checked. An index past the end is a compile error if the compiler can see it, and a `BOUNDS` trap if it can't.

Arrays are values, so assigning one array to another copies the elements, and the two are independent from then on. To compare two arrays you use `equal`, which takes both of them by reference. [Chapter 4](04-functions-references-views.md) explains the `ref`.

<!-- check: fragment -->
```cardlang
const EXPECTED: u8[4] = b"1234";

function matches(given: u8[4]) -> bool {
    return Ok(equal(ref given, ref EXPECTED));
}
```

### Slices

A *slice*, `a[s..e]`, is the part of `a` from index `s` up to but not including `e`. It doesn't copy anything. It's a view of those elements, and it's used in two ways: you can copy into part of an array, or pass part of an array to something that expects an array, such as `equal`.

<!-- check: fragment -->
```cardlang
const MAGIC: u8[2] = [0xCA, 0xFE];

function build_frame() -> bool {
    var frame: u8[8];
    frame[0..2] = MAGIC;                        // copy into bytes 0 and 1
    frame[2..8] = fill(0x55);                   // set bytes 2 to 7
    return Ok(equal(ref frame[0..2], ref MAGIC));
}
```

Both ends of a slice are checked like an index. When you assign to a slice, both sides must have the same length. Chapter 1 already did this, in `response[0..4] = encode_be(counter)`. What you can't do is keep a slice in a variable, since it only lives as long as the statement it's in:

<!-- check: error CE-FUN-5 -->
```cardlang
function head(frame: u8[8]) -> u8 {
    var first: u8[2] = frame[0..2];
    return Ok(first[0]);
}
```

To keep the bytes, declare the array first, `var first: u8[2];`, and copy into it with `first[0..2] = frame[0..2];`. Functions can take slices as parameters, which [chapter 4](04-functions-references-views.md) covers.

## Structures

A `struct` puts several named fields together into one value:

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

A constructor has to name every field, but in any order you like. Structures are values, just like arrays. `limits` above is a copy, so changing it leaves `PIN_LIMITS` as it was. There are no methods and no inheritance. A field can be an array or another structure, but its size always has to be known.

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

You always write a variant together with its enum, as in `Light.Red`. Enums can be compared with `==` and `!=`, and taken apart with `match`.

A `match` has to list every variant, once each (*STM-16*). It has no default arm, and that's useful: add a variant to an enum, and the compiler shows you every `match` that needs a new arm.

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

Variants don't have numbers (*TYP-11*). `Light.Red` isn't 0, and you can't convert an enum to an integer or back:

<!-- check: error CE-EXP-8 -->
```cardlang
enum Light {
    Red;
    Amber;
    Green;
}

const CODE: u8 = convert<u8>(Light.Red);
```

This is on purpose. The bytes a host sends can't be trusted, and an enum value shouldn't exist until those bytes have been checked. You decode them yourself instead, and that's the next thing the vault needs.

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

CardLang has no uninitialized memory, and every value starts out as something you can name. You'll meet defaults in three places. A `var` without an initializer holds its type's default. `persistent` state gets its defaults once, when the applet's state is created at installation, and after that it keeps whatever the applet stores, which is why chapter 1's counter started at zero. `session` state is reset to its defaults whenever a session starts, for example each time the device is switched on. [Chapter 6](06-state.md) goes into those two, and into giving state a different starting value. This is also the one place where the order of an enum's variants matters: whichever variant comes first is the default.

## The vault gets a PIN

The vault now learns a third command, `20`, which verifies a PIN. Its request is the byte `20` followed by four PIN bytes. For now the PIN is fixed, and [chapter 6](06-state.md) will let the user change it.

The commands become an enum, with a function that turns a command byte into one. Add these to `vault.card`, and delete the two command constants from chapter 1:

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

The command bytes now appear only in `decode`. Next, the PIN itself, and a new error in `VaultError` for a wrong one:

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

`process` now decodes the first byte, and uses a `match` to pick what to do:

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

`attempt decode(request[0])` calls `decode`. If `decode` returns an error, `attempt` makes `process` return the same error straight away. Otherwise `operation` gets the command. `attempt` and the other ways of handling errors are the subject of [chapter 5](05-outcomes.md).

Each arm checks the length of its own request. A verify request is one command byte plus `PIN.length` bytes of PIN. Notice the parentheses in `request.length == (1 + PIN.length)`, which are needed because `==` and `+` are two different operators. `request[1..request.length]` is the slice of the request after the command byte, and `equal` compares it with `PIN`. A correct PIN gets `Ok(0)`, an answer with no bytes, since success is all the host needs to know.

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

The PIN bytes are the ASCII codes of the digits, so `31` is "1". Every step passes.
