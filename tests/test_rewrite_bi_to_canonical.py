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


def test_rewrite_file_repairs_runtime_contract_and_reprojects_weak_roadmap(tmp_path: Path):
    sibling = tmp_path / "05_fallen_prince_buys_joseon_bi.json"
    sibling.write_text(
        json.dumps(
            {
                "MasterBible": {
                    "ProjectData": {
                        "MetaInfo": {"title": "테스트 작품", "genre_archetype": "investment"},
                        "CoreIdentity": {"protagonist": "주인공"},
                    },
                    "protagonist_config": {
                        "world_origin": "현대인",
                        "incarnation_type": "회귀자",
                        "pov": "1인칭 제한 시점 (주인공)",
                        "external_pov_insert_policy": "제한적 허용",
                    },
                    "plot_roadmap": [{"block_no": 1, "title": "괜찮은 블록", "content": _full_content("기준")}],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    source = tmp_path / "05_bi_fallen_prince_buys_joseon.json"
    source.write_text(
        json.dumps(
            {
                "MasterBible": {
                    "ProjectData": {
                        "MetaInfo": {"title": "테스트 작품", "genre_archetype": "investment"},
                        "CoreIdentity": {"protagonist": "주인공"},
                    },
                    "protagonist_config": {
                        "world_origin": "대한제국 황자",
                        "incarnation_type": "회귀자",
                    },
                    "plot_roadmap": [{"title": "약한 블록", "summary": "요약만 있음"}],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    treatment = tmp_path / "fallen_prince_buys_joseon_tr_block_070_draft.json"
    treatment.write_text(
        json.dumps(
            [{"block_id": "Block 1", "title": "블록 1", "content": _full_content("본편")}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = rewrite_script.rewrite_file(
        source,
        treatment_path=treatment,
        in_place=False,
        output_dir=None,
        suffix="_canonical_v1",
    )

    copied_payload = json.loads(Path(result["output"]).read_text(encoding="utf-8"))
    protagonist = copied_payload["MasterBible"]["protagonist_config"]

    assert protagonist["pov"] == "1인칭 제한 시점 (주인공)"
    assert protagonist["external_pov_insert_policy"] == "제한적 허용"
    assert copied_payload["MasterBible"]["plot_roadmap"][0]["block_no"] == 1
    assert copied_payload["MasterBible"]["plot_roadmap"][0]["content"]["context"] == "본편 배경"


def test_rewrite_file_infers_missing_runtime_identity_for_regressor(tmp_path: Path):
    source = tmp_path / "02_bi_chaebol_allowance_zero.json"
    source.write_text(
        json.dumps(
            {
                "MasterBible": {
                    "ProjectData": {
                        "MetaInfo": {"title": "테스트 작품", "genre_archetype": "investment"},
                        "CoreIdentity": {"protagonist": "주인공"},
                    },
                    "protagonist_config": {
                        "is_regressor": True,
                        "regression_origin": "망한 미래에서 돌아옴",
                    },
                    "plot_roadmap": [{"block_id": "Block 1", "title": "블록 1", "content": _full_content("본편")}],
                }
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

    copied_payload = json.loads(Path(result["output"]).read_text(encoding="utf-8"))
    protagonist = copied_payload["MasterBible"]["protagonist_config"]

    assert protagonist["world_origin"] == "현대인"
    assert protagonist["incarnation_type"] == "회귀자"
    assert protagonist["pov"] == "3인칭"
    assert protagonist["external_pov_insert_policy"] == "제한적 허용"


def test_rewrite_file_can_force_treatment_roadmap_reprojection(tmp_path: Path):
    source = tmp_path / "0_bi_empire_youngest_allsector.json"
    source.write_text(
        json.dumps(
            {
                "MasterBible": {
                    "ProjectData": {
                        "MetaInfo": {"title": "테스트 작품", "genre_archetype": "investment"},
                        "CoreIdentity": {"protagonist": "주인공"},
                    },
                    "protagonist_config": {
                        "is_regressor": True,
                        "regression_origin": "실패한 미래",
                    },
                    "plot_roadmap": [{"block_no": 1, "title": "기존 블록", "content": _full_content("기존")}],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    treatment = tmp_path / "empire_tr_block_070_draft.json"
    treatment.write_text(
        json.dumps(
            [{"block_id": "Block 1", "title": "교체 블록", "content": _full_content("치환")}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = rewrite_script.rewrite_file(
        source,
        treatment_path=treatment,
        in_place=False,
        output_dir=None,
        suffix="_canonical_v1",
        force_treatment_roadmap=True,
    )

    copied_payload = json.loads(Path(result["output"]).read_text(encoding="utf-8"))

    assert copied_payload["MasterBible"]["plot_roadmap"][0]["title"] == "교체 블록"
    assert any("force-replaced plot_roadmap" in warning for warning in result["warnings"])
