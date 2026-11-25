# 3. Control flow and scope

The vault will soon need to look at every byte of a PIN, one at a time, and for that it needs a loop. This chapter is about the statements a function body is made of: variables and assignment, `if`, loops, and where a name can be seen. It finishes with how an applet's files fit together.

There aren't many statements, and each comes in one form. A few familiar constructs are missing on purpose, and you'll see why as they come up.

## Blocks

The body of a function, an `if` or a loop is a *block*, a list of statements in braces. The braces are required even around a single statement (*STM-1*), so it's always clear which statements an `if` or a loop controls. Statements end with `;`, apart from those that end with a block.

An expression on its own isn't a statement (*STM-2*). `total + 1;` would compute a value and then throw it away, which is nearly always a mistake, so CardLang rejects it:

<!-- check: error CE-STM-1 -->
```cardlang title="Does not compile: CE-STM-1"
function example(total: u32) {
    total + 1;
    return Ok();
}
```

## Variables and assignment

You declare a local variable with `var`, its type, and usually a starting value. If you leave the value out, the variable holds its type's [default value](02-values-and-types.md#default-values).

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

Assignment is a statement and produces no value (*STM-6*), so `a = b = 0` and `if (a = 0)` aren't valid CardLang. There's no `++` or `--` either. Write `count += 1` instead. The compound assignments `+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `<<=` and `>>=` (*STM-25*) check for overflow, just like the operators they're built from.

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

The conditions are tried in order, and the block of the first one that's `true` runs. Each condition must be a `bool` (*STM-11*), and doesn't need parentheses. Since `if` is a statement and not an expression, there's no `?:`.

## Loops

### `while`

A `while` loop checks its condition before every pass, and keeps going while the condition is `true` (*STM-12*):

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

A `for` loop counts through a range of integers, with an index of a type you declare. The range includes its start but not its end, so `0..4` gives 0, 1, 2 and 3 (*STM-13*, *STM-14*).

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

The two ends of the range are worked out once, before the first pass. If a variable they use changes afterwards, the loop doesn't notice. Inside the loop the index is read-only, and it disappears when the loop ends. Both ends have to fit the index's type, which catches people out: `for index: u8 in 0..256` is an error even though the index never actually reaches 256, so use a wider type. Ranges only count upwards, one at a time. To count down, or in bigger steps, use `while`.

### `break` and `continue`

`break` leaves the innermost loop, and `continue` skips to its next pass (*STM-15*). A `while true` loop can only end with a `break` or a `return`.

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

Loops can't be labelled, so a `break` only ever leaves one loop. There's also no `goto`, no `switch` and no `do … while`. For enums, `match` does the job of `switch`, as [chapter 2](02-values-and-types.md#enums) showed, and it has no fall-through.

## Every path returns

The compiler never adds a `return` for you (*STM-21*). It checks that no path through a function can run off the end of its body, and it decides that from the shape of the code alone:

<!-- check: error CE-STM-5 -->
```cardlang title="Does not compile: CE-STM-5"
function sign(value: i32) -> i8 {
    if value < 0 {
        return Ok(-1);
    } else if value > 0 {
        return Ok(1);
    }
}
```

When `value` is zero, this function runs off the end. Even if the conditions did cover every possible value, the compiler wouldn't reason about values to find out. It wants a final `else`, or a `return` after the `if`. That makes the rule simple enough to check by eye (*STM-20*).

## Scope

A local variable can be used from its declaration to the end of the block it's declared in. A new name can't be the same as one that's already visible at that point, whether that's a global, a parameter, or a local of an enclosing block (*NAM-21*). Since nothing can be shadowed, a name always means the same thing throughout a function.

<!-- check: error CE-NAM-3 -->
```cardlang title="Does not compile: CE-NAM-3"
persistent count: u32;

function example() -> u32 {
    var count: u32 = 1;
    return Ok(count);
}
```

That's the error *CE-NAM-3*. Two separate blocks can each have a variable with the same name, though, because neither can see the other's.

## An applet's files

An applet is the set of files that its `cardlang.json` lists. When it grows, you can split it into as many files as you like, as the example applets do:

```json
{ "name": "vault", "files": ["errors.card", "pin.card", "vault.card"], "binding": "raw" }
```

The files share a single scope. A top-level declaration is visible in every file, both before and after the place where it's declared (*NAM-13*), and the order of files and declarations makes no difference (*NAM-4*). That means every top-level name has to be unique across the whole applet. Declaring the same name twice is an error, whether it happens in one file or in two (*NAM-11*). There are no imports, modules, namespaces or private declarations (*NAM-8*). Files are just a way of organising the source. Applets, on the other hand, are completely separate from each other, and nothing in one applet can refer to anything in another (*NAM-5*).

## The vault accepts only digits

A PIN is entered on a keypad, so a PIN that contains anything other than digits should be rejected before it's even compared. Replace `process` with this version, whose verify arm checks every byte in a loop:

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

The loop starts at 1 to skip the command byte, and `0x30` to `0x39` are the ASCII codes of `0` to `9`. A `require` inside a loop behaves as it does anywhere else, so the first byte that isn't a digit ends the command with `MalformedRequest`. A malformed PIN is rejected before the comparison, so it never counts as a wrong guess. That will matter in [chapter 6](06-state.md), when the vault starts limiting guesses.

Add these steps to `vault.scenario`:

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
