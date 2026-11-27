# The virtual card

A virtual card runs one or more applets behind the ISO 7816 binding and talks APDUs, as a real card does. Each applet is a backend card from the harness, so any backend can run it: the Python VM by default, the C VM, or the reference interpreter.

| Module | What it is |
|---|---|
| `apdu.py` | Command APDUs: parsing and building every case, short and extended |
| `iso7816.py` | `VirtualCard`: the card's side of the ISO 7816 binding, from APDUs to the applets and back |
| `card.py` | Card files, and building the card one describes |
| `state.py` | State files: a card's committed state, kept across restarts |

## Card files

A card file is a small JSON file that lists the applets and their AIDs:

```json
{
  "atr": "3B 80 80 01 01",
  "backend": "pyvm",
  "applets": [
    { "program": "fido2", "aid": "A0 00 00 06 47 2F 00 01" },
    { "program": "piv", "aid": "A0 00 00 03 08 00 00 10 00 01 00" }
  ]
}
```

A `program` is a program directory or a `.card` file, relative to the card file, and every applet is built for the ISO 7816 binding. `atr` and `backend` are optional, and so is `state`, which names a state file relative to the card file. That example is [`examples/security-key.json`](../../../examples/security-key.json), which carries both example applets, like a real security key. Each example also has a card of its own, `virtual-card.json`.

```python
import os
from cardlang.card import card
c = card.load("examples/security-key.json")
c.seed(os.urandom(32))          # without it, every run draws the same "random" bytes
c.open("security-key.state")    # restore the state, or install the applets and save it
c.power_on()
response = c.transmit(bytes.fromhex("00A4040008A0000006472F0001"))   # SELECT the FIDO2 applet
```

`open()` without a file installs the applets and keeps nothing.

## State files

With a state file, the card keeps its applets' committed state across restarts, so a registered FIDO2 credential or a PIV certificate is still there the next time. The file holds, for each applet, the hash of its compiled image, its committed persistent bytes and its persistent keys. The card saves it after every command, session start or installation that changed anything. It writes a new file and renames it over the old one, so a crash leaves one whole state or the other.

The file holds private keys in the clear. That's fine for testing, and it's why a virtual card must never hold a real secret.

A state file is refused when it doesn't fit the card: when the card has other applets, or when an applet's program has changed since, because its persistent layout may have changed with it. Delete the file to start over. For now only the Python VM can save its state.

## Randomness

Each applet's random generator starts from a fixed seed, as the scenarios need. `seed()` reseeds every applet, each from the given bytes and its AID. A card used by real clients must be seeded from the operating system, or every run draws the same bytes, and a restarted card repeats what it drew before.

## What the card does

The Base Profile gives the platform these jobs in the ISO 7816 binding, and the card does them:
- **SELECT by AID** (`00 A4 04 xx`) runs the applet's `on_select` and deselects the applet selected before, which ends its session (BP-50a, BP-55). With `P2` = `0C`, the response has no data.
- **Command chaining** (CLA bit `10`): the parts are collected, each answered with `9000`, and `command` runs once on the whole request (BP-48, BP-49).
- **Long responses** go out in parts, the first ones ending in `61xx` and fetched with GET RESPONSE, or all at once when an extended Le allows it (BP-49).
- **Outcomes** become status words as BP-51 says.
- **Power on and reset** start a session of every applet, and **power off** ends them (BP-56). A security reset ends every session and leaves the card off.

## The card's own choices

Where the profile leaves a choice to the platform, the card makes these:

| Choice | The card's answer |
|---|---|
| The ATR | `3B 80 80 01 01`: T=1, no historical bytes. A card file can set another |
| Requests and responses | Up to 4096 bytes each, above the profile's 1280 (BP-48). A longer request gets `6700` |
| AIDs | A SELECT matches the applet whose AID starts with the given bytes, as PIV clients select with `A0 00 00 03 08`. No applet's AID may start with another's |
| SELECT of an unknown AID | `6A82`, and the applet selected before stays selected |
| A failed `on_select` | Its outcome's status word, and no applet is selected |
| A command with no applet selected | `6985` |
| A chain broken off by another command | `6883`, and the chain is dropped |
| GET RESPONSE with nothing to send | `6985` |
| Logical channels | Only the basic channel. Another channel, or MANAGE CHANNEL, gets `6881` |
| A malformed APDU | `6700` |

## Checks

[`tests/card_check.py`](../../../tests/card_check.py) checks APDU parsing, then the transport on two copies of a small echo applet (`tests/testdata/echo/`). It checks state files: the echo applet's persistent counter and key survive a restart, as does a FIDO2 credential, which still signs in with a valid signature. A changed program or another set of applets refuses the old state. Then it replays the FIDO2 and PIV example checks through the card: every request they make goes to the security key as APDUs, once as short APDUs with chaining and GET RESPONSE, and once as extended APDUs.
