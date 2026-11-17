# 3. Program structure and names

CardLang Language Specification, Draft 0.1. Chapter status: **draft complete** (SP2).

This chapter defines how an application is assembled from source files, which declarations exist and where they may appear, and how every name is resolved. What each declaration *means* is defined in later chapters:

| Chapter | Defines |
|---|---|
| 4 | Types, structures and enums |
| 5 | Constants |
| 8 | Functions |
| 9 | Error sets |
| 10 | Persistent and session state |
| 12 | The `command` |

**Grammar approach.** Some restrictions are stated here as rules with their own compile-error classes, not built into the grammar. Examples are the restrictions on storage keywords. The grammar in Annex A §A.2.1 therefore accepts slightly more than CardLang allows, and these rules reject the rest with a precise diagnosis.

## 3.1 Applications and compilation units

**NAM-1 [Agreed]** An application is compiled from a build-supplied list of source files, together with a build-supplied application identity. All the listed files form one *compilation unit*. The format of the build configuration is outside the language. There is no source-level application wrapper.
*Sources: D-021, D-022; DN §3.0, §4.1.*

**NAM-2 [Agreed]** Each source file must on its own be a derivation of `SourceFile` (Annex A §A.2.1): a sequence of complete top-level declarations. A declaration cannot begin in one file and continue in another. Any such attempt fails to derive and is **CE-SYN-1**. A file may contain no declarations at all, for example only comments.
*Sources: D-022, D-313; DN §3.0.*

**NAM-3 [Agreed]** Listing the same file twice in the build file list is a build-configuration error. It is outside the language and has no CE class. The language permits an empty file list. Such an application is still rejected, because it has no host entry point (chapter 12).
*Sources: D-426 (OI-26).*

**NAM-4 [Agreed]** Neither the order of the file list nor the order of declarations within or across files affects name resolution or the meaning of the program. Chapter 5 defines how constants are evaluated regardless of order. Mutable globals have no initializers, so they have no initialization order (chapter 10).
*Sources: D-040, D-314; DN §4.1, §4.2.*

**NAM-5 [Agreed]** Applications are completely isolated. No name in an application refers to a declaration, state, function or error of another application. There are no imports, cross-application calls, shared state or cross-application references.
*Sources: D-020; DN §1, §4.1.*

## 3.2 Top-level declarations

**NAM-6 [Agreed]** The kinds of top-level declaration are:

| Kind | Form |
|---|---|
| Global value | `persistent`, `session` or `const` (chapters 5 and 10) |
| Function | `function` (chapter 8) |
| Host entry point | `command` (chapter 12) |
| Structure type | `struct` (chapter 4) |
| Enum type | `enum` (chapter 4) |
| Error set | `errors` (chapter 9) |

*Sources: D-003, D-022; DN §4.2.*

**NAM-7 [Agreed]** Functions, commands, structures, enums and error sets may be declared only at top level. The statement grammar contains none of these forms, so writing one inside a block is **CE-SYN-1**.
*Sources: D-046, D-316; DN §4.2.*

**NAM-8 [Agreed]** CardLang has no application wrapper, modules, namespaces, imports, exports, classes, access modifiers or per-file privacy.
*Sources: D-022, D-039; DN §4.1.*

**NAM-9 [Agreed]** A top-level value declaration has exactly one storage keyword, and that keyword is `persistent`, `session` or `const`. Each of the following is **CE-NAM-6**:

- a top-level declaration whose only keyword is `var`;
- any declaration with more than one storage keyword, such as `persistent var`, `session var`, `persistent const` or `session const`.

*Sources: D-003, D-320; DN §5.1.*

**NAM-10 [Agreed]** Inside a function or command body, a value declaration has exactly the keyword `var`. A `persistent`, `session` or `const` keyword on a value declaration inside a body is **CE-NAM-7**. This includes local `const`, which is deferred. CardLang has no `local` keyword: `local` is an ordinary identifier, so `local var x: u32;` fails to parse (**CE-SYN-1**).
*Sources: D-006, D-007, D-320; DN §5.1.*

```
SourceFile             ::= TopLevelDeclaration*
TopLevelDeclaration    ::= GlobalValueDeclaration | FunctionDeclaration | CommandDeclaration
                         | StructDeclaration | EnumDeclaration | ErrorSetDeclaration
GlobalValueDeclaration ::= StorageKeyword+ Identifier ':' Type ( '=' Expression )? ';'
StorageKeyword         ::= 'persistent' | 'session' | 'const' | 'var'
```

### Examples

*Invalid:* plain `var` at top level. **CE-NAM-6**. (conformance: `invalid/nam-104-global-var.card`)

```text
var counter: u32;
```

*Invalid:* combined qualifiers. **CE-NAM-6**. (conformance: `invalid/nam-105-combined-qualifiers.card`)

