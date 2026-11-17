"""Reference checker for the platform-catalog rules (NAM-18, EXP-47 for platform calls, TXN-17), built on hepcheck.

Loads the test-only catalog conformance/platform/test-catalog.txt (Annex B, PLT-26; non-normative).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header
import hepcheck, expcheck, consteval
from expcheck import CE

CATALOG_FILE = pathlib.Path(__file__).resolve().parents[2] / "conformance" / "platform" / "test-catalog.txt"

def parse_type(text):
    text = text.strip()
    if text.endswith("[]"): return ("arr", text[:-2].strip(), None)
    return text

def load_catalog(path=CATALOG_FILE):
    catalog = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if not line: continue
        fields = [f.strip() for f in line.split("|")]
        entry_path, params, payload, tx, errors = fields
        plist = []
        if params != "-":
            for item in params.split(","):
                name, rest = [x.strip() for x in item.split(":", 1)]
                mode = None
                for m in ("ref", "inout"):
                    if rest.startswith(m + " "): mode, rest = m, rest[len(m) + 1:]
                plist.append((name, mode, parse_type(rest)))
        catalog[entry_path] = {"params": plist, "ret": "none" if payload == "-" else parse_type(payload),
                               "tx": tx, "errors": [] if errors == "-" else [x.strip() for x in errors.split(",")]}
    return catalog

def platform_path(node):
    """`card.a.b` written as nested field selections; None if the target is not a card path."""
    parts = []
    while node[0] == "field":
        parts.append(node[2]); node = node[1]
    if node[0] == "name" and node[1] == "card" and parts:
        return ".".join(["card"] + parts[::-1])
    return None

def token_paths(toks):
    """Platform paths called in a token list: card . id (. id)* ("""
    out = []
    for i, (_, v) in enumerate(toks):
        if v == "card" and i + 2 < len(toks) and toks[i+1][1] == "." and (i == 0 or toks[i-1][1] != "."):
            j = i; parts = ["card"]
            while j + 2 < len(toks) and toks[j+1][1] == ".":
                parts.append(toks[j+2][1]); j += 2
            if j + 1 < len(toks) and toks[j+1][1] == "(": out.append(".".join(parts))
    return out

class PltChecker(hepcheck.HepChecker):
    def __init__(self, toks, catalog=None):
        self.catalog = catalog if catalog is not None else load_catalog()
        super().__init__(toks)

    def run(self):
        self.check_forbidden_in_transactions()
        super().run()

    # TXN-17: structural rule over the static call graph, as for nesting (TXN-10)
    def check_forbidden_in_transactions(self):
        forbidden = {p for p, e in self.catalog.items() if e["tx"] == "forbidden"}
        memo = {}
        def reaches(f, seen=()):
            if f in memo: return memo[f]
            body = self.funcs[f][2]
            r = any(p in forbidden for p in token_paths(body)) or any(
                reaches(g, seen + (f,)) for g in self.calls_in(body) if g not in seen)
            memo[f] = r; return r
        for name, (_, _, body) in self.funcs.items():
            for i, (_, v) in enumerate(body):
                if v != "transaction": continue
                j = i + 1; depth = 0
                while True:
                    if body[j][1] == "{": depth += 1
                    if body[j][1] == "}":
                        depth -= 1
                        if depth == 0: break
                    j += 1
                inner = body[i + 2:j]
                if any(p in forbidden for p in token_paths(inner)) or any(reaches(g) for g in self.calls_in(inner)):
                    raise CE("CE-TXN-4")

    def call(self, e, L, T):
        path = platform_path(e[1])
        if path is None:
            return super().call(e, L, T)
        if path not in self.catalog: raise CE("CE-NAM-10")                    # NAM-18
        entry = self.catalog[path]
        self.funcs[path] = (entry["params"], entry["ret"], [])               # checked like a function call
        try:
            return super().call(("call", ("name", path), e[2], e[3]), L, T)
        finally:
            del self.funcs[path]

def run(toks, kind="fragment"):
    if kind == "fragment":
        toks = toks + lex(hepcheck.SCAFFOLD)
    PltChecker(toks).run()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/plt-*"
    for t in sorted((repo / "conformance").glob(glob)):
        files = [t / f for f in (t / "files.txt").read_text().split()] if t.is_dir() else [t]
        toks = sum((lex(f.read_bytes()) for f in files), [])
        meta = header(files[0].read_bytes()); exp = meta["expect"]
        try:
            run(toks, meta.get("kind", "fragment")); got = "ok"
        except (CE, consteval.CE) as e:
            got = "compile-error " + str(e)
        st = "PASS" if got == exp else "FAIL"; ok &= st == "PASS"
        print(st, t.name, "| expect", exp, "| checker", got)
    print("ALL PASS" if ok else "FAILURES")
