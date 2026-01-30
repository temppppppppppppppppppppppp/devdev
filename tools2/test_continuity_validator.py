# -*- coding: utf-8 -*-
"""
[V47] ContinuityValidator 테스트

테스트 항목:
1. 아이템 중복 획득 감지
2. 무기 상태 리셋 감지
3. 부상 상태 연속성
4. 정상 케이스 통과
"""

import sys
import os
import io

# Windows 콘솔 UTF-8 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.validation.continuity_validator import ContinuityValidator


def test_duplicate_item_acquisition():
    """이미 소유한 아이템을 다시 획득하는 케이스"""
    print("\n" + "="*60)
    print("테스트 1: 아이템 중복 획득 감지")
    print("="*60)
    
    validator = ContinuityValidator()
    
    # 직전 에피소드에서 대도를 가지고 있음
    prev_hud = {
        "actual_truth": {
            "equipment": ["녹슨 백근 대도", "철혈사자패"]
        }
    }
    
    # 현재 에피소드에서 다시 대도를 획득하러 감
    manuscript = """
    비무가 끝난 연무장의 열기가 채 가시지 않은 해 질 녘, 팽무진은 병장고로 향했다.
    병장고 입구에서 무사들이 막아섰지만 철혈사자패를 보여주자 길을 열었다.
    그는 구석에 처박힌 일백 근 대도를 집어 들어 어깨에 둘러멨다.
    """
    
    validation_context = {"prev_hud": prev_hud}
    result = validator.validate(current_ep=5, manuscript=manuscript, 
                                validation_context=validation_context)
    
    print(f"결과: {'REJECT' if not result['passed'] else 'PASS'}")
    print(f"위반 수: {len(result['violations'])}")
    
    for v in result['violations']:
        print(f"  - [{v['severity']}] {v['reason']}")
        print(f"    수정 방법: {v.get('fix_suggestion', '')}")
    
    assert not result['passed'], "중복 획득이 감지되어야 함"
    assert len(result['violations']) >= 1, "최소 1개 위반"
    print("[PASS] 테스트 통과!")


def test_weapon_state_reset():
    """직전 에피소드에서 들고 있던 무기가 리셋되는 케이스"""
    print("\n" + "="*60)
    print("테스트 2: 무기 상태 리셋 감지")
    print("="*60)
    
    validator = ContinuityValidator()
    
    prev_hud = {
        "actual_truth": {
            "equipment": ["녹슨 백근 대도"]
        }
    }
    
    # 직전 원고: 대도를 어깨에 메고 있음
    prev_manuscript = """
    팽무진은 녹슨 백 근 대도를 어깨에 멘 채 연무장을 빠져나왔다.
    그의 어깨 위에서 묵직한 대도가 석양빛을 받아 붉게 물들었다.
    """
    
    # 현재 원고: 대도를 다시 획득하러 감
    current_manuscript = """
    해가 저문 후, 팽무진은 무기고로 향했다.
    구석에 먼지를 뒤집어쓴 일백 근 대도를 집어 들었다.
    """
    
    validation_context = {
        "prev_hud": prev_hud,
        "prev_full_text": prev_manuscript
    }
    
    result = validator.validate(current_ep=5, manuscript=current_manuscript,
                                validation_context=validation_context)
    
    print(f"결과: {'REJECT' if not result['passed'] else 'PASS'}")
    print(f"위반 수: {len(result['violations'])}")
    
    for v in result['violations']:
        print(f"  - [{v['severity']}] {v['reason']}")
    
    assert not result['passed'], "무기 리셋이 감지되어야 함"
    print("[PASS] 테스트 통과!")


