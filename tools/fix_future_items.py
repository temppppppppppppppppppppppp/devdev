import argparse
import json
import sqlite3
from pathlib import Path


DEFAULT_PROJECT = Path(
    r"C:\Users\wjjo\Desktop\wuxia_Studio_v35 - 복사본\projects\팽가 망나니 가문 재건"
)
DEFAULT_DB = DEFAULT_PROJECT / "project_data.db"
DEFAULT_EXPORT = DEFAULT_PROJECT / "db_exports" / "anchors_export.json"


def _replace_pre15_items(node, allow_future_item):
    if isinstance(node, dict):
        for k, v in node.items():
            node[k] = _replace_pre15_items(v, allow_future_item)
        return node
    if isinstance(node, list):
        return [_replace_pre15_items(v, allow_future_item) for v in node]
    if isinstance(node, str) and not allow_future_item:
        node = node.replace("혼철대도(混鐵大刀)", "대방도(大方刀)")
        node = node.replace("혼철대도", "대방도")
    return node


def _fix_arcs(arcs):
    if not isinstance(arcs, list):
        return arcs
    for arc in arcs:
        arc_no = arc.get("arc_no")
        allow_future_item = isinstance(arc_no, int) and arc_no >= 15
        _replace_pre15_items(arc, allow_future_item)
    return arcs


def _load_db_arcs(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT data FROM anchors WHERE key='arcs'")
    row = cur.fetchone()
    if not row:
        conn.close()
        raise RuntimeError("anchors에 arcs가 없습니다.")
    arcs = json.loads(row[0])
    conn.close()
    return arcs


def _save_db_arcs(db_path, arcs):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "UPDATE anchors SET data=?, updated_at=CURRENT_TIMESTAMP WHERE key='arcs'",
        (json.dumps(arcs, ensure_ascii=False),),
    )
    conn.commit()
    conn.close()


def _update_export_file(export_path):
    data = json.loads(export_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "arcs" in data:
        data["arcs"] = _fix_arcs(data["arcs"])
        export_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
        return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Arc 기준 미래 무구(혼철대도) 조기 노출을 복구합니다."
    )
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB))
    parser.add_argument("--export", type=str, default=str(DEFAULT_EXPORT))
    parser.add_argument("--no-export", action="store_true", help="export 파일 수정을 건너뜁니다.")
    args = parser.parse_args()

    db_path = Path(args.db)
    export_path = Path(args.export)

    if not db_path.exists():
        raise FileNotFoundError(f"DB 파일이 없습니다: {db_path}")

    arcs = _load_db_arcs(db_path)
    fixed_arcs = _fix_arcs(arcs)
    _save_db_arcs(db_path, fixed_arcs)
    print("✅ DB arcs 복구 완료")

    if not args.no_export and export_path.exists():
        updated = _update_export_file(export_path)
        if updated:
            print("✅ anchors_export.json 업데이트 완료")
        else:
            print("⚠️ anchors_export.json에 'arcs' 키가 없어 건너뜀")
    elif args.no_export:
        print("ℹ️ export 파일 수정 건너뜀")
    else:
        print("⚠️ anchors_export.json이 없어 건너뜀")


if __name__ == "__main__":
    main()
