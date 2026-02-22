"""Adaptive retry 핵심 동작 회귀 테스트."""

from modules.core.adaptive_retry import AdaptiveRetryManager, AdaptiveRetryStrategy, ErrorType, retry_with_feedback


def test_classify_error_timeout_and_quota():
    strategy = AdaptiveRetryStrategy()
    timeout_type = strategy.classify_error({"message": "Request timeout exceeded"})
    quota_type = strategy.classify_error({"message": "429 quota exceeded"})
    assert timeout_type == ErrorType.TIMEOUT
    assert quota_type == ErrorType.QUOTA_EXCEEDED


def test_should_retry_stops_after_timeout_limit():
    strategy = AdaptiveRetryStrategy()
    error_info = {"message": "timeout"}

    retry1, et1 = strategy.should_retry("task-timeout", error_info)
    retry2, et2 = strategy.should_retry("task-timeout", error_info)

    assert et1 == ErrorType.TIMEOUT
    assert et2 == ErrorType.TIMEOUT
    assert retry1 is True
    assert retry2 is False


def test_apply_strategy_injects_prompt_and_adjusts_temperature(monkeypatch):
    strategy = AdaptiveRetryStrategy()
    monkeypatch.setattr("modules.core.adaptive_retry.time.sleep", lambda *_: None)

    et = strategy.classify_error({"message": "quality score low", "reason": "밀도 부족", "score": 55})
    payload = strategy.get_retry_strategy("task-quality", et, {"reason": "밀도 부족", "score": 55})
    modified = strategy.apply_strategy("task-quality", "BASE_PROMPT", payload)

    assert "[QUALITY IMPROVEMENT REQUIRED]" in modified
    assert strategy.get_temperature("task-quality", 0.4) > 0.4


def test_retry_with_feedback_succeeds_on_second_attempt():
    state = {"calls": 0}

    def _fn(attempt: int, feedback: str):
        state["calls"] += 1
        if attempt == 0:
            return {"ok": False, "feedback": feedback}
        return {"ok": True, "feedback": feedback}

    def _on_success(result):
        return bool(result.get("ok"))

    def _on_failure(result, _attempt):
        return "이전 시도 보강"

    result, attempt_count, success = retry_with_feedback(
        _fn,
        max_attempts=3,
        on_failure=_on_failure,
        on_success=_on_success,
        task_name="adaptive-test",
    )
    assert success is True
    assert attempt_count == 2
    assert result["ok"] is True
    assert state["calls"] == 2


def test_adaptive_manager_recommends_ultimate_after_repeated_failures():
    manager = AdaptiveRetryManager(max_history=20)
    manager.record_failure(10, "writer", {"message": "quality issue", "reason": "밀도 부족"}, attempt=1)
    manager.record_failure(10, "writer", {"message": "quality issue", "reason": "밀도 부족"}, attempt=2)

    should, recommended = manager.should_trigger_ultimate(10, "writer")
    assert should is True
    assert recommended == "adversarial_self_play"
