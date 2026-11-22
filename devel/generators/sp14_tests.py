"""Write the SP14 conformance tests: tests for testable rules that no earlier test covered (SP14 §3.3, group (b))."""
import re, sys, pathlib
from cardlang import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance
SPEC = "\n".join(f.read_text(encoding="utf-8") for f in sorted((layout.at(repo).spec).glob("*.md")))

def sources(rules):
    """The decision and note sources of the given rules, taken from their Sources lines."""
    ds, notes = [], []
    for r in rules.split(", "):
        m = re.search(rf"^\*\*{r} \[Agreed\]\*\*.*?^\*Sources: (.*?)\.\*$", SPEC, re.M | re.S)
        for part in re.sub(r" \(OI-\d+\)", "", m.group(1)).split("; "):
            part = part.strip()
            if part.startswith(("DN", "PN")):
                doc, secs = part.split(" ", 1)
                entry = next((n for n in notes if n[0] == doc), None)
                if entry is None: entry = (doc, []); notes.append(entry)
                entry[1].extend(s for s in secs.split(", ") if s not in entry[1])
            else:
                ds += [d.strip() for d in part.split(", ") if d.strip().startswith("D-") and d.strip() not in ds]
    key = lambda s: [int(x) if x.isdigit() else x for x in s.lstrip("§").split(".")]
    notes = [f"{doc} " + ", ".join(sorted(secs, key=key)) for doc, secs in notes]
    return "; ".join(x for x in [", ".join(ds)] + notes if x)

def fn(body, ret=None, params="", name="check"):
    arrow = f" -> {ret}" if ret else ""
    return f"function {name}({params}){arrow} {{\n" + "".join("    " + l + "\n" for l in body) + "}\n"

T = {}
def add(path, rule, src, expect, note, code): T[path] = (rule, src, expect, note, code)

LONG = "identifier_" * 30 + "end"                      # 333 characters
add("valid/lex-009-long-identifier.card", "LEX-16", sources("LEX-16"), "ok",
    "A 333-character identifier is accepted and is not truncated.",
    f"const {LONG}: u32 = 1;\nconst {LONG[:-3]}: u32 = 2;\nconst TOTAL: u32 = {LONG} + {LONG[:-3]};\n")
add("invalid/lex-115-missing-semicolon.card", "LEX-23", sources("LEX-23"), "compile-error CE-SYN-1",
    "A line break does not end a declaration: no semicolon is inserted.",
    "const A: u32 = 1\nconst B: u32 = 2;\n")
add("invalid/nam-122-application-wrapper.card", "NAM-8", sources("NAM-8"), "compile-error CE-SYN-1",
    "There is no module or import syntax: the declaration does not derive.",
    "import card;\n\nconst A: u32 = 1;\n")
add("invalid/typ-115-no-64-bit.card", "TYP-8", sources("TYP-8"), "compile-error CE-NAM-2",
    "There is no u64 type: the name does not resolve.",
    "session big: u64;\n")
add("invalid/exp-143-boolean-operator-integer.card", "EXP-16", sources("EXP-16"), "compile-error CE-EXP-1",
    "An integer operand of and: there is no numeric truthiness.",
    fn(["return Ok(flags and true);"], "bool", "flags: u8"))
add("invalid/exp-144-convert-to-bool.card", "EXP-35", sources("EXP-35"), "compile-error CE-EXP-8",
    "There is no conversion to bool; write a comparison instead.",
    fn(["return Ok(convert<bool>(flags));"], "bool", "flags: u8"))
add("invalid/fun-122-reference-variable.card", "FUN-16", sources("FUN-16"), "compile-error CE-SYN-1",
    "There are no reference variables: ref is not a type.",
    fn(["var alias: ref u8 = value;", "return Ok();"], None, "value: ref u8"))
add("invalid/out-131-ok-as-value.card", "OUT-6", sources("OUT-6"), "compile-error CE-SYN-1",
    "Ok is not a constructor of a storable value.",
    fn(["var result: u32 = Ok(1);", "return Ok();"]))

