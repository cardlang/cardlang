"""The front end: the lexer, the checkers of each chapter, the Annex A grammar, and diagnostics (was the checkers folder in tools/).

Each checker module is also the runner of its chapter's conformance tests: `python -m cardlang.front.expcheck <repo>`.
"""
