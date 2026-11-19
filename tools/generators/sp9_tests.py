import re, sys, pathlib
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"
ch = (repo / "spec" / "10-state-and-initialization.md").read_text(encoding="utf-8")
def block(path):
    return re.search(r"\(conformance: `" + re.escape(path) + r"`\)\n\n```text\n(.*?)```", ch, re.S).group(1)
T = {}
def add(path, rule, src, expect, note, code): T[path] = (rule, src, expect, note, code)
for path, rule, src, note in [
 ("valid/sta-001-global-declarations.card", "STA-1, STA-2", "DN §3.9, §5.1", "Persistent and session globals without initializers."),
 ("valid/sta-002-setup-helper.card", "STA-4, STA-5", "DN §3.9", "A setup helper that sets session values from constants."),
 ("valid/sta-003-persistent-assignments.card", "STA-11, STA-12", "DN §7.1", "Persistent assignments to scalars, fields, elements and whole aggregates."),
 ("valid/sta-004-lifecycle-handlers.card", "STA-6, STA-7, STA-10", "D-422, D-438", "The two placeholder handlers."),
]:
    add(path, rule, src, "ok", note, block(path))
I = "invalid/"
for path, code, note, src in [
 ("sta-101-persistent-initializer.card", "persistent balance: u32 = 100;\n", "A persistent global with an initializer.", "DN §3.9"),
 ("sta-102-session-fill-initializer.card", "session scratch: u8[128] = fill(0);\n", "A session global initialized with fill.", "DN §3.9"),
 ("sta-103-persistent-zero-initializer.card", "persistent counter: u32 = 0;\n", "A persistent global initialized to zero.", "DN §3.9"),
 ("sta-104-session-false-initializer.card", "session ready: bool = false;\n", "A session bool initialized to false.", "DN §3.9"),
]:
    add(I + path, "STA-2", src, "compile-error CE-STA-1", note, code)
add(I+"sta-105-handler-with-payload.card", "STA-7", "D-422", "compile-error CE-STA-2", "A handler with a payload.",
"function on_install() -> u32 {\n    return Ok(1);\n}\n")
add(I+"sta-106-handler-with-parameter.card", "STA-7", "D-422", "compile-error CE-STA-2", "A handler with a parameter.",
"function on_session_start(level: u8) {\n    return Ok();\n}\n")
add(I+"sta-107-call-handler.card", "STA-9", "D-422", "compile-error CE-STA-3", "Application code calls a handler.",
"persistent installed_version: u16;\n\nfunction on_install() {\n    installed_version = 1;\n    return Ok();\n}\n\n"
"function reinstall() {\n    attempt on_install();\n    return Ok();\n}\n")
add(I+"sta-108-constant-named-like-handler.card", "STA-8, NAM-14", "D-422", "compile-error CE-NAM-5", "A constant using a handler name.",
"const on_install: u32 = 1;\n")
for path, (rule, src, exp, note, code) in T.items():
    hdr = f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: fragment\n// expect: {exp}\n// note: {note}\n"
    (conf / path).write_text(hdr + code, encoding="utf-8", newline="\n")
refs = set(re.findall(r"`((?:valid|invalid)/sta-[\w-]+\.card)`", ch))
assert refs == set(T), sorted(refs ^ set(T))
print("tests:", len(T))
