# PR6 — The extension into `editors/vscode/`: detailed sub-plan

Planned 2026-11-22, the sixth work package of PR0. The VS Code extension moves to `editors/vscode/`, and it runs the installed commands of the `cardlang` package (PR5) instead of scripts by path. The launchers that PR5 left in `tools/`, and the `vmproto` alias in `clc`, then go, and `tools/` disappears.

## 1. What there is now

- **`tools/vscode/`:**
  - the extension (`extension.js`, `package.json`, the grammars, the snippets and the language configurations);
  - its README;
  - `check_extension.py`, run by `run_checks`;
  - `install.py`, which links the folder into VS Code for development;
  - the packaged `cardlang.vsix`, and `node_modules/` with `vscode-languageclient` and `@vscode/vsce`. Both of these are ignored by git.
- **How it runs the tools:**
  - it runs `uv run --project <repo> python -I <repo>/<script>` for three scripts: `tools/clc.py` for its tasks, `tools/lsp/cardlang_lsp.py` for the language server, and `tools/dap/cardlang_dap.py` for the debugger;
  - it finds the repository as the setting `cardlang.toolsPath`, or else a workspace folder, or one of its parents, that holds `tools/clc.py`.
- **Installed in VS Code:** version 0.1.1, from the `.vsix`. It is a copy, not a link, so moving the folder does not break it. It keeps running the old paths until it is reinstalled.
- **Left by PR5 for this work package:**
  - the three launchers;
  - `clc run --backend vmproto`, an alias that 0.1.1's default setting still sends.

## 2. The work

1. **The move:**
   - `git mv tools/vscode editors/vscode`;
   - the ignored `node_modules/` moves with the folder as a plain file move, so nothing is downloaded again;
   - `tools/` then holds only the launchers, which go in step 4.
2. **The extension runs the installed commands (X1):**
   - its tasks run `uv run --project <repo> clc <args>`;
   - the language server is `uv run --project <repo> cardlang-lsp`;
   - the debugger is `uv run --project <repo> cardlang-dap`;
   - `pythonArgs` and every script path go.
3. **How it finds the repository (X2):** it looks for a folder whose `pyproject.toml` names the project `cardlang`, in the workspace or a folder above it. The setting is renamed `cardlang.repository`, and its description, the warning and the README say what it now points at.
4. **The leftovers:**
   - the three launchers are removed, and `tools/` with them;
   - so is `clc`'s `vmproto` alias.
5. **`check_extension.py`** stays with the extension (X4), and reads the extension's files from its new folder. `run_checks` runs it from `editors/vscode/`. Its check that the debugger is wired up looks for `cardlang-dap` in `package.json`'s scripts, not for a file in `tools/`.
6. **The version and reinstalling (X3):** the `.vsix` is rebuilt with `npm run package`, which uses the `vsce` already in `node_modules`. It is then installed into your VS Code with `code --install-extension editors/vscode/cardlang.vsix --force`, after you confirm.
7. **References:**
   - `layout.MOVED` gains `tools/vscode` and the launchers;
   - the current documents, among them the extension's README, the top-level readme, the package README and `tests/README.md`, are rewritten;
   - the extension README's "How it is built" table, its install steps, and its description of how the tools are found are updated by hand;
   - `layout.tools` and `tools` in `TOP_LEVEL` go, and `editors` comes in.
8. **Checks:**
   - `run_checks` passes;
   - the link check passes;
   - `check_extension` finds no script paths in `extension.js`;
   - after reinstalling, you open the repository in VS Code and try what step 8 of TL1 listed: highlighting, errors as you type, go to definition, completion, Build, Run Scenario and Debug Scenario on both applets.

**Done when:**
- the extension is in `editors/vscode/` and runs `clc`, `cardlang-lsp` and `cardlang-dap`;
- `tools/` is gone;
- the reinstalled extension works in VS Code;
- `run_checks` passes.

## 3. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| X1 | How the extension starts the tools | (a) the installed commands through uv: `uv run --project <repo> clc …`, `cardlang-lsp` and `cardlang-dap`; (b) modules through uv: `uv run --project <repo> python -I -m cardlang.cli`; (c) commands on the PATH, without uv | (a). uv picks the repository's environment, and the extension no longer knows any file inside the package. (c) would need you to activate the environment before starting VS Code |
| X2 | How it finds the repository, and the setting's name | (a) a `pyproject.toml` naming `cardlang`, in the workspace or above it, and rename the setting `cardlang.repository`; (b) the same search, keeping the name `cardlang.toolsPath` | (a). The setting no longer points at a tools folder. Pre-alpha, so the rename needs no compatibility, but if you have set `toolsPath`, set the new one |
| X3 | The extension's version, which VS Code shows | (a) keep 0.1.1, and reinstall with `--force`; (b) bump it to 0.1.2 | (a). It follows the pre-alpha rule of no version changes. `--force` replaces an installed copy of the same version |
| X4 | Where `check_extension.py` lives | (a) with the extension, in `editors/vscode/`, like each example's `check.py`; (b) in `tests/`, with the other tool checks | (a). The extension folder stays self-contained, and its `.vscodeignore` already leaves the check out of the `.vsix` |

**Decided (user, 2026-11-22):** X1 (a) the installed commands through uv, X2 (a) the `pyproject.toml` search and the setting renamed `cardlang.repository`, X3 (a) keep 0.1.1 and reinstall with `--force`, and X4 (a) the check stays with the extension. All four are as recommended.
