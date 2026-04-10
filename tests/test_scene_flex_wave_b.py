from unittest.mock import MagicMock, patch

from modules.core.confidence_calibration import ConfidenceCalibrator
from modules.core.cross_agent_verifier import CrossAgentVerifier
from modules.core.pre_director_checklist import PreDirectorChecklist
from modules.core.stage4_interview_round import Stage4InterviewRound


def _repeat_to_length(seed: str, target: int) -> str:
    text = seed
    while len(text) < target:
        text += "\n\n" + seed
    return text[:target]


def _dense_two_scene_blueprint():
    return {
        "scene_breakdown": {
            "scene_1": {
                "goal": "주인공이 PB센터에서 첫 매수 버튼을 누른다",
                "summary": "매수 체결과 증거 확보",
                "key_events": ["매수", "체결", "증거"],
            },
            "scene_2": {
                "goal": "레버리지 경고와 담보 압박이 동시에 몰려온다",
                "summary": "마감 직전 담보 압박과 전화 경고",
                "key_events": ["경고", "담보", "압박"],
            },
        },
        "ending_hook": "장 마감 10초 전, 담보 경고 전화가 다시 울렸다.",
        "integrated_scenario": "A" * 1000,
    }


def _dense_three_scene_blueprint():
    return {
        "scene_breakdown": {
            "scene_1": {
                "goal": "주인공이 PB센터에서 첫 매수 버튼을 누른다",
                "summary": "매수 체결과 증거 확보",
                "key_events": ["매수", "체결"],
            },
            "scene_2": {
                "goal": "레버리지 경고와 담보 압박이 동시에 몰려온다",
                "summary": "담보 경고와 계좌 압박",
                "key_events": ["경고", "담보", "압박"],
            },
            "scene_3": {
                "goal": "마감 직전 반대매매 위기를 남긴다",
                "summary": "장 마감 직전 마지막 경고",
                "key_events": ["마감", "위기", "전화"],
            },
        },
        "ending_hook": "장 마감 직전, 마지막 경고 전화가 울렸다.",
        "integrated_scenario": "B" * 1200,
    }


def _dense_two_scene_manuscript() -> str:
    seed = """### 씬 1: PB 센터 개장 직후
"사야 해. 지금 아니면 놓쳐."
주인공은 유리 벽 너머 전광판이 번쩍일 때마다 손끝에 식은 땀이 맺히는 것을 느꼈다. PB센터 공기는 차갑고 건조했지만 손바닥은 축축했다. 그는 매수 버튼을 누르고 체결 알림을 확인한 뒤, 프린터에서 밀려 나오는 거래 증거를 접어 안주머니에 넣었다.
커피 향과 프린터 열기가 뒤섞인 자리에서 그는 호흡을 세 번 고르고 계좌 창을 다시 열었다. 숫자가 위로 튀자 목 안쪽이 뜨겁게 달아올랐고, 의자 바퀴가 짧게 삐걱거렸다.
"기록 남겨. 아직 끝나지 않았어."

### 씬 2: 마감 직전 담보 압박
"고객님, 담보 유지 비율이 무너집니다. 지금 대응하셔야 합니다."
전화기 너머 목소리가 높아지자 주인공은 귓바퀴가 얼얼해지는 것을 느꼈다. 창밖은 붉게 기울고, 전광판 아래로 레버리지 경고가 연속해서 튀었다. 그는 이를 악문 채 추가 담보 자료를 찾았지만 서랍 손잡이는 미끄럽고 손끝은 떨렸다.
"10초 남았습니다. 끊지 마세요."
형광등이 윙윙 울리는 가운데 심장은 갈비뼈를 두드렸고, 마지막 숫자가 내려앉는 소리가 귀 안에서 금속성 잔향으로 남았다. 장 마감 10초 전, 담보 경고 전화가 다시 울렸다.
"버틴다. 끝날 때까지 버틴다."
"""
    return _repeat_to_length(seed, 4300)


