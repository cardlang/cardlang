# G0 — The guide's foundations: detailed sub-plan

Planned 2026-11-23, the first work package of the guide's plan of plans. It builds everything the chapters need, and no chapter yet:
- the folder and the site;
- the check that keeps every example correct;
- the workflow that publishes the guide;
- the running example's design;
- the voice.

When it is done, G1 can write chapters 1 and 2 straight into a working, checked, published guide.

## 1. What there is now

- **No guide and no site.** GitHub Pages is not enabled for the repository.
- **Checks to build on:**
  - the conformance tests' metadata: `// kind: fragment`, `// expect: compile-error CE-…`, and the binding;
  - the HEP-16 scaffold that completes a fragment;
  - `grammar.py --notes`, which already reads code blocks out of a Markdown document;
  - the harness, which runs a scenario on any backend;
  - `lexcheck.KEYWORDS`, the one list of the language's keywords.
- **The extension's workflow** shows how a GitHub workflow here checks with uv and builds with npm.

## 2. The work

### 2.1 The folder and the site

```
guide/
  README.md           what the guide is, its chapters as links (it reads on GitHub), and how to build it locally
  mkdocs.yml          the site: Material theme, navigation, highlighting, strict mode
  docs/
    index.md          the site's front page: what CardLang is, who the guide is for, where to start
    01-getting-started.md … 10-coming-from-c.md     written by G1 to G4; G0 adds stubs so the navigation is complete
```

- **The site's tool:** MkDocs with the Material theme (plan of plans Q2), as a development dependency of the uv project: `uv add --dev mkdocs-material`. That is a download, asked before it is run.
- **Building:** `uv run mkdocs build --strict -f guide/mkdocs.yml` builds the site; `serve` previews it.
- **Material's features:** search; light and dark modes, following the reader's setting; copy buttons on code blocks; and admonitions for tips and warnings.

### 2.2 Highlighting CardLang (Q6)

Pygments, which MkDocs uses, has no CardLang lexer. Two new lexers in the package, `cardlang.highlight`:
- **CardLang,** whose keywords come from `lexcheck.KEYWORDS`, so highlighting cannot drift from the language, as with the VS Code grammar;
- **scenario files.**

`pyproject.toml` registers both as Pygments plugins (`[project.entry-points."pygments.lexers"]`), so `cardlang` and `scenario` work as fence languages. A check, joining `check_extension`'s, confirms that the lexer's keywords are the lexer's own list.

### 2.3 The example check (plan of plans Q3; Q5)

`tests/guidecheck.py`, run by `run_checks`, reads every chapter. Each fenced block whose language is `cardlang` or `scenario` must be preceded by a comment that says what it is. The comment is invisible on the site and on GitHub:

| Comment | The block |
|---|---|
| `<!-- check: program NAME -->` | A file of the program `NAME`. The blocks of one name, in one chapter, are joined in order into its files (Q5), so a chapter can show a program in pieces with prose between them. The program must compile with the full front end |
| `<!-- check: fragment -->` | A fragment, completed by the HEP-16 scaffold, as the conformance tests are; it must compile |
| `<!-- check: error CE-XXX-n -->` | A fragment that must fail with exactly that compile error: the guide's "this is wrong" examples |
| `<!-- check: scenario NAME -->` | A scenario run against the program `NAME`, on the reference interpreter and on the Python VM; every `expect` must hold |
| `<!-- check: none -->` | Shown, not checked, such as pseudo-code; used sparingly, and counted in the check's output |

Blocks in other languages, such as `bash` and `json`, are not checked. A `cardlang` block with no comment fails the check, so nothing slips through unchecked.

**How it is checked:**
- `guidecheck` is checked by injection: a broken program, a wrong error code and a failing `expect` must each fail it;
- G0's own stub chapter carries one example of each kind, so the check has something to check from the first commit.

### 2.4 Publishing (Q7, Q8)

A workflow, `.github/workflows/guide.yml`:
- **on a pull request or a push to any branch** touching `guide/`, `cardlang.highlight` or the workflow: `uv sync` (with the dev dependencies), `guidecheck.py`, and `mkdocs build --strict`;
- **on a push to `main`:** the same, then publishes the site to GitHub Pages, with GitHub's own `upload-pages-artifact` and `deploy-pages` actions. The address is `https://cardlang.github.io/cardlang/`;
- **enabling Pages** for the repository, with "GitHub Actions" as its source, is a one-time setting (Q7).

### 2.5 The running example (plan of plans Q4)

The design, written as `guide/docs/` notes for G1 to G4 to follow, and in this plan's Done section: a **PIN-protected secret store,** called *vault* in the guide.

| Chapter | The vault gains |
|---|---|
| 1 | A counter: read it, increment it. The first applet, built and run |
| 2 | Its commands as an enum, its request read field by field |
| 3 | Helper functions; the request as a slice; writing the response through `inout` |
| 4 | An error set; `require` and `attempt`; a malformed request as an error, an overflow as a trap |
| 5 | A persistent PIN and retry counter, a session flag for "unlocked"; changing the PIN in a transaction |
| 6 | The ISO 7816 binding: status words; the same applet on the raw binding |
| 7 | A stored secret, readable only when unlocked; a key generated at installation, signing a challenge |
| 8 | Its scenarios as tests; debugging a trap and a failed `expect` |

