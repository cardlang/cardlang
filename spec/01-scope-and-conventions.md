# 1. Scope and conventions

CardLang Language Specification, **Draft 0.1**. Chapter status: complete for SP0.

This chapter defines what the specification covers, how its layers are separated, and the conventions every later chapter uses: rule status, rule and diagnostic identifiers, notation and examples. It contains no language rules of its own.

## 1.1 Scope

This specification defines the **CardLang** language (D-001, D-002) for writing one card application:

- the source text accepted as a CardLang application (lexical structure and grammar);
- the static semantics: name resolution, typing, constant evaluation and the other compile-time checks;
- the **language-visible** dynamic semantics: evaluation order, values and copies, references, outcomes, traps, persistent, session and local state, transactions, and the contract of the host entry point as seen by application code.

The following are **outside** the normative chapters. They are named in Annex B as platform requirements or platform-defined items, and are not specified here:

- card platform services, permissions and the platform API catalog;
- lifecycle events beyond those this specification defines (see the open issue OI-7), installation, upgrades and migration;
- transport framing, APDU layout, status-word (SW) values and the encoding of outcome categories;
- concrete numeric codes for platform errors and traps;
- storage, journaling and recovery mechanisms, and atomic-write and transaction capacities;
- VM design, bytecode, verification, ABI, memory layout and target-profile limits;
- build-configuration and manifest formats, beyond the facts the language depends on (an explicit source-file list and a build-supplied application identity, D-021).

### Design intent (informative)

The design notes propose a familiar imperative baseline: braces and statements, static types, explicit type annotations, and no inheritance, operator overloading or implicit dynamic allocation (D-134, DN §3). This paragraph is informative. The normative rules in later chapters take precedence wherever they are more specific. The notes also say the language frontend should stay separate from the VM, so that another language could target the VM later (DN §3).

## 1.2 Layer model

| Layer | Defines | Where specified |
|---|---|---|
| **Language** | Source syntax, static rules and language-visible behavior | Chapters 2–13 |
| **Platform contract** | What any conforming card platform must guarantee to CardLang programs, and what it is free to choose | Annex B (`PLT-n` rules and the platform-defined item list) |
| **VM / target profile** | Execution engine, bytecode and resource limits | Not specified; informative notes in Annex B |
| **Transport** | Host communication framing and status encoding | Not specified; requirements in Annex B |

**Separation rule.** A chapter rule never fixes a value or mechanism that belongs to another layer. Where language behavior depends on such a choice, the rule refers to a `PLT-n` requirement or to an item named as **platform-defined**. An implementation may not use an unspecified platform choice to change language semantics (DN §12, D-206).

## 1.3 Normative wording

- **MUST** and **MUST NOT** state requirements on conforming implementations and programs. **MAY** states a permission.
- A **compilation error** means a conforming implementation rejects the application. The specification identifies the *class* of error (§1.6). Diagnostic wording is not normative.
- A **trap** means execution of the current command terminates with an execution fault. A trap is never an `Err` outcome, and application code cannot catch it (DN §6.4).
- A **recoverable error** means an `Err` outcome that application code receives and handles through the outcome mechanisms (DN §6.1, §6.3).
- A behavior described as **platform-defined** is chosen by the platform specification within the constraints of Annex B.
- Examples, notes and sections labelled *informative* are not normative.

## 1.4 Status tags

Every normative rule carries exactly one status tag.

| Tag | Meaning |
|---|---|
| **[Agreed]** | The rule states a decision recorded as agreed in the design or platform notes, including an "agreed direction" (DN header, line 10), or a decision recorded in Annex C's resolution log (`D-4nn`). The rule cites the decision's `D-` ID. |
| **[Proposal]** | The rule states a proposal from the notes, or a gap-filling proposal written during specification work. Its text says so and cites the open issue that tracks it. |
| **[Open]** | No decision exists. The rule is a placeholder that states the open question and cites its open issue. Implementations MUST NOT treat an [Open] rule as fixed. |

**No silent invention.** When a rule needs semantics the notes do not provide, the gap is recorded as an open issue in Annex C, with options and a recommendation. Until it is resolved, the rule is written as [Proposal] or [Open]. Resolutions are recorded in Annex C's resolution log and then reflected in the rule's tag and text.

## 1.5 Rule identifiers

Normative rules have stable identifiers with a chapter prefix:

| Prefix | Chapter |
|---|---|
| `LEX` | 2 Lexical structure |
| `NAM` | 3 Program structure and names |
| `TYP` | 4 Types |
| `CEX` | 5 Constant expressions |
| `EXP` | 6 Expressions |
| `STM` | 7 Statements and control flow |
| `FUN` | 8 Functions, references and slices |
| `OUT` | 9 Outcomes and errors |
| `STA` | 10 State and initialization |
| `TXN` | 11 Transactions |
| `HEP` | 12 Host entry point |
| `RTF` | 13 Runtime failures |
| `PLT` | Annex B Platform contract |
| `SYN` | Annex A Grammar. Used only for the compile-error class `CE-SYN-1`, "no derivation of the grammar exists", for input that violates the syntax without violating a chapter rule |

