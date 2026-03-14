import inspect
import json
from pathlib import Path

from modules.core.stage2_context import (
    _RETRY_FEEDBACK_CALLBACK_SPECS,
    Stage2Context,
)
from modules.core.stage3_context import Stage3Context
from modules.core.stage4_context import _CONDITIONAL_MODULE_KEYS, Stage4Context


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "2026-03-13" / "runtime-ownership-contract.json"
MAIN_A_PATH = ROOT / "main_a.py"
STAGE2_CONTEXT_PATH = ROOT / "modules" / "core" / "stage2_context.py"
STAGE3_CONTEXT_PATH = ROOT / "modules" / "core" / "stage3_context.py"
STAGE4_CONTEXT_PATH = ROOT / "modules" / "core" / "stage4_context.py"


def _load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _init_params(ctx_type) -> set[str]:
    return {
        name
        for name in inspect.signature(ctx_type.__init__).parameters
        if name not in {"self"}
    }


def test_runtime_ownership_contract_declares_main_a_composition_root():
    contract = _load_contract()

    assert contract["contract_id"] == "runtime-ownership-contract-v1"
    assert contract["composition_root"] == {
        "primary_entry_module": "main_a.py",
        "primary_app_class": "SovereignApp",
        "classification": "current_composition_root",
        "non_goals": [
            "thin facade",
            "stale shell",
            "library-style reusable framework entry",
        ],
    }


def test_main_a_matches_stage_wrapper_runtime_ownership_contract():
    contract = _load_contract()
    main_a_source = _read(MAIN_A_PATH)

    assert "self._stage2_orch = Stage2Orchestrator(app=self)" in main_a_source
    assert "self._stage3_orch = Stage3Orchestrator(app=self)" in main_a_source
    assert "self._stage4_orch = Stage4Orchestrator(app=self)" in main_a_source

    wrappers = {item["stage"]: item for item in contract["stage_entry_wrappers"]}

    stage2 = wrappers["stage2"]
    assert stage2["wrapper_method"] == "SovereignApp._stage_2_arcs"
    assert stage2["context_factory"] == "Stage2Context.from_app(self)"
    assert stage2["delegate"] == "Stage2Orchestrator.stage_2_arcs_async_logic"
    assert "self._stage2_orch.ctx = Stage2Context.from_app(self)" in main_a_source
    assert "self.state_tracker = _s2_ctx.state_tracker" in main_a_source
    assert 'self._state_tracker_loaded_arcs = getattr(_s2_ctx, "state_tracker_loaded_arcs", 0)' in main_a_source

    stage3 = wrappers["stage3"]
    assert stage3["wrapper_method"] == "SovereignApp._stage_3_batch_blueprinting"
    assert stage3["context_factory"] == "Stage3Context.from_app(self)"
    assert stage3["delegate"] == "Stage3Orchestrator.stage_3_batch_blueprinting"
    assert "self._stage3_orch.ctx = Stage3Context.from_app(self)" in main_a_source

    stage4 = wrappers["stage4"]
    assert stage4["wrapper_method"] == "SovereignApp._stage_4_v2_chief_writer"
    assert stage4["context_factory"] == "Stage4Context.from_app(self)"
    assert stage4["delegate"] == "Stage4Orchestrator.stage_4_v2_chief_writer"
    assert "if not hasattr(self, \"state_tracker\") or self.state_tracker is None:" in main_a_source
    assert "if not hasattr(self, \"world_state\") or self.world_state is None:" in main_a_source
    assert "if not hasattr(self, \"fact_ledger\") or self.fact_ledger is None:" in main_a_source
    assert "self._stage4_orch.ctx = Stage4Context.from_app(self)" in main_a_source


def test_stage2_contract_matches_live_factory_surface():
    contract = _load_contract()["stage_context_factories"]["stage2"]
    source = _read(STAGE2_CONTEXT_PATH)
    init_params = _init_params(Stage2Context)

    assert contract["safe_reader"] == "_safe_getattr"
    assert "def _safe_getattr" in source

    for name in contract["required_live_base"]:
        assert f"{name}=app.{name}" in source
        assert name in init_params

    for name in contract["optional_state_and_services"]:
        assert f'{name}=_safe_getattr(app, "{name}", None)' in source or (
            name == "use_arc_corrector"
            and f'{name}=_safe_getattr(app, "{name}", False)' in source
        )
        assert name in init_params

    callback_patterns = {
        "audit_event": '_audit_event',
        "cumulative_state_cache": '_cumulative_state_cache',
        "cumulative_state_cache_key": '_cumulative_state_cache_key',
        "write_audit_summary": '_write_audit_summary',
        "validate_arc_data_fields": '_validate_arc_data_fields',
        "validate_arc_mapping": '_validate_arc_mapping',
        "validate_arc_integrity": '_validate_arc_integrity',
        "state_tracker_loaded_arcs": '_state_tracker_loaded_arcs',
        "safe_commit_async": '_safe_commit_async',
        "get_max_episode_from_manuscripts": '_get_max_episode_from_manuscripts',
        "get_int_input": '_get_int_input',
        "fix_entity_registry_protagonist": '_fix_entity_registry_protagonist',
        "calculate_arc_from_episode": '_calculate_arc_from_episode',
        "session_logger": '_session_logger',
    }
    for name in contract["direct_callbacks"]:
        assert name in init_params
        if name == "sync_cache_key_to_app":
            assert "sync_cache_key_to_app=_make_sync_callback(weakref.ref(app))" in source
            continue
        assert callback_patterns[name] in source

    assert set(contract["retry_feedback_callbacks"]) == set(_RETRY_FEEDBACK_CALLBACK_SPECS)
    for name in contract["retry_feedback_callbacks"]:
        assert name in init_params
        assert f'"{name}"' in source


