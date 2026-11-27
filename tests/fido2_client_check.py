"""The FIDO2 example applet against an independent client: Yubico's python-fido2, through the virtual card.

python-fido2 talks to the applet the way it talks to a security key on an NFC reader: SELECT of the FIDO applet, then
CTAP2 messages in NFCCTAP_MSG APDUs, with chaining and GET RESPONSE. Here its APDUs go to the virtual card in-process,
through a small CtapDevice that does what python-fido2's PC/SC device does. Where pyscard is installed (the `reader`
dependency group), python-fido2's own PC/SC device runs too, over a stand-in for a reader connection.

The checks are a WebAuthn registration and authentication, made by python-fido2's client and verified by its server,
then the client PIN (both protocols), a wrong PIN, changing it, and authenticatorReset.

Usage: uv run python -I tests/fido2_client_check.py . [--backend NAME]      (default: pyvm)
"""
import sys, os, pathlib, hashlib
from cardlang import layout
from cardlang.harness import scenario
from cardlang.card import apdu, card

BACKEND, ARGS = scenario.take_backend(sys.argv[1:], default="pyvm")
ROOT = pathlib.Path(ARGS[0]).resolve() if ARGS else layout.at().root
L = layout.at(ROOT)

from fido2.ctap import CtapDevice, CtapError
from fido2.hid import CAPABILITY, CTAPHID
from fido2.ctap2 import Ctap2, ClientPin
from fido2.ctap2.pin import PinProtocolV1, PinProtocolV2
from fido2.client import Fido2Client, DefaultClientDataCollector, UserInteraction, ClientError
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity

AID_FIDO = bytes.fromhex("A0000006472F0001")
ORIGIN, RP_ID = "https://example.com", "example.com"

results = []
def check(name, cond, detail=""):
    results.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + ("" if cond else " | " + str(detail)))

def new_card():
    c = card.load(L.examples / "security-key.json", BACKEND)
    c.seed(os.urandom(32)); c.open(); c.power_on()
    return c

class CardCtapDevice(CtapDevice):
    """A CtapDevice over the virtual card, sending APDUs as python-fido2's PC/SC device does."""
    def __init__(self, vc):
        self.vc = vc
        r = vc.transmit(apdu.build(0x00, 0xA4, 0x04, 0x00, AID_FIDO, 256))
        if r[-2:] != b"\x90\x00": raise ValueError(f"SELECT of the FIDO applet: {r.hex()}")
    @property
    def capabilities(self): return CAPABILITY.CBOR
    def _exchange(self, raw):
        r = self.vc.transmit(raw); body, sw = r[:-2], r[-2:]
        while sw[0] == 0x61:
            r = self.vc.transmit(apdu.build(0x00, 0xC0, 0, 0, ne=sw[1] or 256)); body += r[:-2]; sw = r[-2:]
        return body, sw
    def call(self, cmd, data=b"", event=None, on_keepalive=None):
        if cmd != CTAPHID.CBOR: raise CtapError(CtapError.ERR.INVALID_COMMAND)
        parts = [data[i:i + 250] for i in range(0, len(data), 250)] or [b""]
        for p in parts[:-1]:
            _, sw = self._exchange(apdu.build(0x90, 0x10, 0x80, 0x00, p))
            if sw != b"\x90\x00": raise CtapError(CtapError.ERR.OTHER)
        body, sw = self._exchange(apdu.build(0x80, 0x10, 0x80, 0x00, parts[-1], 256))
        if sw != b"\x90\x00": raise CtapError(CtapError.ERR.OTHER)
        return body
    @classmethod
    def list_devices(cls): return iter(())

class StandInConnection:
    """What python-fido2's PC/SC device needs of a pyscard connection, over the virtual card."""
    def __init__(self, vc): self.vc = vc
    def connect(self, *args, **kwargs): self.vc.power_on()
    def getATR(self): return list(self.vc.atr)
    def transmit(self, command, protocol=None):
        r = self.vc.transmit(bytes(command)); return list(r[:-2]), r[-2], r[-1]
    def disconnect(self): self.vc.power_off()

class Pin(UserInteraction):
    """A user who knows the PIN."""
    def __init__(self, pin): self.pin = pin
    def request_pin(self, permissions, rp_id): return self.pin

