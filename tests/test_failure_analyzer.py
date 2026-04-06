"""FailureAnalyzer success-pattern and quality-distribution tests."""

import json

from modules.core.db_manager import DBManager
from modules.core.failure_analyzer import FailureAnalyzer


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
        db.save_stage_attempt(stage=4, verdict="PASS_WITH_FIX", ep_num=13, arc_num=4, score=89, prompt_version="chief@v2")

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
        db.save_stage_attempt(stage=4, verdict="PASS_WITH_WARNING", ep_num=11, arc_num=3, score=88, prompt_version="chief@v1")
        db.save_stage_attempt(stage=4, verdict="PASS_WITH_FIX", ep_num=12, arc_num=3, score=89, prompt_version="chief@v1")
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
        log_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in entries) + "\n", encoding="utf-8")

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
                "flags": {"patch_mode": True},
                "patch_trace": {
                    "patch_strategy": "inplace_patch_structural",
                    "patch_targets": ["scene_2"],
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
                "flags": {"patch_mode": True},
                "patch_trace": {
                    "patch_strategy": "inplace_patch",
                    "patch_targets": [],
                    "unchanged_ratio": 0.58,
                    "fallback_reason": "global_issue",
                    "focus": "global",
                    "structural_attempted": False,
                },
            },
        ]
        log_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in entries) + "\n", encoding="utf-8")

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
        assert result["top_patch_targets"] == [{"target": "scene_2", "count": 1}]
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

    assert final_union == {"a"}
    assert lifecycle_union == {"c", "e"}
    assert attempts_considered == {"a", "c", "e"}


