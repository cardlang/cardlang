"""clc — the CardLang command line (TL1 step 2): the one front end that the VS Code extension and a terminal share.

    uv run python -I tools/clc.py check  <program> [--json] [--binding iso7816|raw] [--fragment]
    uv run python -I tools/clc.py build  <program> [-o out.clvm] [--json] [--binding ...]
    uv run python -I tools/clc.py disasm <program | image.clvm>
    uv run python -I tools/clc.py run    <scenario.txt> [--program <program>] [--backend interp|vmproto|cvm-msvc|cvm-clang]

A <program> is any of:
- a directory with a `cardlang.json` project file: {"name": ..., "files": [...], "binding": "iso7816" | "raw"};
- a directory without one: its `.card` files, in name order;
- one or more `.card` files.

check runs the full front end (tools/checkers/diagnose.py) and prints each diagnostic as
`file:line:column: CE-XXX-n: message`, or a JSON list with --json. Exit status 1 if there are diagnostics.
build checks first (the compiler alone skips some rules, TL1 finding T1), then compiles to an image, written to
`-o`, or to `build/<name>.clvm` in the program's directory. It prints the image's figures.
run runs a scenario file (tools/harness/README.md), printing every step and its outcome; its program is
--program, or else the scenario's own directory.
"""
import sys, json, pathlib, argparse
TOOLS = pathlib.Path(__file__).resolve().parent
for d in ("checkers", "vmproto", "harness", "interp"):
    p = str(TOOLS / d)
    if p not in sys.path: sys.path.insert(0, p)
import diagnose
from lexcheck import header

class Program:
    """The files of a program, its binding and its name, from the command line's <program>."""
    def __init__(self, paths, binding=None, fragment=False):
        paths = [pathlib.Path(p) for p in paths]
        self.binding, self.name = binding, None
        if len(paths) == 1 and paths[0].is_dir():
            d = paths[0]; self.dir = d
            project = d / "cardlang.json"
            if project.exists():
                meta = json.loads(project.read_text(encoding="utf-8"))
                self.files = [d / f for f in meta["files"]]; self.name = meta.get("name")
                self.binding = self.binding or meta.get("binding")
            else:
                self.files = sorted(d.glob("*.card"))
            self.name = self.name or d.name
        else:
            self.files = paths; self.dir = paths[0].parent if paths else pathlib.Path(".")
            self.name = paths[0].stem if paths else "program"
        if not self.files: raise SystemExit("clc: no .card files")
        meta = header(self.files[0].read_bytes())
        self.binding = self.binding or meta.get("binding")
        self.kind = "fragment" if fragment or meta.get("kind") == "fragment" else "application"

def program_arg(ap):
    ap.add_argument("program", nargs="+", help="a project directory, or .card files")
    ap.add_argument("--binding", choices=["iso7816", "raw"])
    ap.add_argument("--fragment", action="store_true", help="check as a fragment (with the HEP-16 scaffold)")

def diagnostics(prog):
    return diagnose.check(prog.files, prog.binding, prog.kind)

def print_diagnostics(ds, as_json):
    if as_json: print(json.dumps(ds, indent=1))
    else:
        for d in ds: print(diagnose.format_diagnostic(d))

def cmd_check(a):
    prog = Program(a.program, a.binding, a.fragment); ds = diagnostics(prog)
    print_diagnostics(ds, a.json)
    if not ds and not a.json: print(f"{prog.name}: ok, {len(prog.files)} file(s)")
    return 1 if ds else 0

def compile_program(prog):
    import compiler
    return compiler.compile_files(prog.files, prog.binding, prog.kind == "fragment")

