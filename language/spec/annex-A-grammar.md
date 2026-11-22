# Annex A — Grammar

CardLang Language Specification, Draft 0.2.

The grammar has been checked mechanically against every conformance test (§A.3).

The notation is defined in chapter 1 §1.7.1. This annex is normative for the *form* of programs. The chapters are normative for their meaning and for every restriction the grammar does not express. The grammar fragments in the chapters are copies of the productions here. If a fragment and this annex disagree, that is a specification error to be reported, not a choice between the two.

## A.0 Syntax errors

**CE-SYN-1** A source file that tokenizes successfully (chapter 2) but whose token sequence has no derivation from `SourceFile` (§A.2) is a compilation error of class CE-SYN-1. An implementation reports CE-SYN-1 only when no more specific class applies. For example, a rule written as a chapter restriction rather than a grammar production uses that chapter's class.

## A.1 Lexical grammar

The lexical grammar describes how one source file is divided into tokens. Tokens are formed by longest match (LEX-10). Each file is processed separately (LEX-11).

```
/* A.1.1 Source text (LEX-2 to LEX-6) */
SourceText      ::= ByteOrderMark? ( Whitespace | Comment | Token )*
ByteOrderMark   ::= #xFEFF
Whitespace      ::= #x20 | #x09 | LineBreak
LineBreak       ::= #x0D #x0A | #x0D | #x0A

/* A.1.2 Comments (LEX-7 to LEX-9) */
Comment         ::= LineComment | BlockComment
LineComment     ::= '//' [^#x0A#x0D]*
BlockComment    ::= '/*' ( [^*] | '*'+ [^*/] )* '*'+ '/'

/* A.1.3 Tokens (LEX-10) */
Token           ::= Identifier | Keyword | Underscore | IntegerLiteral | ByteStringLiteral | Punctuator

/* A.1.4 Identifiers and keywords (LEX-12 to LEX-16) */
Identifier      ::= ( IdentStart IdentChar* ) - ( Keyword | '_' )
IdentStart      ::= [A-Za-z_]
IdentChar       ::= [A-Za-z0-9_]
Underscore      ::= '_'
Keyword         ::= 'abort' | 'and' | 'attempt' | 'break' | 'command' | 'const'
                  | 'continue' | 'else' | 'enum' | 'Err' | 'errors' | 'false'
                  | 'for' | 'function' | 'if' | 'in' | 'inout' | 'match' | 'not'
                  | 'Ok' | 'or' | 'persistent' | 'ref' | 'require' | 'return'
                  | 'session' | 'struct' | 'transaction' | 'true' | 'var' | 'while'
                  | 'wipe' | 'ignore'

/* A.1.5 Integer and Boolean literals (LEX-17 to LEX-21) */
IntegerLiteral  ::= DecimalLiteral | HexLiteral | BinaryLiteral
DecimalLiteral  ::= Digit ( '_'? Digit )*
HexLiteral      ::= '0x' HexDigit ( '_'? HexDigit )*
BinaryLiteral   ::= '0b' BinDigit ( '_'? BinDigit )*
Digit           ::= [0-9]
HexDigit        ::= [0-9a-fA-F]
BinDigit        ::= [01]
NumericRun      ::= Digit [A-Za-z0-9_]*      /* must wholly match IntegerLiteral (LEX-18) */
BooleanLiteral  ::= 'true' | 'false'         /* keywords; listed for reference */
ByteStringLiteral ::= 'b"' ( ByteChar | '\"' | '\\' | '\x' HexDigit HexDigit )* '"'   /* LEX-25 */
ByteChar        ::= [#x20-#x7E] - ( '"' | '\' )

/* A.1.6 Punctuators (LEX-22) */
Punctuator      ::= '{' | '}' | '(' | ')' | '[' | ']' | ';' | ':' | ',' | '.' | '..'
                  | '->' | '=>' | '=' | '==' | '!=' | '<' | '<=' | '>' | '>='
                  | '+' | '-' | '*' | '/' | '%' | '~' | '&' | '|' | '^' | '<<' | '>>'
                  | '+=' | '-=' | '*=' | '/=' | '%=' | '&=' | '|=' | '^=' | '<<=' | '>>='
```

