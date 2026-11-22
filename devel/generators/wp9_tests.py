"""Write the WP9 conformance tests: byte strings, error-set patterns, attempt-else, ignore, compound assignment."""
import sys, pathlib
import sys, pathlib
from cardlang import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance
SPEC = "\n".join(f.read_text(encoding="utf-8") for f in sorted((layout.at(repo).spec).glob("*.md")))

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

def fn(body, ret=None, params="", name="check"):
    arrow = f" -> {ret}" if ret else ""
    return f"function {name}({params}){arrow} {{\n" + "".join("    " + l + "\n" for l in body) + "}\n"

ERRORS = "errors AppError {\n    Alpha = 1;\n    Beta = 2;\n}\n\n"
GET = "function get() -> u32 {\n    return Err(AppError.Beta);\n}\n\n"
T = {
    "valid/lex-010-byte-string-escapes.card": ("LEX-25", "D-453", "ok", "Byte strings with every escape.",
        'const QUOTE: u8[4] = b"a\\"\\\\\\x00";\nconst EMPTY_TAIL: u8[2] = b"\\xFF ";\n'),
    "invalid/lex-117-unterminated-byte-string.card": ("LEX-25", "D-453", "compile-error CE-LEX-5", "A byte string without its closing quote.",
        'const A: u8[2] = b"ab;\n'),
    "invalid/lex-118-byte-string-bad-escape.card": ("LEX-25", "D-453", "compile-error CE-LEX-5", "An escape other than \\\", \\\\ or \\xHH.",
        'const A: u8[1] = b"\\q";\n'),
    "valid/exp-020-byte-strings.card": ("EXP-55", "D-453", "ok", "Byte strings as constants and initializers, and compared with equal.",
        'const KEY_ID: u8[2] = b"id";\n\n' + fn(['var version: u8[8] = b"FIDO_2_0";', "var other: u8[2] = b\"id\";",
                                                  "return Ok(equal(ref KEY_ID, ref other));"], "bool")),
    "invalid/exp-148-byte-string-length.card": ("EXP-55", "D-453", "compile-error CE-EXP-11", "A 2-byte string for a u8[3].",
        fn(['var short: u8[3] = b"ab";', "return Ok();"])),
    "valid/stm-014-ignore.card": ("STM-24", "D-456", "ok", "ignore with and without a payload.",
        ERRORS + GET + "function act() {\n    return Err(AppError.Alpha);\n}\n\n" + fn(["ignore get();", "ignore act();", "return Ok();"])),
    "invalid/stm-130-ignore-non-call.card": ("STM-24", "D-456", "compile-error CE-OUT-4", "ignore of something that is not a call.",
        fn(["var count: u32 = 0;", "ignore count;", "return Ok();"])),
    "valid/stm-015-compound-assignment.card": ("STM-25", "D-457", "ok", "All ten compound operators.",
        "persistent total: u32;\n\n" + fn(["var x: u8 = 1;", "x += 2;", "x -= 1;", "x *= 3;", "x /= 2;", "x %= 2;", "x &= 0x0F;",
                                           "x |= 0x10;", "x ^= 0x01;", "x <<= 1;", "x >>= 2;", "total += 1;", "return Ok();"])),
    "invalid/stm-129-compound-on-constant.card": ("STM-25", "D-457", "compile-error CE-STM-2", "A compound assignment to a constant.",
        "const LIMIT: u8 = 4;\n\n" + fn(["LIMIT += 1;", "return Ok();"])),
    "invalid/stm-131-compound-type.card": ("STM-25", "D-457", "compile-error CE-EXP-1", "The operand of += must have the place's type.",
        fn(["var small: u8 = 1;", "var wide: u16 = 2;", "small += wide;", "return Ok();"])),
    "invalid/stm-132-split-compound.card": ("STM-25, LEX-22", "D-457", "compile-error CE-SYN-1", "+ = with a space is two tokens, not a compound operator.",
        fn(["var x: u8 = 1;", "x + = 1;", "return Ok();"])),
    "valid/out-010-error-codes-and-mapping.card": ("OUT-21, OUT-22", "D-454, D-455", "ok", "An Err(Set(code)) arm, and attempt-else in both forms.",
        ERRORS + GET + "function act() {\n    return Err(AppError.Alpha);\n}\n\n" + fn(["match get() {", "    Ok(value) => {", "        return Ok(value);", "    }",
                           "    Err(AppError(code)) => {", "        var low: u8 = truncate<u8>(code);", "    }",
                           "    Err(error) => {", "        return Err(error);", "    }", "}",
                           "var value: u32 = attempt get() else AppError.Alpha;",
                           "attempt act() else AppError.Beta;", "return Ok(value);"], "u32")),
    "invalid/out-132-card-error-set-pattern.card": ("OUT-21", "D-454", "compile-error CE-OUT-5", "Err(CardError(code)) is not allowed.",
        ERRORS + GET + fn(["match get() {", "    Ok(value) => {", "        return Ok();", "    }",
                           "    Err(CardError(code)) => {", "        return Ok();", "    }",
                           "    Err(error) => {", "        return Err(error);", "    }", "}"])),
    "invalid/out-133-attempt-else-card-error.card": ("OUT-22", "D-455", "compile-error CE-OUT-3", "The replacement error must be an application error member.",
        ERRORS + GET + fn(["var value: u32 = attempt get() else CardError.NotFound;", "return Ok();"])),
}

