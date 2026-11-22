"""Every example applet's scenarios pass, run by tests/run_checks.py.

Runs each `examples/*/*.scenario` through `clc run`, as the editor's Run Scenario does, on one backend, and prints
PASS or FAIL for each. A scenario's program is its own folder, with its `cardlang.json`.
Usage: uv run python -I tests/example_scenarios.py . [--backend NAME]      (default: interp)
"""
import sys, pathlib, subprocess
from cardlang import layout

def main(argv):
    backend = "interp"
    if "--backend" in argv:
        i = argv.index("--backend"); backend = argv[i + 1]; del argv[i:i + 2]
    L = layout.at(argv[0] if argv else None)
    scenarios = sorted(L.examples.glob("*/*.scenario"))
    ok = bool(scenarios)
    if not scenarios: print("FAIL no example scenarios found")
    for sc in scenarios:
        r = subprocess.run([sys.executable, "-I", "-m", "cardlang.cli", "run", str(sc), "--backend", backend],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        name = sc.relative_to(L.root).as_posix()
        out = (r.stdout + r.stderr).strip().splitlines()
        if r.returncode == 0: print(f"PASS {name}")
        else: ok = False; print(f"FAIL {name} | {out[-1] if out else 'no output'}")
    print("ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1:]) else 1)
