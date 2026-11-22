"""Write the WP6 conformance tests: Base Profile BER-TLV reader and DER writer (platform/base-profile.md §10)."""
import sys, pathlib
import sys, pathlib
from cardlang import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

SRC = "platform/base-profile.md BP-41 to BP-46"
T = {
    "valid/plt-008-tlv-apis.card": ("NAM-18, PLT-25", SRC, "ok", "Every card.tlv and card.der API, called with matching arguments.", """function exercise(data: ref u8[], out: inout u8[]) -> u32 {
    var length: u32 = attempt card.tlv.validate(ref data);
    var first: TlvHead = attempt card.tlv.head(ref data);
    var next: u32 = attempt card.tlv.skip(ref data);
    var size: u32 = attempt card.der.integer_size(ref data[0..4]);
    var at: u32 = attempt card.der.write_head(0x30, size, inout out);
    var n: u32 = attempt card.der.write_integer(ref data[0..4], inout out[at..out.length]);
    return Ok(at + n);
}
"""),
    "invalid/plt-114-der-length-as-bool.card": ("PLT-25, EXP-47", SRC, "compile-error CE-EXP-1", "The length of der.write_head is a u32, not a bool.", """function start(out: inout u8[]) -> u32 {
    var n: u32 = attempt card.der.write_head(0x30, true, inout out);
    return Ok(n);
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
        var length: u32 = attempt card.tlv.validate(ref request[1..end]);
        response[0..4] = encode_be(length);
        return Ok(4);
    } else if operation == 2 {
        var outer: TlvHead = attempt card.tlv.head(ref request[1..end]);
        var at: u32 = 1 + outer.size;
        var inner: TlvHead = attempt card.tlv.head(ref request[at..end]);
        var start: u32 = at + inner.size;
        response[0..inner.length] = request[start..start + inner.length];
        return Ok(inner.length);
    } else if operation == 3 {
        var first: TlvHead = attempt card.tlv.head(ref request[1..end]);
        response[0..4] = encode_be(first.tag);
        response[4..8] = encode_be(first.length);
        response[8] = 0;
        if first.constructed {
            response[8] = 1;
        }
        match first.class {
            TlvClass.Universal => {
                response[9] = 0;
            }
            TlvClass.Application => {
                response[9] = 1;
            }
            TlvClass.ContextSpecific => {
                response[9] = 2;
            }
            TlvClass.Private => {
                response[9] = 3;
            }
        }
        return Ok(10);
    } else if operation == 4 {
        var lr: u32 = attempt card.der.integer_size(ref request[1..33]);
        var ls: u32 = attempt card.der.integer_size(ref request[33..65]);
        var at: u32 = attempt card.der.write_head(0x30, lr + ls, inout response[0..response.length]);
        var n: u32 = attempt card.der.write_integer(ref request[1..33], inout response[at..response.length]);
        at = at + n;
        n = attempt card.der.write_integer(ref request[33..65], inout response[at..response.length]);
        at = at + n;
        var checked: u32 = attempt card.tlv.validate(ref response[0..at]);
        return Ok(at);
    } else if operation == 5 {
        var n: u32 = attempt card.der.write_head(0x30, 300, inout response[0..2]);
        return Ok(n);
    }
    return Err(AppError.UnknownOperation);
}
"""

sp = lambda b: " ".join(f"{x:02x}" for x in b)
def der_int(m):                                      # an independent reference encoder for the expectations
    m = bytes(m).lstrip(b"\0") or b"\0"
    if m[0] & 0x80: m = b"\0" + m
    return bytes([2, len(m)]) + m
def der_sig(r, s):
    body = der_int(r) + der_int(s)
    return bytes([0x30, len(body)]) + body
R1, S1 = bytes([0x80] + [0] * 31), bytes([0] * 31 + [1])            # a high bit, and leading zeros
assert der_sig(R1, S1) == bytes.fromhex("3026022100" + "80" + "00" * 31 + "020101")
R2, S2 = bytes(range(1, 33)), bytes(range(0x40, 0x60))               # a typical value: 32 bytes each
NEST = bytes.fromhex("0400")
for _ in range(15): NEST = bytes([0x30, len(NEST)]) + NEST          # 16 levels
DEEP = bytes([0x30, len(NEST)]) + NEST                               # 17 levels

SCENARIO = f"""install
power_on
command 02 7f 49 06 86 04 01 02 03 04    # walk a constructed object (a two-byte tag) to its primitive child
expect ok 01 02 03 04
command 03 9f 38 03 01 02 03             # a two-byte context-specific tag
expect ok 00 00 9f 38 00 00 00 03 00 02
command 03 7f 49 00                      # constructed, application class
expect ok 00 00 7f 49 00 00 00 00 01 01
command 03 5f 81 2d 82 00 01 aa          # a three-byte tag, the long length form 82
expect ok 00 5f 81 2d 00 00 00 01 00 01
command 01 04 81 02 aa bb                # a non-minimal length is accepted
expect ok 00 00 00 05
command 04 {sp(R1 + S1)}                 # DER signature: a 00 added to r, leading zeros stripped from s
expect ok {sp(der_sig(R1, S1))}
command 04 {sp(R2 + S2)}                 # DER signature, a typical value
expect ok {sp(der_sig(R2, S2))}
command 01 30 80                         # an indefinite length
expect err platform Malformed
command 01 04 ff                         # the reserved length byte
expect err platform Malformed
command 01 04 05 01 02                   # truncated content
expect err platform Malformed
command 01 30 02 04 01 02                # a child that overruns its parent's content
expect err platform Malformed
command 01 04 85 00 00 00 00 01          # a 5-byte length
expect err platform Unsupported
command 01 {sp(NEST)}                    # 16 levels
expect ok 00 00 00 {len(NEST):02x}
command 01 {sp(DEEP)}                    # 17 levels
expect err platform Unsupported
command 05                               # a 4-byte head does not fit a 2-byte view
expect err platform Capacity
"""

for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
d = conf / "runtime" / "run-022-tlv"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("PLT-25, STM-14", SRC, "runtime",
    "Base Profile TLV: walking BER-TLV, multi-byte tags and long lengths, DER signatures from r || s, every Malformed and Unsupported case.",
    "application") + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "wp6_owned.txt").write_text("\n".join(sorted(T) + ["runtime/run-022-tlv/"]) + "\n", encoding="utf-8", newline="\n")
print("tests:", len(T) + 1)
