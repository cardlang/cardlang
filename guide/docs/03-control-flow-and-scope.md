# 3. Control flow and scope

This chapter covers the statements that make up a function's body: variables and assignment, `if`, loops, and how long a name is visible. It ends with how an applet's files fit together, and the vault learns to reject a PIN that is not all digits.

The statements are few, and each has one form. Several common constructs are left out on purpose, and the chapter says why as they come up.

## Blocks

A body is a *block*: statements between braces. Braces are always required, even around a single statement (*STM-1*), so there is no doubt about which statements an `if` or a loop controls. Every statement ends with `;`, except those that end with a block.

An expression on its own is not a statement (*STM-2*). `total + 1;` would compute a value and throw it away, which is almost always a mistake, so it is an error:

<!-- check: error CE-STM-1 -->
```cardlang
function example(total: u32) {
    total + 1;
    return Ok();
}
```

## Variables and assignment

A local variable is declared with `var`, its type, and usually an initial value. Without one, it holds its type's [default value](02-values-and-types.md#default-values):

<!-- check: fragment -->
```cardlang
function example() -> u32 {
    var count: u32 = 10;
    var total: u32;                             // 0
    total = count * 2;
    total += 5;                                 // the same as total = total + 5
    count -= 1;
    return Ok(total);
}
```

Assignment is a statement, not an expression (*STM-6*). It produces no value, so `a = b = 0` and `if (a = 0)` are not CardLang. There is no `++` or `--` either: write `count += 1`. The compound assignments are `+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `<<=` and `>>=` (*STM-25*), and they check overflow just as the operators do.

## `if`

<!-- check: fragment -->
```cardlang
function classify(length: u32) -> u8 {
    if length == 0 {
        return Ok(0);
    } else if length <= 8 {
        return Ok(1);
    } else {
        return Ok(2);
    }
}
```

The conditions are tried in order, and the first that is `true` runs its block. A condition must be a `bool` (*STM-11*), and needs no parentheses around it. `if` is a statement, not an expression: there is no `?:`.

## Loops

### `while`

`while` runs its block as long as its condition is `true`, checking the condition before each run (*STM-12*):

<!-- check: fragment -->
```cardlang
function digits_in(value: u32) -> u8 {
    var remaining: u32 = value;
    var count: u8 = 1;
    while remaining >= 10 {
        remaining /= 10;
        count += 1;
    }
    return Ok(count);
}
```

### `for`

`for` counts through a range of integers. The index has a declared type, and the range includes its start but not its end, so `0..4` runs 0, 1, 2 and 3 (*STM-13*, *STM-14*):

<!-- check: fragment -->
```cardlang
function sum(values: u16[8]) -> u32 {
    var total: u32;
    for index: u32 in 0..8 {
        total += convert<u32>(values[index]);
    }
    return Ok(total);
}
```

- **The bounds are evaluated once,** before the first run. Changing a variable used in them afterwards does not change the loop.
- **The index is read-only** inside the loop, and exists only there.
- **Both bounds must fit the index's type.** `for index: u8 in 0..256` is an error, even though the index never reaches 256: use a wider type.
- **Ranges only count up, by one.** To count down, or in steps, use `while`.

### `break` and `continue`

`break` leaves the innermost loop, and `continue` goes on to its next run (*STM-15*). A `while true` loop ends only through `break` or `return`:

<!-- check: fragment -->
```cardlang
const BLOCK: u8[16] = fill(0x00);

