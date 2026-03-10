"""FailureAnalyzer success-pattern and quality-distribution tests."""

from modules.core.db_manager import DBManager
from modules.core.failure_analyzer import FailureAnalyzer


def test_failure_analyzer_quality_distribution_and_success_patterns(tmp_path):
    db = DBManager(tmp_path / "test.db")
    try:
        db.save_episode_quality_label(
            10,
            {
                "score": 95,
                "verdict": "PASS",
                "selection_reason": "몰입감과 연속성이 좋음",
                "open_review": "특이사항 없음",
                "score_breakdown": {
                    "continuity_contradiction": 39,
                    "blueprint_coverage": 19,
                    "quality_engagement": 19,
                },
                "consistency_checklist": {
                    "scene_variety": "OK",
                    "pacing_quality": "OK",
                    "dialogue_naturalness": "OK",
                },
            },
        )
        db.save_episode_quality_label(
            11,
            {
                "score": 92,
                "verdict": "PASS_WITH_FIX",
                "selection_reason": "연속성과 대화가 안정적",
                "open_review": "후반만 조금 보강",
                "score_breakdown": {
                    "continuity_contradiction": 38,
                    "blueprint_coverage": 18,
                    "quality_engagement": 18,
                },
                "consistency_checklist": {
                    "scene_variety": "OK",
                    "pacing_quality": "OK",
                    "dialogue_naturalness": "OK",
                },
            },
        )

        analyzer = FailureAnalyzer(db)
        distribution = analyzer.quality_distribution()
        patterns = analyzer.top_success_patterns(top_n=3)

        assert distribution["count"] == 2
        assert distribution["high_score_count"] == 2
        assert distribution["pass_with_fix_count"] == 1
        assert any("평균" in item["description"] for item in patterns)
        assert any("OK 비율 높음" in item["description"] for item in patterns)
    finally:
        db.close()


def test_failure_analyzer_compare_versions(tmp_path):
    db = DBManager(tmp_path / "test_compare_versions.db")
    try:
        db.save_stage_attempt(stage=4, verdict="PASS", ep_num=10, arc_num=3, score=91, prompt_version="chief@v1")
        db.save_stage_attempt(stage=4, verdict="REJECT", ep_num=11, arc_num=3, score=74, prompt_version="chief@v1")
        db.save_stage_attempt(stage=4, verdict="PASS", ep_num=12, arc_num=4, score=95, prompt_version="chief@v2")
        db.save_stage_attempt(stage=4, verdict="PASS_WITH_FIX", ep_num=13, arc_num=4, score=89, prompt_version="chief@v2")

        analyzer = FailureAnalyzer(db)
        result = analyzer.compare_versions("chief@v1", "chief@v2", stage=4)

        assert result["versions"]["chief@v1"]["attempts"] == 2
        assert result["versions"]["chief@v1"]["pass_rate_pct"] == 50.0
        assert result["versions"]["chief@v2"]["pass_rate_pct"] == 100.0
        assert result["avg_score_delta"] == 9.5
        assert result["winner"] == "chief@v2"
    finally:
        db.close()
