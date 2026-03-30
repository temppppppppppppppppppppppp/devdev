"""
[Lane-3] consensus-timeout-pass-seam-hardening contract tests.

검증 목표:
1. timeout/error fallback은 PASS로 가장하지 않음 (ABSTAIN)
2. degraded verdict / validation_degraded 플래그 / degraded_reasons 명시
3. existing true-PASS / true-REJECT happy path 회귀 없음
4. downstream pipeline이 degraded 상태를 구분함
"""

from concurrent.futures import TimeoutError as FutureTimeoutError
from unittest.mock import MagicMock

import pytest

from modules.domain.agents.consensus_validator import ConsensusValidator

# ──────────────────────────────────────────────────────────────
# A. _derive_consensus unit tests — ABSTAIN counting logic
# ──────────────────────────────────────────────────────────────


class TestDeriveConsensusAbstainHandling:
    """_derive_consensus: ABSTAIN 레코드가 진짜 합의 증거로 카운트되지 않는다."""

    @pytest.fixture
    def validator(self):
        return ConsensusValidator.__new__(ConsensusValidator)

    def test_all_abstain_produces_degraded_pass(self, validator):
        """모든 검증기 ABSTAIN → DEGRADED_PASS (PASS 아님)."""
        results = [
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
        ]
        final_verdict, _ = validator._derive_consensus(results)
        assert final_verdict == "DEGRADED_PASS"

    def test_all_abstain_sets_validation_degraded_true(self, validator):
        """모든 ABSTAIN → validation_degraded=True."""
        results = [
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
        ]
        _, cr = validator._derive_consensus(results)
        assert cr["validation_degraded"] is True

    def test_all_abstain_degraded_reasons_populated(self, validator):
        """DEGRADED_PASS → degraded_reasons 비어있지 않음."""
        results = [
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
        ]
        _, cr = validator._derive_consensus(results)
        assert len(cr["degraded_reasons"]) > 0

    def test_empty_results_produces_degraded_pass(self, validator):
        """빈 결과 리스트 → total_real=0 → DEGRADED_PASS."""
        final_verdict, cr = validator._derive_consensus([])
        assert final_verdict == "DEGRADED_PASS"
        assert cr["validation_degraded"] is True

    def test_true_pass_has_no_degradation(self, validator):
        """진짜 PASS → validation_degraded=False, final_verdict=PASS."""
        results = [
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
        ]
        final_verdict, cr = validator._derive_consensus(results)
        assert final_verdict == "PASS"
        assert cr["validation_degraded"] is False
        assert cr["degraded_reasons"] == []

    def test_true_reject_critical_has_no_degradation(self, validator):
        """CRITICAL 이슈 REJECT → validation_degraded=False."""
        results = [
            {
                "verdict": "REJECT",
                "confidence": 0.9,
                "issues_found": [{"severity": "CRITICAL", "category": "state", "issue": "dup item"}],
                "passed_checks": [],
            },
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
        ]
        final_verdict, cr = validator._derive_consensus(results)
        assert final_verdict == "REJECT"
        assert cr["validation_degraded"] is False

    def test_partial_abstain_plus_real_pass(self, validator):
        """1 ABSTAIN + 2 PASS → PASS + validation_degraded=True."""
        results = [
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
        ]
        final_verdict, cr = validator._derive_consensus(results)
        assert final_verdict == "PASS"
        assert cr["validation_degraded"] is True

    def test_two_abstain_plus_one_reject(self, validator):
        """2 ABSTAIN + 1 REJECT → REJECT (1/1 real vote) + validation_degraded=True."""
        results = [
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
            {
                "verdict": "REJECT",
                "confidence": 0.9,
                "issues_found": [{"severity": "MAJOR", "category": "state", "issue": "x"}],
                "passed_checks": [],
            },
        ]
        final_verdict, cr = validator._derive_consensus(results)
        assert final_verdict == "REJECT"
        assert cr["validation_degraded"] is True

    def test_vote_summary_has_abstain_key(self, validator):
        """vote_summary에 abstain 키가 포함된다."""
        results = [
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
        ]
        _, cr = validator._derive_consensus(results)
        assert "abstain" in cr["vote_summary"]
        assert cr["vote_summary"]["abstain"] == 1
        assert cr["vote_summary"]["pass"] == 1
        assert cr["vote_summary"]["reject"] == 0

    def test_abstain_does_not_count_as_pass_in_majority(self, validator):
        """ABSTAIN이 PASS 카운트에 포함되지 않는다 (과반수 계산에서 제외)."""
        # 1 PASS + 2 ABSTAIN: total_real=1, real_pass=1 → PASS (과반수 1/1)
        results = [
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
        ]
        final_verdict, cr = validator._derive_consensus(results)
        assert final_verdict == "PASS"
        assert cr["vote_summary"]["pass"] == 1
        assert cr["vote_summary"]["abstain"] == 2
        # degraded 표시는 있어야 함
        assert cr["validation_degraded"] is True

    def test_consensus_reason_mentions_abstained_count(self, validator):
        """consensus_reason에 ABSTAIN 수가 명시된다 (partial abstain case)."""
        results = [
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
        ]
        _, cr = validator._derive_consensus(results)
        assert "1" in cr["consensus_reason"]  # abstain count 언급

    def test_individual_results_preserved(self, validator):
        """individual_results에 ABSTAIN 레코드가 그대로 보존된다."""
        results = [
            {"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"},
        ]
        _, cr = validator._derive_consensus(results)
        indiv = cr["individual_results"]
        assert len(indiv) == 1
        assert indiv[0]["verdict"] == "ABSTAIN"
        assert indiv[0]["fallback_reason"] == "timeout"


