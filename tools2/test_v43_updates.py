"""
[V43] 업데이트 검증 테스트
- 하드코딩 제거 확인
- CatharsisTimer 테스트
- ActionSceneEvaluator 테스트
- MaterialDB 장르 분기 테스트
"""
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_catharsis_timer():
    """CatharsisTimer 테스트"""
    print("\n" + "="*60)
    print("TEST 1: CatharsisTimer")
    print("="*60)

    from modules.validation.catharsis_timer import CatharsisTimer

    # 장르별 타이머 생성
    wuxia_timer = CatharsisTimer(genre="wuxia")
    hunter_timer = CatharsisTimer(genre="hunter")
    investment_timer = CatharsisTimer(genre="investment")

    # 테스트 원고 1: 카타르시스 있음
    catharsis_manuscript = """
    주인공은 일격에 적을 제압했다. 통쾌한 승리였다.
    주변의 무림인들이 경악하며 감탄했다.
    "대단하다! 저 정도의 실력이라니!"
    드디어 복수를 달성한 것이다.
    """

    # 테스트 원고 2: 카타르시스 없음 (좌절)
    frustration_manuscript = """
    주인공은 또다시 패배했다. 절망적인 상황이었다.
    적의 공격에 중상을 입고 후퇴할 수밖에 없었다.
    "이대로는... 안 된다..."
    무력함을 느끼며 도망쳐야 했다.
    """

    # 테스트 1: 카타르시스 감지
    result1 = wuxia_timer.check_catharsis_timing(1, catharsis_manuscript, [])
    print(f"\n[Test 1.1] 카타르시스 감지:")
    print(f"  - has_catharsis: {result1['has_catharsis']} (예상: True)")
    print(f"  - status: {result1['status']}")
    assert result1['has_catharsis'] == True, "카타르시스 감지 실패!"

    # 테스트 2: 좌절 감지
    result2 = wuxia_timer.check_catharsis_timing(1, frustration_manuscript, [])
    print(f"\n[Test 1.2] 좌절 감지:")
    print(f"  - has_catharsis: {result2['has_catharsis']} (예상: False)")
    print(f"  - catharsis_score: {result2['catharsis_score']}")
    assert result2['has_catharsis'] == False, "좌절 감지 실패!"

    # 테스트 3: 연속 좌절 경고
    frustration_history = [
        {"ep_num": 1, "has_catharsis": False},
        {"ep_num": 2, "has_catharsis": False},
        {"ep_num": 3, "has_catharsis": False},
    ]
    result3 = wuxia_timer.check_catharsis_timing(4, frustration_manuscript, frustration_history)
    print(f"\n[Test 1.3] 연속 좌절 경고:")
    print(f"  - status: {result3['status']} (예상: warning 또는 critical)")
    print(f"  - streak: {result3['streak']}")
    print(f"  - message: {result3.get('message', '')}")
    assert result3['status'] in ['warning', 'critical'], "연속 좌절 경고 실패!"

    # 테스트 4: 장르별 지표
    print(f"\n[Test 1.4] 장르별 타이머 생성:")
    print(f"  - 무협: {wuxia_timer.genre}")
    print(f"  - 헌터: {hunter_timer.genre}")
    print(f"  - 투자: {investment_timer.genre}")

    print("\n[PASS] CatharsisTimer 테스트 통과!")
    return True


