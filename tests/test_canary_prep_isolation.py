from pathlib import Path

from modules.core.db_manager import DBManager
from modules.core.fact_ledger import FactLedger
from modules.core.stage4_canary_tools import (
    _validate_truth_store_reset,
    prepare_stage4_canary_project,
    reset_stage4_outputs,
)


def _make_project_root(root: Path) -> None:
    for rel in ("drafts", "logs", "memory", "plans/arcs", "plans/blueprints", "config", "stage0_output"):
        (root / rel).mkdir(parents=True, exist_ok=True)


def _polluted_fact_ledger() -> dict:
    return {
        "characters": {},
        "numbers": {
            "capital": {
                "value": 4_000_000_000,
                "unit": "won",
                "last_ep": 6,
                "established_ep": 1,
                "established_value": 2_000_000_000,
                "history": [
                    "ep1: direct financial scalar extracted",
                    "ep2: direct financial scalar extracted",
                    "ep3: direct financial scalar extracted",
                    "ep4: direct financial scalar extracted",
                    "ep5: direct financial scalar extracted",
                    "ep6: direct financial scalar extracted",
                    "ep1: direct financial scalar extracted",
                    "ep3: direct financial scalar extracted",
                ],
            }
        },
        "items": {},
        "locations": {},
        "organizations": {},
        "last_updated_ep": 6,
    }


def _polluted_world_state() -> dict:
    return {
        "version": 1,
        "last_updated_ep": 6,
        "protagonist": {
            "name": "한시우",
            "location": "여의도 오피스텔",
            "assets": "",
            "injuries": "정상",
            "skills": [],
        },
        "alive_npcs": {
            "기존인물": {"first_seen_ep": 1, "role_at_intro": "조력자", "relation": "협력자"},
            "최민": {"first_seen_ep": 4, "role_at_intro": "감시자", "relation": "적대"},
        },
        "dead_npcs": {},
        "relationships": {"기존인물": "협력자", "최민": "적대"},
        "active_items": {
            "기존장비": {"ep_acquired": 2, "status": "보유"},
            "미래장비": {"ep_acquired": 4, "status": "보유"},
            "OTP 카드": {"ep_acquired": 1, "status": "소실"},
        },
        "destroyed": [],
        "active_plots": [],
        "active_pressure_vectors": [],
        "world_notes": [],
        "world_laws": [],
        "timeline": [{"ep": 6, "type": "pressure", "description": "future residue"}],
        "motivations": [],
        "promises": [],
        "cumulative_elapsed": {"total_days": 0, "history": []},
    }


def _seed_source_project(root: Path) -> None:
    _make_project_root(root)
    db = DBManager(root / "project_data.db")
    try:
        db.save_anchor("genre_info", {"type": "investment", "name": "investment"})
        for ep in range(1, 8):
            db.save_anchor(f"chain_link_{ep}", {"ep": ep, "pending_actions": [f"action-{ep}"]})

        for ep in range(1, 7):
            state_changes = {}
            if ep <= 3:
                state_changes["capital"] = 2_000_000_000
            if ep == 1:
                bible_delta = {
                    "ep_num": ep,
                    "state_changes": state_changes,
                    "new_npcs": [{"name": "기존인물", "role": "조력자"}],
                    "relationship_changes": [{"npc": "기존인물", "from": "", "to": "협력자"}],
                    "new_items": ["OTP 카드"],
                }
                db.save_episode_bible(ep, bible_delta)
                continue
            if ep == 2:
                bible_delta = {
                    "ep_num": ep,
                    "state_changes": state_changes,
                    "new_items": [{"name": "기존장비"}],
                }
                db.save_episode_bible(ep, bible_delta)
                continue
            if ep == 3:
                bible_delta = {
                    "ep_num": ep,
                    "state_changes": state_changes,
                    "lost_items": ["OTP 카드"],
                }
                db.save_episode_bible(ep, bible_delta)
                continue
            if ep == 4:
                bible_delta = {
                    "ep_num": ep,
                    "state_changes": state_changes,
                    "new_npcs": [{"name": "최민", "role": "감시자"}],
                    "relationship_changes": [{"npc": "최민", "from": "", "to": "적대"}],
                    "new_items": ["미래장비"],
                }
                db.save_episode_bible(ep, bible_delta)
                continue
            db.save_episode_bible(ep, {"ep_num": ep, "state_changes": state_changes})

        db.save_anchor("fact_ledger", _polluted_fact_ledger())
        db.save_anchor("world_state", _polluted_world_state())
    finally:
        db.close()

    for ep in range(1, 5):
        (root / "drafts" / f"ep_{ep:04d}.txt").write_text(f"draft-{ep}", encoding="utf-8")
    (root / "logs" / "episode_production.jsonl").write_text('{"ep": 4}\n', encoding="utf-8")
    (root / "memory" / "vec.db").write_text("stub", encoding="utf-8")


