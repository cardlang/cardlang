"""Write the WP13 tests (VM4b, vm/decisions.md V-37): runtime coverage that the VM5 measurements found missing.

- run-029: checked_div, checked_mul, checked_neg, wrapping_sub and wrapping_mul at their boundaries (EXP-29, EXP-30).
- run-030: structure fields through ref and inout references, nested and in persistent storage; fill of an array of
  structures; an aggregate payload forwarded through two calls (FUN-23, EXP-44, OUT-5).
"""
import sys, pathlib
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "checkers"))   # find layout
import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance

def hdr(rule, src, note):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: application\n// expect: runtime\n// note: {note}\n"

ARITH = """errors TestError {
    UnknownOperation = 1;
}

function put2(output: inout u8[], value: u16) -> u32 {
    var bytes: u8[2] = encode_be(value);
    output[0] = bytes[0];
    output[1] = bytes[1];
    return Ok(2);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        var r: u8 = attempt checked_mul(request[1], request[2]);
        response[0] = r;
        return Ok(1);
    } else if operation == 2 {
        var a: i8 = truncate<i8>(request[1]);
        var b: i8 = truncate<i8>(request[2]);
        var r: i8 = attempt checked_mul(a, b);
        response[0] = truncate<u8>(r);
        return Ok(1);
    } else if operation == 3 {
        var a: i8 = truncate<i8>(request[1]);
        var b: i8 = truncate<i8>(request[2]);
        var r: i8 = attempt checked_div(a, b);
        response[0] = truncate<u8>(r);
        return Ok(1);
    } else if operation == 4 {
        var a: i8 = truncate<i8>(request[1]);
        var r: i8 = attempt checked_neg(a);
        response[0] = truncate<u8>(r);
        return Ok(1);
    } else if operation == 5 {
        response[0] = wrapping_sub(request[1], request[2]);
        return Ok(1);
    } else if operation == 6 {
        var a: i8 = truncate<i8>(request[1]);
        var b: i8 = truncate<i8>(request[2]);
        var r: i8 = wrapping_sub(a, b);
        response[0] = truncate<u8>(r);
        return Ok(1);
    } else if operation == 7 {
        var a: u16 = decode_be<u16>(ref request[1..3]);
        var b: u16 = decode_be<u16>(ref request[3..5]);
        var r: u16 = wrapping_mul(a, b);
        return put2(inout response, r);
    } else if operation == 8 {
        var a: i8 = truncate<i8>(request[1]);
        var b: i8 = truncate<i8>(request[2]);
        var r: i8 = wrapping_mul(a, b);
        response[0] = truncate<u8>(r);
        return Ok(1);
    } else if operation == 9 {
        var a: i16 = decode_be<i16>(ref request[1..3]);
        var b: i16 = decode_be<i16>(ref request[3..5]);
        var r: i16 = attempt checked_mul(a, b);
        var w: u16 = truncate<u16>(r);
        return put2(inout response, w);
    }
    return Err(TestError.UnknownOperation);
}
"""

ARITH_SCENARIO = """install
session_start
command 01 0f 11     # 15 * 17 = 255
expect ok ff
command 01 10 10     # 16 * 16 = 256 does not fit u8
expect err platform Overflow
command 02 c0 02     # -64 * 2 = -128, the i8 minimum
expect ok 80
command 02 c0 03     # -64 * 3 = -192
expect err platform Underflow
command 02 40 02     # 64 * 2 = 128
expect err platform Overflow
command 03 80 ff     # the minimum divided by -1 (EXP-29)
expect err platform Overflow
command 03 07 00
expect err platform DivisionByZero
command 03 f9 02     # -7 / 2 truncates toward zero: -3
expect ok fd
command 04 80        # the negation of the minimum
expect err platform Overflow
command 04 05
expect ok fb
command 05 01 02     # 1 - 2 wraps to 255 (EXP-30)
expect ok ff
command 06 80 01     # -128 - 1 wraps to 127
expect ok 7f
command 07 01 00 01 00   # 256 * 256 wraps to 0
expect ok 00 00
command 07 ff ff 00 02   # 65535 * 2 wraps to 65534
expect ok ff fe
command 08 40 04     # 64 * 4 wraps to 0
expect ok 00
command 08 c0 03     # -64 * 3 = -192 wraps to 64
expect ok 40
command 09 c0 00 00 02   # -16384 * 2 = -32768, the i16 minimum
expect ok 80 00
command 09 c0 00 00 03   # -16384 * 3
expect err platform Underflow
"""

