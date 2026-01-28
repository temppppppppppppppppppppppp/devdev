import json
import re
from .base_agent import BaseAgent

class Evaluator(BaseAgent):
    """[V26 Logic Inspector] 각 Stage별 설계도의 맥락적 연결성을 판정함 (1화 루프 방지 로직 포함)"""

    def check_narrative_flow(self, stage, current_data, previous_data=None):
        """
        [Stage 3: 1화 루프 차단 로직 주입]
        각 단계별 설계도의 서사적 맥락 연결성을 판정함
        """
        # 에피소드 번호 추출 (Stage 3일 경우 current_data에서 ep_num 검색)
        ep_num = 1
        if isinstance(current_data, dict):
            ep_num = current_data.get("ep_num", 1)
        elif isinstance(current_data, str):
            ep_match = re.search(r'"ep_num":\s*(\d+)', current_data)
            if ep_match:
                ep_num = int(ep_match.group(1))

        # 1화(Ep 1)의 경우 통과 문턱을 유연하게 조정 (루프 방지)
        threshold = {"Stage 1": 70, "Stage 2": 50, "Stage 3": 50}.get(stage, 50)
        if stage == "Stage 3" and ep_num == 1:
            threshold = 30  # 1화는 신속한 통과를 위해 임계치 하향 조정

        prompt = f"""
        [Role] 서사 무결성 검수관 (Logic Evaluator)
        [Task] {stage} 설계도의 맥락 연결성을 평가하라. (현재 에피소드: {ep_num}화)

        [현재 설계 데이터]
        {current_data}

        [이전 단계 상위 데이터]
        {previous_data if previous_data else "초기 설계임"}

        [📜 V26 맥락 판정 핵심 강령]
        1. **인과 무결성**: 이전 데이터의 결과가 현재 설계에 반영되었는가?
        2. **설정 일관성**: 주인공의 경지(Martial HUD)나 자산이 모순 없이 배치되었는가?
        3. **타임라인 루프 차단**: 
           - 이미 발생한 사건을 의미 없이 반복하면 감점하라.
           - **[🚨 1화 예외 조항]**: 1화의 '회귀 자각'은 필수 요소다. 이를 '루프'나 '정적 묘사'로 오해하여 반려하지 마라.
           - 자각이 '눈을 떴다' 식의 설명이더라도, 뒤이어 즉각적인 '동작'이 이어진다면 무조건 승인(Pass)하라.

        [작가 특별 지시사항 반영]
        - 1화는 예외적으로 '회귀 자각'을 포함한다. 단, 동작 중에 처리되었는가?
        - 완벽한 도입부에 집착하여 재시도를 유도하지 말고, 서사적 허용치 내라면 즉시 승인하라.

        [Output Format] JSON
        {{
            "stage_score": 0~100,
            "is_logical": true/false,
            "logic_review": "맥락 연결성 비평",
            "critical_error": "발견된 치명적 설정 오류 (없으면 null)"
        }}
        """
        # 온도를 낮게 설정하여 일관된 판정 유도
        response = self.ask(prompt, temperature=0.1)
        result = self._extract_json_robust(response)
        
        # 1화 강제 승인 로직 (점수가 낮아도 치명적 오류가 없으면 통과)
        if stage == "Stage 3" and ep_num == 1:
            if result.get("critical_error") is None:
                result["is_logical"] = True
                result["stage_score"] = max(result.get("stage_score", 0), threshold + 1)
        
        return result