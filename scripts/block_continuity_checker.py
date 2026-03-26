#!/usr/bin/env python3
"""블록 연속성 자동 검증 스크립트.

연속된 블록 간 genre_ext / martial_ext 값의 인과적 연속성을 검사한다.
- blockguide: capital_after[N] == capital_before[N+1]
- wuxguide:   realm_after[N] == realm_before[N+1]
              internal_energy_after[N] == internal_energy_before[N+1]
              injury_status 이월 정합성

Usage:
    python block_continuity_checker.py --work-id golden_canary --family blockguide
    python block_continuity_checker.py --work-id samryu_jangmunin --family wuxguide
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_treatment(work_id: str) -> dict[str, Any]:
    """treatments/{work_id}_tr_block_070_draft.json 을 로드한다."""
    base = Path(__file__).resolve().parent.parent / "treatments"
    filepath = base / f"{work_id}_tr_block_070_draft.json"
    if not filepath.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {filepath}", file=sys.stderr)
        sys.exit(2)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_get(d: dict, *keys: str, default: Any = None) -> Any:
    """중첩 딕셔너리에서 키 체인을 따라 안전하게 값을 가져온다."""
    current = d
    for k in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(k, default)
        if current is default:
            return default
    return current


def check_blockguide(blocks: list[dict]) -> list[str]:
    """blockguide 계열: capital_after[N] == capital_before[N+1]."""
    mismatches: list[str] = []
    for i in range(len(blocks) - 1):
        b_curr = blocks[i]
        b_next = blocks[i + 1]
        block_n = b_curr.get("block", i + 1)
        block_n1 = b_next.get("block", i + 2)

        cap_after = safe_get(b_curr, "genre_ext", "capital_after")
        cap_before = safe_get(b_next, "genre_ext", "capital_before")

        if cap_after is None:
            mismatches.append(
                f"[WARN] Block {block_n}: genre_ext.capital_after 필드 누락"
            )
            continue
        if cap_before is None:
            mismatches.append(
                f"[WARN] Block {block_n1}: genre_ext.capital_before 필드 누락"
            )
            continue

        if str(cap_after) != str(cap_before):
            mismatches.append(
                f"[MISMATCH] Block {block_n}→{block_n1}: "
                f"capital_after={cap_after!r} ≠ capital_before={cap_before!r}"
            )
    return mismatches


def check_wuxguide(blocks: list[dict]) -> list[str]:
    """wuxguide 계열: realm, internal_energy, injury_status 연속성."""
    mismatches: list[str] = []
    for i in range(len(blocks) - 1):
        b_curr = blocks[i]
        b_next = blocks[i + 1]
        block_n = b_curr.get("block", i + 1)
        block_n1 = b_next.get("block", i + 2)

        # realm 검사
        realm_after = safe_get(b_curr, "martial_ext", "realm_after")
        realm_before = safe_get(b_next, "martial_ext", "realm_before")
        if realm_after is None:
            mismatches.append(
                f"[WARN] Block {block_n}: martial_ext.realm_after 필드 누락"
            )
        elif realm_before is None:
            mismatches.append(
                f"[WARN] Block {block_n1}: martial_ext.realm_before 필드 누락"
            )
        elif str(realm_after) != str(realm_before):
            mismatches.append(
                f"[MISMATCH] Block {block_n}→{block_n1}: "
                f"realm_after={realm_after!r} ≠ realm_before={realm_before!r}"
            )

        # internal_energy 검사
        energy_after = safe_get(b_curr, "martial_ext", "internal_energy_after")
        energy_before = safe_get(b_next, "martial_ext", "internal_energy_before")
        if energy_after is None:
            mismatches.append(
                f"[WARN] Block {block_n}: martial_ext.internal_energy_after 필드 누락"
            )
        elif energy_before is None:
            mismatches.append(
                f"[WARN] Block {block_n1}: martial_ext.internal_energy_before 필드 누락"
            )
        elif str(energy_after) != str(energy_before):
            mismatches.append(
                f"[MISMATCH] Block {block_n}→{block_n1}: "
                f"internal_energy_after={energy_after!r} ≠ "
                f"internal_energy_before={energy_before!r}"
            )

        # injury_status 이월 검사
        injury_after = safe_get(b_curr, "martial_ext", "injury_status")
        injury_before = safe_get(b_next, "martial_ext", "injury_status_carried")
        if injury_after is not None and injury_before is not None:
            # 리스트/딕셔너리 비교: JSON 직렬화로 정규화
            after_str = json.dumps(injury_after, ensure_ascii=False, sort_keys=True)
            before_str = json.dumps(injury_before, ensure_ascii=False, sort_keys=True)
            if after_str != before_str:
                mismatches.append(
                    f"[MISMATCH] Block {block_n}→{block_n1}: "
                    f"injury_status 이월 불일치"
                )
        elif injury_after is not None and injury_before is None:
            mismatches.append(
                f"[WARN] Block {block_n1}: martial_ext.injury_status_carried 필드 누락 "
                f"(Block {block_n}에 injury_status 존재)"
            )

    return mismatches


def extract_blocks(data: dict[str, Any]) -> list[dict]:
    """TR 데이터에서 블록 배열을 추출한다."""
    # 일반적 구조: data["blocks"] 또는 data["plot_roadmap"]
    if "blocks" in data:
        return data["blocks"]
    if "plot_roadmap" in data:
        return data["plot_roadmap"]
    # MasterBible 하위
    mb = data.get("MasterBible", {})
    if "plot_roadmap" in mb:
        return mb["plot_roadmap"]
    if "blocks" in mb:
        return mb["blocks"]
    print("[ERROR] 블록 배열을 찾을 수 없습니다 (blocks / plot_roadmap)", file=sys.stderr)
    sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="블록 연속성 자동 검증 스크립트"
    )
    parser.add_argument("--work-id", required=True, help="작품 ID")
    parser.add_argument(
        "--family",
        required=True,
        choices=["blockguide", "wuxguide"],
        help="가이드 계열 (blockguide | wuxguide)",
    )
    args = parser.parse_args()

    data = load_treatment(args.work_id)
    blocks = extract_blocks(data)

    if not blocks:
        print("[ERROR] 블록 배열이 비어 있습니다.", file=sys.stderr)
        sys.exit(2)

    print(f"=== 블록 연속성 검증: {args.work_id} ({args.family}) ===")
    print(f"총 블록 수: {len(blocks)}")
    print()

    if args.family == "blockguide":
        issues = check_blockguide(blocks)
    else:
        issues = check_wuxguide(blocks)

    if not issues:
        print("결과: 모든 블록 연속성 검증 통과 (CLEAN)")
        sys.exit(0)
    else:
        print(f"발견된 문제: {len(issues)}건")
        print("-" * 60)
        for issue in issues:
            print(issue)
        print("-" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
