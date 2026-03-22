import re
from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


def test_resolve_narrative_summary_batch_logs_and_returns_none_when_manuscripts_missing():
    ui = SimpleNamespace(log=MagicMock())
    db = SimpleNamespace(get_recent_manuscripts=MagicMock(return_value=None))
    app = SimpleNamespace(ui=ui, current_project=SimpleNamespace(db=db))

    result = main_a.SovereignApp._resolve_narrative_summary_batch(app, up_to_ep=10)

    assert result is None
    logs = [call.args[0] for call in ui.log.call_args_list if call.args]
    assert any("(0화)" in message for message in logs)


def test_resolve_narrative_summary_batch_normalizes_sparse_episode_coverage():
    db = SimpleNamespace(
        get_recent_manuscripts=MagicMock(
            return_value=[
                {"ep_num": 1, "content": "A"},
                {"ep_num": "3", "content": "B"},
                {"ep_num": 5, "content": "C"},
            ]
        )
    )
    app = SimpleNamespace(
        ui=SimpleNamespace(log=MagicMock()),
        current_project=SimpleNamespace(db=db),
        _format_episode_coverage_label=lambda episodes: main_a.SovereignApp._format_episode_coverage_label(
            SimpleNamespace(),
            episodes,
        ),
    )

    result = main_a.SovereignApp._resolve_narrative_summary_batch(app, up_to_ep=5)

    assert result["episode_numbers"] == [1, 3, 5]
    assert result["coverage_label"] == "1,3,5"


def test_build_narrative_summary_combined_text_uses_excerpt_for_long_content():
    app = SimpleNamespace()
    manuscripts = [
        {"ep_num": 1, "content": "short-content"},
        {"ep_num": 2, "content": ("A" * 900) + "사망" + ("B" * 1200)},
    ]
    pattern = re.compile(r"사망|죽|습득|획득|부상|배신|발견|파괴|탈출|각성|잃|빼앗|살해|처단|중상|결별|동맹|합류")

    result = main_a.SovereignApp._build_narrative_summary_combined_text(
        app,
        manuscripts=manuscripts,
        key_event_pattern=pattern,
    )

    assert "[제1화]\nshort-content" in result
    assert "[제2화]" in result
    assert "...(중략)..." in result
    assert "사망" in result


def test_build_narrative_summary_prompt_includes_label_and_trims_excerpt():
    app = SimpleNamespace()
    combined_text = "X" * 13000

    prompt = main_a.SovereignApp._build_narrative_summary_prompt(
        app,
        coverage_label="1-5",
        combined_text=combined_text,
    )

    assert "제1-5화" in prompt
    assert "요약 (800자 이내, 한국어):" in prompt
    assert "X" * 12000 in prompt
    assert "X" * 12050 not in prompt


def test_persist_narrative_summary_anchor_saves_payload_and_logs():
    db = MagicMock()
    db.conn = MagicMock()
    app = SimpleNamespace(
        current_project=SimpleNamespace(db=db),
        ui=SimpleNamespace(log=MagicMock()),
    )

    main_a.SovereignApp._persist_narrative_summary_anchor(
        app,
        up_to_ep=5,
        coverage_label="1,3,5",
        episode_numbers=[1, 3, 5, 5],
        summary="요약문" * 20,
        manuscript_count=3,
    )

    saved_key, payload = db.save_anchor.call_args.args
    assert saved_key == "narrative_summary_ep_005"
    assert payload["ep_range"] == "1,3,5"
    assert payload["episode_list"] == [1, 3, 5]
    assert payload["ep_count"] == 3
    db.conn.commit.assert_called_once()
    logs = [call.args[0] for call in app.ui.log.call_args_list if call.args]
    assert any("narrative_summary_ep_005" in message for message in logs)
