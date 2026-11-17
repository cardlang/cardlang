"""One-off (SP14): add to Annex D §D.2 and the decision register every rule whose Sources line cites a decision.

Existing entries are kept; missing rule IDs are appended in chapter order.
"""
import re, sys, pathlib
repo = pathlib.Path(sys.argv[1])
ORDER = "LEX NAM TYP CEX EXP STM FUN OUT STA TXN HEP RTF PLT".split()
key = lambda r: (ORDER.index(r.split("-")[0]), int(r.split("-")[1]))
spec = "\n".join(f.read_text(encoding="utf-8") for f in sorted((repo / "spec").glob("*.md")))
cites = {}
for m in re.finditer(r"^\*\*([A-Z]{3}-\d+) \[\w+\]\*\*.*?^\*Sources: (.*?)$", spec, re.M | re.S):
    for d in re.findall(r"D-\d{3}", m.group(2)): cites.setdefault(d, set()).add(m.group(1))

def update(path, column):
    p = repo / path; lines = p.read_text(encoding="utf-8").split("\n"); changed = 0
    for i, line in enumerate(lines):
        m = re.match(r"^\| (D-\d{3}) \|", line)
        if not m or m.group(1) not in cites: continue
        cells = line.split(" | ")
        have = set(re.findall(r"[A-Z]{3}-\d+", cells[column]))
        missing = sorted(cites[m.group(1)] - have, key=key)
        if not missing: continue
        end = " |" if cells[column].endswith(" |") else ""
        text = cells[column][: len(cells[column]) - len(end)].strip()
        if text in ("", "—", "pending"): text = ", ".join(missing)
        else: text = text + ", " + ", ".join(missing)
        cells[column] = text + end
        lines[i] = " | ".join(cells); changed += 1
    p.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(path, "rows changed:", changed)

update("spec/annex-D-traceability.md", 3)        # | D-ID | Topic | Owning SP | Rule IDs | ...
update("plans_and_notes/decision-register.md", 8) # ... | Linked OI | Implemented by |
