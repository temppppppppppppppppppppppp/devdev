import json
from pathlib import Path

from scripts import regression_validation_tiers as tiers

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "docs/implementation/regression-validation-tier-contract-v1.json").read_text(encoding="utf-8")
)


def test_regression_validation_tier_contract_matches_python_inventory():
    inventory = tiers.build_tier_inventory()

    assert CONTRACT["tiers"]["contract_safe"]["tests"] == list(tiers.CONTRACT_SAFE_TESTS)
    assert CONTRACT["tiers"]["focused_mutation"]["tests"] == list(tiers.FOCUSED_MUTATION_TESTS)
    assert CONTRACT["tiers"]["focused_mutation"]["scripts"] == list(tiers.FOCUSED_MUTATION_SCRIPTS)
    assert CONTRACT["tiers"]["full_canary_proof"]["scripts"] == list(tiers.FULL_CANARY_PROOF_SCRIPTS)
    assert CONTRACT["recommended_subsets"] == inventory["recommended_subsets"]


def test_mutation_boundaries_are_labeled_on_smoke_and_canary_entrypoints():
    expected_markers = {
        "scripts/run_stage2_smoke.py": "VALIDATION_TIER = FOCUSED_MUTATION",
        "scripts/run_stage3_smoke.py": "VALIDATION_TIER = FOCUSED_MUTATION",
        "scripts/run_stage4_smoke.py": "VALIDATION_TIER = FOCUSED_MUTATION",
        "scripts/run_stage2_canary.py": "VALIDATION_TIER = FULL_CANARY_PROOF",
        "scripts/run_stage3_canary.py": "VALIDATION_TIER = FULL_CANARY_PROOF",
        "scripts/run_stage4_canary.py": "VALIDATION_TIER = FULL_CANARY_PROOF",
        "scripts/run_stage34_canary.py": "VALIDATION_TIER = FULL_CANARY_PROOF",
        "scripts/run_stage34_ep_demo_canary.py": "VALIDATION_TIER = FULL_CANARY_PROOF",
        "scripts/e2e_menu_smoke.ps1": "Validation tier: focused_mutation",
    }

    for rel_path, marker in expected_markers.items():
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        assert marker in text


def test_contract_safe_lane_remains_read_only_documentation_subset():
    tier = CONTRACT["tiers"]["contract_safe"]
    assert tier["mutates_project_state"] is False
    assert tier["scripts"] == []
    assert "tests/test_desktop_shadow_hygiene.py" in tier["tests"]
    assert "tests/test_runtime_ownership_contract.py" in tier["tests"]
