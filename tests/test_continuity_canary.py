from modules.core.continuity_canary import (
    evaluate_continuity_canaries,
    merge_continuity_canary_reports,
)


def test_continuity_canaries_flag_date_location_dead_character_and_replay():
    report = evaluate_continuity_canaries(
        projection={
            "accepted_source_state": {
                "time_flow": "2006-01-03 evening",
                "end_location": "boardroom",
            }
        },
        candidate={
            "time_flow": "2006-01-01 evening",
            "start_location": "lobby",
            "scene_breakdown": [
                {
                    "participants": ["Seo", "Dead Mentor"],
                    "summary": "The same Jan1/Jan3 conflict repeats unchanged.",
                }
            ],
        },
        dead_characters=["Dead Mentor"],
        prior_failure_signatures=["jan1/jan3 conflict"],
    )

    finding_ids = {finding["canary_id"] for finding in report["findings"]}
    assert report["status"] == "review_required"
    assert finding_ids == {
        "date_drift",
        "location_drift",
        "dead_character_active_role",
        "prior_failure_replay",
    }
    assert all(finding["requires_director_review"] for finding in report["findings"])
    assert all(finding["judgment_authority"] == "director_llm" for finding in report["findings"])


def test_location_canary_allows_explicit_transition_marker():
    report = evaluate_continuity_canaries(
        projection={"accepted_source_state": {"end_location": "boardroom"}},
        candidate={
            "start_location": "lobby",
            "integrated_scenario": "* * *\nAfter the scene cut, Seo waits in the lobby.",
        },
    )

    assert report["status"] == "ok"
    assert report["findings"] == []


def test_merge_continuity_canary_reports_promotes_review_required():
    merged = merge_continuity_canary_reports(
        [
            {"status": "ok", "findings": []},
            {
                "status": "review_required",
                "findings": [
                    {
                        "canary_id": "date_drift",
                        "requires_director_review": True,
                    }
                ],
            },
        ]
    )

    assert merged["status"] == "review_required"
    assert merged["finding_count"] == 1
