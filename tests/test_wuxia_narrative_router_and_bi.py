from __future__ import annotations

import json
import sys
from pathlib import Path

import modules.narrative_router.router as router_module
import scripts.audit_wuxia_bi_5pass as audit_script
import scripts.build_wuxia_bi_from_phase0_and_tr as build_script
from modules.narrative_router.artifact_paths import (
    resolve_bi_path,
    resolve_tr_path,
    resolve_work_guard_library_path,
)
from modules.narrative_router.router import resolve_route
from scripts.wuxia_tr_batch_harness import compute_treatment_metrics


def _build_phase0() -> dict:
    return {
        "project": {
            "title_ko": "Wuxia Project",
            "title": "Wuxia Project",
            "format": "wuxia",
            "logline": "A fallen disciple climbs again.",
            "core_premise": "A regressor survives sect politics and climbs through martial insight.",
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
                {"arc_id": "arc_1", "title": "Purged Disciple", "main_opponents": ["Iron Hall"], "block_range": "1-35", "time_window": "spring"},
                {"arc_id": "arc_2", "title": "Archive Return", "main_opponents": ["Black Oath"], "block_range": "36-70", "time_window": "summer"},
            ],
            "npc_timeline": [
                {"name": "Master Han", "role": "mentor"},
                {"name": "Yun Hye", "role": "ally"},
            ],
            "foreshadow_map": [{"id": "S-001", "description": "The blood seal hidden in the archive."}],
            "opponent_transition_plan": [{"faction": "Iron Hall", "goal": "seal the archive"}, {"faction": "Black Oath", "goal": "claim the blood seal"}],
        },
    }


def _build_block(
    block_no: int,
    *,
    realm_before: str,
    realm_after: str,
    energy_before: int,
    energy_after: int,
    opponent_name: str,
    callback: list[str] | None = None,
    foreshadow: list[str] | None = None,
    faction_position: str = "inner court suspect",
    jianghu_reputation: str = "a dangerous unknown",
    enemy_pressure: str = "the sect elders are closing the net",
    martial_art_gain: str = "sharpens Falling Star Sword into a cleaner killing line",
    artifact_or_manual_gain: str = "none",
) -> dict:
    style = ["intercepts", "unthreads", "reframes", "bait-turns", "isolates"][(block_no - 1) % 5]
    venue = ["archive lane", "courtyard ridge", "seal chamber", "river gate", "bell tower"][(block_no - 1) % 5]
    evidence = ["ink ledger", "broken token", "blood seal trace", "witness list", "manual fragment"][(block_no - 1) % 5]
    return {
        "block_id": f"Block {block_no}",
        "title": f"Block {block_no} title",
        "content": {
            "context": (
                f"Block {block_no} sets the pressure around the {venue}, keeps the archive route unstable, "
                f"and forces Seo Jin to choose between caution and initiative before witnesses can close the trap with the {evidence}."
            ),
            "event_villain": (
                f"{opponent_name} moves first, weaponizes rumor and position, and tries to pin the next clash on Seo Jin "
                f"so that the sect punishment will land before the {venue} can be secured."
            ),
            "solution": (
                f"Seo Jin {style} the exchange, redirects the witness line, reads footwork before intent settles, "
                f"and turns the clash into proof that {opponent_name} overcommitted to the wrong angle in public view around the {venue}. "
                f"He then anchors the next move with the {evidence} so the sect cannot rewrite the sequence after the clash ends."
            ),
            "reward": (
                f"The exchange opens a narrow route toward the archive, raises Seo Jin's leverage with allies, "
                f"and leaves a visible mark on {opponent_name}'s authority through the recovered {evidence}."
            ),
        },
        "stakes": (
            f"If Block {block_no} fails, the archive route closes at the {venue}, the purge gains evidence, and Seo Jin loses the timing window "
            f"needed to survive the next sect judgment before the {evidence} can be secured."
        ),
        "power_shift": {"protagonist": "gains initiative", "antagonist": "loses control"},
        "relationship_delta": [{"target": "Yun Hye", "before": "watches carefully", "after": "backs Seo Jin with hidden evidence"}],
        "foreshadow": foreshadow or [],
        "callback": callback or [],
        "emotional_beat": {"type": "resolve" if block_no % 2 else "pressure", "intensity": 7},
        "tension_level": 8,
        "pov_character": "Seo Jin",
        "location": {"place": f"sect-yard-{block_no}", "type": "sect courtyard"},
        "time_span": {"duration": "1 day", "in_story_time": f"spring day {block_no}"},
        "genre_ext": {
            "realm_before": realm_before,
            "realm_after": realm_after,
            "internal_energy_before": energy_before,
            "internal_energy_after": energy_after,
            "martial_art_gain": martial_art_gain,
            "artifact_or_manual_gain": artifact_or_manual_gain,
            "faction_position": faction_position,
            "jianghu_reputation": jianghu_reputation,
            "enemy_pressure": enemy_pressure,
            "opponent": {
                "name": opponent_name,
                "sect_or_faction": "Iron Hall" if block_no <= 35 else "Black Oath",
                "weakness_exploited": f"exposed stance lane {block_no}",
            },
            "success_pattern": f"Block {block_no} rewards timing, pressure control, and a visible martial edge.",
        },
        "regression_ext": {
            "is_regressor": False,
            "regression_type": "none",
            "execution_doctrine": "win before the sect can formalize the accusation",
        },
    }


