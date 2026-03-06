"""BUG-A: 금지 아이템 오탐 수정 — 기존 소지품 화이트리스트 테스트

pipeline-run-audit-01_20260306.md 테스트 계획 5건 전량 구현.
"""

from unittest.mock import MagicMock

from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator


def _make_ensemble() -> ArcEnsembleGenerator:
    ens = object.__new__(ArcEnsembleGenerator)
    ens.host = MagicMock()
    return ens


def _base_candidate(**overrides) -> dict:
    """평가에 필요한 최소 후보 dict."""
    c = {
        "arc_no": 1,
        "ep_count": 4,
        "tactical_doc": "",
        "joint_docs": "docs",
        "state_constraints": {"arc_start_state": {"equipment": []}},
        "state_changes": "changes",
    }
    c.update(overrides)
    return c


class TestForbiddenItemWhitelist:
    """BUG-A 테스트 6건 (감사 문서 TC 1~5 + 실전 재현 1건)."""

    def test_skip_existing_equipment(self):
        """TC-1: arc_start_state.equipment에 있는 아이템은 오탐 없어야 함."""
        ens = _make_ensemble()
        candidate = _base_candidate(
            tactical_doc="장비: 블랙베리 스마트폰. 획득: 금 선물 숏 포지션.",
            state_constraints={
                "arc_start_state": {"equipment": ["블랙베리 스마트폰"]},
            },
        )
        score, issues = ens._evaluate_candidate(
            candidate,
            prev_arc_context="",
            constraint_block="",
            prev_equipment=None,
            forbidden_items=["블랙베리 스마트폰"],
        )
        assert not any("금지 아이템" in i for i in issues), f"오탐 발생: {issues}"

    def test_new_acquisition_still_caught(self):
        """TC-2: 새로 획득한 금지 아이템은 여전히 감지되어야 함."""
        ens = _make_ensemble()
        candidate = _base_candidate(
            state_constraints={
                "arc_start_state": {"equipment": []},
                "items_acquired": ["비밀 장부"],
            },
        )
        score, issues = ens._evaluate_candidate(
            candidate,
            prev_arc_context="",
            constraint_block="",
            prev_equipment=[],
            forbidden_items=["비밀 장부"],
        )
        assert any("금지 아이템 획득 시도: 비밀 장부" in i for i in issues)

    def test_prev_equipment_whitelist(self):
        """TC-3: prev_equipment에 있는 아이템도 화이트리스트 적용."""
        ens = _make_ensemble()
        candidate = _base_candidate(
            tactical_doc="법인인감을 획득하여 서류를 처리했다.",
            state_constraints={"arc_start_state": {"equipment": []}},
        )
        score, issues = ens._evaluate_candidate(
            candidate,
            prev_arc_context="",
            constraint_block="",
            prev_equipment=["법인인감"],
            forbidden_items=["법인인감"],
        )
        assert not any("금지 아이템" in i for i in issues), f"오탐 발생: {issues}"

    def test_no_prev_equipment_first_arc(self):
        """TC-4: 첫 Arc (prev_equipment=[]) — 화이트리스트 비어있으므로 정상 감지."""
        ens = _make_ensemble()
        candidate = _base_candidate(
            state_constraints={
                "arc_start_state": {"equipment": []},
                "items_acquired": ["비밀 장부"],
            },
        )
        score, issues = ens._evaluate_candidate(
            candidate,
            prev_arc_context="",
            constraint_block="",
            prev_equipment=[],
            forbidden_items=["비밀 장부"],
        )
        assert any("금지 아이템 획득 시도: 비밀 장부" in i for i in issues)

    def test_items_acquired_existing_equipment_skip(self):
        """TC-5: items_acquired에 기존 소지품이 포함된 경우 — 화이트리스트로 스킵."""
        ens = _make_ensemble()
        candidate = _base_candidate(
            state_constraints={
                "arc_start_state": {"equipment": ["법인인감"]},
                "items_acquired": ["법인인감"],  # LLM 오류로 기존 소지품이 acquired에 포함
            },
        )
        score, issues = ens._evaluate_candidate(
            candidate,
            prev_arc_context="",
            constraint_block="",
            prev_equipment=[],
            forbidden_items=["법인인감"],
        )
        assert not any("금지 아이템" in i for i in issues), f"기존 소지품인데 오탐: {issues}"

    def test_tactical_false_positive_prevented(self):
        """실전 재현: tactical에 '획득'과 아이템명이 별개 문맥에 존재하는 경우."""
        ens = _make_ensemble()
        candidate = _base_candidate(
            tactical_doc=(
                "[시작 상태]\n장비: 2006년식 피처폰, 블랙베리 스마트폰\n"
                "[종료 상태]\n획득/소모: 금 선물 숏 포지션 진입"
            ),
            state_constraints={
                "arc_start_state": {
                    "equipment": ["2006년식 피처폰", "블랙베리 스마트폰"],
                },
            },
        )
        score, issues = ens._evaluate_candidate(
            candidate,
            prev_arc_context="",
            constraint_block="",
            prev_equipment=["2006년식 피처폰", "블랙베리 스마트폰"],
            forbidden_items=["2006년식 피처폰", "블랙베리 스마트폰"],
        )
        forbidden_issues = [i for i in issues if "금지 아이템" in i]
        assert len(forbidden_issues) == 0, f"실전 오탐 재현: {forbidden_issues}"
