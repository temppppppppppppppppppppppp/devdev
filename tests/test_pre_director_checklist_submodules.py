"""[R5-2c] PreDirectorChecklist submodule tests."""

from modules.core.pre_director_checklist import CheckSeverity, PreDirectorChecklist


def _long_paragraph(text: str) -> str:
    return (text + " ") * 30


class TestNarrativeChecker:
    def test_narrative_flow_normal(self):
        checker = PreDirectorChecklist()
        manuscript = "\n\n".join(
            [
                _long_paragraph("그는 새벽 안개를 가르며 천천히 걸었다"),
                _long_paragraph("시장 골목의 소음 속에서 단서를 차분히 확인했다"),
                _long_paragraph("문파의 표식을 본 그는 경계를 늦추지 않았다"),
                _long_paragraph("해질 무렵 그는 다음 단서를 정리하며 숨을 골랐다"),
            ]
        )

        items = checker.narrative_checker._check_narrative_flow(manuscript, {})

        assert isinstance(items, list)
        assert len(items) >= 1
        assert any(i.severity == CheckSeverity.PASS for i in items)

    def test_npc_behavior_jump_no_context_safe(self):
        checker = PreDirectorChecklist()
        items = checker.narrative_checker._check_npc_behavior_jump("짧은 원고", {"blueprint": None})

        assert isinstance(items, list)

    def test_setting_keywords_dead_npc(self):
        checker = PreDirectorChecklist()
        manuscript = "무영이말했다. 그는 검을 쥐고 다시 앞으로 걸어갔다."
        items = checker.narrative_checker._check_setting_keywords(manuscript, {"dead_npcs": ["무영"]})

        assert any(i.severity in (CheckSeverity.WARNING, CheckSeverity.FAIL) for i in items)

    def test_setting_keywords_pass_when_empty(self):
        checker = PreDirectorChecklist()
        items = checker.narrative_checker._check_setting_keywords("평온한 저녁 공기가 골목에 내려앉았다.", {})

        assert any(i.severity == CheckSeverity.PASS for i in items)


class TestStyleChecker:
    def test_sentence_variety_pass(self):
        checker = PreDirectorChecklist()
        manuscript = (
            "새벽 공기가 차갑게 골목을 훑었다. "
            "문 앞의 등불은 마지막 기름을 태우며 흔들렸다. "
            "지붕 위 그림자는 느리게 미끄러졌다. "
            "멀리서 닭 우는 소리가 짧게 끊겼다. "
            "장터의 바닥은 밤새 내린 습기를 머금고 있었다."
        )

        items = checker.style_checker._check_sentence_variety(manuscript)

        assert len(items) >= 1
        assert any(i.severity == CheckSeverity.PASS for i in items)

    def test_sentence_variety_repetition(self):
        checker = PreDirectorChecklist()
        manuscript = (
            "그는 천천히 복도를 걸으며 벽면의 흔적을 살폈다. "
            "그는 잠긴 문을 밀어 보며 안쪽의 소리를 가늠했다. "
            "그는 숨을 고르고 그림자 흔들림을 끝까지 관찰했다. "
            "그는 다시 칼자루를 단단히 쥐고 자세를 가다듬었다. "
            "그는 끝내 어두운 계단 쪽으로 조심스럽게 전진했다."
        )

        items = checker.style_checker._check_sentence_variety(manuscript)

        assert any(i.severity in (CheckSeverity.WARNING, CheckSeverity.FAIL) for i in items)

    def test_pacing_rhythm_short_text(self):
        checker = PreDirectorChecklist()
        items = checker.style_checker._check_pacing_rhythm("짧은 텍스트")

        assert isinstance(items, list)
        assert len(items) == 0

    def test_pacing_rhythm_long_text(self):
        checker = PreDirectorChecklist()
        manuscript = ("그는 검을 뽑아 공격했다. " * 500) + ('"멈춰라." ' * 150)
        items = checker.style_checker._check_pacing_rhythm(manuscript)

        assert isinstance(items, list)
        assert len(items) >= 1


class TestIntegration:
    def test_check_manuscript_delegates(self):
        checker = PreDirectorChecklist()
        manuscript = ("가" * 5500) + "\n\n" + ("나" * 1200)
        result = checker.check(content=manuscript, content_type="manuscript", context={"blueprint": {}, "arc_data": {}})

        assert hasattr(result, "passed")
        assert isinstance(result.items, list)

    def test_lazy_init_narrative_and_style(self):
        checker = PreDirectorChecklist()
        assert checker._narrative_checker is None
        assert checker._style_checker is None

        _ = checker.narrative_checker
        _ = checker.style_checker

        assert checker._narrative_checker is not None
        assert checker._style_checker is not None

    def test_check_blueprint_still_works(self):
        checker = PreDirectorChecklist()
        blueprint = '{"integrated_scenario":"test","scene_breakdown":{"scene_1":{"description":"x"}}}'
        result = checker.check(content=blueprint, content_type="blueprint", context={})

        assert hasattr(result, "passed")
