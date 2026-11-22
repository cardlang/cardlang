# 4. Types

CardLang Language Specification, Draft 0.2. Chapter status: **draft complete**.

This chapter defines CardLang's types:

- which types exist and how type expressions are written;
- when two types are the same type;
- the rules for primitive types, enums, structures, fixed arrays and unsized array views;
- the default value of every type.

Other chapters build on these definitions:

| Chapter | Defines |
|---|---|
| 5 | Evaluation of array-length expressions |
| 6 | How expressions are typed |
| 7 and 10 | When default values are applied |
| 8 | Passing views and references |

As in chapter 3, the type grammar (Annex A §A.2.2) accepts some forms that rules in this chapter then reject with specific error classes.

## 4.1 Kinds of type

**TYP-1 [Agreed]** The *value types* are:

- the primitive types (§4.3);
- enum types (§4.4);
- structure types (§4.5);
- fixed array types `T[N]` (§4.6).

The following all have a value type:

- variables;
- constants;
- persistent and session globals;
- structure fields;
- array elements;
- by-value parameters;
- successful payloads.

Arrays are composite types, not additional primitive types. Enums and structures are user-defined, nominal types.
*Sources: D-321, D-075; DN §3.1, §3.4.*

**TYP-2 [Agreed]** An *unsized array type* `T[]` is a *view type*. It is not a value type and may appear only where TYP-21 allows. Outcomes, error values and references are not types: no type can be written for them, and they cannot be stored (chapters 8 and 9).
*Sources: D-016, D-028, D-114, D-323; DN §6.3, §8.4.*

## 4.2 Type expressions and type identity

```
Type ::= Identifier ( '[' Expression? ']' )*
```

**TYP-3 [Agreed]** The identifier at the start of a `Type` must resolve, under the rules of chapter 3, to one of:

- a primitive type name;
- an enum declaration;
- a structure declaration;
- a platform-supplied type.

If it resolves to anything else, such as a constant, global, function or error set, that is **CE-TYP-1**. If it does not resolve at all, that is CE-NAM-2. Types may be used before their declarations (NAM-13).
*Sources: D-045, D-314; DN §4.2.* *Derivation: a type position requires a type, and §4.3–§4.5 list everything that denotes one.*

**TYP-4 [Agreed]** Two types are *identical* exactly when one of the following holds:

- both are the same primitive type;
- both name the same enum declaration;
- both name the same structure declaration;
- both are fixed arrays whose element types are identical and whose lengths have the same value (evaluated under chapter 5);
- both are unsized array types whose element types are identical.

Structures and enums are nominal. Two separately declared structures are different types even if their fields match exactly. Two enums are different even if their variant lists match. An array length is compared by value, not by how it is written: `u8[BLOCK * 4]` and `u8[128]` are identical when `BLOCK` is 32.
*Sources: D-065, D-067, D-078; DN §3.11, §8.2, §9.3.*

**TYP-5 [Agreed]** No value is ever implicitly converted from one type to a different type. In particular, there is no conversion:

- between integer types;
- between `bool` and integers;
- between enums and integers;
- between array types;
- between structure types.

Wherever chapters 6–12 require a value of a given type, a value of an identical type (TYP-4) must be supplied. The only exception is the contextual typing of integer literals (chapter 6), which gives an untyped literal a type. It is not a conversion. Explicit numeric conversions are the intrinsics in chapter 6.
*Sources: D-081, D-100, D-084; DN §3.2, §3.4.*

### Examples

*Valid:* two array types written differently are identical, so whole-array assignment between them is accepted. (conformance: `valid/typ-007-same-array-type.card`)

```text
const BLOCK: u32 = 32;
session first: u8[BLOCK * 4];
session second: u8[128];

function copy_buffer() {
    second = first;
    return Ok();
}
```

*Invalid:* a constant used where a type is required. **CE-TYP-1**. (conformance: `invalid/typ-113-not-a-type.card`)

```text
const BASE: u32 = 4;
session buffer: BASE;
```

## 4.3 Primitive types

**TYP-6 [Agreed]** The integer types and their value ranges are:

| Type | Values |
|---|---|
| `u8` | 0 to 255 |
| `u16` | 0 to 65,535 |
| `u32` | 0 to 4,294,967,295 |
| `i8` | −128 to 127 |
| `i16` | −32,768 to 32,767 |
| `i32` | −2,147,483,648 to 2,147,483,647 |

