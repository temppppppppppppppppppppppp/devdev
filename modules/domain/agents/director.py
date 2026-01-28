import json
from .base_agent import BaseAgent



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
   - 특히 '혼철대도'는 Block 15 보상 이전에는 절대 등장하면 안 된다.

### [🚨 유연한 판정 지침 (Pragmatism)]
1. **관대한 승인**: 전술 설계도의 핵심 맥락이 80% 이상 반영되었고 치명적인 설정 오류(예: 죽은 자의 부활, 성별 바뀜 등)가 없다면, 세부 묘사의 미비함은 '수정 지시'만 남기고 [PASS] 판정하라.
2. **요약질 판정 완화**: 결과 중심 서술(그는 승리했다 식)이라 하더라도, 장면의 제목과 핵심 액션이 명확하다면 집필(Writer) 단계에서 충분히 보완이 가능하므로 승인하라.
3. **분량 하한선 조정**: tactical_doc의 전체 텍스트가 한글 기준 1,500자 이상이고 정보 밀도가 충분하다면 [PASS] 처리하라. 기존의 2,000자 기준을 엄격하게 적용하지 않는다.
4. **인과율 밀도 검수 (Causal Anchor Guard)**:
   - 각 장면의 물리적 분량보다 '사건의 전진'이 있는지를 우선하라.
   - 6개의 장면 중 2개 이상이 '단순 묘사'가 아닌, 인물의 심경 변화나 물리적 타격 등 '인과적 전진'이 느껴지는 핵심 키워드를 포함해야 한다.
   - 문장이 길더라도 알맹이가 없는 '중언부언'은 REJECT하되, 문장이 짧더라도 다음 장면으로 넘어가는 '징검다리' 역할이 확실하다면 PASS하라.
   
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
   - **설정 절대 가드 (Hard Constraints)**: 오직 아래 세 가지만 무조건 REJECT하라.
     (A) 주인공의 경지(HUD)를 무시한 초월적 무공명 창조 (예: 삼류인데 이기어검 구사).
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
[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "REJECT",
    "score": 0~100,
    "error_category": "QUALITY_ISSUE" 또는 "LOGIC_ERROR",
    "diagnostic_report": "논리적 모순 발생 시, 정확히 어떤 설정(무기, 인물, 시간)이 충돌했는지 기술",
    "current_beat_achieved": true/false,
    "reason": "판정 근거 (반드시 {audit_mode} 관점에서 서술)",
    "feedback": "증폭/수정을 위한 구체적 지시"
}}
"""

class Director(BaseAgent):
    def audit_manuscript(self, ep_num, manuscript, arc_doc, history_summary, prev_full_text, arc_pos, total_eps=None, target_len=4500, retry_count=0):
        # 1. 검수 모드 자동 결정
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
    

    def audit_strategic_plan(self, arc_plan, prev_arc_context, curr_block=None):
        """[Stage 2] Analyst의 아크 설계안에 대한 전략적 무결성 검수 (루프/미래 오염 방지)"""
        # 🔒 [Hard Guard] 미래 무구 조기 노출 차단
        arc_no = arc_plan.get("arc_no")
        arc_dump = json.dumps(arc_plan, ensure_ascii=False)
        if isinstance(arc_no, int) and arc_no < 15 and "혼철대도" in arc_dump:
            return {
                "decision": "REJECT",
                "score": 0,
                "loop_detected": False,
                "reason": "미래 무구(혼철대도) 조기 등장 감지",
                "re_slice_instruction": "혼철대도/관련 묘사를 전부 제거하고, 현재 시점의 무구로 재설계하라."
            }
        
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
        
        response = self.ask(prompt, temperature=0.1)
        return self._extract_json_robust(response)    

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