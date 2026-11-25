# 9. Testing and debugging

You've written a scenario for every version of the vault so far. This chapter turns that habit into a method. We'll treat scenarios as a test suite, run them from VS Code and from a terminal, use the debugger to track down a real bug, and finish with a look inside the compiled image.

## A test suite of scenarios

A scenario is a test. It drives the applet the way a host would, and checks every answer. Keep your scenarios next to the applet, one file per feature, and start each with a fresh `install` so it can run on its own:

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

In a good scenario every `command` has an `expect` after it, and the failures get as much attention as the successes. Wrong PINs, short requests and responses with no room are what hosts will actually send, and they're also the cases nobody bothers to try by hand.

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

Anything after `#` on a line is a comment.

### Trap kinds

Every trap has a *kind* that says what went wrong, such as `BOUNDS` for an index out of range or `OVERFLOW` for arithmetic that doesn't fit (*RTF-4*). Scenarios name the kind in `expect trap`, and `clc run` and the debugger display it. The [platform reference](reference-platform.md#trap-kinds) lists them all.

The kind is there for you, while you test and debug. The host usually learns only that some trap happened. In the Base Profile it gets category `03` with code `00 00`, or status word `6F00`, whatever the kind was (*PLT-10*). That's one more reason to make anything the host can cause an `Err`, which the host can tell apart, rather than a trap.

## Repeatable randomness

Random bytes, and keys generated from them, come out differently on every real device. To make them repeatable in a test, `seed` restarts the test platform's random generator from a value you choose, and after that the same seed always produces the same bytes. A real platform ignores `seed`.

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

Use it with care. A test that pins down exact random bytes breaks as soon as the applet draws one more byte somewhere earlier, so where you can, check what the random bytes are *for* instead.

## Running the tests

In VS Code, **CardLang: Run Scenario** runs the scenario that's open and prints every step and expectation. From a terminal, `clc run` runs one scenario, and exits with 0 if it passes, so any script or CI job can run the whole suite, on whatever shell or system it uses.

Scenarios run on one of the toolchain's implementations of the CardLang platform, called *backends*. The default is the Python VM, which runs the compiled image, and it's also what the debugger uses. `--backend interp`, or the `cardlang.scenarioBackend` setting, runs the reference interpreter instead. The backends are tested to behave identically, so your applet's tests only need one of them, and the default is the obvious choice.

## Finding a bug

Suppose the loop over the digits in `check_pin_format` had been written to start at 1 instead of 0:

<!-- check: none -->
```cardlang title="Contains a bug"
    for index: u32 in 1..candidate.length {
```

Every scenario so far would still pass. The right PIN is accepted and wrong ones are refused. A new scenario, `pin-format.scenario`, catches the bug:

<!-- check: scenario vault -->
```scenario
install
power_on
command 20 41 32 33 34      # "A234": not all digits
expect err app 1            # malformed, so it costs no try
command 20
expect ok 03                # still three tries
```

With the bug in place, it fails straight away:

```text
pin-format.scenario:3: command 20 41 32 33 34  -> err app 0x4
pin-format.scenario:4: FAIL expect err app 1  (got ('err', 'app', 4))
pin-format.scenario: FAILED, line 4: expected ('err', 'app', 1), got ('err', 'app', 4) (pyvm)
```

`A234` was treated as a well-formed PIN, compared, and counted as a wrong guess, so a typo has cost the user a try. Here's how to see why with the debugger:

1. Check that **Failed expectations** is turned on in the Breakpoints panel, open `pin-format.scenario`, and press F5. The debugger stops at the failing `expect`, and the outcome appears in the Debug Console.
2. Set a breakpoint on the first line of `check_pin_format` and restart with Ctrl+Shift+F5. This time execution stops inside the applet, in the middle of the command.
3. Press F10 until you're inside the loop. In the Variables panel, `index` is 1 on the first pass, while `candidate[0]` is `0x41`, the `A`, which was never checked.
4. Fix the start of the loop and run the scenario again. It passes.

The scenario stays in the suite after the fix, so the bug can't creep back unnoticed.

Not every bug can be caught this way, though. Try moving `tries -= 1` in `check_pin` to after the comparison. No scenario fails, because a scenario can't cut the power at exactly that moment, and [chapter 6](06-state.md) explains why that moment matters. Some properties can only be checked by reading the code.

## The debugger, in full

You can put breakpoints on lines of the `.card` files, or on lines of a scenario to stop before that step runs. Stepping goes statement by statement, with F10 stepping over, F11 stepping into a call, and Shift+F11 stepping out. The call stack runs from the current function down to `process`, with the scenario step at the very bottom. The Variables panel shows the parameters and locals in scope along with the `session`, `persistent` and constant globals, and arrays, structures and views can be expanded.

The Breakpoints panel has two extra switches. **Traps** stops where a trap happens, with the faulting frame still intact, and **Failed expectations** stops at an `expect` that doesn't match. To keep a scenario ready for debugging, add a configuration in `.vscode/launch.json`, as the extension's README describes. <!-- linkcheck: ignore -->

The debugger runs the compiled image on the Python VM, the same code that runs on a device.

## Inside the image

`clc build`, or Build Applet, prints a summary of the compiled image. For the vault it looks something like this:

```text
vault: build\vault.clvm: image 3490 bytes (code 971, constants 6), 12 functions; stack 182, persistent 53, session 1 bytes
```

The *image* is the whole file a device loads, code and constants included. *stack* is the most stack the applet can ever use, in bytes. With no recursion, the compiler can work it out precisely, along every chain of calls. *persistent* and *session* are the bytes of state, laid out by the compiler.

Treat these numbers as your budget. On a device with a few kilobytes of RAM, keep an eye on the stack when you add a large local array or a longer chain of calls.

`clc disasm` lists the compiled code function by function, marking which source line each part comes from:

```text
; function 0: on_install  (frame 24, argc 0, payload 0, operands from 8, code 58 bytes)
; vault.card:42
0000  74                       TXN.BEGIN
...
0031  78 01 00                 NATIVE 1 ; card.key.generate
0034  8b 02                    JERR8 -> 0038
0036  75                       TXN.COMMIT
```

You won't need it often, but when you want to know what something costs, it gives a precise answer. Here, for example, it shows that an `attempt` inside a transaction compiles to a single jump to an abort.
