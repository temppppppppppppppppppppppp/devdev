from __future__ import annotations

import pytest

from scripts.sync_temp_queue_state import (
    build_item_payload,
    load_execution_meta_block,
    validate_dependency_graph,
)


def test_load_execution_meta_block_returns_none_when_absent(tmp_path):
    path = tmp_path / "sample-execution-ssot.md"
    path.write_text(
        "# Sample Execution SSOT\n\nStatus: execution-ready\n\n## 1. Intent\n- no block here\n",
        encoding="utf-8",
    )

    assert load_execution_meta_block(path, expected_topic="sample") is None


def test_load_execution_meta_block_reads_first_yaml_block_under_metadata_heading(tmp_path):
    path = tmp_path / "sample-execution-ssot.md"
    path.write_text(
        "\n".join(
            [
                "# Sample Execution SSOT",
                "",
                "## 0. Execution Metadata Block",
                "",
                "```yaml",
                "execution_meta:",
                "  schema_version: execution-meta-block-v1",
                "  topic: sample",
                "  depends_on:",
                "    - alpha",
                "  tranches:",
                "    - id: first",
                "      title: First tranche",
                "```",
                "",
                "## 1. Intent",
                "- body",
            ]
        ),
        encoding="utf-8",
    )

    block = load_execution_meta_block(path, expected_topic="sample")

    assert block is not None
    assert block["topic"] == "sample"
    assert block["depends_on"] == ["alpha"]
    assert block["tranches"] == [{"id": "first", "title": "First tranche"}]


def test_load_execution_meta_block_ignores_yaml_outside_metadata_heading(tmp_path):
    path = tmp_path / "sample-execution-ssot.md"
    path.write_text(
        "\n".join(
            [
                "# Sample Execution SSOT",
                "",
                "```yaml",
                "execution_meta:",
                "  schema_version: execution-meta-block-v1",
                "  topic: sample",
                "  depends_on: []",
                "  tranches:",
                "    - id: stray",
                "      title: Stray",
                "```",
                "",
                "## 1. Intent",
                "- body",
            ]
        ),
        encoding="utf-8",
    )

    assert load_execution_meta_block(path, expected_topic="sample") is None


def test_build_item_payload_prefers_execution_meta_depends_on_when_present(tmp_path, monkeypatch):
    root = tmp_path
    temp_dir = root / "docs" / "temp"
    temp_dir.mkdir(parents=True)
    temp_doc = temp_dir / "sample-execution-ssot.md"
    canonical = root / "docs" / "2026-04-23" / "sample-execution-ssot.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("# canonical\n", encoding="utf-8")
    temp_doc.write_text(
        "\n".join(
            [
                "# Sample Execution SSOT",
                "Canonical Path: `docs/2026-04-23/sample-execution-ssot.md`",
                "Status: execution-ready",
                "",
                "## 0. Execution Metadata Block",
                "",
                "```yaml",
                "execution_meta:",
                "  schema_version: execution-meta-block-v1",
                "  topic: sample",
                "  depends_on:",
                "    - alpha",
                "    - beta",
                "  tranches:",
                "    - id: first",
                "      title: First tranche",
                "```",
                "",
                "## 1. Intent",
                "- body",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    payload = build_item_payload(
        temp_doc,
        roadmap_item_context={"sample": {"roadmap_rank": 2, "queue_role": "parked_future_wave"}},
    )

    assert payload["depends_on"] == ["alpha", "beta"]
    assert payload["queue_role"] == "parked_future_wave"
    assert payload["roadmap_rank"] == 2


def test_build_item_payload_falls_back_to_legacy_metadata_when_block_absent(tmp_path, monkeypatch):
    root = tmp_path
    temp_dir = root / "docs" / "temp"
    temp_dir.mkdir(parents=True)
    temp_doc = temp_dir / "sample-execution-ssot.md"
    canonical = root / "docs" / "2026-04-23" / "sample-execution-ssot.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("# canonical\n", encoding="utf-8")
    temp_doc.write_text(
        "\n".join(
            [
                "# Sample Execution SSOT",
                "Canonical Path: `docs/2026-04-23/sample-execution-ssot.md`",
                "Status: parked future wave",
                "",
                "## 1. Intent",
                "- body",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    payload = build_item_payload(
        temp_doc,
        roadmap_item_context={"sample": {"roadmap_rank": 4, "queue_role": "parked_future_wave"}},
    )

    assert payload["depends_on"] == []
    assert payload["status"] == "pending"
    assert payload["queue_role"] == "parked_future_wave"
    assert payload["roadmap_rank"] == 4


def test_load_execution_meta_block_rejects_malformed_depends_on(tmp_path):
    path = tmp_path / "sample-execution-ssot.md"
    path.write_text(
        "\n".join(
            [
                "# Sample Execution SSOT",
                "",
                "## 0. Execution Metadata Block",
                "",
                "```yaml",
                "execution_meta:",
                "  schema_version: execution-meta-block-v1",
                "  topic: sample",
                "  depends_on: alpha",
                "  tranches:",
                "    - id: first",
                "      title: First tranche",
                "```",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="depends_on"):
        load_execution_meta_block(path, expected_topic="sample")


def test_load_execution_meta_block_rejects_duplicate_depends_on(tmp_path):
    path = tmp_path / "sample-execution-ssot.md"
    path.write_text(
        "\n".join(
            [
                "# Sample Execution SSOT",
                "",
                "## 0. Execution Metadata Block",
                "",
                "```yaml",
                "execution_meta:",
                "  schema_version: execution-meta-block-v1",
                "  topic: sample",
                "  depends_on:",
                "    - alpha",
                "    - alpha",
                "  tranches:",
                "    - id: first",
                "      title: First tranche",
                "```",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate"):
        load_execution_meta_block(path, expected_topic="sample")


def test_validate_dependency_graph_rejects_cycles():
    items = [
        {"topic": "alpha", "depends_on": ["beta"]},
        {"topic": "beta", "depends_on": ["alpha"]},
    ]

    with pytest.raises(ValueError, match="cycle detected"):
        validate_dependency_graph(items)


def test_validate_dependency_graph_rejects_non_list_depends_on():
    items = [{"topic": "alpha", "depends_on": "beta"}]

    with pytest.raises(ValueError, match="depends_on must be a list"):
        validate_dependency_graph(items)


def test_validate_dependency_graph_allows_rank_aligned_dependencies():
    items = [
        {"topic": "alpha", "depends_on": [], "roadmap_rank": 1},
        {"topic": "beta", "depends_on": ["alpha"], "roadmap_rank": 2},
    ]

    validate_dependency_graph(items)


def test_validate_dependency_graph_rejects_rank_inversion():
    items = [
        {"topic": "alpha", "depends_on": [], "roadmap_rank": 2},
        {"topic": "beta", "depends_on": ["alpha"], "roadmap_rank": 1},
    ]

    with pytest.raises(ValueError, match="rank inversion"):
        validate_dependency_graph(items)


@pytest.mark.parametrize(
    ("alpha_rank", "beta_rank"),
    [
        (None, 2),
        (1, None),
    ],
)
def test_validate_dependency_graph_allows_missing_rank_on_either_side(alpha_rank, beta_rank):
    items = [
        {"topic": "alpha", "depends_on": [], "roadmap_rank": alpha_rank},
        {"topic": "beta", "depends_on": ["alpha"], "roadmap_rank": beta_rank},
    ]

    validate_dependency_graph(items)
