# PR8 — The licence and the release check: detailed sub-plan

Planned 2026-11-22, the last work package of PR0. It gives the repository a licence and checks it, end to end, against what a first public push needs. Publishing itself, by pushing to the remote, is the user's step, not part of this work package.

## 1. What there is now

- **No licence anywhere.**
  - no `LICENSE` file;
  - no `license` field in `pyproject.toml`;
  - the extension's `package.json` says `"license": "UNLICENSED"` and `"private": true`, and `npm run package` passes `--skip-license`.
- **Third-party material:**
  - **Mbed TLS 3.6.8** (Apache-2.0 or GPL-2.0-or-later) is downloaded by the C VM's build, pinned by SHA-256. It is not in the repository.
  - **`cffi`** (MIT) is the one Python dependency.
  - **`vscode-languageclient`** (MIT) is bundled into the `.vsix`, and **`@vscode/vsce`** (MIT) is a development dependency. Neither is in the repository, apart from `package-lock.json`.
  - **The FIDO2Applet clone** that informed the FIDO2 example lives in the ignored `reference/` folder, and none of it was copied.
  - **The test vectors** in the interpreter's test crypto come from public RFCs and standards.
- **The repository:**
  - 732 tracked files, 13 MB of history, branch `main`, and a remote `origin` at `github.com/cardlang/cardlang`. Nothing has been pushed by this work;
  - every commit is by `cardlang`, with no email;
  - the history is published as it is (PR7 C4).
- **Checks:**
  - `run_checks` passes, including the link check's guards against development-step names and home-folder paths;
  - there is no CI. The checks need Windows, for MSVC and llvm-mingw.
- **Open from PR7:** the README's first sentence calls CardLang a language for smart-card applications, while the project's aim is secure enclaves on microcontrollers (P4).
- **Deferred by the user:** `CONTRIBUTING.md` (PR7 C2).

## 2. The work

1. **The licence (P1, P2, P3):**
   - a `LICENSE` file at the root;
   - `license` in `pyproject.toml`;
   - `license` in the extension's `package.json`, with `--skip-license` dropped from its package script so the `.vsix` carries the licence;
   - a short "Licence" section in the README;
   - if P2 gives the documents a different licence, the README and `language/README.md` say which files it covers.
2. **The README's first sentence** (P4).
3. **A third-party notice,** in the README's licence section: Mbed TLS is downloaded and built, with its licence, and the Python and npm dependencies are listed with theirs. Nothing third-party is vendored, so no notice files are copied in.
4. **The release checklist,** run and recorded in the Done section:
   - `run_checks` passes from a clean clone, after `uv sync` and `vm/c/build.py all`. This checks that nothing depends on an ignored or local file;
   - the link check's guards pass: no development step outside `devel/`, and no home-folder path;
   - a scan finds no secrets: no private keys other than published test vectors and the applets' documented test defaults, no tokens, no email addresses;
   - every tracked file is meant to be public: a review of `git ls-files` by folder, for anything generated, large, or private;
   - `.gitignore` covers every build output and `reference/`;
   - the extension's `.vsix` builds with the licence included;
   - every top-level area has a README, and the README's links work. The link check covers this.
5. **What the user then does,** listed at the end of the Done section and not done here:
   - review the remote's settings;
   - push `main` and the tags;
   - make the repository public.

**Done when:**
- the licence is in place, in the repository, the package and the extension;
- the README's opening is decided;
- the checklist passes, from a clean clone.

## 3. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| P1 | The licence for the code: the toolchain, the C VM, the extension and the examples | (a) Apache-2.0: permissive, with an explicit patent grant, and the same as Mbed TLS; (b) MIT: shortest and most permissive, with no patent grant; (c) a copyleft licence, MPL-2.0 or GPL-3.0, which requires changes to be shared | (a). A language and VM meant to be embedded in products benefits from the patent grant, and it matches the C VM's one dependency |
| P2 | The licence for the specification and the other documents | (a) the same as the code, so one licence covers the repository; (b) CC BY 4.0 for `language/`, `platform/` and the documents, which is common for specifications | (a), unless you want others to be able to republish the specification text under a documents licence. One licence is simpler for a pre-alpha project |
| P3 | The copyright holder named in the licence | (a) "The CardLang authors", which matches the commit author `cardlang` and names no person; (b) your name | (a). It keeps the repository free of personal names, as PR7 made it |
| P4 | The README's first sentence | (a) "for writing secure applications for small, isolated environments: smart cards and secure enclaves on microcontrollers, with or without TrustZone"; (b) keep "for writing smart-card applications" | (a). It says what the project aims at, and still covers the applets, which are smart-card protocols |