A rule is written as a heading line followed by its text, then a sources line:

> **EXP-14 [Agreed]** Mixing different binary operators at one grouping level is a compilation error (CE-EXP-3).
> *Sources: D-102; DN §3.5.*

Identifiers are never reused or renumbered. A withdrawn rule keeps its identifier and is marked *withdrawn*, with a reference to its replacement.

## 1.6 Diagnostic and fault identifiers

- **Compile-error classes** are written `CE-<PREFIX>-<n>`, for example `CE-EXP-3`. Each class is defined once, in the chapter that owns its prefix, and indexed in `00-index.md`. Conformance tests refer to the class, not to message text.
- **Trap kinds** are written `TRAP-<KIND>`, for example `TRAP-OVERFLOW`. A trap kind names a language-level reason for a trap. Chapter 13 defines the kinds and `00-index.md` indexes them. How a trap is reported to the host, including any numeric code, is platform-defined (Annex B).
- **Platform errors** are written with the reserved category name the notes use, for example `CardError.<Name>`. Their names are placeholders until the platform error catalog exists. Their codes are platform-defined (OI-15).

## 1.7 Notation

### 1.7.1 Grammar

Grammar fragments in chapters, and the complete grammar in Annex A, use W3C-style EBNF:

| Form | Meaning |
|---|---|
| `Name ::= …` | Production |
| `'text'` | Terminal token, spelled exactly as written |
| `A B` | Sequence |
| `A \| B` | Alternative |
| `A?` | Optional |
| `A*` | Zero or more |
| `A+` | One or more |
| `( … )` | Grouping |
| `[a-z]` | Character class (lexical grammar only) |
| `[^…]` | Any character not in the class (lexical grammar only) |
| `#xN` | The character with hexadecimal code point N (lexical grammar only) |
| `A - B` | Any string matching A that does not match B |
| `/* … */` | Comment |

Lexical productions (characters to tokens) and syntactic productions (tokens to program structure) are kept in separate sections of Annex A. Whitespace and comments separate tokens and never appear in syntactic productions.

### 1.7.2 Typing judgments

Static rules use **bidirectional** typing judgments:

| Judgment | Reading |
|---|---|
| `Γ ⊢ e ⇒ T` | Expression `e` synthesizes type `T`: its type follows from `e` alone. |
| `Γ ⊢ e ⇐ T` | Expression `e` checks against expected type `T`: the context supplies `T`. |
| `Γ ⊢ e const` | `e` is a constant expression (chapter 5). |
| `Γ ⊢ s ok` | Statement `s` is well-formed. |
| `Γ ⊢ D ok` | Declaration `D` is well-formed. |

This notation records the notes' contextual typing policy (DN §3.3). An integer literal has no type of its own, so it only *checks* against an expected type and never *synthesizes* one. The notation adds no semantics. The typing rules in chapters 4–9 are the normative content.

The environment `Γ` records:

- every visible name, with its kind (value, function, type or error set), type, mutability and parameter mode;
- the enclosing function's successful payload type, or that it has no payload;
- whether the current position is inside a loop and inside a transaction, and which function opened that transaction.

Rules are written as inference rules with a name. When a premise fails, a stated compile-error class results:

```
T-ADD   Γ ⊢ e1 ⇒ T    Γ ⊢ e2 ⇐ T    T ∈ IntTypes
        ──────────────────────────────────────────
        Γ ⊢ e1 + e2 ⇒ T
```

(Illustrative only. The real addition rule is in chapter 6.)

**Meta-level outcome types.** The specification writes `Outcome(T)` for the result of a call whose successful payload type is `T`, and `Outcome()` for one with no payload. These are **specification-only** notations. CardLang has no user-visible result type, and outcomes cannot be stored (D-016, DN §6.3).

### 1.7.3 Evaluation rules

Dynamic behavior is written as numbered steps, executed in order. Each step that can fail states its failure result:

- `trap(KIND)`: the command terminates with trap kind `TRAP-KIND`;
- `Err(e)`: the construct's outcome is the recoverable error `e`;
- *propagate*: the failure of a sub-evaluation passes through unchanged.

A completed evaluation produces a value `v`, a successful outcome `Ok(v)` or `Ok()`, an error outcome `Err(e)`, or a control transfer (`return`, `break`, `continue` or `abort`). Unless a rule says otherwise, sub-expressions are evaluated left to right, exactly once (D-104).

### 1.7.4 Other conventions

