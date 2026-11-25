# 4. Functions, references and views

Every command the vault learns makes `process` longer, and it already does everything itself. In this chapter we split it up, one function per command. To do that you'll need the three ways a function can take its parameters, and a look at what CardLang's references can and can't do.

## Functions

A function lists its parameters with their types, and puts the type of its result after `->`:

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

The result comes back as `Ok(…)`. Any function can also fail, by returning `Err(…)`, so what a call gives you is an *outcome*, either `Ok` with a value or `Err` with an error. Outcomes have [chapter 5](05-outcomes.md) to themselves. For now, call functions with `attempt`, which hands you the value inside an `Ok` and sends an `Err` straight back to your own caller:

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

A function that has nothing to return leaves out the `->` and returns `Ok()`. You call it with `attempt` as a statement on its own line:

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

You can call a function before its declaration, and from any of the applet's files, as with every top-level declaration ([chapter 3](03-control-flow-and-scope.md#an-applets-files)). Functions aren't values, though. You can't pass one around, there are no callbacks, and every call names the function it calls (*FUN-4*).

### No recursion

A function can't call itself, either directly or by way of other functions (*FUN-5*):

<!-- check: error CE-FUN-1 -->
```cardlang
function countdown(n: u32) {
    if n > 0 {
        attempt countdown(n - 1);
    }
    return Ok();
}
```

Without recursion, the compiler can find the deepest chain of calls an applet can make, and from that the stack it needs. That's where the "stack 44" from Build Applet in chapter 1 came from. On a device with a few kilobytes of RAM, running out of stack isn't something to discover at runtime. Use a loop instead.

### One call at a time

You can't put a call inside the arguments of another call (*EXP-49*):

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

That goes for intrinsics as well, so `encode_be(wrapping_add(a, b))` is also an error. Store the inner result in a `var` first. With every call on its own line, things happen in the order they're written.

## Parameter modes

Each parameter has a *mode*, which says what the function may do with the caller's data (*FUN-6*):

| Mode | Written | The function gets | It can change the caller's data |
|---|---|---|---|
| By value | `name: T` | A copy | No |
| `ref` | `name: ref T` | Read access to the caller's own storage | No |
| `inout` | `name: inout T` | Read and write access to the caller's own storage | Yes |

You write the mode at the call as well, so anyone reading the call can see what it might change (*FUN-7*):

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

Small values such as numbers are best passed by value. The function gets a copy it can read but not assign to, and if it wants to change it, it copies it into a `var`. `ref` saves copying something large, like a structure or an array, that the function only needs to read. `inout` is for a function whose job is to change something that belongs to the caller, as `deposit` does.

The compiler checks the modes. It rejects a call that leaves out an `inout`, and a function that writes through a `ref`:

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

An argument passed as `ref` or `inout` has to be real storage: a variable, a global, a parameter, or a field, element or slice of one of those. Constants can be passed as `ref`, but never as `inout` (*FUN-9*, *FUN-10*).

### References are not pointers

A `ref` or `inout` parameter refers to the caller's storage only while the call lasts (*FUN-16*). You can't store a reference in a variable or a global, and you can't return one. There are no null references and no pointer arithmetic either, so a reference can never point at something that has gone away.

References can overlap, however. You may pass the same variable twice, once as `ref` and once as `inout`, and a read through the `ref` then sees every write made through the `inout` (*FUN-12*, *FUN-13*):

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

So a function shouldn't count on a `ref` parameter staying the same while it writes through another parameter. If it matters, copy the value into a local first.

## Views

A parameter of type `u8[4]` takes exactly four bytes. To take an array of any length, give the parameter a *view* type, `T[]`, which has no length. A view is always a `ref` or `inout` parameter, and the function finds out how long it is from `.length`:

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

You can pass a whole array of any length as a view, or a slice. A slice isn't copied, and the function works directly on the caller's bytes. In fact you've been using views since chapter 1, because `process` receives the request as a `ref u8[]` and the response as an `inout u8[]`.

Only parameters can be views. A variable, a field or a function's result can't have a view type, because a view lives only as long as the call, like any reference:

<!-- check: error CE-TYP-5 -->
```cardlang
function first_half(data: ref u8[]) -> u8[] {
    return Ok(data);
}
```

## The vault, one function per command

Back to the vault. Each command becomes a function, and they all take the same two parameters: the request's data after the command byte, as a `ref u8[]`, and the response, as an `inout u8[]`. Each function checks its own data and returns the length of its answer. Add them to `vault.card`:

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

`increment` answers with the counter too, so it finishes by handing over to `read_counter`, and returns whatever `read_counter` returns, whether that's a length or an error. This is called a *forwarding return*, and [chapter 5](05-outcomes.md) says more about it. Notice that `increment` passes its own reference on as `ref data`, which any function can do. `verify_pin` takes a `response` it never uses, so that all the command functions look alike and `process` can treat them the same way.

All that's left for `process` is to decode the request and pick a function:

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

`request[1..request.length]` is the request minus its command byte. It's passed as `ref`, so each function sees the request itself and nothing is copied.

The applet should behave as it did at the end of chapter 3, and running its scenario confirms that:

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

Keep a scenario like this one handy whenever you restructure code, and run it before and after the change.
