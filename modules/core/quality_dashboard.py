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
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Any


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

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path
        self.metrics_file = project_path / "logs" / "quality_metrics.jsonl" if project_path else None

        # 인메모리 메트릭
        self.validation_history: List[Dict] = []
        self.stage_stats: Dict[int, Dict] = defaultdict(lambda: {"pass": 0, "reject": 0, "scores": []})
        self.hud_anomalies: List[Dict] = []
        self.blueprint_coverage: List[Dict] = []

        # 파일에서 기존 메트릭 로드
        if self.metrics_file and self.metrics_file.exists():
            self._load_metrics()

    def _load_metrics(self):
        """파일에서 메트릭 로드"""
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        self._process_record(record)
        except Exception as e:
            print(f"[QualityDashboard] 메트릭 로드 실패: {e}")

    def _process_record(self, record: Dict):
        """레코드 처리 및 통계 업데이트"""
        record_type = record.get('type')

        if record_type == 'validation':
            self.validation_history.append(record)
            stage = record.get('stage', 4)
            decision = record.get('decision', 'UNKNOWN')
            score = record.get('score', 0)

            if decision == 'PASS':
                self.stage_stats[stage]['pass'] += 1
            else:
                self.stage_stats[stage]['reject'] += 1

            if score > 0:
                self.stage_stats[stage]['scores'].append(score)

        elif record_type == 'hud_anomaly':
            self.hud_anomalies.append(record)

        elif record_type == 'blueprint_coverage':
            self.blueprint_coverage.append(record)

    def record_validation(self, ep_num: int, result: Dict, stage: int = 4):
        """
        검증 결과 기록

        Args:
            ep_num: 에피소드 번호
            result: 검증 결과 (decision, score, violations 등)
            stage: 스테이지 번호 (2, 3, 4)
        """
        record = {
            'type': 'validation',
            'timestamp': datetime.now().isoformat(),
            'ep_num': ep_num,
            'stage': stage,
            'decision': result.get('decision', 'UNKNOWN'),
            'score': result.get('score', 0),
            'violations': [v.get('type') for v in result.get('violations', [])],
            'warnings': len(result.get('warnings', []))
        }

        self._process_record(record)
        self._save_record(record)

        return record

    def record_hud_anomaly(self, ep_num: int, anomalies: List[Dict]):
        """
        HUD 급변 감지 기록

        Args:
            ep_num: 에피소드 번호
            anomalies: 감지된 급변 목록
        """
        record = {
            'type': 'hud_anomaly',
            'timestamp': datetime.now().isoformat(),
            'ep_num': ep_num,
            'count': len(anomalies),
            'types': [a.get('type') for a in anomalies],
            'severities': [a.get('severity', 'medium') for a in anomalies]
        }

        self.hud_anomalies.append(record)
        self._save_record(record)

        return record

    def record_blueprint_coverage(self, ep_num: int, coverage_result: Dict):
        """
        Blueprint 커버리지 기록

        Args:
            ep_num: 에피소드 번호
            coverage_result: _validate_blueprint_completeness_v60() 결과
        """
        record = {
            'type': 'blueprint_coverage',
            'timestamp': datetime.now().isoformat(),
            'ep_num': ep_num,
            'coverage': coverage_result.get('scene_coverage', 0),
            'expected': coverage_result.get('expected_scenes', 0),
            'reflected': coverage_result.get('reflected_scenes', 0),
            'valid': coverage_result.get('valid', True)
        }

        self.blueprint_coverage.append(record)
        self._save_record(record)

        return record

    def _save_record(self, record: Dict):
        """레코드를 파일에 저장"""
        if not self.metrics_file:
            return

        try:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"[QualityDashboard] 레코드 저장 실패: {e}")

    def get_summary(self) -> Dict:
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
            'total_validations': len(self.validation_history),
            'stage_stats': {},
            'hud_anomaly_rate': 0,
            'avg_blueprint_coverage': 0,
            'common_violations': []
        }

        # Stage별 통계
        for stage, stats in self.stage_stats.items():
            total = stats['pass'] + stats['reject']
            if total > 0:
                pass_rate = stats['pass'] / total * 100
                avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
                summary['stage_stats'][stage] = {
                    'pass_rate': round(pass_rate, 1),
                    'avg_score': round(avg_score, 1),
                    'total': total
                }

        # HUD 급변 비율
        if self.validation_history:
            anomaly_eps = set(a.get('ep_num') for a in self.hud_anomalies)
            summary['hud_anomaly_rate'] = round(
                len(anomaly_eps) / len(self.validation_history) * 100, 1
            )

        # 평균 Blueprint 커버리지
        if self.blueprint_coverage:
            coverages = [c.get('coverage', 0) for c in self.blueprint_coverage]
            summary['avg_blueprint_coverage'] = round(sum(coverages) / len(coverages), 1)

        # 빈번한 위반 유형
        violation_counts = defaultdict(int)
        for record in self.validation_history:
            for v in record.get('violations', []):
                violation_counts[v] += 1

        summary['common_violations'] = sorted(
            violation_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return summary

    def get_episode_trend(self, n_episodes: int = 20) -> List[Dict]:
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
            ep_num = record.get('ep_num')

            # Blueprint 커버리지 찾기
            coverage = None
            for c in self.blueprint_coverage:
                if c.get('ep_num') == ep_num:
                    coverage = c.get('coverage')
                    break

            trend.append({
                'ep_num': ep_num,
                'score': record.get('score', 0),
                'decision': record.get('decision', 'UNKNOWN'),
                'coverage': coverage,
                'violations': len(record.get('violations', []))
            })

        return trend

    def get_failure_patterns(self) -> Dict:
        """
        실패 패턴 분석

        Returns:
            {
                'by_stage': {2: [...], 3: [...], 4: [...]},
                'by_type': {'item': 5, 'continuity': 3, ...},
                'by_episode_range': {'1-10': 3, '11-20': 5, ...}
            }
        """
        patterns = {
            'by_stage': defaultdict(list),
            'by_type': defaultdict(int),
            'by_episode_range': defaultdict(int)
        }

        for record in self.validation_history:
            if record.get('decision') == 'REJECT':
                stage = record.get('stage', 4)
                ep_num = record.get('ep_num', 0)

                patterns['by_stage'][stage].append({
                    'ep_num': ep_num,
                    'violations': record.get('violations', [])
                })

                for v in record.get('violations', []):
                    patterns['by_type'][v] += 1

                # 에피소드 범위별 집계
                range_key = f"{(ep_num - 1) // 10 * 10 + 1}-{(ep_num - 1) // 10 * 10 + 10}"
                patterns['by_episode_range'][range_key] += 1

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
            r for r in self.validation_history[-50:]  # 최근 50개 중
            if r.get('decision') == 'REJECT' and r.get('stage') == stage
        ][-recent_n:]  # 마지막 N개

        if len(recent_rejects) < 2:
            return ""

        # REJECT 사유 카운트
        reason_counts = defaultdict(int)
        reason_keywords = {
            '분량': ['분량', '자', 'length', '짧'],
            '서사 폭주': ['폭주', '압축', '빠르'],
            '서사 정체': ['정체', '반복', '지루'],
            '씬 미반영': ['씬', 'scene', '장면', '누락'],
            '설정 오류': ['설정', '무공', '오류', '모순'],
            '밀도 불균형': ['밀도', '균형', '요약'],
        }

        for record in recent_rejects:
            violations = record.get('violations', [])
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
        lines = [
            "[⚠️ V60.5 빈번 REJECT 사유 경고]",
            f"최근 {len(recent_rejects)}회 REJECT 중 반복되는 패턴:",
            ""
        ]

        for reason, count in frequent[:3]:  # 상위 3개
            lines.append(f"  🔴 {reason}: {count}회 발생")

            # 사유별 구체적 조언
            if reason == '분량':
                lines.append("     → 4,500자 이상 확보. 심리 묘사, 조연 리액션 추가.")
            elif reason == '서사 폭주':
                lines.append("     → 사건을 더 잘게 쪼개라. 과정을 상세히 묘사.")
            elif reason == '서사 정체':
                lines.append("     → 반복 대신 인과적 전진. 새로운 정보/사건 추가.")
            elif reason == '씬 미반영':
                lines.append("     → Blueprint 6개 씬 모두 반영. 특히 후반부 씬 주의.")
            elif reason == '설정 오류':
                lines.append("     → 직전 화 확인. 미습득 무공/장비 사용 금지.")
            elif reason == '밀도 불균형':
                lines.append("     → 앞뒤 분량 균등. 후반부 요약 금지.")

        lines.append("")
        lines.append("⚠️ 위 패턴은 반복 REJECT의 주요 원인입니다. 특히 주의하세요.")

        return "\n".join(lines)

    def print_console_summary(self):
        """콘솔에 요약 출력"""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print(" [V60] Quality Dashboard Summary")
        print("=" * 60)

        print(f"\n📊 총 검증 횟수: {summary['total_validations']}")

        print("\n📈 Stage별 통계:")
        for stage, stats in sorted(summary['stage_stats'].items()):
            print(f"   Stage {stage}: PASS {stats['pass_rate']}% | 평균 점수 {stats['avg_score']} | 총 {stats['total']}회")

        print(f"\n⚠️ HUD 급변 비율: {summary['hud_anomaly_rate']}%")
        print(f"📋 평균 Blueprint 커버리지: {summary['avg_blueprint_coverage']}%")

        if summary['common_violations']:
            print("\n❌ 빈번한 위반 유형:")
            for violation, count in summary['common_violations']:
                print(f"   - {violation}: {count}회")

        print("\n" + "=" * 60)

    def export_for_streamlit(self) -> Dict:
        """
        Streamlit 대시보드용 데이터 내보내기

        Returns:
            Streamlit 차트용 데이터 구조
        """
        return {
            'summary': self.get_summary(),
            'trend': self.get_episode_trend(50),
            'patterns': self.get_failure_patterns(),
            'hud_history': self.hud_anomalies[-50:],
            'coverage_history': self.blueprint_coverage[-50:]
        }

    def analyze_score_trend(self, stage: int = 4, window: int = 5) -> Dict:
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
        stage_records = [
            r for r in self.validation_history
            if r.get('stage') == stage and r.get('score', 0) > 0
        ]

        if len(stage_records) < 3:
            return {
                'trend': 'insufficient_data',
                'recent_avg': 0,
                'overall_avg': 0,
                'feedback': '충분한 데이터가 없습니다.',
                'alert_level': 'info'
            }

        # 전체 평균
        all_scores = [r.get('score', 0) for r in stage_records]
        overall_avg = sum(all_scores) / len(all_scores)

        # 최근 평균
        recent_records = stage_records[-window:]
        recent_scores = [r.get('score', 0) for r in recent_records]
        recent_avg = sum(recent_scores) / len(recent_scores)

        # 추이 분석
        if len(stage_records) >= window * 2:
            older_records = stage_records[-(window * 2):-window]
            older_scores = [r.get('score', 0) for r in older_records]
            older_avg = sum(older_scores) / len(older_scores)

            diff = recent_avg - older_avg
            if diff >= 10:
                trend = 'improving'
            elif diff <= -10:
                trend = 'declining'
            else:
                # 변동성 체크
                variance = sum((s - recent_avg) ** 2 for s in recent_scores) / len(recent_scores)
                if variance > 100:  # 표준편차 10점 이상
                    trend = 'fluctuating'
                else:
                    trend = 'stable'
        else:
            trend = 'stable'

        # 피드백 생성
        feedback_map = {
            'improving': f"✅ 점수가 상승 추세입니다! (최근 평균: {recent_avg:.1f}점)",
            'declining': f"⚠️ 점수가 하락 추세입니다. (최근 평균: {recent_avg:.1f}점, 전체 평균: {overall_avg:.1f}점)",
            'stable': f"➡️ 점수가 안정적입니다. (평균: {recent_avg:.1f}점)",
            'fluctuating': f"🎢 점수가 불안정합니다. 일관성 있는 품질 유지가 필요합니다."
        }

        alert_map = {
            'improving': 'success',
            'declining': 'danger' if recent_avg < 60 else 'warning',
            'stable': 'success' if recent_avg >= 70 else 'warning',
            'fluctuating': 'warning'
        }

        return {
            'trend': trend,
            'recent_avg': round(recent_avg, 1),
            'overall_avg': round(overall_avg, 1),
            'feedback': feedback_map.get(trend, ''),
            'alert_level': alert_map.get(trend, 'info')
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

        if analysis['trend'] == 'insufficient_data':
            return ""

        lines = [f"[V60.4 품질 추이 분석 - Stage {stage}]"]
        lines.append(analysis['feedback'])

        # 추가 가이드
        if analysis['trend'] == 'declining':
            lines.append("\n🔧 개선 제안:")
            lines.append("- 최근 REJECT 사유를 확인하고 반복 오류를 피하라")
            lines.append("- 분량, 밀도, 씬 균등성을 다시 점검하라")
            if stage == 4:
                lines.append("- 대화와 묘사의 균형을 맞춰라")

        elif analysis['trend'] == 'fluctuating':
            lines.append("\n🔧 안정화 제안:")
            lines.append("- 성공한 에피소드의 패턴을 참고하라")
            lines.append("- 무리한 실험보다 안정적인 구조를 우선하라")

        elif analysis['trend'] == 'improving':
            lines.append("\n✨ 현재 패턴을 유지하라. 성공 요인:")
            if analysis['recent_avg'] >= 80:
                lines.append("- 품질이 우수합니다. 이 방향을 계속 유지하세요.")

        return "\n".join(lines)

    def predict_pass_probability(
        self,
        stage: int = 4,
        current_metrics: Optional[Dict] = None
    ) -> Dict:
        """
        [V60.5] PASS 확률 예측

        과거 데이터 기반으로 현재 원고의 PASS 확률을 예측.
        Pre-Director Checklist 결과, 분량, 다이얼로그 비율 등을 고려.

        Args:
            stage: Stage 번호
            current_metrics: 현재 원고의 메트릭 (선택)
                - length: 원고 길이
                - dialogue_ratio: 대화 비율
                - scene_coverage: 씬 반영률
                - pre_checklist_warnings: Pre-Director 경고 수
                - pre_checklist_fails: Pre-Director 실패 수

        Returns:
            {
                'probability': float (0-100),
                'confidence': 'high' | 'medium' | 'low',
                'factors': [{'name': str, 'impact': str, 'weight': float}, ...],
                'recommendation': str,
                'alert_level': 'success' | 'warning' | 'danger'
            }
        """
        result = {
            'probability': 50.0,  # 기본값
            'confidence': 'low',
            'factors': [],
            'recommendation': '',
            'alert_level': 'warning'
        }

        # 1. 기본 확률 계산 (과거 PASS율 기반)
        stage_stat = self.stage_stats.get(stage, {'pass': 0, 'reject': 0})
        total = stage_stat['pass'] + stage_stat['reject']

        if total < 5:
            result['confidence'] = 'low'
            result['recommendation'] = "데이터 부족으로 예측 신뢰도가 낮습니다."
            return result

        base_rate = (stage_stat['pass'] / total) * 100
        probability = base_rate

        # 신뢰도 결정
        if total >= 20:
            result['confidence'] = 'high'
        elif total >= 10:
            result['confidence'] = 'medium'
        else:
            result['confidence'] = 'low'

        # 2. 현재 메트릭 기반 조정
        if current_metrics:
            # 분량 조정
            length = current_metrics.get('length', 0)
            if length > 0:
                if length < 4000:
                    probability -= 40  # 최소 미달 시 대폭 감점
                    result['factors'].append({
                        'name': '분량 부족',
                        'impact': f'{length}자 (최소 4000자)',
                        'weight': -40
                    })
                elif length < 4500:
                    probability -= 15
                    result['factors'].append({
                        'name': '분량 경계',
                        'impact': f'{length}자',
                        'weight': -15
                    })
                elif 4500 <= length <= 8000:
                    probability += 5
                    result['factors'].append({
                        'name': '분량 적정',
                        'impact': f'{length}자',
                        'weight': +5
                    })

            # 대화 비율 조정
            dialogue_ratio = current_metrics.get('dialogue_ratio', -1)
            if dialogue_ratio >= 0:
                if dialogue_ratio < 0.15:
                    probability -= 20
                    result['factors'].append({
                        'name': '대화 부족',
                        'impact': f'{dialogue_ratio:.0%}',
                        'weight': -20
                    })
                elif 0.25 <= dialogue_ratio <= 0.40:
                    probability += 5
                    result['factors'].append({
                        'name': '대화 비율 양호',
                        'impact': f'{dialogue_ratio:.0%}',
                        'weight': +5
                    })

            # 씬 반영률 조정
            scene_coverage = current_metrics.get('scene_coverage', -1)
            if scene_coverage >= 0:
                if scene_coverage < 0.3:
                    probability -= 30
                    result['factors'].append({
                        'name': '씬 반영 부족',
                        'impact': f'{scene_coverage:.0%}',
                        'weight': -30
                    })
                elif scene_coverage < 0.5:
                    probability -= 10
                    result['factors'].append({
                        'name': '씬 반영 경계',
                        'impact': f'{scene_coverage:.0%}',
                        'weight': -10
                    })
                elif scene_coverage >= 0.7:
                    probability += 10
                    result['factors'].append({
                        'name': '씬 반영 우수',
                        'impact': f'{scene_coverage:.0%}',
                        'weight': +10
                    })

            # Pre-Director Checklist 결과 반영
            pre_fails = current_metrics.get('pre_checklist_fails', 0)
            pre_warnings = current_metrics.get('pre_checklist_warnings', 0)

            if pre_fails > 0:
                probability -= pre_fails * 25  # 실패당 25점 감점
                result['factors'].append({
                    'name': 'Pre-Check 실패',
                    'impact': f'{pre_fails}개 항목',
                    'weight': -pre_fails * 25
                })
            elif pre_warnings > 2:
                probability -= (pre_warnings - 2) * 5  # 2개 초과 경고당 5점 감점
                result['factors'].append({
                    'name': 'Pre-Check 경고',
                    'impact': f'{pre_warnings}개 항목',
                    'weight': -(pre_warnings - 2) * 5
                })

        # 3. 추이 기반 조정
        trend_analysis = self.analyze_score_trend(stage=stage)
        if trend_analysis['trend'] == 'declining':
            probability -= 10
            result['factors'].append({
                'name': '하락 추세',
                'impact': '최근 점수 하락',
                'weight': -10
            })
        elif trend_analysis['trend'] == 'improving':
            probability += 5
            result['factors'].append({
                'name': '상승 추세',
                'impact': '최근 점수 상승',
                'weight': +5
            })

        # 4. 확률 범위 제한
        probability = max(5, min(95, probability))
        result['probability'] = round(probability, 1)

        # 5. Alert level 결정
        if probability >= 70:
            result['alert_level'] = 'success'
        elif probability >= 40:
            result['alert_level'] = 'warning'
        else:
            result['alert_level'] = 'danger'

        # 6. 추천 생성
        if probability < 40:
            critical_factors = [f for f in result['factors'] if f.get('weight', 0) <= -20]
            if critical_factors:
                factor_names = [f['name'] for f in critical_factors[:2]]
                result['recommendation'] = f"PASS 확률 낮음. 우선 개선 필요: {', '.join(factor_names)}"
            else:
                result['recommendation'] = "PASS 확률 낮음. 전반적인 품질 개선이 필요합니다."
        elif probability < 60:
            result['recommendation'] = "PASS 확률 보통. 경고 항목 해소 시 확률 상승 가능."
        else:
            result['recommendation'] = "PASS 확률 양호. 현재 품질 유지하세요."

        return result

    def get_pass_prediction_warning(
        self,
        stage: int = 4,
        current_metrics: Optional[Dict] = None
    ) -> str:
        """
        [V60.5] Writer 프롬프트에 주입할 PASS 확률 예측 경고

        Args:
            stage: Stage 번호
            current_metrics: 현재 원고 메트릭

        Returns:
            프롬프트 주입용 경고 문자열 (확률 60% 미만일 때만)
        """
        prediction = self.predict_pass_probability(stage=stage, current_metrics=current_metrics)

        # 확률이 60% 이상이면 경고 불필요
        if prediction['probability'] >= 60:
            return ""

        lines = [
            f"[⚠️ V60.5 PASS 확률 예측 경고]",
            f"현재 예측 PASS 확률: {prediction['probability']:.0f}% ({prediction['confidence']} 신뢰도)",
            ""
        ]

        # 부정적 요인 나열
        negative_factors = [f for f in prediction['factors'] if f.get('weight', 0) < 0]
        if negative_factors:
            lines.append("📉 PASS 확률 저하 요인:")
            for factor in negative_factors[:4]:
                lines.append(f"  - {factor['name']}: {factor['impact']} (영향: {factor['weight']:+d}점)")

        lines.append("")
        lines.append(f"💡 {prediction['recommendation']}")

        # 구체적 조언 추가
        if prediction['probability'] < 40:
            lines.append("")
            lines.append("🚨 현재 상태로는 REJECT 가능성 높음. 다음을 반드시 확인하라:")
            lines.append("  1. 분량이 4,500자 이상인가?")
            lines.append("  2. Blueprint 6개 씬을 모두 반영했는가?")
            lines.append("  3. 대화와 묘사가 균형 잡혀 있는가?")

        return "\n".join(lines)


# 싱글톤 인스턴스 (선택적 사용)
_dashboard_instance: Optional[QualityDashboard] = None


def get_dashboard(project_path: Optional[Path] = None) -> QualityDashboard:
    """대시보드 싱글톤 인스턴스 반환"""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = QualityDashboard(project_path)
    return _dashboard_instance


def reset_dashboard():
    """대시보드 인스턴스 리셋"""
    global _dashboard_instance
    _dashboard_instance = None
