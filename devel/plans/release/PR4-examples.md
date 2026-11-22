# PR4 — Self-contained examples: detailed sub-plan

Planned 2026-11-22, the fourth work package of PR0 (R6). Each example applet becomes a complete unit: its sources, its project file, its scenarios, its own checker and a README, all in one folder. Nothing is deleted, and every move is a `git mv`.

## 1. What there is now

| Applet | In `examples/<app>/` | Elsewhere |
|---|---|---|
| `fido2` | six `.card` sources, `cardlang.json`, `getinfo.scenario`, and a git-ignored `build/` | its checker, `tools/fido/check_fido2.py` (266 lines) |
| `piv` | six `.card` sources, `cardlang.json` and `basic.scenario` | its checker, `tools/piv/check_piv.py` (280 lines) |

- **The checkers** build the applet through a harness backend and run a scripted session. They check every response with code of their own, such as a CBOR codec, a DER parser or a BER-TLV codec, so none of the applet's logic is reused. They take `--backend` (interp, vmproto, cvm-msvc, cvm-clang). Each reaches the toolchain by adding `tools/harness`, `tools/checkers` and `tools/interp` to `sys.path`. From the interpreter they use only its test crypto, `testcrypto.py` and `p256.py`.
- **`run_checks`** lists the two checkers by hand, five lines each: one for each backend.
- **The scenarios** are run only by the debugger and `Run Scenario` in the editor. `dap_check` launches `getinfo.scenario`, but no check runs either scenario to its end, so a wrong `expect` in one would go unnoticed.
- **There are no READMEs.** What each applet implements, and what it leaves out, is in the findings reports (`devel/reports/WP8-fido2-findings.md`, `WP12-piv-findings.md`) and in the work-package plans.
- **Names elsewhere:**
  - in current documents: the top-level readme, `tools/README.md`, `tools/harness/README.md`, `vm/README.md` and `vm/c/README.md`;
  - in `vm/decisions.md`, by checker name only;
  - in historical documents, which keep their paths and resolve through `layout.MOVED`.

## 2. The work

1. **The moves,** with `git mv`:
   - `tools/fido/check_fido2.py` to `examples/fido2/check.py` (E1);
   - `tools/piv/check_piv.py` to `examples/piv/check.py`;
   - `tools/fido/` and `tools/piv/` are then empty and go away.
2. **The checkers:**
   - they find the toolchain through `layout`, with one bootstrap line each, like the scripts in `devel/`;
   - their usage lines name their new paths;
   - nothing else in them changes. PR5 replaces the bootstrap with `import cardlang`.
3. **`run_checks`** finds the applets itself (E3): every `examples/*/check.py`, on every backend. A new applet, such as WP13's OpenPGP, then needs no change to `run_checks`.
4. **The scenarios are checked** (E2): every `examples/*/*.scenario` runs through `clc run` on every backend, and must pass.
5. **A README per applet** (E4):
   - what it is: the standard and the subset it implements;
   - its files, in the order of `cardlang.json`;
   - how to check, build, run a scenario and debug it;
   - what it leaves out, and its known limits, summarised from the findings report, with a link to it.
6. **`examples/README.md`:** a short page listing the applets, and what makes a folder an example. That is a `cardlang.json`, sources, at least one scenario, a `check.py` and a README.
7. **References:**
   - `layout.MOVED` gains the two checkers;
   - the current documents above are rewritten through it, links included;
   - the top-level readme's rows for the two applets say "with its own checker and README".
8. **Checks:**
   - `run_checks` passes, with the same number of runs for the applets as before, plus the scenarios;
   - the link check passes, with no new INFO lines;
   - the VS Code extension still builds, runs and debugs both applets. `dap_check` and `clc_check` cover this.

**Done when:**
- each `examples/<app>/` holds everything about its applet;
- `tools/` has no applet code;
- `run_checks` finds the applets, their checkers and their scenarios without naming them;
- every reference resolves.

## 3. Decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| E1 | The checker's name in its folder | (a) keep it: `examples/fido2/check_fido2.py`, as PR0 says; (b) one name for all: `examples/fido2/check.py` | (a). The name says what it checks wherever it appears: in an editor tab, a traceback or `run_checks` output. The historical documents also name it so | <!-- linkcheck: ignore -->
| E2 | Checking the scenarios | (a) every example scenario runs on every backend in `run_checks`; (b) leave them to the editor | (a). They are the example a new user runs first, so they should be known to pass. It costs a few seconds |
| E3 | How `run_checks` finds the applets | (a) discovers `examples/*/check.py`, and runs each on every backend; (b) keeps listing them by hand | (a). It is what makes an example self-contained: drop in a folder and it is checked |
| E4 | How much goes in each README | (a) a complete page as in §2 step 5, with the limits summarised from the findings; (b) a stub that links to the findings, filled in by PR7 | (a). The README is what a visitor reads first, and the findings report is a development record in `devel/` |

**Decided (user, 2026-11-22):** E1 (b), one name for all: `check.py`. E2 (a), E3 (a) and E4 (a), as recommended. Because of E1, PR0's mention of `check_fido2.py` and `check_piv.py` becomes `check.py`, and `run_checks` labels each run with its applet's folder name.

## 4. Done (2026-11-22)

- **Moved with `git mv`:**
  - `tools/fido/check_fido2.py` to `examples/fido2/check.py`;
  - `tools/piv/check_piv.py` to `examples/piv/check.py`.

  `tools/fido/` and `tools/piv/` are gone.
- **The checkers:**
  - they find `layout` with one bootstrap line, and the toolchain through it;
  - their usage lines name their new paths;
  - nothing else changed.
- **`run_checks`:**
  - it no longer lists the applets;
  - `example_runs()` finds every `examples/*/check.py` and runs it on the four backends, labelled by its folder (`fido2/check.py`);
  - the new `tools/harness/example_scenarios.py` runs every `examples/*/*.scenario` through `clc run`, on each backend;
  - there are now 51 runs: the same 8 applet runs as before, now on all four backends with `interp` named explicitly, plus 4 scenario runs. All pass.
  - Checked by mutation: a scenario with a wrong `expect` fails the scenario run.
- **READMEs:**
  - `examples/README.md`: the applets, and what an example folder holds;
  - `examples/fido2/README.md` and `examples/piv/README.md`: what each implements and leaves out, its limits, its test defaults, its files, how to check, build, run and debug it, what its checker covers, and a link to its findings report.

  The commands in them were run.
- **References:**
  - `layout.MOVED` has the two checkers, and the two folders, which map to their applets;
  - the top-level readme's layout table has an `examples/` group;
  - `tools/README.md` points to the examples in place of its `fido/` section;
  - `vm/README.md` and `tools/harness/README.md` have the new paths, including in their command blocks, which the link check does not read.
- **Left as they are:**
  - `vm/decisions.md` (V-12, V-42) and the step table in `vm/c/README.md` name the checks `check_fido2` and `check_piv`, as decided and done at the time;
  - `vm/README.md` still says the only backend is `interp`.

  PR7's content cleanup takes these up.
- **The link check passes,** with the same four historical INFO paths as before.
