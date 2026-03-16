"""[B-1-3] Stage4InterviewRound unit tests."""

import concurrent.futures
import json
import logging
import time
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from modules.core.context_advisor import RetrievalPlan, RetrievalSlot, RetrievalSources
from modules.core.session_logger import SessionLogger
from modules.core.stage4_context import Stage4Context
from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.core.stage4_orchestrator import Stage4Orchestrator, _RoundContext


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


class _AppTrapInterviewRound(Stage4InterviewRound):
    @property
    def app(self):
        raise AssertionError("Stage4InterviewRound should not access self.app")


def _candidate():
    return {"manuscript": "테스트 원고 " * 300, "strategy_name": "balanced", "title": "테스트"}


def _validation_result():
    return {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 2000}}


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
        ir._god1_stage4_spinner = MagicMock()
        ir._god1_round_num = 0
        ir._god1_arc_pos = 1
        ir._god1_total_ep_in_arc = 10
        ir._god1_arc_data = {}
        ir._god1_prev_manuscript = ""

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
            patch.object(ir, "_build_director_work_focus_summary", return_value="[작품 추적 슬롯 요약]\n- 소꿉친구 라인"),
            patch.object(ir, "_build_director_relationship_context", return_value=""),
        ):
            validation_results = ir._run_pre_director_validation(
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
            )

        assert validation_results[0]["coverage_warnings"] == ["missing_relation_slice"]


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
        rows = [
            json.loads(line)
            for line in decisions_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
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
            previous_attempt={"score": 70, "best_manuscript": "원고"},
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

        history = ir._build_manuscript_history_for_check(prev_manuscripts_text, next_ep=3)

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

        ir._record_s4_attempt(
            episode=2,
            round_num=1,
            success=False,
            score=61,
            verdict="REJECT",
            reject_reason="retry needed",
            error_category="LOGIC_ERROR",
            reject_bucket="post_select_conflict",
            score_breakdown={"narrative_flow": 9},
        )

        kw = ctx.pass_rate_monitor.record_attempt.call_args.kwargs
        assert kw["error_category"] == "LOGIC_ERROR"
        assert kw["reject_bucket"] == "post_select_conflict"
        assert kw["score_breakdown"]["narrative_flow"] == 9

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
            previous_attempt={"score": 70, "best_manuscript": "원고"},
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
            previous_attempt={"score": 70, "best_manuscript": "draft"},
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
            previous_attempt={"score": 70, "best_manuscript": "원고"},
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
        src = Path("modules/core/stage4_interview_round.py").read_text(encoding="utf-8")

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

        verdict, director_feedback, previous_attempt, error_category = ir._run_post_select_checks(
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
            },
            director_feedback="initial feedback",
            score=95,
            error_category="",
            previous_attempt={},
            stage4_spinner=MagicMock(),
            director_memory_context="",
        )

        assert verdict == "REJECT"
        assert error_category == "LOGIC_ERROR"
        assert "[Continuity Conflict]" in director_feedback
        assert previous_attempt["fix_scope"] == "partial"
        assert previous_attempt["selected_strategy_key"] == "tension"
        assert previous_attempt["selection_reason"] == "best candidate"
        assert previous_attempt["verdict_reason"] == "director pass before post-select"
        assert previous_attempt["reject_bucket"] == "post_select_conflict"

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

        verdict, director_feedback, previous_attempt, error_category = ir._run_post_select_checks(
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

    def test_post_select_conflict_prefers_patch_before_inplace(self):
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
                "fix_scope": "",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "tension",
            },
            prev_manuscript="original manuscript",
            style_guide="",
            blueprint={},
            common_writer_kwargs={},
        )

        assert candidates == round_ctx.chief_writer.patch_with_feedback.return_value
        assert is_patch is True
        assert patch_fallback is False
        assert prev_score == 98
        assert asp_manuscript is None
        round_ctx.chief_writer.inplace_patch.assert_not_called()
        round_ctx.chief_writer.patch_with_feedback.assert_called_once()
        round_ctx.chief_writer.regenerate_with_feedback.assert_not_called()

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

    def test_post_select_conflict_force_patch_only_once(self):
        ctx = _make_ctx()
        ir = Stage4InterviewRound(ctx)
        round_ctx = _make_round_ctx()
        round_ctx.chief_writer.inplace_patch.return_value = [_candidate()]

        candidates, is_patch, patch_fallback, prev_score, asp_manuscript = ir._generate_candidates(
            round_num=2,
            chief_writer=round_ctx.chief_writer,
            director_feedback="fix continuity only",
            previous_attempt={
                "score": 98,
                "best_manuscript": "original manuscript",
                "fix_scope": "",
                "reject_bucket": "post_select_conflict",
                "selected_strategy_key": "tension",
            },
            prev_manuscript="original manuscript",
            style_guide="",
            blueprint={},
            common_writer_kwargs={},
        )

        assert candidates == round_ctx.chief_writer.inplace_patch.return_value
        assert is_patch is True
        assert patch_fallback is False
        assert prev_score == 98
        assert asp_manuscript is None
        round_ctx.chief_writer.patch_with_feedback.assert_not_called()
        round_ctx.chief_writer.regenerate_with_feedback.assert_not_called()
        round_ctx.chief_writer.inplace_patch.assert_called_once()

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
        assert result.previous_attempt["fix_scope"] == "partial"
        assert result.previous_attempt["firewall_triggered"] is True
        assert "continuity replay" in result.director_feedback

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
        assert result.previous_attempt["fix_scope"] == "partial"
        assert result.previous_attempt["firewall_triggered"] is True
        assert "continuity replay" in result.director_feedback

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
        assert result.error_category == ""

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
        ir._run_post_select_checks = MagicMock(return_value=("PASS_WITH_FIX", "", {}, ""))
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

    def test_append_episode_log_includes_round_cost_and_strategy_flags(self):
        ctx = _make_ctx()
        ctx.current_project.name = "proj"
        ir = Stage4InterviewRound(ctx)
        ir._round_start_ts = time.monotonic() - 1
        ir._last_strategy_budget = "reduced"
        ir._last_strategy_count = 2
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
        assert payload["patch_trace"]["patch_strategy"] == ""
        assert payload["patch_trace"]["patch_targets"] == []
        assert payload["patch_trace"]["unchanged_ratio"] is None

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

        with patch("modules.core.stage4_interview_round.open", side_effect=OSError("disk full")), patch(
            "os.makedirs"
        ):
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
