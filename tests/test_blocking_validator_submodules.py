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

    def test_required_scenes_passes_when_two_of_two_scenes_found(self):
        validator = BlockingValidator()
        manuscript = "주인공은 객잔에 도착했다. 이후 비밀 문서를 확보했다."
        context = {
            "mode": "MANUSCRIPT",
            "blueprint": {
                "scene_breakdown": {
                    "scene_1": {"description": "객잔 도착"},
                    "scene_2": {"description": "비밀 문서 확보"},
                }
            },
        }

        result = validator.scene_checks._check_required_scenes(manuscript, context)

        assert result["check"] == "required_scenes"
        assert result["passed"] is True

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

    # ── [Wave-TR1] Wuxia technique-vs-realm consistency ─────────────

    def test_wuxia_realm_mismatch_detected(self):
        """입문 경지에서 검기 사용 시 실패."""
        validator = BlockingValidator()
        manuscript = "주인공은 검기를 발출하여 적을 베었다."
        context = {
            "genre": "wuxia",
            "martial_hud": {"actual_truth": {"realm": "입문"}},
        }

        result = validator.consistency_checks._check_wuxia_technique_realm_consistency(manuscript, context)

        assert result["passed"] is False
        assert result["check"] == "wuxia_technique_realm"
        assert result["forbidden_technique"] == "검기"
        assert result["realm"] == "입문"

    def test_wuxia_realm_allowed_passes(self):
        """절정 경지에서 검기 사용은 허용."""
        validator = BlockingValidator()
        manuscript = "주인공은 검기를 발출하여 적을 베었다."
        context = {
            "genre": "wuxia",
            "martial_hud": {"actual_truth": {"realm": "절정"}},
        }

        result = validator.consistency_checks._check_wuxia_technique_realm_consistency(manuscript, context)

        assert result["passed"] is True

    def test_wuxia_realm_absent_noop(self):
        """경지 미확인 시 no-op."""
        validator = BlockingValidator()
        manuscript = "주인공은 검기를 발출하여 적을 베었다."
        context = {
            "genre": "wuxia",
            "martial_hud": {"actual_truth": {}},
        }

        result = validator.consistency_checks._check_wuxia_technique_realm_consistency(manuscript, context)

        assert result["passed"] is True

    def test_wuxia_realm_non_wuxia_genre_noop(self):
        """비무협 장르에서는 no-op."""
        validator = BlockingValidator()
        manuscript = "주인공은 검기를 발출하여 적을 베었다."
        context = {
            "genre": "hunter",
            "martial_hud": {"actual_truth": {"realm": "입문"}},
        }

        result = validator.consistency_checks._check_wuxia_technique_realm_consistency(manuscript, context)

        assert result["passed"] is True

    def test_wuxia_realm_negation_context_passes(self):
        """부정 문맥(사용 불가 서술)은 허용."""
        validator = BlockingValidator()
        manuscript = "주인공은 아직 경지가 낮아 검기를 쓸 수 없었다."
        context = {
            "genre": "wuxia",
            "martial_hud": {"actual_truth": {"realm": "입문"}},
        }

        result = validator.consistency_checks._check_wuxia_technique_realm_consistency(manuscript, context)

        assert result["passed"] is True

    def test_wuxia_realm_facade_integration(self):
        """BlockingValidator facade를 통한 호출 확인."""
        validator = BlockingValidator()
        manuscript = "주인공은 검강을 날렸다."
        context = {
            "genre": "wuxia",
            "martial_hud": {"actual_truth": {"realm": "삼류"}},
        }

        result = validator._check_wuxia_technique_realm_consistency(manuscript, context)

        assert result["passed"] is False
        assert result["forbidden_technique"] == "검강"


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


