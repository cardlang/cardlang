# SP2 — Program structure and names: detailed sub-plan

Parent: `plans_and_notes/specification-plan-of-plans.md`
Status: draft for review. Chapter 3 is not written until you approve this plan.

## 1. Scope

| Output | Content |
|---|---|
| `spec/03-program-structure-and-names.md` | Applications and compilation units; source files; the kinds of top-level declaration and where declarations may appear; the shared application scope; owner-specific member scopes; lexical scopes and visibility; no shadowing; reserved names; platform names |
| `spec/annex-A-grammar.md` §A.2.1 | `SourceFile`, `TopLevelDeclaration` and the outer shape of each declaration kind. The inner parts (types, expressions, bodies, members) are named as nonterminals and filled in by later sub-plans |
| `conformance/valid/nam-*`, `conformance/invalid/nam-*` | One test per chapter example |
| Register, Annex C, Annex D, 00-index | Body decisions D-313…, new issues, rule coverage, and the CE-NAM index |

**Out of scope:**

- What each declaration *means* (types, constants, functions, state, errors, the entry point): chapters 4–12. Chapter 3 only says which declarations exist, where they may appear, and how their names are resolved.
- Rejecting initializers on `persistent`/`session` declarations (D-122): chapter 10 (SP9).
- The order in which constants are evaluated, and dependency cycles: chapter 5 (SP4).
- Field lookup on a value (`account.balance`, `.length`): chapter 6 (SP5). Chapter 3 states only the principle that dot access is resolved from the receiver's type.
- Lifecycle-handler names (OI-22): chapter 10 (SP9).

## 2. Sources

- **DN sections:** §3.0 (source files), §3.6 (blocks, scope, no shadowing), §3.7 (top-level functions, no overloading or nesting), §3.11 (enum variants are always qualified), §4.1, §4.2, §5.1, §6.3 (error members are qualified; `CardError`), §11.1 (platform-supplied declarations).
- **Decisions:**
  - D-003 and D-007: global value declaration keywords, and none inside functions.
  - D-020: application isolation.
  - D-021 and D-022: the file list; complete top-level declarations in each file.
  - D-038 to D-040: visibility across files; no modules; file order is irrelevant.
  - D-044 to D-048: reserved names, the shared scope, no overloading or local definitions, owner scopes, visibility after the initializer completes.
  - D-201: platform-supplied declarations.
  - D-404: the declaration ban for reserved names (the rest of D-404 is done in SP1).
  - D-406: the `card.` path.

### 2.1 Body-only decisions to register (D-313…)

| ID | Decision | Source |
|---|---|---|
| D-313 | A declaration cannot span source files | DN §3.0 |
| D-314 | Functions and types may be used before their declaration, including across files | DN §4.1, §4.2 |
| D-315 | Shadowing any visible name is forbidden: application declarations, parameters, locals, loop and pattern bindings. Duplicates in the same scope are errors. Names may be reused in sibling scopes | DN §3.6, §4.2 |
| D-316 | Function, command, structure, enum and error-set declarations are top-level only | DN §4.2 |
| D-317 | Field names never become bare names. Dot access resolves from the receiver's type | DN §4.2 |
| D-318 | Enum variants and error members are always qualified (`Owner.Member`) and are never imported as bare names | DN §3.11, §4.2, §6.3 |
| D-319 | Platform-supplied configuration structures and algorithm enums use the ordinary naming rules, with no imports, namespaces or private fields | DN §11.1 |
| D-320 | Plain `var`, and combined qualifiers such as `persistent var` or `session const`, are forbidden at application scope. There is no `local` keyword | DN §5.1 |

## 3. Approach: permissive grammar, specific errors

Some restrictions could be written either as grammar or as chapter rules. Examples: `var` at top level, combined storage keywords, and storage keywords inside a function. **I propose writing these as chapter rules with their own error classes, not as grammar.** The grammar accepts a slightly larger language. Then the rule rejects the program with an error class that names the actual mistake, instead of the generic CE-SYN-1. The design notes list these as distinct named errors (DN §5.1 "Invalid examples").

This covers storage keywords on value declarations, at top level and inside blocks. Declarations of other kinds inside blocks (a nested `function`, `struct`, `enum` or `errors`) are left out of the statement grammar, so they are CE-SYN-1. That is enough to show they are forbidden (D-046, D-316).

Global value declarations take this shape:

```
GlobalValueDeclaration ::= StorageKeyword+ Identifier ':' Type ( '=' Expression )? ';'
StorageKeyword         ::= 'persistent' | 'session' | 'const' | 'var'
```

