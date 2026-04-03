from __future__ import annotations

import json
from pathlib import Path

import scripts.rewrite_tr_to_canonical as rewrite_script


def _full_content(label: str) -> dict:
    return {
        "context": f"{label} 배경",
        "event_villain": f"{label} 사건",
        "solution": f"{label} 해결",
        "reward": f"{label} 보상",
    }


def test_canonicalize_treatment_payload_upgrades_raw_list():
    payload, warnings = rewrite_script.canonicalize_treatment_payload(
        [{"block_id": "Block 7", "title": "블록 7", "content": _full_content("본편")}]
    )

    assert payload["_schema"] == "tr.v1"
    assert payload["_total_blocks"] == 1
    assert payload["blocks"][0]["block_no"] == 7
    assert any("raw list wrapper" in warning for warning in warnings)


def test_rewrite_file_can_write_copy_without_touching_source(tmp_path: Path):
    source = tmp_path / "sample_tr_block_070_draft.json"
    source.write_text(
        json.dumps([{"block_id": "Block 2", "title": "블록 2", "content": _full_content("본편")}], ensure_ascii=False),
        encoding="utf-8",
    )

    result = rewrite_script.rewrite_file(source, in_place=False, output_dir=None, suffix="_canonical_v1")
    copied = Path(result["output"])

    original_payload = json.loads(source.read_text(encoding="utf-8"))
    copied_payload = json.loads(copied.read_text(encoding="utf-8"))

    assert isinstance(original_payload, list)
    assert copied_payload["_schema"] == "tr.v1"
    assert copied_payload["blocks"][0]["block_no"] == 2
    assert copied.name == "sample_tr_block_070_draft_canonical_v1.json"
