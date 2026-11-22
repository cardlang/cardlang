# The CardLang Base Profile

A **platform profile** says what a platform gives CardLang programs: the APIs under `card.`, the types they use, the `CardError` codes, and how requests and responses travel. The language leaves these to platforms on purpose. Annex B of the specification sets the requirements every platform must meet (`PLT-n`), and §B.12 lists the choices a platform specification must make. The Base Profile is one such specification, the one the tools, the VMs and the example applets implement.

| File | What it is |
|---|---|
| [`base-profile.md`](base-profile.md) | **The profile itself,** with rules numbered `BP-n`. It covers the API conventions, resources and keys, cryptography, randomness, CBOR, DER and BER-TLV, the transport bindings (ISO 7816 and raw), and its answer to every item of Annex B §B.12 |
| [`base-types.card`](base-types.card) | The profile's types and enums, such as `KeyType`, `Algorithm` and `CborHead`, written in CardLang. Every program is built with them, so their names are predeclared |
| [`base-catalog.txt`](base-catalog.txt) | The API catalog: every `card.` API, with its signature, its errors, and how it behaves in a transaction (it participates, acts at once, or is forbidden). The checkers and the compiler read it |

**Where to start:** `base-profile.md` §1 for what conformance means, then the family you need. The catalog is the reference for exact signatures.

The profile is checked by `tests/profilecheck.py`: its rule numbering, the `CardError` table and its precedence, that `base-types.card` compiles, and every catalog entry's fields, types and errors.
