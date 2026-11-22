# VM0 — Foundations: detailed sub-plan

Parent: `plans_and_notes/vm-plan-of-plans.md`.
Status: decisions A1 to A4 taken 2026-11-19, all as recommended (option (a)). They become V-9 to V-12 in the register. **Drafted 2026-11-19:** the work of §3 is done, and all checks give the same results as before.

## 1. Scope

VM0 sets up everything the later packages share, and writes no VM code:

- the `vm/` folder and its conventions;
- the VM decision register;
- the acceptance criteria every VM must meet;
- a test harness that runs the existing scenarios against any backend: today the reference interpreter, later the Python prototype (VM5) and the C VM (VM7).

## 2. Outputs

### 2.1 Folder layout

```text
vm/
  README.md              what the VM is, the documents, status
  decisions.md           the VM decision register: V-1 to V-8, then V-9 onward
  execution-model.md     VM1
  hal.md                 VM2 (with c/include/cl_hal.h)
  bytecode.md            VM3
  image-format.md        VM3
  c/                     VM7: the product VM in C11
    include/  src/  hal-host/  test/
tools/vmproto/           VM4 and VM5: the Python compiler and VM
tools/harness/           VM0: the scenario runner and the backend interface
plans_and_notes/vm-plans/  one sub-plan per work package
```

### 2.2 Conventions

- **Numbered requirements.** Each `vm/` document states its requirements as numbered items with a per-document prefix: `VEX-n` (execution model), `HAL-n`, `BC-n` (bytecode), `IMG-n` (image format). Each cites the V-n decisions and the spec or profile rules it serves, for example "*Serves: RTF-2, PLT-35; V-2.*" (A1).
- **Decisions.** `vm/decisions.md` holds one row per decision: ID, decision, date, the work package, and the requirements that implement it. An open question waits in the register as a question, never as a requirement.
- **The spec stays the authority.** Where a VM document and the spec or profile disagree, the spec wins, as with the interpreter. A VM document never restates a language rule; it cites it.
- **C naming**, for VM2 and VM7: the prefix `cl_` for functions and types, and `CL_` for macros and constants. One header per layer: `cl_vm.h` (the VM's API to the platform) and `cl_hal.h` (the HAL's API to the VM).
- **Commits:** as for the specification.

### 2.3 Acceptance criteria (A4)

A VM backend is accepted when:

1. **every runtime conformance test passes** (`conformance/runtime/`, 26 today), including the `interrupt` step, which simulates a power loss during a commit;
2. **`check_fido2` passes** (59 checks);
3. **every valid conformance program compiles to an image** (122 today), so the compiler covers the whole language, not only what the runtime tests exercise;
4. **the backend reports its figures:** bytecode size, maximum stack, and frame sizes per program. From VM5 on, it also reports the VM bookkeeping it needs, measured against the 1 KiB bound (V-2).

`tools/run_checks.py` gains one row per backend for criteria 1 to 3, as each backend arrives.

### 2.4 The test harness (A2)

Today the scenario runner sits inside `interp.py`, and `check_fido2.py` builds `interp.Card` directly. VM0 separates them:

- **`tools/harness/scenario.py`** gets the scenario runner (`run_scenario`, `parse_expect`) and the binding encoders (`status_word`, `raw_envelope`), moved unchanged out of `interp.py`.
- **A backend interface,** written down in `tools/harness/README.md`. A backend is built from a checked program and offers what the scenario steps need:

  | Method | Scenario step |
  |---|---|
  | `install()` | `install` |
  | `session_start()` | `session_start`, `power_on` |
  | `session_end()` | `session_end` |
  | `reset()` | `reset` (security reset) |
  | `select()` | `select` |
  | `seed(bytes)` | `seed` (the deterministic DRBG) |
  | `interrupt_next_commit()` | `interrupt` |
  | `command(request, capacity)` | `command` |

  Every method returns the outcome in the form the runner already compares: success with data, an application error code, a platform error, or a trap.
- **A `--backend` option** on the runner and on `check_fido2.py`. Only `interp` exists after VM0; the default stays `interp`, so `run_checks.py` is unchanged.

The interpreter's `Card` becomes the first backend. Its method `power_on` is renamed `session_start`, and the `interrupt` flag becomes a method. Nothing else in it changes.

**A consequence for VM2:** the harness needs fault injection (`interrupt_next_commit`) and a seedable DRBG, so the host HAL must offer both as test hooks.

### 2.5 `vm/README.md` and `vm/decisions.md`

- **The README** gives the VM's purpose and the goals V-1 to V-4, the layer diagram from the plan of plans, the document list with each document's status, and how to run the acceptance checks.
- **The register** opens with V-1 to V-8 from the plan of plans, and V-9 to V-12 from this package's decisions A1 to A4.

## 3. Work

1. Write `vm/README.md` and `vm/decisions.md`.
2. Create `tools/harness/`: move the runner and encoders out of `interp.py`, define the backend interface, and add `--backend`.
3. Point `interp.py`'s command line and `check_fido2.py` at the harness. Behaviour does not change.
4. Run all checks: they must give the same results as before (24 runs, 26 runtime tests, 59 FIDO2 checks).
5. Update the plan of plans: VM0 is done, and VM1 and VM2 are next.

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| A1 | How the `vm/` documents are written | (a) numbered requirements per document (`VEX-n`, `HAL-n`, `BC-n`, `IMG-n`), each citing decisions and spec rules, with no status tags; (b) the spec's full apparatus: status tags, open issues and an annex per document; (c) ordinary design prose | (a). It keeps traceability to the spec, without the overhead of tags: open questions live in the register |
| A2 | One harness for every backend | (a) a shared scenario runner and backend interface; the interpreter is the first backend; (b) a separate runner per VM | (a). One scenario format, one set of expectations, so every VM is checked against the same tests |
| A3 | Where the prototypes live | (a) `tools/vmproto/` for the Python compiler and VM, and `vm/c/` for the C VM; the compiler's long-term home is decided at VM7; (b) a top-level `compiler/` now | (a). The prototype compiler may be rewritten after VM6 |
| A4 | Acceptance criteria | (a) runtime tests, `check_fido2`, every valid program compiles, and the reported figures (§2.3); (b) runtime tests and `check_fido2` only | (a). Criterion 3 stops the compiler from covering only the tested subset of the language |
