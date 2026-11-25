# CardLang for VS Code

[CardLang](https://github.com/cardlang/cardlang) is a small language for secure applets on microcontrollers, TrustZone and smart cards. This extension lets you write, build, run and debug those applets in VS Code.

## What it does

While you type, the extension colours each name by what it is and underlines mistakes straight away, each with its error code from the specification. F12 jumps to a definition, even in another file, and typing `card.` lists the platform's APIs along with their documentation.

You can build an applet and run it against a *scenario*, a short script that sends it commands and checks the answers. When an answer isn't what you expected, start the debugger. You can stop at a breakpoint, step through the applet line by line, and look at its variables and its stored state.

## Getting started

Install the extension and open the folder of an applet, which is a folder with a `cardlang.json` and some `.card` files. The first time, the extension asks whether it may set up the CardLang toolchain, the compiler, language server and debugger it works with. Click **Set Up** and give it a minute. It downloads [uv](https://docs.astral.sh/uv/), a tool for installing Python software, checks that the download hasn't been tampered with, and installs everything into VS Code's storage for the extension. You only do this once.

New to CardLang? [Chapter 1 of the CardLang Guide](https://cardlang.github.io/cardlang/01-getting-started/) takes you from an empty folder to your first applet, built, tested and stepped through in the debugger with this extension.

## Commands

| Command | What it does |
|---|---|
| **CardLang: Check Applet** | Checks the applet and lists any errors in the Problems panel |
| **CardLang: Build Applet** | Checks and compiles the applet |
| **CardLang: Run Scenario** | Runs the open scenario and shows each step and its result |
| **CardLang: Debug Scenario** | Runs the open scenario in the debugger. F5 does the same |
| **CardLang: Set Up Toolchain** | Runs the setup again |

If you debug the same scenario often, keep it in `.vscode/launch.json`: <!-- linkcheck: ignore -->

```json
{
  "type": "cardlang",
  "request": "launch",
  "name": "Debug the PIN tests",
  "scenario": "${workspaceFolder}/pin.scenario"
}
```

## Settings

| Setting | What it's for |
|---|---|
| `cardlang.scenarioBackend` | What runs your scenarios: `pyvm`, the Python VM (the default), or `interp`, the reference interpreter. `cvm`, the C VM, needs a clone of the CardLang repository with the C VM built |
| `cardlang.repository` | A clone of the CardLang repository to take the toolchain from. You only need it if you work on CardLang itself |
| `cardlang.uvPath` | Your own uv, if you'd rather the extension didn't download one |

To make `persistent` globals stand out in your theme, add this to your settings:

```json
"editor.semanticTokenColorCustomizations": {
  "rules": { "variable.persistent": { "fontStyle": "underline" } }
}
```

## Good to know

CardLang is young, and so is this extension. The checker shows one error at a time, and a few rules about names aren't checked yet, so a duplicate name or a shadowed variable goes unreported. Completion covers the platform's APIs and the members of enums and error sets, but not yet the fields of a variable. The debugger runs applets on the Python VM.

The extension is part of the [CardLang repository](https://github.com/cardlang/cardlang), under the Apache License 2.0. If you'd like to work on it, [DEVELOPMENT.md](DEVELOPMENT.md) explains how it's put together.
