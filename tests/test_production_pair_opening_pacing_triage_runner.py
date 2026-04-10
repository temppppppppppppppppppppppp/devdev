from __future__ import annotations

import json
from pathlib import Path

import scripts.production_pair_opening_pacing_triage_runner as triage_script


def _write_treatment(path: Path, blocks: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"_schema": "tr.v1", "_total_blocks": len(blocks), "blocks": blocks}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _block(
    block_no: int,
    *,
    title: str,
    place: str,
    location_type: str = "현장",
    reward: str = "",
    protagonist_shift: str = "",
    antagonist_shift: str = "",
) -> dict:
    return {
        "block_id": f"Block {block_no}",
        "title": title,
        "content": {
            "context": f"{title} 배경",
            "event_villain": f"{title} 사건",
            "solution": f"{title} 해결",
            "reward": reward or f"{title} 보상",
        },
        "location": {"place": place, "type": location_type},
        "power_shift": {"protagonist": protagonist_shift, "antagonist": antagonist_shift},
        "genre_ext": {
            "block_cider": {
                "has_cider": True,
                "receipt_type": "structure",
                "receipt_line": reward or "",
                "pain_only_exit": False,
            }
        },
    }


def test_build_report_marks_funeral_overstay_with_late_signboard_as_red(temp_dir) -> None:
    treatment_path = temp_dir / "treatments" / "chaebol_allowance_zero_tr_block_070_draft.json"
    blocks = [
        _block(1, title="잘린 카드", place="윤성가 장례식장 운영실", location_type="장례 운영 거점", reward="다음 운영 전장 입장권을 확보한다."),
        _block(2, title="장례 밥차", place="장례식장 배식 라인", reward="사람들이 다시 봤다."),
        _block(3, title="검은 리본 주차권", place="장례식장 주차관제실"),
        _block(4, title="꽃값은 현금이다", place="장례식장 꽃 집하장"),
        _block(5, title="빈소 셔틀", place="장례식장 셔틀 대기선"),
        _block(6, title="조의금 영수증", place="장례식장 정산실"),
        _block(7, title="장례식장 세탁실", place="장례식장 지하 세탁실"),
        _block(8, title="밤새는 청소팀", place="장례식장 청소팀 대기실"),
        _block(9, title="첫 월 반복매출", place="제로라인 사무실", reward="첫 월 반복매출이 공식 사례가 된다."),
        _block(10, title="도련님 대신 대표", place="가문 본가 식탁"),
    ]
    _write_treatment(treatment_path, blocks)

    report = triage_script.build_report("chaebol_allowance_zero", treatment_path)

    assert report.triage_grade == "RED"
    assert report.recommended_action == "negative_exemplar_archive"
    assert report.legacy_main_macro_battlefield == "장례 운영축"
    assert report.legacy_macro_overstay is True
    assert report.first_public_signboard_block == 9
    assert "LEGACY-MACRO-OVERSTAY" in report.trigger_codes
    assert "LEGACY-SIGNBOARD-LATE" in report.trigger_codes


def test_build_report_marks_late_signboard_without_overstay_as_yellow(temp_dir) -> None:
    treatment_path = temp_dir / "treatments" / "chaebol_ent_empire_tr_block_070_draft.json"
    blocks = [
        _block(1, title="상속", place="호텔 로비", location_type="호텔 운영축"),
        _block(2, title="유령 회사", place="호텔 BOH 회의실", location_type="호텔 운영축"),
        _block(3, title="감으로만 버는 건 아니다", place="전략 사무실", location_type="오피스"),
        _block(4, title="조준된 패배", place="호텔 연회장", location_type="호텔 운영축", reward="모두가 다시 봤다."),
        _block(5, title="누가 줄을 당기나", place="호텔 하역장", location_type="호텔 운영축"),
        _block(6, title="반격의 밤", place="전략 사무실", location_type="오피스"),
        _block(7, title="첫 판짜기", place="호텔 객실동", location_type="호텔 운영축"),
        _block(8, title="맞는 자리", place="가문 회의실", location_type="오피스"),
        _block(9, title="가능성은 떴는데 돈은 샌다", place="소형 공연장", reward="이 건은 공식 보도와 메인 사례가 된다."),
        _block(10, title="계속할 이유", place="전략 사무실"),
    ]
    _write_treatment(treatment_path, blocks)

    report = triage_script.build_report("chaebol_ent_empire", treatment_path)

    assert report.triage_grade == "YELLOW"
    assert report.recommended_action == "manual_reaudit_then_repair"
    assert report.legacy_macro_overstay is False
    assert report.first_public_signboard_block == 9
    assert report.trigger_codes == ["LEGACY-SIGNBOARD-LATE"]


def test_build_report_marks_balanced_opening_as_green(temp_dir) -> None:
    treatment_path = temp_dir / "treatments" / "defense_defect_engineer_tr_block_070_draft.json"
    blocks = [
        _block(1, title="복도", place="본사 전략실", location_type="오피스"),
        _block(2, title="안건 4번", place="본사 회의실", location_type="오피스", reward="그를 다시 봤다."),
        _block(3, title="매각 저지", place="방산 연구동", location_type="연구동", reward="공식 보도에 이름이 오른다."),
        _block(4, title="48시간", place="시험평가대대 외곽 카페", location_type="현장"),
        _block(5, title="정비로그", place="정비로그 서버실", location_type="오피스"),
        _block(6, title="열처리 장부", place="열처리 라인", location_type="현장", reward="다음 전장 입장권을 미리 쥔다."),
        _block(7, title="시험일정 봉쇄", place="충남 시험평가대대", location_type="현장"),
        _block(8, title="역제안", place="안전 브리핑룸", location_type="오피스"),
        _block(9, title="증거", place="전략조정실", location_type="오피스"),
        _block(10, title="열쇠", place="전략조정실", location_type="오피스"),
    ]
    _write_treatment(treatment_path, blocks)

    report = triage_script.build_report("defense_defect_engineer", treatment_path)

    assert report.triage_grade == "GREEN"
    assert report.recommended_action == "keep_active_inventory"
    assert report.legacy_macro_overstay is False
    assert report.first_public_signboard_block == 3
    assert report.trigger_codes == ["LEGACY-PROVISIONAL-PASS"]


def test_build_report_marks_incomplete_opening_window_as_untriaged(temp_dir) -> None:
    treatment_path = temp_dir / "treatments" / "gulf_tycoon_heir_tr_block_001_draft.json"
    blocks = [
        _block(1, title="야간 호출", place="두바이 투자 데스크", location_type="투자/시장 축"),
        _block(2, title="장부 두 권", place="두바이 투자 데스크", location_type="투자/시장 축"),
        _block(3, title="누가 가짜 오더를 냈나", place="브로커 라운지", location_type="투자/시장 축"),
        _block(4, title="잘못 온 송금", place="브로커 라운지", location_type="투자/시장 축"),
        _block(5, title="계좌 하나가 비어 있다", place="VIP룸", location_type="투자/시장 축"),
    ]
    _write_treatment(treatment_path, blocks)

    report = triage_script.build_report("gulf_tycoon_heir", treatment_path)

    assert report.triage_grade == "UNTRIAGED"
    assert report.recommended_action == "hold_until_opening_window_complete"
    assert report.evidence_mode == "insufficient_opening_window"
    assert report.opening_window_complete is False
    assert report.opening_window_missing_blocks == [6, 7, 8, 9, 10]
    assert report.trigger_codes == ["OPENING-WINDOW-INCOMPLETE"]
