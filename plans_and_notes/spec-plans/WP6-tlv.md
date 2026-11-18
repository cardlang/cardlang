# WP6 — DER writer and BER-TLV reader (`card.der`, `card.tlv`): detailed sub-plan

Parent: `plans_and_notes/base-api-plan.md` (B3: a DER writer, always minimal; a BER-TLV reader with definite lengths only, which also parses DER).
Status: decisions T1–T4 taken 2026-11-18 (§4). **Drafted 2026-11-18.**

## 1. Scope

WP6 fills in profile §10, adds the entries to the catalog, and implements them in the interpreter. It uses the same pattern as WP5's CBOR: stateless calls on the start of a view, with the application advancing by slicing (BP-34). Its uses:

| Use | Needs |
|---|---|
| FIDO2: an ES256 signature must be DER, `SEQUENCE { INTEGER r, INTEGER s }`, while `card.crypto.sign` returns raw `r ‖ s` (BP-29) | The DER writer |
| Attestation: the certificate is opaque bytes, stored and sent as is | Nothing |
| Card protocols in general: GlobalPlatform, PIV and EMV-style data objects, with tags such as `0x7F49` or `0x5F2D` | The BER-TLV reader |

## 2. Design

### 2.1 Tags (T1)

A tag is represented as its **raw bytes packed into a `u32`**, big-endian. This is the card convention. The ISO 7816 and EMV specifications write tags this way: `0x30` is a SEQUENCE, `0x02` an INTEGER, `0x7F49` the PIV public-key template, `0x9F38` the EMV PDOL. Tags longer than 4 bytes are `Unsupported`.

```text
enum TlvClass { Universal; Application; ContextSpecific; Private; }
struct TlvHead {
    tag: u32;            // the raw tag bytes, big-endian, for example 0x7F49
    class: TlvClass;     // bits 8 and 7 of the first tag byte
    constructed: bool;   // bit 6 of the first tag byte
    length: u32;         // the content length
    size: u32;           // the bytes the tag and length occupy
}
```

### 2.2 The reader (BER-TLV, ISO/IEC 7816-4)

| API | Payload | Meaning |
|---|---|---|
| `card.tlv.head(ref data)` | `TlvHead` | Decodes the tag and length at `data[0]`, and checks that the content lies within `data` |
| `card.tlv.skip(ref data)` | `u32` | `size + length` of the object at `data[0]` |
| `card.tlv.validate(ref data)` | `u32` | The object at `data[0]` is well-formed, and, if it is constructed, so is its whole content, recursively. Returns its encoded length (T3) |

**Reading the content.** A primitive object's content is `data[size .. size + length]`. A constructed object's content is a sequence of objects, walked with `head` and `skip`.

**Tag and length forms.**
- **Tags:** a first byte, plus subsequent bytes when the tag number field is `11111`, each with bit 8 set except the last.
- **Lengths:** the short form `00`–`7F`, or the long forms `81`, `82`, `83` and `84`, followed by 1 to 4 bytes.

**What the reader rejects:**
- An indefinite length (`80`) is `Malformed`.
- The length byte `FF` is `Malformed`.
- A length of more than 4 bytes (`85`–`FE`), or a tag of more than 4 bytes, is `Unsupported`.
- Truncation is `Malformed`.

**Leniency (T2).** The reader accepts BER's non-minimal forms, such as `81 05` for a length of 5. DER is a subset, so a DER parser comes for free. Padding bytes (`00` or `FF` between objects, which ISO 7816-4 permits) are not skipped. The application handles them, if a protocol uses them.

### 2.3 The writer (DER)

| API | Payload | Meaning |
|---|---|---|
| `card.der.write_head(tag, length, inout out)` | `u32` | Writes `tag`'s bytes (without leading zero bytes) and `length` in its minimal DER form, and returns the size written |
| `card.der.write_integer(ref magnitude, inout out)` | `u32` | Writes a complete DER INTEGER (`02`, the length, the content) for the unsigned big-endian `magnitude`. Leading zero bytes are removed, a `00` is added when the high bit is set, and zero is encoded as `02 01 00` |
| `card.der.integer_size(ref magnitude)` | `u32` | The size that `write_integer` would write, so an application can compute a SEQUENCE's length before writing its head (T4) |

**Converting a signature to DER** then takes the application about six lines:

```text
var lr: u32 = attempt card.der.integer_size(ref sig[0..32]);
var ls: u32 = attempt card.der.integer_size(ref sig[32..64]);
var at: u32 = attempt card.der.write_head(0x30, lr + ls, inout out[0..out.length]);
var n: u32 = attempt card.der.write_integer(ref sig[0..32], inout out[at..out.length]);
at = at + n;
n = attempt card.der.write_integer(ref sig[32..64], inout out[at..out.length]);
```

**Errors.** A tag value that is not a valid encoded tag (BER tag bytes with an invalid continuation, or 0) is `Malformed`. An output view too short is `Capacity`.

### 2.4 Errors and transactions

- **Errors**, in BP-8 order: `Unsupported`, `Malformed`, `Capacity`.
- **Transactions.** Every API is `immediate`.

## 3. Interpreter and tests

- **`tools/interp/testtlv.py`** is a BER-TLV reader and DER writer, self-tested against hand-checked encodings.
- **Tests** (new generator `wp6_tests.py`):
  - Compile time: a valid use of every API, and a wrong argument type.
  - Runtime: walk a constructed object such as `7F49 { 86 <point> }` and return the point; read two-byte and three-byte tags; read the long length forms `81` and `82`; accept a non-minimal length.
  - Runtime: convert raw `r ‖ s` to DER for three cases — a high bit set (so a `00` is added), leading zeros (which are stripped), and a typical value. The DER result is also checked with `card.tlv.validate`.
  - Runtime: the errors — an indefinite length, `FF`, truncation and a 5-byte length (`Unsupported`), and an output view too short (`Capacity`).

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| T1 | Tag representation | (a) raw tag bytes packed in a `u32`, plus decoded `class` and `constructed`; (b) a class and a tag number, decoded | (a). It matches how card specifications write tags |
| T2 | Leniency | (a) accept BER's non-minimal tag and length forms, and do not skip padding; (b) also skip `00`/`FF` padding | (a) |
| T3 | A recursive `validate` | (a) yes, with at least 16 levels of nesting, as for CBOR; (b) no, only `head` and `skip` | (a). One call checks untrusted input, the same pattern as CBOR |
| T4 | DER writer helpers | (a) `write_head`, `write_integer` and `integer_size`; (b) also a `write_signature(ref rs, inout out)` shortcut for ECDSA | (a). The general calls are enough, and a shortcut can come later |

**Decided 2026-11-18.** You accepted every recommendation:

- **T1 (a):** tags are raw bytes packed in a `u32`.
- **T2 (a):** the reader accepts lenient BER, and does not skip padding.
- **T3 (a):** there is a recursive `validate`, with at least 16 levels.
- **T4 (a):** the DER writer has `write_head`, `write_integer` and `integer_size`.

## 5. Exit checklist

- Profile §10 is written. The catalog has the six entries, and `profilecheck` passes.
- `testtlv.py` passes its self-test.
- `python -I tools/run_checks.py` passes.
