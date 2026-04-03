from __future__ import annotations

import json
from pathlib import Path

import scripts.rewrite_bi_to_canonical as rewrite_script


def _full_content(label: str) -> dict:
    return {
        "context": f"{label} 배경",
        "event_villain": f"{label} 사건",
        "solution": f"{label} 해결",
        "reward": f"{label} 보상",
    }


def test_canonicalize_bible_payload_upgrades_legacy_shape():
    payload, warnings = rewrite_script.canonicalize_bible_payload(
        {
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {"title": "테스트 작품"},
                    "CoreIdentity": {"protagonist": "주인공"},
                    "protagonist_config": {
                        "world_origin": "현대인",
                        "incarnation_type": "회귀자",
                        "pov": "3인칭",
                        "external_pov_insert_policy": "제한적 허용",
                    },
                }
            },
            "plot_roadmap": [{"block_id": "Block 7", "title": "블록 7", "content": _full_content("본편")}],
        }
    )

    assert payload["MasterBible"]["protagonist_config"]["world_origin"] == "현대인"
    assert payload["MasterBible"]["plot_roadmap"][0]["block_no"] == 7
    assert any("lifted ProjectData.protagonist_config" in warning for warning in warnings)
    assert any("lifted root-level plot_roadmap" in warning for warning in warnings)


def test_rewrite_file_can_write_copy_without_touching_source(tmp_path: Path):
    source = tmp_path / "sample_bi.json"
    source.write_text(
        json.dumps(
            {
                "MasterBible": {
                    "ProjectData": {
                        "MetaInfo": {"title": "테스트 작품"},
                        "CoreIdentity": {"protagonist": "주인공"},
                        "protagonist_config": {
                            "world_origin": "현대인",
                            "incarnation_type": "회귀자",
                            "pov": "3인칭",
                            "external_pov_insert_policy": "제한적 허용",
                        },
                    }
                },
                "plot_roadmap": [{"block_id": "Block 2", "title": "블록 2", "content": _full_content("본편")}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = rewrite_script.rewrite_file(
        source,
        treatment_path=None,
        in_place=False,
        output_dir=None,
        suffix="_canonical_v1",
    )
    copied = Path(result["output"])

    original_payload = json.loads(source.read_text(encoding="utf-8"))
    copied_payload = json.loads(copied.read_text(encoding="utf-8"))

    assert "plot_roadmap" in original_payload
    assert "plot_roadmap" not in copied_payload
    assert copied_payload["MasterBible"]["plot_roadmap"][0]["block_no"] == 2
    assert copied.name == "sample_bi_canonical_v1.json"
