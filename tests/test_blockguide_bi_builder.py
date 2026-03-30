from __future__ import annotations

import json
import sys

import scripts.build_bi_from_phase0_and_tr as build_script


def _build_phase0() -> dict:
    return {
        "project": {"title_ko": "테스트 프로젝트", "format": "investment"},
        "setting": {"starter_company": {"name": "테스트컴퍼니"}},
        "protagonist": {"name": "주인공"},
        "phase0_design": {
            "arcs": [],
            "npc_timeline": [],
            "foreshadow_map": [],
            "opponent_transition_plan": [],
        },
    }


def _build_blocks() -> list[dict]:
    return [{"block_id": f"Block {idx}", "title": f"테스트 블록 {idx}"} for idx in range(1, 71)]


def test_blockguide_bi_main_accepts_wrapped_draft_input(monkeypatch, temp_dir) -> None:
    phase0_path = temp_dir / "phase0.json"
    draft_path = temp_dir / "draft.json"
    output_path = temp_dir / "bi.json"

    phase0 = _build_phase0()
    blocks = _build_blocks()
    phase0_path.write_text(json.dumps(phase0, ensure_ascii=False, indent=2), encoding="utf-8")
    draft_path.write_text(json.dumps({"blocks": blocks}, ensure_ascii=False, indent=2), encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_normalize_phase0_design(phase0_design: dict, treatment_blocks: list[dict]) -> dict:
        captured["normalized_blocks"] = treatment_blocks
        return phase0_design

    def fake_build_bible(payload: dict, treatment_blocks: list[dict]) -> dict:
        captured["build_blocks"] = treatment_blocks
        return {
            "MasterBible": {
                "ProjectData": {"CoreIdentity": {"protagonist": "주인공"}},
                "FinanceHUD": {"Protagonist": {"actual_truth": {"name": "주인공"}}},
                "plot_roadmap": treatment_blocks,
            }
        }

    monkeypatch.setattr(build_script, "normalize_phase0_design", fake_normalize_phase0_design)
    monkeypatch.setattr(build_script, "build_bible", fake_build_bible)
    monkeypatch.setattr(build_script, "validate_treatment_structure", lambda _: (True, [], []))
    monkeypatch.setattr(build_script, "validate_bible_structure", lambda _: (True, [], []))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_bi_from_phase0_and_tr.py",
            "--phase0",
            str(phase0_path),
            "--draft",
            str(draft_path),
            "--output",
            str(output_path),
        ],
    )

    exit_code = build_script.main()

    assert exit_code == 0
    assert output_path.exists()
    assert captured["normalized_blocks"] == blocks
    assert captured["build_blocks"] == blocks
