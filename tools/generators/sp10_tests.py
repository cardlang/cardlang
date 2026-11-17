"""Write the SP10 (chapter 11, transactions) conformance tests and cross-check them with the chapter."""
import re, sys, pathlib
repo = pathlib.Path(sys.argv[1]); conf = repo / "conformance"
ch = (repo / "spec" / "11-transactions.md").read_text(encoding="utf-8")

def block(path):
    return re.search(r"\(conformance: `" + re.escape(path) + r"`\)\n\n```text\n(.*?)```", ch, re.S).group(1)
def fn(body, ret=None, params="", name="check"):
    arrow = f" -> {ret}" if ret else ""
    return f"function {name}({params}){arrow} {{\n" + "".join("    " + l + "\n" for l in body) + "}\n"
def txn(inner, after=("return Ok();",)):
    return ["transaction {"] + ["    " + l for l in inner] + ["}"] + list(after)
def match_arms(call, ok=(), err=("abort Err(error);",), err_pat="Err(error)"):
    return [f"match {call} {{", "    Ok() => {"] + ["        " + l for l in ok] + ["    }",
            f"    {err_pat} => {{"] + ["        " + l for l in err] + ["    }", "}"]

T = {}
def add(path, rule, src, expect, note, code): T[path] = (rule, src, expect, note, code)

for path, rule, src, note in [
 ("valid/txn-001-basic.card", "TXN-1, TXN-3", "DN §7.2", "Two persistent writes that commit together."),
 ("valid/txn-002-read-your-writes.card", "TXN-2", "DN §7.2", "A read sees an earlier pending write."),
 ("valid/txn-004-callee-writes.card", "TXN-1, TXN-2", "DN §7.3", "A callee's write takes part in the caller's transaction."),
 ("valid/txn-006-abort-binding.card", "TXN-7, TXN-8", "DN §7.2", "abort with an error binding."),
 ("valid/txn-007-abort-member.card", "TXN-7", "DN §7.2", "abort with an application error member."),
 ("valid/txn-009-validate-then-transact.card", "TXN-6", "DN §10", "Validation before the transaction; return after it."),
 ("valid/txn-010-ends-with-abort.card", "TXN-15", "DN §3.7", "A transaction ending with abort needs no return after it."),
 ("invalid/txn-115-nesting-through-call.card", "TXN-10", "DN §7.3", "A transaction reached through a call from inside another."),
]:
    exp = "compile-error CE-TXN-3" if path.startswith("invalid") else "ok"
    add(path, rule, src, exp, note, block(path))

P = "persistent balance: u32;\n\n"
WALLET = "errors WalletError {\n    InsufficientFunds = 1;\n    Unauthorized = 2;\n}\n\n"
HELPER = "function helper() {\n    balance = 0;\n    return Ok();\n}\n\n"
READ = "function read_amount() -> u32 {\n    return Ok(5);\n}\n\n"
add("valid/txn-003-empty.card", "TXN-3", "DN §7.2", "ok", "An empty transaction.", fn(txn([])))
add("valid/txn-005-err-handled-locally.card", "TXN-9", "DN §7.2", "ok", "A callee error handled locally; the transaction commits.",
"persistent attempts: u32;\n\nfunction perform_update() {\n    attempts = attempts + 1;\n    return Ok();\n}\n\n"
+ fn(txn(match_arms("perform_update()", err=()))))
add("valid/txn-008-loop-inside.card", "TXN-6", "DN §3.6", "ok", "break and continue targeting a loop inside the transaction.",
"persistent counters: u32[8];\n\n" + fn(txn(["for index: u32 in 0..8 {", "    if index == limit {", "        break;", "    }",
   "    if counters[index] == 0 {", "        continue;", "    }", "    counters[index] = 0;", "}"]), None, "limit: u32"))
add("valid/txn-011-helper-with-attempt.card", "TXN-6", "DN §3.6, §6.3", "ok", "A helper using attempt, called from a transaction.",
"persistent total: u32;\n\n" + READ + "function add_amount() {\n    var amount: u32 = attempt read_amount();\n    total = total + amount;\n    return Ok();\n}\n\n"
+ fn(txn(match_arms("add_amount()"))))

