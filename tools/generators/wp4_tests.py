"""Write the WP4 conformance tests: Base Profile crypto and randomness (platform/base-profile.md §8).

Expected values are published test vectors (FIPS 180-4, FIPS 197, RFC 5869) or are computed here with
Python's standard library (HMAC with a 32-byte key, the interpreter's deterministic random stream).
"""
import sys, pathlib, hashlib, hmac
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "checkers"))   # find layout
import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

SRC = "platform/base-profile.md BP-26 to BP-33"
T = {
    "valid/plt-006-crypto-apis.card": ("NAM-18, PLT-25", SRC, "ok", "Every card.crypto and card.random API, called with matching arguments.", """function exercise(data: ref u8[], peer: ref u8[], out: inout u8[]) -> bool {
    var length: u32 = attempt card.crypto.digest(DigestAlgorithm.Sha256, ref data, inout out);
    length = attempt card.crypto.mac(1, MacAlgorithm.HmacSha256, ref data, inout out);
    var signature: u8[64] = fill(0);
    length = attempt card.crypto.sign(2, SignatureAlgorithm.EcdsaP256Sha256, ref data, inout signature);
    var valid: bool = attempt card.crypto.verify(2, SignatureAlgorithm.EcdsaP256Sha256, ref data, ref signature);
    length = attempt card.crypto.agree(2, ref peer, inout out);
    length = attempt card.crypto.derive(KdfAlgorithm.HkdfSha256, ref data, ref data, ref data, 32, inout out);
    var iv: u8[16] = fill(0);
    length = attempt card.crypto.encrypt(3, CipherAlgorithm.AesCbcNoPadding, ref iv, ref data, inout out);
    length = attempt card.crypto.decrypt(3, CipherAlgorithm.AesCbcNoPadding, ref iv, ref data, inout out);
    attempt card.crypto.begin_digest(10, DigestAlgorithm.Sha256, OperationLifetime.Command);
    attempt card.crypto.begin_mac(11, 1, MacAlgorithm.HmacSha256, OperationLifetime.Session);
    attempt card.crypto.begin_sign(12, 2, SignatureAlgorithm.EcdsaP256Sha256, OperationLifetime.Command);
    attempt card.crypto.begin_verify(13, 2, SignatureAlgorithm.EcdsaP256Sha256, OperationLifetime.Command);
    attempt card.crypto.update(10, ref data);
    length = attempt card.crypto.finish(10, inout out);
    var verified: bool = attempt card.crypto.finish_verify(13, ref signature);
    attempt card.crypto.cancel(11);
    length = attempt card.random.fill(inout out);
    return Ok(valid and verified);
}
"""),
    "invalid/plt-111-wrong-algorithm-family.card": ("PLT-25, EXP-47", SRC, "compile-error CE-EXP-1", "A MAC algorithm passed where a digest algorithm is required.", """function hash(data: ref u8[], out: inout u8[]) -> u32 {
    var length: u32 = attempt card.crypto.digest(MacAlgorithm.HmacSha256, ref data, inout out);
    return Ok(length);
}
"""),
    "invalid/plt-112-crypto-missing-inout.card": ("PLT-25, FUN-7", SRC, "compile-error CE-FUN-2", "The output of card.crypto.digest is an inout parameter.", """function hash(data: ref u8[], out: inout u8[]) -> u32 {
    var length: u32 = attempt card.crypto.digest(DigestAlgorithm.Sha256, ref data, out);
    return Ok(length);
}
"""),
}

