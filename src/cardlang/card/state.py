"""State files: a virtual card's committed state, kept across restarts.

The file holds, for each applet, the hash of its compiled image, its committed persistent bytes and its persistent
keys, the private ones included, in the clear. That is fine for a development tool, and wrong for any real secret.

A save writes a new file beside the old one and renames it over it, so a crash leaves the old state or the new one,
never half of either. Loading refuses a state whose applets don't match the card: another AID, or another compiled
image, whose persistent layout may differ.
"""
import json, os, hashlib, pathlib

FORMAT = "cardlang-virtual-card-state"
WARNING = "Development state of a CardLang virtual card. It holds private keys in the clear: never use it for real secrets."

class StateError(ValueError):
    """A state file that doesn't fit the card."""

def supports(applet):
    return all(hasattr(applet.backend, m) for m in ("export_state", "import_state")) and image_of(applet) is not None

def image_of(applet):
    image = getattr(applet.backend, "image", None)
    return hashlib.sha256(bytes(image)).hexdigest() if image is not None else None

def snapshot(card):
    """The card's state as plain data: one entry per applet, None for one that isn't installed."""
    return [a.backend.export_state() if a.installed else None for a in card.applets]

def _encode(card, snap):
    applets = []
    for a, s in zip(card.applets, snap):
        entry = {"name": a.name, "aid": a.aid.hex().upper(), "image": image_of(a), "installed": s is not None}
        if s is not None:
            entry["persistent"] = s["partition"].hex()
            entry["keys"] = [{"id": i, "type": t, "material": m.hex()} for i, t, m in s["keys"]]
        applets.append(entry)
    return {"format": FORMAT, "warning": WARNING, "applets": applets}

def save(path, card, snap=None):
    """Write the card's state to path, atomically."""
    path = pathlib.Path(path)
    text = json.dumps(_encode(card, snapshot(card) if snap is None else snap), indent=1) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

def restore(path, card):
    """Load the state at path into the card's applets, marking those it has as installed."""
    path = pathlib.Path(path)
    try: doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e: raise StateError(f"{path}: {e}") from None
    if doc.get("format") != FORMAT: raise StateError(f"{path}: not a virtual card's state file")
    saved = {e["aid"]: e for e in doc.get("applets", [])}
    mine = {a.aid.hex().upper(): a for a in card.applets}
    if set(saved) != set(mine):
        raise StateError(f"{path}: the state is for the applets {sorted(saved)}, the card has {sorted(mine)}")
    for aid, a in mine.items():
        e = saved[aid]
        if e.get("image") != image_of(a):
            raise StateError(f"{path}: {a.name} has changed since the state was saved, and its persistent layout may differ")
        if not e.get("installed"): continue
        state = {"partition": bytes.fromhex(e["persistent"]),
                 "keys": [(k["id"], k["type"], bytes.fromhex(k["material"])) for k in e.get("keys", [])]}
        try: a.backend.import_state(state)
        except ValueError as err: raise StateError(f"{path}: {a.name}: {err}") from None
        a.installed = True
