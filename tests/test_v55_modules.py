"""
[V55.3] V55 모듈 통합 테스트
자동화 테스트로 시스템 안정성 검증

실행: python -m pytest tests/test_v55_modules.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_blueprint():
    """샘플 블루프린트"""
    return {
        "ep_num": 10,
        "scene_breakdown": {
            "scene_1": {"description": "오프닝 - 직전 화 연결", "characters": ["주인공"]},
            "scene_2": {"description": "긴장 상승 - 적 조우", "characters": ["주인공", "적"]},
            "scene_3": {"description": "대결 - 검술 격돌", "characters": ["주인공", "적"]},
            "scene_4": {"description": "반전 - 정체 발각", "characters": ["주인공"]},
            "scene_5": {"description": "클리프행어 - 위기 상황", "characters": ["주인공"]},
        },
        "ending_hook": "독이 퍼지기 시작했다. 해독제가 필요하다.",
        "protagonist_state": {"inventory": ["검", "은자 10냥", "해독단"]},
    }


@pytest.fixture
def sample_arc():
    """샘플 Arc 데이터"""
    return {
        "arc_no": 5,
        "tactical_doc": "제1화: 청풍검각 도착...",
        "joint_docs": {
            "final_location": "청풍검각",
            "physical_inventory": ["백근대도", "철혈사자패"],
            "world_joint": "무림맹 소집 공지",
        },
        "state_constraints": {"items_acquired": ["백근대도"], "grants_received": ["철혈사자패"]},
    }


@pytest.fixture
def sample_manuscript():
    """샘플 원고 (5000자)"""
    return (
        """
    청풍검각의 아침 안개가 자욱했다. 강호의 고수들이 모여드는 이 곳에서
    주인공은 새로운 임무를 맡게 되었다...
    """
        * 50
    )  # 약 5000자


# ═══════════════════════════════════════════════════════════════════════════════
# ConstitutionalChecker Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestConstitutionalChecker:
    """Constitutional Checker 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from modules.core.constitutional_checker import ConstitutionalChecker

        checker = ConstitutionalChecker(genre="wuxia")
        assert checker is not None
        assert checker.genre == "wuxia"

    def test_arc_constitution(self, sample_arc):
        """Arc 헌법 프롬프트 생성 테스트"""
        from modules.core.constitutional_checker import ConstitutionalChecker

        checker = ConstitutionalChecker(genre="wuxia")

        prompt = checker.get_analyst_constitution(prev_arcs=[sample_arc], additional_constraints="테스트 제약")

        assert "Constitutional Self-Check" in prompt
        assert "Arc 설계" in prompt
        assert "백근대도" in prompt  # 이전 획득 아이템
        assert "철혈사자패" in prompt  # 이전 수여물

    def test_blueprint_constitution(self, sample_blueprint):
        """Blueprint 헌법 프롬프트 생성 테스트"""
        from modules.core.constitutional_checker import ConstitutionalChecker

        checker = ConstitutionalChecker(genre="wuxia")

        prompt = checker.get_architect_constitution(
            prev_blueprint=sample_blueprint, arc_data={"tactical_doc": "테스트 전술"}
        )

        assert "Blueprint 설계" in prompt
        assert "독이 퍼지기" in prompt  # ending_hook

    def test_manuscript_constitution(self, sample_blueprint):
        """Manuscript 헌법 프롬프트 생성 테스트"""
        from modules.core.constitutional_checker import ConstitutionalChecker

        checker = ConstitutionalChecker(genre="wuxia")

        prompt = checker.get_writer_constitution(
            blueprint=sample_blueprint, prev_manuscript="직전 화 마지막...", inventory=["검", "은자"]
        )

        assert "원고 작성" in prompt
        assert "검" in prompt  # 소지품

    def test_reject_examples(self):
        """REJECT 예시 생성 테스트"""
        from modules.core.constitutional_checker import ConstitutionalChecker

        checker = ConstitutionalChecker(genre="wuxia")

        for stage in [2, 3, 4]:
            examples = checker.get_reject_examples(stage)
            assert "❌" in examples
            assert "✅" in examples

    def test_full_injection(self, sample_arc):
        """전체 주입 프롬프트 테스트"""
        from modules.core.constitutional_checker import ConstitutionalChecker

        checker = ConstitutionalChecker(genre="wuxia")

        full = checker.get_full_injection(stage=2, context={"prev_arcs": [sample_arc]})

        assert "Constitutional Self-Check" in full
        assert "REJECT 사례" in full


