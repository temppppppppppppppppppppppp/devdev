from pathlib import Path

from modules.domain.agents.arc_critic import ArcCritic


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_arc_critic_handles_string_scores_without_type_error():
    critic = ArcCritic.__new__(ArcCritic)
    result = critic._ensure_critique_fields({"scores": {"a": "8", "b": "10"}, "critical_issues": []})
    assert result["total_score"] == 18
    assert result["verdict"] == "REJECT"


def test_arc_critic_source_has_int_coercion_for_scores():
    src = _read("modules/domain/agents/arc_critic.py")
    assert "sum(int(v) for v in scores.values())" in src
    assert 'score = int(result["total_score"])' in src


def test_arc_critic_source_has_no_legacy_constraint_head_cut():
    src = _read("modules/domain/agents/arc_critic.py")
    assert 'constraints[:9000]' not in src


def test_director_auditor_source_has_safe_int_scoring_path():
    src = _read("modules/domain/agents/director_auditor.py")
    assert "def _safe_int_score(value, default=50):" in src
    assert 'first_score = _safe_int_score(first_eval.get("score", 50), 50)' in src
    assert 'scores.append(_safe_int_score(e.get("score", 50), 50))' in src
    assert 'abs(_safe_int_score(e.get("score", 50), 50) - median_score)' in src


def test_multi_agent_deliberation_source_has_int_coercion():
    src = _read("modules/core/multi_agent_deliberation.py")
    assert '_score = int(result.get("score", 70))' in src
    assert "score=_score," in src


def test_state_delta_tracker_source_has_energy_try_except():
    src = _read("modules/core/state_delta_tracker.py")
    assert 'energy = int(energy.replace("%", "").strip())' in src
    assert "except (ValueError, TypeError):" in src
    assert "self.current_energy = 50" in src


def test_cross_agent_verifier_source_has_float_coercion():
    src = _read("modules/core/cross_agent_verifier.py")
    assert src.count('score = float(result.get("compliance_score", 0.7))') >= 2


def test_block_enricher_source_has_total_score_int_coercion():
    src = _read("modules/domain/agents/block_enricher.py")
    assert 'total_score = int(result.get("total_score", 0))' in src


def test_constraint_db_source_has_arc_no_parse_guard():
    src = _read("modules/core/constraint_db.py")
    assert "arc_no = int(arc_no)" in src
    assert "[ConstraintDB] arc_no 파싱 실패:" in src
    assert "self.arc_states[arc_no] = state" in src


def test_stage_orchestrators_source_have_score_int_coercion():
    s2 = _read("modules/core/stage2_orchestrator.py")
    s4 = _read("modules/core/stage4_interview_round.py")
    assert '_rej_score = int(_fin.get("score", 0))' in s2
    assert '_prev_score = int(previous_attempt.get("score", 0)) if previous_attempt else 0' in s4


def test_quality_dashboard_source_has_score_int_coercion():
    src = _read("modules/core/quality_dashboard.py")
    assert 'current_score = int(scored[-1].get("score", 0))' in src
    assert 'prev_score = int(scored[-2].get("score", 0))' in src
    assert 'baseline_scores.append(int(r.get("score", 0)))' in src
    assert 'scores.append(int(r.get("score", 0)))' in src
