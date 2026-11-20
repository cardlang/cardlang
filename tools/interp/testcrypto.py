"""Test-only cryptography for the reference interpreter (WP4, base API plan B7): standard library only.

AES-128/256 (FIPS 197) with CBC, HKDF-SHA-256 (RFC 5869), ECDSA P-256 with SHA-256 and RFC 6979 nonces, and ECDH P-256.
Not constant-time and not hardened: it exists only to produce and check real values in conformance tests.
"""
import hashlib, hmac
import p256

# ------------------------------------------------------------------ AES
def _xtime(a): return ((a << 1) ^ 0x1B) & 0xFF if a & 0x80 else a << 1

def _mul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a = _xtime(a); b >>= 1
    return r

def _build_sbox():
    sbox = [0] * 256
    for x in range(256):
        inv = 0 if x == 0 else next(y for y in range(1, 256) if _mul(x, y) == 1)
        s = inv
        for i in range(1, 5): s ^= ((inv << i) | (inv >> (8 - i))) & 0xFF
        sbox[x] = s ^ 0x63
    return sbox

SBOX = _build_sbox()
INV_SBOX = [0] * 256
for _i, _v in enumerate(SBOX): INV_SBOX[_v] = _i

def _expand(key):
    nk = len(key) // 4; rounds = nk + 6
    w = [list(key[4 * i:4 * i + 4]) for i in range(nk)]
    rcon = 1
    for i in range(nk, 4 * (rounds + 1)):
        t = list(w[i - 1])
        if i % nk == 0:
            t = [SBOX[b] for b in t[1:] + t[:1]]; t[0] ^= rcon; rcon = _xtime(rcon)
        elif nk > 6 and i % nk == 4:
            t = [SBOX[b] for b in t]
        w.append([a ^ b for a, b in zip(w[i - nk], t)])
    return [sum(w[4 * r:4 * r + 4], []) for r in range(rounds + 1)]

def _shift(s, inv=False):
    out = [0] * 16
    for c in range(4):
        for r in range(4):
            src = (c + r) % 4 if not inv else (c - r) % 4
            out[4 * c + r] = s[4 * src + r]
    return out

def _mix(s, inv=False):
    m = (14, 11, 13, 9) if inv else (2, 3, 1, 1)
    out = []
    for c in range(4):
        col = s[4 * c:4 * c + 4]
        for r in range(4):
            out.append(_mul(col[0], m[(0 - r) % 4]) ^ _mul(col[1], m[(1 - r) % 4]) ^ _mul(col[2], m[(2 - r) % 4]) ^ _mul(col[3], m[(3 - r) % 4]))
    return out

def aes_block(key, block, decrypt=False):
    rk = _expand(list(key)); n = len(rk) - 1; s = list(block)
    if not decrypt:
        s = [a ^ b for a, b in zip(s, rk[0])]
        for r in range(1, n + 1):
            s = _shift([SBOX[b] for b in s])
            if r != n: s = _mix(s)
            s = [a ^ b for a, b in zip(s, rk[r])]
    else:
        s = [a ^ b for a, b in zip(s, rk[n])]
        for r in range(n - 1, -1, -1):
            s = [INV_SBOX[b] for b in _shift(s, inv=True)]
            s = [a ^ b for a, b in zip(s, rk[r])]
            if r != 0: s = _mix(s, inv=True)
    return s

def aes_cbc(key, iv, data, decrypt=False):
    out, prev = [], list(iv)
    for i in range(0, len(data), 16):
        block = list(data[i:i + 16])
        if decrypt:
            plain = [a ^ b for a, b in zip(aes_block(key, block, True), prev)]; out += plain; prev = block
        else:
            prev = aes_block(key, [a ^ b for a, b in zip(block, prev)]); out += prev
    return out

# ------------------------------------------------------------------ HMAC, HKDF
def hmac_sha256(key, data): return list(hmac.new(bytes(key), bytes(data), hashlib.sha256).digest())

def hkdf_sha256(ikm, salt, info, length):
    prk = hmac.new(bytes(salt) if salt else b"\0" * 32, bytes(ikm), hashlib.sha256).digest()
    okm, t, i = b"", b"", 1
    while len(okm) < length:
        t = hmac.new(prk, t + bytes(info) + bytes([i]), hashlib.sha256).digest(); okm += t; i += 1
    return list(okm[:length])

