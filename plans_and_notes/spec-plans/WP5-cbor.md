# WP5 — Canonical CBOR (`card.cbor`): detailed sub-plan

Parent: `plans_and_notes/base-api-plan.md` (B2: a platform API; a strict canonical reader; an always-canonical writer).
Status: decisions W1–W5 taken 2026-11-18 (§4). **Drafted 2026-11-18.** Clarification: `skip` checks each head but not key order or UTF-8 (BP-38); only `validate` is the full check.

## 1. Scope

WP5 fills in profile §9 and adds the `card.cbor` entries to the catalog, with an implementation in the interpreter. CBOR is CTAP2's message format:
- every request (`authenticatorMakeCredential`, `authenticatorGetAssertion`, `authenticatorClientPIN` and so on) is a map with small integer keys;
- every response is a map as well;
- COSE public keys are CBOR maps with negative integer keys.

## 2. Design

### 2.1 A stateless API over slices (W1)

The base plan sketched a reader with its position held in an application structure. But slice views (FUN-18) make that unnecessary: every call works on the start of the view it is given, and the application advances by slicing. There is no reader or writer state, no new resource kind, and no structure the application has to keep consistent.

```text
var length: u32 = attempt card.cbor.validate(ref request[1..request.length]);   // a whole item, strictly
var head: CborHead = attempt card.cbor.head(ref request[at..end]);              // the head at the start
var next: u32 = attempt card.cbor.skip(ref request[at..end]);                   // the encoded length of the item there
var n: u32 = attempt card.cbor.write_head(CborMajor.Map, 3, inout response[out..response.length]);
```

| API | Payload | Meaning |
|---|---|---|
| `card.cbor.validate(ref data)` | `u32` | `data` must begin with one complete data item that is well-formed and canonical (§2.2). The result is that item's encoded length. Bytes after the item are ignored, so the application can tell trailing data from the length |
| `card.cbor.head(ref data)` | `CborHead` | Decodes the head at `data[0]` |
| `card.cbor.skip(ref data)` | `u32` | The encoded length of the complete item at `data[0]`, including everything nested in it |
| `card.cbor.write_head(major, value, inout out)` | `u32` | Writes the shortest head for `major` and `value` at `out[0]`, and returns the number of bytes written (BP-6) |
| `card.cbor.write_int(value: i32, inout out)` | `u32` | Writes an integer: major type 0 for `value ≥ 0`, otherwise major type 1 with argument `−1 − value` |

```text
enum CborMajor { Unsigned; Negative; Bytes; Text; Array; Map; Tag; Simple; }
struct CborHead {
    major: CborMajor;
    argument: u32;     // the value, the length in bytes, the number of items or pairs, the tag number, or the simple value
    size: u32;         // the bytes the head itself occupies
}
```

**Reading strings.** A byte or text string's content is the slice `data[head.size .. head.size + head.argument]`, which the application reads directly.

**Integer range.** An argument above `u32` is `Err(CardError.Unsupported)` from `head`. A `Negative` item's value is `−1 − argument`. It is representable as `i32` when `argument ≤ 2^31 − 1`, which is what CTAP and COSE use.

**Walking a map.** Read the map's head, then take `2 × argument` items in turn, with `skip` to move past values that are not needed. The application does this with a `for` loop. No recursion is needed, which CardLang forbids anyway (FUN-5).

**Writing.** The application writes heads with `write_head` and `write_int`, and copies string content with slice assignment (FUN-24). It must emit map keys in canonical order. `compare` (EXP-54) helps with that, and `validate` on its own output catches mistakes.

### 2.2 What "canonical" means (W2, W3, W4)

`validate` rejects with `Err(CardError.Malformed)` anything that is not well-formed, or not canonical:

