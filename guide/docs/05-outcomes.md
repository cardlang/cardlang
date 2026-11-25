# 5. Outcomes

A call in CardLang ends in one of two ways. It returns `Ok`, with a result, or `Err`, with an error. Nothing can be thrown, so a failure can't sail past the code that ought to deal with it: the outcome of every call has to be handled right where the call is written. This chapter covers the ways of handling one, where errors come from, and how an error differs from a trap.

## Producing an outcome

A function reports success with `return Ok(…)`, or `return Ok()` when there's no result, and failure with `return Err(…)`, naming one of the applet's errors (*OUT-3*, *OUT-4*):

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

`require c else E;` is shorthand for `if not c { return Err(E); }` (*STM-19*). It reads well as a statement of what the rest of the function relies on.

An outcome isn't a value (*OUT-2*). You can't put it in a variable, pass it as an argument or keep it for later:

<!-- check: error CE-EXP-14 -->
```cardlang title="Does not compile: CE-EXP-14"
function average(a: u32, b: u32) -> u32 {
    return Ok((a + b) / 2);
}

function example() -> u32 {
    var result: u32 = average(2, 4);
    return Ok(result);
}
```

It has to be dealt with there and then, and there are four ways to do it.

## Handling an outcome

| Form | What it does with `Ok` | What it does with `Err` |
|---|---|---|
| `attempt f(…)` | Gives the result | Returns the same error from this function |
| `match f(…) { … }` | Runs the `Ok` arm | Runs an `Err` arm |
| `return f(…);` | Returns the same `Ok` | Returns the same `Err` |
| `ignore f(…);` | Discards it | Discards it |

A call that uses none of them won't compile (*OUT-7*):

