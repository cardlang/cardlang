# 6. State that survives

A device running your applet can lose power at any moment: a card pulled from a reader, a battery running out, a reset. This chapter is about the state that must survive that, and how CardLang makes sure it is never left half-written. By the end, the vault keeps a PIN the user can change, limits wrong guesses, and guards a stored secret behind the PIN.

## Four kinds of storage

| Declared as | Where | Lives | Starts as |
|---|---|---|---|
| `const` | Top level | Forever; never changes | Its initializer |
| `persistent` | Top level | Across commands, resets and power loss | Its default, once, when the applet's state is created |
| `session` | Top level | From the start of a session to its end | Its default, at every session start |
| `var` | In a function | Until the end of its block | Its initializer, or its default |

A *session* is defined by the platform. On a smart card, it runs from power-on to power-off; on other devices, the platform says when one starts and ends (*STA-4*). Session state is the right place for something like "the PIN was verified": it must not outlive the power going off.

## Starting values: lifecycle handlers

A `persistent` or `session` declaration never has an initializer (*STA-2*). There is exactly one form, and it starts at the type's default:

<!-- check: error CE-STA-1 -->
```cardlang
persistent tries: u8 = 3;
```

State that should start with another value is set up by a *lifecycle handler*: a function with a reserved name, which the platform calls at a particular moment (*STA-5*, *STA-6*):

| Handler | Runs |
|---|---|
| `function on_install()` | Once, after the applet's persistent state is created |
| `function on_session_start()` | At every session start, after session state is reset to its defaults |

<!-- check: fragment -->
```cardlang
persistent tries: u8;
session attempts_this_session: u8;

function on_install() {
    tries = 3;
    return Ok();
}
```

Defining a handler is optional. Your code never calls one: only the platform does (*STA-9*). Put logic that both a handler and a command need in an ordinary function they both call.

## A persistent write is all or nothing

Every assignment to persistent state is *atomic* (*STA-11*). If the power fails during the write, the destination afterwards holds either its old value or its new one, never a mixture. That holds for an assignment to a whole array or structure too: `pin = fill(0);` is one atomic write of all its bytes.

Two separate assignments, however, are not atomic together (*STA-12*). Suppose the vault stores a new PIN and then its length:

<!-- check: none -->
```cardlang
pin[0..new_length] = new_pin;
pin_length = new_length;
```

A power cut between the two lines leaves a new PIN with the old length. Neither the old PIN nor the new one would then work, and the vault would be locked for good.

## Transactions

A `transaction` block makes several persistent writes take effect together (*TXN-1*, *TXN-3*):

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

- **Inside the block,** writes are *pending*. Reads in the block, and in functions it calls, see them.
- **At the closing brace,** the transaction *commits*: all its writes take effect at once. If the power fails at any point before or during the commit, none of them do (*TXN-13*).
- **Only persistent state takes part.** Session state and local variables are changed as you go, and are never rolled back (*TXN-4*).
- **A command is not a transaction by itself** (*TXN-5*). Use a transaction exactly where several writes must stay consistent.

### Leaving a transaction early

`abort Err(…)` rolls back every pending write, and returns the error (*TXN-7*, *TXN-8*). Inside a transaction, a failing `require` or `attempt` aborts in the same way (*TXN-18*):

<!-- check: fragment -->
```cardlang
errors WalletError {
    InsufficientFunds = 1;
}

persistent savings: u32;
persistent current: u32;

function transfer(amount: u32) {
    transaction {
        current += amount;
        require amount <= savings else WalletError.InsufficientFunds;
        savings -= amount;
    }
    return Ok();
}
```

If `savings` is too small, the `require` aborts, and `current += amount` is rolled back with it.

`return` is not allowed inside a transaction, nor a `break` or `continue` that would leave it (*TXN-6*). A transaction ends at its closing brace, or with an abort, and nowhere else:

<!-- check: error CE-TXN-1 -->
```cardlang
persistent value: u32;

function set(next: u32) -> u32 {
    transaction {
        value = next;
        return Ok(value);
    }
}
```

Transactions do not nest (*TXN-10*). A transaction inside another, including one in a function the block calls, is an error: one transaction at a time is the whole model.

## The vault keeps a PIN

Now the vault gets its real PIN. It is stored in persistent state, from 4 to 8 digits long, with 3 tries. A correct PIN sets a session flag, `verified`, which the secret commands at the end of the chapter check. Replace `VaultError`, remove the `PIN` constant, and add the state:

