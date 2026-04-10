#!/usr/bin/env python3
"""Triage live production TR pairs for mid/late whole-run pacing drag."""

from __future__ import annotations

import argparse
import json
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
    as_text,
    bundle_size,
    compute_treatment_metrics,
    extract_macro_battlefield,
    has_recognition_signal,
    parse_block_no,
)

WINDOW_SIZE = 10
MIN_BLOCKS_FOR_WHOLE_RUN_TRIAGE = 30
GRADE_ORDER = {"YELLOW": 0, "GREEN": 1, "UNTRIAGED": 2}


@dataclass
class WholeRunWindowReport:
    start_block: int
    end_block: int
    dominant_macro_battlefield: str | None
    dominant_macro_share: float
    recognition_signal_count: int
    avg_bundle_chars: float


@dataclass
class WholeRunPacingReport:
    work_id: str
    treatment_path: str | None
    triage_grade: str
    recommended_action: str
    evidence_mode: str
    block_count: int
    assessed_window_count: int
    late_window_available: bool
    production_density_gate: bool
    late_blank_opponent_blocks: list[int] = field(default_factory=list)
    endgame_low_stakes_blocks: list[int] = field(default_factory=list)
    slow_windows: list[WholeRunWindowReport] = field(default_factory=list)
    trigger_codes: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


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


def _place_head(block: dict[str, Any]) -> str:
    place = as_text(((block.get("location") or {}).get("place")))
    if not place:
        return ""
    return place.split("/")[0].strip()


