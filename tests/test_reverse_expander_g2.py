"""ReverseExpander [G-2] regression tests."""

from unittest.mock import MagicMock, patch

from modules.core.stage0.reverse_expander import ReverseExpander


def _make_expander_with_drafts(count: int) -> ReverseExpander:
    expander = ReverseExpander()
    expander.preset_registry = MagicMock()
    expander.preset_registry.get_schema_for_prompt.return_value = ""
    expander.raw_drafts = [{"ep_num": i, "title": f"ep{i}", "content": f"content-{i}"} for i in range(1, count + 1)]
    return expander


def test_extract_episode_bibles_uses_prev_state_sequentially():
    expander = _make_expander_with_drafts(6)
    seen_prev = []

    def _fake_extract(draft, prev_state, schema):
        seen_prev.append((draft["ep_num"], prev_state.get("ep_num")))
        return {"ep_num": draft["ep_num"], "hud_snapshot": {}, "changes": [], "new_npcs": [], "key_events": []}

    expander._extract_single_episode_bible = _fake_extract

    result = expander.extract_episode_bibles()

    assert [row["ep_num"] for row in result] == [1, 2, 3, 4, 5, 6]
    assert seen_prev == [(1, None), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5)]


def test_extract_episode_bibles_with_progress_uses_prev_state_sequentially():
    expander = _make_expander_with_drafts(6)
    seen_prev = []

    def _fake_extract(draft, prev_state, schema):
        seen_prev.append((draft["ep_num"], prev_state.get("ep_num")))
        return {"ep_num": draft["ep_num"], "hud_snapshot": {}, "changes": [], "new_npcs": [], "key_events": []}

    expander._extract_single_episode_bible = _fake_extract

    class _DummyProgress:
        def __init__(self, total, label):
            self.total = total
            self.label = label

        def start(self):
            return None

        def update(self, message=""):
            return None

        def finish(self, message=""):
            return None

    with patch("modules.core.stage0.reverse_expander.ProgressBar", _DummyProgress):
        expander._extract_episode_bibles_with_progress()

    assert [row["ep_num"] for row in expander.episode_bibles] == [1, 2, 3, 4, 5, 6]
    assert seen_prev == [(1, None), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5)]
