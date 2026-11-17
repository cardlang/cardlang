"""Generate Annex D §D.3, the rule coverage matrix (SP14).

For every rule, the matrix lists:
  * the conformance tests whose `rule:` header cites it (generated from the headers);
  * otherwise, curated tests that clearly exercise it without citing it (EXERCISED below);
  * otherwise, the reason no conformance test can check it (NOT_TESTABLE below).

Rerun after adding or renaming tests:  python -I tools/generators/coverage.py .
The script fails if any rule has neither a test nor a reason, or if a curated test does not exist.
"""
import re, sys, pathlib
repo = pathlib.Path(sys.argv[1]); spec = repo / "spec"; conf = repo / "conformance"

EXERCISED = {
    "LEX-1": "lex-006-two-files, nam-002-multi-file-any-order",
    "LEX-4": "lex-007-byte-order-mark",
    "LEX-15": "nam-116-redeclare-intrinsic, nam-117-redeclare-card, sta-108-constant-named-like-handler",
    "LEX-20": "exp-003-negative-minimum, exp-103-negative-literal-unsigned",
    "NAM-1": "nam-002-multi-file-any-order, lex-006-two-files",
    "NAM-6": "sta-001-global-declarations, nam-104-global-var",
    "TYP-1": "typ-001-primitive-types, typ-003-nested-structures, typ-004-arrays",
    "TYP-2": "typ-006-unsized-parameters, typ-109-unsized-local",
    "TYP-5": "exp-120-bool-from-integer, exp-121-enum-from-integer, exp-123-typed-constant-no-widening",
    "TYP-12": "out-107-err-enum-variant",
    "TYP-22": "stm-001-local-defaults-and-initializers, run-008-state-lifecycle",
    "CEX-2": "cex-001-basic-constants, cex-103-function-call",
    "CEX-14": "exp-124-nested-convert",
    "EXP-9": "lex-004-boolean-literals, exp-007-equality-bool-enum",
    "EXP-13": "exp-101-operand-type-mismatch, run-001-integer-traps",
    "EXP-20": "run-004-assignment-order, run-017-evaluation-and-copies",
    "EXP-28": "exp-007-equality-bool-enum, exp-117-ordering-bool",
    "EXP-38": "exp-016-truncate-and-bytes",
    "EXP-42": "fun-007-slices-and-views, fun-114-slice-in-initializer",
    "EXP-51": "out-004-attempt-forms, fun-009-constant-and-bindings-by-ref, run-017-evaluation-and-copies",
    "STM-1": "stm-004-if-chain, stm-126-standalone-block",
    "STM-18": "stm-010-statements-after-return, out-005-forwarding",
    "FUN-1": "fun-001-forward-call-across-files, fun-010-no-payload-function",
    "FUN-22": "sta-002-setup-helper, txn-004-callee-writes",
    "OUT-1": "out-001-match-ok-err, out-002-no-payload-match",
    "STA-14": "run-009-transactions, run-008-state-lifecycle",
    "TXN-4": "run-009-transactions",
    "HEP-4": "hep-003-dispatch-and-encode, run-007-outcomes",
    "HEP-5": "hep-001-minimal, run-010-response-contract",
    "HEP-6": "run-010-response-contract",
    "HEP-12": "run-007-outcomes, run-001-integer-traps",
    "HEP-14": "run-001-integer-traps",
    "HEP-16": "every test with kind: fragment, for example exp-001-literal-contexts",
    "RTF-1": "run-001-integer-traps, run-003-short-circuit-and-bounds",
    "RTF-5": "every runtime test: each expects one trap kind at one step",
    "RTF-11": "run-007-outcomes, run-001-integer-traps",
    "RTF-12": "run-009-transactions, run-008-state-lifecycle",
    "PLT-3": "hep-003-dispatch-and-encode",
    "PLT-8": "run-010-response-contract",
    "PLT-9": "run-007-outcomes",
    "PLT-12": "run-014-recovery-after-interrupt",
    "PLT-13": "run-009-transactions, run-014-recovery-after-interrupt",
    "PLT-18": "sta-004-lifecycle-handlers, run-008-state-lifecycle",
    "PLT-19": "run-008-state-lifecycle",
    "PLT-26": "plt-001-platform-call and every test that uses the test-only catalog",
    "PLT-27": "run-002-checked-and-conversions, run-015-resource-identifiers",
    "PLT-28": "run-001-integer-traps, run-013-execution-budget",
    "EXP-52": "exp-013-wrapping, exp-017-checked-convert, exp-019-equal-and-compare",
}

