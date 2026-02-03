import json
import statistics
from .base_agent import BaseAgent
from modules.validation.validation_orchestrator import ValidationOrchestrator



# =================================================================
# [NEW] V30 Analyst 전용 전략 감사관(Strategic Plot Auditor) 프롬프트
# =================================================================
STRATEGIC_AUDIT_PROMPT_V30 = """
[Role] V30 Sovereign 전략 감사관 (Pragmatic Plot Auditor)
[Task] Analyst가 설계한 '아크 전술서'의 논리적 무결성을 검수하되, 작가의 창의적 허용 범위를 존중하라.

### 📋 검수 대상: Arc {arc_no} 전략 계획
- **설정 화수**: {ep_count}화 (제 {ep_start}화 ~ 제 {ep_end}화)
- **회차별 비트**: {beat_sequence}
- **전술서 내용**: {tactical_doc}
- **직전 아크 요약**: {prev_context}
- **현재 블록 원문**: {curr_block}

### 🎯 핵심 검수 항목 (S-Grade Flexible Criteria)
1. **서사 분절성 (Temporal Slicing)**: 각 회차가 고유한 사건을 담고 있는가?
2. **루프 차단 (Zero-Overlap Guard)**: 직전 사건의 단순 반복이 아닌가?
3. **가변 페이싱 적합성**: 설정된 화수에 담기에 사건의 양이 적절한가?
4. **미래 오염 차단 (Future Contamination Guard)**:
   - 현재 블록의 보상/해결/상태에 존재하지 않는 고유 명사(무구, 비기, 인맥, 조직)가 전술서에 등장하면 REJECT.
   - 주인공이 아직 획득하지 않은 아이템이나 배우지 않은 무공은 절대 등장해선 안 된다.

### [🚨 유연한 판정 지침 (Pragmatism)]
1. **관대한 승인**: 전술 설계도의 핵심 맥락이 80% 이상 반영되었고 치명적인 설정 오류(예: 죽은 자의 부활, 성별 바뀜 등)가 없다면, 세부 묘사의 미비함은 '수정 지시'만 남기고 [PASS] 판정하라.
2. **요약질 판정 완화**: 결과 중심 서술(그는 승리했다 식)이라 하더라도, 장면의 제목과 핵심 액션이 명확하다면 집필(Writer) 단계에서 충분히 보완이 가능하므로 승인하라.
3. **분량 하한선 조정**: tactical_doc의 전체 텍스트가 한글 기준 1,500자 이상이고 정보 밀도가 충분하다면 [PASS] 처리하라. 기존의 2,000자 기준을 엄격하게 적용하지 않는다.
4. **인과율 밀도 검수 (Causal Anchor Guard)**:
   - 각 장면의 물리적 분량보다 '사건의 전진'이 있는지를 우선하라.
   - 6개의 장면 중 2개 이상이 '단순 묘사'가 아닌, 인물의 심경 변화나 물리적 타격 등 '인과적 전진'이 느껴지는 핵심 키워드를 포함해야 한다.
   - 문장이 길더라도 알맹이가 없는 '중언부언'은 REJECT하되, 문장이 짧더라도 다음 장면으로 넘어가는 '징검다리' 역할이 확실하다면 PASS하라.

### [Chain-of-Thought Strategic Audit]
다음 단계로 검수하십시오:

Step 1: 미래 오염 검사
- 현재 블록의 보상/해결에 존재하지 않는 무구/비기가 전술서에 등장하는가?
- 아직 획득하지 않은 아이템이나 미습득 무공이 등장하면 REJECT
→ 위반 시 REJECT, 아니면 다음 단계

Step 2: 서사 분절성 검사
- 각 회차가 고유한 사건을 담고 있는가?
- 직전 아크의 단순 반복이 아닌가?
→ 루프 감지 시 REJECT, 아니면 다음 단계

Step 3: 페이싱 적합성 검사
- 설정된 화수({ep_count}화)에 사건의 양이 적절한가?
- 너무 압축되거나 늘어지지 않는가?
→ 부적합 시 REJECT, 적합 시 다음 단계

Step 4: 인과율 밀도 검사
- 6개 장면 중 2개 이상이 '인과적 전진'을 포함하는가?
- 단순 묘사로만 채워지지 않았는가?
→ 밀도 미달 시 REJECT, 충족 시 PASS

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "score": 0~100,
    "loop_detected": true/false,
    "reason": "서사 정체 지점 및 번호 불일치 사유 기술",
    "re_slice_instruction": "개선 제안 (REJECT 시에만 필수, PASS 시에는 공란 가능)"
}}
"""



# =================================================================
# V30 S-Grade 서사/밀도 이중 검수(Director) 프롬프트
# =================================================================

