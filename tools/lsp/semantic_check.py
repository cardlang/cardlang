"""Checks of semantic colouring (TL1 step 3b), run by tools/run_checks.py.

1. Every identifier of both applets and of every runtime test gets a kind.
2. The sample tools/lsp/testdata/semantic-sample.card is classified exactly as pinned below, reviewed by hand
   (2026-11-21): every kind and modifier the server produces.
3. Through the language server: a semanticTokens/full request returns the same tokens, in the LSP's encoding.
Usage: uv run python -I tools/lsp/semantic_check.py .
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
for d in (HERE, HERE.parent / "checkers"):
    if str(d) not in sys.path: sys.path.insert(0, str(d))
import semantic, project
from lexcheck import lex

SAMPLE = HERE / "testdata" / "semantic-sample.card"
EXPECTED = [
    (3, "AppError", "enum", "declaration"),
    (4, "Busy", "enumMember", "declaration"),
    (7, "Mode", "enum", "declaration"),
    (8, "Idle", "enumMember", "declaration"),
    (9, "Active", "enumMember", "declaration"),
    (12, "Pair", "struct", "declaration"),
    (13, "first", "property", "declaration"),
    (13, "u32", "type", "defaultLibrary"),
    (14, "second", "property", "declaration"),
    (14, "u32", "type", "defaultLibrary"),
    (17, "LIMIT", "variable", "declaration+readonly"),
    (17, "u32", "type", "defaultLibrary"),
    (18, "mode", "variable", "declaration+static"),
    (18, "Mode", "enum", ""),
    (19, "total", "variable", "declaration+persistent"),
    (19, "u32", "type", "defaultLibrary"),
    (21, "add", "function", "declaration"),
    (21, "values", "parameter", "declaration+readonly"),
    (21, "u8", "type", "defaultLibrary"),
    (21, "extra", "parameter", "declaration"),
    (21, "u32", "type", "defaultLibrary"),
    (21, "u32", "type", "defaultLibrary"),
    (22, "sum", "variable", "declaration"),
    (22, "u32", "type", "defaultLibrary"),
    (22, "extra", "parameter", ""),
    (23, "index", "variable", "declaration"),
    (23, "u32", "type", "defaultLibrary"),
    (23, "values", "parameter", "readonly"),
    (23, "length", "property", "defaultLibrary"),
    (24, "value", "variable", "declaration"),
    (24, "u32", "type", "defaultLibrary"),
    (24, "convert", "macro", "defaultLibrary"),
    (24, "u32", "type", "defaultLibrary"),
    (24, "values", "parameter", "readonly"),
    (24, "index", "variable", ""),
    (25, "sum", "variable", ""),
    (25, "checked_add", "macro", "defaultLibrary"),
    (25, "sum", "variable", ""),
    (25, "value", "variable", ""),
    (25, "AppError", "enum", ""),
    (25, "Busy", "enumMember", ""),
    (27, "sum", "variable", ""),
    (30, "process", "function", "declaration"),
    (30, "request", "parameter", "declaration+readonly"),
    (30, "u8", "type", "defaultLibrary"),
    (30, "response", "parameter", "declaration"),
    (30, "u8", "type", "defaultLibrary"),
    (30, "u32", "type", "defaultLibrary"),
    (31, "mode", "variable", "static"),
    (31, "Mode", "enum", ""),
    (31, "Idle", "enumMember", ""),
    (31, "AppError", "enum", ""),
    (31, "Busy", "enumMember", ""),
    (32, "pair", "variable", "declaration"),
    (32, "Pair", "struct", ""),
    (32, "Pair", "struct", ""),
    (32, "first", "property", ""),
    (32, "LIMIT", "variable", "readonly"),
    (32, "second", "property", ""),
    (33, "digest", "variable", "declaration"),
    (33, "u32", "type", "defaultLibrary"),
    (33, "card", "namespace", "defaultLibrary"),
    (33, "crypto", "namespace", "defaultLibrary"),
    (33, "digest", "function", "defaultLibrary"),
    (33, "DigestAlgorithm", "enum", "defaultLibrary"),
    (33, "Sha256", "enumMember", "defaultLibrary"),
    (33, "request", "parameter", "readonly"),
    (33, "response", "parameter", ""),
    (33, "AppError", "enum", ""),
    (33, "Busy", "enumMember", ""),
    (34, "total", "variable", "persistent"),
    (34, "add", "function", ""),
    (34, "request", "parameter", "readonly"),
    (34, "pair", "variable", ""),
    (34, "first", "property", ""),
    (35, "digest", "variable", ""),
]

def main(repo):
    ok = True
    def check(name, passed, detail=""):
        nonlocal ok
        ok &= bool(passed); print("PASS" if passed else "FAIL", name, "|", detail)
    progs = [repo / "examples" / "fido2", repo / "examples" / "piv"] + sorted((repo / "conformance" / "runtime").glob("run-*"))
    for d in progs:
        files = project.program_files(d); texts = {str(f): f.read_text(encoding="utf-8") for f in files}
        missing, total = [], 0
        for f in files:
            got = {(l, c) for l, c, *_ in semantic.classify(str(f), texts)}
            for t in lex(f.read_bytes(), str(f)):
                if t[0] == "id":
                    total += 1
                    if (t.pos[1] - 1, t.pos[2] - 1) not in got: missing.append(f"{f.name}:{t.pos[1]} {t[1]}")
        check(f"{d.name}: every identifier has a kind", not missing, f"{total} identifiers" + (f"; missing {missing[:5]}" if missing else ""))
    text = SAMPLE.read_text(encoding="utf-8"); lines = text.splitlines()
    got = [(l + 1, lines[l][c:c + n], t, "+".join(sorted(m))) for l, c, n, t, m in semantic.classify(str(SAMPLE), {str(SAMPLE): text})]
    diff = [x for x in EXPECTED if x not in got] + [x for x in got if x not in EXPECTED]
    check("the sample is classified as pinned", got == EXPECTED, f"{len(got)} tokens" + (f"; differences {diff[:4]}" if diff else ""))
    from lsp_check import Client
    c = Client(repo)
    c.request("initialize", {"processId": None, "rootUri": repo.as_uri(), "capabilities": {}})
    uri = SAMPLE.resolve().as_uri()
    c.notify("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": "cardlang", "version": 1, "text": text}})
    r = c.request("textDocument/semanticTokens/full", {"textDocument": {"uri": uri}})
    data = (r.get("result") or {}).get("data", [])
    want = semantic.encode(semantic.classify(str(SAMPLE), {str(SAMPLE): text}))
    check("the server returns the tokens, encoded", data == want and len(data) == 5 * len(EXPECTED), f"{len(data) // 5} tokens")
    c.request("shutdown", None); c.notify("exit", None)
    try: c.p.wait(timeout=10)
    except Exception: c.p.kill()
    print("ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(pathlib.Path(sys.argv[1]).resolve()) else 1)
