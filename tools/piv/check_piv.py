"""Independent check of the PIV example applet (WP12, plans_and_notes/spec-plans/WP12-piv.md §4).

Builds examples/piv with the full checker and the ISO 7816 binding check, runs a host-side PIV session (NIST SP
800-73-5 Part 2) through a harness backend, and checks every response with code of its own: a small BER-TLV
encoder and parser, and the test-only AES and P-256 of tools/interp. None of the applet's logic is reused.

Usage: python -I tools/piv/check_piv.py . [--backend NAME]      (default: interp, the reference interpreter)
"""
import sys, pathlib, os
TOOLS = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "harness"))
import scenario
BACKEND, ARGS = scenario.take_backend(sys.argv[1:])
ROOT = pathlib.Path(ARGS[0]).resolve() if ARGS else TOOLS.parent
sys.path.insert(0, str(ROOT / "tools" / "checkers")); sys.path.insert(0, str(ROOT / "tools" / "interp"))
from lexcheck import lex
import grammar, backends, testcrypto

PIV_AID = bytes.fromhex("A000000308000010000100")
ADMIN_KEY = bytes([1, 2, 3, 4, 5, 6, 7, 8] * 2)

# ------------------------------------------------------------------ a small, independent BER-TLV codec
def tlv(tag, value):
    """Encode one BER-TLV object; tag is an int whose bytes are the tag (0x5FC105 is 5F C1 05)."""
    t = tag.to_bytes((tag.bit_length() + 7) // 8 or 1, "big"); n = len(value)
    if n < 0x80: ln = bytes([n])
    elif n < 0x100: ln = bytes([0x81, n])
    else: ln = bytes([0x82]) + n.to_bytes(2, "big")
    return t + ln + bytes(value)

def parse(data):
    """Parse a sequence of BER-TLV objects into a list of (tag, value)."""
    out, i = [], 0
    while i < len(data):
        j = i + 1
        if data[i] & 0x1F == 0x1F:
            while data[j] & 0x80: j += 1
            j += 1
        tag = int.from_bytes(data[i:j], "big"); l0 = data[j]; j += 1
        if l0 < 0x80: n = l0
        else: k = l0 & 0x7F; n = int.from_bytes(data[j:j + k], "big"); j += k
        out.append((tag, bytes(data[j:j + n]))); i = j + n
    assert i == len(data), "trailing bytes"
    return out

def aes_ecb(key, block, decrypt=False):
    return bytes(testcrypto.aes_block(list(key), list(block), decrypt=decrypt))

# ------------------------------------------------------------------ the session
class Session:
    def __init__(self):
        d = ROOT / "examples" / "piv"
        files = [d / f for f in (d / "files.txt").read_text().split()]
        g = grammar.load_grammar()
        for f in files:
            assert g.recognize(lex(f.read_bytes()))[0], f"{f.name} does not derive from Annex A"
        self.card = backends.build(BACKEND, files, "iso7816")
        self.card.install(); self.card.session_start()

    def apdu(self, ins, p1, p2, data=b"", cla=0x00):
        """Send a command (BP-50: CLA INS P1 P2 and the reassembled data); returns (status word, data)."""
        out = self.card.command(list(bytes([cla, ins, p1, p2]) + bytes(data)), 2048)
        return scenario.status_word(out), bytes(out[1]) if out[0] == "ok" else b""

    def get_data(self, tag):
        return self.apdu(0xCB, 0x3F, 0xFF, tlv(0x5C, tag.to_bytes((tag.bit_length() + 7) // 8, "big")))

    def put_data(self, tag, content):
        return self.apdu(0xDB, 0x3F, 0xFF, tlv(0x5C, tag.to_bytes((tag.bit_length() + 7) // 8, "big")) + tlv(0x53, content))

    def general_authenticate(self, alg, key, children):
        return self.apdu(0x87, alg, key, tlv(0x7C, b"".join(tlv(t, v) for t, v in children)))

    def admin_auth(self, key=ADMIN_KEY):
        """Part 2, Appendix A.1: request a challenge, return its encryption."""
        sw, resp = self.general_authenticate(0x08, 0x9B, [(0x81, b"")])
        if sw != 0x9000: return sw
        challenge = dict(parse(dict(parse(resp))[0x7C]))[0x81]
        sw, _ = self.general_authenticate(0x08, 0x9B, [(0x82, aes_ecb(key, challenge))])
        return sw

# ------------------------------------------------------------------ checks
results = []

def check(name, cond, detail=""):
    results.append(cond); print(("PASS " if cond else "FAIL ") + name + ("" if cond else " | " + detail))

def core_checks(s):
    sel = s.card.select()
    apt = dict(parse(bytes(sel[1]))) if sel[0] == "ok" else {}
    inner = dict(parse(apt.get(0x61, b""))) if apt else {}
    check("SELECT returns the application property template with the full AID",
          sel[0] == "ok" and inner.get(0x4F) == PIV_AID and dict(parse(inner.get(0x79, b""))).get(0x4F) == PIV_AID[:5],
          repr(sel)[:160])
    algs = [v for t, v in parse(inner.get(0xAC, b""))] if inner else []
    check("the template lists P-256 (11) and AES-128 (08)", bytes([0x11]) in algs and bytes([0x08]) in algs, repr(algs))

    check("GET DATA of an absent object is 6A82", s.get_data(0x5FC102)[0] == 0x6A82)
    check("GET DATA of an unknown tag is 6A82", s.get_data(0x5FC1FF)[0] == 0x6A82)
    check("an unknown instruction is 6D00", s.apdu(0x00, 0, 0)[0] == 0x6D00)
    check("PUT DATA without the administrator is 6982", s.put_data(0x5FC102, b"\x30\x19" + bytes(25))[0] == 0x6982)

    # administrator authentication (Part 2, Appendix A.1 and A.2)
    check("a wrong administration key is refused (6982)", s.admin_auth(bytes(16)) == 0x6982)
    check("the administration key authenticates the administrator (A.1)", s.admin_auth() == 0x9000)
    sw, resp = s.general_authenticate(0x08, 0x9B, [(0x80, b"")])
    witness = dict(parse(dict(parse(resp))[0x7C])).get(0x80, b"") if sw == 0x9000 else b""
    host_challenge = os.urandom(16)
    sw2, resp2 = s.general_authenticate(0x08, 0x9B, [(0x80, aes_ecb(ADMIN_KEY, witness, decrypt=True)),
                                                    (0x81, host_challenge), (0x82, b"")])
    reply = dict(parse(dict(parse(resp2))[0x7C])).get(0x82, b"") if sw2 == 0x9000 else b""
    check("mutual authentication (A.2): the card proves the key too", sw == 0x9000 and sw2 == 0x9000
          and aes_ecb(ADMIN_KEY, reply, decrypt=True) == host_challenge, f"{sw:04x} {sw2:04x}")
    check("the administration key accepts only AES-128 (08); another algorithm is 6A86",
          s.general_authenticate(0x0C, 0x9B, [(0x81, b"")])[0] == 0x6A86)

    # data objects
    chuid = tlv(0x30, bytes(range(25))) + tlv(0x34, bytes(range(16))) + tlv(0x35, b"20301231") + tlv(0x3E, b"") + tlv(0xFE, b"")
    check("PUT DATA of the CHUID", s.put_data(0x5FC102, chuid)[0] == 0x9000)
    sw, resp = s.get_data(0x5FC102)
    check("GET DATA returns the CHUID inside 53", sw == 0x9000 and parse(resp) == [(0x53, chuid)], f"{sw:04x}")
    cert = tlv(0x70, os.urandom(900)) + tlv(0x71, b"\x00") + tlv(0xFE, b"")
    check("PUT DATA of a 900-byte certificate for 9A", s.put_data(0x5FC105, cert)[0] == 0x9000)
    sw, resp = s.get_data(0x5FC105)
    check("GET DATA returns the same certificate", sw == 0x9000 and parse(resp) == [(0x53, cert)], f"{sw:04x}")
    big = tlv(0x70, bytes(1950))
    check("an object larger than its buffer is refused (6A84)", s.put_data(0x5FC10A, big)[0] == 0x6A84)
    check("and leaves the object absent", s.get_data(0x5FC10A)[0] == 0x6A82)
    discovery = tlv(0x7E, tlv(0x4F, PIV_AID) + tlv(0x5F2F, b"\x40\x00"))
    check("PUT DATA of the bare Discovery Object (7E)", s.apdu(0xDB, 0x3F, 0xFF, discovery)[0] == 0x9000)
    sw, resp = s.get_data(0x7E)
    check("GET DATA returns the Discovery Object bare, not inside 53", sw == 0x9000 and resp == discovery, resp.hex())
    shorter = tlv(0x70, os.urandom(300)) + tlv(0x71, b"\x00") + tlv(0xFE, b"")
    s.put_data(0x5FC105, shorter)
    sw, resp = s.get_data(0x5FC105)
    check("PUT DATA replaces an object completely", sw == 0x9000 and parse(resp) == [(0x53, shorter)])

    # application security status (Part 2 §2.4.2, profile BP-56)
    s.card.deselect(); s.card.select()
    check("after deselection and a new SELECT, the administrator must authenticate again",
          s.put_data(0x5FC102, chuid)[0] == 0x6982)
    s.card.select()
    check("objects survive a deselection", s.get_data(0x5FC105)[0] == 0x9000)
    s.card.session_end(); s.card.session_start(); s.card.select()
    check("objects survive a power cycle", s.get_data(0x5FC102)[0] == 0x9000)

def main():
    s = Session()
    core_checks(s)
    print("ALL PASS" if all(results) else "FAILURES")

if __name__ == "__main__":
    main()
