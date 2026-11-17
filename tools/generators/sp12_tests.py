"""Write the SP12 runtime conformance tests (conformance/runtime/*) and cross-check them with chapter 13."""
import re, sys, pathlib
# Tests written by sp14_tests.py are referenced in this chapter but owned by that generator.
SP14_OWNED = set((pathlib.Path(__file__).parent / "sp14_owned.txt").read_text().split())
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance" / "runtime"
ch13 = (repo / "spec" / "13-runtime-failures.md").read_text(encoding="utf-8")
ch12 = (repo / "spec" / "12-host-entry-point.md").read_text(encoding="utf-8")

def block(text, path):
    return re.search(r"\(conformance: `" + re.escape(path) + r"`\)\n\n```text\n(.*?)```", text, re.S).group(1)

T = {}
def add(name, rule, src, note, program, scenario, requires=None):
    T[name] = (rule, src, note, program, scenario, requires)

# ---------------------------------------------------------------- run-001
add("run-001-integer-traps", "RTF-4, EXP-23, EXP-24, EXP-25, EXP-26, EXP-30", "DN §3.5, §6.5",
"Integer traps and wrapping results, with operand values taken from the request.", """errors TestError {
    UnknownOperation = 1;
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    var a: u8 = request[1];
    var s: i8 = truncate<i8>(request[1]);
    if operation == 1 {
        var r: u8 = a + 1;
        response[0] = r;
        return Ok(1);
    } else if operation == 2 {
        var r: u8 = a - 1;
        response[0] = r;
        return Ok(1);
    } else if operation == 3 {
        var q: u8 = 100 / a;
        response[0] = q;
        return Ok(1);
    } else if operation == 4 {
        var q: i8 = s / -1;
        response[0] = truncate<u8>(q);
        return Ok(1);
    } else if operation == 5 {
        var r: i8 = s % -1;
        response[0] = truncate<u8>(r);
        return Ok(1);
    } else if operation == 6 {
        var shifted: u8 = 1 << a;
        response[0] = shifted;
        return Ok(1);
    } else if operation == 7 {
        var negated: i8 = -s;
        response[0] = truncate<u8>(negated);
        return Ok(1);
    } else if operation == 8 {
        var wrapped: u8 = wrapping_add(a, 10);
        response[0] = wrapped;
        return Ok(1);
    } else if operation == 9 {
        var q: i8 = s / 2;
        var r: i8 = s % 2;
        response[0] = truncate<u8>(q);
        response[1] = truncate<u8>(r);
        return Ok(2);
    }
    return Err(TestError.UnknownOperation);
}
""", """install
power_on
command 01 05
expect ok 06
command 01 ff        # 255 + 1
expect trap OVERFLOW
command 02 00        # 0 - 1 (unsigned)
expect trap UNDERFLOW
command 03 07        # 100 / 7
expect ok 0e
command 03 00
expect trap DIV-ZERO
command 04 80        # -128 / -1
expect trap OVERFLOW
command 05 80        # -128 % -1 is 0
expect ok 00
command 06 03
expect ok 08
command 06 08        # shift count equals the width
expect trap SHIFT
command 07 80        # -(-128)
expect trap NEGATION
command 08 fa        # wrapping 250 + 10
expect ok 04
command 09 f9        # -7 / 2 = -3, -7 % 2 = -1 (truncation toward zero)
expect ok fd ff
command 0a 00
expect err app 1
""")

