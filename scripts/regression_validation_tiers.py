"""Shared regression validation tier inventory for contract-safe, smoke, and canary lanes."""

from __future__ import annotations

CONTRACT_SAFE = "contract_safe"
FOCUSED_MUTATION = "focused_mutation"
FULL_CANARY_PROOF = "full_canary_proof"

CONTRACT_SAFE_TESTS = (
    "tests/test_bridge_server_desktop_risk_gate.py",
    "tests/test_desktop_contract_refresh.py",
    "tests/test_desktop_direct_surface_contract.py",
    "tests/test_desktop_packaging_contract.py",
    "tests/test_desktop_shadow_hygiene.py",
    "tests/test_desktop_transport_contract.py",
    "tests/test_runtime_ownership_contract.py",
    "tests/test_runtime_paths.py",
    "tests/test_runtime_print_allowlist.py",
    "tests/test_surface_containment_contract.py",
)

FOCUSED_MUTATION_TESTS = (
    "tests/test_run_stage2_canary.py",
    "tests/test_run_stage4_canary.py",
    "tests/test_run_stage34_canary.py",
    "tests/test_run_stage3_canary.py",
    "tests/test_run_stage34_ep_demo_canary.py",
)

FOCUSED_MUTATION_SCRIPTS = (
    "scripts/e2e_menu_smoke.ps1",
    "scripts/run_stage2_smoke.py",
    "scripts/run_stage3_smoke.py",
    "scripts/run_stage4_smoke.py",
)

FULL_CANARY_PROOF_SCRIPTS = (
    "scripts/run_stage2_canary.py",
    "scripts/run_stage4_canary.py",
    "scripts/run_stage34_canary.py",
    "scripts/run_stage3_canary.py",
    "scripts/run_stage34_ep_demo_canary.py",
)

RECOMMENDED_VALIDATION_SUBSETS = {
    CONTRACT_SAFE: (
        "tests/test_desktop_shadow_hygiene.py",
        "tests/test_desktop_direct_surface_contract.py",
        "tests/test_desktop_transport_contract.py",
        "tests/test_bridge_server_desktop_risk_gate.py",
        "tests/test_runtime_ownership_contract.py",
        "tests/test_runtime_print_allowlist.py",
    ),
    FOCUSED_MUTATION: (
        "tests/test_run_stage2_canary.py",
        "tests/test_run_stage4_canary.py",
        "tests/test_run_stage34_canary.py",
        "tests/test_run_stage3_canary.py",
        "tests/test_run_stage34_ep_demo_canary.py",
        "scripts/run_stage2_smoke.py",
        "scripts/run_stage3_smoke.py",
        "scripts/run_stage4_smoke.py",
    ),
    FULL_CANARY_PROOF: (
        "scripts/run_stage2_canary.py",
        "scripts/run_stage4_canary.py",
        "scripts/run_stage34_canary.py",
        "scripts/run_stage3_canary.py",
        "scripts/run_stage34_ep_demo_canary.py",
    ),
}


def build_tier_inventory() -> dict[str, object]:
    return {
        "tiers": {
            CONTRACT_SAFE: {
                "tests": list(CONTRACT_SAFE_TESTS),
                "scripts": [],
                "mutates_project_state": False,
            },
            FOCUSED_MUTATION: {
                "tests": list(FOCUSED_MUTATION_TESTS),
                "scripts": list(FOCUSED_MUTATION_SCRIPTS),
                "mutates_project_state": True,
            },
            FULL_CANARY_PROOF: {
                "tests": [],
                "scripts": list(FULL_CANARY_PROOF_SCRIPTS),
                "mutates_project_state": True,
            },
        },
        "recommended_subsets": {tier: list(entries) for tier, entries in RECOMMENDED_VALIDATION_SUBSETS.items()},
    }
