"""
Phase 3 Systems Integration Test
모든 Phase 3 기능 통합 테스트 및 데모
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import json
from pathlib import Path
from datetime import datetime
from modules.core.data_collector import DataCollector, RLHFCollector
from modules.core.prompt_optimizer import PromptOptimizer, quick_optimize
from modules.core.finetuning_automation import FineTuningManager, quick_finetuning_check


def print_section(title):
    """섹션 헤더 출력"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_data_collection():
    """1. 데이터 수집 시스템 테스트"""
    print_section("1️⃣ Data Collection System Test")

    project_name = "test_project"
    collector = DataCollector(project_name)

    # 샘플 검증 결과 생성
    sample_manuscript = "테스트 원고입니다. " * 500  # 약 4000자
    sample_validation = {
        'total_score': 85,
        'final_decision': 'PASS',
        'blocking_result': {'passed': True},
        'scoring_result': {'passed': True, 'breakdown': {}}
    }
    sample_context = {
        'blueprint': {'scenes': []},
        'hud_snapshot': {}
    }

    # 데이터 수집
    print("✅ Collecting sample validation result...")
    collector.collect_validation_result(
        ep_num=1,
        manuscript=sample_manuscript,
        validation_result=sample_validation,
        validation_context=sample_context
    )

    # 데이터셋 확인
    datasets_dir = Path("datasets") / project_name
    approved_count = len(list((datasets_dir / "approved").glob("*.json"))) if (datasets_dir / "approved").exists() else 0
    rejected_count = len(list((datasets_dir / "rejected").glob("*.json"))) if (datasets_dir / "rejected").exists() else 0

    print(f"📊 Dataset Status:")
    print(f"   Approved: {approved_count}")
    print(f"   Rejected: {rejected_count}")
    print(f"   Location: {datasets_dir}")

    # Fine-tuning 준비 상태 확인
    print("\n🔍 Checking fine-tuning readiness...")
    from modules.core.finetuning_automation import FineTuningManager
    ft_manager = FineTuningManager("test_project")
    readiness = ft_manager.check_readiness(str(datasets_dir))
    print(f"   Ready: {readiness['ready']}")
    print(f"   Approved count: {readiness.get('approved_count', 0)}")
    print(f"   Required minimum: {readiness.get('min_required', 100)}")
    if not readiness['ready']:
        print(f"   ⚠️ {readiness.get('reason', 'Unknown')}")

    return True


def test_prompt_optimization():
    """2. 프롬프트 최적화 시스템 테스트"""
    print_section("2️⃣ Prompt Optimization System Test")

    optimizer = PromptOptimizer("test_project")

    # 샘플 검증 결과 생성
    sample_results = [
        {
            'total_score': 75,
            'decision': 'PASS',
            'scoring_result': {
                'breakdown': {
                    'character_consistency': {'score': 15, 'max': 20},
                    'emotion_arc': {'score': 14, 'max': 20},
                    'dialogue_quality': {'score': 16, 'max': 20},
                    'commercial_appeal': {'score': 18, 'max': 25},
                    'pattern_diversity': {'score': 12, 'max': 15}
                }
            }
        },
        {
            'total_score': 82,
            'decision': 'PASS',
            'scoring_result': {
                'breakdown': {
                    'character_consistency': {'score': 18, 'max': 20},
                    'emotion_arc': {'score': 16, 'max': 20},
                    'dialogue_quality': {'score': 17, 'max': 20},
                    'commercial_appeal': {'score': 20, 'max': 25},
                    'pattern_diversity': {'score': 11, 'max': 15}
                }
            }
        }
    ]

    print("✅ Analyzing validation results...")
    analysis = optimizer.analyze_validation_results(sample_results)

    print(f"📊 Analysis Results:")
    print(f"   Total evaluations: {analysis['total_evaluations']}")
    print(f"   Average score: {analysis['avg_score']:.1f}")
    print(f"   Pass rate: {analysis['pass_rate']:.1%}")
    print(f"   Std dev: {analysis['std_dev']:.2f}")

    if analysis['weaknesses']:
        print(f"\n⚠️ Identified Weaknesses:")
        for category, score in analysis['weaknesses']:
            print(f"   • {category}: {score:.1f}%")

    # 개선된 프롬프트 생성
    original_prompt = """당신은 웹소설 품질 평가자입니다.
원고를 평가하고 점수를 부여하십시오."""

    print("\n✅ Generating improved prompt...")
    improved_prompt = optimizer.generate_improved_prompt(
        original_prompt,
        analysis['weaknesses'],
        analysis
    )

    print(f"\n📝 Improved Prompt Preview:")
    print(improved_prompt[:300] + "..." if len(improved_prompt) > 300 else improved_prompt)

    # 리포트 생성
    report = optimizer.generate_report(analysis)
    report_file = "optimization_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n💾 Full report saved to: {report_file}")

    return True


