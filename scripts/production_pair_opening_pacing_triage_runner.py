#!/usr/bin/env python3
"""Triage live production TR pairs for opening pacing discard vs repair decisions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from production_pair_normalization_runner import LIVE_TREATMENT_DIR, collect_live_pairs, normalize_work_id
from tr_batch_harness import (
    OPENING_MAIN_BATTLEFIELD_DOMINANCE_MIN,
    OPENING_MAIN_BATTLEFIELD_END,
    OPENING_READER_EARNING_SIGNAL_END,
    OPENING_READER_EARNING_SIGNAL_START,
    compute_treatment_metrics,
    extract_macro_battlefield,
    parse_block_no,
)

OPENING_CONTRACT_END = 10
GRADE_ORDER = {"RED": 0, "YELLOW": 1, "GREEN": 2, "UNTRIAGED": 3}
LEGACY_MACRO_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("장례 운영축", ("장례식장", "장례", "빈소", "조의")),
    ("병원/의국 축", ("병원", "수술", "응급실", "검진", "의국", "병동", "회진")),
    ("호텔 운영축", ("호텔", "객실", "린넨", "하우스키핑", "boh")),
    ("오피스/의사결정 축", ("오피스", "사무실", "본사", "회의실", "집무실", "비서실", "전무실", "임원회의", "tf")),
    ("투자/시장 축", ("증권", "거래", "여의도", "투자", "금융", "펀드", "vip룸", "브로커")),
    ("현장/공장 축", ("공장", "창고", "물류", "라인", "차고지", "항구", "조선소", "산업단지", "시험평가대대")),
    ("가문/본가 축", ("본가", "저택", "식탁", "자택", "별채")),
    ("연구/실험 축", ("연구", "실험", "랩", "연구소")),
    ("학원/학교 축", ("학교", "교실", "강의실")),
)


@dataclass
class OpeningPacingTriageReport:
    work_id: str
    treatment_path: str | None
    triage_grade: str
    recommended_action: str
    evidence_mode: str
    observed_opening_block_count: int
    opening_window_complete: bool
    opening_contract_declared: bool
    reader_earning_gate_status: str
    macro_progression_gate_status: str
    first_public_signboard_block: int | None
    representative_reevaluation_block: int | None
    next_battlefield_ticket_block: int | None
    first_reader_earning_signal_block: int | None
    legacy_main_macro_battlefield: str | None
    opening_window_missing_blocks: list[int] = field(default_factory=list)
    legacy_main_macro_battlefield_blocks: list[int] = field(default_factory=list)
    legacy_main_macro_battlefield_share: float = 0.0
    legacy_macro_overstay: bool = False
    legacy_macro_resolution_modes: list[str] = field(default_factory=list)
    trigger_codes: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def load_json(path: Path | None) -> Any | None:
    if path is None or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def extract_blocks(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        blocks = payload.get("blocks")
        if isinstance(blocks, list):
            return [item for item in blocks if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def format_block(block_no: int | None) -> str:
    if block_no is None:
        return "-"
    return f"B{block_no:02d}"


def summarize_opening_window_coverage(blocks: list[dict[str, Any]]) -> tuple[bool, list[int]]:
    observed_block_nos: set[int] = set()
    for index, block in enumerate(blocks, start=1):
        block_no = parse_block_no(block.get("block_no")) or parse_block_no(block.get("block_id")) or index
        if 1 <= block_no <= OPENING_CONTRACT_END:
            observed_block_nos.add(block_no)
    missing = [block_no for block_no in range(1, OPENING_CONTRACT_END + 1) if block_no not in observed_block_nos]
    return not missing, missing


def normalize_place_head(place: str) -> str:
    if not place:
        return ""
    head = place.split("/")[0].strip()
    head = re.sub(r"\s+", " ", head)
    return head[:40]


def infer_legacy_macro_battlefield(block: dict[str, Any]) -> tuple[str, str]:
    declared = extract_macro_battlefield(block)
    if declared:
        return declared, "declared"

    location = block.get("location") if isinstance(block.get("location"), dict) else {}
    joined = " ".join(
        [
            as_text(location.get("place")),
            as_text(location.get("type")),
            as_text(block.get("title")),
        ]
    ).lower()
    for label, keywords in LEGACY_MACRO_KEYWORDS:
        if any(keyword.lower() in joined for keyword in keywords):
            return label, "legacy-keyword"

    place_head = normalize_place_head(as_text(location.get("place")))
    if place_head:
        return place_head, "legacy-place-head"

    location_type = as_text(location.get("type"))
    if location_type:
        return location_type, "legacy-location-type"
    return "", "none"


def summarize_legacy_opening_macro(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    opening_entries: list[tuple[int, str, str]] = []
    for index, block in enumerate(blocks, start=1):
        block_no = parse_block_no(block.get("block_no")) or parse_block_no(block.get("block_id")) or index
        if block_no < 1 or block_no > OPENING_CONTRACT_END:
            continue
        macro_battlefield, resolution = infer_legacy_macro_battlefield(block)
        opening_entries.append((block_no, macro_battlefield, resolution))

    window_entries = [
        (block_no, macro_battlefield)
        for block_no, macro_battlefield, _resolution in opening_entries
        if OPENING_READER_EARNING_SIGNAL_START <= block_no <= OPENING_MAIN_BATTLEFIELD_END and macro_battlefield
    ]
    resolutions = sorted({resolution for _block_no, _macro_battlefield, resolution in opening_entries if resolution != "none"})
    result = {
        "opening_macro_map": [
            {"block_no": block_no, "macro_battlefield": macro_battlefield, "resolution": resolution}
            for block_no, macro_battlefield, resolution in opening_entries
            if macro_battlefield
        ],
        "main_macro_battlefield": None,
        "main_macro_battlefield_blocks": [],
        "main_macro_battlefield_share": 0.0,
        "macro_overstay": False,
        "resolution_modes": resolutions,
        "evidence_mode": "legacy_sparse",
    }
    if not window_entries:
        return result

    macro_counter = Counter(macro_battlefield for _block_no, macro_battlefield in window_entries)
    main_macro, main_count = macro_counter.most_common(1)[0]
    main_blocks = [block_no for block_no, macro_battlefield in window_entries if macro_battlefield == main_macro]
    result["main_macro_battlefield"] = main_macro
    result["main_macro_battlefield_blocks"] = main_blocks
    result["main_macro_battlefield_share"] = round(main_count / len(window_entries) * 100, 1)
    result["macro_overstay"] = (
        OPENING_MAIN_BATTLEFIELD_END in main_blocks and main_count >= OPENING_MAIN_BATTLEFIELD_DOMINANCE_MIN
    )
    result["evidence_mode"] = "legacy_heuristic"
    return result


def grade_declared_contract(metrics: dict[str, Any]) -> tuple[str, str, list[str], list[str]]:
    trigger_codes: list[str] = []
    reasons: list[str] = []
    signboard_block = metrics.get("first_public_signboard_block")
    ticket_block = metrics.get("next_battlefield_ticket_block")

    if not metrics.get("opening_macro_progression_ok", True):
        trigger_codes.append("PACE-004")
        reasons.append("declared opening contract 기준으로 main macro battlefield 과체류가 확정됐다.")
        return "RED", "negative_exemplar_archive", trigger_codes, reasons

    if not metrics.get("opening_reader_earning_signal_by6", True):
        trigger_codes.append("PACE-003")
        reasons.append("declared opening contract 기준으로 TR 2~6 reader-earning signal이 늦다.")
        return "YELLOW", "manual_reaudit_then_repair", trigger_codes, reasons

    if signboard_block is not None and signboard_block >= 9:
        trigger_codes.append("SIGNBOARD-LATE")
        reasons.append(f"public signboard가 {format_block(signboard_block)}에 걸려 opening 폭발이 늦다.")
        return "YELLOW", "manual_reaudit_then_repair", trigger_codes, reasons

    if ticket_block is not None and ticket_block >= 9:
        trigger_codes.append("TICKET-LATE")
        reasons.append(f"next battlefield ticket이 {format_block(ticket_block)}로 밀린다.")
        return "YELLOW", "manual_reaudit_then_repair", trigger_codes, reasons

    trigger_codes.append("DECLARED-PASS")
    reasons.append("declared opening contract 기준에서 구조적 pacing 붕괴가 발견되지 않았다.")
    return "GREEN", "keep_active_inventory", trigger_codes, reasons


def grade_legacy_opening(metrics: dict[str, Any], legacy_macro: dict[str, Any]) -> tuple[str, str, list[str], list[str], list[str]]:
    trigger_codes: list[str] = []
    reasons: list[str] = []
    notes = ["opening contract 필드가 없어 legacy heuristic으로 판정했다."]
    signboard_block = metrics.get("first_public_signboard_block")
    reevaluation_block = metrics.get("representative_reevaluation_block")
    ticket_block = metrics.get("next_battlefield_ticket_block")
    overstay = legacy_macro.get("macro_overstay", False)
    main_macro = legacy_macro.get("main_macro_battlefield")

    if overstay and (signboard_block is None or signboard_block >= 9):
        trigger_codes.extend(["LEGACY-MACRO-OVERSTAY", "LEGACY-SIGNBOARD-LATE"])
        reasons.append(
            f"{main_macro or 'opening 전장'}이 {format_block(OPENING_READER_EARNING_SIGNAL_START)}~"
            f"{format_block(OPENING_MAIN_BATTLEFIELD_END)}을 과점한 채 public signboard가 "
            f"{format_block(signboard_block)}까지 밀렸다."
        )
        return "RED", "negative_exemplar_archive", trigger_codes, reasons, notes

    if signboard_block is None or signboard_block >= 9:
        trigger_codes.append("LEGACY-SIGNBOARD-LATE")
        reasons.append(f"public signboard가 {format_block(signboard_block)}라 opening 폭발 시점이 늦다.")

    if overstay and (reevaluation_block is None or reevaluation_block >= 8):
        trigger_codes.append("LEGACY-MACRO-OVERSTAY")
        reasons.append(
            f"{main_macro or 'opening 전장'}이 {format_block(OPENING_MAIN_BATTLEFIELD_END)}까지 길게 이어지고 "
            f"reevaluation도 {format_block(reevaluation_block)} 수준이다."
        )
    elif overstay and (signboard_block is None or signboard_block > 6):
        trigger_codes.append("LEGACY-MACRO-OVERSTAY")
        reasons.append(
            f"{main_macro or 'opening 전장'}이 opening을 오래 점유하고 signboard가 선호 구간 뒤로 밀린다."
        )

    if ticket_block is not None and ticket_block >= 9:
        trigger_codes.append("LEGACY-TICKET-LATE")
        reasons.append(f"next battlefield ticket이 {format_block(ticket_block)}에서야 드러난다.")

    if reevaluation_block is not None and reevaluation_block >= 8 and not overstay:
        trigger_codes.append("LEGACY-REEVALUATION-LATE")
        reasons.append(f"representative reevaluation이 {format_block(reevaluation_block)}로 늦다.")

    if trigger_codes:
        return "YELLOW", "manual_reaudit_then_repair", trigger_codes, reasons[:3], notes

    trigger_codes.append("LEGACY-PROVISIONAL-PASS")
    reasons.append("legacy heuristic 기준에서 discard 급 opening pacing 붕괴 신호는 없다.")
    return "GREEN", "keep_active_inventory", trigger_codes, reasons, notes


def build_report(work_id: str, treatment_path: Path | None) -> OpeningPacingTriageReport:
    if treatment_path is None or not treatment_path.is_file():
        return OpeningPacingTriageReport(
            work_id=work_id,
            treatment_path=str(treatment_path) if treatment_path else None,
            triage_grade="UNTRIAGED",
            recommended_action="missing_treatment_payload",
            evidence_mode="missing_treatment",
            observed_opening_block_count=0,
            opening_window_complete=False,
            opening_window_missing_blocks=list(range(1, OPENING_CONTRACT_END + 1)),
            opening_contract_declared=False,
            reader_earning_gate_status="unavailable",
            macro_progression_gate_status="unavailable",
            first_public_signboard_block=None,
            representative_reevaluation_block=None,
            next_battlefield_ticket_block=None,
            first_reader_earning_signal_block=None,
            legacy_main_macro_battlefield=None,
            trigger_codes=["TR-MISSING"],
            reasons=["treatment payload가 없어 opening pacing triage를 할 수 없다."],
        )

    payload = load_json(treatment_path)
    metrics = compute_treatment_metrics(payload)
    blocks = extract_blocks(payload)
    opening_window_complete, opening_window_missing_blocks = summarize_opening_window_coverage(blocks)
    if not opening_window_complete:
        missing_summary = ", ".join(format_block(block_no) for block_no in opening_window_missing_blocks)
        return OpeningPacingTriageReport(
            work_id=work_id,
            treatment_path=str(treatment_path),
            triage_grade="UNTRIAGED",
            recommended_action="hold_until_opening_window_complete",
            evidence_mode="insufficient_opening_window",
            observed_opening_block_count=int(metrics.get("observed_opening_block_count") or 0),
            opening_window_complete=False,
            opening_window_missing_blocks=opening_window_missing_blocks,
            opening_contract_declared=bool(metrics.get("opening_contract_declared")),
            reader_earning_gate_status="unavailable",
            macro_progression_gate_status="unavailable",
            first_public_signboard_block=metrics.get("first_public_signboard_block"),
            representative_reevaluation_block=metrics.get("representative_reevaluation_block"),
            next_battlefield_ticket_block=metrics.get("next_battlefield_ticket_block"),
            first_reader_earning_signal_block=metrics.get("first_reader_earning_signal_block"),
            legacy_main_macro_battlefield=None,
            trigger_codes=["OPENING-WINDOW-INCOMPLETE"],
            reasons=[f"opening pacing triage에 필요한 B01~B10 window가 비어 있다: {missing_summary}"],
            notes=["filename이 아니라 실제 opening block coverage 기준으로 판정 보류했다."],
        )

    legacy_macro = summarize_legacy_opening_macro(blocks)
    opening_contract_declared = bool(metrics.get("opening_contract_declared"))

    if opening_contract_declared:
        triage_grade, recommended_action, trigger_codes, reasons = grade_declared_contract(metrics)
        evidence_mode = "declared_contract"
        notes: list[str] = []
    else:
        triage_grade, recommended_action, trigger_codes, reasons, notes = grade_legacy_opening(metrics, legacy_macro)
        evidence_mode = legacy_macro.get("evidence_mode", "legacy_sparse")

    observed_opening_block_count = int(metrics.get("observed_opening_block_count") or 0)
    reader_gate_status = (
        "pass"
        if opening_contract_declared and observed_opening_block_count >= OPENING_READER_EARNING_SIGNAL_END and metrics.get("opening_reader_earning_signal_by6", True)
        else "fail"
        if opening_contract_declared and observed_opening_block_count >= OPENING_READER_EARNING_SIGNAL_END
        else "unavailable"
    )
    macro_gate_status = (
        "pass"
        if opening_contract_declared and observed_opening_block_count >= OPENING_MAIN_BATTLEFIELD_END and metrics.get("opening_macro_progression_ok", True)
        else "fail"
        if opening_contract_declared and observed_opening_block_count >= OPENING_MAIN_BATTLEFIELD_END
        else "unavailable"
    )

    if not opening_contract_declared and legacy_macro.get("resolution_modes"):
        notes.append(f"legacy macro resolution: {', '.join(legacy_macro['resolution_modes'])}")

    return OpeningPacingTriageReport(
        work_id=work_id,
        treatment_path=str(treatment_path),
        triage_grade=triage_grade,
        recommended_action=recommended_action,
        evidence_mode=evidence_mode,
        observed_opening_block_count=observed_opening_block_count,
        opening_window_complete=True,
        opening_window_missing_blocks=[],
        opening_contract_declared=opening_contract_declared,
        reader_earning_gate_status=reader_gate_status,
        macro_progression_gate_status=macro_gate_status,
        first_public_signboard_block=metrics.get("first_public_signboard_block"),
        representative_reevaluation_block=metrics.get("representative_reevaluation_block"),
        next_battlefield_ticket_block=metrics.get("next_battlefield_ticket_block"),
        first_reader_earning_signal_block=metrics.get("first_reader_earning_signal_block"),
        legacy_main_macro_battlefield=legacy_macro.get("main_macro_battlefield"),
        legacy_main_macro_battlefield_blocks=legacy_macro.get("main_macro_battlefield_blocks", []),
        legacy_main_macro_battlefield_share=legacy_macro.get("main_macro_battlefield_share", 0.0),
        legacy_macro_overstay=legacy_macro.get("macro_overstay", False),
        legacy_macro_resolution_modes=legacy_macro.get("resolution_modes", []),
        trigger_codes=trigger_codes,
        reasons=reasons,
        notes=notes[:4],
    )


def render_text(reports: list[OpeningPacingTriageReport]) -> str:
    lines = [f"Scanned {len(reports)} pair(s) for opening pacing triage"]
    counts = Counter(report.triage_grade for report in reports)
    lines.append(
        " | ".join(
            [
                f"RED={counts.get('RED', 0)}",
                f"YELLOW={counts.get('YELLOW', 0)}",
                f"GREEN={counts.get('GREEN', 0)}",
                f"UNTRIAGED={counts.get('UNTRIAGED', 0)}",
            ]
        )
    )
    for report in sorted(reports, key=lambda item: (GRADE_ORDER.get(item.triage_grade, 99), item.work_id)):
        lines.append(
            " | ".join(
                [
                    report.triage_grade,
                    report.work_id,
                    f"action={report.recommended_action}",
                    f"evidence={report.evidence_mode}",
                    f"signboard={format_block(report.first_public_signboard_block)}",
                    f"reeval={format_block(report.representative_reevaluation_block)}",
                    f"ticket={format_block(report.next_battlefield_ticket_block)}",
                    f"opening_window={'complete' if report.opening_window_complete else 'incomplete'}",
                    f"macro={report.legacy_main_macro_battlefield or '-'}",
                    f"overstay={'yes' if report.legacy_macro_overstay else 'no'}",
                ]
            )
        )
        if report.reasons:
            lines.append(f"  reasons: {' | '.join(report.reasons[:3])}")
        if report.notes:
            lines.append(f"  notes: {' | '.join(report.notes[:2])}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--treatment", type=Path, help="Single TR JSON path")
    parser.add_argument("--treatment-dir", type=Path, default=LIVE_TREATMENT_DIR, help="Live TR directory")
    parser.add_argument("--work-id", action="append", default=[], help="Restrict scan to one or more normalized work ids")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.treatment:
        inferred_work_id = normalize_work_id(args.treatment.stem.replace("_tr_block_070_draft", ""))
        pairs = [(inferred_work_id, None, args.treatment)]
    else:
        pairs = collect_live_pairs(ROOT / "bible", args.treatment_dir)

    if args.work_id:
        wanted = {normalize_work_id(value) for value in args.work_id}
        pairs = [pair for pair in pairs if pair[0] in wanted]

    reports = [build_report(work_id, treatment_path) for work_id, _bible_path, treatment_path in pairs]

    if args.json:
        print(json.dumps({"results": [asdict(report) for report in reports]}, ensure_ascii=False, indent=2))
    else:
        print(render_text(reports))

    return 1 if any(report.triage_grade == "RED" for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