PROGRAM = """errors TestError {
    UnknownOperation = 1;
    Refused = 2;
}

struct Pair {
    left: u8;
    right: u8;
}

struct Holder {
    data: u8[2];
}

session order: u32;
session reached: bool;
persistent total: u32;
persistent saved: u8[2];

function first() -> u32 {
    order = (order * 4) + 1;
    return Ok(1);
}

function second() -> u32 {
    order = (order * 4) + 2;
    return Ok(2);
}

function mark(value: ref u8) -> u8 {
    reached = true;
    return Ok(value);
}

function snapshot() -> u8[2] {
    return Ok(saved);
}

function bump(value: inout u32) {
    value = value + 1;
    return Ok();
}

function respond(output: inout u8[], value: u32) -> u32 {
    var bytes: u8[4] = encode_be(value);
    for index: u32 in 0..4 {
        output[index] = bytes[index];
    }
    return Ok(4);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        order = 0;
        var sum: u32 = attempt first() + attempt second();
        return respond(inout response, order);
    } else if operation == 2 {
        var a: Pair = Pair { left: 1, right: 2 };
        var b: Pair = a;
        b.left = 9;
        var source: u8[2] = [3, 4];
        var holder: Holder = Holder { data: source };
        source[0] = 5;
        var copy: u8[2] = attempt snapshot();
        copy[0] = 9;
        response[0] = a.left;
        response[1] = b.left;
        response[2] = holder.data[0];
        response[3] = saved[0];
        response[4] = copy[0];
        return Ok(5);
    } else if operation == 3 {
        var x: u8 = request[1];
        var y: u8 = request[2];
        response[0] = x & y;
        response[1] = x | y;
        response[2] = x ^ y;
        response[3] = ~x;
        response[4] = x << 3;
        response[5] = x >> 2;
        return Ok(6);
    } else if operation == 4 {
        reached = false;
        var value: u8 = attempt mark(ref request[1]);
        return Ok(0);
    } else if operation == 5 {
        if reached {
            response[0] = 1;
        } else {
            response[0] = 0;
        }
        return Ok(1);
    } else if operation == 6 {
        transaction {
            match bump(inout total) {
                Ok() => {
                }
                Err(_) => {
                }
            }
            abort Err(TestError.Refused);
        }
    } else if operation == 7 {
        transaction {
            match bump(inout total) {
                Ok() => {
                }
                Err(_) => {
                }
            }
        }
        return Ok(0);
    } else if operation == 8 {
        return respond(inout response, total);
    } else if operation == 9 {
        total = total + 10;
        var missing: u8 = request[200];
        return Ok(0);
    } else if operation == 10 {
        response[0] = 255;
        response[1] = request[0];
        return Ok(2);
    }
    return Err(TestError.UnknownOperation);
}
"""

SCENARIO = """install
power_on
command 01           # attempt first() + attempt second(): operands left to right
expect ok 00 00 00 06
command 02           # copies are independent of their sources
expect ok 01 09 03 00 09
command 03 c5 3c     # & | ^ ~ << >> on u8 at runtime
expect ok 04 fd f9 3a 28 31
command 04 07        # a valid element reference: the callee runs
expect ok
command 05
expect ok 01
command 04           # request[1] is out of range: trap before the callee starts
expect trap BOUNDS
command 05           # mark never ran
expect ok 00
command 07           # bump(inout total) inside a committed transaction
expect ok
command 06           # bump(inout total), then abort: the write through inout rolls back
expect err app 2
command 08
expect ok 00 00 00 01
command 09           # no implicit command transaction: the write before the trap stays
expect trap BOUNDS
command 08
expect ok 00 00 00 0b
command 0a           # writing the response does not change the request
expect ok ff 0a
"""

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
d = conf / "runtime" / "run-017-evaluation-and-copies"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("EXP-27, EXP-46, EXP-50, FUN-11, FUN-17, FUN-23, TXN-5, HEP-7",
    sources("EXP-27, EXP-46, EXP-50, FUN-11, FUN-17, FUN-23, TXN-5, HEP-7"),
    "runtime", "Evaluation order of attempt operands, independent copies, runtime bitwise results, argument preparation "
    "before entry, inout writes in an aborted transaction, no implicit command transaction, separate request and response.",
    "application") + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "sp14_owned.txt").write_text(
    "\n".join(sorted(T) + ["runtime/run-017-evaluation-and-copies/"]) + "\n", encoding="utf-8", newline="\n")
# Each test is referenced from the section of its rule; its code block there must equal the test code.
checked = 0
for path, (rule, src, exp, note, code) in T.items():
    m = re.search(r"\(conformance: `" + re.escape(path) + r"`\)\n(?:\n```text\n(.*?)```)?", SPEC, re.S)
    assert m, ("not referenced in the specification", path)
    if m.group(1) is not None:
        assert m.group(1) == code, ("code differs", path); checked += 1
print("tests:", len(T) + 1, "| chapter code blocks verified identical:", checked)
