# CardLang Language Specification — Plan of Plans

## Context

`plans_and_notes/` holds two documents:

- `card-language-design-notes.md`: 2,854 lines, dated 2026-11-13 and updated 2026-11-15. It is a brainstorming record that says it is **not normative**. Its §2 decision table has about 135 rows, plus detailed sections §3–§14.
- `cardlang-platform-notes.md`: 125 lines, dated 2026-11-14. It covers the platform/runtime boundary, resources, lifecycle and VM targets.

The goal is a **full, normative CardLang language specification**. The specification must:

1. preserve agreed decisions and keep them distinct from proposals and open questions;
2. flag gaps and contradictions instead of inventing semantics;
3. keep language rules separate from VM, platform and transport contracts;
4. give precise grammar, typing rules and evaluation rules, with valid and invalid examples;
5. include a traceability table from specification sections to the design notes.

This document is the **plan of plans**. It splits the work into sub-plans (SP0–SP14). Each sub-plan gets its own detailed plan before drafting. This document fixes the conventions, ordering and exit criteria they all share.

Choices you confirmed:

- a multi-file `spec/` folder;
- numbered normative rules plus typing judgments and step-by-step evaluation order;
- a separate `conformance/` corpus of valid and invalid test files.

## Deliverables (repo layout)

```
plans_and_notes/
  specification-plan-of-plans.md   ← this plan, saved into the repo
  spec-plans/SPnn-<topic>.md       ← one detailed sub-plan per workstream
  decision-register.md             ← design-note decisions with stable IDs (SP0)
spec/
  00-index.md  01-scope-and-conventions.md  02-lexical-structure.md
  03-program-structure-and-names.md  04-types.md  05-constant-expressions.md
  06-expressions.md  07-statements-and-control-flow.md
  08-functions-and-references.md  09-outcomes-and-errors.md
  10-state-and-initialization.md  11-transactions.md  12-host-entry-point.md
  13-runtime-failures.md
  annex-A-grammar.md  annex-B-platform-contract.md
  annex-C-open-issues.md  annex-D-traceability.md
conformance/
  README.md  valid/  invalid/  runtime/
```

## Ground rules for every sub-plan

- **Status tags.** Every normative rule carries exactly one tag:
  - **[Agreed]**: the design notes record an explicit decision.
  - **[Proposal]**: the notes call it a proposal or direction, or it is my suggestion to fill a gap. The rule's text must say so and cite an open issue.
  - **[Open]**: no decision exists. The rule is a placeholder that points to Annex C.
- **No silent invention.** If a rule needs semantics the notes lack, the sub-plan logs an `OI-nnn` entry in Annex C. The entry gives the options and a recommendation. The rule is then written as [Open] or [Proposal]. You resolve open issues. Resolutions are recorded in Annex C's resolution log and then reflected in the spec. The design notes stay untouched as the historical source unless you ask otherwise.
- **Rule IDs.** Rules are numbered as stable chapter-prefixed IDs: `LEX-n`, `NAM-n`, `TYP-n`, `CEX-n`, `EXP-n`, `STM-n`, `FUN-n`, `OUT-n`, `STA-n`, `TXN-n`, `HEP-n`, `RTF-n`, and `PLT-n` for platform requirements in Annex B.
- **Rule format.**
  - Typing rules use judgments: `Γ ⊢ e : T` for expressions, `Γ ⊢ s ok` for statements, `Γ ⊢ e const` for constant expressions.
  - Evaluation rules are numbered steps. Each step states its failure outcome: compile error ID, trap kind, or `Err`.
  - Compile-error IDs (`CE-<CHAPTER>-<n>`) and trap kinds (`TRAP-<kind>`) are defined in their chapters and indexed in 00-index.
- **Layer separation.** Chapters 01–13 specify language-visible behavior only. Anything the platform, VM or transport decides is a reference to an Annex B `PLT-n` requirement or a "platform-defined" item. Examples: SW mapping, capacities, error and trap codes, lifecycle events, journaling, view representation. Chapters never fix those values.
- **Examples.**
  - Each chapter section ends with valid and invalid examples. Each invalid example names its `CE-`/`TRAP-` ID.
  - Each example also exists as a conformance file whose header carries metadata, for example `// rule: EXP-14` and `// expect: compile-error CE-EXP-3`, `trap TRAP-OVERFLOW`, or `ok`.
  - Examples taken from the notes keep their meaning. Notes examples that are fragments get completed with minimal, clearly marked scaffolding.
- **Traceability.** Every rule cites its sources as decision-register IDs (`D-nnn`) and design-note or platform-note section numbers, for example `DN §3.5` or `PN §5`. Annex D is the reverse index: every `D-nnn` maps to the rule(s) that implement it, or to an `OI-nnn` if it's not covered.

