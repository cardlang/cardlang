# The CardLang Guide

A guide that teaches CardLang by example, for programmers who want to write applets. It is published at **[cardlang.github.io/cardlang](https://cardlang.github.io/cardlang/)**, and its chapters read here too:

- [Introduction](docs/index.md)
1. [Getting started](docs/01-getting-started.md)
2. [Values and types](docs/02-values-and-types.md)
3. [Functions, references and slices](docs/03-functions-references-slices.md)
4. [Outcomes instead of exceptions](docs/04-outcomes.md)
5. [State that survives](docs/05-state.md)
6. [Talking to the host](docs/06-host.md)
7. [Using the platform](docs/07-platform.md)
8. [Testing and debugging](docs/08-testing-and-debugging.md)
9. [A real applet](docs/09-a-real-applet.md)
10. [Coming from C or Java Card](docs/10-coming-from-c.md)

The guide is not normative: the [specification](../language/spec/00-index.md) is.

## Building the site

The site is built with MkDocs and the Material theme, from the repository's uv environment (`uv sync` once). From the repository root:

```bash
uv run mkdocs serve -f guide/mkdocs.yml
```

serves a live preview, and `uv run mkdocs build --strict -f guide/mkdocs.yml` builds it into `guide/site/`. GitHub builds it on every change to the guide, and publishes it from `main` (`.github/workflows/guide.yml`).

CardLang and scenario code is highlighted by the package's own Pygments lexers, in `src/cardlang/highlight.py`. Use `cardlang` and `scenario` as the language of a fenced block.

## Every example is checked

`tests/guidecheck.py`, run by `tests/run_checks.py` and by GitHub, checks every `cardlang` and `scenario` block. A comment on the line before each block says what it is:

| Comment | The block |
|---|---|
| `<!-- check: program NAME -->` | Top-level declarations of the program `NAME`. They carry over: a block continues the program from every earlier block of that name, in this chapter and earlier ones, and a declaration with the same name as an earlier one replaces it. So a chapter shows only what changed. The program must compile at the end of each chapter that shows it. Add `binding=iso7816` for the ISO 7816 binding (the default is raw) |
| `<!-- check: fragment -->` | A fragment that must compile |
| `<!-- check: error CE-XXX-n -->` | A fragment that must fail with exactly that error |
| `<!-- check: scenario NAME -->` | A scenario for the program `NAME` as it stands at that point, run on the reference interpreter and the Python VM |
| `<!-- check: none -->` | Shown, not checked. Use it rarely |

A block without a comment fails the check.

## Writing for the guide

- **Talk to the reader:** "you write…", "your applet…".
- **Show, then explain.** A short piece of code first, then what it does and why.
- **One idea per section,** in short paragraphs. Each chapter ends with what to try next.
- **Name the rule** the first time it matters, as in *EXP-14*, and leave the exact wording to the specification.
- **Grow the running example,** the vault, rather than inventing a new program for each feature, unless a small fragment shows the point better.
- **Describe the language as it is.** Plain words, current state, no history of how it came to be.