def _build_positive_blocks(count: int) -> list[dict]:
    blocks: list[dict] = []
    current_realm = "Body Tempering"
    current_energy = 10
    for block_no in range(1, count + 1):
        next_realm = current_realm if block_no % 3 else "Meridian Opening"
        next_energy = current_energy + 3
        foreshadow = [f"Block {block_no + 1} archive clue becomes usable."] if block_no < count else []
        callback = [f"Block {block_no - 1} archive clue becomes usable."] if block_no > 1 else []
        blocks.append(
            _build_block(
                block_no,
                realm_before=current_realm,
                realm_after=next_realm,
                energy_before=current_energy,
                energy_after=next_energy,
                opponent_name=f"Opponent {block_no}",
                foreshadow=foreshadow,
                callback=callback,
                artifact_or_manual_gain=f"manual fragment {block_no}" if block_no % 5 == 0 else "none",
            )
        )
        current_realm = next_realm
        current_energy = next_energy
    return blocks


def _build_weak_blocks(count: int) -> list[dict]:
    blocks: list[dict] = []
    for block_no in range(1, count + 1):
        blocks.append(
            _build_block(
                block_no,
                realm_before="Body Tempering",
                realm_after="Body Tempering",
                energy_before=10,
                energy_after=10,
                opponent_name="Same Opponent",
                foreshadow=[f"Block {block_no + 1} vague promise."] if block_no < count else [],
                callback=[],
                faction_position="",
                jianghu_reputation="",
                enemy_pressure="",
                martial_art_gain="",
                artifact_or_manual_gain="none",
            )
        )
        blocks[-1]["stakes"] = "Failure is bad."
    return blocks


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_router_detects_stage_from_work_id_artifacts(temp_dir, monkeypatch):
    monkeypatch.setattr(router_module, "ROOT", temp_dir)

    preprocess_dir = temp_dir / "treatments" / "preprocess" / "demo"
    preprocess_dir.mkdir(parents=True)
    for name in ("source_manifest.json", "profile_lock.json", "material_bundle_summary.json"):
        _write_json(preprocess_dir / name, {"ok": True})
    _write_json(preprocess_dir / "phase0_ready_snapshot.json", {"manual_audit_pass": True})

    route = resolve_route(genre="wuxia", work_id="demo")
    assert route.stage == "planning"
    assert route.artifact_state is not None
    assert route.artifact_state.preprocess_ready is True

    _write_json(temp_dir / "treatments" / "phase0" / "demo_phase0_design.json", {"phase0": True})
    route = resolve_route(genre="wuxia", work_id="demo")
    assert route.stage == "production"

    _write_json(temp_dir / "treatments" / "demo_tr_block_070_draft.json", [])
    route = resolve_route(genre="wuxia", work_id="demo")
    assert route.stage == "bi"

    _write_json(temp_dir / "bible" / "0_bi_demo.json", {})
    route = resolve_route(genre="wuxia", work_id="demo")
    assert route.stage == "audit_or_repair"


def test_router_accepts_legacy_root_phase0_path_as_fallback(temp_dir, monkeypatch):
    monkeypatch.setattr(router_module, "ROOT", temp_dir)

    preprocess_dir = temp_dir / "treatments" / "preprocess" / "demo"
    preprocess_dir.mkdir(parents=True)
    for name in ("source_manifest.json", "profile_lock.json", "material_bundle_summary.json"):
        _write_json(preprocess_dir / name, {"ok": True})
    _write_json(preprocess_dir / "phase0_ready_snapshot.json", {"manual_audit_pass": True})

    _write_json(temp_dir / "treatments" / "demo_phase0_design.json", {"phase0": True})
    route = resolve_route(genre="wuxia", work_id="demo")

    assert route.stage == "production"
    assert route.artifact_state is not None
    assert route.artifact_state.phase0_path.endswith("treatments/demo_phase0_design.json")


