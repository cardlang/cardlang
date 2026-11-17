# Annex D — Traceability

This annex links the specification to its sources in both directions.

- **D.1 (forward):** each specification file → the design-note sections it draws on.
- **D.2 (reverse):** each decision ID → the rules that implement it, or the open issue that blocks it.

Decision IDs are defined in `plans_and_notes/decision-register.md`. Each sub-plan updates both tables when it drafts its chapter. Section-level entries become rule-level entries as rules are written.

**Coverage values used in D.2**

| Value | Meaning |
|---|---|
| `pending` | The owning sub-plan has not drafted it yet |
| `covered` | One or more rules implement it fully |
| `partial` | Rules implement it, but a linked open issue leaves part unspecified |
| `deferred` | Assigned to the platform layer (Annex B) or kept as informative material |
| `blocked` | Cannot be specified until the linked open issue is resolved |

## D.1 Specification → sources

| Spec file | Sub-plan | Design-note and platform-note sources | Rule IDs |
|---|---|---|---|
| 01-scope-and-conventions.md | SP0 | DN header, §1, §2, §3 (intro), §12, §13; PN §1 | none (conventions only) |
| 02-lexical-structure.md | SP1 | DN §3.0, §3.3 (literal forms), §3.5, §3.6, §4.1, §6.5 (negative minimum) | LEX-1 … LEX-24 |
| 03-program-structure-and-names.md | SP2 | DN §3.0, §3.6 (scope), §3.7, §3.11, §4.1, §4.2, §5.1, §6.3, §11.1 | NAM-1 … NAM-22 |
| 04-types.md | SP3 | DN §3.1, §3.4, §3.9 (defaults), §3.11, §8, §8.1, §8.2, §8.4, §9–§9.3 | TYP-1 … TYP-23 |
| 05-constant-expressions.md | SP4 | DN §3.3, §3.8, §3.10, §3.11, §5.1, §6.5 | CEX-1 … CEX-14 |
| 06-expressions.md | SP5 | DN §3.2, §3.3, §3.4, §3.5, §3.7, §3.11, §6.2, §6.5, §8.1, §8.2, §8.3, §9.3 | EXP-1 … EXP-51 |
| 07-statements-and-control-flow.md | SP6 | DN §3.5, §3.6, §3.7 (completion), §3.9, §3.10, §3.11, §5.1, §8.2 | STM-1 … STM-22 |
| 08-functions-and-references.md | SP7 | DN §3.0, §3.7, §3.8, §8.4, §9.2 | FUN-1 … FUN-23 |
| 09-outcomes-and-errors.md | SP8 | DN §3.2, §3.6, §3.7, §6.1, §6.2, §6.3, §7.2; PN §5 | OUT-1 … OUT-20 |
| 10-state-and-initialization.md | SP9 | DN §3.9, §5, §5.1, §6.4 (session), §7.1, §8.2, §8.3, §9.3; PN §3 | STA-1 … STA-14 |
| 11-transactions.md | SP10 | DN §3.6 (boundary), §4, §6.4, §7.1–§7.4; PN §5 | TXN-1 … TXN-17 |
| 12-host-entry-point.md | SP11 | DN §3.7, §4, §4.1, §6.3, §7.4, §12; PN §1, §5 | HEP-1 … HEP-16 |
| 13-runtime-failures.md | SP12 | DN §3.6, §6.4, §6.5, §7.2, §12, §13; PN §3, §4, §5 | RTF-1 … RTF-12 |
| annex-A-grammar.md | SP1–SP14 | DN §3.0 plus the syntax of every chapter | A.1 and A.2.1–A.2.10 complete; consolidation pending (SP14) |
| annex-B-platform-contract.md | SP13 | PN §1–§5; DN §4 (transport), §11, §12 | pending |
| annex-C-open-issues.md | all | see each issue | — |

## D.2 Decisions → rules

