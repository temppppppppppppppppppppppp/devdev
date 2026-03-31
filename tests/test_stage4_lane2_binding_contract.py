"""Lane 2 regression tests: stage4-binding-and-fix-scope-contract-hardening.

Covers two contracts added to _normalize_director_gate_semantics:

  [Lane2-G1] Strong advisory classes (tier-2+) must not end as plain PASS.
             TruthGate/NpcDrift/RelDrift/Flashback/InfoParadox trigger escalation.

  [Lane2-G2] PASS_WITH_FIX with blank/invalid authoritative_fix_scope cannot run
             the repair loop. The verdict is gated to REJECT.

Happy-path regression:
  - PASS with no strong advisory stays PASS.
  - PASS_WITH_FIX with a valid fix_scope stays PASS_WITH_FIX.
"""

from unittest.mock import MagicMock

from modules.core.stage4_interview_round import Stage4InterviewRound

# ── helpers ──────────────────────────────────────────────────────────────────

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


def _base_pwf_result(**overrides) -> dict:
    base = {
        "director_verdict": "PASS_WITH_FIX",
        "final_verdict": "PASS_WITH_FIX",
        "verdict": "PASS_WITH_FIX",
        "authoritative_fix_scope": "partial",
        "fix_scope": "partial",
        "repair_scope": "partial",
        "gate_basis": "",
        "fix_pack": {},
    }
    base.update(overrides)
    return base


def _ready_local_fix_pack() -> dict:
    return {
        "patch_targets": ["씬 2 첫 통화 문장"],
        "must_fix": ["박성호의 소속 호칭을 SW인베스트먼트 전담 PB로 바로잡을 것"],
        "do_not_regress": ["EP7 엔딩 연속성 유지"],
        "success_condition": "국소 문장 보정 후 NPC role drift가 사라진다",
        "target_kind": "local_sentence",
    }


# ── [Lane2-G1] plain PASS escalation ──────────────────────────────────────────

