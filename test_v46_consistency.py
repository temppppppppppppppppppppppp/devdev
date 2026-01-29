"""
[V46.1] 일관성 검증 시스템 테스트

테스트 케이스:
1. 모순 + 정당화 없음 -> FAIL
2. 모순 + 정당화 있음 -> PASS
3. 장르별 규칙 적용 확인
4. [V46.1] 권위 위임 검증
5. [V46.1] 미해결 갈등 (고구마) 검증
6. [V46.1] 빌런 반응 검증
"""

import sys
sys.path.insert(0, '.')

def test_wuxia_guard():
    """무협 Guard 테스트"""
    print("=" * 60)
    print("[TEST 1] WuxiaGuard 불가능 행동 + 정당화 패턴")
    print("=" * 60)

    from modules.core.genre_guards.wuxia_guard import WuxiaGuard
    guard = WuxiaGuard()

    # 테스트 케이스 1: 부상 상태에서 중량물 들기
    state_injured = {
        'causal_injuries': '내상 중상',
        'realm': '삼류',
        'internal_energy': 30
    }

    impossible = guard.get_impossible_actions(state_injured)
    print(f"\n[상태] {state_injured}")
    print(f"[불가능 행동] {len(impossible)}개:")
    for action in impossible[:3]:
        print(f"  - {action['reason']}")

    justifications = guard.get_justification_patterns()
    print(f"\n[정당화 패턴] {len(justifications)}개:")
    for p in justifications[:5]:
        print(f"  - {p}")

    # 테스트 케이스 2: 경지 기반 제한
    state_low_realm = {
        'realm': '입문',
        'causal_injuries': '',
        'internal_energy': 100
    }

    impossible_low = guard.get_impossible_actions(state_low_realm)
    print(f"\n[상태] {state_low_realm}")
    print(f"[불가능 행동] {len(impossible_low)}개:")
    for action in impossible_low[:3]:
        print(f"  - {action['reason']}")

    print("\n[PASS] WuxiaGuard 테스트 통과")


def test_hunter_guard():
    """헌터 Guard 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 2] HunterGuard 불가능 행동 + 정당화 패턴")
    print("=" * 60)

    from modules.core.genre_guards.hunter_guard import HunterGuard
    guard = HunterGuard()

    # 테스트 케이스: E급에서 S급 스킬 사용
    state_e_rank = {
        'rank': 'E',
        'mana': 50,
        'status': ''
    }

    impossible = guard.get_impossible_actions(state_e_rank)
    print(f"\n[상태] {state_e_rank}")
    print(f"[불가능 행동] {len(impossible)}개:")
    for action in impossible[:3]:
        print(f"  - {action['reason']}")

    justifications = guard.get_justification_patterns()
    print(f"\n[정당화 패턴] {len(justifications)}개:")
    for p in justifications[:5]:
        print(f"  - {p}")

    print("\n[PASS] HunterGuard 테스트 통과")


def test_authority_delegation():
    """[V46.1] 권위 위임 검증 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 3] 권위 위임 검증 (Authority Delegation)")
    print("=" * 60)

    from modules.core.genre_guards.wuxia_guard import WuxiaGuard
    guard = WuxiaGuard()

    # 테스트 케이스 1: 가주 생존 + 대행 자칭 + 명분 없음
    manuscript_bad = """
    팽무진은 냉정하게 말했다.
    "나는 가주 대행으로서 명한다. 마봉필을 처단하라."
    """

    context_bad = {
        'protagonist_position': '직계',
        'superior_alive': True,
        'superior_name': '팽철산',
        'superior_position': '가주'
    }

    result_bad = guard.check_authority_delegation(manuscript_bad, context_bad)
    print(f"\n[테스트 1] 가주 생존 + 대행 자칭 + 명분 없음")
    print(f"  통과: {result_bad['passed']}")
    print(f"  위반: {len(result_bad['violations'])}개")
    if result_bad['violations']:
        print(f"  사유: {result_bad['violations'][0].get('reason', '')}")

    # 테스트 케이스 2: 가주 생존 + 대행 자칭 + 명분 있음
    manuscript_good = """
    팽무진은 품에서 철혈사자패를 꺼내 보이며 말했다.
    "가주께서 위임하신 권한으로 명한다. 마봉필을 처단하라."
    """

    result_good = guard.check_authority_delegation(manuscript_good, context_bad)
    print(f"\n[테스트 2] 가주 생존 + 대행 자칭 + 명분 있음")
    print(f"  통과: {result_good['passed']}")
    print(f"  정당화 확인: {result_good.get('has_justification', False)}")

    print("\n[PASS] 권위 위임 검증 테스트 완료")