Lexical errors are CE-LEX-1 to CE-LEX-5 (chapter 2 §2.8).

## A.2 Syntactic grammar

The syntactic grammar works on the token sequence of each file. Whitespace and comments never appear in it. In syntactic productions, quoted strings stand for the keyword or punctuator token with that spelling. `Identifier` and `IntegerLiteral` refer to the token classes of §A.1.

### A.2.1 Source files and top-level declarations (chapter 3)

```
SourceFile             ::= TopLevelDeclaration*
TopLevelDeclaration    ::= GlobalValueDeclaration | FunctionDeclaration | CommandDeclaration
                         | StructDeclaration | EnumDeclaration | ErrorSetDeclaration
GlobalValueDeclaration ::= StorageKeyword+ Identifier ':' Type ( '=' Expression )? ';'
StorageKeyword         ::= 'persistent' | 'session' | 'const' | 'var'
StructDeclaration      ::= 'struct' Identifier '{' FieldDeclaration* '}'
FieldDeclaration       ::= Identifier ':' Type ';'
EnumDeclaration        ::= 'enum' Identifier '{' ( Identifier ';' )* '}'
ErrorSetDeclaration    ::= 'errors' Identifier '{' ErrorMember* '}'
ErrorMember            ::= Identifier '=' Expression ';'
FunctionDeclaration    ::= 'function' Identifier ParameterList ReturnType? Block
CommandDeclaration     ::= 'command' Identifier ParameterList ReturnType? Block
```

Notes on these productions:

- **Deliberately permissive.** The grammar accepts some programs that chapter rules then reject with a specific compile-error class:
  - any combination of storage keywords (NAM-9, NAM-10);
  - an initializer on any global value declaration (chapters 5 and 10);
  - empty structures and enums (chapter 4);
  - a `command` with any signature (chapter 12).
- **Dotted names.** `Owner.Member`, `card.service.operation` and field access all parse as the member-access form of the expression grammar (§A.2.4). Chapter 3 (NAM-17) decides which meaning a dotted form has, from what its first segment resolves to. The grammar does not distinguish them.
- **Later sections.** `Type` is defined in §A.2.2, `Expression` in §A.2.4, `Block` in §A.2.5, and `ParameterList` and `ReturnType` in §A.2.6.

### A.2.2 Types (chapter 4)

```
Type ::= Identifier ( '[' Expression? ']' )*
```

The identifier must denote a type (TYP-3). A suffix with an expression forms a fixed array type, whose length must be a constant expression (TYP-19). An empty suffix `[]` forms an unsized array type, which is allowed only as a `ref`/`inout` parameter type (TYP-21). More than one suffix is rejected by TYP-18. The structure and enum declaration productions are in §A.2.1.

### A.2.3 Constant expressions (chapter 5)

Constant expressions have no grammar of their own. They are `Expression`s (§A.2.4) that satisfy the semantic restrictions of chapter 5 (CEX-3 to CEX-5). A position that requires a constant expression uses the ordinary `Expression` nonterminal. Examples are the initializer of a `const` declaration and an array length in `Type`.

### A.2.4 Expressions (chapter 6)

```
Expression        ::= UnaryExpression ( BinaryOperator UnaryExpression )*
BinaryOperator    ::= '+' | '-' | '*' | '/' | '%' | '==' | '!=' | '<' | '<=' | '>' | '>='
                    | 'and' | 'or' | '&' | '|' | '^' | '<<' | '>>'
UnaryExpression   ::= ( '-' | 'not' | '~' ) UnaryExpression
                    | 'attempt' PostfixExpression ( 'else' PostfixExpression )?
                    | PostfixExpression
PostfixExpression ::= PrimaryExpression PostfixPart*
PostfixPart       ::= '[' Expression ']'
                    | '[' Expression '..' Expression ']'
                    | '.' Identifier
                    | Arguments
PrimaryExpression ::= IntegerLiteral | BooleanLiteral | ByteStringLiteral | Identifier
                    | '(' Expression ')'
                    | ArrayList
                    | StructConstructor
                    | TypeArgumentCall
ArrayList         ::= '[' ( Expression ( ',' Expression )* ','? )? ']'
StructConstructor ::= Identifier '{' ( FieldInit ( ',' FieldInit )* ','? )? '}'
FieldInit         ::= Identifier ':' Expression
TypeArgumentCall  ::= TypeArgumentIntrinsic '<' Type '>' Arguments
TypeArgumentIntrinsic ::= 'convert' | 'checked_convert' | 'truncate' | 'decode_be' | 'decode_le'
Arguments         ::= '(' ( Argument ( ',' Argument )* ','? )? ')'
Argument          ::= ( 'ref' | 'inout' )? Expression
ConditionExpression ::= ConditionUnary ( BinaryOperator ConditionUnary )*
ConditionUnary    ::= ( '-' | 'not' | '~' ) ConditionUnary
                    | 'attempt' ConditionPostfix ( 'else' ConditionPostfix )?
                    | ConditionPostfix
ConditionPostfix  ::= ConditionPrimary PostfixPart*
ConditionPrimary  ::= IntegerLiteral | BooleanLiteral | ByteStringLiteral | Identifier
                    | '(' Expression ')'
                    | ArrayList
                    | TypeArgumentCall
```