def _ordered_blocks(blocks: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    ordered: list[tuple[int, dict[str, Any]]] = []
    for index, block in enumerate(blocks, start=1):
        block_no = parse_block_no(block.get("block_no")) or parse_block_no(block.get("block_id")) or index
        ordered.append((block_no, block))
    ordered.sort(key=lambda item: item[0])
    return ordered


def summarize_windows(blocks: list[dict[str, Any]]) -> list[WholeRunWindowReport]:
    ordered = _ordered_blocks(blocks)
    reports: list[WholeRunWindowReport] = []
    for start_index in range(0, len(ordered), WINDOW_SIZE):
        chunk = ordered[start_index : start_index + WINDOW_SIZE]
        if not chunk:
            continue
        chunk_macros: list[str] = []
        for _block_no, block in chunk:
            macro = extract_macro_battlefield(block) or _place_head(block)
            if macro:
                chunk_macros.append(macro)
        dominant_macro = None
        dominant_share = 0.0
        if chunk_macros:
            dominant_macro, dominant_count = Counter(chunk_macros).most_common(1)[0]
            dominant_share = round(dominant_count / len(chunk) * 100, 1)
        recognition_signal_count = sum(1 for _block_no, block in chunk if has_recognition_signal(block))
        avg_bundle_chars = round(sum(bundle_size(block) for _block_no, block in chunk) / len(chunk), 1)
        reports.append(
            WholeRunWindowReport(
                start_block=chunk[0][0],
                end_block=chunk[-1][0],
                dominant_macro_battlefield=dominant_macro,
                dominant_macro_share=dominant_share,
                recognition_signal_count=recognition_signal_count,
                avg_bundle_chars=avg_bundle_chars,
            )
        )
    return reports


def is_slow_window(window: WholeRunWindowReport) -> bool:
    if window.start_block <= WINDOW_SIZE:
        return False
    if window.dominant_macro_share >= 80 and window.recognition_signal_count <= 2 and window.avg_bundle_chars < 750:
        return True
    if window.dominant_macro_share >= 60 and window.recognition_signal_count <= 1 and window.avg_bundle_chars < 650:
        return True
    return False


def build_report(work_id: str, treatment_path: Path | None) -> WholeRunPacingReport:
    if treatment_path is None or not treatment_path.is_file():
        return WholeRunPacingReport(
            work_id=work_id,
            treatment_path=str(treatment_path) if treatment_path else None,
            triage_grade="UNTRIAGED",
            recommended_action="missing_treatment_payload",
            evidence_mode="missing_treatment",
            block_count=0,
            assessed_window_count=0,
            late_window_available=False,
            production_density_gate=False,
            trigger_codes=["TR-MISSING"],
            reasons=["treatment payload가 없어 whole-run pacing triage를 할 수 없다."],
        )

    payload = load_json(treatment_path)
    blocks = extract_blocks(payload)
    metrics = compute_treatment_metrics(payload)
    block_count = int(metrics.get("block_count") or len(blocks))
    windows = summarize_windows(blocks)
    slow_windows = [window for window in windows if is_slow_window(window)]
    late_blank_opponent_blocks = list(metrics.get("late_blank_opponent_blocks") or [])
    endgame_low_stakes_blocks = list(metrics.get("endgame_low_stakes_blocks") or [])
    late_window_available = block_count >= MIN_BLOCKS_FOR_WHOLE_RUN_TRIAGE

    if block_count < MIN_BLOCKS_FOR_WHOLE_RUN_TRIAGE:
        return WholeRunPacingReport(
            work_id=work_id,
            treatment_path=str(treatment_path),
            triage_grade="UNTRIAGED",
            recommended_action="hold_until_mid_late_window_exists",
            evidence_mode="insufficient_mid_late_coverage",
            block_count=block_count,
            assessed_window_count=len(windows),
            late_window_available=False,
            production_density_gate=bool(metrics.get("production_density_gate")),
            late_blank_opponent_blocks=late_blank_opponent_blocks,
            endgame_low_stakes_blocks=endgame_low_stakes_blocks,
            slow_windows=slow_windows,
            trigger_codes=["WHOLE-RUN-COVERAGE-INSUFFICIENT"],
            reasons=[f"middle/late pacing triage에 필요한 block coverage가 부족하다: observed={block_count}"],
            notes=["whole-run pacing은 opening-only keep과 별도로 본다."],
        )

    trigger_codes: list[str] = []
    reasons: list[str] = []
    notes: list[str] = []
    if slow_windows:
        trigger_codes.append("MID-LATE-SLOW-WINDOW")
        window_labels = ", ".join(f"B{item.start_block:02d}-B{item.end_block:02d}" for item in slow_windows[:3])
        reasons.append(f"중반/후반 10-block window에서 pacing drag 의심 구간이 보인다: {window_labels}")
    if len(late_blank_opponent_blocks) >= 3:
        trigger_codes.append("LATE-BLANK-OPPONENT")
        reasons.append(f"후반 blank opponent block이 과다하다: {late_blank_opponent_blocks}")
    if endgame_low_stakes_blocks:
        trigger_codes.append("ENDGAME-LOW-STAKES")
        reasons.append(f"후반 stakes 저하 block이 있다: {endgame_low_stakes_blocks}")

    if trigger_codes:
        notes.append("opening keep 판정과 별개로 whole-run pacing drag 신호가 발견됐다.")
        return WholeRunPacingReport(
            work_id=work_id,
            treatment_path=str(treatment_path),
            triage_grade="YELLOW",
            recommended_action="manual_reaudit_then_repair",
            evidence_mode="whole_run_window_heuristic",
            block_count=block_count,
            assessed_window_count=len(windows),
            late_window_available=late_window_available,
            production_density_gate=bool(metrics.get("production_density_gate")),
            late_blank_opponent_blocks=late_blank_opponent_blocks,
            endgame_low_stakes_blocks=endgame_low_stakes_blocks,
            slow_windows=slow_windows,
            trigger_codes=trigger_codes,
            reasons=reasons,
            notes=notes,
        )

    return WholeRunPacingReport(
        work_id=work_id,
        treatment_path=str(treatment_path),
        triage_grade="GREEN",
        recommended_action="keep_active_inventory",
        evidence_mode="whole_run_window_heuristic",
        block_count=block_count,
        assessed_window_count=len(windows),
        late_window_available=late_window_available,
        production_density_gate=bool(metrics.get("production_density_gate")),
        late_blank_opponent_blocks=late_blank_opponent_blocks,
        endgame_low_stakes_blocks=endgame_low_stakes_blocks,
        slow_windows=slow_windows,
        trigger_codes=["WHOLE-RUN-PROVISIONAL-PASS"],
        reasons=["중반/후반 pacing drag 신호가 현재 evidence 기준으로 발견되지 않았다."],
        notes=["opening keep과 whole-run keep은 서로 다른 판정이다."],
    )


def render_text(reports: list[WholeRunPacingReport]) -> str:
    lines = [f"Scanned {len(reports)} pair(s) for whole-run pacing triage"]
    counts = Counter(report.triage_grade for report in reports)
    lines.append(
        " | ".join(
            [
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
                    f"blocks={report.block_count}",
                    f"windows={report.assessed_window_count}",
                    f"late_window={'yes' if report.late_window_available else 'no'}",
                    f"late_blank_opponent={len(report.late_blank_opponent_blocks)}",
                    f"endgame_low_stakes={len(report.endgame_low_stakes_blocks)}",
                    f"slow_windows={len(report.slow_windows)}",
                ]
            )
        )
        if report.reasons:
            lines.append(f"  reasons: {' | '.join(report.reasons[:3])}")
        if report.slow_windows:
            window_text = ", ".join(
                f"B{item.start_block:02d}-B{item.end_block:02d}(macro_share={item.dominant_macro_share}, recog={item.recognition_signal_count}, avg_bundle={item.avg_bundle_chars})"
                for item in report.slow_windows[:3]
            )
            lines.append(f"  slow_windows: {window_text}")
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

    return 1 if any(report.triage_grade == "YELLOW" for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
