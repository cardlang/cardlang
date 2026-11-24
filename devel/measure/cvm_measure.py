"""Measurements of the C VM (VM7 step 5; plans_and_notes/VM7-measurements.md). Prints a JSON document.

Run with the project's uv environment, from the repository root, after building the C VM (vm/c/README.md):
    CARDLANG_CROSS_CC=<a clang that accepts --target> uv run python -I devel/measure/cvm_measure.py > measurements.json

CARDLANG_CROSS_CC names the cross compiler; its folder must also hold llvm-size, llvm-nm and llvm-objdump (any LLVM
release, or llvm-mingw, has them). Without it, only the host's context sizes and the speed are measured.

1. The VM's context, sizeof(cl_vm): on the host, from the built library, and for 32-bit targets, from a probe
   cross-compiled for the Cortex-M targets.
2. Code size of vm.c and natives.c, by section kind: the host build as built (with the test-only catalog), and
   cross-compiled at -Os for Cortex-M4 and Cortex-M0+, without it. The cross builds are
   freestanding; a shim declares the five <string.h> functions the VM uses. Mutable data and bss must be zero (V-8).
3. The C stack: clang's -fstack-usage frames for Cortex-M4, and the longest call path from each entry point through
   the VM's own functions, read from the relocations of the call instructions. HAL functions count as leaves: their
   stack is the port's. The call graph must have no cycle (no recursion, VEX-19).
4. Speed, for scale only: vm/c/test/bench.card, a loop without natives, so the budget used is the number of
   instructions executed. The same program on the prototype VM gives the ratio.
"""
import os, sys, re, json, time, shutil, pathlib, subprocess, collections

from cardlang import layout
from cardlang.harness import cvm_backend
HERE = layout.at().vm_c            # the C VM, which this script measures
REPO = layout.at().root

SOURCES = ["src/vm.c", "src/natives.c"]
TARGETS = {
    "cortex-m4": ["--target=thumbv7em-none-eabi", "-mcpu=cortex-m4", "-mthumb"],
    "cortex-m0plus": ["--target=thumbv6m-none-eabi", "-mcpu=cortex-m0plus", "-mthumb"],
}
SHIM = """#ifndef CL_SHIM_STRING_H
#define CL_SHIM_STRING_H
#include <stddef.h>
void *memcpy(void *d, const void *s, size_t n);
void *memmove(void *d, const void *s, size_t n);
void *memset(void *d, int c, size_t n);
int memcmp(const void *a, const void *b, size_t n);
size_t strlen(const char *s);
#endif
"""
PROBE = """#include "cl_vm.h"
char cl_vm_probe[sizeof(cl_vm)] = {1};
char cl_op_probe[sizeof(cl_op)] = {1};
char cl_config_probe[sizeof(cl_config)] = {1};
"""
ENTRIES = ["cl_vm_load", "cl_vm_install", "cl_vm_session_start", "cl_vm_session_end", "cl_vm_select", "cl_vm_command"]
BENCH = HERE / "test" / "bench.card"
ROUNDS = 20000

def tool(bindir, name):
    """An LLVM tool beside the cross compiler, with or without .exe."""
    for candidate in (bindir / name, bindir / (name + ".exe")):
        if candidate.exists(): return str(candidate)
    raise SystemExit(f"cvm_measure: {name} not found in {bindir}, beside CARDLANG_CROSS_CC")

def sections(root, obj):
    """Bytes of code, read-only data, mutable data and bss in an object file (llvm-size, System V format)."""
    out = subprocess.run([tool(root, "llvm-size"), "-A", str(obj)], capture_output=True, text=True, check=True).stdout
    kinds = collections.Counter()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 2 or not parts[1].isdigit(): continue
        name, n = parts[0], int(parts[1])
        if name.startswith(".text"): kinds["code"] += n
        elif name.startswith((".rodata", ".rdata")): kinds["rodata"] += n
        elif name.startswith(".data"): kinds["data"] += n
        elif name.startswith(".bss"): kinds["bss"] += n
    return {k: kinds[k] for k in ("code", "rodata", "data", "bss")}

def stack_usage(su):
    frames = {}
    for line in su.read_text(encoding="utf-8").splitlines():
        loc, size, kind = line.split("\t")
        frames[loc.rsplit(":", 1)[1]] = (int(size), kind)
    return frames

def calls(root, obj):
    """Each function's callees, from the relocations of its call and tail-call instructions."""
    out = subprocess.run([tool(root, "llvm-objdump"), "-dr", str(obj)], capture_output=True, text=True, check=True).stdout
    graph, current = collections.defaultdict(set), None
    for line in out.splitlines():
        m = re.match(r"^[0-9a-f]+ <([^>]+)>:", line)
        if m: current = m.group(1); graph[current]; continue
        m = re.search(r"R_ARM_THM_(?:CALL|JUMP24|JUMP11)\s+(\S+)", line)
        if m and current: graph[current].add(m.group(1).removeprefix(".text."))
    return graph

