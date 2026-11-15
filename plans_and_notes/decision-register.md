# CardLang decision register

Status: maintained by the specification sub-plans (see `specification-plan-of-plans.md`).
Created by SP0.

This register gives every recorded design decision a stable ID. Spec rules cite these IDs, and `spec/annex-D-traceability.md` maps each ID back to the rules that implement it.

## Sources and citation

- **DN**: `plans_and_notes/card-language-design-notes.md`, revision of 2026-11-15.
- **PN**: `plans_and_notes/cardlang-platform-notes.md`, dated 2026-11-14.
- Sections are cited as `DN §n.n` or `PN §n`.

## ID ranges

| Range | Content |
|---|---|
| `D-001`…`D-135` | The rows of the DN §2 decision table, in table order. The Topic and Recorded status columns are copied verbatim |
| `D-201`… | Agreed items stated in PN and not covered by a DN §2 row. These are summaries, not verbatim text |
| `D-301`… | Agreed decisions stated only in DN body sections. Later sub-plans add them as they reach each section |
| `D-401`… | Decisions made by resolving open issues. `D-4nn` resolves `OI-nn` (see the Annex C resolution log) |

IDs are never reused or renumbered. A withdrawn decision keeps its row, marked "withdrawn".

## Columns

- **Spec tag**: how the decision is tagged when it becomes a rule. The mapping follows the DN header (line 10): an "agreed direction" records an explicit decision, so it is [Agreed]; a "proposal" is an idea still to validate, so it is [Proposal]. When a status carries an open qualifier (for example "detailed semantics open"), the stated part is [Agreed] and the qualifier becomes the linked open issue.
- **Layer**:
  - `language` decisions become chapter rules.
  - `platform` decisions become Annex B `PLT-n` requirements or platform-defined items.
  - `VM/profile` decisions are informative material in Annex B.
- **Owning SP**: the sub-plan that turns the decision into rules.
- **Linked OI**: the open issue in `spec/annex-C-open-issues.md` for a qualifier, contradiction or gap.
- **Implemented by**: rule IDs, filled in by the owning sub-plan. `pending` means not yet specified.

"Deferred" in a recorded status (D-006 local `const`, D-077 multidimensional arrays) means *excluded from this version*. These rows are [Agreed] exclusions with no open issue: a future version may revisit them.

D-134 ("Familiar imperative syntax, static types", a proposed baseline) is cited as informative design intent in `spec/01-scope-and-conventions.md`. The concrete agreed rows supersede it wherever they are more specific.

## DN §2 decisions

| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |
|---|---|---|---|---|---|---|---|---|
| D-001 | Language name: CardLang | Agreed | [Agreed] | language | DN §1 | SP0 |  | 01 §1.1 |
| D-002 | Custom card-oriented language | Agreed direction | [Agreed] | language | DN §1 | SP0 |  | 01 §1.1 |
| D-003 | Global declarations: `persistent`, `session` or `const` | Agreed; exactly one keyword | [Agreed] | language | DN §5.1 | SP2 |  | pending |
| D-004 | `persistent` and `session` imply mutable state | Agreed | [Agreed] | language | DN §5.1 | SP9 |  | pending |
| D-005 | Global `const` declares a compile-time constant | Agreed | [Agreed] | language | DN §5.1, §3.10 | SP4 |  | pending |
| D-006 | Local value declarations use `var` only | Agreed; local `const` deferred | [Agreed] | language | DN §5.1 | SP6 |  | pending |
| D-007 | Storage qualifiers inside functions/commands are forbidden | Agreed | [Agreed] | language | DN §5.1 | SP2 |  | pending |
| D-008 | Explicit persistent state | Agreed direction; detailed semantics open | [Agreed] | language | DN §5, §5.1 | SP9 | OI-16 | pending |
| D-009 | Simple persistent declarations plus an object API for larger data | Preferred direction accepted in discussion; API not designed | [Agreed] | platform | DN §5 | SP13 | OI-17 | pending |
| D-010 | Recoverable errors through explicit results, execution faults through traps | Agreed direction | [Agreed] | language | DN §6.1, §6.4 | SP8 |  | pending |
| D-011 | No general-purpose exceptions initially | Agreed direction | [Agreed] | language | DN §6.1 | SP8 |  | pending |
| D-012 | Every function returns a success/error result | Agreed direction; detailed typing open | [Agreed] | language | DN §6.1, §6.3 | SP8 | OI-18 | pending |
| D-013 | Explicit outcome handling uses `match` with `Ok` / `Err` | Agreed | [Agreed] | language | DN §3.6, §6.1 | SP8 |  | pending |
| D-014 | Automatic error propagation with `attempt` | Agreed | [Agreed] | language | DN §6.3 | SP8 |  | pending |
| D-015 | Discarded function outcomes | Compilation error | [Agreed] | language | DN §6.3 | SP8 |  | pending |
| D-016 | Stored result values / user-visible `Result<T>` | Not supported initially; outcomes must be consumed immediately | [Agreed] | language | DN §6.3 | SP8 |  | pending |
| D-017 | `attempt` type | Exactly the successful payload type; statement form only for no-payload success | [Agreed] | language | DN §6.3 | SP8 |  | pending |
| D-018 | One application error set with explicit nonzero `u16` codes | Agreed | [Agreed] | language | DN §6.3 | SP8 | OI-13 | pending |
| D-019 | Application/platform errors and traps have separate reporting categories | Agreed | [Agreed] | language | DN §6.3 | SP8 |  | pending |
| D-020 | Single application or completely isolated applications | Agreed; no cross-application calls/references/shared state | [Agreed] | language | DN §1, §4.1; PN §1 | SP2 |  | pending |
| D-021 | Multiple source files form one application compilation unit | Agreed; explicit file list and build-supplied identity | [Agreed] | language | DN §3.0, §4.1 | SP2 |  | pending |
| D-022 | Source files contain complete top-level declarations; no application wrapper | Agreed | [Agreed] | language | DN §3.0, §4.1 | SP2 |  | pending |
| D-023 | Source extension `.card`; UTF-8 source, ASCII identifiers | Agreed | [Agreed] | language | DN §1, §3.0 | SP1 | OI-1 | pending |
| D-024 | Mandatory semicolons, braces and named-declaration type annotations | Agreed | [Agreed] | language | DN §3.0 | SP1 |  | pending |
| D-025 | No-value ordinary function signature | Omit return arrow; the host entry point instead returns a u32 response count | [Agreed] | language | DN §3.0, §3.7, §4 | SP7 |  | pending |
| D-026 | Function arguments | Positional only; explicit parameter types and modes; trailing commas allowed | [Agreed] | language | DN §3.7 | SP7 |  | pending |
| D-027 | Calls inside argument expressions | Forbidden, including intrinsic calls; evaluate into locals first | [Agreed] | language | DN §3.7 | SP5 |  | pending |
| D-028 | Error pattern bindings | Arm-local propagation only; no ordinary error value type initially | [Agreed] | language | DN §6.3 | SP8 |  | pending |
| D-029 | Constant-only calculations outside global constants | Compile-time evaluation; evaluated failures are compilation errors | [Agreed] | language | DN §3.10 | SP4 | OI-11 | pending |
| D-030 | Function completion analysis | Conservative structural rules; trapping calculations are not a return exemption | [Agreed] | language | DN §3.7 | SP6 |  | pending |
| D-031 | Recursion, function values/pointers and user-defined generics | Not supported initially | [Agreed] | language | DN §3.7 | SP7 |  | pending |
| D-032 | Function prototypes | Not supported; definitions are visible regardless of source order | [Agreed] | language | DN §3.7 | SP7 |  | pending |
| D-033 | Successful function returns | One supported value or no payload; no tuples or returned references | [Agreed] | language | DN §3.7 | SP7 |  | pending |
| D-034 | Reachable function fall-through | Compilation error; no implicit success | [Agreed] | language | DN §3.6, §3.7 | SP6 |  | pending |
| D-035 | Commands called by application code | Forbidden; shared logic belongs in ordinary functions | [Agreed] | language | DN §3.7, §4.1 | SP11 |  | pending |
| D-036 | Integer literals | Decimal, hexadecimal, binary; contextual types; no suffixes | [Agreed] | language | DN §3.0, §3.3 | SP1 | OI-14 | pending |
| D-037 | No preprocessor/macros/textual includes | Agreed | [Agreed] | language | DN §3.0 | SP1 |  | pending |
| D-038 | Application declarations and struct fields visible across all source files | Agreed; no per-file privacy | [Agreed] | language | DN §4.1 | SP2 |  | pending |
| D-039 | User modules/namespaces/imports/exports/classes/access modifiers | Omitted initially | [Agreed] | language | DN §4.1 | SP2 |  | pending |
| D-040 | File order does not control name resolution or initialization order | Agreed | [Agreed] | language | DN §4.1, §4.2 | SP2 |  | pending |
| D-041 | Host entry point | Exactly one command per application; ref u8[] request, inout u8[] response, successful u32 byte count | [Agreed] | language | DN §4 | SP11 | OI-5 | pending |
| D-042 | Application protocol | Application parses and dispatches request bytes and encodes response bytes; no generated typed-command serialization | [Agreed] | language | DN §4 | SP11 |  | pending |
| D-043 | Classical smart-card status | Platform reports success/errors/traps through response SW mapping; exact mapping remains platform-defined | [Agreed] | platform | DN §4, §6.3; PN §5 | SP13 | OI-2 | pending |
| D-044 | Platform interface names cannot be redefined | Agreed | [Agreed] | language | DN §4.1, §4.2 | SP2 | OI-4 | pending |
| D-045 | One shared top-level naming scope for types and values | Agreed; duplicate names forbidden | [Agreed] | language | DN §4.2 | SP2 |  | pending |
| D-046 | No function overloading or local function/type/error-set definitions | Agreed | [Agreed] | language | DN §4.2 | SP2 |  | pending |
| D-047 | Fields and error members have owner-specific name scopes | Agreed | [Agreed] | language | DN §4.2 | SP2 |  | pending |
| D-048 | Local binding visible only after its initializer completes | Agreed | [Agreed] | language | DN §3.6, §4.2 | SP2 |  | pending |
| D-049 | Command execution | Agreed; commands never interleave; each finishes or fails before another starts | [Agreed] | language | DN §4 | SP11 |  | pending |
| D-050 | Session state at chip power-on | Agreed; initialize to recursive type defaults | [Agreed] | language | DN §3.9, §6.4 | SP9 |  | pending |
| D-051 | Ordinary traps preserve application session state | Agreed; terminated call frames discarded; subsequent commands may execute | [Agreed] | language | DN §6.4 | SP12 |  | pending |
| D-052 | Runtime-owned resources on ordinary trap | Agreed; no automatic cleanup, deletion or invalidation caused by the trap | [Agreed] | platform | DN §6.4, §11.2; PN §2 | SP13 |  | pending |
| D-053 | Session/persistent logical consistency | Application programmer responsibility; no automatic synchronization or repair | [Agreed] | language | DN §6.4 | SP12 |  | pending |
| D-054 | Runtime-issued security reset | Clears session state; subsequent initialization restores type defaults | [Agreed] | language | DN §6.4 | SP12 |  | pending |
| D-055 | Transactions roll back persistent changes only | Agreed | [Agreed] | language | DN §7.2 | SP10 |  | pending |
| D-056 | Fatal platform failure triggers whole-chip security reset | Platform requirement; clears volatile state | [Agreed] | platform | DN §6.4; PN §3 | SP13 |  | pending |
| D-057 | Each persistent assignment is atomic | Agreed direction; aggregate limits and storage details open | [Agreed] | language | DN §7.1, §7.4 | SP9 | OI-19 | pending |
| D-058 | Explicit handling of overflow and underflow | Required feature | [Agreed] | language | DN §6.2, §6.5 | SP5 |  | pending |
| D-059 | Global/local arrays of supported fixed-size values | Agreed: integers, bool, structs and enums | [Agreed] | language | DN §8, §8.2 | SP3 |  | pending |
| D-060 | Array type syntax `T[N]` | Agreed | [Agreed] | language | DN §8 | SP3 |  | pending |
| D-061 | Array `.length` | Read-only element count of type `u32`; compile-time known for fixed arrays | [Agreed] | language | DN §8.1 | SP5 |  | pending |
| D-062 | Array index types | `u8`, `u16` or `u32`; signed indices forbidden | [Agreed] | language | DN §8.1 | SP5 |  | pending |
| D-063 | Array initialization with `fill(value)` or an exact-length element list | Agreed | [Agreed] | language | DN §8 | SP5 |  | pending |
| D-064 | No special `zero` initializer | Agreed | [Agreed] | language | DN §8 | SP5 |  | pending |
| D-065 | Named structures with typed fields | Agreed; nominal type identity | [Agreed] | language | DN §9, §9.3 | SP3 |  | pending |
| D-066 | Empty structures | Compilation error initially | [Agreed] | language | DN §9.3 | SP3 |  | pending |
| D-067 | Enums | Named, nominal, nonempty; no payloads or numeric values | [Agreed] | language | DN §3.11 | SP3 |  | pending |
| D-068 | Enum defaults | First declared variant | [Agreed] | language | DN §3.11 | SP3 |  | pending |
| D-069 | Enum matching | All variants explicit, no duplicate or catch-all arms | [Agreed] | language | DN §3.11, §3.6 | SP6 |  | pending |
| D-070 | Structure constructors | Direct values; every field exactly once; written-order evaluation | [Agreed] | language | DN §9.3 | SP5 |  | pending |
| D-071 | Structure array fields accept `fill(value)` and explicit lists | Agreed | [Agreed] | language | DN §9 | SP5 |  | pending |
| D-072 | Structures may contain other structures | Agreed | [Agreed] | language | DN §9.1 | SP3 |  | pending |
| D-073 | Nested fields inherit instance storage and mutability | Agreed | [Agreed] | language | DN §9.1 | SP3 |  | pending |
| D-074 | Direct or indirect recursive containment is forbidden | Agreed | [Agreed] | language | DN §9.1, §9.3 | SP3 |  | pending |
| D-075 | Primitive types: `u8`, `u16`, `u32`, `i8`, `i16`, `i32`, `bool` | Agreed | [Agreed] | language | DN §3.1 | SP3 |  | pending |
| D-076 | Byte arrays as `u8[N]` | Agreed | [Agreed] | language | DN §3.1, §8 | SP3 | OI-12 | pending |
| D-077 | Zero-length and direct multidimensional arrays | Forbidden/deferred initially | [Agreed] | language | DN §8.2 | SP3 |  | pending |
| D-078 | Whole-array assignment | Exact element type and length; independent value copy | [Agreed] | language | DN §8.2 | SP6 |  | pending |
| D-079 | fill(expression) | Reserved array-construction intrinsic; direct array value, once-and-copy | [Agreed] | language | DN §8.3 | SP5 |  | pending |
| D-080 | Indexed assignment order | Evaluate/check destination index before right-hand side | [Agreed] | language | DN §8.2 | SP6 | OI-9 | pending |
| D-081 | No implicit conversions between integer types | Agreed | [Agreed] | language | DN §3.2 | SP5 |  | pending |
| D-082 | Arithmetic and comparisons require matching integer types | Agreed | [Agreed] | language | DN §3.2, §3.5 | SP5 |  | pending |
| D-083 | Explicit `convert<T>` and `checked_convert<T>` intrinsics | Agreed | [Agreed] | language | DN §3.2 | SP5 |  | pending |
| D-084 | Contextual integer literal typing; no guessed default type | Agreed | [Agreed] | language | DN §3.3 | SP5 | OI-14 | pending |
| D-085 | Literal-only array index expressions | u32 context; typed unsigned indices retain their types | [Agreed] | language | DN §3.3, §8.1 | SP5 |  | pending |
| D-086 | Conversion intrinsics require a known source type | Agreed | [Agreed] | language | DN §3.3 | SP5 |  | pending |
| D-087 | No widening to avoid intermediate arithmetic failure | Agreed | [Agreed] | language | DN §3.3 | SP5 |  | pending |
| D-088 | Signed minimum / -1 | Trap; checked_div returns arithmetic error | [Agreed] | language | DN §3.5, §6.5 | SP5 |  | pending |
| D-089 | Signed minimum % -1 | Defined zero; checked_rem succeeds | [Agreed] | language | DN §6.5 | SP5 |  | pending |
| D-090 | Unary negation | Signed only; unrepresentable negation traps | [Agreed] | language | DN §6.5 | SP5 |  | pending |
| D-091 | Checked arithmetic | add/sub/mul/div/rem/neg intrinsics return outcomes | [Agreed] | language | DN §6.5 | SP5 | OI-13 | pending |
| D-092 | Wrapping arithmetic | add/sub/mul intrinsics return direct modular values | [Agreed] | language | DN §6.5 | SP5 |  | pending |
| D-093 | Checked/wrapping arithmetic intrinsics in constants | Excluded initially | [Agreed] | language | DN §3.10, §6.5 | SP4 |  | pending |
| D-094 | Constant expressions | Deterministic side-effect-free subset; see section 3.10 | [Agreed] | language | DN §3.10 | SP4 |  | pending |
| D-095 | Guaranteed convert<T> in constant expressions | Agreed; constant operand with independently known source type; full source range must fit target | [Agreed] | language | DN §3.10 | SP4 |  | pending |
| D-096 | checked_convert<T> in constant expressions | Excluded initially; no compile-time outcome handling | [Agreed] | language | DN §3.10 | SP4 |  | pending |
| D-097 | Constant-evaluation boundary algorithm | Structural policy proposed in section 3.10; detailed acceptance examples pending validation | [Agreed] (via D-411) | language | DN §3.10 | SP4 | OI-11 | pending |
| D-098 | Constant dependencies | Forward references allowed; cycles are compilation errors | [Agreed] | language | DN §3.10 | SP4 |  | pending |
| D-099 | Fixed-array lengths | Unsigned constant expressions; literal-only expressions use u32 context | [Agreed] | language | DN §3.10 | SP4 |  | pending |
| D-100 | No implicit boolean/numeric, array or structure conversions | Agreed | [Agreed] | language | DN §3.4 | SP3 |  | pending |
| D-101 | No general truncating cast initially | Agreed | [Agreed] | language | DN §3.2 | SP5 |  | pending |
| D-102 | Mixed binary operators require parentheses; no binary precedence hierarchy | Agreed | [Agreed] | language | DN §3.5 | SP5 |  | pending |
| D-103 | Same-operator chains evaluate left to right; comparison chains forbidden | Agreed | [Agreed] | language | DN §3.5 | SP5 |  | pending |
| D-104 | Left-to-right evaluation and short-circuit boolean logic | Agreed | [Agreed] | language | DN §3.5 | SP5 |  | pending |
| D-105 | Assignment is a statement, not an expression | Agreed | [Agreed] | language | DN §3.5 | SP6 |  | pending |
| D-106 | Control flow: `if`, `while`, range `for`, `match`, `break`, `continue`, `return` | Agreed | [Agreed] | language | DN §3.6 | SP6 |  | pending |
| D-107 | Explicit `return Ok(value)` / `return Err(error)`; no implicit success | Agreed | [Agreed] | language | DN §3.6, §3.7 | SP8 |  | pending |
| D-108 | Exhaustive result matching; read-only loop and pattern bindings | Agreed | [Agreed] | language | DN §3.6 | SP8 |  | pending |
| D-109 | No `return`, `break` or `continue` across transaction boundaries | Agreed | [Agreed] | language | DN §3.6, §7.2 | SP10 |  | pending |
| D-110 | Explicit recoverable transaction exit: `abort Err(error);` | Agreed; roll back persistent changes and return Err from the enclosing function/command | [Agreed] | language | DN §7.2 | SP10 |  | pending |
| D-111 | `abort` scope | Lexically inside a transaction only; helpers return Err for the transaction owner to handle | [Agreed] | language | DN §7.2 | SP10 |  | pending |
| D-112 | Parameters: by value, read-only `ref`, mutable `inout` | Agreed | [Agreed] | language | DN §3.7 | SP7 |  | pending |
| D-113 | Reference modes explicit at declaration and call site | Agreed | [Agreed] | language | DN §3.7 | SP7 |  | pending |
| D-114 | References are call-scoped; no raw pointers or escaping references | Agreed | [Agreed] | language | DN §3.7, §3.8 | SP7 |  | pending |
| D-115 | Reference permissions | ref is read-only through that path; inout permits reads/writes; neither grants exclusivity | [Agreed] | language | DN §3.7, §3.8 | SP7 |  | pending |
| D-116 | Assignment/value parameters/value returns create independent values | Agreed | [Agreed] | language | DN §3.8 | SP7 |  | pending |
| D-117 | References may target variables, fields and array elements; not temporaries | Agreed | [Agreed] | language | DN §3.8 | SP7 |  | pending |
| D-118 | Reference and slice overlap | Allowed, including mutable overlap; no overlap checks or overlap traps | [Agreed] | language | DN §3.8, §8.4 | SP7 |  | pending |
| D-119 | Array slices `array[start..end]` | Agreed; half-open borrowed regions, bounds checked; empty slices allowed | [Agreed] | language | DN §8.4 | SP7 | OI-10 | pending |
| D-120 | Unspecified-size parameters `ref T[]` / `inout T[]` | Agreed; runtime u32 length, exact element type, no backing-array copy | [Agreed] | language | DN §8.4 | SP7 |  | pending |
| D-121 | By-value array parameters | Fixed-size T[N] only | [Agreed] | language | DN §8.4 | SP7 |  | pending |
| D-122 | Mutable global declaration initializers | Forbidden for persistent/session state | [Agreed] | language | DN §3.9 | SP9 |  | pending |
| D-123 | Automatic defaults | New persistent/session state and uninitialized locals: zero/false recursively | [Agreed] | language | DN §3.9 | SP9 |  | pending |
| D-124 | Application-specific global setup | Lifecycle handlers; event API deferred to platform | [Agreed] | language | DN §3.9; PN §3 | SP9 | OI-7 | pending |
| D-125 | Runtime resources | Application-chosen u32 identifiers; 0 invalid; runtime-owned objects | [Agreed] | platform | DN §11.2; PN §2 | SP13 |  | pending |
| D-126 | Resource identifier space | One per isolated application, covering all resource kinds | [Agreed] | platform | DN §11.2; PN §2 | SP13 |  | pending |
| D-127 | Resource storage strategy and cleanup | Platform decisions; identifier API does not require a heap | [Agreed] | platform | DN §11.2; PN §2 | SP13 | OI-20 | pending |
| D-128 | Array/structure defaults apply recursively | Agreed | [Agreed] | language | DN §3.9 | SP9 |  | pending |
| D-129 | Global const requires an explicit initializer | Agreed | [Agreed] | language | DN §3.9, §3.10 | SP4 |  | pending |
| D-130 | Explicit array/structure construction remains complete | Agreed for constants, local initializers and assignments | [Agreed] | language | DN §3.9, §9.3 | SP5 |  | pending |
| D-131 | Nested transactions, including through function calls | Forbidden initially | [Agreed] | language | DN §7.3 | SP10 | OI-3 | pending |
| D-132 | Callee persistent assignments participate in an active transaction | Agreed | [Agreed] | language | DN §7.3 | SP10 |  | pending |
| D-133 | By-value aggregate parameters | Temporary application RAM; call-frame placement proposed | [Agreed]; placement informative (D-421) | VM/profile | DN §3.8; PN §4 | SP13 | OI-21 | pending |
| D-134 | Familiar imperative syntax, static types | Proposed baseline | [Proposal] | language | DN §3 | SP0 |  | 01 §1.1 (informative) |
| D-135 | Compact custom VM with single-digit KiB RAM goals | Feasibility direction; unmeasured | [Proposal] | VM/profile | PN §4 | SP13 |  | pending |