PROGRAM = """errors AppError {
    Alpha = 0x9101;
    Beta = 0x9102;
    Gamma = 0x9103;
}

persistent total: u32;
session calls: u8;
session values: u8[4];

function fail_beta() -> u32 {
    return Err(AppError.Beta);
}

function next() -> u32 {
    calls += 1;
    return Ok(2);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    var operation: u8 = request[0];
    if operation == 1 {
        match fail_beta() {
            Ok(value) => {
                return Ok(0);
            }
            Err(AppError(code)) => {
                response[0..2] = encode_be(code);
                return Ok(2);
            }
            Err(error) => {
                return Err(error);
            }
        }
    } else if operation == 2 {
        var length: u32 = attempt card.key.export_public(99, inout response) else AppError.Gamma;
        return Ok(length);
    } else if operation == 3 {
        transaction {
            total += 5;
            attempt card.key.delete(99) else AppError.Gamma;
        }
        return Ok(0);
    } else if operation == 4 {
        ignore card.key.delete(99);
        ignore fail_beta();
        response[0..2] = b"ok";
        return Ok(2);
    } else if operation == 5 {
        response[0..4] = encode_be(total);
        return Ok(4);
    } else if operation == 6 {
        var small: u8 = request[1];
        small += request[2];
        response[0] = small;
        return Ok(1);
    } else if operation == 7 {
        values[attempt next()] += 1;
        response[0] = calls;
        response[1] = values[2];
        return Ok(2);
    } else if operation == 8 {
        transaction {
            total += 5;
        }
        return Ok(0);
    }
    return Err(AppError.Alpha);
}
"""
SCENARIO = f"""install
power_on
command 01           # Err(AppError(code)) binds the member's code (OUT-21)
expect ok 91 02
command 02           # attempt ... else replaces a platform error (OUT-22)
expect err app {0x9103}
command 03           # inside a transaction, attempt ... else aborts with the replacement
expect err app {0x9103}
command 05           # total += 5 was rolled back
expect ok 00 00 00 00
command 08
expect ok
command 05
expect ok 00 00 00 05
command 04           # ignore discards an Err, with and without a payload (STM-24)
expect ok 6f 6b
command 06 01 02     # compound assignment
expect ok 03
command 06 c8 64     # 200 + 100 overflows u8: checked as usual (STM-25)
expect trap OVERFLOW
command 07           # values[attempt next()] += 1 calls next once
expect ok 01 01
command 07
expect ok 02 02
"""

for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
d = conf / "runtime" / "run-024-ergonomics"; d.mkdir(parents=True, exist_ok=True)
(d / "program.card").write_text(hdr("OUT-21, OUT-22, STM-24, STM-25, EXP-55, TXN-18", "D-453, D-454, D-455, D-456, D-457", "runtime",
    "Error codes through Err(Set(code)), attempt-else in and out of a transaction, ignore, compound assignment and its single evaluation.",
    "application") + PROGRAM, encoding="utf-8", newline="\n")
(d / "scenario.txt").write_text(SCENARIO, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "wp9_owned.txt").write_text("\n".join(sorted(T) + ["runtime/run-024-ergonomics/"]) + "\n", encoding="utf-8", newline="\n")
missing = [p for p in T if not p.startswith(("valid/lex", "invalid/lex", "invalid/stm-131", "invalid/stm-132")) and "`" + p + "`" not in SPEC]
assert not missing, ("not referenced in the specification", missing)
print("tests:", len(T) + 1)
