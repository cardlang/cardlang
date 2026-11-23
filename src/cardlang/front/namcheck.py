"""Reference checker for the name rules of spec chapter 3 (NAM-9, NAM-11, NAM-12, NAM-14, NAM-15, NAM-16, NAM-21).

It works on the tokens of a grammatical program (Annex A derives it) and runs before the other checkers, which
assume unique names:

- **Storage keywords (NAM-9):** a top-level value declaration has exactly one of `persistent`, `session`, `const`
  (CE-NAM-6). Keywords inside a body (NAM-10, CE-NAM-7) are the statement checker's.
- **The application scope (NAM-11, NAM-12):** every top-level name is unique across all files and kinds (CE-NAM-1).
- **Predeclared names (NAM-14):** no top-level declaration takes one (CE-NAM-5), except a `function` named after a
  lifecycle handler.
- **Member scopes (NAM-15, NAM-16):** no structure, enum or error set has two members of one name (CE-NAM-8); a
  qualified `Owner.Member` names a member its owner has (CE-NAM-9).
- **Lexical scopes (NAM-19 to NAM-21):** a parameter, local, `for` index or pattern binding shadows no visible name
  (CE-NAM-3) and repeats no name of its own scope (CE-NAM-4). A local is visible after its declaration (NAM-20).

Unresolved names (CE-NAM-2) and platform paths (CE-NAM-10) are found by the expression and catalog checkers.
"""
import sys, pathlib
from cardlang.front.lexcheck import lex, header
from cardlang import layout
from cardlang.front import project, srcpos, consteval
from cardlang.front.expcheck import CE
from cardlang.front.outcheck import CARD_ERROR

PRIMITIVES = {"u8", "u16", "u32", "i8", "i16", "i32", "bool"}
INTRINSICS = {"fill", "convert", "checked_convert", "checked_add", "checked_sub", "checked_mul", "checked_div",
              "checked_rem", "checked_neg", "wrapping_add", "wrapping_sub", "wrapping_mul", "truncate", "encode_be",
              "encode_le", "decode_be", "decode_le", "equal", "compare"}
PLATFORM = {"card", "CardError"}
HANDLERS = {"on_install", "on_session_start"}
PREDECLARED = PRIMITIVES | INTRINSICS | PLATFORM | HANDLERS
STORAGE = {"persistent", "session", "const", "var"}
OPEN, CLOSE = {"(", "[", "{"}, {")", "]", "}"}

def _err(code, tok):
    return srcpos.at(CE(code), tok)