# ---------------------------------------------------------------- run-002
add("run-002-checked-and-conversions", "EXP-29, EXP-33, EXP-34, EXP-36, EXP-37", "DN §3.2, §6.5; D-432",
"Checked intrinsics, conversions and the byte-order intrinsics.", """errors TestError {
    UnknownOperation = 1;
}

function put(output: inout u8[], bytes: ref u8[]) -> u32 {
    for index: u32 in 0..bytes.length {
        output[index] = bytes[index];
    }
    return Ok(bytes.length);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        var sum: u8 = attempt checked_add(request[1], 250);
        response[0] = sum;
        return Ok(1);
    } else if operation == 2 {
        var s: i8 = truncate<i8>(request[1]);
        var r: i8 = attempt checked_rem(s, -1);
        response[0] = truncate<u8>(r);
        return Ok(1);
    } else if operation == 3 {
        var wide: u16 = decode_be<u16>(ref request[1..3]);
        var narrow: u8 = attempt checked_convert<u8>(wide);
        response[0] = narrow;
        return Ok(1);
    } else if operation == 4 {
        var wide: u16 = decode_be<u16>(ref request[1..3]);
        response[0] = truncate<u8>(wide);
        return Ok(1);
    } else if operation == 5 {
        var value: u32 = decode_be<u32>(ref request[1..5]);
        var encoded: u8[4] = encode_be(value);
        return put(inout response, ref encoded);
    } else if operation == 6 {
        var value: u32 = decode_be<u32>(ref request[1..5]);
        var encoded: u8[4] = encode_le(value);
        return put(inout response, ref encoded);
    } else if operation == 7 {
        var value: u32 = decode_be<u32>(ref request[1..request.length]);
        response[0] = truncate<u8>(value);
        return Ok(1);
    }
    return Err(TestError.UnknownOperation);
}
""", """install
power_on
command 01 05
expect ok ff
command 01 0a        # 10 + 250 overflows u8
expect err platform Overflow
command 02 80        # checked_rem(-128, -1) is Ok(0)
expect ok 00
command 03 00 2a
expect ok 2a
command 03 01 2c     # 300 does not fit u8
expect err platform ConversionRange
command 04 12 34
expect ok 34
command 05 01 02 03 04
expect ok 01 02 03 04
command 06 01 02 03 04
expect ok 04 03 02 01
command 07 01 02     # two bytes for a u32
expect trap BOUNDS
""")

# ---------------------------------------------------------------- run-003
add("run-003-short-circuit-and-bounds", "EXP-21, EXP-39", "DN §3.5, §8.1",
"Short-circuiting prevents an out-of-range index; an unguarded index traps.", """session table: u8[4];

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var index: u8 = request[1];
    if request[0] == 1 {
        var free: bool = (index < 4) and (table[index] == 0);
        if free {
            response[0] = 1;
        } else {
            response[0] = 0;
        }
        return Ok(1);
    }
    response[0] = table[index];
    return Ok(1);
}
""", """install
power_on
command 01 02
expect ok 01
command 01 09        # out of range, but the index is never evaluated
expect ok 00
command 02 02
expect ok 00
command 02 09
expect trap BOUNDS
""")

# ---------------------------------------------------------------- run-004
add("run-004-assignment-order", "STM-9, STM-10", "DN §8.2; D-409",
"The destination path is evaluated and checked before the right-hand side.", """session values: u8[4];
session position: u32;
session touched: bool;

function advance() -> u8 {
    position = position + 1;
    touched = true;
    return Ok(7);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        values[position] = attempt advance();
        response[0] = values[0];
        response[1] = values[1];
        response[2] = truncate<u8>(position);
        return Ok(3);
    } else if operation == 2 {
        var index: u32 = convert<u32>(request[1]);
        values[index] = attempt advance();
        return Ok(0);
    }
    if touched {
        response[0] = 1;
    } else {
        response[0] = 0;
    }
    response[1] = truncate<u8>(position);
    return Ok(2);
}
""", """install
power_on
command 02 09        # bounds failure before the right-hand side runs
expect trap BOUNDS
command 03
expect ok 00 00      # advance() never ran
command 01           # values[0] chosen before advance() moves position to 1
expect ok 07 00 01
command 03
expect ok 01 01
""")

# ---------------------------------------------------------------- run-005
add("run-005-loops-and-locals", "STM-5, STM-14, STM-15", "DN §3.6, §3.9",
"Locals are re-initialized each time they are reached; empty ranges run zero times.", """command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        var total: u8 = 0;
        for index: u8 in 0..3 {
            var step: u8;
            step = step + 1;
            total = total + step;
        }
        response[0] = total;
        return Ok(1);
    } else if operation == 2 {
        var count: u8 = 0;
        var limit: u8 = request[1];
        for index: u8 in 5..limit {
            count = count + 1;
        }
        response[0] = count;
        return Ok(1);
    }
    var evens: u8 = 0;
    var current: u8 = 0;
    while current < request[1] {
        current = current + 1;
        if (current % 2) == 1 {
            continue;
        }
        evens = evens + 1;
    }
    response[0] = evens;
    return Ok(1);
}
""", """install
power_on
command 01           # step restarts at its default each iteration
expect ok 03
command 02 03        # 5..3 is empty
expect ok 00
command 02 08
expect ok 03
command 03 07        # 2, 4, 6
expect ok 03
""")

