# SP0 — Foundations: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. No spec files are written until you approve this plan.

## 1. Scope

SP0 sets up the shared infrastructure that every later chapter uses. It writes **no language rules** apart from conventions.

| Output | Purpose |
|---|---|
| `plans_and_notes/decision-register.md` | Gives every recorded decision a stable `D-` ID for citation and traceability |
| `spec/01-scope-and-conventions.md` | Scope, layer boundary, normative wording, status tags, rule/error/trap ID schemes, judgment notation, example conventions, glossary |
| `spec/00-index.md` | Table of contents, spec status summary, and empty indexes for rules, compile errors and trap kinds |
| `spec/annex-C-open-issues.md` | Open-issue format, seeded with OI-1…OI-15 plus the decision-table qualifiers found in §2.3 below |
| `spec/annex-D-traceability.md` | Skeleton: a forward table (spec section → sources) and a reverse table (`D-` ID → rules or OI), with every `D-` row initially marked "pending SPn" |
| `conformance/README.md` | Conformance file format, directory layout and naming |

Sources: DN §1, §2, §3 (intro), §12, §13, the DN header (line 10 defines "agreed direction" and "proposal"), and PN §1.

## 2. Decision register

### 2.1 ID ranges

| Range | Content |
|---|---|
| `D-001…D-135` | The 135 rows of the DN §2 decision table, in table order. Topic and status text are copied **verbatim** |
| `D-201…` | Agreed items stated only in the platform notes and not already covered by a DN §2 row. Example: PN §5 says the platform must prevent other execution contexts from observing partial transactional state |
| `D-301…` | Agreed decisions stated only in DN body sections (for example the `require` expansion, `while true` completion and the `abort` operand forms). Later sub-plans add these as they reach each section, so SP0 creates only the range header |

### 2.2 Register columns

`ID | Topic (verbatim) | Recorded status (verbatim) | Spec tag | Layer | DN/PN detail sections | Owning SP | Linked OI`

- **Layer** is one of `language`, `platform`, `VM/profile` or `tooling`. It decides whether a row becomes a chapter rule or an Annex B `PLT-n` requirement.
- **Owning SP** is the sub-plan responsible for implementing the row. Annex D starts from this column.

### 2.3 Tag-mapping rule

The DN header (line 10) says an "agreed direction" records an explicit decision and a "proposal" records an idea still to validate. Recorded statuses map to spec tags as follows:

| Recorded status contains | Spec tag |
|---|---|
| Agreed, Agreed direction, Required feature, Compilation error, Forbidden, Not supported initially, Omitted initially | **[Agreed]** |
| One of the above plus an open qualifier, such as "detailed semantics open", "API not designed", "aggregate limits and storage details open", "event API deferred to platform" or "detailed typing open" | **[Agreed]** for the stated part, **plus a new OI** for the qualifier |
| Proposed, proposal, Proposed baseline, Feasibility direction, call-frame placement proposed | **[Proposal]**, with an OI where it affects acceptance or behavior |
| Platform requirement | **[Agreed]**, layer `platform`, so it becomes a `PLT-n` rule in Annex B |

Rows that need an open-qualifier OI (OI-16 onward):

| DN §2 row | Open qualifier |
|---|---|
| Explicit persistent state | Detailed semantics open |
| Simple persistent declarations plus an object API | API not designed |
| Every function returns a result | Detailed typing open |
| Each persistent assignment is atomic | Aggregate limits and storage details open |
| Application-specific global setup | Event API deferred (also covered by OI-7) |
| Resource storage strategy | Platform decision |
| By-value aggregate parameters | Call-frame placement proposed |

These rows go to Annex B as informative (non-normative) material only:

- Proposed baseline
- Compact VM with single-digit KiB RAM goals

## 3. `01-scope-and-conventions.md` contents

1. **Scope and non-scope.**
   - **In scope:** source-level syntax, static semantics and the language-visible dynamic semantics of one application.
   - **Out of scope (Annex B):** platform, VM, transport, bytecode, storage mechanisms, capacities and concrete error, trap and SW codes.
2. **Layer model.** Language, platform contract, VM/target profile, and transport. This states the separation rule from the plan of plans.
3. **Normative wording.** MUST, MUST NOT and MAY. Three outcome terms, each with a fixed meaning:
   - *compilation error*: the program is rejected;
   - *trap*: execution of the current command terminates with a fault;
   - *recoverable error*: an `Err` outcome.
4. **Status tags.** [Agreed], [Proposal] and [Open], with the rule that every [Proposal] or [Open] rule cites an OI.
5. **Rule IDs.** Chapter prefixes `LEX`, `NAM`, `TYP`, `CEX`, `EXP`, `STM`, `FUN`, `OUT`, `STA`, `TXN`, `HEP`, `RTF` and `PLT`. IDs are never reused or renumbered. A removed rule keeps its ID with the note "withdrawn".
6. **Diagnostics and fault IDs.**
   - `CE-<PREFIX>-<n>` identifies a compile-error *class*. Message wording is not normative.
   - `TRAP-<KIND>` identifies a language-level trap kind, such as `TRAP-OVERFLOW` or `TRAP-BOUNDS`. Numeric trap codes are platform-defined (Annex B).
