from unittest.mock import MagicMock

from modules.domain.agents.director_continuity import DirectorContinuityValidator


def _make_validator():
    return DirectorContinuityValidator(MagicMock())


def test_validate_blueprint_completeness_empty_blueprint():
    validator = _make_validator()

    result = validator._validate_blueprint_completeness_v60("원고 텍스트", {})

    assert result["valid"] is True
    assert result["scene_coverage"] == 100
    assert result["expected_scenes"] == 0


def test_blueprint_scene_model_extracts_dict_and_string_scene_entries():
    validator = _make_validator()
    blueprint = {
        "scene_breakdown": {
            "scene1": {
                "type": "Core",
                "summary": "주인공이 시장에서 무기를 산다",
                "key_events": ["상인과 흥정한다"],
            },
            "Scene2": "[Cliffhanger] 적이 골목에서 추격한다",
            "notes": "ignore me",
        }
    }

    expected_scenes, scene_keywords = validator._blueprint_completeness_scene_model(blueprint)

    assert expected_scenes == 2
    assert set(scene_keywords) == {"scene1", "Scene2"}
    assert scene_keywords["scene1"]["type"] == "Core"
    assert "주인공이" in scene_keywords["scene1"]["keywords"]
    assert scene_keywords["Scene2"]["type"] == "Cliffhanger"
    assert "추격한다" in scene_keywords["Scene2"]["keywords"]


def test_blueprint_reflection_reports_missing_keywords():
    validator = _make_validator()
    scene_keywords = {
        "scene1": {"type": "Core", "keywords": ["주인공", "시장"], "content_sample": "시장 장면"},
        "scene2": {"type": "Buffer", "keywords": ["여관", "휴식"], "content_sample": "여관 장면"},
    }

    reflected_count, missing_scenes = validator._blueprint_completeness_reflection(
        "주인공은 시장을 가로질렀다.",
        scene_keywords,
    )

    assert reflected_count == 1
    assert missing_scenes == [
        {
            "scene": "scene2",
            "type": "Buffer",
            "missing_keywords": ["여관", "휴식"],
            "sample": "여관 장면",
        }
    ]


def test_validate_blueprint_completeness_good_coverage():
    validator = _make_validator()
    blueprint = {
        "scene_breakdown": {
            "scene1": "[Core] 주인공이 시장에서 무기를 구매한다",
            "scene2": "[Buffer] 주인공이 여관에서 쉰다",
            "scene3": "[Core] 주인공이 적과 전투한다",
            "scene4": "[Cliffhanger] 갑자기 새로운 적이 나타난다",
        },
        "integrated_scenario": "...",
    }
    manuscript = "주인공이 시장에서 무기를 구매하고, 여관에서 쉬다가, 적과 전투하고, 갑자기 새로운 적이 나타났다."

    result = validator._validate_blueprint_completeness_v60(manuscript, blueprint)

    assert result["valid"] is True
    assert result["expected_scenes"] == 4
    assert result["reflected_scenes"] == 4
    assert result["warnings"] == []


def test_validate_blueprint_completeness_uses_length_fallback_without_scene_keywords():
    validator = _make_validator()
    blueprint = {
        "scene_breakdown": None,
        "integrated_scenario": "[Core 1] A [Buffer 2] B [Scene 3] C [Scene 4] D",
    }

    result = validator._validate_blueprint_completeness_v60("가" * 1300, blueprint)

    assert result["valid"] is False
    assert result["expected_scenes"] == 4
    assert result["reflected_scenes"] == 2
    assert result["scene_coverage"] == 50.0
    assert result["reason"] == "Blueprint 반영률 부족: 2/4 씬 (50.0%)"


def test_validate_blueprint_completeness_warns_on_cliffhanger_without_tension():
    validator = _make_validator()
    blueprint = {
        "scene_breakdown": {
            "scene1": "[Cliffhanger] 주인공이 비밀문을 연다",
        }
    }

    result = validator._validate_blueprint_completeness_v60(
        "주인공이 비밀문을 연다. 문 너머의 어둠만 남는다.",
        blueprint,
    )

    assert result["valid"] is True
    assert result["warnings"] == ["Cliffhanger 엔딩 긴장감 부족 - 마지막 장면에 서스펜스 요소 추가 권장"]
    assert result["score"] == 95


def test_validate_blueprint_completeness_allows_dense_two_scene_tail_heavy_shape():
    validator = _make_validator()
    blueprint = {
        "scene_breakdown": {
            "scene1": {
                "summary": "주인공이 PB센터에서 첫 매수 버튼을 누른다",
                "key_events": ["매수", "체결", "증거"],
            },
            "scene2": {
                "summary": "레버리지 경고와 담보 압박이 동시에 몰려온다",
                "key_events": ["경고", "담보", "압박"],
            },
        }
    }
    manuscript = (
        "주인공은 PB센터에서 매수 주문을 체결하고 증거를 챙겼다. "
        "후반부에는 담보 압박과 레버리지 경고가 한꺼번에 밀려왔고 마지막 경고 전화가 다시 울렸다."
    )

    result = validator._validate_blueprint_completeness_v60(manuscript, blueprint)

    assert result["valid"] is True
    assert result["scene_coverage"] >= 75


def test_validate_blueprint_completeness_keeps_three_scene_single_tail_reflection_fail_closed():
    validator = _make_validator()
    blueprint = {
        "scene_breakdown": {
            "scene1": {
                "summary": "주인공이 PB센터에서 첫 매수 버튼을 누른다",
                "key_events": ["매수", "체결"],
            },
            "scene2": {
                "summary": "레버리지 경고와 담보 압박이 동시에 몰려온다",
                "key_events": ["경고", "담보", "압박"],
            },
            "scene3": {
                "summary": "마감 직전 마지막 위기 전화가 울린다",
                "key_events": ["마감", "위기", "전화"],
            },
        }
    }
    manuscript = "후반부에는 마감 직전 마지막 위기 전화만 거칠게 울렸다."

    result = validator._validate_blueprint_completeness_v60(manuscript, blueprint)

    assert result["valid"] is False
    assert result["scene_coverage"] < 65