# ---------------------------------------------------------------- run-006
add("run-006-aliasing-and-slices", "FUN-12, FUN-14, FUN-20", "DN §3.8, §8.4",
"Observable aliasing through references, and slice bounds at runtime.", """session buffer: u8[16];

function update(target: inout u8, index: u32) {
    target = 1;
    buffer[index] = 2;
    return Ok();
}

function observe(source: ref u8, target: inout u8) -> u8 {
    target = 9;
    return Ok(source);
}

function total(data: ref u8[]) -> u32 {
    var sum: u32 = 0;
    for index: u32 in 0..data.length {
        sum = sum + convert<u32>(data[index]);
    }
    return Ok(sum + data.length);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        attempt update(inout buffer[0], 0);
        response[0] = buffer[0];
        return Ok(1);
    } else if operation == 2 {
        response[0] = attempt observe(ref buffer[1], inout buffer[1]);
        return Ok(1);
    }
    var start: u32 = convert<u32>(request[1]);
    var end: u32 = convert<u32>(request[2]);
    var sum: u32 = attempt total(ref buffer[start..end]);
    response[0] = truncate<u8>(sum);
    return Ok(1);
}
""", """install
power_on
command 01           # the write through the global wins: buffer[0] is 2
expect ok 02
command 02           # a ref is not a snapshot
expect ok 09
command 03 00 04     # 2 + 9 + 0 + 0, plus length 4
expect ok 0f
command 03 10 10     # empty slice at the end
expect ok 00
command 03 04 14     # end beyond the length
expect trap BOUNDS
command 03 08 04     # start after end
expect trap BOUNDS
""")

# ---------------------------------------------------------------- run-007
add("run-007-outcomes", "OUT-10, OUT-18, OUT-20", "DN §6.3",
"attempt propagates errors unchanged, and Err does not roll back.", """errors AppError {
    Rejected = 7;
}

persistent marker: u8;

function failing() -> u8 {
    marker = marker + 1;
    return Err(AppError.Rejected);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        var value: u8 = attempt failing();
        response[0] = value;
        return Ok(1);
    } else if operation == 2 {
        var sum: u8 = attempt checked_add(request[1], 255);
        response[0] = sum;
        return Ok(1);
    }
    response[0] = marker;
    return Ok(1);
}
""", """install
power_on
command 01
expect err app 7
command 03           # the write before Err was kept
expect ok 01
command 02 01        # a platform error keeps its category
expect err platform Overflow
command 02 00
expect ok ff
""")

# ---------------------------------------------------------------- run-008
add("run-008-state-lifecycle", "STA-3, STA-4, STA-6, RTF-2, RTF-9", "DN §3.9, §6.4",
"Persistent defaults once, session defaults at power-on, session kept by traps and cleared by reset.", """persistent installed: u8;
persistent counter: u8;
session level: u8;

function on_install() {
    installed = 5;
    return Ok();
}

function on_power_on() {
    level = 3;
    return Ok();
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 2 {
        counter = counter + 1;
        level = level + 1;
        return Ok(0);
    } else if operation == 3 {
        level = level + 1;
        var divisor: u8 = request[1];
        var quotient: u8 = 1 / divisor;
        return Ok(0);
    }
    response[0] = installed;
    response[1] = counter;
    response[2] = level;
    return Ok(3);
}
""", """install
power_on
command 01
expect ok 05 00 03
command 02
expect ok
command 01
expect ok 05 01 04
command 03 00        # increments level, then traps
expect trap DIV-ZERO
command 01           # the session change survived the trap
expect ok 05 01 05
reset
power_on
command 01           # session back to default plus on_power_on; persistent kept
expect ok 05 01 03
""")

# ---------------------------------------------------------------- run-009
add("run-009-transactions", "TXN-2, TXN-3, TXN-8, TXN-11, TXN-18", "DN §7.2",
"Commit, read-your-writes, abort and trap rollback, session changes surviving rollback, and attempt and require aborting a transaction.", """errors AppError {
    Refused = 1;
}

persistent a: u32;
persistent b: u32;
session notes: u8;

function refuse() {
    return Err(AppError.Refused);
}

function amount_of(flag: u8) -> u32 {
    if flag == 0 {
        return Err(AppError.Refused);
    }
    return Ok(convert<u32>(flag));
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        transaction {
            a = a + 1;
            b = a + 10;
        }
    } else if operation == 2 {
        transaction {
            a = a + 100;
            notes = notes + 1;
            match refuse() {
                Ok() => {
                }
                Err(error) => {
                    abort Err(error);
                }
            }
        }
    } else if operation == 4 {
        transaction {
            a = a + 50;
            var divisor: u32 = convert<u32>(request[1]);
            var quotient: u32 = 1 / divisor;
        }
    } else if operation == 5 {
        transaction {
            a = a + 7;
            var amount: u32 = attempt amount_of(request[1]);
            b = amount;
        }
    } else if operation == 6 {
        transaction {
            a = a + 9;
            require request[1] == 1 else AppError.Refused;
            b = 99;
        }
    }
    response[0] = truncate<u8>(a);
    response[1] = truncate<u8>(b);
    response[2] = notes;
    return Ok(3);
}
""", """install
power_on
command 01           # b reads the pending value of a
expect ok 01 0b 00
command 02
expect err app 1
command 03           # a rolled back; the session change survived
expect ok 01 0b 01
command 04 00
expect trap DIV-ZERO
command 03           # the trap rolled back the pending write
expect ok 01 0b 01
command 05 00        # attempt fails inside the transaction: it aborts (TXN-18)
expect err app 1
command 03           # a + 7 was rolled back
expect ok 01 0b 01
command 05 04        # attempt succeeds: the transaction commits
expect ok 08 04 01
command 06 00        # require fails inside the transaction: it aborts
expect err app 1
command 03
expect ok 08 04 01
""")