# ═══════════════════════════════════════════════════════════════════════════════
# WriterTemplate Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestWriterTemplate:
    """Writer Template 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from modules.core.writer_template import WriterTemplate

        template = WriterTemplate(genre="wuxia")
        assert template is not None

    def test_generate_template(self, sample_blueprint):
        """템플릿 생성 테스트"""
        from modules.core.writer_template import WriterTemplate

        wt = WriterTemplate(genre="wuxia")

        template = wt.generate_template(blueprint=sample_blueprint, prev_ending="직전 화 마지막...")

        assert template.ep_num == 10
        assert template.total_scenes == 5
        assert len(template.slots) == 5
        assert template.total_min_chars >= 4000

    def test_slot_types(self, sample_blueprint):
        """씬 타입 추론 테스트"""
        from modules.core.writer_template import SceneType, WriterTemplate

        wt = WriterTemplate(genre="wuxia")

        template = wt.generate_template(sample_blueprint)

        # 첫 씬은 OPENING
        assert template.slots[0].scene_type == SceneType.OPENING
        # 마지막 씬은 CLIFFHANGER
        assert template.slots[-1].scene_type == SceneType.CLIFFHANGER

    def test_prompt_injection(self, sample_blueprint):
        """프롬프트 주입 생성 테스트"""
        from modules.core.writer_template import WriterTemplate

        wt = WriterTemplate(genre="wuxia")

        template = wt.generate_template(sample_blueprint)
        injection = wt.generate_prompt_injection(template)

        assert "Writer Template" in injection
        assert "씬별 작성 가이드" in injection
        assert "scene_1" in injection

    def test_validation(self, sample_blueprint, sample_manuscript):
        """템플릿 검증 테스트"""
        from modules.core.writer_template import WriterTemplate

        wt = WriterTemplate(genre="wuxia")

        template = wt.generate_template(sample_blueprint)
        result = wt.validate_against_template(sample_manuscript, template)

        assert "passed" in result
        assert "length" in result
        assert "scene_coverage" in result


# ═══════════════════════════════════════════════════════════════════════════════
# PassRateMonitor Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPassRateMonitor:
    """Pass Rate Monitor 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from modules.core.pass_rate_monitor import PassRateMonitor

        monitor = PassRateMonitor()
        assert monitor is not None

    def test_record_attempt(self, tmp_path):
        """시도 기록 테스트"""
        from modules.core.pass_rate_monitor import PassRateMonitor

        monitor = PassRateMonitor(str(tmp_path))

        monitor.record_attempt(stage=4, episode=10, attempt_num=1, success=True)

        assert len(monitor.records) == 1
        assert monitor.records[0].stage == 4
        assert monitor.records[0].success == True

    def test_stage_stats(self, tmp_path):
        """Stage 통계 테스트"""
        from modules.core.pass_rate_monitor import PassRateMonitor

        monitor = PassRateMonitor(str(tmp_path))

        # 테스트 데이터 추가
        for i in range(10):
            monitor.record_attempt(
                stage=4,
                episode=i,
                attempt_num=1,
                success=(i % 2 == 0),  # 50% 통과
            )

        stats = monitor.get_stage_stats(4)

        assert stats.total_attempts == 10
        assert stats.first_attempt_rate == 0.5

    def test_summary(self, tmp_path):
        """요약 생성 테스트"""
        from modules.core.pass_rate_monitor import PassRateMonitor

        monitor = PassRateMonitor(str(tmp_path))

        # 테스트 데이터
        for stage in [2, 3, 4]:
            for i in range(5):
                monitor.record_attempt(stage=stage, episode=i, attempt_num=1, success=True)

        summary = monitor.get_summary(recent_n=20)

        assert "Pass Rate Monitor" in summary
        assert "Stage" in summary


