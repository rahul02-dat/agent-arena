A batch of ECDSA signatures produced by a device with a flawed nonce generator has been pulled from a compromised telemetry pipeline. `/app/data/signatures.json` contains everything recovered from the device: the curve (`secp256k1`), the device's public key `{"x": "0x...", "y": "0x..."}`, and 55 message/signature pairs.

For each signature, a firmware debug log leaked the top `leaked_bits` bits of the nonce `k` that produced it — provided in the JSON as `leaked_msb`. Concretely, for a signature's true 256-bit nonce `k`, `leaked_msb` equals `k >> (nonce_bitlength - leaked_bits)`. No nonce is reused across signatures, and the unleaked lower bits of each nonce are otherwise uniformly random and independent.

Signatures follow the standard ECDSA construction over `secp256k1`: `r` is the x-coordinate of `k*G` reduced mod the curve order `n`, and `s = k^-1 * (h + r*d) mod n`, where `d` is the device's private key and `h` is `SHA-256(message)` (message taken as raw UTF-8 bytes, hash interpreted as a big-endian integer) reduced mod `n`. `r` and `s` are given as hex strings in `/app/data/signatures.json`.

Recover the device's private key `d`. Write it to `/app/private_key.txt` as a hex-encoded integer (a leading `0x` is optional).
