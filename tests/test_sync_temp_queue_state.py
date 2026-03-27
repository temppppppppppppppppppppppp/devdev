from pathlib import Path

from scripts.sync_temp_queue_state import infer_roadmap_status


def test_infer_roadmap_status_prefers_active_prefix_before_closure_note(tmp_path):
    roadmap = tmp_path / "execution-roadmap.md"
    roadmap.write_text(
        "# Example Roadmap\n\n"
        "Date: 2026-03-27\n"
        "Status: active (queue reduced; canary wave closed)\n",
        encoding="utf-8",
    )

    assert infer_roadmap_status(roadmap) == "active"
