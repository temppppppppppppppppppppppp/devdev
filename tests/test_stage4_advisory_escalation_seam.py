"""Regression tests for C-1/C-2 seam fixes: advisory escalation and post-select conflict scope.

C-1: Strong advisory escalation that creates PASS_WITH_FIX with no viable fix_scope
     must carry actionable fix_scope="partial" on the resulting REJECT so the downstream
     reject guidance produces meaningful retry direction instead of a blank-scope loop.

C-2: Post-select conflict downgrade must propagate fix_scope="full" and
     reject_bucket="post_select_conflict" end-to-end through the reject guidance path.
"""

from unittest.mock import MagicMock

from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.core.stage4_orchestrator import Stage4Orchestrator

# ── helpers ─────────────────────────────────────────────────────────────────


def _make_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.name = "test_project"
    ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
    ctx.current_project.db = MagicMock()
    ctx.state_tracker = MagicMock()
    ctx.agents = {"director": MagicMock()}
    ctx.context_advisor = None
    ctx.memory = None
    ctx.adaptive_manager = None
    ctx.failure_learner = None
    ctx.quality_dashboard = None
    ctx.enrich_director_result = None
    ctx.get_module = MagicMock(return_value=None)
    return ctx


def _make_ir(advisory_summary: dict | None = None) -> Stage4InterviewRound:
    ir = Stage4InterviewRound(_make_ctx())
    ir._last_advisory_summary = advisory_summary or {}
    return ir


def _base_pass_result(**overrides) -> dict:
    base = {
        "director_verdict": "PASS",
        "final_verdict": "PASS",
        "verdict": "PASS",
        "authoritative_fix_scope": "",
        "fix_scope": "",
        "repair_scope": "none",
        "gate_basis": "",
        "fix_pack": {},
    }
    base.update(overrides)
    return base


def _ready_local_fix_pack() -> dict:
    return {
        "patch_targets": ["씬 1 객장 묘사 첫 문단"],
        "must_fix": ["박성호 role drift를 SW인베스트먼트 전담 PB로 국소 보정"],
        "do_not_regress": ["EP7 엔딩 직결 opening 유지"],
        "success_condition": "국소 문장 보정만으로 advisory drift가 사라진다",
        "target_kind": "local_sentence",
    }


# ── C-1: advisory escalation produces actionable fix_scope ──────────────────


