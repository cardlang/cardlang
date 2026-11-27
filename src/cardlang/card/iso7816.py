"""The virtual card's operating system for the ISO 7816 binding (Base Profile §11.1).

A VirtualCard holds one or more applets, each a backend card (cardlang.harness.backends) built for the ISO 7816
binding, with its AID. It takes command APDUs and returns response APDUs, doing what the profile gives the platform
to do:

- SELECT by AID (`00 A4 04 xx`), with partial AIDs, runs `on_select`, and deselects the applet selected before, which
  ends its session (BP-50, BP-50a, BP-55);
- command chaining (CLA bit 0x10) is reassembled, so `command` runs once on the whole request (BP-48, BP-49);
- a long response goes out in parts, with `61xx` and GET RESPONSE, or at once with extended length (BP-49);
- outcomes become status words (BP-51);
- power on and reset start a session of every applet, and power off ends them (BP-56);
- logical channels other than the basic one, and MANAGE CHANNEL, are refused (BP-55).

The choices the profile leaves to the platform are this card's own: see the package README.
"""
from cardlang.card import apdu
from cardlang.harness.scenario import status_word

SW_OK = 0x9000
SW_WRONG_LENGTH = 0x6700
SW_NO_LAST_CHAINED = 0x6883             # a chain broken off by a command that does not continue it
SW_CHANNEL_NOT_SUPPORTED = 0x6881
SW_CONDITIONS = 0x6985                  # GET RESPONSE with nothing left, or a command with no applet selected
SW_NOT_FOUND = 0x6A82                   # SELECT of an AID no applet has
SW_CLA_NOT_SUPPORTED = 0x6E00
SW_TRAP = 0x6F00

INS_SELECT, INS_GET_RESPONSE, INS_MANAGE_CHANNEL = 0xA4, 0xC0, 0x70

class Applet:
    """An applet on the card: its AID and its backend card."""
    def __init__(self, name, aid, backend):
        self.name, self.aid, self.backend = name, bytes(aid), backend
        self.installed = False

