from modules.domain.agents.scene_cardinality_contract import evaluate_stage3_scene_cardinality


def test_evaluate_stage3_scene_cardinality_rejects_one_scene():
    passed, scene_count, reason, feedback = evaluate_stage3_scene_cardinality(
        {"scene_1": {"goal": "도입"}},
        "가" * 900,
    )

    assert passed is False
    assert scene_count == 1
    assert "씬 개수 부족" in reason
    assert "최소 2개 이상의 씬" in feedback


def test_evaluate_stage3_scene_cardinality_accepts_dense_two_scene_blueprint():
    passed, scene_count, reason, feedback = evaluate_stage3_scene_cardinality(
        {
            "scene_1": {"goal": "주인공이 PB센터에서 첫 매수 버튼을 누른다", "key_events": ["매수"]},
            "scene_2": {"summary": "레버리지 경고와 담보 압박이 동시에 몰려온다", "key_events": ["경고", "압박"]},
        },
        "가" * 900,
    )

    assert passed is True
    assert scene_count == 2
    assert reason == ""
    assert feedback == ""

