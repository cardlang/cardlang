import re, sys, pathlib
# Tests written by sp14_tests.py are referenced in this chapter but owned by that generator.
SP14_OWNED = set((pathlib.Path(__file__).parent / "sp14_owned.txt").read_text().split())
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"
ch = (repo / "spec" / "06-expressions.md").read_text(encoding="utf-8")

def fn(body, ret=None, params=""):
    arrow = f" -> {ret}" if ret else ""
    return f"function check({params}){arrow} {{\n" + "".join("    " + l + "\n" for l in body) + "}\n"

T = {}  # path: (rule, source, expect, note, code)
def add(path, rule, src, expect, note, code): T[path] = (rule, src, expect, note, code)

# ---------- valid ----------
add("valid/exp-001-literal-contexts.card", "EXP-7, EXP-10", "DN §3.3", "ok", "Literals typed by declarations, assignments, arguments, return Ok and for ranges.",
"""session total: u16;

function scale(factor: u8) -> u8 {
    return Ok(factor * 2);
}

function contexts() -> u32 {
    var count: u8 = 10;
    var sum: u16 = 10 + 20;
    total = 300;
    var scaled: u8 = attempt scale(4);
    for index: u16 in 0..1000 {
        total = index;
    }
    return Ok(5);
}
""")
add("valid/exp-002-typed-operand-either-side.card", "EXP-11", "DN §3.3", "ok", "A typed operand on either side gives the literal its type.",
fn(["var count: u8 = 10;", "var a: u8 = count + 1;", "var b: u8 = 1 + count;", "return Ok(count == 10);"], "bool"))
add("valid/exp-003-negative-minimum.card", "EXP-8, EXP-19", "DN §3.0, §6.5", "ok", "The minimum signed value as a literal, and negation of a signed value.",
"""const MINIMUM: i8 = -128;

function negatives() -> i16 {
    var small: i16 = -32768;
    var value: i16 = 10;
    var negative: i16 = -value;
    return Ok(negative);
}
""")
add("valid/exp-004-same-operator-chains.card", "EXP-2, EXP-3", "DN §3.5", "ok", "Chains of one operator and explicit grouping.",
"""function chains(a: u32, b: u32, c: u32) -> u32 {
    var sum: u32 = a + b + c;
    var difference: u32 = (a + b) - c;
    var mixed: u32 = a + (b * c);
    return Ok(sum);
}
""")
add("valid/exp-005-unary-with-binary.card", "EXP-1, EXP-2", "DN §3.5", "ok", "Unary operators next to binary operators need no parentheses.",
"""session authenticated: bool;
session blocked: bool;

function unary_mix(x: i16, y: i16) -> bool {
    var total: i16 = -x + y;
    return Ok(authenticated and not blocked);
}
""")
add("valid/exp-006-guaranteed-conversions.card", "EXP-31, EXP-32", "DN §3.2", "ok", "Guaranteed conversions.",
"""function widen(small: u8, signed_small: i8) -> u32 {
    var large: u16 = convert<u16>(small);
    var signed_value: i16 = convert<i16>(small);
    var wide: i32 = convert<i32>(signed_small);
    return Ok(convert<u32>(large));
}
""")
add("valid/exp-007-equality-bool-enum.card", "EXP-15", "DN §3.5, §3.11", "ok", "Equality on bool and on an enum.",
"""enum Mode {
    Off;
    On;
}

session mode: Mode;
session ready: bool;

function compare() -> bool {
    var same: bool = ready == true;
    return Ok(mode != Mode.Off);
}
""")
add("valid/exp-008-shifts-and-bitwise.card", "EXP-17, EXP-18", "DN §3.5", "ok", "Bitwise operators and shifts with a u8 count.",
"""function bits(flags: u8, count: u8) -> u8 {
    var low: u8 = flags & 0x0F;
    var shifted: u8 = flags >> 2;
    var moved: u8 = flags << count;
    var check: bool = (flags & 0x03) == 0x01;
    return Ok(~low);
}
""")
add("valid/exp-009-index-types.card", "EXP-39", "DN §3.3, §8.1", "ok", "Literal-only, u8 and u16 indices.",
"""session buffer: u8[16];

function indices(small: u8, medium: u16) -> u8 {
    var first: u8 = buffer[0];
    var second: u8 = buffer[1 + 2];
    var third: u8 = buffer[small];
    return Ok(buffer[medium]);
}
""")
add("valid/exp-010-length-of-field.card", "EXP-40", "DN §8.1", "ok", "The length of an array field.",
"""struct Account {
    identifier: u8[4];
    balance: u32;
}

session account: Account;

function identifier_size() -> u32 {
    return Ok(account.identifier.length);
}
""")
add("valid/exp-011-fill-forms.card", "EXP-44", "DN §8.3", "ok", "fill from a local, and from an element of the destination.",
"""session buffer: u8[16];

function read_byte() -> u8 {
    return Ok(0xA5);
}

function refill() {
    var next_byte: u8 = attempt read_byte();
    buffer = fill(next_byte);
    buffer = fill(buffer[0]);
    return Ok();
}
""")
add("valid/exp-012-constructor-order.card", "EXP-45", "DN §9.3", "ok", "Constructor fields in a different order from the declaration.",
"""struct Account {
    balance: u32;
    identifier: u8[4];
    counters: u32[8];
}

function build() -> Account {
    var working: Account = Account { counters: fill(0), balance: 100, identifier: [1, 2, 3, 4] };
    return Ok(working);
}
""")
add("valid/exp-013-wrapping.card", "EXP-30", "DN §6.5", "ok", "A wrapping intrinsic is a direct value.",
"""function wrap(a: u8, b: u8) -> u8 {
    return Ok(wrapping_add(a, b));
}
""")
add("valid/exp-014-checked-in-match.card", "EXP-29, EXP-48", "DN §6.2, §6.5", "ok", "A checked intrinsic consumed by match.",
"""session balance: u32;

function debit(amount: u32) {
    match checked_sub(balance, amount) {
        Ok(value) => {
            balance = value;
        }
        Err(error) => {
            return Err(error);
        }
    }
    return Ok();
}
""")
add("valid/exp-015-short-circuit-index.card", "EXP-21", "DN §3.5", "ok", "Short-circuiting guards the index.",
"""session buffer: u8[16];

function is_free(index: u8) -> bool {
    return Ok((index < 16) and (buffer[index] == 0));
}
""")
add("valid/exp-016-truncate-and-bytes.card", "EXP-34, EXP-36, EXP-37", "D-432", "ok", "truncate and the byte-order intrinsics.",
"""function encode_amount(amount: u32, request: ref u8[]) -> u8 {
    var low: u8 = truncate<u8>(amount);
    var bytes: u8[4] = encode_be(amount);
    var parsed: u32 = decode_be<u32>(ref request);
    var little: u16 = decode_le<u16>(ref request[0..2]);
    return Ok(low);
}
""")
add("valid/exp-017-checked-convert.card", "EXP-33", "DN §3.2", "ok", "A checked conversion consumed by match.",
"""function narrow(incoming: u16) -> u8 {
    match checked_convert<u8>(incoming) {
        Ok(value) => {
            return Ok(value);
        }
        Err(error) => {
            return Err(error);
        }
    }
}
""")
add("valid/exp-018-parenthesized-constructor-condition.card", "EXP-6", "D-430", "ok", "A parenthesized constructor in an if condition.",
"""struct Limits {
    low: u16;
    high: u16;
}

function check() -> bool {
    if (Limits { low: 1, high: 2 }).high == 2 {
        return Ok(true);
    }
    return Ok(false);
}
""")

