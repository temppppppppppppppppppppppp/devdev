import csv
import json
from pathlib import Path

from scripts.archive_benchmark_record import archive_benchmark_record


def _make_project(root: Path) -> Path:
    project = root / "projects" / "골든 카나리아"
    (project / "logs" / "metrics").mkdir(parents=True, exist_ok=True)
    project.mkdir(parents=True, exist_ok=True)
    return project


def test_archive_benchmark_record_creates_bundle_and_index(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.archive_benchmark_record._collect_git_info",
        lambda _workspace: {"branch": "", "head": "", "dirty": False},
    )
    project = _make_project(tmp_path)
    (project / "project_data.db").write_bytes(b"sqlite-binary")
    (project / "logs" / "pass_rate_monitor.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "stage": 2,
                        "episode": 1,
                        "duration_ms": 1000,
                        "token_cost": 0.11,
                        "success": True,
                        "final_verdict": "PASS",
                        "attempt_key": "s2:ep1:a1",
                    },
                    {
                        "stage": 3,
                        "episode": 4,
                        "duration_ms": 2000,
                        "token_cost": 0.22,
                        "success": True,
                        "final_verdict": "PASS_WITH_WARNING",
                        "attempt_key": "s3:ep4:a1",
                    },
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (project / "logs" / "episode_production.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "ep": 4,
                        "attempt_key": "s4:ep4:a1",
                        "duration_ms": 3000,
                        "round_total_tokens": 4567,
                        "token_cost": 0.33,
                        "final_verdict": "REJECT",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "event": "STAGE4_POST_PASS_CONTRACT",
                        "ep": 4,
                        "attempt_key": "s4:ep4:a1",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "logs" / "runtime_audit_summary.json").write_text(
        json.dumps(
            {
                "tag": "interrupted",
                "proof_digest": {
                    "operational_metadata": {
                        "latest_session_id": "20260422_080513",
                    }
                },
                "summary_window": {
                    "count_window_size": 200,
                    "counts_truncated": True,
                    "event_window_truncated": True,
                },
                "run_scope": {
                    "status": "scoped",
                    "engine_run_id": "run-archive-123",
                    "latest_session_id": "20260422_080513",
                    "basis": ["GEULDOBI_RUN_ID", "proof_digest.latest_session_id"],
                    "authority_role": "companion_snapshot",
                },
                "freshness": {
                    "status": "scoped",
                    "basis": ["GEULDOBI_RUN_ID", "proof_digest.latest_session_id"],
                    "engine_run_id_present": True,
                    "latest_session_id_present": True,
                    "operator_guidance_only": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (project / "logs" / "runtime_audit.jsonl").write_text(
        json.dumps({"type": "db_commit"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (project / "logs" / "quality_metrics.jsonl").write_text(
        json.dumps({"stage": 4, "score": 91}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (project / "logs" / "stage3_direct_supervised_result.json").write_text(
        json.dumps({"project": "골든 카나리아", "target_ep": 16}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (project / "logs" / "metrics" / "metrics_20260422_080513.json").write_text(
        json.dumps({"total_duration_ms": 6000}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    manifest = archive_benchmark_record(
        workspace_root=tmp_path,
        project="골든 카나리아",
        lane="stage4-supervised",
        target_ep=5,
        status="interrupted",
        notes="ep4 blocked by replay",
        recorded_at="2026-04-22T09:30:00+09:00",
    )

    record_root = Path(manifest["record_root"])
    assert record_root.exists()
    assert record_root.name == "20260422_093000__stage4-supervised__target-ep5__nogit"
    assert (record_root / "snapshots" / "project_data.db").read_bytes() == b"sqlite-binary"
    assert (record_root / "logs" / "metrics" / "metrics_20260422_080513.json").exists()

    stage_rows = {}
    with (record_root / "stage_metrics.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            stage_rows[row["stage"]] = row

    assert stage_rows["stage2"]["attempt_count"] == "1"
    assert stage_rows["stage2"]["total_duration_ms"] == "1000"
    assert stage_rows["stage2"]["total_cost_usd"] == "0.110000"
    assert stage_rows["stage3"]["attempt_count"] == "1"
    assert stage_rows["stage3"]["total_duration_ms"] == "2000"
    assert stage_rows["stage4"]["attempt_count"] == "1"
    assert stage_rows["stage4"]["reject_count"] == "1"
    assert stage_rows["stage4"]["total_tokens"] == "4567"
    assert stage_rows["stage4"]["total_cost_usd"] == "0.330000"

    index_path = tmp_path / "benchmarks" / "benchmark_index.csv"
    with index_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    row = rows[0]
    assert row["project_name"] == "골든 카나리아"
    assert row["status"] == "interrupted"
    assert row["runtime_audit_tag"] == "interrupted"
    assert row["latest_session_id"] == "20260422_080513"
    assert row["runtime_freshness_status"] == "scoped"
    assert row["s2_duration_ms"] == "1000"
    assert row["s3_duration_ms"] == "2000"
    assert row["s4_duration_ms"] == "3000"
    assert row["s4_tokens"] == "4567"
    assert row["total_cost_usd"] == "0.660000"
    assert manifest["runtime_summary"]["summary_window"]["counts_truncated"] is True
    assert manifest["runtime_summary"]["summary_window"]["event_window_truncated"] is True
    assert manifest["runtime_summary"]["run_scope"]["engine_run_id"] == "run-archive-123"
    assert manifest["runtime_summary"]["run_scope"]["latest_session_id"] == "20260422_080513"
    assert manifest["runtime_summary"]["freshness"]["status"] == "scoped"
    assert manifest["runtime_summary"]["freshness"]["operator_guidance_only"] is True


def test_archive_benchmark_record_overwrite_replaces_existing_index_row(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.archive_benchmark_record._collect_git_info",
        lambda _workspace: {"branch": "", "head": "", "dirty": False},
    )
    project = _make_project(tmp_path)
    (project / "project_data.db").write_bytes(b"v1")
    (project / "logs" / "pass_rate_monitor.json").write_text('{"records":[]}', encoding="utf-8")
    (project / "logs" / "episode_production.jsonl").write_text("", encoding="utf-8")
    (project / "logs" / "runtime_audit_summary.json").write_text(
        json.dumps({"tag": "snapshot"}, ensure_ascii=False),
        encoding="utf-8",
    )

    archive_benchmark_record(
        workspace_root=tmp_path,
        project="골든 카나리아",
        lane="stage4-supervised",
        run_label="manual-freeze",
        status="snapshot",
        notes="first",
        recorded_at="2026-04-22T10:00:00+09:00",
    )

    (project / "project_data.db").write_bytes(b"v2")
    manifest = archive_benchmark_record(
        workspace_root=tmp_path,
        project="골든 카나리아",
        lane="stage4-supervised",
        run_label="manual-freeze",
        status="completed",
        notes="second",
        recorded_at="2026-04-22T10:00:00+09:00",
        overwrite=True,
    )

    record_root = Path(manifest["record_root"])
    assert (record_root / "snapshots" / "project_data.db").read_bytes() == b"v2"

    index_path = tmp_path / "benchmarks" / "benchmark_index.csv"
    with index_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["run_id"] == "20260422_100000__manual-freeze__target-open__nogit"
    assert rows[0]["status"] == "completed"
    assert rows[0]["notes"] == "second"