DIRECTOR_AUDIT_PROMPT_V30 = """
[Role] 웹소설 유료 연재 시장의 1타 편집장 (Pacing & Volume Specialist)
[Task] 제 {ep_num}화 {audit_mode}의 품질을 검수하여 'PASS' 혹은 'REJECT'를 판정하라.

### 📊 서사 컨텍스트 및 페이싱
- **아크 전체 분량: {total_eps}화** (이 숫자를 기준으로 전체 전개 속도를 조절하라)
- **현재 아크 내 위치: {arc_pos} / {total_eps}**
- **검수 모드: {audit_mode}** (대상에 맞는 검수 강령을 적용할 것)
- **재시도 횟수: {retry_count}회** (2회 이상 시 유연한 판정 적용)

### 🎯 모드별 검수 강령 (V40.3 실용주의 판정)
1. **[BLUEPRINT/MANUSCRIPT 모드 공통]**:
   - **창작권 존중 (Creative Freedom)**: 작가(Writer)가 서사의 줄기를 해치지 않는 선에서 추가하는 대사, 배경 묘사, 조연의 리액션은 무조건 승인하라.
   - **[V45 원고 우선 원칙 (Manuscript Supremacy)]**:
     (A) 직전 원고(prev_full_text)에서 실제로 일어난 사건이 **진실**이다.
     (B) HUD는 참고 자료일 뿐, 원고와 HUD가 충돌하면 **원고가 우선**한다.
     (C) 직전 원고에서 장비를 획득했다면, HUD에 없더라도 사용 가능하다.
     (D) 직전 원고에서 부상을 입었다면, HUD 상태와 무관하게 부상 상태로 간주한다.
   - **설정 절대 가드 (Hard Constraints)**: 오직 아래 세 가지만 무조건 REJECT하라.
     (A) 주인공의 경지가 직전 원고 기준으로 불가능한 초월적 무공 사용 (예: 아직 배우지 않은 무공 구사).
     (B) 전술 설계도에 명시된 핵심 인물 이름 변경 또는 누락.
     (C) 죽은 자가 살아나거나 장소가 순간이동하는 등 '물리적 인과' 붕괴.
   - **[페이싱 및 흐름 관리]**:
     (A) **속도 우선**: 서사가 다음 화로 넘어가는 추진력이 확보되었다면 세부 미비점은 PASS하라.
     (B) **흐름 검수**: 사건이 한 장면에서 허무하게 끝나버리는 '서사 폭주'나, 똑같은 상황이 3장면 이상 반복되는 '서사 정체'는 REJECT하라.
     (C) **장면 수 체크 (유연한 기준)**:
         - 6개 장면(Scene 1~6)이 목표이나, 재시도 횟수가 2회 이상이면 최소 3개 장면만 있어도 PASS 가능.
         - 재시도 0-1회: 최소 4개 장면 필수, 미만 시 REJECT.
         - 재시도 2회 이상: 최소 3개 장면이 명확하고 서사 흐름이 자연스러우면 PASS.

2. **[MANUSCRIPT 모드] (실제 원고 검수)**:
   - **핵심 목표**: 독자의 가독성, 문체의 유려함, 카타르시스 극대화.
   - **검수 기준**: 지문과 대사의 비율, 플랫폼 특화 문체(사이다/절벽걸기)가 구현되었는가?
   - ⚠️ **구조보다는 '독자 경험과 문장력'**을 최우선으로 본다. (목표: {target_len}자)
   - 🚨 **분량 절대 기준**: 공백 포함 4,000자 미만은 무조건 REJECT. 5,000자 이상을 목표로 하되, 최소 4,000자는 반드시 확보해야 함.


   ###   [🚨 SCENE INTEGRITY CHECK]:
1. Architect가 설계한 6개의 장면(Scene 1~6)이 원고에 모두 포함되었는가? (최소 4개 이상 필수)
2. 특정 장면이 생략되거나 후반부로 갈수록 묘사 밀도가 급격히 떨어지지 않는가?
3. 초반 장면은 상세한데 후반 장면이 급격히 요약되거나 비약했다면, 분량이 충분하더라도 무조건 REJECT하라. 모든 씬이 아키텍트의 설계도와 비슷한 비중으로 작성되었는지 검수하라.

   ### 🚑 [V35 진단 시스템: 에러 분류 가이드]
만약 판정이 'REJECT'일 경우, 반드시 아래 카테고리 중 하나로 분류하십시오.

1. **QUALITY_ISSUE (품질 미달)**:
   - 문체가 건조함, 묘사가 부족함, 목표 분량 미달, 장면의 재미가 떨어짐.
   - 이는 아키텍트의 '노력'으로 해결 가능하며, 즉각적인 아크 수술이 필요하지 않음.

2. **LOGIC_ERROR (논리적 모순 - V35 Surgery Trigger)**:
   - 인과관계 붕괴(예: 검을 들었는데 창을 씀), 설정 오류(죽은 인물 등장), 캐릭터 붕괴.
   - 이는 아크 전술서 자체의 결함으로 간주하며, **애널리스트의 수술이 즉시 필요함.**




### 📋 검수 데이터
- 현재 회차: 제 {ep_num}화 (아크 내 {arc_pos}번째)
- 📜 아크 전술 설계도: {arc_doc}
- 🕒 최근 서사 요약: {history_summary}
- 📄 직전 회차 실제 본문: {prev_full_text} 👈 (중복 방지를 위해 반드시 참조!)
- 📝 검수 대상 ({audit_mode}): {manuscript}

### [Chain-of-Thought Evaluation]
다음 순서로 단계적으로 검수하십시오:

Step 1: 설정 일관성 체크 (V45 원고 우선 원칙 적용)
- 직전 원고 기준으로 불가능한 무공이 등장하는가? (HUD보다 원고 우선)
- 사망한 인물, 파괴된 장소가 정상적으로 등장하는가?
- 핵심 인물 이름이 설계도와 일치하는가?
- 직전 원고에서 획득한 장비를 사용하는 것은 허용 (HUD 미반영이라도 OK)
→ 위반 시 REJECT, 아니면 다음 단계로

Step 2: 장면 구성 평가
- 설계된 장면(Scene 1~6)이 충실히 반영되었는가?
- 각 장면의 밀도가 균등한가? (앞만 상세하고 뒤는 요약 아닌가?)
- 장면 수가 기준을 충족하는가?
→ 미달 시 REJECT, 충족 시 다음 단계로

Step 3: 서사 흐름 검수
- 사건이 다음 화로 넘어가는 추진력이 있는가?
- 같은 상황이 3장면 이상 반복되지 않는가?
- 직전 회차와 내용이 중복되지 않는가?
→ 문제 있으면 REJECT, 없으면 다음 단계로

Step 4: 분량 및 품질 종합 평가
- 분량이 기준을 충족하는가? (MANUSCRIPT: 4000자+)
- 문체가 유려하고 독자 경험이 좋은가?

### [V60.4 점수 산정 공식 (Score Formula)]
점수는 아래 5개 항목의 합계로 산정 (총 100점):

1. **설정 일관성 (25점)**:
   - 25점: 설정 완벽 준수 (무공, 인물, 물리적 인과 모두 정상)
   - 15점: 경미한 설정 미비 (보조 NPC 이름 오타 등)
   - 0점: Hard Constraint 위반 (미습득 무공, 죽은 자 부활 등)

2. **장면 구성 (25점)**:
   - 25점: 6개 씬 모두 균등한 밀도로 반영
   - 20점: 5개 씬 반영 또는 밀도 약간 불균등
   - 15점: 4개 씬 반영
   - 10점: 3개 씬 반영 (재시도 2회+ 시만 PASS 가능)
   - 0점: 2개 씬 이하

3. **서사 흐름 (20점)**:
   - 20점: 추진력 있고 정체/폭주 없음
   - 10점: 약간의 반복 또는 급전개
   - 0점: 서사 폭주(압축) 또는 정체(반복 3회+)

4. **분량 충족 (15점)**:
   - 15점: 5,000자 이상 (이상적)
   - 12점: 4,500~5,000자 (안전)
   - 8점: 4,000~4,500자 (위험)
   - 0점: 4,000자 미만 (절대 REJECT)

5. **문체 품질 (15점)**:
   - 15점: 유려하고 몰입감 높음
   - 10점: 가독성 양호
   - 5점: 건조하나 의미 전달됨
   - 0점: 가독성 심각하게 떨어짐

**PASS 기준**: 총점 65점 이상이면 PASS (재시도 2회+ 시 55점) [V60.24 완화]
**자동 REJECT**: 설정 일관성 0점, 장면 구성 0점, 서사 흐름 0점, 분량 0점 중 하나라도 해당 시

Step 5: 최종 판정
- 위 4단계를 종합하여 PASS/REJECT 결정
- 에러 카테고리 분류 (QUALITY_ISSUE vs LOGIC_ERROR)

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "score": 0~100,
    "score_breakdown": {{
        "setting_consistency": 0~25,
        "scene_composition": 0~25,
        "narrative_flow": 0~20,
        "length_fulfillment": 0~15,
        "prose_quality": 0~15
    }},
    "error_category": "QUALITY_ISSUE" 또는 "LOGIC_ERROR",
    "diagnostic_report": "논리적 모순 발생 시, 정확히 어떤 설정(무기, 인물, 시간)이 충돌했는지 기술",
    "current_beat_achieved": true/false,
    "reason": "판정 근거 (반드시 {audit_mode} 관점에서 서술)",
    "feedback": "증폭/수정을 위한 구체적 지시",
    "lowest_score_area": "가장 낮은 점수를 받은 영역 (setting_consistency/scene_composition/narrative_flow/length_fulfillment/prose_quality)"
}}
"""

