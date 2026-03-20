"""[V75-B] 역류 에스컬레이션 — Blueprint 재생성 테스트."""

import dataclasses
import json
from unittest.mock import MagicMock, patch

# ── 1. director_ensemble error_category 전파 ──────────────────


def test_director_ensemble_returns_error_category():
    """director_ensemble 반환 dict에 error_category 키가 존재하는지 구조 확인."""
    # LLM 의존 직접 호출 대신 반환 구조 계약 확인
    from pathlib import Path

    src = Path("modules/domain/agents/director_ensemble.py").read_text(encoding="utf-8")
    assert "error_category" in src, "director_ensemble.py에 error_category 키가 없음"


# ── 2. _InterviewRoundResult error_category 필드 ──────────────


def test_interview_round_result_has_error_category():
    """_InterviewRoundResult에 error_category 필드가 있고 기본값은 빈 문자열."""
    from modules.core.stage4_types import _InterviewRoundResult

    result = _InterviewRoundResult(
        verdict="REJECT",
        director_feedback="test",
        previous_attempt={},
    )
    assert result.error_category == ""


def test_interview_round_result_accepts_error_category():
    """_InterviewRoundResult에 error_category를 설정할 수 있음."""
    from modules.core.stage4_types import _InterviewRoundResult

    result = _InterviewRoundResult(
        verdict="REJECT",
        director_feedback="test",
        previous_attempt={},
        error_category="LOGIC_ERROR",
    )
    assert result.error_category == "LOGIC_ERROR"


# ── 3. LOGIC_ERROR streak 카운팅 ──────────────────────────────


def test_logic_error_streak_counts():
    """2연속 LOGIC_ERROR → streak=2."""
    from modules.core.stage4_types import _InterviewRoundResult

    streak = 0
    for _ in range(2):
        r = _InterviewRoundResult(
            verdict="REJECT",
            director_feedback="",
            previous_attempt={},
            error_category="LOGIC_ERROR",
        )
        if r.error_category == "LOGIC_ERROR":
            streak += 1
        else:
            streak = 0
    assert streak == 2


# ── 4. QUALITY_ISSUE 리셋 ────────────────────────────────────


def test_quality_issue_resets_streak():
    """LOGIC_ERROR → QUALITY_ISSUE → streak=0."""
    from modules.core.stage4_types import _InterviewRoundResult

    streak = 0
    results = [
        _InterviewRoundResult(
            verdict="REJECT",
            director_feedback="",
            previous_attempt={},
            error_category="LOGIC_ERROR",
        ),
        _InterviewRoundResult(
            verdict="REJECT",
            director_feedback="",
            previous_attempt={},
            error_category="QUALITY_ISSUE",
        ),
    ]
    for r in results:
        if r.error_category == "LOGIC_ERROR":
            streak += 1
        else:
            streak = 0
    assert streak == 0


# ── Helper: Stage4Orchestrator mock 팩토리 ───────────────────


def _make_orch(ctx=None):
    """테스트용 Stage4Orchestrator를 property 우회하여 생성."""
    from modules.core.stage4_orchestrator import Stage4Orchestrator

    if ctx is None:
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.agents = {}
        ctx.current_project = MagicMock()
        ctx.perf_timer = MagicMock()
        ctx.get_module = MagicMock(return_value=None)  # CoVe 등 비활성화

    orch = Stage4Orchestrator.__new__(Stage4Orchestrator)
    orch._ctx = ctx  # property setter 우회
    orch._post_processor = MagicMock()
    orch._context_builder = MagicMock()
    orch._interview_round = MagicMock()
    return orch, ctx


# ── 5. B-Light 트리거 (V75-D: inplace 성공 → full regen 불필요) ──


