import json
import hashlib
from curve import N, G, scalar_mult, inv_mod
from fpylll import IntegerMatrix, LLL, BKZ

DATA_PATH = "/app/data/signatures.json"
OUTPUT_PATH = "/app/private_key.txt"


def sha256_int(msg: bytes) -> int:
    h = hashlib.sha256(msg).digest()
    return int.from_bytes(h, "big") % N


def build_hnp(sigs, unknown_bits, n):
    a_list, b_list = [], []
    half_K = 1 << (unknown_bits - 1)
    for sg in sigs:
        r = int(sg["r"], 16)
        s = int(sg["s"], 16)
        msb = int(sg["leaked_msb"], 16)
        h = sha256_int(sg["message"].encode())
        s_inv = inv_mod(s, n)
        a_i = (s_inv * r) % n
        b_i = (s_inv * h - (msb << unknown_bits) - half_K) % n
        a_list.append(a_i)
        b_list.append(b_i)
    return a_list, b_list


def recover_private_key(sigs, unknown_bits, Q, n=N, bkz_block=30):
    m = len(sigs)
    a_list, b_list = build_hnp(sigs, unknown_bits, n)
    half_K = 1 << (unknown_bits - 1)
    K = half_K

    rows, cols = m + 2, m + 1
    M = IntegerMatrix(rows, cols)
    for i in range(m):
        M[i, i] = n
    for i in range(m):
        M[m, i] = a_list[i]
    for i in range(m):
        val = (-b_list[i]) % n
        if val > n // 2:
            val -= n
        M[m + 1, i] = val
    M[m + 1, m] = K

    M = LLL.reduction(M)
    M = BKZ.reduction(M, BKZ.Param(block_size=bkz_block))

    for row in range(rows):
        vec = [M[row, c] for c in range(cols)]
        last = vec[m]
        if abs(last) != K:
            continue
        for sign in (1, -1):
            e = [-sign * vec[i] for i in range(m)]
            for i in range(m):
                if a_list[i] % n == 0:
                    continue
                v_star_i = ((-b_list[i]) % n - e[i]) % n
                d_cand = (inv_mod(a_list[i], n) * v_star_i) % n
                if scalar_mult(d_cand, G) == Q:
                    return d_cand
    return None


def main():
    with open(DATA_PATH) as f:
        data = json.load(f)

    leaked_bits = data["leaked_bits"]
    unknown_bits = data["nonce_bitlength"] - leaked_bits
    Qx = int(data["public_key"]["x"], 16)
    Qy = int(data["public_key"]["y"], 16)
    Q = (Qx, Qy)
    sigs = data["signatures"]

    d = recover_private_key(sigs, unknown_bits, Q)
    if d is None:
        raise SystemExit("lattice attack failed to recover the private key")

    assert scalar_mult(d, G) == Q, "recovered key does not match the public key"

    with open(OUTPUT_PATH, "w") as f:
        f.write(hex(d))


if __name__ == "__main__":
    main()
