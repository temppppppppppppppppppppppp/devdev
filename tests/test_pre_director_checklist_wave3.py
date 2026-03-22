from modules.core.pre_director_checklist import CheckCategory, CheckItem, CheckSeverity, PreDirectorChecklist


def _warning_item(name: str, category: CheckCategory) -> CheckItem:
    return CheckItem(
        category=category,
        name=name,
        passed=True,
        severity=CheckSeverity.WARNING,
        message=name,
    )


def test_check_manuscript_blueprint_alignment_handles_string_scene_breakdown():
    checker = PreDirectorChecklist()
    manuscript = ("평온한 거리와 잔잔한 대화가 이어졌다. " * 120) + "\n\n" + ("누군가는 침묵을 지켰다. " * 60)

    items = checker._check_manuscript_blueprint_alignment(
        manuscript,
        {
            "blueprint": {
                "scene_breakdown": "1: 전투\n2: 대화",
                "ending_hook": "적의 그림자",
            }
        },
    )

    assert any(item.name == "엔딩 훅" for item in items)
    assert all(item.name != "씬 반영" for item in items)


def test_check_manuscript_scope_warns_when_scene_budget_is_exceeded():
    checker = PreDirectorChecklist()

    items = checker._check_manuscript_scope(
        "가" * 2500,
        {
            "blueprint": {
                "scene_breakdown": {
                    "scene_1": {"description": "추적"},
                }
            }
        },
    )

    assert any(item.name == "범위 초과" and item.severity == CheckSeverity.WARNING for item in items)


def test_check_manuscript_prev_linkage_warns_on_low_overlap():
    checker = PreDirectorChecklist()
    prev_manuscript = ("붉은 증표와 닫힌 문이 마지막 장면에 남았다. " * 30) + ("그는 어둠을 바라보았다. " * 15)
    manuscript = ("새벽 광장에서 낯선 상인이 천천히 걸어왔다. " * 40) + "\n\n" + ("바람만이 골목을 스쳤다. " * 20)

    items = checker._check_manuscript_prev_linkage(manuscript, {"prev_manuscript": prev_manuscript})

    assert any(item.name == "직전 화 연결" and item.severity == CheckSeverity.WARNING for item in items)


def test_run_manuscript_quality_checks_aggregates_submodule_results():
    checker = PreDirectorChecklist()

    class FakeNarrativeChecker:
        def _check_narrative_flow(self, manuscript, context):
            return [_warning_item("narrative_flow", CheckCategory.NARRATIVE_FLOW)]

        def _check_npc_behavior_jump(self, manuscript, context):
            return [_warning_item("npc_behavior", CheckCategory.NPC_BEHAVIOR)]

        def _check_setting_keywords(self, manuscript, context):
            return [_warning_item("setting_keywords", CheckCategory.SETTING_KEYWORDS)]

    class FakeStyleChecker:
        def _check_sentence_variety(self, manuscript):
            return [_warning_item("sentence_variety", CheckCategory.SENTENCE_VARIETY)]

        def _check_pacing_rhythm(self, manuscript):
            return [_warning_item("pacing", CheckCategory.PACING)]

    class FakeManuscriptChecker:
        def _check_cliche_density(self, manuscript):
            return [_warning_item("cliche_density", CheckCategory.CLICHE_DENSITY)]

    checker._narrative_checker = FakeNarrativeChecker()
    checker._style_checker = FakeStyleChecker()
    checker._manuscript_checker = FakeManuscriptChecker()

    items = checker._run_manuscript_quality_checks("본문", {})

    assert [item.name for item in items] == [
        "narrative_flow",
        "npc_behavior",
        "sentence_variety",
        "pacing",
        "setting_keywords",
        "cliche_density",
    ]
