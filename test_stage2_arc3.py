"""
[V60.36 테스트] Stage 2 Arc 1-3 간이 테스트
- main_a.py의 _run_stage2_tactical_design 직접 호출
"""

import os
import sys
import json

# UTF-8 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_test():
    print("=" * 70)
    print("[V60.36 테스트] Stage 2 Arc 1-3 간이 테스트")
    print("=" * 70)

    # main_a.py 직접 실행
    from main_a import SovereignApp
    from modules.core.genre_guards.wuxia_guard import WuxiaGuard

    app = SovereignApp()
    project_name = "팽가 망나니 가문 재건"

    try:
        # 1. 프로젝트 부팅
        print(f"\n[1] 프로젝트 부팅: {project_name}")
        app.sys.boot_v20_project(project_name)
        app.current_project = app.sys.project

        # 2. 장르 설정
        print("[2] 장르 설정: 무협")
        app.current_project.guard = WuxiaGuard()
        app.sys.genre_guard = app.current_project.guard
        app.selected_genre = {"type": "wuxia", "name": "무협"}

        # 3. Bible 로드
        print("[3] Bible 로드")
        bible_path = os.path.join(os.path.dirname(__file__), "bible", "팽가_bi.json")
        with open(bible_path, 'r', encoding='utf-8') as f:
            bible_data = json.load(f)
        app.current_project.db.save_anchor('bible', bible_data)

        # 4. Treatment 로드 및 Volumes 변환
        print("[4] Treatment → Volumes 변환")
        treatment_path = os.path.join(os.path.dirname(__file__), "treatments", "팽가 망나니, 가문재건_tr_enriched.json")
        with open(treatment_path, 'r', encoding='utf-8') as f:
            treatment_data = json.load(f)

        # 블록을 볼륨으로 변환 (Arc 3까지 = 1개 볼륨의 첫 3블록)
        volumes = [{
            "vol_no": 1,
            "strategy_doc": "제1권: 가문의 호랑이가 돌아왔다 - 암약하는 부패를 피로 씻어내고 남궁의 오만함을 꺾다",
            "vol_title": "제1권 - 회귀",
            "arc_blocks": treatment_data[:3]  # Arc 3까지만
        }]
        app.current_project.db.save_anchor('volumes', volumes)
        print(f"   Volumes 저장: 1권 (3개 Arc)")

        # 5. 기존 Arc 초기화
        print("[5] 기존 Arc 초기화")
        app.current_project.db.save_anchor('arcs', [])

        # 6. 에이전트 초기화
        print("[6] 에이전트 초기화")
        app._attach_agents()

        # 7. Stage 2 실행
        print("\n" + "=" * 70)
        print("[Stage 2] Arc Tactical Design 시작")
        print("=" * 70 + "\n")

        # 입력 mock - Arc 3까지만 생성
        import builtins
        original_input = builtins.input
        input_queue = ["3"]  # Arc 3까지
        def mock_input(prompt=""):
            print(prompt, end="")
            if input_queue:
                val = input_queue.pop(0)
                print(val)
                return val
            return "3"
        builtins.input = mock_input

        try:
            # Stage 2 호출
            result = app._stage_2_arcs()
        finally:
            builtins.input = original_input

        print("\n" + "=" * 70)
        if result:
            print("[테스트 성공] Stage 2 완료")
            # 결과 확인
            arcs = app.current_project.db.load_anchor('arcs') or []
            print(f"생성된 Arc: {len(arcs)}개")
            for arc in arcs[:3]:
                print(f"  Arc {arc.get('arc_no')}: {len(arc.get('tactical_doc', ''))}자, {arc.get('ep_count', '?')}화")
        else:
            print("[테스트 실패] Stage 2 미완료")
        print("=" * 70)

    except Exception as e:
        print(f"\n테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
