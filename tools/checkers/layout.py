"""Where the repository's parts are (PR1): the one place that knows the repository's layout.

Every tool asks this module, `layout.at(root).spec`, instead of building `root / "spec"` itself, so moving a part
of the repository (PR0: PR2 to PR6) changes this module and nothing else. `tools/checkers/linkcheck.py` checks that
no other Python file builds a path into a top-level part.

    import layout
    L = layout.at()            # this repository; or layout.at(repo) for a repository given on the command line
    L.spec / "00-index.md"
    L.runtime / "run-012-wallet-application"

PR5 moves this module to `cardlang.layout`.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

class Layout:
    """The parts of the repository rooted at `root`."""
    def __init__(self, root=None):
        r = pathlib.Path(root).resolve() if root is not None else ROOT
        self.root = r
        # the language definition (PR3)
        self.language = r / "language"
        self.spec = self.language / "spec"
        self.conformance = self.language / "conformance"
        self.valid = self.conformance / "valid"
        self.invalid = self.conformance / "invalid"
        self.runtime = self.conformance / "runtime"
        self.test_catalog = self.conformance / "platform" / "test-catalog.txt"
        self.rationale = self.language / "rationale"
        self.design_notes = self.rationale / "card-language-design-notes.md"
        self.platform_notes = self.rationale / "cardlang-platform-notes.md"
        self.decision_register = self.rationale / "decision-register.md"
        self.releases = self.language / "releases"
        # the platform profile
        self.platform = r / "platform"
        self.base_profile = self.platform / "base-profile.md"
        self.base_catalog = self.platform / "base-catalog.txt"
        self.base_types = self.platform / "base-types.card"
        # the implementation
        self.examples = r / "examples"
        self.vm = r / "vm"
        self.vm_c = self.vm / "c"
        self.tools = r / "tools"
        # development aids (PR2)
        self.devel = r / "devel"
        self.plans = self.devel / "plans"
        self.reports = self.devel / "reports"
        self.generators = self.devel / "generators"
        self.history = self.devel / "history"
        self.measure = self.devel / "measure"
        # Documents that record the past: their file paths are as of writing (PR1 L4). The rationale and the release
        # notes are part of the definition, but they too are a record.
        self.historical = [self.devel, self.rationale, self.releases]

    def __repr__(self): return f"Layout({str(self.root)!r})"

_here = None

def at(root=None):
    """The layout of the repository at `root`, by default this one."""
    global _here
    if root is None:
        if _here is None: _here = Layout()
        return _here
    return Layout(root)

# The top-level parts, for linkcheck's check that only this module builds paths into them.
TOP_LEVEL = ("language", "platform", "examples", "vm", "tools", "devel")

# Where moved files went: (old path or folder, new path or folder), relative to the root. Historical documents keep the
# paths they were written with (PR1 L4); linkcheck resolves them through this table, so they are still checked.
MOVED = [
    # PR2: development aids into devel/
    ("plans_and_notes/specification-plan-of-plans.md", "devel/plans/specification-plan-of-plans.md"),
    ("plans_and_notes/vm-plan-of-plans.md", "devel/plans/vm-plan-of-plans.md"),
    ("plans_and_notes/spec-plans", "devel/plans/spec"),
    ("plans_and_notes/vm-plans", "devel/plans/vm"),
    ("plans_and_notes/tooling-plans", "devel/plans/tooling"),
    ("plans_and_notes/release-plans", "devel/plans/release"),
    ("plans_and_notes/base-api-plan.md", "devel/plans/spec/base-api-plan.md"),
    ("plans_and_notes/SP14-consolidation-report.md", "devel/reports/SP14-consolidation-report.md"),
    ("plans_and_notes/VM5-measurements.md", "devel/reports/VM5-measurements.md"),
    ("plans_and_notes/VM7-measurements.md", "devel/reports/VM7-measurements.md"),
    ("plans_and_notes/VM7b-measurements.md", "devel/reports/VM7b-measurements.md"),
    ("plans_and_notes/WP8-fido2-findings.md", "devel/reports/WP8-fido2-findings.md"),
    ("plans_and_notes/WP12-piv-findings.md", "devel/reports/WP12-piv-findings.md"),
    ("plans_and_notes/WP8-step0-notes.md", "devel/reports/WP8-step0-notes.md"),
    ("plans_and_notes/PIV-step0-notes.md", "devel/reports/PIV-step0-notes.md"),
    ("tools/generators", "devel/generators"),
    ("tools/history", "devel/history"),
    ("tools/vmproto/measure.py", "devel/measure/pyvm_measure.py"),
    ("tools/vmproto/revision.py", "devel/measure/revision.py"),
    ("vm/c/measure.py", "devel/measure/cvm_measure.py"),
    # PR3: the definition into language/
    ("spec", "language/spec"),
    ("conformance", "language/conformance"),
    ("plans_and_notes/card-language-design-notes.md", "language/rationale/card-language-design-notes.md"),
    ("plans_and_notes/cardlang-platform-notes.md", "language/rationale/cardlang-platform-notes.md"),
    ("plans_and_notes/decision-register.md", "language/rationale/decision-register.md"),
    ("plans_and_notes/draft-0.2-release-notes.md", "language/releases/draft-0.2.md"),
    ("plans_and_notes/draft-0.2-candidates.md", "language/releases/draft-0.2-candidates.md"),
]

def moved(path):
    """Where a root-relative path, or a path inside a moved folder, is now; None if it never moved."""
    for old, new in MOVED:
        if path == old: return new
        if path.startswith(old + "/"): return new + path[len(old):]
    return None
