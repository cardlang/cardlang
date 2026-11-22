"""A scripted session with the CardLang language server (TL1 step 3), run by tools/run_checks.py.

Starts tools/lsp/cardlang_lsp.py as the editor would, then:
1. opens a file of the FIDO2 applet: every file of the program gets an empty diagnostics list;
2. edits it, without saving, to mix two operators: CE-EXP-4 appears in that file, on the edited line;
3. undoes the edit: the diagnostic is cleared;
4. opens an invalid conformance fragment on its own: its error is reported with its code;
5. shuts the server down cleanly.
Usage: uv run python -I tools/lsp/lsp_check.py .
"""
import sys, json, pathlib, subprocess, threading, queue, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jsonrpc

class Client:
    def __init__(self, repo):
        self.p = subprocess.Popen([sys.executable, "-I", str(HERE / "cardlang_lsp.py")], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=repo)
        self.ch = jsonrpc.Channel(self.p.stdout, self.p.stdin); self.q = jsonrpc.reader_thread(self.ch); self.next = 1
    def request(self, method, params):
        mid = self.next; self.next += 1
        self.ch.write({"jsonrpc": "2.0", "id": mid, "method": method, "params": params})
        while True:
            m = self.q.get(timeout=30)
            if m and m.get("id") == mid: return m
    def notify(self, method, params): self.ch.write({"jsonrpc": "2.0", "method": method, "params": params})
    def diagnostics(self, uris, timeout=30):
        """Wait for publishDiagnostics for every uri; returns {uri: diagnostics}."""
        got, end = {}, time.time() + timeout
        while set(uris) - set(got) and time.time() < end:
            try: m = self.q.get(timeout=max(0.1, end - time.time()))
            except queue.Empty: break
            if m and m.get("method") == "textDocument/publishDiagnostics": got[m["params"]["uri"]] = m["params"]["diagnostics"]
        return got

def main(repo):
    ok = True
    def check(name, passed, detail=""):
        nonlocal ok
        ok &= bool(passed); print("PASS" if passed else "FAIL", name, "|", detail)
    c = Client(repo)
    r = c.request("initialize", {"processId": None, "rootUri": repo.as_uri(), "capabilities": {}})
    check("initialize", r.get("result", {}).get("capabilities", {}).get("textDocumentSync"), r.get("result", {}).get("serverInfo"))
    c.notify("initialized", {})
    app = repo / "examples" / "fido2"
    files = [app / f for f in json.loads((app / "cardlang.json").read_text())["files"]]
    uris = [f.resolve().as_uri() for f in files]
    ctap = app / "ctap.card"; uri = ctap.resolve().as_uri(); text = ctap.read_text(encoding="utf-8")
    c.notify("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": "cardlang", "version": 1, "text": text}})
    got = c.diagnostics(uris)
    check("open: every file of the program is clean", set(got) == set(uris) and not any(got.values()), f"{len(got)} files")
    old = "    var code: u8 = message[0];"
    assert text.count(old) == 1
    line = text[:text.index(old)].count("\n")
    edited = text.replace(old, "    var code: u8 = message[0] + 1 * 2;")
    c.notify("textDocument/didChange", {"textDocument": {"uri": uri, "version": 2}, "contentChanges": [{"text": edited}]})
    got = c.diagnostics(uris); ds = got.get(uri, [])
    first = ds[0] if ds else {}
    check("edit: the error is reported where it is", len(ds) == 1 and first.get("code") == "CE-EXP-4"
          and first["range"]["start"]["line"] == line, json.dumps(first)[:160])
    check("edit: the other files stay clean", all(not v for u, v in got.items() if u != uri), "")
    c.notify("textDocument/didChange", {"textDocument": {"uri": uri, "version": 3}, "contentChanges": [{"text": text}]})
    got = c.diagnostics(uris)
    check("undo: the diagnostic is cleared", not got.get(uri, [1]), "")
    bad = repo / "conformance" / "invalid" / "exp-105-mixed-arithmetic.card"; buri = bad.resolve().as_uri()
    c.notify("textDocument/didOpen", {"textDocument": {"uri": buri, "languageId": "cardlang", "version": 1,
                                                       "text": bad.read_text(encoding="utf-8")}})
    ds = c.diagnostics([buri]).get(buri, [])
    check("a single file: its error", len(ds) == 1 and ds[0]["code"] == "CE-EXP-4" and ds[0]["range"]["start"]["line"] == 7,
          json.dumps(ds[:1])[:160])
    prelude = repo / "platform" / "base-types.card"; puri = prelude.resolve().as_uri()
    c.notify("textDocument/didOpen", {"textDocument": {"uri": puri, "languageId": "cardlang", "version": 1,
                                                       "text": prelude.read_text(encoding="utf-8")}})
    ds = c.diagnostics([puri]).get(puri, [1])
    check("the Base Profile's prelude is not checked as an applet", ds == [], json.dumps(ds)[:120])
    r = c.request("shutdown", None); c.notify("exit", None)
    try: rc = c.p.wait(timeout=10)
    except subprocess.TimeoutExpired: c.p.kill(); rc = None
    check("shutdown and exit", r.get("result", 1) is None and rc == 0, f"exit status {rc}")
    print("ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(pathlib.Path(sys.argv[1]).resolve()) else 1)
