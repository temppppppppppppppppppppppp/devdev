"""T4 — /run 검증 로직 회귀 테스트.

커버 분기:
    INVALID_KEY, SUB_KEY_REQUIRED, SUB_KEY_NOT_ALLOWED,
    INVALID_SUB_KEY, RUN_ALREADY_ACTIVE, 정상 통과
"""

import pytest

from modules.api.run_validator import validate_run_request

# ─── INVALID_KEY ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_key", ["10", "33", "100", "", "x", "0x0"])
def test_invalid_key_returns_400(bad_key: str) -> None:
    result = validate_run_request(key=bad_key, sub_key=None, runner_state="idle")
    assert not result.ok
    assert result.http_status == 400
    assert result.code == "INVALID_KEY"


# ─── SUB_KEY_REQUIRED ────────────────────────────────────────────────────────

@pytest.mark.parametrize("sub_key", [None, ""])
def test_key0_missing_sub_key_returns_400(sub_key) -> None:
    result = validate_run_request(key="0", sub_key=sub_key, runner_state="idle")
    assert not result.ok
    assert result.http_status == 400
    assert result.code == "SUB_KEY_REQUIRED"


# ─── INVALID_SUB_KEY ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_sub", ["8", "99", "a", "-1"])
def test_key0_invalid_sub_key_returns_400(bad_sub: str) -> None:
    result = validate_run_request(key="0", sub_key=bad_sub, runner_state="idle")
    assert not result.ok
    assert result.http_status == 400
    assert result.code == "INVALID_SUB_KEY"


# ─── SUB_KEY_NOT_ALLOWED ─────────────────────────────────────────────────────

@pytest.mark.parametrize("key", ["1", "2", "3", "4", "5", "6", "7", "44", "77", "88", "99"])
def test_non_zero_key_with_sub_key_returns_400(key: str) -> None:
    result = validate_run_request(key=key, sub_key="1", runner_state="idle")
    assert not result.ok
    assert result.http_status == 400
    assert result.code == "SUB_KEY_NOT_ALLOWED"


# ─── RUN_ALREADY_ACTIVE ──────────────────────────────────────────────────────

@pytest.mark.parametrize("runner_state", ["starting", "running", "stopping"])
@pytest.mark.parametrize("key", ["1", "2", "4", "6", "7"])
def test_active_runner_states_block_new_run(key: str, runner_state: str) -> None:
    result = validate_run_request(key=key, sub_key=None, runner_state=runner_state)
    assert not result.ok
    assert result.http_status == 409
    assert result.code == "RUN_ALREADY_ACTIVE"


@pytest.mark.parametrize("runner_state", ["starting", "running", "stopping"])
def test_key0_active_runner_states_also_blocked(runner_state: str) -> None:
    result = validate_run_request(key="0", sub_key="1", runner_state=runner_state)
    assert not result.ok
    assert result.code == "RUN_ALREADY_ACTIVE"


# ─── 정상 통과 ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("key", ["1", "2", "3", "4", "5", "6", "7", "44", "77", "88", "99"])
def test_valid_non_zero_keys_pass(key: str) -> None:
    result = validate_run_request(key=key, sub_key=None, runner_state="idle")
    assert result.ok
    assert result.http_status == 202
    assert result.code == "OK"


@pytest.mark.parametrize("sub_key", ["0", "1", "2", "3", "4", "5", "6", "7"])
def test_key0_all_valid_sub_keys_pass(sub_key: str) -> None:
    result = validate_run_request(key="0", sub_key=sub_key, runner_state="idle")
    assert result.ok
    assert result.http_status == 202


def test_non_running_states_do_not_block() -> None:
    for state in ("idle", "error"):
        result = validate_run_request(key="2", sub_key=None, runner_state=state)
        assert result.ok, f"State '{state}' should not block"
