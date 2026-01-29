"""
서사 관성 극복 시스템 통합 테스트
Phase 1, 2, 3 모듈들이 정상 동작하는지 확인
"""
import sys
import os

# Windows UTF-8 encoding fix
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, OSError):
        pass

from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_phase1_imports():
    """Phase 1: Writer 메서드 존재 확인"""
    print("\n" + "="*60)
    print("Phase 1 테스트: Pattern Breaking + Mandatory Context")
    print("="*60)

    try:
        from modules.domain.agents.writer import Writer

        # Writer 클래스에 새로운 메서드가 있는지 확인
        assert hasattr(Writer, '_build_anti_trope_instructions'), "❌ _build_anti_trope_instructions 메서드 없음"
        assert hasattr(Writer, '_build_mandatory_context'), "❌ _build_mandatory_context 메서드 없음"
        assert hasattr(Writer, '_extract_recent_events'), "❌ _extract_recent_events 메서드 없음"
        assert hasattr(Writer, '_extract_npc_last_states'), "❌ _extract_npc_last_states 메서드 없음"

        print("✅ Writer에 Phase 1 메서드 모두 존재")
        return True
    except Exception as e:
        print(f"❌ Phase 1 테스트 실패: {e}")
        return False


def test_phase2_modules():
    """Phase 2: 핵심 인프라 모듈 로드 테스트"""
    print("\n" + "="*60)
    print("Phase 2 테스트: Relationship + Information Diffusion")
    print("="*60)

    try:
        # 모듈 임포트
        from modules.core.relationship_tracker import RelationshipTracker
        from modules.core.information_diffusion import InformationDiffusion

        # RelationshipTracker 테스트
        tracker = RelationshipTracker()
        assert hasattr(tracker, 'STATES'), "❌ STATES 속성 없음"
        assert hasattr(tracker, 'validate_transition'), "❌ validate_transition 메서드 없음"
        assert hasattr(tracker, 'infer_state_from_manuscript'), "❌ infer_state_from_manuscript 메서드 없음"

        print("✅ RelationshipTracker 정상 로드")

        # 간단한 전환 테스트
        result = tracker.validate_transition("테스트NPC", "무시", "경외")
        assert result['valid'], "❌ 무시→경외 전환이 허용되지 않음"
        print("✅ 관계 전환 검증 동작")

        # 불가능한 전환 테스트
        result = tracker.validate_transition("테스트NPC", "경외", "무시")
        assert not result['valid'], "❌ 경외→무시 전환이 허용됨 (버그)"
        print("✅ 불가능한 전환 차단 동작")

        print("✅ Phase 2 모듈 정상 동작")
        return True

    except Exception as e:
        print(f"❌ Phase 2 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase3_module():
    """Phase 3: Retrospective Validator 테스트"""
    print("\n" + "="*60)
    print("Phase 3 테스트: Retrospective Validator")
    print("="*60)

    try:
        from modules.validation.retrospective_validator import RetrospectiveValidator

        # 클래스 로드 확인
        assert RetrospectiveValidator, "❌ RetrospectiveValidator 클래스 로드 실패"

        # 메서드 존재 확인
        # context 없이 클래스 레벨 확인
        methods = [
            'validate_long_term_consistency',
            '_check_realm_regression',
            '_check_relationship_regression',
            '_check_item_disappearance',
            '_check_resolved_conflict_recurrence'
        ]

        for method in methods:
            assert hasattr(RetrospectiveValidator, method), f"❌ {method} 메서드 없음"

        print("✅ RetrospectiveValidator 모든 메서드 존재")
        print("✅ Phase 3 모듈 정상 로드")
        return True

    except Exception as e:
        print(f"❌ Phase 3 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_blocking_validator_integration():
    """BlockingValidator에 Phase 2 통합 확인"""
    print("\n" + "="*60)
    print("통합 테스트: BlockingValidator + Phase 2")
    print("="*60)

    try:
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        # 새로운 메서드 존재 확인
        assert hasattr(validator, '_check_relationship_consistency'), "❌ _check_relationship_consistency 없음"
        assert hasattr(validator, '_check_information_consistency'), "❌ _check_information_consistency 없음"

        print("✅ BlockingValidator에 Phase 2 메서드 통합됨")

        # 간단한 검증 테스트 (context 없이도 통과해야 함)
        test_manuscript = "테스트 원고입니다."
        test_context = {
            'encyclopedia': {'npcs': []},
            'martial_hud': {},
            'ep_num': 1
        }

        result = validator._check_relationship_consistency(test_manuscript, test_context)
        assert result['passed'], "❌ 빈 검증이 실패함"
        print("✅ 관계 일관성 체크 기본 동작")

        result = validator._check_information_consistency(test_manuscript, test_context)
        assert result['passed'], "❌ 정보 일관성 체크 실패"
        print("✅ 정보 일관성 체크 기본 동작")

        return True

    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_orchestrator_integration():
    """ValidationOrchestrator에 Phase 3 통합 확인"""
    print("\n" + "="*60)
    print("통합 테스트: ValidationOrchestrator + Phase 3")
    print("="*60)

    try:
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        # 설정
        config = {
            'scoring_model': 'gemini-2.5-pro',
            'advisory_model': 'gemini-2.5-flash',
            'scoring_threshold': 70,
            'use_self_consistency': False,  # 테스트에서는 비활성화
            'use_retrospective': False  # Phase 3도 일단 비활성화
        }

        orchestrator = ValidationOrchestrator(config=config, client=None, genre='wuxia')

        # 속성 확인
        assert hasattr(orchestrator, 'use_retrospective'), "❌ use_retrospective 속성 없음"
        assert hasattr(orchestrator, 'retrospective'), "❌ retrospective 속성 없음"
        assert hasattr(orchestrator, '_format_retrospective_feedback'), "❌ _format_retrospective_feedback 메서드 없음"

        print("✅ ValidationOrchestrator에 Phase 3 통합됨")

        return True

    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """전체 테스트 실행"""
    print("\n[START] Narrative Inertia System Integration Test\n")

    results = []

    # Phase 1
    results.append(("Phase 1 (Prompts)", test_phase1_imports()))

    # Phase 2
    results.append(("Phase 2 (Infrastructure)", test_phase2_modules()))

    # Phase 3
    results.append(("Phase 3 (Retrospective)", test_phase3_module()))

    # 통합 테스트
    results.append(("Integration (Blocking)", test_blocking_validator_integration()))
    results.append(("Integration (Orchestrator)", test_validation_orchestrator_integration()))

    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:15} {name}")

    print("="*60)
    print(f"통과: {passed}/{total} ({passed/total*100:.1f}%)")
    print("="*60)

    if passed == total:
        print("\n[SUCCESS] All tests passed! System ready.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} tests failed - debugging needed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
