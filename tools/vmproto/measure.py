"""Measurements of the prototype compiler and VM (VM5 stage 5; vm/decisions.md V-12 item 4).

Static: image, code and constant sizes per program; per-function code and frames; opcode frequencies by count and
by bytes; operand widths; frequent instruction sequences. Dynamic: executed opcode frequencies, the deepest stack
actually used against the compiler's stack need, and the budget used per entry, over the runtime tests and the
FIDO2 session. Prints a JSON document. Usage:
    python -I tools/vmproto/measure.py . > measurements.json
"""
import sys, pathlib, json, collections, io, contextlib
HERE = pathlib.Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "checkers", HERE.parent / "harness", HERE.parent / "fido"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
import compiler, typer, isa, disasm, vm, backends, scenario
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "checkers"))   # find layout
import layout

def instructions(image):
    h, funcs, _, names = disasm.read_image(image)
    code = image[h["code_offset"]:h["code_offset"] + h["code_size"]]
    bounds = [f["code"] for f in funcs] + [len(code)]
    for i in range(len(funcs)):
        pc = bounds[i]
        while pc < bounds[i + 1]:
            name, ops, size = isa.decode(code, pc); yield names[i], pc, name, ops, size; pc += size

def static(repo):
    progs = {}; count = collections.Counter(); nbytes = collections.Counter()
    seq3 = collections.Counter(); seq5 = collections.Counter(); widths = collections.Counter()
    fido = None
    for name, toks in typer.programs(repo):
        c = compiler.Compiler(toks); img = c.compile()
        progs[name] = {k: c.report[k] for k in ("image", "code", "const", "stack_need", "persistent", "session")}
        ins = list(instructions(img))
        if name == "examples/fido2": fido = (c, ins)
        names = [n for _, _, n, _, _ in ins]
        for _, _, n, ops, size in ins:
            count[n] += 1; nbytes[n] += size
            if n in ("LDF", "STF"): widths["frame offset < 256" if ops[1] < 256 else "frame offset >= 256"] += 1
            if n in ("ADDR",): widths["ADDR offset < 256" if ops[1] < 256 else "ADDR offset >= 256"] += 1
            if n in ("PUSH.B", "PUSH.H", "PUSH.W"): widths[n] += 1
            if n in ("JMP", "JZ", "JNZ", "JERR"): widths["jump within ±127" if -128 <= ops[-1] < 128 else "jump beyond ±127"] += 1
        for k in range(len(names) - 2): seq3[" ".join(names[k:k + 3])] += 1
        for k in range(len(names) - 4): seq5[" ".join(names[k:k + 5])] += 1
    c, ins = fido
    fcount = collections.Counter(n for _, _, n, _, _ in ins); fbytes = collections.Counter()
    for _, _, n, _, size in ins: fbytes[n] += size
    idiom = 0; names = [n for _, _, n, _, _ in ins]
    for k in range(len(names) - 4):
        if names[k:k + 5] == ["LDF", "LDF", "LDF", "LDF", "SLICE"]: idiom += 1
    return {"programs": progs, "opcodes": dict(count.most_common()), "opcode_bytes": dict(nbytes.most_common()),
            "operand_widths": dict(widths), "seq3": dict(seq3.most_common(15)), "seq5": dict(seq5.most_common(10)),
            "fido2": {"report": c.report, "opcodes": dict(fcount.most_common()), "opcode_bytes": dict(fbytes.most_common()),
                      "instructions": len(ins), "slice_to_end_idiom": idiom}}

class Probe:
    """Wraps vm.step to count executed opcodes and the deepest stack position; records budget per entry."""
    def __init__(self):
        self.count = collections.Counter(); self.max_sp = 0; self.budget = []; self.orig = vm.step; self.orig_entry = vm.entry
    def __enter__(self):
        probe = self
        def step(ctx, name, ops, next_pc, natives):
            probe.count[name] += 1; r = probe.orig(ctx, name, ops, next_pc, natives)
            probe.max_sp = max(probe.max_sp, ctx.sp); return r
        def entry(ctx, findex, cells, natives):
            r = probe.orig_entry(ctx, findex, cells, natives)
            probe.budget.append(ctx.budget_cfg - (ctx.budget or 0)); return r
        vm.step, vm.entry = step, entry; return self
    def __exit__(self, *a): vm.step, vm.entry = self.orig, self.orig_entry

def dynamic(repo):
    out = {}
    with Probe() as p:
        per_test = {}
        for d in sorted((layout.at(repo).runtime).glob("run-*")):
            p.max_sp = 0
            card = backends.build("vmproto", scenario.program_files(d))
            assert scenario.run_scenario(card, (d / "scenario.txt").read_text(encoding="utf-8")) is None
            per_test[d.name] = {"stack_need": card.stack_need, "deepest": p.max_sp}
        out["runtime"] = {"executed": dict(p.count.most_common()), "stack": per_test,
                          "max_budget_used": max(b for b in p.budget if b < 10**6 - 1)}
    with Probe() as p:
        sys.argv = ["check_fido2.py", str(repo), "--backend", "vmproto"]
        import check_fido2
        check_fido2.BACKEND = "vmproto"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): check_fido2.main()
        assert "ALL PASS" in buf.getvalue()
        out["fido2"] = {"executed": dict(p.count.most_common()), "total": sum(p.count.values()),
                        "deepest": p.max_sp, "entries": len(p.budget), "max_budget_used": max(p.budget)}
    out["context_bytes"] = vm.Ctx.size(); out["context_fields"] = vm.Ctx.SIZES
    return out

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1]).resolve()
    print(json.dumps({"static": static(repo), "dynamic": dynamic(repo)}, indent=1))
