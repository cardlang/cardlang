"""P-256 (secp256r1) for the reference interpreter: test-only, standard library only (base API plan B7).

Not constant-time and not hardened: it exists only to produce and check real values in conformance tests.
"""
P = 2**256 - 2**224 + 2**192 + 2**96 - 1
A = P - 3
B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
G = (0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
     0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5)

def on_curve(pt):
    if pt is None: return False
    x, y = pt
    return 0 <= x < P and 0 <= y < P and (y * y - (x * x * x + A * x + B)) % P == 0

def add(p1, p2):
    if p1 is None: return p2
    if p2 is None: return p1
    (x1, y1), (x2, y2) = p1, p2
    if x1 == x2 and (y1 + y2) % P == 0: return None
    if p1 == p2: lam = (3 * x1 * x1 + A) * pow(2 * y1, P - 2, P) % P
    else: lam = (y2 - y1) * pow(x2 - x1, P - 2, P) % P
    x3 = (lam * lam - x1 - x2) % P
    return (x3, (lam * (x1 - x3) - y1) % P)

def mul(k, pt=G):
    result, addend = None, pt
    while k:
        if k & 1: result = add(result, addend)
        addend = add(addend, addend); k >>= 1
    return result

def encode_point(pt):
    return [4] + list(pt[0].to_bytes(32, "big")) + list(pt[1].to_bytes(32, "big"))

def decode_point(data):
    """An uncompressed SEC 1 point, or None if it is malformed or not on the curve."""
    if len(data) != 65 or data[0] != 4: return None
    pt = (int.from_bytes(bytes(data[1:33]), "big"), int.from_bytes(bytes(data[33:]), "big"))
    return pt if on_curve(pt) else None

if __name__ == "__main__":
    # RFC 6979 A.2.5: the P-256 key pair
    d = 0xC9AFA9D845BA75166B5C215767B1D6934E50C3DB36E89B127B8A622B120F6721
    q = mul(d)
    assert q == (0x60FED4BA255A9D31C961EB74C6356D68C049B8923B61FA6CE669622E60F29FB6,
                 0x7903FE1008B8BC99A41AE9E95628BC64F2F1B20C2D7E9F5177A3C294D4462299), q
    assert on_curve(q) and mul(N) is None
    print("p256 self-test passed")