def test_finetuning_automation():
    """3. Fine-tuning 자동화 시스템 테스트"""
    print_section("3️⃣ Fine-tuning Automation System Test")

    project_name = "test_project"
    manager = FineTuningManager(project_name)

    # 준비 상태 확인
    data_dir = f"datasets/{project_name}"
    print("✅ Checking fine-tuning readiness...")
    readiness = manager.check_readiness(data_dir)

    print(f"📊 Readiness Status:")
    print(f"   Ready: {readiness['ready']}")
    print(f"   Approved count: {readiness.get('approved_count', 0)}")
    print(f"   Required minimum: {readiness.get('min_required', 100)}")

    if not readiness['ready']:
        print(f"   ⚠️ {readiness['reason']}")
        print("\n💡 Tip: 실제 프로젝트로 100개 이상의 원고를 수집한 후 다시 시도하세요.")
    else:
        print(f"   ✅ {readiness['message']}")

        # 비용 추정
        print("\n💰 Cost Estimation:")
        cost = manager.estimate_cost(readiness['approved_count'])
        print(f"   Training samples: {cost['total_training_samples']:,}")
        print(f"   Estimated cost: ${cost['estimated_cost_usd']:.2f} USD")
        print(f"                   {cost['estimated_cost_krw']:.0f}원")
        print(f"   Note: {cost['note']}")

    # 리포트 생성
    print("\n✅ Generating fine-tuning report...")
    report = manager.generate_fine_tuning_report(data_dir)
    print("\n" + "="*80)
    print(report)
    print("="*80)

    return True


def test_rlhf_collection():
    """4. RLHF 데이터 수집 테스트"""
    print_section("4️⃣ RLHF Collection System Test")

    project_name = "test_project"
    collector = RLHFCollector(project_name)

    # 샘플 피드백 수집
    print("✅ Collecting sample feedback...")
    collector.collect_feedback(
        ep_num=1,
        manuscript="테스트 원고입니다. " * 500,
        ai_score=75,
        human_score=80,
        human_feedback="AI보다 감정선이 더 자연스럽다고 느꼈습니다.",
        human_decision="APPROVE"
    )

    collector.collect_feedback(
        ep_num=2,
        manuscript="테스트 원고입니다. " * 500,
        ai_score=85,
        human_score=78,
        human_feedback="AI가 상업성을 과대평가한 것 같습니다.",
        human_decision="APPROVE"
    )

    # 불일치 분석
    print("\n✅ Analyzing AI vs Human disagreement...")
    analysis = collector.analyze_disagreement()

    if 'error' not in analysis:
        print(f"📊 Disagreement Analysis:")
        print(f"   Total feedback: {analysis['total_feedback']}")
        print(f"   Agreement rate: {analysis['agreement_rate']:.1%}")
        print(f"   Avg score difference: {analysis['avg_score_difference']:+.1f}")
        print(f"   AI overestimated: {analysis['overestimated_count']} cases")
        print(f"   AI underestimated: {analysis['underestimated_count']} cases")

        # RLHF 데이터 내보내기
        print("\n✅ Exporting RLHF training data...")
        filepath = collector.export_for_rlhf()
        print(f"💾 Exported to: {filepath}")
    else:
        print(f"⚠️ {analysis['error']}")

    return True


def run_integration_demo():
    """통합 데모 실행"""
    print("\n" + "🚀"*40)
    print("  PHASE 3 SYSTEMS INTEGRATION TEST")
    print("  All Systems Operational Check")
    print("🚀"*40 + "\n")

    results = []

    try:
        results.append(("Data Collection", test_data_collection()))
    except Exception as e:
        print(f"❌ Data Collection test failed: {e}")
        results.append(("Data Collection", False))

    try:
        results.append(("Prompt Optimization", test_prompt_optimization()))
    except Exception as e:
        print(f"❌ Prompt Optimization test failed: {e}")
        results.append(("Prompt Optimization", False))

    try:
        results.append(("Fine-tuning Automation", test_finetuning_automation()))
    except Exception as e:
        print(f"❌ Fine-tuning Automation test failed: {e}")
        results.append(("Fine-tuning Automation", False))

    try:
        results.append(("RLHF Collection", test_rlhf_collection()))
    except Exception as e:
        print(f"❌ RLHF Collection test failed: {e}")
        results.append(("RLHF Collection", False))

    # 결과 요약
    print_section("📊 Test Results Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 All Phase 3 systems are operational!")
        print("\n📋 Next Steps:")
        print("   1. Run dashboard: streamlit run performance_dashboard.py")
        print("   2. Run RLHF interface: streamlit run rlhf_interface.py")
        print("   3. Collect 100+ manuscripts with actual project")
        print("   4. Prepare fine-tuning dataset")
        print("   5. Train custom Gemini model")
    else:
        print("\n⚠️ Some tests failed. Review errors above.")

    return passed == total


if __name__ == "__main__":
    try:
        success = run_integration_demo()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
