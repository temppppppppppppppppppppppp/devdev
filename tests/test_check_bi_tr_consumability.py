import json
from pathlib import Path

import scripts.check_bi_tr_consumability as consumability


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _valid_bible(plot_roadmap=None, protagonist_config=None):
    master = {"ProjectData": {"MetaInfo": {"title": "테스트 작품"}}}
    if plot_roadmap is not None:
        master["plot_roadmap"] = plot_roadmap
    if protagonist_config is not None:
        master["protagonist_config"] = protagonist_config
    return {"MasterBible": master}


def _full_content(label: str) -> dict:
    return {
        "context": f"{label} 배경",
        "event_villain": f"{label} 사건",
        "solution": f"{label} 해결",
        "reward": f"{label} 보상",
    }


def test_inspect_pair_marks_pair_pass_when_tr_is_stage2_ready(tmp_path):
    bible_path = tmp_path / "bible" / "_quarantine" / "07_demo_work_bi.json"
    treatment_path = tmp_path / "treatments" / "_quarantine" / "07_demo_work_tr_block_070_draft.json"
    _write_json(
        bible_path,
        _valid_bible(
            plot_roadmap=[{"title": "블록 1", "content": _full_content("사전")}],
            protagonist_config={"world_origin": "현대"},
        ),
    )
    _write_json(
        treatment_path,
        {
            "blocks": [
                {
                    "block_id": "Block 7",
                    "title": "본편 시작",
                    "content": _full_content("본편"),
                }
            ]
        },
    )

    result = consumability.inspect_pair(bible_path=bible_path, treatment_path=treatment_path)

    assert result.verdicts["tr_consumability"] == "pass"
    assert result.verdicts["bi_standalone_roadmap_readiness"] == "mixed"
    assert result.verdicts["pair_consumability"] == "pass"
    assert result.verdicts["pair_canonical_contract"] == "fail"
    assert result.salvage_ready is True
    assert result.canonical_block_count == 1
    assert result.bible_canonical_valid is False
    assert result.treatment_canonical_valid is False
    assert result.normalized_bible_canonical_valid is False
    assert result.normalized_treatment_canonical_valid is True
    assert result.normalized_pair_canonical_valid is False
    assert result.runtime_protagonist_keys_missing == [
        "incarnation_type",
        "pov",
        "external_pov_insert_policy",
    ]


def test_inspect_pair_fails_when_treatment_shape_is_not_consumable(tmp_path):
    bible_path = tmp_path / "bible" / "_quarantine" / "0_bi_broken_work.json"
    treatment_path = tmp_path / "treatments" / "_quarantine" / "broken_work_tr_block_070_draft.json"
    _write_json(bible_path, _valid_bible())
    _write_json(treatment_path, {"unexpected": []})

    result = consumability.inspect_pair(bible_path=bible_path, treatment_path=treatment_path)

    assert result.verdicts["tr_consumability"] == "fail"
    assert result.verdicts["pair_consumability"] == "fail"
    assert result.salvage_ready is False
    assert result.treatment_errors


def test_scan_quarantine_pairs_bi_with_preferred_treatment_and_reports_orphan_tr(tmp_path):
    bible_dir = tmp_path / "bible" / "_quarantine"
    treatment_dir = tmp_path / "treatments" / "_quarantine"
    _write_json(
        bible_dir / "0_bi_sample_work.json",
        _valid_bible(protagonist_config={"world_origin": "현대", "pov": "3인칭"}),
    )
    _write_json(
        treatment_dir / "07_sample_work_tr_block_010_candidate.json",
        {"treatments": [{"title": "후보", "content": _full_content("후보")}]},
    )
    _write_json(
        treatment_dir / "07_sample_work_tr_block_070_draft.json",
        {"blocks": [{"title": "최종", "content": _full_content("최종")}]},
    )
    _write_json(
        treatment_dir / "orphan_story_tr_block_070_draft.json",
        {"blocks": [{"title": "고아", "content": _full_content("고아")}]},
    )

    results = consumability.scan_quarantine(bible_dir, treatment_dir)

    sample = next(result for result in results if result.work_key == "sample_work")
    orphan = next(result for result in results if result.work_key == "orphan_story")
    assert sample.treatment_path.endswith("07_sample_work_tr_block_070_draft.json")
    assert sample.verdicts["pair_consumability"] == "pass"
    assert sample.verdicts["pair_canonical_contract"] == "fail"
    assert orphan.bible_path is None
    assert orphan.verdicts["pair_consumability"] == "fail"


