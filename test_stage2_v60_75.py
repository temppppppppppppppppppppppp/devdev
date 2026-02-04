"""
[V60.75] Stage 2 테스트 코드
FourPhaseArcGenerator 10 Arc 연속 생산 테스트

Usage: python test_stage2_v60_75.py
"""

import os
import sys
import io
import json
import time
from datetime import datetime

# Windows UTF-8 강제 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 환경 설정
# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
# 특정 .env 파일 로드
load_dotenv(r"C:\Users\wjjo\Desktop\글도비\projects\팽가 망나니 가문 재건\.env")

# Google AI 클라이언트
try:
    from google import genai
    client = genai.Client()
    print("[OK] Google GenAI Client initialized")
except Exception as e:
    print(f"[FAIL] Google GenAI Client: {e}")
    sys.exit(1)

# 모듈 import
from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator
from modules.core.constants import Stage2Limits


class MockProjectContext:
    """테스트용 가짜 ProjectContext"""
    def __init__(self, bible_path: str, treatment_path: str):
        self.bible_path = bible_path
        self.treatment_path = treatment_path
        self.bible = self._load_json(bible_path)
        self.treatment = self._load_json(treatment_path)
        self.project_name = "팽가_테스트"

    def _load_json(self, path: str) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_bible(self) -> dict:
        return self.bible

    def get_treatment(self) -> list:
        return self.treatment

    def get_protagonist_name(self) -> str:
        try:
            return self.bible['MasterBible']['ProjectData']['CoreIdentity']['protagonist']
        except:
            return "주인공"


def run_test(num_arcs: int = 10):
    """
    Stage 2 Arc 연속 생산 테스트
    """
    print("=" * 70)
    print(f"[V60.75 Stage 2 Test] {num_arcs} Arc 연속 생산 테스트")
    print("=" * 70)
    print()

    # 파일 경로
    bible_path = r"C:\Users\wjjo\Desktop\글도비\bible\팽가_bi.json"
    treatment_path = r"C:\Users\wjjo\Desktop\글도비\treatments\팽가 망나니, 가문재건_tr_enriched.json"

    # Context 생성
    context = MockProjectContext(bible_path, treatment_path)
    protagonist_name = context.get_protagonist_name()
    print(f"[INFO] 주인공: {protagonist_name}")
    print(f"[INFO] Treatment 블록 수: {len(context.treatment)}")
    print()

    # FourPhaseArcGenerator 생성
    generator = FourPhaseArcGenerator(context, client, model_tier="gemini-2.0-flash")
    print("[OK] FourPhaseArcGenerator initialized")
    print()

    # Bible에서 필요한 정보 추출
    bible = context.get_bible()
    master_bible = bible.get('MasterBible', {})
    assets = master_bible.get('AssetLibrary', {})

    # Volume 전략 (간단한 테스트용)
    vol_strategy = f"""
    [테스트용 Volume 전략]
    - 주인공: {protagonist_name}
    - 목표: 가문 재건, 아버지 인정
    - 초기 상태: 망나니 평판, 삼류 무공
    - 핵심 갈등: 내부 배신자(팽조악), 외부 적대(남궁세가)
    """

    # 결과 저장
    all_arcs = []
    stats = {
        "total_attempts": 0,
        "success": 0,
        "fail": 0,
        "errors": []
    }

    # Arc 생성 루프
    current_ep = 1

    for arc_no in range(1, num_arcs + 1):
        print("=" * 70)
        print(f"[Arc {arc_no}/{num_arcs}] 생성 시작 (ep_start: {current_ep})")
        print("=" * 70)

        stats["total_attempts"] += 1

        # 현재 블록 (treatment에서 추출)
        block_idx = (arc_no - 1) % len(context.treatment)
        curr_block = context.treatment[block_idx]

        # curr_block에 ep_count 추가 (없으면 기본값)
        if 'ep_count' not in curr_block:
            curr_block['ep_count'] = Stage2Limits.DEFAULT_EP_COUNT

        try:
            start_time = time.time()

            # FourPhaseArcGenerator 호출
            arc, pipeline_result = generator.generate(
                arc_no=arc_no,
                ep_start=current_ep,
                vol_strategy=vol_strategy,
                curr_block=curr_block,
                prev_arcs=all_arcs,
                assets=assets,
                max_internal_retries=2,
                protagonist_name=protagonist_name
            )

            elapsed = time.time() - start_time

            if arc and pipeline_result.get('final_verdict') == 'PASS':
                stats["success"] += 1
                all_arcs.append(arc)

                # ep_count 업데이트
                ep_count = arc.get('ep_count', Stage2Limits.DEFAULT_EP_COUNT)
                current_ep += ep_count

                print()
                print(f"[SUCCESS] Arc {arc_no} 생성 완료!")
                print(f"   - 소요 시간: {elapsed:.1f}초")
                print(f"   - ep_count: {ep_count}")
                print(f"   - tactical_doc 길이: {len(arc.get('tactical_doc', ''))}자")
                print(f"   - 내부 재시도: {pipeline_result.get('retries', 0)}회")

                # 획득 아이템 출력
                items = arc.get('state_constraints', {}).get('items_acquired', [])
                if items:
                    print(f"   - 획득 아이템: {items}")
            else:
                stats["fail"] += 1
                print()
                print(f"[FAIL] Arc {arc_no} 생성 실패")
                print(f"   - 소요 시간: {elapsed:.1f}초")
                print(f"   - verdict: {pipeline_result.get('final_verdict', 'UNKNOWN')}")

                # 실패 원인
                if pipeline_result.get('phases', {}).get('validate'):
                    issues = pipeline_result['phases']['validate'].get('issues_count', 0)
                    print(f"   - 검증 이슈: {issues}개")

                stats["errors"].append({
                    "arc_no": arc_no,
                    "reason": pipeline_result.get('final_verdict', 'UNKNOWN')
                })

        except Exception as e:
            import traceback
            stats["fail"] += 1
            elapsed = time.time() - start_time
            error_msg = str(e)[:200]
            print()
            print(f"[ERROR] Arc {arc_no} 예외 발생!")
            print(f"   - 소요 시간: {elapsed:.1f}초")
            print(f"   - 에러: {error_msg}")
            print(f"   - Traceback:")
            traceback.print_exc()
            stats["errors"].append({
                "arc_no": arc_no,
                "reason": f"Exception: {error_msg}"
            })

        print()

        # Rate limiting
        time.sleep(2)

    # 최종 결과
    print("=" * 70)
    print("[최종 결과]")
    print("=" * 70)
    print(f"총 시도: {stats['total_attempts']}")
    print(f"성공: {stats['success']}")
    print(f"실패: {stats['fail']}")
    print(f"성공률: {stats['success']/stats['total_attempts']*100:.1f}%")
    print()

    if stats["errors"]:
        print("[실패 목록]")
        for err in stats["errors"]:
            print(f"   Arc {err['arc_no']}: {err['reason']}")

    # Generator 통계
    print()
    generator.print_stats()

    # 결과 저장
    output_path = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "stats": stats,
            "arcs": all_arcs
        }, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] {output_path}")

    return stats


if __name__ == "__main__":
    run_test(num_arcs=10)
