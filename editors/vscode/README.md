# CardLang for VS Code

Write, build, run and debug CardLang smart-card applets in VS Code. The language server, the build tools and the
debug adapter are commands of the `cardlang` package, run through `uv`. The extension carries that package and sets it
up on first use, or uses the CardLang repository's when one is open.

New to CardLang? The first chapter of **[the CardLang Guide](https://cardlang.github.io/cardlang/01-getting-started/)** installs the tools, and builds, runs and debugs a first applet with this extension.

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

- **VS Code 1.91 or later.** Nothing else: the extension offers to set up its toolchain (see below).
- **Node.js and npm,** only to develop or package the extension itself.

## The toolchain

The extension runs the commands `clc`, `cardlang-lsp` and `cardlang-dap` of the `cardlang` package, from one of two places:

- **The CardLang repository,** when it is open in the workspace (the folder whose `pyproject.toml` names the `cardlang` project, or a folder above the workspace), or when `cardlang.repository` names it. The extension runs `uv run --project <repository>`, so the repository's own environment is used, and kept in step with it.
- **The toolchain it carries,** otherwise. The `.vsix` holds the package and the few specification and platform files it reads while it runs. The first time an applet is opened, the extension offers a one-time setup:
  1. it downloads the [uv](https://docs.astral.sh/uv/) release pinned in `uv.json` for your system from uv's GitHub releases, checks it against the SHA-256 pinned there, and keeps it in VS Code's storage for the extension;
  2. uv installs the package into an environment in the same storage, one for each version of the extension, with a Python if the computer has none (and `cffi` from PyPI);
  3. a smoke test runs `clc`, and the language server starts.

  "Not Now" leaves highlighting and snippets working, and the offer doesn't come back by itself. **CardLang: Set Up Toolchain** runs the setup at any time, and any command that needs the toolchain offers it too. Progress and errors go to the **CardLang** output channel.

If `cardlang.uvPath` names a uv, the extension uses it for everything and downloads none. Without it, the extension uses its own uv once it has one, else `uv` on the `PATH`. The C VM backend (`cardlang.scenarioBackend: cvm`) needs the repository, with the C VM built.

## Installing

**From a release,** for normal use: download `cardlang-<version>.vsix` from the repository's [Releases](https://github.com/cardlang/cardlang/releases) and install it:

```bash
code --install-extension cardlang-<version>.vsix
```

A newer release installs over an older one, and sets up its own environment the first time it starts; the downloaded uv is kept.

**For development,** VS Code loads the extension straight from the repository:

```bash
cd editors/vscode && npm install
uv run python -I editors/vscode/install.py
```

Then run **Developer: Reload Window**. After any change to the extension, reload again. `install.py --remove` removes the link.

**From a package you build,** for trying a change. Build it, remove a development link if you made one, and install it:

```bash
cd editors/vscode && npm install && npm run package
uv run python -I editors/vscode/install.py --remove
code --install-extension editors/vscode/cardlang.vsix --force
```

`npm run package` first runs `bundle.py`, which copies the toolchain into `editors/vscode/toolchain/` (git ignores it), and then writes `editors/vscode/cardlang.vsix`, about 650 KB, which holds the extension, `vscode-languageclient` and the toolchain. `--force` replaces an installed copy of the same version.

**The uv pin** is `uv.json`. To move to another uv release, run `uv run python -I editors/vscode/pin_uv.py <version>`, which reads the SHA-256 that uv publishes for each archive, and review the change.

**The self-test,** `selftest.js`, runs the setup outside VS Code against an unpacked `.vsix`, then uses `clc`, the language server and the debug adapter from the bundled toolchain alone:

```bash
node editors/vscode/selftest.js <unpacked .vsix>/extension
```

It downloads the pinned uv into a new temporary folder.

## Releasing

GitHub builds and checks the extension on every push or pull request that touches it, or the toolchain it checks against (`.github/workflows/vscode-extension.yml`); each run keeps the `.vsix` as a downloadable artifact. To publish a release:

1. Raise `version` in `package.json` (and in `package-lock.json`, with `npm install`), and commit it to `main`.
2. Tag that commit `vscode-v<version>` and push the tag:

   ```bash
   git tag vscode-v0.2.0
   git push origin vscode-v0.2.0
   ```

The workflow builds `cardlang-<version>.vsix`, runs the self-test on Windows, macOS and Linux, checks that the tag matches `package.json`'s version, and creates the GitHub Release with the `.vsix` attached.

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
| **CardLang: Check Applet** | Runs every check of the specification | `uv run clc check examples/fido2` |
| **CardLang: Build Applet** (the package icon) | Checks, then writes `build/<name>.clvm` in the applet's directory and prints the image's figures | `uv run clc build examples/fido2` |
| | Lists the code, with source lines and variable scopes | `uv run clc disasm examples/fido2/build/fido2.clvm` |

## Scenarios

A scenario drives the applet the way a terminal would. It has one step per line, and `#` starts a comment:

```text
install
power_on
select
expect sw 9000
command 80 10 00 00 04        # a command's bytes, in hex; "capacity n" sets the response buffer
expect sw 9000                # or: expect ok <bytes>, expect ok length <n>, expect err app <code>, expect err platform <Member>, expect trap <KIND>
```

The other steps are `session_start`, `session_end`, `reset`, `deselect`, `seed <hex>` (the test random generator) and `interrupt` (a power loss at the next commit). The format is described in `src/cardlang/harness/README.md`.

Scenario files are named `scenario.txt` or `*.scenario`. **CardLang: Run Scenario** (the play icon) runs one and prints every step, its outcome, and each `expect`. On `pyvm`, a trap is shown with the statement where it happened. The `cardlang.scenarioBackend` setting chooses what runs it:
- `pyvm`, the Python VM;
- `interp`, the reference interpreter;
- `cvm`, the C VM, which must be built first (`vm/c/README.md` in the repository).

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

The debugger runs the applet on the Python VM (`pyvm`), which executes exactly what the C VM does: both pass the same tests.

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `cardlang.repository` | empty | The CardLang repository. Empty: found from the workspace, else the toolchain the extension carries |
| `cardlang.uvPath` | empty | The uv executable. Empty: the extension's own uv, else `uv` on the `PATH` |
| `cardlang.scenarioBackend` | `pyvm` | Where Run Scenario runs the applet |

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
- **The debugger** runs on the Python VM only. The C VM has no debug hook yet.

## How it is built

| Part | Where |
|---|---|
| The extension: grammars, snippets, commands, the language client and the debugger contribution | `editors/vscode/` (plain JavaScript, using `vscode-languageclient`) |
| The setup of the bundled toolchain | `editors/vscode/toolchain.js`, with `uv.json`, `bundle.py` and `pin_uv.py` |
| The language server: diagnostics, semantic tokens, definitions and completion | `cardlang.lsp`: `server.py`, `semantic.py`, `complete.py` |
| The debug adapter | `cardlang.dap.adapter` |
| The JSON-RPC framing both use | `src/cardlang/jsonrpc.py` |
| The command line | `cardlang.cli`, the command `clc` |
| Diagnostics with positions | `src/cardlang/front/diagnose.py` |
| Debug information in images (IMG-10) | `src/cardlang/bytecode/debuginfo.py` |

**The checks** are rows of `tests/run_checks.py`:
- `poscheck.py`: diagnostics and their positions;
- `clc_check.py`: the command line;
- `lsp_check.py` and `semantic_check.py`: the language server;
- `check_extension.py`: the extension's static parts, the uv pin and the bundle's file list;
- `debug_check.py`: the image's debug information;
- `dap_check.py`: the debug adapter.

The extension's workflow also runs `selftest.js` on every system, on the packaged `.vsix`.
