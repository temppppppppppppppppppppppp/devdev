from modules.core.response_schemas import (
    validate_bible_canonical_structure,
    validate_treatment_canonical_structure,
)
from modules.core.stage0_handoff import (
    STAGE0_RUNTIME_HANDOFF_KEY,
    build_plot_roadmap_lineage,
    build_stage0_runtime_handoff_summary,
    canonicalize_bible_payload,
    canonicalize_treatment_payload,
    normalize_bible_to_canonical_view,
    normalize_treatment_to_canonical_view,
    plot_roadmap_lineage_matches,
    resolve_stage0_bible_contract,
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


def test_canonicalize_treatment_payload_promotes_tr_v1_contract():
    payload, warnings = canonicalize_treatment_payload(
        [{"block_id": "Block 4", "title": "블록 4", "content": _full_content("정규화")}]
    )

    assert payload["_schema"] == "tr.v1"
    assert payload["_total_blocks"] == 1
    assert payload["blocks"][0]["block_no"] == 4
    assert payload["_stage0_contract"]["artifact_role"] == "canonical_material_source"
    assert payload["_stage0_contract"]["artifact_truth"] == "treatment.blocks"
    assert payload["_stage0_contract"]["runtime_handoff"]["owner"] == "db_anchor:bible"
    assert any("raw list wrapper" in warning for warning in warnings)


def test_canonicalize_bible_payload_repairs_runtime_contract_and_strips_sidecars():
    legacy_bible = {
        "_genre": "wuxia",
        "MasterBible": {
            "ProjectData": {
                "MetaInfo": {"title": "테스트 작품"},
                "CoreIdentity": {"protagonist": "주인공"},
                "protagonist_config": {},
            }
        },
        "plot_roadmap": [{"block_id": "Block 1", "title": "블록 1", "content": _full_content("본편")}],
    }

    payload, warnings = canonicalize_bible_payload(legacy_bible, genre_hint="wuxia")

    protagonist = payload["MasterBible"]["protagonist_config"]
    assert protagonist["world_origin"] == "원시인"
    assert protagonist["incarnation_type"] == "일반"
    assert protagonist["pov"] == "3인칭"
    assert protagonist["external_pov_insert_policy"] == "제한적 허용"
    assert "plot_roadmap" not in payload
    assert "protagonist_config" not in payload["MasterBible"]["ProjectData"]
    assert payload["_stage0_contract"]["artifact_role"] == "bi_projection_artifact"
    assert payload["_stage0_contract"]["field_authority"]["plot_roadmap"] == "MasterBible.plot_roadmap"
    assert payload["_stage0_contract"]["runtime_handoff"]["owner"] == "db_anchor:bible"
    assert payload["_stage0_contract"]["projection_source"] == "treatment.blocks"
    handoff = payload[STAGE0_RUNTIME_HANDOFF_KEY]
    assert handoff["runtime_handoff_owner"] == "db_anchor:bible"
    assert handoff["runtime_handoff_surface"] == "MasterBible.plot_roadmap"
    assert handoff["stage2_consumer_mode"] == "db_anchor_first"
    assert handoff["projection_source"] == "treatment.blocks"
    assert handoff["plot_roadmap_authority"] == "MasterBible.plot_roadmap"
    assert handoff["persistence_call"] == "save_v20_anchor:bible"
    assert handoff["compatibility_bridges"]["force_sync_v25_dna"] == "compatibility_bridge"
    assert any("filled protagonist_config.world_origin='원시인'" in warning for warning in warnings)


def test_resolve_stage0_bible_contract_falls_back_to_default_runtime_owner():
    contract = resolve_stage0_bible_contract({"MasterBible": {"plot_roadmap": [{"block_no": 1}]}})

    assert contract["artifact_role"] == "bi_projection_artifact"
    assert contract["runtime_handoff"]["owner"] == "db_anchor:bible"
    assert contract["field_authority"]["protagonist_config"] == "MasterBible.protagonist_config"


def test_stage0_runtime_handoff_summary_distinguishes_owner_from_projection_source():
    bible = {
        "_stage0_contract": {
            "artifact_role": "bi_projection_artifact",
            "projection_source": "treatment.blocks",
            "field_authority": {"plot_roadmap": "MasterBible.plot_roadmap"},
            "runtime_handoff": {"owner": "db_anchor:bible"},
        },
        "MasterBible": {"plot_roadmap": [{"block_no": 1}]},
    }

    summary = build_stage0_runtime_handoff_summary(bible)

    assert summary["runtime_handoff_owner"] == "db_anchor:bible"
    assert summary["runtime_handoff_anchor"] == "bible"
    assert summary["runtime_handoff_surface"] == "MasterBible.plot_roadmap"
    assert summary["stage2_consumer_mode"] == "db_anchor_first"
    assert summary["projection_source"] == "treatment.blocks"
    assert summary["compatibility_bridges"]["force_sync_v25_dna"] == "compatibility_bridge"


def test_plot_roadmap_lineage_matches_same_source_and_rejects_changed_content():
    roadmap = [
        {
            "block_no": "1",
            "title": "Block 1",
            "content": {
                "context": "ctx",
                "event_villain": "villain",
                "solution": "solve",
                "reward": "reward",
            },
        }
    ]
    same_roadmap = [
        {
            "title": "Block 1",
            "block_no": 1,
            "content": {
                "reward": "reward",
                "solution": "solve",
                "event_villain": "villain",
                "context": "ctx",
            },
        }
    ]
    changed_roadmap = [
        {
            "block_no": 1,
            "title": "Block 1",
            "content": {
                "context": "ctx",
                "event_villain": "villain",
                "solution": "solve",
                "reward": "changed reward",
            },
        }
    ]

    lineage = build_plot_roadmap_lineage(roadmap)
    same_lineage = build_plot_roadmap_lineage(same_roadmap)
    changed_lineage = build_plot_roadmap_lineage(changed_roadmap)

    assert lineage["schema"] == "stage0.plot_roadmap_lineage.v1"
    assert lineage["block_count"] == 1
    assert plot_roadmap_lineage_matches(lineage, same_lineage) is True
    assert plot_roadmap_lineage_matches(lineage, changed_lineage) is False
