"""
[Self-Audit Wave] Stage 3 Blueprint Self-Audit Checklist — Prompt Presence Tests

Verifies that BLUEPRINT_GENERATION_PROMPT in ensemble.yaml contains the
self-audit checklist section with the required structure.
"""

import re

from modules.core.prompt_loader import PromptLoader


def _load_blueprint_prompt() -> str:
    """Load BLUEPRINT_GENERATION_PROMPT via PromptLoader."""
    loader = PromptLoader()
    prompt = loader.load("ensemble", "BLUEPRINT_GENERATION_PROMPT")
    assert prompt is not None, "BLUEPRINT_GENERATION_PROMPT not found in ensemble.yaml"
    return prompt


class TestSelfAuditChecklistPresence:
    """The self-audit checklist exists in BLUEPRINT_GENERATION_PROMPT."""

    def test_checklist_header_present(self):
        prompt = _load_blueprint_prompt()
        assert "자가 검증 체크리스트" in prompt

    def test_checklist_has_at_least_five_checkboxes(self):
        prompt = _load_blueprint_prompt()
        checkbox_count = prompt.count("□")
        assert checkbox_count >= 5, f"Expected ≥5 checkbox items, found {checkbox_count}"

    def test_checklist_has_exactly_seven_checkboxes(self):
        prompt = _load_blueprint_prompt()
        checkbox_count = prompt.count("□")
        assert checkbox_count == 7, f"Expected 7 checkbox items, found {checkbox_count}"

    def test_verify_before_output_instruction_present(self):
        prompt = _load_blueprint_prompt()
        assert "수정한 후 출력" in prompt or "수정한 후" in prompt


class TestSelfAuditChecklistPlacement:
    """The checklist is between [필수 조건] and [V67] 모순 방지."""

    def test_checklist_after_required_conditions(self):
        prompt = _load_blueprint_prompt()
        required_pos = prompt.find("필수 조건")
        checklist_pos = prompt.find("자가 검증 체크리스트")
        assert required_pos >= 0, "[필수 조건] section not found"
        assert checklist_pos >= 0, "Self-audit checklist not found"
        assert checklist_pos > required_pos, "Checklist must come after [필수 조건]"

    def test_checklist_before_contradiction_prevention(self):
        prompt = _load_blueprint_prompt()
        checklist_pos = prompt.find("자가 검증 체크리스트")
        contradiction_pos = prompt.find("[V67] 모순 방지")
        assert checklist_pos >= 0, "Self-audit checklist not found"
        assert contradiction_pos >= 0, "[V67] 모순 방지 section not found"
        assert checklist_pos < contradiction_pos, "Checklist must come before [V67] 모순 방지"


class TestSelfAuditChecklistContent:
    """The checklist covers the required B1-B5 derived items."""

    def test_continuity_item_present(self):
        prompt = _load_blueprint_prompt()
        assert "ending_hook" in prompt.lower() or "cliffhanger" in prompt.lower()

    def test_item_consistency_present(self):
        prompt = _load_blueprint_prompt()
        assert "아이템" in prompt or "무공" in prompt

    def test_scene_specificity_present(self):
        prompt = _load_blueprint_prompt()
        assert "씬" in prompt and ("구체적" in prompt or "사건" in prompt)

    def test_scenario_density_present(self):
        prompt = _load_blueprint_prompt()
        assert "integrated_scenario" in prompt and "1000" in prompt

    def test_location_continuity_present(self):
        prompt = _load_blueprint_prompt()
        assert "start_location" in prompt or "end_location" in prompt

    def test_scope_adherence_present(self):
        prompt = _load_blueprint_prompt()
        assert "tactical_doc" in prompt and ("초과" in prompt or "범위" in prompt)


class TestStage3AuthorityContract:
    """The prompt carries the anti-contamination authority contract."""

    def test_stage3_scene_authority_contract_present(self):
        prompt = _load_blueprint_prompt()
        assert "Stage3 장면 권위 계약" in prompt
        assert "scene_breakdown.key_events" in prompt

    def test_stage3_anti_ui_and_cross_genre_contract_present(self):
        prompt = _load_blueprint_prompt()
        assert "안티 HUD / 안티 시스템 UI" in prompt
        assert "안티 크로스 장르 오염" in prompt


class TestNoNewTemplateVariables:
    """The checklist does not introduce new template variables."""

    def test_no_new_braces_in_checklist_section(self):
        prompt = _load_blueprint_prompt()
        start = prompt.find("자가 검증 체크리스트")
        end = prompt.find("위 항목 중 하나라도", start)
        assert start >= 0 and end >= 0, "Could not isolate checklist section"
        checklist_section = prompt[start:end]
        brace_matches = re.findall(r"\{[a-z_]+\}", checklist_section)
        assert len(brace_matches) == 0, f"Unexpected template variables in checklist: {brace_matches}"