class Director(BaseAgent):
    """
    [V0128] Director - 품질 검증 총괄
    [V59] 품질 등급화 A/B/C 및 구체적 수정 가이드 시스템 추가
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.v0128_orchestrator = None  # Lazy initialization
        self.genre = 'wuxia'  # 기본값, set_genre()로 변경 가능
        self.use_v0128 = False  # V0128 검증 시스템 사용 여부

        # [V49.3] Self-Consistency 설정 (Stage 1-3 감사에 적용)
        self.use_self_consistency = True  # Self-Consistency 활성화 여부
        self.consistency_votes = 3  # 투표 횟수
        self.ambiguous_lower = 40  # 애매한 점수 하한 (전략 감사는 0-100 스케일이 아님)
        self.ambiguous_upper = 65  # [V60.24] 애매한 점수 상한 (70→65)

        # [V60.24] 적응형 PASS 기준선 기본값 - 살짝 완화
        self.base_pass_threshold = 60  # 기본 PASS 기준 점수 (65→60)
        self.adaptive_thresholds_enabled = True

    def get_adaptive_threshold(
        self,
        arc_pos: int = 1,
        total_eps: int = 5,
        ep_type: str = "normal",
        retry_count: int = 0
    ) -> dict:
        """
        [V60.6] 적응형 PASS 기준선 계산

        Arc 위치, 장르, 에피소드 타입별로 동적 기준 적용.

        Args:
            arc_pos: Arc 내 위치 (1-based)
            total_eps: Arc 내 총 에피소드 수
            ep_type: 에피소드 타입 ("intro", "transition", "climax", "normal")
            retry_count: 재시도 횟수 (많을수록 관대해짐)

        Returns:
            {
                'pass_threshold': int,
                'length_threshold': int,
                'strictness_level': str,
                'reason': str
            }
        """
        if not self.adaptive_thresholds_enabled:
            return {
                'pass_threshold': self.base_pass_threshold,
                'length_threshold': 4500,
                'strictness_level': 'standard',
                'reason': 'adaptive thresholds disabled'
            }

        base = self.base_pass_threshold
        length_base = 4500
        reason_parts = []

        # 1. Arc 위치 기반 조정
        arc_position_ratio = arc_pos / total_eps if total_eps > 0 else 0.5

        if arc_position_ratio <= 0.2:
            # 도입부 (Arc 첫 1-2화): 관대
            base -= 5
            length_base -= 300
            reason_parts.append("도입부(-5점)")
        elif arc_position_ratio >= 0.8:
            # 절정/결말 (Arc 마지막 1-2화): 엄격
            base += 10
            length_base += 300
            reason_parts.append("절정부(+10점)")
        elif 0.4 <= arc_position_ratio <= 0.6:
            # 중반 전환점: 약간 엄격
            base += 3
            reason_parts.append("전환점(+3점)")

        # 2. 장르별 조정
        if self.genre == 'wuxia':
            # 무협: 액션 밀도 중시
            base += 0  # 기본
        elif self.genre == 'hunter':
            # 헌터: 시스템 일관성 중시
            base += 2
            reason_parts.append("헌터장르(+2점)")
        elif self.genre == 'investment':
            # 투자: 논리성 중시
            base += 3
            reason_parts.append("투자장르(+3점)")

        # 3. 에피소드 타입별 조정
        if ep_type == "climax":
            base += 10
            length_base += 500
            reason_parts.append("클라이맥스(+10점)")
        elif ep_type == "intro":
            base -= 5
            length_base -= 200
            reason_parts.append("도입부(-5점)")
        elif ep_type == "transition":
            base -= 3
            reason_parts.append("전환(-3점)")

        # 4. 재시도 횟수별 완화 (너무 엄격하면 무한 루프)
        if retry_count >= 3:
            base -= 10
            reason_parts.append("3+회재시도(-10점)")
        elif retry_count >= 2:
            base -= 5
            reason_parts.append("2회재시도(-5점)")

        # 5. 범위 제한
        base = max(45, min(85, base))
        length_base = max(3500, min(6000, length_base))

        # 엄격도 레벨 결정
        if base >= 75:
            strictness = 'strict'
        elif base >= 60:
            strictness = 'standard'
        else:
            strictness = 'lenient'

        return {
            'pass_threshold': base,
            'length_threshold': length_base,
            'strictness_level': strictness,
            'reason': ', '.join(reason_parts) if reason_parts else 'standard'
        }

    def apply_adaptive_decision(
        self,
        score: int,
        original_decision: str,
        arc_pos: int = 1,
        total_eps: int = 5,
        retry_count: int = 0
    ) -> dict:
        """
        [V60.6] 적응형 기준에 따라 PASS/REJECT 재결정

        Args:
            score: 평가 점수
            original_decision: 원래 결정 ("PASS" or "REJECT")
            arc_pos: Arc 내 위치
            total_eps: Arc 내 총 에피소드 수
            retry_count: 재시도 횟수

        Returns:
            {
                'decision': str,
                'adjusted': bool,
                'threshold_used': int,
                'reason': str
            }
        """
        threshold_info = self.get_adaptive_threshold(
            arc_pos=arc_pos,
            total_eps=total_eps,
            retry_count=retry_count
        )

        threshold = threshold_info['pass_threshold']
        adjusted = False
        new_decision = original_decision

        # 점수 기반 재결정
        if score >= threshold:
            if original_decision == 'REJECT':
                # 기준보다 높은데 REJECT였으면 PASS로 변경 고려
                # (단, 심각한 논리 오류가 아닐 때만)
                new_decision = 'CONDITIONAL_PASS'
                adjusted = True
        else:
            if original_decision == 'PASS':
                # 기준보다 낮은데 PASS였으면 주의 필요
                # REJECT까지는 아니지만 경고
                new_decision = 'CONDITIONAL_PASS'
                adjusted = True

        return {
            'decision': new_decision,
            'adjusted': adjusted,
            'threshold_used': threshold,
            'strictness': threshold_info['strictness_level'],
            'reason': threshold_info['reason']
        }

    def set_genre(self, genre: str):
        """장르 설정 (main_a.py에서 boot 시 호출)"""
        self.genre = genre
        # 기존 orchestrator 리셋 (장르 변경 시 재초기화 필요)
        self.v0128_orchestrator = None

    def set_v0128_enabled(self, enabled: bool):
        """V0128 검증 시스템 활성화/비활성화"""
        self.use_v0128 = enabled

    def audit_manuscript(self, ep_num, manuscript, arc_doc, history_summary, prev_full_text, arc_pos, total_eps=None, target_len=4500, retry_count=0, validation_context=None):
        """
        원고 검수 (V0128 통합 + V46 캐릭터 논리 검증)

        V0128 활성화 시 3-Tier 검증 시스템 사용
        비활성화 시 기존 LLM 기반 검증 사용
        """
        # [V46] 캐릭터 논리성 검증 (assess_character_logic 활성화)
        if validation_context:
            npc_profiles = validation_context.get('npc_profiles', {})
            character_traits = validation_context.get('character_traits', {})

            # NPC 정보가 있을 때만 캐릭터 논리 검증 수행
            if npc_profiles or character_traits:
                char_logic_result = self.assess_character_logic(
                    ep_num=ep_num,
                    manuscript=manuscript,
                    npc_profiles=npc_profiles,
                    character_traits=character_traits
                )

                # [FIX] CRITICAL 1개 또는 MAJOR 2개 이상일 때만 REJECT (주석과 코드 일치)
                if char_logic_result.get('decision') == 'REJECT':
                    severity = char_logic_result.get('severity', 'NONE')
                    violations = char_logic_result.get('violations', [])
                    major_count = sum(1 for v in violations if isinstance(v, dict) and v.get('severity') == 'MAJOR')

                    # CRITICAL은 1개라도 REJECT, MAJOR는 2개 이상일 때만 REJECT
                    should_reject = (severity == 'CRITICAL') or (severity == 'MAJOR' and major_count >= 2)

                    if should_reject:
                        print(f"      🚨 [V46] 캐릭터 논리 위반 감지 ({severity}, MAJOR {major_count}개)")
                        return {
                            "decision": "REJECT",
                            "score": char_logic_result.get('score', 30),
                            "error_category": "LOGIC_ERROR",
                            "diagnostic_report": f"캐릭터 논리 위반: {violations}",
                            "current_beat_achieved": False,
                            "reason": char_logic_result.get('feedback', '캐릭터 행동이 설정과 불일치'),
                            "feedback": char_logic_result.get('feedback', ''),
                            "v46_character_logic": char_logic_result
                        }
                    else:
                        # MAJOR 1개 또는 MINOR는 경고만 하고 계속 진행
                        print(f"      ⚠️ [V46] 캐릭터 논리 이슈 ({severity}, MAJOR {major_count}개) - 계속 진행")

        # ═══════════════════════════════════════════════════════════════
        # [V60] Blueprint 완전성 검증 - main_a.py에서 사전 검증하므로 여기서는 스킵
        # [V60.1 FIX] 중복 검증 제거 - main_a.py에서 이미 검증 완료
        # ═══════════════════════════════════════════════════════════════
        # Note: validation_context.get('bp_completeness_done', False)가 True면 이미 검증됨
        # main_a.py에서 _validate_blueprint_completeness_v60()을 먼저 호출하므로 여기서 재검증하지 않음

        # [V43] V0128 검증 시스템 조건부 사용
        if self.use_v0128 and validation_context:
            return self._audit_with_v0128(
                ep_num=ep_num,
                manuscript=manuscript,
                validation_context=validation_context,
                target_len=target_len
            )

        # 1. 검수 모드 자동 결정 (기존 로직)
        audit_mode = "BLUEPRINT" if target_len <= 4000 else "MANUSCRIPT"

        # 2. 데이터 안전 처리
        safe_ms = self._escape_braces(manuscript)
        safe_arc = self._escape_braces(arc_doc)
        safe_history = self._escape_braces(history_summary)
        safe_prev = self._escape_braces(prev_full_text) # 👈 수혈 준비
        current_len = len(manuscript)

        # 2-1. 🔒 [V40 Fix] 분량 강제 체크 (AI 판단 이전에 Python 레벨에서 검증)
        if audit_mode == "MANUSCRIPT" and current_len < 4000:
            return {
                "decision": "REJECT",
                "score": 0,
                "error_category": "QUALITY_ISSUE",
                "diagnostic_report": f"분량 절대 미달: {current_len}자",
                "current_beat_achieved": False,
                "reason": f"공백 포함 {current_len}자로 최소 기준(4,000자) 미달. 목표는 5,000자 이상입니다.",
                "feedback": "장면의 밀도를 높이고, 대사와 묘사를 추가하여 5,000자 이상으로 확장하십시오."
            }

        # 2-2. 🚫 [V40 Premium] 반복 구문 체크 (N-gram Deduplication)
        repetition_check_passed = True
        try:
            from modules.core.repetition_guard import RepetitionGuard

            # RepetitionGuard 초기화
            guard = RepetitionGuard(window_size=5, threshold=3)

            # 이전 5화 원고 수집
            prev_manuscripts = []
            for i in range(max(1, ep_num-5), ep_num):
                try:
                    ms = self.context.db.get_manuscript(i)
                    if ms and 'content' in ms:
                        prev_manuscripts.append(ms['content'])
                except Exception as ms_err:
                    # DB 조회 실패는 무시 (원고 없을 수 있음)
                    pass

            # 금지 구문 목록 구축
            if prev_manuscripts:
                banned_phrases = guard.build_banned_list(prev_manuscripts)

                # 현재 원고 스캔
                violations, clean_score = guard.scan_manuscript(manuscript)

                # 위반 발견 시 REJECT (클린 점수 85% 미만)
                if clean_score < 0.85:
                    correction_prompt = guard.generate_correction_prompt(violations)

                    return {
                        "decision": "REJECT",
                        "score": int(clean_score * 100),
                        "error_category": "QUALITY_ISSUE",
                        "diagnostic_report": f"반복 구문 과다 사용 ({len(violations)}개 발견)",
                        "current_beat_achieved": True,  # 내용은 맞지만 표현이 문제
                        "reason": f"최근 5화에서 반복 사용된 구문 {len(violations)}개 발견 (클린 점수: {clean_score:.0%}). 어휘 다양성 확보 필요.",
                        "feedback": correction_prompt
                    }
        except ImportError as ie:
            print(f"      ⚠️ [Director] RepetitionGuard 모듈 로드 실패: {ie}")
            repetition_check_passed = False
        except AttributeError as ae:
            print(f"      ⚠️ [Director] DB 컨텍스트 오류 (RepetitionGuard): {ae}")
            repetition_check_passed = False
        except Exception as e:
            print(f"      ⚠️ [Director] RepetitionGuard 실행 중 예상치 못한 오류: {type(e).__name__}: {e}")
            repetition_check_passed = False

        # 3. 프롬프트 조립 (모든 데이터 유실 없이 매핑)
        prompt = DIRECTOR_AUDIT_PROMPT_V30.format(
            ep_num=ep_num,
            audit_mode=audit_mode,
            total_eps=total_eps if total_eps else "미정",
            arc_pos=arc_pos,
            arc_doc=safe_arc,
            current_len=current_len,
            target_len=target_len,
            history_summary=safe_history,
            prev_full_text=safe_prev, # 👈 뚫려있던 구멍을 메움
            manuscript=safe_ms,
            retry_count=retry_count  # [V40.3 추가] 재시도 횟수 전달
        )
        
        response = self.ask(prompt, temperature=0.1)
        return self._extract_json_robust(response)
    

    def audit_strategic_plan(self, arc_plan, prev_arc_context, curr_block=None, protagonist_name=None):
        """
        [Stage 2] Analyst의 아크 설계안에 대한 전략적 무결성 검수 (루프/미래 오염 방지)

        [V49.3] Self-Consistency 투표 적용:
        - 1차 평가 후 애매한 결과면 추가 평가 진행
        - 중앙값 + 다수결로 최종 결정
        """
        arc_no = arc_plan.get("arc_no")
        arc_dump = json.dumps(arc_plan, ensure_ascii=False)

        # 🔒 [V42 Hard Guard] 주인공 이름 일관성 검증
        if protagonist_name and len(protagonist_name) >= 2:
            # [V60.55 DEBUG] 주인공 이름 검색 디버깅
            tactical_doc = arc_plan.get('tactical_doc', '')
            name_in_tactical = protagonist_name in tactical_doc
            name_in_dump = protagonist_name in arc_dump
            print(f"      🔍 [V60.55 DEBUG] 주인공 이름 검증: '{protagonist_name}'")
            print(f"         - tactical_doc 내 존재: {name_in_tactical}")
            print(f"         - arc_dump 내 존재: {name_in_dump}")
            print(f"         - tactical_doc 앞 200자: {tactical_doc[:200]}...")

            if not name_in_dump:
                print(f"      🚨 [V60.55] 주인공 이름 '{protagonist_name}' 미발견 → REJECT")
                return {
                    "decision": "REJECT",
                    "score": 0,
                    "loop_detected": False,
                    "reason": f"주인공 이름 '{protagonist_name}' 누락 감지 - 서사 무결성 파괴",
                    "re_slice_instruction": f"모든 주인공 서술에서 '{protagonist_name}'을 명시적으로 사용하라. 유사 명칭이나 다른 인물 이름으로 대체 금지."
                }
            else:
                print(f"      ✅ [V60.55] 주인공 이름 '{protagonist_name}' 확인됨")

        # 🔒 [Hard Guard] 미래 무구 조기 노출 차단 (V43: Bible 기반 동적 검증)
        # 특정 아이템 하드코딩 제거 - Bible의 'future_items' 또는 블록별 보상 데이터로 검증
        # 이 검증은 BlockingValidator의 unowned_item_usage 체크로 대체됨
        pass

        # 데이터 안전화 처리
        safe_tactical = self._escape_braces(arc_plan.get('tactical_doc', ''))
        safe_beats = self._escape_braces(str(arc_plan.get('beat_sequence', [])))
        safe_prev = self._escape_braces(prev_arc_context)
        safe_curr = self._escape_braces(json.dumps(curr_block, ensure_ascii=False)) if curr_block else "없음"

        prompt = STRATEGIC_AUDIT_PROMPT_V30.format(
            arc_no=arc_plan.get('arc_no', '?'),
            ep_count=arc_plan.get('ep_count', 0),
            ep_start=arc_plan.get('ep_start', 0),
            ep_end=arc_plan.get('ep_end', 0),
            beat_sequence=safe_beats,
            tactical_doc=safe_tactical,
            prev_context=safe_prev,
            curr_block=safe_curr
        )

        # [V49.3] Self-Consistency 적용
        if self.use_self_consistency:
            return self._strategic_audit_with_self_consistency(prompt, arc_no)
        else:
            response = self.ask(prompt, temperature=0.1)
            return self._extract_json_robust(response)

    def _strategic_audit_with_self_consistency(self, prompt: str, arc_no: int) -> dict:
        """
        [V49.3] 전략 감사에 Self-Consistency 투표 적용

        Stage 2/3에서 Director가 LLM 단일 호출의 환각을 방지하기 위해:
        1. 1차 평가 실행
        2. 결과가 애매하면 (PASS이지만 score가 낮거나 경고 포함) 추가 2회 평가
        3. 다수결로 최종 PASS/REJECT 결정

        Returns:
            dict: 감사 결과 (self_consistency 정보 포함)
        """
        # 1차 평가
        response = self.ask(prompt, temperature=0.1)
        first_eval = self._extract_json_robust(response)

        if not isinstance(first_eval, dict):
            first_eval = {"decision": "REJECT", "score": 0, "reason": "JSON 파싱 실패"}

        first_decision = first_eval.get('decision', 'REJECT')
        first_score = first_eval.get('score', 50)

        # 명확한 REJECT → 추가 평가 없이 반환
        if first_decision == 'REJECT' and first_score < self.ambiguous_lower:
            reject_reason = first_eval.get('reason', first_eval.get('re_slice_instruction', '사유 미상'))
            print(f"         🎬 [Director] REJECT (score={first_score})")
            print(f"            └─ 사유: {reject_reason[:80]}{'...' if len(str(reject_reason)) > 80 else ''}")
            first_eval['self_consistency'] = {
                'votes': 1,
                'reason': 'clear_reject',
                'pass_votes': 0
            }
            return first_eval

        # 명확한 PASS (점수가 높음) → 추가 평가 없이 반환
        if first_decision == 'PASS' and first_score > self.ambiguous_upper:
            pass_reason = first_eval.get('reason', first_eval.get('strengths', '판단 근거 미상'))
            print(f"         🎬 [Director] PASS (score={first_score})")
            print(f"            └─ 근거: {str(pass_reason)[:80]}{'...' if len(str(pass_reason)) > 80 else ''}")
            first_eval['self_consistency'] = {
                'votes': 1,
                'reason': 'clear_pass',
                'pass_votes': 1
            }
            return first_eval

        # 애매한 구간 → 추가 평가 진행
        print(f"         ⚖️ [V49.3] 애매한 결과({first_decision}, score={first_score}) → Self-Consistency 활성화")

        evaluations = [first_eval]

        # [V60.68] Self-Consistency 병렬화
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _vote_task(vote_idx, temp):
            """단일 투표 작업"""
            response = self.ask(prompt, temperature=temp)
            return vote_idx, self._extract_json_robust(response)

        vote_tasks = [(i, 0.1 + (i * 0.05)) for i in range(1, self.consistency_votes)]

        with ThreadPoolExecutor(max_workers=min(3, len(vote_tasks))) as executor:
            futures = {executor.submit(_vote_task, idx, temp): idx for idx, temp in vote_tasks}

            for future in as_completed(futures):
                try:
                    vote_idx, eval_result = future.result()
                    if isinstance(eval_result, dict):
                        evaluations.append(eval_result)
                        eval_decision = eval_result.get('decision', 'REJECT')
                        eval_score = eval_result.get('score', 0)
                        print(f"            Vote {vote_idx+1}: {eval_decision} (score={eval_score})")
                except Exception as e:
                    print(f"            ⚠️ Vote 오류: {str(e)[:50]}")

        # 점수들의 중앙값
        scores = [e.get('score', 50) for e in evaluations if isinstance(e, dict)]
        median_score = statistics.median(scores) if scores else 50

        # PASS/REJECT 다수결
        pass_votes = sum(1 for e in evaluations if e.get('decision') == 'PASS')
        final_decision = 'PASS' if pass_votes > (len(evaluations) // 2) else 'REJECT'

        # 대표 결과 선택 (중앙값에 가장 가까운 것)
        representative = min(evaluations, key=lambda e: abs(e.get('score', 50) - median_score))

        # 결과 병합
        result = representative.copy()
        result['decision'] = final_decision
        result['score'] = median_score
        result['self_consistency'] = {
            'votes': len(evaluations),
            'pass_votes': pass_votes,
            'scores': scores,
            'median_score': median_score,
            'reason': f'ambiguous_result ({first_decision}, score={first_score})'
        }

        print(f"         ✅ [V49.3] Self-Consistency 완료: {final_decision} (PASS {pass_votes}/{len(evaluations)}, median={median_score})")

        return result    

    def audit_timeline_logic(self, ep_num, current_manuscript, prev_summary):
        """[V38.1] 시공간 및 동선 모순 정밀 감사 (Timeline Auditor)"""

        prompt = f"""
        [Role] 시공간 정합성 감사관 (Continuity Supervisor)
        [Task] 직전 화의 요약본과 현재 원고를 대조하여 '동선'과 '시간'의 모순을 적발하라.

        ### 🔍 감시 대상 데이터
        1. [직전 화 요약 (Prev Context)]: {prev_summary}
        2. [현재 원고 (Current Draft)]: {current_manuscript[:3000]}... (이하 생략)

        ### 🚨 집중 단속 항목 (Red Flags)
        1. **동선 충돌**: A장소에 이미 들어와 있는데, 묘사 없이 다시 A장소 입구로 들어오는 장면이 있는가?
        2. **시간 역행**: 밤(Night)에 잠들거나 활동했는데, 갑자기 설명 없이 낮(Day)이나 황혼으로 시간이 튀는가?
        3. **사건 중복**: 이미 해결된 사건(예: 특정인과의 만남)이 마치 처음인 것처럼 다시 발생하는가?

        [Output Format] JSON Only
        {{
            "status": "PASS" 또는 "FAIL",
            "contradiction_level": 0~10 (0이면 모순 없음, 10이면 치명적),
            "reason": "발견된 모순점 상세 기술 (없으면 '이상 없음')",
            "correction_guide": "모순 해결을 위한 구체적 수정 지시"
        }}
        """
        response = self.ask(prompt, temperature=0.1)
        return self._extract_json_robust(response)


    # =================================================================
    # ═══════════════════════════════════════════════════════════════
    # [V60] Blueprint 완전성 검증
    # ═══════════════════════════════════════════════════════════════

    def _validate_blueprint_completeness_v60(self, manuscript: str, blueprint: dict) -> dict:
        """
        [V60] Blueprint 완전성 검증 - 원고가 설계 씬을 충분히 반영했는지 확인

        Args:
            manuscript: 검증 대상 원고
            blueprint: Blueprint 데이터

        Returns:
            {
                "valid": bool,
                "scene_coverage": float (0-100%),
                "expected_scenes": int,
                "reflected_scenes": int,
                "missing_scenes": list,
                "warnings": list,
                "reason": str,
                "feedback": str,
                "score": int
            }
        """
        import re

        if not blueprint or not isinstance(blueprint, dict):
            return {
                "valid": True,
                "scene_coverage": 100,
                "expected_scenes": 0,
                "reflected_scenes": 0,
                "missing_scenes": [],
                "warnings": [],
                "reason": "",
                "feedback": "",
                "score": 100
            }

        warnings = []
        missing_scenes = []

        # 1. Blueprint에서 씬 정보 추출
        scene_breakdown = blueprint.get('scene_breakdown', {})
        integrated_scenario = blueprint.get('integrated_scenario', '')

        # scene_breakdown이 dict인 경우 씬 개수 계산
        if isinstance(scene_breakdown, dict):
            scene_keys = [k for k in scene_breakdown.keys() if k.startswith('scene') or k.startswith('Scene')]
            expected_scenes = len(scene_keys)

            # 각 씬의 핵심 키워드 추출
            scene_keywords = {}
            for scene_key in scene_keys:
                scene_content = scene_breakdown.get(scene_key, '')
                if isinstance(scene_content, str):
                    # 씬 타입 추출 ([Core], [Buffer], [Cliffhanger] 등)
                    type_match = re.search(r'\[(Core|Buffer|Cliffhanger|Climax)\]', scene_content, re.IGNORECASE)
                    scene_type = type_match.group(1) if type_match else 'Unknown'

                    # 핵심 키워드 추출 (명사/동사 중심)
                    keywords = re.findall(r'[가-힣]{2,5}(?:하다|되다|이다)?', scene_content)
                    # 상위 5개 키워드만 사용
                    scene_keywords[scene_key] = {
                        'type': scene_type,
                        'keywords': keywords[:5] if keywords else [],
                        'content_sample': scene_content[:100]
                    }
        elif isinstance(scene_breakdown, list):
            expected_scenes = len(scene_breakdown)
            scene_keywords = {f'scene_{i+1}': {'type': 'Unknown', 'keywords': [], 'content_sample': str(item)[:100]}
                           for i, item in enumerate(scene_breakdown)}
        else:
            # scene_breakdown이 없으면 integrated_scenario에서 추정
            scene_markers = re.findall(r'\[(?:Core|Buffer|Cliffhanger|Scene)\s*\d*\]', integrated_scenario, re.IGNORECASE)
            expected_scenes = len(scene_markers) if scene_markers else 6  # 기본 6개
            scene_keywords = {}

        if expected_scenes == 0:
            expected_scenes = 6  # 기본값

        # 2. 원고에서 씬 반영 여부 확인
        reflected_count = 0

        for scene_key, scene_info in scene_keywords.items():
            keywords = scene_info.get('keywords', [])
            scene_type = scene_info.get('type', 'Unknown')

            # 키워드 매칭
            matched_keywords = 0
            for keyword in keywords:
                if keyword in manuscript:
                    matched_keywords += 1

            # 키워드의 50% 이상 매칭되면 반영된 것으로 판단
            if len(keywords) == 0 or matched_keywords >= len(keywords) * 0.5:
                reflected_count += 1
            else:
                missing_scenes.append({
                    'scene': scene_key,
                    'type': scene_type,
                    'missing_keywords': [k for k in keywords if k not in manuscript][:3],
                    'sample': scene_info.get('content_sample', '')[:50]
                })

        # 키워드가 없는 경우 길이 기반 추정
        if not scene_keywords:
            # 원고 길이 기반으로 씬 반영 추정
            min_chars_per_scene = 600  # 씬당 최소 600자
            estimated_scenes = len(manuscript) // min_chars_per_scene
            reflected_count = min(estimated_scenes, expected_scenes)

        # 3. 커버리지 계산
        scene_coverage = (reflected_count / expected_scenes * 100) if expected_scenes > 0 else 100

        # 4. 판정 [V60.24] 기준 완화
        MIN_COVERAGE = 65  # [V60.24] 최소 65% 반영 필요 (70→65)

        if scene_coverage < MIN_COVERAGE:
            return {
                "valid": False,
                "scene_coverage": round(scene_coverage, 1),
                "expected_scenes": expected_scenes,
                "reflected_scenes": reflected_count,
                "missing_scenes": missing_scenes,
                "warnings": warnings,
                "reason": f"Blueprint 반영률 부족: {reflected_count}/{expected_scenes} 씬 ({scene_coverage:.1f}%)",
                "feedback": f"설계된 {expected_scenes}개 씬 중 {reflected_count}개만 반영됨. 누락된 씬을 추가하세요: {[m['scene'] for m in missing_scenes[:3]]}",
                "score": int(scene_coverage * 0.5)
            }

        # [V60.24] 75% 미만이면 경고 (80→75)
        if scene_coverage < 75:
            warnings.append(f"씬 반영률 {scene_coverage:.1f}% (권장: 75% 이상)")

        # Cliffhanger 씬 검증
        has_cliffhanger = any(
            'cliffhanger' in str(scene_info.get('type', '')).lower()
            for scene_info in scene_keywords.values()
        )
        if has_cliffhanger:
            # 원고 마지막 500자에서 긴장감 키워드 확인
            ending = manuscript[-500:] if len(manuscript) >= 500 else manuscript
            tension_keywords = ['그때', '순간', '갑자기', '돌연', '하지만', '그러나', '예상치 못한', '충격', '긴장']
            has_tension = any(kw in ending for kw in tension_keywords)
            if not has_tension:
                warnings.append("Cliffhanger 엔딩 긴장감 부족 - 마지막 장면에 서스펜스 요소 추가 권장")

        return {
            "valid": True,
            "scene_coverage": round(scene_coverage, 1),
            "expected_scenes": expected_scenes,
            "reflected_scenes": reflected_count,
            "missing_scenes": missing_scenes,
            "warnings": warnings,
            "reason": "",
            "feedback": "",
            "score": 100 - len(warnings) * 5
        }

    # [V0128] 3-Tier Validation System
    # =================================================================

    def _audit_with_v0128(self, ep_num, manuscript, validation_context, target_len=4500):
        """
        [V43 내부 헬퍼] V0128 검증 시스템 사용 (장르 자동 전달)

        audit_manuscript에서 use_v0128=True일 때 호출됨
        """
        # mode 자동 결정
        mode = "BLUEPRINT" if target_len <= 4000 else "MANUSCRIPT"
        validation_context['mode'] = mode

        # 내부 장르 설정 사용
        return self.audit_manuscript_v0128(
            ep_num=ep_num,
            manuscript=manuscript,
            validation_context=validation_context,
            genre=self.genre  # Director에 저장된 장르 사용
        )

    def audit_manuscript_v0128(self, ep_num, manuscript, validation_context, config=None, genre='wuxia'):
        """
        [V0128] 3-Tier 검증 시스템을 사용한 원고 검수

        Args:
            ep_num: 에피소드 번호
            manuscript: 검수 대상 원고
            validation_context: {
                'encyclopedia': {...},
                'martial_hud': {...},
                'blueprint': {...},
                'mode': 'BLUEPRINT' | 'MANUSCRIPT',
                'history': [...],
                'npc_profiles': {...}
            }
            config: 검증 설정 dict (선택적)
            genre: 장르 ('wuxia', 'hunter', 'investment')

        Returns:
            dict: {
                "final_decision": "PASS" | "CONDITIONAL_PASS" | "REJECT",
                "total_score": float,
                "blocking_result": {...},
                "scoring_result": {...},
                "advisory_result": {...},
                "feedback": str,
                "detailed_feedback": str,
                "self_consistency_used": bool
            }
        """
        # Lazy initialization of ValidationOrchestrator
        if self.v0128_orchestrator is None:
            default_config = {
                'scoring_model': self.primary_model,
                'advisory_model': 'gemini-2.0-flash',
                'scoring_threshold': 65,  # [V60.24] 70→65 완화
                'use_self_consistency': True,
                'consistency_votes': 3
            }
            if config:
                default_config.update(config)

            self.v0128_orchestrator = ValidationOrchestrator(
                config=default_config,
                client=self.client,
                genre=genre
            )

        # Run 3-tier validation
        try:
            result = self.v0128_orchestrator.validate(
                ep_num=ep_num,
                manuscript=manuscript,
                validation_context=validation_context
            )

            # Convert V0128 decision format to legacy format for compatibility
            legacy_result = {
                "decision": result['final_decision'],
                "score": result['total_score'],
                "reason": result['feedback'],
                "feedback": result['detailed_feedback'],
                "v0128_full_result": result  # Keep full result for detailed analysis
            }

            # [FIX] Map V0128 decisions to legacy PASS/REJECT (KeyError 방지)
            final_decision = result.get('final_decision', 'REJECT') if isinstance(result, dict) else 'REJECT'
            if final_decision in ['PASS', 'CONDITIONAL_PASS']:
                legacy_result['decision'] = 'PASS'
            else:
                legacy_result['decision'] = 'REJECT'

            return legacy_result

        except Exception as e:
            print(f"      🚨 [V0128 Error] 검증 중 예외 발생: {e}")
            # [FIX] 안전 실패 - REJECT 반환 (검증 우회 방지)
            return {
                "decision": "REJECT",
                "score": 0,
                "reason": f"V0128 검증 시스템 오류: {str(e)}",
                "feedback": "검증 시스템 오류 - 수동 검토 필요",
                "error": str(e)
            }


    # =================================================================
    # [V41] Director Sovereignty - 캐릭터 논리성 검증 & 상태 승인
    # =================================================================

    def assess_character_logic(self, ep_num, manuscript, npc_profiles, character_traits):
        """
        [V41 Red Team] 캐릭터 논리성 적대적 검증

        Args:
            ep_num: 에피소드 번호
            manuscript: 검수 대상 원고
            npc_profiles: 등장 NPC 프로필 (Master Bible에서 추출)
            character_traits: 캐릭터 특성 DB (성격, 지능, 무공 수준 등)

        Returns:
            dict: {decision, score, violations, severity, feedback}
        """
        safe_manuscript = self._escape_braces(manuscript[:6000])  # 토큰 절약
        safe_npc = self._escape_braces(json.dumps(npc_profiles, ensure_ascii=False))
        safe_traits = self._escape_braces(json.dumps(character_traits, ensure_ascii=False))

        prompt = f"""