def test_artifact_paths_accept_numbered_tr_bi_files(temp_dir):
    (temp_dir / "treatments").mkdir(parents=True)
    (temp_dir / "bible").mkdir(parents=True)
    _write_json(temp_dir / "treatments" / "06_gatekeeper_heir_tr_block_070_draft.json", [])
    _write_json(temp_dir / "bible" / "06_bi_gatekeeper_heir.json", {})

    tr_path = resolve_tr_path("gatekeeper_heir", root=temp_dir)
    bi_path = resolve_bi_path("gatekeeper_heir", root=temp_dir)

    assert tr_path.name == "06_gatekeeper_heir_tr_block_070_draft.json"
    assert bi_path.name == "06_bi_gatekeeper_heir.json"


def test_artifact_paths_accept_waiting_room_partial_tr_files(temp_dir):
    waiting_room = temp_dir / "treatments" / "_waiting_room" / "2026-04-20_donor_ready_root_wave"
    waiting_room.mkdir(parents=True)
    _write_json(waiting_room / "jangyeongshil_industrial_revolution_tr_block_010_draft.json", [])
    _write_json(waiting_room / "jangyeongshil_industrial_revolution_tr_block_016_020_draft.json", [])
    _write_json(waiting_room / "jangyeongshil_industrial_revolution_tr_block_025_draft.json", [])
    _write_json(waiting_room / "hoegui_surgeon_tr_block_020_draft.json", [])

    jang_path = resolve_tr_path("jangyeongshil_industrial_revolution", root=temp_dir)
    hoegui_path = resolve_tr_path("hoegui_surgeon", root=temp_dir)

    assert jang_path.name == "jangyeongshil_industrial_revolution_tr_block_025_draft.json"
    assert hoegui_path.name == "hoegui_surgeon_tr_block_020_draft.json"


def test_artifact_paths_accept_waiting_room_legacy_bi_files(temp_dir):
    waiting_room = temp_dir / "bible" / "_waiting_room" / "2026-04-20_donor_ready_root_wave"
    waiting_room.mkdir(parents=True)
    _write_json(waiting_room / "jangyeongshil_industrial_revolution_bi.json", {})
    _write_json(waiting_room / "0_bi_hoegui_surgeon.json", {})

    jang_path = resolve_bi_path("jangyeongshil_industrial_revolution", root=temp_dir)
    hoegui_path = resolve_bi_path("hoegui_surgeon", root=temp_dir)

    assert jang_path.name == "jangyeongshil_industrial_revolution_bi.json"
    assert hoegui_path.name == "0_bi_hoegui_surgeon.json"


def test_artifact_paths_accept_work_guard_in_genre_subfolder(temp_dir):
    work_guard_path = temp_dir / "work_guards" / "investment" / "demo.yaml"
    work_guard_path.parent.mkdir(parents=True, exist_ok=True)
    work_guard_path.write_text("work_identity:\n  work_id: demo\n", encoding="utf-8")

    resolved = resolve_work_guard_library_path("demo", root=temp_dir)

    assert resolved == work_guard_path


def test_router_surfaces_work_guard_visibility_without_changing_stage(temp_dir, monkeypatch):
    monkeypatch.setattr(router_module, "ROOT", temp_dir)

    preprocess_dir = temp_dir / "treatments" / "preprocess" / "demo"
    preprocess_dir.mkdir(parents=True)
    for name in ("source_manifest.json", "profile_lock.json", "material_bundle_summary.json"):
        _write_json(preprocess_dir / name, {"ok": True})
    _write_json(preprocess_dir / "phase0_ready_snapshot.json", {"manual_audit_pass": True})
    _write_json(temp_dir / "treatments" / "phase0" / "demo_phase0_design.json", {"phase0": True})

    route = resolve_route(genre="wuxia", work_id="demo")

    assert route.stage == "production"
    assert route.artifact_state is not None
    assert route.artifact_state.work_guard_library_exists is False
    assert route.artifact_state.work_guard_advisory == "missing_before_tr"

    work_guard_path = temp_dir / "work_guards" / "wuxia" / "demo.yaml"
    work_guard_path.parent.mkdir(parents=True, exist_ok=True)
    work_guard_path.write_text("work_identity:\n  work_id: demo\n", encoding="utf-8")

    route = resolve_route(genre="wuxia", work_id="demo")

    assert route.stage == "production"
    assert route.artifact_state is not None
    assert route.artifact_state.work_guard_library_exists is True
    assert route.artifact_state.work_guard_advisory == "present"


