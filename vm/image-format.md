# CardLang VM — Image format, version 1

Work package VM3. Plan: `plans_and_notes/vm-plans/VM3-bytecode-and-image.md`. Instructions: `vm/bytecode.md`.

An *image* is one compiled CardLang application, as the platform's loader stores it and `cl_vm_load` receives it (VEX-45). Requirements are numbered `IMG-n` and cite the decisions and the rules they serve (V-9). Like the bytecode, version 1 of the format stays living through VM7 (V-41). Changes are recorded in the change log of `vm/bytecode.md` §9.

## 1. General

**IMG-1 Encoding.** Every multi-byte field is little-endian (V-13). Every offset is in bytes from the start of the image. Fields and sections are unaligned.
*Serves: V-13.*

**IMG-2 Sections.** An image is a header (IMG-3) followed by these sections, in this order. Every section other than the debug section is present, possibly empty:
1. the function table (IMG-6);
2. the native imports (IMG-7);
3. the constants (IMG-8);
4. the code (IMG-9);
5. optionally, the debug section (IMG-10).

*Serves: V-24, V-27.*

**IMG-3 Header.** 72 bytes:

| Offset | Size | Field | Meaning |
|---:|---:|---|---|
| 0 | 4 | `magic` | The bytes `43 4C 56 4D` ("CLVM") |
| 4 | 2 | `format` | The format and bytecode version: 1 |
| 6 | 1 | `profile` | The platform profile: 1 for Base Profile 1 |
| 7 | 1 | `binding` | 0 none, 1 ISO 7816, 2 raw (IMG-4) |
| 8 | 4 | `image_size` | The size of the whole image, including any debug section |
| 12 | 4 | `persistent_size` | Bytes of `PERSISTENT` (VEX-8) |
| 16 | 4 | `session_size` | Bytes of `SESSION` |
| 20 | 4 | `stack_need` | The maximum `STACK` need, over every entry (VEX-17) |
| 24 | 4 | `max_atomic` | The largest persistent destination of static size (VEX-29) |
| 28 | 2 | `function_count` | Entries in the function table |
| 30 | 2 | `entry_command` | The function index of `command` |
| 32 | 2 | `entry_install` | The index of `on_install`, or `0xFFFF` |
| 34 | 2 | `entry_session_start` | The index of `on_session_start`, or `0xFFFF` |
| 36 | 2 | `entry_select` | The index of `on_select`, or `0xFFFF` |
| 38 | 2 | `import_count` | Entries in the native imports |
| 40 | 4 | `functions_offset` | Where the function table starts |
| 44 | 4 | `imports_offset` | Where the native imports start |
| 48 | 4 | `const_offset` | Where the constants start |
| 52 | 4 | `const_size` | Bytes of `CONST` |
| 56 | 4 | `code_offset` | Where the code starts |
| 60 | 4 | `code_size` | Bytes of code |
| 64 | 4 | `debug_offset` | Where the debug section starts, or 0 |
| 68 | 4 | `debug_size` | Bytes of the debug section, or 0 |

*Serves: V-24; VEX-8, VEX-9, VEX-45.*

**IMG-4 Binding.** The binding the application was built for (BP-52). A VM whose platform uses another binding rejects the image at load. 0 means the program declares no binding-specific entry point (no `on_select`), and loads on either binding.
*Serves: BP-47, BP-52.*

**IMG-5 Entry points.** `entry_command` always names a function, because every application declares exactly one command (HEP-1). The lifecycle entries are `0xFFFF` when the handler is not declared. `entry_select` is `0xFFFF` unless the binding is ISO 7816 (BP-50a).
*Serves: HEP-1, STA-6, BP-50a, BP-55.*

## 2. Sections

**IMG-6 The function table.** `function_count` entries of 12 bytes. Function indices start at 0 and are the operand of `CALL` (BC-19).

