"""ISO/IEC 7816-4 command APDUs: parsing, and building them for tests and clients.

A command APDU is a header (CLA INS P1 P2), then an optional data field with its length Lc, then an optional Le,
the most response data the host accepts. Short APDUs code Lc and Le in one byte; extended ones in two or three.
ISO 7816-4 names the four shapes cases 1 to 4:

    case 1   header
    case 2   header Le                   short: Le in 1 byte (00 means 256); extended: 00 then 2 bytes (0000 = 65536)
    case 3   header Lc data              short: Lc in 1 byte (not 00); extended: 00 then 2 bytes
    case 4   header Lc data Le           both short, or both extended (Le then in 2 bytes)

`ne` below is the number of response bytes the host expects: 0 when there is no Le.
"""
from dataclasses import dataclass

class ApduError(ValueError):
    """Bytes that are not a well-formed command APDU (answered with status word 6700)."""

@dataclass
class Command:
    cla: int
    ins: int
    p1: int
    p2: int
    data: bytes = b""
    ne: int = 0                 # the response bytes expected: 0 without Le, else 1 to 256 (short) or 65536 (extended)
    extended: bool = False

def parse(apdu):
    """The Command an APDU codes, or ApduError."""
    b = bytes(apdu)
    if len(b) < 4: raise ApduError(f"{len(b)} bytes: shorter than a header")
    cla, ins, p1, p2 = b[:4]; body = b[4:]
    if not body:
        return Command(cla, ins, p1, p2)                                            # case 1
    if len(body) == 1:
        return Command(cla, ins, p1, p2, ne=body[0] or 256)                         # case 2, short
    if body[0] != 0:                                                                # short: Lc in one byte
        lc = body[0]
        if len(body) == 1 + lc: return Command(cla, ins, p1, p2, body[1:])                          # case 3
        if len(body) == 2 + lc: return Command(cla, ins, p1, p2, body[1:-1], ne=body[-1] or 256)    # case 4
        raise ApduError(f"Lc {lc} does not match the {len(body) - 1} bytes that follow it")
    if len(body) == 3:
        return Command(cla, ins, p1, p2, ne=int.from_bytes(body[1:3], "big") or 65536, extended=True)  # case 2
    if len(body) < 3: raise ApduError("a truncated extended length")
    lc = int.from_bytes(body[1:3], "big")
    if lc == 0: raise ApduError("an extended Lc of 0")
    if len(body) == 3 + lc: return Command(cla, ins, p1, p2, body[3:], extended=True)                 # case 3
    if len(body) == 5 + lc:                                                                           # case 4
        return Command(cla, ins, p1, p2, body[3:3 + lc], ne=int.from_bytes(body[-2:], "big") or 65536, extended=True)
    raise ApduError(f"extended Lc {lc} does not match the {len(body) - 3} bytes that follow it")

def build(cla, ins, p1, p2, data=b"", ne=0, extended=None):
    """The APDU for a command. extended=None chooses extended length only when short cannot code it."""
    data = bytes(data)
    if extended is None: extended = len(data) > 255 or ne > 256
    head = bytes([cla, ins, p1, p2])
    if not extended:
        if len(data) > 255 or ne > 256: raise ApduError("too long for a short APDU")
        return head + (bytes([len(data)]) + data if data else b"") + (bytes([ne % 256]) if ne else b"")
    if len(data) > 65535 or ne > 65536: raise ApduError("too long for an extended APDU")
    out = head
    if data: out += b"\x00" + len(data).to_bytes(2, "big") + data
    if ne: out += (b"" if data else b"\x00") + (ne % 65536).to_bytes(2, "big")
    return out

def response(data, sw):
    """A response APDU: the data, then the status word's two bytes."""
    return bytes(data) + sw.to_bytes(2, "big")

def split(rapdu):
    """(data, status word) of a response APDU."""
    r = bytes(rapdu)
    if len(r) < 2: raise ApduError("a response shorter than its status word")
    return r[:-2], int.from_bytes(r[-2:], "big")
