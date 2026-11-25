# TL2 — The VS Code extension sets up its own toolchain: detailed sub-plan

Planned 2026-11-25, at the user's request. Today the extension is only the client. The language server, the debugger and the build tools are the `cardlang` package, so a user needs uv, a clone of the repository and `uv sync` before the extension does anything beyond highlighting. TL2 removes those steps. A user installs the `.vsix`, agrees once, and the extension provides the rest itself.

## 1. Decisions

| # | Question | Decision |
|---|---|---|
| T1 | Where the toolchain comes from | **Bundled in the `.vsix`.** The packaging step copies the part of the repository the toolchain needs at run time into the extension, so the toolchain always matches the extension's version |
| T2 | How the extension gets uv | **A pinned download.** The extension pins a uv version and the SHA-256 of each platform's archive. It downloads uv from uv's GitHub releases, checks it, and keeps it in its own storage. `cardlang.uvPath` still overrides it |
| T3 | When the setup runs | **It asks once.** On a first start with no repository and no configured uv, a notification offers to set up the toolchain and says what it downloads and where. The command **CardLang: Set Up Toolchain** does the same later. Declining leaves highlighting and snippets working |
| T4 | Where Python comes from | **uv manages it.** uv downloads a standalone Python 3.12 or later if the machine has none, which is its default |

Not in TL2: the C VM backend, which needs a C compiler. A self-installed setup offers the Python VM and the reference interpreter. `cardlang.scenarioBackend: cvm` keeps working for users with a repository and a built C VM.

## 2. What the toolchain reads at run time

The package can't simply become a wheel, because it finds the repository from its own place (`layout.py`: two levels above `src/cardlang/`) and reads these files while it runs:

| File | Read by |
|---|---|
| `language/spec/00-index.md` | `front/diagnose.py`: the one-line meaning of each `CE-` code |
| `language/spec/annex-A-grammar.md` | `front/grammar.py`: the syntactic grammar |
| `language/conformance/platform/test-catalog.txt` | `front/pltcheck.py`: the test-only catalog |
| `platform/base-profile.md`, `base-catalog.txt`, `base-types.card` | `front/pltcheck.py`, `platform/errors.py`, `lsp/complete.py`, `lsp/semantic.py` |

`uv sync` also needs `pyproject.toml`, `uv.lock`, `README.md`, `LICENSE` and `NOTICE`, which the project metadata names.

**The bundle** is a folder `toolchain/` inside the extension that keeps the repository's layout:

```
toolchain/
  pyproject.toml  uv.lock  README.md  LICENSE  NOTICE
  src/cardlang/...                     (no __pycache__)
  language/spec/00-index.md  language/spec/annex-A-grammar.md
  language/conformance/platform/test-catalog.txt
  platform/base-profile.md  platform/base-catalog.txt  platform/base-types.card
```

That's about 2 MB, roughly 1 MB in the `.vsix`. `layout.py` needs no change, because `toolchain/` is laid out like a repository. A list of the bundled files lives in one place, `editors/vscode/bundle.py`. The check (§4) proves the list complete by running the toolchain from the bundle alone.

## 3. The work

1. **`editors/vscode/bundle.py`** (run with `uv run python -I`): copies the files of §2 into `editors/vscode/toolchain/`, which git ignores. `npm run package` runs it first, so the `.vsix` always carries the toolchain of the commit it was built from.
2. **`editors/vscode/uv.json`**: the pinned uv version, plus, for each supported platform, the archive name and its SHA-256. The platforms are Windows x64 and arm64, macOS x64 and arm64, and Linux x64 and arm64 (glibc). A small script, `editors/vscode/pin_uv.py`, fills the table from uv's published `.sha256` files for a chosen version. Raising the pin is a deliberate change, reviewed like any other.
3. **`extension.js`, finding the toolchain**, in this order:
   - `cardlang.repository` if it is set, else a workspace folder that is the repository: unchanged, and run with the uv of `cardlang.uvPath`, else the extension's own uv, else `uv` on the PATH;
   - else the bundled toolchain, if the setup has been done: the extension's own uv, with `--project <extension>/toolchain` and `UV_PROJECT_ENVIRONMENT=<storage>/env-<version>`, so nothing is written inside the extension's folder. Runs use `--frozen`, so `uv.lock` is never rewritten;
   - else it offers the setup (T3).
