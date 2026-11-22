"""Checks of the images' debug information (TL1 step 4; vm/image-format.md IMG-10), run by tools/run_checks.py.

1. Debug information never changes the code: with it on and off, every program's functions, imports, constants
   and code are byte-identical.
2. Every statement of every program has a line-table row, unless it is unreachable and emits no code (V-35).
   Every row names one of the program's files, at a line that exists.
3. Every image's debug section decodes completely, and every variable's scope lies inside its function's code.
4. The sample tools/lsp/testdata/semantic-sample.card has exactly its declared parameters and locals, with their
   types, and a breakpoint offset for each statement line.
5. Traps report their statement: run-001's overflow and underflow, on lines 16 and 20.
Usage: uv run python -I tools/vmproto/debug_check.py .
"""
import sys, pathlib, hashlib
HERE = pathlib.Path(__file__).resolve().parent
for d in (HERE, HERE.parent / "harness"):
    if str(d) not in sys.path: sys.path.insert(0, str(d))
import compiler, typer, disasm, debuginfo, backends, scenario
from cardlang import layout

def body(img):
    h, _, _, _ = disasm.read_image(img)
    return hashlib.sha256(img[72:h["debug_offset"] or len(img)]).hexdigest()

def main(repo):
    ok = True
    def check(name, passed, detail=""):
        nonlocal ok
        ok &= bool(passed); print("PASS" if passed else "FAIL", name, "|", detail)
    same = missing = bad_rows = bad_scopes = decoded = statements = 0
    for name, toks in typer.programs(repo):
        c = compiler.Compiler(toks); c.compile(); img = c.image
        plain = compiler.Compiler(toks); plain.debug = False; plain.compile()
        same += body(img) == body(plain.image)
        info = debuginfo.DebugInfo.of(img); decoded += 1
        rows = {(info.files[f], line) for _, f, line in info.lines}
        for g in c.gens.values():
            unreachable = set((p[0], p[1]) for p in g.unreachable)
            def walk(stmts):
                nonlocal missing, statements
                for s in stmts:
                    if not hasattr(s, "pos"): continue
                    statements += 1
                    if (s.pos[0], s.pos[1]) not in rows and (s.pos[0], s.pos[1]) not in unreachable: missing += 1
                    for part in s[1:]:
                        if isinstance(part, list): walk(part)
                        elif isinstance(part, tuple) and part and isinstance(part[0], tuple):
                            for x in part:
                                if isinstance(x, tuple) and len(x) == 2 and isinstance(x[1], list): walk(x[1])
                    if s[0] == "if":
                        for _, b in s[1]: walk(b)
                        if s[2]: walk(s[2])
                    if s[0] == "match":
                        for _, b in s[2]: walk(b)
            walk(c.typed.bodies[g.name])
        for _, f, line in info.lines:
            path = info.files[f]
            try: n = len(pathlib.Path(path).read_text(encoding="utf-8").splitlines())
            except OSError: n = -1
            if path == "<scaffold>": continue
            if not 1 <= line <= n: bad_rows += 1
        h, funcs, _, _ = disasm.read_image(img)
        bounds = [fn["code"] for fn in funcs] + [h["code_size"]]
        for v in info.vars:
            if not (bounds[v["function"]] <= v["start"] <= v["end"] <= bounds[v["function"] + 1]): bad_scopes += 1
    total = decoded
    check("debug information never changes the code", same == total, f"{same} of {total} programs identical")
    check("every reachable statement has a line-table row", missing == 0, f"{statements} statements, {missing} without a row")
    check("every row names an existing line of a program file", bad_rows == 0, f"{bad_rows} bad rows")
    check("every debug section decodes; scopes lie inside their functions", bad_scopes == 0, f"{decoded} images, {bad_scopes} bad scopes")
    sample = layout.at(repo).tools / "lsp" / "testdata" / "semantic-sample.card"
    c = compiler.compile_files([sample]); info = debuginfo.DebugInfo.of(c.image)
    got = sorted((info.functions[v["function"]], v["name"], info.type_name(v["type"]), v["kind"], v["param"]) for v in info.vars)
    want = sorted([("add", "values", "u8[]", "view", True), ("add", "extra", "u32", "frame", True),
                   ("add", "sum", "u32", "frame", False), ("add", "index", "u32", "frame", False),
                   ("add", "value", "u32", "frame", False),
                   ("process", "request", "u8[]", "view", True), ("process", "response", "u8[]", "view", True),
                   ("process", "pair", "Pair", "frame", False), ("process", "digest", "u32", "frame", False)])
    check("the sample's parameters and locals", got == want, str([x for x in got if x not in want] + [x for x in want if x not in got]))
    lines = [22, 23, 24, 25, 27, 31, 32, 33, 34, 35]
    check("a breakpoint offset for each statement line of the sample", all(info.offsets(str(sample), l) for l in lines),
          str([l for l in lines if not info.offsets(str(sample), l)]))
    globs = sorted((g["name"], g["kind"], info.type_name(g["type"])) for g in info.globals)
    check("the sample's globals", globs == [("LIMIT", "const-scalar", "u32"), ("mode", "session", "Mode"), ("total", "persistent", "u32")], str(globs))
    run = layout.at(repo).runtime / "run-001-integer-traps"
    card = backends.build("vmproto", scenario.program_files(run))
    card.install(); card.session_start()
    positions = []
    for req in ([1, 0xFF], [2, 0]):
        r = card.command(req, 8); p = card.trap_position()
        positions.append((r, (pathlib.Path(p[0]).name, p[1]) if p else None))
    check("traps report their statement", positions == [(("trap", "OVERFLOW"), ("program.card", 16)), (("trap", "UNDERFLOW"), ("program.card", 20))],
          str(positions))
    print("ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(pathlib.Path(sys.argv[1]).resolve()) else 1)
