# Working on the VS Code extension

This is the extension's technical side: how it finds and sets up the toolchain, how to run it from the repository, how it is packaged, tested and released, and where each part lives. For what the extension does for a user, see [README.md](README.md).

The extension is plain JavaScript with no build step, using `vscode-languageclient`. You need Node.js and npm to work on it or package it.

## The toolchain

The extension runs the commands `clc`, `cardlang-lsp` and `cardlang-dap` of the `cardlang` package, through uv, from one of two places.

The first is the CardLang repository, when it's open in the workspace (the folder whose `pyproject.toml` names the `cardlang` project, or a folder above the workspace), or when `cardlang.repository` names it. The extension then runs `uv run --project <repository>`, so the repository's own environment is used and kept in step with it.

The second is the toolchain the extension carries. The `.vsix` holds the package and the few specification and platform files the package reads while it runs, laid out like the repository (`bundle.py` lists them). The first time an applet is opened without a repository, the extension offers a one-time setup, done by `toolchain.js`:

1. It downloads the [uv](https://docs.astral.sh/uv/) release pinned in `uv.json` for the user's system from uv's GitHub releases, checks it against the SHA-256 pinned there, and keeps it in VS Code's storage for the extension. Linux uses uv's static musl builds, which run on any distribution.
2. uv installs the package into an environment in the same storage, one per version of the extension, with a Python if the computer has none, and `cffi` from PyPI. Nothing is written inside the extension's own folder.
3. A smoke test runs `clc`, and the language server starts.

"Not Now" leaves highlighting and snippets working, and the offer doesn't come back by itself. **CardLang: Set Up Toolchain**, or any command that needs the toolchain, offers it again. A repository opened on a computer without uv also gets the offer, and is then run with the extension's own uv. Progress and errors go to the **CardLang** output channel.

If `cardlang.uvPath` names a uv, the extension uses it and downloads none. Otherwise it uses its own uv once it has one, else `uv` on the `PATH`. The C VM backend (`cardlang.scenarioBackend: cvm`) needs the repository, with the C VM built.

## Running it from the repository

VS Code can load the extension straight from the repository:

```bash
cd editors/vscode && npm install
uv run python -I editors/vscode/install.py
```

Then run **Developer: Reload Window**, and reload again after every change. `install.py --remove` removes the link.

To try a packaged build instead, build it, remove a development link if you made one, and install it:

```bash
cd editors/vscode && npm install && npm run package
uv run python -I editors/vscode/install.py --remove
code --install-extension editors/vscode/cardlang.vsix --force
```

`npm run package` first runs `bundle.py`, which copies the toolchain into `editors/vscode/toolchain/` (git ignores it), and then writes `editors/vscode/cardlang.vsix`, about 650 KB, with the extension, `vscode-languageclient` and the toolchain. `--force` replaces an installed copy of the same version.

## The uv pin

`uv.json` names uv's archive and its SHA-256 for each supported system. To move to another uv release, run the script below, which reads the SHA-256 that uv publishes beside each archive, and review the change:

```bash
uv run python -I editors/vscode/pin_uv.py <version>
```

## Testing

`check_extension.py`, a row of `tests/run_checks.py`, checks the extension's static parts. The grammars, keywords and scenario steps must match the language, the extension may start only the package's own commands, the uv pin must cover every system, and the bundle may list only files that exist.

`selftest.js` runs the setup outside VS Code against an unpacked `.vsix`, then uses `clc`, the language server and the debug adapter from the bundled toolchain alone. It downloads the pinned uv into a new temporary folder:

```bash
node editors/vscode/selftest.js <unpacked .vsix>/extension
```

The rest of the tools are checked by their own rows of `tests/run_checks.py`:

| Check | What it covers |
|---|---|
| `poscheck.py` | Diagnostics and their positions |
| `clc_check.py` | The command line |
| `lsp_check.py`, `semantic_check.py` | The language server |
| `debug_check.py` | The debug information in images |
| `dap_check.py` | The debug adapter |

## Releasing

GitHub builds and checks the extension on every push or pull request that touches it, or the toolchain it carries (`.github/workflows/vscode-extension.yml`), and keeps each `.vsix` as a downloadable artifact of the run. It also runs the self-test on Windows, macOS and Linux. To publish a release:

1. Raise `version` in `package.json` (and in `package-lock.json`, with `npm install`), and commit it to `main`.
2. Tag that commit `vscode-v<version>` and push the tag:

   ```bash
   git tag vscode-v0.2.0
   git push origin vscode-v0.2.0
   ```

The workflow builds `cardlang-<version>.vsix`, runs the self-test, checks that the tag matches `package.json`'s version, and creates the GitHub Release with the `.vsix` attached.

## Where things are

| Part | Where |
|---|---|
| Grammars, snippets, commands, the language client and the debugger contribution | `editors/vscode/`: `package.json`, `extension.js`, `syntaxes/`, `snippets/` |
| The setup of the bundled toolchain | `editors/vscode/toolchain.js`, with `uv.json`, `bundle.py` and `pin_uv.py` |
| The language server: diagnostics, semantic tokens, definitions and completion | `cardlang.lsp`: `server.py`, `semantic.py`, `complete.py` |
| The debug adapter | `cardlang.dap.adapter` |
| The JSON-RPC framing both use | `src/cardlang/jsonrpc.py` |
| The command line | `cardlang.cli`, the command `clc` |
| Diagnostics with positions | `src/cardlang/front/diagnose.py` |
| Debug information in images (IMG-10) | `src/cardlang/bytecode/debuginfo.py` |

The scenario format is described in `src/cardlang/harness/README.md`, and for users in chapter 9 of the guide.
