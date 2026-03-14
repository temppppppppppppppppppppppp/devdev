"""
[manual-only] Host-bound DB mutation helper.
This script rewrites a specific local SQLite project and is not part of the live app/runtime path.
"""

import json
import sqlite3
from pathlib import Path
import re


DB_PATH = Path(r"C:\Users\wjjo\Desktop\wuxia_Studio_v35 - 복사본\projects\팽가 망나니 가문 재건\project_data.db")


def _normalize_beat_sequence(beat_sequence, ep_start):
    if not isinstance(beat_sequence, list):
        return beat_sequence
    normalized = []
    for i, beat in enumerate(beat_sequence):
        expected_ep = ep_start + i
        if isinstance(beat, str):
            m = re.match(r"^\s*제\s*.*?화[: ]\s*(.*)$", beat)
            rest = m.group(1) if m else beat.strip()
            normalized.append(f"제 {expected_ep}화: {rest}".strip())
        else:
            normalized.append(beat)
    return normalized


def _normalize_length_meta(node, ep_count):
    length_keys = {"arc_length_chapters", "total_chapters_estimate", "arc_duration_episodes"}
    if isinstance(node, dict):
        for k in list(node.keys()):
            if k in length_keys:
                node[k] = str(ep_count)
            else:
                _normalize_length_meta(node[k], ep_count)
    elif isinstance(node, list):
        for item in node:
            _normalize_length_meta(item, ep_count)


def _normalize_strings(node, allow_future_item=False):
    if isinstance(node, dict):
        for k, v in node.items():
            node[k] = _normalize_strings(v, allow_future_item=allow_future_item)
    elif isinstance(node, list):
        return [_normalize_strings(v, allow_future_item=allow_future_item) for v in node]
    elif isinstance(node, str):
        if allow_future_item:
            node = node.replace("대방도(大方刀)", "혼철대도(混鐵大刀)")
            node = node.replace("대방도", "혼철대도")
        node = node.replace("팽명", "팽무진")
    return node


def normalize_arc(arc):
    if not isinstance(arc, dict):
        return arc
    ep_start = arc.get("ep_start")
    ep_count = arc.get("ep_count")

    if isinstance(ep_start, int) and isinstance(ep_count, int):
        arc["beat_sequence"] = _normalize_beat_sequence(arc.get("beat_sequence", []), ep_start)
        _normalize_length_meta(arc, ep_count)
        tactical = arc.get("tactical_doc")
        if isinstance(tactical, str):
            expected_eps = list(range(ep_start, ep_start + ep_count))
            it = iter(expected_eps)

            def _repl(match):
                try:
                    n = next(it)
                except StopIteration:
                    return match.group(0)
                return f"[제 {n}화 전술 설계]"

            arc["tactical_doc"] = re.sub(r"\[제\s*.*?화 전술 설계\]", _repl, tactical)
        arc_no = arc.get("arc_no")
        allow_future_item = isinstance(arc_no, int) and arc_no >= 15
        _normalize_strings(arc, allow_future_item=allow_future_item)
    return arc


def main():
    if not DB_PATH.exists():
        print(f"❌ DB 파일이 없습니다: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT data FROM anchors WHERE key='arcs'")
    row = cur.fetchone()

    if not row:
        print("⚠️ anchors에 arcs가 없습니다.")
        conn.close()
        return

    try:
        arcs = json.loads(row[0])
    except Exception as e:
        print(f"❌ arcs JSON 파싱 실패: {e}")
        conn.close()
        return

    if not isinstance(arcs, list):
        print("⚠️ arcs가 리스트가 아닙니다. 중단합니다.")
        conn.close()
        return

    normalized_arcs = [normalize_arc(a) for a in arcs]
    cur.execute(
        "UPDATE anchors SET data=?, updated_at=CURRENT_TIMESTAMP WHERE key='arcs'",
        (json.dumps(normalized_arcs, ensure_ascii=False),),
    )
    conn.commit()
    conn.close()
    print("✅ arcs 정규화 완료")


if __name__ == "__main__":
    main()
