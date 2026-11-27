# TL3 — A virtual card behind a real smart card reader: detailed sub-plan

Planned 2026-11-27, at the user's request. Today an applet runs only inside the harness, driven by scenarios. TL3 puts it behind a smart card reader that the operating system sees as real. Ordinary PC/SC software can then talk to the FIDO2 and PIV applets as it would to a security key: python-fido2, OpenSC, Windows' own PIV support, and a browser through the operating system's WebAuthn. That tests the applets against real clients, not only against scenarios we wrote ourselves.

## 1. Decisions

| # | Question | Decision |
|---|---|---|
| R1 | Platforms | **Linux and Windows first-class, macOS best effort.** One bridge in pure Python for every system. Linux runs in CI. Windows is tested by hand. macOS is documented but not promised |
| R2 | State across restarts | **A state file.** Persistent globals and persistent keys are saved after every commit and loaded at start, so a registered passkey or a PIV certificate survives a restart of the bridge |
| R3 | Applets per card | **Several per card,** selected by AID, like a real security key that carries FIDO2 and PIV. A bridge can also serve several cards, one per reader slot |
| R4 | Testing | **Scripted and by hand.** python-fido2 and pyscard as development dependencies (added only after asking, at that step), and OpenSC's tools installed by the CI job. A manual checklist for Windows |

## 2. The reader: vsmartcard's vpcd

