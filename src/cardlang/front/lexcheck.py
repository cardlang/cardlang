"""The reference lexer, written from chapter 2 of the specification."""
import re, sys, pathlib
from cardlang import layout

class Tok(tuple):
    """A (kind, value) token with its source position."""
    def __new__(cls, kind_value, pos):
        t = tuple.__new__(cls, kind_value); t.pos = pos; return t

class Lines:
    """Converts character offsets of one source text to (line, column)."""
    def __init__(self, text):
        self.starts = [0] + [k + 1 for k, ch in enumerate(text) if ch == "\n"]
    def at(self, i):
        import bisect
        line = bisect.bisect_right(self.starts, i)
        return line, i - self.starts[line - 1] + 1


PUNCT3 = ["<<=", ">>="]                                       # compound assignment
PUNCT2 = ["..", "->", "=>", "==", "!=", "<=", ">=", "<<", ">>", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="]
PUNCT1 = list("{}()[];:,.=<>+-*/%~&|^")
KEYWORDS = set("""abort and attempt break command const continue else enum Err errors false for function
if in inout match not Ok or persistent ref require return session struct transaction true var while wipe ignore""".split())
LIT = re.compile(r"(?:[0-9](?:_?[0-9])*|0x[0-9a-fA-F](?:_?[0-9a-fA-F])*|0b[01](?:_?[01])*)\Z")

class LexError(Exception):
    """A lexical error: cls is its code, pos its character offset; where is (file, line, column)."""
    def __init__(self, cls, pos, where=None): super().__init__(cls); self.cls, self.pos, self.where = cls, pos, where

def lex(data: bytes, file=None):
    """The tokens of one source file, as Tok tuples carrying (file, line, column)."""
    try:
        s = data.decode("utf-8")
    except UnicodeDecodeError as e:
        nl = b"\n"
        line = data[:e.start].count(nl) + 1
        raise LexError("CE-LEX-1", e.start, (file, line, e.start - (data.rfind(nl, 0, e.start) + 1) + 1))
    if s.startswith("﻿"):
        s = s[1:]
    i, n, toks = 0, len(s), []
    lines = Lines(s)
    def add(kind_value): toks.append(Tok(kind_value, (file,) + lines.at(i)))
    def fail(cls, at): raise LexError(cls, at, (file,) + lines.at(at))
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
                fail("CE-LEX-3", i)
            i = j + 2
        elif c.isascii() and c.isdigit():
            j = i
            while j < n and s[j].isascii() and (s[j].isalnum() or s[j] == "_"):
                j += 1
            run = s[i:j]
            if not LIT.match(run):
                fail("CE-LEX-4", i)
            add(("int", run)); i = j
        elif s.startswith('b"', i):                             # a byte-string literal
            j = i + 2; out = []
            while True:
                if j >= n or s[j] in "\r\n": fail("CE-LEX-5", i)
                ch = s[j]
                if ch == '"': j += 1; break
                if ch == "\\":
                    esc = s[j + 1:j + 2]
                    if esc in ('"', "\\"): out.append(ord(esc)); j += 2; continue
                    if esc == "x" and re.fullmatch(r"[0-9a-fA-F]{2}", s[j + 2:j + 4] or ""):
                        out.append(int(s[j + 2:j + 4], 16)); j += 4; continue
                    fail("CE-LEX-5", i)
                if not (" " <= ch <= "~"): fail("CE-LEX-5", i)
                out.append(ord(ch)); j += 1
            add(("bytes", tuple(out))); i = j
        elif c.isascii() and (c.isalpha() or c == "_"):
            j = i
            while j < n and s[j].isascii() and (s[j].isalnum() or s[j] == "_"):
                j += 1
            w = s[i:j]
            add(("kw" if w in KEYWORDS else "_" if w == "_" else "id", w)); i = j
        elif s[i:i+3] in PUNCT3:
            add(("p", s[i:i+3])); i += 3
        elif s[i:i+2] in PUNCT2:
            add(("p", s[i:i+2])); i += 2
        elif c in PUNCT1:
            add(("p", c)); i += 1
        else:
            fail("CE-LEX-2", i)
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
    conf = layout.at(repo).conformance
    from cardlang.front import project
    ok = True
    tests = sorted(p for p in conf.glob("*/[a-z][a-z][a-z]-*") )
    for t in tests:
        files = project.program_files(t)
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
    dn = (layout.at(repo).design_notes).read_text(encoding="utf-8")
    pn = (layout.at(repo).platform_notes).read_text(encoding="utf-8")
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