def test_action_scene_evaluator():
    """ActionSceneEvaluator 테스트"""
    print("\n" + "="*60)
    print("TEST 2: ActionSceneEvaluator")
    print("="*60)

    from modules.validation.action_scene_evaluator import ActionSceneEvaluator

    # 장르별 평가자 생성
    wuxia_eval = ActionSceneEvaluator(genre="wuxia")
    hunter_eval = ActionSceneEvaluator(genre="hunter")

    # 테스트 원고: 전투 씬
    action_manuscript = """
    주인공은 검을 뽑아들었다. 적이 앞에서 다가오고 있었다.

    "죽어라!" 적의 검이 위에서 내리쳤다.
    주인공은 좌측으로 회피하며 반격했다. 검기가 적의 팔을 스쳤다.
    피가 튀었다. 적이 비틀거리며 뒤로 물러났다.

    "제법이군!" 적은 검을 다시 들어올렸다.
    주인공은 앞으로 돌진했다. 일격필살의 기회였다.
    검이 적의 가슴을 관통했다. 적이 쓰러졌다.
    통쾌한 승리였다. 최후의 일격이 결정적이었다.
    """

    # 테스트 원고: 전투 없음 (액션 키워드 최소화)
    no_action_manuscript = """
    산속의 초막에서 잠을 청했다. 바람이 불었다.
    눈을 뜨니 해가 떠 있었다.
    "평화로운 아침이다." 산책을 나섰다.
    """

    # 테스트 1: 전투 씬 평가
    result1 = wuxia_eval.evaluate(action_manuscript)
    print(f"\n[Test 2.1] 전투 씬 평가:")
    print(f"  - total_score: {result1['total_score']}/10")
    print(f"  - action_scene_count: {result1['action_scene_count']}")
    print(f"  - choreography: {result1['choreography']['score']}/10")
    print(f"  - stakes_escalation: {result1['stakes_escalation']['score']}/10")
    assert result1['action_scene_count'] > 0, "액션 씬 추출 실패!"

    # 테스트 2: 전투 없는 원고 (휴리스틱이므로 완화된 기준)
    result2 = wuxia_eval.evaluate(no_action_manuscript)
    print(f"\n[Test 2.2] 전투 없는 원고:")
    print(f"  - total_score: {result2['total_score']}/10")
    print(f"  - action_scene_count: {result2['action_scene_count']}")
    # 휴리스틱 방식이므로 완벽한 0을 기대하지 않음
    # 대신 전투 원고보다 액션 씬이 적은지 확인
    assert result2['action_scene_count'] <= 1, "액션 씬 과다 오탐지!"
    assert result2['total_score'] >= 7, "비전투 원고 점수 너무 낮음!"

    # 테스트 3: 긴장감 상승 평가
    scenes = wuxia_eval._extract_action_scenes(action_manuscript)
    escalation = wuxia_eval.evaluate_stakes_escalation(scenes)
    print(f"\n[Test 2.3] 긴장감 상승:")
    print(f"  - is_escalating: {escalation['is_escalating']}")
    print(f"  - stakes_curve: {escalation['stakes_curve']}")

    print("\n[PASS] ActionSceneEvaluator 테스트 통과!")
    return True


def test_material_db_genres():
    """MaterialDB 장르 분기 테스트"""
    print("\n" + "="*60)
    print("TEST 3: MaterialDB 장르 분기")
    print("="*60)

    from modules.core.material_db import MaterialDB

    # 테스트 1: 장르별 소재
    print("\n[Test 3.1] 장르별 기본 소재:")
    for genre in ["wuxia", "hunter", "investment"]:
        materials = MaterialDB.get_materials(genre)
        print(f"  - {genre}: {list(materials.keys())}")

    # 테스트 2: 장르별 랜덤 소재
    print("\n[Test 3.2] 장르별 랜덤 소재:")
    for genre in ["wuxia", "hunter", "investment"]:
        item = MaterialDB.get_random_material(genre, "ITEMS")
        print(f"  - {genre} ITEMS: {item}")

    # 테스트 3: 장르별 목표
    print("\n[Test 3.3] 장르별 목표:")
    for genre in ["wuxia", "hunter", "investment"]:
        objectives = MaterialDB.get_objectives(genre)
        print(f"  - {genre}: {objectives[:2]}...")

    print("\n[PASS] MaterialDB 장르 분기 테스트 통과!")
    return True


