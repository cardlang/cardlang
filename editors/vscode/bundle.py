"""Copy the toolchain into the extension, as editors/vscode/toolchain/, for users without the repository.

The cardlang package finds the repository from its own place (src/cardlang/layout.py) and reads a few of its files
while it runs, so the bundle is laid out like the repository and holds exactly what the package needs: the project
files that `uv sync` reads, the package itself, and the specification and platform files it reads at run time.
`npm run package` runs this first, so a .vsix always carries the toolchain of the commit it was built from.

    uv run python -I editors/vscode/bundle.py           # (re)create editors/vscode/toolchain/
    uv run python -I editors/vscode/bundle.py --list    # print the bundled files, relative to the bundle
"""
import sys, shutil, pathlib
from cardlang import layout

HERE = pathlib.Path(__file__).resolve().parent
BUNDLE = HERE / "toolchain"

def sources(L=None):
    """Every file of the bundle, as a path in the repository."""
    L = L or layout.at()
    files = [L.root / name for name in ("pyproject.toml", "uv.lock", "README.md", "LICENSE", "NOTICE")]
    files += sorted(f for f in L.package.rglob("*") if f.is_file() and "__pycache__" not in f.parts)
    files += [L.spec / "00-index.md",                 # front/diagnose.py: the meaning of each CE- code
              L.spec / "annex-A-grammar.md",          # front/grammar.py: the syntactic grammar
              L.test_catalog,                         # front/pltcheck.py: the test-only catalog
              L.base_profile, L.base_catalog, L.base_types]   # the Base Profile: checkers, errors, completion
    return files

def main():
    L = layout.at()
    files = sources(L)
    if "--list" in sys.argv:
        for f in files: print(f.relative_to(L.root).as_posix())
        return
    missing = [f for f in files if not f.is_file()]
    if missing: sys.exit("missing: " + ", ".join(str(f) for f in missing))
    if BUNDLE.exists(): shutil.rmtree(BUNDLE)
    for f in files:
        target = BUNDLE / f.relative_to(L.root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, target)
    size = sum(f.stat().st_size for f in files)
    print(f"bundled {len(files)} files, {size // 1024} KB, into {BUNDLE}")

if __name__ == "__main__":
    main()
