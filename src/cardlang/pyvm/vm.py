"""The prototype CardLang VM (VM5): executes version-0 images (vm/bytecode.md) as the C VM will.

All of the VM's own mutable state is in one context object, Ctx, whose fields have declared C sizes (V-31). The
interpreter is a set of functions over that context; it keeps no other state. Regions (SESSION, STACK, REQUEST,
RESPONSE) are buffers the platform provides; PERSISTENT is reached only through the HAL (V-7).
Traps are raised as Trap inside the single interpreter loop and turned into the entry's result there (VEX-39).
"""
import sys, pathlib, struct
from cardlang.bytecode import isa
from cardlang.bytecode.isa import TYPE_NAMES, WIDTH, SIGNED, REGIONS
from cardlang.pyvm.hal import HalStatus, PowerLoss, CL_TXN_CAPACITY, CL_COMMIT_FAILED, CL_FATAL

CONST, PERSISTENT, SESSION, STACK, REQUEST, RESPONSE = range(6)
RET_NONE = 0xFFFFFFFF
BOUNCE = 128                                                    # V-22

class Trap(Exception):
    def __init__(self, kind): super().__init__(kind); self.kind = kind

class LoadError(Exception):
    pass

class Ctx:
    """The VM context (cl_vm, VEX-49). SIZES gives each field's size in bytes on a 32-bit target."""
    SIZES = {
        "image": 4, "image_size": 4, "code_off": 4, "code_size": 4, "const_off": 4, "func_off": 4, "func_count": 2,
        "session": 4, "session_size": 4, "stack": 4, "stack_size": 4,
        "request": 4, "request_len": 4, "response": 4, "response_cap": 4,
        "pc": 4, "fp": 4, "sp": 4, "out_cat": 1, "out_code": 2,
        "txn": 1, "atomic": 1, "state": 1, "budget": 4, "budget_cfg": 4, "hal": 4, "bounce": BOUNCE,
    }
    __slots__ = tuple(SIZES)

    def __init__(self):
        for f in self.__slots__: setattr(self, f, None)

    @classmethod
    def size(cls): return sum(cls.SIZES.values())

# lifecycle states (VEX-44)
NOT_INSTALLED, NO_SESSION, IN_SESSION, UNAVAILABLE = range(4)

# ------------------------------------------------------------------ cells and types
MASK = 0xFFFFFFFF

def norm(v, t):
    """Normalize an integer to type code t as a 32-bit cell (BC-4)."""
    name = TYPE_NAMES[t]; bits = 8 * WIDTH[name]; v &= (1 << bits) - 1
    if name in SIGNED and v >= 1 << (bits - 1): v -= 1 << bits
    return v & MASK

def val(c, t):
    """The mathematical value of a normalized cell of type code t."""
    name = TYPE_NAMES[t]
    return c - (1 << 32) if name in SIGNED and c >= 1 << 31 else c

def in_range(v, t):
    name = TYPE_NAMES[t]; bits = 8 * WIDTH[name]
    lo, hi = (-(1 << (bits - 1)), (1 << (bits - 1)) - 1) if name in SIGNED else (0, (1 << bits) - 1)
    return lo <= v <= hi

def arith_trap(v):
    return "OVERFLOW" if v > 0 else "UNDERFLOW"

# ------------------------------------------------------------------ loading (IMG-11)
def load(ctx, image, config, hal):
    h = isa.HEADER.unpack_from(image, 0)
    (magic, fmt, profile, binding, image_size, persistent_size, session_size, stack_need, max_atomic, fcount,
     e_cmd, e_inst, e_sess, e_sel, icount, foff, ioff, coff, csize, codeoff, codesize, doff, dsize) = h
    if magic != isa.MAGIC or fmt != isa.FORMAT: raise LoadError("format")          # format 1 only (V-41)
    if profile != 1 or binding not in (0, config.get("binding", binding)): raise LoadError("profile or binding")
    if image_size != len(image): raise LoadError("size")
    if session_size > len(config["session"]) or stack_need > len(config["stack"]): raise LoadError("areas")
    if max_atomic > hal.atomic_capacity(): raise LoadError("atomic capacity")
    for i in range(icount):
        n = struct.unpack_from("<H", image, ioff + 2 * i)[0]
        if n not in isa.NATIVE_NAMES or (n >= 0xF000 and not config.get("test_natives")): raise LoadError(f"native {n}")
    ctx.image, ctx.image_size = image, len(image)
    ctx.code_off, ctx.code_size, ctx.const_off, ctx.func_off, ctx.func_count = codeoff, codesize, coff, foff, fcount
    ctx.session, ctx.session_size = config["session"], session_size
    ctx.stack, ctx.stack_size = config["stack"], len(config["stack"])
    ctx.budget_cfg = config.get("budget", 1_000_000)
    ctx.hal = hal; ctx.bounce = bytearray(BOUNCE); ctx.txn = 0; ctx.atomic = 0; ctx.state = NOT_INSTALLED
    ctx.out_cat = 0; ctx.out_code = 0; ctx.pc = ctx.fp = ctx.sp = 0
    ctx.request = ctx.response = None; ctx.request_len = ctx.response_cap = 0

