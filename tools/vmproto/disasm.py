"""Disassembler for images (VM4; named disasm, not dis, so as not to shadow the standard module): prints the header, the function table and annotated listings.

Usage:
    uv run python -I tools/vmproto/disasm.py <image.bin>
    uv run python -I tools/vmproto/disasm.py <program dir or .card file>      (compiles it first)
"""
import sys, pathlib, struct
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import isa

def read_image(img):
    h = dict(zip(["magic", "format", "profile", "binding", "image_size", "persistent_size", "session_size", "stack_need",
                  "max_atomic", "function_count", "entry_command", "entry_install", "entry_session_start", "entry_select",
                  "import_count", "functions_offset", "imports_offset", "const_offset", "const_size", "code_offset",
                  "code_size", "debug_offset", "debug_size"], isa.HEADER.unpack_from(img, 0)))
    funcs = [dict(zip(["code", "frame_size", "argc", "payload", "operand_base"], isa.FUNC.unpack_from(img, h["functions_offset"] + 12 * i)))
             for i in range(h["function_count"])]
    imports = [struct.unpack_from("<H", img, h["imports_offset"] + 2 * i)[0] for i in range(h["import_count"])]
    names = [f"f{i}" for i in range(len(funcs))]
    if h["debug_size"]:
        i = h["debug_offset"]; nfiles = struct.unpack_from("<H", img, i)[0]; i += 2
        for _ in range(nfiles): i += 2 + struct.unpack_from("<H", img, i)[0]
        n = struct.unpack_from("<H", img, i)[0]; i += 2; names = []
        for _ in range(n):
            ln = struct.unpack_from("<H", img, i)[0]; names.append(img[i + 2:i + 2 + ln].decode()); i += 2 + ln
    return h, funcs, imports, names

def operand_text(name, kinds, ops, end):
    out = []
    for k, v in zip(kinds, ops):
        if k == "T": out.append(isa.TYPE_NAMES[v])
        elif k == "R": out.append(isa.REGION_NAMES[v])
        elif k == "C": out.append({1: "app", 2: "platform"}[v])
        elif k == "O": out.append("BE" if v == 0 else "LE")
        elif k in ("r", "s"): out.append(f"-> {end + v:04x}")
        else: out.append(str(v))
    if name == "NATIVE": out.append(f"; {isa.NATIVE_NAMES.get(ops[0], '?')}")
    return " ".join(out)

def listing(img):
    """The annotated listing; with debug information (TL1), each statement's source line and each variable's scope."""
    import debuginfo
    info = debuginfo.DebugInfo.of(img)
    marks = {}
    for off, f, line in info.lines: marks.setdefault(off, []).append(f"; {pathlib.Path(info.files[f]).name}:{line}")
    for v in info.vars:
        if not v["param"]:
            marks.setdefault(v["start"], []).append(f";   {v['name']}: {info.type_name(v['type'])} at frame +{v['offset']} ({v['kind']})")
    h, funcs, imports, names = read_image(img)
    code = img[h["code_offset"]:h["code_offset"] + h["code_size"]]
    lines = [f"image {h['image_size']} bytes, format {h['format']}, profile {h['profile']}, binding {h['binding']}",
             f"PERSISTENT {h['persistent_size']}  SESSION {h['session_size']}  stack need {h['stack_need']}  "
             f"max atomic {h['max_atomic']}  CONST {h['const_size']}  code {h['code_size']}",
             "natives: " + (", ".join(f"{n} {isa.NATIVE_NAMES.get(n, '?')}" for n in imports) or "none")]
    bounds = [f["code"] for f in funcs] + [len(code)]
    for i, f in enumerate(funcs):
        lines.append(f"\n; function {i}: {names[i]}  (frame {f['frame_size']}, argc {f['argc']}, payload {f['payload']}, "
                     f"operands from {f['operand_base']}, code {bounds[i + 1] - f['code']} bytes)")
        for v in info.vars:
            if v["function"] == i and v["param"]:
                lines.append(f";   parameter {v['name']}: {info.type_name(v['type'])} at frame +{v['offset']} ({v['kind']})")
        pc = f["code"]
        while pc < bounds[i + 1]:
            lines.extend(marks.get(pc, []))
            name, ops, size = isa.decode(code, pc)
            kinds = isa.OPS[name][1]
            if kinds == "S": text = "[" + ", ".join(f"{pc + size + r:04x}" for r in ops) + "]"
            else: text = operand_text(name, kinds, ops, pc + size)
            lines.append(f"{pc:04x}  {code[pc:pc + size].hex(' '):<24} {name} {text}".rstrip())
            pc += size
    return "\n".join(lines)

if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1])
    if src.suffix == ".bin":
        img = src.read_bytes()
    else:
        sys.path.insert(0, str(HERE.parent / "checkers")); sys.path.insert(0, str(HERE.parent / "harness"))
        import compiler
        from lexcheck import header
        from scenario import program_files
        files = program_files(src) if src.is_dir() else [src]
        meta = header(files[0].read_bytes())
        img = compiler.compile_files(files, meta.get("binding"), meta.get("kind", "fragment" if "conformance" in str(src) else "application") == "fragment").image
    print(listing(img))
