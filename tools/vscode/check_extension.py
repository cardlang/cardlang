"""Consistency checks of the VS Code extension's static parts (TL1 step 3), run by tests/run_checks.py.

- Every JSON file of the extension parses.
- The grammar's keywords are exactly the lexer's (src/cardlang/front/lexcheck.py KEYWORDS), and its intrinsics exactly
  the checker's (src/cardlang/front/expcheck.py), so highlighting cannot drift from the language.
- The scenario grammar's steps are exactly those the scenario runner accepts (src/cardlang/harness/scenario.py).
- Every regular expression of both grammars compiles (in Python's syntax, which these patterns share with
  Oniguruma), and the keyword patterns colour every keyword token of both applets.
Usage: uv run python -I tools/vscode/check_extension.py .
"""
import sys, re, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
from cardlang.front import lexcheck, expcheck, project
from cardlang import layout

def patterns(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("match", "begin", "end") and isinstance(v, str): yield v
            else: yield from patterns(v)
    elif isinstance(node, list):
        for v in node: yield from patterns(v)

def words(rx):
    m = re.search(r"\(\?:([A-Za-z_|]+)\)", rx)
    return set(m.group(1).split("|")) if m else set()

def main(repo):
    ok = True
    def check(name, passed, detail=""):
        nonlocal ok
        ok &= bool(passed); print("PASS" if passed else "FAIL", name, "|", detail)
    docs = {}
    for f in sorted(HERE.rglob("*.json")):
        if "node_modules" in f.parts: continue
        try: docs[f.relative_to(HERE).as_posix()] = json.loads(f.read_text(encoding="utf-8")); check(f"{f.relative_to(HERE)} parses", True)
        except ValueError as e: check(f"{f.relative_to(HERE)} parses", False, str(e))
    g = docs.get("syntaxes/cardlang.tmLanguage.json", {})
    kw = set().union(*(words(p["match"]) for p in g["repository"]["keywords"]["patterns"]))
    check("grammar keywords = lexer keywords", kw == lexcheck.KEYWORDS, f"extra {sorted(kw - lexcheck.KEYWORDS)}, missing {sorted(lexcheck.KEYWORDS - kw)}")
    intr = words(g["repository"]["builtins"]["patterns"][1]["match"])
    want = expcheck.CHECKED2 | expcheck.WRAP | expcheck.TYARG | {"checked_neg", "encode_be", "encode_le", "equal", "compare", "fill"}
    check("grammar intrinsics = checker intrinsics", intr == want, f"extra {sorted(intr - want)}, missing {sorted(want - intr)}")
    s = docs.get("syntaxes/cardlang-scenario.tmLanguage.json", {})
    steps = set(re.search(r"\(install\|[^)]*\)", json.dumps(s)).group(0)[1:-1].split("|"))
    from cardlang.harness import scenario
    src = pathlib.Path(scenario.__file__).read_text(encoding="utf-8")
    runner = {w for w in re.findall(r'"([a-z_]+)"', "\n".join(l for l in src.splitlines() if "step ==" in l or "step in" in l))} - {"expect"}
    check("scenario grammar steps = runner steps", steps == runner, f"grammar {sorted(steps)}, runner {sorted(runner)}")
    bad = []
    for name in ("syntaxes/cardlang.tmLanguage.json", "syntaxes/cardlang-scenario.tmLanguage.json"):
        for rx in patterns(docs.get(name, {})):
            try: re.compile(rx)
            except re.error as e: bad.append((name, rx, str(e)))
    check("every grammar pattern compiles", not bad, str(bad[:2]))
    pkg = docs.get("package.json", {}); contrib = pkg.get("contributes", {})
    js = (HERE / "extension.js").read_text(encoding="utf-8")
    cmds = [c["command"] for c in contrib.get("commands", [])]
    unregistered = [c for c in cmds if f'registerCommand("{c}"' not in js]
    check("every contributed command is registered in extension.js", not unregistered, str(unregistered))
    dbg = (contrib.get("debuggers") or [{}])[0]
    check("the debugger contribution", dbg.get("type") == "cardlang" and dbg["configurationAttributes"]["launch"]["required"] == ["scenario"]
          and {b["language"] for b in contrib.get("breakpoints", [])} == {"cardlang", "cardlang-scenario"}
          and 'registerDebugAdapterDescriptorFactory("cardlang"' in js and (TOOLS / "dap" / "cardlang_dap.py").exists(), str(dbg.get("type")))
    kw_rx = [re.compile(p["match"]) for p in g["repository"]["keywords"]["patterns"]]
    missed = set()
    for app in ("fido2", "piv"):
        for f in project.program_files(layout.at(repo).examples / app):
            for k, v in lexcheck.lex(f.read_bytes()):
                if k == "kw" and not any(r.fullmatch(v) for r in kw_rx): missed.add(v)
    check("keyword patterns colour every keyword in the applets", not missed, str(sorted(missed)))
    print("ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(pathlib.Path(sys.argv[1]).resolve()) else 1)