- `T`, `U` range over types. `IntTypes = {u8, u16, u32, i8, i16, i32}`. `UIntTypes = {u8, u16, u32}`.
- `e`, `s` and `D` range over expressions, statements and declarations.
- Code in `monospace` is CardLang source or a grammar symbol.

## 1.8 Examples and conformance tests

- Each chapter section ends with **valid** and **invalid** examples. Each invalid example states the expected compile-error class or trap kind.
- Examples are independent snippets unless they say otherwise. Repeated names in different examples are not declarations in one program.
- Examples taken from the design notes keep their meaning. When a notes fragment needs surrounding code to become a complete application, the added lines are marked `// scaffold`.
- Every example is also a conformance test file in `conformance/`, and the example names that file. The file format is defined in `conformance/README.md`.

## 1.9 Sources and traceability

- **DN** is `plans_and_notes/card-language-design-notes.md` (revision of 2026-11-15). **PN** is `plans_and_notes/cardlang-platform-notes.md` (2026-11-14). They are cited by section, as `DN §3.5` or `PN §5`.
- Decisions are cited by their ID in `plans_and_notes/decision-register.md` (for example D-102).
- Every normative rule has a *Sources* line citing at least one `D-` ID or DN/PN section, plus the open issue for a [Proposal] or [Open] rule.
- Annex D maps every specification section to its sources, and every `D-` ID to the rules that implement it.

## 1.10 Glossary

Terms are defined as the notes use them. Where a term needs a precise rule, the cited chapter defines it.

| Term | Definition |
|---|---|
| **Application** | A CardLang program: state, types, functions and exactly one host entry point, compiled as one unit and isolated from every other application (D-020; DN §1, §4). |
| **Compilation unit** | All source files on an application's build-supplied file list, sharing one application-wide scope (D-021; DN §4.1). |
| **Source file** | A UTF-8 `.card` file containing complete top-level declarations (D-022, D-023; DN §3.0). |
| **Top-level declaration** | A declaration at application scope: a `persistent`, `session` or `const` value, function, command, structure, enum or error set (DN §4.2). |
| **Host entry point (command)** | The single `command` declaration through which every host request enters the application (D-041; DN §4). |
| **Ordinary function** | A `function` declaration. It always produces an outcome and cannot be called by the host (DN §3.7). |
| **Compiler intrinsic** | A reserved, compiler-provided operation such as `fill`, `convert`, `checked_add` or `wrapping_add`. It is not an ordinary function, and some intrinsics produce values directly instead of outcomes (DN §3.2, §6.5, §8.3). |
| **Platform API** | A reserved, platform-supplied operation. Its catalog is platform-defined (DN §4.1, §11). |
| **Outcome** | The transient success-or-error result of a call: `Ok` with or without a payload, or `Err` with an error. It is never a storable value (D-016; DN §6.3). |
| **Recoverable error** | An `Err` outcome carrying an error value in the application or platform category (DN §6.3). |
| **Error category** | Whether an error is an application error (from the application's error set) or a platform error. The two categories are kept apart in reporting (D-019; DN §6.3). |
| **Trap** | An execution fault that terminates the current command. It is not an outcome and cannot be caught (D-010; DN §6.4). |
| **Security reset** | A runtime-issued whole-chip reset that clears volatile state, including session state. It is required after a fatal platform failure (D-054, D-056; DN §6.4). |
| **Persistent state** | Application-scope state that survives resets (DN §5.1). |
| **Session state** | Application-scope volatile state, set to type defaults at chip power-on and cleared by a security reset (D-050, D-054; DN §5.1). |
| **Local state** | Variables belonging to one function or command invocation (DN §5). |
| **Default value** | The recursive zero, false or first-variant value given to storage without an explicit initializer (D-123, D-128; DN §3.9). |
| **Transaction** | A `transaction { … }` block whose persistent writes commit or roll back together (DN §7.2). |
| **Reference** | A call-scoped `ref` (read-only) or `inout` (mutable) parameter binding to existing storage (D-112–D-118; DN §3.7–§3.8). |
| **Access path** | The route by which code reaches storage, such as a global name, a reference parameter, or a field or element derived from one. Permissions are attached to access paths, not to storage (DN §3.8). |
| **View** | A borrowed array region with a runtime length, passed to an unspecified-size `ref T[]` or `inout T[]` parameter (D-120; DN §8.4). |
| **Slice** | The expression `array[start..end]`, selecting a borrowed half-open view (D-119; DN §8.4). |
| **Constant expression** | An expression in the deterministic, side-effect-free subset that is evaluated at compile time (D-094; DN §3.10). |
| **Platform-defined** | Chosen by the platform specification, within Annex B's constraints (§1.3). |
| **Target profile** | A concrete set of platform and VM capacities and limits. Exceeding one may cause rejection at build or load time, or a runtime trap, but never a change in semantics (D-206; PN §4). |