def header_field(ctx, index):
    return isa.HEADER.unpack_from(ctx.image, 0)[index]

def function(ctx, i):
    return isa.FUNC.unpack_from(ctx.image, ctx.func_off + 12 * i)     # code, frame_size, argc, payload, operand_base

def function_at(ctx, pc):
    """The index of the function whose code contains pc (code offsets increase with the index, IMG-11)."""
    lo, hi = 0, ctx.func_count - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if function(ctx, mid)[0] <= pc: lo = mid
        else: hi = mid - 1
    return lo

# ------------------------------------------------------------------ memory
def split(a): return a >> 29, a & 0x1FFFFFFF

def region_buf(ctx, tag):
    return {SESSION: ctx.session, STACK: ctx.stack, REQUEST: ctx.request, RESPONSE: ctx.response}[tag]

def read(ctx, a, n):
    tag, off = split(a)
    if tag == CONST: return bytes(ctx.image[ctx.const_off + off:ctx.const_off + off + n])
    if tag == PERSISTENT:
        out = bytearray()
        for k in range(0, n, BOUNCE):                       # persistent data moves through the bounce buffer (VEX-34)
            chunk = ctx.hal.read(off + k, min(BOUNCE, n - k)); ctx.bounce[:len(chunk)] = chunk; out += chunk
        ctx.bounce[:] = bytes(BOUNCE)
        return bytes(out)
    return bytes(region_buf(ctx, tag)[off:off + n])

def write(ctx, a, data):
    tag, off = split(a)
    if tag == PERSISTENT:
        hal_call(ctx, ctx.hal.update_begin, off, len(data)); ctx.atomic = 1
        for k in range(0, len(data), BOUNCE): ctx.hal.update_write(off + k, data[k:k + BOUNCE])
        ctx.hal.update_end(); ctx.atomic = 0
        return
    assert tag not in (CONST, REQUEST), "store into a read-only region"
    region_buf(ctx, tag)[off:off + len(data)] = data

def hal_call(ctx, fn, *args):
    try:
        return fn(*args)
    except HalStatus as s:
        if s.code == CL_TXN_CAPACITY: raise Trap("TXN-CAPACITY")
        if s.code == CL_COMMIT_FAILED: raise Trap("COMMIT")
        raise

def load_scalar(ctx, a, t):
    w = WIDTH[TYPE_NAMES[t]]; return norm(int.from_bytes(read(ctx, a, w), "little"), t)

def store_scalar(ctx, a, t, c):
    w = WIDTH[TYPE_NAMES[t]]; write(ctx, a, (c & ((1 << (8 * w)) - 1)).to_bytes(w, "little"))

def copy(ctx, d, s, n):
    if split(d)[0] == PERSISTENT and split(s)[0] == PERSISTENT:
        hal_call(ctx, ctx.hal.copy, split(d)[1], split(s)[1], n); return
    write(ctx, d, read(ctx, s, n))                                # the whole source first: overlap-safe (VEX-15)

# ------------------------------------------------------------------ the stack
def push(ctx, c): struct.pack_into("<I", ctx.stack, ctx.sp, c & MASK); ctx.sp += 4
def pop(ctx): ctx.sp -= 4; return struct.unpack_from("<I", ctx.stack, ctx.sp)[0]

def charge(ctx, n):
    if ctx.budget - n < 0: raise Trap("EXHAUSTED")
    ctx.budget -= n

def blocks(n): return (n + 15) // 16

