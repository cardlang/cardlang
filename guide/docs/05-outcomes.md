# 5. Outcomes

Every call in CardLang ends in one of two ways: `Ok`, with a result, or `Err`, with an error. There are no exceptions. A failure cannot jump past the code that should have dealt with it, because every call's outcome has to be handled where the call is written. This chapter shows the ways to handle one, where errors come from, and how they differ from traps.

## Producing an outcome

A function returns success with `return Ok(…)`, or `return Ok()` if it has no result. It returns failure with `return Err(…)`, naming one of the applet's errors (*OUT-3*, *OUT-4*):

<!-- check: fragment -->
```cardlang
errors WalletError {
    InsufficientFunds = 1;
    LimitExceeded = 2;
}

const LIMIT: u32 = 1000;

session balance: u32;

function withdraw(amount: u32) -> u32 {
    if amount > LIMIT {
        return Err(WalletError.LimitExceeded);
    }
    require amount <= balance else WalletError.InsufficientFunds;
    balance -= amount;
    return Ok(balance);
}
```

`require c else E;` is a short way of writing `if not c { return Err(E); }` (*STM-19*). It reads as the condition the rest of the function relies on.

An outcome is not a value (*OUT-2*). It cannot be stored in a variable, passed as an argument, or kept for later:

<!-- check: error CE-EXP-14 -->
```cardlang
function average(a: u32, b: u32) -> u32 {
    return Ok((a + b) / 2);
}

function example() -> u32 {
    var result: u32 = average(2, 4);
    return Ok(result);
}
```

The call's outcome has to be dealt with on the spot, in one of four ways.

## Handling an outcome

| Form | What it does with `Ok` | What it does with `Err` |
|---|---|---|
| `attempt f(…)` | Gives the result | Returns the same error from this function |
| `match f(…) { … }` | Runs the `Ok` arm | Runs an `Err` arm |
| `return f(…);` | Returns the same `Ok` | Returns the same `Err` |
| `ignore f(…);` | Discards it | Discards it |

A call that does none of these is an error (*OUT-7*):

<!-- check: error CE-OUT-1 -->
```cardlang
session total: u32;

function add(amount: u32) {
    total += amount;
    return Ok();
}

function example() {
    add(5);
    return Ok();
}
```

### `attempt`

`attempt` takes the result of `Ok`, and passes an `Err` straight up to the caller, unchanged (*OUT-10*). It is the right choice when this function cannot do anything useful about the error, which is most of the time. You have used it since chapter 2: `var operation: Command = attempt decode(request[0]);`.

For a function without a result, `attempt f();` is a statement on its own. For a function with one, `attempt` must use the result: discarding a result silently is an error (*OUT-9*).

### `attempt … else`

`attempt f(…) else Set.Member` works like `attempt`, except that any error becomes `Set.Member`, one of the applet's own errors (*OUT-22*). It is the short form for "whatever went wrong in there, the host should see this":

<!-- check: fragment -->
```cardlang
errors TallyError {
    TooLarge = 1;
}

session total: u8;

function add(amount: u8) {
    total = attempt checked_add(total, amount) else TallyError.TooLarge;
    return Ok();
}
```

Use it when every error of the call means the same thing to the caller. When different errors need different answers, use `match`.

### `match`

`match` handles success and failure in place. It has exactly one `Ok` arm, any number of arms for particular errors, and a final arm that catches every other error (*OUT-11*, *OUT-12*):

<!-- check: fragment -->
```cardlang
errors WalletError {
    InsufficientFunds = 1;
    LimitExceeded = 2;
}

session balance: u32;

function withdraw(amount: u32) -> u32 {
    require amount <= balance else WalletError.InsufficientFunds;
    balance -= amount;
    return Ok(balance);
}

function withdraw_what_you_can(amount: u32) -> u32 {
    match withdraw(amount) {
        Ok(remaining) => {
            return Ok(amount);
        }
        Err(WalletError.InsufficientFunds) => {
            var available: u32 = balance;
            balance = 0;
            return Ok(available);
        }
        Err(other) => {
            return Err(other);
        }
    }
}
```

