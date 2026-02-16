"""[L3] Stage 2 smoke test using real golden-route data + mocked LLM agents."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.core.db_manager import DBManager
from modules.core.stage2_context import Stage2Context
from modules.core.stage2_orchestrator import Stage2Orchestrator


def _load_l3_payload() -> tuple[dict, list[dict], str]:
    """Load golden-route bible + treatments and inject 2 treatment contents into plot_roadmap."""
    treatment_candidates = sorted(Path("treatments").glob("*_tr_block_ALL.json"))
    if not treatment_candidates:
        pytest.skip("No *_tr_block_ALL.json found under treatments/")
    treatment_path = treatment_candidates[0]

    prefix = treatment_path.name[: -len("_tr_block_ALL.json")]
    bible_path = Path("bible") / f"{prefix}_bi.json"
    if not bible_path.exists():
        pytest.skip(f"Matching bible not found: {bible_path}")

    bible = json.loads(bible_path.read_text(encoding="utf-8"))
    treatments = json.loads(treatment_path.read_text(encoding="utf-8"))

    if not isinstance(treatments, list) or len(treatments) < 2:
        pytest.skip("Treatment file does not contain at least 2 blocks")

    if "MasterBible" not in bible or not isinstance(bible["MasterBible"], dict):
        pytest.skip("Bible has no MasterBible root")

    block0 = treatments[0].get("content", treatments[0])
    block1 = treatments[1].get("content", treatments[1])
    bible["MasterBible"]["plot_roadmap"] = [block0, block1]
    return bible, treatments[:2], prefix


def _make_mock_arc(arc_no: int, ep_start: int, source_block: dict) -> dict:
    """Return a Stage2-valid arc payload that can PASS finalizer + integrity checks."""
    content = source_block.get("content", {}) if isinstance(source_block, dict) else {}
    block_title = source_block.get("title", f"block-{arc_no}") if isinstance(source_block, dict) else f"block-{arc_no}"
    context_seed = content.get("context", "") if isinstance(content, dict) else ""

    tactical_seed = f"arc {arc_no} {block_title} {context_seed[:80]}".strip()
    tactical_doc = ((tactical_seed + " detailed progression and consequence sentence. ") * 120).strip()

    ep_end = ep_start + 4
    return {
        "arc_no": arc_no,
        "global_arc_no": arc_no,
        "ep_start": ep_start,
        "ep_end": ep_end,
        "ep_count": 5,
        "title": f"Arc {arc_no}",
        "tactical_doc": tactical_doc,
        "beat_sequence": [
            f"arc {arc_no} beat one conflict escalates with concrete action",
            f"arc {arc_no} beat two pressure rises with external consequence",
            f"arc {arc_no} beat three strategic response triggers new cost",
            f"arc {arc_no} beat four reversal creates urgent tactical decision",
            f"arc {arc_no} beat five closes with forward hook and payoff",
        ],
        "state_constraints": {
            "arc_start_state": {"location": "office"},
            "arc_end_state": {
                "location": "market",
                "equipment": ["ledger"],
                "injuries": "normal",
                "internal_energy": 90,
            },
            "protagonist_items": ["ledger"],
            "items_consumed": [],
            "relationship_changes": [],
            "power_changes": {},
            "foreshadowings": [],
            "continuity_checkpoints": [],
        },
        "joint_docs": {
            "final_location": "market",
            "physical_inventory": ["ledger"],
            "world_joint": "stable",
        },
        "status_shadow": {
            "internal_energy_loss": "5%",
            "expected_injuries": "none",
            "item_consumption": [],
        },
        "constraint_summary": "none",
        "hybrid_composition": {
            "primary": "momentum",
            "secondary": ["continuity"],
            "mixing_logic": "smoke",
        },
        "state_changes": {
            "npc_deaths": [],
            "skill_acquisitions": [],
            "relationship_changes": [],
            "major_items": [],
        },
        "content": {
            "context": content.get("context", ""),
            "event_villain": content.get("event_villain", ""),
            "solution": content.get("solution", ""),
            "reward": content.get("reward", ""),
        },
    }


class TestL3Setup:
    def test_load_and_inject_plot_roadmap(self):
        """Golden route files should load and inject 2 roadmap blocks."""
        bible, blocks, prefix = _load_l3_payload()
        assert prefix
        assert "MasterBible" in bible
        assert "plot_roadmap" in bible["MasterBible"]
        assert isinstance(bible["MasterBible"]["plot_roadmap"], list)
        assert len(bible["MasterBible"]["plot_roadmap"]) == 2
        assert isinstance(blocks, list)
        assert len(blocks) == 2


class TestL3PipelineSmoke:
    def test_stage2_pipeline_smoke_with_real_data(self, tmp_path, monkeypatch):
        """Stage2 should complete without crash and persist at least one arc in DB."""

        async def _run():
            bible, treatment_blocks, prefix = _load_l3_payload()
            db = DBManager(tmp_path / "l3_smoke.db")

            # Avoid terminal blocking at end-of-stage and any retry prompt path.
            monkeypatch.setattr("builtins.input", lambda *args, **kwargs: "")

            # Silence Slack notifier side effects during smoke run.
            from modules.core.slack_bot import notifier

            monkeypatch.setattr(notifier, "send_notification", lambda *args, **kwargs: None)

            project = MagicMock()
            project.db = db
            project.name = f"{prefix}_l3_smoke"
            project.master_bible = bible
            project.volumes = []
            project.paths = MagicMock()
            project.paths.root = tmp_path

            def _save_v20_anchor(key, value):
                db.save_anchor(key, value)

            def _load_v20_anchor(key, default=None):
                value = db.load_anchor(key)
                return default if value is None else value

            project.save_v20_anchor = _save_v20_anchor
            project.load_v20_anchor = _load_v20_anchor

            mock_ui = MagicMock()
            mock_ui.log = MagicMock()
            mock_ui.console = MagicMock()
            mock_ui.menu = MagicMock(return_value="2")

            mock_sys = MagicMock()
            mock_sys.api_client = MagicMock()
            mock_sys.hud = MagicMock()
            mock_sys.hud.pro_root = bible["MasterBible"].get("protagonist_config", {})
            mock_sys.lore = MagicMock()

            async def _safe_commit_async():
                db.conn.commit()

            async def _enrich_passthrough(curr_b, _prev_b, _next_b, _seeds, transfused_history=""):
                payload = curr_b if isinstance(curr_b, dict) else {"context": str(curr_b)}
                return {
                    "content": {
                        "context": payload.get("context", ""),
                        "event_villain": payload.get("event_villain", ""),
                        "solution": payload.get("solution", ""),
                        "reward": payload.get("reward", ""),
                    },
                    "joint_docs": {
                        "final_location": "market",
                        "physical_inventory": ["ledger"],
                        "world_joint": "stable",
                    },
                    "status_shadow": {
                        "internal_energy_loss": "0%",
                        "expected_injuries": "none",
                        "item_consumption": [],
                    },
                    "block_theme": payload.get("context", "")[:60],
                    "joint_docs_meta": {"transfused_history": transfused_history[:80]},
                }

            def _generate_four_phase(**kwargs):
                arc_no = int(kwargs.get("arc_no", 1))
                ep_start = int(kwargs.get("ep_start", 1))
                curr_block = kwargs.get("curr_block", {})
                return _make_mock_arc(arc_no, ep_start, curr_block), {"final_verdict": "PASS", "retries": 0}

            mock_analyst = MagicMock()
            mock_analyst.enrich_raw_block_async = AsyncMock(side_effect=_enrich_passthrough)
            mock_analyst.stitch_joints = MagicMock(return_value={"status": "OK"})
            mock_analyst.get_lack_report = MagicMock(return_value={"status": "ok", "martial_deficit": "none"})
            mock_analyst.plan_single_arc_v20 = MagicMock(
                side_effect=lambda **kwargs: _make_mock_arc(
                    int(kwargs.get("arc_no", 1)),
                    int(kwargs.get("ep_start", 1)),
                    {"content": {"context": "fallback analyst arc"}},
                )
            )

            mock_weaver = MagicMock()
            mock_weaver.generate_arc_drive = MagicMock(return_value={"desire_vector": "stable", "status": "ok"})

            mock_four_phase = MagicMock()
            mock_four_phase.generate = MagicMock(side_effect=_generate_four_phase)

            mock_director = MagicMock()
            mock_director.audit_strategic_plan = MagicMock(
                return_value={"decision": "PASS", "score": 80, "reason": "ok"}
            )
            mock_director.ask = MagicMock(return_value="ok")

            agents = {
                "analyst": mock_analyst,
                "weaver": mock_weaver,
                "four_phase": mock_four_phase,
                "four_phase_arc_generator": mock_four_phase,  # alias for compatibility
                "director": mock_director,
            }

            ctx = Stage2Context(
                ui=mock_ui,
                current_project=project,
                agents=agents,
                sys=mock_sys,
                state_tracker=None,
                selected_genre={"type": "investment", "name": "investment"},
                stage_rejection_history=[],
                audit_event=lambda *a, **k: None,
                write_audit_summary=lambda *a, **k: None,
                validate_arc_mapping=lambda arc, *_args, **_kwargs: arc,
                validate_arc_integrity=lambda arc: bool(arc and arc.get("arc_no")),
                safe_commit_async=_safe_commit_async,
                get_max_episode_from_manuscripts=lambda: 0,
                get_int_input=lambda _prompt, **kw: kw.get("default", 2),
                generate_structured_arc_feedback=lambda **_kw: "",
                generate_reverse_feedback_stage3_to_2=lambda **_kw: "",
                fix_entity_registry_protagonist=lambda registry, _name: registry,
                calculate_arc_from_episode=lambda _ep: 0,
                build_strong_kind_feedback=lambda **_kw: "",
                build_minimal_arc_context=lambda *_a, **_k: "",
                build_focused_context=lambda **_kw: "",
                analyze_rejection_pattern_v60=lambda *_a, **_k: "",
                get_adaptive_feedback_intensity=lambda *_a, **_k: {"guidance": "retry"},
                generate_arc_context_v60=lambda _arcs, _arc_no: "",
            )

            app = MagicMock()
            app._state_tracker_loaded_arcs = 0
            app.state_tracker = None

            orch = Stage2Orchestrator(app=app, context=ctx)
            try:
                await orch.stage_2_arcs_async_logic()

                saved_arcs = db.load_anchor("arcs")
                assert isinstance(saved_arcs, list)
                assert len(saved_arcs) >= 1
                first_arc = saved_arcs[0]
                assert "arc_no" in first_arc
                assert "tactical_doc" in first_arc
                assert "ep_start" in first_arc
                assert "ep_end" in first_arc
                assert mock_analyst.enrich_raw_block_async.call_count >= 1
            finally:
                db.close()

        asyncio.run(_run())
