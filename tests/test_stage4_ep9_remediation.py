from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from modules.core.npc_drift_advisor import NpcDriftAdvisor
from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.core.stage4_outcome_runtime import Stage4OutcomeRuntime
from modules.core.world_state import WorldStateManager


def _make_interview_ctx(**overrides):
    ctx = SimpleNamespace(
        ui=MagicMock(),
        world_state=None,
        state_tracker=SimpleNamespace(npc_registry={}),
        agents={"director": MagicMock()},
        current_project=MagicMock(),
    )
    ctx.agents["director"].ask.return_value = "[]"
    for key, value in overrides.items():
        setattr(ctx, key, value)
    return ctx


def test_world_state_snapshot_prefers_current_position_as_authoritative_role():
    ws = WorldStateManager(db=MagicMock())
    ws._state["alive_npcs"]["박성호"] = {
        "role": "SW인베스트먼트 전담 PB",
        "role_at_intro": "SW인베스트먼트 전담 PB",
        "first_seen_ep": 1,
        "known_attrs": {
            "position": {
                "value": "한미증권 파생상품 데스크 팀장",
                "prev": "SW인베스트먼트 전담 PB",
                "changed_ep": 9,
            }
        },
    }

    snap = ws.get_npc_role_snapshot()["박성호"]

    assert snap["authoritative_role"] == "한미증권 파생상품 데스크 팀장"
    assert snap["authoritative_role_source"] == "known_attrs.position"
    assert snap["role_at_intro"] == "SW인베스트먼트 전담 PB"


def test_npc_drift_prompt_uses_authoritative_role_before_intro_role():
    advisor = NpcDriftAdvisor()
    text = advisor._format_snapshot_for_prompt(
        {
            "박성호": {
                "role_at_intro": "SW인베스트먼트 전담 PB",
                "authoritative_role": "한미증권 파생상품 데스크 팀장",
                "first_seen_ep": 1,
                "known_attrs": {},
            }
        },
        ["박성호"],
    )

    assert "현재기준역할: 한미증권 파생상품 데스크 팀장" in text
    assert "초기참고역할: SW인베스트먼트 전담 PB" in text


def test_interview_round_enriches_npc_drift_snapshot_from_state_tracker():
    ws = MagicMock()
    ws.get_npc_role_snapshot.return_value = {
        "박성호": {
            "role": "SW인베스트먼트 전담 PB",
            "role_at_intro": "SW인베스트먼트 전담 PB",
            "authoritative_role": "SW인베스트먼트 전담 PB",
            "authoritative_role_source": "role_at_intro",
            "first_seen_ep": 1,
            "known_attrs": {},
        }
    }
    state_tracker = SimpleNamespace(
        npc_registry={
            "박성호": {
                "position": "한미증권 파생상품 데스크 팀장",
            }
        }
    )
    ir = Stage4InterviewRound(_make_interview_ctx(world_state=ws, state_tracker=state_tracker))
    captured = {}

    drift_mock = MagicMock()

    def _capture(*, manuscript, npc_snapshots, ep_num, max_npcs):
        captured["npc_snapshots"] = npc_snapshots
        return []

    drift_mock.check.side_effect = _capture

    with patch("modules.core.npc_drift_advisor.NpcDriftAdvisor", return_value=drift_mock):
        result = ir._advisory_npc_drift(
            candidates=[{"manuscript": "박성호는 회의실 문을 열고 들어왔다."}],
            validation_results=[{}],
            next_ep=9,
        )

    assert result == []
    snap = captured["npc_snapshots"]["박성호"]
    assert snap["authoritative_role"] == "한미증권 파생상품 데스크 팀장"
    assert snap["authoritative_role_source"] == "state_tracker.position"
    assert snap["known_attrs"]["position"]["value"] == "한미증권 파생상품 데스크 팀장"


def test_retry_runtime_tf4_logs_stage_and_ep():
    ir = Stage4InterviewRound(_make_interview_ctx())

    ir.retry_runtime._resolve_retry_lane_routing(
        previous_attempt={
            "score": 82,
            "fix_scope": "partial",
            "fix_pack": {
                "patch_targets": [],
                "must_fix": ["직함 정정"],
                "do_not_regress": ["연속성 유지"],
                "success_condition": "국소 패치 가능",
                "target_kind": "local_sentence",
            },
            "prior_attempts": [
                {"fix_pack_reason": "missing_patch_targets"},
                {"fix_pack_reason": "missing_patch_targets"},
            ],
        },
        prev_manuscript="원고",
        round_num=6,
        ep_num=9,
    )

    tf4_call = next(
        call
        for call in ir.ctx.ui.log.call_args_list
        if call.args and "[TF-4] patch_targets 연속 부재" in call.args[0]
    )
    assert tf4_call.kwargs["stage"] == "stage4"
    assert tf4_call.kwargs["ep_num"] == 9
    assert tf4_call.kwargs["round_num"] == 6
    assert tf4_call.kwargs["attempt_key"] == "s4:ep9:arc0:a7"


def test_retry_runtime_tf_patch_gate_logs_stage_and_ep():
    ir = Stage4InterviewRound(_make_interview_ctx())

    ir.retry_runtime._resolve_retry_lane_routing(
        previous_attempt={
            "score": 82,
            "fix_scope": "partial",
            "fix_pack": {},
            "prior_attempts": [],
        },
        prev_manuscript="원고",
        round_num=2,
        ep_num=9,
    )

    gate_call = next(
        call
        for call in ir.ctx.ui.log.call_args_list
        if call.args and "[TF-PATCH-GATE] non-ready fix_pack" in call.args[0]
    )
    assert gate_call.kwargs["stage"] == "stage4"
    assert gate_call.kwargs["ep_num"] == 9
    assert gate_call.kwargs["round_num"] == 2
    assert gate_call.kwargs["attempt_key"] == "s4:ep9:arc0:a3"


def test_outcome_runtime_qr7_logs_stage_and_ep():
    owner = SimpleNamespace(ctx=SimpleNamespace(ui=MagicMock()))
    runtime = Stage4OutcomeRuntime(owner)
    previous_attempt = {
        "score": 88,
        "fix_scope_reasoning": "narrow patch",
    }

    runtime._apply_reject_score_trend_advisory(
        previous_attempt=previous_attempt,
        director_feedback="base feedback",
        score_history=[95, 92],
        plateau_advisory_emitted=False,
        next_ep=9,
        interview_round=6,
    )

    qr7_call = next(
        call
        for call in owner.ctx.ui.log.call_args_list
        if call.args and "[QR-7]" in call.args[0]
    )
    assert qr7_call.kwargs["stage"] == "stage4"
    assert qr7_call.kwargs["ep_num"] == 9
    assert qr7_call.kwargs["round_num"] == 6
    assert qr7_call.kwargs["attempt_key"] == "s4:ep9:arc0:a7"
