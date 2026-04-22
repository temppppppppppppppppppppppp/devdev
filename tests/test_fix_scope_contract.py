"""[DCM] fix_scope contract: authoritative scope validation + evidence separation tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ── Helpers ──────────────────────────────────────────────────────


def _make_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
    ctx.current_project.db = MagicMock()
    ctx.current_project.db.get_recent_manuscripts.return_value = []
    ctx.current_project.db.get_manuscript.return_value = {"content": "이전 원고"}
    ctx.current_project.db.get_episode_bible.return_value = {}
    ctx.state_tracker = MagicMock()
    ctx.state_tracker.npc_registry = {}
    ctx.state_tracker.item_state_registry = {}
    ctx.state_tracker.get_npc_change_history.return_value = []
    ctx.state_tracker.check_destroyed_entity_in_manuscript.return_value = []
    ctx.state_tracker.in_world_timeline = []
    ctx.state_tracker.check_time_consistency.return_value = []
    ctx.agents = {"director": MagicMock(), "chief_writer": MagicMock()}
    ctx.context_advisor = None
    ctx.memory = None
    ctx.get_module = MagicMock(return_value=None)
    ctx.quality_dashboard = None
    ctx.session_logger = None
    ctx.sys = MagicMock()
    ctx.sys.hud = MagicMock()
    ctx.sys.hud.pro_root = {}
    return ctx


def _make_s4ir():
    from modules.core.stage4_interview_round import Stage4InterviewRound

    ctx = _make_ctx()
    ir = Stage4InterviewRound(ctx)
    return ir


def _local_fix_pack(*patch_targets, target_kind="entity_ref"):
    return {
        "patch_targets": list(patch_targets) or ["anchor_1"],
        "must_fix": ["fix item"],
        "do_not_regress": ["structure"],
        "success_condition": "anchors updated",
        "target_kind": target_kind,
    }


# ── Prompt contract (T1) ────────────────────────────────────────


_BLANK_FIX_SCOPE_WARNING = "빈 문자열(\"\")로 남기"


def _get_director_prompt(key: str) -> str:
    from modules.core.prompt_loader import PromptLoader

    loader = PromptLoader()
    loader.invalidate_cache("director")
    return loader.get_raw("director", key) or ""


def test_ensemble_variable_prompt_warns_blank_fix_scope():
    prompt = _get_director_prompt("ENSEMBLE_VARIABLE_PROMPT")
    assert _BLANK_FIX_SCOPE_WARNING in prompt


def test_ensemble_selection_prompt_warns_blank_fix_scope():
    prompt = _get_director_prompt("ENSEMBLE_SELECTION_PROMPT")
    assert _BLANK_FIX_SCOPE_WARNING in prompt


def test_audit_prompt_warns_blank_fix_scope():
    prompt = _get_director_prompt("DIRECTOR_AUDIT_PROMPT_V30")
    assert _BLANK_FIX_SCOPE_WARNING in prompt


# ── Authoritative scope validation (T2) ─────────────────────────


class TestAuthoritativeFixScopeValidation:
    """_normalize_director_gate_semantics must flag blank/invalid fix_scope."""

    def test_blank_fix_scope_on_reject_creates_violation(self):
        ir = _make_s4ir()
        result = {
            "verdict": "REJECT",
            "final_verdict": "REJECT",
            "score": 50,
            "fix_scope": "",
        }
        normalized = ir._normalize_director_gate_semantics(result)
        violation = normalized.get("authoritative_fix_scope_violation")
        assert violation is not None
        assert violation["type"] == "blank_authoritative_fix_scope"
        assert violation["verdict"] == "REJECT"

    def test_blank_fix_scope_on_pass_with_fix_creates_violation(self):
        ir = _make_s4ir()
        result = {
            "verdict": "PASS_WITH_FIX",
            "final_verdict": "PASS_WITH_FIX",
            "score": 93,
            "fix_scope": "",
        }
        normalized = ir._normalize_director_gate_semantics(result)
        violation = normalized.get("authoritative_fix_scope_violation")
        assert violation is not None
        assert violation["type"] == "blank_authoritative_fix_scope"
        assert violation["verdict"] == "PASS_WITH_FIX"

    def test_invalid_fix_scope_on_reject_creates_violation(self):
        ir = _make_s4ir()
        result = {
            "verdict": "REJECT",
            "final_verdict": "REJECT",
            "score": 40,
            "fix_scope": "unknown_value",
        }
        normalized = ir._normalize_director_gate_semantics(result)
        violation = normalized.get("authoritative_fix_scope_violation")
        assert violation is not None
        assert violation["type"] == "invalid_authoritative_fix_scope"
        assert violation["raw_value"] == "unknown_value"

    def test_valid_fix_scope_on_reject_no_violation(self):
        ir = _make_s4ir()
        for scope in ("inplace", "partial", "full"):
            result = {
                "verdict": "REJECT",
                "final_verdict": "REJECT",
                "score": 50,
                "fix_scope": scope,
            }
            normalized = ir._normalize_director_gate_semantics(result)
            assert normalized.get("authoritative_fix_scope_violation") is None

    def test_blank_fix_scope_on_pass_no_violation(self):
        ir = _make_s4ir()
        result = {
            "verdict": "PASS",
            "final_verdict": "PASS",
            "score": 95,
            "fix_scope": "",
        }
        normalized = ir._normalize_director_gate_semantics(result)
        assert normalized.get("authoritative_fix_scope_violation") is None

    def test_pass_with_fix_inplace_fix_scope_no_violation(self):
        ir = _make_s4ir()
        result = {
            "verdict": "PASS_WITH_FIX",
            "final_verdict": "PASS_WITH_FIX",
            "score": 93,
            "fix_scope": "inplace",
            "fix_pack": _local_fix_pack("anchor_1"),
        }
        normalized = ir._normalize_director_gate_semantics(result)
        assert normalized.get("authoritative_fix_scope_violation") is None


# ── Evidence separation (T3) ────────────────────────────────────


class TestEvidenceSeparation:
    """Authoritative scope and derived scope must be distinguishable."""

    def test_gate_semantics_payload_includes_violation(self):
        ir = _make_s4ir()
        director_result = {
            "verdict": "REJECT",
            "final_verdict": "REJECT",
            "score": 50,
            "fix_scope": "",
        }
        payload = ir._build_gate_semantics_payload(director_result)
        assert payload["authoritative_fix_scope"] == ""
        assert "authoritative_fix_scope_violation" in payload
        assert payload["authoritative_fix_scope_violation"]["type"] == "blank_authoritative_fix_scope"

    def test_gate_semantics_payload_no_violation_when_valid(self):
        ir = _make_s4ir()
        director_result = {
            "verdict": "REJECT",
            "final_verdict": "REJECT",
            "score": 50,
            "fix_scope": "partial",
        }
        payload = ir._build_gate_semantics_payload(director_result)
        assert "authoritative_fix_scope_violation" not in payload

    def test_compact_attempt_preserves_authoritative_fix_scope(self):
        ir = _make_s4ir()
        attempt = {
            "strategy": "balanced",
            "score": 60,
            "fix_scope": "full",
            "authoritative_fix_scope": "partial",
            "rejection_reason": "post-select conflict",
        }
        snapshot = ir._compact_attempt_snapshot(attempt)
        assert snapshot["fix_scope"] == "full"
        assert snapshot["authoritative_fix_scope"] == "partial"

    def test_compact_attempt_omits_empty_authoritative_fix_scope(self):
        ir = _make_s4ir()
        attempt = {
            "strategy": "balanced",
            "score": 60,
            "fix_scope": "full",
            "authoritative_fix_scope": "",
            "rejection_reason": "some reason",
        }
        snapshot = ir._compact_attempt_snapshot(attempt)
        assert snapshot["fix_scope"] == "full"
        # empty string is filtered out by the {k:v for ... if v not in ("", ...)} guard
        assert "authoritative_fix_scope" not in snapshot


# ── Director ensemble T2 validation ─────────────────────────────


class TestDirectorEnsembleValidation:
    """director_ensemble._build_authoritative_result must emit violation metadata."""

    def test_firewall_inplace_does_not_erase_blank_authoritative_fix_scope(self):
        from modules.domain.agents.director_ensemble import (
            DirectorEnsembleSelector,
            _EnsembleSelectionState,
        )

        director = MagicMock()
        director._last_thinking = ""
        director._operator_log = MagicMock()
        selector = DirectorEnsembleSelector(director)
        state = _EnsembleSelectionState(
            selected_letter="A",
            selected_idx=0,
            selected_candidate={"manuscript": "candidate manuscript"},
            original_verdict="REJECT",
            score=50,
            pre_firewall_score=50,
            score_breakdown_raw={},
            contradiction_check={},
            numeric_consistency_review=[],
            consistency_checklist={},
            v60_97_swapped=False,
            firewall_fixable=True,
            firewall_reason="local contradiction only",
            contradiction_details=[],
        )

        payload = selector._build_ensemble_decision_payload(
            ep_num=1,
            result={"fix_scope": "", "fix_scope_reasoning": "", "fix_pack": {}, "feedback": {}},
            state=state,
            final_verdict="REJECT",
            adaptive_result={},
        )

        assert payload["fix_scope"] == "inplace"
        assert payload["repair_scope"] == "inplace"
        assert payload["authoritative_fix_scope"] == ""
        assert payload["authoritative_fix_scope_violation"]["type"] == "blank_authoritative_fix_scope"

    def test_stage4_firewall_fixable_backfills_fix_pack_when_director_left_it_blank(self):
        from modules.domain.agents.director_ensemble import DirectorEnsembleSelector, _EnsembleSelectionState

        class _FakeDirector:
            def _operator_log(self, *_args, **_kwargs):
                return None

        selector = DirectorEnsembleSelector(_FakeDirector())
        state = _EnsembleSelectionState(
            selected_letter="A",
            selected_idx=0,
            selected_candidate={"manuscript": "candidate manuscript"},
            original_verdict="PASS_WITH_FIX",
            score=97,
            pre_firewall_score=97,
            score_breakdown_raw={"continuity_contradiction": 35},
            contradiction_check={},
            numeric_consistency_review=[],
            consistency_checklist={},
            v60_97_swapped=False,
            firewall_fixable=True,
            firewall_reason="Fixable Contradiction Firewall: local contradiction 2건",
            contradiction_details=[
                {
                    "severity": "MAJOR",
                    "type": "고유명사",
                    "current_violation": "박성호 소속을 잘못 표기함",
                    "fix_suggestion": "박성호 소속을 SW인베스트먼트로 통일",
                }
            ],
        )

        payload = selector._build_ensemble_decision_payload(
            ep_num=11,
            result={
                "fix_scope": "inplace",
                "fix_scope_reasoning": "",
                "fix_pack": {},
                "feedback": {"action_items": ["박성호 소속을 SW인베스트먼트로 통일"]},
            },
            state=state,
            final_verdict="PASS_WITH_FIX",
            adaptive_result={},
        )

        assert payload["fix_pack"]["target_kind"] == "local_sentence"
        assert payload["fix_pack"]["patch_targets"]
        assert payload["fix_pack"]["must_fix"]
        assert payload["fix_pack"]["do_not_regress"]
        assert payload["fix_pack"]["success_condition"]
        assert payload["repair_contract"]["provenance"] == "runtime_synthesized"
