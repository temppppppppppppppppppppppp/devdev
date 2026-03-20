import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from modules.core.constants import AIModels
from modules.core.stage2_finalizer import Stage2Finalizer
from modules.core.stage4_types import WritingDirective
from modules.domain.agents.arc_critic import ArcCritic
from modules.domain.agents.block_enricher import BlockEnricher
from modules.domain.agents.chief_writer_quality import ChiefWriterQualityGate
from modules.domain.agents.unified_arc_validator import UnifiedArcValidator


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _make_quality_host():
    host = MagicMock()
    host.ask = MagicMock(return_value='{"content":"fixed"}')
    host._escape_braces = lambda x: str(x).replace("{", "{{").replace("}", "}}")
    host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}
    return host


def _build_finalizer():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.pass_rate_monitor = MagicMock()
    ctx.quality_dashboard = MagicMock()
    ctx.stage2_optimizer = MagicMock()
    ctx.stage2_optimizer.failure_memory = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.stage_rejection_history = []
    ctx.audit_event = MagicMock()
    ctx.semantic_plot_guard = None
    ctx.validate_arc_integrity = MagicMock(return_value=True)
    ctx.validate_arc_data_fields = None
    ctx.current_project = MagicMock()
    ctx.safe_commit_async = AsyncMock(return_value=True)
    ctx.generate_arc_context_v60 = MagicMock(return_value="context_text")
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = 0
    ctx.get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "guide"})
    ctx.state_tracker = SimpleNamespace(foo=0, bar=0)
    director = MagicMock()
    director.audit_strategic_plan.return_value = {"decision": "REJECT", "score": 55, "reason": "retry"}
    director.ask.return_value = "summary"
    ctx.agents = {"director": director}
    host = MagicMock()
    host.ctx = ctx
    return Stage2Finalizer(host)


def test_arc_critic_remove_items_preserves_empty_protagonist_items():
    critic = ArcCritic.__new__(ArcCritic)
    arc = {
        "state_constraints": {
            "protagonist_items": [],
            "items_acquired": ["fallback-only-item"],
        }
    }
    critique = {"auto_fixes": {"remove_items": ["fallback-only-item"]}}

    fixed = critic._apply_auto_fixes(arc, critique)

    assert fixed["state_constraints"]["protagonist_items"] == []
    assert fixed["state_constraints"]["items_acquired"] == ["fallback-only-item"]


def test_unified_arc_validator_uses_state_constraints_timeline_fallback():
    validator = UnifiedArcValidator.__new__(UnifiedArcValidator)
    arc = {
        "arc_no": 1,
        "ep_count": 5,
        "tactical_doc": "x" * 5000,
        "joint_docs": {"final_location": "market"},
        "state_changes": {"npc_deaths": []},
        "state_constraints": {"timeline": {"start": {"year": 2006}, "end": {"year": 2006}}},
    }

    issues = validator._check_required_fields(arc)

    assert not any(issue["issue"] == "state_changes.timeline 필드 누락" for issue in issues)


@patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
@patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
def test_stage2_finalizer_reject_metrics_preserve_best_strategy(_validate):
    finalizer = _build_finalizer()
    refined_arc = {
        "arc_no": 1,
        "ep_start": 1,
        "ep_end": 10,
        "ep_count": 10,
        "tactical_doc": "A" * 1600,
        "state_changes": {"npc_deaths": [], "relationship_changes": []},
        "hybrid_composition": {"primary": "standard_progression", "secondary": [], "mixing_logic": "default"},
        "joint_docs": {"final_location": "market", "physical_inventory": [], "world_joint": "stable"},
        "status_shadow": {"internal_energy_loss": "10%", "expected_injuries": "none", "item_consumption": []},
        "state_constraints": {"items_acquired": []},
        "_ensemble_meta": {"best_strategy": "creative"},
    }

    kwargs = {
        "refined_arc": refined_arc,
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
        "bible_root": {"protagonist_config": {"name": "hero", "incarnation_type": "회귀"}},
        "genre": "fantasy",
        "constraint_db": MagicMock(arc_states=[]),
    }

    with patch.object(finalizer, "_record_s2_reject_metrics") as mock_record:
        result = asyncio.run(finalizer.run_finalize(**kwargs))

    assert result["action"] == "retry"
    assert mock_record.call_args.kwargs["selected_strategy"] == "creative"


