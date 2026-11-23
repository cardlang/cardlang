# G1 — First steps: detailed sub-plan

Planned 2026-11-23, the second work package of the guide's plan of plans. It writes chapters 1 and 2. They set the voice that the other chapters keep, so each is reviewed by the user before the next is written.

## 1. What there is now

- **The site and its check** (G0): `guide/` builds in strict mode, and `guidecheck` checks every example. Chapters 1 and 2 are stubs.
- **The front page** shows the counter: a `command` with an `if` / `else if` / `else` dispatch, a `persistent` counter, and slice assignment of `encode_be`.
- **The README's getting-started section** covers setup, the FIDO2 example, building, running a scenario, the debugger and `cardlang.json`, in six short steps.
- **The extension:**
  - commands Build Applet, Check Applet, Run Scenario and Debug Scenario;
  - snippets;
  - the settings `cardlang.repository`, `cardlang.uvPath` and `cardlang.scenarioBackend`.

  It finds the toolchain in the workspace folder, a folder above it, or `cardlang.repository`.
- **The vault's design** (`vault.md`):
  - chapter 1 has a counter that can be read and incremented;
  - chapter 2 turns the commands into an enum and the request's fields into typed values.
- **What the language allows for chapter 2:**
  - Enums carry no numeric value (TYP-11) and cannot be converted to or from integers (EXP-31).
  - A command byte therefore becomes an enum only through explicit decoding.

## 2. The work

### 2.1 Chapter 1: Getting started

The reader installs the tools, makes an applet of their own, and builds, runs and debugs it. The language comes in lightly: just enough to read the code, with each feature's chapter named.

1. **What you need.** uv, VS Code, the repository cloned, `uv sync`, and the extension from its latest release. It states what each step does, in plain terms.
2. **A look at a real applet.** Open `examples/fido2/ctap.card` for errors as you type, go to definition, and completion on `card.`. Kept short: the point is that the tools work.
3. **Your first applet** (Q1 decides where it lives):
   - a folder `vault/` with `cardlang.json` and `vault.card`;
   - a first version that only answers its counter (Q2);
   - Check Applet, and then Build Applet, with what the output means: the image, its size and its stack need.
4. **Running it.** `vault.scenario` with `install`, `power_on`, `command` and `expect`, then Run Scenario. Then the reader breaks an `expect` on purpose, to see a failure.
5. **Adding a command:** increment. This is the counter of the front page, reached in two steps.
   - It introduces `persistent` (the value survives power loss), `if` / `else if` / `else`, `require`, and `return Ok(…)` / `Err(…)`, each in a sentence or two, with a pointer to its chapter.
   - A compile error, seen in the Problems panel with its code.
6. **Debugging it.** A breakpoint in `process`, F5 on the scenario, stepping, and watching `counter` and the request and response bytes. Then the Traps breakpoint, by making the counter overflow.
7. **From a terminal.** `uv run clc check`, `build` and `run`, for scripts and CI.
8. **What next.**

**Checked:**
- each version of the vault, and its scenarios;
- the compile error;
- `cardlang.json`, by building the chapter's applet folder once, in the check;
- the extension steps, by doing them once by hand on this machine, from a fresh folder, and recording the outcome in this plan's Done section.

### 2.2 Chapter 2: Values and types

One section per kind of value, each with small fragments. The vault grows at the end.

1. **Integers.**
   - `u8` to `u32` and `i8` to `i32`, and literals in decimal, hex and binary;
   - literals take their type from where they are used;
   - no implicit conversion: `convert`, `checked_convert` and `truncate`;
   - overflow is a trap, and `wrapping_add` and `checked_add` exist for when you mean something else.
