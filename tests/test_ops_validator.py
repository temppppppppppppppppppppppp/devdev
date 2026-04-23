from pathlib import Path

from scripts.ops_validator import historical_backing_reason_from_canonical, run_validation


def _write_minimal_roadmap_pair(temp: Path, dated: Path) -> None:
    roadmap_body = "\n".join(
        [
            "# Active Temp Execution Roadmap",
            "Status: active",
            "Canonical Path: `docs/2026-04-23/active-temp-execution-roadmap.md`",
            "Temp Mirror Path: `docs/temp/execution-roadmap.md`",
            "",
            "Working order:",
            "1. `sample` (parked future wave)",
        ]
    )
    (dated / "active-temp-execution-roadmap.md").write_text(roadmap_body, encoding="utf-8")
    (temp / "execution-roadmap.md").write_text(roadmap_body, encoding="utf-8")


def test_historical_backing_reason_returns_none_for_active_parking(tmp_path):
    canonical = tmp_path / "active.md"
    canonical.write_text(
        "\n".join(
            [
                "# Example",
                "",
                "Date: 2026-04-23",
                "Status: parked (still-live future wave)",
                "Canonical Path: `docs/2026-04-23/example.md`",
                "Source Survey Docs: `docs/2026-04-23/example-survey.md`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert historical_backing_reason_from_canonical(canonical) is None


def test_historical_backing_reason_flags_closed_historical_backing(tmp_path):
    canonical = tmp_path / "closed.md"
    canonical.write_text(
        "\n".join(
            [
                "# Example",
                "",
                "Date: 2026-04-23",
                "Status: closed historical backing (compaction retired this lane from the visible queue)",
                "Canonical Path: `docs/2026-04-23/example.md`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    reason = historical_backing_reason_from_canonical(canonical)

    assert reason is not None
    assert "closed historical backing" in reason


def test_execution_meta_block_is_optional_during_migration(tmp_path, monkeypatch):
    root = tmp_path
    docs = root / "docs"
    temp = docs / "temp"
    dated = docs / "2026-04-23"
    temp.mkdir(parents=True)
    dated.mkdir(parents=True)
    (temp / "README.md").write_text("temp\n", encoding="utf-8")

    canonical = dated / "sample-execution-ssot.md"
    temp_doc = temp / "sample-execution-ssot.md"
    body = "\n".join(
        [
            "# Sample Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/sample-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/sample-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
            "",
            "## 1. Intent",
            "- body",
        ]
    )
    canonical.write_text(body, encoding="utf-8")
    temp_doc.write_text(body, encoding="utf-8")
    _write_minimal_roadmap_pair(temp, dated)
    (temp / "queue-state.json").write_text(
        """{
  "version": "temp-queue-state-v1",
  "generated_at": "2026-04-23T00:00:00+00:00",
  "queue_mode": "single",
  "active_item_count": 1,
  "roadmap": {
    "temp_path": "docs/temp/execution-roadmap.md",
    "canonical_path": "docs/2026-04-23/active-temp-execution-roadmap.md",
    "status": "active"
  },
  "items": [
    {
      "topic": "sample",
      "temp_path": "docs/temp/sample-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/sample-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 1,
      "depends_on": [],
      "mirror_present": true,
      "canonical_present": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.ops_validator.ROOT", root)
    monkeypatch.setattr("scripts.ops_validator.DOCS", docs)
    monkeypatch.setattr("scripts.ops_validator.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    assert run_validation(strict=True) == 0


def test_validator_flags_execution_meta_topic_mismatch_with_filename(tmp_path, monkeypatch, capsys):
    root = tmp_path
    docs = root / "docs"
    temp = docs / "temp"
    dated = docs / "2026-04-23"
    temp.mkdir(parents=True)
    dated.mkdir(parents=True)
    (temp / "README.md").write_text("temp\n", encoding="utf-8")

    canonical = dated / "sample-execution-ssot.md"
    temp_doc = temp / "sample-execution-ssot.md"
    body = "\n".join(
        [
            "# Sample Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/sample-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/sample-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
            "",
            "## 0. Execution Metadata Block",
            "",
            "```yaml",
            "execution_meta:",
            "  schema_version: execution-meta-block-v1",
            "  topic: wrong-topic",
            "  depends_on: []",
            "  tranches:",
            "    - id: first",
            "      title: First tranche",
            "```",
            "",
            "## 1. Intent",
            "- body",
        ]
    )
    canonical.write_text(body, encoding="utf-8")
    temp_doc.write_text(body, encoding="utf-8")
    _write_minimal_roadmap_pair(temp, dated)
    (temp / "queue-state.json").write_text(
        """{
  "version": "temp-queue-state-v1",
  "generated_at": "2026-04-23T00:00:00+00:00",
  "queue_mode": "single",
  "active_item_count": 1,
  "roadmap": {
    "temp_path": "docs/temp/execution-roadmap.md",
    "canonical_path": "docs/2026-04-23/active-temp-execution-roadmap.md",
    "status": "active"
  },
  "items": [
    {
      "topic": "sample",
      "temp_path": "docs/temp/sample-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/sample-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 1,
      "depends_on": [],
      "mirror_present": true,
      "canonical_present": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.ops_validator.ROOT", root)
    monkeypatch.setattr("scripts.ops_validator.DOCS", docs)
    monkeypatch.setattr("scripts.ops_validator.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    assert run_validation(strict=True) == 1
    assert "does not match expected topic sample" in capsys.readouterr().out


def test_validator_flags_execution_meta_invalid_depends_on_type(tmp_path, monkeypatch, capsys):
    root = tmp_path
    docs = root / "docs"
    temp = docs / "temp"
    dated = docs / "2026-04-23"
    temp.mkdir(parents=True)
    dated.mkdir(parents=True)
    (temp / "README.md").write_text("temp\n", encoding="utf-8")

    canonical = dated / "sample-execution-ssot.md"
    temp_doc = temp / "sample-execution-ssot.md"
    body = "\n".join(
        [
            "# Sample Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/sample-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/sample-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
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
            "",
            "## 1. Intent",
            "- body",
        ]
    )
    canonical.write_text(body, encoding="utf-8")
    temp_doc.write_text(body, encoding="utf-8")
    _write_minimal_roadmap_pair(temp, dated)
    (temp / "queue-state.json").write_text(
        """{
  "version": "temp-queue-state-v1",
  "generated_at": "2026-04-23T00:00:00+00:00",
  "queue_mode": "single",
  "active_item_count": 1,
  "roadmap": {
    "temp_path": "docs/temp/execution-roadmap.md",
    "canonical_path": "docs/2026-04-23/active-temp-execution-roadmap.md",
    "status": "active"
  },
  "items": [
    {
      "topic": "sample",
      "temp_path": "docs/temp/sample-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/sample-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 1,
      "depends_on": [],
      "mirror_present": true,
      "canonical_present": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.ops_validator.ROOT", root)
    monkeypatch.setattr("scripts.ops_validator.DOCS", docs)
    monkeypatch.setattr("scripts.ops_validator.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    assert run_validation(strict=True) == 1
    assert "depends_on must be a list" in capsys.readouterr().out


def test_validator_flags_queue_state_mismatch_against_block_metadata(tmp_path, monkeypatch, capsys):
    root = tmp_path
    docs = root / "docs"
    temp = docs / "temp"
    dated = docs / "2026-04-23"
    temp.mkdir(parents=True)
    dated.mkdir(parents=True)
    (temp / "README.md").write_text("temp\n", encoding="utf-8")

    canonical = dated / "sample-execution-ssot.md"
    temp_doc = temp / "sample-execution-ssot.md"
    body = "\n".join(
        [
            "# Sample Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/sample-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/sample-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
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
    )
    canonical.write_text(body, encoding="utf-8")
    temp_doc.write_text(body, encoding="utf-8")
    _write_minimal_roadmap_pair(temp, dated)
    (temp / "queue-state.json").write_text(
        """{
  "version": "temp-queue-state-v1",
  "generated_at": "2026-04-23T00:00:00+00:00",
  "queue_mode": "single",
  "active_item_count": 1,
  "roadmap": {
    "temp_path": "docs/temp/execution-roadmap.md",
    "canonical_path": "docs/2026-04-23/active-temp-execution-roadmap.md",
    "status": "active"
  },
  "items": [
    {
      "topic": "sample",
      "temp_path": "docs/temp/sample-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/sample-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 1,
      "depends_on": [],
      "mirror_present": true,
      "canonical_present": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.ops_validator.ROOT", root)
    monkeypatch.setattr("scripts.ops_validator.DOCS", docs)
    monkeypatch.setattr("scripts.ops_validator.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    assert run_validation(strict=True) == 1
    assert "does not match execution metadata block" in capsys.readouterr().out


def test_validator_ignores_optional_execution_meta_queue_fields_during_phase1(
    tmp_path, monkeypatch, capsys
):
    root = tmp_path
    docs = root / "docs"
    temp = docs / "temp"
    dated = docs / "2026-04-23"
    temp.mkdir(parents=True)
    dated.mkdir(parents=True)
    (temp / "README.md").write_text("temp\n", encoding="utf-8")

    canonical = dated / "sample-execution-ssot.md"
    temp_doc = temp / "sample-execution-ssot.md"
    body = "\n".join(
        [
            "# Sample Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/sample-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/sample-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
            "",
            "## 0. Execution Metadata Block",
            "",
            "```yaml",
            "execution_meta:",
            "  schema_version: execution-meta-block-v1",
            "  topic: sample",
            "  depends_on: []",
            "  tranches:",
            "    - id: first",
            "      title: First tranche",
            "  status: completed",
            "  queue_role: historical_backing",
            "  roadmap_rank: 9",
            "```",
            "",
            "## 1. Intent",
            "- body",
        ]
    )
    canonical.write_text(body, encoding="utf-8")
    temp_doc.write_text(body, encoding="utf-8")
    _write_minimal_roadmap_pair(temp, dated)
    (temp / "queue-state.json").write_text(
        """{
  "version": "temp-queue-state-v1",
  "generated_at": "2026-04-23T00:00:00+00:00",
  "queue_mode": "single",
  "active_item_count": 1,
  "roadmap": {
    "temp_path": "docs/temp/execution-roadmap.md",
    "canonical_path": "docs/2026-04-23/active-temp-execution-roadmap.md",
    "status": "active"
  },
  "items": [
    {
      "topic": "sample",
      "temp_path": "docs/temp/sample-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/sample-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 1,
      "depends_on": [],
      "mirror_present": true,
      "canonical_present": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.ops_validator.ROOT", root)
    monkeypatch.setattr("scripts.ops_validator.DOCS", docs)
    monkeypatch.setattr("scripts.ops_validator.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    assert run_validation(strict=True) == 0
    assert "does not match execution metadata" not in capsys.readouterr().out


def test_validator_flags_queue_state_non_list_depends_on_without_crashing(tmp_path, monkeypatch, capsys):
    root = tmp_path
    docs = root / "docs"
    temp = docs / "temp"
    dated = docs / "2026-04-23"
    temp.mkdir(parents=True)
    dated.mkdir(parents=True)
    (temp / "README.md").write_text("temp\n", encoding="utf-8")

    canonical = dated / "sample-execution-ssot.md"
    temp_doc = temp / "sample-execution-ssot.md"
    body = "\n".join(
        [
            "# Sample Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/sample-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/sample-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
            "",
            "## 1. Intent",
            "- body",
        ]
    )
    canonical.write_text(body, encoding="utf-8")
    temp_doc.write_text(body, encoding="utf-8")
    _write_minimal_roadmap_pair(temp, dated)
    (temp / "queue-state.json").write_text(
        """{
  "version": "temp-queue-state-v1",
  "generated_at": "2026-04-23T00:00:00+00:00",
  "queue_mode": "single",
  "active_item_count": 1,
  "roadmap": {
    "temp_path": "docs/temp/execution-roadmap.md",
    "canonical_path": "docs/2026-04-23/active-temp-execution-roadmap.md",
    "status": "active"
  },
  "items": [
    {
      "topic": "sample",
      "temp_path": "docs/temp/sample-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/sample-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 1,
      "depends_on": 1,
      "mirror_present": true,
      "canonical_present": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.ops_validator.ROOT", root)
    monkeypatch.setattr("scripts.ops_validator.DOCS", docs)
    monkeypatch.setattr("scripts.ops_validator.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    assert run_validation(strict=True) == 1
    assert "depends_on must be a list of non-empty strings" in capsys.readouterr().out


def test_validator_allows_queue_state_rank_aligned_dependency(tmp_path, monkeypatch):
    root = tmp_path
    docs = root / "docs"
    temp = docs / "temp"
    dated = docs / "2026-04-23"
    temp.mkdir(parents=True)
    dated.mkdir(parents=True)
    (temp / "README.md").write_text("temp\n", encoding="utf-8")

    canonical_alpha = dated / "alpha-execution-ssot.md"
    temp_alpha = temp / "alpha-execution-ssot.md"
    alpha_body = "\n".join(
        [
            "# Alpha Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/alpha-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/alpha-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
            "",
            "## 0. Execution Metadata Block",
            "",
            "```yaml",
            "execution_meta:",
            "  schema_version: execution-meta-block-v1",
            "  topic: alpha",
            "  depends_on: []",
            "  tranches:",
            "    - id: first",
            "      title: First tranche",
            "```",
            "",
            "## 1. Intent",
            "- body",
        ]
    )
    canonical_alpha.write_text(alpha_body, encoding="utf-8")
    temp_alpha.write_text(alpha_body, encoding="utf-8")

    canonical_beta = dated / "beta-execution-ssot.md"
    temp_beta = temp / "beta-execution-ssot.md"
    beta_body = "\n".join(
        [
            "# Beta Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/beta-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/beta-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
            "",
            "## 0. Execution Metadata Block",
            "",
            "```yaml",
            "execution_meta:",
            "  schema_version: execution-meta-block-v1",
            "  topic: beta",
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
    )
    canonical_beta.write_text(beta_body, encoding="utf-8")
    temp_beta.write_text(beta_body, encoding="utf-8")

    roadmap_body = "\n".join(
        [
            "# Active Temp Execution Roadmap",
            "Status: active",
            "Canonical Path: `docs/2026-04-23/active-temp-execution-roadmap.md`",
            "Temp Mirror Path: `docs/temp/execution-roadmap.md`",
            "",
            "Working order:",
            "1. `alpha` (parked future wave)",
            "2. `beta` (parked future wave)",
        ]
    )
    (dated / "active-temp-execution-roadmap.md").write_text(roadmap_body, encoding="utf-8")
    (temp / "execution-roadmap.md").write_text(roadmap_body, encoding="utf-8")
    (temp / "queue-state.json").write_text(
        """{
  "version": "temp-queue-state-v1",
  "generated_at": "2026-04-23T00:00:00+00:00",
  "queue_mode": "aggregate",
  "active_item_count": 2,
  "roadmap": {
    "temp_path": "docs/temp/execution-roadmap.md",
    "canonical_path": "docs/2026-04-23/active-temp-execution-roadmap.md",
    "status": "active"
  },
  "items": [
    {
      "topic": "alpha",
      "temp_path": "docs/temp/alpha-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/alpha-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 1,
      "depends_on": [],
      "mirror_present": true,
      "canonical_present": true
    },
    {
      "topic": "beta",
      "temp_path": "docs/temp/beta-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/beta-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 2,
      "depends_on": [
        "alpha"
      ],
      "mirror_present": true,
      "canonical_present": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.ops_validator.ROOT", root)
    monkeypatch.setattr("scripts.ops_validator.DOCS", docs)
    monkeypatch.setattr("scripts.ops_validator.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    assert run_validation(strict=True) == 0


def test_validator_flags_queue_state_rank_inversion(tmp_path, monkeypatch, capsys):
    root = tmp_path
    docs = root / "docs"
    temp = docs / "temp"
    dated = docs / "2026-04-23"
    temp.mkdir(parents=True)
    dated.mkdir(parents=True)
    (temp / "README.md").write_text("temp\n", encoding="utf-8")

    canonical_alpha = dated / "alpha-execution-ssot.md"
    temp_alpha = temp / "alpha-execution-ssot.md"
    alpha_body = "\n".join(
        [
            "# Alpha Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/alpha-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/alpha-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
            "",
            "## 0. Execution Metadata Block",
            "",
            "```yaml",
            "execution_meta:",
            "  schema_version: execution-meta-block-v1",
            "  topic: alpha",
            "  depends_on: []",
            "  tranches:",
            "    - id: first",
            "      title: First tranche",
            "```",
            "",
            "## 1. Intent",
            "- body",
        ]
    )
    canonical_alpha.write_text(alpha_body, encoding="utf-8")
    temp_alpha.write_text(alpha_body, encoding="utf-8")

    canonical_beta = dated / "beta-execution-ssot.md"
    temp_beta = temp / "beta-execution-ssot.md"
    beta_body = "\n".join(
        [
            "# Beta Execution SSOT",
            "Status: execution-ready",
            "Canonical Path: `docs/2026-04-23/beta-execution-ssot.md`",
            "Temp Mirror Path: `docs/temp/beta-execution-ssot.md`",
            "Source Survey Docs:",
            "- `docs/2026-04-23/example.md`",
            "",
            "## 0. Execution Metadata Block",
            "",
            "```yaml",
            "execution_meta:",
            "  schema_version: execution-meta-block-v1",
            "  topic: beta",
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
    )
    canonical_beta.write_text(beta_body, encoding="utf-8")
    temp_beta.write_text(beta_body, encoding="utf-8")

    roadmap_body = "\n".join(
        [
            "# Active Temp Execution Roadmap",
            "Status: active",
            "Canonical Path: `docs/2026-04-23/active-temp-execution-roadmap.md`",
            "Temp Mirror Path: `docs/temp/execution-roadmap.md`",
            "",
            "Working order:",
            "1. `beta` (parked future wave)",
            "2. `alpha` (parked future wave)",
        ]
    )
    (dated / "active-temp-execution-roadmap.md").write_text(roadmap_body, encoding="utf-8")
    (temp / "execution-roadmap.md").write_text(roadmap_body, encoding="utf-8")
    (temp / "queue-state.json").write_text(
        """{
  "version": "temp-queue-state-v1",
  "generated_at": "2026-04-23T00:00:00+00:00",
  "queue_mode": "aggregate",
  "active_item_count": 2,
  "roadmap": {
    "temp_path": "docs/temp/execution-roadmap.md",
    "canonical_path": "docs/2026-04-23/active-temp-execution-roadmap.md",
    "status": "active"
  },
  "items": [
    {
      "topic": "beta",
      "temp_path": "docs/temp/beta-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/beta-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 1,
      "depends_on": [
        "alpha"
      ],
      "mirror_present": true,
      "canonical_present": true
    },
    {
      "topic": "alpha",
      "temp_path": "docs/temp/alpha-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/alpha-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 2,
      "depends_on": [],
      "mirror_present": true,
      "canonical_present": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.ops_validator.ROOT", root)
    monkeypatch.setattr("scripts.ops_validator.DOCS", docs)
    monkeypatch.setattr("scripts.ops_validator.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    assert run_validation(strict=True) == 1
    assert "rank inversion" in capsys.readouterr().out