# ------------------------------------------------------------------ ECDSA, ECDH
def _rfc6979_k(d, h1):
    x = d.to_bytes(32, "big"); h = (int.from_bytes(h1, "big") % p256.N).to_bytes(32, "big")
    mac = lambda k, m: hmac.new(k, m, hashlib.sha256).digest()
    v, k = b"\x01" * 32, b"\x00" * 32
    k = mac(k, v + b"\x00" + x + h); v = mac(k, v)
    k = mac(k, v + b"\x01" + x + h); v = mac(k, v)
    while True:
        v = mac(k, v); cand = int.from_bytes(v, "big")
        if 1 <= cand < p256.N: return cand
        k = mac(k, v + b"\x00"); v = mac(k, v)

def ecdsa_sign(d, message):
    return ecdsa_sign_digest(d, hashlib.sha256(bytes(message)).digest())

def ecdsa_sign_digest(d, digest):
    h1 = bytes(digest); e = int.from_bytes(h1, "big")
    while True:
        k = _rfc6979_k(d, h1)
        r = p256.mul(k)[0] % p256.N
        s = pow(k, p256.N - 2, p256.N) * (e + r * d) % p256.N
        if r and s: return list(r.to_bytes(32, "big") + s.to_bytes(32, "big"))

def ecdsa_verify(q, message, signature):
    return ecdsa_verify_digest(q, hashlib.sha256(bytes(message)).digest(), signature)

def ecdsa_verify_digest(q, digest, signature):
    if len(signature) != 64: return False
    r, s = int.from_bytes(bytes(signature[:32]), "big"), int.from_bytes(bytes(signature[32:]), "big")
    if not (1 <= r < p256.N and 1 <= s < p256.N): return False
    e = int.from_bytes(bytes(digest), "big"); w = pow(s, p256.N - 2, p256.N)
    pt = p256.add(p256.mul(e * w % p256.N), p256.mul(r * w % p256.N, q))
    return pt is not None and pt[0] % p256.N == r

def ecdh(d, q): return list(p256.mul(d, q)[0].to_bytes(32, "big"))

if __name__ == "__main__":
    h = bytes.fromhex
    # FIPS 197 C.1 and C.3
    assert aes_block(range(16), h("00112233445566778899aabbccddeeff")) == list(h("69c4e0d86a7b0430d8cdb78070b4c55a"))
    assert aes_block(range(32), h("00112233445566778899aabbccddeeff")) == list(h("8ea2b7ca516745bfeafc49904b496089"))
    assert aes_block(range(32), h("8ea2b7ca516745bfeafc49904b496089"), True) == list(h("00112233445566778899aabbccddeeff"))
    data = list(range(48)); iv = list(range(100, 116))
    assert aes_cbc(range(16), iv, aes_cbc(range(16), iv, data), True) == data
    # RFC 4231 test case 2, RFC 5869 test case 1
    assert hmac_sha256(b"Jefe", b"what do ya want for nothing?") == list(h("5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"))
    assert hkdf_sha256(b"\x0b" * 22, h("000102030405060708090a0b0c"), h("f0f1f2f3f4f5f6f7f8f9"), 42) == list(h(
        "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865"))
    # RFC 6979 A.2.5, message "sample", SHA-256
    d = 0xC9AFA9D845BA75166B5C215767B1D6934E50C3DB36E89B127B8A622B120F6721
    sig = ecdsa_sign(d, b"sample")
    assert sig == list(h("EFD48B2AACB6A8FD1140DD9CD45E81D69D2C877B56AAF991C34D0EA84EAF3716"
                         "F7CB1C942D657C41D436C7A1B6E29F65F3E900DBB9AFF4064DC4AB2F843ACDA8")), bytes(sig).hex()
    q = p256.mul(d)
    assert ecdsa_verify(q, b"sample", sig) and not ecdsa_verify(q, b"samplf", sig)
    d2 = 12345; assert ecdh(d, p256.mul(d2)) == ecdh(d2, q)
    print("testcrypto self-test passed")
