"""The bytecode's instruction table, shared by the compiler, the Python VM and the disassembler.

The authority is vm/bytecode.md. Each entry is: mnemonic -> (opcode, operand kinds), with the kinds of BC-2:
    T type code   R region tag   C error category   O byte order
    b u8   h u16   w u32   r rel16 (signed, from the end of the instruction)   s rel8 (signed, likewise)
SWITCH is special: an h count followed by that many rel16 offsets.
"""
import struct

TYPES = {"u8": 0, "u16": 1, "u32": 2, "i8": 3, "i16": 4, "i32": 5}            # BC-3
TYPE_NAMES = {v: k for k, v in TYPES.items()}
WIDTH = {"u8": 1, "u16": 2, "u32": 4, "i8": 1, "i16": 2, "i32": 4}
SIGNED = {"i8", "i16", "i32"}
REGIONS = {"CONST": 0, "PERSISTENT": 1, "SESSION": 2, "STACK": 3, "REQUEST": 4, "RESPONSE": 5}   # VEX-7
REGION_NAMES = {v: k for k, v in REGIONS.items()}
CAT_APP, CAT_PLATFORM = 1, 2
ORDERS = {"BE": 0, "LE": 1}

OPS = {
    # 2.1 constants and stack
    "PUSH.B": (0x01, "b"), "PUSH.H": (0x02, "h"), "PUSH.W": (0x03, "w"),
    "DUP": (0x04, ""), "DROP": (0x05, ""), "SWAP": (0x06, ""), "OVER": (0x07, ""), "DUP2": (0x08, ""), "DROP2": (0x09, ""),
    # 2.2 scalar memory, region known
    "LDF": (0x10, "Th"), "STF": (0x11, "Th"), "LDS": (0x12, "Tw"), "STS": (0x13, "Tw"), "LDC": (0x14, "Tw"),
    "LDP": (0x15, "Tw"), "STP": (0x16, "Tw"),
    # 2.3 addresses
    "ADDR": (0x18, "Rw"), "INDEX": (0x19, "hw"), "INDEXV": (0x1A, "h"), "FIELD": (0x1B, "h"),
    # 2.4 indirect
    "LDI": (0x20, "T"), "STI": (0x21, "T"),
    # 2.5 views
    "VIEW": (0x24, "w"), "SLICE": (0x25, "h"),
    # 2.6 blocks
    "COPY": (0x28, "w"), "COPYV": (0x29, "h"), "FILL": (0x2A, "Tw"), "FILLB": (0x2B, "hw"), "ZERO": (0x2C, "w"),
    "WIPE": (0x2D, "w"), "WIPEV": (0x2E, "h"), "EQUAL": (0x2F, "h"), "COMPARE": (0x30, "T"),
    "ENCODE": (0x31, "TO"), "DECODE": (0x32, "TO"),
    # 2.7 arithmetic, logic, comparison, conversion
    "ADD": (0x40, "T"), "SUB": (0x41, "T"), "MUL": (0x42, "T"), "DIV": (0x43, "T"), "REM": (0x44, "T"), "NEG": (0x45, "T"),
    "WADD": (0x46, "T"), "WSUB": (0x47, "T"), "WMUL": (0x48, "T"),
    "CADD": (0x49, "T"), "CSUB": (0x4A, "T"), "CMUL": (0x4B, "T"), "CDIV": (0x4C, "T"), "CREM": (0x4D, "T"), "CNEG": (0x4E, "T"),
    "AND": (0x50, ""), "OR": (0x51, ""), "XOR": (0x52, ""), "INV": (0x53, "T"), "SHL": (0x54, "T"), "SHR": (0x55, "T"),
    "EQ": (0x56, ""), "NE": (0x57, ""), "LT": (0x58, "T"), "LE": (0x59, "T"), "GT": (0x5A, "T"), "GE": (0x5B, "T"),
    "BNOT": (0x5C, ""), "CCONVERT": (0x5D, "TT"), "TRUNC": (0x5E, "T"),
    # 2.8 control
    "JMP": (0x60, "r"), "JZ": (0x61, "r"), "JNZ": (0x62, "r"), "SWITCH": (0x63, "S"),
    # 2.9 calls and outcomes
    "CALL": (0x68, "h"), "RET": (0x69, ""), "RETV": (0x6A, ""), "ERR": (0x6B, "Ch"), "FWD": (0x6C, ""),
    "JERR": (0x6D, "r"), "JERRIS": (0x6E, "Chr"), "JERRCAT": (0x6F, "Cr"), "ERRCODE": (0x70, ""),
    "ERRGET": (0x71, ""), "ERRRAISE": (0x72, ""),                    # see bytecode.md §9
    # 2.10 transactions
    "TXN.BEGIN": (0x74, ""), "TXN.COMMIT": (0x75, ""), "TXN.ABORT": (0x76, ""),
    # 2.11 natives
    "NATIVE": (0x78, "h"),
    # 2.12 short forms (version 1): shorter encodings of the instructions above, with the same semantics
    "LDF8": (0x80, "Tb"), "STF8": (0x81, "Tb"), "LDFW": (0x82, "b"), "STFW": (0x83, "b"),
    "ADDRF": (0x84, "b"), "SLICEF": (0x85, "hbb"), "PUSH0": (0x86, ""), "PUSH1": (0x87, ""),
    "JMP8": (0x88, "s"), "JZ8": (0x89, "s"), "JNZ8": (0x8A, "s"), "JERR8": (0x8B, "s"),
    # 2.13 the second revision: further short forms, from the PIV measurements
    "LDFB": (0x8C, "b"), "STFB": (0x8D, "b"), "ADDRH": (0x8E, "Rh"),
    "JEQI8": (0x8F, "bs"), "JNEI8": (0x90, "bs"),
    "JLTI8": (0x91, "Tbs"), "JLEI8": (0x92, "Tbs"), "JGTI8": (0x93, "Tbs"), "JGEI8": (0x94, "Tbs"),
    "SLICEFK": (0x95, "hbb"),
}
SHORT_JUMP = {"JMP": "JMP8", "JZ": "JZ8", "JNZ": "JNZ8", "JERR": "JERR8"}
LONG_JUMP = {v: k for k, v in SHORT_JUMP.items()}
FORMAT = 1                                               # the image format and bytecode version (IMG-3)
BY_OPCODE = {op: (name, kinds) for name, (op, kinds) in OPS.items()}
SIZE = {"T": 1, "R": 1, "C": 1, "O": 1, "b": 1, "h": 2, "w": 4, "r": 2, "s": 1}

