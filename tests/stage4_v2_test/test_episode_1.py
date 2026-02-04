"""
Stage 4 V2 테스트 - 1화 생성
ChiefWriter 앙상블 → ManuscriptValidator → Director 면담
"""
import sys
import os
import json
import time

# 프로젝트 루트 추가
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

# UTF-8 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from google import genai

# 모듈 임포트
from modules.core.project_manager import ProjectContext
from modules.core.constants import AIModels
from modules.domain.agents.chief_writer import ChiefWriter
from modules.domain.agents.manuscript_validator import ManuscriptValidator
from modules.domain.agents.director import Director


def setup_test_environment():
    """테스트 환경 설정"""
    # .env 로드
    env_path = os.path.join(os.path.dirname(__file__), 'project', '.env')
    load_dotenv(env_path)

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        # 루트 .env도 확인
        load_dotenv(os.path.join(ROOT, '.env'))
        api_key = os.getenv('GOOGLE_API_KEY')

    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found!")

    # Gemini 클라이언트 초기화
    client = genai.Client(api_key=api_key)
    print(f"✅ Gemini 클라이언트 초기화 완료")

    return client


def load_project_context():
    """프로젝트 컨텍스트 로드 (커스텀 경로)"""
    # 테스트용 프로젝트 경로
    test_project_dir = os.path.join(os.path.dirname(__file__), 'project')
    db_path = os.path.join(test_project_dir, 'project_data.db')

    # ProjectContext 수동 초기화 (경로 오버라이드)
    class TestProjectContext:
        def __init__(self, db_path):
            from modules.core.db_manager import DBManager
            self.db = DBManager(db_path)
            self.master_bible = self.db.load_anchor('bible') or {}
            self._latest_state = {}

        @property
        def latest_state(self):
            state = self.db.get_latest_state()
            if not state:
                bible_root = self.master_bible.get('MasterBible', self.master_bible)
                return bible_root.get('MartialHUD', {})
            return state

    context = TestProjectContext(db_path)
    print(f"✅ 프로젝트 컨텍스트 로드 완료")
    print(f"   • DB: {db_path}")
    print(f"   • Bible 키: {list(context.master_bible.keys())[:5]}")

    return context


def load_blueprint(context, ep_num: int) -> dict:
    """Blueprint 로드"""
    bp = context.db.get_blueprint(ep_num)
    if not bp:
        raise ValueError(f"Blueprint for ep {ep_num} not found!")

    print(f"✅ Blueprint {ep_num}화 로드 완료")
    print(f"   • 시나리오 길이: {len(bp.get('integrated_scenario', ''))}자")
    print(f"   • 씬 개수: {len(bp.get('scene_breakdown', {}))}")

    return bp


def load_arc_tactical(context, ep_num: int) -> str:
    """Arc 전술 문서 로드"""
    # Arc 번호 계산 (5화당 1Arc)
    arc_no = (ep_num - 1) // 5 + 1

    arc_data = context.db.load_anchor(f'arc_{arc_no:03d}')
    if arc_data and isinstance(arc_data, dict):
        return arc_data.get('tactical_doc', '')

    # 파일에서 시도
    arc_file = os.path.join(
        os.path.dirname(__file__),
        'project', 'plans', 'arcs',
        f'arc_{arc_no:03d}.txt'
    )
    if os.path.exists(arc_file):
        with open(arc_file, 'r', encoding='utf-8') as f:
            return f.read()

    return ""


