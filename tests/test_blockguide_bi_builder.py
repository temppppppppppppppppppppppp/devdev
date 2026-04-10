from __future__ import annotations

import json
import sys

import scripts.build_bi_from_phase0_and_tr as build_script


def _build_phase0() -> dict:
    return {
        "project": {"title_ko": "Test Project", "format": "investment"},
        "setting": {"starter_company": {"name": "Test Holdings"}},
        "protagonist": {"name": "Hero"},
        "phase0_design": {
            "arcs": [],
            "npc_timeline": [],
            "foreshadow_map": [],
            "opponent_transition_plan": [],
        },
    }


def _full_content(label: str) -> dict:
    return {
        "context": f"{label} context",
        "event_villain": f"{label} incident",
        "solution": f"{label} solution",
        "reward": f"{label} reward",
    }


def _build_blocks() -> list[dict]:
    return [
        {
            "block_id": f"Block {idx}",
            "title": f"Test Block {idx}",
            "content": _full_content(f"Block {idx}"),
        }
        for idx in range(1, 71)
    ]


def _build_phase0_for_real_bible() -> dict:
    return {
        "project": {
            "title_ko": "Test Project",
            "format": "investment",
            "logline": "A young operator rebuilds the family company.",
            "start_year": 2012,
            "end_year": 2026,
            "core_premise": "Rebuild the company through contracts and capital flow.",
        },
        "work_identity_surface": {
            "work_id": "test_project",
            "title": "Golden Route",
            "subtitle": "",
            "commercial_label": "Golden Canary",
            "slug_aliases": ["canary test", "test_project_legacy_slug"],
            "primary_profile": "business_growth_profile",
            "secondary_profile": "investment_market_profile",
        },
        "setting": {
            "group_background": "Legacy industrial group",
            "execution_doctrine": "capital flow and contract leverage",
            "starter_company": {
                "name": "Test Holdings",
                "state": "distressed",
                "assets": ["factory", "network"],
                "liabilities": ["debt", "reputation damage"],
            },
        },
        "protagonist": {
            "name": "Hero",
            "status": "freshly returned",
            "public_image": "quiet heir",
            "true_strength": "reads asset flow before others",
            "true_weakness": "emotional overreach",
            "initial_goal": "stabilize the company",
            "mid_goal": "rebuild the network",
            "final_goal": "restore the group",
            "age_at_start": 19,
        },
        "phase0_design": {
            "arcs": [
                {
                    "arc_id": "arc_1",
                    "title": "Arc 1",
                    "block_range": "1-35",
                    "time_window": "2012 H1",
                    "capital_target": "35B",
                    "front_sectors": ["retail"],
                    "support_sectors": ["logistics"],
                    "main_opponents": ["Opp A"],
                    "new_npcs": ["NPC A"],
                    "emotion_curve": "gain",
                    "quiet_blocks": [5],
                    "defeat_blocks": [10],
                },
                {
                    "arc_id": "arc_2",
                    "title": "Arc 2",
                    "block_range": "36-70",
                    "time_window": "2012 H2",
                    "capital_target": "70B",
                    "front_sectors": ["materials"],
                    "support_sectors": ["finance"],
                    "main_opponents": ["Opp B"],
                    "new_npcs": ["NPC B"],
                    "emotion_curve": "rise",
                    "quiet_blocks": [40],
                    "defeat_blocks": [45],
                },
            ],
            "npc_timeline": [
                {"name": "Ally", "role": "mentor", "first_block": 2, "final_status": "active", "turning_points": []}
            ],
            "foreshadow_map": [{"id": "S-001", "description": "Opening seed", "status": "active"}],
            "opponent_transition_plan": [{"faction": "Opp A", "phase": "opening", "goal": "hostile pressure"}],
        },
    }


def _build_blocks_for_real_bible() -> list[dict]:
    return [
        {
            "block_id": f"Block {idx}",
            "title": f"Test Block {idx}",
            "content": _full_content(f"Block {idx}"),
            "stakes": f"risk {idx}",
            "power_shift": {"protagonist": "gain", "antagonist": "loss"},
            "relationship_delta": [],
            "foreshadow": [],
            "callback": [],
            "emotional_beat": {"type": "resolve", "intensity": 6},
            "tension_level": 7,
            "pov_character": "Hero",
            "location": {"place": "Seoul", "type": "city"},
            "time_span": {"duration": "1 week", "in_story_time": f"2012 week {idx}"},
            "genre_ext": {"capital_after": f"{idx}B", "deal_type": "retail"},
            "regression_ext": {"is_regressor": True, "regression_type": "regressor"},
        }
        for idx in range(1, 71)
    ]


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

    def fake_build_bible(payload: dict, treatment_blocks: list[dict], **_kwargs) -> dict:
        captured["build_blocks"] = treatment_blocks
        return {
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {"title": "Test Project"},
                    "CoreIdentity": {"protagonist": "Hero"},
                },
                "FinanceHUD": {"Protagonist": {"actual_truth": {"name": "Hero"}}},
                "plot_roadmap": treatment_blocks,
            }
        }

    monkeypatch.setattr(build_script, "normalize_phase0_design", fake_normalize_phase0_design)
    monkeypatch.setattr(build_script, "build_bible", fake_build_bible)
    monkeypatch.setattr(build_script, "validate_bible_structure", lambda _: (True, [], []))
    monkeypatch.setattr(build_script, "ROOT", temp_dir)
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
    assert captured["normalized_blocks"][0]["block_no"] == 1
    assert captured["build_blocks"][0]["block_no"] == 1
    assert [block["title"] for block in captured["normalized_blocks"]] == [block["title"] for block in blocks]
    assert [block["title"] for block in captured["build_blocks"]] == [block["title"] for block in blocks]


def test_build_bible_emits_runtime_protagonist_contract_and_normalized_roadmap() -> None:
    bible = build_script.build_bible(
        _build_phase0_for_real_bible(),
        _build_blocks_for_real_bible(),
        work_id="test_project",
        source_phase0="treatments/phase0/test_project_phase0_design.json",
        source_tr="treatments/01_test_project_tr_block_070_draft.json",
        authority_chain=["treatments/preprocess/test_project/source_manifest.json"],
    )

    protagonist_config = bible["MasterBible"]["protagonist_config"]
    meta = bible["MasterBible"]["ProjectData"]["MetaInfo"]
    roadmap = bible["MasterBible"]["plot_roadmap"]

    assert protagonist_config["world_origin"]
    assert protagonist_config["incarnation_type"]
    assert protagonist_config["pov"]
    assert protagonist_config["external_pov_insert_policy"]
    assert meta["title"] == "Golden Route"
    assert meta["commercial_label"] == "Golden Canary"
    assert meta["slug_aliases"] == ["canary test", "test_project_legacy_slug"]
    assert bible["_naming_authority"]["canonical_title"] == "Golden Route"
    assert roadmap[0]["block_no"] == 1
    assert roadmap[-1]["block_no"] == 70
