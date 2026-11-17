"""Write the SP13 (Annex B) conformance tests, which use the test-only platform catalog, and cross-check them with Annex B."""
import re, sys, pathlib
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"
annex = (repo / "spec" / "annex-B-platform-contract.md").read_text(encoding="utf-8")

def fn(body, ret=None, params="", name="check"):
    arrow = f" -> {ret}" if ret else ""
    return f"function {name}({params}){arrow} {{\n" + "".join("    " + l + "\n" for l in body) + "}\n"

T = {}
def add(path, rule, src, expect, note, code): T[path] = (rule, src, expect, note, code)

add("valid/plt-001-platform-call.card", "NAM-18, PLT-25", "D-443", "ok", "A call to a test-catalog API with matching arguments.",
fn(["var value: u32 = attempt card.test.resources.read(1);", "return Ok(value);"], "u32"))
add("valid/plt-002-immediate-api-in-transaction.card", "TXN-17, PLT-24", "D-440, D-443", "ok", "An API marked immediate may be called inside a transaction.",
"persistent total: u32;\n\n" + fn(["transaction {", "    match card.test.resources.read(1) {", "        Ok(value) => {", "            total = value;",
   "        }", "        Err(_) => {", "        }", "    }", "}", "return Ok();"]))
add("invalid/plt-101-unknown-platform-path.card", "NAM-18", "D-406", "compile-error CE-NAM-10", "A card path that is not in the catalog.",
fn(["attempt card.test.missing(1);", "return Ok();"]))
add("invalid/plt-102-wrong-argument-type.card", "PLT-25, EXP-47", "D-443", "compile-error CE-EXP-1", "A bool argument where the catalog says u32.",
fn(["var value: u32 = attempt card.test.resources.read(flag);", "return Ok(value);"], "u32", "flag: bool"))
add("invalid/plt-103-wrong-argument-count.card", "PLT-25, EXP-47", "D-443", "compile-error CE-EXP-16", "A catalog API called with too many arguments.",
fn(["var value: u32 = attempt card.test.resources.read(1, 2);", "return Ok(value);"], "u32"))
add("invalid/plt-104-missing-ref-mode.card", "PLT-25, FUN-7", "D-443", "compile-error CE-FUN-2", "A ref parameter of a catalog API given an argument without ref.",
fn(["var length: u32 = attempt card.test.sign(1, message, inout signature);", "return Ok(length);"], "u32", "message: ref u8[], signature: inout u8[]"))
add("invalid/plt-105-forbidden-in-transaction.card", "TXN-17", "D-440", "compile-error CE-TXN-4", "An API not permitted in transactions, called inside one.",
fn(["transaction {", "    match card.test.resources.create(1, 1) {", "        Ok() => {", "        }", "        Err(_) => {", "        }", "    }", "}", "return Ok();"]))
add("invalid/plt-106-forbidden-through-helper.card", "TXN-17", "D-440", "compile-error CE-TXN-4", "A forbidden API reached through a helper called in a transaction.",
"function provision() {\n    attempt card.test.resources.create(1, 1);\n    return Ok();\n}\n\n"
+ fn(["transaction {", "    match provision() {", "        Ok() => {", "        }", "        Err(_) => {", "        }", "    }", "}", "return Ok();"]))

R = {}
R["run-015-resource-identifiers"] = ("PLT-20, PLT-22, PLT-23", "DN §11.2; PN §2",
"The resource identifier model: create, duplicate, unknown, wrong kind, delete, reuse of an identifier; a trap does not delete a resource.", """errors TestError {
    UnknownOperation = 1;
}

const KIND_COUNTER: u8 = 1;
const KIND_KEY: u8 = 2;

function respond(output: inout u8[], value: u32) -> u32 {
    var bytes: u8[4] = encode_be(value);
    for index: u32 in 0..4 {
        output[index] = bytes[index];
    }
    return Ok(4);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    var id: u32 = convert<u32>(request[1]);
    if operation == 1 {
        attempt card.test.resources.create(id, KIND_COUNTER);
        return Ok(0);
    } else if operation == 2 {
        attempt card.test.resources.create(id, KIND_KEY);
        return Ok(0);
    } else if operation == 3 {
        var value: u32 = attempt card.test.resources.read(id);
        return respond(inout response, value);
    } else if operation == 4 {
        var value: u32 = convert<u32>(request[2]);
        attempt card.test.resources.write(id, value);
        return Ok(0);
    } else if operation == 5 {
        attempt card.test.resources.delete(id);
        return Ok(0);
    } else if operation == 6 {
        var copy: u32 = id;
        var value: u32 = attempt card.test.resources.read(copy);
        return respond(inout response, value);
    } else if operation == 7 {
        attempt card.test.resources.create(id, KIND_COUNTER);
        var missing: u8 = request[200];
        return Ok(0);
    }
    return Err(TestError.UnknownOperation);
}
""", """install
power_on
command 01 01        # create counter 1
expect ok
command 01 01        # never silently replaced
expect err platform AlreadyExists
command 03 02        # unknown identifier
expect err platform NotFound
command 02 02        # create key 2
expect ok
command 03 02        # a key is not a counter
expect err platform WrongResourceType
command 04 01 07     # counter 1 := 7
expect ok
command 06 01        # a copied identifier names the same resource
expect ok 00 00 00 07
command 05 01        # delete counter 1
expect ok
command 03 01
expect err platform NotFound
command 05 01
expect err platform NotFound
command 01 01        # reusing the identifier names a new resource
expect ok
command 03 01
expect ok 00 00 00 00
command 07 03        # create counter 3, then trap
expect trap BOUNDS
command 03 03        # the trap did not delete the resource (PLT-23)
expect ok 00 00 00 00
""")

