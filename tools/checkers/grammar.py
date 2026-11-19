"""Mechanical check of the Annex A syntactic grammar (SP14).

Reads the EBNF productions of Annex A §A.2 directly from spec/annex-A-grammar.md, converts them to BNF,
and runs an Earley recognizer over the tokens of every conformance test file:

  * every valid test, runtime program and fragment must derive SourceFile (each file on its own, NAM-2);
  * every test expecting CE-SYN-1 must not derive;
  * every other invalid test (except lexical ones) must still derive: the grammar is deliberately
    permissive, and those errors come from chapter rules.

Usage: python -I tools/checkers/grammar.py . ["<glob>"]
"""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header, LexError

ROOT = pathlib.Path(__file__).resolve().parents[2]

# ------------------------------------------------------------------ EBNF -> BNF
def load_productions(annex_text):
    syntactic = annex_text[annex_text.index("## A.2 Syntactic grammar"):]
    text = "\n".join(re.findall(r"```\n(.*?)```", syntactic, re.S))
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    prods, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Z][A-Za-z]*)\s*::=(.*)$", line)
        if m:
            cur = m.group(1)
            assert cur not in prods, f"nonterminal defined twice: {cur}"
            prods[cur] = m.group(2)
        elif cur and line.strip():
            prods[cur] += " " + line.strip()
    prods["BooleanLiteral"] = "'true' | 'false'"          # A.1.5, a keyword-level production
    return prods

def tokenize_ebnf(body):
    return re.findall(r"'[^']*'|[A-Za-z][A-Za-z]*|[()|?*+]", body)

class Grammar:
    def __init__(self, prods):
        self.rules = {}; self.fresh = 0
        for name, body in prods.items():
            self.rules[name] = self.alternatives(tokenize_ebnf(body))
        undefined = {s[1] for alts in self.rules.values() for alt in alts for s in alt
                     if s[0] == "n" and s[1] not in self.rules}
        assert not undefined, f"undefined nonterminals: {undefined}"
        self.nullable = self.compute_nullable()

    def new(self, alts):
        self.fresh += 1; name = f"_g{self.fresh}"; self.rules[name] = alts; return ("n", name)

    def alternatives(self, toks):
        alts, cur, i = [], [], 0
        while i < len(toks):
            t = toks[i]
            if t == "|":
                alts.append(cur); cur = []; i += 1; continue
            if t == "(":
                depth, j = 1, i + 1
                while depth:
                    depth += {"(": 1, ")": -1}.get(toks[j], 0); j += 1
                sym = self.new(self.alternatives(toks[i + 1:j - 1])); i = j
            else:
                if t.startswith("'"): sym = ("t", t[1:-1])
                elif t in ("Identifier", "IntegerLiteral", "ByteStringLiteral"): sym = ("k", t)
                else: sym = ("n", t)
                i += 1
            if i < len(toks) and toks[i] in "?*+":
                op = toks[i]; i += 1
                if op == "?": sym = self.new([[sym], []])
                elif op == "*":
                    n = self.new([]); self.rules[n[1]] = [[], [n, sym]]; sym = n
                else:
                    n = self.new([]); self.rules[n[1]] = [[sym], [n, sym]]; sym = n
            cur.append(sym)
        alts.append(cur)
        return alts

    def compute_nullable(self):
        nullable, changed = set(), True
        while changed:
            changed = False
            for name, alts in self.rules.items():
                if name not in nullable and any(all(s[0] == "n" and s[1] in nullable for s in alt) for alt in alts):
                    nullable.add(name); changed = True
        return nullable

    # -------------------------------------------------------------- Earley recognizer
    def matches(self, sym, tok):
        kind, value = tok
        if sym[0] == "t": return value == sym[1]
        if sym[1] == "Identifier": return kind == "id"
        if sym[1] == "IntegerLiteral": return kind == "int"
        if sym[1] == "ByteStringLiteral": return kind == "bytes"
        return False

    def recognize(self, toks, start="SourceFile"):
        n = len(toks)
        sets = [dict() for _ in range(n + 1)]       # item -> None; item = (lhs, alt_index, dot, origin)
        def add(i, item, work):
            if item not in sets[i]:
                sets[i][item] = None; work.append(item)
        work = []
        for k in range(len(self.rules[start])): add(0, (start, k, 0, 0), work)
        for i in range(n + 1):
            work = list(sets[i].keys())
            while work:
                lhs, k, dot, origin = item = work.pop()
                alt = self.rules[lhs][k]
                if dot < len(alt):
                    sym = alt[dot]
                    if sym[0] == "n":
                        for kk in range(len(self.rules[sym[1]])): add(i, (sym[1], kk, 0, i), work)
                        if sym[1] in self.nullable: add(i, (lhs, k, dot + 1, origin), work)
                    elif i < n and self.matches(sym, toks[i]):
                        sets[i + 1][(lhs, k, dot + 1, origin)] = None
                else:
                    for (l2, k2, d2, o2) in list(sets[origin].keys()):
                        a2 = self.rules[l2][k2]
                        if d2 < len(a2) and a2[d2] == ("n", lhs): add(i, (l2, k2, d2 + 1, o2), work)
            if i < n and not sets[i + 1]:
                return False, i                       # no item can consume token i
        ok = any(l == start and d == len(self.rules[l][k]) and o == 0 for (l, k, d, o) in sets[n])
        return ok, n

def load_grammar(repo=ROOT):
    return Grammar(load_productions((repo / "spec" / "annex-A-grammar.md").read_text(encoding="utf-8")))

def test_files(t):
    if not t.is_dir(): return [t]
    if (t / "files.txt").exists(): return [t / f for f in (t / "files.txt").read_text().split()]
    return sorted(t.glob("*.card"))

def check_notes(repo, g):
    """Every design-note code block that the full checker accepts as a fragment must derive SourceFile."""
    import pltcheck
    text = (repo / "plans_and_notes" / "card-language-design-notes.md").read_text(encoding="utf-8")
    ok = True
    for n, block in enumerate(re.findall(r"```[a-z]*\n(.*?)```", text, re.S), 1):
        try:
            toks = lex(block.encode())
            pltcheck.run(toks)
        except Exception:
            continue                                  # a fragment, pseudo-code or an invalid example
        derived, _ = g.recognize(toks)
        st = "PASS" if derived else "FAIL"; ok &= derived
        print(st, f"design-notes block {n}", "| accepted by checker | grammar", "derives" if derived else "no derivation")
    return ok

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); glob = sys.argv[2] if len(sys.argv) > 2 else "*/*"
    g = load_grammar(repo); ok = True
    if glob == "--notes":
        print("ALL PASS" if check_notes(repo, g) else "FAILURES"); sys.exit(0)
    for t in sorted((repo / "conformance").glob(glob)):
        if t.suffix not in (".card", "") or t.name == "platform": continue
        files = test_files(t)
        if not files: continue
        exp = header(files[0].read_bytes()).get("expect", "")
        if "CE-LEX" in exp: continue                 # cannot be tokenized; covered by lexcheck
        want = "no derivation" if exp == "compile-error CE-SYN-1" else "derives"
        got = "derives"
        for f in files:
            derived, at = g.recognize(lex(f.read_bytes()))
            if not derived: got = "no derivation"; break
        st = "PASS" if got == want else "FAIL"; ok &= st == "PASS"
        print(st, t.relative_to(repo / "conformance"), "| expect", want, "| grammar", got)
    print("ALL PASS" if ok else "FAILURES")