ALG = "SignatureAlgorithm.EcdsaP256Sha256"
PROGRAM = f"""errors AppError {{
    UnknownOperation = 1;
}}

command process(request: ref u8[], response: inout u8[]) -> u32 {{
    var operation: u8 = request[0];
    var length: u32 = 0;
    var iv: u8[16] = fill(0);
    var signature: u8[64] = fill(0);
    if operation == 1 {{
        length = attempt card.crypto.digest(DigestAlgorithm.Sha256, ref request[1..request.length], inout response);
        return Ok(length);
    }} else if operation == 2 {{
        attempt card.key.import(1, KeySpec {{ type: KeyType.Hmac256, storage: KeyStorage.Persistent }}, ref request[1..33]);
        return Ok(0);
    }} else if operation == 3 {{
        length = attempt card.crypto.mac(1, MacAlgorithm.HmacSha256, ref request[1..request.length], inout response);
        return Ok(length);
    }} else if operation == 4 {{
        length = attempt card.crypto.derive(KdfAlgorithm.HkdfSha256, ref request[1..23], ref request[23..36], ref request[36..46], 42, inout response);
        return Ok(length);
    }} else if operation == 5 {{
        attempt card.key.import(2, KeySpec {{ type: KeyType.Aes256, storage: KeyStorage.Persistent }}, ref request[1..33]);
        return Ok(0);
    }} else if operation == 6 {{
        length = attempt card.crypto.encrypt(2, CipherAlgorithm.AesCbcNoPadding, ref iv, ref request[1..17], inout response);
        return Ok(length);
    }} else if operation == 7 {{
        length = attempt card.crypto.decrypt(2, CipherAlgorithm.AesCbcNoPadding, ref iv, ref request[1..17], inout response);
        return Ok(length);
    }} else if operation == 8 {{
        var id: u32 = convert<u32>(request[1]);
        attempt card.key.generate(id, KeySpec {{ type: KeyType.EcP256Private, storage: KeyStorage.Persistent }});
        return Ok(0);
    }} else if operation == 9 {{
        var message: u8[16] = fill(0);
        message[0..16] = request[1..17];
        length = attempt card.crypto.sign(3, {ALG}, ref message, inout signature);
        var good: bool = attempt card.crypto.verify(3, {ALG}, ref message, ref signature);
        message[0] = message[0] ^ 1;
        var bad: bool = attempt card.crypto.verify(3, {ALG}, ref message, ref signature);
        response[0] = 0;
        response[1] = 0;
        if good {{
            response[0] = 1;
        }}
        if bad {{
            response[1] = 1;
        }}
        return Ok(2);
    }} else if operation == 10 {{
        attempt card.crypto.begin_sign(10, 3, {ALG}, OperationLifetime.Command);
        attempt card.crypto.update(10, ref request[1..9]);
        attempt card.crypto.update(10, ref request[9..17]);
        length = attempt card.crypto.finish(10, inout signature);
        var valid: bool = attempt card.crypto.verify(3, {ALG}, ref request[1..17], ref signature);
        response[0] = 0;
        if valid {{
            response[0] = 1;
        }}
        return Ok(1);
    }} else if operation == 11 {{
        var point: u8[65] = fill(0);
        var first: u8[32] = fill(0);
        var second: u8[32] = fill(0);
        length = attempt card.key.export_public(4, inout point);
        length = attempt card.crypto.agree(3, ref point, inout first);
        length = attempt card.key.export_public(3, inout point);
        length = attempt card.crypto.agree(4, ref point, inout second);
        response[0] = 0;
        if equal(ref first, ref second) {{
            response[0] = 1;
        }}
        return Ok(1);
    }} else if operation == 12 {{
        attempt card.crypto.begin_digest(20, DigestAlgorithm.Sha256, OperationLifetime.Session);
        attempt card.crypto.update(20, ref request[1..request.length]);
        return Ok(0);
    }} else if operation == 13 {{
        length = attempt card.crypto.finish(20, inout response);
        return Ok(length);
    }} else if operation == 14 {{
        attempt card.crypto.begin_digest(21, DigestAlgorithm.Sha256, OperationLifetime.Command);
        return Ok(0);
    }} else if operation == 15 {{
        attempt card.crypto.update(21, ref request[1..request.length]);
        return Ok(0);
    }} else if operation == 16 {{
        attempt card.crypto.begin_mac(22, 1, MacAlgorithm.HmacSha256, OperationLifetime.Command);
        var verified: bool = attempt card.crypto.finish_verify(22, ref signature);
        return Ok(0);
    }} else if operation == 17 {{
        length = attempt card.crypto.encrypt(2, CipherAlgorithm.AesCbcNoPadding, ref request[1..9], ref request[1..17], inout response);
        return Ok(length);
    }} else if operation == 18 {{
        var secret: u8[32] = fill(0);
        length = attempt card.crypto.agree(3, ref request[1..66], inout secret);
        return Ok(length);
    }} else if operation == 19 {{
        var small: u8[16] = fill(0);
        length = attempt card.crypto.digest(DigestAlgorithm.Sha256, ref request[1..request.length], inout small);
        return Ok(length);
    }} else if operation == 20 {{
        length = attempt card.random.fill(inout response[0..8]);
        return Ok(length);
    }}
    return Err(AppError.UnknownOperation);
}}
"""

