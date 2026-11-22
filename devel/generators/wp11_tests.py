"""Write the WP11 tests: session boundaries (STA-4, OI-59) and the raw-binding envelope (profile BP-53, BP-56)."""
import sys, pathlib
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "checkers"))   # find layout
import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance

def hdr(rule, src, exp, note, kind="fragment", binding=None):
    b = f"// binding: {binding}\n" if binding else ""
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n{b}// expect: {exp}\n// note: {note}\n"

PROGRAM = """errors AppError {
    Refused = 7;
}

session counter: u8;
session marker: u8;

function on_session_start() {
    marker = 0x5A;
    return Ok();
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        counter += 1;
        response[0] = counter;
        response[1] = marker;
        return Ok(2);
    } else if operation == 2 {
        return Err(AppError.Refused);
    } else if operation == 3 {
        var length: u32 = attempt card.key.export_public(9, inout response);
        return Ok(length);
    } else if operation == 4 {
        var missing: u8 = request[200];
        return Ok(0);
    } else if operation == 5 {
        attempt card.key.generate(3, KeySpec { type: KeyType.Aes128, storage: KeyStorage.Volatile });
        return Ok(0);
    } else if operation == 6 {
        attempt card.key.delete(3);
        return Ok(0);
    }
    return Err(AppError.Refused);
}
"""

SCENARIO = """install
session_start        # the host opens a session (BP-53a, BP-56); on_session_start runs
command 01           # the envelope: category 00, code 0000, then the data (BP-53)
expect raw 00 00 00 01 5a
command 01           # session state persists from command to command
expect raw 00 00 00 02 5a
command 02           # an application error: category 01 and the member's code
expect raw 01 00 07
command 03           # a platform error: category 02 and the CardError code (NotFound = 0x0010)
expect raw 02 00 10
command 04           # a trap: category 03
expect raw 03 00 00
command 01           # a trap does not reset session state
expect raw 00 00 00 03 5a
command 05           # a volatile key, for the rest of the session
expect raw 00 00 00
session_end          # the host closes the session
session_start
command 01           # a new session: defaults again, then on_session_start
expect raw 00 00 00 01 5a
command 06           # the volatile key ended with the previous session
expect raw 02 00 10
command 01
expect raw 00 00 00 02 5a
session_start        # a new session start ends the open session (STA-4)
command 01
expect raw 00 00 00 01 5a
"""

d = conf / "runtime" / "run-026-raw-binding-sessions"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("STA-4, STA-6, PLT-9", "D-459; platform/base-profile.md BP-53, BP-56", "runtime",
    "Raw binding: the response envelope for each outcome category, and session boundaries opened and closed by the host.",
    "application", "raw") + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "wp11_owned.txt").write_text("runtime/run-026-raw-binding-sessions/\n", encoding="utf-8", newline="\n")
print("tests: 1")
