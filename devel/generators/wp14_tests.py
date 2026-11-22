"""Write the WP14 tests (WP12 step 1, the profile changes for PIV):

- run-031: card.crypto.sign_digest and verify_digest (BP-29), against sign and verify, with their errors.
- run-032: in the ISO 7816 binding, deselection ends the session; a SELECT afterwards starts a new one (BP-55, BP-56).
"""
import sys, pathlib
import sys, pathlib
from cardlang import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance

def hdr(rule, src, note, binding=None):
    b = f"// binding: {binding}\n" if binding else ""
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: application\n{b}// expect: runtime\n// note: {note}\n"

DIGEST = """errors TestError {
    UnknownOperation = 1;
}

const KEY: u32 = 1;
const AES_KEY: u32 = 2;

function on_install() {
    attempt card.key.generate(KEY, KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Persistent });
    attempt card.key.generate(AES_KEY, KeySpec { type: KeyType.Aes128, storage: KeyStorage.Persistent });
    return Ok();
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        var n: u32 = attempt card.crypto.sign_digest(KEY, SignatureAlgorithm.EcdsaP256Sha256, ref request[1..request.length], inout response);
        return Ok(n);
    } else if operation == 2 {
        var valid: bool = attempt card.crypto.verify_digest(KEY, SignatureAlgorithm.EcdsaP256Sha256, ref request[1..33], ref request[33..request.length]);
        response[0] = 0;
        if valid {
            response[0] = 1;
        }
        return Ok(1);
    } else if operation == 3 {
        var digest: u8[32];
        var dn: u32 = attempt card.crypto.digest(DigestAlgorithm.Sha256, ref request[1..request.length], inout digest);
        var signature: u8[64];
        var sn: u32 = attempt card.crypto.sign_digest(KEY, SignatureAlgorithm.EcdsaP256Sha256, ref digest, inout signature);
        var valid: bool = attempt card.crypto.verify(KEY, SignatureAlgorithm.EcdsaP256Sha256, ref request[1..request.length], ref signature);
        response[0] = 0;
        if valid {
            response[0] = 1;
        }
        return Ok(1);
    } else if operation == 4 {
        var signature: u8[64];
        var sn: u32 = attempt card.crypto.sign_digest(KEY, SignatureAlgorithm.EcdsaP256Sha256, ref request[1..33], inout signature);
        var same: bool = attempt card.crypto.verify_digest(KEY, SignatureAlgorithm.EcdsaP256Sha256, ref request[1..33], ref signature);
        var other: bool = attempt card.crypto.verify_digest(KEY, SignatureAlgorithm.EcdsaP256Sha256, ref request[33..65], ref signature);
        response[0] = 0;
        response[1] = 0;
        if same {
            response[0] = 1;
        }
        if other {
            response[1] = 1;
        }
        return Ok(2);
    } else if operation == 5 {
        var signature: u8[64];
        var sn: u32 = attempt card.crypto.sign_digest(9, SignatureAlgorithm.EcdsaP256Sha256, ref request[1..33], inout signature);
        return Ok(0);
    } else if operation == 6 {
        var signature: u8[64];
        var sn: u32 = attempt card.crypto.sign_digest(AES_KEY, SignatureAlgorithm.EcdsaP256Sha256, ref request[1..33], inout signature);
        return Ok(0);
    } else if operation == 7 {
        var signature: u8[63];
        var sn: u32 = attempt card.crypto.sign_digest(KEY, SignatureAlgorithm.EcdsaP256Sha256, ref request[1..33], inout signature);
        return Ok(0);
    }
    return Err(TestError.UnknownOperation);
}
"""

D1 = " ".join(f"{i:02x}" for i in range(32))
D2 = " ".join(f"{i ^ 0xFF:02x}" for i in range(32))
SIG0 = " ".join(["00"] * 64)
DIGEST_SCENARIO = f"""install
session_start
command 03 61 62 63          # sign_digest(SHA-256(m)) is a valid signature of m under verify (BP-29)
expect ok 01
command 04 {D1} {D2}
expect ok 01 00
command 02 {D1} {SIG0}
expect ok 00
command 01 {D1[:-3]}         # a 31-byte digest
expect err platform Malformed
command 05 {D1}              # no key 9
expect err platform NotFound
command 06 {D1}              # an AES key cannot sign
expect err platform WrongResourceType
command 07 {D1}              # the signature view is 63 bytes
expect err platform Capacity
"""

DESELECT = """errors IsoError {
    Refused = 0x6985;
}

persistent sessions: u8;
session counter: u8;

function on_session_start() {
    sessions += 1;
    return Ok();
}

function on_select(response: inout u8[]) -> u32 {
    response[0] = sessions;
    response[1] = counter;
    return Ok(2);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    if request.length < 4 {
        return Err(IsoError.Refused);
    }
    counter += 1;
    response[0] = counter;
    response[1] = sessions;
    return Ok(2);
}
"""

DESELECT_SCENARIO = """install
power_on             # session 1
select
expect ok 01 00
command 00 01 00 00
expect ok 01 01
command 00 01 00 00
expect ok 02 01
select               # a SELECT of the selected application changes nothing (BP-55)
expect ok 01 02
command 00 01 00 00
expect ok 03 01
deselect             # another application is selected: the session ends (BP-56)
select               # a new session, then on_select
expect ok 02 00
command 00 01 00 00
expect ok 01 02
session_end          # power off
power_on             # session 3
select
expect ok 03 00
"""

written = []
for name, rule, src, note, prog, scen, binding in (
    ("run-031-digest-signatures", "PLT-30", "platform/base-profile.md BP-29 (WP12, PIV step 0 Q1)",
     "card.crypto.sign_digest and verify_digest, against sign and verify, with their errors.", DIGEST, DIGEST_SCENARIO, None),
    ("run-032-deselection-ends-session", "STA-4, STA-6", "platform/base-profile.md BP-55, BP-56 (WP12, PIV step 0 Q2)",
     "ISO 7816: deselection ends the session; the next SELECT starts a new one, and a re-SELECT changes nothing.",
     DESELECT, DESELECT_SCENARIO, "iso7816"),
):
    d = conf / "runtime" / name; d.mkdir(parents=True, exist_ok=True)
    (d / "program.card").write_text(hdr(rule, src, note, binding) + prog, encoding="utf-8", newline="\n")
    (d / "scenario.txt").write_text(scen, encoding="utf-8", newline="\n")
    written.append(f"runtime/{name}/")
(pathlib.Path(__file__).parent / "wp14_owned.txt").write_text("\n".join(written) + "\n", encoding="utf-8", newline="\n")
print("tests:", len(written))
