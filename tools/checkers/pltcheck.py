"""Reference checker for the platform-catalog rules (NAM-18, EXP-47 for platform calls, TXN-17), built on hepcheck.

Loads the test-only catalog conformance/platform/test-catalog.txt (Annex B, PLT-26; non-normative).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header
import project
import srcpos
import hepcheck, expcheck, consteval
from expcheck import CE

ROOT = pathlib.Path(__file__).resolve().parents[2]
CATALOG_FILE = ROOT / "conformance" / "platform" / "test-catalog.txt"
BASE_CATALOG = ROOT / "platform" / "base-catalog.txt"            # Base Profile 1 (platform/base-profile.md)
BASE_TYPES = ROOT / "platform" / "base-types.card"
DECL_KEYWORDS = {"struct", "enum", "function", "persistent", "session", "const", "command", "errors"}

def declared_names(toks):
    """Names introduced by top-level-style declarations in a token list."""
    return {toks[i + 1][1] for i, (_, v) in enumerate(toks[:-1]) if v in DECL_KEYWORDS and toks[i + 1][0] == "id"}

PRELUDE = lex(BASE_TYPES.read_bytes()) if BASE_TYPES.exists() else []
PRELUDE_NAMES = declared_names(PRELUDE)

def parse_params(params):
    plist = []
    if params != "-":
        for item in params.split(","):
            name, rest = [x.strip() for x in item.split(":", 1)]
            mode = None
            for m in ("ref", "inout"):
                if rest.startswith(m + " "): mode, rest = m, rest[len(m) + 1:]
            plist.append((name, mode, parse_type(rest)))
    return plist

def load_block_catalog(path=BASE_CATALOG):
    """The Base Profile catalog: blocks of "api <path>" followed by indented "<field> <value>" lines."""
    blocks, cur = [], None
    if not path.exists(): return {}, blocks
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#")[0].rstrip()
        if not line.strip(): continue
        if not raw[0].isspace():
            key, _, value = line.partition(" ")
            assert key == "api", f"{path.name}:{n}: a block must start with 'api'"
            cur = {"api": value.strip(), "line": n, "fields": []}; blocks.append(cur)
        else:
            key, _, value = line.strip().partition(" ")
            cur["fields"].append((key, value.strip()))
    catalog = {}
    for b in blocks:
        f = dict(b["fields"])
        catalog[b["api"]] = {"params": parse_params(f.get("params", "-")),
                             "ret": "none" if f.get("payload", "-") == "-" else parse_type(f["payload"]),
                             "tx": f.get("transaction"), "errors": [] if f.get("errors", "-") == "-" else [x.strip() for x in f["errors"].split(",")]}
    return catalog, blocks

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
        catalog[entry_path] = {"params": parse_params(params), "ret": "none" if payload == "-" else parse_type(payload),
                               "tx": tx, "errors": [] if errors == "-" else [x.strip() for x in errors.split(",")]}
    catalog.update(load_block_catalog()[0])
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
        clash = declared_names(toks) & PRELUDE_NAMES                          # base types are predeclared (BP-11)
        if clash:
            srcpos.set_declarations(toks); raise srcpos.at(CE("CE-NAM-5"), srcpos.decl(sorted(clash)[0]))
        super().__init__(PRELUDE + toks)

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
                    raise srcpos.at(CE("CE-TXN-4"), body[i])

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

class ProfileError(Exception):
    """A build rejected by a Base Profile rule (not a language compile error), e.g. BP-52."""

def literal_value(text):
    text = text.replace("_", "")
    return int(text, 0) if text[:2].lower() in ("0x", "0b") else int(text, 10)

def error_codes(toks, with_tokens=False):
    """The codes of the application error set: errors Name { Member = literal; ... }; with their literal tokens."""
    codes = []
    for i, (_, v) in enumerate(toks):
        if v == "errors" and i + 2 < len(toks) and toks[i + 2][1] == "{":
            j = i + 3
            while j < len(toks) and toks[j][1] != "}":
                if toks[j][1] == "=" and toks[j + 1][0] == "int":
                    c = literal_value(toks[j + 1][1]); codes.append((c, toks[j + 1]) if with_tokens else c)
                j += 1
    return codes

ON_SELECT = ["(", "?", ":", "inout", "u8", "[", "]", ")", "->", "u32"]

def check_on_select(toks):
    """BP-50a: on_select(response: inout u8[]) -> u32, never called by application code."""
    for i, (kind, v) in enumerate(toks):
        if v != "on_select": continue
        if i > 0 and toks[i - 1][1] == "function":
            sig = [x for _, x in toks[i + 1:i + 1 + len(ON_SELECT)]]
            if [s if p != "?" else "?" for s, p in zip(sig, ON_SELECT)] != ON_SELECT or toks[i + 2][0] != "id":
                raise srcpos.at(ProfileError("BP-50a"), toks[i])
        elif i + 1 < len(toks) and toks[i + 1][1] == "(":
            raise srcpos.at(ProfileError("BP-50a"), toks[i])  # a call: lifecycle handlers are not callable

def check_binding(toks, binding):
    """BP-50a and BP-52 for the ISO 7816 binding: the on_select handler, and application error codes that are
    status words in 6200-6EFF or 9100-9FFF."""
    if binding == "iso7816":
        check_on_select(toks)
        for c, tok in error_codes(toks, True):
            if not (0x6200 <= c <= 0x6EFF or 0x9100 <= c <= 0x9FFF): raise srcpos.at(ProfileError("BP-52"), tok)
    elif binding not in (None, "raw"):
        raise ValueError("unknown binding " + binding)

def run(toks, kind="fragment", binding=None):
    check_binding(toks, binding)
    if kind == "fragment":
        toks = toks + lex(hepcheck.SCAFFOLD)
    PltChecker(toks).run()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/plt-*"
    for t in sorted((repo / "conformance").glob(glob)):
        files = project.program_files(t)
        toks = sum((lex(f.read_bytes()) for f in files), [])
        meta = header(files[0].read_bytes()); exp = meta["expect"]
        try:
            run(toks, meta.get("kind", "fragment"), meta.get("binding")); got = "ok"
        except (CE, consteval.CE) as e:
            got = "compile-error " + str(e)
        except ProfileError as e:
            got = "profile-error " + str(e)
        st = "PASS" if got == exp else "FAIL"; ok &= st == "PASS"
        print(st, t.name, "| expect", exp, "| checker", got)
    print("ALL PASS" if ok else "FAILURES")
