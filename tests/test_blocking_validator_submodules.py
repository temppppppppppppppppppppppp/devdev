"""[R5-2a] BlockingValidator submodule unit tests."""

from modules.validation.blocking_validator import BlockingValidator


def _base_context() -> dict:
    return {
        "mode": "MANUSCRIPT",
        "encyclopedia": {"npcs": [], "items": [], "locations": []},
        "martial_hud": {"actual_truth": {"equipment": []}},
    }


class TestEntityChecks:
    def test_dead_npc_recall_allowed(self):
        validator = BlockingValidator()
        manuscript = "그는 회상 속에서 무영의 마지막 말을 떠올렸다."
        context = {"encyclopedia": {"npcs": [{"name": "무영", "status": "dead", "aliases": []}]}}

        result = validator.entity_checks._check_dead_npc_resurrection(manuscript, context)

        assert result["passed"] is True

    def test_dead_npc_action_blocked(self):
        validator = BlockingValidator()
        manuscript = '무영이 말했다. "이제 끝이다."'
        context = {"encyclopedia": {"npcs": [{"name": "무영", "status": "dead", "aliases": []}]}}

        result = validator.entity_checks._check_dead_npc_resurrection(manuscript, context)

        assert result["passed"] is False
        assert result["check"] == "dead_npc_resurrection"

    def test_unowned_item_detected(self):
        validator = BlockingValidator()
        manuscript = "그는 천상검을 사용해 벽을 부쉈다."
        context = {
            "encyclopedia": {"items": [{"name": "천상검", "aliases": []}]},
            "martial_hud": {"actual_truth": {"equipment": []}},
        }

        result = validator.entity_checks._check_unowned_item_usage(manuscript, context)

        assert result["passed"] is False
        assert result["check"] == "unowned_item_usage"

    def test_damaged_item_usage_detected(self):
        validator = BlockingValidator()
        manuscript = "그는 장검을 휘둘렀다."
        context = {"item_states": {"장검": "파괴"}}

        result = validator.entity_checks._check_damaged_item_usage(manuscript, context)

        assert result["passed"] is False
        assert result["check"] == "damaged_item_usage"

    def test_destroyed_location_visit_detected(self):
        validator = BlockingValidator()
        manuscript = "그는 마을로 들어갔다."
        context = {"encyclopedia": {"locations": [{"name": "마을", "status": "destroyed"}]}}

        result = validator.entity_checks._check_destroyed_location_visit(manuscript, context)

        assert result["passed"] is False
        assert result["check"] == "destroyed_location_visit"


class TestSceneChecks:
    def test_minimum_length_pass(self):
        validator = BlockingValidator()
        manuscript = "가" * 5000

        result = validator.scene_checks._check_minimum_length(manuscript, {"mode": "MANUSCRIPT"})

        assert result["passed"] is True

    def test_minimum_length_fail(self):
        validator = BlockingValidator()
        manuscript = "가" * 100

        result = validator.scene_checks._check_minimum_length(manuscript, {"mode": "MANUSCRIPT"})

        assert result["passed"] is False
        assert result["check"] == "minimum_length"

    def test_required_scenes_calls_keyword_extractor(self):
        validator = BlockingValidator()
        manuscript = "장터 도착 결투 승리 귀환 보상"
        context = {
            "mode": "MANUSCRIPT",
            "blueprint": {
                "scene_breakdown": {
                    "scene_1": {"description": "장터 도착"},
                    "scene_2": {"description": "결투 준비"},
                    "scene_3": {"description": "승리"},
                    "scene_4": {"description": "귀환 보상"},
                }
            },
        }

        result = validator.scene_checks._check_required_scenes(manuscript, context)

        assert result["check"] == "required_scenes"
        assert isinstance(result["passed"], bool)

    def test_scope_overflow_smoke(self):
        validator = BlockingValidator()
        manuscript = "가" * 5000
        context = {"mode": "MANUSCRIPT", "blueprint": {"scene_breakdown": {}}}

        result = validator.scene_checks._check_scope_overflow(manuscript, context)

        assert result["check"] == "scope_overflow"
        assert isinstance(result["passed"], bool)

    def test_strength_grade(self):
        validator = BlockingValidator()
        assert validator.scene_checks._get_strength_grade(85) == "S"


class TestConsistencyChecks:
    def test_extract_keywords(self):
        validator = BlockingValidator()
        keywords = validator.consistency_checks._extract_keywords("천상검을 들고 무림맹으로 향했다.")

        assert isinstance(keywords, list)
        assert len(keywords) <= 3

    def test_relationship_consistency_without_context(self):
        validator = BlockingValidator(context=None)
        result = validator.consistency_checks._check_relationship_consistency(
            manuscript="테스트 원고",
            context={"encyclopedia": {"npcs": []}, "ep_num": 1},
        )

        assert result["passed"] is True

    def test_information_consistency_without_context(self):
        validator = BlockingValidator(context=None)
        result = validator.consistency_checks._check_information_consistency(
            manuscript="테스트 원고",
            context={"encyclopedia": {"npcs": []}, "ep_num": 1},
        )

        assert result["passed"] is True


class TestIntegration:
    def test_validate_runs(self):
        validator = BlockingValidator(enable_justification_checks=False)
        manuscript = "가" * 5000
        context = _base_context()
        context["mode"] = "BLUEPRINT"

        result = validator.validate(manuscript, context)

        assert result["tier"] == "BLOCKING"
        assert "failures" in result

    def test_lazy_init(self):
        validator = BlockingValidator()
        assert validator._entity_checks is None
        assert validator._scene_checks is None
        assert validator._consistency_checks is None

        _ = validator.entity_checks
        _ = validator.scene_checks
        _ = validator.consistency_checks

        assert validator._entity_checks is not None
        assert validator._scene_checks is not None
        assert validator._consistency_checks is not None


class TestDegradedCheck:
    """[C-03] Degraded blocking check counter and warning."""

    def test_degraded_counter_increments(self):
        """양쪽 모두 degraded일 때 카운터 증가"""
        validator = BlockingValidator()
        ctx = _base_context()
        ctx["encyclopedia"]["npcs"] = []
        # 양쪽 모두 exception 발생하도록 consistency_checks mock
        from unittest.mock import MagicMock

        mock_cc = MagicMock()
        mock_cc._check_relationship_consistency.side_effect = RuntimeError("test")
        mock_cc._check_information_consistency.side_effect = RuntimeError("test")
        validator._consistency_checks = mock_cc
        result = validator.validate("테스트 원고 " * 500, ctx)
        assert validator._degraded_count >= 1
        assert "degraded_checks" in result
        assert len(result["degraded_checks"]) == 2

    def test_single_degraded_no_all_warning(self):
        """한쪽만 degraded면 all-degraded 경고 없음"""
        validator = BlockingValidator()
        ctx = _base_context()
        from unittest.mock import MagicMock

        mock_cc = MagicMock()
        mock_cc._check_relationship_consistency.side_effect = RuntimeError("test")
        mock_cc._check_information_consistency.return_value = {"passed": True}
        validator._consistency_checks = mock_cc
        result = validator.validate("테스트 원고 " * 500, ctx)
        assert result.get("degraded_checks") is None or len(result.get("degraded_checks", [])) < 2
