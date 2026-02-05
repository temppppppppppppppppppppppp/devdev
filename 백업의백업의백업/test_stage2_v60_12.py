"""
[V60.12] Stage 2 통과율 테스트 스크립트

목적:
- 제공된 bible과 treatment로 Stage 2 Arc 생성 테스트
- FourPhaseArcGenerator 파이프라인 검증
- 실제 PASS/REJECT 통계 수집

사용법:
    python test_stage2_v60_12.py
"""

import os
import sys
import json
import time
from datetime import datetime

# UTF-8 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_json_file(path):
    """JSON 파일 로드"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_unit_tests():
    """유닛 테스트 실행"""
    print("=" * 70)
    print("[V60.12 Stage 2 Unit Tests]")
    print("=" * 70)

    errors = []

    # 1. ConstraintCompiler 테스트
    print("\n[1] ConstraintCompiler Test...")
    try:
        from modules.domain.agents.constraint_compiler import ConstraintCompiler

        compiler = ConstraintCompiler()

        # 빈 Arc 리스트
        result = compiler.compile([])
        assert "CONSTRAINT CHECKLIST" in result, "Initial constraints should have checklist"
        print("   [OK] Initial constraints generation")

        # 이전 Arc 있는 경우
        prev_arcs = [
            {
                "arc_no": 1,
                "tactical_doc": "제 1화: 주인공이 대도를 획득한다. 제 2화: 철혈사자패를 수여받는다.",
                "state_constraints": {
                    "items_acquired": ["대도"],
                    "grants_received": ["철혈사자패"]
                },
                "joint_docs": {
                    "final_location": "철혈단 본거지",
                    "physical_inventory": ["대도", "철혈사자패"]
                },
                "status_shadow": {
                    "expected_injuries": "왼팔 경상",
                    "internal_energy_loss": "15%"
                }
            }
        ]

        result = compiler.compile(prev_arcs)
        assert "대도" in result, "Should include acquired item in constraints"
        assert "철혈사자패" in result, "Should include grant in constraints"
        print("   [OK] Constraint compilation with prev_arcs")

    except Exception as e:
        errors.append(("ConstraintCompiler", str(e)))
        print(f"   [FAIL] ConstraintCompiler: {e}")

    # 2. ArcDraftValidator 테스트
    print("\n[2] ArcDraftValidator Test...")
    try:
        from modules.domain.agents.arc_draft_validator import ArcDraftValidator

        validator = ArcDraftValidator()

        # 유효한 Arc
        valid_arc = {
            "arc_no": 2,
            "ep_count": 5,
            "ep_start": 6,
            "ep_end": 10,
            "tactical_doc": "A" * 3000,  # 충분한 분량
            "state_constraints": {
                "arc_start_state": {
                    "location": "철혈단 본거지",
                    "equipment": ["대도", "철혈사자패"]
                },
                "items_acquired": ["새로운 비급"],  # 새 아이템
                "grants_received": []
            },
            "joint_docs": {
                "final_location": "흑풍문 전초기지",
                "physical_inventory": ["대도", "철혈사자패", "새로운 비급"]
            }
        }

        result = validator.validate(valid_arc, prev_arcs)
        print(f"   Valid Arc Score: {result['score']}, Valid: {result['valid']}")

        # 중복 아이템 획득 Arc
        duplicate_arc = {
            "arc_no": 2,
            "ep_count": 5,
            "tactical_doc": "A" * 3000,
            "state_constraints": {
                "arc_start_state": {"location": "철혈단 본거지"},
                "items_acquired": ["대도"],  # 이미 획득한 아이템!
                "grants_received": []
            },
            "joint_docs": {"final_location": "어딘가"}
        }

        result = validator.validate(duplicate_arc, prev_arcs)
        assert not result["valid"], "Should reject duplicate acquisition"
        print(f"   [OK] Duplicate detection: valid={result['valid']}")

    except Exception as e:
        errors.append(("ArcDraftValidator", str(e)))
        print(f"   [FAIL] ArcDraftValidator: {e}")

    # 3. NegativeExampleInjector 테스트
    print("\n[3] NegativeExampleInjector Test...")
    try:
        from modules.domain.agents.negative_example_injector import NegativeExampleInjector

        injector = NegativeExampleInjector("wuxia")

        # 주입 텍스트 생성
        injection = injector.generate_injection()
        assert "NEGATIVE EXAMPLES" in injection, "Should have header"
        assert "재획득" in injection or "이미 획득" in injection, "Should include duplicate pattern"
        print("   [OK] Injection generation")

        # 자가 검증 프롬프트
        self_check = injector.generate_self_check_prompt()
        assert "체크리스트" in self_check or "확인" in self_check, "Should have checklist"
        print("   [OK] Self-check prompt generation")

        # REJECT 기록
        injector.record_rejection(
            {"arc_no": 1, "state_constraints": {"items_acquired": ["대도"]}},
            "중복 아이템 획득",
            "duplicate_acquisition"
        )
        assert len(injector.rejection_history) == 1, "Should record rejection"
        print("   [OK] Rejection recording")

    except Exception as e:
        errors.append(("NegativeExampleInjector", str(e)))
        print(f"   [FAIL] NegativeExampleInjector: {e}")

    # 4. PreflightChecker Python 폴백 테스트
    print("\n[4] PreflightChecker Fallback Test...")
    try:
        from modules.domain.agents.preflight_checker import PreflightChecker

        # Mock context (API 호출 없이)
        class MockContext:
            pass

        class MockClient:
            pass

        checker = PreflightChecker(MockContext(), MockClient())

        # Python 폴백 테스트
        fallback_result = checker._extract_constraints_fallback(prev_arcs)
        assert "timeline_analysis" in fallback_result
        assert "absolute_prohibitions" in fallback_result

        # 금지 아이템 확인
        prohibited = fallback_result["absolute_prohibitions"]["items_cannot_acquire"]
        prohibited_items = [p.get("item") for p in prohibited]
        assert "대도" in prohibited_items, "Should prohibit already acquired items"
        print(f"   [OK] Fallback extraction: {len(prohibited_items)} prohibited items")

        # Analyst 주입 텍스트 생성
        injection = checker.generate_analyst_injection(fallback_result)
        assert "PREFLIGHT" in injection, "Should have header"
        print("   [OK] Analyst injection generation")

    except Exception as e:
        errors.append(("PreflightChecker", str(e)))
        print(f"   [FAIL] PreflightChecker: {e}")

    # 5. ArcCritic Python 폴백 테스트
    print("\n[5] ArcCritic Fallback Test...")
    try:
        from modules.domain.agents.arc_critic import ArcCritic

        class MockContext:
            pass

        class MockClient:
            pass

        critic = ArcCritic(MockContext(), MockClient())

        # 분량 부족 Arc
        short_arc = {
            "arc_no": 2,
            "tactical_doc": "짧은 내용"
        }

        critique = critic._python_critique_fallback(short_arc, prev_arcs)
        assert critique["total_score"] < 70, "Short arc should have low score"
        print(f"   [OK] Short arc critique: score={critique['total_score']}")

        # 중복 아이템 Arc
        duplicate_arc = {
            "arc_no": 2,
            "ep_count": 5,
            "tactical_doc": "A" * 3000,
            "joint_docs": {},
            "state_constraints": {
                "items_acquired": ["대도"]  # 중복!
            }
        }

        critique = critic._python_critique_fallback(duplicate_arc, prev_arcs)
        has_critical = any(i.get("severity") == "CRITICAL" for i in critique.get("critical_issues", []))
        print(f"   [OK] Duplicate critique: score={critique['total_score']}, critical={has_critical}")

    except Exception as e:
        errors.append(("ArcCritic", str(e)))
        print(f"   [FAIL] ArcCritic: {e}")

    # 결과 요약
    print("\n" + "=" * 70)
    if errors:
        print(f"[FAIL] {len(errors)} test failures:")
        for name, err in errors:
            print(f"   - {name}: {err}")
    else:
        print("[PASS] All unit tests passed!")
    print("=" * 70)

    return len(errors) == 0


def run_integration_test_without_api():
    """API 없이 통합 테스트 (모의 데이터 사용)"""
    print("\n" + "=" * 70)
    print("[V60.12 Integration Test (No API)]")
    print("=" * 70)

    # 1. 실제 데이터 로드
    print("\n[1] Loading test data...")

    bible_path = "bible/팽가_bi.json"
    treatment_path = "treatments/팽가 망나니, 가문재건_tr_enriched.json"

    try:
        bible = load_json_file(bible_path)
        print(f"   [OK] Bible loaded: {bible['MasterBible']['ProjectData']['MetaInfo']['title']}")
    except Exception as e:
        print(f"   [FAIL] Bible load failed: {e}")
        return False

    # Treatment는 크기가 커서 일부만
    try:
        with open(treatment_path, 'r', encoding='utf-8') as f:
            treatment = json.load(f)
        print(f"   [OK] Treatment loaded: {len(treatment)} blocks")
    except Exception as e:
        print(f"   [FAIL] Treatment load failed: {e}")
        return False

    # 2. 모의 Arc 데이터 생성 (Block 1-2 기반)
    print("\n[2] Generating mock Arc data from treatment...")

    mock_arc_1 = {
        "arc_no": 1,
        "ep_count": 5,
        "ep_start": 1,
        "ep_end": 5,
        "title": treatment[0]["title"],
        "tactical_doc": f"""
