# 10. A real applet

The vault was built to teach. This chapter reads an applet built to work: the FIDO2 authenticator in the repository's [`examples/fido2`](https://github.com/cardlang/cardlang/tree/main/examples/fido2). You will not rewrite it. Instead, the chapter makes four stops in its code, each showing an idea from the earlier chapters at work, and a few things that are new.

## The map

FIDO2 is the standard behind passkeys and security keys. A browser, through the operating system, asks the authenticator to create a credential for a website, and later to prove that it holds it, by signing a challenge. The example implements CTAP 2.0, FIDO2's protocol between the host and the authenticator, over NFC: so it is built for the ISO 7816 binding. It is about 780 lines in six files:

| File | Holds |
|---|---|
| `constants.card` | The constants, the error set, and the persistent and session state |
| `cbor.card` | Reading and writing CTAP's messages, which are CBOR, with `card.cbor` |
| `credentials.card` | Credentials: making and checking their IDs, and deriving their keys |
| `pin.card` | The PIN protocols, and the `clientPIN` command |
| `ctap.card` | The CTAP commands, and the dispatch between them |
| `iso7816-entry.card` | The entry point: `on_select`, and `process` |

To read an applet you did not write, start where the host's bytes come in: the entry point. Then follow one command through, and read the state it touches. The helpers can wait until you need them.

## Stop 1: the entry point and its errors

CTAP reports its own status: every answer starts with a one-byte CTAP status, `00` for success, followed by the data. On NFC, that status travels inside the response data, with status word `9000`, not as an ISO 7816 status word. Here is the entry point:

<!-- check: excerpt examples/fido2/iso7816-entry.card -->
```cardlang
command process(request: ref u8[], response: inout u8[]) -> u32 {
    require request.length >= 4 else IsoError.WrongLength;
    var ins: u8 = request[1];
    if ins == 0x12 {
        return Ok(0);
    }
    require ins == 0x10 else IsoError.InsNotSupported;
    match ctap(ref request[4..request.length], inout response) {
        Ok(count) => {
            return Ok(count);
        }
        Err(IsoError(code)) => {
            // Every error ctap() returns is a Ctap* member, whose code is 0x91 followed by the CTAP status byte.
            var ctap_status: u8 = truncate<u8>(code);
            return status(inout response, ctap_status);
        }
        Err(error) => {
            return Err(error);
        }
    }
}
```

- **`ctap` does the real work,** and returns either the response or an error of the applet's set.
- **`Err(IsoError(code))`** is a pattern you have not met: it matches *any* error of the applet's error set, and binds its code, as a `u16` (*OUT-21*). Platform errors never match it.
- **The codes are designed for this.** Every CTAP error is declared with a code `91` followed by its CTAP status byte, such as `CtapPinInvalid = 0x9131`, so `truncate<u8>(code)` is exactly the byte to send. `91xx` is a range that ISO 7816 applets may use (*BP-52*).
- **`status` writes that byte as the response, and returns `Ok(1)`.** So a CTAP error reaches the host as data, with `9000`, as the protocol requires. Only errors outside CTAP, such as a wrong instruction, become real status words.
- **A platform error,** caught by the last arm, is passed on unchanged, and becomes `6Fxx`.

The rest of the applet uses its errors as in [chapter 5](05-outcomes.md), with `require` and `attempt`. It is the one place where errors turn into CTAP's wire format. This is also the only file that knows about ISO 7816: a raw-binding build would replace it, and keep the five others.

## Stop 2: one command, end to end

`getAssertion` is the command that proves the authenticator holds a credential. It checks the request, finds a credential of this website in the request's list, counts the assertion, builds the data to sign, and signs it:

