# CardLang for VS Code

Write, build, run and debug CardLang smart-card applets in VS Code. The extension is a thin client: the language
server, the build tools and the debug adapter are the Python tools of the CardLang repository, run through `uv`.

## Features

| | |
|---|---|
| **Highlighting** | Keywords, literals, byte strings, comments and operators in `.card` files and in scenario files |
| **Colouring by meaning** | Each name coloured by what it is: function, structure, enum and member, parameter, local, field, intrinsic, `card` API, and globals marked `static` (`session`) or `persistent` |
| **Errors as you type** | The reference checkers run on your unsaved text, across every file of the applet, and report each error with its code (`CE-EXP-4`) and the specification's message |
| **Go to definition** | F12, Ctrl+click and Peek (Alt+F12) on any name, across files, including the Base Profile's types |
| **Completion** | After `card.`: the Base Profile's namespaces and APIs, with signatures and documentation, inserting each argument's `ref` or `inout`. After `Owner.`: the members of an enum or error set |
| **Snippets** | `command`, `function`, `if`, `while`, `for`, `match`, `require`, `attempt`, `transaction`, `errors`, `struct`, `enum`, `persistent`, `session` |
| **Build and run** | **CardLang: Build Applet**, **Check Applet** and **Run Scenario**, with errors in the Problems panel |
| **Debugging** | Run a scenario against the applet and stop at breakpoints in `.card` or scenario files; step over, in and out; see the call stack, parameters, locals, globals, and the request and response bytes; stop where a trap happens or an `expect` fails |

## Requirements

