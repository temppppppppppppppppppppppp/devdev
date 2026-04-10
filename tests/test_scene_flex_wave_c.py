from unittest.mock import MagicMock

from modules.core.quality_amplifier import QualityAmplifier
from modules.core.quality_dashboard import QualityDashboard
from modules.core.writer_template import ManuscriptTemplate, SceneSlot, SceneType, WriterTemplate
from modules.domain.agents.manuscript_validator import ManuscriptValidator
from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator


def _make_dashboard() -> QualityDashboard:
    dashboard = QualityDashboard(project_path=None)
    dashboard.stage_stats[4] = {"pass": 8, "reject": 2, "scores": []}
    return dashboard


def _make_stage3_validator() -> UnifiedBlueprintValidator:
    return UnifiedBlueprintValidator(context=MagicMock(), client=MagicMock())


def test_quality_amplifier_stage3_guidance_drops_rigid_four_to_six_scene_language():
    amplifier = QualityAmplifier()

    architect_constraints = amplifier.generate_architect_constraints(ep_num=7, arc_data={})
    self_check = amplifier.get_self_check_prompt(stage=3)

    assert "4-6개" not in architect_constraints
    assert "4-6개" not in self_check
    assert "planning anchor" in architect_constraints
    assert "planning anchor" in self_check


def test_writer_template_validation_uses_required_beats_for_dense_two_scene_templates():
    template = ManuscriptTemplate(
        ep_num=11,
        total_scenes=2,
        slots=[
            SceneSlot(
                index=1,
                scene_id="scene_1",
                scene_type=SceneType.OPENING,
                description="오프닝 - 직전 화 연결",
                min_chars=50,
                max_chars=400,
                required_elements=["PB센터", "주문", "체결"],
                characters=["주인공"],
            ),
            SceneSlot(
                index=2,
                scene_id="scene_2",
                scene_type=SceneType.CLIFFHANGER,
                description="클리프행어 - 위기 고조",
                min_chars=50,
                max_chars=400,
                required_elements=["담보", "압박", "경고"],
                characters=["주인공"],
            ),
        ],
        total_min_chars=50,
        total_max_chars=2000,
        opening_anchor="PB센터 체결 직후의 긴장",
        closing_hook="담보 압박 경고 전화",
        inventory_reminder=[],
    )
    manuscript = (
        "주인공은 PB센터에서 주문을 체결하고 거래 증거를 챙겼다. "
        "후반부에는 담보 압박과 경고 전화가 연달아 몰려왔다."
    )

    result = WriterTemplate().validate_against_template(manuscript, template)

    assert result["passed"] is True
    assert result["issues"] == []
    assert result["scene_coverage"] == "2/2"


def test_quality_dashboard_avoids_low_scene_false_penalty_when_materialization_is_dense():
    dashboard = _make_dashboard()

    prediction = dashboard.predict_pass_probability(
        stage=4,
        current_metrics={
            "length": 4600,
            "dialogue_ratio": 0.30,
            "scene_coverage": 60.0,
            "expected_scenes": 2,
            "reflected_scenes": 1,
            "pre_checklist_warnings": 0,
            "pre_checklist_fails": 0,
        },
    )

    assert not any(f["name"] == "씬 반영 부족" for f in prediction["factors"])
    assert not any(f["name"] == "저씬 구조 의무 반영 경계" for f in prediction["factors"])
    assert any(f["name"] == "저씬 구조 의무 반영 양호" for f in prediction["factors"])


def test_manuscript_validator_collects_low_scene_materialization_without_emitting_scene_warning():
    validator = ManuscriptValidator()
    blueprint = {
        "scene_breakdown": {
            "scene_1": {
                "summary": "주인공이 PB센터에서 첫 매수 버튼을 누른다",
                "key_events": ["매수", "체결", "증거"],
            },
            "scene_2": {
                "summary": "레버리지 경고와 담보 압박이 동시에 몰려온다",
                "key_events": ["경고", "담보", "압박"],
            },
        }
    }
    manuscript = (
        "주인공은 PB센터에서 매수 주문을 체결하고 증거를 챙겼다. "
        "후반부에는 담보 압박과 레버리지 경고가 한꺼번에 밀려왔다."
    )

    result = validator._check_scene_coverage(manuscript, blueprint)

    assert result["warnings"] == []
    assert result["expected"] == 2
    assert result["reflected"] >= 1
    assert result["coverage"] >= 60


def test_unified_blueprint_validator_skips_avg_chars_pressure_for_low_scene_profiles():
    validator = _make_stage3_validator()
    validator.min_chars = 500
    scenario = (
        "여의도 PB센터에서 15억 원 체결 내역을 확인했다. "
        "테헤란로 본점 회의실에서 담보 압박과 경고 전화를 정리했다. "
        "성북동 저택으로 돌아가기 전 마지막 자금 이동 수치를 다시 검토했다. "
    ) * 2
    scenes = {
        "scene_1": {"goal": "PB센터 첫 체결", "key_events": ["PB센터", "체결", "증거"]},
        "scene_2": {"goal": "담보 압박 정리", "key_events": ["담보", "압박", "경고"]},
        "scene_3": {"goal": "마지막 자금 이동 검토", "key_events": ["자금", "이동", "검토"]},
    }

    issues = validator._collect_scenario_density_issues(integrated=scenario, scenes=scenes, scene_count=3)

    assert not any("밀도 부족" in issue["issue"] for issue in issues)
