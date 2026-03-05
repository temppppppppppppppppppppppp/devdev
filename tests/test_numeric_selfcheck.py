"""Numeric self-check regression tests for NS-1 / NS-1-P / NS-2."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from modules.core.stage2_finalizer import (
    Stage2Finalizer,
    _check_block_worldstate_alignment,
    _check_tactical_arithmetic,
)
from modules.domain.agents.chief_writer_quality import ChiefWriterQualityGate

EOK = "\uc5b5"


def _make_host():
    host = MagicMock()
    host.ask = MagicMock(return_value='{"content":"fixed"}')
    host._escape_braces = lambda x: str(x).replace("{", "{{").replace("}", "}}")
    host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}
    return host


def _make_stage2_ctx(audit_results, *, patch_arc_return=None):
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.pass_rate_monitor = MagicMock()
    ctx.quality_dashboard = MagicMock()
    ctx.stage2_optimizer = MagicMock()
    ctx.stage2_optimizer.failure_memory = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.stage_rejection_history = []
    ctx.audit_event = MagicMock()
    ctx.semantic_plot_guard = None
    ctx.validate_arc_integrity = MagicMock(return_value=True)
    ctx.current_project = MagicMock()
    ctx.safe_commit_async = AsyncMock(return_value=True)
    ctx.generate_arc_context_v60 = MagicMock(return_value="context_text")
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = 0
    ctx.get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "g"})
    ctx.state_tracker = SimpleNamespace(foo=0, bar=0)
    ctx.session_logger = None

    director = MagicMock()
    if isinstance(audit_results, list):
        director.audit_strategic_plan.side_effect = audit_results
    else:
        director.audit_strategic_plan.return_value = audit_results
    director.ask.return_value = "volume summary text long enough"

    four_phase = MagicMock()
    four_phase._inplace_patch_arc.return_value = patch_arc_return
    ctx.agents = {"director": director, "four_phase": four_phase}
    return ctx


def _valid_arc():
    return {
        "arc_no": 1,
        "ep_start": 1,
        "ep_end": 10,
        "ep_count": 10,
        "tactical_doc": "A" * 1600,
        "state_changes": {"npc_deaths": [], "relationship_changes": []},
        "hybrid_composition": {"primary": "std", "secondary": [], "mixing_logic": "default"},
        "joint_docs": {"final_location": "market", "physical_inventory": [], "world_joint": "stable"},
        "status_shadow": {"internal_energy_loss": "10%", "expected_injuries": "none", "item_consumption": []},
        "state_constraints": {"items_acquired": []},
    }


def _make_kwargs(arc):
    return {
        "refined_arc": arc,
        "enriched_block": {
            "joint_docs": {"final_location": "city", "physical_inventory": [], "world_joint": "stable"},
            "status_shadow": {"internal_energy_loss": "5%", "expected_injuries": "none", "item_consumption": []},
            "joint_docs_brief": "brief",
        },
        "arc_drive": {"desire_vector": "test"},
        "all_refined_arcs": [],
        "global_arc_no": 1,
        "current_ep_start": 1,
        "current_feedback": "",
        "protagonist_name": "hero",
        "suspected_duplicates": [],
        "entity_registry_for_director": {},
        "constraint_block": "",
        "draft_validator_passed": True,
        "consensus_passed": True,
        "attempt": 0,
        "generation_method": "four_phase",
        "st_snapshot": None,
        "director_feedback_for_fourphase": "",
        "last_refined_context": "prev context",
        "bible_root": {"protagonist_config": {"name": "hero", "incarnation_type": "none"}},
        "genre": "fantasy",
        "constraint_db": MagicMock(arc_states=[]),
    }


def test_analyst_prompt_contains_ns1_rule():
    src = open("config/prompts/analyst.yaml", encoding="utf-8").read()
    assert "[NS-1] Numeric self-verification" in src
    assert "Arithmetic mismatch: [expr] stated=[X] actual=[Y]" in src


def test_analyst_prompt_contains_numeric_selfcheck_output():
    src = open("config/prompts/analyst.yaml", encoding="utf-8").read()
    assert '"numeric_selfcheck"' in src


def test_blueprint_preflight_contains_ns1_rule():
    src = open("config/prompts/blueprint_generator.yaml", encoding="utf-8").read()
    assert "6. **[NS-1] Blueprint numeric self-verification**" in src
    assert '`severity="high"` and set `passed=false`' in src


def test_cw_arithmetic_checker_catches_wrong_percent():
    gate = ChiefWriterQualityGate.__new__(ChiefWriterQualityGate)
    manuscript = f"profit: 600{EOK} x 17.2% = 451{EOK}"
    issues = gate._check_arithmetic_consistency(manuscript)
    assert len(issues) > 0
    assert issues[0]["type"] == "arithmetic_error"


def test_cw_arithmetic_checker_passes_correct_percent():
    gate = ChiefWriterQualityGate.__new__(ChiefWriterQualityGate)
    manuscript = f"profit: 600{EOK} x 17.2% = 103.2{EOK}"
    issues = gate._check_arithmetic_consistency(manuscript)
    assert issues == []


def test_cw_arithmetic_checker_ignores_non_numeric_text():
    gate = ChiefWriterQualityGate.__new__(ChiefWriterQualityGate)
    issues = gate._check_arithmetic_consistency("plain narrative text only")
    assert issues == []


def test_cw_self_critique_includes_arithmetic_check():
    gate = ChiefWriterQualityGate(_make_host())
    manuscript = f'{{"content":"calc 600{EOK} x 17.2% = 451{EOK}"}}'
    with (
        patch.object(gate, "_check_hud_consistency", return_value=[]),
        patch.object(gate, "_check_cliche_overuse", return_value=[]),
        patch.object(gate, "_check_justification_gaps", return_value=[]),
        patch.object(gate, "_check_npc_relationship", return_value=[]),
        patch.object(gate, "_check_writing_directive", return_value=[]),
        patch.object(gate, "_check_expression_freshness", return_value=[]),
        patch.object(gate, "_check_ending_hook_presence", return_value=[]),
    ):
        out = gate._self_critique(manuscript, "", {"npcs": []}, "genre", ep_num=1)
    assert out["has_issues"] is True
    assert any(i.get("type") == "arithmetic_error" for i in out["issues"])


def test_ns1p_tactical_arithmetic_detects_mismatch():
    text = f"capital 600{EOK} x 17.2% = 451{EOK}"
    issues = _check_tactical_arithmetic(text)
    assert len(issues) > 0
    assert "Arithmetic mismatch" in issues[0]


def test_ns1p_tactical_arithmetic_passes_correct_expression():
    text = f"capital 600{EOK} x 17.2% = 103.2{EOK}"
    issues = _check_tactical_arithmetic(text)
    assert issues == []


def test_ns2_large_divergence_returns_warning():
    block = {"genre_ext": {"capital_after": f"23{EOK}"}}
    arc = {"state_constraints": {"arc_end_state": {"total_assets": f"470{EOK}"}}}
    warns = _check_block_worldstate_alignment(block, arc, arc_no=2)
    assert len(warns) > 0
    assert "[NS-2]" in warns[0]


def test_ns2_small_divergence_no_warning():
    block = {"genre_ext": {"capital_after": f"23{EOK}"}}
    arc = {"state_constraints": {"arc_end_state": {"total_assets": f"25{EOK}"}}}
    warns = _check_block_worldstate_alignment(block, arc, arc_no=2)
    assert warns == []


def test_ns2_no_genre_ext_skips():
    block = {"title": "no genre ext"}
    arc = {"state_constraints": {"arc_end_state": {"capital": f"10{EOK}"}}}
    warns = _check_block_worldstate_alignment(block, arc, arc_no=1)
    assert warns == []


def test_ns1p_warning_injected_into_story_context():
    initial_audit = {
        "decision": "PASS_WITH_FIX",
        "score": 94,
        "reason": "needs fix",
        "re_slice_instruction": "fix numbers",
        "fix_scope": "inplace",
    }
    re_audit = {"decision": "PASS", "score": 96, "reason": "ok"}

    patched_arc = _valid_arc()
    patched_arc["tactical_doc"] = f"profit 600{EOK} x 17.2% = 451{EOK}"

    ctx = _make_stage2_ctx([initial_audit, re_audit], patch_arc_return=patched_arc)
    host = MagicMock()
    host.ctx = ctx
    finalizer = Stage2Finalizer(host)
    kwargs = _make_kwargs(_valid_arc())

    with (
        patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x),
        patch("modules.core.spinners.V50_MODULES_AVAILABLE", False),
    ):
        result = asyncio.run(finalizer.run_finalize(**kwargs))

    assert result["action"] == "break"
    calls = ctx.agents["director"].audit_strategic_plan.call_args_list
    assert len(calls) == 2
    re_story_context = calls[1].kwargs.get("story_context", "")
    assert "[NS-1-P arithmetic warning in inplace patch]" in re_story_context

