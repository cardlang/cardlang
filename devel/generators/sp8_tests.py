import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "checkers"))   # find layout
import layout
# Tests written by sp14_tests.py and wp1_tests.py are referenced in this chapter but owned by those generators.
SP14_OWNED = set().union(*(set(f.read_text().split()) for f in pathlib.Path(__file__).parent.glob("*_owned.txt")))
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance
ch = (layout.at(repo).spec / "09-outcomes-and-errors.md").read_text(encoding="utf-8")

def fn(body, ret=None, params="", name="check"):
    arrow = f" -> {ret}" if ret else ""
    return f"function {name}({params}){arrow} {{\n" + "".join("    " + l + "\n" for l in body) + "}\n"
def block(path):
    return re.search(r"\(conformance: `" + re.escape(path) + r"`\)\n\n```text\n(.*?)```", ch, re.S).group(1)

T = {}
def add(path, rule, src, expect, note, code): T[path] = (rule, src, expect, note, code)

for path, rule, src, note in [
 ("valid/out-001-match-ok-err.card", "OUT-11, OUT-12, OUT-13", "DN §6.1", "Handling success and failure locally."),
 ("valid/out-002-no-payload-match.card", "OUT-11, OUT-12", "DN §3.7, §6.3", "Ok() and a specific error arm before the catch-all."),
 ("valid/out-004-attempt-forms.card", "OUT-9, OUT-10", "DN §6.3", "attempt as an initializer and as a statement."),
 ("valid/out-005-forwarding.card", "OUT-5", "DN §6.3; D-413", "Forwarding a call's outcome and a checked intrinsic's outcome."),
 ("valid/out-007-error-set.card", "OUT-15, OUT-16", "DN §6.3", "An error set with literal codes."),
 ("valid/out-008-no-error-set.card", "OUT-8, OUT-15", "D-413", "attempt on checked_convert with no error set."),
 ("valid/out-009-match-card-error.card", "OUT-11, OUT-19", "D-437", "Matching a CardError member and propagating others."),
]:
    add(path, rule, src, "ok", note, block(path))

READ = "function read_value() -> u32 {\n    return Ok(7);\n}\n\n"
AUTH = "function authenticate() {\n    return Ok();\n}\n\n"
WALLET = "errors WalletError {\n    InsufficientFunds = 1;\n    AccountBlocked = 2;\n}\n\n"
def match(scrutinee, arms, after=("return Ok();",)):
    body = [f"match {scrutinee} {{"]
    for pat, inner in arms:
        body += [f"    {pat} => {{"] + ["        " + l for l in inner] + ["    }"]
    return body + ["}"] + list(after)
PROP = ["return Err(error);"]

add("valid/out-003-ignore-payload.card", "OUT-11", "DN §6.3", "ok", "Ok(_) deliberately ignores a payload.",
READ + fn(match("read_value()", [("Ok(_)", []), ("Err(error)", PROP)])))
add("valid/out-006-unused-error-binding.card", "OUT-14", "DN §6.3", "ok", "An error binding that is never used.",
READ + fn(match("read_value()", [("Ok(value)", ["return Ok(value);"]), ("Err(error)", ["return Ok(0);"])], after=()), "u32"))

