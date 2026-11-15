# CardLang conformance tests

Each test in this folder is a CardLang example from the specification, plus metadata that states the expected result. Every example in `spec/` has exactly one test here, and every test names the rules it exercises. The suite is written so that a future compiler and runtime can run it mechanically. Until one exists, the tests are checked by review.

## Layout

| Folder | Contents | Expected result |
|---|---|---|
| `valid/` | Applications or fragments that must compile | `ok` |
| `invalid/` | Programs that must be rejected | `compile-error CE-…` |
| `runtime/` | Programs that must compile and then behave as stated when run | `trap …` or `outcome …` |

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
| `expect` | yes | `ok`, `compile-error CE-<PREFIX>-<n>`, `trap TRAP-<KIND>`, `outcome Ok`, `outcome Ok(<value>)` or `outcome Err(<ErrorSet.Member>)` |
| `note` | no | One line of explanation |

`expect: compile-error` names one compile-error class. When a test could fail for several reasons, it is rewritten so that only one rule is violated.

### Fragments

Many specification examples are fragments: declarations without a host entry point. A `fragment` test is checked as if the harness added a minimal `command` that never uses the fragment's declarations. The harness's addition must not itself cause an error. The exact form of that scaffold depends on how the entry point is identified (OI-5), so it is defined in SP11.

### Runtime tests [Open]

For `runtime/` tests, the way inputs are supplied is not defined yet. This covers request bytes, initial persistent and session state, and the sequence of commands, power-on events and resets. It depends on the host entry contract (chapter 12) and the runtime failure model (chapter 13), and will be defined in SP11 and SP12. Until then, `runtime/` tests state their scenario in `note` lines.

## Relation to the specification

- Each example in a spec chapter names its test file, for example *(conformance: `invalid/exp-014-mixed-operators.card`)*.
- Examples taken from the design notes keep their meaning. Lines added only to make a fragment complete are marked `// scaffold`.
- SP14 checks that every test's rules exist, that every compile-error class or trap kind is defined, and that every spec example has a test.
