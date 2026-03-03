"""
[V60.12] Stage 2 실제 API 테스트
팽가 망나니, 가문재건 프로젝트로 Arc 생성 테스트
"""

import os
import sys
import json
import time

# UTF-8 인코딩
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv()

# API 클라이언트
from google import genai

# V60.12 모듈
from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator
from modules.domain.agents.constraint_compiler import ConstraintCompiler
from modules.domain.agents.arc_draft_validator import ArcDraftValidator
from modules.domain.agents.negative_example_injector import NegativeExampleInjector


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_mock_context():
    """간단한 Mock Context 생성"""
    class MockContext:
        def __init__(self):
            self.name = "팽가 망나니, 가문재건"
            self.author_directives = ""
    return MockContext()


def run_test():
    print("=" * 70)
    print("[V60.12] Stage 2 Real API Test - 팽가 망나니, 가문재건")
    print("=" * 70)

    # 1. 데이터 로드
    print("\n[1] Loading data...")

    bible = load_json("bible/팽가_bi.json")
    treatment = load_json("treatments/팽가 망나니, 가문재건_tr_enriched.json")

    print(f"   Bible: {bible['MasterBible']['ProjectData']['MetaInfo']['title']}")
    print(f"   Treatment: {len(treatment)} blocks")

    # 2. API 클라이언트 초기화
    print("\n[2] Initializing API client...")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("   [ERROR] GOOGLE_API_KEY not found in .env")
        return False

    client = genai.Client(api_key=api_key)
    print("   [OK] API client initialized")

    # 3. Mock Arc 1 생성 (이전 Arc 시뮬레이션)
    print("\n[3] Creating mock Arc 1 (previous arc simulation)...")

    mock_arc_1 = {
        "arc_no": 1,
        "ep_count": 5,
        "ep_start": 1,
        "ep_end": 5,
        "title": "[가문의 호랑이가 돌아왔다]",
        "tactical_doc": f"""
제 1화: 회귀 - 팽무진이 전생의 기억을 가지고 회귀한다. 망나니로 살았던 과거의 몸에서 깨어난다.

제 2화: 첫 시험 - 사촌 팽조명과의 비무. 도의 무게를 이용한 압도적 승리.

제 3화: 내부 정화 - 가문 내 배신자들의 흔적을 추적. 팽조악의 심복 유삼 발견.

제 4화: 철혈사자패 - 가주 팽철산에게 실력을 인정받아 철혈사자패를 하사받음.

제 5화: 운송 통로권 - 비무 내기로 팽조악의 운송 통로권을 강탈.
        """,
        "state_constraints": {
            "arc_start_state": {
                "location": "팽가 본가",
                "equipment": ["파혼 서신", "이면 장부"],
                "injuries": "만성 숙취",
                "internal_energy": 30
            },
            "arc_end_state": {
                "location": "팽가 본가",
                "equipment": ["백근 대도", "철혈사자패", "운송 통로권"],
                "injuries": "없음",
                "internal_energy": 70
            },
            "items_acquired": ["백근 대도", "운송 통로권"],
            "grants_received": ["철혈사자패"]
        },
        "joint_docs": {
            "final_location": "팽가 본가",
            "physical_inventory": ["백근 대도", "철혈사자패", "운송 통로권", "파혼 서신", "이면 장부"],
            "world_joint": "팽무진이 차기 가주 후보로 복귀. 철혈사자패 획득으로 지하 연무장 출입 가능."
        },
        "status_shadow": {
            "internal_energy_loss": "30%",  # 100% - 70% = 30% 손실 상태로 종료
            "expected_injuries": "없음"
        }
    }

    print(f"   [OK] Mock Arc 1 created")
    print(f"   Items acquired: {mock_arc_1['state_constraints']['items_acquired']}")
    print(f"   Grants received: {mock_arc_1['state_constraints']['grants_received']}")

    # 4. FourPhaseArcGenerator로 Arc 2 생성
    print("\n[4] Generating Arc 2 with FourPhaseArcGenerator...")
    print("   This will use real API calls and cost ~$0.15-0.20")
    print("   Starting 4-phase pipeline...")

    context = create_mock_context()

    # Volume 전략 (간단히)
    vol_strategy = """
Volume 1 전략: 가문 내부 정화
- Arc 1: 회귀와 첫 시험 (완료)
- Arc 2: 내부 배신자 숙청
- Arc 3: 시조의 비급 획득
- Arc 4: 남궁세가 대응
- Arc 5: 가주 인정
    """

    # Block 2 (현재 블록)
    curr_block = treatment[1]  # Block 2

    try:
        generator = FourPhaseArcGenerator(context, client, "gemini-2.5-pro")

        start_time = time.time()

        arc_2, pipeline_result = generator.generate(
            arc_no=2,
            ep_start=6,
            vol_strategy=vol_strategy,
            curr_block=curr_block,
            prev_arcs=[mock_arc_1],
            assets=bible.get("MasterBible", {}).get("AssetLibrary", {}),
            max_internal_retries=1  # 테스트용으로 1회만
        )

        elapsed = time.time() - start_time

        print(f"\n   Elapsed: {elapsed:.1f}s")
        print(f"   Pipeline result: {pipeline_result.get('final_verdict', 'N/A')}")
        print(f"   Retries: {pipeline_result.get('retries', 0)}")

        if arc_2:
            print("\n[5] Arc 2 Generated Successfully!")
            print("-" * 50)
            print(f"   Title: {arc_2.get('title', 'N/A')}")
            print(f"   Episodes: {arc_2.get('ep_start', '?')}-{arc_2.get('ep_end', '?')}")
            print(f"   Items acquired: {arc_2.get('state_constraints', {}).get('items_acquired', [])}")
            print(f"   Grants received: {arc_2.get('state_constraints', {}).get('grants_received', [])}")
            print(f"   Final location: {arc_2.get('joint_docs', {}).get('final_location', 'N/A')}")

            # tactical_doc 일부 출력
            tactical = arc_2.get('tactical_doc', '')
            print(f"\n   Tactical doc ({len(tactical)} chars):")
            print("   " + tactical[:500].replace('\n', '\n   ') + "...")

            # 검증
            print("\n[6] Validating Arc 2...")
            validator = ArcDraftValidator()
            validation = validator.validate(arc_2, [mock_arc_1])

            print(f"   Score: {validation['score']}")
            print(f"   Valid: {validation['valid']}")
            if validation['critical_issues']:
                print(f"   Critical issues: {validation['critical_issues']}")
            if validation['warnings']:
                print(f"   Warnings: {validation['warnings'][:3]}")

            # 통계 출력
            print("\n[7] Generator Stats:")
            generator.print_stats()

            return True
        else:
            print("\n[FAIL] Arc 2 generation failed")
            print(f"   Pipeline phases:")
            for phase_name, phase_data in pipeline_result.get('phases', {}).items():
                print(f"      {phase_name}: {phase_data}")

            # 상세 이슈 출력
            if 'validate' in pipeline_result.get('phases', {}):
                validate_phase = pipeline_result['phases']['validate']
                print(f"\n   [CONSENSUS DETAILS]")
                print(f"   Vote: PASS {validate_phase.get('vote_pass', 0)} / REJECT {validate_phase.get('vote_reject', 0)}")
                print(f"   Critical issues count: {validate_phase.get('critical_issues', 0)}")

                # Critical issues 상세 출력
                critical_detail = validate_phase.get('critical_issues_detail', [])
                if critical_detail:
                    print(f"\n   [CRITICAL ISSUES DETAIL]")
                    for i, issue in enumerate(critical_detail):
                        print(f"   {i+1}. [{issue.get('category', '?')}] {issue.get('issue', '?')}")
                        if issue.get('evidence'):
                            print(f"      Evidence: {issue['evidence'][:200]}...")

                # All issues 출력
                all_issues = validate_phase.get('all_issues', [])
                if all_issues:
                    print(f"\n   [ALL ISSUES (first 10)]")
                    for i, issue in enumerate(all_issues):
                        severity = issue.get('severity', '?')
                        print(f"   {i+1}. [{severity}] [{issue.get('category', '?')}] {issue.get('issue', '?')[:100]}")

            # last_feedback 출력
            if pipeline_result.get('last_feedback'):
                print(f"\n   [LAST FEEDBACK]")
                print(f"   {pipeline_result['last_feedback'][:1000]}")

            return False

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# V60.12 Stage 2 Real API Test")
    print("#" * 70)

    success = run_test()

    print("\n" + "#" * 70)
    print(f"# Result: {'SUCCESS' if success else 'FAILED'}")
    print("#" * 70)
