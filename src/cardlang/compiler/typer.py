"""The static typing pass of the compiler (vm/decisions.md V-29).

The program has already been accepted by the full reference checker (pltcheck). This pass parses every function
body with the shared statement parser (checkers/stmtparse.py) and records the type of every expression node, by
reusing the checker's own type synthesis (synth, check, slice_type) on the parsed tree. Because the program is
valid, nothing here rejects; a CE raised during typing means the typer and the checker disagree, which is a bug.

Types use the checkers' representation:
    "u8" ... "i32", "bool", an enum or structure name, ("arr", T, N) with N None for a view,
    ("outcome", T) with T "none" for no payload, ("error", Set) for an error member.

Usage (from the repository root):
    uv run python -I -m cardlang.compiler.typer .      types every valid test, runtime test and example; prints PASS/FAIL
"""
import sys, pathlib
from cardlang.front.lexcheck import lex, header
from cardlang import layout
from cardlang.front import hepcheck, pltcheck, consteval
from cardlang.front.expcheck import P, CE
from cardlang.front.stmtparse import parse_block
from cardlang.front.project import program_files

class Typed:
    """A typed program: declarations from the checker, parsed bodies, and the type of every expression node."""
    def __init__(self, chk, bodies, types, decls, bindings):
        self.chk = chk                     # the PltChecker: structs, enums, globals, consts, errors, catalog, cp
        self.bodies = bodies               # function name -> parsed body (list of statements)
        self.types = types                 # id(expression node) -> type
        self.decls = decls                 # id(statement) -> the type it declares (var, for, match-arm bindings)
        self.bindings = bindings           # id(name node) of error bindings (Err(e) arms), which have no type
        self.funcs = {n: f for n, f in chk.funcs.items()}
        self.command = chk._commands[0]

    def type_of(self, e):
        return self.types[id(e)]

class Typer(pltcheck.PltChecker):
    # The program is valid: slices are allowed wherever they appear, nothing is read-only, no binding is misused.
    _slice_ok = property(lambda self: True, lambda self, v: None)

    def __init__(self, toks):
        super().__init__(toks)                                # declarations only; acceptance is type_program's
        self.types, self.decls, self.binding_nodes = {}, {}, set()
        self._ro = frozenset(); self._bindings = set()

    # ---- recording wrappers around the checker's own typing
    def _rec(self, e, t):
        if t is not None and isinstance(e, tuple): self.types[id(e)] = t
        return t

    def synth(self, e, L, value=True):
        return self._rec(e, super().synth(e, L, value))

    def check(self, e, T, L):
        super().check(e, T, L)
        if id(e) not in self.types: self.types[id(e)] = T      # literal-only and contextually typed nodes

    def slice_type(self, e, L):
        return self._rec(e, super().slice_type(e, L))

    # ---- statements
    def tblock(self, body, L, ret, bindings):
        L = dict(L)
        for s in body: self.tstmt(s, L, ret, bindings)

    def err_operand(self, e, L, bindings):
        if e[0] == "name" and e[1] in bindings: self.binding_nodes.add(id(e)); return
        self.synth(e, L)

    def tstmt(self, s, L, ret, bindings):
        k = s[0]
        if k == "var":
            T = self.cp.resolve_type(s[2])
            if s[3] is not None: self.check(s[3], T, L)
            L[s[1]] = T; self.decls[id(s)] = T
        elif k == "if":
            for c, b in s[1]:
                self.check(c, "bool", L); self.tblock(b, L, ret, bindings)
            if s[2] is not None: self.tblock(s[2], L, ret, bindings)
        elif k == "while":
            self.check(s[1], "bool", L); self.tblock(s[2], L, ret, bindings)
        elif k == "for":
            T = self.cp.resolve_type(s[2]); self.check(s[3], T, L); self.check(s[4], T, L)
            self.decls[id(s)] = T; L2 = dict(L); L2[s[1]] = T; self.tblock(s[5], L2, ret, bindings)
        elif k == "match":
            st = self.synth(s[1], L)
            for pat, body in s[2]:
                L2 = dict(L); b2 = bindings
                if pat[0] == "ok" and pat[1] not in (None, "_"):
                    L2[pat[1]] = st[1]
                elif pat[0] == "err_set" and pat[2] != "_":
                    L2[pat[2]] = "u16"
                elif pat[0] == "err_bind" and pat[1] != "_":
                    b2 = bindings | {pat[1]}
                self.tblock(body, L2, ret, b2)
        elif k in ("break", "continue"):
            pass
        elif k == "return_ok":
            if s[1] is not None: self.check(s[1], ret, L)
        elif k in ("return_err", "abort"):
            self.err_operand(s[1], L, bindings)
        elif k == "return_fwd":
            self.synth(s[1], L)
        elif k == "require":
            self.check(s[1], "bool", L); self.synth(s[2], L)
        elif k == "attempt":
            self.synth(s[1], L)
            if s[2] is not None: self.synth(s[2], L)
        elif k == "ignore":
            self.synth(s[1], L)
        elif k == "transaction":
            self.tblock(s[1], L, ret, bindings)
        elif k == "wipe":
            self.synth(s[1], L)
        elif k == "compound":
            self.synth(s[1], L)
            self.synth(("bin", s[2], s[1], s[3]), L)            # types the right operand as the operator does
        elif k == "assign":
            dest, src = s[1], s[2]
            dt = self.synth(dest, L)
            if dest[0] == "slice":
                if src[0] == "list" or (src[0] == "call" and src[1] == ("name", "fill")):
                    self.check(src, ("arr", dt[1], self.const_len(dest)), L)
                else:
                    self.synth(src, L)
            else:
                self.check(src, dt, L)
        else:
            raise AssertionError(("statement", s))

    def type_program(self):
        bodies = {}
        for name, (params, ret, body) in self.funcs.items():
            if name.startswith("card."): continue
            tree = parse_block(P(body)); bodies[name] = tree
            self.tblock(tree, {pn: pt for pn, _, pt in params}, ret, frozenset())
        return Typed(self, bodies, self.types, self.decls, self.binding_nodes)

