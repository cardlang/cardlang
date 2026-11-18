# Annex D — Traceability

This annex links the specification to its sources in both directions.

- **D.1 (forward):** each specification file → the design-note sections it draws on.
- **D.2 (reverse):** each decision ID → the rules that implement it, or the open issue that blocks it.
- **D.3 (coverage):** each rule → the conformance tests that check it, or the reason none can.

Decision IDs are defined in `plans_and_notes/decision-register.md`. Every decision is covered (D-134 is informative), and every rule has a test or a stated reason. `tools/checkers/speccheck.py` checks both.

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
| 06-expressions.md | SP5 | DN §3.2, §3.3, §3.4, §3.5, §3.7, §3.11, §6.2, §6.5, §8.1, §8.2, §8.3, §9.3 | EXP-1 … EXP-54 |
| 07-statements-and-control-flow.md | SP6 | DN §3.5, §3.6, §3.7 (completion), §3.9, §3.10, §3.11, §5.1, §8.2 | STM-1 … STM-23 |
| 08-functions-and-references.md | SP7 | DN §3.0, §3.7, §3.8, §8.4, §9.2 | FUN-1 … FUN-24 |
| 09-outcomes-and-errors.md | SP8 | DN §3.2, §3.6, §3.7, §6.1, §6.2, §6.3, §7.2; PN §5 | OUT-1 … OUT-20 |
| 10-state-and-initialization.md | SP9 | DN §3.9, §5, §5.1, §6.4 (session), §7.1, §8.2, §8.3, §9.3; PN §3 | STA-1 … STA-14 |
| 11-transactions.md | SP10 | DN §3.6 (boundary), §4, §6.4, §7.1–§7.4; PN §5 | TXN-1 … TXN-18 |
| 12-host-entry-point.md | SP11 | DN §3.7, §4, §4.1, §6.3, §7.4, §12; PN §1, §5 | HEP-1 … HEP-16 |
| 13-runtime-failures.md | SP12 | DN §3.6, §6.4, §6.5, §7.2, §12, §13; PN §3, §4, §5 | RTF-1 … RTF-12 |
| annex-A-grammar.md | SP1–SP14 | DN §3.0 plus the syntax of every chapter | A.1, A.2.1–A.2.10, A.3; consolidated and checked mechanically (SP14) |
| annex-B-platform-contract.md | SP13 | PN §1–§5; DN §4, §6.3, §6.4, §7.2, §7.4, §11, §12 | PLT-1 … PLT-34 |
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
| D-009 | Simple persistent declarations plus an object API for larger data | SP13 | PLT-17 | OI-17 | covered |
| D-010 | Recoverable errors through explicit results, execution faults through traps | SP8 | OUT-1, RTF-1 |  | covered |
| D-011 | No general-purpose exceptions initially | SP8 | OUT-1 |  | covered |
| D-012 | Every function returns a success/error result | SP8 | OUT-1, OUT-2, EXP-48 | OI-18 | covered |
| D-013 | Explicit outcome handling uses `match` with `Ok` / `Err` | SP8 | OUT-11 |  | covered |
| D-014 | Automatic error propagation with `attempt` | SP8 | OUT-8, OUT-10, EXP-51 |  | covered |
| D-015 | Discarded function outcomes | SP8 | OUT-5, OUT-7, EXP-48 |  | covered |
| D-016 | Stored result values / user-visible `Result<T>` | SP8 | OUT-2, TYP-2, EXP-48 |  | covered |
| D-017 | `attempt` type | SP8 | OUT-9, OUT-10 |  | covered |
| D-018 | One application error set with explicit nonzero `u16` codes | SP8 | OUT-15, OUT-16, PLT-27 | OI-13 | covered |
| D-019 | Application/platform errors and traps have separate reporting categories | SP8 | OUT-18, HEP-12, RTF-11, PLT-9 |  | covered |
| D-020 | Single application or completely isolated applications | SP2 | NAM-5, PLT-2 |  | covered |
| D-021 | Multiple source files form one application compilation unit | SP2 | NAM-1 |  | covered |
| D-022 | Source files contain complete top-level declarations; no application wrapper | SP2 | NAM-1, NAM-2, NAM-6, NAM-8 |  | covered |
| D-023 | Source extension `.card`; UTF-8 source, ASCII identifiers | SP1 | LEX-1, LEX-2, LEX-3, LEX-12 | OI-1 | covered |
| D-024 | Mandatory semicolons, braces and named-declaration type annotations | SP1 | LEX-22, LEX-23, NAM-9, TYP-3, STM-1, FUN-1; Annex A §A.2 |  | covered |
| D-025 | No-value ordinary function signature | SP7 | FUN-2, OUT-3 |  | covered |
| D-026 | Function arguments | SP7 | FUN-1, EXP-47 |  | covered |
| D-027 | Calls inside argument expressions | SP5 | EXP-49, CEX-14 |  | covered |
| D-028 | Error pattern bindings | SP8 | OUT-4, OUT-14, TYP-2, STM-19 |  | covered |
| D-029 | Constant-only calculations outside global constants | SP4 | CEX-7, CEX-8, CEX-9 | OI-11 | covered |
| D-030 | Function completion analysis | SP6 | STM-20, STM-21, TXN-15 |  | covered |
| D-031 | Recursion, function values/pointers and user-defined generics | SP7 | FUN-4, FUN-5, EXP-47 |  | covered |
| D-032 | Function prototypes | SP7 | FUN-3 |  | covered |
| D-033 | Successful function returns | SP7 | FUN-2 |  | covered |
| D-034 | Reachable function fall-through | SP6 | STM-21 |  | covered |
| D-035 | Commands called by application code | SP11 | HEP-3, EXP-47, HEP-4 |  | covered |
| D-036 | Integer literals | SP1 | LEX-17, LEX-18, EXP-7, EXP-10, EXP-11 | OI-14 | covered |
| D-037 | No preprocessor/macros/textual includes | SP1 | LEX-24 |  | covered |
| D-038 | Application declarations and struct fields visible across all source files | SP2 | NAM-13 |  | covered |
| D-039 | User modules/namespaces/imports/exports/classes/access modifiers | SP2 | NAM-8 |  | covered |
| D-040 | File order does not control name resolution or initialization order | SP2 | NAM-4 |  | covered |
| D-041 | Host entry point | SP11 | HEP-1, HEP-2, HEP-4, PLT-3 | OI-5 | covered |
| D-042 | Application protocol | SP11 | HEP-15, PLT-3 |  | covered |
| D-043 | Classical smart-card status | SP13 | HEP-12, PLT-9 | OI-2 | covered |
| D-044 | Platform interface names cannot be redefined | SP2 | LEX-15, NAM-14 | OI-4 | covered |
| D-045 | One shared top-level naming scope for types and values | SP2 | NAM-11, TYP-3 |  | covered |
| D-046 | No function overloading or local function/type/error-set definitions | SP2 | NAM-7, NAM-12 |  | covered |
| D-047 | Fields and error members have owner-specific name scopes | SP2 | NAM-15, NAM-16, NAM-17, EXP-41 |  | covered |
| D-048 | Local binding visible only after its initializer completes | SP2 | NAM-19, NAM-20, NAM-22 |  | covered |
| D-049 | Command execution | SP11 | HEP-13, TXN-14, PLT-4 |  | covered |
| D-050 | Session state at chip power-on | SP9 | STA-4 |  | covered |
| D-051 | Ordinary traps preserve application session state | SP12 | STA-4, RTF-2, RTF-3 |  | covered |
| D-052 | Runtime-owned resources on ordinary trap | SP13 | RTF-2, PLT-23 |  | covered |
| D-053 | Session/persistent logical consistency | SP12 | STA-14, RTF-12, RTF-2 |  | covered |
| D-054 | Runtime-issued security reset | SP12 | STA-4, RTF-9, PLT-19 |  | covered |
| D-055 | Transactions roll back persistent changes only | SP10 | TXN-4, TXN-11, RTF-2 |  | covered |
| D-056 | Fatal platform failure triggers whole-chip security reset | SP13 | RTF-9, PLT-19 |  | covered |
| D-057 | Each persistent assignment is atomic | SP9 | STA-11, STA-12, STM-10, PLT-12 | OI-19 | covered |
| D-058 | Explicit handling of overflow and underflow | SP5 | EXP-23 |  | covered |
| D-059 | Global/local arrays of supported fixed-size values | SP3 | TYP-1, TYP-11, TYP-18 |  | covered |
| D-060 | Array type syntax `T[N]` | SP3 | TYP-17 |  | covered |
| D-061 | Array `.length` | SP5 | EXP-40, STM-7 |  | covered |
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
| D-073 | Nested fields inherit instance storage and mutability | SP3 | TYP-16, CEX-2, STM-7, STA-1 |  | covered |
| D-074 | Direct or indirect recursive containment is forbidden | SP3 | TYP-15, TYP-23 |  | covered |
| D-075 | Primitive types: `u8`, `u16`, `u32`, `i8`, `i16`, `i32`, `bool` | SP3 | TYP-1, TYP-6, TYP-7, TYP-8 |  | covered |
| D-076 | Byte arrays as `u8[N]` | SP3 | TYP-20 | OI-12 | covered |
| D-077 | Zero-length and direct multidimensional arrays | SP3 | TYP-18, TYP-19 |  | covered |
| D-078 | Whole-array assignment | SP6 | STM-8, TYP-4 |  | covered |
| D-079 | fill(expression) | SP5 | EXP-44 |  | covered |
| D-080 | Indexed assignment order | SP6 | STM-9, STM-10 | OI-9 | covered |
| D-081 | No implicit conversions between integer types | SP5 | TYP-5, EXP-12 |  | covered |
| D-082 | Arithmetic and comparisons require matching integer types | SP5 | EXP-12, EXP-13, EXP-14 |  | covered |
| D-083 | Explicit `convert<T>` and `checked_convert<T>` intrinsics | SP5 | EXP-31, EXP-32, EXP-33 |  | covered |
| D-084 | Contextual integer literal typing; no guessed default type | SP5 | EXP-7, EXP-10, EXP-11, LEX-19, TYP-5 | OI-14 | covered |
| D-085 | Literal-only array index expressions | SP5 | EXP-10, EXP-39 |  | covered |
| D-086 | Conversion intrinsics require a known source type | SP5 | EXP-31 |  | covered |
| D-087 | No widening to avoid intermediate arithmetic failure | SP5 | EXP-3, EXP-12, EXP-23, CEX-8 |  | covered |
| D-088 | Signed minimum / -1 | SP5 | EXP-24, CEX-9 |  | covered |
| D-089 | Signed minimum % -1 | SP5 | EXP-24, CEX-9 |  | covered |
| D-090 | Unary negation | SP5 | EXP-8, EXP-19, EXP-25, CEX-9 |  | covered |
| D-091 | Checked arithmetic | SP5 | EXP-29 | OI-13 | covered |
| D-092 | Wrapping arithmetic | SP5 | EXP-30 |  | covered |
| D-093 | Checked/wrapping arithmetic intrinsics in constants | SP4 | CEX-5 |  | covered |
| D-094 | Constant expressions | SP4 | CEX-3, CEX-6 |  | covered |
| D-095 | Guaranteed convert<T> in constant expressions | SP4 | CEX-3, EXP-32 |  | covered |
| D-096 | checked_convert<T> in constant expressions | SP4 | CEX-5 |  | covered |
| D-097 | Constant-evaluation boundary algorithm | SP4 | CEX-7 | OI-11 | covered |
| D-098 | Constant dependencies | SP4 | CEX-12, CEX-13 |  | covered |
| D-099 | Fixed-array lengths | SP4 | TYP-19, CEX-6 |  | covered |
| D-100 | No implicit boolean/numeric, array or structure conversions | SP3 | TYP-5, TYP-7, EXP-7, EXP-16, EXP-35 |  | covered |
| D-101 | No general truncating cast initially | SP5 | EXP-35 |  | covered |
| D-102 | Mixed binary operators require parentheses; no binary precedence hierarchy | SP5 | EXP-1, EXP-2, EXP-5, LEX-22 |  | covered |
| D-103 | Same-operator chains evaluate left to right; comparison chains forbidden | SP5 | EXP-3, EXP-4 |  | covered |
| D-104 | Left-to-right evaluation and short-circuit boolean logic | SP5 | EXP-20, EXP-21, EXP-50, FUN-11 |  | covered |
| D-105 | Assignment is a statement, not an expression | SP6 | STM-6 |  | covered |
| D-106 | Control flow: `if`, `while`, range `for`, `match`, `break`, `continue`, `return` | SP6 | STM-1, STM-11, STM-12, STM-13, STM-14, STM-15, STM-18 |  | covered |
| D-107 | Explicit `return Ok(value)` / `return Err(error)`; no implicit success | SP8 | OUT-3, OUT-4, STM-18 |  | covered |
| D-108 | Exhaustive result matching; read-only loop and pattern bindings | SP8 | OUT-12, OUT-13, STM-7 |  | covered |
| D-109 | No `return`, `break` or `continue` across transaction boundaries | SP10 | TXN-6, TXN-18 |  | covered |
| D-110 | Explicit recoverable transaction exit: `abort Err(error);` | SP10 | TXN-7, TXN-8, TXN-18 |  | covered |
| D-111 | `abort` scope | SP10 | TXN-7 |  | covered |
| D-112 | Parameters: by value, read-only `ref`, mutable `inout` | SP7 | FUN-1, FUN-6, STM-7 |  | covered |
| D-113 | Reference modes explicit at declaration and call site | SP7 | FUN-7 |  | covered |
| D-114 | References are call-scoped; no raw pointers or escaping references | SP7 | FUN-6, FUN-16, TYP-2 |  | covered |
| D-115 | Reference permissions | SP7 | FUN-6, FUN-10, FUN-12, FUN-15 |  | covered |
| D-116 | Assignment/value parameters/value returns create independent values | SP7 | EXP-46, STM-8, FUN-6, FUN-17 |  | covered |
| D-117 | References may target variables, fields and array elements; not temporaries | SP7 | FUN-9 |  | covered |
| D-118 | Reference and slice overlap | SP7 | FUN-12, FUN-13 |  | covered |
| D-119 | Array slices `array[start..end]` | SP7 | FUN-18, FUN-20, EXP-42 | OI-10 | covered |
| D-120 | Unspecified-size parameters `ref T[]` / `inout T[]` | SP7 | TYP-21, FUN-8, FUN-21 |  | covered |
| D-121 | By-value array parameters | SP7 | TYP-21, FUN-8 |  | covered |
| D-122 | Mutable global declaration initializers | SP9 | STA-2 |  | covered |
| D-123 | Automatic defaults | SP9 | TYP-22, STM-5, STA-3, STA-4 |  | covered |
| D-124 | Application-specific global setup | SP9 | STA-5, PLT-18 | OI-7 | covered |
| D-125 | Runtime resources | SP13 | PLT-20 |  | covered |
| D-126 | Resource identifier space | SP13 | PLT-2, PLT-20 |  | covered |
| D-127 | Resource storage strategy and cleanup | SP13 | PLT-24 | OI-20 | covered |
| D-128 | Array/structure defaults apply recursively | SP9 | TYP-22, STM-5, STA-3, STA-4 |  | covered |
| D-129 | Global const requires an explicit initializer | SP4 | CEX-1 |  | covered |
| D-130 | Explicit array/structure construction remains complete | SP5 | EXP-43, EXP-45 |  | covered |
| D-131 | Nested transactions, including through function calls | SP10 | TXN-10 | OI-3 | covered |
| D-132 | Callee persistent assignments participate in an active transaction | SP10 | TXN-1 |  | covered |
| D-133 | By-value aggregate parameters | SP13 | FUN-17, Annex B §B.11 | OI-21 | covered |
| D-134 | Familiar imperative syntax, static types | SP0 | 01 §1.1 |  | deferred |
| D-135 | Compact custom VM with single-digit KiB RAM goals | SP13 | Annex B §B.11 (informative) |  | covered |
| D-201 | No opaque platform value types | SP13 | PLT-21, NAM-14, PLT-25 |  | covered |
| D-202 | Every resource operation validates existence, kind, state and permissions in the caller's resource space | SP13 | PLT-20, PLT-22 |  | covered |
| D-203 | Resource operation outcomes: create on existing ID fails recoverably (never replaces) | SP13 | PLT-22 | OI-15 | covered |
| D-204 | Copying a resource identifier copies only the number | SP13 | PLT-20, PLT-22, PLT-23 |  | covered |
| D-205 | Language transactions do not automatically cover resource-API effects | SP13 | TXN-4, TXN-17, PLT-24 |  | covered |
| D-206 | Exceeding a runtime stack/execution limit traps | SP12 | TYP-23, STA-13, TXN-16, RTF-6, RTF-7, RTF-8, PLT-1, PLT-15, PLT-29 |  | covered |
| D-207 | Commit failure never resumes after the block | SP10 | TXN-12, TXN-13, RTF-10, PLT-13, PLT-14 |  | covered |
| D-208 | The platform must prevent any other execution context (callbacks, reentrant commands) from observing partially updated transactional state | SP13 | TXN-14, PLT-5 |  | covered |
| D-209 | Published application/platform error-code meanings remain stable | SP12 | OUT-17, RTF-11, PLT-11 | OI-15 | covered |
| D-401 | Source file extension is `.card` | SP1 | LEX-1 | OI-1 | covered |
| D-402 | No platform dispatch within an application; PN §1 row superseded | SP13 | HEP-15, PLT-3 | OI-2 | covered |
| D-403 | Nested transactions rejected statically by a structural call-graph rule | SP10 | TXN-10 | OI-3 | covered |
| D-404 | Keyword list; Ok/Err keywords; intrinsics and card/CardError reserved | SP1 | LEX-13, LEX-15, NAM-14 | OI-4 | covered |
| D-405 | Entry point is the single `command` declaration, any name | SP11 | HEP-1, HEP-16 | OI-5 | covered |
| D-406 | Platform API calls use the reserved `card.` path form | SP2 | NAM-17, NAM-18, EXP-47, PLT-25 | OI-6 | covered |
| D-407 | Lifecycle handlers use platform-reserved function names/signatures | SP9 | STA-5, PLT-18 | OI-7 | covered |
| D-408 | `attempt` allowed in any runtime expression position, with three exclusions | SP5 | EXP-51, OUT-8, OUT-10 | OI-8 | covered |
| D-409 | Assignment: destination path first, then RHS, then store | SP6 | STM-9 | OI-9 | covered |
| D-410 | Slice endpoint typing, order, positions and limits fixed | SP7 | EXP-42, FUN-8, FUN-18, FUN-19, FUN-20, STM-7 | OI-10 | covered |
| D-411 | Constant-evaluation algorithm normative; constant OOB index is a compile error | SP4 | CEX-7, CEX-10 | OI-11 | covered |
| D-412 | No `byte` alias in Draft 0.1 | SP3 | TYP-20 | OI-12 | covered |
| D-413 | Zero or one error set; intrinsic outcomes may be forwarded | SP8 | OUT-5, OUT-15, TYP-12 | OI-13 | covered |
| D-414 | Literal prefix, digit and magnitude rules | SP1 | LEX-17, LEX-18, LEX-19, EXP-7 | OI-14 | covered |
| D-415 | Trap-kind and placeholder platform-error names | SP12 | EXP-29, EXP-33, RTF-4, PLT-27, PLT-28, OUT-19 | OI-15 | covered |
| D-416 | Persistent deletion/upgrade/migration are platform-defined | SP9 | STA-3, PLT-16 | OI-16 | covered |
| D-417 | Large-data object API is future platform work | SP13 | PLT-17 | OI-17 | covered |
| D-418 | Outcome typing settled by DN §6.3 | SP8 | OUT-1, OUT-2 | OI-18 | covered |
| D-419 | Oversized atomic aggregate assignment rejected at build/load time | SP9 | STA-13, PLT-15 | OI-19 | covered |
| D-420 | Resource storage strategy is platform-defined | SP13 | PLT-24 | OI-20 | covered |
| D-421 | Call-frame placement is informative VM guidance | SP13 | FUN-17, Annex B §B.11 (informative) | OI-21 | covered |
| D-301 | Identifiers are case-sensitive ASCII: first character a letter or underscore, then letters, digits or underscores | SP1 | LEX-12 |  | covered |
| D-302 | `_` alone is reserved for an ignored pattern | SP1 | LEX-14 |  | covered |
| D-303 | No escaped or Unicode identifiers | SP1 | LEX-12, LEX-13 |  | covered |
| D-304 | Comments may contain Unicode | SP1 | LEX-3 |  | covered |
| D-305 | Spaces, tabs and line breaks separate tokens | SP1 | LEX-6 |  | covered |
| D-306 | Line comments `//` and block comments `/* */` | SP1 | LEX-7, LEX-8, LEX-9 |  | covered |
| D-307 | Integer literals are decimal, hexadecimal or binary | SP1 | LEX-17 |  | covered |
| D-308 | Numeric underscores appear only between digits: no leading, trailing or consecutive underscores, and none directly after a base prefix | SP1 | LEX-17, LEX-18 |  | covered |
| D-309 | No negative-literal token | SP1 | LEX-20 |  | covered |
| D-310 | Boolean literals are exactly `true` and `false` | SP1 | LEX-21, EXP-9 |  | covered |
| D-311 | File and line boundaries are preserved for diagnostics | SP1 | LEX-5, LEX-11 |  | covered |
| D-312 | Semicolons are mandatory | SP1 | LEX-23, LEX-6 |  | covered |
| D-313 | A declaration cannot span source files | SP2 | NAM-2 |  | covered |
| D-314 | Functions and types may be used before their declaration, including across files | SP2 | NAM-4, NAM-13, TYP-3 |  | covered |
| D-315 | Shadowing any visible name is forbidden | SP2 | NAM-21 |  | covered |
| D-316 | Function, command, structure, enum and error-set declarations are top-level only | SP2 | NAM-7 |  | covered |
| D-317 | Field names never become bare names | SP2 | NAM-17, EXP-41 |  | covered |
| D-318 | Enum variants and error members are always qualified | SP2 | NAM-16 |  | covered |
| D-319 | Platform-supplied configuration structures and algorithm enums use the ordinary naming rules, with no imports, namespaces or private fields | SP2 | NAM-14, PLT-21 |  | covered |
| D-320 | Plain `var` and combined qualifiers are forbidden at application scope | SP2 | NAM-9, NAM-10 |  | covered |
| D-321 | Arrays are composite types, not extra primitive scalar types | SP3 | TYP-1 |  | covered |
| D-322 | Every array length is a positive unsigned constant expression whose value fits in `u32` | SP3 | TYP-19 |  | covered |
| D-323 | Unsized array types `T[]` exist only as `ref`/`inout` parameter types | SP3 | TYP-2, TYP-21 |  | covered |
| D-324 | Structure field types are integers, booleans, enums, arrays and other structures | SP3 | TYP-14 |  | covered |
| D-325 | A type declaration does not define physical layout, wire encoding or durable encoding | SP3 | TYP-9, PLT-16 |  | covered |
| D-326 | Constant evaluation is deterministic and side-effect-free | SP4 | CEX-3, CEX-5, CEX-12 |  | covered |
| D-327 | Qualified enum variants are constant expressions | SP4 | CEX-3 |  | covered |
| D-328 | `.length` of a fixed array through a plain variable/field path is constant without reading contents | SP4 | CEX-4 |  | covered |
| D-329 | Compile-time evaluation preserves short-circuiting | SP4 | CEX-11 |  | covered |
| D-330 | Global constants need no writable state and their representation is an implementation detail | SP4 | CEX-2, FUN-10 |  | covered |
| D-331 | The nested-call ban applies in constant expressions | SP4 | CEX-14, EXP-49 |  | covered |
| D-332 | Constant expressions never read persistent or session contents | SP4 | CEX-5 |  | covered |
| D-333 | A typed operand supplies the expected type for an untyped literal operand on either side | SP5 | EXP-11 |  | covered |
| D-334 | A minimum signed literal such as `-128` is accepted in an `i8` context | SP5 | EXP-8, EXP-25 |  | covered |
| D-335 | Equality applies to matching integer types, `bool` and the same enum | SP5 | EXP-15, EXP-28 |  | covered |
| D-336 | Bitwise operators accept only unsigned operands of matching type | SP5 | EXP-17, EXP-18, EXP-26, EXP-27 |  | covered |
| D-337 | Calls, indexing and field access form operands | SP5 | EXP-1 |  | covered |
| D-338 | Optimizations preserve evaluation, short-circuiting and failure behavior | SP5 | EXP-22, RTF-5 |  | covered |
| D-339 | Runtime `.length` evaluates its receiver, preserving calls, errors and bounds checks | SP5 | EXP-40 |  | covered |
| D-340 | `fill` needs an expected fixed-array type | SP5 | EXP-44, STM-9 |  | covered |
| D-341 | Array lists must have exactly the destination length | SP5 | EXP-43 |  | covered |
| D-342 | Integer-to-byte encoding is explicit, separate from numeric conversion, and must state byte order | SP5 | EXP-36, EXP-37, EXP-38 |  | covered |
| D-343 | Braces are mandatory on every control-flow body and match arm | SP6 | STM-1, STM-11 |  | covered |
| D-344 | No `switch`, fall-through, `goto`, labelled loops or multi-level exits | SP6 | STM-1, STM-16 |  | covered |
| D-345 | `for` uses a half-open ascending unit-step range | SP6 | STM-13, STM-14 |  | covered |
| D-346 | `continue` in a `while` rechecks the condition | SP6 | STM-15 |  | covered |
| D-347 | Infinite loops are written `while true` | SP6 | STM-12, RTF-6 |  | covered |
| D-348 | `require c else E | SP6 | STM-19 |  | covered |
| D-349 | No chained assignment, increment/decrement operators or assignment in conditions | SP6 | STM-6 |  | covered |
| D-350 | An explicit local initializer is not preceded by a default | SP6 | STM-5 |  | covered |
| D-351 | Unreachable statements are permitted and still checked | SP6 | STM-22 |  | covered |
| D-352 | Ordinary functions may access globals, call platform APIs and open transactions | SP7 | FUN-3, FUN-22, TXN-1 |  | covered |
| D-353 | All arguments are evaluated left to right and reference/slice regions established and bounds-checked before the callee starts | SP7 | FUN-11 |  | covered |
| D-354 | Forwarding: `ref` to `ref` | SP7 | FUN-15 |  | covered |
| D-355 | References and views end with their call on Ok or Err | SP7 | FUN-16 |  | covered |
| D-356 | Storage identity survives reference passing: a write through `inout` to persistent storage is a persistent write | SP7 | FUN-23, OUT-20 |  | covered |
| D-357 | Compilers preserve observable aliasing effects | SP7 | FUN-14 |  | covered |
| D-358 | Physical copies may be removed only when behavior is unchanged | SP7 | FUN-17 |  | covered |
| D-359 | Inside the callee a view is indexed from 0 and its `.length` is the region length | SP7 | FUN-21 |  | covered |
| D-360 | An outcome match has exactly one success arm, zero or more specific error arms and one mandatory final catch-all (`Err(name)` or `Err(_)`) | SP8 | OUT-12 |  | covered |
| D-361 | Pattern vocabulary: `Ok(name)`, `Ok(_)`, `Ok()`, `Err(Set.Member)`, `Err(name)`, `Err(_)` | SP8 | OUT-11 |  | covered |
| D-362 | Success payload bindings are independent read-only arm-local copies | SP8 | OUT-13 |  | covered |
| D-363 | `Ok` and `Err` are restricted syntax for returns, `abort` and patterns, not general constructors | SP8 | OUT-6 |  | covered |
| D-364 | `attempt` propagates the error unchanged regardless of the enclosing payload type and never catches traps | SP8 | OUT-10 |  | covered |
| D-365 | Application errors carry identity only (no strings or payloads) | SP8 | OUT-16, OUT-18 |  | covered |
| D-366 | Published error codes must not change meaning or be reused after removal | SP8 | OUT-17, PLT-11 |  | covered |
| D-367 | Platform errors use the reserved `CardError` namespace, which applications cannot impersonate | SP8 | OUT-18, OUT-19, PLT-27 |  | covered |
| D-368 | Returning or propagating `Err` is not a rollback request | SP8 | OUT-20, TXN-9 |  | covered |
| D-369 | Persistent defaults apply once, when persistent state is first created | SP9 | STA-3 |  | covered |
| D-370 | Setup writing persistent values is distinct from volatile setup | SP9 | STA-5, PLT-18 |  | covered |
| D-371 | A persistent assignment is atomic: after interruption the destination holds its complete old or complete new value | SP9 | STA-11, STA-12, PLT-12 |  | covered |
| D-372 | Two persistent assignments are not collectively atomic without a transaction | SP9 | STA-12, TXN-5 |  | covered |
| D-373 | Whole-structure and whole-array assignment, including fill, is atomic for the whole destination | SP9 | STA-11, PLT-12 |  | covered |
| D-374 | Global means application-wide | SP9 | STA-1 |  | covered |
| D-375 | Reaching the closing brace commits | SP10 | TXN-3, PLT-13 |  | covered |
| D-376 | Reads within a transaction see earlier writes, including through references and called functions | SP10 | TXN-2 |  | covered |
| D-377 | Only persistent state participates | SP10 | TXN-4 |  | covered |
| D-378 | A callee's Err is not an abort request | SP10 | TXN-9 |  | covered |
| D-379 | abort stops the body, rolls back pending persistent writes and returns the error unchanged from the enclosing function or command | SP10 | TXN-8 |  | covered |
| D-380 | The abort operand is a named error member or an in-scope error binding | SP10 | TXN-7 |  | covered |
| D-381 | break/continue targeting a loop entirely inside the transaction is valid | SP10 | TXN-6 |  | covered |
| D-382 | A trap inside a transaction rolls back its pending persistent writes and aborts the command | SP10 | TXN-11, PLT-13 |  | covered |
| D-383 | A command is not implicitly a transaction | SP10 | TXN-5 |  | covered |
| D-384 | `request.length` is the number of bytes received | SP11 | HEP-5, HEP-6, PLT-6 |  | covered |
| D-385 | The platform supplies separate, non-overlapping request and response regions valid only for the invocation | SP11 | HEP-7, PLT-6 |  | covered |
| D-386 | The application must write every response byte it includes in the count | SP11 | HEP-8 |  | covered |
| D-387 | Response data is transmitted only after successful completion and count validation | SP11 | HEP-9, PLT-8 |  | covered |
| D-388 | Ok means a response was produced, not that the business operation succeeded | SP11 | HEP-11 |  | covered |
| D-389 | No automatic serialization of language values and no automatic dispatch of operation identifiers | SP11 | HEP-15 |  | covered |
| D-390 | The returned u32 is a byte count, not a status word | SP11 | HEP-9, HEP-12, PLT-9 |  | covered |
| D-391 | A reset or power loss may prevent any response | SP11 | HEP-12, PLT-10 |  | covered |
| D-392 | A trap ends only the current command | SP11 | HEP-14, RTF-3 |  | covered |
| D-393 | Response transmission never happens inside a transaction | SP11 | HEP-10, PLT-8 |  | covered |
| D-394 | A trap aborts the current command and cannot be caught by application `match` or `attempt` | SP12 | RTF-1 |  | covered |
| D-395 | Session state may be partially updated when a command traps | SP12 | RTF-2 |  | covered |
| D-396 | Defined trap cases: arithmetic failures, out-of-bounds access, invalid shift counts, stack or execution-budget exhaustion, attempted nested transactions, invalid VM instructions or state | SP12 | RTF-4, PLT-28 |  | covered |
| D-397 | A security reset clears volatile state across all applications and is never returned as a `CardError` | SP12 | RTF-9, PLT-19 |  | covered |
| D-398 | Failures may terminate execution without an outcome while the persistent atomicity guarantees still hold | SP12 | RTF-10 |  | covered |
| D-399 | An ordinary trap does not trigger a lifecycle reset | SP12 | RTF-3 |  | covered |
| D-423 | BOM ignored; LF, CR and CRLF are line breaks | SP1 | LEX-4, LEX-5 | OI-23 | covered |
| D-424 | Longest-match tokens; numeric-run rule; no identifier length limit | SP1 | LEX-10, LEX-16, LEX-18 | OI-24 | covered |
| D-425 | Primitive type names are predeclared | SP2 | NAM-14 | OI-25 | covered |
| D-426 | File-list duplicates are a build error; empty list allowed | SP2 | NAM-3 | OI-26 | covered |
| D-427 | Storage representation is not language-visible | SP3 | TYP-9, EXP-38, PLT-1, PLT-16 | OI-27 | covered |
| D-428 | Error-member codes are integer literals | SP8 | CEX-6, OUT-16 | OI-28 | covered |
| D-429 | Constant slice endpoints checked at compile time | SP4 | CEX-10, FUN-20 | OI-29 | covered |
| D-430 | A structure constructor directly in an if/while condition, for range bound or match scrutinee must be parenthesized | SP5 | EXP-6 | OI-30 | covered |
| D-431 | Arithmetic failure classes: above maximum is Overflow | SP5 | EXP-23, EXP-24, EXP-25, EXP-29 | OI-31 | covered |
| D-432 | Add truncate<T>(x) and value-based byte-order intrinsics encode_be/encode_le and decode_be/decode_le<T> | SP5 | EXP-34, EXP-36, EXP-37, LEX-15, NAM-14, CEX-5 | OI-32 | covered |
| D-433 | Only `attempt call | SP6 | STM-2 | OI-33 | covered |
| D-434 | No standalone block statements in Draft 0.1 | SP6 | STM-3 | OI-34 | covered |
| D-435 | for index or pattern binding may be passed as ref | SP7 | FUN-9, FUN-10 | OI-35 | covered |
| D-436 | An error set must declare at least one member | SP8 | OUT-15 | OI-36 | covered |
| D-437 | Application code may name `CardError` members only in `Err` patterns | SP8 | OUT-4, OUT-19, STM-19, TXN-7 | OI-37 | covered |
| D-422 | Lifecycle handlers: not callable from application code | SP9 | STA-7, STA-8, STA-9, STA-10, NAM-14, LEX-15 | OI-22 | covered |
| D-438 | Placeholder lifecycle handlers on_install() and on_power_on(), no parameters and no payload, until the platform catalog exists | SP9 | STA-6, NAM-14, LEX-15, STA-7, PLT-18 | OI-38 | covered |
| D-439 | Exceeding transaction capacity at runtime is trap(TXN-CAPACITY) | SP10 | TXN-16, RTF-4, PLT-15, PLT-28 | OI-39 | covered |
| D-440 | A call to a platform API marked not-in-transactions, lexically inside a transaction or reachable from one through the call graph, is a compilation error (CE-TXN-4) | SP10 | TXN-17, PLT-24 | OI-40 | covered |
| D-441 | Response region contents unspecified; no foreign data | SP11 | HEP-8, PLT-7 | OI-41 | covered |
| D-442 | Maximum stack need computed; excess rejected at build or load | SP12 | RTF-7, PLT-28, PLT-29 | OI-42 | covered |
| D-443 | Catalog entry requirements; test-only catalog for conformance | SP13 | PLT-25, PLT-26 | OI-43 | covered |
| D-444 | EXP-6 encoded in Annex A with a condition-expression nonterminal | SP14 | EXP-6 | OI-44 | covered |
| D-445 | attempt and require inside a transaction abort it on their error path | Draft 0.2 | TXN-18, TXN-6, STM-19, OUT-10, EXP-51 | OI-45 | covered |
| D-446 | The line between intrinsics and platform APIs | WP1 | EXP-52, PLT-30 | OI-46 | covered |
| D-447 | Moving array data | WP1 | FUN-24, FUN-18, STM-7 | OI-47 | covered |
| D-448 | Comparing arrays | WP1 | EXP-53, EXP-54, LEX-15, NAM-14 | OI-48 | covered |
| D-449 | Wiping secrets | WP1 | STM-23, EXP-22, LEX-13, PLT-34 | OI-49 | covered |
| D-450 | Security expectations for platforms | WP1 | PLT-31 to PLT-34, PLT-32, PLT-33 | OI-50 | covered |
| D-451 | Capacity model withdrawn; runtime-sized atomic overflow traps | WP1 | STA-13, FUN-24, STM-23, RTF-4 | OI-51 | covered |
| D-452 | Derived secrets are application data | WP4 | PLT-33 | OI-52 | covered |

