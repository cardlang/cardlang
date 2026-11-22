# Removing the status markings: plan

Planned 2026-11-22, at the user's request. Every rule of the specification is agreed and every chapter is complete, so the markings that say so carry no information, and a reader finds them confusing. This plan makes "agreed" the default. It removes the markings that only ever say "agreed" or "complete", and keeps a way to mark the exceptions.

## 1. What there is now

| Marking | Where | Count |
|---|---|---|
| `[Agreed]` after a rule's ID, as in `**EXP-6 [Agreed]**` | every rule of chapters 1–13 and Annex B | 305 rules; 309 occurrences with chapter 1's table and the index |
| `[Proposal]`, `[Open]` | only where chapter 1 §1.4 and the index define them. No rule has one | 0 rules |
| "Chapter status: **draft complete**" | the second line of each chapter and of Annex B | 14 |
| The Status column of the index's chapter table | `00-index.md` | 18 rows |
| The "Rule status summary" table, `Rules / [Agreed] / [Proposal] / [Open]` per chapter | `00-index.md` | 14 rows |
| The Status column of the generated "Index of rules" | `00-index.md` | 305 rows |
| `// status: agreed` in a test's header | `language/conformance/` | 413 tests |

**What reads them:**
- **`tests/speccheck.py`:**
  - every rule has exactly one tag;
  - a [Proposal] or [Open] rule cites its open issue;
  - the summary table matches the rules;
  - several regular expressions find a rule's heading by its tag.
- **`tests/rule_index.py`** writes the Status column.
- **`tests/coverage.py`** finds rules by their heading, with the tag.
- **The conformance README** makes `status` a required header field.
- **The one-off history scripts in `devel/history/`** match `[Agreed]`. They are records, not to be re-run, and they stay as they are.

**What stays.** The decision register's "Spec tag" column records how each decision was classified while the specification was written. It is part of the rationale, and it stays.

## 2. The work

1. **Chapter 1 §1.4:**
   - a rule is normative as written, unless it is marked;
   - `[Proposal]` and `[Open]` stay defined, for a rule that a later draft takes up before it is decided, and each still cites its open issue;
   - "No silent invention" stays, since it is the reason for the two marks;
   - §1.9's Sources rule keeps its "plus the open issue for a [Proposal] or [Open] rule".
2. **The rules:** a script removes ` [Agreed]` from every rule heading in chapters 1–13 and Annex B: `**EXP-6 [Agreed]**` becomes `**EXP-6**`. Nothing else in the rule changes.
3. **The status lines (T2)** and the index's tables (T4).
4. **The tests (T3):** a script removes the `// status: agreed` line from the 413 headers. Each file is edited as bytes, so its line endings and encoding stay exactly as they are; these files are byte-exact. The conformance README describes the field as optional: absent means the tested rules are normative, and `proposal` or `open` marks a test that depends on such a rule.
5. **The tools:**
   - **`speccheck`:**
     - a rule heading has at most one tag, which is `[Proposal]` or `[Open]`;
     - a tagged rule cites its open issue;
     - a test that cites a tagged rule says so in its `status` field;
     - every heading pattern accepts an optional tag;
   - **`rule_index.py`** drops the Status column, and the index is regenerated;
   - **`coverage.py`** accepts an optional tag. Annex D §D.3 is regenerated, and must not change;
   - a check that a test's `status`, when present, is `proposal` or `open`.
6. **Other text** that explains the tags is reworded where it now says too much: Annex C's opening, and the conformance README.
7. **Checks:**
   - `run_checks` passes, with the same counts;
   - a grep finds no `[Agreed]` in `language/` or `platform/`, apart from the decision register;
   - the edited test files differ from before only by the removed line;
   - by injection: a rule tagged `[Proposal]` without an open issue fails `speccheck`, and one with an open issue passes.

