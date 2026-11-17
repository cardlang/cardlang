"""Reference interpreter for CardLang runtime conformance tests (non-normative).

It executes the scenario of every test in conformance/runtime/ and compares host-visible results
(responses, errors, traps) with the scenario's `expect` lines. Each program is first checked by the
full static checker (hepcheck). When this interpreter and spec/ disagree, the specification wins.

Usage (from the repository root):
    python -I tools/interp/interp.py . ["runtime/run-*"]
"""
import copy, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "checkers"))
from lexcheck import lex, header
import hepcheck, expcheck, consteval
from expcheck import P, p_expr, p_postfix, p_type, CE

RANGES = consteval.RANGES
WIDTH = {"u8": 8, "u16": 16, "u32": 32, "i8": 8, "i16": 16, "i32": 32}
SIGNED = {"i8", "i16", "i32"}
BUDGET = 200_000

# ------------------------------------------------------------------ runtime values and signals
class Int:
    __slots__ = ("v", "t")
    def __init__(self, v, t): self.v, self.t = v, t
    def __repr__(self): return f"{self.v}:{self.t}"

class ErrVal:
    """An error value: category 'app' with a code, or 'platform' with a CardError member name."""
    def __init__(self, category, ident): self.category, self.ident = category, ident

class View:
    def __init__(self, lst, start, length): self.lst, self.start, self.length = lst, start, length

class Place:
    def __init__(self, c, k): self.c, self.k = c, k
    def get(self): return self.c[self.k]
    def set(self, v): self.c[self.k] = v

class RefTo:
    def __init__(self, place): self.place = place

class Trap(Exception):
    def __init__(self, kind): super().__init__(kind); self.kind = kind
class Ret(Exception):
    def __init__(self, outcome): self.outcome = outcome
class Brk(Exception): pass
class Cont(Exception): pass
class Abort(Exception):
    def __init__(self, err): self.err = err
class Interrupted(Exception): pass

def copy_value(v):
    if isinstance(v, list): return [copy_value(x) for x in v]
    if isinstance(v, dict): return {k: copy_value(x) for k, x in v.items()}
    return v

def restore(live, snap):
    """Roll back a container in place, keeping object identity (references into it stay valid)."""
    keys = range(len(live)) if isinstance(live, list) else list(live.keys())
    for k in keys:
        if isinstance(live[k], (list, dict)) and isinstance(snap[k], (list, dict)) and type(live[k]) is type(snap[k]):
            restore(live[k], snap[k])
        else:
            live[k] = copy_value(snap[k])

# ------------------------------------------------------------------ statement parser
def parse_block(p):
    p.expect("{"); out = []
    while p.peek() != "}":
        out.append(parse_stmt(p))
    p.expect("}"); return out

def parse_pattern(p):
    if p.peek() == "Ok":
        p.take(); p.expect("(")
        name = None if p.peek() == ")" else p.take()
        p.expect(")"); return ("ok", name)
    if p.peek() == "Err":
        p.take(); p.expect("(")
        if p.peek(1) == ".":
            owner = p.take(); p.take(); member = p.take(); p.expect(")"); return ("err_member", owner, member)
        name = p.take(); p.expect(")"); return ("err_bind", name)
    if p.peek() == "_":
        p.take(); return ("wild",)
    owner = p.take(); p.expect("."); return ("enum", owner, p.take())

