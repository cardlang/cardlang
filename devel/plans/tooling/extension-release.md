# Building and publishing the VS Code extension on GitHub: plan

Planned 2026-11-22, on the branch `vscode-release`. Today the `.vsix` is built by hand (`npm run package` in `editors/vscode/`), and users must build it themselves. This plan has GitHub build it, check it, and publish it on the repository's Releases page, where anyone can download it and install it with one command.

## 1. What there is now

- **The extension** is plain JavaScript with no build step, in `editors/vscode/`.
  - `package.json` and `package-lock.json` pin its one dependency, `vscode-languageclient`, and its packaging tool, `@vscode/vsce`;
  - `npm run package` writes `cardlang.vsix`, about 400 KB, using `--allow-missing-repository`, because `package.json` names no repository;
  - its version is 0.1.1.
- **Its check,** `editors/vscode/check_extension.py`, needs Python and the `cardlang` package, which is what uv provides.
- **What a user needs to run it:** the `.vsix` is only the client. The language server, the build tools and the debugger are the `cardlang` package, so a user still needs a clone of the repository, with `uv sync` run once. The README's getting-started chapter says so, and has users build the `.vsix` themselves.
- **The repository:** `github.com/cardlang/cardlang`, public, with no `.github/` folder and no workflows yet.

## 2. The work

1. **A workflow,** `.github/workflows/vscode-extension.yml`, on GitHub's Ubuntu runners. It uses only GitHub's own actions (`actions/checkout`, `actions/setup-node`), uv's official `astral-sh/setup-uv`, and the `gh` command that the runners already have. Its steps:
   - **check:** `uv sync`, then `uv run python -I editors/vscode/check_extension.py .`. This checks that the grammars, keywords and scenario steps match the language, and that the extension runs only installed commands;
   - **build:** `npm ci` and `npm run package` in `editors/vscode/`;
   - **publish (R1):** on a release tag, create a GitHub Release and attach the `.vsix`. Otherwise, keep the `.vsix` as a downloadable artifact of the workflow run, for trying out a change.
2. **The version (R2):** the workflow checks that the tag's version equals `package.json`'s, so a release can never carry the wrong number.
3. **`package.json`:**
   - gains `"repository": {"type": "git", "url": "https://github.com/cardlang/cardlang"}`, so `--allow-missing-repository` goes;
   - gains `"homepage"` and `"bugs"`, which the marketplaces and VS Code's extension page link to.
4. **Documentation:**
   - the README's getting-started step 1 becomes "download `cardlang.vsix` from the latest release and run `code --install-extension cardlang.vsix`", with building it yourself kept as the alternative;
   - the extension's README says the same;
   - `devel/README.md`, or the extension's README, says how to cut a release (R2).
5. **Checks:**
   - the workflow runs on this branch through `workflow_dispatch`, or on a pull request, and its artifact installs in VS Code;
   - then a first release is made from `main`, after the branch is merged.

**Not in this plan:** the VS Code Marketplace and Open VSX (R3); running the full `run_checks` on GitHub, which needs Windows runners with MSVC and llvm-mingw.

**Done when:**
- a release tag produces a GitHub Release with `cardlang.vsix` attached;
- every push that touches `editors/` builds and checks the extension;
- the READMEs point users at the Releases page.

## 3. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| R1 | When the workflow publishes | (a) on a tag `vscode-v<version>`, such as `vscode-v0.1.2`: a GitHub Release with the `.vsix`. Pushes and pull requests that touch `editors/` only build and check, keeping the `.vsix` as a run artifact; (b) also a rolling "latest" pre-release, rebuilt on every push to `main` | (a). Each release is a deliberate step, and its page stays stable. (b) gives the newest build without a release, but VS Code would not know it changed |
| R2 | Versions | (a) raise the extension's version for each release, `0.1.2` and then `0.1.3`, and tag it; VS Code then sees a newer version and updates over the old one; (b) keep 0.1.1, and users reinstall with `--force` | (a). It is a version of a distributed file, not of the language or the bytecode, which the pre-alpha rule is about. Without it, users cannot tell releases apart |
| R3 | The marketplaces | (a) GitHub Releases only, for now; (b) also the VS Code Marketplace and Open VSX, which need a publisher account and a token, stored as a repository secret | (a). The extension needs a clone of the repository anyway, so a marketplace listing would mislead users who install it alone. Revisit once the toolchain can be installed on its own |
| R4 | What the workflow checks before packaging | (a) `check_extension.py`, with uv; (b) nothing beyond the packaging itself | (a). It takes seconds, and catches the grammar or the commands drifting from the language |

**Decided (user, 2026-11-22):** R1 (a), a release on each `vscode-v<version>` tag. R2 (a), the version is raised for each release. R3 (a), GitHub Releases only. R4 (a), `check_extension.py` runs before packaging. All four are as recommended.
