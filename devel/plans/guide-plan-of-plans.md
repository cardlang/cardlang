# The CardLang guide: plan of plans

Planned 2026-11-22, at the user's request. The specification says exactly what CardLang means, for implementers and for settling edge cases. The guide teaches the language to someone who wants to write a program in it. It is less formal, shorter, and built around examples. This plan fixes the guide's shape, how its examples are kept correct, how it is published, and the order of the work. Each work package below gets its own detailed sub-plan, in `devel/plans/guide/`, before it is written.

## 1. Who it is for, and what it is

**The reader** is a programmer who knows C, Python, Java or a similar language. They may or may not have worked on embedded or security code, and they want to write an applet: a small program that keeps secrets and state on a microcontroller, in a TrustZone secure world, or on a smart card. They have VS Code, or are willing to use it.

**After the guide,** the reader can:
- write, build, run and debug an applet of their own;
- use outcomes, persistent state, transactions and the platform's APIs correctly;
- read the example applets;
- know when to look something up in the specification.

**What it is not:**
- not a second specification: it explains and motivates, and points to the rule (as in "EXP-14") rather than restating it;
- not exhaustive: corners go to the specification;
- not a description of the toolchain's internals.

## 2. Principles

1. **Non-normative, and linked.** Chapter 1 of the guide says that the specification is the authority. Where the guide relies on a rule, it names it, so the two cannot silently disagree.
2. **Every example is checked (Q3).** A test, run by `run_checks` and by GitHub, compiles every example in the guide. It checks that an example meant to fail fails with the error it names, and runs every scenario. An example that stops matching the language fails the build.
3. **One running example.** The chapters grow one applet, chosen in G0 (Q4), from a few lines to a complete program. A reader always sees each feature in a setting that needs it.
4. **Short chapters, plain words.** Each chapter teaches one idea, ends with what to try next, and takes about ten minutes to read.
5. **Current state only.** The guide names no development steps and does not link into `devel/`, like every document outside it; the link check enforces this.
6. **Written by Claude, reviewed by the user,** one chapter at a time. Each chapter is drafted, then the user reads it, then it is revised. The tone is set by the first chapters and then kept.

## 3. The outline

A tour of eleven chapters, which can grow into a book later:

| # | Chapter | What the reader learns |
|---|---|---|
| 1 | Getting started | Install the extension; open, build, run and debug an example; the first applet of their own |
| 2 | Values and types | Integers, `bool`, arrays, structures and enums; literals; constants; no implicit conversion |
| 3 | Control flow and scope | Blocks, `var` and assignment, `if`, `while`, `for`, `break` and `continue`, every path returning, scope without shadowing, an applet's files |
| 4 | Functions, references and views | Parameters, `ref` and `inout`, views; why references cannot escape |
| 5 | Outcomes | `Ok` and `Err`, error sets, `match`, `attempt`, `require`; traps, and why they differ from errors |
| 6 | State that survives | `persistent` and `session`, defaults, lifecycle handlers, atomic updates and transactions |
| 7 | Talking to the host | The `command` entry point, request and response bytes, the ISO 7816 and raw bindings |
| 8 | Using the platform | Keys and crypto, randomness, CBOR and TLV, through the Base Profile |
| 9 | Testing and debugging | Scenarios, `clc`, the debugger, traps and failed expectations |
| 10 | A real applet | A walk through part of the FIDO2 example, applying everything so far |
| 11 | Coming from C or Java Card | What is different, and why: no heap, no exceptions, no recursion, atomic state |

## 4. The work packages

| Package | Delivers | Depends on |
|---|---|---|
| **G0 Foundations** | The guide's folder and skeleton (Q1); the site tool and its configuration (Q2); `tests/guidecheck.py`, the example check (Q3), in `run_checks`; a GitHub workflow that builds the site and publishes it to GitHub Pages; the running example's design (Q4); a short style guide for the guide's voice | — |
| **G1 First steps** | Chapters 1 and 2. They set the tone the rest follows | G0 |
| **G2 The core** | Chapters 3, 4, 5 and 6 | G1 |
| **G3 Applets for real** | Chapters 7, 8 and 9 | G2 |
| **G4 Putting it together** | Chapters 10 and 11 | G3 |
| **G5 Polish and links** | A consistency pass; screenshots and a GIF of the extension; links from the README, the specification's index and the extension's README into the guide; the site's front page | G4 |

**With the launch:** G0 and G1 before the launch posts give readers somewhere to go after the README. The rest can follow, chapter by chapter.

**Branch:** the work is done on a branch `guide`, merged into `main` package by package, once each is reviewed.

## 5. Checks, for every package

- `run_checks` passes, including the guide's example check.
- The link check passes, including its guards.
- The site builds, locally and on GitHub, and its pages render. G0 and G5 check this by eye too.
- Each chapter is reviewed by the user before its package is merged.

## 6. Decisions for G0

| ID | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | Where the guide lives | (a) `guide/` at the top level, beside `language/`; (b) `language/guide/`, as part of the definition; (c) `docs/guide/` | (a). It is a document for users, not part of the definition, and a top-level folder is the easiest to find. The README links it |
| Q2 | How it is published | (a) MkDocs with the Material theme: Python, so a development dependency in the uv environment, built and published to GitHub Pages by a workflow; (b) mdBook, a single Rust binary, as *The Rust Programming Language* uses; (c) plain Markdown, read on GitHub, with no site | (a). It fits the project's Python and uv setup, with no extra toolchain. Material gives search, dark mode and code highlighting, and the same Markdown still reads on GitHub. Adding it is a `uv add --dev`, which is asked before it is done |
| Q3 | How the examples are kept correct | (a) the fenced code blocks in the chapters are checked where they are. A short comment before each one says what it is: a complete program, a fragment, or an example expected to fail with a given error; a runnable example is followed by its scenario; (b) the examples are separate `.card` files, included into the chapters when the site is built | (a). A chapter stays readable on GitHub, where includes do not render, and an example is edited where it is read. The check works like the grammar check's reading of the design notes |
| Q4 | The running example | (a) a small PIN-protected secret store, grown across the chapters: a counter first, then a PIN with retries, then a stored secret, then a signature; (b) the counter only, kept small; (c) the FIDO2 example only | (a). It needs every core feature (outcomes, persistent state, transactions, the platform's crypto) and stays small enough to follow. Chapter 9 then shows the FIDO2 example as the real-world version |

**Decided (user, 2026-11-22):**
- Q1 (a): the guide lives in `guide/`.
- Q2 (a): MkDocs with the Material theme. Adding it as a development dependency is asked before it is done.
- Q3 (a): the fenced code blocks are checked where they are.
- Q4 (a): the running example is a PIN-protected secret store.

**Changed (user, 2026-11-23, reviewing chapter 3):** the outline had no place for control flow, or for how an applet's files share one scope. A new chapter 3, *Control flow and scope*, teaches both, and the later chapters move up by one. *Functions, references and slices* became *Functions, references and views*, since slices are taught with arrays in chapter 2. G2 now covers chapters 3 to 6.
