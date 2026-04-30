from pathlib import Path

from modules.core.stage4_truth_manifest import (
    build_stage4_truth_manifest,
    normalize_manuscript_for_equivalence,
    verify_stage4_truth_manifest,
)


def test_truth_manifest_equivalent_for_exact_raw_match(tmp_path: Path):
    manuscript = "first paragraph\n\nsecond paragraph"
    artifact = tmp_path / "logs" / "artifacts" / "stage4" / "ep_0001" / "attempt_01"
    artifact.mkdir(parents=True)
    artifact_path = artifact / "final_manuscript__A.txt"
    artifact_path.write_text(manuscript, encoding="utf-8")

    manifest = build_stage4_truth_manifest(
        ep_num=1,
        title="Title",
        db_manuscript=manuscript,
        draft_path="drafts/ep_0001.txt",
        artifact_meta={"artifact_path": artifact_path.relative_to(tmp_path).as_posix(), "attempt_key": "attempt-1"},
        project_root=tmp_path,
        settlement_path="drafts/ep_0001.settlement.json",
        fully_settled=True,
    )

    assert manifest["equivalent"] is True
    assert manifest["reasons"] == []
    assert manifest["accepted_attempt_key"] == "attempt-1"
    assert manifest["artifact_class"] == "final_manuscript"
    assert manifest["entries"]["final_artifact"]["raw_byte_hash"] == manifest["entries"]["final_artifact"]["raw_hash"]


def test_truth_manifest_equivalent_for_title_header_and_blank_lines(tmp_path: Path):
    manuscript = "first paragraph\n\nsecond paragraph"
    artifact_path = tmp_path / "artifact.txt"
    artifact_path.write_text("# Title\n\nfirst paragraph\n\n\nsecond paragraph", encoding="utf-8")

    manifest = build_stage4_truth_manifest(
        ep_num=1,
        title="Title",
        db_manuscript=manuscript,
        draft_path="drafts/ep_0001.txt",
        artifact_meta={"artifact_path": artifact_path.as_posix()},
        project_root=tmp_path,
    )

    artifact_norm = manifest["entries"]["final_artifact"]["normalization"]
    draft_norm = manifest["entries"]["human_facing_draft"]["normalization"]
    assert manifest["equivalent"] is True
    assert artifact_norm["title_header_normalization_applied"] is True
    assert artifact_norm["blank_line_normalization_applied"] is True
    assert draft_norm["title_header_normalization_applied"] is True


def test_truth_manifest_equivalent_for_line_endings():
    normalized, flags = normalize_manuscript_for_equivalence("a\r\n\r\nb", title="")

    assert normalized == "a\n\nb"
    assert flags["line_ending_normalization_applied"] is True


def test_truth_manifest_detects_true_content_mismatch(tmp_path: Path):
    artifact_path = tmp_path / "artifact.txt"
    artifact_path.write_text("different content", encoding="utf-8")

    manifest = build_stage4_truth_manifest(
        ep_num=1,
        title="Title",
        db_manuscript="original content",
        draft_path="drafts/ep_0001.txt",
        artifact_meta={"artifact_path": artifact_path.as_posix()},
        project_root=tmp_path,
    )

    assert manifest["equivalent"] is False
    assert "normalized_hash_mismatch" in manifest["reasons"]
    verdict = verify_stage4_truth_manifest(manifest)
    assert verdict["equivalent"] is False
    assert verdict["severity"] == "warning"


def test_truth_manifest_missing_artifact_is_not_equivalent(tmp_path: Path):
    manifest = build_stage4_truth_manifest(
        ep_num=1,
        title="Title",
        db_manuscript="original content",
        draft_path="drafts/ep_0001.txt",
        artifact_meta={"artifact_path": "logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__A.txt"},
        project_root=tmp_path,
    )

    assert manifest["equivalent"] is False
    assert "final_artifact_missing" in manifest["reasons"]
    verdict = verify_stage4_truth_manifest(manifest)
    assert verdict["severity"] == "blocker"
