"""The CardLang debug adapter (TL1 step 5): the Debug Adapter Protocol over standard input and output.

It runs a scenario file (tools/harness/README.md) against an applet on the prototype VM (tools/vmproto/vm.py),
which executes exactly what the C VM does, and stops where asked:
- at breakpoints in `.card` files, through the image's line table (IMG-10, src/cardlang/bytecode/debuginfo.py);
- at breakpoints on scenario lines, before that step;
- when a trap happens, before the VM cleans up, so the frames are still there (exception filter `traps`);
- when an `expect` fails (exception filter `expect`).

Stepping is by statement: step over, step in and step out compare frame pointers. The call stack is read from the
frames' saved return addresses and frame pointers (BC-22), with the scenario step as the bottom frame. Variables
are the parameters and locals in scope, the globals, and the elements and fields of arrays, views and structs.

Launch arguments: {"scenario": path, "program": project directory or .card file (default: the scenario's
directory), "stopOnEntry": bool}. Run with: uv run python -I tools/dap/cardlang_dap.py
"""
import sys, os, struct, pathlib, threading, traceback
HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
for d in (TOOLS / "lsp", TOOLS / "vmproto", TOOLS / "harness", TOOLS):
    if str(d) not in sys.path: sys.path.insert(0, str(d))
import jsonrpc, vm
from cardlang.bytecode import debuginfo, isa

THREAD = 1
REGION = {"STACK": vm.STACK, "PERSISTENT": vm.PERSISTENT, "SESSION": vm.SESSION, "CONST": vm.CONST}

class Abort(Exception):
    """Raised in the runner thread to end the session."""

def addr(region, off): return (region << 29) | off

