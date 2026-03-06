"""Phase 5: 프롬프트/설정 위생 + 문서화 테스트"""

from unittest.mock import MagicMock

import pytest

from modules.core.genre_guards.fantasy_guard import FantasyGuard
from modules.core.stage4_context import _CONDITIONAL_MODULE_KEYS, Stage4Context
from modules.validation.advisory_validator import AdvisoryValidator
from modules.validation.blocking_validator_scene_checks import BlockingValidatorSceneChecks

# ── S-07: Pacing Advisory ──────────────────────────────────────


class TestPacingAdvisory:
    def test_short_manuscript_no_suggestion(self):
        """1000자 미만 원고 → None"""
        v = AdvisoryValidator()
        result = v._check_pacing("짧은 원고", {})
        assert result is None

    def test_few_paragraphs_suggestion(self):
        """문단 3개 미만 → 문단 분리 권고"""
        v = AdvisoryValidator()
        manuscript = "A" * 2000  # 단일 문단, 줄바꿈 없음
        result = v._check_pacing(manuscript, {})
        assert result is not None
        assert result["type"] == "pacing_advisory"
        assert "문단 분리" in result["suggestion"]

    def test_long_paragraphs_suggestion(self):
        """평균 문단 > 2000자 → 호흡 조절 권고"""
        v = AdvisoryValidator()
        # 3개 문단, 각 3000자
        manuscript = ("가" * 3000 + "\n\n") * 3
        result = v._check_pacing(manuscript, {})
        assert result is not None
        assert "호흡 조절" in result["suggestion"]

    def test_good_pacing_no_suggestion(self):
        """적절한 페이싱 → None"""
        v = AdvisoryValidator()
        manuscript = "\n\n".join(["가" * 500] * 10)  # 10개 문단, 각 500자
        result = v._check_pacing(manuscript, {})
        assert result is None

    def test_validate_includes_pacing(self):
        """validate() 결과에 pacing suggestion 포함"""
        v = AdvisoryValidator()
        manuscript = "가" * 3000  # 단일 문단
        result = v.validate(manuscript, {})
        assert result["passed"] is True
        types = [s["type"] for s in result["suggestions"]]
        assert "pacing_advisory" in types


# ── S-02: MAX_OUTPUT_TOKENS ────────────────────────────────────


class TestMaxOutputTokens:
    def test_class_constant_exists(self):
        from modules.domain.agents.base_agent import BaseAgent

        assert hasattr(BaseAgent, "MAX_OUTPUT_TOKENS")
        assert isinstance(BaseAgent.MAX_OUTPUT_TOKENS, int)
        assert BaseAgent.MAX_OUTPUT_TOKENS > 0


# ── S-13: Stage4Context Composite ──────────────────────────────


class TestConditionalModulesComposite:
    @pytest.fixture
    def mock_deps(self):
        return {
            "ui": MagicMock(),
            "current_project": MagicMock(),
            "agents": {},
            "sys": MagicMock(),
            "state_tracker": MagicMock(),
        }

    def test_default_empty_dict(self, mock_deps):
        ctx = Stage4Context(**mock_deps)
        assert ctx.conditional_modules == {}

    def test_get_module_missing_returns_none(self, mock_deps):
        ctx = Stage4Context(**mock_deps)
        assert ctx.get_module("nonexistent") is None

    def test_get_module_returns_value(self, mock_deps):
        mock_tot = MagicMock()
        ctx = Stage4Context(**mock_deps, conditional_modules={"tree_of_thoughts": mock_tot})
        assert ctx.get_module("tree_of_thoughts") is mock_tot

    def test_from_app_populates_modules(self):
        app = MagicMock()
        app.cross_verifier = MagicMock()
        app.tree_of_thoughts = MagicMock()
        ctx = Stage4Context.from_app(app)
        assert ctx.get_module("cross_verifier") is app.cross_verifier
        assert ctx.get_module("tree_of_thoughts") is app.tree_of_thoughts

    def test_from_app_skips_none_modules(self):
        app = MagicMock(spec=[])
        app.ui = MagicMock()
        app.current_project = MagicMock()
        app.agents = {}
        app.sys = MagicMock()
        ctx = Stage4Context.from_app(app)
        assert ctx.conditional_modules == {}

    def test_module_keys_constant(self):
        assert len(_CONDITIONAL_MODULE_KEYS) == 8
        assert "adversarial_self_play" in _CONDITIONAL_MODULE_KEYS


# ── S-15: Cliffhanger Target Threshold ─────────────────────────


