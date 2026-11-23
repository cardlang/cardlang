# 4. Functions, references and views

The vault's `process` does everything itself, and each new command makes it longer. In this chapter you split it into functions, one per command. Along the way you meet the three ways a function can take its parameters, and see why CardLang's references are safer than C's pointers.

## Functions

A function names its parameters and their types, and the type of its result after `->`:

<!-- check: fragment -->
```cardlang
function average(a: u32, b: u32) -> u32 {
    var sum: u32 = a + b;
    return Ok(sum / 2);
}

function larger(a: u32, b: u32) -> u32 {
    if a > b {
        return Ok(a);
    }
    return Ok(b);
}
```

A function returns its result as `Ok(…)`. Every function can also fail, by returning `Err(…)`, so a call's result is an *outcome*: either `Ok` with a value, or `Err` with an error. [Chapter 5](05-outcomes.md) is about outcomes. In this chapter, you call a function with `attempt`, which takes the value of `Ok`, and passes an `Err` straight on to the caller:

<!-- check: fragment -->
```cardlang
function average(a: u32, b: u32) -> u32 {
    var sum: u32 = a + b;
    return Ok(sum / 2);
}

function middle(low: u32, high: u32) -> u32 {
    var centre: u32 = attempt average(low, high);
    return Ok(centre);
}
```

A function with nothing to return leaves out `->`, and returns `Ok()`. It is called with `attempt` as a statement of its own:

<!-- check: fragment -->
```cardlang
session total: u32;

function add(amount: u32) {
    total = total + amount;
    return Ok();
}

function add_twice(amount: u32) {
    attempt add(amount);
    attempt add(amount);
    return Ok();
}
```

Like every top-level declaration, a function can be called before it is declared, and from any of the applet's files ([chapter 3](03-control-flow-and-scope.md#an-applets-files)). A function cannot be passed around as a value: there are no function pointers or callbacks, and every call names the function it calls (*FUN-4*).

### No recursion

A function may not call itself, directly or through other functions (*FUN-5*):

<!-- check: error CE-FUN-1 -->
```cardlang
function countdown(n: u32) {
    if n > 0 {
        attempt countdown(n - 1);
    }
    return Ok();
}
```

That is what lets the compiler work out the deepest chain of calls the applet can make, and so the exact stack it needs: the "stack 44" that Build Applet printed in chapter 1. A device with a few kilobytes of RAM cannot afford to find out at runtime. Write a loop instead.

### One call at a time

A call cannot appear in the arguments of another call (*EXP-49*):

<!-- check: error CE-EXP-7 -->
```cardlang
function average(a: u32, b: u32) -> u32 {
    var sum: u32 = a + b;
    return Ok(sum / 2);
}

function mean_of_three(a: u32, b: u32, c: u32) -> u32 {
    return Ok(attempt average(attempt average(a, b), c));
}
```

The rule covers intrinsics too: `encode_be(wrapping_add(a, b))` is an error as well. Give the inner result a name first, with `var`. Every call then has its own line, and the order in which things happen is the order in which they are written.

## Parameter modes

A parameter has one of three *modes*, which say what the function may do with the caller's data (*FUN-6*):

| Mode | Written | The function gets | It can change the caller's data |
|---|---|---|---|
| By value | `name: T` | A copy | No |
| `ref` | `name: ref T` | Read access to the caller's own storage | No |
| `inout` | `name: inout T` | Read and write access to the caller's own storage | Yes |

The mode is written at the call too, so a reader sees at the call what it may change (*FUN-7*):

<!-- check: fragment -->
```cardlang
struct Account {
    balance: u32;
    owner: u8[16];
}

function balance_of(account: ref Account) -> u32 {
    return Ok(account.balance);
}

function deposit(account: inout Account, amount: u32) {
    account.balance = account.balance + amount;
    return Ok();
}

function example() -> u32 {
    var savings: Account;
    attempt deposit(inout savings, 100);
    var balance: u32 = attempt balance_of(ref savings);
    return Ok(balance);
}
```

- **By value** is the right mode for small values, such as numbers. The function gets its own copy, which it can read but not assign to. Copy it into a `var` to change it.
- **`ref`** avoids copying something large, such as a structure or an array, when the function only reads it.
- **`inout`** is for a function whose job is to change something of the caller's, like `deposit`.

Each mode is checked. Leaving out the `inout` at the call, for example, is an error, and so is writing through a `ref`:

<!-- check: error CE-FUN-2 -->
```cardlang
function reset(value: inout u32) {
    value = 0;
    return Ok();
}

function example() {
    var count: u32 = 5;
    attempt reset(count);
    return Ok();
}
```

<!-- check: error CE-STM-2 -->
```cardlang
function reset(value: ref u32) {
    value = 0;
    return Ok();
}
```

A `ref` or `inout` argument must be storage that exists: a variable, a global, a parameter, or a field, element or slice of one. A constant can be passed as `ref`, but never as `inout` (*FUN-9*, *FUN-10*).

### References are not pointers

