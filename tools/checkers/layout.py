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
        # the language definition
        self.spec = r / "spec"
        self.conformance = r / "conformance"
        self.valid = self.conformance / "valid"
        self.invalid = self.conformance / "invalid"
        self.runtime = self.conformance / "runtime"
        self.test_catalog = self.conformance / "platform" / "test-catalog.txt"
        self.design_notes = r / "plans_and_notes" / "card-language-design-notes.md"
        self.platform_notes = r / "plans_and_notes" / "cardlang-platform-notes.md"
        self.decision_register = r / "plans_and_notes" / "decision-register.md"
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
        # development aids
        self.notes = r / "plans_and_notes"
        # Documents that record the past: their file paths are as of writing (PR1 L4). The rationale files in
        # plans_and_notes/ (design notes, decision register) are part of the definition, but they too are a record.
        self.historical = [self.notes]

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
TOP_LEVEL = ("spec", "conformance", "platform", "examples", "vm", "tools", "plans_and_notes")
