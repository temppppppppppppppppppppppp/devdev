"""
[V60.80] Stage 3 Isolated Test - Arc 3 Blueprint Generation

테스트 목적:
- ThreePhaseBlueprintGenerator 파이프라인 검증
- Arc 3 (제11~15화) Blueprint 생성 테스트
- 디렉터주권주의, Python 영향 최소화 확인

실행 방법:
  cd 글도비
  python tests/stage3_isolated_test/test_stage3_arc3.py
"""

import io

# 이후 import
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경 변수 로드
from dotenv import load_dotenv

# 원본 프로젝트 경로
SOURCE_PROJECT = PROJECT_ROOT / "projects" / "팽가 망나니 가문 재건"
TEST_DIR = Path(__file__).parent


def setup_test_environment():
    """테스트 환경 설정"""
    print("=" * 60)
    print("[Setup] 테스트 환경 구성 중...")
    print("=" * 60)

    # .env 로드 (원본 프로젝트의 .env 사용)
    env_path = SOURCE_PROJECT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"  ✓ .env 로드: {env_path}")
    else:
        print(f"  ✗ .env 없음: {env_path}")
        return False

    # API 키 확인
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("  ✗ GOOGLE_API_KEY 없음")
        return False
    print(f"  ✓ API 키 확인됨 (길이: {len(api_key)})")

    return True


def load_arc_data(arc_num: int = 3) -> dict[str, Any]:
    """Arc 데이터 로드"""
    print(f"\n[Load] Arc {arc_num} 데이터 로드 중...")

    # DB에서 arcs 로드
    db_path = SOURCE_PROJECT / "project_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM anchors WHERE key = 'arcs'")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("  ✗ arcs 데이터 없음")
        return None

    arcs = json.loads(row[0])
    print(f"  ✓ 총 {len(arcs)}개 Arc 로드됨")

    # Arc 3 찾기 (인덱스 2)
    arc_idx = arc_num - 1
    if arc_idx >= len(arcs):
        print(f"  ✗ Arc {arc_num} 없음")
        return None

    arc_data = arcs[arc_idx]

    # Arc 파일에서 tactical_doc 보강
    arc_file = SOURCE_PROJECT / "plans" / "arcs" / f"arc_{arc_num:03d}.txt"
    if arc_file.exists():
        with open(arc_file, encoding="utf-8") as f:
            tactical_content = f.read()
        arc_data["tactical_doc"] = tactical_content
        print(f"  ✓ tactical_doc 로드: {len(tactical_content)}자")

    print(f"  ✓ Arc {arc_num}: 제{arc_data.get('ep_start', '?')}화 ~ 제{arc_data.get('ep_end', '?')}화")

    return arc_data


def load_bible() -> dict[str, Any]:
    """Bible 데이터 로드"""
    print("\n[Load] Bible 데이터 로드 중...")

    db_path = SOURCE_PROJECT / "project_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM anchors WHERE key = 'bible'")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("  ✗ bible 데이터 없음")
        return {}

    bible = json.loads(row[0])
    print(f"  ✓ Bible 로드됨 (키: {list(bible.keys())[:5]}...)")

    return bible


class MinimalProjectContext:
    """테스트용 최소 ProjectContext"""

    def __init__(self, bible: dict, arcs: list):
        self.bible = bible
        self.arcs = arcs
        self._blueprints = {}

    def get_blueprint(self, ep_num: int) -> dict | None:
        return self._blueprints.get(ep_num)

    def save_episode_blueprint(self, ep_num: int, blueprint: dict):
        self._blueprints[ep_num] = blueprint
        print(f"      💾 Blueprint 저장됨: 제{ep_num}화")

    def get_causal_history_summary(self) -> str:
        return "테스트용 히스토리 요약"