- **Truncation.** The item is incomplete, or a length exceeds the remaining data.
- **Indefinite lengths.** The additional-information value 31 is not allowed.
- **The reserved additional-information values** 28 to 30.
- **Non-shortest encodings.** An integer, length or count must use the shortest form: a value below 24 in the initial byte, below 256 in one byte, and so on.
- **Map keys.** Keys must be in canonical order, with no duplicates. The order is W2.
- **Text strings** must be valid UTF-8 (W4).
- **Nesting.** For `validate` only, nesting deeper than the platform supports is `Err(CardError.Unsupported)`. Platforms support at least 16 levels (W5).

Floating-point values (major type 7 with additional information 25, 26 or 27) are `Err(CardError.Unsupported)`. Simple values are limited to `false` (20), `true` (21), `null` (22) and `undefined` (23); others are `Malformed` (W3).

`head` and `skip` apply the same rules to what they read. That means they are safe on unvalidated data, but `validate` is the one call that checks a whole message.

### 2.3 Errors and transactions

- **Errors**, in BP-8 order: `Unsupported`, `Malformed`, `Capacity` (from the write APIs).
- **Transactions.** Every CBOR API is `immediate`: none of them touches persistent state or resources.

## 3. Interpreter and tests

- **`tools/interp/testcbor.py`** is a CBOR validator and writer, self-tested against examples from RFC 8949 Appendix A.
- **Tests** (new generator `wp5_tests.py`):
  - Compile time: a valid use of every API, and a wrong argument type.
  - Runtime: parse a CTAP-style request map, such as `{1: h'…', 2: "rp", 3: [1, 2], 4: true}`, by walking it in CardLang, and return the extracted fields.
  - Runtime: build a canonical response map containing a COSE-style key `{1: 2, 3: -7}`, and compare it with the exact expected bytes.
  - Runtime: each `Malformed` case: a non-shortest integer, keys out of order, a duplicate key, an indefinite length, truncation, invalid UTF-8, and a reserved additional-information value.
  - Runtime: the `Unsupported` cases: a float, an argument above `u32`, and nesting too deep.
  - Runtime: `write_head` into a view that is too short gives `Capacity`.

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| W1 | The API's shape | (a) stateless calls on the start of a view, with the application advancing by slicing (§2.1); (b) a reader and writer state held in an application structure, as sketched in the base plan | (a). It is simpler, and makes no new resource or state rules |
| W2 | Canonical map-key order | (a) CTAP2's: the shorter encoded key first, then bytewise (as in RFC 7049 §3.9); (b) RFC 8949's "core deterministic" order: bytewise over the encoded keys | (a). The base profile targets CTAP2, whose clients send this order. The two agree for CTAP's small integer keys and short text keys of different lengths, but not in general |
| W3 | Floats, tags and simple values | (a) floats `Unsupported`; tags accepted structurally (as a head, followed by one item); simple values only `false`, `true`, `null` and `undefined`; (b) tags rejected as well | (a) |
| W4 | UTF-8 in text strings | (a) `validate` checks it, and invalid UTF-8 is `Malformed`; (b) not checked | (a), consistent with the strict choice in B2 |
| W5 | Nesting depth | (a) platforms support at least 16 levels, and deeper is `Unsupported`; (b) no stated minimum | (a). CTAP needs about 4 |

**Decided 2026-11-18:**

- **W1 (a):** stateless calls over slices.
- **W2 (a):** the CTAP2 length-first key order. **Revised 2026-11-18 (WP8 step 0, R1).** CTAP2's actual rule is bytewise order of the encoded keys; my description of option (a) was wrong. The profile now uses bytewise order (option (b), RFC 8949 core deterministic).
- **W3 (a):** floats are `Unsupported`, tags are accepted structurally, and only four simple values are allowed.
- **W4 (a):** `validate` checks UTF-8.
- **W5 (a, clarified):** only `validate` is limited by depth. Its internal key-order check keeps the previous key and the pairs remaining for each open map. Platforms validate at least 16 levels, and deeper input may be `Unsupported`. `head` and `skip` have no depth limit, because one pending-item counter is enough for them.

## 5. Exit checklist

- Profile §9 is written. The catalog has the five entries, and `profilecheck` passes.
- `testcbor.py` passes its self-test.
- `python -I tools/run_checks.py` passes.