<!-- check: program vault remove=PIN -->
```cardlang
errors VaultError {
    MalformedRequest = 1;
    UnsupportedCommand = 2;
    ResponseTooSmall = 3;
    WrongPin = 4;
    CounterExhausted = 5;
    Blocked = 6;
    NotVerified = 7;
}

const MAX_TRIES: u8 = 3;
const MIN_PIN_LENGTH: u32 = 4;
const MAX_PIN_LENGTH: u32 = 8;
const DEFAULT_PIN: u8[4] = b"1234";

persistent pin: u8[MAX_PIN_LENGTH];
persistent pin_length: u32;
persistent tries: u8;
session verified: bool;

function on_install() {
    transaction {
        pin[0..4] = DEFAULT_PIN;
        pin_length = DEFAULT_PIN.length;
        tries = MAX_TRIES;
    }
    return Ok();
}
```

`on_install` gives the vault a default PIN, `1234`, which the user is expected to change. `verified` needs no setup: as session state, it is `false` at the start of every session.

### Checking a PIN

The check is split in two. The first function only checks that a candidate *looks like* a PIN; the second compares it with the stored one:

<!-- check: program vault -->
```cardlang
function check_pin_format(candidate: ref u8[]) {
    require candidate.length >= MIN_PIN_LENGTH else VaultError.MalformedRequest;
    require candidate.length <= MAX_PIN_LENGTH else VaultError.MalformedRequest;
    for index: u32 in 0..candidate.length {
        require (candidate[index] >= 0x30) and (candidate[index] <= 0x39) else VaultError.MalformedRequest;
    }
    return Ok();
}

function check_pin(candidate: ref u8[]) {
    attempt check_pin_format(ref candidate);
    require tries > 0 else VaultError.Blocked;
    verified = false;
    tries -= 1;
    require candidate.length == pin_length else VaultError.WrongPin;
    require equal(ref candidate, ref pin[0..pin_length]) else VaultError.WrongPin;
    tries = MAX_TRIES;
    verified = true;
    return Ok();
}
```

The order of the lines in `check_pin` is the point of this section:

1. **The format is checked first.** A malformed PIN is not a guess, and costs no try.
2. **A blocked PIN stops everything,** even the right one.
3. **`tries` goes down *before* the comparison.** Suppose it went down only after a wrong answer. An attacker could then guess, watch the device, and cut the power the instant a guess turned out wrong, before the decrement was written. Every guess would be free. Written first, the decrement is already stored, atomically, when the comparison runs: cutting the power can only lose a try, never save one.
4. **A correct PIN restores the tries,** and only then sets `verified`.

Each write here stands alone, and each is atomic, so no transaction is needed: there is no moment at which a power cut leaves the PIN usable with tries it should not have.

`verify_pin` now uses `check_pin`. An empty verify request asks how many tries are left: since an error carries no data, this is how the host finds out:

<!-- check: program vault -->
```cardlang
function verify_pin(data: ref u8[], response: inout u8[]) -> u32 {
    if data.length == 0 {
        require response.length >= 1 else VaultError.ResponseTooSmall;
        response[0] = tries;
        return Ok(1);
    }
    attempt check_pin(ref data);
    return Ok(0);
}
```

### Changing the PIN

Command `24` changes the PIN. Its data is the old PIN's length, the old PIN, and the new PIN, so `24 04 31 32 33 34 39 38 37 36 35` changes `1234` to `98765`:

<!-- check: program vault -->
```cardlang
function change_pin(data: ref u8[], response: inout u8[]) -> u32 {
    require data.length >= 1 else VaultError.MalformedRequest;
    var split: u32 = 1 + convert<u32>(data[0]);
    require split <= data.length else VaultError.MalformedRequest;
    attempt check_pin_format(ref data[split..data.length]);
    attempt check_pin(ref data[1..split]);
    var new_length: u32 = data.length - split;
    transaction {
        pin = fill(0);
        pin[0..new_length] = data[split..data.length];
        pin_length = new_length;
    }
    return Ok(0);
}
```

- **The new PIN's format is checked before the old PIN,** so a typo in the new PIN does not cost a try.
- **The old PIN is checked with `check_pin`,** so a wrong one counts as a guess, exactly as in `verify_pin`.
- **The PIN and its length are written in one transaction.** This is the case from the start of the chapter: a power cut now leaves the old PIN or the new one, never a mixture.

### A secret behind the PIN

Finally, what the vault is for: a secret of up to 32 bytes, which can only be stored or read after the PIN has been verified in the current session:

