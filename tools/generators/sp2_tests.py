import re, sys, pathlib
# Tests written by sp14_tests.py and wp1_tests.py are referenced in this chapter but owned by those generators.
SP14_OWNED = set().union(*(set(f.read_text().split()) for f in pathlib.Path(__file__).parent.glob("*_owned.txt")))
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"
ch = (repo / "spec" / "03-program-structure-and-names.md").read_text(encoding="utf-8")

RULES = {
"valid/nam-001-shared-scope-forward-use.card": ("NAM-11, NAM-13", "DN §3.7, §4.1, §4.2"),
"valid/nam-003-member-scopes.card": ("NAM-15, NAM-17", "DN §3.11, §4.2"),
"valid/nam-004-sibling-scopes.card": ("NAM-19, NAM-21", "DN §4.2"),
"valid/nam-005-qualified-members.card": ("NAM-15, NAM-16", "DN §3.11, §4.2, §6.3"),
"invalid/nam-101-duplicate-across-kinds.card": ("NAM-11", "DN §4.2"),
"invalid/nam-103-overloading.card": ("NAM-12", "DN §3.7, §4.2"),
"invalid/nam-104-global-var.card": ("NAM-9", "DN §5.1"),
"invalid/nam-105-combined-qualifiers.card": ("NAM-9", "DN §5.1"),
"invalid/nam-106-local-storage-keyword.card": ("NAM-10", "DN §5.1"),
"invalid/nam-107-local-const.card": ("NAM-10", "DN §5.1"),
"invalid/nam-108-nested-function.card": ("NAM-7", "DN §4.2"),
"invalid/nam-109-parameter-shadows-global.card": ("NAM-21", "DN §4.2"),
"invalid/nam-110-local-shadows-local.card": ("NAM-21", "DN §3.6"),
"invalid/nam-111-self-reference.card": ("NAM-20, NAM-22", "DN §4.2"),
"invalid/nam-112-use-outside-scope.card": ("NAM-19, NAM-22", "DN §3.6"),
"invalid/nam-113-duplicate-field.card": ("NAM-15", "DN §4.2"),
"invalid/nam-114-bare-variant.card": ("NAM-16, NAM-22", "DN §3.11"),
"invalid/nam-115-unknown-member.card": ("NAM-16", "DN §4.2, §6.3"),
"invalid/nam-116-redeclare-intrinsic.card": ("NAM-14", "DN §4.2; D-404"),
"invalid/nam-117-redeclare-card.card": ("NAM-14", "D-404, D-406"),
"invalid/nam-118-redeclare-primitive.card": ("NAM-14", "D-425"),
"invalid/nam-119-same-scope-duplicate.card": ("NAM-21", "DN §4.2"),
"invalid/nam-120-unknown-platform-path.card": ("NAM-18", "D-406"),
"invalid/nam-121-parameter-shadows-primitive.card": ("NAM-14, NAM-21", "D-425"),
}

def hdr(rule, source, expect, note):
    return (f"// rule: {rule}\n// source: {source}\n// status: agreed\n// kind: fragment\n"
            f"// expect: {expect}\n// note: {note}\n")

# Pair each conformance reference with the example paragraph it ends and the next code block.
pat = re.compile(r"\*(Valid|Invalid)[^*]*:\*(.*?)\(conformance: `([^`]+)`\)\n(?:\n```text\n(.*?)```)?", re.S)
done = set()
for kind, text, path, code in pat.findall(ch):
    if path.endswith("/") or path in SP14_OWNED:
        continue
    rule, src = RULES[path]
    m = re.search(r"\*\*(CE-[A-Z]+-\d+)\*\*", text)
    expect = f"compile-error {m.group(1)}" if m else "ok"
    assert (kind == "Valid") == (expect == "ok"), path
    note = re.sub(r"\s+", " ", text.split("**")[0]).strip().rstrip(".").strip()
    p = conf / path
    p.write_text(hdr(rule, src, expect, note[:1].upper() + note[1:] + ".") + code, encoding="utf-8", newline="\n")
    done.add(path)
assert done == set(RULES), set(RULES) ^ done

def multi(path, rule, src, expect, note, files):
    d = conf / path; d.mkdir(parents=True, exist_ok=True)
    (d / "files.txt").write_text("".join(n + "\n" for n, _ in files), encoding="utf-8", newline="\n")
    for k, (name, body) in enumerate(files):
        (d / name).write_text((hdr(rule, src, expect, note) if k == 0 else "") + body, encoding="utf-8", newline="\n")

multi("valid/nam-002-multi-file-any-order", "NAM-4, NAM-11, NAM-13", "DN §4.1", "ok",
      "Declarations used across three files. Must pass for every order of files.txt.", [
 ("a.card", "function total() -> u32 {\n    var base: u32 = attempt base_value();\n    return Ok(base + EXTRA);\n}\n"),
 ("b.card", "function base_value() -> u32 {\n    return Ok(BASE);\n}\n"),
 ("c.card", "const BASE: u32 = 32;\nconst EXTRA: u32 = BASE * 2;\n")])
multi("valid/nam-006-empty-file", "NAM-2", "DN §3.0", "ok",
      "a.card contains only comments; b.card has a declaration.", [
 ("a.card", "// This file intentionally declares nothing.\n"),
 ("b.card", "const A: u32 = 1;\n")])
multi("invalid/nam-102-duplicate-across-files", "NAM-11", "DN §4.1, §4.2", "compile-error CE-NAM-1",
      "The same function is declared in two files.", [
 ("a.card", "function helper() {\n    return Ok();\n}\n"),
 ("b.card", "function helper() {\n    return Ok();\n}\n")])
print("tests written:", len(done) + 3)