# ═══════════════════════════════════════════════════════════════════════════════
# TreeOfThoughts Tests (4분기)
# ═══════════════════════════════════════════════════════════════════════════════


class TestTreeOfThoughts:
    """Tree of Thoughts 테스트"""

    def test_arc_approaches_count(self):
        """Arc 접근 방식 4개 확인"""
        # 클래스 내부의 arc_approaches 확인
        # (explore_arc 메서드 내부이므로 직접 확인 어려움)
        # 대신 파일에서 직접 확인
        import re

        with open("modules/core/tree_of_thoughts.py", encoding="utf-8") as f:
            content = f.read()

        # arc_approaches 정의 부분 찾기
        match = re.search(r"arc_approaches = \[(.*?)\]", content, re.DOTALL)
        if match:
            approaches_str = match.group(1)
            # "name" 키 개수로 접근 방식 수 확인
            count = approaches_str.count('"name"')
            assert count == 4, f"Expected 4 arc approaches, got {count}"

    def test_blueprint_approaches_count(self):
        """Blueprint 접근 방식 4개 확인"""
        import re

        with open("modules/core/tree_of_thoughts.py", encoding="utf-8") as f:
            content = f.read()

        # blueprint_approaches 정의 부분 찾기
        match = re.search(r"blueprint_approaches = \[(.*?)\]", content, re.DOTALL)
        if match:
            approaches_str = match.group(1)
            count = approaches_str.count('"name"')
            assert count == 4, f"Expected 4 blueprint approaches, got {count}"


# ═══════════════════════════════════════════════════════════════════════════════
# ManuscriptEnhancer Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestManuscriptEnhancer:
    """Manuscript Enhancer 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from modules.core.manuscript_enhancer import ManuscriptEnhancer

        enhancer = ManuscriptEnhancer(genre="wuxia")
        assert enhancer is not None

    def test_analyze(self, sample_manuscript):
        """분석 테스트"""
        from modules.core.manuscript_enhancer import ManuscriptEnhancer

        enhancer = ManuscriptEnhancer(genre="wuxia")

        result = enhancer.analyze(sample_manuscript, current_ep=10)

        assert result is not None
        assert hasattr(result, "cliche_count")
        assert hasattr(result, "subtext_ratio")


# ═══════════════════════════════════════════════════════════════════════════════
# [V65] TwoPhaseArcGenerator 삭제됨 — TestTwoPhaseArcGenerator 클래스 제거


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestIntegration:
    """통합 테스트"""

    def test_all_v55_modules_importable(self):
        """V55 모든 모듈 임포트 가능 확인"""
        modules = [
            "modules.core.manuscript_enhancer",
            "modules.core.constitutional_checker",
            "modules.core.writer_template",
            "modules.core.pass_rate_monitor",
            # [V65] two_phase_generator 삭제됨
            "modules.core.tree_of_thoughts",
        ]

        for module_name in modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_main_a_imports(self):
        """main_a.py 임포트 의존성 확인"""
        # main_a.py의 try 블록 내 import 확인
        with open("main_a.py", encoding="utf-8") as f:
            content = f.read()

        required_imports = [
            "ConstitutionalChecker",
            # [V65] TwoPhaseArcGenerator 삭제됨
        ]

        for imp in required_imports:
            assert imp in content, f"Missing import: {imp}"


# ═══════════════════════════════════════════════════════════════════════════════
# Run Tests
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
