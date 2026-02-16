"""
[V60.80] Stage 3 Isolated Test v2 - 컨텍스트 보강 버전
"""

import io
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

SOURCE_PROJECT = PROJECT_ROOT / "projects" / "팽가 망나니 가문 재건"
TEST_DIR = Path(__file__).parent


class EnhancedProjectContext:
    """보강된 테스트용 ProjectContext"""

    def __init__(self, bible: dict, arcs: list[dict], arc_file_content: str = ""):
        self.bible = bible
        self.arcs = arcs
        self._blueprints = {}
        self._manuscripts = {}
        self.arc_file_content = arc_file_content

        # Bible에서 핵심 정보 추출
        self.master_bible = bible.get("MasterBible", {})
        self.martial_hud = self.master_bible.get("MartialHUD", {})
        self.protagonist = self.martial_hud.get("Protagonist", {}).get("actual_truth", {})
        self.world_state = self.master_bible.get("WorldState", {})

    def get_blueprint(self, ep_num: int) -> dict | None:
        return self._blueprints.get(ep_num)

    def save_episode_blueprint(self, ep_num: int, blueprint: dict):
        self._blueprints[ep_num] = blueprint
        print(f"      [DB] Blueprint 저장: 제{ep_num}화")

    def get_causal_history_summary(self) -> str:
        """Arc 2까지의 요약 히스토리 제공"""
        protagonist_name = self.protagonist.get("name", "팽무진")

        # Arc 1-2 요약
        history = f"""[이전 서사 요약 - Arc 1~2]
주인공: {protagonist_name}
- Arc 1 (1-5화): 회귀 후 각성, 팽가 내부에서 첫 번째 시험 통과
- Arc 2 (6-10화): 흑룡각 습격, 이중 장부 획득, 숙부 팽조악의 비리 증거 확보

[Arc 2 종료 시점]
- 위치: 반파된 흑룡각 앞
- 상태: 내공 5%, 우측 어깨 회전근개 파열, 극심한 피로
- 소지품: 백근도, 철혈사자패, 수로 운송권 문서, 형법 집행권, 이중 장부, 은자 팔천 냥 궤짝

[Arc 3 시작 - 제11화]
- {protagonist_name}은 흑룡각 앞에서 은자를 뿌려 충성을 매수해야 함
- 핵심 행동: 돈으로 사람의 마음을 묶는 정치적 행위
- 종료 조건: 가문으로 복귀 명령 후 마차 안에서 의식 잃기 직전까지
"""
        return history

    def get_protagonist_info(self) -> dict:
        """주인공 정보 반환"""
        return {
            "name": self.protagonist.get("name", "팽무진"),
            "alias": self.protagonist.get("alias", "하북광도"),
            "rank": self.protagonist.get("rank", "팽가 장남"),
            "equipment": self.protagonist.get("equipment", "백근도"),
            "current_state": {
                "internal_energy": "5%",
                "injuries": "우측 어깨 회전근개 파열, 손등 열상, 좌측 어깨 타박상",
                "location": "반파된 흑룡각 앞 거리",
            },
        }


def setup_environment():
    """환경 설정"""
    print("=" * 60)
    print("[Setup] 테스트 환경 구성")
    print("=" * 60)

    env_path = SOURCE_PROJECT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("  [OK] .env 로드됨")
    else:
        print("  [FAIL] .env 없음")
        return False

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("  [FAIL] GOOGLE_API_KEY 없음")
        return False
    print("  [OK] API 키 확인됨")
    return True


def load_full_context():
    """전체 컨텍스트 로드"""
    print("\n[Load] 전체 컨텍스트 로드 중...")

    db_path = SOURCE_PROJECT / "project_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Bible 로드
    cursor.execute("SELECT data FROM anchors WHERE key = 'bible'")
    bible = json.loads(cursor.fetchone()[0])
    print("  [OK] Bible 로드됨")

    # Arcs 로드
    cursor.execute("SELECT data FROM anchors WHERE key = 'arcs'")
    arcs = json.loads(cursor.fetchone()[0])
    print(f"  [OK] {len(arcs)}개 Arc 로드됨")

    conn.close()

    # Arc 3 파일 로드
    arc_file = SOURCE_PROJECT / "plans" / "arcs" / "arc_003.txt"
    arc_content = ""
    if arc_file.exists():
        with open(arc_file, encoding="utf-8") as f:
            arc_content = f.read()
        print(f"  [OK] Arc 3 파일 로드됨 ({len(arc_content)}자)")

    return bible, arcs, arc_content