# ------------------------------------------------------------------ the interpreter loop
def run(ctx, findex, cells, natives):
    """Run an entry function with the given argument cells. Returns ('ok', payload or None) | ('err', cat, code)."""
    code0, frame_size, argc, payload, operand_base = function(ctx, findex)
    ctx.fp = 0
    struct.pack_into("<II", ctx.stack, 0, RET_NONE, 0)
    for i, c in enumerate(cells): struct.pack_into("<I", ctx.stack, 8 + 4 * i, c)
    ctx.stack[8 + 4 * len(cells):frame_size] = bytes(frame_size - 8 - 4 * len(cells))
    ctx.sp = operand_base; ctx.pc = code0; ctx.budget = ctx.budget_cfg; ctx.out_cat = 0; ctx.out_code = 0
    base = ctx.code_off; img = ctx.image
    while True:
        try:
            name, ops, size = isa.decode(img, base + ctx.pc)
        except KeyError:
            raise Trap("VM")
        charge(ctx, 1)
        next_pc = ctx.pc + size
        r = step(ctx, name, ops, next_pc, natives)
        if r is not None: return r

def leave(ctx, cat, code, value):
    """Return from the current frame (BC-26). Returns the entry result when the entry frame ends."""
    f = function_at(ctx, ctx.pc); _, frame_size, _, payload, _ = function(ctx, f)
    ret_pc, caller_fp = struct.unpack_from("<II", ctx.stack, ctx.fp)
    ctx.stack[ctx.fp:ctx.fp + frame_size] = bytes(frame_size)    # erase the frame (BC-28, PLT-35)
    ctx.sp = ctx.fp; ctx.out_cat, ctx.out_code = cat, code
    if ret_pc == RET_NONE:
        return ("ok", value) if cat == 0 else ("err", cat, code)
    ctx.fp = caller_fp; ctx.pc = ret_pc
    if payload == 1: push(ctx, value if cat == 0 else 0)
    return None

U32 = isa.TYPES["u32"]
SHORT = {"LDF8": "LDF", "STF8": "STF", "PUSH0": "PUSH.B", "PUSH1": "PUSH.B", "JMP8": "JMP", "JZ8": "JZ", "JNZ8": "JNZ",
         "JERR8": "JERR", "LDFW": "LDF", "STFW": "STF", "ADDRF": "ADDR", "LDFB": "LDF", "STFB": "STF", "ADDRH": "ADDR"}

CMP_BRANCH = {"JEQI8", "JNEI8", "JLTI8", "JLEI8", "JGTI8", "JGEI8"}

