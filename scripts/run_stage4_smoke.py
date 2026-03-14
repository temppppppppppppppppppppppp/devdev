"""Stage4 mock smoke runner for the 코덱스_테스트 project.

Runs Stage4 with 3 seam mocks, persists manuscripts to the real project DB,
and exports manuscript JSON files under plans/manuscripts/.

Validation tier: focused_mutation
Mutation boundary: writes fixture-project DB and manuscript artifacts.

Usage:
    python scripts/run_stage4_smoke.py
"""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.stage4_context import Stage4Context  # noqa: E402
from modules.core.stage4_orchestrator import Stage4Orchestrator, _RoundOutcome, _SessionConfig  # noqa: E402
from scripts.regression_validation_tiers import FOCUSED_MUTATION  # noqa: E402

PROJECT_NAME = "\ucf54\ub371\uc2a4_\ud14c\uc2a4\ud2b8"
PROJECT_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME
DB_PATH = PROJECT_DIR / "project_data.db"
MS_OUTPUT_DIR = PROJECT_DIR / "plans" / "manuscripts"
VALIDATION_TIER = FOCUSED_MUTATION
MUTATES_PROJECT_STATE = True

MOCK_MANUSCRIPT = (
    "\uc2dc\uc724\uc740 \ubaa8\ub2c8\ud130 \uc55e\uc5d0\uc11c \uc22b\uc790 \ud750\ub984\uc744 \ub530\ub77c\uac00\uba70 \ud638\ud761\uc744 \uace0\ub978\ub2e4. "
    "\ubc18\ub300 \ub9e4\ub9e4\uac00 \ubb34\ub108\uc9c0\uc790 \ud3ec\uc9c0\uc158\uc744 \uc808\ubc18\uc73c\ub85c \uc815\ub9ac\ud558\uace0 \ub9ac\uc2a4\ud06c \ud55c\ub3c4\ub97c \ub2e4\uc2dc \uc7ac\uc124\uc815\ud588\ub2e4. "
    "\ud300\uc6d0\ub4e4\uc740 \uc5ec\uc804\ud788 \ud749\ubd84\ud588\uc9c0\ub9cc \uc2dc\uc724\uc740 \uc9c0\ud45c\uc640 \ud604\uae08 \ud750\ub984\uc744 \ubd84\ub9ac\ud574 \ud310\ub2e8\ud588\uace0, "
    "\ub2e4\uc74c \ub9e4\uc218 \uc870\uac74\uc744 \ubc14\ub85c \ubb38\uc11c\ud654\ud574 \uacf5\uc720\ud588\ub2e4. "
) * 70


@contextmanager
def _noop_spinner(*_args, **_kwargs):
    yield MagicMock(update_detail=MagicMock())


def _normalize_arcs(raw_arcs: object) -> list[dict]:
    if isinstance(raw_arcs, list):
        return [arc for arc in raw_arcs if isinstance(arc, dict)]
    if isinstance(raw_arcs, dict):
        values = [arc for arc in raw_arcs.values() if isinstance(arc, dict)]
        return sorted(values, key=lambda arc: arc.get("ep_start", 0) if isinstance(arc.get("ep_start"), int) else 0)
    return []


class _NoopReferenceAnchor:
    def __init__(self, *_args, **_kwargs):
        pass


def _console_only_fallback_text(text: str) -> str:
    """Best-effort console fallback. Durable outputs still stay UTF-8."""
    return text.encode("cp949", errors="ignore").decode("cp949", errors="ignore")


def _make_mock_project(db: DBManager, bible: dict, arcs: list[dict], output_dir: Path):
    project = MagicMock()
    project.db = db
    project.get_blueprint = db.get_blueprint
    project.get_latest_episode_number = db.get_latest_episode_number
    project.arcs = arcs
    project.master_bible = bible
    project.genre = {"type": "investment", "name": "investment"}
    project.paths = MagicMock()
    project.paths.drafts = output_dir
    project.name = PROJECT_NAME
    project.load_v20_anchor = lambda key: db.load_anchor(key)
    return project


def _make_stage4_ctx(project) -> Stage4Context:
    def _safe_log(message):
        text = str(message)
        try:
            print(text)
        except UnicodeEncodeError:
            print(_console_only_fallback_text(text))

    ui = MagicMock()
    ui.log = _safe_log
    ui.console = MagicMock()
    ui.console.clear = MagicMock()
    ui.title = MagicMock()

    sys_obj = MagicMock()
    sys_obj.guard = None
    sys_obj.hud = None
    sys_obj.api_client = MagicMock()

    return Stage4Context(
        ui=ui,
        current_project=project,
        agents={},
        sys=sys_obj,
        state_tracker=None,
        selected_genre={"type": "investment", "name": "investment"},
        perf_timer=MagicMock(),
        get_int_input=lambda *a, **kw: kw.get("default", 1),
        build_item_acquisition_timeline=lambda *a, **kw: "",
        load_narrative_summaries=lambda: "",
        get_protagonist_name=lambda: "\uc2dc\uc724",
        generate_narrative_summary=lambda *a, **kw: None,
        flush_audit_buffer=lambda: None,
        safe_commit=lambda: project.db.conn.commit(),
    )


