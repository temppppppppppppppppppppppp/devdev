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
                logging.warning(f"⚠️ [PassRateMonitor] 기록 로드 실패: {e}")
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
            logging.warning(f"⚠️ [PassRateMonitor] 기록 저장 실패: {e}")

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
            }
        """
        if arc_no <= 0:
            return {
                "arc_no": arc_no,
                "difficulty": "unknown",
                "avg_attempts": 0.0,
                "hard_episodes": [],
            }

        with self._lock:
            arc_records = [r for r in self.records if r.stage == 4 and r.arc == arc_no and r.episode > 0]
        if not arc_records:
            return {
                "arc_no": arc_no,
                "difficulty": "unknown",
                "avg_attempts": 0.0,
                "hard_episodes": [],
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

        return {
            "arc_no": arc_no,
            "difficulty": difficulty,
            "avg_attempts": round(avg_attempts, 1),
            "hard_episodes": hard_eps,
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
