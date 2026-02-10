"""
[V40 Premium] 참조 앵커 시스템

주요 사건을 구조화된 "앵커"로 저장하여 AI가 과거 사건을 정확히 기억하도록 강제합니다.
설정 오류와 인과성 모순을 원천 차단합니다.
"""

import json
import re
from typing import List, Dict, Any


class ReferenceAnchor:
    """
    참조 앵커 시스템

    주요 사건을 구조화하여 AI가 반드시 참조하도록 강제합니다.
    """

    # 앵커 타입 정의
    ANCHOR_TYPES = {
        'combat': '전투',
        'item': '아이템',
        'relationship': '인간관계',
        'location': '위치/이동',
        'power': '경지/능력',
        'revelation': '비밀/폭로',
        'injury': '부상/상태',
        'decision': '중요 결정'
    }

    def __init__(self, project_context):
        """
        Args:
            project_context: ProjectContext 인스턴스
        """
        self.context = project_context

    def extract_anchors_from_manuscript(self, ep_num, manuscript_content):
        """
        원고에서 주요 앵커 추출 (AI 보조)

        Args:
            ep_num: 에피소드 번호
            manuscript_content: 원고 텍스트

        Returns:
            List of anchor dicts
        """
        # 원고가 너무 길면 압축 (API 토큰 제한)
        if len(manuscript_content) > 4000:
            compressed = manuscript_content[:2000] + "\n\n...(중략)...\n\n" + manuscript_content[-2000:]
        else:
            compressed = manuscript_content

        # 간단한 프롬프트로 주요 사건 추출
        prompt = f"""
[Role] 서사 앵커 추출 전문가
[Task] 아래 원고에서 향후 에피소드가 반드시 기억해야 할 핵심 사건 3~5개를 추출하십시오.

[원고 - 제 {ep_num}화]
{compressed}

[추출 기준]
1. **인과성에 영향을 주는 사건**: 주인공의 상태 변화, 중요한 획득/손실
2. **설정 충돌 위험 사건**: 무기 교체, 위치 이동, 새로운 인물 등장
3. **복선/반전 요소**: 나중에 회수될 가능성이 있는 사건

[앵커 타입]
- combat: 전투 (누구를 제압/패배)
- item: 아이템 (무엇을 획득/사용/파괴)
- relationship: 인간관계 (누구와 동맹/적대/만남)
- location: 위치/이동 (어디로 이동/도착)
- power: 경지/능력 (경지 상승/새 무공 습득)
- revelation: 비밀/폭로 (중요한 정보 발각)
- injury: 부상/상태 (중상/회복/상태이상)
- decision: 중요 결정 (전략적 선택/맹세)

[출력 형식] JSON Only
{{
    "anchors": [
        {{
            "type": "combat",
            "summary": "주인공이 적대 인물을 제압하고 승리함"
        }},
        {{
            "type": "item",
            "summary": "중요 아이템을 획득함"
        }},
        {{
            "type": "relationship",
            "summary": "주요 인물과 동맹/적대 관계 형성"
        }}
    ]
}}
"""

        try:
            # BaseAgent 패턴 사용 (API 호출)
            from modules.domain.agents.base_agent import BaseAgent

            # API client 존재 여부 검증
            if not hasattr(self.context, 'sys') or not hasattr(self.context.sys, 'api_client'):
                print(f"      ⚠️ [ReferenceAnchor] API client unavailable (ep {ep_num})")
                return []

            # 임시 에이전트 생성
            agent = BaseAgent(self.context, self.context.sys.api_client, model_tier="gemini-2.0-flash")

            response = agent.ask(prompt, temperature=0.2)
            result = agent._extract_json_robust(response)

            anchors = result.get('anchors', [])

            # 에피소드 번호 태깅
            for anchor in anchors:
                anchor['ep_num'] = ep_num

            return anchors

        except Exception as e:
            print(f"      ⚠️ [ReferenceAnchor] 앵커 추출 실패 (제 {ep_num}화): {e}")
            # 실패 시 빈 리스트 반환 (치명적 오류 아님)
            return []

    def get_relevant_anchors(self, current_ep_num, arc_context, n_anchors=5):
        """
        현재 에피소드에 관련된 앵커 추출

        Args:
            current_ep_num: 현재 에피소드 번호
            arc_context: 현재 아크의 tactical_doc 또는 blueprint
            n_anchors: 반환할 앵커 수

        Returns:
            List of relevant anchor summary strings
        """
        # DB에서 모든 앵커 로드
        all_anchors = self.context.db.load_anchor('reference_anchors', default=[])

        if not all_anchors:
            return []

        # [V63.3] 최근 30화 내의 앵커 + 핵심 타입은 전 구간 검색
        critical_types = {'item', 'injury', 'power', 'relationship', 'revelation'}
        recent_anchors = [
            a for a in all_anchors
            if a.get('ep_num', 0) < current_ep_num and (
                current_ep_num - a.get('ep_num', 0) <= 30
                or a.get('type', '') in critical_types
            )
        ]

        if not recent_anchors:
            return []

        # 키워드 매칭으로 관련성 점수 계산
        arc_keywords = set(re.findall(r'[\w가-힣]{2,}', str(arc_context)))

        scored_anchors = []
        for anchor in recent_anchors:
            summary = anchor.get('summary', '')
            anchor_type = anchor.get('type', 'unknown')
            ep_num = anchor.get('ep_num', 0)

            # 앵커 키워드 추출
            anchor_keywords = set(re.findall(r'[\w가-힣]{2,}', summary))

            # 교집합 비율로 관련성 점수 계산
            if anchor_keywords:
                overlap = len(arc_keywords & anchor_keywords)
                # 최근 화일수록 가중치 (현재-5화 이내면 +10점)
                recency_bonus = 10 if (current_ep_num - ep_num) <= 5 else 0
                score = overlap + recency_bonus
            else:
                score = 0

            scored_anchors.append((score, anchor))

        # 점수 높은 순으로 정렬
        scored_anchors.sort(reverse=True, key=lambda x: x[0])

        # 상위 N개 반환 (포맷팅)
        top_anchors = [anchor for _, anchor in scored_anchors[:n_anchors]]

        formatted_anchors = []
        for anchor in top_anchors:
            ep = anchor.get('ep_num', '?')
            type_name = self.ANCHOR_TYPES.get(anchor.get('type', 'unknown'), '기타')
            summary = anchor.get('summary', '')
            formatted_anchors.append(f"[제 {ep}화 | {type_name}] {summary}")

        return formatted_anchors

    def get_critical_anchors(self, current_ep_num, anchor_types=None):
        """
        특정 타입의 최신 앵커만 추출 (강제 참조용)

        Args:
            current_ep_num: 현재 에피소드 번호
            anchor_types: 필터링할 앵커 타입 리스트 (None이면 전부)

        Returns:
            List of critical anchor strings
        """
        all_anchors = self.context.db.load_anchor('reference_anchors', default=[])

        if not all_anchors:
            return []

        # 타입별 최신 앵커 추출
        type_latest = {}

        for anchor in all_anchors:
            if anchor.get('ep_num', 0) >= current_ep_num:
                continue  # 미래 앵커는 제외

            a_type = anchor.get('type', 'unknown')

            # 타입 필터링
            if anchor_types and a_type not in anchor_types:
                continue

            # 해당 타입의 최신 앵커인지 확인
            if a_type not in type_latest or anchor.get('ep_num', 0) > type_latest[a_type].get('ep_num', 0):
                type_latest[a_type] = anchor

        # 포맷팅
        critical_list = []
        for a_type, anchor in type_latest.items():
            ep = anchor.get('ep_num', '?')
            type_name = self.ANCHOR_TYPES.get(a_type, '기타')
            summary = anchor.get('summary', '')
            critical_list.append(f"[제 {ep}화 | {type_name}] {summary}")

        return critical_list

    def save_anchors(self, new_anchors):
        """
        새로운 앵커를 DB에 저장

        Args:
            new_anchors: 추가할 앵커 리스트
        """
        if not new_anchors:
            return

        # 기존 앵커 로드
        all_anchors = self.context.db.load_anchor('reference_anchors', default=[])

        # 새 앵커 추가
        all_anchors.extend(new_anchors)

        # [V66] 1000개 유지 + 오래된 앵커 중 핵심 타입만 보존
        MAX_ANCHORS = 1000
        if len(all_anchors) > MAX_ANCHORS:
            # 최근 700개는 무조건 보존
            recent = all_anchors[-700:]
            older = all_anchors[:-700]
            # 오래된 것 중 핵심 타입(item/injury/power/relationship)만 유지
            critical_types = {'item', 'injury', 'power', 'relationship', 'revelation'}
            preserved_old = [a for a in older if a.get('type', '') in critical_types]
            all_anchors = preserved_old[-(MAX_ANCHORS - 700):] + recent

        # DB 저장
        self.context.db.save_anchor('reference_anchors', all_anchors)

    def generate_reference_prompt(self, relevant_anchors, critical_anchors=None):
        """
        Writer/Architect에게 전달할 참조 프롬프트 생성

        Args:
            relevant_anchors: 관련 앵커 리스트
            critical_anchors: 필수 참조 앵커 리스트 (선택)

        Returns:
            참조 프롬프트 문자열
        """
        if not relevant_anchors and not critical_anchors:
            return ""

        prompt = "[🔗 MANDATORY REFERENCE ANCHORS - 필수 참조 사건]\n"
        prompt += "아래 사건들은 이미 확정된 과거입니다. 절대 모순되지 않도록 하십시오.\n\n"

        if critical_anchors:
            prompt += "[🚨 Critical Anchors - 최신 확정 사실]\n"
            for anchor in critical_anchors:
                prompt += f"  • {anchor}\n"
            prompt += "\n"

        if relevant_anchors:
            prompt += "[📌 Relevant Anchors - 이번 에피소드 관련 과거]\n"
            for anchor in relevant_anchors:
                prompt += f"  • {anchor}\n"

        prompt += """
[준수 사항]
1. 위 앵커들과 모순되는 내용을 절대 작성하지 마십시오.
2. 특히 아이템(무기), 위치, 인간관계, 부상 상태는 최신 앵커를 따르십시오.
3. 앵커에 없는 새로운 사건을 추가하는 것은 허용됩니다.
"""

        return prompt

    def get_statistics(self):
        """
        현재 앵커 통계 반환

        Returns:
            Dict with statistics
        """
        # 컨텍스트 및 DB 유효성 검증
        if not hasattr(self.context, 'db') or not self.context.db:
            return {
                "status": "no_context",
                "error": "Database context not available",
                "total_anchors": 0
            }

        all_anchors = self.context.db.load_anchor('reference_anchors', default=[])

        if not all_anchors:
            return {"status": "no_anchors"}

        # 타입별 분포
        type_counts = {}
        for anchor in all_anchors:
            a_type = anchor.get('type', 'unknown')
            type_counts[a_type] = type_counts.get(a_type, 0) + 1

        # 최신 5개
        recent_5 = all_anchors[-5:] if len(all_anchors) >= 5 else all_anchors

        return {
            "total_anchors": len(all_anchors),
            "type_distribution": type_counts,
            "recent_anchors": [
                f"[{a.get('ep_num')}화] {a.get('type')}: {a.get('summary')}"
                for a in recent_5
            ]
        }
