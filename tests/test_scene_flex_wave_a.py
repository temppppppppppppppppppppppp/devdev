from unittest.mock import MagicMock

from modules.core.confidence_calibration import ConfidenceCalibrator
from modules.core.cross_agent_verifier import CrossAgentVerifier
from modules.core.pre_director_checklist import CheckSeverity, PreDirectorChecklist
from modules.validation.blocking_validator import BlockingValidator


def _repeat_to_length(seed: str, target: int) -> str:
    text = seed
    while len(text) < target:
        text += "\n" + seed
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


def _stable_five_scene_blueprint():
    return {
        "scene_breakdown": {
            "scene_1": {"summary": "도입 회의", "key_events": ["회의", "보고"]},
            "scene_2": {"summary": "현장 점검", "key_events": ["현장", "점검"]},
            "scene_3": {"summary": "갈등 폭발", "key_events": ["갈등", "폭발"]},
            "scene_4": {"summary": "반격 설계", "key_events": ["반격", "설계"]},
            "scene_5": {"summary": "클리프행어", "key_events": ["경고", "추락"]},
        },
        "ending_hook": "경고등이 켜진 채 엘리베이터가 추락하기 시작했다.",
    }


def _one_scene_blueprint():
    return {
        "scene_breakdown": {
            "scene_1": {
                "summary": "주인공이 모든 문제를 한 번에 해결한다",
                "key_events": ["해결", "완승", "정리"],
            }
        },
        "ending_hook": "모든 일이 끝났다.",
    }


def test_blocking_validator_scope_overflow_allows_dense_two_scene_manuscript():
    validator = BlockingValidator()
    manuscript = _repeat_to_length(
        "주인공은 PB센터에서 매수 버튼을 누르고 체결 증거를 확보했다. "
        "곧바로 담보 압박과 레버리지 경고 전화가 이어졌고 장 마감 직전 다시 경고가 울렸다. ",
        5200,
    )

    result = validator.scene_checks._check_scope_overflow(
        manuscript,
        {"mode": "MANUSCRIPT", "blueprint": _dense_two_scene_blueprint()},
    )

    assert result["passed"] is True


def test_blocking_validator_scope_overflow_still_rejects_one_scene_collapse():
    validator = BlockingValidator()
    manuscript = _repeat_to_length(
        "주인공은 모든 문제를 한 번에 해결했고 완승과 정리를 선언했다. ",
        5000,
    )

    result = validator.scene_checks._check_scope_overflow(
        manuscript,
        {"mode": "MANUSCRIPT", "blueprint": _one_scene_blueprint()},
    )

    assert result["passed"] is False
    assert result["check"] == "scope_overflow"


def test_cross_agent_verifier_writer_precheck_allows_dense_three_scene_manuscript():
    verifier = CrossAgentVerifier(api_client=MagicMock())
    manuscript = _repeat_to_length(
        "주인공은 PB센터에서 매수와 체결을 마무리했다. "
        "곧 담보 압박과 경고가 동시에 밀려왔지만 버티며 대응했다. "
        "장 마감 직전 마지막 위기 전화가 울렸고 모두 숨을 삼켰다. ",
        5300,
    )

    violations = verifier._python_precheck_writer(manuscript, _dense_three_scene_blueprint())

    assert violations == []


def test_cross_agent_verifier_writer_precheck_preserves_stable_five_scene_shape():
    verifier = CrossAgentVerifier(api_client=MagicMock())
    manuscript = (
        _repeat_to_length(
            "도입 회의와 보고가 끝나고 현장 점검이 이어졌다. "
            "갈등 폭발 뒤 반격 설계가 시작됐고 마지막에는 경고와 추락의 클리프행어가 닥쳤다. ",
            5600,
        )
        + " 경고등이 켜진 채 엘리베이터가 추락하기 시작했다."
    )

    violations = verifier._python_precheck_writer(manuscript, _stable_five_scene_blueprint())

    assert violations == []


def test_pre_director_checklist_avoids_false_dense_two_scene_scope_warning():
    checker = PreDirectorChecklist()
    manuscript = _repeat_to_length(
        "주인공은 PB센터에서 매수와 체결 증거를 확보했다. "
        "후반부에는 담보 압박과 경고 전화가 거칠게 몰려오며 장 마감 직전 위기를 남겼다. ",
        5200,
    )
    blueprint = _dense_two_scene_blueprint()

    scope_items = checker._check_manuscript_scope(manuscript, {"blueprint": blueprint})
    alignment_items = checker._check_manuscript_blueprint_alignment(manuscript, {"blueprint": blueprint})

    assert not any(item.name == "범위 초과" for item in scope_items)
    assert not any(item.name == "씬 반영" and item.severity == CheckSeverity.WARNING for item in alignment_items)


def test_confidence_calibrator_keeps_dense_two_scene_manuscript_out_of_low_band():
    calibrator = ConfidenceCalibrator()
    concerns: list[str] = []
    manuscript = _repeat_to_length(
        "주인공은 PB센터에서 매수 버튼을 눌러 체결을 만들고 증거를 챙겼다. "
        "마지막에는 담보 압박과 경고 전화가 동시에 울리며 위기를 남겼다. ",
        4800,
    )

    score = calibrator._score_manuscript_scene_coverage(
        manuscript,
        {"blueprint": _dense_two_scene_blueprint()},
        concerns,
    )

    assert score >= 10
    assert concerns == []
