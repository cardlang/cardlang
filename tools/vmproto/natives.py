"""The prototype's native library (VM5): the catalog APIs as `NATIVE n` executes them (vm/bytecode.md §5).

It does only what involves no cryptography (HAL-1 to HAL-3): it takes the arguments off the operand stack
(BC-34), resolves identifiers in the single identifier space (PLT-20), keeps the operation table with its lifetimes
(BP-14, BP-31), applies the profile's checks in the error precedence of BP-8, moves data between views and the HAL,
and writes results (into persistent views as one atomic update, VEX-28). CBOR, BER-TLV and DER are implemented here
(V-5), reusing the test-only codecs of tools/interp. The order of checks mirrors the reference interpreter, so both
backends give identical outcomes.
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "interp", HERE.parent / "checkers", HERE.parent / "harness"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
import vm, isa, pltcheck, consteval, testcbor, testtlv
from hal import HalStatus
from scenario import CARD_ERROR_CODES

def is_view(t): return isinstance(t, tuple) and t[0] == "arr" and t[2] is None

ENUMS = {n: list(vs) for n, vs in consteval.Prog(pltcheck.PRELUDE).enums.items()}
CATALOG = pltcheck.load_catalog()
OPERATION_SLOTS = 2                                   # BP-16: at least 2 operations at a time

class NativeError(Exception):
    def __init__(self, member): super().__init__(member); self.member = member

class Natives:
    def __init__(self, hal):
        self.hal = hal
        self.ops = {}                                 # the operation table: id -> {purpose, lifetime, ctx}

    # ---- the identifier space (PLT-20, PLT-22)
    def in_use(self, ident):
        return self.hal.key(ident) is not None or ident in self.ops or ident in self.hal.resources

    def key(self, ident, types=None):
        k = self.hal.key(ident)
        if k is None:
            raise NativeError("WrongResourceType" if ident in self.ops or ident in self.hal.resources else "NotFound")
        if types is not None and k.type not in types: raise NativeError("WrongResourceType")
        return k

    # ---- lifetimes (VEX-48)
    def end_command(self, ctx):
        for i in [i for i, o in self.ops.items() if o["lifetime"] == "Command"]: self.drop(i)

    def drop_session(self, ctx):
        for i in list(self.ops): self.drop(i)

    def drop(self, ident):
        self.hal.op_abort(self.ops[ident]["ctx"]); del self.ops[ident]

    # ---- arguments and results (BC-34)
    def call(self, ctx, number):
        path = isa.NATIVE_NAMES[number]; entry = CATALOG[path]
        params, ret = entry["params"], entry["ret"]
        slot = ret != "none" and ret not in ("u32", "bool")
        cells = sum(2 if is_view(pt) else 1 for _, _, pt in params) + (1 if slot else 0)
        raw = [vm.pop(ctx) for _ in range(cells)][::-1]
        args, i, view_bytes = [], 0, 0
        for _, mode, pt in params:
            if is_view(pt):
                args.append((raw[i], raw[i + 1])); view_bytes += raw[i + 1]; i += 2
            else:
                args.append(raw[i]); i += 1
        slot_addr = raw[i] if slot else None
        vm.charge(ctx, 8 + vm.blocks(view_bytes))
        self.ctx = ctx
        try:
            result = getattr(self, "n_" + path[5:].replace(".", "_"))(*args)
            ctx.out_cat, ctx.out_code = 0, 0
        except NativeError as e:
            ctx.out_cat, ctx.out_code = isa.CAT_PLATFORM, CARD_ERROR_CODES[e.member]; result = None
        except HalStatus as s:
            if s.code >= 0x0100: raise                      # TXN-CAPACITY, COMMIT, FATAL: not application errors
            ctx.out_cat, ctx.out_code = isa.CAT_PLATFORM, s.code; result = None
        if ret in ("u32", "bool"): vm.push(ctx, int(result) if result is not None else 0)
        elif slot and result is not None: vm.write(ctx, slot_addr, self.encode_struct(ret, result))

    def encode_struct(self, name, fields):
        out = b""
        for f, ft in self.struct_fields(name):
            v = fields[f]
            if ft in ENUMS: out += bytes([ENUMS[ft].index(v)])
            elif ft == "bool": out += bytes([1 if v else 0])
            else: out += int(v).to_bytes(isa.WIDTH[ft], "little")
        return out

    @staticmethod
    def struct_fields(name):
        return {"CborHead": [("major", "CborMajor"), ("argument", "u32"), ("size", "u32")],
                "TlvHead": [("tag", "u32"), ("class", "TlvClass"), ("constructed", "bool"), ("length", "u32"), ("size", "u32")]}[name]

    def data(self, view): return vm.read(self.ctx, view[0], view[1])

    def out(self, view, data):
        if view[1] < len(data): raise NativeError("Capacity")            # nothing written (BP-6, BP-7)
        vm.write(self.ctx, view[0], bytes(data)); return len(data)

    def enum(self, name, cell): return ENUMS[name][cell]

    def keyspec(self, addr):
        b = vm.read(self.ctx, addr, 2); return self.enum("KeyType", b[0]), self.enum("KeyStorage", b[1])

    # ---- card.key (BP-18 to BP-25)
    def create_key(self, ident, spec, generate, material=None):
        ktype, storage = self.keyspec(spec)
        if self.in_use(ident): raise NativeError("AlreadyExists")
        if generate and ktype == "EcP256Public": raise NativeError("Unsupported")
        if ident == 0: raise NativeError("Malformed")
        if generate: self.hal.key_generate(ident, ktype, storage); return
        data = self.data(material)
        want = {"Aes128": 16, "Aes256": 32, "Hmac256": 32, "EcP256Private": 32, "EcP256Public": 65}[ktype]
        if len(data) != want: raise NativeError("Malformed")
        self.hal.key_import(ident, ktype, storage, data)

    def n_key_generate(self, ident, spec): self.create_key(ident, spec, True)
    def n_key_import(self, ident, spec, material): self.create_key(ident, spec, False, material)

    def n_key_export_public(self, ident, output):
        k = self.key(ident)
        if not k.type.startswith("EcP256"): raise NativeError("WrongResourceType")
        if output[1] < 65: raise NativeError("Capacity")
        return self.out(output, self.hal.key_export_public(ident))

    def n_key_delete(self, ident): self.key(ident); self.hal.key_delete(ident)

    # ---- card.crypto and card.random (BP-26 to BP-33)
    EC = ("EcP256Private", "EcP256Public"); AES = ("Aes128", "Aes256")

    def n_crypto_digest(self, alg, data, out): return self.out(out, self.hal.digest(self.data(data)))

    def n_crypto_mac(self, key, alg, data, out):
        self.key(key, ("Hmac256",)); return self.out(out, self.hal.mac(key, self.data(data)))

    def n_crypto_sign(self, key, alg, message, signature):
        self.key(key, ("EcP256Private",)); return self.out(signature, self.hal.sign(key, self.data(message)))

    def n_crypto_verify(self, key, alg, message, signature):
        self.key(key, self.EC); return self.hal.verify(key, self.data(message), self.data(signature))

    def n_crypto_sign_digest(self, key, alg, digest, signature):
        self.key(key, ("EcP256Private",)); d = self.data(digest)
        if len(d) != 32: raise NativeError("Malformed")
        return self.out(signature, self.hal.sign_digest(key, d))

    def n_crypto_verify_digest(self, key, alg, digest, signature):
        self.key(key, self.EC); d = self.data(digest)
        if len(d) != 32: raise NativeError("Malformed")
        return self.hal.verify_digest(key, d, self.data(signature))

    def n_crypto_agree(self, key, peer, secret):
        self.key(key, ("EcP256Private",)); return self.out(secret, self.hal.agree(key, self.data(peer)))

    def n_crypto_derive(self, alg, secret, salt, info, length, out):
        if not 1 <= length <= 8160: raise NativeError("Malformed")
        return self.out(out, self.hal.derive(self.data(secret), self.data(salt), self.data(info), length))

    def cipher(self, key, iv, data, output, decrypt):
        self.key(key, self.AES); iv, data = self.data(iv), self.data(data)
        if len(iv) != 16 or len(data) % 16: raise NativeError("Malformed")
        return self.out(output, self.hal.cipher(key, iv, data, decrypt))

    def n_crypto_encrypt(self, key, alg, iv, data, output): return self.cipher(key, iv, data, output, False)
    def n_crypto_decrypt(self, key, alg, iv, data, output): return self.cipher(key, iv, data, output, True)

    def begin(self, op, purpose, key, lifetime):
        e = None
        if purpose != "digest":
            try: self.key(key, {"mac": ("Hmac256",), "sign": ("EcP256Private",), "verify": self.EC}[purpose])
            except NativeError as err:
                if err.member == "NotFound": raise
                e = err
        if self.in_use(op): raise NativeError("AlreadyExists")
        if e: raise e
        if op == 0: raise NativeError("Malformed")
        if len(self.ops) >= OPERATION_SLOTS: raise NativeError("Capacity")
        ctx = {}; self.hal.op_begin(ctx, purpose, None if purpose == "digest" else key)
        self.ops[op] = {"purpose": purpose, "lifetime": self.enum("OperationLifetime", lifetime), "ctx": ctx}

    def n_crypto_begin_digest(self, op, alg, lifetime): self.begin(op, "digest", None, lifetime)
    def n_crypto_begin_mac(self, op, key, alg, lifetime): self.begin(op, "mac", key, lifetime)
    def n_crypto_begin_sign(self, op, key, alg, lifetime): self.begin(op, "sign", key, lifetime)
    def n_crypto_begin_verify(self, op, key, alg, lifetime): self.begin(op, "verify", key, lifetime)

    def operation(self, op):
        if op not in self.ops:
            in_use = op in self.hal.resources or self.hal.key(op) is not None
            raise NativeError("WrongResourceType" if in_use else "NotFound")
        return self.ops[op]

    def n_crypto_cancel(self, op): self.operation(op); self.drop(op)
    def n_crypto_update(self, op, data): self.hal.op_update(self.operation(op)["ctx"], self.data(data))

    def n_crypto_finish(self, op, out):
        o = self.operation(op); self.hal._op_key(o["ctx"])
        if o["purpose"] == "verify": raise NativeError("InvalidState")
        result = self.hal.op_finish(o["ctx"])
        if out[1] < len(result): raise NativeError("Capacity")           # the operation continues (BP-31)
        self.drop(op); return self.out(out, result)  # it has ended before the write, which may trap (HAL-26, K3)

    def n_crypto_finish_verify(self, op, signature):
        o = self.operation(op); self.hal._op_key(o["ctx"])
        if o["purpose"] != "verify": raise NativeError("InvalidState")
        r = self.hal.op_finish_verify(o["ctx"], self.data(signature)); self.drop(op); return r

    def n_random_fill(self, out): return self.out(out, self.hal.random(out[1]))

    # ---- card.cbor (BP-34 to BP-40), card.tlv and card.der (BP-41 to BP-46): encodings, not cryptography
    def codec(self, fn):
        try: return fn()
        except testcbor.CborError as e: raise NativeError(e.kind)
        except testtlv.TlvError as e: raise NativeError(e.kind)

    def n_cbor_validate(self, data): return self.codec(lambda: testcbor.validate(list(self.data(data))))
    def n_cbor_skip(self, data): return self.codec(lambda: testcbor.skip(list(self.data(data))))

    def n_cbor_head(self, data):
        major, arg, size = self.codec(lambda: testcbor.head(list(self.data(data))))
        return {"major": major, "argument": arg, "size": size}

    def n_cbor_write_head(self, major, value, out):
        return self.out(out, self.codec(lambda: testcbor.write_head(self.enum("CborMajor", major), value)))

    def n_cbor_write_int(self, value, out):
        v = value - (1 << 32) if value >= 1 << 31 else value
        return self.out(out, self.codec(lambda: testcbor.write_int(v)))

    def n_cbor_write_bool(self, value, out): return self.out(out, [0xF5 if value else 0xF4])

    def n_cbor_write_string(self, major, content, out):
        major = self.enum("CborMajor", major); content = list(self.data(content))
        if major not in ("Bytes", "Text"): raise NativeError("Malformed")
        if major == "Text":
            try: bytes(content).decode("utf-8")
            except UnicodeDecodeError: raise NativeError("Malformed")
        return self.out(out, self.codec(lambda: testcbor.write_head(major, len(content))) + content)

    def n_tlv_head(self, data):
        tag, cls, constructed, length, size = self.codec(lambda: testtlv.head(list(self.data(data))))
        return {"tag": tag, "class": cls, "constructed": constructed, "length": length, "size": size}

    def n_tlv_skip(self, data): return self.codec(lambda: testtlv.skip(list(self.data(data))))
    def n_tlv_validate(self, data): return self.codec(lambda: testtlv.validate(list(self.data(data))))
    def n_der_write_head(self, tag, length, out): return self.out(out, self.codec(lambda: testtlv.write_head(tag, length)))
    def n_der_write_integer(self, magnitude, out):
        return self.out(out, self.codec(lambda: testtlv.write_integer(list(self.data(magnitude)))))
    def n_der_integer_size(self, magnitude): return self.codec(lambda: testtlv.integer_size(list(self.data(magnitude))))

    # ---- the test-only catalog (language/conformance/platform/test-catalog.txt), test builds only (V-33)
    def n_test_resources_create(self, ident, kind):
        res = self.hal.resources
        if ident in res: raise NativeError("AlreadyExists")
        if len(res) >= 4: raise NativeError("Capacity")
        res[ident] = [kind, 0]

    def test_resource(self, ident, kind=None):
        res = self.hal.resources
        if ident not in res: raise NativeError("NotFound")
        if kind is not None and res[ident][0] != kind: raise NativeError("WrongResourceType")
        return res[ident]

    def n_test_resources_delete(self, ident): self.test_resource(ident); del self.hal.resources[ident]
    def n_test_resources_read(self, ident): return self.test_resource(ident, 1)[1]
    def n_test_resources_write(self, ident, value): self.test_resource(ident, 1)[1] = value

    def n_test_sign(self, key, message, signature):
        self.test_resource(key, 2); msg = self.data(message)
        if signature[1] < len(msg): raise NativeError("Capacity")
        return self.out(signature, bytes(b ^ 0x5A for b in msg))
