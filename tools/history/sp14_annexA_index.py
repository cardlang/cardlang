"""One-off (SP14): append Annex A §A.3, the nonterminal index and the note on the mechanical grammar check."""
import re, sys, pathlib
p = pathlib.Path(sys.argv[1]) / "spec" / "annex-A-grammar.md"; t = p.read_text(encoding="utf-8")
t = t.split("\n## A.3 ")[0].rstrip("\n") + "\n"
index, section = [], None
for line in t.splitlines():
    m = re.match(r"^### (A\.2\.\d+) ", line) or re.match(r"^/\* (A\.1\.\d+) ", line)
    if m: section = m.group(1)
    m = re.match(r"^\s*([A-Z][A-Za-z]*)\s*::=", line)
    if m and section: index.append((m.group(1), section))
index.append(("BooleanLiteral", "A.1.5")) if not any(n == "BooleanLiteral" for n, _ in index) else None
index.sort(key=lambda x: x[0].lower())
rows = "\n".join(f"| `{n}` | §{s} |" for n, s in index)
t += f"""
## A.3 Nonterminal index and mechanical check

### A.3.1 Index

Every nonterminal of this annex, with the section that defines it. Each is defined exactly once.

| Nonterminal | Defined in |
|---|---|
{rows}

### A.3.2 Mechanical check

The grammar in §A.2 is checked by `tools/checkers/grammar.py`, which reads the productions directly from this annex, converts them to BNF and runs an Earley recognizer over the tokens of each source file. `tools/run_checks.py` runs it, and it requires:

- every valid test, every runtime program and every other test file, except those expecting a lexical error, to derive `SourceFile`, file by file;
- every test that expects **CE-SYN-1** not to derive;
- every code block in the design notes that the reference checker accepts to derive `SourceFile`.

The check found one inconsistency, OI-44: EXP-6 excluded an unparenthesized constructor from condition positions, but the general `Expression` in those positions allowed one. `ConditionExpression` (§A.2.4) now encodes the rule (D-444). The other invalid tests derive, as intended: the grammar is deliberately permissive, and their errors come from chapter rules (§A.0).
"""
p.write_text(t, encoding="utf-8", newline="\n")
print("nonterminals:", len(index))