class TestStrongAdvisoryEscalation:
    def test_pass_with_no_advisory_stays_pass(self):
        """Regression: plain PASS with no advisory must not be touched."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] == "PASS"
        assert result["verdict"] == "PASS"
        assert "strong_advisory_escalation" not in result

    def test_pass_with_weak_advisory_only_stays_pass(self):
        """Regression: tier-1 advisories (numeric_drift, long_term_rep) must not escalate PASS."""
        ir = _make_ir(advisory_summary={"numeric_drift": 1, "long_term_rep": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] == "PASS"
        assert "strong_advisory_escalation" not in result

    def test_pass_with_truth_gate_advisory_is_escalated(self):
        """PASS + TruthGate (tier 3) → not plain PASS."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] != "PASS", "plain PASS must not survive TruthGate advisory"

    def test_pass_with_npc_drift_advisory_is_escalated(self):
        """PASS + NpcDrift (tier 2) → not plain PASS."""
        ir = _make_ir(advisory_summary={"npc_drift": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] != "PASS"

    def test_pass_with_rel_drift_advisory_is_escalated(self):
        """PASS + RelDrift (tier 2) → not plain PASS."""
        ir = _make_ir(advisory_summary={"rel_drift": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] != "PASS"

    def test_pass_with_flashback_advisory_is_escalated(self):
        """PASS + Flashback (tier 2) → not plain PASS."""
        ir = _make_ir(advisory_summary={"flashback": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] != "PASS"

    def test_pass_with_info_paradox_advisory_is_escalated(self):
        """PASS + InfoParadox (tier 2) → not plain PASS."""
        ir = _make_ir(advisory_summary={"info_paradox": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] != "PASS"

    def test_escalation_sets_strong_advisory_escalation_metadata(self):
        """Escalated result must carry strong_advisory_escalation payload for operator visibility."""
        ir = _make_ir(advisory_summary={"truth_gate": 1, "npc_drift": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert "strong_advisory_escalation" in result
        payload = result["strong_advisory_escalation"]
        assert payload["source_verdict"] == "PASS"
        assert payload["escalated_to"] == "PASS_WITH_FIX"
        assert "truth_gate" in payload["triggered_by"]
        assert "npc_drift" in payload["triggered_by"]

    def test_escalation_does_not_happen_when_verdict_is_already_reject(self):
        """REJECT verdict with strong advisory must not be further mutated by G1."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        result = ir._normalize_director_gate_semantics(
            _base_pass_result(
                director_verdict="REJECT",
                final_verdict="REJECT",
                verdict="REJECT",
                gate_basis="quality_floor_fail",
            )
        )
        assert result["final_verdict"] == "REJECT"
        # gate_basis should not be overwritten by escalation
        assert result["gate_basis"] == "quality_floor_fail"
        assert "strong_advisory_escalation" not in result

    def test_escalation_does_not_happen_when_no_advisory_summary_set(self):
        """When _last_advisory_summary is empty dict (round reset), PASS stays PASS."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert result["final_verdict"] == "PASS"


# ── [Lane2-G2] PASS_WITH_FIX fix_scope contract gate ──────────────────────────

class TestFixScopeContractGate:
    def test_pwf_with_valid_fix_scope_partial_stays_pwf(self):
        """Regression: PASS_WITH_FIX + authoritative_fix_scope=partial must NOT be downgraded."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(_base_pwf_result(authoritative_fix_scope="partial"))
        assert result["final_verdict"] == "PASS_WITH_FIX"
        assert result["verdict"] == "PASS_WITH_FIX"

    def test_pwf_with_valid_fix_scope_full_stays_pwf(self):
        """Regression: PASS_WITH_FIX + authoritative_fix_scope=full must NOT be downgraded."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(_base_pwf_result(authoritative_fix_scope="full"))
        assert result["final_verdict"] == "PASS_WITH_FIX"

    def test_pwf_with_valid_fix_scope_inplace_stays_pwf(self):
        """Regression: PASS_WITH_FIX + authoritative_fix_scope=inplace must NOT be downgraded."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(_base_pwf_result(authoritative_fix_scope="inplace"))
        assert result["final_verdict"] == "PASS_WITH_FIX"

    def test_pwf_with_blank_fix_scope_is_gated_to_reject(self):
        """PASS_WITH_FIX + blank authoritative_fix_scope → REJECT (repair loop blocked)."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(
            _base_pwf_result(authoritative_fix_scope="", fix_scope="")
        )
        assert result["final_verdict"] == "REJECT"
        assert result["verdict"] == "REJECT"

    def test_pwf_with_invalid_fix_scope_is_gated_to_reject(self):
        """PASS_WITH_FIX + invalid authoritative_fix_scope (e.g. 'unknown') → REJECT."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(
            _base_pwf_result(authoritative_fix_scope="unknown", fix_scope="unknown")
        )
        assert result["final_verdict"] == "REJECT"

    def test_pwf_blank_fix_scope_gate_basis_is_fix_scope_contract_violation(self):
        """When G2 fires without G1, gate_basis must be 'fix_scope_contract_violation'."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(
            _base_pwf_result(authoritative_fix_scope="")
        )
        assert result["gate_basis"] == "fix_scope_contract_violation"

    def test_pwf_blank_fix_scope_carries_violation_metadata(self):
        """G2 must set authoritative_fix_scope_violation payload."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics(
            _base_pwf_result(authoritative_fix_scope="")
        )
        assert "authoritative_fix_scope_violation" in result
        assert result["authoritative_fix_scope_violation"]["type"] == "blank_authoritative_fix_scope"

    def test_reject_verdict_with_blank_fix_scope_stays_reject_not_escalated(self):
        """REJECT + blank fix_scope: violation is noted but verdict stays REJECT (G2 does not fire for REJECT)."""
        ir = _make_ir(advisory_summary={})
        result = ir._normalize_director_gate_semantics({
            "director_verdict": "REJECT",
            "final_verdict": "REJECT",
            "verdict": "REJECT",
            "authoritative_fix_scope": "",
            "gate_basis": "director_primary_reject",
        })
        assert result["final_verdict"] == "REJECT"
        assert result["gate_basis"] == "director_primary_reject"


# ── Chain: G1 → G2 ────────────────────────────────────────────────────────────

class TestStrongAdvisoryChainToReject:
    def test_pass_with_strong_advisory_and_blank_fix_scope_ends_as_reject(self):
        """G1 escalates PASS → PASS_WITH_FIX; G2 then gates PASS_WITH_FIX → REJECT (no scope)."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result(authoritative_fix_scope=""))
        assert result["final_verdict"] == "REJECT"
        assert result["verdict"] == "REJECT"

    def test_chained_gate_basis_is_strong_advisory_escalation_no_scope(self):
        """Chain G1+G2: gate_basis must be 'strong_advisory_escalation_no_scope'."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result(authoritative_fix_scope=""))
        assert result["gate_basis"] == "strong_advisory_escalation_no_scope"

    def test_chained_result_carries_escalation_metadata(self):
        """Chain G1+G2: strong_advisory_escalation payload must still be present for audit trail."""
        ir = _make_ir(advisory_summary={"info_paradox": 1})
        result = ir._normalize_director_gate_semantics(_base_pass_result())
        assert "strong_advisory_escalation" in result
        assert result["strong_advisory_escalation"]["source_verdict"] == "PASS"

    def test_pass_with_strong_advisory_and_valid_fix_scope_is_pwf_not_reject(self):
        """Strong advisory may stay PASS_WITH_FIX only when a ready local fix contract exists."""
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

    def test_pass_with_strong_advisory_and_partial_scope_is_reject(self):
        """Non-local scope must not survive as PASS_WITH_FIX under strong advisory escalation."""
        ir = _make_ir(advisory_summary={"npc_drift": 1})
        result = ir._normalize_director_gate_semantics(
            _base_pass_result(
                authoritative_fix_scope="partial",
                fix_scope="partial",
            )
        )
        assert result["final_verdict"] == "REJECT"
        assert result["gate_basis"] == "strong_advisory_escalation_non_local_fix"
        assert result["fix_scope"] == "partial"

    def test_pass_with_strong_advisory_and_empty_local_fix_pack_is_reject(self):
        """Inplace scope without a ready fix_pack must fail closed before PASS_WITH_FIX loop entry."""
        ir = _make_ir(advisory_summary={"flashback": 1})
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

    def test_idempotent_second_call_does_not_re_escalate(self):
        """Calling _normalize_director_gate_semantics twice on the same result is idempotent."""
        ir = _make_ir(advisory_summary={"truth_gate": 1})
        first = ir._normalize_director_gate_semantics(_base_pass_result())
        first_verdict = first["final_verdict"]
        second = ir._normalize_director_gate_semantics(first)
        assert second["final_verdict"] == first_verdict
