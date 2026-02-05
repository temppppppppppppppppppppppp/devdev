"""
[V60.12] Stage 3 & 4 실제 API 테스트
Stage 2에서 생성된 Arc 2를 기반으로 Blueprint + Manuscript 생성 테스트
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

# 에이전트
from modules.domain.agents.architect import Architect
from modules.domain.agents.writer import Writer


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_mock_context():
    """Mock Context 생성"""
    class MockPaths:
        def __init__(self):
            self.project_root = "projects/팽가 망나니, 가문재건"

    class MockContext:
        def __init__(self):
            self.name = "팽가 망나니, 가문재건"
            self.author_directives = ""
            self.db = None
            self.paths = MockPaths()

        def get_blueprint(self, ep_num):
            return None

        def load_anchor(self, name, default=None):
            return default

    return MockContext()


def create_mock_arc_2():
    """Stage 2에서 생성된 Arc 2 시뮬레이션 (실제 테스트 결과 기반)"""
    return {
        "arc_no": 2,
        "ep_count": 5,
        "ep_start": 6,
        "ep_end": 10,
        "title": "[내부 숙청의 서막: 암약하는 배신자]",
        "tactical_doc": """
제6화: 지하 연무장의 깨달음 (650자)
팽가 본가, 고요한 새벽. 팽무진은 가주에게 하사받은 철혈사자패를 손에 쥐고 지하 연무장으로 향했다. 그의 내공은 7할로 충만했고, 몸에는 어떠한 부상도 없었다. 철혈사자패가 발하는 미약한 기운에 반응하듯, 연무장 깊숙한 곳의 낡은 석문이 서서히 열리며 잊힌 공간을 드러냈다. 먼지 쌓인 연무장은 팽가의 시조가 수련했던 곳이라 전해지는 전설적인 장소였다. 그곳에서 팽무진은 벽면에 새겨진 희미한 무공의 흔적을 발견했다. 그것은 팽가 정통 도법과는 다른, 기이하면서도 심오한 검법의 일부였다. 무진은 전생의 경험과 역근경을 바탕으로 그 흔적을 해독하려 애썼다. 며칠 밤낮으로 수련에 몰두하며, 그는 벽화 속 동작들을 따라 했고, 그 과정에서 잊혔던 시조의 비급, '천뢰검결'의 단편적인 초식을 어렴풋이 익히게 되었다.

제7화: 흑룡각의 그림자
팽무진은 지하 연무장에서의 수련을 마치고 팽가 본가로 돌아왔다. 그는 팽조악의 심복 유삼이 운영하는 흑룡각이라는 주점에 대한 정보를 입수했다. 겉으로는 평범한 주점이지만, 실상은 불법 도박장이자 팽조악과 외부 세력 간의 비밀 연락 거점이었다. 팽무진은 과거 방탕했던 시절의 모습으로 위장하고 흑룡각에 잠입했다. 퀘퀘한 담배 연기와 술 냄새, 도박꾼들의 고성이 뒤섞인 흑룡각에서 그는 유삼과 지배인 마영이 은밀한 대화를 나누는 것을 목격했다. 그들의 뒤를 밟던 팽무진은 흑룡각 지하에 비밀 금고가 있다는 것을 알게 되었다.

제8화: 드러나는 검은 거래
팽무진은 운송 통로권을 이용하여 흑룡각 지하로 몰래 침투했다. 금고 안에는 팽가의 자금과 함께, 팽조악과 남궁세가 간의 거래 장부가 숨겨져 있었다. 팽무진은 장부를 통해 팽조악이 남궁세가와 은밀한 거래를 하고 있다는 사실을 알게 되었다. 분노한 팽무진은 유삼과 마영을 제압하려 했으나, 유삼은 흑룡각에 숨겨둔 자객들을 불러 팽무진을 공격했다. 팽무진은 백근 대도를 휘두르며 자객들을 상대했다. 7할의 내공과 전생의 경험, 그리고 역근경으로 단련된 육체로 위기를 돌파했다.

