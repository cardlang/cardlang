# SP3 — Types: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 4 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/04-types.md` | The kinds of type; type expressions and how type names resolve; type identity; primitive types; enums; structures; fixed arrays; unsized array view types; default values; no implicit conversions; finite sizes |
| `spec/annex-A-grammar.md` §A.2.2 | The `Type` production |
| `conformance/valid/typ-*`, `conformance/invalid/typ-*` | One test per chapter example |
| Register, Annex C, Annex D, 00-index | Body decisions D-321…, new issues, rule coverage, and the CE-TYP index |

**Out of scope:**

| Topic | Where |
|---|---|
| Typing of expressions: literals, operators, conversions, equality, field and index access, constructors, `fill`, `.length` | Chapter 6 (SP5). Chapter 4 only defines type identity, which chapter 6 uses |
| Evaluating array-length expressions, and dependency cycles through types | Chapter 5 (SP4). Chapter 4 states what a length must be |
| When defaults are applied (power-on, creation, locals) | Chapter 10 (SP9) and chapter 7 (SP6). Chapter 4 defines the default value of each type |
| Parameter modes, slices, and how views are passed | Chapter 8 (SP7). Chapter 4 defines the `T[]` type form and where it may be written |
| Storage classes and mutability of places | Chapters 8 and 10. Chapter 4 states that sub-places inherit them (D-073) |

## 2. Sources

- **DN sections:** §3.1, §3.4, §3.9 (defaults table), §3.11, §8, §8.1 (lengths), §8.2, §8.4 (`T[]` forms), §9, §9.1, §9.2, §9.3.
- **Decisions:**
  - D-059, D-060: array element types; `T[N]` syntax.
  - D-065, D-066, D-067, D-068: structures and enums.
  - D-072, D-073, D-074: nested structures; inherited storage and mutability; no recursive containment.
  - D-075, D-076, D-077: primitive types; byte arrays; no zero-length or multidimensional arrays.
  - D-100: no implicit Boolean, array or structure conversions.
  - D-412: no `byte` alias.
  - D-425: primitive type names are predeclared.
  - References only, owned by other sub-plans: D-099 (lengths, SP4), D-120 and D-121 (views, SP7), D-123 and D-128 (when defaults apply, SP9).

### 2.1 Body-only decisions to register (D-321…)

| ID | Decision | Source |
|---|---|---|
| D-321 | Arrays are composite types, not extra primitive scalar types. Enums and structures are user-defined types | DN §3.1 |
| D-322 | Every array length is a positive unsigned constant expression whose value fits in `u32` | DN §8.1, §8.2 |
| D-323 | Unsized array types `T[]` exist only as `ref`/`inout` parameter types. There are no unsized owned variables, fields or returns | DN §8.4 |
| D-324 | Structure field types are integers, booleans, enums, arrays and other structures. There are no methods, inheritance, field defaults or field-level storage qualifiers | DN §9 table, §9.3 |
| D-325 | A type declaration does not define physical layout, wire encoding or durable encoding. Enum representation and variant order are not a stable encoding | DN §3.9, §3.11, §9.2, §9.3 |

## 3. Approach

**Permissive type grammar** (the same approach as SP2). The grammar accepts any number of array suffixes, with or without a length:

```
Type ::= Identifier ( '[' Expression? ']' )*
```

Chapter rules then reject what CardLang does not allow, each with its own error class:

- arrays of arrays, such as `u8[2][3]`;
- an unsized `T[]` anywhere except a `ref`/`inout` parameter;
- invalid lengths.

**Type identity** is defined once here, and every later chapter uses it:

- primitive types are identified by name;
- structures and enums are identified by their declaration (nominal identity);
- fixed arrays are identical when their element types are identical and their lengths are equal *values*. For example, `u8[BLOCK * 4]` and `u8[128]` are the same type when `BLOCK` is 32.

## 4. Planned rules (chapter 4)

**§4.1 Kinds of type**

- **TYP-1** The *value types* are the primitive types, enums, structures and fixed arrays. Every variable, field, constant, by-value parameter and successful payload has a value type (D-321).
- **TYP-2** Unsized array types `T[]` are *view types*, not value types. Outcomes, errors and references are not types at all (cross-references to chapters 8 and 9).

**§4.2 Type expressions and identity**

- **TYP-3** In `Type`, the identifier must resolve (chapter 3) to a primitive type, an enum, a structure, or a platform-supplied type. If it resolves to anything else, such as a constant or a function, that is **CE-TYP-1**. If it does not resolve, that is CE-NAM-2.
- **TYP-4** Type identity, as described in §3 above (D-065, D-067).
- **TYP-5** No conversion is ever implicit between distinct types, including Boolean ↔ integer, between array types, and between structure types with matching fields. The one exception is contextual typing of literals (chapter 6) (D-100).

