from __future__ import annotations

from pathlib import Path

from scripts.sync_clickup_queue import (
    QueueItem,
    _collect_material_field_values,
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
        "material_stage": "",
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
        _desired_clickup_status(_item(status="in_progress"), canonical_doc_text=canonical_doc_text) == "Proof Pending"
    )


def test_resolve_clickup_status_name_supports_explicit_and_heuristic_mapping():
    available = ["To Do", "In Progress", "Review", "Blocked", "Done"]

    assert resolve_clickup_status_name("Ready", available) == "To Do"
    assert resolve_clickup_status_name("Realizing", available) == "In Progress"
    assert resolve_clickup_status_name("Proof Pending", available) == "Review"
    assert resolve_clickup_status_name("Closed", available) == "Done"
    assert resolve_clickup_status_name("Parked", available, explicit_map={"Parked": "To Do"}) == "To Do"
    assert resolve_clickup_status_name("Ready", available, explicit_map={"Ready": "READY"}) == "To Do"


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


def test_build_task_markdown_adds_korean_operator_summary():
    markdown = build_task_markdown(
        _item(),
        queue_state_path=Path("docs/temp/queue-state.json"),
        work_type="execution",
        subsystem="stage3",
        desired_status="Proof Pending",
    )

    assert "## 운영 요약" in markdown
    assert "fresh proof wave" in markdown
    assert "Stage3" in markdown


def test_build_task_markdown_material_profile_reads_sequential_status(tmp_path, monkeypatch):
    queue_path = tmp_path / "material-queue-state.json"
    sequential_path = tmp_path / "smart_new_hire_status.json"
    sequential_path.write_text(
        """
{
  "work_id": "smart_new_hire",
  "last_sequential_block_pass": 70,
  "next_unit_type": "complete",
  "next_block_id": null,
  "resume_basis": "bi_audit_pass",
  "production_complete": true,
  "bi_complete": true,
  "updated_at": "2026-04-12"
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.sync_clickup_queue.ROOT", tmp_path)

    markdown = build_task_markdown(
        _item(
            topic="smart_new_hire",
            temp_path="smart_new_hire_status.json",
            canonical_path="docs/2026-04-12/smart_new_hire_live_status.md",
            status="completed",
            queue_role="historical_backing",
            material_stage="bi_production_complete",
            roadmap_rank=None,
        ),
        queue_state_path=queue_path,
        work_type="execution",
        subsystem="stage4",
        desired_status="Closed",
        profile="material",
    )

    assert "글도비 재료 사이드 생산 스케줄 미러" in markdown
    assert "smart_new_hire" in markdown
    assert "`70`" in markdown
    assert "`complete`" in markdown
    assert "Sequential status" in markdown


def test_build_task_markdown_material_profile_handles_canon_stage_without_snapshot(tmp_path, monkeypatch):
    queue_path = tmp_path / "material-queue-state.json"
    monkeypatch.setattr("scripts.sync_clickup_queue.ROOT", tmp_path)

    markdown = build_task_markdown(
        _item(
            topic="africa_farm_king",
            temp_path="",
            canonical_path="material_ssot/20_pitch/canon/africa_farm_king.md",
            status="pending",
            queue_role="front_active",
            material_stage="canon_stage",
            roadmap_rank=None,
        ),
        queue_state_path=queue_path,
        work_type="ops",
        subsystem="ops",
        desired_status="Ready",
        profile="material",
    )

    assert "canon 단계" in markdown
    assert "africa_farm_king" in markdown


def test_collect_material_field_values_reads_sequential_status(tmp_path, monkeypatch):
    sequential_path = tmp_path / "smart_new_hire_status.json"
    sequential_path.write_text(
        """
{
  "work_id": "smart_new_hire",
  "last_sequential_block_pass": 70,
  "next_unit_type": "complete",
  "next_block_id": null,
  "resume_basis": "bi_audit_pass",
  "production_complete": true,
  "bi_complete": true,
  "updated_at": "2026-04-12"
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.sync_clickup_queue.ROOT", tmp_path)

    values = _collect_material_field_values(
        _item(
            topic="smart_new_hire",
            temp_path="smart_new_hire_status.json",
            canonical_path="docs/2026-04-12/smart_new_hire_live_status.md",
            material_stage="bi_production_complete",
        )
    )

    assert values["Work ID"] == "smart_new_hire"
    assert values["Material Stage"] == "BI 생산 완료"
    assert values["Ops State"] == "normal"
    assert values["Current Truth Path"] == "docs/2026-04-12/smart_new_hire_live_status.md"
    assert values["Sequential Status Path"] == "smart_new_hire_status.json"
    assert values["Last Sequential Block Pass"] == 70
    assert values["Next Unit Type"] == "complete"
    assert values["Resume Basis"] == "bi_audit_pass"
    assert values["Production Complete"] is True
    assert values["BI Complete"] is True


def test_collect_material_field_values_for_canon_stage_without_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.sync_clickup_queue.ROOT", tmp_path)

    values = _collect_material_field_values(
        _item(
            topic="africa_farm_king",
            temp_path="",
            canonical_path="material_ssot/20_pitch/canon/africa_farm_king.md",
            material_stage="canon_stage",
            status="pending",
        )
    )

    assert values["Work ID"] == "africa_farm_king"
    assert values["Material Stage"] == "canon 단계"
    assert values["Ops State"] == "normal"
    assert values["Sequential Status Path"] == ""
    assert values["Next Unit Type"] == "canon_stage"
    assert values["Resume Basis"] == "canon_pitch_anchor"


def test_collect_material_field_values_maps_blocked_and_parked_ops_state(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.sync_clickup_queue.ROOT", tmp_path)

    blocked_values = _collect_material_field_values(
        _item(
            topic="blocked_work",
            temp_path="",
            canonical_path="docs/2026-04-12/blocked_work_live_status.md",
            status="blocked",
            queue_role="blocked_holding",
        )
    )
    parked_values = _collect_material_field_values(
        _item(
            topic="parked_work",
            temp_path="",
            canonical_path="docs/2026-04-12/parked_work_live_status.md",
            status="pending",
            queue_role="parked_future_wave",
        )
    )

    assert blocked_values["Ops State"] == "blocked"
    assert parked_values["Ops State"] == "parked"


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
