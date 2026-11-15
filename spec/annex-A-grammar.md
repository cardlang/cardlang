# Annex A — Grammar

CardLang Language Specification, Draft 0.1. Annex status:

- **A.1 lexical grammar:** complete (SP1).
- **A.2 syntactic grammar:** skeleton, filled in by SP2–SP11 and completed in SP14.

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
Token           ::= Identifier | Keyword | Underscore | IntegerLiteral | Punctuator

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

/* A.1.6 Punctuators (LEX-22) */
Punctuator      ::= '{' | '}' | '(' | ')' | '[' | ']' | ';' | ':' | ',' | '.' | '..'
                  | '->' | '=>' | '=' | '==' | '!=' | '<' | '<=' | '>' | '>='
                  | '+' | '-' | '*' | '/' | '%' | '~' | '&' | '|' | '^' | '<<' | '>>'
```

Lexical errors are CE-LEX-1 to CE-LEX-4 (chapter 2 §2.8).

## A.2 Syntactic grammar (skeleton)

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
                    | 'attempt' PostfixExpression
                    | PostfixExpression
PostfixExpression ::= PrimaryExpression PostfixPart*
PostfixPart       ::= '[' Expression ']'
                    | '[' Expression '..' Expression ']'
                    | '.' Identifier
                    | Arguments
PrimaryExpression ::= IntegerLiteral | BooleanLiteral | Identifier
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
```

Notes on these productions:

- **Flat binary structure.** The binary operators have no precedence. A flat sequence is accepted, and EXP-2 to EXP-5 require a single operator per grouping level and forbid comparison chains (CE-EXP-4, CE-EXP-5).
- **Type-argument intrinsics.** The names in `TypeArgumentIntrinsic` are reserved identifiers (LEX-15), not keywords. Writing one followed by `<` always begins a type argument.
- **Constructors in conditions.** A `StructConstructor` must be parenthesized at the outer level of an `if`/`while` condition, a `for` range bound and a `match` scrutinee (EXP-6). In those positions, `Identifier '{'` begins the body.
- **Parsed but restricted.** Slices (`'..'` in an index bracket) and argument modes are parsed here. Chapter 8 restricts where they may appear.

### A.2.5 Statements and blocks (chapter 7)

```
Block               ::= '{' Statement* '}'
Statement           ::= VarStatement | AssignmentStatement | ExpressionStatement
                      | IfStatement | WhileStatement | ForStatement | MatchStatement
                      | BreakStatement | ContinueStatement | ReturnStatement | RequireStatement
                      | TransactionStatement | AbortStatement        /* A.2.9 */
VarStatement        ::= StorageKeyword+ Identifier ':' Type ( '=' Expression )? ';'
AssignmentStatement ::= Expression '=' Expression ';'
ExpressionStatement ::= Expression ';'
IfStatement         ::= 'if' Expression Block ( 'else' 'if' Expression Block )* ( 'else' Block )?
WhileStatement      ::= 'while' Expression Block
ForStatement        ::= 'for' Identifier ':' Type 'in' Expression '..' Expression Block
MatchStatement      ::= 'match' Expression '{' MatchArm* '}'
MatchArm            ::= Pattern '=>' Block
Pattern             ::= 'Ok' '(' ( Identifier | '_' )? ')'
                      | 'Err' '(' ( Identifier | '_' | Identifier '.' Identifier ) ')'
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
- **Range separator.** In `ForStatement`, `..` is the range separator. A `for` bound is parsed with the constructor restriction of EXP-6.
- **Patterns.** `Pattern` covers both enum and outcome patterns. Chapter 9 gives meaning to the `Ok` and `Err` patterns, and §A.2.7 refers back here.

| Section | Content | Filled in by |
|---|---|---|
| A.2.1 | Source files and top-level declarations | SP2 (done) |
| A.2.2 | Types | SP3 (done) |
| A.2.3 | Constant expressions | SP4 (done; see below) |
| A.2.4 | Expressions | SP5 (done) |
| A.2.5 | Statements and blocks | SP6 (done) |
| A.2.6 | Functions, parameters, arguments and slices | SP7 |
| A.2.7 | Outcomes, patterns and error sets | SP8 |
| A.2.8 | State declarations | SP9 |
| A.2.9 | Transactions | SP10 |
| A.2.10 | The host entry point | SP11 |
