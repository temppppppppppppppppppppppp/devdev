#!/usr/bin/env python3
"""Run a deterministic 5-pass audit for a BI JSON against phase0 and treatment draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.response_schemas import validate_bible_structure, validate_treatment_structure

GARBLED_RE = re.compile(r"\?{2,}|�|\ufffd")
FOREIGN_TOKENS = [
    "골든 루트",
    "한시우",
    "SW인베스트먼트",
    "노스스타",
    "퀀텀바이오",
    "오로라 미디어",
    "엠파이어 리본",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def parse_eok(raw: Any) -> int | None:
    if not isinstance(raw, str):
        return None
    text = raw.replace(" ", "")
    match = re.fullmatch(r"(?:(\d+)조)?(?:(\d+)억)?", text)
    if not match:
        return None
    jo = int(match.group(1) or 0)
    eok = int(match.group(2) or 0)
    return jo * 10000 + eok


def sample_fields(bi: dict[str, Any]) -> list[tuple[str, str]]:
    mb = bi["MasterBible"]
    meta = mb["ProjectData"]["MetaInfo"]
    core = mb["ProjectData"]["CoreIdentity"]
    actual = mb["FinanceHUD"]["Protagonist"]["actual_truth"]
    world = mb["WorldState"]
    key_npcs = mb["AssetLibrary"]["KeyNPCs"]
    roadmap = mb["plot_roadmap"]
    samples = [
        ("MetaInfo.title", meta["title"]),
        ("MetaInfo.grand_objective", meta["grand_objective"]),
        ("MetaInfo.genre_archetype", meta["genre_archetype"]),
        ("MetaInfo.logline", meta["logline"]),
        ("CoreIdentity.protagonist", core["protagonist"]),
        ("CoreIdentity.protagonist_faction", core["protagonist_faction"]),
        ("CoreIdentity.edge", core["edge"]),
        ("CoreIdentity.desire", core["desire"]),
        ("CoreIdentity.crisis", core["crisis"]),
        ("FinanceHUD.actual_truth.name", actual["name"]),
        ("FinanceHUD.actual_truth.rank", actual["rank"]),
        ("FinanceHUD.actual_truth.current_objective", actual["current_objective"]),
        ("FinanceHUD.actual_truth.final_goal", actual["final_goal"]),
        ("WorldState.CurrentEra", world["CurrentEra"]),
        ("WorldState.CurrentLocation", world["CurrentLocation"]),
        ("KeyNPCs[0].name", key_npcs[0]["name"]),
        ("KeyNPCs[1].name", key_npcs[1]["name"]),
        ("KeyNPCs[2].name", key_npcs[2]["name"]),
        ("plot_roadmap[0].title", roadmap[0]["title"]),
        ("plot_roadmap[34].title", roadmap[34]["title"]),
        ("plot_roadmap[69].title", roadmap[69]["title"]),
    ]
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase0", type=Path, required=True, help="Phase0 design JSON path")
    parser.add_argument("--draft", type=Path, required=True, help="Treatment draft JSON path")
    parser.add_argument("--bi", type=Path, required=True, help="Bible JSON path")
    parser.add_argument("--report", type=Path, required=True, help="Markdown report output path")
    args = parser.parse_args()

    report_lines: list[str] = []
    fail_count = 0

    phase0 = load_json(args.phase0)
    draft = load_json(args.draft)
    bi = load_json(args.bi)

    draft_valid, draft_errors, draft_warnings = validate_treatment_structure(draft)
    bi_valid, bi_errors, bi_warnings = validate_bible_structure(bi)

    mb = bi["MasterBible"]
    meta = mb["ProjectData"]["MetaInfo"]
    core = mb["ProjectData"]["CoreIdentity"]
    actual = mb["FinanceHUD"]["Protagonist"]["actual_truth"]
    roadmap = mb.get("plot_roadmap", [])
    starter_company = phase0["setting"]["starter_company"]["name"]
    expected_title = phase0["project"]["title_ko"]
    expected_protagonist = phase0["protagonist"]["name"]
    expected_npcs = [phase0["protagonist"]["name"], *[npc["name"] for npc in phase0["phase0_design"]["npc_timeline"]]]

    serialized = json.dumps(bi, ensure_ascii=False)
    garbled_matches = GARBLED_RE.findall(serialized)

    portfolio_history = actual["portfolio_history"]
    portfolio_monotonic = True
    portfolio_sync = True
    last_amount: int | None = None
    for entry in portfolio_history:
        amount = parse_eok(entry.get("total_assets"))
        if amount is None:
            portfolio_monotonic = False
            portfolio_sync = False
            break
        if last_amount is not None and amount < last_amount:
            portfolio_monotonic = False
        block_no = int(entry["block"])
        tr_amount = parse_eok(draft[block_no - 1]["genre_ext"]["capital_after"])
        if tr_amount != amount:
            portfolio_sync = False
        last_amount = amount

    title_seq_match = [block["title"] for block in roadmap] == [block["title"] for block in draft]
    first_last_match = (
        len(roadmap) == len(draft)
        and roadmap[0]["title"] == draft[0]["title"]
        and roadmap[-1]["title"] == draft[-1]["title"]
    )
    roadmap_hash_match = stable_hash(roadmap) == stable_hash(draft)

    sample_pairs = sample_fields(bi)
    sample_clean = all(not GARBLED_RE.search(value) for _, value in sample_pairs)

    foreign_hits = [token for token in FOREIGN_TOKENS if token in serialized]
    key_npc_names = [entry["name"] for entry in mb["AssetLibrary"]["KeyNPCs"]]
    npc_name_match = key_npc_names == expected_npcs

    passes = [
        (
            "PASS 1",
            "인코딩/파싱",
            {
                "utf8_json_parse": True,
                "garbled_token_zero": len(garbled_matches) == 0,
                "draft_schema_valid": draft_valid,
            },
        ),
        (
            "PASS 2",
            "최소 스키마",
            {
                "validate_bible_structure": bi_valid,
                "meta_title_present": bool(meta.get("title")),
                "plot_roadmap_len_70": len(roadmap) == 70,
            },
        ),
        (
            "PASS 3",
            "내부 정합성",
            {
                "protagonist_match": core["protagonist"] == actual["name"] == expected_protagonist,
                "title_match_phase0": meta["title"] == expected_title,
                "starter_company_match": actual["financial_status"]["company"] == starter_company,
                "portfolio_monotonic": portfolio_monotonic,
                "portfolio_sync_with_tr": portfolio_sync,
            },
        ),
        (
            "PASS 4",
            "TR↔BI 동기화",
            {
                "roadmap_title_sequence": title_seq_match,
                "roadmap_first_last": first_last_match,
                "roadmap_hash_equal": roadmap_hash_match,
            },
        ),
        (
            "PASS 5",
            "품질 감리",
            {
                "sample_fields_clean": sample_clean,
                "foreign_token_zero": len(foreign_hits) == 0,
                "company_name_consistent": starter_company in serialized,
                "npc_name_consistent": npc_name_match,
            },
        ),
    ]

    report_lines.append(f"# BI 5-Pass 감리 보고서 ({date.today()})")
    report_lines.append("")
    report_lines.append("## 대상")
    report_lines.append(f"- phase0: `{args.phase0.as_posix()}`")
    report_lines.append(f"- draft: `{args.draft.as_posix()}`")
    report_lines.append(f"- bi: `{args.bi.as_posix()}`")
    report_lines.append("")

    for pass_name, label, checks in passes:
        pass_ok = all(checks.values())
        if not pass_ok:
            fail_count += 1
        report_lines.append(f"## {pass_name}: {label}")
        report_lines.append(f"- result: {'OK' if pass_ok else 'FAIL'}")
        for key, ok in checks.items():
            report_lines.append(f"- {key}: {'OK' if ok else 'FAIL'}")
        report_lines.append("")

    report_lines.append("## 샘플링")
    for path, value in sample_pairs:
        report_lines.append(f"- {path}: {value}")
    report_lines.append("")

    report_lines.append("## 메모")
    if draft_errors:
        report_lines.append(f"- draft_errors: {draft_errors}")
    if draft_warnings:
        report_lines.append(f"- draft_warnings: {draft_warnings}")
    if bi_errors:
        report_lines.append(f"- bi_errors: {bi_errors}")
    if bi_warnings:
        report_lines.append(f"- bi_warnings: {bi_warnings}")
    if garbled_matches:
        report_lines.append(f"- garbled_matches: {garbled_matches[:20]}")
    if foreign_hits:
        report_lines.append(f"- foreign_hits: {foreign_hits}")
    if fail_count == 0:
        report_lines.append("- summary: 5개 PASS 모두 통과")
    else:
        report_lines.append(f"- summary: {fail_count}개 PASS 실패")
    report_lines.append("")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"[OK] audit report written: {args.report}")
    print(f"[RESULT] {'PASS' if fail_count == 0 else 'FAIL'}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
