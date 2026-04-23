from pathlib import Path

from scripts.ops_validator import historical_backing_reason_from_canonical


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
