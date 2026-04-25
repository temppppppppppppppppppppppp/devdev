import json
from pathlib import Path

from modules.core.db_manager import DBManager
from modules.core.stage4_canary_tools import (
    build_stage2_canary_summary,
    prepare_stage2_canary_project,
)


def _make_project_root(root: Path) -> None:
    for rel in ("drafts", "logs", "memory", "plans/arcs", "plans/blueprints", "config"):
        (root / rel).mkdir(parents=True, exist_ok=True)


def _seed_stage2_source_project(root: Path) -> None:
    _make_project_root(root)
    db = DBManager(root / "project_data.db")
    try:
        db.save_anchor("genre_info", {"type": "investment", "name": "investment"})
        arcs = []
        for arc_no in range(1, 6):
            prev_items = [] if arc_no <= 1 else [f"item-{arc_no - 1}"]
            end_items = [] if arc_no <= 3 else [f"item-{arc_no}"]
            arc = {
                "arc_no": arc_no,
                "ep_start": ((arc_no - 1) * 5) + 1,
                "ep_end": arc_no * 5,
                "state_constraints": {
                    "arc_start_state": {"equipment": prev_items},
                    "arc_end_state": {"equipment": end_items},
                    "protagonist_items": [f"delta-{arc_no}"] if arc_no >= 4 else [],
                    "items_acquired": [f"delta-{arc_no}"] if arc_no >= 4 else [],
                },
                "joint_docs": {"physical_inventory": end_items},
            }
            arcs.append(arc)
            db.save_anchor(f"arc_summary_{arc_no}", {"arc_no": arc_no})
            db.save_stage_attempt(
                stage=2,
                verdict="PASS",
                ep_num=arc_no,
                arc_num=arc_no,
                attempt_num=1,
                score=95,
                session_id=f"session-{arc_no}",
                attempt_key=f"s2:arc{arc_no}",
                artifact_path=f"logs/artifacts/stage2/arc_{arc_no:03d}/attempt_01/final_arc.json",
            )
            db.save_director_selection(
                ep_num=arc_no,
                round_num=1,
                selected_label="best",
                selected_strategy="stage2",
                verdict="PASS",
                score=95,
                stage=2,
                attempt_key=f"s2:arc{arc_no}",
                artifact_path=f"logs/artifacts/stage2/arc_{arc_no:03d}/attempt_01/final_arc.json",
            )
        db.save_anchor("arcs", arcs)
    finally:
        db.close()

    for arc_no in range(1, 6):
        (root / "plans" / "arcs" / f"arc_{arc_no:03d}.txt").write_text(f"arc-{arc_no}", encoding="utf-8")
        artifact_dir = root / "logs" / "artifacts" / "stage2" / f"arc_{arc_no:03d}" / "attempt_01"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "final_arc.json").write_text("{}", encoding="utf-8")
    (root / "logs" / "pass_rate_monitor.json").write_text('{"records":[]}', encoding="utf-8")
    (root / "logs" / "quality_metrics.jsonl").write_text('{"stage":2}\n', encoding="utf-8")
    (root / "logs" / "runtime_audit.jsonl").write_text('{"event":"stage2"}\n', encoding="utf-8")
    (root / "logs" / "runtime_audit_summary.json").write_text('{"tag":"stage2"}', encoding="utf-8")
    (root / "logs" / "session_123.log").write_text("session-log", encoding="utf-8")
    session_dir = root / "logs" / "session"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "decisions.jsonl").write_text('{"decision":"old"}\n', encoding="utf-8")