- **`Ok(name)`** binds the result; `Ok(_)` ignores it, and `Ok()` matches a call with no result.
- **`Err(Set.Member)`** handles one particular error.
- **`Err(name)` or `Err(_)`** catches every other error, and must come last. It is required even when you have listed every error you know of, because a call may return errors from functions it calls in turn.

An error caught as `Err(name)` can only be passed on, with `return Err(name)`. It cannot be stored, compared or inspected (*OUT-14*). To act on a particular error, give it its own arm.

### Forwarding with `return`

`return f(…);` passes on the whole outcome of `f`, success or failure, as the outcome of this function (*OUT-5*). `f` must have the same result type. Chapter 4's `increment` ended this way, handing over to `read_counter`.

### `ignore`

`ignore f(…);` runs the call and discards its outcome, whatever it was (*STM-24*). It is for the rare call whose failure truly does not matter, and it says so where a reader will see it.

## The applet's errors

An applet declares its errors in one `errors` declaration, with a fixed code for each (*OUT-15*, *OUT-16*):

- **At most one** error set per applet.
- **Each code** is a nonzero `u16`, unique in the set.
- **Members are always written in full,** as `VaultError.WrongPin`.

The code is what the host sees. Once an applet is in use, a code must keep its meaning in every later version, and a removed error's code must not be reused (*OUT-17*). Choose them as carefully as you would any other part of a protocol.

<!-- check: error CE-OUT-7 -->
```cardlang
errors VaultError {
    MalformedRequest = 0;
}
```

An error carries nothing but its code: no message, and no data. When the host needs more, such as how many tries are left, the applet answers it as ordinary data, in another request.

## Platform errors

The platform has its own error set, `CardError`. Its errors come from the platform's APIs, and from the *checked* intrinsics, such as `checked_add`, which return an outcome instead of trapping:

| Member | Raised by |
|---|---|
| `CardError.Overflow` | `checked_add`, `checked_mul`, … when the result is too large |
| `CardError.Underflow` | `checked_sub`, … when the result is too small |
| `CardError.DivisionByZero` | `checked_div`, `checked_rem` |
| `CardError.ConversionRange` | `checked_convert`, when the value does not fit |

