"""
[V58] Pacing Controller

전개 속도 및 리듬 제어 시스템:
- 씬당 분량 균형
- 연속 씬 유형 경고 (액션만 연속, 대화만 연속)
- 시간 압축/확장 균형
- 긴장도 곡선 분석
- 카타르시스 타이밍 연동

기존 catharsis_timer.py 고도화
LLM 비용: 0원 (순수 Python 기반)
"""

import re
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import math


class PacingController:
    """
    [V58] 전개 속도 제어기

    검증 항목:
    1. 씬 분량 균형 - 씬별 길이 편차 (CV)
    2. 씬 유형 연속성 - 동일 유형 연속 감지
    3. 시간 흐름 균형 - 시간 압축/확장 적정성
    4. 긴장도 곡선 - 전개 리듬 분석
    5. 전환 빈도 - 장면 전환 적정성
    """

    # 씬 유형 분류 패턴
    SCENE_TYPE_PATTERNS = {
        'action': [
            r'검.*휘둘', r'공격.*받', r'피.*튀',
            r'싸움', r'전투', r'대결', r'비무',
            r'스킬.*발동', r'마나.*폭발', r'던전',
        ],
        'dialogue': [
            r'"[^"]{20,}"', r'대화.*나누', r'말.*건네',
            r'물었다', r'대답했다', r'설명했다',
        ],
        'inner': [
            r'생각했다', r'떠올렸다', r'회상',
            r'마음.*속', r'내심', r'혼자.*중얼',
        ],
        'description': [
            r'풍경', r'건물', r'분위기',
            r'햇살', r'바람', r'하늘',
        ],
        'transition': [
            r'시간.*흘러', r'며칠.*후', r'다음.*날',
            r'장소.*옮', r'이동.*하',
        ],
    }

    # 시간 표현 패턴
    TIME_EXPRESSIONS = {
        'instant': [r'순간', r'찰나', r'눈.*깜빡'],
        'seconds': [r'\d+초', r'몇 초'],
        'minutes': [r'\d+분', r'잠시', r'잠깐'],
        'hours': [r'\d+시간', r'몇 시간', r'한나절'],
        'days': [r'\d+일', r'며칠', r'하루', r'이틀'],
        'weeks': [r'\d+주', r'몇 주'],
        'months': [r'\d+개월', r'몇 달'],
        'years': [r'\d+년', r'몇 년'],
    }

    # 긴장도 키워드
    TENSION_KEYWORDS = {
        'high': [
            r'위기', r'절체절명', r'급박', r'긴급',
            r'죽음', r'살인', r'배신', r'폭발',
            r'분노', r'절규', r'공포', r'경악',
        ],
        'medium': [
            r'갈등', r'대립', r'의심', r'불안',
            r'긴장', r'경계', r'추적', r'탐색',
        ],
        'low': [
            r'평화', r'휴식', r'일상', r'여유',
            r'미소', r'웃음', r'안도', r'평온',
        ],
    }

    def __init__(self, genre: str = "wuxia"):
        """
        Args:
            genre: 장르 (wuxia/hunter/investment)
        """
        self.genre = genre

        # 장르별 권장 설정
        self.genre_settings = {
            'wuxia': {
                'scene_length_cv_range': (0.2, 0.5),  # 씬 길이 변동계수
                'max_consecutive_same_type': 3,       # 동일 유형 연속 최대
                'tension_pattern': 'rising_falling',   # 상승-하강 패턴
                'recommended_scene_count': (5, 7),     # 권장 씬 수
            },
            'hunter': {
                'scene_length_cv_range': (0.25, 0.55),
                'max_consecutive_same_type': 3,
                'tension_pattern': 'episodic',         # 에피소드형
                'recommended_scene_count': (5, 8),
            },
            'investment': {
                'scene_length_cv_range': (0.2, 0.45),
                'max_consecutive_same_type': 4,        # 대화가 많으므로 완화
                'tension_pattern': 'building',         # 축적형
                'recommended_scene_count': (4, 6),
            },
        }

    def analyze(self, manuscript: str, blueprint: Dict = None) -> Dict[str, Any]:
        """
        전개 속도 종합 분석

        Args:
            manuscript: 원고 텍스트
            blueprint: 블루프린트 (씬 정보 포함 시 더 정확)

        Returns:
            {
                "score": float,
                "issues": [...],
                "metrics": {...},
                "recommendations": [...]
            }
        """
        issues = []
        metrics = {}
        recommendations = []

        # 1. 씬 분리 (블루프린트 또는 자동 분리)
        scenes = self._split_into_scenes(manuscript, blueprint)
        metrics['scene_count'] = len(scenes)

        # 2. 씬 분량 균형 분석
        length_result = self._analyze_scene_lengths(scenes)
        metrics['scene_length_cv'] = length_result['cv']
        metrics['avg_scene_length'] = length_result['avg']
        if length_result['issues']:
            issues.extend(length_result['issues'])
        if length_result['recommendations']:
            recommendations.extend(length_result['recommendations'])

        # 3. 씬 유형 분석
        type_result = self._analyze_scene_types(scenes)
        metrics['scene_types'] = type_result['type_counts']
        metrics['dominant_type'] = type_result['dominant']
        if type_result['issues']:
            issues.extend(type_result['issues'])

        # 4. 시간 흐름 분석
        time_result = self._analyze_time_flow(manuscript)
        metrics['time_span'] = time_result['estimated_span']
        metrics['time_compression'] = time_result['compression_level']
        if time_result['issues']:
            issues.extend(time_result['issues'])

        # 5. 긴장도 곡선 분석
        tension_result = self._analyze_tension_curve(scenes)
        metrics['tension_curve'] = tension_result['curve']
        metrics['tension_pattern'] = tension_result['pattern']
        if tension_result['issues']:
            issues.extend(tension_result['issues'])

        # 6. 전환 빈도 분석
        transition_result = self._analyze_transitions(manuscript)
        metrics['transition_count'] = transition_result['count']
        if transition_result['issues']:
            issues.extend(transition_result['issues'])

        # 점수 계산
        score = self._calculate_score(issues, metrics)

        return {
            "score": score,
            "passed": score >= 70,
            "issues": issues,
            "metrics": metrics,
            "recommendations": recommendations,
            "summary": self._generate_summary(metrics, issues)
        }

    def _split_into_scenes(self, text: str, blueprint: Dict = None) -> List[Dict]:
        """텍스트를 씬으로 분리"""
        scenes = []

        if blueprint and 'scene_breakdown' in blueprint:
            # 블루프린트 기반 분리 (정확함)
            scene_breakdown = blueprint['scene_breakdown']
            scene_count = len(scene_breakdown)

            # 텍스트를 대략적으로 분할
            avg_length = len(text) // max(1, scene_count)
            for i in range(scene_count):
                start = i * avg_length
                end = (i + 1) * avg_length if i < scene_count - 1 else len(text)
                scenes.append({
                    'index': i + 1,
                    'text': text[start:end],
                    'length': end - start
                })
        else:
            # 자동 분리 (구분자 기반)
            # 빈 줄 2개 이상, 또는 특정 패턴으로 분리
            split_patterns = [
                r'\n\s*\n\s*\n',      # 빈 줄 2개
                r'\n\s*[#\*]{3,}\s*\n',  # 구분선
                r'\n\s*◇\s*\n',        # 다이아몬드 구분
            ]

            combined_pattern = '|'.join(split_patterns)
            parts = re.split(combined_pattern, text)

            for i, part in enumerate(parts):
                if len(part.strip()) > 100:  # 최소 길이
                    scenes.append({
                        'index': i + 1,
                        'text': part.strip(),
                        'length': len(part.strip())
                    })

        # 씬이 너무 적으면 균등 분할
        if len(scenes) < 3:
            chunk_size = len(text) // 5
            scenes = []
            for i in range(5):
                start = i * chunk_size
                end = (i + 1) * chunk_size if i < 4 else len(text)
                scenes.append({
                    'index': i + 1,
                    'text': text[start:end],
                    'length': end - start
                })

        return scenes

    def _analyze_scene_lengths(self, scenes: List[Dict]) -> Dict:
        """씬 분량 균형 분석"""
        result = {'cv': 0, 'avg': 0, 'issues': [], 'recommendations': []}

        if not scenes:
            return result

        lengths = [s['length'] for s in scenes]
        avg = sum(lengths) / len(lengths)
        result['avg'] = avg

        # 변동계수 (CV) 계산
        if avg > 0:
            variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
            std = math.sqrt(variance)
            cv = std / avg
            result['cv'] = cv

            settings = self.genre_settings.get(self.genre, self.genre_settings['wuxia'])
            min_cv, max_cv = settings['scene_length_cv_range']

            if cv < min_cv:
                result['issues'].append({
                    'type': 'uniform_scenes',
                    'severity': 'WARNING',
                    'message': f"씬 길이가 너무 균일함 (CV={cv:.2f} < {min_cv})",
                    'suggestion': "중요 씬은 길게, 전환 씬은 짧게 조절"
                })
                result['recommendations'].append("핵심 씬은 분량을 늘려 밀도감 부여")
            elif cv > max_cv:
                result['issues'].append({
                    'type': 'unbalanced_scenes',
                    'severity': 'WARNING',
                    'message': f"씬 길이 편차 과다 (CV={cv:.2f} > {max_cv})",
                    'suggestion': "극단적으로 짧거나 긴 씬 조절"
                })

        # 극단적 씬 감지
        for scene in scenes:
            if scene['length'] < avg * 0.3:
                result['issues'].append({
                    'type': 'too_short_scene',
                    'severity': 'WARNING',
                    'message': f"씬 {scene['index']} 과도하게 짧음 ({scene['length']}자, 평균의 30% 미만)"
                })
            elif scene['length'] > avg * 2.5:
                result['issues'].append({
                    'type': 'too_long_scene',
                    'severity': 'WARNING',
                    'message': f"씬 {scene['index']} 과도하게 김 ({scene['length']}자, 평균의 2.5배 초과)"
                })

        return result

    def _analyze_scene_types(self, scenes: List[Dict]) -> Dict:
        """씬 유형 분석"""
        result = {
            'type_counts': defaultdict(int),
            'dominant': 'unknown',
            'sequence': [],
            'issues': []
        }

        for scene in scenes:
            scene_type = self._classify_scene_type(scene['text'])
            result['type_counts'][scene_type] += 1
            result['sequence'].append(scene_type)
            scene['type'] = scene_type

        # 우세 유형
        if result['type_counts']:
            result['dominant'] = max(result['type_counts'], key=result['type_counts'].get)

        # 연속 동일 유형 감지
        settings = self.genre_settings.get(self.genre, self.genre_settings['wuxia'])
        max_consecutive = settings['max_consecutive_same_type']

        consecutive = 1
        prev_type = None
        for scene_type in result['sequence']:
            if scene_type == prev_type:
                consecutive += 1
                if consecutive > max_consecutive:
                    result['issues'].append({
                        'type': 'consecutive_same_type',
                        'severity': 'WARNING',
                        'message': f"'{scene_type}' 씬 {consecutive}개 연속 (최대 권장: {max_consecutive})",
                        'suggestion': f"중간에 다른 유형 씬 삽입 권장"
                    })
                    break
            else:
                consecutive = 1
            prev_type = scene_type

        # 유형 다양성
        unique_types = len([k for k, v in result['type_counts'].items() if v > 0])
        if unique_types < 3:
            result['issues'].append({
                'type': 'low_type_diversity',
                'severity': 'WARNING',
                'message': f"씬 유형 다양성 부족 ({unique_types}종류만 사용)",
                'suggestion': "액션, 대화, 내면, 전환 등 다양한 씬 유형 활용"
            })

        return result

    def _classify_scene_type(self, text: str) -> str:
        """씬 유형 분류"""
        scores = {}

        for scene_type, patterns in self.SCENE_TYPE_PATTERNS.items():
            count = 0
            for pattern in patterns:
                count += len(re.findall(pattern, text, re.IGNORECASE))
            scores[scene_type] = count

        if not scores or max(scores.values()) == 0:
            return 'mixed'

        return max(scores, key=scores.get)

    def _analyze_time_flow(self, text: str) -> Dict:
        """시간 흐름 분석"""
        result = {
            'estimated_span': 'unknown',
            'compression_level': 'normal',
            'time_markers': [],
            'issues': []
        }

        # 시간 표현 수집
        for time_unit, patterns in self.TIME_EXPRESSIONS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    result['time_markers'].extend([(m, time_unit) for m in matches])

        # 시간 범위 추정
        if result['time_markers']:
            units_found = set(m[1] for m in result['time_markers'])

            if 'years' in units_found or 'months' in units_found:
                result['estimated_span'] = 'long'
                result['compression_level'] = 'high'
            elif 'weeks' in units_found or 'days' in units_found:
                result['estimated_span'] = 'medium'
                result['compression_level'] = 'medium'
            elif 'hours' in units_found:
                result['estimated_span'] = 'short'
                result['compression_level'] = 'low'
            else:
                result['estimated_span'] = 'instant'
                result['compression_level'] = 'none'

        # 시간 점프 경고
        long_jumps = sum(1 for m in result['time_markers'] if m[1] in ['months', 'years'])
        if long_jumps >= 2:
            result['issues'].append({
                'type': 'multiple_time_jumps',
                'severity': 'WARNING',
                'message': f"큰 시간 점프 {long_jumps}회 (개월/년 단위)",
                'suggestion': "한 화 내 시간 점프는 최소화"
            })

        return result

    def _analyze_tension_curve(self, scenes: List[Dict]) -> Dict:
        """긴장도 곡선 분석"""
        result = {
            'curve': [],
            'pattern': 'unknown',
            'issues': []
        }

        for scene in scenes:
            tension = self._calculate_scene_tension(scene['text'])
            result['curve'].append(tension)
            scene['tension'] = tension

        if not result['curve']:
            return result

        # 패턴 분석
        if len(result['curve']) >= 3:
            # 상승 추세
            rising = all(result['curve'][i] <= result['curve'][i+1]
                        for i in range(len(result['curve'])-1))
            # 하강 추세
            falling = all(result['curve'][i] >= result['curve'][i+1]
                         for i in range(len(result['curve'])-1))
            # 정점 존재
            peak_idx = result['curve'].index(max(result['curve']))
            has_peak = 0 < peak_idx < len(result['curve']) - 1

            if rising:
                result['pattern'] = 'rising'
            elif falling:
                result['pattern'] = 'falling'
                result['issues'].append({
                    'type': 'falling_tension',
                    'severity': 'WARNING',
                    'message': "긴장도가 계속 하락하는 전개",
                    'suggestion': "후반부에 새로운 위기/갈등 추가"
                })
            elif has_peak:
                result['pattern'] = 'peaked'
            else:
                result['pattern'] = 'flat'
                if max(result['curve']) - min(result['curve']) < 0.2:
                    result['issues'].append({
                        'type': 'flat_tension',
                        'severity': 'WARNING',
                        'message': "긴장도 변화 부족 (평탄한 전개)",
                        'suggestion': "긴장-이완의 리듬감 부여"
                    })

        return result

    def _calculate_scene_tension(self, text: str) -> float:
        """씬 긴장도 계산 (0-1)"""
        scores = {'high': 0, 'medium': 0, 'low': 0}

        for level, patterns in self.TENSION_KEYWORDS.items():
            for pattern in patterns:
                count = len(re.findall(pattern, text))
                scores[level] += count

        total = sum(scores.values())
        if total == 0:
            return 0.5  # 기본값

        # 가중 평균
        weighted = scores['high'] * 1.0 + scores['medium'] * 0.5 + scores['low'] * 0.0
        return min(1.0, weighted / total)

    def _analyze_transitions(self, text: str) -> Dict:
        """장면 전환 분석"""
        result = {'count': 0, 'issues': []}

        # 전환 표현
        transition_patterns = [
            r'한편', r'그\s*무렵', r'같은\s*시각',
            r'장소를\s*옮', r'다른\s*곳에서는',
            r'시간이\s*흘러', r'며칠\s*후',
        ]

        for pattern in transition_patterns:
            count = len(re.findall(pattern, text))
            result['count'] += count

        # 과다 전환 경고
        text_length = len(text)
        if text_length > 0:
            transition_density = result['count'] / (text_length / 1000)
            if transition_density > 3:  # 1000자당 3회 이상
                result['issues'].append({
                    'type': 'frequent_transitions',
                    'severity': 'WARNING',
                    'message': f"장면 전환 과다 ({result['count']}회, 밀도 {transition_density:.1f}/1000자)",
                    'suggestion': "하나의 장면을 더 깊이 있게 전개"
                })

        return result

    def _calculate_score(self, issues: List, metrics: Dict) -> float:
        """점수 계산"""
        score = 100.0

        for issue in issues:
            severity = issue.get('severity', 'WARNING')
            if severity == 'CRITICAL':
                score -= 15
            elif severity == 'WARNING':
                score -= 5

        return max(0, min(100, score))

    def _generate_summary(self, metrics: Dict, issues: List) -> str:
        """요약 생성"""
        parts = [f"[V58 Pacing Analysis]"]
        parts.append(f"  씬 수: {metrics.get('scene_count', 0)}")
        parts.append(f"  길이 CV: {metrics.get('scene_length_cv', 0):.2f}")
        parts.append(f"  우세 유형: {metrics.get('dominant_type', 'unknown')}")
        parts.append(f"  긴장 패턴: {metrics.get('tension_pattern', 'unknown')}")
        parts.append(f"  이슈: {len(issues)}건")
        return "\n".join(parts)


def create_pacing_controller(genre: str = "wuxia") -> PacingController:
    """PacingController 인스턴스 생성 헬퍼"""
    return PacingController(genre=genre)