**Decided (user, 2026-11-22):**
- **P1 (a):** Apache-2.0.
- **P2 (a):** the same licence for the documents.
- **P3 (a):** "The CardLang authors".
- **P4 (a), with a change:** no "enclave", a word associated with Apple's Secure Enclave, and the emphasis on uses other than smart cards. The draft wording, to confirm in the work:

  > CardLang is a small, statically typed, imperative language for writing secure applications that run isolated on small devices: trusted applications on microcontrollers, in a TrustZone secure world or a partition isolated by the memory protection unit, and also smart-card applets.

## 4. Done (2026-11-22)

- **The licence (P1–P3):**
  - **`LICENSE`:** the Apache License 2.0, unmodified. It was taken from the copy in the Mbed TLS source the build had already fetched, and checked against a second local copy, `ecdsa-sig-formatter`'s in `node_modules`: their terms are identical. Nothing was downloaded;
  - **`NOTICE`:** "Copyright 2026 The CardLang authors";
  - **`pyproject.toml`:** `license = "Apache-2.0"` and `license-files = ["LICENSE", "NOTICE"]`. The installed metadata shows `License-Expression: Apache-2.0`;
  - **the extension:** `package.json` and the root of `package-lock.json` say `Apache-2.0`, and `--skip-license` is gone. `editors/vscode/LICENSE` is a copy, because `vsce` looks for it in the extension's folder. The rebuilt `.vsix` holds `extension/LICENSE.txt`.
- **The README:**
  - **its opening (P4):** "secure applications that run isolated on small devices: trusted applications on microcontrollers, in a TrustZone secure world or a partition isolated by the memory protection unit, and also smart-card applets". The word "enclave" is not used;
  - **a "Licence" section:** the licence, `NOTICE`, and a table of what the tools fetch, each with its licence, checked from the packages themselves:
    - Mbed TLS: Apache-2.0 or GPL-2.0-or-later;
    - cffi: MIT-0;
    - vscode-languageclient and vsce: MIT.
- **The release checklist:**

  | Item | Result |
  |---|---|
  | `run_checks` from a clean copy of the tracked files | **Passed.** The copy got its own environment (`uv sync --offline`, from the uv cache) and built the C VM with both compilers. Mbed TLS came from the pinned archive and llvm-mingw from `CARDLANG_LLVM_MINGW`. All 51 runs pass, with the same counts as the working tree |
  | The guards: no development step outside `devel/`, no home-folder path | Passed |
  | Secrets | None: no private-key blocks, tokens or API keys. The applets' test defaults and the test vectors are documented as test-only |
  | Email addresses | None outside `package-lock.json`'s third-party metadata |
  | Tracked files | 732. At the root: `.gitattributes`, `.gitignore`, `.python-version`, `LICENSE`, `NOTICE`, `README.md`, `pyproject.toml`, `uv.lock`. The only file over 100 KB is the design notes, at 183 KB. Nothing generated or private |
  | Ignored outputs | `.venv/`, every `__pycache__/`, `vm/c/build/`, the examples' `build/`, `node_modules/`, the `.vsix` and `reference/`: all ignored |
  | The `.vsix` | Builds, with the licence; 404 KB |
  | READMEs and links | Every top-level area has one; the link check passes |

  **Known, not blocking:** `vsce` warns that the extension is not bundled (234 files, most of them `vscode-languageclient`); bundling would need a build step.

## 5. What remains for the user

These publish the work, and are not done here:
1. **Review the remote.** `origin` is `https://github.com/cardlang/cardlang.git`. Check its settings: visibility, default branch `main`, and anything the account adds.
2. **Push** `main` and the three tags: `spec-draft-0.1`, `spec-draft-0.2` and `bytecode-v1`.
3. **Make the repository public.**

The history is published as it is (PR7 C4). Optional, later: `CONTRIBUTING.md` (PR7 C2), and CI. CI needs Windows runners with MSVC and llvm-mingw.
