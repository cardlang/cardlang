# CardLang VM — Plan of plans

Status: V-1 to V-8 decided 2026-11-19 (V-5 to V-8 as recommended). **VM0 done 2026-11-19:** `vm/README.md`, `vm/decisions.md` (V-1 to V-12) and the shared harness `tools/harness/`. **VM1 drafted 2026-11-19:** `vm/execution-model.md` (VEX-1 to VEX-50), V-13 to V-18. **VM2 drafted 2026-11-19:** `vm/hal.md` (HAL-1 to HAL-31), the draft headers, V-19 to V-23. Next: VM3. Parent: CardLang Draft 0.2 (`spec-draft-0.2`).

## 1. Context

Draft 0.2 specifies the language and the Base Profile 1, but not how a program runs. Annex B §B.11 records only informative ideas: a small stack interpreter, bytecode in flash, bounded frames, no heap. This plan turns them into a VM design and an implementation.

The VM is **not part of the language specification**. Its documents go in a new top-level `vm/` folder, as the profile went in `platform/`. Where the VM must honour a language rule (traps, atomicity, frame erasure), it cites the rule ID.

## 2. Decided goals (2026-11-19)

| ID | Decision |
|---|---|
| V-1 | **The VM trusts the bytecode.** The compiler and an off-device verifier establish every static guarantee. On the device, the image is authenticated once, at install (by the HAL); the VM then checks only the image header against its configuration. There is no on-device verifier and no per-instruction type or stack check. |
| V-2 | **RAM is the constraint, not code size.** The VM's own bookkeeping (its state, registers and internal tables) is fixed, independent of the application, and bounded. **Target: at most 1 KiB, aiming for a few hundred bytes.** Application storage (persistent and session globals, frames, operand stack, the request and response buffers) is sized by configuration and the compiler's report, and does not count toward that figure. |
| V-3 | **The product VM is portable C11** over a rich, well-defined HAL. Crypto, keys, randomness, persistent storage with transactions, and communication live in the HAL. Prototypes may be in Python. |
| V-4 | **A stack machine.** Rationale: compact code, a simple compiler, and the static call graph (FUN-5, RTF-7) makes the maximum stack depth a build-time number, so the stack needs no runtime growth or checks. |

## 3. Facts from the language that the VM relies on

These come from Draft 0.2 and keep the VM small. VM1 confirms the list.

- **No recursion, a static call graph (FUN-5).** Every frame size and the maximum stack need are computed at build time (RTF-7). One stack buffer, sized from the image header, is checked once at load (RTF-8).
- **No heap, no allocation, no pointers as values.** References and views exist only for the duration of a call (FUN-16), so they live in frames.
- **Few value kinds.** Integers up to 32 bits, `bool`, enums (no payload, no numeric value), and fixed-size aggregates (structures, arrays). Nominal types disappear at compile time. No floats, no 64-bit integers (TYP-8).
- **One command at a time** (TXN-14), at most one active transaction (TXN-10).
- **Deterministic traps** (RTF-4, RTF-5), all ending the command; the VM does not need to unwind into application code.
- **Platform obligations the VM inherits:** frame erasure on exit, traps included (PLT-35); `wipe` stores never removed (PLT-34); constant-time `equal` (PLT-31); atomic persistent assignment (STA-11).

## 4. Architecture sketch

```text
   host / transport (platform main loop)
          │  requests, session events
   ┌──────▼─────────────────────────────┐
   │ binding adapter (ISO 7816 / raw)   │  status words, raw envelope (BP-50..53)
   ├────────────────────────────────────┤
   │ VM core: loader, interpreter loop, │  traps, outcomes, frames, views
   │ memory regions                     │
   ├────────────────────────────────────┤
   │ native table (catalog APIs)        │  card.* calls by catalog index
   ├────────────────────────────────────┤
   │ HAL                                │  storage + transactions, crypto, keys, RNG
   └────────────────────────────────────┘
```

Design principles, to be confirmed in VM1:

