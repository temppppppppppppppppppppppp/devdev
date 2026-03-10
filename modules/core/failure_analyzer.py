"""[Log-4] Failure pattern post-analysis utility."""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path


class FailureAnalyzer:
    """Utility for analyzing failure patterns from DB telemetry.

    단일 스레드 설계 — 분석 전용 유틸리티. threading.Lock 불필요.
    """

    def __init__(self, db, project_path: str | Path | None = None) -> None:
        self.db = db
        if project_path is not None:
            self.project_path = Path(project_path)
        else:
            db_path = getattr(db, "db_path", None)
            self.project_path = Path(db_path).parent if db_path else None

    def summary(self) -> dict:
        """Top-level summary for quick diagnostics."""
        result = {}
        try:
            result["stage_pass_rates"] = self.stage_pass_rates()
            result["top_failed_agents"] = self.most_failed_agents(top_n=5)
            result["top_failure_categories"] = self.top_failure_categories(top_n=5)
            result["advisory_correlations"] = self.advisory_reject_correlation()
            result["avg_attempts_by_stage"] = self.avg_attempts_by_stage()
            result["failure_prompt_patterns"] = self.failure_prompt_patterns(top_n=5)
            result["top_success_patterns"] = self.top_success_patterns(top_n=3)
            result["quality_distribution"] = self.quality_distribution()
        except Exception as _e:
            logging.debug("[FailureAnalyzer] summary failed: %s", _e)
        return result

    def _load_episode_production_entries(self, min_score: int = 0) -> list[dict]:
        """episode_production.jsonl fallback loader."""
        if self.project_path is None:
            return []

        log_path = self.project_path / "logs" / "episode_production.jsonl"
        if not log_path.exists():
            return []

        entries: list[dict] = []
        try:
            with log_path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue
                    try:
                        score = int(row.get("score", 0) or 0)
                    except (TypeError, ValueError):
                        score = 0
                    if score < min_score:
                        continue
                    entries.append(row)
        except Exception as _e:
            logging.debug("[FailureAnalyzer] episode_production load failed: %s", _e)
            return []
        return entries

    def top_success_patterns(self, top_n: int = 5, min_score: int = 90) -> list[dict]:
        """고득점 에피소드의 공통 품질 패턴 요약."""
        rows: list[dict] = []
        try:
            db_rows = self.db.conn.execute(
                """SELECT ep_num, score, verdict, selection_reason, open_review,
                          score_breakdown, consistency_checklist
                   FROM episode_quality_labels
                   WHERE score >= ?
                   ORDER BY score DESC, ep_num DESC
                   LIMIT ?""",
                (min_score, max(top_n * 3, 6)),
            ).fetchall()
            for row in db_rows:
                item = dict(row)
                for field in ("score_breakdown", "consistency_checklist"):
                    try:
                        item[field] = json.loads(item.get(field) or "{}")
                    except (TypeError, ValueError, json.JSONDecodeError):
                        item[field] = {}
                rows.append(item)
        except Exception as _e:
            logging.debug("[FailureAnalyzer] top_success_patterns DB fallback: %s", _e)

        if not rows:
            for entry in self._load_episode_production_entries(min_score=min_score):
                verdict = str(entry.get("verdict", "") or "")
                if verdict not in ("PASS", "PASS_WITH_FIX"):
                    continue
                rows.append(
                    {
                        "ep_num": entry.get("ep"),
                        "score": entry.get("score", 0),
                        "verdict": verdict,
                        "selection_reason": entry.get("reason", ""),
                        "open_review": entry.get("open_review", ""),
                        "score_breakdown": entry.get("score_breakdown", {}) or {},
                        "consistency_checklist": entry.get("consistency_checklist", {}) or {},
                    }
                )

        if not rows:
            return []

        score_totals: dict[str, float] = defaultdict(float)
        score_counts: dict[str, int] = defaultdict(int)
        checklist_ok: dict[str, int] = defaultdict(int)
        checklist_total: dict[str, int] = defaultdict(int)
        keyword_counts: dict[str, int] = defaultdict(int)
        stopwords = {"그리고", "그러나", "이번", "장면", "서사", "원고", "후보", "score", "review"}

        for row in rows:
            for key, value in (row.get("score_breakdown") or {}).items():
                if isinstance(value, int | float):
                    score_totals[key] += float(value)
                    score_counts[key] += 1
            for key, verdict in (row.get("consistency_checklist") or {}).items():
                verdict_text = str(verdict or "").upper()
                if verdict_text in {"OK", "ISSUE"}:
                    checklist_total[key] += 1
                    if verdict_text == "OK":
                        checklist_ok[key] += 1
            reason_text = " ".join(
                str(row.get(field, "") or "") for field in ("selection_reason", "open_review")
            )
            tokens = {
                token
                for token in re.findall(r"[가-힣A-Za-z]{2,}", reason_text)
                if token.lower() not in stopwords
            }
            for token in tokens:
                keyword_counts[token] += 1

        patterns: list[dict] = []
        axis_avgs = sorted(
            (
                (key, round(score_totals[key] / score_counts[key], 1))
                for key in score_totals
                if score_counts[key] > 0
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        for key, avg in axis_avgs[:2]:
            patterns.append(
                {
                    "pattern": key,
                    "count": len(rows),
                    "description": f"{key} 평균 {avg}점",
                }
            )

        stable_keys = [
            key
            for key, total in checklist_total.items()
            if total > 0 and checklist_ok[key] / total >= 0.8
        ]
        if stable_keys:
            patterns.append(
                {
                    "pattern": "stable_checklist",
                    "count": len(rows),
                    "description": "OK 비율 높음: " + ", ".join(sorted(stable_keys)[:4]),
                }
            )

        common_keywords = [key for key, count in sorted(keyword_counts.items(), key=lambda item: item[1], reverse=True) if count >= 2]
        if common_keywords:
            patterns.append(
                {
                    "pattern": "selection_reason_keywords",
                    "count": len(rows),
                    "description": "반복 키워드: " + ", ".join(common_keywords[:4]),
                }
            )

        return patterns[:top_n]

    def quality_distribution(self, lookback: int = 100) -> dict:
        """정규화된 품질 라벨 분포 요약."""
        rows: list[dict] = []
        try:
            db_rows = self.db.conn.execute(
                """SELECT score, verdict, score_breakdown
                   FROM episode_quality_labels
                   ORDER BY ep_num DESC
                   LIMIT ?""",
                (lookback,),
            ).fetchall()
            for row in db_rows:
                item = dict(row)
                try:
                    item["score_breakdown"] = json.loads(item.get("score_breakdown") or "{}")
                except (TypeError, ValueError, json.JSONDecodeError):
                    item["score_breakdown"] = {}
                rows.append(item)
        except Exception as _e:
            logging.debug("[FailureAnalyzer] quality_distribution DB fallback: %s", _e)

        if not rows:
            for entry in self._load_episode_production_entries(min_score=0)[-lookback:]:
                rows.append(
                    {
                        "score": entry.get("score", 0),
                        "verdict": entry.get("verdict", ""),
                        "score_breakdown": entry.get("score_breakdown", {}) or {},
                    }
                )

        if not rows:
            return {}

        scores = []
        breakdown_sum: dict[str, float] = defaultdict(float)
        breakdown_count: dict[str, int] = defaultdict(int)
        pass_with_fix_count = 0
        high_score_count = 0
        for row in rows:
            try:
                score = int(row.get("score", 0) or 0)
            except (TypeError, ValueError):
                score = 0
            scores.append(score)
            if score >= 90:
                high_score_count += 1
            if str(row.get("verdict", "") or "") == "PASS_WITH_FIX":
                pass_with_fix_count += 1
            for key, value in (row.get("score_breakdown") or {}).items():
                if isinstance(value, int | float):
                    breakdown_sum[key] += float(value)
                    breakdown_count[key] += 1

        return {
            "count": len(rows),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            "high_score_count": high_score_count,
            "pass_with_fix_count": pass_with_fix_count,
            "avg_breakdown": {
                key: round(breakdown_sum[key] / breakdown_count[key], 1)
                for key in breakdown_sum
                if breakdown_count[key] > 0
            },
        }

    def compare_versions(
        self,
        version_a: str,
        version_b: str,
        *,
        stage: int | None = None,
        lookback: int = 200,
    ) -> dict:
        """Compare pass-rate and score deltas between two prompt-version tags."""
        version_a = str(version_a or "").strip()
        version_b = str(version_b or "").strip()
        if not version_a or not version_b:
            return {}

        clauses = ["prompt_version IN (?, ?)"]
        params: list = [version_a, version_b]
        if stage is not None:
            clauses.append("stage = ?")
            params.append(stage)
        where_sql = " AND ".join(clauses)
        params.append(max(int(lookback or 0), 1))

        try:
            rows = self.db.conn.execute(
                f"""SELECT prompt_version, verdict, score
                    FROM (
                        SELECT prompt_version, verdict, score, id
                        FROM stage_attempts
                        WHERE {where_sql}
                        ORDER BY id DESC
                        LIMIT ?
                    ) recent""",
                tuple(params),
            ).fetchall()
        except Exception as _e:
            logging.debug("[FailureAnalyzer] compare_versions: %s", _e)
            return {}

        if not rows:
            return {}

        stats = {
            version_a: {"attempts": 0, "pass": 0, "reject": 0, "scores": []},
            version_b: {"attempts": 0, "pass": 0, "reject": 0, "scores": []},
        }
        for row in rows:
            version = str(row["prompt_version"] or "")
            if version not in stats:
                continue
            stats[version]["attempts"] += 1
            verdict = str(row["verdict"] or "")
            if verdict in {"PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING"}:
                stats[version]["pass"] += 1
            elif verdict == "REJECT":
                stats[version]["reject"] += 1
            try:
                score = int(row["score"])
            except (TypeError, ValueError):
                score = None
            if score is not None:
                stats[version]["scores"].append(score)

        versions: dict[str, dict] = {}
        for version, data in stats.items():
            attempts = int(data["attempts"])
            scores = data["scores"]
            versions[version] = {
                "attempts": attempts,
                "pass": int(data["pass"]),
                "reject": int(data["reject"]),
                "pass_rate_pct": round((data["pass"] / attempts) * 100, 1) if attempts else 0.0,
                "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            }

        delta_pass_rate = round(
            versions[version_b]["pass_rate_pct"] - versions[version_a]["pass_rate_pct"],
            1,
        )
        delta_avg_score = round(
            versions[version_b]["avg_score"] - versions[version_a]["avg_score"],
            1,
        )

        winner = None
        if versions[version_a]["attempts"] and versions[version_b]["attempts"]:
            if (versions[version_b]["pass_rate_pct"], versions[version_b]["avg_score"]) > (
                versions[version_a]["pass_rate_pct"],
                versions[version_a]["avg_score"],
            ):
                winner = version_b
            elif (versions[version_a]["pass_rate_pct"], versions[version_a]["avg_score"]) > (
                versions[version_b]["pass_rate_pct"],
                versions[version_b]["avg_score"],
            ):
                winner = version_a

        return {
            "versions": versions,
            "pass_rate_delta_pct": delta_pass_rate,
            "avg_score_delta": delta_avg_score,
            "winner": winner,
        }

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

    def failed_call_snippets(self, agent_name: str | None = None, top_n: int = 20) -> list[dict]:
        """Recent failed-call prompt/response snippets for root-cause tracing."""
        try:
            if agent_name:
                rows = self.db.conn.execute(
                    """SELECT ts, agent_name, model, ep_num, stage,
                              error_type, error_msg,
                              prompt_snippet, response_snippet,
                              prompt_chars, response_chars, duration_ms
                       FROM llm_calls
                       WHERE success=0 AND prompt_snippet IS NOT NULL
                         AND agent_name=?
                       ORDER BY ts DESC LIMIT ?""",
                    (agent_name, top_n),
                ).fetchall()
            else:
                rows = self.db.conn.execute(
                    """SELECT ts, agent_name, model, ep_num, stage,
                              error_type, error_msg,
                              prompt_snippet, response_snippet,
                              prompt_chars, response_chars, duration_ms
                       FROM llm_calls
                       WHERE success=0 AND prompt_snippet IS NOT NULL
                       ORDER BY ts DESC LIMIT ?""",
                    (top_n,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] failed_call_snippets: %s", _e)
            return []

    def failure_prompt_patterns(self, top_n: int = 10) -> list[dict]:
        """Failure prompt-size/response-size distribution by agent."""
        try:
            rows = self.db.conn.execute(
                """SELECT agent_name,
                          COUNT(*) as fail_count,
                          AVG(prompt_chars) as avg_prompt_chars,
                          MAX(prompt_chars) as max_prompt_chars,
                          AVG(response_chars) as avg_resp_chars
                   FROM llm_calls
                   WHERE success=0
                   GROUP BY agent_name
                   ORDER BY fail_count DESC LIMIT ?""",
                (top_n,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as _e:
            logging.debug("[FailureAnalyzer] failure_prompt_patterns: %s", _e)
            return []

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

    @staticmethod
    def _collect_suffix_candidates(unmatched: list[str], min_count: int = 2) -> list[dict]:
        """미매칭 아이템 목록에서 접미사 후보(count/examples) 추출."""
        counts: dict[str, int] = {}
        examples: dict[str, list[str]] = {}

        for raw_name in unmatched:
            name = str(raw_name).strip()
            if len(name) < 2:
                continue
            for length in (1, 2, 3):
                if len(name) <= length:
                    continue
                suffix = name[-length:]
                counts[suffix] = counts.get(suffix, 0) + 1
                bucket = examples.setdefault(suffix, [])
                if len(bucket) < 3 and name not in bucket:
                    bucket.append(name)

        rows = []
        for suffix, cnt in counts.items():
            if cnt >= min_count:
                rows.append({"suffix": suffix, "count": cnt, "examples": examples.get(suffix, [])})

        rows.sort(key=lambda row: (-int(row["count"]), len(str(row["suffix"])), str(row["suffix"])))
        return rows

    def item_suffix_gap_report(self, registry, genre: str = "") -> dict:
        """아이템 접미사 안전망 갭 리포트 생성."""
        try:
            total_items = len(getattr(registry, "items", {}) or {})
            if not registry or not hasattr(registry, "get_unmatched_items"):
                return {"total_items": total_items, "unmatched_count": 0, "unmatched": [], "suggested_suffixes": []}

            unmatched = registry.get_unmatched_items(genre)
            if not isinstance(unmatched, list):
                unmatched = []

            candidates = self._collect_suffix_candidates(unmatched, min_count=2)
            suggested = [str(row.get("suffix", "")).strip() for row in candidates if str(row.get("suffix", "")).strip()]

            return {
                "total_items": total_items,
                "unmatched_count": len(unmatched),
                "unmatched": unmatched[:30],
                "suggested_suffixes": suggested[:10],
            }
        except Exception as _e:
            logging.debug("[FailureAnalyzer] item_suffix_gap_report: %s", _e)
            return {"total_items": 0, "unmatched_count": 0, "unmatched": [], "suggested_suffixes": []}

    @staticmethod
    def _parse_json_array_response(raw_text: str) -> list[dict]:
        """LLM 텍스트에서 JSON 배열 파싱."""
        if not raw_text:
            return []
        raw_text = str(raw_text).strip()
        if not raw_text:
            return []

        try:
            parsed = json.loads(raw_text)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            pass

        m = re.search(r"\[[\s\S]*\]", raw_text)
        if not m:
            return []

        try:
            parsed = json.loads(m.group(0))
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def review_suffix_candidates(self, candidates: list[dict], llm_ask=None) -> list[dict]:
        """미매칭 아이템 접미사 후보를 LLM으로 배치 심사.

        Args:
            candidates: [{"suffix": str, "examples": list[str], "count": int}, ...]
            llm_ask: prompt(str) -> response(str) callable

        Returns:
            [{"suffix": str, "verdict": "APPROVE"|"REJECT", "reason": str}, ...]
        """
        if not candidates:
            return []

        normalized: list[dict] = []
        for row in candidates[:10]:
            if not isinstance(row, dict):
                continue
            suffix = str(row.get("suffix", "")).strip()
            if not suffix:
                continue

            raw_examples = row.get("examples", [])
            if not isinstance(raw_examples, list):
                raw_examples = [raw_examples]
            examples = [str(x).strip() for x in raw_examples if str(x).strip()][:5]

            try:
                count = int(row.get("count", len(examples)))
            except (TypeError, ValueError):
                count = len(examples)

            normalized.append({"suffix": suffix, "examples": examples, "count": max(1, count)})

        if not normalized:
            return []

        if llm_ask is None:
            return [
                {"suffix": row["suffix"], "verdict": "REJECT", "reason": "llm_ask 콜백 없음 (수동 검토 필요)"}
                for row in normalized
            ]

        prompt = (
            "다음은 웹소설 아이템 regex 안전망에 추가할 접미사 후보 목록입니다.\n"
            '각 후보에 대해 "일반적인 아이템/도구/장비의 접미사로 적합한가?"를 판정해 주세요.\n\n'
            "판정 기준:\n"
            '- APPROVE: 해당 접미사가 아이템 카테고리를 나타냄 (예: "칼", "서", "증")\n'
            '- REJECT: 고유명사/브랜드/우연의 일치 (예: "프로", "플러스", "맥스")\n\n'
            "후보 목록:\n"
            f"{json.dumps(normalized, ensure_ascii=False, indent=2)}\n\n"
            'JSON 배열로 응답: [{"suffix":"...","verdict":"APPROVE"|"REJECT","reason":"..."}]'
        )

        try:
            raw = llm_ask(prompt) or ""
        except Exception as _e:
            logging.debug("[FailureAnalyzer] review_suffix_candidates llm_ask failed: %s", _e)
            raw = ""

        parsed = self._parse_json_array_response(raw)
        parsed_map: dict[str, dict] = {}
        for row in parsed:
            if not isinstance(row, dict):
                continue
            suffix = str(row.get("suffix", "")).strip()
            if not suffix:
                continue
            verdict = str(row.get("verdict", "REJECT")).strip().upper()
            if verdict not in ("APPROVE", "REJECT"):
                verdict = "REJECT"
            reason = str(row.get("reason", "")).strip() or "사유 미기재"
            parsed_map[suffix] = {"suffix": suffix, "verdict": verdict, "reason": reason}

        results: list[dict] = []
        for row in normalized:
            suffix = row["suffix"]
            judged = parsed_map.get(suffix)
            if judged:
                results.append(judged)
            else:
                results.append({"suffix": suffix, "verdict": "REJECT", "reason": "LLM 응답 누락/파싱 실패"})
        return results

    def review_and_apply_suffixes(self, registry, genre: str = "", llm_ask=None) -> dict:
        """미매칭 아이템 → LLM 심사 → APPROVE 시 YAML 자동 append.

        Returns:
            {"reviewed": int, "approved": list[str], "rejected": list[str]}
        """
        report = self.item_suffix_gap_report(registry, genre)
        if report["unmatched_count"] < 10:
            logging.debug("[ItemGap] unmatched %d건 < 10 — 스킵", report["unmatched_count"])
            return {"reviewed": 0, "approved": [], "rejected": []}

        # 후보 구성 (접미사 + 등장 예시)
        candidates = []
        for suffix in report["suggested_suffixes"]:
            examples = [n for n in report["unmatched"] if n.endswith(suffix)][:3]
            candidates.append({"suffix": suffix, "examples": examples, "count": len(examples)})

        if not candidates:
            return {"reviewed": 0, "approved": [], "rejected": []}

        results = self.review_suffix_candidates(candidates, llm_ask=llm_ask)
        approved = [r["suffix"] for r in results if r.get("verdict") == "APPROVE"]
        rejected = [r["suffix"] for r in results if r.get("verdict") == "REJECT"]

        if approved:
            self._append_to_suffix_yaml(genre, approved)
            logging.info("[ItemGap] YAML 자동 추가: genre=%s, suffixes=%s", genre, approved)

        return {"reviewed": len(results), "approved": approved, "rejected": rejected}

    @staticmethod
    def _append_to_suffix_yaml(genre: str, suffixes: list[str]) -> None:
        """APPROVE된 접미사를 item_suffixes.yaml에 자동 append."""
        from pathlib import Path

        import yaml

        from modules.core.genre_schema_builder import _normalize_item_genre_key

        yaml_path = Path(__file__).resolve().parents[2] / "config" / "settings" / "item_suffixes.yaml"
        if not yaml_path.exists():
            logging.warning("[ItemGap] item_suffixes.yaml 없음 — append 스킵")
            return

        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            logging.warning("[ItemGap] YAML 로드 실패: %s", e)
            return

        genre_key = _normalize_item_genre_key(genre) or "_common"
        existing = data.get(genre_key, [])
        if not isinstance(existing, list):
            existing = []

        added = []
        for s in suffixes:
            s = str(s).strip()
            if s and s not in existing:
                existing.append(s)
                added.append(s)

        if not added:
            return

        data[genre_key] = existing
        try:
            yaml_path.write_text(
                yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
                encoding="utf-8",
            )
            logging.info("[ItemGap] item_suffixes.yaml 업데이트: %s += %s", genre_key, added)
        except Exception as e:
            logging.warning("[ItemGap] YAML 쓰기 실패: %s", e)

    def print_report(self) -> None:
        """Print summary report to console."""
        import pprint

        pprint.pprint(self.summary(), width=100, sort_dicts=False)