| Offset | Size | Field | Meaning |
|---:|---:|---|---|
| 0 | 4 | `code` | The function's first instruction, as an offset into the code section |
| 4 | 4 | `frame_size` | The whole frame in bytes: return information, parameters, locals, temporaries and the operand area (BC-22) |
| 8 | 1 | `argc` | Parameter cells, including a hidden payload slot (BC-24, BC-27) |
| 9 | 1 | `payload` | 0 for no payload, 1 for a scalar, 2 for an aggregate through a slot |
| 10 | 2 | `operand_base` | Where the operand area starts, as an offset from the frame base: the size of the return information, parameters, locals and temporaries (BC-22, BC-25) |

*Serves: V-24; VEX-17, VEX-18, BC-22, BC-25.*

**IMG-7 The native imports.** `import_count` entries of 2 bytes: the native numbers (BC-32) that the code uses, each once, in increasing order. They are used only by the load-time check (IMG-11). `NATIVE` names its native directly, so nothing is resolved at load (V-26).
*Serves: V-26; VEX-9.*

**IMG-8 The constants.** `const_size` bytes: the initial and only contents of `CONST` (VEX-7). They include constant arrays, structures, byte strings and array lists, in the layout of VEX-4. Constant scalars are normally folded into instructions and are not stored here.
*Serves: VEX-7, VEX-10.*

**IMG-9 The code.** `code_size` bytes: every function body, as instructions of `vm/bytecode.md`. A function's code runs from its `code` offset up to the next function's offset, or to the end of the section.
*Serves: V-24.*

**IMG-10 The debug section.** It is optional, and the device VM never reads it (V-27). A tool may strip it, which sets `debug_offset` and `debug_size` to 0 and reduces `image_size`. It holds:

| Part | Encoding |
|---|---|
| A count of source files, then each file's name | A `u16` count, then for each file a `u16` length followed by UTF-8 bytes |
| A count of functions, then each function's name | A `u16` count, equal to `function_count`, then names as above |
| A line table | A `u32` count of rows, then rows of `code offset u32`, `file u16`, `line u32`, sorted by code offset |

A row applies from its code offset up to the next row's. The prototype VM and the test harness use the section to report a trap with its source position.
*Serves: V-27.*

## 3. Loading

**IMG-11 Load-time checks.** `cl_vm_load` rejects the image, and runs none of it, if any of these fails:
1. `magic` is "CLVM", and `format` is one the VM implements;
2. `profile` and `binding` match the platform (IMG-4);
3. `image_size` equals the size given to `cl_vm_load`, and every section lies inside the image without overlapping another;
4. every entry index is `0xFFFF` or less than `function_count`, and `entry_command` is not `0xFFFF`;
5. every function's `code` offset lies inside the code section, in increasing order of index;
6. `session_size` and `stack_need` fit the areas in `cl_config` (VEX-8);
7. `persistent_size` fits `cl_hal_storage_size` (HAL-15);
8. `max_atomic` fits `cl_hal_atomic_capacity` (HAL-17, VEX-29);
9. every imported native number is one the VM provides.

These are header checks, as V-1 allows: the code itself is not verified. Checks 6 to 9 are the load-time rejection of RTF-8, STA-13 and TYP-23. Each failure has its own result code in `cl_vm.h` (VM7).
*Serves: V-1; VEX-9, RTF-8, STA-13, TYP-23.*

**IMG-12 Nothing is copied.** The VM reads the image in place through its pointer (VEX-10). Loading writes nothing but the VM context.
*Serves: V-2, V-17.*

## 4. The compiler's resource report

**IMG-13** With every image, the compiler reports:
- the image size, per section;
- for each function: its name, code size, frame size and operand depth;
- `stack_need`, with the call path that needs it;
- `persistent_size`, `session_size` and `max_atomic`, with the destination that sets `max_atomic`;
- the natives used.

From VM5 on, the prototype VM adds the measured figures of V-12: the bookkeeping it needed, opcode frequencies, and the deepest stack actually used.
*Serves: V-12; RTF-7, TYP-23.*
