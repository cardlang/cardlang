"""Checks of the virtual card (src/cardlang/card/): APDUs, the ISO 7816 transport, and the example applets behind it.

- APDU parsing and building, for every case, short and extended, and malformed input.
- The transport, on two copies of a small echo applet (tests/testdata/echo/): SELECT with full and partial AIDs,
  chaining, extended length, long responses through 61xx and GET RESPONSE, session events, and refusals.
- The FIDO2 and PIV example checks (examples/*/check.py), replayed through the transport: every request they make
  goes to the security key (examples/security-key.json) as APDUs, once in short APDUs with chaining and GET RESPONSE,
  and once in extended APDUs.

Usage: uv run python -I tests/card_check.py . [--backend NAME]      (default: pyvm)
"""
import sys, pathlib, importlib.util, io, contextlib, types
from cardlang import layout
from cardlang.harness import scenario
from cardlang.card import apdu, card, iso7816

BACKEND, ARGS = scenario.take_backend(sys.argv[1:], default="pyvm")
ROOT = pathlib.Path(ARGS[0]).resolve() if ARGS else layout.at().root
L = layout.at(ROOT)

results = []
def check(name, cond, detail=""):
    results.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + ("" if cond else " | " + str(detail)))

def sw(r): return apdu.split(r)[1]
def data(r): return apdu.split(r)[0]

# ------------------------------------------------------------------ APDUs
def apdu_checks():
    cases = [
        (apdu.Command(0x00, 0xA4, 0x04, 0x00), "00A40400"),
        (apdu.Command(0x00, 0xB0, 0, 0, ne=256), "00B0000000"),
        (apdu.Command(0x00, 0xB0, 0, 0, ne=16), "00B0000010"),
        (apdu.Command(0x00, 0xD6, 0, 0, b"\x01\x02"), "00D60000020102"),
        (apdu.Command(0x00, 0xA4, 4, 0, b"\xA0\x00", ne=256), "00A4040002A00000"),
        (apdu.Command(0x00, 0xB0, 0, 0, ne=65536, extended=True), "00B0000000" + "0000"),
        (apdu.Command(0x00, 0xB0, 0, 0, ne=300, extended=True), "00B00000" + "00012C"),
        (apdu.Command(0x00, 0xD6, 0, 0, b"\x07" * 300, extended=True), "00D60000" + "00012C" + "07" * 300),
        (apdu.Command(0x00, 0xD6, 0, 0, b"\x07" * 300, ne=65536, extended=True), "00D60000" + "00012C" + "07" * 300 + "0000"),
    ]
    for want, text in cases:
        raw = bytes.fromhex(text)
        got = apdu.parse(raw)
        built = apdu.build(want.cla, want.ins, want.p1, want.p2, want.data, want.ne, want.extended)
        check(f"APDU {text[:24]}{'...' if len(text) > 24 else ''} parses and builds", got == want and built == raw, f"{got} / {built.hex()}")
    for bad in ("00A404", "00A4040005A000", "00A40400000002A0", "00D600000000", "00D60000000003010203FF"):
        try: apdu.parse(bytes.fromhex(bad)); ok = False
        except apdu.ApduError: ok = True
        check(f"malformed APDU {bad} is refused", ok)

# ------------------------------------------------------------------ the transport, on the echo applet
ECHO1, ECHO2 = bytes.fromhex("F0434C0101"), bytes.fromhex("F0434C020100")

def select(c, aid, ne=256, p2=0x00):
    return c.transmit(apdu.build(0x00, 0xA4, 0x04, p2, aid, ne))

def fetch(c, r):
    """The whole response data: follow 61xx with GET RESPONSE."""
    out = data(r)
    while sw(r) >> 8 == 0x61:
        r = c.transmit(apdu.build(0x00, 0xC0, 0, 0, ne=(sw(r) & 0xFF) or 256))
        out += data(r)
    return out, sw(r)

