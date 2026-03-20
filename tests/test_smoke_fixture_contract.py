from pathlib import Path

from scripts.smoke_fixture_contract import (
    BOUND_SMOKE_TARGET_PROJECT,
    CANONICAL_SMOKE_SOURCE_PROJECT,
    PACKAGED_SMOKE_PROJECT,
)


ROOT = Path(".")
RUN_STAGE2 = (ROOT / "scripts/run_stage2_smoke.py").read_text(encoding="utf-8")
RUN_STAGE3 = (ROOT / "scripts/run_stage3_smoke.py").read_text(encoding="utf-8")
RUN_STAGE4 = (ROOT / "scripts/run_stage4_smoke.py").read_text(encoding="utf-8")
PREPARE_SMOKE = (ROOT / "scripts/prepare_smoke_fixture.py").read_text(encoding="utf-8")


def test_smoke_fixture_contract_constants_are_canonical():
    assert CANONICAL_SMOKE_SOURCE_PROJECT == "smoke_fixture_demo"
    assert BOUND_SMOKE_TARGET_PROJECT == "코덱스_테스트"
    assert PACKAGED_SMOKE_PROJECT == "investment_canary_demo"


def test_smoke_runners_share_bounded_target_contract():
    assert "from scripts.smoke_fixture_contract import BOUND_SMOKE_TARGET_PROJECT" in RUN_STAGE2
    assert "from scripts.smoke_fixture_contract import BOUND_SMOKE_TARGET_PROJECT" in RUN_STAGE3
    assert "from scripts.smoke_fixture_contract import BOUND_SMOKE_TARGET_PROJECT" in RUN_STAGE4
    assert 'PROJECT_NAME = BOUND_SMOKE_TARGET_PROJECT' in RUN_STAGE2
    assert 'PROJECT_NAME = BOUND_SMOKE_TARGET_PROJECT' in RUN_STAGE3
    assert 'PROJECT_NAME = BOUND_SMOKE_TARGET_PROJECT' in RUN_STAGE4


def test_prepare_smoke_fixture_defaults_to_canonical_contract():
    assert "DEFAULT_SOURCE_PROJECT = CANONICAL_SMOKE_SOURCE_PROJECT" in PREPARE_SMOKE
    assert "DEFAULT_TARGET_PROJECT = BOUND_SMOKE_TARGET_PROJECT" in PREPARE_SMOKE
