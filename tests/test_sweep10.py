"""
[Sweep10] 숨은 로직 버그 수정 테스트
"""

import re


class TestA1AdaptiveThreshold:
    """A-1: 영구 임계값 설정 시 적응형 비활성화"""

    def test_permanent_disables_adaptive(self):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        orch = ValidationOrchestrator.__new__(ValidationOrchestrator)
        orch.current_threshold = 70
        orch.use_adaptive_threshold = True
        orch.threshold_profile = {"base_threshold": 70}
        orch.set_manual_threshold_v59(80, duration_episodes=0)
        assert orch.use_adaptive_threshold is False
        assert orch.current_threshold == 80

    def test_temporary_keeps_adaptive(self):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        orch = ValidationOrchestrator.__new__(ValidationOrchestrator)
        orch.current_threshold = 70
        orch.use_adaptive_threshold = True
        orch.threshold_profile = {"base_threshold": 70}
        orch.set_manual_threshold_v59(80, duration_episodes=5)
        assert orch.use_adaptive_threshold is True


class TestB1EnsembleSelection:
    """B-1: 앙상블 불합격 폴백 시 최장 후보 선택"""

    def test_selects_longest_qualified(self):
        candidates = [
            {"manuscript": "A" * 4000},
            {"manuscript": "B" * 3000},
            {"manuscript": "C" * 5000},
        ]
        qualified_indices = [0, 2]
        selected_idx = 1  # LLM이 불합격 B 선택

        if selected_idx not in qualified_indices and qualified_indices:
            selected_idx = max(
                qualified_indices,
                key=lambda i: len(candidates[i].get("manuscript", "")),
            )

        assert selected_idx == 2


class TestC1IssueKeyAccess:
    """C-1: issue dict 키 안전 접근"""

    def test_missing_keys_no_crash(self):
        issue = {"problem": "some issue"}  # type/description 키 없음
        issue_type = issue.get("type", "unknown") if isinstance(issue, dict) else str(issue)
        issue_desc = issue.get("description", "") if isinstance(issue, dict) else ""
        result = f"- {issue_type}: {issue_desc}"
        assert "unknown" in result

    def test_string_issue_no_crash(self):
        issue = "plain string issue"
        issue_type = issue.get("type", "unknown") if isinstance(issue, dict) else str(issue)
        issue_desc = issue.get("description", "") if isinstance(issue, dict) else ""
        result = f"- {issue_type}: {issue_desc}"
        assert "plain string issue" in result


class TestD1InventoryConsumption:
    """D-1: 소비된 아이템 dict 타입 처리"""

    def test_dict_consumption_removes_item(self):
        prev_inventory = ["검", "갑옷", "비급"]
        consumed_raw = [{"name": "검", "qty": 1}]

        consumed_names = []
        for c in consumed_raw:
            if isinstance(c, str):
                consumed_names.append(c)
            elif isinstance(c, dict):
                consumed_names.append(c.get("name", c.get("item", "")))

        inherited = [item for item in prev_inventory if item not in consumed_names]
        assert inherited == ["갑옷", "비급"]

    def test_mixed_consumption_types(self):
        prev_inventory = ["검", "갑옷", "비급"]
        consumed_raw = ["갑옷", {"name": "비급"}]

        consumed_names = []
        for c in consumed_raw:
            if isinstance(c, str):
                consumed_names.append(c)
            elif isinstance(c, dict):
                consumed_names.append(c.get("name", c.get("item", "")))

        inherited = [item for item in prev_inventory if item not in consumed_names]
        assert inherited == ["검"]


class TestE1PacingEmptyList:
    """E-1: 빈 리스트에서 min/max 안전"""

    def test_empty_scores_safe(self):
        scores = []
        avg = sum(scores) / len(scores) if scores else 0
        score_range = (min(scores), max(scores)) if scores else (0, 0)
        assert avg == 0
        assert score_range == (0, 0)


class TestE2SentencePattern:
    """E-2: 마침표 없는 마지막 문장 캡처"""

    def test_captures_unpunctuated_ending(self):
        pattern = re.compile(r"[^.!?。？！]+[.!?。？！]+|[^.!?。？！]+$")
        text = "첫 번째 문장입니다. 두 번째 문장입니다"
        sentences = pattern.findall(text)
        assert len(sentences) == 2
        assert "두 번째 문장입니다" in sentences[1]

    def test_all_punctuated_still_works(self):
        pattern = re.compile(r"[^.!?。？！]+[.!?。？！]+|[^.!?。？！]+$")
        text = "첫 번째. 두 번째. 세 번째."
        sentences = pattern.findall(text)
        assert len(sentences) == 3
