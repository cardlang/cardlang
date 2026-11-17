"""Reference checker for spec chapter 8 (FUN-1..FUN-23), built on stmcheck/expcheck."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header
import stmcheck, expcheck, consteval
from expcheck import CE, UNS, p_expr

class FunChecker(stmcheck.StmChecker):
    _slice_ok = False
    _ro = frozenset()

    def run(self):
        self.check_call_graph()
        super().run()

    # FUN-5: cycles in the static call graph
    def check_call_graph(self):
        edges = {}
        for name, (_, _, body) in self.funcs.items():
            callees = set()
            for i, (k, v) in enumerate(body):
                if v in self.funcs and i + 1 < len(body) and body[i+1][1] == "(" and (i == 0 or body[i-1][1] != "."):
                    callees.add(v)
            edges[name] = callees
        state = {}
        def visit(n):
            state[n] = 1
            for m in edges.get(n, ()):
                if state.get(m) == 1: raise CE("CE-FUN-1")
                if m not in state: visit(m)
            state[n] = 2
        for n in edges:
            if n not in state: visit(n)

    def sstmt(self, p, L, ret, ro, loops):
        self._ro = frozenset(ro)
        return super().sstmt(p, L, ret, ro, loops)

    def sblock(self, p, L, ret, ro, loops):
        saved = self._ro
        r = super().sblock(p, L, ret, ro, loops)
        self._ro = saved
        return r

    # ---- slices (FUN-18..FUN-21) ----
    def slice_type(self, e, L):
        recv = e[1]
        rt = self.slice_type(recv, L) if recv[0] == "slice" else self.synth(recv, L)
        if not (isinstance(rt, tuple) and rt[0] == "arr"): raise CE("CE-EXP-1")
        for b in (e[2], e[3]):
            bt = self.synth(b, L)
            if bt is None: self.check(b, "u32", L)
            elif bt not in UNS: raise CE("CE-EXP-9")
        if rt[2] is not None and e[2][0] == "int" and e[3][0] == "int":
            s, t = e[2][1], e[3][1]
            if s > t or t > rt[2]: raise CE("CE-CEX-4")
        return ("arr", rt[1], None)

    @staticmethod
    def const_len(e):
        """Length of a slice whose endpoints are both literals, else None."""
        return e[3][1] - e[2][1] if e[2][0] == "int" and e[3][0] == "int" else None

    def slice_place(self, e, L, ro):
        self.place(self.root(e), L, ro)
        return self.slice_type(e, L)

    def slice_assign(self, e, p, L, ro):
        """FUN-24: place[s..e] = source;"""
        dt = self.slice_place(e, L, ro); dlen = self.const_len(e)
        src = p_expr(p); p.expect(";")
        if src[0] == "slice":
            st = self.slice_type(src, L); slen = self.const_len(src)
        elif src[0] == "list" or (src[0] == "call" and src[1] == ("name", "fill")):
            if dlen is None: raise CE("CE-EXP-10")
            self.check(src, ("arr", dt[1], dlen), L); return
        else:
            st = self.synth(src, L); slen = st[2] if isinstance(st, tuple) and st[0] == "arr" else None
        if not (isinstance(st, tuple) and st[0] == "arr" and st[1] == dt[1]): raise CE("CE-EXP-1")
        if dlen is not None and slen is not None and dlen != slen: raise CE("CE-STM-8")

    def synth(self, e, L, value=True):
        k = e[0]
        if k == "slice":
            if not self._slice_ok: raise CE("CE-FUN-5")
            self._slice_ok = False
            return self.slice_type(e, L)
        if k == "index" and e[1][0] == "slice":
            rt = self.slice_type(e[1], L)
            it = self.synth(e[2], L)
            if it is None: self.check(e[2], "u32", L)
            elif it not in UNS: raise CE("CE-EXP-9")
            return rt[1]
        if k == "field" and e[1][0] == "slice":
            self.slice_type(e[1], L)
            if e[2] != "length": raise CE("CE-EXP-13")
            return "u32"
        return super().synth(e, L, value)

    # ---- reference arguments (FUN-9, FUN-10, FUN-15) ----
    def root(self, e):
        while e[0] in ("field", "index", "slice"): e = e[1]
        return e

    def storage(self, e, L):
        r = self.root(e)
        if r[0] != "name": raise CE("CE-FUN-3")
        if e[0] == "field" and e[2] == "length":
            t = self.synth(e[1], L) if e[1][0] != "slice" else ("arr", None, None)
            if isinstance(t, tuple) and t[0] == "arr": raise CE("CE-FUN-3")
        n = r[1]
        if not (n in L or n in self.globals or n in self.consts): raise CE("CE-FUN-3")
        return n

    def call(self, e, L, T):
        target, tyarg, args = e[1], e[2], e[3]
        if target[0] == "name" and target[1] in self.funcs:
            name = target[1]; params, ret, _ = self.funcs[name]
            self.nested(args)
            if len(args) != len(params): raise CE("CE-EXP-16")
            for (mode, a), (pn, pmode, pt) in zip(args, params):
                if mode != pmode: raise CE("CE-FUN-2")
                unsized = isinstance(pt, tuple) and pt[0] == "arr" and pt[2] is None
                if mode in ("ref", "inout"):
                    n = self.storage(a, L)
                    if mode == "inout" and (n in self.consts or n in self._ro): raise CE("CE-FUN-4")
                    self._slice_ok = True
                    at = self.synth(a, L)
                    self._slice_ok = False
                    if unsized:
                        if not (isinstance(at, tuple) and at[0] == "arr" and at[1] == pt[1]): raise CE("CE-EXP-1")
                    elif at is None:
                        self.check(a, pt, L)
                    elif at != pt:
                        raise CE("CE-EXP-1")
                else:
                    self.check(a, pt, L)
            return ("outcome", ret)
        if target[0] == "name" and target[1] in ("equal", "compare"):
            self.nested(args)
            if len(args) != 2: raise CE("CE-EXP-16")
            ts = []
            for mode, a in args:
                if mode != "ref": raise CE("CE-FUN-2")
                self.storage(a, L); self._slice_ok = True
                ts.append(self.synth(a, L)); self._slice_ok = False
            return self.compare_intrinsic(target[1], ts)
        if target[0] == "name" and target[1] in ("decode_be", "decode_le"):
            if len(args) == 1 and args[0][0] != "ref": raise CE("CE-FUN-2")
            self._slice_ok = True
            try:
                return super().call(e, L, T)
            finally:
                self._slice_ok = False
        for mode, _ in args:
            if mode is not None: raise CE("CE-FUN-2")
        return super().call(e, L, T)

def run(toks):
    FunChecker(toks).run()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/fun-*"
    for t in sorted((repo / "conformance").glob(glob)):
        files = [t / f for f in (t / "files.txt").read_text().split()] if t.is_dir() else [t]
        toks = sum((lex(f.read_bytes()) for f in files), [])
        exp = header(files[0].read_bytes())["expect"]
        try:
            run(toks); got = "ok"
        except (CE, consteval.CE) as e:
            got = "compile-error " + str(e)
        st = "PASS" if got == exp else "FAIL"; ok &= st == "PASS"
        print(st, t.name, "| expect", exp, "| checker", got)
    print("ALL PASS" if ok else "FAILURES")
