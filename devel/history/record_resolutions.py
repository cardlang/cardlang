"""Record the 2026-11-15 open-issue resolutions in Annex C, the register and Annex D."""
import re, sys, pathlib
from cardlang import layout

repo = pathlib.Path(sys.argv[1])
DATE = "2026-11-15"

# OI number: (decision text, layer, owning SP, short title for register)
R = {
1: ("Option (a). `.card` is the normative source file extension. The DN §1 sentence is stale on this point. The compiler executable name stays unfixed (tooling).", "language", "SP1", "Source file extension is `.card`"),
2: ("Option (a). The PN §1 \"dispatch, command identifiers\" row is superseded: there is no platform dispatch within an application, and every request enters the single entry point. Selecting between isolated applications remains a platform matter. The notes themselves are not edited.", "platform", "SP13", "No platform dispatch within an application; PN §1 row superseded"),
3: ("Option (a). Nesting is always detected statically and structurally: it is a compilation error if a `transaction` block can reach a `transaction` statement lexically or through any function it calls, directly or transitively, on the static acyclic call graph. This also rejects paths that are never taken. The runtime check remains only as a VM safety net that a verified program never triggers.", "language", "SP10", "Nested transactions rejected statically by a structural call-graph rule"),
4: ("Recommendation adopted.\n  - Keywords: `persistent session const var function command struct enum errors transaction abort attempt require else if while for in match return break continue true false not and or ref inout Ok Err`.\n  - The intrinsic names (`fill`, `convert`, `checked_convert`, `checked_add`/`sub`/`mul`/`div`/`rem`/`neg`, `wrapping_add`/`sub`/`mul`) are reserved identifiers that cannot be declared or shadowed.\n  - `card` and `CardError` are reserved; other platform names are platform-defined.\n  - No speculative words are reserved.\n  - `length` remains usable as a field name.", "language", "SP1", "Keyword list; Ok/Err keywords; intrinsics and card/CardError reserved"),
5: ("Option (a). The single `command` declaration is the host entry point, and its name is chosen by the application.", "language", "SP11", "Entry point is the single `command` declaration, any name"),
6: ("Option (a). Platform API names use a distinct syntactic form: the reserved root `card` followed by `.` segments. It resolves only against the platform API catalog and is never a field access.", "language", "SP2", "Platform API calls use the reserved `card.` path form"),
7: ("Option (b), chosen over the recommendation. Lifecycle handlers are functions with platform-reserved names and signatures. The platform specification supplies the names, signatures and events. The remaining language-side questions are tracked as OI-22.", "platform", "SP9", "Lifecycle handlers use platform-reserved function names/signatures"),
8: ("Option (a). `attempt call` may appear in any runtime expression position, except inside a call argument, in a constant expression, or where its failure return would cross a transaction boundary. In the right operand of `and`/`or` it runs only if that operand is evaluated.", "language", "SP5", "`attempt` allowed in any runtime expression position, with three exclusions"),
9: ("Option (a). The whole destination path is evaluated left to right first, with each index evaluated once and bounds-checked as it is reached. Then the right-hand side is evaluated, then the value is stored.", "language", "SP6", "Assignment: destination path first, then RHS, then store"),
10: ("All proposed defaults adopted:\n  1. Endpoints use the index types `u8`/`u16`/`u32`, typed independently; literal-only endpoints get `u32` context.\n  2. Evaluation order: receiver, then start, then end; then the checks `start ≤ end` and `end ≤ length`.\n  3. No omitted endpoints; slices appear only as reference arguments and receivers.\n  4. A slice never satisfies a fixed-size `T[N]` parameter.\n  5. No whole-slice copy or fill assignment.", "language", "SP7", "Slice endpoint typing, order, positions and limits fixed"),
11: ("Adopted. The six-step structural evaluation algorithm in DN §3.10, with its acceptance table, is normative. For question 2, option (a): a constant-only index that is out of range for an array whose length is known from its type is a compilation error, even when the array is in mutable storage.", "language", "SP4", "Constant-evaluation algorithm normative; constant OOB index is a compile error"),
12: ("Option (b). `byte` is not adopted in Draft 0.1.", "language", "SP3", "No `byte` alias in Draft 0.1"),
13: ("1(a): an application declares at most one error set, and zero are allowed. 2(a): outcome-producing intrinsics follow the same consumption rules as calls, including whole-outcome forwarding when payload types match.", "language", "SP8", "Zero or one error set; intrinsic outcomes may be forwarded"),
14: ("Recommendation adopted:\n  - `0x` and `0b` prefixes are lowercase only.\n  - Hex digits are case-insensitive.\n  - A prefix with no digits, or a digit outside the base, is a lexical error.\n  - The lexer does not limit magnitude; range is a typing error at the literal's expected type.", "language", "SP1", "Literal prefix, digit and magnitude rules"),
15: ("Adopted. Chapters use the language-level trap kinds `TRAP-OVERFLOW`, `-UNDERFLOW`, `-DIV-ZERO`, `-BOUNDS`, `-SHIFT`, `-NEGATION`, `-RESPONSE-COUNT`, `-NESTED-TXN`, `-COMMIT`, `-EXHAUSTED` and `-VM`, and the placeholder platform errors `CardError.Overflow`, `.Underflow`, `.DivisionByZero`, `.ConversionRange`, `.AlreadyExists`, `.NotFound`, `.WrongResourceType` and `.Capacity`. All codes are platform-defined. SP12 and SP13 confirm or replace the names.", "language", "SP12", "Trap-kind and placeholder platform-error names"),
16: ("Recommendation adopted. The language covers declaration, defaults, atomic assignment and transactions. Persistent-state deletion, upgrade and migration are platform-defined items (Annex B).", "platform", "SP9", "Persistent deletion/upgrade/migration are platform-defined"),
17: ("Recommendation adopted. The object API for larger persistent data is a future platform API, outside Draft 0.1. Annex B lists it as future work.", "platform", "SP13", "Large-data object API is future platform work"),
18: ("Recommendation adopted. \"Detailed typing open\" is settled by DN §6.3 (transient outcomes, no `Result<T>`, exact `attempt` typing). SP8 formalizes it.", "language", "SP8", "Outcome typing settled by DN §6.3"),
19: ("Option (a). A persistent aggregate assignment larger than the target can update atomically causes the application to be rejected at build or load time for that target profile. It never becomes non-atomic. The limit values are platform-defined.", "language", "SP9", "Oversized atomic aggregate assignment rejected at build/load time"),
20: ("Recommendation adopted. Resource storage strategy is a platform-defined item in Annex B, with no language impact.", "platform", "SP13", "Resource storage strategy is platform-defined"),
21: ("Recommendation adopted. The language rule is value semantics: an independent copy that lives for the call. Call-frame placement is informative VM guidance in Annex B.", "VM/profile", "SP13", "Call-frame placement is informative VM guidance"),
}

