# The virtual card

A virtual card runs one or more applets behind the ISO 7816 binding and talks APDUs, as a real card does. Each applet is a backend card from the harness, so any backend can run it: the Python VM by default, the C VM, or the reference interpreter.

| Module | What it is |
|---|---|
| `apdu.py` | Command APDUs: parsing and building every case, short and extended |
| `iso7816.py` | `VirtualCard`: the card's side of the ISO 7816 binding, from APDUs to the applets and back |
| `card.py` | Card files, and building the card one describes |

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

A `program` is a program directory or a `.card` file, relative to the card file, and every applet is built for the ISO 7816 binding. `atr` and `backend` are optional. That example is [`examples/security-key.json`](../../../examples/security-key.json), which carries both example applets, like a real security key. Each example also has a card of its own, `virtual-card.json`.

```python
from cardlang.card import card
c = card.load("examples/security-key.json")
c.install(); c.power_on()
response = c.transmit(bytes.fromhex("00A4040008A0000006472F0001"))   # SELECT the FIDO2 applet
```

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

[`tests/card_check.py`](../../../tests/card_check.py) checks APDU parsing, then the transport on two copies of a small echo applet (`tests/testdata/echo/`). Then it replays the FIDO2 and PIV example checks through the card: every request they make goes to the security key as APDUs, once as short APDUs with chaining and GET RESPONSE, and once as extended APDUs.
