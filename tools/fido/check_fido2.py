"""Independent check of the FIDO2 example applet (WP8 F4).

Builds examples/fido2 with the full checker and the ISO 7816 binding check (BP-50a, BP-52), runs a scripted CTAP
session through the reference interpreter, and checks every response with code of its own: a CBOR codec, a DER
parser, and ECDSA verification from tools/interp/testcrypto.py. None of the applet's logic is reused.

Usage: python -I tools/fido/check_fido2.py . [--backend NAME]      (default: interp, the reference interpreter)
"""
import sys, pathlib, hashlib, hmac
TOOLS = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "harness"))
import scenario
BACKEND, ARGS = scenario.take_backend(sys.argv[1:])
ROOT = pathlib.Path(ARGS[0]).resolve() if ARGS else TOOLS.parent
sys.path.insert(0, str(ROOT / "tools" / "checkers")); sys.path.insert(0, str(ROOT / "tools" / "interp"))
from lexcheck import lex
import layout
import grammar, backends, p256, testcrypto

# ------------------------------------------------------------------ a small, independent CBOR codec
def enc(v):
    def head(major, n):
        if n < 24: return bytes([major << 5 | n])
        for ai, size in ((24, 1), (25, 2), (26, 4), (27, 8)):
            if n < 1 << (8 * size): return bytes([major << 5 | ai]) + n.to_bytes(size, "big")
    if v is False: return b"\xf4"
    if v is True: return b"\xf5"
    if isinstance(v, int): return head(0, v) if v >= 0 else head(1, -1 - v)
    if isinstance(v, bytes): return head(2, len(v)) + v
    if isinstance(v, str): return head(3, len(v.encode())) + v.encode()
    if isinstance(v, list): return head(4, len(v)) + b"".join(enc(x) for x in v)
    if isinstance(v, dict):
        items = sorted((enc(k), enc(x)) for k, x in v.items())          # canonical: bytewise key order
        return head(5, len(items)) + b"".join(k + x for k, x in items)
    raise TypeError(v)

def dec(b, i=0):
    """(value, next offset). Raises on anything CTAP does not use."""
    ib = b[i]; major, ai = ib >> 5, ib & 31; i += 1
    if major == 7:
        return {20: False, 21: True, 22: None}[ai], i
    if ai < 24: n = ai
    else:
        size = 1 << (ai - 24); n = int.from_bytes(b[i:i + size], "big"); i += size
    if major == 0: return n, i
    if major == 1: return -1 - n, i
    if major == 2: return bytes(b[i:i + n]), i + n
    if major == 3: return bytes(b[i:i + n]).decode(), i + n
    if major == 4:
        out = []
        for _ in range(n): x, i = dec(b, i); out.append(x)
        return out, i
    if major == 5:
        out = {}
        for _ in range(n):
            k, i = dec(b, i); x, i = dec(b, i); out[k] = x
        return out, i
    raise ValueError(f"major type {major}")

def der_to_raw(sig):
    assert sig[0] == 0x30 and sig[1] == len(sig) - 2, "DER SEQUENCE"
    out, i = [], 2
    for _ in range(2):
        assert sig[i] == 0x02; n = sig[i + 1]; v = sig[i + 2:i + 2 + n]
        assert n >= 1 and not (n > 1 and v[0] == 0 and v[1] < 0x80) and v[0] < 0x80, "minimal DER INTEGER"
        out.append(int.from_bytes(v, "big")); i += 2 + n
    assert i == len(sig)
    return list(out[0].to_bytes(32, "big") + out[1].to_bytes(32, "big"))

# ------------------------------------------------------------------ the session
class Session:
    def __init__(self):
        d = layout.at(ROOT).examples / "fido2"
        import project; files = project.program_files(d)
        g = grammar.load_grammar()
        for f in files:
            assert g.recognize(lex(f.read_bytes()))[0], f"{f.name} does not derive from Annex A"
        self.card = backends.build(BACKEND, files, "iso7816")
        self.card.install(); self.card.session_start()
    def ctap(self, code, params=None):
        data = bytes([code]) + (enc(params) if params is not None else b"")
        out = self.card.command(list(b"\x80\x10\x00\x00" + data), 1280)
        assert out[0] == "ok", f"expected 9000, got {out}"
        return out[1][0], (dec(bytes(out[1]), 1)[0] if len(out[1]) > 1 else None)
    def apdu(self, raw):
        return scenario.status_word(self.card.command(list(raw), 1280))

