"""One-off generator for SP0: decision register + Annex D reverse table.

Topic/status cells are copied verbatim from DN section 2 (lines 28-162).
"""
import sys, pathlib
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "checkers"))   # find layout
import layout

repo = pathlib.Path(sys.argv[1])
dn = (layout.at(repo).design_notes).read_text(encoding="utf-8").splitlines()
rows = dn[27:162]  # lines 28..162 (1-based)
assert len(rows) == 135, len(rows)
cells = []
for i, line in enumerate(rows, 1):
    assert line.startswith("| ") and line.endswith(" |") and line.count("|") == 3, (i, line)
    topic, status = [c.strip() for c in line[1:-1].split("|")]
    cells.append((topic, status))

A, P = "[Agreed]", "[Proposal]"
L, PL, VM = "language", "platform", "VM/profile"
# id: (tag, layer, sections, owning SP, linked OI)
M = {
1: (A, L, "DN §1", "SP0", ""),
2: (A, L, "DN §1", "SP0", ""),
3: (A, L, "DN §5.1", "SP2", ""),
4: (A, L, "DN §5.1", "SP9", ""),
5: (A, L, "DN §5.1, §3.10", "SP4", ""),
6: (A, L, "DN §5.1", "SP6", ""),
7: (A, L, "DN §5.1", "SP2", ""),
8: (A, L, "DN §5, §5.1", "SP9", "OI-16"),
9: (A, PL, "DN §5", "SP13", "OI-17"),
10: (A, L, "DN §6.1, §6.4", "SP8", ""),
11: (A, L, "DN §6.1", "SP8", ""),
12: (A, L, "DN §6.1, §6.3", "SP8", "OI-18"),
13: (A, L, "DN §3.6, §6.1", "SP8", ""),
14: (A, L, "DN §6.3", "SP8", ""),
15: (A, L, "DN §6.3", "SP8", ""),
16: (A, L, "DN §6.3", "SP8", ""),
17: (A, L, "DN §6.3", "SP8", ""),
18: (A, L, "DN §6.3", "SP8", "OI-13"),
19: (A, L, "DN §6.3", "SP8", ""),
20: (A, L, "DN §1, §4.1; PN §1", "SP2", ""),
21: (A, L, "DN §3.0, §4.1", "SP2", ""),
22: (A, L, "DN §3.0, §4.1", "SP2", ""),
23: (A, L, "DN §1, §3.0", "SP1", "OI-1"),
24: (A, L, "DN §3.0", "SP1", ""),
25: (A, L, "DN §3.0, §3.7, §4", "SP7", ""),
26: (A, L, "DN §3.7", "SP7", ""),
27: (A, L, "DN §3.7", "SP5", ""),
28: (A, L, "DN §6.3", "SP8", ""),
29: (A, L, "DN §3.10", "SP4", "OI-11"),
30: (A, L, "DN §3.7", "SP6", ""),
31: (A, L, "DN §3.7", "SP7", ""),
32: (A, L, "DN §3.7", "SP7", ""),
33: (A, L, "DN §3.7", "SP7", ""),
34: (A, L, "DN §3.6, §3.7", "SP6", ""),
35: (A, L, "DN §3.7, §4.1", "SP11", ""),
36: (A, L, "DN §3.0, §3.3", "SP1", "OI-14"),
37: (A, L, "DN §3.0", "SP1", ""),
38: (A, L, "DN §4.1", "SP2", ""),
39: (A, L, "DN §4.1", "SP2", ""),
40: (A, L, "DN §4.1, §4.2", "SP2", ""),
41: (A, L, "DN §4", "SP11", "OI-5"),
42: (A, L, "DN §4", "SP11", ""),
43: (A, PL, "DN §4, §6.3; PN §5", "SP13", "OI-2"),
44: (A, L, "DN §4.1, §4.2", "SP2", "OI-4"),
45: (A, L, "DN §4.2", "SP2", ""),
46: (A, L, "DN §4.2", "SP2", ""),
47: (A, L, "DN §4.2", "SP2", ""),
48: (A, L, "DN §3.6, §4.2", "SP2", ""),
49: (A, L, "DN §4", "SP11", ""),
50: (A, L, "DN §3.9, §6.4", "SP9", ""),
51: (A, L, "DN §6.4", "SP12", ""),
52: (A, PL, "DN §6.4, §11.2; PN §2", "SP13", ""),
53: (A, L, "DN §6.4", "SP12", ""),
54: (A, L, "DN §6.4", "SP12", ""),
55: (A, L, "DN §7.2", "SP10", ""),
56: (A, PL, "DN §6.4; PN §3", "SP13", ""),
57: (A, L, "DN §7.1, §7.4", "SP9", "OI-19"),
58: (A, L, "DN §6.2, §6.5", "SP5", ""),
59: (A, L, "DN §8, §8.2", "SP3", ""),
60: (A, L, "DN §8", "SP3", ""),
61: (A, L, "DN §8.1", "SP5", ""),
62: (A, L, "DN §8.1", "SP5", ""),
63: (A, L, "DN §8", "SP5", ""),
64: (A, L, "DN §8", "SP5", ""),
65: (A, L, "DN §9, §9.3", "SP3", ""),
66: (A, L, "DN §9.3", "SP3", ""),
67: (A, L, "DN §3.11", "SP3", ""),
68: (A, L, "DN §3.11", "SP3", ""),
69: (A, L, "DN §3.11, §3.6", "SP6", ""),
70: (A, L, "DN §9.3", "SP5", ""),
71: (A, L, "DN §9", "SP5", ""),
72: (A, L, "DN §9.1", "SP3", ""),
73: (A, L, "DN §9.1", "SP3", ""),
74: (A, L, "DN §9.1, §9.3", "SP3", ""),
75: (A, L, "DN §3.1", "SP3", ""),
76: (A, L, "DN §3.1, §8", "SP3", "OI-12"),
77: (A, L, "DN §8.2", "SP3", ""),
78: (A, L, "DN §8.2", "SP6", ""),
79: (A, L, "DN §8.3", "SP5", ""),
80: (A, L, "DN §8.2", "SP6", "OI-9"),
81: (A, L, "DN §3.2", "SP5", ""),
82: (A, L, "DN §3.2, §3.5", "SP5", ""),
83: (A, L, "DN §3.2", "SP5", ""),
84: (A, L, "DN §3.3", "SP5", "OI-14"),
85: (A, L, "DN §3.3, §8.1", "SP5", ""),
86: (A, L, "DN §3.3", "SP5", ""),
87: (A, L, "DN §3.3", "SP5", ""),
88: (A, L, "DN §3.5, §6.5", "SP5", ""),
89: (A, L, "DN §6.5", "SP5", ""),
90: (A, L, "DN §6.5", "SP5", ""),
91: (A, L, "DN §6.5", "SP5", "OI-13"),
92: (A, L, "DN §6.5", "SP5", ""),
93: (A, L, "DN §3.10, §6.5", "SP4", ""),
94: (A, L, "DN §3.10", "SP4", ""),
95: (A, L, "DN §3.10", "SP4", ""),
96: (A, L, "DN §3.10", "SP4", ""),
97: (P, L, "DN §3.10", "SP4", "OI-11"),
98: (A, L, "DN §3.10", "SP4", ""),
99: (A, L, "DN §3.10", "SP4", ""),
100: (A, L, "DN §3.4", "SP3", ""),
101: (A, L, "DN §3.2", "SP5", ""),
102: (A, L, "DN §3.5", "SP5", ""),
103: (A, L, "DN §3.5", "SP5", ""),
104: (A, L, "DN §3.5", "SP5", ""),
105: (A, L, "DN §3.5", "SP6", ""),
106: (A, L, "DN §3.6", "SP6", ""),
107: (A, L, "DN §3.6, §3.7", "SP8", ""),
108: (A, L, "DN §3.6", "SP8", ""),
109: (A, L, "DN §3.6, §7.2", "SP10", ""),
110: (A, L, "DN §7.2", "SP10", ""),
111: (A, L, "DN §7.2", "SP10", ""),
112: (A, L, "DN §3.7", "SP7", ""),
113: (A, L, "DN §3.7", "SP7", ""),
114: (A, L, "DN §3.7, §3.8", "SP7", ""),
115: (A, L, "DN §3.7, §3.8", "SP7", ""),
116: (A, L, "DN §3.8", "SP7", ""),
117: (A, L, "DN §3.8", "SP7", ""),
118: (A, L, "DN §3.8, §8.4", "SP7", ""),
119: (A, L, "DN §8.4", "SP7", "OI-10"),
120: (A, L, "DN §8.4", "SP7", ""),
121: (A, L, "DN §8.4", "SP7", ""),
122: (A, L, "DN §3.9", "SP9", ""),
123: (A, L, "DN §3.9", "SP9", ""),
124: (A, L, "DN §3.9; PN §3", "SP9", "OI-7"),
125: (A, PL, "DN §11.2; PN §2", "SP13", ""),
126: (A, PL, "DN §11.2; PN §2", "SP13", ""),
127: (A, PL, "DN §11.2; PN §2", "SP13", "OI-20"),
128: (A, L, "DN §3.9", "SP9", ""),
129: (A, L, "DN §3.9, §3.10", "SP4", ""),
130: (A, L, "DN §3.9, §9.3", "SP5", ""),
131: (A, L, "DN §7.3", "SP10", "OI-3"),
132: (A, L, "DN §7.3", "SP10", ""),
133: ("[Agreed] / [Proposal] (placement)", VM, "DN §3.8; PN §4", "SP13", "OI-21"),
134: (P, L, "DN §3", "SP0", ""),
135: (P, VM, "PN §4", "SP13", ""),
}
assert set(M) == set(range(1, 136))