I = "invalid/"
add(I+"out-101-bare-call-statement.card", "OUT-7", "DN §6.3", "compile-error CE-OUT-1", "A call used as a statement.",
READ + fn(["read_value();", "return Ok();"]))
add(I+"out-102-bare-checked-statement.card", "OUT-7", "DN §6.3", "compile-error CE-OUT-1", "A checked intrinsic used as a statement.",
fn(["checked_add(a, b);", "return Ok();"], None, "a: u32, b: u32"))
add(I+"out-103-ok-value-in-no-payload.card", "OUT-3", "DN §3.6", "compile-error CE-OUT-2", "Ok with a value in a function without a payload.",
fn(["return Ok(1);"]))
add(I+"out-104-ok-empty-in-payload.card", "OUT-3", "DN §3.6", "compile-error CE-OUT-2", "Ok() in a function with a payload.",
fn(["return Ok();"], "u32"))
add(I+"out-105-forward-mismatch.card", "OUT-5", "DN §3.7", "compile-error CE-OUT-2", "Forwarding a u32 outcome from a u16 function.",
READ + fn(["return read_value();"], "u16"))
add(I+"out-106-err-integer.card", "OUT-4", "DN §6.3", "compile-error CE-OUT-3", "An integer as an Err operand.",
fn(["return Err(5);"]))
add(I+"out-107-err-enum-variant.card", "OUT-4", "DN §3.11, §6.3", "compile-error CE-OUT-3", "An enum variant as an Err operand.",
"enum Mode {\n    Off;\n    On;\n}\n\n" + fn(["return Err(Mode.Off);"]))
add(I+"out-108-originate-card-error.card", "OUT-4, OUT-19", "D-437", "compile-error CE-OUT-3", "Application code originates a platform error.",
fn(["return Err(CardError.NotFound);"]))
add(I+"out-109-require-card-error.card", "OUT-19, STM-19", "D-437", "compile-error CE-OUT-3", "A require naming a platform error.",
fn(["require ready else CardError.NotFound;", "return Ok();"], None, "ready: bool"))
add(I+"out-110-attempt-non-call.card", "OUT-8", "DN §6.3", "compile-error CE-OUT-4", "attempt applied to a variable.",
fn(["var copy: u32 = attempt value;", "return Ok();"], None, "value: u32"))
add(I+"out-111-attempt-statement-with-payload.card", "OUT-9", "DN §6.3", "compile-error CE-OUT-4", "The statement form with a call that has a payload.",
READ + fn(["attempt read_value();", "return Ok();"]))
add(I+"out-112-attempt-expression-no-payload.card", "OUT-9", "DN §6.3", "compile-error CE-OUT-4", "The expression form with a call that has no payload.",
AUTH + fn(["var result: u32 = attempt authenticate();", "return Ok();"]))
add(I+"out-113-missing-catch-all.card", "OUT-12", "DN §6.3", "compile-error CE-OUT-5", "No catch-all arm, although every error is listed.",
WALLET + "function debit() {\n    return Err(WalletError.InsufficientFunds);\n}\n\n"
+ fn(match("debit()", [("Ok()", []), ("Err(WalletError.InsufficientFunds)", []), ("Err(WalletError.AccountBlocked)", [])])))
add(I+"out-114-missing-success-arm.card", "OUT-12", "DN §3.6", "compile-error CE-OUT-5", "No success arm.",
READ + fn(match("read_value()", [("Err(_)", [])])))
add(I+"out-115-specific-after-catch-all.card", "OUT-12", "DN §3.6", "compile-error CE-OUT-5", "A specific error arm after the catch-all.",
WALLET + READ + fn(match("read_value()", [("Ok(_)", []), ("Err(_)", []), ("Err(WalletError.InsufficientFunds)", [])])))
add(I+"out-116-duplicate-specific-arm.card", "OUT-12", "DN §3.6", "compile-error CE-OUT-5", "A specific error listed twice.",
WALLET + READ + fn(match("read_value()", [("Ok(_)", []), ("Err(WalletError.InsufficientFunds)", []), ("Err(WalletError.InsufficientFunds)", []), ("Err(_)", [])])))
add(I+"out-117-ok-empty-against-payload.card", "OUT-11", "DN §3.6", "compile-error CE-OUT-5", "Ok() against an outcome with a payload.",
READ + fn(match("read_value()", [("Ok()", []), ("Err(_)", [])])))
add(I+"out-118-nested-pattern.card", "OUT-11", "DN §3.6", "compile-error CE-SYN-1", "A nested pattern Ok(State.Idle).",
"enum State {\n    Idle;\n    Busy;\n}\n\nfunction read_state() -> State {\n    return Ok(State.Idle);\n}\n\n"
+ fn(match("read_state()", [("Ok(State.Idle)", []), ("Ok(_)", []), ("Err(_)", [])])))
add(I+"out-119-two-success-arms.card", "OUT-12", "DN §3.6", "compile-error CE-OUT-5", "Two success arms.",
READ + fn(match("read_value()", [("Ok(value)", []), ("Ok(_)", []), ("Err(_)", [])])))
add(I+"out-120-compare-error-binding.card", "OUT-14", "DN §6.3", "compile-error CE-OUT-6", "An error binding compared with itself.",
READ + fn(match("read_value()", [("Ok(_)", []), ("Err(error)", ["if error == error {", "}"])])))
add(I+"out-121-store-error-binding.card", "OUT-14", "DN §6.3", "compile-error CE-OUT-6", "An error binding stored in a variable.",
READ + fn(match("read_value()", [("Ok(_)", []), ("Err(error)", ["var saved: u32 = error;"])])))
add(I+"out-122-pass-error-binding.card", "OUT-14", "DN §6.3", "compile-error CE-OUT-6", "An error binding passed as an argument.",
READ + "function log_error(code: u16) {\n    return Ok();\n}\n\n" + fn(match("read_value()", [("Ok(_)", []), ("Err(error)", ["attempt log_error(error);"])])))
add(I+"out-123-error-binding-require.card", "OUT-14, STM-19", "DN §6.3", "compile-error CE-STM-7", "An error binding as a require operand.",
READ + fn(match("read_value()", [("Ok(_)", []), ("Err(error)", ["require ready else error;"])]), None, "ready: bool"))
add(I+"out-124-outcome-in-initializer.card", "OUT-2", "DN §6.3", "compile-error CE-EXP-14", "An outcome used as an initializer.",
READ + fn(["var value: u32 = read_value();", "return Ok();"]))
add(I+"out-125-two-error-sets.card", "OUT-15", "DN §6.3", "compile-error CE-OUT-7", "Two error sets.",
"errors First {\n    A = 1;\n}\n\nerrors Second {\n    B = 2;\n}\n")
add(I+"out-126-zero-code.card", "OUT-16", "DN §6.3", "compile-error CE-OUT-7", "A zero error code.",
"errors WalletError {\n    Missing = 0;\n}\n")
add(I+"out-127-duplicate-code.card", "OUT-16", "DN §6.3", "compile-error CE-OUT-7", "Two members with the same code.",
"errors WalletError {\n    First = 1;\n    Second = 1;\n}\n")
add(I+"out-128-computed-code.card", "OUT-16", "D-428", "compile-error CE-OUT-7", "A computed error code.",
"const BASE_CODE: u16 = 10;\n\nerrors WalletError {\n    Derived = BASE_CODE + 1;\n}\n")
add(I+"out-129-empty-error-set.card", "OUT-15", "D-436", "compile-error CE-OUT-7", "An empty error set.",
"errors Empty {\n}\n")
add(I+"out-130-code-out-of-range.card", "OUT-16", "DN §6.3", "compile-error CE-EXP-2", "An error code above the u16 range.",
"errors WalletError {\n    Huge = 70000;\n}\n")

for path, (rule, src, exp, note, code) in T.items():
    hdr = f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: fragment\n// expect: {exp}\n// note: {note}\n"
    (conf / path).write_text(hdr + code, encoding="utf-8", newline="\n")
refs = set(re.findall(r"`((?:valid|invalid)/out-[\w-]+\.card)`", ch)) - SP14_OWNED
assert refs == set(T), sorted(refs ^ set(T))
print("tests:", len(T))