## Seed register of contradictions and gaps (goes to Annex C in SP0)

I found these while reading the notes. Sub-plans add to this list; they never resolve an item silently.

**Contradictions**

- **OI-1.** DN §1 says the "source extension … not yet fixed". The DN §2 decision table says `.card` is agreed.
- **OI-2.** The PN §1 table still describes `command` with "dispatch, command identifiers". That predates the single byte-oriented entry point adopted in DN §4 (2026-11-15).
- **OI-3.** Nested transactions: DN §7.3 says "reject statically when the compiler can establish it, otherwise runtime trap". That conflicts with the DN §3.10 goal that acceptance must not depend on the optimizer. A static acyclic call graph makes a deterministic rule possible.

**Gaps**

- **OI-4.** There is no complete keyword or reserved-name list. This covers `Ok`, `Err`, `fill`, `convert`, the `checked_*` and `wrapping_*` intrinsics, `in`, `else`, `errors`, and platform names.
- **OI-5.** Entry-point identification: is the name `process` reserved, or is any single `command` declaration the entry point?
- **OI-6.** Platform-API call syntax (`card.crypto.hash_update`) versus the rule that dot access resolves from the receiver's type and that there are no namespaces.
- **OI-7.** Lifecycle-handler declaration syntax is absent, yet nondefault persistent setup depends on it.
- **OI-8.** Where `attempt` may appear as an expression: in arithmetic operands, conditions, `require`, and index expressions. The notes use it in indices and initializers.
- **OI-9.** Evaluation order for assignment destinations with several indices or nested paths. DN §8.2 defines only a single index.
- **OI-10.** The slice details that DN §8.4 lists as remaining: endpoint typing and evaluation order, standalone slices, and whether a slice can satisfy a `T[N]` parameter.
- **OI-11.** The constant-evaluation boundary algorithm is still a proposal (DN §3.10). Whether a constant out-of-range index into mutable storage is a compile-time error is open.
- **OI-12.** The `byte` alias for `u8` is a proposal.
- **OI-13.** Error sets: may an application have zero error sets? Is `return checked_add(a, b);` a valid forwarding return?
- **OI-14.** Literal-only comparisons with no integer context (`1 == 1`). Lexical limits for over-large literals and an empty `0x`.
- **OI-15.** The platform error catalog (`CardError`) for checked arithmetic and conversion, and the trap catalog. Both are platform-defined, but the spec needs named placeholders.

## Sub-plans (workstreams)

Each sub-plan file contains: scope, source sections and `D-` IDs covered, the rule list to write, grammar productions, typing judgments, evaluation rules, the example and conformance list, open issues raised, and exit criteria.

