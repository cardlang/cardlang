# WP1 — Language changes for the base API: detailed sub-plan

Parent: `plans_and_notes/base-api-plan.md` (decisions B1 and B9).
Status: decisions D1–D5 taken 2026-11-17 (§4). **Phase A drafted 2026-11-17**: items 1–5 (EXP-52 to EXP-54, STM-23, FUN-24, PLT-30 to PLT-34, OI-46 to OI-50). **Item 6 (the capacity model, §2.6) was withdrawn on 2026-11-17 (OI-51, D-451).** Only a small amendment to STA-13, FUN-24, STM-23 and RTF-4 was made instead. WP1 is complete.

## 1. Scope

WP1 makes the Draft 0.2 **language** changes that the base platform API needs. The API itself is WP2 to WP7, in `platform/`. WP1 has six items:

| # | Change | Decided by |
|---|---|---|
| 1 | Rules that say what is an intrinsic and what is a platform API | Base plan §2 |
| 2 | Slice assignment, for moving array data | B1(a), B1(c) |
| 3 | The `equal` and `compare` intrinsics | B1(b) |
| 4 | Wiping secrets, so that a compiler can never remove the write | Base plan §3.3 |
| 5 | Security expectations for platforms, as a new Annex B section | Base plan §3.3 |
| 6 | The capacity model: logical size, transaction footprint, capacity classes | B9 |

Each change becomes an open issue in Annex C (OI-46 onwards), resolved by a decision (D-446 onwards) that cites the base-plan decision. The decisions this plan still needs are in §4.

## 2. Rules to write or amend

### 2.1 Intrinsic or platform API (item 1)

- **New EXP rule in §6.6.** It gives the definition of an intrinsic: the language defines it completely over language values, it is deterministic and portable, and it fails only by a compile error or a trap. Intrinsics are predeclared names (NAM-14) and are never reached through a `card.` path.
- **New PLT rule in Annex B §B.8.** It defines a platform API as the complement: it depends on platform state or hardware, fails with `CardError`, states its transaction behaviour, and may be missing on some platforms. A platform must not offer, as an API, an operation the language already provides as an intrinsic.

### 2.2 Slice assignment (item 2)

- **Allowed form.** `place[s..e] = source;` becomes valid when `place` is an assignable place (STM-7) of type `T[N]` or an `inout` view `T[]`.
- **Rule changes.**
  - FUN-18 lists the left side of an assignment as a permitted position for a slice.
  - STM-7 removes "a slice" from its list of forbidden left sides.
  - FUN-18 keeps "a slice on the right side is valid only as the source of a slice assignment" (D1).
- **Typing.** The source has element type `T`. Its length must equal `e − s`. D1 settles the error class when both lengths are known at compile time.
- **Evaluation**, extending STM-9:
  1. evaluate the place's path and both endpoints, and check the region (FUN-20);
  2. evaluate the source;
  3. check that the lengths are equal, otherwise `trap(BOUNDS)`;
  4. copy as if through a temporary, so overlapping regions behave like `memmove`.
- **Persistence.** A slice assignment into persistent storage is one persistent assignment. It is atomic for the whole region (STA-11). Its logical size counts against the atomic minimum (STA-13 as amended in §2.6), and it participates in an active transaction.

### 2.3 `equal` and `compare` (item 3)

| Intrinsic | Type | Meaning |
|---|---|---|
| `equal(ref a, ref b)` | `bool` | The lengths are equal and every element is equal under `==` |
| `compare(ref a, ref b)` | `i8` | Lexicographic order: −1, 0 or 1. A proper prefix sorts first |

- **Arguments.** Both arguments are `ref` arguments: a fixed array, a view or a slice (FUN-18 adds these intrinsics to the positions where slices are allowed). The element types must be identical. D2 settles which element types are allowed.
- **No failure.** They produce a value directly, like `convert`. They never fail and never trap, because they index nothing out of range.
- **Constant time.** For `equal`, Annex B requires (§2.5) that the time depend only on the two lengths, never on the contents. `compare` has no such requirement.
- **Naming.** `equal` and `compare` join the reserved intrinsic names (LEX-15, NAM-14).

### 2.4 Wiping (item 4)

EXP-22 lets an implementation remove a write that nothing observes. That includes a zeroizing `fill` of a buffer that is about to go out of scope, which is exactly the write a security engineer needs. D3 settles the form. My recommendation is a statement, `wipe place;`:
- it stores `default(T)` into the whole place, which may be a slice;
- the store is never removed, reordered after the end of the place's lifetime, or merged away. This is an explicit exception to EXP-22;
- for persistent storage it is an ordinary atomic persistent assignment (STA-11), and it participates in transactions.

`wipe` becomes a keyword (LEX-14 and the keyword table), and the grammar gains a `WipeStatement`.

### 2.5 Security expectations (item 5): new Annex B §B.13

These are PLT rules, obligations on a platform rather than language rules:

- **Constant time.** `equal` and every cryptographic API execute in time independent of secret data: key material, plaintext, and the contents compared by `equal`.
- **Side channels and faults.** The platform protects against side-channel and fault-injection attacks to the level stated in its target profile. The level itself is platform-defined, and it is added to the B.12 checklist.
- **Key material.** Secret and private key material never appears in memory the application can see. Only public keys can be exported (B4).
- **`wipe`.** The platform executes `wipe` stores as written, including on volatile memory about to be released.

### 2.6 The capacity model (item 6)

