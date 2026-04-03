from unittest.mock import MagicMock, mock_open, patch

from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.domain.agents.chief_writer_context import ChiefWriterContextBuilder
from modules.domain.agents.chief_writer_prompts import build_chief_writer_main_prompt


def _make_ctx():
    ctx = MagicMock()
    ctx.agents = {}
    ctx.current_project = MagicMock()
    ctx.current_project.db = MagicMock()
    ctx.current_project.name = "proj"
    return ctx


def _make_host():
    host = MagicMock()
    host._escape_braces = lambda x: str(x).replace("{", "{{").replace("}", "}}")
    host.context = MagicMock()
    host.context.db = MagicMock()
    host.context.master_bible = {}
    host.context.fact_ledger = None
    host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}
    return host


def test_build_gate_semantics_payload_includes_verdict_layers_for_downstream_override():
    ir = Stage4InterviewRound(_make_ctx())

    payload = ir._build_gate_semantics_payload(
        {
            "director_verdict": "PASS",
            "final_verdict": "REJECT",
            "verdict": "REJECT",
            "gate_basis": "strong_advisory_escalation_non_local_fix",
            "repair_scope": "partial",
            "authoritative_fix_scope": "partial",
            "fix_scope": "partial",
        }
    )

    assert payload["verdict_layers"] == {
        "director_quality_passed": True,
        "downstream_override_applied": True,
        "primary_failure_layer": "downstream_gate",
    }


def test_build_stage4_db_attempt_payload_surfaces_query_friendly_override_fields():
    ir = Stage4InterviewRound(_make_ctx())

    payload = ir._build_stage4_db_attempt_payload(
        episode=10,
        round_num=0,
        success=False,
        score=96,
        arc=1,
        verdict="REJECT",
        reject_reason="gate reject",
        fix_scope="partial",
        model="writer-model",
        duration_ms=1200,
        advisory_flags={
            "gate_semantics": {
                "director_verdict": "PASS",
                "final_verdict": "REJECT",
                "gate_basis": "strong_advisory_escalation_non_local_fix",
                "verdict_layers": {
                    "director_quality_passed": True,
                    "downstream_override_applied": True,
                    "primary_failure_layer": "downstream_gate",
                },
            }
        },
        session_id="sess-1",
        attempt_key="attempt-1",
        artifact_meta={"candidate_key": "A", "content_hash": "hash", "artifact_path": "artifact.txt"},
        selection_reason="best",
        verdict_reason="runtime gate",
        open_review="",
        fix_scope_reasoning="",
        runtime_advisory="",
        retry_directives="",
    )

    assert payload["director_quality_passed"] is True
    assert payload["downstream_override_applied"] is True
    assert payload["primary_failure_layer"] == "downstream_gate"


def test_stage4_db_attempt_payload_roundtrips_into_stage_attempts_sink(tmp_path):
    from modules.core.db_manager import DBManager

    ir = Stage4InterviewRound(_make_ctx())
    payload = ir._build_stage4_db_attempt_payload(
        episode=10,
        round_num=0,
        success=False,
        score=96,
        arc=1,
        verdict="REJECT",
        reject_reason="gate reject",
        fix_scope="partial",
        model="writer-model",
        duration_ms=1200,
        advisory_flags={
            "gate_semantics": {
                "director_verdict": "PASS",
                "final_verdict": "REJECT",
                "gate_basis": "strong_advisory_escalation_non_local_fix",
                "verdict_layers": {
                    "director_quality_passed": True,
                    "downstream_override_applied": True,
                    "primary_failure_layer": "downstream_gate",
                },
            }
        },
        session_id="sess-1",
        attempt_key="attempt-1",
        artifact_meta={"candidate_key": "A", "content_hash": "hash", "artifact_path": "artifact.txt"},
        selection_reason="best",
        verdict_reason="runtime gate",
        open_review="",
        fix_scope_reasoning="",
        runtime_advisory="",
        retry_directives="",
    )

    db = DBManager(tmp_path / "stage4_payload_roundtrip.db")
    try:
        assert db.save_stage_attempt(**payload) is True
        row = db.conn.execute(
            """
            SELECT director_quality_passed, downstream_override_applied, primary_failure_layer
            FROM stage_attempts
            WHERE attempt_key = 'attempt-1'
            """
        ).fetchone()
    finally:
        db.close()

    assert row is not None
    assert row["director_quality_passed"] == 1
    assert row["downstream_override_applied"] == 1
    assert row["primary_failure_layer"] == "downstream_gate"


