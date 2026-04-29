from modules.core.stage4_runtime_route import (
    STAGE4_RUNTIME_ROUTE_PAYLOAD_VERSION,
    STAGE4_RUNTIME_ROUTE_TAXONOMY,
    copy_stage4_runtime_route_fields,
    extract_stage4_runtime_route,
    is_stage4_nonlocal_repair_route,
    is_stage4_post_select_route,
    stage4_reject_bucket_from_route,
    stage4_runtime_route_action,
)


def test_stage4_runtime_route_action_maps_gate_basis_without_director_mutation() -> None:
    assert (
        stage4_runtime_route_action(gate_basis="post_select_conflict", final_verdict="REJECT")
        == "route_retry_full_rewrite"
    )
    assert (
        stage4_runtime_route_action(gate_basis="strong_advisory_escalation_non_local_fix", final_verdict="REJECT")
        == "route_retry_nonlocal_repair"
    )
    assert stage4_runtime_route_action(gate_basis="", final_verdict="PASS") == "adopt_stage4_artifact"


def test_extract_stage4_runtime_route_prefers_gate_semantics_then_verdict_layers() -> None:
    route = extract_stage4_runtime_route(
        {
            "runtime_route_action": "route_retry_full_rewrite",
            "verdict_layers": {
                "runtime_route_payload_version": STAGE4_RUNTIME_ROUTE_PAYLOAD_VERSION,
                "runtime_route_verdict": "REJECT",
                "runtime_route_taxonomy": STAGE4_RUNTIME_ROUTE_TAXONOMY,
            },
        }
    )

    assert route == {
        "runtime_route_payload_version": STAGE4_RUNTIME_ROUTE_PAYLOAD_VERSION,
        "runtime_route_verdict": "REJECT",
        "runtime_route_action": "route_retry_full_rewrite",
        "runtime_route_taxonomy": STAGE4_RUNTIME_ROUTE_TAXONOMY,
    }


def test_extract_stage4_runtime_route_reads_session_memory_envelope_surfaces() -> None:
    payload = {
        "session_memory_envelope": {
            "verdict_surface": {
                "runtime_route_payload_version": STAGE4_RUNTIME_ROUTE_PAYLOAD_VERSION,
                "runtime_route_verdict": "REJECT",
            },
            "retry_surface": {
                "runtime_route_action": "block_artifact_adoption",
                "runtime_route_reason": "quality floor",
                "runtime_route_taxonomy": STAGE4_RUNTIME_ROUTE_TAXONOMY,
            },
        }
    }

    route = extract_stage4_runtime_route(payload)

    assert route["runtime_route_payload_version"] == STAGE4_RUNTIME_ROUTE_PAYLOAD_VERSION
    assert route["runtime_route_verdict"] == "REJECT"
    assert route["runtime_route_action"] == "block_artifact_adoption"
    assert route["runtime_route_reason"] == "quality floor"
    assert route["runtime_route_taxonomy"] == STAGE4_RUNTIME_ROUTE_TAXONOMY


def test_stage4_route_predicates_keep_legacy_gate_basis_fallbacks() -> None:
    assert is_stage4_post_select_route({"gate_basis": "post_select_conflict"})
    assert is_stage4_nonlocal_repair_route({"gate_basis": "strong_advisory_escalation_non_local_fix"})
    assert stage4_reject_bucket_from_route({"runtime_route_action": "route_retry_full_rewrite"}) == (
        "post_select_conflict"
    )
    assert stage4_reject_bucket_from_route({"runtime_route_action": "block_artifact_adoption"}) == "quality_issue"


def test_copy_stage4_runtime_route_fields_uses_nested_sources() -> None:
    target: dict[str, object] = {}

    copy_stage4_runtime_route_fields(
        target,
        {"gate_semantics": {"runtime_route_action": "route_retry_full_rewrite"}},
        {"runtime_route_taxonomy": STAGE4_RUNTIME_ROUTE_TAXONOMY},
    )

    assert target == {
        "runtime_route_action": "route_retry_full_rewrite",
        "runtime_route_taxonomy": STAGE4_RUNTIME_ROUTE_TAXONOMY,
    }
