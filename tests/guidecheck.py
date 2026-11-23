"""The guide's examples are correct, run by tests/run_checks.py.

Every fenced `cardlang` or `scenario` block in guide/docs/ must be preceded, on the line before its fence, by a
comment saying what it is:

  <!-- check: program NAME -->              top-level declarations of the program NAME. They carry over: a block
  <!-- check: program NAME binding=B -->    continues the program from every earlier block of that name, in this
                                            chapter and earlier ones (in file-name order), and a declaration with the
                                            same name as an earlier one replaces it in place. The program as it
                                            stands at the end of each chapter that shows it must compile. B is raw
                                            (the default) or iso7816, and stays once given
  <!-- check: program NAME remove=A,B -->   also removes the earlier declarations A and B first, as when the text
                                            tells the reader to delete them
  <!-- check: fragment -->                  a fragment, completed by the HEP-16 scaffold; it must compile
  <!-- check: error CE-XXX-n -->            a fragment that must fail with exactly that compile error
  <!-- check: error CODE binding=B -->      a whole application, built for binding B, that must fail with CODE
  <!-- check: scenario NAME -->             a scenario run against the program NAME as it stands at that point, on
                                            the reference interpreter and the Python VM; every expect must hold
  <!-- check: none -->                      shown but not checked

Blocks in other languages are not checked. Also checked: the site's scenario lexer knows exactly the steps of the VS
Code extension's scenario grammar, which the extension's own check compares with the scenario runner.
Usage: uv run python -I tests/guidecheck.py .
"""
import re, sys, json, shutil, pathlib, tempfile
from cardlang import layout
from cardlang.front import diagnose
from cardlang.front.lexcheck import lex, LexError
from cardlang.harness import backends, scenario

CHECK = re.compile(r"^\s*<!--\s*check:\s*(.*?)\s*-->\s*$")
FENCE = re.compile(r"^(\s*)(`{3,})\s*([\w-]*)\s*$")       # indented too, as inside a list item
BACKENDS = ("interp", "pyvm")
OPENS = {"function", "command", "struct", "enum", "errors"}      # declarations that end with their closing brace
ENDS = {"const", "persistent", "session"}                        # declarations that end with a semicolon

def blocks(path):
    """(line, language, annotation or None, text) of every fenced block of a Markdown file."""
    lines = path.read_text(encoding="utf-8").split("\n"); out = []; i = 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m:
            indent, fence, lang, start = len(m.group(1)), m.group(2), m.group(3), i
            prev = CHECK.match(lines[i - 1]) if i > 0 else None
            j = i + 1
            while j < len(lines) and lines[j].strip() != fence: j += 1
            body = [l[indent:] if l[:indent].strip() == "" else l for l in lines[i + 1:j]]
            out.append((start + 1, lang, prev.group(1) if prev else None, "\n".join(body) + "\n"))
            i = j + 1
        else:
            if CHECK.match(lines[i]) and not (i + 1 < len(lines) and FENCE.match(lines[i + 1])):
                out.append((i + 1, None, CHECK.match(lines[i]).group(1), None))       # a comment with no block after it
            i += 1
    return out

def declarations(text):
    """[(name, text)] of the top-level declarations in a block. Each takes the lines from the end of the one before,
    so the comments above a declaration go with it, and the block's last lines go with its last declaration.
    Raises ValueError for a block that is not a sequence of whole declarations."""
    try:
        toks = lex(text.encode("utf-8"))
    except LexError as e:
        raise ValueError(f"a lexical error, {e.cls}")
    lines = text.split("\n"); out = []; depth = 0; cur = None; last = 0
    for i, tok in enumerate(toks):
        v = tok[1]
        if depth == 0 and cur is None:
            if v not in OPENS | ENDS or i + 1 >= len(toks):
                raise ValueError(f"line {tok.pos[1]}: {v!r} does not start a declaration")
            cur = (toks[i + 1][1], v)
        if v == "{": depth += 1
        elif v == "}": depth -= 1
        if depth == 0 and ((cur[1] in OPENS and v == "}") or (cur[1] in ENDS and v == ";")):
            end = tok.pos[1]
            out.append([cur[0], "\n".join(lines[last:end])]); last = end; cur = None
    if cur is not None or depth:
        raise ValueError("the block ends inside a declaration")
    if not out:
        raise ValueError("no declarations")
    out[-1][1] += "\n" + "\n".join(lines[last:])
    return [tuple(d) for d in out]

