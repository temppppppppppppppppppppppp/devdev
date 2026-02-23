"""
[V60] Quality Dashboard - 품질 메트릭 추적 및 분석

ValidationOrchestrator 결과를 수집하고 분석하는 대시보드 기초 모듈.
Streamlit 또는 콘솔 출력을 위한 데이터 제공.

Usage:
    dashboard = QualityDashboard()
    dashboard.record_validation(ep_num, result, stage)
    summary = dashboard.get_summary()
"""

import json
import logging
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class QualityDashboard:
    """
    품질 메트릭 추적 및 분석

    Features:
    - Stage별 PASS/REJECT 비율 추적
    - 에피소드별 점수 추이
    - 실패 패턴 분석
    - HUD 급변 이력
    - Blueprint 커버리지 추이
    """

    def __init__(self, project_path: Path | None = None):
        self.project_path = project_path
        self.metrics_file = project_path / "logs" / "quality_metrics.jsonl" if project_path else None
        self._max_history = 500
        self._max_stage_scores = 500

        # 인메모리 메트릭
        self.validation_history: list[dict] = []
        self.stage_stats: dict[int, dict] = defaultdict(lambda: {"pass": 0, "reject": 0, "scores": []})
        self.hud_anomalies: list[dict] = []
        self.blueprint_coverage: list[dict] = []

        # 파일에서 기존 메트릭 로드
        if self.metrics_file and self.metrics_file.exists():
            self._load_metrics()

    def _load_metrics(self) -> None:
        """파일에서 메트릭 로드"""
        try:
            with open(self.metrics_file, encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            record = json.loads(line)
                            self._process_record(record)
                        except (json.JSONDecodeError, Exception) as e:  # [V70] 한 줄 오류가 전체 로딩 중단 방지
                            logging.info(f"[QualityDashboard] 메트릭 라인 {line_no} 스킵: {e}")
        except Exception as e:
            logging.warning(f"[QualityDashboard] 메트릭 파일 로드 실패: {e}")

    def _process_record(self, record: dict):
        """레코드 처리 및 통계 업데이트"""
        record_type = record.get("type")

        if record_type == "validation":
            self.validation_history.append(record)
            stage = record.get("stage", 4)
            decision = record.get("decision", "UNKNOWN")
            score = record.get("score", 0)

            if decision == "PASS":
                self.stage_stats[stage]["pass"] += 1
            else:
                self.stage_stats[stage]["reject"] += 1

            if score > 0:
                self.stage_stats[stage]["scores"].append(score)
            self._trim_histories(stage=stage)

        elif record_type == "hud_anomaly":
            self.hud_anomalies.append(record)
            self._trim_histories()

        elif record_type == "blueprint_coverage":
            self.blueprint_coverage.append(record)
            self._trim_histories()

    def _trim_histories(self, stage: int | None = None) -> None:
        if len(self.validation_history) > self._max_history:
            self.validation_history = self.validation_history[-self._max_history :]
        if len(self.hud_anomalies) > self._max_history:
            self.hud_anomalies = self.hud_anomalies[-self._max_history :]
        if len(self.blueprint_coverage) > self._max_history:
            self.blueprint_coverage = self.blueprint_coverage[-self._max_history :]

        if stage is not None:
            scores = self.stage_stats[stage]["scores"]
            if len(scores) > self._max_stage_scores:
                self.stage_stats[stage]["scores"] = scores[-self._max_stage_scores :]

    def record_validation(self, ep_num: int, result: dict, stage: int = 4):
        """
        검증 결과 기록

        Args:
            ep_num: 에피소드 번호
            result: 검증 결과 (decision, score, violations 등)
            stage: 스테이지 번호 (2, 3, 4)
        """
        record = {
            "type": "validation",
            "timestamp": datetime.now().isoformat(),
            "ep_num": ep_num,
            "stage": stage,
            "decision": result.get("decision", "UNKNOWN"),
            "score": result.get("score", 0),
            "violations": [
                v.get("type") if isinstance(v, dict) else str(v) for v in result.get("violations", [])
            ],  # [V70] str 타입 방어
            "warnings": len(result.get("warnings", [])),
        }

        self._process_record(record)
        self._save_record(record)

        return record

    def record_hud_anomaly(self, ep_num: int, anomalies: list[dict]):
        """
        HUD 급변 감지 기록

        Args:
            ep_num: 에피소드 번호
            anomalies: 감지된 급변 목록
        """
        record = {
            "type": "hud_anomaly",
            "timestamp": datetime.now().isoformat(),
            "ep_num": ep_num,
            "count": len(anomalies),
            "types": [a.get("type") for a in anomalies],
            "severities": [a.get("severity", "medium") for a in anomalies],
        }

        self._process_record(record)
        self._save_record(record)

        return record

    def record_blueprint_coverage(self, ep_num: int, coverage_result: dict):
        """
        Blueprint 커버리지 기록

        Args:
            ep_num: 에피소드 번호
            coverage_result: _validate_blueprint_completeness_v60() 결과
        """
        record = {
            "type": "blueprint_coverage",
            "timestamp": datetime.now().isoformat(),
            "ep_num": ep_num,
            "coverage": coverage_result.get("scene_coverage", 0),
            "expected": coverage_result.get("expected_scenes", 0),
            "reflected": coverage_result.get("reflected_scenes", 0),
            "valid": coverage_result.get("valid", True),
        }

        self._process_record(record)
        self._save_record(record)

        return record

    def _save_record(self, record: dict):
        """레코드를 파일에 저장"""
        if not self.metrics_file:
            return

        try:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logging.warning(f"[QualityDashboard] 레코드 저장 실패: {e}")

    def get_summary(self) -> dict:
        """
        품질 요약 통계 반환

        Returns:
            {
                'total_validations': int,
                'stage_stats': {
                    2: {'pass_rate': float, 'avg_score': float},
                    3: {'pass_rate': float, 'avg_score': float},
                    4: {'pass_rate': float, 'avg_score': float}
                },
                'hud_anomaly_rate': float,
                'avg_blueprint_coverage': float,
                'common_violations': [str, ...]
            }
        """
        summary = {
            "total_validations": len(self.validation_history),
            "stage_stats": {},
            "hud_anomaly_rate": 0,
            "avg_blueprint_coverage": 0,
            "common_violations": [],
        }

        # Stage별 통계
        for stage, stats in self.stage_stats.items():
            total = stats["pass"] + stats["reject"]
            if total > 0:
                pass_rate = stats["pass"] / total * 100
                avg_score = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
                summary["stage_stats"][stage] = {
                    "pass_rate": round(pass_rate, 1),
                    "avg_score": round(avg_score, 1),
                    "total": total,
                }

        # HUD 급변 비율
        if self.validation_history:
            anomaly_eps = set(a.get("ep_num") for a in self.hud_anomalies)
            summary["hud_anomaly_rate"] = round(len(anomaly_eps) / len(self.validation_history) * 100, 1)

        # 평균 Blueprint 커버리지
        if self.blueprint_coverage:
            coverages = [c.get("coverage", 0) for c in self.blueprint_coverage]
            summary["avg_blueprint_coverage"] = round(sum(coverages) / len(coverages), 1)

        # 빈번한 위반 유형
        violation_counts = defaultdict(int)
        for record in self.validation_history:
            for v in record.get("violations", []):
                violation_counts[v] += 1

        summary["common_violations"] = sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return summary

    def get_episode_trend(self, n_episodes: int = 20) -> list[dict]:
        """
        최근 N개 에피소드의 품질 추이

        Args:
            n_episodes: 조회할 에피소드 수

        Returns:
            [{'ep_num': int, 'score': float, 'decision': str, 'coverage': float}, ...]
        """
        recent = self.validation_history[-n_episodes:] if self.validation_history else []

        trend = []
        for record in recent:
            ep_num = record.get("ep_num")

            # Blueprint 커버리지 찾기
            coverage = None
            for c in self.blueprint_coverage:
                if c.get("ep_num") == ep_num:
                    coverage = c.get("coverage")
                    break

            trend.append(
                {
                    "ep_num": ep_num,
                    "score": record.get("score", 0),
                    "decision": record.get("decision", "UNKNOWN"),
                    "coverage": coverage,
                    "violations": len(record.get("violations", [])),
                }
            )

        return trend

    def get_failure_patterns(self) -> dict:
        """
        실패 패턴 분석

        Returns:
            {
                'by_stage': {2: [...], 3: [...], 4: [...]},
                'by_type': {'item': 5, 'continuity': 3, ...},
                'by_episode_range': {'1-10': 3, '11-20': 5, ...}
            }
        """
        patterns = {"by_stage": defaultdict(list), "by_type": defaultdict(int), "by_episode_range": defaultdict(int)}

        for record in self.validation_history:
            if record.get("decision") == "REJECT":
                stage = record.get("stage", 4)
                ep_num = record.get("ep_num", 0)

                patterns["by_stage"][stage].append({"ep_num": ep_num, "violations": record.get("violations", [])})

                for v in record.get("violations", []):
                    patterns["by_type"][v] += 1

                # 에피소드 범위별 집계
                ep_num = max(1, ep_num)  # [V70] ep_num=0이면 음수 범위키 방지
                range_key = f"{(ep_num - 1) // 10 * 10 + 1}-{(ep_num - 1) // 10 * 10 + 10}"
                patterns["by_episode_range"][range_key] += 1

        return patterns

    def get_frequent_reject_warning(self, stage: int = 4, recent_n: int = 10) -> str:
        """
        [V60.5] 빈번 REJECT 사유 경고 생성

        최근 N회의 REJECT 사유를 분석하여 Writer에게 사전 경고 제공.

        Args:
            stage: 분석할 Stage
            recent_n: 최근 N회 분석

        Returns:
            경고 문자열 (없으면 빈 문자열)
        """
        # 최근 REJECT 기록 필터링
        recent_rejects = [
            r
            for r in self.validation_history[-50:]  # 최근 50개 중
            if r.get("decision") == "REJECT" and r.get("stage") == stage
        ][-recent_n:]  # 마지막 N개

        if len(recent_rejects) < 2:
            return ""

        # REJECT 사유 카운트
        reason_counts = defaultdict(int)
        reason_keywords = {
            "분량": ["분량", "자", "length", "짧"],
            "서사 폭주": ["폭주", "압축", "빠르"],
            "서사 정체": ["정체", "반복", "지루"],
            "씬 미반영": ["씬", "scene", "장면", "누락"],
            "설정 오류": ["설정", "무공", "오류", "모순"],
            "밀도 불균형": ["밀도", "균형", "요약"],
        }

        for record in recent_rejects:
            violations = record.get("violations", [])
            for v in violations:
                v_lower = str(v).lower() if v else ""
                for reason_name, keywords in reason_keywords.items():
                    if any(kw in v_lower for kw in keywords):
                        reason_counts[reason_name] += 1
                        break

        if not reason_counts:
            return ""

        # 빈번한 사유 추출 (2회 이상)
        frequent = [(name, count) for name, count in reason_counts.items() if count >= 2]
        if not frequent:
            return ""

        frequent.sort(key=lambda x: x[1], reverse=True)

        # 경고 생성
        lines = ["[⚠️ V60.5 빈번 REJECT 사유 경고]", f"최근 {len(recent_rejects)}회 REJECT 중 반복되는 패턴:", ""]

        for reason, count in frequent[:3]:  # 상위 3개
            lines.append(f"  🔴 {reason}: {count}회 발생")

            # 사유별 구체적 조언
            if reason == "분량":
                lines.append("     → 4,500자 이상 확보. 심리 묘사, 조연 리액션 추가.")
            elif reason == "서사 폭주":
                lines.append("     → 사건을 더 잘게 쪼개라. 과정을 상세히 묘사.")
            elif reason == "서사 정체":
                lines.append("     → 반복 대신 인과적 전진. 새로운 정보/사건 추가.")
            elif reason == "씬 미반영":
                lines.append("     → Blueprint 6개 씬 모두 반영. 특히 후반부 씬 주의.")
            elif reason == "설정 오류":
                lines.append("     → 직전 화 확인. 미습득 무공/장비 사용 금지.")
            elif reason == "밀도 불균형":
                lines.append("     → 앞뒤 분량 균등. 후반부 요약 금지.")

        lines.append("")
        lines.append("⚠️ 위 패턴은 반복 REJECT의 주요 원인입니다. 특히 주의하세요.")

        return "\n".join(lines)

    def print_console_summary(self) -> None:
        """콘솔에 요약 출력"""
        summary = self.get_summary()

        logging.info("\n" + "=" * 60)
        logging.info(" [V60] Quality Dashboard Summary")
        logging.info("=" * 60)

        logging.info(f"\n📊 총 검증 횟수: {summary['total_validations']}")

        logging.info("\n📈 Stage별 통계:")
        for stage, stats in sorted(summary["stage_stats"].items()):
            logging.info(
                f"Stage {stage}: PASS {stats['pass_rate']}% | 평균 점수 {stats['avg_score']} | 총 {stats['total']}회"
            )

        logging.info(f"\n⚠️ HUD 급변 비율: {summary['hud_anomaly_rate']}%")
        logging.info(f"📋 평균 Blueprint 커버리지: {summary['avg_blueprint_coverage']}%")

        if summary["common_violations"]:
            logging.warning("\n❌ 빈번한 위반 유형:")
            for violation, count in summary["common_violations"]:
                logging.info(f"- {violation}: {count}회")

        logging.info("\n" + "=" * 60)

    def analyze_score_trend(self, stage: int = 4, window: int = 5) -> dict:
        """
        [V60.4] 점수 추이 분석 및 피드백 생성

        Args:
            stage: 분석할 Stage (2, 3, 4)
            window: 최근 N개 검증 분석

        Returns:
            {
                'trend': 'improving' | 'declining' | 'stable' | 'fluctuating',
                'recent_avg': float,
                'overall_avg': float,
                'feedback': str,
                'alert_level': 'success' | 'warning' | 'danger'
            }
        """
        stage_records = [r for r in self.validation_history if r.get("stage") == stage and r.get("score", 0) > 0]

        if len(stage_records) < 3:
            return {
                "trend": "insufficient_data",
                "recent_avg": 0,
                "overall_avg": 0,
                "feedback": "충분한 데이터가 없습니다.",
                "alert_level": "info",
            }

        # 전체 평균
        # [Sweep60] score=None 방어 (key 존재 시 get default 무시됨)
        all_scores = [r.get("score") or 0 for r in stage_records]
        overall_avg = sum(all_scores) / len(all_scores)

        # 최근 평균
        recent_records = stage_records[-window:]
        recent_scores = [r.get("score") or 0 for r in recent_records]
        recent_avg = sum(recent_scores) / len(recent_scores)

        # 추이 분석
        if len(stage_records) >= window * 2:
            older_records = stage_records[-(window * 2) : -window]
            older_scores = [r.get("score") or 0 for r in older_records]
            older_avg = sum(older_scores) / len(older_scores)

            diff = recent_avg - older_avg
            if diff >= 10:
                trend = "improving"
            elif diff <= -10:
                trend = "declining"
            else:
                # 변동성 체크
                variance = sum((s - recent_avg) ** 2 for s in recent_scores) / len(recent_scores)
                if variance > 100:  # 표준편차 10점 이상
                    trend = "fluctuating"
                else:
                    trend = "stable"
        else:
            trend = "stable"

        # 피드백 생성
        feedback_map = {
            "improving": f"✅ 점수가 상승 추세입니다! (최근 평균: {recent_avg:.1f}점)",
            "declining": f"⚠️ 점수가 하락 추세입니다. (최근 평균: {recent_avg:.1f}점, 전체 평균: {overall_avg:.1f}점)",
            "stable": f"➡️ 점수가 안정적입니다. (평균: {recent_avg:.1f}점)",
            "fluctuating": "🎢 점수가 불안정합니다. 일관성 있는 품질 유지가 필요합니다.",
        }

        alert_map = {
            "improving": "success",
            "declining": "danger" if recent_avg < 60 else "warning",
            "stable": "success" if recent_avg >= 70 else "warning",
            "fluctuating": "warning",
        }

        return {
            "trend": trend,
            "recent_avg": round(recent_avg, 1),
            "overall_avg": round(overall_avg, 1),
            "feedback": feedback_map.get(trend, ""),
            "alert_level": alert_map.get(trend, "info"),
        }

    def get_trend_injection(self, stage: int = 4) -> str:
        """
        [V60.4] Writer/Architect 프롬프트에 주입할 추이 기반 가이드 생성

        Args:
            stage: Stage 번호

        Returns:
            프롬프트 주입용 문자열
        """
        analysis = self.analyze_score_trend(stage=stage)

        if analysis["trend"] == "insufficient_data":
            return ""

        lines = [f"[V60.4 품질 추이 분석 - Stage {stage}]"]
        lines.append(analysis["feedback"])

        # 추가 가이드
        if analysis["trend"] == "declining":
            lines.append("\n🔧 개선 제안:")
            lines.append("- 최근 REJECT 사유를 확인하고 반복 오류를 피하라")
            lines.append("- 분량, 밀도, 씬 균등성을 다시 점검하라")
            if stage == 4:
                lines.append("- 대화와 묘사의 균형을 맞춰라")

        elif analysis["trend"] == "fluctuating":
            lines.append("\n🔧 안정화 제안:")
            lines.append("- 성공한 에피소드의 패턴을 참고하라")
            lines.append("- 무리한 실험보다 안정적인 구조를 우선하라")

        elif analysis["trend"] == "improving":
            lines.append("\n✨ 현재 패턴을 유지하라. 성공 요인:")
            if analysis["recent_avg"] >= 80:
                lines.append("- 품질이 우수합니다. 이 방향을 계속 유지하세요.")

        return "\n".join(lines)

    # ══════════════════════════════════════════════════════════════
    # [Phase 3-QR] Quality Score Regression Detection
    # ══════════════════════════════════════════════════════════════

    def detect_score_regression(
        self,
        ep_num: int | None = None,
        stage: int = 4,
    ) -> dict[str, Any]:
        """
        에피소드 간 점수 회귀 감지.

        직전 에피소드 대비 점수가 drop_threshold 이상 하락하면 regression,
        warning_threshold 이상이면 warning으로 판정.

        Args:
            ep_num: 대상 에피소드 (None이면 가장 최근)
            stage: 분석 대상 Stage

        Returns:
            {
                'is_regression': bool,
                'severity': 'regression' | 'warning' | 'none' | 'insufficient_data',
                'delta': int,
                'baseline_avg': float,
                'recent_avg': float,
                'reason': str,
            }
        """
        from modules.validation.threshold_helper import _threshold

        drop_th = _threshold("quality_regression.drop_threshold", 20)
        warn_th = _threshold("quality_regression.warning_threshold", 10)
        min_samples = _threshold("quality_regression.min_samples", 2)

        # Stage 필터 + 점수 > 0인 PASS 기록만
        scored = [r for r in self.validation_history if r.get("stage") == stage and r.get("score", 0) > 0]

        if len(scored) < min_samples:
            return {
                "is_regression": False,
                "severity": "insufficient_data",
                "delta": 0,
                "baseline_avg": 0,
                "recent_avg": 0,
                "reason": f"데이터 부족 ({len(scored)}/{min_samples})",
            }

        # ep_num 지정 시 해당 에피소드까지만
        if ep_num is not None:
            scored = [r for r in scored if r.get("ep_num", 0) <= ep_num]
            if len(scored) < min_samples:
                return {
                    "is_regression": False,
                    "severity": "insufficient_data",
                    "delta": 0,
                    "baseline_avg": 0,
                    "recent_avg": 0,
                    "reason": f"ep {ep_num}까지 데이터 부족",
                }

        try:
            current_score = int(scored[-1].get("score", 0))
            prev_score = int(scored[-2].get("score", 0))
        except (ValueError, TypeError):
            current_score, prev_score = 0, 0
        delta = prev_score - current_score  # 양수 = 하락

        # 기준선 평균 (최근 제외 직전 N개)
        window = _threshold("quality_regression.window", 5)
        baseline_records = scored[:-1][-window:]
        baseline_scores = []
        for r in baseline_records:
            try:
                baseline_scores.append(int(r.get("score", 0)))
            except (ValueError, TypeError):
                baseline_scores.append(0)
        baseline_avg = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0

        if delta >= drop_th:
            return {
                "is_regression": True,
                "severity": "regression",
                "delta": delta,
                "baseline_avg": round(baseline_avg, 1),
                "recent_avg": round(current_score, 1),
                "reason": f"직전 대비 {delta}점 하락 (임계값 {drop_th})",
            }
        elif delta >= warn_th:
            return {
                "is_regression": False,
                "severity": "warning",
                "delta": delta,
                "baseline_avg": round(baseline_avg, 1),
                "recent_avg": round(current_score, 1),
                "reason": f"직전 대비 {delta}점 하락 (경고 수준)",
            }
        else:
            return {
                "is_regression": False,
                "severity": "none",
                "delta": delta,
                "baseline_avg": round(baseline_avg, 1),
                "recent_avg": round(current_score, 1),
                "reason": "정상 범위",
            }

    def get_score_trend_summary(
        self,
        stage: int = 4,
        recent_n: int = 5,
    ) -> dict[str, Any]:
        """
        최근 N화 점수 추세 요약.

        Args:
            stage: 분석 대상 Stage
            recent_n: 윈도우 크기

        Returns:
            {
                'trend': 'up' | 'down' | 'flat' | 'insufficient_data',
                'window_size': int,
                'avg': float,
                'min': int,
                'max': int,
                'delta': int,       # 윈도우 첫 점수 → 마지막 점수 차이
                'samples': int,
                'summary': str,     # 1줄 한국어 요약
            }
        """
        from modules.validation.threshold_helper import _threshold

        min_samples = _threshold("quality_regression.min_samples", 2)

        scored = [r for r in self.validation_history if r.get("stage") == stage and r.get("score", 0) > 0]

        recent = scored[-recent_n:] if scored else []

        if len(recent) < min_samples:
            return {
                "trend": "insufficient_data",
                "window_size": recent_n,
                "avg": 0,
                "min": 0,
                "max": 0,
                "delta": 0,
                "samples": len(recent),
                "summary": f"데이터 부족 ({len(recent)}화)",
            }

        scores = []
        for r in recent:
            try:
                scores.append(int(r.get("score", 0)))
            except (ValueError, TypeError):
                scores.append(0)
        avg = sum(scores) / len(scores)
        s_min = min(scores)
        s_max = max(scores)
        delta = scores[-1] - scores[0]

        # 추세 판정: 선형 방향
        if len(scores) >= 3:
            first_half = scores[: len(scores) // 2]
            second_half = scores[len(scores) // 2 :]
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            diff = second_avg - first_avg
            if diff >= 5:
                trend = "up"
            elif diff <= -5:
                trend = "down"
            else:
                trend = "flat"
        else:
            trend = "up" if delta > 0 else ("down" if delta < 0 else "flat")

        trend_label = {"up": "상승", "down": "하락", "flat": "안정"}[trend]

        return {
            "trend": trend,
            "window_size": recent_n,
            "avg": round(avg, 1),
            "min": s_min,
            "max": s_max,
            "delta": delta,
            "samples": len(scores),
            "summary": f"최근 {len(scores)}화 평균 {avg:.0f}점, 추세: {trend_label} (직전 대비 {delta:+d})",
        }

    def get_windowed_quality_trend(self, window_size: int = 10, stage: int = 4) -> list[dict[str, Any]]:
        """
        N 에피소드 단위의 품질 추세(평균 점수/통과율) 반환.

        Args:
            window_size: 윈도우 크기
            stage: 분석 대상 Stage

        Returns:
            [{"window": "ep1-10", "avg_score": 75.2, "pass_rate": 0.8, "count": 10}, ...]
        """
        if window_size <= 0:
            return []

        scored = [
            r
            for r in self.validation_history
            if r.get("stage") == stage and isinstance(r.get("score"), int | float) and r.get("score", 0) > 0
        ]
        if not scored:
            return []

        windows: list[dict[str, Any]] = []
        for i in range(0, len(scored), window_size):
            chunk = scored[i : i + window_size]
            if not chunk:
                continue

            scores = [float(r.get("score") or 0) for r in chunk]
            passes = sum(1 for r in chunk if r.get("decision") == "PASS")
            ep_start = chunk[0].get("ep_num", "?")
            ep_end = chunk[-1].get("ep_num", "?")

            windows.append(
                {
                    "window": f"ep{ep_start}-{ep_end}",
                    "avg_score": round(sum(scores) / len(scores), 1),
                    "pass_rate": round(passes / len(chunk), 2),
                    "count": len(chunk),
                }
            )

        return windows

    def detect_quality_drift(self, stage: int = 4, min_windows: int = 3, window_size: int = 10) -> dict[str, Any]:
        """
        윈도우 기반 장기 품질 드리프트(하락/상승/안정) 감지.

        Args:
            stage: 분석 대상 Stage
            min_windows: 판정에 필요한 최소 윈도우 수
            window_size: 윈도우 크기

        Returns:
            {"drift": str, "recent_avg": float, "overall_avg": float, "windows": int}
        """
        windows = self.get_windowed_quality_trend(window_size=window_size, stage=stage)
        if len(windows) < min_windows:
            return {
                "drift": "insufficient_data",
                "recent_avg": 0.0,
                "overall_avg": 0.0,
                "windows": len(windows),
            }

        recent_window_scores = [
            w["avg_score"] for w in windows[-min_windows:] if isinstance(w.get("avg_score"), int | float)
        ]
        all_window_scores = [w["avg_score"] for w in windows if isinstance(w.get("avg_score"), int | float)]

        if not recent_window_scores or not all_window_scores:
            return {
                "drift": "insufficient_data",
                "recent_avg": 0.0,
                "overall_avg": 0.0,
                "windows": len(windows),
            }

        recent_avg = round(sum(recent_window_scores) / len(recent_window_scores), 1)
        overall_avg = round(sum(all_window_scores) / len(all_window_scores), 1)
        slope = recent_window_scores[-1] - recent_window_scores[0]

        if slope <= -5:
            drift = "declining"
        elif slope >= 5:
            drift = "improving"
        else:
            drift = "stable"

        return {
            "drift": drift,
            "recent_avg": recent_avg,
            "overall_avg": overall_avg,
            "windows": len(windows),
        }

    def detect_director_bias(self, selections: list[dict]) -> dict[str, Any]:
        """
        전략별 점수 분포 분석 + 편향 경고 생성.

        Args:
            selections: director_selections 조회 결과

        Returns:
            {
                "strategy_stats": {
                    "balanced": {"avg_score": 75.0, "pass_rate": 0.85, "count": 20},
                    ...
                },
                "bias_warnings": ["전략 'X' 평균 81점 - 편향 가능성", ...],
            }
        """
        by_strategy: dict[str, list[dict]] = defaultdict(list)
        for rec in selections or []:
            strategy = rec.get("selected_strategy") or "unknown"
            by_strategy[str(strategy)].append(rec)

        strategy_stats: dict[str, dict[str, Any]] = {}
        warnings: list[str] = []

        for strategy, recs in by_strategy.items():
            scores = [float(r.get("score")) for r in recs if isinstance(r.get("score"), int | float)]
            passes = sum(
                1
                for r in recs
                if isinstance(r.get("score"), int | float) and str(r.get("verdict", "")).upper() == "PASS"
            )
            count = len(scores)
            avg_score = round(sum(scores) / count, 1) if count > 0 else 0.0

            strategy_stats[strategy] = {
                "avg_score": avg_score,
                "pass_rate": round(passes / count, 2) if count > 0 else 0.0,
                "count": count,
            }

            if len(scores) >= 10 and avg_score > 80:
                warnings.append(f"전략 '{strategy}' 평균 {avg_score:.0f}점 - 편향 가능성")
            if len(scores) >= 10 and avg_score < 40:
                warnings.append(f"전략 '{strategy}' 평균 {avg_score:.0f}점 - 과소평가 가능성")

        return {
            "strategy_stats": strategy_stats,
            "bias_warnings": warnings,
        }


# 싱글톤 인스턴스 (선택적 사용)
_dashboard_instance: QualityDashboard | None = None
_dashboard_lock = threading.Lock()


def get_dashboard(project_path: Path | None = None) -> QualityDashboard:
    """대시보드 싱글톤 인스턴스 반환"""
    global _dashboard_instance
    if _dashboard_instance is None:
        with _dashboard_lock:
            if _dashboard_instance is None:
                _dashboard_instance = QualityDashboard(project_path)
    return _dashboard_instance


def reset_dashboard() -> None:
    """대시보드 인스턴스 리셋"""
    global _dashboard_instance
    _dashboard_instance = None