## Platform-notes items (D-201…)

| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |
|---|---|---|---|---|---|---|---|---|
| D-201 | No opaque platform value types; platform APIs use ordinary value types, with fully visible platform-supplied configuration structures and algorithm enums | (summary; see sources) | [Agreed] | platform | PN §2; DN §11.1 | SP13 |  | pending |
| D-202 | Every resource operation validates existence, kind, state and permissions in the caller's resource space; wrong kind is a defined recoverable error; identifiers never authorize cross-application access | (summary; see sources) | [Agreed] | platform | PN §2; DN §11.1 | SP13 |  | pending |
| D-203 | Resource operation outcomes: create on existing ID fails recoverably (never replaces); unknown ID and wrong kind fail recoverably; capacity failure is a defined recoverable error; failed creation exposes no partial object (error names are placeholders) | (summary; see sources) | [Agreed] | platform | PN §2; DN §11.2 | SP13 | OI-15 | pending |
| D-204 | Copying a resource identifier copies only the number; no stale-handle detection; identifier-variable lifetime is independent of resource lifetime | (summary; see sources) | [Agreed] | platform | PN §2; DN §11.2 | SP13 |  | pending |
| D-205 | Language transactions do not automatically cover resource-API effects; each API must define its transaction participation or prohibit use during a transaction | (summary; see sources) | [Agreed] | platform | PN §2, §5; DN §7.2 | SP13 |  | pending |
| D-206 | Exceeding a runtime stack/execution limit traps; exceeding build/load capacity may reject the application; limits must not silently change language semantics | (summary; see sources) | [Agreed] | language | PN §4; DN §12 | SP12 |  | pending |
| D-207 | Commit failure never resumes after the block; a contained failure traps, an integrity failure triggers security reset; recovery exposes all or none of a transaction and fails closed | (summary; see sources) | [Agreed] | language | PN §5; DN §7.2 | SP10 |  | pending |
| D-208 | The platform must prevent any other execution context (callbacks, reentrant commands) from observing partially updated transactional state | (summary; see sources) | [Agreed] | platform | PN §5 | SP13 |  | pending |
| D-209 | Published application/platform error-code meanings remain stable; codes are nonzero u16 values in separate categories | (summary; see sources) | [Agreed] | language | PN §5; DN §6.3 | SP12 | OI-15 | pending |

