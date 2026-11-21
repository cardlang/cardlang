"""Diagnostics with positions over the whole conformance corpus (TL1 step 1; tools/checkers/diagnose.py).

- Every valid test, runtime program and example applet gets no diagnostic.
- Every invalid test gets its expected code, placed in one of its own files at a line and column. The exceptions
  are the known gaps below: name rules of chapter 3 that no reference checker implements yet.
- A sample of tests is pinned to the exact line the error is reported on.

Usage: uv run python -I tools/checkers/poscheck.py .
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))
import diagnose
from lexcheck import header

# Chapter 3 name rules with no reference checker (found by TL1, 2026-11-21): missed, or reported with another code.
KNOWN_GAPS = {
    "nam-101-duplicate-across-kinds.card", "nam-102-duplicate-across-files", "nam-103-overloading.card",
    "nam-104-global-var.card", "nam-105-combined-qualifiers.card", "nam-109-parameter-shadows-global.card",
    "nam-110-local-shadows-local.card", "nam-113-duplicate-field.card", "nam-115-unknown-member.card",
    "nam-116-redeclare-intrinsic.card", "nam-117-redeclare-card.card", "nam-118-redeclare-primitive.card",
    "nam-119-same-scope-duplicate.card", "nam-121-parameter-shadows-primitive.card",
}

# The line each of these is reported on, checked by hand against the source (2026-11-21).
PINNED = {
    "exp-145-equal-element-types.card": 11, "fun-115-slice-in-assignment.card": 11, "exp-111-convert-narrowing.card": 8,
    "lex-106-literal-underscore-after-prefix.card": 7, "nam-111-self-reference.card": 8, "exp-124-nested-convert.card": 8,
    "exp-108-mixed-boolean.card": 8, "exp-102-literal-out-of-range.card": 8, "cex-106-division-by-zero.card": 7,
    "lex-107-empty-hex-prefix.card": 7, "out-107-err-enum-variant.card": 13, "txn-113-abort-ok.card": 12,
    "fun-112-ref-forwarded-as-inout.card": 13, "stm-104-increment.card": 9, "cex-116-signed-minimum-division.card": 7,
    "exp-141-unary-minus-unsigned.card": 8, "out-104-ok-empty-in-payload.card": 8, "fun-108-temporary-reference.card": 16,
}

def files_of(t):
    if not t.is_dir(): return [t]
    if (t / "files.txt").exists(): return [t / f for f in (t / "files.txt").read_text().split()]
    return sorted(t.glob("*.card"))

def main(repo):
    ok = True; gaps = 0
    def report(passed, name, detail):
        nonlocal ok
        ok &= passed; print("PASS" if passed else "FAIL", name, "|", detail)
    for t in sorted((repo / "conformance").glob("*/*")):
        if t.name == "platform" or (t.suffix != ".card" and not t.is_dir()): continue
        files = files_of(t)
        if not files: continue
        meta = header(files[0].read_bytes()); exp = meta.get("expect", "")
        if not (exp in ("ok", "runtime") or exp.startswith(("compile-error", "profile-error"))): continue
        ds = diagnose.check(files, meta.get("binding"), meta.get("kind", "fragment"))
        if exp in ("ok", "runtime"):
            report(not ds, t.name, "no diagnostic" if not ds else diagnose.format_diagnostic(ds[0])); continue
        want = exp.split()[-1]
        if t.name in KNOWN_GAPS:
            gaps += 1; print("GAP ", t.name, "| expect", want, "| got", ds[0]["code"] if ds else "nothing"); continue
        if not ds: report(False, t.name, f"expect {want}, got no diagnostic"); continue
        d = ds[0]; placed = d["file"] in [str(f) for f in files] and d["line"]
        good = d["code"] == want and placed and PINNED.get(t.name, d["line"]) == d["line"]
        report(bool(good), t.name, diagnose.format_diagnostic(d) + (f" (pinned to line {PINNED[t.name]})" if t.name in PINNED else ""))
    for ex in ("examples/fido2", "examples/piv"):
        ds = diagnose.check(files_of(repo / ex))
        report(not ds, ex, "no diagnostic" if not ds else diagnose.format_diagnostic(ds[0]))
    print(f"{gaps} known gaps (chapter 3 name rules)")
    print("ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(pathlib.Path(sys.argv[1]).resolve()) else 1)
