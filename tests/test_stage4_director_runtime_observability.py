from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.stage4_director_runtime import Stage4DirectorRuntime, _DirectorDecisionPayload


def _make_owner():
    ui = MagicMock()
    ui.log = MagicMock()
    director = MagicMock()
    ctx = SimpleNamespace(
        ui=ui,
        perf_timer=MagicMock(),
        agents={"director": director},
    )
    return SimpleNamespace(
        ctx=ctx,
        _normalize_director_gate_semantics=MagicMock(side_effect=lambda payload: payload),
        _enforce_pass_with_fix_contract=MagicMock(side_effect=lambda payload: payload),
        _build_round_attempt_key=MagicMock(return_value="attempt-key"),
        _log_attempt_event=MagicMock(),
    )


def test_invoke_director_review_logs_wait_heartbeat():
    owner = _make_owner()
    owner.ctx.agents["director"].select_and_judge_ensemble.return_value = {
        "selected": "A",
        "verdict": "PASS",
        "final_verdict": "PASS",
        "score": 91,
        "selection_reason": "picked A",
    }
    runtime = Stage4DirectorRuntime(owner)
    runtime.build_director_input_pack = MagicMock(
        return_value=SimpleNamespace(
            advisory_summary={"memory": 2, "validation": 1},
            mandatory_context="mandatory",
            decision_core="core",
            candidate_evidence="evidence",
            reference_appendix="appendix",
        )
    )
    round_ctx = SimpleNamespace(
        genre_name="wuxia",
        blueprint={"scene_breakdown": []},
        prev_ending="ending",
        arc_pos=1,
        total_ep_in_arc=5,
        episode_digest="digest",
        prev_manuscripts_text="prev",
        story_context="story",
        preflight_advisory="advisory",
        arc_data={"arc_no": 3},
    )

    payload = runtime._invoke_director_review(
        round_ctx=round_ctx,
        round_num=1,
        next_ep=7,
        candidates=[{"manuscript": "A"}, {"manuscript": "B"}],
        validation_results=[{}, {}],
        mandatory_context="ignored",
        writing_directive="directive",
        director_feedback="feedback",
    )

    assert payload.director_result["final_verdict"] == "PASS"
    heartbeat_calls = [
        call
        for call in owner.ctx.ui.log.call_args_list
        if call.args and "Director 판정 대기" in str(call.args[0])
    ]
    assert heartbeat_calls
    assert heartbeat_calls[0].kwargs["event_kind"] == "heartbeat"
    assert heartbeat_calls[0].kwargs["meta"]["candidate_count"] == 2
    assert heartbeat_calls[0].kwargs["meta"]["advisory_total"] == 3


def test_log_director_decision_summary_logs_selection_and_gate_reason():
    owner = _make_owner()
    runtime = Stage4DirectorRuntime(owner)
    decision = _DirectorDecisionPayload(
        director_result={
            "director_verdict": "PASS_WITH_FIX",
            "gate_basis": "director_primary_pass_with_fix",
            "action_items": [],
        },
        advisory_summary={},
        director_mandatory_context="mandatory",
        selected="B",
        verdict="PASS_WITH_FIX",
        score=88,
        selection_reason="후보 B가 구조적으로 가장 안정적",
        verdict_reason="종결 리듬만 보강하면 된다",
        reason="종결 리듬만 보강하면 된다",
        error_category="PACE",
        attempt_key="attempt-key",
    )

    runtime._log_director_decision_summary(
        decision=decision,
        next_ep=7,
        round_num=1,
        arc_num=3,
    )

    log_texts = [call.args[0] for call in owner.ctx.ui.log.call_args_list if call.args]
    assert any("선택 사유:" in text for text in log_texts)
    assert any("판정 근거:" in text for text in log_texts)
    owner._log_attempt_event.assert_called_once()