- **A non-recursive interpreter loop.** A CardLang call does not recurse on the C stack, so the C stack depth is a small constant. A trap is a return code out of the loop, not a `longjmp`.
- **A VM context object.** The VM keeps no C globals; all bookkeeping is in one struct whose size is a compile-time constant, which is how V-2 is measured.
- **Aggregates stay in memory.** The operand stack holds 32-bit cells (integers, Booleans, enum ordinals, addresses). Structures and arrays are never pushed; they are copied between memory regions by block instructions.
- **Region-tagged addresses.** An address names a region (constants, persistent, session, frame, request, response) and an offset. A view is an address plus a length. Persistent accesses go through the HAL.

## 5. Work packages

Each package gets its own sub-plan in `plans_and_notes/vm-plans/VMn-*.md`, reviewed before drafting, as for the specification.

| WP | Output | Depends on |
|---|---|---|
| **VM0 Foundations** | This plan; a VM decision register (V-n) in `vm/decisions.md`; the `vm/` folder layout; the acceptance criterion: the existing runtime conformance tests and `check_fido2` pass on every VM | — |
| **VM1 Execution and memory model** | `vm/execution-model.md`: value representation; regions and addressing; views and references; frame layout (parameters, locals, temporaries, return information); calls and payload returns; the outcome register (`Ok`, `Err`, error code); traps and their effects (RTF-1, RTF-2, PLT-35); the execution budget (RTF-6); the VM context struct and its RAM bound | VM0 |
| **VM2 HAL interface** | `vm/hal.md` and a draft `cl_hal.h`: persistent storage (read, atomic write, begin, commit, abort, recovery), keys, crypto, randomness, session events; ownership of memory; error mapping to `CardError` (profile §4); what must be constant-time | VM0; can run alongside VM1 |
| **VM3 Bytecode and image format, version 0** | `vm/bytecode.md` and `vm/image-format.md`: the instruction set and its encoding; the image (header, function table, constant data, global layout, native import table, stack and frame figures) | VM1, VM2 |
| **VM4 Prototype compiler** | A Python compiler from the checked program (reusing the checkers' front end) to version-0 images, with a resource report (RTF-7, TYP-23) | VM3 |
| **VM5 Prototype VM** | A Python VM over a Python HAL (reusing the test crypto, CBOR and TLV), driven by the existing scenario files. Passes all runtime tests and `check_fido2`. Measures bytecode size, opcode frequencies, stack depth, and the bookkeeping state it actually needs | VM4 |
| **VM6 Bytecode revision** | A measured revision of VM3: encoding density, specialised and combined instructions, from the VM5 figures, mainly on the FIDO2 applet | VM5 |
| **VM7 C11 VM and a host HAL** | `vm/c/`: the product VM in portable C11, a host (PC) HAL implementation, and a harness that runs the same scenarios and `check_fido2` against it | VM6 |
| **VM8 Footprint report** | Measured RAM bookkeeping (V-2), stack and code figures for the FIDO2 applet; optionally a first embedded port | VM7 |

**Order:** VM0, then VM1 and VM2 together, then VM3 to VM8 in sequence. VM4 and VM5 are one feedback loop and may be planned together.

## 6. Decisions for VM0

All four were decided 2026-11-19, as recommended (option (a)).

| ID | Question | Options | Recommendation |
|---|---|---|---|
| V-5 | Where the pure-software catalog APIs live (CBOR, BER-TLV, DER: 13 of the 34) | (a) a portable C native library shipped with the VM, not in the HAL; (b) in the HAL | (a). They need no hardware, and keeping them out of the HAL keeps every port's HAL smaller |
| V-6 | Who owns the transport | (a) the VM is a library: the platform's main loop receives a request and calls the VM (`install`, `session_start`, `select`, `command`, `session_end`); binding adapters ship with the VM; the HAL has no transport; (b) the HAL provides receive and send, and the VM owns the main loop | (a). It fits any transport (APDU, USB HID, a TrustZone-M call gate), and keeps the VM free of I/O |
| V-7 | How persistent storage is accessed | (a) only through HAL calls (read, atomic write, transaction), so any storage and any journaling scheme works; (b) memory-mapped reads plus HAL writes | (a), with (b) left as a later optimisation for targets with execute-in-place flash |
| V-8 | Applications per VM | (a) one application per VM context; a platform that hosts several creates several contexts, and isolation between them is the platform's; (b) a multi-application VM with isolation built in | (a) for now. It keeps the bookkeeping per context fixed and small |
