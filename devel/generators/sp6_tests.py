import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "checkers"))   # find layout
import layout
# Tests written by later generators (sp14_tests.py, wp1_tests.py) are referenced in this chapter but owned by them.
SP14_OWNED = set().union(*(set(f.read_text().split()) for f in pathlib.Path(__file__).parent.glob("*_owned.txt")))
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance
ch = (layout.at(repo).spec / "07-statements-and-control-flow.md").read_text(encoding="utf-8")

def fn(body, ret=None, params="", name="check"):
    arrow = f" -> {ret}" if ret else ""
    return f"function {name}({params}){arrow} {{\n" + "".join("    " + l + "\n" for l in body) + "}\n"

T = {}
def add(path, rule, src, expect, note, code): T[path] = (rule, src, expect, note, code)
block = lambda path: re.search(r"\(conformance: `" + re.escape(path) + r"`\)\n\n```text\n(.*?)```", ch, re.S).group(1)

# valid tests whose code is shown in the chapter
for path, rule, src, note in [
 ("valid/stm-001-local-defaults-and-initializers.card", "STM-4, STM-5", "DN §3.9", "Locals with and without initializers."),
 ("valid/stm-002-assignment-places.card", "STM-7, STM-8", "DN §7.1, §9.1", "Assignment to locals, globals, nested fields, elements and an inout parameter."),
 ("valid/stm-003-whole-array-assignment.card", "STM-8", "DN §8.2", "Whole-array assignment between identical array types."),
 ("valid/stm-004-if-chain.card", "STM-11, STM-20", "DN §3.6", "An if/else if/else chain in which every branch returns."),
 ("valid/stm-005-while-break-continue.card", "STM-12, STM-15", "DN §3.6", "A while loop with continue and break."),
 ("valid/stm-006-for-ranges.card", "STM-13, STM-14", "DN §3.6, §8.1", "for over u8 and i16, an empty range, and a .length bound."),
 ("valid/stm-007-enum-match.card", "STM-16, STM-20", "DN §3.11", "A match listing every variant; every arm returns."),
 ("valid/stm-008-require.card", "STM-19", "DN §6.1", "require before a subtraction it makes safe."),
 ("valid/stm-009-while-true-no-return.card", "STM-20, STM-21", "DN §3.7", "while true without break needs no return after it."),
 ("valid/stm-010-statements-after-return.card", "STM-22", "DN §3.10", "A statement after a return is permitted."),
 ("valid/stm-011-while-true-with-return-inside.card", "STM-20", "DN §3.7", "A return inside while true."),
]:
    add(path, rule, src, "ok", note, block(path))

add("valid/stm-012-match-arms-may-complete.card", "STM-16, STM-20", "DN §3.7, §3.11", "ok", "A match whose arms complete normally, followed by a return.",
"""enum Mode {
    Off;
    On;
}

session mode: Mode;
session level: u8;

function apply() {
    match mode {
        Mode.Off => {
            level = 0;
        }
        Mode.On => {
            level = 1;
        }
    }
    return Ok();
}
""")

ENUM = "enum Mode {\n    Off;\n    On;\n    Standby;\n}\n\nsession mode: Mode;\n\n"
def enum_match(arms):
    body = ["match mode {"]
    for a in arms: body += [f"    {a} => {{", "    }"]
    return ENUM + fn(body + ["}", "return Ok();"])

I = "invalid/"
add(I+"stm-101-chained-assignment.card", "STM-6", "DN §3.5", "compile-error CE-SYN-1", "Chained assignment.",
fn(["var a: u32;", "var b: u32;", "a = b = 0;", "return Ok();"]))
add(I+"stm-102-assignment-in-condition.card", "STM-6", "DN §3.5", "compile-error CE-SYN-1", "Assignment inside a condition.",
fn(["var ready: bool;", "if ready = true {", "}", "return Ok();"]))
add(I+"stm-104-increment.card", "STM-6", "DN §3.5", "compile-error CE-SYN-1", "There is no increment operator.",
fn(["var count: u32;", "count++;", "return Ok();"]))
add(I+"stm-105-assign-constant.card", "STM-7", "DN §5.1", "compile-error CE-STM-2", "Assignment to a constant.",
"const LIMIT: u32 = 4;\n\n" + fn(["LIMIT = 5;", "return Ok();"]))
add(I+"stm-106-assign-constant-element.card", "STM-7", "DN §5.1, §9", "compile-error CE-STM-2", "Assignment to an element of a constant.",
"const IDENTIFIER: u8[4] = [1, 2, 3, 4];\n\n" + fn(["IDENTIFIER[0] = 9;", "return Ok();"]))
add(I+"stm-107-assign-by-value-parameter.card", "STM-7", "DN §3.7", "compile-error CE-STM-2", "Assignment to a by-value parameter.",
fn(["amount = 0;", "return Ok();"], None, "amount: u32"))
add(I+"stm-108-assign-for-index.card", "STM-7, STM-14", "DN §3.6", "compile-error CE-STM-2", "Assignment to a for index.",
fn(["for index: u8 in 0..4 {", "    index = 3;", "}", "return Ok();"]))
add(I+"stm-109-assign-length.card", "STM-7", "DN §8.1", "compile-error CE-STM-2", "Assignment to .length.",
"session buffer: u8[16];\n\n" + fn(["buffer.length = 10;", "return Ok();"]))
add(I+"stm-110-assign-match-binding.card", "STM-7", "DN §3.6", "compile-error CE-STM-2", "Assignment to a pattern binding.",
"session balance: u32;\n\n" + fn(["match checked_sub(balance, amount) {", "    Ok(value) => {", "        value = 1;", "    }",
   "    Err(error) => {", "        return Err(error);", "    }", "}", "return Ok();"], None, "amount: u32"))
