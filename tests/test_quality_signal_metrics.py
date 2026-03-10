from modules.core.quality_signal_metrics import (
    build_signal_stat,
    compute_quality_signal_bundle,
    extract_warning_count,
)


def test_compute_quality_signal_bundle_extracts_python_only_metrics():
    text = (
        "그야말로 숨을 삼켰다. 어느새 입을 열었다. "
        "말 그대로 시선을 돌렸다. 고개를 끄덕였다."
    )
    bundle = compute_quality_signal_bundle(
        text,
        consistency_checklist={
            "scene_variety": "ISSUE",
            "pacing_quality": {"status": "WARN"},
        },
        warning_count=2,
    )

    assert bundle["ced_score"] > 0
    assert bundle["ai_slop_score"] > 0
    assert bundle["compression_ratio"] > 0
    assert bundle["burstiness"] >= 0
    assert bundle["complexity"] > 0
    assert bundle["signal_summary"]["ced_breakdown"]["issue_count"] == 2
    assert bundle["signal_summary"]["ced_breakdown"]["warning_count"] == 2
    assert bundle["ai_slop_hits"]


def test_extract_warning_count_supports_multiple_shapes():
    payload = {
        "warnings": ["a", "b"],
        "validator_warnings": {"continuity": "warn"},
        "structured_warning_count": 2,
    }

    assert extract_warning_count(payload) == 3


def test_build_signal_stat_handles_lower_better_and_deviation_modes():
    lower_better = build_signal_stat(
        field="ced_score",
        recent_rows=[
            {"ced_score": 1.2},
            {"ced_score": 1.0},
            {"ced_score": 0.8},
        ],
        mode="lower_better",
    )
    deviation = build_signal_stat(
        field="compression_ratio",
        recent_rows=[
            {"compression_ratio": 0.34},
            {"compression_ratio": 0.33},
            {"compression_ratio": 0.47},
        ],
        mode="deviation",
    )

    assert lower_better["status"] == "good"
    assert lower_better["trend"] == "down"
    assert deviation["status"] == "alert"
