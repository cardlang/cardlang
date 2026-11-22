"""Scripted consistency checks over the specification text.

Each check prints PASS or FAIL with a short reason:

  rules        every rule is defined once, has exactly one status tag and a Sources line
  references   every rule, decision, open-issue, compile-error and trap ID that is referenced is defined
  ce-classes   every compile-error class is defined once in its chapter, indexed in 00-index,
               expected by at least one conformance test, and its table lists every rule that raises it
  traps        every trap kind in the 00-index catalog is defined in chapter 13
  tables       every Markdown table row has as many cells as its header
  fragments    every grammar production in a chapter equals the Annex A production of the same name
  checklist    every "platform-defined" sentence in chapters 1-13 and Annex B has a row in the B.12 checklist
  reverse      every decision a rule cites lists that rule in Annex D §D.2 and the register
  coverage     every rule has a row in the Annex D §D.3 coverage matrix
  index        the rule status summary in 00-index matches the rules actually defined

Usage: uv run python -I tests/speccheck.py .
"""
import re, sys, pathlib
from cardlang import layout

PREFIXES = "LEX|NAM|TYP|CEX|EXP|STM|FUN|OUT|STA|TXN|HEP|RTF|PLT"
RULE_DEF = re.compile(rf"^\*\*((?:{PREFIXES})-\d+) \[(Agreed|Proposal|Open)\]\*\*", re.M)

def expand_rules(s):
    out = set()
    for a, b, c in re.findall(r"([A-Z]{3})-(\d+)(?:[–-](?:[A-Z]{3}-)?(\d+))?", s):
        out |= {f"{a}-{i}" for i in range(int(b), int(c or b) + 1)}
    return out

def strip_code(line):
    return re.sub(r"`[^`]*`", "``", line)

