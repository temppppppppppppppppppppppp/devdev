"""
[V55.3] Pass Rate Monitor (통과율 모니터링)
실시간 Stage별 통과율 추적 및 분석

핵심: 데이터 기반 품질 개선 의사결정 지원

원리:
1. 각 Stage 시도/통과/실패 기록
2. 실시간 통과율 계산
3. 실패 원인 분류 및 통계
4. 트렌드 분석

비용: $0 (로컬 JSON 저장)

Operator-truth classification:
    - pass_rate_monitor.json is a NON-AUTHORITATIVE convenience cache.
    - It is rebuilt from in-memory records on each save cycle.
    - Authoritative attempt/verdict truth lives in db_manager
      (stage_attempts / director_selections tables) and in
      episode_production.jsonl written by stage4_post_processor.
    - If pass_rate_monitor.json is lost or corrupt, the next session
      starts with an empty record list; no durable truth is lost.

사용:
    monitor = PassRateMonitor(project_path)
    monitor.record_attempt(stage=4, success=True, attempt_num=1)
    stats = monitor.get_stats()
"""

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.core.logging_keys import build_attempt_key


@dataclass
class AttemptRecord:
    """시도 기록"""

    timestamp: str
    stage: int
    episode: int
    arc: int
    attempt_num: int
    success: bool
    reject_reason: str = ""
    generation_method: str = "default"  # default, two_phase, tot, asp, mad
    model_tier: int = 1
    duration_ms: int = 0
    token_cost: float = 0.0
    is_patch: bool = False
    prev_score: float = 0.0
    patch_fallback: bool = False
    attempt_key: str = ""
    final_verdict: str = ""
    director_verdict: str = ""
    gate_basis: str = ""
    repair_scope: str = ""
    fix_pack: dict[str, Any] = field(default_factory=dict)
    retry_budget_axes: dict[str, Any] = field(default_factory=dict)
    patch_strategy: str = ""
    structural_attempted: bool = False
    error_category: str = ""
    reject_bucket: str = ""
    score_breakdown: dict[str, Any] = field(default_factory=dict)
    candidate_key: str = ""
    content_hash: str = ""
    artifact_path: str = ""


@dataclass
class StageStats:
    """Stage별 통계"""

    stage: int
    total_attempts: int = 0
    first_attempt_pass: int = 0
    eventual_pass: int = 0
    total_fail: int = 0
    avg_attempts_to_pass: float = 0.0
    first_attempt_rate: float = 0.0
    eventual_rate: float = 0.0
    common_reject_reasons: dict[str, int] = field(default_factory=dict)
    method_success_rate: dict[str, float] = field(default_factory=dict)


def calculate_episode_rol(
    *,
    token_cost_usd: float,
    duration_ms: int,
    attempts: int,
    quality_score: float,
) -> dict[str, float | int]:
    """Calculate a transparent per-episode ROL score from live-available inputs only."""
    normalized_cost = max(0.0, float(token_cost_usd or 0.0))
    normalized_duration_ms = max(0, int(duration_ms or 0))
    normalized_attempts = max(0, int(attempts or 0))
    normalized_quality = max(0.0, float(quality_score or 0.0))

    duration_minutes = normalized_duration_ms / 60000.0
    retry_penalty = max(0, normalized_attempts - 1)
    investment_score = normalized_cost + duration_minutes + retry_penalty
    rol_score = normalized_quality / max(0.01, investment_score)

    return {
        "quality_score": round(normalized_quality, 2),
        "token_cost_usd": round(normalized_cost, 6),
        "duration_ms": normalized_duration_ms,
        "duration_minutes": round(duration_minutes, 3),
        "attempts": normalized_attempts,
        "retry_penalty": retry_penalty,
        "investment_score": round(investment_score, 6),
        "rol_score": round(rol_score, 4),
    }


