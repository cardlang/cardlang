# CardLang: design notes and prototype sketches

Date: 2026-11-13
Status: brainstorming record, not a normative specification

Companion: `cardlang-platform-notes.md` collects platform responsibilities, resource APIs, lifecycle events, VM capacities and implementation targets.

Updated: single byte-oriented host entry point and platform response/status-word reporting, 2026-11-15.

This document preserves the language ideas developed in the conversation. Examples are pseudocode: spellings, typing details and encoding rules remain provisional. “Agreed direction” records an explicit decision; “proposal” records an idea still to validate.

## 1. Project direction

The agreed language name is **CardLang**. Suggested related names are CardLang VM and CardLang SDK. The source extension and compiler executable name are not yet fixed.

Create a complete, open-source programmable card platform, potentially implemented on an MCU. The platform includes a card OS, isolated applications, persistent storage, security services, application management, developer tools and host communication.

The original scope of one tiny task per container has been superseded. Applications retain persistent state and expose one byte-oriented host entry point. Multiple application operations are parsed and dispatched by application code within that entry point, rather than exposed as separate typed commands. The initial platform has one application, or multiple completely isolated applications: no cross-application calls, shared application state, references or application-to-application error propagation. Each application uses only its own state and permitted platform services.

An existing language was considered, but the chosen direction is to explore a custom language. A precise specification and executable conformance examples should support agentic design and implementation.

## 2. Decision record

| Topic | Current status |
| --- | --- |
| Language name: CardLang | Agreed |
| Custom card-oriented language | Agreed direction |
| Global declarations: `persistent`, `session` or `const` | Agreed; exactly one keyword |
| `persistent` and `session` imply mutable state | Agreed |
| Global `const` declares a compile-time constant | Agreed |
| Local value declarations use `var` only | Agreed; local `const` deferred |
| Storage qualifiers inside functions/commands are forbidden | Agreed |
| Explicit persistent state | Agreed direction; detailed semantics open |
| Simple persistent declarations plus an object API for larger data | Preferred direction accepted in discussion; API not designed |
| Recoverable errors through explicit results, execution faults through traps | Agreed direction |
| No general-purpose exceptions initially | Agreed direction |
| Every function returns a success/error result | Agreed direction; detailed typing open |
| Explicit outcome handling uses `match` with `Ok` / `Err` | Agreed |
| Automatic error propagation with `attempt` | Agreed |
| Discarded function outcomes | Compilation error |
| Stored result values / user-visible `Result<T>` | Not supported initially; outcomes must be consumed immediately |
| `attempt` type | Exactly the successful payload type; statement form only for no-payload success |
| One application error set with explicit nonzero `u16` codes | Agreed |
| Application/platform errors and traps have separate reporting categories | Agreed |
| Single application or completely isolated applications | Agreed; no cross-application calls/references/shared state |
| Multiple source files form one application compilation unit | Agreed; explicit file list and build-supplied identity |
| Source files contain complete top-level declarations; no application wrapper | Agreed |
| Source extension `.card`; UTF-8 source, ASCII identifiers | Agreed |
| Mandatory semicolons, braces and named-declaration type annotations | Agreed |
| No-value ordinary function signature | Omit return arrow; the host entry point instead returns a u32 response count |
| Function arguments | Positional only; explicit parameter types and modes; trailing commas allowed |
| Calls inside argument expressions | Forbidden, including intrinsic calls; evaluate into locals first |
| Error pattern bindings | Arm-local propagation only; no ordinary error value type initially |
| Constant-only calculations outside global constants | Compile-time evaluation; evaluated failures are compilation errors |
| Function completion analysis | Conservative structural rules; trapping calculations are not a return exemption |
| Recursion, function values/pointers and user-defined generics | Not supported initially |
| Function prototypes | Not supported; definitions are visible regardless of source order |
| Successful function returns | One supported value or no payload; no tuples or returned references |
| Reachable function fall-through | Compilation error; no implicit success |
| Commands called by application code | Forbidden; shared logic belongs in ordinary functions |
| Integer literals | Decimal, hexadecimal, binary; contextual types; no suffixes |
| No preprocessor/macros/textual includes | Agreed |
| Application declarations and struct fields visible across all source files | Agreed; no per-file privacy |
| User modules/namespaces/imports/exports/classes/access modifiers | Omitted initially |
| File order does not control name resolution or initialization order | Agreed |
| Host entry point | Exactly one command per application; ref u8[] request, inout u8[] response, successful u32 byte count |
| Application protocol | Application parses and dispatches request bytes and encodes response bytes; no generated typed-command serialization |
| Classical smart-card status | Platform reports success/errors/traps through response SW mapping; exact mapping remains platform-defined |
| Platform interface names cannot be redefined | Agreed |
| One shared top-level naming scope for types and values | Agreed; duplicate names forbidden |
| No function overloading or local function/type/error-set definitions | Agreed |
| Fields and error members have owner-specific name scopes | Agreed |
| Local binding visible only after its initializer completes | Agreed |
| Command execution | Agreed; commands never interleave; each finishes or fails before another starts |
| Session state at chip power-on | Agreed; initialize to recursive type defaults |
| Ordinary traps preserve application session state | Agreed; terminated call frames discarded; subsequent commands may execute |
| Runtime-owned resources on ordinary trap | Agreed; no automatic cleanup, deletion or invalidation caused by the trap |
| Session/persistent logical consistency | Application programmer responsibility; no automatic synchronization or repair |
| Runtime-issued security reset | Clears session state; subsequent initialization restores type defaults |
| Transactions roll back persistent changes only | Agreed |
| Fatal platform failure triggers whole-chip security reset | Platform requirement; clears volatile state |
| Each persistent assignment is atomic | Agreed direction; aggregate limits and storage details open |
| Explicit handling of overflow and underflow | Required feature |
| Global/local arrays of supported fixed-size values | Agreed: integers, bool, structs and enums |
| Array type syntax `T[N]` | Agreed |
| Array `.length` | Read-only element count of type `u32`; compile-time known for fixed arrays |
| Array index types | `u8`, `u16` or `u32`; signed indices forbidden |
| Array initialization with `fill(value)` or an exact-length element list | Agreed |
| No special `zero` initializer | Agreed |
| Named structures with typed fields | Agreed; nominal type identity |
| Empty structures | Compilation error initially |
| Enums | Named, nominal, nonempty; no payloads or numeric values |
| Enum defaults | First declared variant |
| Enum matching | All variants explicit, no duplicate or catch-all arms |
| Structure constructors | Direct values; every field exactly once; written-order evaluation |
| Structure array fields accept `fill(value)` and explicit lists | Agreed |
| Structures may contain other structures | Agreed |
| Nested fields inherit instance storage and mutability | Agreed |
| Direct or indirect recursive containment is forbidden | Agreed |
| Primitive types: `u8`, `u16`, `u32`, `i8`, `i16`, `i32`, `bool` | Agreed |
| Byte arrays as `u8[N]` | Agreed |
| Zero-length and direct multidimensional arrays | Forbidden/deferred initially |
| Whole-array assignment | Exact element type and length; independent value copy |
| fill(expression) | Reserved array-construction intrinsic; direct array value, once-and-copy |
| Indexed assignment order | Evaluate/check destination index before right-hand side |
| No implicit conversions between integer types | Agreed |
| Arithmetic and comparisons require matching integer types | Agreed |
| Explicit `convert<T>` and `checked_convert<T>` intrinsics | Agreed |
| Contextual integer literal typing; no guessed default type | Agreed |
| Literal-only array index expressions | u32 context; typed unsigned indices retain their types |
| Conversion intrinsics require a known source type | Agreed |
| No widening to avoid intermediate arithmetic failure | Agreed |
| Signed minimum / -1 | Trap; checked_div returns arithmetic error |
| Signed minimum % -1 | Defined zero; checked_rem succeeds |
| Unary negation | Signed only; unrepresentable negation traps |
| Checked arithmetic | add/sub/mul/div/rem/neg intrinsics return outcomes |
| Wrapping arithmetic | add/sub/mul intrinsics return direct modular values |
| Checked/wrapping arithmetic intrinsics in constants | Excluded initially |
| Constant expressions | Deterministic side-effect-free subset; see section 3.10 |
| Guaranteed convert<T> in constant expressions | Agreed; constant operand with independently known source type; full source range must fit target |
| checked_convert<T> in constant expressions | Excluded initially; no compile-time outcome handling |
| Constant-evaluation boundary algorithm | Structural policy proposed in section 3.10; detailed acceptance examples pending validation |
| Constant dependencies | Forward references allowed; cycles are compilation errors |
| Fixed-array lengths | Unsigned constant expressions; literal-only expressions use u32 context |
| No implicit boolean/numeric, array or structure conversions | Agreed |
| No general truncating cast initially | Agreed |
| Mixed binary operators require parentheses; no binary precedence hierarchy | Agreed |
| Same-operator chains evaluate left to right; comparison chains forbidden | Agreed |
| Left-to-right evaluation and short-circuit boolean logic | Agreed |
| Assignment is a statement, not an expression | Agreed |
| Control flow: `if`, `while`, range `for`, `match`, `break`, `continue`, `return` | Agreed |
| Explicit `return Ok(value)` / `return Err(error)`; no implicit success | Agreed |
| Exhaustive result matching; read-only loop and pattern bindings | Agreed |
| No `return`, `break` or `continue` across transaction boundaries | Agreed |
| Explicit recoverable transaction exit: `abort Err(error);` | Agreed; roll back persistent changes and return Err from the enclosing function/command |
| `abort` scope | Lexically inside a transaction only; helpers return Err for the transaction owner to handle |
| Parameters: by value, read-only `ref`, mutable `inout` | Agreed |
| Reference modes explicit at declaration and call site | Agreed |
| References are call-scoped; no raw pointers or escaping references | Agreed |
| Reference permissions | ref is read-only through that path; inout permits reads/writes; neither grants exclusivity |
| Assignment/value parameters/value returns create independent values | Agreed |
| References may target variables, fields and array elements; not temporaries | Agreed |
| Reference and slice overlap | Allowed, including mutable overlap; no overlap checks or overlap traps |
| Array slices `array[start..end]` | Agreed; half-open borrowed regions, bounds checked; empty slices allowed |
| Unspecified-size parameters `ref T[]` / `inout T[]` | Agreed; runtime u32 length, exact element type, no backing-array copy |
| By-value array parameters | Fixed-size T[N] only |
| Mutable global declaration initializers | Forbidden for persistent/session state |
| Automatic defaults | New persistent/session state and uninitialized locals: zero/false recursively |
| Application-specific global setup | Lifecycle handlers; event API deferred to platform |
| Runtime resources | Application-chosen u32 identifiers; 0 invalid; runtime-owned objects |
| Resource identifier space | One per isolated application, covering all resource kinds |
| Resource storage strategy and cleanup | Platform decisions; identifier API does not require a heap |
| Array/structure defaults apply recursively | Agreed |
| Global const requires an explicit initializer | Agreed |
| Explicit array/structure construction remains complete | Agreed for constants, local initializers and assignments |
| Nested transactions, including through function calls | Forbidden initially |
| Callee persistent assignments participate in an active transaction | Agreed |
| By-value aggregate parameters | Temporary application RAM; call-frame placement proposed |
| Familiar imperative syntax, static types | Proposed baseline |
| Compact custom VM with single-digit KiB RAM goals | Feasibility direction; unmeasured |

## 3. Language character

Proposed baseline:

- Familiar functions, braces and statements.
- Agreed 8-, 16- and 32-bit signed/unsigned integers and booleans; structures and enums are user-defined types.
- Explicit type annotations on variables, constants, fields and parameters; pattern bindings get types from context.
- Fixed arrays, borrowed slices and unspecified-size ref/inout array parameters.
- Local value declarations use `var` only; globals use `persistent`, `session` or `const`. Local immutable declarations are deferred.
- Ordinary functions plus card-specific declarations such as `command`, `persistent`, `session` and `transaction`.
- No inheritance, user-defined operator overloading or implicit dynamic allocation initially.

The language frontend should be separated from the VM so another language could target the VM later.

### 3.0 Source grammar and lexical conventions (agreed)

The grammar uses conventional explicit punctuation and few optional forms. This section records agreed syntax; a complete parser grammar/EBNF remains a specification deliverable.

#### Source files

Use `.card` source files. Each contains complete top-level declarations. The build configuration supplies the application identity and explicit file list; there is no `application Name { ... }` wrapper, import or source inclusion mechanism.

```text
// state.card
const BUFFER_SIZE: u32 = 128;
persistent counter: u32;
session buffer: u8[BUFFER_SIZE];
```

```text
// operations.card
function increment() -> u32 {
    counter = counter + 1;
    return Ok(counter);
}
```

All files share one application scope. Declarations cannot span files; name resolution is file-order independent. Preserve file/line boundaries for diagnostics and lexical processing; a trailing comment/token cannot consume text from the next file. Duplicate declarations remain errors. Array lengths follow the constant-expression rules in section 3.10.

#### Identifiers and whitespace

- Identifiers are case-sensitive ASCII.
- First character: a letter or underscore; subsequent characters: letters, digits or underscores.
- `_` alone is reserved for an ignored pattern.
- Keywords cannot be identifiers; no escaped or Unicode identifiers initially.
- Capitalization conventions are stylistic, not compiler requirements.
- Source files are UTF-8; comments may contain Unicode. Identifiers and language tokens remain ASCII.
- Spaces, tabs and line breaks separate tokens; indentation has no semantic meaning.

```text
counter
account_balance
Account
WalletError
MAX_ACCOUNTS
```

#### Comments

```text
// Comment to end of line.

/* Block comment,
   possibly spanning several lines. */
```

Block comments do not nest. An unterminated block comment is a compilation error.

#### Literals

```text
123
0xA5
0b1010
1_000_000
0xDEAD_BEEF
true
false
```

- Integers may be decimal, hexadecimal or binary; leading zero does not mean octal.
- Numeric underscores appear only between digits: no leading/trailing/consecutive underscores, or underscore immediately after a base prefix.
- No integer type suffixes initially. Contextual literal typing and explicit conversions apply.
- Negative values use unary `-`, not a negative-literal token. A minimum signed value such as `-128` in an `i8` context must be accepted without first requiring positive 128 to fit in i8.
- Boolean literals are exactly `true` and `false`.
- No string, character, floating-point or null literals initially.

#### Semicolons, braces and commas

Semicolons are mandatory; there is no automatic insertion. Use them after variable/constant declarations, assignments, returns, abort statements, no-value attempt statements, break/continue statements, structure field declarations, enum variants and error members.

```text
struct Identity {
    identifier: u8[4];
    version: u16;
}

errors WalletError {
    InsufficientFunds = 1;
    AccountBlocked = 2;
}
```

Do not add semicolons after closing function, command, struct definition, enum definition, error set or control-flow blocks. A local initialized variable or global constant still ends with a semicolon after its initializer. The following example is a local declaration inside a function/command:

```text
var identity_copy: Identity = Identity {
    identifier: fill(0),
    version: 1
};
```

Braces are mandatory for every control-flow body and match arm. Commas separate function parameters, call arguments, explicit array elements and structure-initializer fields. A trailing comma is optional in these lists:

```text
var identity_copy: Identity = Identity {
    identifier: [1, 2, 3, 4,],
    version: 1,
};
```

Struct definitions use semicolon-separated fields; struct initializers use comma-separated fields. Match-arm blocks need no comma or semicolon after their closing braces. Examples are independent snippets, so repeated names between snippets are not declarations in one program.

#### Type annotations and function signatures

Require explicit types on all named variables, constants, fields and parameters initially:

```text
persistent counter: u32;
session authenticated: bool;
const LIMIT: u32 = 100;

// Inside a function/command:
var working: u32 = counter;
```

Pattern bindings get their types from the matched outcome; loop bindings use the explicit index type already specified.

```text
function calculate(input_value: u32) -> u32 {
    return Ok(input_value + 1);
}

function clear(target: inout u32) {
    target = 0;
    return Ok();
}
```

`-> Type` names the successful payload type. Omitting the arrow means success has no payload, not that a result may be discarded or that a final return is optional. Explicit `return Ok();` is still required on a reachable no-value successful exit. The single host command uses the fixed successful-payload signature in section 4; omission of the arrow is available for ordinary no-value functions, not for the host entry point.

Parameters use the agreed `name: Type`, `name: ref Type` or `name: inout Type` forms. Type arguments such as `convert<u16>(value)` are permitted for designated compiler intrinsics; this does not introduce user-defined generic functions.

#### Excluded source machinery

No preprocessor, `#include`, macros, conditional compilation or textual substitution initially. Build-supplied source-file composition is separate from a source module/import system, which is also omitted.

### 3.1 Primitive types and byte arrays (agreed)

| Type | Values |
| --- | --- |
| `u8` | 0 to 255 |
| `u16` | 0 to 65,535 |
| `u32` | 0 to 4,294,967,295 |
| `i8` | -128 to 127 |
| `i16` | -32,768 to 32,767 |
| `i32` | -2,147,483,648 to 2,147,483,647 |
| `bool` | `true` or `false` |

Byte arrays are supported as `u8[N]`, using the existing array initialization rules:

```text
session buffer: u8[128];
persistent identifier: u8[4];

// Illustrative setup helper; lifecycle binding is platform-defined.
function example_setup_identifier() {
    identifier = [0x01, 0x02, 0x03, 0x04];
    return Ok();
}
```

Arrays are composite types, not additional primitive scalar types. Arrays of supported fixed-size integers, booleans and structures are supported; enums are supported element types. Direct multidimensional arrays are deferred; structures may contain array fields.

The initial primitive set has no floating-point, 64-bit integer, character or string types. Enums and structures are separate user-defined type features. Enum semantics are defined in section 3.11; physical representation remains a compiler/platform detail. Boolean storage representation and detailed arithmetic rules still require specification. Conversion and integer literal rules are defined below.

### 3.2 Numeric conversions (agreed)

Core rule: a conversion preserves the numeric value exactly or reports failure. There are no implicit conversions between integer types, even when widening would always be safe.

Arithmetic and numeric comparisons require operands of the same integer type. The compiler must not silently choose a common width or signedness.

