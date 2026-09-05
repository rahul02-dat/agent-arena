"""Trusted host-side evaluator for the biased-nonce ECDSA private-key recovery task.

Operates strictly on the host. Inspects container state from the outside.
Does NOT copy test files or secrets into the container.
"""
from pathlib import Path
import json
import os
from typing import Any, Dict, Optional, Tuple

from arena.environments.base import BaseEnvironment
from arena.evaluation.evaluator import BaseEvaluator

# secp256k1 parameters
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)


def inv_mod(a: int, m: int) -> int:
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


def scalar_mult(k: int, point):
    result = None
    addend = point
    k = k % N
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


class ECDSANonceBiasEvaluator(BaseEvaluator):
    OUTPUT_PATH = "/app/private_key.txt"

    def __init__(self, environment: BaseEnvironment, task_dir: Optional[Path] = None):
        super().__init__(environment, task_dir)
        self.task_dir = Path(task_dir) if task_dir else Path(".")

    def _read_output_from_container(self) -> Tuple[bool, str]:
        """Read /app/private_key.txt from the container without modifying environment."""
        res = self.environment.execute(f"cat {self.OUTPUT_PATH}")
        if res.get("exit_code") != 0:
            return False, ""
        return True, res.get("stdout", "").strip()

    def validate_submission(self) -> Tuple[bool, Optional[str]]:
        """Validates artifact format and scalar range without checking ground truth."""
        exists, content = self._read_output_from_container()
        if not exists:
            return False, f"required artifact {self.OUTPUT_PATH} is missing"
        if not content:
            return False, f"required artifact {self.OUTPUT_PATH} is empty"

        try:
            d = int(content, 16)
        except ValueError:
            return False, f"required artifact {self.OUTPUT_PATH} is not a valid hex integer"

        if not (0 < d < N):
            return False, f"required artifact {self.OUTPUT_PATH} scalar is not in valid range (0 < d < N)"

        return True, None

    def _get_ground_truth(self, protected_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if protected_data:
            return protected_data

        env_secret = os.environ.get("ARENA_ECDSA_GROUND_TRUTH")
        if env_secret:
            try:
                return json.loads(env_secret)
            except Exception:
                pass

        ref_file = self.task_dir / "reference" / "ground_truth.json"
        if ref_file.exists():
            try:
                with open(ref_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return None

    def evaluate(
        self,
        task: Any = None,
        state: Any = None,
        protected_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Host-side evaluation of private key recovery."""
        # 1. Format and range validation
        is_valid, validation_error = self.validate_submission()
        if not is_valid:
            return {
                "success": False,
                "score": 0.0,
                "metrics": {
                    "format_valid": False,
                    "matches_ground_truth": False,
                    "rederives_public_key": False,
                },
                "failure_reason": validation_error,
            }

        _, content = self._read_output_from_container()
        d = int(content, 16)

        # 2. Retrieve protected ground truth
        gt = self._get_ground_truth(protected_data)
        if not gt:
            return {
                "success": False,
                "score": 0.0,
                "metrics": {
                    "format_valid": True,
                    "matches_ground_truth": False,
                    "rederives_public_key": False,
                },
                "failure_reason": "Protected ground truth not found for evaluator.",
            }

        expected_d = int(gt["private_key_hex"], 16)
        expected_Q = (int(gt["public_key"]["x"], 16), int(gt["public_key"]["y"], 16))

        matches_ground_truth = (d == expected_d)
        rederives_public_key = (scalar_mult(d, G) == expected_Q)

        success = matches_ground_truth and rederives_public_key
        score = 1.0 if success else 0.0

        failure_reason = None
        if not matches_ground_truth:
            failure_reason = "Recovered private key does not match ground truth."
        elif not rederives_public_key:
            failure_reason = "Recovered private key failed public-key rederivation check."

        return {
            "success": success,
            "score": score,
            "metrics": {
                "format_valid": True,
                "matches_ground_truth": matches_ground_truth,
                "rederives_public_key": rederives_public_key,
            },
            "failure_reason": failure_reason,
        }


TaskEvaluator = ECDSANonceBiasEvaluator
