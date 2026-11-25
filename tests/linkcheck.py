"""The link check: references in the documentation, and repository paths in the code, stay correct.

Over every Markdown file the repository tracks:
1. **Links:** a relative link must reach an existing file or folder.
2. **Anchors:** a link's `#anchor` must name a heading of its target, or an explicit `<a id>`. Headings follow
   GitHub's rules: lower case, punctuation dropped, spaces to `-`, and `-1`, `-2` for repeats.
3. **Named files:** a path in backticks must resolve against the repository root, the document's folder, or a folder
   such paths are written relative to (`language/conformance/`, `vm/c/`). A path counts only if its last part has a file
   extension or its first part is a known folder, so `and/or` is not one. Build outputs (in a build or
   node_modules folder, or a generated file such as a .vsix) are not checked: a fresh checkout has none.

   The documents in devel/ (layout.historical) record the past, and name files where they were when they were
   written, so their file paths are not checked. Their links are checked like any other.

A line carrying `<!-- linkcheck: ignore -->` is not checked.

Over every Python file it tracks (4): only `layout` builds paths into the repository's top-level parts. A line that
sets up `sys.path` is exempt: it bootstraps imports, as some scripts in devel/ do.

Over every source file it tracks outside the historical folders (5: .card, .c, .h, .py, .js): a repository path named
anywhere in it, in a comment, a docstring or a string, must exist. A path counts if its first part is a top-level folder.
Usage: uv run python -I tests/linkcheck.py .
"""
import re, sys, pathlib, subprocess, collections
HERE = pathlib.Path(__file__).resolve().parent
from cardlang import layout

IGNORE = "<!-- linkcheck: ignore -->"
EXTENSIONS = {".md", ".py", ".card", ".txt", ".json", ".c", ".h", ".js", ".toml", ".cmake", ".scenario", ".clvm", ".lock",
              ".yml", ".yaml", ".bin", ".dll", ".so", ".exe", ".html", ".svg", ".png", ".ini"}
SKIP_DIRS = {".git", ".venv", "node_modules", "build", "reference", "__pycache__", "_deps",
             "toolchain"}                       # build outputs; toolchain: the extension's bundle, made when it is packaged
SOURCES = (".card", ".c", ".h", ".py", ".js")                                  # source files whose named paths are checked (5)
GENERATED = {".vsix", ".clvm", ".dll", ".so", ".exe", ".lib", ".obj", ".o"}      # build outputs a document may name

def tracked(root, pattern):
    """The tracked files matching pattern, or, outside a git checkout, every such file outside the ignored folders."""
    r = subprocess.run(["git", "-C", str(root), "ls-files", pattern], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip(): return [root / p for p in r.stdout.split()]
    return [p for p in root.rglob(pattern) if not (set(p.relative_to(root).parts) & SKIP_DIRS)]

def strip_code(text):
    """The text with fenced code blocks blanked, keeping line numbers."""
    return re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)

def slug(heading):
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)                  # [text](link) -> text
    h = h.replace("`", "").strip().lower()
    h = re.sub(r"[^\w\- ]", "", h, flags=re.U)
    return h.replace(" ", "-")

_anchors = {}
def anchors(path):
    if path not in _anchors:
        seen = collections.Counter(); out = set()
        text = strip_code(path.read_text(encoding="utf-8", errors="replace"))
        for m in re.finditer(r"^#{1,6}\s+(.*?)\s*#*\s*$", text, re.M):
            s = slug(m.group(1)); n = seen[s]; seen[s] += 1
            out.add(s if n == 0 else f"{s}-{n}")
        out |= set(re.findall(r'<a\s+(?:id|name)="([^"]+)"', text))
        _anchors[path] = out
    return _anchors[path]