Its commands are: read the counter, verify the PIN, change the PIN, store the secret, read the secret and sign. Each chapter's version is a complete program, checked, with its scenario.

### 2.6 The voice

A short style section in `guide/README.md`, for whoever writes:
- second person ("you write…");
- short paragraphs, and one idea per section;
- show the code, then explain it;
- every rule named the spec's way (EXP-14) the first time it matters;
- the current state only, and no development steps;
- the documentation's usual plain-English style.

### 2.7 Links

- **The README:** a line in "Getting started in VS Code" saying that the guide continues from there, linking the site;
- **the repository's layout table:** a row for `guide/`;
- **the guide's `index.md`:** links back to the README, the spec and the examples.

## 3. Checks

- `run_checks` passes, with `guidecheck` in it.
- The link check passes, including on `guide/`.
- `mkdocs build --strict` passes, and the site looks right in the browser: light and dark, highlighting, search.
- The workflow passes on the branch. After the merge, the site is live and its pages load.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q5 | Showing one program in pieces | (a) blocks marked `program NAME` are joined in order within a chapter, so prose can sit between parts of one program, and every part is checked; (b) every block stands alone: each chapter repeats the whole program in one block | (a). A guide explains a program a piece at a time; (b) means long, repetitive listings |
| Q6 | Highlighting CardLang on the site | (a) our own Pygments lexer, with the keywords from `lexcheck`; (b) borrow an existing lexer, such as Rust's or C's | (a). Borrowed highlighting colours CardLang's keywords wrongly, and a small lexer from the one keyword list cannot drift |
| Q7 | Enabling GitHub Pages | (a) I enable it with `gh api`, with your go-ahead at that step; (b) you enable it in the repository's settings (Pages, then Source: GitHub Actions) | Either works. (a) saves you a few clicks, (b) keeps a public setting in your hands |
| Q8 | What the site contains | (a) the guide only; (b) the guide plus the specification and the Base Profile, as reference sections | (a) for now. The spec's internal links and tables would need checking as a site first. Linking to the spec on GitHub is enough until then |

**Decided (user, 2026-11-23):**
- Q5 (a): named blocks are joined within a chapter.
- Q6 (a): our own Pygments lexer.
- Q7 (a): Pages is enabled with `gh api`, with the user's go-ahead at that step.
- Q8 (a): the site holds the guide only.

## 5. Done (2026-11-23, on `guide`)

- **MkDocs Material** is a development dependency (`uv add --dev mkdocs-material`, approved), with MkDocs 1.6.1 and Material 9.8.2.
  - Material now prints that it reaches end of life on 2027-05-05, and that its makers' successor, Zensical, reads the same `mkdocs.yml`. The workflow silences the notice. Moving to Zensical later is a small change, recorded here as a follow-up.
- **`guide/`:**
  - **`mkdocs.yml`:** the Material theme, light and dark modes following the reader, search, copy buttons, admonitions, the navigation of all ten chapters, and the icon as logo and favicon (a copy in `docs/assets/`, since MkDocs only serves its `docs_dir`);
  - **`docs/index.md`:** the front page. It shows the counter, its scenario, and a mistake the compiler catches, all checked, and lists the chapters;
  - **ten stub chapters,** each saying "Coming soon";
  - **`README.md`:** the chapters as links, building the site, the check's comments, and the voice;
  - **`site/`,** the built site, is ignored by git.
- **`src/cardlang/highlight.py`:** the Pygments lexers `cardlang` and `scenario`, registered as plugins in `pyproject.toml`. The keywords come from `lexcheck` and the intrinsics from `expcheck`, as the VS Code grammar's do.
- **`tests/guidecheck.py`,** in `run_checks`. It checks the program, fragment, error, scenario and none comments, a block without a comment, and a comment with no block. It also checks the scenario lexer's steps against the extension's scenario grammar.
  - **By injection on a copy,** it failed each of these: a program that does not compile, a wrong error code, a block with no comment, a failing `expect`, and a scenario for an unknown program. A correct fragment passed.
- **`layout`** gains `guide`, and `TOP_LEVEL` lists it.
- **`.github/workflows/guide.yml`:**
  - on a push or pull request that touches the guide, the package, the check, the lock or the extension's grammars, it runs `guidecheck` and `mkdocs build --strict`, and uploads the site;
  - on `main`, it deploys the site with `actions/deploy-pages`.

  The actions are `checkout@v7`, `setup-uv@v10.3.3`, `upload-pages-artifact@v5` and `deploy-pages@v5`.
- **The running example's design** is in `vault.md`, beside this plan.
- **The README** links the guide after the getting-started chapter, and in the layout table.
- **Checked:**
  - `run_checks` passes, 52 runs;
  - the link check passes;
  - `mkdocs build --strict` passes;
  - served locally and viewed, the front page, the CardLang and scenario highlighting, the light and dark modes and the table of contents all render as intended.
- **Not yet done:**
  - the workflow's first run on GitHub;
  - enabling Pages, which needs the user's go-ahead;
  - after the merge, the site going live.
