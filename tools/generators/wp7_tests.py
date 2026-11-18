"""Write the WP7 conformance tests: Base Profile transport bindings (platform/base-profile.md §11)."""
import sys, pathlib
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"

def hdr(rule, src, exp, note, kind="fragment", binding=None):
    b = f"// binding: {binding}\n" if binding else ""
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n{b}// expect: {exp}\n// note: {note}\n"

SRC = "platform/base-profile.md BP-47 to BP-55"
T = {
    "valid/plt-009-iso-error-codes.card": ("OUT-16", SRC, "ok", "iso7816",
        "In the ISO 7816 binding, application error codes are ISO status words (BP-52).", """errors IsoError {
    WrongData = 0x6A80;
    InsNotSupported = 0x6D00;
    Pending = 0x9101;
}
"""),
    "valid/plt-010-raw-binding-any-code.card": ("OUT-16", SRC, "ok", "raw",
        "In the raw binding, application error codes are only restricted by OUT-16 (BP-53).", """errors AppError {
    Refused = 1;
}
"""),
    "invalid/plt-115-iso-code-not-a-status-word.card": ("OUT-16", SRC, "profile-error BP-52", "iso7816",
        "Code 1 is not an ISO status word, so the build for the ISO 7816 binding is rejected.", """errors AppError {
    Refused = 1;
}
"""),
    "invalid/plt-116-iso-code-platform-range.card": ("OUT-16", SRC, "profile-error BP-52", "iso7816",
        "Codes 6F00 to 6FFF are reserved for platform errors and traps (BP-51).", """errors AppError {
    Refused = 0x6F05;
}
"""),
}

PROGRAM = """errors IsoError {
    WrongLength = 0x6700;
    InsNotSupported = 0x6D00;
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length >= 4 else IsoError.WrongLength;
    var ins: u8 = request[1];
    if ins == 0x10 {
        var n: u32 = request.length - 4;
        response[0..n] = request[4..request.length];
        return Ok(n);
    } else if ins == 0x20 {
        var length: u32 = attempt card.key.export_public(9, inout response);
        return Ok(length);
    } else if ins == 0x30 {
        var zero: u8 = request[2];
        var quotient: u8 = 1 / zero;
        return Ok(0);
    }
    return Err(IsoError.InsNotSupported);
}
"""

SCENARIO = """install
power_on
command 80 10 00 00 01 02 03    # CLA INS P1 P2, then the data field (BP-50)
expect ok 01 02 03
command 80 10 00 00 01 02
expect sw 9000
command 80 20 00 00             # CardError.NotFound is 6F00 + 0x10 (BP-51)
expect sw 6f10
command 80 30 00 00             # a trap
expect sw 6f00
command 80 40 00 00             # the application's own status word
expect sw 6d00
command 80                      # too short for a header
expect sw 6700
"""

for path, (rule, src, exp, binding, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note, binding=binding) + code, encoding="utf-8", newline="\n")
d = conf / "runtime" / "run-023-iso7816-binding"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("HEP-5, HEP-12, PLT-9", SRC, "runtime",
    "The ISO 7816 binding: the request layout, and the status words of success, application and platform errors, and traps.",
    "application", "iso7816") + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "wp7_owned.txt").write_text("\n".join(sorted(T) + ["runtime/run-023-iso7816-binding/"]) + "\n", encoding="utf-8", newline="\n")
print("tests:", len(T) + 1)
