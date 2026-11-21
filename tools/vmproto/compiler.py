"""The prototype CardLang compiler (VM4): a checked program to a version-0 image (vm/bytecode.md, vm/image-format.md).

Stages: accept (pltcheck) -> parse and type (typer.py) -> lay out -> generate -> emit. Constants are folded; nothing
else is optimised (V-32). Usage:
    python -I tools/vmproto/compiler.py <program dir or .card file> [-o image.bin] [--report]
"""
import sys, pathlib, struct
HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
for sub in ("checkers", "harness", "vmproto"):
    if str(TOOLS / sub) not in sys.path: sys.path.insert(0, str(TOOLS / sub))
import isa, typer, pltcheck
from isa import TYPES, WIDTH, REGIONS, CAT_APP, CAT_PLATFORM
from scenario import CARD_ERROR_CODES

INTS = set(TYPES)
ARITH = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "REM"}
BITW = {"&": "AND", "|": "OR", "^": "XOR"}
ORDER = {"<": "LT", "<=": "LE", ">": "GT", ">=": "GE"}
CHECKED = {"checked_add": "CADD", "checked_sub": "CSUB", "checked_mul": "CMUL", "checked_div": "CDIV",
           "checked_rem": "CREM", "checked_neg": "CNEG"}
WRAPPING = {"wrapping_add": "WADD", "wrapping_sub": "WSUB", "wrapping_mul": "WMUL"}
TERMINATORS = {"RET", "RETV", "ERR", "FWD", "ERRRAISE", "JMP"}

class CompileError(Exception):
    """Something the version-0 compiler cannot express (not a language error: the program was accepted)."""

# ------------------------------------------------------------------ types and layout (VEX-4)
class Layout:
    def __init__(self, chk):
        self.chk = chk
        self.enum_order = {n: list(vs) for n, vs in chk.cp.enums.items()}
        self.struct_fields = {n: list(fs.items()) for n, fs in chk.structs.items()}

    def is_enum(self, t): return isinstance(t, str) and t in self.enum_order
    def is_struct(self, t): return isinstance(t, str) and t in self.struct_fields
    def is_scalar(self, t): return t in INTS or t == "bool" or self.is_enum(t)
    def is_view(self, t): return isinstance(t, tuple) and t[0] == "arr" and t[2] is None

    def size(self, t):
        if t in INTS: return WIDTH[t]
        if t == "bool": return 1
        if self.is_enum(t): return 1 if len(self.enum_order[t]) <= 256 else 2
        if self.is_struct(t): return sum(self.size(ft) for _, ft in self.struct_fields[t])
        if isinstance(t, tuple) and t[0] == "arr" and t[2] is not None: return t[2] * self.size(t[1])
        raise CompileError(f"no size for {t!r}")

    def tcode(self, t):
        """The BC-3 type code of a scalar type."""
        if t in INTS: return TYPES[t]
        if t == "bool": return TYPES["u8"]
        if self.is_enum(t): return TYPES["u8"] if self.size(t) == 1 else TYPES["u16"]
        raise CompileError(f"not a scalar: {t!r}")

    def field(self, s, f):
        off = 0
        for name, ft in self.struct_fields[s]:
            if name == f: return off, ft
            off += self.size(ft)
        raise CompileError(f"no field {f} in {s}")

    def ordinal(self, enum, variant): return self.enum_order[enum].index(variant)

    def encode_value(self, v, t):
        """Bytes of a constant value in the layout of VEX-4."""
        if t in INTS: return (v & ((1 << (8 * WIDTH[t])) - 1)).to_bytes(WIDTH[t], "little")
        if t == "bool": return bytes([1 if v else 0])
        if self.is_enum(t):
            o = self.ordinal(t, v.split(".")[1] if isinstance(v, str) else v)
            return o.to_bytes(self.size(t), "little")
        if self.is_struct(t): return b"".join(self.encode_value(v[f], ft) for f, ft in self.struct_fields[t])
        if isinstance(t, tuple) and t[0] == "arr": return b"".join(self.encode_value(x, t[1]) for x in v)
        raise CompileError(f"cannot encode {t!r}")

def cell(v):
    return v & 0xFFFFFFFF

def push_op(v):
    c = cell(v)
    return ("PUSH.B", [c]) if c < 0x100 else ("PUSH.H", [c]) if c < 0x10000 else ("PUSH.W", [c])