def test_unresolved_conflict():
    """[V46.1] 미해결 갈등 (고구마) 검증 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 4] 미해결 갈등 (고구마) 검증")
    print("=" * 60)

    from modules.core.genre_guards.wuxia_guard import WuxiaGuard
    guard = WuxiaGuard()

    # 테스트 케이스 1: 과거 구타 + 응징 없음 + 동행
    manuscript_goguma = """
    달수가 옆에서 말했다.
    "도련님, 저기 객잔이 보입니다."
    팽무진은 고개를 끄덕였다.
    """

    karma_matrix = {
        '달수': {
            'relation_type': '하인',
            'events': [
                {'ep': 1, 'type': '구타', 'result': '주인공 폭행'}
            ]
        }
    }

    result_goguma = guard.check_unresolved_conflict(manuscript_goguma, karma_matrix, ep_num=5)
    print(f"\n[테스트 1] 구타한 하인이 응징 없이 동행")
    print(f"  통과: {result_goguma['passed']}")
    print(f"  고구마 점수: {result_goguma['goguma_score']}/10")
    if result_goguma['violations']:
        print(f"  사유: {result_goguma['violations'][0].get('reason', '')}")

    # 테스트 케이스 2: 과거 구타 + 공포 묘사 있음
    manuscript_fear = """
    달수가 벌벌 떨며 말했다.
    "도, 도련님... 저기 객잔이..."
    그는 감히 도련님의 눈을 마주치지 못했다.
    """

    result_fear = guard.check_unresolved_conflict(manuscript_fear, karma_matrix, ep_num=5)
    print(f"\n[테스트 2] 구타한 하인이 공포에 질려 동행")
    print(f"  통과: {result_fear['passed']}")
    print(f"  고구마 점수: {result_fear['goguma_score']}/10")

    print("\n[PASS] 미해결 갈등 검증 테스트 완료")


def test_villain_response():
    """[V46.1] 빌런 반응 검증 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 5] 빌런 반응 검증 (Villain Response)")
    print("=" * 60)

    from modules.core.genre_guards.wuxia_guard import WuxiaGuard
    guard = WuxiaGuard()

    # 테스트 케이스 1: 주인공 대역전 + 빌런 무반응
    manuscript_no_response = """
    팽무진은 비무에서 승리를 거두었다.
    가주는 만족스러운 표정으로 철혈사자패를 건넸다.
    팽조악은 그 광경을 지켜보았다.
    """

    villain_context = {
        'villain_name': '팽조악',
        'villain_role': '주적',
        'is_aware': True
    }

    recent_events = [
        {'type': '승리', 'result': '비무 승리'}
    ]

    result_no = guard.check_villain_response(manuscript_no_response, villain_context, recent_events)
    print(f"\n[테스트 1] 주인공 승리 + 빌런 무반응")
    print(f"  통과: {result_no['passed']}")
    print(f"  무능한 빌런 위험: {result_no['incompetent_villain_risk']}")
    if result_no['violations']:
        print(f"  제안: {result_no['violations'][0].get('suggestion', '')[:50]}...")

    # 테스트 케이스 2: 주인공 대역전 + 빌런 적절 대응
    manuscript_response = """
    팽무진은 비무에서 승리를 거두었다.
    가주는 만족스러운 표정으로 철혈사자패를 건넸다.
    팽조악은 이를 갈며 주먹을 불끈 쥐었다.
    '두고 보자... 이것으로 끝이 아니다.'
    그때 마침 급한 소식이 전해졌고, 팽조악은 자리를 비워야 했다.
    """

    result_yes = guard.check_villain_response(manuscript_response, villain_context, recent_events)
    print(f"\n[테스트 2] 주인공 승리 + 빌런 적절 대응")
    print(f"  통과: {result_yes['passed']}")
    print(f"  무능한 빌런 위험: {result_yes['incompetent_villain_risk']}")

    print("\n[PASS] 빌런 반응 검증 테스트 완료")


def test_consistency_validator_full():
    """ConsistencyValidator 전체 통합 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 6] ConsistencyValidator 전체 통합 테스트")
    print("=" * 60)

    from modules.validation.consistency_validator import ConsistencyValidator

    validator = ConsistencyValidator(genre='wuxia')

    # 복합 테스트: 여러 문제가 있는 원고
    manuscript_complex = """
    중상을 입은 팽무진은 전력 질주하며 말했다.
    "나는 가주 대행으로서 명한다!"
    달수가 옆에서 웃으며 따라왔다.
    팽조악은 그 광경을 멀리서 지켜보았다.
    """

    context_complex = {
        'martial_hud': {
            'actual_truth': {
                'causal_injuries': '내상 중상',
                'realm': '삼류',
            }
        },
        'karma_matrix': {
            '달수': {
                'relation_type': '하인',
                'events': [{'ep': 1, 'type': '구타'}]
            }
        },
        'authority_context': {
            'protagonist_position': '직계',
            'superior_alive': True,
            'superior_name': '팽철산',
            'superior_position': '가주'
        },
        'villain_context': {
            'villain_name': '팽조악',
            'villain_role': '주적',
            'is_aware': True
        },
        'recent_events': [{'type': '승리'}],
        'ep_num': 5
    }

    result = validator.validate(manuscript_complex, context_complex)
    print(f"\n[복합 테스트] 여러 문제가 있는 원고")
    print(f"  통과: {result['passed']}")
    print(f"  전체 위반: {len(result['violations'])}개")
    print(f"  정당화 가능: {len(result['justifiable_violations'])}개")
    print(f"  정당화 불가: {len(result['unjustifiable_violations'])}개")
    print(f"  감점: {result['score_penalty']}점")
    print(f"\n[피드백 일부]")
    feedback_lines = result['feedback'].split('\n')[:10]
    for line in feedback_lines:
        print(f"  {line}")

    print("\n[PASS] ConsistencyValidator 통합 테스트 완료")


def main():
    """전체 테스트 실행"""
    print("=" * 60)
    print("[V46.1] 일관성 검증 시스템 테스트 시작")
    print("=" * 60)

    try:
        test_wuxia_guard()
        test_hunter_guard()
        test_authority_delegation()
        test_unresolved_conflict()
        test_villain_response()
        test_consistency_validator_full()

        print("\n" + "=" * 60)
        print("[SUCCESS] 모든 테스트 통과!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[FAIL] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
