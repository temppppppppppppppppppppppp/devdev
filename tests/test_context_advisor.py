"""Unit tests for ContextAdvisor (SC-1)."""

from modules.core.constants import GenreTypes
from modules.core.context_advisor import ContextAdvisor, ContextBudgetTracker, RetrievalSlot


def _make_enabled_advisor(*, llm_enricher=None):
    advisor = ContextAdvisor(llm_enricher=llm_enricher)
    advisor.enabled = True
    advisor._is_stage_enabled = lambda _stage: True
    return advisor


def test_stage2_plan_builds_expected_slots():
    advisor = _make_enabled_advisor()
    plan = advisor.plan_stage2_retrieval(
        arc_data={
            "block_theme": "rise of a new fund",
            "tactical_doc": "hedge risk, rotate sectors, keep dry powder",
            "plot_suspension": ["debt covenant"],
        },
        current_ep=12,
        npc_roster=["Han", "Park", "Lee"],
    )

    categories = {slot.category for slot in plan.slots}
    assert plan.stage == "stage2"
    assert len(plan.slots) <= 5
    assert "block_theme" in categories
    assert "similar_theme" in categories
    assert "npc_recent" in categories
    assert "unresolved_plot" in categories
    assert "arc_tactical" in categories
    assert all(slot.max_chars > 0 for slot in plan.slots)


def test_stage4_plan_includes_scene_plot_and_relationship_slots():
    advisor = _make_enabled_advisor()
    plan = advisor.plan_stage4_retrieval(
        arc_data={
            "tactical_doc": "secure liquidity before collapse",
            "plot_suspension": ["unpaid margin loan"],
            "state_changes": {
                "relationship_changes": [{"npc": "Han", "change": "trust->doubt"}],
                "npc_deaths": [{"name": "Kim"}],
            },
        },
        blueprint={
            "scene_breakdown": [
                {"goal": "convince risk committee"},
                {"goal": "execute overnight hedge"},
            ],
            "end_location": "Seoul",
            "ending_hook": "margin call at dawn",
        },
        prev_ending="portfolio was left exposed",
        current_ep=21,
        npc_roster=["Han", "Jung"],
        genre="investment",
    )

    categories = {slot.category for slot in plan.slots}
    assert plan.stage == "stage4"
    assert len(plan.slots) <= 8
    assert "prev_ending" in categories
    assert "scene_context" in categories
    assert "unresolved_plot" in categories
    assert "relationship_history" in categories
    assert any(cat.startswith("genre_context_") for cat in categories)


def test_director_plan_uses_npc_mentions_from_manuscript():
    advisor = _make_enabled_advisor()
    plan = advisor.plan_director_retrieval(
        manuscript="Han meets Park in the vault and claims the deal never happened.",
        blueprint={"core_event": "denied debt rollover", "end_location": "Vault-7"},
        current_ep=33,
        npc_roster=["Han", "Park", "Choi"],
    )

    categories = {slot.category for slot in plan.slots}
    assert plan.stage == "director"
    assert "npc_consistency" in categories
    assert "event_claim" in categories
    assert "location_item_consistency" in categories


def test_should_use_llm_when_trigger_conditions_match():
    advisor = _make_enabled_advisor()
    assert advisor._should_use_llm("stage4", {"is_arc_boundary": True, "npc_roster": []}) is True
    assert advisor._should_use_llm("stage4", {"is_reject_retry": True, "npc_roster": []}) is True
    assert advisor._should_use_llm("stage4", {"npc_roster": ["a", "b", "c", "d", "e"]}) is True
    assert advisor._should_use_llm("stage4", {"npc_roster": ["a", "b"]}) is False


