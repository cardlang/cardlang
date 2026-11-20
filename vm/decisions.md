# CardLang VM — Decision register

Each row is one decision about the VM. The requirements in the `vm/` documents cite these IDs. A question that is still open waits here as a question; it never appears as a requirement.

| ID | Decision | Date | WP | Implemented by |
|---|---|---|---|---|
| V-1 | **The VM trusts the bytecode.** The compiler and an off-device verifier establish every static guarantee. The HAL authenticates the image once, at install. The VM then checks only the image header against its configuration. There is no on-device verifier and no per-instruction type or stack check | 2026-11-19 | plan | VM1, VM3 |
| V-2 | **RAM is the constraint, not code size.** The VM's own bookkeeping is fixed, independent of the application, and at most 1 KiB, aiming for a few hundred bytes. Application storage (globals, frames, operand stack, request and response buffers) is configured and does not count toward it | 2026-11-19 | plan | VM1, VM8 |
| V-3 | **The product VM is portable C11** over a rich, well-defined HAL: crypto, keys, randomness, persistent storage with transactions. Prototypes may be in Python | 2026-11-19 | plan | VM2, VM7 |
| V-4 | **A stack machine** with 32-bit cells. Aggregates stay in memory and are moved by block instructions. The maximum stack depth is known at build time (FUN-5, RTF-7) | 2026-11-19 | plan | VM1, VM3 |
| V-5 | **The pure-software catalog APIs** (CBOR, BER-TLV, DER: 13 of 34) are a portable C native library shipped with the VM, not part of the HAL | 2026-11-19 | plan | VM2, VM7 |
| V-6 | **The VM is a library.** The platform's main loop owns the transport and calls the VM: install, session start, select, command, session end. The binding adapters (ISO 7816, raw) ship with the VM. The HAL has no I/O | 2026-11-19 | plan | VM1, VM2 |
| V-7 | **Persistent storage is accessed only through the HAL:** read, atomic write, begin, commit and abort. Memory-mapped reads may be added later as an optimisation | 2026-11-19 | plan | VM1, VM2 |
| V-8 | **One application per VM context.** A platform hosting several applications creates several contexts; isolation between them is the platform's. The VM keeps no C globals | 2026-11-19 | plan | VM1, VM7 |
| V-9 | **The `vm/` documents** state numbered requirements per document (`VEX-n`, `HAL-n`, `BC-n`, `IMG-n`). Each cites the decisions and the spec or profile rules it serves. There are no status tags; open questions live in this register | 2026-11-19 | VM0 | all `vm/` documents |
| V-10 | **One test harness for every backend** (`tools/harness/`): a shared scenario runner and a backend interface. The reference interpreter is the first backend | 2026-11-19 | VM0 | `tools/harness/` |
| V-11 | **The prototypes live in `tools/vmproto/`;** the C VM in `vm/c/`. The compiler's long-term home is decided at VM7 | 2026-11-19 | VM0 | VM4, VM5, VM7 |
| V-12 | **Acceptance criteria for a VM backend:** every runtime conformance test passes; `check_fido2` passes; every valid conformance program compiles to an image; and the backend reports its bytecode size, stack and frame figures, and from VM5 on its bookkeeping RAM against V-2 | 2026-11-19 | VM0 | `tools/run_checks.py`, VM5, VM7 |
| V-13 | **Values are packed, unaligned and little-endian** in every region; enums are their ordinal in 1 byte (2 above 256 variants). Every default value is then all-zero bytes | 2026-11-19 | VM1 | VEX-4, VEX-5 |
| V-14 | **An address is one 32-bit cell:** a 3-bit region tag and a 29-bit offset. A view is two cells (address, length). Instructions name the region when the compiler knows it | 2026-11-19 | VM1 | VEX-7, VEX-11 to VEX-13 |
| V-15 | **Persistent writes are HAL atomic updates,** written in chunks; the VM never stages a destination in RAM | 2026-11-19 | VM1 | VEX-28 |
| V-16 | **Natives reach application data through VM helpers;** persistent data passes through a bounce buffer in the context (64 bytes; 128 since V-22), wiped after each call | 2026-11-19 | VM1 | VEX-34, VEX-36 |
| V-17 | **The image is memory-mapped** and read through a read-only pointer | 2026-11-19 | VM1 | VEX-10 |
| V-18 | **The execution budget is an instruction counter;** natives and aggregate intrinsics charge per call and per byte | 2026-11-19 | VM1 | VEX-42 |
| V-19 | **All cryptography is in the HAL.** The VM core and the native library perform no cryptographic computation or composition. The HAL's crypto interface follows the catalog's operations (one-shot and multi-part). The backend behind it (PSA, a secure element, a library) is the port's choice | 2026-11-19 | VM2 | HAL-1 to HAL-3, HAL-25, HAL-26 |
| V-20 | **Operation contexts in a configured area.** The HAL publishes the context size and alignment; the native library keeps the slots in the resource area of `cl_config` | 2026-11-19 | VM2 | HAL-27, VEX-35 |
| V-21 | **HAL calls are synchronous** and never re-enter the VM | 2026-11-19 | VM2 | HAL-4 |
| V-22 | **The bounce buffer is 128 bytes** (amends V-16) | 2026-11-19 | VM2 | VEX-34, VEX-50 |
| V-23 | **HAL data arguments are descriptors:** a pointer for RAM and constant data, a reader or writer for persistent data, so nothing persistent is staged in VM RAM | 2026-11-19 | VM2 | HAL-11 to HAL-14 |
| V-24 | **Instructions are a one-byte opcode with fixed-width operands** per opcode, unaligned and little-endian | 2026-11-19 | VM3 | BC-1, BC-2, BC-6 |
| V-25 | **One opcode per operation, with a one-byte type operand** for integer types; VM6 may specialise frequent pairs | 2026-11-19 | VM3 | BC-3, BC-8, BC-13 to BC-17 |
| V-26 | **Natives have fixed numbers** per catalog API, used directly by `NATIVE n`; the image's import list serves only the load-time check | 2026-11-19 | VM3 | BC-21, BC-32 to BC-34, IMG-7 |
| V-27 | **An optional debug section** (files, function names, line table), ignored by the device VM and strippable | 2026-11-19 | VM3 | IMG-10 |
| V-28 | **Bytecode and image version 0 are living** until VM6: VM4 and VM5 may change them, recording each change in the change log | 2026-11-19 | VM3 | `vm/bytecode.md` §9 |
| V-29 | **The prototype compiler's front end** reuses the reference checkers (acceptance, declarations) and the shared statement parser, plus a static typer that reuses the checker's own type synthesis and assumes validity | 2026-11-20 | VM4 | `tools/vmproto/typer.py`, `tools/checkers/stmtparse.py` |
| V-30 | **The prototype VM executes the binary image,** decoded as the C VM will | 2026-11-20 | VM5 | VM5 |
| V-31 | **The prototype VM keeps all its mutable state in one context object** with declared C field sizes; a test checks that it keeps no other state | 2026-11-20 | VM5 | VM5 |
| V-32 | **The prototype compiler folds constants and makes no other optimisation,** so that VM5's measurements are a plain baseline for VM6. *Amended 2026-11-20 (VM4b):* with the baseline on record in `plans_and_notes/VM5-measurements.md`, the compiler may optimise, provided each optimisation is added together with its measured effect | 2026-11-20 | VM4, VM4b | VM4, VM4b |
| V-33 | **The test-only catalog** (`card.test.*`) gets native numbers from `0xF000`, implemented only in test builds; production VMs reject such images at load | 2026-11-20 | VM4 | `vm/bytecode.md` BC-32 |
| V-34 | **Frame slots are allocated stack-like by block and statement:** locals are freed at the end of their block, temporaries at the end of their statement, and a binding's temporaries belong to the binding's block. The frame size is the high-water mark | 2026-11-20 | VM4b | `tools/vmproto/compiler.py` |
| V-35 | **The compiler emits nothing that cannot be reached:** nothing between a terminator and the next jump target | 2026-11-20 | VM4b | `tools/vmproto/compiler.py` |
| V-36 | **Aggregates are built in place** for `var` initialisers and `return Ok(aggregate)`; assignments keep the temporary (STM-9, VEX-30) | 2026-11-20 | VM4b | `tools/vmproto/compiler.py` |
| V-37 | **Runtime tests for the untested intrinsics and structure access** (`run-029`, `run-030`) are added before the instruction set is frozen | 2026-11-20 | VM4b | `tools/generators/wp13_tests.py` |

## Open questions

None. VM1 to VM3 raised none.
