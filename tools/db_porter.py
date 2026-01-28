
import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 데이터베이스 경로 설정 (사용자 요청 경로)
DEFAULT_DB_PATH = r"C:\Users\wjjo\Desktop\wuxia_Studio_v35 - 복사본\projects\팽가 망나니 가문 재건\project_data.db"
EXPORT_DIR = "db_exports"

class DBPorter:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            print(f"❌ DB 파일을 찾을 수 없습니다: {self.db_path}")
            sys.exit(1)
        
        self.export_path = self.db_path.parent / EXPORT_DIR
        self.export_path.mkdir(exist_ok=True)
        print(f"📂 작업 대상 DB: {self.db_path.name}")
        print(f"📂 입출력 폴더: {self.export_path}")

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def export_data(self):
        """DB -> JSON 내보내기"""
        print("\n📤 [EXPORT] 데이터 반출 시작...")
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 1. Anchors 반출
        try:
            cur.execute("SELECT key, data FROM anchors")
            rows = cur.fetchall()
            anchors_data = {row['key']: json.loads(row['data']) for row in rows}
            
            # 파일 저장
            file_path = self.export_path / "anchors_export.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(anchors_data, f, indent=4, ensure_ascii=False)
            print(f"   ✅ Anchors ({len(rows)}건) -> {file_path.name}")
        except Exception as e:
            print(f"   ❌ Anchors 반출 실패: {e}")

        # 2. Blueprints 반출
        try:
            cur.execute("SELECT ep_num, data FROM blueprints")
            rows = cur.fetchall()
            bp_data = {str(row['ep_num']): json.loads(row['data']) for row in rows}
            
            # 파일 저장
            file_path = self.export_path / "blueprints_export.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(bp_data, f, indent=4, ensure_ascii=False)
            print(f"   ✅ Blueprints ({len(rows)}건) -> {file_path.name}")
        except Exception as e:
            print(f"   ❌ Blueprints 반출 실패: {e}")

        conn.close()
        print("✨ 반출 완료. JSON 파일을 수정 후 Import 하세요.")

    def import_data(self):
        """JSON -> DB 불러오기"""
        print("\n📥 [IMPORT] 데이터 반입 시작 (주의: DB 덮어쓰기)...")
        
        # 확인 질문
        check = input("⚠️ DB의 기존 데이터가 JSON 내용으로 덮어씌워집니다. 진행하시겠습니까? (y/n): ")
        if check.lower() != 'y':
            print("🚫 작업 취소됨.")
            return

        conn = self.get_connection()
        cur = conn.cursor()

        # 1. Anchors 반입
        anchors_file = self.export_path / "anchors_export.json"
        if anchors_file.exists():
            try:
                with open(anchors_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                count = 0
                for key, content in data.items():
                    json_str = json.dumps(content, ensure_ascii=False)
                    cur.execute("""
                        INSERT OR REPLACE INTO anchors (key, data, updated_at) 
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    """, (key, json_str))
                    count += 1
                print(f"   ✅ Anchors ({count}건) 로드 완료.")
            except Exception as e:
                print(f"   ❌ Anchors 반입 실패: {e}")
        else:
            print(f"   ⚠️ 파일 없음: {anchors_file.name}")

        # 2. Blueprints 반입
        bp_file = self.export_path / "blueprints_export.json"
        if bp_file.exists():
            try:
                with open(bp_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                count = 0
                for ep_str, content in data.items():
                    json_str = json.dumps(content, ensure_ascii=False)
                    cur.execute("""
                        INSERT OR REPLACE INTO blueprints (ep_num, data) 
                        VALUES (?, ?)
                    """, (int(ep_str), json_str))
                    count += 1
                print(f"   ✅ Blueprints ({count}건) 로드 완료.")
            except Exception as e:
                print(f"   ❌ Blueprints 반입 실패: {e}")
        else:
            print(f"   ⚠️ 파일 없음: {bp_file.name}")

        conn.commit()
        conn.close()
        print("✨ 반입 완료. DB가 업데이트되었습니다.")

def main():
    exporter = DBPorter(DEFAULT_DB_PATH)
    
    while True:
        print("\n[DB Porter Menu]")
        print("1. 📤 Export (DB -> JSON)")
        print("2. 📥 Import (JSON -> DB)")
        print("3. 종료")
        
        choice = input("선택 > ").strip()
        
        if choice == '1':
            exporter.export_data()
        elif choice == '2':
            exporter.import_data()
        elif choice == '3':
            break
        else:
            print("잘못된 입력입니다.")

if __name__ == "__main__":
    main()