A `ref` or `inout` parameter refers to the caller's storage only for the duration of the call (*FUN-16*). A reference cannot be stored in a variable, kept in a global, or returned. There are no null references and no pointer arithmetic. So a reference can never point at something that no longer exists.

What references *can* do is overlap. Passing the same variable twice, as `ref` and as `inout`, is allowed, and a read through the `ref` sees each write made through the `inout` (*FUN-12*, *FUN-13*):

<!-- check: fragment -->
```cardlang
function double_into(source: ref u32, target: inout u32) {
    target = source + source;
    return Ok();
}

function example() -> u32 {
    var value: u32 = 3;
    attempt double_into(ref value, inout value);    // value becomes 6
    return Ok(value);
}
```

That is why a function should not assume a `ref` parameter stays the same while it writes through another one. When it matters, copy the value into a local first.

## Views

A function that takes `u8[4]` accepts exactly four bytes. To accept an array of any length, the parameter is a *view*, `T[]`, with no length. A view is always a `ref` or `inout` parameter, and its `.length` tells the function how long it is:

<!-- check: fragment -->
```cardlang
function checksum(data: ref u8[]) -> u8 {
    var sum: u8;
    for index: u32 in 0..data.length {
        sum = wrapping_add(sum, data[index]);
    }
    return Ok(sum);
}

function example() -> u8 {
    var block: u8[16] = fill(0x01);
    var whole: u8 = attempt checksum(ref block);            // all 16 bytes
    var head: u8 = attempt checksum(ref block[0..4]);       // the first 4
    return Ok(wrapping_add(whole, head));
}
```

A view accepts a whole array of any length, or a slice. A slice passed this way is not copied: the function works on the caller's bytes. You have used views since chapter 1: `process` takes the request as `ref u8[]`, and the response as `inout u8[]`.

A view can only be a parameter. A variable, a field or a result cannot have a view type, because a view, like any reference, lives only as long as the call:

<!-- check: error CE-TYP-5 -->
```cardlang
function first_half(data: ref u8[]) -> u8[] {
    return Ok(data);
}
```

## The vault, one function per command

Now the vault. Each command becomes a function with the same two parameters: the request's data after its command byte, as a `ref u8[]`, and the response, as an `inout u8[]`. Each checks its own data, and returns the length of its answer. Add them to `vault.card`:

<!-- check: program vault -->
```cardlang
function read_counter(data: ref u8[], response: inout u8[]) -> u32 {
    require data.length == 0 else VaultError.MalformedRequest;
    require response.length >= 4 else VaultError.ResponseTooSmall;
    response[0..4] = encode_be(counter);
    return Ok(4);
}

function increment(data: ref u8[], response: inout u8[]) -> u32 {
    require data.length == 0 else VaultError.MalformedRequest;
    counter += 1;
    return read_counter(ref data, inout response);
}

function verify_pin(data: ref u8[], response: inout u8[]) -> u32 {
    require data.length == PIN.length else VaultError.MalformedRequest;
    for index: u32 in 0..data.length {
        require (data[index] >= 0x30) and (data[index] <= 0x39) else VaultError.MalformedRequest;
    }
    require equal(ref data, ref PIN) else VaultError.WrongPin;
    return Ok(0);
}
```

- **`increment` ends with `return read_counter(…)`.** It answers with the counter too, so it hands over to `read_counter`, and returns whatever `read_counter` returns: the length, or an error. This is a *forwarding return*, and [chapter 5](05-outcomes.md) has more on it.
- **`data` is passed on as `ref data`.** A function can pass its own references to the functions it calls.
- **`verify_pin` takes a `response` it does not use.** Every command function has the same shape, so `process` can treat them alike.

`process` shrinks to decoding the request, and choosing the function:

<!-- check: program vault -->
```cardlang
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
    }
}
```

`request[1..request.length]` is the request without its command byte. Passed as `ref`, it is a view of the request itself, not a copy.

The applet does exactly what it did before. Run the scenario from chapter 3 to check:

<!-- check: scenario vault -->
```scenario
install
power_on
command 02              # increment
expect ok 00 00 00 01
command 01 capacity 2   # no room for the answer
expect err app 3
command 20 31 32 33 34  # verify "1234"
expect ok
command 20 31 32 33 35
expect err app 4
command 20 31 32 33
expect err app 1
command 20 31 32 41 34  # not all digits
expect err app 1
command 01 FF           # read takes no data
expect err app 1
command 07
expect err app 2
```

A scenario like this is the safety net for a change that should not change behaviour. When you restructure code, run it before and after.

## What next

- Add a command `03` that resets the counter to zero, as a function of the same shape. Where does it need a change besides its own function?
- Write `checksum` from the Views section as a command: it answers the checksum of the request's data, in one byte.
- `increment` changes the counter before `read_counter` checks the response's length. With `command 02 capacity 2`, the counter goes up, and the host gets an error. Change `increment` so that a too-small response leaves the counter alone. [Chapter 5](05-outcomes.md) looks at why `Err` does not undo the change by itself.