def test_prepare_stage4_canary_project_cleans_orphan_truth_store_anchors_from_partial_boundary(tmp_path):
    source = tmp_path / "source_project"
    target = tmp_path / "target_project"
    _seed_source_project(source)

    result = prepare_stage4_canary_project(source, target, from_ep=4)

    assert result["cleanup"]["anchor_validation"]["status"] == "ok"
    assert result["cleanup"]["anchor_validation"]["cleanup_status"] == "ok"
    assert result["cleanup"]["anchor_validation"]["minimum_truth_status"] == "ok"
    assert result["cleanup"]["db_impact"]["orphan_chain_link_anchors"] == 4
    assert result["cleanup"]["anchor_validation"]["missing_world_state_npcs"] == []
    assert result["cleanup"]["anchor_validation"]["missing_world_state_active_items"] == []
    assert result["cleanup"]["anchor_validation"]["world_state_relationship_mismatches"] == []

    db = DBManager(target / "project_data.db")
    try:
        assert db.load_anchor("chain_link_1")["ep"] == 1
        assert db.load_anchor("chain_link_3")["ep"] == 3
        assert db.load_anchor("chain_link_4") == {}
        assert db.load_anchor("chain_link_7") == {}

        fact_ledger = db.load_anchor("fact_ledger")
        capital = fact_ledger["numbers"]["capital"]
        assert capital["value"] == 2_000_000_000
        assert capital["last_ep"] == 3
        assert all(not str(entry).startswith(("ep4:", "ep5:", "ep6:", "ep7:")) for entry in capital["history"])

        world_state = db.load_anchor("world_state")
        assert world_state["last_updated_ep"] == 3
        assert "기존인물" in world_state["alive_npcs"]
        assert "최민" not in world_state["alive_npcs"]
        assert world_state["relationships"]["기존인물"] == "협력자"
        assert "기존장비" in world_state["active_items"]
        assert world_state["active_items"]["OTP 카드"]["status"] == "lost"
        assert "미래장비" not in world_state["active_items"]
    finally:
        db.close()

    assert (target / "drafts" / "ep_0003.txt").exists() is True
    assert (target / "drafts" / "ep_0004.txt").exists() is False


def test_reset_stage4_outputs_is_idempotent_for_truth_store_boundary(tmp_path):
    project = tmp_path / "project"
    _seed_source_project(project)

    first = reset_stage4_outputs(project, from_ep=4)
    second = reset_stage4_outputs(project, from_ep=4)

    assert first["anchor_validation"]["status"] == "ok"
    assert second["anchor_validation"]["status"] == "ok"
    assert first["anchor_validation"]["minimum_truth_status"] == "ok"
    assert second["anchor_validation"]["minimum_truth_status"] == "ok"

    db = DBManager(project / "project_data.db")
    try:
        fact_ledger = db.load_anchor("fact_ledger")
        capital = fact_ledger["numbers"]["capital"]
        assert capital["value"] == 2_000_000_000
        assert capital["last_ep"] == 3
        assert all(not str(entry).startswith(("ep4:", "ep5:", "ep6:", "ep7:")) for entry in capital["history"])

        world_state = db.load_anchor("world_state")
        assert world_state["last_updated_ep"] == 3
        assert "기존인물" in world_state["alive_npcs"]
        assert world_state["relationships"]["기존인물"] == "협력자"
        assert "기존장비" in world_state["active_items"]
        assert world_state["active_items"]["OTP 카드"]["status"] == "lost"
        assert "최민" not in world_state["alive_npcs"]
        assert "미래장비" not in world_state["active_items"]
    finally:
        db.close()


def test_truth_store_validation_fails_when_minimum_world_state_truth_is_missing(tmp_path):
    project = tmp_path / "project"
    _seed_source_project(project)
    reset_stage4_outputs(project, from_ep=4)

    db = DBManager(project / "project_data.db")
    try:
        world_state = db.load_anchor("world_state")
        world_state["alive_npcs"].pop("기존인물", None)
        world_state["relationships"].pop("기존인물", None)
        world_state["active_items"].pop("기존장비", None)
        db.save_anchor("world_state", world_state)

        validation = _validate_truth_store_reset(db, from_ep=4)
    finally:
        db.close()

    assert validation["cleanup_status"] == "ok"
    assert validation["minimum_truth_status"] == "fail"
    assert validation["status"] == "fail"
    assert "기존인물" in validation["missing_world_state_npcs"]
    assert "기존장비" in validation["missing_world_state_active_items"]
    assert validation["world_state_relationship_mismatches"] == [
        {"npc": "기존인물", "expected": "협력자", "actual": ""}
    ]


def test_fact_ledger_update_number_skips_same_ep_same_value_duplicate(tmp_path):
    db = DBManager(tmp_path / "project_data.db")
    try:
        ledger = FactLedger(db)
        ledger.update_number("capital", 2_000_000_000, "won", 1, note="direct financial scalar extracted")
        ledger.update_number("capital", 2_000_000_000, "won", 1, note="direct financial scalar extracted")

        capital = ledger._ledger["numbers"]["capital"]
        assert capital["value"] == 2_000_000_000
        assert capital["last_ep"] == 1
        assert capital["history"] == ["ep1: direct financial scalar extracted"]
    finally:
        db.close()