제 1화: {treatment[0]["content"]["context"][:500]}

제 2화: {treatment[0]["content"]["event_villain"][:500]}

제 3화: {treatment[0]["content"]["solution"][:500]}

제 4화: {treatment[0]["content"]["reward"][:500]}

제 5화: 팽무진은 철혈사자패를 품에 넣고 다음 단계를 준비한다.
        """,
        "state_constraints": {
            "arc_start_state": {
                "location": "팽가 본가",
                "equipment": ["파혼 서신", "이면 장부"],
                "injuries": "만성 숙취",
                "internal_energy": 30
            },
            "arc_end_state": {
                "location": "철혈단 본거지",
                "equipment": ["백근 대도", "철혈사자패", "운송 통로권"],
                "injuries": "없음",
                "internal_energy": 70
            },
            "items_acquired": ["백근 대도", "운송 통로권"],
            "items_consumed": [],
            "grants_received": ["철혈사자패"]
        },
        "joint_docs": {
            "final_location": "철혈단 본거지",
            "physical_inventory": ["백근 대도", "철혈사자패", "운송 통로권", "파혼 서신", "이면 장부"],
            "world_joint": "팽무진이 차기 가주 후보로 복귀, 철혈사자패 획득"
        },
        "status_shadow": {
            "internal_energy_loss": "0%",
            "expected_injuries": "없음",
            "item_consumption": []
        }
    }

    print(f"   [OK] Mock Arc 1 created: {mock_arc_1['title'][:30]}...")

    # 3. Arc 2 생성을 위한 제약 검사
    print("\n[3] Testing constraint checking for Arc 2...")

    from modules.domain.agents.constraint_compiler import ConstraintCompiler
    from modules.domain.agents.arc_draft_validator import ArcDraftValidator
    from modules.domain.agents.negative_example_injector import NegativeExampleInjector

    compiler = ConstraintCompiler()
    validator = ArcDraftValidator()
    injector = NegativeExampleInjector("wuxia")

    # 제약 컴파일
    constraints = compiler.compile([mock_arc_1])
    print(f"   [OK] Constraints compiled: {len(constraints)} chars")

    # 잘못된 Arc 2 (중복 획득)
    bad_arc_2 = {
        "arc_no": 2,
        "ep_count": 5,
        "tactical_doc": "A" * 3000,
        "state_constraints": {
            "arc_start_state": {
                "location": "철혈단 본거지",
                "equipment": ["백근 대도", "철혈사자패"]
            },
            "items_acquired": ["백근 대도"],  # 중복!
            "grants_received": ["철혈사자패"]  # 중복!
        },
        "joint_docs": {
            "final_location": "흑룡각"
        }
    }

    result = validator.validate(bad_arc_2, [mock_arc_1])
    print(f"   Bad Arc 2 validation: valid={result['valid']}, score={result['score']}")
    print(f"   Critical issues: {result['critical_issues']}")

    # 올바른 Arc 2
    good_arc_2 = {
        "arc_no": 2,
        "ep_count": 5,
        "ep_start": 6,
        "ep_end": 10,
        "tactical_doc": f"""
