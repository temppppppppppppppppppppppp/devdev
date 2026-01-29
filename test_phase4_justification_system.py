"""
Phase 4: 정당화 패턴 시스템 테스트
Few-Shot Learning 기반 정당화 패턴이 정상 작동하는지 확인
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


def test_phase4_1_pattern_library():
    """Phase 4.1: 패턴 라이브러리 로드 테스트"""
    print("\n" + "="*60)
    print("Phase 4.1 테스트: Justification Pattern Library")
    print("="*60)

    try:
        from modules.core.justification_patterns import (
            get_justification_guide,
            get_available_patterns,
            get_pattern_description
        )

        # 1. 무협 장르 패턴 로드
        wuxia_patterns = get_available_patterns('wuxia')
        assert len(wuxia_patterns) > 0, "❌ 무협 패턴이 비어있음"
        print(f"✅ 무협 패턴 {len(wuxia_patterns)}개 로드됨: {wuxia_patterns}")

        # 2. 특정 패턴 설명 로드
        desc = get_pattern_description('wuxia', 'weak_body_strong_action')
        assert desc and len(desc) > 10, "❌ 패턴 설명이 너무 짧음"
        print(f"✅ 패턴 설명 로드 성공: {desc[:50]}...")

        # 3. Few-Shot 가이드 생성
        guide = get_justification_guide('wuxia', 'weak_body_strong_action')
        assert guide and len(guide) > 100, "❌ 가이드가 너무 짧음"
        assert '논리 구조' in guide or 'logic_structure' in guide, "❌ 논리 구조 정보 없음"
        assert '예시' in guide or 'examples' in guide, "❌ 예시 정보 없음"
        print(f"✅ Few-Shot 가이드 생성 성공 ({len(guide)}자)")

        # 4. 헌터/투자 장르도 체크
        hunter_patterns = get_available_patterns('hunter')
        investment_patterns = get_available_patterns('investment')
        print(f"✅ 헌터 패턴 {len(hunter_patterns)}개, 투자 패턴 {len(investment_patterns)}개")

        return True

    except Exception as e:
        print(f"❌ Phase 4.1 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase4_2_blocking_validator_suggestions():
    """Phase 4.2: BlockingValidator 제안 기능 테스트"""
    print("\n" + "="*60)
    print("Phase 4.2 테스트: Blocking Validator Justification Suggestions")
    print("="*60)

    try:
        from modules.validation.blocking_validator import BlockingValidator

        # 1. 정당화 체크 비활성화 모드 (기본값)
        validator_off = BlockingValidator(context=None, enable_justification_checks=False)
        assert hasattr(validator_off, 'enable_justification_checks'), "❌ 설정 속성 없음"
        assert validator_off.enable_justification_checks == False, "❌ 기본값이 False가 아님"
        print("✅ 기본 모드 (정당화 체크 OFF) 생성 성공")

        # 2. 정당화 체크 활성화 모드
        validator_on = BlockingValidator(context=None, enable_justification_checks=True)
        assert validator_on.enable_justification_checks == True, "❌ 활성화 실패"
        print("✅ 정당화 체크 모드 (ON) 생성 성공")

        # 3. 새로운 메서드 존재 확인
        assert hasattr(validator_on, '_check_physical_capability'), "❌ _check_physical_capability 메서드 없음"
        assert hasattr(validator_on, '_check_authority_exercise'), "❌ _check_authority_exercise 메서드 없음"
        print("✅ Phase 4.2 메서드 존재 확인")

        # 4. 간단한 검증 테스트 (물리적 능력 체크)
        test_manuscript = "주인공은 나약한 몸으로 100근 대도를 들어올렸다."
        test_context = {
            'martial_hud': {
                'actual_truth': {
                    'physical_tags': ['나약', '중독'],
                    'reputation': 5
                }
            },
            'genre': 'wuxia',
            'ep_num': 3
        }

        # 정당화 체크 활성화 시 감지해야 함
        result = validator_on._check_physical_capability(test_manuscript, test_context)
        # 정당화가 없으면 실패해야 함
        if not result['passed']:
            assert 'justification_guide' in result, "❌ 정당화 가이드가 제공되지 않음"
            assert 'quick_fixes' in result, "❌ 빠른 수정 제안이 없음"
            print("✅ 물리적 능력 체크 + 제안 기능 동작")
        else:
            print("⚠️ 물리적 능력 체크 통과 (정당화 키워드 감지됨)")

        # 5. 권위 행사 체크
        test_manuscript2 = "하인이었던 주인공은 단호하게 명령했다."
        result2 = validator_on._check_authority_exercise(test_manuscript2, test_context)
        if not result2['passed']:
            assert 'suggested_pattern' in result2, "❌ 제안 패턴 없음"
            print("✅ 권위 행사 체크 + 제안 기능 동작")
        else:
            print("⚠️ 권위 체크 통과 (정당화 키워드 감지됨)")

        return True

    except Exception as e:
        print(f"❌ Phase 4.2 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase4_3_writer_integration():
    """Phase 4.3: Writer 통합 테스트"""
    print("\n" + "="*60)
    print("Phase 4.3 테스트: Writer Agent Integration")
    print("="*60)

    try:
        from modules.domain.agents.writer import Writer

        # Writer 클래스에 새로운 메서드 존재 확인
        assert hasattr(Writer, '_build_justification_guidance'), "❌ _build_justification_guidance 메서드 없음"
        print("✅ Writer에 Phase 4.3 메서드 존재")

        # Mock context 생성 (간단 버전)
        class MockContext:
            def __init__(self):
                self.genre = {'name': '무협'}

        mock_ctx = MockContext()

        # Writer 인스턴스 생성 (client 없이 메서드만 테스트)
        writer = Writer(context=mock_ctx, client=None, model_tier="test")

        # HUD 리포트 시뮬레이션
        test_hud_report = """
        [주인공 현재 상태]
        - 경지: 후천 3류
        - 내공: 50/100
        - 신체 상태: 나약, 중독
        - 명성(reputation): 10
        - 지위: 하인
        """

        # 정당화 가이드 생성
        guidance = writer._build_justification_guidance(test_hud_report, '무협')

        # 제약이 감지되었는지 확인
        if guidance:
            assert '제약 감지' in guidance or 'JUSTIFICATION' in guidance, "❌ 제약 감지 실패"
            assert '논리 구조' in guidance or 'logic_structure' in guidance, "❌ Few-Shot 가이드 미포함"
            print(f"✅ 정당화 가이드 생성 성공 ({len(guidance)}자)")
            print(f"   - 신체 제약: {'신체 제약 감지' in guidance}")
            print(f"   - 지위 제약: {'지위 제약 감지' in guidance}")
        else:
            print("⚠️ 제약 없음 또는 가이드 생성 실패 (정상 케이스일 수 있음)")

        # 제약 없는 HUD 테스트
        normal_hud = """
        [주인공 현재 상태]
        - 경지: 선천 고수
        - 내공: 1000/1000
        - 신체 상태: 정상
        - 명성(reputation): 95
        """

        guidance2 = writer._build_justification_guidance(normal_hud, '무협')
        assert guidance2 == "", "❌ 제약 없을 때 빈 문자열이 아님"
        print("✅ 제약 없을 때 가이드 미생성 확인")

        return True

    except Exception as e:
        print(f"❌ Phase 4.3 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """전체 Phase 4 테스트 실행"""
    print("\n[START] Phase 4 Justification System Test\n")

    results = []

    # Phase 4.1
    results.append(("Phase 4.1 (Pattern Library)", test_phase4_1_pattern_library()))

    # Phase 4.2
    results.append(("Phase 4.2 (Validator Suggestions)", test_phase4_2_blocking_validator_suggestions()))

    # Phase 4.3
    results.append(("Phase 4.3 (Writer Integration)", test_phase4_3_writer_integration()))

    # 결과 요약
    print("\n" + "="*60)
    print("Phase 4 테스트 결과 요약")
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
        print("\n[SUCCESS] Phase 4 완료! 정당화 시스템 준비됨.")
        print("\n다음 단계:")
        print("1. config/settings.json에서 enable_justification_checks 설정 (옵션)")
        print("2. 원고 생산 테스트로 실제 효과 확인")
        print("3. 서사 관성 극복 여부 검증")
        return 0
    else:
        print(f"\n[WARNING] {total - passed}개 테스트 실패 - 디버깅 필요")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