def cmd_build(a):
    prog = Program(a.program, a.binding, a.fragment); ds = diagnostics(prog)
    if ds: print_diagnostics(ds, a.json); return 1
    c = compile_program(prog)
    out = pathlib.Path(a.output) if a.output else prog.dir / "build" / f"{prog.name}.clvm"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(c.image)
    r = c.report
    summary = {"output": str(out), "image": r["image"], "code": r["code"], "const": r["const"],
               "stack_need": r["stack_need"], "persistent": r["persistent"], "session": r["session"],
               "functions": len(r["functions"]), "natives": len(r["natives"])}
    if a.json: print(json.dumps(summary, indent=1))
    else:
        print(f"{prog.name}: {out}: image {r['image']} bytes (code {r['code']}, constants {r['const']}), "
              f"{len(r['functions'])} functions; stack {r['stack_need']}, persistent {r['persistent']}, "
              f"session {r['session']} bytes")
    return 0

def cmd_disasm(a):
    import disasm
    src = pathlib.Path(a.program[0])
    if len(a.program) == 1 and src.is_file() and src.suffix in (".clvm", ".bin"): img = src.read_bytes()
    else:
        prog = Program(a.program, a.binding, a.fragment); ds = diagnostics(prog)
        if ds: print_diagnostics(ds, False); return 1
        img = compile_program(prog).image
    print(disasm.listing(img)); return 0

def describe(outcome):
    if outcome is None: return ""
    if outcome[0] == "ok": return "ok " + " ".join(f"{b:02x}" for b in outcome[1]) if outcome[1] else "ok"
    if outcome[0] == "err": return f"err {outcome[1]} {outcome[2] if isinstance(outcome[2], str) else hex(outcome[2])}"
    if outcome[0] == "trap": return f"trap {outcome[1] or '(application unavailable)'}"
    return " ".join(str(x) for x in outcome)

def cmd_run(a):
    import backends, scenario
    sc = pathlib.Path(a.scenario)
    prog = Program(a.program or [str(sc.parent)], a.binding)
    ds = diagnostics(prog)
    if ds: print_diagnostics(ds, False); return 1
    card = backends.build(a.backend, prog.files, prog.binding)
    def trace(lineno, step, words, outcome):
        if step == "expect":
            _, want, got = outcome; mark = "ok  " if want == got else "FAIL"
            print(f"{sc.name}:{lineno}: {mark} expect {' '.join(words)}" + ("" if want == got else f"  (got {got})"))
        else:
            shown = " ".join(words); res = describe(outcome)
            if outcome and outcome[0] == "trap" and hasattr(card, "trap_position") and card.trap_position():
                f, line = card.trap_position(); res += f" at {pathlib.Path(f).name}:{line}"
            print(f"{sc.name}:{lineno}: {step} {shown[:60]}{'...' if len(shown) > 60 else ''}" + (f"  -> {res}" if res else ""))
    problem = scenario.run_scenario(card, sc.read_text(encoding="utf-8"), trace)
    print(f"{sc.name}: " + ("passed" if problem is None else "FAILED, " + problem) + f" ({a.backend})")
    return 0 if problem is None else 1

def main(argv=None):
    ap = argparse.ArgumentParser(prog="clc", description="The CardLang command line (TL1)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check", help="check a program and report diagnostics"); program_arg(p)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("build", help="check and compile a program to an image"); program_arg(p)
    p.add_argument("-o", "--output"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("disasm", help="list an image's code"); program_arg(p)
    p = sub.add_parser("run", help="run a scenario against a program")
    p.add_argument("scenario"); p.add_argument("--program", nargs="+"); p.add_argument("--binding", choices=["iso7816", "raw"])
    p.add_argument("--backend", default="vmproto", choices=["interp", "vmproto", "cvm-msvc", "cvm-clang"])
    a = ap.parse_args(argv)
    return {"check": cmd_check, "build": cmd_build, "disasm": cmd_disasm, "run": cmd_run}[a.cmd](a)

if __name__ == "__main__":
    try: sys.exit(main())
    except BrokenPipeError: sys.exit(0)                     # output piped into a command that stopped reading
