# 1. Getting started

In this chapter you install the tools and write your first applet: the start of the *vault*, the small PIN-protected store for a secret that this guide builds. You build it, run it, break it on purpose, and step through it in the debugger. The language itself comes in lightly here; each feature you meet is explained properly in a later chapter.

## What you need

- **[uv](https://docs.astral.sh/uv/),** the Python package manager. The CardLang toolchain is a Python package, and uv installs it, with the right Python, into an environment of its own.
- **[VS Code](https://code.visualstudio.com/).**
- **The CardLang repository,** cloned, with its toolchain installed:

    ```bash
    git clone https://github.com/cardlang/cardlang.git
    cd cardlang
    uv sync
    ```

    `uv sync` installs the compiler `clc`, the language server and the debugger into the repository's `.venv`. Nothing is installed system-wide.

- **The VS Code extension.** Download `cardlang-<version>.vsix` from the [extension's latest release](https://github.com/cardlang/cardlang/releases). In VS Code, open the Extensions view (Ctrl+Shift+X, or Cmd+Shift+X on a Mac), click the **…** menu at its top, choose **Install from VSIX…**, and pick the file. Or, from a terminal:

    ```bash
    code --install-extension cardlang-<version>.vsix
    ```

    The extension runs the toolchain from the repository you cloned.

## A quick look at a real applet

Before writing your own, see what the tools do. Open the repository's folder in VS Code, and open `examples/fido2/ctap.card`, part of a FIDO2 authenticator.

- **Errors appear as you type.** Change `u32` to `u16` somewhere, or misspell a name: the error is underlined at once, with its code from the specification. Undo the change.
- **Go to definition** works with F12 or Ctrl+click, across the applet's files.
- **Completion:** type `card.` inside a function to see the platform's APIs, with their documentation.

## Applets, platforms and hosts

Three parties are involved whenever an applet runs:

- **The applet** is the program you write in CardLang.
- **The platform** is the software on the device that runs it. It loads the compiled applet and runs it on the CardLang virtual machine. It keeps the applet's persistent state safe across power loss, and offers it services such as keys, cryptography and randomness, through APIs named `card.…`. And it passes messages between the applet and the host.
- **The host** is whatever talks to the applet from outside: the main firmware beside a TrustZone secure partition, an app on a phone, or a computer with a card reader.

The language deliberately leaves the platform's details open, so that the same applets can run on very different devices. What a platform provides is written down in a *platform profile*. This guide uses the [Base Profile](https://github.com/cardlang/cardlang/blob/main/platform/base-profile.md), which defines the `card.…` APIs, the platform's errors, and two ways for messages to travel between host and applet, called *bindings*:

- **The raw binding** passes the host's bytes to the applet exactly as they arrive, and wraps each answer in a small envelope, shown [below](#what-the-host-receives). It suits microcontrollers and TrustZone, where the host is firmware on the same chip.
- **The ISO 7816 binding** speaks the protocol of smart cards: commands as APDUs, answers ending in a two-byte *status word*. [Chapter 7](07-host.md) covers it.

An applet is built for one binding. The vault uses the raw binding until chapter 7.

## Your first applet

An applet is a folder of your own, anywhere you like. Make one called `vault`, and open it in VS Code. Since it is outside the CardLang repository, tell the extension where the toolchain is, once: open the settings (Ctrl+, or Cmd+,), search for **cardlang.repository**, and enter the path of your clone.

The folder needs a `cardlang.json`, which names the applet and lists its source files:

```json
{ "name": "vault", "files": ["vault.card"], "binding": "raw" }
```

`"binding": "raw"` chooses the raw binding.

Now `vault.card`. For a start, the vault keeps a counter, and answers one command: read it.

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

Read it from the bottom up:

- **`command process`** is the applet's entry point. Every applet has exactly one (*HEP-1*). The host sends a request, a few bytes, and the command writes its answer into `response`. `ref` means the command can read the request but not change it; `inout` means it can write the response.
- **It returns an outcome.** `Ok(4)` says the answer is the first 4 bytes of `response`. `Err(…)` reports an error instead, from the applet's own list of errors, `VaultError`. CardLang has no exceptions; [chapter 5](05-outcomes.md) shows how errors work instead.
- **`require`** checks a condition, and returns the error after `else` if it does not hold (*STM-19*). Here it makes sure the request is one byte long and there is room for the answer.
- **`persistent counter: u32`** is a 32-bit unsigned integer that keeps its value when the device loses power. It starts at zero, and [chapter 6](06-state.md) covers the other kinds of state an applet can keep.
- **`encode_be(counter)`** turns the counter into 4 bytes, most significant first, and `response[0..4] = …` copies them into the first 4 bytes of the response.

**Build it.** With `vault.card` open, run **CardLang: Build Applet** from the command palette (Ctrl+Shift+P), or click the package icon in the editor's title bar. The output panel shows something like:

```text
vault: build\vault.clvm: image 346 bytes (code 70, constants 0), 1 functions; stack 44, persistent 4, session 0 bytes
```

The *image* in `build/vault.clvm` is what a device runs: 346 bytes in all. Because CardLang has no recursion and no heap, the compiler knows exactly how much memory the applet can ever need: 44 bytes of stack and 4 bytes of persistent storage, for the counter.

## Running it

You don't need a device to run the applet. A *scenario* plays the host: it sends commands and states the answers it expects. Create `vault.scenario` next to `vault.card`:

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

Now see a failure: change the first `expect` to `expect ok 00 00 00 05`, and run it again. The scenario stops at that line, and says what it expected and what it got. Change it back.

### What the host receives

A command ends in one of four ways, and the host can always tell which. In the raw binding, every answer is an *envelope*: one byte of *category*, two bytes of *code*, most significant first, and then the data (*BP-53*):

| The command ends with | Category | Code | Data |
|---|---|---|---|
| `Ok(count)` | `00` | `00 00` | The first `count` bytes of the response |
| `Err` with one of the applet's errors | `01` | The error's code | None |
| `Err` with one of the platform's errors | `02` | The platform error's code | None |
| A trap | `03` | `00 00` | None |

`expect ok …` and `expect err app …` check what the outcome means. `expect raw` checks the exact bytes the host receives:

<!-- check: scenario vault -->
```scenario
install
power_on
command 01
expect raw 00 00 00 00 00 00 00   # category 00, code 0000, then the counter
command 01 capacity 2
expect raw 01 00 03               # category 01: the applet's error 3
```

Applet errors and platform errors have separate categories, so the host never confuses the two, even when their codes are equal. The platform's errors appear in [chapter 5](05-outcomes.md#platform-errors), and traps later in this chapter. In the ISO 7816 binding, the same four outcomes become status words instead.

## Adding a command

A counter that is always zero is not much use. Give the vault a second command, which increments it. Add a constant below `READ_COUNTER`, and replace `process` with this version:

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

Both commands answer with the counter, so `return Ok(4)` moves to the end, and any other command byte is an error.

Replace the scenario too. This one increments twice, then switches the device off and on again with `power_on`, to show that the counter survives:

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

**Make a mistake.** In `process`, change `counter = counter + 1;` to `counter = request[0];`. The line is underlined at once, and the Problems panel (Ctrl+Shift+M) says:

```text
CE-EXP-1: Type does not match the required type
```

`request[0]` is a `u8`, and `counter` a `u32`. CardLang never converts between integer types by itself; [chapter 2](02-values-and-types.md) shows how to convert when you mean to. Every compile error has a code like `CE-EXP-1`, which you can look up in the [specification](https://github.com/cardlang/cardlang/blob/main/language/spec/00-index.md). Undo the change.

## Debugging it

Open `vault.card`, and click left of the line `if request[0] == READ_COUNTER {` to set a breakpoint. Then open `vault.scenario` and press F5. The scenario runs until the applet reaches the breakpoint.

- **Step** with F10 (over), F11 (into) and Shift+F11 (out).
- **The Variables panel** shows the request and response bytes, the command's locals, and the `persistent` globals: watch `counter` change as you step over the increment.
- **Continue** with F5 to the next command.

**Catch a trap.** Some mistakes can only show up while the applet runs, like reading past the end of the request. CardLang turns these into *traps*: the command stops at once, and nothing it did is half-finished (*RTF-1*). To see one, delete the first `require` line from `process`, so that nothing checks the request's length, and add this to the end of the scenario:

<!-- check: none -->
```scenario
command                 # an empty request: request[0] does not exist
expect trap BOUNDS
```

Run the scenario: the empty request now ends in `trap BOUNDS at vault.card:14`, the line that reads `request[0]`. In the debugger, turn on **Traps** in the Breakpoints panel, and press F5: it stops on that line, with the request in view. Put the `require` back, and remove the two steps.

A trap is not an error the applet reports; it is a bug. The host receives an envelope of category `03`, with no data: it learns that the command failed, but not why. The `require` turns an empty request into an `Err` the host can understand.

## From a terminal

Everything the extension does is also a command, for scripts and continuous integration. From the `vault` folder:

```bash
uv run --project path/to/cardlang clc check .
uv run --project path/to/cardlang clc build .
uv run --project path/to/cardlang clc run vault.scenario
```

`clc run` runs on the Python VM unless you choose another with `--backend`, as in `--backend interp` for the reference interpreter.

## What next

- Add a command that resets the counter to zero, with its own byte and a scenario step that checks it.
- Make `INCREMENT` add the request's second byte instead of 1. You will need to change the first `require`, and you will run into the integer conversion from the mistake above, which [chapter 2](02-values-and-types.md) explains.
