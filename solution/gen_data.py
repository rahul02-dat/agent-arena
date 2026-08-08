#!/usr/bin/env python3
"""Generate signatures.json for the biased-nonce ECDSA task.

Uses the existing keypair from ground_truth.json. Generates 80 ECDSA
signatures over secp256k1 with biased nonces — the top `LEAKED_BITS` bits
of each 256-bit nonce are leaked as `leaked_msb`.

Usage:
    python gen_data.py
"""
import hashlib
import json
import secrets
import sys
import os

# ── secp256k1 constants ──────────────────────────────────────────────────
P  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


def inv_mod(a, m):
    return pow(a, -1, m)


def point_add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        lam = (3 * x1 * x1) * inv_mod(2 * y1, P) % P
    else:
        lam = (y2 - y1) * inv_mod((x2 - x1) % P, P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def scalar_mult(k, point):
    result = None
    addend = point
    k = k % N
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


G = (Gx, Gy)

# ── Parameters ───────────────────────────────────────────────────────────
LEAKED_BITS = 5
NONCE_BITLENGTH = 256
NUM_SIGNATURES = 55

# ── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GT_PATH = os.path.join(SCRIPT_DIR, "..", "tests", "ground_truth.json")
OUT_PATH = os.path.join(SCRIPT_DIR, "..", "environment", "data", "signatures.json")


def sha256_int(msg: bytes) -> int:
    return int.from_bytes(hashlib.sha256(msg).digest(), "big") % N


def generate_signature(d: int, message: str):
    """Sign a message using ECDSA with a random nonce and return the
    signature along with the leaked MSB of the nonce."""
    h = sha256_int(message.encode())

    while True:
        # Generate a random nonce in [1, N-1]
        k = 1 + secrets.randbelow(N - 1)

        R = scalar_mult(k, G)
        if R is None:
            continue
        r = R[0] % N
        if r == 0:
            continue

        s = (inv_mod(k, N) * (h + r * d)) % N
        if s == 0:
            continue

        # Leak the top LEAKED_BITS bits of the nonce
        leaked_msb = k >> (NONCE_BITLENGTH - LEAKED_BITS)

        return {
            "message": message,
            "r": hex(r),
            "s": hex(s),
            "leaked_msb": hex(leaked_msb),
        }


def main():
    # Load the existing keypair
    with open(GT_PATH) as f:
        gt = json.load(f)

    d = int(gt["private_key_hex"], 16)
    Qx = int(gt["public_key"]["x"], 16)
    Qy = int(gt["public_key"]["y"], 16)
    Q = (Qx, Qy)

    # Verify the keypair is consistent
    Q_check = scalar_mult(d, G)
    assert Q_check == Q, "ground_truth.json keypair is inconsistent!"

    print(f"Generating {NUM_SIGNATURES} signatures with leaked_bits={LEAKED_BITS}...")

    signatures = []
    for i in range(NUM_SIGNATURES):
        msg = f"telemetry-record-{i:04d}"
        sig = generate_signature(d, msg)
        signatures.append(sig)
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{NUM_SIGNATURES} done")

    data = {
        "curve": "secp256k1",
        "leaked_bits": LEAKED_BITS,
        "nonce_bitlength": NONCE_BITLENGTH,
        "public_key": {
            "x": hex(Qx),
            "y": hex(Qy),
        },
        "signatures": signatures,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"Wrote {OUT_PATH}")
    print(f"  leaked_bits: {LEAKED_BITS}")
    print(f"  signatures: {NUM_SIGNATURES}")
    print(f"  leaked_msb range: [0, {(1 << LEAKED_BITS) - 1}]")

    # Quick verification: check the first signature
    sig0 = signatures[0]
    r0 = int(sig0["r"], 16)
    s0 = int(sig0["s"], 16)
    h0 = sha256_int(sig0["message"].encode())
    # Recover nonce: k = s^-1 * (h + r*d) mod n
    k0 = (inv_mod(s0, N) * (h0 + r0 * d)) % N
    R0 = scalar_mult(k0, G)
    assert R0 is not None and R0[0] % N == r0, "Self-check failed!"
    print("  Self-check: first signature verified ✓")


if __name__ == "__main__":
    main()
