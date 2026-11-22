# The CardLang language definition

This folder holds what CardLang *is*: the specification, the tests that pin it down, and the reasoning behind it. The platform profile, which says what a card platform provides to programs, is a separate specification in [`platform/`](../platform/base-profile.md). The VM, which runs compiled programs, is in [`vm/`](../vm/README.md).

| Folder | What it is |
|---|---|
| [`spec/`](spec/00-index.md) | **The specification, and the only normative part.** Chapters 1–13 give the language's rules, each with an ID such as `EXP-6` and the sources it comes from. Annex A is the grammar, Annex B the contract a platform must meet, Annex C the open issues and their resolutions, and Annex D the traceability from rules to decisions and tests |
| [`conformance/`](conformance/README.md) | **The conformance suite.** `valid/` programs must be accepted, `invalid/` programs must be rejected with the compile error each one names, and `runtime/` scenarios run programs and check their responses. Every example in the specification is one of these tests |
| [`rationale/`](rationale/) | **Why the language is as it is.** The design notes record the discussion the rules came from, the platform notes the early thinking on the platform boundary, and the decision register the decisions with the IDs that rules cite. They are a record and are not normative |
| [`releases/`](releases/) | **What changed in each draft,** and the candidates for the next one |

**Where to start:**
- **To learn the language,** read [the index](spec/00-index.md), then chapter 1 for the conventions, then the chapters in order. The examples at the end of each section are short, complete programs.
- **To implement it,** read the specification and run the conformance suite against your implementation. [`conformance/README.md`](conformance/README.md) describes the test format.
- **To see why a rule is as it is,** follow its Sources line to the decision register and the design notes.

When the specification and anything else disagree, including the rationale, the tools or the VM, the specification wins.
