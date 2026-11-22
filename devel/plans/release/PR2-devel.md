# PR2 — Development aids into `devel/`: detailed sub-plan

Planned 2026-11-22, the second work package of PR0. It moves the record of how the project was built, and the scripts used along the way, into `devel/`. Nothing is deleted, and every move is a `git mv`.

## 1. What moves

| From | To |
|---|---|
| `plans_and_notes/specification-plan-of-plans.md`, `vm-plan-of-plans.md` | `devel/plans/` |
| `plans_and_notes/spec-plans/`, `vm-plans/`, `tooling-plans/`, `release-plans/` | `devel/plans/spec/`, `vm/`, `tooling/`, `release/` (Q1) |
| `plans_and_notes/base-api-plan.md` | `devel/plans/spec/` (it planned the Base Profile's work packages) |
| `plans_and_notes/SP14-consolidation-report.md`, `VM5-measurements.md`, `VM7-measurements.md`, `VM7b-measurements.md`, `WP8-fido2-findings.md`, `WP12-piv-findings.md`, `WP8-step0-notes.md`, `PIV-step0-notes.md` | `devel/reports/` |
| `tools/generators/` | `devel/generators/` |
| `tools/history/` | `devel/history/` |
| `tools/vmproto/measure.py`, `revision.py`; `vm/c/measure.py` | `devel/measure/`, as `pyvm_measure.py`, `revision.py` and `cvm_measure.py` (Q3) |

**What stays, until PR3 (Q2):** the rationale in `plans_and_notes/`:
- the design notes;
- the platform notes;
- the decision register;
- the draft 0.2 release notes and candidates.

PR3 moves them into `language/rationale/`, and `plans_and_notes/` then disappears.

**What stays for later work packages:**
- **the checks** in `tools/vmproto/` (`check_state`, `compile_all`, `debug_check`), and the applet checkers in `tools/fido/` and `tools/piv/`, which go to `tests/` and `examples/` in PR4 and PR5;
- **`tools/vscode/`,** which goes to `editors/` in PR6.

## 2. The work

1. **The moves above,** with `git mv`.
2. **`layout`:**
   - new parts `devel`, `plans`, `reports`, `generators`, `history` and `measure`;
   - `historical` becomes `devel/` plus the rationale.
3. **The current-state documents** are rewritten to the new paths. These are the 14 documents that name these files: the spec's index and annexes, the VM documents, the platform profile, the READMEs, and the conformance README, which tells readers to run `tools/generators/coverage.py`. Their links are rewritten too.
4. **The historical documents keep their text** (PR1 L4). The link check learns where each moved path went (Q4), so their references still resolve, and a reader of the check's output sees where a file is now.
5. **The moved scripts:** their `sys.path` set-up lines are adjusted to their new folders, and the script paths that the plans' own run instructions give are noted in `devel/README.md`.
6. **`devel/README.md`:**
   - what is here, and why it is kept: the record of how the specification, the VM and the tools were built;
   - that its documents are as of writing, so their paths may name files that have moved since;
   - how to run the generators.
7. **Checks:**
   - `run_checks` passes, including the link check, with no new INFO lines;
   - the generators and the history scripts that ran before still run against a copy of the repository;
   - the measurement scripts still run.

**Done when:**
- `plans_and_notes/` holds only the rationale;
- `tools/` holds no generators, history or measurement scripts;
- `devel/` has its README;
- `run_checks` passes;
- every reference, current or historical, resolves.

## 3. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | The plan folders' names | (a) `devel/plans/spec/`, `vm/`, `tooling/`, `release/`, with the plans of plans directly in `devel/plans/`; (b) keep `spec-plans/` and the rest as they are | (a). The `-plans` suffix is redundant inside `devel/plans/` |
| Q2 | When the rationale moves | (a) PR3, with the rest of the definition; (b) now, straight to `language/rationale/` | (a). PR3 is the work package for the definition; until then `plans_and_notes/` holds only those five files |
| Q3 | The measurement scripts | (a) to `devel/measure/`, renamed `pyvm_measure.py` and `cvm_measure.py` so two files are not both `measure.py`, with `revision.py` as it is; (b) leave them beside what they measure | (a). They are development aids, which PR0 puts in `devel/` |
| Q4 | Paths in historical documents that point at moved files | (a) the link check keeps a table of moves, from old prefix to new place, and resolves them through it: the text stays as written and every reference is still checked; (b) report them as INFO, which here would be most of the plans' 124-odd references; (c) rewrite the historical documents | (a). It keeps the history exact without burying the check in noise. The table also records the moves |

**Answered (user, 2026-11-22):** Q1 (a), Q2 (a), Q3 (a), Q4 (a): the recommendations.

## 4. Done (2026-11-22)

- **Moved with `git mv`:**
  - the plans, to `devel/plans/`, with `spec/`, `vm/`, `tooling/` and `release/` and the plans of plans directly in it;
  - the base API plan, to `devel/plans/spec/`;
  - eight reports and notes, to `devel/reports/`;
  - the generators and history scripts, to `devel/generators/` and `devel/history/`;
  - the three measurement scripts, to `devel/measure/`, as `pyvm_measure.py`, `revision.py` and `cvm_measure.py`.

  `plans_and_notes/` now holds only the five rationale files.
- **`layout`:**
  - new parts `devel`, `plans`, `reports`, `generators`, `history` and `measure`;
  - `historical` is now `devel/` and the rationale;
  - `layout.MOVED`, the table of moves, with `layout.moved(path)` to look up where a path went.
- **The link check:**
  - in historical documents, a moved path resolves through the table, silently;
  - in current-state documents, a moved path fails, naming its new place;
  - checked by injection: an old path in `vm/README.md` fails, and in a report it resolves.
- **Current-state references rewritten through the table:** 16 documents, among them the spec's index and annexes B, C and D, the VM documents, the platform profile, the READMEs and the conformance README. Also the docstring of `tools/piv/check_piv.py` and a comment in `vm/c/CMakeLists.txt`.
- **The moved scripts:**
  - their `sys.path` lines and usage lines now point from `devel/`;
  - `cvm_measure.py` takes the C VM's folder from `layout.at().vm_c`;
  - all three measurement scripts run;
  - the 33 generators and history scripts that ran before still run against a copy of the repository, and the three that already failed still fail the same way.
- **`devel/README.md`:**
  - what is here and why it is kept;
  - that paths are as of writing, and how the check resolves them;
  - the generator and history sections, moved from `tools/README.md`, which now points here;
  - how to run the measurement scripts.
- **`readme.md`:** the layout table describes `plans_and_notes/` as the rationale, and gains `devel/`.
- **`run_checks` passes.** The link check reports four historical INFO paths, the same planned names that were never created.