[vsmartcard](https://github.com/frankmorgner/vsmartcard) provides *vpcd*, a reader driver for pcsc-lite (Linux, macOS) and for the Windows smart card service. The operating system sees an ordinary reader. Behind it, vpcd forwards everything over a local TCP socket to a *virtual card* process. The project is maintained (release 0.11, September 2026, with Windows x64 and ARM64 and macOS builds). We only speak its socket protocol and link nothing of it, so its licence doesn't reach our code.

**The protocol.** vpcd listens on localhost, port 35963 (pcsc-lite's default configuration also opens 35964), and the card process connects to it. Every message, in both directions, is a 2-byte big-endian length followed by that many bytes. A one-byte message from vpcd is a control code: `00` power off, `01` power on, `02` reset, `04` get the ATR, which the card answers with its ATR. Any longer message is a command APDU, answered with a response APDU.

**Per system:**
- **Linux:** the package `vsmartcard-vpcd` (Debian and Ubuntu), with `pcscd`. Its reader configuration sits in `/etc/reader.conf.d/`.
- **Windows:** the release's MSI installs the driver (the BixVReader UMDF driver with vpcd's interface), configured in `C:\Windows\BixVReader.ini`. The driver is signed with the project's own test certificate, which must be imported into the machine's *Trusted Root* and *Trusted Publishers* stores. That changes the machine's trust, so it's a step for the user to take knowingly, and the documentation says so. The Windows driver can't connect out, so the card process always connects to it.
- **macOS (best effort):** built from source with `--enable-infoplist`. Since macOS 10.10 the system only loads readers that are USB devices, so vpcd's Info.plist must name a real USB device's vendor and product ID, and the reader exists only while that device is plugged in. We document this and stop there.

## 3. What exists, and what's missing

| Need | What exists | What's missing |
|---|---|---|
| Running an applet | Three backends behind one interface (`cardlang.harness.backends`): `install`, `session_start`, `session_end`, `reset`, `select`, `deselect`, `command` | Nothing: the virtual card drives the same interface |
| The ISO 7816 binding | The Base Profile defines it fully: whole messages of at least 1280 bytes (BP-48); chaining, extended length and `61xx` with GET RESPONSE (BP-49); the request without length fields (BP-50); `on_select` (BP-50a); status words (BP-51); sessions (BP-55, BP-56) | **No implementation of the transport.** The scenario runner hands requests to `command` directly and only encodes status words (`harness/scenario.py`). APDU parsing, chaining, GET RESPONSE, extended length and SELECT by AID don't exist |
| AIDs | The applets know their own protocol AIDs only in comments | Somewhere to say which AID selects which applet |
| State across restarts | The Python VM's HAL holds the committed persistent bytes and the persistent keys (`pyvm/hal.py`) | Saving and loading them. The C VM's host HAL keeps its keys in Mbed TLS's key store |
| Randomness | A deterministic generator, seeded by scenarios | Seeding from the operating system for real use |

No change to the specification or the Base Profile is expected. Everything the virtual card decides that the profile leaves open (the ATR, the AIDs, the size limits, how partial AIDs match) is written down as the virtual card's own choices in its README.

## 4. The design

**The virtual card** (`src/cardlang/card/`, a new subpackage):
- `apdu.py` parses command APDUs, short and extended (cases 1–4), and builds responses.
- `iso7816.py` is the card's operating system for the ISO 7816 binding:
  - SELECT by AID (`00 A4 04 00`), matching an applet whose AID starts with the given bytes, as PIV clients select with the short `A0 00 00 03 08`. It runs `on_select`, and deselects the previous applet, which ends its session (BP-55);
  - command chaining: parts are collected until the last one, then `command` runs once on the whole request (BP-48);
  - long responses: `61xx` and GET RESPONSE, or extended Le, as the host asks (BP-49);
  - outcomes to status words, reusing the scenario runner's encoding (BP-51);
  - power on and reset start a session of every installed applet, and power off ends them (BP-56);
  - MANAGE CHANNEL is refused with `6881`, since logical channels aren't visible (BP-55);
  - a request longer than the card's limit, at least 1280 bytes, gets `6700`.
- `card.py` holds a card: its applets, each a backend card from `harness.backends` built from its program, plus their AIDs and the ATR.
- `vpcd.py` is the socket client of §2. It reconnects when vpcd restarts, as it does when the reader service restarts.
- `state.py` saves and loads a card's state (R2).

**The card file.** A small JSON file describes a card:

```json
{
  "atr": "3B 80 80 01 01",
  "backend": "pyvm",
  "state": "security-key.state",
  "applets": [
    { "program": "../examples/fido2", "aid": "A0 00 00 06 47 2F 00 01" },
    { "program": "../examples/piv", "aid": "A0 00 00 03 08 00 00 10 00 01 00" }
  ]
}
```

Paths are relative to the file. A card for each example ships beside it, and one card with both, the *security key*, ships in `examples/`.

**The command.** `clc card <card file> [--port 35963] [--trace] [--seed <hex>]` builds the applets, installs them on first use or loads the state file, connects to vpcd, and serves until it's stopped. `--trace` prints every APDU and response, and the source line of any trap. `--seed` makes the random generator repeatable, for tests. Without it, the generator is seeded from the operating system.

**The state file.** After every command that committed anything, the card writes its state to a new file and renames it over the old one, so a crash never leaves half a state. The file holds, per applet, the hash of its compiled image, the committed persistent bytes, and the persistent keys. A state whose image hash doesn't match the program is refused with a clear message, and `--reset-state` starts over. The file holds private keys in the clear, which is fine for a development tool and wrong for anything else: the command and the README say so plainly.

## 5. The work

1. **The transport, without a reader.** `apdu.py`, `iso7816.py` and `card.py`, driven in-process. Tests in a new `tests/card_check.py`, a row of `run_checks`:
   - SELECT with full and partial AIDs, an unknown AID (`6A82`), and `on_select`'s data;
   - chaining of a 1280-byte request in short APDUs, and the same request in one extended APDU;
   - a long response through `61xx` and GET RESPONSE, and through extended Le;
   - switching between the FIDO2 and PIV applets ends the other's session, as PIV's security status requires;
   - power off and on, and reset;
   - the existing FIDO2 and PIV session checks (`examples/*/check.py`) replayed as APDUs through the transport.
2. **State files** for the Python VM: `hal.py` exports and imports its committed partition and persistent keys. `state.py` with the atomic write. Tests: register a credential, restart, and use it; a changed program refuses the old state.
3. **The vpcd link and `clc card`.** `vpcd.py`, the command, and a test that plays vpcd's side of the socket in-process, so `run_checks` covers the protocol without a reader.
4. **Real clients, in-process.** python-fido2 and pyscard become development dependencies (I'll ask before adding them). python-fido2's CTAP2 client runs against the transport through a small in-process device, so make-credential, get-assertion, the client PIN and credential management run in `run_checks` on every system, with no reader. A PIV flow does the same through pyscard's APDU interface where it can.
5. **Linux CI with a real reader.** A job installs `pcscd`, `vsmartcard-vpcd` and `opensc` from the distribution, starts `clc card` on the security key, and runs:
   - python-fido2 over PC/SC: register, then authenticate, with and without a PIN;
   - OpenSC on the PIV applet: `opensc-tool --list-readers` finds the card, `pkcs11-tool` logs in with the PIN, lists objects, and signs with a key, and the signature checks against the certificate's public key;
   - a restart of `clc card` between registering and authenticating, so the state file is tested too.
6. **Windows, by hand.** The README gets the setup (vpcd's MSI and the certificate step), and a checklist, each item marked as verified or not:
   - `certutil -scinfo` reads the PIV card through Windows' built-in PIV support;
   - a file is signed with a PIV key (OpenSC's `pkcs11-tool`, or a certificate in Windows' store);
   - python-fido2 registers and authenticates over PC/SC;
   - a browser registers a passkey on webauthn.io through Windows' security-key support. Whether Windows offers a key behind a PC/SC reader to browsers is unknown, and this item finds out.
7. **The C VM as a backend.** A host-side export and import of the C VM's partition and persistent keys, so `"backend": "cvm"` works with state files too. The Linux CI job then runs once per backend.
8. **Documentation.**
   - `src/cardlang/card/README.md`: the virtual card, its choices (§3), the card file, the state file, and the setup on each system;
   - the guide: a section in chapter 9, *Testing and debugging*, on talking to an applet from real software, kept short and pointing to the README for the reader setup;
   - the root README and the extension's DEVELOPMENT.md, a line each.

Each step ends with `run_checks` passing, and is committed on its own when asked. Steps 1 to 4 need nothing installed and run everywhere. Steps 5 and 6 need a reader. Step 7 can come later without blocking the rest.

## 6. Checks

- `card_check.py` covers the transport, the state file and the vpcd protocol in-process, on every CI system.
- The in-process python-fido2 tests run the FIDO2 applet against an independent CTAP2 client on every CI system.
- The Linux reader job proves the whole path: pcscd, vpcd, `clc card`, the applet, and two independent clients.
- On Windows, the checklist of step 6, done by hand on this machine, with the results recorded in this plan.

## 7. Risks and open questions

- **Windows' driver certificate.** Importing a test certificate into the trusted roots weakens the machine's trust a little. We document exactly what is imported and how to remove it, and leave the decision to whoever installs it. If the project ever ships a properly signed driver, the step goes away.
- **Browsers.** A browser on Windows may or may not use a FIDO2 key behind a PC/SC reader. On Linux, Chrome and Firefox speak only USB HID to security keys, so browser tests there would need a virtual HID device, which is out of scope. Real FIDO2 clients over PC/SC (python-fido2, and libfido2 when built with PC/SC support) still test the applet fully.
- **Speed.** The Python VM's ECDSA is pure Python. If a signature takes long enough to trip a client's timeout, the C VM backend of step 7 is the answer, and step 5 measures it.
- **Clients that expect a YubiKey.** Some tools check a vendor's version command first. They're out of scope: we test against the standards, through clients that follow them.
- **The ATR.** A plain T=1 ATR should be enough for both systems' reader stacks. If Windows' smart card plug-and-play insists on a driver for an unknown ATR, the ATR in the card file is the knob, and the checklist records what works.

## 8. Progress

**Step 1 built 2026-11-27,** on the branch `virtual-card-reader`. `src/cardlang/card/` has `apdu.py`, `iso7816.py` (`VirtualCard`) and `card.py` (card files). The examples have card files: `examples/fido2/virtual-card.json`, `examples/piv/virtual-card.json`, and `examples/security-key.json` with both. `tests/card_check.py` checks APDU parsing, then the transport on two copies of a small echo applet (`tests/testdata/echo/`). Then it replays both example checks through the security key, as short APDUs with chaining and GET RESPONSE and as extended APDUs. It runs as two rows of `run_checks`, on pyvm and on cvm, and it also passes on interp. The card's own choices are in `src/cardlang/card/README.md`.

Two things the replay showed:
- The example checks model a power cycle as a reset followed by a session start, with no new SELECT, because a backend card has one applet, selected for good. Over the transport the replay selects again after power-on, as real hosts do.
- None of the FIDO2 example's requests or responses go over 255 bytes, so its short and extended runs send the same APDUs. Only the echo applet and PIV exercise chaining and GET RESPONSE.

**Step 2 built 2026-11-27.** The Python VM's HAL exports and imports its committed partition and persistent keys (`export_persistent`, `import_persistent`), and its card offers `export_state` and `import_state`. `src/cardlang/card/state.py` writes the state file atomically, with each applet's image hash, persistent bytes and keys, and refuses a file that doesn't fit the card. `VirtualCard.open(path)` restores or installs, then saves after every change, comparing snapshots so an unchanged state isn't rewritten. Card files may name a `state`. `VirtualCard.seed()` reseeds every applet from the given bytes and its AID. The real-use command must seed from the operating system, because the test generator's fixed seed would repeat its bytes after a restart.

The echo applet gained a persistent counter and a persistent key. `card_check.py` checks that both survive a restart, as does a FIDO2 credential, which then signs in with a valid signature. It also checks that a changed program and another set of applets are refused, and that the C VM and the interpreter refuse a state file with a hint.

**Step 3 built 2026-11-27.** `src/cardlang/card/vpcd.py` is the link. It connects to vpcd, serves the length-prefixed protocol, and handles power off, power on, reset and ATR. It reconnects when the connection drops, and logs once while vpcd is away. `clc card <card file>` builds and opens the card and serves it. It seeds from the operating system unless `--seed` is given, and has `--state`, `--no-state`, `--backend`, `--host`, `--port` and `--trace`. The trace includes the source line of a trap. The example card files now keep their state under `build/`, which git ignores. `card_check.py` tests the link against a stand-in vpcd in-process: the protocol, a 600-byte extended exchange, power events, reconnecting, waiting and stopping. It also starts `clc card` as a process on the security key, with a state file, and talks FIDO2 and PIV to it. Nothing has run against the real vpcd yet: that's steps 5 and 6.
