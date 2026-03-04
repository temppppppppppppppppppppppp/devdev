"""[Log-4] Failure pattern post-analysis utility."""

from __future__ import annotations

import json
import logging
from collections import defaultdict


class FailureAnalyzer:
    """Utility for analyzing failure patterns from DB telemetry."""

    def __init__(self, db) -> None:
        self.db = db

    def summary(self) -> dict:
        """Top-level summary for quick diagnostics."""
        result = {}
        try:
            result["stage_pass_rates"] = self.stage_pass_rates()
            result["top_failed_agents"] = self.most_failed_agents(top_n=5)
            result["top_failure_categories"] = self.top_failure_categories(top_n=5)
            result["advisory_correlations"] = self.advisory_reject_correlation()
            result["avg_attempts_by_stage"] = self.avg_attempts_by_stage()
        except Exception as _e:
            logging.debug("[FailureAnalyzer] summary failed: %s", _e)
        return result

    def stage_pass_rates(self) -> dict:
        """Per-stage attempt/pass/reject rates."""
        try:
            rows = self.db.conn.execute(
                """SELECT stage, verdict, COUNT(*) as cnt
                   FROM stage_attempts GROUP BY stage, verdict"""
            ).fetchall()
            if not rows:
                return {}
            by_stage: dict[int, dict] = defaultdict(lambda: defaultdict(int))
            for r in rows:
                by_stage[r["stage"]][r["verdict"]] += r["cnt"]
            result = {}
            for stage, counts in sorted(by_stage.items()):
                total = sum(counts.values())
                passes = counts.get("PASS", 0) + counts.get("PASS_WITH_FIX", 0)
                result[f"stage_{stage}"] = {
                    "total_attempts": total,
                    "pass": passes,
                    "reject": counts.get("REJECT", 0),
                    "pass_rate_pct": round(passes / total * 100, 1) if total else 0,
                }
            return result
        except Exception as _e:
            logging.debug("[FailureAnalyzer] stage_pass_rates: %s", _e)
            return {}

    def avg_attempts_by_stage(self) -> dict:
        """Average max attempt count per episode by stage."""
        try:
            rows = self.db.conn.execute(
                """SELECT stage, ep_num, MAX(attempt_num) as max_attempt
                   FROM stage_attempts GROUP BY stage, ep_num"""
            ).fetchall()
            if not rows:
                return {}
            by_stage: dict[int, list] = defaultdict(list)
            for r in rows:
                by_stage[r["stage"]].append(r["max_attempt"])
            return {f"stage_{s}": round(sum(v) / len(v), 2) if v else 0 for s, v in sorted(by_stage.items())}
        except Exception as _e:
            logging.debug("[FailureAnalyzer] avg_attempts_by_stage: %s", _e)
            return {}

    def most_failed_agents(self, top_n: int = 10) -> list[dict]:
        """Top agents by absolute failure counts."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name, model,
                          SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failures,
                          COUNT(*) as total,
                          AVG(duration_ms) as avg_ms
                   FROM llm_calls
                   GROUP BY agent_name, model
                   ORDER BY failures DESC
                   LIMIT ?""",
                (top_n,),
            ).fetchall()
            return [
                {
                    "agent": r["agent_name"],
                    "model": r["model"],
                    "failures": r["failures"],
                    "total": r["total"],
                    "fail_rate_pct": round(r["failures"] / r["total"] * 100, 1) if r["total"] else 0,
                    "avg_duration_ms": int(r["avg_ms"] or 0),
                }
                for r in rows
            ]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] most_failed_agents: %s", _e)
            return []

    def slowest_agents(self, top_n: int = 10) -> list[dict]:
        """Top agents by average successful latency."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name, model,
                          AVG(duration_ms) as avg_ms,
                          MAX(duration_ms) as max_ms,
                          COUNT(*) as total
                   FROM llm_calls WHERE success=1
                   GROUP BY agent_name, model
                   ORDER BY avg_ms DESC LIMIT ?""",
                (top_n,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] slowest_agents: %s", _e)
            return []

    def agent_error_types(self) -> dict:
        """Error type distribution grouped by agent."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name, error_type, COUNT(*) as cnt
                   FROM llm_calls WHERE success=0 AND error_type IS NOT NULL
                   GROUP BY agent_name, error_type
                   ORDER BY cnt DESC"""
            ).fetchall()
            result: dict[str, dict] = defaultdict(dict)
            for r in rows:
                result[r["agent_name"]][r["error_type"]] = r["cnt"]
            return dict(result)
        except Exception as _e:
            logging.debug("[FailureAnalyzer] agent_error_types: %s", _e)
            return {}

    def top_failure_categories(self, top_n: int = 10, stage: int | None = None) -> list[dict]:
        """Top reject categories from stage attempts."""
        try:
            if stage is not None:
                rows = self.db.conn.execute(
                    """SELECT failure_category, COUNT(*) as cnt
                       FROM stage_attempts
                       WHERE verdict='REJECT' AND failure_category IS NOT NULL AND stage=?
                       GROUP BY failure_category ORDER BY cnt DESC LIMIT ?""",
                    (stage, top_n),
                ).fetchall()
            else:
                rows = self.db.conn.execute(
                    """SELECT failure_category, COUNT(*) as cnt
                       FROM stage_attempts
                       WHERE verdict='REJECT' AND failure_category IS NOT NULL
                       GROUP BY failure_category ORDER BY cnt DESC LIMIT ?""",
                    (top_n,),
                ).fetchall()
            return [{"category": r["failure_category"], "count": r["cnt"]} for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] top_failure_categories: %s", _e)
            return []

    def failure_trend_by_episode(self) -> list[dict]:
        """Reject rate trend by episode."""
        try:
            rows = self.db.conn.execute(
                """SELECT ep_num,
                          SUM(CASE WHEN verdict='REJECT' THEN 1 ELSE 0 END) as rejects,
                          COUNT(*) as total
                   FROM stage_attempts
                   WHERE ep_num IS NOT NULL
                   GROUP BY ep_num ORDER BY ep_num"""
            ).fetchall()
            return [
                {
                    "ep": r["ep_num"],
                    "rejects": r["rejects"],
                    "total": r["total"],
                    "reject_rate_pct": round(r["rejects"] / r["total"] * 100, 1) if r["total"] else 0,
                }
                for r in rows
            ]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] failure_trend_by_episode: %s", _e)
            return []

    def advisory_reject_correlation(self) -> dict:
        """Compare reject rates when each advisory flag is triggered vs not triggered."""
        try:
            rows = self.db.conn.execute(
                """SELECT advisory_warnings, verdict
                   FROM director_selections
                   WHERE advisory_warnings IS NOT NULL"""
            ).fetchall()
            if not rows:
                return {}

            advisory_types = [
                "truth_gate",
                "npc_drift",
                "numeric_drift",
                "rel_drift",
                "flashback",
                "info_paradox",
                "long_term_rep",
            ]
            result = {}
            for adv_type in advisory_types:
                with_adv_pass = with_adv_reject = without_adv_pass = without_adv_reject = 0
                for r in rows:
                    try:
                        flags = json.loads(r["advisory_warnings"] or "{}")
                    except (json.JSONDecodeError, TypeError):
                        continue
                    has_flag = bool(flags.get(adv_type))
                    is_reject = r["verdict"] == "REJECT"
                    if has_flag:
                        if is_reject:
                            with_adv_reject += 1
                        else:
                            with_adv_pass += 1
                    else:
                        if is_reject:
                            without_adv_reject += 1
                        else:
                            without_adv_pass += 1

                total_with = with_adv_pass + with_adv_reject
                total_without = without_adv_pass + without_adv_reject
                if total_with == 0:
                    continue
                result[adv_type] = {
                    "triggered_count": total_with,
                    "reject_rate_when_triggered_pct": round(with_adv_reject / total_with * 100, 1),
                    "reject_rate_when_not_triggered_pct": (
                        round(without_adv_reject / total_without * 100, 1) if total_without else 0
                    ),
                    "signal_lift": round(
                        (with_adv_reject / total_with) / (without_adv_reject / total_without)
                        if total_without and without_adv_reject
                        else 0,
                        2,
                    ),
                }
            return result
        except Exception as _e:
            logging.debug("[FailureAnalyzer] advisory_reject_correlation: %s", _e)
            return {}

    def model_performance(self) -> dict:
        """Model-level success/latency/response-size summary."""
        try:
            rows = self.db.conn.execute(
                """SELECT model,
                          SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successes,
                          COUNT(*) as total,
                          AVG(duration_ms) as avg_ms,
                          AVG(response_chars) as avg_resp_chars
                   FROM llm_calls
                   GROUP BY model ORDER BY total DESC"""
            ).fetchall()
            if not rows:
                return {}
            return {
                r["model"]: {
                    "total_calls": r["total"],
                    "success_rate_pct": round(r["successes"] / r["total"] * 100, 1) if r["total"] else 0,
                    "avg_duration_ms": int(r["avg_ms"] or 0),
                    "avg_response_chars": int(r["avg_resp_chars"] or 0),
                }
                for r in rows
            }
        except Exception as _e:
            logging.debug("[FailureAnalyzer] model_performance: %s", _e)
            return {}

    def large_prompt_calls(self, threshold_chars: int = 50000, top_n: int = 20) -> list[dict]:
        """Calls with unusually large prompt payloads."""
        try:
            rows = self.db.conn.execute(
                """SELECT ts, agent_name, model, ep_num, stage,
                          prompt_chars, response_chars, duration_ms, context_tag
                   FROM llm_calls
                   WHERE prompt_chars >= ?
                   ORDER BY prompt_chars DESC LIMIT ?""",
                (threshold_chars, top_n),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] large_prompt_calls: %s", _e)
            return []

    def empty_response_calls(self) -> list[dict]:
        """Successful API calls with near-empty responses."""
        try:
            rows = self.db.conn.execute(
                """SELECT ts, agent_name, model, ep_num, stage,
                          prompt_chars, response_chars, error_type, error_msg
                   FROM llm_calls
                   WHERE success=1 AND (response_chars IS NULL OR response_chars < 50)
                   ORDER BY ts DESC LIMIT 50"""
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] empty_response_calls: %s", _e)
            return []

    def print_report(self) -> None:
        """Print summary report to console."""
        import pprint

        pprint.pprint(self.summary(), width=100, sort_dicts=False)