<!-- check: error CE-OUT-1 -->
```cardlang title="Does not compile: CE-OUT-1"
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

`attempt` gives you the result inside an `Ok`, and passes an `Err` up to the caller unchanged (*OUT-10*). It's what you want whenever the current function can't do anything useful about the error, which is most of the time. The vault has used it since chapter 2, in `var operation: Command = attempt decode(request[0]);`.

If the function you call has no result, `attempt f();` stands on its own as a statement. If it does have one, you have to use it, because quietly discarding a result is an error (*OUT-9*).

### `attempt … else`

`attempt f(…) else Set.Member` behaves like `attempt`, except that whatever error comes back is replaced by `Set.Member`, one of the applet's own errors (*OUT-22*). Think of it as "whatever went wrong in there, the host should see this":

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

It suits calls where every possible error means the same thing to the caller. If different errors need different answers, reach for `match`.

### `match`

`match` deals with success and failure on the spot. It has one `Ok` arm, as many arms as you like for particular errors, and a last arm that catches all the others (*OUT-11*, *OUT-12*):

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

`Ok(name)` binds the result to a name, `Ok(_)` ignores it, and `Ok()` matches a call that has no result. `Err(Set.Member)` picks out one particular error. The catch-all, `Err(name)` or `Err(_)`, has to come last, and it's required even when you've listed every error you can think of, because the call might pass on errors from the functions it calls in turn.

An error caught as `Err(name)` can only be passed on with `return Err(name)`. You can't store it, compare it or look inside it (*OUT-14*). If you need to treat an error differently, give it an arm of its own.

### Forwarding with `return`

`return f(…);` hands back the whole outcome of `f`, success or failure, as the outcome of the current function (*OUT-5*). `f` must have the same result type. That's how chapter 4's `increment` ended, passing over to `read_counter`.

### `ignore`

`ignore f(…);` makes the call and throws its outcome away, whatever it was (*STM-24*). It's meant for the occasional call whose failure really doesn't matter, and it makes that visible to anyone reading the code.

## The applet's errors

An applet declares all its errors in a single `errors` declaration, and gives each one a fixed code (*OUT-15*, *OUT-16*). There's at most one such set per applet, each code is a nonzero `u16` that no other member of the set uses, and members are always written in full, as in `VaultError.WrongPin`.

The host sees the code, so treat the codes as part of your protocol. Once an applet is in use, a code has to keep its meaning in every later version, and a code that belonged to a removed error must not be reused (*OUT-17*). Zero is never a valid code:

<!-- check: error CE-OUT-7 -->
```cardlang title="Does not compile: CE-OUT-7"
errors VaultError {
    MalformedRequest = 0;
}
```

An error is nothing but its code. It has no message and no data. When the host needs to know more, such as how many tries are left, the applet answers that as ordinary data, in reply to another request.

## Platform errors

The platform has an error set of its own, `CardError`. Its errors come from the platform's APIs, and from the *checked* intrinsics, such as `checked_add`, which return an outcome where plain arithmetic would trap:

| Member | Raised by |
|---|---|
| `CardError.Overflow` | `checked_add`, `checked_mul`, … when the result is too large |
| `CardError.Underflow` | `checked_sub`, … when the result is too small |
| `CardError.DivisionByZero` | `checked_div`, `checked_rem` |
| `CardError.ConversionRange` | `checked_convert`, when the value does not fit |

The platform's APIs add more, and the [platform reference](reference-platform.md#the-platforms-errors) lists them all. Every error is either an *application* error or a *platform* error, and the host can always tell which, even if two codes are equal (*OUT-18*). In the raw binding it's the envelope's first byte that says so, `01` for the applet's errors and `02` for the platform's ([chapter 1](01-getting-started.md#what-the-host-receives)). An applet can catch a platform error by name and pass it on, but it can't make one up: `return Err(CardError.Overflow)` is an error (*OUT-19*).

Here's a small applet that keeps a running total of one-byte amounts, and handles overflow in both ways. Command `01` turns an overflow into an error of its own, and command `02` passes the platform's error on with `attempt`:

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

The traps you met in chapter 1 are a different thing altogether. An `Err` is a result the applet decided to return, while a trap is a fault, such as an index out of range, a plain `+` that overflows, or a division by zero. A trap ends the whole command immediately, and no `match` or `attempt` can catch it (*RTF-1*).

| | `Err` | Trap |
|---|---|---|
| Caused by | The applet returning it | A fault: `BOUNDS`, `OVERFLOW`, `DIV-ZERO`, … |
| Can be handled | Yes, by the caller | No |
| The host sees | The error's category and code | Only that a trap happened: category `03`, and no data |

For anything that can go wrong, then, you decide whether it should be an error or a trap. If the host can cause it, with a short request, an unknown command, a wrong PIN or an amount that's too large, make it an `Err`. The host sent bad input and deserves an answer it can act on, so check for it with `require` or use a checked intrinsic. If it could only happen through a bug in the applet, say an index the code has already checked, or a sum that can't overflow given the limits enforced earlier, you can leave it to trap. The trap stops the command before it does any damage with a wrong value.

## `Err` undoes nothing

Returning `Err` doesn't roll anything back (*OUT-20*). Whatever the function changed before it returned stays changed, whether that's persistent state, session state or something written through an `inout`.

Chapter 4's `increment` has exactly this bug. It adds 1 to the counter and then calls `read_counter`, which can fail if the response is too small. The host gets an error, but the counter has gone up anyway. The way to avoid it is to check everything that can fail before you change anything. When several changes have to happen together or not at all, you need a transaction, and those are in [chapter 6](06-state.md).

## The vault handles its errors

The vault gets one new error, and an `increment` that does its checks first and reports the end of the counter as an error the host can see. Replace `VaultError` and `increment`:

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

Both `require` lines now come first, so a request that's going to fail leaves the counter alone. `checked_add` has replaced `+`. Once the counter reaches 4 294 967 295 it can't go any higher, and where `+` would have trapped, the host now gets `CounterExhausted` and the counter keeps its value. The `Err(other)` arm passes on anything else. Here `checked_add` can only return `Overflow`, but the catch-all is required anyway, and passing on an error you didn't expect is the safe choice.

A scenario can't increment the counter four billion times, which is why the tally applet above tests this pattern instead. It can check the first fix, though: a response that's too small no longer moves the counter.

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

There's still a gap in `verify_pin`. It answers `WrongPin` to any wrong PIN, as often as the host likes. A real device limits the guesses, and for that the vault has to remember them, even when the power goes off. That's [chapter 6](06-state.md).