# ---------- invalid ----------
S3 = "a: u32, b: u32, c: u32"
add("invalid/exp-101-operand-type-mismatch.card", "EXP-12", "DN §3.2", "compile-error CE-EXP-1", "Operands of different integer types.",
fn(["return Ok(count + increment);"], "u16", "count: u16, increment: u8"))
add("invalid/exp-102-literal-out-of-range.card", "EXP-7", "DN §3.3", "compile-error CE-EXP-2", "A literal out of range for u8.",
fn(["var invalid: u8 = 300;", "return Ok();"]))
add("invalid/exp-103-negative-literal-unsigned.card", "EXP-8, EXP-19", "DN §6.5", "compile-error CE-EXP-6", "A negative literal in an unsigned context.",
fn(["var invalid: u8 = -1;", "return Ok();"]))
add("invalid/exp-104-no-literal-context.card", "EXP-11", "DN §3.3", "compile-error CE-EXP-3", "A comparison of literals has no integer context.",
fn(["var same: bool = 1 == 1;", "return Ok();"]))
add("invalid/exp-105-mixed-arithmetic.card", "EXP-2", "DN §3.5", "compile-error CE-EXP-4", "Mixed + and * without grouping.",
fn(["return Ok(a + b * c);"], "u32", S3))
add("invalid/exp-106-mixed-plus-minus.card", "EXP-2", "DN §3.5", "compile-error CE-EXP-4", "Mixed + and - without grouping.",
fn(["return Ok(a + b - c);"], "u32", S3))
add("invalid/exp-107-mixed-bitwise-comparison.card", "EXP-2, EXP-5", "DN §3.5", "compile-error CE-EXP-4", "Mixed & and == without grouping.",
fn(["return Ok(flags & 0x03 == 0x01);"], "bool", "flags: u8"))
add("invalid/exp-108-mixed-boolean.card", "EXP-2, EXP-5", "DN §3.5", "compile-error CE-EXP-4", "Mixed and/or without grouping.",
fn(["return Ok(authenticated and ready or emergency);"], "bool", "authenticated: bool, ready: bool, emergency: bool"))
add("invalid/exp-109-comparison-chain.card", "EXP-4", "DN §3.5", "compile-error CE-EXP-5", "A chain of ordering comparisons.",
fn(["return Ok(0 < amount < limit);"], "bool", "amount: u32, limit: u32"))
add("invalid/exp-110-equality-chain.card", "EXP-4", "DN §3.5", "compile-error CE-EXP-5", "A chain of equality comparisons on bool values.",
fn(["return Ok(a == b == c);"], "bool", "a: bool, b: bool, c: bool"))
add("invalid/exp-111-convert-narrowing.card", "EXP-32", "DN §3.2", "compile-error CE-EXP-8", "convert from u16 to u8 is not guaranteed.",
fn(["return Ok(convert<u8>(value));"], "u8", "value: u16"))
add("invalid/exp-112-convert-unknown-source.card", "EXP-31", "DN §3.3", "compile-error CE-EXP-8", "convert of a literal has no source type.",
fn(["return Ok(convert<u32>(32));"], "u32"))
add("invalid/exp-113-signed-index.card", "EXP-39", "DN §8.1", "compile-error CE-EXP-9", "A signed index.",
"session buffer: u8[16];\n\n" + fn(["buffer[signed_index] = 3;", "return Ok();"], None, "signed_index: i16"))
add("invalid/exp-114-bool-index.card", "EXP-39", "DN §8.1", "compile-error CE-EXP-9", "A bool index.",
"session buffer: u8[16];\n\n" + fn(["return Ok(buffer[flag]);"], "u8", "flag: bool"))
add("invalid/exp-115-signed-shift-count.card", "EXP-18", "DN §3.5", "compile-error CE-EXP-1", "A shift count that is not u8.",
fn(["return Ok(flags << count);"], "u8", "flags: u8, count: i8"))
add("invalid/exp-116-bitwise-signed.card", "EXP-17", "DN §3.5", "compile-error CE-EXP-6", "Bitwise and on signed operands.",
fn(["return Ok(x & y);"], "i16", "x: i16, y: i16"))
add("invalid/exp-117-ordering-bool.card", "EXP-14", "DN §3.5", "compile-error CE-EXP-6", "Ordering comparison on bool values.",
fn(["return Ok(ready < blocked);"], "bool", "ready: bool, blocked: bool"))
add("invalid/exp-118-structure-equality.card", "EXP-15", "DN §9.3", "compile-error CE-EXP-6", "Equality on structures.",
"struct Pair {\n    left: u8;\n    right: u8;\n}\n\n" + fn(["return Ok(first == second);"], "bool", "first: Pair, second: Pair"))
add("invalid/exp-119-array-equality.card", "EXP-15", "DN §8.2", "compile-error CE-EXP-6", "Equality on arrays.",
fn(["return Ok(left == right);"], "bool", "left: u8[4], right: u8[4]"))
add("invalid/exp-120-bool-from-integer.card", "EXP-7", "DN §3.4", "compile-error CE-EXP-1", "An integer literal where bool is required.",
fn(["var invalid: bool = 1;", "return Ok();"]))
add("invalid/exp-121-enum-from-integer.card", "EXP-7", "DN §3.11", "compile-error CE-EXP-1", "An integer literal assigned to an enum variable.",
"enum OperationState {\n    Idle;\n    Receiving;\n}\n\nsession state: OperationState;\n\n" + fn(["state = 1;", "return Ok();"]))
add("invalid/exp-122-distinct-structures.card", "EXP-12", "DN §9.3", "compile-error CE-EXP-1", "Assignment between distinct structure types with identical fields.",
"struct First {\n    value: u32;\n}\n\nstruct Second {\n    value: u32;\n}\n\n" + fn(["var first: First;", "var second: Second;", "second = first;", "return Ok();"]))
add("invalid/exp-123-typed-constant-no-widening.card", "EXP-12", "DN §3.10", "compile-error CE-EXP-1", "A typed u8 constant is not implicitly widened.",
"const SMALL: u8 = 32;\nconst LARGE: u32 = SMALL;\n")
add("invalid/exp-124-nested-convert.card", "EXP-49", "DN §3.10", "compile-error CE-EXP-7", "A conversion nested in a conversion argument.",
"const SMALL: u8 = 32;\nconst X: u32 = convert<u32>(convert<u16>(SMALL));\n")
add("invalid/exp-125-intrinsic-in-argument.card", "EXP-49", "DN §3.7", "compile-error CE-EXP-7", "An intrinsic call inside a call argument.",
"function process_value(value: u32) {\n    return Ok();\n}\n\n" + fn(["attempt process_value(convert<u32>(small));", "return Ok();"], None, "small: u8"))
add("invalid/exp-126-attempt-in-argument.card", "EXP-49", "DN §3.7", "compile-error CE-EXP-7", "attempt inside a call argument.",
"session counter: u32;\n\nfunction next_value() -> u32 {\n    return Ok(1);\n}\n\nfunction process(target: inout u32, value: u32) {\n    return Ok();\n}\n\n"
+ fn(["attempt process(inout counter, attempt next_value());", "return Ok();"]))
add("invalid/exp-127-outcome-as-value.card", "EXP-48", "DN §3.5", "compile-error CE-EXP-14", "A call outcome used as an arithmetic operand.",
"session balance: u32;\n\nfunction subtract(current_balance: u32, amount: u32) -> u32 {\n    return Ok(current_balance - amount);\n}\n\n"
+ fn(["var result: u32 = balance + subtract(balance, amount);", "return Ok();"], None, "amount: u32"))
add("invalid/exp-128-list-too-short.card", "EXP-43", "DN §8", "compile-error CE-EXP-11", "An array list shorter than the destination.",
"session short: u8[4];\n\n" + fn(["short = [1, 2];", "return Ok();"]))
add("invalid/exp-129-list-too-long.card", "EXP-43", "DN §8", "compile-error CE-EXP-11", "An array list longer than the destination.",
"session long: u8[2];\n\n" + fn(["long = [1, 2, 3];", "return Ok();"]))
add("invalid/exp-130-fill-without-context.card", "EXP-44", "DN §8.3", "compile-error CE-EXP-10", "fill with no expected array type.",
fn(["var size: u32 = fill(0).length;", "return Ok();"]))
ACC = "struct Account {\n    balance: u32;\n    identifier: u8[4];\n}\n\n"
add("invalid/exp-131-constructor-missing-field.card", "EXP-45", "DN §9.3", "compile-error CE-EXP-12", "A constructor without the balance field.",
ACC + fn(["var working: Account = Account { identifier: [1, 2, 3, 4] };", "return Ok();"]))
add("invalid/exp-132-constructor-unknown-field.card", "EXP-45", "DN §9.3", "compile-error CE-EXP-12", "A constructor with an undeclared field.",
ACC + fn(["var working: Account = Account { balance: 0, identifier: [1, 2, 3, 4], owner: 7 };", "return Ok();"]))
add("invalid/exp-133-constructor-duplicate-field.card", "EXP-45", "DN §9.3", "compile-error CE-EXP-12", "A constructor that gives balance twice.",
ACC + fn(["var working: Account = Account { balance: 0, identifier: [1, 2, 3, 4], balance: 1 };", "return Ok();"]))
add("invalid/exp-134-unknown-field.card", "EXP-41", "DN §4.2", "compile-error CE-EXP-13", "A field the structure does not declare.",
ACC + "session account: Account;\n\n" + fn(["return Ok(account.missing);"], "u32"))
add("invalid/exp-135-unparenthesized-constructor-condition.card", "EXP-6", "D-430", "compile-error CE-SYN-1", "A constructor directly in an if condition.",
"struct Limits {\n    low: u16;\n    high: u16;\n}\n\n" + fn(["if Limits { low: 1, high: 2 }.high == 2 {", "    return Ok(true);", "}", "return Ok(false);"], "bool"))
add("invalid/exp-136-truncate-unknown-source.card", "EXP-31, EXP-34", "D-432", "compile-error CE-EXP-8", "truncate of a literal has no source type.",
fn(["return Ok(truncate<u8>(300));"], "u8"))
add("invalid/exp-137-encode-unsupported-type.card", "EXP-36", "D-432", "compile-error CE-EXP-8", "encode_be of a u8 value.",
fn(["var bytes: u8[1] = encode_be(small);", "return Ok();"], None, "small: u8"))
add("invalid/exp-138-argument-count.card", "EXP-47", "DN §3.7", "compile-error CE-EXP-16", "A wrapping intrinsic with one argument.",
fn(["return Ok(wrapping_add(a));"], "u8", "a: u8"))
add("invalid/exp-139-call-non-function.card", "EXP-47", "DN §3.7", "compile-error CE-EXP-15", "A call whose target is a constant.",
"const LIMIT: u32 = 4;\n\n" + fn(["attempt LIMIT();", "return Ok();"]))
add("invalid/exp-140-length-on-integer.card", "EXP-40, EXP-41", "DN §8.1", "compile-error CE-EXP-13", ".length on an integer.",
fn(["return Ok(count.length);"], "u32", "count: u32"))
add("invalid/exp-141-unary-minus-unsigned.card", "EXP-19", "DN §6.5", "compile-error CE-EXP-6", "Unary minus on an unsigned value.",
fn(["return Ok(-count);"], "u8", "count: u8"))
add("invalid/exp-142-checked-no-context.card", "EXP-11, EXP-29", "DN §3.3", "compile-error CE-EXP-3", "A checked intrinsic whose operands are all literals.",
fn(["match checked_add(1, 2) {", "    Ok(value) => {", "    }", "    Err(error) => {", "        return Err(error);", "    }", "}", "return Ok();"]))

# write files
for path, (rule, src, exp, note, code) in T.items():
    hdr = f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: fragment\n// expect: {exp}\n// note: {note}\n"
    (conf / path).write_text(hdr + code, encoding="utf-8", newline="\n")

# cross-check with chapter: every referenced path exists in T, every T path referenced, code blocks match
refs = set(re.findall(r"`((?:valid|invalid)/exp-[\w-]+\.card)`", ch)) - SP14_OWNED
assert refs == set(T), ("mismatch", sorted(refs ^ set(T)))
pat = re.compile(r"\(conformance: ([^)]*)\)\n\n```text\n(.*?)```", re.S)
checked = 0
for reflist, code in pat.findall(ch):
    paths = [p for p in re.findall(r"`([^`]+)`", reflist) if p not in SP14_OWNED]
    if not paths: continue
    assert any(T[p][4] == code for p in paths), ("code differs", paths); checked += 1
print("tests:", len(T), "| chapter code blocks verified identical:", checked)
