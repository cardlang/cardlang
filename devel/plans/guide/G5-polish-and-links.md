# G5 — Polish and links: detailed sub-plan

Planned 2026-11-24, the last work package of the guide's plan of plans. All eleven chapters are written and reviewed. G5 makes them read as one book, links the guide from the rest of the project, and publishes it.

## 1. What there is now

- **Chapters 1 to 11** are on `guide`. `origin/guide` is at chapter 8, where the guide workflow passed. `main` has nothing that `guide` lacks, so the merge is a fast-forward.
- **GitHub Pages is not enabled** (`gh api repos/cardlang/cardlang/pages` gives 404).
- **The guide cites 89 distinct spec rules,** such as *EXP-2* and *BP-21*. Nothing checks that each one exists.
- **The README** links the guide after its own getting-started section, which duplicates chapter 1 in brief. G1 left shortening it to G5.
- **The spec's index and the extension's README** do not mention the guide.
- **The front page** lists the chapters, with a description for chapter 1 only.
- **The guide has no images.** Chapters 1 and 9 describe the extension in words.
- **MkDocs Material reaches end of life in May 2027.** Its successor, Zensical, reads the same `mkdocs.yml` (G0's note).

## 2. The work

### 2.1 A consistency pass

**I read the guide from start to finish as one book:**
- terms used one way throughout: applet, host, platform, binding, outcome, trap;
- the vault's code and commands as each chapter left them, and no text that later chapters made untrue;
- the cross-references between chapters, and their anchors;
- every "What next";
- the voice of `guide/README.md`.

**Fixes go in one commit per chapter, or one for all if they are small.**

**`guidecheck` checks every rule the guide cites,** written as *XXX-n* or *BP-n*, against the specification's rule headings and the Base Profile's. A citation of a rule that does not exist fails. It is checked by injection.

### 2.2 Images (Q1)

None for now (Q1 b). The text describes the extension, and images can be added later.

### 2.3 Links

- **The specification's index:** a line for readers who want a tutorial, pointing to the guide.
- **The extension's README:** a line under its getting-started, pointing to chapter 1.
- **The README (Q2):** unchanged. It keeps its getting-started section, with the existing link to the guide.

### 2.4 The front page

- A one-line description for every chapter, not only chapter 1.
- A short *Where to start*: chapter 1 for everyone, and chapter 11 for readers from C or Java Card who want the differences first.

### 2.5 Going live (Q3)

1. Push `guide`, and watch the guide workflow pass.
2. Enable Pages, with build type "GitHub Actions", by `gh api`. This is a public setting, done only with the user's go-ahead at that moment (G0 Q7).
3. Merge `guide` into `main` (Q3), and watch the workflow deploy.
4. Open the published site, and check the front page, one chapter, search, and dark mode.

### 2.6 Recorded, not done

- **Zensical:** a migration when Material's end of life approaches. Nothing changes now.
- **The extension:** the next release carries the scenario grammar's `length` keyword. That release is its own step, done when the user asks.

## 3. Checks

- `run_checks` passes, including the new rule-citation check, and the link check passes.
- `mkdocs build --strict` passes, and the guide workflow passes on GitHub.
- The published site is viewed.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | Images of the extension in chapters 1 and 9 | (a) I write a shot list, about five images: errors as you type, Build Applet's output, Run Scenario's output, the debugger stopped with Variables, and the Breakpoints panel. You capture them, and I place them, with alt text; (b) no images for now. The text describes everything; (c) I capture them with computer use. In VS Code it can click but not type, so only some shots are possible | (a). Real screenshots from your setup, in the extension's theme, help a newcomer most in chapter 1. (b) is fine if you would rather publish sooner, and add them later |
| Q2 | The README's getting-started section, which repeats chapter 1 in brief | (a) shorten it to the essentials: clone, `uv sync`, install the extension, open an example, and "continue with the guide's chapter 1"; (b) keep it as it is, with its link to the guide | (a). One place to maintain the full steps, the guide, and the README stays a quick landing page |
| Q3 | How `guide` reaches `main` | (a) a pull request from `guide`, so the workflow runs on it and the history shows one merge. You merge it on GitHub, or I do with `gh` on your word; (b) fast-forward `main` to `guide` locally, and push `main` | (a). It is the usual public path, the PR records what the guide added, and the workflow runs on it before `main` changes. It is a merge commit, not a squash, so each chapter's commit stays in the history |

**Decided (user, 2026-11-24):**
- Q1 (b): no images for now.
- Q2 (b): the README stays as it is.
- Q3 (a): a pull request from `guide` to `main`, merged with a merge commit.

## 5. Progress (2026-11-24; going live held back by the user)

- **Rule citations:**
  - **The check:** `guidecheck` now checks every *XXX-n* or *BP-n* in `guide/docs` against the `**ID**` rule headings of `language/spec/*.md` and `platform/base-profile.md`. That is 96 citations. Injection: *EXP-999* failed.
  - **Read side by side:** every citation, with the start of its rule. Two were wrong:
    - chapter 1 said a trap leaves "nothing … half-finished", citing RTF-1, but persistent writes outside a transaction remain (RTF-2). The sentence now says so;
    - chapter 2 cited EXP-10 for a literal fitting its type, where EXP-7 says it. It now cites both.
- **Terms:** the front page said "application" for the reader's program. It now says "applet", and defines it once. The other uses of "application" are correct: the error category, and applications on an ISO 7816 card.
- **Cross-references:** all were listed with their context and read. One was untrue: chapter 2's last exercise pointed to chapter 5 for why `match` works only on enums and outcomes. It became a self-contained hint. The vault's continuity is checked by `guidecheck`, which compiles each version and runs every scenario.
- **The front page:**
  - "applet" throughout;
  - a line for every chapter;
  - *Where to start*: chapter 1 for everyone, chapter 11 first for readers from C or Java Card, and the specification for exact rules.
- **`guide/README.md`:** the house rules the reviews produced:
  - comparisons only in chapter 11;
  - invalid code says so;
  - independent of the host system, with no toolchain compilers named;
  - read the rule before citing it.
- **Links:** the specification's index and the extension's README point to the guide, and the extension's to chapter 1.

**Question (user): where would an applet author learn the `CardError` and trap members?** The Base Profile (BP-12), the catalog, editor completion, and spec RTF-4 have them, but the guide listed neither in full. Chapter 5 also promised a list in chapter 8 that was not there.
- **Chapter 8** gains *The platform's errors*: the 11 members with their codes and causes (BP-12), each API's own list in the catalog and in completion, the precedence (BP-8), failure changing nothing (BP-7), no traps for argument values (BP-9), and what the host sees.
- **Chapter 5's pointer** now leads to that table.
- **Chapter 9** gains *Trap kinds*: the RTF-4 kinds, with the slice-assignment case of `BOUNDS` from FUN-24. It notes that the host usually learns only that a trap happened (PLT-10, and `03 00 00` or `6F00` in the Base Profile).