def test_stage3_contract_matches_live_factory_surface():
    contract = _load_contract()["stage_context_factories"]["stage3"]
    source = _read(STAGE3_CONTEXT_PATH)
    init_params = _init_params(Stage3Context)

    assert contract["safe_reader"] == "getattr"
    assert "getattr(app, " in source
    assert "_safe_getattr" not in source

    for name in contract["required_live_base"]:
        assert f"{name}=app.{name}" in source
        assert name in init_params

    for name in contract["optional_state_and_services"]:
        assert f'{name}=getattr(app, "{name}", None)' in source
        assert name in init_params

    callback_patterns = {
        "get_protagonist_name": '_get_protagonist_name',
        "audit_event": '_audit_event',
        "write_audit_summary": '_write_audit_summary',
        "get_arc_context_for_episode": '_get_arc_context_for_episode',
        "get_max_episode_from_manuscripts": '_get_max_episode_from_manuscripts',
        "get_int_input": '_get_int_input',
        "safe_commit": '_safe_commit',
        "validate_arc_data_fields": '_validate_arc_data_fields',
        "validate_blueprint_integrity": '_validate_blueprint_integrity',
        "fix_entity_registry_protagonist": '_fix_entity_registry_protagonist',
        "session_logger": '_session_logger',
    }
    for name in contract["callbacks_and_observers"]:
        assert name in init_params
        assert callback_patterns[name] in source


def test_stage4_contract_matches_live_factory_surface():
    contract = _load_contract()["stage_context_factories"]["stage4"]
    source = _read(STAGE4_CONTEXT_PATH)
    init_params = _init_params(Stage4Context)

    assert contract["safe_reader"] == "_safe_getattr"
    assert "def _safe_getattr" in source
    assert list(_CONDITIONAL_MODULE_KEYS) == contract["conditional_modules"]

    for name in contract["required_live_base"]:
        assert f"{name}=app.{name}" in source
        assert name in init_params

    for name in contract["optional_state_and_services"]:
        token = f'{name}=_safe_getattr(app, "{name}", None)'
        if name == "session_logger":
            token = 'session_logger=_safe_getattr(app, "_session_logger", None)'
        assert token in source
        assert name in init_params

    callback_patterns = {
        "get_int_input": '_get_int_input',
        "build_item_acquisition_timeline": '_build_item_acquisition_timeline',
        "load_narrative_summaries": '_load_narrative_summaries',
        "get_protagonist_name": '_get_protagonist_name',
        "extract_npc_profiles": '_extract_npc_profiles',
        "generate_narrative_summary": '_generate_narrative_summary',
        "generate_writer_guidance_v60_8": '_generate_writer_guidance_v60_8',
        "enrich_director_result": '_enrich_director_result',
        "audit_event": '_audit_event',
        "write_audit_summary": '_write_audit_summary',
        "flush_audit_buffer": '_flush_audit_buffer',
        "safe_commit": '_safe_commit',
    }
    for name in contract["callbacks"]:
        assert name in init_params
        assert callback_patterns[name] in source


def test_runtime_ownership_contract_splits_stage_ownership_and_downstream_compatibility():
    contract = _load_contract()
    seams = contract["repair_seam_ownership"]
    stage_owners = {item["surface"] for item in seams if item["classification"] == "stage_ownership"}
    downstream = {
        item["surface"] for item in seams if item["classification"] == "downstream_compatibility"
    }

    assert stage_owners == {
        "main_a.py:SovereignApp._stage_2_arcs",
        "main_a.py:SovereignApp._stage_3_batch_blueprinting",
        "main_a.py:SovereignApp._stage_4_v2_chief_writer",
    }
    assert downstream == {
        "modules/core/stage2_context.py:Stage2Context.from_app",
        "modules/core/stage3_context.py:Stage3Context.from_app",
        "modules/core/stage4_context.py:Stage4Context.from_app",
    }