add(I+"stm-111-break-outside-loop.card", "STM-15", "DN §3.6", "compile-error CE-STM-3", "break outside a loop.",
fn(["break;", "return Ok();"]))
add(I+"stm-112-continue-outside-loop.card", "STM-15", "DN §3.6", "compile-error CE-STM-3", "continue outside a loop.",
fn(["continue;", "return Ok();"]))
add(I+"stm-113-enum-match-missing.card", "STM-16", "DN §3.11", "compile-error CE-STM-4", "A variant is missing.",
enum_match(["Mode.Off", "Mode.On"]))
add(I+"stm-114-enum-match-duplicate.card", "STM-16", "DN §3.11", "compile-error CE-STM-4", "A variant appears twice.",
enum_match(["Mode.Off", "Mode.On", "Mode.Standby", "Mode.On"]))
add(I+"stm-115-enum-match-foreign.card", "STM-16", "DN §3.11", "compile-error CE-STM-4", "A variant of another enum.",
"enum Other {\n    Off;\n}\n\n" + enum_match(["Mode.Off", "Mode.On", "Other.Off"]))
add(I+"stm-116-enum-match-wildcard.card", "STM-16", "DN §3.11", "compile-error CE-STM-4", "A catch-all arm.",
enum_match(["Mode.Off", "_"]))
add(I+"stm-117-match-integer.card", "STM-17", "DN §3.6", "compile-error CE-STM-4", "An integer scrutinee.",
fn(["match count {", "    _ => {", "    }", "}", "return Ok();"], None, "count: u8"))
add(I+"stm-118-missing-return.card", "STM-21", "DN §3.7", "compile-error CE-STM-5", "No final return.",
fn(["var count: u32 = 1;"]))
add(I+"stm-119-if-without-else-return.card", "STM-20, STM-21", "DN §3.7", "compile-error CE-STM-5", "An if without else that returns only in its block.",
fn(["if ready {", "    return Ok(1);", "}"], "u32", "ready: bool"))
add(I+"stm-120-while-true-with-break.card", "STM-20, STM-21", "DN §3.7", "compile-error CE-STM-5", "while true with a break, and no return after the loop.",
fn(["while true {", "    if ready {", "        break;", "    }", "}"], "u32", "ready: bool"))
add(I+"stm-121-for-bool-index.card", "STM-13", "DN §3.6", "compile-error CE-STM-6", "A bool for index.",
fn(["for flag: bool in false..true {", "}", "return Ok();"]))
add(I+"stm-122-for-endpoint-out-of-range.card", "STM-13", "DN §3.6", "compile-error CE-EXP-2", "An endpoint that does not fit u8.",
"session buffer: u8[256];\n\n" + fn(["for index: u8 in 0..256 {", "    buffer[index] = 0;", "}", "return Ok();"]))
add(I+"stm-123-require-integer-operand.card", "STM-19", "DN §3.6", "compile-error CE-STM-7", "A require operand that is an integer.",
fn(["require ready else 5;", "return Ok();"], None, "ready: bool"))
add(I+"stm-124-non-bool-condition.card", "STM-11", "DN §3.4, §3.6", "compile-error CE-EXP-1", "An integer condition.",
fn(["if count {", "}", "return Ok();"], None, "count: u8"))
add(I+"stm-125-expression-statement.card", "STM-2", "D-433", "compile-error CE-STM-1", "An arithmetic expression used as a statement.",
fn(["a + b;", "return Ok();"], None, "a: u32, b: u32"))
add(I+"stm-126-standalone-block.card", "STM-3", "D-434", "compile-error CE-SYN-1", "A standalone block.",
fn(["{", "    var inner: u32 = 1;", "}", "return Ok();"]))
add(I+"stm-127-assign-function.card", "STM-7", "DN §3.7", "compile-error CE-STM-2", "Assignment to a function name.",
"function helper() {\n    return Ok();\n}\n\n" + fn(["helper = 1;", "return Ok();"]))

for path, (rule, src, exp, note, code) in T.items():
    hdr = f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: fragment\n// expect: {exp}\n// note: {note}\n"
    (conf / path).write_text(hdr + code, encoding="utf-8", newline="\n")
refs = set(re.findall(r"`((?:valid|invalid)/stm-[\w-]+\.card)`", ch)) - SP14_OWNED
assert refs == set(T), sorted(refs ^ set(T))
print("tests:", len(T))
