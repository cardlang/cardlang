"""Consistency checks for the CardLang Base Profile (platform/), WP2.

  rules      every BP-n rule is defined once, numbered from 1 without gaps
  errors     the CardError table has unique nonzero u16 codes; BP-8's precedence names only table members
  types      platform/base-types.card compiles under the full checker; the profile's type table lists exactly its names
  catalog    every block of platform/base-catalog.txt has every field, in order, with valid values: a known family,
             known types, a valid transaction behaviour, and CardError members from the table, in precedence order

Usage: uv run python -I tests/profilecheck.py .
"""
import re, sys, pathlib
from cardlang.front import pltcheck
from cardlang import layout
from cardlang.front.lexcheck import lex

FIELDS = ["params", "payload", "transaction", "errors", "resources", "on-failure", "permission", "summary"]
PRIMITIVE = {"u8", "u16", "u32", "i8", "i16", "i32", "bool"}

def main(repo):
    sys.stdout.reconfigure(encoding="utf-8")
    prof = (layout.at(repo).base_profile).read_text(encoding="utf-8")
    results = []
    def report(name, problems):
        results.append(not problems)
        print(("PASS " if not problems else "FAIL ") + name + (" | " + "; ".join(problems) if problems else ""))

    # rules
    ids = [int(n) for n in re.findall(r"^\*\*BP-(\d+)\b", prof, re.M)]
    problems = [] if ids == list(range(1, len(ids) + 1)) else [f"BP rules not numbered 1..n: {ids}"]
    report(f"rules ({len(ids)} BP rules)", problems)

    # errors
    table = re.findall(r"^\| `(\w+)` \| `0x([0-9A-Fa-f]{4})` \|", prof, re.M)
    members = [m for m, _ in table]; codes = [int(c, 16) for _, c in table]
    problems = []
    if len(set(members)) != len(members): problems.append("duplicate member")
    if len(set(codes)) != len(codes) or any(c == 0 for c in codes): problems.append("codes must be unique and nonzero")
    m = re.search(r"\*\*BP-8 Error precedence\.\*\*.*?order: (.*?)\. Each", prof, re.S)
    precedence = re.findall(r"`(\w+)`", m.group(1)) if m else []
    if not precedence: problems.append("BP-8 precedence not found")
    problems += [f"precedence names unknown member {x}" for x in precedence if x not in members]
    report(f"errors ({len(members)} members)", problems)

    # types
    problems = []
    try:
        pltcheck.run([], "fragment")
    except Exception as e:
        problems.append(f"base-types.card does not compile: {e}")
    listed = set(re.findall(r"^\| `(\w+)` \| ", prof.split("## 3. Types")[1].split("## 4.")[0], re.M))
    if listed != pltcheck.PRELUDE_NAMES:
        problems.append(f"type table {sorted(listed)} differs from base-types.card {sorted(pltcheck.PRELUDE_NAMES)}")
    report(f"types ({len(pltcheck.PRELUDE_NAMES)} declared)", problems)

    # catalog
    families = set(re.findall(r"^\| `(card\.\w+)`(?:, `(card\.\w+)`)? \|", prof, re.M))
    families = {f for pair in families for f in pair if f}
    _, blocks = pltcheck.load_block_catalog()
    problems = []
    def type_ok(ty):
        ty = ty.strip()
        for m in ("ref ", "inout "):
            if ty.startswith(m): ty = ty[len(m):]
        base = re.sub(r"\[\d*\]$", "", ty)
        return base in PRIMITIVE or base in pltcheck.PRELUDE_NAMES
    for b in blocks:
        where = f"{b['api']} (line {b['line']})"
        if ".".join(b["api"].split(".")[:2]) not in families: problems.append(f"{where}: unknown family")
        keys = [k for k, _ in b["fields"]]
        if keys != FIELDS: problems.append(f"{where}: fields {keys}, expected {FIELDS}")
        f = dict(b["fields"])
        if f.get("transaction") not in ("participates", "immediate", "forbidden"): problems.append(f"{where}: bad transaction value")
        errs = [] if f.get("errors", "-") == "-" else [x.strip() for x in f["errors"].split(",")]
        problems += [f"{where}: unknown error {x}" for x in errs if x not in members]
        known = [x for x in errs if x in precedence]
        if known != sorted(known, key=precedence.index): problems.append(f"{where}: errors not in BP-8 order")
        for item in ([] if f.get("params", "-") == "-" else f["params"].split(",")):
            if ":" not in item or not type_ok(item.split(":", 1)[1]): problems.append(f"{where}: bad parameter '{item.strip()}'")
        if f.get("payload", "-") != "-" and not type_ok(f["payload"]): problems.append(f"{where}: bad payload type")
        if not f.get("summary"): problems.append(f"{where}: empty summary")
    report(f"catalog ({len(blocks)} entries)", problems)

    print("ALL PASS" if all(results) else "FAILURES")

if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]).resolve())
