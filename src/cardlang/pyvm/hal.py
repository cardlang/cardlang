"""The prototype's test HAL (VM5), following vm/hal.md:
- persistent storage, atomic updates, transactions, recovery and the interrupt hook (HAL-15 to HAL-20);
- the key store, with persistent key changes joining transactions (HAL-21 to HAL-23);
- every cryptographic operation and randomness (HAL-25 to HAL-28), done by the test-only implementations in
  cardlang.platform (testcrypto, p256), with the same deterministic generator as the reference interpreter;
- the test hooks (HAL-31), and the fictional resources of the test-only catalog (card.test.*, V-33).

Statuses are raised as HalStatus(code). A simulated power loss during a commit is raised as PowerLoss, after the HAL
has done its recovery (the transaction is undone: HAL-6, HAL-19). The prototype passes data as byte strings; the
descriptors of HAL-11 and HAL-12 are a concern of the C interface.
"""
import sys, pathlib, hashlib
from cardlang.platform import p256, testcrypto

CL_TXN_CAPACITY, CL_COMMIT_FAILED, CL_FATAL = 0x0100, 0x0101, 0x01FF
NOT_FOUND, WRONG_RESOURCE, INVALID_STATE, CAPACITY, MALFORMED = 0x0010, 0x0012, 0x0013, 0x0014, 0x0021

class HalStatus(Exception):
    def __init__(self, code): super().__init__(hex(code)); self.code = code

class PowerLoss(Exception):
    """The test hook's power loss during a commit; recovery has already rolled the transaction back."""

class Key:
    __slots__ = ("type", "storage", "material")
    def __init__(self, ktype, storage, material): self.type, self.storage, self.material = ktype, storage, material
    def public(self): return p256.mul(self.material) if self.type == "EcP256Private" else self.material

