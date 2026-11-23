"""The guide's examples are correct, run by tests/run_checks.py.

Every fenced `cardlang` or `scenario` block in guide/docs/ must be preceded, on the line before its fence, by a
comment saying what it is:

  <!-- check: program NAME -->              a part of the program NAME; a chapter's parts of one name are joined in
  <!-- check: program NAME binding=B -->    order into one file, which must compile. B is raw (the default) or iso7816
  <!-- check: fragment -->                  a fragment, completed by the HEP-16 scaffold; it must compile
  <!-- check: error CE-XXX-n -->            a fragment that must fail with exactly that compile error
  <!-- check: scenario NAME -->             a scenario run against the program NAME of the same chapter, on the
                                            reference interpreter and the Python VM; every expect must hold
  <!-- check: none -->                      shown but not checked

Blocks in other languages are not checked. Also checked: the site's scenario lexer knows exactly the steps of the VS
Code extension's scenario grammar, which the extension's own check compares with the scenario runner.
Usage: uv run python -I tests/guidecheck.py .
"""
import re, sys, json, shutil, pathlib, tempfile
from cardlang import layout
from cardlang.front import diagnose
from cardlang.harness import backends, scenario

CHECK = re.compile(r"^<!--\s*check:\s*(.*?)\s*-->\s*$")
FENCE = re.compile(r"^(`{3,})\s*([\w-]*)\s*$")
BACKENDS = ("interp", "pyvm")

def blocks(path):
    """(line, language, annotation or None, text) of every fenced block of a Markdown file."""
    lines = path.read_text(encoding="utf-8").split("\n"); out = []; i = 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m:
            fence, lang, start = m.group(1), m.group(2), i
            prev = CHECK.match(lines[i - 1]) if i > 0 else None
            j = i + 1
            while j < len(lines) and lines[j].strip() != fence: j += 1
            out.append((start + 1, lang, prev.group(1) if prev else None, "\n".join(lines[i + 1:j]) + "\n"))
            i = j + 1
        else:
            if CHECK.match(lines[i]) and not (i + 1 < len(lines) and FENCE.match(lines[i + 1])):
                out.append((i + 1, None, CHECK.match(lines[i]).group(1), None))       # a comment with no block after it
            i += 1
    return out

def main(repo):
    L = layout.at(repo); docs = L.guide / "docs"
    ok = True; counts = {"program": 0, "fragment": 0, "error": 0, "scenario": 0, "none": 0}
    def report(passed, where, detail):
        nonlocal ok
        ok &= bool(passed); print("PASS" if passed else "FAIL", where, "|", detail)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="guidecheck-"))
    for md in sorted(docs.rglob("*.md")):
        rel = md.relative_to(L.root).as_posix()
        programs = {}                                  # name -> {"parts": [...], "binding": ...}
        scenarios = []
        for line, lang, note, text in blocks(md):
            where = f"{rel}:{line}"
            if lang is None:
                report(False, where, f"a check comment with no code block after it: {note}"); continue
            if lang not in ("cardlang", "scenario"):
                continue
            if note is None:
                report(False, where, f"a {lang} block with no check comment"); continue
            words = note.split(); kind = words[0]
            if kind not in counts:
                report(False, where, f"an unknown check: {note}"); continue
            counts[kind] += 1
            if kind == "none": continue
            if (kind == "scenario") != (lang == "scenario"):
                report(False, where, f"a {lang} block marked {kind}"); continue
            if kind == "program":
                if len(words) < 2: report(False, where, "a program needs a name"); continue
                opts = dict(w.split("=", 1) for w in words[2:] if "=" in w)
                prog = programs.setdefault(words[1], {"parts": [], "binding": None, "line": line})
                prog["parts"].append(text)
                if "binding" in opts: prog["binding"] = opts["binding"]
            elif kind in ("fragment", "error"):
                f = tmp / f"{md.stem}-{line}.card"; f.write_text(text, encoding="utf-8")
                ds = diagnose.check([f], None, "fragment")
                if kind == "fragment":
                    report(not ds, where, "a fragment compiles" if not ds else diagnose.format_diagnostic(ds[0]))
                else:
                    want = words[1] if len(words) > 1 else "?"
                    got = ds[0]["code"] if ds else None
                    report(got == want, where, f"fails with {want}" if got == want else f"expected {want}, got {got or 'no error'}")
            elif kind == "scenario":
                scenarios.append((where, words[1] if len(words) > 1 else None, text))
        built = {}
        for name, prog in programs.items():
            f = tmp / f"{md.stem}-{name}.card"; f.write_text("\n".join(prog["parts"]), encoding="utf-8")
            ds = diagnose.check([f], prog["binding"], "application")
            report(not ds, f"{rel}:{prog['line']}", f"program {name} ({len(prog['parts'])} parts) compiles"
                   if not ds else f"program {name}: " + diagnose.format_diagnostic(ds[0]))
            if not ds: built[name] = (f, prog["binding"])
        for where, name, text in scenarios:
            if name not in built:
                report(False, where, f"a scenario for {name!r}, which is not a compiling program of this chapter"); continue
            f, binding = built[name]
            for b in BACKENDS:
                try:
                    problem = scenario.run_scenario(backends.build(b, [f], binding), text)
                except backends.BuildError as e:
                    problem = "does not build: " + str(e)
                report(problem is None, where, f"scenario for {name} passes on {b}" if problem is None else f"{b}: {problem}")
    # the site's scenario lexer, against the extension's scenario grammar
    from cardlang.highlight import STEPS
    g = json.loads((L.vscode / "syntaxes" / "cardlang-scenario.tmLanguage.json").read_text(encoding="utf-8"))
    grammar = set(re.search(r"\(install\|[^)]*\)", json.dumps(g)).group(0)[1:-1].split("|"))
    report(set(STEPS) == grammar, "src/cardlang/highlight.py", f"lexer steps {sorted(STEPS)}" if set(STEPS) == grammar
           else f"lexer {sorted(STEPS)}, extension grammar {sorted(grammar)}")
    shutil.rmtree(tmp, ignore_errors=True)
    print("checked:", ", ".join(f"{v} {k}" for k, v in counts.items()))
    print("ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None) else 1)
