"""
[Wave1] Stage 3 Blueprint Clarity/Density — Authority Re-Banding + Prevalidation Tests

Tranche A: Authority re-banding in blueprint_ensemble._format_constraints()
Tranche B: Scene-specificity + scenario-density prevalidation in unified_blueprint_validator
"""

from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler
from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator
from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator

# ============================================================
# Helpers
# ============================================================


def _make_ensemble() -> BlueprintEnsembleGenerator:
    """Minimal BlueprintEnsemble for constraint formatting tests."""

    class _Stub:
        pass

    ctx = _Stub()
    ctx.current_project = None
    ctx.ui = _Stub()
    ctx.ui.log = lambda *a, **kw: None
    ens = object.__new__(BlueprintEnsembleGenerator)
    ens.context = ctx
    return ens


def _make_validator() -> UnifiedBlueprintValidator:
    """Minimal UnifiedBlueprintValidator for prevalidation tests."""

    class _Stub:
        pass

    v = object.__new__(UnifiedBlueprintValidator)
    v.min_chars = 800
    return v


# ============================================================
# Tranche A: Authority Re-Banding
# ============================================================


class TestAuthorityBanding:
    """Prompt constraint block shows explicit 4-tier authority bands."""

    def test_priority_preamble_present(self):
        ens = _make_ensemble()
        result = ens._format_constraints({}, genre="wuxia")
        assert "IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY" in result

    def test_immutable_band_header_with_fact_lock(self):
        block = {
            "fact_lock_packet": {
                "anchors": [{"category": "위치", "fact": "청석관 후원"}],
                "source": "prev",
            }
        }
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="wuxia")
        assert "IMMUTABLE" in result
        assert "FACT-LOCK" in result
        assert "청석관 후원" in result

    def test_capital_lock_in_immutable_band(self):
        block = {
            "capital_continuity_packet": {
                "fields": [{"label": "잔고", "value": "5억 원"}],
                "source": "prev",
            },
            "must_focus": {"key_events": ["테스트 이벤트"]},
        }
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="investment")
        # CAPITAL-LOCK must be inside the IMMUTABLE band section
        immutable_header = "═══ IMMUTABLE"
        hard_header = "─── HARD CONSTRAINT"
        immutable_idx = result.find(immutable_header)
        capital_idx = result.find("CAPITAL-LOCK")
        hard_idx = result.find(hard_header)
        assert immutable_idx >= 0
        assert capital_idx > immutable_idx
        assert hard_idx >= 0
        assert capital_idx < hard_idx

    def test_hard_constraint_band_with_must_focus(self):
        block = {
            "must_focus": {
                "key_events": ["WTI 선물 매수", "환율 리스크 발견"],
            }
        }
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="investment")
        assert "HARD CONSTRAINT" in result
        assert "WTI 선물 매수" in result

    def test_stop_line_in_hard_constraint_band(self):
        block = {
            "stop_line": {
                "content": "에콰도르 투자",
                "next_ep": 10,
            },
            "ep_num": 9,
        }
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="investment")
        hard_idx = result.find("HARD CONSTRAINT")
        stop_idx = result.find("Stop Line")
        assert hard_idx >= 0
        assert stop_idx > hard_idx

    def test_continuity_in_expected_continuity_band(self):
        block = {
            "continuity": {"location": "여의도 한미증권 VIP룸"},
        }
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="investment")
        cont_idx = result.find("EXPECTED CONTINUITY")
        loc_idx = result.find("여의도 한미증권 VIP룸")
        assert cont_idx >= 0
        assert loc_idx > cont_idx

    def test_formatted_constraints_keep_arc_start_state_authority(self):
        compiler = BlueprintConstraintCompiler()
        block = compiler.compile(
            arc_data={
                "ep_start": 11,
                "ep_count": 3,
                "arc_no": 3,
                "tactical_doc": "제11화: 개장 직전 브리핑",
                "state_constraints": {
                    "arc_start_state": {
                        "location": "Gangnam HQ",
                        "equipment": ["BlackBerry 7130", "Ecuador memo"],
                        "injuries": "없음",
                    }
                },
            },
            ep_num=11,
            prev_blueprint={
                "end_location": "Old Office",
                "protagonist_state": {
                    "equipment": ["Stale pager"],
                    "injuries": "왼팔 타박상",
                },
            },
        )
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="investment")

        assert "EXPECTED CONTINUITY" in result
        assert "이전 종료 위치: Gangnam HQ" in result
        assert "장비: BlackBerry 7130, Ecuador memo" in result
        assert "부상: 없음" in result

    def test_formatted_constraints_filter_future_capital_events(self):
        compiler = BlueprintConstraintCompiler()
        block = compiler.compile(
            arc_data={
                "ep_start": 11,
                "ep_count": 3,
                "arc_no": 3,
                "tactical_doc": "제11화: 포지션 점검",
                "state_changes": {
                    "capital_changes": [
                        {"episode": 12, "description": "차익 실현", "amount": "5억"},
                        {"episode": 11, "description": "WTI 포지션 유지", "amount": "12.5억"},
                    ]
                },
            },
            ep_num=11,
            prev_blueprint={},
            genre="investment",
        )
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="investment")

        assert "WTI 포지션 유지" in result
        assert "차익 실현" not in result

    def test_hard_constraint_band_with_arc_summary(self):
        block = {
            "arc_constraint_summary": "테스트 Arc 요약",
        }
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="wuxia")
        hard_idx = result.find("HARD CONSTRAINT")
        summary_idx = result.find("테스트 Arc 요약")
        assert hard_idx >= 0
        assert summary_idx > hard_idx

    def test_full_band_ordering(self):
        """All 4 bands appear in correct order: IMMUTABLE > HARD > CONTINUITY > ADVISORY."""
        block = {
            "fact_lock_packet": {
                "anchors": [{"category": "위치", "fact": "남궁세가"}],
                "source": "prev",
            },
            "must_focus": {"key_events": ["비급 탈환"]},
            "continuity": {"location": "남궁세가 후원"},
            "arc_constraint_summary": "Arc 1 요약",
            "state_changes_summary": "Arc state summary",
        }
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="wuxia")
        immutable_idx = result.find("IMMUTABLE")
        hard_idx = result.find("HARD CONSTRAINT")
        cont_idx = result.find("EXPECTED CONTINUITY")
        advisory_idx = result.find("ADVISORY")
        assert immutable_idx < hard_idx < cont_idx < advisory_idx

    def test_empty_constraint_block_still_has_preamble(self):
        ens = _make_ensemble()
        result = ens._format_constraints({}, genre="wuxia")
        assert "IMMUTABLE > HARD CONSTRAINT" in result
        # No band headers if no content
        assert "FACT-LOCK" not in result

    def test_degraded_path_content_in_hard_band(self):
        """When key_events absent, must_focus.content goes to HARD band, not duplicated."""
        block = {
            "must_focus": {"content": "한시우가 WTI 매수를 결심하는 장면"},
        }
        ens = _make_ensemble()
        result = ens._format_constraints(block, genre="investment")
        hard_idx = result.find("HARD CONSTRAINT")
        content_idx = result.find("한시우가 WTI 매수를 결심하는 장면")
        assert hard_idx >= 0
        assert content_idx > hard_idx
        # Content should appear exactly once
        assert result.count("한시우가 WTI 매수를 결심하는 장면") == 1