**§4.3 Primitive types**

- **TYP-6** The integer types are `u8`, `u16`, `u32`, `i8`, `i16` and `i32`, with exact ranges. The signed types use two's-complement ranges (D-075).
- **TYP-7** `bool` has exactly the values `true` and `false`, and is not an integer type (D-075, D-100).
- **TYP-8** There are no floating-point, 64-bit, character or string types (DN §3.1).
- **TYP-9** No language construct exposes the physical representation of a value. How Booleans, enums, structures and arrays are stored is not part of the language [→ OI-27] (D-325).

**§4.4 Enums**

- **TYP-10** An enum declares at least one variant. An empty enum is **CE-TYP-2**. A duplicate variant is CE-NAM-8 (D-067).
- **TYP-11** An enum's values are exactly its variants. There are no payloads, numeric values, ordering, arithmetic or numeric conversion (D-067; DN §3.11).
- **TYP-12** Enums are separate from the application's error set: a variant is never an error (DN §3.11).

**§4.5 Structures**

- **TYP-13** A structure declares at least one field. An empty structure is **CE-TYP-3** (D-066).
- **TYP-14** A field's type must be a value type. A `T[]` field is **CE-TYP-5**. Structures have no methods, inheritance, field defaults, access modifiers or per-field storage keywords (D-324).
- **TYP-15** No structure may contain itself, directly or indirectly, including through array fields. Such a containment cycle is **CE-TYP-4** (D-074).
- **TYP-16** A field, or an element at any depth, has the storage lifetime and mutability of the instance that contains it. Chapters 8 and 10 apply this rule (D-073).

**§4.6 Fixed arrays**

- **TYP-17** `T[N]` is an array of exactly `N` elements of type `T` (D-060).
- **TYP-18** The element type must be an integer, `bool`, an enum or a structure. An array of arrays, such as `u8[2][3]`, is **CE-TYP-6**. Use a structure with an array field instead (D-059, D-077).
- **TYP-19** The length must be a constant expression (chapter 5) of an unsigned integer type. A literal-only length is typed `u32`. Its value must be at least 1. A length of zero, or a length whose type is signed or Boolean, is **CE-TYP-7**. An unsigned length always fits in `u32` (D-322, D-077, D-099).
- **TYP-20** Byte arrays are written `u8[N]`. There is no `byte` alias (D-076, D-412).

**§4.7 Unsized array view types**

- **TYP-21** `T[]`, with the same element-type rule as TYP-18, may appear only as the type of a `ref` or `inout` parameter. Anywhere else it is **CE-TYP-5**: in a by-value parameter, a local, a global, a field, a constant, a return type, or an element type (D-323, D-120, D-121).

**§4.8 Default values**

- **TYP-22** `default(T)` is defined recursively:
  - zero for integer types;
  - `false` for `bool`;
  - the first declared variant for an enum;
  - every element's default for an array;
  - every field's default for a structure.

  Chapters 7 and 10 say when defaults are applied (D-068, D-123, D-128; DN §3.9).

**§4.9 Finite sizes**

- **TYP-23** Every value type has a finite size known at compile time. If a type or program exceeds the capacity of the selected target profile, the application is rejected at build or load time. Semantics never change to fit (D-206; DN §9.1).

**Errors**

| Class | Meaning |
|---|---|
| CE-TYP-1 | The name in a type position is not a type |
| CE-TYP-2 | Empty enum |
| CE-TYP-3 | Empty structure |
| CE-TYP-4 | Recursive containment |
| CE-TYP-5 | `T[]` outside a `ref`/`inout` parameter |
| CE-TYP-6 | Array of arrays |
| CE-TYP-7 | Invalid array length |

## 5. New open issue

| ID | Question | Recommendation |
|---|---|---|
| **OI-27** Boolean and enum storage representation | DN §3.1 says "Boolean storage representation … still require[s] specification". DN §3.9 and §3.11, however, say physical representation is an implementation or platform detail, and enum order is not a stable encoding. Must the language fix a representation? | No. The language exposes no representation, because no construct can observe it (TYP-9). How persistent values are laid out, and preserved across upgrades, belongs to the platform. It goes with the persistent-migration item already decided in D-416. The DN §3.1 sentence is treated as superseded |

**Decided 2026-11-15:** you accepted the recommendation. Step 1 records it as D-427, and TYP-9 is written as **[Agreed]**.

