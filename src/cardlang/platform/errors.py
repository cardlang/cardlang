"""The Base Profile's CardError codes, read from the profile's table (platform/base-profile.md).

The compiler, the Python VM and the harness all need them.
"""
import re
from cardlang import layout

CARD_ERROR_CODES = {m: int(c, 16) for m, c in re.findall(r"^\| `(\w+)` \| `0x([0-9A-Fa-f]{4})` \|",
                                                         layout.at().base_profile.read_text(encoding="utf-8"), re.M)}