def test_wuxia_compute_treatment_metrics_passes_positive_fixture():
    metrics = compute_treatment_metrics(_build_positive_blocks(10))

    assert metrics["production_density_gate"] is True
    assert metrics["callback_ratio"] >= 0.55
    assert metrics["unresolved_foreshadow_count"] == 0
    assert metrics["martial_progress_blocks"]
    assert metrics["hard_gate_failures"] == []


def test_wuxia_compute_treatment_metrics_rejects_low_signal_fixture():
    metrics = compute_treatment_metrics(_build_weak_blocks(10))

    assert metrics["production_density_gate"] is False
    assert "callback_ratio_ok" in metrics["hard_gate_failures"]
    assert "faction_position_present" in metrics["hard_gate_failures"]
    assert "martial_progress_ratio_ok" in metrics["hard_gate_failures"]


def test_build_wuxia_bi_syncs_current_state_from_final_tr_block():
    phase0 = _build_phase0()
    draft = _build_positive_blocks(4)
    draft[-1]["genre_ext"]["realm_after"] = "Core Formation"
    draft[-1]["genre_ext"]["internal_energy_after"] = 77
    draft[-1]["genre_ext"]["jianghu_reputation"] = "known as the archive ghost"
    draft[-1]["genre_ext"]["enemy_pressure"] = "Black Oath is mobilizing openly"

    bible = build_script.build_bible(phase0, draft)
    actual_truth = bible["MasterBible"]["MartialHUD"]["Protagonist"]["actual_truth"]

    assert actual_truth["realm"] == "Core Formation"
    assert actual_truth["current_realm"] == "Core Formation"
    assert actual_truth["internal_energy"] == 77
    assert actual_truth["reputation"] == "known as the archive ghost"
    assert actual_truth["current_enemy_pressure"] == "Black Oath is mobilizing openly"
    assert actual_truth["last_confirmed_block"] == 4


def test_audit_wuxia_bi_blocks_bi_handoff_when_source_tr_gate_fails(monkeypatch, temp_dir):
    phase0_path = temp_dir / "phase0.json"
    draft_path = temp_dir / "draft.json"
    bi_path = temp_dir / "bi.json"
    report_path = temp_dir / "report.md"

    phase0 = _build_phase0()
    draft = _build_positive_blocks(70)
    draft[-1]["genre_ext"]["realm_after"] = "Core Formation"
    draft[-1]["genre_ext"]["internal_energy_after"] = 144
    draft[-1]["genre_ext"]["jianghu_reputation"] = "the archive ghost"
    draft[-1]["genre_ext"]["enemy_pressure"] = "Black Oath surrounds the valley"
    bi = build_script.build_bible(phase0, draft)

    _write_json(phase0_path, phase0)
    _write_json(draft_path, draft)
    _write_json(bi_path, bi)

    monkeypatch.setattr(
        audit_script,
        "compute_treatment_metrics",
        lambda _draft: {
            "production_density_gate": False,
            "avg_solution_chars": 80,
            "one_sentence_like_solution_blocks": 30,
            "opponent_unique": 3,
            "top_opponent_share": 60.0,
            "top_weakness_repetition": 5,
            "callback_ratio": 0.2,
            "martial_progress_blocks": list(range(1, 10)),
            "block_count": 70,
            "hard_gate_checks": {
                "critical_thin_blocks_zero": True,
                "thin_blocks_ratio_ok": True,
                "late_thin_blocks_zero": True,
                "short_stakes_blocks_total_ok": True,
                "endgame_low_stakes_zero": True,
                "callback_ratio_ok": False,
                "unresolved_foreshadow_count_ok": True,
                "faction_position_present": True,
                "jianghu_reputation_present": True,
                "enemy_pressure_present": True,
                "late_blank_opponent_ok": True,
                "normalized_solution_stakes_repeat_ok": True,
                "martial_progress_ratio_ok": False,
            },
            "hard_gate_failures": ["callback_ratio_ok", "martial_progress_ratio_ok"],
            "is_regressor_treatment": False,
        },
    )
    monkeypatch.setattr(audit_script, "validate_treatment_structure", lambda _: (True, [], []))
    monkeypatch.setattr(audit_script, "validate_bible_structure", lambda _: (True, [], []))
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

    exit_code = audit_script.main()
    report_text = report_path.read_text(encoding="utf-8")

    assert exit_code == 1
    assert "- source_tr_density_gate: FAIL" in report_text
    assert "- source_tr_callback_gate: FAIL" in report_text
    assert "- source_tr_martial_progress_gate: FAIL" in report_text
    assert "- source_tr_hard_gate_failures: ['callback_ratio_ok', 'martial_progress_ratio_ok']" in report_text
