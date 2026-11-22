"""Write the WP3 conformance tests: Base Profile keys (platform/base-profile.md §7, card.key)."""
import sys, pathlib
import sys, pathlib
from cardlang import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

SRC = "platform/base-profile.md BP-18 to BP-25"
T = {
    "valid/plt-004-key-apis.card": ("NAM-18, PLT-25", SRC, "ok", "Every card.key API, called with matching arguments.", """function provision(material: ref u8[], output: inout u8[]) -> u32 {
    var spec: KeySpec = KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Persistent };
    attempt card.key.import(1, spec, ref material);
    attempt card.key.generate(2, KeySpec { type: KeyType.Aes256, storage: KeyStorage.Volatile });
    var length: u32 = attempt card.key.export_public(1, inout output);
    attempt card.key.delete(2);
    return Ok(length);
}
"""),
    "valid/plt-005-key-in-transaction.card": ("TXN-17, PLT-24", SRC, "ok", "Persistent key changes participate in transactions, so they are permitted inside one.", """function rotate() {
    transaction {
        attempt card.key.delete(1);
        attempt card.key.generate(1, KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Persistent });
    }
    return Ok();
}
"""),
    "invalid/plt-108-key-import-missing-ref.card": ("PLT-25, FUN-7", SRC, "compile-error CE-FUN-2", "The material of card.key.import is a ref parameter.", """function provision(material: ref u8[]) {
    attempt card.key.import(1, KeySpec { type: KeyType.Aes128, storage: KeyStorage.Volatile }, material);
    return Ok();
}
"""),
    "invalid/plt-109-key-spec-wrong-type.card": ("PLT-25, EXP-47", SRC, "compile-error CE-EXP-1", "A KeySpec parameter given an integer.", """function provision() {
    attempt card.key.generate(1, 5);
    return Ok();
}
"""),
    "invalid/plt-110-redeclare-key-type.card": ("NAM-14", SRC, "compile-error CE-NAM-5", "KeyType is predeclared by the Base Profile.", """enum KeyType {
    Small;
}
"""),
}

D = "c9afa9d845ba75166b5c215767b1d6934e50c3db36e89b127b8a622b120f6721"                       # RFC 6979 A.2.5
Q = ("04" "60fed4ba255a9d31c961eb74c6356d68c049b8923b61fa6ce669622e60f29fb6"
     "7903fe1008b8bc99a41ae9e95628bc64f2f1b20c2d7e9f5177a3c294d4462299")
BAD = Q[:-2] + "98"                                                                          # not on the curve
sp = lambda h: " ".join(h[i:i + 2] for i in range(0, len(h), 2))

PROGRAM = """errors AppError {
    UnknownOperation = 1;
    Refused = 2;
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    var id: u32 = convert<u32>(request[1]);
    if operation == 1 {
        attempt card.key.import(id, KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Persistent }, ref request[2..34]);
        return Ok(0);
    } else if operation == 2 {
        var length: u32 = attempt card.key.export_public(id, inout response);
        return Ok(length);
    } else if operation == 3 {
        attempt card.key.generate(id, KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Persistent });
        return Ok(0);
    } else if operation == 4 {
        var point: u8[65] = fill(0);
        var length: u32 = attempt card.key.export_public(id, inout point);
        var other: u32 = convert<u32>(request[2]);
        attempt card.key.import(other, KeySpec { type: KeyType.EcP256Public, storage: KeyStorage.Volatile }, ref point);
        return Ok(0);
    } else if operation == 5 {
        attempt card.key.generate(id, KeySpec { type: KeyType.Aes128, storage: KeyStorage.Volatile });
        return Ok(0);
    } else if operation == 6 {
        attempt card.key.delete(id);
        return Ok(0);
    } else if operation == 7 {
        attempt card.key.import(id, KeySpec { type: KeyType.EcP256Public, storage: KeyStorage.Volatile }, ref request[2..67]);
        return Ok(0);
    } else if operation == 8 {
        transaction {
            attempt card.key.generate(id, KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Persistent });
            abort Err(AppError.Refused);
        }
    } else if operation == 9 {
        transaction {
            attempt card.key.delete(id);
            var missing: u8 = request[200];
        }
        return Ok(0);
    } else if operation == 10 {
        var small: u8[10] = fill(0);
        var length: u32 = attempt card.key.export_public(id, inout small);
        return Ok(length);
    } else if operation == 11 {
        attempt card.key.generate(id, KeySpec { type: KeyType.EcP256Public, storage: KeyStorage.Volatile });
        return Ok(0);
    }
    return Err(AppError.UnknownOperation);
}
"""

SCENARIO = f"""install
power_on
command 01 01 {sp(D)}
expect ok
command 02 01        # the public point of the RFC 6979 A.2.5 key
expect ok {sp(Q)}
command 01 01 {sp(D)}
expect err platform AlreadyExists
command 03 02        # generate a key pair
expect ok
command 04 02 03     # its public point imports as a valid EcP256Public key
expect ok
command 05 04        # a volatile AES key
expect ok
command 02 04        # an AES key has no public part
expect err platform WrongResourceType
command 02 09
expect err platform NotFound
command 02 00        # identifier 0 never names a key
expect err platform NotFound
command 05 00        # creating with identifier 0
expect err platform Malformed
command 07 05 {sp(BAD)}
expect err platform Malformed
command 0b 06        # a public key cannot be generated
expect err platform Unsupported
command 0a 01        # output view too short
expect err platform Capacity
command 08 06        # generate inside a transaction, then abort
expect err app 2
command 02 06        # rolled back
expect err platform NotFound
command 09 01        # delete inside a transaction, then trap
expect trap BOUNDS
command 02 01        # the deletion was rolled back
expect ok {sp(Q)}
reset
power_on
command 02 04        # the volatile key is gone
expect err platform NotFound
command 02 01        # the persistent key survives
expect ok {sp(Q)}
command 06 01
expect ok
command 02 01
expect err platform NotFound
"""

for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
d = conf / "runtime" / "run-019-keys"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("PLT-22, PLT-24, TXN-11", SRC, "runtime",
    "Base Profile keys: a published P-256 vector, generation checked by re-import, every error, rollback by abort and by trap, volatile keys at reset.",
    "application") + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "wp3_owned.txt").write_text("\n".join(sorted(T) + ["runtime/run-019-keys/"]) + "\n", encoding="utf-8", newline="\n")
print("tests:", len(T) + 1)
