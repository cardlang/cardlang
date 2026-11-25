# 6. State that survives

A device can lose power at any moment. A card gets pulled out of a reader, a battery runs flat, or the device is reset. This chapter is about the state that has to survive all that, and how CardLang makes sure it's never left half-written. By the end, the vault has a PIN the user can change, it limits wrong guesses, and it keeps a secret that only the right PIN unlocks.

## Four kinds of storage

| Declared as | Where | Lives | Starts as |
|---|---|---|---|
| `const` | Top level | Forever; never changes | Its initializer |
| `persistent` | Top level | Across commands, resets and power loss | Its default, once, when the applet's state is created |
| `session` | Top level | From the start of a session to its end | Its default, at every session start |
| `var` | In a function | Until the end of its block | Its initializer, or its default |

The platform decides what a *session* is. On a smart card it lasts from power-on to power-off, and other devices define their own start and end (*STA-4*). Something like "the PIN has been verified" belongs in session state, because it mustn't outlive the power going off.

## Starting values: lifecycle handlers

You can't give a `persistent` or `session` declaration an initializer (*STA-2*). Such a declaration has a single form, and starts out at its type's default:

<!-- check: error CE-STA-1 -->
```cardlang title="Does not compile: CE-STA-1"
persistent tries: u8 = 3;
```

If state needs to start with some other value, you set it in a *lifecycle handler*. That's a function with a reserved name, which the platform calls at a particular moment (*STA-5*, *STA-6*):

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

You don't have to define either handler. Your code never calls one, because only the platform does (*STA-9*). If a handler and a command need the same logic, put it in an ordinary function that both of them call.

## A persistent write is all or nothing

Every assignment to persistent state is *atomic* (*STA-11*). If the power fails in the middle of the write, the destination ends up with either its old value or its new one, never a mixture. That includes assigning a whole array or structure, so `pin = fill(0);` writes all of its bytes in one atomic step.

Two separate assignments aren't atomic together, though (*STA-12*). Suppose the vault stored a new PIN and then its length:

<!-- check: none -->
```cardlang title="Contains a bug"
pin[0..new_length] = new_pin;
pin_length = new_length;
```

If the power were cut between those two lines, the new PIN would be stored with the old length. Neither the old PIN nor the new one would work after that, and the vault would be locked for good.

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

Writes inside the block are *pending*. Code in the block, including any function it calls, already sees them. At the closing brace the transaction *commits*, and all of its writes take effect at once. If the power fails at any point before or during the commit, none of them do (*TXN-13*). Only persistent state takes part. Session state and local variables change as the code runs, and are never rolled back (*TXN-4*). A command isn't a transaction in itself (*TXN-5*), so put a transaction around exactly the writes that have to stay consistent with each other.

### Leaving a transaction early

`abort Err(…)` rolls back all the pending writes and returns the error (*TXN-7*, *TXN-8*). Inside a transaction, a `require` or an `attempt` that fails aborts in the same way (*TXN-18*):

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

If there isn't enough in `savings`, the `require` aborts the transaction, and the earlier `current += amount` is rolled back along with it.

You can't `return` from inside a transaction, and a `break` or `continue` can't leave one either (*TXN-6*). A transaction ends at its closing brace or with an abort, and nowhere else:

<!-- check: error CE-TXN-1 -->
```cardlang title="Does not compile: CE-TXN-1"
persistent value: u32;

function set(next: u32) -> u32 {
    transaction {
        value = next;
        return Ok(value);
    }
}
```

Nor can transactions be nested (*TXN-10*). Opening one inside another is an error, even when the inner one is in a function that the outer block calls. There's only ever one transaction at a time.

## The vault keeps a PIN

Time for the vault's real PIN. It's kept in persistent state, it's 4 to 8 digits long, and it allows 3 tries. A correct PIN sets a session flag, `verified`, which the secret commands at the end of the chapter look at. Replace `VaultError`, delete the `PIN` constant, and add the new state:

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

`on_install` sets a default PIN, `1234`, which the user is meant to change. `verified` needs no setting up. It's session state, so it's `false` whenever a session starts.

### Checking a PIN

Checking a PIN takes two functions. The first only makes sure the candidate *looks* like a PIN, and the second compares it with the stored one:

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

What matters most in `check_pin` is the order of its lines:

1. The format is checked first. A malformed PIN isn't a guess, and doesn't use up a try.
2. A blocked PIN is refused, even if it's the right one.
3. `tries` goes down *before* the comparison.
4. Only a correct PIN restores the tries and sets `verified`.

The third step is the one to understand. Suppose `tries` only went down after a wrong answer. An attacker could make a guess, watch the device, and cut the power the moment the guess turned out wrong, before the decrement was written. Every guess would be free. With the decrement written first, it's already stored, atomically, by the time the comparison runs, so cutting the power can lose a try but never save one.

Each of these writes stands on its own, and each is atomic, so there's no need for a transaction. At no point can a power cut leave the PIN usable with more tries than it should have.

`verify_pin` now calls `check_pin`. Since an error carries no data, the host needs another way to find out how many tries are left, so an empty verify request answers with that number:

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

The new command `24` changes the PIN. Its data is the length of the old PIN, then the old PIN, then the new one. `24 04 31 32 33 34 39 38 37 36 35`, for example, changes `1234` to `98765`.

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

The format of the new PIN is checked before the old PIN, so a typo in the new one doesn't cost a try. The old PIN goes through `check_pin`, which means a wrong one counts as a guess, just as it does in `verify_pin`. Then the PIN and its length are written in a single transaction. That's the case from the start of the chapter, and now a power cut leaves either the old PIN or the new one, never a mixture.

### A secret behind the PIN

At last, the thing the vault exists for: a secret of up to 32 bytes, which can only be stored or read once the PIN has been verified in the current session.

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

The new commands need variants in `Command`, lines in `decode` and arms in `process`. Replace all three:

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

If you add the `ChangePin` variant before its arm, the compiler points at the `match` in `process` until the arm is there. That's the rule from chapter 2 that every `match` lists every variant, doing its job.

### Trying it

This scenario takes the PIN through its whole life:

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

This one cuts the power in the middle of changing the PIN. `interrupt` makes the next commit fail as though the power had gone, and `expect none` says the host got no answer at all:

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

The writes made before the transaction did happen. `check_pin` had accepted the old PIN, so the tries were restored. The transaction, which held the new PIN and its length, never committed, though, so the old PIN is still the PIN.

You can see what the transaction is worth by taking it out of `change_pin` and running this scenario again. It fails, because `interrupt` cuts the power at a transaction's commit and there's no longer a commit to cut. On a real device the power can go at any instant, including between the two writes.
