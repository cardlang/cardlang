"""The link between a virtual card and vsmartcard's virtual reader, vpcd.

vpcd is a reader driver for pcsc-lite and for the Windows smart card service: the operating system sees an ordinary
smart card reader, and vpcd forwards everything over a TCP socket to a card process, this one. vpcd listens (on
localhost, port 35963 by default) and the card connects to it. Every message, both ways, is a 2-byte big-endian length
and then that many bytes:

- one byte from vpcd is a control code: 00 power off, 01 power on, 02 reset, 04 send the ATR, which the card answers
  with its ATR as a message of its own;
- anything longer is a command APDU, which the card answers with the response APDU.

The link reconnects whenever the connection drops, as it does when the reader service restarts, and waits while
vpcd isn't there.
"""
import socket, threading, time

POWER_OFF, POWER_ON, RESET, GET_ATR = 0x00, 0x01, 0x02, 0x04
DEFAULT_PORT = 35963

class Link:
    """Serve a VirtualCard to vpcd until stop() is called."""

    def __init__(self, card, host="localhost", port=DEFAULT_PORT, log=None, trace=None):
        self.card, self.host, self.port = card, host, port
        self.log = log or (lambda text: None)       # connection events
        self.trace = trace                          # if set, trace(direction, bytes) for every APDU and control
        self.stopping = threading.Event()
        self.connected = threading.Event()

    def stop(self):
        self.stopping.set()

    def serve(self, retry=1.0):
        """Connect, serve, and reconnect, until stopped."""
        waiting = False
        while not self.stopping.is_set():
            try:
                sock = socket.create_connection((self.host, self.port), timeout=2)
            except OSError:
                if not waiting:
                    self.log(f"waiting for the virtual reader (vpcd) at {self.host}:{self.port}")
                    waiting = True
                self.stopping.wait(retry)
                continue
            waiting = False
            self.log(f"connected to the virtual reader at {self.host}:{self.port}")
            self.connected.set()
            try:
                self._session(sock)
            except OSError as e:
                self.log(f"the connection dropped: {e}")
            finally:
                sock.close(); self.connected.clear()
                self.card.power_off()
            if not self.stopping.is_set():
                self.log("disconnected; reconnecting")

    def _session(self, sock):
        sock.settimeout(0.5)                        # so stop() is noticed between messages
        while not self.stopping.is_set():
            message = self._receive(sock)
            if message is None: return              # vpcd closed the connection
            if len(message) == 1:
                self._control(sock, message[0])
            elif message:
                if self.trace: self.trace(">", message)
                response = self.card.transmit(message)
                if self.trace: self.trace("<", response)
                self._send(sock, response)

    def _control(self, sock, code):
        if code == POWER_OFF:
            self.card.power_off()
        elif code in (POWER_ON, RESET):
            self.card.power_on()
        elif code == GET_ATR:
            self._send(sock, self.card.atr)
        if self.trace: self.trace("*", bytes([code]))

    def _receive(self, sock):
        head = self._read(sock, 2)
        if head is None: return None
        return self._read(sock, int.from_bytes(head, "big"), started=True)

    def _read(self, sock, n, started=False):
        """n bytes, or None if the connection closed before a message began."""
        data = b""
        while len(data) < n:
            try:
                chunk = sock.recv(n - len(data))
            except socket.timeout:
                if self.stopping.is_set(): return None
                continue
            if not chunk:
                if data or started: raise OSError("the connection closed in the middle of a message")
                return None
            data += chunk
        return data

    def _send(self, sock, data):
        sock.sendall(len(data).to_bytes(2, "big") + bytes(data))
