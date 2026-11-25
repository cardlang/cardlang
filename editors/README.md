# Editor support

[`vscode/`](vscode/README.md) is the CardLang extension for VS Code. It gives highlighting, errors as you type, go to definition, completion, building and running applets, and a debugger. It runs the `cardlang` package's commands (`clc`, `cardlang-lsp` and `cardlang-dap`), so another editor that speaks the Language Server Protocol or the Debug Adapter Protocol can use the same ones. [`vscode/DEVELOPMENT.md`](vscode/DEVELOPMENT.md) explains how the extension is built, tested and released.