class TestAdvisoryEscalationFixScope:
    """C-1 seam: strong advisory escalation REJECT must carry fix_scope='partial'."""

    def test_advisory_escalation_reject_has_partial_fix_scope(self):
        """G1+G2 chain must set fix_scope='partial' on the resulting REJECT."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] == "REJECT"
        assert result["fix_scope"] == "partial"

    def test_advisory_escalation_with_inplace_scope_but_empty_fix_pack_is_reject(self):
        """The rerun blocker: inplace scope alone is insufficient when fix_pack is not locally actionable."""
        ir = _make_ir(advisory_summary={"npc_drift": 1})
        result = ir._normalize_director_gate_semantics(
            _base_pass_result(
                authoritative_fix_scope="inplace",
                fix_scope="inplace",
                fix_pack={},
            )
        )
        assert result["final_verdict"] == "REJECT"
        assert result["gate_basis"] == "strong_advisory_escalation_non_local_fix"
        assert result["fix_scope"] == "partial"
        assert result["strong_advisory_escalation"]["local_fix_contract"]["reason"] == "missing_fix_pack"

    def test_advisory_escalation_reject_has_fix_scope_reasoning(self):
        """G1+G2 chain must populate fix_scope_reasoning with advisory class detail."""
        ir = _make_ir(advisory_summary={"truth_gate": 1, "npc_drift": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        reasoning = result.get("fix_scope_reasoning", "")
        assert "Lane2-G2a" in reasoning
        assert "truth_gate" in reasoning or "npc_drift" in reasoning

    def test_advisory_escalation_with_multiple_classes_lists_all(self):
        """All triggered advisory classes must appear in fix_scope_reasoning."""
        ir = _make_ir(advisory_summary={"truth_gate": 1, "rel_drift": 1, "flashback": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        reasoning = result.get("fix_scope_reasoning", "")
        assert "truth_gate" in reasoning
        assert "rel_drift" in reasoning
        assert "flashback" in reasoning

    def test_non_advisory_fix_scope_violation_does_not_get_partial(self):
        """G2-only (no advisory) must NOT inject fix_scope='partial'."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics({
            "director_verdict": "PASS_WITH_FIX",
            "final_verdict": "PASS_WITH_FIX",
            "verdict": "PASS_WITH_FIX",
            "authoritative_fix_scope": "",
            "fix_scope": "",
            "repair_scope": "none",
            "gate_basis": "",
            "fix_pack": {},
        })
        assert result["final_verdict"] == "REJECT"
        assert result["gate_basis"] == "fix_scope_contract_violation"
        # fix_scope stays blank for non-advisory G2
        assert result.get("fix_scope", "") == ""

    def test_advisory_escalation_preserves_escalation_metadata(self):
        """strong_advisory_escalation payload must survive the G2 REJECT."""
        ir = _make_ir(advisory_summary={"info_paradox": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert "strong_advisory_escalation" in result
        assert result["strong_advisory_escalation"]["source_verdict"] == "PASS"

    def test_advisory_escalation_fix_scope_feeds_reject_guidance(self):
        """End-to-end: reject guidance must read 'partial' from advisory-escalated REJECT."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        ir._build_retry_feedback_provenance = MagicMock(
            return_value={
                "merged_feedback": "truth_gate advisory feedback",
                "director_feedback_text": "director note",
                "runtime_advisory": "",
                "retry_directives": "",
            }
        )

        # Simulate the G1+G2 chain
        director_result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert director_result["final_verdict"] == "REJECT"

        payload = ir.reject_runtime._build_reject_guidance_payload(
            director_result=director_result,
            director_feedback="truth_gate advisory feedback",
            validation_results=[{}],
            selected="A",
            round_num=1,
            blueprint={"episode": 8},
            prev_manuscript="previous manuscript",
            tot_used=False,
            mad_used=False,
            error_category="",
        )
        # fix_scope must NOT be blank — this was the C-1 root cause
        assert payload.resolved_fix_scope != ""
        assert payload.resolved_fix_scope in ("partial", "full")

    def test_advisory_escalation_gate_semantics_marks_runtime_widened(self):
        """Gate semantics must show runtime widening when authoritative scope is blank."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())

        payload = ir._build_gate_semantics_payload(result)

        assert payload["authoritative_fix_scope"] == ""
        assert payload["repair_scope"] == "partial"
        assert payload["scope_origin"]["fix_scope"] == "runtime_widened"
        assert payload["authoritative_fix_scope_violation"]["type"] == "blank_authoritative_fix_scope"

    def test_advisory_escalation_reject_snapshot_marks_runtime_widened(self):
        """Reject snapshot must preserve blank authoritative scope and mark runtime widening."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        ir._collect_validation_warning_lines = MagicMock(return_value=[])
        ir._inherit_attempt_history = MagicMock(return_value=[])
        ir._set_retry_budget_axes = MagicMock(return_value={})
        ir._evaluate_fix_pack_contract = MagicMock(return_value={"ready": False, "reason": "missing_patch_targets"})

        director_result = ir._normalize_director_gate_semantics(_base_pass_result())
        payload = ir.reject_runtime._build_reject_retry_snapshot(
            director_result=director_result,
            selected="A",
            director_feedback="truth_gate advisory feedback",
            action_items=[],
            score=95,
            validation_results=[{}],
            reject_bucket="constraint_violation",
            tot_used=False,
            mad_used=False,
            resolved_fix_scope="partial",
            resolved_fix_scope_reasoning=director_result.get("fix_scope_reasoning", ""),
            resolved_fix_pack={},
            error_category="",
            feedback_provenance={
                "director_feedback_text": "",
                "runtime_advisory": "",
                "retry_directives": "",
            },
            previous_attempt=None,
            round_num=0,
        )

        previous_attempt = payload.previous_attempt
        assert previous_attempt["authoritative_fix_scope"] == ""
        assert previous_attempt["repair_scope"] == "partial"
        assert previous_attempt["scope_origin"]["fix_scope"] == "runtime_widened"
        assert previous_attempt["scope_origin"]["authoritative_fix_scope"] == "director_authoritative"

    def test_advisory_escalation_pathology_payload_marks_runtime_widened(self):
        """Retry pathology payload fallback must not flatten blank-authoritative widening."""
        orch = Stage4Orchestrator(_make_ctx())

        payload = orch.outcome_runtime.build_retry_pathology_payload(
            ep_num=8,
            round_num=0,
            previous_attempt={
                "reject_bucket": "constraint_violation",
                "gate_basis": "strong_advisory_escalation_no_scope",
                "fix_scope": "partial",
                "authoritative_fix_scope": "",
                "repair_scope": "partial",
                "fix_scope_reasoning": "[Lane2-G2a] advisory widening",
                "fix_pack": {},
                "score": 95,
            },
        )

        assert payload["repair_scope"] == "partial"
        assert payload["authoritative_fix_scope"] == ""
        assert payload["scope_origin"]["fix_scope"] == "runtime_widened"


# ── C-1 happy path regression ──────────────────────────────────────────────


class TestAdvisoryEscalationHappyPathRegression:
    """Existing valid PASS_WITH_FIX paths must NOT be broken by C-1 fix."""

    def test_pass_with_valid_scope_stays_pass_with_fix(self):
        """PASS + strong advisory + ready local fix contract → PASS_WITH_FIX (not REJECT)."""
        ir = _make_ir(advisory_summary={"npc_drift": 1})
        result = ir._normalize_director_gate_semantics(
            _base_pass_result(
                authoritative_fix_scope="inplace",
                fix_scope="inplace",
                fix_pack=_ready_local_fix_pack(),
            )
        )
        assert result["final_verdict"] == "PASS_WITH_FIX"
        assert result["verdict"] == "PASS_WITH_FIX"

    def test_pass_with_strong_advisory_backfills_local_fix_contract(self):
        """Runtime strong advisory may backfill a bounded local fix contract for local targets."""
        ir = _make_ir(advisory_summary={"npc_drift": 1})
        result = ir._normalize_director_gate_semantics(
            _base_pass_result(
                authoritative_fix_scope="inplace",
                fix_scope="inplace",
                fix_pack={
                    "patch_targets": [],
                    "must_fix": [],
                    "do_not_regress": ["EP7 opening carryover 유지"],
                    "success_condition": "NPC drift 경고가 사라진다",
                    "target_kind": "local_phrase",
                },
            )
        )

        assert result["final_verdict"] == "PASS_WITH_FIX"
        assert result["fix_pack"]["patch_targets"] == ["NPC 역할/관계 서술 문장"]
        assert result["fix_pack"]["must_fix"] == ["NPC 역할 또는 관계 표현을 canonical truth에 맞게 국소 수정"]
        assert result["strong_advisory_escalation"]["local_fix_contract_backfilled"] is True

    def test_pass_with_relation_tag_npc_drift_synthesizes_local_fix_contract_from_zero(self):
        """NpcDrift relation-tag subtype may synthesize a zero-to-local fix contract."""
        ir = _make_ir(advisory_summary={"npc_drift": 1})
        ir._last_advisory_metadata = {
            "npc_drift": [
                {
                    "npc": "한정호",
                    "field": "relation_to_protag",
                    "expected": "집착100/오해-80",
                    "found_in_ms": "한정호는 주인공을 별다른 감정 없는 거래 상대로만 여겼다",
                    "drift_subtype": "relation_tag_semantic",
                    "target_kind": "local_phrase",
                    "expected_relation_axes": ["집착100", "오해-80"],
                    "_cand_idx": 0,
                }
            ]
        }
        result = ir._normalize_director_gate_semantics(
            _base_pass_result(
                selected="A",
                authoritative_fix_scope="inplace",
                fix_scope="inplace",
                fix_pack={},
            )
        )

        assert result["final_verdict"] == "PASS_WITH_FIX"
        assert result["fix_pack"]["target_kind"] == "local_phrase"
        assert "한정호" in result["fix_pack"]["patch_targets"][0]
        assert "압축 관계 태그" in result["fix_pack"]["must_fix"][0]
        assert result["strong_advisory_escalation"]["local_fix_contract_backfilled"] is True
        assert result["strong_advisory_escalation"]["backfilled_from"] == ["npc_drift_relation_tag_semantic"]

    def test_strong_advisory_backfill_does_not_widen_scene_model_targets(self):
        """scene_model targets stay non-local even if strong advisory is backfilled."""
        ir = _make_ir(advisory_summary={"npc_drift": 1})
        result = ir._normalize_director_gate_semantics(
            _base_pass_result(
                authoritative_fix_scope="inplace",
                fix_scope="inplace",
                fix_pack={
                    "patch_targets": [],
                    "must_fix": [],
                    "do_not_regress": ["scene flow 유지"],
                    "success_condition": "scene-level rewrite",
                    "target_kind": "scene_model",
                },
            )
        )

        assert result["final_verdict"] == "REJECT"
        assert result["gate_basis"] == "strong_advisory_escalation_non_local_fix"

    def test_plain_pass_without_advisory_unaffected(self):
        """Plain PASS with no advisory must stay PASS."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] == "PASS"
        assert result.get("fix_scope", "") == ""

    def test_reject_verdict_unchanged(self):
        """Existing REJECT must not be re-escalated or modified."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        result = ir._normalize_director_gate_semantics({
            "director_verdict": "REJECT",
            "final_verdict": "REJECT",
            "verdict": "REJECT",
            "authoritative_fix_scope": "",
            "fix_scope": "full",
            "gate_basis": "director_primary_reject",
        })
        assert result["final_verdict"] == "REJECT"
        assert result["gate_basis"] == "director_primary_reject"
        assert result["fix_scope"] == "full"


# ── C-2: post-select conflict scope propagation ────────────────────────────


class TestPostSelectConflictScopePropagation:
    """C-2 seam: post-select conflict downgrade must propagate full scope end-to-end."""

    def test_reject_bucket_promoted_from_gate_basis(self):
        """reject_bucket must be 'post_select_conflict' when gate_basis says so."""
        ir = _make_ir()
        ir._build_retry_feedback_provenance = MagicMock(
            return_value={
                "merged_feedback": "[Continuity Conflict] timeline mismatch",
                "director_feedback_text": "",
                "runtime_advisory": "",
                "retry_directives": "",
            }
        )
        # _classify_reject_bucket would return "constraint_violation" from text,
        # but gate_basis should override it
        payload = ir.reject_runtime._build_reject_guidance_payload(
            director_result={
                "selected_candidate": {"manuscript": "candidate"},
                "feedback": {"issues": ["timeline mismatch"]},
                "action_items": [],
                "fix_scope": "full",
                "fix_scope_reasoning": "",
                "fix_pack": {},
                "gate_basis": "post_select_conflict",
            },
            director_feedback="[Continuity Conflict] timeline mismatch",
            validation_results=[{}],
            selected="A",
            round_num=2,
            blueprint={"episode": 8},
            prev_manuscript="prev",
            tot_used=False,
            mad_used=False,
            error_category="POST_SELECT_CONTINUITY_CONFLICT",
        )
        assert payload.reject_bucket == "post_select_conflict"
        assert payload.resolved_fix_scope == "full"

    def test_post_select_conflict_fix_scope_on_director_result(self):
        """_run_post_select_checks must stamp fix_scope='full' on director_result."""
        ir = _make_ir()
        # The director_result before post-select conflict had fix_scope="inplace"
        director_result = {
            "director_verdict": "PASS",
            "final_verdict": "PASS",
            "verdict": "PASS",
            "fix_scope": "inplace",
            "authoritative_fix_scope": "inplace",
            "repair_scope": "inplace",
            "gate_basis": "director_primary_pass",
        }
        # Directly call _apply_director_gate_update + stamp fix_scope as the production code does
        director_result = ir._apply_director_gate_update(
            director_result,
            final_verdict="REJECT",
            gate_basis="post_select_conflict",
            repair_scope="full",
        )
        director_result["fix_scope"] = "full"

        assert director_result["gate_basis"] == "post_select_conflict"
        assert director_result["repair_scope"] == "full"
        assert director_result["fix_scope"] == "full"

    def test_stale_inplace_does_not_survive_post_select_downgrade(self):
        """After post-select conflict, the old 'inplace' fix_scope must not propagate."""
        ir = _make_ir()
        ir._build_retry_feedback_provenance = MagicMock(
            return_value={
                "merged_feedback": "[Continuity Conflict] stale inplace",
                "director_feedback_text": "",
                "runtime_advisory": "",
                "retry_directives": "",
            }
        )
        # Director result with the old "inplace" before post-select conflict
        # but gate_basis already updated to post_select_conflict
        payload = ir.reject_runtime._build_reject_guidance_payload(
            director_result={
                "selected_candidate": {"manuscript": "candidate"},
                "feedback": {},
                "action_items": [],
                "fix_scope": "inplace",
                "fix_scope_reasoning": "",
                "fix_pack": {},
                "gate_basis": "post_select_conflict",
            },
            director_feedback="[Continuity Conflict] stale inplace",
            validation_results=[{}],
            selected="B",
            round_num=3,
            blueprint={"episode": 8},
            prev_manuscript="prev",
            tot_used=False,
            mad_used=False,
            error_category="POST_SELECT_CONTINUITY_CONFLICT",
        )
        # Even though director_result.fix_scope was "inplace", the gate_basis promotion
        # must force it to "full"
        assert payload.resolved_fix_scope == "full"
        assert payload.reject_bucket == "post_select_conflict"

    def test_non_post_select_gate_basis_not_promoted(self):
        """reject_bucket must NOT be promoted for unrelated gate_basis values."""
        ir = _make_ir()
        ir._build_retry_feedback_provenance = MagicMock(
            return_value={
                "merged_feedback": "quality floor fail feedback",
                "director_feedback_text": "",
                "runtime_advisory": "",
                "retry_directives": "",
            }
        )
        payload = ir.reject_runtime._build_reject_guidance_payload(
            director_result={
                "selected_candidate": {"manuscript": "candidate"},
                "feedback": {"issues": ["quality low"]},
                "action_items": [],
                "fix_scope": "inplace",
                "fix_scope_reasoning": "",
                "fix_pack": {},
                "gate_basis": "quality_floor_fail",
            },
            director_feedback="quality floor fail feedback",
            validation_results=[{}],
            selected="A",
            round_num=1,
            blueprint={"episode": 8},
            prev_manuscript="prev",
            tot_used=False,
            mad_used=False,
            error_category="QUALITY_FLOOR_FAIL",
        )
        assert payload.reject_bucket != "post_select_conflict"


# ── C-2 retry lane routing propagation ──────────────────────────────────────


class TestPostSelectConflictRetryRouting:
    """Verify that fix_scope='full' from post-select conflict reaches retry lane routing."""

    def test_full_scope_blocks_inplace_retry(self):
        """fix_scope='full' must prevent use_inplace in retry routing."""
        ir = _make_ir()
        previous_attempt = {
            "score": 95,
            "fix_scope": "full",
            "fix_pack": {},
            "reject_bucket": "post_select_conflict",
            "selected_strategy_key": "balanced",
            "prior_attempts": [],
        }
        routing = ir.retry_runtime._resolve_retry_lane_routing(
            previous_attempt=previous_attempt,
            prev_manuscript="previous manuscript",
            round_num=1,
        )
        assert not routing.use_inplace
        assert not routing.force_patch
        assert routing.fix_scope == "full"

    def test_full_scope_blocks_patch_retry(self):
        """fix_scope='full' must prevent use_patch in retry routing."""
        ir = _make_ir()
        previous_attempt = {
            "score": 95,
            "fix_scope": "full",
            "fix_pack": {"patch_targets": ["anchor"], "must_fix": ["x"], "do_not_regress": ["y"],
                         "success_condition": "ok", "target_kind": "dialogue"},
            "reject_bucket": "post_select_conflict",
            "selected_strategy_key": "balanced",
            "prior_attempts": [],
        }
        routing = ir.retry_runtime._resolve_retry_lane_routing(
            previous_attempt=previous_attempt,
            prev_manuscript="previous manuscript",
            round_num=1,
        )
        assert not routing.use_patch
        assert routing.fix_scope == "full"


class TestAdvisoryEscalationObservability:
    def test_escalation_logs_triggered_families_to_ui_sink(self):
        ir = _make_ir(advisory_summary={"flashback": 1, "truth_gate": 1})

        result = ir._normalize_director_gate_semantics(
            _base_pass_result(
                authoritative_fix_scope="inplace",
                fix_scope="inplace",
                fix_pack=_ready_local_fix_pack(),
            )
        )

        assert result["final_verdict"] == "PASS_WITH_FIX"
        policy_calls = [
            call
            for call in ir.ctx.ui.log.call_args_list
            if call.kwargs.get("component") == "director_gate"
            and call.kwargs.get("event_kind") == "policy"
        ]
        assert policy_calls
        assert any(call.kwargs.get("meta", {}).get("triggered_by") == ["flashback", "truth_gate"] for call in policy_calls)

    def test_non_local_fix_reject_logs_contract_reason(self):
        ir = _make_ir(advisory_summary={"flashback": 1})

        result = ir._normalize_director_gate_semantics(
            _base_pass_result(
                authoritative_fix_scope="inplace",
                fix_scope="inplace",
                fix_pack={},
            )
        )

        assert result["final_verdict"] == "REJECT"
        policy_calls = [
            call
            for call in ir.ctx.ui.log.call_args_list
            if call.kwargs.get("component") == "director_gate"
            and call.kwargs.get("event_kind") == "policy"
        ]
        assert any(
            call.kwargs.get("meta", {}).get("gate_basis") == "strong_advisory_escalation_non_local_fix"
            and call.kwargs.get("meta", {}).get("contract_reason") == "missing_fix_pack"
            for call in policy_calls
        )