# ============================================================
# Tranche B: Scene-Specificity Prevalidation
# ============================================================


class TestSceneSpecificityPrevalidation:
    """New scene-specificity check family catches thin scenes."""

    def test_no_issues_for_rich_scenes(self):
        scenes = {
            "scene_1": {"goal": "한시우가 VIP룸에서 WTI 매수 주문을 넣는다", "key_events": ["매수 체결"]},
            "scene_2": {"goal": "박성호 PB가 레버리지 위험을 경고한다", "key_events": ["경고"]},
            "scene_3": {"goal": "한시우가 거래 성공을 확인한다", "key_events": ["확인"]},
        }
        v = _make_validator()
        issues = v._collect_scene_specificity_issues(scenes=scenes, scene_count=3)
        assert len(issues) == 0

    def test_thin_goals_detected(self):
        scenes = {
            "scene_1": {"goal": "갈등", "summary": "전개", "key_events": ["a"]},
            "scene_2": {"goal": "심화", "summary": "흐름", "key_events": ["b"]},
            "scene_3": {"goal": "한시우가 VIP룸에서 WTI 매수 주문을 넣는다", "key_events": ["c"]},
        }
        v = _make_validator()
        issues = v._collect_scene_specificity_issues(scenes=scenes, scene_count=3)
        assert any(i["category"] == "scene_specificity" for i in issues)
        assert any("목표 미흡" in i["issue"] for i in issues)

    def test_empty_key_events_detected(self):
        scenes = {
            "scene_1": {"goal": "한시우가 매수 결정", "key_events": []},
            "scene_2": {"goal": "PB가 레버리지 경고", "key_events": []},
            "scene_3": {"goal": "거래 성공 확인 장면", "key_events": ["확인"]},
        }
        v = _make_validator()
        issues = v._collect_scene_specificity_issues(scenes=scenes, scene_count=3)
        assert any(i["category"] == "scene_completeness" for i in issues)
        assert any("scene.key_events" in i["issue"] for i in issues)

    def test_single_thin_scene_not_flagged(self):
        """One thin scene is below threshold (>=2 required)."""
        scenes = {
            "scene_1": {"goal": "짧게", "key_events": ["a"]},
            "scene_2": {"goal": "한시우가 VIP룸에서 매수", "key_events": ["b"]},
            "scene_3": {"goal": "PB가 레버리지 위험 경고", "key_events": ["c"]},
        }
        v = _make_validator()
        issues = v._collect_scene_specificity_issues(scenes=scenes, scene_count=3)
        assert not any("목표 미흡" in i.get("issue", "") for i in issues)

    def test_string_scenes_ignored(self):
        """String-only scenes are skipped (already caught by structure check)."""
        scenes = {"scene_1": "just a string", "scene_2": "another string", "scene_3": "third"}
        v = _make_validator()
        issues = v._collect_scene_specificity_issues(scenes=scenes, scene_count=3)
        # String scenes are not dict, so thin_goal_count stays 0
        assert len(issues) == 0

    def test_max_two_issues_returned(self):
        scenes = {
            "scene_1": {"goal": "", "key_events": []},
            "scene_2": {"goal": "", "key_events": []},
            "scene_3": {"goal": "", "key_events": []},
        }
        v = _make_validator()
        issues = v._collect_scene_specificity_issues(scenes=scenes, scene_count=3)
        assert len(issues) <= 2


