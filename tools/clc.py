"""A launcher. clc, the CardLang command line, is `cardlang.cli`, installed as the command `clc`.

The installed VS Code extension (0.1.1) runs this path. PR6 moves the extension to the installed commands and removes
this launcher (PR5 S2).
"""
from cardlang.cli import entry
entry()
