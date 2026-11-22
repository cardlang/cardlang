"""Link this folder into VS Code's extensions folder, for development.

VS Code then loads the extension from the repository itself: after an edit, run "Developer: Reload Window".
A packaged .vsix replaces this for normal use. Run `npm install` in this folder first.

    uv run python -I editors/vscode/install.py            # create the link
    uv run python -I editors/vscode/install.py --remove   # remove it
"""
import sys, json, os, pathlib, subprocess

HERE = pathlib.Path(__file__).resolve().parent

def main():
    meta = json.loads((HERE / "package.json").read_text(encoding="utf-8"))
    target = pathlib.Path.home() / ".vscode" / "extensions" / f"{meta['publisher']}.{meta['name']}-{meta['version']}"
    if "--remove" in sys.argv:
        if target.exists(): os.rmdir(target) if target.is_junction() else sys.exit(f"{target} is not a link; not removing it")
        print(f"removed {target}"); return
    if not (HERE / "node_modules" / "vscode-languageclient").exists():
        sys.exit("run `npm install` in editors/vscode first")
    if target.exists():
        print(f"already linked: {target}"); return
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cmd", "/c", "mklink", "/J", str(target), str(HERE)], check=True, capture_output=True)
    print(f"linked {target} -> {HERE}\nRestart VS Code, or run Developer: Reload Window.")

if __name__ == "__main__":
    main()
