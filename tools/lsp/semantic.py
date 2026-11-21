"""Semantic tokens: each identifier coloured by what it is (TL1 step 3b).

classify(target, texts) returns, for one file of a program, a list of (line, column, length, type, modifiers),
0-based, in source order. It works from the tokens of every file of the program (texts: path -> text) and the Base
Profile's prelude, and needs no successful check: a program with errors is still coloured.

The kinds are VS Code's standard token types, so every colour theme colours them, plus one custom modifier,
`persistent`, for what lives in persistent storage:

| CardLang | Type | Modifiers |
|---|---|---|
| function, command, handler | function | declaration where declared |
| struct, its fields | struct, property | |
| enum or error set, its members | enum, enumMember | |
| parameter | parameter | readonly for `ref` |
| local (`var`, `for`, a match binding) | variable | |
| `const` | variable | readonly |
| `session` global | variable | static |
| `persistent` global | variable | persistent |
| primitive type, `.length` | type, property | defaultLibrary |
| intrinsic (`checked_add`, `fill`, ...) | macro | defaultLibrary |
| `card` and the path segments of a platform API | namespace, function | defaultLibrary |
| a Base Profile type or member (KeySpec, KeyType.Aes128) | struct, enum, enumMember | defaultLibrary |
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
for d in (HERE.parent / "checkers",):
    if str(d) not in sys.path: sys.path.insert(0, str(d))
from lexcheck import lex, LexError
import expcheck

TYPES = ["namespace", "type", "struct", "enum", "enumMember", "parameter", "variable", "property", "function", "macro"]
MODIFIERS = ["declaration", "readonly", "static", "defaultLibrary", "persistent"]
PRIMITIVES = {"u8", "u16", "u32", "i8", "i16", "i32", "bool"}
INTRINSICS = expcheck.CHECKED2 | expcheck.WRAP | expcheck.TYARG | {"checked_neg", "encode_be", "encode_le", "equal", "compare", "fill"}

class Symbols:
    """The program-level names: kind, modifiers, and which token declares each."""
    def __init__(self):
        self.kind = {}                 # name -> (type, set of modifiers)
        self.fields = set()            # every struct field name
        self.members = {}              # enum or error-set name -> its member names
        self.decl_tokens = set()       # id() of every declaring token

    def add(self, name, typ, mods=(), tok=None):
        if name not in self.kind: self.kind[name] = (typ, set(mods))
        if tok is not None: self.decl_tokens.add(id(tok))

def collect(toks, syms, library=False):
    """The top-level declarations of one file's tokens, into syms."""
    lib = {"defaultLibrary"} if library else set()
    i, n = 0, len(toks)
    while i < n:
        v = toks[i][1]
        if v in ("function", "command") and i + 1 < n and toks[i + 1][0] == "id":
            syms.add(toks[i + 1][1], "function", lib, toks[i + 1])
        elif v in ("struct", "enum", "errors") and i + 2 < n and toks[i + 1][0] == "id" and toks[i + 2][1] == "{":
            name = toks[i + 1][1]
            syms.add(name, "struct" if v == "struct" else "enum", lib, toks[i + 1])
            j = i + 3; members = set()
            while j < n and toks[j][1] != "}":
                if toks[j][0] == "id" and toks[j - 1][1] in ("{", ";", ","):
                    syms.decl_tokens.add(id(toks[j]))
                    if v == "struct": syms.fields.add(toks[j][1])
                    else: members.add(toks[j][1])
                j += 1
            if v != "struct": syms.members[name] = members
            i = j
        elif v in ("const", "persistent", "session") and i + 1 < n and toks[i + 1][0] == "id" and (i == 0 or toks[i - 1][1] in ("}", ";")):
            mods = {"const": {"readonly"}, "persistent": {"persistent"}, "session": {"static"}}[v] | lib
            syms.add(toks[i + 1][1], "variable", mods, toks[i + 1])
        i += 1

def functions(toks):
    """(params, body_start, body_end) for each function or command: params maps a name to its modifiers."""
    out, i, n = [], 0, len(toks)
    while i < n:
        if toks[i][1] in ("function", "command") and i + 2 < n and toks[i + 2][1] == "(":
            params, j, depth = {}, i + 3, 1
            while j < n and depth:
                v = toks[j][1]
                if v == "(": depth += 1
                elif v == ")": depth -= 1
                elif toks[j][0] == "id" and j + 1 < n and toks[j + 1][1] == ":" and toks[j - 1][1] in ("(", ","):
                    mode = toks[j + 2][1] if j + 2 < n else None
                    params[toks[j][1]] = ({"readonly"} if mode == "ref" else set(), toks[j])
                j += 1
            while j < n and toks[j][1] != "{": j += 1
            start, depth = j, 0
            while j < n:
                if toks[j][1] == "{": depth += 1
                elif toks[j][1] == "}":
                    depth -= 1
                    if depth == 0: break
                j += 1
            out.append((params, i + 3, start, j)); i = j
        i += 1
    return out