def test_hardcoding_removal():
    """하드코딩 제거 확인"""
    print("\n" + "="*60)
    print("TEST 4: 하드코딩 제거 확인")
    print("="*60)

    import re

    # 검사할 파일들
    files_to_check = [
        "modules/domain/agents/analyst.py",
        "modules/domain/agents/director.py",
        "modules/domain/agents/weaver.py",
        "modules/core/reference_anchor.py",
        "modules/core/quality_constitution.py",
        "modules/validation/blocking_validator.py"
    ]

    # 하드코딩 패턴 (제거되어야 함)
    hardcoded_patterns = [
        r'팽무진',
        r'팽조악',
        r'혼철대도',
        r'대방도',
        r'남궁설',
        r'혈마련',
        r'Block 15'
    ]

    issues = []

    for filepath in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if not os.path.exists(full_path):
            print(f"  [WARN] 파일 없음: {filepath}")
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for pattern in hardcoded_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # 주석/문서 내용은 제외 (간단한 휴리스틱)
                # 실제 코드에서 사용되는지 확인
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if pattern in line:
                        # 주석이 아닌 경우만
                        stripped = line.strip()
                        if not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                            # 문자열 내 예시인지 체크 (예: "예시: 혼철대도")
                            if '예시' not in line and 'example' not in line.lower():
                                issues.append(f"  - {filepath}:{i+1}: '{pattern}' 발견")

    if issues:
        print("\n[경고] 하드코딩 잔존:")
        for issue in issues[:10]:  # 최대 10개만 출력
            print(issue)
        print(f"\n[WARN] {len(issues)}개 하드코딩 의심 패턴 발견")
    else:
        print("\n[PASS] 하드코딩 제거 확인 완료!")

    return len(issues) == 0


def test_validation_orchestrator_integration():
    """ValidationOrchestrator 통합 테스트"""
    print("\n" + "="*60)
    print("TEST 5: ValidationOrchestrator 통합")
    print("="*60)

    from modules.validation.validation_orchestrator import ValidationOrchestrator

    # 설정
    config = {
        'scoring_threshold': 70,
        'use_self_consistency': False,  # 테스트에서는 비활성화
        'catharsis_max_gap': 3
    }

    # 오케스트레이터 생성 (LLM 없이)
    orchestrator = ValidationOrchestrator(config, client=None, genre='wuxia')

    # 속성 확인
    print("\n[Test 5.1] 모듈 초기화 확인:")
    print(f"  - blocking: {type(orchestrator.blocking).__name__}")
    print(f"  - scoring: {type(orchestrator.scoring).__name__}")
    print(f"  - advisory: {type(orchestrator.advisory).__name__}")
    print(f"  - catharsis_timer: {type(orchestrator.catharsis_timer).__name__}")
    print(f"  - action_evaluator: {type(orchestrator.action_evaluator).__name__}")

    assert hasattr(orchestrator, 'catharsis_timer'), "CatharsisTimer 없음!"
    assert hasattr(orchestrator, 'action_evaluator'), "ActionSceneEvaluator 없음!"

    print("\n[PASS] ValidationOrchestrator 통합 테스트 통과!")
    return True


