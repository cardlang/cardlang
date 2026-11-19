# Draft 0.2 — candidate language changes

Status: open list (started 2026-11-18). Items here are candidates, not decisions. Each one becomes an open issue in Annex C when it is taken up, and is decided there.

Changes already made after Draft 0.1, for reference: OI-45 (`attempt` and `require` abort a transaction), OI-46 to OI-51 (WP1: intrinsics and platform APIs, slice assignment, `equal`, `compare`, `wipe`, security expectations, the capacity model withdrawn), and OI-52 (PLT-33 and derived secrets).

| # | Candidate | Origin | Notes |
|---|---|---|---|
| 1 | **Session boundaries defined by the transport binding.** Session state and volatile resources are tied to *power-on* and *security reset* (STA-4, RTF-9, BP-14). That is card-centric. In a TEE (for example TrustZone-M), power-on is device boot, and clients open and close sessions many times between boots. Proposal: STA-4 and the related rules say "at every session start, as the platform's binding defines it", and the ISO 7816 binding defines session start as power-on and security reset | Review of the transport bindings (WP7), 2026-11-18 | Affects STA-4, RTF-9, RTF-12, STA-14, BP-14, BP-55, and the `power_on` scenario step. The language change is small, but it touches several chapters |
| 2 | **No calls inside call arguments (EXP-49).** This forces temporaries, for example `truncate<u8>(compare(ref a, ref b))` is rejected | Review of Draft 0.1, 2026-11-17 | Revisit with the evidence from WP8 |
| 3 | **A standard envelope for the raw binding.** The host-side encoding of the (category, code) pair is platform-defined (BP-53), so host software is not portable between raw platforms | WP7 review | A profile change, not a language change, if taken up |
| 4 | **A user-presence API** for platforms with a button or sensor. BP-54 covers only contactless interfaces | WP7 review | A profile change |
| 5 | **Done in WP9 (OI-53).** **Byte-string literals** (`b"public-key"` checking against `u8[N]`) | WP8 L1 | The strongest readability finding |
| 6 | **Done in WP9 (OI-54).** **Reading an application error's code** (`code_of(e)`), so errors can be translated without one match arm per member | WP8 L2 | Related to the one-error-set rule (L3) |
| 7 | **Several error sets**, or binding-local ones | WP8 L3 | Changes OUT-16 |
| 8 | **Done in WP9 (OI-55).** **`attempt c else E.M`**: map any `Err` to an application error | WP8 L4 | Analogous to `require` |
| 9 | **Done in WP9 (OI-56).** **A short form for discarding an outcome** (`ignore c;`) | WP8 L5 | |
| 10 | **Done in WP9 (OI-57).** **Compound assignment** (`+=`, deferred in STM-6) | WP8 L6 | |
| 11 | **Dropped (2026-11-19).** **A block-scoped view binding** | WP8 L7 | Dropped: a helper function taking `ref u8[]` does the same with no language change, and the binding would add a keyword, a scoping rule and aliasing interactions (FUN-12 to FUN-15) |
| 12 | **Done (BP-14, BP-24).** **Command-lifetime keys** (`KeyStorage.Command`) | WP8 P1 | A profile change |
| 13 | **Done (BP-39).** **`card.cbor.write_string`** | WP8 P2 | A profile change |

Evidence against changing a rule: WP8 L8 found that EXP-49 and the mixed-operator rule cost little in a real applet. Item 2 (EXP-49) therefore has weaker support than it seemed.

| 14 | **Done, differently (OI-58, PLT-35).** Not `defer`, but a platform obligation: a frame's locals are erased when it ends, traps included | WP8 L10 (after WP9) | `defer` could not cover traps |
| 15 | **`card.cbor.write_bool`** | WP8 N3 | A profile change |
| 16 | **`fill` in constant initializers**, to check first | WP8 N5 | A language check, possibly a change |
| 17 | **Exporting a key's material encrypted under another key** (limited wrap), so secrets like the PIN token need not sit in session state | WP8 N6 | A profile change; later |