def transport_checks():
    c = card.load(L.tests / "testdata" / "echo-card.json", BACKEND)
    check("both echo applets install", all(o == ("ok", []) for _, o in c.install()), c.install())
    check("power on returns the ATR", c.power_on() == bytes.fromhex("3B80800101"))
    check("a command with no applet selected: 6985", sw(c.transmit(bytes.fromhex("0001000000"))) == 0x6985)

    r = select(c, ECHO1)
    check("SELECT by full AID runs on_select", (data(r), sw(r)) == (b"\xE0", 0x9000), r.hex())
    r = select(c, bytes.fromhex("F0434C02"))
    check("SELECT by partial AID picks the applet it starts", (data(r), sw(r)) == (b"\xE0", 0x9000) and c.selected.aid == ECHO2, r.hex())
    check("SELECT with P2 0C returns no data", select(c, ECHO1, p2=0x0C) == b"\x90\x00")
    r = select(c, bytes.fromhex("F0434C03"))
    check("SELECT of an unknown AID: 6A82, the selection stays", sw(r) == 0x6A82 and c.selected.aid == ECHO1, r.hex())

    r = c.transmit(apdu.build(0x00, 0x01, 0, 0, b"hello", 256))
    check("a short command and response", (data(r), sw(r)) == (b"hello", 0x9000), r.hex())
    big = bytes(range(256)) * 5                                     # 1280 bytes, the profile's minimum (BP-48)
    parts = [big[i:i + 255] for i in range(0, len(big), 255)]
    for p in parts[:-1]:
        r = c.transmit(apdu.build(0x10, 0x01, 0, 0, p))
        if sw(r) != 0x9000: break
    check("every part of a chain but the last: 9000", sw(r) == 0x9000, r.hex())
    got, last = fetch(c, c.transmit(apdu.build(0x00, 0x01, 0, 0, parts[-1], 256)))
    check("a 1280-byte request in a chain, and its 1280-byte response through 61xx and GET RESPONSE", (got, last) == (big, 0x9000), f"{len(got)} {last:04X}")
    r = c.transmit(apdu.build(0x00, 0x01, 0, 0, big, 65536))
    check("the same request in one extended APDU, answered at once", (data(r), sw(r)) == (big, 0x9000), f"{len(data(r))} {sw(r):04X}")
    r = c.transmit(apdu.build(0x00, 0x03, 0x01, 0x2C, ne=256))
    check("a response longer than Le: the first Le bytes, then 61 2C", len(data(r)) == 256 and sw(r) == 0x612C, f"{len(data(r))} {sw(r):04X}")
    got, last = fetch(c, r)
    check("GET RESPONSE returns the rest", got == bytes(i % 256 for i in range(300)) and last == 0x9000, f"{len(got)}")
    check("GET RESPONSE with nothing left: 6985", sw(c.transmit(bytes.fromhex("00C0000000"))) == 0x6985)
    r = c.transmit(apdu.build(0x00, 0x03, 0x00, 0x10))
    check("response data without Le: 61 10, then GET RESPONSE", sw(r) == 0x6110 and fetch(c, r)[0] == bytes(range(16)), r.hex())
    c.transmit(apdu.build(0x10, 0x01, 0, 0, b"part"))
    r = c.transmit(apdu.build(0x00, 0x02, 0, 0, ne=256))
    check("a chain broken off by another command: 6883", sw(r) == 0x6883, r.hex())
    over = c.transmit(apdu.build(0x00, 0x01, 0, 0, b"\x00" * (c.max_request + 1), 256))
    check("a request over the card's limit: 6700", sw(over) == 0x6700, over.hex())
    check("a command on logical channel 1: 6881", sw(c.transmit(bytes.fromhex("0101000000"))) == 0x6881)
    check("MANAGE CHANNEL: 6881", sw(c.transmit(bytes.fromhex("0070000001"))) == 0x6881)
    check("a malformed APDU: 6700", sw(c.transmit(bytes.fromhex("0001000005AA"))) == 0x6700)
    check("an application error reaches the host as its status word", sw(c.transmit(bytes.fromhex("0009000000"))) == 0x6D00)

    count = lambda: int.from_bytes(data(c.transmit(apdu.build(0x00, 0x02, 0, 0, ne=256))), "big")
    first = [count(), count()]
    select(c, ECHO2); select(c, ECHO1)
    check("deselection ends the session: the count starts over", first == [1, 2] and count() == 1, first)
    select(c, ECHO1)
    check("a SELECT of the selected applet keeps its session", count() == 2)
    c.power_on(); select(c, ECHO1)
    check("a reset starts a new session", count() == 1)
    c.power_off()
    r = c.transmit(apdu.build(0x00, 0xA4, 0x04, 0x00, ECHO1, 256))
    check("a command after power off powers the card on first", sw(r) == 0x9000 and count() == 1)