# ------------------------------------------------------------------ one function
class FuncGen:
    def __init__(self, comp, name):
        self.c = comp; self.L = comp.layout; self.name = name
        self.typed = comp.typed; self.T = comp.typed.types
        params, ret, _ = comp.typed.funcs[name]
        self.ret = ret
        self.code = []                      # ("op", name, operands) or ("label", L)
        self.depth = 0; self.max_depth = 0; self.label_depth = {}; self.nlabels = 0
        self.tramp = {}                     # (depth, txn, else) -> label
        self.callees = set()
        # parameters (BC-24)
        self.scopes = [{}]; off = 8; self.prologue = []
        for pn, mode, pt in params:
            if self.L.is_view(pt):
                self.scopes[0][pn] = ("view", off, pt); off += 8
            elif mode in ("ref", "inout"):
                self.scopes[0][pn] = ("ref", off, pt); off += 4
            elif self.L.is_scalar(pt):
                self.scopes[0][pn] = ("frame", off, pt); off += 4
            else:
                self.prologue.append((pn, off, pt)); off += 4          # by-value aggregate: copied on entry
        self.slot_param = None
        if self.ret != "none" and not self.L.is_scalar(self.ret):
            self.slot_param = off; off += 4                            # hidden payload slot (BC-27)
        self.argc = (off - 8) // 4
        self.cur = self.high = off              # the allocation point and its high-water mark (V-34)

    # ---- emission
    def label(self):
        self.nlabels += 1; return f"L{self.nlabels}"

    def place_label(self, lab):
        if self.depth is None: self.depth = self.label_depth.get(lab)     # reachable again only if jumped to
        elif lab in self.label_depth: assert self.label_depth[lab] == self.depth, (self.name, lab)
        if self.depth is not None: self.label_depth.setdefault(lab, self.depth)
        self.code.append(("label", lab))

    def emit(self, op, *operands, pops=0, pushes=0):
        if self.depth is None: return                  # unreachable: emit nothing (V-35)
        effect = STACK.get(op)
        if effect is not None: pops, pushes = effect
        self.depth -= pops
        assert self.depth >= 0, (self.name, op, self.code[-5:])
        if op in ("JZ", "JNZ", "JMP", "JERR", "JERRIS", "JERRCAT"):
            lab = operands[-1]; self.label_depth.setdefault(lab, self.depth)
        if op == "SWITCH":
            for lab in operands[0]: self.label_depth.setdefault(lab, self.depth)
        self.depth += pushes; self.max_depth = max(self.max_depth, self.depth)
        self.code.append(("op", op, list(operands[0]) if op == "SWITCH" else list(operands)))
        if op in TERMINATORS: self.depth = None

    def push(self, v):
        op, ops = push_op(v); self.emit(op, *ops)

    def alloc(self, size):
        off = self.cur; self.cur += size; self.high = max(self.high, self.cur); return off

    # ---- names
    def lookup(self, name):
        for s in reversed(self.scopes):
            if name in s: return s[name]
        c = self.c
        if name in c.persistent: return ("persistent",) + c.persistent[name]
        if name in c.session: return ("session",) + c.session[name]
        if name in c.const_agg: return ("const",) + c.const_agg[name]
        raise CompileError(f"unknown name {name}")

    def const_scalar(self, e):
        """The folded value of a constant scalar expression, or None (V-32: leaves only)."""
        k = e[0]
        if k == "int": return e[1]
        if k == "bool": return 1 if e[1] else 0
        if k == "un" and e[1] == "-" and e[2][0] == "int": return -e[2][1]
        if k == "name" and e[1] in self.c.const_scalar and not any(e[1] in s for s in self.scopes):
            return self.c.const_scalar[e[1]]
        if k == "field" and e[1][0] == "name" and self.L.is_enum(e[1][1]) and not any(e[1][1] in s for s in self.scopes):
            return self.L.ordinal(e[1][1], e[2])
        return None

    def type_of(self, e): return self.T[id(e)]

    # ---- places: ('static', region, offset, type) with no code, or ('dyn', type) with the address pushed
    def place(self, e):
        k = e[0]
        if k == "name":
            b = self.lookup(e[1])
            if b[0] == "frame": return ("static", "F", b[1], b[2])
            if b[0] == "persistent": return ("static", "P", b[1], b[2])
            if b[0] == "session": return ("static", "S", b[1], b[2])
            if b[0] == "const": return ("static", "C", b[1], b[2])
            if b[0] == "ref": self.emit("LDF", TYPES["u32"], b[1]); return ("dyn", b[2])
            raise CompileError(f"{e[1]} is not a place ({b[0]})")
        if k == "field":
            base = self.place(e[1]); s = base[-1]
            off, ft = self.L.field(s, e[2])
            if base[0] == "static": return ("static", base[1], base[2] + off, ft)
            if off: self.emit("FIELD", off)
            return ("dyn", ft)
        if k == "index":
            at = self.type_of(e[1]); et = at[1]; esz = self.L.size(et)
            if at[2] is None or e[1][0] == "slice":
                self.view(e[1]); self.value(e[2]); self.emit("INDEXV", esz); return ("dyn", et)
            c = self.const_scalar(e[2])
            base = self.place(e[1])
            if c is not None and 0 <= c < at[2]:
                if base[0] == "static": return ("static", base[1], base[2] + c * esz, et)
                if c: self.emit("FIELD", c * esz)
                return ("dyn", et)
            self.to_address(base); self.value(e[2]); self.emit("INDEX", esz, at[2]); return ("dyn", et)
        # an rvalue aggregate: materialise it
        t = self.type_of(e); off = self.materialise(e, t)
        return ("static", "F", off, t)

    def to_address(self, p):
        if p[0] == "static":
            self.emit("ADDR", {"F": REGIONS["STACK"], "P": REGIONS["PERSISTENT"], "S": REGIONS["SESSION"],
                               "C": REGIONS["CONST"]}[p[1]], p[2])

    def address(self, e):
        p = self.place(e); self.to_address(p); return p[-1]

    def load(self, p):
        t = p[-1]; tc = self.L.tcode(t)
        if p[0] == "dyn": self.emit("LDI", tc); return
        self.emit({"F": "LDF", "S": "LDS", "P": "LDP", "C": "LDC"}[p[1]], tc, p[2])

    def store_static(self, p):
        self.emit({"F": "STF", "S": "STS", "P": "STP"}[p[1]], self.L.tcode(p[-1]), p[2])

    # ---- views: (address, length) pushed
    def view(self, e):
        k = e[0]
        if k == "slice":
            self.view(e[1]); self.value(e[2]); self.value(e[3])
            self.emit("SLICE", self.L.size(self.type_of(e)[1])); return
        if k == "name":
            b = self.lookup(e[1])
            if b[0] == "view":
                self.emit("LDF", TYPES["u32"], b[1]); self.emit("LDF", TYPES["u32"], b[1] + 4); return
        t = self.type_of(e)
        self.address(e); self.emit("VIEW", t[2])

    # ---- scalar values
    def value(self, e):
        c = self.const_scalar(e)
        if c is not None: self.push(c); return
        k = e[0]
        if k == "field" and e[2] == "length":
            rt = self.type_of(e[1])
            if isinstance(rt, tuple) and rt[0] == "arr":
                if rt[2] is not None and e[1][0] != "slice": self.push(rt[2]); return
                if e[1][0] == "name" and self.lookup_kind(e[1][1]) == "view":
                    self.emit("LDF", TYPES["u32"], self.lookup(e[1][1])[1] + 4); return     # the length cell
                self.view(e[1]); self.emit("SWAP"); self.emit("DROP"); return
        if k in ("name", "field", "index"):
            self.load(self.place(e)); return
        if k == "un":
            t = self.type_of(e); self.value(e[2])
            self.emit({"-": "NEG", "~": "INV"}[e[1]], self.L.tcode(t)) if e[1] != "not" else self.emit("BNOT"); return
        if k == "bin": self.binary(e); return
        if k == "attempt":
            kind = self.call(e[1]); self.on_error(e[2] if len(e) > 2 else None)
            if kind[0] != "scalar": raise CompileError("attempt of a non-scalar used as a value")
            return
        if k == "call": self.intrinsic_value(e); return
        raise CompileError(f"value of {k}")

    def binary(self, e):
        op, l, r = e[1], e[2], e[3]
        if op in ("and", "or"):
            done, short = self.label(), self.label()
            self.value(l); self.emit("JZ" if op == "and" else "JNZ", short)
            self.value(r); self.emit("JMP", done)
            self.place_label(short); self.push(0 if op == "and" else 1); self.place_label(done); return
        ot = self.type_of(l)
        self.value(l); self.value(r)
        if op in ARITH: self.emit(ARITH[op], self.L.tcode(ot))
        elif op in BITW: self.emit(BITW[op])
        elif op == "<<": self.emit("SHL", self.L.tcode(ot))
        elif op == ">>": self.emit("SHR", self.L.tcode(ot))
        elif op == "==": self.emit("EQ")
        elif op == "!=": self.emit("NE")
        elif op in ORDER: self.emit(ORDER[op], self.L.tcode(ot))
        else: raise CompileError(op)

    def intrinsic_value(self, e):
        name = e[1][1] if e[1][0] == "name" else None; args = e[3]; t = self.type_of(e)
        if name in WRAPPING:
            self.value(args[0][1]); self.value(args[1][1]); self.emit(WRAPPING[name], self.L.tcode(t)); return
        if name == "convert": self.value(args[0][1]); return
        if name == "truncate": self.value(args[0][1]); self.emit("TRUNC", self.L.tcode(t)); return
        if name in ("decode_be", "decode_le"):
            self.view(args[0][1]); self.emit("DECODE", self.L.tcode(t), 0 if name.endswith("be") else 1); return
        if name in ("equal", "compare"):
            et = self.type_of(args[0][1])[1]
            self.view(args[0][1]); self.view(args[1][1])
            if name == "equal": self.emit("EQUAL", self.L.size(et))
            else: self.emit("COMPARE", self.L.tcode(et))
            return
        raise CompileError(f"value of call {name}")

    # ---- aggregates: build an rvalue into a fresh frame temporary; returns its frame offset
    @staticmethod
    def is_rvalue(e):
        """An aggregate expression that is built rather than read from a place."""
        return e[0] in ("list", "ctor", "attempt") or (
            e[0] == "call" and e[1][0] == "name" and e[1][1] in ("fill", "encode_be", "encode_le"))

    def materialise(self, e, t):
        """Build an rvalue aggregate into a fresh frame temporary; returns its frame offset."""
        tmp = self.alloc(self.L.size(t)); self.build(e, t, ("F", tmp)); return tmp

    # A destination is ("F", frame offset), or ("S", offset) inside the caller's payload slot (BC-27).
    def dest_addr(self, dest, extra=0):
        kind, base = dest
        if kind == "F": self.emit("ADDR", REGIONS["STACK"], base + extra); return
        self.emit("LDF", TYPES["u32"], self.slot_param)
        if base + extra: self.emit("FIELD", base + extra)

    def build(self, e, t, dest):
        """Build the rvalue aggregate e of type t directly in dest (V-36)."""
        k = e[0]; size = self.L.size(t)
        if k == "list":
            if all(self.const_scalar(x) is not None for x in e[1]) and self.L.is_scalar(t[1]):
                off = self.c.add_const(b"".join(self.L.encode_value(self.const_scalar(x), t[1]) for x in e[1]))
                self.dest_addr(dest); self.emit("ADDR", REGIONS["CONST"], off); self.emit("COPY", size); return
            esz = self.L.size(t[1])
            for i, x in enumerate(e[1]): self.build_into(dest, i * esz, x, t[1])
            return
        if k == "ctor":
            for f, x in e[2]:
                off, ft = self.L.field(t, f); self.build_into(dest, off, x, ft)
            return
        if k == "call" and e[1] == ("name", "fill"):
            et = t[1]; x = e[3][0][1]
            if self.L.is_scalar(et):
                self.dest_addr(dest); self.value(x); self.emit("FILL", self.L.tcode(et), t[2])
            else:
                self.dest_addr(dest); self.address(x); self.emit("FILLB", self.L.size(et), t[2])
            return
        if k == "call" and e[1][0] == "name" and e[1][1] in ("encode_be", "encode_le"):
            x = e[3][0][1]; self.dest_addr(dest); self.value(x)
            self.emit("ENCODE", self.L.tcode(self.type_of(x)), 0 if e[1][1].endswith("be") else 1); return
        if k == "attempt":
            if dest[0] == "F":
                self.call(e[1], slot_at=dest[1]); self.on_error(e[2] if len(e) > 2 else None); return
            kind = self.call(e[1]); self.on_error(e[2] if len(e) > 2 else None)
            self.dest_addr(dest); self.emit("ADDR", REGIONS["STACK"], kind[1]); self.emit("COPY", size); return
        raise CompileError(f"build {k}")

    def build_into(self, dest, extra, x, t):
        """Store the value of x at offset extra of dest."""
        if self.L.is_scalar(t):
            if dest[0] == "F": self.value(x); self.emit("STF", self.L.tcode(t), dest[1] + extra)
            else: self.dest_addr(dest, extra); self.value(x); self.emit("STI", self.L.tcode(t))
        elif self.is_rvalue(x):
            self.build(x, t, (dest[0], dest[1] + extra))
        else:
            self.dest_addr(dest, extra); self.address(x); self.emit("COPY", self.L.size(t))

    # ---- calls: returns ('none',) | ('scalar',) with the payload cell pushed | ('slot', frame offset)
    def call(self, e, slot_at=None):
        target, args = e[1], e[3]
        path = pltcheck.platform_path(target)
        if path is not None:
            entry = self.c.chk.catalog[path]; params, ret = entry["params"], entry["ret"]
            cells = self.arguments(args, params)
            slot = None
            if ret != "none" and not self.L.is_scalar(ret):
                slot = self.alloc(self.L.size(ret)) if slot_at is None else slot_at; self.emit("ADDR", REGIONS["STACK"], slot); cells += 1
            self.c.natives.add(isa.NATIVE_NUMBERS[path])
            scalar = ret != "none" and slot is None
            self.emit("NATIVE", isa.NATIVE_NUMBERS[path], pops=cells, pushes=1 if scalar else 0)
            return ("none",) if ret == "none" else ("scalar",) if scalar else ("slot", slot)
        name = target[1]
        if name in CHECKED:
            t = self.type_of(e)[1]
            for _, a in args: self.value(a)
            self.emit(CHECKED[name], self.L.tcode(t)); return ("scalar",)
        if name == "checked_convert":
            a = args[0][1]; self.value(a)
            self.emit("CCONVERT", self.L.tcode(self.type_of(a)), self.L.tcode(self.type_of(e)[1])); return ("scalar",)
        params, ret, _ = self.typed.funcs[name]
        cells = self.arguments(args, params)
        slot = None
        if ret != "none" and not self.L.is_scalar(ret):
            slot = self.alloc(self.L.size(ret)) if slot_at is None else slot_at; self.emit("ADDR", REGIONS["STACK"], slot); cells += 1
        self.callees.add(name)
        scalar = ret != "none" and slot is None
        self.emit("CALL", self.c.findex[name], pops=cells, pushes=1 if scalar else 0)
        return ("none",) if ret == "none" else ("scalar",) if scalar else ("slot", slot)

    def arguments(self, args, params):
        cells = 0
        for (mode, a), (_, pmode, pt) in zip(args, params):
            if self.L.is_view(pt): self.view(a); cells += 2
            elif mode in ("ref", "inout") or not self.L.is_scalar(pt): self.address(a); cells += 1
            else: self.value(a); cells += 1
        return cells

    def err_member(self, e):
        owner, member = e[1][1], e[2]
        if owner == "CardError": return CAT_PLATFORM, CARD_ERROR_CODES[member]
        return CAT_APP, self.c.app_codes[(owner, member)]

    def on_error(self, else_member):
        """After a call: on Err, propagate (or map to else_member), aborting an enclosing transaction (TXN-18)."""
        if self.depth is None: return                  # unreachable
        key = (self.depth, self.in_txn, None if else_member is None else self.err_member(else_member))
        if key not in self.tramp: self.tramp[key] = self.label()
        self.emit("JERR", self.tramp[key])

    # ---- statements
    def block(self, body):
        self.scopes.append({}); mark = self.cur
        for s in body: self.stmt(s)
        self.scopes.pop()
        if self.c.reuse: self.cur = mark                 # a block's locals end with it (V-34)

    def bind(self, name, b): self.scopes[-1][name] = b

    def assign(self, dest, src):
        dt = self.type_of(dest)
        if dest[0] == "slice":
            et = dt[1]; self.view(dest)
            if src[0] == "slice" or (src[0] == "name" and self.lookup_kind(src[1]) == "view"):
                self.view(src)
            else:
                st = self.type_of(src)
                if src[0] in ("list", "call", "ctor") and not (src[0] == "call" and pltcheck.platform_path(src[1])):
                    off = self.materialise(src, st); self.emit("ADDR", REGIONS["STACK"], off)
                else:
                    self.address(src)
                self.emit("VIEW", st[2])
            self.emit("COPYV", self.L.size(et)); return
        if self.L.is_scalar(dt):
            p = self.place(dest); self.value(src)
            self.emit("STI", self.L.tcode(dt)) if p[0] == "dyn" else self.store_static(p); return
        p = self.place(dest); self.to_address(p)
        if src[0] in ("name", "field", "index"):
            self.address(src)
        else:
            off = self.materialise(src, dt); self.emit("ADDR", REGIONS["STACK"], off)
        self.emit("COPY", self.L.size(dt))

    def lookup_kind(self, name):
        try: return self.lookup(name)[0]
        except CompileError: return None

    def stmt(self, s):
        mark = self.cur
        var_end = self.stmt_body(s)                       # a var's own slot lives on with its block
        if self.c.reuse:                                  # a statement's temporaries end with it (V-34)
            self.cur = var_end if var_end is not None and not self.c.reuse_mutant else mark

    def stmt_body(self, s):
        k = s[0]
        if k == "var":
            t = self.typed.decls[id(s)]; off = self.alloc(self.L.size(t)); var_end = self.cur
            if s[3] is None:
                if self.L.is_scalar(t): self.push(0); self.emit("STF", self.L.tcode(t), off)
                else: self.emit("ADDR", REGIONS["STACK"], off); self.emit("ZERO", self.L.size(t))
            elif self.L.is_scalar(t):
                self.value(s[3]); self.emit("STF", self.L.tcode(t), off)
            elif self.is_rvalue(s[3]):
                self.build(s[3], t, ("F", off))                     # in place (V-36)
            else:
                self.emit("ADDR", REGIONS["STACK"], off); self.address(s[3]); self.emit("COPY", self.L.size(t))
            self.bind(s[1], ("frame", off, t)); return var_end
        elif k == "assign": self.assign(s[1], s[2])
        elif k == "compound":
            dest, op, src = s[1], s[2], s[3]; dt = self.type_of(dest)
            p = self.place(dest)
            if p[0] == "dyn": self.emit("DUP")
            self.load(p)
            self.value(src)
            if op in ARITH: self.emit(ARITH[op], self.L.tcode(dt))
            elif op in BITW: self.emit(BITW[op])
            else: self.emit("SHL" if op == "<<" else "SHR", self.L.tcode(dt))
            self.emit("STI", self.L.tcode(dt)) if p[0] == "dyn" else self.store_static(p)
        elif k == "if":
            end = self.label()
            for c, body in s[1]:
                nxt = self.label(); self.value(c); self.emit("JZ", nxt)
                self.block(body); self.emit("JMP", end); self.place_label(nxt)
            if s[2] is not None: self.block(s[2])
            self.place_label(end)
        elif k == "while":
            top, end = self.label(), self.label()
            self.place_label(top); self.value(s[1]); self.emit("JZ", end)
            self.loops.append((end, top)); self.block(s[2]); self.loops.pop()
            self.emit("JMP", top); self.place_label(end)
        elif k == "for":
            t = self.typed.decls[id(s)]; tc = self.L.tcode(t)
            idx = self.alloc(4); hi = self.alloc(4)
            self.value(s[3]); self.emit("STF", tc, idx); self.value(s[4]); self.emit("STF", tc, hi)
            top, step, end = self.label(), self.label(), self.label()
            self.place_label(top); self.emit("LDF", tc, idx); self.emit("LDF", tc, hi); self.emit("LT", tc); self.emit("JZ", end)
            self.scopes.append({s[1]: ("frame", idx, t)}); self.loops.append((end, step))
            self.block(s[5]); self.loops.pop(); self.scopes.pop()
            self.place_label(step); self.emit("LDF", tc, idx); self.push(1); self.emit("ADD", tc); self.emit("STF", tc, idx)
            self.emit("JMP", top); self.place_label(end)
        elif k == "break": self.emit("JMP", self.loops[-1][0])
        elif k == "continue": self.emit("JMP", self.loops[-1][1])
        elif k == "match": self.match(s)
        elif k == "return_ok":
            if s[1] is None: self.emit("RET")
            elif self.L.is_scalar(self.ret): self.value(s[1]); self.emit("RETV")
            elif self.is_rvalue(s[1]):
                self.build(s[1], self.ret, ("S", 0)); self.emit("RET")    # straight into the caller's slot (V-36)
            else:
                self.emit("LDF", TYPES["u32"], self.slot_param); self.address(s[1])
                self.emit("COPY", self.L.size(self.ret)); self.emit("RET")
        elif k in ("return_err", "abort"):
            if k == "abort": self.emit("TXN.ABORT")
            e = s[1]
            if e[0] == "name" and self.lookup_kind(e[1]) == "errbind":
                self.emit("LDF", TYPES["u32"], self.lookup(e[1])[1]); self.emit("ERRRAISE")
            else:
                self.emit("ERR", *self.err_member(e))
        elif k == "return_fwd":
            if self.slot_param is not None and pltcheck.platform_path(s[1][1]) is not None:
                kind = self.call(s[1]); self.on_error(None)          # a native's aggregate payload: copy it on
                self.emit("LDF", TYPES["u32"], self.slot_param); self.emit("ADDR", REGIONS["STACK"], kind[1])
                self.emit("COPY", self.L.size(self.ret)); self.emit("RET"); return
            kind = self.call_forwarding(s[1]); self.on_error(None)
            self.emit("RETV" if kind[0] == "scalar" else "RET")
        elif k == "require":
            ok = self.label(); self.value(s[1]); self.emit("JNZ", ok)
            if self.in_txn: self.emit("TXN.ABORT")
            self.emit("ERR", *self.err_member(s[2])); self.place_label(ok)
        elif k == "attempt":
            self.call(s[1]); self.on_error(s[2])
        elif k == "ignore":
            kind = self.call(s[1])
            if kind[0] == "scalar": self.emit("DROP")
        elif k == "transaction":
            self.emit("TXN.BEGIN"); saved = self.in_txn; self.in_txn = True
            self.block(s[1]); self.in_txn = saved; self.emit("TXN.COMMIT")
        elif k == "wipe":
            e = s[1]
            if e[0] == "slice" or self.L.is_view(self.type_of(e)):
                self.view(e); self.emit("WIPEV", self.L.size(self.type_of(e)[1]))
            else:
                t = self.address(e); self.emit("WIPE", self.L.size(t))
        else:
            raise CompileError(f"statement {k}")

    def call_forwarding(self, e):
        """`return c;` for an aggregate payload passes this function's own slot on (BC-27)."""
        if self.slot_param is None: return self.call(e)
        target, args = e[1], e[3]
        name = target[1]; params, ret, _ = self.typed.funcs[name]
        cells = self.arguments(args, params) + 1
        self.emit("LDF", TYPES["u32"], self.slot_param)
        self.callees.add(name); self.emit("CALL", self.c.findex[name], pops=cells, pushes=0)
        return ("none",)

    def match(self, s):
        st = self.type_of(s[1]); end = self.label()
        if self.L.is_enum(st):
            self.value(s[1]); labels = [None] * len(self.L.enum_order[st]); arms = []
            for pat, body in s[2]:
                lab = self.label(); labels[self.L.ordinal(st, pat[2])] = lab; arms.append((lab, body))
            self.emit("SWITCH", labels)
            for lab, body in arms:
                self.place_label(lab); self.block(body); self.emit("JMP", end)
            self.place_label(end); return
        kind = self.call(s[1]); payload = None
        if kind[0] == "scalar":
            payload = self.alloc(4); self.emit("STF", self.L.tcode(st[1]), payload)
        elif kind[0] == "slot": payload = kind[1]
        arms = []; ok_arm = None; catch = None
        for pat, body in s[2]:
            lab = self.label(); arms.append((lab, pat, body))
            if pat[0] == "ok": ok_arm = lab
            elif pat[0] == "err_member": self.emit("JERRIS", *self.err_member(("field", ("name", pat[1]), pat[2])), lab)
            elif pat[0] == "err_set": self.emit("JERRCAT", CAT_APP, lab)
            elif pat[0] in ("err_bind", "wild"): catch = lab
        if catch is not None: self.emit("JERR", catch)
        self.emit("JMP", ok_arm)
        for lab, pat, body in arms:
            self.place_label(lab); self.scopes.append({})
            if pat[0] == "ok" and pat[1] not in (None, "_"): self.bind(pat[1], ("frame", payload, st[1]))
            if pat[0] == "err_set" and pat[2] != "_":
                slot = self.alloc(2); self.emit("ERRCODE"); self.emit("STF", TYPES["u16"], slot)
                self.bind(pat[2], ("frame", slot, "u16"))
            if pat[0] == "err_bind" and pat[1] != "_":
                slot = self.alloc(4); self.emit("ERRGET"); self.emit("STF", TYPES["u32"], slot)
                self.bind(pat[1], ("errbind", slot))
            self.block(body); self.scopes.pop(); self.emit("JMP", end)
        self.place_label(end)

    # ---- the whole function
    def generate(self):
        self.loops = []; self.in_txn = False
        for pn, off, pt in self.prologue:
            local = self.alloc(self.L.size(pt))
            self.emit("ADDR", REGIONS["STACK"], local); self.emit("LDF", TYPES["u32"], off); self.emit("COPY", self.L.size(pt))
            self.scopes[0][pn] = ("frame", local, pt)
        self.block(self.typed.bodies[self.name])
        for (depth, txn, member), lab in self.tramp.items():
            self.depth = None; self.label_depth[lab] = depth; self.place_label(lab)
            if txn: self.emit("TXN.ABORT")
            if member is None: self.emit("FWD")
            else: self.emit("ERR", *member)
        self.operand_base = self.high
        self.frame_size = self.high + 4 * self.max_depth
        return self

    # VM7b (b): a comparison with PUSH.B k as its right operand, then JNZ or JZ, as one compare-and-branch.
    # JZ jumps when the comparison is false, so it takes the opposite form.
    CMP_BRANCH = {("EQ", "JNZ"): "JEQI8", ("EQ", "JZ"): "JNEI8", ("NE", "JNZ"): "JNEI8", ("NE", "JZ"): "JEQI8",
                  ("LT", "JNZ"): "JLTI8", ("LT", "JZ"): "JGEI8", ("LE", "JNZ"): "JLEI8", ("LE", "JZ"): "JGTI8",
                  ("GT", "JNZ"): "JGTI8", ("GT", "JZ"): "JLEI8", ("GE", "JNZ"): "JGEI8", ("GE", "JZ"): "JLTI8"}

    def shorten(self):
        """Select the short forms (V-38, bytecode.md sections 2.12 and 2.13). Semantics are unchanged.
        A compare-and-branch becomes a ("fused", name, operands, long items) entry: assemble() uses the short form
        when its 8-bit jump reaches, and the original three instructions otherwise."""
        S = self.c.shorten; U32 = TYPES["u32"]; out = []
        code = self.code; i = 0
        while i < len(code):
            item = code[i]
            if "cmpjump" in S and i + 2 < len(code) and all(x[0] == "op" for x in code[i:i + 3]):
                p, c, j = code[i:i + 3]
                if p[1] == "PUSH.B" and (c[1], j[1]) in self.CMP_BRANCH:
                    name = self.CMP_BRANCH[(c[1], j[1])]; k = p[2][0]; lab = j[2][-1]
                    ops = [k, lab] if name in ("JEQI8", "JNEI8") else [c[2][0], k, lab]
                    push = ("op", "PUSH0" if k == 0 else "PUSH1", []) if "push" in S and k in (0, 1) else p
                    out.append(("fused", name, ops, [push, c, j])); i += 3; continue
            # SLICEF: a view in the frame, sliced from a u32 frame slot to its end (candidate 4)
            if "slice" in S and i + 4 < len(code) and all(x[0] == "op" for x in code[i:i + 5]):
                ops = [x[1] for x in code[i:i + 5]]; a = [x[2] for x in code[i:i + 5]]
                if (ops == ["LDF", "LDF", "LDF", "LDF", "SLICE"] and all(x[0] == U32 for x in a[:4])
                        and a[1][1] == a[0][1] + 4 and a[3][1] == a[1][1] and a[0][1] < 256 and a[2][1] < 256):
                    out.append(("op", "SLICEF", [a[4][0], a[0][1], a[2][1]])); i += 5; continue
                # VM7b (c) SLICEFK: the same, from a constant start below 256
                if ("slicek" in S and ops == ["LDF", "LDF", "PUSH.B", "LDF", "SLICE"] and a[0][0] == U32 and a[1][0] == U32
                        and a[3][0] == U32 and a[1][1] == a[0][1] + 4 and a[3][1] == a[1][1] and a[0][1] < 256):
                    out.append(("op", "SLICEFK", [a[4][0], a[0][1], a[2][0]])); i += 5; continue
            if item[0] == "op":
                op, ar = item[1], item[2]
                if "frame" in S and op in ("LDF", "STF") and ar[1] < 256:          # candidate 2
                    if ar[0] == U32: item = ("op", ("LDFW" if op == "LDF" else "STFW"), [ar[1]])
                    elif "byte" in S and ar[0] == TYPES["u8"]: item = ("op", ("LDFB" if op == "LDF" else "STFB"), [ar[1]])   # VM7b (e)
                    else: item = ("op", op + "8", ar)
                elif "addr" in S and op == "ADDR" and ar[0] == REGIONS["STACK"] and ar[1] < 256:   # candidate 3
                    item = ("op", "ADDRF", [ar[1]])
                elif "addr16" in S and op == "ADDR" and ar[1] < 0x10000:            # VM7b (d)
                    item = ("op", "ADDRH", ar)
                elif "push" in S and op == "PUSH.B" and ar[0] in (0, 1):            # candidate 5
                    item = ("op", "PUSH0" if ar[0] == 0 else "PUSH1", [])
            out.append(item); i += 1
        self.code = out

    def share_exits(self):
        """VM7b (a): repeated error exits within a function become one. Each `J… ok; [TXN.ABORT]; ERR c; ok:`
        whose exit occurs more than once becomes `J(opposite) shared`, and one copy of the exit is placed after the
        function's last instruction, which is a terminator, so nothing falls into it."""
        code = self.code
        if not code or code[-1][0] != "op" or code[-1][1] not in TERMINATORS: return
        sites = {}
        for k in range(len(code) - 2):
            j = code[k]
            if j[0] != "op" or j[1] not in ("JZ", "JNZ"): continue
            for n in (1, 2):
                body = code[k + 1:k + 1 + n]
                if (k + 1 + n < len(code) and code[k + 1 + n] == ("label", j[2][0]) and all(x[0] == "op" for x in body)
                        and body[-1][1] == "ERR" and (n == 1 or body[0][1] == "TXN.ABORT")):
                    sites.setdefault(tuple((x[1], tuple(x[2])) for x in body), []).append((k, n)); break
        shared = {key: v for key, v in sites.items() if len(v) > 1}
        if not shared: return
        replace, drop, tail = {}, set(), []
        for key, v in shared.items():
            exit_label = self.label()
            for k, n in v:
                replace[k] = ("op", "JNZ" if code[k][1] == "JZ" else "JZ", [exit_label]); drop.update(range(k + 1, k + 1 + n))
            tail.append(("label", exit_label)); tail += [("op", name, list(ops)) for name, ops in key]
        self.code = [replace.get(k, x) for k, x in enumerate(code) if k not in drop] + tail

    def assemble(self):
        """Resolve labels, relaxing jumps to their 8-bit forms where they reach (candidate 6): returns the code."""
        if "errexit" in self.c.shorten: self.share_exits()
        self.shorten()
        short = {k for k, item in enumerate(self.code)
                 if "jump" in self.c.shorten and item[0] == "op" and item[1] in isa.SHORT_JUMP}
        short |= {k for k, item in enumerate(self.code) if item[0] == "fused"}
        def name_of(k, item): return isa.SHORT_JUMP[item[1]] if k in short and item[0] == "op" else item[1]
        def size(k, item):
            if item[0] == "fused" and k not in short: return sum(isa.size_of(x[1], x[2]) for x in item[3])
            return isa.size_of(name_of(k, item), item[2])
        while True:                                       # start short, lengthen what does not reach, repeat
            pos, ends, pc = {}, {}, 0
            for k, item in enumerate(self.code):
                if item[0] == "label": pos[item[1]] = pc; continue
                pc += size(k, item); ends[k] = pc
            far = {k for k in short if not -128 <= pos[self.code[k][2][-1]] - ends[k] <= 127}
            if not far: break
            short -= far
        out = bytearray(); pc = 0
        for k, item in enumerate(self.code):
            if item[0] == "label": continue
            if item[0] == "fused" and k not in short:      # out of 8-bit reach: the original instructions
                for x in item[3]:
                    end = pc + isa.size_of(x[1], x[2])
                    def rel_long(lab, end=end):
                        r = pos[lab] - end
                        if not -32768 <= r < 32768: raise CompileError(f"{self.name}: jump out of range")
                        return r
                    out += isa.encode(x[1], x[2], rel_long); pc = end
                continue
            name = name_of(k, item); size = isa.size_of(name, item[2]); end = pc + size
            def rel(lab, end=end):
                r = pos[lab] - end
                if not -32768 <= r < 32768: raise CompileError(f"{self.name}: jump out of range")
                return r
            out += isa.encode(name, item[2], rel); pc = end
        return bytes(out)

