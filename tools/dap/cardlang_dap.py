"""A launcher. The debug adapter is `cardlang.dap.adapter`, installed as the command `cardlang-dap`.

The installed VS Code extension (0.1.1) runs this path. PR6 moves the extension to the installed commands and removes
this launcher (PR5 S2).
"""
from cardlang.dap.adapter import main
main()
