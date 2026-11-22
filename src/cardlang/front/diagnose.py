"""Diagnostics for a CardLang program, with positions and messages.

check(files) runs the full reference front end (the lexer and every checker, as `pltcheck` composes them) and
returns a list of diagnostics, each a dict: code, message, file, line, column. The front end stops at its first
error, so the list has at most one entry; an empty list means the program is valid.

- **Positions:** see srcpos.py. A lexical error has an exact position. A checker error is placed at the token the
  checker was examining when it found the error, which is on the offending construct or just after it.
- **Messages:** the one-line meaning of each code, read from the index of the specification (language/spec/00-index.md).
- **Unexpected input:** a checker that fails on input it does not expect reports CE-SYN-1, a syntax error, at the
  last token examined. The checkers assume grammatical input; Annex A's recognizer is the authority on syntax.

Usage, for a quick look:
    uv run python -I -m cardlang.front.diagnose <file.card> ...
"""
import sys, pathlib, re
HERE = pathlib.Path(__file__).resolve().parent
from cardlang.front.lexcheck import lex, LexError, header
from cardlang import layout
from cardlang.front import srcpos, consteval, expcheck, pltcheck, typecheck, grammar

ROOT = layout.at().root
_messages = None

def messages():
    """{code: meaning} from the specification's index of errors."""
    global _messages
    if _messages is None:
        _messages = {}
        index = layout.at(ROOT).spec / "00-index.md"
        if index.exists():
            for m in re.finditer(r"^\| (CE-[A-Z]+-\d+) \| ([^|]+) \|", index.read_text(encoding="utf-8"), re.M):
                _messages[m.group(1)] = m.group(2).strip()
    return _messages

def diagnostic(code, where, detail=None):
    file, line, col = where if where else (None, None, None)
    msg = messages().get(code, "")
    if detail: msg = f"{msg} ({detail})" if msg else detail
    return {"code": code, "message": msg, "file": file, "line": line, "column": col}

_grammar = None

def check(files, binding=None, kind="application", sources=None):
    """Diagnostics for a program made of these files (paths), as an application unless kind is "fragment".
    sources maps a file's name, as str(path), to text that replaces the file's contents: an editor's unsaved text.
    The stages: lexical structure (chapter 2); Annex A's grammar; types (chapter 4); the composed checker of
    chapters 3 and 6 to 12 and Annex B; then constant evaluation (chapter 5), whose CE-CEX errors the composed
    checker does not detect."""
    global _grammar
    srcpos.reset()
    names = [str(f) for f in files]; per_file = []
    for f, name in zip(files, names):
        data = sources[name].encode("utf-8") if sources and name in sources else pathlib.Path(f).read_bytes()
        try: per_file.append(lex(data, name))
        except LexError as e: return [diagnostic(e.cls, e.where)]
    if _grammar is None: _grammar = grammar.load_grammar(ROOT)
    for name, ft in zip(names, per_file):
        derived, at = _grammar.recognize(ft)
        if not derived:
            where = ft[at].pos if at < len(ft) else ((name,) + _end_of(ft))
            return [diagnostic("CE-SYN-1", where)]
    toks = sum(per_file, [])
    srcpos.set_declarations(toks)
    def located(exc, detail=None):
        where = srcpos.position_of(exc)
        if where is not None and where[0] not in names: where = None     # inside the prelude or the scaffold
        return [diagnostic(str(exc), where, detail)]
    errs, _ = typecheck.check_located(pltcheck.PRELUDE + toks)              # with the Base Profile's types
    if errs:
        code, tok = errs[0]
        return [diagnostic(code, tok.pos if getattr(tok, "pos", None) and tok.pos[0] in names else None)]
    try:
        pltcheck.run(toks, kind, binding)
    except (expcheck.CE, consteval.CE) as e:
        return located(e)
    except pltcheck.ProfileError as e:
        return located(e, "a Base Profile rule")
    except RecursionError:
        raise
    except Exception as e:                                    # input the checkers do not expect: a syntax error
        r = located(e, f"{type(e).__name__} in the checker"); r[0]["code"] = "CE-SYN-1"
        r[0]["message"] = messages().get("CE-SYN-1", "") + f" ({type(e).__name__} in the checker)"; return r
    # Chapter 5 last: its evaluator checks what the composed checker does not (CE-CEX). It is written for constant
    # declarations, so a failure of its own on other input is not a diagnostic.
    srcpos.reset()
    try: consteval.run(pltcheck.PRELUDE + toks)
    except consteval.CE as e: return located(e)
    except RecursionError: raise
    except Exception: pass
    return []

def _end_of(toks):
    return (toks[-1].pos[1], toks[-1].pos[2] + 1) if toks else (1, 1)

def format_diagnostic(d):
    where = f"{d['file']}:{d['line']}:{d['column']}" if d["file"] else "<unknown position>"
    return f"{where}: {d['code']}: {d['message']}"

if __name__ == "__main__":
    files = sys.argv[1:]
    meta = header(pathlib.Path(files[0]).read_bytes()) if files else {}
    ds = check(files, meta.get("binding"), meta.get("kind", "application"))
    for d in ds: print(format_diagnostic(d))
    print("ok" if not ds else "", end="")
    sys.exit(1 if ds else 0)
