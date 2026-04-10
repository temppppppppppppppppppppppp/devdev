from __future__ import annotations

import json
from pathlib import Path

import scripts.production_pair_whole_run_pacing_triage_runner as triage_script


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
    reward: str,
    opponent_name: str = "상대",
    stakes: str = "이번 판단이 틀리면 다음 전장과 신뢰, 자금선까지 같이 잃는다.",
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
            "reward": reward,
        },
        "stakes": stakes,
        "location": {"place": place, "type": "현장"},
        "power_shift": {"protagonist": protagonist_shift, "antagonist": antagonist_shift},
        "genre_ext": {
            "opponent": {"name": opponent_name, "weakness_exploited": "정보 차"},
            "block_cider": {
                "has_cider": True,
                "receipt_type": "structure",
                "receipt_line": reward,
                "pain_only_exit": False,
            },
        },
    }


def test_build_report_marks_short_run_as_untriaged(temp_dir) -> None:
    treatment_path = temp_dir / "treatments" / "africa_farm_king_tr_block_001_draft.json"
    blocks = [
        _block(
            idx,
            title=f"초반 {idx}",
            place=f"농장 구역 {idx}",
            reward="첫 공개 인정이 붙는다.",
            protagonist_shift="사람들이 다시 본다.",
        )
        for idx in range(1, 11)
    ]
    _write_treatment(treatment_path, blocks)

    report = triage_script.build_report("africa_farm_king", treatment_path)

    assert report.triage_grade == "UNTRIAGED"
    assert report.recommended_action == "hold_until_mid_late_window_exists"
    assert report.trigger_codes == ["WHOLE-RUN-COVERAGE-INSUFFICIENT"]


def test_build_report_marks_late_blank_opponent_as_yellow(temp_dir) -> None:
    treatment_path = temp_dir / "treatments" / "wuxia_heavenly_physician_tr_block_070_draft.json"
    blocks = []
    for idx in range(1, 71):
        opponent_name = "혈마" if idx < 61 else ""
        reward = "동맹과 적대 구도가 다시 조정된다."
        protagonist_shift = "세력이 다시 본다." if idx % 7 == 0 else ""
        blocks.append(
            _block(
                idx,
                title=f"후반 {idx}",
                place=f"진가장 구역 {idx}",
                reward=reward,
                opponent_name=opponent_name,
                protagonist_shift=protagonist_shift,
            )
        )
    _write_treatment(treatment_path, blocks)

    report = triage_script.build_report("wuxia_heavenly_physician", treatment_path)

    assert report.triage_grade == "YELLOW"
    assert report.recommended_action == "manual_reaudit_then_repair"
    assert "LATE-BLANK-OPPONENT" in report.trigger_codes


def test_build_report_marks_balanced_full_run_as_green(temp_dir) -> None:
    treatment_path = temp_dir / "treatments" / "golden_canary_tr_block_070_draft.json"
    blocks = []
    for idx in range(1, 61):
        if idx <= 10:
            place = f"전략실-{idx % 3}"
        elif idx <= 20:
            place = f"투자 데스크-{idx % 3}"
        elif idx <= 30:
            place = f"현장 브리핑룸-{idx % 3}"
        elif idx <= 40:
            place = f"협상 테이블-{idx % 3}"
        elif idx <= 50:
            place = f"리스크 룸-{idx % 3}"
        else:
            place = f"이사회 보조실-{idx % 3}"
        reward = "공식 인정과 다음 전장 입장권이 같이 열린다."
        protagonist_shift = "사람들이 다시 봤다." if idx % 2 == 0 else ""
        blocks.append(
            _block(
                idx,
                title=f"균형 {idx}",
                place=place,
                reward=reward,
                opponent_name=f"상대 {idx % 5}",
                protagonist_shift=protagonist_shift,
            )
        )
    _write_treatment(treatment_path, blocks)

    report = triage_script.build_report("golden_canary", treatment_path)

    assert report.triage_grade == "GREEN"
    assert report.recommended_action == "keep_active_inventory"
    assert report.trigger_codes == ["WHOLE-RUN-PROVISIONAL-PASS"]