The *unsigned* integer types are `u8`, `u16` and `u32`. The *signed* integer types are `i8`, `i16` and `i32`. The value of an `N`-bit signed type is in the two's-complement range: from −2^(N−1) to 2^(N−1) − 1. Chapter 6 uses the two's-complement interpretation where an operation is defined on bits (wrapping arithmetic).
*Sources: D-075; DN §3.1, §6.5.*

**TYP-7 [Agreed]** The type `bool` has exactly two values, `true` and `false`. `bool` is not an integer type. No integer operation applies to it, and it has no numeric value (TYP-5).
*Sources: D-075, D-100; DN §3.1, §3.4.*

**TYP-8 [Agreed]** CardLang has no floating-point, 64-bit integer, character or string types.
*Sources: D-075; DN §3.1.*

**TYP-9 [Agreed]** The physical representation of values is not part of the language. This covers how Booleans, enums, integers, structures and arrays are stored in memory or persistent storage, including field order, padding and byte order. No language construct can observe a representation: there are no casts, unions, memory views or size-of operators. Converting values to and from bytes is done explicitly by application code (chapter 6). Persistent layout, and its preservation across application upgrades, are platform-defined (Annex B). Enum variant order defines the default value (TYP-22) and nothing else. In particular, it is not a stable encoding.
*Sources: D-325, D-427 (OI-27); DN §3.4, §3.9, §3.11, §9.2, §9.3.*

### Examples

*Valid:* globals of every primitive type. (conformance: `valid/typ-001-primitive-types.card`)

```text
persistent small: u8;
persistent medium: u16;
persistent large: u32;
session delta8: i8;
session delta16: i16;
session delta32: i32;
session ready: bool;
```

*Invalid:* there is no 64-bit integer type, so `u64` does not resolve (TYP-8). **CE-NAM-2**. (conformance: `invalid/typ-115-no-64-bit.card`)

```text
session big: u64;
```

## 4.4 Enums

```
EnumDeclaration ::= 'enum' Identifier '{' ( Identifier ';' )* '}'
```

**TYP-10 [Agreed]** An enum declaration declares a new nominal type whose values are exactly its variants. It must declare at least one variant. An enum with no variants is **CE-TYP-2**. Variant names are unique within their enum (NAM-15) and are always written qualified, as in `OperationState.Idle` (NAM-16).
*Sources: D-067; DN §3.11.*

**TYP-11 [Agreed]** Enum variants carry no payload and no numeric value. Enum types have:

- no ordering;
- no arithmetic or bitwise operations;
- no numeric conversion, including `convert` and `checked_convert`.

The operations on enum values are equality (chapter 6) and `match` (chapter 7). Enums may be element types of arrays and field types of structures.
*Sources: D-067, D-059; DN §3.11.*

**TYP-12 [Agreed]** An enum is not an error set. Its variants are never error values and cannot be returned as errors. Defining any number of enums does not change the limit of at most one application error set (chapter 9).
*Sources: D-067, D-413; DN §3.11.*

### Examples

*Valid:* an enum used as a global, an array element type and a field type. (conformance: `valid/typ-002-enums.card`)

```text
enum OperationState {
    Idle;
    Receiving;
    Complete;
}

struct Operation {
    state: OperationState;
    received: u32;
}

session state: OperationState;
session history: OperationState[4];
session operation: Operation;
```

*Invalid:* an enum with no variants. **CE-TYP-2**. (conformance: `invalid/typ-101-empty-enum.card`)

```text
enum Empty {
}
```

## 4.5 Structures

```
StructDeclaration ::= 'struct' Identifier '{' FieldDeclaration* '}'
FieldDeclaration  ::= Identifier ':' Type ';'
```

**TYP-13 [Agreed]** A structure declaration declares a new nominal type with named, typed fields. It must declare at least one field. A structure with no fields is **CE-TYP-3**. Field names are unique within their structure (NAM-15).
*Sources: D-065, D-066; DN §9, §9.3.*

**TYP-14 [Agreed]** The type of each field must be a value type (TYP-1): an integer, `bool`, an enum, a fixed array or another structure. A field of unsized array type is **CE-TYP-5** (TYP-21). Structures have none of the following:

- methods;
- inheritance;
- field default values;
- access modifiers;
- per-field storage keywords.