def devices():
    """(name, a function making a fresh device on a fresh card)."""
    out = [("python-fido2's CTAP2 over the card's APDUs", lambda: CardCtapDevice(new_card()))]
    try:
        from fido2.pcsc import CtapPcscDevice
        out.append(("python-fido2's PC/SC device", lambda: CtapPcscDevice(StandInConnection(new_card()), "CardLang virtual card")))
    except ImportError:
        print("(pyscard is not installed, so python-fido2's PC/SC device is not tried: uv sync --group reader)")
    return out

def webauthn(device, pin=None, uv="discouraged"):
    """Register and authenticate once with python-fido2's client and server. Returns (registered, authenticated)."""
    server = Fido2Server(PublicKeyCredentialRpEntity(name="Example", id=RP_ID))
    client = Fido2Client(device, DefaultClientDataCollector(ORIGIN), user_interaction=Pin(pin) if pin else UserInteraction())
    user = PublicKeyCredentialUserEntity(id=os.urandom(16), name="alice", display_name="Alice")
    options, state = server.register_begin(user, user_verification=uv)
    response = client.make_credential(options["publicKey"])
    auth_data = server.register_complete(state, response)
    credential = auth_data.credential_data
    options, state = server.authenticate_begin([credential], user_verification=uv)
    selection = client.get_assertion(options["publicKey"])
    server.authenticate_complete(state, [credential], selection.get_response(0))
    return auth_data, credential

def checks(name, make):
    device = make()
    ctap = Ctap2(device)
    info = ctap.get_info()
    check(f"{name}: getInfo", "FIDO_2_0" in info.versions and info.aaguid == b"CardLangExample1"
          and set(info.pin_uv_protocols) == {1, 2} and info.max_msg_size == 1280, info)

    try:
        auth_data, credential = webauthn(device)
        ok = auth_data.is_user_present() and credential.public_key is not None
        check(f"{name}: WebAuthn registration and authentication, verified by python-fido2's server", ok, auth_data)
    except Exception as e:
        check(f"{name}: WebAuthn registration and authentication, verified by python-fido2's server", False, repr(e))

    try:
        client = Fido2Client(device, DefaultClientDataCollector(ORIGIN))
        server = Fido2Server(PublicKeyCredentialRpEntity(name="Example", id=RP_ID))
        options, _ = server.authenticate_begin([{"type": "public-key", "id": os.urandom(48)}], user_verification="discouraged")
        client.get_assertion(options["publicKey"]); refused = "no error"
    except ClientError as e:
        refused = e.code == ClientError.ERR.DEVICE_INELIGIBLE or repr(e)
    check(f"{name}: an unknown credential is refused: no credential on this device", refused is True, refused)

    for protocol in (PinProtocolV2(), PinProtocolV1()):
        p = protocol.VERSION
        device = make(); ctap = Ctap2(device)
        client_pin = ClientPin(ctap, protocol)
        client_pin.set_pin("1234")
        check(f"{name}: protocol {p}: setPIN, and getInfo then says clientPin", ctap.get_info().options.get("clientPin") is True)
        try:
            auth_data, _ = webauthn(device, pin="1234", uv="required")
            check(f"{name}: protocol {p}: WebAuthn with the PIN, user verified", auth_data.is_user_verified(), auth_data)
        except Exception as e:
            check(f"{name}: protocol {p}: WebAuthn with the PIN, user verified", False, repr(e))
        before = client_pin.get_pin_retries()[0]
        try: client_pin.get_pin_token("9999"); wrong = None
        except CtapError as e: wrong = e.code
        check(f"{name}: protocol {p}: a wrong PIN: PIN_INVALID, one try fewer",
              wrong == CtapError.ERR.PIN_INVALID and client_pin.get_pin_retries()[0] == before - 1, f"{wrong} {before}")
        client_pin.change_pin("1234", "567890")
        try: client_pin.get_pin_token("1234"); old = None
        except CtapError as e: old = e.code
        token = client_pin.get_pin_token("567890")
        check(f"{name}: protocol {p}: changePIN: the old PIN fails, the new one gives a token", old == CtapError.ERR.PIN_INVALID and token, old)
        ctap.reset()
        check(f"{name}: protocol {p}: authenticatorReset clears the PIN", ctap.get_info().options.get("clientPin") is False)

def main():
    for name, make in devices():
        checks(name, make)
    print("ALL PASS" if all(results) else "FAILURES")
    return all(results)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
