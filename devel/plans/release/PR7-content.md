# PR7 — Content cleanup: detailed sub-plan

Planned 2026-11-22, the seventh work package of PR0. PR1 to PR6 put everything where it will stay. This work package makes what a visitor reads true and complete:
- a README for every top-level area;
- current-state wording in place of notes written while the work was in progress;
- nothing personal or machine-specific.

Nothing is moved, apart from the top-level readme's rename (C1).

## 1. What the survey found

**READMEs.**

| Area | README |
|---|---|
| `language/`, `examples/`, `vm/`, `tests/`, `devel/` | yes |
| `src/cardlang/`, `editors/vscode/`, `vm/c/`, `src/cardlang/harness/`, each example | yes |
| `platform/` | **missing.** Its entry point is `base-profile.md`, but a visitor opening the folder sees no README |
| `editors/` | **missing.** It holds only `vscode/` |
| the root | `readme.md`, in lower case (C1) |

**Stale statements in current documents.** Found by a scan. The review in §2 step 1 reads every document in full, so it will find more.
- **`vm/README.md`:**
  - "the design, and later the implementation";
  - the `c/` row of its table says "not started";
  - `bytecode.md` is "living through VM7";
  - "The only backend so far is `interp`".

  The C VM has been done since VM7, and there are four backends.
- **`vm/decisions.md` and the step table in `vm/c/README.md`** name the applet checks by their old names, `check_fido2` and `check_piv` (PR4 left these). In the decision register they stay as decided. In the README's step table they are records.
- **`readme.md`:**
  - "Since Draft 0.2, the repository also holds" is a list of what was added after the last draft, written as news;
  - the layout table is right, but the opening says "reference tools that check the two against each other", which predates the compiler, the VMs and the editor;
  - the "Next steps" section mixes plans with a missing checker.
- **`src/cardlang/README.md`:**
  - it was `tools/README.md` and still reads partly as a list of scripts;
  - it says "All scripts need only Python 3 and its standard library", but the package needs `cffi`.
- **`.gitignore`:**
  - it has the comment "Python bytecode (tools/)";
  - it ignores `.vscode/`, which is right for a user's settings.

  Nothing tracked should be ignored, and nothing ignored is tracked.
- **`pyproject.toml`:** it has no `description` and no `readme`.

**Personal and machine-specific data.**
- **The current tree:** one document, `devel/plans/vm/VM7-c-vm.md`, has an absolute path with a user name, twice: where the llvm-mingw toolchain was installed (C3).
- **The history:**
  - the same lines appear in three diff lines of the history (C4);
  - the commit authors are all `cardlang` with no email;
  - no commit message has a trailer;
  - no email address appears anywhere.
- **Tools and builds:** the build scripts already find the toolchain through `CARDLANG_LLVM_MINGW` or a search, and name no machine path.

## 2. The work

1. **A review of every current-state document,** read in full against what is now true. The documents are:
   - the readme;
   - `language/README.md`, the spec's index (its status lines only), and the conformance README;
   - the `vm/` documents and `vm/c/README.md`;
   - every example's README, and `examples/README.md`;
   - the package README and the harness README;
   - `tests/README.md`, the extension's README and `devel/README.md`.

   Statements of status, counts, "not started", "so far" and "later" are corrected. Lists of what was added become descriptions of what is there. The normative text of the specification and the profile is not reworded: only paths and status lines. Each fix is listed in the Done section.
2. **New READMEs:**
   - `platform/README.md`: what the Base Profile is, its three files, and how it relates to the language's Annex B;
   - `editors/README.md`: one paragraph and a link to `vscode/`.
3. **The readme:**
   - renamed to `README.md` (C1);
   - its opening describes the whole repository: the language, its toolchain, the two VMs and the editor;
   - "Next steps" becomes a short "Status and plans" section that links to the plans of plans.
4. **No `CONTRIBUTING.md` for now** (C2).
5. **Personal data:** the two paths in the VM7 plan are generalised (C3). How the history is published (C4) is decided now and done in PR8.
6. **A scan in the link check:** it fails a tracked text file that contains an absolute path into a user's home folder (`C:\Users\…`, `/home/…`, `/Users/…`), with `<!-- linkcheck: ignore -->` for a deliberate example. This keeps it from coming back.
7. **Small fixes:**
   - `.gitignore`'s comments;
   - `pyproject.toml` gains `description` and `readme = "README.md"`;
   - the package README's dependency line.