<!-- check: program vault -->
```cardlang
const MAX_SECRET_LENGTH: u32 = 32;

persistent secret: u8[MAX_SECRET_LENGTH];
persistent secret_length: u32;

function store_secret(data: ref u8[], response: inout u8[]) -> u32 {
    require verified else VaultError.NotVerified;
    require data.length <= MAX_SECRET_LENGTH else VaultError.MalformedRequest;
    transaction {
        secret = fill(0);
        secret[0..data.length] = data;
        secret_length = data.length;
    }
    return Ok(0);
}

function read_secret(data: ref u8[], response: inout u8[]) -> u32 {
    require data.length == 0 else VaultError.MalformedRequest;
    require verified else VaultError.NotVerified;
    require response.length >= secret_length else VaultError.ResponseTooSmall;
    response[0..secret_length] = secret[0..secret_length];
    return Ok(secret_length);
}
```

### Wiring up the commands

The new commands need variants, decoding and dispatch. Replace `Command`, `decode` and `process`:

<!-- check: program vault -->
```cardlang
enum Command {
    ReadCounter;
    Increment;
    VerifyPin;
    ChangePin;
    StoreSecret;
    ReadSecret;
}

function decode(code: u8) -> Command {
    if code == 0x01 {
        return Ok(Command.ReadCounter);
    } else if code == 0x02 {
        return Ok(Command.Increment);
    } else if code == 0x20 {
        return Ok(Command.VerifyPin);
    } else if code == 0x24 {
        return Ok(Command.ChangePin);
    } else if code == 0xD0 {
        return Ok(Command.StoreSecret);
    } else if code == 0xCA {
        return Ok(Command.ReadSecret);
    }
    return Err(VaultError.UnsupportedCommand);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length >= 1 else VaultError.MalformedRequest;
    var operation: Command = attempt decode(request[0]);
    match operation {
        Command.ReadCounter => {
            return read_counter(ref request[1..request.length], inout response);
        }
        Command.Increment => {
            return increment(ref request[1..request.length], inout response);
        }
        Command.VerifyPin => {
            return verify_pin(ref request[1..request.length], inout response);
        }
        Command.ChangePin => {
            return change_pin(ref request[1..request.length], inout response);
        }
        Command.StoreSecret => {
            return store_secret(ref request[1..request.length], inout response);
        }
        Command.ReadSecret => {
            return read_secret(ref request[1..request.length], inout response);
        }
    }
}
```

When you add the `ChangePin` variant, the compiler points at the `match` in `process` until it has an arm for it: the exhaustive `match` of chapter 2, earning its keep.

### Trying it

This scenario walks through the whole life of the PIN:

<!-- check: scenario vault -->
```scenario
install
power_on
command 20              # tries left
expect ok 03
command 20 31 32 33 35  # a wrong PIN costs a try
expect err app 4
command 20
expect ok 02
command 20 31 32 33 34  # the right one restores them
expect ok
command 20
expect ok 03
command D0 73 65 63 72 65 74      # store "secret"
expect ok
command CA
expect ok 73 65 63 72 65 74
power_on                # a new session: no longer verified
command CA
expect err app 7
command 24 04 31 32 33 34 39 38 37 36 35   # change 1234 to 98765
expect ok
command 20 31 32 33 34
expect err app 4
command 20 39 38 37 36 35
expect ok
command 20 31 31 31 31  # three wrong guesses
expect err app 4
command 20 31 31 31 31
expect err app 4
command 20 31 31 31 31
expect err app 4
command 20              # no tries left
expect ok 00
command 20 39 38 37 36 35   # blocked, even with the right PIN
expect err app 6
```

And this one cuts the power in the middle of a PIN change. `interrupt` makes the next commit fail as if the power were lost, and `expect none` says the host got no answer at all:

<!-- check: scenario vault -->
```scenario
install
power_on
interrupt during-commit
command 24 04 31 32 33 34 39 38 37 36   # power lost during the change
expect none
power_on
command 20 39 38 37 36  # the new PIN was never stored
expect err app 4
command 20 31 32 33 34  # the old one still works
expect ok
```

The writes made before the transaction stayed: `check_pin` had accepted the old PIN, so the tries were restored. The transaction itself, the new PIN and its length, never committed, so the old PIN is still the PIN.

## What next

- Remove the `transaction` from `change_pin`, and run the interrupted scenario again. It fails: `interrupt` cuts the power at a transaction's commit, and now there is none in the command. On a real device, the power can go at any instant. What could a cut between the two writes leave behind?
- A blocked vault is blocked for good. Add an unblock command with a second, longer code (a *PUK*), with its own tries.
- `on_session_start` is not used. What could the vault use it for?
