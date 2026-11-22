"""JSON-RPC over standard input and output, with Content-Length framing.

The framing that both the Language Server Protocol and the Debug Adapter Protocol use: a header block of
`Name: value` lines ended by an empty line, then a UTF-8 JSON body of Content-Length bytes. No dependencies.
"""
import sys, json, threading, queue

BOM = bytes([0xEF, 0xBB, 0xBF])

class Channel:
    def __init__(self, inp=None, out=None):
        self.inp = inp or sys.stdin.buffer
        self.out = out or sys.stdout.buffer
        self.lock = threading.Lock()

    def read(self):
        """The next message as a dict, or None at the end of the input."""
        length = None
        while True:
            line = self.inp.readline()
            if not line: return None
            line = line.strip()
            if line.startswith(BOM): line = line[3:]            # a byte-order mark some shells add
            if not line:
                if length is not None: break
                continue
            name, _, value = line.decode("latin-1").partition(":")
            if name.strip().lower() == "content-length": length = int(value.strip())
        body = self.inp.read(length)
        return json.loads(body.decode("utf-8"))

    def write(self, message):
        body = json.dumps(message, separators=(",", ":")).encode("utf-8")
        with self.lock:
            self.out.write(b"Content-Length: %d\r\n\r\n" % len(body) + body); self.out.flush()

def reader_thread(channel):
    """Read messages on a thread, into a queue; None marks the end of the input."""
    q = queue.Queue()
    def run():
        while True:
            try: m = channel.read()
            except Exception as e:                          # broken input: end the session, rather than hang
                print(f"jsonrpc: unreadable input ({e}); ending", file=sys.stderr); m = None
            q.put(m)
            if m is None: return
    threading.Thread(target=run, daemon=True).start()
    return q
