# G6 — The platform reference: detailed sub-plan

Planned 2026-11-24, after the user asked whether the guide should have a dedicated platform reference: one place listing the APIs, the platform's errors and the trap kinds. G5 is complete; this adds one page to the guide before it goes live.

## 1. What there is now

- **`platform/base-catalog.txt`:** 36 APIs in six families (`key` 4, `crypto` 18, `random` 1, `cbor` 7, `der` 3, `tlv` 3). Each has the fields `params`, `payload`, `transaction`, `errors` (in precedence order), `resources`, `on-failure`, `permission` and `summary`. `pltcheck.load_catalog` reads it.
- **`platform/base-types.card`:** the profile's types, such as `KeySpec`, `KeyType`, `KeyStorage`, the algorithm enums and `CborHead`.
- **`platform/base-profile.md` §4:** the `CardError` table, read by `cardlang.platform.errors`.
- **The spec's RTF-4:** the trap kinds, in a table.
- **The guide:** chapter 8 has a hand-written `CardError` table, chapter 9 a table of trap kinds, and chapter 8 points to the catalog file for each API's errors.
- **The precedent:** `tests/rule_index.py` generates the spec's index of rules from the chapters.

## 2. The work

### 2.1 The page

A page after chapter 11, under a *Reference* heading in the navigation: `guide/docs/reference-platform.md`, *Platform reference* (Q1). It begins with a short paragraph:
- the page lists what the Base Profile gives an applet;
- it is generated from the profile, so it is always current;
- the profile and the specification are the authority.

**Its sections:**
1. **APIs,** one section per family (Q4). For each API:
   - its call, as CardLang, such as `card.key.generate(id: u32, spec: KeySpec)` or `card.crypto.sign(…) -> u32`;
   - the summary;
   - its errors, in precedence order;
   - how it behaves in a transaction;
   - the resources it creates, uses or deletes, when it has any.
2. **Types:** the enums and structures of `base-types.card`, as CardLang declarations.
3. **The platform's errors:** member, code, and when it is returned, from the profile's table.
4. **Trap kinds:** kind, and when it happens, from RTF-4.

**Links:** each `CardError` member in an API's errors links to its row in section 3. Each type in a signature links to its declaration in section 2.

### 2.2 The generator and its check (Q2)

- **`tests/guide_reference.py`:**
  - it reads the catalog with the same reader the compiler uses, `base-types.card`, the profile's table and the spec's RTF-4 table;
  - it writes the page;
  - `--check` compares instead of writing, and fails when the page is out of date, naming what differs.
- **In `run_checks`,** with `--check`. Changing the catalog without regenerating the page fails the checks, as for the rule index.
- **Checked by injection:** an edited summary in the catalog, a removed `CardError` row, and a hand edit to the page each fail `--check`.
- **`guidecheck`** ignores the page's CardLang blocks, which are signatures and declarations, through `check: none`. The generator writes those comments. The page is generated and checked as a whole, so the comments are not a loophole.

### 2.3 Chapters 8 and 9 (Q3)

The two tables are replaced by links (Q3 b):
- **Chapter 8's** *The platform's errors* keeps its prose: each API returns only some errors, the precedence, failure changing nothing, no traps for argument values, and what the host sees. It links to the reference for the members and their codes.
- **Chapter 9's** *Trap kinds* keeps its prose: the kind is for testing, and the host usually learns only that a trap happened. It links to the reference for the list.
- **Chapter 5's** pointer goes to the reference too.

### 2.4 The rest

- The front page's chapter list and *Where to start* gain the reference, and so does `guide/README.md`.
- The link check and `mkdocs build --strict` pass, and the page is viewed in the preview.

## 3. Checks

- `run_checks` passes, including `guide_reference.py --check` and the link check.
- `mkdocs build --strict` passes.
- The user reviews the page.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | What the reference covers | (a) **the platform:** APIs, the profile's types, `CardError` and trap kinds; (b) also the tools: scenario steps and expectations, and the `clc` commands; (c) only the APIs and the errors | (a). It answers "what can I call, what can it return, what can go wrong" in one place. The tools are a different subject: chapter 9 already lists the scenario forms, and a tools reference could be a second appendix later |
| Q2 | How the page is kept current | (a) a generated Markdown page, committed, with a `--check` in `run_checks`, as for the spec's rule index; (b) generated while the site is built, by an MkDocs hook, so it never exists in the repository | (a). The page reads on GitHub like every other chapter, a change to it shows in diffs, and it works the same with any site tool, including a later move to Zensical |
| Q3 | Chapter 8's `CardError` table and chapter 9's trap kinds | (a) keep both, link each to the reference, and have `guidecheck` verify that chapter 8's table names exactly the profile's members and codes, and chapter 9's exactly RTF-4's kinds; (b) replace them with links to the reference | (a). Each table is short, and explains its subject where the reader meets it. The check stops them drifting |
| Q4 | How each API is laid out | (a) a small block per API: its call as a CardLang signature, then the summary, errors, transaction behaviour and resources as short lines; (b) one table per family, with a column per field | (a). Signatures are long, and a table with eight columns does not fit a phone or a narrow window |

**Decided (user, 2026-11-24):**
- Q1 (a): the platform, meaning the APIs, the types, `CardError` and the trap kinds.
- Q2 (a): a committed, generated page, with `--check` in `run_checks`.
- Q3 (b): chapters 8 and 9 replace their tables with links to the reference.
- Q4 (a): a block per API.

## 5. Done (2026-11-24, uncommitted, waiting for the user's review)

- **`tests/guide_reference.py`** writes `guide/docs/reference-platform.md`, and is in `run_checks` with `--check`. The page has:
  - all 36 APIs, by family, as blocks (Q4): the signature, the catalog's summary, types linked to their declarations, errors in precedence order linked to their rows, transaction behaviour, resources, and non-default failure and permission;
  - the profile's types, in the groups of `base-types.card`, each group with its comment. The file's own header comment is left out;
  - the `CardError` table (BP-12);
  - the trap kinds (RTF-4).
- **Injection:** an edited catalog summary, a removed `CardError` row, and a hand edit to the page each failed `--check`.
- **Chapters 8 and 9** dropped their tables for links (Q3). Chapter 8 kept its prose about errors, and chapter 9 its prose about trap kinds. Chapter 5's pointer and chapter 8's catalog links now go to the reference. Chapter 5's four-row table of checked-arithmetic errors stays, as a teaching table.
- **The navigation** gains a *Reference* section, and the front page and `guide/README.md` list the page.
- **Found:** RTF-4's `BOUNDS` row does not mention slice assignments of different lengths, which FUN-24 makes `trap(BOUNDS)`. Chapter 9's hand table had added it; the generated page follows RTF-4. Fixing RTF-4 is offered to the user.
- **RTF-4 fixed (user):** the `BOUNDS` row now names slice assignments whose sides differ in length, and cites FUN-24. The reference was regenerated from it; `--check` failed until then, as it should.
