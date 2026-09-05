from pathlib import Path
from arena.evaluation.evaluator import BaseEvaluator, get_evaluator
from tasks.ecdsa_nonce_bias_001.evaluator.evaluator import ECDSANonceBiasEvaluator, G, scalar_mult


class MockEnvironment:
    def __init__(self, key_hex: str):
        self.key_hex = key_hex

    def execute(self, cmd: str, timeout: int | None = None):
        if "cat /app/private_key.txt" in cmd:
            return {"exit_code": 0, "stdout": self.key_hex, "stderr": ""}
        return {"exit_code": 0, "stdout": "", "stderr": ""}


def test_evaluator_correct_key_and_public_key_rederivation():
    # A known test private key
    priv_key_int = 0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0
    pub_point = scalar_mult(priv_key_int, G)

    protected_data = {
        "private_key_hex": hex(priv_key_int),
        "public_key": {
            "x": hex(pub_point[0]),
            "y": hex(pub_point[1]),
        },
    }

    env = MockEnvironment(key_hex=hex(priv_key_int))
    evaluator = ECDSANonceBiasEvaluator(environment=env)

    result = evaluator.evaluate(protected_data=protected_data)
    assert result["success"] is True
    assert result["score"] == 1.0
    assert result["metrics"]["format_valid"] is True
    assert result["metrics"]["matches_ground_truth"] is True
    assert result["metrics"]["rederives_public_key"] is True
    assert result["failure_reason"] is None


def test_evaluator_wrong_key_rejected():
    correct_priv_key_int = 0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0
    wrong_priv_key_int = 0x9999999999999999999999999999999999999999999999999999999999999999
    pub_point = scalar_mult(correct_priv_key_int, G)

    protected_data = {
        "private_key_hex": hex(correct_priv_key_int),
        "public_key": {
            "x": hex(pub_point[0]),
            "y": hex(pub_point[1]),
        },
    }

    env = MockEnvironment(key_hex=hex(wrong_priv_key_int))
    evaluator = ECDSANonceBiasEvaluator(environment=env)

    result = evaluator.evaluate(protected_data=protected_data)
    assert result["success"] is False
    assert result["score"] == 0.0
    assert result["metrics"]["format_valid"] is True
    assert result["metrics"]["matches_ground_truth"] is False
    assert "does not match ground truth" in result["failure_reason"]


def test_get_evaluator_factory():
    env = MockEnvironment(key_hex="0x1234")
    task_dir = Path("tasks") / "ecdsa_nonce_bias_001"

    evaluator = get_evaluator(environment=env, task_dir=task_dir)
    assert isinstance(evaluator, ECDSANonceBiasEvaluator)

    # Unknown dir returns BaseEvaluator
    fallback_evaluator = get_evaluator(environment=env, task_dir=Path("non_existent_dir"))
    assert isinstance(fallback_evaluator, BaseEvaluator)