def step(ctx, name, ops, next_pc, natives):
    if name in SHORT:                                   # a short form: the same semantics as its long form (BC-39)
        if name == "PUSH0": ops = [0]
        elif name == "PUSH1": ops = [1]
        elif name in ("LDFW", "STFW"): ops = [U32, ops[0]]
        elif name in ("LDFB", "STFB"): ops = [isa.TYPES["u8"], ops[0]]
        elif name == "ADDRF": ops = [STACK, ops[0]]
        name = SHORT[name]
    elif name in CMP_BRANCH:                            # PUSH.B k; the comparison; JNZ (VM7b, bytecode.md 2.13)
        x = pop(ctx); k = ops[-2]
        if name in ("JEQI8", "JNEI8"): taken = (x == k) == (name == "JEQI8")
        else:
            xv, kv = val(x, ops[0]), val(k, ops[0])
            taken = {"JLTI8": xv < kv, "JLEI8": xv <= kv, "JGTI8": xv > kv, "JGEI8": xv >= kv}[name]
        ctx.pc = next_pc + ops[-1] if taken else next_pc; return None
    elif name in ("SLICEF", "SLICEFK"):                 # the frame view at base, from the u32 at start (SLICEF) or
        size, base, start = ops                         # from the constant start (SLICEFK, VM7b) to its end
        a = load_scalar(ctx, (STACK << 29) | (ctx.fp + base), U32)
        n = load_scalar(ctx, (STACK << 29) | (ctx.fp + base + 4), U32)
        s = start if name == "SLICEFK" else load_scalar(ctx, (STACK << 29) | (ctx.fp + start), U32)
        if s > n: raise Trap("BOUNDS")
        push(ctx, a + s * size); push(ctx, n - s); ctx.pc = next_pc; return None
    t = ops[0] if ops else None
    ctx_pc = next_pc
    if name in ("PUSH.B", "PUSH.H", "PUSH.W"): push(ctx, ops[0])
    elif name == "DUP": c = pop(ctx); push(ctx, c); push(ctx, c)
    elif name == "DROP": pop(ctx)
    elif name == "SWAP": b = pop(ctx); a = pop(ctx); push(ctx, b); push(ctx, a)
    elif name == "OVER": b = pop(ctx); a = pop(ctx); push(ctx, a); push(ctx, b); push(ctx, a)
    elif name == "DUP2": b = pop(ctx); a = pop(ctx); [push(ctx, x) for x in (a, b, a, b)]
    elif name == "DROP2": pop(ctx); pop(ctx)
    elif name == "LDF": push(ctx, load_scalar(ctx, (STACK << 29) | (ctx.fp + ops[1]), t))
    elif name == "STF": store_scalar(ctx, (STACK << 29) | (ctx.fp + ops[1]), t, pop(ctx))
    elif name == "LDS": push(ctx, load_scalar(ctx, (SESSION << 29) | ops[1], t))
    elif name == "STS": store_scalar(ctx, (SESSION << 29) | ops[1], t, pop(ctx))
    elif name == "LDC": push(ctx, load_scalar(ctx, (CONST << 29) | ops[1], t))
    elif name == "LDP": push(ctx, load_scalar(ctx, (PERSISTENT << 29) | ops[1], t))
    elif name == "STP": store_scalar(ctx, (PERSISTENT << 29) | ops[1], t, pop(ctx))
    elif name == "ADDR":
        off = ctx.fp + ops[1] if ops[0] == STACK else ops[1]
        push(ctx, (ops[0] << 29) | off)
    elif name == "INDEX":
        i = pop(ctx); a = pop(ctx)
        if i >= ops[1]: raise Trap("BOUNDS")
        push(ctx, a + i * ops[0])
    elif name == "INDEXV":
        i = pop(ctx); n = pop(ctx); a = pop(ctx)
        if i >= n: raise Trap("BOUNDS")
        push(ctx, a + i * ops[0])
    elif name == "FIELD": push(ctx, pop(ctx) + ops[0])
    elif name == "LDI": push(ctx, load_scalar(ctx, pop(ctx), t))
    elif name == "STI": c = pop(ctx); a = pop(ctx); store_scalar(ctx, a, t, c)
    elif name == "VIEW": push(ctx, ops[0])
    elif name == "SLICE":
        e = pop(ctx); s = pop(ctx); n = pop(ctx); a = pop(ctx)
        if s > e or e > n: raise Trap("BOUNDS")
        push(ctx, a + s * ops[0]); push(ctx, e - s)
    elif name in ("COPY", "COPYV", "FILL", "FILLB", "ZERO", "WIPE", "WIPEV", "EQUAL", "COMPARE", "ENCODE", "DECODE"):
        block(ctx, name, ops)
    elif name in ("ADD", "SUB", "MUL", "DIV", "REM", "CADD", "CSUB", "CMUL", "CDIV", "CREM"):
        y = val(pop(ctx), t); x = val(pop(ctx), t); checked = name[0] == "C"; op = name[1:] if checked else name
        err, r = None, 0
        if op in ("DIV", "REM") and y == 0: err = "DIV-ZERO"
        else:
            if op == "ADD": r = x + y
            elif op == "SUB": r = x - y
            elif op == "MUL": r = x * y
            elif op == "DIV": r = abs(x) // abs(y) * (1 if (x >= 0) == (y >= 0) else -1)
            elif op == "REM": q = abs(x) // abs(y) * (1 if (x >= 0) == (y >= 0) else -1); r = x - q * y
            if not in_range(r, t): err = arith_trap(r)
        if checked:
            codes = {"OVERFLOW": 0x0001, "UNDERFLOW": 0x0002, "DIV-ZERO": 0x0003}
            if err: ctx.out_cat, ctx.out_code = isa.CAT_PLATFORM, codes[err]; push(ctx, 0)
            else: ctx.out_cat, ctx.out_code = 0, 0; push(ctx, norm(r, t))
        else:
            if err: raise Trap(err)
            push(ctx, norm(r, t))
    elif name in ("NEG", "CNEG"):
        x = val(pop(ctx), t)
        if not in_range(-x, t):
            if name == "NEG": raise Trap("NEGATION")
            ctx.out_cat, ctx.out_code = isa.CAT_PLATFORM, 0x0001; push(ctx, 0)
        else:
            if name == "CNEG": ctx.out_cat, ctx.out_code = 0, 0
            push(ctx, norm(-x, t))
    elif name in ("WADD", "WSUB", "WMUL"):
        y = val(pop(ctx), t); x = val(pop(ctx), t)
        push(ctx, norm({"WADD": x + y, "WSUB": x - y, "WMUL": x * y}[name], t))
    elif name in ("AND", "OR", "XOR"):
        y = pop(ctx); x = pop(ctx); push(ctx, {"AND": x & y, "OR": x | y, "XOR": x ^ y}[name])
    elif name == "INV": push(ctx, norm(~pop(ctx), t))
    elif name in ("SHL", "SHR"):
        n = pop(ctx); x = pop(ctx); bits = 8 * WIDTH[TYPE_NAMES[t]]
        if n >= bits: raise Trap("SHIFT")
        push(ctx, norm(x << n if name == "SHL" else x >> n, t))
    elif name in ("EQ", "NE"): y = pop(ctx); x = pop(ctx); push(ctx, int((x == y) == (name == "EQ")))
    elif name in ("LT", "LE", "GT", "GE"):
        y = val(pop(ctx), t); x = val(pop(ctx), t)
        push(ctx, int({"LT": x < y, "LE": x <= y, "GT": x > y, "GE": x >= y}[name]))
    elif name == "BNOT": push(ctx, pop(ctx) ^ 1)
    elif name == "CCONVERT":
        x = val(pop(ctx), ops[0])
        if in_range(x, ops[1]): ctx.out_cat, ctx.out_code = 0, 0; push(ctx, norm(x, ops[1]))
        else: ctx.out_cat, ctx.out_code = isa.CAT_PLATFORM, 0x0004; push(ctx, 0)
    elif name == "TRUNC": push(ctx, norm(pop(ctx), t))
    elif name == "JMP": ctx_pc = next_pc + ops[0]
    elif name in ("JZ", "JNZ"):
        c = pop(ctx)
        if (c == 0) == (name == "JZ"): ctx_pc = next_pc + ops[0]
    elif name == "SWITCH": ctx_pc = next_pc + ops[pop(ctx)]
    elif name == "CALL":
        callee = function(ctx, ops[0]); code0, frame_size, argc, payload, operand_base = callee
        args = [pop(ctx) for _ in range(argc)][::-1]
        nfp = ctx.sp
        struct.pack_into("<II", ctx.stack, nfp, next_pc, ctx.fp)
        for i, c in enumerate(args): struct.pack_into("<I", ctx.stack, nfp + 8 + 4 * i, c)
        ctx.stack[nfp + 8 + 4 * argc:nfp + frame_size] = bytes(frame_size - 8 - 4 * argc)   # defaults (BC-25)
        ctx.fp = nfp; ctx.sp = nfp + operand_base; ctx_pc = code0
    elif name in ("RET", "RETV", "ERR", "FWD", "ERRRAISE"):
        value = None
        if name == "RETV": value = pop(ctx); cat, code = 0, 0
        elif name == "RET": cat, code = 0, 0
        elif name == "ERR": cat, code = ops[0], ops[1]
        elif name == "FWD": cat, code = ctx.out_cat, ctx.out_code
        else: c = pop(ctx); cat, code = c >> 16, c & 0xFFFF
        r = leave(ctx, cat, code, value)
        if r is not None: return r
        return None
    elif name == "JERR":
        if ctx.out_cat != 0: ctx_pc = next_pc + ops[0]
    elif name == "JERRIS":
        if ctx.out_cat == ops[0] and ctx.out_code == ops[1]: ctx_pc = next_pc + ops[2]
    elif name == "JERRCAT":
        if ctx.out_cat == ops[0]: ctx_pc = next_pc + ops[1]
    elif name == "ERRCODE": push(ctx, ctx.out_code)
    elif name == "ERRGET": push(ctx, (ctx.out_cat << 16) | ctx.out_code)
    elif name == "TXN.BEGIN": ctx.hal.txn_begin(); ctx.txn = 1
    elif name == "TXN.COMMIT": hal_call(ctx, ctx.hal.txn_commit); ctx.txn = 0
    elif name == "TXN.ABORT": ctx.hal.txn_abort(); ctx.txn = 0
    elif name == "NATIVE": natives.call(ctx, ops[0])
    else:
        raise Trap("VM")
    ctx.pc = ctx_pc
    return None

