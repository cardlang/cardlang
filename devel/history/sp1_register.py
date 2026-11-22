import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "checkers"))   # find layout
import layout
repo = pathlib.Path(sys.argv[1])
DATE = "2026-11-15"
BODY = [
("Identifiers are case-sensitive ASCII: first character a letter or underscore, then letters, digits or underscores", "DN §3.0"),
("`_` alone is reserved for an ignored pattern", "DN §3.0"),
("No escaped or Unicode identifiers; keywords cannot be identifiers", "DN §3.0"),
("Comments may contain Unicode; identifiers and language tokens are ASCII", "DN §3.0"),
("Spaces, tabs and line breaks separate tokens; indentation has no semantic meaning", "DN §3.0"),
("Line comments `//` and block comments `/* */`; block comments do not nest; an unterminated block comment is a compilation error", "DN §3.0"),
("Integer literals are decimal, hexadecimal or binary; a leading zero does not mean octal", "DN §3.0"),
("Numeric underscores appear only between digits: no leading, trailing or consecutive underscores, and none directly after a base prefix", "DN §3.0"),
("No negative-literal token; negative values use unary `-`", "DN §3.0, §6.5"),
("Boolean literals are exactly `true` and `false`; no string, character, floating-point or null literals", "DN §3.0"),
("File and line boundaries are preserved for diagnostics; a trailing comment or token cannot consume the next file's text", "DN §3.0, §4.1"),
("Semicolons are mandatory; there is no automatic semicolon insertion", "DN §3.0"),
]
hdr = "| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |\n|---|---|---|---|---|---|---|---|---|\n"
p = layout.at(repo).decision_register
t = p.read_text(encoding="utf-8")
rows = [f"| D-{301+i} | {topic} | Agreed (DN body text) | [Agreed] | language | {sec} | SP1 |  | pending |" for i, (topic, sec) in enumerate(BODY)]
old = "None registered yet. Sub-plans SP1–SP13 add rows here as they reach each DN section.\n\n" + hdr.rstrip()
assert old in t
t = t.replace(old, "Sub-plans add rows here as they reach each DN section.\n\n" + hdr + "\n".join(rows))
res = [
f"| D-423 | Leading UTF-8 byte-order mark ignored; LF, CR and CRLF are line breaks (CRLF counts once) | Resolved by user {DATE} | [Agreed] | language | Annex C OI-23 | SP1 | OI-23 | pending |",
f"| D-424 | Longest-match tokens; numeric-run rule for literals; no identifier length limit | Resolved by user {DATE} | [Agreed] | language | Annex C OI-24 | SP1 | OI-24 | pending |",
]
t = t.rstrip("\n") + "\n" + "\n".join(res) + "\n"
p.write_text(t, encoding="utf-8", newline="\n")

p = layout.at(repo).spec / "annex-D-traceability.md"
t = p.read_text(encoding="utf-8").rstrip("\n")
add = [f"| D-{301+i} | {topic.split(';')[0]} | SP1 | — |  | pending |" for i, (topic, sec) in enumerate(BODY)]
add += ["| D-423 | BOM ignored; LF, CR and CRLF are line breaks | SP1 | — | OI-23 | pending |",
        "| D-424 | Longest-match tokens; numeric-run rule; no identifier length limit | SP1 | — | OI-24 | pending |"]
p.write_text(t + "\n" + "\n".join(add) + "\n", encoding="utf-8", newline="\n")

p = layout.at(repo).spec / "annex-C-open-issues.md"
t = p.read_text(encoding="utf-8")
t = t.replace("| OI-22 | Language rules for lifecycle handler functions | Gap | SP9 | Open |",
 "| OI-22 | Language rules for lifecycle handler functions | Gap | SP9 | Open |\n| OI-23 | Source text details: byte-order mark and line breaks | Gap | SP1 | Resolved |\n| OI-24 | Token formation and identifier length | Gap | SP1 | Resolved |")
entries = f"""## OI-23 — Source text details: byte-order mark and line breaks

- **Kind:** gap
- **Sources:** DN §3.0 ("Source files are UTF-8"; "Spaces, tabs and line breaks separate tokens"); D-023
- **Affected rules:** LEX-4, LEX-5
- **Questions:**
  1. Is a UTF-8 byte-order mark at the start of a file permitted and ignored, or an error?
  2. Which sequences are line breaks: LF, CR, CRLF?
- **Options:**
  1. Ignored or error.
  2. All three, or LF and CRLF only.
- **Recommendation:**
  1. Ignored, because common Windows editors write one.
  2. All three, with CRLF counting as one line break.
- **Status:** resolved {DATE} (D-423)
- **Decision:** Recommendation adopted.

## OI-24 — Token formation and identifier length

- **Kind:** gap
- **Sources:** DN §3.0; OI-14 resolution (D-414)
- **Affected rules:** LEX-10, LEX-16, LEX-18
- **Questions:**
  1. Is the longest possible token always taken?
  2. Is a numeric literal the longest run of letters, digits and `_` starting with a digit, which must wholly match a literal form? This is how the OI-14 decision is implemented.
  3. Is there a maximum identifier length?
- **Recommendation:**
  1. Yes.
  2. Yes.
  3. No language limit. A tool may report a limit but must not silently truncate.
- **Status:** resolved {DATE} (D-424)
- **Decision:** Recommendation adopted.

---

## Resolution log"""
t = t.replace("---\n\n## Resolution log", entries, 1)
t = t.rstrip("\n") + f"\n| {DATE} | OI-23 | BOM ignored; LF, CR and CRLF are line breaks (D-423) | User | Applied in chapter 2 (SP1) |\n| {DATE} | OI-24 | Longest match; numeric-run rule; no identifier length limit (D-424) | User | Applied in chapter 2 (SP1) |\n"
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
