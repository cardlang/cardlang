"""Write the WP1 conformance tests: slice assignment, equal and compare, wipe (Draft 0.2 language changes)."""
import re, sys, pathlib
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"
SPEC = "\n".join(f.read_text(encoding="utf-8") for f in sorted((repo / "spec").glob("*.md")))

def fn(body, ret=None, params="", name="check"):
    arrow = f" -> {ret}" if ret else ""
    return f"function {name}({params}){arrow} {{\n" + "".join("    " + l + "\n" for l in body) + "}\n"

T = {}
def add(path, rule, src, expect, note, code): T[path] = (rule, src, expect, note, code)

add("valid/fun-011-slice-assignment.card", "FUN-24", "D-447", "ok",
    "Slice assignments from a list, fill, another slice, a whole array and a view.",
    "session buffer: u8[8];\nsession block: u8[4];\n\n" + fn([
        "buffer[0..4] = [1, 2, 3, 4];",
        "buffer[4..8] = fill(0);",
        "buffer[2..6] = buffer[0..4];",
        "buffer[4..8] = block;",
        "output[0..2] = source[0..2];",
        "return Ok();"], None, "source: ref u8[], output: inout u8[]"))
add("valid/fun-012-views-equal-and-wipe.card", "EXP-53, EXP-54, STM-23", "D-448, D-449", "ok",
    "equal and compare on views and slices, and wipe of a slice.",
    fn(["var same: bool = equal(ref a[0..2], ref b);",
        "var order: i8 = compare(ref a, ref b[0..1]);",
        "wipe secret[0..4];",
        "return Ok(same);"], "bool", "a: ref u8[], b: ref u8[], secret: inout u8[]"))
add("valid/exp-019-equal-and-compare.card", "EXP-53, EXP-54", "D-448", "ok",
    "equal and compare on whole arrays.",
    "session x: u8[4];\nsession y: u8[4];\n\n" + fn([
        "var same: bool = equal(ref x, ref y);",
        "var order: i8 = compare(ref x, ref y);",
        "return Ok(same and (order == 0));"], "bool"))
add("valid/stm-013-wipe.card", "STM-23", "D-449", "ok",
    "wipe of a local, a session global and an inout view.",
    "session key: u8[16];\n\n" + fn([
        "var scratch: u8[4] = [1, 2, 3, 4];",
        "wipe scratch;",
        "wipe key;",
        "wipe secret;",
        "return Ok();"], None, "secret: inout u8[]"))
add("invalid/fun-123-slice-assignment-length.card", "FUN-24", "D-447", "compile-error CE-STM-8",
    "Slice lengths known to differ.",
    "session buffer: u8[8];\n\n" + fn(["buffer[0..4] = buffer[0..3];", "return Ok();"]))
add("invalid/fun-124-slice-assignment-into-ref.card", "FUN-24", "D-447", "compile-error CE-STM-2",
    "A slice assignment into a ref parameter.",
    fn(["data[0..2] = [1, 2];", "return Ok();"], None, "data: ref u8[]"))
add("invalid/fun-125-slice-assignment-element-type.card", "FUN-24", "D-447", "compile-error CE-EXP-1",
    "A slice assignment between different element types.",
    "session bytes: u8[4];\nsession words: u16[4];\n\n" + fn(["bytes[0..4] = words;", "return Ok();"]))
add("invalid/exp-145-equal-element-types.card", "EXP-53", "D-448", "compile-error CE-EXP-1",
    "equal on arrays with different element types.",
    "session bytes: u8[4];\nsession words: u16[4];\n\n" + fn(["return Ok(equal(ref bytes, ref words));"], "bool"))
add("invalid/exp-146-compare-bool.card", "EXP-54", "D-448", "compile-error CE-EXP-6",
    "compare on bool elements.",
    "session flags: bool[2];\n\n" + fn(["var order: i8 = compare(ref flags, ref flags);", "return Ok();"]))
add("invalid/exp-147-equal-by-value.card", "EXP-53", "D-448", "compile-error CE-FUN-2",
    "equal with by-value arguments.",
    "session x: u8[4];\nsession y: u8[4];\n\n" + fn(["return Ok(equal(x, y));"], "bool"))
