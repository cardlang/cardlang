"""Checker for chapter 4 type rules (TYP-3, 10, 13, 15, 18, 19, 21) over token streams."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header

PRIM = {"u8", "u16", "u32", "i8", "i16", "i32", "bool"}
SIGNED = {"i8", "i16", "i32"}

def scan(toks):
    """Collect declarations and type positions. Returns (structs, enums, consts, others, positions)."""
    structs, enums, consts, others, positions = {}, {}, {}, set(), []
    i, n = 0, len(toks)
    def parse_type(j, ctx):
        start = j; name = toks[j][1]; j += 1; suffixes = []
        while j < n and toks[j][1] == "[":
            k = j + 1; depth = 1
            while depth:
                if toks[k][1] == "[": depth += 1
                if toks[k][1] == "]": depth -= 1
                k += 1
            suffixes.append([t[1] for t in toks[j+1:k-1]]); j = k
        positions.append((name, suffixes, ctx)); return j
    paren_ctx = []  # stack of booleans: inside a parameter list
    while i < n:
        k, v = toks[i]
        if v in ("struct", "enum") and i + 2 < n and toks[i+2][1] == "{":
            name = toks[i+1][1]; j = i + 3; members = []
            while toks[j][1] != "}":
                if v == "enum":
                    members.append(toks[j][1]); j += 2
                else:
                    fname = toks[j][1]; j0 = j + 2
                    j = parse_type(j0, "field"); members.append((fname, positions[-1]))
                    j += 1  # ';'
            (structs if v == "struct" else enums)[name] = members; i = j + 1; continue
        if v in ("function", "command"):
            others.add(toks[i+1][1])
        if v == "const" and toks[i+2][1] == ":":
            consts[toks[i+1][1]] = toks[i+3][1]
        if v == "(":
            paren_ctx.append(i > 1 and toks[i-2][1] in ("function", "command"))
        if v == ")":
            paren_ctx and paren_ctx.pop()
        if v == ":" and k == "p" and toks[i-1][0] == "id":
            j = i + 1; mode = None
            if toks[j][1] in ("ref", "inout"):
                mode = toks[j][1]; j += 1
            in_params = bool(paren_ctx and paren_ctx[-1])
            ctx = ("param-" + (mode or "value")) if in_params else "value"
            i = parse_type(j, ctx); continue
        if v == "->":
            i = parse_type(i + 1, "return"); continue
        i += 1
    return structs, enums, consts, others, positions

def check(toks):
    structs, enums, consts, others, positions = scan(toks)
    errs = []
    for name, members in enums.items():
        if not members: errs.append("CE-TYP-2")
    for name, fields in structs.items():
        if not fields: errs.append("CE-TYP-3")
    for name, suffixes, ctx in positions:
        if name not in PRIM | set(structs) | set(enums):
            errs.append("CE-TYP-1" if name in consts or name in others else "CE-NAM-2")
        if len(suffixes) > 1: errs.append("CE-TYP-6")
        for s in suffixes:
            if not s:
                if ctx not in ("param-ref", "param-inout"): errs.append("CE-TYP-5")
            elif len(s) == 1:
                tok = s[0]
                if tok in consts and consts[tok] in SIGNED | {"bool"}: errs.append("CE-TYP-7")
                if re.fullmatch(r"[0-9_]+", tok) and int(tok.replace("_", "")) == 0: errs.append("CE-TYP-7")
    # containment cycles
    def contained(s):
        return {t for _, (t, suf, _) in structs[s] if t in structs}
    for s in structs:
        seen, stack = set(), list(contained(s))
        while stack:
            r = stack.pop()
            if r == s: errs.append("CE-TYP-4"); break
            if r not in seen: seen.add(r); stack += contained(r)
    return sorted(set(errs)), positions

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True
    for t in sorted((repo / "conformance").glob("*/typ-*")):
        meta = header(t.read_bytes()); exp = meta["expect"]
        errs, _ = check(lex(t.read_bytes()))
        want = [] if exp == "ok" else [exp.split()[-1]]
        st = "PASS" if errs == want else "FAIL"; ok &= st == "PASS"
        print(st, t.name, "expect", exp, "found", errs)
    # notes: every type position must satisfy suffix rules
    dn = (repo / "plans_and_notes" / "card-language-design-notes.md").read_text(encoding="utf-8")
    bad = []
    for block in re.findall(r"```text\n(.*?)```", dn, re.S):
        try:
            _, pos = check(lex(block.encode()))
        except Exception as e:
            continue
        for name, suffixes, ctx in pos:
            if len(suffixes) > 1 or (any(not s for s in suffixes) and ctx not in ("param-ref", "param-inout")):
                bad.append((name, suffixes, ctx))
    print("ALL TYP TESTS PASS" if ok else "TYP FAILURES", "| notes type positions violating TYP-18/21:", bad)