def block(ctx, name, ops):
    if name == "COPY":
        s = pop(ctx); d = pop(ctx); charge(ctx, blocks(ops[0])); copy(ctx, d, s, ops[0])
    elif name == "COPYV":
        m = pop(ctx); s = pop(ctx); n = pop(ctx); d = pop(ctx)
        if n != m: raise Trap("BOUNDS")
        size = n * ops[0]; charge(ctx, blocks(size)); atomic_check(ctx, d, size); copy(ctx, d, s, size)
    elif name == "FILL":
        c = pop(ctx); d = pop(ctx); w = WIDTH[TYPE_NAMES[ops[0]]]
        charge(ctx, blocks(w * ops[1])); write(ctx, d, (c & ((1 << (8 * w)) - 1)).to_bytes(w, "little") * ops[1])
    elif name == "FILLB":
        s = pop(ctx); d = pop(ctx); elem = read(ctx, s, ops[0])
        charge(ctx, blocks(ops[0] * ops[1])); write(ctx, d, elem * ops[1])
    elif name in ("ZERO", "WIPE"):
        d = pop(ctx); charge(ctx, blocks(ops[0])); write(ctx, d, bytes(ops[0]))
    elif name == "WIPEV":
        n = pop(ctx); d = pop(ctx); size = n * ops[0]; charge(ctx, blocks(size)); atomic_check(ctx, d, size)
        write(ctx, d, bytes(size))
    elif name == "EQUAL":
        m = pop(ctx); b = pop(ctx); n = pop(ctx); a = pop(ctx)
        charge(ctx, blocks(n * ops[0]) + blocks(m * ops[0]))
        x, y = read(ctx, a, n * ops[0]), read(ctx, b, m * ops[0])
        diff = 0
        for i in range(min(len(x), len(y))): diff |= x[i] ^ y[i]             # no early exit (PLT-31)
        push(ctx, int(n == m and diff == 0))
    elif name == "COMPARE":
        m = pop(ctx); b = pop(ctx); n = pop(ctx); a = pop(ctx); t = ops[0]; w = WIDTH[TYPE_NAMES[t]]
        charge(ctx, blocks(n * w) + blocks(m * w))
        x = [val(norm(int.from_bytes(read(ctx, a + i * w, w), "little"), t), t) for i in range(n)]
        y = [val(norm(int.from_bytes(read(ctx, b + i * w, w), "little"), t), t) for i in range(m)]
        push(ctx, norm(-1 if x < y else 1 if x > y else 0, isa.TYPES["i8"]))
    elif name == "ENCODE":
        c = pop(ctx); d = pop(ctx); w = WIDTH[TYPE_NAMES[ops[0]]]
        write(ctx, d, (c & ((1 << (8 * w)) - 1)).to_bytes(w, "big" if ops[1] == 0 else "little"))
    elif name == "DECODE":
        n = pop(ctx); a = pop(ctx); w = WIDTH[TYPE_NAMES[ops[0]]]
        if n != w: raise Trap("BOUNDS")
        push(ctx, norm(int.from_bytes(read(ctx, a, w), "big" if ops[1] == 0 else "little"), ops[0]))

def atomic_check(ctx, d, size):
    if split(d)[0] == PERSISTENT and size > ctx.hal.atomic_capacity(): raise Trap("TXN-CAPACITY")

# ------------------------------------------------------------------ entry points (VEX-45)
def cleanup_after_trap(ctx, natives):
    if ctx.atomic: ctx.hal.update_abort(); ctx.atomic = 0
    if ctx.hal.update is not None: ctx.hal.update_abort()
    if ctx.txn: ctx.hal.txn_abort(); ctx.txn = 0
    ctx.stack[:] = bytes(len(ctx.stack)); ctx.bounce[:] = bytes(BOUNCE)

def entry(ctx, findex, cells, natives):
    """Run one entry; returns ('ok', v) | ('err', cat, code) | ('trap', kind) | ('none',)."""
    try:
        return run(ctx, findex, cells, natives)
    except Trap as t:
        cleanup_after_trap(ctx, natives); return ("trap", t.kind)
    except PowerLoss:
        cleanup_after_trap(ctx, natives); ctx.state = NO_SESSION; ctx.session[:] = bytes(len(ctx.session))
        return ("none",)
