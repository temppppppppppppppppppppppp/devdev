import json
from pathlib import Path

from modules.core.services.project_service import DestructiveOpResult


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "2026-03-13" / "safe-op-recovery-state-matrix.json"
MAIN_A_PATH = ROOT / "main_a.py"
PROJECT_SERVICE_PATH = ROOT / "modules" / "core" / "services" / "project_service.py"


def _load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_safe_op_recovery_contract_matches_destructive_result_state_vector():
    contract = _load_contract()
    result_model = contract["destructive_result_model"]

    assert contract["contract_id"] == "safe-op-recovery-state-matrix-v1"
    assert result_model["status_enum"] == ["aborted", "partial_restore_failed", "success"]

    aborted = DestructiveOpResult(operation="rollback_episode", target_ep=4)
    partial = DestructiveOpResult(
        operation="rollback_episode",
        target_ep=4,
        db_committed=True,
        partial_failures=[{"step": "project.load_from_db", "reason": "boom"}],
    )
    success = DestructiveOpResult(operation="rollback_episode", target_ep=4, db_committed=True)

    assert aborted.status == "aborted"
    assert aborted.runtime_restore_ok is False
    assert aborted.cache_invalidation_required is False

    assert partial.status == "partial_restore_failed"
    assert partial.runtime_restore_ok is False
    assert partial.cache_invalidation_required is True

    assert success.status == "success"
    assert success.runtime_restore_ok is True
    assert success.cache_invalidation_required is True


def test_safe_ops_matrix_matches_project_service_restore_pipeline():
    contract = _load_contract()
    source = _read(PROJECT_SERVICE_PATH)
    pipeline = contract["runtime_restore_pipeline"]

    assert 'if result.status == "success":' in source
    assert 'return "partial_restore_failed"' in source
    assert 'return "success"' in source
    assert 'return "aborted"' in source
    assert '[Partial] {result.operation} committed' in source

    for step in pipeline["restore_steps"]:
        assert f'"{step}"' in source

    assert "_trim_emotion_tracker_history" in source
    assert "_trim_state_delta_tracker_history" in source
    assert '"emotion_history.invariant"' in source
    assert '"state_delta_tracker.invariant"' in source
    assert "_clear_base_agent_context_caches" in source
    assert "self.last_destructive_result = result" in source


def test_safe_ops_matrix_covers_all_destructive_operations_and_wrapper_cache_policy():
    contract = _load_contract()
    project_service_source = _read(PROJECT_SERVICE_PATH)
    main_a_source = _read(MAIN_A_PATH)

    wrapper_expectations = {
        "reset_stage_2": {
            "wrapper": "def _reset_stage_2(self):",
            "service_call": "self._project_service.reset_stage_2()",
            "foreshadow": "_ft.clear()",
        },
        "rewind_stage_2": {
            "wrapper": "def _rewind_stage_2(self):",
            "service_call": "self._project_service.rewind_stage_2()",
            "foreshadow": "_ft.load_from_db(self.current_project.db)",
        },
        "rollback_episode": {
            "wrapper": "def _rollback_episode(self):",
            "service_call": "self._project_service.rollback_episode()",
            "foreshadow": "_ft.load_from_db(self.current_project.db)",
        },
        "wipe_production_data": {
            "wrapper": "def _wipe_production_data(self):",
            "service_call": "self._project_service.wipe_production_data()",
            "foreshadow": "_ft.clear()",
        },
    }

    for operation, matrix in contract["safe_ops"].items():
        assert operation in wrapper_expectations
        assert f"def {matrix['service_method'].split('.')[-1]}(self)" in project_service_source or (
            operation in {"rewind_stage_2", "rollback_episode"} and f"def {matrix['service_method'].split('.')[-1]}(self" in project_service_source
        )
        assert wrapper_expectations[operation]["wrapper"] in main_a_source
        assert wrapper_expectations[operation]["service_call"] in main_a_source
        assert wrapper_expectations[operation]["foreshadow"] in main_a_source
        assert f'operation="{operation}"' in project_service_source
        assert matrix["bool_return_semantics"] == "True iff db_committed"
        assert matrix["wrapper_post_success"]["null_app_caches"] == [
            "state_tracker",
            "_cumulative_state_cache",
            "_cumulative_state_cache_key",
            "_narrative_summaries_cache",
        ]
        assert matrix["wrapper_post_success"]["invalidate_prompt_builder"] is True

    assert "self._prompt_builder.invalidate_timeline_cache()" in main_a_source
    assert "invalidate_manuscript_cache" in main_a_source
    assert "invalidate_caches" in main_a_source


def test_project_switch_semantics_are_explicitly_separate_from_safe_op_result_model():
    contract = _load_contract()
    main_a_source = _read(MAIN_A_PATH)
    project_switch = contract["project_switch_semantics"]

    assert project_switch["classification"] == "project_switch_not_safe_op"
    assert project_switch["uses_destructive_result_model"] is False
    assert "def _reload_project_environment(self, project_name: str)" in main_a_source
    assert "BaseAgent._context_caches.clear()" in main_a_source
    assert "BaseAgent._current_key_idx = 0" in main_a_source
    assert "BaseAgent._init_api_keys()" in main_a_source
