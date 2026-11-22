"""A scripted session with the CardLang debug adapter (TL1 step 5), run by tests/run_checks.py.

Starts the debug adapter, cardlang.dap.adapter, as VS Code would, and debugs two runtime tests:
- run-012 (the wallet): a breakpoint in `credit` (line 57) is hit on the scenario's credit command (line 11); the
  stack is credit <- process <- the scenario step; `amount` is 1000 and the globals are readable; step over
  reaches line 58 with `updated` in scope; step in reaches the `Ok` arm (line 60); step out returns to `process`;
  with the breakpoint removed, the scenario runs to its end and passes.
- run-001 (integer traps): the overflow stops as an exception on line 16, before the VM cleans up, so `a` is
  still 255; continuing finishes the scenario.
Usage: uv run python -I tests/dap_check.py .
"""
import sys, json, pathlib, subprocess, queue, time
HERE = pathlib.Path(__file__).resolve().parent
from cardlang import jsonrpc
from cardlang import layout

class Client:
    def __init__(self, repo):
        self.p = subprocess.Popen([sys.executable, "-I", "-m", "cardlang.dap.adapter"], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=repo)
        self.ch = jsonrpc.Channel(self.p.stdout, self.p.stdin); self.q = jsonrpc.reader_thread(self.ch)
        self.seq = 1; self.events = []; self.output = []
    def _next(self, timeout=60):
        m = self.q.get(timeout=timeout)
        if m and m.get("type") == "event":
            if m["event"] == "output": self.output.append(m["body"]["output"])
            self.events.append(m)
        return m
    def request(self, command, arguments=None):
        seq = self.seq; self.seq += 1
        self.ch.write({"seq": seq, "type": "request", "command": command, "arguments": arguments or {}})
        while True:
            m = self._next()
            if m and m.get("type") == "response" and m["request_seq"] == seq: return m
    def wait(self, name, timeout=60):
        for i, e in enumerate(self.events):
            if e["event"] == name: return self.events.pop(i)
        end = time.time() + timeout
        while time.time() < end:
            m = self._next(max(0.1, end - time.time()))
            if m and m.get("type") == "event" and m["event"] == name: self.events.remove(m); return m
        raise TimeoutError(name)
    def stack(self): return self.request("stackTrace", {"threadId": 1})["body"]["stackFrames"]
    def locals(self, frame=0):
        scopes = self.request("scopes", {"frameId": frame})["body"]["scopes"]
        out = {}
        for s in scopes:
            for v in self.request("variables", {"variablesReference": s["variablesReference"]})["body"]["variables"]:
                out[(s["name"], v["name"])] = v["value"]
        return out
    def close(self):
        self.request("disconnect", {})
        try: self.p.wait(timeout=10)
        except subprocess.TimeoutExpired: self.p.kill()

