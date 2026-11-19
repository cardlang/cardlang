# CardLang conformance tests

Each test in this folder is a CardLang example from the specification, plus metadata that states the expected result. Every example in `spec/` has exactly one test here, and every test names the rules it exercises. The suite is written so that a future compiler and runtime can run it mechanically. Until one exists, the tests are checked by review.

## Layout

| Folder | Contents | Expected result |
|---|---|---|
| `valid/` | Applications or fragments that must compile | `ok` |
| `invalid/` | Programs that must be rejected | `compile-error CE-…` |
| `runtime/` | Complete applications that must compile, then behave as their scenario states when run | `runtime` |

## Naming

- **Single-file test:** `<prefix>-<nnn>-<slug>.card`, where `<prefix>` is the lowercase rule prefix of the main rule tested. Example: `exp-014-mixed-operators.card`.
- **Multi-file test:** a directory with the same naming pattern. It contains its `.card` files and a `files.txt` that lists them one per line, in the order given to the build. This mirrors the build-supplied source-file list (DN §4.1). Because file order must not affect name resolution (D-040), a multi-file test may say it must pass for every order of `files.txt`.
- Numbers are never reused.

## Header metadata

Every test file starts with a block of `//` comment lines, one field per line. For a multi-file test, the block is in the first file listed in `files.txt`.

```text
// rule: EXP-14, EXP-15
// source: DN §3.5
// status: agreed
// kind: fragment
// expect: compile-error CE-EXP-3
// note: Mixed + and * without grouping.
```

| Field | Required | Values |
|---|---|---|
| `rule` | yes | One or more rule IDs from `spec/`, comma-separated |
| `source` | yes | DN/PN sections or `D-` IDs that the example comes from |
| `status` | yes | `agreed`, `proposal` or `open`: the strongest tag among the rules tested. A test that depends on a [Proposal] or [Open] rule is not normative until that rule is agreed |
| `kind` | yes | `application` (a complete application, including its single `command`) or `fragment` (declarations checked on their own; see below) |
| `expect` | yes | `ok`, `compile-error CE-<PREFIX>-<n>`, `profile-error BP-<n>` (a build rejected by a Base Profile rule, `platform/base-profile.md`), or `runtime` for a runtime test, whose expected results are in its `scenario.txt` |
| `binding` | no | The Base Profile transport binding the test is built for: `iso7816` or `raw` (profile BP-47). Absent means no binding check |
| `requires` | no | `fault-injection`, for runtime tests that need a harness able to inject faults |
| `also` | no | Other compile-error classes an implementation may report in addition to `expect`. Used only when the violation being tested cannot avoid a second one (for example, a stray `*/` after a comment that may not cross files) |
| `note` | no | One line of explanation |

`expect: compile-error` names one compile-error class: the one the test is about. A conforming implementation must report that class. It may also report the classes listed in `also`, and no others. Where possible, a test is written so that only one rule is violated and `also` is not needed.

### Byte-exact files

Some lexical tests depend on exact bytes: a byte-order mark, lone CR and CRLF line breaks, or invalid UTF-8. `.gitattributes` marks `conformance/**/*.card` as `-text`, so Git stores and checks out every test file unchanged. Edit such files with a tool that preserves bytes.

### Fragments

Many specification examples are fragments: declarations without a host entry point. A `fragment` test is checked as if the harness added the following file to the end of the test's file list. The entry point is the single `command` declaration, whatever its name (D-405).

```text
command scaffold_entry(request: ref u8[], response: inout u8[]) -> u32 {
    return Ok(0);
}
```

A fragment test must therefore not declare a `command` itself, and must not use the name `scaffold_entry`. The scaffold is defined normatively in chapter 12 (HEP-16). If it changes there, this section changes with it.

### Runtime tests

A runtime test is a directory in `runtime/`. It contains:

- `program.card`, or several `.card` files plus `files.txt`. This is a complete application (`kind: application`).
- `scenario.txt`, which lists the steps to run, one per line.