The grammar accepts any combination. Rules then require exactly one of `persistent`, `session` or `const` (NAM-9, NAM-10). An initializer is required on `const` and forbidden on the others (chapter 5 and chapter 10).

## 4. Planned rules (chapter 3)

**§3.1 Applications and compilation units**

- **NAM-1** An application is compiled from the build-supplied, ordered list of source files, together with a build-supplied application identity. These are one compilation unit. The build-configuration format is outside the language (D-021).
- **NAM-2** Each file must derive `SourceFile` on its own. A declaration cannot begin in one file and continue in another (CE-SYN-1; D-313, D-022). A file may contain no declarations at all.
- **NAM-3** File-list constraints [Open → OI-26]: whether listing the same file twice, or an empty list, is permitted.
- **NAM-4** The order of the file list, and the order of declarations within and across files, never affects name resolution or program meaning (D-040, D-314). Constant evaluation order is handled in chapter 5.
- **NAM-5** Isolation: no name in an application refers to anything in another application. There are no cross-application names, imports, calls or shared state (D-020).

**§3.2 Top-level declarations**

- **NAM-6** The kinds of top-level declaration are: global value (`persistent`, `session`, `const`), `function`, `command`, `struct`, `enum` and `errors` (DN §4.2). The A.2.1 grammar defines their outer shape.
- **NAM-7** Functions, commands, structures, enums and error sets are top-level only (D-316, D-046). Inside a block they are CE-SYN-1.
- **NAM-8** There is no application wrapper, module, namespace, import, export, class or access modifier (D-022, D-039).
- **NAM-9** A global value declaration has exactly one storage keyword, and it must be `persistent`, `session` or `const`. Plain `var` at top level is **CE-NAM-7**. A combination such as `persistent var` or `session const` is also **CE-NAM-7** (D-003, D-320).
- **NAM-10** Inside a function or command, a value declaration uses `var` alone. `persistent`, `session` or `const` there is **CE-NAM-8** (D-006, D-007).

**§3.3 The application scope**

- **NAM-11** All top-level declarations share one application-wide scope, whatever their kind and whichever file they are in. Two declarations with the same name are **CE-NAM-1**. This applies across kinds too: a structure and a global cannot share a name. Names are case-sensitive (D-045).
- **NAM-12** No overloading: two functions with the same name are a duplicate under NAM-11, even if their parameter types differ (D-046).
- **NAM-13** Every top-level declaration is visible throughout the application, before and after its position and in every file (D-038, D-314).
- **NAM-14** Predeclared names occupy the application scope as if declared there, and cannot be declared again (**CE-NAM-6**). They are:
  - the primitive type names [Open → OI-25];
  - the reserved identifiers of LEX-15 (intrinsics, `card`, `CardError`);
  - the platform-supplied declarations, such as configuration structures and algorithm enums (D-319, D-201);
  - any further platform-reserved names (D-044, D-404).

**§3.4 Member scopes and qualified names**

- **NAM-15** Each structure has its own field scope. Each enum has its own variant scope. Each error set, including the platform's `CardError`, has its own member scope. Duplicates inside one owner are **CE-NAM-9**. The same member name may appear in different owners, and may match top-level names (D-047).
- **NAM-16** Enum variants and error members are written qualified, as `Owner.Member`. A bare variant or member name is resolved as an ordinary name, so it fails unless something else has that name (D-318). An unknown member in a qualified name is **CE-NAM-10**.
- **NAM-17** Resolving `X.Y`:
  - If `X` resolves to an enum or error-set declaration, `X.Y` is a qualified member under NAM-16.
  - If `X` is the reserved root `card`, `X.Y…` is a platform name under NAM-18.
  - Otherwise `X` must be a value, and `.Y` is resolved from that value's type (chapter 6).

  Field names never become bare names (D-317).
- **NAM-18** `card` followed by one or more `.Identifier` segments names an entry in the platform API catalog. It is never a field access. A path that is not in the catalog is **CE-NAM-11**. The catalog itself is platform-defined (Annex B) (D-406).

**§3.5 Lexical scopes and visibility**

- **NAM-19** Lexical scopes:
  - a function's or command's parameters cover its whole body;
  - each block `{ … }` is a scope;
  - a `for` index is local to the loop body;
  - a pattern binding is local to its match arm.

  (D-048; DN §3.6, §4.2.)
