"""Verifier for the biased-nonce ECDSA private-key recovery task.

All tests read the single output the instruction asks for:
`/app/private_key.txt`, a hex-encoded integer private key.

The ground-truth comparison uses `ground_truth.json` (secret to the agent).
The cross-check test for rederiving the public key also derives its expectations
from the immutable `ground_truth.json` file.
"""
import hashlib
import json

OUTPUT_PATH = "/app/private_key.txt"
GROUND_TRUTH_PATH = "/tests/ground_truth.json"

# --- minimal secp256k1 arithmetic, independent of anything in solution/ ---
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)


def _point_add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        lam = (3 * x1 * x1) * pow(2 * y1, -1, P) % P
    else:
        lam = (y2 - y1) * pow((x2 - x1) % P, -1, P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def _scalar_mult(k, point):
    result = None
    addend = point
    k = k % N
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _read_recovered_private_key():
    with open(OUTPUT_PATH) as f:
        content = f.read().strip()
    return int(content, 16)


def _ground_truth():
    with open(GROUND_TRUTH_PATH) as f:
        return json.load(f)


def test_output_file_is_a_valid_hex_integer():
    """Checks /app/private_key.txt exists and parses as a hex-encoded integer, as instructed."""
    d = _read_recovered_private_key()
    assert isinstance(d, int)
    assert 0 < d < N


def test_recovered_key_matches_ground_truth():
    """Checks the recovered private key exactly matches the key used to generate the dataset."""
    d = _read_recovered_private_key()
    gt = _ground_truth()
    expected = int(gt["private_key_hex"], 16)
    assert d == expected


def test_recovered_key_rederives_the_public_key():
    """Robustness check: scalar-multiplying the recovered key by the curve base
    point must reproduce the public key from ground_truth.json."""
    d = _read_recovered_private_key()
    gt = _ground_truth()
    expected_Q = (int(gt["public_key"]["x"], 16), int(gt["public_key"]["y"], 16))
    assert _scalar_mult(d, G) == expected_Q