def test_prepare_stage2_canary_project_rewinds_arc_payloads_and_logs(tmp_path):
    source = tmp_path / "source_project"
    target = tmp_path / "canary" / "target_project"
    _seed_stage2_source_project(source)

    result = prepare_stage2_canary_project(source, target, keep_arcs=3)

    assert result["canary_scope"] == "stage2_only"
    assert result["keep_arcs"] == 3
    assert result["cleanup"]["db_impact"]["removed_arc_count"] == 2

    target_db = DBManager(target / "project_data.db")
    try:
        kept_arcs = target_db.load_anchor("arcs")
        assert len(kept_arcs) == 3
        keys = {row["key"] for row in target_db.conn.execute("SELECT key FROM anchors ORDER BY key").fetchall()}
        assert "arc_payload_0004" not in keys
        assert "arc_payload_0005" not in keys
        assert "arc_summary_4" not in keys
        assert "arc_summary_5" not in keys
        stage2_attempts = target_db.conn.execute("SELECT COUNT(*) AS c FROM stage_attempts WHERE stage = 2").fetchone()[
            "c"
        ]
        director_rows = target_db.conn.execute(
            "SELECT COUNT(*) AS c FROM director_selections WHERE stage = 2"
        ).fetchone()["c"]
        assert stage2_attempts == 3
        assert director_rows == 3
    finally:
        target_db.close()

    assert (target / "plans" / "arcs" / "arc_003.txt").exists() is True
    assert (target / "plans" / "arcs" / "arc_004.txt").exists() is False
    assert (target / "logs" / "artifacts" / "stage2" / "arc_003").exists() is True
    assert (target / "logs" / "artifacts" / "stage2" / "arc_004").exists() is False
    assert (target / "logs" / "pass_rate_monitor.json").exists() is False
    assert list((target / "logs" / "session").iterdir()) == []
    assert (target / "logs" / "stage2_canary_prep.json").exists() is True

    source_db = DBManager(source / "project_data.db")
    try:
        assert len(source_db.load_anchor("arcs")) == 5
    finally:
        source_db.close()
    assert (source / "plans" / "arcs" / "arc_005.txt").exists() is True


def test_build_stage2_canary_summary_reports_carryover_match_and_delta_channel(tmp_path):
    project = tmp_path / "stage2_canary"
    _make_project_root(project)
    db = DBManager(project / "project_data.db")
    try:
        db.save_anchor("genre_info", {"type": "investment", "name": "investment"})
        db.save_anchor(
            "arcs",
            [
                {
                    "arc_no": 4,
                    "ep_start": 18,
                    "ep_end": 22,
                    "state_constraints": {
                        "arc_start_state": {"equipment": []},
                        "arc_end_state": {"equipment": ["양장 수첩", "OTP 카드"]},
                        "protagonist_items": [],
                        "items_acquired": [],
                    },
                    "joint_docs": {"physical_inventory": ["양장 수첩", "OTP 카드"]},
                },
                {
                    "arc_no": 5,
                    "ep_start": 23,
                    "ep_end": 26,
                    "state_constraints": {
                        "arc_start_state": {"equipment": ["양장 수첩", "OTP 카드"]},
                        "arc_end_state": {"equipment": ["양장 수첩", "50억 잔고 증명서"]},
                        "protagonist_items": ["50억 잔고 증명서"],
                        "items_acquired": ["50억 잔고 증명서"],
                    },
                    "joint_docs": {"physical_inventory": ["양장 수첩", "50억 잔고 증명서"]},
                },
            ],
        )
        db.save_stage_attempt(
            stage=2,
            verdict="PASS",
            ep_num=4,
            arc_num=4,
            attempt_num=1,
            score=95,
            session_id="sess",
            attempt_key="s2:4",
            artifact_path="logs/artifacts/stage2/arc_004/attempt_01/final_arc.json",
        )
        db.save_stage_attempt(
            stage=2,
            verdict="PASS",
            ep_num=5,
            arc_num=5,
            attempt_num=1,
            score=100,
            session_id="sess",
            attempt_key="s2:5",
            artifact_path="logs/artifacts/stage2/arc_005/attempt_01/final_arc.json",
        )
    finally:
        db.close()

    (project / "logs" / "stage2_canary_prep.json").write_text(
        json.dumps({"source_project": "baseline", "keep_arcs": 3}, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_stage2_canary_summary(project, expected_final_arc_count=2)

    assert summary["summary_role"] == "stage2_only_canary"
    assert summary["hard_gates"]["status"] == "pass"
    assert summary["latest_carryover_pair"]["previous_arc_no"] == 4
    assert summary["latest_carryover_pair"]["current_arc_no"] == 5
    assert summary["latest_carryover_pair"]["carryover_match"] is True
    assert summary["latest_carryover_pair"]["joint_inventory_matches_end_equipment"] is True
    assert summary["latest_carryover_pair"]["current_protagonist_items"] == ["50억 잔고 증명서"]
