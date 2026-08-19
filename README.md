# ECDSA Nonce Bias Private Key Recovery

A security cryptanalysis evaluation task for recovering a 256-bit ECDSA private key over the `secp256k1` elliptic curve from a batch of signatures produced with biased nonces.

## Overview

In ECDSA signing implementations, per-signature nonces $k$ must be strictly secret, uniform, and independent. When a flawed nonce generator leaks partial bits (even a tiny fraction per signature), the underlying private key $d$ can be recovered by casting the system of signature equations into an instance of the **Hidden Number Problem (HNP)** and solving it via lattice reduction.

This task models a side-channel / firmware leak scenario:
- **Curve**: `secp256k1`
- **Leak Model**: Top 5 bits of each 256-bit nonce $k$ are known (`leaked_msb = k >> 251`).
- **Signature Count**: 55 message/signature pairs (providing $55 \times 5 = 275$ bits of leaked information for a 256-bit key).
- **Attack Vector**: HNP formulation using Kannan's embedding technique and lattice reduction (LLL + BKZ block size $\ge 30$) via `fpylll`.

---

## Directory Structure

```text
.
├── instruction.md             # Task description provided to the agent/solver
├── task.toml                  # Benchmark task metadata and resource configuration
├── environment/
│   ├── Dockerfile             # Docker container definition (Python 3.12, fpylll, cysignals)
│   └── data/
│       └── signatures.json    # Recovered signatures, public key, and leaked nonce MSBs
├── solution/
│   ├── curve.py               # Pure-Python secp256k1 elliptic curve arithmetic
│   ├── gen_data.py            # Generator script to build synthetic signature datasets
│   ├── solve.py               # Reference solver (HNP lattice construction & BKZ reduction)
│   └── solve.sh               # Executable script entrypoint for the solver
└── tests/
    ├── ground_truth.json      # Ground-truth private/public keypair (secret to verifier)
    ├── test_outputs.py        # Pytest verifier for output format, correctness, and scalar mult
    └── test.sh                # Test runner script writing verification rewards
```

---

## Mathematical Formulation & Cryptanalysis

### 1. ECDSA Relation to HNP
For signature $i$, standard ECDSA over `secp256k1` defines:
$$s_i \equiv k_i^{-1} (h_i + r_i d) \pmod n$$

Solving for nonce $k_i$:
$$k_i \equiv s_i^{-1} h_i + s_i^{-1} r_i d \pmod n$$

Decomposing the nonce $k_i$ into known high bits ($\text{msb}_i$) and unknown low bits ($e_i$):
$$k_i = \text{msb}_i \cdot 2^{u} + 2^{u-1} + e_i \quad \text{where } |e_i| \le 2^{u-1}$$
here $u = 256 - 5 = 251$ is the number of unknown low bits per nonce.

Rearranging terms yields linear congruences for the hidden private key $d$:
$$a_i d + b_i \equiv e_i \pmod n$$
where:
- $a_i = s_i^{-1} r_i \pmod n$
- $b_i = s_i^{-1} h_i - \text{msb}_i \cdot 2^u - 2^{u-1} \pmod n$

### 2. Kannan's Embedding Matrix Construction
For $m = 55$ signatures, an $(m+2) \times (m+1)$ basis matrix $M$ is constructed:

$$
M = \begin{pmatrix}
n & 0 & \dots & 0 & 0 \\
0 & n & \dots & 0 & 0 \\
\vdots & \vdots & \ddots & \vdots & \vdots \\
0 & 0 & \dots & n & 0 \\
a_1 & a_2 & \dots & a_m & 0 \\
-b_1 & -b_2 & \dots & -b_m & K
\end{pmatrix}
$$

where $K = 2^{u-1} = 2^{250}$ scales the target vector so that the true error vector $(e_1, e_2, \dots, e_m, K)$ emerges as an exceptionally short vector in the reduced lattice.

### 3. Lattice Reduction & Key Extraction
- **Lattice Gap**: At 5 leaked bits per signature, plain LLL reduction fails and BKZ with block size 20 is unreliable.
- **Reduction**: The solver uses `BKZ.reduction(M, BKZ.Param(block_size=30))` from `fpylll`.
- **Key Reconstruction**: The row containing $K$ at its final index yields the error vector $(e_1, \dots, e_m)$. The private key $d$ is recovered via:
  $$d \equiv a_i^{-1} ((-b_i \bmod n) - e_i) \pmod n$$
  and validated against the public key $Q = d \cdot G$.

---

## Setup & Running

### Requirements
- Python 3.12+
- C compiler & dependencies (`build-essential`)
- `fpylll` (v0.6.4), `cysignals` (v1.12.6), `pytest` (v8.3.4), `pytest-json-ctrf`

### Local Execution
To run the reference solution:
```bash
python3 solution/solve.py
```
Or execute via the shell script:
```bash
./solution/solve.sh
```
This reads `/app/data/signatures.json` and outputs the hex-encoded key to `/app/private_key.txt`.

### Docker Execution
Build and run the evaluation environment:
```bash
docker build -t ecdsa-nonce-bias environment/
docker run --rm ecdsa-nonce-bias
```

### Data Generation
To regenerate signatures from the ground truth keypair:
```bash
python3 solution/gen_data.py
```

### Running Tests / Verifier
To execute the task verifier suite:
```bash
./tests/test.sh
```

---

## Verification

The verifier ([tests/test_outputs.py](file:///Users/rahulmac/Documents/Projects/projects/Cryptography/tests/test_outputs.py)) validates the output file `/app/private_key.txt` using three strict checks:
1. **Format Validation**: Confirms the file contains a valid hex-encoded integer in $(0, n)$.
2. **Ground Truth Comparison**: Checks exact match against `ground_truth.json`.
3. **Public Key Rederivation**: Multiplies the recovered key $d$ by the `secp256k1` base point $G$ and confirms $d \cdot G = Q$.
