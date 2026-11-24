# The execution harness

One scenario runner for every CardLang execution backend (`vm/decisions.md` V-10). There are three backends, which run the same tests: `interp`, the reference interpreter; `pyvm`, the compiler and the Python VM; and `cvm`, the C VM as built by CMake, in `vm/c/build` or the tree `CARDLANG_CVM_BUILD` names (`cvm_backend.py`, through cffi).

- `scenario.py`: the scenario runner, the binding encoders (`status_word`, `raw_envelope`), and the command line.
- `backends.py`: the backend table and `build(name, files, binding=None)`.

```bash
uv run python -I -m cardlang.harness.scenario . --backend interp
```

```bash
uv run python -I examples/fido2/check.py . --backend pyvm
```

## The backend interface

`backends.build` checks the program with the reference checkers and builds a *card*. A program that does not compile raises `BuildError`. The card offers one method per scenario step:

| Method | Scenario step | Meaning |
|---|---|---|
| `install()` | `install` | Persistent state gets its defaults; `on_install` runs. Returns its outcome; on `Err` or a trap the application is not installed (BP-55) |
| `session_start()` | `session_start`, `power_on` | A session start (STA-4, profile BP-56); `on_session_start` runs. Returns its outcome; on `Err` or a trap the application is unavailable until the next session start (BP-55) |
| `session_end()` | `session_end` | A session end: session state, volatile keys and session operations are discarded |
| `reset()` | `reset` | A security reset (RTF-9) |
| `select()` | `select` | ISO 7816 SELECT: runs `on_select`, if declared, and returns its outcome (BP-50a). After a `deselect`, it first starts a new session (BP-56) |
| `deselect()` | `deselect` | ISO 7816: another application is selected, which ends the session (BP-55, BP-56) |
| `seed(data)` | `seed <hex>` | Test hook: seeds the deterministic random generator |
| `interrupt_next_commit()` | `interrupt` | Test hook: the next commit is interrupted by a power loss |
| `command(request, capacity)` | `command <hex> [capacity n]` | Runs the command handler; returns its outcome |

`install()`, `session_start()`, `select()` and `command()` return an *outcome*; a handler that is not declared gives `("ok", [])`:

| Outcome | Meaning |
|---|---|
| `("ok", [bytes])` | `Ok(count)`, with the first `count` bytes of the response |
| `("err", "app", code)` | An application error, with its code |
| `("err", "platform", "Member")` | A `CardError`, by member name |
| `("trap", "KIND")` | A trap, by its RTF-4 kind |
| `("trap", None)` | A command to an application that is unavailable (BP-55). A scenario checks it with a bare `expect trap` |
| `("none",)` | No response: a power loss or a security reset |

The runner turns outcomes into status words or raw envelopes for the `expect sw` and `expect raw` forms, and a success into its length for `expect ok length n`. Backends never encode bindings themselves.