# stack effects (pops, pushes); CALL and NATIVE pass theirs explicitly
STACK = {
    "PUSH.B": (0, 1), "PUSH.H": (0, 1), "PUSH.W": (0, 1), "DUP": (1, 2), "DROP": (1, 0), "SWAP": (2, 2), "OVER": (2, 3),
    "DUP2": (2, 4), "DROP2": (2, 0),
    "LDF": (0, 1), "LDS": (0, 1), "LDC": (0, 1), "LDP": (0, 1), "STF": (1, 0), "STS": (1, 0), "STP": (1, 0),
    "ADDR": (0, 1), "INDEX": (2, 1), "INDEXV": (3, 1), "FIELD": (1, 1), "LDI": (1, 1), "STI": (2, 0),
    "VIEW": (1, 2), "SLICE": (4, 2), "COPY": (2, 0), "COPYV": (4, 0), "FILL": (2, 0), "FILLB": (2, 0), "ZERO": (1, 0),
    "WIPE": (1, 0), "WIPEV": (2, 0), "EQUAL": (4, 1), "COMPARE": (4, 1), "ENCODE": (2, 0), "DECODE": (2, 1),
    "NEG": (1, 1), "INV": (1, 1), "BNOT": (1, 1), "TRUNC": (1, 1), "CCONVERT": (1, 1), "CNEG": (1, 1),
    "JMP": (0, 0), "JZ": (1, 0), "JNZ": (1, 0), "SWITCH": (1, 0),
    "RET": (0, 0), "RETV": (1, 0), "ERR": (0, 0), "FWD": (0, 0), "ERRRAISE": (1, 0),
    "JERR": (0, 0), "JERRIS": (0, 0), "JERRCAT": (0, 0), "ERRCODE": (0, 1), "ERRGET": (0, 1),
    "TXN.BEGIN": (0, 0), "TXN.COMMIT": (0, 0), "TXN.ABORT": (0, 0),
}
for _op in ("ADD", "SUB", "MUL", "DIV", "REM", "WADD", "WSUB", "WMUL", "CADD", "CSUB", "CMUL", "CDIV", "CREM",
            "AND", "OR", "XOR", "SHL", "SHR", "EQ", "NE", "LT", "LE", "GT", "GE"):
    STACK[_op] = (2, 1)

