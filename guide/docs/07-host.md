# 7. Talking to the host

All an applet ever sees is bytes. A request comes in and a response goes out. How those bytes travel, and how the host learns whether a command worked, depends on the *binding* the applet is built for. [Chapter 1](01-getting-started.md#applets-platforms-and-hosts) introduced the Base Profile's two bindings and the raw binding's envelope. Here we put the two bindings side by side, and then take a closer look at ISO 7816, the binding smart cards use, with a small applet written for it.

## One outcome, two encodings

Whichever binding you use, a command ends in one of four ways, and the host can always tell which (*PLT-9*). The bindings only encode them differently:

| The command ends with | Raw binding: the envelope | ISO 7816: the response |
|---|---|---|
| `Ok(count)` | `00 00 00`, then the data | The data, then status word `9000` |
| `Err` with the applet's error of code `c` | `01`, then `c` | Status word `c` |
| `Err(CardError.m)` | `02`, then `m`'s code | Status word `6F00` + `m`'s code |
| A trap | `03 00 00` | Status word `6F00` |

The applet's own code doesn't change. You write `return Err(PinError.WrongPin)` once, and the platform encodes it for whichever binding the applet uses.

## Choosing a binding

The binding follows from the device and the host you're writing for. You name it in `cardlang.json`, and an applet is built for exactly one (*BP-47*).

The raw binding is for a host that talks to the applet directly, typically the main firmware of a microcontroller calling into a TrustZone secure partition. You design the request format yourself, as we did for the vault. The ISO 7816 binding is for smart cards and NFC tokens, and for hosts that already speak their protocol, such as card readers, phones, and the standard middleware for PIV, OpenPGP or FIDO. Its requests and status words follow ISO/IEC 7816-4.

An applet written for one binding rarely needs the other. The vault stays on the raw binding, and the rest of this chapter uses a small applet of its own.

## The ISO 7816 binding

### Requests are APDUs

An ISO 7816 command is called an *APDU*. It has four header bytes followed by data, and the platform passes it to `command` without its length fields (*BP-50*):

| Bytes | Name | Meaning |
|---|---|---|
| `request[0]` | CLA | The class of the command |
| `request[1]` | INS | The instruction, such as `20` for VERIFY |
| `request[2]`, `request[3]` | P1, P2 | Parameters of the instruction |
| `request[4..request.length]` | Data | The command data, if any |

The class says whose command it is. Class `00` is *interindustry*, for the commands that ISO 7816-4 defines itself, such as VERIFY (`00 20`), which mean the same on every card. An applet mustn't declare its own commands there. Its own commands go in a *proprietary* class, such as `80`, where it can decide what each instruction means.

The length the host expects back, *Le*, isn't passed to the applet. `response.length` tells it how much room the platform has given the answer instead. If a message is too long for one APDU, the host splits it, using *command chaining* or *extended length*, and the platform puts it back together. Long answers are split by the platform, with `61XX` and GET RESPONSE. None of this reaches the applet. `command` runs once on the whole request and writes the whole response (*BP-48*, *BP-49*).

### Status words

Every answer ends with a two-byte *status word*. `9000` means success, and other values report errors. ISO 7816-4 defines a great many, and applets reuse them:

| Status word | Meaning |
|---|---|
| `6300` | Verification failed |
| `6700` | Wrong length |
| `6982` | Security status not satisfied, for example a PIN is needed first |
| `6983` | Authentication method blocked |
| `6A86` | Incorrect P1 or P2 |
| `6D00` | Instruction not supported |
| `6E00` | Class not supported |

In this binding an applet's error codes *are* its status words. Every code therefore has to lie in `6200`–`6EFF` or `9100`–`9FFF` (*BP-52*), which keeps the applet's codes away from `9000`, and from the `6Fxx` range that the platform uses for its own errors and for traps. Any other code is rejected when the applet is built:

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

A card holds several applications, and the host chooses one with a SELECT command, giving the application's *identifier*. The platform deals with SELECT itself, and `command` never sees it (*BP-50*). An applet can still answer it, though, with an `on_select` handler, whose data becomes the response to the SELECT (*BP-50a*):

<!-- check: fragment -->
```cardlang
const VERSION: u8[7] = b"PIN 1.0";

function on_select(response: inout u8[]) -> u32 {
    response[0..VERSION.length] = VERSION;
    return Ok(VERSION.length);
}
```

If `on_select` returns `Err` or traps, the applet isn't selected.

### Sessions

On a card, an applet's session begins at power-on, and again at the first SELECT after it was deselected. It ends when another application is selected or the power goes (*BP-56*). So session state such as "the PIN was verified" disappears as soon as the host talks to another application on the card. Smart-card hosts expect this, and security standards such as PIV require it.

## A PIN applet for smart cards

Here's a small applet in the style of a smart card's PIN check. It answers two commands, the interindustry VERIFY (`00 20`), and a proprietary status command (`80 10`) that says whether the PIN has been verified. Its `cardlang.json` names the ISO 7816 binding:

```json
{ "name": "pincheck", "files": ["pincheck.card"], "binding": "iso7816" }
```

Its errors are status words taken from the table above:

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

VERIFY checks the PIN the same way the vault's `check_pin` does in [chapter 6](06-state.md#checking-a-pin), counting the try before it compares. Sent without data, it answers the number of tries left:

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

`process` reads the header and looks at the class and the instruction together:

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

A command is identified by its class and its instruction together. `00 20` is VERIFY and `80 10` is the applet's own status command, but `80 20` and `00 10` are neither, so they count as unsupported instructions. P2 = `80` names which PIN to verify, as ISO 7816 and PIV do, and any other P1 or P2 gets `6A86`. With only two commands, an `if` chain is enough to tell them apart. An applet with more of them is better off with an enum and a `decode` function, like the vault's.

Real cards report a wrong PIN a little differently, as `63CX`, where `X` is the number of tries left. An error can only carry its code, so that needs one error member per count, such as `Retries2 = 0x63C2;`. The [PIV example](https://github.com/cardlang/cardlang/tree/main/examples/piv) does it that way.

### Scenarios on ISO 7816

Scenarios for an ISO 7816 applet have two extra steps, `select` and `deselect`, and can check status words with `expect sw`:

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

`expect ok …` checks the data of a successful answer, while `expect sw …` checks the status word the host receives, whatever the outcome.