Behavior is written as ordinary functions.
*Sources: D-072, D-324; DN §9, §9.3.*

**TYP-15 [Agreed]** A structure must not contain itself. Structure `S` *contains* structure `R` if any field of `S` has one of these types:

- `R`;
- a fixed array whose element type is `R`;
- a structure that contains `R`.

A structure that contains itself, directly or through any chain of fields and array element types, is **CE-TYP-4**. This keeps the size of every structure finite (TYP-23).
*Sources: D-074; DN §9.1, §9.3.*

**TYP-16 [Agreed]** Fields and elements have no storage class or mutability of their own. A field of a structure, or an element of an array, at any depth, has the storage lifetime and mutability of the instance that contains it:

- every part of a persistent instance is persistent;
- every part of a session instance has session lifetime;
- no part of a constant can be modified.

Chapters 8 and 10 apply this rule to access paths and state.
*Sources: D-073; DN §9, §9.1.*

### Examples

*Valid:* a structure nested in another structure (DN §9.1). (conformance: `valid/typ-003-nested-structures.card`)

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
```

*Invalid:* a structure with no fields (DN §9.3). **CE-TYP-3**. (conformance: `invalid/typ-102-empty-struct.card`)

```text
struct Empty {
}
```

*Invalid:* a structure that directly contains itself (DN §9.1). **CE-TYP-4**. (conformance: `invalid/typ-103-direct-recursion.card`)

```text
struct Node {
    child: Node;
}
```

*Invalid:* two structures that contain each other. **CE-TYP-4**. (conformance: `invalid/typ-104-indirect-recursion.card`)

```text
struct First {
    second: Second;
}

struct Second {
    first: First;
}
```

*Invalid:* a structure that contains itself through an array field. **CE-TYP-4**. (conformance: `invalid/typ-105-recursion-through-array.card`)

```text
struct Tree {
    children: Tree[2];
}
```

*Invalid:* a field of unsized array type. **CE-TYP-5**. (conformance: `invalid/typ-110-unsized-field.card`)

```text
struct Packet {
    payload: u8[];
}
```

## 4.6 Fixed arrays

**TYP-17 [Agreed]** The type `T[N]` is a fixed array of exactly `N` elements of type `T`, where `N` is the array's *length*. The length is part of the type (TYP-4) and is never changed at runtime.
*Sources: D-060; DN §8, §8.2.*

**TYP-18 [Agreed]** The element type `T` of an array must be one of:

- an integer type;
- `bool`;
- an enum type;
- a structure type.

An array type whose element type is itself an array type, such as `u8[2][3]`, is **CE-TYP-6**. To get a multidimensional shape, use an array of structures with array fields.
*Sources: D-059, D-077; DN §8, §8.2.*

**TYP-19 [Agreed]** The length expression `N` must be a constant expression (chapter 5) whose type is an unsigned integer type:

- a typed constant of type `u8`, `u16` or `u32` keeps its type;
- an expression made only of literals is typed `u32`.

The value of `N` must be at least 1. Each of the following is **CE-TYP-7**:

- a length whose value is zero;
- a length whose type is a signed integer type or `bool`.

A length that is not a constant expression is an error defined in chapter 5. Every valid length fits in `u32`. A length the target profile cannot support is handled by TYP-23.
*Sources: D-077, D-099, D-322; DN §3.10, §8.1, §8.2.*

**TYP-20 [Agreed]** Byte arrays are ordinary arrays of `u8`, written `u8[N]`. CardLang has no `byte` alias: `byte` is an ordinary identifier with no predeclared meaning.
*Sources: D-076, D-412 (OI-12); DN §3.1, §8.*

### Examples

*Valid:* arrays of integers, Booleans, structures and enums. (conformance: `valid/typ-004-arrays.card`)

```text
struct Account {
    balance: u32;
    identifier: u8[4];
    counters: u32[8];
}

enum Mode {
    Off;
    On;
}

