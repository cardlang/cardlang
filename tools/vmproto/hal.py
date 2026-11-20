"""The prototype's test HAL (VM5), following vm/hal.md. Stage 2: persistent storage, atomic updates, transactions,
recovery and the interrupt hook (HAL-15 to HAL-20, HAL-31). Keys and cryptography arrive in stage 3.

Statuses are raised as HalStatus(code); a simulated power loss during a commit is raised as PowerLoss, after the
HAL has performed its recovery (the transaction is undone: HAL-6, HAL-19).
"""

CL_TXN_CAPACITY, CL_COMMIT_FAILED, CL_FATAL = 0x0100, 0x0101, 0x01FF

class HalStatus(Exception):
    def __init__(self, code): super().__init__(hex(code)); self.code = code

class PowerLoss(Exception):
    """The test hook's power loss during a commit; recovery has already rolled the transaction back."""

class TestHal:
    ATOMIC_CAPACITY = 4096              # the largest destination one atomic update can hold (HAL-17)
    TXN_CAPACITY = 64 * 1024            # bytes of pending writes a transaction can hold (HAL-19)

    def __init__(self):
        self.partition = None           # committed persistent bytes of the application (HAL-15)
        self.shadow = None              # the active transaction's view of the partition, or None
        self.pending = 0
        self.update = None              # an open atomic update: [offset, length, bytearray]
        self.interrupt = False

    # ---- partition lifecycle (the platform's loader; not VM calls)
    def create_partition(self, size): self.partition = bytearray(size); self.shadow = None
    def delete_partition(self): self.partition = None; self.shadow = None

    # ---- HAL-15 to HAL-20
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
        assert self.shadow is None; self.shadow = bytearray(self.partition); self.pending = 0

    def txn_commit(self):
        if self.interrupt:                              # the test hook: power loss during the commit (HAL-31)
            self.interrupt = False; self.shadow = None; raise PowerLoss()
        self.partition[:] = self.shadow; self.shadow = None

    def txn_abort(self): self.shadow = None

    # ---- test hooks (HAL-31)
    def test_interrupt_next_commit(self): self.interrupt = True
    def test_seed(self, data): self.seed = bytes(data)

    # ---- resources: stage 3
    def keys_drop(self, storage): pass