| SP | Output | Main sources | Depends on |
|---|---|---|---|
| **SP0** Foundations | `01-scope-and-conventions.md`, `00-index.md` skeleton, `decision-register.md` (DN §2 rows → `D-001…`, plus PN agreed items), glossary, conformance file format in `conformance/README.md`, Annex C seeded with OI-1…15, Annex D skeleton | DN §1, §2, §13; PN §1 | — |
| **SP1** Lexical structure | `02-lexical-structure.md` and the lexical part of Annex A | DN §3.0, §3.3 (literal forms), §6.5 (negative minimum) | SP0 |
| **SP2** Program structure and names | `03-program-structure-and-names.md`: compilation unit, file list, top-level declarations, shared scope, no shadowing, reserved names, declaration placement | DN §3.0, §4.1, §4.2, §5.1, §3.6 (scope) | SP1 |
| **SP3** Types | `04-types.md`: primitives, bool, arrays `T[N]`, unsized `T[]` parameter types, structs, enums, nominal identity, finiteness, defaults table, no implicit conversions | DN §3.1, §3.4, §3.11, §8, §8.2, §9–§9.3, §3.9 (defaults) | SP2 |
| **SP4** Constant expressions | `05-constant-expressions.md`: the constant subset, dependencies and cycles, compile-time failure, short-circuiting, array lengths. The boundary algorithm is tagged [Proposal] | DN §3.10, §3.3 | SP3 |
| **SP5** Expressions | `06-expressions.md`: contextual literal typing, operators, the mixed-operator grouping rule, evaluation order, arithmetic and shift edge cases, indexing and `.length`, field access, constructors, `fill`, conversion, checked and wrapping intrinsic catalog, no nested calls in arguments | DN §3.2, §3.3, §3.5, §6.2, §6.5, §8.1, §8.3, §9.3 | SP3, SP4 |
| **SP6** Statements and control flow | `07-statements-and-control-flow.md`: `var`, assignment (including indexed-assignment order), `if`, `while`, `for`, `break`, `continue`, `return`, `require`, `match` for enums, blocks and scope, completion analysis | DN §3.6, §3.7 (completion), §8.2 | SP5 |
| **SP7** Functions, references and slices | `08-functions-and-references.md`: declarations, parameter modes, call-site modes, argument preparation, aliasing and access-path permissions, forwarding, slices, the static call graph (no recursion), value copies | DN §3.7, §3.8, §8.4 | SP5 |
| **SP8** Outcomes and errors | `09-outcomes-and-errors.md`: transient outcomes, `Ok`/`Err` syntax, outcome `match` patterns, `attempt`, forwarding returns, the `errors` declaration, restricted error bindings, error categories | DN §6.1, §6.3, §3.6 (patterns), §3.2 (`checked_convert`) | SP6, SP7 |
| **SP9** State and initialization | `10-state-and-initialization.md`: `persistent`, `session` and `const` semantics, defaults timing, no mutable-global initializers, lifecycle-handler boundary (OI-7), atomic persistent assignment | DN §3.9, §5, §5.1, §7.1, §6.4 (session) | SP3, SP8 |
| **SP10** Transactions | `11-transactions.md`: the block, commit point, read-your-writes, participation, `abort Err`, boundary rule, no nesting (OI-3), traps inside transactions | DN §7.2–§7.4, §3.6 (boundary) | SP8, SP9 |
| **SP11** Host entry point | `12-host-entry-point.md`: the `command` signature, request and response views, the count contract, non-interleaving, reporting categories (language side only) | DN §4, §6.3 (host reporting) | SP7, SP8 |
| **SP12** Runtime failures | `13-runtime-failures.md`: trap kinds, what traps preserve and discard, security reset as seen by the language, the four-category outcome model | DN §6.4, §6.5, §12; PN §3, §5 | SP9–SP11 |
| **SP13** Platform contract annex | `annex-B-platform-contract.md`: `PLT-n` requirements the language places on any conforming platform, plus an explicit list of platform-defined items (SW mapping, capacities, error and trap catalogs, lifecycle events, resource API, journaling, target profiles, VM format). The runtime-resource identifier model is described as platform API guidance, not language syntax | PN (all), DN §11, §12, §4 (transport) | SP9–SP12 |
| **SP14** Consolidation | Complete `annex-A-grammar.md` (whole EBNF, cross-checked against every chapter); final `annex-C-open-issues.md`; complete `annex-D-traceability.md`; conformance completeness; a cross-chapter consistency review. Also verify that the three representative apps from DN §13 (counter, wallet, signer up to the platform-API boundary) can be written using only [Agreed] rules, and list what blocks them | everything | SP1–SP13 |

**Order:** SP0, SP1, SP2 and SP3 run in sequence. After that, SP4 and SP5. Then SP6 and SP7 can run in parallel. Then SP8 → SP9 → SP10, SP11 and SP12 → SP13 → SP14.

## Per-sub-plan workflow

1. Write `plans_and_notes/spec-plans/SPnn-<topic>.md` using the template above. Present it to you for review before drafting, and list any new open issues it needs decided.
2. Draft the chapter: rules, grammar fragment, judgments, evaluation steps and examples.
3. Add conformance files for every example.
4. Update Annex A (grammar fragment), Annex C (new or changed OIs) and Annex D (the `D-` → rule mapping).
5. Run the sub-plan's exit checklist (see Verification). Commit only when you ask.

**Commit conventions:** use the repo-local author `cardlang` with an empty email, and **no `Co-Authored-By` trailer**. You asked for that.

## Immediate next steps after approval

1. Save this plan as `plans_and_notes/specification-plan-of-plans.md`.
2. Start SP0 by writing its detailed sub-plan `plans_and_notes/spec-plans/SP00-foundations.md` for your review.

## Verification

For each sub-plan, and again globally in SP14:

- **Traceability coverage.** Every `D-nnn` in the decision register appears in Annex D and maps to at least one rule ID or an `OI-nnn`. Every rule cites at least one source. Check by grepping rule IDs and `D-` IDs and diffing the two sets.
- **Status integrity.** No rule lacks a tag. Every [Proposal] or [Open] rule references an existing `OI-nnn`. Check by grep.
- **Grammar consistency.** Every syntax form used in chapter examples is derivable from Annex A. Manually walk each example's productions. In SP14, do a full pass over all conformance files.
- **Examples.** Every invalid example names an existing `CE-`/`TRAP-` ID defined in its chapter. Every conformance file has valid metadata (rule, expect) and its rule ID exists.
- **Layer separation.** Grep chapters 01–13 for concrete platform values: SW codes, byte capacities, numeric error codes other than application examples. None should appear outside Annex B references.
- **Fidelity.** Spot-check every [Agreed] rule against its cited note section to confirm no meaning changed. Any deliberate wording tightening is noted in the rule's rationale line.
