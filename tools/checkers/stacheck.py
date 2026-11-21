"""Reference checker for spec chapter 10 (STA-1..STA-14), built on outcheck."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lexcheck import lex, header
import srcpos
import outcheck, expcheck, consteval
from expcheck import CE

HANDLERS = {"on_install", "on_session_start"}   # placeholders, D-438

class StaChecker(outcheck.OutChecker):
    def run(self):
        for name, (_, init) in self.cp.globals.items():
            if init is not None: raise srcpos.at(CE("CE-STA-1"), srcpos.decl(name))   # STA-2
        for group in (self.consts, self.globals, self.structs, self.enums, self.errors):
            if HANDLERS & set(group):                                       # STA-8
                raise srcpos.at(CE("CE-NAM-5"), srcpos.decl(sorted(HANDLERS & set(group))[0]))
        for name in HANDLERS & set(self.funcs):
            params, ret, _ = self.funcs[name]
            if params or ret != "none": raise srcpos.at(CE("CE-STA-2"), srcpos.decl(name))   # STA-7
        for name, (_, _, body) in self.funcs.items():
            for i, (k, v) in enumerate(body):
                if v in HANDLERS and i + 1 < len(body) and body[i+1][1] == "(":
                    raise srcpos.at(CE("CE-STA-3"), body[i])                # STA-9
        super().run()

def run(toks):
    StaChecker(toks).run()

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True; glob = sys.argv[2] if len(sys.argv) > 2 else "*/sta-*"
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
