import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import main_a
from modules.core.stage4_orchestrator import Stage4Orchestrator, _clamp_reference_excerpt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "docs" / "2026-03-13" / "provider-config-context-continuity-contract.json"


def test_contract_freezes_stage3_authority_and_models_policy():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    main_source = (PROJECT_ROOT / "main_a.py").read_text(encoding="utf-8")

    assert contract["unit"] == "BGR-E5"
    assert contract["stage3_context"]["authority_factory"] == "Stage3Context.from_app(self)"
    assert contract["models_config"]["source_of_truth"] == "config/models.yaml"
    assert contract["models_config"]["policy"] == "repo_root_only"
    assert "self._stage3_orch.ctx = Stage3Context.from_app(self)" in main_source


def test_main_a_load_models_yaml_uses_repo_root_ssot(tmp_path, monkeypatch):
    root_models = tmp_path / "config" / "models.yaml"
    project_models = tmp_path / "projects" / "demo" / "config" / "models.yaml"
    root_models.parent.mkdir(parents=True, exist_ok=True)
    project_models.parent.mkdir(parents=True, exist_ok=True)

    root_models.write_text("agents:\n  writer: root-writer\n", encoding="utf-8")
    project_models.write_text("agents:\n  writer: project-writer\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("main_a.load_models_yaml", lambda: {"agents": {"writer": "root-writer"}})

    app = SimpleNamespace(
        current_project=SimpleNamespace(paths=SimpleNamespace(config=project_models.parent)),
        ui=MagicMock(),
    )

    loaded = main_a.SovereignApp._load_models_yaml(app)

    assert loaded["agents"]["writer"] == "root-writer"


def test_reference_excerpt_clamp_uses_stage4_budget_guard():
    trimmed = _clamp_reference_excerpt("A" * 12000, max_chars=4096)

    assert len(trimmed) <= 4096
    assert trimmed.startswith("A" * 100)


def test_prepare_stage4_session_clamps_reference_excerpt(monkeypatch, tmp_path):
    app = MagicMock()
    app.ui = MagicMock()
    app.ui.log = MagicMock()
    app.ui.console = MagicMock()
    app.ui.title = MagicMock()
    app.selected_genre = {"type": "wuxia", "name": "무협"}
    app.current_project = MagicMock()
    app.current_project.master_bible = {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "천하제일"}},
            "AssetLibrary": {"KeyNPCs": [], "Key_Items": []},
            "protagonist_config": {"world_origin": "현대", "incarnation_type": "빙의"}
        }
    }
    app.current_project.arcs = [{"arc_no": 1}]
    app.current_project.paths = MagicMock()
    app.current_project.paths.drafts = tmp_path
    app.current_project.db = MagicMock()
    app.current_project.db.get_latest_blueprint_number.return_value = 3
    app.current_project.get_latest_episode_number.return_value = 1
    app.current_project.name = "test_project"
    app.perf_timer = MagicMock()
    app.sys = MagicMock()
    app.sys.api_client = MagicMock()
    app.agents = {"director": MagicMock(), "writer": MagicMock(), "manager": MagicMock()}
    app.character_voice = None
    app.diversity_engine = None
    app.memory = MagicMock()
    app.failure_learner = None
    app.foreshadow_tracker = None
    app.state_tracker = None

    monkeypatch.setattr(
        "modules.core.stage4_orchestrator.load_style_guide_anchor",
        lambda _project: {"reference_excerpt": "B" * 12000},
    )
    monkeypatch.setattr("modules.core.stage4_orchestrator.resolve_project_bible_pov", lambda _project: None)
    monkeypatch.setattr("modules.core.spinners.STAGE0_AVAILABLE", True)
    monkeypatch.setattr("modules.core.spinners.V50_MODULES_AVAILABLE", False)

    with (
        patch("modules.domain.agents.chief_writer.ChiefWriter", return_value=MagicMock()),
        patch("modules.domain.agents.manuscript_validator.ManuscriptValidator", return_value=MagicMock()),
        patch("modules.validation.consistency_validator.ConsistencyValidator", return_value=MagicMock()),
        patch("modules.validation.blocking_validator.BlockingValidator", return_value=MagicMock()),
        patch("modules.validation.continuity_validator.ContinuityValidator", return_value=MagicMock()),
        patch(
            "modules.core.stage4_orchestrator._threshold",
            side_effect=lambda key, default: 4096 if key == "context.reference_excerpt_chars" else default,
        ),
    ):
        session = Stage4Orchestrator(app)._prepare_stage4_session(limit_mode=False, target_ep=2)

    assert session is not None
    assert len(session.reference_excerpt) <= 4096