# ------------------------------------------------------------------ the example checks, replayed as APDUs
FIDO, PIV = bytes.fromhex("A0000006472F0001"), bytes.fromhex("A0000003080000100001 00".replace(" ", ""))

class ApduCard:
    """The backend interface (src/cardlang/harness/README.md) on top of a VirtualCard: every call becomes APDUs.
    An outcome comes back from the status word, as one that encodes to the same status word (all the checks use)."""
    def __init__(self, vc, aid, other, mode):
        self.vc, self.aid, self.other, self.mode = vc, aid, other, mode
        self.apdus = 0
    def _send(self, raw):
        self.apdus += 1
        return self.vc.transmit(raw)
    def _outcome(self, r):
        body = data(r)
        while sw(r) >> 8 == 0x61:
            r = self._send(apdu.build(0x00, 0xC0, 0, 0, ne=(sw(r) & 0xFF) or 256))
            body += data(r)
        return ("ok", list(body)) if sw(r) == 0x9000 else ("err", "app", sw(r))
    def install(self): return ("ok", [])
    def session_start(self):
        # A backend card has one applet, selected for good; over the transport a host selects it again after a reset.
        self.vc.power_on(); self.select(); return ("ok", [])
    def session_end(self): self.vc.power_off()
    def reset(self): self.vc.security_reset()
    def select(self): return self._outcome(self._send(apdu.build(0x00, 0xA4, 0x04, 0x00, self.aid, 256)))
    def deselect(self): self._send(apdu.build(0x00, 0xA4, 0x04, 0x00, self.other, 256))
    def command(self, request, capacity):
        if len(request) < 4: return self._outcome(self._send(bytes(request)))     # not an APDU: the card says 6700
        head, body = bytes(request[:4]), bytes(request[4:])
        if self.mode == "extended":
            return self._outcome(self._send(apdu.build(*head, body, 65536, extended=True)))
        parts = [body[i:i + 255] for i in range(0, len(body), 255)] or [b""]
        for p in parts[:-1]:
            r = self._send(apdu.build(head[0] | 0x10, *head[1:], p))
            if sw(r) != 0x9000: return self._outcome(r)
        return self._outcome(self._send(apdu.build(*head, parts[-1], 256)))

def load_check(path):
    """Import an example's check.py as a module, without running its main()."""
    saved = sys.argv
    sys.argv = [str(path), str(ROOT), "--backend", BACKEND]
    try:
        spec = importlib.util.spec_from_file_location(f"replay_{path.parent.name}", path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    finally:
        sys.argv = saved
    return module

def replay_checks():
    for name, aid, other in (("fido2", FIDO, PIV), ("piv", PIV, FIDO)):
        for mode in ("short", "extended"):
            cards = []
            def build(backend, files, binding=None, aid=aid, other=other, mode=mode):
                vc = card.load(L.examples / "security-key.json", BACKEND)
                vc.install()
                cards.append(ApduCard(vc, aid, other, mode))
                return cards[-1]
            module = load_check(L.examples / name / "check.py")
            module.backends = types.SimpleNamespace(build=build)        # only the example's own reference
            out = io.StringIO()
            try:
                with contextlib.redirect_stdout(out): module.main()
            except Exception as e:
                print(out.getvalue()); check(f"{name} check through the transport ({mode} APDUs)", False, repr(e)); continue
            lines = out.getvalue().splitlines()
            fails = [l for l in lines if l.startswith("FAIL")]
            check(f"{name} check through the transport ({mode} APDUs): {len(lines) - 1} checks, {sum(c.apdus for c in cards)} APDUs",
                  lines and lines[-1] == "ALL PASS" and not fails, "; ".join(fails[:3]))

def main():
    apdu_checks()
    transport_checks()
    replay_checks()
    print("ALL PASS" if all(results) else "FAILURES")
    return all(results)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
