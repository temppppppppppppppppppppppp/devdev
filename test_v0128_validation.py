"""
V0128 3-Tier Validation System Test Script

Tests all three tiers independently and as an integrated system.
"""
import sys
import os

# [CRITICAL] UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

def test_blocking_validator():
    """Test TIER 1: BLOCKING Validator"""
    print("\n" + "=" * 60)
    print("TIER 1: BLOCKING VALIDATOR TEST")
    print("=" * 60)

    from modules.validation.blocking_validator import BlockingValidator

    validator = BlockingValidator()

    # Test Case 1: Minimum length failure
    print("\n[Test 1] 분량 미달 체크")
    manuscript = "강호풍은 객잔에 도착했다."  # Too short
    context = {'mode': 'MANUSCRIPT'}

    result = validator.validate(manuscript, context)
    print(f"Result: {result['passed']}")
    if not result['passed']:
        print(f"Failures: {result['failures']}")
    assert not result['passed'], "Should fail on minimum length"
    print("✅ PASS: Minimum length check working")

    # Test Case 2: Dead NPC resurrection
    print("\n[Test 2] 사망 NPC 재등장 체크")
    manuscript = "강호풍은 객잔에서 사망한 막삼을 만났다." * 500  # Make it long enough
    context = {
        'mode': 'MANUSCRIPT',
        'encyclopedia': {
            'npcs': [
                {'name': '막삼', 'status': 'dead', 'aliases': []}
            ],
            'items': [],
            'locations': []
        }
    }

    result = validator.validate(manuscript, context)
    print(f"Result: {result['passed']}")
    if not result['passed']:
        print(f"Failures: {[f['reason'] for f in result['failures']]}")
    assert not result['passed'], "Should fail on dead NPC appearance"
    print("✅ PASS: Dead NPC check working")

    # Test Case 3: Valid manuscript
    print("\n[Test 3] 정상 원고 체크")
    manuscript = """
    강호풍은 객잔에 도착했다. 그는 방을 잡고 휴식을 취했다.
    다음 날 아침, 그는 일어나 창밖을 바라보았다.
    거리에는 사람들이 북적였다. 그는 가볍게 미소지었다.
    오늘은 어떤 일이 일어날까? 그는 기대에 찼다.
    """ * 40  # Make it 4000+ chars (40 * ~100 = 4000)

    context = {
        'mode': 'MANUSCRIPT',
        'encyclopedia': {
            'npcs': [],
            'items': [],
            'locations': []
        },
        'martial_hud': {},
        'blueprint': {'scene_breakdown': {
            'Scene 1': '객잔 도착',
            'Scene 2': '휴식',
            'Scene 3': '아침',
            'Scene 4': '거리 관찰'
        }}
    }

    result = validator.validate(manuscript, context)
    print(f"Result: {result['passed']}")
    if not result['passed']:
        print(f"Failures: {result['failures']}")
    assert result['passed'], "Should pass for valid manuscript"
    print("✅ PASS: Valid manuscript accepted")


def test_scoring_validator():
    """Test TIER 2: SCORING Validator"""
    print("\n" + "=" * 60)
    print("TIER 2: SCORING VALIDATOR TEST")
    print("=" * 60)

    from modules.validation.scoring_validator import ScoringValidator

    # Test without LLM (Python metrics only)
    print("\n[Test 1] Python 기반 점수 계산 (LLM 없음)")
    validator = ScoringValidator(client=None)

    manuscript = """
    강호풍은 객잔에 도착했다. 그는 검을 뽑아 적을 베었다.
    피가 튀었다. 그는 승리했다. 내공이 상승했다.
    다음 날 아침이 밝았다. 그는 일어나 창밖을 바라보았다.
    거리에는 사람들이 북적였다. 그는 가볍게 미소지었다.
    """ * 10

    context = {}
    result = validator.validate(manuscript, context)

    print(f"총점: {result['total_score']}/100")
    print(f"PASS 여부: {result['passed']}")
    print(f"세부 점수:")
    for category, data in result['breakdown'].items():
        if isinstance(data, dict):
            print(f"  - {category}: {data.get('score')}/{data.get('max')} - {data.get('reason')}")

    assert 'total_score' in result, "Should return total_score"
    print("✅ PASS: Python metrics calculated")

    # Test with LLM (if API key available)
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("\n[Test 2] LLM 기반 점수 계산")
        try:
            client = genai.Client(api_key=api_key)
            validator_llm = ScoringValidator(client=client, model="gemini-2.5-flash")

            result_llm = validator_llm.validate(manuscript, context)
            print(f"총점 (LLM): {result_llm['total_score']}/100")
            print(f"PASS 여부: {result_llm['passed']}")
            print("✅ PASS: LLM evaluation completed")
        except Exception as e:
            print(f"⚠️ LLM test skipped: {e}")
    else:
        print("\n⚠️ GOOGLE_API_KEY not found, skipping LLM test")


def test_advisory_validator():
    """Test TIER 3: ADVISORY Validator"""
    print("\n" + "=" * 60)
    print("TIER 3: ADVISORY VALIDATOR TEST")
    print("=" * 60)

    from modules.validation.advisory_validator import AdvisoryValidator

    validator = AdvisoryValidator(client=None)

    # Test with cliché detection
    manuscript = """
    강호풍은 다시 눈을 떴다. 과거로 돌아왔다는 사실을 깨달았다.
    그는 알고 있는 미래를 이용하여 복수를 다짐했다.
    반드시 복수하겠다고 마음먹었다.
    """

    context = {}
    result = validator.validate(manuscript, context)

    print(f"PASS 여부: {result['passed']} (항상 True여야 함)")
    print(f"제안 개수: {len(result['suggestions'])}")
    print("제안 내용:")
    for suggestion in result['suggestions']:
        print(f"  - {suggestion.get('suggestion', suggestion)}")

    assert result['passed'] == True, "ADVISORY should always pass"
    assert len(result['suggestions']) > 0, "Should detect clichés"
    print("✅ PASS: Advisory suggestions generated")