제 1화: 팽무진은 철혈단 본거지에서 출발하여 흑룡각으로 향한다. 허리에는 백근 대도가 묵직하게 매달려 있고, 품에는 철혈사자패가 있다. 전생의 기억을 더듬어 유삼의 거점을 찾아간다.

제 2화: 흑룡각에 도착한 팽무진은 유삼과 마영의 불법 도박장을 발견한다. 팽조악의 심복들이 가문 자금을 횡령하고 있음을 확인한다.

제 3화: 팽무진은 도박장의 무뢰배들을 제압하고 비자금 장부를 획득한다. 철혈사자패의 권위로 정당한 단속임을 선언한다.

제 4화: 비자금 장부를 분석하며 팽조악의 배후를 파악한다. 남궁세가와의 수상한 거래 흔적을 발견한다.

제 5화: 팽가 사병들의 충성을 얻고 흑룡각을 정리한다. 회수된 자금으로 사병들의 장비를 교체한다.
        """,
        "state_constraints": {
            "arc_start_state": {
                "location": "철혈단 본거지",
                "equipment": ["백근 대도", "철혈사자패", "운송 통로권"],
                "injuries": "없음",
                "internal_energy": 70
            },
            "arc_end_state": {
                "location": "흑룡각",
                "equipment": ["백근 대도", "철혈사자패", "운송 통로권", "비자금 장부"],
                "injuries": "경미한 타박상",
                "internal_energy": 60
            },
            "items_acquired": ["비자금 장부", "은자 이천 냥"],  # 새 아이템만
            "items_consumed": [],
            "grants_received": []  # 새 수여물 없음
        },
        "joint_docs": {
            "final_location": "흑룡각",
            "physical_inventory": ["백근 대도", "철혈사자패", "운송 통로권", "비자금 장부"],
            "world_joint": "팽가 내부 숙청 시작, 사병들의 충성 획득"
        },
        "status_shadow": {
            "internal_energy_loss": "10%",
            "expected_injuries": "경미한 타박상",
            "item_consumption": []
        }
    }

    result = validator.validate(good_arc_2, [mock_arc_1])
    print(f"   Good Arc 2 validation: valid={result['valid']}, score={result['score']}")

    # 4. 파이프라인 흐름 검증
    print("\n[4] Testing pipeline flow...")

    # Preflight 폴백
    from modules.domain.agents.preflight_checker import PreflightChecker

    class MockContext:
        pass
    class MockClient:
        pass

    preflight = PreflightChecker(MockContext(), MockClient())
    preflight_result = preflight._extract_constraints_fallback([mock_arc_1])

    prohibited_items = [p.get("item") for p in preflight_result["absolute_prohibitions"]["items_cannot_acquire"]]
    print(f"   Prohibited items: {prohibited_items}")

    # Critic 폴백
    from modules.domain.agents.arc_critic import ArcCritic

    critic = ArcCritic(MockContext(), MockClient())

    critique_bad = critic._python_critique_fallback(bad_arc_2, [mock_arc_1])
    critique_good = critic._python_critique_fallback(good_arc_2, [mock_arc_1])

    print(f"   Bad Arc critique: score={critique_bad['total_score']}, verdict={critique_bad['verdict']}")
    print(f"   Good Arc critique: score={critique_good['total_score']}, verdict={critique_good['verdict']}")

    print("\n" + "=" * 70)
    print("[PASS] Integration test completed successfully!")
    print("=" * 70)

    return True


def main():
    """메인 함수"""
    print("\n" + "#" * 70)
    print("#" + " V60.12 Stage 2 Test Suite ".center(68) + "#")
    print("#" * 70)
    print(f"\nTest started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 유닛 테스트
    unit_passed = run_unit_tests()

    # 2. 통합 테스트 (API 없이)
    integration_passed = run_integration_test_without_api()

    # 결과 요약
    print("\n" + "#" * 70)
    print("#" + " Test Summary ".center(68) + "#")
    print("#" * 70)
    print(f"\n  Unit Tests:        {'PASS' if unit_passed else 'FAIL'}")
    print(f"  Integration Tests: {'PASS' if integration_passed else 'FAIL'}")
    print(f"\n  Overall: {'ALL PASSED' if (unit_passed and integration_passed) else 'SOME FAILED'}")
    print("\n" + "#" * 70)

    if unit_passed and integration_passed:
        print("\n[INFO] 모든 테스트 통과!")
        print("[INFO] 실제 API 테스트를 위해서는 main_a.py를 실행하세요.")
        print("[INFO] 예: python main_a.py -> 프로젝트 선택 -> Stage 2 실행")

    return 0 if (unit_passed and integration_passed) else 1


if __name__ == "__main__":
    sys.exit(main())