# ──────────────────────────────────────────────────────────────
# B. validate_with_consensus integration — timeout/error paths
# ──────────────────────────────────────────────────────────────


class TestTimeoutFallbackContract:
    """validate_with_consensus: timeout/error 발생 시 ABSTAIN 레코드 생성 (PASS 아님)."""

    @pytest.fixture
    def validator(self):
        v = ConsensusValidator.__new__(ConsensusValidator)
        v.max_workers = 3
        v.ENSEMBLE_TIMEOUT = 30
        v.SINGLE_VOTE_TIMEOUT = 10
        v.perspectives = [
            {"name": "p1", "role": "r1", "focus": "f1", "temperature": 0.1},
            {"name": "p2", "role": "r2", "focus": "f2", "temperature": 0.1},
        ]
        v._generate_prev_summary = MagicMock(return_value="prev_summary")
        return v

    def test_all_individual_timeout_produces_degraded_pass(self, validator):
        """모든 개별 future 타임아웃 → DEGRADED_PASS (PASS 아님)."""
        validator._validate_single = MagicMock(side_effect=FutureTimeoutError())

        final_verdict, cr = validator.validate_with_consensus(
            arc={"arc_no": 2, "tactical_doc": "test"},
            prev_arcs=[{"arc_no": 1}],
        )

        assert final_verdict == "DEGRADED_PASS"
        assert cr["validation_degraded"] is True

    def test_all_individual_timeout_records_are_abstain_not_pass(self, validator):
        """개별 타임아웃 → individual_results에 PASS 레코드 없음."""
        validator._validate_single = MagicMock(side_effect=FutureTimeoutError())

        _, cr = validator.validate_with_consensus(
            arc={"arc_no": 2, "tactical_doc": "test"},
            prev_arcs=[{"arc_no": 1}],
        )

        individual = cr.get("individual_results", [])
        assert len(individual) > 0, "individual_results should not be empty"
        for rec in individual:
            assert rec.get("verdict") != "PASS", f"timeout record must not be PASS: {rec}"
            assert rec.get("verdict") == "ABSTAIN"

    def test_all_error_produces_degraded_pass(self, validator):
        """모든 개별 future 오류 → DEGRADED_PASS."""
        validator._validate_single = MagicMock(side_effect=RuntimeError("API error"))

        final_verdict, cr = validator.validate_with_consensus(
            arc={"arc_no": 2, "tactical_doc": "test"},
            prev_arcs=[{"arc_no": 1}],
        )

        assert final_verdict == "DEGRADED_PASS"
        assert cr["validation_degraded"] is True

    def test_all_error_records_have_fallback_reason(self, validator):
        """오류 레코드에 fallback_reason 필드가 있어야 한다."""
        validator._validate_single = MagicMock(side_effect=RuntimeError("API error"))

        _, cr = validator.validate_with_consensus(
            arc={"arc_no": 2, "tactical_doc": "test"},
            prev_arcs=[{"arc_no": 1}],
        )

        for rec in cr.get("individual_results", []):
            assert "fallback_reason" in rec

    def test_timeout_confidence_is_zero_not_half(self, validator):
        """타임아웃 레코드 confidence는 0.5가 아니라 0.0이어야 한다."""
        validator._validate_single = MagicMock(side_effect=FutureTimeoutError())

        _, cr = validator.validate_with_consensus(
            arc={"arc_no": 2, "tactical_doc": "test"},
            prev_arcs=[{"arc_no": 1}],
        )

        for rec in cr.get("individual_results", []):
            assert rec.get("confidence") == 0.0, f"timeout confidence must be 0.0, got {rec.get('confidence')}"

    def test_true_pass_happy_path_regression(self, validator):
        """진짜 PASS happy path 회귀 없음."""
        validator._validate_single = MagicMock(
            return_value={
                "verdict": "PASS",
                "confidence": 0.9,
                "issues_found": [],
                "passed_checks": ["check1"],
                "reasoning": "ok",
            }
        )

        final_verdict, cr = validator.validate_with_consensus(
            arc={"arc_no": 2, "tactical_doc": "test"},
            prev_arcs=[{"arc_no": 1}],
        )

        assert final_verdict == "PASS"
        assert cr["validation_degraded"] is False
        assert cr["degraded_reasons"] == []

    def test_true_reject_critical_happy_path_regression(self, validator):
        """진짜 CRITICAL REJECT happy path 회귀 없음."""
        validator._validate_single = MagicMock(
            return_value={
                "verdict": "REJECT",
                "confidence": 0.9,
                "issues_found": [{"severity": "CRITICAL", "category": "state", "issue": "dup item"}],
                "passed_checks": [],
                "reasoning": "critical issue",
            }
        )

        final_verdict, cr = validator.validate_with_consensus(
            arc={"arc_no": 2, "tactical_doc": "test"},
            prev_arcs=[{"arc_no": 1}],
        )

        assert final_verdict == "REJECT"
        assert cr["validation_degraded"] is False

    def test_arc1_no_prev_arcs_timeout_produces_degraded_pass(self, validator):
        """Arc 1 (prev_arcs 없음) 상황에서도 타임아웃 → DEGRADED_PASS."""
        validator._validate_single = MagicMock(side_effect=FutureTimeoutError())

        final_verdict, cr = validator.validate_with_consensus(
            arc={"arc_no": 1, "tactical_doc": "test"},
            prev_arcs=[],  # Arc 1: 연속성 검증 스킵
        )

        assert final_verdict == "DEGRADED_PASS"
        assert cr["validation_degraded"] is True