def test_append_episode_log_persists_verdict_layers():
    ir = Stage4InterviewRound(_make_ctx())
    ir._round_start_ts = 0.0
    ir._get_round_metrics_delta = MagicMock(
        return_value={
            "total_calls": 1,
            "total_tokens": 100,
            "total_cost_usd": 0.01,
            "model_breakdown": {"writer-model": {"tokens": 100, "cost": 0.01}},
        }
    )

    with patch("builtins.open", mock_open()) as mocked_open, patch("os.makedirs"), patch(
        "time.monotonic", return_value=1.0
    ):
        ir._append_episode_log(
            ep_num=10,
            round_num=0,
            director_result={
                "verdict": "REJECT",
                "director_verdict": "PASS",
                "final_verdict": "REJECT",
                "gate_basis": "strong_advisory_escalation_non_local_fix",
                "repair_scope": "partial",
                "authoritative_fix_scope": "partial",
                "fix_scope": "partial",
                "score": 96,
                "selected": "A",
                "selection_reason": "best candidate",
                "selected_candidate": {"strategy_name": "balanced"},
                "score_breakdown": {},
                "action_items": [],
                "open_review": "",
            },
            initial_verdict="PASS",
            final_verdict="REJECT",
            initial_score=96,
            final_score=96,
            is_patch=False,
            patch_fallback=False,
            tot_used=False,
            mad_used=False,
            asp_used=False,
            model="writer-model",
            reject_bucket="downstream_gate",
            validation_warnings=[],
        )

    written = "".join(call.args[0] for call in mocked_open().write.call_args_list)
    assert '"downstream_override_applied": true' in written
    assert '"primary_failure_layer": "downstream_gate"' in written


def test_main_prompt_has_early_authority_preface():
    prompt = build_chief_writer_main_prompt(
        ep_num=5,
        dna_instruction="dna",
        purism_section="purism",
        world_origin_constraint_section="origin",
        feedback_section="feedback",
        constraint_section="constraint",
        future_guard_section="future",
        past_guard_section="past",
        writer_core_section="writer-core",
        hud_anomaly_section="hud-anomaly",
        scene_breakdown="scene-breakdown",
        prev_digest="PREV-DIGEST",
        prev_ending="PREV-ENDING",
        hud_report="HUD",
        high_density_hud_section="hd-hud",
        hud_trend_section="hud-trend",
        npc_equipment_section="npc-equip",
        npc_frequency_section="npc-freq",
        arc_doc="arc",
        core_identity_desire="desire",
        style_guide="style",
        common_rules="common-rules",
        writing_guidelines="guidelines",
        chain_link_section="CHAIN-LINK",
        prev_manuscripts_section="PREV-FULL-TEXT",
        carryover_ceiling_section="CARRYOVER-CEILING",
    )

    assert "Read This Authority First" in prompt
    assert "prior manuscript full-text" in prompt
    assert "chain_link" in prompt
    assert prompt.index("Read This Authority First") < prompt.index("feedback")


def test_main_prompt_strengthens_writer_identity_and_prefers_split_writer_sections():
    prompt = build_chief_writer_main_prompt(
        ep_num=5,
        dna_instruction="dna",
        purism_section="purism",
        world_origin_constraint_section="origin",
        feedback_section="feedback",
        constraint_section="constraint",
        future_guard_section="future",
        past_guard_section="past",
        writer_core_section="legacy-writer-core",
        hud_anomaly_section="hud-anomaly",
        scene_breakdown="scene-breakdown",
        prev_digest="PREV-DIGEST",
        prev_ending="PREV-ENDING",
        hud_report="HUD",
        high_density_hud_section="hd-hud",
        hud_trend_section="hud-trend",
        npc_equipment_section="npc-equip",
        npc_frequency_section="npc-freq",
        arc_doc="arc",
        core_identity_desire="desire",
        style_guide="style",
        common_rules="common-rules",
        writing_guidelines="guidelines",
        writer_hard_canon_section="HARD-CANON",
        writer_soft_guidance_section="SOFT-GUIDANCE",
    )

    assert "너는 분석가, 요약가, 브리핑 엔진" in prompt
    assert prompt.index("HARD-CANON") < prompt.index("SOFT-GUIDANCE")
    assert prompt.index("SOFT-GUIDANCE") < prompt.index("scene-breakdown")
    assert "legacy-writer-core" not in prompt


def test_carryover_ceiling_uses_prev_digest_fallback_when_specific_hits_are_sparse():
    builder = ChiefWriterContextBuilder(_make_host())
    section = builder.context_packets._build_stage4_carryover_ceiling_section(
        blueprint={"scene_breakdown": {"scene_1": {"goal": "keep moving"}}},
        prev_manuscript="plain transition without matched keywords",
        prev_digest="- generic authority line one\n- generic authority line two",
    )

    assert "prior digest authority reminders" in section
    assert "generic authority line one" in section
    assert "generic authority line two" in section
