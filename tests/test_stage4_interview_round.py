"""[B-1-3] Stage4InterviewRound unit tests."""

import concurrent.futures
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

from modules.core import stage4_episode_logging as s4_episode_logging
from modules.core.context_advisor import RetrievalPlan, RetrievalSlot, RetrievalSources
from modules.core.session_logger import SessionLogger
from modules.core.stage4_context import Stage4Context
from modules.core.stage4_director_runtime import _DirectorInputPackResult
from modules.core.stage4_interview_round import (
    Stage4InterviewRound,
    _RoundOutcomeTracePayload,
    _Stage4AttemptPreludePayload,
)
from modules.core.stage4_orchestrator import Stage4Orchestrator, _RoundContext
from modules.core.stage4_reject_runtime import _RejectLoggingPayload


def _make_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.name = "test_project"
    ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
    ctx.current_project.db = MagicMock()
    ctx.current_project.db.get_recent_manuscripts.return_value = []
    ctx.current_project.db.get_manuscript.return_value = {"content": "이전 원고"}
    ctx.current_project.db.load_state_log.return_value = None
    ctx.state_tracker = MagicMock()
    ctx.state_tracker.npc_registry = {}
    ctx.state_tracker.item_state_registry = {}
    ctx.state_tracker.get_npc_change_history.return_value = []
    ctx.state_tracker.check_destroyed_entity_in_manuscript.return_value = []
    ctx.state_tracker.in_world_timeline = []
    ctx.state_tracker.check_time_consistency.return_value = []
    ctx.agents = {"director": MagicMock()}
    ctx.context_advisor = None
    ctx.memory = None
    ctx.adaptive_manager = None
    ctx.failure_learner = None
    ctx.quality_dashboard = None
    ctx.enrich_director_result = None
    ctx.get_module = MagicMock(return_value=None)
    return ctx


def _make_round_ctx():
    chief_writer = MagicMock()
    chief_writer.generate_ensemble.return_value = []
    chief_writer.patch_with_feedback.return_value = []
    chief_writer.regenerate_with_feedback.return_value = []

    manuscript_validator = MagicMock()
    manuscript_validator.validate_all_candidates.return_value = []
    consistency_validator = MagicMock()
    consistency_validator.validate.return_value = {"violations": [], "score_penalty": 0}
    blocking_validator = MagicMock()
    blocking_validator.validate.return_value = {"failures": []}
    continuity_validator = MagicMock()
    continuity_validator.validate.return_value = {"violations": [], "warnings": []}
    continuity_validator.check_frustration_streak.return_value = []

    return _RoundContext(
        chief_writer=chief_writer,
        manuscript_validator=manuscript_validator,
        consistency_validator=consistency_validator,
        blocking_validator=blocking_validator,
        continuity_validator=continuity_validator,
        next_ep=1,
        blueprint={"integrated_scenario": "테스트"},
        arc_data={"arc_no": 1},
        arc_pos=1,
        total_ep_in_arc=10,
        arc_tactical="전술",
        prev_text="이전 원고",
        prev_ending="엔딩",
        prev_manuscripts_text="",
        episode_digest="",
        hud_report="HUD",
        current_inventory=[],
        current_martial_arts=[],
        dead_npcs=[],
        item_acquisition_timeline="",
        chain_link_section="",
        world_state_summary="",
        purism_prompt="",
        genre_name="무협",
        npc_equipment_summary="",
        effective_anti_trope="",
        intro_dna="CYNICAL",
        story_context="",
        style_guide="",
        reference_anchor_prompt="",
        mandatory_context="",
        justification_prompt="",
        reflexion_prompt="",
        preflight_advisory="",
    )


@dataclass(slots=True)
class _TestPassEpisodeLogRequest:
    ep_num: int
    round_num: int
    chief_writer: object
    director_result: dict
    trace_director_result: object
    director_feedback: str
    initial_verdict: str
    initial_score: int
    final_verdict: str
    final_score: int
    is_patch: bool
    is_patch_fallback: bool
    tot_used: bool
    mad_used: bool
    validation_warnings: list[str]
    final_warnings: list[str]
    patch_trace: dict
    logging_payload: object
    selection_artifact_meta: dict
    arc_num: int
    asp_manuscript: str


def _normalize_test_pass_episode_log_request(*, request, session_id=None):
    trace_verdict_reason = None
    if isinstance(request.trace_director_result, dict):
        trace_verdict_reason = request.trace_director_result.get("verdict_reason")
    return s4_episode_logging.Stage4PassEpisodeLogRequest(
        ep_num=request.ep_num,
        round_num=request.round_num,
        arc_num=request.arc_num,
        director_result=request.director_result,
        director_feedback=request.director_feedback,
        trace_verdict_reason=trace_verdict_reason,
        initial_verdict=request.initial_verdict,
        initial_score=request.initial_score,
        final_verdict=request.final_verdict,
        final_score=request.final_score,
        is_patch=request.is_patch,
        is_patch_fallback=request.is_patch_fallback,
        tot_used=request.tot_used,
        mad_used=request.mad_used,
        asp_used=bool(request.asp_manuscript),
        model_tier=getattr(request.chief_writer, "model_tier", None),
        validation_warnings=request.validation_warnings,
        final_warnings=request.final_warnings,
        patch_trace=request.patch_trace,
        session_runtime_advisory=request.logging_payload.session_runtime_advisory,
        session_retry_directives=request.logging_payload.session_retry_directives,
        log_artifact_meta=request.logging_payload.log_artifact_meta,
        selection_artifact_meta=request.selection_artifact_meta,
        session_id=session_id,
    )


def _call_pass_log_builder(builder, request, *, session_id=None):
    return builder(request=_normalize_test_pass_episode_log_request(request=request, session_id=session_id))


class _AppTrapInterviewRound(Stage4InterviewRound):
    @property
    def app(self):
        raise AssertionError("Stage4InterviewRound should not access self.app")


def _candidate():
    return {"manuscript": "테스트 원고 " * 300, "strategy_name": "balanced", "title": "테스트"}


def _validation_result():
    return {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 2000}}


def _local_fix_pack(*patch_targets: str, target_kind: str = "entity_ref"):
    targets = list(patch_targets) or ["opening_location_name"]
    return {
        "patch_targets": targets,
        "must_fix": [f"{targets[0]} fact correction"],
        "do_not_regress": ["scene mood", "timeline", "blocking"],
        "success_condition": "Only the listed anchors are corrected while scene semantics stay intact.",
        "target_kind": target_kind,
    }


def _writing_directive_stub(*, ending_style="", expression_ban=None, emotion_required=""):
    directive = MagicMock()
    directive.ending_style = ending_style
    directive.expression_ban = expression_ban or []
    directive.emotion_required = emotion_required
    directive.is_empty.return_value = not any((ending_style, directive.expression_ban, emotion_required))
    return directive


class TestInterviewRoundInit:
    def test_init_with_ctx(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        assert ir.ctx is ctx
        assert ir.time_warnings == []

    def test_lazy_init_via_orchestrator(self):
        app = MagicMock()
        ctx = _make_ctx()
        orch = Stage4Orchestrator(app, context=ctx)
        ir = orch.interview_round
        assert isinstance(ir, Stage4InterviewRound)
        assert ir.ctx is ctx

    def test_lazy_init_singleton(self):
        app = MagicMock()
        ctx = _make_ctx()
        orch = Stage4Orchestrator(app, context=ctx)
        assert orch.interview_round is orch.interview_round


class TestInterviewRoundHelpers:
    def test_inherit_attempt_history_appends_previous_attempt(self):
        ir = Stage4InterviewRound(_make_ctx())

        history = ir._inherit_attempt_history(
            {
                "strategy": "A",
                "score": 61,
                "rejection_reason": "연속성 실패",
                "reject_bucket": "constraint_violation",
                "prior_attempts": [{"strategy": "B", "score": 48, "rejection_reason": "분량 부족"}],
            }
        )

        assert len(history) == 2
        assert history[-1]["strategy"] == "A"
        assert history[-1]["reject_bucket"] == "constraint_violation"

    def test_extract_fix_feedback_keeps_reasoning_and_open_review(self):
        ir = Stage4InterviewRound(_make_ctx())

        feedback = ir._extract_fix_feedback(
            {
                "action_items": ["첫 장면 감정선 조정"],
                "fix_scope_reasoning": "국소 수정으로 해결 가능",
                "open_review": "주인공 목소리가 중반에 흔들립니다.",
                "feedback": {"issues": ["[자유 리뷰] 톤이 흔들립니다.", "장면 전환이 급함"]},
            }
        )

        assert "[핵심 수정 지시]" in feedback
        assert "[수정 범위 근거]" in feedback
        assert "[Director 자유 리뷰]" in feedback
        assert "장면 전환이 급함" in feedback

    def test_extract_fix_feedback_includes_contradiction_details(self):
        ir = Stage4InterviewRound(_make_ctx())

        feedback = ir._extract_fix_feedback(
            {
                "action_items": ["이름 표기만 정정"],
                "contradiction_details": [
                    {
                        "severity": "CRITICAL",
                        "type": "고유명사",
                        "current_violation": "한태준으로 표기됨",
                        "fix_suggestion": "한진호로 치환",
                    }
                ],
            }
        )

        assert "[모순 세부]" in feedback
        assert "한태준으로 표기됨" in feedback
        assert "한진호로 치환" in feedback

    def test_retry_feedback_provenance_includes_contradiction_details(self):
        ir = Stage4InterviewRound(_make_ctx())

        provenance = ir._build_retry_feedback_provenance(
            director_result={
                "feedback": {"issues": ["이름 일관성 수정"]},
                "contradiction_details": [
                    {
                        "severity": "CRITICAL",
                        "type": "고유명사",
                        "current_violation": "한태준으로 표기됨",
                        "fix_suggestion": "한진호로 치환",
                    }
                ],
            },
            director_feedback="",
            selected_validation={},
            round_num=1,
        )

        assert "[모순 세부]" in provenance["merged_feedback"]
        assert "한태준으로 표기됨" in provenance["director_feedback_text"]

    def test_retry_feedback_provenance_includes_quality_signal_warnings(self):
        ir = Stage4InterviewRound(_make_ctx())

        provenance = ir._build_retry_feedback_provenance(
            director_result={"feedback": {}},
            director_feedback="",
            selected_validation={
                "quality_signal_warnings": [
                    "ai_slop score 1.20 (recent median 0.40) / hits=그야말로x2",
                    "dialogue_ratio 24% < style target 40%",
                ]
            },
            round_num=1,
        )

        assert "[STYLE] ai_slop score 1.20" in provenance["evidence_summary"]
        assert "[STYLE] dialogue_ratio 24% < style target 40%" in provenance["merged_feedback"]

    def test_retry_feedback_provenance_includes_structured_validation_handoff(self):
        ir = Stage4InterviewRound(_make_ctx())

        provenance = ir._build_retry_feedback_provenance(
            director_result={"feedback": {}},
            director_feedback="",
            selected_validation={
                "npc_drift_warnings": [
                    {
                        "npc": "연홍",
                        "field": "말투",
                        "expected": "반말",
                        "found_in_ms": "존댓말",
                    }
                ],
                "numeric_consistency_warnings": [
                    {
                        "severity": "MAJOR",
                        "text": "[수치 불일치] 원고 '포지션 60억' vs FactLedger '포지션'=40억",
                    }
                ],
                "coverage_warnings": ["missing_relation_slice"],
            },
            round_num=1,
        )

        assert "[NPC] 연홍 말투:" in provenance["evidence_summary"]
        assert "[FACT] [수치 불일치]" in provenance["merged_feedback"]
        assert "[COVERAGE] 관계 의미 질의가 빠졌다." in provenance["merged_feedback"]

    def test_retry_feedback_provenance_tags_numeric_carryover_authority_warning(self):
        ir = Stage4InterviewRound(_make_ctx())

        provenance = ir._build_retry_feedback_provenance(
            director_result={"feedback": {}},
            director_feedback="",
            selected_validation={
                "numeric_consistency_warnings": [
                    {
                        "severity": "MAJOR",
                        "category": "numeric_carryover_authority",
                        "text": "[numeric carryover authority mismatch] 원고 '자산 200억' vs resumed FactLedger 'total_assets'=0.1억",
                    }
                ],
            },
            round_num=1,
        )

        assert "[FACT] [numeric_carryover_authority]" in provenance["merged_feedback"]

    def test_retry_feedback_provenance_preserves_full_validation_detail_without_caps(self):
        ir = Stage4InterviewRound(_make_ctx())
        long_truth_warning = "timeline mismatch " * 18
        long_violation = "structural contradiction " * 16

        provenance = ir._build_retry_feedback_provenance(
            director_result={"feedback": {}},
            director_feedback="",
            selected_validation={
                "truth_gate_warnings": [{"severity": "MAJOR", "text": long_truth_warning}],
                "structured_violations": [{"reason": long_violation}],
                "quality_signal_warnings": ["style-a", "style-b", "style-c", "style-d"],
                "npc_drift_warnings": [
                    {"npc": "npc1", "field": "tone", "expected": "warm", "found_in_ms": "cold"},
                    {"npc": "npc2", "field": "title", "expected": "chief", "found_in_ms": "intern"},
                    {"npc": "npc3", "field": "goal", "expected": "launch", "found_in_ms": "stall"},
                    {"npc": "npc4", "field": "status", "expected": "ready", "found_in_ms": "blocked"},
                ],
                "numeric_consistency_warnings": [
                    {"text": "num-one"},
                    {"text": "num-two"},
                    {"text": "num-three"},
                    {"text": "num-four"},
                ],
                "coverage_warnings": [
                    "missing_relation_slice",
                    "trimmed_work_slot_summary",
                    "missing_work_slot_summary",
                    "work_focus_without_slots",
                ],
            },
            round_num=1,
        )

        merged_feedback = provenance["merged_feedback"]
        assert long_truth_warning.strip() in merged_feedback
        assert long_violation.strip() in merged_feedback
        assert "[STYLE] style-d" in merged_feedback
        assert merged_feedback.count("[NPC]") == 4
        assert merged_feedback.count("[FACT]") == 4
        assert merged_feedback.count("[COVERAGE]") == 4

    def legacy_test_retry_directives_preserve_newline_structure(self):
        """[pre-rerun] retry_directives가 줄바꿈 구조를 유지하는지 검증 (이전: ' / ' 평탄화)."""
        ir = Stage4InterviewRound(_make_ctx())

        provenance = ir._build_retry_feedback_provenance(
            director_result={"feedback": {}},
            director_feedback="첫 번째 지시사항입니다\n두 번째 지시사항입니다\n세 번째 지시사항입니다",
            selected_validation={},
            round_num=2,
        )

        directives = provenance["retry_directives"]
        assert " / " not in directives, "retry_directives는 ' / '로 평탄화되면 안 됩니다"
        assert "\n" in directives, "retry_directives는 줄바꿈 구조를 유지해야 합니다"
        assert "첫 번째 지시사항입니다" in directives
        assert "두 번째 지시사항입니다" in directives
        assert "세 번째 지시사항입니다" in directives

    def legacy_test_retry_directives_dedup_and_keep_latest_20_lines(self):
        ir = Stage4InterviewRound(_make_ctx())
        backlog = [f"line-{idx}" for idx in range(25)] + ["line-24", "line-23"]

        provenance = ir._build_retry_feedback_provenance(
            director_result={"feedback": {}},
            director_feedback="\n".join(backlog),
            selected_validation={},
            round_num=3,
        )

        directives = provenance["retry_directives"].splitlines()
        assert len(directives) == 20
        assert directives[0] == "line-5"
        assert directives[-1] == "line-24"
        assert directives.count("line-23") == 1

    def test_retry_directives_keep_latest_round_advisories_and_persistent_directives(self):
        ir = Stage4InterviewRound(_make_ctx())

        provenance = ir._build_retry_feedback_provenance(
            director_result={"feedback": {}},
            director_feedback="\n".join(
                [
                    "[IFC] immutable fact conflict still unresolved",
                    "- [R0] stale advisory from older round",
                    "- latest advisory from previous round",
                    "plain stale note that should be dropped",
                    "[Lane3 Gate] REJECT retry widened to partial",
                ]
            ),
            selected_validation={},
            round_num=2,
        )

        directives = provenance["retry_directives"].splitlines()
        assert directives == [
            "[IFC] immutable fact conflict still unresolved",
            "- [R1] latest advisory from previous round",
            "[Lane3 Gate] REJECT retry widened to partial",
        ]

    def test_retry_directives_dedup_cap_and_drop_older_tagged_advisories(self):
        ir = Stage4InterviewRound(_make_ctx())
        backlog = [f"- advisory-{idx}" for idx in range(25)] + ["- advisory-24", "- [R1] stale older advisory"]

        provenance = ir._build_retry_feedback_provenance(
            director_result={"feedback": {}},
            director_feedback="\n".join(backlog),
            selected_validation={},
            round_num=3,
        )

        directives = provenance["retry_directives"].splitlines()
        assert len(directives) == 20
        assert directives[0] == "- [R2] advisory-5"
        assert directives[-1] == "- [R2] advisory-24"
        assert "- [R1] stale older advisory" not in directives

    def test_compact_attempt_snapshot_preserves_full_feedback_lists(self):
        snapshot = Stage4InterviewRound._compact_attempt_snapshot(
            {
                "strategy": "repair",
                "score": 44,
                "attempt_key": "s4:ep9:arc1:a4",
                "candidate_key": "A|repair",
                "content_hash": "hash-123",
                "selection_content_hash": "sel-hash-123",
                "fix_scope_reasoning": "keep all details",
                "open_review": "review",
                "rejection_reason": "reason",
                "retry_budget_axes": {"repair": "rewrite_regenerate"},
                "action_items": [f"fix-step-{idx}" for idx in range(10)],
                "contradiction_types": [f"type-{idx}" for idx in range(6)],
                "contradiction_details": [
                    {
                        "severity": "MAJOR",
                        "type": f"kind-{idx}",
                        "current_violation": f"violation-{idx}",
                        "fix_suggestion": f"repair-{idx}",
                    }
                    for idx in range(4)
                ],
            }
        )

        assert len(snapshot["action_items"]) == 10
        assert len(snapshot["contradiction_types"]) == 6
        assert len(snapshot["contradiction_details"]) == 4
        assert "repair-3" in snapshot["contradiction_details"][-1]
        assert snapshot["attempt_key"] == "s4:ep9:arc1:a4"
        assert snapshot["candidate_key"] == "A|repair"
        assert snapshot["content_hash"] == "hash-123"
        assert snapshot["selection_content_hash"] == "sel-hash-123"
        assert snapshot["retry_budget_axes"] == {"repair": "rewrite_regenerate"}

    def test_extract_fix_feedback_preserves_full_fix_pack_and_issue_lists(self):
        ir = Stage4InterviewRound(_make_ctx())
        feedback = ir._extract_fix_feedback(
            {
                "fix_pack": {
                    "provenance": "runtime_backfilled",
                    "provenance_sources": ["flashback_continuity_localfix", "post_select_conflict"],
                    "patch_targets": [f"slot_{idx}" for idx in range(7)],
                    "must_fix": [f"must-fix-{idx}" for idx in range(6)],
                    "do_not_regress": [f"guard-{idx}" for idx in range(6)],
                    "success_condition": "success-condition " * 20,
                    "evidence_summary": "evidence-summary " * 18,
                },
                "action_items": [f"action-{idx}" for idx in range(7)],
                "feedback": {"issues": [f"issue-{idx}" for idx in range(6)]},
            }
        )

        assert "slot_6" in feedback
        assert "must-fix-5" in feedback
        assert "guard-5" in feedback
        assert "provenance=runtime_backfilled" in feedback
        assert "provenance_sources=flashback_continuity_localfix, post_select_conflict" in feedback
        assert "action-6" in feedback
        assert "issue-5" in feedback

    def test_build_fix_pack_payload_preserves_provenance_fields(self):
        ir = Stage4InterviewRound(_make_ctx())

        payload = ir._build_fix_pack_payload(
            {
                "fix_pack": {
                    "patch_targets": ["ending_sentence"],
                    "must_fix": ["ending consistency"],
                    "do_not_regress": ["tone"],
                    "success_condition": "ending contradiction disappears",
                    "target_kind": "local_sentence",
                    "subtype": "movement",
                    "subtypes": ["movement", "location"],
                    "provenance": "runtime_synthesized",
                    "provenance_sources": ["flashback_continuity_localfix"],
                }
            }
        )

        assert payload["subtype"] == "movement"
        assert payload["subtypes"] == ["movement", "location"]
        assert payload["provenance"] == "runtime_synthesized"
        assert payload["provenance_sources"] == ["flashback_continuity_localfix"]

    def test_advisory_style_signals_reports_runtime_core_gaps(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_quality_signal_summary.return_value = {
            "available": True,
            "signals": {
                "ai_slop": {"median": 0.4},
                "ced": {"median": 0.5},
            },
        }
        ctx.current_project.load_v20_anchor = MagicMock(return_value={"dialogue_ratio": 0.40})
        ir = Stage4InterviewRound(ctx)
        candidates = [
            {"manuscript": ("그야말로 놀라운 순간이었다. " * 140) + ('"짧게 말한다." ' * 18)},
            {"manuscript": "담백한 원고 " * 300},
        ]
        validation_results = [
            {"warning_count": 12, "warnings": []},
            {"warning_count": 0, "warnings": []},
        ]

        advisory = ir._advisory_style_signals(candidates, validation_results, next_ep=7)

        assert advisory
        assert "StyleSignalAdvisor" in advisory[0]
        assert "ai_slop score" in advisory[0]
        assert "ced_score" in advisory[0]
        assert "dialogue_ratio" in advisory[0]
        assert validation_results[0]["quality_signal_warnings"]

    def test_build_reaudit_story_context_injects_patch_history(self):
        ir = Stage4InterviewRound(_make_ctx())

        story_context = ir._build_reaudit_story_context(
            "기존 story context",
            ["scope=inplace | reason=대사 조정", "scope=inplace | reason=엔딩 긴장 복구"],
        )

        assert story_context.startswith("기존 story context")
        assert "[PASS_WITH_FIX 재심사 — 이미 적용된 패치]" in story_context
        assert "- scope=inplace | reason=엔딩 긴장 복구" in story_context

    def test_suppress_conflicting_advisories_prefers_higher_tier(self):
        ir = Stage4InterviewRound(_make_ctx())
        parts = [
            "[NumericDriftAdvisor]\n- [MAJOR] '자본금': 누적 표류 의심",
            "[TruthGate Advisory — CRITICAL 경고 시 반드시 REJECT]\n- [CRITICAL] 자본금 10억이 갑자기 100억으로 변함",
        ]

        filtered = ir._suppress_conflicting_advisories(parts)

        assert len(filtered) == 1
        assert "TruthGate" in filtered[0]

    def test_build_candidate_diversity_advisory_warns_for_similar_candidates(self):
        ir = Stage4InterviewRound(_make_ctx())
        candidates = [
            {"manuscript": "같은 내용이 길게 이어진다. 같은 내용이 길게 이어진다."},
            {"manuscript": "같은 내용이 길게 이어진다! 같은 내용이 길게 이어진다."},
            {"manuscript": "같은 내용이 길게 이어진다? 같은 내용이 길게 이어진다."},
        ]

        advisory = ir._build_candidate_diversity_advisory(candidates)

        assert "후보 다양성 경고" in advisory
        assert "가장 다른 접근" in advisory

    def test_summarize_candidate_diversity_reports_pairwise_similarity(self):
        ir = Stage4InterviewRound(_make_ctx())
        candidates = [
            {"manuscript": "같은 내용이 길게 이어진다. 같은 내용이 길게 이어진다."},
            {"manuscript": "같은 내용이 길게 이어진다! 같은 내용이 길게 이어진다."},
            {"manuscript": "전혀 다른 접근으로 새로운 장면이 열린다."},
        ]

        summary = ir._summarize_candidate_diversity(candidates, threshold=0.6)

        assert summary["max_similarity"] >= 0.6
        assert any(pair["pair"] == "A-B" for pair in summary["pairwise"])
        assert any(pair["similarity"] < 0.5 for pair in summary["pairwise"])

    def test_detect_shared_failure_warnings_when_all_candidates_share_signature(self):
        ir = Stage4InterviewRound(_make_ctx())
        validation_results = [
            {"warnings": ["[Python검증-HIGH] NPC 텔레포트"], "structured_violations": []},
            {"warnings": ["[Python검증-HIGH] NPC 텔레포트"], "structured_violations": []},
            {"warnings": ["[Python검증-HIGH] NPC 텔레포트"], "structured_violations": []},
        ]

        warnings = ir._detect_shared_failure_warnings(validation_results)

        assert warnings == ["[⚠️ 전원 동일 위반: NPC 텔레포트]"]

    def test_merge_retry_advisory_feedback_appends_digest_once(self):
        ir = Stage4InterviewRound(_make_ctx())
        ir._last_advisory_details = [
            "[CRITICAL · TruthGate] 마지막 장면의 수치 모순",
            "[MAJOR · NpcDrift] 주연 NPC 말투 이탈",
        ]

        merged = ir._merge_retry_advisory_feedback("기본 피드백")

        assert "[Advisory 핵심 요약 - 재시도 시 반영]" in merged
        assert "TruthGate" in merged
        assert "NpcDrift" in merged
        assert ir._merge_retry_advisory_feedback(merged) == merged


class TestAdvisoryChain:
    def test_timeout_cancels_pending_futures_and_returns_empty(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        class _FakeFuture:
            def __init__(self):
                self.cancelled = False

            def done(self):
                return False

            def cancel(self):
                self.cancelled = True
                return True

            def result(self, timeout=None):
                return []

        class _FakeExecutor:
            last_instance = None

            def __init__(self, *args, **kwargs):
                self.futures = []
                self.shutdown_calls = []
                _FakeExecutor.last_instance = self

            def submit(self, *_args, **_kwargs):
                future = _FakeFuture()
                self.futures.append(future)
                return future

            def shutdown(self, wait=True, cancel_futures=False):
                self.shutdown_calls.append((wait, cancel_futures))

        def _raise_timeout(_futures, timeout=None):
            raise concurrent.futures.TimeoutError("boom")

        with (
            patch("concurrent.futures.ThreadPoolExecutor", _FakeExecutor),
            patch("concurrent.futures.as_completed", side_effect=_raise_timeout),
        ):
            result = ir._run_advisory_chain(
                candidates=[_candidate()],
                validation_results=[_validation_result()],
                next_ep=1,
                genre_name="무협",
            )

        assert result == []
        assert _FakeExecutor.last_instance is not None
        assert _FakeExecutor.last_instance.shutdown_calls == [(False, True)]
        assert all(f.cancelled for f in _FakeExecutor.last_instance.futures)

    def test_advisory_chain_uses_local_validation_copies_and_merges_back(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        validation_results = [_validation_result()]
        seen_ids = {}

        class _ImmediateFuture:
            def __init__(self, fn, *args):
                self._result = fn(*args)

            def result(self, timeout=None):
                return self._result

            def done(self):
                return True

            def cancel(self):
                return False

        class _FakeExecutor:
            def __init__(self, *args, **kwargs):
                self.shutdown_calls = []

            def submit(self, fn, *args, **kwargs):
                return _ImmediateFuture(fn, *args)

            def shutdown(self, wait=True, cancel_futures=False):
                self.shutdown_calls.append((wait, cancel_futures))

        def _truth_gate(_candidates, local_results, _next_ep):
            seen_ids["truth"] = id(local_results)
            local_results[0]["truth_gate_warnings"] = [{"severity": "CRITICAL", "text": "사망 NPC 등장"}]
            return ["[TruthGate Advisory]"]

        def _npc_drift(_candidates, local_results, _next_ep):
            seen_ids["npc"] = id(local_results)
            local_results[0]["npc_drift_warnings"] = [{"npc": "연홍"}]
            return ["[NpcDriftAdvisor]"]

        def _numeric_consistency(_candidates, local_results, _next_ep):
            seen_ids["numeric"] = id(local_results)
            local_results[0]["numeric_consistency_warnings"] = [
                {
                    "severity": "MAJOR",
                    "text": "[수치 불일치] 원고 '포지션 60억' vs FactLedger '포지션'=40억",
                }
            ]
            return ["[NumericConsistency]"]

        with (
            patch("concurrent.futures.ThreadPoolExecutor", _FakeExecutor),
            patch("concurrent.futures.as_completed", side_effect=lambda futures, timeout=None: list(futures)),
            patch.object(ir, "_advisory_truth_gate", side_effect=_truth_gate),
            patch.object(ir, "_advisory_npc_drift", side_effect=_npc_drift),
            patch.object(ir, "_advisory_numeric_drift", return_value=[]),
            patch.object(ir, "_advisory_flashback", return_value=[]),
            patch.object(ir, "_advisory_info_paradox", return_value=[]),
            patch.object(ir, "_advisory_rel_drift", return_value=[]),
            patch.object(ir, "_advisory_long_term_rep", return_value=[]),
            patch.object(ir, "_advisory_numeric_consistency", side_effect=_numeric_consistency),
            patch.object(ir, "_advisory_style_signals", return_value=[]),
        ):
            result = ir._run_advisory_chain(
                candidates=[_candidate()],
                validation_results=validation_results,
                next_ep=1,
                genre_name="무협",
            )

        assert result == ["[TruthGate Advisory]", "[NpcDriftAdvisor]", "[NumericConsistency]"]
        assert seen_ids["truth"] != id(validation_results)
        assert seen_ids["npc"] != id(validation_results)
        assert seen_ids["numeric"] != id(validation_results)
        assert seen_ids["truth"] != seen_ids["npc"]
        assert validation_results[0]["truth_gate_warnings"][0]["text"] == "사망 NPC 등장"
        assert validation_results[0]["npc_drift_warnings"][0]["npc"] == "연홍"
        assert "포지션 60억" in validation_results[0]["numeric_consistency_warnings"][0]["text"]

    def test_partial_advisory_failure_logs_warning_and_continues(self, caplog):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        class _ImmediateFuture:
            def __init__(self, fn, *args):
                self._fn = fn
                self._args = args

            def result(self, timeout=None):
                return self._fn(*self._args)

            def done(self):
                return True

            def cancel(self):
                return False

        class _FakeExecutor:
            def __init__(self, *args, **kwargs):
                self.shutdown_calls = []

            def submit(self, fn, *args, **kwargs):
                return _ImmediateFuture(fn, *args)

            def shutdown(self, wait=True, cancel_futures=False):
                self.shutdown_calls.append((wait, cancel_futures))

        def _truth_gate_failure(*_args, **_kwargs):
            raise RuntimeError("truth gate exploded")

        with (
            patch("concurrent.futures.ThreadPoolExecutor", _FakeExecutor),
            patch("concurrent.futures.as_completed", side_effect=lambda futures, timeout=None: list(futures)),
            patch.object(ir, "_advisory_truth_gate", side_effect=_truth_gate_failure),
            patch.object(ir, "_advisory_npc_drift", return_value=["[NpcDriftAdvisor]"]),
            patch.object(ir, "_advisory_numeric_drift", return_value=[]),
            patch.object(ir, "_advisory_flashback", return_value=[]),
            patch.object(ir, "_advisory_info_paradox", return_value=[]),
            patch.object(ir, "_advisory_rel_drift", return_value=[]),
            patch.object(ir, "_advisory_long_term_rep", return_value=[]),
            patch.object(ir, "_advisory_numeric_consistency", return_value=[]),
            patch.object(ir, "_advisory_style_signals", return_value=[]),
            caplog.at_level(logging.WARNING),
        ):
            result = ir._run_advisory_chain(
                candidates=[_candidate()],
                validation_results=[_validation_result()],
                next_ep=1,
                genre_name="무협",
            )

        assert result == ["[NpcDriftAdvisor]"]
        assert "[Advisory] TruthGate 실패 (비치명): truth gate exploded" in caplog.text


class TestPreDirectorValidation:
    def test_pre_director_validation_attaches_coverage_warnings_to_candidates(self):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.context_advisor = MagicMock()
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=4,
            slots=[
                RetrievalSlot(
                    category="work_relationship_context",
                    query="관계 변화 이력: 주인공, 연홍",
                    source=RetrievalSources.DB_NPC_RELATIONSHIP,
                    priority=1,
                )
            ],
            total_budget_chars=800,
        )
        ir = Stage4InterviewRound(ctx)

        round_ctx = _make_round_ctx()
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.director_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            return default

        with (
            patch("modules.validation.threshold_helper._threshold", side_effect=threshold_side_effect),
            patch.object(ir, "_resolve_director_work_focus", return_value={"tracking_slots": ["소꿉친구 라인"]}),
            patch.object(
                ir, "_build_director_work_focus_summary", return_value="[작품 추적 슬롯 요약]\n- 소꿉친구 라인"
            ),
            patch.object(ir, "_build_director_relationship_context", return_value=""),
        ):
            validation_results, _director_mem = ir.director_runtime.run_pre_director_validation(
                candidates=[_candidate()],
                next_ep=4,
                blueprint={"characters": ["연홍"]},
                prev_text="이전 원고",
                hud_report="HUD",
                genre_name="무협",
                manuscript_validator=round_ctx.manuscript_validator,
                consistency_validator=round_ctx.consistency_validator,
                blocking_validator=round_ctx.blocking_validator,
                continuity_validator=round_ctx.continuity_validator,
                stage4_spinner=MagicMock(),
                round_num=0,
                arc_pos=1,
                total_ep_in_arc=10,
                arc_data={},
                prev_manuscript="",
            )

        assert validation_results[0]["coverage_warnings"] == ["missing_relation_slice"]

    def test_collect_director_retrieval_context_attaches_warnings_and_observation(self):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.context_advisor = MagicMock()
        ctx.quality_dashboard = MagicMock()
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=4,
            slots=[
                RetrievalSlot(
                    category="work_relationship_context",
                    query="관계 변화 이력: 주인공, 연홍",
                    source=RetrievalSources.DB_NPC_RELATIONSHIP,
                    priority=1,
                )
            ],
            total_budget_chars=800,
        )
        ir = Stage4InterviewRound(ctx)
        validation_results = [_validation_result()]

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.director_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            return default

        with (
            patch("modules.validation.threshold_helper._threshold", side_effect=threshold_side_effect),
            patch.object(ir, "_resolve_director_work_focus", return_value={"tracking_slots": ["소꿉친구 라인"]}),
            patch.object(
                ir, "_build_director_work_focus_summary", return_value="[작품 추적 슬롯 요약]\n- 소꿉친구 라인"
            ),
            patch.object(ir, "_build_director_relationship_context", return_value=""),
        ):
            director_memory_context = ir.director_runtime.collect_director_retrieval_context(
                validation_results=validation_results,
                next_ep=4,
                round_num=0,
                blueprint={"characters": ["연홍"]},
                prev_text="이전 원고",
                genre_name="무협",
                arc_pos=1,
                total_ep_in_arc=10,
            )

        assert "[작품 추적 슬롯 요약]" in director_memory_context
        assert validation_results[0]["coverage_warnings"] == ["missing_relation_slice"]
        ctx.quality_dashboard.record_retrieval_observation.assert_called_once()
        observation = ctx.quality_dashboard.record_retrieval_observation.call_args.kwargs["observation"]
        assert observation["relation_slice_included"] is False
        assert observation["coverage_warnings"] == ["missing_relation_slice"]

    def test_build_director_retrieval_payload_collects_plan_and_memory_context(self):
        ctx = _make_ctx()
        ctx.memory = MagicMock()
        ctx.context_advisor = MagicMock()
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=4,
            slots=[
                RetrievalSlot(
                    category="work_relationship_context",
                    query="관계 변화 이력: 주인공 고한",
                    source=RetrievalSources.DB_NPC_RELATIONSHIP,
                    priority=1,
                )
            ],
            total_budget_chars=800,
        )
        ir = Stage4InterviewRound(ctx)

        def threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.director_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            return default

        with (
            patch("modules.validation.threshold_helper._threshold", side_effect=threshold_side_effect),
            patch.object(ir, "_resolve_director_work_focus", return_value={"tracking_slots": ["guild line"]}),
            patch.object(ir, "_build_director_work_focus_summary", return_value="[작품 추적 슬롯 요약]\n- guild line"),
            patch.object(ir, "_build_director_relationship_context", return_value="[관계 의미 질의]\n- ally -> rival"),
        ):
            payload = ir.director_runtime._build_director_retrieval_payload(
                next_ep=4,
                round_num=0,
                blueprint={"characters": ["고한"]},
                prev_text="이전 원고",
                genre_name="무협",
                arc_pos=1,
                total_ep_in_arc=10,
            )

        assert payload.work_focus == {"tracking_slots": ["guild line"]}
        assert payload.work_focus_summary == "[작품 추적 슬롯 요약]\n- guild line"
        assert payload.plan is ctx.context_advisor.plan_director_retrieval.return_value
        assert "[작품 추적 슬롯 요약]" in payload.director_memory_context
        assert "[관계 의미 질의]" in payload.director_memory_context

    def test_resolve_director_slot_npcs_falls_back_to_query_tokens(self):
        ir = Stage4InterviewRound(_make_ctx())
        slot_npcs = ir.director_runtime._resolve_director_slot_npcs(
            npc_roster=[],
            slot_query="고한 / 청우, 장문인",
            max_npcs_per_slot=2,
        )

        assert slot_npcs == ["고한", "청우"]

    def test_run_pre_director_validation_forwards_blocking_degraded_advisory(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        round_ctx = _make_round_ctx()
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        round_ctx.blocking_validator.validate.return_value = {
            "passed": True,
            "failures": [],
            "warnings": ["degraded: relationship_consistency"],
            "degraded_checks": ["relationship_consistency"],
        }

        validation_results, _director_mem = ir.director_runtime.run_pre_director_validation(
            candidates=[_candidate()],
            next_ep=4,
            blueprint={"characters": ["연홍"]},
            prev_text="이전 원고",
            hud_report="HUD",
            genre_name="무협",
            manuscript_validator=round_ctx.manuscript_validator,
            consistency_validator=round_ctx.consistency_validator,
            blocking_validator=round_ctx.blocking_validator,
            continuity_validator=round_ctx.continuity_validator,
            stage4_spinner=MagicMock(),
            round_num=0,
            arc_pos=1,
            total_ep_in_arc=10,
            arc_data={},
            prev_manuscript="",
        )

        assert validation_results[0]["warnings"] == ["[Python검증-ADVISORY] degraded: relationship_consistency"]
        assert validation_results[0]["warning_count"] == 1
        assert validation_results[0]["focus_points"] == ["Python 검증 advisory 1건 (Director 참고)"]

    def test_run_director_core_validation_modules_routes_validator_advisories(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        validation_results = [_validation_result()]
        candidates = [{"manuscript": "candidate manuscript", "strategy_name": "balanced"}]

        consistency_validator = MagicMock()
        consistency_validator.validate.return_value = {
            "violations": [{"reason": "canon drift", "severity": "HIGH"}],
            "score_penalty": 3,
        }
        blocking_validator = MagicMock()
        blocking_validator.validate.return_value = {
            "failures": [{"reason": "grave issue", "severity": "CRITICAL"}],
            "warnings": ["soft warning"],
            "degraded_checks": ["timeline_link"],
        }
        continuity_validator = MagicMock()
        continuity_validator.validate.return_value = {
            "violations": [{"reason": "time jump"}],
            "warnings": [{"reason": "clock drift"}],
        }
        continuity_validator.check_frustration_streak.return_value = ["frustration alert"]
        ctx.state_tracker.check_destroyed_entity_in_manuscript.return_value = [{"message": "ruined gate"}]

        with patch.object(ir.director_runtime, "build_cv_context", return_value={"context": "ok"}):
            ir.director_runtime.run_director_core_validation_modules(
                candidates=candidates,
                validation_results=validation_results,
                next_ep=4,
                round_num=1,
                genre_name="genre",
                blueprint={"characters": ["hero"]},
                arc_data={},
                consistency_validator=consistency_validator,
                blocking_validator=blocking_validator,
                continuity_validator=continuity_validator,
            )

        warnings = validation_results[0]["warnings"]
        assert "[V63.2] 일관성: [HIGH] canon drift" in warnings
        assert "[Python검증-CRITICAL] grave issue" in warnings
        assert "[Python검증-ADVISORY] soft warning" in warnings
        assert "[Python검증-ADVISORY] degraded: timeline_link" in warnings
        assert "[V66.1] 연속성: time jump" in warnings
        assert "[V66.1] 연속성 경고: clock drift" in warnings
        assert "[D Step 4] frustration alert" in warnings
        assert "[V66.2] 파괴된 엔티티 등장: ruined gate" in warnings
        assert validation_results[0]["warning_count"] == len(warnings)
        assert validation_results[0]["focus_points"] == [
            "일관성 위반 1건 (감점 3)",
            "Python 검증 경고 1건 (Director 판단 필요)",
            "Python 검증 advisory 2건 (Director 참고)",
            "연속성 위반 1건",
        ]

    def test_build_cv_identity_context_injects_prev_hud_and_protagonist_fields(self):
        ctx = _make_ctx()
        ctx.failure_learner = MagicMock()
        ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {"incarnation_type": "reincarnated"}}}
        ir = Stage4InterviewRound(ctx)
        ir.time_warnings = ["timeline risk"]

        with patch.object(ir, "_resolve_prev_hud_snapshot", return_value=({"hp": 99}, "persisted")):
            with patch("modules.core.constants.HUDKeys.get_protagonist_name", return_value="한유진"):
                result = ir._build_cv_identity_context(next_ep=4, genre_name="무협")

        assert result["prev_hud"] == {"hp": 99}
        assert result["prev_hud_source"] == "persisted"
        assert result["martial_hud"] == {"hp": 99}
        assert result["incarnation_type"] == "reincarnated"
        assert result["protagonist_name"] == "한유진"
        assert result["time_warnings"] == ["timeline risk"]
        assert result["_failure_learner"] is ctx.failure_learner

    def test_build_cv_state_tracker_context_collects_registry_and_history(self):
        ctx = _make_ctx()
        ctx.state_tracker.npc_registry = {
            "사부": {
                "status": "alive",
                "death_arc": None,
                "aliases": ["스승"],
                "personality_traits": "냉정",
                "primary_motivation": "보호",
            }
        }
        ctx.state_tracker.item_state_registry = {"검": {"condition": "파손"}}
        ctx.state_tracker.get_npc_change_history.return_value = [{"ep": 3, "change": "injured"}]
        ir = Stage4InterviewRound(ctx)

        result = ir._build_cv_state_tracker_context()

        assert result["encyclopedia"]["npcs"] == [
            {"name": "사부", "status": "alive", "death_arc": None, "aliases": ["스승"]}
        ]
        assert result["item_states"] == {"검": "파손"}
        assert result["npc_personalities"] == {"사부": {"traits": "냉정", "motivation": "보호"}}
        assert result["npc_history"] == {"사부": [{"ep": 3, "change": "injured"}]}

    def test_build_cv_role_context_builds_karma_villain_and_authority_context(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_episode_bible.return_value = {
            "karma_matrix": [
                {"target": "진악", "relation": "enemy", "type": "betrayal", "description": "betrayed the sect"}
            ]
        }
        ctx.current_project.master_bible = {
            "MasterBible": {
                "protagonist_config": {"position": "제자"},
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "진악", "role": "악역", "position": "수장"},
                        {"name": "사부", "role": "사부", "position": "장문인"},
                    ]
                },
            }
        }
        ctx.world_state = MagicMock()
        ctx.world_state._state = {"alive_npcs": {"사부": {"known_attrs": {"position": {"value": "대장로"}}}}}
        ir = Stage4InterviewRound(ctx)

        result = ir._build_cv_role_context(next_ep=3)

        assert result["karma_matrix"]["진악"]["relation_type"] == "enemy"
        assert result["villain_context"] == {"villain_name": "진악", "villain_role": "악역", "is_aware": True}
        assert result["authority_context"] == {
            "protagonist_position": "제자",
            "superior_alive": True,
            "superior_name": "사부",
            "superior_position": "대장로",
        }

    def test_run_director_continuity_and_state_tracker_advisories_routes_outputs(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        validation_results = [_validation_result()]
        continuity_validator = MagicMock()
        continuity_validator.validate.return_value = {
            "violations": [{"reason": "time jump"}],
            "warnings": [{"reason": "clock drift"}],
        }
        continuity_validator.check_frustration_streak.return_value = ["frustration alert"]
        ctx.state_tracker.check_destroyed_entity_in_manuscript.return_value = [{"message": "ruined gate"}]

        ir._run_director_continuity_and_state_tracker_advisories(
            candidates=[{"manuscript": "candidate manuscript"}],
            validation_results=validation_results,
            next_ep=4,
            cv_context={"context": "ok"},
            continuity_validator=continuity_validator,
        )

        warnings = validation_results[0]["warnings"]
        assert any("time jump" in warning for warning in warnings)
        assert any("clock drift" in warning for warning in warnings)
        assert any("frustration alert" in warning for warning in warnings)
        assert any("ruined gate" in warning for warning in warnings)
        assert validation_results[0]["warning_count"] == len(warnings)
        assert len(validation_results[0]["focus_points"]) == 1
        continuity_validator.validate.assert_called_once_with(4, "candidate manuscript", {"context": "ok"})
        continuity_validator.check_frustration_streak.assert_called_once_with(4)
        ctx.state_tracker.check_destroyed_entity_in_manuscript.assert_called_once_with("candidate manuscript")

    def test_run_blocking_validator_advisories_routes_failures_and_deduped_advisories(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        validation_results = [_validation_result()]
        blocking_validator = MagicMock()
        blocking_validator.validate.return_value = {
            "failures": [{"reason": "grave issue", "severity": "CRITICAL"}],
            "warnings": ["soft warning", "soft warning"],
            "degraded_checks": ["timeline_link", "timeline_link"],
        }

        ir._run_blocking_validator_advisories(
            candidates=[{"manuscript": "candidate manuscript"}],
            validation_results=validation_results,
            next_ep=4,
            round_num=1,
            cv_context={"context": "ok"},
            blocking_validator=blocking_validator,
        )

        warnings = validation_results[0]["warnings"]
        assert warnings == [
            "[Python검증-CRITICAL] grave issue",
            "[Python검증-ADVISORY] soft warning",
            "[Python검증-ADVISORY] degraded: timeline_link",
        ]
        assert validation_results[0]["warning_count"] == 3
        assert validation_results[0]["focus_points"] == [
            "Python 검증 경고 1건 (Director 판단 필요)",
            "Python 검증 advisory 2건 (Director 참고)",
        ]

    def test_apply_blocking_validator_result_routes_failures_and_advisories(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        validation_result = _validation_result()

        ir._apply_blocking_validator_result(
            validation_result=validation_result,
            bv_result={
                "failures": [{"reason": "grave issue", "severity": "CRITICAL"}],
                "warnings": ["soft warning", "soft warning"],
                "degraded_checks": ["timeline_link", "timeline_link"],
            },
            candidate_index=1,
            next_ep=4,
            round_num=1,
        )

        assert validation_result["warnings"] == [
            "[Python검증-CRITICAL] grave issue",
            "[Python검증-ADVISORY] soft warning",
            "[Python검증-ADVISORY] degraded: timeline_link",
        ]
        assert validation_result["warning_count"] == 3
        assert validation_result["focus_points"] == [
            "Python 검증 경고 1건 (Director 판단 필요)",
            "Python 검증 advisory 2건 (Director 참고)",
        ]
        assert any("Python 검증 경고 1건" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)
        assert any("Python 검증 advisory 2건" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)

    def test_apply_blocking_validator_failures_updates_focus_points_and_logs_details(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        validation_result = _validation_result()

        ir._apply_blocking_validator_failures(
            validation_result=validation_result,
            bv_failures=[{"reason": "grave issue", "severity": "CRITICAL"}],
            candidate_index=1,
            next_ep=4,
            round_num=1,
        )

        assert validation_result["warnings"] == ["[Python검증-CRITICAL] grave issue"]
        assert validation_result["warning_count"] == 1
        assert validation_result["focus_points"] == ["Python 검증 경고 1건 (Director 판단 필요)"]
        assert any("Python 검증 경고 1건" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)
        assert any("[CRITICAL] grave issue" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)

    def test_apply_blocking_validator_advisories_updates_focus_points_and_logs_summary(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        validation_result = _validation_result()

        ir._apply_blocking_validator_advisories(
            validation_result=validation_result,
            bv_advisory_warnings=["soft warning", "degraded: timeline_link"],
            candidate_index=1,
            next_ep=4,
            round_num=1,
        )

        assert validation_result["warnings"] == [
            "[Python검증-ADVISORY] soft warning",
            "[Python검증-ADVISORY] degraded: timeline_link",
        ]
        assert validation_result["warning_count"] == 2
        assert validation_result["focus_points"] == ["Python 검증 advisory 2건 (Director 참고)"]
        assert any("Python 검증 advisory 2건" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)

    def test_collect_blocking_validator_advisory_warnings_dedupes_and_formats(self):
        warnings = Stage4InterviewRound._collect_blocking_validator_advisory_warnings(
            {
                "warnings": ["soft warning", "soft warning", ""],
                "degraded_checks": ["timeline_link", "timeline_link", ""],
            }
        )

        assert warnings == [
            "soft warning",
            "degraded: timeline_link",
        ]

    def test_run_director_optional_validation_modules_routes_checklist_confidence_and_crossverify(self):
        from types import SimpleNamespace

        from modules.core.cross_agent_verifier import ComplianceLevel

        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        checklist = MagicMock()
        checklist.check.return_value = SimpleNamespace(
            passed=False,
            blocking_reasons=["style drift"],
            summary="style drift summary",
        )
        confidence = MagicMock()
        confidence.assess.return_value = SimpleNamespace(
            concerns=["uncertain causality"],
            level=SimpleNamespace(value="LOW"),
        )
        cross_verifier = MagicMock()
        cross_verifier.verify_writer_compliance.return_value = SimpleNamespace(
            level=ComplianceLevel.VIOLATION,
            violations=[{"reason": "timeline conflict"}],
            warnings=[],
        )
        ctx.get_module.side_effect = lambda name: {
            "pre_director_checklist": checklist,
            "confidence_calibrator": confidence,
            "cross_verifier": cross_verifier,
        }.get(name)
        validation_results = [_validation_result()]

        with (
            patch("modules.core.project_support.resolve_style_dialogue_ratio_target", return_value=0.42),
            patch.object(ir, "_detect_shared_failure_warnings", return_value=["shared warning"]),
        ):
            ir.director_runtime.run_director_optional_validation_modules(
                candidates=[_candidate()],
                validation_results=validation_results,
                blueprint={"characters": ["연홍"]},
                prev_manuscript="이전 원고",
            )

        assert checklist.check.call_args.kwargs["context"]["style_dialogue_ratio_target"] == 0.42
        assert "[PreCheck] style drift" in validation_results[0]["warnings"]
        assert "[Confidence:LOW] uncertain causality" in validation_results[0]["warnings"]
        assert "[CrossVerify:VIOLATION] timeline conflict" in validation_results[0]["warnings"]
        assert validation_results[0]["shared_failure_warnings"] == ["shared warning"]


class TestInterviewRoundRun:
    def test_empty_candidates_returns_empty(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = []

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "EMPTY"

    def test_non_dict_or_blank_candidates_filter_to_empty(self, caplog):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [
            "bad-candidate",
            {"manuscript": "   "},
            {"title": "missing manuscript"},
        ]

        with caplog.at_level(logging.WARNING):
            result = ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert result.verdict == "EMPTY"
        assert "후보 3건 전량 필터링 탈락" in caplog.text

    def test_pass_returns_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "좋음",
            "selected_candidate": {"manuscript": "통과 원고", "title": "통과"},
            "state_updates": {},
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS"
        assert result.final_manuscript == "통과 원고"

    def test_prepare_round_execution_builds_payload_and_generation_start_log(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._log_attempt_event = MagicMock()
        round_ctx = _make_round_ctx()
        round_ctx.arc_pos = 1
        stage4_spinner = MagicMock()

        with (
            patch.object(ir, "_capture_round_metrics_baseline"),
            patch.object(ir, "_setup_writing_directive", return_value=("directive", None)),
            patch.object(
                ir,
                "_build_common_writer_kwargs",
                return_value=("merged mandatory context", {"common": "kwargs"}),
            ) as build_common,
        ):
            result = ir._prepare_round_execution(
                round_num=0,
                stage4_spinner=stage4_spinner,
                director_feedback=123,
                round_ctx=round_ctx,
            )

        assert result.chief_writer is round_ctx.chief_writer
        assert result.next_ep == round_ctx.next_ep
        assert result.blueprint == round_ctx.blueprint
        assert result.style_guide == round_ctx.style_guide
        assert result.mandatory_context == "merged mandatory context"
        assert result.writing_directive == "directive"
        assert result.common_writer_kwargs == {"common": "kwargs"}
        assert result.director_feedback == "123"
        build_kwargs = build_common.call_args.kwargs
        assert build_kwargs["mandatory_context"].startswith("[Arc 첫 화 특별 지시]")
        stage4_spinner.update_detail.assert_called_once_with("제1화 · 1차 면담 · 앙상블 생성")
        ir._log_attempt_event.assert_called_once()

    def test_prepend_arc_first_location_note_only_for_arc_opening(self):
        note = Stage4InterviewRound._prepend_arc_first_location_note(
            arc_pos=1,
            mandatory_context="base context",
        )
        unchanged = Stage4InterviewRound._prepend_arc_first_location_note(
            arc_pos=2,
            mandatory_context="base context",
        )

        assert note.startswith("[Arc 첫 화 특별 지시]")
        assert "base context" in note
        assert unchanged == "base context"

    def test_pass_writes_session_decision_row_with_join_metadata(self, tmp_path):
        ctx = _make_ctx()
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.root = tmp_path
        ctx.session_logger = SessionLogger(tmp_path / "logs" / "session", enabled=True)
        ir = Stage4InterviewRound(ctx)
        ir._build_retry_advisory_digest = MagicMock(return_value="[advisory] keep continuity")
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 7
        round_ctx.arc_data = {"arc_no": 2}
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "verdict_reason": "pass rationale",
            "selected_candidate": {
                "manuscript": "pass manuscript",
                "title": "pass",
                "strategy_name": "balanced",
            },
            "state_updates": {},
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        decisions_path = tmp_path / "logs" / "session" / "decisions.jsonl"
        rows = [json.loads(line) for line in decisions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        row = rows[-1]
        meta = row["meta"]

        assert result.verdict == "PASS"
        assert row["stage"] == "stage4"
        assert row["result"] == "PASS"
        assert meta["attempt_key"].startswith("s4:ep7:arc2:a")
        assert meta["candidate_key"]
        assert meta["content_hash"]
        assert meta["artifact_path"].endswith(".txt")
        assert meta["selection_candidate_key"] == "A|balanced"
        assert meta["selection_artifact_path"].endswith("selected_candidate__A_balanced.txt")
        assert meta["reason"] == "pass rationale"
        assert meta["selection_reason"] == "ok"
        assert meta["verdict_reason"] == "pass rationale"
        assert meta["runtime_advisory"] == "[advisory] keep continuity"
        assert meta["retry_directives"] == ""
        assert (tmp_path / meta["artifact_path"]).exists()
        assert (tmp_path / meta["selection_artifact_path"]).exists()

    def test_reject_returns_reject(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ir._run_advisory_chain = MagicMock(return_value=["[TruthGate Advisory] 마지막 장면 모순"])
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 40,
            "selection_reason": "부족",
            "feedback": {"issues": ["문제"]},
            "action_items": ["수정1"],
            "selected_candidate": {"manuscript": "거절 원고"},
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        assert result.final_manuscript is None
        assert "[Advisory 핵심 요약 - 재시도 시 반영]" in result.previous_attempt["rejection_reason"]

    def test_reject_preserves_structured_validation_warnings_for_retry(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            {
                "warnings": [],
                "warning_count": 0,
                "focus_points": [],
                "metrics": {"length": 2000},
                "npc_drift_warnings": [
                    {
                        "npc": "연홍",
                        "field": "말투",
                        "expected": "반말",
                        "found_in_ms": "존댓말",
                    }
                ],
                "numeric_consistency_warnings": [
                    {
                        "severity": "MAJOR",
                        "text": "[수치 불일치] 원고 '포지션 60억' vs FactLedger '포지션'=40억",
                    }
                ],
                "coverage_warnings": ["missing_relation_slice"],
            }
        ]
        ir._run_advisory_chain = MagicMock(return_value=[])
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 40,
            "selection_reason": "부족",
            "feedback": {"issues": ["문제"]},
            "action_items": ["수정1"],
            "selected_candidate": {"manuscript": "거절 원고"},
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert any("[후보 A] [NPC]" in warning for warning in result.previous_attempt["validation_warnings"])
        assert any("[후보 A] [FACT]" in warning for warning in result.previous_attempt["validation_warnings"])
        assert any("[후보 A] [COVERAGE]" in warning for warning in result.previous_attempt["validation_warnings"])

    def test_patch_and_fallback_use_ctx_state_tracker(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.inplace_patch.return_value = []  # [TF-23] InPlace 실패 유도
        round_ctx.chief_writer.patch_with_feedback.return_value = []  # 폴백 유도
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 80,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=1,
            stage4_spinner=MagicMock(),
            director_feedback="피드백",
            previous_attempt={
                "score": 70,
                "best_manuscript": "원고",
                "fix_scope": "partial",
                "reject_bucket": "post_select_conflict",
                "fix_pack": _local_fix_pack(),
            },
            round_ctx=round_ctx,
        )

        assert round_ctx.chief_writer.patch_with_feedback.call_args.kwargs["state_tracker"] is ctx.state_tracker
        assert round_ctx.chief_writer.regenerate_with_feedback.call_args.kwargs["state_tracker"] is ctx.state_tracker

    def test_general_regenerate_uses_ctx_state_tracker(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.inplace_patch.return_value = []  # [TF-23] InPlace 안 타도록 방어
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 80,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=2,
            stage4_spinner=MagicMock(),
            director_feedback="피드백",
            previous_attempt={"score": 20, "best_manuscript": ""},
            round_ctx=round_ctx,
        )

        assert round_ctx.chief_writer.regenerate_with_feedback.call_args.kwargs["state_tracker"] is ctx.state_tracker

    def test_time_warnings_stored_and_used_in_context(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir.time_warnings = ["기존 경고"]
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.state_tracker.check_time_consistency.return_value = ["신규 경고"]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 90,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        used_context = round_ctx.consistency_validator.validate.call_args.args[1]
        assert "기존 경고" in used_context["time_warnings"]
        assert "신규 경고" in ir.time_warnings

    def test_cv_context_includes_blueprint_payload(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 2
        round_ctx.blueprint = {"integrated_scenario": "테스트 플롯", "characters": [{"name": "청운"}]}
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 90,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        used_context = round_ctx.consistency_validator.validate.call_args.args[1]
        assert used_context["blueprint"] == round_ctx.blueprint
        assert "integrated_scenario" in used_context["blueprint_text"]

    def test_director_mandatory_context_includes_pov_block(self):
        ctx = _make_ctx()
        ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {"pov": "혼합"}}}
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과 원고", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        director_kwargs = ctx.agents["director"].select_and_judge_ensemble.call_args.kwargs
        assert "[작품 시점]" in director_kwargs["mandatory_context"]
        assert "기본 POV: 혼합" in director_kwargs["mandatory_context"]

    def test_director_mandatory_context_includes_external_pov_policy(self):
        ctx = _make_ctx()
        ctx.current_project.master_bible = {
            "MasterBible": {"protagonist_config": {"pov": "혼합", "external_pov_insert_policy": "제한적 허용"}}
        }
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과 원고", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        director_kwargs = ctx.agents["director"].select_and_judge_ensemble.call_args.kwargs
        assert "policy: 제한적 허용" in director_kwargs["mandatory_context"]

    def test_build_history_parser_accepts_inline_header_without_newline(self):
        ctx = _make_ctx()
        ctx.current_project.db.get_manuscript.return_value = None
        ir = Stage4InterviewRound(ctx)
        prev_manuscripts_text = "[제2화] " + ("history " * 30)

        history = ir.post_select_runtime.build_manuscript_history_for_check(prev_manuscripts_text, next_ep=3)

        assert len(history) == 1
        assert history[0]["ep_num"] == 2
        assert "history" in history[0]["text"]

    def test_director_sc5_legacy_fallback_without_advisor(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "pass manuscript", "title": "pass"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        continuity_call = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs
        history_call = ctx.agents["director"].check_manuscript_history_conflicts.call_args.kwargs
        assert continuity_call["memory_context"] == ""
        assert history_call["memory_context"] == ""

    def test_director_sc5_advisor_dispatches_memory_context(self):
        ctx = _make_ctx()
        ctx.context_advisor = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "vec memory block"
        ctx.memory.retrieve_npc_context.return_value = "npc memory block"
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=3,
            slots=[
                RetrievalSlot(category="event_claim", query="event query", source="vec_memory", priority=1),
                RetrievalSlot(category="npc_consistency", query="alice bob", source="db_npc_history", priority=1),
            ],
            total_budget_chars=20000,
        )

        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.blueprint = {"characters": [{"name": "alice"}, {"name": "bob"}], "integrated_scenario": "x"}
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "pass manuscript", "title": "pass"},
            "state_updates": {},
        }

        def _threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.director_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            if key == "smart_retrieval.director_total_budget":
                return 20000
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect):
            ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        ctx.context_advisor.plan_director_retrieval.assert_called_once()
        ctx.memory.retrieve_multi_query_context.assert_called()
        ctx.memory.retrieve_npc_context.assert_called()

        continuity_ctx = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs[
            "memory_context"
        ]
        history_ctx = ctx.agents["director"].check_manuscript_history_conflicts.call_args.kwargs["memory_context"]
        assert continuity_ctx
        assert history_ctx
        assert continuity_ctx == history_ctx
        assert "[SC:" in continuity_ctx

    def test_director_sc5_injects_work_focus_and_relation_slice(self):
        ctx = _make_ctx()
        ctx.context_advisor = MagicMock()
        ctx.quality_dashboard = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "vec memory block"
        ctx.memory.retrieve_npc_context.return_value = "npc memory block"
        ctx.current_project.db.get_relationship_history.return_value = [
            {"change_ep": 7, "old_relation": "소꿉친구", "new_relation": "멀어진 동료"}
        ]
        ctx.sys = MagicMock()
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.select_retrieval_focus.return_value = {
            "tracking_slots": ["소꿉친구 관계선"],
            "mandatory_scene_engines": ["관계 반전"],
            "registry_profiles": [{"name": "relationship_registry", "purpose": "주인공의 오래된 인연 추적"}],
        }
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=3,
            slots=[
                RetrievalSlot(
                    category="relationship_consistency",
                    query="한태하 연홍 관계선",
                    source=RetrievalSources.DB_NPC_RELATIONSHIP,
                    priority=1,
                ),
            ],
            total_budget_chars=20000,
        )

        ir = Stage4InterviewRound(ctx)
        ir._resolve_director_protagonist_name = MagicMock(return_value="한태하")
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.prev_ending = "연홍과의 관계가 흔들린 채 끝난다."
        round_ctx.blueprint = {
            "characters": [{"name": "한태하"}, {"name": "연홍"}],
            "core_event": "오래된 인연이 시험받는다",
            "story_goal": "연홍의 진심을 확인한다",
            "integrated_scenario": "x",
        }
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "pass manuscript", "title": "pass"},
            "state_updates": {},
        }

        def _threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.director_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            if key == "smart_retrieval.director_total_budget":
                return 20000
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect):
            ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        call_kwargs = ctx.context_advisor.plan_director_retrieval.call_args.kwargs
        assert call_kwargs["work_focus"]["tracking_slots"] == ["소꿉친구 관계선"]
        continuity_ctx = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs[
            "memory_context"
        ]
        ctx.quality_dashboard.record_retrieval_observation.assert_called_once()
        kwargs = ctx.quality_dashboard.record_retrieval_observation.call_args.kwargs
        assert kwargs["stage"] == "director"
        assert kwargs["observation"]["relation_slice_included"] is True
        assert "[작품 추적 슬롯 요약]" in continuity_ctx
        assert "[관계 의미 질의]" in continuity_ctx
        assert "[SC:relationship_consistency]" in continuity_ctx
        ctx.current_project.db.get_relationship_history.assert_called()

    def test_post_select_continuity_conflict_downgrades_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "selected manuscript", "title": "selected"},
            "state_updates": {},
            "feedback": {"issues": []},
            "action_items": [],
        }
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "CONFLICT",
            "summary": "dead npc appears again",
        }
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {
            "decision": "PASS",
            "summary": "",
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        rejection_reason = result.previous_attempt.get("rejection_reason", "") if result.previous_attempt else ""
        assert "[Continuity Conflict]" in rejection_reason
        ctx.agents["director"].check_manuscript_continuity_with_cache.assert_called_once()

    def test_post_select_history_conflict_downgrades_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "[제2화]\n" + ("history " * 60)
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "selected manuscript", "title": "selected"},
            "state_updates": {},
            "feedback": {"issues": []},
            "action_items": [],
        }
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "PASS",
            "summary": "",
        }
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {
            "decision": "CONFLICT",
            "summary": "location mismatch",
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        rejection_reason = result.previous_attempt.get("rejection_reason", "") if result.previous_attempt else ""
        assert "[V67] History Conflict:" in rejection_reason
        ctx.agents["director"].check_manuscript_history_conflicts.assert_called_once()

    def test_post_select_no_conflict_keeps_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "[제2화]\n" + ("history " * 60)
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "selected manuscript", "title": "selected"},
            "state_updates": {},
        }
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "PASS",
            "summary": "",
        }
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {
            "decision": "PASS",
            "summary": "",
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "PASS"
        assert result.final_manuscript == "selected manuscript"

    def test_pre_selection_no_llm_continuity_check(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "[제2화]\n" + ("history " * 60)
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate(), _candidate(), _candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [
            _validation_result(),
            _validation_result(),
            _validation_result(),
        ]

        def _select_side_effect(*args, **kwargs):
            assert ctx.agents["director"].check_manuscript_continuity_with_cache.call_count == 0
            assert ctx.agents["director"].check_manuscript_history_conflicts.call_count == 0
            return {
                "selected": "A",
                "verdict": "REJECT",
                "score": 40,
                "selection_reason": "reject",
                "feedback": {"issues": ["issue"]},
                "action_items": ["fix"],
                "selected_candidate": {"manuscript": "candidate manuscript"},
            }

        ctx.agents["director"].select_and_judge_ensemble.side_effect = _select_side_effect

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        assert ctx.agents["director"].check_manuscript_continuity_with_cache.call_count == 0
        assert ctx.agents["director"].check_manuscript_history_conflicts.call_count == 0


class TestRecordS4Attempt:
    """Stage 4 PassRateMonitor 기록 테스트."""

    def test_pass_records_success(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "좋음",
            "selected_candidate": {"manuscript": "통과 원고", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["stage"] == 4
        assert kw["success"] is True
        assert kw["generation_method"] == "ensemble"
        assert kw["is_patch"] is False
        assert kw["arc"] == 1
        assert kw["attempt_key"] == "s4:ep1:arc1:a1"
        assert kw["final_verdict"] == "PASS"

    def test_reject_records_failure(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 40,
            "selection_reason": "부족",
            "feedback": {"issues": ["문제"]},
            "action_items": ["수정1"],
            "selected_candidate": {"manuscript": "거절 원고"},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["success"] is False
        assert kw["reject_reason"] == "수정1"
        assert kw["arc"] == 1
        assert kw["attempt_key"] == "s4:ep1:arc1:a1"
        assert kw["final_verdict"] == "REJECT"

    def test_record_s4_attempt_persists_semantic_failure_fields(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        advisory_flags = {
            "gate_semantics": {
                "director_verdict": "PASS_WITH_FIX",
                "gate_basis": "bounded_local_repair",
                "repair_scope": "inplace",
            },
            "fix_pack": {
                "patch_targets": ["opening_location_name", "ending_location_name"],
                "must_fix": ["rename both location anchors"],
                "do_not_regress": ["scene mood", "timeline"],
                "success_condition": "Only the two location anchors change.",
                "target_kind": "entity_ref",
            },
            "retry_budget_axes": {"round": 1, "repair": 1, "guidance": 0},
        }

        ir._record_s4_attempt(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            verdict="REJECT",
            reject_reason="retry needed",
            advisory_flags=advisory_flags,
            error_category="LOGIC_ERROR",
            reject_bucket="post_select_conflict",
            score_breakdown={"narrative_flow": 9},
        )

        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["error_category"] == "LOGIC_ERROR"
        assert kw["reject_bucket"] == "post_select_conflict"
        assert kw["score_breakdown"]["narrative_flow"] == 9
        assert kw["director_verdict"] == "PASS_WITH_FIX"
        assert kw["gate_basis"] == "bounded_local_repair"
        assert kw["repair_scope"] == "inplace"
        assert kw["fix_pack"]["patch_targets"] == ["opening_location_name", "ending_location_name"]
        assert kw["retry_budget_axes"] == {"round": 1, "repair": 1, "guidance": 0}

    def test_build_stage4_attempt_artifact_meta_defaults_without_payload(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        meta = ir._build_stage4_attempt_artifact_meta(
            episode=1,
            round_num=0,
            arc=1,
            candidate_key="A|balanced",
            artifact_kind="final_manuscript",
            artifact_payload=None,
        )

        assert meta == {
            "candidate_key": "A|balanced",
            "content_hash": "",
            "artifact_path": "",
        }

    def test_extract_stage4_advisory_contract_payloads_ignores_non_dict_sections(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        gate_semantics, fix_pack, repair_contract, retry_budget_axes = ir._extract_stage4_advisory_contract_payloads(
            {
                "gate_semantics": {"director_verdict": "PASS_WITH_FIX"},
                "fix_pack": ["not-a-dict"],
                "retry_budget_axes": {"round": 1},
            }
        )

        assert gate_semantics == {"director_verdict": "PASS_WITH_FIX"}
        assert fix_pack == {}
        assert repair_contract == {}
        assert retry_budget_axes == {"round": 1}

    def test_build_stage4_pass_rate_attempt_payload_extracts_gate_semantics(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir._build_stage4_pass_rate_attempt_payload(
            episode=2,
            round_num=1,
            score=61,
            arc=1,
            success=False,
            reject_reason="retry needed",
            is_patch=True,
            patch_fallback=False,
            duration_ms=321,
            token_cost=0.125,
            prev_score=55,
            attempt_key="s4:ep2:arc1:a2",
            verdict="REJECT",
            advisory_flags={
                "gate_semantics": {
                    "director_verdict": "PASS_WITH_FIX",
                    "gate_basis": "bounded_local_repair",
                    "repair_scope": "inplace",
                    "strong_advisory_escalation": {
                        "source_verdict": "PASS",
                        "escalated_to": "PASS_WITH_FIX",
                        "triggered_by": ["truth_gate"],
                    },
                },
                "fix_pack": {
                    "must_fix": ["repair ending"],
                    "target_kind": "local_sentence",
                    "subtype": "movement",
                    "provenance": "runtime_synthesized",
                },
                "repair_contract": {
                    "subtype": "movement",
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "target_kind": "local_sentence",
                    "provenance": "runtime_synthesized",
                },
                "retry_budget_axes": {"round": 1, "repair": 1, "guidance": 0},
            },
            patch_strategy="patch_with_feedback",
            structural_attempted=True,
            error_category="LOGIC_ERROR",
            reject_bucket="post_select_conflict",
            score_breakdown={"narrative_flow": 9},
            artifact_meta={
                "candidate_key": "A|balanced",
                "content_hash": "hash123",
                "artifact_path": "logs/final.txt",
            },
        )

        assert payload["generation_method"] == "patch"
        assert payload["director_verdict"] == "PASS_WITH_FIX"
        assert payload["gate_basis"] == "bounded_local_repair"
        assert payload["repair_scope"] == "inplace"
        assert payload["fix_scope"] == "inplace"
        assert payload["authoritative_fix_scope"] == ""
        assert payload["strong_advisory_escalation"]["triggered_by"] == ["truth_gate"]
        assert payload["fix_pack"]["must_fix"] == ["repair ending"]
        assert payload["fix_pack"]["provenance"] == "runtime_synthesized"
        assert payload["repair_contract"]["subtype"] == "movement"
        assert payload["repair_contract"]["provenance"] == "runtime_synthesized"
        assert payload["scope_authority"] == {
            "fix_scope": "inplace",
            "repair_scope": "inplace",
            "widened": False,
        }
        assert payload["retry_budget_axes"] == {"round": 1, "repair": 1, "guidance": 0}
        assert payload["candidate_key"] == "A|balanced"
        assert payload["artifact_path"] == "logs/final.txt"

    def test_resolve_stage4_db_attempt_advisory_flags_uses_last_summary_fallback(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._last_advisory_summary = {"continuity": ["keep timeline"]}

        resolved = ir._resolve_stage4_db_attempt_advisory_flags(None)

        assert resolved == {"continuity": ["keep timeline"]}

    def test_resolve_stage4_db_attempt_advisory_flags_backfills_nested_gate_repair_contract(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        resolved = ir._resolve_stage4_db_attempt_advisory_flags(
            {
                "gate_semantics": {
                    "director_verdict": "REJECT",
                    "final_verdict": "REJECT",
                    "gate_basis": "continuity_firewall",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "scope_origin": {
                        "fix_scope": "director_authoritative",
                        "authoritative_fix_scope": "director_authoritative",
                        "repair_scope": "runtime_lane",
                    },
                    "repair_contract": {
                        "subtype": "수치",
                        "fix_scope": "inplace",
                        "repair_scope": "inplace",
                        "authoritative_fix_scope": "inplace",
                        "scope_origin": {
                            "fix_scope": "director_authoritative",
                            "authoritative_fix_scope": "director_authoritative",
                            "repair_scope": "runtime_lane",
                        },
                    },
                    "scope_authority": {
                        "fix_scope": "inplace",
                        "repair_scope": "inplace",
                        "authoritative_fix_scope": "inplace",
                        "scope_origin": {
                            "fix_scope": "director_authoritative",
                            "authoritative_fix_scope": "director_authoritative",
                            "repair_scope": "runtime_lane",
                        },
                        "widened": False,
                    },
                },
                "fix_pack": {},
                "retry_budget_axes": {"repair": "rewrite_regenerate"},
            }
        )

        assert resolved["repair_contract"]["subtype"] == "수치"
        assert resolved["repair_contract"]["fix_scope"] == "inplace"
        assert resolved["scope_authority"]["authoritative_fix_scope"] == "inplace"
        assert resolved["scope_authority"]["widened"] is False

    def test_resolve_stage4_db_attempt_advisory_flags_prefers_nested_gate_scope_over_stale_root(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        resolved = ir._resolve_stage4_db_attempt_advisory_flags(
            {
                "gate_semantics": {
                    "director_verdict": "REJECT",
                    "gate_basis": "continuity_firewall",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "partial",
                    "repair_contract": {
                        "subtype": "수학",
                        "fix_scope": "partial",
                        "repair_scope": "partial",
                        "authoritative_fix_scope": "partial",
                    },
                    "scope_authority": {
                        "fix_scope": "partial",
                        "repair_scope": "partial",
                        "authoritative_fix_scope": "partial",
                        "widened": False,
                    },
                },
                "repair_contract": {
                    "subtype": "수학",
                    "fix_scope": "full",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "partial",
                },
                "scope_authority": {
                    "fix_scope": "full",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "partial",
                    "widened": True,
                },
            }
        )

        assert resolved["repair_contract"]["fix_scope"] == "partial"
        assert resolved["scope_authority"]["fix_scope"] == "partial"
        assert resolved["scope_authority"]["widened"] is False

    def test_resolve_stage4_db_attempt_model_uses_director_primary_model(self):
        ctx = _make_ctx()
        ctx.agents["director"].primary_model = "gemini-2.5-pro"
        ir = Stage4InterviewRound(ctx)

        resolved = ir._resolve_stage4_db_attempt_model(None)

        assert resolved == "gemini-2.5-pro"

    def test_build_stage4_db_attempt_payload_uses_fallback_advisory_and_model(self):
        ctx = _make_ctx()
        ctx.agents["director"].primary_model = "gemini-2.5-pro"
        ir = Stage4InterviewRound(ctx)
        ir._last_advisory_summary = {"continuity": ["keep timeline"]}

        payload = ir._build_stage4_db_attempt_payload(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            arc=1,
            verdict="REJECT",
            reject_reason="retry needed",
            fix_scope="inplace",
            model=None,
            duration_ms=222,
            advisory_flags=None,
            session_id="sess-stage4",
            attempt_key="s4:ep2:arc1:a2:sess-stage4",
            artifact_meta={
                "candidate_key": "A|balanced",
                "content_hash": "hash123",
                "artifact_path": "logs/final.txt",
            },
            selection_reason="best candidate",
            verdict_reason="conflict",
            open_review="repeat detected",
            fix_scope_reasoning="bounded fix",
            runtime_advisory="keep continuity",
            retry_directives="change ending",
            failure_category="LOGIC_ERROR",
            initial_verdict="PASS_WITH_FIX",
            score_breakdown={"narrative_flow": 9},
            is_patch=True,
            is_patch_fallback=False,
            patch_strategy="patch_with_feedback",
        )

        assert payload["model"] == "gemini-2.5-pro"
        assert payload["advisory_flags"] == {"continuity": ["keep timeline"]}
        assert payload["attempt_key"] == "s4:ep2:arc1:a2:sess-stage4"
        assert payload["selection_reason"] == "best candidate"
        assert payload["artifact_path"] == "logs/final.txt"
        assert payload["failure_category"] == "LOGIC_ERROR"
        assert payload["initial_verdict"] == "PASS_WITH_FIX"
        assert payload["score_breakdown"] == {"narrative_flow": 9}
        assert payload["is_patch"] is True
        assert payload["is_patch_fallback"] is False
        assert payload["patch_strategy"] == "patch_with_feedback"

    def test_build_stage4_db_attempt_payload_prefers_resolved_scope_authority_fix_scope(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir._build_stage4_db_attempt_payload(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            arc=1,
            verdict="REJECT",
            reject_reason="retry needed",
            fix_scope="inplace",
            model="gemini-2.5-pro",
            duration_ms=222,
            advisory_flags={
                "gate_semantics": {
                    "director_verdict": "PASS_WITH_FIX",
                    "final_verdict": "REJECT",
                    "gate_basis": "quality_floor_fail",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "inplace",
                    "scope_origin": {
                        "fix_scope": "runtime_widened",
                        "authoritative_fix_scope": "director_authoritative",
                        "repair_scope": "runtime_lane",
                    },
                    "scope_authority": {
                        "fix_scope": "partial",
                        "repair_scope": "partial",
                        "authoritative_fix_scope": "inplace",
                        "scope_origin": {
                            "fix_scope": "runtime_widened",
                            "authoritative_fix_scope": "director_authoritative",
                            "repair_scope": "runtime_lane",
                        },
                        "widened": True,
                    },
                },
                "repair_contract": {
                    "subtype": "movement",
                    "fix_scope": "partial",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "inplace",
                    "provenance": "director_authored",
                },
                "scope_authority": {
                    "fix_scope": "partial",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "inplace",
                    "scope_origin": {
                        "fix_scope": "runtime_widened",
                        "authoritative_fix_scope": "director_authoritative",
                        "repair_scope": "runtime_lane",
                    },
                    "widened": True,
                },
            },
            session_id="sess-stage4",
            attempt_key="s4:ep2:arc1:a2:sess-stage4",
            artifact_meta={
                "candidate_key": "A|balanced",
                "content_hash": "hash123",
                "artifact_path": "logs/final.txt",
            },
            selection_reason="best candidate",
            verdict_reason="conflict",
            open_review="repeat detected",
            fix_scope_reasoning="bounded fix",
            runtime_advisory="keep continuity",
            retry_directives="change ending",
            failure_category="LOGIC_ERROR",
            initial_verdict="PASS_WITH_FIX",
            score_breakdown={"narrative_flow": 9},
            is_patch=False,
            is_patch_fallback=False,
            patch_strategy="",
        )

        assert payload["fix_scope"] == "partial"
        assert payload["advisory_flags"]["scope_authority"]["fix_scope"] == "partial"
        assert payload["advisory_flags"]["scope_authority"]["authoritative_fix_scope"] == "inplace"

    def test_build_stage4_db_attempt_payload_prefers_root_scope_authority_fix_scope(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir._build_stage4_db_attempt_payload(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            arc=1,
            verdict="REJECT",
            reject_reason="retry needed",
            fix_scope="inplace",
            model="gemini-2.5-pro",
            duration_ms=222,
            advisory_flags={
                "scope_authority": {
                    "fix_scope": "partial",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "inplace",
                    "widened": True,
                }
            },
            session_id="sess-stage4-root-scope",
            attempt_key="s4:ep2:arc1:a2:sess-stage4-root-scope",
            artifact_meta={
                "candidate_key": "A|balanced",
                "content_hash": "hash123",
                "artifact_path": "logs/final.txt",
            },
            selection_reason="best candidate",
            verdict_reason="conflict",
            open_review="repeat detected",
            fix_scope_reasoning="bounded fix",
            runtime_advisory="keep continuity",
            retry_directives="change ending",
            failure_category="LOGIC_ERROR",
            initial_verdict="PASS_WITH_FIX",
            score_breakdown={"narrative_flow": 9},
            is_patch=False,
            is_patch_fallback=False,
            patch_strategy="",
        )

        assert payload["fix_scope"] == "partial"
        assert payload["advisory_flags"]["scope_authority"]["fix_scope"] == "partial"
        assert payload["advisory_flags"]["scope_authority"]["authoritative_fix_scope"] == "inplace"

    def test_build_stage4_patch_advisory_payload_promotes_structured_targets_and_trace(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir._build_stage4_patch_advisory_payload(
            director_result={
                "fix_pack": {
                    "patch_targets": ["opening_location_name"],
                    "must_fix": ["rename opening location"],
                    "do_not_regress": ["timeline"],
                    "success_condition": "opening label is corrected",
                    "target_kind": "entity_ref",
                }
            },
            patch_trace={
                "patch_strategy": "inplace_patch_local_ops",
                "patch_round": 2,
                "patch_targets": ["opening_location_name"],
                "repair_trace": [
                    {
                        "old_excerpt": "old venue",
                        "new_excerpt": "new venue",
                        "why_changed": "rename opening location",
                    }
                ],
                "guard_result": {"status": "pass"},
            },
        )

        assert payload["fix_pack"]["patch_target_records"][0]["summary"] == "opening_location_name"
        assert payload["fix_pack"]["patch_target_records"][0]["target_kind"] == "entity_ref"
        assert payload["partial_fix_eval"]["patch_round"] == 2
        assert payload["partial_fix_eval"]["patch_target_id"].startswith("pt:")
        assert payload["repair_trace"][0]["guard_result"]["status"] == "pass"
        assert payload["repair_trace"][0]["new_excerpt"] == "new venue"

    def test_log_session_decision_surfaces_authoritative_fix_scope_metadata(self):
        ctx = _make_ctx()
        ctx.session_logger = MagicMock()
        ir = Stage4InterviewRound(ctx)

        ir._log_session_decision(
            next_ep=2,
            round_num=1,
            arc_num=1,
            verdict="REJECT",
            score=50,
            selected="A",
            error_category="QUALITY_ISSUE",
            reason="reason",
            fix_scope="partial",
            open_review="review",
            action_items=["fix"],
            attempt_key="attempt-1",
            authoritative_fix_scope="",
            authoritative_fix_scope_violation={"type": "blank_authoritative_fix_scope"},
            scope_origin={
                "fix_scope": "director_authoritative",
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
            repair_contract={
                "subtype": "movement",
                "fix_scope": "partial",
                "repair_scope": "partial",
                "provenance": "runtime_synthesized",
            },
            scope_authority={
                "fix_scope": "partial",
                "repair_scope": "partial",
                "authoritative_fix_scope": "",
                "scope_origin": {
                    "fix_scope": "director_authoritative",
                    "authoritative_fix_scope": "director_authoritative",
                    "repair_scope": "runtime_lane",
                },
                "authoritative_fix_scope_violation": {"type": "blank_authoritative_fix_scope"},
                "widened": False,
            },
        )

        kwargs = ctx.session_logger.log_decision.call_args.kwargs
        assert kwargs["fix_scope"] == "partial"
        assert kwargs["authoritative_fix_scope"] == ""
        assert kwargs["authoritative_fix_scope_violation"] == {"type": "blank_authoritative_fix_scope"}
        assert kwargs["scope_origin"] == {
            "fix_scope": "director_authoritative",
            "authoritative_fix_scope": "director_authoritative",
            "repair_scope": "runtime_lane",
        }
        assert kwargs["repair_contract"] == {
            "subtype": "movement",
            "fix_scope": "partial",
            "repair_scope": "partial",
            "provenance": "runtime_synthesized",
        }
        assert kwargs["scope_authority"] == {
            "fix_scope": "partial",
            "repair_scope": "partial",
            "authoritative_fix_scope": "",
            "scope_origin": {
                "fix_scope": "director_authoritative",
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
            "authoritative_fix_scope_violation": {"type": "blank_authoritative_fix_scope"},
            "widened": False,
        }

    def test_log_pass_session_decision_uses_logging_payload_fix_pack(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        ctx = _make_ctx()
        ctx.session_logger = MagicMock()
        ir = Stage4InterviewRound(ctx)

        payload = _PassResultLoggingPayload(
            log_artifact_meta={
                "candidate_key": "A|patched",
                "content_hash": "hash-final",
                "artifact_path": "artifacts/final.txt",
            },
            session_selection_reason="final selection",
            session_verdict_reason="final verdict",
            session_runtime_advisory="runtime digest",
            session_retry_directives="retry digest",
            session_gate_semantics={
                "director_verdict": "PASS",
                "gate_basis": "patch_reaudit_pass",
                "repair_scope": "inplace",
            },
            session_fix_pack={
                "patch_targets": ["name_anchor"],
                "must_fix": ["rename family anchor"],
                "do_not_regress": ["ending hook"],
                "success_condition": "anchor renamed",
                "target_kind": "entity_ref",
            },
        )

        ir._log_pass_session_decision(
            next_ep=1,
            round_num=0,
            arc_num=1,
            director_result={"fix_scope": "inplace"},
            trace_director_result={},
            final_verdict="PASS",
            final_score=90,
            selected="A",
            reason="legacy reason",
            error_category="",
            attempt_key="s4:ep1:arc1:a1:test",
            selection_artifact_meta={
                "candidate_key": "A|pre",
                "content_hash": "hash-pre",
                "artifact_path": "artifacts/pre.txt",
            },
            initial_verdict="PASS_WITH_FIX",
            initial_score=90,
            logging_payload=payload,
        )

        call_kwargs = ctx.session_logger.log_decision.call_args.kwargs
        assert call_kwargs["fix_pack"]["target_kind"] == "entity_ref"
        assert call_kwargs["fix_pack"]["patch_targets"] == ["name_anchor"]
        assert call_kwargs["reason"] == "legacy reason"
        assert call_kwargs["selection_reason"] == "final selection"
        assert call_kwargs["verdict_reason"] == "final verdict"

    def test_record_stage4_pass_rate_attempt_uses_prelude_payload(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        prelude = _Stage4AttemptPreludePayload(
            duration_ms=321,
            token_cost=0.125,
            session_id="sess-stage4",
            attempt_key="s4:ep2:arc1:a2:sess-stage4",
            normalized_patch_strategy="patch_with_feedback",
            artifact_meta={
                "candidate_key": "A|balanced",
                "content_hash": "hash123",
                "artifact_path": "logs/final.txt",
            },
        )

        ir._record_stage4_pass_rate_attempt(
            episode=2,
            round_num=1,
            score=61,
            arc=1,
            success=False,
            reject_reason="retry needed",
            is_patch=True,
            patch_fallback=False,
            prev_score=55,
            verdict="REJECT",
            advisory_flags=None,
            structural_attempted=True,
            error_category="LOGIC_ERROR",
            reject_bucket="post_select_conflict",
            score_breakdown={"narrative_flow": 9},
            prelude=prelude,
        )

        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["attempt_key"] == "s4:ep2:arc1:a2:sess-stage4"
        assert kw["patch_strategy"] == "patch_with_feedback"
        assert kw["artifact_path"] == "logs/final.txt"

    def test_save_stage4_db_attempt_uses_prelude_payload(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        prelude = _Stage4AttemptPreludePayload(
            duration_ms=222,
            token_cost=0.0,
            session_id="sess-stage4",
            attempt_key="s4:ep2:arc1:a2:sess-stage4",
            normalized_patch_strategy="patch_with_feedback",
            artifact_meta={
                "candidate_key": "A|balanced",
                "content_hash": "hash123",
                "artifact_path": "logs/final.txt",
            },
        )

        ir._save_stage4_db_attempt(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            arc=1,
            verdict="REJECT",
            reject_reason="retry needed",
            fix_scope="inplace",
            model="gemini-2.5-pro",
            advisory_flags={"continuity": ["keep timeline"]},
            selection_reason="best candidate",
            verdict_reason="conflict",
            open_review="repeat detected",
            fix_scope_reasoning="bounded fix",
            runtime_advisory="keep continuity",
            retry_directives="change ending",
            error_category="LOGIC_ERROR",
            initial_verdict="PASS_WITH_FIX",
            score_breakdown={"continuity": 0},
            is_patch=True,
            is_patch_fallback=False,
            patch_strategy="patch_with_feedback",
            prelude=prelude,
        )

        kw = ctx.current_project.db.save_stage_attempt.call_args.kwargs
        assert kw["session_id"] == "sess-stage4"
        assert kw["attempt_key"] == "s4:ep2:arc1:a2:sess-stage4"
        assert kw["artifact_path"] == "logs/final.txt"
        assert kw["failure_category"] == "LOGIC_ERROR"
        assert kw["initial_verdict"] == "PASS_WITH_FIX"
        assert kw["score_breakdown"] == {"continuity": 0}
        assert kw["is_patch"] is True
        assert kw["is_patch_fallback"] is False
        assert kw["patch_strategy"] == "patch_with_feedback"

    def test_attempt_key_uses_metrics_session_id_when_available(self):
        ctx = _make_ctx()
        ctx.current_project.metrics_session_id = "sess_stage4"
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)

        ir._record_s4_attempt(episode=1, round_num=0, success=True, score=95, arc=1, verdict="PASS")

        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["attempt_key"] == "s4:ep1:arc1:a1:sess_stage4"
        db_kw = ctx.current_project.db.save_stage_attempt.call_args.kwargs
        assert db_kw["attempt_key"] == "s4:ep1:arc1:a1:sess_stage4"
        assert db_kw["session_id"] == "sess_stage4"

    @patch("modules.core.stage4_interview_round.time.monotonic", return_value=110.0)
    def test_build_stage4_attempt_prelude_defaults_runtime_and_patch_strategy(self, _mock_monotonic):
        ctx = _make_ctx()
        ctx.current_project.metrics_session_id = "sess_stage4"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = 100.0
        ir._get_round_metrics_delta = MagicMock(return_value={"total_cost_usd": 0.25})

        prelude = ir._build_stage4_attempt_prelude(
            episode=2,
            round_num=1,
            arc=3,
            is_patch=True,
            patch_fallback=True,
            patch_strategy="",
            candidate_key="A|balanced",
            artifact_kind="final_manuscript",
            artifact_payload=None,
            duration_ms=None,
            token_cost=None,
        )

        assert prelude.duration_ms == 10000
        assert prelude.token_cost == 0.25
        assert prelude.session_id == "sess_stage4"
        assert prelude.attempt_key == "s4:ep2:arc3:a2:sess_stage4"
        assert prelude.normalized_patch_strategy == "patch_fallback_rewrite"
        assert prelude.artifact_meta["candidate_key"] == "A|balanced"

    def test_record_s4_attempt_defaults_patch_strategy_for_direct_patch(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)

        ir._record_s4_attempt(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            is_patch=True,
            patch_fallback=False,
            arc=1,
            verdict="REJECT",
            reject_reason="retry needed",
        )

        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["is_patch"] is True
        assert kw["generation_method"] == "patch"
        assert kw["patch_strategy"] == "patch_with_feedback"

    def test_record_s4_attempt_defaults_patch_strategy_for_patch_fallback(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)

        ir._record_s4_attempt(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            is_patch=True,
            patch_fallback=True,
            arc=1,
            verdict="REJECT",
            reject_reason="retry needed",
        )

        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["is_patch"] is True
        assert kw["generation_method"] == "ensemble"
        assert kw["patch_strategy"] == "patch_fallback_rewrite"

    def test_patch_records_method_patch(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.inplace_patch.return_value = []  # [TF-23] InPlace 실패 → Patch 폴백
        round_ctx.chief_writer.patch_with_feedback.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 80,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=1,
            stage4_spinner=MagicMock(),
            director_feedback="피드백",
            previous_attempt={
                "score": 70,
                "best_manuscript": "원고",
                "fix_scope": "partial",
                "reject_bucket": "post_select_conflict",
                "fix_pack": _local_fix_pack(),
            },
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["is_patch"] is True
        assert kw["generation_method"] == "patch"
        assert kw["prev_score"] == 70
        assert kw["arc"] == 1
        assert kw["attempt_key"] == "s4:ep1:arc1:a2"

    def test_patch_run_moves_patch_provenance_into_advisory_metadata(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.inplace_patch.return_value = []
        round_ctx.chief_writer.patch_with_feedback.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 80,
            "selection_reason": "ok",
            "selected_candidate": _candidate(),
            "state_updates": {},
        }

        ir.run(
            round_num=1,
            stage4_spinner=MagicMock(),
            director_feedback="feedback",
            previous_attempt={
                "score": 70,
                "best_manuscript": "draft",
                "fix_scope": "partial",
                "reject_bucket": "post_select_conflict",
                "fix_pack": _local_fix_pack(),
            },
            round_ctx=round_ctx,
        )

        db_kwargs = ctx.current_project.db.save_director_selection.call_args.kwargs
        assert db_kwargs["selection_reason"] == "ok"
        assert db_kwargs["advisory_warnings"]["patch_context"] == {"tag": "patch", "score": 70}

    def test_patch_fallback_records_method_ensemble(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.inplace_patch.return_value = []  # [TF-23] InPlace 실패
        round_ctx.chief_writer.patch_with_feedback.return_value = []
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 82,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "통과", "title": "통과"},
            "state_updates": {},
        }

        ir.run(
            round_num=1,
            stage4_spinner=MagicMock(),
            director_feedback="피드백",
            previous_attempt={
                "score": 70,
                "best_manuscript": "원고",
                "fix_scope": "partial",
                "reject_bucket": "post_select_conflict",
                "fix_pack": _local_fix_pack(),
            },
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["is_patch"] is True
        assert kw["patch_fallback"] is True
        assert kw["generation_method"] == "ensemble"
        assert kw["attempt_key"] == "s4:ep1:arc1:a2"
        round_ctx.chief_writer.regenerate_with_feedback.assert_called_once()

    def test_empty_candidates_records_failure(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = []

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["success"] is False
        assert kw["reject_reason"] == "empty_candidates"
        assert kw["arc"] == 1
        assert kw["attempt_key"] == "s4:ep1:arc1:a1"
        assert kw["final_verdict"] == "EMPTY"

    def test_source_defaults_align_with_validation_yaml(self):
        src = "\n".join(
            [
                Path("modules/core/stage4_interview_round.py").read_text(encoding="utf-8"),
                Path("modules/core/stage4_director_runtime.py").read_text(encoding="utf-8"),
            ]
        )

        assert '_threshold("smart_retrieval.enabled", True)' in src
        assert '_threshold("smart_retrieval.director_enabled", True)' in src
        assert '_threshold("context.vector_max_results_s4", 50)' in src
        assert '_threshold("smart_retrieval.slot_max_chars_default", 3000)' in src
        assert '_threshold("smart_retrieval.director_total_budget", 300000)' in src

    def test_save_director_selection_persists_verdict_metadata(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 44,
            "pre_firewall_score": 100,
            "selection_reason": "최우수 후보 선택",
            "verdict_reason": "Contradiction Firewall: CRITICAL 1건",
            "firewall_triggered": True,
            "firewall_reason": "Contradiction Firewall: CRITICAL 1건",
            "feedback": {"issues": ["중대 모순"]},
            "action_items": ["마지막 장면 수정"],
            "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        ctx.current_project.db.save_director_selection.assert_called_once()
        kw = ctx.current_project.db.save_director_selection.call_args.kwargs
        assert kw["selection_reason"] == "최우수 후보 선택"
        assert kw["verdict_reason"] == "Contradiction Firewall: CRITICAL 1건"
        assert kw["pre_firewall_score"] == 100
        assert kw["firewall_triggered"] is True
        assert kw["firewall_reason"] == "Contradiction Firewall: CRITICAL 1건"

    def test_save_director_selection_persists_artifact_linkage(self, tmp_path):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.root = tmp_path
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 44,
            "selection_reason": "best candidate",
            "verdict_reason": "conflict",
            "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
            "feedback": {"issues": ["conflict"]},
            "action_items": ["fix ending"],
        }

        with patch("builtins.open", mock_open()), patch("os.makedirs"):
            ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        kw = ctx.current_project.db.save_director_selection.call_args.kwargs
        assert kw["candidate_key"] == "A|balanced"
        assert kw["content_hash"]
        assert kw["artifact_path"].endswith("rejected_best__A_balanced.txt")
        assert (tmp_path / kw["artifact_path"]).exists()

    def test_post_select_conflict_preserves_patch_seed_metadata(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 2
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "CONFLICT",
            "summary": "continuity mismatch",
        }

        verdict, director_feedback, previous_attempt, error_category = ir.post_select_runtime.run_post_select_checks(
            verdict="PASS",
            final_manuscript="patched manuscript",
            final_state_updates={},
            next_ep=2,
            round_num=0,
            round_ctx=round_ctx,
            director_result={
                "selected_candidate": {
                    "manuscript": "patched manuscript",
                    "strategy": "tension",
                    "strategy_name": "tension",
                },
                "selection_reason": "best candidate",
                "verdict_reason": "director pass before post-select",
                "fix_scope": "",
                "open_review": "",
                "fix_pack": _local_fix_pack("opening_location_name", target_kind="entity_ref"),
                "action_items": ["fix the opening location"],
            },
            director_feedback="initial feedback",
            score=95,
            error_category="",
            previous_attempt={},
            stage4_spinner=MagicMock(),
            director_memory_context="",
        )

        assert verdict == "REJECT"
        assert error_category == "POST_SELECT_CONTINUITY_CONFLICT"
        assert "[Continuity Conflict]" in director_feedback
        assert previous_attempt["fix_scope"] == "full"
        assert previous_attempt["selected_strategy_key"] == "tension"
        assert previous_attempt["selection_reason"] == "best candidate"
        assert previous_attempt["verdict_reason"] == "director pass before post-select"
        assert previous_attempt["reject_bucket"] == "post_select_conflict"
        assert previous_attempt["retry_pathology_source"] == "post_select_conflict"
        assert previous_attempt["provisional_pass_downgrade"] is True
        assert previous_attempt["fix_pack"]["patch_targets"] == ["opening_location_name"]
        assert previous_attempt["action_items"] == ["fix the opening location"]
        assert previous_attempt["reuse_contract"]["mode"] == "best_manuscript_baseline"
        assert previous_attempt["conflict_contract"]["contract_type"] == "post_select_conflict"
        assert previous_attempt["conflict_contract"]["conflicts"][0]["conflict_type"] == "continuity"

    def test_post_select_checks_run_on_retry_rounds_too(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "━━━ 제1화 원고 ━━━\n이전 원고"
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "PASS",
            "summary": "",
        }
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {
            "decision": "PASS",
            "summary": "",
        }

        verdict, director_feedback, previous_attempt, error_category = ir.post_select_runtime.run_post_select_checks(
            verdict="PASS",
            final_manuscript="patched manuscript",
            final_state_updates={},
            next_ep=3,
            round_num=1,
            round_ctx=round_ctx,
            director_result={},
            director_feedback="",
            score=95,
            error_category="",
            previous_attempt={},
            stage4_spinner=MagicMock(),
            director_memory_context="",
        )

        assert verdict == "PASS"
        assert director_feedback == ""
        assert previous_attempt == {}
        assert error_category == ""
        ctx.agents["director"].check_manuscript_continuity_with_cache.assert_called_once()
        ctx.agents["director"].check_manuscript_history_conflicts.assert_called_once()

    def test_post_select_conflict_prefers_regenerate_over_patch(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.inplace_patch.return_value = [_candidate()]
        round_ctx.chief_writer.patch_with_feedback.return_value = [_candidate()]
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]

        candidates, is_patch, patch_fallback, prev_score, asp_manuscript = ir._generate_candidates(
            round_num=1,
            chief_writer=round_ctx.chief_writer,
            director_feedback="fix continuity only",
            previous_attempt={
                "score": 98,
                "best_manuscript": "original manuscript",
                "fix_scope": "full",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "tension",
            },
            prev_manuscript="original manuscript",
            style_guide="",
            blueprint={},
            common_writer_kwargs={},
        )

        assert candidates == round_ctx.chief_writer.regenerate_with_feedback.return_value
        assert is_patch is False
        assert patch_fallback is False
        assert prev_score == 98
        assert asp_manuscript is None
        round_ctx.chief_writer.inplace_patch.assert_not_called()
        round_ctx.chief_writer.patch_with_feedback.assert_not_called()
        round_ctx.chief_writer.regenerate_with_feedback.assert_called_once()

    def test_resolve_retry_lane_routing_avoids_patch_for_full_post_select_conflict(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.retry_runtime._resolve_retry_lane_routing(
            previous_attempt={
                "score": "98",
                "fix_scope": "full",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "tension",
            },
            prev_manuscript="original manuscript",
            round_num=1,
        )

        assert payload.prev_score == 98
        assert payload.reject_bucket == "post_select_conflict"
        assert payload.selected_strategy_key == "tension"
        assert payload.force_patch is False
        assert payload.use_inplace is False
        assert payload.use_patch is False

    def test_retry_runtime_resolve_retry_lane_routing_avoids_patch_for_full_post_select_conflict(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.retry_runtime._resolve_retry_lane_routing(
            previous_attempt={
                "score": "98",
                "fix_scope": "full",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "tension",
            },
            prev_manuscript="original manuscript",
            round_num=1,
        )

        assert payload.prev_score == 98
        assert payload.reject_bucket == "post_select_conflict"
        assert payload.selected_strategy_key == "tension"
        assert payload.force_patch is False
        assert payload.use_inplace is False
        assert payload.use_patch is False

    def test_resolve_retry_lane_routing_allows_bounded_flashback_patch_for_full_post_select_conflict(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.retry_runtime._resolve_retry_lane_routing(
            previous_attempt={
                "score": "96",
                "fix_scope": "full",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "tension",
                "conflict_contract": {
                    "contract_type": "post_select_conflict",
                    "bounded_local_fix_hint": True,
                    "contradiction_types": ["continuity"],
                },
                "fix_pack": {
                    **_local_fix_pack("flashback_line", target_kind="local_sentence"),
                    "evidence_summary": "runtime flashback continuity backfill: movement",
                },
            },
            prev_manuscript="original manuscript",
            round_num=4,
        )

        assert payload.reject_bucket == "post_select_conflict"
        assert payload.use_inplace is False
        assert payload.use_patch is True
        assert payload.force_patch is False

    def test_resolve_retry_lane_routing_allows_opening_action_continuity_patch(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.retry_runtime._resolve_retry_lane_routing(
            previous_attempt={
                "score": "96",
                "fix_scope": "full",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "tension",
                "conflict_contract": {
                    "contract_type": "post_select_conflict",
                    "bounded_local_fix_hint": True,
                    "contradiction_types": ["opening_action_continuity"],
                },
                "fix_pack": _local_fix_pack("opening_turnback_line", target_kind="local_sentence"),
            },
            prev_manuscript="original manuscript",
            round_num=4,
        )

        assert payload.reject_bucket == "post_select_conflict"
        assert payload.use_patch is True
        assert payload.use_inplace is False
        assert payload.force_patch is False

    def test_build_retry_regenerate_kwargs_reduces_strategy_budget_for_constraint_violation(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        common_writer_kwargs = {"state_tracker": ctx.state_tracker}

        regen_kwargs, strategy_budget, strategy_count = ir._build_retry_regenerate_kwargs(
            common_writer_kwargs=common_writer_kwargs,
            reject_bucket="constraint_violation",
            fix_scope="partial",
            selected_strategy_key="tension",
        )

        assert common_writer_kwargs == {"state_tracker": ctx.state_tracker}
        assert regen_kwargs["state_tracker"] is ctx.state_tracker
        assert regen_kwargs["strategy_budget"] == "reduced"
        assert regen_kwargs["preferred_strategy"] == "tension"
        assert strategy_budget == "reduced"
        assert strategy_count == 2

    def test_run_inplace_retry_lane_returns_none_on_shrunk_patch_output(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        chief_writer = MagicMock()
        prev_manuscript = "original " * 500
        chief_writer.inplace_patch.return_value = [{"manuscript": "patched " * 300}]

        candidates, is_patch = ir.retry_runtime._run_inplace_retry_lane(
            chief_writer=chief_writer,
            director_feedback="fix continuity only",
            round_num=1,
            prev_score=70,
            prev_manuscript=prev_manuscript,
            style_guide="",
            fix_pack_contract={"fix_pack": _local_fix_pack("opening_location_name")},
            reject_bucket="quality_issue",
            previous_attempt={"score": 70},
        )

        assert candidates is None
        assert is_patch is False
        chief_writer.inplace_patch.assert_called_once()

    def test_run_patch_or_rewrite_retry_lane_falls_back_to_rewrite_after_patch_failure(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        chief_writer = MagicMock()
        chief_writer.patch_with_feedback.return_value = []
        chief_writer.regenerate_with_feedback.return_value = [_candidate()]
        common_writer_kwargs = {"state_tracker": ctx.state_tracker}

        candidates, is_patch, is_patch_fallback = ir.retry_runtime._run_patch_or_rewrite_retry_lane(
            chief_writer=chief_writer,
            common_writer_kwargs=common_writer_kwargs,
            previous_attempt={"score": 70},
            prev_manuscript="original manuscript",
            round_num=1,
            prev_score=70,
            reject_bucket="post_select_conflict",
            fix_scope="partial",
            selected_strategy_key="balanced",
            use_patch=True,
        )

        assert candidates == chief_writer.regenerate_with_feedback.return_value
        assert is_patch is True
        assert is_patch_fallback is True
        chief_writer.patch_with_feedback.assert_called_once()
        chief_writer.regenerate_with_feedback.assert_called_once()

    def test_run_asp_correction_builds_context_and_returns_final_output(self):
        ctx = _make_ctx()
        asp_module = MagicMock()
        asp_result = MagicMock()
        asp_result.final_output = "asp manuscript"
        asp_result.improvement_delta = 3
        asp_module.generate_with_adversary.return_value = asp_result
        ctx.get_module.side_effect = lambda name: asp_module if name == "adversarial_self_play" else None
        ir = Stage4InterviewRound(ctx)

        asp_manuscript = ir.retry_runtime._run_asp_correction(
            round_num=2,
            previous_attempt={"score": 70},
            prev_manuscript="previous manuscript",
            blueprint={"episode": 1},
            director_feedback="tighten logic",
        )

        assert asp_manuscript == "asp manuscript"
        asp_module.generate_with_adversary.assert_called_once_with(
            initial_content="previous manuscript",
            content_type="manuscript",
            context={"blueprint": {"episode": 1}, "director_feedback": "tighten logic"},
        )

    def test_apply_asp_candidate_replacement_swaps_shortest_candidate(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        candidates = [
            {"manuscript": "A" * 400, "strategy": "a"},
            {"manuscript": "B" * 100, "strategy": "b"},
            {"manuscript": "C" * 250, "strategy": "c"},
        ]

        updated = ir.retry_runtime._apply_asp_candidate_replacement(
            candidates=candidates,
            asp_manuscript="asp manuscript",
        )

        assert updated[1] == {"manuscript": "asp manuscript", "strategy": "asp_correction"}
        assert updated[0]["strategy"] == "a"
        assert updated[2]["strategy"] == "c"

    def test_reject_retry_shrunk_inplace_patch_falls_back_to_patch(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        prev_manuscript = "original " * 500
        round_ctx.chief_writer.inplace_patch.return_value = [{"manuscript": "patched " * 300}]
        round_ctx.chief_writer.patch_with_feedback.return_value = [_candidate()]

        candidates, is_patch, patch_fallback, prev_score, asp_manuscript = ir._generate_candidates(
            round_num=1,
            chief_writer=round_ctx.chief_writer,
            director_feedback="fix continuity only",
            previous_attempt={
                "score": 70,
                "best_manuscript": prev_manuscript,
                "fix_scope": "inplace",
                "fix_pack": _local_fix_pack("opening_location_name"),
                "reject_bucket": "quality_issue",
                "selected_strategy_key": "balanced",
            },
            prev_manuscript=prev_manuscript,
            style_guide="",
            blueprint={},
            common_writer_kwargs={},
        )

        assert candidates == round_ctx.chief_writer.patch_with_feedback.return_value
        assert is_patch is True
        assert patch_fallback is False
        assert prev_score == 70
        assert asp_manuscript is None
        round_ctx.chief_writer.inplace_patch.assert_called_once()
        round_ctx.chief_writer.patch_with_feedback.assert_called_once()
        round_ctx.chief_writer.regenerate_with_feedback.assert_not_called()

    def test_no_monitor_does_not_crash(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = None
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = []

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "EMPTY"

    def test_monitor_exception_is_non_blocking(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ctx.pass_rate_monitor.record_attempt.side_effect = RuntimeError("boom")
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = []

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "EMPTY"

    def test_post_select_conflict_uses_regenerate_on_later_retry(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.patch_with_feedback.return_value = [_candidate()]
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]

        candidates, is_patch, patch_fallback, prev_score, asp_manuscript = ir._generate_candidates(
            round_num=2,
            chief_writer=round_ctx.chief_writer,
            director_feedback="fix continuity only",
            previous_attempt={
                "score": 98,
                "best_manuscript": "original manuscript",
                "fix_scope": "full",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "tension",
            },
            prev_manuscript="original manuscript",
            style_guide="",
            blueprint={},
            common_writer_kwargs={},
        )

        assert candidates == round_ctx.chief_writer.regenerate_with_feedback.return_value
        assert is_patch is False
        assert patch_fallback is False
        assert prev_score == 98
        assert asp_manuscript is None
        round_ctx.chief_writer.patch_with_feedback.assert_not_called()
        round_ctx.chief_writer.regenerate_with_feedback.assert_called_once()
        round_ctx.chief_writer.inplace_patch.assert_not_called()

    def test_post_select_conflict_uses_patch_when_bounded_flashback_fix_pack_preserved(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.patch_with_feedback.return_value = [_candidate()]
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]

        candidates, is_patch, patch_fallback, prev_score, asp_manuscript = ir._generate_candidates(
            round_num=4,
            chief_writer=round_ctx.chief_writer,
            director_feedback="fix flashback continuity only",
            previous_attempt={
                "score": 96,
                "best_manuscript": "original manuscript",
                "fix_scope": "full",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "tension",
                "conflict_contract": {
                    "contract_type": "post_select_conflict",
                    "bounded_local_fix_hint": True,
                    "contradiction_types": ["continuity"],
                },
                "fix_pack": {
                    **_local_fix_pack("flashback_line", target_kind="local_sentence"),
                    "evidence_summary": "runtime flashback continuity backfill: movement",
                },
            },
            prev_manuscript="original manuscript",
            style_guide="",
            blueprint={},
            common_writer_kwargs={},
        )

        assert candidates == round_ctx.chief_writer.patch_with_feedback.return_value
        assert is_patch is True
        assert patch_fallback is False
        assert prev_score == 96
        assert asp_manuscript is None
        round_ctx.chief_writer.patch_with_feedback.assert_called_once()
        round_ctx.chief_writer.regenerate_with_feedback.assert_not_called()
        round_ctx.chief_writer.inplace_patch.assert_not_called()

    def test_pass_with_fix_without_fix_pack_downgrades_before_inplace(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS_WITH_FIX",
            "score": 99,
            "selection_reason": "high score but local cleanup needed",
            "verdict_reason": "minor rename",
            "feedback": {"action_items": ["fix the location label"]},
            "action_items": ["fix the location label"],
            "fix_scope": "inplace",
            "selected_candidate": {"manuscript": "candidate manuscript " * 220, "strategy_name": "balanced"},
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        assert result.verdict == "REJECT"
        round_ctx.chief_writer.inplace_patch.assert_not_called()
        saved_verdict = ctx.current_project.db.save_director_selection.call_args.kwargs["verdict"]
        assert saved_verdict == "REJECT"

    def test_retry_inplace_requires_fix_pack_and_routes_to_rewrite(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]

        candidates, is_patch, patch_fallback, prev_score, asp_manuscript = ir._generate_candidates(
            round_num=1,
            chief_writer=round_ctx.chief_writer,
            director_feedback="fix continuity only",
            previous_attempt={
                "score": 95,
                "best_manuscript": "original manuscript",
                "fix_scope": "inplace",
                "reject_bucket": "quality_issue",
                "selected_strategy_key": "balanced",
            },
            prev_manuscript="original manuscript",
            style_guide="",
            blueprint={},
            common_writer_kwargs={},
        )

        assert candidates == round_ctx.chief_writer.regenerate_with_feedback.return_value
        assert is_patch is False
        assert patch_fallback is False
        assert prev_score == 95
        assert asp_manuscript is None
        round_ctx.chief_writer.inplace_patch.assert_not_called()
        round_ctx.chief_writer.patch_with_feedback.assert_not_called()
        round_ctx.chief_writer.regenerate_with_feedback.assert_called_once()
        assert ir._last_retry_budget_axes["repair"] == "rewrite_regenerate"

    def test_pass_with_fix_scene_model_target_downgrades_to_reject(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        result = ir._enforce_pass_with_fix_contract(
            {
                "verdict": "PASS_WITH_FIX",
                "director_verdict": "PASS_WITH_FIX",
                "final_verdict": "PASS_WITH_FIX",
                "fix_scope": "inplace",
                "fix_pack": _local_fix_pack("opening_location_name", target_kind="scene_model"),
            }
        )

        assert result["final_verdict"] == "REJECT"
        assert result["fix_scope"] == "partial"
        assert result["gate_basis"] == "pass_with_fix_contract_scene_model_target"

    """
    def test_firewall_continuity_reject_promotes_patch_path(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()

        result = ir._handle_reject(
            director_result={
                "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
                "selection_reason": "best candidate",
                "verdict_reason": "Contradiction Firewall: CRITICAL 1건",
                "feedback": {"issues": ["scene overlap conflict"]},
                "action_items": ["revise the opening beat"],
                "fix_scope": "inplace",
                "fix_scope_reasoning": "minor local fix",
                "open_review": "직전 화와 같은 사건이 반복됩니다.",
                "firewall_triggered": True,
                "firewall_reason": "Contradiction Firewall: CRITICAL 1건",
                "contradiction_types": ["scene_overlap"],
            },
            director_feedback="initial reject",
            candidates=[_candidate()],
            validation_results=[_validation_result()],
            round_ctx=round_ctx,
            round_num=0,
            previous_attempt={},
            is_patch=False,
            is_patch_fallback=False,
            prev_score=94,
            prev_manuscript="previous manuscript",
            asp_manuscript=None,
            tot_used=False,
            mad_used=False,
            selected="A",
            score=44,
            error_category="",
        )

        assert result.error_category == "LOGIC_ERROR"
        assert result.previous_attempt["reject_bucket"] == "post_select_conflict"
        assert result.previous_attempt["fix_scope"] == "full"
        assert result.previous_attempt["firewall_triggered"] is True
        assert "continuity replay" in result.director_feedback
        assert result.previous_attempt["selection_reason"] == ""
        assert result.previous_attempt["open_review"] == ""
        assert result.previous_attempt["fix_pack"] == {}

    def test_firewall_numeric_reject_does_not_promote_patch_path(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()

        result = ir._handle_reject(
            director_result={
                "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
                "selection_reason": "best candidate",
                "verdict_reason": "Contradiction Firewall: CRITICAL 1건",
                "feedback": {"issues": ["numeric contradiction"]},
                "action_items": ["fix the numbers"],
                "fix_scope": "inplace",
                "fix_scope_reasoning": "minor local fix",
                "open_review": "",
                "firewall_triggered": True,
                "firewall_reason": "Contradiction Firewall: CRITICAL 1건",
                "contradiction_types": ["arithmetic"],
            },
            director_feedback="initial reject",
            candidates=[_candidate()],
            validation_results=[_validation_result()],
            round_ctx=round_ctx,
            round_num=0,
            previous_attempt={},
            is_patch=False,
            is_patch_fallback=False,
            prev_score=94,
            prev_manuscript="previous manuscript",
            asp_manuscript=None,
            tot_used=False,
            mad_used=False,
            selected="A",
            score=44,
            error_category="",
        )

        assert result.previous_attempt["reject_bucket"] != "post_select_conflict"
        assert result.previous_attempt["fix_scope"] == "inplace"
        assert result.error_category == ""

    """

    def test_firewall_continuity_reject_promotes_patch_path(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()

        result = ir._handle_reject(
            director_result={
                "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
                "selection_reason": "best candidate",
                "verdict_reason": "Contradiction Firewall: CRITICAL 1",
                "feedback": {"issues": ["scene overlap conflict"]},
                "action_items": ["revise the opening beat"],
                "fix_scope": "inplace",
                "fix_scope_reasoning": "minor local fix",
                "open_review": "The previous episode event is being repeated.",
                "firewall_triggered": True,
                "firewall_reason": "Contradiction Firewall: CRITICAL 1",
                "contradiction_types": ["scene_overlap"],
            },
            director_feedback="initial reject",
            candidates=[_candidate()],
            validation_results=[_validation_result()],
            round_ctx=round_ctx,
            round_num=0,
            previous_attempt={},
            is_patch=False,
            is_patch_fallback=False,
            prev_score=94,
            prev_manuscript="previous manuscript",
            asp_manuscript=None,
            tot_used=False,
            mad_used=False,
            selected="A",
            score=44,
            error_category="",
        )

        assert result.error_category == "LOGIC_ERROR"
        assert result.previous_attempt["reject_bucket"] == "post_select_conflict"
        assert result.previous_attempt["fix_scope"] == "full"
        assert result.previous_attempt["firewall_triggered"] is True
        assert "continuity replay" in result.director_feedback
        assert result.previous_attempt["selection_reason"] == ""
        assert result.previous_attempt["open_review"] == ""
        assert result.previous_attempt["fix_pack"] == {}

    def test_firewall_numeric_reject_does_not_promote_patch_path(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()

        result = ir._handle_reject(
            director_result={
                "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
                "selection_reason": "best candidate",
                "verdict_reason": "Contradiction Firewall: CRITICAL 1",
                "feedback": {"issues": ["numeric contradiction"]},
                "action_items": ["fix the numbers"],
                "fix_scope": "inplace",
                "fix_pack": _local_fix_pack("portfolio_return_value"),
                "fix_scope_reasoning": "minor local fix",
                "open_review": "",
                "firewall_triggered": True,
                "firewall_reason": "Contradiction Firewall: CRITICAL 1",
                "contradiction_types": ["arithmetic"],
            },
            director_feedback="initial reject",
            candidates=[_candidate()],
            validation_results=[_validation_result()],
            round_ctx=round_ctx,
            round_num=0,
            previous_attempt={},
            is_patch=False,
            is_patch_fallback=False,
            prev_score=94,
            prev_manuscript="previous manuscript",
            asp_manuscript=None,
            tot_used=False,
            mad_used=False,
            selected="A",
            score=44,
            error_category="",
        )

        assert result.previous_attempt["reject_bucket"] != "post_select_conflict"
        assert result.previous_attempt["fix_scope"] == "inplace"
        # [TF-5] error_category는 reject_bucket에서 유도됨 (NULL 방지)
        assert result.error_category in ("", "QUALITY_ISSUE", "CONSTRAINT_VIOLATION", "STRUCTURE_ERROR")

    def test_retry_regenerate_uses_reduced_strategy_budget_for_constraint_violation(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]

        candidates, is_patch, patch_fallback, prev_score, asp_manuscript = ir._generate_candidates(
            round_num=2,
            chief_writer=round_ctx.chief_writer,
            director_feedback="fix constraint only",
            previous_attempt={
                "score": 10,
                "best_manuscript": "",
                "fix_scope": "",
                "reject_bucket": "constraint_violation",
                "selected_strategy_key": "tension",
            },
            prev_manuscript="original manuscript",
            style_guide="",
            blueprint={},
            common_writer_kwargs={},
        )

        assert candidates == round_ctx.chief_writer.regenerate_with_feedback.return_value
        assert is_patch is False
        assert patch_fallback is False
        assert prev_score == 10
        assert asp_manuscript is None
        call_kwargs = round_ctx.chief_writer.regenerate_with_feedback.call_args.kwargs
        assert call_kwargs["strategy_budget"] == "reduced"
        assert call_kwargs["preferred_strategy"] == "tension"
        assert ir._last_strategy_budget == "reduced"
        assert ir._last_strategy_count == 2

    def test_retry_regenerate_suppresses_exact_duplicate_hash_in_same_retry_context(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        prev_manuscript = "original manuscript"
        fresh_candidate = {"manuscript": "fresh rewrite", "strategy": "narrative"}
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [
            {"manuscript": prev_manuscript, "strategy": "balanced"},
            fresh_candidate,
        ]

        candidates, is_patch, patch_fallback, prev_score, asp_manuscript = ir._generate_candidates(
            round_num=2,
            chief_writer=round_ctx.chief_writer,
            director_feedback="fix continuity only",
            previous_attempt={
                "score": 88,
                "best_manuscript": prev_manuscript,
                "content_hash": ir.retry_runtime._compute_candidate_content_hash(prev_manuscript),
                "fix_scope": "full",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "balanced",
                "retry_budget_axes": {"repair": "rewrite_regenerate"},
            },
            prev_manuscript=prev_manuscript,
            style_guide="",
            blueprint={},
            common_writer_kwargs={"ep_num": 9},
            arc_num=1,
        )

        assert candidates == [fresh_candidate]
        assert is_patch is False
        assert patch_fallback is False
        assert prev_score == 88
        assert asp_manuscript is None
        tf_rh1_call = next(call for call in ctx.ui.log.call_args_list if call.args and "[TF-RH1]" in call.args[0])
        assert tf_rh1_call.kwargs["event_kind"] == "policy"
        assert tf_rh1_call.kwargs["attempt_key"] == "s4:ep9:arc1:a3"

    def test_retry_regenerate_keeps_full_strategy_budget_for_structure_error(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.regenerate_with_feedback.return_value = [_candidate()]

        candidates, is_patch, patch_fallback, prev_score, asp_manuscript = ir._generate_candidates(
            round_num=2,
            chief_writer=round_ctx.chief_writer,
            director_feedback="fix structure only",
            previous_attempt={
                "score": 10,
                "best_manuscript": "",
                "fix_scope": "",
                "reject_bucket": "structure_error",
                "selected_strategy_key": "tension",
            },
            prev_manuscript="original manuscript",
            style_guide="",
            blueprint={},
            common_writer_kwargs={},
        )

        assert candidates == round_ctx.chief_writer.regenerate_with_feedback.return_value
        assert is_patch is False
        assert patch_fallback is False
        assert prev_score == 10
        assert asp_manuscript is None
        call_kwargs = round_ctx.chief_writer.regenerate_with_feedback.call_args.kwargs
        assert call_kwargs.get("strategy_budget", "full") == "full"
        assert call_kwargs.get("preferred_strategy", "") == ""
        assert ir._last_strategy_budget == "full"
        assert ir._last_strategy_count == 3

    def test_record_s4_attempt_passes_round_duration_and_token_cost(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._round_metrics_start = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "model_breakdown": {},
        }
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 2,
                "total_tokens": 3000,
                "total_cost_usd": 0.321,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 3000, "cost": 0.321}},
            }
        )

        ir._record_s4_attempt(
            episode=1,
            round_num=0,
            success=True,
            score=90,
            model="gemini-2.5-pro",
        )

        kwargs = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kwargs["duration_ms"] > 0
        assert kwargs["token_cost"] == 0.321
        assert kwargs["attempt_key"] == "s4:ep1:arc0:a1"

    def test_record_s4_attempt_persists_artifact_linkage(self, tmp_path):
        ctx = _make_ctx()
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.root = tmp_path
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)

        ir._record_s4_attempt(
            episode=1,
            round_num=0,
            success=True,
            score=91,
            candidate_key="A|balanced",
            artifact_payload="final manuscript text",
            artifact_kind="final_manuscript",
        )

        prm_kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        db_kw = ctx.current_project.db.save_stage_attempt.call_args.kwargs
        assert prm_kw["candidate_key"] == "A|balanced"
        assert prm_kw["content_hash"]
        assert prm_kw["artifact_path"].endswith("final_manuscript__A_balanced.txt")
        assert (tmp_path / prm_kw["artifact_path"]).exists()
        assert db_kw["artifact_path"] == prm_kw["artifact_path"]

    """
    def test_record_s4_attempt_persists_rationale_fields(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)

        ir._record_s4_attempt(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            verdict="REJECT",
            reject_reason="retry needed",
            selection_reason="best candidate",
            verdict_reason="Contradiction Firewall: CRITICAL 1건",
            open_review="직전 화와 같은 사건 반복",
            fix_scope_reasoning="frontier conflict",
            runtime_advisory="[Advisory 핵심 요약 - 재시도 시 반영]\n- keep continuity",
            retry_directives="keep the ending distinct",
        )

        db_kw = ctx.current_project.db.save_stage_attempt.call_args.kwargs
        assert db_kw["selection_reason"] == "best candidate"
        assert db_kw["verdict_reason"] == "Contradiction Firewall: CRITICAL 1건"
        assert db_kw["open_review"] == "직전 화와 같은 사건 반복"
        assert db_kw["fix_scope_reasoning"] == "frontier conflict"
        assert "Advisory 핵심 요약" in db_kw["runtime_advisory"]
        assert db_kw["retry_directives"] == "keep the ending distinct"

    """

    def test_record_s4_attempt_persists_rationale_fields(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)

        ir._record_s4_attempt(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            verdict="REJECT",
            reject_reason="retry needed",
            selection_reason="best candidate",
            verdict_reason="Contradiction Firewall: CRITICAL 1",
            open_review="The previous episode event is being repeated.",
            fix_scope_reasoning="frontier conflict",
            runtime_advisory="[Advisory digest - apply on retry]\n- keep continuity",
            retry_directives="keep the ending distinct",
        )

        db_kw = ctx.current_project.db.save_stage_attempt.call_args.kwargs
        assert db_kw["selection_reason"] == "best candidate"
        assert db_kw["verdict_reason"] == "Contradiction Firewall: CRITICAL 1"
        assert db_kw["open_review"] == "The previous episode event is being repeated."
        assert db_kw["fix_scope_reasoning"] == "frontier conflict"
        assert "Advisory digest" in db_kw["runtime_advisory"]
        assert db_kw["retry_directives"] == "keep the ending distinct"

    def test_process_verdict_uses_reaudit_score_for_final_state_and_attempt(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._record_s4_attempt = MagicMock()
        ir.post_select_runtime.run_post_select_checks = MagicMock(return_value=("PASS_WITH_FIX", "", {}, ""))
        ir._execute_pass_with_fix_loop = MagicMock(
            return_value=(
                "PASS",
                "patched manuscript " * 200,
                {"patched": True},
                {
                    "score": 98,
                    "selection_reason": "re-audited best candidate",
                    "open_review": "tightened final beat",
                    "score_breakdown": {"structure": 98},
                    "consistency_checklist": {"timeline": "ok"},
                },
                "resolved",
                {"patch_strategy": "inplace_patch_structural"},
            )
        )
        round_ctx = _make_round_ctx()
        director_result = {
            "selected_candidate": {
                "manuscript": "candidate manuscript " * 200,
                "title": "제1화",
            },
            "state_updates": {},
            "selection_reason": "initial pick",
            "open_review": "",
            "score_breakdown": {"structure": 92},
            "consistency_checklist": {},
        }

        result, director_feedback, previous_attempt, trace_meta = ir._process_verdict(
            verdict="PASS_WITH_FIX",
            score=92,
            director_result=director_result,
            director_feedback="initial feedback",
            round_ctx=round_ctx,
            round_num=0,
            previous_attempt={},
            is_patch=False,
            is_patch_fallback=False,
            prev_score=0,
            stage4_spinner=MagicMock(),
            director_mandatory_context="",
            director_memory_context="",
            error_category="",
        )

        assert result is not None
        assert result.verdict == "PASS"
        assert director_feedback == "resolved"
        assert previous_attempt == {}
        assert result.final_state_updates["director_score"] == 98
        assert result.final_state_updates["_director_quality_labels"]["score"] == 98
        assert result.final_state_updates["_director_quality_labels"]["verdict"] == "PASS"
        assert result.final_state_updates["_director_quality_labels"]["selection_reason"] == "re-audited best candidate"
        assert ir._record_s4_attempt.call_args.kwargs["score"] == 98
        assert trace_meta["final_verdict"] == "PASS"
        assert trace_meta["final_score"] == 98

    def test_process_positive_verdict_returns_trace_only_when_post_select_downgrades_to_reject(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._record_s4_attempt = MagicMock()
        ir.post_select_runtime.run_post_select_checks = MagicMock(
            return_value=("REJECT", "retry required", {"score": 71, "fix_scope": "partial"}, "LOGIC_ERROR")
        )
        round_ctx = _make_round_ctx()
        director_result = {
            "selected_candidate": {
                "manuscript": "candidate manuscript",
                "title": "제1화",
            },
            "state_updates": {},
            "selection_reason": "initial pick",
        }

        payload = ir._process_positive_verdict(
            verdict="PASS",
            score=91,
            director_result=director_result,
            director_feedback="initial feedback",
            round_ctx=round_ctx,
            round_num=0,
            previous_attempt={},
            is_patch=False,
            is_patch_fallback=False,
            prev_score=0,
            stage4_spinner=MagicMock(),
            director_mandatory_context="mandatory",
            director_memory_context="memory",
            error_category="",
            quality_gate_score=90,
        )

        assert payload.pass_result is None
        assert payload.director_feedback == "retry required"
        assert payload.previous_attempt == {"score": 71, "fix_scope": "partial"}
        assert payload.trace_meta["final_verdict"] == "REJECT"
        assert payload.trace_meta["final_score"] == 91
        assert payload.trace_meta["patch_trace"] == {}
        ir._record_s4_attempt.assert_not_called()

    def test_process_verdict_normalizes_conditional_pass_to_positive_path(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._process_positive_verdict = MagicMock(
            return_value=SimpleNamespace(
                pass_result={"verdict": "PASS"},
                director_feedback="normalized feedback",
                previous_attempt={"score": 95},
                trace_meta={"final_verdict": "PASS"},
            )
        )

        result, director_feedback, previous_attempt, trace_meta = ir._process_verdict(
            director_result={"selected_candidate": {"manuscript": "candidate manuscript"}},
            director_feedback="initial",
            verdict="CONDITIONAL_PASS",
            score=95,
            round_ctx=_make_round_ctx(),
            round_num=0,
            previous_attempt={},
            is_patch=False,
            is_patch_fallback=False,
            prev_score=0,
            stage4_spinner=MagicMock(),
            director_mandatory_context="",
            director_memory_context="",
            error_category="",
        )

        ir._process_positive_verdict.assert_called_once()
        assert ir._process_positive_verdict.call_args.kwargs["verdict"] == "PASS"
        assert result == {"verdict": "PASS"}
        assert director_feedback == "normalized feedback"
        assert previous_attempt == {"score": 95}
        assert trace_meta["final_verdict"] == "PASS"

    def test_build_positive_verdict_seed_clones_selected_candidate_and_state_updates(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        director_result = {
            "selected_candidate": {
                "manuscript": "candidate manuscript",
                "title": "제3화",
                "strategy_name": "balanced",
            },
            "state_updates": {
                "director_score": 91,
            },
        }

        payload = ir._build_positive_verdict_seed(
            round_ctx=round_ctx,
            director_result=director_result,
        )

        director_result["selected_candidate"]["strategy_name"] = "mutated"
        director_result["state_updates"]["director_score"] = 0

        assert payload.next_ep == 3
        assert payload.initial_selected_candidate["strategy_name"] == "balanced"
        assert payload.final_manuscript == "candidate manuscript"
        assert payload.final_title == "제3화"
        assert payload.final_state_updates["director_score"] == 91

    def test_run_positive_verdict_transition_executes_patch_loop_and_uses_reaudit_score(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        ir.post_select_runtime.run_post_select_checks = MagicMock(
            return_value=("PASS_WITH_FIX", "needs patch", {"score": 94}, "")
        )
        ir._execute_pass_with_fix_loop = MagicMock(
            return_value=(
                "PASS",
                "patched manuscript",
                {"patched": True},
                {"score": "98", "selection_reason": "re-audited best candidate"},
                "resolved",
                {"patch_strategy": "inplace_patch_structural"},
            )
        )

        payload = ir._run_positive_verdict_transition(
            verdict="PASS",
            director_feedback="initial feedback",
            previous_attempt={},
            error_category="",
            score=91,
            round_ctx=round_ctx,
            round_num=0,
            stage4_spinner=MagicMock(),
            director_memory_context="memory",
            director_mandatory_context="mandatory",
            quality_gate_score=90,
            final_manuscript="candidate manuscript",
            final_state_updates={"seed": True},
            director_result={"selected_candidate": {"manuscript": "candidate manuscript"}},
        )

        assert payload.verdict == "PASS"
        assert payload.director_feedback == "resolved"
        assert payload.previous_attempt == {"score": 94}
        assert payload.final_manuscript == "patched manuscript"
        assert payload.final_state_updates == {"patched": True}
        assert payload.director_result["selection_reason"] == "re-audited best candidate"
        assert payload.patch_trace == {"patch_strategy": "inplace_patch_structural"}
        assert payload.final_score == 98
        ir._execute_pass_with_fix_loop.assert_called_once()
        assert ir._execute_pass_with_fix_loop.call_args.kwargs["quality_gate_score"] == 90

    def test_build_positive_verdict_success_result_uses_annotated_state_and_payload_builder(self):
        from modules.core.stage4_interview_round import (
            _PositiveVerdictSeedPayload,
            _PositiveVerdictTransitionPayload,
            _VerdictProcessingPayload,
        )

        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        ir._annotate_positive_verdict_state = MagicMock(return_value={"director_score": 98})
        expected = _VerdictProcessingPayload(
            pass_result=MagicMock(),
            director_feedback="resolved",
            previous_attempt={},
            trace_meta={"final_verdict": "PASS"},
        )
        ir._build_positive_verdict_payload = MagicMock(return_value=expected)

        payload = ir._build_positive_verdict_success_result(
            transition=_PositiveVerdictTransitionPayload(
                verdict="PASS",
                director_feedback="resolved",
                previous_attempt={},
                error_category="",
                final_manuscript="patched manuscript",
                final_state_updates={"patched": True},
                director_result={"selection_reason": "best candidate"},
                patch_trace={"patch_strategy": "inplace_patch_structural"},
                final_score=98,
            ),
            seed_payload=_PositiveVerdictSeedPayload(
                next_ep=1,
                initial_selected_candidate={"strategy_name": "balanced"},
                final_manuscript="candidate manuscript",
                final_title="제1화",
                final_state_updates={"seed": True},
            ),
            round_ctx=round_ctx,
            round_num=0,
            prev_score=91,
            is_patch=True,
            is_patch_fallback=False,
        )

        assert payload is expected
        ir._annotate_positive_verdict_state.assert_called_once()
        ir._build_positive_verdict_payload.assert_called_once()
        assert ir._build_positive_verdict_payload.call_args.kwargs["final_state_updates"] == {"director_score": 98}
        assert ir._build_positive_verdict_payload.call_args.kwargs["patch_trace"] == {
            "patch_strategy": "inplace_patch_structural"
        }

    def test_build_positive_verdict_trace_only_payload_preserves_transition_trace(self):
        from modules.core.stage4_interview_round import _PositiveVerdictTransitionPayload

        payload = Stage4InterviewRound._build_positive_verdict_trace_only_payload(
            transition=_PositiveVerdictTransitionPayload(
                verdict="REJECT",
                director_feedback="retry required",
                previous_attempt={"score": 71, "fix_scope": "partial"},
                error_category="LOGIC_ERROR",
                final_manuscript="candidate manuscript",
                final_state_updates={"patched": True},
                director_result={"score": 71},
                patch_trace={"patch_strategy": "inplace_patch_structural"},
                final_score=71,
            )
        )

        assert payload.pass_result is None
        assert payload.director_feedback == "retry required"
        assert payload.previous_attempt == {"score": 71, "fix_scope": "partial"}
        assert payload.trace_meta == {
            "final_verdict": "REJECT",
            "final_score": 71,
            "director_result": {"score": 71},
            "patch_trace": {"patch_strategy": "inplace_patch_structural"},
        }

    def test_annotate_positive_verdict_state_sets_labels_and_time_warnings(self):
        ctx = _make_ctx()
        ctx.state_tracker.check_time_consistency.return_value = ["timeline drift"]
        ir = Stage4InterviewRound(ctx)

        state_updates = ir._annotate_positive_verdict_state(
            final_state_updates={},
            director_result={
                "director_verdict": "PASS",
                "gate_basis": "patch_reaudit_pass",
                "repair_scope": "partial",
                "selection_reason": "best candidate",
                "open_review": "tightened ending",
                "score_breakdown": {"structure": 98},
                "consistency_checklist": {"timeline": "ok"},
            },
            final_score=98,
            verdict="PASS",
            final_manuscript="patched manuscript",
        )

        assert state_updates["director_score"] == 98
        assert state_updates["_director_quality_labels"]["score"] == 98
        assert state_updates["_director_quality_labels"]["selection_reason"] == "best candidate"
        assert ir.time_warnings == ["timeline drift"]
        ctx.ui.log.assert_any_call("   [V66.1] Time warning: timeline drift")

    def test_build_positive_verdict_payload_records_attempt_and_trace_meta(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._record_s4_attempt = MagicMock(return_value={"candidate_key": "stage4|A"})
        round_ctx = _make_round_ctx()

        payload = ir._build_positive_verdict_payload(
            verdict="PASS",
            director_feedback="resolved",
            previous_attempt={},
            final_manuscript="patched manuscript",
            final_title="제1화",
            final_state_updates={"director_score": 98},
            director_result={
                "selected": "A",
                "selected_candidate": {"strategy_name": "balanced", "manuscript": "patched manuscript"},
                "selection_reason": "best candidate",
                "verdict_reason": "resolved by patch",
                "open_review": "tightened ending",
                "fix_scope_reasoning": "local patch",
                "score_breakdown": {"structure": 98},
            },
            error_category="",
            next_ep=1,
            round_num=0,
            round_ctx=round_ctx,
            prev_score=91,
            is_patch=True,
            is_patch_fallback=False,
            patch_trace={"patch_strategy": "inplace_patch_structural", "structural_attempted": True},
            initial_selected_candidate={"strategy_name": "fallback"},
            final_score=98,
        )

        assert payload.pass_result is not None
        assert payload.pass_result.verdict == "PASS"
        assert payload.pass_result.final_manuscript == "patched manuscript"
        assert payload.pass_result.attempt_artifact_meta == {"candidate_key": "stage4|A"}
        assert payload.trace_meta["final_verdict"] == "PASS"
        assert payload.trace_meta["final_score"] == 98
        ir._record_s4_attempt.assert_called_once()
        record_kwargs = ir._record_s4_attempt.call_args.kwargs
        assert record_kwargs["artifact_payload"] == "patched manuscript"
        assert record_kwargs["patch_strategy"] == "inplace_patch_structural"
        assert record_kwargs["structural_attempted"] is True
        assert record_kwargs["selection_reason"] == "best candidate"

    def test_pass_with_fix_loop_logs_explicit_abort_when_feedback_missing(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._extract_fix_feedback = MagicMock(return_value="")
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 2

        verdict, final_manuscript, final_state_updates, director_result, director_feedback, patch_trace = (
            ir._execute_pass_with_fix_loop(
                verdict="PASS_WITH_FIX",
                final_manuscript="candidate manuscript " * 200,
                final_state_updates={},
                director_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
                director_feedback="initial feedback",
                round_ctx=round_ctx,
                round_num=0,
                score=92,
                quality_gate_score=80,
                director_mandatory_context="",
            )
        )

        assert verdict == "REJECT"
        assert final_manuscript.startswith("candidate manuscript")
        assert final_state_updates == {}
        assert patch_trace == {}
        assert "[TF-32-V] PASS_WITH_FIX 피드백 비어 있음" in director_feedback
        assert director_result["verdict_reason"].startswith("[TF-32-V] PASS_WITH_FIX 피드백 비어 있음")
        assert any("피드백 비어 있음" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)

    def test_prepare_pass_with_fix_iteration_gate_aborts_when_feedback_missing(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 2

        payload = ir.retry_runtime._prepare_pass_with_fix_iteration_gate(
            current_feedback="",
            current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
            director_feedback="initial feedback",
            round_ctx=round_ctx,
            round_num=0,
        )

        assert payload.should_abort is True
        assert "[TF-32-V] PASS_WITH_FIX" in payload.director_feedback
        assert payload.current_audit_result["gate_basis"] == "empty_feedback_abort"
        assert payload.current_audit_result["verdict_reason"].startswith("[TF-32-V] PASS_WITH_FIX")

    def test_retry_runtime_prepare_pass_with_fix_iteration_gate_aborts_when_feedback_missing(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 2

        payload = ir.retry_runtime._prepare_pass_with_fix_iteration_gate(
            current_feedback="",
            current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
            director_feedback="initial feedback",
            round_ctx=round_ctx,
            round_num=0,
        )

        assert payload.should_abort is True
        assert "[TF-32-V] PASS_WITH_FIX" in payload.director_feedback
        assert payload.current_audit_result["gate_basis"] == "empty_feedback_abort"
        assert payload.current_audit_result["verdict_reason"].startswith("[TF-32-V] PASS_WITH_FIX")

    def test_prepare_pass_with_fix_iteration_gate_reroutes_partial_scope_without_patch(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()

        with patch.object(
            ir,
            "_evaluate_pass_with_fix_contract",
            return_value={"eligible": True, "fix_pack": _local_fix_pack("scene_2", target_kind="local_sentence")},
        ):
            payload = ir.retry_runtime._prepare_pass_with_fix_iteration_gate(
                current_feedback="tighten ending",
                current_audit_result={
                    "verdict": "PASS_WITH_FIX",
                    "fix_scope": "partial",
                    "fix_pack": _local_fix_pack("scene_2", target_kind="local_sentence"),
                },
                director_feedback="director feedback",
                round_ctx=round_ctx,
                round_num=1,
            )

        assert payload.should_abort is True
        assert payload.fix_pack == {}
        assert payload.director_feedback == "director feedback"
        assert any("fix_scope='partial'" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)

    def test_run_pass_with_fix_patch_attempt_uses_candidate_patch_targets_and_clears_context(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.blueprint = {"scene_breakdown": {"scene_2": {"description": "ending payoff"}}}
        round_ctx.genre_name = "무협"
        round_ctx.chief_writer.inplace_patch.return_value = [
            {"manuscript": "patched manuscript " * 50, "patch_targets": ["scene_2"]}
        ]

        payload = ir.retry_runtime._run_pass_with_fix_patch_attempt(
            chief_writer=round_ctx.chief_writer,
            round_ctx=round_ctx,
            current_ms="original manuscript " * 50,
            current_feedback="tighten ending",
            fix_index=0,
            style_guide=round_ctx.style_guide,
            fix_pack=_local_fix_pack("scene_2", target_kind="local_sentence"),
            current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
            director_feedback="director feedback",
            last_patch_trace={},
        )

        assert payload.should_abort is False
        assert payload.patched_manuscript.startswith("patched manuscript")
        assert payload.patch_trace["patch_strategy"] == "inplace_patch"
        assert payload.patch_trace["patch_targets"] == ["scene_2"]
        assert round_ctx.chief_writer._inplace_patch_blueprint is None
        assert round_ctx.chief_writer._inplace_patch_genre_name == ""

    def test_run_pass_with_fix_patch_attempt_marks_exception_fail_closed(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.inplace_patch.side_effect = RuntimeError("boom")

        with patch.object(
            ir,
            "_mark_pass_with_fix_inplace_contract_fail",
            return_value=(
                {"gate_basis": "inplace_exception"},
                "director feedback\nnotice",
                {"failure_key": "inplace_exception"},
            ),
        ) as mocked_fail:
            payload = ir.retry_runtime._run_pass_with_fix_patch_attempt(
                chief_writer=round_ctx.chief_writer,
                round_ctx=round_ctx,
                current_ms="original manuscript " * 50,
                current_feedback="tighten ending",
                fix_index=0,
                style_guide=round_ctx.style_guide,
                fix_pack=_local_fix_pack("scene_2", target_kind="local_sentence"),
                current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
                director_feedback="director feedback",
                last_patch_trace={},
            )

        assert payload.should_abort is True
        assert payload.patched_candidates == []
        assert payload.current_audit_result["gate_basis"] == "inplace_exception"
        assert payload.patch_trace["failure_key"] == "inplace_exception"
        assert round_ctx.chief_writer._inplace_patch_blueprint is None
        assert round_ctx.chief_writer._inplace_patch_genre_name == ""
        assert mocked_fail.call_args.kwargs["failure_key"] == "inplace_exception"

    def test_run_pass_with_fix_patch_guards_rejects_short_patch_output(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        with patch.object(
            ir,
            "_mark_pass_with_fix_inplace_contract_fail",
            return_value=(
                {"gate_basis": "min_patched_length"},
                "director feedback\nnotice",
                {"failure_key": "min_patched_length"},
            ),
        ) as mocked_fail:
            payload = ir.retry_runtime._run_pass_with_fix_patch_guards(
                current_ms="original manuscript " * 200,
                patched_ms="patched manuscript " * 5,
                current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
                director_feedback="director feedback",
                patch_trace={"patch_strategy": "inplace_patch"},
            )

        assert payload.should_abort is True
        assert payload.current_audit_result["gate_basis"] == "min_patched_length"
        assert payload.patch_trace["failure_key"] == "min_patched_length"
        assert mocked_fail.call_args.kwargs["failure_key"] == "min_patched_length"

    def test_run_pass_with_fix_patch_guards_rejects_low_preserve_ratio(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        with patch.object(
            ir,
            "_mark_pass_with_fix_inplace_contract_fail",
            return_value=(
                {"gate_basis": "inplace_min_preserve_ratio"},
                "director feedback\nnotice",
                {"failure_key": "inplace_min_preserve_ratio"},
            ),
        ) as mocked_fail:
            payload = ir.retry_runtime._run_pass_with_fix_patch_guards(
                current_ms="original manuscript " * 400,
                patched_ms="patched manuscript " * 120,
                current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
                director_feedback="director feedback",
                patch_trace={"patch_strategy": "inplace_patch"},
            )

        assert payload.should_abort is True
        assert payload.current_audit_result["gate_basis"] == "inplace_min_preserve_ratio"
        assert payload.patch_trace["failure_key"] == "inplace_min_preserve_ratio"
        assert mocked_fail.call_args.kwargs["failure_key"] == "inplace_min_preserve_ratio"

    def test_capture_pass_with_fix_patch_delta_updates_trace_without_warning(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        with (
            patch("modules.core.constants.log_patch_diff") as mocked_diff,
            patch(
                "modules.core.constants.calc_patch_change_ratio",
                return_value=0.125,
            ),
        ):
            payload = ir.retry_runtime._capture_pass_with_fix_patch_delta(
                current_ms="original manuscript",
                patched_ms="patched manuscript",
                patch_trace={"patch_strategy": "inplace_patch"},
                max_change_ratio=0.30,
            )

        assert payload.f2_advisory == ""
        assert payload.patch_trace["patch_strategy"] == "inplace_patch"
        assert payload.patch_trace["change_ratio"] == 0.125
        assert payload.patch_trace["unchanged_ratio"] == 0.875
        mocked_diff.assert_called_once_with("S4-Manuscript", "original manuscript", "patched manuscript")

    def test_capture_pass_with_fix_patch_delta_emits_f2_warning_when_ratio_exceeds_threshold(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        with (
            patch("modules.core.constants.log_patch_diff"),
            patch(
                "modules.core.constants.calc_patch_change_ratio",
                return_value=0.42,
            ),
        ):
            payload = ir.retry_runtime._capture_pass_with_fix_patch_delta(
                current_ms="original manuscript",
                patched_ms="patched manuscript",
                patch_trace={"patch_strategy": "inplace_patch"},
                max_change_ratio=0.30,
            )

        assert "[F-2 경고]" in payload.f2_advisory
        assert payload.patch_trace["change_ratio"] == 0.42
        assert payload.patch_trace["unchanged_ratio"] == 0.58

    def test_run_pass_with_fix_reaudit_builds_request_and_appends_patch_history(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.story_context = "base story context"
        director = MagicMock()
        director.select_and_judge_ensemble.return_value = {"verdict": "PASS", "score": 97}

        with patch.object(ir, "_summarize_patch_provenance", return_value="patch summary"):
            payload = ir.retry_runtime._run_pass_with_fix_reaudit(
                director=director,
                round_ctx=round_ctx,
                round_num=0,
                score=92,
                current_feedback="tighten ending",
                current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
                patched_candidates=[{"state_updates": {"ending": "tightened"}}],
                patched_manuscript="patched manuscript " * 50,
                final_state_updates={"seed": True},
                director_mandatory_context="MANDATORY",
                applied_patch_history=[],
                last_patch_trace={"patch_strategy": "inplace_patch"},
                f2_advisory="[F-2] notice",
            )

        assert payload.should_abort is False
        assert payload.applied_patch_history == ["patch summary"]
        assert payload.re_audit["verdict"] == "PASS"
        kwargs = director.select_and_judge_ensemble.call_args.kwargs
        assert kwargs["candidates"][0]["state_updates"] == {"seed": True, "ending": "tightened"}
        assert "[F-2] notice" in kwargs["validation_results"][0]["warnings"]
        assert "[PASS_WITH_FIX 재심사 — 이미 적용된 패치]" in kwargs["story_context"]

    def test_run_pass_with_fix_reaudit_fails_closed_on_director_exception(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        director = MagicMock()
        director.select_and_judge_ensemble.side_effect = RuntimeError("boom")

        payload = ir.retry_runtime._run_pass_with_fix_reaudit(
            director=director,
            round_ctx=round_ctx,
            round_num=0,
            score=92,
            current_feedback="tighten ending",
            current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
            patched_candidates=[{"state_updates": {"ending": "tightened"}}],
            patched_manuscript="patched manuscript " * 50,
            final_state_updates={"seed": True},
            director_mandatory_context="MANDATORY",
            applied_patch_history=["patch summary"],
            last_patch_trace={"patch_strategy": "inplace_patch"},
            f2_advisory="",
        )

        assert payload.should_abort is True
        assert payload.re_audit == {}
        assert payload.applied_patch_history == ["patch summary"]

    def test_apply_pass_with_fix_reaudit_verdict_rejects_quality_floor_failure(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.retry_runtime._apply_pass_with_fix_reaudit_verdict(
            re_audit={"verdict": "PASS", "score": 85},
            patched_ms="patched manuscript",
            current_ms="original manuscript",
            current_feedback="tighten ending",
            current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
            final_state_updates={"seed": True},
            director_result={"score": 92},
            quality_gate_score=90,
            fix_index=1,
        )

        assert payload.should_break is True
        assert payload.fix_ok is False
        assert payload.current_ms == "original manuscript"
        assert payload.current_audit_result["gate_basis"] == "quality_floor_fail"
        assert payload.current_feedback == "tighten ending"
        assert any("score=85 < 90" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)

    def test_apply_pass_with_fix_reaudit_verdict_promotes_successful_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.retry_runtime._apply_pass_with_fix_reaudit_verdict(
            re_audit={"verdict": "PASS", "score": 97, "state_updates": {"ending": "tightened"}},
            patched_ms="patched manuscript",
            current_ms="original manuscript",
            current_feedback="tighten ending",
            current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
            final_state_updates={"seed": True},
            director_result={"score": 92, "selection_reason": "baseline"},
            quality_gate_score=90,
            fix_index=0,
        )

        assert payload.should_break is True
        assert payload.fix_ok is True
        assert payload.current_ms == "patched manuscript"
        assert payload.director_result["verdict"] == "PASS"
        assert payload.director_result["gate_basis"] == "patch_reaudit_pass"
        assert payload.final_state_updates == {"seed": True, "ending": "tightened"}

    def test_apply_pass_with_fix_reaudit_verdict_keeps_loop_for_pass_with_fix(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        with patch.object(ir, "_extract_fix_feedback", return_value="next feedback"):
            payload = ir.retry_runtime._apply_pass_with_fix_reaudit_verdict(
                re_audit={"verdict": "PASS_WITH_FIX", "score": 93, "state_updates": {"ending": "tightened"}},
                patched_ms="patched manuscript",
                current_ms="original manuscript",
                current_feedback="tighten ending",
                current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
                final_state_updates={"seed": True},
                director_result={"score": 92},
                quality_gate_score=90,
                fix_index=0,
            )

        assert payload.should_break is False
        assert payload.fix_ok is False
        assert payload.current_ms == "patched manuscript"
        assert payload.current_audit_result["verdict"] == "PASS_WITH_FIX"
        assert payload.final_state_updates == {"seed": True, "ending": "tightened"}
        assert payload.current_feedback == "next feedback"

    def test_apply_pass_with_fix_reaudit_verdict_rejects_failed_reaudit(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.retry_runtime._apply_pass_with_fix_reaudit_verdict(
            re_audit={"verdict": "REJECT", "score": 41},
            patched_ms="patched manuscript",
            current_ms="original manuscript",
            current_feedback="tighten ending",
            current_audit_result={"verdict": "PASS_WITH_FIX", "fix_scope": "inplace"},
            final_state_updates={"seed": True},
            director_result={"score": 92},
            quality_gate_score=90,
            fix_index=0,
        )

        assert payload.should_break is True
        assert payload.fix_ok is False
        assert payload.current_ms == "original manuscript"
        assert payload.current_audit_result["gate_basis"] == "patch_reaudit_fail"

    def test_finalize_pass_with_fix_loop_outcome_promotes_pass(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.retry_runtime._finalize_pass_with_fix_loop_outcome(
            fix_ok=True,
            current_ms="patched manuscript",
            current_audit_result={"verdict": "PASS"},
            director_result={"score": 97},
            final_manuscript="original manuscript",
            director_feedback="tighten ending",
            last_patched_ms=None,
            score=92,
        )

        assert payload.verdict == "PASS"
        assert payload.final_manuscript == "patched manuscript"
        assert payload.director_result["verdict"] == "PASS"
        assert payload.director_result["gate_basis"] == "patch_reaudit_pass"
        assert payload.director_feedback == "tighten ending"

    def test_finalize_pass_with_fix_loop_outcome_adopts_last_patch_for_reject_tail(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.retry_runtime._finalize_pass_with_fix_loop_outcome(
            fix_ok=False,
            current_ms="original manuscript",
            current_audit_result={
                "verdict": "PASS_WITH_FIX",
                "score": "95",
                "gate_basis": "patch_reaudit_fail",
                "fix_scope": "inplace",
                "selection_reason": "re-audit still incomplete",
            },
            director_result={"score": 92},
            final_manuscript="original manuscript",
            director_feedback="tighten ending",
            last_patched_ms="patched manuscript",
            score=92,
        )

        assert payload.verdict == "REJECT"
        assert payload.final_manuscript == "patched manuscript"
        assert payload.director_result["score"] == 95
        assert payload.director_result["fix_scope"] == "inplace"
        assert payload.director_result["gate_basis"] == "patch_reaudit_fail"
        assert payload.director_feedback.endswith("[TF-32-V] PASS_WITH_FIX 수정 실패 → REJECT")

    def test_append_episode_log_includes_round_cost_and_strategy_flags(self):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._last_strategy_budget = "reduced"
        ir._last_strategy_count = 2
        ir._last_retry_budget_axes = {
            "round": "retry_round_2",
            "repair": "patch_revision",
            "strategy": "reduced",
            "escalation": "mad",
            "guidance": "augmented",
        }
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 4,
                "total_tokens": 4321,
                "total_cost_usd": 0.456,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 4321, "cost": 0.456}},
            }
        )

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            ir._append_episode_log(
                ep_num=3,
                round_num=1,
                director_result={
                    "verdict": "REJECT",
                    "score": 44,
                    "selected": "A",
                    "selection_reason": "best candidate",
                    "selected_candidate": {"strategy_name": "tension"},
                    "score_breakdown": {},
                    "action_items": [],
                    "open_review": "",
                },
                is_patch=False,
                patch_fallback=False,
                tot_used=False,
                mad_used=False,
                asp_used=False,
                model="gemini-2.5-pro",
                reject_bucket="constraint_violation",
                validation_warnings=["warn-1"],
            )

        written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
        payload = json.loads(written.strip())
        assert payload["round_total_calls"] == 4
        assert payload["round_total_tokens"] == 4321
        assert payload["round_total_cost_usd"] == 0.456
        assert payload["round_model_breakdown"]["gemini-2.5-pro"]["tokens"] == 4321
        assert payload["flags"]["strategy_budget"] == "reduced"
        assert payload["flags"]["strategy_count"] == 2
        assert payload["flags"]["reject_bucket"] == "constraint_violation"
        assert payload["flags"]["retry_budget_axes"]["repair"] == "patch_revision"
        assert payload["patch_trace"]["patch_strategy"] == ""
        assert payload["patch_trace"]["patch_targets"] == []
        assert payload["patch_trace"]["unchanged_ratio"] is None

    def test_append_episode_log_normalizes_patch_strategy_for_feedback_retry(self):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 2,
                "total_tokens": 2000,
                "total_cost_usd": 0.2,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 2000, "cost": 0.2}},
            }
        )

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            ir._append_episode_log(
                ep_num=2,
                round_num=1,
                director_result={
                    "verdict": "PASS_WITH_FIX",
                    "score": 61,
                    "selected": "A",
                    "selection_reason": "best candidate",
                    "selected_candidate": {"strategy_name": "balanced"},
                    "score_breakdown": {},
                    "action_items": [],
                    "open_review": "",
                },
                is_patch=True,
                patch_fallback=False,
                tot_used=False,
                mad_used=False,
                asp_used=False,
                model="gemini-2.5-pro",
                patch_trace={},
            )

        written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
        payload = json.loads(written.strip())
        assert payload["flags"]["patch_mode"] is True
        assert payload["patch_trace"]["patch_strategy"] == "patch_with_feedback"

    def test_append_episode_log_persists_selection_and_verdict_reason(self):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 1,
                "total_tokens": 1234,
                "total_cost_usd": 0.123,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 1234, "cost": 0.123}},
            }
        )

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            ir._append_episode_log(
                ep_num=4,
                round_num=0,
                director_result={
                    "verdict": "REJECT",
                    "score": 44,
                    "selected": "A",
                    "selection_reason": "최우수 후보 선택",
                    "verdict_reason": "Contradiction Firewall: CRITICAL 1건",
                    "selected_candidate": {"strategy_name": "balanced"},
                    "score_breakdown": {},
                    "action_items": ["마지막 장면 수정"],
                    "open_review": "",
                },
                is_patch=False,
                patch_fallback=False,
                tot_used=False,
                mad_used=False,
                asp_used=False,
                model="gemini-2.5-pro",
                reject_bucket="constraint_violation",
                validation_warnings=[],
            )

            written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
            payload = json.loads(written.strip())
            assert payload["reason"] == "최우수 후보 선택"
            assert payload["selection_reason"] == "최우수 후보 선택"
            assert payload["verdict_reason"] == "Contradiction Firewall: CRITICAL 1건"

    def test_append_episode_log_defaults_verdict_reason_to_selection_reason(self):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 1,
                "total_tokens": 1000,
                "total_cost_usd": 0.1,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 1000, "cost": 0.1}},
            }
        )

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            ir._append_episode_log(
                ep_num=5,
                round_num=0,
                director_result={
                    "verdict": "PASS",
                    "score": 95,
                    "selected": "A",
                    "selection_reason": "리듬과 연속성이 안정적",
                    "selected_candidate": {"strategy_name": "balanced"},
                    "score_breakdown": {},
                    "action_items": [],
                    "open_review": "",
                },
                is_patch=False,
                patch_fallback=False,
                tot_used=False,
                mad_used=False,
                asp_used=False,
                model="gemini-2.5-pro",
                reject_bucket="",
                validation_warnings=[],
            )

        written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
        payload = json.loads(written.strip())
        assert payload["selection_reason"] == "리듬과 연속성이 안정적"
        assert payload["verdict_reason"] == "리듬과 연속성이 안정적"

        assert payload["initial_verdict"] == "PASS"
        assert payload["final_verdict"] == "PASS"
        assert payload["initial_score"] == 95
        assert payload["final_score"] == 95
        assert payload["attempt_key"] == "s4:ep5:arc0:a1"

    def test_append_episode_log_prefers_explicit_final_sink_metadata(self):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 1,
                "total_tokens": 1000,
                "total_cost_usd": 0.1,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 1000, "cost": 0.1}},
            }
        )

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            ir._append_episode_log(
                ep_num=5,
                round_num=0,
                director_result={
                    "verdict": "PASS_WITH_FIX",
                    "score": 90,
                    "selected": "A",
                    "selection_reason": "stale selection",
                    "verdict_reason": "stale verdict",
                    "selected_candidate": {"strategy_name": "balanced"},
                    "fix_scope": "inplace",
                    "fix_pack": {
                        "patch_targets": ["name_anchor"],
                        "must_fix": ["rename family anchor"],
                        "do_not_regress": ["ending hook"],
                        "success_condition": "anchor renamed",
                        "target_kind": "entity_ref",
                        "subtype": "고유명사",
                        "provenance": "director_authored",
                    },
                    "score_breakdown": {},
                    "action_items": [],
                    "open_review": "",
                },
                initial_verdict="PASS_WITH_FIX",
                final_verdict="PASS",
                initial_score=90,
                final_score=90,
                is_patch=True,
                patch_fallback=False,
                tot_used=False,
                mad_used=False,
                asp_used=False,
                model="gemini-2.5-pro",
                validation_warnings=[],
                final_warnings=[],
                patch_trace={"patch_strategy": "inplace_patch_local_ops", "patch_targets": ["name_anchor"]},
                selection_reason="final selection",
                verdict_reason="final verdict",
                gate_semantics={
                    "director_verdict": "PASS",
                    "final_verdict": "PASS",
                    "gate_basis": "patch_reaudit_pass",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "repair_contract": {
                        "subtype": "고유명사",
                        "fix_scope": "inplace",
                        "repair_scope": "inplace",
                        "authoritative_fix_scope": "inplace",
                        "provenance": "director_authored",
                        "target_kind": "entity_ref",
                    },
                    "scope_authority": {
                        "fix_scope": "inplace",
                        "repair_scope": "inplace",
                        "authoritative_fix_scope": "inplace",
                        "widened": False,
                    },
                },
                fix_pack={
                    "patch_targets": ["name_anchor"],
                    "must_fix": ["rename family anchor"],
                    "do_not_regress": ["ending hook"],
                    "success_condition": "anchor renamed",
                    "target_kind": "entity_ref",
                    "subtype": "고유명사",
                    "provenance": "director_authored",
                },
                runtime_advisory="runtime digest",
                retry_directives="retry digest",
            )

        written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
        payload = json.loads(written.strip())
        assert payload["selection_reason"] == "final selection"
        assert payload["verdict_reason"] == "final verdict"
        assert payload["director_verdict"] == "PASS"
        assert payload["gate_basis"] == "patch_reaudit_pass"
        assert payload["fix_pack"]["target_kind"] == "entity_ref"
        assert payload["repair_contract"]["provenance"] == "director_authored"
        assert payload["feedback_provenance"]["runtime_advisory"] == "runtime digest"
        assert payload["feedback_provenance"]["retry_directives"] == "retry digest"

    def test_append_episode_log_includes_top_level_token_aliases(self):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 2,
                "total_tokens": 222,
                "total_cost_usd": 0.22,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 222, "cost": 0.22}},
            }
        )

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            ir._append_episode_log(
                ep_num=8,
                round_num=0,
                director_result={
                    "verdict": "PASS",
                    "score": 91,
                    "selected": "B",
                    "selection_reason": "clear win",
                    "selected_candidate": {"strategy_name": "balanced"},
                    "score_breakdown": {},
                    "action_items": [],
                    "open_review": "",
                },
                is_patch=False,
                patch_fallback=False,
                tot_used=False,
                mad_used=False,
                asp_used=False,
                model="gemini-2.5-pro",
                reject_bucket="",
                validation_warnings=[],
            )

        payload = json.loads("".join(call.args[0] for call in mocked_open().write.call_args_list).strip())
        assert payload["token_cost"] == 0.22
        assert payload["token_usage"]["total_calls"] == 2
        assert payload["token_usage"]["total_tokens"] == 222
        assert payload["token_usage"]["model_breakdown"]["gemini-2.5-pro"]["tokens"] == 222

    def test_log_round_outcome_emits_attempt_key_and_artifact(self, caplog):
        ctx = _make_ctx()
        ctx.current_project.metrics_session_id = "sess_round"
        ir = Stage4InterviewRound(ctx)

        with caplog.at_level(logging.INFO):
            ir._log_round_outcome(
                next_ep=9,
                round_num=1,
                arc_num=3,
                initial_verdict="PASS_WITH_FIX",
                final_verdict="PASS",
                initial_score=82,
                final_score=91,
                patch_mode=True,
                patch_fallback=False,
                warning_count=3,
                final_warning_count=1,
                reject_bucket="",
                candidate_key="B|balanced",
                artifact_path="logs/artifacts/stage4/final.txt",
            )

        assert "[s4:ep9:arc3:a2:sess_round] round_complete" in caplog.text
        assert "initial=PASS_WITH_FIX/82" in caplog.text
        assert "final=PASS/91" in caplog.text
        assert "candidate_key=B|balanced" in caplog.text
        assert "artifact=logs/artifacts/stage4/final.txt" in caplog.text

    def test_append_episode_log_separates_candidate_and_final_warnings_for_pass_rows(self):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 1,
                "total_tokens": 1000,
                "total_cost_usd": 0.1,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 1000, "cost": 0.1}},
            }
        )

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            ir._append_episode_log(
                ep_num=6,
                round_num=0,
                director_result={
                    "verdict": "PASS",
                    "score": 96,
                    "selected": "A",
                    "selection_reason": "accepted",
                    "selected_candidate": {"strategy_name": "balanced"},
                    "score_breakdown": {},
                    "action_items": [],
                    "open_review": "",
                },
                is_patch=False,
                patch_fallback=False,
                tot_used=False,
                mad_used=False,
                asp_used=False,
                model="gemini-2.5-pro",
                reject_bucket="",
                validation_warnings=["candidate-only warning"],
                final_warnings=["final-only warning"],
            )

        payload = json.loads("".join(call.args[0] for call in mocked_open().write.call_args_list).strip())
        assert payload["warnings"] == ["final-only warning"]
        assert payload["final_warnings"] == ["final-only warning"]
        assert payload["candidate_warnings"] == ["candidate-only warning"]

    def test_append_episode_log_uses_project_root_logs_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctx = _make_ctx()
        ctx.current_project.name = "fallback_project"
        ctx.current_project.paths.root = tmp_path / "actual_project"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 1,
                "total_tokens": 100,
                "total_cost_usd": 0.01,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 100, "cost": 0.01}},
            }
        )

        ir._append_episode_log(
            ep_num=2,
            round_num=0,
            director_result={
                "verdict": "PASS",
                "score": 91,
                "selected": "A",
                "selection_reason": "accepted",
                "selected_candidate": {"strategy_name": "balanced"},
                "score_breakdown": {},
                "action_items": [],
                "open_review": "",
            },
            is_patch=False,
            patch_fallback=False,
            tot_used=False,
            mad_used=False,
            asp_used=False,
            model="gemini-2.5-pro",
            reject_bucket="",
            validation_warnings=[],
        )

        expected_path = ctx.current_project.paths.root / "logs" / "episode_production.jsonl"
        fallback_path = tmp_path / "projects" / "fallback_project" / "logs" / "episode_production.jsonl"
        assert expected_path.exists()
        assert not fallback_path.exists()

    def test_pass_with_fix_run_logs_initial_and_final_verdicts(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.model_tier = "gemini-2.5-pro"
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]

        def _inplace_side_effect(**kwargs):
            round_ctx.chief_writer._last_inplace_patch_trace = {
                "patch_strategy": "inplace_patch_structural",
                "patch_targets": ["scene_2"],
                "fallback_reason": "",
                "focus": "ending",
                "structural_attempted": True,
            }
            return [{"manuscript": "patched manuscript " * 200, "patch_targets": ["scene_2"]}]

        round_ctx.chief_writer.inplace_patch.side_effect = _inplace_side_effect
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            {
                "selected": "A",
                "verdict": "PASS_WITH_FIX",
                "score": 92,
                "selection_reason": "initial selection",
                "verdict_reason": "ending needs a local fix",
                "feedback": {"action_items": ["tighten the ending"]},
                "action_items": ["tighten the ending"],
                "fix_scope": "inplace",
                "fix_pack": _local_fix_pack("scene_2", target_kind="local_sentence"),
                "selected_candidate": {"manuscript": "candidate manuscript " * 200, "strategy_name": "balanced"},
                "score_breakdown": {},
                "open_review": "",
            },
            {
                "verdict": "PASS",
                "score": 98,
                "selection_reason": "re-audit accepted",
                "open_review": "ending tension restored",
                "score_breakdown": {"structure": 98},
                "consistency_checklist": {"timeline": "ok"},
            },
        ]

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            result = ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert result.verdict == "PASS"
        written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
        payload = json.loads(written.strip())
        assert payload["verdict"] == "PASS_WITH_FIX"
        assert payload["score"] == 92
        assert payload["initial_verdict"] == "PASS_WITH_FIX"
        assert payload["final_verdict"] == "PASS"
        assert payload["initial_score"] == 92
        assert payload["final_score"] == 98
        assert payload["attempt_key"] == "s4:ep1:arc1:a1"
        assert payload["flags"]["patch_mode"] is True
        assert payload["patch_trace"]["patch_strategy"] == "inplace_patch_structural"
        assert payload["patch_trace"]["patch_targets"] == ["scene_2"]
        assert payload["patch_trace"]["fallback_reason"] == ""
        assert payload["patch_trace"]["focus"] == "ending"
        assert payload["patch_trace"]["structural_attempted"] is True
        assert 0.0 <= payload["patch_trace"]["unchanged_ratio"] <= 1.0
        prm_kwargs = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert prm_kwargs["is_patch"] is True

    def test_append_episode_log_persists_strong_advisory_escalation(self, tmp_path):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "model_breakdown": {},
            }
        )
        ir._build_fix_pack_payload = MagicMock(return_value={})
        strong_advisory = {
            "source_verdict": "PASS",
            "escalated_to": "PASS_WITH_FIX",
            "triggered_by": ["truth_gate"],
        }

        with (
            patch("modules.core.stage4_interview_round.resolve_project_log_dir", return_value=tmp_path / "logs"),
            patch("modules.core.stage4_interview_round.append_jsonl_record") as append_mock,
        ):
            ir._append_episode_log(
                ep_num=1,
                round_num=0,
                director_result={
                    "selected": "A",
                    "selected_candidate": {"strategy_name": "balanced"},
                    "director_verdict": "PASS",
                    "final_verdict": "PASS_WITH_FIX",
                    "verdict": "PASS_WITH_FIX",
                    "score": 91,
                    "selection_reason": "binding escalation",
                    "verdict_reason": "strong advisory",
                    "fix_scope": "partial",
                    "authoritative_fix_scope": "partial",
                    "strong_advisory_escalation": strong_advisory,
                    "action_items": ["repair opening"],
                    "score_breakdown": {},
                    "open_review": "review",
                },
                is_patch=False,
                patch_fallback=False,
                tot_used=False,
                mad_used=False,
                asp_used=False,
                model="gemini-2.5-pro",
                validation_warnings=[],
            )

        assert append_mock.called
        log_path, payload = append_mock.call_args.args
        assert log_path == (tmp_path / "logs" / "episode_production.jsonl")
        assert payload["strong_advisory_escalation"] == strong_advisory

    def test_pass_with_fix_multi_anchor_fix_pack_is_logged_and_passes(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.model_tier = "gemini-2.5-pro"
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]

        def _inplace_side_effect(**kwargs):
            assert kwargs["fix_pack"]["patch_targets"] == ["opening_location_name", "ending_location_name"]
            round_ctx.chief_writer._last_inplace_patch_trace = {
                "patch_strategy": "inplace_patch",
                "patch_targets": ["opening_location_name", "ending_location_name"],
                "fallback_reason": "",
                "focus": "",
                "structural_attempted": False,
            }
            return [
                {
                    "manuscript": "patched manuscript " * 200,
                    "patch_targets": ["opening_location_name", "ending_location_name"],
                }
            ]

        round_ctx.chief_writer.inplace_patch.side_effect = _inplace_side_effect
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            {
                "selected": "A",
                "verdict": "PASS_WITH_FIX",
                "score": 94,
                "selection_reason": "local rename only",
                "verdict_reason": "two location anchors need correction",
                "feedback": {"action_items": ["fix the location labels"]},
                "action_items": ["fix the location labels"],
                "fix_scope": "inplace",
                "fix_pack": {
                    "patch_targets": ["opening_location_name", "ending_location_name"],
                    "must_fix": ["replace both location labels with the approved venue"],
                    "do_not_regress": ["scene mood", "timeline", "blocking"],
                    "success_condition": "Both anchors are corrected and the rest of the scene stays intact.",
                    "target_kind": "entity_ref",
                },
                "selected_candidate": {"manuscript": "candidate manuscript " * 200, "strategy_name": "balanced"},
                "score_breakdown": {},
                "open_review": "",
            },
            {
                "verdict": "PASS",
                "score": 97,
                "selection_reason": "re-audit accepted",
                "open_review": "anchors corrected",
                "score_breakdown": {"structure": 97},
                "consistency_checklist": {"timeline": "ok"},
            },
        ]

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            result = ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert result.verdict == "PASS"
        payload = json.loads("".join(call.args[0] for call in mocked_open().write.call_args_list).strip())
        assert payload["patch_trace"]["patch_targets"] == ["opening_location_name", "ending_location_name"]
        assert payload["fix_pack"]["target_kind"] == "entity_ref"
        assert payload["fix_pack"]["patch_targets"] == ["opening_location_name", "ending_location_name"]

    def test_pass_with_fix_run_logs_artifact_linkage(self, tmp_path):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.root = tmp_path
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.model_tier = "gemini-2.5-pro"
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]

        def _inplace_side_effect(**kwargs):
            round_ctx.chief_writer._last_inplace_patch_trace = {
                "patch_strategy": "inplace_patch_structural",
                "patch_targets": ["scene_2"],
                "fallback_reason": "",
                "focus": "ending",
                "structural_attempted": True,
            }
            return [{"manuscript": "patched manuscript " * 200, "patch_targets": ["scene_2"]}]

        round_ctx.chief_writer.inplace_patch.side_effect = _inplace_side_effect
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            {
                "selected": "A",
                "verdict": "PASS_WITH_FIX",
                "score": 92,
                "selection_reason": "initial selection",
                "verdict_reason": "ending needs a local fix",
                "feedback": {"action_items": ["tighten the ending"]},
                "action_items": ["tighten the ending"],
                "fix_scope": "inplace",
                "fix_pack": _local_fix_pack("scene_2", target_kind="local_sentence"),
                "selected_candidate": {"manuscript": "candidate manuscript " * 200, "strategy_name": "balanced"},
                "score_breakdown": {},
                "open_review": "",
            },
            {
                "verdict": "PASS",
                "score": 98,
                "selection_reason": "re-audit accepted",
                "open_review": "ending tension restored",
                "score_breakdown": {"structure": 98},
                "consistency_checklist": {"timeline": "ok"},
            },
        ]

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            result = ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert result.verdict == "PASS"
        written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
        payload = json.loads(written.strip())
        assert payload["candidate_key"] == "A|balanced"
        assert payload["content_hash"]
        assert payload["artifact_path"].endswith("patched_after_fix__A_balanced.txt")
        assert payload["selection_candidate_key"] == "A|balanced"
        assert (tmp_path / payload["artifact_path"]).exists()

    def test_pass_with_fix_episode_log_uses_final_attempt_meta_and_preserves_selection_meta(self, tmp_path):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.root = tmp_path
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.model_tier = "gemini-2.5-pro"
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]

        def _inplace_side_effect(**kwargs):
            round_ctx.chief_writer._last_inplace_patch_trace = {
                "patch_strategy": "inplace_patch_structural",
                "patch_targets": ["scene_2"],
                "fallback_reason": "",
                "focus": "ending",
                "structural_attempted": True,
            }
            return [{"manuscript": "patched manuscript " * 200, "patch_targets": ["scene_2"]}]

        round_ctx.chief_writer.inplace_patch.side_effect = _inplace_side_effect
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.side_effect = [
            {
                "selected": "A",
                "verdict": "PASS_WITH_FIX",
                "score": 92,
                "selection_reason": "initial selection",
                "verdict_reason": "ending needs a local fix",
                "feedback": {"action_items": ["tighten the ending"]},
                "action_items": ["tighten the ending"],
                "fix_scope": "inplace",
                "fix_pack": _local_fix_pack("scene_2", target_kind="local_sentence"),
                "selected_candidate": {
                    "manuscript": "candidate manuscript " * 200,
                    "strategy": "balanced",
                    "strategy_name": "균형 전략",
                },
                "score_breakdown": {},
                "open_review": "",
            },
            {
                "selected": "A",
                "selected_candidate": {
                    "manuscript": "patched manuscript " * 200,
                    "strategy": "inplace_patch",
                    "strategy_name": "InPlace 수정",
                },
                "verdict": "PASS",
                "score": 98,
                "selection_reason": "re-audit accepted",
                "open_review": "ending tension restored",
                "score_breakdown": {"structure": 98},
                "consistency_checklist": {"timeline": "ok"},
            },
        ]

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            result = ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert result.verdict == "PASS"
        prm_kwargs = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        db_kwargs = ctx.current_project.db.save_director_selection.call_args.kwargs
        payload = json.loads("".join(call.args[0] for call in mocked_open().write.call_args_list).strip())
        assert prm_kwargs["candidate_key"] == "A|InPlace 수정"
        assert payload["candidate_key"] == prm_kwargs["candidate_key"]
        assert payload["artifact_path"] == prm_kwargs["artifact_path"]
        assert payload["selection_candidate_key"] == db_kwargs["candidate_key"]
        assert payload["selection_candidate_key"] == "A|균형 전략"
        assert payload["selection_artifact_path"] == db_kwargs["artifact_path"]
        ctx.current_project.db.update_director_selection_rationale.assert_called_once_with(
            attempt_key="s4:ep1:arc1:a1",
            selection_reason="re-audit accepted",
            verdict_reason="ending needs a local fix",
            fix_scope="inplace",
        )

    def test_reject_episode_log_uses_final_attempt_meta_and_preserves_selection_meta(self, tmp_path):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.root = tmp_path
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.model_tier = "gemini-2.5-pro"
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "B",
            "verdict": "REJECT",
            "score": 44,
            "selection_reason": "best candidate",
            "verdict_reason": "conflict",
            "selected_candidate": {
                "manuscript": "candidate manuscript",
                "strategy": "balanced",
                "strategy_name": "균형 전략",
            },
            "feedback": {"issues": ["conflict"]},
            "action_items": ["fix ending"],
        }

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            result = ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert result.verdict == "REJECT"
        prm_kwargs = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        db_kwargs = ctx.current_project.db.save_director_selection.call_args.kwargs
        payload = json.loads("".join(call.args[0] for call in mocked_open().write.call_args_list).strip())
        assert prm_kwargs["candidate_key"] == "B|balanced"
        assert payload["candidate_key"] == prm_kwargs["candidate_key"]
        assert payload["artifact_path"] == prm_kwargs["artifact_path"]
        assert payload["selection_candidate_key"] == db_kwargs["candidate_key"]
        assert payload["selection_candidate_key"] == "B|균형 전략"
        assert payload["selection_artifact_path"] == db_kwargs["artifact_path"]
        ctx.current_project.db.update_director_selection_rationale.assert_called_once_with(
            attempt_key="s4:ep1:arc1:a1",
            selection_reason="best candidate",
            verdict_reason="conflict",
            fix_scope="",
        )

    def test_pass_with_fix_loop_sets_and_clears_structural_patch_context(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.blueprint = {
            "ep_num": 1,
            "scene_breakdown": {
                "scene_1": {"description": "opening buildup"},
                "scene_2": {"description": "ending payoff"},
            },
        }
        round_ctx.genre_name = "무협"

        def _inplace_side_effect(**kwargs):
            assert round_ctx.chief_writer._inplace_patch_blueprint == round_ctx.blueprint
            assert round_ctx.chief_writer._inplace_patch_genre_name == "무협"
            round_ctx.chief_writer._last_inplace_patch_trace = {
                "patch_strategy": "inplace_patch_structural",
                "patch_targets": ["scene_2"],
                "fallback_reason": "",
                "focus": "ending",
                "structural_attempted": True,
            }
            return [{"manuscript": "patched manuscript " * 200, "state_updates": {"ending": "tightened"}}]

        round_ctx.chief_writer.inplace_patch.side_effect = _inplace_side_effect
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "verdict": "PASS",
            "score": 97,
            "selection_reason": "re-audit accepted",
            "open_review": "ending tension restored",
            "score_breakdown": {"structure": 97},
            "consistency_checklist": {"timeline": "ok"},
            "state_updates": {"ending": "tightened"},
        }

        verdict, final_manuscript, final_state_updates, final_director_result, final_feedback, patch_trace = (
            ir._execute_pass_with_fix_loop(
                verdict="PASS_WITH_FIX",
                final_manuscript="original manuscript " * 220,
                final_state_updates={},
                director_result={
                    "fix_scope": "inplace",
                    "fix_pack": _local_fix_pack("scene_2", target_kind="local_sentence"),
                    "action_items": ["엔딩 장면 보강"],
                    "feedback": {"action_items": ["엔딩 장면 보강"]},
                    "selected_candidate": {"manuscript": "candidate manuscript " * 220},
                    "score": 92,
                },
                director_feedback="엔딩 장면 보강",
                round_ctx=round_ctx,
                round_num=0,
                score=92,
                quality_gate_score=90,
                director_mandatory_context="",
            )
        )

        assert verdict == "PASS"
        assert final_manuscript == "patched manuscript " * 200
        assert final_state_updates["ending"] == "tightened"
        assert final_director_result["score"] == 97
        assert final_feedback == "엔딩 장면 보강"
        assert patch_trace["patch_strategy"] == "inplace_patch_structural"
        assert patch_trace["patch_targets"] == ["scene_2"]
        assert 0.0 <= patch_trace["unchanged_ratio"] <= 1.0
        assert round_ctx.chief_writer._inplace_patch_blueprint is None
        assert round_ctx.chief_writer._inplace_patch_genre_name == ""

    def test_reject_run_keeps_db_and_episode_log_reasoning_consistent(self):
        ctx = _make_ctx()
        ctx.current_project.metrics_session_id = "sess_stage4_reject"
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.model_tier = "gemini-2.5-pro"
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 44,
            "selection_reason": "최우수 후보 선택",
            "verdict_reason": "Contradiction Firewall: CRITICAL 1건",
            "pre_firewall_score": 100,
            "firewall_triggered": True,
            "firewall_reason": "Contradiction Firewall: CRITICAL 1건",
            "feedback": {"issues": ["중대 모순"]},
            "action_items": ["마지막 장면 수정"],
            "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
            "score_breakdown": {},
            "open_review": "",
        }

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            result = ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert result.verdict == "REJECT"
        db_kwargs = ctx.current_project.db.save_director_selection.call_args.kwargs
        assert db_kwargs["selection_reason"] == "최우수 후보 선택"
        assert db_kwargs["verdict_reason"] == "Contradiction Firewall: CRITICAL 1건"
        prm_kwargs = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert prm_kwargs["success"] is False
        assert prm_kwargs["reject_reason"] == "마지막 장면 수정"
        assert prm_kwargs["attempt_key"] == "s4:ep1:arc1:a1:sess_stage4_reject"
        cost_kwargs = ctx.current_project.db.save_cost_record.call_args.kwargs
        assert cost_kwargs["session_id"] == "sess_stage4_reject"

        written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
        payload = json.loads(written.strip())
        assert payload["selection_reason"] == "최우수 후보 선택"
        assert payload["verdict_reason"] == "Contradiction Firewall: CRITICAL 1건"
        assert payload["initial_verdict"] == "REJECT"
        assert payload["final_verdict"] == "REJECT"
        assert payload["flags"]["reject_bucket"] == "quality_issue"

    def test_reject_decision_jsonl_persists_firewall_metadata(self, tmp_path):
        ctx = _make_ctx()
        ctx.current_project.metrics_session_id = "sess_stage4_firewall_jsonl"
        ctx.current_project.paths = MagicMock()
        ctx.current_project.paths.root = tmp_path
        ctx.session_logger = SessionLogger(tmp_path / "logs" / "session", enabled=True)
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 44,
            "selection_reason": "best candidate before firewall",
            "verdict_reason": "Contradiction Firewall: CRITICAL 1",
            "pre_firewall_score": 100,
            "firewall_triggered": True,
            "firewall_reason": "Contradiction Firewall: CRITICAL 1",
            "feedback": {"issues": ["major contradiction"]},
            "action_items": ["repair the final scene"],
            "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
            "score_breakdown": {},
            "open_review": "",
        }

        result = ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        decisions_path = tmp_path / "logs" / "session" / "decisions.jsonl"
        rows = [json.loads(line) for line in decisions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        row = rows[-1]
        meta = row["meta"]

        assert result.verdict == "REJECT"
        assert row["stage"] == "stage4"
        assert row["result"] == "REJECT"
        assert meta["firewall_triggered"] is True
        assert meta["firewall_reason"] == "Contradiction Firewall: CRITICAL 1"

    def test_episode_log_write_failure_is_non_blocking_and_other_records_persist(self):
        ctx = _make_ctx()
        ctx.pass_rate_monitor = MagicMock()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.model_tier = "gemini-2.5-pro"
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": 44,
            "selection_reason": "최우수 후보 선택",
            "verdict_reason": "Contradiction Firewall: CRITICAL 1건",
            "pre_firewall_score": 100,
            "firewall_triggered": True,
            "firewall_reason": "Contradiction Firewall: CRITICAL 1건",
            "feedback": {"issues": ["중대 모순"]},
            "action_items": ["마지막 장면 수정"],
            "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
            "score_breakdown": {},
            "open_review": "",
        }

        with patch("modules.core.stage4_interview_round.open", side_effect=OSError("disk full")), patch("os.makedirs"):
            result = ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        assert result.verdict == "REJECT"
        db_kwargs = ctx.current_project.db.save_director_selection.call_args.kwargs
        assert db_kwargs["selection_reason"] == "최우수 후보 선택"
        assert db_kwargs["verdict_reason"] == "Contradiction Firewall: CRITICAL 1건"
        prm_kwargs = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert prm_kwargs["success"] is False
        assert prm_kwargs["reject_reason"] == "마지막 장면 수정"
        assert prm_kwargs["attempt_key"] == "s4:ep1:arc1:a1"


class TestModuleStructure:
    def test_import(self):
        assert Stage4InterviewRound is not None

    def test_orchestrator_has_interview_round_property(self):
        assert hasattr(Stage4Orchestrator, "interview_round")

    def test_orchestrator_no_legacy_interview_method(self):
        assert not hasattr(Stage4Orchestrator, "_run_interview_round")

    def test_round_attempt_key_does_not_touch_self_app(self):
        ctx = _make_ctx()
        ir = _AppTrapInterviewRound(ctx)

        attempt_key = ir._build_round_attempt_key(next_ep=1, round_num=0, arc_num=1)

        assert attempt_key == "s4:ep1:arc1:a1"

    def test_stage4_context_from_app_extracts_pass_rate_monitor(self):
        app = MagicMock(spec=[])
        app.ui = MagicMock()
        app.current_project = MagicMock()
        app.agents = {}
        app.sys = MagicMock()
        app.pass_rate_monitor = MagicMock()

        ctx = Stage4Context.from_app(app)

        assert ctx.pass_rate_monitor is app.pass_rate_monitor


class TestSlotMaxChars:
    """P1-2: 슬롯별 max_chars가 하드코딩 1500 대신 반영되는지 검증."""

    def test_slot_max_chars_respected(self):
        ctx = _make_ctx()
        ctx.context_advisor = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "A" * 3000
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=3,
            slots=[
                RetrievalSlot(
                    category="event_claim",
                    query="event query",
                    source=RetrievalSources.VEC_MEMORY,
                    priority=1,
                    max_chars=500,
                ),
            ],
            total_budget_chars=50000,
        )

        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.blueprint = {"characters": [{"name": "alice"}], "integrated_scenario": "x"}
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "pass manuscript", "title": "pass"},
            "state_updates": {},
        }

        def _threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.director_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            if key == "smart_retrieval.director_total_budget":
                return 50000
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect):
            ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        continuity_ctx = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs[
            "memory_context"
        ]
        # slot.max_chars=500, so the content within [SC:event_claim] should be <= 500 chars
        sc_block = continuity_ctx.split("[SC:event_claim]\n")[-1] if "[SC:event_claim]" in continuity_ctx else ""
        assert len(sc_block) <= 500

    def test_slot_max_chars_preserve_recent_tail_context(self):
        ctx = _make_ctx()
        ctx.context_advisor = MagicMock()
        ctx.memory = MagicMock()
        ctx.memory.retrieve_multi_query_context.return_value = "HEAD-VEC " + ("A" * 260) + " TAIL-VEC"
        ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
            stage="director",
            episode_num=3,
            slots=[
                RetrievalSlot(
                    category="event_claim",
                    query="event query",
                    source=RetrievalSources.VEC_MEMORY,
                    priority=1,
                    max_chars=120,
                ),
            ],
            total_budget_chars=50000,
        )

        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "history-present"
        round_ctx.blueprint = {"characters": [{"name": "alice"}], "integrated_scenario": "x"}
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].check_manuscript_history_conflicts.return_value = {"decision": "PASS", "summary": ""}
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "pass manuscript", "title": "pass"},
            "state_updates": {},
        }

        def _threshold_side_effect(key, default=None):
            if key == "smart_retrieval.enabled":
                return True
            if key == "smart_retrieval.director_enabled":
                return True
            if key == "context.vector_max_results_s4":
                return 16
            if key == "smart_retrieval.director_total_budget":
                return 50000
            return default

        with patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect):
            ir.run(
                round_num=0,
                stage4_spinner=MagicMock(),
                director_feedback="",
                previous_attempt={},
                round_ctx=round_ctx,
            )

        continuity_ctx = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs[
            "memory_context"
        ]
        sc_block = continuity_ctx.split("[SC:event_claim]\n")[-1] if "[SC:event_claim]" in continuity_ctx else ""
        assert len(sc_block) <= 120
        assert "TAIL-VEC" in sc_block


class TestLane2DirectorSemantics:
    def test_director_input_packs_are_split_and_ordered(self):
        ctx = _make_ctx()
        ctx.current_project.master_bible = {
            "MasterBible": {"protagonist_config": {"pov": "limited", "external_pov_insert_policy": "guarded"}}
        }
        ctx.current_project.db.get_strategy_win_rates.return_value = {"total": 4, "balanced": 0.5}
        ctx.current_project.db.get_fix_scope_stats.return_value = [
            {"fix_scope": "inplace", "verdict": "PASS", "cnt": 2}
        ]
        ctx.sys = MagicMock()
        ctx.sys.guard = MagicMock()
        ctx.sys.guard.get_director_review_advisory.return_value = "operator note"
        ir = Stage4InterviewRound(ctx)
        ir._run_advisory_chain = MagicMock(return_value=["truth advisory"])
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        validation_result = _validation_result()
        validation_result["warnings"] = ["python warning"]
        validation_result["warning_count"] = 1
        validation_result["shared_failure_warnings"] = ["shared failure"]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [validation_result]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "PASS",
            "score": 95,
            "selection_reason": "ok",
            "selected_candidate": {"manuscript": "pass manuscript", "title": "pass", "strategy_name": "balanced"},
            "state_updates": {},
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="history conflict",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        director_kwargs = ctx.agents["director"].select_and_judge_ensemble.call_args.kwargs
        assert "### [Decision Core]" in director_kwargs["decision_core"]
        assert "### [Candidate Evidence]" in director_kwargs["candidate_evidence"]
        assert "### [Reference Appendix]" in director_kwargs["reference_appendix"]
        assert "shared failure" in director_kwargs["decision_core"]
        assert "python warning" in director_kwargs["candidate_evidence"]
        assert "history conflict" in director_kwargs["candidate_evidence"]
        assert "operator note" in director_kwargs["reference_appendix"]
        mandatory_context = director_kwargs["mandatory_context"]
        assert mandatory_context.index("### [Decision Core]") < mandatory_context.index("### [Candidate Evidence]")
        assert mandatory_context.index("### [Candidate Evidence]") < mandatory_context.index("### [Reference Appendix]")

    def test_save_director_selection_persists_gate_semantics_payload(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
        round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "director_verdict": "PASS_WITH_FIX",
            "final_verdict": "REJECT",
            "gate_basis": "quality_floor_fail",
            "fix_scope": "partial",
            "authoritative_fix_scope": "inplace",
            "repair_scope": "partial",
            "fix_pack": {
                "must_fix": ["tighten ending"],
                "target_kind": "local_sentence",
                "subtype": "movement",
                "provenance": "director_authored",
            },
            "score": 44,
            "selection_reason": "best candidate",
            "verdict_reason": "quality floor fail",
            "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
            "feedback": {"issues": ["quality floor"]},
            "action_items": ["tighten ending"],
        }

        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

        kw = ctx.current_project.db.save_director_selection.call_args.kwargs
        gate_semantics = kw["advisory_warnings"]["gate_semantics"]
        assert gate_semantics["director_verdict"] == "PASS_WITH_FIX"
        assert gate_semantics["final_verdict"] == "REJECT"
        assert gate_semantics["gate_basis"] == "quality_floor_fail"
        repair_contract = kw["advisory_warnings"]["repair_contract"]
        assert repair_contract["subtype"] == "movement"
        assert repair_contract["fix_scope"] == "partial"
        assert repair_contract["provenance"] == "director_authored"
        assert kw["advisory_warnings"]["scope_authority"] == {
            "fix_scope": "partial",
            "repair_scope": "partial",
            "authoritative_fix_scope": "inplace",
            "scope_origin": {
                "fix_scope": "runtime_widened",
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
            "widened": True,
        }
        assert gate_semantics["repair_scope"] == "partial"

    def test_save_director_selection_persists_raw_advisory_payload_bundle(self):
        ctx = _make_ctx()
        ctx.current_project.db.save_director_selection = MagicMock()
        ctx.current_project.db.save_attempt_raw_rationale = MagicMock()
        ir = Stage4InterviewRound(ctx)

        with patch(
            "modules.core.stage4_interview_round.snapshot_logged_artifact",
            return_value={
                "candidate_key": "A|balanced",
                "content_hash": "hash123",
                "artifact_path": "logs/artifacts/stage4/ep_0001/rejected_best__A_balanced.txt",
            },
        ):
            ir._persist_director_selection(
                round_ctx=_make_round_ctx(),
                next_ep=1,
                round_num=0,
                candidates=[_candidate()],
                validation_results=[
                    {
                        "truth_gate_warnings": [{"severity": "CRITICAL", "text": "사망 NPC 등장"}],
                        "structured_violations": [{"reason": "연속성 위반"}],
                        "quality_signal_warnings": ["style drift"],
                        "warnings": ["[Python검증-HIGH] timeline drift"],
                        "warning_count": 4,
                    }
                ],
                director_result={
                    "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
                    "_director_thinking": "full director thinking payload",
                },
                advisory_summary={"truth_gate": 1},
                selected="A",
                verdict="REJECT",
                score=44,
                selection_reason="best candidate",
                verdict_reason="conflict",
                attempt_key="s4:ep1:arc1:a1",
                is_patch=False,
                is_patch_fallback=False,
                prev_score=0,
            )

        raw_calls = ctx.current_project.db.save_attempt_raw_rationale.call_args_list
        payload_calls = [call.kwargs for call in raw_calls if call.kwargs["payload_kind"] == "advisory_warnings_raw"]
        assert len(payload_calls) == 1
        payload = json.loads(payload_calls[0]["payload"])
        assert payload["selection_summary"]["truth_gate"] == 1
        candidate_payload = payload["candidate_validation_payloads"][0]
        assert candidate_payload["candidate_label"] == "A"
        assert candidate_payload["truth_gate_warnings"][0]["severity"] == "CRITICAL"
        assert candidate_payload["structured_violations"][0]["reason"] == "연속성 위반"
        assert candidate_payload["quality_signal_warnings"] == ["style drift"]
        assert candidate_payload["warnings"] == ["[Python검증-HIGH] timeline drift"]
        assert candidate_payload["warning_count"] == 4

    def test_build_director_decision_core_parts_injects_stage3_pov_and_writing_directive(self):
        ctx = _make_ctx()
        ctx.current_project.master_bible = {
            "MasterBible": {
                "protagonist_config": {
                    "pov": "first_person",
                    "external_pov_insert_policy": "limited",
                }
            }
        }
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.blueprint = {
            "_stage3_meta": {
                "quality_risk": True,
                "final_verdict": "REJECT",
                "last_score": 41,
            }
        }

        parts = ir.director_runtime._build_director_decision_core_parts(
            round_ctx=round_ctx,
            validation_results=[{"shared_failure_warnings": ["shared failure"]}],
            mandatory_context="mandatory context",
            writing_directive=_writing_directive_stub(
                ending_style="cliffhanger",
                expression_ban=["adverb"],
                emotion_required="rage",
            ),
        )

        assert parts[0] == "[타자 시점 삽입 정책]\n- policy: limited"
        assert parts[1] == "[작품 시점]\n- 기본 POV: first_person"
        assert "[WritingDirective]" in parts[2]
        assert "- ending_style: cliffhanger" in parts[2]
        assert "shared failure" == parts[3]
        assert "mandatory context" == parts[4]
        assert parts[5].startswith("[S3-META 경고]")

    def test_build_director_decision_core_parts_injects_stage3_binding_note(self):
        ctx = _make_ctx()
        ctx.current_project.master_bible = {
            "MasterBible": {
                "protagonist_config": {
                    "pov": "first_person",
                    "external_pov_insert_policy": "limited",
                }
            }
        }
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.blueprint = {
            "_stage3_meta": {
                "revision_required": True,
                "final_verdict": "PASS_WITH_FIX",
                "last_score": 77,
                "binding_prevalidation_issue_count": 2,
                "binding_prevalidation_categories": ["dead_npc", "fact_lock_location"],
            }
        }

        parts = ir.director_runtime._build_director_decision_core_parts(
            round_ctx=round_ctx,
            validation_results=[{"shared_failure_warnings": []}],
            mandatory_context="mandatory context",
            writing_directive=_writing_directive_stub(),
        )

        assert any(part.startswith("[S3-META binding]") for part in parts)
        assert any("dead_npc, fact_lock_location" in part for part in parts)
        assert any(part.startswith("[S3-META 주의]") for part in parts)

    def test_build_director_candidate_evidence_parts_formats_advisories_and_feedback(self):
        ctx = _make_ctx()
        ctx.current_project.arcs = []
        ctx.world_state = None
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()

        with (
            patch.object(
                ir,
                "_run_advisory_chain",
                return_value=[
                    "[TruthGate] hard fact conflict",
                    "[LM-B] npc moved",
                    "StyleSignal drift",
                    "[Whatever] 이상 없음",
                ],
            ),
            patch.object(ir, "_suppress_conflicting_advisories", side_effect=lambda parts: parts),
            patch.object(ir, "_log_attempt_event"),
        ):
            payload = ir.director_runtime._build_director_candidate_evidence_parts(
                candidates=[_candidate()],
                validation_results=[{"warnings": ["python warning"]}],
                round_ctx=round_ctx,
                next_ep=1,
                round_num=0,
                genre_name="무협",
                preflight_advisory="preflight note",
                director_feedback="history conflict",
            )

        assert payload.advisory_summary == {
            "truth_gate": 1,
            "npc_drift": 1,
            "style_signal": 1,
        }
        assert any("[CRITICAL · TruthGate] hard fact conflict" in part for part in payload.parts)
        assert any("[MAJOR · NpcDrift] [LM-B] npc moved" == part for part in payload.parts)
        assert any("[MAJOR · StyleSignal] StyleSignal drift" == part for part in payload.parts)
        assert any("[Whatever] 이상 없음" == part for part in payload.parts)
        assert any("🔍 preflight note" == part for part in payload.parts)
        assert any("python warning" in part for part in payload.parts)
        assert any("history conflict" in part for part in payload.parts)

    def test_build_director_advisory_payload_formats_and_summarizes_tags(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        with (
            patch.object(
                ir,
                "_run_advisory_chain",
                return_value=[
                    "[TruthGate] hard fact conflict",
                    "[LM-B] npc moved",
                    "StyleSignal drift",
                    "[Whatever] 이상 없음",
                ],
            ),
            patch.object(ir, "_suppress_conflicting_advisories", side_effect=lambda parts: parts),
            patch.object(ir, "_log_attempt_event"),
        ):
            payload = ir.director_runtime._build_director_advisory_payload(
                candidates=[_candidate()],
                validation_results=[_validation_result()],
                next_ep=1,
                round_num=0,
                arc_num=1,
                genre_name="무협",
            )

        assert payload.summary == {
            "truth_gate": 1,
            "npc_drift": 1,
            "style_signal": 1,
        }
        assert payload.parts == [
            "[CRITICAL · TruthGate] hard fact conflict",
            "[MAJOR · NpcDrift] [LM-B] npc moved",
            "[MAJOR · StyleSignal] StyleSignal drift",
            "[Whatever] 이상 없음",
        ]

    def test_run_director_review_phase_returns_payload_and_persists_selection(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        candidates = [_candidate()]
        validation_results = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": "44",
            "selection_reason": "best candidate",
            "verdict_reason": "conflict",
            "selected_candidate": {"manuscript": "candidate manuscript", "strategy_name": "balanced"},
            "feedback": {"issues": ["conflict"]},
            "action_items": ["fix ending"],
        }

        with (
            patch.object(
                ir.director_runtime,
                "build_director_input_pack",
                return_value=_DirectorInputPackResult(
                    mandatory_context="MANDATORY",
                    decision_core="DECISION",
                    candidate_evidence="EVIDENCE",
                    reference_appendix="APPENDIX",
                    advisory_summary={"shared_failure_warnings": 1},
                ),
            ),
            patch(
                "modules.core.stage4_interview_round.snapshot_logged_artifact",
                return_value={
                    "candidate_key": "A|balanced",
                    "content_hash": "hash123",
                    "artifact_path": "logs/artifacts/stage4/ep_001/attempt_01/rejected_best__A_balanced.txt",
                },
            ),
        ):
            result = ir.director_runtime.run_director_review_phase(
                stage4_spinner=MagicMock(),
                round_num=0,
                round_ctx=round_ctx,
                candidates=candidates,
                validation_results=validation_results,
                mandatory_context="base context",
                writing_directive="writing directive",
                director_feedback="",
                is_patch=False,
                is_patch_fallback=False,
                prev_score=0,
            )

        assert result.verdict == "REJECT"
        assert result.score == 44
        assert result.attempt_key == "s4:ep1:arc1:a1"
        assert result.selection_artifact_meta["candidate_key"] == "A|balanced"
        assert result.selection_artifact_meta["artifact_path"].endswith("rejected_best__A_balanced.txt")
        db_kwargs = ctx.current_project.db.save_director_selection.call_args.kwargs
        assert db_kwargs["attempt_key"] == result.attempt_key
        assert db_kwargs["candidate_key"] == "A|balanced"
        assert db_kwargs["artifact_path"].endswith("rejected_best__A_balanced.txt")
        assert db_kwargs["advisory_warnings"]["shared_failure_warnings"] == 1

    def test_run_director_decision_and_log_summary_returns_normalized_payload(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        candidates = [_candidate()]
        validation_results = [_validation_result()]
        ctx.agents["director"].select_and_judge_ensemble.return_value = {
            "selected": "A",
            "verdict": "REJECT",
            "score": "44",
            "selection_reason": "best candidate",
            "verdict_reason": "conflict",
            "action_items": ["fix ending"],
        }

        with patch.object(
            ir.director_runtime,
            "build_director_input_pack",
            return_value=_DirectorInputPackResult(
                mandatory_context="MANDATORY",
                decision_core="DECISION",
                candidate_evidence="EVIDENCE",
                reference_appendix="APPENDIX",
                advisory_summary={"shared_failure_warnings": 1},
            ),
        ):
            payload = ir.director_runtime._run_director_decision_and_log_summary(
                round_ctx=round_ctx,
                round_num=0,
                next_ep=round_ctx.next_ep,
                arc_num=round_ctx.arc_data.get("arc_no", 0),
                candidates=candidates,
                validation_results=validation_results,
                mandatory_context="base context",
                writing_directive="writing directive",
                director_feedback="",
            )

        assert payload.director_mandatory_context == "MANDATORY"
        assert payload.advisory_summary == {"shared_failure_warnings": 1}
        assert payload.selected == "A"
        assert payload.verdict == "REJECT"
        assert payload.score == 44
        assert payload.reason == "conflict"
        assert payload.attempt_key == "s4:ep1:arc1:a1"
        assert any("fix ending" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)

    def test_build_director_decision_payload_normalizes_score_and_attempt_key(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        payload = ir.director_runtime._build_director_decision_payload(
            director_result={
                "selected": "B",
                "verdict": "PASS",
                "final_verdict": "PASS",
                "score": "97",
                "selection_reason": "strongest ending",
                "verdict_reason": "clean landing",
                "error_category": "none",
            },
            advisory_summary={"shared_failure_warnings": 2},
            director_mandatory_context="MANDATORY",
            next_ep=3,
            round_num=1,
            arc_num=2,
        )

        assert payload.selected == "B"
        assert payload.verdict == "PASS"
        assert payload.score == 97
        assert payload.selection_reason == "strongest ending"
        assert payload.reason == "clean landing"
        assert payload.error_category == "none"
        assert payload.attempt_key == "s4:ep3:arc2:a2"
        assert payload.advisory_summary == {"shared_failure_warnings": 2}
        assert payload.director_mandatory_context == "MANDATORY"

    def test_log_director_review_prelude_emits_candidate_warning_summary(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        spinner = MagicMock()

        ir.director_runtime._log_director_review_prelude(
            stage4_spinner=spinner,
            next_ep=1,
            round_num=0,
            arc_num=1,
            candidates=[{"manuscript": "candidate manuscript"}],
            validation_results=[{"warnings": ["timeline drift", "tone drift"]}],
        )

        spinner.update_detail.assert_called_once()
        assert any("후보 수: 1개" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)
        assert any("timeline drift" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)

    def test_complete_round_after_review_routes_review_and_generation_payloads(self):
        from types import SimpleNamespace

        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        chief_writer = MagicMock()
        stage4_spinner = MagicMock()
        final_result = {"status": "done"}
        review = SimpleNamespace(
            director_result={"selected_candidate": {"manuscript": "candidate manuscript"}},
            director_mandatory_context="director mandatory",
            selected="A",
            verdict="PASS",
            score=91,
            reason="good",
            error_category="",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A|balanced"},
        )
        generation = SimpleNamespace(
            is_patch=True,
            is_patch_fallback=False,
            prev_score=77,
            prev_manuscript="prev manuscript",
            tot_used=True,
            mad_used=False,
            asp_manuscript="asp manuscript",
        )
        ir._maybe_enrich_director_result = MagicMock(return_value={"enriched": True})
        ir._merge_retry_advisory_feedback = MagicMock(return_value="merged feedback")
        ir._process_verdict = MagicMock(return_value=("pass-result", "next feedback", {"score": 80}, {"trace": True}))
        ir._finalize_round_outcome = MagicMock(return_value=final_result)

        result = ir._complete_round_after_review(
            next_ep=1,
            round_num=0,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            review=review,
            generation=generation,
            director_feedback="raw feedback",
            previous_attempt={"old": True},
            candidates=[_candidate()],
            validation_results=[_validation_result()],
            director_memory_context="memory context",
            stage4_spinner=stage4_spinner,
        )

        assert result == final_result
        ir._maybe_enrich_director_result.assert_called_once_with(
            {"selected_candidate": {"manuscript": "candidate manuscript"}},
            manuscript_text="candidate manuscript",
        )
        ir._merge_retry_advisory_feedback.assert_called_once_with("raw feedback")
        process_kwargs = ir._process_verdict.call_args.kwargs
        assert process_kwargs["director_result"] == {"enriched": True}
        assert process_kwargs["director_feedback"] == "merged feedback"
        assert process_kwargs["verdict"] == "PASS"
        assert process_kwargs["score"] == 91
        assert process_kwargs["is_patch"] is True
        assert process_kwargs["prev_score"] == 77
        assert process_kwargs["director_mandatory_context"] == "director mandatory"
        assert process_kwargs["director_memory_context"] == "memory context"
        finalize_kwargs = ir._finalize_round_outcome.call_args.kwargs
        assert finalize_kwargs["director_result"] == {"enriched": True}
        assert finalize_kwargs["director_feedback"] == "next feedback"
        assert finalize_kwargs["previous_attempt"] == {"score": 80}
        assert finalize_kwargs["trace_meta"] == {"trace": True}
        assert finalize_kwargs["selected"] == "A"
        assert finalize_kwargs["attempt_key"] == "attempt-1"
        assert finalize_kwargs["is_patch"] is True
        assert finalize_kwargs["prev_manuscript"] == "prev manuscript"
        assert finalize_kwargs["tot_used"] is True
        assert finalize_kwargs["asp_manuscript"] == "asp manuscript"

    def test_finalize_round_outcome_routes_pass_branch_with_trace_meta(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        chief_writer = MagicMock()
        pass_result = MagicMock(name="pass_result")
        finalized = {"status": "pass"}
        ir._collect_validation_warning_lines = MagicMock(return_value=["warn"])
        ir._finalize_pass_result = MagicMock(return_value=finalized)
        ir._handle_reject = MagicMock()

        result = ir._finalize_round_outcome(
            pass_result=pass_result,
            next_ep=1,
            round_num=0,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result={"verdict": "PASS"},
            director_feedback="feedback",
            previous_attempt={},
            trace_meta={
                "director_result": {"verdict": "PASS_WITH_FIX", "trace": True},
                "final_verdict": "PASS_WITH_FIX",
                "final_score": 88,
                "patch_trace": {"mode": "patch"},
            },
            candidates=[_candidate()],
            validation_results=[_validation_result()],
            initial_verdict="PASS",
            initial_score=81,
            selected="A",
            reason="ok",
            error_category="",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A"},
            is_patch=False,
            is_patch_fallback=False,
            prev_score=0,
            prev_manuscript="prev",
            tot_used=False,
            mad_used=False,
            asp_manuscript="",
        )

        assert result == finalized
        ir._handle_reject.assert_not_called()
        ir._finalize_pass_result.assert_called_once()
        kwargs = ir._finalize_pass_result.call_args.kwargs
        assert kwargs["trace_director_result"] == {"verdict": "PASS_WITH_FIX", "trace": True}
        assert kwargs["final_verdict"] == "PASS_WITH_FIX"
        assert kwargs["final_score"] == 88
        assert kwargs["validation_warnings"] == ["warn"]
        assert kwargs["is_patch"] is True
        assert kwargs["trace_patch_trace"] == {"mode": "patch"}

    def test_finalize_round_pass_path_delegates_trace_payload_to_finalize_pass(self):
        from modules.core.stage4_interview_round import _RoundOutcomeTracePayload

        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        chief_writer = MagicMock()
        pass_result = MagicMock(name="pass_result")
        finalized = {"status": "pass"}
        ir._finalize_pass_result = MagicMock(return_value=finalized)

        result = ir._finalize_round_pass_path(
            pass_result=pass_result,
            next_ep=1,
            round_num=0,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result={"verdict": "PASS"},
            director_feedback="feedback",
            trace_payload=_RoundOutcomeTracePayload(
                trace_director_result={"verdict": "PASS_WITH_FIX", "trace": True},
                final_verdict="PASS_WITH_FIX",
                final_score=88,
                validation_warnings=["warn"],
                is_patch=True,
                trace_patch_trace={"mode": "patch"},
            ),
            initial_verdict="PASS",
            initial_score=81,
            selected="A",
            reason="ok",
            error_category="",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A"},
            is_patch_fallback=False,
            tot_used=False,
            mad_used=False,
            asp_manuscript="",
        )

        assert result == finalized
        ir._finalize_pass_result.assert_called_once()
        kwargs = ir._finalize_pass_result.call_args.kwargs
        assert kwargs["trace_director_result"] == {"verdict": "PASS_WITH_FIX", "trace": True}
        assert kwargs["final_verdict"] == "PASS_WITH_FIX"
        assert kwargs["final_score"] == 88
        assert kwargs["validation_warnings"] == ["warn"]
        assert kwargs["is_patch"] is True
        assert kwargs["trace_patch_trace"] == {"mode": "patch"}

    def test_build_pass_result_logging_payload_snapshots_trace_candidate_when_attempt_meta_missing(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        pass_result = MagicMock()
        pass_result.attempt_artifact_meta = {}
        pass_result.final_manuscript = "final manuscript"
        ir._build_retry_advisory_digest = MagicMock(return_value="runtime digest")
        ir._build_gate_semantics_payload = MagicMock(
            return_value={
                "director_verdict": "PASS_WITH_FIX",
                "gate_basis": "trace_gate",
                "repair_scope": "rewrite",
            }
        )

        with patch(
            "modules.core.stage4_interview_round.snapshot_logged_artifact",
            return_value={
                "candidate_key": "stage4|A",
                "content_hash": "hash-123",
                "artifact_path": "logs/final.json",
            },
        ):
            payload = ir._build_pass_result_logging_payload(
                pass_result=pass_result,
                next_ep=1,
                round_num=0,
                round_ctx=round_ctx,
                director_result={"selection_reason": "director selection"},
                trace_director_result={
                    "selected": "A",
                    "selected_candidate": {"strategy_name": "balanced"},
                    "selection_reason": "trace selection",
                    "verdict_reason": "trace verdict",
                },
                reason="fallback reason",
                is_patch=False,
                trace_patch_trace={"mode": "patch"},
            )

        assert payload.log_artifact_meta["candidate_key"] == "stage4|A"
        assert payload.log_artifact_meta["content_hash"] == "hash-123"
        assert payload.log_artifact_meta["artifact_path"] == "logs/final.json"
        assert payload.session_selection_reason == "trace selection"
        assert payload.session_verdict_reason == "trace verdict"
        assert payload.session_runtime_advisory == "runtime digest"
        assert payload.session_retry_directives == ""
        assert payload.session_gate_semantics["gate_basis"] == "trace_gate"

    def test_sync_pass_result_selection_rationale_prefers_trace_fix_scope(self):
        ctx = _make_ctx()
        ctx.current_project.db = MagicMock()
        ir = Stage4InterviewRound(ctx)

        ir._sync_pass_result_selection_rationale(
            attempt_key="attempt-1",
            trace_director_result={"fix_scope": "rewrite"},
            director_result={"fix_scope": "patch"},
            selection_reason="selection",
            verdict_reason="verdict",
        )

        ctx.current_project.db.update_director_selection_rationale.assert_called_once_with(
            attempt_key="attempt-1",
            selection_reason="selection",
            verdict_reason="verdict",
            fix_scope="rewrite",
        )

    def test_sync_reject_result_selection_rationale_prefers_trace_fix_scope(self):
        ctx = _make_ctx()
        ctx.current_project.db = MagicMock()
        ir = Stage4InterviewRound(ctx)

        ir.reject_runtime._sync_reject_result_selection_rationale(
            attempt_key="attempt-1",
            trace_director_result={"fix_scope": "partial"},
            director_result={"fix_scope": "full"},
            selection_reason="selection",
            verdict_reason="verdict",
        )

        ctx.current_project.db.update_director_selection_rationale.assert_called_once_with(
            attempt_key="attempt-1",
            selection_reason="selection",
            verdict_reason="verdict",
            fix_scope="partial",
        )

    def test_build_reject_retry_snapshot_preserves_candidate_and_retry_metadata(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._collect_validation_warning_lines = MagicMock(return_value=["warn-a"])
        ir._inherit_attempt_history = MagicMock(return_value=[{"old": True}])
        ir._set_retry_budget_axes = MagicMock(return_value={"repair": "patch_revision"})

        payload = ir.reject_runtime._build_reject_retry_snapshot(
            director_result={
                "selected_candidate": {
                    "manuscript": "candidate manuscript",
                    "strategy_name": "balanced",
                },
                "selection_reason": "best candidate",
                "verdict_reason": "continuity conflict",
                "director_verdict": "REJECT",
                "final_verdict": "REJECT",
                "gate_basis": "consistency",
                "repair_scope": "partial",
                "authoritative_fix_scope": "",
                "authoritative_fix_scope_violation": {"type": "blank_authoritative_fix_scope"},
                "consistency_checklist": {"rule": "keep"},
                "state_updates": {"hud": "snapshot"},
                "open_review": "review note",
                "contradiction_types": ["scene_overlap"],
                "contradiction_details": ["detail-1", "detail-2"],
                "firewall_triggered": True,
                "firewall_reason": "firewall",
            },
            selected="A",
            director_feedback="retry with fix",
            action_items=["fix ending"],
            score=44,
            validation_results=[_validation_result()],
            reject_bucket="constraint_violation",
            tot_used=True,
            mad_used=False,
            resolved_fix_scope="partial",
            resolved_fix_scope_reasoning="continuity replay",
            resolved_fix_pack={
                "must_fix": ["ending"],
                "target_kind": "local_sentence",
                "provenance": "runtime_synthesized",
                "provenance_sources": ["flashback_continuity_localfix"],
            },
            error_category="LOGIC_ERROR",
            feedback_provenance={
                "director_feedback_text": "director note",
                "runtime_advisory": "runtime digest",
                "retry_directives": "retry directives",
            },
            previous_attempt={"old": True},
            round_num=0,
        )

        assert payload.candidate_key == "A|balanced"
        assert payload.previous_attempt["strategy"] == "A"
        assert payload.previous_attempt["selected_strategy_key"] == "balanced"
        assert payload.previous_attempt["best_manuscript"] == "candidate manuscript"
        assert payload.previous_attempt["validation_warnings"] == ["warn-a"]
        assert payload.previous_attempt["reject_bucket"] == "constraint_violation"
        assert payload.previous_attempt["_tot_used"] is True
        assert payload.previous_attempt["_mad_used"] is False
        assert payload.previous_attempt["fix_scope"] == "partial"
        assert payload.previous_attempt["authoritative_fix_scope"] == ""
        assert payload.previous_attempt["authoritative_fix_scope_violation"] == {
            "type": "blank_authoritative_fix_scope"
        }
        assert payload.previous_attempt["director_feedback_text"] == "director note"
        assert payload.previous_attempt["runtime_advisory"] == "runtime digest"
        assert payload.previous_attempt["retry_directives"] == "retry directives"
        assert payload.previous_attempt["prior_attempts"] == [{"old": True}]
        assert payload.previous_attempt["retry_budget_axes"] == {"repair": "patch_revision"}
        assert payload.previous_attempt["fix_pack"]["provenance"] == "runtime_synthesized"
        assert payload.previous_attempt["fix_pack"]["provenance_sources"] == ["flashback_continuity_localfix"]
        assert payload.previous_attempt["fix_pack_origin"] == {
            "provenance": "runtime_synthesized",
            "provenance_sources": ["flashback_continuity_localfix"],
            "routing_contract": "runtime_generated_prefers_patch",
        }
        assert payload.previous_attempt["scope_authority"] == {
            "fix_scope": "partial",
            "repair_scope": "partial",
            "scope_origin": {
                "fix_scope": "runtime_widened",
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
            "authoritative_fix_scope_violation": {"type": "blank_authoritative_fix_scope"},
            "widened": True,
        }
        assert payload.previous_attempt["repair_contract"] == {
            "subtype": "scene_overlap",
            "fix_scope": "partial",
            "repair_scope": "partial",
            "scope_origin": {
                "fix_scope": "runtime_widened",
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
            "provenance": "runtime_synthesized",
            "provenance_sources": ["flashback_continuity_localfix"],
            "target_kind": "local_sentence",
        }

    def test_retry_pathology_payload_separates_authoritative_and_derived_fix_scope(self):
        from modules.core.stage4_outcome_runtime import Stage4OutcomeRuntime

        owner = MagicMock()
        owner.interview_round = MagicMock()
        owner.interview_round._evaluate_fix_pack_contract.return_value = {
            "ready": False,
            "reason": "missing_fix_pack",
            "fix_pack": {},
        }
        runtime = Stage4OutcomeRuntime(owner)

        payload = runtime.build_retry_pathology_payload(
            ep_num=1,
            round_num=2,
            previous_attempt={
                "reject_bucket": "quality_issue",
                "gate_basis": "director_primary_reject",
                "fix_scope": "partial",
                "authoritative_fix_scope": "",
                "authoritative_fix_scope_violation": {"type": "blank_authoritative_fix_scope"},
                "repair_scope": "partial",
                "error_category": "QUALITY_ISSUE",
                "fix_scope_reasoning": "[IFC] keep the ending grounded",
                "open_review": "review",
                "score": 50,
                "plateau_detected": True,
                "fix_pack": {},
                "conflict_contract": {
                    "contract_type": "post_select_conflict",
                    "conflicts": [
                        {
                            "conflict_type": "continuity",
                            "conflict_detail": "repeat detected",
                            "source_episode": "",
                            "expected_truth": "repeat detected",
                        }
                    ],
                },
            },
        )

        assert payload["fix_scope"] == "partial"
        assert payload["authoritative_fix_scope"] == ""
        assert payload["authoritative_fix_scope_violation"] == {"type": "blank_authoritative_fix_scope"}
        assert payload["fix_pack_reason"] == "missing_fix_pack"
        assert payload["conflict_contract"]["contract_type"] == "post_select_conflict"

    def test_post_select_conflict_snapshot_preserves_high_score_downgraded_pass_rationale(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._collect_validation_warning_lines = MagicMock(return_value=["warn-a"])
        ir._inherit_attempt_history = MagicMock(return_value=[{"old": True}])
        ir._set_retry_budget_axes = MagicMock(return_value={"repair": "rewrite_regenerate"})

        payload = ir.reject_runtime._build_reject_retry_snapshot(
            director_result={
                "selected_candidate": {
                    "manuscript": "candidate manuscript",
                    "strategy_name": "balanced",
                },
                "selection_reason": "best candidate because covert network felt sharp",
                "verdict_reason": "sharp covert network",
                "director_verdict": "PASS",
                "final_verdict": "REJECT",
                "gate_basis": "post_select_conflict",
                "repair_scope": "full",
                "pre_firewall_score": 98,
                "consistency_checklist": {"rule": "keep"},
                "state_updates": {"hud": "snapshot"},
                "open_review": "keep the burner phone idea",
                "contradiction_types": ["scene_overlap"],
                "contradiction_details": ["detail-1"],
                "firewall_triggered": True,
                "firewall_reason": "firewall",
            },
            selected="A",
            director_feedback="conflict-first reject feedback",
            action_items=["rebuild from prior authority"],
            score=44,
            validation_results=[{}],
            reject_bucket="post_select_conflict",
            tot_used=True,
            mad_used=False,
            resolved_fix_scope="full",
            resolved_fix_scope_reasoning="conflict-first rewrite",
            resolved_fix_pack={"patch_targets": ["anchor"], "do_not_regress": ["burner phone"]},
            error_category="LOGIC_ERROR",
            feedback_provenance={
                "director_feedback_text": "director note",
                "runtime_advisory": "runtime digest",
                "retry_directives": "retry directives",
            },
            previous_attempt={
                "old": True,
                "provisional_pass_downgrade": True,
                "conflict_contract": {
                    "contract_type": "post_select_conflict",
                    "conflicts": [
                        {
                            "conflict_type": "continuity",
                            "conflict_detail": "scene overlap conflict",
                            "source_episode": "",
                            "expected_truth": "scene overlap conflict",
                        }
                    ],
                },
                "reuse_contract": {
                    "mode": "best_manuscript_baseline",
                    "baseline_field": "best_manuscript",
                    "conflict_field": "conflict_contract",
                    "preserve_rationale": True,
                },
            },
            round_num=0,
        )

        assert payload.previous_attempt["selection_reason"] == "best candidate because covert network felt sharp"
        assert payload.previous_attempt["open_review"] == "keep the burner phone idea"
        assert payload.previous_attempt["fix_pack"] == {}
        assert payload.previous_attempt["rejection_reason"] == "conflict-first reject feedback"
        assert payload.previous_attempt["conflict_contract"]["contract_type"] == "post_select_conflict"
        assert payload.previous_attempt["reuse_contract"]["mode"] == "best_manuscript_baseline"

    def test_post_select_conflict_snapshot_preserves_bounded_fix_pack_hints(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._collect_validation_warning_lines = MagicMock(return_value=["warn-a"])
        ir._inherit_attempt_history = MagicMock(return_value=[{"old": True}])
        ir._set_retry_budget_axes = MagicMock(return_value={"repair": "rewrite_regenerate"})

        payload = ir.reject_runtime._build_reject_retry_snapshot(
            director_result={
                "selected_candidate": {
                    "manuscript": "candidate manuscript",
                    "strategy_name": "balanced",
                },
                "selection_reason": "best candidate because proper noun continuity almost landed",
                "verdict_reason": "needs final continuity repair",
                "director_verdict": "PASS_WITH_FIX",
                "final_verdict": "REJECT",
                "gate_basis": "post_select_conflict",
                "repair_scope": "full",
                "pre_firewall_score": 92,
                "consistency_checklist": {"rule": "keep"},
                "state_updates": {"hud": "snapshot"},
                "open_review": "rename institution only",
                "contradiction_types": ["proper_noun"],
                "contradiction_details": ["detail-1"],
                "firewall_triggered": True,
                "firewall_reason": "firewall",
            },
            selected="A",
            director_feedback="conflict-first reject feedback",
            action_items=["rename institution anchor"],
            score=44,
            validation_results=[{}],
            reject_bucket="post_select_conflict",
            tot_used=True,
            mad_used=False,
            resolved_fix_scope="full",
            resolved_fix_scope_reasoning="conflict-first rewrite",
            resolved_fix_pack={
                "patch_targets": ["기관명 표기 문장"],
                "must_fix": ["기관명을 이전 화 canonical 표기로 교체"],
                "do_not_regress": ["opening continuity 유지"],
                "success_condition": "proper noun continuity resolved",
                "target_kind": "entity_ref",
            },
            error_category="LOGIC_ERROR",
            feedback_provenance={
                "director_feedback_text": "director note",
                "runtime_advisory": "runtime digest",
                "retry_directives": "retry directives",
            },
            previous_attempt={
                "old": True,
                "provisional_pass_downgrade": True,
                "conflict_contract": {
                    "contract_type": "post_select_conflict",
                    "conflicts": [
                        {
                            "conflict_type": "continuity",
                            "conflict_detail": "scene overlap conflict",
                            "source_episode": "",
                            "expected_truth": "scene overlap conflict",
                        }
                    ],
                },
                "reuse_contract": {
                    "mode": "best_manuscript_baseline",
                    "baseline_field": "best_manuscript",
                    "conflict_field": "conflict_contract",
                    "preserve_rationale": True,
                },
            },
            round_num=0,
        )

        assert payload.previous_attempt["fix_pack"]["patch_targets"] == ["기관명 표기 문장"]
        assert payload.previous_attempt["post_select_fix_pack_preserved"] is True

    def test_build_reject_guidance_payload_applies_inplace_gate_and_mad_hint(self):
        ctx = _make_ctx()
        mad_module = MagicMock()
        mad_result = MagicMock()
        mad_result.consensus_output = "consensus repair"
        mad_module.deliberate.return_value = mad_result

        def _get_module(name):
            if name == "multi_agent_deliberation":
                return mad_module
            return None

        ctx.get_module.side_effect = _get_module
        ir = Stage4InterviewRound(ctx)
        ir._build_retry_feedback_provenance = MagicMock(
            return_value={
                "merged_feedback": "merged reject feedback",
                "director_feedback_text": "director note",
                "runtime_advisory": "runtime digest",
                "retry_directives": "retry directives",
            }
        )
        ir._classify_reject_bucket = MagicMock(return_value="constraint_violation")
        ir._is_continuity_replay_reject = MagicMock(return_value=False)
        ir._evaluate_fix_pack_contract = MagicMock(return_value={"ready": False, "reason": "missing_fix_pack"})

        payload = ir.reject_runtime._build_reject_guidance_payload(
            director_result={
                "selected_candidate": {"manuscript": "candidate manuscript"},
                "feedback": {"issues": ["constraint drift"]},
                "action_items": ["repair constraint"],
                "fix_scope": "inplace",
                "fix_scope_reasoning": "local retry",
                "fix_pack": {"must_fix": ["anchor"]},
            },
            director_feedback="initial reject",
            validation_results=[_validation_result()],
            selected="A",
            round_num=0,
            blueprint={"episode": 1},
            prev_manuscript="previous manuscript",
            tot_used=False,
            mad_used=False,
            error_category="",
        )

        assert payload.reject_bucket == "constraint_violation"
        assert payload.resolved_fix_scope == "partial"
        assert "REJECT retry widened to partial" in payload.director_feedback
        assert "[MAD 제약/합의 개선 지침]" in payload.director_feedback
        assert payload.feedback_provenance["runtime_advisory"] == "runtime digest"
        assert payload.feedback_provenance["retry_directives"] == "retry directives"
        assert payload.mad_used is True
        assert payload.tot_used is False
        mad_module.deliberate.assert_called_once()

    def test_build_reject_guidance_payload_preserves_bounded_post_select_fix_pack(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._build_retry_feedback_provenance = MagicMock(
            return_value={
                "merged_feedback": "[Continuity Conflict] proper noun mismatch",
                "director_feedback_text": "director note",
                "runtime_advisory": "",
                "retry_directives": "",
            }
        )
        ir._classify_reject_bucket = MagicMock(return_value="constraint_violation")
        ir._is_continuity_replay_reject = MagicMock(return_value=False)

        payload = ir.reject_runtime._build_reject_guidance_payload(
            director_result={
                "selected_candidate": {"manuscript": "candidate manuscript"},
                "feedback": {"issues": ["proper noun mismatch"]},
                "action_items": ["rename institution anchor"],
                "fix_scope": "inplace",
                "fix_scope_reasoning": "director local repair",
                "gate_basis": "post_select_conflict",
                "fix_pack": {
                    "patch_targets": ["기관명 표기 문장"],
                    "must_fix": ["기관명을 이전 화 canonical 표기로 교체"],
                    "do_not_regress": ["opening continuity 유지"],
                    "success_condition": "proper noun continuity resolved",
                    "target_kind": "entity_ref",
                },
            },
            director_feedback="initial reject",
            validation_results=[_validation_result()],
            selected="A",
            round_num=0,
            blueprint={"episode": 1},
            prev_manuscript="previous manuscript",
            tot_used=False,
            mad_used=False,
            error_category="LOGIC_ERROR",
        )

        assert payload.reject_bucket == "post_select_conflict"
        assert payload.resolved_fix_scope == "full"
        assert payload.resolved_fix_pack["patch_targets"] == ["기관명 표기 문장"]
        assert "TF-F1" in payload.resolved_fix_scope_reasoning

    def test_record_reject_attempt_artifact_builds_reject_attempt_payload(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.model_tier = "writer-model"
        ir._record_s4_attempt = MagicMock(return_value={"artifact_path": "reject.json"})
        ir._build_gate_semantics_payload = MagicMock(
            side_effect=lambda payload: {
                "gate_basis": payload.get("gate_basis", "consistency"),
                "repair_scope": payload.get("repair_scope", ""),
            }
        )
        ir._build_fix_pack_payload = MagicMock(side_effect=lambda payload: dict(payload.get("fix_pack", {}) or {}))
        ir._last_advisory_summary = {"blocking": 1}
        ir._last_retry_budget_axes = {"repair": "patch_revision"}

        payload = ir.reject_runtime._record_reject_attempt_artifact(
            next_ep=1,
            round_num=0,
            round_ctx=round_ctx,
            score=44,
            is_patch=False,
            prev_score=94,
            is_patch_fallback=False,
            director_feedback="reject feedback",
            resolved_fix_scope="partial",
            resolved_fix_scope_reasoning="continuity replay",
            director_result={
                "selection_reason": "best candidate",
                "verdict_reason": "contradiction",
                "open_review": "open review",
                "score_breakdown": {"consistency": 0},
            },
            candidate_key="A|balanced",
            previous_attempt={
                "best_manuscript": "candidate manuscript",
                "gate_basis": "post_select_conflict",
                "repair_scope": "full",
                "fix_pack": {
                    "patch_targets": ["opening_turnback_line"],
                    "must_fix": ["오프닝 동선 반전을 직전 화 엔딩 기준으로 수정"],
                    "target_kind": "local_sentence",
                },
                "scope_origin": {
                    "fix_scope": "post_select_conflict_override",
                    "authoritative_fix_scope": "director_authoritative",
                    "repair_scope": "runtime_lane",
                },
                "conflict_contract": {
                    "contract_type": "post_select_conflict",
                    "conflicts": [{"conflict_type": "continuity"}],
                },
                "reuse_contract": {
                    "mode": "best_manuscript_baseline",
                    "baseline_field": "best_manuscript",
                },
            },
            prev_manuscript="previous manuscript",
            feedback_provenance={
                "runtime_advisory": "runtime digest",
                "retry_directives": "retry directives",
            },
            reject_bucket="post_select_conflict",
            error_category="LOGIC_ERROR",
        )

        assert payload == {"artifact_path": "reject.json"}
        kwargs = ir._record_s4_attempt.call_args.kwargs
        assert kwargs["verdict"] == "REJECT"
        assert kwargs["fix_scope"] == "partial"
        assert kwargs["fix_scope_reasoning"] == "continuity replay"
        assert kwargs["candidate_key"] == "A|balanced"
        assert kwargs["artifact_payload"] == "candidate manuscript"
        assert kwargs["runtime_advisory"] == "runtime digest"
        assert kwargs["retry_directives"] == "retry directives"
        assert kwargs["error_category"] == "LOGIC_ERROR"
        assert kwargs["reject_bucket"] == "post_select_conflict"
        assert kwargs["advisory_flags"]["gate_semantics"]["gate_basis"] == "post_select_conflict"
        assert kwargs["advisory_flags"]["gate_semantics"]["repair_scope"] == "full"
        assert (
            kwargs["advisory_flags"]["gate_semantics"]["scope_origin"]["fix_scope"] == "post_select_conflict_override"
        )
        assert (
            kwargs["advisory_flags"]["gate_semantics"]["conflict_resolution_linkage"]["original_contract_type"]
            == "post_select_conflict"
        )
        assert kwargs["advisory_flags"]["gate_semantics"]["reuse_contract"]["mode"] == "best_manuscript_baseline"
        assert kwargs["advisory_flags"]["fix_pack"]["patch_targets"] == ["opening_turnback_line"]
        assert kwargs["advisory_flags"]["retry_budget_axes"] == {"repair": "patch_revision"}

    def test_record_reject_round_metrics_persists_cost_record_and_ui_log(self):
        ctx = _make_ctx()
        ctx.current_project.metrics_session_id = "sess-stage4-reject"
        ir = Stage4InterviewRound(ctx)

        ir.reject_runtime._record_reject_round_metrics(
            next_ep=2,
            reject_bucket="structure_error",
            score=44,
            round_num=1,
            selected="B",
            asp_manuscript="asp draft",
            tot_used=True,
            mad_used=False,
            director_feedback="repair the scene boundary",
        )

        cost_kwargs = ctx.current_project.db.save_cost_record.call_args.kwargs
        assert cost_kwargs["session_id"] == "sess-stage4-reject"
        assert cost_kwargs["scope_id"] == 2
        assert cost_kwargs["model_breakdown"]["event"] == "stage4_reject"
        assert cost_kwargs["model_breakdown"]["bucket"] == "structure_error"
        assert cost_kwargs["model_breakdown"]["strategy"] == "B"
        assert cost_kwargs["model_breakdown"]["intelligence_used"] == {
            "asp": True,
            "tot": True,
            "mad": False,
        }
        ctx.ui.log.assert_called_once()
        assert "2차 면담 REJECT" in ctx.ui.log.call_args.args[0]

    def test_run_reject_followup_side_effects_records_integrations_and_appends_injection(self):
        ctx = _make_ctx()
        ctx.failure_learner = MagicMock()
        ctx.adaptive_manager = MagicMock()
        ctx.adaptive_manager.get_injection_prompt.return_value = "adaptive injection"
        ctx.quality_dashboard = MagicMock()
        ir = Stage4InterviewRound(ctx)

        updated_feedback = ir.reject_runtime._run_reject_followup_side_effects(
            next_ep=3,
            arc_num=4,
            reject_bucket="post_select_conflict",
            director_feedback="reject feedback",
            score=52,
            round_num=1,
            previous_attempt={
                "contradiction_types": ["opening_action_continuity"],
                "repair_contract": {"subtype": "opening_action_continuity", "repair_scope": "full"},
                "scope_authority": {"authority_kind": "post_select_conflict"},
                "scope_origin": {"fix_scope": "post_select_conflict_override"},
                "fix_pack_reason": "bounded_continuity_patch",
                "fix_pack_origin": {"source": "post_select_conflict"},
            },
        )

        assert updated_feedback == "reject feedback\nadaptive injection"
        ctx.failure_learner.record_failure.assert_called_once_with(
            stage=4,
            episode=3,
            arc=4,
            reason="post_select_conflict: reject feedback",
            details={
                "bucket": "post_select_conflict",
                "score": 52,
                "round": 1,
                "contradiction_types": ["opening_action_continuity"],
                "dominant_contradiction_type": "opening_action_continuity",
                "repair_contract": {"subtype": "opening_action_continuity", "repair_scope": "full"},
                "scope_authority": {"authority_kind": "post_select_conflict"},
                "scope_origin": {"fix_scope": "post_select_conflict_override"},
                "fix_pack_reason": "bounded_continuity_patch",
                "fix_pack_origin": {"source": "post_select_conflict"},
            },
        )
        ctx.adaptive_manager.record_failure.assert_called_once_with(
            ep_num=3,
            agent="director",
            error_info={
                "reason": "reject feedback",
                "bucket": "post_select_conflict",
                "score": 52,
                "round": 1,
                "contradiction_types": ["opening_action_continuity"],
                "dominant_contradiction_type": "opening_action_continuity",
                "repair_contract": {"subtype": "opening_action_continuity", "repair_scope": "full"},
                "scope_authority": {"authority_kind": "post_select_conflict"},
                "scope_origin": {"fix_scope": "post_select_conflict_override"},
                "fix_pack_reason": "bounded_continuity_patch",
                "fix_pack_origin": {"source": "post_select_conflict"},
            },
            attempt=2,
        )
        ctx.adaptive_manager.get_injection_prompt.assert_called_once_with(
            ep_num=3,
            agent="director",
            current_attempt=2,
        )
        dashboard_kwargs = ctx.quality_dashboard.record_validation.call_args.kwargs
        assert dashboard_kwargs["ep_num"] == 3
        assert dashboard_kwargs["stage"] == 4
        assert dashboard_kwargs["result"]["decision"] == "REJECT"
        violation = dashboard_kwargs["result"]["violations"][0]
        assert "adaptive injection" in violation["description"]
        assert violation["subtype"] == "opening_action_continuity"
        assert violation["contradiction_types"] == ["opening_action_continuity"]
        assert violation["repair_contract"] == {"subtype": "opening_action_continuity", "repair_scope": "full"}
        assert violation["scope_authority"] == {"authority_kind": "post_select_conflict"}
        assert violation["scope_origin"] == {"fix_scope": "post_select_conflict_override"}
        assert violation["fix_pack_reason"] == "bounded_continuity_patch"
        assert violation["fix_pack_origin"] == {"source": "post_select_conflict"}

    def test_append_pass_episode_log_routes_feedback_and_artifact_meta(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        chief_writer = MagicMock()
        chief_writer.model_tier = "writer-model"
        ir._append_episode_log = MagicMock()

        ir._append_pass_episode_log(
            ep_num=1,
            round_num=0,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result={},
            trace_director_result={"verdict_reason": "trace verdict"},
            director_feedback="raw feedback",
            initial_verdict="PASS",
            initial_score=91,
            final_verdict="PASS_WITH_FIX",
            final_score=98,
            is_patch=True,
            is_patch_fallback=False,
            selection_artifact_meta={
                "candidate_key": "A",
                "content_hash": "sel-hash",
                "artifact_path": "selection.json",
            },
            validation_warnings=["warn-a"],
            final_warnings=["final-warn"],
            patch_trace={"mode": "patch"},
            tot_used=False,
            mad_used=True,
            logging_payload=_PassResultLoggingPayload(
                log_artifact_meta={
                    "candidate_key": "stage4|A",
                    "content_hash": "hash-123",
                    "artifact_path": "artifact.json",
                },
                session_selection_reason="selection",
                session_verdict_reason="verdict",
                session_runtime_advisory="runtime digest",
                session_retry_directives="retry directives",
                session_gate_semantics={},
            ),
            arc_num=1,
            asp_manuscript="asp",
        )

        ir._append_episode_log.assert_called_once()
        append_kwargs = ir._append_episode_log.call_args.kwargs
        assert append_kwargs["feedback_provenance"]["director_feedback"] == "trace verdict"
        assert append_kwargs["feedback_provenance"]["runtime_advisory"] == "runtime digest"
        assert append_kwargs["candidate_key"] == "stage4|A"
        assert append_kwargs["selection_candidate_key"] == "A"

    def test_stage4_pass_episode_log_payload_prefers_trace_reason_and_selection_artifact_meta(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        ctx = _make_ctx()
        ctx.current_project.id = "proj-1"
        chief_writer = MagicMock()
        chief_writer.model_tier = "writer-model"

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_payload,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=chief_writer,
                director_result={},
                trace_director_result={"verdict_reason": "trace verdict"},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload["feedback_provenance"]["director_feedback"] == "trace verdict"
        assert payload["feedback_provenance"]["runtime_advisory"] == "runtime digest"
        assert payload["feedback_provenance"]["retry_directives"] == "retry directives"
        assert payload["candidate_key"] == "stage4|A"
        assert payload["selection_candidate_key"] == "A"
        assert payload["selection_content_hash"] == "sel-hash"
        assert payload["selection_artifact_path"] == "selection.json"
        assert payload["model"] == "writer-model"
        assert payload["asp_used"] is True
        assert payload["attempt_key"] == "s4:ep1:arc1:a1"

    def test_build_pass_result_logging_payload_preserves_fix_pack_when_trace_is_partial(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._build_retry_advisory_digest = MagicMock(return_value="[advisory] keep continuity")

        payload = ir._build_pass_result_logging_payload(
            pass_result=SimpleNamespace(
                attempt_artifact_meta={
                    "candidate_key": "A|patched",
                    "content_hash": "hash-final",
                    "artifact_path": "artifacts/final.txt",
                },
                final_manuscript="patched manuscript",
                previous_attempt={},
            ),
            next_ep=1,
            round_num=0,
            round_ctx=_make_round_ctx(),
            director_result={
                "selection_reason": "pre-fix selection",
                "verdict_reason": "pre-fix verdict",
                "fix_scope": "inplace",
                "fix_pack": {
                    "patch_targets": ["name_anchor"],
                    "must_fix": ["rename family anchor"],
                    "do_not_regress": ["ending hook"],
                    "success_condition": "anchor renamed",
                    "target_kind": "entity_ref",
                    "subtype": "고유명사",
                    "provenance": "director_authored",
                },
            },
            trace_director_result={
                "selection_reason": "post-fix selection",
                "verdict_reason": "post-fix verdict",
                "director_verdict": "PASS",
                "final_verdict": "PASS",
                "gate_basis": "patch_reaudit_pass",
                "repair_scope": "inplace",
                "authoritative_fix_scope": "inplace",
            },
            reason="fallback",
            is_patch=True,
            trace_patch_trace={"patch_targets": ["name_anchor"], "target_kind": "entity_ref"},
        )

        assert payload.session_selection_reason == "post-fix selection"
        assert payload.session_verdict_reason == "post-fix verdict"
        assert payload.session_fix_pack["target_kind"] == "entity_ref"
        assert payload.session_fix_pack["patch_targets"] == ["name_anchor"]
        assert payload.session_gate_semantics["repair_contract"]["subtype"] == "고유명사"
        assert payload.session_gate_semantics["repair_contract"]["provenance"] == "director_authored"

    def test_append_pass_episode_log_delegates_to_stage4_episode_logging(self):
        from modules.core import stage4_episode_logging as s4_episode_logging
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        ctx = _make_ctx()
        ctx.current_project.metrics_session_id = "sess-pass-log"
        ir = Stage4InterviewRound(ctx)
        ir._append_episode_log = MagicMock()
        chief_writer = MagicMock()
        chief_writer.model_tier = "writer-model"
        expected = {"attempt_key": "s4:ep1:arc1:a1"}
        session_gate_semantics = {
            "director_verdict": "PASS",
            "gate_basis": "patch_reaudit_pass",
            "repair_scope": "inplace",
        }
        session_fix_pack = {
            "patch_targets": ["name_anchor"],
            "target_kind": "entity_ref",
        }

        with patch.object(s4_episode_logging, "build_pass_episode_log_payload", return_value=expected) as mock_builder:
            ir._append_pass_episode_log(
                ep_num=1,
                round_num=0,
                round_ctx=_make_round_ctx(),
                chief_writer=chief_writer,
                director_result={},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics=session_gate_semantics,
                    session_fix_pack=session_fix_pack,
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            )

        ir._append_episode_log.assert_called_once()
        append_kwargs = ir._append_episode_log.call_args.kwargs
        assert append_kwargs["attempt_key"] == "s4:ep1:arc1:a1"
        assert append_kwargs["selection_reason"] == "selection"
        assert append_kwargs["verdict_reason"] == "verdict"
        assert append_kwargs["gate_semantics"] == session_gate_semantics
        assert append_kwargs["fix_pack"] == session_fix_pack
        assert append_kwargs["runtime_advisory"] == "runtime digest"
        assert append_kwargs["retry_directives"] == "retry directives"
        assert append_kwargs["carryover_contracts"] is None
        mock_builder.assert_called_once()
        normalized_request = mock_builder.call_args.kwargs["request"]
        assert normalized_request.model_tier == "writer-model"
        assert normalized_request.session_id == "sess-pass-log"
        assert normalized_request.session_runtime_advisory == "runtime digest"
        assert normalized_request.selection_artifact_meta["candidate_key"] == "A"

    def test_build_pass_episode_log_parts_collects_base_provenance_and_artifact_sections(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        ctx = _make_ctx()
        ctx.current_project.id = "proj-1"
        chief_writer = MagicMock()
        chief_writer.model_tier = "writer-model"

        parts = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_parts,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=chief_writer,
                director_result={"selected": "A"},
                trace_director_result={"verdict_reason": "trace verdict"},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
            session_id="sess-pass-log",
        )

        assert parts.base_fields["final_verdict"] == "PASS_WITH_FIX"
        assert parts.base_fields["model"] == "writer-model"
        assert parts.feedback_provenance["director_feedback"] == "trace verdict"
        assert parts.feedback_provenance["runtime_advisory"] == "runtime digest"
        assert parts.artifact_fields["candidate_key"] == "stage4|A"
        assert parts.artifact_fields["selection_candidate_key"] == "A"

    def test_assemble_pass_episode_log_payload_merges_base_provenance_and_artifacts(self):
        from modules.core import stage4_episode_logging as s4_episode_logging

        payload = s4_episode_logging.assemble_pass_episode_log_payload(
            base_fields={"ep_num": 1, "final_verdict": "PASS"},
            feedback_provenance={"director_feedback": "trace verdict"},
            artifact_fields={"candidate_key": "stage4|A", "artifact_path": "artifact.json"},
        )

        assert payload == {
            "ep_num": 1,
            "final_verdict": "PASS",
            "feedback_provenance": {"director_feedback": "trace verdict"},
            "candidate_key": "stage4|A",
            "artifact_path": "artifact.json",
        }

    def test_build_pass_feedback_provenance_prefers_trace_reason(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        provenance = _call_pass_log_builder(
            s4_episode_logging.build_pass_feedback_provenance,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=MagicMock(),
                director_result={},
                trace_director_result={"verdict_reason": "trace verdict"},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert provenance == {
            "director_feedback": "trace verdict",
            "runtime_advisory": "runtime digest",
            "retry_directives": "retry directives",
        }

    def test_build_pass_episode_log_base_fields_preserves_core_round_metadata(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        chief_writer = MagicMock()
        chief_writer.model_tier = "writer-model"

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_base_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=chief_writer,
                director_result={"selected": "A"},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "ep_num": 1,
            "round_num": 0,
            "director_result": {"selected": "A"},
            "initial_verdict": "PASS",
            "initial_score": 91,
            "final_verdict": "PASS_WITH_FIX",
            "final_score": 98,
            "is_patch": True,
            "patch_fallback": False,
            "tot_used": False,
            "mad_used": True,
            "asp_used": True,
            "model": "writer-model",
            "reject_bucket": "",
            "validation_warnings": ["warn-a"],
            "final_warnings": ["final-warn"],
            "patch_trace": {"mode": "patch"},
        }

    def test_build_pass_episode_log_round_fields_preserves_verdict_scores_and_selection(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_round_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=MagicMock(),
                director_result={"selected": "A"},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "ep_num": 1,
            "round_num": 0,
            "director_result": {"selected": "A"},
            "initial_verdict": "PASS",
            "initial_score": 91,
            "final_verdict": "PASS_WITH_FIX",
            "final_score": 98,
        }

    def test_build_pass_episode_log_status_fields_preserves_usage_flags_and_model(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        chief_writer = MagicMock()
        chief_writer.model_tier = "writer-model"

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_status_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=chief_writer,
                director_result={"selected": "A"},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "is_patch": True,
            "patch_fallback": False,
            "tot_used": False,
            "mad_used": True,
            "asp_used": True,
            "model": "writer-model",
            "reject_bucket": "",
            "validation_warnings": ["warn-a"],
            "final_warnings": ["final-warn"],
            "patch_trace": {"mode": "patch"},
        }

    def test_build_pass_episode_log_usage_fields_preserves_usage_flags_and_model(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        chief_writer = MagicMock()
        chief_writer.model_tier = "writer-model"

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_usage_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=chief_writer,
                director_result={"selected": "A"},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "is_patch": True,
            "patch_fallback": False,
            "tot_used": False,
            "mad_used": True,
            "asp_used": True,
            "model": "writer-model",
        }

    def test_build_pass_episode_log_usage_flag_fields_preserves_patch_and_usage_flags(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        chief_writer = MagicMock()
        chief_writer.model_tier = "writer-model"

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_usage_flag_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=chief_writer,
                director_result={"selected": "A"},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "is_patch": True,
            "patch_fallback": False,
            "tot_used": False,
            "mad_used": True,
            "asp_used": True,
        }

    def test_build_pass_episode_log_model_field_reads_model_tier(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        chief_writer = MagicMock()
        chief_writer.model_tier = "writer-model"

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_model_field,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=chief_writer,
                director_result={"selected": "A"},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {"model": "writer-model"}

    def test_build_pass_episode_log_warning_fields_preserves_warning_bundle(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_warning_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=MagicMock(),
                director_result={"selected": "A"},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "reject_bucket": "",
            "validation_warnings": ["warn-a"],
            "final_warnings": ["final-warn"],
            "patch_trace": {"mode": "patch"},
        }

    def test_build_pass_episode_log_artifact_fields_includes_attempt_key_and_selection_meta(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_artifact_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=MagicMock(),
                director_result={},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "arc_num": 1,
            "attempt_key": "s4:ep1:arc1:a1",
            "candidate_key": "stage4|A",
            "content_hash": "hash-123",
            "artifact_path": "artifact.json",
            "selection_candidate_key": "A",
            "selection_content_hash": "sel-hash",
            "selection_artifact_path": "selection.json",
        }

    def test_build_pass_episode_log_artifact_core_fields_includes_attempt_key_and_logged_artifact(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_artifact_core_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=MagicMock(),
                director_result={},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "arc_num": 1,
            "attempt_key": "s4:ep1:arc1:a1",
            "candidate_key": "stage4|A",
            "content_hash": "hash-123",
            "artifact_path": "artifact.json",
        }

    def test_build_pass_episode_log_attempt_fields_includes_arc_and_attempt_key(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_attempt_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=MagicMock(),
                director_result={},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "arc_num": 1,
            "attempt_key": "s4:ep1:arc1:a1",
        }

    def test_build_pass_episode_log_logged_artifact_fields_reads_logged_artifact_meta(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_logged_artifact_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=MagicMock(),
                director_result={},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "candidate_key": "stage4|A",
            "content_hash": "hash-123",
            "artifact_path": "artifact.json",
        }

    def test_build_pass_episode_log_selection_artifact_fields_reads_selection_meta(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        payload = _call_pass_log_builder(
            s4_episode_logging.build_pass_episode_log_selection_artifact_fields,
            _TestPassEpisodeLogRequest(
                ep_num=1,
                round_num=0,
                chief_writer=MagicMock(),
                director_result={},
                trace_director_result={},
                director_feedback="raw feedback",
                initial_verdict="PASS",
                initial_score=91,
                final_verdict="PASS_WITH_FIX",
                final_score=98,
                is_patch=True,
                is_patch_fallback=False,
                tot_used=False,
                mad_used=True,
                validation_warnings=["warn-a"],
                final_warnings=["final-warn"],
                patch_trace={"mode": "patch"},
                logging_payload=_PassResultLoggingPayload(
                    log_artifact_meta={
                        "candidate_key": "stage4|A",
                        "content_hash": "hash-123",
                        "artifact_path": "artifact.json",
                    },
                    session_selection_reason="selection",
                    session_verdict_reason="verdict",
                    session_runtime_advisory="runtime digest",
                    session_retry_directives="retry directives",
                    session_gate_semantics={},
                ),
                selection_artifact_meta={
                    "candidate_key": "A",
                    "content_hash": "sel-hash",
                    "artifact_path": "selection.json",
                },
                arc_num=1,
                asp_manuscript="asp",
            ),
        )

        assert payload == {
            "selection_candidate_key": "A",
            "selection_content_hash": "sel-hash",
            "selection_artifact_path": "selection.json",
        }

    def test_append_pass_round_logs_delegates_episode_log_and_round_outcome(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        chief_writer = MagicMock()
        ir._append_pass_episode_log = MagicMock()
        ir._log_round_outcome = MagicMock()

        ir._append_pass_round_logs(
            next_ep=1,
            round_num=0,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result={},
            trace_director_result={"verdict_reason": "trace verdict"},
            director_feedback="raw feedback",
            initial_verdict="PASS",
            initial_score=91,
            final_verdict="PASS_WITH_FIX",
            final_score=98,
            selection_artifact_meta={
                "candidate_key": "A",
                "content_hash": "sel-hash",
                "artifact_path": "selection.json",
            },
            validation_warnings=["warn-a"],
            is_patch=True,
            is_patch_fallback=False,
            trace_patch_trace={"mode": "patch"},
            tot_used=False,
            mad_used=True,
            asp_manuscript="asp",
            logging_payload=_PassResultLoggingPayload(
                log_artifact_meta={
                    "candidate_key": "stage4|A",
                    "content_hash": "hash-123",
                    "artifact_path": "artifact.json",
                },
                session_selection_reason="selection",
                session_verdict_reason="verdict",
                session_runtime_advisory="runtime digest",
                session_retry_directives="retry directives",
                session_gate_semantics={},
            ),
            arc_num=1,
            final_warnings=["final-warn"],
        )

        ir._append_pass_episode_log.assert_called_once()
        ir._log_round_outcome.assert_called_once()
        outcome_kwargs = ir._log_round_outcome.call_args.kwargs
        assert outcome_kwargs["final_warning_count"] == 1
        assert outcome_kwargs["artifact_path"] == "artifact.json"

    def test_log_pass_session_decision_prefers_trace_fields(self):
        from modules.core.stage4_interview_round import _PassResultLoggingPayload

        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._build_fix_pack_payload = MagicMock(return_value={"must_fix": ["anchor"]})
        ir._log_session_decision = MagicMock()
        ir._last_retry_budget_axes = {"repair": "patch_revision"}

        ir._log_pass_session_decision(
            next_ep=1,
            round_num=0,
            arc_num=1,
            director_result={
                "fix_scope": "partial",
                "open_review": "director open review",
                "action_items": ["director item"],
                "firewall_triggered": False,
                "firewall_reason": "",
            },
            trace_director_result={
                "verdict_reason": "trace verdict",
                "fix_scope": "rewrite",
                "open_review": "trace open review",
                "action_items": ["trace item"],
                "firewall_triggered": True,
                "firewall_reason": "trace firewall",
            },
            final_verdict="PASS_WITH_FIX",
            final_score=98,
            selected="A",
            reason="fallback reason",
            error_category="LOGIC_ERROR",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A"},
            initial_verdict="PASS",
            initial_score=91,
            logging_payload=_PassResultLoggingPayload(
                log_artifact_meta={
                    "candidate_key": "stage4|A",
                    "content_hash": "hash-123",
                    "artifact_path": "artifact.json",
                },
                session_selection_reason="selection",
                session_verdict_reason="verdict",
                session_runtime_advisory="runtime digest",
                session_retry_directives="retry directives",
                session_gate_semantics={
                    "director_verdict": "PASS_WITH_FIX",
                    "gate_basis": "trace_gate",
                    "repair_scope": "rewrite",
                },
            ),
        )

        ir._log_session_decision.assert_called_once()
        kwargs = ir._log_session_decision.call_args.kwargs
        assert kwargs["reason"] == "trace verdict"
        assert kwargs["fix_scope"] == "rewrite"
        assert kwargs["open_review"] == "trace open review"
        assert kwargs["action_items"] == ["trace item"]
        assert kwargs["firewall_triggered"] is True
        assert kwargs["firewall_reason"] == "trace firewall"
        assert kwargs["retry_budget_axes"] == {"repair": "patch_revision"}
        assert kwargs["fix_pack"] == {"must_fix": ["anchor"]}

    def test_log_reject_session_decision_prefers_trace_fields(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._build_fix_pack_payload = MagicMock(return_value={"must_fix": ["anchor"]})
        ir._log_session_decision = MagicMock()
        ir._last_retry_budget_axes = {"repair": "patch_revision"}

        ir.reject_runtime._log_reject_session_decision(
            next_ep=1,
            round_num=0,
            arc_num=1,
            director_result={
                "fix_scope": "full",
                "open_review": "director open review",
                "action_items": ["director item"],
                "firewall_triggered": False,
                "firewall_reason": "",
            },
            trace_director_result={
                "verdict_reason": "trace reject verdict",
                "fix_scope": "partial",
                "open_review": "trace open review",
                "action_items": ["trace item"],
                "firewall_triggered": True,
                "firewall_reason": "trace firewall",
            },
            final_verdict="REJECT",
            final_score=44,
            selected="A",
            reason="fallback reason",
            error_category="LOGIC_ERROR",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A"},
            initial_verdict="REJECT",
            initial_score=40,
            reject_logging=_RejectLoggingPayload(
                reject_bucket="continuity",
                reject_artifact_meta={
                    "candidate_key": "stage4|reject",
                    "content_hash": "hash-r",
                    "artifact_path": "reject.json",
                },
                session_selection_reason="selection",
                session_verdict_reason="verdict",
                session_runtime_advisory="runtime digest",
                session_retry_directives="retry directives",
                session_gate_semantics={
                    "director_verdict": "REJECT",
                    "gate_basis": "continuity",
                    "repair_scope": "partial",
                },
                feedback_provenance={
                    "director_feedback": "director said no",
                    "runtime_advisory": "runtime digest",
                    "retry_directives": "retry directives",
                },
            ),
        )

        ir._log_session_decision.assert_called_once()
        kwargs = ir._log_session_decision.call_args.kwargs
        assert kwargs["reason"] == "trace reject verdict"
        assert kwargs["fix_scope"] == "partial"
        assert kwargs["open_review"] == "trace open review"
        assert kwargs["action_items"] == ["trace item"]
        assert kwargs["artifact_meta"]["candidate_key"] == "stage4|reject"
        assert kwargs["selection_reason"] == "selection"
        assert kwargs["verdict_reason"] == "verdict"
        assert kwargs["director_verdict"] == "REJECT"
        assert kwargs["gate_basis"] == "continuity"
        assert kwargs["repair_scope"] == "partial"
        assert kwargs["retry_budget_axes"] == {"repair": "patch_revision"}
        assert kwargs["fix_pack"] == {"must_fix": ["anchor"]}
        assert kwargs["runtime_advisory"] == "runtime digest"
        assert kwargs["retry_directives"] == "retry directives"

    def test_log_reject_session_decision_prefers_final_reject_scope_and_fix_pack(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._build_fix_pack_payload = MagicMock(side_effect=lambda source: dict(source.get("fix_pack") or {}))
        ir._log_session_decision = MagicMock()
        ir._last_retry_budget_axes = {"repair": "rewrite_regenerate"}

        ir.reject_runtime._log_reject_session_decision(
            next_ep=1,
            round_num=0,
            arc_num=1,
            director_result={
                "fix_scope": "partial",
                "fix_pack": {"target_kind": "scene_model"},
                "open_review": "director open review",
                "action_items": ["director item"],
                "firewall_triggered": False,
                "firewall_reason": "",
            },
            trace_director_result={
                "fix_scope": "partial",
                "fix_pack": {"target_kind": "scene_model"},
                "open_review": "trace open review",
                "action_items": ["trace item"],
                "firewall_triggered": False,
                "firewall_reason": "",
            },
            final_verdict="REJECT",
            final_score=44,
            selected="A",
            reason="fallback reason",
            error_category="LOGIC_ERROR",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A"},
            initial_verdict="REJECT",
            initial_score=40,
            reject_logging=_RejectLoggingPayload(
                reject_bucket="post_select_conflict",
                reject_artifact_meta={
                    "candidate_key": "stage4|reject",
                    "content_hash": "hash-r",
                    "artifact_path": "reject.json",
                },
                session_selection_reason="selection",
                session_verdict_reason="verdict",
                session_runtime_advisory="runtime digest",
                session_retry_directives="retry directives",
                session_gate_semantics={
                    "director_verdict": "REJECT",
                    "gate_basis": "continuity_firewall",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "partial",
                    "fix_pack": {},
                    "repair_contract": {
                        "subtype": "수학",
                        "fix_scope": "full",
                        "repair_scope": "partial",
                        "authoritative_fix_scope": "partial",
                    },
                    "scope_authority": {
                        "fix_scope": "full",
                        "repair_scope": "partial",
                        "authoritative_fix_scope": "partial",
                        "widened": True,
                    },
                },
                feedback_provenance={
                    "director_feedback": "director said no",
                    "runtime_advisory": "runtime digest",
                    "retry_directives": "retry directives",
                },
            ),
        )

        kwargs = ir._log_session_decision.call_args.kwargs
        assert kwargs["fix_scope"] == "full"
        assert kwargs["repair_scope"] == "partial"
        assert kwargs["fix_pack"] == {}

    def test_finalize_reject_result_logs_episode_with_final_reject_scope_metadata(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._append_episode_log = MagicMock()
        ir._log_round_outcome = MagicMock()
        ir.reject_runtime._sync_reject_result_selection_rationale = MagicMock()
        ir.reject_runtime._log_reject_session_decision = MagicMock()

        reject_result = SimpleNamespace(
            previous_attempt={
                "attempt_key": "attempt-1",
                "candidate_key": "stage4|reject",
                "content_hash": "hash-r",
                "artifact_path": "reject.json",
                "selection_reason": "selection",
                "verdict_reason": "verdict",
                "fix_scope": "full",
                "authoritative_fix_scope": "partial",
                "repair_scope": "partial",
                "fix_pack": {},
                "repair_contract": {
                    "subtype": "수학",
                    "fix_scope": "full",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "partial",
                },
                "scope_authority": {
                    "fix_scope": "full",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "partial",
                    "widened": True,
                },
                "scope_origin": {
                    "fix_scope": "runtime_widened",
                    "authoritative_fix_scope": "director_authoritative",
                    "repair_scope": "runtime_lane",
                },
                "firewall_triggered": True,
                "firewall_reason": "trace firewall",
                "reject_bucket": "post_select_conflict",
                "runtime_advisory": "runtime digest",
                "retry_directives": "retry later",
            },
            attempt_artifact_meta={
                "candidate_key": "stage4|reject",
                "content_hash": "hash-r",
                "artifact_path": "reject.json",
            },
        )

        ir.reject_runtime._build_reject_logging_payload = MagicMock(
            return_value=_RejectLoggingPayload(
                reject_bucket="post_select_conflict",
                reject_artifact_meta={
                    "candidate_key": "stage4|reject",
                    "content_hash": "hash-r",
                    "artifact_path": "reject.json",
                },
                session_selection_reason="selection",
                session_verdict_reason="verdict",
                session_runtime_advisory="runtime digest",
                session_retry_directives="retry later",
                session_gate_semantics={
                    "director_verdict": "REJECT",
                    "gate_basis": "continuity_firewall",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "partial",
                    "fix_pack": {},
                    "repair_contract": {
                        "subtype": "수학",
                        "fix_scope": "full",
                        "repair_scope": "partial",
                        "authoritative_fix_scope": "partial",
                    },
                    "scope_authority": {
                        "fix_scope": "full",
                        "repair_scope": "partial",
                        "authoritative_fix_scope": "partial",
                        "widened": True,
                    },
                    "scope_origin": {
                        "fix_scope": "runtime_widened",
                        "authoritative_fix_scope": "director_authoritative",
                        "repair_scope": "runtime_lane",
                    },
                },
                feedback_provenance={
                    "director_feedback": "director said no",
                    "runtime_advisory": "runtime digest",
                    "retry_directives": "retry later",
                },
            )
        )

        ir.reject_runtime.finalize_reject_result(
            reject_result=reject_result,
            next_ep=1,
            round_num=0,
            round_ctx=_make_round_ctx(),
            chief_writer=MagicMock(model_tier="gemini-2.5-pro"),
            director_result={
                "selection_reason": "best candidate",
                "verdict_reason": "reject reason",
                "fix_scope": "partial",
                "fix_pack": {"target_kind": "scene_model"},
                "open_review": "director review",
                "action_items": ["tighten ending"],
            },
            trace_director_result={
                "selection_reason": "trace selection",
                "verdict_reason": "trace reason",
                "fix_scope": "partial",
                "fix_pack": {"target_kind": "scene_model"},
                "open_review": "trace review",
                "action_items": ["trace item"],
            },
            initial_verdict="REJECT",
            initial_score=71,
            final_verdict="REJECT",
            final_score=44,
            selected="A",
            reason="fallback reason",
            error_category="LOGIC_ERROR",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A", "content_hash": "sel-hash", "artifact_path": "sel.txt"},
            validation_warnings=[],
            is_patch=False,
            is_patch_fallback=False,
            trace_patch_trace={},
            tot_used=False,
            mad_used=False,
            asp_manuscript="",
        )

        kwargs = ir._append_episode_log.call_args.kwargs
        assert kwargs["director_result"]["fix_scope"] == "full"
        assert kwargs["director_result"]["fix_pack"] == {}
        assert kwargs["director_result"]["scope_authority"]["fix_scope"] == "full"
        assert kwargs["director_result"]["authoritative_fix_scope"] == "partial"

    def test_build_round_outcome_trace_payload_prefers_trace_meta_and_collects_warnings(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._collect_validation_warning_lines = MagicMock(return_value=["warn-a", "warn-b"])

        payload = ir._build_round_outcome_trace_payload(
            trace_meta={
                "director_result": {"verdict": "PASS_WITH_FIX", "trace": True},
                "final_verdict": "PASS_WITH_FIX",
                "final_score": 88,
                "patch_trace": {"mode": "patch"},
            },
            director_result={"verdict": "PASS"},
            initial_verdict="PASS",
            initial_score=81,
            validation_results=[_validation_result()],
            is_patch=False,
        )

        assert payload.trace_director_result == {"verdict": "PASS_WITH_FIX", "trace": True}
        assert payload.final_verdict == "PASS_WITH_FIX"
        assert payload.final_score == 88
        assert payload.trace_patch_trace == {"mode": "patch"}
        assert payload.is_patch is True
        assert payload.validation_warnings == ["warn-a", "warn-b"]
        ir._collect_validation_warning_lines.assert_called_once_with([_validation_result()], limit=20)

    def test_build_reject_logging_payload_prefers_trace_reason_and_previous_attempt_metadata(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._build_gate_semantics_payload = MagicMock(
            return_value={
                "director_verdict": "REJECT",
                "gate_basis": "continuity",
                "repair_scope": "partial",
            }
        )
        reject_result = MagicMock()
        reject_result.previous_attempt = {
            "reject_bucket": "continuity",
            "runtime_advisory": "runtime digest",
            "retry_directives": "retry later",
            "director_feedback_text": "director said no",
            "scope_origin": {
                "fix_scope": "post_select_conflict_override",
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
            "repair_contract": {"subtype": "opening_action_continuity", "fix_scope": "full"},
            "conflict_contract": {
                "contract_type": "post_select_conflict",
                "conflicts": [{"conflict_type": "continuity"}, {"conflict_type": "history"}],
            },
            "reuse_contract": {"mode": "best_manuscript_baseline"},
        }
        reject_result.attempt_artifact_meta = {
            "candidate_key": "stage4|reject",
            "content_hash": "hash-r",
            "artifact_path": "reject.json",
        }

        payload = ir.reject_runtime._build_reject_logging_payload(
            reject_result=reject_result,
            director_result={"selection_reason": "initial selection"},
            trace_director_result={
                "selection_reason": "re-audit selection",
                "verdict_reason": "trace reject reason",
            },
            reason="fallback reason",
        )

        assert payload.reject_bucket == "continuity"
        assert payload.reject_artifact_meta["candidate_key"] == "stage4|reject"
        assert payload.session_selection_reason == "re-audit selection"
        assert payload.session_verdict_reason == "trace reject reason"
        assert payload.session_runtime_advisory == "runtime digest"
        assert payload.session_retry_directives == "retry later"
        assert payload.feedback_provenance == {
            "director_feedback": "director said no",
            "runtime_advisory": "runtime digest",
            "retry_directives": "retry later",
        }
        assert payload.session_gate_semantics["gate_basis"] == "continuity"
        assert payload.session_gate_semantics["scope_origin"]["fix_scope"] == "post_select_conflict_override"
        assert payload.session_gate_semantics["repair_contract"]["subtype"] == "opening_action_continuity"
        assert payload.session_gate_semantics["conflict_resolution_linkage"]["conflict_count"] == 2
        assert payload.session_gate_semantics["reuse_contract"]["mode"] == "best_manuscript_baseline"

    def test_build_reject_logging_payload_adds_numeric_carryover_operator_notes(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._build_gate_semantics_payload = MagicMock(
            return_value={
                "director_verdict": "REJECT",
                "gate_basis": "continuity",
                "repair_scope": "full",
            }
        )
        reject_result = MagicMock()
        reject_result.previous_attempt = {
            "reject_bucket": "quality_issue",
            "runtime_advisory": "runtime digest",
            "retry_directives": "retry later",
            "director_feedback_text": "director said no",
            "contradiction_types": ["numeric_carryover_authority"],
            "repair_contract": {
                "subtype": "numeric_carryover_authority",
                "fix_scope": "full",
                "authoritative_fix_scope": "partial",
                "provenance": "runtime_synthesized",
            },
            "scope_authority": {
                "fix_scope": "full",
                "authoritative_fix_scope": "partial",
                "widened": True,
            },
        }
        reject_result.attempt_artifact_meta = {}

        payload = ir.reject_runtime._build_reject_logging_payload(
            reject_result=reject_result,
            director_result={"selection_reason": "initial selection"},
            trace_director_result={},
            reason="fallback reason",
        )

        assert "[Numeric carryover authority]" in payload.session_runtime_advisory
        assert "FactLedger carryover baseline remains the canonical numeric source" in payload.session_runtime_advisory
        assert "Scope: runtime=full, authoritative=partial." in payload.session_runtime_advisory
        assert "Provenance: runtime_synthesized." in payload.session_runtime_advisory
        assert "[Numeric carryover authority]" in payload.session_retry_directives
        assert (
            "do not promote blueprint/manuscript future or liquidatable asset claims"
            in payload.session_retry_directives
        )
        assert payload.feedback_provenance["runtime_advisory"] == payload.session_runtime_advisory
        assert payload.feedback_provenance["retry_directives"] == payload.session_retry_directives

    def test_build_reject_logging_payload_adds_scope_authority_operator_notes(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._build_gate_semantics_payload = MagicMock(
            return_value={
                "director_verdict": "REJECT",
                "gate_basis": "continuity",
                "repair_scope": "full",
            }
        )
        reject_result = MagicMock()
        reject_result.previous_attempt = {
            "reject_bucket": "quality_issue",
            "runtime_advisory": "runtime digest",
            "retry_directives": "retry later",
            "director_feedback_text": "director said no",
            "repair_contract": {
                "subtype": "opening_action_continuity",
                "fix_scope": "full",
                "authoritative_fix_scope": "inplace",
                "provenance": "runtime_synthesized",
            },
            "scope_authority": {
                "fix_scope": "full",
                "authoritative_fix_scope": "inplace",
                "widened": True,
            },
            "scope_origin": {
                "fix_scope": "runtime_widened",
            },
        }
        reject_result.attempt_artifact_meta = {}

        payload = ir.reject_runtime._build_reject_logging_payload(
            reject_result=reject_result,
            director_result={"selection_reason": "initial selection"},
            trace_director_result={},
            reason="fallback reason",
        )

        assert "[Repair scope authority]" in payload.session_runtime_advisory
        assert "runtime scope widened from authoritative=inplace to runtime=full" in payload.session_runtime_advisory
        assert "origin=runtime_widened" in payload.session_runtime_advisory
        assert "provenance=runtime_synthesized" in payload.session_runtime_advisory
        assert "[Repair scope authority]" in payload.session_retry_directives
        assert "Preserve authoritative_fix_scope=inplace" in payload.session_retry_directives
        assert payload.feedback_provenance["runtime_advisory"] == payload.session_runtime_advisory
        assert payload.feedback_provenance["retry_directives"] == payload.session_retry_directives

    def test_build_reject_logging_payload_synthesizes_explicit_non_local_fix_contract(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        reject_result = MagicMock()
        reject_result.previous_attempt = {
            "reject_bucket": "quality_issue",
            "runtime_advisory": "runtime digest",
            "retry_directives": "retry later",
            "director_feedback_text": "director said no",
            "gate_basis": "strong_advisory_escalation_non_local_fix",
            "repair_scope": "partial",
            "fix_scope": "partial",
            "authoritative_fix_scope": "inplace",
            "fix_pack": {},
            "repair_contract": {
                "fix_scope": "partial",
                "repair_scope": "partial",
                "authoritative_fix_scope": "inplace",
            },
            "scope_authority": {
                "fix_scope": "partial",
                "repair_scope": "partial",
                "authoritative_fix_scope": "inplace",
                "widened": True,
            },
            "strong_advisory_escalation": {
                "triggered_by": ["npc_drift"],
                "local_fix_contract": {
                    "ready": False,
                    "reason": "missing_fix_pack",
                    "fix_scope": "inplace",
                },
            },
        }
        reject_result.attempt_artifact_meta = {}

        payload = ir.reject_runtime._build_reject_logging_payload(
            reject_result=reject_result,
            director_result={"selection_reason": "initial selection"},
            trace_director_result={},
            reason="fallback reason",
        )

        fix_pack = payload.session_gate_semantics["fix_pack"]
        assert fix_pack["target_kind"] == "scene_model"
        assert fix_pack["provenance"] == "runtime_synthesized"
        assert fix_pack["patch_targets"] == ["scene-model rewrite boundary"]
        assert "broader rewrite contract" in fix_pack["evidence_summary"]
        repair_contract = payload.session_gate_semantics["repair_contract"]
        assert repair_contract["provenance"] == "runtime_synthesized"
        assert repair_contract["target_kind"] == "scene_model"
        assert payload.session_gate_semantics["fix_pack_origin"] == {
            "provenance": "runtime_synthesized",
            "provenance_sources": ["strong_advisory_non_local_fix", "npc_drift"],
            "routing_contract": "runtime_generated_requires_rewrite",
        }

    def test_finalize_reject_result_synthesizes_explicit_non_local_fix_contract_in_episode_log(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._append_episode_log = MagicMock()
        ir._log_round_outcome = MagicMock()
        ir.reject_runtime._sync_reject_result_selection_rationale = MagicMock()
        ir.reject_runtime._log_reject_session_decision = MagicMock()

        reject_result = SimpleNamespace(
            previous_attempt={
                "attempt_key": "attempt-1",
                "candidate_key": "stage4|reject",
                "content_hash": "hash-r",
                "artifact_path": "reject.json",
                "selection_reason": "selection",
                "verdict_reason": "verdict",
                "gate_basis": "strong_advisory_escalation_non_local_fix",
                "fix_scope": "partial",
                "authoritative_fix_scope": "inplace",
                "repair_scope": "partial",
                "fix_pack": {},
                "repair_contract": {
                    "fix_scope": "partial",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "inplace",
                },
                "scope_authority": {
                    "fix_scope": "partial",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "inplace",
                    "widened": True,
                },
                "strong_advisory_escalation": {
                    "triggered_by": ["npc_drift"],
                    "local_fix_contract": {
                        "ready": False,
                        "reason": "missing_fix_pack",
                        "fix_scope": "inplace",
                    },
                },
                "runtime_advisory": "runtime digest",
                "retry_directives": "retry later",
                "reject_bucket": "quality_issue",
            },
            attempt_artifact_meta={
                "candidate_key": "stage4|reject",
                "content_hash": "hash-r",
                "artifact_path": "reject.json",
            },
        )

        ir.reject_runtime.finalize_reject_result(
            reject_result=reject_result,
            next_ep=1,
            round_num=0,
            round_ctx=_make_round_ctx(),
            chief_writer=MagicMock(model_tier="gemini-2.5-pro"),
            director_result={
                "selection_reason": "best candidate",
                "verdict_reason": "reject reason",
                "fix_scope": "partial",
                "gate_basis": "strong_advisory_escalation_non_local_fix",
                "repair_scope": "partial",
                "authoritative_fix_scope": "inplace",
                "strong_advisory_escalation": {
                    "triggered_by": ["npc_drift"],
                    "local_fix_contract": {
                        "ready": False,
                        "reason": "missing_fix_pack",
                        "fix_scope": "inplace",
                    },
                },
                "open_review": "director review",
                "action_items": ["tighten ending"],
            },
            trace_director_result={},
            initial_verdict="REJECT",
            initial_score=98,
            final_verdict="REJECT",
            final_score=98,
            selected="A",
            reason="fallback reason",
            error_category="QUALITY_ISSUE",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A"},
            validation_warnings=[],
            is_patch=True,
            is_patch_fallback=False,
            trace_patch_trace={},
            tot_used=False,
            mad_used=False,
            asp_manuscript="",
        )

        sink_source = ir._append_episode_log.call_args.kwargs["director_result"]
        assert sink_source["fix_pack"]["target_kind"] == "scene_model"
        assert sink_source["fix_pack"]["provenance"] == "runtime_synthesized"
        assert sink_source["fix_pack_reason"] == "scene_model_target"
        assert sink_source["repair_contract"]["provenance"] == "runtime_synthesized"
        assert sink_source["repair_contract"]["target_kind"] == "scene_model"
        assert sink_source["fix_pack_origin"]["routing_contract"] == "runtime_generated_requires_rewrite"

    def test_finalize_round_outcome_routes_reject_branch_with_trace_meta(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        chief_writer = MagicMock()
        reject_result = MagicMock(name="reject_result")
        finalized = {"status": "reject"}
        ir._collect_validation_warning_lines = MagicMock(return_value=["warn"])
        ir._handle_reject = MagicMock(return_value=reject_result)
        ir._finalize_reject_result = MagicMock(return_value=finalized)

        result = ir._finalize_round_outcome(
            pass_result=None,
            next_ep=1,
            round_num=0,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result={"verdict": "REJECT"},
            director_feedback="feedback",
            previous_attempt={"attempt": 1},
            trace_meta={
                "director_result": {"verdict": "REJECT", "trace": True},
                "final_verdict": "",
                "final_score": 44,
                "patch_trace": {"mode": "patch"},
            },
            candidates=[_candidate()],
            validation_results=[_validation_result()],
            initial_verdict="REJECT",
            initial_score=40,
            selected="A",
            reason="conflict",
            error_category="continuity",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A"},
            is_patch=False,
            is_patch_fallback=True,
            prev_score=33,
            prev_manuscript="prev",
            tot_used=True,
            mad_used=False,
            asp_manuscript="asp",
        )

        assert result == finalized
        ir._handle_reject.assert_called_once()
        reject_kwargs = ir._handle_reject.call_args.kwargs
        assert reject_kwargs["director_result"] == {"verdict": "REJECT", "trace": True}
        assert reject_kwargs["score"] == 44
        assert reject_kwargs["is_patch"] is True
        ir._finalize_reject_result.assert_called_once()
        finalize_kwargs = ir._finalize_reject_result.call_args.kwargs
        assert finalize_kwargs["reject_result"] is reject_result
        assert finalize_kwargs["final_verdict"] == "REJECT"
        assert finalize_kwargs["final_score"] == 44
        assert finalize_kwargs["validation_warnings"] == ["warn"]
        assert finalize_kwargs["trace_patch_trace"] == {"mode": "patch"}

    def test_finalize_round_reject_path_routes_handle_reject_and_finalize(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        chief_writer = MagicMock()
        reject_result = MagicMock(name="reject_result")
        finalized = {"status": "reject"}
        ir._handle_reject = MagicMock(return_value=reject_result)
        ir._finalize_reject_result = MagicMock(return_value=finalized)

        result = ir._finalize_round_reject_path(
            next_ep=1,
            round_num=0,
            round_ctx=round_ctx,
            chief_writer=chief_writer,
            director_result={"verdict": "REJECT"},
            director_feedback="feedback",
            previous_attempt={"attempt": 1},
            trace_payload=_RoundOutcomeTracePayload(
                trace_director_result={"verdict": "REJECT", "trace": True},
                final_verdict="",
                final_score=44,
                trace_patch_trace={"mode": "patch"},
                is_patch=True,
                validation_warnings=["warn"],
            ),
            candidates=[_candidate()],
            validation_results=[_validation_result()],
            initial_verdict="REJECT",
            initial_score=40,
            selected="A",
            reason="conflict",
            error_category="continuity",
            attempt_key="attempt-1",
            selection_artifact_meta={"candidate_key": "A"},
            is_patch_fallback=True,
            prev_score=33,
            prev_manuscript="prev",
            tot_used=True,
            mad_used=False,
            asp_manuscript="asp",
        )

        assert result == finalized
        ir._handle_reject.assert_called_once()
        reject_kwargs = ir._handle_reject.call_args.kwargs
        assert reject_kwargs["director_result"] == {"verdict": "REJECT", "trace": True}
        assert reject_kwargs["score"] == 44
        assert reject_kwargs["is_patch"] is True
        ir._finalize_reject_result.assert_called_once()
        finalize_kwargs = ir._finalize_reject_result.call_args.kwargs
        assert finalize_kwargs["reject_result"] is reject_result
        assert finalize_kwargs["final_verdict"] == "REJECT"
        assert finalize_kwargs["final_score"] == 44
        assert finalize_kwargs["validation_warnings"] == ["warn"]
        assert finalize_kwargs["trace_patch_trace"] == {"mode": "patch"}

    def test_append_episode_log_includes_gate_semantics(self):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._get_round_metrics_delta = MagicMock(
            return_value={
                "total_calls": 1,
                "total_tokens": 100,
                "total_cost_usd": 0.01,
                "model_breakdown": {"gemini-2.5-pro": {"tokens": 100, "cost": 0.01}},
            }
        )

        with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"):
            ir._append_episode_log(
                ep_num=6,
                round_num=0,
                director_result={
                    "verdict": "PASS_WITH_FIX",
                    "director_verdict": "PASS_WITH_FIX",
                    "final_verdict": "REJECT",
                    "gate_basis": "quality_floor_fail",
                    "fix_scope": "partial",
                    "authoritative_fix_scope": "inplace",
                    "repair_scope": "partial",
                    "fix_pack": {
                        "must_fix": ["tighten ending"],
                        "target_kind": "local_sentence",
                        "subtype": "movement",
                        "provenance": "director_authored",
                    },
                    "score": 83,
                    "selected": "A",
                    "selection_reason": "best candidate",
                    "selected_candidate": {"strategy_name": "balanced"},
                    "score_breakdown": {},
                    "action_items": ["tighten ending"],
                    "open_review": "",
                },
                initial_verdict="PASS_WITH_FIX",
                final_verdict="REJECT",
                initial_score=83,
                final_score=44,
                is_patch=False,
                patch_fallback=False,
                tot_used=False,
                mad_used=False,
                asp_used=False,
                model="gemini-2.5-pro",
                reject_bucket="quality_floor_fail",
                validation_warnings=[],
            )

        written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
        payload = json.loads(written.strip())
        assert payload["director_verdict"] == "PASS_WITH_FIX"
        assert payload["final_verdict"] == "REJECT"
        assert payload["gate_basis"] == "quality_floor_fail"
        assert payload["repair_scope"] == "partial"
        assert payload["fix_scope"] == "partial"
        assert payload["authoritative_fix_scope"] == "inplace"
        assert payload["repair_contract"]["subtype"] == "movement"
        assert payload["repair_contract"]["fix_scope"] == "partial"
        assert payload["repair_contract"]["provenance"] == "director_authored"
        assert payload["scope_authority"] == {
            "fix_scope": "partial",
            "repair_scope": "partial",
            "authoritative_fix_scope": "inplace",
            "scope_origin": {
                "fix_scope": "runtime_widened",
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
            "widened": True,
        }
        assert payload["scope_origin"] == {
            "fix_scope": "runtime_widened",
            "authoritative_fix_scope": "director_authoritative",
            "repair_scope": "runtime_lane",
        }


def test_director_sc5_budget_preserves_recent_tail_context():
    ctx = _make_ctx()
    ctx.context_advisor = MagicMock()
    ctx.quality_dashboard = MagicMock()
    ctx.memory = MagicMock()
    ctx.memory.retrieve_multi_query_context.return_value = "HEAD-VEC " + ("A" * 260) + " TAIL-VEC"
    ctx.memory.retrieve_npc_context.return_value = "HEAD-NPC " + ("B" * 260) + " TAIL-NPC"
    ctx.context_advisor.plan_director_retrieval.return_value = RetrievalPlan(
        stage="director",
        episode_num=3,
        slots=[
            RetrievalSlot(category="similar_blueprint", query="vec query", source="vec_memory", priority=1),
            RetrievalSlot(category="npc_history", query="npc query", source="db_npc_history", priority=2),
        ],
        total_budget_chars=1000,
    )

    ir = Stage4InterviewRound(ctx)
    ir._resolve_director_protagonist_name = MagicMock(return_value="hero")
    round_ctx = _make_round_ctx()
    round_ctx.next_ep = 3
    round_ctx.prev_manuscripts_text = "history-present"
    round_ctx.blueprint = {"characters": [{"name": "ally"}], "integrated_scenario": "x"}
    round_ctx.chief_writer.generate_ensemble.return_value = [_candidate()]
    round_ctx.manuscript_validator.validate_all_candidates.return_value = [_validation_result()]

    ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {"decision": "PASS", "summary": ""}
    ctx.agents["director"].check_manuscript_history_conflicts.return_value = {"decision": "PASS", "summary": ""}
    ctx.agents["director"].select_and_judge_ensemble.return_value = {
        "selected": "A",
        "verdict": "PASS",
        "score": 95,
        "selection_reason": "ok",
        "selected_candidate": {"manuscript": "pass manuscript", "title": "pass"},
        "state_updates": {},
    }

    def _threshold_side_effect(key, default=None):
        if key == "smart_retrieval.enabled":
            return True
        if key == "smart_retrieval.director_enabled":
            return True
        if key == "context.vector_max_results_s4":
            return 16
        if key == "smart_retrieval.director_total_budget":
            return 180
        return default

    with patch("modules.validation.threshold_helper._threshold", side_effect=_threshold_side_effect):
        ir.run(
            round_num=0,
            stage4_spinner=MagicMock(),
            director_feedback="",
            previous_attempt={},
            round_ctx=round_ctx,
        )

    continuity_ctx = ctx.agents["director"].check_manuscript_continuity_with_cache.call_args.kwargs["memory_context"]
    assert len(continuity_ctx) <= 180
    assert "TAIL-NPC" in continuity_ctx


# ═══════════════════════════════════════════════════════════════
# Operator Parity Tests — console-log-max-display residual
# ═══════════════════════════════════════════════════════════════


class TestOperatorParitySessionLogger:
    """Session logger must receive untruncated provenance fields."""

    def test_session_logger_receives_full_reason_fields(self):
        ctx = _make_ctx()
        sl = MagicMock()
        ctx.session_logger = sl
        ir = Stage4InterviewRound(ctx)

        long_reason = "판정 사유입니다 " * 200  # well over 500 chars
        long_advisory = "advisory 내용 " * 200
        long_directives = "지시사항 " * 200
        long_open_review = "리뷰 " * 200

        ir._log_session_decision(
            next_ep=1,
            round_num=0,
            arc_num=1,
            verdict="PASS",
            score=85,
            selected="A",
            error_category="",
            reason=long_reason,
            fix_scope="",
            open_review=long_open_review,
            action_items=list(range(30)),
            attempt_key="test",
            selection_reason=long_reason,
            verdict_reason=long_reason,
            runtime_advisory=long_advisory,
            retry_directives=long_directives,
            firewall_reason=long_reason,
        )

        assert sl.log_decision.called
        call_kwargs = sl.log_decision.call_args.kwargs

        assert call_kwargs["reason"] == long_reason.strip()
        assert len(call_kwargs["reason"]) > 500
        assert call_kwargs["selection_reason"] == long_reason.strip()
        assert call_kwargs["verdict_reason"] == long_reason.strip()
        assert call_kwargs["open_review"] == long_open_review.strip()
        assert len(call_kwargs["open_review"]) > 300
        assert call_kwargs["runtime_advisory"] == long_advisory.strip()
        assert call_kwargs["retry_directives"] == long_directives.strip()
        assert call_kwargs["firewall_reason"] == long_reason.strip()
        assert len(call_kwargs["action_items"]) == 30

    def test_session_logger_receives_strong_advisory_escalation_meta(self):
        ctx = _make_ctx()
        sl = MagicMock()
        ctx.session_logger = sl
        ir = Stage4InterviewRound(ctx)

        strong_advisory = {
            "source_verdict": "PASS",
            "escalated_to": "PASS_WITH_FIX",
            "triggered_by": ["truth_gate", "npc_drift"],
        }

        ir._log_session_decision(
            next_ep=1,
            round_num=0,
            arc_num=1,
            verdict="PASS_WITH_FIX",
            score=91,
            selected="A",
            error_category="LOGIC_ERROR",
            reason="binding escalation",
            fix_scope="partial",
            open_review="review",
            action_items=["repair opening"],
            attempt_key="s4:ep1:arc1:a1",
            strong_advisory_escalation=strong_advisory,
        )

        assert sl.log_decision.called
        call_kwargs = sl.log_decision.call_args.kwargs
        assert call_kwargs["strong_advisory_escalation"] == strong_advisory


class TestOperatorParityAdvisoryFullSurface:
    """Advisory methods must return all items without truncation."""

    def test_truth_gate_returns_all_warnings(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        warnings = [{"severity": "CRITICAL", "text": f"경고_{i}"} for i in range(25)]
        tg_mock = MagicMock()
        tg_mock.validate.return_value = {"structured_warnings": warnings}
        ctx.state_tracker.check_destroyed_entity_in_manuscript.return_value = []

        with patch("modules.core.truth_gate.TruthGate", return_value=tg_mock):
            result = ir._advisory_truth_gate(
                candidates=[{"manuscript": "원고내용", "state_updates": {}}],
                validation_results=[{}],
                next_ep=1,
            )

        assert result
        joined = result[0]
        for i in range(25):
            assert f"경고_{i}" in joined

    def test_npc_drift_returns_all_items_without_truncation(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        long_found = "이것은 아주 긴 원고 내 발견된 NPC 속성 값입니다 " * 5  # >40 chars

        drift_mock = MagicMock()
        drift_items = [
            {"npc": f"NPC_{i}", "field": "성격", "expected": "냉정", "found_in_ms": long_found} for i in range(15)
        ]
        drift_mock.check.return_value = drift_items

        ws_mock = MagicMock()
        ws_mock.get_npc_role_snapshot.return_value = {"npc1": {}}
        ctx.world_state = ws_mock

        with patch(
            "modules.core.npc_drift_advisor.NpcDriftAdvisor",
            return_value=drift_mock,
        ):
            result = ir._advisory_npc_drift(
                candidates=[{"manuscript": "원고"}],
                validation_results=[{}],
                next_ep=1,
            )

        assert result
        joined = result[0]
        for i in range(15):
            assert f"NPC_{i}" in joined
        # Verify no truncation on found_in_ms
        assert long_found in joined

    def test_npc_drift_persists_structured_relation_tag_metadata(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        drift_mock = MagicMock()
        drift_mock.check.return_value = [
            {
                "npc": "한정호",
                "field": "relation_to_protag",
                "expected": "집착100/오해-80",
                "found_in_ms": "한정호는 주인공을 무덤덤한 거래 상대로만 대했다",
                "drift_subtype": "relation_tag_semantic",
                "target_kind": "local_phrase",
                "expected_relation_axes": ["집착100", "오해-80"],
            }
        ]

        ws_mock = MagicMock()
        ws_mock.get_npc_role_snapshot.return_value = {"한정호": {}}
        ctx.world_state = ws_mock

        with patch(
            "modules.core.npc_drift_advisor.NpcDriftAdvisor",
            return_value=drift_mock,
        ):
            result = ir._advisory_npc_drift(
                candidates=[{"manuscript": "원고"}],
                validation_results=[{}],
                next_ep=2,
            )

        assert result
        cached = ir._last_advisory_metadata["npc_drift"][0]
        assert cached["npc"] == "한정호"
        assert cached["drift_subtype"] == "relation_tag_semantic"
        assert cached["target_kind"] == "local_phrase"
        assert cached["_cand_idx"] == 0
        assert cached["expected_relation_axes"] == ["집착100", "오해-80"]

    def test_numeric_consistency_returns_all_items_full_text(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        long_text = "수치 불일치 상세 설명입니다 " * 20  # >120 chars

        nc_mock = MagicMock()
        nc_items = [{"severity": "MAJOR", "text": long_text} for _ in range(15)]
        nc_mock.check.return_value = nc_items

        with patch(
            "modules.core.numeric_consistency_checker.NumericConsistencyChecker",
            return_value=nc_mock,
        ):
            result = ir._advisory_numeric_consistency(
                candidates=[{"manuscript": "원고", "state_updates": {}}],
                validation_results=[{}],
                next_ep=1,
            )

        assert result
        joined = result[0]
        assert joined.count("[NC-") == 15
        assert long_text in joined

    def test_numeric_consistency_advisory_includes_category_tag(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        nc_mock = MagicMock()
        nc_mock.check.return_value = [
            {
                "severity": "MAJOR",
                "category": "numeric_carryover_authority",
                "text": "[numeric carryover authority mismatch] 원고 '자산 200억' vs resumed FactLedger 'total_assets'=0.1억",
            }
        ]

        with patch(
            "modules.core.numeric_consistency_checker.NumericConsistencyChecker",
            return_value=nc_mock,
        ):
            result = ir._advisory_numeric_consistency(
                candidates=[{"manuscript": "원고", "state_updates": {}}],
                validation_results=[{}],
                next_ep=2,
            )

        assert "[numeric_carryover_authority]" in result[0]

    def test_relationship_drift_returns_all_items_full_text(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        long_pair = "소림파_장문인_과_화산파_장로" * 3  # >30 chars
        long_why = "관계도 변경이 원고와 일치하지 않습니다. 상세 사유: " * 3  # >60 chars

        rd_mock = MagicMock()
        rd_items = [{"npc_pair": long_pair, "why_drift": long_why} for _ in range(10)]
        rd_mock.check.return_value = rd_items

        ws_mock = MagicMock()
        ws_mock.get_relationship_snapshot.return_value = {"pair1": {}}
        ctx.world_state = ws_mock

        with patch(
            "modules.core.relationship_drift_advisor.RelationshipDriftAdvisor",
            return_value=rd_mock,
        ):
            result = ir._advisory_rel_drift(
                candidates=[{"manuscript": "원고"}],
                next_ep=5,
            )

        assert result
        joined = result[0]
        assert joined.count("[MAJOR]") == 10
        assert long_pair in joined
        assert long_why in joined

    def test_flashback_returns_all_items_full_text(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        long_issue = "회상 전환 표지가 현재 원고 맥락과 충돌합니다. " * 6
        fb_mock = MagicMock()
        fb_mock.detect_flashbacks.return_value = [{"text": f"flashback_{i}"} for i in range(2)]
        fb_items = [{"marker": f"marker_{i}", "issue": long_issue} for i in range(8)]
        fb_mock.check.return_value = fb_items

        memory_mock = MagicMock()
        memory_mock.retrieve_high_res_context.return_value = "[제 1화] context"
        memory_mock.fetch_manuscript_snippet.return_value = "snippet"
        ctx.memory = memory_mock

        with patch(
            "modules.core.flashback_verifier.FlashbackVerifier",
            return_value=fb_mock,
        ):
            result = ir._advisory_flashback(
                candidates=[{"manuscript": "원고"}],
                next_ep=6,
            )

        assert result
        joined = result[0]
        assert joined.count("[MAJOR]") == 8
        assert "marker_7" in joined
        assert long_issue in joined

    def test_advisory_flashback_persists_structured_metadata(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        fb_mock = MagicMock()
        fb_mock.detect_flashbacks.return_value = [{"text": "flashback_0"}]
        fb_mock.check.return_value = [
            {
                "marker": "과거의",
                "issue": "과거에는 멈추지 않았는데 회상에서는 멈춘다",
                "contradiction_subtype": "movement",
                "local_fixable": True,
                "patch_anchor": "회상 장면 동선 서술 문장",
                "expected_truth": "1화: 발걸음은 멈추지 않았다",
            }
        ]

        memory_mock = MagicMock()
        memory_mock.retrieve_high_res_context.return_value = "[제 1화] context"
        memory_mock.fetch_manuscript_snippet.return_value = "snippet"
        ctx.memory = memory_mock

        with patch(
            "modules.core.flashback_verifier.FlashbackVerifier",
            return_value=fb_mock,
        ):
            result = ir._advisory_flashback(
                candidates=[{"manuscript": "원고"}],
                next_ep=6,
            )

        assert result
        assert "flashback" in ir._last_advisory_metadata
        item = ir._last_advisory_metadata["flashback"][0]
        assert item["contradiction_subtype"] == "movement"
        assert item["local_fixable"] is True
        assert item["patch_anchor"] == "회상 장면 동선 서술 문장"
        assert item["_cand_idx"] == 0

    def test_info_paradox_returns_all_items_full_text(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        long_info = "주인공만 알 수 없는 기밀 정보"
        long_why = "시점상 접근할 수 없는 정보인데 현재 내면 독백에서 단정적으로 사용되었습니다. " * 4

        ctx.current_project.master_bible = {
            "MasterBible": {"protagonist_config": {"pov": "1인칭", "incarnation_type": "회귀자"}}
        }
        ctx.current_project.db = MagicMock()

        ip_mock = MagicMock()
        ip_items = [{"info_used": long_info, "why_paradox": long_why} for _ in range(9)]
        ip_mock.check.return_value = ip_items

        with (
            patch("modules.core.constants.HUDKeys.get_protagonist_name", return_value="한시우"),
            patch(
                "modules.core.info_paradox_checker.InfoParadoxChecker.build_knowledge_summary",
                return_value="knowledge",
            ),
            patch(
                "modules.core.info_paradox_checker.InfoParadoxChecker",
                return_value=ip_mock,
            ),
        ):
            result = ir._advisory_info_paradox(
                candidates=[{"manuscript": "원고"}],
                next_ep=6,
                genre_name="investment",
            )

        assert result
        joined = result[0]
        assert joined.count("[MAJOR]") == 9
        assert long_info in joined
        assert long_why in joined

    def test_long_term_repetition_returns_all_items_full_text(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        ctx.current_project.db = MagicMock()
        long_pattern = "유사한 장면 구성 패턴"
        long_issue = "최근 장기 구간에서 같은 감정 전개와 연출이 반복되고 있습니다. " * 4

        ltr_mock = MagicMock()
        ltr_items = [{"pattern": long_pattern, "issue": long_issue} for _ in range(7)]
        ltr_mock.check.return_value = ltr_items

        with (
            patch(
                "modules.core.long_term_repetition_advisor.LongTermRepetitionAdvisor.build_pattern_summary",
                return_value="summary",
            ),
            patch(
                "modules.core.long_term_repetition_advisor.LongTermRepetitionAdvisor",
                return_value=ltr_mock,
            ),
        ):
            result = ir._advisory_long_term_rep(
                candidates=[{"manuscript": "원고"}],
                next_ep=20,
            )

        assert result
        joined = result[0]
        assert joined.count("[MAJOR]") == 7
        assert long_pattern in joined
        assert long_issue in joined

    def test_python_validation_advisory_logs_detail_lines(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        validation_result = {"warnings": [], "warning_count": 0, "focus_points": []}
        bv_warnings = ["degraded: check_a", "경고: NPC 이름 불일치", "경고: 시간선 오류"]
        ir._apply_blocking_validator_advisories(
            validation_result=validation_result,
            bv_advisory_warnings=bv_warnings,
            candidate_index=0,
            next_ep=1,
            round_num=0,
        )

        ctx.ui.log.assert_called_once()
        log_msg = ctx.ui.log.call_args.args[0]
        assert "3건" in log_msg
        for w in bv_warnings:
            assert w in log_msg
        call_kwargs = ctx.ui.log.call_args.kwargs
        assert call_kwargs["meta"]["advisory_details"] == bv_warnings


class TestOperatorParityCompactTextNone:
    """_compact_text with limit=None must not truncate."""

    def test_compact_text_none_preserves_full_string(self):
        long_text = "판정 사유 " * 500
        result = Stage4InterviewRound._compact_text(long_text, limit=None)
        assert result == long_text.strip()
        assert len(result) > 500

    def test_compact_text_none_still_strips(self):
        result = Stage4InterviewRound._compact_text("  hello  ", limit=None)
        assert result == "hello"

    def test_compact_text_none_on_empty(self):
        assert Stage4InterviewRound._compact_text("", limit=None) == ""
        assert Stage4InterviewRound._compact_text(None, limit=None) == ""

    def test_summarize_patch_provenance_preserves_all_targets_and_fields(self):
        director_result = {
            "fix_scope": "full",
            "fix_scope_reasoning": "reason-text",
            "open_review": "review-text",
            "fix_pack": {"patch_targets": [f"target_{i}" for i in range(8)]},
        }
        patch_trace = {
            "patch_targets": [f"trace_target_{i}" for i in range(8)],
            "patch_strategy": "line_patch",
            "change_ratio": 0.375,
        }

        summary = Stage4InterviewRound._summarize_patch_provenance(
            director_result,
            "feedback-text",
            patch_trace,
        )

        for i in range(8):
            assert f"trace_target_{i}" in summary
        assert "scope=full" in summary
        assert "reason=reason-text" in summary
        assert "review=review-text" in summary
        assert "feedback=feedback-text" in summary
        assert "strategy=line_patch" in summary
        assert "change_ratio=37.5%" in summary


# ═══════════════════════════════════════════════════════════════════════
# [SSS] Scope Sink Semantics regression tests
# ═══════════════════════════════════════════════════════════════════════


class TestScopeSinkSemantics:
    """Prove scope_origin, carryover persistence, rationale elision, and no routing change."""

    def test_reject_snapshot_contains_scope_origin_runtime_widened(self):
        """When Director scope differs from resolved scope, scope_origin marks fix_scope as runtime_widened."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._collect_validation_warning_lines = MagicMock(return_value=[])
        ir._inherit_attempt_history = MagicMock(return_value=[])
        ir._set_retry_budget_axes = MagicMock(return_value={})
        ir._evaluate_fix_pack_contract = MagicMock(return_value={"ready": False, "reason": "n/a"})

        payload = ir.reject_runtime._build_reject_retry_snapshot(
            director_result={
                "selected_candidate": {"manuscript": "m", "strategy_name": "s"},
                "selection_reason": "r",
                "verdict_reason": "v",
                "director_verdict": "REJECT",
                "final_verdict": "REJECT",
                "gate_basis": "director_primary_reject",
                "repair_scope": "partial",
                "fix_scope": "inplace",
                "authoritative_fix_scope": "inplace",
                "consistency_checklist": {},
                "state_updates": {},
                "open_review": "",
            },
            selected="A",
            director_feedback="feedback",
            action_items=[],
            score=50,
            validation_results=[{}],
            reject_bucket="quality_issue",
            tot_used=False,
            mad_used=False,
            resolved_fix_scope="full",
            resolved_fix_scope_reasoning="widened by continuity replay",
            resolved_fix_pack={},
            error_category="QUALITY_ISSUE",
            feedback_provenance={"director_feedback_text": "", "runtime_advisory": "", "retry_directives": ""},
            previous_attempt=None,
            round_num=0,
        )

        pa = payload.previous_attempt
        assert "scope_origin" in pa
        assert pa["scope_origin"]["authoritative_fix_scope"] == "director_authoritative"
        assert pa["scope_origin"]["repair_scope"] == "runtime_lane"
        # Director gave inplace, runtime widened to full → runtime_widened
        assert pa["scope_origin"]["fix_scope"] == "runtime_widened"

    def test_reject_snapshot_contains_scope_origin_director_authoritative(self):
        """When Director scope matches resolved scope, scope_origin marks fix_scope as director_authoritative."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._collect_validation_warning_lines = MagicMock(return_value=[])
        ir._inherit_attempt_history = MagicMock(return_value=[])
        ir._set_retry_budget_axes = MagicMock(return_value={})
        ir._evaluate_fix_pack_contract = MagicMock(return_value={"ready": False, "reason": "n/a"})

        payload = ir.reject_runtime._build_reject_retry_snapshot(
            director_result={
                "selected_candidate": {"manuscript": "m", "strategy_name": "s"},
                "selection_reason": "r",
                "verdict_reason": "v",
                "director_verdict": "REJECT",
                "final_verdict": "REJECT",
                "gate_basis": "director_primary_reject",
                "repair_scope": "partial",
                "fix_scope": "partial",
                "authoritative_fix_scope": "partial",
                "consistency_checklist": {},
                "state_updates": {},
                "open_review": "",
            },
            selected="A",
            director_feedback="feedback",
            action_items=[],
            score=55,
            validation_results=[{}],
            reject_bucket="quality_issue",
            tot_used=False,
            mad_used=False,
            resolved_fix_scope="partial",
            resolved_fix_scope_reasoning="stays partial",
            resolved_fix_pack={},
            error_category="QUALITY_ISSUE",
            feedback_provenance={"director_feedback_text": "", "runtime_advisory": "", "retry_directives": ""},
            previous_attempt=None,
            round_num=0,
        )

        pa = payload.previous_attempt
        assert pa["scope_origin"]["fix_scope"] == "director_authoritative"

    def test_rationale_blanked_by_set_on_elision_path(self):
        """When runtime elides rationale in post_select_conflict, rationale_blanked_by is set."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._collect_validation_warning_lines = MagicMock(return_value=[])
        ir._inherit_attempt_history = MagicMock(return_value=[])
        ir._set_retry_budget_axes = MagicMock(return_value={})
        ir._evaluate_fix_pack_contract = MagicMock(return_value={"ready": False, "reason": "n/a"})

        payload = ir.reject_runtime._build_reject_retry_snapshot(
            director_result={
                "selected_candidate": {"manuscript": "m", "strategy_name": "s"},
                "selection_reason": "original-selection-reason",
                "verdict_reason": "original-verdict-reason",
                "director_verdict": "PASS",
                "final_verdict": "REJECT",
                "gate_basis": "post_select_conflict",
                "repair_scope": "full",
                "pre_firewall_score": 60,
                "consistency_checklist": {},
                "state_updates": {},
                "open_review": "original-review",
            },
            selected="A",
            director_feedback="conflict feedback",
            action_items=[],
            score=60,
            validation_results=[{}],
            reject_bucket="post_select_conflict",
            tot_used=False,
            mad_used=False,
            resolved_fix_scope="full",
            resolved_fix_scope_reasoning="full rewrite",
            resolved_fix_pack={},
            error_category="LOGIC_ERROR",
            feedback_provenance={"director_feedback_text": "", "runtime_advisory": "", "retry_directives": ""},
            previous_attempt=None,
            round_num=0,
        )

        pa = payload.previous_attempt
        assert pa["rationale_blanked_by"] == "runtime_post_select_conflict_elision"
        # Confirm blanking actually happened
        assert pa["selection_reason"] == ""
        assert pa["open_review"] == ""

    def test_rationale_blanked_by_absent_when_preserved(self):
        """High-score downgraded PASS preserves rationale and does not set rationale_blanked_by."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        ir._collect_validation_warning_lines = MagicMock(return_value=[])
        ir._inherit_attempt_history = MagicMock(return_value=[])
        ir._set_retry_budget_axes = MagicMock(return_value={})
        ir._evaluate_fix_pack_contract = MagicMock(return_value={"ready": False, "reason": "n/a"})

        payload = ir.reject_runtime._build_reject_retry_snapshot(
            director_result={
                "selected_candidate": {"manuscript": "m", "strategy_name": "s"},
                "selection_reason": "preserve-me",
                "verdict_reason": "preserve-verdict",
                "director_verdict": "PASS",
                "final_verdict": "REJECT",
                "gate_basis": "post_select_conflict",
                "repair_scope": "full",
                "pre_firewall_score": 98,
                "consistency_checklist": {},
                "state_updates": {},
                "open_review": "preserve-review",
            },
            selected="A",
            director_feedback="conflict feedback",
            action_items=[],
            score=44,
            validation_results=[{}],
            reject_bucket="post_select_conflict",
            tot_used=False,
            mad_used=False,
            resolved_fix_scope="full",
            resolved_fix_scope_reasoning="full rewrite",
            resolved_fix_pack={},
            error_category="LOGIC_ERROR",
            feedback_provenance={"director_feedback_text": "", "runtime_advisory": "", "retry_directives": ""},
            previous_attempt={"provisional_pass_downgrade": True},
            round_num=0,
        )

        pa = payload.previous_attempt
        assert "rationale_blanked_by" not in pa
        assert pa["selection_reason"] == "preserve-me"
        assert pa["open_review"] == "preserve-review"

    def test_pathology_payload_contains_reuse_contract_and_scope_origin(self):
        """build_retry_pathology_payload persists reuse_contract and scope_origin."""
        ctx = _make_ctx()
        orch = Stage4Orchestrator(ctx)
        runtime = orch.outcome_runtime

        payload = runtime.build_retry_pathology_payload(
            ep_num=5,
            round_num=1,
            previous_attempt={
                "reject_bucket": "post_select_conflict",
                "gate_basis": "post_select_conflict",
                "fix_scope": "full",
                "authoritative_fix_scope": "inplace",
                "repair_scope": "full",
                "error_category": "LOGIC_ERROR",
                "score": 50,
                "fix_pack": {},
                "reuse_contract": {
                    "mode": "best_manuscript_baseline",
                    "baseline_field": "best_manuscript",
                    "conflict_field": "conflict_contract",
                    "preserve_rationale": True,
                },
                "scope_origin": {
                    "fix_scope": "post_select_conflict_override",
                    "authoritative_fix_scope": "director_authoritative",
                    "repair_scope": "runtime_lane",
                },
                "conflict_contract": {
                    "contract_type": "post_select_conflict",
                    "conflicts": [{"conflict_type": "continuity"}],
                },
            },
        )

        assert payload["reuse_contract"]["mode"] == "best_manuscript_baseline"
        assert "scope_origin" in payload
        assert payload["scope_origin"]["authoritative_fix_scope"] == "director_authoritative"
        assert payload["scope_origin"]["repair_scope"] == "runtime_lane"
        # Preserve more specific provenance instead of flattening to generic runtime_widened
        assert payload["scope_origin"]["fix_scope"] == "post_select_conflict_override"

    def test_pathology_payload_contains_rationale_blanked_by(self):
        """build_retry_pathology_payload surfaces rationale_blanked_by from previous_attempt."""
        ctx = _make_ctx()
        orch = Stage4Orchestrator(ctx)
        runtime = orch.outcome_runtime

        payload = runtime.build_retry_pathology_payload(
            ep_num=5,
            round_num=1,
            previous_attempt={
                "reject_bucket": "post_select_conflict",
                "gate_basis": "post_select_conflict",
                "fix_scope": "full",
                "authoritative_fix_scope": "full",
                "repair_scope": "full",
                "error_category": "LOGIC_ERROR",
                "score": 50,
                "fix_pack": {},
                "rationale_blanked_by": "runtime_post_select_conflict_elision",
            },
        )

        assert payload["rationale_blanked_by"] == "runtime_post_select_conflict_elision"

    def test_pass_side_conflict_resolution_linkage_in_gate_semantics(self):
        """PASS-side logging payload contains conflict_resolution_linkage when previous_attempt had conflict_contract."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        mock_pass_result = SimpleNamespace(
            attempt_artifact_meta={"candidate_key": "k", "content_hash": "h", "artifact_path": "p"},
            final_manuscript="manuscript",
            previous_attempt={
                "conflict_contract": {
                    "contract_type": "post_select_conflict",
                    "conflicts": [
                        {"conflict_type": "continuity", "conflict_detail": "d"},
                        {"conflict_type": "history", "conflict_detail": "d2"},
                    ],
                },
                "reuse_contract": {
                    "mode": "best_manuscript_baseline",
                    "baseline_field": "best_manuscript",
                },
            },
        )

        payload = ir._build_pass_result_logging_payload(
            pass_result=mock_pass_result,
            next_ep=3,
            round_num=1,
            round_ctx=_make_round_ctx(),
            director_result={"director_verdict": "PASS", "final_verdict": "PASS", "score": 90},
            trace_director_result=None,
            reason="good",
            is_patch=False,
            trace_patch_trace={},
        )

        gs = payload.session_gate_semantics
        assert "conflict_resolution_linkage" in gs
        assert gs["conflict_resolution_linkage"]["resolved_from"] == "prior_attempt_conflict"
        assert gs["conflict_resolution_linkage"]["original_contract_type"] == "post_select_conflict"
        assert gs["conflict_resolution_linkage"]["conflict_count"] == 2
        assert "reuse_contract" in gs
        assert gs["reuse_contract"]["mode"] == "best_manuscript_baseline"

    def test_pass_side_no_linkage_when_no_prior_conflict(self):
        """PASS-side logging payload has no conflict_resolution_linkage when previous_attempt lacks conflict_contract."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        mock_pass_result = SimpleNamespace(
            attempt_artifact_meta={"candidate_key": "k", "content_hash": "h", "artifact_path": "p"},
            final_manuscript="manuscript",
            previous_attempt=None,
        )

        payload = ir._build_pass_result_logging_payload(
            pass_result=mock_pass_result,
            next_ep=3,
            round_num=0,
            round_ctx=_make_round_ctx(),
            director_result={"director_verdict": "PASS", "final_verdict": "PASS", "score": 90},
            trace_director_result=None,
            reason="first attempt pass",
            is_patch=False,
            trace_patch_trace={},
        )

        gs = payload.session_gate_semantics
        assert "conflict_resolution_linkage" not in gs
        assert "reuse_contract" not in gs

    def test_post_select_conflict_previous_attempt_contains_scope_origin(self):
        """Post-select conflict downgrade path sets scope_origin with post_select_conflict_override."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 3
        round_ctx.prev_manuscripts_text = "━━━ 제1화 원고 ━━━\n이전 원고"
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "CONFLICT",
            "summary": "location mismatch",
        }

        verdict, director_feedback, previous_attempt, error_category = ir.post_select_runtime.run_post_select_checks(
            verdict="PASS",
            next_ep=3,
            round_num=1,
            round_ctx=round_ctx,
            final_manuscript="원고 텍스트",
            final_state_updates={},
            director_result={
                "director_verdict": "PASS",
                "final_verdict": "PASS",
                "selected": "A",
                "selected_candidate": {"strategy_name": "tension", "manuscript": "원고"},
                "fix_scope": "partial",
                "selection_reason": "best candidate",
                "verdict_reason": "pass before post-select",
                "repair_scope": "partial",
                "score_breakdown": {},
                "consistency_checklist": {},
                "open_review": "review",
                "fix_pack": {"patch_targets": ["target"]},
                "action_items": ["fix it"],
            },
            director_feedback="initial feedback",
            score=95,
            error_category="",
            previous_attempt={},
            stage4_spinner=MagicMock(),
            director_memory_context="",
        )

        assert verdict == "REJECT"
        assert "scope_origin" in previous_attempt
        assert previous_attempt["scope_origin"]["fix_scope"] == "post_select_conflict_override"
        assert previous_attempt["scope_origin"]["authoritative_fix_scope"] == "director_authoritative"
        assert previous_attempt["scope_origin"]["repair_scope"] == "runtime_lane"
        assert previous_attempt["scope_authority"] == {
            "fix_scope": "full",
            "repair_scope": "full",
            "authoritative_fix_scope": "full",
            "scope_origin": {
                "fix_scope": "post_select_conflict_override",
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
            "widened": True,
        }

    def test_post_select_conflict_preserves_contradiction_subtype_contract(self):
        """Post-select downgrade should retain contradiction subtype/detail and bounded local-fix hint."""
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 4
        round_ctx.prev_manuscripts_text = "prev manuscript"
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "CONFLICT",
            "summary": "institution mismatch",
        }

        verdict, director_feedback, previous_attempt, error_category = ir.post_select_runtime.run_post_select_checks(
            verdict="PASS",
            next_ep=4,
            round_num=2,
            round_ctx=round_ctx,
            final_manuscript="candidate manuscript",
            final_state_updates={},
            director_result={
                "director_verdict": "PASS_WITH_FIX",
                "final_verdict": "PASS_WITH_FIX",
                "selected": "A",
                "selected_candidate": {"strategy_name": "balanced", "manuscript": "candidate manuscript"},
                "fix_scope": "inplace",
                "selection_reason": "best candidate because proper noun continuity almost landed",
                "verdict_reason": "needs local institution rename",
                "repair_scope": "inplace",
                "score_breakdown": {},
                "consistency_checklist": {},
                "open_review": "rename institution only",
                "fix_pack": {
                    "patch_targets": ["replace institution anchor"],
                    "must_fix": ["rename institution to canonical anchor"],
                    "do_not_regress": ["keep timeline stable"],
                    "success_condition": "institution continuity restored",
                    "target_kind": "entity_ref",
                },
                "action_items": ["rename institution anchor"],
                "contradiction_types": ["proper_noun"],
                "contradiction_details": [
                    {
                        "severity": "CRITICAL",
                        "type": "proper_noun",
                        "current_violation": "institution mismatch",
                        "fix_suggestion": "rename institution anchor",
                    }
                ],
            },
            director_feedback="initial feedback",
            score=92,
            error_category="",
            previous_attempt={},
            stage4_spinner=MagicMock(),
            director_memory_context="",
        )

        assert verdict == "REJECT"
        assert previous_attempt["contradiction_types"] == ["proper_noun"]
        assert previous_attempt["conflict_contract"]["contract_type"] == "post_select_conflict"
        assert previous_attempt["conflict_contract"]["contradiction_types"] == ["proper_noun"]
        assert previous_attempt["conflict_contract"]["bounded_local_fix_hint"] is True
        assert previous_attempt["conflict_contract"]["target_kind"] == "entity_ref"
        assert previous_attempt["repair_contract"] == {
            "subtype": "proper_noun",
            "fix_scope": "full",
            "repair_scope": "full",
            "authoritative_fix_scope": "full",
            "scope_origin": {
                "fix_scope": "post_select_conflict_override",
                "authoritative_fix_scope": "director_authoritative",
                "repair_scope": "runtime_lane",
            },
            "provenance": "director_authored",
            "target_kind": "entity_ref",
        }
        assert any(
            "institution mismatch" in item for item in previous_attempt["conflict_contract"]["contradiction_details"]
        )

    def test_post_select_conflict_merges_opening_continuity_pin_metadata(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.next_ep = 2
        round_ctx.prev_manuscripts_text = "prev manuscript"
        round_ctx.blueprint = {
            "integrated_scenario": "아버지 호출 이후 장면",
            "_continuity_pins": [
                {
                    "type": "opening_action_continuity_pin",
                    "before": "멈추지 않음",
                    "expected": "직전 화 이탈 동선을 유지하거나 전환을 명시",
                    "observed": "걸음을 멈춤, 몸을 돌림, 아버지를 마주 봄",
                }
            ],
        }
        ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
            "decision": "CONFLICT",
            "summary": "opening continuity mismatch",
        }

        verdict, director_feedback, previous_attempt, error_category = ir.post_select_runtime.run_post_select_checks(
            verdict="PASS",
            next_ep=2,
            round_num=0,
            round_ctx=round_ctx,
            final_manuscript="candidate manuscript",
            final_state_updates={},
            director_result={
                "director_verdict": "PASS",
                "final_verdict": "PASS",
                "selected_candidate": {"strategy_name": "balanced", "manuscript": "candidate manuscript"},
                "score_breakdown": {},
                "consistency_checklist": {},
                "fix_pack": {},
                "action_items": [],
            },
            director_feedback="initial feedback",
            score=88,
            error_category="",
            previous_attempt={},
            stage4_spinner=MagicMock(),
            director_memory_context="",
        )

        assert verdict == "REJECT"
        assert error_category == "POST_SELECT_CONTINUITY_CONFLICT"
        assert "opening_action_continuity" in previous_attempt["contradiction_types"]
        assert "opening_action_continuity" in previous_attempt["conflict_contract"]["contradiction_types"]
        assert any(
            "opening continuity pin" in item for item in previous_attempt["conflict_contract"]["contradiction_details"]
        )
        assert "[Continuity Conflict]" in director_feedback

    def test_opening_action_continuity_type_counts_as_continuity_replay_reject(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)

        assert ir._is_continuity_replay_reject(
            director_result={
                "firewall_triggered": True,
                "contradiction_types": ["opening_action_continuity"],
                "firewall_reason": "Contradiction Firewall: opening continuity mismatch",
            },
            director_feedback="",
        )


def test_post_select_conflict_logs_detail_to_ui_sink():
    ctx = _make_ctx()
    ir = Stage4InterviewRound(ctx)
    round_ctx = _make_round_ctx()
    round_ctx.next_ep = 3
    round_ctx.prev_manuscripts_text = "정답 이전 원고\n이전 원고"
    ctx.agents["director"].check_manuscript_continuity_with_cache.return_value = {
        "decision": "CONFLICT",
        "summary": "location mismatch",
    }

    verdict, director_feedback, previous_attempt, error_category = ir.post_select_runtime.run_post_select_checks(
        verdict="PASS",
        next_ep=3,
        round_num=1,
        round_ctx=round_ctx,
        final_manuscript="원고 텍스트",
        final_state_updates={},
        director_result={
            "director_verdict": "PASS",
            "final_verdict": "PASS",
            "selected": "A",
            "selected_candidate": {"strategy_name": "tension", "manuscript": "원고"},
            "fix_scope": "partial",
            "selection_reason": "best candidate",
            "verdict_reason": "pass before post-select",
            "repair_scope": "partial",
            "score_breakdown": {},
            "consistency_checklist": {},
            "open_review": "review",
            "fix_pack": {"patch_targets": ["target"]},
            "action_items": ["fix it"],
        },
        director_feedback="initial feedback",
        score=95,
        error_category="",
        previous_attempt={},
        stage4_spinner=MagicMock(),
        director_memory_context="",
    )

    assert verdict == "REJECT"
    detail_calls = [
        call
        for call in ctx.ui.log.call_args_list
        if call.kwargs.get("component") == "post_select_validation" and call.kwargs.get("event_kind") == "detail"
    ]
    assert detail_calls
    assert any("location mismatch" in call.args[0] for call in detail_calls if call.args)
    assert any(call.kwargs.get("meta", {}).get("conflict_type") == "continuity" for call in detail_calls)