```text
var count: u16 = 100;
var increment: u8 = 5;
count = count + increment;                 // Compilation error: different types.
count = count + convert<u16>(increment);   // Valid; addition still checks overflow.
```

#### Guaranteed conversion: `convert<T>(value)`

This intrinsic is permitted only when every possible value of the source type fits in the destination type. It produces the converted value directly and cannot fail because of range. Safety is based on the entire source type range, not just the current value or a preceding condition.

```text
var small: u8 = 200;
var large: u16 = convert<u16>(small);
var signed: i16 = convert<i16>(small);
```

| Source to destination | Guaranteed conversion? | Reason |
| --- | --- | --- |
| `u8` to `u16` | Yes | All source values fit |
| `i8` to `i32` | Yes | All source values fit |
| `u8` to `i16` | Yes | All source values fit |
| `u16` to `i16` | No | Some values exceed the signed maximum |
| `i16` to `u32` | No | Negative values do not fit |
| `u32` to `u8` | No | Some values exceed the destination maximum |

Using `convert<T>` where the source range does not fit is a compilation error. For example, converting a typed `u16` to `u8` requires a checked conversion even if its current value is 10.

#### Fallible conversion: `checked_convert<T>(value)`

This intrinsic returns `Ok(converted_value)` when the numeric value is representable in the destination, or `Err(error)` otherwise. It never silently truncates, wraps or clamps.

```text
var incoming: u16 = 300;

match checked_convert<u8>(incoming) {
    Ok(value) => {
        // Use the converted byte.
    }
    Err(error) => {
        // Reject or otherwise handle the out-of-range value.
    }
}
```

A negative signed value converted to an unsigned type fails even when the destination has more bits. Failure uses the common platform-error category; exact error names/codes remain platform-defined. No ordinary user-declarable error value type is introduced.

`convert` and `checked_convert` are compiler intrinsics, not ordinary user functions: the first produces a value directly, while the second produces a success/error outcome. This is an explicit distinction from the universal result convention for ordinary functions. No general-purpose truncating cast is provided initially.

### 3.3 Integer literals (agreed)

Integer literals take their type from context and must fit that type:

```text
var counter: u8 = 10;    // Valid: literal 10 is typed as u8.
counter = counter + 1;   // Valid: literal 1 is typed as u8.
var invalid: u8 = 300;   // Compilation error: literal is out of range.
```

Contextual literal typing is not conversion of an already typed value. If context cannot establish a unique integer type, an annotation is required; the compiler must not silently pick a default. Literal formats and the negative-minimum case are specified in section 3.0. The contextual typing policy is completed below; named declarations require explicit type annotations. A formal typing judgment remains an implementation/specification deliverable.

#### Contextual typing policy (agreed)

There is no general type inference for named variable, constant, field or parameter declarations: all require annotations. Context supplies types for literals and compiler-introduced bindings.

| Construct | Type source |
| --- | --- |
| Variable/constant initializer | Explicit declaration type |
| Ordinary function argument | Declared parameter type |
| Successful `return Ok(...)` payload | Enclosing function's successful payload type |
| `Ok(value)` / `Err(error)` pattern binding | Matched outcome |
| Range bounds | Explicit loop index type |
| Array/structure initializer elements | Declared element/field type |
| Application error-code literal | Required u16 code type |

A unique expected integer type propagates through a literal-only arithmetic expression:

```text
var total: u16 = 10 + 20;  // Both operands and arithmetic result use u16.
```

A typed operand supplies the expected type for an untyped literal operand, independently of operand order:

```text
var count: u8 = 10;
// Expression fragments:
count + 1    // Literal 1 is u8.
1 + count    // Literal 1 is u8.
count == 10  // Literal 10 is u8; comparison produces bool.
```

Typed values are never implicitly converted to resolve a context. Conflicting typed operands or a mismatch with the required destination/parameter type is a compilation error. A boolean result expectation alone does not establish integer operand widths for a comparison of otherwise untyped literals; missing or ambiguous integer context must not be resolved by guessing a default.

No automatic widening is permitted to make an intermediate computation fit:

```text
var invalid: u8 = 250 + 10; // Compilation error: u8 overflow.
```

The compiler cannot evaluate this as a wider integer and silently narrow it afterward. Existing intermediate-result checks and explicit-grouping rules still apply.

#### Index expressions

For an array index with no typed operand, indexing supplies u32 context:

```text
buffer[0]       // Literal index is u32.
buffer[1 + 2]   // Literal-only arithmetic uses u32.
```

Already typed unsigned indices retain their types:

```text
var index: u8 = 0;
buffer[index]   // u8 index, not an implicit conversion to u32.
```

This is a specific context supplied by indexing, not a general default integer type. The bounds-check and unsigned-only rules in section 8.1 remain in force.

#### Conversion source typing

`convert<T>` and `checked_convert<T>` require the source expression to have a known source type independently of the destination type argument:

```text
var incoming: u16 = 300;
// Expression fragments:
checked_convert<u8>(incoming)  // Known u16 source, u8 destination.
checked_convert<u8>(300)       // Compilation error: source type unknown.
```

The destination does not invent a source width or signedness. A typed variable provides the source type without literal suffix syntax. The same known-source requirement applies to guaranteed `convert<T>`.

#### Structure construction

Keep the explicit type name in a structure initializer:

```text
var account_copy: Account = Account {
    balance: 0,
    // All other fields must also be provided.
};
```

This is a syntax fragment, not a complete constructor unless the actual Account has only the displayed field. No anonymous/shorthand structure initializer is introduced. Field literals obtain their types from the named structure definition. Aggregate completeness and nested initialization rules still apply.

### 3.4 Booleans and composite types (agreed)

Booleans do not implicitly convert to or from integers. Use an explicit condition:

```text
var invalid: bool = 1;       // Compilation error.
var flags: u8 = 1;
var enabled: bool = flags != 0;
```

Arrays and structures do not implicitly convert to other array or structure types. Encoding an integer as bytes is separate from numeric conversion and must explicitly specify byte order. Encoding API names and any future deliberately lossy byte-extraction operations remain open.

### 3.5 Expressions (agreed direction)

Expressions use familiar operators, strict typing and explicit grouping. The initial binary-precedence proposal is superseded: programmers do not need to memorize a binary precedence table.

#### Operators

| Purpose | Operators | Example |
| --- | --- | --- |
| Arithmetic | `+`, `-`, `*`, `/`, `%` | `balance - amount` |
| Comparison | `==`, `!=`, `<`, `<=`, `>`, `>=` | `balance >= amount` |
| Boolean logic | `not`, `and`, `or` | `authenticated and not blocked` |
| Bitwise logic | `~`, `&`, `\|`, `^` | `flags & 0x0F` |
| Shifts | `<<`, `>>` | `flags >> 2` |
| Field access | `.` | `account.balance` |
| Indexing | `[]` | `buffer[index]` |
| Grouping | `()` | `(balance + credit) - debit` |

Unary `-` is also supported subject to integer type/range rules. Lexical rules are specified in section 3.0, including acceptance of a signed minimum literal such as -128 in an i8 context.

#### Mandatory parentheses for mixed binary operators

At each parenthesis/grouping level, mixing different binary operators is a compilation error. Parenthesize the intended subexpressions instead:

```text
a + b * c          // Compilation error: mixed operators.
a + (b * c)        // Valid.
(a + b) * c        // Valid.
a + b - c          // Compilation error: mixed operators.
(a + b) - c        // Valid.
```

Repeated uses of the same binary operator may be written without grouping and associate left to right:

```text
a + b + c          // Equivalent to (a + b) + c.
a - b - c          // Equivalent to (a - b) - c.
```

Each intermediate arithmetic result is subject to its normal checks; later terms do not cancel an earlier overflow or underflow. Comparison chains are forbidden even if the comparison operator is repeated:

```text
0 < amount < limit                 // Compilation error.
(amount > 0) and (amount < limit)   // Valid.
a == b == c                        // Compilation error.
```

Boolean and bitwise expressions follow the same grouping rule:

```text
authenticated and not blocked           // Valid: one binary operator.
authenticated and ready or emergency    // Compilation error.
(authenticated and ready) or emergency  // Valid.
(flags & 0x03) == 0x01                  // Valid.
flags & 0x03 == 0x01                    // Compilation error.
```

Calls, indexing and field access form operands normally; unary operators apply to their operands without requiring parentheses solely because a binary operator is present:

```text
account.balance + buffer[index]
```

This fragment illustrates grouping only; it is type-correct only when the field and array element have matching integer types. The mixed-operator rule concerns binary operators, not assignment statement syntax or operators inside independently grouped call arguments/index expressions.

#### Typing and evaluation

- Arithmetic operands must have the same integer type.
- Ordering comparisons use matching integer types and produce `bool`.
- Equality supports matching integer types, booleans and values of the same enum type. Automatic array/structure equality is omitted.
- Boolean operators accept only `bool`; there is no numeric truthiness.
- Bitwise operators initially accept unsigned integers; binary bitwise operands have matching types.
- Shifts are the explicit exception to matching operand types: the left operand is unsigned, and the count is `u8`.
- Ordinary operands and function arguments evaluate left to right.
- `and` evaluates its right operand only if the left is true; `or` evaluates its right operand only if the left is false.

```text
(index < 16) and (buffer[index] == 0)
```

Here indexing occurs only when the first condition is true. The example assumes a 16-element buffer and a valid numeric type for `index`. Permitted index types are `u8`, `u16` and `u32`; signed indices are forbidden (section 8.1).

#### Arithmetic and shift edge cases

| Situation | Behavior |
| --- | --- |
| Arithmetic overflow or underflow | Trap |
| Division or remainder by zero | Trap |
| Signed division | Truncate toward zero |
| Signed remainder | Same sign as dividend, unless zero |
| Minimum signed integer divided by `-1` | Trap |
| Invalid operation established during required compile-time evaluation | Compilation error |
| Shift count at least the left operand's bit width | Trap |
| Unsigned right shift | Insert zero bits |
| Unsigned left shift | Discard bits shifted out; not checked multiplication |

Signed minimum remainder -1 is defined as zero (section 6.5). Required constant-evaluation failures are compilation errors. Optimizations must preserve evaluation, short-circuiting and failure behavior; checks may be eliminated only when safety is proved, not by changing arithmetic semantics between build modes.

#### Assignment and calls

Assignment is a statement, never an expression. Chained assignment and increment/decrement operators are not supported:

```text
balance = balance - amount;   // Valid statement.
a = b = 0;                    // Compilation error.
```

Assignment inside a condition is a compilation error. Compound assignments such as `+=` are deferred. Ternary `?:`, expression-valued blocks and implicit boolean conversions are omitted initially.

An ordinary function call produces a success/error outcome, not an implicitly extracted numeric value:

```text
balance + subtract(balance, amount)   // Compilation error.
```

Handle an ordinary call outcome with `match`, extract/propagate with `attempt`, or forward the complete outcome with a compatible `return function(...)`. Discarding an outcome is a compilation error. Direct-value intrinsics such as `convert<u16>(value)` may appear in arithmetic expressions. An ordinary call evaluating to `Err` does not imply propagation unless explicitly requested.

### 3.6 Control flow (agreed)

The initial control-flow set is `if`, `while`, ascending range-based `for`, `match`, `break`, `continue`, `return` and the transaction-specific `abort`. No `switch`, fall-through, `goto`, exceptions, labeled loops or multi-level loop exits are supported initially. `abort` is a reserved keyword.

#### Blocks, scope and conditions

Blocks always use braces, including single-statement bodies. Conditions require `bool`; there is no numeric truthiness. Parentheses around an entire condition are optional, but mixed binary operators still require explicit grouping.

```text
if authenticated and (amount <= balance) {
    balance = balance - amount;
}
```

Locals are visible after their initializer completes through the end of their enclosing block; a local cannot refer to itself in its initializer. Use outside scope is a compilation error. Shadowing visible names is forbidden. Function parameters and loop/match bindings participate in lexical scope; application-wide visibility and collision rules are specified in sections 4.1-4.2.

#### If / else

```text
if amount == 0 {
    // First branch.
} else if amount > balance {
    // Second branch.
} else {
    // Final branch.
}
```

Conditions evaluate in order, and only the first matching branch runs. Final `else` is optional. `if` is a statement, not a value-producing expression.

#### While

```text
var index: u8 = 0;
while index < 16 {
    buffer[index] = 0;
    index = index + 1;
}
```

The boolean condition is checked before each iteration; the body may run zero times. Infinite loops may be expressed with `while true`. The language need not prove termination; exhaustion of the VM execution budget traps. Budget configuration remains a runtime-design question.

#### Range-based for

```text
for index: u8 in 0..16 {
    buffer[index] = 0;
}
```

- Ranges are half-open: include the start, exclude the end.
- Both bounds must have the declared index type, with contextual typing for literals.
- Evaluate bounds once, left to right, before iteration.
- If start is at least end, execute zero iterations.
- The index binding is local to the loop body and read-only to application code.
- Advance the index with checked arithmetic; it must not wrap.
- Initially support ascending ranges with a unit step only.

The read-only index is introduced by `for`, not a local `const` declaration. An endpoint must fit its type: `for index: u8 in 0..256` is a compilation error; use a wider index. Array indices may be any unsigned integer type (section 8.1). No array-iteration syntax has been adopted yet.

#### Break / continue

`break;` exits the nearest loop; `continue;` proceeds to its next iteration. For `while`, continue rechecks the condition. For `for`, continue advances the index before the next iteration. Both are compilation errors outside loops, or if they cross an enclosing transaction boundary.

```text
for index: u8 in 0..16 {
    if buffer[index] == 0 {
        continue;
    }
    if buffer[index] == 0xFF {
        break;
    }
    // Process the byte.
}
```

#### Match

```text
match subtract(balance, amount) {
    Ok(value) => {
        balance = value;
    }
    Err(error) => {
        // Handle the error.
    }
}
```

Evaluate the matched expression exactly once and execute exactly one matching arm; there is no fall-through. Matching must be exhaustive: a result needs both success and error coverage. Pattern bindings exist only in their arm and are read-only; copy into a `var` for a changeable local. `_` may ignore a payload, as in `Err(_)`.

Initially, `match` accepts only success/error outcomes and enum values. Matching integers, Booleans, arrays, structures or standalone error values is not supported; use `if` for scalar conditions. `match` is a statement, not a value-producing expression. Arms contain ordinary statements and obey the existing return, loop-exit and transaction-boundary rules.

The complete initial pattern vocabulary is:

| Matched input or branch | Allowed patterns |
| --- | --- |
| Success carrying a payload | `Ok(name)` or `Ok(_)` |
| Success without a payload | `Ok()` |
| Recoverable error branch | `Err(ErrorSet.Member)`, `Err(name)` or `Err(_)` |
| Enum value | Qualified variant, such as `State.Idle` |

`name` introduces a new read-only, arm-local binding with its type determined by the input; existing no-shadowing rules apply. `Ok(name)` makes the successful payload available in the arm, while `Ok(_)` deliberately ignores it. `Ok()` is reserved for success without a payload. Successful payload bindings follow independent-value semantics, including arrays and structures; they do not introduce references. Matching an enum examines its value without modifying the original. Error-member patterns may name either application or platform errors.

An outcome match requires exactly one success arm, zero or more specific error arms, and exactly one final error catch-all, either `Err(name)` or `Err(_)`. Specific errors precede that catch-all. The final catch-all is mandatory even when every currently known error is listed: all functions use the common error representation, so a list of known errors is not proof of exhaustive error coverage.

An enum match lists every variant exactly once, with no catch-all, as specified in section 3.11. Missing cases, duplicate patterns, unreachable arms, a variant from the wrong enum, and patterns incompatible with the matched type are compilation errors. For example, repeating a specific error or placing it after `Err(_)` is forbidden; `Ok()` cannot match an outcome carrying a payload.

No guards, numeric/range patterns, combined alternatives joined by `|`, structure/array destructuring or nested patterns are supported initially. Put additional conditions inside an arm. To inspect a successful enum payload, bind it with `Ok(value)` and use a separate nested `match` in the arm; `Ok(State.Idle)` is not supported.

#### Return

Every function returns an explicit success/error outcome:

```text
return Ok(balance);
return Err(WalletError.InsufficientFunds);
```

A function with no successful value uses `return Ok();`. A signature such as `-> u32` describes the successful payload type. For no-value success in an ordinary function, omit the return arrow and type. The host command instead has successful type u32, the response byte count (section 4).

Every function body that may complete normally under the structural rules in section 3.7 must explicitly return an outcome. There is no implicit success at a closing brace. `return value;` and `return error;` without outcome wrappers are not the chosen syntax. All examples are independent sketches/fragments, not a single executable compilation unit.

Use `attempt` to accept success and immediately propagate a recoverable error. Alternatively `match` may recover or propagate with `return Err(error);`, or `return function(...)` forwards the entire outcome when the successful payload types match. These returns, including the implicit failure return of `attempt`, obey transaction-boundary restrictions.

`require` has a precise control-flow meaning:

```text
require authenticated else WalletError.Unauthorized;
```

is equivalent to:

```text
if not authenticated {
    return Err(WalletError.Unauthorized);
}
```

#### Transaction boundary rule

`return`, `break` and `continue` may not cross an enclosing transaction boundary. Such transfers are compilation errors. Consequently a direct `require` with a potentially failing path inside a transaction would also attempt a forbidden exit.

A break/continue targeting a loop entirely inside a transaction is valid. Returning from a function called during a transaction is valid because it does not exit the caller's transaction. The caller must handle the returned outcome without a forbidden exit.

A transaction reaches its closing brace to commit; a trap aborts it. The explicit `abort Err(error);` statement is the permitted recoverable exit: it rolls back the transaction's persistent changes and returns the specified error from the enclosing function or command. It is valid only lexically inside a transaction in that same function or command. Ordinary `return`, `attempt`, `require`, `break` and `continue` retain their boundary restrictions; no implicit rollback is added to them. Section 7.2 defines abort behavior and examples.

### 3.7 Functions and parameter passing (agreed)

#### Declaration form and arguments

An ordinary function has one declaration form:

```text
function name(parameters) -> SuccessType {
    // Body with explicit outcome returns.
}
```

The arrow names the successful payload type; every ordinary function still produces a success/error outcome. Omit the arrow and type when success has no payload:

```text
function clear(target: inout u32) {
    target = 0;
    return Ok();
}
```

Every parameter has an explicit name, type and mode as shown below. Arguments are positional only: no named arguments, default values, optional parameters or variadic parameters initially. Parameter and argument lists may have a trailing comma. Existing exact-type, contextual-literal, left-to-right evaluation, lifetime and access-path permission rules apply.

Functions are top-level declarations visible across the application regardless of file or declaration order. Duplicate names and overloading are forbidden; nested functions are not supported. Parameters may not shadow visible application names, following section 4.2.

#### No nested calls in argument expressions

An argument to an ordinary function, platform API or compiler intrinsic must not contain another call anywhere in its expression, including within an array index, a structure constructor or another nested expression. This restriction includes compiler intrinsic calls, whether direct-value or outcome-producing. Evaluate the inner call into an explicitly typed local first:

```text
// Forbidden:
attempt process(inout counter, attempt next_value());
attempt process_value(convert<u32>(small));

// Allowed, assuming the corresponding declarations:
var next: u32 = attempt next_value();
attempt process(inout counter, next);
var widened: u32 = convert<u32>(small);
attempt process_value(widened);
```

`Ok` and `Err` in outcome-return syntax, including `Err` in `abort Err(error);`, are not ordinary call constructors; this rule does not prohibit `return Ok(attempt read_value());`. Calls in other expression positions, such as an assignment's right-hand side or a destination index, remain allowed under their existing result and evaluation rules, unless they occur within a call argument.

All arguments evaluate left to right before callee entry. By-value argument values and selected reference regions are established, and required bounds checks complete, before callee execution. Overlapping references are allowed and require no overlap checks. Argument preparation does not acquire exclusive permissions. The existing ban on nested calls in argument expressions remains a separate language restriction; it is not needed to enforce exclusivity.

#### Parameter modes

Retain three explicit modes. The alternative of implicitly passing ordinary arrays/structures by read-only reference was not adopted.

| Parameter declaration | Semantics | Copy? | Can change caller data? |
| --- | --- | --- | --- |
| `value: u32` | By value, read-only binding | Independent value semantically | No |
| `source: ref Account` | Read-only reference | No data copy required | No, through this reference |
| `target: inout Account` | Mutable reference | No data copy required | Yes |

Ordinary parameters are read-only independent values, including arrays and structures with all nested fields. A compiler may eliminate physical copies only if observable behavior is preserved. Passing a large aggregate by value can require substantial memory; use explicit reference modes when appropriate.

```text
function increment(input_value: u32) -> u32 {
    return Ok(input_value + 1);
}
```

To change a working value, copy it into a local `var`:

```text
var working: u32 = input_value;
```

Read-only parameter bindings do not reintroduce local `const` declarations. Their immutability follows from the parameter mode.

#### Read-only reference: ref

```text
function get_balance(source: ref Account) -> u32 {
    return Ok(source.balance);
}
```

Call-site mode is explicit:

```text
match get_balance(ref account) {
    Ok(balance) => {
        // Use balance.
    }
    Err(error) => {
        return Err(error);
    }
}
```

Writing to `source` or its nested fields/elements through this reference is a compilation error. Read-only access grants no mutation permission.

#### Mutable reference: inout

```text
function debit(target: inout Account, amount: u32) {
    require amount <= target.balance else WalletError.InsufficientFunds;
    target.balance = target.balance - amount;
    return Ok();
}
```

```text
match debit(inout account, amount) {
    Ok() => {
        // Debit completed.
    }
    Err(error) => {
        return Err(error);
    }
}
```

`Ok()` is the agreed no-value success pattern. The account type in these fragments is assumed to have a `balance: u32` field. Function arguments still evaluate left to right, and ordinary calls still produce success/error outcomes.

#### Reference constraints

- References are temporary access permissions, not arbitrary machine addresses.
- References are parameters whose lifetime is bounded by the call. No general first-class reference variables/types are introduced by this decision.
- They cannot be returned, stored in globals/structures, or converted to integers.
- No null references, pointer arithmetic or raw pointers initially.
- Parameter types match exactly, except that ref/inout T[] accepts fixed arrays or slices with exactly element type T and any valid length (section 8.4). Fixed-size array parameters retain exact-length matching. Numeric conversions remain explicit; literals retain contextual typing.
- `inout` requires a mutable destination. A constant cannot be passed as `inout`.
- A read-only reference cannot be forwarded as `inout`.
- Forwarding to nested calls may not extend a reference's lifetime or strengthen its access-path permissions; section 3.8 defines permitted forwarding. No original access is suspended to enforce exclusivity.

#### Aliasing and access-path permissions

References may overlap, including multiple inout references or an inout reference overlapping a ref reference. Overlap alone is neither a compilation error nor a runtime trap. Globals and nested helpers may access the same storage through other permitted paths.

A ref parameter prohibits writes through that reference and its derived fields/elements; it does not guarantee that the underlying storage remains unchanged. An inout parameter permits reads and writes through that reference without granting exclusive access. Constants and independent read-only by-value parameters remain immutable.

Reads and writes follow the specified evaluation and statement order. Compilers must preserve observable aliasing effects and must not assume that ref storage is stable or that inout storage is unaliased. Optional warnings about suspicious overlap do not alter program acceptance or execution. Detailed examples are in section 3.8.

#### Persistence, errors and transactions

Storage identity survives reference passing: writing through `inout` to a persistent destination is still an atomic persistent assignment. Two such writes remain separate unless coordinated by a transaction. Passing a persistent aggregate by value instead produces an independent value; mutating an explicit local copy does not update persistent storage.

Returning `Err` does not automatically undo earlier mutations through `inout`. Validate before changing data or use an appropriate transaction. Transaction-boundary exit rules remain in force: a function may validate and return an error before opening its own transaction, but may not use ordinary `return` across a transaction it opened. Use `abort Err(error);` inside that transaction to roll back its persistent changes, including persistent writes through references, and return a recoverable error.

The internal parameter modes do not imply that an external host can pass references or pointers into card memory. The platform supplies validated byte-array views to the single host entry point (section 4); application code parses the request and invokes ordinary helpers. Transport framing and buffer capacities remain platform contracts.

#### Successful return values and completion

A successful return may contain any supported value type: an integer, Boolean, enum, fixed-size array or structure, including nested aggregates. Returned arrays and structures are independent values under the copy rules of section 3.8. References cannot be returned. Multiple return values and tuples are not supported initially; use a structure to group values:

```text
struct Measurement {
    value: u32;
    valid: bool;
}

function measure() -> Measurement {
    return Ok(Measurement { value: 10, valid: true });
}
```

`return Ok(value);` requires a payload of exactly the declared successful type, with the usual contextual typing of literals. A no-payload function uses `return Ok();`. `return Err(error);` uses the common error representation. `return another_call();` forwards an outcome only when its successful type exactly matches the enclosing function's successful type, including the no-payload case.

Reject a function or command if its body may complete normally under the following conservative structural rules; the compiler never inserts success. These rules do not require proving arbitrary program behavior.

| Construct | Normal-completion rule |
| --- | --- |
| `return ...` | Cannot continue normally |
| `abort Err(...)` | Cannot continue normally; rolls back the enclosing transaction and returns Err from the enclosing function/command |
| Ordinary declaration, assignment or call handling | Conservatively may continue normally |
| `break` / `continue` | Cannot continue to the next statement in the same block; transfer to their existing loop target |
| `if` without `else` | May continue normally |
| `if` with `else` | Cannot continue only if both branches cannot continue |
| Exhaustive `match` | Cannot continue only if every arm cannot continue |
| `for` or ordinary `while` | Conservatively may continue after the loop |
| `while true` | Cannot continue after the loop if there is no syntactic `break` targeting that loop |
| Block | Cannot continue once a statement cannot continue normally |
| `transaction` block | May complete normally exactly when its body may; `abort Err(...)` exits recoverably, while ordinary boundary-crossing transfers remain forbidden |

For `while true`, count every syntactic `break` targeting that loop, even inside a condition the compiler could prove false. Breaks targeting nested loops do not count. No other constant-condition or data-flow proof is required for completion analysis. The special exemption previously suggested for necessarily trapping calculations is removed: predicted arithmetic or platform-call traps do not justify omitting a return. Existing transaction-boundary restrictions on `return` and `attempt` remain in force.

#### Effects and command boundary

Ordinary functions may access application globals, call permitted platform APIs and open transactions, subject to the existing aliasing, permission and no-nested-transaction rules. No purity or effect annotations, or `pure`, `static` or `public` modifiers, are introduced.

Each application has one external host command with the signature in section 4. It cannot be called directly by application code. Ordinary functions are not host-callable; application parsing, dispatch and shared behavior belong in ordinary helpers:

```text
persistent counter: u32;

function perform_increment() -> u32 {
    counter = counter + 1;
    return Ok(counter);
}

function increment() -> u32 {
    return perform_increment();
}
```

#### Function features and static call graph (agreed)

Direct and indirect recursion are forbidden initially. The compiler checks the complete application's call graph and rejects recursive cycles, including cycles spanning source files. Use loops for repetition. For example, this cycle is a compilation error:

```text
function first() {
    return second();
}

function second() {
    return first();  // Forbidden recursive call cycle.
}
```

Functions are not values: no function pointers, function-valued variables, function arguments or function return values are supported. Every ordinary call names its target directly; runtime selection between functions uses ordinary control flow. Runtime callbacks and event dispatch require separately specified platform rules and are not introduced by this decision.

User-defined generic functions and type parameters are not supported initially. Designated compiler intrinsics such as `convert<T>` remain available; their type-argument syntax does not introduce general generics.

Separate function prototypes, forward declarations and application-defined external declarations are not supported. Each ordinary function definition supplies its signature and body. Definitions are visible regardless of source-file or declaration order, so a function may call a later definition:

```text
function run() {
    return prepare();
}

function prepare() {
    return Ok();
}
```

Platform API declarations are supplied by the platform. Application code cannot invent external declarations.

Together these rules give application-defined functions statically known call targets and an acyclic call graph. This makes maximum application call depth predictable and helps the implementation calculate stack requirements; concrete memory limits and platform call costs remain VM/platform concerns.

#### Remaining enforcement and platform details

Aggregate-return resource limits belong to the VM/platform specification; detailed parameter/reference enforcement remains to be formalized without changing the agreed value, access-path and lifetime semantics. Slices and unspecified-size ref/inout parameters obey the existing call-scoped lifetime and access rules (section 8.4).

### 3.8 References and copies (agreed)

Core rule: values are independent; references temporarily access an existing value. Copying does not create a hidden shared reference.

#### Value copies

```text
var working: Account = account;
working.balance = 0;
```

`account` is unchanged. Assignment copies the complete value, including nested structures and arrays. Ordinary by-value parameters and successful value returns have the same independent-value semantics. Parameter bindings remain read-only; a local `var` copy is mutable.

Physical copies may be eliminated only when observable behavior is preserved. The compiler must not silently switch to shared-reference semantics to save memory. Runtime resource identifiers are ordinary u32 names: copying an identifier does not duplicate its runtime-owned object (section 11).

#### Reference targets

References may target named variables, structure fields and array elements, including nested combinations. A reference to a field covers that field, not automatically the whole parent structure. A constant may be passed through `ref`, but never through `inout`; any implementation materialization preserves its immutable semantics and does not make references first-class values.

```text
function reset(target: inout Account) {
    target.balance = 0;
    return Ok();
}
```

```text
match increment(inout account.balance) {
    Ok() => {
        // The field was updated.
    }
    Err(error) => {
        return Err(error);
    }
}
```

This call fragment assumes an `increment` function taking an `inout u32` and returning no successful payload. It is independent of earlier by-value increment examples.

An array-element reference must pass its bounds check before the callee starts. Temporaries and expressions that do not identify existing storage cannot be reference arguments initially, including read-only `ref` arguments. For example, `ref Account { balance: 0 }` is forbidden. References cannot escape a call through returns, stored fields, globals or integer conversions. There are no reference variables, arrays of references, null references, reference comparisons, raw pointers or pointer arithmetic.

#### Aliasing and overlap

| Argument combination | Rule |
| --- | --- |
| Overlapping ref references | Allowed |
| Overlapping inout references | Allowed |
| inout overlapping ref | Allowed |
| References to distinct fields/elements | Allowed |

Call fragments below assume matching declarations; complete code must consume outcomes:

```text
compare(ref account, ref account);       // Allowed.
modify(inout account, ref account);      // Allowed; ref may observe modifications.
modify(inout account, inout account);    // Allowed; both refer to the same storage.
update(inout counters[first], inout counters[second]); // Equal indices allowed.
```

An aggregate and its fields/elements may be aliased. Array-element and slice bounds must still be checked before callee entry, but no separation proof or runtime overlap check is required. References retain the selected storage identity. The compiler must not silently substitute independent copies to conceal observable aliasing.

| Access path | Permission |
| --- | --- |
| ref, including derived fields/elements/slices | Read only through this path |
| inout, including derived fields/elements/slices | Read/write through this path |
| Another mutable reference or mutable global | May access the same storage using its own permissions |

For example, this complete snippet writes the same byte twice:

```text
session buffer: u8[16];

function update(target: inout u8, index: u32) {
    target = 1;
    buffer[index] = 2;
    return Ok();
}

function demonstrate_aliasing() {
    attempt update(inout buffer[0], 0);
    return Ok();
}
```

After successful completion, buffer[0] is 2. Neither access violates a borrow rule. If a ref alias is read after a write through another permitted path, it observes that write according to the ordinary evaluation and transaction rules. A ref is not a snapshot or an immutability promise about the underlying storage. By-value parameters and assignments retain independent-copy semantics.

Optimizations must preserve these effects, including effects through globals and nested calls. No active-borrow registry, exclusive-region tracking, permission suspension or overlap trap is required by the language. Bounds, storage ownership, access-path permissions, application isolation and nonescaping lifetimes remain enforced; allowing aliasing does not introduce raw pointers or cross-application access.

#### Forwarding references

A ref parameter may be forwarded as ref, never as inout. An inout parameter may be forwarded as either ref or inout. Fields, elements and slices may be forwarded under the same bounds and lifetime rules. Forwarding cannot strengthen permissions through the original path or extend its lifetime. It does not suspend other access paths or acquire exclusivity.

```text
function process(target: inout Account) {
    attempt inspect(ref target);
    attempt update(inout target);
    return Ok();
}
```

This fragment assumes matching no-payload helpers. A helper receiving ref target cannot write through that reference; it may still change the same storage through a separate mutable global or inout path if one is available.

References end with their calls on Ok or Err. Ordinary return Err does not undo mutations. Explicit abort Err first rolls back the enclosing transaction and returns Err under section 7.2. References in frames terminated by a trap cease to exist with those frames.

#### Mutations, errors and persistent state

```text
match update(inout account) {
    Ok() => {
        // Update completed.
    }
    Err(error) => {
        // Account may already have changed.
    }
}
```

Returning an error does not undo earlier mutations. References do not imply transactions. Every persistent assignment remains atomic, including writes through `inout`; several assignments need an explicit transaction for collective atomicity. Existing transaction exit restrictions still apply.

#### RAM and deferred features

Large copies may consume substantial RAM. The compiler should report storage requirements and reject programs exceeding the selected card profile rather than silently change copy semantics. Explicit `ref` and `inout` provide ways to avoid those copies. Exact stack/temporary accounting remains a compiler/VM design task.

By-value aggregate arguments naturally occupy the callee's frame in the application's bounded RAM. They exist for the call and are released on return; they do not inherit the source's persistent/session storage lifetime. This is the proposed VM placement, not a language requirement for a particular physical stack layout.

| Logical stack area | Contents |
| --- | --- |
| Call frames | Parameters, local variables and return bookkeeping |
| Operand stack | Temporary expression values |

These areas may share one bounded arena internally. The compiler should calculate or conservatively bound required storage, and the VM must check available space before copying arguments or entering the callee. Reference parameters need a small descriptor rather than a full data copy; descriptor size is not yet specified. Optimizations may change physical placement while preserving independent-value semantics.

Slices borrow existing storage without copying elements; their unspecified-size ref/inout parameters carry runtime length (section 8.4). By-value arrays retain fixed sizes. The host entry point receives request and response byte-array views (section 4); transport framing, capacities and physical buffer representation remain platform ABI questions.

### 3.9 Initialization and lifecycle-driven setup (agreed)

Mutable globals have automatic defaults and no declaration initializers. Global `const` declarations still require explicit constant initializers; local `var` declarations may have runtime initializers or use defaults.

| Declaration | Explicit initializer? | Default/initial behavior |
| --- | --- | --- |
| `persistent name: Type;` | Forbidden | Recursive defaults when durable state is first created |
| `session name: Type;` | Forbidden | Recursive type defaults on chip power-on; security reset clears session state and subsequent initialization restores defaults |
| Global `const name: Type = expression;` | Required | Compile-time constant expression |
| Local `var name: Type;` | Optional | Recursive defaults if initializer omitted |

```text
persistent balance: u32;
session retry_limit: u8;
session scratch: u8[128];
const DEFAULT_RETRY_LIMIT: u8 = 3;
```

These globals do not contain uninitialized memory. Defaults are:

| Type | Default value |
| --- | --- |
| Signed/unsigned integer | Numeric zero |
| `bool` | `false` |
| Enum | First declared variant |
| Fixed array | Each element receives its type's default |
| Structure | Each field receives its type's default, recursively |

Persistent defaults apply once when the state is created, not on every reset or command. Session variables receive their recursive type defaults on chip power-on. A security reset wipes session state; subsequent initialization restores these defaults. An ordinary command trap preserves session state and does not trigger default initialization. Locals default each time execution reaches their declaration. Semantic defaults do not imply a particular physical boolean or storage representation.

#### Nondefault application setup

Application-specific setup belongs in handlers invoked for platform lifecycle events such as installation or power-on. Power-on defaults and security-reset clearing are defined here. Remaining lifecycle events, handler names/signatures, binding syntax, interrupted installation and behavior after setup failure remain platform questions. No lifecycle callback syntax is introduced here.

```text
// Illustrative setup helper only; not a defined lifecycle callback.
function example_setup() {
    retry_limit = DEFAULT_RETRY_LIMIT;
    scratch = fill(0xFF);
    return Ok();
}
```