- **Logical size.** A new rule in chapter 4 defines a logical size for every value type, computed from its type. It is a counting rule only, and TYP-9 still holds.

  | Type | Logical size |
  |---|---|
  | `u8`, `i8`, `bool` | 1 |
  | `u16`, `i16` | 2 |
  | `u32`, `i32` | 4 |
  | Enum | D4 |
  | `T[N]` | `N` × size(`T`) |
  | Structure | Sum of its fields' sizes |

- **Transaction footprint.** A new rule in chapter 11, with two parts: logical bytes and key units.
  - The footprint adds the logical size of every persistent write the block can perform, including writes in called functions along the static call graph.
  - The key units come from the catalog's entry for each platform API called (WP2 adds a key-unit field to the catalog).
  - `if` and `match` take the maximum over their branches.
  - A `for` loop with constant bounds multiplies its body by the iteration count.
  - A `while` loop, or a `for` loop with a runtime bound, makes the footprint *unbounded*.
  - Repeated writes to the same destination count every time. This is conservative, because a platform may journal a location once.
- **Capacity classes.** New PLT rules in Annex B §B.10. A capacity class states two minimums:
  - a minimum transaction capacity, in logical bytes and key units;
  - a minimum atomic-assignment size, in logical bytes.

  A platform claiming the class must commit every transaction within those minimums, and must perform atomically every assignment within the atomic minimum. The values belong to the profiles (WP2), not to the language.
- **Checks against a class** (D5):
  - STA-13 now compares the destination's logical size with the class's atomic minimum;
  - TXN-16 compares a bounded footprint with the class's transaction minimum;
  - an unbounded footprint is accepted, `trap(TXN-CAPACITY)` stays the safety net, and the tooling reports that the transaction has no guarantee.
- **Amendments.** TYP-23, STA-13, TXN-16, RTF-8, PLT-15 and PLT-29. B9 replaces "target profile limits" with "capacity class minimums" in these places.

## 3. Grammar, tests and tools

- **Annex A.**
  - `WipeStatement ::= 'wipe' Expression ';'`, if D3 is (a).
  - The slice-assignment form already derives, because a slice is a postfix expression: STM-7 rejected it, not the grammar.
- **Tests**, written by a new generator `tools/generators/wp1_tests.py`:
  - valid: slice copy, overlapping copy, persistent slice copy inside a transaction, `equal` and `compare` on views, and `wipe` on a local, a session global and a slice;
  - invalid: mismatched constant lengths, a slice into a `ref` parameter, `equal` with different element types, a slice on the right side outside a slice assignment, and declaring `equal` as a name;
  - runtime: overlapping copies in both directions, a length mismatch trapping `BOUNDS`, `compare` ordering, and a persistent slice copy rolled back by `abort`;
  - capacity: the checker reports the footprint of each transaction. Tests with a bounded footprint, an unbounded footprint, and one above a test capacity class (D5).
- **Tools.**
  - `stmcheck` and `funcheck`: slice-assignment typing.
  - `expcheck`: the new intrinsics.
  - `txncheck`: the footprint analysis.
  - The interpreter: the copy, the comparisons and `wipe`.
  - `grammar.py`: picks up Annex A automatically.
- **Bookkeeping.** The chapter error tables, Annex C (OI-46 onwards), Annex D (D.2, regenerated D.3), the 00-index counts, the B.12 checklist and the decision register. All of it is checked by `speccheck.py`.

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Slice assignment: what may the right side be, and what is a length mismatch known at compile time? | (a) any expression of type `T[N]` or a view `T[]` (array, list, `fill`, payload, slice); mismatch is a new **CE-STM-8**. (b) only a slice or a whole array place | (a) |
| D2 | Element types for `equal` and `compare` | (a) `equal`: any type with `==` (integers, `bool`, enums); `compare`: integer types only. (b) both `u8` only | (a) |
| D3 | The form of wiping | (a) a `wipe place;` statement (new keyword). (b) a `secret` qualifier on declarations: every store is kept, and the value is wiped automatically when its scope or the command ends. (c) both | (a) now; (b) can be added later if needed |
| D4 | The logical size of an enum | (a) 1 when it has at most 256 variants, otherwise 2. (b) always 1, with at most 256 variants allowed. (c) always 4 | (a) |
| D5 | A bounded footprint above the class minimum | (a) rejected for that class at build or load time, as for STA-13 and RTF-7. (b) only a warning; the runtime trap stays | (a), matching the existing treatment of computable limits |

**Decided 2026-11-17.** You accepted every recommendation:

- **D1 (a):** the source is any expression of type `T[N]` or a view `T[]`. A length mismatch known at compile time is the new **CE-STM-8**; otherwise it is `trap(BOUNDS)`.
- **D2 (a):** `equal` accepts any element type with `==`; `compare` accepts integer element types only.
- **D3 (a):** wiping is a `wipe place;` statement, with `wipe` as a new keyword.
- **D4 (a):** an enum's logical size is 1 if it has at most 256 variants, and 2 otherwise.
- **D5 (a):** a bounded footprint above the class minimum is rejected for that class at build or load time.

## 5. Exit checklist

- Every new or amended rule is [Agreed], cites its D-4nn and base-plan decision, and has tests or a reason in §D.3.
- `python -I tools/run_checks.py` passes, including the grammar and speccheck runs.
- Annex B §B.12 lists the new platform-defined items: the side-channel protection level and the capacity class values.