h = bytes.fromhex
sp = lambda b: " ".join(f"{x:02x}" for x in b)
ABC = b"abc"
SHA_ABC = h("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")          # FIPS 180-4
assert hashlib.sha256(ABC).digest() == SHA_ABC
HKEY = bytes(range(32))
MAC_ABC = hmac.new(HKEY, ABC, hashlib.sha256).digest()
IKM, SALT, INFO = b"\x0b" * 22, h("000102030405060708090a0b0c"), h("f0f1f2f3f4f5f6f7f8f9")            # RFC 5869 A.1
OKM = h("3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865")
AKEY, PT = bytes(range(32)), h("00112233445566778899aabbccddeeff")                                    # FIPS 197 C.3
CT = h("8ea2b7ca516745bfeafc49904b496089")
MSG = bytes(range(0x40, 0x50))
BADPT = h("04" + "11" * 64)
RANDOM = hashlib.sha256(b"\x00" + (0).to_bytes(8, "big")).digest()[:8]

SCENARIO = f"""install
power_on
command 01 {sp(ABC)}          # SHA-256("abc"), FIPS 180-4
expect ok {sp(SHA_ABC)}
command 02 {sp(HKEY)}
expect ok
command 03 {sp(ABC)}          # HMAC-SHA-256 under an imported Hmac256 key
expect ok {sp(MAC_ABC)}
command 04 {sp(IKM + SALT + INFO)}   # HKDF, RFC 5869 A.1
expect ok {sp(OKM)}
command 05 {sp(AKEY)}
expect ok
command 06 {sp(PT)}           # one CBC block with a zero IV is the FIPS 197 C.3 vector
expect ok {sp(CT)}
command 07 {sp(CT)}
expect ok {sp(PT)}
command 08 03
expect ok
command 08 04
expect ok
command 09 {sp(MSG)}          # sign, verify, and verify a tampered message
expect ok 01 00
command 0a {sp(MSG)}          # a multi-part signature verifies with the one-shot API
expect ok 01
command 0b                    # ECDH: both sides compute the same secret
expect ok 01
command 0c {sp(ABC)}          # a Session operation survives into the next command
expect ok
command 0d
expect ok {sp(SHA_ABC)}
command 0e                    # a Command operation ends with its command
expect ok
command 0f {sp(ABC)}
expect err platform NotFound
command 10                    # the wrong finish for the operation's purpose
expect err platform InvalidState
command 11 {sp(PT)}           # an 8-byte IV
expect err platform Malformed
command 12 {sp(BADPT)}        # a peer point not on the curve
expect err platform Malformed
command 13 {sp(ABC)}          # a 32-byte digest does not fit 16 bytes
expect err platform Capacity
command 0c {sp(ABC)}
expect ok
reset
power_on
command 0d                    # a Session operation ends at reset
expect err platform NotFound
seed 00
command 14                    # the interpreter's deterministic stream after seed 00
expect ok {sp(RANDOM)}
"""

for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
d = conf / "runtime" / "run-020-crypto"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("PLT-24, PLT-25", SRC, "runtime",
    "Base Profile crypto: published vectors through CardLang, sign and verify, multi-part operations and lifetimes, ECDH, errors, random.",
    "application") + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "wp4_owned.txt").write_text("\n".join(sorted(T) + ["runtime/run-020-crypto/"]) + "\n", encoding="utf-8", newline="\n")
print("tests:", len(T) + 1)