def longest(graph, frames, entry):
    """The deepest stack from entry, and its path. Callees outside the VM count as 0; a cycle is an error."""
    memo, active = {}, set()
    def go(f):
        if f in memo: return memo[f]
        if f in active: raise SystemExit(f"recursion in the call graph through {f} (VEX-19)")
        active.add(f)
        best = (0, [])
        for g in graph.get(f, ()):
            if g in frames or g in graph:
                d = go(g)
                if d[0] > best[0]: best = d
        active.discard(f)
        memo[f] = (frames.get(f, (0, ""))[0] + best[0], [f] + best[1])
        return memo[f]
    return go(entry)

def cross(root):
    result = {}
    inc = HERE / "include"
    for name, flags in TARGETS.items():
        d = cvm_backend.build_tree() / "measure" / name
        (d / "shim").mkdir(parents=True, exist_ok=True)
        (d / "shim" / "string.h").write_text(SHIM, encoding="utf-8")
        (d / "probe.c").write_text(PROBE, encoding="utf-8")
        common = flags + ["-std=c11", "-Os", "-ffreestanding", "-fno-common", "-ffunction-sections", "-fdata-sections",
                          "-fstack-usage", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "-I", str(inc), "-I", str(d / "shim"), "-c"]
        files, frames, graph = {}, {}, collections.defaultdict(set)
        for src in SOURCES + [str(d / "probe.c")]:
            path = pathlib.Path(src) if pathlib.Path(src).is_absolute() else HERE / src
            obj = d / (path.stem + ".o")
            subprocess.run([str(CROSS_CC)] + common + [str(path), "-o", str(obj)], check=True)
            if path.stem == "probe":
                nm = subprocess.run([tool(root, "llvm-nm"), "-S", str(obj)], capture_output=True, text=True, check=True).stdout
                sizes = {l.split()[3].removesuffix("_probe"): int(l.split()[1], 16) for l in nm.splitlines() if len(l.split()) == 4}
                continue
            files[path.name] = sections(root, obj)
            frames.update(stack_usage(obj.with_suffix(".su")))
            for f, gs in calls(root, obj).items(): graph[f] |= gs
        dynamic = [f for f, (_, kind) in frames.items() if kind != "static"]
        deepest = {e: longest(graph, frames, e) for e in ENTRIES}
        external = sorted({g for gs in graph.values() for g in gs if g not in frames and g not in graph})
        biggest = sorted(((n, f) for f, (n, _) in frames.items()), reverse=True)[:8]
        result[name] = {"sizes": sizes, "files": files,
                        "total": {k: sum(f[k] for f in files.values()) for k in ("code", "rodata", "data", "bss")},
                        "stack": {"deepest": {e: {"bytes": b, "path": p} for e, (b, p) in deepest.items()},
                                  "largest_frames": [{"function": f, "bytes": n} for n, f in biggest],
                                  "dynamic_frames": dynamic, "leaves_outside_vm": external}}
    return result

def host(root):
    """The host build, as built: its context sizes and, with the LLVM tools, the code of its object files."""
    out = {"sizeof_cl_vm": cvm_backend.context_size(), "op_context": cvm_backend.op_context_size()}
    if root is None: return out
    objects = {}
    for s in SOURCES:                    # wherever the generator put them: vm.obj, vm.c.obj or vm.c.o
        name = pathlib.Path(s).name
        found = [f for f in cvm_backend.build_tree().rglob("*") if f.name in (name + ".obj", name + ".o",
                 pathlib.Path(s).stem + ".obj") and "cardlang_vm" in str(f)]
        if not found: raise SystemExit(f"cvm_measure: the object file of {s} is not in {cvm_backend.build_tree()}")
        objects[s] = sections(root, found[0])
    out["files"] = objects
    out["total"] = {k: sum(f[k] for f in objects.values()) for k in ("code", "rodata", "data", "bss")}
    return out

def speed():
    from cardlang.harness import backends, cvm_backend
    request = [ROUNDS >> 8, ROUNDS & 0xFF]
    out = {}
    card = backends.build("pyvm", [BENCH]); card.install(); card.session_start()
    t = time.perf_counter(); ref = card.command(request, 8); dt = time.perf_counter() - t
    n = card.ctx.budget_cfg - card.ctx.budget
    out["vmproto"] = {"instructions": n, "seconds": dt, "per_second": n / dt}
    c = cvm_backend.CvmCard([BENCH], budget=10_000_000); c.install(); c.session_start()
    assert c.command(request, 8) == ref, "the C VM computes a different result"
    assert c.budget_used() == n, "the C VM executes a different number of instructions"
    runs = 50; t = time.perf_counter()
    for _ in range(runs): c.command(request, 8)
    dt = time.perf_counter() - t
    out["cvm"] = {"instructions": n, "seconds": dt / runs, "per_second": n * runs / dt}
    return out

CROSS_CC = None

if __name__ == "__main__":
    named = os.environ.get("CARDLANG_CROSS_CC")
    if named:
        CROSS_CC = pathlib.Path(shutil.which(named) or named)
        if not CROSS_CC.exists(): sys.exit(f"cvm_measure: CARDLANG_CROSS_CC names {named}, which is not found")
    bindir = CROSS_CC.parent if CROSS_CC else None
    if bindir is None:
        print("cvm_measure: CARDLANG_CROSS_CC is not set; measuring the host's context sizes and the speed only",
              file=sys.stderr)
    report = {"host": host(bindir), "speed": speed()}
    if bindir is not None: report["cross"] = cross(bindir)
    print(json.dumps(report, indent=1))
