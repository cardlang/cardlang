"""Source positions for the front end (TL1 step 1).

A token is still a (kind, value) tuple, as every checker expects, but the lexer makes it a Tok, which also carries
.pos = (file, line, column), both 1-based. The parsers note each token they look at; an error then takes the
position of the token being examined when it was raised, unless it names a token itself (exc.tok).
"""

from cardlang.front.lexcheck import Tok, Lines

_last = [None]

def note(tok):
    """Called by the parsers for the token they are examining."""
    if type(tok) is Tok: _last[0] = tok

def reset(): _last[0] = None

def last(): return _last[0]

def position_of(exc):
    """(file, line, column) for an error: its own token, or the last token examined, or None."""
    tok = getattr(exc, "tok", None)
    if type(tok) is Tok: return tok.pos
    return _last[0].pos if _last[0] is not None else None

def at(exc, tok):
    """The error exc, placed at token tok (when tok is a Tok): for errors found outside the parsers."""
    if type(tok) is Tok: exc.tok = tok
    return exc

DECLARING = {"function", "command", "const", "persistent", "session", "struct", "enum", "errors"}
_decl = {}

def set_declarations(toks):
    """Index the name token of every top-level-style declaration, for errors about a declaration as a whole."""
    _decl.clear()
    for i in range(len(toks) - 1):
        if toks[i][1] in DECLARING and toks[i + 1][0] == "id" and toks[i + 1][1] not in _decl:
            _decl[toks[i + 1][1]] = toks[i + 1]

def decl(name):
    """The token that declares name, or None."""
    return _decl.get(name)