def parse_stmt(p):
    v = p.peek()
    if v == "var":
        p.take(); name = p.take(); p.expect(":"); ty = p_type(p); init = None
        if p.peek() == "=":
            p.take(); init = p_expr(p)
        p.expect(";"); return ("var", name, ty, init)
    if v == "if":
        branches = []; p.take(); c = p_expr(p, True); branches.append((c, parse_block(p))); other = None
        while p.peek() == "else":
            p.take()
            if p.peek() == "if":
                p.take(); c = p_expr(p, True); branches.append((c, parse_block(p)))
            else:
                other = parse_block(p)
        return ("if", branches, other)
    if v == "while":
        p.take(); c = p_expr(p, True); return ("while", c, parse_block(p))
    if v == "for":
        p.take(); name = p.take(); p.expect(":"); ty = p_type(p); p.expect("in")
        lo = p_expr(p, True); p.expect(".."); hi = p_expr(p, True); return ("for", name, ty, lo, hi, parse_block(p))
    if v == "match":
        p.take(); s = p_expr(p, True); p.expect("{"); arms = []
        while p.peek() != "}":
            pat = parse_pattern(p); p.expect("=>"); arms.append((pat, parse_block(p)))
        p.expect("}"); return ("match", s, arms)
    if v in ("break", "continue"):
        p.take(); p.expect(";"); return (v,)
    if v == "return":
        p.take()
        if p.peek() == "Ok":
            p.take(); p.expect("(")
            e = None if p.peek() == ")" else p_expr(p)
            p.expect(")"); p.expect(";"); return ("return_ok", e)
        if p.peek() == "Err":
            p.take(); p.expect("("); e = p_expr(p); p.expect(")"); p.expect(";"); return ("return_err", e)
        e = p_expr(p); p.expect(";"); return ("return_fwd", e)
    if v == "require":
        p.take(); c = p_expr(p); p.expect("else"); e = p_expr(p); p.expect(";"); return ("require", c, e)
    if v == "attempt":
        p.take(); e = p_postfix(p, False); p.expect(";"); return ("attempt", e)
    if v == "transaction":
        p.take(); return ("transaction", parse_block(p))
    if v == "abort":
        p.take(); p.expect("Err"); p.expect("("); e = p_expr(p); p.expect(")"); p.expect(";"); return ("abort", e)
    dest = p_expr(p); p.expect("="); e = p_expr(p); p.expect(";"); return ("assign", dest, e)

