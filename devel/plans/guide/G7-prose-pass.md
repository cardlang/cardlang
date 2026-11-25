# G7 — A prose pass: detailed sub-plan

Planned 2026-11-25, at the user's request: a pass over the guide's prose, for more varied sentences and lists, fewer filler words, and chapters that do not all open and close the same way. The meaning, the examples and the rule citations stay as they are. Only the prose changes.

## 1. What there is now

Measured over the prose of the front page and chapters 1 to 11: about 21,700 words and 745 sentences, not counting code, tables or headings.

| Pattern | Count | Example |
|---|---|---|
| **Bullets that open with a bold phrase** | 131 of 164 bullets (80%) | "- **Each arm checks its own request length.** A verify request is…" |
| **A colon that introduces an explanation** | 131, about one sentence in six | "A *scenario* plays the host: it sends commands and states the answers it expects." |
| **Pivot sentences** | 7, plus variants | "That is why…", "That is what lets the compiler…", "That is the point." |
| **Intensifiers** | "exactly" 26, "whole" 20, "deliberately" or "on purpose" 8 | "…exactly how much memory it needs." |
| **The same frame on every chapter** | an opening "In this chapter you…" or "This chapter covers…"; a closing *What next* with three bullets, in 10 chapters | |
| **The same rhythm in every section** | a code block, then a bullet list explaining it | |
| **Contrast templates** | ", not …", and "X is not Y. It is Z." | "A trap is not an error the applet reports; it is a bug." |

Other things readers notice, not counted: lists of three; signposts such as "Here is" and "Now"; and every paragraph ending on its reason.

The guide is checked by `guidecheck`, so code, error codes, scenarios and rule citations cannot change by accident. `reference-platform.md` is generated, and keeps its reference style.

## 2. The work

### 2.1 A style sheet, first

Before any chapter is edited, the plan records the rules, with before-and-after pairs from the guide itself:
- **Bullets:**
  - a bullet list is for items that really are a list;
  - explanations of code become prose;
  - bold stays only for a term defined there, or for a warning, and in fewer than one bullet in five.
- **Colons:** where a colon carries an explanation, write two sentences, or use "because" or "so". Keep colons that introduce a list or a code block.
- **Pivot sentences:** say the consequence directly, in the sentence it belongs to.
- **Intensifiers:** remove "exactly", "whole" and "deliberately" wherever the sentence means the same without them.
- **Openings and endings:**
  - each chapter opens in its own way: with the problem, the code, or the vault where it stands;
  - the *What next* sections are removed (Q3). An exercise that teaches something the chapter needs becomes a sentence in the text, if it fits there.
- **Rhythm:** vary sentence length, and let some code be explained in a paragraph, some in a sentence, and some not at all.
- **Keep:** plain words, second person, short paragraphs, the rule citations, and the house rules of `guide/README.md`.
- **Contractions:** "don't", "isn't" and "you'll", in a conversational tone, in moderation (Q2).

### 2.2 A measuring script

`devel/measure/guide_style.py` counts the patterns of §1 per chapter, before and after. It is a guide for the work, not a gate: the counts should fall, not reach zero, and it is not added to `run_checks`.

### 2.3 The chapters (Q1, Q3)

**A deep pass (Q1).** Sections may be restructured into flowing prose, merged or split, and openings and endings rewritten freely. The constraints:
- every example and scenario stays, with its check comment, in an order where the carried-over program still compiles;
- every fact and rule citation stays;
- the cross-references between chapters still land, which the link check verifies, anchors included.

A heading that other chapters link to keeps its anchor, or every link to it is updated.

The chapters are edited in batches (Q4). For each:
- the counts before and after;
- `guidecheck`, the link check and `mkdocs build --strict`;
- the user reads the result in the preview.

### 2.4 Also

- `guide/README.md`'s *Writing for the guide* gains the style sheet's rules in short, so later edits keep the voice.
- The front page is edited with the first batch.

## 3. Checks

