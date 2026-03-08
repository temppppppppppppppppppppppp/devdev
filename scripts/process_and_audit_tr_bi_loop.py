#!/usr/bin/env python3
"""Full processing + 3-pass audit loop until confidence target is met."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.response_schemas import validate_bible_structure, validate_treatment_structure


TR_BI_PAIRS = [
    ("dynasty_heir_possession", "a"),
    ("franchise_tycoon_possession", "b"),
    ("entertainment_ceo_possession", "c"),
    ("northstar_logistics", "d"),
    ("quantum_bio", "e"),
    ("aegis_city", "f"),
    ("aurora_media", "g"),
    ("empire_reborn", "h"),
]

TARGET_CONFIDENCE = 99.0
MAX_ITERATIONS = 6
TIME_RE = re.compile(r"\d{4}년\s*\d{1,2}월(?:~\d{1,2}월)?")
BANNED_TOKENS = ["???", "보내는다", "핵심 딱", "정규화되었다."]


@dataclass
class PairAudit:
    key: str
    bi_name: str
    confidence: float
    checks: dict[str, bool]
    notes: list[str]


def run_cmd(args: list[str]) -> None:
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")


def process_all() -> None:
    run_cmd([sys.executable, "-X", "utf8", "scripts/repair_tr_korean_utf8.py"])
    run_cmd([sys.executable, "-X", "utf8", "scripts/generate_tr_bibles.py", "--include-empire-reborn"])


def get_bi_path(tag: str) -> Path:
    candidates = sorted((ROOT / "bible").glob(f"{tag}_*_bi.json"))
    if not candidates:
        raise FileNotFoundError(f"BI file with tag '{tag}_' not found")
    return candidates[0]


def parse_eok(raw: Any) -> int | None:
    if not isinstance(raw, str):
        return None
    text = raw.replace(" ", "")
    m = re.fullmatch(r"(?:(\d+)조)?(?:(\d+)억)?", text)
    if not m:
        return None
    jo = int(m.group(1) or 0)
    eok = int(m.group(2) or 0)
    return jo * 10_000 + eok


def uniq_ratio(items: list[str]) -> float:
    if not items:
        return 0.0
    return len(set(items)) / len(items)


def no_banned_tokens(text: str) -> bool:
    return all(tok not in text for tok in BANNED_TOKENS)


def audit_pair(key: str, tag: str) -> PairAudit:
    tr_path = ROOT / "treatments" / f"{key}_tr_block_070_draft.json"
    bi_path = get_bi_path(tag)

    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    bi = json.loads(bi_path.read_text(encoding="utf-8"))
    mb = bi.get("MasterBible", {})
    roadmap = mb.get("plot_roadmap", [])

    checks: dict[str, bool] = {}
    notes: list[str] = []

    tr_valid, tr_errors, _tr_warnings = validate_treatment_structure(tr)
    checks["tr_valid_schema"] = tr_valid
    if tr_errors:
        notes.append(f"TR schema errors: {len(tr_errors)}")

    checks["tr_len_70"] = isinstance(tr, list) and len(tr) == 70
    checks["tr_block_id_seq"] = all(
        isinstance(b, dict) and b.get("block_id") == f"Block {i}"
        for i, b in enumerate(tr, start=1)
    )

    povs = {b.get("pov_character") for b in tr if isinstance(b, dict)}
    checks["tr_single_pov"] = len(povs) == 1 and all(isinstance(p, str) and p.strip() for p in povs)

    checks["tr_time_format"] = all(
        bool(TIME_RE.search(str((b.get("time_span") or {}).get("in_story_time", ""))))
        for b in tr
        if isinstance(b, dict)
    )

    checks["tr_content_fields"] = all(
        isinstance(b.get("content"), dict)
        and all(k in b["content"] and isinstance(b["content"][k], str) and b["content"][k].strip() for k in ["context", "event_villain", "solution", "reward"])
        for b in tr
        if isinstance(b, dict)
    )

    whole_tr = json.dumps(tr, ensure_ascii=False)
    checks["tr_no_banned_tokens"] = no_banned_tokens(whole_tr)

    before_vals: list[int] = []
    after_vals: list[int] = []
    cap_parse_ok = True
    intra_ok = True
    inter_ok = True
    prev_after: int | None = None
    for b in tr:
        g = b.get("genre_ext", {}) if isinstance(b, dict) else {}
        before = parse_eok(g.get("capital_before"))
        after = parse_eok(g.get("capital_after"))
        if before is None or after is None:
            cap_parse_ok = False
            break
        before_vals.append(before)
        after_vals.append(after)
        if after < before:
            intra_ok = False
        if prev_after is not None and before < prev_after:
            inter_ok = False
        prev_after = after
    checks["tr_capital_parse_ok"] = cap_parse_ok
    checks["tr_capital_intra_ok"] = intra_ok
    checks["tr_capital_inter_ok"] = inter_ok

    contexts = [b["content"]["context"] for b in tr if isinstance(b, dict)]
    villains = [b["content"]["event_villain"] for b in tr if isinstance(b, dict)]
    solutions = [b["content"]["solution"] for b in tr if isinstance(b, dict)]
    stakes = [str(b.get("stakes", "")) for b in tr if isinstance(b, dict)]
    ppro = [str((b.get("power_shift") or {}).get("protagonist", "")) for b in tr if isinstance(b, dict)]

    checks["tr_context_diversity"] = uniq_ratio(contexts) >= 0.90
    checks["tr_villain_diversity"] = uniq_ratio(villains) >= 0.80
    checks["tr_solution_diversity"] = uniq_ratio(solutions) >= 0.80
    checks["tr_stakes_diversity"] = uniq_ratio(stakes) >= 0.80
    checks["tr_power_diversity"] = uniq_ratio(ppro) >= 0.75

    bi_valid, bi_errors, _bi_warnings = validate_bible_structure(bi)
    checks["bi_valid_schema"] = bi_valid
    if bi_errors:
        notes.append(f"BI schema errors: {len(bi_errors)}")

    core_pro = mb.get("ProjectData", {}).get("CoreIdentity", {}).get("protagonist", "")
    hud_pro = mb.get("FinanceHUD", {}).get("Protagonist", {}).get("actual_truth", {}).get("name", "")
    checks["bi_protagonist_consistent"] = bool(core_pro) and core_pro == hud_pro
    checks["bi_plot_roadmap_70"] = isinstance(roadmap, list) and len(roadmap) == 70
    checks["bi_no_banned_tokens"] = no_banned_tokens(json.dumps(bi, ensure_ascii=False))

    tr_first_pro = tr[0].get("pov_character", "") if tr else ""
    tr_reg = str((tr[0].get("regression_ext") or {}).get("regression_type", "")) if tr else ""
    bi_inc = str(mb.get("protagonist_config", {}).get("incarnation_type", ""))
    checks["cross_protagonist_match"] = tr_first_pro == core_pro
    checks["cross_regression_match"] = (("회귀" in tr_reg) and ("회귀" in bi_inc)) or (("빙의" in tr_reg) and ("빙의" in bi_inc))

    tr_hash = hashlib.sha256(json.dumps(tr, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    rr_hash = hashlib.sha256(json.dumps(roadmap, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    checks["cross_roadmap_hash_equal"] = tr_hash == rr_hash
    checks["cross_edge_title_match"] = bool(tr) and bool(roadmap) and tr[0].get("title") == roadmap[0].get("title") and tr[-1].get("title") == roadmap[-1].get("title")

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    confidence = round((passed / total) * 100.0, 2)
    return PairAudit(key=key, bi_name=bi_path.name, confidence=confidence, checks=checks, notes=notes)


def run_audit_round(round_no: int) -> tuple[float, list[PairAudit]]:
    pair_results = [audit_pair(key, tag) for key, tag in TR_BI_PAIRS]
    overall = round(mean(r.confidence for r in pair_results), 2)
    print(f"[Round {round_no}] overall confidence: {overall}%")
    for r in pair_results:
        print(f"  - {r.key}: {r.confidence}% ({r.bi_name})")
    return overall, pair_results


def write_report(
    history: list[dict[str, Any]],
    final_confidence: float,
    success: bool,
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# TR/BI 전체 처리 + 감리 루프 보고서 ({date.today()})")
    lines.append("")
    lines.append(f"- 목표 신뢰도: {TARGET_CONFIDENCE}%")
    lines.append(f"- 최종 신뢰도: {final_confidence}%")
    lines.append(f"- 달성 여부: {'달성' if success else '미달'}")
    lines.append("")
    for item in history:
        lines.append(f"## Iteration {item['iteration']}")
        lines.append(f"- round_confidences: {item['round_confidences']}")
        lines.append(f"- stable_confidence(min): {item['stable_confidence']}%")
        lines.append("")
        for r in item["pairs"]:
            lines.append(f"### {r.key} ({r.bi_name})")
            lines.append(f"- confidence: {r.confidence}%")
            for k, v in r.checks.items():
                lines.append(f"- {k}: {'OK' if v else 'FAIL'}")
            if r.notes:
                for note in r.notes:
                    lines.append(f"- note: {note}")
            lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    history: list[dict[str, Any]] = []
    success = False
    final_conf = 0.0

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n=== Iteration {iteration} ===")
        process_all()

        round_scores: list[float] = []
        latest_pairs: list[PairAudit] = []
        for round_no in range(1, 4):
            score, pairs = run_audit_round(round_no)
            round_scores.append(score)
            latest_pairs = pairs

        stable_conf = round(min(round_scores), 2)
        history.append(
            {
                "iteration": iteration,
                "round_confidences": round_scores,
                "stable_confidence": stable_conf,
                "pairs": latest_pairs,
            }
        )

        if stable_conf >= TARGET_CONFIDENCE and all(all(v for v in p.checks.values()) for p in latest_pairs):
            success = True
            final_conf = stable_conf
            break
        final_conf = stable_conf

    report_path = ROOT / "docs" / str(date.today()) / "tr-bi-loop-audit-report.md"
    write_report(history, final_conf, success, report_path)
    print(f"\nReport: {report_path}")
    print(f"Final confidence: {final_conf}%")
    print(f"Success: {success}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