4. **`extension.js`, the setup** (one function, behind a progress notification that can be cancelled):
   - download the pinned uv archive with Node's `https` (VS Code applies the user's proxy settings), following GitHub's redirects, into `globalStorageUri`;
   - check its SHA-256 against `uv.json`, and stop with a clear message on a mismatch;
   - unpack it with the system's `tar`, which reads `.zip` on Windows 10 and later as well as `.tar.gz`, so no new npm dependency is needed;
   - run `uv sync --frozen --project <extension>/toolchain` with the environment variable above. uv fetches Python if needed (T4) and `cffi` from PyPI;
   - run `clc --version` as a smoke test, then start the language server.

   Every step logs to the CardLang output channel. A failure leaves no half-installed state: a fresh setup starts over.
5. **Updates and clean-up.** A new extension version brings a new bundle, so its environment `env-<version>` is created by a fresh `uv sync` (seconds, from uv's cache). The setup removes environments of other versions. uv itself is kept as long as its pin doesn't change.
6. **`package.json`**: the command `cardlang.setUpToolchain`, and the descriptions of `cardlang.repository` and `cardlang.uvPath` updated. `.vscodeignore` keeps `toolchain/` in, and leaves out `bundle.py` and `pin_uv.py`.
7. **The workflow** (`vscode-extension.yml`): it builds the bundle and the `.vsix` as before. A new job, on Windows, macOS and Linux, runs the setup outside VS Code with a small Node driver (`editors/vscode/selftest.js`) that uses the same functions as the extension. The job downloads uv, syncs, and runs `clc check` and `clc run` on a sample applet and scenario from the bundle alone, with no repository checked out beside it.
8. **`check_extension.py`**: checks that `uv.json` covers every platform the extension claims, and that the bundle list names only files that exist.
9. **Documentation**:
   - the extension's README: Requirements becomes "none; the extension offers to set up its toolchain", with the repository as the alternative for those who work on CardLang;
   - the root README's extension section, likewise;
   - the guide's chapter 1: installing becomes "install the extension and accept the setup". Cloning the repository becomes the path for reading the examples, and the `cardlang.repository` step for an applet outside the repository goes away. Platform-neutral wording, as the guide's rules require.
10. **Release**: version 0.2.0 of the extension (a new capability), through the existing tag-and-release flow.

## 4. Checks

- The self-test job is green on all three systems, from a clean runner with no uv, no Python 3.12 and no repository.
- By hand on this machine: remove uv from the PATH and unset `cardlang.repository`, install the `.vsix`, accept the setup, then open the vault from the guide in a folder of its own. Diagnostics, Build Applet, Run Scenario and the debugger all work.
- With the repository open, the extension still uses the repository and never offers the setup.
- A corrupted download (change one byte in `uv.json`'s checksum) stops the setup with a message, and leaves nothing behind.
- Declining the setup leaves highlighting working and shows no repeated prompts. The command still offers it.
- `run_checks`, `check_extension.py`, guidecheck and linkcheck pass.

## 5. Risks

- **Downloads at first start.** The setup needs a network, and some networks block downloading executables. The message on failure names the URL and points to the alternative: install uv yourself and set `cardlang.uvPath`, or use a clone of the repository.
- **Trust.** Running a downloaded program is something users and reviewers notice. The prompt says exactly what is downloaded and from where, the archive is checked against a pinned hash, and nothing runs without the user's agreement.
- **uv's editable install** of the bundled project points into the extension's folder. That folder is fixed per version, and `env-<version>` follows it. The self-test proves this works on all three systems before release.
- **Size.** The `.vsix` grows from about 400 KB to about 1.5 MB.

## 6. Progress

**Built 2026-11-25,** on the branch `vscode-self-setup`. Two departures from the plan:

- **Linux uses uv's static musl builds,** not the glibc ones. They run on glibc and musl systems alike, so one pin covers Alpine too.
- **A repository with no uv** also gets the setup offer. Without it, a user who opens a clone first, as chapter 1 suggests, would get a language server that can't start. After the setup, the repository is run with the extension's own uv.

The setup lives in `toolchain.js`, plain Node, so `selftest.js` runs exactly the shipped code against an unpacked `.vsix`. Locally, on Windows x64, the self-test passes: the setup, `clc check`, `build` and `run`, the language server's diagnostics and `card.` completion, the debug adapter, and a second setup that reuses uv. A first run found that a removal could fail on Windows while a server's Python was still exiting. The self-test now closes the servers as VS Code does, and the setup's removals retry.

Not yet verified: a machine with no Python (CI runners have one), a corrupted download (only by reading the code), and the extension inside VS Code.
