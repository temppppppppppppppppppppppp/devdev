from unittest.mock import MagicMock

from modules.core.final_accepted_context import (
    has_final_accepted_context_accessor,
    load_final_accepted_manuscript_row,
    load_final_accepted_manuscript_text,
)


class _FinalContextDb:
    def __init__(self, context):
        self.context = context
        self.get_manuscript_called = False

    def get_final_accepted_episode_context(self, ep_num, *, stage=4):
        return self.context

    def get_manuscript(self, ep_num):
        self.get_manuscript_called = True
        return {"ep_num": ep_num, "content": "fallback should not win"}


class _LegacyDb:
    def get_manuscript(self, ep_num):
        return {"ep_num": ep_num, "title": "legacy", "content": "legacy text"}


def test_load_final_accepted_manuscript_row_uses_final_context_accessor():
    db = _FinalContextDb(
        {
            "ep_num": 4,
            "title": "accepted",
            "content": "accepted text",
            "authority_status": "stage4_final_accepted",
            "source_kind": "db_manuscript_plus_stage_attempt",
            "content_hash": "hash",
        }
    )

    row = load_final_accepted_manuscript_row(db, 4)

    assert row["content"] == "accepted text"
    assert row["final_context_status"] == "stage4_final_accepted"
    assert row["final_context_source"] == "db_manuscript_plus_stage_attempt"
    assert db.get_manuscript_called is False


def test_load_final_accepted_manuscript_row_does_not_fallback_after_blocked_context():
    db = _FinalContextDb(
        {
            "ep_num": 4,
            "content": "",
            "authority_status": "blocked_by_non_final_stage4_attempt",
            "source_kind": "stage_attempts",
            "usable": False,
        }
    )

    assert load_final_accepted_manuscript_row(db, 4) is None
    assert load_final_accepted_manuscript_text(db, 4) == ""
    assert db.get_manuscript_called is False


def test_load_final_accepted_manuscript_row_allows_legacy_fallback():
    row = load_final_accepted_manuscript_row(_LegacyDb(), 3)

    assert row["content"] == "legacy text"
    assert row["final_context_status"] == "legacy_manuscript_fallback"
    assert row["final_context_source"] == "get_manuscript"


def test_load_final_accepted_manuscript_row_ignores_unconfigured_mock_rows():
    db = MagicMock()

    assert load_final_accepted_manuscript_row(db, 3) is None
    assert has_final_accepted_context_accessor(db) is False