Notes on these productions:

- **Flat binary structure.** The binary operators have no precedence. A flat sequence is accepted, and EXP-2 to EXP-5 require a single operator per grouping level and forbid comparison chains (CE-EXP-4, CE-EXP-5).
- **Type-argument intrinsics.** The names in `TypeArgumentIntrinsic` are reserved identifiers (LEX-15), not keywords. Writing one followed by `<` always begins a type argument.
- **Constructors in conditions.** The condition of `if` and `while`, each `for` range bound, and the scrutinee of `match` use `ConditionExpression` (EXP-6, D-444). It is `Expression` without an unparenthesized `StructConstructor`, so in those positions `Identifier '{'` always begins the body. A parenthesized constructor, `'(' Expression ')'`, and constructors inside brackets or arguments are allowed.
- **Parsed but restricted.** Slices (`'..'` in an index bracket) and argument modes are parsed here. Chapter 8 restricts where they may appear.

### A.2.5 Statements and blocks (chapter 7)

```
Block               ::= '{' Statement* '}'
Statement           ::= VarStatement | AssignmentStatement | ExpressionStatement
                      | IfStatement | WhileStatement | ForStatement | MatchStatement
                      | BreakStatement | ContinueStatement | ReturnStatement | RequireStatement
                      | TransactionStatement | AbortStatement        /* A.2.9 */
                      | WipeStatement | IgnoreStatement
VarStatement        ::= StorageKeyword+ Identifier ':' Type ( '=' Expression )? ';'
AssignmentStatement ::= Expression ( '=' | CompoundOperator ) Expression ';'
CompoundOperator    ::= '+=' | '-=' | '*=' | '/=' | '%=' | '&=' | '|=' | '^=' | '<<=' | '>>='
WipeStatement       ::= 'wipe' Expression ';'
IgnoreStatement     ::= 'ignore' PostfixExpression ';'
ExpressionStatement ::= Expression ';'
IfStatement         ::= 'if' ConditionExpression Block ( 'else' 'if' ConditionExpression Block )* ( 'else' Block )?
WhileStatement      ::= 'while' ConditionExpression Block
ForStatement        ::= 'for' Identifier ':' Type 'in' ConditionExpression '..' ConditionExpression Block
MatchStatement      ::= 'match' ConditionExpression '{' MatchArm* '}'
MatchArm            ::= Pattern '=>' Block
Pattern             ::= 'Ok' '(' ( Identifier | '_' )? ')'
                      | 'Err' '(' ( Identifier | '_' | Identifier '.' Identifier | Identifier '(' ( Identifier | '_' ) ')' ) ')'
                      | Identifier '.' Identifier
                      | '_'
BreakStatement      ::= 'break' ';'
ContinueStatement   ::= 'continue' ';'
ReturnStatement     ::= 'return' ( 'Ok' '(' Expression? ')' | 'Err' '(' Expression ')' | Expression ) ';'
RequireStatement    ::= 'require' Expression 'else' Expression ';'
```

Notes on these productions:

