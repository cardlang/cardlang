"""The CardLang language server (TL1 step 3): diagnostics as you type.

Speaks the Language Server Protocol over standard input and output (src/cardlang/jsonrpc.py), and checks with the
reference front end (src/cardlang/front/diagnose.py), using the editor's unsaved text.

**Which program a file belongs to.** A file listed in the `cardlang.json` of its directory is checked as part of
that whole program, with the project's binding, and diagnostics are published for every file of the program. Any
other `.card` file is checked on its own, as an application, or as a fragment if its header says `kind: fragment`.

**When.** After a change, the server waits until the editor has been quiet for a moment (DEBOUNCE), then checks.
Run with: uv run cardlang-lsp
"""
import sys, os, re, queue, pathlib, urllib.parse, urllib.request, traceback
from cardlang import jsonrpc
from cardlang.lsp import semantic, complete
from cardlang.front import diagnose, project
from cardlang.front.lexcheck import header

DEBOUNCE = 0.3                          # seconds of quiet before checking

def uri_to_path(uri):
    p = urllib.parse.urlparse(uri)
    return pathlib.Path(urllib.request.url2pathname(urllib.parse.unquote(p.path)))

def path_to_uri(path): return pathlib.Path(path).resolve().as_uri()

def key(path): return os.path.normcase(os.path.abspath(str(path)))

class Program:
    def __init__(self, files, binding, kind):
        self.files, self.binding, self.kind = files, binding, kind

def program_of(path, text=None):
    """The program that the file at path belongs to."""
    path = pathlib.Path(os.path.abspath(path)); d = path.parent
    meta = project.load(d)
    if meta and any(key(d / f) == key(path) for f in meta["files"]):
        return Program([d / f for f in meta["files"]], meta.get("binding"), "application")
    data = text.encode("utf-8") if text is not None else (path.read_bytes() if path.exists() else b"")
    try: meta = header(data)
    except Exception: meta = {}
    return Program([path], meta.get("binding"), "fragment" if meta.get("kind") == "fragment" else "application")

def token_end(line_text, col):
    """The column after the token that starts at col (0-based), for a diagnostic's range."""
    m = re.compile(r"[A-Za-z0-9_]+|\S").match(line_text, col)
    return m.end() if m else col + 1

