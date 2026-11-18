"""Write the WP5 conformance tests: Base Profile canonical CBOR (platform/base-profile.md §9)."""
import sys, pathlib
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

SRC = "platform/base-profile.md BP-34 to BP-40"
T = {
    "valid/plt-007-cbor-apis.card": ("NAM-18, PLT-25", SRC, "ok", "Every card.cbor API, called with matching arguments.", """function exercise(data: ref u8[], out: inout u8[]) -> u32 {
    var length: u32 = attempt card.cbor.validate(ref data);
    var first: CborHead = attempt card.cbor.head(ref data);
    var next: u32 = attempt card.cbor.skip(ref data[first.size..data.length]);
    var written: u32 = attempt card.cbor.write_head(CborMajor.Map, 2, inout out);
    written = attempt card.cbor.write_int(-7, inout out[written..out.length]);
    return Ok(length);
}
"""),
    "invalid/plt-113-cbor-major-as-integer.card": ("PLT-25, EXP-47", SRC, "compile-error CE-EXP-1", "The major type of write_head is a CborMajor, not an integer.", """function start(out: inout u8[]) -> u32 {
    var written: u32 = attempt card.cbor.write_head(5, 2, inout out);
    return Ok(written);
}
"""),
}

PROGRAM = """errors AppError {
    UnknownOperation = 1;
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    var end: u32 = request.length;
    if operation == 1 {
        var length: u32 = attempt card.cbor.validate(ref request[1..end]);
        response[0..4] = encode_be(length);
        return Ok(4);
    } else if operation == 2 {
        var checked: u32 = attempt card.cbor.validate(ref request[1..end]);
        var at: u32 = 1;
        var map: CborHead = attempt card.cbor.head(ref request[at..end]);
        at = at + map.size;
        var out: u32 = 0;
        for pair: u32 in 0..map.argument {
            var key: CborHead = attempt card.cbor.head(ref request[at..end]);
            at = at + key.size;
            var value: CborHead = attempt card.cbor.head(ref request[at..end]);
            if (key.argument == 1) or (key.argument == 2) {
                var start: u32 = at + value.size;
                response[out..out + value.argument] = request[start..start + value.argument];
                out = out + value.argument;
            }
            var skipped: u32 = attempt card.cbor.skip(ref request[at..end]);
            at = at + skipped;
        }
        return Ok(out);
    } else if operation == 3 {
        var tail: u8[2] = [170, 187];
        var at: u32 = attempt card.cbor.write_head(CborMajor.Map, 3, inout response[0..response.length]);
        var n: u32 = attempt card.cbor.write_int(1, inout response[at..response.length]);
        at = at + n;
        n = attempt card.cbor.write_int(2, inout response[at..response.length]);
        at = at + n;
        n = attempt card.cbor.write_int(3, inout response[at..response.length]);
        at = at + n;
        n = attempt card.cbor.write_int(-7, inout response[at..response.length]);
        at = at + n;
        n = attempt card.cbor.write_int(-1, inout response[at..response.length]);
        at = at + n;
        n = attempt card.cbor.write_head(CborMajor.Bytes, 2, inout response[at..response.length]);
        at = at + n;
        response[at..at + 2] = tail;
        at = at + 2;
        var checked: u32 = attempt card.cbor.validate(ref response[0..at]);
        return Ok(at);
    } else if operation == 4 {
        var first: CborHead = attempt card.cbor.head(ref request[1..end]);
        response[0..4] = encode_be(first.argument);
        return Ok(4);
    } else if operation == 5 {
        var n: u32 = attempt card.cbor.write_head(CborMajor.Unsigned, 1000, inout response[0..1]);
        return Ok(n);
    }
    return Err(AppError.UnknownOperation);
}
"""

REQUEST = "a4 01 44 01 02 03 04 02 62 72 70 03 82 01 02 04 f5"          # {1: h'01020304', 2: "rp", 3: [1, 2], 4: true}
SCENARIO = f"""install
power_on
command 02 {REQUEST}    # walk a CTAP-style map; return the bytes of key 1 and the text of key 2
expect ok 01 02 03 04 72 70
command 01 {REQUEST} 00    # validate returns the item's length; trailing bytes are not examined
expect ok 00 00 00 11
command 03                 # build {{1: 2, 3: -7, -1: h'aabb'}} in canonical order
expect ok a3 01 02 03 26 20 42 aa bb
command 01 a2 19 03 e8 00 61 7a 00    # 1000 (19 03 e8) before "z" (61 7a): bytewise order (BP-36)
expect ok 00 00 00 08
command 01 a2 61 7a 00 19 03 e8 00    # the same keys in length-first order, which BP-36 rejects
expect err platform Malformed
command 01 18 05           # not the shortest form
expect err platform Malformed
command 01 a2 01 00 01 00  # a duplicate key
expect err platform Malformed
command 01 9f 01 ff        # an indefinite length
expect err platform Malformed
command 01 44 01 02        # truncated
expect err platform Malformed
command 01 62 c3 28        # invalid UTF-8
expect err platform Malformed
command 01 1c              # a reserved additional-information value
expect err platform Malformed
command 01 f9 3c 00        # a float
expect err platform Unsupported
command 01 {"81 " * 15}00    # 16 levels
expect ok 00 00 00 10
command 01 {"81 " * 16}00    # 17 levels
expect err platform Unsupported
command 04 1b 00 00 00 01 00 00 00 00    # an argument above u32
expect err platform Unsupported
command 05                 # a 3-byte head does not fit a 1-byte view
expect err platform Capacity
"""

for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
d = conf / "runtime" / "run-021-cbor"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("PLT-25, FUN-24", SRC, "runtime",
    "Base Profile CBOR: walking a CTAP-style map, writing a canonical COSE-style map, every Malformed and Unsupported case.",
    "application") + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "wp5_owned.txt").write_text("\n".join(sorted(T) + ["runtime/run-021-cbor/"]) + "\n", encoding="utf-8", newline="\n")
print("tests:", len(T) + 1)