def test_llm_enrich_adds_slots_when_available():
    def fake_enricher(**_kwargs):
        return [
            {"query": "verify covenant breach timeline", "priority": 1, "category": "event_claim"},
            {"query": "Han Park prior conflict episodes", "priority": 2, "category": "npc_consistency"},
        ]

    advisor = _make_enabled_advisor(llm_enricher=fake_enricher)
    plan = advisor.plan_stage4_retrieval(
        arc_data={},
        blueprint={"scene_breakdown": [{"goal": "close emergency funding"}]},
        prev_ending="liquidity panic overnight",
        current_ep=8,
        npc_roster=["Han", "Park", "Lee", "Choi", "Jang"],
        genre="investment",
    )

    queries = {slot.query for slot in plan.slots}
    assert plan.used_llm is True
    assert "verify covenant breach timeline" in queries
    assert "Han Park prior conflict episodes" in queries


def test_llm_enrich_falls_back_to_heuristic_on_failure():
    def failing_enricher(**_kwargs):
        raise RuntimeError("timeout")

    advisor = _make_enabled_advisor(llm_enricher=failing_enricher)
    plan = advisor.plan_stage4_retrieval(
        arc_data={},
        blueprint={"scene_breakdown": [{"goal": "hold risk line"}]},
        prev_ending="carry trade unwind",
        current_ep=9,
        npc_roster=["A", "B", "C", "D", "E"],
        genre="investment",
    )

    assert plan.used_llm is False
    assert any(slot.category == "scene_context" for slot in plan.slots)


def test_stage4_genre_queries_are_dense_and_multiple():
    advisor = _make_enabled_advisor()
    plan = advisor.plan_stage4_retrieval(
        arc_data={},
        blueprint={"scene_breakdown": [{"goal": "시장 패닉 대응"}]},
        prev_ending="유동성 위기 조짐",
        current_ep=14,
        npc_roster=["한시우"],
        genre="investment",
    )

    genre_slots = [slot for slot in plan.slots if slot.category.startswith("genre_context_")]
    assert len(genre_slots) >= 2
    queries = " ".join(slot.query for slot in genre_slots)
    assert "레버리지" in queries
    assert "금리" in queries
    assert "부동산" in queries


def test_stage4_fantasy_genre_queries_include_non_magic_combat_terms():
    advisor = _make_enabled_advisor()
    plan = advisor.plan_stage4_retrieval(
        arc_data={},
        blueprint={"scene_breakdown": [{"goal": "결전 준비"}]},
        prev_ending="성문이 함락되기 직전",
        current_ep=27,
        npc_roster=["주인공", "기사단장"],
        genre="fantasy",
    )

    genre_slots = [slot for slot in plan.slots if slot.category.startswith("genre_context_")]
    assert len(genre_slots) >= 2
    queries = " ".join(slot.query for slot in genre_slots)
    assert "검술" in queries
    assert "전투" in queries


def test_supported_genres_have_context_hints():
    advisor = _make_enabled_advisor()
    for genre in GenreTypes.all():
        assert genre in advisor._GENRE_HINTS
        assert len(advisor._GENRE_HINTS[genre]) >= 3


def test_master_flag_off_returns_empty_plan(monkeypatch):
    def fake_threshold(key, default):
        if key == "smart_retrieval.enabled":
            return False
        return default

    monkeypatch.setattr("modules.core.context_advisor._threshold", fake_threshold)
    advisor = ContextAdvisor()
    plan = advisor.plan_stage2_retrieval({"block_theme": "x"}, 1, ["npc"])

    assert plan.slots == []


def test_budget_tracker_reports_and_targets():
    tracker = ContextBudgetTracker(total_budget_chars=1000)
    tracker.register_section("a", "x" * 300)
    tracker.register_section("b", "x" * 500)
    tracker.register_section("c", "x" * 400)

    report = tracker.get_usage_report()
    assert report["used_chars"] == 1200
    assert report["remaining_chars"] == 0

    targets = tracker.get_compression_targets()
    assert targets
    assert targets[0] == "b"


def test_dedupe_slots_keeps_first_and_sorts_by_priority():
    slots = [
        RetrievalSlot(category="x", query="same query", priority=3),
        RetrievalSlot(category="x", query="same query", priority=1),
        RetrievalSlot(category="y", query="other", priority=1),
    ]
    deduped = ContextAdvisor._dedupe_slots(slots)
    assert len(deduped) == 2
    assert deduped[0].priority <= deduped[1].priority
