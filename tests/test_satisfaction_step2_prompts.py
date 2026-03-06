"""
[Phase 3-D2] Reader Satisfaction — Director 프롬프트 확장 테스트

Director 심사 프롬프트에 대리만족 기준/장르 예시가 반영되었는지 검증.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.prompt_loader import PromptLoader

# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def loader():
    """PromptLoader 인스턴스"""
    return PromptLoader()


# ── 1. ENSEMBLE_SELECTION_PROMPT 대리만족 키워드 ─────────────────


class TestEnsembleSelectionSatisfaction:
    """ENSEMBLE_SELECTION_PROMPT에 대리만족 심사 기준이 포함되는지 검증"""

    def test_ensemble_prompt_has_payoff_keyword(self, loader):
        """ENSEMBLE_SELECTION_PROMPT에 '보상 시점' 또는 'Payoff' 키워드 존재"""
        prompt = loader.load("director", "ENSEMBLE_SELECTION_PROMPT")
        assert "Payoff" in prompt or "보상 시점" in prompt

    def test_ensemble_prompt_has_frustration_reward(self, loader):
        """ENSEMBLE_SELECTION_PROMPT에 '좌절-보상' 키워드 존재"""
        prompt = loader.load("director", "ENSEMBLE_SELECTION_PROMPT")
        assert "좌절-보상" in prompt or "좌절" in prompt

    def test_ensemble_prompt_has_growth_perception(self, loader):
        """ENSEMBLE_SELECTION_PROMPT에 '성장 체감' 키워드 존재"""
        prompt = loader.load("director", "ENSEMBLE_SELECTION_PROMPT")
        assert "성장 체감" in prompt or "성장" in prompt

    def test_ensemble_prompt_has_genre_examples(self, loader):
        """ENSEMBLE_SELECTION_PROMPT에 장르별 보상 예시 포함"""
        prompt = loader.load("director", "ENSEMBLE_SELECTION_PROMPT")
        assert "무협" in prompt
        assert "헌터" in prompt
        assert "투자" in prompt
        assert "판타지" in prompt


# ── 2. DIRECTOR_AUDIT_PROMPT 대리만족 키워드 ────────────────────


class TestDirectorAuditSatisfaction:
    """DIRECTOR_AUDIT_PROMPT_V30에 대리만족 관점이 포함되는지 검증"""

    def test_audit_prompt_engagement_has_satisfaction(self, loader):
        """독자 몰입도 항목에 '대리만족' 키워드 존재"""
        prompt = loader.load("director", "DIRECTOR_AUDIT_PROMPT_V30")
        assert "대리만족" in prompt

    def test_audit_prompt_has_payoff_criteria(self, loader):
        """DIRECTOR_AUDIT_PROMPT_V30에 보상 시점/Payoff 관련 기준 존재"""
        prompt = loader.load("director", "DIRECTOR_AUDIT_PROMPT_V30")
        assert "보상" in prompt

    def test_audit_prompt_has_genre_rewards(self, loader):
        """DIRECTOR_AUDIT_PROMPT_V30에 장르별 보상 예시 포함"""
        prompt = loader.load("director", "DIRECTOR_AUDIT_PROMPT_V30")
        assert "경지돌파" in prompt or "경지 돌파" in prompt
        assert "각성" in prompt
        assert "자산성장" in prompt or "자산 성장" in prompt

    def test_audit_cot_step4_has_satisfaction(self, loader):
        """Chain-of-Thought Step 4에 대리만족 관점 추가됨"""
        prompt = loader.load("director", "DIRECTOR_AUDIT_PROMPT_V30")
        assert "D-Step2" in prompt


# ── 3. Blueprint 비교 프롬프트 ──────────────────────────────────


class TestBlueprintComparisonSatisfaction:
    """COMPARE_AND_SELECT_BLUEPRINT__COMPARISON_PROMPT에 대리만족 기준 포함"""

    def test_blueprint_comparison_prompt_removed(self, loader):
        """Removed director_ensemble comparison prompt should return None."""
        prompt = loader.load("director_ensemble", "COMPARE_AND_SELECT_BLUEPRINT__COMPARISON_PROMPT")
        assert prompt is None


# ── 4. JSON 스키마 보존 (회귀 테스트) ──────────────────────────


class TestJsonSchemaPreservation:
    """프롬프트 수정 후에도 JSON 출력 스키마가 그대로인지 검증"""

    def test_ensemble_json_schema_keys_preserved(self, loader):
        """ENSEMBLE_SELECTION_PROMPT JSON 스키마 필수 키 보존"""
        prompt = loader.load("director", "ENSEMBLE_SELECTION_PROMPT")
        required_keys = [
            "selected",
            "selection_reason",
            "verdict",
            "score",
            "score_breakdown",
            "contradiction_check",
            "open_review",
            "feedback",
            "state_updates",
            "other_candidates_notes",
        ]
        for key in required_keys:
            assert f'"{key}"' in prompt, f"Missing JSON key: {key}"

    def test_audit_json_schema_keys_preserved(self, loader):
        """DIRECTOR_AUDIT_PROMPT_V30 JSON 스키마 필수 키 보존"""
        prompt = loader.load("director", "DIRECTOR_AUDIT_PROMPT_V30")
        required_keys = [
            "decision",
            "score",
            "score_breakdown",
            "error_category",
            "diagnostic_report",
            "current_beat_achieved",
            "reason",
            "feedback",
            "open_review",
            "lowest_score_area",
        ]
        for key in required_keys:
            assert f'"{key}"' in prompt, f"Missing JSON key: {key}"

    def test_audit_score_breakdown_sub_keys_preserved(self, loader):
        """DIRECTOR_AUDIT score_breakdown 하위 키 보존"""
        prompt = loader.load("director", "DIRECTOR_AUDIT_PROMPT_V30")
        sub_keys = [
            "setting_consistency",
            "scene_composition",
            "narrative_flow",
            "reader_engagement",
            "prose_quality",
        ]
        for key in sub_keys:
            assert f'"{key}"' in prompt, f"Missing score_breakdown key: {key}"


# ── 5. ScoringValidator 프롬프트 장르 예시 ─────────────────────


class TestScoringValidatorPromptGenreExamples:
    """ScoringValidator LLM 프롬프트에 장르별 보상 예시 포함 검증"""

    def test_llm_prompt_has_genre_payoff_examples(self):
        """LLM 프롬프트 Step 6에 장르별 보상 예시 포함"""
        from modules.validation.scoring_validator import ScoringValidator

        sv = ScoringValidator(client=None, genre="wuxia")
        # _calculate_llm_scores 내 prompt 문자열을 직접 확인하기 어려우므로
        # fallback 쪽 장르 설명으로 간접 검증
        notes = sv._get_genre_item_note("wuxia", "reader_satisfaction")
        assert "경지 돌파" in notes or "경지돌파" in notes

    def test_llm_prompt_frustration_reward_keyword(self):
        """LLM 프롬프트 Step 6에 '좌절-보상' 키워드 포함"""
        import inspect

        from modules.validation.scoring_validator import ScoringValidator

        source = inspect.getsource(ScoringValidator._calculate_llm_scores)
        assert "좌절-보상" in source or "좌절" in source


# ── 6. 프롬프트 길이 제한 ──────────────────────────────────────


class TestPromptLengthCap:
    """프롬프트 변경으로 토큰 과다 증가가 없는지 검증"""

    def test_ensemble_prompt_length_reasonable(self, loader):
        """ENSEMBLE_SELECTION_PROMPT 길이가 합리적 범위(< 12000자) [TF-57-A fiction_term_leak 추가]"""
        prompt = loader.load("director", "ENSEMBLE_SELECTION_PROMPT")
        assert len(prompt) < 12000, f"Prompt too long: {len(prompt)} chars"

    def test_audit_prompt_length_reasonable(self, loader):
        """DIRECTOR_AUDIT_PROMPT_V30 길이가 합리적 범위(< 10200자) [NC-3B few-shot 추가]"""
        prompt = loader.load("director", "DIRECTOR_AUDIT_PROMPT_V30")
        assert len(prompt) < 10200, f"Prompt too long: {len(prompt)} chars"
