"""Consistency checks of the VS Code extension's static parts, run by tests/run_checks.py.

- Every JSON file of the extension parses.
- The grammar's keywords are exactly the lexer's (src/cardlang/front/lexcheck.py KEYWORDS), and its intrinsics exactly
  the checker's (src/cardlang/front/expcheck.py), so highlighting cannot drift from the language.
- The scenario grammar's steps are exactly those the scenario runner accepts (src/cardlang/harness/scenario.py).
- Every regular expression of both grammars compiles (in Python's syntax, which these patterns share with
  Oniguruma), and the keyword patterns colour every keyword token of both applets.
- The extension starts the tools only by the commands the package installs, never a script by its path.
- The uv pin (uv.json) covers every platform, each with a release URL of the pinned version and a SHA-256, and the
  bundle (bundle.py) names only files that exist; the .vsix leaves neither out.
Usage: uv run python -I editors/vscode/check_extension.py .
"""
import sys, re, json, pathlib, tomllib
HERE = pathlib.Path(__file__).resolve().parent
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
          and 'registerDebugAdapterDescriptorFactory("cardlang"' in js and 'tools.run("cardlang-dap"' in js, str(dbg.get("type")))
    scripts = tomllib.loads((layout.at(repo).root / "pyproject.toml").read_text(encoding="utf-8")).get("project", {}).get("scripts", {})
    used = set(re.findall(r'tools\.run\("([\w-]+)"', js))
    check("the extension runs only commands the package installs", used == {"clc", "cardlang-lsp", "cardlang-dap"} and used <= set(scripts),
          f"uses {sorted(used)}; installed {sorted(scripts)}")
    tjs = (HERE / "toolchain.js").read_text(encoding="utf-8")
    check("the extension names no script by its path", not re.search(r'\.py\b', js + tjs), "")
    pin = docs.get("uv.json", {}); plats = pin.get("platforms", {})
    want_plats = {f"{o}-{a}" for o in ("win32", "darwin", "linux") for a in ("x64", "arm64")}
    good = all(re.fullmatch(r"https://github\.com/astral-sh/uv/releases/download/" + re.escape(pin.get("version", "?")) + r"/uv-[\w.-]+\.(zip|tar\.gz)", e.get("url", ""))
               and re.fullmatch(r"[0-9a-f]{64}", e.get("sha256", "")) for e in plats.values())
    check("uv.json pins uv for every platform", set(plats) == want_plats and good, f"uv {pin.get('version')}, platforms {sorted(plats)}")
    import importlib.util
    spec = importlib.util.spec_from_file_location("bundle", HERE / "bundle.py"); bundle = importlib.util.module_from_spec(spec); spec.loader.exec_module(bundle)
    files = bundle.sources(layout.at(repo))
    missing = [str(f) for f in files if not f.is_file()]
    check("the bundle names only files that exist", files and not missing, f"{len(files)} files; missing {missing[:3]}")
    ignored = [l.strip() for l in (HERE / ".vscodeignore").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    shipped = ("toolchain", "toolchain.js", "uv.json", "extension.js")
    check("the .vsix keeps the toolchain, toolchain.js and uv.json", not [l for l in ignored if l.split("/")[0] in shipped], str(ignored))
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