def run_stage3_test(arc_data: dict, bible: dict, target_episodes: list = None):
    """Stage 3 테스트 실행"""
    print("\n" + "=" * 60)
    print("[Test] Stage 3 Blueprint Generation 테스트")
    print("=" * 60)

    # 필요한 모듈 임포트
    from google import genai

    from modules.domain.agents.director import Director
    from modules.domain.agents.three_phase_blueprint_generator import ThreePhaseBlueprintGenerator

    # API 클라이언트 생성
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    print("  ✓ Gemini API 클라이언트 생성됨")

    # 최소 컨텍스트 생성
    context = MinimalProjectContext(bible, [arc_data])

    # 에이전트 생성
    three_phase_bp = ThreePhaseBlueprintGenerator(context, client, model_tier="gemini-2.5-flash")
    director = Director(context, client, model_tier="gemini-2.5-flash")
    print("  ✓ ThreePhaseBlueprintGenerator 생성됨")
    print("  ✓ Director 생성됨")

    # 테스트할 에피소드 범위
    ep_start = arc_data.get("ep_start", 11)
    ep_end = arc_data.get("ep_end", 15)

    if target_episodes:
        episodes = target_episodes
    else:
        episodes = list(range(ep_start, ep_end + 1))

    print(f"\n  📋 테스트 대상: 제{episodes[0]}화 ~ 제{episodes[-1]}화 ({len(episodes)}개)")

    # 결과 저장
    results = {
        "test_time": datetime.now().isoformat(),
        "arc_no": arc_data.get("arc_no", 3),
        "episodes": {},
        "summary": {"total": len(episodes), "success": 0, "failed": 0},
    }

    prev_blueprint = None
    prev_blueprints = []

    for ep_num in episodes:
        print(f"\n{'─' * 50}")
        print(f"  🎯 제{ep_num}화 Blueprint 생성 시작")
        print(f"{'─' * 50}")

        try:
            blueprint, pipeline_result = three_phase_bp.generate(
                ep_num=ep_num,
                arc_data=arc_data,
                prev_blueprint=prev_blueprint,
                prev_blueprints=prev_blueprints[-5:] if prev_blueprints else None,
                max_retries=2,  # 총 3번 시도
                director=director,
                arc_idx=arc_data.get("arc_no", 3) - 1,
            )

            if blueprint and pipeline_result.get("final_verdict") == "PASS":
                results["summary"]["success"] += 1
                results["episodes"][ep_num] = {
                    "status": "PASS",
                    "title": blueprint.get("title", "?"),
                    "scene_count": len(blueprint.get("scene_breakdown", {})),
                    "scenario_length": len(blueprint.get("integrated_scenario", "")),
                    "retries": pipeline_result.get("retries", 0),
                }

                print(f"\n  ✅ 제{ep_num}화 PASS")
                print(f"     제목: {blueprint.get('title', '?')}")
                print(f"     씬 개수: {len(blueprint.get('scene_breakdown', {}))}")
                print(f"     시나리오: {len(blueprint.get('integrated_scenario', ''))}자")

                # 다음 화를 위해 저장
                prev_blueprint = blueprint
                prev_blueprints.append(blueprint)
                context.save_episode_blueprint(ep_num, blueprint)

            else:
                results["summary"]["failed"] += 1
                results["episodes"][ep_num] = {
                    "status": "FAILED",
                    "verdict": pipeline_result.get("final_verdict", "?"),
                    "retries": pipeline_result.get("retries", 0),
                }
                print(f"\n  ❌ 제{ep_num}화 FAILED - {pipeline_result.get('final_verdict', '?')}")

        except Exception as e:
            results["summary"]["failed"] += 1
            results["episodes"][ep_num] = {"status": "ERROR", "error": str(e)[:200]}
            print(f"\n  ❌ 제{ep_num}화 ERROR: {str(e)[:100]}")
            import traceback

            traceback.print_exc()

    # 통계 출력
    print("\n" + "=" * 60)
    print("[Result] 테스트 결과 요약")
    print("=" * 60)
    print(f"  총 테스트: {results['summary']['total']}개")
    print(f"  성공: {results['summary']['success']}개")
    print(f"  실패: {results['summary']['failed']}개")
    print(f"  성공률: {results['summary']['success'] / results['summary']['total'] * 100:.1f}%")

    # Generator 통계
    if hasattr(three_phase_bp, "get_stats"):
        stats = three_phase_bp.get_stats()
        print("\n  [Generator 통계]")
        print(f"    Phase 1 완료: {stats.get('phase1_complete', 0)}")
        print(f"    Phase 2 완료: {stats.get('phase2_complete', 0)}")
        print(f"    Phase 3 PASS: {stats.get('phase3_pass', 0)}")
        print(f"    Phase 3 REJECT: {stats.get('phase3_reject', 0)}")

    # 결과 파일 저장
    result_file = TEST_DIR / f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 결과 저장: {result_file}")

    return results


def main():
    """메인 실행"""
    print("\n" + "=" * 60)
    print("  [V60.80] Stage 3 Isolated Test")
    print("  Arc 3 Blueprint Generation Test")
    print("=" * 60)

    # 1. 환경 설정
    if not setup_test_environment():
        print("\n❌ 환경 설정 실패")
        return

    # 2. 데이터 로드
    arc_data = load_arc_data(arc_num=3)
    if not arc_data:
        print("\n❌ Arc 데이터 로드 실패")
        return

    bible = load_bible()

    # 3. 테스트 실행 (첫 번째 에피소드만 테스트)
    # 전체 테스트: target_episodes=None
    # 단일 테스트: target_episodes=[11]
    print("\n⚠️  단일 에피소드 테스트 (제11화만)")
    print("   전체 테스트 원하면 target_episodes=None 으로 변경\n")

    results = run_stage3_test(
        arc_data=arc_data,
        bible=bible,
        target_episodes=[11],  # 첫 에피소드만 테스트 (비용 절감)
        # target_episodes=None  # 전체 테스트 (11~15화)
    )

    print("\n" + "=" * 60)
    print("  테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    # Windows UTF-8 출력 설정 (pytest 수집 시 capture 파괴 방지)
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    main()