```text
persistent var value: u32;
```

*Invalid:* a storage keyword inside a function. **CE-NAM-7**. (conformance: `invalid/nam-106-local-storage-keyword.card`)

```text
function process() {
    session ready: bool;
    return Ok();
}
```

*Invalid:* local `const`, which is deferred. **CE-NAM-7**. (conformance: `invalid/nam-107-local-const.card`)

```text
function process() {
    const step: u32 = 1;
    return Ok();
}
```

*Invalid:* a function declared inside a function. **CE-SYN-1**. (conformance: `invalid/nam-108-nested-function.card`)

```text
function outer() {
    function inner() {
        return Ok();
    }
    return Ok();
}
```

*Invalid:* there is no import or module syntax (NAM-8). **CE-SYN-1**. (conformance: `invalid/nam-122-application-wrapper.card`)

```text
import card;

const A: u32 = 1;
```

## 3.3 The application scope

**NAM-11 [Agreed]** All top-level declarations of an application share one *application scope*, regardless of kind or source file. Two declarations with the same name in the application scope are **CE-NAM-1**, even if they are of different kinds or in different files. A later declaration never replaces an earlier one. Names are case-sensitive.
*Sources: D-045; DN §4.1, §4.2.*

**NAM-12 [Agreed]** CardLang has no function overloading. Two functions with the same name are duplicates under NAM-11, even if their parameter lists differ.
*Sources: D-046; DN §3.7, §4.2.*

**NAM-13 [Agreed]** Every top-level declaration is visible throughout the application: before and after its position in its own file, and in every other file. Functions and types may therefore be used before they are declared. Visibility does not grant access. Constants, read-only parameters and references keep their own restrictions (chapters 5 and 8). Visibility also exposes nothing to the host: only the `command` is host-callable (chapter 12).
*Sources: D-038, D-314; DN §4.1, §4.2.*

**NAM-14 [Agreed]** The following *predeclared names* are part of every application scope, exactly as if they were declared there:

1. the primitive type names `u8`, `u16`, `u32`, `i8`, `i16`, `i32` and `bool` (chapter 4);
2. the compiler intrinsics `fill`, `convert`, `checked_convert`, `checked_add`, `checked_sub`, `checked_mul`, `checked_div`, `checked_rem`, `checked_neg`, `wrapping_add`, `wrapping_sub`, `wrapping_mul`, `truncate`, `encode_be`, `encode_le`, `decode_be` and `decode_le` (chapter 6; the last five added by D-432);
3. the platform names `card` (the root of platform API paths, NAM-18) and `CardError` (the platform error set, chapter 9);
4. the configuration structures, algorithm enums and other names the platform specification supplies (Annex B);
5. the lifecycle-handler names, currently the placeholders `on_install` and `on_power_on` (chapter 10; added by D-422 and D-438).

Declaring a top-level name that equals a predeclared name is **CE-NAM-5**. The one exception is a lifecycle-handler name: an application may declare a `function` with that name, and doing so defines the handler (STA-7). Declaring anything else with a handler name is still CE-NAM-5. Using one as a parameter, local or binding name is shadowing and therefore **CE-NAM-3** (NAM-21). Platform-supplied structures and enums follow all ordinary rules for structures and enums. They introduce no imports, namespaces or hidden fields.
*Sources: D-044, D-201, D-319, D-404 (OI-4), D-425 (OI-25), D-432 (OI-32), D-422 (OI-22), D-438 (OI-38); DN §4.1, §4.2, §11.1.*

### Examples

*Valid:* use before declaration. A function calls a later function, and a constant uses a later structure type. (conformance: `valid/nam-001-shared-scope-forward-use.card`)

```text
function run() -> u32 {
    return prepare();
}

function prepare() -> u32 {
    return Ok(INITIAL.value);
}

const INITIAL: Measurement = Measurement { value: 10, valid: true };

struct Measurement {
    value: u32;
    valid: bool;
}
```

*Valid (three files):* declarations used across files. The test must pass for every order of its file list. (conformance: `valid/nam-002-multi-file-any-order/`)

```text
// a.card
function total() -> u32 {
    var base: u32 = attempt base_value();
    return Ok(base + EXTRA);
}
```

```text
// b.card
function base_value() -> u32 {
    return Ok(BASE);
}
```

```text
// c.card
const BASE: u32 = 32;
const EXTRA: u32 = BASE * 2;
```

*Valid:* a file containing only comments, alongside a normal file. (conformance: `valid/nam-006-empty-file/`)

*Invalid:* the same name for a type and a global. **CE-NAM-1**. (conformance: `invalid/nam-101-duplicate-across-kinds.card`)

```text
struct Account {
    balance: u32;
}

persistent Account: u32;
```

*Invalid:* the same function declared in two files. **CE-NAM-1**. (conformance: `invalid/nam-102-duplicate-across-files/`)

