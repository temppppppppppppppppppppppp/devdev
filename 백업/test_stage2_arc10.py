"""
[Stage 2 Arc 1-10 자동화 테스트]
- main_a.py의 Stage 2 로직 직접 호출
- Arc 10까지 반복 테스트
- 에러 발생 시 상세 로그 출력
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime

# UTF-8 설정 (Windows)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
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

# 테스트 설정
MAX_TEST_TIME = 2 * 60 * 60  # 2시간
TARGET_ARC = 10
PROJECT_NAME = "팽가 망나니 가문 재건"

# 로그 파일
LOG_FILE = os.path.join(os.path.dirname(__file__), "test_stage2_arc10_log.txt")


def log(msg: str):
    """로그 출력 및 파일 저장"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


def run_stage2_test():
    """Stage 2 Arc 1-10 테스트 실행"""
    start_time = time.time()

    # 로그 파일 초기화
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"=== Stage 2 Arc 1-10 Test Started: {datetime.now()} ===\n\n")

    log("=" * 70)
    log(" [Stage 2 Arc 1-10 자동화 테스트]")
    log(f" - 목표: Arc {TARGET_ARC}까지 생성")
    log(f" - 최대 시간: {MAX_TEST_TIME // 3600}시간")
    log("=" * 70)

    from main_a import SovereignApp
    from modules.core.genre_guards.wuxia_guard import WuxiaGuard

    app = SovereignApp()

    try:
        # 1. 프로젝트 부팅
        log(f"\n[1] 프로젝트 부팅: {PROJECT_NAME}")
        app.sys.boot_v20_project(PROJECT_NAME)
        app.current_project = app.sys.project
        log(f"   [OK] 프로젝트 로드 완료")

        # 2. 장르 설정
        log("\n[2] 장르 설정: 무협")
        app.current_project.guard = WuxiaGuard()
        app.sys.genre_guard = app.current_project.guard
        app.selected_genre = {"type": "wuxia", "name": "무협"}
        log(f"   [OK] WuxiaGuard 설정 완료")

        # 3. Bible 로드
        log("\n[3] Bible 로드")
        bible_path = os.path.join(os.path.dirname(__file__), "bible", "팽가_bi.json")
        with open(bible_path, 'r', encoding='utf-8') as f:
            bible_data = json.load(f)
        app.current_project.db.save_anchor('bible', bible_data)
        app.current_project.master_bible = bible_data

        protagonist_name = bible_data.get("MasterBible", {}).get("MartialHUD", {}).get("Protagonist", {}).get("actual_truth", {}).get("name", "팽무진")
        log(f"   [OK] Bible 로드 완료 - 주인공: {protagonist_name}")

        # 4. Treatment 로드 및 Volumes 변환
        log("\n[4] Treatment → Volumes 변환")
        treatment_path = os.path.join(os.path.dirname(__file__), "treatments", "팽가 망나니, 가문재건_tr_enriched.json")
        with open(treatment_path, 'r', encoding='utf-8') as f:
            treatment_data = json.load(f)

        log(f"   - Treatment Blocks: {len(treatment_data)}개")

        # Arc 10까지 = 2개 볼륨 (볼륨당 5개 Arc)
        volumes = []
        for vol_no in range(1, 3):  # 1, 2권
            start_idx = (vol_no - 1) * 5
            end_idx = min(vol_no * 5, len(treatment_data))
            volumes.append({
                "vol_no": vol_no,
                "strategy_doc": f"제{vol_no}권 전략",
                "vol_title": f"제{vol_no}권",
                "arc_blocks": treatment_data[start_idx:end_idx]
            })

        app.current_project.db.save_anchor('volumes', volumes)
        app.current_project.volumes = volumes
        log(f"   [OK] Volumes 저장: {len(volumes)}권")

        # plot_roadmap 설정 (Arc 소스)
        bible_root = bible_data.get('MasterBible', bible_data)
        if 'plot_roadmap' not in bible_root:
            bible_root['plot_roadmap'] = treatment_data[:TARGET_ARC]
            app.current_project.db.save_anchor('bible', bible_data)
            app.current_project.master_bible = bible_data
        log(f"   [OK] plot_roadmap 설정: {len(bible_root.get('plot_roadmap', []))}개 블록")

        # 5. 기존 Arc 초기화
        log("\n[5] 기존 Arc 초기화")
        app.current_project.db.save_anchor('arcs', [])
        app.current_project.arcs = []
        log(f"   [OK] Arc 데이터 초기화")

        # 6. 에이전트 초기화
        log("\n[6] 에이전트 초기화")
        result = app._attach_agents()
        if result:
            log(f"   [OK] 에이전트 초기화 완료")

            # 주요 컴포넌트 확인
            components = [
                ('arc_corrector', 'ArcCorrector'),
                ('arc_draft_validator', 'ArcDraftValidator'),
                ('constraint_compiler', 'ConstraintCompiler'),
                ('four_phase_arc_generator', 'FourPhaseArcGenerator'),
            ]
            for attr, name in components:
                if hasattr(app, attr) and getattr(app, attr):
                    log(f"   [OK] {name} 활성화")
                else:
                    log(f"   [WARN] {name} 비활성화")
        else:
            log(f"   [FAIL] 에이전트 초기화 실패!")
            return False

        # 7. Stage 2 실행
        log("\n" + "=" * 70)
        log(" [Stage 2] Arc Tactical Design 시작")
        log("=" * 70 + "\n")

        # 입력 mock - Arc 10까지 생성
        import builtins
        original_input = builtins.input
        input_queue = [str(TARGET_ARC), "y"]  # Arc 10까지, 확인
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
            stage2_start = time.time()
            result = app._stage_2_arcs()
            stage2_elapsed = time.time() - stage2_start
        finally:
            builtins.input = original_input

        # 8. 결과 확인
        log("\n" + "=" * 70)
        log(" 테스트 결과")
        log("=" * 70)

        arcs = app.current_project.db.load_anchor('arcs') or []
        total_elapsed = time.time() - start_time

        if len(arcs) >= TARGET_ARC:
            log(f" [SUCCESS] Arc {TARGET_ARC}까지 생성 완료!")
            log(f" - 생성된 Arc: {len(arcs)}개")
            log(f" - Stage 2 소요 시간: {stage2_elapsed:.1f}초")
            log(f" - 총 소요 시간: {total_elapsed:.1f}초")

            # Arc 상세 정보
            log("\n [Arc 상세]")
            for arc in arcs[:TARGET_ARC]:
                arc_no = arc.get('arc_no', '?')
                ep_count = arc.get('ep_count', '?')
                ep_range = f"{arc.get('ep_start', '?')}~{arc.get('ep_end', '?')}"
                tactical_len = len(arc.get('tactical_doc', '')) if isinstance(arc.get('tactical_doc'), str) else 0

                joint = arc.get('joint_docs', {})
                state = arc.get('state_constraints', {})

                log(f"\n   [Arc {arc_no}]")
                log(f"      - 회차: {ep_range}화 ({ep_count}화)")
                log(f"      - tactical_doc: {tactical_len}자")
                log(f"      - 종료 위치: {joint.get('final_location', '?')}")

                # 소지품 요약
                inventory = joint.get('physical_inventory', [])
                if isinstance(inventory, list) and inventory:
                    log(f"      - 소지품: {', '.join(str(i) for i in inventory[:3])}...")

                # 획득 아이템
                items = state.get('items_acquired', [])
                if items:
                    log(f"      - 획득 아이템: {items}")

            # 결과 파일 저장
            result_path = os.path.join(os.path.dirname(__file__), "test_stage2_arc10_result.json")
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(arcs[:TARGET_ARC], f, ensure_ascii=False, indent=2)
            log(f"\n [결과 저장] {result_path}")

            return True
        else:
            log(f" [FAIL] Arc {TARGET_ARC} 미달성")
            log(f" - 생성된 Arc: {len(arcs)}개")
            log(f" - 소요 시간: {total_elapsed:.1f}초")

            if arcs:
                log("\n [생성된 Arc 정보]")
                for arc in arcs:
                    arc_no = arc.get('arc_no', '?')
                    log(f"   - Arc {arc_no}: {arc.get('ep_count', '?')}화")

            return False

    except KeyboardInterrupt:
        log("\n\n[중단] 사용자에 의해 테스트 중단됨")
        return False
    except Exception as e:
        log(f"\n[ERROR] 테스트 실패: {e}")
        log(traceback.format_exc())
        return False
    finally:
        total_elapsed = time.time() - start_time
        log(f"\n총 실행 시간: {total_elapsed:.1f}초 ({total_elapsed/60:.1f}분)")


if __name__ == "__main__":
    success = run_stage2_test()
    sys.exit(0 if success else 1)
