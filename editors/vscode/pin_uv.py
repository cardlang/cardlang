"""Pin the uv that the extension downloads for users without uv: write editors/vscode/uv.json.

For each platform the extension supports, uv.json names uv's release archive and its SHA-256, which this script reads
from the .sha256 file uv publishes beside each archive. The extension checks every download against that hash.
Raising the pin is a deliberate change: run this with the new version, and review the diff.

    uv run python -I editors/vscode/pin_uv.py 0.11.7
"""
import sys, json, re, pathlib, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
BASE = "https://github.com/astral-sh/uv/releases/download"

# VS Code's platform and architecture (Node's process.platform-process.arch) -> uv's build. Linux uses the static musl
# build, which runs on glibc and musl systems alike.
TARGETS = {
    "win32-x64": "uv-x86_64-pc-windows-msvc.zip",
    "win32-arm64": "uv-aarch64-pc-windows-msvc.zip",
    "darwin-x64": "uv-x86_64-apple-darwin.tar.gz",
    "darwin-arm64": "uv-aarch64-apple-darwin.tar.gz",
    "linux-x64": "uv-x86_64-unknown-linux-musl.tar.gz",
    "linux-arm64": "uv-aarch64-unknown-linux-musl.tar.gz",
}

def main(version):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version): sys.exit(f"not a uv version: {version}")
    platforms = {}
    for platform, archive in TARGETS.items():
        url = f"{BASE}/{version}/{archive}"
        with urllib.request.urlopen(url + ".sha256", timeout=30) as r:
            digest = r.read().decode("ascii").split()[0].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest): sys.exit(f"{archive}.sha256: not a SHA-256")
        platforms[platform] = {"url": url, "sha256": digest}
        print(platform, digest)
    pin = {"version": version, "platforms": platforms}
    (HERE / "uv.json").write_text(json.dumps(pin, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {HERE / 'uv.json'}")

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