# ============================================================
# Tranche B: Scenario-Density Prevalidation
# ============================================================


class TestScenarioDensityPrevalidation:
    """New scenario-density check family catches low-density scenarios."""

    def test_no_issues_for_dense_scenario(self):
        # 1200 chars, 4 scenes, has concrete anchors
        scenario = (
            "여의도 한미증권 VIP룸에서 한시우가 WTI 6월물 15억 원 매수 주문을 넣었다. "
            "3배 레버리지로 총 45억 원 규모의 포지션이 잡혔다. 박성호 PB가 마른침을 삼켰다. "
            "테헤란로 SW인베스트먼트 사무실에서 한시우는 다음 타깃을 구상했다. "
            "성북동 저택 거실에서 한태준과 한태민이 한시우를 조롱했다. "
            "한시우는 지분율 32%를 언급하며 형들의 조롱을 짓밟았다. "
        ) * 3  # ~1200+ chars
        scenes = {f"scene_{i}": {"goal": f"goal_{i}" * 5, "key_events": [f"e_{i}"]} for i in range(1, 5)}
        v = _make_validator()
        issues = v._collect_scenario_density_issues(integrated=scenario, scenes=scenes, scene_count=4)
        assert len(issues) == 0

    def test_low_avg_chars_per_scene_detected(self):
        # 800 chars total, 5 scenes → 160 chars/scene < 200 threshold
        scenario = "가" * 800
        scenes = {f"scene_{i}": {"goal": f"goal_{i}"} for i in range(1, 6)}
        v = _make_validator()
        issues = v._collect_scenario_density_issues(integrated=scenario, scenes=scenes, scene_count=5)
        assert any("밀도 부족" in i["issue"] for i in issues)

    def test_no_issue_below_min_chars(self):
        """Below min_chars floor, density check defers to the structure check."""
        scenario = "가" * 500
        scenes = {"scene_1": {"goal": "a"}}
        v = _make_validator()
        issues = v._collect_scenario_density_issues(integrated=scenario, scenes=scenes, scene_count=1)
        assert len(issues) == 0

    def test_low_anchor_density_detected(self):
        # 800+ chars but no concrete anchors (no institution names, locations, numbers)
        scenario = "그는 조용히 생각했다. 상황은 매우 복잡하고 어려웠다. 결국 모든 것이 완전히 달라질 터였다. " * 20
        scenes = {"scene_1": {"goal": "a" * 20}, "scene_2": {"goal": "b" * 20}, "scene_3": {"goal": "c" * 20}}
        v = _make_validator()
        issues = v._collect_scenario_density_issues(integrated=scenario, scenes=scenes, scene_count=3)
        anchor_issue = next(i for i in issues if "구체성 부족" in i["issue"])
        assert anchor_issue["advisory_only"] is True
        assert anchor_issue["director_focus"] is False

    def test_low_anchor_density_exposes_structured_advisory_packet(self):
        scenario = "The market mood stays vague and abstract without concrete anchors. " * 30
        scenes = {
            "scene_1": {"goal": "hold the room", "key_events": ["hesitation"]},
            "scene_2": {"goal": "read the reaction", "key_events": ["silence"]},
            "scene_3": {"goal": "delay the trade", "key_events": ["stall"]},
        }
        v = _make_validator()

        issues = v._collect_scenario_density_issues(integrated=scenario, scenes=scenes, scene_count=3)

        anchor_issue = next(issue for issue in issues if issue.get("advisory_code") == "anchor_density")
        assert anchor_issue["advisory_packet"]["anchor_count"] == 0
        assert anchor_issue["advisory_packet"]["anchor_min"] == 5
        assert anchor_issue["fix_pack"]["patch_target_records"][0]["field_path"] == "integrated_scenario"
        assert anchor_issue["fix_pack"]["patch_target_records"][0]["target_kind"] == "local_sentence"
        assert "anchor_count=0" in anchor_issue["fix_pack"]["evidence_summary"]

    def test_adequate_anchor_density_no_issue(self):
        scenario = (
            "여의도 한미증권 VIP룸에서 15억 원을 투자했다. "
            "박성호 PB가 3배 레버리지를 확인했다. "
            "테헤란로 사무실에서 5억 원 잔고를 점검했다. "
            "성북동 저택에서 32% 지분율을 언급했다. "
            "한태준이 20억 원을 조롱했다. "
        ) * 4
        scenes = {"scene_1": {"goal": "a" * 20}, "scene_2": {"goal": "b" * 20}}
        v = _make_validator()
        issues = v._collect_scenario_density_issues(integrated=scenario, scenes=scenes, scene_count=2)
        density_issues = [i for i in issues if "구체성 부족" in i.get("issue", "")]
        assert len(density_issues) == 0

    def test_empty_scenario_no_crash(self):
        v = _make_validator()
        issues = v._collect_scenario_density_issues(integrated="", scenes={}, scene_count=0)
        assert issues == []

    def test_max_two_issues_returned(self):
        scenario = "가" * 800
        scenes = {f"scene_{i}": {"goal": "a"} for i in range(1, 6)}
        v = _make_validator()
        issues = v._collect_scenario_density_issues(integrated=scenario, scenes=scenes, scene_count=5)
        assert len(issues) <= 2