def type_program(toks):
    """Accept the program with the unmodified full checker, then type it."""
    pltcheck.PltChecker(toks).run()
    return Typer(toks).type_program()

# ------------------------------------------------------------------ coverage: every expression node is typed
SKIP_CHILDREN = {"name", "int", "bool"}

def untyped(typed):
    """Expression nodes that the code generator will need a type for, but that have none."""
    missing = []
    enums, errors = typed.chk.enums, typed.chk.errors
    def expr(e):
        if not isinstance(e, tuple): return
        k = e[0]
        if k == "field" and e[1][0] == "name" and (e[1][1] in enums or e[1][1] in errors):
            if id(e) not in typed.types: missing.append(e)
            return                                         # an enum variant or an error member: the receiver is a set
        if k == "call":
            if id(e) not in typed.types: missing.append(e)
            for _, a in e[3]: expr(a)                      # the target is a name or a card path, not a value
            return
        if id(e) not in typed.types and id(e) not in typed.bindings: missing.append(e)
        if k == "bin": expr(e[2]); expr(e[3])
        elif k == "un" and e[1] == "-" and e[2][0] == "int": pass   # a negative literal (EXP-8): one constant
        elif k == "un": expr(e[2])
        elif k == "attempt": expr(e[1])                    # e[2], an error member of attempt ... else, has no value
        elif k in ("index",): expr(e[1]); expr(e[2])
        elif k == "slice": expr(e[1]); expr(e[2]); expr(e[3])
        elif k == "field": expr(e[1])
        elif k == "list": [expr(x) for x in e[1]]
        elif k == "ctor": [expr(x) for _, x in e[2]]
    def stmt(s):
        k = s[0]
        if k == "var":
            if s[3] is not None: expr(s[3])
        elif k == "if":
            for c, b in s[1]: expr(c); [stmt(x) for x in b]
            if s[2]: [stmt(x) for x in s[2]]
        elif k == "while": expr(s[1]); [stmt(x) for x in s[2]]
        elif k == "for": expr(s[3]); expr(s[4]); [stmt(x) for x in s[5]]
        elif k == "match":
            expr(s[1])
            for _, b in s[2]: [stmt(x) for x in b]
        elif k in ("return_ok",):
            if s[1] is not None: expr(s[1])
        elif k in ("return_err", "abort", "return_fwd", "ignore", "wipe"): expr(s[1])
        elif k == "require": expr(s[1]); expr(s[2])
        elif k == "attempt": expr(s[1])
        elif k == "transaction": [stmt(x) for x in s[1]]
        elif k == "compound": expr(s[1]); expr(s[3])
        elif k == "assign": expr(s[1]); expr(s[2])
    for body in typed.bodies.values():
        for s in body: stmt(s)
    return missing

def programs(repo):
    """(name, tokens) of every program the compiler must handle: valid tests, runtime tests, examples."""
    conf = layout.at(repo).conformance
    for f in sorted((conf / "valid").iterdir()):
        files = program_files(f) if f.is_dir() else [f] if f.suffix == ".card" else []
        if not files: continue
        toks = sum((lex(x.read_bytes(), str(x)) for x in files), [])
        if header(files[0].read_bytes()).get("kind", "fragment") == "fragment": toks = toks + lex(hepcheck.SCAFFOLD, "<scaffold>")
        yield f.stem if f.is_file() else f.name, toks
    for d in sorted((conf / "runtime").glob("run-*")):
        yield d.name, sum((lex(f.read_bytes(), str(f)) for f in program_files(d)), [])
    for d in sorted((layout.at(repo).examples).iterdir()):
        if (d / "cardlang.json").exists():
            from cardlang.front import project
            yield "examples/" + d.name, sum((lex(f.read_bytes(), str(f)) for f in project.program_files(d)), [])

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True
    for name, toks in programs(repo):
        try:
            typed = type_program(toks); miss = untyped(typed)
            problem = f"{len(miss)} untyped node(s), first {miss[0]!r}"[:200] if miss else None
        except (CE, consteval.CE) as e:
            problem = "typing raised " + str(e)
        ok &= problem is None
        print("PASS" if problem is None else "FAIL", name, "" if problem is None else "| " + problem)
    print("ALL PASS" if ok else "FAILURES")