PLATFORM = "A platform obligation: it is checked by a platform's own conformance, not by language tests"
NOT_TESTABLE = {
    "NAM-3": "A build-configuration rule, outside the language; it has no CE class",
    "NAM-5": "Isolation between applications; each conformance test is a single application",
    "TYP-9": "Representation is not observable by a conforming program",
    "TYP-23": "Target storage limits are platform-defined; the suite has no target profile",
    "EXP-22": "Permits only transformations that are unobservable by definition",
    "OUT-17": "An obligation across versions of an application, not on one program",
    "STA-13": "Rejection depends on a target's atomic-update limit, which is platform-defined",
    "TXN-12": "The scenario format cannot inject a contained commit failure",
    "TXN-14": "Not observable: commands never interleave, so no other context runs during a transaction",
    "TXN-16": "Transaction capacity is platform-defined; the suite has no target profile",
    "HEP-8": "The initial response contents are deliberately unspecified, so no expectation is portable",
    "HEP-10": "Transmission timing relative to commit is not observable through the scenario format",
    "HEP-13": "Non-interleaving is a property of the platform; the harness runs commands one at a time by construction",
    "RTF-7": "Stack limits are per target profile and platform-defined",
    "RTF-8": "A rule about how limits are enforced; the suite has no target profile",
    "PLT-17": "Informative: future platform work",
    "PLT-31": "Timing is not observable by a conforming program; checked by platform evaluation",
    "PLT-32": "Side-channel and fault resistance is not observable by a conforming program; checked by platform evaluation",
}
for r in "PLT-1 PLT-2 PLT-4 PLT-5 PLT-6 PLT-7 PLT-10 PLT-11 PLT-14 PLT-15 PLT-16 PLT-21 PLT-29 PLT-30 PLT-33 PLT-34".split():
    NOT_TESTABLE[r] = PLATFORM

ORDER = "LEX NAM TYP CEX EXP STM FUN OUT STA TXN HEP RTF PLT".split()
rules = []
for f in sorted(spec.glob("*.md")):
    rules += re.findall(r"^\*\*([A-Z]{3}-\d+) \[\w+\]\*\*", f.read_text(encoding="utf-8"), re.M)
rules.sort(key=lambda r: (ORDER.index(r.split("-")[0]), int(r.split("-")[1])))

tests = {}
for f in sorted(conf.rglob("*.card")):
    name = (f.parent.name if f.parent.parent.name in ("valid", "invalid", "runtime") else f.stem)
    head = f.read_text(encoding="utf-8", errors="replace").split("\n\n")[0]
    m = re.search(r"^// rule: (.*)$", head, re.M)
    for r in re.findall(r"[A-Z]{3}-\d+", m.group(1) if m else ""):
        tests.setdefault(r, [])
        if name not in tests[r]: tests[r].append(name)
names = {p.stem if p.suffix else p.name for d in ("valid", "invalid", "runtime") for p in (conf / d).iterdir()}

rows, counts, problems = [], {"cited": 0, "exercised": 0, "reason": 0}, []
for r in rules:
    if r in tests:
        rows.append(f"| {r} | cited | {', '.join(sorted(tests[r]))} |"); counts["cited"] += 1
        if r in EXERCISED or r in NOT_TESTABLE: problems.append(f"{r} is cited by a test; remove its curated entry")
    elif r in EXERCISED:
        for t in re.findall(r"\b[a-z]{3}-\d{3}-[\w-]+", EXERCISED[r]):
            if t not in names: problems.append(f"{r}: no test named {t}")
        rows.append(f"| {r} | exercised | {EXERCISED[r]} |"); counts["exercised"] += 1
    elif r in NOT_TESTABLE:
        rows.append(f"| {r} | not testable | {NOT_TESTABLE[r]} |"); counts["reason"] += 1
    else:
        problems.append(f"{r} has neither a test nor a reason")
assert not problems, problems

section = f"""## D.3 Rules → conformance tests

<!-- D.3 generated by tools/generators/coverage.py; do not edit by hand -->

Every rule has at least one conformance test, or a stated reason why no conformance test can check it.

| Value | Meaning |
|---|---|
| `cited` | The tests listed cite the rule in their `rule:` header |
| `exercised` | No test cites the rule, but the tests listed clearly depend on it |
| `not testable` | No conformance test can check the rule, for the reason given |

**Totals:** {len(rules)} rules: {counts['cited']} cited, {counts['exercised']} exercised, {counts['reason']} not testable.

| Rule | Coverage | Tests or reason |
|---|---|---|
""" + "\n".join(rows) + "\n"

p = spec / "annex-D-traceability.md"; t = p.read_text(encoding="utf-8")
t = t.split("## D.3 Rules → conformance tests")[0].rstrip("\n") + "\n\n" + section
p.write_text(t, encoding="utf-8", newline="\n")
print("rules:", len(rules), counts)
