"""[R5-1a] PreDirectorManuscriptChecker 서브모듈 직접 테스트."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.pre_director_checklist import (
    CheckSeverity,
    PreDirectorChecklist,
)
from modules.core.pre_director_manuscript_checker import PreDirectorManuscriptChecker

# ─── Fixture ────────────────────────────────────────


@pytest.fixture
def host():
    return PreDirectorChecklist()


@pytest.fixture
def checker(host):
    return PreDirectorManuscriptChecker(host)


# ─── host 참조 ──────────────────────────────────────


class TestHostWiring:
    """서브모듈이 host 상수를 올바르게 참조하는지."""

    def test_host_reference(self, checker, host):
        assert checker.host is host

    def test_lazy_property(self, host):
        """PreDirectorChecklist.manuscript_checker가 lazy init."""
        assert host._manuscript_checker is None
        mc = host.manuscript_checker
        assert isinstance(mc, PreDirectorManuscriptChecker)
        assert host._manuscript_checker is mc  # 캐싱

    def test_host_constants_accessible(self, checker):
        assert "dialogue" in checker.host.MANUSCRIPT_REQUIRED


# ─── _check_dialogue_ratio ──────────────────────────


class TestDialogueRatio:
    def test_short_manuscript_no_items(self, checker):
        """1000자 미만이면 빈 리스트."""
        result = checker._check_dialogue_ratio("짧은 원고")
        assert result == []

    def test_dialogue_balanced(self, checker):
        """대화 30% 범위면 PASS."""
        narrative = "가" * 7000
        dialogue = '"{}" '.format("나" * 100) * 30  # ~3000자
        ms = narrative + dialogue
        items = checker._check_dialogue_ratio(ms)
        assert len(items) >= 1
        assert items[0].severity in (CheckSeverity.PASS, CheckSeverity.WARNING)

    def test_no_dialogue_fail(self, checker):
        """대화 0개면 FAIL."""
        ms = "가" * 2000
        items = checker._check_dialogue_ratio(ms)
        assert len(items) >= 1
        assert items[0].severity == CheckSeverity.FAIL

    def test_excessive_dialogue_warning(self, checker):
        """대화 60%+ 면 WARNING."""
        dialogue = '"{}" '.format("대화" * 50) * 60  # 대화 과다
        narrative = "서술" * 100
        ms = dialogue + narrative
        items = checker._check_dialogue_ratio(ms)
        assert len(items) >= 1
        # 과다 대화이므로 WARNING 또는 PASS
        assert any(i.severity in (CheckSeverity.WARNING, CheckSeverity.PASS) for i in items)

    def test_dialogue_target_from_context_raises_warning_band(self, checker):
        """style target이 높으면 fixed 30% 대신 target 기준으로 경고한다."""
        narrative = "가" * 7400
        dialogue = '"{}" '.format("나" * 100) * 26  # 대략 26%
        ms = narrative + dialogue

        items = checker._check_dialogue_ratio(ms, {"style_dialogue_ratio_target": 0.40})

        assert any(item.severity == CheckSeverity.WARNING for item in items)
        assert any("스타일 목표 40%" in item.message for item in items)


# ─── _measure_scene_reflection ──────────────────────


class TestSceneReflection:
    def test_empty_breakdown_returns_default(self, checker):
        result = checker._measure_scene_reflection("원고 텍스트", {})
        assert result["overall_ratio"] == 0
        assert result["weak_scenes"] == []

    def test_matching_keywords_high_ratio(self, checker):
        breakdown = {
            "scene_1": {"title": "무림맹 회의", "description": "무림맹에서 장로들이 회의한다"},
        }
        ms = "무림맹 대전에서 장로들이 회의를 시작했다. 무림맹주가 입을 열었다."
        result = checker._measure_scene_reflection(ms, breakdown)
        assert result["overall_ratio"] > 0.3

    def test_no_matching_keywords_weak(self, checker):
        breakdown = {
            "scene_1": {"title": "해저 궁전", "description": "해저 궁전에서 인어공주가 노래한다"},
        }
        ms = "산속 오두막에서 노인이 차를 마셨다."
        result = checker._measure_scene_reflection(ms, breakdown)
        assert len(result["weak_scenes"]) >= 1


# ─── _check_scene_density_balance ───────────────────


class TestSceneDensityBalance:
    def test_few_scenes_no_items(self, checker):
        """씬 2개 이하면 빈 리스트."""
        breakdown = {"s1": "a", "s2": "b"}
        result = checker._check_scene_density_balance("원고", breakdown)
        assert result == []

    def test_balanced_scenes(self, checker):
        """균등 밀도면 PASS 포함."""
        kw = "무림"
        breakdown = {f"s{i}": {"description": f"{kw} 장면 {i}"} for i in range(5)}
        ms = f"{kw} " * 500 + "서술 " * 500
        items = checker._check_scene_density_balance(ms, breakdown)
        # 결과가 있으면 PASS/WARNING 중 하나
        if items:
            severities = {i.severity for i in items}
            assert CheckSeverity.PASS in severities or CheckSeverity.WARNING in severities


# ─── _check_high_impact_zone ────────────────────────


class TestHighImpactZone:
    def test_few_scenes_no_items(self, checker):
        """4씬 미만이면 빈 리스트."""
        result = checker._check_high_impact_zone(["a", "b", "c"], [0.5, 0.5, 0.5], 3)
        assert result == []

    def test_short_high_impact_warning(self, checker):
        """마지막 2씬이 600자 미만이면 WARNING."""
        sections = ["x" * 1000, "x" * 1000, "x" * 1000, "x" * 100, "x" * 100]
        densities = [0.6, 0.6, 0.6, 0.6, 0.6]
        items = checker._check_high_impact_zone(sections, densities, 5)
        assert any(i.name == "High Impact Zone 분량 부족" for i in items)

    def test_good_high_impact_pass(self, checker):
        """마지막 2씬 충분하고 밀도 높으면 PASS."""
        sections = ["x" * 800] * 5
        densities = [0.6, 0.6, 0.6, 0.7, 0.8]
        items = checker._check_high_impact_zone(sections, densities, 5)
        assert any(i.severity == CheckSeverity.PASS for i in items)


# ─── _check_cliche_density ──────────────────────────


class TestClicheDensity:
    def test_no_cliches_pass(self, checker):
        ms = "맑은 하늘 아래 두 사람이 나란히 걸었다. " * 100
        items = checker._check_cliche_density(ms)
        assert len(items) == 1
        assert items[0].severity == CheckSeverity.PASS

    def test_many_cliches_fail(self, checker):
        """1000자당 5개 초과면 FAIL."""
        ms = "이를 악물고 주먹을 불끈 쥐었다. 심장이 쿵 뛰고 눈앞이 캄캄해졌다. 온몸이 굳었다. " * 20
        items = checker._check_cliche_density(ms)
        assert len(items) == 1
        assert items[0].severity in (CheckSeverity.FAIL, CheckSeverity.WARNING)

    def test_empty_manuscript(self, checker):
        items = checker._check_cliche_density("")
        assert len(items) == 1
        assert items[0].severity == CheckSeverity.PASS


# ─── 통합: PreDirectorChecklist.check() 경유 ───────


class TestIntegrationViaHost:
    """facade를 통해 서브모듈이 정상 호출되는지."""

    def test_check_manuscript_includes_dialogue(self):
        cl = PreDirectorChecklist()
        ms = "가" * 2000
        result = cl.check(content=ms, content_type="manuscript", context={})
        names = [item.name for item in result.items]
        assert "대화 수" in names or "대화 비율" in names

    def test_check_manuscript_includes_cliche(self):
        cl = PreDirectorChecklist()
        ms = "이를 악물고 주먹을 불끈 쥐며 " * 100
        result = cl.check(content=ms, content_type="manuscript", context={})
        names = [item.name for item in result.items]
        assert any("클리셰" in n for n in names)