- `guidecheck` passes after every batch: the same programs, fragments, errors, scenarios, excerpts and rule citations.
- No rule citation is lost. The count of citations stays at 104, or explains each difference.
- The counts of §1 fall in every chapter.
- The user reviews each batch.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | How deep the pass goes | (a) **moderate:** rewrite the sentences and lists that carry the patterns above, and keep each chapter's sections and order; (b) **deep:** also restructure sections into flowing prose, merge or split sections, and rewrite openings and endings freely; (c) **light:** words and phrases only, keeping every list and sentence shape | (a). It removes what readers notice, without risking the structure that was reviewed chapter by chapter. A chapter that still reads mechanically after (a) can get (b) on its own |
| Q2 | Contractions in the prose ("don't", "isn't", "you'll") | (a) use them in a conversational tone, in moderation; (b) avoid them, as now in most chapters | (a). They make the tone conversational, and the guide already addresses the reader as "you" |
| Q3 | The *What next* sections | (a) keep the heading, but vary them: as many exercises as are worth doing, written as a short paragraph or a list, and none where nothing useful remains; (b) keep them uniform; (c) remove them | (a). Exercises help a learner, but ten identical three-bullet endings read like a template |
| Q4 | Review batches | (a) four batches: the front page and chapters 1 to 3; 4 to 6; 7 to 9; 10 and 11; (b) one chapter at a time, as when the guide was written | (a). The edits are smaller than writing a chapter, and a batch shows whether the voice holds across chapters |

**Decided (user, 2026-11-25):**
- Q1 (b): a deep pass.
- Q2 (a): contractions, in moderation.
- Q3 (c): the *What next* sections are removed.
- Q4 (a): four review batches.

## 5. The style sheet, by example

Pairs from the first batch:

| Before | After |
|---|---|
| "- **`require`** checks a condition, and returns the error after `else` if it does not hold (*STM-19*)." | "The two `require` lines guard the rest of the command (*STM-19*). If the request isn't exactly one byte long, or there's no room for a 4-byte answer, the command returns the error named after `else`." |
| "A *scenario* plays the host: it sends commands and states the answers it expects." | "A *scenario* plays the part of the host, sending commands and stating the answer it expects to each one." |
| "That is what lets the compiler tell you, before the applet ever runs, exactly how much memory it needs." | "Because of that, the compiler knows how much memory an applet needs before it ever runs." |
| "In this chapter you install the tools and write your first applet: the start of the *vault*…" | "By the end of this chapter you'll have the tools installed and an applet of your own running." |
| "- **The bounds are evaluated once,** before the first run." (four bold bullets) | "The two ends of the range are worked out once, before the first pass…" (one paragraph) |

## 6. Progress

**Batch 1, 2026-11-25 (front page, chapters 1 to 3), waiting for the user's review:**
- **Rewritten as prose:** every bullet list that explained code or listed facts. The front page's chapter list is a real list, and stays.
- **Removed:** the *What next* sections. Two exercises' ideas are gone with them; none was needed by a later chapter.
- **House rule:** chapter 2's two comparisons with C ("as unsigned arithmetic does in C", "Unlike in C") are gone. Comparisons belong in chapter 11.
- **Kept, byte for byte:** every code block and check comment. `guidecheck`'s counts are the same as before: 24 programs, 36 fragments, 28 errors, 16 scenarios and 7 excerpts.
- **Rule citations:** the same set per chapter as on `main`, except the front page's example citation, *EXP-14*, which became *EXP-2* to match chapter 11.
- **Anchors** that other chapters link to are kept: *Applets, platforms and hosts*, *Your first applet*, *What the host receives*, *Integers*, *Constants*, *Enums*, *Default values* and *An applet's files*. The link check passes.

| Measure (chapters 1 to 3) | Before | After |
|---|---|---|
| Bullets | 58 | 0 |
| Bold-lead bullets | 50 | 0 |
| Colon introducing a clause | 51 | 8 |
| "That is why/what" | 3 | 0 |
| "exactly" | 6 | 2 |

**Batch 2, 2026-11-25 (chapters 4 to 6), waiting for the user's review:**
- **Prose:** explanations as paragraphs. The ordered steps of *Checking a PIN* stay a numbered list, without bold leads, because their order is the point.
- **Removed:** the *What next* sections. Their bridges forward stay as sentences:
  - the end of chapter 5 now leads into chapter 6 through `verify_pin`'s unlimited guesses;
  - chapter 6's "take the transaction out and run the scenario again" is kept as a closing sentence.
