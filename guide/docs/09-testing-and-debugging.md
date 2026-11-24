# 9. Testing and debugging

You have written a scenario for every version of the vault. This chapter turns those habits into a method: scenarios as a test suite, run in VS Code or from a terminal; the debugger, used to find a real bug; and a look inside the compiled image.

## A test suite of scenarios

A scenario is a test: it drives the applet as a host would, and checks every answer. Keep them beside the applet, one file per feature, each starting from a fresh `install`, so that each can run on its own:

```text
vault/
  cardlang.json
  vault.card
  counter.scenario
  pin.scenario
  pin-format.scenario
  secret.scenario
  signing.scenario
```

A good scenario follows every `command` with an `expect`, and tests the failures as carefully as the successes: the wrong PIN, the short request, the response with no room. Those are the cases a host will hit, and the ones nobody tries by hand.

### Steps

| Step | What it does |
|---|---|
| `install` | Installs the applet on a fresh device, and runs `on_install` |
| `power_on` | Powers the device on: a session start, which runs `on_session_start` |
| `session_start`, `session_end` | Start or end a session explicitly, as a raw-binding host does |
| `reset` | A *security reset*: the platform's emergency stop, which ends every session (*RTF-9*) |
| `select`, `deselect` | ISO 7816 only: select the applet, or another application |
| `command <hex> [capacity n]` | Sends a request; `capacity` sets the room for the response, 256 bytes by default |
| `interrupt during-commit` | Makes the next commit fail, as if the power were cut |
| `seed <hex>` | Restarts the test platform's random generator from a seed |

### Expectations

| Expectation | The outcome must be |
|---|---|
| `expect ok` | Success, with no data |
| `expect ok <hex>` | Success, with exactly these bytes |
| `expect ok length <n>` | Success, with exactly `n` bytes, whatever they are |
| `expect err app <code>` | The applet's error with this code |
| `expect err platform <Member>` | This `CardError` |
| `expect trap <KIND>` | A trap of this kind, such as `BOUNDS` |
| `expect none` | No answer at all, after `interrupt` |
| `expect raw <hex>` | Exactly this raw-binding envelope |
| `expect sw <hex>` | Exactly this ISO 7816 status word |

`#` starts a comment, anywhere on a line.

### Trap kinds

