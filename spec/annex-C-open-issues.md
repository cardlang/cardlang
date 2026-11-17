# Annex C — Open issues

This annex records every contradiction, gap and proposal-to-validate found while writing the specification. The rules that depend on an issue are tagged [Proposal] or [Open] and cite it (§1.4). A **recommendation** is the specification authors' suggestion. It is not a decision. An issue is resolved only by a decision recorded in the resolution log at the end of this annex.

**Entry format**

- **Kind:** contradiction, gap, or proposal-to-validate. The kind *qualifier* marks the open part of an otherwise agreed decision, and *platform-deferred* marks an item that probably belongs to the platform layer.
- **Sources:** DN and PN sections, and decision IDs.
- **Affected rules:** filled in by sub-plans as they write rules.
- **Question**, then **Options**, then **Recommendation**.
- **Status:** open or resolved.

## Summary

| ID | Title | Kind | Owning SP | Status |
|---|---|---|---|---|
| OI-1 | Source file extension: fixed or not | Contradiction | SP1 | Resolved |
| OI-2 | Platform notes still describe typed host commands | Contradiction | SP13 | Resolved |
| OI-3 | Nested-transaction detection depends on the compiler | Contradiction | SP10 | Resolved |
| OI-4 | Complete keyword and reserved-name list | Gap | SP1, SP2 | Resolved |
| OI-5 | How the host entry point is identified | Gap | SP11 | Resolved |
| OI-6 | Syntax for calling platform APIs | Gap | SP2, SP5 | Resolved |
| OI-7 | Lifecycle-handler declaration and binding | Gap | SP9 | Resolved |
| OI-8 | Positions where `attempt` may appear | Gap | SP5, SP8 | Resolved |
| OI-9 | Evaluation order for compound assignment destinations | Gap | SP6 | Resolved |
| OI-10 | Remaining slice details | Gap | SP7 | Resolved |
| OI-11 | Constant-evaluation boundary and constant indices into mutable storage | Proposal-to-validate | SP4 | Resolved |
| OI-12 | `byte` alias for `u8` | Proposal-to-validate | SP3 | Resolved |
| OI-13 | Number of error sets, and forwarding intrinsic outcomes | Gap | SP8 | Resolved |
| OI-14 | Lexical limits of integer literals | Gap | SP1 | Resolved |
| OI-15 | Placeholder names for platform errors and traps | Gap (platform-deferred) | SP12, SP13 | Resolved |
| OI-16 | Remaining semantics of explicit persistent state | Qualifier | SP9 | Resolved |
| OI-17 | Object API for larger persistent data | Qualifier (platform-deferred) | SP13 | Resolved |
| OI-18 | "Detailed typing open" for function results | Qualifier | SP8 | Resolved |
| OI-19 | Size limits for atomic aggregate assignment | Qualifier | SP9 | Resolved |
| OI-20 | Resource storage strategy | Qualifier (platform-deferred) | SP13 | Resolved |
| OI-21 | Call-frame placement of by-value aggregates | Qualifier (proposal) | SP13 | Resolved |
| OI-22 | Language rules for lifecycle handler functions | Gap | SP9 | Resolved |
| OI-23 | Source text details: byte-order mark and line breaks | Gap | SP1 | Resolved |
| OI-24 | Token formation and identifier length | Gap | SP1 | Resolved |
| OI-25 | Primitive type names | Gap | SP2 | Resolved |
| OI-26 | Build file-list constraints | Gap | SP2 | Resolved |
| OI-27 | Boolean and enum storage representation | Contradiction | SP3 | Resolved |
| OI-28 | Error-member code expressions | Gap | SP4, SP8 | Resolved |
| OI-29 | Constant slice endpoints | Gap | SP4 | Resolved |
| OI-30 | Structure constructor in conditions | Gap | SP5 | Resolved |
| OI-31 | Overflow versus underflow | Proposal-to-validate | SP5 | Resolved |
| OI-32 | Integer and byte conversion | Gap | SP5 | Resolved |
| OI-33 | Expression statements | Gap | SP6 | Resolved |
| OI-34 | Standalone blocks | Gap | SP6 | Resolved |
| OI-35 | `ref` to read-only bindings | Gap | SP7 | Resolved |
| OI-36 | Empty error set | Gap | SP8 | Resolved |
| OI-37 | Application use of `CardError` members | Gap | SP8 | Resolved |
| OI-38 | Placeholder lifecycle handler names | Gap | SP9 | Resolved |
| OI-39 | Exceeding transaction capacity at runtime | Gap | SP10 | Resolved |
| OI-40 | Platform services inside a transaction | Gap | SP10 | Resolved |

---

## OI-1 — Source file extension: fixed or not

- **Kind:** contradiction
- **Sources:** DN §1 says "The source extension and compiler executable name are not yet fixed". DN §2 row D-023 and DN §3.0 record `.card` as agreed.
- **Affected rules:** LEX-1
- **Question:** Is `.card` the normative source file extension?
- **Options:**
  - (a) `.card` is agreed, and the DN §1 sentence is stale for the extension (the compiler executable name stays unfixed).
  - (b) The extension is not fixed, and the specification states no extension.
- **Recommendation:** (a). The decision table and §3.0 are later and more specific. The executable name is a tooling matter outside the language in any case.
- **Status:** resolved 2026-11-15 (D-401)
- **Decision:** Option (a). `.card` is the normative source file extension. The DN §1 sentence is stale on this point. The compiler executable name stays unfixed (tooling).

## OI-2 — Platform notes still describe typed host commands

- **Kind:** contradiction
- **Sources:** The PN §1 table says "`command` identifies a host-callable entry point | Dispatch, command identifiers, transport and request/response encoding". DN §4 (2026-11-15) and D-041/D-042 adopted a single byte-oriented entry point with application-side dispatch. D-043 is affected.
- **Affected rules:** pending (SP11, SP13)
- **Question:** Does the platform dispatch between commands by identifier?
- **Options:**
  - (a) No. The PN §1 row is superseded: the platform delivers every request to the one entry point, and "command identifiers" exist only inside the application's own protocol.
  - (b) The platform keeps a dispatch layer, for example application selection, in front of the single entry point.
