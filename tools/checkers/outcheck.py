"""Reference checker for spec chapter 9 (OUT-1..OUT-20), built on funcheck."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header
import funcheck, expcheck, consteval
from expcheck import CE, P, p_expr, p_postfix

CARD_ERROR = {"Overflow", "Underflow", "DivisionByZero", "ConversionRange", "AlreadyExists", "NotFound", "WrongResourceType", "Capacity"}

class OutChecker(funcheck.FunChecker):
    def __init__(self, toks):
        super().__init__(toks)
        self.check_error_sets(toks)
        self.errors["CardError"] = set(CARD_ERROR)
        self._bindings = set()

    def check_error_sets(self, toks):
        sets = 0; i = 0
        while i < len(toks):
            if toks[i][1] == "errors" and (i == 0 or toks[i-1][1] in ("}", ";")):
                sets += 1
                if sets > 1: raise CE("CE-OUT-7")
                j = i + 3; codes = set(); members = 0
                while toks[j][1] != "}":
                    members += 1
                    val = toks[j+2]
                    if toks[j+3][1] != ";" or val[0] != "int": raise CE("CE-OUT-7")
                    code = consteval.primary(consteval.P([val]))[1]
                    if code > 65535: raise CE("CE-EXP-2")
                    if code == 0 or code in codes: raise CE("CE-OUT-7")
                    codes.add(code); j += 4
                if members == 0: raise CE("CE-OUT-7")
                i = j
            i += 1

    def app_member(self, e):
        return (e[0] == "field" and e[1][0] == "name" and e[1][1] in self.errors and e[1][1] != "CardError"
                and e[2] in self.errors[e[1][1]])

    def synth(self, e, L, value=True):
        if e[0] == "name" and e[1] in self._bindings: raise CE("CE-OUT-6")
        if e[0] == "attempt":
            if len(e) == 3 and not self.app_member(e[2]): raise CE("CE-OUT-3")     # OUT-22
            if e[1][0] != "call": raise CE("CE-OUT-4")
            t = self.synth(e[1], L)
            if not (isinstance(t, tuple) and t[0] == "outcome"): raise CE("CE-OUT-4")
            if t[1] == "none": raise CE("CE-OUT-4")
            return t[1]
        return super().synth(e, L, value)

    def sstmt(self, p, L, ret, ro, loops):
        self._ro = frozenset(ro)
        v = p.peek()
        if v == "return":
            p.take()
            if p.peek() == "Ok":
                p.take(); p.expect("(")
                if p.peek() == ")":
                    p.take()
                    if ret != "none": raise CE("CE-OUT-2")
                else:
                    if ret == "none": raise CE("CE-OUT-2")
                    self.check(p_expr(p), ret, L); p.expect(")")
            elif p.peek() == "Err":
                p.take(); p.expect("("); x = p_expr(p); p.expect(")")
                if not (self.app_member(x) or (x[0] == "name" and x[1] in self._bindings)): raise CE("CE-OUT-3")
            else:
                e = p_expr(p)
                if e[0] != "call": raise CE("CE-OUT-2")
                t = self.synth(e, L)
                if t != ("outcome", ret): raise CE("CE-OUT-2")
            p.expect(";"); return False
        if v == "attempt":
            p.take(); e = p_postfix(p, False)
            if p.peek() == "else":
                p.take()
                if not self.app_member(p_postfix(p, False)): raise CE("CE-OUT-3")      # OUT-22
            if e[0] != "call": raise CE("CE-OUT-4")
            t = self.synth(e, L)
            if not (isinstance(t, tuple) and t[0] == "outcome") or t[1] != "none": raise CE("CE-OUT-4")
            p.expect(";"); return True
        if v == "require":
            save = p.i; p.take(); p_expr(p); p.expect("else"); op = p_expr(p)
            if op[0] == "field" and op[1][0] == "name" and op[1][1] == "CardError": raise CE("CE-OUT-3")
            p.i = save
            return super().sstmt(p, L, ret, ro, loops)
        if v == "match":
            save = p.i; p.take(); st = self.synth(p_expr(p, nostruct=True), L)
            if not (isinstance(st, tuple) and st[0] == "outcome"):
                p.i = save; return super().sstmt(p, L, ret, ro, loops)
            return self.outcome_match(p, st[1], L, ret, ro, loops)
        if v not in ("var", "if", "while", "for", "break", "continue", "{", "wipe", "ignore") and v not in ("persistent", "session", "const"):
            save = p.i; e = p_expr(p)
            if p.peek() == ";" and e[0] == "call":
                t = self.synth(e, L)
                if isinstance(t, tuple) and t[0] == "outcome": raise CE("CE-OUT-1")
            p.i = save
        return super().sstmt(p, L, ret, ro, loops)

    def outcome_match(self, p, payload, L, ret, ro, loops):
        p.expect("{")
        ok_arms = 0; specifics = set(); catch_all = False; any_completes = False
        while p.peek() != "}":
            if catch_all: raise CE("CE-OUT-5")       # any arm after the catch-all
            L2 = dict(L); ro2 = set(ro); binding = None
            if p.peek() == "Ok":
                p.take(); p.expect("(")
                ok_arms += 1
                if ok_arms > 1: raise CE("CE-OUT-5")
                if p.peek() == ")":
                    if payload != "none": raise CE("CE-OUT-5")
                else:
                    if payload == "none": raise CE("CE-OUT-5")
                    b = p.take()
                    if p.peek() != ")": raise CE("CE-SYN-1")    # nested pattern such as Ok(State.Idle)
                    if b != "_": L2[b] = payload; ro2.add(b)
                p.expect(")")
            elif p.peek() == "Err":
                p.take(); p.expect("(")
                if p.peek(1) == "(":                                  # Err(Set(code)), OUT-21
                    owner = p.take(); p.take(); b = p.take(); p.expect(")")
                    if owner not in self.errors: raise CE("CE-NAM-2")
                    if owner == "CardError" or ("set", owner) in specifics: raise CE("CE-OUT-5")
                    specifics.add(("set", owner))
                    if b != "_": L2[b] = "u16"; ro2.add(b)
                elif p.peek(1) == ".":
                    owner = p.take(); p.take(); member = p.take()
                    if owner not in self.errors: raise CE("CE-NAM-2")
                    if member not in self.errors[owner]: raise CE("CE-NAM-9")
                    if (owner, member) in specifics or ("set", owner) in specifics: raise CE("CE-OUT-5")
                    specifics.add((owner, member))
                else:
                    b = p.take(); catch_all = True
                    if b != "_": binding = b
                p.expect(")")
            else:
                raise CE("CE-OUT-5")
            p.expect("=>")
            saved = self._bindings
            if binding: self._bindings = saved | {binding}
            try:
                any_completes = self.sblock(p, L2, ret, ro2, loops) or any_completes
            finally:
                self._bindings = saved
        p.expect("}")
        if ok_arms != 1 or not catch_all: raise CE("CE-OUT-5")
        return any_completes

def run(toks):
    OutChecker(toks).run()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/out-*"
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
