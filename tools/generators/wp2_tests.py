"""Write the WP2 conformance tests: the Base Profile's platform-supplied types (platform/base-types.card)."""
import sys, pathlib
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "checkers"))   # find layout
import layout
repo = pathlib.Path(sys.argv[1]); conf = layout.at(repo).conformance

def hdr(rule, src, exp, note, kind="fragment"):
    return f"// rule: {rule}\n// source: {src}\n// status: agreed\n// kind: {kind}\n// expect: {exp}\n// note: {note}\n"

T = {
    "valid/plt-003-base-types.card": ("NAM-14, PLT-21", "D-446; platform/base-profile.md BP-11", "ok",
        "The Base Profile types are predeclared and usable like ordinary enums and structures.",
        """session spec: KeySpec;

function choose() -> KeySpec {
    var chosen: KeySpec = KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Persistent };
    var lifetime: OperationLifetime = OperationLifetime.Command;
    return Ok(chosen);
}
"""),
    "invalid/plt-107-redeclare-base-type.card": ("NAM-14", "platform/base-profile.md BP-11", "compile-error CE-NAM-5",
        "An application may not declare a name that the Base Profile predeclares.",
        """struct KeySpec {
    size: u16;
}
"""),
}
for path, (rule, src, exp, note, code) in T.items():
    (conf / path).write_text(hdr(rule, src, exp, note) + code, encoding="utf-8", newline="\n")
(pathlib.Path(__file__).parent / "wp2_owned.txt").write_text("\n".join(sorted(T)) + "\n", encoding="utf-8", newline="\n")
print("tests:", len(T))