## 3. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| T1 | The tags themselves | (a) keep `[Proposal]` and `[Open]` for exceptions; untagged means agreed; (b) remove the mechanism entirely; a rule not yet decided stays in Annex C until it is | (a). The open-issue process of Annex C uses them when a candidate for Draft 0.3 is drafted before it is decided, and they cost nothing while unused |
| T2 | The second line of each chapter, "CardLang Language Specification, Draft 0.2. Chapter status: **draft complete**." | (a) keep "CardLang Language Specification, Draft 0.2." and drop the status; (b) drop the whole line, since the index states the draft | (a). A chapter read on its own still says which draft it belongs to |
| T3 | The tests' `status: agreed` lines | (a) remove them from all 413 tests, and make the field optional; (b) keep the lines, and only make the field optional | (a). Otherwise every test still says "agreed", which is what this change removes |
| T4 | The index | (a) the "Rule status summary" becomes "Rules per chapter" (chapter and count only), and the chapter table and the rule index lose their Status columns; (b) remove the summary table too | (a). The count per chapter is still useful, and `speccheck` keeps checking it |

**Decided (user, 2026-11-22):** T1 (a), T2 (a), T3 (a) and T4 (a), all as recommended.

## 4. Done (2026-11-22)

- **Chapter 1 §1.4** is now "Rule marks":
  - a rule is normative as written;
  - `[Proposal]` and `[Open]` mark an undecided rule, and no rule of this draft carries one;
  - when an issue is resolved, its rule loses the mark;
  - the example rule in §1.5 is unmarked.
- **The rules:** ` [Agreed]` is removed from all 305 rule headings, in chapters 2–13 and Annex B. Nothing else changed.
- **The status lines (T2):**
  - each chapter and Annex B now reads "CardLang Language Specification, Draft 0.2.";
  - Annex A's status list is now one sentence on its mechanical check;
  - the index's status sentence keeps only the draft and its date.
- **The index (T4):**
  - "Contents and status" is "Contents", without its Status column;
  - the summary is "Rules per chapter" (chapter and count);
  - the generated rule index has `Rule` and `Defined in`. `rule_index.py` writes a mark after a rule's ID only when it has one.
- **The tests (T3):**
  - the `// status: agreed` line is removed from 412 test files and from the conformance README's example. They were edited as bytes, and each file differs from before by exactly that line;
  - the README's field table makes `status` optional: `proposal` or `open`, or absent for normative rules.
- **The tools:**
  - **`speccheck`:**
    - a rule may be unmarked;
    - a mark other than `[Proposal]` or `[Open]` fails;
    - a marked rule must cite an open issue on its Sources line;
    - a new **test-marks** check requires each test's `status` to match the strongest mark among the rules it cites, and to be absent when they are all unmarked;
    - every heading pattern accepts an optional mark;
  - **`coverage.py`** accepts the optional mark, and regenerates Annex D §D.3 unchanged;
  - **the line pins:** removing a header line moved every test's code up by one line. The checks that pin positions in conformance files were shifted to match: 18 pins in `poscheck`, one each in `clc_check` and `lsp_check`, the trap lines in `debug_check`, and the run-012 and run-001 lines in `dap_check`. The FIDO2 applet and the semantic sample did not move.
- **Checked by injection, on copies:**
  - `EXP-14 [Proposal]` without an open issue fails `rules`, and its tests then fail `test-marks`;
  - the same with `OI-3` on its Sources line passes `rules`, and its tests still need `status: proposal`;
  - `EXP-14 [Agreed]` fails as an unknown mark;
  - a test with `status: agreed` fails.
- **Checks:**
  - `run_checks` passes all 51 runs;
  - `speccheck` has 11 checks, one more;
  - no `[Agreed]` remains in `language/` or `platform/`, apart from the decision register and the Draft 0.2 release notes, which are records.
- **The generators in `devel/generators/`** still write `// status: agreed` if re-run. `test-marks` then fails on the regenerated tests, as it should.