def _mock_prepare_session(output_dir: Path, target_ep: int = 3) -> _SessionConfig:
    return _SessionConfig(
        chief_writer=MagicMock(),
        manuscript_validator=MagicMock(),
        consistency_validator=MagicMock(),
        blocking_validator=MagicMock(),
        continuity_validator=MagicMock(),
        s4_genre_type="investment",
        story_context="- genre: investment\n- protagonist: \uc2dc\uc724",
        style_guide="\uce74\ub9ac\uc2a4\ub9c8 \uc0ac\uc774\ubc84 \ubb38\ud3ec, 4K \uc774\uc0c1",
        target_ep=target_ep,
        output_dir=output_dir,
        v50_modules_available=False,
        total_planned_ep=3,
    )


def _mock_handle_round_outcome(*, round_ctx) -> _RoundOutcome:
    next_ep = int(getattr(round_ctx, "next_ep", 1))
    return _RoundOutcome(
        final_manuscript=MOCK_MANUSCRIPT,
        final_title=f"{next_ep}\ud654 \uace8\ub4e0\ub8e8\ud2b8",
        final_state_updates={},
        should_return=False,
    )


def _make_slim_process_pass_result(db: DBManager, output_dir: Path):
    def _slim(
        *,
        next_ep: int,
        final_manuscript: str,
        final_title: str,
        **_kwargs,
    ) -> bool:
        db.save_manuscript(ep_num=next_ep, title=final_title, content=final_manuscript)
        db.conn.commit()
        out = output_dir / f"ep_{next_ep:04d}.txt"
        out.write_text(f"# {final_title}\n\n{final_manuscript}", encoding="utf-8")
        return True

    return _slim


def main() -> None:
    assert DB_PATH.exists(), f"DB not found: {DB_PATH}"
    MS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    db = DBManager(DB_PATH)
    try:
        bible = db.load_anchor("bible")
        arcs = _normalize_arcs(db.load_anchor("arcs"))
        assert bible, "Bible is empty"
        assert len(arcs) >= 1, f"arcs must be >= 1, got {len(arcs)}"
        bp_count = db.get_latest_blueprint_number()
        assert bp_count >= 3, f"blueprints must be >= 3, got {bp_count}"
        print(f"[OK] precheck passed: arcs={len(arcs)}, blueprints={bp_count}")

        existing_next_ep = db.get_latest_episode_number()
        if existing_next_ep > 1:
            print(f"[WARN] existing manuscripts detected (next_ep={existing_next_ep}), clearing manuscripts table.")
            db.cursor.execute("DELETE FROM manuscripts")
            db.conn.commit()

        project = _make_mock_project(db, bible, arcs, MS_OUTPUT_DIR)
        ctx = _make_stage4_ctx(project)
        orch = Stage4Orchestrator(app=MagicMock(), context=ctx)

        orch._prepare_stage4_session = lambda **_kw: _mock_prepare_session(MS_OUTPUT_DIR, target_ep=3)
        orch._handle_round_outcome = _mock_handle_round_outcome

        orch._post_processor = MagicMock()
        orch._post_processor.process_pass_result = _make_slim_process_pass_result(db, MS_OUTPUT_DIR)
        orch._post_processor.run_post_episode_tasks = MagicMock()

        orch._context_builder = MagicMock()
        orch._context_builder.prepare_episode_context.return_value = {
            "arc_pos": 1,
            "total_ep_in_arc": 10,
            "arc_tactical": "",
            "prev_text": "",
            "prev_ending": "",
            "prev_manuscripts_text": "",
            "episode_digest": "",
            "hud_report": "",
            "current_inventory": [],
            "current_martial_arts": [],
            "cumulative_bible": {},
            "dead_npcs": [],
            "item_acquisition_timeline": "",
            "chain_link_section": "",
            "world_state_summary": "",
        }
        orch._context_builder.build_mandatory_context.return_value = {
            "reference_anchor_prompt": "",
            "mandatory_context": "",
            "anti_trope_prompt": "",
            "justification_prompt": "",
            "reflexion_prompt": "",
        }
        orch._context_builder.build_round_context.side_effect = lambda **kwargs: SimpleNamespace(
            next_ep=kwargs["next_ep"]
        )

        print("[RUN] Stage4 start (3 episodes, mock LLM seams)...")
        with (
            patch("modules.core.spinners.StageSpinner", _noop_spinner),
            patch("modules.core.reference_anchor.ReferenceAnchor", _NoopReferenceAnchor),
        ):
            orch.stage_4_v2_chief_writer(limit_mode=False)
        print("[OK] Stage4 complete")

        saved_count = 0
        for ep in range(1, 4):
            ms = db.get_manuscript(ep)
            if not ms:
                continue
            saved_count += 1
            out_path = MS_OUTPUT_DIR / f"manuscript_ep{ep}.json"
            out_path.write_text(
                json.dumps(
                    {
                        "ep_num": ep,
                        "title": ms["title"],
                        "content_length": len(ms["content"]),
                        "content_preview": ms["content"][:500],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"[FILE] ep{ep} '{ms['title']}' len={len(ms['content'])} -> {out_path.name}")

        next_ep = db.get_latest_episode_number()
        print(f"[DONE] manuscripts saved={saved_count}, next_ep={next_ep}, output={MS_OUTPUT_DIR}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
