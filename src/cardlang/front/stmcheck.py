"""Reference statement checker for spec chapter 7 (STM-1..STM-22), built on expcheck."""
import sys, pathlib
from cardlang.front.lexcheck import lex, header
from cardlang import layout
from cardlang.front import project
from cardlang.front import expcheck, consteval
from cardlang.front.expcheck import CE, P, p_expr, p_postfix, INT

class StmChecker(expcheck.Checker):
    def run(self):
        for n, (ty, init) in self.cp.consts.items():
            if init is not None:
                self.check(p_expr(P(self._tokens_of_const(n))), self.consts[n], {})
        for name, (params, ret, body) in self.funcs.items():
            L = {pn: pt for pn, _, pt in params}
            ro = {pn for pn, mode, _ in params if mode != "inout"}
            p = P(body)
            completes = self.sblock(p, L, ret, ro, loops=[])
            if completes: raise CE("CE-STM-5")

    # returns True if the block may complete normally
    def sblock(self, p, L, ret, ro, loops):
        p.expect("{")
        L = dict(L); ro = set(ro); completes = True
        while p.peek() != "}":
            c = self.sstmt(p, L, ret, ro, loops)
            completes = completes and c
        p.expect("}")
        return completes

    def place(self, e, L, ro):
        """STM-7: return normally if e is an assignable place."""
        k = e[0]
        if k == "name":
            n = e[1]
            if n in ro: raise CE("CE-STM-2")
            if n in L or n in self.globals: return
            if n in self.consts or n in self.funcs or n in self.structs or n in self.enums or n in self.errors:
                raise CE("CE-STM-2")
            raise CE("CE-NAM-2")
        if k == "field":
            if e[2] == "length":
                rt = self.synth(e[1], L)
                if isinstance(rt, tuple) and rt[0] == "arr": raise CE("CE-STM-2")
            if e[1][0] == "name" and (e[1][1] in self.enums or e[1][1] in self.errors): raise CE("CE-STM-2")
            return self.place(e[1], L, ro)
        if k == "index":
            return self.place(e[1], L, ro)
        raise CE("CE-STM-2")

    def slice_place(self, e, L, ro):
        raise CE("CE-STM-2")                              # chapter 7 alone: slices are chapter 8

    def slice_assign(self, e, p, L, ro):
        raise CE("CE-STM-2")

    def sstmt(self, p, L, ret, ro, loops):
        v = p.peek()
        if v == "{": raise CE("CE-SYN-1")                       # STM-3
        if v in ("var", "persistent", "session", "const"):
            kws = []
            while p.peek() in ("var", "persistent", "session", "const"): kws.append(p.take())
            if kws != ["var"]: raise CE("CE-NAM-7")
            name = p.take(); p.expect(":"); t = self.cp.resolve_type(expcheck.p_type(p))
            if p.peek() == "=":
                p.take(); self.check(p_expr(p), t, L)
            p.expect(";"); L[name] = t; return True
        if v == "return":
            p.take()
            if p.peek() == "Ok":
                p.take(); p.expect("(")
                if p.peek() == ")": p.take()
                else: self.check(p_expr(p), ret, L); p.expect(")")
            elif p.peek() == "Err":
                p.take(); p.expect("("); p_expr(p); p.expect(")")
            else:
                t = self.synth(p_expr(p), L)
                if t != ("outcome", ret): raise CE("CE-EXP-1")
            p.expect(";"); return False
        if v == "attempt":
            p.take(); e = p_postfix(p, False)
            if p.peek() == "else": p.take(); p_postfix(p, False)
            t = self.synth(e, L)
            if t != ("outcome", "none"): raise CE("CE-EXP-1")
            p.expect(";"); return True
        if v == "ignore":                                        # STM-24
            p.take(); e = p_postfix(p, False); p.expect(";")
            if e[0] != "call": raise CE("CE-OUT-4")
            t = self.synth(e, L)
            if not (isinstance(t, tuple) and t[0] == "outcome"): raise CE("CE-OUT-4")
            return True
        if v in ("break", "continue"):
            p.take(); p.expect(";")
            if not loops: raise CE("CE-STM-3")
            if v == "break": loops[-1]["broken"] = True
            return False
        if v == "require":
            p.take(); c = p_expr(p); p.expect("else"); op = p_expr(p); p.expect(";")
            if not (op[0] == "field" and op[1][0] == "name" and op[1][1] in self.errors): raise CE("CE-STM-7")
            self.check(c, "bool", L); return True
        if v in ("if", "while"):
            p.take(); cond = p_expr(p, nostruct=True)
            save = p.i; self._skip_block(p); p.i = save
            self.check(cond, "bool", L)
            if v == "while":
                frame = {"broken": False}
                self.sblock(p, L, ret, ro, loops + [frame])
                is_true = cond == ("bool", True)   # only the literal `true` (STM-20)
                return (not is_true) or frame["broken"]
            any_completes = self.sblock(p, L, ret, ro, loops); has_else = False
            while p.peek() == "else":
                p.take()
                if p.peek() == "if":
                    p.take(); c2 = p_expr(p, nostruct=True)
                    save2 = p.i; self._skip_block(p); p.i = save2; self.check(c2, "bool", L)
                    any_completes = self.sblock(p, L, ret, ro, loops) or any_completes
                else:
                    any_completes = self.sblock(p, L, ret, ro, loops) or any_completes; has_else = True
            return any_completes or not has_else
        if v == "for":
            p.take(); name = p.take(); p.expect(":"); t = self.cp.resolve_type(expcheck.p_type(p))
            if t not in INT: raise CE("CE-STM-6")
            p.expect("in"); self.check(p_expr(p, True), t, L); p.expect(".."); self.check(p_expr(p, True), t, L)
            L2 = dict(L); L2[name] = t
            self.sblock(p, L2, ret, ro | {name}, loops + [{"broken": False}]); return True
        if v == "match":
            p.take(); st = self.synth(p_expr(p, nostruct=True), L); p.expect("{")
            is_enum = isinstance(st, str) and st in self.enums
            is_outcome = isinstance(st, tuple) and st[0] == "outcome"
            if not (is_enum or is_outcome): raise CE("CE-STM-4")
            seen = []; any_completes = False
            while p.peek() != "}":
                L2 = dict(L); ro2 = set(ro)
                if p.peek() == "_":
                    p.take()
                    if is_enum: raise CE("CE-STM-4")
                elif p.peek() == "Ok":
                    if is_enum: raise CE("CE-STM-4")
                    p.take(); p.expect("(")
                    if p.peek() != ")":
                        b = p.take()
                        if b != "_": L2[b] = st[1]; ro2.add(b)
                    p.expect(")")
                elif p.peek() == "Err":
                    if is_enum: raise CE("CE-STM-4")
                    p.take(); p.expect("(")
                    while p.peek() != ")": p.take()
                    p.expect(")")
                else:
                    owner = p.take(); p.expect("."); var = p.take()
                    if is_outcome or owner != st or var not in self.enums[st] or var in seen: raise CE("CE-STM-4")
                    seen.append(var)
                p.expect("=>")
                any_completes = self.sblock(p, L2, ret, ro2, loops) or any_completes
            p.expect("}")
            if is_enum and set(seen) != self.enums[st]: raise CE("CE-STM-4")
            return any_completes
        if v == "wipe":                                  # STM-23
            p.take(); e = p_expr(p); p.expect(";")
            if e[0] == "slice": self.slice_place(e, L, ro)
            else: self.place(e, L, ro); self.synth(e, L)
            return True
        # assignment or expression statement
        e = p_expr(p)
        if p.peek() == "=" and e[0] == "slice":           # FUN-24, checked by funcheck
            p.take(); self.slice_assign(e, p, L, ro); return True
        if p.peek() in ("+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="):                                         # STM-25
            op = p.take()[:-1]
            if e[0] == "slice": raise CE("CE-STM-2")
            self.place(e, L, ro); dt = self.synth(e, L)
            if self.synth(("bin", op, e, p_expr(p)), L) != dt: raise CE("CE-EXP-1")
            p.expect(";"); return True
        if p.peek() == "=":
            p.take(); self.place(e, L, ro); dt = self.synth(e, L)
            self.check(p_expr(p), dt, L); p.expect(";"); return True
        if p.peek() == ";":
            raise CE("CE-STM-1")
        raise CE("CE-SYN-1")

    def _last_bool_true(self, p, cond_end):
        # the condition token just before the block start is the literal `true`
        return p.t[cond_end - 1][1] == "true"

def run(toks):
    StmChecker(toks).run()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/stm-*"
    for t in sorted((layout.at(repo).conformance).glob(glob)):
        files = project.program_files(t)
        toks = sum((lex(f.read_bytes()) for f in files), [])
        exp = header(files[0].read_bytes())["expect"]
        try:
            run(toks); got = "ok"
        except (CE, consteval.CE) as e:
            got = "compile-error " + str(e)
        st = "PASS" if got == exp else "FAIL"; ok &= st == "PASS"
        print(st, t.name, "| expect", exp, "| checker", got)
    print("ALL PASS" if ok else "FAILURES")
