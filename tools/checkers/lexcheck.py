"""Reference lexer written from spec chapter 2, used to verify SP1."""
import re, sys, pathlib

PUNCT3 = ["<<=", ">>="]                                       # compound assignment (WP9 L6)
PUNCT2 = ["..", "->", "=>", "==", "!=", "<=", ">=", "<<", ">>", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="]
PUNCT1 = list("{}()[];:,.=<>+-*/%~&|^")
KEYWORDS = set("""abort and attempt break command const continue else enum Err errors false for function
if in inout match not Ok or persistent ref require return session struct transaction true var while wipe ignore""".split())
LIT = re.compile(r"(?:[0-9](?:_?[0-9])*|0x[0-9a-fA-F](?:_?[0-9a-fA-F])*|0b[01](?:_?[01])*)\Z")

class LexError(Exception):
    def __init__(self, cls, pos): super().__init__(cls); self.cls, self.pos = cls, pos

def lex(data: bytes):
    try:
        s = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise LexError("CE-LEX-1", e.start)
    if s.startswith("﻿"):
        s = s[1:]
    i, n, toks = 0, len(s), []
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
        elif s.startswith("//", i):
            while i < n and s[i] not in "\r\n":
                i += 1
        elif s.startswith("/*", i):
            j = s.find("*/", i + 2)
            if j < 0:
                raise LexError("CE-LEX-3", i)
            i = j + 2
        elif c.isascii() and c.isdigit():
            j = i
            while j < n and s[j].isascii() and (s[j].isalnum() or s[j] == "_"):
                j += 1
            run = s[i:j]
            if not LIT.match(run):
                raise LexError("CE-LEX-4", i)
            toks.append(("int", run)); i = j
        elif s.startswith('b"', i):                             # a byte-string literal (WP9 L1)
            j = i + 2; out = []
            while True:
                if j >= n or s[j] in "\r\n": raise LexError("CE-LEX-5", i)
                ch = s[j]
                if ch == '"': j += 1; break
                if ch == "\\":
                    esc = s[j + 1:j + 2]
                    if esc in ('"', "\\"): out.append(ord(esc)); j += 2; continue
                    if esc == "x" and re.fullmatch(r"[0-9a-fA-F]{2}", s[j + 2:j + 4] or ""):
                        out.append(int(s[j + 2:j + 4], 16)); j += 4; continue
                    raise LexError("CE-LEX-5", i)
                if not (" " <= ch <= "~"): raise LexError("CE-LEX-5", i)
                out.append(ord(ch)); j += 1
            toks.append(("bytes", tuple(out))); i = j
        elif c.isascii() and (c.isalpha() or c == "_"):
            j = i
            while j < n and s[j].isascii() and (s[j].isalnum() or s[j] == "_"):
                j += 1
            w = s[i:j]
            toks.append(("kw" if w in KEYWORDS else "_" if w == "_" else "id", w)); i = j
        elif s[i:i+3] in PUNCT3:
            toks.append(("p", s[i:i+3])); i += 3
        elif s[i:i+2] in PUNCT2:
            toks.append(("p", s[i:i+2])); i += 2
        elif c in PUNCT1:
            toks.append(("p", c)); i += 1
        else:
            raise LexError("CE-LEX-2", i)
    return toks

def header(data):
    meta = {}
    for line in data.decode("utf-8", "replace").lstrip("﻿").splitlines():
        m = re.match(r"// (\w+): (.*)", line)
        if not m: break
        meta[m.group(1)] = m.group(2)
    return meta

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[1])
    conf = repo / "conformance"
    ok = True
    tests = sorted(p for p in conf.glob("*/[a-z][a-z][a-z]-*") )
    for t in tests:
        files = ([t / f for f in (t / "files.txt").read_text().split()] if (t / "files.txt").exists() else sorted(t.glob("*.card"))) if t.is_dir() else [t]
        meta = header(files[0].read_bytes())
        got = "ok"
        for f in files:
            try:
                lex(f.read_bytes())
            except LexError as e:
                got = "compile-error " + e.cls; break
        exp = meta["expect"]
        lexical_expect = exp if "CE-LEX" in exp else "ok"   # CE-SYN cases must lex cleanly
        status = "PASS" if got == lexical_expect else "FAIL"
        ok &= status == "PASS"
        print(f"{status} {t.relative_to(conf)}: expect {exp}, lexer {got}")
    # DN code blocks
    dn = (repo / "plans_and_notes" / "card-language-design-notes.md").read_text(encoding="utf-8")
    pn = (repo / "plans_and_notes" / "cardlang-platform-notes.md").read_text(encoding="utf-8")
    bad = 0
    for name, doc in (("DN", dn), ("PN", pn)):
        for k, block in enumerate(re.findall(r"```text\n(.*?)```", doc, re.S)):
            try:
                lex(block.encode())
            except LexError as e:
                bad += 1
                ln = block[:e.pos].count("\n")
                print(f"{name} block {k}: {e.cls} at {block.splitlines()[ln]!r}")
    print("ALL TESTS PASS" if ok else "SOME TESTS FAIL", "| notes blocks failing:", bad)
