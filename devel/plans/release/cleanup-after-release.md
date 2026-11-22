# Cleanup after the release check (2026-11-22)

Asked by the user after reading the published tree.

| Item | Decision (user) | Done |
|---|---|---|
| The design notes named a third-party card platform as an architectural reference | Remove it, and from the history too | The paragraph is removed from `language/rationale/card-language-design-notes.md`. The history is rewritten as described below |
| `compiler.py` and others called the compiler and the Python VM "prototype" | They are not prototypes any more | "the prototype compiler" is now "the compiler", and "the prototype VM" and "the prototype's" are now "the Python VM" and "the Python VM's". This covers the package, the tests, the C sources' comments, the VM documents, decisions V-11 and V-29 to V-32, and the extension's settings text. V-3 and V-28 keep the word, as decisions about prototypes made at the time. The design notes' "function prototypes" is the language feature, and stays |
| The package's `__init__.py` files said where they used to be ("was in tools/") | Irrelevant to a reader | Removed |
| `layout.MOVED`, the table of moves | Remove it | It is gone, with `layout.moved()`. Only `devel/` is historical now, and the link check does not check the file paths its documents name, only their links. The rationale and the release notes are checked like any current document; three old paths in them were updated |
| `vm/c/cmake/llvm-mingw-x86_64.cmake` | Remove it; take clang from the PATH | Removed. `build.py` uses `x86_64-w64-mingw32-clang` from the PATH, or `CC`, and CMake finds the archiver and resource compiler beside it. `cvm_measure.py` finds its tools the same way. A clean clang build passed with llvm-mingw's `bin` on the PATH. **llvm-mingw's `bin` folder must now be on the PATH for the clang build** |
| `vm/decisions.md` | Keep it in `vm/` | Unchanged: 224 citations in 31 files use its V-n IDs |

`run_checks` passes all 51 runs.

## The history rewrite

`git filter-branch --index-filter` rewrote `main` and the tags `spec-draft-0.1`, `spec-draft-0.2` and `bytecode-v1`, over all 105 commits. In every commit it changed only two blobs:
- **the design notes,** at both of the paths they had: the paragraph that named the third-party platform is removed;
- **the VM7 plan,** at both of its paths: the two absolute paths to the llvm-mingw folder now read `<workspace>\…`, as PR7 had already done for the current tree.

**Checked:**
- each of the 105 new commits differs from its original only in those files;
- authors, dates and messages are unchanged;
- the platform's name and the user name appear nowhere in the new history, neither in files nor in messages;
- the last commit's tree is identical.

**Consequences:**
- every commit hash has changed. The "committed as `abc1234`" notes in the plans name the old hashes;
- the old history is kept locally in `refs/original/`, and in a bundle in the session's scratch folder, until the remote is updated;
- the remote still has the old history. It is replaced by a force-push, which is the user's step.