session buffer: u8[128];
session counters: u32[8];
session enabled: bool[8];
session accounts: Account[4];
session modes: Mode[2];
```

*Valid:* lengths given by constant expressions, including a typed `u16` constant. (conformance: `valid/typ-005-constant-length.card`)

```text
const BLOCK_SIZE: u32 = 32;
const SMALL_COUNT: u16 = 4;
session buffer: u8[BLOCK_SIZE * 4];
session flags: bool[SMALL_COUNT];
```

*Invalid:* an array of arrays. **CE-TYP-6**. (conformance: `invalid/typ-106-array-of-arrays.card`)

```text
session grid: u8[2][3];
```

*Invalid:* a zero length. **CE-TYP-7**. (conformance: `invalid/typ-107-zero-length.card`)

```text
session buffer: u8[0];
```

*Invalid:* a length of signed type. **CE-TYP-7**. (conformance: `invalid/typ-108-signed-length.card`)

```text
const COUNT: i8 = 4;
session buffer: u8[COUNT];
```

*Invalid:* `byte` is not a type name. **CE-NAM-2**. (conformance: `invalid/typ-114-byte-alias.card`)

```text
session buffer: byte[4];
```

## 4.7 Unsized array view types

**TYP-21 [Agreed]** An unsized array type `T[]` follows the element-type rule of TYP-18. It may be written only as the declared type of a `ref` or `inout` parameter (chapter 8). There, it accepts a whole fixed array or a slice whose element type is identical to `T`, of any length, and its length is known only at runtime. An unsized array type anywhere else is **CE-TYP-5**. That includes:

- a by-value parameter;
- a local variable;
- a global;
- a constant;
- a structure field;
- an array element type;
- a successful return type.

CardLang has no owned variable-length values.
*Sources: D-120, D-121, D-323; DN §8.4.*

### Examples

*Valid:* unsized `ref` and `inout` parameters. (conformance: `valid/typ-006-unsized-parameters.card`)

```text
struct Account {
    balance: u32;
}

function inspect(data: ref u8[]) {
    return Ok();
}

function clear_balances(accounts: inout Account[]) {
    for index: u32 in 0..accounts.length {
        accounts[index].balance = 0;
    }
    return Ok();
}
```

*Invalid:* an unsized local variable. **CE-TYP-5**. (conformance: `invalid/typ-109-unsized-local.card`)

```text
function process() {
    var data: u8[];
    return Ok();
}
```

*Invalid:* an unsized by-value parameter. **CE-TYP-5**. (conformance: `invalid/typ-111-unsized-by-value-parameter.card`)

```text
function inspect(data: u8[]) {
    return Ok();
}
```

*Invalid:* an unsized return type. The body is an endless loop, so it needs no `return` and the only error is the return type. **CE-TYP-5**. (conformance: `invalid/typ-112-unsized-return.card`)

```text
function produce() -> u8[] {
    while true {
    }
}
```

## 4.8 Default values

**TYP-22 [Agreed]** Every value type `T` has a *default value*, `default(T)`, defined recursively:

| Type | `default(T)` |
|---|---|
| Integer type | Zero |
| `bool` | `false` |
| Enum | Its first declared variant |
| `T[N]` | An array whose `N` elements are each `default(T)` |
| Structure | A structure whose fields each have the default of their own type |

Default values are semantic values. They say nothing about representation (TYP-9). Chapter 10 says when persistent and session state receives default values. Chapter 7 does the same for local variables declared without an initializer. Reordering an enum's variants changes its default. That is intended.
*Sources: D-068, D-123, D-128; DN §3.9, §3.11.*

## 4.9 Finite sizes and target capacity

**TYP-23 [Agreed]** Every value type has a finite size known at compile time. TYP-15, TYP-18 and TYP-19 guarantee this. If a type or program needs more storage than the selected target profile provides, the application is rejected at build or load time, under rules in Annex B. A conforming implementation never changes language semantics to fit a limit, for example by replacing value copies with shared references.
*Sources: D-206, D-074; DN §9.1, §12; PN §4.*

## 4.10 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-TYP-1** | The name in a type position is not a type | TYP-3 |
| **CE-TYP-2** | An enum declares no variants | TYP-10 |
| **CE-TYP-3** | A structure declares no fields | TYP-13 |
| **CE-TYP-4** | A structure contains itself | TYP-15 |
| **CE-TYP-5** | An unsized array type outside a `ref`/`inout` parameter | TYP-14, TYP-21 |
| **CE-TYP-6** | An array type whose element type is an array | TYP-18 |
| **CE-TYP-7** | An array length that is zero or not of an unsigned integer type | TYP-19 |

The following typing errors involving these types are defined in chapter 6 and tested there:

- assigning between distinct structure types with identical fields;
- initializing a `bool` from an integer;
- assigning an integer to an enum variable.
