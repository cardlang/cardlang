"""MkDocs hooks for the guide.

A code block's title marks an example that is wrong on purpose: "Does not compile: CE-…" or
"Contains a bug" (tests/guidecheck.py enforces which blocks carry them). This hook gives those
titles a class, so the stylesheet can draw them as warnings rather than as file names.
"""

import re

MARKS = {"Does not compile": "cl-fails", "Contains a bug": "cl-buggy"}
TITLE = re.compile(r'<span class="filename">(' + "|".join(map(re.escape, MARKS)) + r")")


def on_page_content(html, **kwargs):
    return TITLE.sub(lambda m: f'<span class="filename {MARKS[m.group(1)]}">{m.group(1)}', html)
