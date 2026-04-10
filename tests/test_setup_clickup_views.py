from scripts.setup_clickup_views import (
    FULL_QUEUE_TABLE_NAME,
    OPERATIONS_BOARD_NAME,
    _find_view_by_name,
    build_full_queue_table_payload,
    build_operations_board_payload,
)


def test_build_operations_board_payload_has_expected_defaults():
    payload = build_operations_board_payload()

    assert payload["name"] == OPERATIONS_BOARD_NAME
    assert payload["type"] == "board"
    assert payload["grouping"]["field"] == "status"
    assert payload["filters"]["show_closed"] is False
    assert payload["settings"]["show_empty_statuses"] is True


def test_build_full_queue_table_payload_has_expected_defaults():
    payload = build_full_queue_table_payload()

    assert payload["name"] == FULL_QUEUE_TABLE_NAME
    assert payload["type"] == "table"
    assert payload["filters"]["show_closed"] is True
    assert payload["settings"]["show_closed_subtasks"] is True


def test_find_view_by_name_matches_case_insensitively():
    views = [
        {"id": "1", "name": "Table"},
        {"id": "2", "name": "글도비 운영 보드"},
    ]

    assert _find_view_by_name(views, "글도비 운영 보드") == {"id": "2", "name": "글도비 운영 보드"}
    assert _find_view_by_name(views, "글도비 운영 보드".upper()) == {"id": "2", "name": "글도비 운영 보드"}
    assert _find_view_by_name(views, "missing") is None