The program's header uses `expect: runtime`. It may also carry `requires: fault-injection`, for tests that only a harness able to inject faults can run. A harness without fault injection reports such tests as skipped.

The application must first compile without errors. The harness then runs the scenario's steps in order, starting from a fresh card where nothing is installed:

| Step | Meaning |
|---|---|
| `install` | Create the application's persistent state with defaults (STA-3). Then run `on_install`, if the application defines it (STA-6) |
| `session_start` | A session start (STA-4): end any open session, apply session defaults, then run `on_session_start` if the application defines it. In the ISO 7816 binding this is power-on |
| `power_on` | The ISO 7816 binding's name for `session_start` |
| `session_end` | A session end (STA-4): session state, volatile keys and `Session` operations are discarded. In the raw binding, the host closing the session |
| `command <hex bytes>` | Invoke the command with these request bytes, for example `command 01 ff`. With no bytes, the request is empty. The response capacity is 256 bytes |
| `command <hex bytes> capacity <n>` | The same, with a response capacity of `n` bytes |
| `reset` | A security reset: all session state is cleared (RTF-9). A `power_on` step is needed before the next command |
| `interrupt during-commit` | Fault injection. The next commit is interrupted by power loss, so the command produces no outcome. Persistent state recovers to all-or-nothing (TXN-13), and the session is lost. Needs `requires: fault-injection` |
| `select` | ISO 7816 binding: a SELECT of the application. It runs `on_select`, if declared, and its outcome is checked by the following `expect` (profile BP-50a) |
| `seed <hex>` | Restart the reference interpreter's deterministic random generator with this seed (WP3 K4). It affects `card.random.fill` and key generation. A real platform ignores it |

Every `command` step is followed by exactly one `expect` line:

| Line | The command must… |
|---|---|
| `expect ok` | Succeed with an empty response |
| `expect ok <hex bytes>` | Succeed with exactly these response bytes |
| `expect err app <code>` | Return an application error with this decimal code |
| `expect err platform <Member>` | Return this `CardError` member. The names are the placeholders of D-415 |
| `expect trap <KIND>` | Trap with this kind, for example `expect trap OVERFLOW` |
| `expect sw <hex>` | The ISO 7816 binding's status word for the outcome (profile BP-51), for example `expect sw 6d00` |
| `expect raw <hex>` | The raw binding's response envelope for the outcome: category, a 2-byte code, then the data (profile BP-53), for example `expect raw 01 00 07` |
| `expect none` | Produce no outcome, after an `interrupt` |

Blank lines, and anything after `#`, are ignored. Tests observe only what the host can see. State is checked indirectly, through the responses of later commands.

### Platform API catalog for tests

Tests that call platform APIs use the **test-only catalog** in `platform/test-catalog.txt` (Annex B, PLT-26; D-443). Its entries are fictional, and all of them live under `card.test.`. The file states each entry's signature, its transaction behavior and, for the interpreter, its test-only runtime behavior. A real platform supplies its own catalog (PLT-25) and need not provide these entries.

## Checking the tests

Until a compiler exists, the reference checkers in `tools/checkers/` verify the compile-time tests against the rules of chapters 2–12. `grammar.py` checks every test against the Annex A grammar, and it is the authority for CE-SYN-1. The reference interpreter in `tools/interp/` runs the runtime tests. Run them all from the repository root:

```bash
python -I tools/run_checks.py
```

See `tools/README.md` for details and known limitations.

## Relation to the specification

- Each example in a spec chapter names its test file, for example *(conformance: `invalid/exp-014-mixed-operators.card`)*.
- Examples taken from the design notes keep their meaning. Lines added only to make a fragment complete are marked `// scaffold`.
- `tools/checkers/speccheck.py` checks that every rule a test cites exists, and that every compile-error class and trap kind is defined. It also checks that every compile-error class is expected by at least one test.
- Annex D §D.3 maps every rule to its tests, or gives the reason no test can check it. Regenerate it with `python -I tools/generators/coverage.py .` after adding tests.