2. **`bool`** and conditions. There is no truthiness.
3. **Constants.** `const`, expressions evaluated by the compiler, and mixed operators needing parentheses (the front page's example, now explained).
4. **Arrays.**
   - `T[N]`, `.length` and indexing, and an out-of-range index as a trap;
   - array lists and `fill`;
   - `equal`, for comparing arrays.
5. **Structures:** declaring, constructing, and field access.
6. **Enums and `match`.** Variants have no numeric value. Every `match` lists every variant, so adding a variant shows every place to update.
7. **The vault, version 2** (Q3):
   - the commands as an enum, decoded from the request's first byte;
   - a `match` dispatching on them;
   - a fixed PIN as a `u8[4]` constant, with a verify command that compares it using `equal`. Chapter 5 makes the PIN persistent and changeable.
8. **What next.**

**Checked:** every fragment; each "this is wrong" example with its error code; the vault and its scenarios.

### 2.3 Showing a growing program (Q4)

The vault is shown in versions, and each version changes a few declarations. Under G0's rule (Q5) a program is joined from the blocks of one name within one chapter. A second version would have to repeat the whole program under a new name. Q4 decides how a block shows only what changed and is still checked.

### 2.4 The README

The README's getting-started section stays as the quick version, and ends by pointing to chapter 1. Making it shorter is left to G5.

## 3. Checks

- `run_checks` passes, including `guidecheck`, and the link check passes.
- `mkdocs build --strict` passes, and both chapters are viewed in the local preview.
- The chapter 1 steps in VS Code are done once by hand, as written.
- The user reviews chapter 1 before chapter 2 is written, and chapter 2 before G1 is merged.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | Where the reader's own applet lives | (a) any folder of their own, with `cardlang.repository` set once to the clone; (b) a folder inside the clone, so the extension finds the toolchain by itself | (a). An applet is the reader's project, not part of CardLang's repository, and the setting is one line, done once. (b) is simpler at first, but leaves their work inside someone else's git checkout |
| Q2 | How chapter 1's applet relates to the front page's counter | (a) it starts smaller, a counter that can only be read, and reaches the front page's counter by adding increment; (b) it starts from the front page's counter, pasted whole, and explains it | (a). Two steps give the reader a change to make, build and see, and the front page then reads as a preview. (b) is shorter but gives the reader nothing to do |
| Q3 | Turning the command byte into an enum, in chapter 2 | (a) a small `decode` function: an `if` chain from bytes to variants, returning `Err` for an unknown byte. Functions are used here and explained in chapter 3; (b) keep the commands as `const` bytes, and show enums on something else; (c) move enums to chapter 3, with functions | (a). Decoding bytes into typed values is what every applet does, and it shows why enums carry no number. Using one function before chapter 3 explains them costs a sentence |
| Q4 | How a block shows only what changed | (a) **declarations carry over:** a `program NAME` block continues the program from all earlier blocks of that name, in this chapter and earlier ones. A top-level declaration with the same name as an earlier one replaces it. A scenario runs against the program as it stands at that point; (b) keep G0's rule, and show each version whole under a new name; (c) the whole program per chapter in a hidden `.card` file, and the chapter's blocks checked to be excerpts of it | (a). The reader sees only the changed declarations, the check builds every version, and nothing is hidden from the reader. It changes `guidecheck`: declarations are found with the front end's parser, and each step is checked by injection. (b) gets long by chapter 5. (c) keeps a second copy of the program out of the reader's sight |

**Decided (user, 2026-11-23):**
- Q1 (a): the reader's applet lives in a folder of their own, with `cardlang.repository` set once.
- Q2 (a): chapter 1 starts with a counter that can only be read, and adds increment.
- Q3 (a): chapter 2 decodes the command byte with a small `decode` function.
- Q4 (a): declarations carry over. A `program NAME` block continues the program, a declaration of the same name replaces the earlier one, and a scenario runs against the program as it stands at that point.

## 5. Progress

**`guidecheck` carries declarations over (Q4), 2026-11-23:**
- A `program` block is split into its top-level declarations with the reference lexer, and each declaration replaces one of the same name or is added.
- The program as it stands is compiled at each scenario that uses it and at the end of each chapter that shows it.
- Checked by injection with temporary chapters:
  - a replacement carried into a second chapter, and a scenario there seeing the new version, passed;
  - a scenario expecting the old version failed;
  - a block starting with a statement failed;
  - an unterminated declaration failed;
  - a program with an unresolved name failed.

**Chapter 1, drafted 2026-11-23, waiting for the user's review:**
- **Done by hand from a fresh folder outside the clone** (the scratchpad), with `uv run --project <clone> clc`:
  - the `cardlang.json`, check, build and its output line;
  - both scenarios, including `capacity`;
  - the failing `expect`;
  - the trap and its line, `vault.card:14` after the increment step;
  - the `CE-EXP-1` message.
- **The VS Code steps** (the settings, Build, Run, F5, Traps) are written from the extension's README. They are not yet done by hand: the user's review covers them.
- **Two changes from §2.1:**
  - **The trap** is reading past an empty request, with the first `require` deleted, not an overflowing counter, which would take 2³² increments.
  - **The compile error** is shown as the output it prints, checked by hand, not as an `error` block. The mistake sits inside the command, and a checked fragment cannot contain a `command` (HEP-16).
