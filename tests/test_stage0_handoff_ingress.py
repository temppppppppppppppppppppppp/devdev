import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.project_manager import ProjectContext
from modules.core.response_schemas import validate_phase0_files, validate_treatment_structure
from modules.core.stage0_handoff import build_plot_roadmap_from_treatment


def _valid_bible():
    return {"MasterBible": {"ProjectData": {"MetaInfo": {"title": "테스트 작품"}}}}


def _full_content(label: str) -> dict:
    return {
        "context": f"{label} 배경",
        "event_villain": f"{label} 적대 사건",
        "solution": f"{label} 해결",
        "reward": f"{label} 보상",
    }


def test_validate_treatment_structure_accepts_existing_list_path():
    treatment = [{"title": "블록 1", "content": _full_content("도입")}]

    valid, errors, warnings = validate_treatment_structure(treatment)

    assert valid is True
    assert errors == []
    assert warnings == []
    roadmap = build_plot_roadmap_from_treatment(treatment)
    assert roadmap[0]["block_no"] == 1


def test_dict_blocks_treatment_normalizes_to_stage2_ready_roadmap():
    treatment = {
        "blocks": [
            {
                "block_id": "Block 7",
                "title": "화산 입문",
                "content": _full_content("입문"),
                "genre_ext": {"realm": "삼류"},
            }
        ]
    }

    valid, errors, warnings = validate_treatment_structure(treatment)

    assert valid is True
    assert errors == []
    assert warnings == []
    roadmap = build_plot_roadmap_from_treatment(treatment)
    assert len(roadmap) == 1
    assert roadmap[0]["block_no"] == 7
    assert roadmap[0]["content"]["context"] == "입문 배경"
    assert roadmap[0]["genre_ext"]["realm"] == "삼류"


def test_dict_treatments_normalizes_and_reports_block_count():
    treatment = {
        "treatments": [
            {"title": "블록 1", "content": _full_content("전개")},
            {"title": "블록 2", "content": _full_content("후반"), "block": "Block 12"},
        ]
    }

    valid, report = validate_phase0_files(_valid_bible(), treatment)

    assert valid is True
    assert report["treatment"]["block_count"] == 2
    roadmap = build_plot_roadmap_from_treatment(treatment)
    assert [entry["block_no"] for entry in roadmap] == [1, 12]


def test_build_plot_roadmap_guarantees_block_no_with_enumeration_fallback():
    treatment = {"blocks": [{"title": "무명 블록", "content": _full_content("기승")}]}

    roadmap = build_plot_roadmap_from_treatment(treatment)

    assert roadmap[0]["block_no"] == 1


def test_force_sync_v25_dna_uses_normalized_block_list(tmp_path):
    workspace_root = tmp_path
    (workspace_root / "bible").mkdir()
    (workspace_root / "treatments").mkdir()
    project_root = workspace_root / "projects" / "demo"
    project_root.mkdir(parents=True)

    bible_path = workspace_root / "bible" / "bible.json"
    bible_path.write_text(json.dumps(_valid_bible(), ensure_ascii=False), encoding="utf-8")

    treatment_path = workspace_root / "treatments" / "treatment.json"
    treatment_path.write_text(
        json.dumps(
            {
                "blocks": [
                    {
                        "block_id": "Block 9",
                        "title": "의술 개안",
                        "content": _full_content("각성"),
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    ctx = SimpleNamespace(
        paths=SimpleNamespace(root=project_root),
        save_v20_anchor=MagicMock(return_value=True),
        master_bible={},
    )

    result = ProjectContext.force_sync_v25_dna(ctx, "bible.json", "treatment.json")

    assert result is True
    roadmap = ctx.master_bible["MasterBible"]["plot_roadmap"]
    assert len(roadmap) == 1
    assert roadmap[0]["block_no"] == 9
    assert roadmap[0]["title"] == "의술 개안"
    ctx.save_v20_anchor.assert_called_once_with("bible", ctx.master_bible)
