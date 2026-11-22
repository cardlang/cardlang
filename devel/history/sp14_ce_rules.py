"""One-off (SP14): complete the 'Rules' column of every chapter's compile-error table.

The column lists every rule whose text, up to its Sources line, raises the class (written **CE-...**), plus the rules listed before.
"""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "checkers"))   # find layout
import layout
repo = pathlib.Path(sys.argv[1]); spec = layout.at(repo).spec
ORDER = "LEX NAM TYP CEX EXP STM FUN OUT STA TXN HEP RTF PLT".split()

def key(r):
    p, n = r.split("-"); return (ORDER.index(p), int(n))

def expand(s):
    out = set()
    for a, b, c in re.findall(r"([A-Z]{3})-(\d+)(?:[–-](?:[A-Z]{3}-)?(\d+))?", s):
        out |= {f"{a}-{i}" for i in range(int(b), int(c or b) + 1)}
    return out

def compress(rules):
    rules = sorted(rules, key=key); out = []; i = 0
    while i < len(rules):
        j = i
        while j + 1 < len(rules) and key(rules[j + 1]) == (key(rules[j])[0], key(rules[j])[1] + 1): j += 1
        if j - i >= 2: out.append(f"{rules[i]}–{rules[j]}")
        else: out.extend(rules[i:j + 1])
        i = j + 1
    return ", ".join(out)

users = {}
for f in sorted(spec.glob("*.md")):
    t = f.read_text(encoding="utf-8")
    for m in re.finditer(r"^\*\*([A-Z]{3}-\d+) \[\w+\]\*\* (.*?)(?=^\*\*[A-Z]{3}-\d+ |^## |\Z)", t, re.M | re.S):
        for ce in set(re.findall(r"\*\*(CE-[A-Z]+-\d+)\*\*", m.group(2).split("*Sources:")[0])):
            users.setdefault(ce, set()).add(m.group(1))

changed = 0
for f in sorted(spec.glob("[01][0-9]-*.md")):
    t = f.read_text(encoding="utf-8")
    def fix(m):
        global changed
        new = compress(expand(m.group(3)) | users.get(m.group(1), set()))
        if new != m.group(3).strip(): changed += 1
        return f"{m.group(2)}{new} |"
    t2 = re.sub(r"^(?=\| \*\*(CE-[A-Z]+-\d+)\*\* \|)((?:[^|\n]*\|){3} )([^|\n]*) \|[ \t]*$", fix, t, flags=re.M)
    if t2 != t: f.write_text(t2, encoding="utf-8", newline="\n")
print("rows changed:", changed)