I = "invalid/"
add(I+"txn-101-return-inside.card", "TXN-6", "DN §3.6", "compile-error CE-TXN-1", "return inside a transaction.",
P + fn(txn(["balance = 0;", "return Ok();"])))
add(I+"txn-102-forwarding-return-inside.card", "TXN-6", "DN §3.6", "compile-error CE-TXN-1", "A forwarding return inside a transaction.",
P + HELPER + fn(txn(["return helper();"])))
add("valid/txn-012-attempt-inside.card", "TXN-18", "D-445; DN §6.3", "ok", "attempt inside a transaction: its error path aborts the transaction.",
P + READ + fn(txn(["var amount: u32 = attempt read_amount();", "balance = amount;"])))
add("valid/txn-013-require-inside.card", "TXN-18", "D-445; DN §3.6", "ok", "require inside a transaction: a false condition aborts the transaction.",
P + WALLET + fn(txn(["require ready else WalletError.Unauthorized;", "balance = 0;"]), None, "ready: bool"))
add(I+"txn-105-break-to-outer-loop.card", "TXN-6", "DN §3.6", "compile-error CE-TXN-1", "break targeting a loop around the transaction.",
P + fn(["while true {"] + ["    " + l for l in txn(["balance = 0;", "break;"], after=())] + ["}", "return Ok();"]))
add(I+"txn-106-continue-to-outer-loop.card", "TXN-6", "DN §3.6", "compile-error CE-TXN-1", "continue targeting a loop around the transaction.",
P + fn(["for index: u8 in 0..4 {"] + ["    " + l for l in txn(["balance = 0;", "continue;"], after=())] + ["}", "return Ok();"]))
add(I+"txn-107-return-in-match-arm.card", "TXN-6", "DN §3.6", "compile-error CE-TXN-1", "return in a match arm inside a transaction.",
P + HELPER + fn(txn(match_arms("helper()", err=("return Err(error);",)))))
add(I+"txn-108-abort-outside.card", "TXN-7", "DN §7.2", "compile-error CE-TXN-2", "abort in a function with no transaction.",
WALLET + fn(["abort Err(WalletError.InsufficientFunds);"]))
add(I+"txn-109-abort-in-helper.card", "TXN-7", "DN §7.2", "compile-error CE-TXN-2", "abort in a helper called from a transaction.",
P + WALLET + "function helper() {\n    abort Err(WalletError.InsufficientFunds);\n}\n\n" + fn(txn(match_arms("helper()"))))
add(I+"txn-110-abort-card-error.card", "TXN-7, OUT-19", "D-437", "compile-error CE-OUT-3", "abort naming a platform error.",
P + fn(txn(["balance = 0;", "abort Err(CardError.NotFound);"], after=())))
add(I+"txn-111-abort-integer.card", "TXN-7", "DN §7.2", "compile-error CE-OUT-3", "abort with an integer operand.",
P + fn(txn(["balance = 0;", "abort Err(5);"], after=())))
add(I+"txn-112-bare-abort.card", "TXN-7", "DN §7.2", "compile-error CE-SYN-1", "abort without an operand.",
P + fn(txn(["balance = 0;", "abort;"], after=())))
add(I+"txn-113-abort-ok.card", "TXN-7", "DN §7.2", "compile-error CE-SYN-1", "abort with Ok.",
P + fn(txn(["balance = 0;", "abort Ok();"], after=())))
add(I+"txn-114-lexical-nesting.card", "TXN-10", "DN §7.3", "compile-error CE-TXN-3", "A transaction inside a transaction block.",
P + fn(txn(["balance = 1;"] + txn(["balance = 2;"], after=()))))
NEST = "function update() {\n    transaction {\n        balance = 1;\n    }\n    return Ok();\n}\n\n"
add(I+"txn-116-nesting-two-step.card", "TXN-10", "DN §7.3; D-403", "compile-error CE-TXN-3", "Nesting through a chain of two calls.",
P + NEST + "function middle() {\n    attempt update();\n    return Ok();\n}\n\n" + fn(txn(match_arms("middle()", err=()))))
add(I+"txn-117-nesting-untaken-path.card", "TXN-10", "D-403", "compile-error CE-TXN-3", "A nesting call inside if false still counts.",
P + NEST + fn(txn(["if false {"] + ["    " + l for l in match_arms("update()", err=())] + ["}"])))

for path, (rule, src, exp, note, code) in T.items():
    hdr = f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: fragment\n// expect: {exp}\n// note: {note}\n"
    (conf / path).write_text(hdr + code, encoding="utf-8", newline="\n")
refs = set(re.findall(r"`((?:valid|invalid)/txn-[\w-]+\.card)`", ch))
assert refs == set(T), sorted(refs ^ set(T))
print("tests:", len(T))
