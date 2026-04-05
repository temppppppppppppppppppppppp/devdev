"""[Sweep20] Regression tests for StateTrackerNPC."""

import sys
import types
from unittest.mock import MagicMock

from modules.domain.agents.state_tracker import StateTracker
from modules.domain.agents.state_tracker_npc import StateTrackerNPC


def _install_google_genai_types(monkeypatch):
    google_mod = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    types_mod = types.ModuleType("google.genai.types")
    types_mod.GenerateContentConfig = lambda **kwargs: kwargs
    genai_mod.types = types_mod
    google_mod.genai = genai_mod
    monkeypatch.setitem(sys.modules, "google", google_mod)
    monkeypatch.setitem(sys.modules, "google.genai", genai_mod)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_mod)


def test_regex_extract_npc_injuries_handles_single_group_body_pattern():
    helper = StateTrackerNPC(tracker=MagicMock())
    injuries = helper._regex_extract_npc_injuries("강철의 팔이 부러졌다.")
    assert any(i.get("name") == "강철" and i.get("state") == "중상" for i in injuries)


def test_cleanup_npc_registry_with_llm_returns_empty_list_on_empty_response(monkeypatch):
    tracker = MagicMock()
    tracker.npc_registry = {name: {"status": "alive"} for name in ["강철", "백운", "청화", "도윤", "현무"]}

    _install_google_genai_types(monkeypatch)
    monkeypatch.setattr("modules.domain.agents.state_tracker_npc.time.sleep", lambda *_: None)
    monkeypatch.setattr(
        "modules.domain.agents.state_tracker_npc.generate_content_via_router",
        lambda **_: MagicMock(text=""),
    )

    tracker._llm_client = MagicMock()

    helper = StateTrackerNPC(tracker=tracker)
    result = helper.cleanup_npc_registry_with_llm(arc_no=5)
    assert result == []


def test_cleanup_npc_registry_with_llm_accepts_fenced_json(monkeypatch):
    tracker = MagicMock()
    tracker.npc_registry = {name: {"status": "alive"} for name in ["강철", "백운", "청화", "도윤", "현무"]}

    _install_google_genai_types(monkeypatch)
    monkeypatch.setattr("modules.domain.agents.state_tracker_npc.time.sleep", lambda *_: None)
    monkeypatch.setattr(
        "modules.domain.agents.state_tracker_npc.generate_content_via_router",
        lambda **_: MagicMock(text='```json\n{"remove": ["강철"]}\n```'),
    )

    tracker._llm_client = MagicMock()

    helper = StateTrackerNPC(tracker=tracker)
    result = helper.cleanup_npc_registry_with_llm(arc_no=5)

    assert result == ["강철"]


def test_verify_npc_names_llm_retries_on_empty_response(monkeypatch):
    tracker = MagicMock()
    tracker.npc_registry = {}

    _install_google_genai_types(monkeypatch)
    monkeypatch.setattr("modules.domain.agents.state_tracker_npc.time.sleep", lambda *_: None)
    responses = iter([MagicMock(text=""), MagicMock(text='["강철"]')])
    call_count = 0

    def _fake_generate_content(**_):
        nonlocal call_count
        call_count += 1
        return next(responses)

    monkeypatch.setattr("modules.domain.agents.state_tracker_npc.generate_content_via_router", _fake_generate_content)

    tracker._llm_client = MagicMock()

    helper = StateTrackerNPC(tracker=tracker)
    result = helper._verify_npc_names_llm(["강철", "도윤"], "맥락", arc_no=1)

    assert result == ["강철"]
    assert call_count == 2


def test_verify_npc_names_llm_accepts_whitespace_padded_json(monkeypatch):
    tracker = MagicMock()
    tracker.npc_registry = {}

    _install_google_genai_types(monkeypatch)
    monkeypatch.setattr("modules.domain.agents.state_tracker_npc.time.sleep", lambda *_: None)
    monkeypatch.setattr(
        "modules.domain.agents.state_tracker_npc.generate_content_via_router",
        lambda **_: MagicMock(text='  ["강철"]  '),
    )

    tracker._llm_client = MagicMock()

    helper = StateTrackerNPC(tracker=tracker)
    result = helper._verify_npc_names_llm(["강철", "도윤"], "맥락", arc_no=1)

    assert result == ["강철"]


def test_verify_npc_names_llm_accepts_fenced_json(monkeypatch):
    tracker = MagicMock()
    tracker.npc_registry = {}

    _install_google_genai_types(monkeypatch)
    monkeypatch.setattr("modules.domain.agents.state_tracker_npc.time.sleep", lambda *_: None)
    monkeypatch.setattr(
        "modules.domain.agents.state_tracker_npc.generate_content_via_router",
        lambda **_: MagicMock(text='```json\n["강철"]\n```'),
    )

    tracker._llm_client = MagicMock()

    helper = StateTrackerNPC(tracker=tracker)
    result = helper._verify_npc_names_llm(["강철", "도윤"], "맥락", arc_no=1)

    assert result == ["강철"]


def test_verify_npc_names_llm_retry_exhausted_fail_closed(monkeypatch):
    tracker = MagicMock()
    tracker.npc_registry = {}

    _install_google_genai_types(monkeypatch)
    monkeypatch.setattr("modules.domain.agents.state_tracker_npc.time.sleep", lambda *_: None)
    responses = iter([MagicMock(text=""), MagicMock(text="")])
    call_count = 0

    def _fake_generate_content(**_):
        nonlocal call_count
        call_count += 1
        return next(responses)

    monkeypatch.setattr("modules.domain.agents.state_tracker_npc.generate_content_via_router", _fake_generate_content)

    tracker._llm_client = MagicMock()

    helper = StateTrackerNPC(tracker=tracker)
    result = helper._verify_npc_names_llm(["강철", "도윤"], "맥락", arc_no=1)

    assert result == []
    assert call_count == 2


def test_extract_npc_martial_state_changes_reads_explicit_state_changes_only():
    tracker = StateTracker()
    helper = tracker._npc

    result = helper.extract_npc_martial_state_changes_from_arc(
        {
            "arc_no": 3,
            "ep_start": 11,
            "tactical_doc": "Chief Han reached Peak and used Storm Palm.",
            "state_changes": {
                "npc_martial_state_changes": [
                    {
                        "name": "Chief Han",
                        "episode": 12,
                        "realm": "Peak",
                        "techniques_learned": ["Storm Palm", "Storm Palm"],
                    }
                ]
            },
        }
    )

    assert result == [
        {
            "name": "Chief Han",
            "episode": 12,
            "realm": "Peak",
            "techniques_learned": ["Storm Palm"],
        }
    ]


def test_extract_npc_martial_state_changes_does_not_fallback_to_regex_only_text():
    tracker = StateTracker()
    helper = tracker._npc

    result = helper.extract_npc_martial_state_changes_from_arc(
        {
            "arc_no": 3,
            "ep_start": 11,
            "tactical_doc": "Chief Han reached Peak and learned Storm Palm.",
            "state_changes": {},
        }
    )

    assert result == []