제9화: 철혈의 심판
팽무진은 흑룡각 내부의 지형지물을 이용하여 자객들을 하나씩 제압해 나갔다. 좁은 공간에서의 기습, 어둠 속에서의 은신, 그리고 백근 대도의 무게를 이용한 공격으로 자객들을 무력화시켰다. 팽무진은 유삼과 마영을 생포하고, 그들의 죄를 낱낱이 밝혔다. 그는 철혈사자패의 권한으로 유삼과 마영에게 팽가의 법도를 집행했다. 흑룡각은 팽무진의 철혈 심판으로 아수라장이 되었다. 팽무진의 활약은 팽가 사병들에게 큰 감명을 주었다.

제10화: 새로운 충성과 다가오는 폭풍
팽무진이 회수한 자금으로 팽가 사병들의 식단과 장비가 개선되자, 하급 무사들은 그에게 감사를 표했다. 팽무진은 팽가 내에서의 입지를 더욱 강화하며, 팽조악과의 전면전을 준비했다. 그는 남궁세가와의 관계를 주시하며, 팽가 내부의 배신자들을 숙청하기 위한 계획을 세웠다. 그러나 팽조악도 가만히 있지 않았다. 그는 매화객이라는 정체불명의 인물과 접촉하며 팽무진을 제거할 음모를 꾸미고 있었다. 팽무진은 매화객에 대한 정보를 입수하고, 다가오는 폭풍을 대비하며 팽가 본가에서 힘을 기르기로 결심했다.
        """,
        "state_constraints": {
            "arc_start_state": {
                "location": "팽가 본가",
                "equipment": ["백근 대도", "철혈사자패", "운송 통로권", "파혼 서신", "이면 장부"],
                "injuries": "없음",
                "internal_energy": 70
            },
            "arc_end_state": {
                "location": "팽가 본가",
                "equipment": ["백근 대도", "철혈사자패", "운송 통로권", "파혼 서신", "이면 장부", "남궁세가 관련 증거"],
                "injuries": "경미한 찰과상",
                "internal_energy": 65
            },
            "items_acquired": ["천뢰검결 단서", "매화객의 정보", "남궁세가 관련 증거"],
            "items_consumed": [],
            "grants_received": []
        },
        "joint_docs": {
            "final_location": "팽가 본가",
            "physical_inventory": ["백근 대도", "철혈사자패", "운송 통로권", "파혼 서신", "이면 장부", "남궁세가 관련 증거", "매화객의 정보"],
            "world_joint": "팽무진이 팽조악의 비리를 폭로할 증거 확보. 매화객이라는 새로운 위협 등장."
        },
        "status_shadow": {
            "internal_energy_loss": "5%",
            "expected_injuries": "경미한 찰과상",
            "item_consumption": []
        }
    }


def create_mock_hud():
    """Mock Martial HUD"""
    return {
        "character_name": "팽무진",
        "martial_power": 65,
        "internal_energy": 70,
        "technique_level": "이류",
        "equipment": ["백근 대도", "철혈사자패"],
        "injuries": "없음",
        "location": "팽가 본가"
    }


def create_mock_encyclopedia(bible):
    """Bible에서 Encyclopedia 추출"""
    assets = bible.get("MasterBible", {}).get("AssetLibrary", {})
    return {
        "key_npcs": assets.get("KeyNPCs", []),
        "locations": assets.get("Locations", []),
        "items": assets.get("Items", []),
        "techniques": assets.get("Techniques", [])
    }


def extract_episode_material(arc, ep_num):
    """Arc에서 특정 화의 재료 추출"""
    tactical_doc = arc.get("tactical_doc", "")

    # 해당 화 내용 추출
    import re
    pattern = rf"제{ep_num}화[:\s].*?(?=제\d+화|$)"
    match = re.search(pattern, tactical_doc, re.DOTALL)

    if match:
        return match.group(0).strip()

    # 못 찾으면 전체 문서 반환
    return tactical_doc


def run_stage3_test(client, bible, arc_2, ep_num=6):
    """Stage 3: Blueprint 생성 테스트"""
    print("\n" + "=" * 70)
    print(f"[Stage 3] Blueprint 생성 테스트 - 제{ep_num}화")
    print("=" * 70)

    context = create_mock_context()
    architect = Architect(context, client, "gemini-2.5-pro")

    # 필요한 데이터 준비
    martial_hud = create_mock_hud()
    encyclopedia = create_mock_encyclopedia(bible)

    # Arc에서 해당 화 재료 추출
    ep_material = extract_episode_material(arc_2, ep_num)

    # Arc 정보를 focus_info 형태로 구성
    arc_pos = ep_num - arc_2['ep_start'] + 1  # 예: 1 (정수)

    focus_info = {
        "MUST_FOCUS": ep_material,
        "FULL_MAP": arc_2.get("tactical_doc", ""),
        "STOP_LINE": f"제{ep_num}화 종료 시점",
        "arc_drive": {
            "short_term_objective": "팽조악의 비리 증거 수집",
            "current_lack": "권력 기반",
            "pacing_strategy": {"core_ratio": "30%", "tension_limit": 80}
        },
        "hybrid_composition": arc_2.get("hybrid_composition", {
            "primary": "회귀물",
            "secondary": ["복수물", "성장물"],
            "mixing_logic": "회귀 지식 + 복수 동기 + 점진적 성장"
        }),
        "joint_docs": arc_2.get("joint_docs", {}),
        "status_shadow": arc_2.get("status_shadow", {})
    }

    try:
        start_time = time.time()

        blueprint = architect.design_v20_breakdown(
            ep_num=ep_num,
            arc_pos=arc_pos,
            arc_tactical_doc=focus_info,
            martial_hud=martial_hud,
            encyclopedia=encyclopedia,
            narrative_context=f"Arc 2: {arc_2.get('title', '')}",
            tactical_references="무협 장르 기본 규칙 적용",
            style_guide="몰입감 있는 무협 소설 스타일",
            prev_ms_ending="",  # 첫 화이므로 없음
            surgery_intel="",
            enrichment_level=0
        )

        elapsed = time.time() - start_time

        print(f"\n   Elapsed: {elapsed:.1f}s")

        if blueprint:
            print(f"\n   [SUCCESS] Blueprint 생성 완료!")

            # Blueprint가 dict인 경우 문자열로 변환
            if isinstance(blueprint, dict):
                blueprint_str = json.dumps(blueprint, ensure_ascii=False, indent=2)
                print(f"   Blueprint 타입: dict")
            else:
                blueprint_str = str(blueprint)
                print(f"   Blueprint 타입: string")

            print(f"   Blueprint 길이: {len(blueprint_str)}자")
            print(f"\n   Blueprint 미리보기 (처음 1000자):")
            print("   " + "-" * 50)
            preview = blueprint_str[:1000].replace('\n', '\n   ')
            print(f"   {preview}...")
            return blueprint_str
        else:
            print(f"\n   [FAIL] Blueprint 생성 실패")
            return None

    except Exception as e:
        print(f"\n   [ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_stage4_test(client, bible, arc_2, blueprint, ep_num=6):
    """Stage 4: Manuscript 생성 테스트"""
    print("\n" + "=" * 70)
    print(f"[Stage 4] Manuscript 생성 테스트 - 제{ep_num}화")
    print("=" * 70)

    context = create_mock_context()
    writer = Writer(context, client, "gemini-2.5-pro")

    # 필요한 데이터 준비
    hud_report = json.dumps(create_mock_hud(), ensure_ascii=False)

    # Arc 정보 구성
    arc_doc = {
        "MUST_FOCUS_ON": extract_episode_material(arc_2, ep_num),
        "FULL_ARC_MAP": arc_2.get("tactical_doc", ""),
        "PATTERN_PROFILE": arc_2.get("hybrid_composition", {}),
        "PATTERN_MIXING_LOGIC": arc_2.get("hybrid_composition", {}).get("mixing_logic", "")
    }

    try:
        start_time = time.time()

        manuscript = writer.write_v20_manuscript(
            ep_num=ep_num,
            breakdown_doc=blueprint,
            master_bible=bible,
            hud_report=hud_report,
            purism_prompt="무협 장르 원칙 준수",
            style_mode="몰입형",
            intro_dna="CYNICAL" if ep_num == 1 else "",
            feedback="",
            prev_full_manuscript="",  # 첫 화이므로 없음
            arc_doc=arc_doc,
            tactical_references="전투 씬은 구체적으로, 심리 묘사는 깊이 있게"
        )

        elapsed = time.time() - start_time

        print(f"\n   Elapsed: {elapsed:.1f}s")

        if manuscript:
            print(f"\n   [SUCCESS] Manuscript 생성 완료!")

            # Manuscript가 dict인 경우 content 추출
            if isinstance(manuscript, dict):
                content = manuscript.get("content", "")
                print(f"   Manuscript 타입: dict (content 추출)")
                print(f"   전체 JSON 길이: {len(json.dumps(manuscript, ensure_ascii=False))}자")
                print(f"   Content 길이: {len(content)}자")
                manuscript_text = content
            else:
                manuscript_text = str(manuscript)
                print(f"   Manuscript 타입: string")
                print(f"   Manuscript 길이: {len(manuscript_text)}자")

            # 기본 품질 체크
            if len(manuscript_text) >= 4000:
                print(f"   품질 체크: PASS (4000자 이상)")
            else:
                print(f"   품질 체크: WARNING (4000자 미만 - {len(manuscript_text)}자)")

            print(f"\n   Manuscript 미리보기 (처음 1500자):")
            print("   " + "-" * 50)
            preview = manuscript[:1500].replace('\n', '\n   ')
            print(f"   {preview}...")

            print(f"\n   Manuscript 마지막 부분 (마지막 500자):")
            print("   " + "-" * 50)
            ending = manuscript[-500:].replace('\n', '\n   ')
            print(f"   ...{ending}")

            return manuscript
        else:
            print(f"\n   [FAIL] Manuscript 생성 실패")
            return None

    except Exception as e:
        print(f"\n   [ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_full_test():
    """전체 Stage 3 & 4 테스트"""
    print("\n" + "#" * 70)
    print("# V60.12 Stage 3 & 4 Real API Test")
    print("#" * 70)

    # 1. 데이터 로드
    print("\n[1] Loading data...")
    bible = load_json("bible/팽가_bi.json")
    print(f"   Bible: {bible['MasterBible']['ProjectData']['MetaInfo']['title']}")

    # 2. API 클라이언트 초기화
    print("\n[2] Initializing API client...")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("   [ERROR] GOOGLE_API_KEY not found in .env")
        return False

    client = genai.Client(api_key=api_key)
    print("   [OK] API client initialized")

    # 3. Mock Arc 2 생성 (Stage 2 결과 시뮬레이션)
    print("\n[3] Creating mock Arc 2 (Stage 2 simulation)...")
    arc_2 = create_mock_arc_2()
    print(f"   Arc 2: {arc_2['title']}")
    print(f"   Episodes: {arc_2['ep_start']}-{arc_2['ep_end']}")

    # 4. Stage 3: Blueprint 생성
    ep_num = 6  # Arc 2의 첫 번째 화
    blueprint = run_stage3_test(client, bible, arc_2, ep_num)

    if not blueprint:
        print("\n[FAIL] Stage 3 실패로 Stage 4 스킵")
        return False

    # 5. Stage 4: Manuscript 생성
    manuscript = run_stage4_test(client, bible, arc_2, blueprint, ep_num)

    if not manuscript:
        print("\n[FAIL] Stage 4 실패")
        return False

    # 6. 결과 요약
    print("\n" + "=" * 70)
    print("[SUMMARY] Stage 3 & 4 Test Results")
    print("=" * 70)
    print(f"   Stage 3 (Blueprint): {len(blueprint)}자 - SUCCESS")
    print(f"   Stage 4 (Manuscript): {len(manuscript)}자 - {'SUCCESS' if len(manuscript) >= 4000 else 'WARNING'}")

    return True


if __name__ == "__main__":
    success = run_full_test()

    print("\n" + "#" * 70)
    print(f"# Final Result: {'SUCCESS' if success else 'FAILED'}")
    print("#" * 70)