Setup that writes persistent values is distinct from volatile/session setup: resetting a durable balance or regenerating keys on every power-on would destroy existing application state. The platform must determine when provisioning runs and how interruption/recovery and activation are handled.

Earlier nondefault global-declaration examples elsewhere in these notes are represented with illustrative setup helpers. Their names have no implicit event registration or automatic execution meaning.

#### Invalid global initializers

```text
persistent balance: u32 = 100;      // Compilation error: global initializer forbidden.
session scratch: u8[128] = fill(0); // Compilation error: global initializer forbidden.
```

The ban includes zero/false initializers; there is one mutable-global declaration form, without `=`. Global constants are the separate explicit-initializer exception.

#### Local initialization and aggregate assignment

Local runtime initialization remains supported:

```text
var previous: u32 = balance;
var amount: u32 = attempt read_amount();
var working: u8[16];  // Defaults to zeros.
```

An explicit local initializer determines the initial value; it is not implicitly preceded by separately observable default initialization. A failed initializer does not fall back to a default. The variable becomes visible only after initialization completes, and previous side effects are not automatically undone.

Array construction with `fill(value)` or an exact-length list, and named structure construction, are valid in local initializers and on the right-hand side of assignments. The destination supplies element/field type and fixed length context:

```text
scratch = fill(0xFF);

account = Account {
    balance: 100,
    identifier: fill(0),
    counters: fill(0)
};
```

The second fragment assumes the Account definition with balance, identifier and counters fields. A persistent aggregate assignment retains its whole-destination atomicity guarantee, subject to platform capacity rules. Several separate assignments are not collectively atomic without a transaction.

Explicit array lists remain exact-length, with no padding/truncation. Explicit structure construction supplies every field, recursively; omitted fields do not default inside an explicit constructor. Entire variables without initializers default recursively instead. No field-level default declarations or default function arguments are implied.

Runtime resource identifiers use ordinary u32 defaults. Zero is invalid and names no resource; default initialization never creates a key or grants authority. No special opaque-handle default type is required. Enum defaults are the first declared variant (section 3.11).

Global constant evaluation is specified in section 3.10. Local explicit array elements and structure field expressions evaluate left to right in written order; field declaration order must not rearrange side effects. Fill evaluates its argument once and independently copies the value to each element (section 8.2). Any additional local expression restrictions remain to be formalized. Mutable-global initializer dependencies are no longer a language question because such initializers are forbidden.

### 3.10 Constant expressions (agreed)

Global `const` declarations have explicit types and explicit compile-time initializers. Constant evaluation is deterministic and side-effect-free. Guaranteed convert<T> is permitted for constant operands. The first version does not provide user-defined compile-time functions, checked_convert<T>, or checked/wrapping arithmetic intrinsics in constant expressions.

| Construct | Constant-expression support |
| --- | --- |
| Integer and boolean literals | Allowed with contextual typing |
| Other global constants | Allowed, including forward references |
| Existing arithmetic/comparison/boolean/bitwise operators | Allowed under their existing type and grouping rules |
| Explicit array/structure initializers | Allowed when every component is constant |
| `fill(value)` | Allowed when its value is constant; aggregate construction |
| Fixed-array `.length` | Allowed: determined by type, not stored contents |
| Indexing a constant array / selecting a constant structure field | Allowed, with normal bounds/type rules |
| Reading persistent or session contents | Forbidden |
| Ordinary function calls, platform APIs, user-defined compile-time functions | Forbidden |
| `convert<T>` | Allowed with a constant operand and a guaranteed value-preserving conversion |
| `checked_convert<T>` | Forbidden initially |
| Checked/wrapping arithmetic intrinsics | Forbidden initially |
| References, mutation, `attempt`, transactions | Forbidden |

Examples (independent snippets):

```text
const BASE: u32 = 32;
const CAPACITY: u32 = BASE * 4;
const MASK: u8 = 0x0F;
const DEFAULT_ID: u8[4] = fill(0);
```

The existing strict integer typing and parentheses-for-mixed-operators rules apply unchanged. No conversion is implicit, including conversion of typed constant values:

```text
const SMALL: u8 = 32;
const LARGE: u32 = SMALL;  // Compilation error: different types.
```

Use an explicit guaranteed conversion to reuse a typed constant at a compatible width:

```text
const SMALL: u8 = 32;
const LARGE: u32 = convert<u32>(SMALL);  // Valid: value 32, type u32.
```

The source type must be known independently of the destination type argument. Every value of the source type must fit the destination type, just as at runtime; the current constant value does not relax that requirement. Thus convert<u8> on a typed u16 constant remains invalid even if that constant equals 10. convert<u32>(32) remains invalid because the source type is not established. No implicit conversions are introduced.

Guaranteed convert is constant-evaluable only when its operand is constant. checked_convert remains excluded because compile-time outcome handling is not supported. The nested-call ban still applies, including in constant expressions: nested conversions must use separately declared intermediate constants rather than nested calls. This restores guaranteed constant conversion and supersedes the earlier blanket exclusion.

#### Dependencies

Constants may refer to constants declared later, including in another source file:

```text
const CAPACITY: u32 = BLOCK_SIZE * 4;
const BLOCK_SIZE: u32 = 32;
```

The compiler resolves dependencies independently of source-file order. Direct or indirect dependency cycles are compilation errors, including dependencies through types and array lengths:

```text
const FIRST: u32 = SECOND + 1;
const SECOND: u32 = FIRST + 1;  // Compilation error: dependency cycle.
```

This policy concerns constants; it does not imply arbitrary execution or file-order initialization for mutable globals.

#### Evaluation and failures

Compile-time arithmetic follows runtime numeric semantics. No implicit wider intermediates may rescue an out-of-range operation. A failure encountered during required constant evaluation is a compilation error, not a runtime trap.

Constant-only calculations, including calculations using named constants, are evaluated during compilation even in local initializers and other runtime-expression positions. An arithmetic, shift or bounds failure encountered while evaluating such a calculation is a compilation error. Calculations involving runtime values retain runtime checks. The constant-expression subset remains the one defined above: intrinsics excluded from constant evaluation do not become constant-evaluable merely because their arguments are constants. Additional analysis may warn about dynamic failures, but optimization must preserve the required acceptance and runtime behavior. Constant evaluation respects short-circuiting and does not report arithmetic failure from a skipped Boolean operand; all operands must still resolve names and type-check.

```text
const TOO_LARGE: u8 = 250 + 10;  // Compilation error.
const DIV_ZERO: u32 = 10 / 0;    // Compilation error.
```

Boolean short-circuiting is preserved. A skipped operand is not evaluated, but both operands must type-check and resolve names:

```text
const ZERO: u32 = 0;
const ENABLED: bool = false and ((10 / ZERO) == 1);
```

Here the right operand is not evaluated; its integer literals get u32 context from ZERO. A skipped operand cannot excuse missing names or type errors. Constant-array out-of-bounds access is a compilation error when evaluated.

#### Structural evaluation boundary (proposal for specification)

The agreed goals are mandatory evaluation of constant-only calculations, preserved Boolean short-circuiting, and program acceptance independent of optimizer sophistication. The following algorithm and edge-case outcomes are proposed to make those goals precise; they are not yet settled acceptance rules.

1. Resolve names and type-check every expression, including skipped Boolean operands and unreachable statements.
2. Identify constant-only expressions structurally using the permitted subset above. Mutable variables are runtime values even if an optimizer can infer their contents. Guaranteed convert is included when its operand qualifies; excluded intrinsics remain excluded even with constant operands.
3. Evaluate maximal constant-only subexpressions using the language's ordinary arithmetic, bounds and short-circuit rules. Do not independently evaluate a descendant that evaluation of its containing constant Boolean expression skips.
4. When an enclosing expression is runtime-dependent, recursively check its constant-only parts. A runtime-dependent guard does not suppress mandatory evaluation of such parts. A structurally constant false left operand of and, or true left operand of or, suppresses evaluation of the right operand, while preserving its name/type checks.
5. Do not use statement reachability analysis to suppress mandatory evaluation. Constant-only expressions in an unreachable statement are still checked; Boolean short-circuiting within those expressions still applies.
6. Additional optimization or data-flow analysis may warn about dynamic failures, but cannot change acceptance or replace a required runtime failure with a compilation error.

Illustrative cases below assume ZERO is a global u32 constant equal to zero and runtime_flag is a runtime bool:

| Expression or location | Proposed result |
| --- | --- |
| `false and ((10 / ZERO) == 1)` | Valid false; division is skipped |
| `runtime_flag and ((10 / ZERO) == 1)` | Compilation error in the constant-only division |
| `runtime_flag and (false and ((10 / ZERO) == 1))` | Valid; the nested constant Boolean expression skips division |
| Constant `10 / ZERO` inside an `if false` body or after a return | Compilation error; statement reachability supplies no exemption |
| `10 / divisor`, with divisor a mutable u32 local initialized to zero | Runtime division check; inferred local contents do not make it a required constant expression |

A remaining classification question is indexing mutable storage with a constant invalid index. Its array length is type-known, but the full element expression is not constant-only. The specification must explicitly decide whether such bounds validation is mandatory at compile time; it must not let optimizer capability decide. The current constant-array rule is unchanged: evaluated constant-array bounds failures are compilation errors.

These proposed cases should become executable conformance examples once their acceptance rules are agreed. They do not broaden constant evaluation to ordinary calls, platform APIs, mutable-state reads, attempt or stored outcomes.

#### Array lengths and type-derived properties

Fixed-array lengths are unsigned constant expressions. Existing typed u8/u16/u32 constants retain their types; literal-only length expressions receive u32 context. No general implicit integer conversion is introduced. Zero-length arrays are compilation errors; each declared fixed-array length must be at least one (section 8.2).

```text
const BLOCK_SIZE: u32 = 32;
session buffer: u8[BLOCK_SIZE * 4];
const BUFFER_LENGTH: u32 = buffer.length;
```

The `.length` expression is constant because the fixed length belongs to the array type; no session contents are read. More complex receivers of `.length` must satisfy constant-expression restrictions themselves, including any index evaluation and bounds checks. The type-known result cannot hide a function call or mutable-state read. Plain variable/field paths to fixed arrays remain permitted without reading their contents. Runtime receiver-evaluation behavior is specified in section 8.1.

This does not allow reading array elements from session/persistent state:

```text
const FIRST_BYTE: u8 = buffer[0];  // Compilation error: session data read.
```

An actual constant array may be indexed:

```text
const IDENTIFIER: u8[4] = [1, 2, 3, 4];
const FIRST_BYTE: u8 = IDENTIFIER[0];
```

Aggregate initializers must remain complete. Fill evaluates its argument once and copies the resulting value independently into each element (section 8.2); no side effects are permitted in a constant fill argument.

### 3.11 Enums (agreed)

Enums are simple named value types with no payloads or user-assigned integer values initially. They are distinct from the application's numeric error set.

```text
enum OperationState {
    Idle;
    Receiving;
    Complete;
}
```

An enum declaration is top-level, declares at least one variant and has no semicolon after its closing brace. Variants are semicolon-terminated and unique within their owning enum. Multiple enums per application are allowed. Enum type names participate in the shared top-level naming scope.

Always qualify variant names, even within the same application:

```text
session state: OperationState;

// Inside a function/command:
state = OperationState.Receiving;
```

Different enums may reuse variant names:

```text
enum ConnectionState {
    Idle;
    Connected;
}
```

ConnectionState.Idle and OperationState.Idle are unrelated values. Enums have nominal identity: assignments, parameters, return values and equality require the same named enum type, not a matching variant list or representation.

| Feature | Rule |
| --- | --- |
| Value construction | Qualified variant expression, producing a direct value, not Result |
| Equality | == and != for values of the same enum |
| Ordering/arithmetic | Unsupported |
| Numeric assignments/conversions | Unsupported, including convert/checked_convert |
| Associated data/payloads | Unsupported initially |
| Arrays and structure fields | Supported |
| Bit flags, methods and numeric encoding syntax | Omitted initially |

```text
state = 1;  // Compilation error.
const INITIAL_STATE: OperationState = OperationState.Idle;
```

Qualified variants are constant expressions, and equality of matching constant enum values is constant-evaluable. There is no application-visible ordinal or numeric conversion. Internal storage representation is a compiler/platform detail, not a host protocol contract.

#### Default value

The first declared variant is the default. Reordering variants can therefore change the declared default; that consequence is intentional.

```text
struct Operation {
    state: OperationState;
    received: u32;
}

session operation: Operation;
// Defaults: state = OperationState.Idle; received = 0.
```

Recursive defaults apply to enum arrays and nested structures. Mutable-global declarations still have no explicit initializers. Preservation/migration of stored enum values across application upgrades belongs to the platform specification; declaration order is not a promise of stable numeric encoding.

#### Matching

```text
match state {
    OperationState.Idle => {
        // No operation active.
    }
    OperationState.Receiving => {
        // Accept more input.
    }
    OperationState.Complete => {
        // Result available.
    }
}
```

Evaluate the matched value once and execute exactly one arm. Every enum variant must appear explicitly exactly once; missing, duplicate or foreign-enum variants are compilation errors. No catch-all enum arm initially. Adding a variant therefore forces affected matches to be updated. Result/error matching retains its separate rules, including Err(error) / Err(_) coverage for unspecified recoverable errors.

#### Enums versus error sets

Enums describe application values. The single application error set describes failures and uses explicit stable nonzero u16 codes. Enum variants cannot be returned as errors merely because they are named values. Multiple ordinary enums do not relax the one-error-set limit. Structs may represent associated data separately, and unsigned integers may represent explicit bit masks.

## 4. Application host entry point

An application groups state, ordinary functions and exactly one host-callable command. All host requests for that application enter this command. The application parses request bytes, selects the requested operation and encodes response bytes. ASN.1, CBOR or a custom representation are application protocol choices, not language features.

### Byte-oriented entry contract (agreed)

```text
command process(request: ref u8[], response: inout u8[]) -> u32 {
    // Parse request, perform the operation, and encode response bytes.
    // This minimal example produces an empty successful response.
    return Ok(0);
}
```

The signature has two parameters in this order: a read-only unspecified-size byte array for the request and a mutable unspecified-size byte array for the response. The successful return type is u32. The example uses process as the entry-point name; whether that spelling is reserved or the sole command declaration identifies the entry remains a specification detail. Parameter names are illustrative. A complete application must have exactly one command with this signature; additional operations use ordinary functions. Earlier typed command examples in these notes have been converted to helper functions, not additional host entry points.

| Item | Meaning |
| --- | --- |
| request.length | Number of request bytes received and supplied by the platform |
| response.length | Available output capacity in bytes |
| Ok(count) | Response produced successfully; transmit only the first count output bytes |
| Err(error) | Recoverable command failure; report its application/platform category through the platform status mapping |
| Trap | Current command terminated with an execution fault; use the platform trap reporting category |

The platform supplies separate, non-overlapping input and output regions, valid only for the invocation. The host cannot pass raw references into card memory. Separate host buffers are an entry-point contract, not language-wide exclusive borrowing. The application cannot resize either region. Existing indexing, slice, access-path and nonescaping-lifetime rules apply.

The application must write every response byte it includes in the returned count; no initial response-buffer contents are promised by this contract. The platform transmits response data only after successful entry-point completion and validation of count. A count greater than response.length traps and produces no application response payload. On Err or trap, partially written response bytes are not transmitted. Bytes beyond count are never part of the application response. Output transmission is not performed by assignment to the response buffer.

Malformed input and unsupported operations can produce ordinary application errors. Application-specific protocol failures may instead be encoded in response bytes with Ok(count), when that is the chosen protocol convention: Ok means that a response was produced successfully, not necessarily that the requested business operation succeeded.

This replaces multiple typed host-callable commands and compiler-generated command bindings. The compiler/runtime does not automatically serialize structures, enums or other language values for the host, or dispatch application operation identifiers. Ordinary helpers implement those responsibilities. Existing strict type and conversion rules apply to application parsing and encoding.

### Response status and transport boundary (agreed)

For a classical smart-card target, the response status word (SW) carries the platform's success/error/trap reporting. The response byte array contains application response data; the platform supplies the status separately. The returned u32 is a byte count, not a status word. Error returns preserve their category and code inside CardLang; the platform maps them to the wire status representation.

The exact SW values and mapping, including how application errors, platform errors and traps remain distinguishable under section 6.3, belong to the platform protocol specification. Error codes from different categories must not be treated as an unqualified wire identity merely because they are u16 values. No particular numeric SW assignments are adopted here. Other transports may use their own status envelope while preserving the language outcome distinctions. Reset or power loss may prevent a response altogether.

The platform specification must define which received bytes comprise request (including any transport/APDU header treatment), framing, maximum request size, response capacity, transport length negotiation and status encoding. This entry contract does not silently choose a complete APDU layout or put transport headers/SW into the application arrays. Application payload encoding remains application-defined.

#### Command execution (agreed)

Commands never interleave. Each command completes successfully, returns an error, or terminates with a trap before another command starts. Scheduling or callback dispatch must not start another command while a command is active. A security reset may interrupt execution under the reset rules in section 6.4.

An ordinary trap terminates the current command, not the continued usability of the device or application. Subsequent commands may execute after trap handling and any required persistent transaction rollback. Session changes and runtime-owned resources remain as specified in section 6.4. Serial command execution does not make a whole command an implicit persistent transaction.

### 4.1 Multi-file applications and visibility (agreed)

Keep the first version simple: each application is one compilation unit assembled from an explicit list of source files. All files share one application scope. Files organize source text but do not create modules, namespaces or visibility boundaries.

| Item | Visibility/access |
| --- | --- |
| Application globals and constants | Entire application across all listed source files |
| Functions, structures and error declarations | Entire application across all listed source files |
| Structure fields | Wherever an instance of the structure is accessible |
| Function parameters and locals | Existing lexical scopes; not application-wide |
| Other applications | Inaccessible |
| Platform APIs | Separate reserved interface; exact API TBD |

There are no user-defined namespaces, classes, imports, exports, private/public field/member modifiers or per-file privacy initially. Structs remain data types; application-wide visibility does not grant write access to const values, read-only parameters or references. Existing scope, no-shadowing and aliasing rules still apply.

