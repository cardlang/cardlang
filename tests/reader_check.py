"""The example applets behind a real smart card reader: vsmartcard's vpcd, through the system's PC/SC service.

This check needs a machine set up for it, so tests/run_checks.py doesn't run it. The CI job "virtual reader" does,
on Linux; on Windows, run it by hand once vpcd is installed (src/cardlang/card/README.md):
- the PC/SC service with vpcd's reader;
- pyscard: uv sync --group reader;
- OpenSC (opensc-tool, piv-tool, pkcs11-tool) for the PIV part, which is skipped, and says so, without it.

It starts `clc card` on the security key (examples/security-key.json) with a state file of its own, and then:
- finds the card in the reader, and reads its ATR through PC/SC;
- FIDO2: python-fido2 finds the card as a PC/SC authenticator, and registers a WebAuthn credential with its client and
  server;
- PIV: OpenSC recognises a PIV card; piv-tool generates a P-256 key in slot 9A with the administration key; a
  certificate for that key is loaded; pkcs11-tool logs in with the PIN (a wrong PIN first) and signs a digest; the
  signature checks against the certificate's key;
- restarts `clc card`, and then authenticates with the FIDO2 credential and signs with the PIV key again, so the state
  file has kept both.

Usage: uv run python -I tests/reader_check.py . [--port 35963] [--reader "Virtual PCD"] [--keep]
"""
import sys, os, re, time, shutil, hashlib, datetime, pathlib, tempfile, subprocess, argparse
from cardlang import layout

ap = argparse.ArgumentParser()
ap.add_argument("root", nargs="?", default=None)
ap.add_argument("--port", type=int, default=35963, help="vpcd's port for the reader to use")
ap.add_argument("--reader", default="Virtual PCD", help="a part of the reader's name")
ap.add_argument("--keep", action="store_true", help="keep the work folder, with clc card's log")
ARGS = ap.parse_args()
ROOT = pathlib.Path(ARGS.root).resolve() if ARGS.root else layout.at().root
L = layout.at(ROOT)

from smartcard.System import readers as pcsc_readers
from smartcard.Exceptions import CardConnectionException, NoCardException

ATR = [0x3B, 0x80, 0x80, 0x01, 0x01]
ADMIN_KEY = "01:02:03:04:05:06:07:08:01:02:03:04:05:06:07:08"     # the example's test default (examples/piv/README.md)
PIN = "123456"

results = []
def check(name, cond, detail=""):
    results.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + ("" if cond else " | " + str(detail)), flush=True)

# ------------------------------------------------------------------ the card process
class CardProcess:
    def __init__(self, work):
        self.work, self.proc, self.runs = work, None, 0
    def start(self):
        self.runs += 1
        self.log = open(self.work / f"clc-card-{self.runs}.log", "w", encoding="utf-8")
        self.proc = subprocess.Popen([sys.executable, "-I", "-m", "cardlang.cli", "card", str(L.examples / "security-key.json"),
                                      "--state", str(self.work / "security-key.state"), "--port", str(ARGS.port), "--trace"],
                                     cwd=ROOT, stdout=self.log, stderr=subprocess.STDOUT)
    def wait_connected(self, timeout=90):
        """Wait until this run of clc card has connected to vpcd: before that, the reader may still show the last run's card."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if "connected to the virtual reader" in (self.work / f"clc-card-{self.runs}.log").read_text(encoding="utf-8"): return True
            if self.proc.poll() is not None: return False
            time.sleep(0.2)
        return False
    def stop(self):
        if self.proc:
            self.proc.terminate()
            try: self.proc.wait(20)
            except subprocess.TimeoutExpired: self.proc.kill(); self.proc.wait()
            self.log.close(); self.proc = None
    def tail(self, n=15):
        return "\n".join((self.work / f"clc-card-{self.runs}.log").read_text(encoding="utf-8").splitlines()[-n:])

def find_card(timeout=90):
    """The PC/SC reader that holds the card, once it's there: (reader, connection)."""
    deadline, seen = time.time() + timeout, set()
    while time.time() < deadline:
        try: names = pcsc_readers()
        except Exception: names = []
        for r in names:
            seen.add(str(r))
            if ARGS.reader.lower() not in str(r).lower(): continue
            conn = r.createConnection()
            try:
                conn.connect(); return r, conn
            except (CardConnectionException, NoCardException):
                pass
        time.sleep(0.5)
    return None, sorted(seen)

