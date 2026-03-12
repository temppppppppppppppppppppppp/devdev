from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from modules.core.artifact_logging import build_candidate_key, snapshot_logged_artifact


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
    assert (tmp_path / result["artifact_path"]).read_text(encoding="utf-8") == "hello world"


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
