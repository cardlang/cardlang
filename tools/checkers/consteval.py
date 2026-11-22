"""Reference constant evaluator for spec chapter 5 (CEX-3..CEX-13), arithmetic per DN §3.5/§6.5."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header
import layout
import project
import srcpos
from srcpos import note

RANGES = {"u8": (0, 255), "u16": (0, 65535), "u32": (0, 2**32 - 1),
          "i8": (-128, 127), "i16": (-32768, 32767), "i32": (-2**31, 2**31 - 1)}
WIDTH = {"u8": 8, "u16": 16, "u32": 32, "i8": 8, "i16": 16, "i32": 32}
EXCLUDED = {"checked_convert", "checked_add", "checked_sub", "checked_mul", "checked_div",
            "checked_rem", "checked_neg", "wrapping_add", "wrapping_sub", "wrapping_mul"}

class CE(Exception):
    pass

RT = object()  # runtime-dependent marker

# ---------- parsing ----------
class P:
    def __init__(self, toks): self.t = toks; self.i = 0
    def peek(self, k=0):
        if self.i + k >= len(self.t): return None
        if k == 0: note(self.t[self.i])                     # the token being examined (TL1: error positions)
        return self.t[self.i + k][1]
    def take(self): v = self.t[self.i]; note(v); self.i += 1; return v
    def expect(self, v):
        assert self.peek() == v, (v, self.t[self.i:self.i+5]); self.i += 1

BIN = {"+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=", "&", "|", "^", "<<", ">>", "and", "or"}

def expr(p):
    left = unary(p)
    while p.peek() in BIN:
        op = p.take()[1]; right = unary(p); left = ("bin", op, left, right)
    return left

def unary(p):
    if p.peek() in ("-", "not", "~"):
        op = p.take()[1]; return ("un", op, unary(p))
    if p.peek() == "attempt":
        p.take(); return ("attempt", postfix(p))
    return postfix(p)

def postfix(p):
    n = primary(p)
    while p.peek() in ("[", "."):
        if p.take()[1] == "[":
            idx = expr(p)
            if p.peek() == "..":
                p.take(); end = expr(p); p.expect("]"); n = ("slice", n, idx, end)
            else:
                p.expect("]"); n = ("index", n, idx)
        else:
            n = ("field", n, p.take()[1])
    return n

def args(p):
    out = []; p.expect("(")
    while p.peek() != ")":
        if p.peek() in ("ref", "inout"): p.take()
        out.append(expr(p))
        if p.peek() == ",": p.take()
    p.expect(")"); return out

def primary(p):
    k, v = p.take()
    if k == "bytes": return ("list", [("int", b) for b in v])                  # WP9 L1
    if k == "int":
        s = v.replace("_", "")  # LEX-17/LEX-19: a leading zero is decimal, never octal
        return ("int", int(s[2:], 16) if s.startswith("0x") else int(s[2:], 2) if s.startswith("0b") else int(s, 10))
    if v in ("true", "false"): return ("bool", v == "true")
    if v == "(":
        e = expr(p); p.expect(")"); return e
    if v == "[":
        items = []
        while p.peek() != "]":
            items.append(expr(p))
            if p.peek() == ",": p.take()
        p.expect("]"); return ("list", items)
    if k == "id":
        if p.peek() == "<":
            p.take(); ty = p.take()[1]; p.expect(">"); return ("call", v, ty, args(p))
        if p.peek() == "(":
            return ("call", v, None, args(p))
        if p.peek() == "{" and v[:1].isupper():
            p.take(); fields = {}
            while p.peek() != "}":
                f = p.take()[1]; p.expect(":"); fields[f] = expr(p)
                if p.peek() == ",": p.take()
            p.expect("}"); return ("ctor", v, fields)
        return ("name", v)
    raise AssertionError(("bad primary", v))

def parse_type(p):
    name = p.take()[1]; dims = []
    while p.peek() == "[":
        p.take()
        if p.peek() == "]": dims.append(None)
        else: dims.append(expr(p))
        p.expect("]")
    return (name, dims)

# ---------- program model ----------
class Prog:
    def __init__(self, toks):
        self.consts, self.globals, self.structs, self.enums, self.funcs = {}, {}, {}, {}, []
        p = P(toks)
        while p.peek() is not None:
            v = p.peek()
            if v in ("const", "persistent", "session"):
                p.take(); name = p.take()[1]; p.expect(":"); ty = parse_type(p); init = None
                if p.peek() == "=": p.take(); init = expr(p)
                p.expect(";")
                (self.consts if v == "const" else self.globals)[name] = (ty, init)
            elif v in ("struct", "enum"):
                p.take(); name = p.take()[1]; p.expect("{"); mem = []
                while p.peek() != "}":
                    m = p.take()[1]
                    if v == "struct": p.expect(":"); mem.append((m, parse_type(p)))
                    else: mem.append(m)
                    p.expect(";")
                p.expect("}"); (self.structs if v == "struct" else self.enums)[name] = mem
            elif v == "errors":
                while p.take()[1] != "}":
                    pass
            elif v in ("function", "command"):
                p.take(); name = p.take()[1]; depth = 0; p.expect("(")
                params = []
                while p.peek() != ")":
                    pn = p.take()[1]; p.expect(":")
                    if p.peek() in ("ref", "inout"): p.take()
                    params.append((pn, parse_type(p)))
                    if p.peek() == ",": p.take()
                p.expect(")"); ret = None
                if p.peek() == "->": p.take(); ret = parse_type(p)
                start = p.i
                while True:
                    t = p.take()[1]
                    if t == "{": depth += 1
                    if t == "}":
                        depth -= 1
                        if depth == 0: break
                self.funcs.append((name, params, ret, toks[start:p.i]))
            else:
                raise AssertionError(("top", v))
        self.cache, self.active = {}, set()

    # ----- types -----
    def resolve_type(self, ty):
        name, dims = ty
        t = name
        for d in dims:
            if d is None: t = ("arr", t, None); continue
            ln = self.ev(d, "u32", length=True)
            if ln is RT: raise CE("CE-CEX-2")
            t = ("arr", t, ln[0])
        return t

    # ----- constants -----
    def const_value(self, name):
        if name in self.cache: return self.cache[name]
        if name in self.active: raise srcpos.at(CE("CE-CEX-5"), srcpos.decl(name))
        self.active.add(name)
        ty, init = self.consts[name]
        if init is None: raise CE("CE-CEX-1")
        t = self.resolve_type(ty)
        v = self.ev(init, t)
        if v is RT: raise CE("CE-CEX-2")
        self.active.discard(name); self.cache[name] = (v[0], t); return self.cache[name]

    def global_type(self, name):
        key = "g:" + name
        if key in self.cache: return self.cache[key]
        if key in self.active: raise srcpos.at(CE("CE-CEX-5"), srcpos.decl(name))
        self.active.add(key); t = self.resolve_type(self.globals[name][0]); self.active.discard(key)
        self.cache[key] = t; return t

    # ----- evaluation: returns RT or (value, type) -----
    def check_range(self, v, t):
        lo, hi = RANGES[t]
        if not lo <= v <= hi: raise CE("CE-CEX-3")
        return (v, t)

    def static_type(self, n, local_types):
        """Type of a plain path (names and fields) without reading contents; None if not a plain path."""
        if n[0] == "name":
            if n[1] in self.globals: return self.global_type(n[1])
            if n[1] in self.consts: return self.const_value(n[1])[1]
            if n[1] in local_types: return local_types[n[1]]
            return None
        if n[0] == "field":
            st = self.static_type(n[1], local_types)
            if isinstance(st, str) and st in self.structs:
                for f, fty in self.structs[st]:
                    if f == n[2]: return self.resolve_type(fty)
        return None

    def ev(self, n, ctx, length=False, locals_=None):
        L = locals_ or {}
        k = n[0]
        if k == "int":
            return self.check_range(n[1], ctx) if ctx in RANGES else (n[1], None)
        if k == "bool": return (n[1], "bool")
        if k == "name":
            if n[1] in self.consts: return self.const_value(n[1])
            return RT
        if k == "field":
            if n[2] == "length":
                st = self.static_type(n[1], L)
                if isinstance(st, tuple) and st[0] == "arr" and st[2] is not None:
                    return (st[2], "u32")
            if n[1][0] == "name" and n[1][1] in self.enums:
                return (n[1][1] + "." + n[2], n[1][1])
            b = self.ev(n[1], None, locals_=L)
            if b is RT: return RT
            return (b[0][n[2]], None)
        if k == "index":
            base = self.ev(n[1], None, locals_=L)
            idx = self.ev(n[2], "u32" if not self.typed(n[2]) else None, locals_=L)
            st = self.static_type(n[1], L)
            ln = st[2] if isinstance(st, tuple) and st[0] == "arr" else (len(base[0]) if base is not RT else None)
            if idx is not RT and ln is not None and idx[0] >= ln: raise CE("CE-CEX-4")
            if base is RT or idx is RT: return RT
            return (base[0][idx[0]], None)
        if k == "un":
            op = n[1]
            if op == "-" and n[2][0] == "int":  # negative literal in context
                return self.check_range(-n[2][1], ctx) if ctx in RANGES else (-n[2][1], None)
            a = self.ev(n[2], ctx, locals_=L)
            if a is RT: return RT
            if op == "not": return (not a[0], "bool")
            if op == "-": return self.check_range(-a[0], a[1])
            if op == "~": return ((~a[0]) & ((1 << WIDTH[a[1]]) - 1), a[1])
        if k == "bin":
            op, l, r = n[1], n[2], n[3]
            if op in ("and", "or"):
                a = self.ev(l, "bool", locals_=L)
                if a is not RT and ((op == "and" and a[0] is False) or (op == "or" and a[0] is True)):
                    return a  # right operand skipped (still type-checked by a real compiler)
                b = self.ev(r, "bool", locals_=L)  # evaluated even behind a runtime guard
                if a is RT or b is RT: return RT
                return (a[0] and b[0], "bool") if op == "and" else (a[0] or b[0], "bool")
            cmp = op in ("==", "!=", "<", "<=", ">", ">=")
            lt, rt = self.typeof(l, L), self.typeof(r, L)
            if op in ("<<", ">>"):
                ot = lt or (ctx if ctx in RANGES else None)
                a = self.ev(l, ot, locals_=L); b = self.ev(r, "u8", locals_=L)
                if a is RT or b is RT: return RT
                if b[0] >= WIDTH[ot]: raise CE("CE-CEX-3")
                return ((a[0] << b[0]) & ((1 << WIDTH[ot]) - 1) if op == "<<" else a[0] >> b[0], ot)
            ot = lt or rt or (None if cmp else ctx)
            a = self.ev(l, ot, locals_=L); b = self.ev(r, ot, locals_=L)
            if a is RT or b is RT: return RT
            x, y = a[0], b[0]
            if cmp:
                return ({"==": x == y, "!=": x != y, "<": x < y, "<=": x <= y, ">": x > y, ">=": x >= y}[op], "bool")
            if op in ("/", "%"):
                if y == 0: raise CE("CE-CEX-3")
                q = abs(x) // abs(y) * (1 if (x >= 0) == (y >= 0) else -1)
                return self.check_range(q, ot) if op == "/" else (x - q * y, ot)
            v = {"+": x + y, "-": x - y, "*": x * y, "&": x & y, "|": x | y, "^": x ^ y}[op]
            return self.check_range(v, ot)
        if k == "list":
            et = ctx[1] if isinstance(ctx, tuple) else None
            vals = [self.ev(e, et, locals_=L) for e in n[1]]
            return RT if any(v is RT for v in vals) else ([v[0] for v in vals], ctx)
        if k == "ctor":
            fts = dict(self.structs[n[1]]); out = {}
            for f, e in n[2].items():
                v = self.ev(e, self.resolve_type(fts[f]), locals_=L)
                if v is RT: return RT
                out[f] = v[0]
            return (out, n[1])
        if k == "call":
            name, ty, a = n[1], n[2], n[3]
            if name == "fill":
                v = self.ev(a[0], ctx[1] if isinstance(ctx, tuple) else None, locals_=L)
                return RT if v is RT else ([v[0]] * ctx[2], ctx)
            if name == "convert":
                v = self.ev(a[0], None, locals_=L)
                return RT if v is RT else self.check_range(v[0], ty)
            for e in a: self.ev(e, None, locals_=L)  # constant-only args still evaluated
            return RT  # calls and excluded intrinsics are never constant
        if k == "attempt":
            return RT
        if k == "slice":
            return RT
        raise AssertionError(n)

    def typed(self, n):
        return self.typeof(n, {}) is not None

    def typeof(self, n, L):
        if n[0] == "name":
            if n[1] in self.consts: return self.consts[n[1]][0][0] if not self.consts[n[1]][0][1] else None
            if n[1] in self.globals and not self.globals[n[1]][0][1]: return self.globals[n[1]][0][0]
            if n[1] in L and isinstance(L[n[1]], str): return L[n[1]]
            return None
        if n[0] == "field" and n[2] == "length": return "u32"
        if n[0] == "index":
            st = self.static_type(n[1], L)
            return st[1] if isinstance(st, tuple) else None
        if n[0] == "un" and n[1] != "not": return self.typeof(n[2], L)
        if n[0] == "bin" and n[1] not in ("==", "!=", "<", "<=", ">", ">=", "and", "or"):
            return self.typeof(n[2], L) or self.typeof(n[3], L)
        if n[0] == "call" and n[1] == "convert": return n[2]
        return None

    # ----- function bodies: evaluate constant-only parts of each expression -----
    def check_bodies(self):
        for name, params, ret, body in self.funcs:
            L = {pn: self.resolve_type(pt) for pn, pt in params}
            rett = self.resolve_type(ret) if ret else None
            toks = body; i = 0
            while i < len(toks):
                v = toks[i][1]
                if v == "var":
                    vn = toks[i+1][1]; p = P(toks); p.i = i + 3; vt = self.resolve_type(parse_type(p))
                    if p.peek() == "=":
                        p.take(); self.ev(expr(p), vt, locals_=L)
                    L[vn] = vt; i = p.i; continue
                if v == "Ok" and toks[i+1][1] == "(" and toks[i+2][1] != ")":
                    p = P(toks); p.i = i + 2; self.ev(expr(p), rett, locals_=L); i = p.i; continue
                if v == "=" and toks[i-1][1] in ("]",) :
                    # destination index check: walk back to the indexed name
                    j = i - 1; depth = 0
                    while True:
                        if toks[j][1] == "]": depth += 1
                        if toks[j][1] == "[":
                            depth -= 1
                            if depth == 0: break
                        j -= 1
                    p = P(toks); p.i = j - 1; dest = postfix(p)
                    self.ev(dest, None, locals_=L)
                    p.i = i + 1; self.ev(expr(p), None, locals_=L); i = p.i; continue
                i += 1

def run(toks):
    pr = Prog(toks)
    for name in pr.consts: pr.const_value(name)
    for name in pr.globals: pr.global_type(name)
    pr.check_bodies()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True
    for t in sorted((layout.at(repo).conformance).glob("*/cex-*")):
        files = project.program_files(t)
        toks = sum((lex(f.read_bytes()) for f in files), [])
        exp = header(files[0].read_bytes())["expect"]
        try:
            run(toks); got = "ok"
        except CE as e:
            got = "compile-error " + str(e)
        st = "PASS" if got == exp else "FAIL"; ok &= st == "PASS"
        print(st, t.name, "| expect", exp, "| evaluator", got)
    print("ALL CEX TESTS PASS" if ok else "CEX FAILURES")