8. **Checks:**
   - `run_checks` passes;
   - the link check passes, including the new scan;
   - a final grep finds no user name, email address or absolute home path in the tree.

**Done when:**
- every top-level area has a README;
- no current document states something that is no longer true, to the review's knowledge;
- the tree has no personal data, and the scan guards it;
- `run_checks` passes.

## 3. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| C1 | The top-level readme's name | (a) `README.md`, the usual name; (b) keep `readme.md` | (a). Both display on GitHub, but `README.md` is what visitors and tools expect. The link check then rewrites the links to it |
| C2 | What `CONTRIBUTING.md` covers | (a) setting up (uv, the C VM's two toolchains), running the checks, the conventions (rule IDs and status tags, a plan before each work package in `devel/plans/`, `git mv` for moves, the link check), how a language change is proposed (an open issue in Annex C, decided, then the rules), and that pre-alpha means no compatibility promises; (b) a short pointer to the READMEs, for now | (a). The conventions are the part a newcomer cannot guess, and they are written down nowhere in one place |
| C3 | The two absolute paths in the VM7 plan, a historical document | (a) generalise them, for example to `<workspace>\llvm-mingw-20261117-ucrt-i686`, with a note that the path was generalised; (b) leave them, since plans keep their text | (a). Privacy outweighs the rule that records keep their text (PR1 L4); the version and folder name, which are what matter, stay |
| C4 | The history, which has the same two paths in old commits | (a) publish the history as it is: it holds only a user name in a folder path, no email, and every commit is by `cardlang`; (b) publish a fresh history, squashed to one commit, keeping this one private; (c) rewrite the old commits to remove the lines, which changes every hash and the tags | (a), if you are content with that user name being visible. Otherwise (b). (c) is the most work and breaks the tags. Whichever you choose is done in PR8, at publication |

**Decided (user, 2026-11-22):**
- C1 (a): the readme becomes `README.md`.
- C2: no `CONTRIBUTING.md` for now. It is left out of PR7, and PR0's mention of it waits for a later decision.
- C3 (a): the two paths in the VM7 plan are generalised.
- C4 (a): the history is published as it is, in PR8.

## 4. Added: no development steps outside `devel/` (user, 2026-11-22)

The user asked that the names of development steps stay in `devel/`, the internal kitchen. These are the work packages (`WP8`, `SP5`, `VM7`, `TL1`, `PR3`, and their steps), and the decisions and findings local to a plan (`H2`, `J1`, `T1`, `PR5 S3`). Since PR7 reads every file anyway, the removal is done now.

**How much.** About 1,300 mentions outside `devel/`:

| Where | Mentions | Mostly |
|---|---|---|
| `language/spec/` | 521 | Annex D's "Sub-plan" column (315), Annex C's "Owning SP" column (142), the index's sub-plan column and each chapter's status line |
| `language/rationale/` | 302 | the decision register's "Owning SP" column, and its header |
| `vm/` | 182 | `decisions.md`'s "WP" column and its "Implemented by" entries, the change logs of `bytecode.md` and `image-format.md`, and prose ("the C VM (VM7)") |
| `src/`, `tests/`, `examples/`, `editors/` | 196 | comments, docstrings and `run_checks`' labels ("(TL1 step 3)", "(WP9 L4)", "(V-12 item 3, K1)") |
| `language/releases/`, `platform/`, `language/conformance/`, the readme | 74 | prose, and comments in the catalog, the base types and two test programs |

**What stays.** The project's own stable IDs are not development steps, and they stay:
- the rules (`EXP-6`), compile errors (`CE-EXP-1`) and traps (`TRAP-BOUNDS`);
- the decisions (`D-102`, `V-12`) and open issues (`OI-53`);
- the Base Profile's, HAL's, bytecode's and image's requirements (`BP-50a`, `HAL-25`, `BC-1`, `IMG-10`, `PLT-35`);
- the drafts (`Draft 0.2`) and the tags.

**Decisions.**

| ID | Question | Decision (user) |
|---|---|---|
| D1 | The rationale and the release notes | The rationale stays in `language/`, since 346 of 362 rules cite it, and is cleaned like the rest. The release notes are cleaned too |
| D2 | Columns that record which work package did something | Dropped: Annex C's "Owning SP", Annex D's "Sub-plan", the index's "Sub-plan", the decision register's "Owning SP", and `vm/decisions.md`'s "WP". A chapter's status line loses its "(SPn)" |
| D3 | Links from current documents into `devel/` | Removed. Current documents state the facts directly, such as a measured figure. Only the top-level README and `devel/README.md` lead into `devel/` |
| D4 | A guard | The link check fails on a work-package name outside `devel/`, with `<!-- linkcheck: ignore -->` (or the same in a source comment) for a deliberate one |

**How.**
1. **The columns (D2), by script:**
   - the columns are removed from every row of their tables;
   - `speccheck` and any check that reads them by position are updated;
   - so is `devel/generators/coverage.py`, which still writes Annex D §D.3 and which the conformance README tells contributors to run.

   The one-off history scripts that edit these tables (`sp14_reverse_links.py`, `gen_register.py`) are records of the old layout. They are not updated, and if they stop running against the new layout, that is recorded.
2. **The rest, by hand, in the review of §2 step 1:**
   - every mention is read in context and rewritten as what it describes: "(VM7)" goes; "TL1 step 4: the debug section gains a line table" becomes "the debug section gains a line table";
   - the change logs keep their dates and drop the work package;
   - comments in code say what the code does, and why, without the plan that asked for it.
3. **The links into `devel/` (D3):** each is replaced by the fact it supported, or dropped where it only said "see the plan".
4. **The guard (D4):**
   - added last, once the tree is clean;
   - it matches `WP`, `SP`, `VM`, `TL` and `PR` followed by a number;
   - plan-local IDs such as `T1` are too short to match safely, so the review removes those and the guard does not cover them.

**Stages.** PR7 becomes two commits:
- **7a:** the columns, the links into `devel/`, and the comments and labels in code: the parts a script or a grep can drive;
- **7b:** the full review of §2, which removes the remaining mentions in prose, together with the READMEs, the rename, the privacy fixes and the guard.

## 5. Done: stage 7a (2026-11-22)

- **The columns (D2)** were dropped by a script that splits table cells as GitHub does, on unescaped pipes, and keeps every other byte:
  - the decision register's "Owning SP", in its four tables;
  - the index's "Sub-plan";
  - Annex C's "Owning SP";
  - Annex D's "Sub-plan" (D.1) and "Owning SP" (D.2);
  - `vm/README.md`'s "Work package";
  - `vm/decisions.md`'s "WP".

  `speccheck` read D.2 by column position, and now skips one column fewer.
- **Links into `devel/` (D3):** every one outside the top-level readme and `devel/README.md` is gone, replaced by the fact it supported or dropped. These were:
  - the "Plan:" headers of the VM documents;
  - the measurement figures in `bytecode.md`'s change log, now given directly;
  - Annex C's "raised by …" notes;
  - the examples' "Background" sections and the extension README's plan link;
  - the comments in the examples, the C VM and two conformance programs. Their `source:` lines now cite V-37 or the profile rule.
- **The two live generators** moved to `tests/` (decided by the user during 7a): `coverage.py` (Annex D §D.3) and `rule_index.py` (the index of rules). Both reproduce the specification byte for byte. The conformance README and the hidden "generated by" markers name them there. `tests/README.md` lists them, and `devel/README.md` says where they went.
- **Code:** step names and plan-local IDs are gone from every comment, docstring and check label in `src/`, `tests/`, `examples/`, `vm/c/`, `editors/vscode/`, `platform/` and the conformance comments.
  - A script stripped the parentheticals that were only references, such as "(TL1 step 3)", "(VM7, J1)" and "(WP12 H2)".
  - The rest were rewritten by hand, for example "VM7b (b): a comparison" became "A comparison", and "WP3 (card.key), WP4 …" became a list of the families.
  - `layout.py`'s comments lost their PR numbers; its table of moves keeps the old file names, which are data.
- **Left for 7b:** 242 mentions, all in Markdown prose. Most are in Annex C (77), the Draft 0.3 candidates (23), the VM documents (45) and the profile (12), plus one status line in each chapter.
- **Checks:**
  - `run_checks` passes all 51 runs, with the same counts;
  - `speccheck` and the link check pass;
  - the edited conformance files keep their line endings, byte for byte.
- **Scripts:**
  - against a copy, 33 of the generators, history scripts and the two moved generators run;
  - the three that always failed still fail;
  - `sp13_checklist.py` now fails too, because the B.12 marker it searches for no longer names it. It is a one-off record, so this is expected;
  - both measurement scripts run.
- **Found on the way:** `vm/c/build/msvc` and `vm/c/build/clang` had disappeared during the session. `vm/c/build/` held a different CMake configuration, written at 16:32 by a tool outside this work, perhaps the editor's CMake support. `vm/c/build.py all` rebuilt both from the local Mbed TLS archive, with no download.
