"""Write the SP11 (chapter 12, host entry point) conformance tests and cross-check them with the chapter."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "checkers"))   # find layout
import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance
ch = (layout.at(repo).spec / "12-host-entry-point.md").read_text(encoding="utf-8")

def block(path):
    return re.search(r"\(conformance: `" + re.escape(path) + r"`\)\n\n```text\n(.*?)```", ch, re.S).group(1)

T = {}
def add(path, rule, src, expect, note, code, kind="application"):
    T[path] = (rule, src, expect, note, code, kind)

for path, rule, src, note in [
 ("valid/hep-001-minimal.card", "HEP-1, HEP-2", "DN §4", "The minimal entry point."),
 ("valid/hep-002-any-names.card", "HEP-1, HEP-2", "D-405", "Application-chosen command and parameter names."),
 ("valid/hep-003-dispatch-and-encode.card", "HEP-15, HEP-9", "DN §4", "Dispatch on the first byte; a u32 encoded big-endian."),
 ("valid/hep-004-protocol-status-in-payload.card", "HEP-11", "DN §4", "A protocol status in the payload and an Err."),
 ("valid/hep-005-counter-application.card", "HEP-1, HEP-9, HEP-15, TXN-3", "DN §13", "The counter application, the first representative application."),
]:
    add(path, rule, src, "ok", note, block(path))

def command(params="request: ref u8[], response: inout u8[]", ret=" -> u32", body="    return Ok(0);\n", name="process"):
    return f"command {name}({params}){ret} {{\n{body}}}\n"

I = "invalid/"
add(I+"hep-101-no-command.card", "HEP-1", "DN §4", "compile-error CE-HEP-1", "An application with no command.",
"function helper() {\n    return Ok();\n}\n")
add(I+"hep-102-two-commands.card", "HEP-1", "DN §4", "compile-error CE-HEP-2", "Two command declarations.",
command() + "\n" + command(name="process_again"))
add(I+"hep-103-wrong-return-type.card", "HEP-2", "DN §4", "compile-error CE-HEP-3", "A command returning u16.",
command(ret=" -> u16"))
add(I+"hep-104-no-return-type.card", "HEP-2", "DN §4", "compile-error CE-HEP-3", "A command with no return type.",
command(ret="", body="    return Ok();\n"))
add(I+"hep-105-inout-request.card", "HEP-2", "DN §4", "compile-error CE-HEP-3", "The request declared inout.",
command(params="request: inout u8[], response: inout u8[]"))
add(I+"hep-106-fixed-size-request.card", "HEP-2", "DN §4", "compile-error CE-HEP-3", "A fixed-size request.",
command(params="request: ref u8[16], response: inout u8[]"))
add(I+"hep-107-extra-parameter.card", "HEP-2", "DN §4", "compile-error CE-HEP-3", "A third parameter.",
command(params="request: ref u8[], response: inout u8[], extra: u8"))
add(I+"hep-108-call-command.card", "HEP-3, EXP-47", "DN §3.7", "compile-error CE-EXP-15", "A function that calls the command.",
command() + "\nfunction reenter(request: ref u8[], response: inout u8[]) -> u32 {\n    return process(ref request, inout response);\n}\n")

for path, (rule, src, exp, note, code, kind) in T.items():
    hdr = f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"
    (conf / path).write_text(hdr + code, encoding="utf-8", newline="\n")
refs = set(re.findall(r"`((?:valid|invalid)/hep-[\w-]+\.card)`", ch))
assert refs == set(T), sorted(refs ^ set(T))
print("tests:", len(T))