def _dense_three_scene_manuscript() -> str:
    seed = """### 씬 1: PB 센터 첫 진입
"들어간다. 오늘은 물러서지 않아."
주인공은 PB센터 접수대의 차가운 금속 냄새와 잉크 냄새를 동시에 맡으며 매수 버튼을 눌렀다. 체결 수치가 번쩍이자 목덜미가 달아올랐고, 그는 곧장 증거 캡처와 메모를 정리했다. 화면 가장자리에서 초 단위 시계가 짧게 떨렸다.

### 씬 2: 담보 경고와 계좌 압박
"지금 담보가 흔들립니다. 추가 대응 없으면 버티기 어렵습니다."
전화기 스피커에서는 거친 숨소리가 섞여 나왔고, 주인공은 혀끝에서 비릿한 긴장을 느꼈다. 그는 계좌 압박 수치를 훑으며 의자 팔걸이를 세게 움켜쥐었다. 경고 문구가 한 줄씩 늘어날수록 형광등 소리가 더 날카롭게 박혔다.
"알아. 아직 버틴다."
그는 서류철에서 담보 자료를 다시 꺼내며 시간을 벌었다.

### 씬 3: 장 마감 직전 마지막 경고
"마감 직전입니다. 반대매매 경계선이 바로 앞입니다."
창밖 저녁빛이 유리창에 길게 번지고, 바닥 카펫은 눅눅한 먼지 냄새를 올렸다. 주인공은 마지막 숫자를 노려보며 숨을 짧게 끊어 쉬었다. 손목 시계 초침이 탁, 탁, 탁 끊기고 모두가 말을 멈췄다.
"아직 안 끝났어. 끝나기 전까진 버틴다."
마지막 경고 전화가 다시 울리자 목 안쪽이 서늘하게 식었다. 장 마감 직전, 마지막 경고 전화가 울렸다.
"""
    return _repeat_to_length(seed, 4500)


def _make_stage4_round():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.current_project = MagicMock()
    modules = {
        "pre_director_checklist": PreDirectorChecklist(),
        "confidence_calibrator": ConfidenceCalibrator(),
        "cross_verifier": CrossAgentVerifier(api_client=MagicMock()),
    }
    ctx.get_module.side_effect = lambda name: modules.get(name)
    return Stage4InterviewRound(ctx), ctx


def _run_stage4_operator_canary(*, manuscript: str, blueprint: dict, style_dialogue_ratio_target: float):
    interview_round, ctx = _make_stage4_round()
    validation_results = [{"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": len(manuscript)}}]
    with (
        patch("modules.core.project_support.resolve_style_dialogue_ratio_target", return_value=style_dialogue_ratio_target),
        patch.object(interview_round, "_detect_shared_failure_warnings", return_value=[]),
    ):
        interview_round.director_runtime.run_director_optional_validation_modules(
            candidates=[{"manuscript": manuscript}],
            validation_results=validation_results,
            blueprint=blueprint,
            prev_manuscript="",
        )
    return validation_results[0], ctx


def _assert_scene_flex_pressure_is_absent(warnings: list[str]) -> None:
    assert not any(warning.startswith("[PreCheck]") for warning in warnings)
    assert not any(warning.startswith("[CrossVerify:VIOLATION]") for warning in warnings)
    assert not any("씬 반영" in warning for warning in warnings)
    assert not any("범위 초과" in warning for warning in warnings)
    assert not any("Blueprint 씬 반영 부족" in warning for warning in warnings)
    assert not any(warning.startswith("[Confidence:LOW]") for warning in warnings)


def test_stage4_operator_path_canary_keeps_dense_two_scene_candidate_out_of_scene_flex_warning_lane():
    result, ctx = _run_stage4_operator_canary(
        manuscript=_dense_two_scene_manuscript(),
        blueprint=_dense_two_scene_blueprint(),
        style_dialogue_ratio_target=0.10,
    )

    _assert_scene_flex_pressure_is_absent(result["warnings"])
    assert ctx.ui.log.call_count == 0


def test_stage4_operator_path_canary_keeps_dense_three_scene_candidate_out_of_scene_flex_warning_lane():
    result, ctx = _run_stage4_operator_canary(
        manuscript=_dense_three_scene_manuscript(),
        blueprint=_dense_three_scene_blueprint(),
        style_dialogue_ratio_target=0.14,
    )

    _assert_scene_flex_pressure_is_absent(result["warnings"])
    assert ctx.ui.log.call_count == 0