# PN-only agreed items (not covered by a DN §2 row). Summaries, not verbatim.
PN_ITEMS = [
("No opaque platform value types; platform APIs use ordinary value types, with fully visible platform-supplied configuration structures and algorithm enums", A, PL, "PN §2; DN §11.1", "SP13", ""),
("Every resource operation validates existence, kind, state and permissions in the caller's resource space; wrong kind is a defined recoverable error; identifiers never authorize cross-application access", A, PL, "PN §2; DN §11.1", "SP13", ""),
("Resource operation outcomes: create on existing ID fails recoverably (never replaces); unknown ID and wrong kind fail recoverably; capacity failure is a defined recoverable error; failed creation exposes no partial object (error names are placeholders)", A, PL, "PN §2; DN §11.2", "SP13", "OI-15"),
("Copying a resource identifier copies only the number; no stale-handle detection; identifier-variable lifetime is independent of resource lifetime", A, PL, "PN §2; DN §11.2", "SP13", ""),
("Language transactions do not automatically cover resource-API effects; each API must define its transaction participation or prohibit use during a transaction", A, PL, "PN §2, §5; DN §7.2", "SP13", ""),
("Exceeding a runtime stack/execution limit traps; exceeding build/load capacity may reject the application; limits must not silently change language semantics", A, L, "PN §4; DN §12", "SP12", ""),
("Commit failure never resumes after the block; a contained failure traps, an integrity failure triggers security reset; recovery exposes all or none of a transaction and fails closed", A, L, "PN §5; DN §7.2", "SP10", ""),
("The platform must prevent any other execution context (callbacks, reentrant commands) from observing partially updated transactional state", A, PL, "PN §5", "SP13", ""),
("Published application/platform error-code meanings remain stable; codes are nonzero u16 values in separate categories", A, L, "PN §5; DN §6.3", "SP12", "OI-15"),
]