#### Compilation and duplicate declarations

- The build supplies the source-file list explicitly; source imports are not required.
- File order must not affect name resolution. Functions and types may be used before their declarations, including across files.
- Duplicate declarations are compilation errors, never last-definition-wins. This does not introduce function overloading.
- Mutable globals have no declaration initializers and receive automatic defaults. Nondefault setup belongs in platform lifecycle handlers, not file-order initialization (section 3.9).
- Platform-reserved names may not be redefined by application code.

The concatenation analogy describes shared scope, not literal byte concatenation. Preserve source file/line information in diagnostics, and preserve lexical boundaries so a trailing comment or token in one file cannot consume/change the next file's source. No textual include/preprocessor system is implied.

There is no source-level application wrapper. Each source file contains complete top-level declarations; application identity and the file list come from the build configuration. Manifest/build-file format and the exact reserved platform name set remain tooling/platform details. Earlier application-wrapper sketches have been updated.

#### External access and platform calls

Only the application's single `command` declaration is host-callable, with the byte-oriented signature in section 4. Application code cannot call it directly; shared behavior belongs in ordinary helper functions. Ordinary functions, globals, constants and structure fields are not exposed to the host merely because they are visible throughout the application. There are no inter-application interfaces, calls, shared state or references.

Platform functionality is provided through reserved APIs, to be designed separately. A recognizable spelling such as `card.crypto...` may be used without introducing a general application namespace system; the precise spelling is not fixed. Platform services remain subject to permissions and validation, not unrestricted hardware or memory access.

### 4.2 Name resolution (agreed)

#### Shared top-level naming scope

Globals, constants, functions, commands, structure types, enum types and error-set names share one application-wide naming scope. Distinct declarations cannot reuse the same top-level name, even across different declaration kinds or source files. Names are case-sensitive.

```text
struct Account {
    balance: u32;
}

persistent Account: u32;  // Compilation error: type name already declared.
```

There is no function overloading: the same function name with different parameter types is still a duplicate-declaration error. Forward references to functions and types are allowed across source files. Initialization dependencies are governed separately; finding a name does not imply it may be read during every initializer.

#### Fields and error members

Each structure has its own field-name scope. Different structures may reuse field names; duplicate fields within one structure are errors. Access a field through an instance, not by an implicit bare field lookup.

```text
struct Account {
    balance: u32;
}

struct Summary {
    balance: u32;  // Valid: separate owning structure.
}
```

Error members belong to their named error set and are qualified, for example `WalletError.InsufficientFunds`. They are not automatically imported as bare names. This is owner-qualified lookup, not a general user namespace/module feature.

Dot access resolves from the receiver's type: `buffer.length` is the built-in array property; `account.balance` names a structure field. A structure may declare a field named `length` without conflicting with the array property. No implicit field search or conversion is performed to resolve a name.

#### Parameters, locals and bindings

Parameters, locals, loop indices and pattern bindings obey the existing lexical scopes. They cannot shadow a visible application declaration, parameter, local, loop binding or pattern binding. A same-scope duplicate is also an error. Field names do not become bare visible application names merely because an instance is in scope.

```text
persistent account: Account;

function inspect(source: ref Account) -> u32 {
    return Ok(source.balance);
}
```

Naming the parameter `account` here would shadow the global and is a compilation error; use `source` or another distinct name. Earlier function examples have been adjusted where their parameter names could conflict with the demonstrated globals.

A local becomes available only after its initializer has completed:

```text
var next: u32 = next + 1;  // Compilation error: self-reference in initializer.
```

Default initialization does not make a variable visible during its own explicit initializer. The no-shadowing rule prevents interpreting the same spelling as a hidden outer variable.

Names may be reused in sibling/non-overlapping scopes:

```text
if condition {
    var temporary: u32;
} else {
    var temporary: u32;  // Valid: first binding is not visible here.
}
```

#### Declaration placement and reserved names

Function, command, structure, enum and error-set declarations are top-level only initially; they cannot be declared inside functions or commands. A structure may have fields whose types are other structures; this does not imply lexically nested type declarations.

Compiler-provided built-ins and reserved platform interface names cannot be redeclared or shadowed. Exact platform names are supplied with the platform API specification. Keywords remain unavailable as identifiers, and `_` alone is reserved for an ignored pattern.

Constant dependencies are resolved independently of file order, and cycles are compilation errors (section 3.10). Mutable-global initializers are forbidden, so they have no dependency/order mechanism. Lifecycle handler scheduling remains platform-defined. Name lookup does not introduce source-file-dependent initialization.

## 5. State: scope and lifetime

Scope and lifetime are separate concepts.

| Kind | Intended meaning | Still to define |
| --- | --- | --- |
| Persistent application state | Survives reset | Initialization, updates, deletion, upgrades and transactions |
| Session application state | Shared within the application; defaulted on chip power-on, preserved on ordinary traps, cleared by security reset | Any additional lifecycle behavior such as deselection/channels; application authentication policy |
| Local state | Belongs to a function/command invocation | Stack layout, reference lifetimes and cleanup |

“Global” means application-wide. Cross-application calls, shared application state and references are forbidden in the initial isolated-application model.

Simple durable values should be easy to declare. Larger persistent data may use a separate object API rather than requiring the entire data set in RAM.

### 5.1 Agreed declaration syntax

At application scope, use exactly one of three declaration keywords:

| Global keyword | Meaning | Changeable? |
| --- | --- | --- |
| `persistent` | State surviving reset | Yes |
| `session` | State initialized to type defaults on chip power-on and cleared by security reset; preserved across commands and ordinary traps | Yes |
| `const` | Compile-time constant without a session lifetime | No |

```text
persistent counter: u32;
session authenticated: bool;
const MAX_ACCOUNTS: u16 = 16;

function increment() {
    var step: u32 = 1;
    var next: u32 = counter + step;
    counter = next;
    return Ok();
}
```

Inside functions and commands, use plain `var` for local values. Local `const` declarations are not supported for now; immutable locals may be reconsidered later. There is no `local` keyword. Global `const` remains a compile-time constant.

Compilation rules:

- Plain `var` at application scope is forbidden; use `persistent` or `session` for global mutable state.
- Plain global `const` is valid and requires no storage qualifier.
- Do not combine global qualifiers: forms such as `persistent var`, `session var`, `persistent const` and `session const` are forbidden.
- `persistent`, `session` and `const` declarations inside functions or commands are forbidden; local value declarations use `var`.
- Every value declaration needs a keyword valid at its location.
- Assigning to a `const`, including its array elements or structure fields, is forbidden.
- These rules concern value declarations. A `struct` declaration defines a type, not a stored instance, and needs no storage qualifier. Parameter modes and binding mutability are defined in section 3.7.

Invalid examples (intentionally fail compilation):

```text
var counter: u32 = 0;                 // Global var forbidden.
persistent var value: u32 = 0;        // Combined qualifiers forbidden.
session const limit: u32 = 100;       // Combined qualifiers forbidden.
persistent const fixed: u32 = 10;     // Combined qualifiers forbidden.

function process() {
    session ready: bool = false;      // Session declaration forbidden here.
    persistent value: u32 = 0;        // Persistent declaration forbidden here.
    local var count: u32 = 0;         // No local keyword.
    const step: u32 = 1;              // Local const deferred; use var.
}
```

This replaces the earlier two-part global storage/mutability scheme. `session const` is not a supported declaration. A durable value fixed during provisioning would need a separate mechanism later; global compile-time constants do not provide that mechanism.

Persistent initialization is not repeated on every reset. Global constants require no writable persistent state; their physical representation is an implementation detail. Power-on defaults, ordinary-trap preservation and security-reset clearing are defined. Any additional session lifecycle events and detailed reference enforcement remain open; reference and slice lifetimes are call-scoped (sections 3.7-3.8 and 8.4). Block visibility and no-shadowing rules are specified in section 3.6.

“Global” means within the application, not shared between applications. Visibility and storage lifetime are separate concepts.

## 6. Arithmetic and error handling

### 6.1 Function outcomes and explicit handling

Agreed direction: every function returns a result, either successful completion (with a value when applicable) or a recoverable error. General-purpose exceptions are not part of the initial design. Traps remain separate execution faults and are not `Err` outcomes.

The signature names the successful value type rather than explicitly writing a result wrapper:

```text
function subtract(current_balance: u32, amount: u32) -> u32 {
    require amount <= current_balance else WalletError.InsufficientFunds;
    return Ok(current_balance - amount);
}
```

Here `-> u32` describes the successful payload type, not a guarantee of success. `return Ok(balance - amount);` produces success; a failing `require` produces an error. Explicit `Ok`/`Err` return syntax is agreed and supersedes the earlier implicit-success return proposal. All functions use a common error value representation, with application and platform categories as defined in section 6.3. No-value successful completion uses `return Ok();` and matches `Ok()`; its signature omits the return arrow and type. Host-command success carries a u32 response byte count. Outcome reporting uses a platform status envelope; a classical smart-card target uses SW as described in section 4. Exact status mappings remain platform-defined.

Agreed explicit handling syntax:

```text
match subtract(balance, amount) {
    Ok(value) => {
        balance = value;
    }
    Err(error) => {
        // Handle the error here.
    }
}
```

`match` selects a branch. `Ok(value)` exposes the successful value; `Err(error)` exposes the recoverable error. These bindings are introduced by patterns, not by local `const` declarations. Bindings are read-only and arm-local, and handling must be exhaustive as specified in section 3.6. No-value success matches `Ok()`.

The alternative `call ... into ... otherwise` syntax was rejected. Both `match` and `attempt` are retained: the former handles outcomes locally and the latter propagates errors (section 6.3).

### 6.2 Arithmetic

Current operation direction:

```text
a + b                 // Checked; overflow traps.
checked_add(a, b)      // Recoverable success/error outcome; inspect with match.
wrapping_add(a, b)     // Explicit modular arithmetic.
```

Arithmetic operators are distinct from ordinary function calls. Fill is a compiler-provided array-construction intrinsic producing a direct array value, not a Result (section 8.3). Checked arithmetic intrinsics return outcomes, while wrapping_add/sub/mul are direct-value intrinsics as specified in section 6.5.

A recoverable subtraction can be inspected similarly:

```text
match checked_sub(balance, amount) {
    Ok(value) => {
        balance = value;
    }
    Err(error) => {
        // Recover, map, or propagate with return Err(error).
    }
}
```

Often a business-rule check is clearer:

```text
require amount <= balance else WalletError.InsufficientFunds;
balance = balance - amount;
```

The `require` syntax expands to an `if` returning `Err` on a false condition, as defined in section 3.6. It uses the common error representation and must obey the transaction-boundary exit rule. A `match` handles `Err`; it does not catch overflow traps, bounds faults or other VM traps.

Proposed arithmetic failure categories:

| Condition | Proposed outcome |
| --- | --- |
| Unsigned subtraction below zero | Underflow |
| Signed or unsigned result above the type maximum | Overflow |
| Signed result below the type minimum | Underflow |
| Division by zero | Division-by-zero failure |
| Checked conversion out of destination range | Recoverable conversion error; see section 3.2 |

Signed division/shift behavior is defined in section 3.5; the remaining arithmetic edge cases and intrinsic families are specified in section 6.5. Checked arithmetic errors use the common platform-error representation; exact numeric codes belong to the platform catalog. Numeric conversion and operand type rules are defined in section 3.

Earlier `try/catch` arithmetic sketches are superseded by results and traps. Use `attempt` for concise recoverable-error propagation.

### 6.3 Result consumption, errors and reporting (agreed)

#### Outcomes are not stored values

Results are transient function outcomes, not ordinary stored values. No user-visible `Result<T>` type is provided initially. An outcome cannot be stored in a variable, constant, structure field or array, or passed as a function parameter. These restrictions apply equally to outcome-producing compiler intrinsics such as checked arithmetic and checked conversion. Every outcome must be consumed immediately by `match`, `attempt` or a compatible whole-outcome forwarding return.

```text
var value: u32 = read_value();  // Compilation error: an outcome is not a u32.
```

Use `var value: u32 = attempt read_value();` to extract success and propagate failure, or use a `match` to handle both cases locally. A forwarding `return read_value();` requires exactly matching successful types, including the no-payload case.

`Ok` and `Err` are restricted syntax for return statements and match patterns, with `Err` additionally permitted in `abort Err(error);`; they are not general constructors for storable values. `return Ok(expression);`, `return Ok();` and `return Err(error);` construct the enclosing function's outcome. `abort Err(error);` rolls back the enclosing transaction before returning the error outcome (section 7.2). Nested results, result-typed parameters and aggregates containing outcomes are not supported initially. A successful aggregate return contains ordinary supported values, not another outcome.

#### Exact typing and use of attempt

For a call whose successful payload type is `T`, `attempt call(...)` produces exactly `T`, with no implicit conversion or default value. Arrays and structures follow the independent-value copy rules. On failure, `attempt` immediately returns the unchanged error from the enclosing function or command. Its enclosing function's successful type need not match the called function's successful type:

```text
function is_nonzero() -> bool {
    var value: u32 = attempt read_value();
    return Ok(value != 0);
}
```

This fragment assumes `read_value` is declared with successful type `u32`. `attempt` never catches traps and retains all existing transaction-boundary restrictions.

A no-payload call uses the statement form `attempt authenticate();`. This statement form is permitted only for no-payload success; it cannot silently discard a successful payload. A no-payload outcome cannot supply an ordinary expression value. To deliberately ignore a successful payload while still handling failure, use `Ok(_)` in a match:

```text
match read_value() {
    Ok(_) => {
        // Deliberately ignore the successful value.
    }
    Err(error) => {
        return Err(error);
    }
}
```

#### Every ordinary function outcome must be handled

Discarding a function outcome is a compilation error. Use one of:

- `match`: handle success and failure locally.
- `attempt`: extract success or immediately propagate the unchanged error.
- `return function(...)`: forward the complete outcome when the successful payload types match (including no-value success).

```text
var remaining: u32 = attempt subtract(balance, amount);
attempt authenticate(pin);  // Function with no successful payload.
return subtract(balance, amount);  // Whole-outcome forwarding in a compatible function.
```

These are independent fragments; the assumed function signatures must match their uses. `attempt` is an expression when a success value is needed, and may be used as a statement for no-value success. It handles `Err` only, never a trap. The exact error is propagated without reclassifying or renumbering it.

Because `attempt` implicitly returns on failure, it cannot cross a transaction boundary opened in the current function. A called function may use `attempt` when that return does not cross a transaction it opened; it merely returns to the caller, even when the caller has an active transaction. Whole-outcome forwarding returns have the same boundary restrictions.

#### Application error declarations

One named error set per application initially, with explicit numeric codes:

```text
errors WalletError {
    InsufficientFunds = 1;
    AccountBlocked = 2;
    InvalidAmount = 3;
    Unauthorized = 4;
}
```

- Codes are nonzero `u16` values. Zero is reserved and cannot identify an error; success is represented by `Ok`.
- Duplicate names or codes in the application error set are compilation errors.
- Published codes must not change meaning or be reused for a different error after removal.
- Application errors carry identity only, without strings or arbitrary payloads initially.
- Source uses names: `return Err(WalletError.InsufficientFunds);`.
- Explicit codes supersede the temporary proposal for compiler-assigned, build-dependent error identifiers.

All functions share a common error value representation. Platform errors use a reserved namespace such as `CardError`, with platform-defined nonzero `u16` codes. Application-defined names cannot impersonate that namespace. An error's category distinguishes application codes from platform codes; numeric ranges need not be partitioned between the categories. The exact representation/encoding of this category remains a platform design detail.

#### Restricted error bindings (agreed)

There is no ordinary user-declarable error value type initially. An `Err(error)` pattern introduces an arm-local, read-only binding whose only permitted uses are unchanged propagation through `return Err(error);` or, lexically inside a transaction, `abort Err(error);`. It cannot be copied, stored, compared, passed as an argument, returned as an `Ok` payload or used in a `require` expression. It needs no application-written type annotation. Other handling statements may run in the arm before propagation; a binding need not be used. Use `Err(_)` to explicitly ignore an error, and specific error patterns to distinguish cases. Named error members are permitted in `return Err(...)`, `abort Err(...)`, `require ... else ...` and specific `Err(ErrorSet.Member)` patterns, without becoming ordinary storable values.

Applications are completely isolated: no cross-application calls, references, shared application state or error forwarding. Different applications may reuse names and numeric codes. There is no application-origin field in each error; the host already knows which application it addressed. Propagation within an application preserves the category and code.

#### Matching a particular error

```text
match debit(inout account, amount) {
    Ok() => {
        // Completed.
    }
    Err(WalletError.InsufficientFunds) => {
        // Handle this error locally.
    }
    Err(error) => {
        return Err(error);
    }
}
```

Handle specific errors first, followed by the mandatory final `Err(error)` or `Err(_)` catch-all for remaining failures. Result matching requires exactly one success arm and exactly one final error catch-all. Duplicate patterns, unreachable arms and type-incompatible patterns are compilation errors, following section 3.6.

Ordinary return or propagation of `Err` is not a rollback request. Prior persistent commits and session mutations remain, and a caller's active transaction is not automatically aborted by a callee returning an error. The transaction owner may handle that outcome locally and continue, or explicitly use `abort Err(error);` to roll back its transaction before returning the error.

#### Host reporting

Keep four reporting categories distinct:

| Category | Meaning |
| --- | --- |
| Success | Ordinary function success payload or no payload; at the host entry point, u32 response byte count |
| Application error | Application-assigned `u16` error code |
| Platform error | Platform-defined `u16` recoverable error code |
| Trap | Command aborted due to an execution fault |

A trap must not masquerade as a recoverable application/platform error. For a classical smart-card target the response SW reports the outcome, separately from application response data. Exact status-word mapping, byte order, category encoding, trap reporting codes and permitted diagnostics remain part of the card-protocol specification. Application response bytes are transmitted only for Ok(count), within capacity; Err and traps suppress any partial response payload. A reset or power loss may prevent any response. No internal VM details are automatically disclosed to the host.

### 6.4 Traps, rollback and volatile state (agreed)