*Invalid:* overloading. **CE-NAM-1**. (conformance: `invalid/nam-103-overloading.card`)

```text
function check(value: u32) {
    return Ok();
}

function check(value: u8) {
    return Ok();
}
```

*Invalid:* redeclaring an intrinsic. **CE-NAM-5**. (conformance: `invalid/nam-116-redeclare-intrinsic.card`)

```text
function fill() {
    return Ok();
}
```

*Invalid:* redeclaring the platform root. **CE-NAM-5**. (conformance: `invalid/nam-117-redeclare-card.card`)

```text
const card: u32 = 1;
```

*Invalid:* redeclaring a primitive type name. **CE-NAM-5**. (conformance: `invalid/nam-118-redeclare-primitive.card`)

```text
struct u8 {
    value: u32;
}
```

## 3.4 Member scopes and dotted names

**NAM-15 [Agreed]** Each owner has its own member scope:

- each structure, for its fields;
- each enum, for its variants;
- each error set, including the platform's `CardError`, for its members.

Two members with the same name in one owner are **CE-NAM-8**. Different owners may reuse member names. A member name may also equal a name in the application scope, because members are never looked up as bare names (NAM-16, NAM-17).
*Sources: D-047; DN §3.11, §4.2.*

**NAM-16 [Agreed]** Enum variants and error-set members are always written qualified, as `Owner.Member`, everywhere, including inside the application that declares them. A bare variant or member name never denotes the variant or member. It is resolved as an ordinary name under §3.5, so it refers to whatever the application scope or a lexical scope binds under that name. If nothing is bound under that name, it is **CE-NAM-2**. A qualified name whose owner exists but has no such member is **CE-NAM-9**.
*Sources: D-047, D-318; DN §3.11, §4.2, §6.3.*

**NAM-17 [Agreed]** A dotted form `X.Y` is resolved by what its first segment `X` resolves to:

1. If `X` names an enum or an error set (including `CardError`), `X.Y` is a qualified member under NAM-16.
2. If `X` is the predeclared root `card`, the whole dotted chain `card.Y…` is a platform name under NAM-18.
3. Otherwise `X` must denote a value, and each `.Y` is resolved from the type of the value to its left (chapter 6). For a structure, `.Y` is a field. For an array, `.length` is its element count.

Because every top-level name is unique (NAM-11), exactly one case applies. Field names never become bare names: an instance being in scope does not make its fields visible as names.
*Sources: D-047, D-317, D-406 (OI-6); DN §4.2.*

**NAM-18 [Agreed]** The root `card` followed by one or more `.Identifier` segments names an entry in the platform API catalog. It is never a field access, and `card` alone is not a value. A path that does not name an entry in the catalog is **CE-NAM-10**. The catalog, including which paths exist and what they denote, is platform-defined (Annex B).
*Sources: D-406 (OI-6); DN §4.1, §11.2.*

### Examples

*Valid:* reused field and variant names, and a field named `length`. (conformance: `valid/nam-003-member-scopes.card`)

```text
struct Account {
    balance: u32;
    length: u32;
}

struct Summary {
    balance: u32;
}

enum OperationState {
    Idle;
    Receiving;
}

enum ConnectionState {
    Idle;
    Connected;
}

session state: OperationState;
session link: ConnectionState;

function reset_states() {
    state = OperationState.Idle;
    link = ConnectionState.Idle;
    return Ok();
}
```

*Valid:* qualified members whose names equal top-level constants. (conformance: `valid/nam-005-qualified-members.card`)

```text
errors WalletError {
    InsufficientFunds = 1;
}

const InsufficientFunds: u16 = 7;

enum OperationState {
    Idle;
    Receiving;
}

const Receiving: bool = true;
session state: OperationState;

function start() {
    state = OperationState.Receiving;
    return Ok();
}

function refuse() {
    return Err(WalletError.InsufficientFunds);
}
```

*Invalid:* a duplicate field. **CE-NAM-8**. (conformance: `invalid/nam-113-duplicate-field.card`)

```text
struct Account {
    balance: u32;
    balance: u32;
}
```

*Invalid:* a bare variant name. **CE-NAM-2**. (conformance: `invalid/nam-114-bare-variant.card`)

```text
enum OperationState {
    Idle;
    Receiving;
}

session state: OperationState;

function reset_state() {
    state = Idle;
    return Ok();
}
```

*Invalid:* an unknown error member. **CE-NAM-9**. (conformance: `invalid/nam-115-unknown-member.card`)

```text
errors WalletError {
    InsufficientFunds = 1;
}

function refuse() {
    return Err(WalletError.Missing);
}
```

*Invalid:* a platform path that is not in the catalog. **CE-NAM-10**. The test assumes the catalog has no service with this name. (conformance: `invalid/nam-120-unknown-platform-path.card`)

