"""NS-3 block target checks (fallback self-critic + FourPhase phase 2.55)."""

from modules.domain.agents.analyst import _format_block_numeric_targets
from modules.domain.agents.four_phase_arc_generator import _check_arc_vs_block_targets

EOK = "억"


def test_ns3a_block_targets_injected_into_critic_input():
    block = {"genre_ext": {"capital_before": f"20{EOK}", "capital_after": f"23{EOK}", "profit_loss": f"+3{EOK}"}}
    result = _format_block_numeric_targets(block)
    assert "[NS-3 Treatment" in result
    assert "capital_after" in result


def test_ns3a_no_genre_ext_returns_empty():
    block = {"title": "무협 블록", "emotional_beat": "돌파"}
    assert _format_block_numeric_targets(block) == ""


def test_ns3a_none_block_returns_empty():
    assert _format_block_numeric_targets(None) == ""


def test_ns3b_large_divergence_returns_warning():
    arc = {"state_constraints": {"arc_end_state": {"total_assets": f"470{EOK}"}}}
    block = {"genre_ext": {"capital_after": f"23{EOK}"}}
    result = _check_arc_vs_block_targets(arc, block, arc_no=2)
    assert result != ""
    assert "NS-3-B" in result or "divergence" in result


def test_ns3b_small_divergence_returns_empty():
    arc = {"state_constraints": {"arc_end_state": {"total_assets": f"25{EOK}"}}}
    block = {"genre_ext": {"capital_after": f"23{EOK}"}}
    assert _check_arc_vs_block_targets(arc, block, arc_no=2) == ""


def test_ns3b_no_genre_ext_returns_empty():
    arc = {"state_constraints": {"arc_end_state": {"total_assets": f"25{EOK}"}}}
    block = {"title": "no genre ext"}
    assert _check_arc_vs_block_targets(arc, block, arc_no=1) == ""

