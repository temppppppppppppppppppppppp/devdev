from __future__ import annotations

import json
import sys

import scripts.audit_wuxia_bi_5pass as audit_script
import scripts.build_wuxia_bi_from_phase0_and_tr as build_script


def _write_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_phase0() -> dict:
    return {
        "project": {
            "title_ko": "Wuxia Project",
            "title": "Wuxia Project",
            "format": "wuxia",
            "logline": "A fallen disciple climbs again.",
            "core_premise": "A regressor survives sect politics and climbs through martial insight.",
            "start_year": "late dynasty",
            "end_year": "restored order",
        },
        "setting": {
            "resource_state": "lean",
            "starter_faction": {"name": "Azure Sect"},
            "jianghu_phase": "fractured order",
            "execution_doctrine": "win through technique and timing",
        },
        "protagonist": {
            "name": "Seo Jin",
            "public_image": "Quiet Blade",
            "age_at_start": 22,
            "status": "outer disciple",
            "initial_goal": "survive the purge",
            "mid_goal": "retake the archive",
            "final_goal": "break the blood feud",
            "true_strength": "reads movement before intent fully forms",
            "true_weakness": "old meridian injury",
            "signature_art": "Falling Star Sword",
            "mental_method": "Still Water Breathing",
            "reputation": "unknown",
            "inventory": ["travel blade"],
            "martial_arts": ["Falling Star Sword"],
        },
        "phase0_design": {
            "arcs": [
                {"arc_id": "arc_1", "title": "Purged Disciple", "main_opponents": ["Iron Hall"], "block_range": "1-2", "time_window": "spring"},
            ],
            "npc_timeline": [{"name": "Master Han", "role": "mentor"}],
            "foreshadow_map": [{"id": "S-001", "description": "The blood seal hidden in the archive."}],
            "opponent_transition_plan": [{"faction": "Iron Hall", "goal": "seal the archive"}],
        },
    }


def _build_blocks() -> list[dict]:
    return [
        {
            "block_id": f"Block {idx}",
            "title": f"Block {idx} title",
            "content": {
                "context": f"Block {idx} context",
                "event_villain": f"Block {idx} villain move",
                "solution": f"Block {idx} solution",
                "reward": f"Block {idx} reward",
            },
            "stakes": f"stakes {idx}",
            "power_shift": {"protagonist": "gains initiative", "antagonist": "loses control"},
            "relationship_delta": [],
            "foreshadow": [],
            "callback": [],
            "emotional_beat": {"type": "resolve", "intensity": 7},
            "tension_level": 8,
            "pov_character": "Seo Jin",
            "location": {"place": f"sect-yard-{idx}", "type": "sect courtyard"},
            "time_span": {"duration": "1 day", "in_story_time": f"spring day {idx}"},
            "martial_ext": {
                "realm_after": "Body Tempering",
                "internal_energy_after": idx * 10,
                "jianghu_reputation": "unknown",
                "enemy_pressure": "low",
            },
            "regression_ext": {"is_regressor": False, "regression_type": "none"},
        }
        for idx in range(1, 3)
    ]


def _good_metrics() -> dict:
    return {
        "production_density_gate": True,
        "hard_gate_checks": {
            "critical_thin_blocks_zero": True,
            "thin_blocks_ratio_ok": True,
            "late_thin_blocks_zero": True,
            "short_stakes_blocks_total_ok": True,
            "endgame_low_stakes_zero": True,
            "callback_ratio_ok": True,
            "unresolved_foreshadow_count_ok": True,
            "faction_position_present": True,
            "jianghu_reputation_present": True,
            "enemy_pressure_present": True,
            "late_blank_opponent_ok": True,
            "normalized_solution_stakes_repeat_ok": True,
            "martial_progress_ratio_ok": True,
        },
        "opponent_unique": 8,
        "top_opponent_share": 20.0,
        "top_weakness_repetition": 1,
        "avg_solution_chars": 150,
        "one_sentence_like_solution_blocks": 0,
        "is_regressor_treatment": False,
        "callback_ratio": 0.8,
        "hard_gate_failures": [],
        "martial_progress_blocks": [1, 2],
        "block_count": 2,
    }


def test_audit_wuxia_bi_reports_raw_and_normalized_canonical_status(monkeypatch, temp_dir):
    phase0 = _build_phase0()
    draft_blocks = _build_blocks()
    draft_payload = {
        "_schema": "wuxguide_tr_block_070_draft_v1",
        "_total_blocks": len(draft_blocks),
        "blocks": draft_blocks,
    }
    bi = build_script.build_bible(phase0, draft_blocks)

    phase0_path = temp_dir / "phase0.json"
    draft_path = temp_dir / "draft.json"
    bi_path = temp_dir / "bi.json"
    report_path = temp_dir / "report.md"
    _write_json(phase0_path, phase0)
    _write_json(draft_path, draft_payload)
    _write_json(bi_path, bi)

    monkeypatch.setattr(audit_script, "compute_treatment_metrics", lambda _draft: _good_metrics())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "audit_wuxia_bi_5pass.py",
            "--phase0",
            str(phase0_path),
            "--draft",
            str(draft_path),
            "--bi",
            str(bi_path),
            "--report",
            str(report_path),
        ],
    )

    audit_script.main()
    report_text = report_path.read_text(encoding="utf-8")

    assert "- raw_bi_canonical_contract: PASS" in report_text
    assert "- raw_tr_canonical_contract: FAIL" in report_text
    assert "- raw_pair_canonical_contract: FAIL" in report_text
    assert "- normalized_bi_canonical_view: PASS" in report_text
    assert "- normalized_tr_canonical_view: PASS" in report_text
    assert "- normalized_pair_canonical_view: PASS" in report_text
