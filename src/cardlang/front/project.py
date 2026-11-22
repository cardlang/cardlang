"""A CardLang program's source files: the `cardlang.json` project file.

A program is one `.card` file, or a directory. A directory's `cardlang.json` lists its files in build order, and may
give the program a name and a binding:

    {"name": "piv", "files": ["constants.card", "objects.card", ...], "binding": "iso7816"}

A directory without one is its `.card` files in name order. `cardlang.json` replaces the older `files.txt`.
"""
import json, pathlib

PROJECT = "cardlang.json"

def load(d):
    """The project file of directory d, as a dict, or None."""
    p = pathlib.Path(d) / PROJECT
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def program_files(t):
    """The source files of a program: t itself if it is a file, else its project's files, else its .card files."""
    t = pathlib.Path(t)
    if not t.is_dir(): return [t]
    meta = load(t)
    return [t / f for f in meta["files"]] if meta else sorted(t.glob("*.card"))

def write(d, files, **fields):
    """Write directory d's project file (used by the test generators)."""
    meta = dict(fields); meta["files"] = list(files)
    (pathlib.Path(d) / PROJECT).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n")
