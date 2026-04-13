from scripts.setup_clickup_views import (
    FULL_QUEUE_TABLE_NAME,
    MATERIAL_BI_COMPLETE_TABLE_NAME,
    MATERIAL_BOARD_NAME,
    MATERIAL_CANON_TABLE_NAME,
    MATERIAL_EXCEPTION_TABLE_NAME,
    MATERIAL_QUEUE_TABLE_NAME,
    MATERIAL_TR_BI_TABLE_NAME,
    OPERATIONS_BOARD_NAME,
    _dropdown_option_id,
    _find_custom_field_by_name,
    _find_view_by_name,
    build_full_queue_table_payload,
    build_material_exception_table_payload,
    build_material_stage_filtered_table_payload,
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


def test_build_material_view_payloads_accept_custom_names():
    board = build_operations_board_payload(MATERIAL_BOARD_NAME)
    table = build_full_queue_table_payload(MATERIAL_QUEUE_TABLE_NAME)

    assert board["name"] == MATERIAL_BOARD_NAME
    assert table["name"] == MATERIAL_QUEUE_TABLE_NAME
    assert board["type"] == "board"
    assert table["type"] == "table"


def test_build_material_stage_filtered_table_payload_filters_stage_value():
    payload = build_material_stage_filtered_table_payload(
        "field-123",
        "TR/BI 생산 단계",
        name=MATERIAL_TR_BI_TABLE_NAME,
    )

    assert payload["name"] == MATERIAL_TR_BI_TABLE_NAME
    assert payload["type"] == "table"
    assert payload["filters"]["fields"] == [{"field": "cf_field-123", "op": "EQ", "values": ["TR/BI 생산 단계"]}]


def test_build_material_exception_table_payload_filters_non_normal_ops_state():
    payload = build_material_exception_table_payload("field-ops", "opt-normal")

    assert payload["name"] == MATERIAL_EXCEPTION_TABLE_NAME
    assert payload["type"] == "table"
    assert payload["filters"]["fields"] == [{"field": "cf_field-ops", "op": "NOT", "values": ["opt-normal"]}]


def test_find_custom_field_helpers_match_name_and_option():
    fields = [
        {
            "id": "ops-field",
            "name": "Ops State",
            "type": "drop_down",
            "type_config": {"options": [{"id": "normal-id", "name": "normal"}]},
        },
        {"id": "stage-field", "name": "Material Stage", "type": "short_text"},
    ]

    assert _find_custom_field_by_name(fields, "ops state") == fields[0]
    assert _find_custom_field_by_name(fields, "Material Stage") == fields[1]
    assert _dropdown_option_id(fields[0], "normal") == "normal-id"
    assert _dropdown_option_id(fields[1], "normal") is None


def test_material_stage_view_names_are_stable():
    assert MATERIAL_CANON_TABLE_NAME == "글도비 canon 큐"
    assert MATERIAL_TR_BI_TABLE_NAME == "글도비 TR/BI 생산 큐"
    assert MATERIAL_BI_COMPLETE_TABLE_NAME == "글도비 BI 완료 큐"


def test_find_view_by_name_matches_case_insensitively():
    views = [
        {"id": "1", "name": "Table"},
        {"id": "2", "name": "글도비 운영 보드"},
    ]

    assert _find_view_by_name(views, "글도비 운영 보드") == {"id": "2", "name": "글도비 운영 보드"}
    assert _find_view_by_name(views, "글도비 운영 보드".upper()) == {"id": "2", "name": "글도비 운영 보드"}
    assert _find_view_by_name(views, "missing") is None
