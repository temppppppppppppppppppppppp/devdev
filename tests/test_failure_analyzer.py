"""FailureAnalyzer success-pattern and quality-distribution tests."""

import hashlib
import json

from modules.core.db_manager import DBManager
from modules.core.failure_analyzer import FailureAnalyzer
from modules.core.stage4_raw_evidence import summarize_stage4_raw_rationale_rows


def test_failure_analyzer_quality_distribution_and_success_patterns(tmp_path):
    db = DBManager(tmp_path / "test.db")
    try:
        db.save_episode_quality_label(
            10,
            {
                "score": 95,
                "verdict": "PASS",
                "selection_reason": "몰입감과 연속성이 좋음",
                "open_review": "특이사항 없음",
                "score_breakdown": {
                    "continuity_contradiction": 39,
                    "blueprint_coverage": 19,
                    "quality_engagement": 19,
                },
                "consistency_checklist": {
                    "scene_variety": "OK",
                    "pacing_quality": "OK",
                    "dialogue_naturalness": "OK",
                },
            },
        )
        db.save_episode_quality_label(
            11,
            {
                "score": 92,
                "verdict": "PASS_WITH_FIX",
                "selection_reason": "연속성과 대화가 안정적",
                "open_review": "후반만 조금 보강",
                "score_breakdown": {
                    "continuity_contradiction": 38,
                    "blueprint_coverage": 18,
                    "quality_engagement": 18,
                },
                "consistency_checklist": {
                    "scene_variety": "OK",
                    "pacing_quality": "OK",
                    "dialogue_naturalness": "OK",
                },
            },
        )

        analyzer = FailureAnalyzer(db)
        distribution = analyzer.quality_distribution()
        patterns = analyzer.top_success_patterns(top_n=3)

        assert distribution["count"] == 2
        assert distribution["high_score_count"] == 2
        assert distribution["pass_with_fix_count"] == 1
        assert any("평균" in item["description"] for item in patterns)
        assert any("OK 비율 높음" in item["description"] for item in patterns)
    finally:
        db.close()


def test_failure_analyzer_compare_versions(tmp_path):
    db = DBManager(tmp_path / "test_compare_versions.db")
    try:
        db.save_stage_attempt(stage=4, verdict="PASS", ep_num=10, arc_num=3, score=91, prompt_version="chief@v1")
        db.save_stage_attempt(stage=4, verdict="REJECT", ep_num=11, arc_num=3, score=74, prompt_version="chief@v1")
        db.save_stage_attempt(stage=4, verdict="PASS", ep_num=12, arc_num=4, score=95, prompt_version="chief@v2")
        db.save_stage_attempt(
            stage=4, verdict="PASS_WITH_FIX", ep_num=13, arc_num=4, score=89, prompt_version="chief@v2"
        )

        analyzer = FailureAnalyzer(db)
        result = analyzer.compare_versions("chief@v1", "chief@v2", stage=4)

        assert result["versions"]["chief@v1"]["attempts"] == 2
        assert result["versions"]["chief@v1"]["pass_rate_pct"] == 50.0
        assert result["versions"]["chief@v2"]["pass_rate_pct"] == 50.0
        assert result["avg_score_delta"] == 9.5
        assert result["winner"] == "chief@v2"
    finally:
        db.close()


def test_failure_analyzer_stage_pass_rates_treats_pass_with_fix_as_transient(tmp_path):
    db = DBManager(tmp_path / "test_stage_pass_rates.db")
    try:
        db.save_stage_attempt(stage=4, verdict="PASS", ep_num=10, arc_num=3, score=91, prompt_version="chief@v1")
        db.save_stage_attempt(
            stage=4, verdict="PASS_WITH_WARNING", ep_num=11, arc_num=3, score=88, prompt_version="chief@v1"
        )
        db.save_stage_attempt(
            stage=4, verdict="PASS_WITH_FIX", ep_num=12, arc_num=3, score=89, prompt_version="chief@v1"
        )
        db.save_stage_attempt(stage=4, verdict="REJECT", ep_num=13, arc_num=3, score=61, prompt_version="chief@v1")

        analyzer = FailureAnalyzer(db)
        result = analyzer.stage_pass_rates()

        assert result["stage_4"]["total_attempts"] == 4
        assert result["stage_4"]["pass"] == 2
        assert result["stage_4"]["reject"] == 1
        assert result["stage_4"]["pass_with_fix_transient"] == 1
        assert result["stage_4"]["pass_rate_pct"] == 50.0
    finally:
        db.close()


def test_failure_analyzer_numeric_consistency_summary_surfaces_persisted_nc_signals(tmp_path):
    db = DBManager(tmp_path / "test_numeric_consistency_summary.db")
    try:
        db.save_stage_attempt(
            stage=4,
            verdict="REJECT",
            ep_num=2,
            attempt_num=1,
            arc_num=1,
            session_id="sess_num",
            attempt_key="s4:ep2:arc1:a1:sess_num",
            runtime_advisory=(
                "[NC-1][후보 A][MAJOR][numeric_carryover_authority] "
                "[numeric carryover authority mismatch] 원고 '20억 원' (20.0억) vs resumed "
                "FactLedger 'capital'=2000000000.0억 (EP1 carryover baseline)."
            ),
            retry_directives=(
                "[NC-1][후보 A][MAJOR][numeric_carryover_authority] "
                "[numeric carryover authority mismatch] 원고 '20억 원' (20.0억) vs resumed "
                "FactLedger 'capital'=2000000000.0억 (EP1 carryover baseline). / "
                "- [NC-2][후보 A][MAJOR][numeric_carryover_authority] "
                "[numeric carryover authority mismatch] 원고 '20억 원' (20.0억) vs resumed "
                "FactLedger 'total_assets'=2000000000.0억 (EP1 carryover baseline)."
            ),
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            ep_num=3,
            attempt_num=1,
            arc_num=1,
            session_id="other_sess",
            attempt_key="s4:ep3:arc1:a1:other_sess",
            runtime_advisory="[NC-1][후보 B][MINOR] [first_mention_drift] something else",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.numeric_consistency_summary(stage=4, session_id="sess_num")

        assert result["status"] == "warn"
        assert result["attempt_rows_considered"] == 1
        assert result["attempts_with_signals"] == 1
        assert result["signal_count"] == 2
        assert result["category_counts"]["numeric_carryover_authority"] == 2
        assert result["ledger_field_counts"]["capital"] == 1
        assert result["ledger_field_counts"]["total_assets"] == 1
        assert result["signal_examples"][0]["attempt_key"] == "s4:ep2:arc1:a1:sess_num"
    finally:
        db.close()


def test_failure_analyzer_episode_log_fallback_prefers_final_verdict_and_score(tmp_path):
    db = DBManager(tmp_path / "test_episode_log_fallback.db")
    try:
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / "episode_production.jsonl"
        entries = [
            {
                "ep": 11,
                "verdict": "PASS_WITH_FIX",
                "score": 92,
                "initial_verdict": "PASS_WITH_FIX",
                "initial_score": 92,
                "final_verdict": "PASS",
                "final_score": 98,
                "reason": "엔딩만 보강하면 됨",
                "open_review": "엔딩 긴장감 회복",
                "score_breakdown": {"structure": 98},
                "consistency_checklist": {"timeline": "OK"},
            },
            {
                "ep": 12,
                "verdict": "PASS_WITH_FIX",
                "score": 96,
                "initial_verdict": "PASS_WITH_FIX",
                "initial_score": 96,
                "final_verdict": "REJECT",
                "final_score": 61,
                "reason": "수정 범위 확대",
                "open_review": "",
                "score_breakdown": {"structure": 61},
                "consistency_checklist": {"timeline": "WARN"},
            },
        ]
        log_path.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in entries) + "\n", encoding="utf-8"
        )

        analyzer = FailureAnalyzer(db)
        patterns = analyzer.top_success_patterns(top_n=3, min_score=95)

        assert len(patterns) >= 1
        assert all(item["count"] >= 1 for item in patterns)
    finally:
        db.close()


def test_failure_analyzer_patch_trace_summary_uses_episode_logs(tmp_path):
    db = DBManager(tmp_path / "test_patch_trace_summary.db")
    try:
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / "episode_production.jsonl"
        entries = [
            {
                "ep": 21,
                "verdict": "PASS_WITH_FIX",
                "score": 92,
                "initial_verdict": "PASS_WITH_FIX",
                "initial_score": 92,
                "final_verdict": "PASS",
                "final_score": 98,
                "fix_scope": "inplace",
                "flags": {"patch_mode": True},
                "patch_trace": {
                    "patch_strategy": "inplace_patch_structural",
                    "patch_targets": ["scene_2"],
                    "patch_target_records": [
                        {
                            "patch_target_id": "pt:scene_2",
                            "summary": "scene_2",
                            "target_kind": "scene_block",
                        }
                    ],
                    "partial_fix_eval": {
                        "patch_round": 1,
                        "is_patch_attempt": True,
                        "patch_target_id": "pt:scene_2",
                        "target_kind": "scene_block",
                        "must_fix_resolved": True,
                        "do_not_regress_held": True,
                        "success_condition_met": True,
                        "fallback_reason": "",
                    },
                    "unchanged_ratio": 0.83,
                    "fallback_reason": "",
                    "focus": "ending",
                    "structural_attempted": True,
                },
            },
            {
                "ep": 22,
                "verdict": "PASS_WITH_FIX",
                "score": 88,
                "initial_verdict": "PASS_WITH_FIX",
                "initial_score": 88,
                "final_verdict": "REJECT",
                "final_score": 61,
                "fix_scope": "partial",
                "flags": {"patch_mode": True},
                "patch_trace": {
                    "patch_strategy": "inplace_patch",
                    "patch_targets": [],
                    "patch_target_records": [
                        {
                            "patch_target_id": "pt:scene_2",
                            "summary": "scene_2",
                            "target_kind": "scene_block",
                        }
                    ],
                    "partial_fix_eval": {
                        "patch_round": 2,
                        "is_patch_attempt": True,
                        "patch_target_id": "pt:scene_2",
                        "target_kind": "scene_block",
                        "must_fix_resolved": False,
                        "do_not_regress_held": False,
                        "success_condition_met": False,
                        "fallback_reason": "global_issue",
                    },
                    "unchanged_ratio": 0.58,
                    "fallback_reason": "global_issue",
                    "focus": "global",
                    "structural_attempted": False,
                },
            },
        ]
        log_path.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in entries) + "\n", encoding="utf-8"
        )

        analyzer = FailureAnalyzer(db)
        result = analyzer.patch_trace_summary()
        summary = analyzer.summary()

        assert result["count"] == 2
        assert result["structural_attempted_count"] == 1
        assert result["final_pass"] == 1
        assert result["final_reject"] == 1
        assert result["avg_unchanged_ratio"] == 0.705
        assert result["strategy_counts"]["inplace_patch"] == 1
        assert result["strategy_counts"]["inplace_patch_structural"] == 1
        assert result["fallback_reasons"]["global_issue"] == 1
        assert result["focus_counts"]["ending"] == 1
        assert result["top_patch_targets"] == [{"target": "scene_2", "count": 2}]
        assert result["partial_fix_eval"]["local_hit_rate"] == 0.5
        assert result["partial_fix_eval"]["fallback_to_partial_or_full"] == 0.5
        assert result["partial_fix_eval"]["same_target_retry_avg"] == 2.0
        assert result["partial_fix_eval"]["same_target_retry_p95"] == 2
        assert result["partial_fix_eval"]["do_not_regress_violation_rate"] == 0.5
        assert result["partial_fix_eval"]["verifier_coverage"] == 1.0
        assert summary["patch_trace_summary"]["count"] == 2
    finally:
        db.close()


