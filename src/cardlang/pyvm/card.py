"""The `pyvm` backend of the harness (V-10): compile a program, load it into the Python VM over the test HAL, and
offer the scenario steps of src/cardlang/harness/README.md. This module plays the platform: it owns the buffers, the main
loop's calls into the VM (VEX-45) and the lifecycle state the platform reports.
"""
import sys, pathlib
from cardlang.pyvm import vm
from cardlang.compiler import compiler
from cardlang.bytecode import isa
from cardlang.pyvm.hal import TestHal
from cardlang.pyvm.natives import Natives
from cardlang.platform.errors import CARD_ERROR_CODES

CARD_ERROR_NAMES = {v: k for k, v in CARD_ERROR_CODES.items()}
STACK, RESPONSE, REQUEST = vm.STACK, vm.RESPONSE, vm.REQUEST

class VmCard:
    def __init__(self, files, binding=None, fragment=False, budget=1_000_000):
        self.compiled = compiler.compile_files(files, binding, fragment)
        self.image = self.compiled.image
        h = isa.HEADER.unpack_from(self.image, 0)
        self.persistent_size, self.session_size, self.stack_need = h[5], h[6], h[7]
        self.entries = {"command": h[10], "on_install": h[11], "on_session_start": h[12], "on_select": h[13]}
        self.hal = TestHal()
        self.config = {"session": bytearray(self.session_size), "stack": bytearray(self.stack_need),
                       "budget": budget, "binding": isa.BINDINGS[binding], "test_natives": True}
        self.ctx = vm.Ctx(); vm.load(self.ctx, self.image, self.config, self.hal)
        self.natives = Natives(self.hal)

    # ---- results as the harness reports them
    def outcome(self, r, response=None):
        self.trap_pc = self.ctx.pc if r[0] == "trap" else None        # where it trapped (trap positions)
        if r[0] == "ok":
            if response is None: return ("ok", [])
            return ("ok", list(response[:r[1]]))
        if r[0] == "err":
            return ("err", "app", r[2]) if r[1] == isa.CAT_APP else ("err", "platform", CARD_ERROR_NAMES[r[2]])
        return r

    def trap_position(self):
        """(file, line) of the statement where the last outcome trapped, from the debug section, or None."""
        if getattr(self, "trap_pc", None) is None: return None
        from cardlang.bytecode import debuginfo
        if not hasattr(self, "_debug"): self._debug = debuginfo.DebugInfo.of(self.image)
        return self._debug.position(self.trap_pc)

    def handler(self, name):
        i = self.entries[name]
        if i == isa.NONE_ENTRY: return ("ok", None)
        r = vm.entry(self.ctx, i, [], self.natives); self.check_stack(); return r

    def check_stack(self):
        assert len(self.config["stack"]) == self.stack_need, "the stack grew beyond the compiler's stack need"

    # ---- scenario steps
    def install(self):
        self.hal.create_partition(self.persistent_size); self.ctx.state = vm.NO_SESSION
        r = self.handler("on_install")
        if r[0] != "ok": self.hal.delete_partition(); self.ctx.state = vm.NOT_INSTALLED     # BP-55
        return self.outcome(r)

    def end_session(self):
        self.config["session"][:] = bytes(self.session_size)
        self.hal.keys_drop("Volatile"); self.natives.drop_session(self.ctx)

    def session_start(self):
        assert self.ctx.state != vm.NOT_INSTALLED, "session start before install"
        self.end_session(); self.ctx.state = vm.IN_SESSION
        r = self.handler("on_session_start")
        if r[0] != "ok": self.ctx.state = vm.UNAVAILABLE                                   # BP-55
        return self.outcome(r)

    def session_end(self):
        self.end_session(); self.ctx.state = vm.NO_SESSION

    def reset(self):
        self.session_end()

    def seed(self, data): self.hal.test_seed(data)
    def interrupt_next_commit(self): self.hal.test_interrupt_next_commit()

    def deselect(self):
        """ISO 7816: another application is selected; this one's session ends (BP-55, BP-56)."""
        self.session_end(); self.deselected = True

    def select(self):
        if getattr(self, "deselected", False):                      # the first SELECT after a deselection (BP-56)
            self.deselected = False
            out = self.session_start()
            if out[0] != "ok": return out
        if self.entries["on_select"] == isa.NONE_ENTRY: return ("ok", [])
        resp = bytearray(256); self.ctx.response, self.ctx.response_cap = resp, 256
        r = vm.entry(self.ctx, self.entries["on_select"], [RESPONSE << 29, 256], self.natives); self.check_stack()
        self.ctx.response = None
        return self.outcome(r, resp)

    def command(self, request, capacity):
        if self.ctx.state in (vm.NOT_INSTALLED, vm.NO_SESSION): raise RuntimeError("command before install/session_start")
        if self.ctx.state == vm.UNAVAILABLE: return ("trap", None)                         # BP-55
        req, resp = bytes(request), bytearray(capacity)
        self.ctx.request, self.ctx.request_len, self.ctx.response, self.ctx.response_cap = req, len(req), resp, capacity
        r = vm.entry(self.ctx, self.entries["command"], [REQUEST << 29, len(req), RESPONSE << 29, capacity], self.natives)
        self.natives.end_command(self.ctx); self.hal.keys_drop("Command")                 # VEX-48, BP-14
        self.check_stack(); self.ctx.request = self.ctx.response = None
        if r[0] == "ok" and r[1] > capacity: return ("trap", "RESPONSE-COUNT")             # HEP-9, BC-29
        return self.outcome(r, resp)
