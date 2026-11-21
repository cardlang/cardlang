# TL1 — A VS Code extension for CardLang: detailed sub-plan

Planned 2026-11-21, at the user's request, before VM8, VM9 and WP13. Tooling work packages are numbered `TL-n`, so they cannot collide with the specification's `WP-n` or the VM's `VM-n`.

**Goal.** One VS Code extension that makes CardLang pleasant to write, build and debug. It has three parts, as the user asked:
1. **Syntax highlighting** for `.card` files, and for the scenario files that drive an applet.
2. **Building** an applet: check and compile from the editor, with every error shown at its file, line and column.
3. **Debugging** an applet: run a scenario against it, and stop at breakpoints in the `.card` source. There you can step, see the call stack, and inspect parameters, locals, globals and the request and response bytes. A trap stops at its source line.

**Why now.** It eases every later step (VM8, VM9, WP13), and it is what a real developer of applets will need. Today that is the user.

## 1. Where it starts

| Need | What exists | What is missing |
|---|---|---|
| Highlighting | The lexer, `tools/checkers/lexcheck.py`: its keywords and literal forms are the definition | A TextMate grammar |
| Errors at a position | The checkers report a code, `CE-EXP-4` for example. The specification defines each code | **Tokens carry no position**, so no error can say where it is. Error messages are only codes |
| Building | The prototype compiler (`tools/vmproto/compiler.py`) produces an image | A command-line front end that the editor can call |
| Debug information | The image has a debug section (IMG-10): files, function names and a line table | **The line table is always empty**, and the section has no variable information |
| Running an applet | Scenario files, and four backends behind one interface (`tools/harness/`) | A way to stop in the middle of an entry point |
| The environment | VS Code 1.146 and the project's uv Python | **Node.js is not installed** (M1) |

## 2. The design

**The extension (M1).**
- It is plain JavaScript using only the `vscode` API, with no npm packages and no build step.
- It lives in `tools/vscode/`: `package.json`, `extension.js`, two TextMate grammars, a language configuration and snippets.
- `tools/vscode/install.py` links the folder into `~/.vscode/extensions` with a directory junction, so an edit takes effect after reloading the window. Nothing is downloaded.
- For the tools, it calls the repository's Python through uv. The setting `cardlang.toolsPath` names the repository, and defaults to the open workspace.

**The command line: `tools/clc.py`.** The one front end that the extension and a terminal share:
- `clc check <files>` reports diagnostics as `file:line:col: CE-EXP-4: <message>`, or as JSON with `--json`;
- `clc build <files> -o app.clvm` writes the image, with its debug section;
- `clc disasm app.clvm` lists the code with source lines;
- `clc run <scenario> --backend <name>` runs a scenario, with the program files named by its header or given on the command line.

**Source positions.**
- **Positions:** the lexer records each token's file and character position alongside the token list. A compile error names the token where it was found; the parsers already know the current token index.
- **Messages:** the text for each `CE-` code comes from the specification. Every chapter defines its codes, and a small table, generated from the chapters, gives each code its one-line meaning.
- **Coverage, M3:** this is the part that touches the most code. Every checker that raises an error must say at which token.

**Debug information** (IMG-10, extended in place under V-51):
- **Line table:** one row per statement, with its code offset, file and line. This also lets traps report their position, as IMG-10 always meant them to.
- **Variables:** per function, each parameter and local with its name, type, frame offset and the code range of its scope.
- **Globals:** each `session` and `persistent` global with its name, type and offset.
- **Types:** a compact type table, enough to show integers, booleans, enums by member name, arrays, structures and views.

The device VM never reads the section, and a tool may strip it.

**The debugger (M2, M4).**
- **The adapter:** a Debug Adapter Protocol server in Python, `tools/dap/cardlang_dap.py`, speaking DAP over standard input and output. The extension starts it.
- **The engine:** the prototype VM, `tools/vmproto/vm.py`, stepped one instruction at a time. It executes exactly what the C VM does, which differential testing has shown since VM7.
- **What drives it:** a launch configuration names the program and a scenario file. The adapter runs the scenario's steps in order, and the debug console shows every APDU, outcome and check.
- **Breakpoints:** by line, through the line table.
- **Stepping:** in, over and out, by source line. The call stack comes from the frames.
- **Variables:**
  - parameters and locals, from the frame and the debug information;
  - `session` and `persistent` globals;
  - the request and the response, as bytes.
- **Failures:**
  - a trap stops at its line, with its kind;
  - a failed `expect` stops at its scenario line.

## 3. Work

| Step | What | Done when |
|---|---|---|
| 1 | **Source positions** in the lexer and the checkers; the code-to-message table | Every invalid conformance test reports its expected code at a file and line; a check in `run_checks` verifies a sample |
| 2 | **`tools/clc.py`**: check, build, disasm, run | It builds both applets, and reports errors with positions |
| 3 | **The extension, part 1:** the language, both grammars, the language configuration, snippets, and the Check and Build commands with diagnostics on save (M3) | Highlighting works on every example; errors appear in the Problems panel at the right place |
| 4 | **Debug information** in the image: the line table, variables, globals and types | `clc disasm` shows source lines; traps report positions in the harness |
| 5 | **The debug adapter** on the prototype VM | A scripted DAP session in `run_checks` sets a breakpoint in FIDO2, stops, reads variables, steps and continues |
| 6 | **The extension, part 2:** the debugger contribution, launch configurations and their snippets | The user debugs the FIDO2 and PIV applets from VS Code |
| 7 | **Documentation:** `tools/vscode/README.md`, and a short user guide | |

