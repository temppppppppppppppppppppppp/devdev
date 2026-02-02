"""
[V58] Dialogue Quality Validator

대화 품질 검증 시스템:
- 대사 태그 다양성 (said 반복 방지)
- 캐릭터별 어투 일관성
- 대화/서술 비율 균형
- 대사 길이 적정성
- 감정 태그 일치

LLM 비용: 0원 (순수 Python 기반)
"""

import re
from typing import Dict, List, Any, Tuple
from collections import Counter


class DialogueValidator:
    """
    [V58] 대화 품질 검증기

    검증 항목:
    1. 대사 태그 다양성 - "말했다" 과다 반복 감지
    2. 대화/서술 비율 - 30-50% 권장
    3. 대사 길이 균형 - 너무 길거나 짧은 대사 경고
    4. 연속 대화 감지 - 서술 없이 대화만 연속되는 구간
    5. 캐릭터 어투 일관성 - 존댓말/반말 혼용 감지
    """

    # 대사 태그 패턴 (한국어)
    DIALOGUE_TAG_PATTERNS = {
        'neutral': [
            r'말했다', r'말하였다', r'말을 했다',
            r'대답했다', r'대답하였다',
            r'답했다', r'답하였다',
        ],
        'emotional': [
            r'외쳤다', r'소리쳤다', r'고함쳤다', r'울부짖었다',
            r'속삭였다', r'중얼거렸다', r'투덜거렸다',
            r'한숨.*쉬며', r'탄식했다',
            r'웃으며', r'미소.*지으며', r'씩.*웃으며',
            r'으르렁거렸다', r'낮게.*말했다', r'차갑게.*말했다',
        ],
        'action': [
            r'물었다', r'되물었다', r'반문했다',
            r'명령했다', r'지시했다', r'호령했다',
            r'부탁했다', r'청했다', r'요청했다',
            r'설명했다', r'덧붙였다', r'이었다',
            r'끊었다', r'잘랐다', r'막았다',
        ],
    }

    # 존댓말/반말 패턴
    SPEECH_LEVEL_PATTERNS = {
        'formal': [  # 존댓말
            r'습니다[.!?"\']', r'습니까[.!?"\']',
            r'세요[.!?"\']', r'시오[.!?"\']',
            r'옵니다[.!?"\']', r'겠습니다[.!?"\']',
        ],
        'informal': [  # 반말
            r'[^습]다[.!?"\']', r'[^니]까[.!?"\']',
            r'어[.!?"\']', r'지[.!?"\']', r'야[.!?"\']',
            r'군[.!?"\']', r'네[.!?"\']',
        ],
        'archaic': [  # 고어체 (무협)
            r'하오[.!?"\']', r'하시오[.!?"\']',
            r'하게[.!?"\']', r'하겠네[.!?"\']',
            r'이로다[.!?"\']', r'하였느니라[.!?"\']',
            r'이니라[.!?"\']', r'로다[.!?"\']',
        ],
    }

    def __init__(self, genre: str = "wuxia"):
        """
        Args:
            genre: 장르 (wuxia/hunter/investment)
        """
        self.genre = genre

        # 장르별 권장 대화 비율
        self.dialogue_ratio_range = {
            'wuxia': (0.25, 0.45),      # 무협: 서술 중심
            'hunter': (0.30, 0.50),     # 헌터: 균형
            'investment': (0.35, 0.55), # 투자: 대화/협상 많음
        }

    def validate(self, manuscript: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        대화 품질 종합 검증

        Args:
            manuscript: 원고 텍스트
            context: 추가 컨텍스트 (캐릭터 정보 등)

        Returns:
            {
                "passed": bool,
                "score": float (0-100),
                "issues": [{"type", "severity", "message", "location"}],
                "metrics": {...}
            }
        """
        issues = []
        metrics = {}

        # 1. 대화 추출
        dialogues = self._extract_dialogues(manuscript)
        metrics['dialogue_count'] = len(dialogues)

        # 2. 대화/서술 비율 검증
        ratio_result = self._check_dialogue_ratio(manuscript, dialogues)
        metrics['dialogue_ratio'] = ratio_result['ratio']
        if ratio_result['issues']:
            issues.extend(ratio_result['issues'])

        # 3. 대사 태그 다양성 검증
        tag_result = self._check_tag_diversity(manuscript)
        metrics['tag_diversity'] = tag_result['diversity']
        metrics['most_common_tags'] = tag_result['most_common']
        if tag_result['issues']:
            issues.extend(tag_result['issues'])

        # 4. 대사 길이 검증
        length_result = self._check_dialogue_lengths(dialogues)
        metrics['avg_dialogue_length'] = length_result['avg_length']
        if length_result['issues']:
            issues.extend(length_result['issues'])

        # 5. 연속 대화 검증
        consecutive_result = self._check_consecutive_dialogues(manuscript)
        metrics['max_consecutive'] = consecutive_result['max_consecutive']
        if consecutive_result['issues']:
            issues.extend(consecutive_result['issues'])

        # 6. 어투 일관성 검증 (컨텍스트 필요)
        if context and context.get('characters'):
            consistency_result = self._check_speech_consistency(
                manuscript, dialogues, context.get('characters', {})
            )
            if consistency_result['issues']:
                issues.extend(consistency_result['issues'])

        # 점수 계산
        score = self._calculate_score(issues, metrics)

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
                "dialogue_count": len(dialogues),
                "dialogue_ratio": f"{metrics.get('dialogue_ratio', 0)*100:.1f}%"
            }
        }

    def _extract_dialogues(self, text: str) -> List[Dict[str, Any]]:
        """대화문 추출"""
        dialogues = []

        # 큰따옴표 대화
        pattern1 = r'"([^"]+)"'
        for match in re.finditer(pattern1, text):
            dialogues.append({
                'text': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'type': 'double_quote'
            })

        # 작은따옴표 대화 (생각/독백)
        pattern2 = r"'([^']+)'"
        for match in re.finditer(pattern2, text):
            # 이미 큰따옴표 안에 있는지 체크
            if not any(d['start'] < match.start() < d['end'] for d in dialogues):
                dialogues.append({
                    'text': match.group(1),
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'single_quote'
                })

        return sorted(dialogues, key=lambda x: x['start'])

    def _check_dialogue_ratio(self, text: str, dialogues: List) -> Dict:
        """대화/서술 비율 검증"""
        result = {'ratio': 0, 'issues': []}

        total_length = len(text)
        if total_length == 0:
            return result

        dialogue_length = sum(len(d['text']) for d in dialogues)
        ratio = dialogue_length / total_length
        result['ratio'] = ratio

        min_ratio, max_ratio = self.dialogue_ratio_range.get(self.genre, (0.25, 0.50))

        if ratio < min_ratio:
            result['issues'].append({
                'type': 'low_dialogue_ratio',
                'severity': 'WARNING',
                'message': f"대화 비율 부족: {ratio*100:.1f}% (권장: {min_ratio*100:.0f}%~{max_ratio*100:.0f}%)",
                'location': None
            })
        elif ratio > max_ratio:
            result['issues'].append({
                'type': 'high_dialogue_ratio',
                'severity': 'WARNING',
                'message': f"대화 비율 과다: {ratio*100:.1f}% (권장: {min_ratio*100:.0f}%~{max_ratio*100:.0f}%)",
                'location': None
            })

        return result

    def _check_tag_diversity(self, text: str) -> Dict:
        """대사 태그 다양성 검증"""
        result = {'diversity': 0, 'most_common': [], 'issues': []}

        # 모든 태그 패턴 매칭
        all_tags = []
        for category, patterns in self.DIALOGUE_TAG_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                all_tags.extend([(m, category) for m in matches])

        if not all_tags:
            return result

        # 빈도 계산
        tag_counts = Counter([t[0] for t in all_tags])
        total_tags = len(all_tags)

        # 가장 많이 사용된 태그
        result['most_common'] = tag_counts.most_common(5)

        # 다양성 점수 (고유 태그 수 / 전체 태그 수)
        unique_tags = len(tag_counts)
        result['diversity'] = unique_tags / total_tags if total_tags > 0 else 0

        # "말했다" 계열 과다 반복 체크
        neutral_count = sum(
            count for tag, count in tag_counts.items()
            if any(re.match(p, tag) for p in self.DIALOGUE_TAG_PATTERNS['neutral'])
        )

        if total_tags > 5 and neutral_count / total_tags > 0.5:
            result['issues'].append({
                'type': 'repetitive_tags',
                'severity': 'WARNING',
                'message': f"대사 태그 단조로움: '말했다' 계열 {neutral_count}/{total_tags}회 ({neutral_count/total_tags*100:.0f}%)",
                'location': None,
                'suggestion': "외쳤다, 속삭였다, 중얼거렸다 등 감정이 담긴 태그 활용"
            })

        # 특정 태그 5회 이상 반복
        for tag, count in tag_counts.items():
            if count >= 5:
                result['issues'].append({
                    'type': 'tag_overuse',
                    'severity': 'WARNING',
                    'message': f"'{tag}' {count}회 반복 사용",
                    'location': None
                })

        return result

    def _check_dialogue_lengths(self, dialogues: List) -> Dict:
        """대사 길이 검증"""
        result = {'avg_length': 0, 'issues': []}

        if not dialogues:
            return result

        lengths = [len(d['text']) for d in dialogues]
        result['avg_length'] = sum(lengths) / len(lengths)

        # 너무 긴 대사 (200자 이상)
        long_dialogues = [d for d in dialogues if len(d['text']) > 200]
        if long_dialogues:
            result['issues'].append({
                'type': 'long_dialogue',
                'severity': 'WARNING',
                'message': f"과도하게 긴 대사 {len(long_dialogues)}개 (200자 초과)",
                'location': long_dialogues[0]['start'],
                'suggestion': "긴 대사는 중간에 행동/반응 묘사로 분리"
            })

        # 너무 짧은 대사만 연속 (5자 이하가 5개 이상 연속)
        short_streak = 0
        max_short_streak = 0
        for d in dialogues:
            if len(d['text']) <= 5:
                short_streak += 1
                max_short_streak = max(max_short_streak, short_streak)
            else:
                short_streak = 0

        if max_short_streak >= 5:
            result['issues'].append({
                'type': 'short_dialogue_streak',
                'severity': 'WARNING',
                'message': f"짧은 대사 {max_short_streak}개 연속 (핑퐁 대화)",
                'location': None,
                'suggestion': "감정/행동 묘사를 사이에 추가하여 리듬감 부여"
            })

        return result

    def _check_consecutive_dialogues(self, text: str) -> Dict:
        """연속 대화 검증 (서술 없이 대화만 이어지는 구간)"""
        result = {'max_consecutive': 0, 'issues': []}

        # 대화 사이 텍스트 길이 체크
        pattern = r'"[^"]+"'
        matches = list(re.finditer(pattern, text))

        if len(matches) < 2:
            return result

        consecutive = 1
        max_consecutive = 1

        for i in range(1, len(matches)):
            between = text[matches[i-1].end():matches[i].start()]
            # 대화 사이 텍스트가 30자 미만이면 연속으로 간주
            if len(between.strip()) < 30:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        result['max_consecutive'] = max_consecutive

        if max_consecutive >= 6:
            result['issues'].append({
                'type': 'consecutive_dialogue',
                'severity': 'WARNING',
                'message': f"서술 없이 대화 {max_consecutive}개 연속 (드라마 대본화)",
                'location': None,
                'suggestion': "대화 사이에 행동, 표정, 환경 묘사 추가"
            })

        return result

    def _check_speech_consistency(
        self,
        text: str,
        dialogues: List,
        characters: Dict[str, Any]
    ) -> Dict:
        """캐릭터별 어투 일관성 검증"""
        result = {'issues': []}

        # 캐릭터별 대사 수집 (간단한 휴리스틱)
        # 대사 직전에 이름이 나오면 해당 캐릭터의 대사로 추정
        char_dialogues = {name: [] for name in characters.keys()}

        for dialogue in dialogues:
            # 대사 앞 50자에서 캐릭터 이름 찾기
            start = max(0, dialogue['start'] - 50)
            context = text[start:dialogue['start']]

            for char_name in characters.keys():
                if char_name in context:
                    char_dialogues[char_name].append(dialogue['text'])
                    break

        # 각 캐릭터의 어투 일관성 체크
        for char_name, char_info in characters.items():
            char_speech = char_dialogues.get(char_name, [])
            if len(char_speech) < 3:
                continue

            expected_level = char_info.get('speech_level', None)
            if not expected_level:
                continue

            # 어투 패턴 매칭
            levels_found = {'formal': 0, 'informal': 0, 'archaic': 0}
            for speech in char_speech:
                for level, patterns in self.SPEECH_LEVEL_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, speech):
                            levels_found[level] += 1
                            break

            total = sum(levels_found.values())
            if total == 0:
                continue

            # 기대 어투 비율 체크
            expected_ratio = levels_found.get(expected_level, 0) / total
            if expected_ratio < 0.7:
                result['issues'].append({
                    'type': 'speech_inconsistency',
                    'severity': 'WARNING',
                    'message': f"'{char_name}' 어투 불일치: {expected_level} 기대, 실제 {expected_ratio*100:.0f}%",
                    'location': None
                })

        return result

    def _calculate_score(self, issues: List, metrics: Dict) -> float:
        """점수 계산 (0-100)"""
        score = 100.0

        for issue in issues:
            severity = issue.get('severity', 'WARNING')
            if severity == 'CRITICAL':
                score -= 15
            elif severity == 'WARNING':
                score -= 5

        # 다양성 보너스
        diversity = metrics.get('tag_diversity', 0)
        if diversity > 0.5:
            score += 5

        return max(0, min(100, score))

    def get_improvement_suggestions(self, result: Dict) -> List[str]:
        """개선 제안 생성"""
        suggestions = []

        for issue in result.get('issues', []):
            if 'suggestion' in issue:
                suggestions.append(f"- {issue['suggestion']}")
            elif issue['type'] == 'low_dialogue_ratio':
                suggestions.append("- 캐릭터 간 대화를 통해 정보 전달 및 갈등 표현")
            elif issue['type'] == 'high_dialogue_ratio':
                suggestions.append("- 환경 묘사, 내면 서술, 행동 묘사 추가")

        return list(set(suggestions))


def create_dialogue_validator(genre: str = "wuxia") -> DialogueValidator:
    """DialogueValidator 인스턴스 생성 헬퍼"""
    return DialogueValidator(genre=genre)
