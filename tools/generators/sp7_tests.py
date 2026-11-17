import re, sys, pathlib
# Tests written by sp14_tests.py and wp1_tests.py are referenced in this chapter but owned by those generators.
SP14_OWNED = set().union(*(set(f.read_text().split()) for f in pathlib.Path(__file__).parent.glob("*_owned.txt")))
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"
ch = (repo / "spec" / "08-functions-and-references.md").read_text(encoding="utf-8")

def fn(body, ret=None, params="", name="check"):
    arrow = f" -> {ret}" if ret else ""
    return f"function {name}({params}){arrow} {{\n" + "".join("    " + l + "\n" for l in body) + "}\n"
def block(path):
    m = re.search(r"\(conformance: `" + re.escape(path) + r"`\)\n\n```text\n(.*?)```", ch, re.S)
    return m.group(1)

T = {}; MULTI = {}
def add(path, rule, src, expect, note, code): T[path] = (rule, src, expect, note, code)

for path, rule, src, note in [
 ("valid/fun-002-structure-return.card", "FUN-2", "DN §3.7", "A structure groups two return values."),
 ("valid/fun-010-no-payload-function.card", "FUN-2", "DN §3.7", "A function with no successful payload."),
 ("valid/fun-009-constant-and-bindings-by-ref.card", "FUN-9", "DN §3.8; D-435", "References to a constant, a by-value parameter and a for index."),
 ("valid/fun-004-aliasing.card", "FUN-12, FUN-13, FUN-14", "DN §3.8", "The same byte written through a reference and a global."),
 ("valid/fun-005-overlapping-references.card", "FUN-13", "DN §3.8", "Overlapping inout/ref and inout/inout arguments."),
 ("valid/fun-006-forwarding.card", "FUN-15", "DN §3.8", "An inout parameter forwarded as ref and as inout."),
 ("valid/fun-003-ref-and-inout-field.card", "FUN-6, FUN-9", "DN §3.8", "ref and inout of a structure and of a field."),
 ("valid/fun-007-slices-and-views.card", "FUN-18, FUN-20, FUN-21", "DN §8.4", "A whole array, a slice and an empty slice passed to ref u8[]."),
 ("valid/fun-008-narrowing-views.card", "FUN-18, FUN-21", "DN §8.4", "Narrowing a view, and a slice as the receiver of .length."),
]:
    add(path, rule, src, "ok", note, block(path))
add("invalid/fun-102-indirect-recursion.card", "FUN-5", "DN §3.7", "compile-error CE-FUN-1", "Indirect recursion.", block("invalid/fun-102-indirect-recursion.card"))

MULTI["valid/fun-001-forward-call-across-files"] = ("FUN-3, FUN-4", "DN §3.7, §4.1", "ok", "A call to a function declared later in another file.",
  [("a.card", "function run() -> u32 {\n    return prepare();\n}\n"), ("b.card", "function prepare() -> u32 {\n    return Ok(1);\n}\n")])
MULTI["invalid/fun-103-recursion-across-files"] = ("FUN-5", "DN §3.7", "compile-error CE-FUN-1", "Recursion across two files.",
  [("a.card", "function first() {\n    return second();\n}\n"), ("b.card", "function second() {\n    return first();\n}\n")])

