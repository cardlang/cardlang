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
| 02-lexical-structure.md | SP1 | DN §3.0, §3.3 (literal forms), §6.5 (negative minimum) | pending |
| 03-program-structure-and-names.md | SP2 | DN §3.0, §3.6 (scope), §4.1, §4.2, §5.1 | pending |
| 04-types.md | SP3 | DN §3.1, §3.4, §3.9 (defaults), §3.11, §8, §8.2, §9–§9.3 | pending |
| 05-constant-expressions.md | SP4 | DN §3.3, §3.10 | pending |
| 06-expressions.md | SP5 | DN §3.2, §3.3, §3.5, §6.2, §6.5, §8.1, §8.3, §9.3 | pending |
| 07-statements-and-control-flow.md | SP6 | DN §3.6, §3.7 (completion), §8.2 | pending |
| 08-functions-and-references.md | SP7 | DN §3.7, §3.8, §8.4 | pending |
| 09-outcomes-and-errors.md | SP8 | DN §3.2 (`checked_convert`), §3.6 (patterns), §6.1, §6.3 | pending |
| 10-state-and-initialization.md | SP9 | DN §3.9, §5, §5.1, §6.4 (session), §7.1 | pending |
| 11-transactions.md | SP10 | DN §3.6 (boundary), §7.2–§7.4; PN §5 | pending |
| 12-host-entry-point.md | SP11 | DN §4, §6.3 (host reporting) | pending |
| 13-runtime-failures.md | SP12 | DN §6.4, §6.5, §12; PN §3, §5 | pending |
| annex-A-grammar.md | SP1–SP14 | DN §3.0 plus the syntax of every chapter | pending |
| annex-B-platform-contract.md | SP13 | PN §1–§5; DN §4 (transport), §11, §12 | pending |
| annex-C-open-issues.md | all | see each issue | — |

## D.2 Decisions → rules

