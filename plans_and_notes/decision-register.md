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
| D-003 | Global declarations: `persistent`, `session` or `const` | Agreed; exactly one keyword | [Agreed] | language | DN §5.1 | SP2 |  | NAM-6, NAM-9 |
| D-004 | `persistent` and `session` imply mutable state | Agreed | [Agreed] | language | DN §5.1 | SP9 |  | STA-1 |
| D-005 | Global `const` declares a compile-time constant | Agreed | [Agreed] | language | DN §5.1, §3.10 | SP4 |  | CEX-1, CEX-2 |
| D-006 | Local value declarations use `var` only | Agreed; local `const` deferred | [Agreed] | language | DN §5.1 | SP6 |  | NAM-10, STM-4 |
| D-007 | Storage qualifiers inside functions/commands are forbidden | Agreed | [Agreed] | language | DN §5.1 | SP2 |  | NAM-10 |
| D-008 | Explicit persistent state | Agreed direction; detailed semantics open | [Agreed] | language | DN §5, §5.1 | SP9 | OI-16 | STA-3, STA-11 |
| D-009 | Simple persistent declarations plus an object API for larger data | Preferred direction accepted in discussion; API not designed | [Agreed] | platform | DN §5 | SP13 | OI-17 | PLT-17 |
| D-010 | Recoverable errors through explicit results, execution faults through traps | Agreed direction | [Agreed] | language | DN §6.1, §6.4 | SP8 |  | OUT-1 |
| D-011 | No general-purpose exceptions initially | Agreed direction | [Agreed] | language | DN §6.1 | SP8 |  | OUT-1 |
| D-012 | Every function returns a success/error result | Agreed direction; detailed typing open | [Agreed] | language | DN §6.1, §6.3 | SP8 | OI-18 | OUT-1, OUT-2 |
| D-013 | Explicit outcome handling uses `match` with `Ok` / `Err` | Agreed | [Agreed] | language | DN §3.6, §6.1 | SP8 |  | OUT-11 |
| D-014 | Automatic error propagation with `attempt` | Agreed | [Agreed] | language | DN §6.3 | SP8 |  | OUT-8, OUT-10 |
| D-015 | Discarded function outcomes | Compilation error | [Agreed] | language | DN §6.3 | SP8 |  | OUT-5, OUT-7 |
| D-016 | Stored result values / user-visible `Result<T>` | Not supported initially; outcomes must be consumed immediately | [Agreed] | language | DN §6.3 | SP8 |  | OUT-2 |
| D-017 | `attempt` type | Exactly the successful payload type; statement form only for no-payload success | [Agreed] | language | DN §6.3 | SP8 |  | OUT-9, OUT-10 |
| D-018 | One application error set with explicit nonzero `u16` codes | Agreed | [Agreed] | language | DN §6.3 | SP8 | OI-13 | OUT-15, OUT-16 |
| D-019 | Application/platform errors and traps have separate reporting categories | Agreed | [Agreed] | language | DN §6.3 | SP8 |  | OUT-18 |
| D-020 | Single application or completely isolated applications | Agreed; no cross-application calls/references/shared state | [Agreed] | language | DN §1, §4.1; PN §1 | SP2 |  | NAM-5 |
| D-021 | Multiple source files form one application compilation unit | Agreed; explicit file list and build-supplied identity | [Agreed] | language | DN §3.0, §4.1 | SP2 |  | NAM-1 |
| D-022 | Source files contain complete top-level declarations; no application wrapper | Agreed | [Agreed] | language | DN §3.0, §4.1 | SP2 |  | NAM-1, NAM-2, NAM-6, NAM-8 |
| D-023 | Source extension `.card`; UTF-8 source, ASCII identifiers | Agreed | [Agreed] | language | DN §1, §3.0 | SP1 | OI-1 | LEX-1, LEX-2, LEX-3, LEX-12 |
| D-024 | Mandatory semicolons, braces and named-declaration type annotations | Agreed | [Agreed] | language | DN §3.0 | SP1 |  | LEX-22, LEX-23, NAM-9, TYP-3, STM-1, FUN-1; Annex A §A.2 |
| D-025 | No-value ordinary function signature | Omit return arrow; the host entry point instead returns a u32 response count | [Agreed] | language | DN §3.0, §3.7, §4 | SP7 |  | FUN-2 |
| D-026 | Function arguments | Positional only; explicit parameter types and modes; trailing commas allowed | [Agreed] | language | DN §3.7 | SP7 |  | FUN-1 |
| D-027 | Calls inside argument expressions | Forbidden, including intrinsic calls; evaluate into locals first | [Agreed] | language | DN §3.7 | SP5 |  | EXP-49 |
| D-028 | Error pattern bindings | Arm-local propagation only; no ordinary error value type initially | [Agreed] | language | DN §6.3 | SP8 |  | OUT-4, OUT-14 |
| D-029 | Constant-only calculations outside global constants | Compile-time evaluation; evaluated failures are compilation errors | [Agreed] | language | DN §3.10 | SP4 | OI-11 | CEX-7, CEX-8, CEX-9 |
| D-030 | Function completion analysis | Conservative structural rules; trapping calculations are not a return exemption | [Agreed] | language | DN §3.7 | SP6 |  | STM-20, STM-21 |
| D-031 | Recursion, function values/pointers and user-defined generics | Not supported initially | [Agreed] | language | DN §3.7 | SP7 |  | FUN-4, FUN-5 |
| D-032 | Function prototypes | Not supported; definitions are visible regardless of source order | [Agreed] | language | DN §3.7 | SP7 |  | FUN-3 |
| D-033 | Successful function returns | One supported value or no payload; no tuples or returned references | [Agreed] | language | DN §3.7 | SP7 |  | FUN-2 |
| D-034 | Reachable function fall-through | Compilation error; no implicit success | [Agreed] | language | DN §3.6, §3.7 | SP6 |  | STM-21 |
| D-035 | Commands called by application code | Forbidden; shared logic belongs in ordinary functions | [Agreed] | language | DN §3.7, §4.1 | SP11 |  | HEP-3 |
| D-036 | Integer literals | Decimal, hexadecimal, binary; contextual types; no suffixes | [Agreed] | language | DN §3.0, §3.3 | SP1 | OI-14 | LEX-17, LEX-18, EXP-7, EXP-10, EXP-11 |
| D-037 | No preprocessor/macros/textual includes | Agreed | [Agreed] | language | DN §3.0 | SP1 |  | LEX-24 |
| D-038 | Application declarations and struct fields visible across all source files | Agreed; no per-file privacy | [Agreed] | language | DN §4.1 | SP2 |  | NAM-13 |
| D-039 | User modules/namespaces/imports/exports/classes/access modifiers | Omitted initially | [Agreed] | language | DN §4.1 | SP2 |  | NAM-8 |
| D-040 | File order does not control name resolution or initialization order | Agreed | [Agreed] | language | DN §4.1, §4.2 | SP2 |  | NAM-4 |
| D-041 | Host entry point | Exactly one command per application; ref u8[] request, inout u8[] response, successful u32 byte count | [Agreed] | language | DN §4 | SP11 | OI-5 | HEP-1, HEP-2, HEP-4 |
| D-042 | Application protocol | Application parses and dispatches request bytes and encodes response bytes; no generated typed-command serialization | [Agreed] | language | DN §4 | SP11 |  | HEP-15 |
| D-043 | Classical smart-card status | Platform reports success/errors/traps through response SW mapping; exact mapping remains platform-defined | [Agreed] | platform | DN §4, §6.3; PN §5 | SP13 | OI-2 | HEP-12, PLT-9 |
| D-044 | Platform interface names cannot be redefined | Agreed | [Agreed] | language | DN §4.1, §4.2 | SP2 | OI-4 | LEX-15, NAM-14 |
| D-045 | One shared top-level naming scope for types and values | Agreed; duplicate names forbidden | [Agreed] | language | DN §4.2 | SP2 |  | NAM-11 |
| D-046 | No function overloading or local function/type/error-set definitions | Agreed | [Agreed] | language | DN §4.2 | SP2 |  | NAM-7, NAM-12 |
| D-047 | Fields and error members have owner-specific name scopes | Agreed | [Agreed] | language | DN §4.2 | SP2 |  | NAM-15, NAM-16, NAM-17 |
| D-048 | Local binding visible only after its initializer completes | Agreed | [Agreed] | language | DN §3.6, §4.2 | SP2 |  | NAM-19, NAM-20, NAM-22 |
| D-049 | Command execution | Agreed; commands never interleave; each finishes or fails before another starts | [Agreed] | language | DN §4 | SP11 |  | HEP-13, TXN-14 |
| D-050 | Session state at chip power-on | Agreed; initialize to recursive type defaults | [Agreed] | language | DN §3.9, §6.4 | SP9 |  | STA-4 |
| D-051 | Ordinary traps preserve application session state | Agreed; terminated call frames discarded; subsequent commands may execute | [Agreed] | language | DN §6.4 | SP12 |  | STA-4, RTF-2, RTF-3 |
| D-052 | Runtime-owned resources on ordinary trap | Agreed; no automatic cleanup, deletion or invalidation caused by the trap | [Agreed] | platform | DN §6.4, §11.2; PN §2 | SP13 |  | RTF-2, PLT-23 |
| D-053 | Session/persistent logical consistency | Application programmer responsibility; no automatic synchronization or repair | [Agreed] | language | DN §6.4 | SP12 |  | STA-14, RTF-12 |
| D-054 | Runtime-issued security reset | Clears session state; subsequent initialization restores type defaults | [Agreed] | language | DN §6.4 | SP12 |  | STA-4, RTF-9 |
| D-055 | Transactions roll back persistent changes only | Agreed | [Agreed] | language | DN §7.2 | SP10 |  | TXN-4, TXN-11 |
| D-056 | Fatal platform failure triggers whole-chip security reset | Platform requirement; clears volatile state | [Agreed] | platform | DN §6.4; PN §3 | SP13 |  | RTF-9, PLT-19 |
| D-057 | Each persistent assignment is atomic | Agreed direction; aggregate limits and storage details open | [Agreed] | language | DN §7.1, §7.4 | SP9 | OI-19 | STA-11, STA-12 |
| D-058 | Explicit handling of overflow and underflow | Required feature | [Agreed] | language | DN §6.2, §6.5 | SP5 |  | EXP-23 |
| D-059 | Global/local arrays of supported fixed-size values | Agreed: integers, bool, structs and enums | [Agreed] | language | DN §8, §8.2 | SP3 |  | TYP-1, TYP-11, TYP-18 |
| D-060 | Array type syntax `T[N]` | Agreed | [Agreed] | language | DN §8 | SP3 |  | TYP-17 |
| D-061 | Array `.length` | Read-only element count of type `u32`; compile-time known for fixed arrays | [Agreed] | language | DN §8.1 | SP5 |  | EXP-40 |
| D-062 | Array index types | `u8`, `u16` or `u32`; signed indices forbidden | [Agreed] | language | DN §8.1 | SP5 |  | EXP-39 |
| D-063 | Array initialization with `fill(value)` or an exact-length element list | Agreed | [Agreed] | language | DN §8 | SP5 |  | EXP-43, EXP-44 |
| D-064 | No special `zero` initializer | Agreed | [Agreed] | language | DN §8 | SP5 |  | EXP-44 |
| D-065 | Named structures with typed fields | Agreed; nominal type identity | [Agreed] | language | DN §9, §9.3 | SP3 |  | TYP-4, TYP-13 |
| D-066 | Empty structures | Compilation error initially | [Agreed] | language | DN §9.3 | SP3 |  | TYP-13 |
| D-067 | Enums | Named, nominal, nonempty; no payloads or numeric values | [Agreed] | language | DN §3.11 | SP3 |  | TYP-4, TYP-10, TYP-11, TYP-12 |
| D-068 | Enum defaults | First declared variant | [Agreed] | language | DN §3.11 | SP3 |  | TYP-22 |
| D-069 | Enum matching | All variants explicit, no duplicate or catch-all arms | [Agreed] | language | DN §3.11, §3.6 | SP6 |  | STM-16, STM-17 |
| D-070 | Structure constructors | Direct values; every field exactly once; written-order evaluation | [Agreed] | language | DN §9.3 | SP5 |  | EXP-45 |
| D-071 | Structure array fields accept `fill(value)` and explicit lists | Agreed | [Agreed] | language | DN §9 | SP5 |  | TYP-14, EXP-45 |
| D-072 | Structures may contain other structures | Agreed | [Agreed] | language | DN §9.1 | SP3 |  | TYP-14 |
| D-073 | Nested fields inherit instance storage and mutability | Agreed | [Agreed] | language | DN §9.1 | SP3 |  | TYP-16 |
| D-074 | Direct or indirect recursive containment is forbidden | Agreed | [Agreed] | language | DN §9.1, §9.3 | SP3 |  | TYP-15, TYP-23 |
| D-075 | Primitive types: `u8`, `u16`, `u32`, `i8`, `i16`, `i32`, `bool` | Agreed | [Agreed] | language | DN §3.1 | SP3 |  | TYP-1, TYP-6, TYP-7, TYP-8 |
| D-076 | Byte arrays as `u8[N]` | Agreed | [Agreed] | language | DN §3.1, §8 | SP3 | OI-12 | TYP-20 |
| D-077 | Zero-length and direct multidimensional arrays | Forbidden/deferred initially | [Agreed] | language | DN §8.2 | SP3 |  | TYP-18, TYP-19 |
| D-078 | Whole-array assignment | Exact element type and length; independent value copy | [Agreed] | language | DN §8.2 | SP6 |  | STM-8 |
| D-079 | fill(expression) | Reserved array-construction intrinsic; direct array value, once-and-copy | [Agreed] | language | DN §8.3 | SP5 |  | EXP-44 |
| D-080 | Indexed assignment order | Evaluate/check destination index before right-hand side | [Agreed] | language | DN §8.2 | SP6 | OI-9 | STM-9, STM-10 |
| D-081 | No implicit conversions between integer types | Agreed | [Agreed] | language | DN §3.2 | SP5 |  | TYP-5, EXP-12 |
| D-082 | Arithmetic and comparisons require matching integer types | Agreed | [Agreed] | language | DN §3.2, §3.5 | SP5 |  | EXP-12, EXP-13, EXP-14 |
| D-083 | Explicit `convert<T>` and `checked_convert<T>` intrinsics | Agreed | [Agreed] | language | DN §3.2 | SP5 |  | EXP-31, EXP-32, EXP-33 |
| D-084 | Contextual integer literal typing; no guessed default type | Agreed | [Agreed] | language | DN §3.3 | SP5 | OI-14 | EXP-7, EXP-10, EXP-11 |
| D-085 | Literal-only array index expressions | u32 context; typed unsigned indices retain their types | [Agreed] | language | DN §3.3, §8.1 | SP5 |  | EXP-10, EXP-39 |
| D-086 | Conversion intrinsics require a known source type | Agreed | [Agreed] | language | DN §3.3 | SP5 |  | EXP-31 |
| D-087 | No widening to avoid intermediate arithmetic failure | Agreed | [Agreed] | language | DN §3.3 | SP5 |  | EXP-3, EXP-12, EXP-23 |
| D-088 | Signed minimum / -1 | Trap; checked_div returns arithmetic error | [Agreed] | language | DN §3.5, §6.5 | SP5 |  | EXP-24 |
| D-089 | Signed minimum % -1 | Defined zero; checked_rem succeeds | [Agreed] | language | DN §6.5 | SP5 |  | EXP-24 |
| D-090 | Unary negation | Signed only; unrepresentable negation traps | [Agreed] | language | DN §6.5 | SP5 |  | EXP-8, EXP-19, EXP-25 |
| D-091 | Checked arithmetic | add/sub/mul/div/rem/neg intrinsics return outcomes | [Agreed] | language | DN §6.5 | SP5 | OI-13 | EXP-29 |
| D-092 | Wrapping arithmetic | add/sub/mul intrinsics return direct modular values | [Agreed] | language | DN §6.5 | SP5 |  | EXP-30 |
| D-093 | Checked/wrapping arithmetic intrinsics in constants | Excluded initially | [Agreed] | language | DN §3.10, §6.5 | SP4 |  | CEX-5 |
| D-094 | Constant expressions | Deterministic side-effect-free subset; see section 3.10 | [Agreed] | language | DN §3.10 | SP4 |  | CEX-3, CEX-6 |
| D-095 | Guaranteed convert<T> in constant expressions | Agreed; constant operand with independently known source type; full source range must fit target | [Agreed] | language | DN §3.10 | SP4 |  | CEX-3 |
| D-096 | checked_convert<T> in constant expressions | Excluded initially; no compile-time outcome handling | [Agreed] | language | DN §3.10 | SP4 |  | CEX-5 |
| D-097 | Constant-evaluation boundary algorithm | Structural policy proposed in section 3.10; detailed acceptance examples pending validation | [Agreed] (via D-411) | language | DN §3.10 | SP4 | OI-11 | CEX-7 |
| D-098 | Constant dependencies | Forward references allowed; cycles are compilation errors | [Agreed] | language | DN §3.10 | SP4 |  | CEX-12, CEX-13 |
| D-099 | Fixed-array lengths | Unsigned constant expressions; literal-only expressions use u32 context | [Agreed] | language | DN §3.10 | SP4 |  | TYP-19, CEX-6 |
| D-100 | No implicit boolean/numeric, array or structure conversions | Agreed | [Agreed] | language | DN §3.4 | SP3 |  | TYP-5, TYP-7 |
| D-101 | No general truncating cast initially | Agreed | [Agreed] | language | DN §3.2 | SP5 |  | EXP-35 |
| D-102 | Mixed binary operators require parentheses; no binary precedence hierarchy | Agreed | [Agreed] | language | DN §3.5 | SP5 |  | EXP-1, EXP-2, EXP-5 |
| D-103 | Same-operator chains evaluate left to right; comparison chains forbidden | Agreed | [Agreed] | language | DN §3.5 | SP5 |  | EXP-3, EXP-4 |
| D-104 | Left-to-right evaluation and short-circuit boolean logic | Agreed | [Agreed] | language | DN §3.5 | SP5 |  | EXP-20, EXP-21, EXP-50 |
| D-105 | Assignment is a statement, not an expression | Agreed | [Agreed] | language | DN §3.5 | SP6 |  | STM-6 |
| D-106 | Control flow: `if`, `while`, range `for`, `match`, `break`, `continue`, `return` | Agreed | [Agreed] | language | DN §3.6 | SP6 |  | STM-1, STM-11, STM-12, STM-13, STM-14, STM-15 |
| D-107 | Explicit `return Ok(value)` / `return Err(error)`; no implicit success | Agreed | [Agreed] | language | DN §3.6, §3.7 | SP8 |  | OUT-3, OUT-4 |
| D-108 | Exhaustive result matching; read-only loop and pattern bindings | Agreed | [Agreed] | language | DN §3.6 | SP8 |  | OUT-12, OUT-13 |
| D-109 | No `return`, `break` or `continue` across transaction boundaries | Agreed | [Agreed] | language | DN §3.6, §7.2 | SP10 |  | TXN-6 |
| D-110 | Explicit recoverable transaction exit: `abort Err(error);` | Agreed; roll back persistent changes and return Err from the enclosing function/command | [Agreed] | language | DN §7.2 | SP10 |  | TXN-7, TXN-8 |
| D-111 | `abort` scope | Lexically inside a transaction only; helpers return Err for the transaction owner to handle | [Agreed] | language | DN §7.2 | SP10 |  | TXN-7 |
| D-112 | Parameters: by value, read-only `ref`, mutable `inout` | Agreed | [Agreed] | language | DN §3.7 | SP7 |  | FUN-1, FUN-6 |
| D-113 | Reference modes explicit at declaration and call site | Agreed | [Agreed] | language | DN §3.7 | SP7 |  | FUN-7 |
| D-114 | References are call-scoped; no raw pointers or escaping references | Agreed | [Agreed] | language | DN §3.7, §3.8 | SP7 |  | FUN-6, FUN-16 |
| D-115 | Reference permissions | ref is read-only through that path; inout permits reads/writes; neither grants exclusivity | [Agreed] | language | DN §3.7, §3.8 | SP7 |  | FUN-6, FUN-10, FUN-12, FUN-15 |
| D-116 | Assignment/value parameters/value returns create independent values | Agreed | [Agreed] | language | DN §3.8 | SP7 |  | EXP-46, STM-8, FUN-6, FUN-17 |
| D-117 | References may target variables, fields and array elements; not temporaries | Agreed | [Agreed] | language | DN §3.8 | SP7 |  | FUN-9 |
| D-118 | Reference and slice overlap | Allowed, including mutable overlap; no overlap checks or overlap traps | [Agreed] | language | DN §3.8, §8.4 | SP7 |  | FUN-12, FUN-13 |
| D-119 | Array slices `array[start..end]` | Agreed; half-open borrowed regions, bounds checked; empty slices allowed | [Agreed] | language | DN §8.4 | SP7 | OI-10 | FUN-18, FUN-20 |
| D-120 | Unspecified-size parameters `ref T[]` / `inout T[]` | Agreed; runtime u32 length, exact element type, no backing-array copy | [Agreed] | language | DN §8.4 | SP7 |  | TYP-21, FUN-8, FUN-21 |
| D-121 | By-value array parameters | Fixed-size T[N] only | [Agreed] | language | DN §8.4 | SP7 |  | TYP-21, FUN-8 |
| D-122 | Mutable global declaration initializers | Forbidden for persistent/session state | [Agreed] | language | DN §3.9 | SP9 |  | STA-2 |
| D-123 | Automatic defaults | New persistent/session state and uninitialized locals: zero/false recursively | [Agreed] | language | DN §3.9 | SP9 |  | TYP-22, STM-5, STA-3, STA-4 |
| D-124 | Application-specific global setup | Lifecycle handlers; event API deferred to platform | [Agreed] | language | DN §3.9; PN §3 | SP9 | OI-7 | STA-5 |
| D-125 | Runtime resources | Application-chosen u32 identifiers; 0 invalid; runtime-owned objects | [Agreed] | platform | DN §11.2; PN §2 | SP13 |  | PLT-20 |
| D-126 | Resource identifier space | One per isolated application, covering all resource kinds | [Agreed] | platform | DN §11.2; PN §2 | SP13 |  | PLT-2, PLT-20 |
| D-127 | Resource storage strategy and cleanup | Platform decisions; identifier API does not require a heap | [Agreed] | platform | DN §11.2; PN §2 | SP13 | OI-20 | PLT-24 |
| D-128 | Array/structure defaults apply recursively | Agreed | [Agreed] | language | DN §3.9 | SP9 |  | TYP-22, STM-5, STA-3, STA-4 |
| D-129 | Global const requires an explicit initializer | Agreed | [Agreed] | language | DN §3.9, §3.10 | SP4 |  | CEX-1 |
| D-130 | Explicit array/structure construction remains complete | Agreed for constants, local initializers and assignments | [Agreed] | language | DN §3.9, §9.3 | SP5 |  | EXP-43, EXP-45 |
| D-131 | Nested transactions, including through function calls | Forbidden initially | [Agreed] | language | DN §7.3 | SP10 | OI-3 | TXN-10 |
| D-132 | Callee persistent assignments participate in an active transaction | Agreed | [Agreed] | language | DN §7.3 | SP10 |  | TXN-1 |
| D-133 | By-value aggregate parameters | Temporary application RAM; call-frame placement proposed | [Agreed]; placement informative (D-421) | VM/profile | DN §3.8; PN §4 | SP13 | OI-21 | FUN-17, Annex B §B.11 |
| D-134 | Familiar imperative syntax, static types | Proposed baseline | [Proposal] | language | DN §3 | SP0 |  | 01 §1.1 (informative) |
| D-135 | Compact custom VM with single-digit KiB RAM goals | Feasibility direction; unmeasured | [Proposal] | VM/profile | PN §4 | SP13 |  | Annex B §B.11 (informative) |