- **NAM-20** A local becomes visible only after its initializer completes, and stays visible to the end of its enclosing block. A use before that point, including inside its own initializer, does not resolve to it. An unresolvable name is **CE-NAM-2** (D-048).
- **NAM-21** A parameter, local, `for` index or pattern binding must not have the name of any visible declaration: a top-level declaration, a predeclared name, or a parameter, local or binding in an enclosing scope. Doing so is **CE-NAM-3**. Two such names in the same scope are **CE-NAM-4**. Sibling scopes may reuse a name (D-315).
- **NAM-22** Every use of a name must resolve under these rules. Otherwise it is **CE-NAM-2**.

**§3.6 Error classes**

| Class | Meaning |
|---|---|
| CE-NAM-1 | Duplicate top-level name |
| CE-NAM-2 | Unresolved name |
| CE-NAM-3 | Shadowing |
| CE-NAM-4 | Duplicate name in one lexical scope |
| CE-NAM-5 | Unused: kept free (see note) |
| CE-NAM-6 | Declaring a reserved or predeclared name |
| CE-NAM-7 | Bad global storage keyword |
| CE-NAM-8 | Storage keyword inside a function or command |
| CE-NAM-9 | Duplicate member within an owner |
| CE-NAM-10 | Unknown qualified member |
| CE-NAM-11 | Unknown platform path |

Note: if the CE-NAM-5 slot is still unused when the chapter is drafted, the classes are renumbered so there is no gap. Error-class IDs only become stable once the chapter is drafted.

## 5. New open issues

| ID | Question | Recommendation |
|---|---|---|
| **OI-25** Primitive type names | The names `u8 u16 u32 i8 i16 i32 bool` are not keywords (the agreed keyword list, D-404, omits them). Can an application declare something called `u8` or `bool`, for example a struct or a constant? | No. Make them predeclared type names in the application scope, so declaring them is CE-NAM-6 and shadowing them is CE-NAM-3. They stay lexically identifiers, so the agreed keyword list is unchanged |
| **OI-26** Build file-list constraints | (1) The same file listed twice in the build file list. (2) An empty file list | (1) A build-configuration error, outside the language. Without that rule it would usually show up as CE-NAM-1 duplicates anyway. (2) Allowed by the language. It fails because there is no `command` (chapter 12) |

**Decided 2026-11-15:** you accepted both recommendations. Step 1 records them as D-425 and D-426. NAM-3 and NAM-14 are therefore written as **[Agreed]**, and `invalid/nam-118-redeclare-primitive.card` has status `agreed`.

## 6. Grammar (Annex A §A.2.1)

```
SourceFile              ::= TopLevelDeclaration*
TopLevelDeclaration     ::= GlobalValueDeclaration | FunctionDeclaration | CommandDeclaration
                          | StructDeclaration | EnumDeclaration | ErrorSetDeclaration
GlobalValueDeclaration  ::= StorageKeyword+ Identifier ':' Type ( '=' Expression )? ';'
StorageKeyword          ::= 'persistent' | 'session' | 'const' | 'var'
StructDeclaration       ::= 'struct' Identifier '{' FieldDeclaration* '}'
FieldDeclaration        ::= Identifier ':' Type ';'
EnumDeclaration         ::= 'enum' Identifier '{' ( Identifier ';' )* '}'
ErrorSetDeclaration     ::= 'errors' Identifier '{' ErrorMember* '}'
ErrorMember             ::= Identifier '=' Expression ';'
FunctionDeclaration     ::= 'function' Identifier ParameterList ReturnType? Block   /* A.2.6 */
CommandDeclaration      ::= 'command'  Identifier ParameterList ReturnType? Block   /* A.2.10 */
QualifiedName           ::= Identifier '.' Identifier
PlatformName            ::= 'card' ( '.' Identifier )+
```

Notes on this grammar:

- `card` is a reserved identifier (LEX-15), not a keyword. In `PlatformName` it stands for the identifier token with that spelling.
- `Type`, `Expression`, `ParameterList`, `ReturnType` and `Block` are defined by SP3–SP7.
- Empty structures and empty enums parse, and are rejected by chapter 4 (D-066, D-067). This again follows §3: the grammar accepts them so the chapter can give a specific error.
- `CommandDeclaration` has the same outer shape as `FunctionDeclaration`. Chapter 12 fixes the exact signature.

## 7. Examples and conformance tests

Unmarked tests use `kind: fragment`.

**Valid**

| Test | Shows |
|---|---|
| `valid/nam-001-shared-scope-forward-use.card` | A function calls a function declared later, and a constant's type uses a struct declared later |
| `valid/nam-002-multi-file-any-order/` | Three files using each other's declarations. Must pass for every order of `files.txt` |
| `valid/nam-003-member-scopes.card` | Two structs with a `balance` field; two enums with an `Idle` variant; a field named `length` |
| `valid/nam-004-sibling-scopes.card` | The same local name in the `if` and `else` blocks (DN §4.2 example) |
| `valid/nam-005-qualified-members.card` | `OperationState.Receiving` and `WalletError.InsufficientFunds` used where an error-set member name equals a const name |
| `valid/nam-006-empty-file/` | One file containing only a comment, alongside a normal file |

