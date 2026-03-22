import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import main_a
from modules.core.stage2_context import Stage2Context
from modules.core.stage3_context import Stage3Context
from modules.core.stage4_context import Stage4Context


def _bind_episode_label_helper(app):
    app._format_episode_coverage_label = lambda episodes: main_a.SovereignApp._format_episode_coverage_label(app, episodes)
    app._resolve_narrative_summary_batch = (
        lambda up_to_ep: main_a.SovereignApp._resolve_narrative_summary_batch(app, up_to_ep)
    )
    app._build_narrative_summary_combined_text = (
        lambda **kwargs: main_a.SovereignApp._build_narrative_summary_combined_text(app, **kwargs)
    )
    app._build_narrative_summary_prompt = (
        lambda **kwargs: main_a.SovereignApp._build_narrative_summary_prompt(app, **kwargs)
    )
    app._persist_narrative_summary_anchor = (
        lambda **kwargs: main_a.SovereignApp._persist_narrative_summary_anchor(app, **kwargs)
    )
    return app


def test_get_protagonist_name_prefers_live_master_bible_over_db_anchor():
    current_project = SimpleNamespace(
        master_bible={"MasterBible": {"characters": [{"name": "라이브 주인공"}]}},
        db=MagicMock(),
    )
    current_project.db.load_anchor.return_value = {"MasterBible": {"characters": [{"name": "stale hero"}]}}
    app = SimpleNamespace(current_project=current_project, selected_genre={"type": "wuxia"})

    result = main_a.SovereignApp._get_protagonist_name(app)

    assert result == "라이브 주인공"


def test_fix_entity_registry_protagonist_promotes_existing_extracted_row():
    registry = {"characters": [{"name": "윤호", "role": "extracted", "first_appearance": "unknown"}]}

    result = main_a.SovereignApp._fix_entity_registry_protagonist(SimpleNamespace(), registry, protagonist_name="윤호")

    assert len(result["characters"]) == 1
    assert result["characters"][0]["name"] == "윤호"
    assert result["characters"][0]["role"] == "주인공"


def test_calculate_arc_from_episode_uses_actual_arc_boundaries_before_default_bucket():
    app = SimpleNamespace(
        current_project=SimpleNamespace(
            arcs=[
                {"arc_no": 1, "ep_start": 1, "ep_end": 4},
                {"arc_no": 2, "ep_start": 5, "ep_end": 7},
                {"arc_no": 3, "ep_start": 8, "ep_end": 11},
            ]
        )
    )

    assert main_a.SovereignApp._calculate_arc_from_episode(app, 5) == 2
    assert main_a.SovereignApp._calculate_arc_from_episode(app, 9) == 3


def test_restore_preset_registry_clears_stale_registry_when_payload_missing():
    app = SimpleNamespace(
        current_project=SimpleNamespace(_preset_state_raw=None),
        preset_registry="STALE",
        ui=MagicMock(),
    )

    main_a.SovereignApp._restore_preset_registry(app)

    assert app.preset_registry is None


def test_restore_preset_registry_clears_stale_registry_on_malformed_payload():
    app = SimpleNamespace(
        current_project=SimpleNamespace(_preset_state_raw={"bad": object()}),
        preset_registry="STALE",
        ui=MagicMock(),
    )

    main_a.SovereignApp._restore_preset_registry(app)

    assert app.preset_registry is None


def _make_cache_app(tmp_path: Path, *, save_ok: bool, commit_ok: bool):
    db = MagicMock()
    db.load_anchor.return_value = {
        "writer_cache": "writer-cache",
        "analyst_cache": "analyst-cache",
        "weaver_cache": "weaver-cache",
    }
    db.save_anchor.return_value = save_ok
    app = SimpleNamespace(
        current_project=SimpleNamespace(db=db, paths=SimpleNamespace(config=tmp_path)),
        ui=MagicMock(),
        sys=SimpleNamespace(api_client=MagicMock()),
        agents={
            "writer": SimpleNamespace(),
            "analyst": SimpleNamespace(),
            "weaver": SimpleNamespace(),
        },
        _get_agent_model_map=lambda: {},
        _is_cache_alive=lambda _name: True,
        _safe_commit=lambda: commit_ok,
        _audit_event=MagicMock(),
    )
    app.ui.log = MagicMock()
    return app


def test_load_quad_cache_contexts_reads_prompt_sources(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True)
    (prompts_dir / "writer_rules.json").write_text(
        '{"common_manifesto": ["rule one", "rule two"]}',
        encoding="utf-8",
    )
    (prompts_dir / "analyst_libraries.json").write_text('{"library":"analyst"}', encoding="utf-8")
    (prompts_dir / "weaver_rules.json").write_text('{"rule":"weaver"}', encoding="utf-8")

    app = SimpleNamespace(current_project=SimpleNamespace(paths=SimpleNamespace(config=tmp_path)))

    contexts = main_a.SovereignApp._load_quad_cache_contexts(app)

    assert "rule one" in contexts["writer"]
    assert '{"library":"analyst"}' in contexts["analyst"]
    assert '{"rule":"weaver"}' in contexts["weaver"]


