"""Where the repository's parts are: the one place that knows the repository's layout.

Every tool asks this module, `layout.at(root).spec`, instead of building `root / "spec"` itself, so moving a part
of the repository changes this module and nothing else. `tests/linkcheck.py` checks that
no other Python file builds a path into a top-level part.

    from cardlang import layout
    L = layout.at()            # this repository; or layout.at(repo) for a repository given on the command line
    L.spec / "00-index.md"
    L.runtime / "run-012-wallet-application"

It finds the repository from its own place, two levels above `src/cardlang/`.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

class Layout:
    """The parts of the repository rooted at `root`."""
    def __init__(self, root=None):
        r = pathlib.Path(root).resolve() if root is not None else ROOT
        self.root = r
        # the language definition
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
        self.guide = r / "guide"                      # the language guide, and its site
        self.editors = r / "editors"
        self.vscode = self.editors / "vscode"         # the VS Code extension
        self.src = r / "src"
        self.package = self.src / "cardlang"          # the Python toolchain
        self.front = self.package / "front"
        self.tests = r / "tests"                      # the checks of the tools and of the definition
        # development aids
        self.devel = r / "devel"
        self.plans = self.devel / "plans"
        self.reports = self.devel / "reports"
        self.generators = self.devel / "generators"
        self.history = self.devel / "history"
        self.measure = self.devel / "measure"
        # Documents that record the past, whose file paths are as of writing: the link check does not check those paths.
        self.historical = [self.devel]

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
TOP_LEVEL = ("language", "platform", "guide", "examples", "vm", "src", "tests", "editors", "devel")