# ------------------------------------------------------------------ the platform side of the PIN protocols
class PinHost:
    """CTAP 2.1 §6.5.6 and §6.5.7, written independently of the applet."""
    def __init__(self, session, protocol):
        self.s, self.protocol = session, protocol
        self.d = 0x1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF % p256.N
    def agree(self):
        st, out = self.s.ctap(0x06, {1: self.protocol, 2: 2})
        assert st == 0, f"getKeyAgreement: {st:#x}"
        key = out[1]; peer = (int.from_bytes(key[-2], "big"), int.from_bytes(key[-3], "big"))
        assert key[1] == 2 and key[3] == -25 and key[-1] == 1 and p256.on_curve(peer), key
        z = p256.mul(self.d, peer)[0].to_bytes(32, "big")
        if self.protocol == 1:
            self.secret = hashlib.sha256(z).digest()
        else:
            salt = bytes(32)
            self.secret = bytes(testcrypto.hkdf_sha256(z, salt, b"CTAP2 HMAC key", 32) + testcrypto.hkdf_sha256(z, salt, b"CTAP2 AES key", 32))
        q = p256.mul(self.d)
        self.cose = {1: 2, 3: -25, -1: 1, -2: q[0].to_bytes(32, "big"), -3: q[1].to_bytes(32, "big")}
        return key
    def encrypt(self, data):
        if self.protocol == 1: return bytes(testcrypto.aes_cbc(self.secret, bytes(16), data))
        iv = hashlib.sha256(b"iv" + data).digest()[:16]
        return iv + bytes(testcrypto.aes_cbc(self.secret[32:], iv, data))
    def decrypt(self, data):
        if self.protocol == 1: return bytes(testcrypto.aes_cbc(self.secret, bytes(16), data, decrypt=True))
        return bytes(testcrypto.aes_cbc(self.secret[32:], data[:16], data[16:], decrypt=True))
    def authenticate(self, key, message):
        mac = hmac.new(key[:32], message, hashlib.sha256).digest()
        return mac[:16] if self.protocol == 1 else mac
    def set_pin(self, pin):
        self.agree(); enc = self.encrypt(pin.encode().ljust(64, b"\0"))
        return self.s.ctap(0x06, {1: self.protocol, 2: 3, 3: self.cose, 4: self.authenticate(self.secret, enc), 5: enc})[0]
    def change_pin(self, old, new):
        self.agree(); new_enc = self.encrypt(new.encode().ljust(64, b"\0"))
        hash_enc = self.encrypt(hashlib.sha256(old.encode()).digest()[:16])
        return self.s.ctap(0x06, {1: self.protocol, 2: 4, 3: self.cose, 4: self.authenticate(self.secret, new_enc + hash_enc),
                                  5: new_enc, 6: hash_enc})[0]
    def get_token(self, pin):
        self.agree(); hash_enc = self.encrypt(hashlib.sha256(pin.encode()).digest()[:16])
        st, out = self.s.ctap(0x06, {1: self.protocol, 2: 5, 3: self.cose, 6: hash_enc})
        return st, (self.decrypt(out[2]) if st == 0 else None)
    def retries(self):
        st, out = self.s.ctap(0x06, {1: self.protocol, 2: 1})
        return out[3] if st == 0 else None

