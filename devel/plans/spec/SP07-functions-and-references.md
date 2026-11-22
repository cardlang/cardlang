# SP7 — Functions, references and slices: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 8 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/08-functions-and-references.md` | Function declarations and signatures; the static call graph (no recursion); parameter modes and call-site modes; reference and view arguments; argument preparation; access-path permissions and aliasing; forwarding; lifetimes; value semantics and copies; slices; effects; persistence and errors through references |
| `spec/annex-A-grammar.md` §A.2.6 | `ParameterList`, `Parameter` and `ReturnType`. Slices and argument modes are already in §A.2.4 |
| `conformance/valid/fun-*`, `conformance/invalid/fun-*` | One test per example, plus the constant-slice test deferred from SP4 (D-429) |
| Register, Annex C, Annex D, 00-index | Body decisions D-352…, new issues, rule coverage and the CE-FUN index |

**Out of scope:**

| Topic | Where |
|---|---|
| Typing of outcomes, `return` forms and forwarding returns | Chapter 9 (SP8) |
| The `command` signature | Chapter 12 (SP11) |
| Transaction participation of writes through references | Chapters 10 and 11. Chapter 8 states that storage identity is preserved |
| Call-frame placement, reference descriptor representation and stack accounting | Annex B (SP13) |

## 2. Sources

- **DN sections:** §3.0 (signatures), §3.7 (all), §3.8 (all), §8.4 (all), §9.2 (by-value aggregate parameters), §11.1 (identifiers are values, not references).
- **Decisions:**

| Decisions | Topic |
|---|---|
| D-025, D-026 | Signatures; positional arguments; modes; trailing commas |
| D-031, D-032, D-033 | No recursion, function values, prototypes or tuples |
| D-112 to D-121 | Modes, references, permissions, copies, targets, overlap, slices, `T[]` parameters, fixed-size by-value arrays |
| D-330 | A constant may be passed through `ref`, never `inout` |
| D-410 | Slice details |
| D-429 | Constant slice bounds (already applied in chapter 5) |

### 2.1 Body-only decisions to register (D-352…)

| ID | Decision | Source |
|---|---|---|
| D-352 | Ordinary functions may access globals, call platform APIs and open transactions. There are no purity or effect annotations, and no `pure`, `static` or `public` modifiers | DN §3.7 |
| D-353 | Before the callee starts, all arguments are evaluated left to right, by-value values are established, reference and slice regions are fixed, and their bounds are checked. Regions are not re-evaluated during the call | DN §3.7, §8.4 |
| D-354 | Forwarding: `ref` to `ref`; `inout` to `ref` or `inout`; fields, elements and slices forwarded under the same rules. Forwarding never strengthens permissions or extends lifetime | DN §3.8, §8.4 |
| D-355 | References and views end with their call, whether it returns `Ok` or `Err`. Frames ended by a trap discard their references | DN §3.8 |
| D-356 | Storage identity survives reference passing: a write through `inout` to persistent storage is a persistent write. `Err` does not undo earlier mutations | DN §3.7, §3.8 |
| D-357 | Compilers must preserve observable aliasing effects. They must not assume that `ref` storage is stable or that `inout` storage is unaliased, and must not substitute copies to hide aliasing | DN §3.7, §3.8 |
| D-358 | Physical copies may be removed only when behavior is unchanged. Sharing is never substituted for copying | DN §3.8 |
| D-359 | Inside the callee, a view is indexed from 0, and its `.length` is the length of the region. A parameter cannot resize or rebind its region. A view may be narrowed to a slice within its region | DN §8.4 |

## 3. Planned rules (chapter 8)

**§8.1 Declarations**

- **FUN-1** The grammar `function name(params) (-> T)? Block`. Parameters are written `name: Type`, `name: ref Type` or `name: inout Type`, with an optional trailing comma (D-026).
- **FUN-2** The return type `T` is a value type; `T[]` is rejected by TYP-21. Omitting the arrow means success carries no payload. There is exactly one payload: no tuples, and no references. A structure is the way to group values (D-025, D-033).
- **FUN-3** There are no prototypes, forward declarations, external declarations, nested functions, overloading or modifiers. Platform APIs are supplied by the platform (D-032, D-352; NAM-7, NAM-12).

**§8.2 The static call graph**

- **FUN-4** Every call names its target directly. Function values, function pointers and callbacks do not exist (D-031).
- **FUN-5** The *call graph* has an edge from F to G when F's body contains a call to G. Direct or indirect recursion — a cycle in this graph across the whole application — is **CE-FUN-1**. Intrinsics and platform APIs are leaves: they never call application code (D-031).

**§8.3 Parameter modes**

- **FUN-6** The meaning of each parameter mode:

| Mode | Meaning |
|---|---|
| By value | An independent copy, bound read-only. To change it, copy it into a `var` |
| `ref` | A read-only access path to existing storage of exactly type `T`, or of a `T[]` view |
| `inout` | A read-write access path to existing storage |

  (D-112, D-114, D-115.)