class PassRateMonitor:
    """통과율 모니터링 시스템"""

    def __init__(self, project_path: str = None):
        """
        Args:
            project_path: 프로젝트 경로 (logs 저장 위치)
        """
        self.project_path = Path(project_path) if project_path else Path(".")
        self.log_path = self.project_path / "logs" / "pass_rate_monitor.json"
        self.records: list[AttemptRecord] = []
        self.session_start = datetime.now().isoformat()
        self._lock = threading.Lock()

        # 기존 기록 로드
        self._load_records()

    def _load_records(self) -> None:
        """기존 기록 로드"""
        if self.log_path.exists():
            try:
                with open(self.log_path, encoding="utf-8") as f:
                    data = json.load(f)
                    fields = set(AttemptRecord.__dataclass_fields__.keys())
                    self.records = [
                        AttemptRecord(**{k: v for k, v in r.items() if k in fields}) for r in data.get("records", [])
                    ]
            except Exception as e:
                logging.warning(f" [PassRateMonitor] 기록 로드 실패: {e}")
                self.records = []

    def _save_records(self) -> None:
        """기록 저장"""
        try:
            with self._lock:
                records_snapshot = [asdict(r) for r in self.records[-1000:]]  # 최근 1000개만
                total_records = len(self.records)
                session_start = self.session_start
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "session_start": session_start,
                        "last_updated": datetime.now().isoformat(),
                        "total_records": total_records,
                        "records": records_snapshot,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logging.warning(f" [PassRateMonitor] 기록 저장 실패: {e}")

    def record_attempt(
        self,
        stage: int,
        episode: int = 0,
        arc: int = 0,
        attempt_num: int = 1,
        success: bool = False,
        reject_reason: str = "",
        generation_method: str = "default",
        model_tier: int = 1,
        duration_ms: int = 0,
        token_cost: float = 0.0,
        is_patch: bool = False,
        prev_score: float = 0.0,
        patch_fallback: bool = False,
        attempt_key: str = "",
        final_verdict: str = "",
        director_verdict: str = "",
        gate_basis: str = "",
        repair_scope: str = "",
        fix_pack: dict[str, Any] | None = None,
        retry_budget_axes: dict[str, Any] | None = None,
        patch_strategy: str = "",
        structural_attempted: bool = False,
        error_category: str = "",
        reject_bucket: str = "",
        score_breakdown: dict[str, Any] | None = None,
        candidate_key: str = "",
        content_hash: str = "",
        artifact_path: str = "",
    ):
        """
        시도 기록

        Args:
            stage: Stage 번호 (1, 2, 3, 4)
            episode: 에피소드 번호
            arc: Arc 번호
            attempt_num: 시도 횟수 (1부터 시작)
            success: 통과 여부
            reject_reason: REJECT 사유
            generation_method: 생성 방법
            model_tier: 모델 티어
            duration_ms: 소요 시간 (ms)
            token_cost: 토큰 비용 ($)
        """
        record = AttemptRecord(
            timestamp=datetime.now().isoformat(),
            stage=stage,
            episode=episode,
            arc=arc,
            attempt_num=attempt_num,
            success=success,
            reject_reason=reject_reason,
            generation_method=generation_method,
            model_tier=model_tier,
            duration_ms=duration_ms,
            token_cost=token_cost,
            is_patch=is_patch,
            prev_score=prev_score,
            patch_fallback=patch_fallback,
            attempt_key=str(
                attempt_key
                or build_attempt_key(stage=stage, ep_num=episode, arc_num=arc, attempt_num=attempt_num)
            ),
            final_verdict=str(final_verdict or ""),
            director_verdict=str(director_verdict or ""),
            gate_basis=str(gate_basis or ""),
            repair_scope=str(repair_scope or ""),
            fix_pack=dict(fix_pack or {}),
            retry_budget_axes=dict(retry_budget_axes or {}),
            patch_strategy=str(patch_strategy or ""),
            structural_attempted=bool(structural_attempted),
            error_category=str(error_category or ""),
            reject_bucket=str(reject_bucket or ""),
            score_breakdown=dict(score_breakdown or {}),
            candidate_key=str(candidate_key or ""),
            content_hash=str(content_hash or ""),
            artifact_path=str(artifact_path or ""),
        )

        with self._lock:
            self.records.append(record)
            if len(self.records) > 1000:
                self.records = self.records[-1000:]
            should_save = len(self.records) % 100 == 0

        # 100건마다 자동 저장
        if should_save:
            self._save_records()

    def get_stage_stats(self, stage: int, recent_n: int = None) -> StageStats:
        """
        Stage별 통계 계산

        Args:
            stage: Stage 번호
            recent_n: 최근 N건만 분석 (None이면 전체)

        Returns:
            StageStats
        """
        # 해당 Stage 기록 필터링
        with self._lock:
            stage_records = [r for r in self.records if r.stage == stage]
        if recent_n:
            stage_records = stage_records[-recent_n:]

        if not stage_records:
            return StageStats(stage=stage)

        # 에피소드/Arc 단위로 그룹핑
        episodes = {}
        for r in stage_records:
            key = (r.episode, r.arc)
            if key not in episodes:
                episodes[key] = []
            episodes[key].append(r)

        # 통계 계산
        total_attempts = len(stage_records)
        first_attempt_pass = 0
        eventual_pass = 0
        total_fail = 0
        attempts_to_pass = []
        reject_reasons = {}
        method_attempts = {}
        method_success = {}

        for key, records in episodes.items():
            # 첫 시도 통과
            if records[0].success:
                first_attempt_pass += 1
                eventual_pass += 1
                attempts_to_pass.append(1)
            else:
                # 최종 통과 여부
                passed = any(r.success for r in records)
                if passed:
                    eventual_pass += 1
                    pass_attempt = next((i + 1 for i, r in enumerate(records) if r.success), len(records))
                    attempts_to_pass.append(pass_attempt)
                else:
                    total_fail += 1

            # REJECT 사유 집계
            for r in records:
                if not r.success and r.reject_reason:
                    reason_key = r.reject_reason[:50]  # 50자로 제한
                    reject_reasons[reason_key] = reject_reasons.get(reason_key, 0) + 1

                # 생성 방법별 통계
                method = r.generation_method
                method_attempts[method] = method_attempts.get(method, 0) + 1
                if r.success:
                    method_success[method] = method_success.get(method, 0) + 1

        # 비율 계산
        total_episodes = len(episodes)
        first_attempt_rate = first_attempt_pass / total_episodes if total_episodes > 0 else 0
        eventual_rate = eventual_pass / total_episodes if total_episodes > 0 else 0
        avg_attempts = sum(attempts_to_pass) / len(attempts_to_pass) if attempts_to_pass else 0

        # 생성 방법별 성공률
        method_success_rate = {}
        for method, attempts in method_attempts.items():
            successes = method_success.get(method, 0)
            method_success_rate[method] = successes / attempts if attempts > 0 else 0

        # 상위 REJECT 사유
        sorted_reasons = sorted(reject_reasons.items(), key=lambda x: x[1], reverse=True)
        common_reasons = dict(sorted_reasons[:5])

        return StageStats(
            stage=stage,
            total_attempts=total_attempts,
            first_attempt_pass=first_attempt_pass,
            eventual_pass=eventual_pass,
            total_fail=total_fail,
            avg_attempts_to_pass=avg_attempts,
            first_attempt_rate=first_attempt_rate,
            eventual_rate=eventual_rate,
            common_reject_reasons=common_reasons,
            method_success_rate=method_success_rate,
        )

    def get_all_stats(self, recent_n: int = None) -> dict[int, StageStats]:
        """
        전체 Stage 통계

        Args:
            recent_n: 최근 N건만 분석

        Returns:
            {stage: StageStats}
        """
        return {stage: self.get_stage_stats(stage, recent_n) for stage in [1, 2, 3, 4]}

    def get_patch_effectiveness(self, stage: int | None = None, recent_n: int = 200) -> dict[str, Any]:
        """Patch mode effectiveness summary."""
        with self._lock:
            records = list(self.records)
        records = records[-recent_n:] if recent_n else records
        if stage is not None:
            records = [r for r in records if r.stage == stage]

        patch_records = [r for r in records if getattr(r, "is_patch", False)]
        non_patch_records = [r for r in records if not getattr(r, "is_patch", False)]

        patch_attempts = len(patch_records)
        patch_success = sum(1 for r in patch_records if r.success)
        patch_fallbacks = sum(1 for r in patch_records if getattr(r, "patch_fallback", False))
        direct_patch_records = [r for r in patch_records if not getattr(r, "patch_fallback", False)]
        direct_patch_success = sum(1 for r in direct_patch_records if r.success)
        avg_prev_score = (
            sum(float(getattr(r, "prev_score", 0) or 0) for r in patch_records) / patch_attempts
            if patch_attempts
            else 0.0
        )

        return {
            "stage": stage,
            "recent_n": recent_n,
            "total_attempts": len(records),
            "patch_attempts": patch_attempts,
            "patch_success_rate": patch_success / patch_attempts if patch_attempts else 0.0,
            "patch_fallback_rate": patch_fallbacks / patch_attempts if patch_attempts else 0.0,
            "direct_patch_success_rate": direct_patch_success / len(direct_patch_records)
            if direct_patch_records
            else 0.0,
            "non_patch_success_rate": (
                (sum(1 for r in non_patch_records if r.success) / len(non_patch_records)) if non_patch_records else 0.0
            ),
            "avg_prev_score": avg_prev_score,
        }

    def get_episode_rol_snapshot(
        self,
        quality_rows: list[dict[str, Any]] | None,
        *,
        stage: int = 4,
        recent_n: int = 20,
    ) -> dict[str, Any]:
        """Build per-episode ROL rows by joining pass monitor attempts with quality scores."""
        payload: dict[str, Any] = {
            "available": False,
            "stage": stage,
            "recent_n": recent_n,
            "formula_version": "v1_quality_over_cost_time_retry",
            "formula": "quality_score / max(0.01, token_cost_usd + duration_minutes + retry_penalty)",
            "row_count": 0,
            "latest_ep": None,
            "avg_rol": 0.0,
            "best_ep": None,
            "best_rol": 0.0,
            "rows": [],
        }
        if not isinstance(quality_rows, list) or not quality_rows:
            return payload

        # Keep the latest quality row per episode so stale duplicates do not override newer verdicts.
        quality_by_episode: dict[int, dict[str, Any]] = {}
        for row in quality_rows:
            if not isinstance(row, dict):
                continue
            ep_num = int(row.get("ep_num") or 0)
            if ep_num <= 0:
                continue
            quality_entry = {
                "score": float(row.get("score") or 0.0),
                "decision": str(row.get("decision") or "UNKNOWN"),
            }
            quality_by_episode.pop(ep_num, None)
            quality_by_episode[ep_num] = quality_entry

        if not quality_by_episode:
            return payload

        quality_items = list(quality_by_episode.items())
        if recent_n > 0:
            quality_items = quality_items[-recent_n:]
        quality_by_episode = dict(quality_items)
        ordered_eps = sorted(quality_by_episode)

        with self._lock:
            records = [r for r in self.records if r.stage == stage and r.episode > 0]
        if not records:
            return payload

        records_by_episode: dict[int, list[AttemptRecord]] = {}
        for record in records:
            if record.episode not in quality_by_episode:
                continue
            records_by_episode.setdefault(record.episode, []).append(record)

        rows: list[dict[str, Any]] = []
        for ep_num in ordered_eps:
            episode_records = records_by_episode.get(ep_num) or []
            if not episode_records:
                continue

            max_attempt_num = max(int(getattr(record, "attempt_num", 0) or 0) for record in episode_records)
            attempts = max(len(episode_records), max_attempt_num)
            token_cost_usd = sum(max(0.0, float(getattr(record, "token_cost", 0.0) or 0.0)) for record in episode_records)
            duration_ms = sum(max(0, int(getattr(record, "duration_ms", 0) or 0)) for record in episode_records)
            quality_entry = quality_by_episode[ep_num]
            calculation = calculate_episode_rol(
                token_cost_usd=token_cost_usd,
                duration_ms=duration_ms,
                attempts=attempts,
                quality_score=float(quality_entry.get("score") or 0.0),
            )
            rows.append(
                {
                    "ep_num": ep_num,
                    "decision": str(quality_entry.get("decision") or "UNKNOWN"),
                    "success": any(bool(record.success) for record in episode_records),
                    **calculation,
                }
            )

        if not rows:
            return payload

        best_row = max(rows, key=lambda row: float(row.get("rol_score") or 0.0))
        payload.update(
            {
                "available": True,
                "row_count": len(rows),
                "latest_ep": rows[-1]["ep_num"],
                "avg_rol": round(
                    sum(float(row.get("rol_score") or 0.0) for row in rows) / len(rows),
                    4,
                ),
                "best_ep": int(best_row.get("ep_num") or 0),
                "best_rol": round(float(best_row.get("rol_score") or 0.0), 4),
                "rows": rows,
            }
        )
        return payload

    def get_arc_cost_correlation(
        self,
        cost_rows: list[dict[str, Any]] | None,
        *,
        recent_n: int = 10,
    ) -> dict[str, Any]:
        """Join arc difficulty with aggregated arc-cost rows and compute correlation."""
        payload: dict[str, Any] = {
            "available": False,
            "recent_n": recent_n,
            "row_count": 0,
            "latest_arc_no": None,
            "costliest_arc_no": None,
            "hardest_arc_no": None,
            "correlation_coefficient": None,
            "correlation_label": "insufficient_data",
            "rows": [],
        }
        if not isinstance(cost_rows, list) or not cost_rows:
            return payload

        cost_by_arc: dict[int, dict[str, Any]] = {}
        for row in cost_rows:
            if not isinstance(row, dict):
                continue
            scope_type = str(row.get("scope_type", "") or "").strip()
            if scope_type and scope_type != "arc":
                continue
            arc_no = int(row.get("scope_id") or 0)
            if arc_no <= 0:
                continue
            entry = cost_by_arc.setdefault(
                arc_no,
                {
                    "total_cost_usd": 0.0,
                    "total_calls": 0,
                    "total_tokens": 0,
                    "snapshot_count": 0,
                },
            )
            entry["total_cost_usd"] += max(0.0, float(row.get("total_cost_usd") or 0.0))
            entry["total_calls"] += max(0, int(row.get("total_calls") or 0))
            entry["total_tokens"] += max(0, int(row.get("total_tokens") or 0))
            entry["snapshot_count"] += 1

        if not cost_by_arc:
            return payload

        arc_numbers = sorted(cost_by_arc)
        if recent_n > 0:
            arc_numbers = arc_numbers[-recent_n:]

        with self._lock:
            stage4_records = [r for r in self.records if r.stage == 4 and r.arc in set(arc_numbers) and r.episode > 0]

        records_by_arc: dict[int, list[AttemptRecord]] = {}
        for record in stage4_records:
            records_by_arc.setdefault(record.arc, []).append(record)

        rows: list[dict[str, Any]] = []
        for arc_no in arc_numbers:
            arc_records = records_by_arc.get(arc_no) or []
            if not arc_records:
                continue
            episodes: dict[int, list[AttemptRecord]] = {}
            for record in arc_records:
                episodes.setdefault(record.episode, []).append(record)
            episode_count = len(episodes)
            if episode_count <= 0:
                continue

            total_attempts = len(arc_records)
            difficulty = self.get_arc_difficulty(arc_no)
            cost_entry = cost_by_arc[arc_no]
            total_cost_usd = float(cost_entry["total_cost_usd"])
            rows.append(
                {
                    "arc_no": arc_no,
                    "difficulty": str(difficulty.get("difficulty") or "unknown"),
                    "avg_attempts": round(float(difficulty.get("avg_attempts") or 0.0), 1),
                    "episode_count": episode_count,
                    "total_attempts": total_attempts,
                    "hard_episode_count": len(difficulty.get("hard_episodes") or []),
                    "semantic_failure_count": len(difficulty.get("semantic_failures") or []),
                    "total_cost_usd": round(total_cost_usd, 6),
                    "total_calls": int(cost_entry["total_calls"]),
                    "total_tokens": int(cost_entry["total_tokens"]),
                    "snapshot_count": int(cost_entry["snapshot_count"]),
                    "cost_per_episode_usd": round(total_cost_usd / max(1, episode_count), 6),
                    "cost_per_attempt_usd": round(total_cost_usd / max(1, total_attempts), 6),
                }
            )

        if not rows:
            return payload

        xs = [float(row["avg_attempts"]) for row in rows]
        ys = [float(row["total_cost_usd"]) for row in rows]
        correlation_coefficient = None
        if len(rows) >= 2:
            mean_x = sum(xs) / len(xs)
            mean_y = sum(ys) / len(ys)
            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=False))
            denominator_x = sum((x - mean_x) ** 2 for x in xs)
            denominator_y = sum((y - mean_y) ** 2 for y in ys)
            if denominator_x > 0 and denominator_y > 0:
                correlation_coefficient = numerator / ((denominator_x * denominator_y) ** 0.5)

        if correlation_coefficient is None:
            correlation_label = "insufficient_data"
        elif correlation_coefficient >= 0.75:
            correlation_label = "strong_positive"
        elif correlation_coefficient >= 0.25:
            correlation_label = "positive"
        elif correlation_coefficient <= -0.75:
            correlation_label = "strong_negative"
        elif correlation_coefficient <= -0.25:
            correlation_label = "negative"
        else:
            correlation_label = "flat"

        costliest_row = max(rows, key=lambda row: float(row.get("total_cost_usd") or 0.0))
        hardest_row = max(rows, key=lambda row: float(row.get("avg_attempts") or 0.0))
        payload.update(
            {
                "available": True,
                "row_count": len(rows),
                "latest_arc_no": rows[-1]["arc_no"],
                "costliest_arc_no": int(costliest_row.get("arc_no") or 0),
                "hardest_arc_no": int(hardest_row.get("arc_no") or 0),
                "correlation_coefficient": round(correlation_coefficient, 4)
                if correlation_coefficient is not None
                else None,
                "correlation_label": correlation_label,
                "rows": rows,
            }
        )
        return payload

    def get_summary(self, recent_n: int = 100) -> str:
        """
        요약 문자열 생성

        Args:
            recent_n: 최근 N건 기준

        Returns:
            요약 문자열
        """
        all_stats = self.get_all_stats(recent_n)

        lines = [
            "=" * 50,
            f"[V55.3 Pass Rate Monitor] 최근 {recent_n}건 기준",
            "=" * 50,
            "",
            "Stage | 첫시도 | 최종  | 평균시도 | 총실패",
            "-" * 50,
        ]

        for stage in [1, 2, 3, 4]:
            stats = all_stats[stage]
            lines.append(
                f"  {stage}   | {stats.first_attempt_rate:5.1%}  | "
                f"{stats.eventual_rate:5.1%} | {stats.avg_attempts_to_pass:5.1f}회  | "
                f"{stats.total_fail:3d}"
            )

        lines.append("")
        lines.append("생성 방법별 성공률:")
        lines.append("-" * 50)

        # 전체 방법 집계
        all_methods = set()
        for stats in all_stats.values():
            all_methods.update(stats.method_success_rate.keys())

        for method in sorted(all_methods):
            rates = []
            for stage in [2, 3, 4]:
                rate = all_stats[stage].method_success_rate.get(method, 0)
                rates.append(f"S{stage}:{rate:.0%}")
            lines.append(f"  {method:12s} | {' | '.join(rates)}")

        lines.append("")
        lines.append("주요 REJECT 사유 (Stage 4):")
        lines.append("-" * 50)

        s4_stats = all_stats[4]
        for reason, count in list(s4_stats.common_reject_reasons.items())[:5]:
            lines.append(f"  [{count:3d}] {reason[:40]}")

        lines.append("=" * 50)

        return "\n".join(lines)

    def get_trend(self, stage: int, window: int = 20) -> dict[str, Any]:
        """
        트렌드 분석 (최근 vs 이전)

        Args:
            stage: Stage 번호
            window: 윈도우 크기

        Returns:
            트렌드 정보
        """
        with self._lock:
            stage_records = [r for r in self.records if r.stage == stage]

        if len(stage_records) < window * 2:
            return {"trend": "insufficient_data"}

        recent = stage_records[-window:]
        previous = stage_records[-window * 2 : -window]

        recent_rate = sum(1 for r in recent if r.success) / len(recent)
        previous_rate = sum(1 for r in previous if r.success) / len(previous)

        diff = recent_rate - previous_rate

        if diff > 0.05:
            trend = "improving"
        elif diff < -0.05:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "recent_rate": recent_rate,
            "previous_rate": previous_rate,
            "diff": diff,
            "window": window,
        }

    def check_alerts(self, window: int = 20) -> list[str]:
        """
        통과율 하락 경고 체크

        Args:
            window: 분석 윈도우 크기

        Returns:
            경고 메시지 리스트
        """
        alerts = []

        for stage in [2, 3, 4]:
            trend_info = self.get_trend(stage, window)

            if trend_info.get("trend") == "declining":
                diff = trend_info.get("diff", 0)
                recent_rate = trend_info.get("recent_rate", 0)

                if diff < -0.15:  # 15% 이상 급락
                    alerts.append(f"🚨 [Stage {stage}] 통과율 급락: {recent_rate:.0%} (이전 대비 {abs(diff):.0%}↓)")
                elif diff < -0.05:  # 5% 이상 하락
                    alerts.append(f"⚠️ [Stage {stage}] 통과율 하락: {recent_rate:.0%} (이전 대비 {abs(diff):.0%}↓)")

        # 전체 첫 시도 통과율 확인
        for stage in [3, 4]:
            stats = self.get_stage_stats(stage, recent_n=window)
            if stats.first_attempt_rate < 0.5 and stats.total_attempts >= 10:
                alerts.append(f"📉 [Stage {stage}] 첫 시도 통과율 50% 미만: {stats.first_attempt_rate:.0%}")

        return alerts

    def get_arc_difficulty(self, arc_no: int) -> dict[str, Any]:
        """
        Arc별 집필 난이도 추정 (Stage 4 시도 횟수 기반).

        Returns:
            {
                "arc_no": int,
                "difficulty": "easy" | "normal" | "hard" | "unknown",
                "avg_attempts": float,
                "hard_episodes": list[int],
                "semantic_failures": list[dict],
            }
        """
        if arc_no <= 0:
            return {
                "arc_no": arc_no,
                "difficulty": "unknown",
                "avg_attempts": 0.0,
                "hard_episodes": [],
                "semantic_failures": [],
            }

        with self._lock:
            arc_records = [r for r in self.records if r.stage == 4 and r.arc == arc_no and r.episode > 0]
        if not arc_records:
            return {
                "arc_no": arc_no,
                "difficulty": "unknown",
                "avg_attempts": 0.0,
                "hard_episodes": [],
                "semantic_failures": [],
            }

        episodes: dict[int, list[AttemptRecord]] = {}
        for record in arc_records:
            episodes.setdefault(record.episode, []).append(record)

        attempts_per_ep: list[int] = []
        hard_eps: list[int] = []
        for episode, recs in sorted(episodes.items()):
            attempt_count = len(recs)
            attempts_per_ep.append(attempt_count)
            if attempt_count >= 3:
                hard_eps.append(episode)

        avg_attempts = sum(attempts_per_ep) / len(attempts_per_ep) if attempts_per_ep else 0.0
        if avg_attempts <= 1.5:
            difficulty = "easy"
        elif avg_attempts <= 3.0:
            difficulty = "normal"
        else:
            difficulty = "hard"

        semantic_failures: list[dict[str, Any]] = []
        failed_records = sorted(
            (record for record in arc_records if not record.success),
            key=lambda record: (record.episode, record.attempt_num),
        )
        for record in failed_records[-5:]:
            semantic_failures.append(
                {
                    "episode": record.episode,
                    "attempt_num": record.attempt_num,
                    "error_category": str(record.error_category or ""),
                    "reject_bucket": str(record.reject_bucket or ""),
                    "score_breakdown": dict(record.score_breakdown or {}),
                    "reject_reason": str(record.reject_reason or "")[:160],
                }
            )

        return {
            "arc_no": arc_no,
            "difficulty": difficulty,
            "avg_attempts": round(avg_attempts, 1),
            "hard_episodes": hard_eps,
            "semantic_failures": semantic_failures,
        }

    def save(self) -> None:
        """명시적 저장"""
        self._save_records()


# 싱글톤 인스턴스
_monitor_instance: PassRateMonitor | None = None
_monitor_project_path: str | None = None  # [V70] 프로젝트 경로 추적
_monitor_lock = threading.Lock()


def get_monitor(project_path: str = None) -> PassRateMonitor:
    """싱글톤 모니터 인스턴스 반환 [V70] 프로젝트 변경 시 재생성"""
    global _monitor_instance, _monitor_project_path
    if _monitor_instance is None or (project_path and project_path != _monitor_project_path):
        with _monitor_lock:
            if _monitor_instance is None or (project_path and project_path != _monitor_project_path):
                _monitor_instance = PassRateMonitor(project_path)
                _monitor_project_path = project_path
    return _monitor_instance


def reset_monitor() -> None:
    """[V70] 싱글톤 리셋"""
    global _monitor_instance, _monitor_project_path
    _monitor_instance = None
    _monitor_project_path = None
