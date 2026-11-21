"""The debug section of an image, decoded (IMG-10; TL1 step 4).

    info = DebugInfo.of(image)
    info.position(code_offset)   -> (file, line), the statement that code offset belongs to
    info.offsets(file, line)     -> the code offsets where a statement on that line starts: breakpoints
    info.function_at(code_offset)-> function index
    info.variables(fn, offset)   -> the parameters and locals in scope there
    info.globals, info.types     -> the session, persistent and constant globals; the type table

The section holds, in order:
- the source files;
- the function names;
- the line table: code offset, file and line per statement, sorted;
- the types: integer, bool, enum, struct, array or view;
- the variables: function, name, kind, parameter or not, type, frame offset, and the code range of their scope;
- the globals: name, kind (constant aggregate, persistent, session or constant scalar), type, and offset or value.

A variable's kind says where its value is in the frame:
- `frame`: the value itself;
- `ref`: a cell that holds its address;
- `view`: two cells, the address and the length;
- `error`: a u32 error code.
"""
import struct, bisect

KINDS = ["frame", "ref", "view", "error"]
GLOBAL_KINDS = ["const", "persistent", "session", "const-scalar"]
TYPE_NAMES = ["u8", "u16", "u32", "i8", "i16", "i32"]          # BC-3 type codes

class Reader:
    def __init__(self, data, i): self.d, self.i = data, i
    def u8(self): v = self.d[self.i]; self.i += 1; return v
    def u16(self): v = struct.unpack_from("<H", self.d, self.i)[0]; self.i += 2; return v
    def u32(self): v = struct.unpack_from("<I", self.d, self.i)[0]; self.i += 4; return v
    def str(self): n = self.u16(); s = self.d[self.i:self.i + n].decode("utf-8"); self.i += n; return s

class DebugInfo:
    def __init__(self):
        self.files, self.functions, self.lines, self.types, self.vars, self.globals = [], [], [], [], [], []
        self.function_starts = []

    @classmethod
    def of(cls, image):
        h = struct.unpack_from("<4sHBBIIIII", image, 0)
        import disasm
        hdr, funcs, _, _ = disasm.read_image(image)
        info = cls(); info.function_starts = [f["code"] for f in funcs]
        if not hdr["debug_size"]: return info
        r = Reader(image, hdr["debug_offset"]); end = hdr["debug_offset"] + hdr["debug_size"]
        info.files = [r.str() for _ in range(r.u16())]
        info.functions = [r.str() for _ in range(r.u16())]
        info.lines = [(r.u32(), r.u16(), r.u32()) for _ in range(r.u32())]
        if r.i >= end: return info                               # an image without the TL1 parts
        for _ in range(r.u16()):
            tag = r.u8()
            if tag == 0: info.types.append(("int", TYPE_NAMES[r.u8()]))
            elif tag == 1: info.types.append(("bool",))
            elif tag == 2: name = r.str(); info.types.append(("enum", name, [r.str() for _ in range(r.u16())]))
            elif tag == 3:
                name = r.str(); n = r.u16(); fields = []
                for _ in range(n): fname = r.str(); fields.append((fname, r.u16(), r.u16()))
                info.types.append(("struct", name, fields))
            elif tag == 4: info.types.append(("array", r.u16(), r.u32()))
            elif tag == 5: info.types.append(("view", r.u16()))
            else: raise ValueError(f"unknown debug type tag {tag}")
        for _ in range(r.u32()):
            fn = r.u16(); name = r.str(); kind = KINDS[r.u8()]; param = bool(r.u8())
            t = r.u16(); off = r.u16(); start = r.u32(); stop = r.u32()
            info.vars.append({"function": fn, "name": name, "kind": kind, "param": param, "type": t, "offset": off,
                              "start": start, "end": stop})
        for _ in range(r.u16()):
            name = r.str(); kind = GLOBAL_KINDS[r.u8()]; t = r.u16(); value = r.u32()
            info.globals.append({"name": name, "kind": kind, "type": t, "offset": value})
        return info

    def position(self, offset):
        """(file, line) of the statement that the code offset belongs to, or None."""
        k = bisect.bisect_right([r[0] for r in self.lines], offset) - 1
        if k < 0: return None
        _, f, line = self.lines[k]
        return self.files[f], line

    def offsets(self, file, line):
        """The code offsets where a statement on that line of that file starts."""
        want = {i for i, f in enumerate(self.files) if same_file(f, file)}
        return sorted({off for off, f, l in self.lines if f in want and l == line})

    def function_at(self, offset):
        return max(0, bisect.bisect_right(self.function_starts, offset) - 1)

    def variables(self, fn, offset):
        """Parameters and locals of function fn in scope at the code offset, in declaration order."""
        return [v for v in self.vars if v["function"] == fn and (v["param"] or v["start"] <= offset < v["end"])]

    def type_name(self, t):
        ty = self.types[t]
        if ty[0] == "int": return ty[1]
        if ty[0] == "bool": return "bool"
        if ty[0] in ("enum", "struct"): return ty[1]
        if ty[0] == "array": return f"{self.type_name(ty[1])}[{ty[2]}]"
        return f"{self.type_name(ty[1])}[]"

def same_file(a, b):
    import os
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))
