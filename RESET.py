"""[Phase 4D-3] 프로젝트 리셋 도구 (VecMemory 호환)"""

import json
import os
import shutil
import sqlite3
from pathlib import Path


def get_project_list():
    root = Path("projects")
    if not root.exists():
        return []
    return [d.name for d in root.iterdir() if d.is_dir()]


def selective_reset():
    projects = get_project_list()
    if not projects:
        print("❌ 프로젝트 폴더가 없습니다.")
        return

    print("\n📚 [Reset Target] 리셋할 프로젝트를 선택하십시오:")
    for i, p in enumerate(projects, 1):
        print(f"   {i}. {p}")

    try:
        p_idx = int(input("\n👉 Choice: ")) - 1
        project_name = projects[p_idx]
    except (ValueError, IndexError):
        return

    project_root = Path(f"projects/{project_name}")
    db_path = project_root / "project_data.db"
    vec_db_path = project_root / "memory" / "vec_memory.db"
    drafts_path = project_root / "drafts"

    print(f"\n🎹 [V30.6 Sovereign] '{project_name}' 정밀 리셋 가동")
    print("--------------------------------------------------")
    print(" 1. 정밀 되감기 (Rewind): 특정 화수 이후 모든 기록 삭제")
    print(" 2. 완전 초기화 (Nuclear): 모든 테이블 및 파일 소거")
    print(" 3. 취소")

    choice = input("\n👉 선택: ").strip()

    if choice == "1":
        target_ep = input("⏪ 몇 화부터 삭제하시겠습니까? (예: 1 입력 시 전체 삭제): ").strip()
        if target_ep.isdigit():
            perform_selective_rewind(int(target_ep), db_path, vec_db_path, drafts_path)
    elif choice == "2":
        confirm = input("❗ [경고] 모든 데이터가 삭제됩니다. 계속할까요? (y/n): ").lower()
        if confirm == "y":
            perform_nuclear_reset(db_path, vec_db_path, drafts_path, project_root)


def perform_selective_rewind(target_ep, db_path, vec_db_path, drafts_path):
    """정밀 되감기 — target_ep 이후 모든 기록 삭제"""
    if not db_path.exists():
        print(f"❌ DB 파일을 찾을 수 없습니다: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. 삭제 대상 테이블
        ep_tables = [
            "manuscripts",
            "blueprints",
            "state_logs",
            "martial_tracker",
            "sync_status",
            "causal_graph",
        ]

        # 2. 상태 롤백
        if target_ep > 1:
            cursor.execute("SELECT data FROM state_logs WHERE ep_num = ?", (target_ep - 1,))
            row = cursor.fetchone()
            if row:
                past_actual = json.loads(row["data"]).get("state_updates", {}).get("actual_truth")
                if past_actual:
                    cursor.execute("SELECT data FROM anchors WHERE key = 'bible'")
                    bible_row = cursor.fetchone()
                    if bible_row:
                        bible_data = json.loads(bible_row["data"])
                        if "MasterBible" in bible_data:
                            bible_data["MasterBible"]["MartialHUD"]["Protagonist"]["actual_truth"] = past_actual
                        cursor.execute(
                            "UPDATE anchors SET data = ? WHERE key = 'bible'",
                            (json.dumps(bible_data, ensure_ascii=False),),
                        )
                        print(f"   📉 [Rollback] 주인공 스펙을 {target_ep - 1}화 시점으로 롤백.")

        # 3. SQL 데이터 삭제
        for t in ep_tables:
            cursor.execute(f"DELETE FROM {t} WHERE ep_num >= ?", (target_ep,))
            print(f"   ✂️  '{t}' 테이블: {target_ep}화 이후 기록 삭제 완료.")

        cursor.execute("DELETE FROM encyclopedia")
        cursor.execute("DELETE FROM karma_status WHERE last_updated_ep >= ?", (target_ep,))
        cursor.execute("UPDATE seeds SET status = 'active', recovered_ep = NULL WHERE recovered_ep >= ?", (target_ep,))
        print("   📚 [Lore/Seeds] 인과 관계 초기화 완료.")

        seq_targets = "('manuscripts', 'blueprints', 'state_logs', 'martial_tracker', 'causal_graph', 'sync_status')"
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name IN {seq_targets}")
        print("   🔢 [Sequence] 테이블 ID 카운터를 초기화했습니다.")

        conn.commit()

        # 4. 물리 파일 삭제
        if drafts_path.exists():
            for f in drafts_path.glob("*.txt"):
                try:
                    if int(f.name[:4]) >= target_ep:
                        f.unlink()
                except (ValueError, IndexError, OSError):
                    pass
            print("   📂 원고 파일 삭제 완료.")

        # 5. 벡터 DB 기억 소거 (VecMemory — sqlite-vec)
        if vec_db_path.exists():
            try:
                vec_conn = sqlite3.connect(vec_db_path)
                # episode_meta에서 대상 rowid 조회 후 vec_episodes + 메타 삭제
                rows = vec_conn.execute("SELECT ep_num FROM episode_meta WHERE ep_num >= ?", (target_ep,)).fetchall()
                for (ep,) in rows:
                    vec_conn.execute("DELETE FROM vec_episodes WHERE rowid = ?", (ep,))
                vec_conn.execute("DELETE FROM episode_meta WHERE ep_num >= ?", (target_ep,))
                vec_conn.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))
                vec_conn.commit()
                vec_conn.close()
                print(f"   🌌 벡터 메모리 소거 완료 ({len(rows)}건)")
            except Exception as vdb_err:
                print(f"   ⚠️ 벡터 DB 소거 건너뜀: {vdb_err}")

        print(f"\n✅ [Success] {target_ep}화 시점으로 되감기 성공!")
        print("👉 DB 툴(DBeaver 등)에서 'Refresh(새로고침)'를 눌러 확인하세요.")

    except Exception as e:
        print(f"❌ 리셋 실패: {e}")
    finally:
        if "conn" in locals() and conn:
            conn.close()


def perform_nuclear_reset(db_path, vec_db_path, drafts_path, project_root):
    """전체 삭제"""
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall()]
            for t in tables:
                if t != "sqlite_sequence" and t.isidentifier():
                    cursor.execute(f"DROP TABLE IF EXISTS [{t}]")
            conn.commit()

    # VecMemory DB 삭제
    if vec_db_path.exists():
        os.remove(vec_db_path)
        print("   🗑️ vec_memory.db 삭제 완료")

    # 레거시 ChromaDB 디렉토리 삭제
    chroma_root = project_root / "chroma_db"
    if chroma_root.exists():
        shutil.rmtree(chroma_root)
        print("   🗑️ 레거시 chroma_db 삭제 완료")

    if drafts_path.exists():
        for f in drafts_path.glob("*.txt"):
            f.unlink()

    print("\n🔥 [Nuclear Success] 전체 초기화 완료.")


if __name__ == "__main__":
    selective_reset()
