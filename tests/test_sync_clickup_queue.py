from __future__ import annotations

from pathlib import Path

from scripts.sync_clickup_queue import (
    QueueItem,
    _desired_clickup_status,
    _extract_sync_marker,
    _looks_proof_pending,
    _resolve_field_value_payload,
    build_task_markdown,
    resolve_clickup_status_name,
)


def _item(**overrides) -> QueueItem:
    base = {
        "topic": "0_0-stage4-consumer-contract-normalization-remediation",
        "temp_path": "docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md",
        "canonical_path": "docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md",
        "status": "in_progress",
        "queue_role": "front_active",
        "roadmap_rank": 1,
        "depends_on": [],
        "mirror_present": True,
        "canonical_present": True,
    }
    base.update(overrides)
    return QueueItem(**base)


def test_desired_clickup_status_maps_repo_semantics():
    assert _desired_clickup_status(_item(status="blocked")) == "Blocked"
    assert _desired_clickup_status(_item(queue_role="parked_future_wave")) == "Parked"
    assert _desired_clickup_status(_item(queue_role="historical_backing")) == "Closed"
    assert _desired_clickup_status(_item(status="pending")) == "Ready"
    assert _desired_clickup_status(_item(status="in_progress")) == "Realizing"


def test_desired_clickup_status_marks_proof_pending_items_for_review():
    canonical_doc_text = """
    keep this SSOT verification-pending until the next bounded rerun lands.
    closure still requires a completed rerun before we demote the lane.
    """

    assert _looks_proof_pending(canonical_doc_text) is True
    assert (
        _desired_clickup_status(_item(status="in_progress"), canonical_doc_text=canonical_doc_text)
        == "Proof Pending"
    )


def test_resolve_clickup_status_name_supports_explicit_and_heuristic_mapping():
    available = ["To Do", "In Progress", "Review", "Blocked", "Done"]

    assert resolve_clickup_status_name("Ready", available) == "To Do"
    assert resolve_clickup_status_name("Realizing", available) == "In Progress"
    assert resolve_clickup_status_name("Proof Pending", available) == "Review"
    assert resolve_clickup_status_name("Closed", available) == "Done"
    assert (
        resolve_clickup_status_name("Parked", available, explicit_map={"Parked": "To Do"}) == "To Do"
    )


def test_build_task_markdown_embeds_sync_marker_and_paths():
    queue_path = Path("docs/temp/queue-state.json")
    markdown = build_task_markdown(
        _item(depends_on=["0_0-stage4-repair-contract-normalization-remediation"]),
        queue_state_path=queue_path,
        work_type="execution",
        subsystem="stage4",
        desired_status="Realizing",
    )

    assert _extract_sync_marker(markdown) == "0_0-stage4-consumer-contract-normalization-remediation"
    assert "docs/temp/execution-roadmap.md" in markdown
    assert "docs/temp/queue-state.json" in markdown
    assert "0_0-stage4-repair-contract-normalization-remediation" in markdown


def test_resolve_field_value_payload_for_dropdown_and_text():
    dropdown_field = {
        "name": "Queue Role",
        "type": "drop_down",
        "type_config": {
            "options": [
                {"id": "opt-front", "name": "front_active"},
                {"id": "opt-parked", "name": "parked_future_wave"},
            ]
        },
    }
    text_field = {"name": "Canonical Path", "type": "text"}

    assert _resolve_field_value_payload(dropdown_field, "parked_future_wave") == {"value": "opt-parked"}
    assert _resolve_field_value_payload(text_field, "docs/2026-04-02/example.md") == {
        "value": "docs/2026-04-02/example.md"
    }
