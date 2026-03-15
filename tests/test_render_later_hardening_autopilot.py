from __future__ import annotations

from scripts.render_later_hardening_autopilot import (
    HitSummary,
    RuffStat,
    Snapshot,
    build_prompt,
    parse_remaining_tfs,
    parse_ruff_statistics,
)


def test_parse_remaining_tfs_prefers_later_hardening_tranche():
    lane_text = """
    lane status decision:
      - keep this integrated lane active only for the later hardening tranche: `TF-014`, `TF-015`, `TF-016`, and `TF-019`
    """
    assert parse_remaining_tfs(lane_text) == ["TF-014", "TF-015", "TF-016", "TF-019"]


def test_parse_ruff_statistics_extracts_totals_and_breakdown():
    output = """
    20  I001   [*] unsorted-imports
     9 E402   [ ] module-import-not-at-top-of-file
    Found 66 errors.
    [*] 53 fixable with the `--fix` option.
    """
    total, fixable, stats = parse_ruff_statistics(output)
    assert total == 66
    assert fixable == 53
    assert stats[0].code == "I001"
    assert stats[0].count == 20
    assert stats[1].fixable_marker == " "


def test_build_prompt_includes_order_and_live_signals():
    snapshot = Snapshot(
        head="abc123",
        dirty_summary="dirty: 2 modified, 0 deleted, 1 untracked",
        remaining_tfs=["TF-014", "TF-015", "TF-016", "TF-019"],
        next_tf="TF-014",
        lane_status="active",
        roadmap_status="active",
        print_hits=HitSummary(total_hits=179, top_paths=[(48, "modules/core/stage0/spinner.py")]),
        guard_hits=HitSummary(total_hits=42, top_paths=[(12, "modules/core/genre_guards/work_guard.py")]),
        ruff_total_errors=66,
        ruff_fixable_errors=53,
        ruff_stats=[RuffStat(code="I001", count=20, fixable_marker="*", label="unsorted-imports")],
    )
    rendered = build_prompt(snapshot)
    assert "TF-014 Console Print Audit" in rendered
    assert "TF-019 Guard Chain Config Validation" in rendered
    assert "179 hits" in rendered
    assert "66 errors, 53 fixable" in rendered