def test_failure_analyzer_collect_sink_alignment_missing_buckets_tracks_final_and_lifecycle_gaps():
    final_missing, lifecycle_missing, lifecycle_missing_in_final = (
        FailureAnalyzer._collect_sink_alignment_missing_buckets(
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

    assert final_missing == {
        "stage_attempts": {"count": 1, "examples": ["b"]},
        "session_decisions": {"count": 1, "examples": ["b"]},
    }
    assert lifecycle_missing == {
        "director_selections": {"count": 1, "examples": ["b"]},
        "episode_production": {"count": 1, "examples": ["c"]},
    }
    assert lifecycle_missing_in_final == {
        "stage_attempts": {"count": 2, "examples": ["b", "c"]},
    }


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
                "gate_repair_metadata_missing",
                "rationale_metadata_missing",
                "artifact_missing_files",
                "selection_companion_pre_final_rows",
                "selection_companion_missing_rows",
            )
        }
        consistency_results["patch_strategy_mismatches"] = [
            {"attempt_key": attempt_key, "pass_rate_monitor": "inplace_patch", "episode_production": "rewrite"}
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
            session_decision_rows_without_attempt_key=0,
            final_authority_rows=[
                {"selection_companion_status": "same_as_final"},
                {"selection_companion_status": "pre_final_candidate"},
                {"selection_companion_status": "missing"},
            ],
            consistency_results=consistency_results,
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
        assert result["patch_strategy_mismatches"] == consistency_results["patch_strategy_mismatches"]
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
            item["attempt_key"] == mismatch_key
            for item in result["scope_authority_authoritative_fix_scope_mismatches"]
        )
        assert any(item["attempt_key"] == mismatch_key for item in result["scope_authority_widened_mismatches"])

        missing_entries = [item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == missing_key]
        assert any(item["field"] == "director_verdict" and "pass_rate_monitor" in item["sinks"] for item in missing_entries)
        assert any(item["field"] == "fix_pack_patch_targets" and "pass_rate_monitor" in item["sinks"] for item in missing_entries)
        assert any(item["field"] == "repair_contract_subtype" and "pass_rate_monitor" in item["sinks"] for item in missing_entries)
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
        assert result["selection_candidate_key_mismatches"] == [
            {
                "attempt_key": attempt_key_bad,
                "director_selections": "C|balanced",
                "episode_production": "B|balanced",
            }
        ]
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

        logs_dir = tmp_path / "logs"
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
        assert with_session["status"] == "ok"
        assert with_session["final_sink_missing"] == {}
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
                            "episode": 62,
                            "arc": 6,
                            "attempt_num": 1,
                            "success": True,
                            "attempt_key": new_key,
                            "final_verdict": "PASS",
                            "candidate_key": "A|balanced",
                            "content_hash": "hash-new",
                            "artifact_path": new_artifact,
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
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
            json.dumps(authoritative_row, ensure_ascii=False) + "\n" + json.dumps(pathology_row, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        analyzer = FailureAnalyzer(db, project_path=tmp_path)
        result = analyzer.sink_alignment_summary(stage=4, session_id="sess_path")

        assert result["coverage"]["episode_production"] == 1
        missing_entries = [item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == attempt_key]
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
            json.dumps(authoritative_row, ensure_ascii=False) + "\n" + json.dumps(pathology_row, ensure_ascii=False) + "\n",
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

        missing_entries = [item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == attempt_key]
        assert not any(
            item["field"] == "repair_contract_subtype" and "stage_attempts" in item["sinks"] for item in missing_entries
        )
        assert not any(
            item["field"] == "repair_contract_provenance" and "stage_attempts" in item["sinks"] for item in missing_entries
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

        missing_entries = [item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == attempt_key]
        assert not any(
            item["field"] == "gate_basis" and "stage_attempts" in item["sinks"] for item in missing_entries
        )
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
            item["field"] == "repair_contract_provenance" and "stage_attempts" in item["sinks"] for item in missing_entries
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
            item["field"] == "scope_authority_widened" and "stage_attempts" in item["sinks"]
            for item in missing_entries
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

        missing_entries = [item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == attempt_key]
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
        assert rows[0]["runtime_advisory"] == "[advisory] keep continuity"
        assert rows[0]["retry_directives"] == "preserve the ending cadence"
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
        )

        logs_dir = tmp_path / "logs"
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
                        "fix_scope": "inplace",
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
        assert result["fix_scope_mismatches"] == []
        assert result["rationale_metadata_missing"] == []
        assert result["status"] == "ok"
    finally:
        db.close()


def test_rescue_effectiveness_basic(tmp_path):
    """Tranche C: rescue effectiveness helper returns bounded metrics."""
    db = DBManager(tmp_path / "test_rescue.db")
    try:
        # patch attempt that succeeded
        db.save_stage_attempt(
            stage=3, verdict="PASS", ep_num=1, attempt_num=2, score=88,
            is_patch=True, patch_strategy="targeted_fix",
            initial_verdict="REJECT",
        )
        # patch attempt that failed
        db.save_stage_attempt(
            stage=3, verdict="REJECT", ep_num=2, attempt_num=2, score=55,
            is_patch=True, patch_strategy="full_rewrite",
            initial_verdict="REJECT",
        )
        # patch fallback (no strategy)
        db.save_stage_attempt(
            stage=4, verdict="PASS_WITH_WARNING", ep_num=3, attempt_num=3, score=82,
            is_patch_fallback=True, initial_verdict="REJECT",
        )
        # normal attempt (should be excluded)
        db.save_stage_attempt(
            stage=3, verdict="PASS", ep_num=4, attempt_num=1, score=95,
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
            stage=3, verdict="PASS", ep_num=1, attempt_num=1, score=90,
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
            stage=4, verdict="PASS", ep_num=1, attempt_num=3, score=91,
            is_patch=True, patch_strategy="asp_correction",
            initial_verdict="REJECT",
        )
        db.save_stage_attempt(
            stage=4, verdict="PASS", ep_num=2, attempt_num=2, score=89,
            is_patch=True, patch_strategy="patch_with_feedback",
            initial_verdict="REJECT",
        )
        analyzer = FailureAnalyzer(db)
        result = analyzer.rescue_effectiveness()
        assert result["asp_used_count"] == 1
    finally:
        db.close()
