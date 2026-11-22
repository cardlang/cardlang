"""Checks of tools/clc.py (TL1 step 2), run by tools/run_checks.py.

Each check runs clc as a subprocess, as the extension will, and looks at its exit status and output.
Usage: uv run python -I tools/clc_check.py .
"""
import sys, subprocess, pathlib, tempfile, json, shutil
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0] / "checkers"))   # find layout
import layout

def clc(repo, *args):
    r = subprocess.run([sys.executable, "-I", str(layout.at(repo).tools / "clc.py"), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=repo)
    return r.returncode, r.stdout + r.stderr

def main(repo):
    ok = True
    def check(name, passed, detail=""):
        nonlocal ok
        ok &= passed; print("PASS" if passed else "FAIL", name, "|", detail.strip().splitlines()[-1] if detail.strip() else "")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for app in ("fido2", "piv"):
            rc, out = clc(repo, "check", f"examples/{app}"); check(f"check examples/{app}", rc == 0 and "ok" in out, out)
            rc, out = clc(repo, "build", f"examples/{app}", "-o", str(tmp / f"{app}.clvm"), "--json")
            info = json.loads(out) if rc == 0 else {}
            check(f"build examples/{app}", rc == 0 and (tmp / f"{app}.clvm").stat().st_size == info.get("image"), out)
            rc, out = clc(repo, "disasm", str(tmp / f"{app}.clvm")); check(f"disasm {app}.clvm", rc == 0 and "function 0" in out, out)
        bad = "conformance/invalid/exp-105-mixed-arithmetic.card"
        rc, out = clc(repo, "check", bad, "--fragment", "--json")
        d = json.loads(out)[0] if rc == 1 else {}
        check("check reports an error with its position", rc == 1 and d.get("code") == "CE-EXP-4" and d.get("line") == 8, out)
        cex = "conformance/invalid/cex-105-overflow.card"                    # the compiler alone accepts it (T1)
        rc, out = clc(repo, "build", cex, "--fragment", "-o", str(tmp / "cex.clvm"))
        check("build refuses what the compiler alone accepts", rc == 1 and "CE-CEX-3" in out and not (tmp / "cex.clvm").exists(), out)
        sc = repo / "conformance/runtime/run-020-crypto/scenario.txt"
        for backend in ("interp", "vmproto", "cvm-clang"):
            rc, out = clc(repo, "run", str(sc), "--backend", backend); check(f"run run-020 on {backend}", rc == 0 and "passed" in out, out)
        wrong = tmp / "wrong"; shutil.copytree(sc.parent, wrong)
        text = (wrong / "scenario.txt").read_text(encoding="utf-8").replace("expect ok ba 78 16 bf", "expect ok ba 78 16 be", 1)
        (wrong / "scenario.txt").write_text(text, encoding="utf-8")
        rc, out = clc(repo, "run", str(wrong / "scenario.txt"))
        check("run reports a failed expectation", rc == 1 and "FAIL expect" in out and "FAILED" in out, out)
    print("ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(pathlib.Path(sys.argv[1]).resolve()) else 1)
