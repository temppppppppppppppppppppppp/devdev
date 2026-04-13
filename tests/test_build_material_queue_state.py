from __future__ import annotations

import json
from pathlib import Path

from scripts.build_material_queue_state import build_material_queue_payload


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_build_material_queue_payload_classifies_active_and_complete(tmp_path):
    preprocess_root = tmp_path / "treatments" / "preprocess"
    docs_root = tmp_path / "docs" / "2026-04-12"
    canon_root = tmp_path / "material_ssot" / "20_pitch" / "canon"
    docs_root.mkdir(parents=True, exist_ok=True)
    canon_root.mkdir(parents=True, exist_ok=True)

    _write_json(
        preprocess_root / "empire_youngest_allsector" / "sequential_run_status.json",
        {
            "work_id": "empire_youngest_allsector",
            "next_unit_type": "bi_handoff",
            "last_sequential_block_pass": 70,
        },
    )
    _write_json(
        preprocess_root / "smart_new_hire" / "sequential_run_status.json",
        {
            "work_id": "smart_new_hire",
            "next_unit_type": "complete",
            "production_complete": True,
            "bi_complete": True,
            "last_sequential_block_pass": 70,
        },
    )
    (docs_root / "empire_youngest_allsector_live_status.md").write_text("# status\n", encoding="utf-8")
    (docs_root / "smart_new_hire_live_status.md").write_text("# status\n", encoding="utf-8")
    (canon_root / "africa_farm_king.md").write_text("# canon\n", encoding="utf-8")

    from scripts import build_material_queue_state as module

    old_root = module.ROOT
    old_canon_root = module.CANON_ROOT
    old_registry_json = module.REGISTRY_JSON
    try:
        module.ROOT = tmp_path
        module.CANON_ROOT = canon_root
        module.REGISTRY_JSON = tmp_path / "missing_registry.json"
        payload = build_material_queue_payload(preprocess_root)
    finally:
        module.ROOT = old_root
        module.CANON_ROOT = old_canon_root
        module.REGISTRY_JSON = old_registry_json

    assert payload["queue_mode"] == "aggregate"
    assert payload["active_item_count"] == 2
    assert [item["topic"] for item in payload["items"]] == [
        "africa_farm_king",
        "empire_youngest_allsector",
        "smart_new_hire",
    ]
    assert payload["items"][0]["status"] == "pending"
    assert payload["items"][0]["queue_role"] == "front_active"
    assert payload["items"][0]["material_stage"] == "canon_stage"
    assert payload["items"][0]["canonical_path"].endswith("africa_farm_king.md")
    assert payload["items"][1]["status"] == "in_progress"
    assert payload["items"][1]["material_stage"] == "tr_or_bi_production"
    assert payload["items"][1]["canonical_path"].endswith("empire_youngest_allsector_live_status.md")
    assert payload["items"][2]["status"] == "completed"
    assert payload["items"][2]["material_stage"] == "bi_production_complete"


def test_build_material_queue_payload_can_include_completed(tmp_path):
    preprocess_root = tmp_path / "treatments" / "preprocess"
    docs_root = tmp_path / "docs" / "2026-04-12"
    docs_root.mkdir(parents=True, exist_ok=True)

    _write_json(
        preprocess_root / "empire_youngest_allsector" / "sequential_run_status.json",
        {
            "work_id": "empire_youngest_allsector",
            "next_unit_type": "bi_handoff",
            "last_sequential_block_pass": 70,
        },
    )
    _write_json(
        preprocess_root / "smart_new_hire" / "sequential_run_status.json",
        {
            "work_id": "smart_new_hire",
            "next_unit_type": "complete",
            "production_complete": True,
            "bi_complete": True,
            "last_sequential_block_pass": 70,
        },
    )
    (docs_root / "empire_youngest_allsector_live_status.md").write_text("# status\n", encoding="utf-8")
    (docs_root / "smart_new_hire_live_status.md").write_text("# status\n", encoding="utf-8")

    from scripts import build_material_queue_state as module

    old_root = module.ROOT
    old_registry_json = module.REGISTRY_JSON
    try:
        module.ROOT = tmp_path
        module.REGISTRY_JSON = tmp_path / "missing_registry.json"
        payload = build_material_queue_payload(preprocess_root, include_completed=True)
    finally:
        module.ROOT = old_root
        module.REGISTRY_JSON = old_registry_json

    assert [item["topic"] for item in payload["items"]] == [
        "empire_youngest_allsector",
        "smart_new_hire",
    ]
    assert payload["items"][1]["status"] == "completed"
    assert payload["items"][1]["queue_role"] == "historical_backing"


def test_build_material_queue_payload_active_only_excludes_completed(tmp_path):
    preprocess_root = tmp_path / "treatments" / "preprocess"
    docs_root = tmp_path / "docs" / "2026-04-12"
    docs_root.mkdir(parents=True, exist_ok=True)

    _write_json(
        preprocess_root / "empire_youngest_allsector" / "sequential_run_status.json",
        {
            "work_id": "empire_youngest_allsector",
            "next_unit_type": "bi_handoff",
            "last_sequential_block_pass": 70,
        },
    )
    _write_json(
        preprocess_root / "smart_new_hire" / "sequential_run_status.json",
        {
            "work_id": "smart_new_hire",
            "next_unit_type": "complete",
            "production_complete": True,
            "bi_complete": True,
            "last_sequential_block_pass": 70,
        },
    )
    (docs_root / "empire_youngest_allsector_live_status.md").write_text("# status\n", encoding="utf-8")
    (docs_root / "smart_new_hire_live_status.md").write_text("# status\n", encoding="utf-8")

    from scripts import build_material_queue_state as module

    old_root = module.ROOT
    old_registry_json = module.REGISTRY_JSON
    try:
        module.ROOT = tmp_path
        module.REGISTRY_JSON = tmp_path / "missing_registry.json"
        payload = build_material_queue_payload(preprocess_root, include_completed=False)
    finally:
        module.ROOT = old_root
        module.REGISTRY_JSON = old_registry_json

    assert [item["topic"] for item in payload["items"]] == ["empire_youngest_allsector"]