# ------------------------------------------------------------------ the program
class Compiler:
    def __init__(self, toks, binding=None):
        self.typed = typer.type_program(toks)
        self.chk = self.typed.chk; self.layout = Layout(self.chk); self.binding = binding
        self.const_data = bytearray(); self.natives = set()
        self.reuse, self.reuse_mutant = True, False    # slot reuse (V-34); the mutant frees live locals
        self.shorten = {"frame", "addr", "slice", "push", "jump",    # the short forms of VM6 (V-38)
                        "byte", "addr16", "cmpjump", "slicek",       # and of VM7b (vm/bytecode.md §2.13),
                        "errexit"}                                    # with its shared error exits
        self.app_codes = {k: v for k, v in pltcheck_error_codes(self.chk.toks).items()}
        names = list(self.typed.bodies)
        self.findex = {n: i for i, n in enumerate(names)}
        self.lay_out_globals()

    def add_const(self, data):
        off = len(self.const_data); self.const_data += data; return off

    def lay_out_globals(self):
        toks = self.chk.toks; L = self.layout
        kind = {}
        for i in range(len(toks) - 1):
            if toks[i][1] in ("persistent", "session") and (i == 0 or toks[i - 1][1] in (";", "}")):
                kind[toks[i + 1][1]] = toks[i][1]
        self.persistent, self.session = {}, {}; poff = soff = 0
        for n in self.chk.cp.globals:
            t = self.chk.globals[n]
            if kind.get(n) == "persistent": self.persistent[n] = (poff, t); poff += L.size(t)
            else: self.session[n] = (soff, t); soff += L.size(t)
        self.persistent_size, self.session_size = poff, soff
        self.const_scalar, self.const_agg = {}, {}
        for n in self.chk.cp.consts:
            v, t = self.chk.cp.const_value(n)
            if L.is_scalar(t):
                self.const_scalar[n] = L.ordinal(t, v.split(".")[1]) if L.is_enum(t) else (1 if v is True else 0 if v is False else v)
            else:
                self.const_agg[n] = (self.add_const(L.encode_value(v, t)), t)

    def compile(self):
        self.gens = {n: FuncGen(self, n).generate() for n in self.typed.bodies}
        code = bytearray(); offsets = {}
        for n, g in self.gens.items():
            offsets[n] = len(code); g.bytes = g.assemble(); code += g.bytes
        # stack need over the static call graph (VEX-17); acyclic (FUN-5)
        need = {}
        def stack_need(n):
            if n not in need:
                g = self.gens[n]; need[n] = g.frame_size + max([stack_need(c) for c in g.callees] or [0])
            return need[n]
        entries = [self.typed.command] + [h for h in ("on_install", "on_session_start", "on_select") if h in self.findex]
        stack = max(stack_need(n) for n in entries)
        functions = b"".join(isa.FUNC.pack(offsets[n], g.frame_size, g.argc,
                                           0 if g.ret == "none" else 1 if self.layout.is_scalar(g.ret) else 2,
                                           g.operand_base) for n, g in self.gens.items())
        imports = b"".join(struct.pack("<H", n) for n in sorted(self.natives))
        debug = struct.pack("<H", 0) + struct.pack("<H", len(self.gens)) + b"".join(
            struct.pack("<H", len(n.encode())) + n.encode() for n in self.gens) + struct.pack("<I", 0)
        max_atomic = max([self.layout.size(t) for _, t in self.persistent.values()] or [0])
        functions_off = isa.HEADER.size; imports_off = functions_off + len(functions)
        const_off = imports_off + len(imports); code_off = const_off + len(self.const_data); debug_off = code_off + len(code)
        size = debug_off + len(debug)
        entry = lambda h: self.findex.get(h, isa.NONE_ENTRY)
        header = isa.HEADER.pack(isa.MAGIC, isa.FORMAT, 1, isa.BINDINGS[self.binding], size, self.persistent_size,
                                 self.session_size, stack, max_atomic, len(self.gens), self.findex[self.typed.command],
                                 entry("on_install"), entry("on_session_start"), entry("on_select"), len(self.natives),
                                 functions_off, imports_off, const_off, len(self.const_data), code_off, len(code),
                                 debug_off, len(debug))
        self.image = header + functions + imports + bytes(self.const_data) + bytes(code) + debug
        self.report = {"image": len(self.image), "code": len(code), "const": len(self.const_data),
                       "functions": {n: {"code": len(g.bytes), "frame": g.frame_size, "depth": g.max_depth} for n, g in self.gens.items()},
                       "stack_need": stack, "persistent": self.persistent_size, "session": self.session_size,
                       "max_atomic": max_atomic, "natives": sorted(self.natives)}
        return self.image