- **Recommendation:** (a) for dispatch *within* an application. Application selection between isolated applications remains a platform matter (Annex B). The PN §1 table should be updated when you choose.
- **Status:** resolved 2026-11-15 (D-402)
- **Decision:** Option (a). The PN §1 "dispatch, command identifiers" row is superseded: there is no platform dispatch within an application, and every request enters the single entry point. Selecting between isolated applications remains a platform matter. The notes themselves are not edited.

## OI-3 — Nested-transaction detection depends on the compiler

- **Kind:** contradiction
- **Sources:** DN §7.3 says "Reject nesting statically when the compiler can establish it. Otherwise the runtime checks … a violation traps". DN §3.10 states the goal that program acceptance must not depend on optimizer sophistication. D-131 is affected.
- **Affected rules:** TXN-10
- **Question:** When exactly is a nested transaction a compilation error rather than a trap?
- **Options:**
  - (a) **Always static, defined structurally.** It is a compilation error if a `transaction` block can reach a `transaction` statement through the static call graph: lexically, or in any function called, directly or transitively, from inside the block. Call targets are static and the call graph is acyclic (D-031), so this is decidable and independent of the compiler. It is conservative: it also rejects inner transactions on paths that are never taken. The runtime check stays as a VM safety net that a verified program never triggers.
  - (b) **Always dynamic.** Never reject; the runtime traps when an inner transaction starts.
  - (c) **As written.** Static rejection where an implementation can prove it, plus a runtime trap. Acceptance then varies between compilers.
- **Recommendation:** (a).
- **Status:** resolved 2026-11-15 (D-403)
- **Decision:** Option (a). Nesting is always detected statically and structurally: it is a compilation error if a `transaction` block can reach a `transaction` statement lexically or through any function it calls, directly or transitively, on the static acyclic call graph. This also rejects paths that are never taken. The runtime check remains only as a VM safety net that a verified program never triggers.

## OI-4 — Complete keyword and reserved-name list

- **Kind:** gap
- **Sources:** DN §3.0 says keywords cannot be identifiers but gives no list. DN §4.2 says built-ins and platform names are reserved. DN §3.6 says `abort` is reserved. D-044 is affected.
- **Affected rules:** LEX-13, LEX-15, NAM-14
- **Question:** Which spellings are keywords, which are reserved built-in names, and which platform names are reserved?
- **Options:** Keywords, as they appear in the notes' syntax: `persistent session const var function command struct enum errors transaction abort attempt require else if while for in match return break continue true false not and or ref inout`. Then decide:
  - (a) whether `Ok` and `Err` are keywords or reserved names;
  - (b) whether the intrinsic names (`fill`, `convert`, `checked_convert`, `checked_add`/`sub`/`mul`/`div`/`rem`/`neg`, `wrapping_add`/`sub`/`mul`) are keywords or reserved identifiers;
  - (c) which platform names are reserved: `card`, `CardError`, and the set the platform API catalog supplies;
  - (d) whether to reserve likely future words now.
- **Recommendation:**
  - Take the keyword list above as-is.
  - Make `Ok` and `Err` keywords.
  - Make the intrinsics reserved identifiers that cannot be declared or shadowed.
  - Reserve `card` and `CardError`, with the rest of the platform names platform-defined.
  - Reserve no speculative words.
  - `length` stays usable as a field name (DN §4.2).
- **Status:** resolved 2026-11-15 (D-404)
- **Decision:** Recommendation adopted.
  - Keywords: `persistent session const var function command struct enum errors transaction abort attempt require else if while for in match return break continue true false not and or ref inout Ok Err`.
  - The intrinsic names (`fill`, `convert`, `checked_convert`, `checked_add`/`sub`/`mul`/`div`/`rem`/`neg`, `wrapping_add`/`sub`/`mul`) are reserved identifiers that cannot be declared or shadowed.
  - `card` and `CardError` are reserved; other platform names are platform-defined.
  - No speculative words are reserved.
  - `length` remains usable as a field name.

## OI-5 — How the host entry point is identified

- **Kind:** gap
- **Sources:** DN §4 says "whether that spelling [`process`] is reserved or the sole command declaration identifies the entry remains a specification detail". D-041 is affected.
- **Affected rules:** pending (SP11)
- **Options:**
  - (a) The single `command` declaration is the entry point; its name is chosen by the application.
  - (b) The entry point must be named `process`.
- **Recommendation:** (a). The `command` keyword already marks it, and DN §4 calls the parameter names illustrative.
- **Status:** resolved 2026-11-15 (D-405)
- **Decision:** Option (a). The single `command` declaration is the host entry point, and its name is chosen by the application.

## OI-6 — Syntax for calling platform APIs

- **Kind:** gap
- **Sources:** DN §4.1 says a spelling such as `card.crypto...` "may be used without introducing a general application namespace system; the precise spelling is not fixed". DN §4.2 says dot access resolves from the receiver's type. DN §11.2 gives illustrative calls `card.resources.create(…)`.
- **Affected rules:** NAM-17, NAM-18; call syntax pending (SP5)
- **Question:** How does the grammar express a platform API call without a namespace system?
- **Options:**
  - (a) A distinct syntactic form for platform names: a reserved root `card` followed by `.` segments. It resolves only against the platform API catalog and is never a field access.
  - (b) Flat reserved identifiers, such as `card_hash_update`.
  - (c) Leave the call spelling to the platform specification, with a grammar hook only.
- **Recommendation:** (a). It matches every example in the notes and keeps ordinary dot access type-directed.
- **Status:** resolved 2026-11-15 (D-406)
- **Decision:** Option (a). Platform API names use a distinct syntactic form: the reserved root `card` followed by `.` segments. It resolves only against the platform API catalog and is never a field access.

## OI-7 — Lifecycle-handler declaration and binding

- **Kind:** gap
- **Sources:**
  - DN §3.9: nondefault setup belongs in lifecycle handlers, but "No lifecycle callback syntax is introduced here".
  - PN §3: handler names and signatures, registration and order are still to be specified.
  - D-124 is affected.