## 6. Grammar (Annex A §A.2.2)

```
Type ::= Identifier ( '[' Expression? ']' )*
```

`Expression` in a length position must be a constant expression (chapter 5). Several suffixes, or an empty suffix outside a `ref`/`inout` parameter, are rejected by TYP-18 and TYP-21.

## 7. Examples and conformance tests

All tests use `kind: fragment`.

**Valid**

| Test | Shows |
|---|---|
| `valid/typ-001-primitive-types.card` | Globals of all seven primitive types |
| `valid/typ-002-enums.card` | Enum declarations, an enum-typed global, an enum array, and an enum field |
| `valid/typ-003-nested-structures.card` | `Identity` nested in `Account` (DN §9.1) |
| `valid/typ-004-arrays.card` | `u8[128]`, `u32[8]`, `bool[8]`, `Account[4]` and an enum array |
| `valid/typ-005-constant-length.card` | `u8[BLOCK_SIZE * 4]`, plus a typed `u16` constant used as a length |
| `valid/typ-006-unsized-parameters.card` | `ref u8[]` and `inout Account[]` parameters |
| `valid/typ-007-same-array-type.card` | `u8[BLOCK * 4]` and `u8[128]` are one type: whole-array assignment between them is accepted |

**Invalid**

| Test | Expected error | Shows |
|---|---|---|
| `invalid/typ-101-empty-enum.card` | CE-TYP-2 | An empty enum |
| `invalid/typ-102-empty-struct.card` | CE-TYP-3 | An empty structure (DN §9.3) |
| `invalid/typ-103-direct-recursion.card` | CE-TYP-4 | `struct Node { child: Node; }` (DN §9.1) |
| `invalid/typ-104-indirect-recursion.card` | CE-TYP-4 | A contains B, and B contains A |
| `invalid/typ-105-recursion-through-array.card` | CE-TYP-4 | `struct A { items: A[2]; }` |
| `invalid/typ-106-array-of-arrays.card` | CE-TYP-6 | `u8[2][3]` |
| `invalid/typ-107-zero-length.card` | CE-TYP-7 | `u8[0]` |
| `invalid/typ-108-signed-length.card` | CE-TYP-7 | A length given by an `i8` constant |
| `invalid/typ-109-unsized-local.card` | CE-TYP-5 | `var data: u8[];` |
| `invalid/typ-110-unsized-field.card` | CE-TYP-5 | A `u8[]` field |
| `invalid/typ-111-unsized-by-value-parameter.card` | CE-TYP-5 | `data: u8[]` without `ref`/`inout` |
| `invalid/typ-112-unsized-return.card` | CE-TYP-5 | `-> u8[]` |
| `invalid/typ-113-not-a-type.card` | CE-TYP-1 | A constant's name used as a type |
| `invalid/typ-114-byte-alias.card` | CE-NAM-2 | `byte` is not adopted (D-412) |

The following are **deferred to SP5**, because they are typing errors in expressions: assigning between distinct structures with identical fields (DN §9.3), `var invalid: bool = 1;` (DN §3.4), and assigning an integer to an enum (DN §3.11). Chapter 4 refers to them.

Runtime tests that observe default values are **deferred to SP9**, because the runtime test format is still open.

## 8. Steps

1. Register D-321…D-325. Add OI-27 to Annex C and record your decision on it.
2. Write chapter 4.
3. Fill in Annex A §A.2.2.
4. Write the 21 tests, generated from the chapter examples as in SP2.
5. Update Annex D (D-059, D-060, D-065–D-068, D-072–D-077, D-100, D-321–D-325, D-412, plus partial references for D-099, D-120, D-121, D-123 and D-128), the index and the register.
6. Run the exit checklist. That includes a lexical check of all tests, and a scripted containment-cycle and array-suffix checker run over the tests' struct declarations.

## 9. Exit checklist

- Every TYP rule has a tag and a sources line. TYP-9 cites OI-27 until it is decided.
- Every type form used in DN code blocks derives from `Type`, and is valid under TYP-17 to TYP-21 (scripted scan).
- Every example has a test, and every reference resolves.
- Chapter 4 decides nothing about expression typing or evaluation.

## 10. Choices made in this sub-plan

These are open for redirection:

- The permissive type grammar, with its specific errors.
- Array type identity is decided by the *value* of the length, not how it is written.
- "View type" as the name for `T[]`.
- The default values of types are defined here, while *when* they apply is defined in chapters 7 and 10.
- Expression-level typing examples are deferred to SP5.