def test_inspect_pair_marks_canonical_pass_when_raw_bi_and_tr_are_canonical(tmp_path):
    bible_path = tmp_path / "bible" / "_quarantine" / "01_canonical_work_bi.json"
    treatment_path = tmp_path / "treatments" / "_quarantine" / "canonical_work_tr_block_070_draft.json"
    _write_json(
        bible_path,
        {
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {"title": "정본 작품"},
                    "CoreIdentity": {"protagonist": "주인공"},
                },
                "protagonist_config": {
                    "world_origin": "현대인",
                    "incarnation_type": "회귀자",
                    "pov": "3인칭",
                    "external_pov_insert_policy": "제한적 허용",
                },
                "plot_roadmap": [
                    {
                        "block_no": 1,
                        "title": "정본 블록 1",
                        "content": _full_content("정본"),
                    }
                ],
            }
        },
    )
    _write_json(
        treatment_path,
        {
            "_schema": "tr.v1",
            "_total_blocks": 1,
            "blocks": [
                {
                    "block_no": 1,
                    "title": "정본 블록 1",
                    "content": _full_content("정본"),
                }
            ],
        },
    )

    result = consumability.inspect_pair(bible_path=bible_path, treatment_path=treatment_path)

    assert result.verdicts["pair_consumability"] == "pass"
    assert result.verdicts["pair_canonical_contract"] == "pass"
    assert result.verdicts["normalized_pair_canonical_view"] == "pass"
    assert result.bible_canonical_valid is True
    assert result.treatment_canonical_valid is True
    assert result.pair_canonical_valid is True
    assert result.normalized_bible_canonical_valid is True
    assert result.normalized_treatment_canonical_valid is True
    assert result.normalized_pair_canonical_valid is True
    assert result.bible_canonical_errors == []
    assert result.treatment_canonical_errors == []


def test_text_report_includes_canonical_contract_status(capsys, tmp_path):
    bible_path = tmp_path / "bible" / "_quarantine" / "01_canonical_work_bi.json"
    treatment_path = tmp_path / "treatments" / "_quarantine" / "canonical_work_tr_block_070_draft.json"
    _write_json(
        bible_path,
        {
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {"title": "정본 작품"},
                    "CoreIdentity": {"protagonist": "주인공"},
                },
                "protagonist_config": {
                    "world_origin": "현대인",
                    "incarnation_type": "회귀자",
                    "pov": "3인칭",
                    "external_pov_insert_policy": "제한적 허용",
                },
                "plot_roadmap": [
                    {
                        "block_no": 1,
                        "title": "정본 블록 1",
                        "content": _full_content("정본"),
                    }
                ],
            }
        },
    )
    _write_json(
        treatment_path,
        {
            "_schema": "tr.v1",
            "_total_blocks": 1,
            "blocks": [
                {
                    "block_no": 1,
                    "title": "정본 블록 1",
                    "content": _full_content("정본"),
                }
            ],
        },
    )

    result = consumability.inspect_pair(bible_path=bible_path, treatment_path=treatment_path)
    consumability._print_text_report([result])
    out = capsys.readouterr().out

    assert "canonical-pair=1" in out
    assert "normalized-canonical-pair=1" in out
    assert "canonical=pass (tr=pass, bi=pass)" in out
    assert "normalized=pass (tr=pass, bi=pass)" in out