- **Affected rules:** STA-5 to STA-10
- **Question:** How does an application designate code to run on platform lifecycle events such as installation? Without this, nondefault persistent setup cannot be expressed.
- **Options:**
  - (a) Language syntax for handlers, for example a `handler` declaration naming an event.
  - (b) Reserved function names and signatures supplied by the platform.
  - (c) No language construct: the build configuration binds ordinary no-payload functions to platform events.
- **Recommendation:** (c) for Draft 0.1. It needs no new syntax, which matches DN §3.9. The language then only has to state that such functions are ordinary functions, with no special semantics. Whether application code may also call them is to be decided with this issue.
- **Status:** resolved 2026-11-15 (D-407)
- **Decision:** Option (b), chosen over the recommendation. Lifecycle handlers are functions with platform-reserved names and signatures. The platform specification supplies the names, signatures and events. The remaining language-side questions are tracked as OI-22.

## OI-8 — Positions where `attempt` may appear

- **Kind:** gap
- **Sources:**
  - DN §6.3 says `attempt` is "an expression when a success value is needed".
  - The notes use it in local initializers, assignment right-hand sides, `return Ok(attempt …)`, an index expression (`records[attempt choose_index()]`, DN §8.1) and a constructor field (DN §9.3).
  - DN §3.7 forbids calls in arguments.
  - D-014 and D-017 are affected.
- **Affected rules:** EXP-51; chapter 9 pending (SP8)
- **Options:**
  - (a) `attempt call` is allowed in any runtime expression position, except:
    - inside a call argument (the nested-call ban);
    - in constant expressions;
    - where its failure return would cross a transaction boundary.
  - (b) It is allowed only in a whitelist of positions: initializers, assignment right-hand sides, `return Ok(…)`, index expressions and constructor fields.
- **Recommendation:** (a). Note that in (a), an `attempt` in the right operand of `and`/`or` runs only when that operand is evaluated, under ordinary short-circuiting.
- **Status:** resolved 2026-11-15 (D-408)
- **Decision:** Option (a). `attempt call` may appear in any runtime expression position, except inside a call argument, in a constant expression, or where its failure return would cross a transaction boundary. In the right operand of `and`/`or` it runs only if that operand is evaluated.

## OI-9 — Evaluation order for compound assignment destinations

- **Kind:** gap
- **Sources:** DN §8.2 defines the order for one indexed destination: index, then bounds check, then right-hand side, then store. DN §3.5 gives general left-to-right evaluation. D-080 is affected.
- **Affected rules:** STM-9
- **Question:** What is the order for destinations like `a[i].b[j] = rhs` or `s.f[k] = rhs`?
- **Options:**
  - (a) Evaluate the whole destination path left to right first, with each index evaluated once and bounds-checked as it is reached. Then evaluate the right-hand side, then store.
  - (b) Evaluate the right-hand side first.
- **Recommendation:** (a). It directly generalizes the agreed single-index rule.
- **Status:** resolved 2026-11-15 (D-409)
- **Decision:** Option (a). The whole destination path is evaluated left to right first, with each index evaluated once and bounds-checked as it is reached. Then the right-hand side is evaluated, then the value is stored.

## OI-10 — Remaining slice details

- **Kind:** gap
- **Sources:** DN §8.4 "Remaining slice specification details" lists five items. D-119 and D-120 are affected.
- **Affected rules:** EXP-42, FUN-8, FUN-18, FUN-19, FUN-20, FUN-21
- **Questions:**
  1. Endpoint typing: are the allowed endpoint types the same as index types (`u8`/`u16`/`u32`)? Must both endpoints have the same type? Do literal-only endpoints get `u32` context?
  2. The order in which receiver, start and end are evaluated, and which failed check is reported first.
  3. Omitted endpoints (`a[..n]`), and slice expressions outside argument and receiver positions.
  4. Whether a slice of known length can satisfy a fixed-size `T[N]` parameter.
  5. Whole-region copy or fill assignment through a slice.
- **Recommendation:** decide in SP7. Proposed defaults:
  1. Index types, with independent typing of the two endpoints and `u32` context for literals.
  2. Receiver, then start, then end; then the checks `start ≤ end` and `end ≤ length`.
  3. No omitted endpoints, and slices only in reference-argument and receiver positions.
  4. No.
  5. Not added.
- **Status:** resolved 2026-11-15 (D-410)
- **Decision:** All proposed defaults adopted:
  1. Endpoints use the index types `u8`/`u16`/`u32`, typed independently; literal-only endpoints get `u32` context.
  2. Evaluation order: receiver, then start, then end; then the checks `start ≤ end` and `end ≤ length`.
  3. No omitted endpoints; slices appear only as reference arguments and receivers.
  4. A slice never satisfies a fixed-size `T[N]` parameter.
  5. No whole-slice copy or fill assignment.

## OI-11 — Constant-evaluation boundary and constant indices into mutable storage

- **Kind:** proposal-to-validate, plus gap
- **Sources:** DN §3.10 "Structural evaluation boundary (proposal for specification)" and its remaining classification question. D-029 and D-097 are affected.
- **Affected rules:** CEX-7, CEX-10
- **Questions:**
  1. Adopt the six-step structural algorithm and the illustrative acceptance table in DN §3.10 as normative?
  2. If a constant-only index is out of range for an array whose length is known from its type, but the array is in mutable storage (for example `buffer[200]` on a `u8[128]` session array), is that a compilation error or a runtime trap?
- **Options for question 2:**
  - (a) A compilation error. The index is constant-only and the length is type-known, so the check is structural.
  - (b) A runtime trap.
- **Recommendation:** adopt the algorithm. For question 2, choose (a), which is deterministic and in line with mandatory evaluation of constant-only parts.
- **Status:** resolved 2026-11-15 (D-411)
- **Decision:** Adopted. The six-step structural evaluation algorithm in DN §3.10, with its acceptance table, is normative. For question 2, option (a): a constant-only index that is out of range for an array whose length is known from its type is a compilation error, even when the array is in mutable storage.

## OI-12 — `byte` alias for `u8`

