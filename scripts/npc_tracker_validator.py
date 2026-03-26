"""
NPC 추적표 ↔ draft JSON 교차 검증 스크립트
- 추적표에 기록된 'Block N after' 값이 실제 draft의 relationship_delta.after와 일치하는지 확인
- 추적표에 누락된 NPC가 있는지 탐지
- 결과를 validation report로 출력
"""

import json
import sys
import os
import re
from pathlib import Path
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE = Path(r"C:\Users\wjjo\Desktop\글도비")
TREATMENTS = BASE / "treatments"
DOCS = BASE / "전처리_ssot" / "docs" / "20260324"

# 작품별 설정: (draft_file, tracker_file, cutoff_block)
WORKS = {
    "failed_future_ceo_intern": {
        "draft": TREATMENTS / "failed_future_ceo_intern_tr_block_070_draft.json",
        "tracker": DOCS / "failed_future_ceo_intern_npc_tracker.md",
        "cutoff": 56,
    },
    "wuxia_nakyang_merchant_daughter": {
        "draft": TREATMENTS / "wuxia_nakyang_merchant_daughter_tr_block_070_draft.json",
        "tracker": DOCS / "wuxia_nakyang_merchant_daughter_npc_tracker.md",
        "cutoff": 40,
    },
    "wuxia_third_rate_sect_master": {
        "draft": TREATMENTS / "wuxia_third_rate_sect_master_tr_block_070_draft.json",
        "tracker": DOCS / "wuxia_third_rate_sect_master_npc_tracker.md",
        "cutoff": 44,
    },
    "empire_youngest_allsector": {
        "draft": TREATMENTS / "empire_youngest_allsector_tr_block_070_draft.json",
        "tracker": DOCS / "empire_youngest_allsector_npc_tracker_final.md",
        "cutoff": 70,
    },
    "wuxia_heavenly_physician": {
        "draft": TREATMENTS / "wuxia_heavenly_physician_tr_block_070_draft.json",
        "tracker": DOCS / "wuxia_heavenly_physician_npc_tracker_final.md",
        "cutoff": 70,
    },
}


def extract_block_number(block_id: str) -> int:
    """'Block 56' -> 56"""
    m = re.search(r"\d+", block_id)
    return int(m.group()) if m else 0