def create_enriched_arc_data(arcs: list[dict], arc_content: str, context: EnhancedProjectContext) -> dict:
    """Arc 3 데이터에 컨텍스트 보강"""
    arc_data = arcs[2].copy()  # Arc 3

    # tactical_doc 보강
    arc_data["tactical_doc"] = arc_content

    # 주인공 정보 추가
    protagonist = context.get_protagonist_info()

    # 이전 Arc 종료 상태 추가 (Arc 2)
    arc2_end = arcs[1].get("state_constraints", {}).get("arc_end_state", {})

    # state_constraints 보강
    if "state_constraints" not in arc_data:
        arc_data["state_constraints"] = {}

    arc_data["state_constraints"]["protagonist"] = protagonist
    arc_data["state_constraints"]["previous_arc_end"] = arc2_end

    # 핵심 캐릭터 이름 강조
    arc_data["protagonist_name"] = protagonist["name"]

    print("  [OK] Arc 3 데이터 보강 완료")
    print(f"      주인공: {protagonist['name']}")
    print(f"      에피소드: 제{arc_data['ep_start']}화 ~ 제{arc_data['ep_end']}화")

    return arc_data


def run_test(context: EnhancedProjectContext, arc_data: dict, target_ep: int = 11):
    """테스트 실행"""
    print("\n" + "=" * 60)
    print(f"[Test] 제{target_ep}화 Blueprint 생성 테스트")
    print("=" * 60)

    from google import genai

    from modules.domain.agents.director import Director
    from modules.domain.agents.three_phase_blueprint_generator import ThreePhaseBlueprintGenerator

    # API 클라이언트
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    # 에이전트 생성 (Flash 사용 - 비용 절감)
    three_phase = ThreePhaseBlueprintGenerator(context, client, model_tier="gemini-2.5-flash")
    director = Director(context, client, model_tier="gemini-2.5-flash")

    print("  [OK] 에이전트 생성됨")
    print(f"  [INFO] 주인공: {arc_data.get('protagonist_name', '?')}")
    print(f"  [INFO] 히스토리 요약 길이: {len(context.get_causal_history_summary())}자")

    # 테스트 실행
    print(f"\n{'─' * 50}")
    print(f"  제{target_ep}화 생성 시작")
    print(f"{'─' * 50}")

    try:
        blueprint, result = three_phase.generate(
            ep_num=target_ep,
            arc_data=arc_data,
            prev_blueprint=None,
            prev_blueprints=None,
            max_retries=2,  # 총 3번
            director=director,
            arc_idx=2,  # Arc 3 (0-indexed)
        )

        if blueprint and result.get("final_verdict") == "PASS":
            print(f"\n  [PASS] 제{target_ep}화 성공!")
            print(f"    제목: {blueprint.get('title', '?')}")
            print(f"    씬 개수: {len(blueprint.get('scene_breakdown', {}))}")
            print(f"    시나리오: {len(blueprint.get('integrated_scenario', ''))}자")

            # 시나리오 일부 출력
            scenario = blueprint.get("integrated_scenario", "")
            print("\n  [시나리오 미리보기]")
            print(f"  {scenario[:500]}...")

            return True, blueprint
        else:
            print(f"\n  [FAIL] 제{target_ep}화 실패")
            print(f"    verdict: {result.get('final_verdict', '?')}")
            print(f"    retries: {result.get('retries', '?')}")
            return False, result

    except Exception as e:
        print(f"\n  [ERROR] {str(e)[:200]}")
        import traceback

        traceback.print_exc()
        return False, {"error": str(e)}


def main():
    print("\n" + "=" * 60)
    print("  [V60.80] Stage 3 Test v2 - 컨텍스트 보강")
    print("=" * 60)

    # 1. 환경 설정
    if not setup_environment():
        return

    # 2. 컨텍스트 로드
    bible, arcs, arc_content = load_full_context()

    # 3. Enhanced Context 생성
    context = EnhancedProjectContext(bible, arcs, arc_content)

    # 4. Arc 데이터 보강
    arc_data = create_enriched_arc_data(arcs, arc_content, context)

    # 5. 테스트 실행
    success, result = run_test(context, arc_data, target_ep=11)

    # 6. 결과 저장
    result_file = TEST_DIR / f"test_v2_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        # Blueprint는 저장, 아니면 에러 정보
        save_data = result if isinstance(result, dict) else {"blueprint": result}
        json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  [OK] 결과 저장: {result_file.name}")

    print("\n" + "=" * 60)
    print(f"  테스트 완료! {'성공' if success else '실패'}")
    print("=" * 60)


if __name__ == "__main__":
    # Windows UTF-8 출력 설정 (pytest 수집 시 capture 파괴 방지)
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    main()