STRUCTS = """errors TestError {
    UnknownOperation = 1;
}

struct Point {
    x: u8;
    y: u16;
}

struct Box {
    low: Point;
    high: Point;
    tag: u8;
}

persistent stored: Box;
persistent points: Point[3];

function bump(p: inout Point, by: u8) {
    p.x += by;
    p.y = p.y + 1;
    return Ok();
}

function grow(b: inout Box) {
    attempt bump(inout b.low, 1);
    attempt bump(inout b.high, 2);
    b.tag = b.low.x + b.high.x;
    return Ok();
}

function read_x(p: ref Point) -> u8 {
    return Ok(p.x);
}

function make(seed: u8) -> Box {
    return Ok(Box { low: Point { x: seed, y: 0 }, high: Point { x: seed, y: 1 }, tag: 0 });
}

function forward(seed: u8) -> Box {
    return make(seed);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        var b: Box = attempt forward(request[1]);
        attempt grow(inout b);
        response[0] = b.low.x;
        response[1] = b.high.x;
        response[2] = b.tag;
        response[3] = truncate<u8>(b.high.y);
        return Ok(4);
    } else if operation == 2 {
        attempt grow(inout stored);
        response[0] = stored.low.x;
        response[1] = stored.tag;
        var x: u8 = attempt read_x(ref stored.high);
        response[2] = x;
        return Ok(3);
    } else if operation == 3 {
        points = fill(Point { x: request[1], y: 7 });
        attempt bump(inout points[1], 5);
        response[0] = points[0].x;
        response[1] = points[1].x;
        response[2] = truncate<u8>(points[1].y);
        response[3] = points[2].x;
        return Ok(4);
    }
    return Err(TestError.UnknownOperation);
}
"""

STRUCTS_SCENARIO = """install
session_start
command 01 05        # a Box forwarded through two calls, then fields changed through inout references
expect ok 06 07 0d 02
command 01 7f        # the tag overflows u8: 128 + 129
expect trap OVERFLOW
command 02           # the same through persistent storage; a field read through a ref
expect ok 01 03 02
command 02
expect ok 02 06 04
command 03 09        # fill of an array of structures; an element changed through a reference
expect ok 09 0e 08 09
"""

written = []
for name, rule, src, note, prog, scen in (
    ("run-029-checked-and-wrapping", "EXP-29, EXP-30", "VM4b (plans_and_notes/VM5-measurements.md §6)",
     "checked_div, checked_mul, checked_neg, wrapping_sub and wrapping_mul at their boundaries.", ARITH, ARITH_SCENARIO),
    ("run-030-fields-through-references", "FUN-23, EXP-44, OUT-5", "VM4b (plans_and_notes/VM5-measurements.md §6)",
     "Structure fields through ref and inout references, nested and persistent; fill of structures; a forwarded aggregate payload.",
     STRUCTS, STRUCTS_SCENARIO),
):
    d = conf / "runtime" / name; d.mkdir(parents=True, exist_ok=True)
    (d / "program.card").write_text(hdr(rule, src, note) + prog, encoding="utf-8", newline="\n")
    (d / "scenario.txt").write_text(scen, encoding="utf-8", newline="\n")
    written.append(f"runtime/{name}/")
(pathlib.Path(__file__).parent / "wp13_owned.txt").write_text("\n".join(written) + "\n", encoding="utf-8", newline="\n")
print("tests:", len(written))