class VirtualCard:
    """A card holding applets, driven by APDUs. Build it, then power it on (which returns the ATR)."""

    def __init__(self, applets, atr=bytes.fromhex("3B80800101"), capacity=4096, max_request=4096):
        if max_request < 1280 or capacity < 1280:
            raise ValueError("the profile asks for requests and responses of at least 1280 bytes (BP-48)")
        aids = [a.aid for a in applets]
        for a in aids:
            if any(b != a and b.startswith(a) for b in aids):
                raise ValueError(f"the AID {a.hex().upper()} is a prefix of another applet's AID")
        self.applets, self.atr = list(applets), bytes(atr)
        self.capacity, self.max_request = capacity, max_request
        self.powered = False
        self.selected = None            # the selected Applet, or None
        self.chain = None               # (header, collected data) of a command chain in progress
        self.pending = b""              # response data still to be fetched with GET RESPONSE
        self.log = None                 # if set, called as log(text) for every event

    # ------------------------------------------------------------------ installation and power
    def install(self):
        """Install every applet that isn't installed yet. Returns [(name, outcome of on_install)]."""
        results = []
        for a in self.applets:
            if not a.installed:
                outcome = a.backend.install()
                a.installed = outcome is not None and outcome[0] == "ok"
                results.append((a.name, outcome))
                self._log(f"install {a.name}: {outcome}")
        return results

    def power_on(self):
        """A cold or warm reset: every installed applet starts a new session (BP-56). Returns the ATR."""
        if self.powered: self.power_off()
        self.powered, self.selected, self.chain, self.pending = True, None, None, b""
        for a in self.applets:
            if a.installed:
                outcome = a.backend.session_start()
                if outcome is not None and outcome[0] != "ok": self._log(f"on_session_start of {a.name}: {outcome}")
        self._log("power on")
        return self.atr

    def power_off(self):
        """Power off: every session ends (BP-56)."""
        if self.powered:
            for a in self.applets:
                if a.installed: a.backend.session_end()
        self.powered, self.selected, self.chain, self.pending = False, None, None, b""
        self._log("power off")

    reset = power_on

    def security_reset(self):
        """A security reset (RTF-9): every applet's session ends, and the card stays off until powered on again."""
        for a in self.applets:
            if a.installed: a.backend.reset()
        self.powered, self.selected, self.chain, self.pending = False, None, None, b""
        self._log("security reset")

    # ------------------------------------------------------------------ APDUs
    def transmit(self, command_apdu):
        """Process one command APDU; return the response APDU."""
        if not self.powered: self.power_on()
        try:
            c = apdu.parse(command_apdu)
        except apdu.ApduError as e:
            self.chain = None
            return self._sw(SW_WRONG_LENGTH, f"malformed APDU: {e}")
        if c.cla == 0xFF: return self._sw(SW_CLA_NOT_SUPPORTED)
        if self._channel(c.cla) != 0 or c.ins == INS_MANAGE_CHANNEL:
            return self._sw(SW_CHANNEL_NOT_SUPPORTED, "only the basic channel")
        if c.ins == INS_GET_RESPONSE and c.cla & ~0x10 == 0x00 and self.chain is None:
            return self._get_response(c)
        self.pending = b""                              # any other command drops what was not fetched
        header = bytes([c.cla & ~0x10, c.ins, c.p1, c.p2])
        if self.chain is not None and self.chain[0] != header:
            self.chain = None
            return self._sw(SW_NO_LAST_CHAINED, "a chain was broken off")
        if c.cla & 0x10:                                # one part of a chain: collect it
            data = (self.chain[1] if self.chain else b"") + c.data
            if len(data) > self.max_request:
                self.chain = None
                return self._sw(SW_WRONG_LENGTH, f"a chained request over {self.max_request} bytes")
            self.chain = (header, data)
            return self._sw(SW_OK)
        data = (self.chain[1] if self.chain else b"") + c.data
        self.chain = None
        if len(data) > self.max_request:
            return self._sw(SW_WRONG_LENGTH, f"a request over {self.max_request} bytes")
        if header[0] == 0x00 and c.ins == INS_SELECT and c.p1 == 0x04:
            return self._select(data, c)
        if self.selected is None:
            return self._sw(SW_CONDITIONS, "no applet is selected")
        outcome = self.selected.backend.command(list(header + data), self.capacity)
        return self._answer(outcome, c.ne)

    def _channel(self, cla):
        """The logical channel a CLA names (ISO 7816-4 §5.4.1); proprietary classes are coded like interindustry ones."""
        return cla & 0x03 if cla & 0x40 == 0 else 4 + (cla & 0x0F)

    def _select(self, aid, c):
        matches = [a for a in self.applets if a.installed and a.aid.startswith(aid) and aid]
        if not matches:
            return self._sw(SW_NOT_FOUND, f"no applet has the AID {aid.hex().upper()}")
        target = matches[0]
        if self.selected is not None and self.selected is not target:
            self.selected.backend.deselect()            # deselection ends its session (BP-55)
            self._log(f"deselect {self.selected.name}")
        self.selected = None
        outcome = target.backend.select()
        self._log(f"select {target.name}: {outcome}")
        if outcome is None or outcome[0] != "ok":
            return self._answer(outcome, c.ne)          # the applet is not selected (BP-50a)
        self.selected = target
        if c.p2 & 0x0C == 0x0C: outcome = ("ok", [])    # P2 asks for no response data
        return self._answer(outcome, c.ne)

    def _answer(self, outcome, ne):
        """The response APDU for an outcome: the data (in parts if longer than Le) and the status word (BP-51)."""
        if outcome is None or outcome[0] != "ok":
            sw = status_word(outcome)
            return self._sw(SW_TRAP if sw is None else sw, f"outcome {outcome}")
        return self._send(bytes(outcome[1]), ne)

    def _send(self, data, ne):
        if not data: return self._sw(SW_OK)
        if ne >= len(data): return apdu.response(data, SW_OK)
        part = data[:ne]
        self.pending = data[ne:]
        return apdu.response(part, 0x6100 | min(len(self.pending), 256) % 256)

    def _get_response(self, c):
        if not self.pending: return self._sw(SW_CONDITIONS, "GET RESPONSE with nothing to send")
        data, self.pending = self.pending, b""
        return self._send(data, c.ne or 256)

    def _sw(self, sw, why=None):
        if why: self._log(f"{sw:04X}: {why}")
        return apdu.response(b"", sw)

    def _log(self, text):
        if self.log: self.log(text)