class TestCliffhangerThreshold:
    @pytest.fixture
    def scene_checks(self):
        host = MagicMock()
        host.consistency_checks._extract_keywords.return_value = []
        return BlockingValidatorSceneChecks(host)

    def test_low_strength_gets_warning(self, scene_checks):
        """낮은 강도 점수 → warning 필드 추가"""
        # 기본 체크 (cliffhanger 미지시) 시 평이한 엔딩
        ctx = {"blueprint": {}}
        manuscript = "가" * 1000 + "\n잠들었다."
        result = scene_checks._check_cliffhanger_ending(manuscript, ctx)
        assert result["passed"] is True
        # 평이한 엔딩은 strength=15 → target 40 미달
        assert result["cliffhanger_strength"] == 15

    def test_strong_cliffhanger_no_warning(self, scene_checks):
        """강한 강도 → warning 없음"""
        ctx = {"blueprint": {"cliffhanger": "적이 나타났다"}}
        manuscript = (
            "가" * 1000 + "\n바로 그때, 갑자기 그림자가 나타났다. 과연 그의 정체는? 죽음의 위기가 다가오고 있었다."
        )
        result = scene_checks._check_cliffhanger_ending(manuscript, ctx)
        assert result["passed"] is True
        if result.get("cliffhanger_strength", 0) >= 40:
            assert "warning" not in result


# ── S-16: Fantasy Guard Deep Validation ─────────────────────────


class TestFantasyGuardDeepValidation:
    @pytest.fixture
    def guard(self):
        return FantasyGuard()

    def test_wuxia_compound_pattern_detected(self, guard):
        """무협 복합 표현 감지"""
        ms = "마나를 모아 마법을 시전했다. 그는 기를 모으며 단전에서 내공을 끌어올렸다."
        result = guard.run_deep_validation(ms)
        compound = [v for v in result["violations"] if v["type"] == "wuxia_compound_pattern"]
        assert len(compound) >= 1

    def test_clean_fantasy_no_compound(self, guard):
        """순수 판타지 원고 → 복합 패턴 0건"""
        ms = "마법사는 마나를 집중하여 파이어볼 주문을 시전했다. 마법진이 빛나며 스킬이 발동했다."
        result = guard.run_deep_validation(ms)
        compound = [v for v in result["violations"] if v["type"] == "wuxia_compound_pattern"]
        assert len(compound) == 0

    def test_forbidden_term_promoted_to_high(self, guard):
        """핵심 무협 용어는 HIGH 승격"""
        ms = "그는 내공을 운용하여 진기를 끌어올렸다."
        result = guard.run_deep_validation(ms)
        high_terms = [
            v for v in result["violations"] if v.get("severity") == "HIGH" and v.get("type") == "forbidden_term"
        ]
        assert len(high_terms) >= 1

    def test_spell_tier_violation(self, guard):
        """견습 마법사의 상위 주문 사용 → violation"""
        ms = "견습 마법사가 시간 역행 마법을 시전했다."
        state = {"magic_tier": "견습"}
        result = guard.run_deep_validation(ms, state)
        tier_violations = [v for v in result["violations"] if v["type"] == "spell_tier_violation"]
        assert len(tier_violations) >= 1


# ============================================================
# [TF-16-06] _threshold() 키 ↔ validation.yaml 매핑 검증
# ============================================================
class TestThresholdKeyMapping:
    """_threshold()로 접근하는 validation.yaml 키가 None이 아닌 값을 반환하는지 확인."""

    def setup_method(self):
        """테스트 격리 — _threshold 캐시 리셋 (이전 테스트가 cfg=None으로 오염 방지)."""
        from modules.validation.threshold_helper import _threshold
        if hasattr(_threshold, "_cfg"):
            del _threshold._cfg

    @pytest.mark.parametrize("key,expected_type", [
        ("manuscript.min_length", int),
        ("manuscript.target_length", int),
        ("scoring.quality_gate_score", int),
        ("scoring.default_pass_threshold", int),
        ("scope.chars_per_scene", int),
        ("arc.ns3b_divergence_threshold", float),
        ("arc.jaccard_similarity_threshold", float),
        ("quality.cliche_window", int),
        ("ensemble_timeouts_validation.consensus_total", int),
        ("adaptive_grading.base_score_min", int),
        ("adaptive_grading.base_score_max", int),
        ("adaptive_grading.length_base_min", int),
        ("adaptive_grading.length_base_max", int),
        ("retry.director_max_attempts", int),
        ("patch_mode.rewrite_below", int),
        ("smart_retrieval.dense_k", int),
    ])
    def test_threshold_key_resolves(self, key, expected_type):
        """validation.yaml에 정의된 키가 _threshold()로 접근 시 기본값 이상의 값을 반환."""
        from modules.validation.threshold_helper import _threshold

        sentinel = object()
        result = _threshold(key, sentinel)
        assert result is not sentinel, f"키 '{key}'가 validation.yaml에 없음 (None fallback)"
        assert isinstance(result, expected_type), (
            f"키 '{key}': 기대 타입={expected_type.__name__}, 실제={type(result).__name__}"
        )