- **The CardLang repository,** with its uv environment (`uv sync` once).
- **[uv](https://docs.astral.sh/uv/)** on the `PATH`, or named by the `cardlang.uvPath` setting.
- **VS Code 1.91 or later.**
- **Node.js and npm,** only to develop or package the extension itself.

The extension finds the repository, the folder that holds `tools/clc.py`, in the workspace or in a folder above it. You can also set `cardlang.toolsPath`.

## Installing

**For development,** VS Code loads the extension straight from the repository:

```bash
cd tools/vscode && npm install
uv run python -I tools/vscode/install.py
```

Then run **Developer: Reload Window**. After any change to the extension, reload again. `install.py --remove` removes the link.

**From a package,** for normal use. Build it, remove a development link if you made one, and install it:

```bash
cd tools/vscode && npm install && npm run package
uv run python -I tools/vscode/install.py --remove
code --install-extension tools/vscode/cardlang.vsix
```

`npm run package` writes `tools/vscode/cardlang.vsix`, about 400 KB, which holds the extension and `vscode-languageclient`. The language server, the debugger and the build tools stay in the repository, so the extension still needs it, through `cardlang.toolsPath` or the workspace.

## Applets and projects

An applet is a directory with a `cardlang.json` project file:

```json
{ "name": "wallet", "files": ["constants.card", "accounts.card", "entry.card"], "binding": "iso7816" }
```

- `files` lists the source files in build order.
- `binding` is `iso7816` or `raw`.

A `.card` file listed there is checked as part of the whole applet. A `.card` file outside any project is checked on its own, as an application, or as a fragment if its header says `// kind: fragment`. `examples/fido2` and `examples/piv` are complete applets to try.

## Building

| Command | What it does | The same in a terminal |
|---|---|---|
| **CardLang: Check Applet** | Runs every check of the specification | `uv run python -I tools/clc.py check examples/fido2` |
| **CardLang: Build Applet** (the package icon) | Checks, then writes `build/<name>.clvm` in the applet's directory and prints the image's figures | `uv run python -I tools/clc.py build examples/fido2` |
| | Lists the code, with source lines and variable scopes | `uv run python -I tools/clc.py disasm examples/fido2/build/fido2.clvm` |

## Scenarios

A scenario drives the applet the way a terminal would. It has one step per line, and `#` starts a comment:

```text
install
power_on
select
expect sw 9000
command 80 10 00 00 04        # a command's bytes, in hex; "capacity n" sets the response buffer
expect sw 9000                # or: expect ok <bytes>, expect err app <code>, expect err platform <Member>, expect trap <KIND>
```

The other steps are `session_start`, `session_end`, `reset`, `deselect`, `seed <hex>` (the test random generator) and `interrupt` (a power loss at the next commit). The format is described in `tools/harness/README.md`.

Scenario files are named `scenario.txt` or `*.scenario`. **CardLang: Run Scenario** (the play icon) runs one and prints every step, its outcome, and each `expect`. On `vmproto`, a trap is shown with the statement where it happened. The `cardlang.scenarioBackend` setting chooses what runs it:
- `vmproto`, the prototype VM;
- `interp`, the reference interpreter;
- `cvm-msvc` or `cvm-clang`, the C VM, which `vm/c/build.py` builds first.

## Debugging

Open a scenario and press F5, or click **CardLang: Debug Scenario** (the debug icon). Set breakpoints in the applet's `.card` files, or on scenario lines to stop before a step. To keep a configuration, add it to `.vscode/launch.json`: <!-- linkcheck: ignore -->

```json
{
  "type": "cardlang",
  "request": "launch",
  "name": "Debug getInfo",
  "scenario": "${workspaceFolder}/examples/fido2/getinfo.scenario",
  "program": "${workspaceFolder}/examples/fido2",
  "stopOnEntry": false
}
```

`program` defaults to the scenario's directory.

**What you see when it stops:**
- **The call stack:** each function down to the entry point, then the scenario step at the bottom.
- **Locals:** the parameters and locals in scope. Structures, arrays and views expand into their fields and elements.
- **Globals:** `session`, `persistent` and constant.
- **Hover:** a variable's value.
- **The Debug Console:** every scenario step, its outcome and each `expect`.

**Stepping is by statement.** Step over (F10) stays in the current function, step in (F11) enters calls, and step out (Shift+F11) returns to the caller.

**Exception breakpoints,** in the Breakpoints panel:
- **Traps** stop where a trap happens, with the faulting frame and its variables still intact;
- **Failed expectations** stop at an `expect` that does not match.

The debugger runs the applet on the prototype VM, which executes exactly what the C VM does: both pass the same tests.

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `cardlang.toolsPath` | empty | The CardLang repository. Empty: found from the workspace |
| `cardlang.uvPath` | `uv` | The uv executable |
| `cardlang.scenarioBackend` | `vmproto` | Where Run Scenario runs the applet |

## Colouring persistent state

Themes colour the standard kinds. To make `persistent` globals stand out, add a rule to your settings:

```json
"editor.semanticTokenColorCustomizations": {
  "rules": {
    "variable.persistent": { "foreground": "#d19a66", "fontStyle": "underline" },
    "variable.static": { "fontStyle": "italic" }
  }
}
```

Use **Developer: Inspect Editor Tokens and Scopes** to see a name's kind and modifiers.

## Known limits

- **One error at a time:** the checkers stop at their first error, so each applet shows at most one.
- **Placement:** some errors are placed at the end of their construct; for example, a `match` missing an arm is reported at its closing brace.
- **Missing name rules:** fourteen name rules of chapter 3 have no checker yet. Duplicate names, shadowing, and redeclared intrinsics are not reported.
- **Completion:** it covers the `card` APIs and enum and error-set members. Fields after a variable (`head.`) are not completed yet.
- **The debugger** runs on the prototype VM only. The C VM has no debug hook yet.

## How it is built

| Part | Where |
|---|---|
| The extension: grammars, snippets, commands, the language client and the debugger contribution | `tools/vscode/` (plain JavaScript, using `vscode-languageclient`) |
| The language server: diagnostics, semantic tokens, definitions and completion | `tools/lsp/cardlang_lsp.py`, `semantic.py`, `complete.py` |
| The debug adapter | `tools/dap/cardlang_dap.py` |
| The JSON-RPC framing both use | `tools/lsp/jsonrpc.py` |
| The command line | `tools/clc.py` |
| Diagnostics with positions | `src/cardlang/front/diagnose.py` |
| Debug information in images (IMG-10) | `src/cardlang/bytecode/debuginfo.py` |

**The checks** are rows of `tools/run_checks.py`:
- `poscheck.py`: diagnostics and their positions;
- `clc_check.py`: the command line;
- `lsp_check.py` and `semantic_check.py`: the language server;
- `check_extension.py`: the extension's static parts;
- `debug_check.py`: the image's debug information;
- `dap_check.py`: the debug adapter.

The plan and its history are in `devel/plans/tooling/TL1-vscode-extension.md`.