def test_failure_analyzer_load_stage_attempt_alignment_sink_dedupes_latest_row(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_stage_attempt_loader.db")
    try:
        attempt_key = "s4:ep81:arc8:a1:sess_loader"
        db.save_stage_attempt(
            stage=4,
            verdict="REJECT",
            attempt_num=1,
            ep_num=81,
            arc_num=8,
            score=61,
            session_id="sess_loader",
            attempt_key=attempt_key,
            candidate_key="old-key",
            advisory_flags={"gate_semantics": {"director_verdict": "REJECT"}},
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=2,
            ep_num=81,
            arc_num=8,
            score=97,
            session_id="sess_loader",
            attempt_key=attempt_key,
            candidate_key="new-key",
            content_hash="hash-new",
            artifact_path="logs/artifacts/stage4/ep_0081/attempt_02/final.txt",
            advisory_flags={
                "gate_semantics": {
                    "director_verdict": "PASS_WITH_FIX",
                    "gate_basis": "bounded_local_repair",
                    "repair_scope": "inplace",
                },
                "fix_pack": {"target_kind": "entity_ref", "patch_targets": ["scene_2"]},
                "retry_budget_axes": {"round": 1, "repair": 2},
            },
        )

        analyzer = FailureAnalyzer(db)
        result = analyzer._load_stage_attempt_alignment_sink(
            stage=4,
            lookback=10,
            session_id="sess_loader",
        )

        assert result is not None
        assert list(result) == [attempt_key]
        assert result[attempt_key]["final_verdict"] == "PASS"
        assert result[attempt_key]["final_score"] == 97
        assert result[attempt_key]["candidate_key"] == "new-key"
        assert result[attempt_key]["content_hash"] == "hash-new"
        assert result[attempt_key]["director_verdict"] == "PASS_WITH_FIX"
        assert result[attempt_key]["gate_basis"] == "bounded_local_repair"
        assert result[attempt_key]["repair_scope"] == "inplace"
        assert result[attempt_key]["fix_pack_target_kind"] == "entity_ref"
        assert result[attempt_key]["fix_pack_patch_targets"] == ["scene_2"]
        assert result[attempt_key]["retry_budget_axes"] == {"round": 1, "repair": 2}
    finally:
        db.close()


def test_failure_analyzer_load_stage_attempt_alignment_sink_reads_root_gate_repair_fields(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_stage_attempt_root_gate_repair.db")
    try:
        attempt_key = "s4:ep82:arc8:a1:sess_root_gate"
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=82,
            arc_num=8,
            score=94,
            session_id="sess_root_gate",
            attempt_key=attempt_key,
            advisory_flags={
                "director_verdict": "PASS_WITH_FIX",
                "gate_basis": "bounded_local_repair",
                "repair_scope": "partial",
                "repair_contract": {
                    "subtype": "movement",
                    "provenance": "runtime_synthesized",
                },
                "scope_authority": {
                    "fix_scope": "partial",
                    "repair_scope": "partial",
                    "authoritative_fix_scope": "inplace",
                    "widened": True,
                },
            },
        )

        analyzer = FailureAnalyzer(db)
        result = analyzer._load_stage_attempt_alignment_sink(
            stage=4,
            lookback=10,
            session_id="sess_root_gate",
        )

        assert result is not None
        assert result[attempt_key]["director_verdict"] == "PASS_WITH_FIX"
        assert result[attempt_key]["gate_basis"] == "bounded_local_repair"
        assert result[attempt_key]["repair_scope"] == "partial"
        assert result[attempt_key]["repair_contract_subtype"] == "movement"
        assert result[attempt_key]["repair_contract_provenance"] == "runtime_synthesized"
        assert result[attempt_key]["scope_authority_fix_scope"] == "partial"
        assert result[attempt_key]["scope_authority_authoritative_fix_scope"] == "inplace"
        assert result[attempt_key]["scope_authority_widened"] is True
    finally:
        db.close()


def test_failure_analyzer_build_sink_alignment_attempt_sets_respects_optional_sinks():
    final_union, lifecycle_union, attempts_considered = FailureAnalyzer._build_sink_alignment_attempt_sets(
        stage=4,
        include_session_decisions=False,
        stage_attempts={"a": {}},
        pass_rate_monitor={"b": {}},
        director_selections={"c": {}},
        session_decisions={"d": {}},
        episode_production={"e": {}},
    )

    assert final_union == {"a", "b", "c"}
    assert lifecycle_union == {"c", "e"}
    assert attempts_considered == {"a", "b", "c", "e"}


def test_failure_analyzer_build_sink_alignment_attempt_sets_includes_stage3_monitor_and_selection_sinks():
    final_union, lifecycle_union, attempts_considered = FailureAnalyzer._build_sink_alignment_attempt_sets(
        stage=3,
        include_session_decisions=False,
        stage_attempts={"a": {}},
        pass_rate_monitor={"b": {}},
        director_selections={"c": {}},
        session_decisions={"d": {}},
        episode_production={"e": {}},
    )

    assert final_union == {"a", "b", "c"}
    assert lifecycle_union == set()
    assert attempts_considered == {"a", "b", "c"}


def test_failure_analyzer_collect_sink_alignment_missing_buckets_tracks_final_and_lifecycle_gaps():
    final_missing, lifecycle_missing, lifecycle_missing_in_final = (
        FailureAnalyzer._collect_sink_alignment_missing_buckets(
            stage=4,
            include_session_decisions=True,
            final_union={"a", "b"},
            lifecycle_union={"b", "c"},
            stage_attempts={"a": {}},
            pass_rate_monitor={"b": {}},
            director_selections={"c": {}},
            session_decisions={"a": {}},
            episode_production={"b": {}},
        )
    )

    assert final_missing["stage_attempts"]["count"] == 1
    assert set(final_missing["stage_attempts"]["examples"]) == {"b"}
    assert final_missing["session_decisions"]["count"] == 1
    assert set(final_missing["session_decisions"]["examples"]) == {"b"}
    assert final_missing["pass_rate_monitor"]["count"] == 1
    assert set(final_missing["pass_rate_monitor"]["examples"]) == {"a"}
    assert final_missing["director_selections"]["count"] == 2
    assert set(final_missing["director_selections"]["examples"]) == {"a", "b"}
    assert lifecycle_missing == {
        "director_selections": {"count": 1, "examples": ["b"]},
        "episode_production": {"count": 1, "examples": ["c"]},
    }
    assert lifecycle_missing_in_final == {
        "stage_attempts": {"count": 2, "examples": ["b", "c"]},
    }


def test_failure_analyzer_collect_sink_alignment_missing_buckets_tracks_stage3_final_gaps():
    final_missing, lifecycle_missing, lifecycle_missing_in_final = (
        FailureAnalyzer._collect_sink_alignment_missing_buckets(
            stage=3,
            include_session_decisions=False,
            final_union={"a", "b", "c"},
            lifecycle_union=set(),
            stage_attempts={"a": {}},
            pass_rate_monitor={"b": {}},
            director_selections={"c": {}},
            session_decisions={},
            episode_production={},
        )
    )

    assert final_missing == {
        "stage_attempts": {"count": 2, "examples": ["b", "c"]},
        "pass_rate_monitor": {"count": 2, "examples": ["a", "c"]},
        "director_selections": {"count": 2, "examples": ["a", "b"]},
    }
    assert lifecycle_missing == {}
    assert lifecycle_missing_in_final == {}


def test_load_session_decision_alignment_sink_backfills_empty_rationale_from_reason(tmp_path):
    db = DBManager(tmp_path / "test_stage3_session_reason_backfill.db")
    try:
        logs_dir = tmp_path / "logs" / "session"
        logs_dir.mkdir(parents=True, exist_ok=True)
        attempt_key = "s3:ep21:arc1:a1:sess_reason_backfill"
        (logs_dir / "decisions.jsonl").write_text(
            json.dumps(
                {
                    "stage": "stage3",
                    "ep_num": 21,
                    "round_num": 0,
                    "decision_type": "blueprint",
                    "result": "PASS",
                    "score": 91,
                    "meta": {
                        "attempt_key": attempt_key,
                        "reason": "fallback rationale from reason",
                        "selection_reason": "",
                        "verdict_reason": "",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        rows, missing = analyzer._load_session_decision_alignment_sink(
            stage=3,
            lookback=10,
            include_session_decisions=True,
            session_id="sess_reason_backfill",
        )

        assert missing == 0
        assert rows[attempt_key]["selection_reason"] == "fallback rationale from reason"
        assert rows[attempt_key]["verdict_reason"] == "fallback rationale from reason"
    finally:
        db.close()


def test_stage4_raw_evidence_summary_tracks_kind_family_and_surface():
    summary = summarize_stage4_raw_rationale_rows(
        [
            {
                "payload_kind": "selection_contract_snapshot_raw",
                "payload": json.dumps(
                    {
                        "_meta": {
                            "record_family": "contract_snapshot",
                            "surface": "selection_contract_snapshot_raw",
                        },
                        "gate_semantics": {"gate_basis": "quality_floor_fail"},
                    },
                    ensure_ascii=False,
                ),
            },
            {
                "payload_kind": "feedback_provenance_raw",
                "payload": json.dumps(
                    {
                        "director_feedback": "trace verdict",
                        "runtime_advisory": "runtime digest",
                    },
                    ensure_ascii=False,
                ),
            },
        ]
    )

    assert summary["payload_kinds"] == {"selection_contract_snapshot_raw", "feedback_provenance_raw"}
    assert summary["record_families"] == {"contract_snapshot", "feedback_provenance"}
    assert summary["surfaces"] == {"selection_contract_snapshot_raw", "feedback_provenance_raw"}
    assert summary["projected_payloads"]["selection_contract_snapshot_raw"]["gate_basis"] == "quality_floor_fail"
    assert summary["projected_payloads"]["feedback_provenance_raw"]["runtime_advisory"] == "runtime digest"


def test_failure_analyzer_collect_sink_alignment_raw_rationale_results_tracks_stage4_missing_kinds():
    results = FailureAnalyzer._collect_sink_alignment_raw_rationale_results(
        stage=4,
        attempt_key="s4:ep81:arc8:a1:sess_payload",
        raw_rationale_by_attempt={
            "s4:ep81:arc8:a1:sess_payload": {
                "payload_kinds": {"selection_surface_raw", "feedback_provenance_raw"},
                "record_families": {"selection_surface", "feedback_provenance"},
            }
        },
        stage_attempts={},
        pass_rate_monitor={},
        director_selections={"s4:ep81:arc8:a1:sess_payload": {}},
        session_decisions={},
        episode_production={"s4:ep81:arc8:a1:sess_payload": {}},
    )

    assert results["raw_rationale_missing"] == []
    assert results["raw_rationale_kind_missing"] == [
        {
            "attempt_key": "s4:ep81:arc8:a1:sess_payload",
            "missing_payload_kinds": ["contract_snapshot_raw", "selection_contract_snapshot_raw"],
            "present_payload_kinds": ["feedback_provenance_raw", "selection_surface_raw"],
        }
    ]
    assert results["raw_rationale_family_missing"] == [
        {
            "attempt_key": "s4:ep81:arc8:a1:sess_payload",
            "missing_record_families": ["contract_snapshot"],
            "present_record_families": ["feedback_provenance", "selection_surface"],
        }
    ]
    assert results["raw_rationale_surface_mismatches"] == []
    assert results["raw_rationale_contract_mismatches"] == []
    assert results["raw_rationale_feedback_mismatches"] == []
    assert results["raw_rationale_patch_trace_mismatches"] == []


def test_failure_analyzer_collect_sink_alignment_raw_rationale_results_tracks_stage4_selection_surface_mismatch():
    attempt_key = "s4:ep81:arc8:a1:sess_surface"
    results = FailureAnalyzer._collect_sink_alignment_raw_rationale_results(
        stage=4,
        attempt_key=attempt_key,
        raw_rationale_by_attempt={
            attempt_key: {
                "payload_kinds": {"selection_surface_raw"},
                "record_families": {"selection_surface"},
                "decoded_payloads": {
                    "selection_surface_raw": {
                        "selected_label": "A",
                        "selected_strategy": "balanced",
                        "verdict": "PASS",
                        "score": 92,
                        "selection_reason": "raw selection",
                        "verdict_reason": "raw verdict",
                    }
                },
            }
        },
        stage_attempts={
            attempt_key: {
                "patch_strategy": "stage_attempt_rewrite",
            }
        },
        pass_rate_monitor={},
        director_selections={
            attempt_key: {
                "selected_label": "B",
                "selected_strategy": "balanced",
                "initial_verdict": "REJECT",
                "initial_score": 90,
                "selection_reason": "db selection",
                "verdict_reason": "raw verdict",
            }
        },
        session_decisions={},
        episode_production={},
    )

    assert results["raw_rationale_surface_mismatches"] == [
        {
            "attempt_key": attempt_key,
            "mismatched_fields": {
                "selected_label": {
                    "selection_surface_raw": "A",
                    "director_selections": "B",
                },
                "verdict": {
                    "selection_surface_raw": "PASS",
                    "director_selections": "REJECT",
                },
                "score": {
                    "selection_surface_raw": 92,
                    "director_selections": 90,
                },
                "selection_reason": {
                    "selection_surface_raw": "raw selection",
                    "director_selections": "db selection",
                },
            },
        }
    ]


def test_failure_analyzer_collect_sink_alignment_raw_rationale_results_tracks_stage4_contract_snapshot_mismatch():
    attempt_key = "s4:ep81:arc8:a1:sess_contract"
    results = FailureAnalyzer._collect_sink_alignment_raw_rationale_results(
        stage=4,
        attempt_key=attempt_key,
        raw_rationale_by_attempt={
            attempt_key: {
                "payload_kinds": {"selection_contract_snapshot_raw"},
                "record_families": {"contract_snapshot"},
                "decoded_payloads": {
                    "selection_contract_snapshot_raw": {
                        "gate_semantics": {
                            "director_verdict": "PASS_WITH_FIX",
                            "gate_basis": "bounded_local_repair",
                            "repair_scope": "partial",
                        },
                        "fix_pack": {
                            "target_kind": "scene_model",
                            "patch_targets": ["ending beat"],
                        },
                        "repair_contract": {
                            "provenance": "runtime_synthesized",
                        },
                        "scope_authority": {
                            "fix_scope": "local",
                            "authoritative_fix_scope": "partial",
                            "widened": False,
                        },
                    }
                },
                "projected_payloads": {
                    "selection_contract_snapshot_raw": {
                        "director_verdict": "PASS_WITH_FIX",
                        "gate_basis": "bounded_local_repair",
                        "repair_scope": "partial",
                        "fix_pack_target_kind": "scene_model",
                        "fix_pack_patch_targets": ["ending beat"],
                        "retry_budget_axes": {},
                        "repair_contract": {"provenance": "runtime_synthesized"},
                        "repair_contract_subtype": "",
                        "repair_contract_provenance": "runtime_synthesized",
                        "scope_authority": {
                            "fix_scope": "local",
                            "authoritative_fix_scope": "partial",
                            "widened": False,
                        },
                        "scope_authority_fix_scope": "local",
                        "scope_authority_authoritative_fix_scope": "partial",
                        "scope_authority_scope_origin": "",
                        "scope_authority_widened": False,
                    }
                },
            }
        },
        stage_attempts={},
        pass_rate_monitor={},
        director_selections={
            attempt_key: {
                "director_verdict": "REJECT",
                "gate_basis": "bounded_local_repair",
                "repair_scope": "partial",
                "fix_pack_target_kind": "scene_model",
                "fix_pack_patch_targets": ["ending beat", "opening beat"],
                "repair_contract_provenance": "director_authored",
                "scope_authority_fix_scope": "local",
                "scope_authority_authoritative_fix_scope": "full",
                "scope_authority_widened": True,
            }
        },
        session_decisions={},
        episode_production={},
    )

    assert results["raw_rationale_contract_mismatches"] == [
        {
            "attempt_key": attempt_key,
            "payload_kind": "selection_contract_snapshot_raw",
            "mismatched_fields": {
                "director_verdict": {
                    "selection_contract_snapshot_raw": "PASS_WITH_FIX",
                    "director_selections": "REJECT",
                },
                "fix_pack_patch_targets": {
                    "selection_contract_snapshot_raw": ["ending beat"],
                    "director_selections": ["ending beat", "opening beat"],
                },
                "repair_contract_provenance": {
                    "selection_contract_snapshot_raw": "runtime_synthesized",
                    "director_selections": "director_authored",
                },
                "scope_authority_authoritative_fix_scope": {
                    "selection_contract_snapshot_raw": "partial",
                    "director_selections": "full",
                },
                "scope_authority_widened": {
                    "selection_contract_snapshot_raw": False,
                    "director_selections": True,
                },
            },
        }
    ]


def test_failure_analyzer_collect_sink_alignment_raw_rationale_results_tracks_stage4_contract_snapshot_multisink_mismatch():
    attempt_key = "s4:ep82:arc8:a1:sess_contract_multi"
    results = FailureAnalyzer._collect_sink_alignment_raw_rationale_results(
        stage=4,
        attempt_key=attempt_key,
        raw_rationale_by_attempt={
            attempt_key: {
                "payload_kinds": {"contract_snapshot_raw"},
                "record_families": {"contract_snapshot"},
                "projected_payloads": {
                    "contract_snapshot_raw": {
                        "director_verdict": "PASS",
                        "gate_basis": "direct_pass",
                        "repair_scope": "full",
                        "fix_pack_target_kind": "",
                        "fix_pack_patch_targets": [],
                        "retry_budget_axes": {"repair": "rewrite_regenerate"},
                        "repair_contract": {},
                        "repair_contract_subtype": "",
                        "repair_contract_provenance": "",
                        "scope_authority": {},
                        "scope_authority_fix_scope": "",
                        "scope_authority_authoritative_fix_scope": "",
                        "scope_authority_scope_origin": "",
                        "scope_authority_widened": None,
                    }
                },
            }
        },
        stage_attempts={
            attempt_key: {
                "director_verdict": "REJECT",
                "gate_basis": "direct_pass",
                "repair_scope": "full",
            }
        },
        pass_rate_monitor={
            attempt_key: {
                "director_verdict": "PASS",
                "gate_basis": "patch_reaudit_fail",
                "repair_scope": "full",
            }
        },
        director_selections={},
        session_decisions={
            attempt_key: {
                "director_verdict": "REJECT",
                "gate_basis": "patch_reaudit_fail",
                "repair_scope": "partial",
            }
        },
        episode_production={
            attempt_key: {
                "director_verdict": "PASS",
                "gate_basis": "direct_pass",
                "repair_scope": "partial",
            }
        },
    )

    assert results["raw_rationale_contract_mismatches"] == [
        {
            "attempt_key": attempt_key,
            "payload_kind": "contract_snapshot_raw",
            "mismatched_fields": {
                "director_verdict": {
                    "contract_snapshot_raw": "PASS",
                    "stage_attempts": "REJECT",
                    "session_decisions": "REJECT",
                },
                "gate_basis": {
                    "contract_snapshot_raw": "direct_pass",
                    "pass_rate_monitor": "patch_reaudit_fail",
                    "session_decisions": "patch_reaudit_fail",
                },
                "repair_scope": {
                    "contract_snapshot_raw": "full",
                    "session_decisions": "partial",
                    "episode_production": "partial",
                },
            },
        }
    ]


def test_failure_analyzer_collect_sink_alignment_raw_rationale_results_tracks_stage4_feedback_provenance_mismatch():
    attempt_key = "s4:ep81:arc8:a1:sess_feedback"
    results = FailureAnalyzer._collect_sink_alignment_raw_rationale_results(
        stage=4,
        attempt_key=attempt_key,
        raw_rationale_by_attempt={
            attempt_key: {
                "payload_kinds": {"feedback_provenance_raw"},
                "record_families": {"feedback_provenance"},
                "decoded_payloads": {
                    "feedback_provenance_raw": {
                        "runtime_advisory": "raw advisory",
                        "retry_directives": "raw retry",
                    }
                },
            }
        },
        stage_attempts={
            attempt_key: {
                "runtime_advisory": "db advisory",
                "retry_directives": "raw retry",
            }
        },
        pass_rate_monitor={},
        director_selections={
            attempt_key: {
                "runtime_advisory": "raw advisory",
                "retry_directives": "db retry",
            }
        },
        session_decisions={
            attempt_key: {
                "runtime_advisory": "session advisory",
                "retry_directives": "session retry",
            }
        },
        episode_production={},
    )

    assert results["raw_rationale_feedback_mismatches"] == [
        {
            "attempt_key": attempt_key,
            "field": "runtime_advisory",
            "feedback_provenance_raw": "raw advisory",
            "stage_attempts": "db advisory",
            "session_decisions": "session advisory",
        },
        {
            "attempt_key": attempt_key,
            "field": "retry_directives",
            "feedback_provenance_raw": "raw retry",
            "director_selections": "db retry",
            "session_decisions": "session retry",
        },
    ]


def test_failure_analyzer_collect_sink_alignment_raw_rationale_results_ignores_prefinal_companion_contract_and_feedback_drift():
    attempt_key = "s4:ep81:arc8:a1:sess_prefinal_raw"
    results = FailureAnalyzer._collect_sink_alignment_raw_rationale_results(
        stage=4,
        attempt_key=attempt_key,
        raw_rationale_by_attempt={
            attempt_key: {
                "payload_kinds": {"selection_contract_snapshot_raw", "feedback_provenance_raw"},
                "record_families": {"contract_snapshot", "feedback_provenance"},
                "projected_payloads": {
                    "selection_contract_snapshot_raw": {
                        "director_verdict": "PASS_WITH_FIX",
                        "gate_basis": "director_primary_pass_with_fix",
                        "repair_scope": "inplace",
                        "scope_authority_fix_scope": "inplace",
                        "scope_authority_widened": False,
                    },
                    "feedback_provenance_raw": {
                        "runtime_advisory": "raw advisory",
                        "retry_directives": "raw retry",
                    },
                },
            }
        },
        stage_attempts={
            attempt_key: {
                "runtime_advisory": "db advisory",
                "retry_directives": "db retry",
            }
        },
        pass_rate_monitor={},
        director_selections={
            attempt_key: {
                "director_verdict": "REJECT",
                "gate_basis": "post_select_conflict",
                "repair_scope": "full",
                "scope_authority_fix_scope": "full",
                "scope_authority_widened": True,
                "runtime_advisory": "director advisory",
                "retry_directives": "director retry",
            }
        },
        session_decisions={},
        episode_production={},
        authority_row={"selection_companion_status": "pre_final_candidate"},
    )

    assert results["raw_rationale_contract_mismatches"] == []
    assert results["raw_rationale_feedback_mismatches"] == []


def test_failure_analyzer_collect_sink_alignment_raw_rationale_results_tracks_stage4_patch_trace_mismatch():
    attempt_key = "s4:ep81:arc8:a1:sess_patchtrace"
    results = FailureAnalyzer._collect_sink_alignment_raw_rationale_results(
        stage=4,
        attempt_key=attempt_key,
        raw_rationale_by_attempt={
            attempt_key: {
                "payload_kinds": {"patch_trace_raw"},
                "record_families": {"patch_trace"},
                "decoded_payloads": {
                    "patch_trace_raw": {
                        "patch_strategy": "patch_with_feedback",
                        "structural_attempted": True,
                    }
                },
            }
        },
        stage_attempts={
            attempt_key: {
                "patch_strategy": "stage_attempt_rewrite",
            }
        },
        pass_rate_monitor={
            attempt_key: {
                "patch_strategy": "rewrite",
                "structural_attempted": False,
            }
        },
        director_selections={},
        session_decisions={},
        episode_production={
            attempt_key: {
                "patch_strategy": "patch_with_feedback",
                "structural_attempted": False,
            }
        },
    )

    assert results["raw_rationale_patch_trace_mismatches"] == [
        {
            "attempt_key": attempt_key,
            "field": "patch_strategy",
            "patch_trace_raw": "patch_with_feedback",
            "stage_attempts": "stage_attempt_rewrite",
            "pass_rate_monitor": "rewrite",
        },
        {
            "attempt_key": attempt_key,
            "field": "structural_attempted",
            "patch_trace_raw": True,
            "pass_rate_monitor": False,
            "episode_production": False,
        },
    ]


def test_failure_analyzer_collect_sink_alignment_raw_rationale_results_tracks_stage4_retry_chain_mismatch():
    attempt_key = "s4:ep81:arc8:a1:sess_retrychain"
    results = FailureAnalyzer._collect_sink_alignment_raw_rationale_results(
        stage=4,
        attempt_key=attempt_key,
        raw_rationale_by_attempt={
            attempt_key: {
                "payload_kinds": {"reject_retry_snapshot_raw", "retry_pathology_raw"},
                "record_families": {"reject_retry_snapshot", "retry_pathology"},
                "projected_payloads": {
                    "reject_retry_snapshot_raw": {
                        "previous_attempt_attempt_key": "s4:ep81:arc8:a1:sess_retrychain",
                        "previous_attempt_candidate_key": "A|balanced",
                        "previous_attempt_content_hash": "hash-a",
                        "previous_attempt_scope_origin": {"fix_scope": "runtime_widened"},
                        "previous_attempt_reuse_contract": {"mode": "best_manuscript_baseline"},
                    },
                    "retry_pathology_raw": {
                        "attempt_key": "s4:ep81:arc8:a1:sess_retrychain",
                        "candidate_key": "B|balanced",
                        "content_hash": "hash-a",
                        "scope_origin": {"fix_scope": "director_authoritative"},
                        "reuse_contract": {"mode": "best_manuscript_baseline"},
                    },
                },
            }
        },
        stage_attempts={},
        pass_rate_monitor={},
        director_selections={},
        session_decisions={},
        episode_production={},
    )

    assert results["raw_rationale_retry_chain_mismatches"] == [
        {
            "attempt_key": attempt_key,
            "mismatched_fields": {
                "previous_attempt_candidate_key": {
                    "reject_retry_snapshot_raw": "A|balanced",
                    "retry_pathology_raw": "B|balanced",
                },
                "previous_attempt_scope_origin": {
                    "reject_retry_snapshot_raw": {"fix_scope": "runtime_widened"},
                    "retry_pathology_raw": {"fix_scope": "director_authoritative"},
                },
            },
        }
    ]


def test_failure_analyzer_build_sink_alignment_summary_payload_marks_warn_and_counts_contract_rows(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_summary_payload.db")
    try:
        analyzer = FailureAnalyzer(db)
        attempt_key = "s4:ep81:arc8:a1:sess_payload"
        consistency_results = {
            key: []
            for key in (
                "final_verdict_mismatches",
                "final_score_mismatches",
                "initial_verdict_mismatches",
                "director_verdict_mismatches",
                "gate_basis_mismatches",
                "repair_scope_mismatches",
                "fix_pack_target_kind_mismatches",
                "fix_pack_patch_targets_mismatches",
                "retry_budget_axes_mismatches",
                "repair_contract_subtype_mismatches",
                "repair_contract_provenance_mismatches",
                "scope_authority_fix_scope_mismatches",
                "scope_authority_authoritative_fix_scope_mismatches",
                "scope_authority_widened_mismatches",
                "patch_strategy_mismatches",
                "candidate_key_mismatches",
                "selection_candidate_key_mismatches",
                "content_hash_mismatches",
                "artifact_path_mismatches",
                "artifact_metadata_missing",
                "selection_reason_mismatches",
                "verdict_reason_mismatches",
                "fix_scope_mismatches",
                "runtime_advisory_mismatches",
                "retry_directives_mismatches",
                "gate_repair_metadata_missing",
                "rationale_metadata_missing",
                "artifact_missing_files",
                "selection_companion_pre_final_rows",
                "selection_companion_missing_rows",
                "raw_rationale_missing",
                "raw_rationale_kind_missing",
                "raw_rationale_family_missing",
                "raw_rationale_surface_mismatches",
                "raw_rationale_contract_mismatches",
                "raw_rationale_feedback_mismatches",
                "raw_rationale_patch_trace_mismatches",
                "raw_rationale_retry_chain_mismatches",
            )
        }
        consistency_results["patch_strategy_mismatches"] = [
            {"attempt_key": attempt_key, "pass_rate_monitor": "inplace_patch", "episode_production": "rewrite"}
        ]
        consistency_results["raw_rationale_surface_mismatches"] = [
            {
                "attempt_key": attempt_key,
                "mismatched_fields": {"selected_strategy": {"selection_surface_raw": "balanced"}},
            }
        ]
        consistency_results["selection_companion_pre_final_rows"] = [{"attempt_key": attempt_key}]
        consistency_results["selection_companion_missing_rows"] = [{"attempt_key": "s4:ep82:arc8:a1:sess_payload"}]

        result = analyzer._build_sink_alignment_summary_payload(
            stage=4,
            session_id="sess_payload",
            attempts_considered={attempt_key, "legacy-key"},
            final_union={attempt_key},
            lifecycle_union={attempt_key},
            stage_attempts={attempt_key: {}},
            pass_rate_monitor={attempt_key: {}},
            director_selections={attempt_key: {}},
            session_decisions={},
            episode_production={attempt_key: {}},
            final_missing={},
            lifecycle_missing={},
            lifecycle_missing_in_final={},
            stage_attempt_rows_without_attempt_key=0,
            session_decision_rows_without_attempt_key=0,
            final_authority_rows=[
                {"selection_companion_status": "same_as_final"},
                {"selection_companion_status": "pre_final_candidate"},
                {"selection_companion_status": "missing"},
            ],
            consistency_results=consistency_results,
            raw_rationale_by_attempt={
                attempt_key: {
                    "payload_kinds": {"selection_surface_raw", "contract_snapshot_raw"},
                    "record_families": {"selection_surface", "contract_snapshot"},
                    "surfaces": {"selection_surface_raw", "contract_snapshot_raw"},
                    "projected_payloads": {
                        "selection_surface_raw": {"selected_label": "candidate_alpha"},
                        "contract_snapshot_raw": {"gate_basis": "quality_floor_fail"},
                    },
                }
            },
        )

        assert result["status"] == "warn"
        assert result["attempts_considered"] == 2
        assert result["complete_final_attempts"] == 1
        assert result["director_lifecycle_attempts"] == 1
        assert result["complete_lifecycle_attempts"] == 1
        assert result["session_scoped_attempts"] == 1
        assert result["legacy_key_attempts"] == 1
        assert result["final_authority_contract"] == {
            "status": "ok",
            "final_authority_sink": "stage_attempts",
            "selection_role": "historical_companion",
            "rows_considered": 3,
            "aligned_selection_rows": 1,
            "pre_final_selection_rows": 1,
            "missing_selection_rows": 1,
            "note": (
                "Stage 4 final authority resolves from stage_attempts. "
                "director_selections remains companion review history and may point to pre-final artifacts."
            ),
        }
        assert result["coverage"]["attempt_raw_rationale"] == 1
        assert result["raw_rationale_summary"] == {
            "attempts_with_raw_rationale": 1,
            "attempts_with_projected_payloads": 1,
            "payload_kinds_present": ["contract_snapshot_raw", "selection_surface_raw"],
            "record_families_present": ["contract_snapshot", "selection_surface"],
            "surfaces_present": ["contract_snapshot_raw", "selection_surface_raw"],
            "projected_payload_kinds_present": ["contract_snapshot_raw", "selection_surface_raw"],
            "payload_kind_attempt_counts": {
                "contract_snapshot_raw": 1,
                "selection_surface_raw": 1,
            },
            "record_family_attempt_counts": {
                "contract_snapshot": 1,
                "selection_surface": 1,
            },
            "surface_attempt_counts": {
                "contract_snapshot_raw": 1,
                "selection_surface_raw": 1,
            },
            "projected_payload_attempt_counts": {
                "contract_snapshot_raw": 1,
                "selection_surface_raw": 1,
            },
            "payload_kind_examples": {
                "contract_snapshot_raw": [attempt_key],
                "selection_surface_raw": [attempt_key],
            },
            "record_family_examples": {
                "contract_snapshot": [attempt_key],
                "selection_surface": [attempt_key],
            },
            "surface_examples": {
                "contract_snapshot_raw": [attempt_key],
                "selection_surface_raw": [attempt_key],
            },
            "projected_payload_examples": {
                "contract_snapshot_raw": [attempt_key],
                "selection_surface_raw": [attempt_key],
            },
        }
        assert result["raw_rationale_health"] == {
            "status": "warn",
            "attempts_with_raw_rationale": 1,
            "attempts_with_projected_payloads": 1,
            "projection_gap": 0,
            "payload_kinds_present": ["contract_snapshot_raw", "selection_surface_raw"],
            "record_families_present": ["contract_snapshot", "selection_surface"],
            "surfaces_present": ["contract_snapshot_raw", "selection_surface_raw"],
            "issue_counts": {
                "surface_mismatches": 1,
            },
            "issue_examples": {
                "surface_mismatches": [attempt_key],
            },
        }
        assert result["raw_rationale_watchlist"] == [
            {
                "priority": "P2",
                "focus": "raw_surface_drift",
                "count": 1,
                "next_action": (
                    "Selection surface raw rows disagree with director selection sinks; "
                    "verify surface projection and persistence ordering."
                ),
                "examples": [attempt_key],
            }
        ]
        assert result["raw_rationale_watchlist_headline"] == {
            "headline": "P2 raw_surface_drift x1",
            "priority": "P2",
            "focus": "raw_surface_drift",
            "count": 1,
            "next_action": (
                "Selection surface raw rows disagree with director selection sinks; "
                "verify surface projection and persistence ordering."
            ),
            "examples": [attempt_key],
        }
        assert result["raw_rationale_operator_summary"] == (
            "Stage4 raw rationale warn: 1 attempt(s), 1 projected, 2 family(s), 2 surface(s). "
            "Top watchlist: P2 raw_surface_drift x1. "
            "Next: Selection surface raw rows disagree with director selection sinks; "
            "verify surface projection and persistence ordering."
        )
        assert result["coverage_gap_count"] == 0
        assert result["structured_issue_count"] == 2
        assert result["raw_issue_count"] == 1
        assert result["top_issue_headline"] == {
            "headline": "P2 structured_sink_drift x2",
            "priority": "P2",
            "focus": "structured_sink_drift",
            "count": 2,
            "next_action": "Inspect structured sink mismatches before trusting cross-sink contract parity.",
        }
        assert result["operator_summary"] == (
            "Stage4 sink alignment warn: 2 attempt(s), final 1/1, lifecycle 1/1, "
            "coverage gaps 0, sink issues 2, evidence issues 1. "
            "Top issue: P2 structured_sink_drift x2. "
            "Next: Inspect structured sink mismatches before trusting cross-sink contract parity. "
            "Evidence: Stage4 raw rationale warn: 1 attempt(s), 1 projected, 2 family(s), 2 surface(s). "
            "Top watchlist: P2 raw_surface_drift x1. "
            "Next: Selection surface raw rows disagree with director selection sinks; "
            "verify surface projection and persistence ordering."
        )
        assert result["patch_strategy_mismatches"] == consistency_results["patch_strategy_mismatches"]
        assert result["raw_rationale_surface_mismatches"] == consistency_results["raw_rationale_surface_mismatches"]
    finally:
        db.close()


def test_failure_analyzer_collect_sink_alignment_verdict_results_detects_core_mismatches():
    attempt_key = "s4:ep91:arc9:a1:sess_verdict"
    result = FailureAnalyzer._collect_sink_alignment_verdict_results(
        attempt_key=attempt_key,
        stage_attempts={attempt_key: {"final_verdict": "REJECT", "final_score": 61}},
        pass_rate_monitor={attempt_key: {"final_verdict": "PASS", "patch_strategy": "inplace_patch"}},
        director_selections={attempt_key: {"initial_verdict": "PASS_WITH_FIX"}},
        session_decisions={attempt_key: {"final_verdict": "PASS", "final_score": 95}},
        episode_production={
            attempt_key: {
                "final_verdict": "PASS",
                "final_score": 98,
                "initial_verdict": "REJECT",
                "patch_strategy": "rewrite",
            }
        },
    )

    assert result == {
        "final_verdict_mismatches": [
            {
                "attempt_key": attempt_key,
                "stage_attempts": "REJECT",
                "pass_rate_monitor": "PASS",
                "session_decisions": "PASS",
                "episode_production": "PASS",
            }
        ],
        "final_score_mismatches": [
            {
                "attempt_key": attempt_key,
                "stage_attempts": 61,
                "session_decisions": 95,
                "episode_production": 98,
            }
        ],
        "initial_verdict_mismatches": [
            {
                "attempt_key": attempt_key,
                "director_selections": "PASS_WITH_FIX",
                "episode_production": "REJECT",
            }
        ],
        "patch_strategy_mismatches": [
            {
                "attempt_key": attempt_key,
                "pass_rate_monitor": "inplace_patch",
                "episode_production": "rewrite",
            }
        ],
    }


def test_failure_analyzer_collect_sink_alignment_artifact_results_detects_mismatch_and_missing_file(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_artifact_helper.db")
    try:
        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        attempt_key = "s4:ep92:arc9:a1:sess_artifact"
        existing_path = "logs/artifacts/stage4/ep_0092/attempt_01/final.txt"
        missing_path = "logs/artifacts/stage4/ep_0092/attempt_01/missing.txt"
        existing_file = tmp_path / existing_path
        existing_file.parent.mkdir(parents=True, exist_ok=True)
        existing_file.write_text("artifact", encoding="utf-8")

        result = analyzer._collect_sink_alignment_artifact_results(
            attempt_key=attempt_key,
            stage_attempts={
                attempt_key: {
                    "candidate_key": "A|final",
                    "content_hash": "hash-a",
                    "artifact_path": existing_path,
                }
            },
            pass_rate_monitor={
                attempt_key: {
                    "candidate_key": "B|final",
                    "content_hash": "hash-b",
                    "artifact_path": missing_path,
                }
            },
            director_selections={attempt_key: {"candidate_key": "C|selected"}},
            session_decisions={},
            episode_production={
                attempt_key: {
                    "candidate_key": "A|final",
                    "selection_candidate_key": "D|selected",
                    "content_hash": "hash-a",
                    "artifact_path": existing_path,
                }
            },
        )

        assert result["candidate_key_mismatches"] == [
            {
                "attempt_key": attempt_key,
                "stage_attempts": "A|final",
                "pass_rate_monitor": "B|final",
                "episode_production": "A|final",
            }
        ]
        assert result["content_hash_mismatches"] == [
            {
                "attempt_key": attempt_key,
                "stage_attempts": "hash-a",
                "pass_rate_monitor": "hash-b",
                "episode_production": "hash-a",
            }
        ]
        assert result["artifact_path_mismatches"] == [
            {
                "attempt_key": attempt_key,
                "stage_attempts": existing_path,
                "pass_rate_monitor": missing_path,
                "episode_production": existing_path,
            }
        ]
        assert result["selection_candidate_key_mismatches"] == [
            {
                "attempt_key": attempt_key,
                "director_selections": "C|selected",
                "episode_production": "D|selected",
            }
        ]
        assert result["artifact_metadata_missing"] == []
        assert result["artifact_missing_files"] == [
            {
                "attempt_key": attempt_key,
                "sink": "pass_rate_monitor",
                "artifact_path": missing_path,
            }
        ]
    finally:
        db.close()


def test_failure_analyzer_collect_sink_alignment_artifact_results_recomputes_file_hash(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_artifact_hash_helper.db")
    try:
        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        attempt_key = "s4:ep93:arc9:a1:sess_artifact_hash"
        artifact_path = "logs/artifacts/stage4/ep_0093/attempt_01/final.txt"
        artifact_file = tmp_path / artifact_path
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_bytes(b"artifact bytes")
        actual_hash = hashlib.sha256(b"artifact bytes").hexdigest()

        result = analyzer._collect_sink_alignment_artifact_results(
            attempt_key=attempt_key,
            stage_attempts={
                attempt_key: {
                    "candidate_key": "A|final",
                    "content_hash": "0" * 64,
                    "artifact_path": artifact_path,
                }
            },
            pass_rate_monitor={},
            director_selections={},
            session_decisions={},
            episode_production={},
        )

        assert result["artifact_missing_files"] == []
        assert result["artifact_content_hash_mismatches"] == [
            {
                "attempt_key": attempt_key,
                "sink": "stage_attempts",
                "artifact_path": artifact_path,
                "content_hash": "0" * 64,
                "actual_content_hash": actual_hash,
            }
        ]
    finally:
        db.close()


def test_failure_analyzer_sink_alignment_summary_detects_missing_and_mismatch(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_summary.db")
    try:
        attempt_key_1 = "s4:ep31:arc3:a1:sess_a"
        attempt_key_2 = "s4:ep32:arc3:a1:sess_a"

        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=31,
            arc_num=3,
            score=98,
            session_id="sess_a",
            attempt_key=attempt_key_1,
        )
        db.save_stage_attempt(
            stage=4,
            verdict="REJECT",
            attempt_num=1,
            ep_num=32,
            arc_num=3,
            score=61,
            session_id="sess_a",
            attempt_key=attempt_key_2,
        )

        db.save_director_selection(
            ep_num=31,
            round_num=1,
            selected_label="candidate_a",
            selected_strategy="default",
            verdict="PASS_WITH_FIX",
            score=92,
            stage=4,
            attempt_key=attempt_key_1,
        )
        db.save_director_selection(
            ep_num=32,
            round_num=1,
            selected_label="candidate_b",
            selected_strategy="default",
            verdict="REJECT",
            score=61,
            stage=4,
            attempt_key=attempt_key_2,
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        episode_entries = [
            {
                "ep": 31,
                "attempt_key": attempt_key_1,
                "verdict": "PASS_WITH_FIX",
                "score": 92,
                "initial_verdict": "PASS_WITH_FIX",
                "initial_score": 92,
                "final_verdict": "PASS",
                "final_score": 98,
                "patch_trace": {
                    "patch_strategy": "inplace_patch_structural",
                    "patch_targets": ["scene_3"],
                    "unchanged_ratio": 0.84,
                    "fallback_reason": "",
                    "focus": "ending",
                    "structural_attempted": True,
                },
            }
        ]
        (logs_dir / "episode_production.jsonl").write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in episode_entries) + "\n",
            encoding="utf-8",
        )

        pass_rate_payload = {
            "records": [
                {
                    "stage": 4,
                    "episode": 31,
                    "arc": 3,
                    "attempt_num": 1,
                    "success": True,
                    "attempt_key": attempt_key_1,
                    "final_verdict": "PASS",
                    "patch_strategy": "inplace_patch_structural",
                    "structural_attempted": True,
                },
                {
                    "stage": 4,
                    "episode": 32,
                    "arc": 3,
                    "attempt_num": 1,
                    "success": False,
                    "attempt_key": attempt_key_2,
                    "final_verdict": "PASS",
                    "patch_strategy": "",
                    "structural_attempted": False,
                },
            ]
        }
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(pass_rate_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db)
        result = analyzer.sink_alignment_summary()
        summary = analyzer.summary()

        assert result["attempts_considered"] == 2
        assert result["coverage"]["stage_attempts"] == 2
        assert result["coverage"]["pass_rate_monitor"] == 2
        assert result["coverage"]["director_selections"] == 2
        assert result["coverage"]["episode_production"] == 1
        assert result["complete_final_attempts"] == 2
        assert result["director_lifecycle_attempts"] == 2
        assert result["complete_lifecycle_attempts"] == 1
        assert result["session_scoped_attempts"] == 2
        assert result["legacy_key_attempts"] == 0
        assert result["status"] == "warn"
        assert result["lifecycle_sink_missing"]["episode_production"]["count"] == 1
        assert attempt_key_2 in result["lifecycle_sink_missing"]["episode_production"]["examples"]
        assert result["lifecycle_missing_in_final_sinks"] == {}
        assert result["final_verdict_mismatches"] == [
            {
                "attempt_key": attempt_key_2,
                "stage_attempts": "REJECT",
                "pass_rate_monitor": "PASS",
            }
        ]
        assert summary["sink_alignment_summary"]["attempts_considered"] == 2
        assert summary["sink_alignment_summary"]["status"] == "warn"
    finally:
        db.close()


def test_failure_analyzer_sink_alignment_summary_tracks_gate_repair_contract_fields(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_gate_repair.db")
    try:
        mismatch_key = "s4:ep71:arc7:a1:sess_gate"
        missing_key = "s4:ep72:arc7:a1:sess_gate"
        no_meta_key = "s4:ep73:arc7:a1:sess_gate"

        advisory_flags = {
            "gate_semantics": {
                "director_verdict": "PASS_WITH_FIX",
                "gate_basis": "bounded_local_repair",
                "repair_scope": "inplace",
            },
            "repair_contract": {
                "subtype": "opening_spatial_continuity",
                "provenance": "runtime_synthesized",
            },
            "scope_authority": {
                "fix_scope": "local",
                "authoritative_fix_scope": "inplace",
                "scope_origin": "director_authored",
                "widened": False,
            },
            "fix_pack": {
                "target_kind": "entity_ref",
                "patch_targets": ["opening_location_name", "ending_location_name"],
            },
            "retry_budget_axes": {"round": 1, "repair": 1},
        }

        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=71,
            arc_num=7,
            score=96,
            session_id="sess_gate",
            attempt_key=mismatch_key,
            advisory_flags=advisory_flags,
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=72,
            arc_num=7,
            score=93,
            session_id="sess_gate",
            attempt_key=missing_key,
            advisory_flags=advisory_flags,
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=73,
            arc_num=7,
            score=90,
            session_id="sess_gate",
            attempt_key=no_meta_key,
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "stage": 4,
                            "episode": 71,
                            "arc": 7,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": mismatch_key,
                            "final_verdict": "PASS",
                            "director_verdict": "REJECT",
                            "gate_basis": "scene_rewrite",
                            "repair_scope": "full",
                            "repair_contract": {
                                "subtype": "scene_transition_conflict",
                                "provenance": "director_authored",
                            },
                            "scope_authority": {
                                "fix_scope": "full",
                                "authoritative_fix_scope": "scene_rewrite",
                                "scope_origin": "runtime_widened",
                                "widened": True,
                            },
                            "fix_pack": {
                                "target_kind": "scene_model",
                                "patch_targets": ["scene_model"],
                            },
                            "retry_budget_axes": {"round": 2, "repair": 3},
                        },
                        {
                            "stage": 4,
                            "episode": 72,
                            "arc": 7,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": missing_key,
                            "final_verdict": "PASS",
                        },
                        {
                            "stage": 4,
                            "episode": 73,
                            "arc": 7,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": no_meta_key,
                            "final_verdict": "PASS",
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary(stage=4)

        assert any(item["attempt_key"] == mismatch_key for item in result["director_verdict_mismatches"])
        assert any(item["attempt_key"] == mismatch_key for item in result["gate_basis_mismatches"])
        assert any(item["attempt_key"] == mismatch_key for item in result["repair_scope_mismatches"])
        assert any(item["attempt_key"] == mismatch_key for item in result["fix_pack_target_kind_mismatches"])
        assert any(item["attempt_key"] == mismatch_key for item in result["fix_pack_patch_targets_mismatches"])
        assert any(item["attempt_key"] == mismatch_key for item in result["retry_budget_axes_mismatches"])
        assert any(item["attempt_key"] == mismatch_key for item in result["repair_contract_subtype_mismatches"])
        assert any(item["attempt_key"] == mismatch_key for item in result["repair_contract_provenance_mismatches"])
        assert any(item["attempt_key"] == mismatch_key for item in result["scope_authority_fix_scope_mismatches"])
        assert any(
            item["attempt_key"] == mismatch_key for item in result["scope_authority_authoritative_fix_scope_mismatches"]
        )
        assert any(item["attempt_key"] == mismatch_key for item in result["scope_authority_widened_mismatches"])

        missing_entries = [
            item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == missing_key
        ]
        assert any(
            item["field"] == "director_verdict" and "pass_rate_monitor" in item["sinks"] for item in missing_entries
        )
        assert any(
            item["field"] == "fix_pack_patch_targets" and "pass_rate_monitor" in item["sinks"]
            for item in missing_entries
        )
        assert any(
            item["field"] == "repair_contract_subtype" and "pass_rate_monitor" in item["sinks"]
            for item in missing_entries
        )
        assert any(
            item["field"] == "scope_authority_authoritative_fix_scope" and "pass_rate_monitor" in item["sinks"]
            for item in missing_entries
        )
        assert not any(item["attempt_key"] == no_meta_key for item in result["gate_repair_metadata_missing"])
    finally:
        db.close()


def test_failure_analyzer_sink_alignment_summary_reports_artifact_linkage_issues(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_artifact.db")
    try:
        attempt_key_ok = "s4:ep41:arc4:a1:sess_art"
        attempt_key_bad = "s4:ep42:arc4:a1:sess_art"
        good_artifact = "logs/artifacts/stage4/ep_0041/attempt_01/final_manuscript__A_balanced.txt"
        bad_artifact = "logs/artifacts/stage4/ep_0042/attempt_01/final_manuscript__B_balanced.txt"
        bad_alt_artifact = "logs/artifacts/stage4/ep_0042/attempt_01/final_manuscript__B_alt.txt"

        good_path = tmp_path / good_artifact
        good_path.parent.mkdir(parents=True, exist_ok=True)
        good_path.write_text("artifact ok", encoding="utf-8")

        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=41,
            arc_num=4,
            score=97,
            session_id="sess_art",
            attempt_key=attempt_key_ok,
            candidate_key="A|balanced",
            content_hash="hash-ok",
            artifact_path=good_artifact,
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=42,
            arc_num=4,
            score=94,
            session_id="sess_art",
            attempt_key=attempt_key_bad,
            candidate_key="B|balanced",
            content_hash="hash-bad-db",
            artifact_path=bad_artifact,
        )

        db.save_director_selection(
            ep_num=41,
            round_num=1,
            selected_label="candidate_a",
            selected_strategy="balanced",
            verdict="PASS",
            score=97,
            stage=4,
            attempt_key=attempt_key_ok,
            candidate_key="A|balanced",
            content_hash="hash-ok",
            artifact_path=good_artifact,
        )
        db.save_director_selection(
            ep_num=42,
            round_num=1,
            selected_label="candidate_b",
            selected_strategy="balanced",
            verdict="PASS_WITH_FIX",
            score=91,
            stage=4,
            attempt_key=attempt_key_bad,
            candidate_key="C|balanced",
            content_hash="hash-bad-director",
            artifact_path="logs/artifacts/stage4/ep_0042/attempt_01/selected_before_fix__C_balanced.txt",
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        episode_entries = [
            {
                "ep": 41,
                "attempt_key": attempt_key_ok,
                "verdict": "PASS",
                "score": 97,
                "initial_verdict": "PASS",
                "initial_score": 97,
                "final_verdict": "PASS",
                "final_score": 97,
                "candidate_key": "A|balanced",
                "content_hash": "hash-ok",
                "artifact_path": good_artifact,
                "patch_trace": {"patch_strategy": "", "structural_attempted": False},
            },
            {
                "ep": 42,
                "attempt_key": attempt_key_bad,
                "verdict": "PASS_WITH_FIX",
                "score": 91,
                "initial_verdict": "PASS_WITH_FIX",
                "initial_score": 91,
                "final_verdict": "PASS",
                "final_score": 94,
                "candidate_key": "B|balanced",
                "content_hash": "hash-bad-episode",
                "artifact_path": bad_artifact,
                "patch_trace": {"patch_strategy": "inplace_patch_structural", "structural_attempted": True},
            },
        ]
        (logs_dir / "episode_production.jsonl").write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in episode_entries) + "\n",
            encoding="utf-8",
        )

        pass_rate_payload = {
            "records": [
                {
                    "stage": 4,
                    "episode": 41,
                    "arc": 4,
                    "attempt_num": 1,
                    "success": True,
                    "attempt_key": attempt_key_ok,
                    "final_verdict": "PASS",
                    "patch_strategy": "",
                    "structural_attempted": False,
                    "candidate_key": "A|balanced",
                    "content_hash": "hash-ok",
                    "artifact_path": good_artifact,
                },
                {
                    "stage": 4,
                    "episode": 42,
                    "arc": 4,
                    "attempt_num": 1,
                    "success": True,
                    "attempt_key": attempt_key_bad,
                    "final_verdict": "PASS",
                    "patch_strategy": "inplace_patch_structural",
                    "structural_attempted": True,
                    "candidate_key": "B|balanced",
                    "content_hash": "hash-bad-monitor",
                    "artifact_path": bad_alt_artifact,
                },
            ]
        }
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(pass_rate_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary()

        assert result["status"] == "warn"
        assert result["candidate_key_mismatches"] == []
        assert result["selection_candidate_key_mismatches"] == []
        assert result["content_hash_mismatches"] == [
            {
                "attempt_key": attempt_key_bad,
                "stage_attempts": "hash-bad-db",
                "pass_rate_monitor": "hash-bad-monitor",
                "episode_production": "hash-bad-episode",
            }
        ]
        assert result["artifact_path_mismatches"] == [
            {
                "attempt_key": attempt_key_bad,
                "stage_attempts": bad_artifact,
                "pass_rate_monitor": bad_alt_artifact,
                "episode_production": bad_artifact,
            }
        ]
        assert result["artifact_metadata_missing"] == []
        assert any(
            row["attempt_key"] == attempt_key_bad and row["artifact_path"] == bad_artifact
            for row in result["artifact_missing_files"]
        )
        assert any(
            row["attempt_key"] == attempt_key_bad and row["artifact_path"] == bad_alt_artifact
            for row in result["artifact_missing_files"]
        )
        assert result["final_authority_contract"] == {
            "status": "ok",
            "final_authority_sink": "stage_attempts",
            "selection_role": "historical_companion",
            "rows_considered": 2,
            "aligned_selection_rows": 1,
            "pre_final_selection_rows": 1,
            "missing_selection_rows": 0,
            "note": (
                "Stage 4 final authority resolves from stage_attempts. "
                "director_selections remains companion review history and may point to pre-final artifacts."
            ),
        }
        assert result["selection_companion_pre_final_rows"] == [
            {
                "attempt_key": attempt_key_bad,
                "ep_num": 42,
                "attempt_num": 1,
                "selection_artifact_path": "logs/artifacts/stage4/ep_0042/attempt_01/selected_before_fix__C_balanced.txt",
                "final_artifact_path": bad_artifact,
                "selection_content_hash": "hash-bad-director",
                "final_content_hash": "hash-bad-db",
                "diff_fields": ["content_hash", "artifact_path"],
            }
        ]
    finally:
        db.close()


def test_failure_analyzer_summary_reports_soft_failures(tmp_path):
    db = DBManager(tmp_path / "test_summary_soft_failure.db")
    try:
        analyzer = FailureAnalyzer(db)
        analyzer.stage_pass_rates = lambda: (_ for _ in ()).throw(RuntimeError("summary boom"))

        summary = analyzer.summary()

        assert "stage_pass_rates" not in summary
        soft_failures = tmp_path / "logs" / "soft_failures.jsonl"
        assert soft_failures.exists()
        assert "stage_pass_rates" in soft_failures.read_text(encoding="utf-8")
    finally:
        db.close()


def test_sink_alignment_uses_selection_candidate_key_from_episode_production_when_available(tmp_path):
    db = DBManager(tmp_path / "test_selection_candidate_key.db")
    try:
        attempt_key = "s4:ep7:arc1:a1:sess"
        good_artifact = "logs/artifacts/stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt"

        (tmp_path / good_artifact).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / good_artifact).write_text("patched", encoding="utf-8")

        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=7,
            arc_num=1,
            score=98,
            session_id="sess",
            attempt_key=attempt_key,
            candidate_key="A|InPlace 수정",
            content_hash="hash-ok",
            artifact_path=good_artifact,
        )
        db.save_director_selection(
            ep_num=7,
            round_num=0,
            selected_label="A",
            selected_strategy="균형 전략",
            verdict="PASS_WITH_FIX",
            stage=4,
            score=92,
            attempt_key=attempt_key,
            candidate_key="A|균형 전략",
            content_hash="hash-selected",
            artifact_path="logs/artifacts/stage4/ep_0007/attempt_01/selected_before_fix__A.txt",
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "stage": 4,
                            "episode": 7,
                            "arc": 1,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": attempt_key,
                            "final_verdict": "PASS",
                            "patch_strategy": "inplace_patch_structural",
                            "structural_attempted": True,
                            "candidate_key": "A|InPlace 수정",
                            "content_hash": "hash-ok",
                            "artifact_path": good_artifact,
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(
                {
                    "ep": 7,
                    "attempt_key": attempt_key,
                    "verdict": "PASS_WITH_FIX",
                    "initial_verdict": "PASS_WITH_FIX",
                    "final_verdict": "PASS",
                    "final_score": 98,
                    "candidate_key": "A|InPlace 수정",
                    "selection_candidate_key": "A|균형 전략",
                    "content_hash": "hash-ok",
                    "artifact_path": good_artifact,
                    "patch_trace": {"patch_strategy": "inplace_patch_structural", "structural_attempted": True},
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        db.save_attempt_raw_rationale(
            attempt_key=attempt_key,
            stage=4,
            ep_num=7,
            payload_kind="selection_contract_snapshot_raw",
            payload=json.dumps({"gate_basis": "bounded_local_repair"}, ensure_ascii=False),
        )
        db.save_attempt_raw_rationale(
            attempt_key=attempt_key,
            stage=4,
            ep_num=7,
            payload_kind="selection_surface_raw",
            payload=json.dumps(
                {
                    "selected_label": "A",
                    "selected_strategy": "균형 전략",
                    "verdict": "PASS_WITH_FIX",
                    "score": 92,
                    "candidate_key": "A|균형 전략",
                    "content_hash": "hash-selected",
                    "artifact_path": "logs/artifacts/stage4/ep_0007/attempt_01/selected_before_fix__A.txt",
                },
                ensure_ascii=False,
            ),
        )
        db.save_attempt_raw_rationale(
            attempt_key=attempt_key,
            stage=4,
            ep_num=7,
            payload_kind="feedback_provenance_raw",
            payload=json.dumps({"director_feedback": "patched after fix"}, ensure_ascii=False),
        )
        db.save_attempt_raw_rationale(
            attempt_key=attempt_key,
            stage=4,
            ep_num=7,
            payload_kind="contract_snapshot_raw",
            payload=json.dumps({"gate_basis": "bounded_local_repair"}, ensure_ascii=False),
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary()

        assert result["candidate_key_mismatches"] == []
        assert result["selection_candidate_key_mismatches"] == []
        assert result["artifact_path_mismatches"] == []
        assert result["final_authority_contract"]["pre_final_selection_rows"] == 1
        assert result["selection_companion_pre_final_rows"] == [
            {
                "attempt_key": attempt_key,
                "ep_num": 7,
                "attempt_num": 1,
                "selection_artifact_path": "logs/artifacts/stage4/ep_0007/attempt_01/selected_before_fix__A.txt",
                "final_artifact_path": good_artifact,
                "selection_content_hash": "hash-selected",
                "final_content_hash": "hash-ok",
                "diff_fields": ["content_hash", "artifact_path"],
            }
        ]
        assert result["status"] == "ok"
    finally:
        db.close()


def test_failure_analyzer_sink_alignment_summary_includes_session_decisions_when_requested(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_session.db")
    try:
        attempt_key = "s4:ep51:arc5:a1:sess_join"
        artifact_path = "logs/artifacts/stage4/ep_0051/attempt_01/final_manuscript__A_balanced.txt"
        artifact_file = tmp_path / artifact_path
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("artifact", encoding="utf-8")

        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=51,
            arc_num=5,
            score=97,
            session_id="sess_join",
            attempt_key=attempt_key,
            candidate_key="A|balanced",
            content_hash="hash-join",
            artifact_path=artifact_path,
        )
        db.save_director_selection(
            ep_num=51,
            round_num=1,
            selected_label="candidate_a",
            selected_strategy="balanced",
            verdict="PASS",
            score=97,
            stage=4,
            attempt_key=attempt_key,
            candidate_key="A|balanced",
            content_hash="hash-join",
            artifact_path=artifact_path,
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "session").mkdir(parents=True, exist_ok=True)
        (logs_dir / "session" / "decisions.jsonl").write_text(
            json.dumps(
                {
                    "stage": "stage4",
                    "ep_num": 51,
                    "round_num": 0,
                    "decision_type": "manuscript",
                    "result": "PASS",
                    "score": 97,
                    "meta": {
                        "attempt_key": attempt_key,
                        "candidate_key": "A|balanced",
                        "content_hash": "hash-join",
                        "artifact_path": artifact_path,
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(
                {
                    "ep": 51,
                    "attempt_key": attempt_key,
                    "verdict": "PASS",
                    "initial_verdict": "PASS",
                    "final_verdict": "PASS",
                    "final_score": 97,
                    "candidate_key": "A|balanced",
                    "content_hash": "hash-join",
                    "artifact_path": artifact_path,
                    "patch_trace": {"patch_strategy": "", "structural_attempted": False},
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "stage": 4,
                            "episode": 51,
                            "arc": 5,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": attempt_key,
                            "final_verdict": "PASS",
                            "candidate_key": "A|balanced",
                            "content_hash": "hash-join",
                            "artifact_path": artifact_path,
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        without_session = analyzer.sink_alignment_summary(stage=4, include_session_decisions=False)
        with_session = analyzer.sink_alignment_summary(stage=4, include_session_decisions=True)

        assert without_session["coverage"]["session_decisions"] == 0
        assert with_session["coverage"]["session_decisions"] == 1
        assert with_session["final_sink_missing"] == {}
        assert with_session["lifecycle_sink_missing"] == {}
    finally:
        db.close()


def test_failure_analyzer_sink_alignment_summary_can_filter_to_latest_session(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_session_filter.db")
    try:
        old_key = "s4:ep61:arc6:a1:old_sess"
        new_key = "s4:ep62:arc6:a1:new_sess"
        old_artifact = "logs/artifacts/stage4/ep_0061/attempt_01/final_manuscript__A.txt"
        new_artifact = "logs/artifacts/stage4/ep_0062/attempt_01/final_manuscript__A.txt"

        for artifact in (old_artifact, new_artifact):
            artifact_file = tmp_path / artifact
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            artifact_file.write_text("artifact", encoding="utf-8")

        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=61,
            arc_num=6,
            score=95,
            session_id="old_sess",
            attempt_key=old_key,
            candidate_key="A|balanced",
            content_hash="hash-old",
            artifact_path=old_artifact,
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=62,
            arc_num=6,
            score=97,
            session_id="new_sess",
            attempt_key=new_key,
            candidate_key="A|balanced",
            content_hash="hash-new",
            artifact_path=new_artifact,
        )
        db.save_director_selection(
            ep_num=61,
            round_num=1,
            selected_label="candidate_a",
            selected_strategy="balanced",
            verdict="PASS",
            score=95,
            stage=4,
            attempt_key=old_key,
            candidate_key="A|balanced",
            content_hash="hash-old",
            artifact_path=old_artifact,
        )
        db.save_director_selection(
            ep_num=62,
            round_num=1,
            selected_label="candidate_a",
            selected_strategy="balanced",
            verdict="PASS",
            score=97,
            stage=4,
            attempt_key=new_key,
            candidate_key="A|balanced",
            content_hash="hash-new",
            artifact_path=new_artifact,
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "episode_production.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "ep": 61,
                            "attempt_key": old_key,
                            "verdict": "PASS",
                            "initial_verdict": "PASS",
                            "final_verdict": "PASS",
                            "final_score": 95,
                            "candidate_key": "A|balanced",
                            "content_hash": "hash-old",
                            "artifact_path": old_artifact,
                            "patch_trace": {"patch_strategy": "", "structural_attempted": False},
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "ep": 62,
                            "attempt_key": new_key,
                            "verdict": "PASS",
                            "initial_verdict": "PASS",
                            "final_verdict": "PASS",
                            "final_score": 97,
                            "candidate_key": "A|balanced",
                            "content_hash": "hash-new",
                            "artifact_path": new_artifact,
                            "patch_trace": {"patch_strategy": "", "structural_attempted": False},
                        },
                        ensure_ascii=False,
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "stage": 4,
                            "episode": 61,
                            "arc": 6,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": old_key,
                            "final_verdict": "PASS",
                            "candidate_key": "A|balanced",
                            "content_hash": "hash-old",
                            "artifact_path": old_artifact,
                        },
                        {
                            "stage": 4,
                            "episode": 62,
                            "arc": 6,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": new_key,
                            "final_verdict": "PASS",
                            "candidate_key": "A|balanced",
                            "content_hash": "hash-new",
                            "artifact_path": new_artifact,
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        for ep_num, attempt_key, artifact_path, content_hash in (
            (61, old_key, old_artifact, "hash-old"),
            (62, new_key, new_artifact, "hash-new"),
        ):
            db.save_attempt_raw_rationale(
                attempt_key=attempt_key,
                stage=4,
                ep_num=ep_num,
                payload_kind="selection_contract_snapshot_raw",
                payload=json.dumps({"gate_basis": "direct_pass"}, ensure_ascii=False),
            )
            db.save_attempt_raw_rationale(
                attempt_key=attempt_key,
                stage=4,
                ep_num=ep_num,
                payload_kind="selection_surface_raw",
                payload=json.dumps(
                    {
                        "selected_label": "candidate_a",
                        "selected_strategy": "balanced",
                        "verdict": "PASS",
                        "score": 95 if attempt_key == old_key else 97,
                        "candidate_key": "A|balanced",
                        "content_hash": content_hash,
                        "artifact_path": artifact_path,
                    },
                    ensure_ascii=False,
                ),
            )
            db.save_attempt_raw_rationale(
                attempt_key=attempt_key,
                stage=4,
                ep_num=ep_num,
                payload_kind="feedback_provenance_raw",
                payload=json.dumps({"director_feedback": "pass"}, ensure_ascii=False),
            )
            db.save_attempt_raw_rationale(
                attempt_key=attempt_key,
                stage=4,
                ep_num=ep_num,
                payload_kind="contract_snapshot_raw",
                payload=json.dumps({"gate_basis": "direct_pass"}, ensure_ascii=False),
            )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        unfiltered = analyzer.sink_alignment_summary(stage=4)
        filtered = analyzer.sink_alignment_summary(stage=4, session_id="new_sess")

        assert unfiltered["status"] == "ok"
        assert unfiltered["final_sink_missing"] == {}
        assert filtered["status"] == "ok"
        assert filtered["session_filter"] == "new_sess"
        assert filtered["attempts_considered"] == 1
        assert filtered["coverage"]["stage_attempts"] == 1
        assert filtered["coverage"]["pass_rate_monitor"] == 1
        assert filtered["coverage"]["director_selections"] == 1
        assert filtered["coverage"]["episode_production"] == 1
    finally:
        db.close()


def test_sink_alignment_ignores_lifecycle_only_episode_production_rows_for_final_score_and_artifact_checks(tmp_path):
    db = DBManager(tmp_path / "test_stage4_pathology_alignment.db")
    try:
        attempt_key = "s4:ep81:arc1:a1:sess_path"
        artifact_path = "logs/artifacts/stage4/ep_0081/attempt_01/rejected_best__C_balanced.txt"
        artifact_file = tmp_path / artifact_path
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("artifact", encoding="utf-8")

        db.save_stage_attempt(
            stage=4,
            verdict="REJECT",
            attempt_num=1,
            ep_num=81,
            arc_num=1,
            score=44,
            session_id="sess_path",
            attempt_key=attempt_key,
            candidate_key="C|balanced",
            content_hash="hash-path",
            artifact_path=artifact_path,
            selection_reason="selection",
            verdict_reason="reject",
        )
        db.save_director_selection(
            ep_num=81,
            round_num=1,
            selected_label="C",
            selected_strategy="balanced",
            verdict="REJECT",
            stage=4,
            score=44,
            attempt_key=attempt_key,
            candidate_key="C|균형 전략",
            content_hash="hash-path",
            artifact_path="logs/artifacts/stage4/ep_0081/attempt_01/rejected_best__C.txt",
            selection_reason="selection",
            verdict_reason="reject",
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(
                {
                    "event": "STAGE4_RETRY_PATHOLOGY",
                    "ep": 81,
                    "attempt_key": attempt_key,
                    "result": "REJECT",
                    "score": 99,
                    "candidate_key": "C|balanced",
                    "content_hash": "hash-path",
                    "artifact_path": "",
                    "selection_candidate_key": "C|balanced",
                    "repair_contract": {"subtype": "수치"},
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary(stage=4, session_id="sess_path")

        assert result["coverage"]["episode_production"] == 1
        assert result["final_score_mismatches"] == []
        assert result["artifact_metadata_missing"] == []
        assert result["selection_candidate_key_mismatches"] == []
    finally:
        db.close()


def test_sink_alignment_prefers_authoritative_episode_production_row_over_lifecycle_only_duplicate(tmp_path):
    db = DBManager(tmp_path / "test_stage4_pathology_prefer_authoritative.db")
    try:
        attempt_key = "s4:ep82:arc1:a1:sess_path"
        artifact_path = "logs/artifacts/stage4/ep_0082/attempt_01/rejected_best__C_balanced.txt"
        artifact_file = tmp_path / artifact_path
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("artifact", encoding="utf-8")

        db.save_stage_attempt(
            stage=4,
            verdict="REJECT",
            attempt_num=1,
            ep_num=82,
            arc_num=1,
            score=44,
            session_id="sess_path",
            attempt_key=attempt_key,
            candidate_key="C|balanced",
            content_hash="hash-path",
            artifact_path=artifact_path,
            selection_reason="selection",
            verdict_reason="reject",
            advisory_flags={
                "gate_semantics": {
                    "director_verdict": "REJECT",
                    "gate_basis": "continuity_firewall",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "scope_origin": {
                        "fix_scope": "director_authoritative",
                        "authoritative_fix_scope": "director_authoritative",
                        "repair_scope": "runtime_lane",
                    },
                },
                "repair_contract": {
                    "subtype": "수치",
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                },
                "scope_authority": {
                    "fix_scope": "inplace",
                    "repair_scope": "inplace",
                    "authoritative_fix_scope": "inplace",
                    "widened": False,
                },
                "retry_budget_axes": {"repair": "rewrite_regenerate"},
            },
        )
        db.save_director_selection(
            ep_num=82,
            round_num=1,
            selected_label="C",
            selected_strategy="balanced",
            verdict="REJECT",
            stage=4,
            score=44,
            attempt_key=attempt_key,
            candidate_key="C|balanced",
            content_hash="hash-path",
            artifact_path="logs/artifacts/stage4/ep_0082/attempt_01/rejected_best__C.txt",
            selection_reason="selection",
            verdict_reason="reject",
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        authoritative_row = {
            "ep": 82,
            "attempt_key": attempt_key,
            "verdict": "REJECT",
            "initial_verdict": "REJECT",
            "final_verdict": "REJECT",
            "score": 44,
            "director_verdict": "REJECT",
            "gate_basis": "continuity_firewall",
            "repair_scope": "inplace",
            "fix_scope": "inplace",
            "authoritative_fix_scope": "inplace",
            "candidate_key": "C|balanced",
            "content_hash": "hash-path",
            "artifact_path": artifact_path,
            "selection_candidate_key": "C|balanced",
            "selection_reason": "selection",
            "verdict_reason": "reject",
            "repair_contract": {"subtype": "수치", "fix_scope": "inplace"},
            "scope_authority": {
                "fix_scope": "inplace",
                "authoritative_fix_scope": "inplace",
                "widened": False,
            },
            "flags": {"retry_budget_axes": {"repair": "rewrite_regenerate"}},
            "patch_trace": {},
        }
        pathology_row = {
            "event": "STAGE4_RETRY_PATHOLOGY",
            "ep": 82,
            "attempt_key": attempt_key,
            "result": "REJECT",
            "score": 99,
            "candidate_key": "C|balanced",
            "content_hash": "hash-path",
            "artifact_path": "",
            "selection_candidate_key": "C|balanced",
            "repair_contract": {"subtype": "수치"},
        }
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(authoritative_row, ensure_ascii=False)
            + "\n"
            + json.dumps(pathology_row, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary(stage=4, session_id="sess_path")

        assert result["coverage"]["episode_production"] == 1
        missing_entries = [
            item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == attempt_key
        ]
        assert not any("episode_production" in item["sinks"] for item in missing_entries)
        assert result["repair_contract_subtype_mismatches"] == []
        assert result["scope_authority_authoritative_fix_scope_mismatches"] == []
    finally:
        db.close()


def test_load_episode_production_alignment_sink_merges_lifecycle_runtime_scope_authority(tmp_path):
    db = DBManager(tmp_path / "test_stage4_pathology_merge_scope.db")
    try:
        attempt_key = "s4:ep84:arc1:a1:sess_scope"
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        authoritative_row = {
            "ep": 84,
            "attempt_key": attempt_key,
            "verdict": "REJECT",
            "initial_verdict": "REJECT",
            "final_verdict": "REJECT",
            "score": 44,
            "director_verdict": "REJECT",
            "gate_basis": "continuity_firewall",
            "repair_scope": "partial",
            "candidate_key": "A|balanced",
            "content_hash": "hash-scope",
            "artifact_path": "logs/artifacts/stage4/ep_0084/attempt_01/rejected_best__A_balanced.txt",
            "selection_candidate_key": "A|balanced",
            "selection_reason": "selection",
            "verdict_reason": "reject",
            "repair_contract": {
                "subtype": "수치",
                "fix_scope": "partial",
                "repair_scope": "partial",
                "authoritative_fix_scope": "partial",
                "provenance": "director_authored",
            },
            "scope_authority": {
                "fix_scope": "partial",
                "repair_scope": "partial",
                "authoritative_fix_scope": "partial",
                "widened": False,
            },
            "fix_pack": {"target_kind": "scene_model", "patch_targets": ["scene_4"]},
            "patch_trace": {},
        }
        pathology_row = {
            "event": "STAGE4_RETRY_PATHOLOGY",
            "ep": 84,
            "attempt_key": attempt_key,
            "result": "REJECT",
            "score": 71,
            "gate_basis": "continuity_firewall",
            "repair_scope": "partial",
            "repair_contract": {"subtype": "수치", "fix_scope": "partial", "repair_scope": "partial"},
            "scope_authority": {
                "fix_scope": "full",
                "repair_scope": "partial",
                "authoritative_fix_scope": "partial",
                "widened": True,
            },
        }
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(authoritative_row, ensure_ascii=False)
            + "\n"
            + json.dumps(pathology_row, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer._load_episode_production_alignment_sink(stage=4, lookback=10, session_id="sess_scope")

        assert result[attempt_key]["artifact_path"] == authoritative_row["artifact_path"]
        assert result[attempt_key]["fix_pack_target_kind"] == "scene_model"
        assert result[attempt_key]["repair_contract_provenance"] == "director_authored"
        assert result[attempt_key]["scope_authority_fix_scope"] == "full"
        assert result[attempt_key]["scope_authority_authoritative_fix_scope"] == "partial"
        assert result[attempt_key]["scope_authority_widened"] is True
    finally:
        db.close()


def test_load_episode_production_alignment_sink_backfills_empty_rationale_from_reason(tmp_path):
    db = DBManager(tmp_path / "test_stage4_episode_reason_backfill.db")
    try:
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        attempt_key = "s4:ep84:arc1:a1:sess_reason_backfill"
        row = {
            "ep": 84,
            "attempt_key": attempt_key,
            "verdict": "PASS",
            "initial_verdict": "PASS",
            "final_verdict": "PASS",
            "final_score": 88,
            "candidate_key": "A|balanced",
            "content_hash": "hash-reason",
            "artifact_path": "logs/artifacts/stage4/ep_0084/attempt_01/final.txt",
            "reason": "fallback rationale from reason",
            "selection_reason": "",
            "verdict_reason": "",
            "patch_trace": {},
        }
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(row, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer._load_episode_production_alignment_sink(
            stage=4,
            lookback=10,
            session_id="sess_reason_backfill",
        )

        assert result[attempt_key]["selection_reason"] == "fallback rationale from reason"
        assert result[attempt_key]["verdict_reason"] == "fallback rationale from reason"
    finally:
        db.close()


def test_sink_alignment_backfills_stage_attempt_repair_contract_from_nested_gate_semantics(tmp_path):
    db = DBManager(tmp_path / "test_stage4_nested_gate_repair_backfill.db")
    try:
        attempt_key = "s4:ep83:arc1:a1:sess_nested"
        artifact_path = "logs/artifacts/stage4/ep_0083/attempt_01/rejected_best__A_balanced.txt"
        artifact_file = tmp_path / artifact_path
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("artifact", encoding="utf-8")

        db.save_stage_attempt(
            stage=4,
            verdict="REJECT",
            attempt_num=1,
            ep_num=83,
            arc_num=1,
            score=52,
            session_id="sess_nested",
            attempt_key=attempt_key,
            candidate_key="A|balanced",
            content_hash="hash-nested",
            artifact_path=artifact_path,
            selection_reason="selection",
            verdict_reason="reject",
            advisory_flags={
                "gate_semantics": {
                    "director_verdict": "REJECT",
                    "gate_basis": "continuity_firewall",
                    "repair_scope": "inplace",
                    "repair_contract": {"subtype": "수치", "provenance": "gate_semantics"},
                    "scope_authority": {
                        "fix_scope": "inplace",
                        "authoritative_fix_scope": "inplace",
                        "widened": False,
                    },
                },
                "repair_contract": {"fix_scope": "inplace"},
                "scope_authority": {"fix_scope": "inplace"},
            },
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        authoritative_row = {
            "ep": 83,
            "attempt_key": attempt_key,
            "verdict": "REJECT",
            "initial_verdict": "REJECT",
            "final_verdict": "REJECT",
            "score": 52,
            "director_verdict": "REJECT",
            "gate_basis": "continuity_firewall",
            "repair_scope": "inplace",
            "candidate_key": "A|balanced",
            "content_hash": "hash-nested",
            "artifact_path": artifact_path,
            "selection_candidate_key": "A|balanced",
            "selection_reason": "selection",
            "verdict_reason": "reject",
            "repair_contract": {"subtype": "수치", "provenance": "gate_semantics", "fix_scope": "inplace"},
            "scope_authority": {
                "fix_scope": "inplace",
                "authoritative_fix_scope": "inplace",
                "widened": False,
            },
            "patch_trace": {},
        }
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(authoritative_row, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary(stage=4, session_id="sess_nested")

        missing_entries = [
            item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == attempt_key
        ]
        assert not any(
            item["field"] == "repair_contract_subtype" and "stage_attempts" in item["sinks"] for item in missing_entries
        )
        assert not any(
            item["field"] == "repair_contract_provenance" and "stage_attempts" in item["sinks"]
            for item in missing_entries
        )
        assert result["repair_contract_subtype_mismatches"] == []
        assert result["repair_contract_provenance_mismatches"] == []
    finally:
        db.close()


def test_collect_sink_alignment_gate_repair_results_backfills_stage_attempt_from_consensus_runtime_sinks(tmp_path):
    db = DBManager(tmp_path / "test_stage4_consensus_backfill.db")
    try:
        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        attempt_key = "s4:ep85:arc1:a1:sess_backfill"
        result = analyzer._collect_sink_alignment_gate_repair_results(
            stage=4,
            attempt_key=attempt_key,
            stage_attempts={
                attempt_key: {
                    "gate_basis": "",
                    "repair_scope": "",
                    "fix_pack_target_kind": "",
                    "fix_pack_patch_targets": [],
                    "repair_contract_provenance": "",
                    "scope_authority_fix_scope": "",
                    "scope_authority_authoritative_fix_scope": "",
                }
            },
            pass_rate_monitor={},
            director_selections={},
            session_decisions={
                attempt_key: {
                    "gate_basis": "bounded_local_repair",
                    "repair_scope": "partial",
                    "fix_pack_target_kind": "scene_model",
                    "fix_pack_patch_targets": ["scene_4"],
                    "repair_contract_provenance": "director_authored",
                    "scope_authority_fix_scope": "partial",
                    "scope_authority_authoritative_fix_scope": "inplace",
                    "scope_authority_widened": True,
                }
            },
            episode_production={
                attempt_key: {
                    "gate_basis": "bounded_local_repair",
                    "repair_scope": "partial",
                    "fix_pack_target_kind": "scene_model",
                    "fix_pack_patch_targets": ["scene_4"],
                    "repair_contract_provenance": "director_authored",
                    "scope_authority_fix_scope": "partial",
                    "scope_authority_authoritative_fix_scope": "inplace",
                    "scope_authority_widened": True,
                }
            },
            authority_row=None,
        )

        missing_entries = [
            item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == attempt_key
        ]
        assert not any(item["field"] == "gate_basis" and "stage_attempts" in item["sinks"] for item in missing_entries)
        assert not any(
            item["field"] == "repair_scope" and "stage_attempts" in item["sinks"] for item in missing_entries
        )
        assert not any(
            item["field"] == "fix_pack_target_kind" and "stage_attempts" in item["sinks"] for item in missing_entries
        )
        assert not any(
            item["field"] == "fix_pack_patch_targets" and "stage_attempts" in item["sinks"] for item in missing_entries
        )
        assert not any(
            item["field"] == "repair_contract_provenance" and "stage_attempts" in item["sinks"]
            for item in missing_entries
        )
        assert not any(
            item["field"] == "scope_authority_fix_scope" and "stage_attempts" in item["sinks"]
            for item in missing_entries
        )
        assert not any(
            item["field"] == "scope_authority_authoritative_fix_scope" and "stage_attempts" in item["sinks"]
            for item in missing_entries
        )
        assert not any(
            item["field"] == "scope_authority_widened" and "stage_attempts" in item["sinks"] for item in missing_entries
        )
        assert result["gate_basis_mismatches"] == []
        assert result["repair_scope_mismatches"] == []
        assert result["fix_pack_target_kind_mismatches"] == []
        assert result["fix_pack_patch_targets_mismatches"] == []
        assert result["repair_contract_provenance_mismatches"] == []
        assert result["scope_authority_fix_scope_mismatches"] == []
        assert result["scope_authority_authoritative_fix_scope_mismatches"] == []
        assert result["scope_authority_widened_mismatches"] == []
    finally:
        db.close()


def test_collect_sink_alignment_gate_repair_results_ignores_pre_final_director_companion_mismatch(tmp_path):
    db = DBManager(tmp_path / "test_stage4_pre_final_companion_gate_repair.db")
    try:
        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        attempt_key = "s4:ep86:arc1:a1:sess_prefinal"
        result = analyzer._collect_sink_alignment_gate_repair_results(
            stage=4,
            attempt_key=attempt_key,
            stage_attempts={
                attempt_key: {
                    "director_verdict": "REJECT",
                    "gate_basis": "patch_reaudit_fail",
                    "repair_scope": "partial",
                    "scope_authority_fix_scope": "full",
                    "scope_authority_widened": True,
                }
            },
            pass_rate_monitor={},
            director_selections={
                attempt_key: {
                    "director_verdict": "PASS",
                    "gate_basis": "strong_advisory_escalation",
                    "repair_scope": "partial",
                    "scope_authority_fix_scope": "partial",
                    "scope_authority_widened": False,
                }
            },
            session_decisions={
                attempt_key: {
                    "director_verdict": "REJECT",
                    "gate_basis": "patch_reaudit_fail",
                    "repair_scope": "partial",
                    "scope_authority_fix_scope": "full",
                    "scope_authority_widened": True,
                }
            },
            episode_production={
                attempt_key: {
                    "director_verdict": "REJECT",
                    "gate_basis": "patch_reaudit_fail",
                    "repair_scope": "partial",
                    "scope_authority_fix_scope": "full",
                    "scope_authority_widened": True,
                }
            },
            authority_row={"selection_companion_status": "pre_final_candidate"},
        )

        assert result["director_verdict_mismatches"] == []
        assert result["gate_basis_mismatches"] == []
        assert result["scope_authority_fix_scope_mismatches"] == []
        assert result["scope_authority_widened_mismatches"] == []
    finally:
        db.close()


def test_collect_sink_alignment_artifact_results_ignores_pre_final_director_companion_candidate_mismatch(tmp_path):
    db = DBManager(tmp_path / "test_stage4_pre_final_companion_artifact.db")
    try:
        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        attempt_key = "s4:ep86:arc1:a1:sess_prefinal"
        result = analyzer._collect_sink_alignment_artifact_results(
            attempt_key=attempt_key,
            stage_attempts={},
            pass_rate_monitor={},
            director_selections={
                attempt_key: {
                    "candidate_key": "C|balanced",
                }
            },
            session_decisions={},
            episode_production={
                attempt_key: {
                    "candidate_key": "A|tension",
                    "content_hash": "hash-a",
                    "artifact_path": "logs/artifacts/stage4/ep_0086/attempt_01/rejected_best__A_tension.txt",
                    "final_sink_authoritative": True,
                    "selection_candidate_key": "A|tension",
                }
            },
            authority_row={"selection_companion_status": "pre_final_candidate"},
        )

        assert result["selection_candidate_key_mismatches"] == []
    finally:
        db.close()


def test_collect_sink_alignment_gate_repair_results_ignores_non_local_scene_model_patch_target_noise(tmp_path):
    db = DBManager(tmp_path / "test_stage4_non_local_scene_model_patch_target_noise.db")
    try:
        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        attempt_key = "s4:ep87:arc1:a1:sess_nonlocal"
        result = analyzer._collect_sink_alignment_gate_repair_results(
            stage=4,
            attempt_key=attempt_key,
            stage_attempts={
                attempt_key: {
                    "gate_basis": "strong_advisory_escalation_non_local_fix",
                    "fix_pack_target_kind": "scene_model",
                    "fix_pack_patch_targets": ["scene-model rewrite boundary"],
                    "repair_contract_provenance": "runtime_synthesized",
                }
            },
            pass_rate_monitor={
                attempt_key: {
                    "gate_basis": "strong_advisory_escalation_non_local_fix",
                    "fix_pack_target_kind": "scene_model",
                    "fix_pack_patch_targets": [],
                    "repair_contract_provenance": "runtime_synthesized",
                }
            },
            director_selections={},
            session_decisions={
                attempt_key: {
                    "gate_basis": "strong_advisory_escalation_non_local_fix",
                    "fix_pack_target_kind": "scene_model",
                    "fix_pack_patch_targets": ["rewrite boundary"],
                    "repair_contract_provenance": "runtime_synthesized",
                }
            },
            episode_production={
                attempt_key: {
                    "gate_basis": "strong_advisory_escalation_non_local_fix",
                    "fix_pack_target_kind": "scene_model",
                    "fix_pack_patch_targets": ["scene-model rewrite boundary"],
                    "repair_contract_provenance": "runtime_synthesized",
                    "repair_contract": {
                        "target_kind": "scene_model",
                        "provenance": "runtime_synthesized",
                    },
                }
            },
            authority_row=None,
        )

        missing_entries = [
            item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == attempt_key
        ]
        assert not any(item["field"] == "fix_pack_patch_targets" for item in missing_entries)
        assert result["fix_pack_patch_targets_mismatches"] == []
        assert result["repair_contract_provenance_mismatches"] == []
    finally:
        db.close()


def test_load_session_decision_entries_preserves_stage4_rationale_and_provenance_fields(tmp_path):
    db = DBManager(tmp_path / "test_session_decisions_stage4.db")
    try:
        session_dir = tmp_path / "logs" / "session"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "decisions.jsonl").write_text(
            json.dumps(
                {
                    "stage": "stage4",
                    "ep_num": 9,
                    "round_num": 0,
                    "decision_type": "manuscript",
                    "result": "PASS",
                    "score": 97,
                    "meta": {
                        "attempt_key": "s4:ep9:arc1:a1:sess_meta",
                        "candidate_key": "A|balanced",
                        "content_hash": "hash-stage4",
                        "artifact_path": "logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__A_balanced.txt",
                        "selection_reason": "best candidate",
                        "verdict_reason": "final pass rationale",
                        "comparison_notes": "candidate A preserved the ending cadence best",
                        "selected_candidate_advisory_struct": {
                            "quality_risk": True,
                            "python_warnings": [{"category": "cadence", "message": "tighten the closing beat"}],
                        },
                        "reason": "final pass rationale",
                        "runtime_advisory": "[advisory] keep continuity",
                        "retry_directives": "preserve the ending cadence",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        rows = analyzer._load_session_decision_entries(stage=4)

        assert len(rows) == 1
        assert rows[0]["attempt_key"] == "s4:ep9:arc1:a1:sess_meta"
        assert rows[0]["selection_reason"] == "best candidate"
        assert rows[0]["verdict_reason"] == "final pass rationale"
        assert rows[0]["comparison_notes"] == "candidate A preserved the ending cadence best"
        assert rows[0]["selected_candidate_advisory_struct"]["quality_risk"] is True
        assert rows[0]["runtime_advisory"] == "[advisory] keep continuity"
        assert rows[0]["retry_directives"] == "preserve the ending cadence"
    finally:
        db.close()


def test_load_session_decision_entries_ignores_legacy_selected_candidate_advisory_without_struct(tmp_path):
    db = DBManager(tmp_path / "test_stage3_legacy_advisory_shape.db")
    try:
        decisions_path = tmp_path / "logs" / "session" / "decisions.jsonl"
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        decisions_path.write_text(
            json.dumps(
                {
                    "stage": "stage3",
                    "ep_num": 7,
                    "decision_type": "blueprint",
                    "result": "PASS",
                    "score": 88,
                    "meta": {
                        "attempt_key": "s3:ep7:arc2:a1:sess_legacy",
                        "candidate_key": "B|balanced",
                        "content_hash": "hash-stage3",
                        "artifact_path": "logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__B_balanced.json",
                        "selection_reason": "best candidate",
                        "selected_candidate_advisory": {"quality_risk": True},
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        rows = analyzer._load_session_decision_entries(stage=3)

        assert len(rows) == 1
        assert rows[0]["attempt_key"] == "s3:ep7:arc2:a1:sess_legacy"
        assert rows[0]["selected_candidate_advisory_struct"] == {}
    finally:
        db.close()


def test_failure_analyzer_sink_alignment_summary_aligns_stage3_session_rationale_with_director_selection(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_stage3_rationale.db")
    try:
        attempt_key = "s3:ep12:arc1:a1:sess_stage3"
        artifact_path = "logs/artifacts/stage3/ep_0012/attempt_01/final_blueprint__dialogue_focused.json"
        artifact_file = tmp_path / artifact_path
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("{}", encoding="utf-8")

        db.save_stage_attempt(
            stage=3,
            verdict="PASS",
            attempt_num=1,
            ep_num=12,
            arc_num=1,
            score=93,
            session_id="sess_stage3",
            attempt_key=attempt_key,
            candidate_key="dialogue_focused",
            content_hash="hash-stage3",
            artifact_path=artifact_path,
            selection_reason="후보 B가 감정선과 연속성 연결이 가장 안정적",
            verdict_reason="구조 리스크 없이 바로 사용 가능",
            fix_scope="inplace",
            runtime_advisory="[stage3 advisory] opening continuity locked",
            retry_directives="preserve arc_start_state carryover",
            advisory_flags={
                "comparison_notes": "후보 B가 opening relay와 감정선 연결을 가장 안정적으로 유지",
                "selected_candidate_advisory_struct": {
                    "candidate_index": 1,
                    "quality_risk": True,
                    "python_warnings": [
                        {"category": "npc_density", "message": "Arc NPC mention is thin"},
                    ],
                },
            },
        )
        db.save_director_selection(
            ep_num=12,
            round_num=1,
            selected_label="B",
            selected_strategy="dialogue_focused",
            verdict="PASS",
            score=93,
            selection_reason="후보 B가 감정선과 연속성 연결이 가장 안정적",
            fix_scope="inplace",
            stage=3,
            verdict_reason="구조 리스크 없이 바로 사용 가능",
            attempt_key=attempt_key,
            candidate_key="dialogue_focused",
            content_hash="hash-stage3",
            artifact_path=artifact_path,
            runtime_advisory="[stage3 advisory] opening continuity locked",
            retry_directives="preserve arc_start_state carryover",
            advisory_warnings={
                "comparison_notes": "후보 B가 opening relay와 감정선 연결을 가장 안정적으로 유지",
                "selected_candidate_advisory_struct": {
                    "candidate_index": 1,
                    "quality_risk": True,
                    "python_warnings": [
                        {"category": "npc_density", "message": "Arc NPC mention is thin"},
                    ],
                },
            },
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "session").mkdir(parents=True, exist_ok=True)
        (logs_dir / "session" / "decisions.jsonl").write_text(
            json.dumps(
                {
                    "stage": "stage3",
                    "ep_num": 12,
                    "round_num": 0,
                    "decision_type": "blueprint",
                    "result": "PASS",
                    "score": 93,
                    "meta": {
                        "attempt_key": attempt_key,
                        "candidate_key": "dialogue_focused",
                        "content_hash": "hash-stage3",
                        "artifact_path": artifact_path,
                        "reason": "구조 리스크 없이 바로 사용 가능",
                        "selection_reason": "후보 B가 감정선과 연속성 연결이 가장 안정적",
                        "verdict_reason": "구조 리스크 없이 바로 사용 가능",
                        "comparison_notes": "후보 B가 opening relay와 감정선 연결을 가장 안정적으로 유지",
                        "selected_candidate_advisory_struct": {
                            "candidate_index": 1,
                            "quality_risk": True,
                            "python_warnings": [
                                {"category": "npc_density", "message": "Arc NPC mention is thin"},
                            ],
                        },
                        "fix_scope": "inplace",
                        "runtime_advisory": "[stage3 advisory] opening continuity locked",
                        "retry_directives": "preserve arc_start_state carryover",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(
                {
                    "ep": 14,
                    "attempt_key": attempt_key,
                    "verdict": "PASS",
                    "initial_verdict": "PASS",
                    "final_verdict": "PASS",
                    "final_score": 96,
                    "candidate_key": "balanced",
                    "content_hash": "hash-stage4",
                    "artifact_path": artifact_path,
                    "selection_reason": "후보 A가 후반 리듬과 장면 연결이 가장 안정적",
                    "verdict_reason": "수정 없이 바로 사용 가능",
                    "patch_trace": {"patch_strategy": "", "structural_attempted": False},
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "stage": 3,
                            "episode": 12,
                            "arc": 1,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": attempt_key,
                            "final_verdict": "PASS",
                            "candidate_key": "dialogue_focused",
                            "content_hash": "hash-stage3",
                            "artifact_path": artifact_path,
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary(stage=3, include_session_decisions=True)

        assert result["coverage"]["director_selections"] == 1
        assert result["coverage"]["session_decisions"] == 1
        assert result["selection_reason_mismatches"] == []
        assert result["verdict_reason_mismatches"] == []
        assert result["comparison_notes_mismatches"] == []
        assert result["selected_candidate_advisory_mismatches"] == []
        assert result["fix_scope_mismatches"] == []
        assert result["runtime_advisory_mismatches"] == []
        assert result["retry_directives_mismatches"] == []
        assert result["rationale_metadata_missing"] == []
        assert result["top_issue_headline"] == {
            "headline": "Stage3 sink_alignment_clean",
            "priority": "OK",
            "focus": "sink_alignment_clean",
            "count": 0,
            "next_action": "No immediate sink-alignment follow-up required.",
        }
        assert result["operator_summary"] == (
            "Stage3 sink alignment ok: 1 attempt(s), final 1/1, lifecycle 0/0, "
            "coverage gaps 0, sink issues 0. "
            "Top issue: Stage3 sink_alignment_clean. "
            "Next: No immediate sink-alignment follow-up required."
        )
        assert result["status"] == "ok"
    finally:
        db.close()


def test_failure_analyzer_sink_alignment_summary_flags_stage3_runtime_rationale_mismatch(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_stage3_runtime_rationale.db")
    try:
        attempt_key = "s3:ep13:arc1:a1:sess_stage3_mismatch"
        artifact_path = "logs/artifacts/stage3/ep_0013/attempt_01/final_blueprint__balanced.json"
        artifact_file = tmp_path / artifact_path
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("{}", encoding="utf-8")

        db.save_stage_attempt(
            stage=3,
            verdict="PASS_WITH_FIX",
            attempt_num=1,
            ep_num=13,
            arc_num=1,
            score=89,
            session_id="sess_stage3_mismatch",
            attempt_key=attempt_key,
            candidate_key="balanced",
            content_hash="hash-stage3-mismatch",
            artifact_path=artifact_path,
            selection_reason="후보 A가 구조는 가장 안정적",
            verdict_reason="소형 opening drift만 보정하면 사용 가능",
            fix_scope="inplace",
            runtime_advisory="[stage3 advisory] preserve opening-state continuity",
            retry_directives="carry forward the same capital packet",
        )
        db.save_director_selection(
            ep_num=13,
            round_num=1,
            selected_label="A",
            selected_strategy="balanced",
            verdict="PASS_WITH_FIX",
            score=89,
            selection_reason="후보 A가 구조는 가장 안정적",
            fix_scope="inplace",
            stage=3,
            verdict_reason="소형 opening drift만 보정하면 사용 가능",
            attempt_key=attempt_key,
            candidate_key="balanced",
            content_hash="hash-stage3-mismatch",
            artifact_path=artifact_path,
            runtime_advisory="[stage3 advisory] preserve opening-state continuity",
            retry_directives="carry forward the same capital packet",
        )

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "session").mkdir(parents=True, exist_ok=True)
        (logs_dir / "session" / "decisions.jsonl").write_text(
            json.dumps(
                {
                    "stage": "stage3",
                    "ep_num": 13,
                    "round_num": 0,
                    "decision_type": "blueprint",
                    "result": "PASS_WITH_FIX",
                    "score": 89,
                    "meta": {
                        "attempt_key": attempt_key,
                        "candidate_key": "balanced",
                        "content_hash": "hash-stage3-mismatch",
                        "artifact_path": artifact_path,
                        "reason": "소형 opening drift만 보정하면 사용 가능",
                        "selection_reason": "후보 A가 구조는 가장 안정적",
                        "verdict_reason": "소형 opening drift만 보정하면 사용 가능",
                        "fix_scope": "inplace",
                        "runtime_advisory": "[stage3 advisory] stale prompt packet leaked",
                        "retry_directives": "rewrite the opening packet from scratch",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(
                {
                    "ep": 15,
                    "attempt_key": attempt_key,
                    "verdict": "PASS_WITH_FIX",
                    "initial_verdict": "PASS_WITH_FIX",
                    "final_verdict": "PASS_WITH_FIX",
                    "final_score": 88,
                    "candidate_key": "balanced",
                    "content_hash": "hash-stage4-mismatch",
                    "artifact_path": artifact_path,
                    "selection_reason": "후보 A가 전체 구조는 가장 안정적",
                    "verdict_reason": "소형 리듬 보정만 하면 사용 가능",
                    "patch_trace": {"patch_strategy": "inplace", "structural_attempted": False},
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "stage": 3,
                            "episode": 13,
                            "arc": 1,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": attempt_key,
                            "final_verdict": "PASS_WITH_FIX",
                            "candidate_key": "balanced",
                            "content_hash": "hash-stage3-mismatch",
                            "artifact_path": artifact_path,
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary(stage=3, include_session_decisions=True)

        assert len(result["runtime_advisory_mismatches"]) == 1
        assert result["runtime_advisory_mismatches"][0]["attempt_key"] == attempt_key
        assert len(result["retry_directives_mismatches"]) == 1
        assert result["retry_directives_mismatches"][0]["attempt_key"] == attempt_key
        assert result["top_issue_headline"] == {
            "headline": "P2 structured_sink_drift x2",
            "priority": "P2",
            "focus": "structured_sink_drift",
            "count": 2,
            "next_action": "Inspect structured sink mismatches before trusting cross-sink contract parity.",
        }
        assert result["operator_summary"] == (
            "Stage3 sink alignment warn: 1 attempt(s), final 1/1, lifecycle 0/0, "
            "coverage gaps 0, sink issues 2. "
            "Top issue: P2 structured_sink_drift x2. "
            "Next: Inspect structured sink mismatches before trusting cross-sink contract parity."
        )
        assert result["status"] == "warn"
    finally:
        db.close()


def test_failure_analyzer_sink_alignment_summary_aligns_stage4_session_rationale_with_director_selection(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_stage4_rationale.db")
    try:
        attempt_key = "s4:ep14:arc2:a1:sess_stage4"
        artifact_path = "logs/artifacts/stage4/ep_0014/attempt_01/final_manuscript__balanced.txt"
        artifact_file = tmp_path / artifact_path
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("stage4 artifact", encoding="utf-8")

        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            attempt_num=1,
            ep_num=14,
            arc_num=2,
            score=96,
            session_id="sess_stage4",
            attempt_key=attempt_key,
            candidate_key="balanced",
            content_hash="hash-stage4",
            artifact_path=artifact_path,
            selection_reason="후보 A가 후반 리듬과 장면 연결이 가장 안정적",
            verdict_reason="수정 없이 바로 사용 가능",
            fix_scope="inplace",
            runtime_advisory="[stage4 advisory] preserve ending cadence",
            retry_directives="keep the chapter break timing intact",
        )
        db.save_director_selection(
            ep_num=14,
            round_num=1,
            selected_label="A",
            selected_strategy="balanced",
            verdict="PASS",
            score=96,
            selection_reason="후보 A가 후반 리듬과 장면 연결이 가장 안정적",
            fix_scope="inplace",
            stage=4,
            verdict_reason="수정 없이 바로 사용 가능",
            attempt_key=attempt_key,
            candidate_key="balanced",
            content_hash="hash-stage4",
            artifact_path=artifact_path,
            runtime_advisory="[stage4 advisory] preserve ending cadence",
            retry_directives="keep the chapter break timing intact",
        )

        logs_dir = tmp_path / "logs"
        (logs_dir / "session").mkdir(parents=True, exist_ok=True)
        (logs_dir / "session" / "decisions.jsonl").write_text(
            json.dumps(
                {
                    "stage": "stage4",
                    "ep_num": 14,
                    "round_num": 0,
                    "decision_type": "manuscript",
                    "result": "PASS",
                    "score": 96,
                    "meta": {
                        "attempt_key": attempt_key,
                        "candidate_key": "balanced",
                        "content_hash": "hash-stage4",
                        "artifact_path": artifact_path,
                        "reason": "수정 없이 바로 사용 가능",
                        "selection_reason": "후보 A가 후반 리듬과 장면 연결이 가장 안정적",
                        "verdict_reason": "수정 없이 바로 사용 가능",
                        "fix_scope": "inplace",
                        "runtime_advisory": "[stage4 advisory] preserve ending cadence",
                        "retry_directives": "keep the chapter break timing intact",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "stage": 4,
                            "episode": 14,
                            "arc": 2,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": attempt_key,
                            "final_verdict": "PASS",
                            "candidate_key": "balanced",
                            "content_hash": "hash-stage4",
                            "artifact_path": artifact_path,
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (logs_dir / "episode_production.jsonl").write_text(
            json.dumps(
                {
                    "stage": "stage4",
                    "decision_type": "manuscript",
                    "ep_num": 14,
                    "attempt_key": attempt_key,
                    "candidate_key": "balanced",
                    "selection_candidate_key": "balanced",
                    "content_hash": "hash-stage4",
                    "artifact_path": artifact_path,
                    "initial_verdict": "PASS",
                    "final_verdict": "PASS",
                    "score": 96,
                    "final_score": 96,
                    "selection_reason": "후보 A가 후반 리듬과 장면 연결이 가장 안정적",
                    "verdict_reason": "수정 없이 바로 사용 가능",
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary(stage=4, include_session_decisions=True)

        assert result["coverage"]["director_selections"] == 1
        assert result["coverage"]["session_decisions"] == 1
        assert result["coverage"]["pass_rate_monitor"] == 1
        assert result["coverage"]["episode_production"] == 1
        assert result["complete_lifecycle_attempts"] == 1
        assert result["runtime_advisory_mismatches"] == []
        assert result["retry_directives_mismatches"] == []
        assert result["rationale_metadata_missing"] == []
        assert result["final_sink_missing"] == {}
        assert result["lifecycle_sink_missing"] == {}
        assert result["lifecycle_missing_in_final_sinks"] == {}
    finally:
        db.close()


def test_failure_analyzer_stage4_companion_missing_runtime_advisory_is_not_metadata_gap(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_stage4_companion_advisory.db")
    try:
        analyzer = FailureAnalyzer(db)
        attempt_key = "s4:ep16:arc2:a1:sess_stage4_companion"
        result = analyzer._collect_sink_alignment_rationale_results(
            stage=4,
            include_session_decisions=True,
            attempt_key=attempt_key,
            stage_attempts={
                attempt_key: {
                    "selection_reason": "candidate B best preserves continuity",
                    "verdict_reason": "director accepted candidate B",
                    "comparison_notes": "B has stronger scene continuity",
                    "selected_candidate_advisory_struct": {},
                    "fix_scope": "inplace",
                    "runtime_advisory": "[stage4 advisory] preserve continuity",
                    "retry_directives": "",
                }
            },
            director_selections={
                attempt_key: {
                    "selection_reason": "candidate B best preserves continuity",
                    "verdict_reason": "director accepted candidate B",
                    "comparison_notes": "B has stronger scene continuity",
                    "selected_candidate_advisory_struct": {},
                    "fix_scope": "inplace",
                }
            },
            session_decisions={
                attempt_key: {
                    "selection_reason": "candidate B best preserves continuity",
                    "verdict_reason": "director accepted candidate B",
                    "comparison_notes": "B has stronger scene continuity",
                    "selected_candidate_advisory_struct": {},
                    "fix_scope": "inplace",
                    "runtime_advisory": "[stage4 advisory] preserve continuity",
                    "retry_directives": "",
                }
            },
            episode_production={
                attempt_key: {
                    "selection_reason": "candidate B best preserves continuity",
                    "verdict_reason": "director accepted candidate B",
                }
            },
        )

        assert result["runtime_advisory_mismatches"] == []
        assert result["retry_directives_mismatches"] == []
        assert result["rationale_metadata_missing"] == []
    finally:
        db.close()


def test_failure_analyzer_stage4_prefinal_director_rationale_drift_is_phase_warning(tmp_path):
    db = DBManager(tmp_path / "test_stage4_prefinal_rationale_phase_drift.db")
    try:
        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        attempt_key = "s4:ep16:arc2:a1:sess_stage4_prefinal"
        result = analyzer._collect_sink_alignment_rationale_results(
            stage=4,
            include_session_decisions=True,
            attempt_key=attempt_key,
            stage_attempts={
                attempt_key: {
                    "selection_reason": "settled post-fix candidate B wins",
                    "verdict_reason": "settled manuscript passes after fix",
                    "comparison_notes": "same comparison",
                    "selected_candidate_advisory_struct": {},
                    "fix_scope": "inplace",
                    "runtime_advisory": "",
                    "retry_directives": "",
                }
            },
            director_selections={
                attempt_key: {
                    "selection_reason": "original candidate A was best before repair",
                    "verdict_reason": "original director pass with fix",
                    "comparison_notes": "same comparison",
                    "selected_candidate_advisory_struct": {},
                    "fix_scope": "inplace",
                }
            },
            session_decisions={
                attempt_key: {
                    "selection_reason": "settled post-fix candidate B wins",
                    "verdict_reason": "settled manuscript passes after fix",
                    "comparison_notes": "same comparison",
                    "selected_candidate_advisory_struct": {},
                    "fix_scope": "inplace",
                    "runtime_advisory": "",
                    "retry_directives": "",
                }
            },
            episode_production={
                attempt_key: {
                    "selection_reason": "settled post-fix candidate B wins",
                    "verdict_reason": "settled manuscript passes after fix",
                }
            },
            authority_row={"selection_companion_status": "pre_final_candidate"},
        )

        assert result["selection_reason_mismatches"] == []
        assert result["verdict_reason_mismatches"] == []
        assert len(result["phase_drift_rationale_warnings"]) == 2
        fields = {row["field"] for row in result["phase_drift_rationale_warnings"]}
        assert fields == {"selection_reason", "verdict_reason"}
        assert all(
            row["phase_role"] == "director_selection_companion_pre_final"
            for row in result["phase_drift_rationale_warnings"]
        )
    finally:
        db.close()


def test_failure_analyzer_sink_alignment_summary_flags_stage4_runtime_rationale_mismatch(tmp_path):
    db = DBManager(tmp_path / "test_sink_alignment_stage4_runtime_rationale.db")
    try:
        attempt_key = "s4:ep15:arc2:a1:sess_stage4_mismatch"
        artifact_path = "logs/artifacts/stage4/ep_0015/attempt_01/final_manuscript__balanced.txt"
        artifact_file = tmp_path / artifact_path
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("stage4 artifact", encoding="utf-8")

        db.save_stage_attempt(
            stage=4,
            verdict="PASS_WITH_FIX",
            attempt_num=1,
            ep_num=15,
            arc_num=2,
            score=88,
            session_id="sess_stage4_mismatch",
            attempt_key=attempt_key,
            candidate_key="balanced",
            content_hash="hash-stage4-mismatch",
            artifact_path=artifact_path,
            selection_reason="후보 A가 전체 구조는 가장 안정적",
            verdict_reason="소형 리듬 보정만 하면 사용 가능",
            fix_scope="inplace",
            runtime_advisory="[stage4 advisory] preserve ending cadence",
            retry_directives="keep the same emotional landing",
        )
        db.save_director_selection(
            ep_num=15,
            round_num=1,
            selected_label="A",
            selected_strategy="balanced",
            verdict="PASS_WITH_FIX",
            score=88,
            selection_reason="후보 A가 전체 구조는 가장 안정적",
            fix_scope="inplace",
            stage=4,
            verdict_reason="소형 리듬 보정만 하면 사용 가능",
            attempt_key=attempt_key,
            candidate_key="balanced",
            content_hash="hash-stage4-mismatch",
            artifact_path=artifact_path,
            runtime_advisory="[stage4 advisory] preserve ending cadence",
            retry_directives="keep the same emotional landing",
        )

        logs_dir = tmp_path / "logs"
        (logs_dir / "session").mkdir(parents=True, exist_ok=True)
        (logs_dir / "session" / "decisions.jsonl").write_text(
            json.dumps(
                {
                    "stage": "stage4",
                    "ep_num": 15,
                    "round_num": 0,
                    "decision_type": "manuscript",
                    "result": "PASS_WITH_FIX",
                    "score": 88,
                    "meta": {
                        "attempt_key": attempt_key,
                        "candidate_key": "balanced",
                        "content_hash": "hash-stage4-mismatch",
                        "artifact_path": artifact_path,
                        "reason": "소형 리듬 보정만 하면 사용 가능",
                        "selection_reason": "후보 A가 전체 구조는 가장 안정적",
                        "verdict_reason": "소형 리듬 보정만 하면 사용 가능",
                        "fix_scope": "inplace",
                        "runtime_advisory": "[stage4 advisory] stale cadence packet leaked",
                        "retry_directives": "rewrite the closing paragraph from scratch",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (logs_dir / "pass_rate_monitor.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "stage": 4,
                            "episode": 15,
                            "arc": 2,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": attempt_key,
                            "final_verdict": "PASS_WITH_FIX",
                            "candidate_key": "balanced",
                            "content_hash": "hash-stage4-mismatch",
                            "artifact_path": artifact_path,
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary(stage=4, include_session_decisions=True)

        assert len(result["runtime_advisory_mismatches"]) == 1
        assert result["runtime_advisory_mismatches"][0]["attempt_key"] == attempt_key
        assert len(result["retry_directives_mismatches"]) == 1
        assert result["retry_directives_mismatches"][0]["attempt_key"] == attempt_key
        assert result["warning_taxonomy_counts"]["runtime_advisory_warn"] == 2
        assert result["status"] == "warn"
    finally:
        db.close()


def test_rescue_effectiveness_basic(tmp_path):
    """Tranche C: rescue effectiveness helper returns bounded metrics."""
    db = DBManager(tmp_path / "test_rescue.db")
    try:
        # patch attempt that succeeded
        db.save_stage_attempt(
            stage=3,
            verdict="PASS",
            ep_num=1,
            attempt_num=2,
            score=88,
            is_patch=True,
            patch_strategy="targeted_fix",
            initial_verdict="REJECT",
        )
        # patch attempt that failed
        db.save_stage_attempt(
            stage=3,
            verdict="REJECT",
            ep_num=2,
            attempt_num=2,
            score=55,
            is_patch=True,
            patch_strategy="full_rewrite",
            initial_verdict="REJECT",
        )
        # patch fallback (no strategy)
        db.save_stage_attempt(
            stage=4,
            verdict="PASS_WITH_WARNING",
            ep_num=3,
            attempt_num=3,
            score=82,
            is_patch_fallback=True,
            initial_verdict="REJECT",
        )
        # normal attempt (should be excluded)
        db.save_stage_attempt(
            stage=3,
            verdict="PASS",
            ep_num=4,
            attempt_num=1,
            score=95,
        )

        analyzer = FailureAnalyzer(db)
        result = analyzer.rescue_effectiveness()

        assert result["rescue_attempted_count"] == 3
        assert result["rescue_succeeded_count"] == 2  # PASS + PASS_WITH_WARNING
        assert result["rescue_success_rate_pct"] == 66.7
        assert result["asp_used_count"] == 0
        assert result["avg_score_delta"] is not None
        assert result["avg_score_delta"] > 0
    finally:
        db.close()


def test_rescue_effectiveness_empty(tmp_path):
    """Tranche C: rescue effectiveness returns zeros when no rescue attempts."""
    db = DBManager(tmp_path / "test_rescue_empty.db")
    try:
        db.save_stage_attempt(
            stage=3,
            verdict="PASS",
            ep_num=1,
            attempt_num=1,
            score=90,
        )
        analyzer = FailureAnalyzer(db)
        result = analyzer.rescue_effectiveness()
        assert result["rescue_attempted_count"] == 0
        assert result["rescue_succeeded_count"] == 0
        assert result["rescue_success_rate_pct"] == 0.0
        assert result["avg_score_delta"] is None
        assert result["asp_used_count"] == 0
    finally:
        db.close()


def test_rescue_effectiveness_counts_only_explicit_asp_strategy(tmp_path):
    """Only explicit ASP evidence should increment asp_used_count."""
    db = DBManager(tmp_path / "test_rescue_asp.db")
    try:
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            ep_num=1,
            attempt_num=3,
            score=91,
            is_patch=True,
            patch_strategy="asp_correction",
            initial_verdict="REJECT",
        )
        db.save_stage_attempt(
            stage=4,
            verdict="PASS",
            ep_num=2,
            attempt_num=2,
            score=89,
            is_patch=True,
            patch_strategy="patch_with_feedback",
            initial_verdict="REJECT",
        )
        analyzer = FailureAnalyzer(db)
        result = analyzer.rescue_effectiveness()
        assert result["asp_used_count"] == 1
    finally:
        db.close()