## Platform-notes items (D-201…)

| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |
|---|---|---|---|---|---|---|---|---|
| D-201 | No opaque platform value types; platform APIs use ordinary value types, with fully visible platform-supplied configuration structures and algorithm enums | (summary; see sources) | [Agreed] | platform | PN §2; DN §11.1 | SP13 |  | PLT-21 |
| D-202 | Every resource operation validates existence, kind, state and permissions in the caller's resource space; wrong kind is a defined recoverable error; identifiers never authorize cross-application access | (summary; see sources) | [Agreed] | platform | PN §2; DN §11.1 | SP13 |  | PLT-20, PLT-22 |
| D-203 | Resource operation outcomes: create on existing ID fails recoverably (never replaces); unknown ID and wrong kind fail recoverably; capacity failure is a defined recoverable error; failed creation exposes no partial object (error names are placeholders) | (summary; see sources) | [Agreed] | platform | PN §2; DN §11.2 | SP13 | OI-15 | PLT-22 |
| D-204 | Copying a resource identifier copies only the number; no stale-handle detection; identifier-variable lifetime is independent of resource lifetime | (summary; see sources) | [Agreed] | platform | PN §2; DN §11.2 | SP13 |  | PLT-20, PLT-22, PLT-23 |
| D-205 | Language transactions do not automatically cover resource-API effects; each API must define its transaction participation or prohibit use during a transaction | (summary; see sources) | [Agreed] | platform | PN §2, §5; DN §7.2 | SP13 |  | TXN-4, TXN-17, PLT-24 |
| D-206 | Exceeding a runtime stack/execution limit traps; exceeding build/load capacity may reject the application; limits must not silently change language semantics | (summary; see sources) | [Agreed] | language | PN §4; DN §12 | SP12 |  | TYP-23, STA-13, TXN-16, RTF-6, RTF-7, RTF-8 |
| D-207 | Commit failure never resumes after the block; a contained failure traps, an integrity failure triggers security reset; recovery exposes all or none of a transaction and fails closed | (summary; see sources) | [Agreed] | language | PN §5; DN §7.2 | SP10 |  | TXN-12, TXN-13 |
| D-208 | The platform must prevent any other execution context (callbacks, reentrant commands) from observing partially updated transactional state | (summary; see sources) | [Agreed] | platform | PN §5 | SP13 |  | TXN-14, PLT-5 |
| D-209 | Published application/platform error-code meanings remain stable; codes are nonzero u16 values in separate categories | (summary; see sources) | [Agreed] | language | PN §5; DN §6.3 | SP12 | OI-15 | OUT-17, RTF-11 |