class NameChecker:
    def __init__(self, toks, prelude=()):
        self.t = list(toks)
        self.members = {"CardError": set(CARD_ERROR)}      # enum and error-set members, for NAM-16
        self.predeclared = set(PREDECLARED)
        for kind, name, _, members, _ in self.declarations(list(prelude)):
            self.predeclared.add(name)
            if kind in ("enum", "errors"): self.members[name] = {m[1] for m in members}

    # ---------------- top level ----------------
    def skip_to(self, i, stops):
        """The index of the first token at i or after, outside brackets, whose value is in stops."""
        depth = 0
        while i < len(self.t):
            v = self.t[i][1]
            if depth == 0 and v in stops: return i
            if v in OPEN: depth += 1
            elif v in CLOSE: depth -= 1
            i += 1
        return i

    def declarations(self, t=None):
        """(kind, name, name token, members, body start) for each top-level declaration. Members are name tokens
        (fields, variants, error members) or, for a function or command, (name token) parameters."""
        saved = self.t
        if t is not None: self.t = t
        try:
            out = []; i = 0
            while i < len(self.t):
                v = self.t[i][1]
                if v in STORAGE:
                    j = i
                    while self.t[j][1] in STORAGE: j += 1
                    out.append(("value", self.t[j][1], self.t[j], self.t[i:j], None))
                    i = self.skip_to(j, {";"}) + 1
                elif v in ("struct", "enum", "errors"):
                    name = self.t[i + 1]; j = i + 3; members = []
                    while self.t[j][1] != "}":
                        members.append(self.t[j]); j = self.skip_to(j, {";"}) + 1
                    out.append((v, name[1], name, members, None)); i = j + 1
                elif v in ("function", "command"):
                    name = self.t[i + 1]; j = i + 3; params = []
                    while self.t[j][1] != ")":
                        params.append(self.t[j]); j = self.skip_to(j, {",", ")"})
                        if self.t[j][1] == ",": j += 1
                    body = self.skip_to(j + 1, {"{"})
                    out.append((v, name[1], name, params, body)); i = self.skip_to(body + 1, {"}"}) + 1
                else:
                    i += 1                                    # not grammatical: the grammar reports it
            return out
        finally:
            self.t = saved

    def run(self):
        decls = self.declarations()
        seen = set()
        for kind, name, tok, members, _ in decls:
            if kind == "value":
                kws = [k[1] for k in members]
                if len(kws) != 1: raise _err("CE-NAM-6", members[1])              # NAM-9: two or more keywords
                if kws[0] == "var": raise _err("CE-NAM-6", members[0])            # NAM-9: plain var
            if name in self.predeclared and not (kind == "function" and name in HANDLERS):
                raise _err("CE-NAM-5", tok)                                       # NAM-14
            if name in seen: raise _err("CE-NAM-1", tok)                          # NAM-11, NAM-12
            seen.add(name)
            if kind in ("struct", "enum", "errors"):
                names = set()
                for m in members:
                    if m[1] in names: raise _err("CE-NAM-8", m)                   # NAM-15
                    names.add(m[1])
                if kind != "struct": self.members[name] = names
        app = seen | self.predeclared
        for kind, name, tok, params, body in decls:
            if kind not in ("function", "command"): continue
            scopes = [app, set()]
            for p in params: self.bind(p, scopes)
            self.block(body, scopes)
        self.qualified()

    # ---------------- lexical scopes ----------------
    def bind(self, tok, scopes):
        """Declare tok's name in the innermost scope (NAM-21)."""
        name = tok[1]
        if name == "_": return
        if name in scopes[-1]: raise _err("CE-NAM-4", tok)
        if any(name in s for s in scopes[:-1]): raise _err("CE-NAM-3", tok)
        scopes[-1].add(name)

    def block(self, i, scopes):
        """Check the block at token i ('{'); return the index after its '}'."""
        scopes = scopes + [set()]; i += 1
        while self.t[i][1] != "}":
            i = self.statement(i, scopes)
        return i + 1

    def statement(self, i, scopes):
        v = self.t[i][1]
        if v in STORAGE:                                      # var x: T = e;  visible after it (NAM-20)
            j = i
            while self.t[j][1] in STORAGE: j += 1
            end = self.skip_to(j, {";"})
            self.bind(self.t[j], scopes)
            return end + 1
        if v in ("if", "while"):
            i = self.block(self.skip_to(i + 1, {"{"}), scopes)
            while v == "if" and i < len(self.t) and self.t[i][1] == "else":
                if self.t[i + 1][1] == "if": i = self.block(self.skip_to(i + 2, {"{"}), scopes)
                else: i = self.block(i + 1, scopes)
            return i
        if v == "for":                                        # the index is in scope in the body only
            inner = scopes + [set()]
            self.bind(self.t[i + 1], inner)
            return self.block(self.skip_to(i + 2, {"{"}), inner)
        if v == "match":
            i = self.skip_to(i + 1, {"{"}) + 1
            while self.t[i][1] != "}":
                arrow = self.skip_to(i, {"=>"})
                inner = scopes + [set()]
                b = self.pattern_binding(self.t[i:arrow])
                if b is not None: self.bind(b, inner)
                i = self.block(arrow + 1, inner)
            return i + 1
        if v == "transaction":
            return self.block(i + 1, scopes)
        if v == "{":
            return self.block(i, scopes)
        return self.skip_to(i, {";"}) + 1

    @staticmethod
    def pattern_binding(p):
        """The binding token of a match pattern, or None: Ok(b), Err(b), Err(Set(b))."""
        vals = [x[1] for x in p]
        if len(vals) == 4 and vals[0] in ("Ok", "Err") and p[2][0] == "id": return p[2]
        if len(vals) == 7 and vals[0] == "Err" and vals[3] == "(" and p[4][0] == "id": return p[4]
        return None

    # ---------------- qualified members ----------------
    def qualified(self):
        """NAM-16: Owner.Member names a member of an enum or error set Owner. Field selections (after '.') and
        platform paths are left to the expression and catalog checkers."""
        t = self.t
        for i in range(len(t) - 2):
            if (t[i][0] == "id" and t[i][1] in self.members and t[i + 1][1] == "." and t[i + 2][0] == "id"
                    and (i == 0 or t[i - 1][1] != ".") and t[i + 2][1] not in self.members[t[i][1]]):
                raise _err("CE-NAM-9", t[i + 2])

def check(toks, prelude=()):
    """Raise CE for the first violation of the chapter 3 name rules in a program's tokens."""
    NameChecker(toks, prelude).run()

if __name__ == "__main__":
    from cardlang.front import pltcheck
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/nam-*"
    MINE = {"CE-NAM-1", "CE-NAM-3", "CE-NAM-4", "CE-NAM-5", "CE-NAM-6", "CE-NAM-8", "CE-NAM-9"}
    for t in sorted((layout.at(repo).conformance).glob(glob)):
        files = project.program_files(t)
        toks = sum((lex(f.read_bytes()) for f in files), [])
        exp = header(files[0].read_bytes())["expect"]
        if exp not in ("ok", "runtime") and exp.split()[-1] not in MINE:
            print("SKIP", t.name, "| expect", exp, "| found by another checker"); continue
        want = "ok" if exp in ("ok", "runtime") else exp
        try:
            check(toks, pltcheck.PRELUDE); got = "ok"
        except (CE, consteval.CE) as e:
            got = "compile-error " + str(e)
        st = "PASS" if got == want else "FAIL"; ok &= st == "PASS"
        print(st, t.name, "| expect", exp, "| checker", got)
    print("ALL PASS" if ok else "FAILURES")