def size_of(name, operands=()):
    kinds = OPS[name][1]
    if kinds == "S": return 1 + 2 + 2 * len(operands)
    return 1 + sum(SIZE[k] for k in kinds)

def encode(name, operands, rel_of=None):
    """Encode one instruction. Operands are ints (types, regions etc. already converted); for `r` operands,
    rel_of(label) returns the signed offset from the end of this instruction."""
    op, kinds = OPS[name]
    out = bytearray([op])
    if kinds == "S":
        out += struct.pack("<H", len(operands))
        for lab in operands: out += struct.pack("<h", rel_of(lab))
        return bytes(out)
    for k, v in zip(kinds, operands):
        if k in "TRCOb": out += struct.pack("<B", v)
        elif k == "h": out += struct.pack("<H", v)
        elif k == "w": out += struct.pack("<I", v & 0xFFFFFFFF)
        elif k == "r": out += struct.pack("<h", rel_of(v))
        elif k == "s": out += struct.pack("<b", rel_of(v))
    return bytes(out)

def decode(code, pc):
    """Decode the instruction at pc: (name, operands, size). Raises KeyError for an invalid opcode."""
    name, kinds = BY_OPCODE[code[pc]]
    i = pc + 1; ops = []
    if kinds == "S":
        n = struct.unpack_from("<H", code, i)[0]; i += 2
        ops = [struct.unpack_from("<h", code, i + 2 * k)[0] for k in range(n)]; i += 2 * n
        return name, ops, i - pc
    for k in kinds:
        if k in "TRCOb": ops.append(code[i]); i += 1
        elif k == "h": ops.append(struct.unpack_from("<H", code, i)[0]); i += 2
        elif k == "w": ops.append(struct.unpack_from("<I", code, i)[0]); i += 4
        elif k == "r": ops.append(struct.unpack_from("<h", code, i)[0]); i += 2
        elif k == "s": ops.append(struct.unpack_from("<b", code, i)[0]); i += 1
    return name, ops, i - pc

# ------------------------------------------------------------------ natives (BC-32, V-33)
BASE_NATIVES = [
    "card.key.generate", "card.key.import", "card.key.export_public", "card.key.delete",
    "card.crypto.digest", "card.crypto.mac", "card.crypto.sign", "card.crypto.verify", "card.crypto.agree",
    "card.crypto.derive", "card.crypto.encrypt", "card.crypto.decrypt", "card.crypto.begin_digest",
    "card.crypto.begin_mac", "card.crypto.begin_sign", "card.crypto.begin_verify", "card.crypto.update",
    "card.crypto.finish", "card.crypto.finish_verify", "card.crypto.cancel", "card.random.fill",
    "card.cbor.validate", "card.cbor.head", "card.cbor.skip", "card.cbor.write_head", "card.cbor.write_int",
    "card.tlv.head", "card.tlv.skip", "card.tlv.validate", "card.der.write_head", "card.der.write_integer",
    "card.der.integer_size", "card.cbor.write_string", "card.cbor.write_bool",
    "card.crypto.sign_digest", "card.crypto.verify_digest",            # 35, 36
]
TEST_NATIVES = ["card.test.resources.create", "card.test.resources.delete", "card.test.resources.read",
                "card.test.resources.write", "card.test.sign"]
NATIVE_NUMBERS = {name: i + 1 for i, name in enumerate(BASE_NATIVES)}
NATIVE_NUMBERS.update({name: 0xF000 + i for i, name in enumerate(TEST_NATIVES)})
NATIVE_NAMES = {v: k for k, v in NATIVE_NUMBERS.items()}

# ------------------------------------------------------------------ image (IMG-3, IMG-6)
MAGIC = b"CLVM"
HEADER = struct.Struct("<4sHBBIIIIIHHHHHHIIIIIIII")       # 72 bytes
FUNC = struct.Struct("<IIBBH")                           # code, frame_size, argc, payload, operand_base
NONE_ENTRY = 0xFFFF
BINDINGS = {None: 0, "iso7816": 1, "raw": 2}
assert HEADER.size == 72 and FUNC.size == 12
