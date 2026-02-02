"""
[V58] POV (Point of View) Consistency Validator

시점 일관성 검증 시스템:
- 1인칭/3인칭 혼용 감지
- 전지적 시점 누수 감지 (모르는 정보 언급)
- 주인공 인지 범위 검증
- 시점 전환 적절성

LLM 비용: 0원 (순수 Python 기반)
"""

import re
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict


class POVValidator:
    """
    [V58] 시점 일관성 검증기

    검증 항목:
    1. 인칭 혼용 - 1인칭("나는")과 3인칭("그는") 혼용 감지
    2. 전지적 시점 누수 - 주인공이 알 수 없는 정보 언급
    3. 인지 범위 초과 - 주인공 시야/청각 밖 사건 묘사
    4. 내면 서술 위반 - 타인의 내면을 직접 서술
    5. 시제 일관성 - 과거/현재 시제 혼용
    """

    # 1인칭 지시어
    FIRST_PERSON_MARKERS = [
        r'\b나는\b', r'\b나의\b', r'\b내가\b', r'\b내\b',
        r'\b나를\b', r'\b나에게\b', r'\b내게\b',
        r'\b우리는\b', r'\b우리의\b', r'\b우리가\b',
    ]

    # 3인칭 지시어 (주인공)
    THIRD_PERSON_MARKERS = [
        r'\b그는\b', r'\b그의\b', r'\b그가\b',
        r'\b그녀는\b', r'\b그녀의\b', r'\b그녀가\b',
        r'\b그를\b', r'\b그에게\b', r'\b그녀를\b',
    ]

    # 전지적 시점 누수 패턴 (타인 내면)
    OMNISCIENT_LEAK_PATTERNS = [
        # 타인의 생각/감정 직접 서술
        r'(?:그|그녀|그들|[가-힣]{2,4})(?:은|는|이|가)\s+(?:생각했다|느꼈다|판단했다|결심했다)',
        r'(?:그|그녀|그들|[가-힣]{2,4})의\s+(?:마음|생각|심중|속내)(?:에|은|는|이)',
        r'(?:그|그녀|그들|[가-힣]{2,4})(?:은|는)\s+(?:내심|속으로)\s',

        # 주인공이 모르는 장소의 사건
        r'한편\s+(?:그|다른|먼)',
        r'그\s+시각\s+(?:다른|먼|저)',
        r'같은\s+시각',
    ]

    # 인지 범위 초과 패턴
    PERCEPTION_VIOLATION_PATTERNS = [
        # 시각 범위 밖
        r'(?:뒤에서|등\s?뒤에서)(?:[^"]*?)(?:몰래|조용히)',
        r'보이지\s+않는\s+곳에서',
        r'시야\s+밖에서',

        # 청각 범위 밖
        r'들리지\s+않는\s+(?:곳|거리)에서',
        r'(?:멀리서|저\s+멀리서)\s+(?:속삭|중얼)',
    ]

    # 시제 패턴
    TENSE_PATTERNS = {
        'past': [
            r'했다[.!?\s]', r'였다[.!?\s]', r'었다[.!?\s]',
            r'았다[.!?\s]', r'ᆻ다[.!?\s]',
        ],
        'present': [
            r'한다[.!?\s]', r'이다[.!?\s]', r'된다[.!?\s]',
            r'있다[.!?\s]', r'없다[.!?\s]',
        ],
    }

    def __init__(self, pov_type: str = "third_limited", protagonist_name: str = None):
        """
        Args:
            pov_type: 시점 유형
                - "first": 1인칭 시점
                - "third_limited": 3인칭 제한 시점 (기본)
                - "third_omniscient": 3인칭 전지적 시점
            protagonist_name: 주인공 이름 (있으면 더 정확한 검증)
        """
        self.pov_type = pov_type
        self.protagonist_name = protagonist_name

    def validate(self, manuscript: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        시점 일관성 종합 검증

        Args:
            manuscript: 원고 텍스트
            context: 추가 컨텍스트
                - known_characters: 주인공이 아는 캐릭터 목록
                - protagonist_location: 주인공 현재 위치
                - known_info: 주인공이 아는 정보

        Returns:
            {
                "passed": bool,
                "score": float (0-100),
                "issues": [{"type", "severity", "message", "location", "text"}],
                "metrics": {...}
            }
        """
        issues = []
        metrics = {}
        context = context or {}

        # 1. 인칭 혼용 검증
        person_result = self._check_person_consistency(manuscript)
        metrics['first_person_count'] = person_result['first_person_count']
        metrics['third_person_count'] = person_result['third_person_count']
        if person_result['issues']:
            issues.extend(person_result['issues'])

        # 2. 전지적 시점 누수 검증 (3인칭 제한 시점인 경우)
        if self.pov_type == "third_limited":
            omniscient_result = self._check_omniscient_leaks(
                manuscript,
                context.get('known_characters', [])
            )
            metrics['omniscient_leaks'] = omniscient_result['leak_count']
            if omniscient_result['issues']:
                issues.extend(omniscient_result['issues'])

        # 3. 인지 범위 검증
        perception_result = self._check_perception_range(manuscript)
        metrics['perception_violations'] = perception_result['violation_count']
        if perception_result['issues']:
            issues.extend(perception_result['issues'])

        # 4. 내면 서술 위반 검증
        if self.pov_type != "third_omniscient":
            inner_result = self._check_inner_narration(
                manuscript,
                self.protagonist_name
            )
            metrics['inner_violations'] = inner_result['violation_count']
            if inner_result['issues']:
                issues.extend(inner_result['issues'])

        # 5. 시제 일관성 검증
        tense_result = self._check_tense_consistency(manuscript)
        metrics['dominant_tense'] = tense_result['dominant']
        metrics['tense_ratio'] = tense_result['ratio']
        if tense_result['issues']:
            issues.extend(tense_result['issues'])

        # 점수 계산
        score = self._calculate_score(issues)

        # 심각도별 분류
        critical_count = sum(1 for i in issues if i.get('severity') == 'CRITICAL')
        warning_count = sum(1 for i in issues if i.get('severity') == 'WARNING')

        return {
            "passed": critical_count == 0,
            "score": score,
            "issues": issues,
            "metrics": metrics,
            "summary": {
                "critical": critical_count,
                "warning": warning_count,
                "pov_type": self.pov_type,
                "dominant_tense": metrics.get('dominant_tense', 'unknown')
            }
        }

    def _check_person_consistency(self, text: str) -> Dict:
        """인칭 일관성 검증"""
        result = {
            'first_person_count': 0,
            'third_person_count': 0,
            'issues': []
        }

        # 대화문 제외 (대화 안에서는 1인칭 허용)
        text_without_dialogue = re.sub(r'"[^"]*"', '', text)
        text_without_dialogue = re.sub(r"'[^']*'", '', text_without_dialogue)

        # 1인칭 카운트
        for pattern in self.FIRST_PERSON_MARKERS:
            matches = re.findall(pattern, text_without_dialogue)
            result['first_person_count'] += len(matches)

        # 3인칭 카운트
        for pattern in self.THIRD_PERSON_MARKERS:
            matches = re.findall(pattern, text_without_dialogue)
            result['third_person_count'] += len(matches)

        # 혼용 감지
        first = result['first_person_count']
        third = result['third_person_count']

        if first > 0 and third > 0:
            total = first + third
            # 소수 시점이 20% 이상이면 혼용으로 판단
            minor_ratio = min(first, third) / total

            if minor_ratio > 0.2:
                result['issues'].append({
                    'type': 'person_mixing',
                    'severity': 'CRITICAL',
                    'message': f"1인칭/3인칭 혼용 감지: 1인칭 {first}회, 3인칭 {third}회",
                    'location': None,
                    'suggestion': f"{'1인칭' if first < third else '3인칭'}으로 통일 필요"
                })
            elif minor_ratio > 0.1:
                result['issues'].append({
                    'type': 'person_mixing_minor',
                    'severity': 'WARNING',
                    'message': f"시점 흔들림 감지: 1인칭 {first}회, 3인칭 {third}회",
                    'location': None
                })

        # 설정된 시점과 불일치 체크
        if self.pov_type == "first" and third > first:
            result['issues'].append({
                'type': 'pov_mismatch',
                'severity': 'CRITICAL',
                'message': f"1인칭 시점 설정이나 3인칭 서술 우세 ({third} > {first})",
                'location': None
            })
        elif self.pov_type.startswith("third") and first > third and first > 5:
            result['issues'].append({
                'type': 'pov_mismatch',
                'severity': 'CRITICAL',
                'message': f"3인칭 시점 설정이나 1인칭 서술 다수 ({first} > {third})",
                'location': None
            })

        return result

    def _check_omniscient_leaks(self, text: str, known_characters: List[str]) -> Dict:
        """전지적 시점 누수 검증"""
        result = {'leak_count': 0, 'issues': []}

        # 대화문 제외
        text_without_dialogue = re.sub(r'"[^"]*"', '', text)

        for pattern in self.OMNISCIENT_LEAK_PATTERNS:
            matches = list(re.finditer(pattern, text_without_dialogue))
            for match in matches:
                # 주인공이면 허용
                if self.protagonist_name and self.protagonist_name in match.group():
                    continue

                result['leak_count'] += 1

                # 처음 3개만 보고
                if result['leak_count'] <= 3:
                    result['issues'].append({
                        'type': 'omniscient_leak',
                        'severity': 'WARNING',
                        'message': f"전지적 시점 누수: '{match.group()[:50]}...'",
                        'location': match.start(),
                        'text': match.group()[:80]
                    })

        if result['leak_count'] > 3:
            result['issues'].append({
                'type': 'multiple_leaks',
                'severity': 'WARNING',
                'message': f"전지적 시점 누수 총 {result['leak_count']}건 (위 3건 외 {result['leak_count']-3}건 추가)",
                'location': None
            })

        return result

    def _check_perception_range(self, text: str) -> Dict:
        """인지 범위 검증"""
        result = {'violation_count': 0, 'issues': []}

        for pattern in self.PERCEPTION_VIOLATION_PATTERNS:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                result['violation_count'] += 1

                if result['violation_count'] <= 2:
                    result['issues'].append({
                        'type': 'perception_violation',
                        'severity': 'WARNING',
                        'message': f"인지 범위 초과 의심: '{match.group()[:50]}'",
                        'location': match.start(),
                        'suggestion': "주인공이 인지할 수 없는 정보는 나중에 알게 되는 형식으로"
                    })

        return result

    def _check_inner_narration(self, text: str, protagonist_name: str) -> Dict:
        """타인 내면 서술 검증"""
        result = {'violation_count': 0, 'issues': []}

        # 내면 서술 패턴
        inner_patterns = [
            r'([가-힣]{2,4})(?:은|는|이|가)\s+(?:생각했다|느꼈다|마음먹었다|결심했다)',
            r'([가-힣]{2,4})의\s+(?:마음|심중|속마음)(?:에는|은|는)',
        ]

        for pattern in inner_patterns:
            for match in re.finditer(pattern, text):
                character = match.group(1) if match.groups() else ""

                # 주인공 내면은 허용
                if protagonist_name and protagonist_name in character:
                    continue

                # "그"는 주인공일 수 있으므로 주의
                if character in ['그', '그녀']:
                    continue

                result['violation_count'] += 1

                if result['violation_count'] <= 2:
                    result['issues'].append({
                        'type': 'inner_narration_violation',
                        'severity': 'WARNING',
                        'message': f"타인 내면 직접 서술: '{match.group()[:50]}'",
                        'location': match.start(),
                        'suggestion': "'~처럼 보였다', '~인 듯했다' 등 관찰자 시점으로 수정"
                    })

        return result

    def _check_tense_consistency(self, text: str) -> Dict:
        """시제 일관성 검증"""
        result = {'dominant': 'unknown', 'ratio': 0, 'issues': []}

        counts = {'past': 0, 'present': 0}

        for tense, patterns in self.TENSE_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                counts[tense] += len(matches)

        total = counts['past'] + counts['present']
        if total == 0:
            return result

        # 우세 시제 판별
        if counts['past'] >= counts['present']:
            result['dominant'] = 'past'
            result['ratio'] = counts['past'] / total
        else:
            result['dominant'] = 'present'
            result['ratio'] = counts['present'] / total

        # 혼용 감지 (소수 시제가 15% 이상)
        minor_ratio = 1 - result['ratio']
        if minor_ratio > 0.15:
            result['issues'].append({
                'type': 'tense_mixing',
                'severity': 'WARNING',
                'message': f"시제 혼용: {result['dominant']} 시제 {result['ratio']*100:.0f}%, "
                          f"{'present' if result['dominant'] == 'past' else 'past'} 시제 {minor_ratio*100:.0f}%",
                'location': None,
                'suggestion': f"{'과거' if result['dominant'] == 'past' else '현재'} 시제로 통일"
            })

        return result

    def _calculate_score(self, issues: List) -> float:
        """점수 계산"""
        score = 100.0

        for issue in issues:
            severity = issue.get('severity', 'WARNING')
            if severity == 'CRITICAL':
                score -= 20
            elif severity == 'WARNING':
                score -= 5

        return max(0, min(100, score))


def create_pov_validator(
    pov_type: str = "third_limited",
    protagonist_name: str = None
) -> POVValidator:
    """POVValidator 인스턴스 생성 헬퍼"""
    return POVValidator(pov_type=pov_type, protagonist_name=protagonist_name)
