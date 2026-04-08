from modules.core.stage_cross_stage_contract import (
    OPENING_TRANSITION_DIRECT,
    OPENING_TRANSITION_EXPLICIT,
    OPENING_TRANSITION_JUMP,
    apply_opening_transition_contract,
    infer_opening_transition_contract,
)


def test_infer_opening_transition_contract_direct_continuation():
    blueprint = {
        "start_location": "서재 앞 복도",
        "time_flow": "직후",
        "scene_breakdown": {
            "scene_1": {
                "title": "직후 후속 비트",
                "summary": "통화를 마친 직후 숨을 고른다.",
                "location": "서재 앞 복도",
            }
        },
    }

    contract = infer_opening_transition_contract(
        blueprint,
        prev_blueprint={"end_location": "서재 앞 복도", "time_flow": "직후"},
    )

    assert contract["type"] == OPENING_TRANSITION_DIRECT
    assert "same_location_anchor" in contract["signals"]


def test_infer_opening_transition_contract_explicit_transition():
    blueprint = {
        "start_location": "본가 저택 현관",
        "time_flow": "직후",
        "scene_breakdown": {
            "scene_1": {
                "title": "복도에서 현관으로 이동",
                "summary": "서재 앞 복도에서 현관 쪽으로 걸음을 옮긴 뒤 문 앞에 선다.",
                "location": "본가 저택 현관",
            }
        },
    }

    contract = infer_opening_transition_contract(
        blueprint,
        prev_blueprint={"end_location": "본가 저택 서재 앞 복도", "time_flow": "직후"},
    )

    assert contract["type"] == OPENING_TRANSITION_EXPLICIT
    assert "scene_transition_cue" in contract["signals"]


def test_apply_opening_transition_contract_normalizes_jump_opening():
    blueprint = {
        "start_location": "강남 PB센터 상담실",
        "time_flow": "다음 날 아침",
        "scene_breakdown": {
            "scene_1": {
                "title": "새 미팅",
                "summary": "한시우는 PB센터 상담실에서 새 회의를 시작한다.",
                "location": "강남 PB센터 상담실",
            }
        },
    }

    contract = apply_opening_transition_contract(
        blueprint,
        prev_blueprint={"end_location": "본가 저택 서재 앞 복도", "time_flow": "직후"},
    )

    assert contract["type"] == OPENING_TRANSITION_JUMP
    assert blueprint["opening_transition"]["type"] == OPENING_TRANSITION_JUMP
    assert "location_shift" in blueprint["opening_transition"]["signals"]