def test_block_enricher_flash_helper_restores_primary_model():
    enricher = BlockEnricher.__new__(BlockEnricher)
    enricher.primary_model = "main-model"
    enricher._flash_model_lock = threading.Lock()
    seen = []

    def _fake_ask(prompt, temperature=0.3):
        seen.append((prompt, temperature, enricher.primary_model))
        return {"ok": True}

    enricher.ask = _fake_ask
    result = BlockEnricher._ask_with_flash_model(enricher, "prompt", temperature=0.3)

    assert result == {"ok": True}
    assert seen == [("prompt", 0.3, AIModels.FLASH_ANALYSIS_MODEL)]
    assert enricher.primary_model == "main-model"


def test_block_enricher_source_routes_flash_calls_through_helper():
    src = _read("modules/domain/agents/block_enricher.py")
    assert "self._flash_model_lock = threading.Lock()" in src
    assert "def _ask_with_flash_model" in src
    assert src.count("self._ask_with_flash_model(") >= 3


def test_block_enricher_retry_prompt_preserves_tail_context():
    enricher = BlockEnricher.__new__(BlockEnricher)
    enricher._escape_braces = lambda x: str(x).replace("{", "{{").replace("}", "}}")
    enricher.analyze_block_density = MagicMock(
        return_value={"needs_enrichment": True, "density_score": 0.2, "missing_elements": []}
    )

    first_result = {
        "block_id": "B2",
        "content": {
            "context": "HEAD-RESULT\n" + ("R" * 70000) + "\nTAIL-BLOCK-RETRY",
            "event_villain": "적",
            "solution": "해결",
            "reward": "보상",
        },
    }
    second_result = {
        "block_id": "B2",
        "content": {
            "context": "fixed",
            "event_villain": "적",
            "solution": "해결",
            "reward": "보상",
        },
    }

    prompts = []
    ask_results = iter([first_result, second_result])
    validations = iter(
        [
            {"validation_result": "FAIL", "issues": ["tail issue"]},
            {"validation_result": "PASS", "issues": []},
        ]
    )

    def _fake_ask(prompt, temperature=0.7):
        prompts.append(prompt)
        return next(ask_results)

    enricher.ask = _fake_ask
    enricher._validate_enrichment = MagicMock(side_effect=lambda **_kwargs: next(validations))
    enricher._director_audit_block = MagicMock(return_value={"decision": "PASS", "total_score": 90})

    result = enricher.enrich_block(
        current_block={"block_id": "B2", "content": {"context": "short"}},
        reference_block={"block_id": "B1", "content": {"context": "ref"}},
        prev_block={"block_id": "B1"},
        next_block={"block_id": "B3"},
    )

    assert result["enriched"] is True
    assert len(prompts) == 2
    assert "TAIL-BLOCK-RETRY" in prompts[1]
    assert "...(중간 생략)..." in prompts[1]


def test_block_enricher_causal_fix_prompt_preserves_tail_context():
    enricher = BlockEnricher.__new__(BlockEnricher)
    captured = {}

    def _fake_ask(prompt, temperature=0.5):
        captured["prompt"] = prompt
        return {
            "block_id": "B3",
            "content": {"context": "ok", "event_villain": "e", "solution": "s", "reward": "r"},
        }

    enricher.ask = _fake_ask

    result = enricher._re_enrich_with_causal_fix(
        current_block={"block_id": "B3", "content": {"context": "short"}},
        enriched_prev_block={"content": {"reward": "이전 보상"}},
        next_block={"payload": "N" * 3000, "tail": "TAIL-NEXT-BLOCK"},
        reference_block={"payload": "R" * 4000, "tail": "TAIL-REF-BLOCK"},
        causal_issue="인과 누락",
        protagonist_name="주인공",
        genre="wuxia",
    )

    assert result["enriched"] is True
    assert "TAIL-REF-BLOCK" in captured["prompt"]
    assert "TAIL-NEXT-BLOCK" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_chief_writer_quality_returns_structured_writing_directive_issues():
    gate = ChiefWriterQualityGate(_make_quality_host())

    issues = gate._check_writing_directive("금기 표현이 들어간 문장", WritingDirective(expression_ban=["금기 표현"]))

    assert any(isinstance(issue, dict) and issue.get("type") == "expression_ban_violation" for issue in issues)


def test_chief_writer_quality_returns_structured_expression_freshness_issues():
    gate = ChiefWriterQualityGate(_make_quality_host())

    issues = gate._check_expression_freshness("반복 문장", {"반복 문장": 3})

    assert any(
        isinstance(issue, dict) and issue.get("type") == "expression_freshness_repetition"
        for issue in issues
    )
