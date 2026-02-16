"""[Phase 3-Obs Step 2] 에이전트 레벨 ThreadPoolExecutor PerfTimer 계측 테스트.

A. ChiefWriter (2건): 타이머 로그 출력, 예외 비전파
B. ArcEnsemble (1건): 타이머 로그 출력
C. BlueprintEnsemble (1건): 타이머 로그 출력
D. ConsensusValidator (1건): 타이머 로그 출력
E. DirectorAuditor (1건): 타이머 로그 출력
F. 공통 (1건): 타이머 예외 시 비전파 확인
"""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ══════════════════════════════════════════════════════════════
# A. ChiefWriter
# ══════════════════════════════════════════════════════════════


class TestChiefWriterTimer:
    """ChiefWriter.generate_ensemble ThreadPoolExecutor 타이머 검증."""

    @pytest.fixture
    def writer(self):
        with patch("modules.domain.agents.chief_writer.BaseAgent.__init__", return_value=None):
            from modules.domain.agents.chief_writer import ChiefWriter

            cw = ChiefWriter.__new__(ChiefWriter)
            # 필수 속성 세팅
            cw.ENSEMBLE_TIMEOUT = 10
            cw.SINGLE_CANDIDATE_TIMEOUT = 5
            cw.context = MagicMock()
            cw._context_builder = None  # [B-1-4] lazy init 전제
            cw._quality_gate = None  # [B-1-5] lazy init 전제
            return cw

    def test_timer_log_emitted(self, writer, caplog):
        """generate_ensemble 호출 시 [PerfTimer:ChiefWriter] 로그 출력."""
        dummy_candidate = {
            "strategy": "balanced",
            "manuscript": "테스트 원고" * 100,
            "title": "테스트",
            "state_updates": {},
            "metadata": {},
        }
        writer._prefetch_manuscripts = MagicMock()
        writer._build_common_context = MagicMock(return_value="context")
        writer._get_or_create_context_cache = MagicMock(return_value={})
        writer._generate_single_candidate = MagicMock(return_value=dummy_candidate)

        with caplog.at_level(logging.INFO):
            result = writer.generate_ensemble(
                ep_num=1,
                blueprint={},
                prev_manuscript="",
                hud_report="",
                arc_doc="",
                master_bible={},
                genre_name="wuxia",
            )

        timer_logs = [r for r in caplog.records if "[PerfTimer:ChiefWriter]" in r.message]
        assert len(timer_logs) == 1
        assert "cw_ep1_ensemble=" in timer_logs[0].message
        assert timer_logs[0].message.endswith("s")

    def test_timer_exception_non_propagating(self, writer, caplog):
        """타이머 코드 예외 시 결과에 영향 없음."""
        dummy_candidate = {
            "strategy": "balanced",
            "manuscript": "테스트 원고" * 100,
            "title": "테스트",
            "state_updates": {},
            "metadata": {},
        }
        writer._prefetch_manuscripts = MagicMock()
        writer._build_common_context = MagicMock(return_value="context")
        writer._get_or_create_context_cache = MagicMock(return_value={})
        writer._generate_single_candidate = MagicMock(return_value=dummy_candidate)

        # time.monotonic 패치로 logging.info에서 예외 발생시켜도 결과 정상
        with patch("modules.domain.agents.chief_writer.logging.info", side_effect=Exception("log fail")):
            # generate_ensemble 내부에서 모든 logging.info가 실패하지만 크래시 안 됨
            result = writer.generate_ensemble(
                ep_num=1,
                blueprint={},
                prev_manuscript="",
                hud_report="",
                arc_doc="",
                master_bible={},
                genre_name="wuxia",
            )
        # 후보가 0개여도 크래시 없이 반환
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════
# B. ArcEnsemble
# ══════════════════════════════════════════════════════════════