# ------------------------------------------------------------------ the machine
class Card:
    def __init__(self, toks):
        self.chk = hepcheck.HepChecker(toks)
        self.chk.run()                                   # static checks first
        cp = self.chk.cp
        self.types = lambda ty: cp.resolve_type(ty)
        self.funcs = {n: (params, ret, parse_block(P(body))) for n, (params, ret, body) in self.chk.funcs.items()}
        self.command_name = self.chk._commands[0]
        self.enum_order = cp.enums
        self.structs = self.chk.structs
        self.persistent_types = {n: self.chk.globals[n] for n, (ty, _) in cp.globals.items() if self.kind_of(toks, n) == "persistent"}
        self.session_types = {n: t for n, t in self.chk.globals.items() if n not in self.persistent_types}
        self.consts = {n: self.conv(cp.const_value(n)[0], self.chk.consts[n]) for n in cp.consts}
        self.codes = self.error_codes(toks)
        self.persistent = None; self.session = None
        self.interrupt_next_commit = False; self.in_txn = None

    @staticmethod
    def kind_of(toks, name):
        for i in range(len(toks) - 1):
            if toks[i][1] in ("persistent", "session") and toks[i+1][1] == name: return toks[i][1]
        return None

    @staticmethod
    def error_codes(toks):
        codes = {}
        for i, (_, v) in enumerate(toks):
            if v == "errors":
                owner = toks[i+1][1]; j = i + 3
                while toks[j][1] != "}":
                    codes[(owner, toks[j][1])] = consteval.primary(consteval.P([toks[j+2]]))[1]; j += 4
        return codes

    # ---- types and defaults
    def default(self, T):
        if T in RANGES: return Int(0, T)
        if T == "bool": return False
        if isinstance(T, tuple): return [self.default(T[1]) for _ in range(T[2])]
        if T in self.enum_order: return ("enum", T, self.enum_order[T][0])
        return dict({f: self.default(ft) for f, ft in self.structs[T].items()}, **{"#": T})

    def conv(self, v, T):
        """Convert a constant from the constant evaluator's representation."""
        if T in RANGES: return Int(v, T)
        if T == "bool": return v
        if isinstance(T, tuple): return [self.conv(x, T[1]) for x in v]
        if T in self.enum_order: return ("enum",) + tuple(v.split("."))
        return dict({f: self.conv(v[f], self.structs[T][f]) for f in self.structs[T]}, **{"#": T})

    def type_of(self, v):
        if isinstance(v, Int): return v.t
        if isinstance(v, bool): return "bool"
        if isinstance(v, list): return ("arr", self.type_of(v[0]), len(v))
        if isinstance(v, dict): return v["#"]
        if isinstance(v, tuple) and v[0] == "enum": return v[1]
        return None

    def coerce(self, v, T):
        if isinstance(v, Int) and v.t is None and T in RANGES: return Int(v.v, T)
        if isinstance(v, list) and isinstance(T, tuple): return [self.coerce(x, T[1]) for x in v]
        return v

    # ---- arithmetic
    def ranged(self, v, T):
        lo, hi = RANGES[T]
        if v > hi: raise Trap("OVERFLOW")
        if v < lo: raise Trap("UNDERFLOW")
        return Int(v, T)

    def arith(self, op, a, b, T):
        x, y = a.v, b.v
        if T is None:                                         # untyped literal-only arithmetic
            return Int({"+": x + y, "-": x - y, "*": x * y}.get(op, x), None) if op in "+-*" else Int(x // y if y else 0, None)
        if op in ("/", "%"):
            if y == 0: raise Trap("DIV-ZERO")
            q = abs(x) // abs(y) * (1 if (x >= 0) == (y >= 0) else -1)
            return self.ranged(q, T) if op == "/" else Int(x - q * y, T)
        if op in ("&", "|", "^"):
            return Int({"&": x & y, "|": x | y, "^": x ^ y}[op], T)
        return self.ranged({"+": x + y, "-": x - y, "*": x * y}[op], T)

    @staticmethod
    def wrap(v, T):
        n = WIDTH[T]; v &= (1 << n) - 1
        if T in SIGNED and v >= 1 << (n - 1): v -= 1 << n
        return Int(v, T)

    # ---- expressions
    def lookup(self, env, name):
        for scope in reversed(env["scopes"]):
            if name in scope: return scope, name
        if name in self.consts: return self.consts, name
        if name in self.persistent_types: return self.persistent, name
        if name in self.session_types: return self.session, name
        raise RuntimeError("unresolved " + name)

    def place(self, e, env):
        k = e[0]
        if k == "name":
            c, n = self.lookup(env, e[1]); v = c[n]
            if isinstance(v, RefTo): return v.place
            if isinstance(v, View): return v
            return Place(c, n)
        if k == "field":
            base = self.place(e[1], env)
            return Place(base.get(), e[2])
        if k == "index":
            base = self.place(e[1], env)
            idx = self.eval(e[2], env, "u32").v
            if isinstance(base, View):
                if idx >= base.length: raise Trap("BOUNDS")
                return Place(base.lst, base.start + idx)
            lst = base.get()
            if idx >= len(lst): raise Trap("BOUNDS")
            return Place(lst, idx)
        if k == "slice":
            base = self.place(e[1], env)
            s = self.eval(e[2], env, "u32").v; t = self.eval(e[3], env, "u32").v
            lst, off, n = (base.lst, base.start, base.length) if isinstance(base, View) else (base.get(), 0, len(base.get()))
            if s > t or t > n: raise Trap("BOUNDS")
            return View(lst, off + s, t - s)
        tmp = {"v": self.eval(e, env)}                     # read-only temporary (e.g. a ref to a constant)
        return Place(tmp, "v")

    def tick(self, env):
        env["card"]["budget"] -= 1
        if env["card"]["budget"] < 0: raise Trap("EXHAUSTED")

    def eval(self, e, env, T=None):
        k = e[0]
        if k == "int": return Int(e[1], T if T in RANGES else None)
        if k == "bool": return e[1]
        if k == "name":
            c, n = self.lookup(env, e[1]); v = c[n]
            return v.place.get() if isinstance(v, RefTo) else v
        if k == "field":
            r = e[1]
            if r[0] == "name" and r[1] in self.enum_order: return ("enum", r[1], e[2])
            if r[0] == "name" and (r[1] == "CardError" or any(o == r[1] for o, _ in self.codes)):
                return ErrVal("platform", e[2]) if r[1] == "CardError" else ErrVal("app", self.codes[(r[1], e[2])])
            if e[2] == "length":
                base = self.place(r, env) if r[0] in ("name", "field", "index", "slice") else None
                if isinstance(base, View): return Int(base.length, "u32")
                val = base.get() if base is not None else self.eval(r, env)
                if isinstance(val, list): return Int(len(val), "u32")
            return self.place(e, env).get()
        if k == "index": return self.place(e, env).get()
        if k == "un":
            op, a = e[1], e[2]
            if op == "not": return not self.eval(a, env, "bool")
            x = self.eval(a, env, T)
            if op == "-":
                if x.t is None: return Int(-x.v, None)
                if x.v == RANGES[x.t][0]: raise Trap("NEGATION")
                return Int(-x.v, x.t)
            return Int(~x.v & ((1 << WIDTH[x.t]) - 1), x.t)
        if k == "bin": return self.binary(e, env, T)
        if k == "attempt":
            out = self.eval(e[1], env)
            if out[0] == "err": raise Ret(out)
            return copy_value(out[1])
        if k == "call": return self.call(e, env, T)
        if k == "list":
            et = T[1] if isinstance(T, tuple) else None
            return [self.coerce(self.eval(x, env, et), et) for x in e[1]]
        if k == "ctor":
            out = {"#": e[1]}
            for f, x in e[2]:
                ft = self.structs[e[1]][f]; out[f] = self.coerce(copy_value(self.eval(x, env, ft)), ft)
            return out
        raise RuntimeError(("cannot evaluate", e))

    def binary(self, e, env, T):
        op, l, r = e[1], e[2], e[3]
        if op == "and": return self.eval(l, env, "bool") and self.eval(r, env, "bool")
        if op == "or": return self.eval(l, env, "bool") or self.eval(r, env, "bool")
        a = self.eval(l, env, T if op not in ("==", "!=", "<", "<=", ">", ">=") else None)
        if op in ("<<", ">>"):
            b = self.eval(r, env, "u8"); t = a.t or (T if T in RANGES else None)
            if b.v >= WIDTH[t]: raise Trap("SHIFT")
            return Int((a.v << b.v) & ((1 << WIDTH[t]) - 1), t) if op == "<<" else Int(a.v >> b.v, t)
        b = self.eval(r, env, a.t if isinstance(a, Int) else None)
        if op in ("==", "!="):
            same = (a.v == b.v) if isinstance(a, Int) else (a == b)
            return same if op == "==" else not same
        if op in ("<", "<=", ">", ">="):
            return {"<": a.v < b.v, "<=": a.v <= b.v, ">": a.v > b.v, ">=": a.v >= b.v}[op]
        t = a.t or b.t or (T if T in RANGES else None)
        return self.arith(op, a, b, t)

    # ---- calls
    def call(self, e, env, T):
        name, tyarg, args = e[1][1], e[2], e[3]
        if name in self.funcs:
            return self.invoke(name, args, env)
        vals = lambda ts=(None, None): [self.eval(a, env, t) for (_, a), t in zip(args, ts)]
        if name == "convert": return self.coerce(Int(self.eval(args[0][1], env).v, None), self.types(tyarg))
        if name == "truncate": return self.wrap(self.eval(args[0][1], env).v, self.types(tyarg))
        if name == "checked_convert":
            t = self.types(tyarg); v = self.eval(args[0][1], env).v; lo, hi = RANGES[t]
            return ("ok", Int(v, t)) if lo <= v <= hi else ("err", ErrVal("platform", "ConversionRange"))
        if name in ("encode_be", "encode_le"):
            v = self.eval(args[0][1], env); n = WIDTH[v.t] // 8; u = v.v & ((1 << WIDTH[v.t]) - 1)
            bs = [Int((u >> (8 * (n - 1 - i))) & 0xFF, "u8") for i in range(n)]
            return bs if name == "encode_be" else bs[::-1]
        if name in ("decode_be", "decode_le"):
            t = self.types(tyarg); src = self.place(args[0][1], env)
            data = [src.lst[src.start + i].v for i in range(src.length)] if isinstance(src, View) else [x.v for x in src.get()]
            n = WIDTH[t] // 8
            if len(data) != n: raise Trap("BOUNDS")
            if name == "decode_le": data = data[::-1]
            u = 0
            for byte in data: u = (u << 8) | byte
            return self.wrap(u, t)
        if name == "fill":
            v = self.eval(args[0][1], env, T[1])
            return [self.coerce(copy_value(v), T[1]) for _ in range(T[2])]
        if name.startswith("wrapping_"):
            a, b = vals((T, T)); t = a.t or b.t or T
            x, y = a.v, b.v
            return self.wrap({"wrapping_add": x + y, "wrapping_sub": x - y, "wrapping_mul": x * y}[name], t)
        if name.startswith("checked_"):
            op = {"checked_add": "+", "checked_sub": "-", "checked_mul": "*", "checked_div": "/", "checked_rem": "%"}.get(name)
            try:
                if name == "checked_neg":
                    x = self.eval(args[0][1], env)
                    if x.v == RANGES[x.t][0]: raise Trap("NEGATION")
                    return ("ok", Int(-x.v, x.t))
                a, b = vals(); t = a.t or b.t
                return ("ok", self.arith(op, Int(a.v, t), Int(b.v, t), t))
            except Trap as tr:
                member = {"OVERFLOW": "Overflow", "UNDERFLOW": "Underflow", "DIV-ZERO": "DivisionByZero", "NEGATION": "Overflow"}[tr.kind]
                return ("err", ErrVal("platform", member))
        raise RuntimeError("unknown callee " + name)

    def invoke(self, name, args, env):
        params, ret, body = self.funcs[name]
        scope = {}
        for (mode, a), (pn, pmode, pt) in zip(args, params):          # left to right, before entry
            if pmode is None:
                scope[pn] = self.coerce(copy_value(self.eval(a, env, pt)), pt)
            else:
                target = self.place(a, env)
                if isinstance(pt, tuple) and pt[2] is None:
                    scope[pn] = target if isinstance(target, View) else View(target.get(), 0, len(target.get()))
                else:
                    scope[pn] = target if isinstance(target, View) else RefTo(target)
        callee = {"scopes": [scope], "ret": ret, "card": env["card"]}
        try:
            self.block(body, callee)
        except Ret as r:
            return r.outcome
        raise RuntimeError(f"{name} completed without an outcome")

    # ---- statements
    def block(self, stmts, env):
        env["scopes"].append({})
        try:
            for s in stmts:
                self.stmt(s, env)
        finally:
            env["scopes"].pop()

    def outcome_of_return(self, s, env):
        if s[0] == "return_ok":
            if s[1] is None: return ("ok", None)
            return ("ok", self.coerce(copy_value(self.eval(s[1], env, env["ret"])), env["ret"]))
        if s[0] == "return_err": return ("err", self.eval(s[1], env))
        return self.eval(s[1], env)

    def stmt(self, s, env):
        self.tick(env)
        k = s[0]
        if k == "var":
            t = self.types(s[2])
            v = self.default(t) if s[3] is None else self.coerce(copy_value(self.eval(s[3], env, t)), t)
            env["scopes"][-1][s[1]] = v
        elif k == "assign":
            dest = self.place(s[1], env)                       # destination path first (STM-9)
            t = self.type_of(dest.get())
            v = self.eval(s[2], env, t)
            dest.set(self.coerce(copy_value(v), t))
        elif k == "if":
            for cond, blk in s[1]:
                if self.eval(cond, env, "bool"):
                    self.block(blk, env); return
            if s[2] is not None: self.block(s[2], env)
        elif k == "while":
            while self.eval(s[1], env, "bool"):
                self.tick(env)
                try: self.block(s[2], env)
                except Brk: break
                except Cont: continue
        elif k == "for":
            t = self.types(s[2]); lo = self.eval(s[3], env, t).v; hi = self.eval(s[4], env, t).v
            for i in range(lo, hi):
                env["scopes"].append({s[1]: Int(i, t)})
                try: self.block(s[5], env)
                except Brk: break
                except Cont: continue
                finally: env["scopes"].pop()
        elif k == "match":
            v = self.eval(s[1], env)
            for pat, blk in s[2]:
                bind = self.matches(pat, v)
                if bind is not None:
                    env["scopes"].append(bind)
                    try: self.block(blk, env)
                    finally: env["scopes"].pop()
                    return
            raise RuntimeError("no match arm")
        elif k == "break": raise Brk()
        elif k == "continue": raise Cont()
        elif k.startswith("return"): raise Ret(self.outcome_of_return(s, env))
        elif k == "require":
            if not self.eval(s[1], env, "bool"): raise Ret(("err", self.eval(s[2], env)))
        elif k == "attempt":
            out = self.eval(s[1], env)
            if out[0] == "err": raise Ret(out)
        elif k == "transaction":
            snap = copy.deepcopy(self.persistent)
            try:
                self.block(s[1], env)
            except Abort as a:
                restore(self.persistent, snap); raise Ret(("err", a.err))
            except BaseException:
                restore(self.persistent, snap); raise
            if self.interrupt_next_commit:                     # power loss during the commit
                self.interrupt_next_commit = False
                restore(self.persistent, snap); raise Interrupted()
        elif k == "abort":
            raise Abort(self.eval(s[1], env))
        else:
            raise RuntimeError(("statement", s))

    def matches(self, pat, v):
        if pat[0] == "enum": return {} if v == ("enum", pat[1], pat[2]) else None
        if v[0] == "ok":
            if pat[0] != "ok": return None
            return {} if pat[1] in (None, "_") else {pat[1]: copy_value(v[1])}
        if pat[0] == "err_member":
            e = v[1]
            if pat[1] == "CardError": return {} if e.category == "platform" and e.ident == pat[2] else None
            return {} if e.category == "app" and e.ident == self.codes[(pat[1], pat[2])] else None
        if pat[0] == "err_bind": return {} if pat[1] == "_" else {pat[1]: v[1]}
        return None

    # ---- the card lifecycle (scenario steps)
    def run_handler(self, name):
        if name in self.funcs:
            env = {"scopes": [], "ret": "none", "card": {"budget": BUDGET}}
            try:
                self.invoke(name, [], env)
            except Trap:
                pass                                           # handler failure handling is platform-defined

    def install(self):
        self.persistent = {n: self.default(t) for n, t in self.persistent_types.items()}
        self.run_handler("on_install")

    def power_on(self):
        self.session = {n: self.default(t) for n, t in self.session_types.items()}
        self.run_handler("on_power_on")

    def reset(self):
        self.session = None

    def command(self, request, capacity):
        if self.persistent is None or self.session is None: raise RuntimeError("command before install/power_on")
        req = View([Int(b, "u8") for b in request], 0, len(request))
        resp = View([Int(0, "u8") for _ in range(capacity)], 0, capacity)
        params, ret, body = self.funcs[self.command_name]
        env = {"scopes": [{params[0][0]: req, params[1][0]: resp}], "ret": "u32", "card": {"budget": BUDGET}}
        try:
            self.block(body, env)
            raise RuntimeError("command completed without an outcome")
        except Ret as r:
            out = r.outcome
        except Trap as t:
            return ("trap", t.kind)
        except Interrupted:
            self.session = None                                # power loss clears volatile state
            return ("none",)
        if out[0] == "err":
            e = out[1]
            return ("err", e.category, e.ident)
        count = out[1].v
        if count > capacity: return ("trap", "RESPONSE-COUNT")
        return ("ok", [resp.lst[i].v for i in range(count)])

# ------------------------------------------------------------------ scenarios
def parse_expect(words):
    if words[0] == "ok": return ("ok", [int(w, 16) for w in words[1:]])
    if words[0] == "err" and words[1] == "app": return ("err", "app", int(words[2]))
    if words[0] == "err" and words[1] == "platform": return ("err", "platform", words[2])
    if words[0] == "trap": return ("trap", words[1])
    if words[0] == "none": return ("none",)
    raise ValueError(words)

def run_scenario(card, text):
    pending = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#")[0].split()
        if not line: continue
        step = line[0]
        if step == "install": card.install()
        elif step == "power_on": card.power_on()
        elif step == "reset": card.reset()
        elif step == "interrupt": card.interrupt_next_commit = True
        elif step == "command":
            words = line[1:]; capacity = 256
            if "capacity" in words:
                i = words.index("capacity"); capacity = int(words[i + 1]); words = words[:i]
            pending = card.command([int(w, 16) for w in words], capacity)
        elif step == "expect":
            want = parse_expect(line[1:])
            if pending != want:
                return f"line {lineno}: expected {want}, got {pending}"
            pending = None
        else:
            return f"line {lineno}: unknown step {step}"
    return None

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); glob = sys.argv[2] if len(sys.argv) > 2 else "runtime/run-*"
    ok = True
    for d in sorted((repo / "conformance").glob(glob)):
        files = [d / f for f in (d / "files.txt").read_text().split()] if (d / "files.txt").exists() else sorted(d.glob("*.card"))
        toks = sum((lex(f.read_bytes()) for f in files), [])
        try:
            card = Card(toks)
            problem = run_scenario(card, (d / "scenario.txt").read_text(encoding="utf-8"))
        except (CE, consteval.CE) as e:
            problem = "does not compile: " + str(e)
        status = "PASS" if problem is None else "FAIL"; ok &= problem is None
        print(status, d.name, "" if problem is None else "| " + problem)
    print("ALL PASS" if ok else "FAILURES")
