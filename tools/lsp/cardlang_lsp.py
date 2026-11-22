"""A launcher. The language server is `cardlang.lsp.server`, installed as the command `cardlang-lsp`.

The installed VS Code extension (0.1.1) runs this path. PR6 moves the extension to the installed commands and removes
this launcher (PR5 S2).
"""
from cardlang.lsp.server import main
main()