7. **Notation.**
   - **Bidirectional typing judgments.** `Γ ⊢ e ⇒ T` means the type is synthesized from the expression. `Γ ⊢ e ⇐ T` means the expression is checked against an expected type T. This models the notes' contextual literal typing directly: literals only check and never synthesize. This is a notation choice, not new semantics.
   - Other judgments: `Γ ⊢ s ok` for statements, `Γ ⊢ e const` for constant expressions.
   - The environment Γ maps names to kind, type, mutability and parameter mode. It also records the enclosing function's success type and whether code is inside a loop or transaction.
   - **Meta-only outcome type.** `Outcome(T)` and `Outcome()` exist only inside the spec. They are **not** user-visible types (DN §6.3).
   - Evaluation results are written `v`, `Err(e)` or `trap(KIND)`. Evaluation rules are numbered steps, and each step states its failure result.
8. **Grammar notation.** W3C-style EBNF, defined once here and used in Annex A and the chapter fragments.
9. **Example conventions.**
   - Each example is labelled *valid* or *invalid*, and invalid examples give their `CE-`/`TRAP-` ID.
   - Scaffolding added to complete a notes fragment is marked with a `// scaffold` comment.
   - Examples are independent unless stated otherwise.
   - Each example links to its conformance file.
10. **Glossary.** Application, compilation unit, source file list, top-level declaration, host entry point (command), ordinary function, compiler intrinsic, platform API, outcome, recoverable error, error category, trap, security reset, persistent / session / local state, default value, transaction, reference, access path, view, slice, constant expression, platform-defined, target profile.
11. **Document status.** Draft version label (proposed: "CardLang Language Specification, Draft 0.1") and the rule for citing DN and PN by section number.

## 4. `annex-C-open-issues.md` format

Each issue is an entry with these fields:

- **ID** (`OI-n`) and title;
- **Kind:** contradiction, gap or proposal-to-validate;
- **Sources:** DN and PN sections, plus `D-` IDs;
- **Affected rules:** filled in by later SPs;
- **Options:** the possible resolutions;
- **Recommendation:** clearly marked as a recommendation, not a decision;
- **Status:** open or resolved, with the date and your decision.

The annex closes with a resolution log. SP0 seeds OI-1…OI-15 from the plan of plans and OI-16 onward from §2.3.

## 5. `conformance/README.md` format

- **Layout:**
  - `valid/`: must compile;
  - `invalid/`: must be rejected with a stated error class;
  - `runtime/`: must compile, then show a stated runtime result.
- **Single-file test name:** `<prefix>-<nnn>-<slug>.card`, for example `exp-014-mixed-operators.card`.
- **Multi-file test:** a directory containing the `.card` files and a `files.txt` that lists them. This mirrors the build-supplied file list (DN §4.1).
- **Header metadata** in the first comment lines:
  ```
  // rule: EXP-14, EXP-15
  // source: DN §3.5
  // status: agreed | proposal | open
  // expect: ok | compile-error CE-EXP-3 | trap TRAP-OVERFLOW | outcome Ok | outcome Err(WalletError.InsufficientFunds)
  ```
- **Runtime test inputs** (request bytes, initial state) are marked [Open]. SP11 and SP12 define them, because they depend on the host entry contract.

## 6. Steps

1. Build the decision register from DN §2 (135 rows) and PN, applying §2.1–§2.3.
2. Write `01-scope-and-conventions.md` as described in §3.
3. Write the `00-index.md` skeleton.
4. Write Annex C with OI-1…OI-15 and the qualifier OIs.
5. Write the Annex D skeleton, generated from the register's "Owning SP" column.
6. Write `conformance/README.md` and create the empty `valid/`, `invalid/` and `runtime/` folders, each with a `.gitkeep`.

## 7. Exit checklist

- The register has exactly as many `D-0nn` rows as the DN §2 table has rows. Check this by counting table rows in both files.
- Every register row has a tag, a layer and an owning SP. Every row with a qualifier links to an OI.
- Annex D lists every `D-` ID exactly once.
- Every OI has kind, sources, options and status.
- 01 defines every ID prefix and notation that the plan of plans uses.
- No language rule beyond the conventions has been written yet.

## 8. Choices made in this sub-plan

These are open for redirection:

- "Agreed direction" counts as [Agreed], based on the DN header.
- Bidirectional (`⇒` / `⇐`) judgment notation.
- W3C-style EBNF.
- Draft version label "Draft 0.1".
- Body-only decisions are added to the register lazily (`D-301…`) by the sub-plan that reaches them, not all extracted up front.
