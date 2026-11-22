"""Canonical CBOR for the reference interpreter (WP5): test-only, standard library only.

validate() is the strict check of profile §9 (BP-36). head() and skip() check each head they read, but not map key
order, which needs per-level state (W5). Errors are raised as CborError("Malformed") or CborError("Unsupported").
"""
MAX_DEPTH = 16                                   # the minimum the profile requires for validate (W5)
MAJORS = ["Unsigned", "Negative", "Bytes", "Text", "Array", "Map", "Tag", "Simple"]

class CborError(Exception):
    def __init__(self, kind): super().__init__(kind); self.kind = kind

def read_head(d, i):
    """(major, argument, size) of the head at d[i], checking well-formedness and the shortest form."""
    if i >= len(d): raise CborError("Malformed")
    ib = d[i]; major, ai = ib >> 5, ib & 31
    if major == 7:
        if 20 <= ai <= 23: return major, ai, 1
        if 25 <= ai <= 27: raise CborError("Unsupported")         # floating point
        raise CborError("Malformed")                              # other simple values, reserved, break
    if ai < 24: return major, ai, 1
    if ai > 27: raise CborError("Malformed")                      # 28-30 reserved, 31 indefinite length
    n = 1 << (ai - 24)
    if i + 1 + n > len(d): raise CborError("Malformed")
    val = int.from_bytes(bytes(d[i + 1:i + 1 + n]), "big")
    if val < (24 if n == 1 else 1 << (4 * n)): raise CborError("Malformed")   # not the shortest form
    return major, val, 1 + n

def head(d):
    major, val, size = read_head(d, 0)
    if val > 0xFFFFFFFF: raise CborError("Unsupported")
    return MAJORS[major], val, size

def skip(d):
    pos, pending = 0, 1
    while pending:
        major, val, size = read_head(d, pos); pos += size; pending -= 1
        if major in (2, 3):
            if pos + val > len(d): raise CborError("Malformed")
            pos += val
        elif major == 4: pending += val
        elif major == 5: pending += 2 * val
        elif major == 6: pending += 1
    return pos

def _validate(d, pos, depth):
    if depth > MAX_DEPTH: raise CborError("Unsupported")
    major, val, size = read_head(d, pos); p = pos + size
    if major in (2, 3):
        if p + val > len(d): raise CborError("Malformed")
        if major == 3:
            try: bytes(d[p:p + val]).decode("utf-8")
            except UnicodeDecodeError: raise CborError("Malformed")
        return p + val
    if major == 4:
        for _ in range(val): p = _validate(d, p, depth + 1)
        return p
    if major == 5:
        prev = None
        for _ in range(val):
            start = p; p = _validate(d, p, depth + 1); key = bytes(d[start:p])
            if prev is not None and not prev < key:
                raise CborError("Malformed")                      # not in bytewise order (BP-36, R1), or a duplicate
            prev = key; p = _validate(d, p, depth + 1)
        return p
    if major == 6: return _validate(d, p, depth + 1)
    return p

def validate(d): return _validate(list(d), 0, 1)

def write_head(major, val):
    m = MAJORS.index(major) << 5
    if major == "Simple":
        if not 20 <= val <= 23: raise CborError("Malformed")
        return [m | val]
    if val < 24: return [m | val]
    for ai, n in ((24, 1), (25, 2), (26, 4)):
        if val < 1 << (8 * n): return [m | ai] + list(val.to_bytes(n, "big"))
    raise CborError("Unsupported")

def write_int(v): return write_head("Unsigned", v) if v >= 0 else write_head("Negative", -1 - v)

if __name__ == "__main__":
    h = bytes.fromhex
    # RFC 8949 Appendix A
    for v, enc in ((0, "00"), (23, "17"), (24, "1818"), (100, "1864"), (1000, "1903e8"), (1000000, "1a000f4240"),
                   (-1, "20"), (-10, "29"), (-100, "3863"), (-1000, "3903e7")):
        assert write_int(v) == list(h(enc)), v
    for enc in ("6161", "4401020304", "83010203", "a201020304", "a26161016162820203", "f5", "f6", "c11a514b67b0"):
        assert validate(h(enc)) == len(h(enc)) == skip(h(enc)), enc
    for bad, kind in (("1805", "Malformed"), ("a2030001 00".replace(" ", ""), "Malformed"), ("a201000100", "Malformed"),
                      ("9f01ff", "Malformed"), ("440102", "Malformed"), ("62c328", "Malformed"), ("1c", "Malformed"),
                      ("f93c00", "Unsupported"), ("81" * 16 + "00", "Unsupported")):
        try: validate(h(bad)); raise AssertionError(bad)
        except CborError as e: assert e.kind == kind, (bad, e.kind)
    assert validate(h("81" * 15 + "00")) == 16
    assert validate(h("a21903e800617a00")) == 8                    # 1000 (19 03 e8) sorts before "z" (61 7a): bytewise
    try: validate(h("a2617a001903e800")); raise AssertionError("order")
    except CborError as e: assert e.kind == "Malformed"
    try: head(h("1b0000000100000000")); raise AssertionError("range")
    except CborError as e: assert e.kind == "Unsupported"
    print("testcbor self-test passed")
