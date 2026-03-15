import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from modules.core.artifact_logging import build_candidate_key, normalize_artifact_meta, snapshot_logged_artifact


def _project(root: Path):
    return SimpleNamespace(paths=SimpleNamespace(root=root))


def test_build_candidate_key_prefers_label_and_strategy():
    assert build_candidate_key(label="A", strategy="balanced", fallback="stage4") == "A|balanced"
    assert build_candidate_key(label="", strategy="", fallback="stage4") == "stage4"


def test_snapshot_logged_artifact_persists_and_returns_linkage(tmp_path):
    project = _project(tmp_path)

    result = snapshot_logged_artifact(
        project,
        stage=4,
        ep_num=7,
        attempt_num=2,
        candidate_key="A|balanced",
        artifact_kind="selected_before_fix",
        payload="hello world",
    )

    assert result["candidate_key"] == "A|balanced"
    assert result["content_hash"]
    assert result["artifact_path"].endswith("selected_before_fix__A_balanced.txt")
    persisted = (tmp_path / result["artifact_path"]).read_bytes()
    assert persisted.decode("utf-8") == "hello world"
    assert result["content_hash"] == hashlib.sha256(persisted).hexdigest()


def test_snapshot_logged_artifact_hash_matches_persisted_json_bytes(tmp_path):
    project = _project(tmp_path)

    result = snapshot_logged_artifact(
        project,
        stage=3,
        ep_num=4,
        attempt_num=1,
        candidate_key="blueprint",
        artifact_kind="integrated_blueprint",
        payload={"title": "Blueprint", "scene_count": 3},
    )

    persisted = (tmp_path / result["artifact_path"]).read_bytes()

    assert persisted.decode("utf-8").startswith("{\n")
    assert result["content_hash"] == hashlib.sha256(persisted).hexdigest()


def test_snapshot_logged_artifact_write_failure_is_soft_failure(tmp_path):
    project = _project(tmp_path)

    with patch("modules.core.artifact_logging._write_artifact_snapshot", side_effect=OSError("disk full")):
        result = snapshot_logged_artifact(
            project,
            stage=4,
            ep_num=7,
            attempt_num=2,
            candidate_key="A|balanced",
            artifact_kind="selected_before_fix",
            payload="hello world",
        )

    assert result["candidate_key"] == "A|balanced"
    assert result["content_hash"]
    assert result["artifact_path"] == ""
    soft_failures = tmp_path / "logs" / "soft_failures.jsonl"
    assert soft_failures.exists()
    assert "artifact_logging" in soft_failures.read_text(encoding="utf-8")


def test_normalize_artifact_meta_fills_missing_fields():
    result = normalize_artifact_meta({"candidate_key": "A|balanced"}, fallback_artifact_path="logs/x.txt")

    assert result == {
        "candidate_key": "A|balanced",
        "content_hash": "",
        "artifact_path": "logs/x.txt",
    }