R["run-016-signer-application"] = ("HEP-15, PLT-20, PLT-22, STA-6", "DN §13",
"Signer application skeleton up to the API boundary: a provisioned key, PIN-guarded signing, and a reset clearing authorization. The signing API is the fictional test-catalog entry.", """errors SignerError {
    MalformedRequest = 1;
    UnsupportedOperation = 2;
    Unauthorized = 3;
    WrongPin = 4;
}

const OP_VERIFY: u8 = 0x20;
const OP_SIGN: u8 = 0x40;
const OP_COUNT: u8 = 0x41;
const SIGNING_KEY: u32 = 1;
const KIND_KEY: u8 = 2;
const PIN: u8[4] = [9, 8, 7, 6];

persistent signatures: u32;
session authenticated: bool;

function on_install() {
    match card.test.resources.create(SIGNING_KEY, KIND_KEY) {
        Ok() => {
        }
        Err(_) => {
        }
    }
    return Ok();
}

function verify(input: ref u8[]) {
    require input.length == 5 else SignerError.MalformedRequest;
    for index: u32 in 0..4 {
        if input[index + 1] != PIN[index] {
            authenticated = false;
            return Err(SignerError.WrongPin);
        }
    }
    authenticated = true;
    return Ok();
}

function encode_count(output: inout u8[]) -> u32 {
    var bytes: u8[4] = encode_be(signatures);
    for index: u32 in 0..4 {
        output[index] = bytes[index];
    }
    return Ok(4);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length >= 1 else SignerError.MalformedRequest;
    var operation: u8 = request[0];
    if operation == OP_VERIFY {
        attempt verify(ref request);
        return Ok(0);
    } else if operation == OP_SIGN {
        require authenticated else SignerError.Unauthorized;
        var length: u32 = attempt card.test.sign(SIGNING_KEY, ref request[1..request.length], inout response);
        signatures = signatures + 1;
        return Ok(length);
    } else if operation == OP_COUNT {
        return encode_count(inout response);
    }
    return Err(SignerError.UnsupportedOperation);
}
""", """install              # on_install provisions the signing key
power_on
command 40 01 02 03
expect err app 3     # signing needs the PIN
command 20 09 08 07 00
expect err app 4
command 20 09 08 07 06
expect ok
command 40 01 02 03  # fictional signature: each byte XOR 0x5A
expect ok 5b 58 59
command 41
expect ok 00 00 00 01
command 40 01 02 03 capacity 2
expect err platform Capacity
command 41           # the failed signature was not counted
expect ok 00 00 00 01
reset
power_on
command 40 01
expect err app 3     # authorization was session state
command 41
expect ok 00 00 00 01
""")

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"
for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
for name, (rule, src, note, program, scenario) in R.items():
    d = conf / "runtime" / name; d.mkdir(parents=True, exist_ok=True)
    (d / "program.card").write_text(hdr(rule, src, "runtime", note, "application") + program, encoding="utf-8", newline="\n")
    (d / "scenario.txt").write_text(scenario, encoding="utf-8", newline="\n")
refs = set(re.findall(r"`((?:valid|invalid)/plt-[\w-]+\.card|runtime/run-[\w-]+/)`", annex))
have = set(T) | {f"runtime/{n}/" for n in R}
assert refs == have, sorted(refs ^ have)
print("tests:", len(have))
