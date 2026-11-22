"""Reference expression type checker for spec chapter 6 (bidirectional typing, EXP-1..EXP-51)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header
import layout
import project
from srcpos import note
import consteval

INT = ["u8", "u16", "u32", "i8", "i16", "i32"]
UNS = {"u8", "u16", "u32"}
SIG = {"i8", "i16", "i32"}
RANGE = consteval.RANGES
BIN = {"+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=", "and", "or", "&", "|", "^", "<<", ">>"}
CMP = {"==", "!=", "<", "<=", ">", ">="}
ARITH = {"+", "-", "*", "/", "%"}
BITW = {"&", "|", "^"}
CHECKED2 = {"checked_add", "checked_sub", "checked_mul", "checked_div", "checked_rem"}
WRAP = {"wrapping_add", "wrapping_sub", "wrapping_mul"}
TYARG = {"convert", "checked_convert", "truncate", "decode_be", "decode_le"}
BYTEW = {"u16", "u32", "i16", "i32"}

class CE(Exception):
    pass

# ---------------- parsing ----------------
class P:
    def __init__(self, toks): self.t = toks; self.i = 0
    def peek(self, k=0):
        if self.i + k >= len(self.t): return None
        if k == 0: note(self.t[self.i])                     # the token being examined (TL1: error positions)
        return self.t[self.i + k][1]
    def kind(self, k=0): return self.t[self.i + k][0] if self.i + k < len(self.t) else None
    def take(self): v = self.t[self.i]; note(v); self.i += 1; return v[1]
    def expect(self, v):
        if self.peek() != v: raise CE("CE-SYN-1")
        self.i += 1

def p_expr(p, nostruct=False):
    operands = [p_unary(p, nostruct)]; ops = []
    while p.peek() in BIN:
        ops.append(p.take()); operands.append(p_unary(p, nostruct))
    if not ops: return operands[0]
    if len(set(ops)) > 1: raise CE("CE-EXP-4")
    if ops[0] in CMP and len(ops) > 1: raise CE("CE-EXP-5")
    node = operands[0]
    for op, r in zip(ops, operands[1:]): node = ("bin", op, node, r)
    return node

def p_unary(p, ns):
    if p.peek() in ("-", "not", "~"):
        op = p.take(); return ("un", op, p_unary(p, ns))
    if p.peek() == "attempt":
        p.take(); call = p_postfix(p, ns)
        if p.peek() == "else":                                 # attempt c else E.M (WP9 L4)
            p.take(); return ("attempt", call, p_postfix(p, ns))
        return ("attempt", call)
    return p_postfix(p, ns)

def p_args(p):
    p.expect("("); out = []
    while p.peek() != ")":
        mode = p.take() if p.peek() in ("ref", "inout") else None
        out.append((mode, p_expr(p)))
        if p.peek() == ",": p.take()
    p.expect(")"); return out

def p_postfix(p, ns):
    n = p_primary(p, ns)
    while p.peek() in ("[", ".", "("):
        v = p.peek()
        if v == "[":
            p.take(); a = p_expr(p)
            if p.peek() == "..":
                p.take(); b = p_expr(p); p.expect("]"); n = ("slice", n, a, b)
            else:
                p.expect("]"); n = ("index", n, a)
        elif v == ".":
            p.take(); n = ("field", n, p.take())
        else:
            n = ("call", n, None, p_args(p))
    return n

def p_type(p):
    name = p.take(); dims = []
    while p.peek() == "[":
        p.take(); dims.append(None if p.peek() == "]" else consteval.expr(consteval.P(p.t[p.i:])))
        while p.peek() != "]": p.take()
        p.take()
    return (name, dims)

def p_primary(p, ns):
    k = p.kind(); v = p.take()
    if k == "bytes": return ("list", [("int", b) for b in v])                  # WP9 L1: an array list of bytes
    if k == "int": return ("int", consteval.primary(consteval.P([("int", v)]))[1])
    if v in ("true", "false"): return ("bool", v == "true")
    if v == "(":
        e = p_expr(p); p.expect(")"); return e
    if v == "[":
        items = []
        while p.peek() != "]":
            items.append(p_expr(p))
            if p.peek() == ",": p.take()
        p.expect("]"); return ("list", items)
    if k == "id":
        if v in TYARG and p.peek() == "<":
            p.take(); ty = p_type(p); p.expect(">"); return ("call", ("name", v), ty, p_args(p))
        if p.peek() == "{" and not ns and v[:1].isupper():
            p.take(); fields = []
            while p.peek() != "}":
                f = p.take(); p.expect(":"); fields.append((f, p_expr(p)))
                if p.peek() == ",": p.take()
            p.expect("}"); return ("ctor", v, fields)
        return ("name", v)
    raise CE("CE-SYN-1")

# ---------------- checker ----------------
class Checker:
    def __init__(self, toks):
        self.cp = consteval.Prog(toks)
        self.toks = toks
        self.structs = {n: {f: self.cp.resolve_type(t) for f, t in fs} for n, fs in self.cp.structs.items()}
        self.enums = {n: set(vs) for n, vs in self.cp.enums.items()}
        self.globals = {n: self.cp.resolve_type(t) for n, (t, _) in self.cp.globals.items()}
        self.consts = {n: self.cp.resolve_type(t) for n, (t, _) in self.cp.consts.items()}
        self.errors = {}
        self.funcs = {}
        p = P(toks)
        while p.peek() is not None:
            if p.peek() == "errors":
                p.take(); name = p.take(); p.expect("{"); mem = set()
                while p.peek() != "}":
                    mem.add(p.take())
                    while p.take() != ";": pass
                p.take(); self.errors[name] = mem; continue
            if p.peek() in ("function", "command"):
                p.take(); name = p.take(); p.expect("("); params = []
                while p.peek() != ")":
                    pn = p.take(); p.expect(":")
                    mode = p.take() if p.peek() in ("ref", "inout") else None
                    params.append((pn, mode, self.cp.resolve_type(p_type(p))))
                    if p.peek() == ",": p.take()
                p.expect(")"); ret = "none"
                if p.peek() == "->": p.take(); ret = self.cp.resolve_type(p_type(p))
                start = p.i; depth = 0
                while True:
                    t = p.take()
                    if t == "{": depth += 1
                    if t == "}":
                        depth -= 1
                        if depth == 0: break
                self.funcs[name] = (params, ret, toks[start:p.i]); continue
            p.take()

    # ---- types ----
    def is_int(self, t): return t in INT
    def same(self, a, b): return a == b

    def var_type(self, name, L):
        if name in L: return L[name]
        if name in self.globals: return self.globals[name]
        if name in self.consts: return self.consts[name]
        if name in self.funcs or name in self.structs or name in self.enums or name in self.errors: return ("notvalue", name)
        raise CE("CE-NAM-2")

    def synth(self, e, L, value=True):
        """Return a type, or None for an untyped literal-only expression."""
        k = e[0]
        if k == "int": return None
        if k == "bool": return "bool"
        if k == "name":
            t = self.var_type(e[1], L)
            if isinstance(t, tuple) and t[0] == "notvalue": raise CE("CE-EXP-1")
            return t
        if k == "un":
            op, a = e[1], e[2]
            if op == "-" and a[0] == "int": return None
            t = self.synth(a, L)
            if t is None: return None
            self.value(t)
            if op == "-" and t not in SIG: raise CE("CE-EXP-6")
            if op == "~" and t not in UNS: raise CE("CE-EXP-6")
            if op == "not" and t != "bool": raise CE("CE-EXP-1")
            return t
        if k == "bin":
            return self.binary(e, L, None)
        if k == "field":
            r = e[1]
            if r[0] == "name" and r[1] in self.enums:
                if e[2] not in self.enums[r[1]]: raise CE("CE-NAM-9")
                return r[1]
            if r[0] == "name" and r[1] in self.errors:
                return ("error", r[1])
            rt = self.synth(r, L)
            if rt is None: raise CE("CE-EXP-10") if r[0] in ("call", "list") else CE("CE-EXP-3")
            self.value(rt)
            if isinstance(rt, tuple) and rt[0] == "arr" and e[2] == "length": return "u32"
            if isinstance(rt, str) and rt in self.structs:
                if e[2] not in self.structs[rt]: raise CE("CE-EXP-13")
                return self.structs[rt][e[2]]
            raise CE("CE-EXP-13")
        if k == "index":
            rt = self.synth(e[1], L); self.value(rt)
            if not (isinstance(rt, tuple) and rt[0] == "arr"): raise CE("CE-EXP-1")
            it = self.synth(e[2], L)
            if it is None: self.check(e[2], "u32", L)
            elif it not in UNS: raise CE("CE-EXP-9")
            return rt[1]
        if k == "slice":
            rt = self.synth(e[1], L)
            for b in (e[2], e[3]):
                bt = self.synth(b, L)
                if bt is None: self.check(b, "u32", L)
                elif bt not in UNS: raise CE("CE-EXP-9")
            return ("arr", rt[1], None)
        if k == "list": raise CE("CE-EXP-10")
        if k == "ctor":
            if e[1] not in self.structs: raise CE("CE-EXP-15")
            fields = self.structs[e[1]]; seen = set()
            for f, x in e[2]:
                if f not in fields or f in seen: raise CE("CE-EXP-12")
                seen.add(f); self.check(x, fields[f], L)
            if seen != set(fields): raise CE("CE-EXP-12")
            return e[1]
        if k == "attempt":
            t = self.synth(e[1], L)
            if not (isinstance(t, tuple) and t[0] == "outcome"): raise CE("CE-EXP-1")
            if t[1] == "none": raise CE("CE-EXP-1")
            return t[1]
        if k == "call":
            return self.call(e, L, None)
        raise AssertionError(e)

    def value(self, t):
        if isinstance(t, tuple) and t[0] == "outcome": raise CE("CE-EXP-14")

    def check(self, e, T, L):
        k = e[0]
        if k == "int":
            if T not in INT: raise CE("CE-EXP-1")
            lo, hi = RANGE[T]
            if not lo <= e[1] <= hi: raise CE("CE-EXP-2")
            return
        if k == "un" and e[1] == "-" and e[2][0] == "int":
            if T in UNS: raise CE("CE-EXP-6")
            if T not in SIG: raise CE("CE-EXP-1")
            lo, hi = RANGE[T]
            if not lo <= -e[2][1] <= hi: raise CE("CE-EXP-2")
            return
        if k == "bin":
            t = self.binary(e, L, T)
        elif k == "list":
            if not (isinstance(T, tuple) and T[0] == "arr"): raise CE("CE-EXP-10")
            if len(e[1]) != T[2]: raise CE("CE-EXP-11")
            for x in e[1]: self.check(x, T[1], L)
            return
        elif k == "call" and e[1] == ("name", "fill"):
            if not (isinstance(T, tuple) and T[0] == "arr"): raise CE("CE-EXP-10")
            self.nested(e[3]); self.check(e[3][0][1], T[1], L); return
        elif k == "call":
            t = self.call(e, L, T)
        else:
            t = self.synth(e, L)
        if t is None: return
        self.value(t)
        if t != T: raise CE("CE-EXP-1")

    def binary(self, e, L, T):
        op, l, r = e[1], e[2], e[3]
        if op in ("and", "or"):
            self.check(l, "bool", L); self.check(r, "bool", L); return "bool"
        if op in ("<<", ">>"):
            lt = self.synth(l, L) or (T if T in INT else None)
            if lt is None: raise CE("CE-EXP-3")
            self.value(lt)
            if lt not in UNS: raise CE("CE-EXP-6")
            self.check(l, lt, L); ct = self.synth(r, L)
            if ct is None: self.check(r, "u8", L)
            elif ct != "u8": raise CE("CE-EXP-1")
            return lt
        lt, rt = self.synth(l, L), self.synth(r, L)
        for t in (lt, rt):
            if t is not None: self.value(t)
        ot = lt if lt is not None else rt
        if ot is None:
            if op in CMP: raise CE("CE-EXP-3")
            if T is None: return None  # untyped literal-only expression: the caller supplies context
            if T not in INT: raise CE("CE-EXP-3")
            ot = T
        if lt is not None and rt is not None and lt != rt: raise CE("CE-EXP-1")
        if op in ARITH and ot not in INT: raise CE("CE-EXP-6")
        if op in BITW and ot not in UNS: raise CE("CE-EXP-6")
        if op in ("<", "<=", ">", ">=") and ot not in INT: raise CE("CE-EXP-6")
        if op in ("==", "!=") and not (ot in INT or ot == "bool" or ot in self.enums): raise CE("CE-EXP-6")
        self.check(l, ot, L); self.check(r, ot, L)
        return "bool" if op in CMP else ot

    def nested(self, args):
        def has_call(n):
            if not isinstance(n, tuple): return False
            if n and n[0] in ("call", "attempt"): return True
            return any(has_call(c) for c in n[1:] if isinstance(c, tuple)) or any(
                has_call(x) for c in n[1:] if isinstance(c, list) for x in (c if not c or not isinstance(c[0], tuple) or len(c[0]) != 2 else [y for _, y in c]))
        for _, a in args:
            if has_call(a): raise CE("CE-EXP-7")

    def compare_intrinsic(self, name, ts):
        if not all(isinstance(t, tuple) and t[0] == "arr" for t in ts): raise CE("CE-EXP-1")
        if ts[0][1] != ts[1][1]: raise CE("CE-EXP-1")
        el = ts[0][1]
        if name == "compare":
            if el not in INT: raise CE("CE-EXP-6")
            return "i8"
        if isinstance(el, tuple) or el in self.structs: raise CE("CE-EXP-6")   # == is not defined on aggregates
        return "bool"

    def call(self, e, L, T):
        target, tyarg, args = e[1], e[2], e[3]
        if target[0] != "name": raise CE("CE-EXP-15")
        name = target[1]
        self.nested(args)
        if name in TYARG:
            ty = self.cp.resolve_type(tyarg)
            if len(args) != 1: raise CE("CE-EXP-16")
            mode, a = args[0]
            if name in ("decode_be", "decode_le"):
                if ty not in BYTEW: raise CE("CE-EXP-8")
                at = self.synth(a, L)
                if not (isinstance(at, tuple) and at[0] == "arr" and at[1] == "u8") or mode != "ref": raise CE("CE-EXP-1")
                return ty
            st = self.synth(a, L)
            if st is None or st not in INT or ty not in INT: raise CE("CE-EXP-8")
            if name == "convert":
                lo, hi = RANGE[st]; tlo, thi = RANGE[ty]
                if not (tlo <= lo and hi <= thi): raise CE("CE-EXP-8")
                return ty
            if name == "truncate": return ty
            return ("outcome", ty)
        if name in ("equal", "compare"):                 # EXP-53, EXP-54 (whole arrays; views in funcheck)
            if len(args) != 2: raise CE("CE-EXP-16")
            if any(m != "ref" for m, _ in args): raise CE("CE-FUN-2")
            return self.compare_intrinsic(name, [self.synth(a, L) for _, a in args])
        if name in ("encode_be", "encode_le"):
            if len(args) != 1: raise CE("CE-EXP-16")
            st = self.synth(args[0][1], L)
            if st not in BYTEW: raise CE("CE-EXP-8")
            return ("arr", "u8", 2 if st in ("u16", "i16") else 4)
        if name in CHECKED2 | WRAP or name == "checked_neg":
            want = 1 if name == "checked_neg" else 2
            if len(args) != want: raise CE("CE-EXP-16")
            if want == 2:
                t = self.binary(("bin", "+", args[0][1], args[1][1]), L, T if name in WRAP else None)
                if t is None: raise CE("CE-EXP-3")
            else:
                t = self.synth(args[0][1], L)
                if t is None: raise CE("CE-EXP-3")
                if t not in SIG: raise CE("CE-EXP-6")
            return t if name in WRAP else ("outcome", t)
        if name == "fill": raise CE("CE-EXP-10")
        if name in self.funcs:
            params, ret, _ = self.funcs[name]
            if len(args) != len(params): raise CE("CE-EXP-16")
            for (mode, a), (pn, pmode, pt) in zip(args, params):
                if isinstance(pt, tuple) and pt[0] == "arr" and pt[2] is None:
                    at = self.synth(a, L)
                    if not (isinstance(at, tuple) and at[0] == "arr" and at[1] == pt[1]): raise CE("CE-EXP-1")
                else:
                    self.check(a, pt, L)
            return ("outcome", ret)
        if name in L or name in self.globals or name in self.consts or name in self.structs or name in self.enums:
            raise CE("CE-EXP-15")
        raise CE("CE-NAM-2")

    # ---- statements ----
    def block(self, p, L, ret):
        p.expect("{")
        while p.peek() != "}":
            self.stmt(p, L, ret)
        p.expect("}")

    def stmt(self, p, L, ret):
        v = p.peek()
        if v == "var":
            p.take(); name = p.take(); p.expect(":"); t = self.cp.resolve_type(p_type(p))
            if p.peek() == "=":
                p.take(); self.check(p_expr(p), t, L)
            p.expect(";"); L[name] = t; return
        if v == "return":
            p.take()
            if p.peek() == "Ok":
                p.take(); p.expect("(")
                if p.peek() == ")":
                    p.take()
                else:
                    self.check(p_expr(p), ret, L); p.expect(")")
            elif p.peek() == "Err":
                p.take(); p.expect("("); p_expr(p); p.expect(")")
            else:
                t = self.synth(p_expr(p), L)
                if t != ("outcome", ret): raise CE("CE-EXP-1")
            p.expect(";"); return
        if v == "attempt":
            p.take(); e = p_postfix(p, False)
            if p.peek() == "else": p.take(); p_postfix(p, False)
            t = self.synth(e, L)
            if t != ("outcome", "none"): raise CE("CE-EXP-1")
            p.expect(";"); return
        if v == "ignore":
            p.take(); e = p_postfix(p, False); self.synth(e, L); p.expect(";"); return
        if v in ("if", "while"):
            # parse the condition and body first: syntax errors take precedence (Annex A §A.0)
            p.take(); cond = p_expr(p, nostruct=True)
            save = p.i; self._skip_block(p); p.i = save
            self.check(cond, "bool", L); self.block(p, dict(L), ret)
            while v == "if" and p.peek() == "else":
                p.take()
                if p.peek() == "if":
                    p.take(); c2 = p_expr(p, nostruct=True)
                    save = p.i; self._skip_block(p); p.i = save
                    self.check(c2, "bool", L)
                self.block(p, dict(L), ret)
            return
        if v == "for":
            p.take(); name = p.take(); p.expect(":"); t = self.cp.resolve_type(p_type(p)); p.expect("in")
            self.check(p_expr(p, True), t, L); p.expect(".."); self.check(p_expr(p, True), t, L)
            L2 = dict(L); L2[name] = t; self.block(p, L2, ret); return
        if v == "match":
            p.take(); st = self.synth(p_expr(p, nostruct=True), L); p.expect("{")
            while p.peek() != "}":
                L2 = dict(L)
                if p.peek() == "Ok":
                    p.take(); p.expect("(")
                    if p.peek() != ")":
                        b = p.take()
                        if b != "_": L2[b] = st[1]
                    p.expect(")")
                elif p.peek() == "Err":
                    p.take(); p.expect("(")
                    while p.peek() != ")": p.take()
                    p.expect(")")
                else:
                    while p.peek() != "=>": p.take()
                p.expect("=>"); self.block(p, L2, ret)
            p.expect("}"); return
        if v == "break" or v == "continue":
            p.take(); p.expect(";"); return
        # assignment
        dest = p_postfix(p, False)
        if p.peek() == "=":
            p.take(); dt = self.synth(dest, L); self.check(p_expr(p), dt, L); p.expect(";"); return
        if p.peek() in ("+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="):
            op = p.take()[:-1]; dt = self.synth(dest, L)
            if self.synth(("bin", op, dest, p_expr(p)), L) != dt: raise CE("CE-EXP-1")
            p.expect(";"); return
        raise CE("CE-SYN-1")

    def _skip_block(self, p):
        """Syntax-only pass over a block: statements must start like statements."""
        p.expect("{")
        while p.peek() != "}":
            v = p.peek()
            if v == "{":
                self._skip_block(p); continue
            at_statement_start = p.t[p.i - 1][1] in ("{", ";", "}")
            if (p.t[p.i - 1][1] == "{" and p.t[p.i - 2][0] == "id" and p.t[p.i - 2][1][:1].isupper()
                    and p.t[p.i - 3][1] in ("=", "(", ",", ":", "[")):
                at_statement_start = False   # the first field of a constructor in a value position, as in `= Pair { left: 1 }`
            if at_statement_start and p.kind() == "id" and p.peek(1) == ":":
                raise CE("CE-SYN-1")  # e.g. `low: 1` is not a statement
            p.take()
        p.expect("}")

    def run(self):
        for n, (ty, init) in self.cp.consts.items():
            if init is not None:
                self.check(p_expr(P(self._tokens_of_const(n))), self.consts[n], {})
        for name, (params, ret, body) in self.funcs.items():
            L = {pn: pt for pn, _, pt in params}
            self.block(P(body), L, ret)

    def _tokens_of_const(self, name):
        toks = self.toks
        for i in range(len(toks) - 2):
            if toks[i][1] == "const" and toks[i+1][1] == name:
                j = i
                while toks[j][1] != "=": j += 1
                k = j + 1; depth = 0
                while not (toks[k][1] == ";" and depth == 0):
                    punct = toks[k][1] if toks[k][0] == "p" else ""          # byte-string tokens carry a tuple
                    depth += punct in ("(", "[", "{") and 1 or 0; depth -= punct in (")", "]", "}") and 1 or 0; k += 1
                return toks[j+1:k]

def run(toks):
    Checker(toks).run()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/exp-*"
    for t in sorted((layout.at(repo).conformance).glob(glob)):
        files = project.program_files(t)
        toks = sum((lex(f.read_bytes()) for f in files), [])
        exp = header(files[0].read_bytes())["expect"]
        try:
            run(toks); got = "ok"
        except CE as e:
            got = "compile-error " + str(e)
        except consteval.CE as e:
            got = "compile-error " + str(e)
        st = "PASS" if got == exp else "FAIL"; ok &= st == "PASS"
        print(st, t.name, "| expect", exp, "| checker", got)
    print("ALL PASS" if ok else "FAILURES")