def test_ensure_quad_agent_cache_skips_short_context_without_api_create():
    cache_info = {}
    create_mock = MagicMock()
    app = SimpleNamespace(
        _is_cache_alive=lambda _name: False,
        ui=SimpleNamespace(log=MagicMock()),
        sys=SimpleNamespace(api_client=SimpleNamespace(caches=SimpleNamespace(create=create_mock))),
    )

    main_a.SovereignApp._ensure_quad_agent_cache(
        app,
        cache_info=cache_info,
        cache_key="writer_cache",
        agent_label="Writer",
        context_text="too short",
        model_id="gemini-2.5-flash",
        display_name="WRITER_V31",
        system_instruction="소설가",
    )

    assert cache_info["writer_cache"] is None
    create_mock.assert_not_called()


def test_inject_quad_cache_names_assigns_existing_handles():
    app = SimpleNamespace(
        agents={
            "writer": SimpleNamespace(),
            "analyst": SimpleNamespace(),
            "weaver": SimpleNamespace(),
        },
        ui=SimpleNamespace(log=MagicMock()),
    )

    main_a.SovereignApp._inject_quad_cache_names(
        app,
        {
            "writer_cache": "writer-cache",
            "analyst_cache": "analyst-cache",
            "weaver_cache": "weaver-cache",
        },
    )

    assert app.agents["writer"].cache_name == "writer-cache"
    assert app.agents["analyst"].cache_name == "analyst-cache"
    assert app.agents["weaver"].cache_name == "weaver-cache"


@pytest.mark.parametrize(
    ("save_ok", "commit_ok"),
    [
        (False, True),
        (True, False),
    ],
)
def test_ignite_quad_cache_system_skips_success_injection_on_persistence_failure(tmp_path, save_ok, commit_ok):
    app = _make_cache_app(tmp_path, save_ok=save_ok, commit_ok=commit_ok)

    main_a.SovereignApp._ignite_quad_cache_system(app)

    logs = [call.args[0] for call in app.ui.log.call_args_list if call.args]
    assert not any("캐시 정보 DB 저장 완료" in message for message in logs)
    assert not hasattr(app.agents["writer"], "cache_name")
    assert not hasattr(app.agents["analyst"], "cache_name")
    assert not hasattr(app.agents["weaver"], "cache_name")
    assert not any(
        call.args and call.args[0] == main_a.AuditEvents.CACHE_CREATED for call in app._audit_event.call_args_list
    )


def test_load_narrative_summaries_filters_future_anchors_by_latest_episode():
    db = SimpleNamespace(
        load_all_anchors=lambda: {
            "narrative_summary_ep_005": {"ep_range": "1-5", "summary": "과거 요약"},
            "narrative_summary_ep_010": {"ep_range": "6-10", "summary": "미래 요약"},
        }
    )
    app = _bind_episode_label_helper(
        SimpleNamespace(
            _narrative_summaries_cache=None,
            current_project=SimpleNamespace(get_latest_episode_number=lambda: 6, db=db),
        )
    )

    result = main_a.SovereignApp._load_narrative_summaries(app)

    assert "과거 요약" in result
    assert "미래 요약" not in result


def test_generate_narrative_summary_persists_sparse_episode_coverage(monkeypatch):
    db = MagicMock()
    db.get_recent_manuscripts.return_value = [
        {"ep_num": 1, "content": "A" * 2000},
        {"ep_num": 3, "content": "B" * 2000},
        {"ep_num": 5, "content": "C" * 2000},
    ]
    db.conn = MagicMock()
    app = _bind_episode_label_helper(
        SimpleNamespace(
            ui=MagicMock(),
            current_project=SimpleNamespace(db=db),
            sys=SimpleNamespace(api_client=MagicMock()),
            _narrative_summaries_cache=None,
        )
    )
    app.ui.log = MagicMock()

    monkeypatch.setattr(time, "sleep", lambda _secs: None)
    monkeypatch.setattr(main_a, "generate_content_via_router", lambda **_kwargs: SimpleNamespace(text="요약문 " * 20))

    main_a.SovereignApp._generate_narrative_summary(app, up_to_ep=5)

    saved_key, payload = db.save_anchor.call_args.args
    assert saved_key == "narrative_summary_ep_005"
    assert payload["ep_range"] == "1,3,5"
    assert payload["episode_list"] == [1, 3, 5]


def test_reserved_state_service_facade_shims_are_documented_and_not_context_wired():
    expected = {
        "_extract_block_index",
        "_extract_pattern_keywords",
        "_pattern_presence_check",
        "_build_validation_context",
        "_load_genre_references",
    }

    assert set(main_a.RESERVED_STATE_SERVICE_FACADE_SHIMS) == expected

    for shim_name in expected:
        assert hasattr(main_a.SovereignApp, shim_name)
        callback_name = shim_name.removeprefix("_")
        assert callback_name not in Stage2Context.__slots__
        assert callback_name not in Stage3Context.__slots__
        assert callback_name not in Stage4Context.__slots__