def main(repo):
    L = layout.at(repo); docs = L.guide / "docs"
    ok = True; counts = {"program": 0, "fragment": 0, "error": 0, "scenario": 0, "none": 0}
    def report(passed, where, detail):
        nonlocal ok
        ok &= bool(passed); print("PASS" if passed else "FAIL", where, "|", detail)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="guidecheck-"))
    programs = {}                       # name -> {"decls": {declaration name: text}, "binding": B}, across chapters
    versions = {}                       # (name, text, binding) -> its file, or None if it does not compile
    def build(name, where):
        """The program as it stands now: its file, or None, after reporting (once per version) whether it compiles."""
        prog = programs[name]
        text = "\n\n".join(d.strip("\n") for d in prog["decls"].values()) + "\n"
        key = (name, text, prog["binding"])
        if key not in versions:
            f = tmp / f"{name}-{len(versions)}.card"; f.write_text(text, encoding="utf-8")
            ds = diagnose.check([f], prog["binding"], "application")
            report(not ds, where, f"program {name} ({len(prog['decls'])} declarations) compiles"
                   if not ds else f"program {name}: " + diagnose.format_diagnostic(ds[0]))
            versions[key] = None if ds else f
        return versions[key]
    for md in sorted(docs.rglob("*.md")):
        rel = md.relative_to(L.root).as_posix()
        shown = {}                                     # program name -> where its last block in this chapter is
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
                try:
                    decls = declarations(text)
                except ValueError as e:
                    report(False, where, f"program {words[1]}: {e}"); continue
                prog = programs.setdefault(words[1], {"decls": {}, "binding": None})
                gone = [n for n in opts.get("remove", "").split(",") if n]
                missing = [n for n in gone if n not in prog["decls"]]
                if missing:
                    report(False, where, f"program {words[1]}: nothing to remove called {', '.join(missing)}"); continue
                for n in gone: del prog["decls"][n]
                prog["decls"].update(decls)
                if "binding" in opts: prog["binding"] = opts["binding"]
                shown[words[1]] = where
            elif kind in ("fragment", "error"):
                f = tmp / f"{md.stem}-{line}.card"; f.write_text(text, encoding="utf-8")
                opts = dict(w.split("=", 1) for w in words[1:] if "=" in w)
                words = [w for w in words if "=" not in w]
                if "binding" in opts:                  # a whole application, built for that binding
                    ds = diagnose.check([f], opts["binding"], "application")
                else:
                    ds = diagnose.check([f], None, "fragment")
                if kind == "fragment":
                    report(not ds, where, "a fragment compiles" if not ds else diagnose.format_diagnostic(ds[0]))
                else:
                    want = words[1] if len(words) > 1 else "?"
                    got = ds[0]["code"] if ds else None
                    report(got == want, where, f"fails with {want}" if got == want else f"expected {want}, got {got or 'no error'}")
            elif kind == "scenario":
                name = words[1] if len(words) > 1 else None
                f = build(name, where) if name in programs else None
                if f is None:
                    report(False, where, f"a scenario for {name!r}, which is not a compiling program at this point"); continue
                for b in BACKENDS:
                    try:
                        problem = scenario.run_scenario(backends.build(b, [f], programs[name]["binding"]), text)
                    except backends.BuildError as e:
                        problem = "does not build: " + str(e)
                    report(problem is None, where, f"scenario for {name} passes on {b}" if problem is None else f"{b}: {problem}")
        for name, where in shown.items():
            build(name, where)
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