def main(root):
    L = layout.at(root); root = L.root
    bases = [root, L.conformance, L.vm_c]
    known_dirs = {p.name for p in root.iterdir() if p.is_dir()} | {"valid", "invalid", "runtime", "platform", "src", "include",
                                                                    "hal-host", "test", "cmake", "testdata", "syntaxes", "snippets"}
    historical = [pathlib.Path(h) for h in L.historical]
    fails = files = 0
    def fail(where, msg):
        nonlocal fails
        fails += 1; print(f"FAIL {where} | {msg}")
    for md in sorted(tracked(root, "*.md")):
        files += 1; rel = md.relative_to(root).as_posix()
        hist = any(md.resolve().is_relative_to(h) for h in historical)
        lines = strip_code(md.read_text(encoding="utf-8", errors="replace")).split("\n")
        before = fails
        for n, line in enumerate(lines, 1):
            if IGNORE in line: continue
            code_free = re.sub(r"`[^`]*`", "", line)
            for m in re.finditer(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)", code_free):
                target = m.group(1)
                if re.match(r"[a-z][a-z0-9+.-]*:", target): continue        # http:, mailto:, and the like
                file_part, _, anchor = target.partition("#")
                dest = (md.parent / file_part).resolve() if file_part else md.resolve()
                if not dest.exists(): fail(f"{rel}:{n}", f"link to a missing file: {target}"); continue
                if anchor and dest.is_file() and dest.suffix == ".md" and anchor.lower() not in anchors(dest):
                    fail(f"{rel}:{n}", f"link to a missing heading: {target}")
            for m in ([] if hist else re.finditer(r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+)/?`", line)):
                p = m.group(1); parts = p.split("/")
                if not (pathlib.PurePosixPath(parts[-1]).suffix.lower() in EXTENSIONS or parts[0] in known_dirs): continue
                if set(parts) & SKIP_DIRS or pathlib.PurePosixPath(parts[-1]).suffix.lower() in GENERATED: continue   # a build output
                if any((b / p).exists() for b in bases + [md.parent]): continue
                fail(f"{rel}:{n}", f"a named file that does not exist: {p}")
        if fails == before: print(f"PASS {rel}")
    # 4. only layout builds paths into the top-level parts
    top = "|".join(layout.TOP_LEVEL)
    rx = re.compile(r'(?:\bROOT|\bREPO|\brepo|\broot|parents\[\d\]|\.parent|\bTOOLS)\s*/\s*"(' + top + r')"')
    bad = 0
    for py in sorted(tracked(root, "*.py")):
        if py.name == "layout.py": continue
        for n, line in enumerate(py.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            if "sys.path" in line or line.lstrip().startswith("#"): continue
            if rx.search(line):
                bad += 1; fail(f"{py.relative_to(root).as_posix()}:{n}", "a repository path built outside layout: " + line.strip()[:100])
    if not bad: print("PASS only layout builds paths into the top-level parts")
    # 5. repository paths named in source files: comments, docstrings and strings
    tops = {p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")} - SKIP_DIRS
    rx = re.compile(r"(?<![\w./-])((?:" + "|".join(sorted(tops)) + r")(?:/[A-Za-z0-9_.*-]+)+)")
    bad = 0
    for src in sorted(sum((tracked(root, f"*{ext}") for ext in SOURCES), [])):
        if any(src.resolve().is_relative_to(h) for h in historical): continue
        if set(src.relative_to(root).parts) & SKIP_DIRS: continue
        for n, line in enumerate(src.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            if IGNORE in line: continue
            for m in rx.finditer(line):
                p = m.group(1).rstrip(".,;:")
                if "*" in p or set(p.split("/")) & SKIP_DIRS or pathlib.PurePosixPath(p).suffix.lower() in GENERATED or (root / p).exists() or (src.parent / p).exists(): continue
                bad += 1; fail(f"{src.relative_to(root).as_posix()}:{n}", f"a named file that does not exist: {p}")
    if not bad: print("PASS repository paths named in source files exist")
    # 6. development steps stay in devel/, and 7. no absolute path into a user's home folder, in any tracked text file
    step = re.compile(r"\b(?:WP|SP|VM|TL|PR)\d+[a-z]?\b")
    home = re.compile(r"\b[A-Za-z]:[\\/]+Users[\\/]+\w|(?<![\w.])/(?:home|Users)/[A-Za-z]")
    devel = L.devel
    bad_step = bad_home = 0
    for f in sorted(tracked(root, "*")):
        if not f.is_file() or set(f.relative_to(root).parts) & SKIP_DIRS: continue
        data = f.read_bytes()
        if b"\0" in data[:4096]: continue                                       # a binary file
        rel = f.relative_to(root).as_posix(); in_devel = f.resolve().is_relative_to(devel.resolve())
        for n, line in enumerate(data.decode("utf-8", errors="replace").split("\n"), 1):
            if IGNORE in line or "linkcheck: ignore" in line: continue
            if not in_devel and step.search(line):
                bad_step += 1; fail(f"{rel}:{n}", f"a development step outside devel/: {step.search(line).group(0)}")
            if home.search(line):
                bad_home += 1; fail(f"{rel}:{n}", f"an absolute path into a home folder: {home.search(line).group(0)}")
    if not bad_step: print("PASS development steps are named only in devel/")
    if not bad_home: print("PASS no absolute path into a home folder")
    print(f"{files} documents; {fails} failures")
    print("ALL PASS" if fails == 0 else "FAILURES")
    return fails == 0

if __name__ == "__main__":
    sys.exit(0 if main(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None) else 1)