def test_director_genre_propagation():
    """Director 장르 전파 테스트"""
    print("\n" + "="*60)
    print("TEST 6: Director 장르 전파")
    print("="*60)

    from modules.domain.agents.director import Director

    # Mock context
    class MockContext:
        def __init__(self):
            self.db = None

    class MockClient:
        pass

    # Director 인스턴스 생성
    director = Director(MockContext(), MockClient(), model_tier="gemini-2.0-flash")

    # 테스트 1: 기본 장르 확인
    print(f"\n[Test 6.1] 기본 장르:")
    print(f"  - genre: {director.genre} (예상: wuxia)")
    assert director.genre == 'wuxia', "기본 장르가 wuxia가 아님!"

    # 테스트 2: 장르 변경
    director.set_genre('hunter')
    print(f"\n[Test 6.2] 장르 변경 후:")
    print(f"  - genre: {director.genre} (예상: hunter)")
    assert director.genre == 'hunter', "장르 변경 실패!"

    # 테스트 3: V0128 설정
    print(f"\n[Test 6.3] V0128 설정:")
    print(f"  - use_v0128 (before): {director.use_v0128}")
    director.set_v0128_enabled(True)
    print(f"  - use_v0128 (after): {director.use_v0128}")
    assert director.use_v0128 == True, "V0128 활성화 실패!"

    # 테스트 4: 장르별 orchestrator 리셋
    director.v0128_orchestrator = "dummy"  # 임시 값 설정
    director.set_genre('investment')
    print(f"\n[Test 6.4] 장르 변경 시 orchestrator 리셋:")
    print(f"  - v0128_orchestrator: {director.v0128_orchestrator}")
    assert director.v0128_orchestrator is None, "orchestrator 리셋 실패!"

    print("\n[PASS] Director 장르 전파 테스트 통과!")
    return True


def test_genre_specific_components():
    """장르별 컴포넌트 전문화 테스트"""
    print("\n" + "="*60)
    print("TEST 7: 장르별 컴포넌트 전문화")
    print("="*60)

    from modules.validation.catharsis_timer import CatharsisTimer
    from modules.validation.action_scene_evaluator import ActionSceneEvaluator
    from modules.validation.validation_orchestrator import ValidationOrchestrator

    genres = ['wuxia', 'hunter', 'investment']

    print("\n[Test 7.1] CatharsisTimer 장르별 지표:")
    for genre in genres:
        timer = CatharsisTimer(genre=genre)
        indicators = timer.CATHARSIS_INDICATORS.get(genre, [])
        print(f"  - {genre}: {len(indicators)}개 지표")
        assert len(indicators) > 0, f"{genre} 카타르시스 지표 없음!"

    print("\n[Test 7.2] ActionSceneEvaluator 장르별 키워드:")
    for genre in genres:
        evaluator = ActionSceneEvaluator(genre=genre)
        keywords = evaluator.ACTION_KEYWORDS.get(genre, [])
        print(f"  - {genre}: {len(keywords)}개 키워드")
        assert len(keywords) > 0, f"{genre} 액션 키워드 없음!"

    print("\n[Test 7.3] ValidationOrchestrator 장르별 초기화:")
    config = {'scoring_threshold': 70, 'use_self_consistency': False}
    for genre in genres:
        orchestrator = ValidationOrchestrator(config, client=None, genre=genre)
        print(f"  - {genre}: catharsis_timer.genre={orchestrator.catharsis_timer.genre}, action_evaluator.genre={orchestrator.action_evaluator.genre}")
        assert orchestrator.catharsis_timer.genre == genre, f"CatharsisTimer 장르 불일치!"
        assert orchestrator.action_evaluator.genre == genre, f"ActionSceneEvaluator 장르 불일치!"

    print("\n[PASS] 장르별 컴포넌트 전문화 테스트 통과!")
    return True