<!-- check: excerpt examples/fido2/ctap.card -->
```cardlang
function get_assertion(params: ref u8[], response: inout u8[]) -> u32 {
    var p: u32[8];
    var end: u32 = attempt index_map(ref params, 0, inout p);
    require (p[1] != 0) and (p[2] != 0) else IsoError.CtapMissingParameter;
    var rp_id: Span = attempt read_string(ref params, p[1], CborMajor.Text);
    var client_hash: Span = attempt read_string(ref params, p[2], CborMajor.Bytes);
    require client_hash.length == 32 else IsoError.CtapInvalidParameter;
// ...
    var rp_hash: u8[32];
    var n: u32 = attempt card.crypto.digest(DigestAlgorithm.Sha256, ref params[rp_id.start..rp_id.start + rp_id.length], inout rp_hash);
    require p[3] != 0 else IsoError.CtapNoCredentials;
    var id_start: u32 = attempt first_valid(ref params, p[3], ref rp_hash);
    require id_start != 0 else IsoError.CtapNoCredentials;

    sign_count += 1;
// ...
    var signed: u8[69];
    signed[0..32] = rp_hash;
    signed[32] = flags;
    signed[33..37] = encode_be(sign_count);
    signed[37..69] = params[client_hash.start..client_hash.start + 32];
    var loaded: bool = attempt load_credential_key(ref rp_hash, ref params[id_start..id_start + 32]);
    require loaded else IsoError.CtapOther;
    var raw: u8[64];
    n = attempt card.crypto.sign(TEMP_KEY, SignatureAlgorithm.EcdsaP256Sha256, ref signed, inout raw);
// ...
}
```

- **The request is never copied.** `index_map` finds where each of the request's fields starts, and `read_string` returns a `Span`, a small structure of a start and a length. Everything after works on slices of `params`, the request itself, as in [chapter 4](04-functions-references-views.md#views).
- **Every step that can fail is an `attempt` or a `require`,** and each failure is already the right CTAP error. Read down the left edge, and you read the command's checks in order.
- **The counter goes up before the signature,** unlike the vault's in chapter 8, and that is deliberate. A website only needs the counter to increase. A skipped value, if signing then fails, is harmless; a value used twice is not. And `+=` traps if the counter ever reaches its maximum, so every later assertion fails: for this counter, stopping is the safe answer.
- **The signature is ECDSA over the data,** with `card.crypto.sign`, which hashes it, and the key is a credential key, loaded by the next stop.

The part left out sets the flags, converts the signature to the DER encoding CTAP wants, and writes the CBOR response, with one `card.cbor.write_…` call per item.

## Stop 3: credentials without storage

An authenticator may hold credentials for any number of websites. This one stores none of them. A credential's ID, which the website keeps and sends back, carries everything needed to recreate the credential's key:

<!-- check: excerpt examples/fido2/credentials.card -->
```cardlang
// Non-resident credentials with derived keys. A credential ID is nonce (32 bytes) || tag (16 bytes):
//   tag = the first 16 bytes of HMAC(MAC_KEY, rpIdHash || nonce)
//   d   = HMAC(DERIVE_KEY, rpIdHash || nonce), the credential's P-256 private key
// Nothing is stored per credential. Both HMAC keys are persistent Hmac256 keys that never leave the platform.
```

<!-- check: excerpt examples/fido2/credentials.card -->
```cardlang
function load_credential_key(rp_hash: ref u8[], nonce: ref u8[]) -> bool {
    var material: u8[64];
    material[0..32] = rp_hash;
    material[32..64] = nonce;
    var derived: u8[32];
    var n: u32 = attempt card.crypto.mac(DERIVE_KEY, MacAlgorithm.HmacSha256, ref material, inout derived);
    match card.key.import(TEMP_KEY, KeySpec { type: KeyType.EcP256Private, storage: KeyStorage.Command }, ref derived) {
        Ok() => {
            return Ok(true);
        }
        Err(CardError.Malformed) => {
            return Ok(false);
        }
        Err(_) => {
            return Err(IsoError.CtapOther);
        }
    }
}
```