def main(repo):
    spec = layout.at(repo).spec
    files = sorted(spec.glob("*.md"))
    texts = {f.name: f.read_text(encoding="utf-8") for f in files}
    chapters = {n: t for n, t in texts.items() if re.match(r"\d\d-", n) and n != "00-index.md"}
    normative = dict(chapters); normative["annex-B-platform-contract.md"] = texts["annex-B-platform-contract.md"]
    tests = sorted((layout.at(repo).conformance).rglob("*.card"))
    headers = [f.read_text(encoding="utf-8", errors="replace").split("\n\n")[0] for f in tests]
    results = []
    def report(name, problems):
        results.append(not problems)
        print(("PASS " if not problems else "FAIL ") + name + (" | " + "; ".join(problems[:8]) if problems else ""))
        for p in problems[8:]: print("       " + p)

    # rules -----------------------------------------------------------------------------------
    rules, problems = {}, []
    for name, text in normative.items():
        for m in RULE_DEF.finditer(text):
            rid = m.group(1)
            if rid in rules: problems.append(f"{rid} defined twice")
            rules[rid] = (name, m.group(2))
            rest = text[m.end():]
            nxt = re.search(rf"^\*\*(?:{PREFIXES})-\d+ \[|^#", rest, re.M)
            body = rest[: nxt.start() if nxt else len(rest)]
            if "*Sources:" not in body: problems.append(f"{rid} has no Sources line")
            if re.search(r"\[(Agreed|Proposal|Open)\]", body.split("*Sources:")[0]):
                problems.append(f"{rid} has a second status tag")
        for m in re.finditer(rf"^\*\*((?:{PREFIXES})-\d+)\b(?! \[(?:Agreed|Proposal|Open)\]\*\*)", text, re.M):
            problems.append(f"{m.group(1)} has no status tag")
    report(f"rules ({len(rules)} defined)", problems)

    # references ------------------------------------------------------------------------------
    register = (layout.at(repo).decision_register).read_text(encoding="utf-8")
    decisions = set(re.findall(r"^\| (D-\d+) \|", register, re.M))
    issues = set(re.findall(r"^## (OI-\d+) ", texts["annex-C-open-issues.md"], re.M))
    index = texts["00-index.md"]
    ce_indexed = re.findall(r"^\| (CE-[A-Z]+-\d+) \|", index, re.M)
    traps = set(re.findall(r"^\| (TRAP-[A-Z]+(?:-[A-Z]+)*) \|", index, re.M))
    problems = []
    corpus = list(texts.items()) + [(str(f.relative_to(repo)), h) for f, h in zip(tests, headers)]
    for name, text in corpus:
        for rid in set(re.findall(rf"\b((?:{PREFIXES})-\d+)\b", text)):
            if rid not in rules: problems.append(f"{name}: rule {rid} undefined")
        for did in set(re.findall(r"\b(D-\d{3})\b", text)):
            if did not in decisions: problems.append(f"{name}: decision {did} undefined")
        for oi in set(re.findall(r"\b(OI-\d+)\b", text)):
            if oi not in issues: problems.append(f"{name}: issue {oi} undefined")
        for ce in set(re.findall(r"\b(CE-[A-Z]+-\d+)\b", text)):
            if ce not in ce_indexed: problems.append(f"{name}: compile-error class {ce} undefined")
        for tk in set(re.findall(r"\b(TRAP-[A-Z]+(?:-[A-Z]+)*)\b", text)) - {"TRAP-KIND"}:
            if tk not in traps: problems.append(f"{name}: trap {tk} undefined")
    report(f"references ({len(decisions)} decisions, {len(issues)} issues)", problems)

    # compile-error classes -------------------------------------------------------------------
    problems = []
    defined = {}
    for name, text in list(chapters.items()) + [("annex-A-grammar.md", texts["annex-A-grammar.md"])]:
        for ce in re.findall(r"^\| \*\*(CE-[A-Z]+-\d+)\*\* \|", text, re.M):
            if ce in defined: problems.append(f"{ce} defined in {defined[ce]} and {name}")
            defined[ce] = name
    if "CE-SYN-1" not in defined and "CE-SYN-1" in texts["annex-A-grammar.md"]: defined["CE-SYN-1"] = "annex-A-grammar.md"
    for ce in ce_indexed:
        if ce not in defined: problems.append(f"{ce} indexed but not defined in a chapter table")
    if len(set(ce_indexed)) != len(ce_indexed): problems.append("00-index lists a class twice")
    for ce in defined:
        if ce not in ce_indexed: problems.append(f"{ce} not in the 00-index")
    expected = set(re.findall(r"expect: compile-error (CE-[A-Z]+-\d+)", "\n".join(headers)))
    for ce in defined:
        if ce not in expected: problems.append(f"{ce} expected by no conformance test")
    listed = {}
    for text in chapters.values():
        for m in re.finditer(r"^\| \*\*(CE-[A-Z]+-\d+)\*\* \|.*\| ([^|]*) \|[ \t]*$", text, re.M):
            listed[m.group(1)] = expand_rules(m.group(2))
    for name, text in normative.items():
        for m in re.finditer(rf"^\*\*((?:{PREFIXES})-\d+) \[\w+\]\*\* (.*?)(?=^\*\*(?:{PREFIXES})-\d+ |^## |\Z)", text, re.M | re.S):
            for ce in set(re.findall(r"\*\*(CE-[A-Z]+-\d+)\*\*", m.group(2).split("*Sources:")[0])):
                if ce in listed and m.group(1) not in listed[ce]:
                    problems.append(f"{m.group(1)} raises {ce} but its table does not list it")
    report(f"ce-classes ({len(defined)} classes)", problems)

    # traps -----------------------------------------------------------------------------------
    problems = [f"{t} not defined in chapter 13" for t in sorted(traps)
                if not re.search(rf"^\| `{t[5:]}` \|", texts["13-runtime-failures.md"], re.M)]
    report(f"traps ({len(traps)} kinds)", problems)

    # tables ----------------------------------------------------------------------------------
    problems = []
    for name, text in list(texts.items()) + [(p.name, p.read_text(encoding="utf-8")) for p in
                                             [layout.at(repo).decision_register]]:
        in_code, width = False, None
        for n, line in enumerate(text.splitlines(), 1):
            if line.startswith("```"): in_code = not in_code
            if in_code or not line.startswith("|"):
                width = None; continue
            cells = strip_code(line).replace("\\|", "").count("|") - 1
            if width is None: width = cells
            elif cells != width: problems.append(f"{name}:{n} has {cells} cells, header {width}")
    report("tables", problems)

    # grammar fragments -----------------------------------------------------------------------
    def productions(text):
        out = {}
        for block in re.findall(r"```(?:text)?\n(.*?)```", text, re.S):
            if "::=" not in block: continue
            block = re.sub(r"/\*.*?\*/", " ", block, flags=re.S)
            cur = None
            for line in block.splitlines():
                m = re.match(r"^\s*([A-Z][A-Za-z]*)\s*::=(.*)$", line)
                if m: cur = m.group(1); out[cur] = m.group(2)
                elif cur and line.strip(): out[cur] += " " + line
        return {k: " ".join(v.split()) for k, v in out.items()}
    def alternatives(body):
        alts, cur, depth = [], "", 0
        for ch in re.findall(r"'[^']*'|.", body):
            depth += {"(": 1, ")": -1}.get(ch, 0)
            if ch == "|" and depth == 0: alts.append(cur.strip()); cur = ""
            else: cur += ch
        return [" ".join(a.split()) for a in alts + [cur]]
    annex = productions(texts["annex-A-grammar.md"]); problems = []; compared = 0
    for name, text in chapters.items():
        for nt, body in productions(text).items():
            compared += 1
            if nt not in annex: problems.append(f"{name}: {nt} not in Annex A")
            elif "…" in body:                       # an excerpt: the alternatives shown must exist in Annex A
                shown = [a for a in alternatives(body) if a != "…"]
                if not set(shown) <= set(alternatives(annex[nt])): problems.append(f"{name}: excerpt of {nt} differs from Annex A")
            elif annex[nt] != body: problems.append(f"{name}: {nt} differs from Annex A")
    report(f"fragments ({compared} chapter productions, {len(annex)} in Annex A)", problems)

    # B.12 checklist --------------------------------------------------------------------------
    annex_b = texts["annex-B-platform-contract.md"]
    listed = re.findall(r"^\| \d+ \| \[((?:%s)-\d+)\]" % PREFIXES, annex_b.split("## B.12")[1], re.M)
    wanted = []
    for name, text in normative.items():
        for m in re.finditer(rf"^\*\*((?:{PREFIXES})-\d+) \[Agreed\]\*\* (.*?)(?=^\*\*(?:{PREFIXES})-\d+ |\Z|^## )", text, re.M | re.S):
            body = m.group(2).split("*Sources:")[0]
            for sentence in re.split(r"(?<=[.)])\s+(?=[A-Z])", re.sub(r"\s+", " ", body)):
                if "platform-defined" in sentence.lower(): wanted.append(m.group(1))
    problems = []
    if sorted(wanted) != sorted(listed):
        missing = sorted(set(wanted) - set(listed)); extra = sorted(set(listed) - set(wanted))
        problems.append(f"checklist out of date: {len(wanted)} references, {len(listed)} rows; missing {missing}, extra {extra}")
    report(f"checklist ({len(listed)} rows)", problems)

    # reverse traceability --------------------------------------------------------------------
    problems = []
    d2 = texts["annex-D-traceability.md"].split("## D.2")[1].split("## D.3")[0]
    d2_rules = {m.group(1): set(re.findall(r"[A-Z]{3}-\d+", m.group(2)))
                for m in re.finditer(r"^\| (D-\d{3}) \|(?:[^|]*\|){1}([^|]*)\|", d2, re.M)}   # ID, topic, rule IDs
    reg_rules = {m.group(1): set(re.findall(r"[A-Z]{3}-\d+", m.group(2)))
                 for m in re.finditer(r"^\| (D-\d{3}) \|.*\| ([^|]*) \|[ \t]*$", register, re.M)}
    for name, text in normative.items():
        for m in re.finditer(rf"^\*\*((?:{PREFIXES})-\d+) \[\w+\]\*\*.*?^\*Sources: (.*?)$", text, re.M | re.S):
            for d in set(re.findall(r"D-\d{3}", m.group(2))):
                if m.group(1) not in d2_rules.get(d, set()): problems.append(f"{m.group(1)} cites {d}, but D.2 does not list it")
                if m.group(1) not in reg_rules.get(d, set()): problems.append(f"{m.group(1)} cites {d}, but the register does not list it")
    missing = sorted(decisions - set(d2_rules))
    if missing: problems.append(f"decisions without a D.2 row: {missing}")
    report(f"reverse ({len(d2_rules)} D.2 rows)", problems)

    # coverage matrix -------------------------------------------------------------------------
    d3 = texts["annex-D-traceability.md"].split("## D.3")[-1]
    covered = dict(re.findall(rf"^\| ((?:{PREFIXES})-\d+) \| (cited|exercised|not testable) \| \S", d3, re.M))
    problems = [f"{r} has no row in Annex D §D.3" for r in rules if r not in covered]
    problems += [f"D.3 lists unknown rule {r}" for r in covered if r not in rules]
    report(f"coverage ({len(covered)} rules in D.3)", problems)

    # index rule counts -----------------------------------------------------------------------
    problems = []
    m = re.search(r"^\| \*\*Total\*\* \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|", index, re.M)
    counts = [sum(1 for r in rules.values() if r[1] == s) for s in ("Agreed", "Proposal", "Open")]
    if not m or [int(x) for x in m.groups()] != [len(rules)] + counts:
        problems.append(f"00-index total row does not match {len(rules)} rules {counts}")
    report("index", problems)

    print("ALL PASS" if all(results) else "FAILURES")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(pathlib.Path(sys.argv[1]).resolve())
