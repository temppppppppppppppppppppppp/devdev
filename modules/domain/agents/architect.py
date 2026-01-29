import json
import re
from google.genai import types
from .base_agent import BaseAgent

class Architect(BaseAgent):
    """
    [V37 Sovereign Architect - 0124 Manifesto]
    - 욕망 기반 장면 정렬: 위버의 'short_term_objective'를 설계도의 중심축으로 설정
    - Core/Buffer 밸런싱: 아크별 긴장도 예산에 따라 장면 밀도 강제 조절
    - 무결성 가드: 위버의 목적과 무관한 '지랄(불필요한 서사)' 차단
    """
    def __init__(self, context, client, model_tier="gemini-3-flash-preview"):
        super().__init__(context, client, model_tier)
        self.cache_name = None # main_a.py에서 주입됨

    def _get_hud_trend_safe(self, ep_num: int) -> str:
        """
        [Lightweight Alternative] HUD 추세 안전 호출

        Args:
            ep_num: 에피소드 번호

        Returns:
            str: HUD 추세 또는 에러 메시지
        """
        try:
            if hasattr(self.context, 'sys') and hasattr(self.context.sys, 'hud'):
                return self.context.sys.hud.get_hud_trend(ep_num, window=5)
            elif hasattr(self, 'martial'):  # fallback
                return self.martial.get_hud_trend(ep_num, window=5)
            else:
                return "HUD 추세 정보 없음"
        except Exception:
            return "안정적"

    def design_v20_breakdown(self, ep_num, arc_pos, arc_tactical_doc, martial_hud, encyclopedia, 
                              narrative_context="", tactical_references="", style_guide="", 
                              prev_ms_ending="", surgery_intel="", enrichment_level=0):

        """
        [0124 매니페스토] 위버의 '욕망 엔진' 데이터를 블루프린트에 이식하는 핵심 메서드
        """

        # main_a.py에서 보낸 딕셔너리에서 정보를 추출합니다.
        focus_info = arc_tactical_doc if isinstance(arc_tactical_doc, dict) else {}
        ep_material = focus_info.get("MUST_FOCUS", str(arc_tactical_doc)) # 이번 화 요리 재료
        full_map = focus_info.get("FULL_MAP", "N/A")                    # 참고용 전체 지도
        stop_line = focus_info.get("STOP_LINE", "N/A")                  # 정지선
        # ----------------------------------
        # 1. 위버의 욕망 데이터(Arc Drive) 인출
        # [V45 Fix] arc_tactical_doc이 dict가 아닐 경우 focus_info 사용
        arc_drive = focus_info.get('arc_drive', {})
        objective = arc_drive.get('short_term_objective', "전술적 흐름 유지")
        current_lack = arc_drive.get('current_lack', "결핍 정보 없음")
        pacing = arc_drive.get('pacing_strategy', {})
        pattern_profile = arc_tactical_doc.get('hybrid_composition', {}) if isinstance(arc_tactical_doc, dict) else {}
        pattern_primary = pattern_profile.get('primary', '패턴 정보 없음')
        pattern_secondary = pattern_profile.get('secondary', [])
        pattern_logic = pattern_profile.get('mixing_logic', '')
        
        # 1. [Phase 4] 물리적 제약 조건 및 상태 그림자 인출
        # [V45 Fix] focus_info 사용 (arc_tactical_doc이 dict 아닐 수 있음)
        joint_docs = focus_info.get('joint_docs', {})
        status_shadow = focus_info.get('status_shadow', {})
        is_surgery = focus_info.get('v35_surgery', False)
        

        # 3. [0124 핵심] 목적 중심 설계 지침 강화
        objective_enforcement = f"""
[🚨 MISSION CRITICAL: OBJECTIVE ALIGNMENT]
이번 화는 주인공의 결핍 [{current_lack}]을 해소하기 위한 과정이다.
1. 최종 목적: {objective}
2. 장면 배분 가이드: 전체 6개 장면 중 최소 2개 이상은 위 목적에 직접적으로 기여하는 'Core_Scene'이어야 함.
3. 완급 조절 전략: {pacing.get('core_ratio', '30%')}의 Core 비중 유지 및 긴장도 {pacing.get('tension_limit', 80)} 돌파 금지.
"""

        # 4. [V40 Premium] 감정선 아크 추적 및 단조로움 방지
        emotion_directive = ""
        try:
            from modules.core.emotion_tracker import EmotionArcTracker

            emotion_tracker = EmotionArcTracker(self.context)
            emotion_tracker.load_from_db(self.context.db)

            # 충분한 데이터가 있을 때만 체크 (최소 3화 필요)
            if len(emotion_tracker.history) >= 3:
                # 단조로움 검사 (최근 5화)
                is_monotonous, recommendation = emotion_tracker.check_monotony(last_n_episodes=5)

                # 권장 감정 상태 추출
                recommended_emotion, reasoning = emotion_tracker.get_recommended_emotion_for_next()

                if is_monotonous:
                    # 단조로움 감지 시 강력한 지침 주입
                    emotion_directive = f"""
[🎭 V40 PREMIUM: EMOTION ARC DIRECTIVE - CRITICAL]
{recommendation}

[다음 에피소드 권장 감정]: {recommended_emotion}
[근거]: {reasoning}

이번 에피소드는 반드시 '{recommended_emotion}' 감정을 중심으로 설계하십시오.
특히 웹소설 독자는 3화 이상 동일한 감정 톤이 지속되면 이탈합니다.
장면 설계 시 위 감정 상태를 반영하는 사건/대사/분위기를 반드시 포함하십시오.
"""
                else:
                    # 정상 범위 내에서도 권장 감정 제시
                    emotion_directive = f"""
[🎭 V40 PREMIUM: EMOTION BALANCE]
현재 감정선은 적정 수준이나, 다음 감정 목표를 참고하십시오:
- 권장 감정: {recommended_emotion}
- 근거: {reasoning}
"""
            else:
                # 초반부 (3화 미만)는 감정 추적 스킵
                emotion_directive = "[🎭 V40 PREMIUM: 초반부 감정선 자유 설정 허용]"

        except ImportError as ie:
            print(f"      ⚠️ [Architect] EmotionTracker 모듈 로드 실패: {ie}")
            emotion_directive = ""
        except Exception as e:
            print(f"      ⚠️ [Architect] EmotionTracker 실행 실패: {type(e).__name__}: {e}")
            emotion_directive = ""

        surgery_header = ""
        if surgery_intel:
            surgery_header = f"""
[🚨 과거 설계 실패 사례 기반 교정 지침]
{surgery_intel}
위 내용은 최근 Director에 의해 반려된 실제 사례이다. 
이번 설계에서는 위 오류(인과 붕괴, 설정 오류)를 반복하지 않는 것을 최우선 순위로 하라.
"""

        # 3. [Phase 4] 물리적 불변 법칙 섹션 구성 (구조적 기둥)
        physical_constraints = f"""
[🚨 ABSOLUTE PHYSICAL CONSTRAINTS: 물리적 불변 법칙]
이 데이터는 Analyst에 의해 용접된 확정 팩트이다. 설계를 변경하거나 무시하지 마라.
1. 최종 위치(Final Location): {joint_docs.get('final_location', '이전 아크 상태 계승')}
2. 물리적 소지품(Inventory): {joint_docs.get('physical_inventory', '변동 없음')}
3. 상태 그림자(Status Shadow):
   - 내공 예상 소모량: {status_shadow.get('internal_energy_loss', '정상 범위')}
   - 예상 부상 부위 및 정도: {status_shadow.get('expected_injuries', '무상(無傷)')}
   - 소모 확정 아이템: {status_shadow.get('item_consumption', [])}
4. 세계관 연결점: {joint_docs.get('world_joint', '특이사항 없음')}
"""

        # 4. 설계 재료 확보 및 비트 매핑
        # [V45 Fix] focus_info 사용 (arc_tactical_doc이 dict 아닐 수 있음)
        tactical_blueprint = focus_info.get('tactical_doc') or focus_info.get('strategy_doc', "내용 없음")
        total_arc_eps = int(focus_info.get('ep_count', 5))
        beats = focus_info.get('beat_sequence', [])
        current_beat = str(beats[arc_pos-1]) if 0 < arc_pos <= len(beats) else "전술 설계도의 흐름에 집중하라."
        target_ep_focus = focus_info.get("target_episode_focus", f"[제 {ep_num}화 전술 설계]")
        beat_list = focus_info.get("beat_sequence", [])
        # 이번 화의 핵심 비트를 문자열로 추출
        current_beat_summary = str(current_beat)
        # 5. [V35.5 S-Grade 강화] 수술 모드 지시어 증폭
        surgery_instructions = ""
        if is_surgery:
            surgery_instructions = f"""
[🚨 EMERGENCY SURGERY MODE : 인과율 복구 비상 공정]
현재 에피소드는 서사 붕괴 위기로 인해 Analyst의 '응급 수술'을 받은 상태다. 
아키텍트인 당신은 평소의 지능을 버리고 아래 '수술 수칙'을 광신적으로 따라라:

1. **MasterBible 결착**: 현재 장면의 모든 물리적 충돌(대들보의 무게, 주인공의 악력 등)을 성경의 HUD 수치와 $0.1$의 오차도 없이 일치시켜라.
2. **Causal Anchor**: Analyst가 수술한 '전술서'의 5배 농축된 비트들을 단 하나도 누락하지 마라. 요약하지 말고 비트 사이의 0.1초를 쪼개라.
3. **Logic Shield**: 만약 당신이 설계하려는 내용이 이전의 물리적 제약(부상, 내공 부족)과 충돌한다면, 창의성을 발휘해 '주변 지형지물 이용'이나 '심리적 속임수'로 개연성을 강제 생성하라.
4. **NO CHATTER**: 불필요한 일상 묘사는 삭제한다. 오직 '위기 돌파'와 '인과 용접'에만 모든 토큰을 할당하라.
"""
        pattern_guidance = f"""
[🧩 HYBRID PATTERN GUIDANCE]
1. 주 패턴(Primary): {pattern_primary}
2. 부 패턴(Secondary): {pattern_secondary}
3. 조합 논리(Mixing Logic): {pattern_logic}
4. 최소 2개 장면에서 패턴의 핵심 행위가 드러나야 한다.
"""

        # [Phase 5.2.2] Reflexion: 과거 실패 패턴 주입
        reflexion_prompt = ""
        try:
            # 20화 이후부터 활성화, context 존재 확인
            if ep_num >= 20 and hasattr(self, 'context') and self.context:
                from modules.core.reflexion_manager import ReflexionManager
                reflexion = ReflexionManager(self.context)
                reflexion_prompt = reflexion.get_prompt_injection(min_frequency=2)
        except Exception as e:
            print(f"      ⚠️ [Architect] Reflexion 로드 실패: {e}")
        # [Phase 5.1.1] CoT 구조화 프롬프트
        cot_structure = f"""
{reflexion_prompt}

[🧠 PHASE 5: CHAIN-OF-THOUGHT BLUEPRINT DESIGN]
당신은 5단계 사고 과정을 거쳐 Blueprint를 설계합니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STEP 1] 이전 화 상황 분석
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 제{ep_num-1}화 엔딩: {prev_ms_ending[-200:] if prev_ms_ending else '첫 화'}
- 현재 주인공 상태 요약:
  * 경지: {martial_hud.get('actual_truth', {}).get('realm', '불명')}
  * 내공: {martial_hud.get('actual_truth', {}).get('internal_energy', '불명')}
  * 상태: {martial_hud.get('actual_truth', {}).get('status_tags', [])}
  * [Lightweight] 최근 추세: {self._get_hud_trend_safe(ep_num)}
- 미해결 갈등: {current_lack}
- 전술적 위치: 아크 진행도 {arc_pos}/{total_arc_eps}

[분석 결과] 이번 화는 어떤 상황에서 시작하는가?
→ (주인공의 현재 처지를 한 문장으로 요약)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STEP 2] 갈등 설계
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 이번 화 목적: {objective}
- 핵심 비트: {current_beat_summary[:200]}
- 감정 목표: {emotion_directive[:100] if emotion_directive else '자유 설정'}

[갈등 설계]
1. 이번 화 핵심 갈등: (무엇과 무엇이 충돌하는가?)
2. 갈등 강도: (긴장도 {pacing.get('tension_limit', 80)} 이하 유지)
3. 해결 방식: (완전 해결 / 부분 해결 / 악화)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STEP 3] 장면 배치 전략
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[6개 장면 구조 계획]
- Scene 1-2: (도입부, Buffer 가능)
- Scene 3-4: (갈등 핵심, Core 필수)
- Scene 5-6: (전개 및 절벽걸기)

[Core/Buffer 비율]
- Core 장면 수: 최소 2개 ({pacing.get('core_ratio', '30%')} 비중)
- Buffer 장면: 분위기/맥락 제공

[정지선 확인]
- 이번 화 마지막 장면은 '{stop_line}'이 시작되기 직전에서 멈춤

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STEP 4] 정합성 사전 체크
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[HUD 범위 확인]
- 주인공이 할 수 있는 행동: (경지/내공/장비 기준)
- 주인공이 할 수 없는 행동: (제약 명시)

[NPC 관계 확인]
- 등장 예정 NPC: (이름, 관계 상태)
- 관계 전환 가능 여부: (경외→무시 같은 역행 금지)

[미래 누수 방지]
- '{stop_line}' 이후 내용을 미리 쓰지 않았는가?
- 다른 화의 비트를 가져오지 않았는가?

[물리적 제약]
- 최종 위치: {joint_docs.get('final_location', '이전 상태 계승') if joint_docs else '확인 필요'}
- 소지품: {joint_docs.get('physical_inventory', '변동 없음') if joint_docs else '확인 필요'}
- 예상 부상: {status_shadow.get('expected_injuries', '무상') if status_shadow else '확인 필요'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STEP 5] 최종 Blueprint 작성
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
위 4단계 분석을 바탕으로 최종 Blueprint JSON 작성
- 6개 장면을 각각 300-500자로 상세 설계
- integrated_scenario는 3000자+ 고해상도 시나리오
"""

        dynamic_prompt = f"""
        {cot_structure}

        [🚨 FINAL CHECKPOINT: 당신의 목숨줄이다]
        1. 당신은 창작자가 아니라 '설계 구현자'다. 상위 설계도(Tactical Doc)에 명시된 인물 이름(예: 팽조명)을 단 한 글자라도 바꾸면 즉시 파기된다.
        2. 모든 비트(Beat 1~3)를 반드시 Scene 1~6 사이에 골고루 배분하라. 특히 핵심 장면 누락은 절대 용납하지 않는다.

        {surgery_header}
        {emotion_directive}
        {physical_constraints}
        {surgery_instructions}
        {pattern_guidance}
        
        ### [🚨 시야 고정 및 페이싱 지침]
        1. **집중 구역**: 당신은 현재 [제 {ep_num}화]를 설계 중이다. 반드시 아래 '에피소드 재료'에만 집중하라.
           - 에피소드 재료: {ep_material}

        2. **맥락 참고**: 아래 '전체 로드맵'은 인과율 유지를 위한 참고용이다. 절대 이 내용을 끌어다 쓰지 마라.
           - 전체 로드맵: {full_map}

        3. **물리적 정지선**: 이번 화의 마지막 장면(Scene 6)은 반드시 아래 사건이 시작되기 직전에서 멈춰야 한다.
           - 다음 화 예고(정지선): {stop_line}

        4. **밀도 최우선**: 미래의 사건을 가져와서 지면을 채우는 행위는 금지된다. 대신 현재 장면의 오감(질감), 인과(0.1초 단위), 파동(주변 반응)을 극한으로 서술하여 2,000자 이상의 밀도를 확보하라.
        [🚨 SEARCH & EXTRACT MISSION]
        1. 아래 '상위 아크 전술 설계도'에서 **[제 {ep_num}화 전술 설계]**라고 명시된 섹션을 찾아라.
        2. 오직 해당 섹션에 적힌 '전술 비트'만을 사용하여 6개의 상세 장면을 설계하라.
        3. 다른 화(Section)의 내용을 미리 가져오는 행위는 '서사 붕괴'로 간주하여 즉시 반려(REJECT)한다.
        
        [MISSION: Episode {ep_num} Breakdown Design]
        [TASK] 제 {ep_num}화의 초정밀 시나리오를 설계하라.

        ### 🎯 1. 이번 화 실행 미션 (Pacing: {arc_pos}/{total_arc_eps})
        - 비트: {self._escape_braces(current_beat)}

        ### 📜 2. 상위 아크 전술 설계도 (Tactical Context)
        {self._escape_braces(tactical_blueprint)}

        ### 🛡️ 3. 서사 무결성 데이터 (Fact Check)
        - 주인공 실시간 HUD: {self._escape_braces(json.dumps(martial_hud, ensure_ascii=False))}
        - 직전 화 실제 엔딩: "...{self._escape_braces(prev_ms_ending)}"
        - 최근 서사 맥락 요약: {self._escape_braces(narrative_context)}
        - 세계관 백과사전 참조: {self._escape_braces(json.dumps(encyclopedia, ensure_ascii=False))}
        - 최근 수술 기록/맥락: {self._escape_braces(surgery_intel)} {self._escape_braces(narrative_context)}
        
        ### 🎨 4. 스타일 및 전술 참조
        - 스타일 가이드: {self._escape_braces(style_guide)}
        - 기술적 참조 리포트: {self._escape_braces(tactical_references)}
        
        [🚨 Enrichment Level: {enrichment_level}] {f"(강화 지침 반영 요망)" if enrichment_level > 0 else ""}

        ### ⚠️ 출력 형식 (Strict JSON Only)
        {{
            "ep_num": {ep_num},
            "title": "에피소드 제목",
            "scene_breakdown": {{
                "scene_1": "[Buffer]: 묘사 내용...",
                "scene_2": "[Core]: {objective}를 향한 직접적 행동...",
                "scene_3": "[Core]: 묘사 내용...",
                "scene_4": "[Buffer]: 묘사 내용...",
                "scene_5": "[Buffer]: 묘사 내용...",
                "scene_6": "[Cliffhanger]: 다음 화 유도..."
            }},
            "integrated_scenario": "3,000자 이상의 고해상도 시나리오 (6개 장면의 모든 대사와 상황을 물 흐르듯 연결)"
        }}
        """

        # 6. [API 호출] 캐시 유무에 따른 분기 처리 (기능 저하 없음)
        try:
            if self.cache_name:
                response = self.client.models.generate_content(
                    model=self.primary_model,
                    contents=dynamic_prompt,
                    config=types.GenerateContentConfig(
                        cached_content=self.cache_name,
                        temperature=0.4,
                        response_mime_type="application/json"
                    )
                )
                return self._extract_json_robust(response.text)
            else:
                return self._fallback_full_request(dynamic_prompt)
        except Exception as e:
            print(f"      🚨 [Architect Error] 설계 공정 중단: {e}")
            return self._fallback_full_request(dynamic_prompt)

    def _fallback_full_request(self, dynamic_prompt):
        """[V31.5 Fallback] 캐시 실패 시 로컬 규칙 파일을 직접 읽어 전체 프롬프트 재구성"""
        try:
            rules_path = self.context.paths.config / "prompts" / "architect_rules.json"
            full_context = "[SYSTEM: ARCHITECT STRUCTURAL RULES - FULL LOAD]\n"
            
            if rules_path.exists():
                rule_data = json.loads(rules_path.read_text(encoding='utf-8'))
                full_context += json.dumps(rule_data, ensure_ascii=False, indent=2)
            
            full_prompt = f"{full_context}\n\n{dynamic_prompt}"
            # 일반 API 호출 수행
            raw_res = self.ask(full_prompt, temperature=0.4)
            return self._extract_json_robust(raw_res)
            
        except Exception as e:
            print(f"      ❌ [Architect] Fallback 구성 중 치명적 오류: {e}")
            # 최후의 수단으로 지시서만이라도 전송
            return self._extract_json_robust(self.ask(dynamic_prompt, temperature=0.4))