function first_nonzero(data: u8[16]) -> u32 {
    var found: u32 = data.length;
    for index: u32 in 0..data.length {
        if data[index] == 0 {
            continue;
        }
        found = index;
        break;
    }
    return Ok(found);
}
```

There are no labelled loops, so a `break` cannot leave two loops at once. CardLang has no `goto`, no `switch`, and no `do … while`. `match` takes the place of `switch` for enums, as [chapter 2](02-values-and-types.md#enums) showed, and has no fall-through.

## Every path returns

A function must end with a `return`: the compiler never adds one for you (*STM-21*). It checks, from the shape of the code alone, that no path can run off the end of the body:

<!-- check: error CE-STM-5 -->
```cardlang
function sign(value: i32) -> i8 {
    if value < 0 {
        return Ok(-1);
    } else if value > 0 {
        return Ok(1);
    }
}
```

Here the case `value == 0` falls off the end. Even if every case were covered by conditions, the compiler does not reason about the values: it needs a final `else`, or a `return` after the `if`. The rule is deliberately simple, so that you can apply it by eye (*STM-20*).

## Scope

A local variable exists from its declaration to the end of the block that contains it. A name declared in a block cannot be the same as any name already visible there: a global, a parameter, or a local of an enclosing block (*NAM-21*). There is no shadowing, so a name always means one thing in a function:

<!-- check: error CE-NAM-3 -->
```cardlang
persistent count: u32;

function example() -> u32 {
    var count: u32 = 1;
    return Ok(count);
}
```

This is the error *CE-NAM-3*. Two separate blocks can each declare their own variable of the same name, since neither is visible from the other.

## An applet's files

An applet is the set of files listed in its `cardlang.json`. As it grows, you can split it into as many files as you like, as the example applets do:

```json
{ "name": "vault", "files": ["errors.card", "pin.card", "vault.card"], "binding": "raw" }
```

All of an applet's files share one scope:

- **Every top-level declaration is visible everywhere,** in every file, before and after the point where it is declared (*NAM-13*). Neither the order of the files nor the order of declarations matters (*NAM-4*).
- **So every top-level name must be unique** across the whole applet. Two declarations of one name, in the same file or in two, are an error (*NAM-11*).
- **There are no imports, modules, namespaces or private declarations** (*NAM-8*). A file is a way to organise the source, not a boundary.
- **Applets are isolated from each other.** Nothing in one applet can name anything in another (*NAM-5*).

## The vault accepts only digits

A PIN is typed on a keypad, so the vault should reject one that is not all digits, before comparing it. Replace `process` with this version, whose verify arm checks every byte with a loop:

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
            counter += 1;
            response[0..4] = encode_be(counter);
            return Ok(4);
        }
        Command.VerifyPin => {
            require request.length == (1 + PIN.length) else VaultError.MalformedRequest;
            for index: u32 in 1..request.length {
                var digit: u8 = request[index];
                require (digit >= 0x30) and (digit <= 0x39) else VaultError.MalformedRequest;
            }
            require equal(ref request[1..request.length], ref PIN) else VaultError.WrongPin;
            return Ok(0);
        }
    }
}
```

- **The loop starts at 1,** skipping the command byte. `0x30` to `0x39` are the ASCII codes of the digits `0` to `9`.
- **`require` works inside a loop,** as anywhere: the first byte that is not a digit ends the command with `MalformedRequest`.
- **A malformed PIN is not a wrong PIN.** It is rejected before it is compared, so it does not count as a guess. That will matter in [chapter 6](06-state.md), when wrong guesses are limited.

Add to `vault.scenario`:

<!-- check: scenario vault -->
```scenario
install
power_on
command 20 31 32 33 34  # verify "1234"
expect ok
command 20 31 32 33 35  # "1235": a wrong PIN
expect err app 4
command 20 31 32 41 34  # "12A4": not all digits
expect err app 1
command 02
expect ok 00 00 00 01
```

## What next

- Split `vault.card` into two files: the errors, the constants and `decode` in one, `process` in the other. List both in `cardlang.json`, and check that nothing else needs to change.
- Write the digit check with `while` instead of `for`. Which is easier to read?
- Change the verify arm so that the loop checks only the PIN's bytes, by looping over `0..PIN.length` and indexing `request[index + 1]`. Is it clearer?
