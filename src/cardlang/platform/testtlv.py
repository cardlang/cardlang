"""BER-TLV reader and DER writer for the reference interpreter (WP6): test-only, standard library only.

Errors are raised as TlvError("Malformed") or TlvError("Unsupported").
"""
MAX_DEPTH = 16                                   # the minimum the profile requires for validate (T3)
CLASSES = ["Universal", "Application", "ContextSpecific", "Private"]

class TlvError(Exception):
    def __init__(self, kind): super().__init__(kind); self.kind = kind

def head(d):
    """(tag, class, constructed, length, size) of the object at d[0] (BP-42)."""
    d = list(d)
    if not d: raise TlvError("Malformed")
    i = 1
    if d[0] & 0x1F == 0x1F:                      # subsequent tag bytes, bit 8 set on all but the last
        while True:
            if i >= len(d): raise TlvError("Malformed")
            i += 1
            if not d[i - 1] & 0x80: break
    if i > 4: raise TlvError("Unsupported")
    tag = int.from_bytes(bytes(d[:i]), "big")
    if i >= len(d): raise TlvError("Malformed")
    l0 = d[i]; i += 1
    if l0 < 0x80: length = l0
    elif l0 == 0x80 or l0 == 0xFF: raise TlvError("Malformed")          # indefinite, reserved
    elif l0 > 0x84: raise TlvError("Unsupported")                        # more than 4 length bytes
    else:
        n = l0 - 0x80
        if i + n > len(d): raise TlvError("Malformed")
        length = int.from_bytes(bytes(d[i:i + n]), "big"); i += n
    if i + length > len(d): raise TlvError("Malformed")
    return tag, CLASSES[d[0] >> 6], bool(d[0] & 0x20), length, i

def skip(d):
    _, _, _, length, size = head(d)
    return size + length

def _validate(d, depth):
    if depth > MAX_DEPTH: raise TlvError("Unsupported")
    _, _, constructed, length, size = head(d)
    if constructed:
        content, pos = d[size:size + length], 0
        while pos < length: pos += _validate(content[pos:], depth + 1)
    return size + length

def validate(d): return _validate(list(d), 1)

def der_length(n):
    if n < 0x80: return [n]
    body = list(n.to_bytes((n.bit_length() + 7) // 8, "big"))
    return [0x80 | len(body)] + body

def write_head(tag, length):
    if tag == 0: raise TlvError("Malformed")
    tb = list(tag.to_bytes(4, "big")); tb = tb[next(i for i, b in enumerate(tb) if b):]
    if (tb[0] & 0x1F == 0x1F) != (len(tb) > 1): raise TlvError("Malformed")
    if any(not b & 0x80 for b in tb[1:-1]) or (len(tb) > 1 and tb[-1] & 0x80): raise TlvError("Malformed")
    return tb + der_length(length)

def write_integer(magnitude):
    m = list(magnitude)
    while m and m[0] == 0: m = m[1:]
    if not m: m = [0]
    if m[0] & 0x80: m = [0] + m
    return [0x02] + der_length(len(m)) + m

def integer_size(magnitude): return len(write_integer(magnitude))

if __name__ == "__main__":
    h = bytes.fromhex
    assert write_integer([1]) == list(h("020101")) and write_integer([0x80]) == list(h("02020080"))
    assert write_integer([0, 0, 0x7F]) == list(h("02017f")) and write_integer([]) == write_integer([0, 0]) == list(h("020100"))
    assert write_head(0x30, 200) == list(h("3081c8")) and write_head(0x7F49, 5) == list(h("7f4905"))
    assert write_head(0x30, 0x1234) == list(h("30821234"))
    for bad in (0x1F, 0x7F, 0x9F80, 0):
        try: write_head(bad, 1); raise AssertionError(hex(bad))
        except TlvError as e: assert e.kind == "Malformed"
    assert head(h("9f3803010203")) == (0x9F38, "ContextSpecific", False, 3, 3)
    assert head(h("7f4906860401020304")) == (0x7F49, "Application", True, 6, 3)
    assert head(h("048102aabb")) == (0x04, "Universal", False, 2, 3)                  # non-minimal length accepted
    assert validate(h("7f4906860401020304")) == 9
    for bad, kind in (("3080", "Malformed"), ("04ff", "Malformed"), ("04850000000001", "Unsupported"),
                      ("04050102", "Malformed"), ("9f", "Malformed"), ("1f8181818101", "Unsupported"), ("3002040102", "Malformed")):
        try: validate(h(bad)); raise AssertionError(bad)
        except TlvError as e: assert e.kind == kind, (bad, e.kind)
    obj = h("0400")
    for _ in range(15): obj = bytes([0x30, len(obj)]) + obj
    assert validate(obj) == len(obj)                                                   # 16 levels
    try: validate(bytes([0x30, len(obj)]) + obj); raise AssertionError("depth")
    except TlvError as e: assert e.kind == "Unsupported"
    print("testtlv self-test passed")
