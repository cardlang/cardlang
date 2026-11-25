# 1. Getting started

By the end of this chapter you'll have the tools installed and an applet of your own running. It's the first version of the *vault*, the PIN-protected store for a secret that the guide builds up chapter by chapter. You'll build it, run it, break it on purpose, and step through it in the debugger. Don't worry about the language yet. Each feature you meet here gets a proper explanation later.

## What you need

You need [VS Code](https://code.visualstudio.com/) and the CardLang extension. Download `cardlang-<version>.vsix` from the [extension's latest release](https://github.com/cardlang/cardlang/releases), open the Extensions view in VS Code (Ctrl+Shift+X, or Cmd+Shift+X on a Mac), choose **Install from VSIX…** from the **…** menu at the top, and pick the file. If you prefer a terminal:

```bash
code --install-extension cardlang-<version>.vsix
```

The extension brings its own copy of the CardLang toolchain, which is the compiler `clc`, the language server and the debugger. The first time you open an applet, it asks whether it may set the toolchain up. Click **Set Up** and give it a minute. It downloads [uv](https://docs.astral.sh/uv/), a tool for installing Python software, checks that the download hasn't been tampered with, and has uv install the toolchain, along with Python if your computer doesn't have it yet. Everything stays in VS Code's storage for the extension, so nothing is installed system-wide. If you ever need to repeat the setup, run **CardLang: Set Up Toolchain** from the Command Palette.

## A quick look at a real applet

Before you write anything of your own, it helps to see a finished applet. The examples live in the CardLang repository, next to the specification, so get a copy of it:

```bash
git clone https://github.com/cardlang/cardlang.git
```

Open the folder in VS Code and look at `examples/fido2/ctap.card`, part of a FIDO2 authenticator. Change a `u32` to `u16` somewhere, or misspell a name, and the mistake is underlined straight away, with an error code from the specification. Undo it. F12 or Ctrl+click takes you to a definition, even in another file, and typing `card.` inside a function lists the platform's APIs with their documentation.

## Applets, platforms and hosts

Three pieces of software are involved whenever an applet runs. The *applet* is the program you write in CardLang. The *host* is whatever talks to it from outside, which might be the main firmware next to a TrustZone secure partition, an app on a phone, or a computer with a card reader. Between the two sits the *platform*, the software on the device that loads the compiled applet and runs it on the CardLang virtual machine. The platform also keeps the applet's persistent state safe when the power fails, offers it keys, cryptography and randomness through APIs named `card.…`, and carries messages between the applet and the host.

CardLang doesn't pin down the details of the platform, so that the same applet can run on very different devices. A *platform profile* writes down what a platform provides. This guide uses the [Base Profile](https://github.com/cardlang/cardlang/blob/main/platform/base-profile.md), which defines the `card.…` APIs, the platform's errors, and two *bindings*, the ways messages travel between host and applet.

The raw binding hands the applet the host's bytes as they arrive, and wraps every answer in a small envelope, which you'll see [below](#what-the-host-receives). It suits microcontrollers and TrustZone, where the host is firmware on the same chip. The ISO 7816 binding speaks the protocol of smart cards, with commands sent as APDUs and answers that end in a two-byte *status word*. [Chapter 7](07-host.md) covers it. An applet is built for one binding, and the vault uses the raw binding until chapter 7.

## Your first applet

An applet is a folder of your own, and it can live anywhere. Make one called `vault` and open it in VS Code.

The folder needs a `cardlang.json`, which names the applet, lists its source files and picks the raw binding:

```json
{ "name": "vault", "files": ["vault.card"], "binding": "raw" }
```

The first version of `vault.card` keeps a counter and answers a single command, which reads it.

<!-- check: program vault -->
```cardlang
errors VaultError {
    MalformedRequest = 1;
    UnsupportedCommand = 2;
    ResponseTooSmall = 3;
}

const READ_COUNTER: u8 = 0x01;

persistent counter: u32;

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length == 1 else VaultError.MalformedRequest;
    require response.length >= 4 else VaultError.ResponseTooSmall;
    if request[0] == READ_COUNTER {
        response[0..4] = encode_be(counter);
        return Ok(4);
    }
    return Err(VaultError.UnsupportedCommand);
}
```

It's easiest to read from the bottom up. `command process` is the applet's entry point, and every applet has exactly one (*HEP-1*). The host sends a request of a few bytes, and the command writes its answer into `response`. The request is passed as `ref`, so the command can read it but not change it, while `response` is `inout`, so the command can write to it.

The command doesn't throw exceptions, because CardLang has none. It returns an outcome. `Ok(4)` means the answer is the first 4 bytes of `response`, and `Err(…)` reports one of the applet's own errors from `VaultError` instead. [Chapter 5](05-outcomes.md) is about outcomes. The two `require` lines guard the rest of the command (*STM-19*). If the request isn't exactly one byte long, or there's no room for a 4-byte answer, the command returns the error named after `else`.

`persistent counter: u32` is a 32-bit unsigned integer that keeps its value when the device loses power. It starts at zero, and [chapter 6](06-state.md) covers the other kinds of state an applet can have. Finally, `encode_be(counter)` turns the counter into 4 bytes, most significant first, and `response[0..4] = …` copies them into the start of the response.

To build it, open `vault.card` and run **CardLang: Build Applet** from the command palette (Ctrl+Shift+P), or click the package icon in the editor's title bar. The output panel shows something like this:

```text
vault: build\vault.clvm: image 346 bytes (code 70, constants 0), 1 functions; stack 44, persistent 4, session 0 bytes
```

`build/vault.clvm` is the *image*, the file a device runs, and it's 346 bytes long. CardLang has no recursion and no heap, so the compiler can work out how much memory the applet will ever need: 44 bytes of stack, and 4 bytes of persistent storage for the counter.

## Running it

You can run the applet without a device. A *scenario* plays the part of the host, sending commands and stating the answer it expects to each one. Create `vault.scenario` next to `vault.card`:

<!-- check: scenario vault -->
```scenario
install                 # install the applet on a fresh device
power_on
command 01              # read the counter
expect ok 00 00 00 00
command 01 capacity 2   # the same, with room for only 2 bytes of answer
expect err app 3
command                 # an empty request
expect err app 1
```

Run **CardLang: Run Scenario**, or click the play icon. Each step is printed with its outcome:

```text
vault.scenario:3: command 01  -> ok 00 00 00 00
vault.scenario:4: ok   expect ok 00 00 00 00
vault.scenario:5: command 01 capacity 2  -> err app 0x3
vault.scenario:6: ok   expect err app 3
...
vault.scenario: passed (pyvm)
```

`err app 3` is `ResponseTooSmall`, the error with code 3 in `VaultError`.

It's worth seeing a failure too. Change the first `expect` to `expect ok 00 00 00 05` and run the scenario again. It stops at that line and tells you what it expected and what it got. Then change it back.

### What the host receives

However a command ends, the host can tell how. In the raw binding every answer arrives in an *envelope*, made of one byte of *category*, two bytes of *code* (most significant first), and then any data (*BP-53*):

| The command ends with | Category | Code | Data |
|---|---|---|---|
| `Ok(count)` | `00` | `00 00` | The first `count` bytes of the response |
| `Err` with one of the applet's errors | `01` | The error's code | None |
| `Err` with one of the platform's errors | `02` | The platform error's code | None |
| A trap | `03` | `00 00` | None |

`expect ok …` and `expect err app …` check what an outcome means, and `expect raw` checks the bytes the host actually receives:

<!-- check: scenario vault -->
```scenario
install
power_on
command 01
expect raw 00 00 00 00 00 00 00   # category 00, code 0000, then the counter
command 01 capacity 2
expect raw 01 00 03               # category 01: the applet's error 3
```

Because the applet's errors and the platform's errors have separate categories, the host can't mix them up, even if two codes happen to be equal. You'll meet the platform's errors in [chapter 5](05-outcomes.md#platform-errors), and traps later in this chapter. The ISO 7816 binding reports the same four outcomes as status words.

## Adding a command

A counter that never changes isn't much use, so the vault's second command increments it. Add a constant below `READ_COUNTER`, and replace `process` with this version:

<!-- check: program vault -->
```cardlang
const INCREMENT: u8 = 0x02;

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length == 1 else VaultError.MalformedRequest;
    require response.length >= 4 else VaultError.ResponseTooSmall;
    if request[0] == READ_COUNTER {
        response[0..4] = encode_be(counter);
    } else if request[0] == INCREMENT {
        counter = counter + 1;
        response[0..4] = encode_be(counter);
    } else {
        return Err(VaultError.UnsupportedCommand);
    }
    return Ok(4);
}
```

Both commands answer with the counter, so `return Ok(4)` has moved to the end, and any other command byte is an error.

Replace the scenario as well. The new one increments the counter twice, then uses `power_on` to switch the device off and on, to show that the counter survives:

<!-- check: scenario vault -->
```scenario
install
power_on
command 02              # increment
expect ok 00 00 00 01
command 02
expect ok 00 00 00 02
power_on                # power lost and restored
command 01              # the counter is still 2
expect ok 00 00 00 02
command 07              # a command the vault does not know
expect err app 2
```

Now introduce a mistake. In `process`, change `counter = counter + 1;` to `counter = request[0];`. The line is underlined immediately, and the Problems panel (Ctrl+Shift+M) says:

```text
CE-EXP-1: Type does not match the required type
```

`request[0]` is a `u8` and `counter` is a `u32`, and CardLang never converts between integer types without being asked. [Chapter 2](02-values-and-types.md) shows how you ask. Every compile error has a code like `CE-EXP-1` that you can look up in the [specification](https://github.com/cardlang/cardlang/blob/main/language/spec/00-index.md). Undo the change before going on.

## Debugging it

Open `vault.card` and click to the left of the line `if request[0] == READ_COUNTER {` to set a breakpoint. Then open `vault.scenario` and press F5. The scenario runs until the applet reaches your breakpoint. From there, F10 steps over a statement, F11 steps into a call, Shift+F11 steps out, and F5 continues to the next command. The Variables panel shows the request and response bytes, the command's locals, and the `persistent` globals, so you can watch `counter` go up as you step over the increment.

Some mistakes only show up while the applet runs, such as reading past the end of the request. CardLang turns these into *traps*. A trap stops the command at once, and the host learns nothing except that it trapped (*RTF-1*). Persistent changes made before the trap remain, unless they were inside a transaction, which [chapter 6](06-state.md#transactions) explains (*RTF-2*).

To cause one, delete the first `require` line from `process`, so nothing checks the length of the request any more, and add two steps to the end of the scenario:

<!-- check: none -->
```scenario
command                 # an empty request: request[0] does not exist
expect trap BOUNDS
```

Run the scenario again. The empty request now ends in `trap BOUNDS at vault.card:14`, the line that reads `request[0]`. Back in the debugger, turn on **Traps** in the Breakpoints panel and press F5, and execution stops on that same line with the request in view. When you've seen it, put the `require` back and remove the two steps.

A trap means the applet has a bug. It isn't an error the applet chose to report. The host gets an envelope of category `03` with no data, so it knows the command failed but not why. With the `require` in place, an empty request becomes an `Err` that the host can make sense of.

## From a terminal

Everything the extension does is also available as a command, which is handy for scripts and continuous integration. The commands run from your copy of the repository, through uv, so for these you need [uv installed](https://docs.astral.sh/uv/getting-started/installation/) on your computer. The first command installs the toolchain into the repository's folder, which takes a moment. From the `vault` folder:

```bash
uv run --project path/to/cardlang clc check .
uv run --project path/to/cardlang clc build .
uv run --project path/to/cardlang clc run vault.scenario
```

`clc run` uses the Python VM unless you pick something else with `--backend`. `--backend interp` runs the reference interpreter, for example.