# ------------------------------------------------------------------ FIDO2, with python-fido2 over PC/SC
def fido2_device(reader):
    from fido2.pcsc import CtapPcscDevice
    for device in CtapPcscDevice.list_devices(str(reader)):
        return device
    return None

def fido2_server():
    from fido2.server import Fido2Server
    from fido2.webauthn import PublicKeyCredentialRpEntity
    return Fido2Server(PublicKeyCredentialRpEntity(name="Example", id="example.com"))

def fido2_client(device):
    from fido2.client import Fido2Client, DefaultClientDataCollector
    return Fido2Client(device, DefaultClientDataCollector("https://example.com"))

def fido2_register(reader):
    from fido2.webauthn import PublicKeyCredentialUserEntity
    device = fido2_device(reader)
    check("FIDO2: python-fido2 finds the card as a PC/SC authenticator", device is not None)
    if device is None: return None
    server = fido2_server()
    options, state = server.register_begin(PublicKeyCredentialUserEntity(id=os.urandom(16), name="alice", display_name="Alice"),
                                           user_verification="discouraged")
    try:
        auth_data = server.register_complete(state, fido2_client(device).make_credential(options["publicKey"]))
        check("FIDO2: a WebAuthn registration, verified by python-fido2's server", auth_data.is_user_present())
        return auth_data.credential_data
    except Exception as e:
        check("FIDO2: a WebAuthn registration, verified by python-fido2's server", False, repr(e))
    finally:
        device.close()

def fido2_authenticate(reader, credential):
    device = fido2_device(reader)
    if device is None or credential is None:
        check("FIDO2: after a restart, the credential authenticates", False, "no device or no credential"); return
    server = fido2_server()
    options, state = server.authenticate_begin([credential], user_verification="discouraged")
    try:
        server.authenticate_complete(state, [credential], fido2_client(device).get_assertion(options["publicKey"]).get_response(0))
        check("FIDO2: after a restart, the credential authenticates, verified by the server", True)
    except Exception as e:
        check("FIDO2: after a restart, the credential authenticates, verified by the server", False, repr(e))
    finally:
        device.close()

# ------------------------------------------------------------------ PIV, with OpenSC
def run(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, **kw)
    return r.returncode, (r.stdout + r.stderr).strip()

def opensc_reader_index():
    """OpenSC's number for the reader that holds the card."""
    code, out = run(["opensc-tool", "--list-readers"])
    for line in out.splitlines():                   # "Nr.  Card  Features  Name", where Features may be empty
        m = re.match(r"\s*(\d+)\s+(Yes|No)\s+(.*?)\s*$", line)
        if m and m.group(2) == "Yes" and ARGS.reader.lower() in m.group(3).lower(): return m.group(1)
    return None