- **Deliberately permissive.** Some forms parse so that a chapter rule can give a specific error:
  - any storage keywords in `VarStatement` (NAM-10);
  - any left side in `AssignmentStatement` (STM-7);
  - any `ExpressionStatement` (STM-2);
  - a `_` arm (STM-16, chapter 9).
- **What is absent.** There is no standalone block statement (STM-3) and no compound-assignment form (STM-6).
- **Range separator.** In `ForStatement`, `..` is the range separator. Both bounds are `ConditionExpression`s (§A.2.4), as are the conditions of `if` and `while` and the scrutinee of `match`.
- **Patterns.** `Pattern` covers both enum and outcome patterns. Chapter 9 gives meaning to the `Ok` and `Err` patterns, and §A.2.7 refers back here.

### A.2.6 Functions and parameters (chapter 8)

```
ParameterList       ::= '(' ( Parameter ( ',' Parameter )* ','? )? ')'
Parameter           ::= Identifier ':' ( 'ref' | 'inout' )? Type
ReturnType          ::= '->' Type
```

Notes on these productions:

- **Declarations.** `FunctionDeclaration` and `CommandDeclaration` are in §A.2.1.
- **Arguments and slices.** Call-site argument modes (`Argument`) and slices (the `'..'` form of `PostfixPart`) are in §A.2.4.
- **Restrictions from chapter 8.** Chapter 8 restricts where slices may appear (FUN-18), requires argument modes to match parameter modes (FUN-7), and restricts which arguments a reference may take (FUN-9, FUN-10).
- **Restriction from chapter 4.** An unsized `T[]` parameter type is allowed only with `ref` or `inout` (TYP-21).

### A.2.7 Outcomes, patterns and error sets (chapter 9)

This section adds no new productions. The relevant ones are defined elsewhere:

- `ErrorSetDeclaration` and `ErrorMember` are in §A.2.1.
- The `Ok` and `Err` forms of `Pattern` and `ReturnStatement` are in §A.2.5.
- `attempt` is in `UnaryExpression`, §A.2.4.

Chapter 9 restricts these productions as follows:

- `ErrorMember` accepts any `Expression` as its code, but OUT-16 requires an integer literal (CE-OUT-7).
- `Ok(…)` and `Err(…)` occur only in returns, `abort` and patterns (OUT-6).
- Nested patterns such as `Ok(State.Idle)` do not derive (CE-SYN-1).

### A.2.8 State declarations (chapter 10)

This section adds no new productions. `persistent` and `session` globals are `GlobalValueDeclaration`s (§A.2.1). Chapter 10 restricts them:

- they take no initializer (STA-2, CE-STA-1);
- lifecycle handlers are ordinary `FunctionDeclaration`s with reserved names and signatures (STA-7).

### A.2.9 Transactions (chapter 11)

```
TransactionStatement ::= 'transaction' Block
AbortStatement       ::= 'abort' 'Err' '(' Expression ')' ';'
```

Both productions are alternatives of `Statement` (§A.2.5). Chapter 11 restricts them by meaning, not by grammar:

- `return` and loop exits must not leave a transaction (TXN-6, CE-TXN-1); the error path of `attempt` and `require` aborts it (TXN-18);
- `abort` is valid only lexically inside a transaction (TXN-7, CE-TXN-2);
- transactions do not nest (TXN-10, CE-TXN-3).

### A.2.10 The host entry point (chapter 12)

This section adds no new productions. `CommandDeclaration` is in §A.2.1. Chapter 12 restricts it as follows:

- an application declares exactly one `command` (HEP-1, CE-HEP-1 and CE-HEP-2);
- its signature must be `(ref u8[], inout u8[]) -> u32` (HEP-2, CE-HEP-3);
- application code never calls it (HEP-3, CE-EXP-15).

## A.3 Nonterminal index and mechanical check

### A.3.1 Index

Every nonterminal of this annex, with the section that defines it. Each is defined exactly once.

