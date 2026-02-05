"""
[V60.42 테스트] Stage 2 Arc 1-3 테스트
- main_a.py의 Stage 2 로직 직접 호출
- ArcCorrector 통합 테스트 포함
"""

import os
import sys
import json
import time

# UTF-8 설정 (Windows)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        # Python 3.7+ reconfigure 사용
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# .env 로드 (API 키)
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), "projects", "팽가 망나니 가문 재건", ".env")
load_dotenv(env_path)


def run_stage2_test():
    """Stage 2 Arc 1-3 테스트 실행"""
    print("=" * 70)
    print(" [V60.42 테스트] Stage 2 Arc 1-3 생성 테스트")
    print("=" * 70)
    print(f" - ArcCorrector 통합 테스트 포함")
    print(f" - 목표: Arc 3까지 생성 및 검증")
    print("=" * 70)

    from main_a import SovereignApp
    from modules.core.genre_guards.wuxia_guard import WuxiaGuard

    app = SovereignApp()
    project_name = "팽가 망나니 가문 재건"

    try:
        # 1. 프로젝트 부팅
        print(f"\n[1] 프로젝트 부팅: {project_name}")
        app.sys.boot_v20_project(project_name)
        app.current_project = app.sys.project
        print(f"   [OK] 프로젝트 로드 완료")

        # 2. 장르 설정
        print("\n[2] 장르 설정: 무협")
        app.current_project.guard = WuxiaGuard()
        app.sys.genre_guard = app.current_project.guard
        app.selected_genre = {"type": "wuxia", "name": "무협"}
        print(f"   [OK] WuxiaGuard 설정 완료")

        # 3. Bible 로드
        print("\n[3] Bible 로드")
        bible_path = os.path.join(os.path.dirname(__file__), "bible", "팽가_bi.json")
        with open(bible_path, 'r', encoding='utf-8') as f:
            bible_data = json.load(f)
        app.current_project.db.save_anchor('bible', bible_data)

        protagonist_name = bible_data.get("MasterBible", {}).get("MartialHUD", {}).get("Protagonist", {}).get("actual_truth", {}).get("name", "팽무진")
        print(f"   [OK] Bible 로드 완료")
        print(f"   - 주인공: {protagonist_name}")

        # 4. Treatment 로드 및 Volumes 변환
        print("\n[4] Treatment → Volumes 변환")
        treatment_path = os.path.join(os.path.dirname(__file__), "treatments", "팽가 망나니, 가문재건_tr_enriched.json")
        with open(treatment_path, 'r', encoding='utf-8') as f:
            treatment_data = json.load(f)

        print(f"   - Treatment Blocks: {len(treatment_data)}개")

        # 블록을 볼륨으로 변환 (Arc 3까지 = 1개 볼륨의 첫 3블록)
        volumes = [{
            "vol_no": 1,
            "strategy_doc": "제1권: 가문의 호랑이가 돌아왔다",
            "vol_title": "제1권 - 회귀",
            "arc_blocks": treatment_data[:3]  # Arc 3까지만
        }]
        app.current_project.db.save_anchor('volumes', volumes)
        print(f"   [OK] Volumes 저장: 1권 (3개 Arc Block)")

        for i, block in enumerate(treatment_data[:3], 1):
            print(f"      Block {i}: {block.get('title', '?')[:40]}...")

        # 5. 기존 Arc 초기화
        print("\n[5] 기존 Arc 초기화")
        app.current_project.db.save_anchor('arcs', [])
        app.current_project.arcs = []
        print(f"   [OK] Arc 데이터 초기화")

        # 6. 에이전트 초기화
        print("\n[6] 에이전트 초기화")
        result = app._attach_agents()
        if result:
            print(f"   [OK] 에이전트 초기화 완료")

            # ArcCorrector 확인
            if hasattr(app, 'arc_corrector') and app.arc_corrector:
                print(f"   [OK] ArcCorrector 활성화 (V60.42)")
            else:
                print(f"   [WARN] ArcCorrector 비활성화")

            # DraftValidator 확인
            if hasattr(app, 'arc_draft_validator') and app.arc_draft_validator:
                print(f"   [OK] ArcDraftValidator 활성화 (V60.11)")
            else:
                print(f"   [WARN] ArcDraftValidator 비활성화")
        else:
            print(f"   [FAIL] 에이전트 초기화 실패!")
            return

        # 7. Stage 2 실행
        print("\n" + "=" * 70)
        print(" [Stage 2] Arc Tactical Design 시작")
        print("=" * 70 + "\n")

        # 입력 mock - Arc 3까지만 생성
        import builtins
        original_input = builtins.input
        input_queue = ["3", "y"]  # Arc 3까지, 확인
        input_idx = [0]

        def mock_input(prompt=""):
            print(prompt, end="")
            if input_idx[0] < len(input_queue):
                val = input_queue[input_idx[0]]
                input_idx[0] += 1
                print(val)
                return val
            return ""

        builtins.input = mock_input

        try:
            # Stage 2 호출
            start_time = time.time()
            result = app._stage_2_arcs()
            elapsed = time.time() - start_time
        finally:
            builtins.input = original_input

        # 8. 결과 확인
        print("\n" + "=" * 70)
        print(" 테스트 결과")
        print("=" * 70)

        arcs = app.current_project.db.load_anchor('arcs') or []

        if result and len(arcs) >= 3:
            print(f" [SUCCESS] Stage 2 완료!")
            print(f" - 생성된 Arc: {len(arcs)}개")
            print(f" - 소요 시간: {elapsed:.1f}초")

            print("\n [Arc 상세]")
            for arc in arcs[:3]:
                arc_no = arc.get('arc_no', '?')
                ep_count = arc.get('ep_count', '?')
                ep_range = f"{arc.get('ep_start', '?')}~{arc.get('ep_end', '?')}"
                tactical_len = len(arc.get('tactical_doc', '')) if isinstance(arc.get('tactical_doc'), str) else 0

                joint = arc.get('joint_docs', {})
                state = arc.get('state_constraints', {})

                print(f"\n   [Arc {arc_no}]")
                print(f"      - 회차: {ep_range}화 ({ep_count}화)")
                print(f"      - tactical_doc: {tactical_len}자")
                print(f"      - 종료 위치: {joint.get('final_location', '?')}")
                print(f"      - 소지품: {joint.get('physical_inventory', [])}")
                print(f"      - 획득 아이템: {state.get('items_acquired', [])}")
                print(f"      - 수여물: {state.get('grants_received', [])}")

                # 상태 체크포인트 확인
                end_state = state.get('arc_end_state', {})
                if end_state:
                    print(f"      - 종료 상태: 내공 {end_state.get('internal_energy', '?')}%, 부상: {end_state.get('injuries', '?')}")

            # 결과 파일 저장
            result_path = os.path.join(os.path.dirname(__file__), "test_stage2_result.json")
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(arcs[:3], f, ensure_ascii=False, indent=2)
            print(f"\n [결과 저장] {result_path}")

        else:
            print(f" [FAIL] Stage 2 미완료")
            print(f" - 생성된 Arc: {len(arcs)}개")
            if arcs:
                for arc in arcs:
                    print(f"   - Arc {arc.get('arc_no', '?')}: {arc.get('ep_count', '?')}화")

        print("\n" + "=" * 70)
        print(" 테스트 완료")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n[중단] 사용자에 의해 테스트 중단됨")
    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_stage2_test()