- **Two persistent keys, generated at installation,** are the whole secret state. The tag proves that an ID was made by this authenticator, for this website. The private key is derived from the ID each time it is needed.
- **The derived key is a `Command` key** ([chapter 8](08-platform.md#keys-are-resources)): it exists only until the command ends, however it ends, even by a trap.

### Not every HMAC is a key

A P-256 private key is a number `d` with 1 ≤ `d` < `n`, where `n`, the order of the curve, is a little below 2²⁵⁶. An HMAC is 256 uniformly random-looking bits, so about once in 2³² it is `n` or more, and not a valid key at all. The platform does not quietly reduce it: `card.key.import` refuses it, with `CardError.Malformed` (*BP-21*). `load_credential_key` turns exactly that case into `false`, and any other failure into an error.

What to do with `false` depends on the command. Making a credential, the authenticator chooses the nonce, so it simply draws another:

<!-- check: excerpt examples/fido2/ctap.card -->
```cardlang
    var credential_id: u8[48];
    var loaded: bool = false;
    var draws: u32 = 0;
    while (not loaded) and (draws < MAX_NONCE_DRAWS) {
        n = attempt card.random.fill(inout credential_id[0..32]);
        loaded = attempt load_credential_key(ref rp_hash, ref credential_id[0..32]);
        draws += 1;
    }
    require loaded else IsoError.CtapOther;
```

- **The loop is bounded.** An invalid draw is a one-in-four-billion event; four in a row would mean the random generator is broken. Then the command fails, rather than looping forever.
- **Only nonces with valid keys are ever issued.** So in `getAssertion`, where the nonce comes back from the website, deriving its key always succeeds, and `require loaded` guards a case that cannot happen with a genuine ID.

No test can make the platform reject a derived key: finding such a nonce takes billions of tries. The retry is checked by reading it, and by the platform's own check, which a test can trigger directly, by importing an invalid key.

## Stop 4: two PIN counters

CTAP limits PIN guesses in two ways: 8 wrong PINs in all block the PIN for good, and 3 wrong PINs in a row need the device to be powered off and on before the next try. The two counters live in two kinds of state:

<!-- check: excerpt examples/fido2/constants.card -->
```cardlang
persistent pin_retries: u8;
// Consecutive wrong PINs since power-on, and the pinUvAuthToken.
session pin_failures: u8;
```

`pin_retries` must survive power loss: it is `persistent`. `pin_failures` must be cleared by a power cycle, which is exactly what `session` state does, with no code at all ([chapter 6](06-state.md#four-kinds-of-storage)). The check itself follows the rule of chapter 6, and its comment says why:

<!-- check: excerpt examples/fido2/pin.card -->
```cardlang
// Check pinHashEnc against the stored PIN. The retries counter is decremented first, as one atomic persistent
// assignment (STA-11), so removing the card cannot save an attempt.
function check_pin_hash(protocol: u32, data: ref u8[], hash_at: u32) {
    var encrypted: Span = attempt read_string(ref data, hash_at, CborMajor.Bytes);
    pin_retries -= 1;
    var hash: u8[16];
    var length: u32 = attempt decrypt_secret(protocol, ref data[encrypted.start..encrypted.start + encrypted.length], inout hash);
    require length == 16 else IsoError.CtapPinAuthInvalid;
    if not equal(ref hash, ref pin_hash) {
        attempt pin_mismatch();
    }
    pin_retries = 8;
    pin_failures = 0;
    return Ok();
}
```

- **`pin_retries -= 1` cannot underflow here:** both callers first `require pin_retries != 0`. A trap would be a bug, and the guard makes sure there is none.
- **`attempt pin_mismatch();`** never succeeds: `pin_mismatch` always returns one of three errors, chosen from the two counters, so `attempt` returns it at once. It reads as "on a mismatch, fail the way `pin_mismatch` says".
- **The PIN itself is never stored.** The applet keeps 16 bytes of its SHA-256 hash, and compares hashes.

## How it is tested

The example comes with two kinds of test:

- **`getinfo.scenario`,** a short scenario to run or debug in VS Code: SELECT, `getInfo`, `reset`, a malformed request, and an unknown instruction.
- **`check.py`,** an independent host: 59 checks over a full CTAP session, each checking a response with code of its own, with no logic shared with the applet. It has its own CBOR codec, its own DER parser, and its own host side of both PIN protocols.

The second is worth copying for any applet that implements a real protocol. Scenarios check the applet's behaviour as you designed it; an independent host checks it against the protocol, which catches the cases where your design itself was wrong.

## What next

- Read `cbor.card`, and see how `card.cbor` parses a message with no allocation, using offsets into the request.
- Read `client_pin` in `pin.card`, which follows the same shapes as the stops above, with more cryptography: ECDH, HKDF and AES.
- Read the [PIV example](https://github.com/cardlang/cardlang/tree/main/examples/piv), a smart-card standard with a different style: status words, data objects, and `63CX` for the tries left.