def pin_checks(protocol, make_credential, assertion):
    s = Session(); h = PinHost(s, protocol); tag = f"protocol {protocol}: "
    mc, rp, cdh = make_credential
    check(tag + "PIN retries before a PIN is set: 8", h.retries() == 8)
    st, _ = s.ctap(0x01, mc)
    check(tag + "makeCredential without a PIN: allowed", st == 0, hex(st))
    check(tag + "setPIN", h.set_pin("1234") == 0)
    st, info = s.ctap(0x04)
    check(tag + "getInfo: clientPin true after setPIN", info[4]["clientPin"] is True, str(info[4]))
    check(tag + "setPIN again: PIN auth invalid (0x33)", h.set_pin("9999") == 0x33)
    st, _ = s.ctap(0x01, mc)
    check(tag + "makeCredential without a token: token required (0x36)", st == 0x36, hex(st))
    st, token = h.get_token("1234")
    check(tag + "getPinToken: a 32-byte token", st == 0 and len(token) == 32, f"{st:#x}")
    if st != 0:
        return                                   # the rest of the session depends on the token
    st, att = s.ctap(0x01, {**mc, 8: h.authenticate(token, cdh), 9: protocol})
    ok = st == 0 and att[2][32] == 0x45
    check(tag + "makeCredential with the token: UP, UV and AT set (0x45)", ok, f"{st:#x}")
    if ok:
        cred = att[2][55:103]; cose, _ = dec(att[2], 103)
        q = (int.from_bytes(cose[-2], "big"), int.from_bytes(cose[-3], "big"))
        cdh2 = hashlib.sha256(b"pin assertion").digest()
        st, ga = s.ctap(0x02, {1: rp, 2: cdh2, 3: [{"id": cred, "type": "public-key"}], 6: h.authenticate(token, cdh2), 7: protocol})
        valid = st == 0 and ga[2][32] == 0x05 and testcrypto.ecdsa_verify(q, ga[2] + cdh2, der_to_raw(ga[3]))
        check(tag + "getAssertion with the token: UV set, signature verifies", valid, f"{st:#x}")
        st, _ = s.ctap(0x02, {1: rp, 2: cdh2, 3: [{"id": cred, "type": "public-key"}], 6: bytes(len(token) // (2 if protocol == 1 else 1)), 7: protocol})
        check(tag + "getAssertion with a wrong pinUvAuthParam: 0x33", st == 0x33, hex(st))
    st, _ = h.get_token("0000")
    check(tag + "wrong PIN: PIN invalid (0x31), retries 7", st == 0x31 and h.retries() == 7, hex(st))
    h.get_token("0000"); st, _ = h.get_token("0000")
    check(tag + "third consecutive wrong PIN: PIN auth blocked (0x34)", st == 0x34, hex(st))
    st, _ = h.get_token("1234")
    check(tag + "blocked until a power cycle, even with the right PIN", st == 0x34, hex(st))
    s.card.reset(); s.card.session_start()
    st, token = h.get_token("1234")
    check(tag + "after a power cycle: the right PIN works, retries back to 8", st == 0 and h.retries() == 8, hex(st))
    check(tag + "changePIN", h.change_pin("1234", "567890") == 0)
    st, _ = h.get_token("1234")
    st2, _ = h.get_token("567890")
    check(tag + "after changePIN: the old PIN fails, the new one works", st == 0x31 and st2 == 0, f"{st:#x} {st2:#x}")
    for i in range(8):
        if i and i % 3 == 0:
            s.card.reset(); s.card.session_start()
        st, _ = h.get_token("0000")
    check(tag + "eight wrong PINs: PIN blocked (0x32)", st == 0x32 and h.retries() == 0, f"{st:#x} {h.retries()}")
    s.card.reset(); s.card.session_start()
    st, _ = h.get_token("567890")
    check(tag + "PIN blocked survives a power cycle", st == 0x32, hex(st))
    st, _ = s.ctap(0x07)
    st2, info = s.ctap(0x04)
    check(tag + "reset clears the PIN", st == 0 and info[4]["clientPin"] is False and h.retries() == 8, str(info[4]))

results = []
def check(name, cond, detail=""):
    results.append(cond); print(("PASS " if cond else "FAIL ") + name + ("" if cond else " | " + detail))

def main():
    s = Session()
    sel = s.card.select()
    check("SELECT returns FIDO_2_0", sel == ("ok", list(b"FIDO_2_0")), str(sel))

    st, info = s.ctap(0x04)
    check("getInfo", st == 0 and info[1] == ["FIDO_2_0"] and info[3] == b"CardLangExample1"
          and info[4] == {"rk": False, "up": True, "plat": False, "clientPin": False} and info[5] == 1280
          and info[6] == [2, 1], str(info))

    rp, cdh = "webauthn.io", hashlib.sha256(b"client data").digest()
    mc = {1: cdh, 2: {"id": rp, "name": "WebAuthn.io"}, 3: {"id": b"\x01", "name": "alice"},
          4: [{"alg": -257, "type": "public-key"}, {"alg": -7, "type": "public-key"}]}
    st, att = s.ctap(0x01, mc)
    ok = st == 0 and att[1] == "none" and att[3] == {}
    a = att[2] if ok else b""
    ok = ok and a[:32] == hashlib.sha256(rp.encode()).digest() and a[32] == 0x41 and a[37:53] == b"CardLangExample1"
    cred_len = int.from_bytes(a[53:55], "big") if ok else 0
    cred = a[55:55 + cred_len]
    cose, end = dec(a, 55 + cred_len) if ok else ({}, 0)
    ok = ok and cred_len == 48 and end == len(a) and cose.get(1) == 2 and cose.get(3) == -7 and cose.get(-1) == 1
    q = (int.from_bytes(cose[-2], "big"), int.from_bytes(cose[-3], "big")) if ok else None
    check("makeCredential: none attestation, authData, COSE key on the curve", ok and p256.on_curve(q), repr(att)[:200])
    first_count = int.from_bytes(a[33:37], "big") if ok else -1

    def assertion(rp_id, cred_id, client_hash):
        return s.ctap(0x02, {1: rp_id, 2: client_hash, 3: [{"id": cred_id, "type": "public-key"}]})
    for i in (1, 2):
        cdh2 = hashlib.sha256(b"assertion %d" % i).digest()
        st, ga = assertion(rp, cred, cdh2)
        ad = ga[2] if st == 0 else b""
        ok = st == 0 and ga[1] == {"id": cred, "type": "public-key"} and len(ad) == 37 and ad[:32] == a[:32] and ad[32] == 0x01
        count = int.from_bytes(ad[33:37], "big") if ok else -1
        valid = ok and testcrypto.ecdsa_verify(q, ad + cdh2, der_to_raw(ga[3]))
        check(f"getAssertion {i}: DER signature verifies with the credential's COSE key", valid, repr(ga)[:200])
        check(f"getAssertion {i}: counter increases", count == first_count + i, f"{count}")

    st, _ = assertion("evil.example", cred, cdh)
    check("getAssertion for another RP: no credentials (0x2E)", st == 0x2E, hex(st))
    tampered = cred[:-1] + bytes([cred[-1] ^ 1])
    st, _ = assertion(rp, tampered, cdh)
    check("getAssertion with a tampered credential ID: no credentials (0x2E)", st == 0x2E, hex(st))
    st, _ = s.ctap(0x01, {**mc, 5: [{"id": cred, "type": "public-key"}]})
    check("makeCredential with the credential in excludeList: 0x19", st == 0x19, hex(st))
    st, _ = s.ctap(0x01, {**mc, 4: [{"alg": -257, "type": "public-key"}]})
    check("makeCredential without ES256: unsupported algorithm (0x26)", st == 0x26, hex(st))
    st, _ = s.ctap(0x01, {**mc, 7: {"rk": True}})
    check("makeCredential with rk: unsupported option (0x2B)", st == 0x2B, hex(st))
    st, _ = s.ctap(0x01, {1: cdh})
    check("makeCredential without rp: missing parameter (0x14)", st == 0x14, hex(st))
    out = s.card.command(list(b"\x80\x10\x00\x00\x01" + bytes.fromhex("a1011805")), 1280)
    check("non-canonical CBOR: invalid CBOR (0x12)", out[0] == "ok" and out[1] == [0x12], str(out))
    st, _ = s.ctap(0x99)
    check("unknown CTAP command: invalid command (0x01)", st == 0x01, hex(st))
    check("unknown INS: status word 6D00", s.apdu(b"\x80\x20\x00\x00") == 0x6D00)
    check("short APDU: status word 6700", s.apdu(b"\x80") == 0x6700)

    st, _ = s.ctap(0x07)
    check("reset", st == 0, hex(st))
    st, _ = assertion(rp, cred, cdh)
    check("after reset, the old credential is unknown (0x2E)", st == 0x2E, hex(st))
    st, att = s.ctap(0x01, mc)
    check("after reset, the counter starts again at 0", st == 0 and att[2][33:37] == b"\0\0\0\0", repr(att)[:120])

    s.card.reset(); s.card.session_start()
    st, att2 = s.ctap(0x01, mc)
    cred2 = att2[2][55:103]
    st2, _ = assertion(rp, cred2, cdh)
    check("after a security reset, credentials still work (persistent HMAC keys)", st == 0 and st2 == 0, f"{st} {st2}")

    for protocol in (2, 1):
        pin_checks(protocol, (mc, rp, cdh), assertion)
    print("ALL PASS" if all(results) else "FAILURES")

if __name__ == "__main__":
    main()
