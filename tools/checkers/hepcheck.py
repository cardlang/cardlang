"""Reference checker for spec chapter 12 (HEP-1..HEP-16), built on txncheck.

Fragment tests (kind: fragment) are completed with the HEP-16 scaffold before checking;
application tests (kind: application) are checked as written.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header
import txncheck, expcheck, consteval
import srcpos
from expcheck import CE

SCAFFOLD = b"command scaffold_entry(request: ref u8[], response: inout u8[]) -> u32 {\n    return Ok(0);\n}\n"
U8_VIEW = ("arr", "u8", None)

class HepChecker(txncheck.TxnChecker):
    def __init__(self, toks):
        depth = 0; self._commands = []
        for i, (_, v) in enumerate(toks):
            if v == "{": depth += 1
            elif v == "}": depth -= 1
            elif v == "command" and depth == 0: self._commands.append(toks[i + 1][1])
        super().__init__(toks)

    def run(self):
        if not self._commands: raise CE("CE-HEP-1")                              # HEP-1
        if len(self._commands) > 1: raise srcpos.at(CE("CE-HEP-2"), srcpos.decl(self._commands[1]))
        params, ret, _ = self.funcs[self._commands[0]]
        shape = [(mode, t) for _, mode, t in params]
        if shape != [("ref", U8_VIEW), ("inout", U8_VIEW)] or ret != "u32":       # HEP-2
            raise srcpos.at(CE("CE-HEP-3"), srcpos.decl(self._commands[0]))
        super().run()

    def call(self, e, L, T):
        target = e[1]
        if target[0] == "name" and target[1] in self._commands: raise CE("CE-EXP-15")   # HEP-3
        return super().call(e, L, T)

def run(toks, kind="fragment"):
    if kind == "fragment":
        toks = toks + lex(SCAFFOLD)
    HepChecker(toks).run()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/hep-*"
    for t in sorted((repo / "conformance").glob(glob)):
        files = [t / f for f in (t / "files.txt").read_text().split()] if t.is_dir() else [t]
        toks = sum((lex(f.read_bytes()) for f in files), [])
        meta = header(files[0].read_bytes()); exp = meta["expect"]
        try:
            run(toks, meta.get("kind", "fragment")); got = "ok"
        except (CE, consteval.CE) as e:
            got = "compile-error " + str(e)
        st = "PASS" if got == exp else "FAIL"; ok &= st == "PASS"
        print(st, t.name, "| expect", exp, "| checker", got)
    print("ALL PASS" if ok else "FAILURES")
