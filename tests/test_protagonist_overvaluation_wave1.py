"""Protagonist overvaluation wave 1 integration tests.

Tests:
- BLUEPRINT_GENERATION_PROMPT contains staging guidance block
- WorkGuard protagonist_evaluation blueprint retrieval-contract surfacing
- backward compat: absent protagonist_evaluation does not break existing flows
"""

import textwrap
from pathlib import Path

import pytest
import yaml


# ── helpers ───────────────────────────────────────────────────


class _MockBaseGuard:
    def __init__(self):
        self.FORBIDDEN_TERMS = []
        self.ALLOWED_TERMS = []
        self.MANDATORY_CONCEPTS = []

    def get_genre_name(self):
        return "TEST"

    def get_v20_purism_prompt(self):
        return "base"

    def get_impossible_actions(self, current_state=None):
        return []

    def get_justification_patterns(self):
        return []

    def get_hierarchy_rules(self):
        return {}

    def check_state_action_consistency(self, manuscript, current_state):
        return {"violations": []}

    def run_deep_validation(self, manuscript, current_state=None):
        return {
            "has_critical": False,
            "violations": [],
            "summary": "",
            "feedback": "",
        }


def _write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "work_guard.yaml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ── BLUEPRINT_GENERATION_PROMPT staging block ─────────────────


class TestBlueprintStagingBlock:
    @pytest.fixture(scope="class")
    def blueprint_prompt(self):
        prompt_path = Path(__file__).resolve().parent.parent / "config" / "prompts" / "ensemble.yaml"
        with open(prompt_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data["BLUEPRINT_GENERATION_PROMPT"]

    def test_staging_block_present(self, blueprint_prompt):
        assert "주인공 고평가 연출 가이드" in blueprint_prompt

    def test_observer_allocation_guidance(self, blueprint_prompt):
        assert "관찰자 배분" in blueprint_prompt

    def test_information_asymmetry_guidance(self, blueprint_prompt):
        assert "정보 비대칭" in blueprint_prompt

    def test_reveal_ordering_guidance(self, blueprint_prompt):
        assert "공개 순서" in blueprint_prompt

    def test_show_not_tell_guidance(self, blueprint_prompt):
        assert "보여주기 원칙" in blueprint_prompt

    def test_forbidden_patterns_listed(self, blueprint_prompt):
        assert "큰 숫자 자체로 감동 유발" in blueprint_prompt
        assert "균일 반응" in blueprint_prompt
        assert "서술자가 직접 주인공을 찬양" in blueprint_prompt
        assert "즉시 인정" in blueprint_prompt

    def test_no_new_template_variables(self, blueprint_prompt):
        import re
        # existing variables are {ep_num}, {protagonist_name}, etc.
        # ensure no NEW protagonist_evaluation variable was introduced
        all_vars = set(re.findall(r"\{(\w+)\}", blueprint_prompt))
        assert "protagonist_evaluation" not in all_vars
        assert "admiration_axes" not in all_vars
        assert "forbidden_praise_patterns" not in all_vars

    def test_staging_block_before_output_format(self, blueprint_prompt):
        staging_idx = blueprint_prompt.index("주인공 고평가 연출 가이드")
        output_idx = blueprint_prompt.index("출력 형식 - 반드시 JSON만 출력")
        assert staging_idx < output_idx


# ── WorkGuard blueprint retrieval contract with protagonist_evaluation ──


class TestBlueprintRetrievalContractWithProtagonistEval:
    def test_full_protagonist_evaluation_contract(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              tracking_slots:
                - "무공 계보"
              protagonist_evaluation:
                admiration_axes:
                  - "method_quality"
                  - "conditional_reversal"
                  - "information_asymmetry"
                  - "hierarchy_shock"
                forbidden_praise_patterns:
                  - "big_number_wow"
                  - "uniform_reaction"
                  - "narrator_hype"
                  - "instant_recognition"
                observer_tiers:
                  - "일반 무인"
                  - "장로급"
                  - "적대 고수"
                evaluation_thresholds:
                  - "2화 이상 간격 두고 감탄"
                  - "같은 관찰자 연속 감탄 금지"
        """,
        )
        guard = WorkGuard(_MockBaseGuard(), p)
        contract = guard.get_retrieval_contract_prompt("blueprint")

        assert "method_quality" in contract
        assert "hierarchy_shock" in contract
        assert "big_number_wow" in contract
        assert "narrator_hype" in contract
        assert "장로급" in contract
        assert "2화 이상 간격" in contract

    def test_empty_protagonist_evaluation_no_contract_lines(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              tracking_slots:
                - "핵심 라인"
              protagonist_evaluation: {}
        """,
        )
        guard = WorkGuard(_MockBaseGuard(), p)
        contract = guard.get_retrieval_contract_prompt("blueprint")

        assert "주인공 감탄 축" not in contract

    def test_protagonist_evaluation_only_in_blueprint_stage(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              tracking_slots:
                - "핵심 라인"
              protagonist_evaluation:
                admiration_axes:
                  - "method_quality"
        """,
        )
        guard = WorkGuard(_MockBaseGuard(), p)

        for stage in ("volume", "arc", "block", "manuscript"):
            contract = guard.get_retrieval_contract_prompt(stage)
            assert "주인공 감탄 축" not in contract, f"protagonist_evaluation leaked into stage={stage}"


# ── backward compat ──────────────────────────────────────────


class TestBackwardCompat:
    def test_no_protagonist_evaluation_still_works(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(
            tmp_path,
            """\
            work_identity:
              work_type: "현대물"
              tracking_slots:
                - "자금 라인"
        """,
        )
        guard = WorkGuard(_MockBaseGuard(), p)

        prompt = guard.get_v20_purism_prompt()
        assert "작품 유형: 현대물" in prompt
        assert "주인공 감탄 축" not in prompt

        contract = guard.get_retrieval_contract_prompt("blueprint")
        assert "자금 라인" in contract
        assert "주인공 감탄 축" not in contract

    def test_empty_yaml_backward_compat(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(tmp_path, "")
        guard = WorkGuard(_MockBaseGuard(), p)
        assert guard.get_v20_purism_prompt() == "base"
        assert guard.get_retrieval_contract_prompt("blueprint") == ""

    def test_deep_validation_unchanged_without_protagonist_eval(self, tmp_path):
        from modules.core.genre_guards.work_guard import WorkGuard

        p = _write_yaml(tmp_path, "")
        guard = WorkGuard(_MockBaseGuard(), p)
        result = guard.run_deep_validation("clean manuscript", {})
        assert result["has_critical"] is False
        assert result["has_warning"] is False
