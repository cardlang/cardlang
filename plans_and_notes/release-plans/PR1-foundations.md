# PR1 — Foundations for moving: one place for paths, and a link check

Planned 2026-11-22, the first work package of PR0 (`PR0-release-plan-of-plans.md`). It moves nothing. It makes the moves of PR2 to PR6 cheap and checkable:
- **the code side:** where the repository's parts are is decided in one module, not in the 66 files that build those paths today;
- **the documentation side:** every link and every named file is checked, so a move that breaks a reference fails `run_checks`.

## 1. Where it starts (measured 2026-11-22)

- **Python:**
  - 66 files build paths into the repository, such as `ROOT / "conformance"`, `repo / "spec"` and `REPO / "platform" / "base-catalog.txt"`: 118 places;
  - 13 work out the repository root themselves, with `parents[n]`;
  - most scripts also take the repository as their first argument, `run_checks` passes it, and some build paths from that.
- **Markdown:**
  - 85 tracked files, with 690 relative links, none broken today;
  - many links carry an anchor (`06-expressions.md#613-errors-defined-in-this-chapter`), which nothing checks;
  - 926 file paths are named in backticks (`` `tools/clc.py` ``). Of those, 23 do not resolve, almost all in the plans: historical names, test names without `.card`, and the future paths in PR0.

## 2. The work

**(a) The paths module: `layout` (L1).**
- **What it provides:** `layout.paths(root=None)` returns the repository's parts by name: `root`, `spec`, `conformance`, `valid`, `invalid`, `runtime`, `test_catalog`, `platform`, `base_profile`, `base_catalog`, `base_types`, `examples`, `vm`, `vm_c`, `tools`, the rationale files (`design_notes`, `decision_register`), and the plan and report folders. The default root is the repository the module sits in.
- **Who changes:** every file that builds a repository path asks it instead, including the scripts that take the repository as an argument. Their argument is still honoured, through `layout.paths(repo)`.
- **What stays local:** paths inside a tool's own folder, such as the language server's test data and `vm/c`'s own sources, are not repository layout.
- **Where it lives (L1):** `tools/checkers/layout.py` for now, where every tool already looks. PR5 moves it to `cardlang.layout`.

**(b) The link check: `linkcheck.py`, in `run_checks`.** Over every Markdown file git tracks:
- **Links:** every relative link must reach an existing file or folder.
- **Anchors (L2):** a link's anchor must name a heading of its target, following GitHub's heading-anchor rules (lower case; spaces to `-`; punctuation dropped).
- **Named files (L3):** a path in backticks must resolve against the repository root, the document's own folder, or one of the folders such paths are written relative to: `conformance/` for `invalid/…` and `valid/…`, and `vm/c/` for `src/…`, `include/…` and `hal-host/…`.

  Historical documents keep the names they were written with (L4): the plans, the measurement reports, the findings and the step notes. There, a path that no longer exists is reported only as information, never as a failure. Their links are still checked.
- **A deliberate exception** is written next to the path itself as `<!-- linkcheck: ignore -->`. An example is PR0's future paths, until they exist.

**(c) The 23 unresolved paths today** are resolved by each one's kind:
- **test names written without `.card`:** fixed in place;
- **future paths in PR0:** marked as exceptions;
- **historical names in plans:** left as written (L4).

**Done when:**
- no Python file outside `layout` builds a path into the repository's top-level parts, which a grep check in `linkcheck.py` confirms;
- `linkcheck.py` passes, and fails on a broken link, anchor or named file, which a mutation check confirms;
- `run_checks` passes.

## 3. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| L1 | Where the paths module lives until PR5 | (a) `tools/checkers/layout.py`: every tool already finds that folder; (b) `tools/layout.py`, which half the tools would need a new `sys.path` entry for | (a). It moves to `cardlang.layout` in PR5 anyway |
| L2 | Check anchors too | (a) yes, by GitHub's anchor rules; (b) links to files only | (a). The spec's index is mostly links to anchors, and a renamed heading would otherwise break them unnoticed in a public repository |
| L3 | Check file paths named in backticks | (a) yes, strictly, in the current-state documents; (b) links only | (a). Most cross-references in the plans and READMEs are backtick paths, not links. Only checking them makes PR2 and PR3 safe |
| L4 | Historical documents: plans, measurement reports, findings, step notes | (a) keep the paths they were written with; the check reports stale ones as information; `devel/README.md` (PR2) says these paths are as of writing; (b) rewrite them to the new paths at every move | (a). They record what was true then. Rewriting history makes it inaccurate, and their links still work |

**Answered (user, 2026-11-22):** L1 (a) `tools/checkers/layout.py`; L2 (a) check anchors; L3 (a) check backtick paths strictly in current-state documents; L4 (a) historical documents keep their paths as written.
