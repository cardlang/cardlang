"""Pygments lexers for CardLang and its scenario files, used by the guide's site (and by any Pygments user).

The keywords come from the reference lexer, and the intrinsics from the expression checker, so the highlighting
cannot drift from the language. The scenario steps are the scenario runner's; `tests/guidecheck.py` checks them
against the VS Code extension's scenario grammar, which its own check compares with the runner.

Registered in pyproject.toml as the Pygments lexers `cardlang` and `scenario`.
"""
from pygments.lexer import RegexLexer, words, bygroups
from pygments.token import Comment, Keyword, Name, Number, Operator, Punctuation, String, Text, Whitespace

from cardlang.front.lexcheck import KEYWORDS
from cardlang.front import expcheck

TYPES = ("u8", "u16", "u32", "i8", "i16", "i32", "bool")
CONSTANTS = ("true", "false")
DECLARATIONS = ("function", "command", "struct", "enum", "errors", "const", "var", "persistent", "session")
INTRINSICS = tuple(sorted(expcheck.CHECKED2 | expcheck.WRAP | expcheck.TYARG
                          | {"checked_neg", "encode_be", "encode_le", "equal", "compare", "fill"}))
STEPS = ("install", "power_on", "session_start", "session_end", "reset", "select", "deselect", "interrupt", "seed",
         "command")


class CardLangLexer(RegexLexer):
    """CardLang source files (`.card`)."""
    name = "CardLang"
    aliases = ["cardlang", "card"]
    filenames = ["*.card"]

    tokens = {
        "root": [
            (r"\s+", Whitespace),
            (r"//[^\n]*", Comment.Single),
            (r"/\*", Comment.Multiline, "comment"),
            (r'b"', String, "bytes"),
            (r"0x[0-9a-fA-F](?:_?[0-9a-fA-F])*", Number.Hex),
            (r"0b[01](?:_?[01])*", Number.Bin),
            (r"[0-9](?:_?[0-9])*", Number.Integer),
            (words(CONSTANTS, suffix=r"\b"), Keyword.Constant),
            (words(TYPES, suffix=r"\b"), Keyword.Type),
            (words(DECLARATIONS, suffix=r"\b"), Keyword.Declaration),
            (words(tuple(sorted(KEYWORDS - set(CONSTANTS) - set(DECLARATIONS))), suffix=r"\b"), Keyword),
            (words(INTRINSICS, suffix=r"\b"), Name.Builtin),
            (r"\bcard\b", Name.Builtin.Pseudo),
            (r"([A-Za-z_][A-Za-z0-9_]*)(\s*)(?=\()", bygroups(Name.Function, Whitespace)),
            (r"[A-Z][A-Za-z0-9_]*", Name.Class),
            (r"[A-Za-z_][A-Za-z0-9_]*", Name),
            (r"->|=>|\.\.|<<=|>>=|[-+*/%&|^]=|==|!=|<=|>=|<<|>>|[-+*/%&|^~<>=!]", Operator),
            (r"[{}()\[\];:,.]", Punctuation),
        ],
        "comment": [
            (r"[^*/]+", Comment.Multiline),
            (r"\*/", Comment.Multiline, "#pop"),
            (r"[*/]", Comment.Multiline),
        ],
        "bytes": [
            (r'\\(?:x[0-9a-fA-F]{2}|["\\])', String.Escape),
            (r'"', String, "#pop"),
            (r'[^"\\\n]+', String),
        ],
    }


class ScenarioLexer(RegexLexer):
    """Scenario files: the steps that drive an applet, and the outcomes they expect."""
    name = "CardLang scenario"
    aliases = ["scenario"]
    filenames = ["*.scenario"]

    tokens = {
        "root": [
            (r"#[^\n]*", Comment.Single),
            (r"\s+", Whitespace),
            (r"(expect)(\s+)(ok|err|trap|sw|raw|none)\b", bygroups(Keyword, Whitespace, Keyword.Type)),
            (r"\b(app|platform|capacity)\b", Keyword.Type),
            (words(STEPS, prefix=r"^\s*", suffix=r"\b"), Keyword),
            (r"\b[0-9a-fA-F]{2}\b", Number.Hex),
            (r"[0-9]+", Number.Integer),
            (r"[A-Z][A-Z_-]*", Name.Constant),
            (r"[A-Za-z_][A-Za-z0-9_]*", Name),
            (r".", Text),
        ],
    }