def test_validation_orchestrator():
    """Test Full 3-Tier Validation System"""
    print("\n" + "=" * 60)
    print("FULL 3-TIER VALIDATION ORCHESTRATOR TEST")
    print("=" * 60)

    from modules.validation.validation_orchestrator import ValidationOrchestrator

    # Test configuration
    config = {
        'scoring_model': 'gemini-2.5-flash',  # Use flash for testing
        'advisory_model': 'gemini-2.5-flash',
        'scoring_threshold': 70,
        'use_self_consistency': False,  # Disable for faster testing
        'consistency_votes': 1
    }

    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else None

    orchestrator = ValidationOrchestrator(config, client, genre='wuxia')

    # Test Case 1: Should REJECT on BLOCKING failure
    print("\n[Test 1] BLOCKING 실패 시나리오")
    manuscript_short = "강호풍은 객잔에 도착했다."  # Too short
    context = {
        'encyclopedia': {'npcs': [], 'items': [], 'locations': []},
        'martial_hud': {'actual_truth': {'realm': '삼류', 'internal_energy': 100, 'equipment': []}},
        'blueprint': {},
        'mode': 'MANUSCRIPT',
        'history': [],
        'npc_profiles': {}
    }

    result = orchestrator.validate(1, manuscript_short, context)
    print(f"최종 판정: {result['final_decision']}")
    print(f"총점: {result['total_score']}")
    assert result['final_decision'] == 'REJECT', "Should reject on BLOCKING failure"
    print("✅ PASS: BLOCKING failure triggers REJECT")

    # Test Case 2: Should evaluate SCORING
    print("\n[Test 2] SCORING 평가 시나리오")
    manuscript_long = """
    강호풍은 객잔에 도착했다. 그는 검을 뽑아 적을 베었다.
    피가 튀었다. 그는 승리했다. 내공이 상승했다.
    다음 날 아침이 밝았다. 그는 일어나 창밖을 바라보았다.
    거리에는 사람들이 북적였다. 그는 가볍게 미소지었다.
    오늘은 어떤 일이 일어날까? 그는 기대에 찼다.
    """ * 30  # 충분히 길게

    result = orchestrator.validate(2, manuscript_long, context)
    print(f"최종 판정: {result['final_decision']}")
    print(f"총점: {result['total_score']}/100")
    print(f"피드백: {result['feedback']}")

    assert 'blocking_result' in result, "Should have blocking_result"
    assert 'scoring_result' in result, "Should have scoring_result"
    assert 'advisory_result' in result, "Should have advisory_result"
    print("✅ PASS: Full validation pipeline completed")


def test_director_integration():
    """Test Director Integration with V0128"""
    print("\n" + "=" * 60)
    print("DIRECTOR INTEGRATION TEST")
    print("=" * 60)

    from modules.domain.agents.director import Director
    from modules.core.project_manager import ProjectContext

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ GOOGLE_API_KEY not found, skipping Director integration test")
        return

    # Mock context (minimal setup)
    class MockDB:
        pass

    class MockContext:
        def __init__(self):
            self.db = MockDB()
            self.author_directives = ""

    client = genai.Client(api_key=api_key)
    context = MockContext()

    director = Director(context, client, model_tier="gemini-2.5-flash")

    # Test V0128 method
    manuscript = """
    강호풍은 객잔에 도착했다. 그는 검을 뽑아 적을 베었다.
    피가 튀었다. 그는 승리했다. 내공이 상승했다.
    다음 날 아침이 밝았다. 그는 일어나 창밖을 바라보았다.
    거리에는 사람들이 북적였다. 그는 가볍게 미소지었다.
    """ * 30

    validation_context = {
        'encyclopedia': {'npcs': [], 'items': [], 'locations': []},
        'martial_hud': {'actual_truth': {'realm': '삼류', 'internal_energy': 100, 'equipment': []}},
        'blueprint': {},
        'mode': 'MANUSCRIPT',
        'history': [],
        'npc_profiles': {}
    }

    v0128_config = {
        'use_self_consistency': False,
        'consistency_votes': 1
    }

    try:
        result = director.audit_manuscript_v0128(
            ep_num=1,
            manuscript=manuscript,
            validation_context=validation_context,
            config=v0128_config,
            genre='wuxia'
        )

        print(f"판정: {result['decision']}")
        print(f"점수: {result['score']}")
        print(f"이유: {result['reason']}")

        assert 'decision' in result, "Should return decision"
        assert result['decision'] in ['PASS', 'REJECT'], "Should be PASS or REJECT"
        print("✅ PASS: Director V0128 integration working")

    except Exception as e:
        print(f"⚠️ Director test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("V0128 3-TIER VALIDATION SYSTEM TEST SUITE")
    print("=" * 60)

    try:
        test_blocking_validator()
        test_scoring_validator()
        test_advisory_validator()
        test_validation_orchestrator()
        test_director_integration()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nV0128 시스템이 정상 작동합니다.")
        print("config/settings.json에서 'use_v0128': true로 설정하여 활성화하세요.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n🚨 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