def test_injury_continuity_warning():
    """부상 상태에서 무리한 행동 경고"""
    print("\n" + "="*60)
    print("테스트 3: 부상 상태 연속성 경고")
    print("="*60)
    
    validator = ContinuityValidator()
    
    # 직전 에피소드에서 어깨 부상
    prev_hud = {
        "actual_truth": {
            "condition": "우측 어깨 근육 파열",
            "equipment": ["녹슨 백근 대도"]
        }
    }
    
    prev_manuscript = """
    대도를 억지로 휘두른 반동으로 팽무진의 우측 어깨 근육이 파열되었다.
    """
    
    # 현재 원고: 부상에도 불구하고 대도를 휘두름 (정당화 없음)
    current_manuscript = """
    팽무진은 대도를 휘두르며 적들을 베어 나갔다.
    그의 대도는 적의 검을 부러뜨렸다.
    """
    
    validation_context = {
        "prev_hud": prev_hud,
        "prev_full_text": prev_manuscript
    }
    
    result = validator.validate(current_ep=5, manuscript=current_manuscript,
                                validation_context=validation_context)
    
    print(f"결과: {'REJECT' if not result['passed'] else 'PASS'}")
    print(f"경고 수: {len(result['warnings'])}")
    
    for w in result['warnings']:
        print(f"  - [{w.get('severity', 'WARNING')}] {w['reason']}")
    
    # 부상은 경고만, REJECT하지 않음
    assert result['passed'], "부상은 경고만 (PASS)"
    assert len(result['warnings']) >= 1, "최소 1개 경고"
    print("[PASS] 테스트 통과!")


def test_normal_case_pass():
    """정상 케이스 통과"""
    print("\n" + "="*60)
    print("테스트 4: 정상 케이스 통과")
    print("="*60)
    
    validator = ContinuityValidator()
    
    # 직전 에피소드에서 대도를 가지고 있음
    prev_hud = {
        "actual_truth": {
            "equipment": ["녹슨 백근 대도", "철혈사자패"]
        }
    }
    
    prev_manuscript = """
    팽무진은 녹슨 백 근 대도를 어깨에 메고 서쪽 창고로 향했다.
    """
    
    # 현재 원고: 대도를 이미 들고 있는 상태로 시작
    current_manuscript = """
    어깨에 멘 녹슨 대도의 무게가 묵직했다.
    팽무진은 창고 문 앞에 섰다. 그의 손에 들린 철혈사자패가 번뜩였다.
    "문을 열어라." 그가 차갑게 말했다.
    """
    
    validation_context = {
        "prev_hud": prev_hud,
        "prev_full_text": prev_manuscript
    }
    
    result = validator.validate(current_ep=5, manuscript=current_manuscript,
                                validation_context=validation_context)
    
    print(f"결과: {'REJECT' if not result['passed'] else 'PASS'}")
    print(f"위반 수: {len(result['violations'])}")
    print(f"경고 수: {len(result['warnings'])}")
    
    assert result['passed'], "정상 케이스는 PASS"
    assert len(result['violations']) == 0, "위반 없음"
    print("[PASS] 테스트 통과!")


def test_first_episode_skip():
    """첫 번째 에피소드는 검증 스킵"""
    print("\n" + "="*60)
    print("테스트 5: 첫 번째 에피소드 스킵")
    print("="*60)
    
    validator = ContinuityValidator()
    
    result = validator.validate(current_ep=1, manuscript="아무 내용",
                                validation_context={})
    
    print(f"결과: {'REJECT' if not result['passed'] else 'PASS'}")
    print(f"메시지: {result['message']}")
    
    assert result['passed'], "1화는 스킵"
    print("[PASS] 테스트 통과!")


def main():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("[V47] ContinuityValidator 테스트 시작")
    print("="*60)
    
    tests = [
        test_first_episode_skip,
        test_duplicate_item_acquisition,
        test_weapon_state_reset,
        test_injury_continuity_warning,
        test_normal_case_pass,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] 테스트 실패: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] 테스트 오류: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"테스트 결과: {passed}/{len(tests)} 통과")
    if failed == 0:
        print("*** 모든 테스트 통과! ***")
    else:
        print(f"[WARNING] {failed}개 테스트 실패")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
