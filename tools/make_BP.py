import sqlite3
import json
import os
from pathlib import Path

# ==========================================================
# 1. 환경 설정 (프로젝트명만 바꾸면 자동으로 경로를 잡습니다)
# ==========================================================
PROJECT_NAME = "팽가 망나니 가문 재건"
BASE_PATH = Path(rf"C:\Users\PC\Desktop\wuxia_Studio_v33\projects\{PROJECT_NAME}")
DB_PATH = BASE_PATH / "project_data.db"
OUTPUT_FILE = f"00_Sovereign_Blueprints_{PROJECT_NAME.replace(' ', '_')}.txt"

def make_BP_final_v33():
    if not DB_PATH.exists():
        print(f"❌ DB 파일을 찾을 수 없습니다: {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 에피소드 순서대로 설계도 인출
        cursor.execute("SELECT ep_num, data FROM blueprints ORDER BY ep_num ASC")
        rows = cursor.fetchall()

        if not rows:
            print("⚠️ DB에 저장된 설계도가 없습니다.")
            return

        combined_text = [
            f"{'='*80}\n",
            f"  📜 [SOVEREIGN PRODUCTION] 전 회차 에피소드 설계도 합본\n",
            f"  프로젝트: {PROJECT_NAME}\n",
            f"  추출 시점: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}\n",
            f"{'='*80}\n\n"
        ]

        for row in rows:
            ep_num = row['ep_num']
            try:
                data = json.loads(row['data'])
            except json.JSONDecodeError:
                print(f"🚨 제 {ep_num}화 데이터 파싱 실패 (JSON 오류)")
                continue
            
            title = data.get('title', '제목 없음')
            scenes = data.get('scene_breakdown', {})
            scenario = data.get('integrated_scenario', "시나리오 데이터가 없습니다.")
            cider = data.get('cider_element', data.get('cider_score', '보통'))

            # [출력 레이아웃 설계]
            bp_text = f"▶ 제 {ep_num:03d} 화 : {title}\n"
            bp_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            bp_text += f"🎯 핵심 전리품/사이다: {cider}\n"
            bp_text += f"--------------------------------------------------------------------------------\n\n"
            
            # 1. SCENE BREAKDOWN (가독성 보정)
            bp_text += "### [1. SCENE BREAKDOWN]\n"
            if isinstance(scenes, dict):
                # 씬 번호 순서대로 정렬하여 출력
                sorted_scenes = sorted(scenes.items(), key=lambda x: int(x[0].split('_')[-1]) if '_' in x[0] else 0)
                for s_num, s_desc in sorted_scenes:
                    clean_s_num = s_num.replace('scene_', '씬 ').upper()
                    bp_text += f"  {clean_s_num}: {s_desc}\n"
            else:
                bp_text += f"  {scenes}\n"
            
            # 2. INTEGRATED SCENARIO (구분선 추가)
            bp_text += "\n### [2. INTEGRATED SCENARIO]\n"
            bp_text += f"{scenario.strip()}\n\n"
            bp_text += f"{'='*80}\n\n"
            
            combined_text.append(bp_text)

        # 파일 저장
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("".join(combined_text))
            
        print(f"✅ 추출 완료: 총 {len(rows)}개 회차 설계도")
        print(f"📂 파일 생성됨: {os.path.abspath(OUTPUT_FILE)}")

    except Exception as e:
        print(f"❌ 작업 중 오류 발생: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    make_BP_final_v33()