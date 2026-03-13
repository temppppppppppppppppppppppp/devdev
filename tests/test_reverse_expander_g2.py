"""ReverseExpander [G-2] regression tests."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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


def test_load_drafts_from_folder_accepts_cp949_input(tmp_path: Path):
    source_dir = tmp_path / "drafts"
    source_dir.mkdir()
    (source_dir / "1.txt").write_bytes("투자물 테스트".encode("cp949"))

    expander = ReverseExpander()

    count = expander.load_drafts_from_folder(str(tmp_path))

    assert count == 1
    assert expander.raw_drafts[0]["content"] == "투자물 테스트"


def test_load_drafts_from_file_fails_closed_on_unrecoverable_encoding(tmp_path: Path):
    draft_path = tmp_path / "broken.txt"
    draft_path.write_bytes(b"\x80")

    expander = ReverseExpander()

    with pytest.raises(ReverseExpander.DraftEncodingError):
        expander.load_drafts_from_file(str(draft_path))


def test_load_drafts_from_folder_fails_closed_on_unrecoverable_encoding(tmp_path: Path):
    source_dir = tmp_path / "drafts"
    source_dir.mkdir()
    (source_dir / "1.txt").write_bytes(b"\x80")

    expander = ReverseExpander()

    with pytest.raises(ReverseExpander.DraftEncodingError):
        expander.load_drafts_from_folder(str(tmp_path))


def test_run_returns_plot_roadmap_before_save(tmp_path: Path):
    source_dir = tmp_path / "drafts"
    source_dir.mkdir()
    (source_dir / "1.txt").write_text("초안", encoding="utf-8")

    expander = ReverseExpander()
    expander.load_drafts_from_folder = MagicMock(
        side_effect=lambda _path: (
            setattr(expander, "raw_drafts", [{"ep_num": 1, "title": "제1화", "content": "초안"}]) or 1
        )
    )
    expander.detect_genre = MagicMock(return_value="wuxia")
    expander.init_preset = MagicMock()
    expander.extract_bible = MagicMock(side_effect=lambda: setattr(expander, "bible", {"MasterBible": {}}))
    expander.extract_episode_bibles = MagicMock(
        side_effect=lambda: setattr(
            expander,
            "episode_bibles",
            [{"ep_num": 1, "hud_snapshot": {}, "changes": [], "new_npcs": [], "key_events": ["event-1"]}],
        )
    )
    expander.extract_style_guide = MagicMock()
    expander.save_all = MagicMock()

    with patch("modules.core.stage0.reverse_expander.SPINNER_AVAILABLE", False):
        bible, episode_bibles, style_guide = expander.run(str(source_dir), str(tmp_path))

    assert style_guide is None
    assert len(episode_bibles) == 1
    roadmap = bible["MasterBible"]["plot_roadmap"]
    assert roadmap[0]["block_no"] == 1
    assert roadmap[0]["arc_no"] == 1
    assert roadmap[0]["ep_count"] == 1
    assert roadmap[0]["key_events"] == ["event-1"]