# ---------- Annex C ----------
p = layout.at(repo).spec / "annex-C-open-issues.md"
t = p.read_text(encoding="utf-8")
for n, (dec, *_r) in R.items():
    hdr = f"## OI-{n} "
    start = t.index(hdr)
    end = t.find("\n## ", start + 1)
    sec = t[start:end]
    assert sec.count("- **Status:** open") == 1, n
    sec = sec.replace("- **Status:** open", f"- **Status:** resolved {DATE} (D-{400+n})\n- **Decision:** {dec}")
    t = t[:start] + sec + t[end:]
    t, k = re.subn(rf"^(\| OI-{n} \|.*\| )Open \|$", rf"\g<1>Resolved |", t, flags=re.M)
    assert k == 1, n

oi22 = f"""## OI-22 — Language rules for lifecycle handler functions

- **Kind:** gap, opened by the OI-7 resolution
- **Sources:** OI-7 resolution (D-407); DN §3.9; PN §3
- **Affected rules:** pending (SP9)
- **Questions:**
  1. May application code call a lifecycle handler function directly?
  2. Do handlers follow all ordinary-function rules (always produce an outcome, may not recurse, and so on), with only the name and signature fixed by the platform?
  3. Are the handler names reserved even when the application does not define them, and is defining a handler optional?
- **Recommendation:**
  1. No. This mirrors the rule that application code cannot call the `command`.
  2. Yes.
  3. Reserved always; optional unless the platform requires a particular handler.
- **Status:** open

---

## Resolution log"""
t = t.replace("---\n\n## Resolution log", oi22, 1)
t = t.replace("| OI-21 | Call-frame placement of by-value aggregates | Qualifier (proposal) | SP13 | Resolved |",
              "| OI-21 | Call-frame placement of by-value aggregates | Qualifier (proposal) | SP13 | Resolved |\n| OI-22 | Language rules for lifecycle handler functions | Gap | SP9 | Open |")
log = [f"| {DATE} | OI-{n} | {R[n][3]} (D-{400+n}) | User | Pending: applied when {R[n][2]} drafts its chapter |" for n in R]
t = t.replace("| — | — | No resolutions yet | — | — |", "\n".join(log))
p.write_text(t, encoding="utf-8", newline="\n")

# ---------- Register ----------
p = layout.at(repo).decision_register
t = p.read_text(encoding="utf-8")
t = t.replace("| `D-301`… | Agreed decisions stated only in DN body sections. Later sub-plans add them as they reach each section |",
              "| `D-301`… | Agreed decisions stated only in DN body sections. Later sub-plans add them as they reach each section |\n| `D-401`… | Decisions made by resolving open issues. `D-4nn` resolves `OI-nn` (see the Annex C resolution log) |")
t, k = re.subn(r"^(\| D-097 \|(?:[^|]*\|){2}) \[Proposal\] \|", r"\1 [Agreed] (via D-411) |", t, flags=re.M); assert k == 1
t, k = re.subn(r"^(\| D-133 \|(?:[^|]*\|){2}) \[Agreed\] / \[Proposal\] \(placement\) \|", r"\1 [Agreed]; placement informative (D-421) |", t, flags=re.M); assert k == 1
hdr = "| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |\n|---|---|---|---|---|---|---|---|---|\n"
rows = [f"| D-{400+n} | {R[n][3]} | Resolved by user {DATE} | [Agreed] | {R[n][1]} | Annex C OI-{n} | {R[n][2]} | OI-{n} | pending |" for n in R]
t = t.rstrip("\n") + f"\n\n## Open-issue resolutions (D-401…)\n\n{hdr}" + "\n".join(rows) + "\n"
p.write_text(t, encoding="utf-8", newline="\n")

# ---------- Annex D ----------
p = layout.at(repo).spec / "annex-D-traceability.md"
t = p.read_text(encoding="utf-8").rstrip("\n")
t += "\n" + "\n".join(f"| D-{400+n} | {R[n][3]} | {R[n][2]} | — | OI-{n} | pending |" for n in R) + "\n"
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