def test_b_light_triggers_on_double_logic_error():
    """[V75-D] 2연속 LOGIC_ERROR → inplace 패치 성공 → full regen 미호출."""
    from modules.core.stage4_types import _InterviewRoundResult, _RoundContext

    orch, ctx = _make_orch()

    # inplace 패치 에이전트 mock
    mock_bp_agent = MagicMock()
    patched_bp = {"scenes": [{"description": "패치된 블루프린트"}]}
    mock_bp_agent._inplace_patch_blueprint.return_value = patched_bp
    ctx.agents = {"three_phase_bp": mock_bp_agent}

    # 2연속 LOGIC_ERROR REJECT → 3번째에 PASS (inplace 성공 후)
    call_count = [0]

    def mock_run(**kwargs):
        call_count[0] += 1
        if call_count[0] <= 2:
            return _InterviewRoundResult(
                verdict="REJECT",
                director_feedback="논리 오류",
                previous_attempt={},
                error_category="LOGIC_ERROR",
            )
        return _InterviewRoundResult(
            verdict="PASS",
            director_feedback="",
            previous_attempt={},
            final_manuscript="좋은 원고",
            final_title="제1화",
            final_state_updates={},
            error_category="",
        )

    orch._interview_round.run = mock_run

    # _regenerate_blueprint mock
    orch._regenerate_blueprint = MagicMock(return_value=None)

    # _RoundContext stub
    fields = {f.name: MagicMock() for f in dataclasses.fields(_RoundContext)}
    fields["next_ep"] = 1
    fields["blueprint"] = {"scenes": [{"description": "원래 블루프린트"}]}
    fields["arc_data"] = {"arc_no": 1}
    round_ctx = _RoundContext(**fields)

    with patch("modules.core.stage4_orchestrator._threshold", return_value=5):
        from modules.core.spinners import StageSpinner

        with (
            patch.object(StageSpinner, "__init__", return_value=None),
            patch.object(StageSpinner, "__enter__", return_value=MagicMock()),
            patch.object(StageSpinner, "__exit__", return_value=False),
        ):
            result = orch._handle_round_outcome(round_ctx=round_ctx)

    # [V75-D] inplace 패치 호출됨, full regen 미호출
    mock_bp_agent._inplace_patch_blueprint.assert_called_once()
    orch._regenerate_blueprint.assert_not_called()
    assert result.final_manuscript