The platform's APIs add more; [chapter 8](08-platform.md#the-platforms-errors) has the full table. An error is either an *application* error or a *platform* error, and the host can always tell which, even when two codes are equal (*OUT-18*). In the raw binding, the envelope's first byte says which: `01` for the applet's errors, `02` for the platform's ([chapter 1](01-getting-started.md#what-the-host-receives)). An applet can catch a platform error by name, and pass it on, but never create one: `return Err(CardError.Overflow)` is an error (*OUT-19*).

Here is a small applet that keeps a running total of one-byte amounts, and handles overflow both ways. Command `01` turns it into an error of its own; command `02` passes the platform's error on with `attempt`:

<!-- check: program tally -->
```cardlang
errors TallyError {
    Malformed = 1;
    TooLarge = 2;
}

session total: u8;

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length == 2 else TallyError.Malformed;
    require response.length >= 1 else TallyError.Malformed;
    var amount: u8 = request[1];
    if request[0] == 0x01 {
        match checked_add(total, amount) {
            Ok(sum) => {
                total = sum;
            }
            Err(CardError.Overflow) => {
                return Err(TallyError.TooLarge);
            }
            Err(other) => {
                return Err(other);
            }
        }
    } else {
        total = attempt checked_add(total, amount);
    }
    response[0] = total;
    return Ok(1);
}
```

<!-- check: scenario tally -->
```scenario
install
power_on
command 01 F0           # 0 + 240
expect ok F0
command 01 20           # 240 + 32 does not fit a u8
expect err app 2
command 02 20           # the same, passed on as the platform's error
expect err platform Overflow
command 02 20           # as the host receives it: category 02, Overflow's code 0001
expect raw 02 00 01
command 01 0F           # the total is unchanged: 240 + 15
expect ok FF
```

## Traps are not errors

A trap, which you met in chapter 1, is something else entirely. An `Err` is a result the applet chose to return. A trap is a fault: an index out of range, plain `+` overflowing, a division by zero. It ends the whole command at once, and no `match` or `attempt` can catch it (*RTF-1*).

| | `Err` | Trap |
|---|---|---|
| Caused by | The applet returning it | A fault: `BOUNDS`, `OVERFLOW`, `DIV-ZERO`, … |
| Can be handled | Yes, by the caller | No |
| The host sees | The error's category and code | Only that a trap happened: category `03`, and no data |

So the question for every operation that can fail is: should it be an error or a trap?

- **Anything the host can cause** should be an `Err`: a short request, an unknown command, a wrong PIN, an amount too large. The host sent bad input, and deserves an answer it can act on. Check it with `require`, or use a checked intrinsic.
- **Anything that would be a bug in the applet** can be left to trap: an index the code has already checked, a sum that cannot overflow given the limits enforced earlier. A trap stops the command before it can do damage with a wrong value.

## `Err` undoes nothing

Returning `Err` does not roll anything back (*OUT-20*). Whatever the function changed before it returned stays changed: persistent state, session state, and anything written through an `inout`.

Chapter 4's `increment` has exactly this bug. It adds 1 to the counter, then calls `read_counter`, which can fail because the response is too small. The host gets an error, and the counter has gone up anyway. The rule that avoids it: **check everything that can fail before changing anything.** When several changes must happen together or not at all, that is what transactions are for, in [chapter 6](06-state.md).

## The vault handles its errors

The vault gets one new error, and an `increment` that checks first and treats the counter's end as an error the host can see. Replace `VaultError` and `increment`:

<!-- check: program vault -->
```cardlang
errors VaultError {
    MalformedRequest = 1;
    UnsupportedCommand = 2;
    ResponseTooSmall = 3;
    WrongPin = 4;
    CounterExhausted = 5;
}

function increment(data: ref u8[], response: inout u8[]) -> u32 {
    require data.length == 0 else VaultError.MalformedRequest;
    require response.length >= 4 else VaultError.ResponseTooSmall;
    match checked_add(counter, 1) {
        Ok(next) => {
            counter = next;
        }
        Err(CardError.Overflow) => {
            return Err(VaultError.CounterExhausted);
        }
        Err(other) => {
            return Err(other);
        }
    }
    return read_counter(ref data, inout response);
}
```

- **Both `require`s come first,** so a request that will fail changes nothing.
- **`checked_add` replaces `+`.** At 4 294 967 295 the counter cannot go up any more. With `+`, that was a trap; now the host gets `CounterExhausted`, and the counter keeps its value.
- **`Err(other)` passes on anything else.** `checked_add` returns nothing but `Overflow` here, but the catch-all is required, and passing an unexpected error on is the safe default.

No scenario can increment the counter four billion times, so the tally applet above is the test of this pattern. The scenario can check the first fix, though: a too-small response now leaves the counter alone.

<!-- check: scenario vault -->
```scenario
install
power_on
command 02 capacity 2   # no room for the answer
expect err app 3
command 01              # the counter did not change
expect ok 00 00 00 00
command 02
expect ok 00 00 00 01
command 20 31 32 33 34
expect ok
```

## What next

- In the tally applet, replace the `match` with `ignore checked_add(total, amount);`. What does the host see, and why is it worse than either version above?
- Find the places in the vault that can still trap. Can the host cause any of them?
- `verify_pin` answers `WrongPin` for any wrong PIN. A real device limits the guesses. To do that, the vault has to remember them, even when the power goes: [chapter 6](06-state.md).