def pltcheck_error_codes(toks):
    codes = {}
    for i, (_, v) in enumerate(toks):
        if v == "errors" and i + 2 < len(toks) and toks[i + 2][1] == "{":
            owner = toks[i + 1][1]; j = i + 3
            while toks[j][1] != "}":
                codes[(owner, toks[j][1])] = pltcheck.literal_value(toks[j + 2][1]); j += 4
    return codes

def compile_files(files, binding=None, fragment=False):
    from lexcheck import lex
    import hepcheck
    toks = sum((lex(f.read_bytes()) for f in files), [])
    if fragment: toks = toks + lex(hepcheck.SCAFFOLD)
    c = Compiler(toks, binding); c.compile(); return c

if __name__ == "__main__":
    from lexcheck import header
    from scenario import program_files
    src = pathlib.Path(sys.argv[1]); files = program_files(src) if src.is_dir() else [src]
    meta = header(files[0].read_bytes())
    c = compile_files(files, meta.get("binding"), meta.get("kind", "fragment" if "conformance" in str(src) else "application") == "fragment")
    if "-o" in sys.argv: pathlib.Path(sys.argv[sys.argv.index("-o") + 1]).write_bytes(c.image)
    if "--report" in sys.argv or "-o" not in sys.argv:
        import json; print(json.dumps(c.report, indent=2))
