"""
[V60.55] duplicate_acquisition 로직 단독 테스트
- LLM 호출 없음, Python 로직만 검증
- 실행 시간: ~1초
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 테스트 케이스 정의
TEST_CASES = [
    # (item1, item2, expected_result, description)
    ("녹슨 백근 대도", "녹슨 백근 대도", True, "정확히 같은 아이템"),
    ("녹슨 백근 대도", "대도", False, "부분 포함 - 다른 아이템이어야 함"),
    ("대도", "녹슨 백근 대도", False, "부분 포함 역순 - 다른 아이템이어야 함"),
    ("철혈사자패", "철혈사자패(鐵血獅子牌)", False, "괄호 포함 - 다른 아이템이어야 함"),
    ("비자금 장부", "남궁세가 연루 비자금 장부", False, "수식어 차이 - 다른 아이템이어야 함"),
    ("칼", "녹슨 칼", False, "수식어 차이 - 다른 아이템이어야 함"),
    ("검", "검", True, "정확히 같은 아이템"),
    ("황금 육천 냥", "황금 육천 냥(어음 및 현물)", False, "괄호 포함 - 다른 아이템이어야 함"),
    ("팽조악의 비자금 장부", "비자금 장부", False, "소유격 차이 - 다른 아이템이어야 함"),
    ("하북 동부 상권 문서", "상권 문서", False, "지역명 차이 - 다른 아이템이어야 함"),
]

def test_is_same_item():
    """_is_same_item 메서드 테스트"""
    from modules.domain.agents.continuity_inspector import ContinuityInspector

    # Mock context와 client
    class MockContext:
        pass

    class MockClient:
        pass

    inspector = ContinuityInspector(MockContext(), MockClient())

    print("=" * 70)
    print(" [V60.55] _is_same_item 로직 테스트")
    print("=" * 70)

    passed = 0
    failed = 0

    for item1, item2, expected, desc in TEST_CASES:
        result = inspector._is_same_item(item1, item2)
        status = "✅ PASS" if result == expected else "❌ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}: {desc}")
        print(f"   '{item1}' vs '{item2}'")
        print(f"   예상: {expected}, 실제: {result}")

    print("\n" + "=" * 70)
    print(f" 결과: {passed}/{len(TEST_CASES)} 통과")
    if failed > 0:
        print(f" ⚠️ {failed}개 실패!")
    else:
        print(" ✅ 모든 테스트 통과!")
    print("=" * 70)

    return failed == 0


def test_duplicate_acquisition_flow():
    """중복 획득 검사 전체 흐름 테스트"""
    from modules.domain.agents.continuity_inspector import ContinuityInspector

    class MockContext:
        pass

    class MockClient:
        pass

    inspector = ContinuityInspector(MockContext(), MockClient())

    print("\n" + "=" * 70)
    print(" [V60.55] 중복 획득 검사 흐름 테스트")
    print("=" * 70)

    # 시나리오: Arc 1에서 "녹슨 백근 대도" 획득, Arc 2에서 "대도"가 나옴
    prev_arcs = [
        {
            "arc_no": 1,
            "tactical_doc": "팽무진이 녹슨 백근 대도를 획득했다.",
            "state_constraints": {
                "items_acquired": ["녹슨 백근 대도", "철혈사자패"]
            },
            "joint_docs": {
                "physical_inventory": ["녹슨 백근 대도", "철혈사자패"],
                "final_location": "연무장"
            },
            "status_shadow": {}
        }
    ]

    # Arc 2: "대도를 뽑아 들었다" (사용) vs "새 대도를 획득" (획득)
    current_arc_usage = {
        "arc_no": 2,
        "tactical_doc": "팽무진이 대도를 뽑아 들었다. 비자금 장부를 획득했다.",
        "state_constraints": {
            "items_acquired": ["비자금 장부"]  # 새 아이템만
        },
        "joint_docs": {
            "physical_inventory": ["녹슨 백근 대도", "철혈사자패", "비자금 장부"]
        },
        "status_shadow": {}
    }

    print("\n[테스트 1] 정상 케이스 - 새 아이템 획득")
    print("   Arc 1 획득: 녹슨 백근 대도, 철혈사자패")
    print("   Arc 2 획득: 비자금 장부 (새 아이템)")

    result = inspector.inspect_arc(current_arc_usage, prev_arcs)

    dup_violations = [v for v in result.get('critical_violations', [])
                      if v.get('type') == 'duplicate_acquisition']

    if not dup_violations:
        print("   ✅ PASS: 중복 획득 없음 (정상)")
    else:
        print(f"   ❌ FAIL: 중복 획득 감지됨 (오탐)")
        for v in dup_violations:
            print(f"      - {v.get('item_or_subject')}: {v.get('description')}")

    # 테스트 2: 실제 중복 획득
    current_arc_duplicate = {
        "arc_no": 2,
        "tactical_doc": "팽무진이 철혈사자패를 획득했다.",
        "state_constraints": {
            "items_acquired": ["철혈사자패"]  # Arc 1에서 이미 획득함
        },
        "joint_docs": {
            "physical_inventory": ["녹슨 백근 대도", "철혈사자패"]
        },
        "status_shadow": {}
    }

    print("\n[테스트 2] 실제 중복 - 같은 아이템 재획득")
    print("   Arc 1 획득: 녹슨 백근 대도, 철혈사자패")
    print("   Arc 2 획득: 철혈사자패 (중복!)")

    result2 = inspector.inspect_arc(current_arc_duplicate, prev_arcs)

    dup_violations2 = [v for v in result2.get('critical_violations', [])
                       if v.get('type') == 'duplicate_acquisition']

    if dup_violations2:
        print("   ✅ PASS: 중복 획득 감지됨 (정상)")
        for v in dup_violations2:
            print(f"      - {v.get('item_or_subject')}")
    else:
        print("   ❌ FAIL: 중복 획득 미감지 (미탐)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("\n[V60.55] duplicate_acquisition 로직 테스트 시작\n")

    success1 = test_is_same_item()
    test_duplicate_acquisition_flow()

    print("\n테스트 완료!")