- **FUN-7** Each argument is written with exactly its parameter's mode: `ref e` for a `ref` parameter, `inout e` for an `inout` parameter, and a plain expression for a by-value parameter. A missing, extra or different mode is **CE-FUN-2** (D-113).
- **FUN-8** Argument types match the parameter type exactly (TYP-4). The one exception is a `T[]` parameter, which accepts a fixed array `T[N]` of any `N`, a slice, or another `T[]` view, as long as the element type is exactly `T`. A slice or a view never satisfies a `T[N]` parameter. By-value array parameters are always fixed size (D-120, D-121, D-410).

**§8.4 Reference arguments**

- **FUN-9** A `ref` or `inout` argument must *identify existing storage*:
  - a variable, global, constant or parameter;
  - a pattern binding or `for` index [→ OI-35];
  - a field or element path rooted in one of those;
  - a slice.

  Anything else is **CE-FUN-3**. That includes literals, calls, constructors, array lists, `fill`, arithmetic, `attempt` and `.length` (D-117).
- **FUN-10** An `inout` argument must also be a mutable place under STM-7. Each of the following is **CE-FUN-4**: a constant, a path rooted in a `ref` parameter, a by-value parameter, a `for` index or a pattern binding (D-330, D-115).

**§8.5 Argument preparation**

- **FUN-11** Arguments are prepared left to right:
  - a by-value argument is evaluated and copied;
  - for a reference argument, its path is evaluated and every index is checked (`TRAP-BOUNDS`);
  - for a slice argument, its region is established and checked (§8.10).

  All of this completes before the callee starts. Paths and regions are never re-evaluated during the call. No exclusive access is acquired (D-353).

**§8.6 Access-path permissions and aliasing**

- **FUN-12** Permissions attach to the access path, not to the storage:
  - Writing through a `ref` path is rejected by STM-7.
  - `inout` permits reading and writing through its path.
  - Neither grants exclusive access. Other paths — globals, other references, or nested calls — may read or write the same storage under their own permissions.
  - A `ref` parameter is not a snapshot: it observes writes made through other paths, in evaluation order.

  (D-115, D-118.)
- **FUN-13** Overlapping references and slices are allowed in every combination, including `inout` with `inout`. There are no overlap checks and no overlap traps (D-118).
- **FUN-14** Implementations must preserve every observable aliasing effect. They must not assume that `ref` storage is stable or that `inout` storage is unaliased, and must not substitute copies to hide aliasing (D-357).

**§8.7 Forwarding**

- **FUN-15** A `ref` parameter, or a path or slice derived from it, may be passed on only as `ref`. Passing it as `inout` is **CE-FUN-4**. An `inout` parameter, or anything derived from it, may be passed on as `ref` or `inout`. Forwarding never extends a lifetime (D-354).

**§8.8 Lifetimes**

- **FUN-16** A reference or view exists only during the call it was passed to, and ends when that call returns `Ok` or `Err`, or when a trap ends the frame. References and views cannot be returned (TYP-21, FUN-2), stored in variables, globals, fields or arrays, compared, converted, or made null. No reference variables or arrays of references exist (D-114, D-355).

**§8.9 Value semantics**

- **FUN-17** By-value arguments and successful return payloads are independent, complete copies, including nested aggregates. A compiler may remove a physical copy only when this cannot be observed. Sharing is never substituted for copying. Storage that exceeds a target's limits leads to rejection (TYP-23) (D-116, D-358).

**§8.10 Slices**

- **FUN-18** `a[s..e]`, where `a` has type `T[N]` or `T[]`, has type `T[]`. A slice may appear only in these positions:
  - as a `ref` or `inout` argument to a `T[]` parameter, including the `decode_*` intrinsics;
  - as the receiver of indexing, of `.length`, or of another slice.

  Anywhere else it is **CE-FUN-5**. That covers initializers, assignments, operands, by-value arguments and return payloads (D-119, D-410).
- **FUN-19** The endpoints `s` and `e` are each typed `u8`, `u16` or `u32`, independently of each other. A literal-only endpoint gets `u32` context. A signed or non-integer endpoint is CE-EXP-9 (D-410).
- **FUN-20** Evaluation order:
  1. Evaluate the receiver.
  2. Evaluate `s`.
  3. Evaluate `e`.
  4. Check that `s ≤ e` and `e ≤ a.length`; otherwise `trap(BOUNDS)`.

  On a fixed array, constant-only endpoints are checked at compile time instead (CEX-10, D-429). Empty slices are valid. Both endpoints must always be written (D-119, D-410).
- **FUN-21** The view refers to the elements `a[s]` … `a[e−1]`, without copying them. Inside the callee, indexing starts at 0 and `.length` is `e − s`. The view's permissions are those of the path it came from. A parameter cannot resize or rebind its view, but it may pass on a narrower slice of it. There is no whole-slice assignment or `fill` (D-359, D-410).

**§8.11 Effects, persistence and errors**