[Role] 레드팀 캐릭터 논리성 감사관 (Character Logic Auditor)
[Task] 원고 내 등장인물의 행동이 설정된 특성과 일치하는지 적대적으로 검증하라.

### 📋 검수 대상 데이터
- 현재 회차: 제 {ep_num}화
- 📝 원고 내용: {safe_manuscript}
- 👤 등장 NPC 프로필: {safe_npc}
- 🎭 캐릭터 특성 DB: {safe_traits}

### 🎯 적대적 검증 항목 (Red Team Criteria)
1. **지능적 캐릭터의 어리석은 결정**:
   - '교활한', '노회한', '간사한' 특성의 인물이 비합리적/어리석은 결정을 내리는가?
   - 예: 교활한 악당이 주인공을 함정에 빠뜨릴 수 있는 상황에서 정면대결을 선택

2. **강자의 급격한 약화**:
   - 설정상 강자가 설명 없이 쉽게 제압당하는가?
   - 예: 일류 고수가 삼류의 기습에 무력하게 당함

3. **성격 일관성 위반**:
   - 냉혹한 인물이 갑자기 자비를 베풀거나, 소심한 인물이 돌연 대담해지는가?
   - 성격 변화가 있다면 충분한 서사적 근거가 있는가?

4. **동기 불명 행동**:
   - 인물의 행동에 명확한 동기가 보이지 않는가?
   - 특히 주인공에게 유리한 방향으로 '우연히' 행동하는 조연

