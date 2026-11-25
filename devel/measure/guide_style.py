"""Counts prose patterns in the guide's chapters, for the prose pass (devel/plans/guide/G7-prose-pass.md).

A measure, not a check: the counts should fall, not reach zero. Code blocks, inline code, tables, headings and check
comments are left out, so only prose is counted.

Usage (from the repository root):  uv run python -I devel/measure/guide_style.py .
"""
import re, sys, pathlib
from cardlang import layout

PATTERNS = {
    "bold bullets": r"^\s*(?:- |\d+\. )\*\*",
    "colon + clause": r": [a-z]",
    "that is why/what": r"\b(?:that|this) is (?:why|what|how|the point)\b|\bthat's (?:why|what|the point)\b",
    "exactly": r"\bexactly\b",
    "whole": r"\bwhole\b",
    "deliberately": r"\bdeliberate(?:ly)?\b|\bon purpose\b",
    ", not": r", not [a-z]",
    "here is/now,": r"^(?:here is|here's|now,)",
}

def prose(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`]*`", "X", text)
    return [l for l in text.split("\n") if l.strip() and not l.lstrip().startswith(("|", "#", "<!--"))]

def measure(path):
    lines = prose(path.read_text(encoding="utf-8"))
    counts = {k: sum(len(re.findall(p, l, re.I | re.M)) for l in lines) for k, p in PATTERNS.items()}
    counts["bullets"] = sum(1 for l in lines if re.match(r"\s*(?:- |\d+\. )", l))
    counts["sentences"] = sum(len(re.findall(r"[.!?](?:\s|$)", l)) for l in lines)
    counts["words"] = sum(len(l.split()) for l in lines)
    return counts

def main(repo):
    docs = layout.at(repo).guide / "docs"
    rows = [(p.name, measure(p)) for p in sorted(docs.glob("*.md")) if not p.name.startswith("reference")]
    keys = ["words", "sentences", "bullets"] + list(PATTERNS)
    print(f"{'chapter':34}" + "".join(f"{k[:13]:>14}" for k in keys))
    total = {k: 0 for k in keys}
    for name, c in rows:
        print(f"{name:34}" + "".join(f"{c[k]:>14}" for k in keys))
        for k in keys: total[k] += c[k]
    print(f"{'total':34}" + "".join(f"{total[k]:>14}" for k in keys))

if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None)
