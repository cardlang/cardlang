"""Write the WP12 tests: failures of the lifecycle handlers on_install and on_session_start (profile BP-55).

Found while drafting the VM execution model (VM1, vm/execution-model.md VEX-45): the reference interpreter ignored
handler failures, which BP-55 defines.
"""
import sys, pathlib
import sys, pathlib
from cardlang import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance

def hdr(rule, src, exp, note, kind="application"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

INSTALL = """errors AppError {
    Refused = 7;
}

persistent marker: u8;

function on_install() {
    marker = 1;
    return Err(AppError.Refused);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    response[0] = marker;
    return Ok(1);
}
"""

INSTALL_SCENARIO = """install              # on_install returns Err: installation fails (BP-55)
expect err app 7
"""

SESSION = """errors AppError {
    Refused = 7;
}

persistent starts: u8;
session ready: u8;

function on_session_start() {
    starts += 1;
    if (starts % 2) == 0 {
        return Err(AppError.Refused);
    }
    if starts == 3 {
        var cells: u8[2] = fill(0);
        var index: u8 = starts;
        cells[index] = 1;
    }
    ready = 1;
    return Ok();
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    response[0] = starts;
    response[1] = ready;
    return Ok(2);
}
"""

SESSION_SCENARIO = """install
expect ok
session_start        # the first session: on_session_start succeeds
expect ok
command 00
expect ok 01 01
session_start        # the second: on_session_start returns Err (BP-55)
expect err app 7
command 00           # the application is unavailable: every command is reported as a trap
expect trap
command 00
expect sw 6f00
session_start        # the third: on_session_start traps
expect trap BOUNDS
command 00
expect trap
session_end
session_start        # the fourth: Err again; the persistent writes of the failed starts remain
expect err app 7
session_start        # the fifth: available again
expect ok
command 00
expect ok 05 01
"""

written = []
for name, prog, scen, note in (
    ("run-027-install-failure", INSTALL, INSTALL_SCENARIO,
     "Profile BP-55: when on_install returns Err, installation fails and the outcome is reported."),
    ("run-028-session-start-failure", SESSION, SESSION_SCENARIO,
     "Profile BP-55: when on_session_start returns Err or traps, the application is unavailable until the next session start, and every command is reported as a trap."),
):
    d = conf / "runtime" / name; d.mkdir(parents=True, exist_ok=True)
    (d / "program.card").write_text(hdr("STA-6", "platform/base-profile.md BP-55", "runtime", note) + prog, encoding="utf-8", newline="\n")
    (d / "scenario.txt").write_text(scen, encoding="utf-8", newline="\n")
    written.append(f"runtime/{name}/")
(pathlib.Path(__file__).parent / "wp12_owned.txt").write_text("\n".join(written) + "\n", encoding="utf-8", newline="\n")
print("tests:", len(written))