## D.3 Rules → conformance tests

<!-- D.3 generated by tools/generators/coverage.py; do not edit by hand -->

Every rule has at least one conformance test, or a stated reason why no conformance test can check it.

| Value | Meaning |
|---|---|
| `cited` | The tests listed cite the rule in their `rule:` header |
| `exercised` | No test cites the rule, but the tests listed clearly depend on it |
| `not testable` | No conformance test can check the rule, for the reason given |

**Totals:** 298 rules: 217 cited, 48 exercised, 33 not testable.

| Rule | Coverage | Tests or reason |
|---|---|---|
| LEX-1 | exercised | lex-006-two-files, nam-002-multi-file-any-order |
| LEX-2 | cited | lex-113-invalid-utf8 |
| LEX-3 | cited | lex-002-comments, lex-101-non-ascii-identifier |
| LEX-4 | exercised | lex-007-byte-order-mark |
| LEX-5 | cited | lex-008-line-breaks |
| LEX-6 | cited | lex-114-preprocessor-directive |
| LEX-7 | cited | lex-002-comments, lex-006-two-files, lex-008-line-breaks |
| LEX-8 | cited | lex-002-comments, lex-102-unterminated-block-comment, lex-103-nested-block-comment, lex-112-comment-across-files |
| LEX-9 | cited | lex-002-comments, lex-103-nested-block-comment |
| LEX-10 | cited | lex-005-longest-match |
| LEX-11 | cited | lex-006-two-files, lex-112-comment-across-files |
| LEX-12 | cited | lex-001-identifiers, lex-101-non-ascii-identifier |
| LEX-13 | cited | lex-110-keyword-as-identifier, lex-116-wipe-is-keyword |
| LEX-14 | cited | lex-001-identifiers, lex-111-underscore-as-name |
| LEX-15 | exercised | nam-116-redeclare-intrinsic, nam-117-redeclare-card, sta-108-constant-named-like-handler |
| LEX-16 | cited | lex-009-long-identifier |
| LEX-17 | cited | lex-003-integer-literals, lex-104-literal-double-underscore, lex-105-literal-trailing-underscore, lex-106-literal-underscore-after-prefix, lex-107-empty-hex-prefix, lex-108-binary-digit-out-of-base, lex-109-uppercase-prefix |
| LEX-18 | cited | lex-104-literal-double-underscore, lex-105-literal-trailing-underscore, lex-106-literal-underscore-after-prefix, lex-107-empty-hex-prefix, lex-108-binary-digit-out-of-base, lex-109-uppercase-prefix |
| LEX-19 | cited | lex-003-integer-literals |
| LEX-20 | exercised | exp-003-negative-minimum, exp-103-negative-literal-unsigned |
| LEX-21 | cited | lex-004-boolean-literals |
| LEX-22 | cited | lex-005-longest-match |
| LEX-23 | cited | lex-115-missing-semicolon |
| LEX-24 | cited | lex-114-preprocessor-directive |
| NAM-1 | exercised | nam-002-multi-file-any-order, lex-006-two-files |
| NAM-2 | cited | nam-006-empty-file |
| NAM-3 | not testable | A build-configuration rule, outside the language; it has no CE class |
| NAM-4 | cited | nam-002-multi-file-any-order |
| NAM-5 | not testable | Isolation between applications; each conformance test is a single application |
| NAM-6 | exercised | sta-001-global-declarations, nam-104-global-var |
| NAM-7 | cited | nam-108-nested-function |
| NAM-8 | cited | nam-122-application-wrapper |
| NAM-9 | cited | nam-104-global-var, nam-105-combined-qualifiers |
| NAM-10 | cited | nam-106-local-storage-keyword, nam-107-local-const |
| NAM-11 | cited | nam-001-shared-scope-forward-use, nam-002-multi-file-any-order, nam-101-duplicate-across-kinds, nam-102-duplicate-across-files |
| NAM-12 | cited | nam-103-overloading |
| NAM-13 | cited | nam-001-shared-scope-forward-use, nam-002-multi-file-any-order |
| NAM-14 | cited | nam-116-redeclare-intrinsic, nam-117-redeclare-card, nam-118-redeclare-primitive, nam-121-parameter-shadows-primitive, plt-003-base-types, plt-107-redeclare-base-type, plt-110-redeclare-key-type, sta-108-constant-named-like-handler |
| NAM-15 | cited | nam-003-member-scopes, nam-005-qualified-members, nam-113-duplicate-field |
| NAM-16 | cited | nam-005-qualified-members, nam-114-bare-variant, nam-115-unknown-member |
| NAM-17 | cited | nam-003-member-scopes |
| NAM-18 | cited | nam-120-unknown-platform-path, plt-001-platform-call, plt-004-key-apis, plt-006-crypto-apis, plt-007-cbor-apis, plt-101-unknown-platform-path |
| NAM-19 | cited | nam-004-sibling-scopes, nam-112-use-outside-scope |
| NAM-20 | cited | nam-111-self-reference |
| NAM-21 | cited | nam-004-sibling-scopes, nam-109-parameter-shadows-global, nam-110-local-shadows-local, nam-119-same-scope-duplicate, nam-121-parameter-shadows-primitive |
| NAM-22 | cited | nam-111-self-reference, nam-112-use-outside-scope, nam-114-bare-variant |
| TYP-1 | exercised | typ-001-primitive-types, typ-003-nested-structures, typ-004-arrays |
| TYP-2 | exercised | typ-006-unsized-parameters, typ-109-unsized-local |
| TYP-3 | cited | typ-113-not-a-type |
| TYP-4 | cited | typ-007-same-array-type |
| TYP-5 | exercised | exp-120-bool-from-integer, exp-121-enum-from-integer, exp-123-typed-constant-no-widening |
| TYP-6 | cited | typ-001-primitive-types |
| TYP-7 | cited | typ-001-primitive-types |
| TYP-8 | cited | typ-115-no-64-bit |
| TYP-9 | not testable | Representation is not observable by a conforming program |
| TYP-10 | cited | typ-002-enums, typ-101-empty-enum |
| TYP-11 | cited | typ-002-enums |
| TYP-12 | exercised | out-107-err-enum-variant |
| TYP-13 | cited | typ-003-nested-structures, typ-102-empty-struct |
| TYP-14 | cited | typ-003-nested-structures, typ-110-unsized-field |
| TYP-15 | cited | typ-103-direct-recursion, typ-104-indirect-recursion, typ-105-recursion-through-array |
| TYP-16 | cited | typ-003-nested-structures |
| TYP-17 | cited | typ-004-arrays |
| TYP-18 | cited | typ-004-arrays, typ-106-array-of-arrays |
| TYP-19 | cited | typ-005-constant-length, typ-107-zero-length, typ-108-signed-length |
| TYP-20 | cited | typ-114-byte-alias |
| TYP-21 | cited | typ-006-unsized-parameters, typ-109-unsized-local, typ-110-unsized-field, typ-111-unsized-by-value-parameter, typ-112-unsized-return |
| TYP-22 | exercised | stm-001-local-defaults-and-initializers, run-008-state-lifecycle |
| TYP-23 | not testable | Target storage limits are platform-defined; the suite has no target profile |
| CEX-1 | cited | cex-001-basic-constants, cex-101-missing-initializer |
| CEX-2 | exercised | cex-001-basic-constants, cex-103-function-call |
| CEX-3 | cited | cex-001-basic-constants, cex-003-convert-typed-constant, cex-004-constant-aggregates, cex-006-enum-constants |
| CEX-4 | cited | cex-005-length-of-session-array |
| CEX-5 | cited | cex-102-reads-session, cex-103-function-call, cex-104-wrapping-intrinsic |
| CEX-6 | cited | cex-102-reads-session, cex-103-function-call, cex-104-wrapping-intrinsic |
| CEX-7 | cited | cex-007-short-circuit-skip, cex-008-nested-constant-guard, cex-009-runtime-division, cex-107-runtime-guard, cex-108-unreachable-if-false, cex-109-after-return, cex-114-local-constant-overflow |
| CEX-8 | cited | cex-105-overflow |
| CEX-9 | cited | cex-105-overflow, cex-106-division-by-zero, cex-110-constant-array-bounds, cex-114-local-constant-overflow, cex-115-shift-count, cex-116-signed-minimum-division |
| CEX-10 | cited | cex-111-mutable-array-constant-index |
| CEX-11 | cited | cex-007-short-circuit-skip |
| CEX-12 | cited | cex-002-forward-dependency |
| CEX-13 | cited | cex-112-cycle, cex-113-cycle-through-length |
| CEX-14 | exercised | exp-124-nested-convert |
| EXP-1 | cited | exp-005-unary-with-binary |
| EXP-2 | cited | exp-004-same-operator-chains, exp-005-unary-with-binary, exp-105-mixed-arithmetic, exp-106-mixed-plus-minus, exp-107-mixed-bitwise-comparison, exp-108-mixed-boolean |
| EXP-3 | cited | exp-004-same-operator-chains |
| EXP-4 | cited | exp-109-comparison-chain, exp-110-equality-chain |
| EXP-5 | cited | exp-107-mixed-bitwise-comparison, exp-108-mixed-boolean |
| EXP-6 | cited | exp-018-parenthesized-constructor-condition, exp-135-unparenthesized-constructor-condition |
| EXP-7 | cited | exp-001-literal-contexts, exp-102-literal-out-of-range, exp-120-bool-from-integer, exp-121-enum-from-integer |
| EXP-8 | cited | exp-003-negative-minimum, exp-103-negative-literal-unsigned |
| EXP-9 | exercised | lex-004-boolean-literals, exp-007-equality-bool-enum |
| EXP-10 | cited | exp-001-literal-contexts |
| EXP-11 | cited | exp-002-typed-operand-either-side, exp-104-no-literal-context, exp-142-checked-no-context |
| EXP-12 | cited | exp-101-operand-type-mismatch, exp-122-distinct-structures, exp-123-typed-constant-no-widening |
| EXP-13 | exercised | exp-101-operand-type-mismatch, run-001-integer-traps |
| EXP-14 | cited | exp-117-ordering-bool |
| EXP-15 | cited | exp-007-equality-bool-enum, exp-118-structure-equality, exp-119-array-equality |
| EXP-16 | cited | exp-143-boolean-operator-integer |
| EXP-17 | cited | exp-008-shifts-and-bitwise, exp-116-bitwise-signed |
| EXP-18 | cited | exp-008-shifts-and-bitwise, exp-115-signed-shift-count |
| EXP-19 | cited | exp-003-negative-minimum, exp-103-negative-literal-unsigned, exp-141-unary-minus-unsigned |
| EXP-20 | exercised | run-004-assignment-order, run-017-evaluation-and-copies |
| EXP-21 | cited | exp-015-short-circuit-index, run-003-short-circuit-and-bounds |
| EXP-22 | not testable | Permits only transformations that are unobservable by definition |
| EXP-23 | cited | run-001-integer-traps |
| EXP-24 | cited | run-001-integer-traps |
| EXP-25 | cited | run-001-integer-traps |
| EXP-26 | cited | run-001-integer-traps |
| EXP-27 | cited | run-017-evaluation-and-copies |
| EXP-28 | exercised | exp-007-equality-bool-enum, exp-117-ordering-bool |
| EXP-29 | cited | exp-014-checked-in-match, exp-142-checked-no-context, run-002-checked-and-conversions |
| EXP-30 | cited | exp-013-wrapping, run-001-integer-traps |
| EXP-31 | cited | exp-006-guaranteed-conversions, exp-112-convert-unknown-source, exp-136-truncate-unknown-source |
| EXP-32 | cited | exp-006-guaranteed-conversions, exp-111-convert-narrowing |
| EXP-33 | cited | exp-017-checked-convert, run-002-checked-and-conversions |
| EXP-34 | cited | exp-016-truncate-and-bytes, exp-136-truncate-unknown-source, run-002-checked-and-conversions |
| EXP-35 | cited | exp-144-convert-to-bool |
| EXP-36 | cited | exp-016-truncate-and-bytes, exp-137-encode-unsupported-type, run-002-checked-and-conversions |
| EXP-37 | cited | exp-016-truncate-and-bytes, run-002-checked-and-conversions |
| EXP-38 | exercised | exp-016-truncate-and-bytes |
| EXP-39 | cited | exp-009-index-types, exp-113-signed-index, exp-114-bool-index, run-003-short-circuit-and-bounds |
| EXP-40 | cited | exp-010-length-of-field, exp-140-length-on-integer |
| EXP-41 | cited | exp-134-unknown-field, exp-140-length-on-integer |
| EXP-42 | exercised | fun-007-slices-and-views, fun-114-slice-in-initializer |
| EXP-43 | cited | exp-128-list-too-short, exp-129-list-too-long |
| EXP-44 | cited | exp-011-fill-forms, exp-130-fill-without-context |
| EXP-45 | cited | exp-012-constructor-order, exp-131-constructor-missing-field, exp-132-constructor-unknown-field, exp-133-constructor-duplicate-field |
| EXP-46 | cited | run-017-evaluation-and-copies |
| EXP-47 | cited | exp-138-argument-count, exp-139-call-non-function, hep-108-call-command, plt-102-wrong-argument-type, plt-103-wrong-argument-count, plt-109-key-spec-wrong-type, plt-111-wrong-algorithm-family, plt-113-cbor-major-as-integer |
| EXP-48 | cited | exp-014-checked-in-match, exp-127-outcome-as-value |
| EXP-49 | cited | exp-124-nested-convert, exp-125-intrinsic-in-argument, exp-126-attempt-in-argument |
| EXP-50 | cited | run-017-evaluation-and-copies |
| EXP-51 | exercised | out-004-attempt-forms, fun-009-constant-and-bindings-by-ref, run-017-evaluation-and-copies |
| EXP-52 | exercised | exp-013-wrapping, exp-017-checked-convert, exp-019-equal-and-compare |
| EXP-53 | cited | exp-019-equal-and-compare, exp-145-equal-element-types, exp-147-equal-by-value, fun-012-views-equal-and-wipe, run-018-array-operations |
| EXP-54 | cited | exp-019-equal-and-compare, exp-146-compare-bool, fun-012-views-equal-and-wipe, run-018-array-operations |
| STM-1 | exercised | stm-004-if-chain, stm-126-standalone-block |
| STM-2 | cited | stm-125-expression-statement |
| STM-3 | cited | stm-126-standalone-block |
| STM-4 | cited | stm-001-local-defaults-and-initializers |
| STM-5 | cited | run-005-loops-and-locals, stm-001-local-defaults-and-initializers |
| STM-6 | cited | stm-101-chained-assignment, stm-102-assignment-in-condition, stm-103-compound-assignment, stm-104-increment |
| STM-7 | cited | stm-002-assignment-places, stm-105-assign-constant, stm-106-assign-constant-element, stm-107-assign-by-value-parameter, stm-108-assign-for-index, stm-109-assign-length, stm-110-assign-match-binding, stm-127-assign-function |
| STM-8 | cited | stm-002-assignment-places, stm-003-whole-array-assignment |
| STM-9 | cited | run-004-assignment-order |
| STM-10 | cited | run-004-assignment-order |
| STM-11 | cited | stm-004-if-chain, stm-124-non-bool-condition |
| STM-12 | cited | stm-005-while-break-continue |
| STM-13 | cited | stm-006-for-ranges, stm-121-for-bool-index, stm-122-for-endpoint-out-of-range |
| STM-14 | cited | run-005-loops-and-locals, stm-006-for-ranges, stm-108-assign-for-index |
| STM-15 | cited | run-005-loops-and-locals, stm-005-while-break-continue, stm-111-break-outside-loop, stm-112-continue-outside-loop |
| STM-16 | cited | stm-007-enum-match, stm-012-match-arms-may-complete, stm-113-enum-match-missing, stm-114-enum-match-duplicate, stm-115-enum-match-foreign, stm-116-enum-match-wildcard |
| STM-17 | cited | stm-117-match-integer |
| STM-18 | exercised | stm-010-statements-after-return, out-005-forwarding |
| STM-19 | cited | out-109-require-card-error, out-123-error-binding-require, stm-008-require, stm-123-require-integer-operand |
| STM-20 | cited | stm-004-if-chain, stm-007-enum-match, stm-009-while-true-no-return, stm-011-while-true-with-return-inside, stm-012-match-arms-may-complete, stm-119-if-without-else-return, stm-120-while-true-with-break |
| STM-21 | cited | stm-009-while-true-no-return, stm-118-missing-return, stm-119-if-without-else-return, stm-120-while-true-with-break |
| STM-22 | cited | stm-010-statements-after-return |
| STM-23 | cited | fun-012-views-equal-and-wipe, run-018-array-operations, stm-013-wipe, stm-128-wipe-constant |
| FUN-1 | exercised | fun-001-forward-call-across-files, fun-010-no-payload-function |
| FUN-2 | cited | fun-002-structure-return, fun-010-no-payload-function |
| FUN-3 | cited | fun-001-forward-call-across-files |
| FUN-4 | cited | fun-001-forward-call-across-files |
| FUN-5 | cited | fun-101-direct-recursion, fun-102-indirect-recursion, fun-103-recursion-across-files |
| FUN-6 | cited | fun-003-ref-and-inout-field |
| FUN-7 | cited | fun-104-missing-ref-mode, fun-105-missing-inout-mode, fun-106-ref-for-by-value, fun-107-inout-for-ref, plt-104-missing-ref-mode, plt-108-key-import-missing-ref, plt-112-crypto-missing-inout |
| FUN-8 | cited | fun-117-slice-to-fixed-parameter, fun-118-element-type-mismatch |
| FUN-9 | cited | fun-003-ref-and-inout-field, fun-009-constant-and-bindings-by-ref, fun-108-temporary-reference, fun-109-reference-to-literal, fun-110-reference-to-arithmetic |
| FUN-10 | cited | fun-111-constant-as-inout, fun-113-by-value-as-inout |
| FUN-11 | cited | run-017-evaluation-and-copies |
| FUN-12 | cited | fun-004-aliasing, run-006-aliasing-and-slices |
| FUN-13 | cited | fun-004-aliasing, fun-005-overlapping-references |
| FUN-14 | cited | fun-004-aliasing, run-006-aliasing-and-slices |
| FUN-15 | cited | fun-006-forwarding, fun-112-ref-forwarded-as-inout |
| FUN-16 | cited | fun-122-reference-variable |
| FUN-17 | cited | run-017-evaluation-and-copies |
| FUN-18 | cited | fun-007-slices-and-views, fun-008-narrowing-views, fun-114-slice-in-initializer, fun-115-slice-in-assignment, fun-116-slice-by-value |
| FUN-19 | cited | fun-119-signed-slice-endpoint |
| FUN-20 | cited | fun-007-slices-and-views, fun-120-constant-slice-out-of-range, fun-121-constant-slice-reversed, run-006-aliasing-and-slices |
| FUN-21 | cited | fun-007-slices-and-views, fun-008-narrowing-views |
| FUN-22 | exercised | sta-002-setup-helper, txn-004-callee-writes |
| FUN-23 | cited | run-017-evaluation-and-copies |
| FUN-24 | cited | fun-011-slice-assignment, fun-123-slice-assignment-length, fun-124-slice-assignment-into-ref, fun-125-slice-assignment-element-type, run-018-array-operations, run-021-cbor |
| OUT-1 | exercised | out-001-match-ok-err, out-002-no-payload-match |
| OUT-2 | cited | out-124-outcome-in-initializer |
| OUT-3 | cited | out-103-ok-value-in-no-payload, out-104-ok-empty-in-payload |
| OUT-4 | cited | out-106-err-integer, out-107-err-enum-variant, out-108-originate-card-error |
| OUT-5 | cited | out-005-forwarding, out-105-forward-mismatch |
| OUT-6 | cited | out-131-ok-as-value |
| OUT-7 | cited | out-101-bare-call-statement, out-102-bare-checked-statement |
| OUT-8 | cited | out-008-no-error-set, out-110-attempt-non-call |
| OUT-9 | cited | out-004-attempt-forms, out-111-attempt-statement-with-payload, out-112-attempt-expression-no-payload |
| OUT-10 | cited | out-004-attempt-forms, run-007-outcomes |
| OUT-11 | cited | out-001-match-ok-err, out-002-no-payload-match, out-003-ignore-payload, out-009-match-card-error, out-117-ok-empty-against-payload, out-118-nested-pattern |
| OUT-12 | cited | out-001-match-ok-err, out-002-no-payload-match, out-113-missing-catch-all, out-114-missing-success-arm, out-115-specific-after-catch-all, out-116-duplicate-specific-arm, out-119-two-success-arms |
| OUT-13 | cited | out-001-match-ok-err |
| OUT-14 | cited | out-006-unused-error-binding, out-120-compare-error-binding, out-121-store-error-binding, out-122-pass-error-binding, out-123-error-binding-require |
| OUT-15 | cited | out-007-error-set, out-008-no-error-set, out-125-two-error-sets, out-129-empty-error-set |
| OUT-16 | cited | out-007-error-set, out-126-zero-code, out-127-duplicate-code, out-128-computed-code, out-130-code-out-of-range |
| OUT-17 | not testable | An obligation across versions of an application, not on one program |
| OUT-18 | cited | run-007-outcomes |
| OUT-19 | cited | out-009-match-card-error, out-108-originate-card-error, out-109-require-card-error, txn-110-abort-card-error |
| OUT-20 | cited | run-007-outcomes, run-011-counter-application, run-012-wallet-application |
| STA-1 | cited | sta-001-global-declarations |
| STA-2 | cited | sta-001-global-declarations, sta-101-persistent-initializer, sta-102-session-fill-initializer, sta-103-persistent-zero-initializer, sta-104-session-false-initializer |
| STA-3 | cited | run-008-state-lifecycle |
| STA-4 | cited | run-008-state-lifecycle, run-012-wallet-application, sta-002-setup-helper |
| STA-5 | cited | sta-002-setup-helper |
| STA-6 | cited | run-008-state-lifecycle, run-016-signer-application, sta-004-lifecycle-handlers |
| STA-7 | cited | sta-004-lifecycle-handlers, sta-105-handler-with-payload, sta-106-handler-with-parameter |
| STA-8 | cited | sta-108-constant-named-like-handler |
| STA-9 | cited | sta-107-call-handler |
| STA-10 | cited | sta-004-lifecycle-handlers |
| STA-11 | cited | sta-003-persistent-assignments |
| STA-12 | cited | sta-003-persistent-assignments |
| STA-13 | not testable | Rejection depends on a target's atomic-update limit, which is platform-defined |
| STA-14 | exercised | run-009-transactions, run-008-state-lifecycle |
| TXN-1 | cited | txn-001-basic, txn-004-callee-writes |
| TXN-2 | cited | run-009-transactions, txn-002-read-your-writes, txn-004-callee-writes |
| TXN-3 | cited | hep-005-counter-application, run-009-transactions, run-011-counter-application, txn-001-basic, txn-003-empty |
| TXN-4 | exercised | run-009-transactions |
| TXN-5 | cited | run-017-evaluation-and-copies |
| TXN-6 | cited | txn-008-loop-inside, txn-009-validate-then-transact, txn-011-helper-with-attempt, txn-101-return-inside, txn-102-forwarding-return-inside, txn-105-break-to-outer-loop, txn-106-continue-to-outer-loop, txn-107-return-in-match-arm |
| TXN-7 | cited | txn-006-abort-binding, txn-007-abort-member, txn-108-abort-outside, txn-109-abort-in-helper, txn-110-abort-card-error, txn-111-abort-integer, txn-112-bare-abort, txn-113-abort-ok |
| TXN-8 | cited | run-009-transactions, run-012-wallet-application, txn-006-abort-binding |
| TXN-9 | cited | txn-005-err-handled-locally |
| TXN-10 | cited | txn-114-lexical-nesting, txn-115-nesting-through-call, txn-116-nesting-two-step, txn-117-nesting-untaken-path |
| TXN-11 | cited | run-009-transactions, run-019-keys |
| TXN-12 | not testable | The scenario format cannot inject a contained commit failure |
| TXN-13 | cited | run-014-recovery-after-interrupt |
| TXN-14 | not testable | Not observable: commands never interleave, so no other context runs during a transaction |
| TXN-15 | cited | txn-010-ends-with-abort |
| TXN-16 | not testable | Transaction capacity is platform-defined; the suite has no target profile |
| TXN-17 | cited | plt-002-immediate-api-in-transaction, plt-005-key-in-transaction, plt-105-forbidden-in-transaction, plt-106-forbidden-through-helper |
| TXN-18 | cited | run-009-transactions, txn-012-attempt-inside, txn-013-require-inside |
| HEP-1 | cited | hep-001-minimal, hep-002-any-names, hep-005-counter-application, hep-101-no-command, hep-102-two-commands |
| HEP-2 | cited | hep-001-minimal, hep-002-any-names, hep-103-wrong-return-type, hep-104-no-return-type, hep-105-inout-request, hep-106-fixed-size-request, hep-107-extra-parameter |
| HEP-3 | cited | hep-108-call-command |
| HEP-4 | exercised | hep-003-dispatch-and-encode, run-007-outcomes |
| HEP-5 | exercised | hep-001-minimal, run-010-response-contract |
| HEP-6 | exercised | run-010-response-contract |
| HEP-7 | cited | run-017-evaluation-and-copies |
| HEP-8 | not testable | The initial response contents are deliberately unspecified, so no expectation is portable |
| HEP-9 | cited | hep-003-dispatch-and-encode, hep-005-counter-application, run-010-response-contract |
| HEP-10 | not testable | Transmission timing relative to commit is not observable through the scenario format |
| HEP-11 | cited | hep-004-protocol-status-in-payload |
| HEP-12 | exercised | run-007-outcomes, run-001-integer-traps |
| HEP-13 | not testable | Non-interleaving is a property of the platform; the harness runs commands one at a time by construction |
| HEP-14 | exercised | run-001-integer-traps |
| HEP-15 | cited | hep-003-dispatch-and-encode, hep-005-counter-application, run-011-counter-application, run-012-wallet-application, run-016-signer-application |
| HEP-16 | exercised | every test with kind: fragment, for example exp-001-literal-contexts |
| RTF-1 | exercised | run-001-integer-traps, run-003-short-circuit-and-bounds |
| RTF-2 | cited | run-008-state-lifecycle |
| RTF-3 | cited | run-013-execution-budget |
| RTF-4 | cited | run-001-integer-traps |
| RTF-5 | exercised | every runtime test: each expects one trap kind at one step |
| RTF-6 | cited | run-013-execution-budget |
| RTF-7 | not testable | Stack limits are per target profile and platform-defined |
| RTF-8 | not testable | A rule about how limits are enforced; the suite has no target profile |
| RTF-9 | cited | run-008-state-lifecycle, run-012-wallet-application |
| RTF-10 | cited | run-014-recovery-after-interrupt |
| RTF-11 | exercised | run-007-outcomes, run-001-integer-traps |
| RTF-12 | exercised | run-009-transactions, run-008-state-lifecycle |
| PLT-1 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-2 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-3 | exercised | hep-003-dispatch-and-encode |
| PLT-4 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-5 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-6 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-7 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-8 | exercised | run-010-response-contract |
| PLT-9 | exercised | run-007-outcomes |
| PLT-10 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-11 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-12 | exercised | run-014-recovery-after-interrupt |
| PLT-13 | exercised | run-009-transactions, run-014-recovery-after-interrupt |
| PLT-14 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-15 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-16 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-17 | not testable | Informative: future platform work |
| PLT-18 | exercised | sta-004-lifecycle-handlers, run-008-state-lifecycle |
| PLT-19 | exercised | run-008-state-lifecycle |
| PLT-20 | cited | run-015-resource-identifiers, run-016-signer-application |
| PLT-21 | cited | plt-003-base-types |
| PLT-22 | cited | run-015-resource-identifiers, run-016-signer-application, run-019-keys |
| PLT-23 | cited | run-015-resource-identifiers |
| PLT-24 | cited | plt-002-immediate-api-in-transaction, plt-005-key-in-transaction, run-019-keys, run-020-crypto |
| PLT-25 | cited | plt-001-platform-call, plt-004-key-apis, plt-006-crypto-apis, plt-007-cbor-apis, plt-102-wrong-argument-type, plt-103-wrong-argument-count, plt-104-missing-ref-mode, plt-108-key-import-missing-ref, plt-109-key-spec-wrong-type, plt-111-wrong-algorithm-family, plt-112-crypto-missing-inout, plt-113-cbor-major-as-integer, run-020-crypto, run-021-cbor |
| PLT-26 | exercised | plt-001-platform-call and every test that uses the test-only catalog |
| PLT-27 | exercised | run-002-checked-and-conversions, run-015-resource-identifiers |
| PLT-28 | exercised | run-001-integer-traps, run-013-execution-budget |
| PLT-29 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-30 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-31 | not testable | Timing is not observable by a conforming program; checked by platform evaluation |
| PLT-32 | not testable | Side-channel and fault resistance is not observable by a conforming program; checked by platform evaluation |
| PLT-33 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
| PLT-34 | not testable | A platform obligation: it is checked by a platform's own conformance, not by language tests |
