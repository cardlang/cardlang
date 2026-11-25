# 8. Using the platform

Up to now the vault has used nothing but the language. Real applets rely on the platform for the things the language leaves out on purpose, namely keys, cryptography and randomness. In this chapter the vault gets a signing key that never leaves the device, and learns to wipe its secret when the PIN is blocked.

## The platform's APIs

The platform's services are functions named `card.<family>.<name>`, described in the Base Profile. You'll find every one of them, with its exact signature, in the [platform reference](reference-platform.md). They come in these families:

| Family | For |
|---|---|
| `card.key` | Creating, importing, exporting and deleting keys |
| `card.crypto` | Digests, MACs, signatures, key agreement, key derivation, AES |
| `card.random` | Random bytes |
| `card.cbor`, `card.der`, `card.tlv` | Reading and writing CBOR, DER and BER-TLV |

You call a platform API like any other function, and the same rules apply. It returns an outcome, and its errors are `CardError`s, such as `CardError.NotFound` for a key that doesn't exist, which you handle with `attempt` or `match` as in [chapter 5](05-outcomes.md#platform-errors). An API that produces bytes writes them into an `inout` view you pass in, and returns how many it wrote. If the view is too small, you get `CardError.Capacity` and nothing is written. Each family of algorithms has an enum of its own, such as `SignatureAlgorithm.EcdsaP256Sha256`, so passing a digest algorithm where a signature algorithm should go doesn't compile.

## The platform's errors

The platform's errors are the members of `CardError`, such as `CardError.NotFound` and `CardError.Capacity`, and the Base Profile fixes a code for each (*BP-12*). The [platform reference](reference-platform.md#the-platforms-errors) has the full list with codes, and also shows which errors each API can return. VS Code shows them too, when it completes a `card.…` call.

When more than one error applies, an API returns the first in a fixed order: `NotFound`, `AlreadyExists`, `WrongResourceType`, `InvalidState`, `Unsupported`, `Malformed`, `Capacity` (*BP-8*). A call that fails changes nothing, so no output is written and no resource is created or deleted (*BP-7*). And an API never traps because of the values of its arguments (*BP-9*). Anything it can detect, it reports as an error the applet can handle. The host sees category `02` and the code in the raw binding, or status word `6F00` plus the code in the ISO 7816 binding, as in [chapter 7](07-host.md#one-outcome-two-encodings).

## Keys are resources

A key lives inside the platform, not in a variable. The applet refers to it by a number of its own choosing, any `u32` except 0, and the platform keeps the key material. Neither the applet nor the host can ever read out the *private* or secret part of a key. The applet can only ask the platform to use it (*PLT-33*).

You create a key with a `KeySpec`, a structure declared by the Base Profile, which gives the key's type and how long it lives:

| `KeyStorage` | The key lives |
|---|---|
| `Persistent` | Until it is deleted, across power loss |
| `Volatile` | Until the end of the session |
| `Command` | Until the end of the command that created it |

Creating or deleting a persistent key takes part in a transaction, just like writing a persistent variable (*BP-24*). If the transaction aborts, the key was never created.

## The vault signs

The vault gets an ECDSA P-256 key, generated on the device when the applet is installed. A host can read the key's public half, and once the PIN has been verified it can ask the vault to sign a 32-byte digest. The counter, which hasn't had a real job since chapter 1, now counts signatures, so the increment command goes. Add the key and the two new commands, and remove `increment`:

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

`on_install` generates the key inside its transaction. If generating it fails, `attempt` aborts the transaction, the PIN isn't set up either, and the whole installation fails. `read_public_key` simply forwards what the platform returns: `export_public` writes the 65-byte public point and returns 65.

`sign` does all its checks first, including whether the counter can still go up, in the order [chapter 5](05-outcomes.md#err-undoes-nothing) recommends. It stores the new count only after the signature has succeeded, so a failed signature isn't counted. `sign_digest` signs the digest it's given, without hashing it again.

The new commands are `30`, which reads the public key, and `2A`, which signs. Replace `Command`, `decode` and `process`:

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

An ECDSA signature comes out different every time, and a platform is free to compute it in any valid way, so no test can rely on its exact bytes (*BP-30*). A scenario checks what it can instead. `expect ok length 64` confirms that signing succeeded with 64 bytes, and the other steps check everything around it:

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

Whether a signature is actually *valid* is for the host to check, using the public key from command `30`. The applet's own tests cover the rest: it signs only when it should, counts correctly, and fails cleanly.

## Randomness

`card.random.fill` fills a view with bytes from the platform's secure random generator, which is what you need for a challenge, a nonce or a fresh identifier:

<!-- check: fragment -->
```cardlang
session challenge: u8[16];

function new_challenge(response: inout u8[]) -> u32 {
    var filled: u32 = attempt card.random.fill(inout challenge);
    response[0..challenge.length] = challenge;
    return Ok(challenge.length);
}
```

On a device the bytes are unpredictable, but a scenario can make them repeatable with its `seed` step, which [chapter 9](09-testing-and-debugging.md) shows.

## Wiping the secret

`wipe p;` sets every element of `p` back to its default value, which for bytes means zero (*STM-23*). The effect is the same as `p = fill(0);`, but `wipe` also says why you're doing it, because the old contents have to go. The vault uses it when the PIN becomes blocked. A device whose tries have all been used up has probably fallen into the wrong hands, so the secret goes with it. Replace `check_pin`:

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

The comparison has become a `bool`, because a wrong PIN now has two things to do: wipe the secret on the last try, and then report `WrongPin`. `and` stops early, so `equal` isn't even called when the lengths differ. The secret and its length are wiped in one transaction, so a power cut can't leave behind a length that points at zeros.

No scenario can see that the secret has gone, because once the PIN is blocked nothing can read the secret anyway, wiped or not. What a scenario can check is that the vault behaves as blocked:

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