# ---------------------------------------------------------------- run-010
add("run-010-response-contract", "HEP-9", "DN §4",
"Only the counted bytes are sent; an oversized count traps; Err sends no payload.", """errors AppError {
    Failed = 1;
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    for index: u32 in 0..response.length {
        response[index] = 0x11;
    }
    var operation: u8 = request[0];
    if operation == 1 {
        response[0] = 0xAA;
        response[1] = 0xBB;
        response[2] = 0xCC;
        return Ok(2);
    } else if operation == 2 {
        return Ok(convert<u32>(request[1]));
    }
    return Err(AppError.Failed);
}
""", """install
power_on
command 01
expect ok aa bb
command 02 03 capacity 4
expect ok 11 11 11
command 02 05 capacity 4
expect trap RESPONSE-COUNT
command 03
expect err app 1
""")

# ---------------------------------------------------------------- run-011
add("run-011-counter-application", "HEP-15, OUT-20, TXN-3", "DN §13",
"The counter application (chapter 12) across a sequence of commands.", block(ch12, "valid/hep-005-counter-application.card"), """install
power_on
command 01
expect ok 00 00 00 00
command 02
expect ok 00 00 00 01
command 02
expect ok 00 00 00 02
command 01
expect ok 00 00 00 02
command
expect err app 1
command 01 02
expect err app 1
command 07
expect err app 2
command 02 capacity 2  # the increment commits before the response check fails
expect err app 3
command 01             # Err did not undo the committed increment
expect ok 00 00 00 03
""")

