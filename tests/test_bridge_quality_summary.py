import asyncio
import json

from modules.api import bridge_server
from modules.core.db_manager import DBManager


def test_quality_summary_endpoint_reads_project_sidecar(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_server, "PROJECT_ROOT", tmp_path)
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True)

    db = DBManager(project_dir / "project_data.db")
    db.save_episode_quality_signal(
        3,
        {
            "ced_score": 1.1,
            "ai_slop_score": 0.8,
            "ai_slop_hits": [{"pattern": "그야말로", "count": 1}],
            "compression_ratio": 0.31,
            "burstiness": 9.4,
            "complexity": 28.8,
            "signal_summary": {"sentence_count": 37},
        },
    )
    db.close()

    response = asyncio.run(bridge_server.quality_summary_endpoint(project="demo", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["data"]["available"] is True
    assert payload["data"]["latest_ep"] == 3
    assert payload["data"]["signals"]["ced"]["value"] == 1.1


def test_quality_summary_endpoint_rejects_missing_project():
    response = asyncio.run(bridge_server.quality_summary_endpoint(project="", lookback=5))
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 400
    assert payload["code"] == "INVALID_PROJECT"
