# 10. A real applet

The vault was written to teach. The applet in this chapter was written to do a job: it's the FIDO2 authenticator in the repository's [`examples/fido2`](https://github.com/cardlang/cardlang/tree/main/examples/fido2). We won't rewrite it. Instead we'll stop at four places in its code, each one showing an idea from the earlier chapters at work, along with a few things you haven't seen yet.

## The map

FIDO2 is the standard behind passkeys and security keys. A browser, through the operating system, asks the authenticator to create a credential for a website, and later asks it to prove that it still holds that credential by signing a challenge. The example implements CTAP 2.0, the protocol FIDO2 uses between host and authenticator, over NFC, so it's built for the ISO 7816 binding. It runs to about 780 lines in six files:

| File | Holds |
|---|---|
| `constants.card` | The constants, the error set, and the persistent and session state |
| `cbor.card` | Reading and writing CTAP's messages, which are CBOR, with `card.cbor` |
| `credentials.card` | Credentials: making and checking their IDs, and deriving their keys |
| `pin.card` | The PIN protocols, and the `clientPIN` command |
| `ctap.card` | The CTAP commands, and the dispatch between them |
| `iso7816-entry.card` | The entry point: `on_select`, and `process` |

When you read an applet someone else wrote, start at the entry point, where the host's bytes arrive. Then follow one command all the way through, and read the state it touches. The helper functions can wait until you need them.

## Stop 1: the entry point and its errors

CTAP has its own way of reporting status. Every answer starts with a one-byte CTAP status, `00` for success, followed by the data. Over NFC, that status travels inside the response data with status word `9000`, rather than as an ISO 7816 status word. This is the entry point:

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

`ctap` does the real work, and returns either the response or one of the applet's errors. The second arm uses a pattern you haven't met before. `Err(IsoError(code))` matches *any* error from the applet's error set and binds its code as a `u16` (*OUT-21*). Platform errors never match it.

The error codes were chosen with this arm in mind. Every CTAP error is declared with a code made of `91` and its CTAP status byte, such as `CtapPinInvalid = 0x9131`, so `truncate<u8>(code)` gives the byte to send. ISO 7816 applets are allowed to use the `91xx` range (*BP-52*). `status` writes that byte as the response and returns `Ok(1)`. A CTAP error therefore reaches the host as data with `9000`, which is what the protocol requires. Only errors outside CTAP, such as an unknown instruction, become real status words. A platform error falls through to the last arm, is passed on unchanged, and arrives as `6Fxx`.

Everywhere else, the applet uses its errors as [chapter 5](05-outcomes.md) describes, with `require` and `attempt`. This file is the only place where they're turned into CTAP's wire format, and it's also the only file that knows about ISO 7816. A raw-binding build would swap this file for another and keep the other five.

## Stop 2: one command, end to end

`getAssertion` is the command in which the authenticator proves it holds a credential. It checks the request, looks through the request's list for a credential that belongs to this website, counts the assertion, puts together the data to sign, and signs it:

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

The request is never copied. `index_map` records where each field of the request starts, and `read_string` returns a `Span`, a small structure holding a start and a length. Everything after that works on slices of `params`, the request itself, as in [chapter 4](04-functions-references-views.md#views). Every step that can fail is an `attempt` or a `require`, and every failure is already the right CTAP error, so reading down the left edge of the function gives you its checks in order.

The counter goes up *before* the signature is made, the opposite of the vault in chapter 8, and for a reason. A website only needs the counter to keep increasing. If signing fails after the counter has gone up, one value is skipped, which does no harm, whereas a value used twice would. And because `+=` traps when the counter reaches its maximum, every assertion after that point fails, which for this counter is the safe way to stop.

The signature is an ECDSA signature over the data, made with `card.crypto.sign`, which does the hashing itself. Its key is a credential key, loaded by the code at the next stop. The parts left out of the excerpt set the flags, convert the signature to the DER encoding CTAP expects, and write the CBOR response, with one `card.cbor.write_…` call per item.

## Stop 3: credentials without storage

An authenticator can hold credentials for any number of websites. This one stores none at all. A credential's ID, which the website keeps and sends back, carries everything needed to recreate the credential's key:

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

All the secret state is two persistent keys, generated at installation. The tag proves that an ID was made by this authenticator for this website, and the private key is derived from the ID every time it's needed. The derived key is a `Command` key ([chapter 8](08-platform.md#keys-are-resources)), so it lasts only until the command ends, however it ends, even by a trap.

### Not every HMAC is a key

A P-256 private key is a number `d` with 1 ≤ `d` < `n`, where `n`, the order of the curve, is a little below 2²⁵⁶. An HMAC is 256 random-looking bits, so roughly once in 2³² it comes out at `n` or above, and isn't a valid key at all. The platform doesn't quietly reduce it. `card.key.import` refuses it with `CardError.Malformed` (*BP-21*), and `load_credential_key` turns that one case into `false` and any other failure into an error.

What happens next depends on the command. When it's making a credential, the authenticator picks the nonce itself, so it just draws another:

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

The loop has a limit. An invalid draw happens about once in four billion tries, so four in a row would mean the random generator is broken, and the command fails rather than looping forever. Only nonces with valid keys are ever handed out, so in `getAssertion`, where the website sends the nonce back, deriving the key always works, and `require loaded` guards against something a genuine ID can't cause.

No test can make the platform reject a derived key, because finding a nonce that does so would take billions of attempts. The retry is checked by reading it, and through the platform's own check, which a test can trigger directly by importing an invalid key.

## Stop 4: two PIN counters

CTAP limits PIN guesses in two ways. Eight wrong PINs in total block the PIN for good, and after three wrong PINs in a row the device has to be switched off and on before it accepts another try. The two counters live in two kinds of state:

<!-- check: excerpt examples/fido2/constants.card -->
```cardlang
persistent pin_retries: u8;
// Consecutive wrong PINs since power-on, and the pinUvAuthToken.
session pin_failures: u8;
```

`pin_retries` has to survive power loss, so it's `persistent`. `pin_failures` has to be cleared by a power cycle, which is exactly what `session` state does, without a line of code ([chapter 6](06-state.md#four-kinds-of-storage)). The check itself follows chapter 6's rule, and its comment explains why:

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

`pin_retries -= 1` can't underflow here, because both callers `require pin_retries != 0` first. A trap would mean a bug, and the guard makes sure there isn't one. `attempt pin_mismatch();` never succeeds, since `pin_mismatch` always returns one of three errors, picked according to the two counters, and `attempt` returns it straight away. You can read the line as "on a mismatch, fail the way `pin_mismatch` says". Note too that the PIN itself is never stored. The applet keeps 16 bytes of its SHA-256 hash and compares hashes.

## How it is tested

The example has two kinds of test. `getinfo.scenario` is a short scenario to run or debug in VS Code, covering SELECT, `getInfo`, `reset`, a malformed request and an unknown instruction. `check.py` is an independent host. It runs 59 checks over a full CTAP session and checks each response with code of its own, sharing no logic with the applet. It has its own CBOR codec, its own DER parser, and its own host side of both PIN protocols.

That second kind of test is worth copying for any applet that implements a real protocol. Scenarios check that the applet behaves as you designed it. An independent host checks it against the protocol itself, which catches the cases where the design was wrong in the first place.

If you'd like to read further, `cbor.card` shows how `card.cbor` parses a message without allocating anything, using offsets into the request, and `client_pin` in `pin.card` follows the same patterns as the stops above, with more cryptography: ECDH, HKDF and AES. The [PIV example](https://github.com/cardlang/cardlang/tree/main/examples/piv) implements a smart-card standard in a different style, with status words, data objects, and `63CX` for the tries left.
