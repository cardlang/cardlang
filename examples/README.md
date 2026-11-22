# Example applets

Complete smart-card applications written in CardLang, each implementing part of a real standard. They show what the language and the Base Profile look like on real protocols, and they are tested on every backend.

| Applet | What it is |
|---|---|
| [`fido2/`](fido2/README.md) | A FIDO2 authenticator: CTAP 2.0 over NFC, with PIN/UV auth protocols two and one |
| [`piv/`](piv/README.md) | A PIV card application (NIST SP 800-73-5), for the contact interface |

## What an example holds

Each folder is self-contained:
- **`cardlang.json`:** the project, giving its source files in order and its transport binding;
- **the `.card` sources;**
- **at least one `.scenario`:** a short session to run or debug, in the editor or with `clc run`;
- **`check.py`:** an independent check, which runs a session and checks every response with code of its own, without reusing the applet's logic;
- **a README:** what it implements and leaves out, its files, and how to check, build, run and debug it.

`tools/run_checks.py` finds every `examples/*/check.py` and every `examples/*/*.scenario`, and runs them on every backend: the reference interpreter, the Python VM, and the C VM built with MSVC and with clang. A new example is checked as soon as its folder holds these files.
