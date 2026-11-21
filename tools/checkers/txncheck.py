"""Reference checker for spec chapter 11 (TXN-1..TXN-17), built on stacheck."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header
import project
import srcpos
import stacheck, expcheck, consteval
from expcheck import CE, P, p_expr

class TxnChecker(stacheck.StaChecker):
    _txn = None   # loop depth at entry to the active transaction, or None

    def run(self):
        self.check_nesting()
        super().run()

    # TXN-10: structural nesting over the static call graph
    def calls_in(self, toks):
        return {v for i, (k, v) in enumerate(toks)
                if v in self.funcs and i + 1 < len(toks) and toks[i+1][1] == "(" and (i == 0 or toks[i-1][1] != ".")}

    def check_nesting(self):
        memo = {}
        def has_txn(f, seen=()):
            if f in memo: return memo[f]
            body = self.funcs[f][2]
            r = any(v == "transaction" for _, v in body) or any(
                has_txn(g, seen + (f,)) for g in self.calls_in(body) if g not in seen)
            memo[f] = r; return r
        for name, (_, _, body) in self.funcs.items():
            for i, (_, v) in enumerate(body):
                if v != "transaction": continue
                j = i + 1; depth = 0; start = j
                while True:
                    t = body[j][1]
                    if t == "{": depth += 1
                    if t == "}":
                        depth -= 1
                        if depth == 0: break
                    j += 1
                inner = body[start + 1:j]
                nested = next((t for t in inner if t[1] == "transaction"), None)
                if nested is not None: raise srcpos.at(CE("CE-TXN-3"), nested)
                if any(has_txn(g) for g in self.calls_in(inner)): raise srcpos.at(CE("CE-TXN-3"), body[i])

    def sstmt(self, p, L, ret, ro, loops):
        v = p.peek()
        if v == "transaction":
            p.take(); saved = self._txn; self._txn = len(loops)
            try:
                return self.sblock(p, L, ret, ro, loops)
            finally:
                self._txn = saved
        if v == "abort":
            if self._txn is None: raise CE("CE-TXN-2")
            p.take()
            if p.peek() != "Err": raise CE("CE-SYN-1")
            p.take(); p.expect("("); x = p_expr(p); p.expect(")"); p.expect(";")
            if not (self.app_member(x) or (x[0] == "name" and x[1] in self._bindings)): raise CE("CE-OUT-3")
            return False
        if self._txn is not None:
            if v == "return": raise CE("CE-TXN-1")   # attempt and require abort instead (TXN-18)
            if v in ("break", "continue") and len(loops) <= self._txn: raise CE("CE-TXN-1")
        return super().sstmt(p, L, ret, ro, loops)

def run(toks):
    TxnChecker(toks).run()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/txn-*"
    for t in sorted((repo / "conformance").glob(glob)):
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
