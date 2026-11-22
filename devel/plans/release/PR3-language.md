# PR3 — The definition into `language/`: detailed sub-plan

Planned 2026-11-22, the third work package of PR0. It gathers the language definition into one top-level folder: the specification, the conformance suite, and the rationale behind them. `platform/` stays at the top level (PR0 R3). Nothing is deleted, and every move is a `git mv`.

## 1. What moves

| From | To |
|---|---|
| `spec/` | `language/spec/` |
| `conformance/` | `language/conformance/` |
| `plans_and_notes/card-language-design-notes.md`, `decision-register.md` | `language/rationale/` |
| `plans_and_notes/cardlang-platform-notes.md` | `language/rationale/` (P1) |
| `plans_and_notes/draft-0.2-release-notes.md`, `draft-0.2-candidates.md` | `language/releases/`, as `draft-0.2.md` and `draft-0.2-candidates.md` (P2) |

`plans_and_notes/` then disappears.

## 2. What the survey found

- **The code needs one change.** About 59 Python files reach these folders, but all of them go through `layout` since PR1. `layout`'s attributes for the spec, the conformance suite and the rationale change, and nothing else does.
- **`.gitattributes` must move with the suite.** `conformance/**/*.card -text` keeps the byte-exact tests (BOM, CR, CRLF, invalid UTF-8) from being normalised. If the pattern is not updated in the same commit, the moved files lose the attribute. The check: after the move, `git ls-files --eol` shows the same line endings for every conformance file as before, and `git check-attr text` reports `unset` for them.
- **Two checks find fragments by path.** `compiler.py` and `disasm.py` treat a file whose path contains `conformance` as a fragment. `language/conformance/` still contains it, so they keep working. PR5 replaces this with the project's `kind`.
- **Current-state documents:** 15 Markdown files name these paths. They are the spec's index, chapters 1, 12 and 13, and annexes B, C and D; the conformance README; the platform profile; the top-level readme; `tools/README.md`; and two VM documents. Only the readme has Markdown links into these folders.
- **Source comments** also name them. These are the C VM's `natives.c` and `cl_hal_test.h`, two conformance programs, two example sources, and Python docstrings in `tools/`. One of them, `examples/fido2/constants.card`, already names `plans_and_notes/base-api-plan.md`, which PR2 moved. The link check does not see it, because it reads only Markdown (P4).
- **Historical documents:** 56 files in `devel/` name these paths. They keep their text, as before. `layout.MOVED` gains the PR3 moves, so their references resolve.
- **The rationale stays historical.** The design notes say they are not normative, the register is generated from them, and the release notes record a release. They stay in `layout.historical`, now as `language/rationale/`.

## 3. The work

1. **The moves,** with `git mv`, together with **`.gitattributes`** in the same commit.
2. **`layout`:**
   - `spec`, `conformance` and their sub-parts are now under `language/`;
   - a new part, `language`, and `rationale` in place of `notes`;
   - `historical` becomes `devel/` plus `language/rationale/`;
   - `TOP_LEVEL` gains `language`, and drops `plans_and_notes`, `spec` and `conformance`;
   - `MOVED` gains the PR3 rows.
3. **The current-state documents** are rewritten through `MOVED`, links included. The spec's own text changes only in the paths it names. Per the pre-alpha rule, there is no version change.
4. **Source comments:** the link check's path rule extends to comments in tracked `.card`, `.c`, `.h` and `.py` files outside `devel/` (P4), and the comments it finds are rewritten.
5. **`language/README.md`** (P3): what the spec, the conformance suite, the rationale and the releases are, and where to start reading.
6. **The top-level readme:** the layout table gets one `language/` row with its three parts, and loses the `spec/`, `conformance/` and `plans_and_notes/` rows.
7. **Checks:**
   - `run_checks` passes, including the link check, with no new INFO lines;
   - the conformance files' line endings and attributes are unchanged (see §2);
   - the VS Code extension still finds `base-types.card` and compiles an example; it is unaffected, since `platform/` does not move;
   - the generators and history scripts that ran after PR2 still run against a copy of the repository.

**Done when:**
- `spec/`, `conformance/` and `plans_and_notes/` are gone from the top level;
- `language/` holds the definition;
- `run_checks` passes;
- every reference, current or historical, resolves.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| P1 | Where the platform notes go. They are the early notes on the platform and runtime boundary, and the source of Annex B and the Base Profile | (a) `language/rationale/`, beside the design notes; (b) `platform/rationale/` | (a). They predate the profile and were written as input to the language's Annex B, which is part of the specification |
| P2 | The Draft 0.2 release notes and candidates | (a) `language/rationale/`, as PR0 says; (b) `language/releases/`: the release notes as `draft-0.2.md`, beside the candidates for the next draft | (b). A reader looks for what changed in a release, which is not rationale; a folder of releases also has room for Draft 0.3 |
| P3 | A README for `language/` | (a) now: a short page on what each part is, and where to start reading; (b) leave it to PR7 | (a). A new top-level folder with no README is the first thing a visitor sees |
| P4 | Paths named in source comments (`.card`, `.c`, `.h`, Python docstrings) | (a) extend the link check's path rule to comments in tracked source files outside `devel/`; (b) rewrite this PR's comments by hand and keep the check to Markdown | (a). The FIDO2 comment shows that hand-checking already misses one. Files in `devel/` are historical and stay out |

**Decided (user, 2026-11-22):** P1 (a), P2 (b), P3 (a), P4 (a), all as recommended.