class TestHal:
    ATOMIC_CAPACITY = 4096              # the largest destination one atomic update can hold (HAL-17)
    TXN_CAPACITY = 64 * 1024            # bytes of pending writes a transaction can hold (HAL-19)

    def __init__(self):
        self.partition = None           # committed persistent bytes of the application (HAL-15)
        self.shadow = None              # the active transaction's view of the partition, or None
        self.pending = 0
        self.update = None              # an open atomic update: [offset, length, bytearray]
        self.interrupt = False
        self.pkeys, self.vkeys = {}, {}  # the key store (HAL-21): id -> Key
        self.pkeys_saved = None         # the persistent keys as they were when the transaction began
        self.resources = {}             # the test-only catalog's resources: id -> [kind, value]
        self.test_seed(b"cardlang-test-drbg")

    # ---- partition lifecycle (the platform's loader; not VM calls)
    def create_partition(self, size): self.partition = bytearray(size); self.shadow = None; self.pkeys = {}
    def delete_partition(self): self.partition = None; self.shadow = None; self.pkeys = {}

    # ---- storage (HAL-15 to HAL-20)
    def storage_size(self): return len(self.partition) if self.partition is not None else 0
    def atomic_capacity(self): return self.ATOMIC_CAPACITY

    def _view(self): return self.shadow if self.shadow is not None else self.partition

    def read(self, off, n):
        return bytes(self._view()[off:off + n])        # an open update is invisible (HAL-20)

    def update_begin(self, off, length):
        assert self.update is None, "one atomic update at a time"
        if length > self.ATOMIC_CAPACITY: raise HalStatus(CL_TXN_CAPACITY)
        if self.shadow is not None and self.pending + length > self.TXN_CAPACITY: raise HalStatus(CL_TXN_CAPACITY)
        self.update = [off, length, bytearray(self._view()[off:off + length])]

    def update_write(self, off, data):
        u = self.update; rel = off - u[0]
        assert 0 <= rel and rel + len(data) <= u[1], "write outside the atomic update's range"
        u[2][rel:rel + len(data)] = data

    def update_end(self):
        off, length, data = self.update; self.update = None
        self._view()[off:off + length] = data
        if self.shadow is not None: self.pending += length

    def update_abort(self): self.update = None

    def copy(self, dst, src, n):
        data = self.read(src, n); self.update_begin(dst, n); self.update_write(dst, data); self.update_end()

    def txn_begin(self):
        assert self.shadow is None
        self.shadow = bytearray(self.partition); self.pending = 0
        self.pkeys_saved = dict(self.pkeys)                     # persistent key changes join it (HAL-19, BP-24)

    def txn_commit(self):
        if self.interrupt:                                      # the test hook: power loss during the commit
            self.interrupt = False; self.txn_abort(); raise PowerLoss()
        self.partition[:] = self.shadow; self.shadow = None; self.pkeys_saved = None

    def txn_abort(self):
        self.shadow = None
        if self.pkeys_saved is not None: self.pkeys = self.pkeys_saved; self.pkeys_saved = None

    # ---- test hooks (HAL-31)
    def test_interrupt_next_commit(self): self.interrupt = True
    def test_seed(self, data): self.drbg = (bytes(data), 0)

    # ---- randomness (HAL-28)
    def random(self, n):
        seed, counter = self.drbg; out = b""
        while len(out) < n:
            out += hashlib.sha256(seed + counter.to_bytes(8, "big")).digest(); counter += 1
        self.drbg = (seed, counter)
        return out[:n]

    # ---- keys (HAL-21 to HAL-23). The native library has already checked identifiers, types and lengths.
    def key(self, ident): return self.pkeys.get(ident, self.vkeys.get(ident))

    def key_info(self, ident):
        k = self.key(ident)
        if k is None: raise HalStatus(NOT_FOUND)
        return k.type, k.storage

    def _store(self, ident, key):
        store = self.pkeys if key.storage == "Persistent" else self.vkeys
        if len(store) >= (8 if key.storage == "Persistent" else 4): raise HalStatus(CAPACITY)     # BP-25
        store[ident] = key

    def key_generate(self, ident, ktype, storage):
        if ktype.startswith("Aes") or ktype == "Hmac256": material = tuple(self.random(16 if ktype == "Aes128" else 32))
        else: material = 1 + int.from_bytes(self.random(40), "big") % (p256.N - 1)
        self._store(ident, Key(ktype, storage, material))

    def key_import(self, ident, ktype, storage, data):
        data = list(data)
        if ktype.startswith("Aes") or ktype == "Hmac256": material = tuple(data)
        elif ktype == "EcP256Private":
            material = int.from_bytes(bytes(data), "big")
            if not 1 <= material < p256.N: raise HalStatus(MALFORMED)
        else:
            material = p256.decode_point(data)
            if material is None: raise HalStatus(MALFORMED)
        self._store(ident, Key(ktype, storage, material))

    def key_export_public(self, ident): return bytes(p256.encode_point(self.key(ident).public()))

    def key_delete(self, ident): (self.pkeys if ident in self.pkeys else self.vkeys).pop(ident)

    def keys_drop(self, storage):
        """Volatile: every volatile and command key (session end). Command: the command keys (BP-14)."""
        self.vkeys = {i: k for i, k in self.vkeys.items() if not (storage == "Volatile" or k.storage == storage)}

    # ---- one-shot cryptography (HAL-25)
    def digest(self, data): return hashlib.sha256(bytes(data)).digest()
    def mac(self, ident, data): return bytes(testcrypto.hmac_sha256(self.key(ident).material, list(data)))
    def sign(self, ident, message): return bytes(testcrypto.ecdsa_sign(self.key(ident).material, list(message)))

    def verify(self, ident, message, signature):
        return testcrypto.ecdsa_verify(self.key(ident).public(), list(message), list(signature))

    def sign_digest(self, ident, digest): return bytes(testcrypto.ecdsa_sign_digest(self.key(ident).material, list(digest)))

    def verify_digest(self, ident, digest, signature):
        return testcrypto.ecdsa_verify_digest(self.key(ident).public(), list(digest), list(signature))

    def agree(self, ident, peer):
        q = p256.decode_point(list(peer))
        if q is None: raise HalStatus(MALFORMED)
        return bytes(testcrypto.ecdh(self.key(ident).material, q))

    def derive(self, secret, salt, info, length):
        return bytes(testcrypto.hkdf_sha256(list(secret), list(salt), list(info), length))

    def cipher(self, ident, iv, data, decrypt):
        return bytes(testcrypto.aes_cbc(self.key(ident).material, list(iv), list(data), decrypt=decrypt))

    # ---- multi-part cryptography (HAL-26), on a context the caller provides (a dict standing for its bytes)
    def op_begin(self, ctx, purpose, ident):
        ctx.clear(); ctx.update({"purpose": purpose, "key": None if ident is None else self.key(ident), "data": b""})

    def _op_key(self, ctx):
        k = ctx["key"]
        if k is not None and not any(v is k for v in list(self.pkeys.values()) + list(self.vkeys.values())):
            raise HalStatus(INVALID_STATE)                       # its key was deleted, even if the id is reused
        return k

    def op_update(self, ctx, data): self._op_key(ctx); ctx["data"] += bytes(data)

    def op_finish(self, ctx):
        k = self._op_key(ctx); d = ctx["data"]
        if ctx["purpose"] == "digest": return hashlib.sha256(d).digest()
        if ctx["purpose"] == "mac": return bytes(testcrypto.hmac_sha256(k.material, list(d)))
        return bytes(testcrypto.ecdsa_sign(k.material, list(d)))

    def op_finish_verify(self, ctx, signature):
        k = self._op_key(ctx); return testcrypto.ecdsa_verify(k.public(), list(ctx["data"]), list(signature))

    def op_abort(self, ctx): ctx.clear()