def locals_in(toks, start, end):
    """The local names declared in a body, and their declaring tokens: var x, for x, and match bindings."""
    names, decls = set(), set()
    for j in range(start, end):
        k, v = toks[j]
        if k != "id": continue
        prev = toks[j - 1][1]
        if prev in ("var", "for"): names.add(v); decls.add(id(toks[j]))
        elif (prev == "(" and j + 2 < end and toks[j + 1][1] == ")" and toks[j + 2][1] == "=>" and j >= 2
              and toks[j - 2][1] in ("Ok", "Err")):
            names.add(v); decls.add(id(toks[j]))                   # Ok(count) =>, Err(error) =>
        elif (prev == "(" and j + 3 < end and toks[j + 1][1] == ")" and toks[j + 2][1] == ")" and toks[j + 3][1] == "=>"
              and j >= 4 and toks[j - 3][1] == "(" and toks[j - 4][1] == "Err"):
            names.add(v); decls.add(id(toks[j]))                   # Err(IsoError(code)) =>
    return names, decls

_prelude = None

def prelude_symbols():
    global _prelude
    if _prelude is None:
        import pltcheck
        _prelude = Symbols(); collect(pltcheck.PRELUDE, _prelude, library=True)
        _prelude.add("CardError", "enum", {"defaultLibrary"})                   # the platform's error set (BP-5)
        _prelude.members["CardError"] = card_error_members()
    return _prelude

def card_error_members():
    """The CardError members of the Base Profile's table (tools/harness/scenario.py reads the same table)."""
    import re
    profile = HERE.parents[1] / "platform" / "base-profile.md"
    text = profile.read_text(encoding="utf-8") if profile.exists() else ""
    return set(re.findall(r"^\| `(\w+)` \| `0x[0-9A-Fa-f]{4}` \|", text, re.M))

def classify(target, texts):
    """Semantic tokens of file `target` (a key of texts) in the program whose files' texts are given."""
    syms = Symbols(); base = prelude_symbols()
    syms.kind.update(base.kind); syms.fields |= base.fields; syms.members.update(base.members)
    lexed = {}
    for path, text in texts.items():
        try: lexed[path] = lex(text.encode("utf-8"), path)
        except LexError: lexed[path] = []
    own = Symbols()
    for path, toks in lexed.items(): collect(toks, own)
    syms.kind.update(own.kind); syms.fields |= own.fields; syms.members.update(own.members); syms.decl_tokens = own.decl_tokens
    toks = lexed.get(target, [])
    scopes = []
    for params, _, start, end in functions(toks):
        names, decls = locals_in(toks, start, end)
        scopes.append((start, end, params, names, decls))
    for params, _, _, _ in functions(toks):
        for _, (_, tok) in params.items(): syms.decl_tokens.add(id(tok))
    out = []
    def scope_at(j):
        for s in scopes:
            if s[0] <= j <= s[1]: return s
        return None
    def param_scope_at(j):
        for params, open_paren, start, end in functions(toks):
            if open_paren <= j < start: return params
        return None
    for j, tok in enumerate(toks):
        kind, name = tok
        if kind != "id": continue
        prev = toks[j - 1][1] if j else None
        nxt = toks[j + 1][1] if j + 1 < len(toks) else None
        typ, mods = None, set()
        if prev == ".":
            owner = toks[j - 2][1] if j >= 2 else None
            path_start = j - 2
            while path_start >= 2 and toks[path_start - 1][1] == ".": path_start -= 2
            if toks[path_start][1] == "card": typ, mods = ("namespace" if nxt == "." else "function"), {"defaultLibrary"}
            elif owner in syms.members: typ = "enumMember"; mods = {"defaultLibrary"} if owner in base.members else set()
            elif name == "length": typ, mods = "property", {"defaultLibrary"}
            else: typ = "property"
        elif name == "card" and nxt == ".": typ, mods = "namespace", {"defaultLibrary"}
        elif name in PRIMITIVES: typ, mods = "type", {"defaultLibrary"}
        elif name in INTRINSICS and nxt in ("(", "<"): typ, mods = "macro", {"defaultLibrary"}
        else:
            s = scope_at(j); params = param_scope_at(j)
            if params is not None and name in params: typ, mods = "parameter", set(params[name][0])
            elif s and name in s[2]: typ, mods = "parameter", set(s[2][name][0])
            elif s and name in s[3]: typ = "variable"
            elif nxt == ":" and prev in ("{", ",") and name in syms.fields: typ = "property"       # a constructor's field
            elif name in syms.kind: typ, mods = syms.kind[name][0], set(syms.kind[name][1])
            elif name in syms.fields: typ = "property"
            elif any(name in m for m in syms.members.values()): typ = "enumMember"
        if typ is None: continue
        decl = id(tok) in syms.decl_tokens or any(id(tok) in sc[4] for sc in scopes)
        if decl: mods = mods | {"declaration"}
        _, line, col = tok.pos
        out.append((line - 1, col - 1, len(name), typ, mods))
    return out

def encode(tokens):
    """The LSP's relative encoding: [deltaLine, deltaStart, length, type, modifier bits] per token."""
    data, last_line, last_col = [], 0, 0
    for line, col, length, typ, mods in sorted(tokens):
        dl = line - last_line; dc = col - last_col if dl == 0 else col
        bits = sum(1 << MODIFIERS.index(m) for m in mods)
        data += [dl, dc, length, TYPES.index(typ), bits]; last_line, last_col = line, col
    return data
