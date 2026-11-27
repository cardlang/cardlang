"""Card files: a JSON description of a virtual card, and building the card it describes.

    {
      "atr": "3B 80 80 01 01",
      "backend": "pyvm",
      "applets": [
        { "program": "fido2", "aid": "A0 00 00 06 47 2F 00 01" },
        { "program": "piv", "aid": "A0 00 00 03 08 00 00 10 00 01 00" }
      ]
    }

`program` is a program directory or `.card` file, relative to the card file. Every applet is built for the ISO 7816
binding. `atr`, `backend` and `state` are optional: the defaults are the card's plain T=1 ATR, the Python VM, and no
state file. `state` names the file, relative to the card file, that keeps the card's state across restarts.
"""
import json, pathlib
from cardlang.front import project
from cardlang.harness import backends
from cardlang.card.iso7816 import Applet, VirtualCard

class CardFileError(ValueError):
    """A card file that can't be used."""

def _hex(text, what):
    try: return bytes.fromhex(str(text).replace(" ", ""))
    except ValueError: raise CardFileError(f"{what}: not hexadecimal: {text!r}") from None

def load(path, backend=None):
    """Build the VirtualCard a card file describes. backend overrides the file's."""
    path = pathlib.Path(path)
    try: desc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e: raise CardFileError(f"{path}: {e}") from None
    if not desc.get("applets"): raise CardFileError(f"{path}: no applets")
    name = backend or desc.get("backend", "pyvm")
    applets = []
    for i, a in enumerate(desc["applets"]):
        if "program" not in a or "aid" not in a: raise CardFileError(f"{path}: applet {i + 1} needs a program and an aid")
        program = (path.parent / a["program"]).resolve()
        if not program.exists(): raise CardFileError(f"{path}: applet {i + 1}: no program at {program}")
        meta = project.load(program) if program.is_dir() else None
        label = (meta or {}).get("name") or program.stem
        aid = _hex(a["aid"], f"{path}: applet {label}")
        if not 5 <= len(aid) <= 16: raise CardFileError(f"{path}: applet {label}: an AID has 5 to 16 bytes")
        if meta and meta.get("binding") not in (None, "iso7816"):
            raise CardFileError(f"{path}: applet {label} is built for the {meta['binding']} binding, not iso7816")
        applets.append(Applet(label, aid, backends.build(name, project.program_files(program), "iso7816")))
    kwargs = {"atr": _hex(desc["atr"], f"{path}: atr")} if "atr" in desc else {}
    try: vc = VirtualCard(applets, **kwargs)
    except ValueError as e: raise CardFileError(f"{path}: {e}") from None
    vc.state_file = (path.parent / desc["state"]).resolve() if desc.get("state") else None    # for open()
    return vc