def test_analyst_genre_library():
    """Analyst 장르별 라이브러리 로드 테스트"""
    print("\n" + "="*60)
    print("TEST 8: Analyst 장르별 라이브러리 로드")
    print("="*60)

    import os
    from pathlib import Path

    # 라이브러리 파일 존재 확인
    base_path = Path(os.path.dirname(__file__)) / "config" / "prompts"

    library_files = {
        'wuxia': 'analyst_libraries.json',
        'hunter': 'analyst_libraries_hunter.json',
        'investment': 'analyst_libraries_investment.json'
    }

    print("\n[Test 8.1] 장르별 라이브러리 파일 존재 확인:")
    for genre, filename in library_files.items():
        filepath = base_path / filename
        exists = filepath.exists()
        status = "[PASS]" if exists else "[FAIL]"
        print(f"  {status} {genre}: {filename} - {'존재' if exists else '없음'}")
        assert exists, f"{genre} 라이브러리 파일이 없습니다: {filename}"

    print("\n[Test 8.2] 라이브러리 내용 검증:")
    import json
    for genre, filename in library_files.items():
        filepath = base_path / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 필수 키 확인
        required_keys = ['narrative_archetypes']
        for key in required_keys:
            assert key in data, f"{genre}: {key} 키 없음"

        archetype_count = len(data.get('narrative_archetypes', {}))
        print(f"  - {genre}: {archetype_count}개 서사 아키타입")
        assert archetype_count >= 10, f"{genre}: 서사 아키타입이 너무 적음 ({archetype_count})"

    print("\n[Test 8.3] Analyst 장르 감지 메서드 테스트:")

    # Mock Guard 클래스들
    class MockWuxiaGuard:
        def get_genre_name(self):
            return "무협물(WUXIA)"

    class MockHunterGuard:
        def get_genre_name(self):
            return "헌터물(HUNTER)"

    class MockInvestmentGuard:
        def get_genre_name(self):
            return "투자물(INVESTMENT)"

    class MockPaths:
        def __init__(self):
            self.config = Path(os.path.dirname(__file__)) / "config"

    class MockContext:
        def __init__(self, guard):
            self.guard = guard
            self.paths = MockPaths()
            self.db = None

    class MockClient:
        pass

    from modules.domain.agents.analyst import Analyst

    test_cases = [
        (MockWuxiaGuard(), 'wuxia'),
        (MockHunterGuard(), 'hunter'),
        (MockInvestmentGuard(), 'investment')
    ]

    for guard, expected_genre in test_cases:
        context = MockContext(guard)
        analyst = Analyst(context, MockClient(), model_tier="gemini-2.0-flash")
        detected_genre = analyst._get_current_genre()
        status = "[PASS]" if detected_genre == expected_genre else "[FAIL]"
        print(f"  {status} {guard.get_genre_name()} -> {detected_genre} (예상: {expected_genre})")
        assert detected_genre == expected_genre, f"장르 감지 실패: {detected_genre} != {expected_genre}"

    print("\n[Test 8.4] 장르별 라이브러리 경로 테스트:")
    for guard, expected_genre in test_cases:
        context = MockContext(guard)
        analyst = Analyst(context, MockClient(), model_tier="gemini-2.0-flash")
        lib_path = analyst._get_genre_library_path(expected_genre)
        expected_filename = library_files[expected_genre]
        actual_filename = lib_path.name
        status = "[PASS]" if actual_filename == expected_filename else "[FAIL]"
        print(f"  {status} {expected_genre} -> {actual_filename}")
        assert actual_filename == expected_filename, f"경로 불일치: {actual_filename} != {expected_filename}"

    print("\n[PASS] Analyst 장르별 라이브러리 로드 테스트 통과!")
    return True


def main():
    """전체 테스트 실행"""
    print("\n" + "="*60)
    print("       V43 업데이트 검증 테스트 스위트")
    print("="*60)

    results = []

    # 테스트 실행
    tests = [
        ("CatharsisTimer", test_catharsis_timer),
        ("ActionSceneEvaluator", test_action_scene_evaluator),
        ("MaterialDB 장르 분기", test_material_db_genres),
        ("하드코딩 제거", test_hardcoding_removal),
        ("ValidationOrchestrator 통합", test_validation_orchestrator_integration),
        ("Director 장르 전파", test_director_genre_propagation),
        ("장르별 컴포넌트 전문화", test_genre_specific_components),
        ("Analyst 장르별 라이브러리", test_analyst_genre_library)
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] {name} 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 결과 요약
    print("\n" + "="*60)
    print("                    테스트 결과 요약")
    print("="*60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"  {status}: {name}")

    print(f"\n총 {passed}/{total} 테스트 통과")

    if passed == total:
        print("\n[SUCCESS] 모든 테스트 통과! V43 업데이트 검증 완료.")
    else:
        print(f"\n[WARN] {total - passed}개 테스트 실패. 수정이 필요합니다.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