add("invalid/stm-128-wipe-constant.card", "STM-23", "D-449", "compile-error CE-STM-2",
    "wipe of a constant.",
    "const LIMIT: u8 = 4;\n\n" + fn(["wipe LIMIT;", "return Ok();"]))
add("invalid/lex-116-wipe-is-keyword.card", "LEX-13", "D-449", "compile-error CE-SYN-1",
    "wipe is a keyword and cannot be a name.",
    "session wipe: u8;\n")

PROGRAM = """errors AppError {
    UnknownOperation = 1;
    Refused = 2;
}

persistent stored: u8[4];
session scratch: u8[2];

function copy_view(source: ref u8[], target: inout u8[]) {
    target[0..4] = source;
    return Ok();
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    var buffer: u8[8] = [1, 2, 3, 4, 5, 6, 7, 8];
    if operation == 1 {
        buffer[1..8] = buffer[0..7];
        response[0..8] = buffer;
        return Ok(8);
    } else if operation == 2 {
        buffer[0..7] = buffer[1..8];
        response[0..8] = buffer;
        return Ok(8);
    } else if operation == 3 {
        var count: u32 = convert<u32>(request[1]);
        buffer[0..count] = buffer[4..8];
        return Ok(0);
    } else if operation == 4 {
        var a: u8[3] = [1, 2, 3];
        var b: u8[3] = [1, 2, 4];
        var first: i8 = compare(ref a, ref b);
        var second: i8 = compare(ref b, ref a);
        var prefix: i8 = compare(ref a[0..2], ref a);
        response[0] = truncate<u8>(first);
        response[1] = truncate<u8>(second);
        response[2] = truncate<u8>(prefix);
        if equal(ref a, ref b) {
            response[3] = 1;
        } else {
            response[3] = 0;
        }
        return Ok(4);
    } else if operation == 5 {
        transaction {
            stored[0..4] = [9, 9, 9, 9];
            abort Err(AppError.Refused);
        }
    } else if operation == 6 {
        response[0..4] = stored;
        return Ok(4);
    } else if operation == 7 {
        scratch = [7, 8];
        wipe scratch;
        response[0..2] = scratch;
        return Ok(2);
    } else if operation == 9 {
        attempt copy_view(ref request[1..5], inout response[0..4]);
        return Ok(4);
    } else if operation == 8 {
        transaction {
            stored[0..2] = [5, 6];
        }
        return Ok(0);
    }
    return Err(AppError.UnknownOperation);
}
"""

SCENARIO = """install
power_on
command 01           # overlapping copy to the right: every element gets the original value
expect ok 01 01 02 03 04 05 06 07
command 02           # overlapping copy to the left
expect ok 02 03 04 05 06 07 08 08
command 03 03        # lengths differ at runtime
expect trap BOUNDS
command 03 04
expect ok
command 04           # compare: -1, 1, prefix -1; equal: false
expect ok ff 01 ff 00
command 05           # slice assignment into persistent storage, then abort
expect err app 2
command 06           # rolled back
expect ok 00 00 00 00
command 08           # committed
expect ok
command 06
expect ok 05 06 00 00
command 07           # wipe stores the default
expect ok 00 00
command 09 0a 0b 0c 0d    # a whole view parameter as the source of a slice assignment (WP8 finding T1)
expect ok 0a 0b 0c 0d
"""

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
d = conf / "runtime" / "run-018-array-operations"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("FUN-24, EXP-53, EXP-54, STM-23", "D-447, D-448, D-449", "runtime",
    "Overlapping slice copies, a runtime length mismatch, compare and equal, persistent slice copies under abort and commit, and wipe.",
    "application") + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
owned = sorted(T) + ["runtime/run-018-array-operations/"]
(pathlib.Path(__file__).parent / "wp1_owned.txt").write_text("\n".join(owned) + "\n", encoding="utf-8", newline="\n")
missing = [p for p in T if "`" + p + "`" not in SPEC and not p.startswith("invalid/lex-116")]
assert not missing, ("not referenced in the specification", missing)
print("tests:", len(T) + 1)
