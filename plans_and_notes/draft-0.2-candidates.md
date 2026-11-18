# Draft 0.2 — candidate language changes

Status: open list (started 2026-11-18). Items here are candidates, not decisions. Each one becomes an open issue in Annex C when it is taken up, and is decided there.

Changes already made after Draft 0.1, for reference: OI-45 (`attempt` and `require` abort a transaction), OI-46 to OI-51 (WP1: intrinsics and platform APIs, slice assignment, `equal`, `compare`, `wipe`, security expectations, the capacity model withdrawn), and OI-52 (PLT-33 and derived secrets).

| # | Candidate | Origin | Notes |
|---|---|---|---|
| 1 | **Session boundaries defined by the transport binding.** Session state and volatile resources are tied to *power-on* and *security reset* (STA-4, RTF-9, BP-14). That is card-centric. In a TEE (for example TrustZone-M), power-on is device boot, and clients open and close sessions many times between boots. Proposal: STA-4 and the related rules say "at every session start, as the platform's binding defines it", and the ISO 7816 binding defines session start as power-on and security reset | Review of the transport bindings (WP7), 2026-11-18 | Affects STA-4, RTF-9, RTF-12, STA-14, BP-14, BP-55, and the `power_on` scenario step. The language change is small, but it touches several chapters |
| 2 | **No calls inside call arguments (EXP-49).** This forces temporaries, for example `truncate<u8>(compare(ref a, ref b))` is rejected | Review of Draft 0.1, 2026-11-17 | Revisit with the evidence from WP8 |
| 3 | **A standard envelope for the raw binding.** The host-side encoding of the (category, code) pair is platform-defined (BP-53), so host software is not portable between raw platforms | WP7 review | A profile change, not a language change, if taken up |
| 4 | **A user-presence API** for platforms with a button or sensor. BP-54 covers only contactless interfaces | WP7 review | A profile change |
| 5 | **Findings from the FIDO2 check (WP8)** | WP8 | To be filled in from `plans_and_notes/WP8-fido2-findings.md` |
