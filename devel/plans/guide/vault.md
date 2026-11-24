# The guide's running example: the vault

The chapters grow one applet, the *vault*: a small store for a secret, protected by a PIN. This note is the authors' design for it, so that each chapter's version fits the next. Each version is a complete, checked program with its scenario, in its chapter.

## What it does, in the end

A host talks to it with one-byte commands, followed by their data:

| Command | Byte | Data | Response |
|---|---|---|---|
| Read the counter | `01` | — | the counter, 4 bytes, big-endian |
| Verify the PIN | `20` | the PIN, 4 to 8 bytes | nothing; a wrong PIN answers the retries left |
| Change the PIN | `24` | old PIN length, old PIN, new PIN | nothing |
| Store the secret | `D0` | up to 32 bytes | nothing; needs the PIN verified in this session |
| Read the secret | `CA` | — | the secret; needs the PIN verified in this session |
| Sign | `2A` | a 32-byte digest | an ECDSA P-256 signature, 64 bytes; needs the PIN verified |

The counter counts successful signatures, so it means something.

## How it grows

| Chapter | The vault gains | Language features |
|---|---|---|
| 1 Getting started | A counter that can be read and incremented. Built, run and debugged in VS Code | `command`, `persistent`, a scenario |
| 2 Values and types | Its commands as an enum, decoded from the first byte; a verify command with a fixed 4-byte PIN | integers, `bool`, arrays, byte strings, `equal`, `enum`, `match`, constants, `convert`. Structures are shown on their own |
| 3 Control flow and scope | A PIN must be all digits, checked with a loop | `var`, assignment, `if`, `for`, `while`, scope, files |
| 4 Functions, references and views | One function per command, with the same shape | functions, `ref`, `inout`, views, forwarding returns |
| 5 Outcomes | Counter overflow as an error the host sees, through `checked_add` | `errors`, `Ok`, `Err`, `require`, `attempt`, `match`, traps |
| 6 State that survives | A persistent PIN of 4 to 8 digits and 3 tries, counted before comparing; a `verified` session flag; changing the PIN in a transaction; storing and reading the secret behind the flag | `persistent`, `session`, defaults, `on_install`, atomic writes, `transaction`, `interrupt` |
| 7 Talking to the host | Status words over the ISO 7816 binding; the same applet over the raw binding | bindings, SELECT, status words, the error code mapping |
| 8 Using the platform | A key generated at installation, signing a digest; wiping the secret | `card.key`, `card.crypto`, `card.random`, `wipe` |
| 9 Testing and debugging | A full set of scenarios; finding a bug with the debugger | scenarios, `clc`, breakpoints, traps |

Chapter 10 then reads part of the FIDO2 example, the real-world version of the same ideas. Chapter 11 needs no new code.

## Limits

- The PIN is 4 to 8 bytes, with 3 tries. The secret is at most 32 bytes.
- Its errors are application errors with small codes. The ISO 7816 version maps them to status words in chapter 7.
- It stays small enough that each chapter shows only what changed, as `program vault` parts with prose between them.