class TestSceneCompletenessRegression:
    """[pre-rerun] 씬 완성도 체크가 마크다운 씬 헤더를 인식하는지 검증."""

    def test_markdown_scene_headers_pass(self):
        """### 씬 N: 형식 헤더가 있는 원고는 0/5 오탐이 아닌 PASS."""
        validator = BlockingValidator()
        manuscript = (
            "### 씬 1: 보이지 않는 감시망\n"
            + "가" * 400
            + "\n### 씬 2: 자산 청산 작전\n"
            + "나" * 400
            + "\n### 씬 3: 뒤따르는 그림자\n"
            + "다" * 400
            + "\n### 씬 4: 야밤의 추격전\n"
            + "라" * 400
            + "\n### 씬 5: 새벽의 결단\n"
            + "마" * 400
        )
        context = {
            "blueprint": {
                "scene_breakdown": {
                    "scene_1": {"title": "보이지 않는 감시망"},
                    "scene_2": {"title": "자산 청산 작전"},
                    "scene_3": {"title": "뒤따르는 그림자"},
                    "scene_4": {"title": "야밤의 추격전"},
                    "scene_5": {"title": "새벽의 결단"},
                }
            }
        }
        result = validator.scene_checks._check_scene_completeness(manuscript, context)
        assert result["passed"] is True

    def test_markdown_scene_headers_incomplete_rejects(self):
        """씬 헤더는 있지만 3/5 미달이면 여전히 REJECT."""
        validator = BlockingValidator()
        manuscript = (
            "### 씬 1: 시작\n"
            + "가" * 400
            + "\n### 씬 2: 전개\n"
            + "짧"  # 미달
            + "\n### 씬 3: 위기\n"
            + "짧"  # 미달
            + "\n### 씬 4: 절정\n"
            + "짧"  # 미달
            + "\n### 씬 5: 결말\n"
            + "마" * 400
        )
        context = {
            "blueprint": {
                "scene_breakdown": {
                    "scene_1": {"title": "시작"},
                    "scene_2": {"title": "전개"},
                    "scene_3": {"title": "위기"},
                    "scene_4": {"title": "절정"},
                    "scene_5": {"title": "결말"},
                }
            }
        }
        result = validator.scene_checks._check_scene_completeness(manuscript, context)
        assert result["passed"] is False

    def test_no_headers_uses_keyword_fallback(self):
        """씬 헤더 없으면 키워드 fallback 사용."""
        validator = BlockingValidator()
        manuscript = "주인공은 객잔에 도착했다. " * 50 + "비밀 문서를 확보했다. " * 50
        context = {
            "blueprint": {
                "scene_breakdown": {
                    "scene_1": {"description": "객잔 도착"},
                    "scene_2": {"description": "비밀 문서 확보"},
                }
            }
        }
        result = validator.scene_checks._check_scene_completeness(manuscript, context)
        assert result["check"] == "scene_completeness"
        # fallback 경로를 탔다는 것만 확인 (결과는 키워드 매칭 의존)

    def test_no_headers_scene_gap_is_director_advisory(self):
        """Visible 헤더 없는 scene separation gap은 Python reject가 아니라 Director advisory."""
        validator = BlockingValidator()
        manuscript = "헤더 없는 산문 원고입니다. " * 200
        context = {
            "blueprint": {
                "scene_breakdown": {
                    "scene_1": {"description": "객잔 도착"},
                    "scene_2": {"description": "비밀 문서 확보"},
                    "scene_3": {"description": "추격전"},
                    "scene_4": {"description": "새 단서 발견"},
                    "scene_5": {"description": "다음 목표 확정"},
                }
            }
        }
        result = validator.scene_checks._check_scene_completeness(manuscript, context)
        assert result["passed"] is True
        assert result["severity"] == "ADVISORY"
        assert result["advisory_only"] is True
        assert result["authority"] == "director"
        assert "visible scene header" in result["suggestion"]

    def test_no_headers_scene_gap_validate_exposes_warning(self):
        """Blocking facade warnings에 scene separation advisory를 전달한다."""
        validator = BlockingValidator(enable_justification_checks=False)
        manuscript = "헤더 없는 산문 원고입니다. 서술이 이어졌다. " * 180
        context = {
            "mode": "MANUSCRIPT",
            "blueprint": {
                "scene_breakdown": {
                    "scene_1": {"description": "객잔 도착"},
                    "scene_2": {"description": "비밀 문서 확보"},
                    "scene_3": {"description": "추격전"},
                    "scene_4": {"description": "새 단서 발견"},
                    "scene_5": {"description": "다음 목표 확정"},
                }
            },
        }
        result = validator.validate(manuscript, context)
        assert result["passed"] is True
        assert any("scene_completeness" in warning and "Director advisory" in warning for warning in result["warnings"])

    def test_hash_scene_header_variants(self):
        """## 씬 N: 형식 (2-level heading)도 인식."""
        validator = BlockingValidator()
        manuscript = "## 씬 1: 접선\n" + "가" * 400 + "\n## 씬 2: 탈출\n" + "나" * 400
        context = {
            "blueprint": {
                "scene_breakdown": {
                    "scene_1": {"title": "접선"},
                    "scene_2": {"title": "탈출"},
                }
            }
        }
        result = validator.scene_checks._check_scene_completeness(manuscript, context)
        assert result["passed"] is True

    def test_no_blueprint_skips(self):
        """Blueprint 없으면 체크 스킵."""
        validator = BlockingValidator()
        result = validator.scene_checks._check_scene_completeness("원고", {})
        assert result["passed"] is True