class Adapter:
    def __init__(self, channel):
        self.ch = channel; self.seq = 1
        self.breakpoints = {}          # normalised .card path -> {line: [code offsets]}
        self.code_breaks = set()       # code offsets
        self.scenario_breaks = set()   # scenario line numbers
        self.filters = {"traps", "expect"}
        self.resume = threading.Event(); self.mode = "run"; self.start_fp = 0; self.skip_pc = None
        self.paused = False; self.aborted = False; self.scenario_line = 0; self.where = None
        self.refs = {}; self.card = None; self.info = None; self.args = {}
        self.bp_ids = {}               # (path, requested line) -> breakpoint id, so later resolution can update it

    # ---------------------------------------------------------------- protocol
    def send(self, m):
        m["seq"] = self.seq; self.seq += 1; self.ch.write(m)

    def respond(self, req, body=None, ok=True, message=None):
        m = {"type": "response", "request_seq": req["seq"], "command": req["command"], "success": ok}
        if body is not None: m["body"] = body
        if message: m["message"] = message
        self.send(m)

    def event(self, name, body=None):
        m = {"type": "event", "event": name}
        if body is not None: m["body"] = body
        self.send(m)

    def out(self, text, category="console"):
        self.event("output", {"category": category, "output": text + "\n"})

    # ---------------------------------------------------------------- requests
    def handle(self, req):
        cmd, a = req.get("command"), req.get("arguments") or {}
        if cmd == "initialize":
            self.respond(req, {"supportsConfigurationDoneRequest": True, "supportsEvaluateForHovers": True,
                               "supportsTerminateRequest": True,
                               "exceptionBreakpointFilters": [
                                   {"filter": "traps", "label": "Traps", "default": True},
                                   {"filter": "expect", "label": "Failed expectations", "default": True}]})
            self.event("initialized")
        elif cmd == "launch": self.launch(req, a)
        elif cmd == "setBreakpoints": self.respond(req, {"breakpoints": self.set_breakpoints(a)})
        elif cmd == "setExceptionBreakpoints": self.filters = set(a.get("filters", [])); self.respond(req, {})
        elif cmd == "configurationDone":
            self.respond(req); threading.Thread(target=self.run, daemon=True).start()
        elif cmd == "threads": self.respond(req, {"threads": [{"id": THREAD, "name": "applet"}]})
        elif cmd == "stackTrace":
            frames = self.frames(); self.respond(req, {"stackFrames": frames, "totalFrames": len(frames)})
        elif cmd == "scopes": self.respond(req, {"scopes": self.scopes(a["frameId"])})
        elif cmd == "variables": self.respond(req, {"variables": self.variables(a["variablesReference"])})
        elif cmd == "evaluate": self.evaluate(req, a)
        elif cmd in ("continue", "next", "stepIn", "stepOut"):
            self.go({"continue": "run", "next": "over", "stepIn": "in", "stepOut": "out"}[cmd])
            self.respond(req, {"allThreadsContinued": True} if cmd == "continue" else None)
        elif cmd == "pause": self.mode = "pause"; self.respond(req)
        elif cmd in ("disconnect", "terminate"):
            self.aborted = True; self.resume.set(); self.respond(req)
            if cmd == "disconnect": self.finish(0)
            else: self.event("terminated")
        else: self.respond(req, ok=False, message=f"not supported: {cmd}")

    def finish(self, status):
        sys.stdout.flush(); sys.stderr.flush(); os._exit(status)

    # ---------------------------------------------------------------- launching
    def launch(self, req, a):
        import clc, backends
        from cardlang.front import diagnose
        self.args = a
        try:
            self.scenario = pathlib.Path(a["scenario"]).resolve()
            given = a.get("program") or str(self.scenario.parent)
            paths = given if isinstance(given, list) else [given]
            prog = clc.Program([str(pathlib.Path(p).resolve()) for p in paths])
            prog.files = [f.resolve() for f in prog.files]
            ds = diagnose.check(prog.files, prog.binding, prog.kind)
            if ds:
                for d in ds: self.out(diagnose.format_diagnostic(d), "stderr")
                self.respond(req, ok=False, message="the program does not compile: " + diagnose.format_diagnostic(ds[0])); return
            self.card = backends.build("vmproto", prog.files, prog.binding)
            self.info = debuginfo.DebugInfo.of(self.card.image)
            self.row_offsets = {off for off, _, _ in self.info.lines}
            self.program = prog
        except Exception as e:
            self.respond(req, ok=False, message=f"launch failed: {e}"); self.out(traceback.format_exc(), "stderr"); return
        self.mode = "entry" if a.get("stopOnEntry") else "run"
        self.respond(req)
        for path in list(self.breakpoints):                     # set before the program was built: verify them now
            for bp in self.resolve(path): self.event("breakpoint", {"reason": "changed", "breakpoint": bp})

    def set_breakpoints(self, a):
        path = a["source"].get("path", ""); lines = [b["line"] for b in a.get("breakpoints", [])]
        key = os.path.normcase(os.path.abspath(path))
        if key.endswith((".scenario", "scenario.txt")) or key.endswith(".txt"):
            self.scenario_breaks = set(lines)
            return [{"verified": True, "line": l} for l in lines]
        for offs in self.breakpoints.get(key, {}).values(): self.code_breaks -= set(offs)   # the file's old ones
        self.breakpoints[key] = {l: [] for l in lines}
        return self.resolve(key)

    def resolve(self, key):
        """Map a file's breakpoint lines to code offsets: a line with no statement moves to the next one that has."""
        result = []
        self.code_breaks -= {o for offs in self.breakpoints[key].values() for o in offs}
        new = {}
        for line in list(self.breakpoints[key]):
            if self.info is None:
                bid = self.bp_ids.setdefault((key, line), len(self.bp_ids) + 1)
                result.append({"id": bid, "verified": False, "line": line, "message": "the program is not built yet"})
                new[line] = []; continue
            actual, offs = line, []
            for l in range(line, line + 20):
                offs = self.info.offsets(key, l)
                if offs: actual = l; break
            new[line] = offs; self.code_breaks |= set(offs)
            bid = self.bp_ids.setdefault((key, line), len(self.bp_ids) + 1)
            result.append({"id": bid, "verified": True, "line": actual} if offs else
                          {"id": bid, "verified": False, "line": line, "message": "no statement here"})
        self.breakpoints[key] = new
        return result

    # ---------------------------------------------------------------- running
    def run(self):
        import scenario
        orig_step, orig_cleanup = vm.step, vm.cleanup_after_trap
        def step(ctx, name, ops, next_pc, natives):
            self.check(ctx); return orig_step(ctx, name, ops, next_pc, natives)
        def cleanup(ctx, natives):
            if "traps" in self.filters:
                import sys as _s
                kind = _s.exc_info()[1].kind if isinstance(_s.exc_info()[1], vm.Trap) else "trap"
                self.stop("exception", ctx, f"trap {kind}")
            return orig_cleanup(ctx, natives)
        vm.step, vm.cleanup_after_trap = step, cleanup
        failed = None
        def before(lineno, step_name, words):
            self.scenario_line = lineno; self.where = None
            if lineno in self.scenario_breaks or self.mode == "entry": self.stop("breakpoint" if self.mode != "entry" else "entry")
        def trace(lineno, step_name, words, outcome):
            import clc
            if step_name == "expect":
                _, want, got = outcome
                self.out(f"{self.scenario.name}:{lineno}: {'ok  ' if want == got else 'FAIL'} expect {' '.join(words)}"
                         + ("" if want == got else f"  (got {got})"))
                if want != got and "expect" in self.filters: self.stop("exception", None, f"expect failed: got {got}")
            else:
                res = clc.describe(outcome)
                if outcome and outcome[0] == "trap" and self.card.trap_position():
                    f, l = self.card.trap_position(); res += f" at {pathlib.Path(f).name}:{l}"
                self.out(f"{self.scenario.name}:{lineno}: {step_name} {' '.join(words)[:60]}" + (f"  -> {res}" if res else ""))
        try:
            failed = scenario.run_scenario(self.card, self.scenario.read_text(encoding="utf-8"), trace, before)
            self.out(f"{self.scenario.name}: " + ("passed" if failed is None else "FAILED, " + failed) + " (vmproto)")
            status = 0 if failed is None else 1
        except Abort:
            status = 1
        except Exception:
            self.out(traceback.format_exc(), "stderr"); status = 1
        finally:
            vm.step, vm.cleanup_after_trap = orig_step, orig_cleanup
        self.event("exited", {"exitCode": status}); self.event("terminated")

    def check(self, ctx):
        """Before each instruction: stop if a breakpoint, a step or a pause asks for it."""
        pc = ctx.pc
        if self.skip_pc is not None:
            if pc == self.skip_pc and ctx.fp == self.start_fp: return          # the instruction we stopped at
            self.skip_pc = None
        at_row = pc in self.row_offsets
        if pc in self.code_breaks: self.stop("breakpoint", ctx); return
        m = self.mode
        if m == "pause" or m == "entry": self.stop("pause" if m == "pause" else "entry", ctx); return
        if not at_row: return
        if m == "in" or (m == "over" and ctx.fp <= self.start_fp) or (m == "out" and ctx.fp < self.start_fp):
            self.stop("step", ctx)

    def stop(self, reason, ctx=None, text=None):
        self.where = (ctx.pc, ctx.fp) if ctx is not None else None
        self.ctx = ctx if ctx is not None else self.card.ctx
        self.refs = {}; self.paused = True; self.resume.clear()
        body = {"reason": reason, "threadId": THREAD, "allThreadsStopped": True}
        if text: body["text"] = text; body["description"] = text
        self.event("stopped", body)
        self.resume.wait()
        self.paused = False
        if self.aborted: raise Abort()

    def go(self, mode):
        self.mode = mode
        if self.where is not None: self.start_fp = self.where[1]; self.skip_pc = self.where[0]
        else: self.start_fp = 1 << 30; self.skip_pc = None                    # from a scenario step: any frame
        self.resume.set()

    # ---------------------------------------------------------------- the stack
    def frames(self):
        out = []
        if self.where is not None:
            ctx = self.ctx; pc, fp = self.where; k = 0
            while True:
                fn = self.info.function_at(pc)
                pos = self.info.position(pc if k == 0 else max(pc - 1, 0))
                frame = {"id": k, "name": self.info.functions[fn] if fn < len(self.info.functions) else f"f{fn}",
                         "line": pos[1] if pos else 0, "column": 1}
                if pos: frame["source"] = {"name": pathlib.Path(pos[0]).name, "path": str(pathlib.Path(pos[0]).resolve())}
                out.append(frame); self.frame_state = getattr(self, "frame_state", {}); self.frame_state[k] = (fn, pc, fp)
                ret_pc, caller_fp = struct.unpack_from("<II", ctx.stack, fp)
                if ret_pc == vm.RET_NONE or k > 64: break
                pc, fp = ret_pc, caller_fp; k += 1
        out.append({"id": 1000, "name": f"scenario step", "line": self.scenario_line, "column": 1,
                    "source": {"name": self.scenario.name, "path": str(self.scenario)}})
        return out

    def scopes(self, frame_id):
        if frame_id == 1000 or frame_id not in getattr(self, "frame_state", {}):
            return [{"name": "Globals", "variablesReference": self.ref(("globals",)), "expensive": False}]
        return [{"name": "Locals", "variablesReference": self.ref(("locals", frame_id)), "expensive": False},
                {"name": "Globals", "variablesReference": self.ref(("globals",)), "expensive": False}]

    def ref(self, what):
        n = len(self.refs) + 1; self.refs[n] = what; return n

    # ---------------------------------------------------------------- values
    def size(self, t):
        ty = self.info.types[t]
        if ty[0] == "int": return isa.WIDTH[ty[1]]
        if ty[0] == "bool": return 1
        if ty[0] == "enum": return 1 if len(ty[2]) <= 256 else 2
        if ty[0] == "struct": return sum(self.size(ft) for _, ft, _ in ty[2])
        if ty[0] == "array": return ty[2] * self.size(ty[1])
        return 8

    def value(self, name, a, t, length=None):
        """A DAP variable for the value of type t at address a (or the view a, length)."""
        ty = self.info.types[t]; tn = self.info.type_name(t)
        v = {"name": name, "type": tn, "variablesReference": 0}
        try:
            if ty[0] == "int":
                x = vm.load_scalar(self.ctx, a, isa.TYPES[ty[1]])
                if ty[1].startswith("i") and x >= 1 << (8 * isa.WIDTH[ty[1]] - 1): x -= 1 << (8 * isa.WIDTH[ty[1]])
                v["value"] = str(x) if abs(x) < 10 else f"{x} (0x{x & 0xFFFFFFFF:x})"
            elif ty[0] == "bool": v["value"] = "true" if vm.read(self.ctx, a, 1)[0] else "false"
            elif ty[0] == "enum":
                o = int.from_bytes(vm.read(self.ctx, a, self.size(t)), "little")
                v["value"] = f"{ty[1]}.{ty[2][o]}" if o < len(ty[2]) else f"{ty[1]}({o})"
            elif ty[0] == "struct":
                v["value"] = f"{ty[1]} {{…}}"; v["variablesReference"] = self.ref(("struct", a, t))
            else:
                elem = ty[1]; n = ty[2] if ty[0] == "array" else length
                es = self.size(elem); shown = vm.read(self.ctx, a, min(n, 16) * es) if es == 1 else b""
                preview = " ".join(f"{b:02x}" for b in shown) + (" …" if n > 16 else "") if es == 1 else ""
                v["value"] = f"[{n}] {preview}".rstrip(); v["indexedVariables"] = n
                v["variablesReference"] = self.ref(("elements", a, elem, n))
        except Exception as e:
            v["value"] = f"<unreadable: {e}>"
        return v

    def variables(self, ref):
        what = self.refs.get(ref)
        if what is None: return []
        if what[0] == "locals":
            fn, pc, fp = self.frame_state[what[1]]
            out = []
            for var in self.info.variables(fn, pc):
                if not var["param"] and not (var["start"] <= pc < var["end"]): continue
                cell = addr(vm.STACK, fp + var["offset"])
                if var["kind"] == "frame": out.append(self.value(var["name"], cell, var["type"]))
                elif var["kind"] == "ref":
                    out.append(self.value(var["name"], vm.load_scalar(self.ctx, cell, isa.TYPES["u32"]), var["type"]))
                elif var["kind"] == "view":
                    base = vm.load_scalar(self.ctx, cell, isa.TYPES["u32"]); n = vm.load_scalar(self.ctx, cell + 4, isa.TYPES["u32"])
                    out.append(self.value(var["name"], base, var["type"], n))
                else:
                    e = vm.load_scalar(self.ctx, cell, isa.TYPES["u32"])
                    out.append({"name": var["name"], "value": f"error 0x{e:08x}", "type": "error", "variablesReference": 0})
            return out
        if what[0] == "globals":
            out = []
            for g in self.info.globals:
                if g["kind"] == "const-scalar":
                    ty = self.info.types[g["type"]]
                    val = f"{ty[1]}.{ty[2][g['offset']]}" if ty[0] == "enum" else ("true" if g["offset"] else "false") if ty[0] == "bool" else str(g["offset"])
                    out.append({"name": g["name"], "value": val, "type": self.info.type_name(g["type"]), "variablesReference": 0})
                else:
                    region = {"persistent": vm.PERSISTENT, "session": vm.SESSION, "const": vm.CONST}[g["kind"]]
                    v = self.value(g["name"], addr(region, g["offset"]), g["type"])
                    v["presentationHint"] = {"attributes": ["readOnly"]} if g["kind"] == "const" else {}
                    out.append(v)
            return out
        if what[0] == "struct":
            _, a, t = what; ty = self.info.types[t]
            return [self.value(f, a + off, ft) for f, ft, off in ty[2]]
        if what[0] == "elements":
            _, a, elem, n = what; es = self.size(elem)
            return [self.value(f"[{i}]", a + i * es, elem) for i in range(min(n, 4096))]
        return []

    def evaluate(self, req, a):
        """Hover and watch: a variable's name, looked up in the frame, then the globals."""
        name = a.get("expression", "").strip(); fid = a.get("frameId")
        pools = []
        if fid is not None and fid in getattr(self, "frame_state", {}): pools.append(self.variables(self.ref(("locals", fid))))
        pools.append(self.variables(self.ref(("globals",))))
        for pool in pools:
            for v in pool:
                if v["name"] == name:
                    self.respond(req, {"result": v["value"], "type": v.get("type"), "variablesReference": v["variablesReference"]}); return
        self.respond(req, ok=False, message=f"not a variable here: {name}")

    # ---------------------------------------------------------------- main loop
    def serve(self):
        q = jsonrpc.reader_thread(self.ch)
        while True:
            m = q.get()
            if m is None: self.finish(0)
            if m.get("type") != "request": continue
            try: self.handle(m)
            except Exception as e:
                self.respond(m, ok=False, message=f"{type(e).__name__}: {e}"); self.out(traceback.format_exc(), "stderr")

if __name__ == "__main__":
    Adapter(jsonrpc.Channel()).serve()
