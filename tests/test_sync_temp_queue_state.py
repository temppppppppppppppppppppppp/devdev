import pytest

from pathlib import Path

from scripts.ops_support import queue_items_from_state
from scripts.sync_temp_queue_state import (
    extract_roadmap_item_context,
    infer_item_status,
    infer_roadmap_status,
)


@pytest.mark.parametrize(
    ("raw_status", "expected"),
    [
        ("parked (survey-backed future wave; not active while active Stage4 seams remain)", "pending"),
        ("partially_realized (code landed, static validation closed; runtime closure pending)", "in_progress"),
        ("blocked — Stage4 still paused behind remaining seams", "blocked"),
        ("completed (runtime proof captured; no longer fronts the queue)", "completed"),
    ],
)
def test_infer_item_status_uses_leading_status_instead_of_substring_false_positives(raw_status, expected):
    assert infer_item_status(raw_status) == expected


def test_extract_roadmap_item_context_captures_rank_and_role_from_working_order(tmp_path):
    roadmap = tmp_path / "execution-roadmap.md"
    roadmap.write_text(
        "# Example Roadmap\n\n"
        "Working order:\n\n"
        "1. `stage4-consumer` (aggregate Stage4 wave; PASS proof captured, residual seam narrowed)\n"
        "2. `stage4-repair` (shared repair-contract grammar lane; next open Stage4 substrate after the child-lane closures)\n"
        "3. `readiness-parent` (blocked parent lane; do not reopen S2/S3 while Stage4 front seams remain)\n"
        "4. `stage3-tightening` (parked future wave; explicit canary proof pending)\n"
        "5. `flashback-child` (completed runtime-positive substrate; historical backing only)\n",
        encoding="utf-8",
    )

    context = extract_roadmap_item_context(roadmap)

    assert context["stage4-consumer"] == {"roadmap_rank": 1, "queue_role": "front_active"}
    assert context["stage4-repair"] == {"roadmap_rank": 2, "queue_role": "front_active"}
    assert context["readiness-parent"] == {"roadmap_rank": 3, "queue_role": "blocked_holding"}
    assert context["stage3-tightening"] == {"roadmap_rank": 4, "queue_role": "parked_future_wave"}
    assert context["flashback-child"] == {"roadmap_rank": 5, "queue_role": "historical_backing"}


def test_queue_items_from_state_sorts_by_roadmap_rank():
    state = {
        "items": [
            {
                "topic": "later",
                "temp_path": "docs/temp/later-execution-ssot.md",
                "canonical_path": "docs/2026-04-06/later-execution-ssot.md",
                "status": "pending",
                "queue_role": "parked_future_wave",
                "roadmap_rank": 4,
                "depends_on": [],
                "mirror_present": True,
                "canonical_present": True,
            },
            {
                "topic": "front",
                "temp_path": "docs/temp/front-execution-ssot.md",
                "canonical_path": "docs/2026-04-06/front-execution-ssot.md",
                "status": "in_progress",
                "queue_role": "front_active",
                "roadmap_rank": 1,
                "depends_on": [],
                "mirror_present": True,
                "canonical_present": True,
            },
            {
                "topic": "unranked",
                "temp_path": "docs/temp/unranked-execution-ssot.md",
                "canonical_path": "docs/2026-04-06/unranked-execution-ssot.md",
                "status": "completed",
                "queue_role": "historical_backing",
                "roadmap_rank": None,
                "depends_on": [],
                "mirror_present": True,
                "canonical_present": True,
            },
        ]
    }

    items = queue_items_from_state(state)

    assert [item.topic for item in items] == ["front", "later", "unranked"]


def test_infer_roadmap_status_prefers_active_prefix_before_closure_note(tmp_path):
    roadmap = tmp_path / "execution-roadmap.md"
    roadmap.write_text(
        "# Example Roadmap\n\n"
        "Date: 2026-03-27\n"
        "Status: active (queue reduced; canary wave closed)\n",
        encoding="utf-8",
    )

    assert infer_roadmap_status(roadmap) == "active"