# ---------------------------------------------------------------- run-012
add("run-012-wallet-application", "HEP-15, TXN-8, OUT-20, STA-4, RTF-9", "DN §13",
"The wallet application: PIN authorization, credit and debit, abort rollback and a security reset.", """errors WalletError {
    MalformedRequest = 1;
    UnsupportedOperation = 2;
    Unauthorized = 3;
    InsufficientFunds = 4;
    WrongPin = 5;
    LimitExceeded = 6;
    ResponseTooSmall = 7;
}

const OP_VERIFY: u8 = 0x20;
const OP_BALANCE: u8 = 0x30;
const OP_CREDIT: u8 = 0x31;
const OP_DEBIT: u8 = 0x32;
const PIN: u8[4] = [1, 2, 3, 4];
const MAX_BALANCE: u32 = 100000;
const MAX_DEBIT: u32 = 500;

persistent balance: u32;
persistent sequence: u32;
session authenticated: bool;

function verify(input: ref u8[]) {
    require input.length == 5 else WalletError.MalformedRequest;
    for index: u32 in 0..4 {
        if input[index + 1] != PIN[index] {
            authenticated = false;
            return Err(WalletError.WrongPin);
        }
    }
    authenticated = true;
    return Ok();
}

function read_amount(input: ref u8[]) -> u32 {
    require input.length == 5 else WalletError.MalformedRequest;
    return Ok(decode_be<u32>(ref input[1..5]));
}

function encode_balance(output: inout u8[]) -> u32 {
    require output.length >= 4 else WalletError.ResponseTooSmall;
    var bytes: u8[4] = encode_be(balance);
    for index: u32 in 0..4 {
        output[index] = bytes[index];
    }
    return Ok(4);
}

function credit(amount: u32) {
    require authenticated else WalletError.Unauthorized;
    var updated: u32 = 0;
    match checked_add(balance, amount) {
        Ok(value) => {
            updated = value;
        }
        Err(_) => {
            return Err(WalletError.LimitExceeded);
        }
    }
    require updated <= MAX_BALANCE else WalletError.LimitExceeded;
    transaction {
        balance = updated;
        sequence = sequence + 1;
    }
    return Ok();
}

function record_debit(amount: u32) {
    sequence = sequence + 1;
    if amount > MAX_DEBIT {
        return Err(WalletError.LimitExceeded);
    }
    return Ok();
}

function debit(amount: u32) {
    require authenticated else WalletError.Unauthorized;
    require amount <= balance else WalletError.InsufficientFunds;
    transaction {
        balance = balance - amount;
        match record_debit(amount) {
            Ok() => {
            }
            Err(error) => {
                abort Err(error);
            }
        }
    }
    return Ok();
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length >= 1 else WalletError.MalformedRequest;
    var operation: u8 = request[0];
    if operation == OP_VERIFY {
        attempt verify(ref request);
        return Ok(0);
    } else if operation == OP_BALANCE {
        require authenticated else WalletError.Unauthorized;
    } else if operation == OP_CREDIT {
        var amount: u32 = attempt read_amount(ref request);
        attempt credit(amount);
    } else if operation == OP_DEBIT {
        var amount: u32 = attempt read_amount(ref request);
        attempt debit(amount);
    } else {
        return Err(WalletError.UnsupportedOperation);
    }
    return encode_balance(inout response);
}
""", """install
power_on
command 30
expect err app 3                 # not authenticated
command 20 01 02 03 05
expect err app 5                 # wrong PIN
command 20 01 02 03 04
expect ok
command 30
expect ok 00 00 00 00
command 31 00 00 03 e8           # credit 1000
expect ok 00 00 03 e8
command 32 00 00 01 2c           # debit 300
expect ok 00 00 02 bc
command 32 00 00 02 58           # debit 600: record_debit fails, the transaction is aborted
expect err app 6
command 30                       # balance rolled back to 700
expect ok 00 00 02 bc
command 32 00 00 03 20           # debit 800
expect err app 4
command 31 00 01 86 a0           # 700 + 100000 exceeds MAX_BALANCE
expect err app 6
command 31 ff ff ff ff           # checked_add overflow
expect err app 6
command 31 00 00 01
expect err app 1
command 40
expect err app 2
reset
power_on
command 32 00 00 00 64           # the session (authentication) was cleared
expect err app 3
command 20 01 02 03 04
expect ok
command 30                       # persistent balance kept across the reset
expect ok 00 00 02 bc
""")

# ---------------------------------------------------------------- run-013
add("run-013-execution-budget", "RTF-6, RTF-3", "DN §3.6",
"An endless loop exhausts the execution budget; the next command still runs.", """command process(request: ref u8[], response: inout u8[]) -> u32 {
    if request.length == 0 {
        while true {
        }
    }
    return Ok(0);
}
""", """install
power_on
command
expect trap EXHAUSTED
command 01
expect ok
""")

# ---------------------------------------------------------------- run-014
add("run-014-recovery-after-interrupt", "TXN-13, RTF-10", "DN §7.2",
"Power loss during a commit recovers to all-or-nothing.", """persistent first: u32;
persistent second: u32;

command process(request: ref u8[], response: inout u8[]) -> u32 {
    transaction {
        first = first + 1;
        second = second + 1;
    }
    response[0] = truncate<u8>(first);
    response[1] = truncate<u8>(second);
    return Ok(2);
}
""", """install
power_on
command 01
expect ok 01 01
interrupt during-commit
command 01
expect none
power_on
command 01           # the interrupted transaction left no trace
expect ok 02 02
""", requires="fault-injection")

# ---------------------------------------------------------------- write
for name, (rule, src, note, program, scenario, requires) in T.items():
    d = conf / name; d.mkdir(parents=True, exist_ok=True)
    hdr = f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: application\n// expect: runtime\n"
    if requires: hdr += f"// requires: {requires}\n"
    hdr += f"// note: {note}\n"
    (d / "program.card").write_text(hdr + program, encoding="utf-8", newline="\n")
    (d / "scenario.txt").write_text(scenario, encoding="utf-8", newline="\n")
refs = set(re.findall(r"`runtime/(run-[\w-]+)/`", ch13)) - {p.split("/")[1] for p in SP14_OWNED if p.startswith("runtime/")}
assert refs == set(T), sorted(refs ^ set(T))
gk = conf / ".gitkeep"
if gk.exists(): gk.unlink()
print("runtime tests:", len(T))
