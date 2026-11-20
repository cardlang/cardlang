"""V-31: the prototype VM keeps all of its own mutable state in its context (vm.Ctx), and nowhere else.

Checks, while every runtime scenario runs on the vmproto backend:
1. Ctx has __slots__ only (no per-instance dictionary), so no field can be added at run time;
2. no module-level value of vm.py changes (the interpreter has no global state);
3. the native library holds only its operation table (the resource area of cl_config, HAL-27) besides its references
   to the HAL and to the current context;
and reports the context's size against the 1 KiB bound (V-2, VEX-50). Usage:
    python -I tools/vmproto/check_state.py .
"""
import sys, pathlib, copy, types
HERE = pathlib.Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "checkers", HERE.parent / "harness"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
import vm, backends, scenario

def module_state(mod):
    return {k: copy.deepcopy(v) for k, v in vars(mod).items()
            if not k.startswith("__") and not isinstance(v, (types.ModuleType, types.FunctionType, type))}

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]); ok = True
    def report(name, good, detail=""):
        global ok
        ok &= good; print("PASS" if good else "FAIL", name, "" if good else "| " + detail)
    report("context has slots only", not hasattr(vm.Ctx(), "__dict__"))
    before = module_state(vm); extra = set()
    for d in sorted((repo / "conformance" / "runtime").glob("run-*")):
        card = backends.build("vmproto", scenario.program_files(d))
        scenario.run_scenario(card, (d / "scenario.txt").read_text(encoding="utf-8"))
        extra |= set(vars(card.natives)) - {"hal", "ops", "ctx"}
    after = module_state(vm)
    report("vm.py keeps no global state", before == after, str({k for k in before if before[k] != after.get(k)}))
    report("native library holds only its operation table", not extra, str(extra))
    size = vm.Ctx.size()
    report(f"context is {size} bytes, within 1 KiB (V-2)", size <= 1024, str(size))
    print("ALL PASS" if ok else "FAILURES")