- **FUN-22** Functions may read and write globals, call platform APIs, and open transactions, subject to chapter 11 (D-352).
- **FUN-23** A write through `inout` to persistent storage is a persistent write: atomic per assignment, and part of any active transaction (chapters 10 and 11). Returning `Err` never undoes earlier writes through references, and `abort` rolls back only persistent ones (chapter 11) (D-356).

**Error classes**

| Class | Meaning |
|---|---|
| CE-FUN-1 | Recursion |
| CE-FUN-2 | Argument mode mismatch |
| CE-FUN-3 | A reference argument does not identify storage |
| CE-FUN-4 | An `inout` argument is not mutable, including a `ref` forwarded as `inout` |
| CE-FUN-5 | A slice in a disallowed position |

Argument type mismatches use CE-EXP-1.

## 4. New open issue

| ID | Question | Options | Recommendation |
|---|---|---|---|
| **OI-35** `ref` to read-only bindings | DN §3.8 says references may target "named variables, structure fields and array elements". May a `for` index or a pattern binding, both read-only bindings, be passed as `ref`? A by-value parameter is a named read-only variable, so it already qualifies | (a) Yes, as `ref` only, never `inout`. (b) No: copy it into a `var` first | (a). Such a binding is existing read-only storage, so passing it as `ref` grants nothing new |

**Decided 2026-11-15:** you accepted the recommendation. It is recorded as D-435, and FUN-9 is **[Agreed]**.

## 5. Grammar (Annex A §A.2.6)

```
ParameterList ::= '(' ( Parameter ( ',' Parameter )* ','? )? ')'
Parameter     ::= Identifier ':' ( 'ref' | 'inout' )? Type
ReturnType    ::= '->' Type
```

## 6. Conformance tests (about 36)

**Valid (about 14):**

- a forward call across files;
- a struct return used to group values (DN §3.7 `Measurement`);
- no-payload and payload functions;
- `ref` and `inout` of a field (DN §3.8);
- an element reference;
- overlapping `inout`/`inout` and `inout`/`ref` (DN §3.8);
- the aliasing example from DN §3.8, with `update(inout buffer[0], 0)`;
- forwarding `inout` as `ref` and as `inout` (DN §3.8 `process`);
- a whole array and a slice passed to `ref u8[]` (DN §8.4);
- an empty slice at the end of an array;
- narrowing a view to a slice;
- slice `.length` as a receiver;
- a constant passed as `ref`;
- a by-value parameter passed as `ref`;
- `ref` of a `for` index (if OI-35 is (a)).

**Invalid (about 22):**

| Test | Expected error |
|---|---|
| Direct recursion (DN §3.7) | CE-FUN-1 |
| Indirect recursion (DN §3.7) | CE-FUN-1 |
| Recursion across files | CE-FUN-1 |
| Missing call-site `ref` | CE-FUN-2 |
| Missing call-site `inout` | CE-FUN-2 |
| `ref` given to a by-value parameter | CE-FUN-2 |
| `inout` given to a `ref` parameter | CE-FUN-2 |
| `ref Account { … }`, a temporary (DN §3.8) | CE-FUN-3 |
| `ref` of a call result | CE-FUN-3 |
| `ref` of an arithmetic expression | CE-FUN-3 |
| A constant passed as `inout` | CE-FUN-4 |
| A `ref` parameter forwarded as `inout` | CE-FUN-4 |
| A by-value parameter passed as `inout` | CE-FUN-4 |
| A slice in an initializer | CE-FUN-5 |
| A slice in an assignment | CE-FUN-5 |
| A slice passed by value | CE-FUN-5 |
| A slice given to a `T[N]` parameter | CE-EXP-1 |
| An element type mismatch for `ref u8[]` | CE-EXP-1 |
| A signed slice endpoint | CE-EXP-9 |
| A constant slice beyond the length (D-429, deferred from SP4) | CE-CEX-4 |
| Constant slice endpoints with start > end | CE-CEX-4 |
| A `T[]` return type | CE-TYP-5 |

**Runtime tests** for aliasing results, argument preparation order and slice bounds traps are listed now and written in SP12.

## 7. Steps

1. Register D-352…D-359. Add OI-35 and record your decision.
2. Write chapter 8.
3. Fill in §A.2.6.
4. Generate the tests, with the chapter cross-check.
5. Update the traceability. This also resolves the partial entries for D-330 and D-410.
6. Checks: extend the checker with modes, reference targets, forwarding, slice positions and endpoints, and call-graph cycle detection. Run it over all tests and the DN blocks.

## 8. Choices made in this sub-plan

These are open for redirection:

- A slice may be the receiver of indexing, `.length`, or another slice. This is how I read "receivers" in the OI-10 decision.
- A by-value parameter counts as existing storage for `ref`.
- Argument type mismatches reuse CE-EXP-1 rather than adding a CE-FUN class.
- Intrinsics and platform APIs are leaves of the call graph. A platform callback model, if one is ever introduced, would need its own rules (DN §3.7).