def main(repo):
    ok = True
    def check(name, passed, detail=""):
        nonlocal ok
        ok &= bool(passed); print("PASS" if passed else "FAIL", name, "|", str(detail)[:200])
    run = layout.at(repo).runtime / "run-012-wallet-application"; program = run / "program.card"
    c = Client(repo)
    r = c.request("initialize", {"adapterID": "cardlang", "linesStartAt1": True, "columnsStartAt1": True})
    check("initialize", r["success"] and r["body"].get("supportsConfigurationDoneRequest"), r["body"])
    c.wait("initialized")
    r = c.request("launch", {"scenario": str(run / "scenario.txt"), "program": str(run)}); check("launch", r["success"], r.get("message"))
    r = c.request("setBreakpoints", {"source": {"path": str(program)}, "breakpoints": [{"line": 57}]})
    bps = r["body"]["breakpoints"]; check("the breakpoint is verified", bps and bps[0]["verified"] and bps[0]["line"] == 57, bps)
    c.request("setExceptionBreakpoints", {"filters": ["traps", "expect"]})
    c.request("configurationDone")
    e = c.wait("stopped"); check("stopped at the breakpoint", e["body"]["reason"] == "breakpoint", e["body"])
    st = c.stack()
    check("the stack: credit, process, the scenario step",
          [f["name"] for f in st] == ["credit", "process", "scenario step"] and st[0]["line"] == 57 and st[-1]["line"] == 11,
          [(f["name"], f["line"]) for f in st])
    v = c.locals()
    check("parameters and globals", v.get(("Locals", "amount")) == "1000 (0x3e8)" and v.get(("Globals", "balance")) == "0"
          and v.get(("Globals", "authenticated")) == "true" and ("Locals", "updated") not in v, v)
    r = c.request("evaluate", {"expression": "amount", "frameId": 0, "context": "hover"})
    check("hover evaluates a name", r["success"] and r["body"]["result"] == "1000 (0x3e8)", r.get("body"))
    c.request("next", {"threadId": 1}); c.wait("stopped"); st = c.stack(); v = c.locals()
    check("step over: the next statement, with its local", st[0]["line"] == 58 and v.get(("Locals", "updated")) == "0", (st[0]["line"], v))
    c.request("stepIn", {"threadId": 1}); c.wait("stopped"); st = c.stack()
    check("step in: the Ok arm", st[0]["line"] == 60 and st[0]["name"] == "credit", (st[0]["name"], st[0]["line"]))
    c.request("stepOut", {"threadId": 1}); c.wait("stopped"); st = c.stack()
    check("step out: back in process", st[0]["name"] == "process", (st[0]["name"], st[0]["line"]))
    c.request("setBreakpoints", {"source": {"path": str(program)}, "breakpoints": []})
    c.request("continue", {"threadId": 1})
    e = c.wait("exited"); c.wait("terminated")
    check("runs to the end and passes", e["body"]["exitCode"] == 0 and any("passed" in o for o in c.output), c.output[-1:])
    c.close()
    run = layout.at(repo).runtime / "run-001-integer-traps"
    c = Client(repo)
    c.request("initialize", {"adapterID": "cardlang"}); c.wait("initialized")
    r = c.request("setBreakpoints", {"source": {"path": str(run / "program.card")}, "breakpoints": [{"line": 15}]})
    early = r["body"]["breakpoints"][0]
    c.request("launch", {"scenario": str(run / "scenario.txt")})
    e = c.wait("breakpoint")
    check("a breakpoint set before launch is verified after the build", not early["verified"] and e["body"]["breakpoint"]["verified"]
          and e["body"]["breakpoint"]["id"] == early["id"] and e["body"]["breakpoint"]["line"] == 15, (early, e["body"]))
    c.request("setBreakpoints", {"source": {"path": str(run / "program.card")}, "breakpoints": []})
    c.request("setExceptionBreakpoints", {"filters": ["traps"]}); c.request("configurationDone")
    e = c.wait("stopped"); st = c.stack(); v = c.locals()
    check("a trap stops before the cleanup", e["body"]["reason"] == "exception" and e["body"].get("text") == "trap OVERFLOW"
          and st[0]["line"] == 16 and v.get(("Locals", "a")) == "255 (0xff)", (e["body"], st[0]["line"], v.get(("Locals", "a"))))
    c.request("setExceptionBreakpoints", {"filters": []}); c.request("continue", {"threadId": 1})
    e = c.wait("exited"); check("and the scenario still passes", e["body"]["exitCode"] == 0, c.output[-1:])
    c.close()
    app = layout.at(repo).examples / "fido2"
    c = Client(repo)
    c.request("initialize", {"adapterID": "cardlang"}); c.wait("initialized")
    c.request("launch", {"scenario": str(app / "getinfo.scenario")})          # the program: the scenario's project
    r = c.request("setBreakpoints", {"source": {"path": str(app / "ctap.card")}, "breakpoints": [{"line": 30}]})
    c.request("setExceptionBreakpoints", {"filters": []}); c.request("configurationDone")
    e = c.wait("stopped"); st = c.stack()
    check("an applet: a breakpoint in the FIDO2 getInfo handler", r["body"]["breakpoints"][0]["verified"] and st[0]["name"] == "get_info"
          and st[0]["line"] == 30 and st[-1]["line"] == 6, [(f["name"], f["line"]) for f in st])
    c.request("setBreakpoints", {"source": {"path": str(app / "ctap.card")}, "breakpoints": []}); c.request("continue", {"threadId": 1})
    e = c.wait("exited"); check("and its scenario passes", e["body"]["exitCode"] == 0, c.output[-1:])
    c.close()
    print("ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(pathlib.Path(sys.argv[1]).resolve()) else 1)