- **Kind:** proposal-to-validate
- **Sources:** DN §8 says "`byte` may be an alias for `u8`" and "The optional byte alias remains a separate naming proposal". D-076 is affected.
- **Affected rules:** TYP-20
- **Options:**
  - (a) Adopt `byte` as an exact alias of `u8`.
  - (b) Do not adopt it in Draft 0.1.
- **Recommendation:** (b). One spelling per type is simpler, and the alias can be added later without breaking programs.
- **Status:** resolved 2026-11-15 (D-412)
- **Decision:** Option (b). `byte` is not adopted in Draft 0.1.

## OI-13 — Number of error sets, and forwarding intrinsic outcomes

- **Kind:** gap
- **Sources:** DN §6.3 says "One named error set per application initially" and lists the outcome consumption forms. DN §6.5 lists the outcome-producing intrinsics. D-018 and D-091 are affected.
- **Questions:**
  1. May an application declare **no** error set?
  2. Is `return checked_add(a, b);` (whole-outcome forwarding of an intrinsic's outcome) allowed when the payload types match?
- **Options:**
  1. (a) At most one error set, zero allowed; or (b) exactly one, required.
  2. (a) Allowed, because outcome-producing intrinsics follow the same consumption rules as calls (DN §6.3); or (b) forbidden.
- **Recommendation:** 1(a) and 2(a).
- **Status:** resolved 2026-11-15 (D-413)
- **Decision:** 1(a): an application declares at most one error set, and zero are allowed. 2(a): outcome-producing intrinsics follow the same consumption rules as calls, including whole-outcome forwarding when payload types match.

## OI-14 — Lexical limits of integer literals

- **Kind:** gap
- **Sources:** DN §3.0 (literal forms) and DN §3.3. D-036 and D-084 are affected. Note that a comparison of literal-only operands with no integer context (for example `1 == 1`) is **already settled** by DN §3.3: "missing or ambiguous integer context must not be resolved by guessing a default". It is a compilation error and is not part of this issue.
- **Affected rules:** LEX-17, LEX-18, LEX-19
- **Questions:**
  1. Are the prefixes `0X` and `0B` (uppercase) accepted?
  2. Are hex digits case-insensitive?
  3. Is a prefix with no digits (`0x`) a lexical error?
  4. Is a digit outside the base (`0b2`, `0xG`) a lexical error?
  5. Is a literal whose value exceeds every integer type (more than 2³²−1) a lexical error or a typing error?
- **Recommendation:**
  1. Lowercase prefixes only.
  2. Hex digits case-insensitive.
  3. Lexical error.
  4. Lexical error.
  5. A typing error at the literal's expected type. The lexer does not limit magnitude.
- **Status:** resolved 2026-11-15 (D-414)
- **Decision:** Recommendation adopted:
  - `0x` and `0b` prefixes are lowercase only.
  - Hex digits are case-insensitive.
  - A prefix with no digits, or a digit outside the base, is a lexical error.
  - The lexer does not limit magnitude; range is a typing error at the literal's expected type.

## OI-15 — Placeholder names for platform errors and traps

- **Kind:** gap (platform-deferred)
- **Sources:**
  - DN §3.2, §6.2, §6.5: checked arithmetic and conversion errors are "platform-defined".
  - DN §6.4: the trap list and catalog are platform work.
  - PN §2: resource error names are placeholders.
  - D-203 and D-209 are affected.
- **Affected rules:** pending (SP5, SP12, SP13)
- **Question:** Which names may chapters use until the platform catalogs exist?
- **Recommendation:**
  - Chapters use **language-level trap kinds** (chapter 13): `TRAP-OVERFLOW`, `TRAP-UNDERFLOW`, `TRAP-DIV-ZERO`, `TRAP-BOUNDS`, `TRAP-SHIFT`, `TRAP-NEGATION`, `TRAP-RESPONSE-COUNT`, `TRAP-NESTED-TXN`, `TRAP-COMMIT`, `TRAP-EXHAUSTED` (stack or execution budget) and `TRAP-VM` (invalid instruction or state).
  - Chapters use **placeholder platform error names**: `CardError.Overflow`, `CardError.Underflow`, `CardError.DivisionByZero`, `CardError.ConversionRange`, `CardError.AlreadyExists`, `CardError.NotFound`, `CardError.WrongResourceType` and `CardError.Capacity`. Each is marked as a placeholder, and all codes are platform-defined.
  - The final names are confirmed or replaced in SP12 and SP13.
- **Status:** resolved 2026-11-15 (D-415)
- **Decision:** Adopted. Chapters use the language-level trap kinds `TRAP-OVERFLOW`, `-UNDERFLOW`, `-DIV-ZERO`, `-BOUNDS`, `-SHIFT`, `-NEGATION`, `-RESPONSE-COUNT`, `-NESTED-TXN`, `-COMMIT`, `-EXHAUSTED` and `-VM`, and the placeholder platform errors `CardError.Overflow`, `.Underflow`, `.DivisionByZero`, `.ConversionRange`, `.AlreadyExists`, `.NotFound`, `.WrongResourceType` and `.Capacity`. All codes are platform-defined. SP12 and SP13 confirm or replace the names.

## OI-16 — Remaining semantics of explicit persistent state

- **Kind:** qualifier
- **Sources:** D-008 says "Agreed direction; detailed semantics open". The DN §5 table lists "Initialization, updates, deletion, upgrades and transactions" as still to define.
- **Affected rules:** STA-3
- **Note:** Initialization (DN §3.9), updates (DN §7.1) and transactions (DN §7.2) have since been specified in the notes. What remains is deletion, upgrades and migration.
- **Recommendation:** the language covers declaration, defaults, atomic assignment and transactions. Deletion, upgrade and migration become platform-defined items in Annex B. Close this issue after SP9 confirms.
- **Status:** resolved 2026-11-15 (D-416)
- **Decision:** Recommendation adopted. The language covers declaration, defaults, atomic assignment and transactions. Persistent-state deletion, upgrade and migration are platform-defined items (Annex B).

## OI-17 — Object API for larger persistent data

- **Kind:** qualifier (platform-deferred)
- **Sources:** D-009 says "Preferred direction accepted in discussion; API not designed". DN §5 is also relevant.
- **Affected rules:** pending (SP13)
- **Options:**
  - (a) A platform API, outside the language.
  - (b) A language feature.
- **Recommendation:** (a), and not part of Draft 0.1. Annex B lists it as future platform work.
- **Status:** resolved 2026-11-15 (D-417)
- **Decision:** Recommendation adopted. The object API for larger persistent data is a future platform API, outside Draft 0.1. Annex B lists it as future work.

## OI-18 — "Detailed typing open" for function results

- **Kind:** qualifier
- **Sources:** D-012 says "Agreed direction; detailed typing open". The typing was later developed in DN §6.3: transient outcomes, no `Result<T>`, and exact `attempt` typing (D-015–D-017).
- **Affected rules:** OUT-1 to OUT-14
- **Recommendation:** treat this as resolved by DN §6.3 once SP8 has formalized the outcome typing rules. Close it at SP8 review.
- **Status:** resolved 2026-11-15 (D-418)
- **Decision:** Recommendation adopted. "Detailed typing open" is settled by DN §6.3 (transient outcomes, no `Result<T>`, exact `attempt` typing). SP8 formalizes it.

## OI-19 — Size limits for atomic aggregate assignment

- **Kind:** qualifier
- **Sources:**
  - D-057 says "aggregate limits and storage details open".
  - DN §7.1: the maximum atomic-write size and the behavior for unsupported sizes need specification.
  - DN §7.4 asks the same questions.
- **Affected rules:** STA-13
- **Question:** What happens when a persistent aggregate assignment exceeds what the platform can update atomically?
- **Options:**
  - (a) The application is rejected at build or load time for that target profile.
  - (b) The assignment traps at runtime.
  - (c) The assignment silently becomes non-atomic. This is excluded, because limits must not change semantics (D-206).
- **Recommendation:** (a). The limit values themselves are platform-defined (Annex B).
- **Status:** resolved 2026-11-15 (D-419)
- **Decision:** Option (a). A persistent aggregate assignment larger than the target can update atomically causes the application to be rejected at build or load time for that target profile. It never becomes non-atomic. The limit values are platform-defined.

## OI-20 — Resource storage strategy

- **Kind:** qualifier (platform-deferred)
- **Sources:** D-127 says "Platform decisions; identifier API does not require a heap". DN §11.2 and PN §2 are also relevant.
- **Affected rules:** pending (SP13)
- **Recommendation:** close as a platform-defined item in Annex B. It has no language impact.
- **Status:** resolved 2026-11-15 (D-420)
- **Decision:** Recommendation adopted. Resource storage strategy is a platform-defined item in Annex B, with no language impact.

## OI-21 — Call-frame placement of by-value aggregates

- **Kind:** qualifier (proposal)
- **Sources:** D-133 says "Temporary application RAM; call-frame placement proposed". DN §3.8 and PN §4 are also relevant.
- **Affected rules:** pending (SP7, SP13)
- **Recommendation:** the language rule stays at value semantics: an independent copy that lives for the call. Frame placement becomes informative VM guidance in Annex B. Close it at SP13.
- **Status:** resolved 2026-11-15 (D-421)
- **Decision:** Recommendation adopted. The language rule is value semantics: an independent copy that lives for the call. Call-frame placement is informative VM guidance in Annex B.

## OI-22 — Language rules for lifecycle handler functions

- **Kind:** gap, opened by the OI-7 resolution
- **Sources:** OI-7 resolution (D-407); DN §3.9; PN §3
- **Affected rules:** STA-7, STA-8, STA-9, STA-10; NAM-14
- **Questions:**
  1. May application code call a lifecycle handler function directly?
  2. Do handlers follow all ordinary-function rules (always produce an outcome, may not recurse, and so on), with only the name and signature fixed by the platform?
  3. Are the handler names reserved even when the application does not define them, and is defining a handler optional?
- **Recommendation:**
  1. No. This mirrors the rule that application code cannot call the `command`.
  2. Yes.
  3. Reserved always; optional unless the platform requires a particular handler.
- **Status:** resolved 2026-11-15 (D-422)
- **Decision:** Recommendation adopted for all three questions.

## OI-23 — Source text details: byte-order mark and line breaks

- **Kind:** gap
- **Sources:** DN §3.0 ("Source files are UTF-8"; "Spaces, tabs and line breaks separate tokens"); D-023
- **Affected rules:** LEX-4, LEX-5
- **Questions:**
  1. Is a UTF-8 byte-order mark at the start of a file permitted and ignored, or an error?
  2. Which sequences are line breaks: LF, CR, CRLF?
- **Options:**
  1. Ignored or error.
  2. All three, or LF and CRLF only.
- **Recommendation:**
  1. Ignored, because common Windows editors write one.
  2. All three, with CRLF counting as one line break.
- **Status:** resolved 2026-11-15 (D-423)
- **Decision:** Recommendation adopted.

## OI-24 — Token formation and identifier length

- **Kind:** gap
- **Sources:** DN §3.0; OI-14 resolution (D-414)
- **Affected rules:** LEX-10, LEX-16, LEX-18
- **Questions:**
  1. Is the longest possible token always taken?
  2. Is a numeric literal the longest run of letters, digits and `_` starting with a digit, which must wholly match a literal form? This is how the OI-14 decision is implemented.
  3. Is there a maximum identifier length?
- **Recommendation:**
  1. Yes.
  2. Yes.
  3. No language limit. A tool may report a limit but must not silently truncate.
- **Status:** resolved 2026-11-15 (D-424)
- **Decision:** Recommendation adopted.

## OI-25 — Primitive type names

- **Kind:** gap
- **Sources:** DN §3.1 (primitive types); D-075; D-404 (the keyword list does not include the type names)
- **Affected rules:** NAM-14, NAM-21
- **Question:** The names `u8 u16 u32 i8 i16 i32 bool` are not keywords. Can an application declare something with one of these names?
- **Options:**
  - (a) No. They are predeclared type names in the application scope.
  - (b) No. Make them keywords.
  - (c) Yes, they may be redeclared.
- **Recommendation:** (a). This keeps the agreed keyword list unchanged.
- **Status:** resolved 2026-11-15 (D-425)
- **Decision:** Option (a). Declaring one is CE-NAM-5, and shadowing one is CE-NAM-3.

## OI-26 — Build file-list constraints

- **Kind:** gap
- **Sources:** DN §4.1; D-021
- **Affected rules:** NAM-3
- **Questions:**
  1. What happens if the same file is listed twice in the build file list?
  2. Is an empty file list allowed?
- **Recommendation:**
  1. A build-configuration error, outside the language.
  2. Allowed by the language. It fails because there is no `command` (chapter 12).
- **Status:** resolved 2026-11-15 (D-426)
- **Decision:** Recommendation adopted.

## OI-27 — Boolean and enum storage representation

- **Kind:** contradiction
- **Sources:**
  - DN §3.1 says "Boolean storage representation and detailed arithmetic rules still require specification".
  - DN §3.9 says "Semantic defaults do not imply a particular physical boolean or storage representation".
  - DN §3.11 says enum "Internal storage representation is a compiler/platform detail" and that declaration order is not a stable encoding.
  - D-075 and D-325 are affected.
- **Affected rules:** TYP-9
- **Question:** Must the language fix how Boolean and enum values, and aggregates, are stored?
- **Options:**
  - (a) No. Representation is not language-visible. Persistent layout and its preservation across upgrades are platform-defined.
  - (b) Yes. The language fixes concrete encodings.
- **Recommendation:** (a). The DN §3.1 sentence is treated as superseded for storage. Its arithmetic part is covered by chapter 6.
- **Status:** resolved 2026-11-15 (D-427)
- **Decision:** Option (a).

## OI-28 — Error-member code expressions

- **Kind:** gap
- **Sources:**
  - DN §6.3 shows only literal codes, such as `InsufficientFunds = 1;`.
  - The DN §3.3 table lists "Application error-code literal" as having the required `u16` type.
  - D-018 is affected.
- **Affected rules:** CEX-6, OUT-16
- **Question:** May an error-member code be any constant expression of type `u16`, or only a literal?
- **Options:**
  - (a) An integer literal only, with `u16` context.
  - (b) Any constant expression of type `u16`.
- **Recommendation:** (a). It matches the notes and keeps published codes easy to read in the source. It can be relaxed later without breaking programs.
- **Status:** resolved 2026-11-15 (D-428)
- **Decision:** Option (a).

## OI-29 — Constant slice endpoints

- **Kind:** gap
- **Sources:** D-411 (a constant out-of-range index is a compile error); DN §8.4; D-119
- **Affected rules:** CEX-10
- **Question:** Are constant-only slice endpoints on an array of type-known length checked at compile time, covering `end > length` and `start > end`?
- **Options:**
  - (a) Yes, as a compile error.
  - (b) No, as a runtime trap.
- **Recommendation:** (a), for consistency with D-411. Slices of unsized `T[]` parameters remain runtime-checked.
- **Status:** resolved 2026-11-15 (D-429)
- **Decision:** Option (a).

## OI-30 — Structure constructor in conditions

- **Kind:** gap
- **Sources:** DN §3.0 (mandatory braces), §3.6, §9.3; D-070
- **Affected rules:** EXP-6
- **Question:** `if ready { … }` and a constructor `Point { … }` both have the form `Name {`. How does the grammar tell them apart in condition positions?
- **Options:**
  - (a) A constructor directly in an `if`/`while` condition, a `for` range bound or a `match` scrutinee must be parenthesized. This is a grammar rule.
  - (b) Decide by name resolution: `Name {` is a constructor exactly when `Name` is a structure type.
- **Recommendation:** (a). Parsing stays independent of name resolution.
- **Status:** resolved 2026-11-15 (D-430)
- **Decision:** Option (a).

## OI-31 — Overflow versus underflow

- **Kind:** proposal-to-validate
- **Sources:** DN §6.2 "Proposed arithmetic failure categories"; DN §6.5; D-058, D-088, D-090, D-091; OI-15 resolution (D-415)
- **Affected rules:** EXP-23, EXP-24, EXP-25, EXP-29
- **Question:** How are out-of-range results classified for trap kinds and for `CardError` members?
- **Options:**
  - (a) Adopt the DN table:
    - above the maximum is Overflow;
    - below the minimum, including unsigned subtraction below zero, is Underflow;
    - the minimum signed value divided by −1 is Overflow;
    - negating the minimum is `TRAP-NEGATION`, and `checked_neg` returns `CardError.Overflow`.
  - (b) A single Overflow kind for everything.
- **Recommendation:** (a).
- **Status:** resolved 2026-11-15 (D-431)
- **Decision:** Option (a).

## OI-32 — Integer and byte conversion

- **Kind:** gap
- **Sources:** DN §3.4 ("Encoding API names and any future deliberately lossy byte-extraction operations remain open"); D-101, D-342
- **Affected rules:** EXP-34, EXP-36, EXP-37; LEX-15; NAM-14; CEX-5
- **Question:** What should Draft 0.1 provide for extracting bytes from integers and assembling integers from bytes?
- **Options:**
  - (a) Nothing new.
  - (b) A truncating intrinsic.
  - (c) Byte-order intrinsics.
  - (d) Both (b) and (c).
- **Recommendation:** none. The notes leave this as a language-design choice.
- **Status:** resolved 2026-11-15 (D-432)
- **Decision:** Option (d), with these details:
  - `truncate<T>(x)` converts any integer type to any integer type. The source type must be known independently. The result is the low bits of `x` reinterpreted as `T`, using two's complement for signed types. It never fails.
  - `encode_be(x)` and `encode_le(x)` accept `T` in `u16`, `u32`, `i16` and `i32`. Each returns a direct `u8[N]` value.
  - `decode_be<T>(ref bytes)` and `decode_le<T>(ref bytes)` return a direct `T`. They trap with `TRAP-BOUNDS` when the length is not `N`.
  - All are direct-value intrinsics, excluded from constant expressions initially.
  - Their names are reserved.

## OI-33 — Expression statements

- **Kind:** gap
- **Sources:** DN §6.3 (the `attempt` statement form only for no-payload success; discarded outcomes are errors)
- **Affected rules:** STM-2
- **Question:** Besides `attempt call;`, may an expression be used as a statement, as in `a + b;`?
- **Options:**
  - (a) No. The `attempt` form is the only expression statement.
  - (b) Allow expression statements that produce no outcome.
- **Recommendation:** (a). Other forms have no useful effect.
- **Status:** resolved 2026-11-15 (D-433)
- **Decision:** Option (a).

## OI-34 — Standalone blocks

- **Kind:** gap
- **Sources:** DN §3.6 (blocks belong to control-flow bodies; standalone blocks are neither used nor forbidden)
- **Affected rules:** STM-3
- **Question:** May a bare `{ … }` be used as a statement that opens a nested scope?
- **Options:**
  - (a) No.
  - (b) Yes.
- **Recommendation:** (a). It can be added later without breaking programs.
- **Status:** resolved 2026-11-15 (D-434)
- **Decision:** Option (a).

## OI-35 — `ref` to read-only bindings

- **Kind:** gap
- **Sources:** DN §3.8 (references may target "named variables, structure fields and array elements"); D-117
- **Affected rules:** FUN-9
- **Question:** May a `for` index or a pattern binding be passed as a `ref` argument?
- **Options:**
  - (a) Yes, as `ref` only, never `inout`.
  - (b) No; copy the value into a `var` first.
- **Recommendation:** (a). Such a binding is existing read-only storage, so passing it as `ref` grants nothing new.
- **Status:** resolved 2026-11-15 (D-435)
- **Decision:** Option (a).

## OI-36 — Empty error set

- **Kind:** gap
- **Sources:** DN §6.3 (only non-empty sets are shown); TYP-10, TYP-13 (empty enums and structures are errors); D-413
- **Affected rules:** OUT-15
- **Question:** May an error set declare no members?
- **Options:**
  - (a) No; at least one member.
  - (b) Yes.
- **Recommendation:** (a). This is consistent with enums and structures. An application without errors declares no set.
- **Status:** resolved 2026-11-15 (D-436)
- **Decision:** Option (a).

## OI-37 — Application use of `CardError` members

- **Kind:** gap
- **Sources:** DN §6.3:
  - "Named error members are permitted in `return Err(...)`, `abort Err(...)`, `require ... else ...` and specific `Err(ErrorSet.Member)` patterns."
  - "Error-member patterns may name either application or platform errors."
  - "Application-defined names cannot impersonate that namespace."
- **Affected rules:** OUT-4, OUT-19; STM-19
- **Question:** May application code originate a platform error, for example `return Err(CardError.NotFound);`?
- **Options:**
  - (a) No. `CardError` members may be named only in patterns, and received platform errors are propagated through error bindings.
  - (b) Yes, everywhere.
- **Recommendation:** (a). A platform-category error then always originates in the platform.
- **Status:** resolved 2026-11-15 (D-437)
- **Decision:** Option (a).

## OI-38 — Placeholder lifecycle handler names

- **Kind:** gap, opened by the OI-7 decision
- **Sources:** D-407 (handlers have platform-reserved names and signatures); D-415 (the precedent of placeholder names); PN §3
- **Affected rules:** STA-6; NAM-14
- **Question:** Which handler names and signatures may chapters and tests use before the platform catalog exists?
- **Recommendation:**
  - `on_install()`: no parameters and no payload. It runs once, after persistent state is created.
  - `on_power_on()`: no parameters and no payload. It runs after session defaults are applied at power-on.
  - Both are marked as placeholders, and Annex B confirms or replaces them.
- **Status:** resolved 2026-11-15 (D-438)
- **Decision:** Recommendation adopted.

## OI-39 — Exceeding transaction capacity at runtime

- **Kind:** gap
- **Sources:** DN §7.4 ("What limits apply to transaction size?"); D-206
- **Affected rules:** TXN-16
- **Question:** Loops make the number of pending writes unknowable at compile time. What happens when a running transaction exceeds the target's capacity?
- **Options:**
  - (a) A dedicated trap kind, `TRAP-TXN-CAPACITY`.
  - (b) Treat it as a commit failure, `TRAP-COMMIT`.
  - (c) Reject at build or load time when a bound is computable, and trap otherwise.
- **Recommendation:** (a). Option (c) would make acceptance depend on how sophisticated the analysis is.
- **Status:** resolved 2026-11-17 (D-439)
- **Decision:** Option (a). Pending writes roll back, as for any trap. `TRAP-TXN-CAPACITY` joins the placeholder trap kinds of D-415.

## OI-40 — Platform services inside a transaction

- **Kind:** gap
- **Sources:** DN §7.2, §7.4; PN §2, §5 (each API must define its transaction behaviour or prohibit use during a transaction); D-205
- **Affected rules:** TXN-17
- **Question:** How is a call to a prohibited API inside a transaction detected?
- **Options:**
  - (a) Statically, with the same structural call-graph rule as nesting (D-403).
  - (b) At runtime, as a recoverable error.
  - (c) At runtime, as a trap.
- **Recommendation:** (a).
- **Status:** resolved 2026-11-17 (D-440)
- **Decision:** Option (a). Each API's catalog entry says whether it is permitted inside a transaction (Annex B).

---

## Resolution log

| Date | ID | Decision | Decided by | Spec changes |
|---|---|---|---|---|
| 2026-11-15 | OI-1 | Source file extension is `.card` (D-401) | User | Applied in chapter 2: LEX-1 (SP1) |
| 2026-11-15 | OI-2 | No platform dispatch within an application; PN §1 row superseded (D-402) | User | Pending: applied when SP13 drafts its chapter |
| 2026-11-15 | OI-3 | Nested transactions rejected statically by a structural call-graph rule (D-403) | User | Applied in chapter 11: TXN-10 (SP10) |
| 2026-11-15 | OI-4 | Keyword list; Ok/Err keywords; intrinsics and card/CardError reserved (D-404) | User | Applied: LEX-13, LEX-15 (SP1); NAM-14 (SP2) |
| 2026-11-15 | OI-5 | Entry point is the single `command` declaration, any name (D-405) | User | Pending: applied when SP11 drafts its chapter |
| 2026-11-15 | OI-6 | Platform API calls use the reserved `card.` path form (D-406) | User | Applied: NAM-17, NAM-18 (SP2); call syntax in chapter 6 (SP5) |
| 2026-11-15 | OI-7 | Lifecycle handlers use platform-reserved function names/signatures (D-407) | User | Applied in chapter 10: STA-5 to STA-10 (SP9); catalog pending Annex B (SP13) |
| 2026-11-15 | OI-8 | `attempt` allowed in any runtime expression position, with three exclusions (D-408) | User | Applied in chapter 6: EXP-51 (SP5); meaning in chapter 9 (SP8) |
| 2026-11-15 | OI-9 | Assignment: destination path first, then RHS, then store (D-409) | User | Applied in chapter 7: STM-9 (SP6) |
| 2026-11-15 | OI-10 | Slice endpoint typing, order, positions and limits fixed (D-410) | User | Applied in chapter 8: FUN-8, FUN-18 to FUN-21 (SP7) |
| 2026-11-15 | OI-11 | Constant-evaluation algorithm normative; constant OOB index is a compile error (D-411) | User | Applied in chapter 5: CEX-7, CEX-10 (SP4) |
| 2026-11-15 | OI-12 | No `byte` alias in Draft 0.1 (D-412) | User | Applied in chapter 4: TYP-20 (SP3) |
| 2026-11-15 | OI-13 | Zero or one error set; intrinsic outcomes may be forwarded (D-413) | User | Applied in chapter 9: OUT-5, OUT-15 (SP8) |
| 2026-11-15 | OI-14 | Literal prefix, digit and magnitude rules (D-414) | User | Applied in chapter 2: LEX-17 to LEX-19 (SP1) |
| 2026-11-15 | OI-15 | Trap-kind and placeholder platform-error names (D-415) | User | Pending: applied when SP12 drafts its chapter |
| 2026-11-15 | OI-16 | Persistent deletion/upgrade/migration are platform-defined (D-416) | User | Applied in chapter 10: STA-3 (SP9); platform items pending Annex B (SP13) |
| 2026-11-15 | OI-17 | Large-data object API is future platform work (D-417) | User | Pending: applied when SP13 drafts its chapter |
| 2026-11-15 | OI-18 | Outcome typing settled by DN §6.3 (D-418) | User | Applied in chapter 9: OUT-1 to OUT-14 (SP8); closed |
| 2026-11-15 | OI-19 | Oversized atomic aggregate assignment rejected at build/load time (D-419) | User | Applied in chapter 10: STA-13 (SP9) |
| 2026-11-15 | OI-20 | Resource storage strategy is platform-defined (D-420) | User | Pending: applied when SP13 drafts its chapter |
| 2026-11-15 | OI-21 | Call-frame placement is informative VM guidance (D-421) | User | Pending: applied when SP13 drafts its chapter |
| 2026-11-15 | OI-23 | BOM ignored; LF, CR and CRLF are line breaks (D-423) | User | Applied in chapter 2 (SP1) |
| 2026-11-15 | OI-24 | Longest match; numeric-run rule; no identifier length limit (D-424) | User | Applied in chapter 2 (SP1) |
| 2026-11-15 | OI-25 | Primitive type names are predeclared (D-425) | User | Applied in chapter 3: NAM-14 (SP2) |
| 2026-11-15 | OI-26 | File-list duplicates are a build error; empty list allowed (D-426) | User | Applied in chapter 3: NAM-3 (SP2) |
| 2026-11-15 | OI-27 | Storage representation is not language-visible (D-427) | User | Applied in chapter 4: TYP-9 (SP3) |
| 2026-11-15 | OI-28 | Error-member codes are integer literals (D-428) | User | Applied: CEX-6 (SP4); chapter 9: OUT-16 (SP8) |
| 2026-11-15 | OI-29 | Constant slice endpoints checked at compile time (D-429) | User | Applied in chapter 5: CEX-10 (SP4) |
| 2026-11-15 | OI-30 | A structure constructor directly in an if/while condition, for range bound or match scrutinee must be parenthesized (D-430) | User | Applied in chapter 6 (SP5) |
| 2026-11-15 | OI-31 | Arithmetic failure classes: above maximum is Overflow (D-431) | User | Applied in chapter 6 (SP5) |
| 2026-11-15 | OI-32 | Add truncate<T>(x) and value-based byte-order intrinsics encode_be/encode_le and decode_be/decode_le<T> (D-432) | User | Applied in chapter 6 (SP5) |
| 2026-11-15 | OI-33 | Only the attempt expression statement (D-433) | User | Applied in chapter 7: STM-2 (SP6) |
| 2026-11-15 | OI-34 | No standalone blocks (D-434) | User | Applied in chapter 7: STM-3 (SP6) |
| 2026-11-15 | OI-35 | for index or pattern binding may be passed as ref (D-435) | User | Applied in chapter 8: FUN-9 (SP7) |
| 2026-11-15 | OI-36 | An error set needs at least one member (D-436) | User | Applied in chapter 9: OUT-15 (SP8) |
| 2026-11-15 | OI-37 | CardError members only in patterns (D-437) | User | Applied in chapter 9: OUT-4, OUT-19; chapter 7: STM-19 (SP8) |
| 2026-11-15 | OI-22 | Lifecycle handler rules (D-422) | User | Applied in chapter 10: STA-7 to STA-10 (SP9) |
| 2026-11-15 | OI-38 | Placeholder handlers on_install and on_power_on (D-438) | User | Applied in chapter 10: STA-6; NAM-14 (SP9) |
| 2026-11-17 | OI-39 | Dedicated trap TRAP-TXN-CAPACITY (D-439) | User | Applied in chapter 11: TXN-16 (SP10) |
| 2026-11-17 | OI-40 | Prohibited services rejected statically, CE-TXN-4 (D-440) | User | Applied in chapter 11: TXN-17 (SP10) |