| D-ID | Topic (short) | Owning SP | Rule IDs | Linked OI | Coverage |
|---|---|---|---|---|---|
| D-001 | Language name: CardLang | SP0 | 01 §1.1 |  | covered |
| D-002 | Custom card-oriented language | SP0 | 01 §1.1 |  | covered |
| D-003 | Global declarations: `persistent`, `session` or `const` | SP2 | NAM-6, NAM-9 |  | covered |
| D-004 | `persistent` and `session` imply mutable state | SP9 | STA-1 |  | covered |
| D-005 | Global `const` declares a compile-time constant | SP4 | CEX-1, CEX-2 |  | covered |
| D-006 | Local value declarations use `var` only | SP6 | NAM-10, STM-4 |  | covered |
| D-007 | Storage qualifiers inside functions/commands are forbidden | SP2 | NAM-10 |  | covered |
| D-008 | Explicit persistent state | SP9 | STA-3, STA-11 | OI-16 | covered |
| D-009 | Simple persistent declarations plus an object API for larger data | SP13 | — | OI-17 | pending |
| D-010 | Recoverable errors through explicit results, execution faults through traps | SP8 | OUT-1 |  | covered |
| D-011 | No general-purpose exceptions initially | SP8 | OUT-1 |  | covered |
| D-012 | Every function returns a success/error result | SP8 | OUT-1, OUT-2 | OI-18 | covered |
| D-013 | Explicit outcome handling uses `match` with `Ok` / `Err` | SP8 | OUT-11 |  | covered |
| D-014 | Automatic error propagation with `attempt` | SP8 | OUT-8, OUT-10 |  | covered |
| D-015 | Discarded function outcomes | SP8 | OUT-5, OUT-7 |  | covered |
| D-016 | Stored result values / user-visible `Result<T>` | SP8 | OUT-2 |  | covered |
| D-017 | `attempt` type | SP8 | OUT-9, OUT-10 |  | covered |
| D-018 | One application error set with explicit nonzero `u16` codes | SP8 | OUT-15, OUT-16 | OI-13 | covered |
| D-019 | Application/platform errors and traps have separate reporting categories | SP8 | OUT-18 |  | covered |
| D-020 | Single application or completely isolated applications | SP2 | NAM-5 |  | covered |
| D-021 | Multiple source files form one application compilation unit | SP2 | NAM-1 |  | covered |
| D-022 | Source files contain complete top-level declarations; no application wrapper | SP2 | NAM-1, NAM-2, NAM-6, NAM-8 |  | covered |
| D-023 | Source extension `.card`; UTF-8 source, ASCII identifiers | SP1 | LEX-1, LEX-2, LEX-3, LEX-12 | OI-1 | covered |
| D-024 | Mandatory semicolons, braces and named-declaration type annotations | SP1 | LEX-22, LEX-23 (tokens); syntax side pending SP2–SP11 |  | partial |
| D-025 | No-value ordinary function signature | SP7 | FUN-2 |  | covered |
| D-026 | Function arguments | SP7 | FUN-1 |  | covered |
| D-027 | Calls inside argument expressions | SP5 | EXP-49 |  | covered |
| D-028 | Error pattern bindings | SP8 | OUT-4, OUT-14 |  | covered |
| D-029 | Constant-only calculations outside global constants | SP4 | CEX-7, CEX-8, CEX-9 | OI-11 | covered |
| D-030 | Function completion analysis | SP6 | STM-20, STM-21 |  | covered |
| D-031 | Recursion, function values/pointers and user-defined generics | SP7 | FUN-4, FUN-5 |  | covered |
| D-032 | Function prototypes | SP7 | FUN-3 |  | covered |
| D-033 | Successful function returns | SP7 | FUN-2 |  | covered |
| D-034 | Reachable function fall-through | SP6 | STM-21 |  | covered |
| D-035 | Commands called by application code | SP11 | HEP-3 |  | covered |
| D-036 | Integer literals | SP1 | LEX-17, LEX-18; contextual typing pending SP5 | OI-14 | partial |
| D-037 | No preprocessor/macros/textual includes | SP1 | LEX-24 |  | covered |
| D-038 | Application declarations and struct fields visible across all source files | SP2 | NAM-13 |  | covered |
| D-039 | User modules/namespaces/imports/exports/classes/access modifiers | SP2 | NAM-8 |  | covered |
| D-040 | File order does not control name resolution or initialization order | SP2 | NAM-4 |  | covered |
| D-041 | Host entry point | SP11 | HEP-1, HEP-2, HEP-4 | OI-5 | covered |
| D-042 | Application protocol | SP11 | HEP-15 |  | covered |
| D-043 | Classical smart-card status | SP13 | HEP-12; status-word mapping pending Annex B (SP13) | OI-2 | partial |
| D-044 | Platform interface names cannot be redefined | SP2 | LEX-15, NAM-14 | OI-4 | covered |
| D-045 | One shared top-level naming scope for types and values | SP2 | NAM-11 |  | covered |
| D-046 | No function overloading or local function/type/error-set definitions | SP2 | NAM-7, NAM-12 |  | covered |
| D-047 | Fields and error members have owner-specific name scopes | SP2 | NAM-15, NAM-16, NAM-17 |  | covered |
| D-048 | Local binding visible only after its initializer completes | SP2 | NAM-19, NAM-20, NAM-22 |  | covered |
| D-049 | Command execution | SP11 | HEP-13, TXN-14 |  | covered |
| D-050 | Session state at chip power-on | SP9 | STA-4 |  | covered |
| D-051 | Ordinary traps preserve application session state | SP12 | STA-4, RTF-2, RTF-3 |  | covered |
| D-052 | Runtime-owned resources on ordinary trap | SP13 | RTF-2; resource lifecycle pending Annex B (SP13) |  | partial |
| D-053 | Session/persistent logical consistency | SP12 | STA-14, RTF-12 |  | covered |
| D-054 | Runtime-issued security reset | SP12 | STA-4, RTF-9 |  | covered |
| D-055 | Transactions roll back persistent changes only | SP10 | TXN-4, TXN-11 |  | covered |
| D-056 | Fatal platform failure triggers whole-chip security reset | SP13 | RTF-9; platform failure handling pending Annex B (SP13) |  | partial |
| D-057 | Each persistent assignment is atomic | SP9 | STA-11, STA-12 | OI-19 | covered |
| D-058 | Explicit handling of overflow and underflow | SP5 | EXP-23 |  | covered |
| D-059 | Global/local arrays of supported fixed-size values | SP3 | TYP-1, TYP-11, TYP-18 |  | covered |
| D-060 | Array type syntax `T[N]` | SP3 | TYP-17 |  | covered |
| D-061 | Array `.length` | SP5 | EXP-40 |  | covered |
| D-062 | Array index types | SP5 | EXP-39 |  | covered |
| D-063 | Array initialization with `fill(value)` or an exact-length element list | SP5 | EXP-43, EXP-44 |  | covered |
| D-064 | No special `zero` initializer | SP5 | EXP-44 |  | covered |
| D-065 | Named structures with typed fields | SP3 | TYP-4, TYP-13 |  | covered |
| D-066 | Empty structures | SP3 | TYP-13 |  | covered |
| D-067 | Enums | SP3 | TYP-4, TYP-10, TYP-11, TYP-12 |  | covered |
| D-068 | Enum defaults | SP3 | TYP-22 |  | covered |
| D-069 | Enum matching | SP6 | STM-16, STM-17 |  | covered |
| D-070 | Structure constructors | SP5 | EXP-45 |  | covered |
| D-071 | Structure array fields accept `fill(value)` and explicit lists | SP5 | TYP-14, EXP-45 |  | covered |
| D-072 | Structures may contain other structures | SP3 | TYP-14 |  | covered |
| D-073 | Nested fields inherit instance storage and mutability | SP3 | TYP-16 |  | covered |
| D-074 | Direct or indirect recursive containment is forbidden | SP3 | TYP-15, TYP-23 |  | covered |
| D-075 | Primitive types: `u8`, `u16`, `u32`, `i8`, `i16`, `i32`, `bool` | SP3 | TYP-1, TYP-6, TYP-7, TYP-8 |  | covered |
| D-076 | Byte arrays as `u8[N]` | SP3 | TYP-20 | OI-12 | covered |
| D-077 | Zero-length and direct multidimensional arrays | SP3 | TYP-18, TYP-19 |  | covered |
| D-078 | Whole-array assignment | SP6 | STM-8 |  | covered |
| D-079 | fill(expression) | SP5 | EXP-44 |  | covered |
| D-080 | Indexed assignment order | SP6 | STM-9, STM-10 | OI-9 | covered |
| D-081 | No implicit conversions between integer types | SP5 | TYP-5, EXP-12 |  | covered |
| D-082 | Arithmetic and comparisons require matching integer types | SP5 | EXP-12, EXP-13, EXP-14 |  | covered |
| D-083 | Explicit `convert<T>` and `checked_convert<T>` intrinsics | SP5 | EXP-31, EXP-32, EXP-33 |  | covered |
| D-084 | Contextual integer literal typing; no guessed default type | SP5 | EXP-7, EXP-10, EXP-11 | OI-14 | covered |
| D-085 | Literal-only array index expressions | SP5 | EXP-10, EXP-39 |  | covered |
| D-086 | Conversion intrinsics require a known source type | SP5 | EXP-31 |  | covered |
| D-087 | No widening to avoid intermediate arithmetic failure | SP5 | EXP-3, EXP-12, EXP-23 |  | covered |
| D-088 | Signed minimum / -1 | SP5 | EXP-24 |  | covered |
| D-089 | Signed minimum % -1 | SP5 | EXP-24 |  | covered |
| D-090 | Unary negation | SP5 | EXP-8, EXP-19, EXP-25 |  | covered |
| D-091 | Checked arithmetic | SP5 | EXP-29 | OI-13 | covered |
| D-092 | Wrapping arithmetic | SP5 | EXP-30 |  | covered |
| D-093 | Checked/wrapping arithmetic intrinsics in constants | SP4 | CEX-5 |  | covered |
| D-094 | Constant expressions | SP4 | CEX-3, CEX-6 |  | covered |
| D-095 | Guaranteed convert<T> in constant expressions | SP4 | CEX-3 |  | covered |
| D-096 | checked_convert<T> in constant expressions | SP4 | CEX-5 |  | covered |
| D-097 | Constant-evaluation boundary algorithm | SP4 | CEX-7 | OI-11 | covered |
| D-098 | Constant dependencies | SP4 | CEX-12, CEX-13 |  | covered |
| D-099 | Fixed-array lengths | SP4 | TYP-19, CEX-6 |  | covered |
| D-100 | No implicit boolean/numeric, array or structure conversions | SP3 | TYP-5, TYP-7 |  | covered |
| D-101 | No general truncating cast initially | SP5 | EXP-35 |  | covered |
| D-102 | Mixed binary operators require parentheses; no binary precedence hierarchy | SP5 | EXP-1, EXP-2, EXP-5 |  | covered |
| D-103 | Same-operator chains evaluate left to right; comparison chains forbidden | SP5 | EXP-3, EXP-4 |  | covered |
| D-104 | Left-to-right evaluation and short-circuit boolean logic | SP5 | EXP-20, EXP-21, EXP-50 |  | covered |
| D-105 | Assignment is a statement, not an expression | SP6 | STM-6 |  | covered |
| D-106 | Control flow: `if`, `while`, range `for`, `match`, `break`, `continue`, `return` | SP6 | STM-1, STM-11, STM-12, STM-13, STM-14, STM-15 |  | covered |
| D-107 | Explicit `return Ok(value)` / `return Err(error)`; no implicit success | SP8 | OUT-3, OUT-4 |  | covered |
| D-108 | Exhaustive result matching; read-only loop and pattern bindings | SP8 | OUT-12, OUT-13 |  | covered |
| D-109 | No `return`, `break` or `continue` across transaction boundaries | SP10 | TXN-6 |  | covered |
| D-110 | Explicit recoverable transaction exit: `abort Err(error);` | SP10 | TXN-7, TXN-8 |  | covered |
| D-111 | `abort` scope | SP10 | TXN-7 |  | covered |
| D-112 | Parameters: by value, read-only `ref`, mutable `inout` | SP7 | FUN-1, FUN-6 |  | covered |
| D-113 | Reference modes explicit at declaration and call site | SP7 | FUN-7 |  | covered |
| D-114 | References are call-scoped; no raw pointers or escaping references | SP7 | FUN-6, FUN-16 |  | covered |
| D-115 | Reference permissions | SP7 | FUN-6, FUN-10, FUN-12, FUN-15 |  | covered |
| D-116 | Assignment/value parameters/value returns create independent values | SP7 | EXP-46, STM-8, FUN-6, FUN-17 |  | covered |
| D-117 | References may target variables, fields and array elements; not temporaries | SP7 | FUN-9 |  | covered |
| D-118 | Reference and slice overlap | SP7 | FUN-12, FUN-13 |  | covered |
| D-119 | Array slices `array[start..end]` | SP7 | FUN-18, FUN-20 | OI-10 | covered |
| D-120 | Unspecified-size parameters `ref T[]` / `inout T[]` | SP7 | TYP-21, FUN-8, FUN-21 |  | covered |
| D-121 | By-value array parameters | SP7 | TYP-21, FUN-8 |  | covered |
| D-122 | Mutable global declaration initializers | SP9 | STA-2 |  | covered |
| D-123 | Automatic defaults | SP9 | TYP-22, STM-5, STA-3, STA-4 |  | covered |
| D-124 | Application-specific global setup | SP9 | STA-5 | OI-7 | covered |
| D-125 | Runtime resources | SP13 | — |  | pending |
| D-126 | Resource identifier space | SP13 | — |  | pending |
| D-127 | Resource storage strategy and cleanup | SP13 | — | OI-20 | pending |
| D-128 | Array/structure defaults apply recursively | SP9 | TYP-22, STM-5, STA-3, STA-4 |  | covered |
| D-129 | Global const requires an explicit initializer | SP4 | CEX-1 |  | covered |
| D-130 | Explicit array/structure construction remains complete | SP5 | EXP-43, EXP-45 |  | covered |
| D-131 | Nested transactions, including through function calls | SP10 | TXN-10 | OI-3 | covered |
| D-132 | Callee persistent assignments participate in an active transaction | SP10 | TXN-1 |  | covered |
| D-133 | By-value aggregate parameters | SP13 | FUN-17 (value semantics); placement guidance pending Annex B (SP13) | OI-21 | partial |
| D-134 | Familiar imperative syntax, static types | SP0 | 01 §1.1 |  | deferred |
| D-135 | Compact custom VM with single-digit KiB RAM goals | SP13 | — |  | pending |
| D-201 | No opaque platform value types | SP13 | — |  | pending |
| D-202 | Every resource operation validates existence, kind, state and permissions in the caller's resource space | SP13 | — |  | pending |
| D-203 | Resource operation outcomes: create on existing ID fails recoverably (never replaces) | SP13 | — | OI-15 | pending |
| D-204 | Copying a resource identifier copies only the number | SP13 | — |  | pending |
| D-205 | Language transactions do not automatically cover resource-API effects | SP13 | TXN-4, TXN-17; API contracts pending Annex B (SP13) |  | partial |
| D-206 | Exceeding a runtime stack/execution limit traps | SP12 | TYP-23, STA-13, TXN-16, RTF-6, RTF-7, RTF-8 |  | covered |
| D-207 | Commit failure never resumes after the block | SP10 | TXN-12, TXN-13 |  | covered |
| D-208 | The platform must prevent any other execution context (callbacks, reentrant commands) from observing partially updated transactional state | SP13 | TXN-14; platform mechanism pending Annex B (SP13) |  | partial |
| D-209 | Published application/platform error-code meanings remain stable | SP12 | OUT-17, RTF-11 | OI-15 | covered |
| D-401 | Source file extension is `.card` | SP1 | LEX-1 | OI-1 | covered |
| D-402 | No platform dispatch within an application; PN §1 row superseded | SP13 | HEP-15; PN §1 superseded row pending Annex B (SP13) | OI-2 | partial |
| D-403 | Nested transactions rejected statically by a structural call-graph rule | SP10 | TXN-10 | OI-3 | covered |
| D-404 | Keyword list; Ok/Err keywords; intrinsics and card/CardError reserved | SP1 | LEX-13, LEX-15, NAM-14 | OI-4 | covered |
| D-405 | Entry point is the single `command` declaration, any name | SP11 | HEP-1, HEP-16 | OI-5 | covered |
| D-406 | Platform API calls use the reserved `card.` path form | SP2 | NAM-17, NAM-18 | OI-6 | covered |
| D-407 | Lifecycle handlers use platform-reserved function names/signatures | SP9 | STA-5 | OI-7 | covered |
| D-408 | `attempt` allowed in any runtime expression position, with three exclusions | SP5 | EXP-51, OUT-8, OUT-10 | OI-8 | covered |
| D-409 | Assignment: destination path first, then RHS, then store | SP6 | STM-9 | OI-9 | covered |
| D-410 | Slice endpoint typing, order, positions and limits fixed | SP7 | EXP-42, FUN-8, FUN-18, FUN-19, FUN-20 | OI-10 | covered |
| D-411 | Constant-evaluation algorithm normative; constant OOB index is a compile error | SP4 | CEX-7, CEX-10 | OI-11 | covered |
| D-412 | No `byte` alias in Draft 0.1 | SP3 | TYP-20 | OI-12 | covered |
| D-413 | Zero or one error set; intrinsic outcomes may be forwarded | SP8 | OUT-5, OUT-15 | OI-13 | covered |
| D-414 | Literal prefix, digit and magnitude rules | SP1 | LEX-17, LEX-18, LEX-19, EXP-7 | OI-14 | covered |
| D-415 | Trap-kind and placeholder platform-error names | SP12 | RTF-4 (trap kinds), EXP-29, EXP-33; CardError names and codes pending Annex B (SP13) | OI-15 | partial |
| D-416 | Persistent deletion/upgrade/migration are platform-defined | SP9 | STA-3; platform items pending Annex B (SP13) | OI-16 | partial |
| D-417 | Large-data object API is future platform work | SP13 | — | OI-17 | pending |
| D-418 | Outcome typing settled by DN §6.3 | SP8 | OUT-1, OUT-2 | OI-18 | covered |
| D-419 | Oversized atomic aggregate assignment rejected at build/load time | SP9 | STA-13 | OI-19 | covered |
| D-420 | Resource storage strategy is platform-defined | SP13 | — | OI-20 | pending |
| D-421 | Call-frame placement is informative VM guidance | SP13 | — | OI-21 | pending |
| D-301 | Identifiers are case-sensitive ASCII: first character a letter or underscore, then letters, digits or underscores | SP1 | LEX-12 |  | covered |
| D-302 | `_` alone is reserved for an ignored pattern | SP1 | LEX-14 |  | covered |
| D-303 | No escaped or Unicode identifiers | SP1 | LEX-12, LEX-13 |  | covered |
| D-304 | Comments may contain Unicode | SP1 | LEX-3 |  | covered |
| D-305 | Spaces, tabs and line breaks separate tokens | SP1 | LEX-6 |  | covered |
| D-306 | Line comments `//` and block comments `/* */` | SP1 | LEX-7, LEX-8, LEX-9 |  | covered |
| D-307 | Integer literals are decimal, hexadecimal or binary | SP1 | LEX-17 |  | covered |
| D-308 | Numeric underscores appear only between digits: no leading, trailing or consecutive underscores, and none directly after a base prefix | SP1 | LEX-17, LEX-18 |  | covered |
| D-309 | No negative-literal token | SP1 | LEX-20 |  | covered |
| D-310 | Boolean literals are exactly `true` and `false` | SP1 | LEX-21 |  | covered |
| D-311 | File and line boundaries are preserved for diagnostics | SP1 | LEX-5, LEX-11 |  | covered |
| D-312 | Semicolons are mandatory | SP1 | LEX-23 |  | covered |
| D-313 | A declaration cannot span source files | SP2 | NAM-2 |  | covered |
| D-314 | Functions and types may be used before their declaration, including across files | SP2 | NAM-4, NAM-13 |  | covered |
| D-315 | Shadowing any visible name is forbidden | SP2 | NAM-21 |  | covered |
| D-316 | Function, command, structure, enum and error-set declarations are top-level only | SP2 | NAM-7 |  | covered |
| D-317 | Field names never become bare names | SP2 | NAM-17 |  | covered |
| D-318 | Enum variants and error members are always qualified | SP2 | NAM-16 |  | covered |
| D-319 | Platform-supplied configuration structures and algorithm enums use the ordinary naming rules, with no imports, namespaces or private fields | SP2 | NAM-14 |  | covered |
| D-320 | Plain `var` and combined qualifiers are forbidden at application scope | SP2 | NAM-9, NAM-10 |  | covered |
| D-321 | Arrays are composite types, not extra primitive scalar types | SP3 | TYP-1 |  | covered |
| D-322 | Every array length is a positive unsigned constant expression whose value fits in `u32` | SP3 | TYP-19 |  | covered |
| D-323 | Unsized array types `T[]` exist only as `ref`/`inout` parameter types | SP3 | TYP-2, TYP-21 |  | covered |
| D-324 | Structure field types are integers, booleans, enums, arrays and other structures | SP3 | TYP-14 |  | covered |
| D-325 | A type declaration does not define physical layout, wire encoding or durable encoding | SP3 | TYP-9 |  | covered |
| D-326 | Constant evaluation is deterministic and side-effect-free | SP4 | CEX-3, CEX-5, CEX-12 |  | covered |
| D-327 | Qualified enum variants are constant expressions | SP4 | CEX-3 |  | covered |
| D-328 | `.length` of a fixed array through a plain variable/field path is constant without reading contents | SP4 | CEX-4 |  | covered |
| D-329 | Compile-time evaluation preserves short-circuiting | SP4 | CEX-11 |  | covered |
| D-330 | Global constants need no writable state and their representation is an implementation detail | SP4 | CEX-2, FUN-10 |  | covered |
| D-331 | The nested-call ban applies in constant expressions | SP4 | CEX-14 |  | covered |
| D-332 | Constant expressions never read persistent or session contents | SP4 | CEX-5 |  | covered |
| D-333 | A typed operand supplies the expected type for an untyped literal operand on either side | SP5 | EXP-11 |  | covered |
| D-334 | A minimum signed literal such as `-128` is accepted in an `i8` context | SP5 | EXP-8, EXP-25 |  | covered |
| D-335 | Equality applies to matching integer types, `bool` and the same enum | SP5 | EXP-15, EXP-28 |  | covered |
| D-336 | Bitwise operators accept only unsigned operands of matching type | SP5 | EXP-17, EXP-18, EXP-26, EXP-27 |  | covered |
| D-337 | Calls, indexing and field access form operands | SP5 | EXP-1 |  | covered |
| D-338 | Optimizations preserve evaluation, short-circuiting and failure behavior | SP5 | EXP-22 |  | covered |
| D-339 | Runtime `.length` evaluates its receiver, preserving calls, errors and bounds checks | SP5 | EXP-40 |  | covered |
| D-340 | `fill` needs an expected fixed-array type | SP5 | EXP-44 |  | covered |
| D-341 | Array lists must have exactly the destination length | SP5 | EXP-43 |  | covered |
| D-342 | Integer-to-byte encoding is explicit, separate from numeric conversion, and must state byte order | SP5 | EXP-36, EXP-37, EXP-38 |  | covered |
| D-343 | Braces are mandatory on every control-flow body and match arm | SP6 | STM-1, STM-11 |  | covered |
| D-344 | No `switch`, fall-through, `goto`, labelled loops or multi-level exits | SP6 | STM-1, STM-16 |  | covered |
| D-345 | `for` uses a half-open ascending unit-step range | SP6 | STM-13, STM-14 |  | covered |
| D-346 | `continue` in a `while` rechecks the condition | SP6 | STM-15 |  | covered |
| D-347 | Infinite loops are written `while true` | SP6 | STM-12 |  | covered |
| D-348 | `require c else E | SP6 | STM-19 |  | covered |
| D-349 | No chained assignment, increment/decrement operators or assignment in conditions | SP6 | STM-6 |  | covered |
| D-350 | An explicit local initializer is not preceded by a default | SP6 | STM-5 |  | covered |
| D-351 | Unreachable statements are permitted and still checked | SP6 | STM-22 |  | covered |
| D-352 | Ordinary functions may access globals, call platform APIs and open transactions | SP7 | FUN-3, FUN-22 |  | covered |
| D-353 | All arguments are evaluated left to right and reference/slice regions established and bounds-checked before the callee starts | SP7 | FUN-11 |  | covered |
| D-354 | Forwarding: `ref` to `ref` | SP7 | FUN-15 |  | covered |
| D-355 | References and views end with their call on Ok or Err | SP7 | FUN-16 |  | covered |
| D-356 | Storage identity survives reference passing: a write through `inout` to persistent storage is a persistent write | SP7 | FUN-23 |  | covered |
| D-357 | Compilers preserve observable aliasing effects | SP7 | FUN-14 |  | covered |
| D-358 | Physical copies may be removed only when behavior is unchanged | SP7 | FUN-17 |  | covered |
| D-359 | Inside the callee a view is indexed from 0 and its `.length` is the region length | SP7 | FUN-21 |  | covered |
| D-360 | An outcome match has exactly one success arm, zero or more specific error arms and one mandatory final catch-all (`Err(name)` or `Err(_)`) | SP8 | OUT-12 |  | covered |
| D-361 | Pattern vocabulary: `Ok(name)`, `Ok(_)`, `Ok()`, `Err(Set.Member)`, `Err(name)`, `Err(_)` | SP8 | OUT-11 |  | covered |
| D-362 | Success payload bindings are independent read-only arm-local copies | SP8 | OUT-13 |  | covered |
| D-363 | `Ok` and `Err` are restricted syntax for returns, `abort` and patterns, not general constructors | SP8 | OUT-6 |  | covered |
| D-364 | `attempt` propagates the error unchanged regardless of the enclosing payload type and never catches traps | SP8 | OUT-10 |  | covered |
| D-365 | Application errors carry identity only (no strings or payloads) | SP8 | OUT-16, OUT-18 |  | covered |
| D-366 | Published error codes must not change meaning or be reused after removal | SP8 | OUT-17 |  | covered |
| D-367 | Platform errors use the reserved `CardError` namespace, which applications cannot impersonate | SP8 | OUT-18, OUT-19 |  | covered |
| D-368 | Returning or propagating `Err` is not a rollback request | SP8 | OUT-20 |  | covered |
| D-369 | Persistent defaults apply once, when persistent state is first created | SP9 | STA-3 |  | covered |
| D-370 | Setup writing persistent values is distinct from volatile setup | SP9 | STA-5 |  | covered |
| D-371 | A persistent assignment is atomic: after interruption the destination holds its complete old or complete new value | SP9 | STA-11, STA-12 |  | covered |
| D-372 | Two persistent assignments are not collectively atomic without a transaction | SP9 | STA-12 |  | covered |
| D-373 | Whole-structure and whole-array assignment, including fill, is atomic for the whole destination | SP9 | STA-11 |  | covered |
| D-374 | Global means application-wide | SP9 | STA-1 |  | covered |
| D-375 | Reaching the closing brace commits | SP10 | TXN-3 |  | covered |
| D-376 | Reads within a transaction see earlier writes, including through references and called functions | SP10 | TXN-2 |  | covered |
| D-377 | Only persistent state participates | SP10 | TXN-4 |  | covered |
| D-378 | A callee's Err is not an abort request | SP10 | TXN-9 |  | covered |
| D-379 | abort stops the body, rolls back pending persistent writes and returns the error unchanged from the enclosing function or command | SP10 | TXN-8 |  | covered |
| D-380 | The abort operand is a named error member or an in-scope error binding | SP10 | TXN-7 |  | covered |
| D-381 | break/continue targeting a loop entirely inside the transaction is valid | SP10 | TXN-6 |  | covered |
| D-382 | A trap inside a transaction rolls back its pending persistent writes and aborts the command | SP10 | TXN-11 |  | covered |
| D-383 | A command is not implicitly a transaction | SP10 | TXN-5 |  | covered |
| D-384 | `request.length` is the number of bytes received | SP11 | HEP-5, HEP-6 |  | covered |
| D-385 | The platform supplies separate, non-overlapping request and response regions valid only for the invocation | SP11 | HEP-7 |  | covered |
| D-386 | The application must write every response byte it includes in the count | SP11 | HEP-8 |  | covered |
| D-387 | Response data is transmitted only after successful completion and count validation | SP11 | HEP-9 |  | covered |
| D-388 | Ok means a response was produced, not that the business operation succeeded | SP11 | HEP-11 |  | covered |
| D-389 | No automatic serialization of language values and no automatic dispatch of operation identifiers | SP11 | HEP-15 |  | covered |
| D-390 | The returned u32 is a byte count, not a status word | SP11 | HEP-9, HEP-12 |  | covered |
| D-391 | A reset or power loss may prevent any response | SP11 | HEP-12 |  | covered |
| D-392 | A trap ends only the current command | SP11 | HEP-14 |  | covered |
| D-393 | Response transmission never happens inside a transaction | SP11 | HEP-10 |  | covered |
| D-394 | A trap aborts the current command and cannot be caught by application `match` or `attempt` | SP12 | RTF-1 |  | covered |
| D-395 | Session state may be partially updated when a command traps | SP12 | RTF-2 |  | covered |
| D-396 | Defined trap cases: arithmetic failures, out-of-bounds access, invalid shift counts, stack or execution-budget exhaustion, attempted nested transactions, invalid VM instructions or state | SP12 | RTF-4 |  | covered |
| D-397 | A security reset clears volatile state across all applications and is never returned as a `CardError` | SP12 | RTF-9 |  | covered |
| D-398 | Failures may terminate execution without an outcome while the persistent atomicity guarantees still hold | SP12 | RTF-10 |  | covered |
| D-399 | An ordinary trap does not trigger a lifecycle reset | SP12 | RTF-3 |  | covered |
| D-423 | BOM ignored; LF, CR and CRLF are line breaks | SP1 | LEX-4, LEX-5 | OI-23 | covered |
| D-424 | Longest-match tokens; numeric-run rule; no identifier length limit | SP1 | LEX-10, LEX-16, LEX-18 | OI-24 | covered |
| D-425 | Primitive type names are predeclared | SP2 | NAM-14 | OI-25 | covered |
| D-426 | File-list duplicates are a build error; empty list allowed | SP2 | NAM-3 | OI-26 | covered |
| D-427 | Storage representation is not language-visible | SP3 | TYP-9 | OI-27 | covered |
| D-428 | Error-member codes are integer literals | SP8 | CEX-6, OUT-16 | OI-28 | covered |
| D-429 | Constant slice endpoints checked at compile time | SP4 | CEX-10 | OI-29 | covered |
| D-430 | A structure constructor directly in an if/while condition, for range bound or match scrutinee must be parenthesized | SP5 | EXP-6 | OI-30 | covered |
| D-431 | Arithmetic failure classes: above maximum is Overflow | SP5 | EXP-23, EXP-24, EXP-25, EXP-29 | OI-31 | covered |
| D-432 | Add truncate<T>(x) and value-based byte-order intrinsics encode_be/encode_le and decode_be/decode_le<T> | SP5 | EXP-34, EXP-36, EXP-37, LEX-15, NAM-14, CEX-5 | OI-32 | covered |
| D-433 | Only `attempt call | SP6 | STM-2 | OI-33 | covered |
| D-434 | No standalone block statements in Draft 0.1 | SP6 | STM-3 | OI-34 | covered |
| D-435 | for index or pattern binding may be passed as ref | SP7 | FUN-9, FUN-10 | OI-35 | covered |
| D-436 | An error set must declare at least one member | SP8 | OUT-15 | OI-36 | covered |
| D-437 | Application code may name `CardError` members only in `Err` patterns | SP8 | OUT-4, OUT-19, STM-19 | OI-37 | covered |
| D-422 | Lifecycle handlers: not callable from application code | SP9 | STA-7, STA-8, STA-9, STA-10, NAM-14 | OI-22 | covered |
| D-438 | Placeholder lifecycle handlers on_install() and on_power_on(), no parameters and no payload, until the platform catalog exists | SP9 | STA-6, NAM-14 | OI-38 | covered |
| D-439 | Exceeding transaction capacity at runtime is trap(TXN-CAPACITY) | SP10 | TXN-16 | OI-39 | covered |
| D-440 | A call to a platform API marked not-in-transactions, lexically inside a transaction or reachable from one through the call graph, is a compilation error (CE-TXN-4) | SP10 | TXN-17 | OI-40 | covered |
| D-441 | Response region contents unspecified; no foreign data | SP11 | HEP-8; PLT requirement pending Annex B (SP13) | OI-41 | partial |
| D-442 | Maximum stack need computed; excess rejected at build or load | SP12 | RTF-7 | OI-42 | covered |
