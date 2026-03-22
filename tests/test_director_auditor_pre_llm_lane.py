from unittest.mock import MagicMock

from modules.domain.agents.director_auditor import DirectorQualityAuditor


def _make_auditor():
    director = MagicMock()
    director.genre_validation_enabled = True
    director.guard = MagicMock()
    director.manuscript_history_check_enabled = True
    director.protagonist_config_check_enabled = True
    director.entity_consistency_enabled = True
    director._caching = MagicMock()
    director._caching.manuscript_cache_name = None
    director.check_manuscript_history_conflicts = MagicMock()
    director.check_manuscript_history_with_cache = MagicMock()
    director.validate_entity_consistency = MagicMock()
    return DirectorQualityAuditor(director)


def test_run_manuscript_pre_llm_checks_shell_coordinates_helper_family(monkeypatch):
    auditor = _make_auditor()
    validation_context = {"seed": "value"}

    monkeypatch.setattr(
        auditor,
        "_collect_dead_npc_pre_llm_warnings",
        lambda **kwargs: ["dead warning"],
    )
    monkeypatch.setattr(
        auditor,
        "_collect_genre_pre_llm_findings",
        lambda **kwargs: {"warnings": ["genre warning"], "advisories": ["genre advisory"]},
    )
    monkeypatch.setattr(
        auditor,
        "_apply_history_pre_llm_checks",
        lambda **kwargs: {"early_result": None, "validation_context": {"history": True}},
    )
    monkeypatch.setattr(
        auditor,
        "_apply_protagonist_config_pre_llm_checks",
        lambda **kwargs: {"warnings": ["config warning"], "validation_context": {"history": True, "config": True}},
    )
    monkeypatch.setattr(
        auditor,
        "_apply_entity_consistency_pre_llm_checks",
        lambda **kwargs: {"early_result": None, "validation_context": {"history": True, "config": True, "entity": True}},
    )
    monkeypatch.setattr(
        auditor,
        "_apply_character_logic_pre_llm_checks",
        lambda **kwargs: {"early_result": None},
    )

    result = auditor._run_manuscript_pre_llm_checks(
        ep_num=7,
        manuscript="body",
        arc_no=2,
        validation_context=validation_context,
        entity_registry={"npc": "A"},
        manuscript_history=[{"ep": 6}],
        state_tracker=MagicMock(),
    )

    assert result["early_result"] is None
    assert result["validation_context"] == {"history": True, "config": True, "entity": True}
    assert result["pre_llm_warnings"] == ["dead warning", "genre warning", "config warning"]
    assert result["pre_llm_advisories"] == ["genre advisory"]


def test_apply_history_pre_llm_checks_returns_conflict_reject():
    auditor = _make_auditor()
    auditor._d.check_manuscript_history_conflicts.return_value = {
        "decision": "CONFLICT",
        "conflicts": [{"type": "fact", "prev_fact": "A", "current_violation": "B"}],
        "summary": "conflict summary",
    }

    result = auditor._apply_history_pre_llm_checks(
        ep_num=3,
        manuscript="body",
        manuscript_history=[{"ep_num": 2, "summary": "old"}],
        validation_context=None,
    )

    assert result["early_result"]["decision"] == "REJECT"
    assert result["early_result"]["error_category"] == "LOGIC_ERROR"
    assert "A vs B" in result["early_result"]["reason"]


def test_apply_protagonist_config_pre_llm_checks_records_warning_context():
    auditor = _make_auditor()
    auditor.validate_protagonist_config_compliance = MagicMock(
        return_value={"decision": "WARNING", "violations": [{"field": "world_origin"}]}
    )

    result = auditor._apply_protagonist_config_pre_llm_checks(
        manuscript="body",
        ep_num=5,
        validation_context={"seed": "value"},
    )

    assert result["warnings"] == []
    assert result["validation_context"]["seed"] == "value"
    assert result["validation_context"]["v60_89_config_warnings"] == [{"field": "world_origin"}]


def test_apply_character_logic_pre_llm_checks_rejects_major_multi_violation():
    auditor = _make_auditor()
    auditor.assess_character_logic = MagicMock(
        return_value={
            "decision": "REJECT",
            "score": 41,
            "severity": "MAJOR",
            "violations": ["a", "b"],
            "feedback": "logic drift",
        }
    )

    result = auditor._apply_character_logic_pre_llm_checks(
        ep_num=4,
        manuscript="body",
        validation_context={"npc_profiles": {}, "character_traits": {}},
    )

    assert result["early_result"]["decision"] == "REJECT"
    assert result["early_result"]["score"] == 41
    assert result["early_result"]["feedback"] == "logic drift"