### [🚨 판정 기준]
- NPC 프로필이나 특성 DB가 비어있으면 자동 PASS (검증 불가)
- 경미한 위반(MINOR)은 경고만 하고 PASS
- 중대한 위반(MAJOR) 2개 이상 또는 치명적 위반(CRITICAL) 1개 이상 시 REJECT

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "score": 0~100,
    "violations": [
        {{
            "character": "캐릭터명",
            "trait": "설정된 특성",
            "action": "문제 행동",
            "reason": "위반 사유"
        }}
    ],
    "severity": "NONE" 또는 "MINOR" 또는 "MAJOR" 또는 "CRITICAL",
    "feedback": "수정 지침 (REJECT 시 필수, PASS 시 권고사항)"
}}
"""
        # NPC 정보가 비어있으면 자동 PASS
        if not npc_profiles and not character_traits:
            return {
                "decision": "PASS",
                "score": 100,
                "violations": [],
                "severity": "NONE",
                "feedback": "NPC 프로필 없음 - 캐릭터 논리 검증 생략"
            }

        response = self.ask(prompt, temperature=0.1)
        return self._extract_json_robust(response)


    def on_approve_workflow(self, ep_num, state_updates, current_hud, martial_manager=None):
        """
        [V41 Director Sovereignty] 상태 업데이트 검증 및 적용

        Writer가 제안한 state_updates를 검증하고, 승인된 항목만 반환합니다.

        Args:
            ep_num: 에피소드 번호
            state_updates: Writer가 제안한 상태 변화 dict
            current_hud: 현재 HUD 상태 dict
            martial_manager: MartialManager 인스턴스 (선택적)

        Returns:
            dict: {
                "approved": True/False,
                "applied_updates": {...},  # 실제 적용할 업데이트
                "rejected_updates": {...}, # 거부된 업데이트 (이유 포함)
                "warnings": [...]          # 경고 메시지
            }
        """
        if not state_updates or not isinstance(state_updates, dict):
            return {
                "approved": True,
                "applied_updates": {},
                "rejected_updates": {},
                "warnings": ["Writer가 state_updates를 제출하지 않음 - 상태 변경 없음"]
            }

        applied = {}
        rejected = {}
        warnings = []

        # 검증 규칙 정의
        LIMITS = {
            "internal_energy": {"max_increase": 200, "max_decrease": -500},
            "misunderstanding": {"max_change": 30},
            "obsession": {"max_change": 30},
            "wealth": {"max_change": 10000}
        }

        for key, value in state_updates.items():
            # "현상 유지" 처리
            if value in ["현상 유지", "유지", "변화 없음", None, ""]:
                continue

            # 수치 변화 파싱 시도
            if isinstance(value, str) and (value.startswith("+") or value.startswith("-")):
                try:
                    # [V44 Fix] 정규식으로 안전한 숫자 추출 ("+100" → 100, "-50냥" → -50)
                    import re
                    numeric_match = re.match(r'^([+-]?\d+)', value)
                    if numeric_match:
                        change = int(numeric_match.group(1))

                        # 범위 검증
                        if key in LIMITS:
                            limits = LIMITS[key]
                            if "max_increase" in limits and change > limits["max_increase"]:
                                rejected[key] = {
                                    "proposed": value,
                                    "reason": f"증가량 초과 (최대 +{limits['max_increase']})"
                                }
                                warnings.append(f"[REJECT] {key}: {value} → 비합리적 증가량")
                                continue
                            if "max_decrease" in limits and change < limits["max_decrease"]:
                                rejected[key] = {
                                    "proposed": value,
                                    "reason": f"감소량 초과 (최대 {limits['max_decrease']})"
                                }
                                warnings.append(f"[REJECT] {key}: {value} → 비합리적 감소량")
                                continue
                            if "max_change" in limits and abs(change) > limits["max_change"]:
                                rejected[key] = {
                                    "proposed": value,
                                    "reason": f"변화량 초과 (최대 ±{limits['max_change']})"
                                }
                                warnings.append(f"[REJECT] {key}: {value} → 변화량 초과")
                                continue
                except ValueError:
                    pass  # 숫자가 아닌 경우 그대로 진행

            # 경지(realm) 변화 검증 - 한 단계 이상 점프 시 경고
            if key == "realm" and current_hud:
                current_realm = current_hud.get("realm", "")
                if value != current_realm:
                    # 경지 변화는 허용하되 경고 기록
                    warnings.append(f"[INFO] 경지 변화 감지: {current_realm} → {value}")

            # 부상(causal_injuries) 검증 - 회복 시 경고
            if key == "causal_injuries" and current_hud:
                current_injury = current_hud.get("causal_injuries", "")
                if current_injury and "중상" in str(current_injury) and "정상" in str(value):
                    warnings.append(f"[WARN] 부상 급회복: {current_injury} → {value} (서사적 근거 필요)")

            # 승인된 업데이트 추가
            applied[key] = value

        # 최종 결과 구성
        is_approved = len(rejected) == 0 or len(applied) > 0

        return {
            "approved": is_approved,
            "applied_updates": applied,
            "rejected_updates": rejected,
            "warnings": warnings
        }

    # =================================================================
    # [V59] 품질 등급화 시스템 (A/B/C Grade)
    # =================================================================

    # [V59] 등급별 기준 정의
    QUALITY_GRADES = {
        'A': {
            'min_score': 85,
            'label': '출판 수준',
            'description': '수정 없이 바로 게재 가능한 수준',
            'action': 'PUBLISH_READY'
        },
        'B': {
            'min_score': 70,
            'label': '게재 가능',
            'description': '경미한 수정 후 게재 가능',
            'action': 'MINOR_REVISION'
        },
        'C': {
            'min_score': 50,
            'label': '수정 필요',
            'description': '상당한 수정 후 재검토 필요',
            'action': 'MAJOR_REVISION'
        },
        'D': {
            'min_score': 0,
            'label': '재작성 필요',
            'description': '근본적인 재작성 필요',
            'action': 'REWRITE'
        }
    }

    # [V59] 품질 항목별 가중치
    QUALITY_WEIGHTS = {
        'structure': 0.20,      # 구조적 완성도
        'prose': 0.20,          # 문장력
        'consistency': 0.25,    # 설정 일관성
        'engagement': 0.20,     # 독자 몰입도
        'commercial': 0.15,     # 상업적 매력
    }

    def grade_manuscript_v59(self, ep_num: int, manuscript: str, validation_result: dict) -> dict:
        """
        [V59] 원고 품질 등급화

        Args:
            ep_num: 에피소드 번호
            manuscript: 원고 텍스트
            validation_result: ValidationOrchestrator 결과

        Returns:
            {
                'grade': 'A' | 'B' | 'C' | 'D',
                'score': float,
                'label': str,
                'breakdown': {...},
                'revision_guide': {...},
                'strengths': [...],
                'weaknesses': [...]
            }
        """
        # 1. 기본 점수 추출
        base_score = validation_result.get('total_score', 0)
        breakdown = validation_result.get('breakdown', {})

        # 2. 세부 점수 분석
        item_scores = {}
        for category, weight in self.QUALITY_WEIGHTS.items():
            # validation_result에서 관련 점수 추출
            related_score = self._extract_category_score(breakdown, category)
            item_scores[category] = {
                'score': related_score,
                'weight': weight,
                'weighted_score': related_score * weight
            }

        # 3. 가중 총점 계산
        weighted_total = sum(item['weighted_score'] for item in item_scores.values())

        # 4. 등급 결정
        grade = 'D'
        for g, criteria in self.QUALITY_GRADES.items():
            if weighted_total >= criteria['min_score']:
                grade = g
                break

        grade_info = self.QUALITY_GRADES[grade]

        # 5. 강점/약점 추출
        strengths = []
        weaknesses = []
        for category, data in item_scores.items():
            if data['score'] >= 80:
                strengths.append({
                    'category': category,
                    'score': data['score'],
                    'note': self._get_strength_description(category)
                })
            elif data['score'] < 60:
                weaknesses.append({
                    'category': category,
                    'score': data['score'],
                    'note': self._get_weakness_description(category)
                })

        # 6. 수정 가이드 생성
        revision_guide = self.generate_revision_guide_v59(
            grade=grade,
            item_scores=item_scores,
            weaknesses=weaknesses,
            validation_result=validation_result
        )

        return {
            'grade': grade,
            'score': round(weighted_total, 1),
            'label': grade_info['label'],
            'description': grade_info['description'],
            'action': grade_info['action'],
            'breakdown': item_scores,
            'revision_guide': revision_guide,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'ep_num': ep_num
        }

    def _extract_category_score(self, breakdown: dict, category: str) -> float:
        """validation breakdown에서 카테고리별 점수 추출"""
        # 카테고리-항목 매핑
        category_mapping = {
            'structure': ['scene_completeness', 'scope_overflow', 'required_scenes'],
            'prose': ['prose_rhythm', 'vocabulary_diversity', 'show_dont_tell'],
            'consistency': ['character_consistency', 'relationship_consistency', 'continuity'],
            'engagement': ['emotion_arc', 'commercial_appeal', 'cliffhanger'],
            'commercial': ['commercial_appeal', 'pattern_diversity'],
        }

        related_items = category_mapping.get(category, [])
        scores = []

        for item_name in related_items:
            if item_name in breakdown:
                item_data = breakdown[item_name]
                if isinstance(item_data, dict):
                    score = item_data.get('score', 0)
                    max_score = item_data.get('max', 1)
                    scores.append((score / max_score) * 100 if max_score > 0 else 0)

        return sum(scores) / len(scores) if scores else 50  # 기본값 50

    def _get_strength_description(self, category: str) -> str:
        """강점 설명 반환"""
        descriptions = {
            'structure': '씬 구성과 전개가 탄탄합니다',
            'prose': '문장력이 유려하고 읽기 좋습니다',
            'consistency': '설정 일관성이 잘 유지됩니다',
            'engagement': '독자 몰입도가 높습니다',
            'commercial': '상업적 매력이 있습니다',
        }
        return descriptions.get(category, '양호한 수준입니다')

    def _get_weakness_description(self, category: str) -> str:
        """약점 설명 반환"""
        descriptions = {
            'structure': '씬 구성이 불균형하거나 누락이 있습니다',
            'prose': '문장이 단조롭거나 묘사가 부족합니다',
            'consistency': '설정 모순이나 불일치가 있습니다',
            'engagement': '독자 몰입을 방해하는 요소가 있습니다',
            'commercial': '상업적 매력 요소가 부족합니다',
        }
        return descriptions.get(category, '개선이 필요합니다')

    # =================================================================
    # [V59] 구체적 수정 가이드 시스템
    # =================================================================

    def generate_revision_guide_v59(self, grade: str, item_scores: dict,
                                     weaknesses: list, validation_result: dict) -> dict:
        """
        [V59] 등급 및 약점 기반 구체적 수정 가이드 생성

        Args:
            grade: 품질 등급 (A/B/C/D)
            item_scores: 항목별 점수
            weaknesses: 약점 목록
            validation_result: 전체 검증 결과

        Returns:
            {
                'priority': str,
                'tasks': [...],
                'examples': [...],
                'estimated_effort': str
            }
        """
        tasks = []
        examples = []

        # 등급별 기본 지침
        if grade == 'D':
            priority = 'CRITICAL'
            tasks.append({
                'type': 'rewrite',
                'description': '원고 전체를 재구성해야 합니다',
                'detail': 'Blueprint를 다시 확인하고 기본 구조부터 재설계하세요'
            })
        elif grade == 'C':
            priority = 'HIGH'
            tasks.append({
                'type': 'major_revision',
                'description': '주요 문제점 수정이 필요합니다',
                'detail': '아래 약점 항목들을 집중 개선하세요'
            })
        elif grade == 'B':
            priority = 'MEDIUM'
            tasks.append({
                'type': 'minor_revision',
                'description': '경미한 수정으로 품질 향상 가능합니다',
                'detail': '아래 제안사항을 참고하여 다듬으세요'
            })
        else:  # A
            priority = 'LOW'
            tasks.append({
                'type': 'polish',
                'description': '최종 교정 수준의 검토만 필요합니다',
                'detail': '오탈자나 미세한 표현 개선 위주로 확인하세요'
            })

        # 약점별 구체적 수정 지침
        for weakness in weaknesses:
            category = weakness.get('category', '')
            score = weakness.get('score', 0)

            revision_task = self._generate_category_revision(category, score, validation_result)
            if revision_task:
                tasks.append(revision_task)

            # 예시 추가
            example = self._get_revision_example(category)
            if example:
                examples.append(example)

        # 노력 수준 추정
        effort_map = {
            'D': '4시간 이상 소요 예상',
            'C': '2-4시간 소요 예상',
            'B': '30분-1시간 소요 예상',
            'A': '15분 내외 소요 예상'
        }

        return {
            'priority': priority,
            'grade': grade,
            'tasks': tasks[:10],  # 최대 10개
            'examples': examples[:5],  # 최대 5개
            'estimated_effort': effort_map.get(grade, '알 수 없음'),
            'focus_areas': [w['category'] for w in weaknesses[:3]]
        }

    def _generate_category_revision(self, category: str, score: float, validation_result: dict) -> dict:
        """카테고리별 수정 지침 생성"""
        revisions = {
            'structure': {
                'type': 'structure_fix',
                'description': '씬 구조 개선',
                'details': [
                    'Blueprint의 6개 씬이 모두 반영되었는지 확인',
                    '각 씬의 분량이 균등하게 배분되었는지 검토',
                    '씬 전환이 자연스러운지 점검'
                ]
            },
            'prose': {
                'type': 'prose_improvement',
                'description': '문장력 향상',
                'details': [
                    '직접 감정 서술("슬펐다") → 묘사로 전환',
                    '문장 시작 패턴 다양화 (연속 3문장 같은 시작 금지)',
                    '감각 묘사 추가 (시각 외 청각, 촉각 등)'
                ]
            },
            'consistency': {
                'type': 'consistency_fix',
                'description': '설정 일관성 수정',
                'details': [
                    '직전 화 엔딩과 현재 화 시작의 연결 확인',
                    'NPC 관계 상태 변화의 정당성 검토',
                    '아이템/무공 사용의 획득 시점 확인'
                ]
            },
            'engagement': {
                'type': 'engagement_boost',
                'description': '몰입도 강화',
                'details': [
                    '감정 전환의 자연스러운 흐름 설계',
                    '긴장감 있는 갈등 요소 추가',
                    'Cliffhanger 엔딩 강화'
                ]
            },
            'commercial': {
                'type': 'commercial_appeal',
                'description': '상업적 매력 강화',
                'details': [
                    '사이다 요소 또는 복선 추가',
                    '다음 화 기대감을 높이는 떡밥 배치',
                    '독자 감정 반응 유발 포인트 삽입'
                ]
            }
        }

        base_revision = revisions.get(category, {})
        if not base_revision:
            return None

        # 점수에 따른 심각도 추가
        if score < 40:
            base_revision['urgency'] = 'CRITICAL'
            base_revision['note'] = '이 항목의 대폭 개선 없이는 게재 불가'
        elif score < 60:
            base_revision['urgency'] = 'HIGH'
            base_revision['note'] = '상당한 수정 필요'
        else:
            base_revision['urgency'] = 'MEDIUM'
            base_revision['note'] = '다듬기 수준의 개선 권장'

        return base_revision

    def _get_revision_example(self, category: str) -> dict:
        """카테고리별 수정 예시"""
        examples = {
            'structure': {
                'before': '갑자기 장면이 전환되어 다른 장소에 있었다.',
                'after': '한참을 걸은 끝에 객잔의 불빛이 눈에 들어왔다. 주인공은 지친 발걸음을 옮겨 문을 밀었다.',
                'note': '장면 전환에 시간/공간의 흐름을 명시'
            },
            'prose': {
                'before': '그는 슬펐다. 정말 슬펐다. 너무 슬펐다.',
                'after': '어깨가 축 처졌다. 주먹이 부들부들 떨렸고, 눈앞이 흐릿해졌다.',
                'note': '감정을 행동/신체 반응으로 묘사'
            },
            'consistency': {
                'before': '(직전 화 부상) → 멀쩡하게 전력 질주했다.',
                'after': '(직전 화 부상) → 부상당한 다리를 끌며 겨우 뛰었다. 통증이 밀려왔지만 멈출 수 없었다.',
                'note': '상태의 연속성 유지'
            },
            'engagement': {
                'before': '무사히 해결되어 잠들었다.',
                'after': '해결된 줄 알았다. 그때, 창문 너머로 낯선 그림자가 스쳐 지나갔다.',
                'note': 'Cliffhanger로 긴장감 유지'
            },
            'commercial': {
                'before': '다음에 또 보자고 인사했다.',
                'after': '"다음에 보자. 그때...내가 숨긴 비밀을 알려주마." 의미심장한 미소가 번졌다.',
                'note': '떡밥/복선으로 기대감 유발'
            }
        }

        return examples.get(category)

    def format_revision_report_v59(self, grade_result: dict) -> str:
        """
        [V59] 수정 가이드를 사람이 읽기 좋은 형태로 포맷

        Args:
            grade_result: grade_manuscript_v59() 결과

        Returns:
            str: 포맷팅된 리포트 텍스트
        """
        lines = [
            f"\n{'='*60}",
            f"📊 [V59] 품질 등급 리포트 - 제{grade_result.get('ep_num', '?')}화",
            f"{'='*60}\n",
        ]

        # 등급 표시
        grade = grade_result.get('grade', '?')
        score = grade_result.get('score', 0)
        label = grade_result.get('label', '')

        grade_emoji = {'A': '🏆', 'B': '✅', 'C': '⚠️', 'D': '❌'}.get(grade, '❓')
        lines.append(f"{grade_emoji} 등급: {grade} ({label})")
        lines.append(f"   점수: {score}/100")
        lines.append(f"   판정: {grade_result.get('description', '')}\n")

        # 강점
        strengths = grade_result.get('strengths', [])
        if strengths:
            lines.append("✨ 강점:")
            for s in strengths[:3]:
                lines.append(f"   - {s['category']}: {s['note']} ({s['score']}점)")
            lines.append("")

        # 약점
        weaknesses = grade_result.get('weaknesses', [])
        if weaknesses:
            lines.append("⚠️ 개선 필요:")
            for w in weaknesses[:3]:
                lines.append(f"   - {w['category']}: {w['note']} ({w['score']}점)")
            lines.append("")

        # 수정 가이드
        revision = grade_result.get('revision_guide', {})
        if revision:
            lines.append(f"📝 수정 가이드 (우선순위: {revision.get('priority', '?')})")
            lines.append(f"   예상 소요: {revision.get('estimated_effort', '?')}")
            lines.append("")

            tasks = revision.get('tasks', [])
            for i, task in enumerate(tasks[:5], 1):
                lines.append(f"   {i}. [{task.get('type', '?')}] {task.get('description', '')}")
                if task.get('details'):
                    for detail in task['details'][:3]:
                        lines.append(f"      - {detail}")

            # 예시
            examples = revision.get('examples', [])
            if examples:
                lines.append("\n📚 수정 예시:")
                for ex in examples[:2]:
                    if ex:
                        lines.append(f"   Before: {ex.get('before', '')[:50]}...")
                        lines.append(f"   After:  {ex.get('after', '')[:50]}...")
                        lines.append(f"   💡 {ex.get('note', '')}")
                        lines.append("")

        lines.append(f"{'='*60}\n")

        return "\n".join(lines)