- **House rule:** chapter 4's opening comparison with C's pointers is gone. "Earning its keep" is gone too.
- **Unchanged:** every code block and check comment, and `guidecheck`'s counts. Rule citations are the same set per chapter as on `main`.
- **Anchors kept:** *Parameter modes*, *Views*, *Platform errors*, *`Err` undoes nothing*, *Four kinds of storage*, *Transactions*, *Checking a PIN* and *Changing the PIN*.

| Measure (chapters 4 to 6) | Before | After |
|---|---|---|
| Bullets | 37 | 4 (one numbered list) |
| Bold-lead bullets | 28 | 0 |
| Colon introducing a clause | 38 | 6 |
| "That is why/what" | 4 | 0 |
| "exactly" | 7 | 3 |

**Batch 2:** committed.

**Batch 3, 2026-11-25 (chapters 7 to 9), waiting for the user's review:**
- **Prose:** explanations as paragraphs. The debugger walk-through in chapter 9 stays a numbered list of four steps, without bold leads, because it is a procedure.
- **Removed:** the *What next* sections. Two items kept their substance as paragraphs:
  - chapter 7's `63CX` convention, with its pointer to the PIV example;
  - chapter 9's "moving the try counter breaks no scenario; some properties can only be checked by reading the code", now the end of *Finding a bug*.
- **Kept:** the `linkcheck: ignore` marker on the `.vscode/launch.json` line.
- **Unchanged:** every code block and check comment, and `guidecheck`'s counts. Rule citations are the same set per chapter as on `main`.
- **Anchors kept:** *One outcome, two encodings*, *Keys are resources* and *Inside the image*.

| Measure (chapters 7 to 9) | Before | After |
|---|---|---|
| Bullets | 40 | 4 (one numbered list) |
| Bold-lead bullets | 28 | 0 |
| Colon introducing a clause | 36 | 6 |
| "That is why/what" | 2 | 0 |
| "exactly" | 4 | 2 |

**Batch 3:** committed.

**Batch 4, 2026-11-25 (chapters 10 and 11, and `guide/README.md`), waiting for the user's review:**
- **Chapter 10:** the explanations after each excerpt are prose. *What next*'s reading suggestions became a closing paragraph. All seven excerpts still match the example's files, character for character.
- **Chapter 11:** the seven "**Why:**" labels are gone, with their reasons woven into each section. *Where to go from here* is a paragraph. The C and Java snippets, and every CardLang block, are unchanged.
- **`guide/README.md`'s *Writing for the guide*** now describes the guide as it is:
  - prose over lists, and lists without bold leads;
  - varied sentences instead of explanatory colons and pivot sentences;
  - no filler words;
  - each chapter opens in its own way, with no end-of-chapter exercise lists;
  - contractions in moderation;
  - and the earlier house rules.
- **Rule citations:** the same set per chapter as on `main`.

## 7. Done: the whole guide

| Measure (front page and chapters 1 to 11) | Before | After |
|---|---|---|
| Bullets | 174 | 19: the front page's chapter list (11), two numbered procedures (8) |
| Bold-lead bullets | 131 | 0 |
| Colon introducing a clause | 160 | 33, of which 11 are the chapter list's |
| "That is why/what/the point" | 9 | 0 |
| "exactly" | 21 | 9 |
| "whole" | 18 | 12, mostly literal ("the whole request") |
| "deliberately" or "on purpose" | 8 | 4 |
| *What next* sections | 10 | 0 |

Every example, scenario, excerpt and rule citation is unchanged, and so are `guidecheck`'s counts: 24 programs, 36 fragments, 28 errors, 16 scenarios and 7 excerpts.

**The README (user's request, 2026-11-25):** the same pass.
- **Rewritten as paragraphs:** the list of what the repository holds, the language's key properties, and the extension's features.
- **The VM's figures** stay a short list, without bold leads.
- **Unchanged:** the code block, the tables, every link and the licence facts. The link check passes.