## DN body-only decisions (D-301…)

None registered yet. Sub-plans SP1–SP13 add rows here as they reach each DN section.

| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |
|---|---|---|---|---|---|---|---|---|

## Open-issue resolutions (D-401…)

| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |
|---|---|---|---|---|---|---|---|---|
| D-401 | Source file extension is `.card` | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-1 | SP1 | OI-1 | pending |
| D-402 | No platform dispatch within an application; PN §1 row superseded | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-2 | SP13 | OI-2 | pending |
| D-403 | Nested transactions rejected statically by a structural call-graph rule | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-3 | SP10 | OI-3 | pending |
| D-404 | Keyword list; Ok/Err keywords; intrinsics and card/CardError reserved | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-4 | SP1 | OI-4 | pending |
| D-405 | Entry point is the single `command` declaration, any name | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-5 | SP11 | OI-5 | pending |
| D-406 | Platform API calls use the reserved `card.` path form | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-6 | SP2 | OI-6 | pending |
| D-407 | Lifecycle handlers use platform-reserved function names/signatures | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-7 | SP9 | OI-7 | pending |
| D-408 | `attempt` allowed in any runtime expression position, with three exclusions | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-8 | SP5 | OI-8 | pending |
| D-409 | Assignment: destination path first, then RHS, then store | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-9 | SP6 | OI-9 | pending |
| D-410 | Slice endpoint typing, order, positions and limits fixed | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-10 | SP7 | OI-10 | pending |
| D-411 | Constant-evaluation algorithm normative; constant OOB index is a compile error | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-11 | SP4 | OI-11 | pending |
| D-412 | No `byte` alias in Draft 0.1 | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-12 | SP3 | OI-12 | pending |
| D-413 | Zero or one error set; intrinsic outcomes may be forwarded | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-13 | SP8 | OI-13 | pending |
| D-414 | Literal prefix, digit and magnitude rules | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-14 | SP1 | OI-14 | pending |
| D-415 | Trap-kind and placeholder platform-error names | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-15 | SP12 | OI-15 | pending |
| D-416 | Persistent deletion/upgrade/migration are platform-defined | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-16 | SP9 | OI-16 | pending |
| D-417 | Large-data object API is future platform work | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-17 | SP13 | OI-17 | pending |
| D-418 | Outcome typing settled by DN §6.3 | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-18 | SP8 | OI-18 | pending |
| D-419 | Oversized atomic aggregate assignment rejected at build/load time | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-19 | SP9 | OI-19 | pending |
| D-420 | Resource storage strategy is platform-defined | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-20 | SP13 | OI-20 | pending |
| D-421 | Call-frame placement is informative VM guidance | Resolved by user 2026-11-15 | [Agreed] | VM/profile | Annex C OI-21 | SP13 | OI-21 | pending |