def get_npc_final_states(draft_path: Path, cutoff: int) -> dict:
    """
    draft JSON에서 cutoff 블록까지의 각 NPC 최종 상태를 추출.
    returns: {npc_name: {"after": str, "last_block": str, "block_num": int}}
    """
    with open(draft_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both [blocks] and {"blocks": [blocks]} formats
    if isinstance(data, dict):
        blocks = data.get("blocks", [])
    else:
        blocks = data

    npc_states = {}
    for b in blocks:
        bid = b.get("block_id", "")
        bnum = extract_block_number(bid)
        if bnum > cutoff:
            break
        for rd in b.get("relationship_delta", []):
            target = rd["target"]
            npc_states[target] = {
                "after": rd.get("after", ""),
                "last_block": bid,
                "block_num": bnum,
            }
    return npc_states


def extract_tracker_npcs(tracker_path: Path) -> dict:
    """
    추적표 MD에서 NPC 이름과 after 값을 추출.
    returns: {npc_name: {"after_snippet": str}}
    """
    if not tracker_path.exists():
        return {}

    with open(tracker_path, "r", encoding="utf-8") as f:
        content = f.read()

    npcs = {}
    # Multiple patterns for different tracker formats
    patterns = [
        # 미완성작: ### NPC이름 — 역할\n- **Block N after**: 상태값
        re.compile(
            r"###\s+(.+?)\s*(?:—|─|-)\s*.+?\n"
            r".*?\*\*Block \d+ after\*\*:\s*(.+?)(?:\n|$)",
            re.DOTALL,
        ),
        # 완성작: ### NPC이름 — 역할\n- **최종 상태**: 상태값
        re.compile(
            r"###\s+(.+?)\s*(?:—|─|-)\s*.+?\n"
            r".*?\*\*최종 상태\*\*:\s*(.+?)(?:\n|$)",
            re.DOTALL,
        ),
        # 완성작 대안: ### NPC이름 — 역할\n- **최종 블록**: Block N\n- **최종 상태**: 상태값
        re.compile(
            r"###\s+(.+?)\s*(?:—|─|-)\s*.+?\n"
            r".*?\*\*최종 블록\*\*:.+?\n.*?\*\*최종 상태\*\*:\s*(.+?)(?:\n|$)",
            re.DOTALL,
        ),
        # 테이블 기반 추출: | NPC이름 | Block N after 값 |
        # (before 값 테이블에서 이름과 상태 추출)
        re.compile(
            r"\|\s*(.+?)\s*\|\s*(.{20,}?)\s*\|",
        ),
    ]

    for pattern in patterns:
        for m in pattern.finditer(content):
            name = m.group(1).strip()
            after_val = m.group(2).strip()
            # Skip table headers and non-NPC rows
            if name in ("NPC", "항목", "---", "이름", "정규 이름") or name.startswith("-"):
                continue
            if after_val.startswith("-") or after_val.startswith("수"):
                continue
            # Remove markdown bold markers
            name = re.sub(r"\*\*", "", name)
            if name and after_val and name not in npcs:
                npcs[name] = {"after_snippet": after_val}

    return npcs


def similarity(a: str, b: str) -> float:
    """두 문자열의 유사도 (0~1)"""
    return SequenceMatcher(None, a[:100], b[:100]).ratio()


def validate_work(work_id: str, config: dict) -> dict:
    """한 작품의 추적표 검증"""
    result = {
        "work_id": work_id,
        "cutoff": config["cutoff"],
        "draft_exists": config["draft"].exists(),
        "tracker_exists": config["tracker"].exists(),
        "matches": [],
        "mismatches": [],
        "missing_in_tracker": [],
        "extra_in_tracker": [],
        "errors": [],
    }

    if not config["draft"].exists():
        result["errors"].append(f"Draft 파일 없음: {config['draft']}")
        return result
    if not config["tracker"].exists():
        result["errors"].append(f"추적표 파일 없음: {config['tracker']}")
        return result

    try:
        draft_npcs = get_npc_final_states(config["draft"], config["cutoff"])
        tracker_npcs = extract_tracker_npcs(config["tracker"])
    except Exception as e:
        result["errors"].append(f"파싱 오류: {e}")
        return result

    # Draft NPC를 기준으로 추적표 매칭
    matched_tracker_names = set()
    for draft_name, draft_state in draft_npcs.items():
        # 추적표에서 이름 매칭 (정확 매치 우선, 부분 매치 허용)
        tracker_match = None
        for t_name in tracker_npcs:
            if draft_name == t_name or draft_name in t_name or t_name in draft_name:
                tracker_match = t_name
                break

        if tracker_match:
            matched_tracker_names.add(tracker_match)
            sim = similarity(draft_state["after"], tracker_npcs[tracker_match]["after_snippet"])
            entry = {
                "npc": draft_name,
                "last_block": draft_state["last_block"],
                "draft_after": draft_state["after"][:80],
                "tracker_after": tracker_npcs[tracker_match]["after_snippet"][:80],
                "similarity": round(sim, 2),
            }
            if sim >= 0.5:
                result["matches"].append(entry)
            else:
                result["mismatches"].append(entry)
        else:
            result["missing_in_tracker"].append({
                "npc": draft_name,
                "last_block": draft_state["last_block"],
                "draft_after": draft_state["after"][:80],
            })

    # 추적표에만 있고 draft에 없는 NPC
    for t_name in tracker_npcs:
        if t_name not in matched_tracker_names:
            # Draft 이름과 부분 매치 시도
            found = any(
                t_name == d or t_name in d or d in t_name
                for d in draft_npcs
            )
            if not found:
                result["extra_in_tracker"].append({"npc": t_name})

    return result


def format_report(results: list[dict]) -> str:
    """검증 결과를 마크다운 리포트로 포맷"""
    lines = [
        "# NPC 추적표 교차 검증 리포트",
        "",
        f"> 검증 일시: 2026-03-25",
        f"> 검증 대상: {len(results)}개 작품",
        "",
        "---",
        "",
    ]

    total_match = 0
    total_mismatch = 0
    total_missing = 0

    for r in results:
        lines.append(f"## {r['work_id']} (cutoff: Block {r['cutoff']})")
        lines.append("")

        if r["errors"]:
            for e in r["errors"]:
                lines.append(f"- **ERROR**: {e}")
            lines.append("")
            continue

        n_match = len(r["matches"])
        n_mismatch = len(r["mismatches"])
        n_missing = len(r["missing_in_tracker"])
        n_extra = len(r["extra_in_tracker"])
        total_match += n_match
        total_mismatch += n_mismatch
        total_missing += n_missing

        total = n_match + n_mismatch + n_missing
        rate = (n_match / total * 100) if total > 0 else 0

        lines.append(f"| 항목 | 수 |")
        lines.append(f"|------|-----|")
        lines.append(f"| 일치 (유사도 ≥ 0.5) | {n_match} |")
        lines.append(f"| 불일치 (유사도 < 0.5) | {n_mismatch} |")
        lines.append(f"| 추적표 누락 (draft에만 존재) | {n_missing} |")
        lines.append(f"| 추적표 추가 (draft에 없음) | {n_extra} |")
        lines.append(f"| **정합률** | **{rate:.1f}%** |")
        lines.append("")

        if r["mismatches"]:
            lines.append("### 불일치 NPC")
            lines.append("")
            lines.append("| NPC | 마지막 블록 | 유사도 | Draft after | Tracker after |")
            lines.append("|-----|------------|--------|-------------|---------------|")
            for m in r["mismatches"]:
                lines.append(
                    f"| {m['npc']} | {m['last_block']} | {m['similarity']} | {m['draft_after'][:40]}… | {m['tracker_after'][:40]}… |"
                )
            lines.append("")

        if r["missing_in_tracker"]:
            lines.append("### 추적표 누락 NPC")
            lines.append("")
            lines.append("| NPC | 마지막 블록 | Draft after |")
            lines.append("|-----|------------|-------------|")
            for m in r["missing_in_tracker"]:
                lines.append(f"| {m['npc']} | {m['last_block']} | {m['draft_after'][:50]}… |")
            lines.append("")

        lines.append("---")
        lines.append("")

    # 종합
    grand_total = total_match + total_mismatch + total_missing
    grand_rate = (total_match / grand_total * 100) if grand_total > 0 else 0
    lines.append("## 종합 결과")
    lines.append("")
    lines.append(f"| 항목 | 전체 |")
    lines.append(f"|------|------|")
    lines.append(f"| 총 NPC 검증 수 | {grand_total} |")
    lines.append(f"| 일치 | {total_match} |")
    lines.append(f"| 불일치 | {total_mismatch} |")
    lines.append(f"| 누락 | {total_missing} |")
    lines.append(f"| **전체 정합률** | **{grand_rate:.1f}%** |")

    return "\n".join(lines)


def main():
    results = []
    for work_id, config in WORKS.items():
        print(f"검증 중: {work_id}...", file=sys.stderr)
        r = validate_work(work_id, config)
        results.append(r)

    report = format_report(results)

    # 리포트 출력
    print(report)

    # 리포트 저장
    report_path = DOCS / "npc_tracker_validation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n리포트 저장: {report_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