| Nonterminal | Defined in |
|---|---|
| `AbortStatement` | §A.2.9 |
| `Argument` | §A.2.4 |
| `Arguments` | §A.2.4 |
| `ArrayList` | §A.2.4 |
| `AssignmentStatement` | §A.2.5 |
| `BinaryLiteral` | §A.1.5 |
| `BinaryOperator` | §A.2.4 |
| `BinDigit` | §A.1.5 |
| `Block` | §A.2.5 |
| `BlockComment` | §A.1.2 |
| `BooleanLiteral` | §A.1.5 |
| `BreakStatement` | §A.2.5 |
| `ByteChar` | §A.1.5 |
| `ByteOrderMark` | §A.1.1 |
| `ByteStringLiteral` | §A.1.5 |
| `CommandDeclaration` | §A.2.1 |
| `Comment` | §A.1.2 |
| `CompoundOperator` | §A.2.5 |
| `ConditionExpression` | §A.2.4 |
| `ConditionPostfix` | §A.2.4 |
| `ConditionPrimary` | §A.2.4 |
| `ConditionUnary` | §A.2.4 |
| `ContinueStatement` | §A.2.5 |
| `DecimalLiteral` | §A.1.5 |
| `Digit` | §A.1.5 |
| `EnumDeclaration` | §A.2.1 |
| `ErrorMember` | §A.2.1 |
| `ErrorSetDeclaration` | §A.2.1 |
| `Expression` | §A.2.4 |
| `ExpressionStatement` | §A.2.5 |
| `FieldDeclaration` | §A.2.1 |
| `FieldInit` | §A.2.4 |
| `ForStatement` | §A.2.5 |
| `FunctionDeclaration` | §A.2.1 |
| `GlobalValueDeclaration` | §A.2.1 |
| `HexDigit` | §A.1.5 |
| `HexLiteral` | §A.1.5 |
| `IdentChar` | §A.1.4 |
| `Identifier` | §A.1.4 |
| `IdentStart` | §A.1.4 |
| `IfStatement` | §A.2.5 |
| `IgnoreStatement` | §A.2.5 |
| `IntegerLiteral` | §A.1.5 |
| `Keyword` | §A.1.4 |
| `LineBreak` | §A.1.1 |
| `LineComment` | §A.1.2 |
| `MatchArm` | §A.2.5 |
| `MatchStatement` | §A.2.5 |
| `NumericRun` | §A.1.5 |
| `Parameter` | §A.2.6 |
| `ParameterList` | §A.2.6 |
| `Pattern` | §A.2.5 |
| `PostfixExpression` | §A.2.4 |
| `PostfixPart` | §A.2.4 |
| `PrimaryExpression` | §A.2.4 |
| `Punctuator` | §A.1.6 |
| `RequireStatement` | §A.2.5 |
| `ReturnStatement` | §A.2.5 |
| `ReturnType` | §A.2.6 |
| `SourceFile` | §A.2.1 |
| `SourceText` | §A.1.1 |
| `Statement` | §A.2.5 |
| `StorageKeyword` | §A.2.1 |
| `StructConstructor` | §A.2.4 |
| `StructDeclaration` | §A.2.1 |
| `Token` | §A.1.3 |
| `TopLevelDeclaration` | §A.2.1 |
| `TransactionStatement` | §A.2.9 |
| `Type` | §A.2.2 |
| `TypeArgumentCall` | §A.2.4 |
| `TypeArgumentIntrinsic` | §A.2.4 |
| `UnaryExpression` | §A.2.4 |
| `Underscore` | §A.1.4 |
| `VarStatement` | §A.2.5 |
| `WhileStatement` | §A.2.5 |
| `Whitespace` | §A.1.1 |
| `WipeStatement` | §A.2.5 |

### A.3.2 Mechanical check

The grammar in §A.2 is checked by `src/cardlang/front/grammar.py`, which reads the productions directly from this annex, converts them to BNF and runs an Earley recognizer over the tokens of each source file. `tests/run_checks.py` runs it, and it requires:

- every valid test, every runtime program and every other test file, except those expecting a lexical error, to derive `SourceFile`, file by file;
- every test that expects **CE-SYN-1** not to derive;
- every code block in the design notes that the reference checker accepts to derive `SourceFile`.

The check found one inconsistency, OI-44: EXP-6 excluded an unparenthesized constructor from condition positions, but the general `Expression` in those positions allowed one. `ConditionExpression` (§A.2.4) now encodes the rule (D-444). The other invalid tests derive, as intended: the grammar is deliberately permissive, and their errors come from chapter rules (§A.0).
