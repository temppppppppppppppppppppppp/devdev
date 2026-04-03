from __future__ import annotations

from pathlib import Path

from scripts.process_and_audit_tr_bi_loop import PairAudit, compute_canonical_contract_status, write_report


def _full_content(label: str) -> dict:
    return {
        "context": f"{label} 배경",
        "event_villain": f"{label} 적대 사건",
        "solution": f"{label} 해결",
        "reward": f"{label} 보상",
    }


def test_compute_canonical_contract_status_reports_raw_fail_but_normalized_pass():
    treatment = [{"block_id": "Block 1", "title": "블록 1", "content": _full_content("본편")}]
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

    status, notes = compute_canonical_contract_status(treatment, bible)

    assert status["raw_bi_canonical_contract"] is True
    assert status["raw_tr_canonical_contract"] is False
    assert status["raw_pair_canonical_contract"] is False
    assert status["normalized_bi_canonical_view"] is True
    assert status["normalized_tr_canonical_view"] is True
    assert status["normalized_pair_canonical_view"] is True
    assert any("raw_tr_canonical_errors" in note for note in notes)
    assert any("tr_normalization_warnings" in note for note in notes)


def test_write_report_includes_canonical_contract_section(tmp_path: Path):
    out_path = tmp_path / "loop-report.md"
    pair = PairAudit(
        key="sample_work",
        bi_name="sample_bi.json",
        confidence=95.0,
        checks={"bi_valid_schema": True, "cross_edge_title_match": False},
        notes=["legacy note"],
        canonical_checks={
            "raw_bi_canonical_contract": True,
            "raw_tr_canonical_contract": False,
            "raw_pair_canonical_contract": False,
            "normalized_bi_canonical_view": True,
            "normalized_tr_canonical_view": True,
            "normalized_pair_canonical_view": True,
        },
        canonical_notes=["raw_tr_canonical_errors[1]: Canonical TR requires dict wrapper with blocks"],
    )

    write_report(
        history=[
            {
                "iteration": 1,
                "round_confidences": [95.0, 95.0, 95.0],
                "stable_confidence": 95.0,
                "pairs": [pair],
            }
        ],
        final_confidence=95.0,
        success=False,
        out_path=out_path,
    )

    report = out_path.read_text(encoding="utf-8")

    assert "- canonical_contract:" in report
    assert "- raw_pair_canonical_contract: FAIL" in report
    assert "- normalized_pair_canonical_view: OK" in report
    assert "- canonical_note: raw_tr_canonical_errors[1]: Canonical TR requires dict wrapper with blocks" in report