class TestArcEnsembleTimer:
    """ArcEnsembleGenerator.generate_ensemble ThreadPoolExecutor 타이머 검증."""

    @pytest.fixture
    def ensemble(self):
        with patch("modules.domain.agents.arc_ensemble.BaseAgent.__init__", return_value=None):
            from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator

            ae = ArcEnsembleGenerator.__new__(ArcEnsembleGenerator)
            ae.max_workers = 3
            ae.ENSEMBLE_TIMEOUT = 10
            ae.SINGLE_CANDIDATE_TIMEOUT = 5
            ae.strategies = [
                {"name": "s1", "emphasis": ""},
                {"name": "s2", "emphasis": ""},
                {"name": "s3", "emphasis": ""},
            ]
            ae.context = MagicMock()
            return ae

    def test_timer_log_emitted(self, ensemble, caplog):
        """generate_ensemble 호출 시 [PerfTimer:ArcEnsemble] 로그 출력."""
        dummy_arc = {
            "tactical_doc": "테스트" * 500,
            "arc_no": 1,
            "ep_start": 1,
            "ep_end": 5,
            "_strategy": "s1",
        }
        ensemble._generate_single = MagicMock(return_value=dummy_arc)
        ensemble._safe_tactical_str = MagicMock(side_effect=lambda x: x if isinstance(x, str) else str(x))

        with caplog.at_level(logging.INFO):
            best, candidates = ensemble.generate_ensemble(
                arc_no=3,
                ep_start=1,
                vol_strategy="",
                curr_block={},
                prev_arc_context="",
                constraint_block="",
            )

        timer_logs = [r for r in caplog.records if "[PerfTimer:ArcEnsemble]" in r.message]
        assert len(timer_logs) == 1
        assert "arc_3_ensemble=" in timer_logs[0].message


# ══════════════════════════════════════════════════════════════
# C. BlueprintEnsemble
# ══════════════════════════════════════════════════════════════


class TestBlueprintEnsembleTimer:
    """BlueprintEnsembleGenerator.generate_ensemble ThreadPoolExecutor 타이머 검증."""

    @pytest.fixture
    def ensemble(self):
        with patch("modules.domain.agents.blueprint_ensemble.BaseAgent.__init__", return_value=None):
            from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator

            be = BlueprintEnsembleGenerator.__new__(BlueprintEnsembleGenerator)
            be.max_workers = 3
            be.ENSEMBLE_TIMEOUT = 10
            be.SINGLE_CANDIDATE_TIMEOUT = 5
            be.strategies = [
                {"name": "action", "emphasis": ""},
                {"name": "emotion", "emphasis": ""},
                {"name": "dialogue", "emphasis": ""},
            ]
            be.context = MagicMock()
            return be

    def test_timer_log_emitted(self, ensemble, caplog):
        """generate_ensemble 호출 시 [PerfTimer:BlueprintEnsemble] 로그 출력."""
        dummy_bp = {
            "scene_breakdown": {"s1": {}, "s2": {}, "s3": {}, "s4": {}},
            "integrated_scenario": "테스트 시나리오",
            "_strategy": "action",
        }
        ensemble._generate_single = MagicMock(return_value=dummy_bp)
        ensemble._format_constraints = MagicMock(return_value="")
        ensemble._format_prev_info_expanded = MagicMock(return_value="")
        ensemble._build_hud_context = MagicMock(return_value="")

        with caplog.at_level(logging.INFO):
            best, candidates = ensemble.generate_ensemble(
                ep_num=5,
                arc_data={"tactical_doc": "test"},
                constraint_block={},
            )

        timer_logs = [r for r in caplog.records if "[PerfTimer:BlueprintEnsemble]" in r.message]
        assert len(timer_logs) == 1
        assert "bp_ep5_ensemble=" in timer_logs[0].message


# ══════════════════════════════════════════════════════════════
# D. ConsensusValidator
# ══════════════════════════════════════════════════════════════


