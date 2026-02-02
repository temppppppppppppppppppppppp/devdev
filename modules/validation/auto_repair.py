"""
[V58] Auto-Repair Pipeline

REJECT된 원고/블루프린트 자동 수정 시스템:
- REJECT 사유별 수정 로직
- Python 기반 빠른 수정 (비용 0)
- LLM 기반 정밀 수정 (필요시)
- 수정 후 재검증 루프

수정 가능 항목:
- 분량 문제 (길이 조절)
- 반복 표현 (다양화)
- 포맷 오류 (교정)
- 연속성 오류 (패치)
- 씬 누락 (삽입)
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum


class RepairType(Enum):
    """수정 유형"""
    PYTHON_QUICK = "python"     # Python 빠른 수정
    LLM_PATCH = "llm_patch"     # LLM 부분 수정
    LLM_REWRITE = "llm_rewrite" # LLM 전체 재작성
    MANUAL = "manual"           # 수동 수정 필요


@dataclass
class RepairResult:
    """수정 결과"""
    success: bool
    repair_type: str
    original_issue: str
    changes_made: List[str]
    content: str
    confidence: float  # 수정 신뢰도 (0-1)


class AutoRepairPipeline:
    """
    [V58] 자동 수정 파이프라인

    REJECT 사유에 따라 적절한 수정 전략을 선택하고 적용

    수정 우선순위:
    1. Python 빠른 수정 (비용 0, 확실한 패턴)
    2. LLM 부분 수정 (낮은 비용, 특정 부분만)
    3. LLM 전체 재작성 (높은 비용, 최후 수단)
    """

    # REJECT 사유별 수정 전략
    REPAIR_STRATEGIES = {
        # 분량 문제
        'too_short': {
            'type': RepairType.LLM_PATCH,
            'description': '분량 부족 - 내용 확장 필요',
            'can_python_fix': False,
        },
        'too_long': {
            'type': RepairType.PYTHON_QUICK,
            'description': '분량 초과 - 잘라내기',
            'can_python_fix': True,
        },
        'scope_overflow': {
            'type': RepairType.PYTHON_QUICK,
            'description': 'Blueprint 범위 초과 - 초과분 제거',
            'can_python_fix': True,
        },

        # 반복 문제
        'word_repetition': {
            'type': RepairType.PYTHON_QUICK,
            'description': '단어 과다 반복 - 대체어 사용',
            'can_python_fix': True,
        },
        'pattern_repetition': {
            'type': RepairType.LLM_PATCH,
            'description': '패턴 반복 - 다양화 필요',
            'can_python_fix': False,
        },
        'sentence_repetition': {
            'type': RepairType.PYTHON_QUICK,
            'description': '문장 시작 반복 - 변경',
            'can_python_fix': True,
        },

        # 연속성 문제
        'item_continuity': {
            'type': RepairType.LLM_PATCH,
            'description': '아이템 연속성 오류 - 패치',
            'can_python_fix': False,
        },
        'state_continuity': {
            'type': RepairType.LLM_PATCH,
            'description': '상태 연속성 오류 - 패치',
            'can_python_fix': False,
        },
        'relationship_jump': {
            'type': RepairType.LLM_PATCH,
            'description': '관계 급변 - 중간 단계 추가',
            'can_python_fix': False,
        },

        # 씬 문제
        'missing_scene': {
            'type': RepairType.LLM_PATCH,
            'description': '씬 누락 - 삽입 필요',
            'can_python_fix': False,
        },
        'scene_order': {
            'type': RepairType.PYTHON_QUICK,
            'description': '씬 순서 오류 - 재배치',
            'can_python_fix': True,
        },

        # 포맷 문제
        'format_error': {
            'type': RepairType.PYTHON_QUICK,
            'description': '포맷 오류 - 교정',
            'can_python_fix': True,
        },
        'dialogue_tag': {
            'type': RepairType.PYTHON_QUICK,
            'description': '대사 태그 문제 - 교정',
            'can_python_fix': True,
        },

        # 시점 문제
        'pov_violation': {
            'type': RepairType.LLM_PATCH,
            'description': '시점 오류 - 수정',
            'can_python_fix': False,
        },

        # 기타
        'default': {
            'type': RepairType.LLM_REWRITE,
            'description': '기타 문제 - 재작성 필요',
            'can_python_fix': False,
        },
    }

    # 대체어 사전
    SYNONYM_MAP = {
        '말했다': ['대답했다', '중얼거렸다', '외쳤다', '속삭였다', '답했다'],
        '생각했다': ['떠올렸다', '판단했다', '고민했다', '느꼈다'],
        '보았다': ['바라보았다', '응시했다', '훑어보았다', '살펴보았다'],
        '걸었다': ['걸음을 옮겼다', '발걸음을 떼었다', '이동했다'],
        '그는': ['청년은', '그 사내는', '주인공은'],
        '그녀는': ['여인은', '그 여자는'],
    }

    def __init__(self, client=None, max_repair_attempts: int = 2):
        """
        Args:
            client: Gemini API 클라이언트 (LLM 수정 시 필요)
            max_repair_attempts: 최대 수정 시도 횟수
        """
        self.client = client
        self.max_attempts = max_repair_attempts
        self.repair_history = []

    def repair(
        self,
        content: str,
        validation_result: Dict[str, Any],
        content_type: str = "manuscript",
        context: Dict[str, Any] = None
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        검증 실패 콘텐츠 자동 수정

        Args:
            content: 원본 콘텐츠
            validation_result: 검증 결과 (issues 필수)
            content_type: 콘텐츠 유형 (manuscript/blueprint)
            context: 추가 컨텍스트 (이전 원고, Blueprint 등)

        Returns:
            (수정된 콘텐츠 또는 None, 메타데이터)
        """
        metadata = {
            'attempted': True,
            'repairs_applied': [],
            'success': False,
            'total_attempts': 0,
        }

        issues = validation_result.get('issues', [])
        if not issues:
            metadata['attempted'] = False
            return content, metadata

        repaired_content = content
        remaining_issues = issues.copy()

        for attempt in range(self.max_attempts):
            metadata['total_attempts'] += 1

            # 수정 가능한 이슈 정렬 (Python 수정 가능한 것 우선)
            sorted_issues = self._prioritize_issues(remaining_issues)

            if not sorted_issues:
                break

            for issue in sorted_issues:
                issue_type = issue.get('type', 'default')
                strategy = self.REPAIR_STRATEGIES.get(
                    issue_type,
                    self.REPAIR_STRATEGIES['default']
                )

                # Python 빠른 수정 시도
                if strategy['can_python_fix']:
                    result = self._apply_python_repair(
                        repaired_content, issue, issue_type
                    )
                    if result.success:
                        repaired_content = result.content
                        metadata['repairs_applied'].append({
                            'type': issue_type,
                            'method': 'python',
                            'changes': result.changes_made,
                        })
                        remaining_issues.remove(issue)
                        continue

                # LLM 수정 시도 (클라이언트 있을 때만)
                if self.client and strategy['type'] in [RepairType.LLM_PATCH, RepairType.LLM_REWRITE]:
                    result = self._apply_llm_repair(
                        repaired_content, issue, issue_type,
                        content_type, context
                    )
                    if result.success:
                        repaired_content = result.content
                        metadata['repairs_applied'].append({
                            'type': issue_type,
                            'method': 'llm',
                            'changes': result.changes_made,
                        })
                        remaining_issues.remove(issue)

            # 모든 이슈 해결됐으면 종료
            if not remaining_issues:
                break

        metadata['success'] = len(remaining_issues) == 0
        metadata['remaining_issues'] = len(remaining_issues)

        if metadata['repairs_applied']:
            return repaired_content, metadata
        else:
            return None, metadata

    def _prioritize_issues(self, issues: List[Dict]) -> List[Dict]:
        """이슈 우선순위 정렬"""
        def priority_key(issue):
            issue_type = issue.get('type', 'default')
            strategy = self.REPAIR_STRATEGIES.get(issue_type, self.REPAIR_STRATEGIES['default'])

            # Python 수정 가능 → 높은 우선순위
            python_score = 0 if strategy['can_python_fix'] else 1

            # 심각도
            severity_map = {'CRITICAL': 0, 'WARNING': 1, 'INFO': 2}
            severity_score = severity_map.get(issue.get('severity', 'WARNING'), 1)

            return (python_score, severity_score)

        return sorted(issues, key=priority_key)

    def _apply_python_repair(
        self,
        content: str,
        issue: Dict,
        issue_type: str
    ) -> RepairResult:
        """Python 기반 빠른 수정"""
        changes = []
        repaired = content

        try:
            if issue_type == 'too_long':
                # 분량 초과 - 마지막 씬 축소
                target_length = issue.get('target_length', len(content) * 0.9)
                if len(repaired) > target_length:
                    repaired = repaired[:int(target_length)]
                    # 마지막 문장 완성
                    last_period = repaired.rfind('.')
                    if last_period > 0:
                        repaired = repaired[:last_period + 1]
                    changes.append(f"분량 {len(content)} → {len(repaired)}자로 축소")

            elif issue_type == 'scope_overflow':
                # Blueprint 범위 초과 - 씬 개수 기준 잘라내기
                scene_count = issue.get('expected_scenes', 6)
                max_length = scene_count * 1500 * 1.2  # 20% 여유
                if len(repaired) > max_length:
                    repaired = repaired[:int(max_length)]
                    last_period = repaired.rfind('.')
                    if last_period > 0:
                        repaired = repaired[:last_period + 1]
                    changes.append(f"범위 초과 수정: {len(content)} → {len(repaired)}자")

            elif issue_type == 'word_repetition':
                # 단어 과다 반복 - 대체어 사용
                word = issue.get('word', '')
                if word and word in self.SYNONYM_MAP:
                    synonyms = self.SYNONYM_MAP[word]
                    # 일부만 대체 (전부 대체하면 부자연스러움)
                    count = 0
                    for synonym in synonyms:
                        if repaired.count(word) > 3:
                            repaired = repaired.replace(word, synonym, 1)
                            count += 1
                            if count >= 2:
                                break
                    if count > 0:
                        changes.append(f"'{word}' {count}회 대체")

            elif issue_type == 'sentence_repetition':
                # 문장 시작 반복 - 다양화
                pattern = issue.get('pattern', '')
                if pattern:
                    # 연속 반복만 수정
                    sentences = re.split(r'(?<=[.!?])\s+', repaired)
                    modified = []
                    prev_start = None
                    for sent in sentences:
                        words = sent.split()
                        if words:
                            start = words[0]
                            if start == prev_start and start in self.SYNONYM_MAP:
                                # 첫 단어 대체
                                words[0] = self.SYNONYM_MAP[start][0]
                                sent = ' '.join(words)
                                changes.append(f"문장 시작 '{start}' 변경")
                            prev_start = start
                        modified.append(sent)
                    repaired = ' '.join(modified)

            elif issue_type == 'format_error':
                # 포맷 오류 - 공백/줄바꿈 정리
                repaired = re.sub(r'[ \t]+', ' ', repaired)
                repaired = re.sub(r'\n{3,}', '\n\n', repaired)
                repaired = re.sub(r'"\s+', '"', repaired)
                repaired = re.sub(r'\s+"', '"', repaired)
                changes.append("포맷 정리")

            elif issue_type == 'dialogue_tag':
                # 대사 태그 다양화
                tag = issue.get('tag', '말했다')
                if tag in self.SYNONYM_MAP:
                    count = repaired.count(tag)
                    if count > 3:
                        synonyms = self.SYNONYM_MAP[tag]
                        for i, syn in enumerate(synonyms):
                            if i < count - 2:  # 2개는 남김
                                repaired = repaired.replace(tag, syn, 1)
                        changes.append(f"'{tag}' 다양화")

            if changes:
                return RepairResult(
                    success=True,
                    repair_type='python',
                    original_issue=issue_type,
                    changes_made=changes,
                    content=repaired,
                    confidence=0.9
                )

        except Exception as e:
            print(f"      ⚠️ [AutoRepair] Python 수정 실패: {e}")

        return RepairResult(
            success=False,
            repair_type='python',
            original_issue=issue_type,
            changes_made=[],
            content=content,
            confidence=0
        )

    def _apply_llm_repair(
        self,
        content: str,
        issue: Dict,
        issue_type: str,
        content_type: str,
        context: Dict[str, Any] = None
    ) -> RepairResult:
        """LLM 기반 정밀 수정"""
        if not self.client:
            return RepairResult(
                success=False,
                repair_type='llm',
                original_issue=issue_type,
                changes_made=[],
                content=content,
                confidence=0
            )

        try:
            # 이슈별 수정 프롬프트 생성
            repair_prompt = self._generate_repair_prompt(
                content, issue, issue_type, content_type, context
            )

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=repair_prompt,
                config={
                    "temperature": 0.3,
                    "max_output_tokens": 8192,
                }
            )

            repaired = response.text.strip()

            # 기본 검증 (너무 짧거나 길면 실패)
            if len(repaired) < len(content) * 0.5 or len(repaired) > len(content) * 2:
                return RepairResult(
                    success=False,
                    repair_type='llm',
                    original_issue=issue_type,
                    changes_made=['수정 결과 분량 이상'],
                    content=content,
                    confidence=0.3
                )

            return RepairResult(
                success=True,
                repair_type='llm',
                original_issue=issue_type,
                changes_made=[f"{issue_type} LLM 수정 적용"],
                content=repaired,
                confidence=0.7
            )

        except Exception as e:
            print(f"      ⚠️ [AutoRepair] LLM 수정 실패: {e}")
            return RepairResult(
                success=False,
                repair_type='llm',
                original_issue=issue_type,
                changes_made=[],
                content=content,
                confidence=0
            )

    def _generate_repair_prompt(
        self,
        content: str,
        issue: Dict,
        issue_type: str,
        content_type: str,
        context: Dict[str, Any] = None
    ) -> str:
        """수정 프롬프트 생성"""
        context = context or {}

        base_prompt = f"""다음 {content_type}의 문제를 수정해주세요.

[문제 유형] {issue_type}
[문제 설명] {issue.get('message', '상세 설명 없음')}
"""

        # 이슈별 특화 지시
        specific_instructions = {
            'item_continuity': """
[수정 지시]
- 아이템 연속성 오류를 수정하세요
- 미획득 아이템 사용 → 이미 소지한 것으로 수정하거나 획득 씬 추가
- 이미 사용한 아이템 재사용 → 대체 아이템이나 새 획득으로 수정
""",
            'state_continuity': """
[수정 지시]
- 상태 연속성 오류를 수정하세요
- 부상 상태에서 무리한 행동 → 부상 언급 추가 또는 행동 완화
- 급격한 회복 → 회복 과정 언급 추가
""",
            'relationship_jump': """
[수정 지시]
- 관계 급변 오류를 수정하세요
- 갑작스러운 태도 변화 → 중간 단계 심리 묘사 추가
- 적대에서 우호로 → 계기가 되는 사건/대화 추가
""",
            'missing_scene': """
[수정 지시]
- 누락된 씬을 추가하세요
- Blueprint의 해당 씬 내용을 자연스럽게 삽입
- 전후 맥락과 일관성 유지
""",
            'pov_violation': """
[수정 지시]
- 시점 오류를 수정하세요
- 타인 내면 서술 → '~처럼 보였다', '~인 듯했다'로 수정
- 1인칭/3인칭 혼용 → 일관된 시점으로 통일
""",
        }

        prompt = base_prompt + specific_instructions.get(issue_type, """
[수정 지시]
- 지적된 문제만 최소한으로 수정하세요
- 나머지 내용은 그대로 유지하세요
""")

        # 컨텍스트 추가
        if context.get('prev_manuscript'):
            prompt += f"\n[이전 원고 끝부분]\n{context['prev_manuscript'][-500:]}"

        if context.get('blueprint'):
            bp_str = json.dumps(context['blueprint'], ensure_ascii=False)[:1000]
            prompt += f"\n[Blueprint]\n{bp_str}"

        prompt += f"""

[원본 {content_type}]
{content[:5000]}

[출력]
수정된 내용만 출력하세요. 설명 없이 본문만 작성하세요.
"""

        return prompt

    def get_repair_stats(self) -> Dict[str, Any]:
        """수정 통계"""
        if not self.repair_history:
            return {"total": 0}

        success_count = sum(1 for r in self.repair_history if r.success)
        by_type = {}
        for r in self.repair_history:
            by_type[r.original_issue] = by_type.get(r.original_issue, 0) + 1

        return {
            "total": len(self.repair_history),
            "success": success_count,
            "success_rate": success_count / len(self.repair_history) * 100,
            "by_issue_type": by_type,
        }


def create_auto_repair(client=None, max_attempts: int = 2) -> AutoRepairPipeline:
    """AutoRepairPipeline 인스턴스 생성 헬퍼"""
    return AutoRepairPipeline(client=client, max_repair_attempts=max_attempts)