hdr = "| ID | Topic | Recorded status | Spec tag | Layer | Detail sections | Owning SP | Linked OI | Implemented by |\n|---|---|---|---|---|---|---|---|---|\n"
out = []
for i, (topic, status) in enumerate(cells, 1):
    tag, layer, sec, sp, oi = M[i]
    out.append(f"| D-{i:03d} | {topic} | {status} | {tag} | {layer} | {sec} | {sp} | {oi} | pending |")
pn = []
for j, (topic, tag, layer, sec, sp, oi) in enumerate(PN_ITEMS, 201):
    pn.append(f"| D-{j} | {topic} | (summary; see sources) | {tag} | {layer} | {sec} | {sp} | {oi} | pending |")

register = f"""# CardLang decision register

Status: maintained by the specification sub-plans (see `specification-plan-of-plans.md`).
Created by SP0.

This register gives every recorded design decision a stable ID. Spec rules cite these IDs, and `spec/annex-D-traceability.md` maps each ID back to the rules that implement it.

## Sources and citation

- **DN**: `plans_and_notes/card-language-design-notes.md`, revision of 2026-11-15.
- **PN**: `plans_and_notes/cardlang-platform-notes.md`, dated 2026-11-14.
- Sections are cited as `DN §n.n` or `PN §n`.

## ID ranges

| Range | Content |
|---|---|
| `D-001`…`D-135` | The rows of the DN §2 decision table, in table order. The Topic and Recorded status columns are copied verbatim |
| `D-201`… | Agreed items stated in PN and not covered by a DN §2 row. These are summaries, not verbatim text |
| `D-301`… | Agreed decisions stated only in DN body sections. Later sub-plans add them as they reach each section |

IDs are never reused or renumbered. A withdrawn decision keeps its row, marked "withdrawn".

## Columns

- **Spec tag**: how the decision is tagged when it becomes a rule. The mapping follows the DN header (line 10): an "agreed direction" records an explicit decision, so it is [Agreed]; a "proposal" is an idea still to validate, so it is [Proposal]. When a status carries an open qualifier (for example "detailed semantics open"), the stated part is [Agreed] and the qualifier becomes the linked open issue.
- **Layer**:
  - `language` decisions become chapter rules.
  - `platform` decisions become Annex B `PLT-n` requirements or platform-defined items.
  - `VM/profile` decisions are informative material in Annex B.
- **Owning SP**: the sub-plan that turns the decision into rules.
- **Linked OI**: the open issue in `spec/annex-C-open-issues.md` for a qualifier, contradiction or gap.
- **Implemented by**: rule IDs, filled in by the owning sub-plan. `pending` means not yet specified.

D-134 ("Familiar imperative syntax, static types", a proposed baseline) is cited as informative design intent in `spec/01-scope-and-conventions.md`. The concrete agreed rows supersede it wherever they are more specific.

## DN §2 decisions

{hdr}{chr(10).join(out)}

## Platform-notes items (D-201…)

{hdr}{chr(10).join(pn)}

## DN body-only decisions (D-301…)

None registered yet. Sub-plans SP1–SP13 add rows here as they reach each DN section.

{hdr.rstrip()}
"""
(layout.at(repo).decision_register).write_text(register, encoding="utf-8", newline="\n")

rev = ["| D-ID | Topic (short) | Owning SP | Rule IDs | Linked OI | Coverage |", "|---|---|---|---|---|---|"]
for i, (topic, _s) in enumerate(cells, 1):
    tag, layer, sec, sp, oi = M[i]
    rev.append(f"| D-{i:03d} | {topic} | {sp} | — | {oi} | pending |")
for j, (topic, tag, layer, sec, sp, oi) in enumerate(PN_ITEMS, 201):
    short = topic.split(";")[0]
    rev.append(f"| D-{j} | {short} | {sp} | — | {oi} | pending |")
(pathlib.Path(sys.argv[2])).write_text("\n".join(rev) + "\n", encoding="utf-8", newline="\n")
print("rows", len(cells), "pn", len(PN_ITEMS))
