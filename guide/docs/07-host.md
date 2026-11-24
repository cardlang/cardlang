# 7. Talking to the host

An applet only ever sees bytes: a request comes in, a response goes out. How those bytes travel between the host and the applet, and how the host learns whether a command succeeded, is decided by the *binding* the applet is built for. [Chapter 1](01-getting-started.md#applets-platforms-and-hosts) introduced the two bindings of the Base Profile, and the raw binding's envelope. This chapter puts the two side by side, and then looks closely at ISO 7816, the binding of smart cards, with a small applet written for it.

## One outcome, two encodings

Whatever the binding, a command ends in one of four ways, and the host can always tell them apart (*PLT-9*). Only the encoding differs:

| The command ends with | Raw binding: the envelope | ISO 7816: the response |
|---|---|---|
| `Ok(count)` | `00 00 00`, then the data | The data, then status word `9000` |
| `Err` with the applet's error of code `c` | `01`, then `c` | Status word `c` |
| `Err(CardError.m)` | `02`, then `m`'s code | Status word `6F00` + `m`'s code |
| A trap | `03 00 00` | Status word `6F00` |

The applet's code is the same in both. `return Err(PinError.WrongPin)` is written once, and the platform encodes it for the binding.

## Choosing a binding

You choose the binding for the device and the host you are writing for. It is named in `cardlang.json`, and an applet is built for exactly one (*BP-47*):

- **The raw binding** is for a host that talks to the applet directly. Typically that is the main firmware of a microcontroller calling into a TrustZone secure partition. You design the request format yourself, as the vault does.
- **The ISO 7816 binding** is for smart cards and NFC tokens, and for hosts that already speak their protocol: card readers, phones, and standard middleware for PIV, OpenPGP or FIDO. Its requests and status words follow ISO/IEC 7816-4.

An applet written for one rarely needs the other. The vault stays on the raw binding; the rest of this chapter uses a small applet of its own.

## The ISO 7816 binding

### Requests are APDUs

An ISO 7816 command is an *APDU*: four header bytes, then the data. The platform passes it to `command` without its length fields (*BP-50*):

| Bytes | Name | Meaning |
|---|---|---|
| `request[0]` | CLA | The class of the command |
| `request[1]` | INS | The instruction, such as `20` for VERIFY |
| `request[2]`, `request[3]` | P1, P2 | Parameters of the instruction |
| `request[4..request.length]` | Data | The command data, if any |

The class says whose command it is. `00` is the *interindustry* class: commands defined by ISO 7816-4 itself, such as VERIFY (`00 20`), mean the same on every card. An applet's own commands must not be declared in that space. They use a *proprietary* class, such as `80`, where the applet decides what each instruction means.

The host's expected response length, *Le*, is not passed: `response.length` is the room the platform gives the answer. Messages too long for one APDU are split by the host, and reassembled by the platform, with *command chaining* or *extended length*. Long answers are split by the platform, with `61XX` and GET RESPONSE. The applet never sees any of this: `command` runs once, on the whole request, and writes the whole response (*BP-48*, *BP-49*).

### Status words

Every answer ends with a two-byte *status word*. `9000` means success; the rest report errors. ISO 7816-4 defines many, and applets reuse them:

| Status word | Meaning |
|---|---|
| `6300` | Verification failed |
| `6700` | Wrong length |
| `6982` | Security status not satisfied, for example a PIN is needed first |
| `6983` | Authentication method blocked |
| `6A86` | Incorrect P1 or P2 |
| `6D00` | Instruction not supported |
| `6E00` | Class not supported |

An applet's error codes *are* its status words, so in an applet built for ISO 7816 every code must lie in `6200`–`6EFF` or `9100`–`9FFF` (*BP-52*). That keeps them clear of `9000`, and of the `6Fxx` range the platform uses for its own errors and for traps. A code outside those ranges is rejected when the applet is built:

<!-- check: error BP-52 binding=iso7816 -->
```cardlang
errors PinError {
    WrongPin = 4;
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    return Err(PinError.WrongPin);
}
```

### SELECT

A card holds several applications, and the host chooses one by its *application identifier* with a SELECT command. The platform handles SELECT itself: the applet never sees it in `command` (*BP-50*). An applet may answer it, though, with the handler `on_select`, whose data becomes the SELECT response (*BP-50a*):

<!-- check: fragment -->
```cardlang
const VERSION: u8[7] = b"PIN 1.0";

function on_select(response: inout u8[]) -> u32 {
    response[0..VERSION.length] = VERSION;
    return Ok(VERSION.length);
}
```

If `on_select` returns `Err`, or traps, the applet is not selected.

### Sessions

On a card, an applet's session starts at power-on, and again at the first SELECT after it was deselected. It ends when another applet is selected, or when the power goes (*BP-56*). So session state, such as "the PIN was verified", is lost as soon as the host talks to another application on the card. This is what smart-card hosts expect, and what security standards such as PIV require.

## A PIN applet for smart cards

Here is a small applet in the style of a smart card's PIN check. It answers two commands: the interindustry VERIFY (`00 20`), and a proprietary status command (`80 10`) that says whether the PIN is verified. Its `cardlang.json` names the ISO 7816 binding:

```json
{ "name": "pincheck", "files": ["pincheck.card"], "binding": "iso7816" }
```

Its errors are status words from the table above:

<!-- check: program pincheck binding=iso7816 -->
```cardlang
errors PinError {
    WrongPin = 0x6300;
    WrongLength = 0x6700;
    Blocked = 0x6983;
    WrongParameters = 0x6A86;
    UnsupportedInstruction = 0x6D00;
    UnsupportedClass = 0x6E00;
}

const CLA_INTERINDUSTRY: u8 = 0x00;
const CLA_PROPRIETARY: u8 = 0x80;
const INS_VERIFY: u8 = 0x20;
const INS_STATUS: u8 = 0x10;
const PIN_REFERENCE: u8 = 0x80;
const PIN: u8[6] = b"246810";
const MAX_TRIES: u8 = 3;
const VERSION: u8[7] = b"PIN 1.0";

persistent tries: u8;
session verified: bool;

function on_install() {
    tries = MAX_TRIES;
    return Ok();
}

function on_select(response: inout u8[]) -> u32 {
    response[0..VERSION.length] = VERSION;
    return Ok(VERSION.length);
}
```

VERIFY checks the PIN exactly as the vault's `check_pin` does in [chapter 6](06-state.md#checking-a-pin), counting the try before comparing. VERIFY with no data answers the tries left:

<!-- check: program pincheck -->
```cardlang
function verify(pin: ref u8[], response: inout u8[]) -> u32 {
    if pin.length == 0 {
        response[0] = tries;
        return Ok(1);
    }
    require tries > 0 else PinError.Blocked;
    verified = false;
    tries -= 1;
    require pin.length == PIN.length else PinError.WrongPin;
    require equal(ref pin, ref PIN) else PinError.WrongPin;
    tries = MAX_TRIES;
    verified = true;
    return Ok(0);
}
```

`process` reads the header, and dispatches on the class and the instruction together:

<!-- check: program pincheck -->
```cardlang
command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length >= 4 else PinError.WrongLength;
    var class: u8 = request[0];
    var instruction: u8 = request[1];
    require (class == CLA_INTERINDUSTRY) or (class == CLA_PROPRIETARY) else PinError.UnsupportedClass;
    if (class == CLA_INTERINDUSTRY) and (instruction == INS_VERIFY) {
        require (request[2] == 0x00) and (request[3] == PIN_REFERENCE) else PinError.WrongParameters;
        return verify(ref request[4..request.length], inout response);
    } else if (class == CLA_PROPRIETARY) and (instruction == INS_STATUS) {
        require request.length == 4 else PinError.WrongLength;
        if verified {
            response[0] = 0x01;
        } else {
            response[0] = 0x00;
        }
        return Ok(1);
    }
    return Err(PinError.UnsupportedInstruction);
}
```

- **P2 = `80`** names the PIN to verify, as ISO 7816 and PIV do. Any other P1 or P2 is `6A86`.
- **A command is its class and instruction together.** `00 20` is VERIFY, and `80 10` is the applet's own status command. `80 20` and `00 10` are neither, so they are unsupported instructions.
- **The commands** are decoded with an `if` chain here. With more instructions, an enum and a `decode` function, as in the vault, scale better.

### Scenarios on ISO 7816

A scenario for an ISO 7816 applet uses two more steps, `select` and `deselect`, and can check status words with `expect sw`:

<!-- check: scenario pincheck -->
```scenario
install
power_on
select                              # SELECT: on_select answers the version
expect ok 50 49 4E 20 31 2E 30
command 00 20 00 80                 # VERIFY with no data: the tries left
expect ok 03
command 00 20 00 80 31 32 33 34 35 36
expect sw 6300                      # a wrong PIN
command 00 20 00 80 32 34 36 38 31 30
expect sw 9000                      # the right one
command 80 10 00 00
expect ok 01                        # verified
deselect                            # another application is selected
select
expect sw 9000
command 80 10 00 00
expect ok 00                        # a new session: no longer verified
command 00 B0 00 00
expect sw 6D00                      # an instruction it does not know
command 80 20 00 80
expect sw 6D00                      # VERIFY exists only in the interindustry class
command A0 20 00 80
expect sw 6E00                      # a class it does not know
```

`expect ok …` checks the data of a successful answer; `expect sw …` checks the status word the host receives, whatever the outcome.

## What next

- Real cards report a wrong PIN as `63CX`, where `X` is the tries left. Since an error carries only its code, that takes one error member per count: `Retries2 = 0x63C2;`, and so on. The [PIV example](https://github.com/cardlang/cardlang/tree/main/examples/piv) does exactly this. Change `verify` to answer `63C2` and `63C1` after wrong guesses.
- Add CHANGE REFERENCE DATA, instruction `24`, which changes the PIN. Store the PIN in persistent state, and change it in a transaction, as in [chapter 6](06-state.md#changing-the-pin).
- Send `command 80 10 00 00 FF`, a status request with data. What does the host get, and which `require` decides it?