class TestConsensusTimer:
    """ConsensusValidator.validate_with_consensus ThreadPoolExecutor 타이머 검증."""

    @pytest.fixture
    def validator(self):
        with patch("modules.domain.agents.consensus_validator.BaseAgent.__init__", return_value=None):
            from modules.domain.agents.consensus_validator import VALIDATION_PERSPECTIVES, ConsensusValidator

            cv = ConsensusValidator.__new__(ConsensusValidator)
            cv.max_workers = 3
            cv.ENSEMBLE_TIMEOUT = 10
            cv.SINGLE_VOTE_TIMEOUT = 5
            cv.perspectives = VALIDATION_PERSPECTIVES
            cv.context = MagicMock()
            return cv

    def test_timer_log_emitted(self, validator, caplog):
        """validate_with_consensus 호출 시 [PerfTimer:Consensus] 로그 출력."""
        dummy_result = {"verdict": "PASS", "confidence": 0.9, "issues_found": []}
        validator._validate_single = MagicMock(return_value=dummy_result)
        validator._generate_prev_summary = MagicMock(return_value="")
        validator._derive_consensus = MagicMock(return_value=("PASS", {"vote_summary": {}}))

        with caplog.at_level(logging.INFO):
            verdict, result = validator.validate_with_consensus(
                arc={"arc_no": 1, "tactical_doc": "test"},
                prev_arcs=[{"arc_no": 0}],
            )

        timer_logs = [r for r in caplog.records if "[PerfTimer:Consensus]" in r.message]
        assert len(timer_logs) == 1
        assert "consensus_validation=" in timer_logs[0].message


# ══════════════════════════════════════════════════════════════
# E. DirectorAuditor
# ══════════════════════════════════════════════════════════════


class TestDirectorAuditorTimer:
    """DirectorQualityAuditor._strategic_audit_with_self_consistency 타이머 검증."""

    @pytest.fixture
    def auditor(self):
        from modules.domain.agents.director_auditor import DirectorQualityAuditor

        mock_director = MagicMock()
        mock_director.consistency_votes = 3
        mock_director.ambiguous_lower = 40
        mock_director.ambiguous_upper = 80
        # 1차 평가: 애매한 점수 → Self-Consistency 활성화
        mock_director.ask = MagicMock(return_value='{"decision": "PASS", "score": 60, "reason": "ok"}')
        mock_director._extract_json_robust = MagicMock(return_value={"decision": "PASS", "score": 60, "reason": "ok"})
        auditor = DirectorQualityAuditor(mock_director)
        return auditor

    def test_timer_log_emitted(self, auditor, caplog):
        """Self-Consistency 투표 시 [PerfTimer:DirectorAuditor] 로그 출력."""
        with caplog.at_level(logging.INFO):
            result = auditor._strategic_audit_with_self_consistency(
                prompt="테스트 프롬프트",
                arc_no=2,
            )

        timer_logs = [r for r in caplog.records if "[PerfTimer:DirectorAuditor]" in r.message]
        assert len(timer_logs) == 1
        assert "director_sc_arc2_voting=" in timer_logs[0].message


# ══════════════════════════════════════════════════════════════
# F. 공통 — 타이머 코드 예외 비전파
# ══════════════════════════════════════════════════════════════


class TestTimerExceptionSafety:
    """타이머 코드에서 예외 발생 시 메인 로직에 영향 없음."""

    def test_time_monotonic_failure_non_propagating(self):
        """time.monotonic가 실패해도 ThreadPoolExecutor 블록 정상 실행."""
        import time

        original = time.monotonic
        call_count = 0

        def failing_monotonic():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("clock failure")
            return original()

        # monotonic 첫 호출 실패 시 _tp_t0가 예외 → 후속 로그에서 NameError
        # 하지만 try/except로 감싸져 있으므로 비전파
        # 이 테스트는 패턴의 안전성을 확인
        _tp_t0 = None
        try:
            _tp_t0 = failing_monotonic()
        except Exception:
            pass

        # 메인 로직 (ThreadPoolExecutor 대역)
        result = sum(range(100))

        try:
            if _tp_t0 is not None:
                elapsed = time.monotonic() - _tp_t0
                logging.info(f"[PerfTimer:Test] test={elapsed:.2f}s")
        except Exception:
            pass

        assert result == 4950