class Server:
    def __init__(self, channel):
        self.ch = channel; self.docs = {}; self.pending = set(); self.shutting_down = False

    # ---- protocol
    def respond(self, mid, result=None, error=None):
        m = {"jsonrpc": "2.0", "id": mid}
        if error: m["error"] = error
        else: m["result"] = result
        self.ch.write(m)

    def notify(self, method, params): self.ch.write({"jsonrpc": "2.0", "method": method, "params": params})

    def exit(self, status):
        # os._exit, not sys.exit: the reader thread is blocked reading standard input, and finalising the
        # interpreter under it crashes on Windows (0xC0000005, TL1).
        sys.stdout.flush(); sys.stderr.flush(); os._exit(status)

    def log(self, text): self.notify("window/logMessage", {"type": 4, "message": text})

    def handle(self, m):
        method, params, mid = m.get("method"), m.get("params") or {}, m.get("id")
        if method == "initialize":
            self.respond(mid, {"capabilities": {"textDocumentSync": {"openClose": True, "change": 1, "save": {"includeText": False}},
                                                "semanticTokensProvider": {"legend": {"tokenTypes": semantic.TYPES,
                                                                                      "tokenModifiers": semantic.MODIFIERS},
                                                                           "full": True},
                                                "definitionProvider": True,
                                                "completionProvider": {"triggerCharacters": ["."], "resolveProvider": False}},
                               "serverInfo": {"name": "cardlang-lsp", "version": "0.1"}})
        elif method == "shutdown": self.shutting_down = True; self.respond(mid, None)
        elif method == "exit": self.exit(0 if self.shutting_down else 1)
        elif method == "textDocument/didOpen":
            td = params["textDocument"]; p = uri_to_path(td["uri"]); self.docs[key(p)] = td["text"]; self.pending.add(p)
        elif method == "textDocument/didChange":
            p = uri_to_path(params["textDocument"]["uri"]); changes = params.get("contentChanges") or []
            if changes: self.docs[key(p)] = changes[-1]["text"]                 # full synchronisation
            self.pending.add(p)
        elif method == "textDocument/didSave": self.pending.add(uri_to_path(params["textDocument"]["uri"]))
        elif method == "textDocument/didClose":
            p = uri_to_path(params["textDocument"]["uri"]); self.docs.pop(key(p), None)
            prog = program_of(p)
            if len(prog.files) == 1: self.notify("textDocument/publishDiagnostics", {"uri": path_to_uri(p), "diagnostics": []})
            else: self.pending.add(p)
        elif method == "textDocument/completion":
            pos = params["position"]
            self.respond(mid, {"isIncomplete": False, "items": self.completion(uri_to_path(params["textDocument"]["uri"]), pos["line"], pos["character"])})
        elif method == "textDocument/definition":
            pos = params["position"]
            self.respond(mid, self.definition(uri_to_path(params["textDocument"]["uri"]), pos["line"], pos["character"]))
        elif method == "textDocument/semanticTokens/full":
            self.respond(mid, {"data": self.semantic_tokens(uri_to_path(params["textDocument"]["uri"]))})
        elif mid is not None and method is not None:
            self.respond(mid, error={"code": -32601, "message": f"not supported: {method}"})

    # ---- checking
    def text_of(self, path):
        k = key(path)
        if k in self.docs: return self.docs[k]
        try: return pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError: return ""

    def completion(self, path, line, character):
        """Completion (TL1): the runtime APIs after `card.`, and enum and error-set members after `Owner.`."""
        prog = program_of(path, self.docs.get(key(path)))
        texts = {str(f): self.text_of(f) for f in prog.files}
        target = next((str(f) for f in prog.files if key(f) == key(path)), str(path))
        texts.setdefault(target, self.text_of(path))
        try: return complete.completions(target, texts, line, character)
        except Exception:
            self.log("cardlang-lsp: completion failed: " + traceback.format_exc()); return []

    def definition(self, path, line, character):
        """Go to definition (TL1): the declaring locations of the name at the position, from the program's texts."""
        prog = program_of(path, self.docs.get(key(path)))
        texts = {str(f): self.text_of(f) for f in prog.files}
        target = next((str(f) for f in prog.files if key(f) == key(path)), str(path))
        texts.setdefault(target, self.text_of(path))
        try: found = semantic.definition(target, texts, line, character)
        except Exception:
            self.log("cardlang-lsp: definition failed: " + traceback.format_exc()); return []
        return [{"uri": path_to_uri(f), "range": {"start": {"line": l, "character": c}, "end": {"line": l, "character": c + n}}}
                for f, l, c, n in found]

    def semantic_tokens(self, path):
        """Step 3b: the identifiers of one file, coloured by what they are, from the program's current texts."""
        prog = program_of(path, self.docs.get(key(path)))
        texts = {str(f): self.text_of(f) for f in prog.files}
        target = next((str(f) for f in prog.files if key(f) == key(path)), str(path))
        texts.setdefault(target, self.text_of(path))
        try: return semantic.encode(semantic.classify(target, texts))
        except Exception:
            self.log("cardlang-lsp: semantic tokens failed: " + traceback.format_exc()); return []

    def check(self, path):
        from cardlang.front import pltcheck
        if key(path) == key(pltcheck.BASE_TYPES):
            # The Base Profile's prelude: every program already includes it, so checked as a program of its own each
            # of its declarations would clash with itself (CE-NAM-5). It is the platform's file, not an applet.
            self.notify("textDocument/publishDiagnostics", {"uri": path_to_uri(path), "diagnostics": []}); return
        prog = program_of(path, self.docs.get(key(path)))
        sources = {str(f): self.docs[key(f)] for f in prog.files if key(f) in self.docs}
        try:
            ds = diagnose.check(prog.files, prog.binding, prog.kind, sources)
        except Exception:
            self.log("cardlang-lsp: the checker failed:\n" + traceback.format_exc()); return
        by_file = {key(f): [] for f in prog.files}
        for d in ds:
            target = key(d["file"]) if d["file"] else key(path)
            if target not in by_file: target = key(path)
            line = (d["line"] or 1) - 1; col = (d["column"] or 1) - 1
            lines = self.text_of(next(f for f in prog.files if key(f) == target)).splitlines()
            end = token_end(lines[line], col) if line < len(lines) else col + 1
            by_file[target].append({"range": {"start": {"line": line, "character": col}, "end": {"line": line, "character": end}},
                                    "severity": 1, "code": d["code"], "source": "cardlang", "message": d["message"] or d["code"]})
        for f in prog.files:
            self.notify("textDocument/publishDiagnostics", {"uri": path_to_uri(f), "diagnostics": by_file[key(f)]})

    def run(self):
        q = jsonrpc.reader_thread(self.ch)
        while True:
            try: m = q.get(timeout=DEBOUNCE if self.pending else None)
            except queue.Empty:
                done = set()
                for p in list(self.pending):
                    files = program_of(p, self.docs.get(key(p))).files
                    if not any(key(f) in done for f in files): self.check(p); done.update(key(f) for f in files)
                self.pending.clear(); continue
            if m is None: self.exit(0 if self.shutting_down else 1)
            try: self.handle(m)
            except SystemExit: raise
            except Exception: self.log("cardlang-lsp: " + traceback.format_exc())

def main():
    """The `cardlang-lsp` command."""
    Server(jsonrpc.Channel()).run()

if __name__ == "__main__":
    main()
