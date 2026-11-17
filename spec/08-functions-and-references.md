# 8. Functions, references and slices

CardLang Language Specification, Draft 0.1. Chapter status: **draft complete** (SP7).

This chapter covers:

- function declarations and the static call graph;
- parameter modes and how arguments are passed;
- references (`ref` and `inout`) and their permissions, aliasing, forwarding and lifetimes;
- value semantics for copies;
- slices and unsized array views.

Related topics are covered in other chapters:

| Topic | Chapter |
|---|---|
| Typing of `return Ok`/`Err` and whole-outcome forwarding | 9 |
| The `command` signature | 12 |
| Transaction participation of writes through references | 10 and 11 |

How references are physically represented, where by-value aggregates are placed, and how stack space is accounted for are VM matters described in Annex B. They are not language semantics.

## 8.1 Function declarations

```
FunctionDeclaration ::= 'function' Identifier ParameterList ReturnType? Block
ParameterList       ::= '(' ( Parameter ( ',' Parameter )* ','? )? ')'
Parameter           ::= Identifier ':' ( 'ref' | 'inout' )? Type
ReturnType          ::= '->' Type
```

**FUN-1 [Agreed]** A function declaration gives the function's name, its parameters in order, an optional successful payload type and its body. Each parameter has an explicit name, an optional mode and a type:

| Form | Mode |
|---|---|
| `name: T` | By value |
| `name: ref T` | Read-only reference |
| `name: inout T` | Mutable reference |

A trailing comma is allowed after the last parameter. Arguments are positional only. There are no named arguments, default values, optional parameters or variadic parameters.
*Sources: D-026, D-112; DN §3.0, §3.7.*

**FUN-2 [Agreed]** `-> T` names the successful payload type. `T` must be a value type: an integer, `bool`, an enum, a fixed array or a structure, including nested aggregates. An unsized `T[]` return type is rejected by TYP-21. Omitting the arrow means success carries no payload. A function returns at most one value. There are no tuples, and references are never returned. To return several values, group them in a structure.
*Sources: D-025, D-033; DN §3.0, §3.7.*

**FUN-3 [Agreed]** CardLang has none of the following:

- function prototypes, forward declarations or application-defined external declarations (a function's single definition is visible everywhere, NAM-13);
- nested functions (NAM-7);
- overloading (NAM-12);
- modifiers such as `pure`, `static` or `public`;
- purity or effect annotations.

Platform API declarations are supplied by the platform, not written by applications.
*Sources: D-032, D-352; DN §3.7.*

### Examples

*Valid:* a structure used to return two values (DN §3.7). (conformance: `valid/fun-002-structure-return.card`)

```text
struct Measurement {
    value: u32;
    valid: bool;
}

function measure() -> Measurement {
    return Ok(Measurement { value: 10, valid: true });
}
```

*Valid:* a function with no successful payload (DN §3.7). (conformance: `valid/fun-010-no-payload-function.card`)

```text
function clear(target: inout u32) {
    target = 0;
    return Ok();
}
```

## 8.2 The static call graph

**FUN-4 [Agreed]** Every call names its target directly (EXP-47). Functions are not values. There are no function pointers, no variables or parameters holding functions, no functions returned as values, and no callbacks. Choosing between functions at runtime is written with ordinary control flow.
*Sources: D-031; DN §3.7.*

**FUN-5 [Agreed]** The *call graph* of an application has one node per function. It has an edge from `F` to `G` whenever the body of `F` contains a call to `G`, whether or not that call can actually run. The command is also a node in this graph (chapter 12). A cycle in the call graph is **CE-FUN-1**. This covers:

- direct recursion;
- indirect recursion through any number of functions;
- recursion across source files.

Intrinsics and platform APIs are not nodes, and they never call application code. The call graph is therefore acyclic and finite, so the maximum call depth can be calculated during compilation.
*Sources: D-031; DN §3.7.*

### Examples

*Valid (two files):* a call to a function in another file, declared later. (conformance: `valid/fun-001-forward-call-across-files/`)

*Invalid:* indirect recursion (DN §3.7). **CE-FUN-1**. (conformance: `invalid/fun-102-indirect-recursion.card`)

```text
function first() {
    return second();
}

function second() {
    return first();
}
```

*Invalid:* direct recursion (conformance: `invalid/fun-101-direct-recursion.card`), and recursion across two files (conformance: `invalid/fun-103-recursion-across-files/`). Both are **CE-FUN-1**.

## 8.3 Parameter modes and call-site modes

**FUN-6 [Agreed]** The three parameter modes mean:

| Mode | Inside the callee | Copy? | Can change caller data? |
|---|---|---|---|
| By value (`name: T`) | An independent value, bound read-only. Copy it into a `var` to change it | Yes, semantically | No |
| `ref` (`name: ref T`) | A read-only access path to the caller's existing storage | No | No, not through this path |
| `inout` (`name: inout T`) | A read-write access path to the caller's existing storage | No | Yes |

A read-only parameter binding is not a local `const`. Its immutability comes from its mode.
*Sources: D-112, D-114, D-115, D-116; DN §3.7.*

**FUN-7 [Agreed]** At the call site, each argument carries exactly the mode of its parameter:

| Parameter mode | Argument form |
|---|---|
| `ref` | `ref e` |
| `inout` | `inout e` |
| By value | `e`, with no mode word |

A missing, extra or different mode is **CE-FUN-2**. The same rule applies to platform APIs and intrinsics: `decode_be` and `decode_le` take a `ref` argument, and every other intrinsic takes by-value arguments.
*Sources: D-113; DN §3.7.*

**FUN-8 [Agreed]** An argument's type must be identical to its parameter's type (TYP-4), with literals typed by context (EXP-10). Otherwise it is **CE-EXP-1**. The single exception is a `ref T[]` or `inout T[]` parameter, which accepts:

- a fixed array `T[N]` of any length;
- a slice;
- another `T[]` view.

In every case the element type must be exactly `T`. A slice or view never satisfies a `T[N]` parameter, even when its length is known. By-value array parameters always have a fixed size `T[N]`, and the argument's length must equal `N`.
*Sources: D-120, D-121, D-410 (OI-10); DN §3.7, §8.4.*

### Examples

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `inspect(buffer)` with parameter `data: ref u8[]` | CE-FUN-2 | `invalid/fun-104-missing-ref-mode.card` |
| `clear(counter)` with parameter `target: inout u32` | CE-FUN-2 | `invalid/fun-105-missing-inout-mode.card` |
| `show(ref value)` with by-value parameter `value: u32` | CE-FUN-2 | `invalid/fun-106-ref-for-by-value.card` |
| `inspect(inout account)` with parameter `source: ref Account` | CE-FUN-2 | `invalid/fun-107-inout-for-ref.card` |
| `fixed(ref buffer[0..4])` with parameter `data: ref u8[4]` | CE-EXP-1 | `invalid/fun-117-slice-to-fixed-parameter.card` |
| `inspect(ref counters)` with `counters: u32[4]` and parameter `ref u8[]` | CE-EXP-1 | `invalid/fun-118-element-type-mismatch.card` |

## 8.4 Reference arguments

**FUN-9 [Agreed]** A `ref` or `inout` argument must *identify existing storage*. It must be one of:

- the name of a local variable, global, constant or parameter of any mode;
- a `for` index or pattern binding (`ref` only, FUN-10);
- a path of field selections and index operations rooted in one of the above;
- a slice of one of the above (§8.10).

Anything else is **CE-FUN-3**. That includes literals, calls, structure constructors, array lists, `fill`, operator expressions, `attempt` and `.length`. A reference to a field covers that field only, not the whole structure that contains it.
*Sources: D-117, D-435 (OI-35); DN §3.8.*

**FUN-10 [Agreed]** An `inout` argument must also be an assignable place under STM-7. Each of the following passed as `inout` is **CE-FUN-4**:

- a constant, or any part of one;
- a by-value parameter;
- a `for` index or pattern binding;
- any path rooted in a `ref` parameter (FUN-15).

A constant may be passed as `ref`. Any temporary copy an implementation makes for it remains immutable, and it does not turn references into values.
*Sources: D-115, D-330, D-435 (OI-35); DN §3.7, §3.8.*

### Examples

*Valid:* references to a constant, a by-value parameter and a `for` index. (conformance: `valid/fun-009-constant-and-bindings-by-ref.card`)

```text
const IDENTIFIER: u8[4] = [1, 2, 3, 4];

function sum(data: ref u8[]) -> u32 {
    return Ok(data.length);
}

function count(value: ref u32) -> u32 {
    return Ok(value);
}

function readers(limit: u32) -> u32 {
    var total: u32 = attempt sum(ref IDENTIFIER);
    var copied: u32 = attempt count(ref limit);
    for index: u32 in 0..4 {
        total = total + attempt count(ref index);
    }
    return Ok(total + copied);
}
```

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `get_balance(ref Account { balance: 0 })`, a temporary (DN §3.8) | CE-FUN-3 | `invalid/fun-108-temporary-reference.card` |
| `count(ref 5)` | CE-FUN-3 | `invalid/fun-109-reference-to-literal.card` |
| `count(ref (limit + 1))` | CE-FUN-3 | `invalid/fun-110-reference-to-arithmetic.card` |
| `clear(inout LIMIT)` with `LIMIT` a constant | CE-FUN-4 | `invalid/fun-111-constant-as-inout.card` |
| `clear(inout value)` with `value` a by-value parameter | CE-FUN-4 | `invalid/fun-113-by-value-as-inout.card` |

## 8.5 Argument preparation

**FUN-11 [Agreed]** Before the callee starts, the arguments of a call are prepared one at a time, left to right:

1. **By-value argument:** evaluate it, and establish its value as an independent copy.
2. **Reference argument:** evaluate its path, and check every index on the path against its array's bounds. Out of range is `trap(BOUNDS)`.
3. **Slice argument:** evaluate its receiver and endpoints, and check the region (FUN-20).

Every check completes before the callee runs. Paths and regions are fixed at this point and are not evaluated again during the call. Preparing arguments acquires no exclusive access to anything.
*Sources: D-104, D-353; DN §3.7, §3.8, §8.4.*

## 8.6 Access-path permissions and aliasing

**FUN-12 [Agreed]** Permissions belong to *access paths*, not to storage:

- **`ref`:** a `ref` parameter, and every field, element or slice derived from it, can be read but not written. Writing through it is rejected by STM-7.
- **`inout`:** an `inout` parameter, and everything derived from it, can be read and written.
- **No exclusivity:** neither mode grants exclusive access. Another access path to the same storage keeps its own permissions and may be used during the call. That includes a global, another reference parameter, or a path in a function called from the callee.
- **No snapshot:** a `ref` parameter is not a snapshot. A read through it observes every write made earlier through any path, in evaluation order.

*Sources: D-115, D-118; DN §3.7, §3.8.*

**FUN-13 [Agreed]** References and slices may overlap in any combination, and overlap is neither a compilation error nor a trap. That includes `ref` with `ref`, `inout` with `ref`, `inout` with `inout`, and an aggregate with its own fields or elements. There are no overlap checks.
*Sources: D-118; DN §3.7, §3.8, §8.4.*

**FUN-14 [Agreed]** An implementation must preserve every observable effect of aliasing, including effects through globals and nested calls. It must not assume that storage behind a `ref` parameter is unchanged during the call, or that storage behind an `inout` parameter has no other access path. It must not substitute independent copies to hide aliasing. Optional warnings about suspicious overlap do not affect whether a program is accepted or how it runs.
*Sources: D-357; DN §3.7, §3.8.*

### Examples

*Valid:* the same byte written through a reference and through a global. After `demonstrate_aliasing` succeeds, `buffer[0]` is `2` (DN §3.8). (conformance: `valid/fun-004-aliasing.card`)

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

*Valid:* overlapping `inout`/`ref` and `inout`/`inout` arguments (DN §3.8). The indices may be equal. (conformance: `valid/fun-005-overlapping-references.card`)

```text
struct Account {
    balance: u32;
}

session account: Account;
session counters: u32[4];

function modify(target: inout Account, source: ref Account) {
    target.balance = source.balance + 1;
    return Ok();
}

function copy_into(first: inout u32, second: inout u32) {
    first = second;
    return Ok();
}

function overlap(first_index: u8, second_index: u8) {
    attempt modify(inout account, ref account);
    attempt copy_into(inout counters[first_index], inout counters[second_index]);
    return Ok();
}
```

## 8.7 Forwarding references

**FUN-15 [Agreed]** A callee may pass its own reference parameters, or paths and slices derived from them, as arguments to further calls:

- Something derived from a `ref` parameter may be passed only as `ref`. Passing it as `inout` is **CE-FUN-4**.
- Something derived from an `inout` parameter may be passed as `ref` or as `inout`.

Forwarding never strengthens the permissions of the original path and never extends its lifetime. It suspends no other access path.
*Sources: D-115, D-354; DN §3.8, §8.4.*

### Examples

*Valid:* an `inout` parameter forwarded as `ref` and as `inout` (DN §3.8). (conformance: `valid/fun-006-forwarding.card`)

```text
struct Account {
    balance: u32;
}

function inspect(source: ref Account) {
    return Ok();
}

function update(target: inout Account) {
    target.balance = 0;
    return Ok();
}

function process(target: inout Account) {
    attempt inspect(ref target);
    attempt update(inout target);
    return Ok();
}
```

*Invalid:* a `ref` parameter forwarded as `inout`. **CE-FUN-4**. (conformance: `invalid/fun-112-ref-forwarded-as-inout.card`)

## 8.8 Lifetimes of references

**FUN-16 [Agreed]** A reference or view exists only for the duration of the call it was passed to. It ends when the callee returns `Ok` or `Err`, or when a trap ends the callee's frame. References and views:

- cannot be returned (FUN-2, TYP-21);
- cannot be stored in a variable, global, field or array element;
- cannot be compared or converted to integers.

A by-value use, such as `return Ok(source.balance)` or `var copy: Account = source;`, produces an independent copy, not a reference. CardLang has no reference variables, arrays of references, null references, raw pointers or pointer arithmetic.
*Sources: D-114, D-355; DN §3.7, §3.8.*

*Invalid:* there are no reference variables, because `ref` is not part of a type (FUN-16). **CE-SYN-1**. (conformance: `invalid/fun-122-reference-variable.card`)

```text
function check(value: ref u8) {
    var alias: ref u8 = value;
    return Ok();
}
```

## 8.9 Value semantics

**FUN-17 [Agreed]** By-value arguments and successful return payloads are complete, independent copies, including every nested field and element. Changing a copy never changes its source, and changing the source never changes a copy. An implementation may avoid a physical copy only when no program can observe the difference. It must never substitute sharing for copying, even to save memory. A program whose copies exceed the capacity of the target profile is rejected (TYP-23). Passing a large aggregate with `ref` or `inout` avoids the copy.
*Sources: D-116, D-358, D-133; DN §3.7, §3.8, §9.2.*

### Examples

*Valid:* `ref` and `inout` of a structure and of a field (DN §3.8). (conformance: `valid/fun-003-ref-and-inout-field.card`)

```text
struct Account {
    balance: u32;
}

persistent account: Account;

function get_balance(source: ref Account) -> u32 {
    return Ok(source.balance);
}

function increment(target: inout u32) {
    target = target + 1;
    return Ok();
}

function use_references() -> u32 {
    attempt increment(inout account.balance);
    var balance: u32 = attempt get_balance(ref account);
    return Ok(balance);
}
```

## 8.10 Slices and unsized views

```
PostfixPart ::= … | '[' Expression '..' Expression ']'      /* §A.2.4 */
```

**FUN-18 [Agreed]** A slice `a[s..e]`, where `a` has type `T[N]` or `T[]`, has the view type `T[]`. A slice may appear only:

- as a `ref` or `inout` argument whose parameter type is `T[]`, including the argument of `decode_be` and `decode_le` and the arguments of `equal` and `compare`;
- as the receiver of an index operation, of `.length`, or of another slice;
- as either side of a slice assignment (FUN-24), or as the operand of `wipe` (STM-23).

A slice in any other position is **CE-FUN-5**: for example in an initializer, either side of an assignment, an operand, a by-value argument or a return payload. A slice assignment is defined by FUN-24. There are no local slice variables.
*Sources: D-119, D-410 (OI-10); DN §8.4.*

**FUN-19 [Agreed]** Both endpoints are required. Each endpoint is typed separately: it must synthesize `u8`, `u16` or `u32`, and an endpoint containing no typed operand is typed `u32` (as for indices, EXP-39). A signed or non-integer endpoint is **CE-EXP-9**.
*Sources: D-410 (OI-10); DN §8.4.*

**FUN-20 [Agreed]** A slice is evaluated as follows:

1. Evaluate the receiver `a`.
2. Evaluate `s`.
3. Evaluate `e`.
4. If `s > e` or `e > a.length`, the result is `trap(BOUNDS)`.

When `a` has a fixed array type and both endpoints are constant-only, the check is done during compilation instead (CEX-10). A slice with `s = e` is a valid empty view, including at the end of an array: its length is 0, and every index into it is out of bounds.
*Sources: D-119, D-410 (OI-10), D-429 (OI-29); DN §8.4.*

**FUN-21 [Agreed]** A view refers to the elements `a[s]` to `a[e − 1]` of the existing storage, without copying or allocating. Through the view:

- index 0 refers to `a[s]`;
- `.length` is `e − s`, of type `u32`;
- an index must be less than `.length` (EXP-39).

A view has the permissions of the path it was taken from: read-only through `ref`, read-write through `inout` (FUN-12). A callee cannot resize or rebind its view, and cannot change the length of the caller's array. It may pass on a narrower slice of its view under FUN-15. The same applies to a whole fixed array passed to a `T[]` parameter: index 0 is its first element, and `.length` is its length `N`.
*Sources: D-120, D-359; DN §8.4.*

**FUN-24 [Agreed]** A *slice assignment* `p[s..e] = x;` copies elements into an existing region:

- **Left side.** A slice of an assignable place (STM-7), of type `T[N]` or an `inout` view `T[]`. A slice rooted in a `ref` parameter or a constant is **CE-STM-2**.
- **Right side.** Any expression of type `T[M]` or of a view `T[]`: an array place, an array list, `fill`, a call's payload, or a slice. Its element type must be `T`, otherwise **CE-EXP-1**. An array list or `fill` takes its expected type `T[e − s]` from the left side, so both endpoints must then be constant-only, otherwise **CE-EXP-10**.
- **Lengths.** When both lengths are known at compile time, from constant-only endpoints or a fixed array type, and they differ, that is **CE-STM-8**.
- **Evaluation.**
  1. Evaluate the left side's path and endpoints, and check its region (FUN-20).
  2. Evaluate the right side. A slice's region is checked as in FUN-20.
  3. If the two lengths differ, the result is `trap(BOUNDS)`, and nothing is stored.
  4. Copy the elements as if through a temporary: when the regions overlap, every element receives the source's original value.
- **Persistence.** A slice assignment into persistent storage is one persistent assignment. It is atomic for the whole region (STA-11), the region is its destination for STA-13, and it participates in an active transaction. When the region's size is known only at runtime, STA-13 applies at runtime instead (D-451).
*Sources: D-447 (OI-47), D-451 (OI-51); DN §8.4.*

*Valid:* slice assignments from a list, `fill`, another slice and a view. (conformance: `valid/fun-011-slice-assignment.card`)

*Valid:* `equal` and `compare` on views and slices, and `wipe` of a slice. (conformance: `valid/fun-012-views-equal-and-wipe.card`)

*Invalid:* slice lengths known to differ. **CE-STM-8**. (conformance: `invalid/fun-123-slice-assignment-length.card`)

*Invalid:* a slice assignment into a `ref` parameter. **CE-STM-2**. (conformance: `invalid/fun-124-slice-assignment-into-ref.card`)

*Invalid:* a slice assignment between different element types. **CE-EXP-1**. (conformance: `invalid/fun-125-slice-assignment-element-type.card`)

### Examples

*Valid:* a whole array, a slice and an empty slice passed to `ref u8[]` (DN §8.4). In the second call, `data[0]` is `buffer[4]` and `data.length` is 8. (conformance: `valid/fun-007-slices-and-views.card`)

```text
session buffer: u8[16];

function inspect(data: ref u8[]) -> u32 {
    var total: u32 = 0;
    for index: u32 in 0..data.length {
        total = total + convert<u32>(data[index]);
    }
    return Ok(total);
}

function use_slices() -> u32 {
    var whole: u32 = attempt inspect(ref buffer);
    var part: u32 = attempt inspect(ref buffer[4..12]);
    var empty: u32 = attempt inspect(ref buffer[16..16]);
    return Ok(whole + part + empty);
}
```

*Valid:* narrowing a view, and a slice used as the receiver of `.length`. (conformance: `valid/fun-008-narrowing-views.card`)

```text
function first_half(data: ref u8[]) -> u32 {
    return Ok(data.length);
}

function narrow(data: inout u8[]) -> u32 {
    var half: u32 = data.length / 2;
    var size: u32 = data[0..half].length;
    data[0] = 1;
    return first_half(ref data[0..half]);
}
```

*Invalid:* each of these is in its own test.

| Code | Class | Conformance |
|---|---|---|
| `var part: u8[4] = buffer[0..4];` | CE-FUN-5 | `invalid/fun-114-slice-in-initializer.card` |
| `destination = buffer[0..4];` | CE-FUN-5 | `invalid/fun-115-slice-in-assignment.card` |
| `fixed(buffer[0..4])` with by-value parameter `data: u8[4]` | CE-FUN-5 | `invalid/fun-116-slice-by-value.card` |
| `inspect(ref buffer[start..4])` with `start: i8` | CE-EXP-9 | `invalid/fun-119-signed-slice-endpoint.card` |
| `inspect(ref buffer[4..20])` on a `u8[16]` | CE-CEX-4 | `invalid/fun-120-constant-slice-out-of-range.card` |
| `inspect(ref buffer[8..4])` | CE-CEX-4 | `invalid/fun-121-constant-slice-reversed.card` |

## 8.11 Effects, persistence and errors through references

**FUN-22 [Agreed]** Functions may read and write any global, call platform APIs, and open transactions, subject to chapter 11. Calls have no purity or effect restrictions beyond those rules.
*Sources: D-352; DN §3.7.*

**FUN-23 [Agreed]** Passing storage by reference keeps its identity. A write through an `inout` path into persistent storage is a persistent write. It is atomic for its destination, and it participates in an active transaction (chapters 10 and 11). Two such writes are not atomic together unless a transaction groups them. A function that returns `Err` does not undo writes it made through references. Validate before changing data, or use a transaction and `abort` (chapter 11), which rolls back only the persistent writes.
*Sources: D-356; DN §3.7, §3.8, §8.4.*

## 8.12 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-FUN-1** | The call graph contains a cycle (recursion) | FUN-5 |
| **CE-FUN-2** | An argument's mode does not match its parameter's mode | EXP-53, FUN-7 |
| **CE-FUN-3** | A `ref` or `inout` argument does not identify existing storage | FUN-9 |
| **CE-FUN-4** | An `inout` argument is not mutable through its path | FUN-10, FUN-15 |
| **CE-FUN-5** | A slice in a position where slices are not allowed | FUN-18 |