| Outcome | Persistent state | Volatile state |
| --- | --- | --- |
| `Err(error)` | Earlier writes remain; error return does not itself trigger rollback | Preserved, subject to normal function-frame lifetimes |
| `abort Err(error);` | Roll back the enclosing transaction; retain previous commits and completed standalone atomic assignments | Preserve session state; discard the returning function/command's frame under normal return rules |
| Language/VM trap | Roll back the active transaction; retain previous commits and completed standalone atomic assignments | Preserve session state; discard terminated call frames |
| Runtime-issued security reset, including fatal platform failure | Platform recovery must preserve promised atomicity/transaction guarantees | Whole-chip reset wipes session/volatile state; subsequent session initialization restores type defaults |

A trap aborts the current command and is not catchable by application `match` or `attempt`. Transactions restore persistent changes only, not session state or local working values. Ordinary trap handling does not reset or reinitialize application session variables. Consequently session state may be partially updated when a command traps; that is intentional and must be visible in the specification. Locals do not survive termination of their call frames.

Defined trap cases include arithmetic overflow/underflow and invalid division/remainder, out-of-bounds access, invalid shift counts, stack/execution-budget exhaustion, attempted nested transactions and invalid VM instructions/state. Details already left open for particular arithmetic cases remain open. The final trap-code catalog, service-specific recoverable error catalog and distinction between safely contained VM faults and fatal runtime integrity failures require a platform contract.

The runtime may issue a security reset; a real/fatal platform failure requires one. A security reset clears volatile state, including session variables, across all applications. Subsequent session initialization restores the recursive type defaults. It is not returned as an ordinary recoverable `CardError`. Hardware reset, secure cleanup, persistent recovery, interrupted-commit behavior and fail-closed handling if recovery cannot complete belong primarily to the platform specification. The language only acknowledges that such failures may terminate execution without an outcome while retaining its persistent atomicity guarantees.

An ordinary trap is an execution fault after which the device and application can continue serving subsequent commands. The trap itself does not automatically delete, invalidate or clean up runtime-owned resources. An individual resource operation must still specify the state it leaves on failure; preserving resources on trap does not promise that an interrupted operation completed successfully or that earlier resource mutations are undone. Resource behavior on power-on and security reset remains a platform/resource lifecycle contract.

Maintaining logical consistency between session and persistent state is the application programmer's responsibility. The runtime does not infer application invariants or synchronize, repair or invalidate session variables when persistent state is rolled back. For example, a session cache updated before a transaction abort may differ from the restored persistent value; application logic must arrange cache invalidation or reconstruction as appropriate. Non-interleaving commands prevent another command from running midway through the operation, but do not remove this responsibility after failure.

| Event | Session state | Runtime-owned resources |
| --- | --- | --- |
| Chip power-on | Initialized to recursive type defaults | Follow their defined power-on lifecycle |
| Ordinary trap | Preserved; current command frames terminate | No automatic cleanup, deletion or invalidation caused by the trap |
| Security reset | Wiped; subsequent initialization restores defaults | Follow their platform-defined reset lifecycle |

`abort Err(error);` deliberately rolls back the enclosing transaction and returns a recoverable error without trapping. It is valid only lexically inside that transaction and does not resume execution after the block. Ordinary boundary-crossing returns remain forbidden. Session changes are not rolled back. See section 7.2 for the full contract.

### 6.5 Integer arithmetic edge cases and intrinsics (agreed)

Ordinary integer arithmetic is checked for both signed and unsigned types. These semantics do not change with build/optimization mode; no release mode silently disables required arithmetic behavior. A compiler may remove a check only if it proves the operation cannot fail, preserving all observable semantics.

#### Signed minimum division and remainder

| Case | Ordinary operator | Checked intrinsic |
| --- | --- | --- |
| Signed minimum divided by -1 | Trap: quotient is unrepresentable | checked_div returns recoverable arithmetic error |
| Signed minimum remainder -1 | Return zero | checked_rem returns Ok(0) |
| Division/remainder by zero | Trap | checked_div/rem returns recoverable arithmetic error |

For i8, -128 / -1 overflows, but -128 % -1 is defined as 0. The VM must implement the remainder case deliberately, even if the host language or CPU combines division/remainder and would fault or leave that case undefined. There is no dependency on C integer promotions or host-language overflow rules. Signed division otherwise truncates toward zero; a nonzero remainder has the dividend's sign.

#### Unary negation

Unary minus applies only to signed integers. Applying it to an unsigned typed value is a compilation error; no implicit signed conversion occurs.

```text
var signed_value: i16 = 10;
var negative: i16 = -signed_value;

var minimum: i8 = -128;
var invalid: i8 = -minimum;  // Runtime unrepresentable negation traps.
```

The existing negative-minimum literal rule is unchanged: -128 is accepted in an i8 context without first requiring positive 128 to fit i8. Negating a minimum signed runtime value is different: its positive counterpart is unrepresentable. The source grammar has no separate signed-negative literal token.

#### Checked arithmetic family

These compiler intrinsics return Ok(value) or a recoverable platform arithmetic error:

| Intrinsic | Operand types | Arithmetic failure |
| --- | --- | --- |
| checked_add | Matching integer types | Result outside destination range |
| checked_sub | Matching integer types | Result outside destination range |
| checked_mul | Matching integer types | Result outside destination range |
| checked_div | Matching integer types | Zero divisor or unrepresentable quotient |
| checked_rem | Matching integer types | Zero divisor |
| checked_neg | Signed integer | Unrepresentable negation |

The successful payload has the operand integer type. Literal operands follow existing contextual typing. Intrinsics do not trap for the arithmetic conditions they specifically check, but traps during argument evaluation propagate normally. All use the common categorized error value; precise platform arithmetic error names/codes are specified separately.

#### Wrapping arithmetic family

Provide only wrapping_add, wrapping_sub and wrapping_mul initially. These are direct-value compiler intrinsics accepting matching integer types and returning that same type, not a Result.

They compute modulo 2^N, where N is the type width. Signed results interpret the resulting bits as two's complement. No wrapping division, remainder or negation intrinsic initially. Argument evaluation may still trap; wrapping only specifies the arithmetic operation itself.

#### Compile-time policy and diagnostics

Checked and wrapping arithmetic intrinsics remain excluded from constant expressions initially, as does checked_convert. Guaranteed convert is allowed for constant operands under section 3.10. Constant expressions retain ordinary checked operators; this does not add compile-time Result handling.

| Condition | Required behavior |
| --- | --- |
| Invalid operand types or out-of-range literal | Compilation error |
| Arithmetic failure evaluated in a required constant expression | Compilation error |
| Ordinary runtime arithmetic failure | Trap |
| Arithmetic failure handled by checked intrinsic | Err |
| Explicit wrapping operation | Defined modular result |

A short-circuited operand is still type-checked but not evaluated. No implicit widening rescues intermediate arithmetic. Numeric platform error/trap encodings remain a platform concern; the language-visible success/error/trap distinction is fixed here.

## 7. Transactions and failure

### 7.1 Atomic persistent assignments

Agreed direction: a single assignment to a persistent destination is atomic. After interruption and recovery, the destination contains either its complete previous value or its complete new value, never a partially written value. Persistent assignments are permitted outside explicit transactions.

```text
balance = balance - amount;
account.identity.version = 2;
account.counters[0] = account.counters[0] + 1;
```

The assignment destination defines the update: a scalar, selected field or selected array element in these examples. If evaluating the right-hand side fails before the assignment, that destination update does not happen. This does not roll back side effects performed while evaluating the right-hand side.

For an aggregate destination, the intended rule covers the whole assignment:

```text
account = replacement;  // Whole structure assignment is atomic.
```

Whole-array assignment is intended to follow the same destination-based rule. The storage implementation, maximum supported atomic-write size and behavior for unsupported sizes still need specification. Atomicity does not mean that a single hardware write performs the operation, nor does it make a multi-assignment command atomic. Commands do not interleave, but interruption and power-loss recovery still follow assignment/transaction boundaries.

Two assignments are not collectively atomic by default:

```text
balance = balance - amount;
sequence = sequence + 1;
```

An interruption may occur between them. Function calls and their side effects are not automatically atomic merely because they participate in an assignment expression.

### 7.2 Explicit transactions

Transactions group persistent changes with defined commit and power-loss recovery semantics.

```text
transaction {
    balance = balance - amount;
    sequence = sequence + 1;
}
```

A language/VM trap aborts the command and rolls back its active transaction's persistent changes only. Previously committed writes remain committed; session state is preserved, while terminated call frames are discarded. Session/local mutations are not transactionally restored. A command is not implicitly atomic as a whole. Fatal platform failure instead triggers the whole-chip reset described in section 6.4.

Returning an error is distinct from trapping. Early `return`, `break` and `continue` transfers across a transaction boundary are compilation errors (section 3.6). Normal completion at the closing brace commits; `abort Err(error);` rolls back and returns a recoverable error; a trap rolls back and aborts the command. Returning from a called function does not exit the caller's transaction.

#### Commit point and read-your-writes

Reaching the closing brace commits all persistent writes in the transaction together. Execution continues after the block only after successful commit. A transaction with no persistent writes is valid. A trap before commit rolls back all persistent changes in the active transaction; previously committed transactions and standalone assignments remain committed.

Reads within the transaction see earlier writes in that transaction, including reads through references and called functions:

```text
transaction {
    counter = counter + 1;
    last_counter = counter;  // Reads the incremented value.
}
```

These are language-visible semantics, not a requirement to implement transactions with a particular copying or journaling mechanism.

#### Participating state and recoverable errors

Only persistent application state participates automatically. Session variables and locals behave normally and are not restored on rollback. A completed session write survives an ordinary trap; locals disappear when their call frames terminate. Runtime-owned resource operations participate only when their platform API explicitly guarantees it; otherwise the API must define its transaction behavior or prohibit use during a transaction.

`Err` is a recoverable function outcome, not an abort request. Persistent changes made by a callee before it returns `Err` remain in the active transaction. If the caller handles the error locally and execution reaches the closing brace, those changes commit:

```text
transaction {
    match perform_update() {
        Ok() => {
            // Continue.
        }
        Err(error) => {
            // Handle locally; the transaction remains active.
        }
    }
}
```

The fragment assumes a no-payload helper. To abandon the pending persistent changes instead, the transaction owner uses `abort Err(error);` as defined below. `attempt` remains forbidden where its implicit failure return would cross a transaction opened in the current function; a callee may use it when returning only to its caller inside that caller's transaction.

#### Explicit recoverable abort (agreed)

Use `abort Err(error);` to roll back a transaction and return a recoverable error from the enclosing function or command:

```text
transaction {
    balance = balance - amount;

    match record_payment(amount) {
        Ok() => {
            // Continue toward commit.
        }
        Err(error) => {
            abort Err(error);
        }
    }
}

return Ok();
```

This fragment assumes a persistent balance, a validated amount of the same integer type, a no-payload record_payment helper and a no-payload enclosing ordinary function. The host command returns a response count rather than Ok().

The statement has the following semantics:

1. Stop executing the transaction body; do not execute subsequent statements in the body or after the transaction in the enclosing function/command.
2. Roll back all persistent changes in that transaction, including changes made through references or called helpers.
3. Return the specified categorized error from the enclosing function or command. Preserve its category and code unchanged.

Only persistent state participating in the transaction is rolled back. Earlier committed transactions and completed standalone assignments remain committed. Session mutations remain; locals follow normal function-return lifetimes. Resource effects retain their separately specified platform transaction behavior. Abort does not turn the error into a trap or introduce a new host-reporting category. If the transaction belongs to an ordinary function, its caller receives Err normally and may handle it; abort does not by itself terminate that caller or the entire command.

`abort` is valid only lexically inside a transaction in the same function or command. A helper cannot use it merely because its caller has an active transaction; that is a compilation error. The helper returns Err normally, and the transaction owner decides whether to recover locally or abort. Nested transactions remain forbidden.

The operand must be a named application/platform error member or an in-scope Err pattern binding. Both `abort Err(WalletError.InsufficientFunds);` and `abort Err(error);` are valid with the corresponding declaration/binding. Bare `abort;`, `abort error;`, `abort Ok(...);` and abort outside a lexical transaction are compilation errors. Abort is a statement, not an expression, and requires a semicolon. It returns an error regardless of the enclosing successful payload type.

| Exit | Persistent transaction effect | Execution effect |
| --- | --- | --- |
| Reach closing brace normally | Commit | Continue after the block |
| `abort Err(error);` | Roll back | Return Err from the enclosing function/command |
| Trap | Roll back | Abort the current command |

Ordinary return and implicit error propagation through attempt or require retain their existing boundary restrictions. Only explicit abort requests recoverable rollback; handling an Err locally does not automatically abort. Abort provides no savepoint or rollback-and-continue form.

#### Commit failure and interruption

A failed commit must never resume normal execution after the block as though it succeeded. A safely contained commit failure terminates the command with a trap; an integrity failure requires the platform's whole-chip security-reset handling. After interruption or recovery, persistent state reflects either the complete transaction or none of it, never a partial commit. The exact storage mechanism, recovery procedure and failure classification belong to the platform specification. A reset or power loss may prevent a host response.

Commands do not interleave: no other command starts before the current command finishes or fails. Platform lifecycle/callback rules must also preserve transaction visibility and recovery guarantees, and must not dispatch a reentrant command. Detailed non-command lifecycle scheduling remains a platform responsibility.

No additional language-level commit protocol is introduced. Reaching the closing brace performs commit, and successful completion of the block means its persistent writes are committed. A trap before commit rolls back the active transaction. Interruption during commit recovers to the complete old or complete new persistent state according to the platform's recovery mechanism; its internal progress and storage decisions are not language semantics. A later trap does not undo an already committed transaction.

### 7.3 No nested transactions (agreed)

Only one transaction may be active in an execution context. Starting a transaction while one is already active is forbidden, whether nesting is lexical or occurs through a function call.

| Situation | Behavior |
| --- | --- |
| Persistent assignment outside a transaction | That assignment is atomic |
| Persistent assignments while a transaction is active | Participate in the active transaction and commit/roll back together |
| Start a transaction while another is active | Forbidden |

```text
function update() {
    transaction {
        // Persistent updates.
    }
    return Ok();
}

// Invalid nesting through a call:
transaction {
    match update() {
        Ok() => {
            // update attempts to start a nested transaction.
        }
        Err(error) => {
            // Handling a result does not catch a transaction-nesting trap.
        }
    }
}
```

Reject nesting statically when the compiler can establish it. Otherwise the runtime checks before the inner transaction starts; a violation traps, aborting the command and rolling back the active outer transaction under the existing trap rules. There is no inner savepoint, partial commit or automatic flattening of nested transaction blocks.

A called function may write persistent data without opening a transaction of its own; those assignments join the caller's active transaction. If called without an active transaction, its individual persistent assignments are independently atomic. Returning from that function does not end the caller's transaction. Returning `Err` still does not automatically roll back mutations; the caller must follow the result and transaction-boundary rules.

The existing prohibition on `return`, `break` and `continue` crossing transaction boundaries remains unchanged. Cross-application transactions are excluded by complete application isolation. Commands never interleave. The precise execution-context definition for non-command lifecycle work remains a platform detail.

### 7.4 Remaining transaction questions

- What atomic-write size limits apply to fields, arrays and structures, and how are unsupported operations rejected?
- What limits apply to transaction size?
- Which platform services, cryptographic/resource operations and host I/O are permitted in a transaction, and how do their effects participate? Application reads and ordinary helper calls already obey the rules above.
- At what point may a response be sent relative to durable commit?

Under the single-entry contract, the response buffer is transmitted only after successful command completion, so response transmission does not occur inside a transaction. Writes into the output buffer are ordinary volatile writes, not external transmission and not persistent transaction changes. Other externally visible platform services still need explicit transaction contracts.

## 8. Arrays and slices

Fixed arrays are supported at application scope and locally, for supported fixed-size integer, boolean and structure element types. Enums are supported array element types under section 3.11.

Agreed array declaration and initialization syntax:

```text
persistent identifier: u8[4];
session scratch: u8[128];
session values: u8[128];

function process() {
    var buffer: u8[64] = fill(0);
    buffer[0] = 0xA5;
    return Ok();
}

// Illustrative setup helper; lifecycle binding is platform-defined.
function example_setup_identifier() {
    identifier = [0x01, 0x02, 0x03, 0x04];
    values = fill(10);
    return Ok();
}
```

The array type is `T[N]`: `T` is the element type and `N` is the number of elements. For example, `u8[128]` is an array of 128 unsigned bytes.

| Initializer | Meaning |
| --- | --- |
| `fill(0)` | Initialize every element to zero |
| `fill(10)` | Initialize every element to 10 |
| `[0x01, 0x02, 0x03, 0x04]` | Initialize with the listed elements, in order |

`fill(value)` gets the required element count from the destination array type in a constant/local initializer or assignment. It has no separate length argument. An explicit list must contain exactly the declared number of elements: too few or too many is a compilation error, with no implicit padding or truncation. Element values must match the element type under the existing contextual typing and explicit conversion rules; no implicit element conversions are introduced.

```text
session scratch: u8[128];
session values: u8[128];
session short: u8[4];
session long: u8[2];

// Illustrative setup helper; lifecycle binding is platform-defined.
function example_setup_values() {
    values = fill(10);     // Valid: 128 values of 10.
    short = [1, 2];         // Compilation error: expected 4 elements, got 2.
    long = [1, 2, 3];       // Compilation error: expected 2 elements, got 3.
    return Ok();
}
```

There is no special `zero` keyword or initializer: `fill(0)` explicitly requests zero initialization, and omitting the variable initializer defaults integer arrays to zero (section 3.9). The earlier semicolon-based type and repetition syntax is superseded. Explicit construction forms apply to constant/local initializers and runtime assignments, including assignments to session/persistent arrays. Mutable-global declarations have no initializer; runtime persistent assignments obey atomicity/transaction rules.

Other supported element types (local declaration fragments):

```text
var counters: u32[8] = fill(0);
var enabled: bool[8] = fill(false);
```

Slices use buffer[start..end] to select a borrowed half-open region. Unspecified-size ref/inout parameters accept whole arrays or slices (section 8.4).

Array rules:

- Fixed-array lengths are compile-time constants; slices and unspecified-size parameters have runtime lengths.
- Indexing and slice bounds are checked against the receiver length.
- Elements have defined defaults when the variable initializer is omitted; explicit initialization must be complete (section 3.9).
- Mutation is explicit.
- References obey the call-scoped lifetime and access rules in sections 3.7-3.8.
- Fixed-array assignment copies elements independently; borrowing a slice does not copy elements.
- `byte` may be an alias for `u8`.

Direct multidimensional arrays and owned variable-length bounded buffers remain deferred. Borrowed slices are supported. Bounds checks apply before array-element and slice reference calls. The optional byte alias remains a separate naming proposal.

### 8.1 Array length and indexing (agreed)

Every array exposes a read-only `.length` property:

```text
session buffer: u8[128];

// Inside a function/command:
var size: u32 = buffer.length;  // 128.
```

Rules:

- `.length` returns `u32` regardless of element type.
- It counts elements, not bytes.
- It cannot be assigned to; `buffer.length = 10;` is a compilation error.
- For a fixed array, its length is known at compile time and requires no runtime length field.
- For a slice or unspecified-size parameter, .length is the supplied region's runtime element count as u32; it is not a required constant expression.
- It is available on array variables, array fields and array parameters in all three parameter modes (value, `ref`, `inout`).

```text
account.identifier.length
```

The fragment above accesses the length of an array field. The same element-count rule applies to non-byte element arrays; `.length` is not a storage-size operator. Permitted array lengths must be representable by `u32`; smaller platform capacity limits belong to the target profile.

Runtime `.length` still evaluates its receiver, preserving calls, errors and bounds checks even when a fixed array's resulting length is type-known:

```text
var size: u32 = records[attempt choose_index()].bytes.length;
```

This assumes records is an array of structures with a fixed-array field named bytes and choose_index returns a valid unsigned index type. Execute choose_index, propagate any Err, and check the selected index before producing the length; an invalid index traps. A compiler cannot replace the whole expression with a literal and erase observable evaluation. If such an expression occurs in a call argument, the no-nested-call rule still applies. Constant-expression eligibility is separately defined in section 3.10.

Range loops work naturally with `.length`:

```text
for index: u32 in 0..buffer.length {
    buffer[index] = 0;
}
```

Indexing accepts `u8`, `u16` or `u32`, with bounds checks. A signed integer index is a compilation error, even if its current value is nonnegative. No implicit numeric conversion between ordinary typed values is introduced; indexing explicitly accepts the unsigned integer types.

```text
var small_index: u8 = 0;
var wide_index: u32 = 0;
buffer[small_index] = 1;  // Valid if in bounds.
buffer[wide_index] = 2;   // Valid if in bounds.

var signed_index: i16 = 0;
buffer[signed_index] = 3; // Compilation error: signed index.
```

An index is valid exactly when its mathematical value is less than the array's element count. Runtime out-of-bounds access traps; no truncation or wrapping of an index is allowed. Array-element references must pass the check before entering the callee as already specified. Otherwise-untyped literal-only index expressions receive u32 context as specified in section 3.3. Already typed unsigned indices retain their type; this is not a general default integer type.

### 8.2 Remaining fixed-array decisions (agreed)

#### Element types and shape

Arrays may contain supported fixed-size integer types, bool and structures. Enums are supported element types. Structures and arrays nested through structure fields remain subject to finite-size/nonrecursive-containment rules.

```text
session counters: u32[8];
session enabled: bool[8];
session accounts: Account[4];
```

These globals receive recursive defaults; they do not have declaration initializers. Every array length is a positive unsigned constant expression representable by u32. A zero length is a compilation error. Platform capacity limits remain separate.

Direct multidimensional/array-of-array types are deferred initially; use arrays of structures containing fixed-array fields when needed. No implicit resizing or variable-length owned array values are introduced. Borrowed slices are defined in section 8.4.

#### Whole-array assignment

Source and destination must have exactly matching element types and lengths:

```text
var source: u8[16];
var destination: u8[16];
destination = source;  // Independent complete copy.
```

Different lengths or element types are compilation errors. Copies include nested structure/array field values without hidden sharing. No implicit element conversion, padding or truncation is permitted. Assignment to a persistent array is atomic for the whole destination under the existing persistent-assignment rule; target capacities/enforcement remain platform responsibilities.

Automatic array equality is omitted initially. Comparing lengths does not compare contents.

#### Fill evaluates once

`fill(expression)` obtains its element type and length from the destination. Evaluate the expression exactly once, then copy the successful value independently into every element:

```text
var next_byte: u8 = attempt read_byte();
buffer = fill(next_byte);
```

This fragment assumes a byte array and a function returning a byte outcome. The read happens before fill, complying with the no-nested-argument-call rule. read_byte runs once. If it returns Err, attempt propagates it and the assignment does not occur. Earlier evaluation side effects are not automatically rolled back. A trap follows normal trap/transaction rules.

For aggregate values:

```text
var template: Account = Account {
    balance: 100,
    identifier: fill(0),
    counters: fill(0)
};
accounts = fill(template);
```

This assumes the matching Account type. Construct the local template first, evaluating its fields in written order, then pass it to fill and copy its complete value independently into each array element. This keeps its field-initializer intrinsic calls outside fill's argument. No shared object/reference is created by fill. Constant fill arguments remain restricted to constant expressions.

#### Indexed assignment evaluation order

```text
buffer[index] = attempt read_byte();
```

1. Evaluate the destination index once.
2. Check bounds.
3. Evaluate the right-hand side.
4. Perform the assignment.

An invalid index traps before the right-hand side executes. Do not reevaluate the index after the right-hand side, even if that evaluation changes other state. Persistent element writes remain atomic, and all reference/aliasing restrictions continue to apply.

This specifies indexed-assignment ordering; general left-to-right expression evaluation and pre-call reference validation remain unchanged. Compile-time evaluation failures use existing diagnostic rules; runtime bounds failures trap.

### 8.3 Fill intrinsic (agreed)

`fill(expression)` is a reserved, compiler-provided array-construction intrinsic, not an ordinary function. It produces an array value directly, not an Ok/Err outcome. Applications cannot redefine it.

| Aspect | Rule |
| --- | --- |
| Expected type | A fixed array type must be known from context; otherwise compilation fails |
| Element type and length | Supplied by the expected array type |
| Argument evaluation | Exactly once |
| Population | Independent copies of that value in all elements |
| Aggregate elements | Complete value copies, including nested structure/array fields |
| Allocation | No dynamic array allocation |
| Constant evaluation | Allowed only when the argument is constant |
| Persistent assignment | Whole-destination atomicity under the existing rules |

Existing contextual literal and explicit-conversion rules apply to the argument. A typed source of a different element type is not implicitly converted. A literal that cannot fit the expected element type is a compilation error. A fallible operation must be evaluated and handled before the fill call, using a local so no call appears inside its argument:

```text
var next_byte: u8 = attempt read_byte();
buffer = fill(next_byte);
```

Read once; if the call returns Err, attempt propagates it and no destination assignment takes place. A trap follows the usual trap/transaction rules. Previous side effects while evaluating the argument are not automatically undone. Attempt still cannot cross a transaction boundary opened by the current function.

Self-source filling captures the original value before writing:

```text
buffer = fill(buffer[0]);
```

The first element is read once, then its captured value is copied into every element. This does not repeatedly read the array while overwriting it. Existing bounds, access-path permission and lifetime rules remain applicable; aliasing is allowed.

The compiler may fill a destination directly rather than materialize a temporary array only if behavior is identical: evaluate once, preserve independent value semantics, preserve failure ordering and enforce persistent atomicity. Required storage and implementation strategy are not prescribed by the language.

Together with section 8.2, this completes fill behavior for the initial version. It does not add resizing, partial fill ranges, a separate length argument or a special zero initializer.

### 8.4 Array slices and unspecified-size parameters (agreed)

Slices select regions of existing arrays; unspecified-size parameters accept array regions of different lengths. Both coexist with fixed-size arrays.

| Form | Meaning |
| --- | --- |
| `T[N]` | Fixed-size array; a fixed-array parameter requires exactly N elements of type T |
| `name: ref T[]` | Read-only borrowed array parameter with runtime length |
| `name: inout T[]` | Mutable borrowed array parameter with runtime length |
| `array[start..end]` | Borrowed half-open region from start through end minus one |

T may be any supported fixed-array element type, including structures and enums. Element types must match exactly. Unspecified-size array parameters support ref and inout modes only initially; a by-value `name: T[]` parameter is forbidden. This does not introduce unsized owned variables or runtime-sized backing allocations.

#### Passing whole arrays and slices

```text
function inspect(data: ref u8[]) {
    for index: u32 in 0..data.length {
        // Read data[index].
    }
    return Ok();
}

// Inside a function/command with a suitably sized byte array buffer:
attempt inspect(ref buffer);         // Whole array, any fixed length.
attempt inspect(ref buffer[4..12]);  // Eight-element region.
```

The mode remains explicit at declaration and call site. Passing a whole array supplies its full region; passing a slice supplies the selected region. Neither copies or allocates underlying elements. The view may require region/length metadata; its physical representation is a VM detail.

Within the callee, indexing starts at zero and .length returns the supplied region's element count as u32. In the second call, data[0] accesses buffer[4] and data.length is 8. Indexing must satisfy index < data.length. A parameter cannot resize or rebind its region; inout permits mutation of selected elements, not changing the caller's array length.

#### Bounds and empty regions

The agreed syntax supplies both endpoints. Bounds must satisfy start <= end <= the receiver's length. Invalid runtime bounds trap before callee entry; required constant-evaluation failures follow the existing compile-time rules. Empty slices, including an empty region at the end of an array, are valid. Their length is zero and every element index is out of bounds. Zero-length fixed-array declarations remain forbidden.

Slice arguments follow existing left-to-right argument preparation. Regions and bounds are established before entry and are not reevaluated during the call. Calls within slice argument expressions remain subject to the no-nested-argument-call rule. Precise endpoint typing and evaluation details remain listed below for specification work.

#### Borrowing, storage and lifetime

A slice retains underlying storage identity. An inout slice of persistent storage performs persistent writes: each element/field assignment has the existing atomicity guarantee, and writes join an active transaction. Borrowing a slice does not make multiple assignments collectively atomic.

A ref slice is read-only through that view; another mutable path may change its underlying elements. An inout slice requires mutable storage but no exclusive access. Overlapping ref/inout and inout/inout slices are allowed, as are disjoint slices. Views identify the selected elements; accesses through aliases or globals follow ordinary evaluation order and their own access-path permissions. No overlap checks or overlap traps apply.

An unspecified-size parameter may be forwarded under existing reference-forwarding rules: ref to ref, and inout to ref or inout. It may also be narrowed to a slice within its supplied region. Forwarding cannot strengthen permissions or extend lifetime.

Slices cannot escape the call, be returned, or be stored in globals or structures. No raw pointers or dynamic backing allocation are introduced. These decisions cover slice arguments and reference parameters; local slice-binding syntax is not adopted here.

#### Remaining slice specification details

- Exact endpoint typing/context rules and receiver/start/end evaluation order, including failed-check ordering.
- Whether omitted endpoints or standalone slice expressions outside argument/receiver positions are supported.
- Whether a known-length slice may satisfy a fixed-size T[N] parameter; existing fixed-array exact-length matching remains unchanged.
- Whether whole-region copy/fill assignment syntax is added; fixed-array value assignment and element mutation remain the defined operations.
- Physical view representation and host command ABI validation. External callers do not supply raw card-memory references.

## 9. Structures

Structures group named, typed fields. Nested structures are allowed. Parameter passing uses the three modes in section 3.7; detailed layout and reference checking remain open.

```text
struct Account {
    balance: u32;
    identifier: u8[4];
    counters: u32[8];
}

persistent account: Account;

// Illustrative setup helper; lifecycle binding is platform-defined.
function example_setup_account() {
    account = Account {
        balance: 0,
        identifier: [0x01, 0x02, 0x03, 0x04],
        counters: fill(0)
    };
    return Ok();
}
```

Agreed: array fields use the same initialization forms as standalone arrays:

- `fill(value)` uses the array field's declared length and initializes every element.
- An explicit list must contain exactly that many elements; no implicit padding or truncation.
- Every element must be valid for the field's element type.
- No separate array-field initialization syntax is introduced.

Thus `identifier` above receives four explicit bytes, and `counters` receives eight zero values. Too few or too many explicit field-array elements is a compilation error.

Field access and updates use dot notation. For example, inside a command:

```text
var previous: u32 = account.balance;

transaction {
    account.balance = account.balance - amount;
    account.counters[0] = account.counters[0] + 1;
}
```

This fragment assumes `account` and `amount` are in scope. The instance declaration determines storage and mutability; fields do not individually declare `persistent`, `session`, `const` or `var` in the proposed initial model.

Initial structure rules:

| Question | Rule |
| --- | --- |
| Field types | Integers, booleans, enums, arrays and other structures |
| Construction | Global mutable instances always default; local omitted initializers default; explicit constructors supply every field |
| Mutable instance | Individual fields and array elements can be updated |
| Const instance | Fields and array elements cannot be changed |
| Assignment | Copies the complete value |
| Storage | Fields inherit the instance's storage lifetime |
| Methods and inheritance | Omit initially; use ordinary functions |

### 9.1 Nested structures (agreed)

A structure field may have another structure as its type. Define the types separately, then compose their values with nested initializers:

```text
struct Identity {
    identifier: u8[4];
    version: u16;
}

struct Account {
    identity: Identity;
    balance: u32;
}

persistent account: Account;

function update_version() {
    account.identity.version = 2;
    return Ok();
}

// Illustrative setup helper; lifecycle binding is platform-defined.
function example_setup_account() {
    account = Account {
        identity: Identity {
            identifier: [0x01, 0x02, 0x03, 0x04],
            version: 1
        },
        balance: 0
    };
    return Ok();
}
```

Chained dot notation selects nested fields. Nested array fields accept both explicit lists and `fill(value)`, using the field's declared length.

All nested fields inherit the outer instance's storage and mutability: a persistent instance is persistent throughout, a session instance has session lifetime throughout, and a const instance cannot have its nested fields or array elements modified. Inner fields do not select a different storage class.

Direct or indirect recursive containment is a compilation error:

```text
struct Node {
    child: Node;  // Compilation error: directly contains itself.
}
```

An indirect cycle is also forbidden: if A contains B and B contains A, neither type has a finite by-value layout. Containment through arrays must not introduce such cycles either. These rules keep structure sizes finite and calculable at compile time. Any future reference-based recursive data model would require a separate design.

The example's `Account` is a separate illustrative definition from the earlier section's `Account`; examples are not a single combined compilation unit. Type declarations are top-level only under section 4.2; the nested-structure feature means fields whose types are other structures, not lexically nested declarations.

### 9.2 Arrays of structures and representation

Arrays of structures use the same array syntax (agreed):

```text
session accounts: Account[4];

// Illustrative setup helper; lifecycle binding is platform-defined.
function example_setup_accounts() {
    var template: Account = Account {
        balance: 0,
        identifier: fill(0),
        counters: fill(0)
    };
    accounts = fill(template);
    return Ok();
}
```

Each element is an independent structure. Fill evaluates the aggregate argument once and independently copies that value into every element (section 8.2).

Structure memory/storage layout must not automatically define wire encoding. Byte order, field order, lengths, padding, persistence layout and upgrade compatibility need explicit rules.

Structures support by-value parameters, explicit read-only `ref` and mutable `inout`, as agreed in section 3.7. By-value passing gives independent values; reference modes avoid required copies. Detailed enforcement and layout remain open.

### 9.3 Structure construction and type identity (agreed)

A constructor explicitly names the structure and supplies every field:

```text
var working: Account = Account {
    balance: 100,
    identifier: [1, 2, 3, 4],
    counters: fill(0)
};
```

This assumes the Account definition with the three named fields shown. It is a local declaration fragment; mutable globals still have no declaration initializers. Omitted local initializers and new global storage receive recursive defaults under section 3.9.

| Condition | Behavior |
| --- | --- |
| Missing field | Compilation error |
| Unknown field | Compilation error |
| Field supplied twice | Compilation error |
| Field order differs from declaration | Allowed; evaluate in written order |
| Field expression has incompatible type | Compilation error under existing contextual/conversion rules |
| Constructor result | Direct structure value, not a Result |
| Fallible field expression | Handle explicitly, e.g. with attempt |
| Field-level defaults in the struct definition | Not supported initially |
| Copy/update shorthand for unspecified fields | Not supported initially |

A constructor creates an independent complete value, including nested structures and arrays. Fields must each be supplied exactly once regardless of declaration order. Literal values and fill arguments get expected types from the corresponding field definition. No anonymous/shorthand constructor is introduced.

```text
working = Account {
    counters: fill(0),
    balance: 100,
    identifier: [1, 2, 3, 4]
};
```

This is valid. Evaluate explicit field expressions left to right as written, not reordered to match the type's field declarations.

```text
working = Account {
    balance: attempt read_balance(),
    identifier: [1, 2, 3, 4],
    counters: fill(0)
};
```

This assumes read_balance returns a u32 outcome. If evaluating a field fails, no destination assignment occurs and later field expressions are not evaluated. Earlier side effects remain unless separately covered by transaction semantics. Attempt obeys its existing transaction-boundary restriction. Runtime traps follow ordinary trap handling.

Assignment to a persistent structure remains atomic for the whole destination, not separately for each constructor field. Field evaluation can have side effects, but those effects are not automatically part of the final assignment's atomicity. Constructors in constant expressions are restricted to constant-valued field expressions.

#### Nominal identity

Separately named structures are distinct types even if their fields/layouts match:

```text
struct First {
    value: u32;
}

struct Second {
    value: u32;
}
```

```text
var first: First;
var second: Second;
second = first;  // Compilation error: distinct structure types.
second = Second { value: first.value };  // Valid explicit construction.
```

There is no structural conversion based on matching field names or memory layout. The exact named type must match for assignment, parameters and return payloads. Existing by-value copy, ref and inout rules apply. Automatic structure equality remains omitted initially.

#### Nonempty and finite types

Structures must declare at least one field:

```text
struct Empty {
}  // Compilation error: empty structures unsupported initially.
```

