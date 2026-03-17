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

        missing_entries = [item for item in result["gate_repair_metadata_missing"] if item["attempt_key"] == missing_key]
        assert any(item["field"] == "director_verdict" and "pass_rate_monitor" in item["sinks"] for item in missing_entries)
        assert any(item["field"] == "fix_pack_patch_targets" and "pass_rate_monitor" in item["sinks"] for item in missing_entries)
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

        assert unfiltered["status"] == "warn"
        assert unfiltered["final_sink_missing"]["pass_rate_monitor"]["count"] == 1
        assert filtered["status"] == "ok"
        assert filtered["session_filter"] == "new_sess"
        assert filtered["attempts_considered"] == 1
        assert filtered["coverage"]["stage_attempts"] == 1
        assert filtered["coverage"]["pass_rate_monitor"] == 1
        assert filtered["coverage"]["director_selections"] == 1
        assert filtered["coverage"]["episode_production"] == 1
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
