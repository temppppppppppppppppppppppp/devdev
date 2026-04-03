from modules.core.response_schemas import (
    validate_bible_canonical_structure,
    validate_treatment_canonical_structure,
)
from modules.core.stage0_handoff import (
    normalize_bible_to_canonical_view,
    normalize_treatment_to_canonical_view,
)


def _full_content(label: str) -> dict:
    return {
        "context": f"{label} 배경",
        "event_villain": f"{label} 적대 사건",
        "solution": f"{label} 해결",
        "reward": f"{label} 보상",
    }


def test_normalize_bible_to_canonical_view_lifts_runtime_fields_and_root_sidecar():
    bible = {
        "_schema_version": "2.0",
        "MasterBible": {
            "ProjectData": {
                "MetaInfo": {"title": "테스트 작품"},
                "CoreIdentity": {"protagonist": "주인공"},
                "protagonist_config": {
                    "world_origin": "현대인",
                    "incarnation_type": "회귀자",
                    "pov": "혼합",
                    "external_pov_insert_policy": "제한적 허용",
                },
            }
        },
        "plot_roadmap": [{"block_id": "Block 7", "title": "블록 7", "content": _full_content("도입")}],
    }

    canonical, warnings = normalize_bible_to_canonical_view(bible)

    assert canonical["MasterBible"]["protagonist_config"]["world_origin"] == "현대인"
    assert canonical["MasterBible"]["plot_roadmap"][0]["block_no"] == 7
    assert any("lifted ProjectData.protagonist_config" in warning for warning in warnings)
    assert any("lifted root-level plot_roadmap" in warning for warning in warnings)


def test_normalize_bible_to_canonical_view_projects_plot_roadmap_from_treatment():
    bible = {
        "MasterBible": {
            "ProjectData": {
                "MetaInfo": {"title": "테스트 작품"},
                "CoreIdentity": {"protagonist": "주인공"},
            },
            "protagonist_config": {
                "world_origin": "현대인",
                "incarnation_type": "회귀자",
                "pov": "혼합",
                "external_pov_insert_policy": "제한적 허용",
            },
        }
    }
    treatment = {"blocks": [{"block_id": "Block 3", "title": "블록 3", "content": _full_content("본편")}]}

    canonical, warnings = normalize_bible_to_canonical_view(bible, treatment=treatment)

    assert canonical["MasterBible"]["plot_roadmap"][0]["block_no"] == 3
    assert any("projected plot_roadmap from treatment" in warning for warning in warnings)


def test_normalize_treatment_to_canonical_view_wraps_raw_list():
    treatment = [{"block_id": "Block 2", "title": "블록 2", "content": _full_content("전개")}]

    canonical, warnings = normalize_treatment_to_canonical_view(treatment)

    assert canonical["_schema"] == "tr.compat"
    assert canonical["_total_blocks"] == 1
    assert canonical["blocks"][0]["block_no"] == 2
    assert any("raw list wrapper" in warning for warning in warnings)


def test_validate_bible_canonical_structure_accepts_stage2_ready_shape():
    bible = {
        "MasterBible": {
            "ProjectData": {
                "MetaInfo": {"title": "테스트 작품"},
                "CoreIdentity": {"protagonist": "주인공"},
            },
            "protagonist_config": {
                "world_origin": "현대인",
                "incarnation_type": "회귀자",
                "pov": "혼합",
                "external_pov_insert_policy": "제한적 허용",
            },
            "plot_roadmap": [{"block_no": 1, "title": "블록 1", "content": _full_content("본편")}],
        }
    }

    valid, errors, warnings = validate_bible_canonical_structure(bible)

    assert valid is True
    assert errors == []
    assert warnings == []


def test_validate_bible_canonical_structure_rejects_legacy_sidecar_shape():
    legacy_bible = {
        "MasterBible": {
            "ProjectData": {
                "MetaInfo": {"title": "테스트 작품"},
                "CoreIdentity": {"protagonist": "주인공"},
                "protagonist_config": {
                    "world_origin": "현대인",
                    "incarnation_type": "회귀자",
                },
            }
        },
        "plot_roadmap": [{"block_id": "Block 1", "title": "블록 1", "content": _full_content("본편")}],
    }

    valid, errors, _warnings = validate_bible_canonical_structure(legacy_bible)

    assert valid is False
    assert "Canonical BI requires MasterBible.protagonist_config dict" in errors
    assert "Canonical BI requires MasterBible.plot_roadmap" in errors


def test_validate_treatment_canonical_structure_requires_blocks_wrapper_and_block_no():
    raw_list_valid, raw_list_errors, _ = validate_treatment_canonical_structure(
        [{"block_id": "Block 1", "title": "블록 1", "content": _full_content("본편")}]
    )
    assert raw_list_valid is False
    assert raw_list_errors == ["Canonical TR requires dict wrapper with blocks"]

    wrapped_missing_block_no = {
        "blocks": [{"title": "블록 1", "content": _full_content("본편")}],
        "_total_blocks": 1,
    }
    wrapped_valid, wrapped_errors, _ = validate_treatment_canonical_structure(wrapped_missing_block_no)

    assert wrapped_valid is False
    assert any("block_no missing" in error for error in wrapped_errors)

    canonical_treatment = {
        "_schema": "tr.v1",
        "_total_blocks": 1,
        "blocks": [{"block_no": 1, "title": "블록 1", "content": _full_content("본편")}],
    }
    canonical_valid, canonical_errors, canonical_warnings = validate_treatment_canonical_structure(canonical_treatment)

    assert canonical_valid is True
    assert canonical_errors == []
    assert canonical_warnings == []