def piv_setup(work):
    """Generate a key in 9A, load a certificate for it; return the certificate's public key, or None."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    index = opensc_reader_index()
    check("PIV: OpenSC lists the reader with the card", index is not None, run(["opensc-tool", "--list-readers"])[1])
    if index is None: return None
    code, out = run(["opensc-tool", "--reader", index, "--name"])
    check("PIV: OpenSC recognises a PIV card", code == 0 and "PIV" in out, out)
    key_file = work / "admin.key"; key_file.write_text(ADMIN_KEY, encoding="ascii")
    env = dict(os.environ, PIV_EXT_AUTH_KEY=str(key_file))
    public_pem = work / "9a-public.pem"
    code, out = run(["piv-tool", "--reader", index, "--admin", "A:9B:08", "--genkey", "9A:11", "--out", str(public_pem)], env=env)
    check("PIV: piv-tool generates a P-256 key in 9A with the administration key", code == 0 and public_pem.exists(), out)
    if not public_pem.exists(): return None
    public = serialization.load_pem_public_key(public_pem.read_bytes())
    ca = ec.generate_private_key(ec.SECP256R1())
    name = lambda cn: x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name("CardLang virtual card")).issuer_name(name("CardLang test CA"))
            .public_key(public).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1)).not_valid_after(now + datetime.timedelta(days=30))
            .sign(ca, hashes.SHA256()))
    cert_der = work / "9a.der"; cert_der.write_bytes(cert.public_bytes(serialization.Encoding.DER))
    code, out = run(["piv-tool", "--reader", index, "--admin", "A:9B:08", "--cert", "9A", "--in", str(cert_der)], env=env)
    check("PIV: piv-tool loads a certificate for that key", code == 0, out)
    return public

def piv_sign(work, public, label):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, utils
    from cryptography.exceptions import InvalidSignature
    if public is None:
        check(f"PIV: {label}: pkcs11-tool signs with the PIN", False, "no key"); return
    digest = hashlib.sha256(f"CardLang {label}".encode()).digest()
    data, sig = work / "digest.bin", work / "signature.der"
    data.write_bytes(digest); sig.unlink(missing_ok=True)
    code, out = run(["pkcs11-tool", "--login", "--pin", "999999", "--sign", "--id", "01", "--mechanism", "ECDSA",
                     "--input-file", str(data), "--output-file", str(sig), "--signature-format", "openssl"])
    check(f"PIV: {label}: a wrong PIN is refused", code != 0 and not sig.exists(), out[-300:])
    code, out = run(["pkcs11-tool", "--login", "--pin", PIN, "--sign", "--id", "01", "--mechanism", "ECDSA",
                     "--input-file", str(data), "--output-file", str(sig), "--signature-format", "openssl"])
    try:
        public.verify(sig.read_bytes(), digest, ec.ECDSA(utils.Prehashed(hashes.SHA256()))); valid = True
    except (InvalidSignature, OSError, ValueError) as e:
        valid = repr(e)
    check(f"PIV: {label}: pkcs11-tool signs with the PIN, and the signature checks against the certificate's key",
          code == 0 and valid is True, f"{valid} {out[-300:]}")

# ------------------------------------------------------------------ the run
def main():
    work = pathlib.Path(tempfile.mkdtemp(prefix="cardlang-reader-"))
    card = CardProcess(work)
    have_opensc = all(shutil.which(t) for t in ("opensc-tool", "piv-tool", "pkcs11-tool"))
    if not have_opensc: print("(OpenSC is not installed, so the PIV part is skipped)")
    try:
        card.start()
        check("clc card connects to the virtual reader", card.wait_connected(), card.tail())
        reader, conn = find_card()
        check("the card shows up in the reader", reader is not None, f"readers seen: {conn}\n{card.tail()}")
        if reader is None: return False
        check("the ATR, through PC/SC", conn.getATR() == ATR, conn.getATR())
        conn.disconnect()
        credential = fido2_register(reader)
        public = piv_setup(work) if have_opensc else None
        if have_opensc: piv_sign(work, public, "first run")

        card.stop()
        card.start()
        check("after a restart, clc card connects again", card.wait_connected(), card.tail())
        reader, conn = find_card()
        check("after a restart of clc card, the card is back", reader is not None, card.tail())
        if reader is None: return False
        conn.disconnect()
        fido2_authenticate(reader, credential)
        if have_opensc: piv_sign(work, public, "after a restart")
    finally:
        card.stop()
        if not all(results): print(f"--- the end of clc card's log ---\n{card.tail(40)}")
        if ARGS.keep: print(f"work folder: {work}")
        else: shutil.rmtree(work, ignore_errors=True)
    print("ALL PASS" if all(results) else "FAILURES")
    return all(results)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