| D-ID | Topic (short) | Owning SP | Rule IDs | Linked OI | Coverage |
|---|---|---|---|---|---|
| D-001 | Language name: CardLang | SP0 | 01 §1.1 |  | covered |
| D-002 | Custom card-oriented language | SP0 | 01 §1.1 |  | covered |
| D-003 | Global declarations: `persistent`, `session` or `const` | SP2 | — |  | pending |
| D-004 | `persistent` and `session` imply mutable state | SP9 | — |  | pending |
| D-005 | Global `const` declares a compile-time constant | SP4 | — |  | pending |
| D-006 | Local value declarations use `var` only | SP6 | — |  | pending |
| D-007 | Storage qualifiers inside functions/commands are forbidden | SP2 | — |  | pending |
| D-008 | Explicit persistent state | SP9 | — | OI-16 | pending |
| D-009 | Simple persistent declarations plus an object API for larger data | SP13 | — | OI-17 | pending |
| D-010 | Recoverable errors through explicit results, execution faults through traps | SP8 | — |  | pending |
| D-011 | No general-purpose exceptions initially | SP8 | — |  | pending |
| D-012 | Every function returns a success/error result | SP8 | — | OI-18 | pending |
| D-013 | Explicit outcome handling uses `match` with `Ok` / `Err` | SP8 | — |  | pending |
| D-014 | Automatic error propagation with `attempt` | SP8 | — |  | pending |
| D-015 | Discarded function outcomes | SP8 | — |  | pending |
| D-016 | Stored result values / user-visible `Result<T>` | SP8 | — |  | pending |
| D-017 | `attempt` type | SP8 | — |  | pending |
| D-018 | One application error set with explicit nonzero `u16` codes | SP8 | — | OI-13 | pending |
| D-019 | Application/platform errors and traps have separate reporting categories | SP8 | — |  | pending |
| D-020 | Single application or completely isolated applications | SP2 | — |  | pending |
| D-021 | Multiple source files form one application compilation unit | SP2 | — |  | pending |
| D-022 | Source files contain complete top-level declarations; no application wrapper | SP2 | — |  | pending |
| D-023 | Source extension `.card`; UTF-8 source, ASCII identifiers | SP1 | — | OI-1 | pending |
| D-024 | Mandatory semicolons, braces and named-declaration type annotations | SP1 | — |  | pending |
| D-025 | No-value ordinary function signature | SP7 | — |  | pending |
| D-026 | Function arguments | SP7 | — |  | pending |
| D-027 | Calls inside argument expressions | SP5 | — |  | pending |
| D-028 | Error pattern bindings | SP8 | — |  | pending |
| D-029 | Constant-only calculations outside global constants | SP4 | — | OI-11 | pending |
| D-030 | Function completion analysis | SP6 | — |  | pending |
| D-031 | Recursion, function values/pointers and user-defined generics | SP7 | — |  | pending |
| D-032 | Function prototypes | SP7 | — |  | pending |
| D-033 | Successful function returns | SP7 | — |  | pending |
| D-034 | Reachable function fall-through | SP6 | — |  | pending |
| D-035 | Commands called by application code | SP11 | — |  | pending |
| D-036 | Integer literals | SP1 | — | OI-14 | pending |
| D-037 | No preprocessor/macros/textual includes | SP1 | — |  | pending |
| D-038 | Application declarations and struct fields visible across all source files | SP2 | — |  | pending |
| D-039 | User modules/namespaces/imports/exports/classes/access modifiers | SP2 | — |  | pending |
| D-040 | File order does not control name resolution or initialization order | SP2 | — |  | pending |
| D-041 | Host entry point | SP11 | — | OI-5 | pending |
| D-042 | Application protocol | SP11 | — |  | pending |
| D-043 | Classical smart-card status | SP13 | — | OI-2 | pending |
| D-044 | Platform interface names cannot be redefined | SP2 | — | OI-4 | pending |
| D-045 | One shared top-level naming scope for types and values | SP2 | — |  | pending |
| D-046 | No function overloading or local function/type/error-set definitions | SP2 | — |  | pending |
| D-047 | Fields and error members have owner-specific name scopes | SP2 | — |  | pending |
| D-048 | Local binding visible only after its initializer completes | SP2 | — |  | pending |
| D-049 | Command execution | SP11 | — |  | pending |
| D-050 | Session state at chip power-on | SP9 | — |  | pending |
| D-051 | Ordinary traps preserve application session state | SP12 | — |  | pending |
| D-052 | Runtime-owned resources on ordinary trap | SP13 | — |  | pending |
| D-053 | Session/persistent logical consistency | SP12 | — |  | pending |
| D-054 | Runtime-issued security reset | SP12 | — |  | pending |
| D-055 | Transactions roll back persistent changes only | SP10 | — |  | pending |
| D-056 | Fatal platform failure triggers whole-chip security reset | SP13 | — |  | pending |
| D-057 | Each persistent assignment is atomic | SP9 | — | OI-19 | pending |
| D-058 | Explicit handling of overflow and underflow | SP5 | — |  | pending |
| D-059 | Global/local arrays of supported fixed-size values | SP3 | — |  | pending |
| D-060 | Array type syntax `T[N]` | SP3 | — |  | pending |
| D-061 | Array `.length` | SP5 | — |  | pending |
| D-062 | Array index types | SP5 | — |  | pending |
| D-063 | Array initialization with `fill(value)` or an exact-length element list | SP5 | — |  | pending |
| D-064 | No special `zero` initializer | SP5 | — |  | pending |
| D-065 | Named structures with typed fields | SP3 | — |  | pending |
| D-066 | Empty structures | SP3 | — |  | pending |
| D-067 | Enums | SP3 | — |  | pending |
| D-068 | Enum defaults | SP3 | — |  | pending |
| D-069 | Enum matching | SP6 | — |  | pending |
| D-070 | Structure constructors | SP5 | — |  | pending |
| D-071 | Structure array fields accept `fill(value)` and explicit lists | SP5 | — |  | pending |
| D-072 | Structures may contain other structures | SP3 | — |  | pending |
| D-073 | Nested fields inherit instance storage and mutability | SP3 | — |  | pending |
| D-074 | Direct or indirect recursive containment is forbidden | SP3 | — |  | pending |
| D-075 | Primitive types: `u8`, `u16`, `u32`, `i8`, `i16`, `i32`, `bool` | SP3 | — |  | pending |
| D-076 | Byte arrays as `u8[N]` | SP3 | — | OI-12 | pending |
| D-077 | Zero-length and direct multidimensional arrays | SP3 | — |  | pending |
| D-078 | Whole-array assignment | SP6 | — |  | pending |
| D-079 | fill(expression) | SP5 | — |  | pending |
| D-080 | Indexed assignment order | SP6 | — | OI-9 | pending |
| D-081 | No implicit conversions between integer types | SP5 | — |  | pending |
| D-082 | Arithmetic and comparisons require matching integer types | SP5 | — |  | pending |
| D-083 | Explicit `convert<T>` and `checked_convert<T>` intrinsics | SP5 | — |  | pending |
| D-084 | Contextual integer literal typing; no guessed default type | SP5 | — | OI-14 | pending |
| D-085 | Literal-only array index expressions | SP5 | — |  | pending |
| D-086 | Conversion intrinsics require a known source type | SP5 | — |  | pending |
| D-087 | No widening to avoid intermediate arithmetic failure | SP5 | — |  | pending |
| D-088 | Signed minimum / -1 | SP5 | — |  | pending |
| D-089 | Signed minimum % -1 | SP5 | — |  | pending |
| D-090 | Unary negation | SP5 | — |  | pending |
| D-091 | Checked arithmetic | SP5 | — | OI-13 | pending |
| D-092 | Wrapping arithmetic | SP5 | — |  | pending |
| D-093 | Checked/wrapping arithmetic intrinsics in constants | SP4 | — |  | pending |
| D-094 | Constant expressions | SP4 | — |  | pending |
| D-095 | Guaranteed convert<T> in constant expressions | SP4 | — |  | pending |
| D-096 | checked_convert<T> in constant expressions | SP4 | — |  | pending |
| D-097 | Constant-evaluation boundary algorithm | SP4 | — | OI-11 | pending |
| D-098 | Constant dependencies | SP4 | — |  | pending |
| D-099 | Fixed-array lengths | SP4 | — |  | pending |
| D-100 | No implicit boolean/numeric, array or structure conversions | SP3 | — |  | pending |
| D-101 | No general truncating cast initially | SP5 | — |  | pending |
| D-102 | Mixed binary operators require parentheses; no binary precedence hierarchy | SP5 | — |  | pending |
| D-103 | Same-operator chains evaluate left to right; comparison chains forbidden | SP5 | — |  | pending |
| D-104 | Left-to-right evaluation and short-circuit boolean logic | SP5 | — |  | pending |
| D-105 | Assignment is a statement, not an expression | SP6 | — |  | pending |
| D-106 | Control flow: `if`, `while`, range `for`, `match`, `break`, `continue`, `return` | SP6 | — |  | pending |
| D-107 | Explicit `return Ok(value)` / `return Err(error)`; no implicit success | SP8 | — |  | pending |
| D-108 | Exhaustive result matching; read-only loop and pattern bindings | SP8 | — |  | pending |
| D-109 | No `return`, `break` or `continue` across transaction boundaries | SP10 | — |  | pending |
| D-110 | Explicit recoverable transaction exit: `abort Err(error);` | SP10 | — |  | pending |
| D-111 | `abort` scope | SP10 | — |  | pending |
| D-112 | Parameters: by value, read-only `ref`, mutable `inout` | SP7 | — |  | pending |
| D-113 | Reference modes explicit at declaration and call site | SP7 | — |  | pending |
| D-114 | References are call-scoped; no raw pointers or escaping references | SP7 | — |  | pending |
| D-115 | Reference permissions | SP7 | — |  | pending |
| D-116 | Assignment/value parameters/value returns create independent values | SP7 | — |  | pending |
| D-117 | References may target variables, fields and array elements; not temporaries | SP7 | — |  | pending |
| D-118 | Reference and slice overlap | SP7 | — |  | pending |
| D-119 | Array slices `array[start..end]` | SP7 | — | OI-10 | pending |
| D-120 | Unspecified-size parameters `ref T[]` / `inout T[]` | SP7 | — |  | pending |
| D-121 | By-value array parameters | SP7 | — |  | pending |
| D-122 | Mutable global declaration initializers | SP9 | — |  | pending |
| D-123 | Automatic defaults | SP9 | — |  | pending |
| D-124 | Application-specific global setup | SP9 | — | OI-7 | pending |
| D-125 | Runtime resources | SP13 | — |  | pending |
| D-126 | Resource identifier space | SP13 | — |  | pending |
| D-127 | Resource storage strategy and cleanup | SP13 | — | OI-20 | pending |
| D-128 | Array/structure defaults apply recursively | SP9 | — |  | pending |
| D-129 | Global const requires an explicit initializer | SP4 | — |  | pending |
| D-130 | Explicit array/structure construction remains complete | SP5 | — |  | pending |
| D-131 | Nested transactions, including through function calls | SP10 | — | OI-3 | pending |
| D-132 | Callee persistent assignments participate in an active transaction | SP10 | — |  | pending |
| D-133 | By-value aggregate parameters | SP13 | — | OI-21 | pending |
| D-134 | Familiar imperative syntax, static types | SP0 | 01 §1.1 |  | deferred |
| D-135 | Compact custom VM with single-digit KiB RAM goals | SP13 | — |  | pending |
| D-201 | No opaque platform value types | SP13 | — |  | pending |
| D-202 | Every resource operation validates existence, kind, state and permissions in the caller's resource space | SP13 | — |  | pending |
| D-203 | Resource operation outcomes: create on existing ID fails recoverably (never replaces) | SP13 | — | OI-15 | pending |
| D-204 | Copying a resource identifier copies only the number | SP13 | — |  | pending |
| D-205 | Language transactions do not automatically cover resource-API effects | SP13 | — |  | pending |
| D-206 | Exceeding a runtime stack/execution limit traps | SP12 | — |  | pending |
| D-207 | Commit failure never resumes after the block | SP10 | — |  | pending |
| D-208 | The platform must prevent any other execution context (callbacks, reentrant commands) from observing partially updated transactional state | SP13 | — |  | pending |
| D-209 | Published application/platform error-code meanings remain stable | SP12 | — | OI-15 | pending |
| D-401 | Source file extension is `.card` | SP1 | — | OI-1 | pending |
| D-402 | No platform dispatch within an application; PN §1 row superseded | SP13 | — | OI-2 | pending |
| D-403 | Nested transactions rejected statically by a structural call-graph rule | SP10 | — | OI-3 | pending |
| D-404 | Keyword list; Ok/Err keywords; intrinsics and card/CardError reserved | SP1 | — | OI-4 | pending |
| D-405 | Entry point is the single `command` declaration, any name | SP11 | — | OI-5 | pending |
| D-406 | Platform API calls use the reserved `card.` path form | SP2 | — | OI-6 | pending |
| D-407 | Lifecycle handlers use platform-reserved function names/signatures | SP9 | — | OI-7 | pending |
| D-408 | `attempt` allowed in any runtime expression position, with three exclusions | SP5 | — | OI-8 | pending |
| D-409 | Assignment: destination path first, then RHS, then store | SP6 | — | OI-9 | pending |
| D-410 | Slice endpoint typing, order, positions and limits fixed | SP7 | — | OI-10 | pending |
| D-411 | Constant-evaluation algorithm normative; constant OOB index is a compile error | SP4 | — | OI-11 | pending |
| D-412 | No `byte` alias in Draft 0.1 | SP3 | — | OI-12 | pending |
| D-413 | Zero or one error set; intrinsic outcomes may be forwarded | SP8 | — | OI-13 | pending |
| D-414 | Literal prefix, digit and magnitude rules | SP1 | — | OI-14 | pending |
| D-415 | Trap-kind and placeholder platform-error names | SP12 | — | OI-15 | pending |
| D-416 | Persistent deletion/upgrade/migration are platform-defined | SP9 | — | OI-16 | pending |
| D-417 | Large-data object API is future platform work | SP13 | — | OI-17 | pending |
| D-418 | Outcome typing settled by DN §6.3 | SP8 | — | OI-18 | pending |
| D-419 | Oversized atomic aggregate assignment rejected at build/load time | SP9 | — | OI-19 | pending |
| D-420 | Resource storage strategy is platform-defined | SP13 | — | OI-20 | pending |
| D-421 | Call-frame placement is informative VM guidance | SP13 | — | OI-21 | pending |