## DN body-only decisions (D-301…)

Sub-plans add rows here as they reach each DN section.

| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |
|---|---|---|---|---|---|---|---|---|
| D-301 | Identifiers are case-sensitive ASCII: first character a letter or underscore, then letters, digits or underscores | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-12 |
| D-302 | `_` alone is reserved for an ignored pattern | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-14 |
| D-303 | No escaped or Unicode identifiers; keywords cannot be identifiers | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-12, LEX-13 |
| D-304 | Comments may contain Unicode; identifiers and language tokens are ASCII | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-3 |
| D-305 | Spaces, tabs and line breaks separate tokens; indentation has no semantic meaning | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-6 |
| D-306 | Line comments `//` and block comments `/* */`; block comments do not nest; an unterminated block comment is a compilation error | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-7, LEX-8, LEX-9 |
| D-307 | Integer literals are decimal, hexadecimal or binary; a leading zero does not mean octal | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-17 |
| D-308 | Numeric underscores appear only between digits: no leading, trailing or consecutive underscores, and none directly after a base prefix | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-17, LEX-18 |
| D-309 | No negative-literal token; negative values use unary `-` | Agreed (DN body text) | [Agreed] | language | DN §3.0, §6.5 | SP1 |  | LEX-20 |
| D-310 | Boolean literals are exactly `true` and `false`; no string, character, floating-point or null literals | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-21 |
| D-311 | File and line boundaries are preserved for diagnostics; a trailing comment or token cannot consume the next file's text | Agreed (DN body text) | [Agreed] | language | DN §3.0, §4.1 | SP1 |  | LEX-5, LEX-11 |
| D-312 | Semicolons are mandatory; there is no automatic semicolon insertion | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP1 |  | LEX-23 |
| D-313 | A declaration cannot span source files | Agreed (DN body text) | [Agreed] | language | DN §3.0 | SP2 |  | NAM-2 |
| D-314 | Functions and types may be used before their declaration, including across files | Agreed (DN body text) | [Agreed] | language | DN §4.1, §4.2 | SP2 |  | NAM-4, NAM-13 |
| D-315 | Shadowing any visible name is forbidden (application declarations, parameters, locals, loop and pattern bindings); same-scope duplicates are errors; sibling scopes may reuse names | Agreed (DN body text) | [Agreed] | language | DN §3.6, §4.2 | SP2 |  | NAM-21 |
| D-316 | Function, command, structure, enum and error-set declarations are top-level only | Agreed (DN body text) | [Agreed] | language | DN §4.2 | SP2 |  | NAM-7 |
| D-317 | Field names never become bare names; dot access resolves from the receiver's type | Agreed (DN body text) | [Agreed] | language | DN §4.2 | SP2 |  | NAM-17 |
| D-318 | Enum variants and error members are always qualified (`Owner.Member`) and are never imported as bare names | Agreed (DN body text) | [Agreed] | language | DN §3.11, §4.2, §6.3 | SP2 |  | NAM-16 |
| D-319 | Platform-supplied configuration structures and algorithm enums use the ordinary naming rules, with no imports, namespaces or private fields | Agreed (DN body text) | [Agreed] | language | DN §11.1 | SP2 |  | NAM-14 |
| D-320 | Plain `var` and combined qualifiers are forbidden at application scope; there is no `local` keyword | Agreed (DN body text) | [Agreed] | language | DN §5.1 | SP2 |  | NAM-9, NAM-10 |
| D-321 | Arrays are composite types, not extra primitive scalar types; enums and structures are user-defined types | Agreed (DN body text) | [Agreed] | language | DN §3.1 | SP3 |  | TYP-1 |
| D-322 | Every array length is a positive unsigned constant expression whose value fits in `u32` | Agreed (DN body text) | [Agreed] | language | DN §8.1, §8.2 | SP3 |  | TYP-19 |
| D-323 | Unsized array types `T[]` exist only as `ref`/`inout` parameter types; no unsized owned variables, fields or returns | Agreed (DN body text) | [Agreed] | language | DN §8.4 | SP3 |  | TYP-2, TYP-21 |
| D-324 | Structure field types are integers, booleans, enums, arrays and other structures; no methods, inheritance, field defaults or field-level storage qualifiers | Agreed (DN body text) | [Agreed] | language | DN §9, §9.3 | SP3 |  | TYP-14 |
| D-325 | A type declaration does not define physical layout, wire encoding or durable encoding; enum representation and variant order are not a stable encoding | Agreed (DN body text) | [Agreed] | language | DN §3.9, §3.11, §9.2, §9.3 | SP3 |  | TYP-9 |
| D-326 | Constant evaluation is deterministic and side-effect-free; no user-defined compile-time functions | Agreed (DN body text) | [Agreed] | language | DN §3.10 | SP4 |  | CEX-3, CEX-5, CEX-12 |
| D-327 | Qualified enum variants are constant expressions; equality of constant enum values is constant-evaluable | Agreed (DN body text) | [Agreed] | language | DN §3.11 | SP4 |  | CEX-3 |
| D-328 | `.length` of a fixed array through a plain variable/field path is constant without reading contents; more complex receivers must satisfy the constant restrictions | Agreed (DN body text) | [Agreed] | language | DN §3.10 | SP4 |  | CEX-4 |
| D-329 | Compile-time evaluation preserves short-circuiting; skipped operands are still name-resolved and type-checked | Agreed (DN body text) | [Agreed] | language | DN §3.10 | SP4 |  | CEX-11 |
| D-330 | Global constants need no writable state and their representation is an implementation detail; a constant may be passed through `ref`, never `inout` | Agreed (DN body text) | [Agreed] | language | DN §3.8, §5.1 | SP4 |  | CEX-2, FUN-10 |
| D-331 | The nested-call ban applies in constant expressions; nested conversions use intermediate constants | Agreed (DN body text) | [Agreed] | language | DN §3.10 | SP4 |  | CEX-14 |
| D-332 | Constant expressions never read persistent or session contents | Agreed (DN body text) | [Agreed] | language | DN §3.10 | SP4 |  | CEX-5 |
| D-333 | A typed operand supplies the expected type for an untyped literal operand on either side; a Boolean result expectation alone does not establish integer widths; missing or ambiguous context is an error | Agreed (DN body text) | [Agreed] | language | DN §3.3 | SP5 |  | EXP-11 |
| D-334 | A minimum signed literal such as `-128` is accepted in an `i8` context; negating a minimum signed runtime value traps | Agreed (DN body text) | [Agreed] | language | DN §3.0, §6.5 | SP5 |  | EXP-8, EXP-25 |
| D-335 | Equality applies to matching integer types, `bool` and the same enum; no automatic array or structure equality | Agreed (DN body text) | [Agreed] | language | DN §3.5, §3.11, §8.2, §9.3 | SP5 |  | EXP-15, EXP-28 |
| D-336 | Bitwise operators accept only unsigned operands of matching type; shifts take an unsigned left operand and a `u8` count | Agreed (DN body text) | [Agreed] | language | DN §3.5 | SP5 |  | EXP-17, EXP-18, EXP-26, EXP-27 |
| D-337 | Calls, indexing and field access form operands; unary operators need no parentheses because a binary operator is present | Agreed (DN body text) | [Agreed] | language | DN §3.5 | SP5 |  | EXP-1 |
| D-338 | Optimizations preserve evaluation, short-circuiting and failure behavior; checks are removed only when proved unnecessary; no build-mode variation | Agreed (DN body text) | [Agreed] | language | DN §3.5, §6.5 | SP5 |  | EXP-22 |
| D-339 | Runtime `.length` evaluates its receiver, preserving calls, errors and bounds checks | Agreed (DN body text) | [Agreed] | language | DN §8.1 | SP5 |  | EXP-40 |
| D-340 | `fill` needs an expected fixed-array type; evaluates its argument once; copies independently; self-source fill captures the original value | Agreed (DN body text) | [Agreed] | language | DN §8.3 | SP5 |  | EXP-44 |
| D-341 | Array lists must have exactly the destination length; no padding or truncation | Agreed (DN body text) | [Agreed] | language | DN §8 | SP5 |  | EXP-43 |
| D-342 | Integer-to-byte encoding is explicit, separate from numeric conversion, and must state byte order | Agreed (DN body text) | [Agreed] | language | DN §3.4 | SP5 |  | EXP-36, EXP-37, EXP-38 |
| D-343 | Braces are mandatory on every control-flow body and match arm; conditions must be `bool`; parentheses around a whole condition are optional | Agreed (DN body text) | [Agreed] | language | DN §3.6 | SP6 |  | STM-1, STM-11 |
| D-344 | No `switch`, fall-through, `goto`, labelled loops or multi-level exits; `if` and `match` are statements | Agreed (DN body text) | [Agreed] | language | DN §3.6 | SP6 |  | STM-1, STM-16 |
| D-345 | `for` uses a half-open ascending unit-step range; bounds evaluated once left to right; zero iterations when start >= end; read-only index local to the body; endpoints must fit the index type | Agreed (DN body text) | [Agreed] | language | DN §3.6 | SP6 |  | STM-13, STM-14 |
| D-346 | `continue` in a `while` rechecks the condition; in a `for` it advances the index | Agreed (DN body text) | [Agreed] | language | DN §3.6 | SP6 |  | STM-15 |
| D-347 | Infinite loops are written `while true`; termination need not be proved; execution-budget exhaustion traps | Agreed (DN body text) | [Agreed] | language | DN §3.6 | SP6 |  | STM-12 |
| D-348 | `require c else E;` is exactly `if not c { return Err(E); }` | Agreed (DN body text) | [Agreed] | language | DN §3.6 | SP6 |  | STM-19 |
| D-349 | No chained assignment, increment/decrement operators or assignment in conditions; compound assignment is deferred | Agreed (DN body text) | [Agreed] | language | DN §3.5 | SP6 |  | STM-6 |
| D-350 | An explicit local initializer is not preceded by a default; a failed initializer has no default fallback; uninitialized locals default each time their declaration is reached | Agreed (DN body text) | [Agreed] | language | DN §3.9 | SP6 |  | STM-5 |
| D-351 | Unreachable statements are permitted and still checked | Agreed (DN body text) | [Agreed] | language | DN §3.10 | SP6 |  | STM-22 |
| D-352 | Ordinary functions may access globals, call platform APIs and open transactions; no purity or effect annotations and no `pure`, `static` or `public` modifiers | Agreed (DN body text) | [Agreed] | language | DN §3.7 | SP7 |  | FUN-3, FUN-22 |
| D-353 | All arguments are evaluated left to right and reference/slice regions established and bounds-checked before the callee starts; regions are not re-evaluated during the call | Agreed (DN body text) | [Agreed] | language | DN §3.7, §8.4 | SP7 |  | FUN-11 |
| D-354 | Forwarding: `ref` to `ref`; `inout` to `ref` or `inout`; fields, elements and slices forwarded alike; never strengthens permissions or extends lifetime | Agreed (DN body text) | [Agreed] | language | DN §3.8, §8.4 | SP7 |  | FUN-15 |
| D-355 | References and views end with their call on Ok or Err; frames terminated by a trap discard their references | Agreed (DN body text) | [Agreed] | language | DN §3.8 | SP7 |  | FUN-16 |
| D-356 | Storage identity survives reference passing: a write through `inout` to persistent storage is a persistent write; Err does not undo earlier mutations | Agreed (DN body text) | [Agreed] | language | DN §3.7, §3.8 | SP7 |  | FUN-23 |
| D-357 | Compilers preserve observable aliasing effects; no assumption that `ref` storage is stable or `inout` storage unaliased; no substituted copies | Agreed (DN body text) | [Agreed] | language | DN §3.7, §3.8 | SP7 |  | FUN-14 |
| D-358 | Physical copies may be removed only when behavior is unchanged; sharing is never substituted for copying | Agreed (DN body text) | [Agreed] | language | DN §3.8 | SP7 |  | FUN-17 |
| D-359 | Inside the callee a view is indexed from 0 and its `.length` is the region length; a parameter cannot resize or rebind its region; a view may be narrowed to a slice within its region | Agreed (DN body text) | [Agreed] | language | DN §8.4 | SP7 |  | FUN-21 |
| D-360 | An outcome match has exactly one success arm, zero or more specific error arms and one mandatory final catch-all (`Err(name)` or `Err(_)`); specific errors precede the catch-all; listing every known error does not make the catch-all optional | Agreed (DN body text) | [Agreed] | language | DN §3.6, §6.3 | SP8 |  | OUT-12 |
| D-361 | Pattern vocabulary: `Ok(name)`, `Ok(_)`, `Ok()`, `Err(Set.Member)`, `Err(name)`, `Err(_)`; no guards, alternatives, ranges, nested patterns or destructuring | Agreed (DN body text) | [Agreed] | language | DN §3.6 | SP8 |  | OUT-11 |
| D-362 | Success payload bindings are independent read-only arm-local copies | Agreed (DN body text) | [Agreed] | language | DN §3.6 | SP8 |  | OUT-13 |
| D-363 | `Ok` and `Err` are restricted syntax for returns, `abort` and patterns, not general constructors | Agreed (DN body text) | [Agreed] | language | DN §6.3 | SP8 |  | OUT-6 |
| D-364 | `attempt` propagates the error unchanged regardless of the enclosing payload type and never catches traps | Agreed (DN body text) | [Agreed] | language | DN §6.3 | SP8 |  | OUT-10 |
| D-365 | Application errors carry identity only (no strings or payloads); names and codes are unique within the error set | Agreed (DN body text) | [Agreed] | language | DN §6.3 | SP8 |  | OUT-16, OUT-18 |
| D-366 | Published error codes must not change meaning or be reused after removal | Agreed (DN body text) | [Agreed] | language | DN §6.3; PN §5 | SP8 |  | OUT-17 |
| D-367 | Platform errors use the reserved `CardError` namespace, which applications cannot impersonate; no application-origin field; propagation preserves category and code | Agreed (DN body text) | [Agreed] | language | DN §6.3 | SP8 |  | OUT-18, OUT-19 |
| D-368 | Returning or propagating `Err` is not a rollback request; earlier persistent and session changes remain | Agreed (DN body text) | [Agreed] | language | DN §6.3, §7.2 | SP8 |  | OUT-20 |
| D-369 | Persistent defaults apply once, when persistent state is first created; never reapplied on reset or command | Agreed (DN body text) | [Agreed] | language | DN §3.9 | SP9 |  | STA-3 |
| D-370 | Setup writing persistent values is distinct from volatile setup; the platform decides when provisioning runs and how interruption and activation are handled | Agreed (DN body text) | [Agreed] | language | DN §3.9; PN §3 | SP9 |  | STA-5 |
| D-371 | A persistent assignment is atomic: after interruption the destination holds its complete old or complete new value; a failed right-hand side means no update and its side effects are not undone | Agreed (DN body text) | [Agreed] | language | DN §7.1 | SP9 |  | STA-11, STA-12 |
| D-372 | Two persistent assignments are not collectively atomic without a transaction; atomicity is not a single hardware write and does not make a command atomic | Agreed (DN body text) | [Agreed] | language | DN §7.1 | SP9 |  | STA-12 |
| D-373 | Whole-structure and whole-array assignment, including fill, is atomic for the whole destination | Agreed (DN body text) | [Agreed] | language | DN §7.1, §8.2, §8.3, §9.3 | SP9 |  | STA-11 |
| D-374 | Global means application-wide; scope and lifetime are separate; session state is shared within its application | Agreed (DN body text) | [Agreed] | language | DN §5, §5.1 | SP9 |  | STA-1 |
| D-375 | Reaching the closing brace commits; execution continues after the block only after a successful commit; an empty transaction is valid | Agreed (DN body text) | [Agreed] | language | DN §7.2 | SP10 |  | TXN-3 |
| D-376 | Reads within a transaction see earlier writes, including through references and called functions | Agreed (DN body text) | [Agreed] | language | DN §7.2 | SP10 |  | TXN-2 |
| D-377 | Only persistent state participates; session state and locals are not restored; resource-API effects participate only where their API says so | Agreed (DN body text) | [Agreed] | language | DN §7.2; PN §5 | SP10 |  | TXN-4 |
| D-378 | A callee's Err is not an abort request; pending changes remain and commit if the closing brace is reached | Agreed (DN body text) | [Agreed] | language | DN §7.2 | SP10 |  | TXN-9 |
| D-379 | abort stops the body, rolls back pending persistent writes and returns the error unchanged from the enclosing function or command; session changes and earlier commits remain; no savepoints | Agreed (DN body text) | [Agreed] | language | DN §7.2 | SP10 |  | TXN-8 |
| D-380 | The abort operand is a named error member or an in-scope error binding; abort is a statement; bare abort, abort error and abort Ok are invalid | Agreed (DN body text) | [Agreed] | language | DN §7.2 | SP10 |  | TXN-7 |
| D-381 | break/continue targeting a loop entirely inside the transaction is valid; returning from a called function does not exit the caller's transaction | Agreed (DN body text) | [Agreed] | language | DN §3.6 | SP10 |  | TXN-6 |
| D-382 | A trap inside a transaction rolls back its pending persistent writes and aborts the command | Agreed (DN body text) | [Agreed] | language | DN §6.4, §7.2 | SP10 |  | TXN-11 |
| D-383 | A command is not implicitly a transaction | Agreed (DN body text) | [Agreed] | language | DN §4, §7.2 | SP10 |  | TXN-5 |
| D-384 | `request.length` is the number of bytes received; `response.length` is the output capacity | Agreed (DN body text) | [Agreed] | language | DN §4 | SP11 |  | HEP-5, HEP-6 |
| D-385 | The platform supplies separate, non-overlapping request and response regions valid only for the invocation; the application cannot resize them; the host cannot pass references into card memory | Agreed (DN body text) | [Agreed] | language | DN §4 | SP11 |  | HEP-7 |
| D-386 | The application must write every response byte it includes in the count; no initial response contents are promised | Agreed (DN body text) | [Agreed] | language | DN §4 | SP11 |  | HEP-8 |
| D-387 | Response data is transmitted only after successful completion and count validation; a count above `response.length` traps with no payload; Err or a trap suppresses any partial payload; bytes beyond the count are never sent | Agreed (DN body text) | [Agreed] | language | DN §4, §6.3 | SP11 |  | HEP-9 |
| D-388 | Ok means a response was produced, not that the business operation succeeded; protocol failures may be encoded in the payload | Agreed (DN body text) | [Agreed] | language | DN §4 | SP11 |  | HEP-11 |
| D-389 | No automatic serialization of language values and no automatic dispatch of operation identifiers | Agreed (DN body text) | [Agreed] | language | DN §4 | SP11 |  | HEP-15 |
| D-390 | The returned u32 is a byte count, not a status word; errors keep category and code and the platform maps them to the wire status | Agreed (DN body text) | [Agreed] | language | DN §4 | SP11 |  | HEP-9, HEP-12 |
| D-391 | A reset or power loss may prevent any response; no internal VM details are disclosed to the host | Agreed (DN body text) | [Agreed] | language | DN §4, §6.3 | SP11 |  | HEP-12 |
| D-392 | A trap ends only the current command; subsequent commands may run; serial execution does not make a command an implicit transaction | Agreed (DN body text) | [Agreed] | language | DN §4 | SP11 |  | HEP-14 |
| D-393 | Response transmission never happens inside a transaction; response-buffer writes are ordinary volatile writes | Agreed (DN body text) | [Agreed] | language | DN §7.4 | SP11 |  | HEP-10 |
| D-394 | A trap aborts the current command and cannot be caught by application `match` or `attempt` | Agreed (DN body text) | [Agreed] | language | DN §6.4 | SP12 |  | RTF-1 |
| D-395 | Session state may be partially updated when a command traps; this is intentional and visible in the specification | Agreed (DN body text) | [Agreed] | language | DN §6.4 | SP12 |  | RTF-2 |
| D-396 | Defined trap cases: arithmetic failures, out-of-bounds access, invalid shift counts, stack or execution-budget exhaustion, attempted nested transactions, invalid VM instructions or state | Agreed (DN body text) | [Agreed] | language | DN §6.4 | SP12 |  | RTF-4 |
| D-397 | A security reset clears volatile state across all applications and is never returned as a `CardError` | Agreed (DN body text) | [Agreed] | language | DN §6.4 | SP12 |  | RTF-9 |
| D-398 | Failures may terminate execution without an outcome while the persistent atomicity guarantees still hold | Agreed (DN body text) | [Agreed] | language | DN §6.4 | SP12 |  | RTF-10 |
| D-399 | An ordinary trap does not trigger a lifecycle reset | Agreed (DN body text) | [Agreed] | language | DN §6.4; PN §3 | SP12 |  | RTF-3 |