The steps are in dependency order. Step 3 needs only steps 1 and 2, so highlighting and building are usable before the debugger exists.

## 4. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| M1 | How the extension is built and installed | (a) plain JavaScript with no npm packages, linked into `~/.vscode/extensions` by a script: nothing to download or build; (b) TypeScript, with `npm`, the VS Code type definitions, and `vsce` to make a `.vsix` package: this needs Node.js installed, plus npm downloads | (a). The extension is small: a grammar, a few commands, and a debug adapter factory. The adapter itself is Python. A `.vsix` can come later, for sharing |
| M2 | What the debugger runs on | (a) the prototype VM in Python: easy to instrument, with no change to the C VM, and identical behaviour; (b) the C VM, with a debug hook in test builds (stop, step, read memory), through `cffi`; (c) (a) now, (b) when VM9 needs debugging on the real host build | (c). The prototype gives a full debugger quickly. A C-side hook is real work and adds code to the VM, so it waits until the bridge needs it |
| M3 | How errors reach the editor | (a) the extension runs `clc check` on save, and fills the Problems panel; (b) a language server (LSP) in Python, checking as you type, with room for hover, go-to-definition and outline later | (a) first. It needs the same positions as (b) and none of its protocol. An LSP can replace it later, reusing `clc`'s checking |
| M4 | What drives a debug session | (a) a scenario file, the existing harness format, named in the launch configuration; (b) an interactive console where you type APDUs; (c) both | (a), with (b) as a later addition. Scenarios already exist for every applet and test, and are repeatable |

**Answered (user, 2026-11-21):**
- **M1:** quoting the user, "In the end a .vsix would be great, but if developing without node is easier let's go with it. I can install node and any other programs if they will help." With M3's answer, Node.js does help: a language server needs a client on the VS Code side, and the standard one, `vscode-languageclient`, is an npm package. The proposal is therefore N1.
- **M2 (c):** the debugger runs on the prototype VM first; a debug hook in the C VM comes when VM9 needs it.
- **M3 (b):** a language server. It checks as you type, and leaves room for hover, go-to-definition and an outline later.
- **M4 (a):** scenario files drive a debug session; an interactive APDU console may come later.

**Revised design, following M1 and M3:**
- **The extension:** plain JavaScript, with no TypeScript build step. It depends on one npm package, `vscode-languageclient`. `@vscode/vsce` packages it as a `.vsix`, which is installed like any other extension. This needs Node.js LTS (N1).
- **The language server:** Python, `tools/lsp/cardlang_lsp.py`, over standard input and output. It reuses `clc`'s checking and publishes diagnostics as you type. Hover, go-to-definition and the outline come later, from the same front end once it has positions.
- **The protocol layer (N2):** the language server and the debug adapter both speak JSON-RPC with the same framing.
- **The plan's steps,** as revised:
  - step 3 builds the language server, and the extension's client for it, instead of check-on-save;
  - a new step 8 packages the `.vsix`.

**N1 and N2 (user, 2026-11-21):**
- **N1:** the user installs Node.js LTS. The extension is plain JavaScript, using `vscode-languageclient`, and is packaged as a `.vsix` with `@vscode/vsce`. Each npm download is asked for first.
- **N2:** the Python protocol layer is our own: one module for the `Content-Length` framing, shared by the language server and the debug adapter. No new Python dependencies.

**The steps, final:**
1. Source positions, and the table from codes to messages.
2. `tools/clc.py`.
3. The extension, part 1: the grammars, the language configuration, snippets, the Build command, and the language server with diagnostics as you type.
4. Debug information in the image.
5. The debug adapter.
6. The extension, part 2: debugging.
7. Documentation.
8. The `.vsix`.

Steps 1, 2 and 4 need no Node.js. The extension in step 3 can first be tried by linking its folder into VS Code, and then once `vscode-languageclient` is installed.

**Code colouring (user, 2026-11-21).** This is in addition to the grammar's highlighting.
- **Two layers, as VS Code does it:**
  - **Lexical colouring:** the TextMate grammar of step 3 colours keywords, literals, byte strings, comments, operators and punctuation. It is instant, works without the server, and covers scenario files too.
  - **Semantic colouring:** the language server sends *semantic tokens*, so that each identifier is coloured by what it is, not by how it is spelled. The checker already resolves every name, and step 1 gives each one a position.
- **Kinds, using VS Code's standard token types,** so every colour theme colours them without setup:
  - `function`, for a function, a handler or `command`;
  - `type` and `struct`, for types and structures;
  - `enum` and `enumMember`, for enums and their members;
  - `parameter` and `variable`;
  - `property`, for a structure field;
  - `macro`, for intrinsics such as `checked_add`, `fill` and `convert`;
  - `namespace`, for the `card` APIs' path segments.
- **Modifiers:**
  - `readonly`, for a `const`, or a `ref` parameter;
  - `declaration`, where a name is declared;
  - `static`, for a `session` global;
  - a custom `persistent` modifier, for a `persistent` global. A theme can be set, through `editor.semanticTokenColorCustomizations`, to show at a glance what lives in persistent storage. The extension's README will give an example.
- **Error sets:** the members of an `errors` set are `enumMember`.

**Step 3b, semantic colouring,** comes after the language server of step 3. It is done when every identifier in both applets and in the runtime tests gets a kind, and a check in `run_checks` compares the kinds in one sample file with the expected ones.

**Node.js:** v26.13.1 and npm 11.20.0, installed by the user in `C:\Program Files\nodejs`. The tools take `PATH` from the registry, as `vm/c/build.py` does, because a session started before the installation does not see it.