I = "invalid/"
add(I+"fun-101-direct-recursion.card", "FUN-5", "DN §3.7", "compile-error CE-FUN-1", "Direct recursion.",
"function countdown(value: u32) -> u32 {\n    return countdown(value);\n}\n")
INSPECT = "session buffer: u8[16];\n\nfunction inspect(data: ref u8[]) {\n    return Ok();\n}\n\n"
CLEAR = "function clear(target: inout u32) {\n    target = 0;\n    return Ok();\n}\n\n"
COUNT = "function count(value: ref u32) -> u32 {\n    return Ok(value);\n}\n\n"
ACC = "struct Account {\n    balance: u32;\n}\n\n"
add(I+"fun-104-missing-ref-mode.card", "FUN-7", "DN §3.7", "compile-error CE-FUN-2", "A ref parameter given an argument without ref.",
INSPECT + fn(["attempt inspect(buffer);", "return Ok();"]))
add(I+"fun-105-missing-inout-mode.card", "FUN-7", "DN §3.7", "compile-error CE-FUN-2", "An inout parameter given an argument without inout.",
"session counter: u32;\n\n" + CLEAR + fn(["attempt clear(counter);", "return Ok();"]))
add(I+"fun-106-ref-for-by-value.card", "FUN-7", "DN §3.7", "compile-error CE-FUN-2", "A by-value parameter given a ref argument.",
"function show(value: u32) {\n    return Ok();\n}\n\n" + fn(["var value: u32 = 1;", "attempt show(ref value);", "return Ok();"]))
add(I+"fun-107-inout-for-ref.card", "FUN-7", "DN §3.7", "compile-error CE-FUN-2", "A ref parameter given an inout argument.",
ACC + "session account: Account;\n\nfunction inspect(source: ref Account) {\n    return Ok();\n}\n\n" + fn(["attempt inspect(inout account);", "return Ok();"]))
add(I+"fun-108-temporary-reference.card", "FUN-9", "DN §3.8", "compile-error CE-FUN-3", "A reference to a temporary constructor value.",
ACC + "function get_balance(source: ref Account) -> u32 {\n    return Ok(source.balance);\n}\n\n"
+ fn(["var balance: u32 = attempt get_balance(ref Account { balance: 0 });", "return Ok();"]))
add(I+"fun-109-reference-to-literal.card", "FUN-9", "DN §3.8", "compile-error CE-FUN-3", "A reference to a literal.",
COUNT + fn(["var total: u32 = attempt count(ref 5);", "return Ok();"]))
add(I+"fun-110-reference-to-arithmetic.card", "FUN-9", "DN §3.8", "compile-error CE-FUN-3", "A reference to an arithmetic expression.",
COUNT + fn(["var total: u32 = attempt count(ref (limit + 1));", "return Ok();"], None, "limit: u32"))
add(I+"fun-111-constant-as-inout.card", "FUN-10", "DN §3.7, §3.8", "compile-error CE-FUN-4", "A constant passed as inout.",
"const LIMIT: u32 = 4;\n\n" + CLEAR + fn(["attempt clear(inout LIMIT);", "return Ok();"]))
add(I+"fun-112-ref-forwarded-as-inout.card", "FUN-15", "DN §3.8", "compile-error CE-FUN-4", "A ref parameter forwarded as inout.",
CLEAR + fn(["attempt clear(inout source);", "return Ok();"], None, "source: ref u32"))
add(I+"fun-113-by-value-as-inout.card", "FUN-10", "DN §3.7", "compile-error CE-FUN-4", "A by-value parameter passed as inout.",
CLEAR + fn(["attempt clear(inout value);", "return Ok();"], None, "value: u32"))
add(I+"fun-114-slice-in-initializer.card", "FUN-18", "DN §8.4", "compile-error CE-FUN-5", "A slice in a variable initializer.",
"session buffer: u8[16];\n\n" + fn(["var part: u8[4] = buffer[0..4];", "return Ok();"]))
add(I+"fun-115-slice-in-assignment.card", "FUN-18", "DN §8.4", "compile-error CE-FUN-5", "A slice on the right of an assignment.",
"session buffer: u8[16];\nsession destination: u8[4];\n\n" + fn(["destination = buffer[0..4];", "return Ok();"]))
FIXED = "session buffer: u8[16];\n\nfunction fixed(data: {mode}u8[4]) {{\n    return Ok();\n}}\n\n"
add(I+"fun-116-slice-by-value.card", "FUN-18", "DN §8.4", "compile-error CE-FUN-5", "A slice passed to a by-value parameter.",
FIXED.format(mode="") + fn(["attempt fixed(buffer[0..4]);", "return Ok();"]))
add(I+"fun-117-slice-to-fixed-parameter.card", "FUN-8", "DN §8.4; D-410", "compile-error CE-EXP-1", "A slice given to a fixed-size ref parameter.",
FIXED.format(mode="ref ") + fn(["attempt fixed(ref buffer[0..4]);", "return Ok();"]))
add(I+"fun-118-element-type-mismatch.card", "FUN-8", "DN §8.4", "compile-error CE-EXP-1", "A u32 array passed to ref u8[].",
INSPECT + "session counters: u32[4];\n\n" + fn(["attempt inspect(ref counters);", "return Ok();"]))
add(I+"fun-119-signed-slice-endpoint.card", "FUN-19", "D-410", "compile-error CE-EXP-9", "A signed slice endpoint.",
INSPECT + fn(["attempt inspect(ref buffer[start..4]);", "return Ok();"], None, "start: i8"))
add(I+"fun-120-constant-slice-out-of-range.card", "FUN-20", "D-429", "compile-error CE-CEX-4", "A constant slice end beyond the array length.",
INSPECT + fn(["attempt inspect(ref buffer[4..20]);", "return Ok();"]))
add(I+"fun-121-constant-slice-reversed.card", "FUN-20", "D-429", "compile-error CE-CEX-4", "Constant slice endpoints with start greater than end.",
INSPECT + fn(["attempt inspect(ref buffer[8..4]);", "return Ok();"]))

def hdr(rule, src, exp, note):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: fragment\n// expect: {exp}\n// note: {note}\n"
for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
for path, (rule, src, exp, note, files) in MULTI.items():
    d = conf / path; d.mkdir(parents=True, exist_ok=True)
    (d / "files.txt").write_text("".join(n + "\n" for n, _ in files), encoding="utf-8", newline="\n")
    for k, (n, body) in enumerate(files):
        (d / n).write_text((hdr(rule, src, exp, note) if k == 0 else "") + body, encoding="utf-8", newline="\n")
refs = set(re.findall(r"`((?:valid|invalid)/fun-[\w-]+(?:\.card|/))`", ch)) - SP14_OWNED
have = set(T) | {p + "/" for p in MULTI}
assert refs == have, sorted(refs ^ have)
print("tests:", len(have))
