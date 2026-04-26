from modules.core.session_memory_envelope import (
    SESSION_MEMORY_ENVELOPE_KEY,
    SESSION_MEMORY_ENVELOPE_VERSION,
    attach_session_memory_envelope,
    build_stage4_session_memory_envelope,
    get_session_memory_envelope,
)


def test_build_stage4_session_memory_envelope_collects_retry_and_truth_surfaces():
    envelope = build_stage4_session_memory_envelope(
        episode=2,
        round_num=1,
        arc=3,
        success=False,
        score=61,
        verdict="REJECT",
        reject_reason="retry needed",
        fix_scope="partial",
        advisory_flags={
            "gate_semantics": {
                "truth_pins": {"ledger": "position=40"},
                "conflict_resolution_linkage": {"original_contract_type": "timeline"},
            },
            "retry_budget_axes": {"repair": "patch_revision"},
            "coverage_warnings": ["missing relation recovery"],
            "cache_lineage": {"cached_content": "projects/cache/abc"},
        },
        session_id="sess-stage4",
        attempt_key="s4:ep2:arc3:a2:sess-stage4",
        artifact_meta={
            "candidate_key": "A|balanced",
            "content_hash": "hash123",
            "artifact_path": "logs/final.txt",
        },
        selection_reason="best candidate",
        verdict_reason="conflict",
        open_review="repeat detected",
        fix_scope_reasoning="bounded fix",
        runtime_advisory="keep continuity",
        retry_directives="change ending",
        failure_category="LOGIC_ERROR",
        initial_verdict="PASS_WITH_FIX",
        is_patch=True,
        is_patch_fallback=False,
        patch_strategy="patch_with_feedback",
    )

    assert envelope["schema_version"] == SESSION_MEMORY_ENVELOPE_VERSION
    assert envelope["source"] == "stage4_attempt"
    assert envelope["attempt_key"] == "s4:ep2:arc3:a2:sess-stage4"
    assert envelope["candidate"]["candidate_key"] == "A|balanced"
    assert envelope["verdict_surface"]["accepted"] is False
    assert envelope["verdict_surface"]["initial_verdict"] == "PASS_WITH_FIX"
    assert envelope["retry_surface"]["retry_directives"] == "change ending"
    assert envelope["retry_surface"]["reject_bucket"] == ""
    assert envelope["retry_surface"]["authority_schema_version"] == "advisory-authority-levels-v1"
    assert envelope["retry_surface"]["authority_levels"] == {"retry_budget_axes": "route"}
    assert envelope["retry_surface"]["retry_budget_axes"] == {"repair": "patch_revision"}
    assert envelope["truth_pins"] == {"ledger": "position=40"}
    assert envelope["carryover_refs"] == {"original_contract_type": "timeline"}
    assert envelope["coverage_warnings"] == ["missing relation recovery"]
    assert envelope["cache_lineage"] == {"cached_content": "projects/cache/abc"}


def test_build_stage4_session_memory_envelope_preserves_authoritative_continuity_projection():
    envelope = build_stage4_session_memory_envelope(
        episode=2,
        round_num=0,
        arc=1,
        success=False,
        score=70,
        verdict="REJECT",
        reject_reason="timeline drift",
        fix_scope="partial",
        advisory_flags={
            "authoritative_continuity_projection": {
                "schema_version": "authoritative-continuity-projection-v1",
                "accepted_source_state": {"end_location": "boardroom"},
            }
        },
        session_id="sess-stage4",
        attempt_key="s4:ep2:arc1:a1:sess-stage4",
        artifact_meta={},
        selection_reason="candidate drifted least",
        verdict_reason="needs bridge",
        open_review="timeline reset",
        fix_scope_reasoning="bounded continuity repair",
        runtime_advisory="use source state",
        retry_directives="repair opening",
        failure_category="LOGIC_ERROR",
        initial_verdict="REJECT",
        is_patch=False,
        is_patch_fallback=False,
        patch_strategy="",
    )

    assert envelope["authoritative_continuity_projection"]["accepted_source_state"] == {"end_location": "boardroom"}


def test_attach_session_memory_envelope_preserves_existing_advisory_payload():
    advisory_flags = {"continuity": ["keep timeline"]}
    envelope = {
        "schema_version": SESSION_MEMORY_ENVELOPE_VERSION,
        "source": "stage4_attempt",
        "attempt_key": "s4:ep1:arc1:a1",
    }

    merged = attach_session_memory_envelope(advisory_flags, envelope)

    assert merged["continuity"] == ["keep timeline"]
    assert merged[SESSION_MEMORY_ENVELOPE_KEY]["attempt_key"] == "s4:ep1:arc1:a1"
    assert SESSION_MEMORY_ENVELOPE_KEY not in advisory_flags


def test_get_session_memory_envelope_returns_deep_copied_payload():
    advisory_flags = {
        SESSION_MEMORY_ENVELOPE_KEY: {
            "schema_version": SESSION_MEMORY_ENVELOPE_VERSION,
            "retry_surface": {"runtime_advisory": "keep continuity"},
        }
    }

    envelope = get_session_memory_envelope(advisory_flags)
    envelope["retry_surface"]["runtime_advisory"] = "mutated"

    assert advisory_flags[SESSION_MEMORY_ENVELOPE_KEY]["retry_surface"]["runtime_advisory"] == "keep continuity"


def test_build_stage4_session_memory_envelope_preserves_structured_truth_pin_items():
    envelope = build_stage4_session_memory_envelope(
        episode=2,
        round_num=1,
        arc=3,
        success=False,
        score=61,
        verdict="REJECT",
        reject_reason="retry needed",
        fix_scope="full",
        advisory_flags={
            "conflict_contract": {
                "truth_pins": [
                    {
                        "pin_key": "family_group_name",
                        "family": "proper_noun_group",
                        "expected": "대한그룹",
                        "observed": "대현그룹",
                    }
                ]
            }
        },
        session_id="sess-stage4",
        attempt_key="s4:ep2:arc3:a2:sess-stage4",
        artifact_meta={},
        selection_reason="best candidate",
        verdict_reason="conflict",
        open_review="repeat detected",
        fix_scope_reasoning="rewrite only",
        runtime_advisory="keep canon",
        retry_directives="retry",
        failure_category="LOGIC_ERROR",
        initial_verdict="PASS_WITH_FIX",
        is_patch=False,
        is_patch_fallback=False,
        patch_strategy="",
    )

    assert envelope["truth_pin_items"] == [
        {
            "pin_key": "family_group_name",
            "family": "proper_noun_group",
            "expected": "대한그룹",
            "observed": "대현그룹",
        }
    ]
    assert envelope["truth_pins"]["family_group_name"] == "대한그룹"
