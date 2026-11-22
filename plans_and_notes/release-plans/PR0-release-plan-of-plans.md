# PR0 — Preparing the repository to be public: plan of plans

Agreed with the user on 2026-11-22. Release-preparation work packages are numbered `PR-n`. Each gets its own detailed sub-plan before it starts, as every work package has. Nothing is removed by this plan: content is moved, separated and cleaned up.

## 1. The principle

Everything in the repository is one of three kinds, and each kind gets its own place:

1. **The language definition:** what CardLang *is*. The normative specification, the conformance suite that pins it down, and the rationale behind it: the design notes and the decision register. The platform profile is a separate specification, and so sits beside the language rather than inside it.
2. **The implementation:** what someone *uses*.
   - the Python toolchain: front end, compiler, bytecode, interpreter, the Python VM, harness, command line, language server and debugger;
   - the C VM;
   - the editor extension;
   - the example applets.
3. **Development aids:** how the project *got here*. The work-package plans, step notes, measurement reports, findings, test generators, history scripts and measurement scripts. They are kept, but in a place of their own, clearly apart.

## 2. The target layout

```
README.md  LICENSE  CONTRIBUTING.md
language/                 the definition
  spec/                   the specification (was spec/)
  conformance/            the conformance suite (was conformance/)
  rationale/              design notes, decision register, draft release notes and candidates
platform/                 the Base Profile, a platform specification: profile, base types, API catalog
vm/                       the VM: its design documents (decisions, execution model, HAL, bytecode, image format)
  c/                      and the C VM
src/cardlang/             the Python toolchain, one installable package
  front/                  lexer, checkers, diagnose, projects (was tools/checkers)
  bytecode/               instruction set, image, debug information, disassembler
  compiler/               typer, compiler
  interp/                 the reference interpreter
  pyvm/                   the Python VM, its HAL and natives (was tools/vmproto)
  harness/                scenarios and backends
  lsp/  dap/              language server and debug adapter
  cli.py                  clc, an installed command
editors/vscode/           the VS Code extension
examples/                 each applet self-contained:
  fido2/                    sources, cardlang.json, scenarios, its own checker, a README
  piv/
tests/                    run_checks.py, and the checks of the tools and of the definition
devel/                    development aids
  plans/                  every plan: spec, VM, tooling and release, and the plans of plans
  reports/                measurements, findings, step notes, the consolidation report
  generators/             conformance test generators, the rule index, coverage
  history/                one-off scripts behind past changes
  measure/                measurement scripts (measure.py, revision.py, the C VM's measure.py)
```

**Items that sit between groups:**
- **The reference checkers.** As code they are the toolchain's front end, `src/cardlang/front/`, used by the compiler and the language server. Their other job is verifying the definition: `tests/` runs them against `language/conformance/`. <!-- linkcheck: ignore -->
- **The specification checks** (`speccheck`, `grammar`, `profilecheck`) maintain the definition. They live in `tests/`, as checks of `language/` and `platform/`.
- **The reference interpreter** is an executable reading of the specification. It is part of the toolchain, as a backend, and is documented as the semantic oracle that the VMs are measured against.
- **The VM's design documents** stay with the C VM in `vm/`. The language specification deliberately leaves the VM out, so they are not part of `language/`.

**Two renames:**
- **The prototype VM becomes `pyvm`,** both the package (`cardlang.pyvm`) and the backend name (`clc run --backend pyvm`, the extension's `cardlang.scenarioBackend`). It is renamed as it moves into the package (PR5c), since that move changes all of its imports anyway. Historical reports keep the name `vmproto`, which it had when they were written.
- **The applet checkers move into their applets,** `examples/fido2/check_fido2.py` and `examples/piv/check_piv.py`, so each applet is a complete unit. <!-- linkcheck: ignore -->

## 3. The work packages

Every work package keeps `run_checks` passing, and moves files with `git mv` so their history is kept.

| PR | Work | Why in this order |
|---|---|---|
| **PR1 Foundations for moving** | **(a) One place for paths:** a module that knows where the repository's parts are (spec, conformance, platform, examples, VM). Every tool asks it, rather than building `repo / "conformance"` itself. **(b) A link check:** every relative link and file path named in the Markdown files must exist. It joins `run_checks` | Later moves then touch one module and are checked mechanically |
| **PR2 Development aids into `devel/`** | Plans, reports, findings, step notes, generators, history and measurement scripts | Few code dependencies, many links: the link check proves the move |
| **PR3 The definition into `language/`** | `spec/`, `conformance/`, and the rationale: design notes, decision register, draft release notes and candidates. `platform/` stays at the top level | The paths module makes the code side one change |
| **PR4 Self-contained examples** | Each applet gets its checker, its scenarios and a README | Small, independent |
| **PR5 The Python package `src/cardlang/`** | In stages, each passing `run_checks`. **(a)** `pyproject.toml` gains a build backend, and `bytecode` and `compiler` move in. Compiling runs the full diagnostics, closing finding T1. **(b)** `front`. **(c)** `interp`, `pyvm` (the rename) and `harness`. **(d)** `lsp`, `dap` and `cli`, with `clc` an installed command. The `sys.path` editing in 44 files goes away stage by stage | The largest change, so it is split into stages that can each be checked | <!-- linkcheck: ignore -->
| **PR6 The extension into `editors/vscode/`** | It finds its tools through the installed package and commands | After PR5, so it can use them |
| **PR7 Content cleanup** | A README per top-level area; current-state wording in place of "in progress" notes; stale statements fixed; `CONTRIBUTING.md`; a `.gitignore` review; a scan for anything personal or machine-specific, such as absolute paths and user names in the plans and reports | Once things are where they will stay |
| **PR8 The licence and the release check** | The licence, chosen by the user; a final review against a public-release checklist | Last |

## 4. Decisions made (user, 2026-11-22)

| ID | Decision |
|---|---|
| R1 | Three kinds of content, separated: the definition, the implementation, and development aids. Nothing is removed |
| R2 | The names `language/` and `devel/` |
| R3 | The Base Profile stays a top-level `platform/`, beside the language rather than inside it |
| R4 | All plans go to `devel/plans/`. The top-level README links to the plans of plans |
| R5 | `vm/` keeps the VM's design documents beside the C VM |
| R6 | Examples at the root, each applet self-contained with its checker |
| R7 | The prototype VM becomes `pyvm`, renamed during its move into the package (PR5c) |

## 5. Decisions for the work packages

These are asked when their work package is planned.
- **PR5:**
  - the build backend: `hatchling` or `uv_build`;
  - whether the old import paths are removed outright, or kept as shims;
  - whether compiling refuses invalid programs (T1).

  The draft that preceded this plan recommended: `hatchling`, no shims, and refusing.
- **PR8:** the licence.