**Invalid**

| Test | Expected error | Shows |
|---|---|---|
| `invalid/nam-101-duplicate-across-kinds.card` | CE-NAM-1 | `struct Account` and `persistent Account: u32;` (DN §4.2) |
| `invalid/nam-102-duplicate-across-files/` | CE-NAM-1 | The same function declared in two files |
| `invalid/nam-103-overloading.card` | CE-NAM-1 | Two functions `f` with different parameters |
| `invalid/nam-104-global-var.card` | CE-NAM-7 | `var counter: u32;` at top level |
| `invalid/nam-105-combined-qualifiers.card` | CE-NAM-7 | `persistent var value: u32;` |
| `invalid/nam-106-local-storage-keyword.card` | CE-NAM-8 | `session ready: bool;` inside a function |
| `invalid/nam-107-local-const.card` | CE-NAM-8 | `const step: u32 = 1;` inside a function |
| `invalid/nam-108-nested-function.card` | CE-SYN-1 | A `function` inside a function body |
| `invalid/nam-109-parameter-shadows-global.card` | CE-NAM-3 | Parameter `account` when a global `account` exists (DN §4.2) |
| `invalid/nam-110-local-shadows-local.card` | CE-NAM-3 | An inner-block `var` with the same name as an outer one |
| `invalid/nam-111-self-reference.card` | CE-NAM-2 | `var next: u32 = next + 1;` (DN §4.2) |
| `invalid/nam-112-use-outside-scope.card` | CE-NAM-2 | A local used after its block ends |
| `invalid/nam-113-duplicate-field.card` | CE-NAM-9 | A struct with two `balance` fields |
| `invalid/nam-114-bare-variant.card` | CE-NAM-2 | `state = Idle;` without qualification |
| `invalid/nam-115-unknown-member.card` | CE-NAM-10 | `WalletError.Missing` |
| `invalid/nam-116-redeclare-intrinsic.card` | CE-NAM-6 | `function fill() { … }` |
| `invalid/nam-117-redeclare-card.card` | CE-NAM-6 | `const card: u32 = 1;` |
| `invalid/nam-118-redeclare-primitive.card` | CE-NAM-6 | `struct u8 { … }`. Status `open` until OI-25 is decided |
| `invalid/nam-119-same-scope-duplicate.card` | CE-NAM-4 | Two `var x` declarations in one block |

These tests use types, statements and expressions that later chapters define. Each test uses only constructs whose syntax the notes give as agreed, so no test relies on undecided syntax. A test's validity is re-checked when SP3–SP11 draft their chapters.

## 8. Steps

1. Register D-313…D-320, add OI-25 and OI-26 to Annex C, and record your decisions on them.
2. Write chapter 3: rules, grammar fragments and examples.
3. Fill in Annex A §A.2.1.
4. Write the 25 conformance tests.
5. Update Annex D (D-003, D-007, D-020–D-022, D-038–D-040, D-044–D-048, D-201, D-313–D-320, D-404, D-406), the 00-index (status, CE-NAM index, rule counts) and the register's "Implemented by" column.
6. Run the exit checklist. Extend the scratchpad reference lexer into a small name-resolution checker where that is practical, and run it over the tests and the DN examples. At minimum, check that the tests tokenize and that every name they use is declared.

## 9. Exit checklist

- Every NAM rule has a tag and a sources line. Every [Open] rule cites OI-25 or OI-26.
- The A.2.1 productions derive every top-level declaration shape that appears in DN code blocks. Check by a manual walk plus a scripted scan for the leading keyword.
- Every example has a test, and every test's rule IDs and error classes exist.
- Every DN §5.1 and §4.2 invalid example maps to a CE-NAM or CE-SYN class.
- Annex D and the register are updated. Nothing in chapter 3 decides types, values or evaluation.

## 10. Choices made in this sub-plan

These are open for redirection:

- The permissive-grammar approach (§3).
- Predeclared names, including platform-supplied declarations, behave as declarations in the application scope (NAM-14).
- `X.Y` resolves by what `X` is (NAM-17). This works because there is one shared scope.
- Bare enum variants and error members are ordinary unresolved names (CE-NAM-2), not a special error class.
- Error-class numbers are only fixed when the chapter is drafted.