# ──────────────────────────────────────────────────────────────
# C. vote_summary backward-compat — existing keys preserved
# ──────────────────────────────────────────────────────────────


class TestVoteSummaryBackwardCompat:
    """vote_summary 기존 pass/reject 키가 유지된다."""

    @pytest.fixture
    def validator(self):
        return ConsensusValidator.__new__(ConsensusValidator)

    def test_pass_reject_keys_still_present(self, validator):
        results = [
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
            {"verdict": "REJECT", "confidence": 0.9, "issues_found": [], "passed_checks": []},
        ]
        _, cr = validator._derive_consensus(results)
        assert "pass" in cr["vote_summary"]
        assert "reject" in cr["vote_summary"]

    def test_abstain_key_added(self, validator):
        results = [
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
        ]
        _, cr = validator._derive_consensus(results)
        assert "abstain" in cr["vote_summary"]
        assert cr["vote_summary"]["abstain"] == 0

    def test_degraded_reasons_key_present_even_when_empty(self, validator):
        """validation_degraded=False인 경우에도 degraded_reasons 키가 존재."""
        results = [
            {"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []},
        ]
        _, cr = validator._derive_consensus(results)
        assert "degraded_reasons" in cr
        assert cr["degraded_reasons"] == []

    def test_validation_degraded_key_always_present(self, validator):
        """validation_degraded 키가 항상 존재한다."""
        for results in [
            [{"verdict": "PASS", "confidence": 0.9, "issues_found": [], "passed_checks": []}],
            [{"verdict": "ABSTAIN", "confidence": 0.0, "issues_found": [], "fallback_reason": "timeout"}],
            [],
        ]:
            _, cr = validator._derive_consensus(results)
            assert "validation_degraded" in cr


# ──────────────────────────────────────────────────────────────
# D. Pipeline seam — degraded advisory
# ──────────────────────────────────────────────────────────────


class TestPipelineDegradedSeam:
    """stage2_validation_pipeline: degraded consensus는 WARNING advisory를 추가한다."""

    def _make_pipeline(self):
        """최소 pipeline fixture — Stage2Orchestrator 경유."""
        from modules.core.stage2_orchestrator import Stage2Orchestrator
        from modules.core.stage2_validation_pipeline import Stage2ValidationPipeline

        orchestrator = Stage2Orchestrator(app=MagicMock())
        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.agents = {}
        orchestrator._ctx = ctx
        return Stage2ValidationPipeline(orchestrator)

    def test_degraded_pass_adds_warning_advisory(self):
        """DEGRADED_PASS → _python_advisories에 WARNING severity 항목 추가."""
        pipeline = self._make_pipeline()

        consensus_mock = MagicMock()
        consensus_mock.validate_with_consensus.return_value = (
            "DEGRADED_PASS",
            {
                "vote_summary": {"pass": 0, "reject": 0, "abstain": 3},
                "critical_issues": [],
                "passed_checks": [],
                "validation_degraded": True,
                "degraded_reasons": ["all_validators_abstained"],
            },
        )
        pipeline.ctx.agents = {"consensus": consensus_mock}

        _python_advisories: list = []
        result = pipeline._run_consensus_phase(
            refined_arc={"arc_no": 2},
            four_phase_passed=False,
            all_refined_arcs=[],
            constraint_block="",
            rich_console=MagicMock(),
            python_advisory=[],
            _python_advisories=_python_advisories,
            consensus_passed=False,
        )

        # consensus_passed는 True (파이프라인이 계속 진행)
        assert result is True
        # WARNING advisory가 추가됨
        warning_advisories = [a for a in _python_advisories if a.get("severity") == "WARNING"]
        assert len(warning_advisories) >= 1
        assert any("consensus" in a.get("source", "") for a in warning_advisories)

    def test_true_pass_does_not_add_warning_advisory(self):
        """진짜 PASS → WARNING advisory 없음."""
        pipeline = self._make_pipeline()

        consensus_mock = MagicMock()
        consensus_mock.validate_with_consensus.return_value = (
            "PASS",
            {
                "vote_summary": {"pass": 3, "reject": 0, "abstain": 0},
                "critical_issues": [],
                "passed_checks": ["check1"],
                "validation_degraded": False,
                "degraded_reasons": [],
            },
        )
        pipeline.ctx.agents = {"consensus": consensus_mock}

        _python_advisories: list = []
        pipeline._run_consensus_phase(
            refined_arc={"arc_no": 2},
            four_phase_passed=False,
            all_refined_arcs=[],
            constraint_block="",
            rich_console=MagicMock(),
            python_advisory=[],
            _python_advisories=_python_advisories,
            consensus_passed=False,
        )

        warning_advisories = [a for a in _python_advisories if a.get("severity") == "WARNING"]
        assert len(warning_advisories) == 0