# ============================================================
# Integration: New checks appear in _python_pre_validate
# ============================================================


class TestPrevalidateIntegration:
    """New check families are wired into the prevalidation pipeline."""

    def test_thin_scenes_surface_in_prevalidation(self):
        blueprint = {
            "scene_breakdown": {
                "scene_1": {"goal": "짧", "key_events": []},
                "scene_2": {"goal": "짧", "key_events": []},
                "scene_3": {"goal": "짧", "key_events": []},
            },
            "integrated_scenario": "가" * 900,
        }
        v = _make_validator()
        result = v._python_pre_validate(
            blueprint=blueprint,
            constraint_block={},
            prev_blueprint=None,
        )
        categories = [i["category"] for i in result["issues"]]
        assert "scene_specificity" in categories

    def test_low_density_surfaces_in_prevalidation(self):
        blueprint = {
            "scene_breakdown": {
                "scene_1": {"goal": "한시우가 매수 결정", "key_events": ["a"]},
                "scene_2": {"goal": "PB가 레버리지 경고", "key_events": ["b"]},
                "scene_3": {"goal": "거래 성공 확인 장면", "key_events": ["c"]},
                "scene_4": {"goal": "마무리 및 다음 타깃", "key_events": ["d"]},
                "scene_5": {"goal": "엔딩 훅 설정 장면", "key_events": ["e"]},
            },
            "integrated_scenario": "가" * 800,
        }
        v = _make_validator()
        result = v._python_pre_validate(
            blueprint=blueprint,
            constraint_block={},
            prev_blueprint=None,
        )
        categories = [i["category"] for i in result["issues"]]
        assert "scenario_density" in categories