A trap has a *kind*, which says what went wrong: `BOUNDS` for an index out of range, `OVERFLOW` for arithmetic that does not fit, and so on (*RTF-4*). Scenarios name it in `expect trap`, and `clc run` and the debugger show it. The [platform reference](reference-platform.md#trap-kinds) lists every kind.

The kind is for you, while testing and debugging. The host, on the other hand, usually learns only that a trap happened: in the Base Profile, it gets category `03` with code `00 00`, or status word `6F00`, whatever the kind (*PLT-10*). That is one more reason why anything the host can cause should be an `Err`, which it can tell apart, and not a trap.

## Repeatable randomness

Random bytes, and keys generated from them, are different on every real device. To make them repeatable in a test, `seed` restarts the test platform's random generator from a value you give. From then on, the same seed gives the same bytes, on every run. A real platform ignores `seed`.

<!-- check: program dice -->
```cardlang
command process(request: ref u8[], response: inout u8[]) -> u32 {
    var bytes: u8[4];
    var filled: u32 = attempt card.random.fill(inout bytes);
    response[0..4] = bytes;
    return Ok(4);
}
```

<!-- check: scenario dice -->
```scenario
install
power_on
seed 01 02 03 04
command 00
expect ok 62 1F 46 6F       # always these bytes, after this seed
```

Use it sparingly: a test that pins exact random bytes breaks whenever the applet draws one more byte earlier on. Prefer checking what the random bytes are *for*.

## Running the tests

**In VS Code,** **CardLang: Run Scenario** runs the open scenario, and prints every step and expectation.

**From a terminal,** `clc run` runs one scenario. Its exit code is 0 when the scenario passes, so any script or CI job can run the whole suite, whatever shell or system it uses.

**Where it runs.** A scenario runs on one of the toolchain's implementations of the CardLang platform, its *backends*. The Python VM, which runs the compiled image, is the default, and what the debugger uses. `--backend interp`, or the setting `cardlang.scenarioBackend`, chooses the reference interpreter instead. The backends are tested to behave identically, so one is enough for your applet's tests: the default is the natural choice.

## Finding a bug

Suppose that, in `check_pin_format`, the loop over the digits had been written to start at 1, not 0:

<!-- check: none -->
```cardlang
    for index: u32 in 1..candidate.length {
```

Every scenario so far still passes: the right PIN is accepted, wrong ones are refused. A new scenario, `pin-format.scenario`, catches it:

<!-- check: scenario vault -->
```scenario
install
power_on
command 20 41 32 33 34      # "A234": not all digits
expect err app 1            # malformed, so it costs no try
command 20
expect ok 03                # still three tries
```

With the bug, it fails at once:

```text
pin-format.scenario:3: command 20 41 32 33 34  -> err app 0x4
pin-format.scenario:4: FAIL expect err app 1  (got ('err', 'app', 4))
pin-format.scenario: FAILED, line 4: expected ('err', 'app', 1), got ('err', 'app', 4) (pyvm)
```

`A234` was taken for a well-formed PIN, compared, and counted as a wrong guess: a typo costs the user a try. To see why:

1. In the Breakpoints panel, make sure **Failed expectations** is on. Open `pin-format.scenario`, and press F5. The debugger stops at the failing `expect`, with the outcome in the Debug Console.
2. Set a breakpoint on the first line of `check_pin_format`, and restart (Ctrl+Shift+F5). This time it stops inside the applet, during the command.
3. Press F10 until you are inside the loop. In the Variables panel, `index` is 1 on the first pass, and `candidate[0]` is `0x41`, the `A`: it was never checked.
4. Fix the loop's start, and run the scenario again. It passes.

The bug is fixed, and the scenario stays in the suite, so it cannot come back unnoticed.

## The debugger, in full

- **Breakpoints** go on lines of the `.card` files, or on scenario lines, to stop before a step runs.
- **Stepping is by statement:** F10 steps over, F11 steps into a call, and Shift+F11 steps out.
- **The call stack** runs from the current function down to `process`, with the scenario step at the bottom.
- **Variables** shows the parameters and locals in scope, and the `session`, `persistent` and constant globals. Arrays, structures and views expand.
- **Traps** and **Failed expectations**, in the Breakpoints panel, stop where a trap happens, with the faulting frame intact, or at an `expect` that does not match.
- **A configuration** in `.vscode/launch.json` keeps a scenario to debug, as the extension's README shows. <!-- linkcheck: ignore -->

The debugger runs the compiled image on the Python VM, the same code a device runs.

## Inside the image

`clc build`, or Build Applet, prints a summary of the compiled image. For the vault, it is something like:

```text
vault: build\vault.clvm: image 3490 bytes (code 971, constants 6), 12 functions; stack 182, persistent 53, session 1 bytes
```

- **image** is the whole file a device loads, with its code and constants.
- **stack** is the most stack the applet can ever use, in bytes. With no recursion, the compiler works it out exactly, across every chain of calls.
- **persistent** and **session** are the bytes of state, laid out by the compiler.

These numbers are your budget. On a device with a few kilobytes of RAM, watch the stack when you add a large local array, or a deeper chain of calls.

`clc disasm` lists the compiled code, function by function, with the source line of each part:

```text
; function 0: on_install  (frame 24, argc 0, payload 0, operands from 8, code 58 bytes)
; vault.card:42
0000  74                       TXN.BEGIN
...
0031  78 01 00                 NATIVE 1 ; card.key.generate
0034  8b 02                    JERR8 -> 0038
0036  75                       TXN.COMMIT
```

You rarely need it, but it answers "what does this cost?" precisely: here, `attempt` inside a transaction is a single jump to an abort.

## What next

- Split the vault's scenarios into one file per feature, as above, and run each with `clc run` from a terminal.
- Plant a bug of your own: change `tries -= 1` to come after the comparison in `check_pin`. Which scenario catches it? If none does, write one. (Hint: chapter 6 says why a power cut there matters, and no scenario can cut the power at that moment. Some properties can only be checked by reading the code.)
