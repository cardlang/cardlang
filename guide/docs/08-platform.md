# 8. Using the platform

So far the vault has used only the language. Real applets lean on the platform for what the language deliberately leaves out: keys, cryptography and randomness. In this chapter the vault gets a signing key, which never leaves the device, and the secret is wiped when the PIN is blocked.

## The platform's APIs

The platform's services are functions named `card.<family>.<name>`, described in the Base Profile and listed with their exact signatures in its [catalog](https://github.com/cardlang/cardlang/blob/main/platform/base-catalog.txt):

| Family | For |
|---|---|
| `card.key` | Creating, importing, exporting and deleting keys |
| `card.crypto` | Digests, MACs, signatures, key agreement, key derivation, AES |
| `card.random` | Random bytes |
| `card.cbor`, `card.der`, `card.tlv` | Reading and writing CBOR, DER and BER-TLV |

A platform API is called like any function, and follows the same rules:

- **It returns an outcome.** Its errors are `CardError`s, such as `CardError.NotFound` for a key that does not exist. Handle them with `attempt` or `match`, as in [chapter 5](05-outcomes.md#platform-errors).
- **Results go into `inout` views.** An API that produces bytes writes them into a view you pass, and returns how many it wrote. A view that is too small is `CardError.Capacity`, and nothing is written.
- **Choices are enums.** Each family of algorithms has its own enum, such as `SignatureAlgorithm.EcdsaP256Sha256`, so passing a digest algorithm where a signature algorithm belongs is a compile error.

## The platform's errors

The platform's errors are the members of `CardError`, each with a code fixed by the Base Profile (*BP-12*):

| Member | Code | Returned when |
|---|---|---|
| `CardError.Overflow` | `0001` | A checked addition or multiplication is too large |
| `CardError.Underflow` | `0002` | A checked subtraction is too small |
| `CardError.DivisionByZero` | `0003` | A checked division or remainder by zero |
| `CardError.ConversionRange` | `0004` | `checked_convert`: the value does not fit |
| `CardError.NotFound` | `0010` | No key or operation has that identifier |
| `CardError.AlreadyExists` | `0011` | Creating a key or operation whose identifier is in use |
| `CardError.WrongResourceType` | `0012` | The identifier names the wrong kind of resource, or a key of a type the API does not accept |
| `CardError.InvalidState` | `0013` | A multi-part operation used out of order |
| `CardError.Capacity` | `0014` | No room: for another key, or in the output view |
| `CardError.Unsupported` | `0020` | An algorithm, size or value the platform does not provide |
| `CardError.Malformed` | `0021` | Input that is not well-formed, such as a key of the wrong length or out of range |

- **Each API returns only some of them.** The Base Profile's [catalog](https://github.com/cardlang/cardlang/blob/main/platform/base-catalog.txt) lists the errors of every API, and VS Code shows them when it completes a `card.…` call.
- **When several apply,** an API returns the first in a fixed order: `NotFound`, `AlreadyExists`, `WrongResourceType`, `InvalidState`, `Unsupported`, `Malformed`, `Capacity` (*BP-8*).
- **A failed call changes nothing:** no output is written, and no resource is created or deleted (*BP-7*).
- **An API never traps because of its arguments' values** (*BP-9*). Whatever it can detect, it reports as an error, which the applet can handle.
- **The host sees** category `02` and the code in the raw binding, or status word `6F00` plus the code in the ISO 7816 binding, as [chapter 7](07-host.md#one-outcome-two-encodings) showed.

## Keys are resources

A key lives inside the platform, not in a variable. The applet names it by a number of its own choosing, a `u32` other than 0, and the platform keeps the key material. The *private* or secret part of a key can never be read out by the applet or the host: the applet can only ask the platform to use it (*PLT-33*).

A key is created with a `KeySpec`, a structure the Base Profile declares, which gives its type and how long it lives:

| `KeyStorage` | The key lives |
|---|---|
| `Persistent` | Until it is deleted, across power loss |
| `Volatile` | Until the end of the session |
| `Command` | Until the end of the command that created it |

Creating or deleting a persistent key takes part in a transaction, like a persistent variable (*BP-24*): if the transaction aborts, the key was never created.

## The vault signs

The vault gets an ECDSA P-256 key, generated on the device at installation. A host can read its public key, and, once the PIN is verified, ask the vault to sign a 32-byte digest. The counter, which has had no real job since chapter 1, now counts signatures, so the increment command goes. Add the key and the two new commands, and remove `increment`:

<!-- check: program vault remove=increment -->
```cardlang
const SIGNING_KEY: u32 = 1;
const SIGNING_KEY_SPEC: KeySpec = KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Persistent };
const DIGEST_LENGTH: u32 = 32;
const SIGNATURE_LENGTH: u32 = 64;
const PUBLIC_KEY_LENGTH: u32 = 65;

function on_install() {
    transaction {
        pin[0..4] = DEFAULT_PIN;
        pin_length = DEFAULT_PIN.length;
        tries = MAX_TRIES;
        attempt card.key.generate(SIGNING_KEY, SIGNING_KEY_SPEC);
    }
    return Ok();
}

function read_public_key(data: ref u8[], response: inout u8[]) -> u32 {
    require data.length == 0 else VaultError.MalformedRequest;
    require response.length >= PUBLIC_KEY_LENGTH else VaultError.ResponseTooSmall;
    return card.key.export_public(SIGNING_KEY, inout response);
}

function sign(data: ref u8[], response: inout u8[]) -> u32 {
    require verified else VaultError.NotVerified;
    require data.length == DIGEST_LENGTH else VaultError.MalformedRequest;
    require response.length >= SIGNATURE_LENGTH else VaultError.ResponseTooSmall;
    var next: u32 = attempt checked_add(counter, 1) else VaultError.CounterExhausted;
    var length: u32 = attempt card.crypto.sign_digest(SIGNING_KEY, SignatureAlgorithm.EcdsaP256Sha256, ref data, inout response);
    counter = next;
    return Ok(length);
}
```

- **`on_install` generates the key inside its transaction.** If generating fails, `attempt` aborts the transaction, so the PIN is not set up either, and the installation fails as a whole.
- **`read_public_key` forwards** the platform's outcome: `export_public` writes the 65-byte public point and returns 65.
- **`sign` checks everything first,** including whether the counter can still go up, in the order of [chapter 5](05-outcomes.md#err-undoes-nothing). The count is stored only after the signature has succeeded, so a failed signature is not counted. `sign_digest` signs the digest as given, without hashing it again.

Then the commands: `30` reads the public key, and `2A` signs. Replace `Command`, `decode` and `process`:

<!-- check: program vault -->
```cardlang
enum Command {
    ReadCounter;
    VerifyPin;
    ChangePin;
    StoreSecret;
    ReadSecret;
    ReadPublicKey;
    Sign;
}

function decode(code: u8) -> Command {
    if code == 0x01 {
        return Ok(Command.ReadCounter);
    } else if code == 0x20 {
        return Ok(Command.VerifyPin);
    } else if code == 0x24 {
        return Ok(Command.ChangePin);
    } else if code == 0xD0 {
        return Ok(Command.StoreSecret);
    } else if code == 0xCA {
        return Ok(Command.ReadSecret);
    } else if code == 0x30 {
        return Ok(Command.ReadPublicKey);
    } else if code == 0x2A {
        return Ok(Command.Sign);
    }
    return Err(VaultError.UnsupportedCommand);
}

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length >= 1 else VaultError.MalformedRequest;
    var operation: Command = attempt decode(request[0]);
    match operation {
        Command.ReadCounter => {
            return read_counter(ref request[1..request.length], inout response);
        }
        Command.VerifyPin => {
            return verify_pin(ref request[1..request.length], inout response);
        }
        Command.ChangePin => {
            return change_pin(ref request[1..request.length], inout response);
        }
        Command.StoreSecret => {
            return store_secret(ref request[1..request.length], inout response);
        }
        Command.ReadSecret => {
            return read_secret(ref request[1..request.length], inout response);
        }
        Command.ReadPublicKey => {
            return read_public_key(ref request[1..request.length], inout response);
        }
        Command.Sign => {
            return sign(ref request[1..request.length], inout response);
        }
    }
}
```

## Testing what cannot be predicted

An ECDSA signature is different every time, and a platform may compute it in any valid way, so no test may rely on its exact bytes (*BP-30*). A scenario checks what it can: that signing succeeds with 64 bytes, with `expect ok length 64`, and everything around it.

<!-- check: scenario vault -->
```scenario
install
power_on
command 30                  # the public key: 65 bytes, 04 then X and Y
expect ok length 65
command 2A 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F
expect err app 7            # signing needs the PIN
command 20 31 32 33 34
expect ok
command 2A 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F
expect ok length 64         # a signature, whatever its bytes
command 01
expect ok 00 00 00 01       # counted
command 2A 00 01 02         # not a 32-byte digest
expect err app 1
command 2A 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F capacity 32
expect err app 3            # no room for a signature
command 01
expect ok 00 00 00 01       # and not counted
```

Whether a signature is *valid* is checked on the host, which verifies it with the public key from command `30`. The applet's tests cover the rest: that it signs only when it should, counts correctly, and fails cleanly.

## Randomness

`card.random.fill` fills a view with bytes from the platform's secure random generator, as you would need for a challenge, a nonce or a fresh identifier:

<!-- check: fragment -->
```cardlang
session challenge: u8[16];

function new_challenge(response: inout u8[]) -> u32 {
    var filled: u32 = attempt card.random.fill(inout challenge);
    response[0..challenge.length] = challenge;
    return Ok(challenge.length);
}
```

Random bytes are unpredictable on a device, but a scenario can make them repeatable with its `seed` step: [chapter 9](09-testing-and-debugging.md) shows how.

## Wiping the secret

`wipe p;` sets every element of `p` to its default value: zeros, for bytes (*STM-23*). It does what `p = fill(0);` does, but it says why: the old contents must be gone. The vault uses it when the PIN becomes blocked. A device that has had every try used up is probably in the wrong hands, so the secret goes with it. Replace `check_pin`:

<!-- check: program vault -->
```cardlang
function check_pin(candidate: ref u8[]) {
    attempt check_pin_format(ref candidate);
    require tries > 0 else VaultError.Blocked;
    verified = false;
    tries -= 1;
    var correct: bool = (candidate.length == pin_length) and equal(ref candidate, ref pin[0..pin_length]);
    if not correct {
        if tries == 0 {
            transaction {
                wipe secret;
                secret_length = 0;
            }
        }
        return Err(VaultError.WrongPin);
    }
    tries = MAX_TRIES;
    verified = true;
    return Ok();
}
```

- **The comparison is now a `bool`,** because a wrong PIN has two things to do: wipe on the last try, then report `WrongPin`.
- **`and` stops early.** When the lengths differ, `equal` is not called at all.
- **The secret and its length are wiped in one transaction,** so a power cut cannot leave a length pointing at zeros.

No scenario can see that the secret is gone: once the PIN is blocked, nothing can read the secret anyway. That is the point. A scenario can still check that the vault behaves as blocked:

<!-- check: scenario vault -->
```scenario
install
power_on
command 20 31 32 33 34
expect ok
command D0 73 65 63 72 65 74
expect ok
command 20 31 31 31 31
expect err app 4
command 20 31 31 31 31
expect err app 4
command 20 31 31 31 31      # the last try: the secret is wiped
expect err app 4
power_on
command 20 31 32 33 34      # even the right PIN is refused
expect err app 6
command CA
expect err app 7
```

## What next

- Add a command that deletes the signing key and generates a new one, with `card.key.delete` and `card.key.generate` in one transaction. Who should be allowed to run it?
- Make the vault sign a whole message instead of a digest, with `card.crypto.sign`, which hashes it for you. What limits the message's length?
- Use `card.random.fill` to give the vault a command that answers a fresh 16-byte challenge, and store it in session state for a later command to check.
