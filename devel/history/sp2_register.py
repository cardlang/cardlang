import sys, pathlib
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "checkers"))   # find layout
import layout
repo = pathlib.Path(sys.argv[1]); DATE = "2026-11-15"
BODY = [
("A declaration cannot span source files", "DN §3.0"),
("Functions and types may be used before their declaration, including across files", "DN §4.1, §4.2"),
("Shadowing any visible name is forbidden (application declarations, parameters, locals, loop and pattern bindings); same-scope duplicates are errors; sibling scopes may reuse names", "DN §3.6, §4.2"),
("Function, command, structure, enum and error-set declarations are top-level only", "DN §4.2"),
("Field names never become bare names; dot access resolves from the receiver's type", "DN §4.2"),
("Enum variants and error members are always qualified (`Owner.Member`) and are never imported as bare names", "DN §3.11, §4.2, §6.3"),
("Platform-supplied configuration structures and algorithm enums use the ordinary naming rules, with no imports, namespaces or private fields", "DN §11.1"),
("Plain `var` and combined qualifiers are forbidden at application scope; there is no `local` keyword", "DN §5.1"),
]
p = layout.at(repo).decision_register; t = p.read_text(encoding="utf-8")
anchor = "| D-312 |"
i = t.index(anchor); j = t.index("\n", i)
rows = "\n".join(f"| D-{313+k} | {a} | Agreed (DN body text) | [Agreed] | language | {s} | SP2 |  | pending |" for k, (a, s) in enumerate(BODY))
t = t[:j+1] + rows + "\n" + t[j+1:]
t = t.rstrip("\n") + "\n" + "\n".join([
f"| D-425 | Primitive type names are predeclared names in every application scope, not keywords | Resolved by user {DATE} | [Agreed] | language | Annex C OI-25 | SP2 | OI-25 | pending |",
f"| D-426 | A file listed twice is a build-configuration error; an empty file list is allowed by the language | Resolved by user {DATE} | [Agreed] | tooling | Annex C OI-26 | SP2 | OI-26 | pending |"]) + "\n"
p.write_text(t, encoding="utf-8", newline="\n")

p = layout.at(repo).spec / "annex-D-traceability.md"; t = p.read_text(encoding="utf-8")
i = t.index("| D-312 |"); j = t.index("\n", i)
rows = "\n".join(f"| D-{313+k} | {a.split(';')[0].split(' (')[0]} | SP2 | — |  | pending |" for k, (a, s) in enumerate(BODY))
t = t[:j+1] + rows + "\n" + t[j+1:]
t = t.rstrip("\n") + "\n| D-425 | Primitive type names are predeclared | SP2 | — | OI-25 | pending |\n| D-426 | File-list duplicates are a build error; empty list allowed | SP2 | — | OI-26 | pending |\n"
p.write_text(t, encoding="utf-8", newline="\n")

p = layout.at(repo).spec / "annex-C-open-issues.md"; t = p.read_text(encoding="utf-8")
t = t.replace("| OI-24 | Token formation and identifier length | Gap | SP1 | Resolved |",
 "| OI-24 | Token formation and identifier length | Gap | SP1 | Resolved |\n| OI-25 | Primitive type names | Gap | SP2 | Resolved |\n| OI-26 | Build file-list constraints | Gap | SP2 | Resolved |")
entries = f"""## OI-25 — Primitive type names

- **Kind:** gap
- **Sources:** DN §3.1 (primitive types); D-075; D-404 (the keyword list does not include the type names)
- **Affected rules:** NAM-14, NAM-21
- **Question:** The names `u8 u16 u32 i8 i16 i32 bool` are not keywords. Can an application declare something with one of these names?
- **Options:**
  - (a) No. They are predeclared type names in the application scope.
  - (b) No. Make them keywords.
  - (c) Yes, they may be redeclared.
- **Recommendation:** (a). This keeps the agreed keyword list unchanged.
- **Status:** resolved {DATE} (D-425)
- **Decision:** Option (a). Declaring one is CE-NAM-5, and shadowing one is CE-NAM-3.

## OI-26 — Build file-list constraints

- **Kind:** gap
- **Sources:** DN §4.1; D-021
- **Affected rules:** NAM-3
- **Questions:**
  1. What happens if the same file is listed twice in the build file list?
  2. Is an empty file list allowed?
- **Recommendation:**
  1. A build-configuration error, outside the language.
  2. Allowed by the language. It fails because there is no `command` (chapter 12).
- **Status:** resolved {DATE} (D-426)
- **Decision:** Recommendation adopted.

---

## Resolution log"""
t = t.replace("---\n\n## Resolution log", entries, 1)
t = t.rstrip("\n") + f"\n| {DATE} | OI-25 | Primitive type names are predeclared (D-425) | User | Applied in chapter 3: NAM-14 (SP2) |\n| {DATE} | OI-26 | File-list duplicates are a build error; empty list allowed (D-426) | User | Applied in chapter 3: NAM-3 (SP2) |\n"
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