Direct/indirect recursive containment remains forbidden, including through array fields. Nested structures and arrays of structures must have finite compile-time sizes. Binary layout, alignment/padding, durable encoding and host serialization are separate from construction syntax; constructing a value does not define its wire representation.

## 10. Combined wallet helper sketch

```text
persistent balance: u32;
session authenticated: bool;

function get_balance() -> u32 {
    return Ok(balance);
}

function debit(amount: u32) -> u32 {
    require authenticated else WalletError.Unauthorized;
    require amount <= balance else WalletError.InsufficientFunds;

    transaction {
        balance = balance - amount;
    }

    return Ok(balance);
}
```

This sketch defines ordinary wallet helpers using successful-payload signatures and explicit Ok returns. A single byte-oriented host command must parse a request, invoke the appropriate helper and encode its result into the response buffer. The sketch omits that protocol handler, authentication setup and error declarations. Validation occurs before the transaction for simplicity. Because commands do not interleave, another command cannot change the balance between this validation and update. Application logic remains responsible for consistency after failures; a command is not implicitly atomic.

## 11. Runtime-owned resources and security boundary

Agreed interface direction: resource objects are owned by the runtime and named by application-chosen u32 identifiers. This replaces earlier typed-handle, opaque-inline-object and single-Resource-type proposals. No new resource type or allocation syntax is added to CardLang.

### 11.1 No opaque platform value types (agreed)

Opaque platform types are not supported initially. There are no hidden-layout `KeyHandle`, `HashContext` or other runtime-object values that applications can declare, copy or pass. Platform API values use the existing integers, Booleans, fixed arrays, structures and enums, with the common success/error mechanism and existing `ref`/`inout` parameter modes where appropriate.

Platform-supplied configuration structures and algorithm enums have complete, visible declarations and follow ordinary construction, copying, matching and naming rules. Supplying these declarations does not add imports, namespaces, private fields or application-defined external declarations. Reserved platform interface names retain their existing protection.

Resource identifiers remain ordinary `u32` values, with normal integer comparison and copying. Passing an identifier does not transfer ownership. The compiler does not distinguish a key identifier from an operation identifier: the runtime validates existence, kind, state and permissions on every operation, returning a defined recoverable error for the wrong resource kind. Identifiers do not grant access to another application's objects. This deliberately leaves resource-kind checking at runtime rather than adding language-level handle types.

Internal object representations remain entirely runtime-owned. Applications do not allocate byte arrays to hold hidden runtime object layouts. Arrays passed to APIs contain defined application data, such as messages, signatures or encoded public keys; an explicitly specified serialized format is data, not an application-visible runtime object representation. Typed resource handles may be considered as a future extension but are not part of the initial language.

### 11.2 Resource naming and lifecycle boundary

```text
const SIGNING_KEY: u32 = 1;
const HASH_OPERATION: u32 = 2;
```

Rules:

- Zero is reserved as invalid. Each isolated application has one resource-name space covering all resource kinds; applications may reuse the same numbers independently.
- Identifiers are ordinary values passed/copied by value. They are names, not pointers, ref/inout borrows or authorization tokens.
- Copying an identifier does not copy or clone the object. Lookup is always scoped to the calling application, with runtime kind/state/permission checks.
- Create an unused identifier to establish a resource. Existing identifiers produce a recoverable AlreadyExists error, never silent replacement.
- Unknown identifiers produce NotFound; incompatible kinds produce WrongResourceType; insufficient capacity produces a defined capacity error. Exact platform error codes/names remain TBD.
- Delete removes a resource under the platform's cleanup rules. Deleting an unknown resource returns NotFound.
- Failed creation must not expose a usable partially created object.
- After deletion, saved copies name a nonexistent object. Reusing the identifier makes them name the replacement. There is no stale-handle detection in this name-based model.
- Variable lifetime and resource lifetime are separate. A constant ID can name a durable key; storing an ID persistently does not make its object durable. Leaving a function does not implicitly delete resources named by locals.

Illustrative API fragments only; configuration types, final signatures and lifecycle details are platform-defined:

```text
attempt card.resources.create(HASH_OPERATION, configuration);
attempt card.crypto.hash_update(HASH_OPERATION, ref message);
attempt card.resources.delete(HASH_OPERATION);
```

These calls use existing function outcome handling. Earlier successful calls are not automatically undone on Err. An ordinary trap does not automatically clean up, delete or invalidate runtime-owned resources. Each operation must define its own failure-state behavior. Resource power-on/security-reset behavior and whether operations participate in or are forbidden during language transactions remain platform API contracts. Language persistent-variable atomicity alone does not define resource creation/deletion recovery.

Resource storage may use fixed slots, bounded pools or a heap; no allocator strategy is required by the language. Key algorithms/curves/roles, resource sizes, durable versus volatile storage, capacities and enumeration belong to `cardlang-platform-notes.md` and the future platform API specification.

Existing security boundaries remain: isolated applications, permission-checked services, validated buffer ownership, no escaping application references, and defined sensitive-data cleanup. The language does not by itself guarantee constant-time cryptographic application behavior or prevent every information leak.

## 12. Language versus VM/platform responsibilities

The companion `cardlang-platform-notes.md` records concrete VM ideas and prior unmeasured memory targets. RAM/stack/execution budgets, transaction capacities, installed-application counts, allocation mechanisms and physical layout are target/runtime decisions, not language syntax.

The language retains these semantic guarantees:

- Runtime stack/execution-limit exhaustion traps; programs exceeding supported build/load capacity may be rejected.
- Limits and optimizations cannot silently change independent-copy, reference, arithmetic or persistent atomicity semantics.
- Exactly one command receives request/response byte-array views and returns a u32 response count. Application code owns operation dispatch and payload parsing/encoding; the platform owns transport framing, buffer provisioning, permissions and status reporting (SW for classical smart cards).
- Commands never interleave; each finishes or fails before another starts.
- Session variables receive type defaults on chip power-on and are wiped by security reset; subsequent initialization restores defaults. Other lifecycle events, provisioning, installation/upgrades and migration belong to the platform.
- Ordinary traps terminate the current command, preserve session state and roll back active persistent transactions. They cause no automatic resource cleanup or invalidation; subsequent commands may execute.
- The runtime may issue whole-chip security resets, and fatal platform failure requires one. These clear session/volatile state.
- Application programmers maintain session/persistent logical consistency; the runtime does not automatically synchronize or repair it.
- `abort Err(error);` rolls back its enclosing transaction's persistent changes and returns the error from the enclosing function/command; session state and earlier commits remain.

No cross-application calls, shared state or references are introduced by runtime resources. Compiler memory reports are tooling features. Resource allocation and cleanup remain explicit platform contracts; the application language still has no general-purpose heap or garbage collector.

## 13. Specification and implementation workflow

Maintain separate language semantics and VM/card-platform specifications. The implementation must not silently define unspecified behavior.

Develop three representative applications alongside the design:

1. Counter: arithmetic, commands and durable updates.
2. Wallet: authorization, transactions and recovery.
3. Signing application: keys, permissions and security services.

For each feature, specify successful behavior, failure behavior and resource limits; then write independent conformance tests. Prioritize malformed inputs, bounds failures, arithmetic faults and interrupted persistent updates as well as normal operation.

Next specification work: settle any additional lifecycle events beyond the agreed power-on, trap and security-reset behavior, entry-point naming, transport framing/buffer capacities and exact status mappings, error/trap catalogs, remaining transaction/storage limits and detailed reference enforcement before fixing bytecode encodings. The primary result/error propagation and post-trap state rules are now defined.


## 14. Revision notes

- Adopted the name CardLang.
- Replaced earlier local declarations with `var` only; local `const` is deferred.
- Superseded the two-part global declaration scheme: use exactly `persistent`, `session` or `const`.
- Global `persistent` and `session` state is mutable; global `const` is compile-time and immutable. Global plain `var` and combined qualifiers are forbidden.
- Local declarations use `var` inside functions and commands; no `local` qualifier, storage qualifiers or local `const`.
- Adopted `T[N]` arrays and `fill(value)` initialization; explicit lists must match the declared length exactly. No special `zero` initializer.
- Added structures, field access and array-field initialization using both `fill` and explicit lists.
- Distinguished agreed syntax from proposed structure semantics and open layout/reference decisions.

- Confirmed nested structures, nested initialization, chained field access and inherited storage/mutability; recursive containment is a compilation error.

- Adopted universal function success/error outcomes and retained `match` with `Ok` / `Err` for explicit handling. Explicit outcome-return syntax is agreed; common categorized error values are now defined in section 6.3.
- Dropped `call ... into ... otherwise`; subsequently adopted `attempt` alongside `match`.
- Defined atomic persistent assignments and distinguished them from multi-assignment transactions; storage limits remain open; ordinary transaction-boundary exits are forbidden, with explicit abort added below.

- Fixed the primitive set to signed/unsigned 8-, 16- and 32-bit integers plus bool; confirmed byte arrays; subsequent decisions extend fixed arrays to all supported fixed-size value types.

- Adopted explicit value-preserving integer conversions, matching-type arithmetic/comparisons, contextual literal typing, boolean separation and no general truncating casts. Conversion intrinsics have explicit direct-value versus result behavior.

- Adopted expression operators and evaluation rules, replacing binary precedence with mandatory parentheses for mixed operators. Recorded comparison-chain rejection, arithmetic/shift behavior, statement-only assignment and explicit function-outcome handling.

- Formalized control flow, mandatory braces, block scope/no shadowing, range loops, read-only loop/pattern bindings and exhaustive match. Adopted explicit Ok/Err returns and require expansion; forbade ordinary control transfers crossing transaction boundaries. Explicit abort was added subsequently.

- Retained the original three parameter modes: value, read-only ref and mutable inout. Added call-site syntax, read-only bindings, call-scoped references, initially adopted overlap/exclusivity constraints (subsequently removed) and persistence/error behavior; adopted Ok() for no-value success matching.

- Confirmed independent aggregate copies and by-value returns; references may target fields/elements but not temporaries. Initially defined overlap conflicts as traps (subsequently removed); retained distinct-field access and no implicit rollback of mutations; initially deferred general slices, subsequently adopted in section 8.4.

- Added implicit variable defaults: integer zero, false booleans, and recursive array/structure initialization. Defined per-lifetime timing, explicit global const initialization and complete explicit aggregates; resource identifier zero is invalid; enum defaults are now the first declared variant.

- Disallowed nested transactions, including indirect nesting through calls: static rejection where provable, otherwise a pre-start trap aborting the outer transaction. Callee persistent writes join an active transaction. Recorded temporary RAM/call-frame placement for by-value aggregate copies.

- Consolidated result consumption with match/attempt/forwarding returns; explicit stable application u16 errors, separate platform errors and trap reporting, and full application isolation. Ordinary traps preserve session state; transactions restore persistent changes only. Fatal platform failures security-reset the whole chip at the platform layer.

- Adopted one shared application scope across an explicit source-file list, no module/visibility machinery, file-order-independent name resolution, duplicate-declaration errors and reserved platform APIs. Only command declarations are host-callable.

- Added read-only array .length of type u32, counting elements without a per-array runtime length field. Allowed u8/u16/u32 indices with bounds checks; signed indices are compilation errors.

- Adopted source grammar: .card files with top-level declarations and no application wrapper, UTF-8 source/ASCII names, comment and literal rules, mandatory punctuation/types, optional trailing commas, no-value signature spelling and no preprocessor. Updated earlier examples to the wrapper-free form.

- Formalized a single top-level type/value naming scope, no overloading, owner-specific field/error lookup, reserved names, no shadowing and local visibility after initialization. Reconciled parameter examples; initialization dependencies remain separate.

- Completed contextual typing policy: explicit declaration types, symmetric literal typing from typed operands, no implicit widening, u32 context for literal-only indices and known-source conversion intrinsics. Retained explicit named structure constructors.

- Defined constant-expression subset, forward dependencies/cycle rejection, compile-time failure and short-circuit semantics, unsigned constant array lengths and type-derived .length. Initially excluded all conversion intrinsics from constant evaluation; this was subsequently revised to allow guaranteed convert for constant operands. checked_convert remains excluded; runtime conversion rules are unchanged.

- Removed declaration initializers from persistent/session globals; automatic recursive defaults remain mandatory. Nondefault setup moves to platform lifecycle handlers. Constants still require compile-time initializers; locals retain runtime initializers. Aggregate fill/list/struct construction also works in assignment expressions.

- Adopted app-scoped u32 names for runtime-owned resources, reserving zero; removed superseded typed-handle proposals. Added cardlang-platform-notes.md and moved concrete VM budgets/implementation ideas there while preserving language-visible guarantees.

- Completed fixed-array rules: supported value element types, positive lengths, no direct multidimensional arrays initially, exact-type/length whole copies, once-and-copy fill and bounds-checked destination evaluation before assignment RHS.

- Classified fill as a reserved compiler intrinsic producing a direct, context-sized array value. Recorded constant restrictions, explicit handling of fallible arguments, original-value capture for self-source fill and semantics-preserving optimization requirements.

- Completed structure construction validation and direct-value semantics. Adopted nominal structure identity and nonempty structures, preserved written-order evaluation and whole persistent assignment atomicity, and omitted field defaults/update shorthand initially.

- Added simple nonempty nominal enums with qualified variants, first-variant defaults, equality, arrays/fields and exhaustive explicit matching. No payloads, numeric conversion, ordering or catch-all enum arms initially; error sets remain separate and limited to one per app.

- Completed integer arithmetic edge cases: minimum signed remainder -1 is zero, division still fails, unary negation is signed-only, checked and wrapping intrinsic families are explicit, and both are excluded from constants initially. Required checks preserve semantics across optimization modes.

- Consolidated function declarations: explicit positional parameters and modes, optional trailing commas, supported single-value aggregate returns, explicit outcome completion with no reachable fall-through, and host-only commands with ordinary helpers for shared logic.

- Settled initial function features: reject direct/indirect recursion, omit function values/pointers and user-defined generics, and use definitions without separate prototypes or application-defined external declarations. Ordinary call targets are statically known; the compiler rejects cycles across the complete application's call graph. Platform callback/event rules remain separate.

- Defined outcomes as transient, immediately consumed results with no user-visible Result<T>, stored/nested outcomes or general Ok/Err constructors. attempt produces the exact successful payload type, propagates unchanged errors across differing enclosing success types, and has statement form only for no-payload calls; Ok(_) explicitly ignores a payload.

- Completed initial pattern matching: outcomes and enums only; explicit limited patterns, independent read-only payload bindings, exactly one success arm and mandatory final error catch-all, exhaustive enum variants, and compilation errors for duplicate/unreachable/type-incompatible arms. Guards, alternatives, range patterns and nested/aggregate destructuring are omitted initially.

- Initially specified shared-read/exclusive-write borrowing and forwarding with suspension. The subsequent aliasing decision supersedes exclusivity, overlap traps and suspension. Existing-storage targets, constants through ref, nonescaping references and ordinary error returns without rollback remain.

- Completed transaction semantics: closing-brace commit, read-your-writes through helpers/references, empty transactions, persistent-only participation, locally handled Err retaining pending changes, and no normal continuation after commit failure. Added companion requirements for atomic recovery and prevention of partial-state observation across execution contexts.

- Omitted opaque platform value types initially. APIs use existing values and fully visible configuration structures/enums; runtime objects remain hidden behind ordinary u32 names with runtime kind/state/permission checks. No hidden object layouts in application byte arrays; explicit serialized API data remains supported.

- Resolved specification-readiness questions: no nested calls in arguments (including intrinsics), reference argument preparation before callee entry, propagation-only error bindings, compile-time checks for constant-only calculations, observable length-receiver evaluation, conservative structural completion rules, and the existing closing-brace commit contract. Rewrote fill examples to use explicit locals.

- 2026-11-15: Adopted `abort Err(error);` for explicit recoverable transaction exit. Abort is valid only lexically inside a transaction, rolls back that transaction's persistent changes and returns the specified error from its enclosing function/command. Session mutations and earlier commits remain. Helpers return Err for the transaction owner to handle; ordinary return, attempt, require and loop-exit boundary restrictions remain. Extended restricted error bindings and completion analysis to cover abort, and superseded the earlier absence of recoverable abort syntax.

- 2026-11-15: Restored half-open array slices and adopted unspecified-size ref T[] / inout T[] parameters alongside fixed-size T[N] parameters. Views borrow existing storage, expose runtime u32 lengths, allow empty regions and obey call-scoped reference and persistent-write rules. By-value arrays retain fixed sizes. Replaced earlier slice deferrals; remaining syntax and typing details are explicit specification work.

- 2026-11-15: Dropped exclusive borrowing to simplify the tiny VM. Overlapping references and slices, including ref/inout and inout/inout, are allowed. ref restricts writes through that path only; inout grants read/write access without exclusivity. Removed overlap checks/traps and forwarding suspension. Evaluation order, observable aliasing effects, independent value copies, bounds checks, access-path permissions, application isolation, persistent atomicity and call-scoped lifetimes remain. The nested-argument-call ban is unchanged.

- 2026-11-15: Defined non-interleaving command execution. Session variables receive recursive type defaults on chip power-on; ordinary traps preserve session state, terminate only the current command and cause no automatic resource cleanup/deletion/invalidation. Subsequent commands can execute. The runtime may issue security resets, which wipe session state; subsequent initialization restores defaults. Resource operation failure states and power-on/reset lifecycles remain platform contracts. Application programmers are responsible for logical consistency between session and persistent state; no automatic repair or synchronization is introduced.

- 2026-11-15: Allowed guaranteed convert<T> in constant expressions with constant operands, independently known source types and full source-range representability. checked_convert and checked/wrapping arithmetic remain excluded; nested-call restrictions remain. Added a clearly labeled structural evaluation proposal and acceptance examples for runtime guards and unreachable code, leaving unresolved bounds classification explicit.

- 2026-11-15: Replaced multiple typed host commands with one byte-oriented entry point taking ref u8[] request and inout u8[] response and returning a successful u32 byte count. Application code owns parsing, dispatch and payload encoding (for example ASN.1, CBOR or a custom format). Platform-owned separate buffers are invocation-scoped; data is sent only after successful completion with a valid count. Err/traps suppress partial data. Classical smart-card outcomes are reported through response SW, with exact mappings left to the platform. Converted earlier typed/no-value command examples to ordinary helpers.
