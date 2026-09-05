from tasks.ecdsa_nonce_bias_001.evaluator.evaluator import ECDSANonceBiasEvaluator, N


class MockEnvironment:
    def __init__(self, file_content: str | None = None, file_exists: bool = True):
        self.file_content = file_content
        self.file_exists = file_exists

    def execute(self, cmd: str, timeout: int | None = None):
        if "cat /app/private_key.txt" in cmd:
            if not self.file_exists:
                return {"exit_code": 1, "stdout": "", "stderr": "cat: /app/private_key.txt: No such file"}
            return {"exit_code": 0, "stdout": self.file_content or "", "stderr": ""}
        return {"exit_code": 0, "stdout": "", "stderr": ""}


def test_missing_private_key_rejected():
    env = MockEnvironment(file_exists=False)
    evaluator = ECDSANonceBiasEvaluator(environment=env)

    is_valid, reason = evaluator.validate_submission()
    assert is_valid is False
    assert "missing" in reason.lower()

    # Evaluator.evaluate must also fail without crashing
    res = evaluator.evaluate()
    assert res["success"] is False
    assert res["score"] == 0.0
    assert "missing" in res["failure_reason"].lower()


def test_empty_private_key_rejected():
    env = MockEnvironment(file_content="", file_exists=True)
    evaluator = ECDSANonceBiasEvaluator(environment=env)

    is_valid, reason = evaluator.validate_submission()
    assert is_valid is False
    assert "empty" in reason.lower()

    res = evaluator.evaluate()
    assert res["success"] is False
    assert res["score"] == 0.0
    assert "empty" in res["failure_reason"].lower()


def test_whitespace_only_private_key_rejected():
    env = MockEnvironment(file_content="   \n  \t ", file_exists=True)
    evaluator = ECDSANonceBiasEvaluator(environment=env)

    is_valid, reason = evaluator.validate_submission()
    assert is_valid is False
    assert "empty" in reason.lower()


def test_invalid_hex_private_key_rejected():
    env = MockEnvironment(file_content="not_a_hex_integer", file_exists=True)
    evaluator = ECDSANonceBiasEvaluator(environment=env)

    is_valid, reason = evaluator.validate_submission()
    assert is_valid is False
    assert "not a valid hex integer" in reason.lower()


def test_out_of_range_private_key_rejected():
    # d = 0
    env_zero = MockEnvironment(file_content="0x0", file_exists=True)
    evaluator_zero = ECDSANonceBiasEvaluator(environment=env_zero)
    is_valid, reason = evaluator_zero.validate_submission()
    assert is_valid is False
    assert "valid range" in reason.lower()

    # d >= N
    env_large = MockEnvironment(file_content=hex(N + 1), file_exists=True)
    evaluator_large = ECDSANonceBiasEvaluator(environment=env_large)
    is_valid, reason = evaluator_large.validate_submission()
    assert is_valid is False
    assert "valid range" in reason.lower()


def test_valid_scalar_format_accepted():
    valid_scalar_hex = "0x123456789abcdef"
    env = MockEnvironment(file_content=valid_scalar_hex, file_exists=True)
    evaluator = ECDSANonceBiasEvaluator(environment=env)

    is_valid, reason = evaluator.validate_submission()
    assert is_valid is True
    assert reason is None
