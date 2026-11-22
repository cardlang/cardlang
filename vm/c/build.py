"""Configure and build the C VM with both toolchains: MSVC, and a MinGW-w64 clang.

Run with the project's uv environment, from the repository root:
    uv run python -I vm/c/build.py [msvc | clang | all] [--clean]

- MSVC is found with vswhere, and its environment is taken from vcvars64.bat. CMake and Ninja are Visual Studio's.
- clang is `x86_64-w64-mingw32-clang` from the PATH, or the compiler named by CC. It must target 64-bit Windows,
  because the harness loads the VM's library into 64-bit Python. llvm-mingw provides it: put its `bin` folder on
  the PATH. CMake and Ninja come from the PATH too, and no Visual Studio is needed.
- Build trees go to vm/c/build/<toolchain>, which git ignores.
"""
import os, sys, json, shutil, pathlib, subprocess

HERE = pathlib.Path(__file__).resolve().parent
INSTALLER = pathlib.Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer")

def fail(msg):
    print("build.py: " + msg, file=sys.stderr); sys.exit(1)

def visual_studio():
    vswhere = INSTALLER / "vswhere.exe"
    if not vswhere.exists(): fail("vswhere.exe not found; is Visual Studio installed?")
    out = subprocess.run([str(vswhere), "-latest", "-prerelease", "-products", "*", "-format", "json",
                          "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"],
                         capture_output=True, text=True, check=True).stdout
    found = json.loads(out)
    if not found: fail("no Visual Studio with the C++ tools found")
    return pathlib.Path(found[0]["installationPath"])

def msvc_environment(vs):
    """The environment vcvars64.bat produces, as a dict."""
    vcvars = vs / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    env = dict(os.environ); env["PATH"] = str(INSTALLER) + os.pathsep + env.get("PATH", "")
    out = subprocess.run(f'"{vcvars}" >nul && set', shell=True, capture_output=True, text=True, env=env, check=True).stdout
    result = {}
    for line in out.splitlines():
        k, sep, v = line.partition("=")
        if sep: result[k] = v
    if not shutil.which("cl", path=env_path(result)): fail("vcvars64.bat did not put cl on the path")
    return result

def clang_compiler(env):
    """The C compiler of the clang build: CC, or the MinGW-w64 clang that targets 64-bit Windows, from the PATH."""
    cc = env.get("CC") or "x86_64-w64-mingw32-clang"
    if not shutil.which(cc, path=env_path(env)):
        fail(f"{cc} not found on the PATH: put a MinGW-w64 clang for 64-bit Windows on the PATH (llvm-mingw's bin folder), or set CC")
    return cc

def env_path(env):
    return next((v for k, v in env.items() if k.upper() == "PATH"), "")

def system_environment():
    """This environment, with PATH refreshed from the registry (user and machine), so that tools installed after
    this session started, such as a global CMake and Ninja, are found. No Visual Studio is involved."""
    env = {k: v for k, v in os.environ.items() if k.upper() != "PATH"}
    parts = []
    try:
        import winreg
        for root, key in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                          (winreg.HKEY_CURRENT_USER, r"Environment")):
            try:
                with winreg.OpenKey(root, key) as k: parts.append(os.path.expandvars(winreg.QueryValueEx(k, "Path")[0]))
            except OSError: pass
    except ImportError: pass                                    # not Windows: the inherited PATH is current
    parts.append(os.environ.get("PATH", ""))
    env["PATH"] = os.pathsep.join(p for p in parts if p)
    for tool in ("cmake", "ninja"):
        if not shutil.which(tool, path=env["PATH"]): fail(f"{tool} not found on the PATH; the clang build needs a global {tool}")
    return env

def run(cmd, env):
    # On Windows, subprocess looks a program up on this process's PATH, not env's: resolve it against env first.
    exe = shutil.which(str(cmd[0]), path=env_path(env)) or str(cmd[0])
    print("+ " + " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run([exe] + [str(c) for c in cmd[1:]], env=env)
    if r.returncode != 0: fail(f"failed: {cmd[0]} (exit {r.returncode})")

def build(name, clean):
    # MSVC: Visual Studio's environment, which also carries its CMake and Ninja. clang: no Visual Studio at all, but
    # CMake, Ninja and the compiler from the PATH.
    env = msvc_environment(visual_studio()) if name == "msvc" else system_environment()
    tree = HERE / "build" / name
    if clean and tree.exists(): shutil.rmtree(tree)
    args = ["cmake", "-S", HERE, "-B", tree, "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release"]
    if name == "msvc":
        args += ["-DCMAKE_C_COMPILER=cl"]
    else:
        args += [f"-DCMAKE_C_COMPILER={clang_compiler(env)}"]
    run(args, env)
    run(["cmake", "--build", tree], env)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    which = args[0] if args else "all"
    if which not in ("msvc", "clang", "all"): fail("usage: build.py [msvc | clang | all] [--clean]")
    for name in (["msvc", "clang"] if which == "all" else [which]):
        build(name, "--clean" in sys.argv)
    print("build.py: done")
