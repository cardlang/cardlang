"""Write the Draft 0.2 profile tests for command-lifetime keys (P1) and card.cbor.write_string (P2)."""
import sys, pathlib
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

SRC = "platform/base-profile.md BP-14, BP-24, BP-39"
PROGRAM = """errors AppError {
    UnknownOperation = 1;
}

const RP: u8[2] = b"rp";

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        attempt card.key.generate(5, KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Command });
        var length: u32 = attempt card.key.export_public(5, inout response);
        response[0] = 0x55;
        return Ok(1);
    } else if operation == 2 {
        var length: u32 = attempt card.key.export_public(5, inout response);
        return Ok(length);
    } else if operation == 3 {
        attempt card.key.generate(5, KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Command });
        var missing: u8 = request[200];
        return Ok(0);
    } else if operation == 4 {
        var at: u32 = attempt card.cbor.write_string(CborMajor.Text, ref RP, inout response[0..response.length]);
        at += attempt card.cbor.write_string(CborMajor.Bytes, ref request[1..request.length], inout response[at..response.length]);
        return Ok(at);
    } else if operation == 5 {
        var bad: u8[2] = [0xC3, 0x28];
        var n: u32 = attempt card.cbor.write_string(CborMajor.Text, ref bad, inout response);
        return Ok(n);
    } else if operation == 6 {
        var n: u32 = attempt card.cbor.write_string(CborMajor.Unsigned, ref request[1..request.length], inout response);
        return Ok(n);
    } else if operation == 7 {
        var n: u32 = attempt card.cbor.write_string(CborMajor.Bytes, ref request[1..request.length], inout response[0..2]);
        return Ok(n);
    }
    return Err(AppError.UnknownOperation);
}
"""
SCENARIO = """install
power_on
command 01           # a Command key is usable within its command
expect ok 55
command 02           # ... and gone in the next one (BP-14)
expect err platform NotFound
command 03           # created, then the command traps
expect trap BOUNDS
command 02           # a trap does not leave a Command key behind
expect err platform NotFound
command 04 aa bb cc  # write_string: "rp" as text, then 3 bytes (BP-39)
expect ok 62 72 70 43 aa bb cc
command 05           # text that is not valid UTF-8
expect err platform Malformed
command 06 01        # a major type that is not a string
expect err platform Malformed
command 07 aa bb     # head plus content do not fit 2 bytes
expect err platform Capacity
"""
d = conf / "runtime" / "run-025-command-keys-and-strings"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("PLT-22, PLT-23", SRC, "runtime",
    "Command-lifetime keys end with their command, also on a trap; card.cbor.write_string and its errors.", "application")
    + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "wp10_owned.txt").write_text("runtime/run-025-command-keys-and-strings/\n", encoding="utf-8", newline="\n")
print("tests: 1")