```text
function use_platform() {
    attempt card.no_such_service.no_such_operation();
    return Ok();
}
```

## 3.5 Lexical scopes and visibility

**NAM-19 [Agreed]** The lexical scopes are:

- **Parameters:** the parameters of a function or command are in scope throughout its body.
- **Blocks:** each block `{ … }` is a scope. A local declared in it is in scope from the point given by NAM-20 to the end of that block.
- **`for` loops:** the index binding of a `for` loop is in scope in the loop body only.
- **Match arms:** a pattern binding is in scope in its match arm only.

Scopes nest: a block inside another block is inside that block's scope.
*Sources: D-048; DN §3.6, §4.2.*

**NAM-20 [Agreed]** A local variable becomes visible only after its initializer has completed. A local without an initializer becomes visible at the end of its declaration. Before that point, including inside its own initializer, its name does not refer to it.
*Sources: D-048; DN §3.6, §4.2.*

**NAM-21 [Agreed]** A parameter, local variable, `for` index or pattern binding must not have the same name as any name visible at its declaration. Visible names include top-level declarations, predeclared names, and parameters, locals and bindings of enclosing scopes. Such shadowing is **CE-NAM-3**. Two of these names declared in the same scope are **CE-NAM-4**. Scopes that do not nest, such as the two branches of an `if`, may reuse a name.
*Sources: D-315; DN §3.6, §3.7, §4.2.*

**NAM-22 [Agreed]** Every use of a bare name must resolve to a visible declaration: a lexical-scope name, else a name in the application scope. A name that resolves to nothing is **CE-NAM-2**. This includes a local used before it is visible (NAM-20), and a local used after its scope has ended.
*Sources: D-048; DN §3.6, §4.2.*

### Examples

*Valid:* the same local name in sibling scopes (DN §4.2). (conformance: `valid/nam-004-sibling-scopes.card`)

```text
function choose(condition: bool) -> u32 {
    if condition {
        var temporary: u32 = 1;
        return Ok(temporary);
    } else {
        var temporary: u32 = 2;
        return Ok(temporary);
    }
}
```

*Invalid:* a parameter that shadows a global (DN §4.2). **CE-NAM-3**. (conformance: `invalid/nam-109-parameter-shadows-global.card`)

```text
struct Account {
    balance: u32;
}

persistent account: Account;

function inspect(account: ref Account) -> u32 {
    return Ok(account.balance);
}
```

*Invalid:* an inner local that shadows an outer local. **CE-NAM-3**. (conformance: `invalid/nam-110-local-shadows-local.card`)

```text
function process() {
    var count: u32 = 1;
    if true {
        var count: u32 = 2;
    }
    return Ok();
}
```

*Invalid:* a parameter named like a predeclared type. **CE-NAM-3**. (conformance: `invalid/nam-121-parameter-shadows-primitive.card`)

```text
function check(u8: u32) {
    return Ok();
}
```

*Invalid:* a local that refers to itself in its own initializer (DN §4.2). **CE-NAM-2**. (conformance: `invalid/nam-111-self-reference.card`)

```text
function advance() {
    var next: u32 = next + 1;
    return Ok();
}
```

*Invalid:* a local used after its block has ended. **CE-NAM-2**. (conformance: `invalid/nam-112-use-outside-scope.card`)

```text
function outside() -> u32 {
    if true {
        var inner: u32 = 1;
    }
    return Ok(inner);
}
```

*Invalid:* two locals with the same name in one block. **CE-NAM-4**. (conformance: `invalid/nam-119-same-scope-duplicate.card`)

```text
function duplicate() {
    var value: u32 = 1;
    var value: u32 = 2;
    return Ok();
}
```

## 3.6 Errors defined in this chapter

| Class | Meaning | Rules |
|---|---|---|
| **CE-NAM-1** | Two declarations in the application scope have the same name | NAM-11, NAM-12 |
| **CE-NAM-2** | A name does not resolve | NAM-16, NAM-20, NAM-22 |
| **CE-NAM-3** | A parameter, local, `for` index or pattern binding shadows a visible name | NAM-14, NAM-21 |
| **CE-NAM-4** | Two parameters, locals or bindings in one scope have the same name | NAM-21 |
| **CE-NAM-5** | A top-level declaration uses a predeclared name | NAM-14, STA-8 |
| **CE-NAM-6** | A top-level value declaration does not have exactly one of `persistent`, `session` or `const` | NAM-9 |
| **CE-NAM-7** | A value declaration inside a body has a keyword other than `var` | NAM-10 |
| **CE-NAM-8** | Two members of one structure, enum or error set have the same name | NAM-15 |
| **CE-NAM-9** | A qualified name's owner has no member of that name | NAM-16 |
| **CE-NAM-10** | A `card.` path is not in the platform API catalog | NAM-18 |