def run_stage4_v2_test(ep_num: int = 1):
    """Stage 4 V2 테스트 실행"""
    print("\n" + "="*70)
    print(f"🎬 Stage 4 V2 테스트 - 제{ep_num}화 생성")
    print("="*70 + "\n")

    start_time = time.time()

    # 1. 환경 설정
    client = setup_test_environment()
    context = load_project_context()

    # 2. 데이터 로드
    blueprint = load_blueprint(context, ep_num)
    arc_tactical = load_arc_tactical(context, ep_num)

    # 이전 원고 (1화면 없음)
    prev_manuscript = ""
    prev_ending = ""
    if ep_num > 1:
        prev_ms = context.db.get_manuscript(ep_num - 1)
        if prev_ms:
            prev_manuscript = prev_ms.get('content', '')
            prev_ending = prev_manuscript[-500:] if prev_manuscript else ""

    # HUD 리포트
    hud_state = context.latest_state
    hud_report = json.dumps(hud_state, ensure_ascii=False, indent=2) if hud_state else "HUD 정보 없음"

    # 3. 에이전트 초기화
    print("\n📦 에이전트 초기화...")

    chief_writer = ChiefWriter(
        context=context,
        client=client,
        model_tier=AIModels.STAGE4_FIXED_WRITER_MODEL
    )
    print(f"   • ChiefWriter: {AIModels.STAGE4_FIXED_WRITER_MODEL}")

    manuscript_validator = ManuscriptValidator(context=context)
    print(f"   • ManuscriptValidator: Python 기반")

    director = Director(
        context=context,
        client=client,
        model_tier="gemini-2.5-pro"
    )
    print(f"   • Director: gemini-2.5-pro")

    # 4. 앙상블 생성
    print("\n" + "-"*50)
    print("🎭 Phase 1: ChiefWriter 앙상블 생성 (3개 후보)")
    print("-"*50)

    candidates = chief_writer.generate_ensemble(
        ep_num=ep_num,
        blueprint=blueprint,
        prev_manuscript=prev_manuscript,
        hud_report=hud_report,
        arc_doc=arc_tactical,
        master_bible=context.master_bible,
        style_guide="",
        genre_name="무협"
    )

    print(f"\n✅ 후보 생성 완료: {len(candidates)}개")
    for i, c in enumerate(candidates):
        ms_len = len(c.get('manuscript', ''))
        strategy = c.get('strategy_name', c.get('strategy', f'후보{i+1}'))
        print(f"   • {strategy}: {ms_len}자")

    # 5. Python 사전 검증
    print("\n" + "-"*50)
    print("🔍 Phase 2: ManuscriptValidator 사전 검증")
    print("-"*50)

    validation_results = manuscript_validator.validate_all_candidates(
        candidates=candidates,
        blueprint=blueprint,
        prev_manuscript=prev_manuscript,
        hud_report=hud_report
    )

    for i, vr in enumerate(validation_results):
        strategy = candidates[i].get('strategy_name', f'후보{i+1}')
        print(f"   • {strategy}: 경고 {vr.get('warning_count', 0)}개, 분량 {vr.get('metrics', {}).get('length', 0)}자")

    # 6. Director 면담
    print("\n" + "-"*50)
    print("🎬 Phase 3: Director 면담")
    print("-"*50)

    # Arc 위치 계산
    arc_pos = ((ep_num - 1) % 5) + 1
    total_ep_in_arc = 5

    director_result = director.select_and_judge_ensemble(
        ep_num=ep_num,
        candidates=candidates,
        validation_results=validation_results,
        blueprint=blueprint,
        previous_ending=prev_ending,
        arc_pos=arc_pos,
        total_eps=total_ep_in_arc,
        retry_count=0
    )

    verdict = director_result.get('verdict', 'UNKNOWN')
    score = director_result.get('score', 0)
    selected = director_result.get('selected', 'A')
    reason = director_result.get('selection_reason', '')

    print(f"\n📊 Director 판정: {verdict}")
    print(f"   • 점수: {score}")
    print(f"   • 선택: 후보 {selected}")
    print(f"   • 사유: {reason[:100]}...")

    # 7. 결과 저장
    elapsed = time.time() - start_time

    if verdict == "PASS":
        selected_candidate = director_result.get('selected_candidate', {})
        final_manuscript = selected_candidate.get('manuscript', '')
        final_title = selected_candidate.get('title', f'제{ep_num}화')

        # 결과 파일 저장
        result_dir = os.path.join(os.path.dirname(__file__), 'results')
        os.makedirs(result_dir, exist_ok=True)

        result_file = os.path.join(result_dir, f'ep_{ep_num:04d}.txt')
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"# {final_title}\n\n")
            f.write(final_manuscript)

        print(f"\n✅ 원고 저장: {result_file}")
        print(f"   • 제목: {final_title}")
        print(f"   • 분량: {len(final_manuscript)}자")
    else:
        print(f"\n❌ REJECT - 재시도 필요")
        feedback = director_result.get('feedback', {})
        action_items = director_result.get('action_items', [])
        print(f"   • 피드백: {feedback}")
        print(f"   • 액션: {action_items}")

    print("\n" + "="*70)
    print(f"⏱️ 총 소요 시간: {elapsed:.1f}초")
    print("="*70)

    return director_result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ep', type=int, default=1, help='Episode number')
    args = parser.parse_args()

    run_stage4_v2_test(args.ep)