## Open-issue resolutions (D-401…)

| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |
|---|---|---|---|---|---|---|---|---|
| D-401 | Source file extension is `.card` | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-1 | SP1 | OI-1 | LEX-1 |
| D-402 | No platform dispatch within an application; PN §1 row superseded | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-2 | SP13 | OI-2 | HEP-15, PLT-3 |
| D-403 | Nested transactions rejected statically by a structural call-graph rule | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-3 | SP10 | OI-3 | TXN-10 |
| D-404 | Keyword list; Ok/Err keywords; intrinsics and card/CardError reserved | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-4 | SP1 | OI-4 | LEX-13, LEX-15, NAM-14 |
| D-405 | Entry point is the single `command` declaration, any name | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-5 | SP11 | OI-5 | HEP-1, HEP-16 |
| D-406 | Platform API calls use the reserved `card.` path form | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-6 | SP2 | OI-6 | NAM-17, NAM-18 |
| D-407 | Lifecycle handlers use platform-reserved function names/signatures | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-7 | SP9 | OI-7 | STA-5 |
| D-408 | `attempt` allowed in any runtime expression position, with three exclusions | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-8 | SP5 | OI-8 | EXP-51, OUT-8, OUT-10 |
| D-409 | Assignment: destination path first, then RHS, then store | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-9 | SP6 | OI-9 | STM-9 |
| D-410 | Slice endpoint typing, order, positions and limits fixed | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-10 | SP7 | OI-10 | EXP-42, FUN-8, FUN-18, FUN-19, FUN-20 |
| D-411 | Constant-evaluation algorithm normative; constant OOB index is a compile error | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-11 | SP4 | OI-11 | CEX-7, CEX-10 |
| D-412 | No `byte` alias in Draft 0.1 | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-12 | SP3 | OI-12 | TYP-20 |
| D-413 | Zero or one error set; intrinsic outcomes may be forwarded | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-13 | SP8 | OI-13 | OUT-5, OUT-15 |
| D-414 | Literal prefix, digit and magnitude rules | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-14 | SP1 | OI-14 | LEX-17, LEX-18, LEX-19, EXP-7 |
| D-415 | Trap-kind and placeholder platform-error names | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-15 | SP12 | OI-15 | EXP-29, EXP-33, RTF-4, PLT-27, PLT-28 |
| D-416 | Persistent deletion/upgrade/migration are platform-defined | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-16 | SP9 | OI-16 | STA-3, PLT-16 |
| D-417 | Large-data object API is future platform work | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-17 | SP13 | OI-17 | PLT-17 |
| D-418 | Outcome typing settled by DN §6.3 | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-18 | SP8 | OI-18 | OUT-1, OUT-2 |
| D-419 | Oversized atomic aggregate assignment rejected at build/load time | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-19 | SP9 | OI-19 | STA-13 |
| D-420 | Resource storage strategy is platform-defined | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-20 | SP13 | OI-20 | PLT-24 |
| D-421 | Call-frame placement is informative VM guidance | Resolved by user 2026-11-15 | [Agreed] | VM/profile | Annex C OI-21 | SP13 | OI-21 | FUN-17, Annex B §B.11 (informative) |
| D-423 | Leading UTF-8 byte-order mark ignored; LF, CR and CRLF are line breaks (CRLF counts once) | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-23 | SP1 | OI-23 | LEX-4, LEX-5 |
| D-424 | Longest-match tokens; numeric-run rule for literals; no identifier length limit | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-24 | SP1 | OI-24 | LEX-10, LEX-16, LEX-18 |
| D-425 | Primitive type names are predeclared names in every application scope, not keywords | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-25 | SP2 | OI-25 | NAM-14 |
| D-426 | A file listed twice is a build-configuration error; an empty file list is allowed by the language | Resolved by user 2026-11-15 | [Agreed] | tooling | Annex C OI-26 | SP2 | OI-26 | NAM-3 |
| D-427 | Storage representation of values (Booleans, enums, layouts) is not language-visible; persistent layout across upgrades is platform-defined | Resolved by user 2026-11-15 | [Agreed] | platform | Annex C OI-27 | SP3 | OI-27 | TYP-9 |
| D-428 | Error-member codes are integer literals (u16 context), not general constant expressions | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-28 | SP8 | OI-28 | CEX-6, OUT-16 |
| D-429 | Constant slice endpoints on an array of type-known length are checked at compile time | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-29 | SP4 | OI-29 | CEX-10 |
| D-430 | A structure constructor directly in an if/while condition, for range bound or match scrutinee must be parenthesized | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-30 | SP5 | OI-30 | EXP-6 |
| D-431 | Arithmetic failure classes: above maximum is Overflow; below minimum (incl. unsigned subtraction) is Underflow; signed minimum / -1 is Overflow; negating the signed minimum is TRAP-NEGATION and checked_neg returns CardError.Overflow | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-31 | SP5 | OI-31 | EXP-23, EXP-24, EXP-25, EXP-29 |
| D-432 | Add truncate<T>(x) and value-based byte-order intrinsics encode_be/encode_le and decode_be/decode_le<T>; direct values; excluded from constant expressions initially | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-32 | SP5 | OI-32 | EXP-34, EXP-36, EXP-37, LEX-15, NAM-14, CEX-5 |
| D-433 | Only `attempt call;` is an expression statement; any other expression statement is a compilation error | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-33 | SP6 | OI-33 | STM-2 |
| D-434 | No standalone block statements in Draft 0.1 | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-34 | SP6 | OI-34 | STM-3 |
| D-435 | A `for` index or pattern binding may be passed as `ref`, never `inout` | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-35 | SP7 | OI-35 | FUN-9, FUN-10 |
| D-436 | An error set must declare at least one member | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-36 | SP8 | OI-36 | OUT-15 |
| D-437 | Application code may name `CardError` members only in `Err` patterns; it propagates platform errors through bindings and never originates them in return, abort or require | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-37 | SP8 | OI-37 | OUT-4, OUT-19, STM-19 |
| D-422 | Lifecycle handlers: not callable from application code; otherwise ordinary functions; names always reserved; defining one is optional unless the platform requires it; wrong signature is a compilation error | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-22 | SP9 | OI-22 | STA-7, STA-8, STA-9, STA-10, NAM-14 |
| D-438 | Placeholder lifecycle handlers on_install() and on_power_on(), no parameters and no payload, until the platform catalog exists | Resolved by user 2026-11-15 | [Agreed] | language | Annex C OI-38 | SP9 | OI-38 | STA-6, NAM-14 |
| D-439 | Exceeding transaction capacity at runtime is trap(TXN-CAPACITY); pending writes roll back; TRAP-TXN-CAPACITY joins the placeholder trap kinds of D-415 | Resolved by user 2026-11-17 | [Agreed] | language | Annex C OI-39 | SP10 | OI-39 | TXN-16 |
| D-440 | A call to a platform API marked not-in-transactions, lexically inside a transaction or reachable from one through the call graph, is a compilation error (CE-TXN-4) | Resolved by user 2026-11-17 | [Agreed] | language | Annex C OI-40 | SP10 | OI-40 | TXN-17 |
| D-441 | The initial contents of the response region are unspecified for the language; the platform must ensure it never holds data from another application or from the platform | Resolved by user 2026-11-17 | [Agreed] | platform | Annex C OI-41 | SP11 | OI-41 | HEP-8, PLT-7 |
| D-442 | An application's maximum stack need is computed; exceeding the target's stack is rejected at build or load time; a runtime stack check remains only as a safety net | Resolved by user 2026-11-17 | [Agreed] | language | Annex C OI-42 | SP12 | OI-42 | RTF-7 |
| D-443 | Annex B defines only the platform API catalog entry requirements; conformance tests use a test-only, non-normative catalog of fictional `card.test.` entries | Resolved by user 2026-11-17 | [Agreed] | platform | Annex C OI-43 | SP13 | OI-43 | PLT-25, PLT-26 |
