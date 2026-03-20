from pathlib import Path

from scripts.run_stage2_smoke import make_mock_arc
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


def test_smoke_runners_use_shared_fixture_readiness_gate():
    assert "from modules.core.smoke_fixture_tools import assert_smoke_fixture_ready" in RUN_STAGE2
    assert "from modules.core.smoke_fixture_tools import assert_smoke_fixture_ready" in RUN_STAGE3
    assert "from modules.core.smoke_fixture_tools import assert_smoke_fixture_ready" in RUN_STAGE4
    assert 'assert_smoke_fixture_ready(PROJECT_DIR, lane="stage2_smoke")' in RUN_STAGE2
    assert 'assert_smoke_fixture_ready(PROJECT_DIR, lane="stage3_smoke")' in RUN_STAGE3
    assert 'assert_smoke_fixture_ready(PROJECT_DIR, lane="stage4_smoke")' in RUN_STAGE4


def test_stage2_smoke_resets_rich_fixture_start_state_and_uses_pass_side_score():
    assert "reset_stage2_smoke_state" in RUN_STAGE2
    assert 'director.audit_strategic_plan = MagicMock(return_value={"decision": "PASS", "score": 95, "reason": "mock ok"})' in RUN_STAGE2
    assert "db.conn.commit()\n            return True" in RUN_STAGE2
    assert "ctx.perf_timer = _NullPerfTimer()" in RUN_STAGE2
    assert "_install_narrative_analyzer_smoke_stub()" in RUN_STAGE2
    assert "raise RuntimeError(f\"stage2 smoke wrote failure reports: {report_names}\")" in RUN_STAGE2
    assert "manual_arcs = [make_mock_arc(i + 1, roadmap[i]) for i in range(3)]" not in RUN_STAGE2


def test_stage2_smoke_mock_arc_meets_flow_guard_baseline():
    arc = make_mock_arc(
        1,
        {
            "title": "Block 1",
            "content": {
                "context": "The protagonist secures a market entry window with a disciplined setup.",
                "event_villain": "A rival fund attempts to corner the same position and raise pressure.",
                "solution": "The team spreads execution risk and prepares a staged response plan.",
                "reward": "The protagonist locks in an early strategic advantage and cash buffer.",
            },
        },
    )

    beats = arc["beat_sequence"]
    assert len(beats) >= int(arc["ep_count"])
    assert min(len(beat.split()) for beat in beats) >= 4


def test_stage2_smoke_uses_realistic_arc_mapping_callback():
    assert "calculate_arc_from_episode=lambda ep: max(1, (int(ep) - 1) // 10 + 1) if ep else 0" in RUN_STAGE2