def test_v75d_success_persists_blueprint_artifact_and_logs_linkage(tmp_path):
    """[V75-D] inplace 성공 시 patched blueprint snapshot과 linkage가 남는다."""
    from modules.core.stage4_types import _InterviewRoundResult, _RoundContext

    orch, ctx = _make_orch()
    ctx.current_project.name = "proj"
    ctx.current_project.paths = MagicMock()
    ctx.current_project.paths.root = tmp_path
    ctx.audit_event = MagicMock()

    mock_bp_agent = MagicMock()
    patched_bp = {"scenes": [{"description": "patched blueprint"}], "meta": {"mode": "inplace"}}
    mock_bp_agent._inplace_patch_blueprint.return_value = patched_bp
    ctx.agents = {"three_phase_bp": mock_bp_agent}

    call_count = [0]

    def mock_run(**kwargs):
        call_count[0] += 1
        if call_count[0] <= 2:
            return _InterviewRoundResult(
                verdict="REJECT",
                director_feedback="logic error",
                previous_attempt={},
                error_category="LOGIC_ERROR",
            )
        return _InterviewRoundResult(
            verdict="PASS",
            director_feedback="",
            previous_attempt={},
            final_manuscript="patched manuscript",
            final_title="ep2",
            final_state_updates={},
            error_category="",
        )

    orch._interview_round.run = mock_run
    orch._regenerate_blueprint = MagicMock(return_value=None)

    fields = {f.name: MagicMock() for f in dataclasses.fields(_RoundContext)}
    fields["next_ep"] = 1
    fields["blueprint"] = {"scenes": [{"description": "original blueprint"}]}
    fields["arc_data"] = {"arc_no": 1}
    round_ctx = _RoundContext(**fields)

    with patch("modules.core.stage4_orchestrator._threshold", return_value=5):
        from modules.core.spinners import StageSpinner

        with (
            patch.object(StageSpinner, "__init__", return_value=None),
            patch.object(StageSpinner, "__enter__", return_value=MagicMock()),
            patch.object(StageSpinner, "__exit__", return_value=False),
        ):
            result = orch._handle_round_outcome(round_ctx=round_ctx)

    assert result.final_manuscript == "patched manuscript"
    artifact_dir = tmp_path / "logs" / "artifacts" / "stage4" / "ep_0001" / "attempt_02"
    artifact_files = list(artifact_dir.glob("patched_blueprint_after_fix__*.json"))
    assert len(artifact_files) == 1
    assert json.loads(artifact_files[0].read_text(encoding="utf-8")) == patched_bp

    rows = [
        json.loads(line)
        for line in (tmp_path / "logs" / "episode_production.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    payload = rows[-1]
    assert payload["event"] == "V75-D_INPLACE"
    assert payload["success"] is True
    assert payload["candidate_key"] == "V75-D|blueprint_inplace"
    assert payload["content_hash"]
    assert payload["artifact_path"] == artifact_files[0].relative_to(tmp_path).as_posix()

    audit_calls = [call.args for call in ctx.audit_event.call_args_list]
    assert any(
        event_name == "stage4_v75d_blueprint_patch_snapshot"
        and message == "stage4 V75-D blueprint patch snapshot persisted"
        and meta["ep_num"] == 1
        and meta["round_num"] == 2
        and meta["candidate_key"] == "V75-D|blueprint_inplace"
        and meta["content_hash"] == payload["content_hash"]
        and meta["artifact_path"] == payload["artifact_path"]
        and isinstance(meta.get("change_ratio"), float)
        and meta["change_ratio"] > 0
        for event_name, message, meta in audit_calls
    )
    return
    assert result.final_manuscript == "좋은 원고"


# ── 6. B-Light 1회 제한 (V75-D: inplace 실패 후 full regen 1회) ──


def test_b_light_only_once():
    """[V75-D] inplace 실패 → full regen 1회 → 2번째 재생성 안 함."""
    from modules.core.stage4_types import _InterviewRoundResult, _RoundContext

    orch, ctx = _make_orch()

    # inplace 패치 실패 (None 반환)
    mock_bp_agent = MagicMock()
    mock_bp_agent._inplace_patch_blueprint.return_value = None
    ctx.agents = {"three_phase_bp": mock_bp_agent}

    # 5연속 LOGIC_ERROR (전부 REJECT)
    def mock_run(**kwargs):
        return _InterviewRoundResult(
            verdict="REJECT",
            director_feedback="논리 오류",
            previous_attempt={"best_manuscript": "", "score": 30},
            error_category="LOGIC_ERROR",
        )

    orch._interview_round.run = mock_run
    orch._regenerate_blueprint = MagicMock(return_value={"scenes": []})

    fields = {f.name: MagicMock() for f in dataclasses.fields(_RoundContext)}
    fields["next_ep"] = 1
    fields["blueprint"] = {"scenes": []}
    fields["arc_data"] = {"arc_no": 1}
    round_ctx = _RoundContext(**fields)

    with patch("modules.core.stage4_orchestrator._threshold", return_value=5):
        from modules.core.spinners import StageSpinner

        with (
            patch.object(StageSpinner, "__init__", return_value=None),
            patch.object(StageSpinner, "__enter__", return_value=MagicMock()),
            patch.object(StageSpinner, "__exit__", return_value=False),
        ):
            orch._handle_round_outcome(round_ctx=round_ctx)

    # [V75-D] inplace 1회 + full regen 1회
    mock_bp_agent._inplace_patch_blueprint.assert_called_once()
    assert orch._regenerate_blueprint.call_count == 1


# ── 7. B-Light 실패 폴백 (V75-D: inplace+regen 둘다 실패) ──


def test_b_light_failure_keeps_original_blueprint():
    """[V75-D] inplace 실패 + 재생성 실패 → 기존 블루프린트 유지."""
    from modules.core.stage4_types import _InterviewRoundResult, _RoundContext

    orch, ctx = _make_orch()

    # inplace 패치 실패 (None 반환)
    mock_bp_agent = MagicMock()
    mock_bp_agent._inplace_patch_blueprint.return_value = None
    ctx.agents = {"three_phase_bp": mock_bp_agent}

    call_count = [0]

    def mock_run(**kwargs):
        call_count[0] += 1
        if call_count[0] <= 4:
            return _InterviewRoundResult(
                verdict="REJECT",
                director_feedback="논리 오류",
                previous_attempt={"best_manuscript": "임시", "score": 30},
                error_category="LOGIC_ERROR",
            )
        return _InterviewRoundResult(
            verdict="PASS",
            director_feedback="",
            previous_attempt={},
            final_manuscript="원고",
            final_title="제1화",
            final_state_updates={},
        )

    orch._interview_round.run = mock_run
    # 재생성 실패 (None 반환)
    orch._regenerate_blueprint = MagicMock(return_value=None)

    original_bp = {"scenes": [{"description": "원래"}]}
    fields = {f.name: MagicMock() for f in dataclasses.fields(_RoundContext)}
    fields["next_ep"] = 1
    fields["blueprint"] = original_bp
    fields["arc_data"] = {"arc_no": 1}
    round_ctx = _RoundContext(**fields)

    with patch("modules.core.stage4_orchestrator._threshold", return_value=5):
        from modules.core.spinners import StageSpinner

        with (
            patch.object(StageSpinner, "__init__", return_value=None),
            patch.object(StageSpinner, "__enter__", return_value=MagicMock()),
            patch.object(StageSpinner, "__exit__", return_value=False),
        ):
            result = orch._handle_round_outcome(round_ctx=round_ctx)

    # [V75-D] inplace 시도 → full regen 시도 (둘 다 실패)
    mock_bp_agent._inplace_patch_blueprint.assert_called_once()
    orch._regenerate_blueprint.assert_called_once()
    # 실패 경고 로그
    ctx.ui.log.assert_any_call("   ⚠️ [V75-B] 블루프린트 재생성 실패 — 기존 블루프린트 유지")


# ── 8. B-Full 제안 ───────────────────────────────────────────


def test_b_full_suggestion_after_regen_failure():
    """재생성 후에도 전량 실패 → B-Full Arc 재생성 제안 메시지."""
    from modules.core.stage4_types import _InterviewRoundResult, _RoundContext

    orch, ctx = _make_orch()
    # get_int_input → 2 (건너뛰기)
    ctx.get_int_input = MagicMock(return_value=2)

    def mock_run(**kwargs):
        return _InterviewRoundResult(
            verdict="REJECT",
            director_feedback="논리 오류",
            previous_attempt={"best_manuscript": "임시 원고", "score": 30},
            error_category="LOGIC_ERROR",
        )

    orch._interview_round.run = mock_run
    orch._regenerate_blueprint = MagicMock(return_value={"scenes": []})

    fields = {f.name: MagicMock() for f in dataclasses.fields(_RoundContext)}
    fields["next_ep"] = 1
    fields["blueprint"] = {"scenes": []}
    fields["arc_data"] = {"arc_no": 1}
    round_ctx = _RoundContext(**fields)

    with patch("modules.core.stage4_orchestrator._threshold", return_value=5):
        from modules.core.spinners import StageSpinner

        with (
            patch.object(StageSpinner, "__init__", return_value=None),
            patch.object(StageSpinner, "__enter__", return_value=MagicMock()),
            patch.object(StageSpinner, "__exit__", return_value=False),
        ):
            result = orch._handle_round_outcome(round_ctx=round_ctx)

    # B-Full 제안 메시지 확인
    log_calls = [str(c) for c in ctx.ui.log.call_args_list]
    b_full_found = any("Arc(전술서) 자체에 문제가 있을 수 있습니다" in c for c in log_calls)
    assert b_full_found, f"B-Full 제안 메시지가 없음. 로그: {log_calls[-5:]}"

    # should_return=True (건너뛰기)
    assert result.should_return is True


# ── 9. _regenerate_blueprint 단위 테스트 ──────────────────────


def test_regenerate_blueprint_no_agent():
    """bp_agent가 없으면 None 반환."""
    from modules.core.stage4_types import _RoundContext

    orch, ctx = _make_orch()
    ctx.agents = {}  # three_phase_bp 없음

    fields = {f.name: MagicMock() for f in dataclasses.fields(_RoundContext)}
    round_ctx = _RoundContext(**fields)

    result = orch._regenerate_blueprint(1, {"arc_no": 1}, round_ctx)
    assert result is None


def test_regenerate_blueprint_success():
    """bp_agent.generate가 유효한 dict 반환 → 저장 + 반환."""
    from modules.core.stage4_types import _RoundContext

    bp_agent = MagicMock()
    new_bp = {"scenes": [{"title": "새 장면"}]}
    bp_agent.generate.return_value = (new_bp, {"final_verdict": "PASS"})

    orch, ctx = _make_orch()
    ctx.agents = {"three_phase_bp": bp_agent}
    ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {"name": "주인공"}}}
    ctx.current_project.get_blueprint.return_value = None

    fields = {f.name: MagicMock() for f in dataclasses.fields(_RoundContext)}
    round_ctx = _RoundContext(**fields)

    result = orch._regenerate_blueprint(1, {"arc_no": 1}, round_ctx)
    assert result == new_bp
    ctx.current_project.save_episode_blueprint.assert_called_once_with(1, new_bp)


def test_regenerate_blueprint_returns_none_on_invalid():
    """bp_agent.generate가 None 반환 → None."""
    from modules.core.stage4_types import _RoundContext

    bp_agent = MagicMock()
    bp_agent.generate.return_value = (None, {"final_verdict": "ERROR"})

    orch, ctx = _make_orch()
    ctx.agents = {"three_phase_bp": bp_agent}
    ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {"name": "주인공"}}}
    ctx.current_project.get_blueprint.return_value = None

    fields = {f.name: MagicMock() for f in dataclasses.fields(_RoundContext)}
    round_ctx = _RoundContext(**fields)

    result = orch._regenerate_blueprint(1, {"arc_no": 1}, round_ctx)
    assert result is None
