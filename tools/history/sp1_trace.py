import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "checkers"))   # find layout
import layout
repo = pathlib.Path(sys.argv[1])
M = {  # D-ID: (rules, coverage)
"D-023": ("LEX-1, LEX-2, LEX-3, LEX-12", "covered"),
"D-024": ("LEX-22, LEX-23 (tokens); syntax side pending SP2–SP11", "partial"),
"D-036": ("LEX-17, LEX-18; contextual typing pending SP5", "partial"),
"D-037": ("LEX-24", "covered"),
"D-044": ("LEX-15 (spellings); declaration ban pending SP2", "partial"),
"D-301": ("LEX-12", "covered"),
"D-302": ("LEX-14", "covered"),
"D-303": ("LEX-12, LEX-13", "covered"),
"D-304": ("LEX-3", "covered"),
"D-305": ("LEX-6", "covered"),
"D-306": ("LEX-7, LEX-8, LEX-9", "covered"),
"D-307": ("LEX-17", "covered"),
"D-308": ("LEX-17, LEX-18", "covered"),
"D-309": ("LEX-20", "covered"),
"D-310": ("LEX-21", "covered"),
"D-311": ("LEX-5, LEX-11", "covered"),
"D-312": ("LEX-23", "covered"),
"D-401": ("LEX-1", "covered"),
"D-404": ("LEX-13, LEX-15; declaration ban pending SP2", "partial"),
"D-414": ("LEX-17, LEX-18, LEX-19", "covered"),
"D-423": ("LEX-4, LEX-5", "covered"),
"D-424": ("LEX-10, LEX-16, LEX-18", "covered"),
}
# Annex D: columns D-ID | Topic | SP | Rule IDs | OI | Coverage
p = layout.at(repo).spec / "annex-D-traceability.md"; t = p.read_text(encoding="utf-8")
for d, (rules, cov) in M.items():
    t, n = re.subn(rf"^(\| {d} \|[^|]*\|[^|]*\| )[^|]*(\|[^|]*\| )[^|]*\|$", rf"\g<1>{rules} \g<2>{cov} |", t, flags=re.M)
    assert n == 1, d
t = t.replace("| 02-lexical-structure.md | SP1 | DN §3.0, §3.3 (literal forms), §6.5 (negative minimum) | pending |",
              "| 02-lexical-structure.md | SP1 | DN §3.0, §3.3 (literal forms), §3.5, §3.6, §4.1, §6.5 (negative minimum) | LEX-1 … LEX-24 |")
t = t.replace("| annex-A-grammar.md | SP1–SP14 | DN §3.0 plus the syntax of every chapter | pending |",
              "| annex-A-grammar.md | SP1–SP14 | DN §3.0 plus the syntax of every chapter | A.1 complete (LEX rules); A.2 pending |")
p.write_text(t, encoding="utf-8", newline="\n")
# Register: last column
p = layout.at(repo).decision_register; t = p.read_text(encoding="utf-8")
for d, (rules, cov) in M.items():
    t, n = re.subn(rf"^(\| {d} \|.*\| )[^|]*\|$", rf"\g<1>{rules} |", t, flags=re.M)
    assert n == 1, d
p.write_text(t, encoding="utf-8", newline="\n")
# Annex C resolution log
p = layout.at(repo).spec / "annex-C-open-issues.md"; t = p.read_text(encoding="utf-8")
for oi, txt in [("OI-1", "Applied in chapter 2: LEX-1 (SP1)"),
                ("OI-4", "Applied in chapter 2: LEX-13, LEX-15 (SP1); declaration ban in chapter 3 (SP2)"),
                ("OI-14", "Applied in chapter 2: LEX-17 to LEX-19 (SP1)")]:
    t, n = re.subn(rf"^(\| 2026-11-15 \| {oi} \|.*\| User \| )Pending: applied when SP1 drafts its chapter \|$", rf"\g<1>{txt} |", t, flags=re.M)
    assert n == 1, oi
for oi, rules in [("OI-1", "LEX-1"), ("OI-4", "LEX-13, LEX-15; chapter 3 pending (SP2)"), ("OI-14", "LEX-17, LEX-18, LEX-19")]:
    sec_start = t.index(f"## {oi} ")
    sec_end = t.index("\n## ", sec_start + 1)
    sec = t[sec_start:sec_end]
    sec2 = re.sub(r"- \*\*Affected rules:\*\* pending \([^)]*\)", f"- **Affected rules:** {rules}", sec, count=1)
    assert sec2 != sec, oi
    t = t[:sec_start] + sec2 + t[sec_end:]
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
