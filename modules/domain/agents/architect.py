import json
import re
from google.genai import types
from .base_agent import BaseAgent

class Architect(BaseAgent):
    """
    [V48 Sovereign Architect - 0130 Manifesto]
    - 욕망 기반 장면 정렬: 위버의 'short_term_objective'를 설계도의 중심축으로 설정
    - Core/Buffer 밸런싱: 아크별 긴장도 예산에 따라 장면 밀도 강제 조절
    - 무결성 가드: 위버의 목적과 무관한 '지랄(불필요한 서사)' 차단
    - [V48 NEW] 이전 블루프린트 컨텍스트 주입: 연속성 사전 확보
    - [V59] 긴장도 곡선 분석 및 자동 씬 밸런싱
    """
    def __init__(self, context, client, model_tier="gemini-3-flash-preview"):
        super().__init__(context, client, model_tier)
        self.cache_name = None # main_a.py에서 주입됨
        self.prev_blueprints_context = ""  # [V48] 이전 블루프린트 요약

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

    def load_prev_blueprints_context(self, ep_num: int, window: int = 15) -> str:
        """
        [V48] 이전 블루프린트 요약 로드 및 캐싱
        [V60] 윈도우 5→10화 확장, 아이템 추출 정밀화, 중복 획득 경고 강화
        [V60.9] 윈도우 10→15화 확장, 장기 아이템/NPC 추적 강화

        Args:
            ep_num: 현재 에피소드 번호
            window: 조회할 이전 에피소드 수 (V60.9: 기본 15화)

        Returns:
            str: 이전 블루프린트 요약 (프롬프트용)
        """
        if ep_num <= 1:
            return ""
        
        try:
            prev_summaries = []
            acquired_items = []
            granted_items = []
            
            for prev_ep in range(max(1, ep_num - window), ep_num):
                bp = self.context.get_blueprint(prev_ep)
                if bp and isinstance(bp, dict):
                    scenario = bp.get('integrated_scenario', '')
                    
                    # 핵심 정보 추출
                    items = self._extract_acquisitions(scenario)
                    grants = self._extract_grants(scenario)
                    
                    if items:
                        acquired_items.extend([(prev_ep, item) for item in items])
                    if grants:
                        granted_items.extend([(prev_ep, grant) for grant in grants])
                    
                    # 엔딩 요약 (마지막 500자)
                    ending = scenario[-500:] if len(scenario) > 500 else scenario
                    prev_summaries.append(f"[제{prev_ep}화 엔딩] {ending[:300]}...")
            
            # 연속성 컨텍스트 구성
            context_parts = []
            
            if acquired_items:
                items_str = ", ".join([f"'{item}'(제{ep}화)" for ep, item in acquired_items[-5:]])
                context_parts.append(f"[이미 획득한 아이템] {items_str}")
            
            if granted_items:
                grants_str = ", ".join([f"'{grant}'(제{ep}화)" for ep, grant in granted_items[-3:]])
                context_parts.append(f"[이미 수여받은 것] {grants_str}")
            
            if prev_summaries:
                context_parts.append(f"[최근 에피소드 엔딩]\n" + "\n".join(prev_summaries[-2:]))
            
            self.prev_blueprints_context = "\n".join(context_parts)
            return self.prev_blueprints_context
            
        except Exception as e:
            print(f"      ⚠️ [Architect] 이전 블루프린트 로드 실패: {e}")
            return ""
    
    def _extract_acquisitions(self, scenario: str) -> list:
        """
        [V60 Enhanced] 시나리오에서 획득 아이템 정밀 추출

        오탐 방지:
        - 일반 동작 필터링 (펼쳤다, 꺼냈다 등은 제외)
        - 길이 필터 (2-15자)
        - 불용어 필터
        """
        # 획득 확정 패턴 (소유권 이전 명확)
        acquisition_patterns = [
            (r'(.+?)(?:을|를)\s*(?:획득|소유|얻|받)', 'acquire'),
            (r'(.+?)(?:을|를)\s*(?:집어\s*들|뽑아\s*들|주워\s*들|낚아\s*챔)', 'pickup'),
            (r'(.+?)(?:을|를)\s*(?:가져가|챙겨\s*들|손에\s*넣)', 'take'),
            (r'(?:전달받|하사받|넘겨받|지급받).*?(.+?)(?:을|를)', 'receive'),
        ]

        # 오탐 방지: 일반 동작 (소유권 이전 아님)
        false_positive_patterns = [
            r'펼치|꺼내|열어|들여다|바라보|확인|살펴',
        ]

        # 불용어 (아이템이 아닌 것)
        stopwords = {'것', '이것', '그것', '저것', '무엇', '뭔가', '모든', '여러', '각종',
                    '손', '발', '눈', '입', '말', '몸', '마음', '생각', '기억', '힘',
                    '그', '이', '저', '그녀', '그들', '자신', '상대'}

        items = []
        for pattern, source_type in acquisition_patterns:
            matches = re.findall(pattern, scenario)
            for item in matches:
                item = item.strip()

                # 길이 필터 (2-15자)
                if not (2 <= len(item) <= 15):
                    continue

                # 불용어 필터
                if item in stopwords:
                    continue

                # 오탐 필터: 해당 문장에 일반 동작 패턴이 있으면 제외
                item_context = scenario[max(0, scenario.find(item)-30):scenario.find(item)+30]
                is_false_positive = any(re.search(fp, item_context) for fp in false_positive_patterns)
                if is_false_positive:
                    continue

                items.append(item)

        return list(set(items))[:8]  # 중복 제거, 최대 8개 (V60: 5→8)
    
    def _extract_grants(self, scenario: str) -> list:
        """시나리오에서 수여물 추출"""
        patterns = [
            r"(.+?)(?:을|를)\s*(?:하사|수여|내리|던져\s*주)",
            r"(?:형법\s*집행권|사자패|옥패|금패)",
        ]
        grants = []
        for pattern in patterns:
            matches = re.findall(pattern, scenario)
            for grant in matches:
                grant = grant.strip() if isinstance(grant, str) else str(grant)
                if grant and 2 <= len(grant) <= 20:
                    grants.append(grant)
        return list(set(grants))[:3]

    def load_semantic_context(self, ep_num: int, current_scenario: str = "") -> str:
        """
        [V49.3] Semantic RAG를 통한 관련 Blueprint 검색

        시간 순서가 아닌 의미적 유사성으로 관련 Blueprint를 찾아
        연속성 컨텍스트를 보강합니다.

        Args:
            ep_num: 현재 에피소드 번호
            current_scenario: 현재 설계하려는 시나리오 (쿼리용)

        Returns:
            str: 시맨틱 컨텍스트 프롬프트
        """
        try:
            from modules.core.blueprint_memory import BlueprintMemory

            # BlueprintMemory 초기화
            bp_memory = BlueprintMemory(self.context)
            if not bp_memory.initialized:
                return ""

            # 쿼리 텍스트 결정
            query = current_scenario[:500] if current_scenario else ""
            if not query:
                # 현재 설계하려는 아크 전술서에서 쿼리 추출
                if hasattr(self, 'prev_blueprints_context') and self.prev_blueprints_context:
                    query = self.prev_blueprints_context[:500]
                else:
                    return ""

            # 관련 Blueprint 검색 (현재 에피소드 제외)
            exclude_list = list(range(max(1, ep_num - 3), ep_num + 1))  # 최근 3화 제외
            related_bps = bp_memory.search_related(
                query=query,
                n_results=5,
                exclude_eps=exclude_list
            )

            if not related_bps:
                return ""

            # 프롬프트 생성
            return bp_memory.generate_context_prompt(related_bps)

        except ImportError:
            return ""
        except Exception as e:
            print(f"      ⚠️ [Architect] Semantic RAG 실패: {e}")
            return ""

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
        

        # [V60.88] 주인공 설정 추출 (context에서 master_bible 접근)
        protagonist_config_section = ""
        try:
            master_bible = getattr(self.context, 'master_bible', {})
            if master_bible:
                bible_root = master_bible.get('MasterBible', master_bible)
                protagonist_config = bible_root.get('protagonist_config', {})
                world_origin = protagonist_config.get('world_origin', '원시인')
                incarnation_type = protagonist_config.get('incarnation_type', '회귀자')

                protagonist_instructions = []
                if world_origin == '원시인':
                    protagonist_instructions.append('⚠️ 현대 용어 완전 금지 (킬로그램, 아드레날린 등)')
                else:
                    protagonist_instructions.append('📝 주인공은 현대 사회를 알고 있음')
                if incarnation_type == '회귀자':
                    protagonist_instructions.append('🔄 미래를 알고 있음 (합리적 이유 없이는 내면 독백으로 처리)')
                elif incarnation_type == '빙의자':
                    protagonist_instructions.append('👤 원래 인물의 기억/관계를 의식')
                elif incarnation_type == '환생자':
                    protagonist_instructions.append('👶 전생의 기억이 있음')

                if protagonist_instructions:
                    protagonist_config_section = f"""
[🌍 V60.88 주인공 설정]
- 세계 출신: {world_origin}
- 환생 유형: {incarnation_type}
{chr(10).join(protagonist_instructions)}
"""
        except Exception:
            pass  # 실패 시 무시

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

        # [V48] 이전 블루프린트 연속성 컨텍스트 로드
        # [V60.9] 윈도우 5→15화 확장 (장기 아이템/NPC 추적)
        continuity_context = ""
        try:
            if ep_num > 1:
                continuity_context = self.load_prev_blueprints_context(ep_num, window=15)
        except Exception as e:
            print(f"      ⚠️ [Architect] 연속성 컨텍스트 로드 실패: {e}")
        
        # [V48] 연속성 경고 섹션
        continuity_warning = ""
        if continuity_context:
            continuity_warning = f"""
[🚨 V48 CONTINUITY GUARD: 연속성 필수 준수 사항]
아래는 이전 에피소드에서 이미 발생한 사건입니다. 절대 중복하지 마십시오.

{continuity_context}

⚠️ 위에 나열된 아이템을 다시 획득하는 장면을 작성하지 마십시오.
⚠️ 위에 나열된 수여물을 수여 전 에피소드에서 소지하고 있는 것으로 쓰지 마십시오.
⚠️ 이미 획득한 것은 '소지 중'인 상태로, 이미 수여받은 것은 '보유 중'인 상태로 시작하십시오.
"""
        # [Phase 5.1.1] CoT 구조화 프롬프트
        cot_structure = f"""
{reflexion_prompt}
{continuity_warning}

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
        {protagonist_config_section}
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
            "integrated_scenario": "3,000자 이상의 고해상도 시나리오",
            "time_flow": "이전 화 대비 시간 흐름 (예: 같은 날 밤, 다음 날 아침, 3일 후)",
            "relationship_changes": [
                {{"target": "변화 대상(NPC/집단)", "from_state": "이전 관계", "to_state": "변화 후 관계", "justification": "변화 근거 (어떤 사건으로?)"}}
            ],
            "item_movements": {{
                "scene_1": {{"acquired": [], "used": [], "lost": []}},
                "scene_2": {{"acquired": ["대도 획득"], "used": [], "lost": []}},
                "scene_3": {{"acquired": [], "used": ["회복단 사용"], "lost": []}},
                "scene_4": {{"acquired": [], "used": [], "lost": []}},
                "scene_5": {{"acquired": ["비급 발견"], "used": [], "lost": []}},
                "scene_6": {{"acquired": [], "used": [], "lost": []}}
            }},
            "inventory_snapshot": {{
                "start": ["이전 화 종료 시점 소지품"],
                "end": ["이번 화 종료 시점 소지품"]
            }}
        }}

        ※ relationship_changes 규칙:
        - 2단계 이상 점프 금지 (무시→충성 X, 무시→경외→충성 O)
        - 허용 전환: 멸시→무시/의심, 무시→의심/경외, 의심→경외, 경외→충성
        - 점프 시 반드시 justification에 구체적 사건 명시

        ※ [V57] item_movements 규칙:
        - 각 씬에서 발생하는 아이템 변동을 명시
        - acquired: 해당 씬에서 새로 획득한 아이템
        - used: 해당 씬에서 사용/소모한 아이템
        - lost: 해당 씬에서 잃어버린/파괴된 아이템
        - inventory_snapshot.end는 시작 + 획득 - 소모/손실로 계산
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
                result = self._extract_json_robust(response.text)
                # [V47] 블루프린트 구조 검증
                return self._validate_blueprint_structure(result, ep_num)
            else:
                result = self._fallback_full_request(dynamic_prompt)
                return self._validate_blueprint_structure(result, ep_num)
        except Exception as e:
            print(f"      🚨 [Architect Error] 설계 공정 중단: {e}")
            result = self._fallback_full_request(dynamic_prompt)
            return self._validate_blueprint_structure(result, ep_num)

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

    def _validate_blueprint_structure(self, blueprint: dict, ep_num: int) -> dict:
        """
        [V57] 블루프린트 구조 검증 및 보완
        [V60] 최소 Scene 기준 4→6개 상향, 부족 시 자동 생성
        - scene_breakdown에 최소 6개 scene 필요 (V60)
        - 필수 필드 존재 여부 확인
        - [V57] item_movements 일관성 검증
        """
        if not blueprint or not isinstance(blueprint, dict):
            print(f"      ⚠️ [Architect] 블루프린트 구조 오류 - 빈 응답")
            return {"ep_num": ep_num, "validation_failed": True, "scene_breakdown": {}}

        # 필수 필드 검증
        required_fields = ['scene_breakdown', 'integrated_scenario']
        missing_fields = [f for f in required_fields if f not in blueprint]
        if missing_fields:
            print(f"      ⚠️ [Architect] 필수 필드 누락: {missing_fields}")
            blueprint['validation_warning'] = f"missing_fields: {missing_fields}"

        # [V60] scene_breakdown 검증 (최소 6개 요구)
        scene_breakdown = blueprint.get('scene_breakdown', {})
        MIN_SCENES = 6  # V60: 4→6 상향

        if isinstance(scene_breakdown, dict):
            scene_count = len([k for k in scene_breakdown.keys() if k.startswith('scene') or k.startswith('Scene')])
            if scene_count < MIN_SCENES:
                print(f"      ⚠️ [V60] Scene 부족 ({scene_count}/{MIN_SCENES}) - 자동 생성 시도")
                blueprint = self._auto_generate_missing_scenes_v60(blueprint, MIN_SCENES)
                blueprint['validation_warning'] = f"auto_generated_scenes: {MIN_SCENES - scene_count}"
        elif isinstance(scene_breakdown, str):
            # scene_breakdown이 문자열로 왔을 때 복구 시도
            print(f"      ⚠️ [Architect] scene_breakdown이 문자열 - dict 변환 + 자동 생성")
            blueprint['scene_breakdown'] = {"scene_1": scene_breakdown}
            blueprint = self._auto_generate_missing_scenes_v60(blueprint, MIN_SCENES)
            blueprint['validation_warning'] = "scene_breakdown_was_string_and_generated"

        # [V57] item_movements 검증 및 보완
        item_movements = blueprint.get('item_movements', {})
        if not item_movements or not isinstance(item_movements, dict):
            # item_movements 자동 생성
            blueprint['item_movements'] = self._generate_item_movements_from_scenario(blueprint)
            print(f"      [V57] item_movements 자동 생성됨")
        else:
            # item_movements 일관성 검증
            validation_result = self._validate_item_movements(item_movements, blueprint)
            if validation_result.get('warnings'):
                for warn in validation_result['warnings']:
                    print(f"      ⚠️ [V57] {warn}")
                blueprint['item_movement_warnings'] = validation_result['warnings']

        # [V57] inventory_snapshot 보완
        if 'inventory_snapshot' not in blueprint:
            blueprint['inventory_snapshot'] = self._compute_inventory_snapshot(blueprint)

        # ep_num 강제 설정
        blueprint['ep_num'] = ep_num

        return blueprint

    def _auto_generate_missing_scenes_v60(self, blueprint: dict, target_count: int = 6) -> dict:
        """
        [V60] 부족한 Scene 자동 생성

        기존 씬의 내용을 분석하여 누락된 씬을 추론적으로 생성합니다.
        Buffer/Transition 씬 위주로 자동 생성됩니다.

        Args:
            blueprint: 원본 블루프린트
            target_count: 목표 씬 개수

        Returns:
            보완된 블루프린트
        """
        scene_breakdown = blueprint.get('scene_breakdown', {})
        if not isinstance(scene_breakdown, dict):
            scene_breakdown = {}

        current_count = len([k for k in scene_breakdown.keys() if k.startswith('scene') or k.startswith('Scene')])

        if current_count >= target_count:
            return blueprint

        # 기존 씬에서 컨텍스트 추출
        existing_scenes = list(scene_breakdown.values())
        last_scene_content = existing_scenes[-1] if existing_scenes else ""

        # 씬 타입 패턴
        scene_type_rotation = ['Buffer', 'Core', 'Buffer', 'Core', 'Buffer', 'Cliffhanger']

        # 부족한 씬 자동 생성
        for i in range(current_count + 1, target_count + 1):
            scene_type = scene_type_rotation[(i - 1) % len(scene_type_rotation)]

            if scene_type == 'Buffer':
                auto_content = f"[{scene_type}]: (V60 자동 생성) 전환 씬 - 이전 장면의 여운을 정리하고 다음 전개를 준비하는 장면. 상세 내용은 Writer 단계에서 확장 필요."
            elif scene_type == 'Core':
                auto_content = f"[{scene_type}]: (V60 자동 생성) 핵심 씬 - 에피소드의 주요 갈등/사건을 전개하는 장면. 상세 내용은 Writer 단계에서 확장 필요."
            else:  # Cliffhanger
                auto_content = f"[{scene_type}]: (V60 자동 생성) 클리프행어 - 긴장감 있는 엔딩으로 다음 화에 대한 기대를 유발하는 장면. 상세 내용은 Writer 단계에서 확장 필요."

            scene_breakdown[f'scene_{i}'] = auto_content

        blueprint['scene_breakdown'] = scene_breakdown
        blueprint['v60_auto_generated_scenes'] = target_count - current_count

        print(f"      🔧 [V60] {target_count - current_count}개 씬 자동 생성 완료 (총 {target_count}개)")

        return blueprint

    def _generate_item_movements_from_scenario(self, blueprint: dict) -> dict:
        """
        [V57] integrated_scenario에서 item_movements 자동 추출
        """
        scenario = blueprint.get('integrated_scenario', '')
        scene_breakdown = blueprint.get('scene_breakdown', {})

        movements = {}

        # 씬별로 아이템 이동 추출
        for scene_key in scene_breakdown.keys():
            scene_content = scene_breakdown.get(scene_key, '')
            if not isinstance(scene_content, str):
                scene_content = str(scene_content)

            movements[scene_key] = {
                "acquired": self._extract_acquisitions(scene_content),
                "used": self._extract_item_usage(scene_content),
                "lost": self._extract_item_loss(scene_content)
            }

        return movements

    def _extract_item_usage(self, text: str) -> list:
        """텍스트에서 아이템 사용/소모 추출"""
        patterns = [
            r"(.+?)(?:을|를)\s*(?:사용|복용|먹|마시|소모|꺼내|써)",
            r"(.+?)(?:으로|로)\s*(?:치료|회복|수련)",
        ]
        items = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for item in matches:
                item = item.strip()
                if item and 2 <= len(item) <= 15:
                    items.append(item)
        return list(set(items))[:3]

    def _extract_item_loss(self, text: str) -> list:
        """텍스트에서 아이템 손실/파괴 추출"""
        patterns = [
            r"(.+?)(?:이|가)\s*(?:부러지|깨지|파괴|망가지|잃어버리|빼앗|도난)",
            r"(.+?)(?:을|를)\s*(?:잃|빼앗기|떨어뜨)",
        ]
        items = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for item in matches:
                item = item.strip()
                if item and 2 <= len(item) <= 15:
                    items.append(item)
        return list(set(items))[:3]

    def _validate_item_movements(self, item_movements: dict, blueprint: dict) -> dict:
        """
        [V57] item_movements 일관성 검증

        검증 항목:
        1. 획득 전 사용 방지
        2. 중복 획득 방지
        3. inventory_snapshot과의 일관성
        """
        result = {"valid": True, "warnings": []}

        # 누적 인벤토리 추적
        inventory = set()
        inventory_snapshot = blueprint.get('inventory_snapshot', {})
        start_items = inventory_snapshot.get('start', [])
        if isinstance(start_items, list):
            inventory.update(start_items)

        all_acquired = []
        all_used = []
        all_lost = []

        for scene_key in sorted(item_movements.keys()):
            movements = item_movements.get(scene_key, {})
            if not isinstance(movements, dict):
                continue

            acquired = movements.get('acquired', [])
            used = movements.get('used', [])
            lost = movements.get('lost', [])

            # 획득 전 사용 검증
            for item in used:
                if item not in inventory and item not in all_acquired:
                    result['warnings'].append(
                        f"{scene_key}: '{item}' 사용 - 미획득 아이템"
                    )

            # 중복 획득 검증
            for item in acquired:
                if item in all_acquired:
                    result['warnings'].append(
                        f"{scene_key}: '{item}' 중복 획득"
                    )

            all_acquired.extend(acquired)
            all_used.extend(used)
            all_lost.extend(lost)

            # 인벤토리 업데이트
            inventory.update(acquired)
            for item in used + lost:
                inventory.discard(item)

        if result['warnings']:
            result['valid'] = False

        return result

    def _compute_inventory_snapshot(self, blueprint: dict) -> dict:
        """
        [V57] item_movements 기반 inventory_snapshot 계산
        """
        item_movements = blueprint.get('item_movements', {})

        # 이전 화 정보에서 시작 인벤토리 추출
        start_inventory = []
        if hasattr(self, 'prev_blueprints_context') and self.prev_blueprints_context:
            # 이미 획득한 아이템 섹션에서 추출
            import re
            match = re.search(r'\[이미 획득한 아이템\]\s*(.+?)(?:\n|$)', self.prev_blueprints_context)
            if match:
                items_str = match.group(1)
                items = re.findall(r"'([^']+)'", items_str)
                start_inventory = items[:10]  # 최대 10개

        # 종료 인벤토리 계산
        end_inventory = set(start_inventory)

        for scene_key in sorted(item_movements.keys()):
            movements = item_movements.get(scene_key, {})
            if not isinstance(movements, dict):
                continue

            acquired = movements.get('acquired', [])
            used = movements.get('used', [])
            lost = movements.get('lost', [])

            end_inventory.update(acquired)
            for item in used + lost:
                end_inventory.discard(item)

        return {
            "start": start_inventory,
            "end": list(end_inventory)
        }

    # ========================================================================
    # [V59] 긴장도 곡선 시스템
    # ========================================================================

    # [V59] 씬 유형별 기본 긴장도
    SCENE_TYPE_TENSION = {
        'buffer': {'base': 30, 'range': (20, 40)},
        'core': {'base': 70, 'range': (60, 85)},
        'cliffhanger': {'base': 80, 'range': (70, 95)},
        'dialogue': {'base': 40, 'range': (30, 55)},
        'action': {'base': 75, 'range': (65, 90)},
        'discovery': {'base': 55, 'range': (45, 70)},
        'training': {'base': 45, 'range': (35, 60)},
        'crisis': {'base': 85, 'range': (75, 100)},
    }

    # [V59] 장르별 권장 긴장도 패턴
    GENRE_TENSION_PATTERNS = {
        'wuxia': {
            'standard': [30, 45, 65, 75, 60, 85],  # 점진적 상승 + 클리프
            'training': [40, 55, 50, 65, 70, 55],  # 수련 에피소드
            'crisis': [60, 75, 85, 90, 70, 95],     # 위기 에피소드
        },
        'hunter': {
            'dungeon': [50, 60, 75, 85, 65, 90],   # 던전 공략
            'growth': [35, 50, 60, 55, 70, 75],    # 성장 에피소드
            'boss': [55, 70, 80, 90, 75, 95],      # 보스전
        },
        'investment': {
            'analysis': [35, 45, 55, 50, 60, 70],  # 분석/준비
            'trade': [45, 60, 75, 80, 65, 85],     # 거래 실행
            'crisis': [70, 80, 90, 85, 75, 95],    # 시장 위기
        }
    }

    def analyze_tension_curve(self, blueprint: dict, genre: str = 'wuxia') -> dict:
        """
        [V59] Blueprint의 긴장도 곡선 분석

        Args:
            blueprint: 블루프린트
            genre: 장르

        Returns:
            {
                'scene_tensions': [{'scene': 'scene_1', 'tension': 35, 'type': 'buffer'}, ...],
                'curve_shape': 'ascending' | 'descending' | 'plateau' | 'wave',
                'climax_scene': 4,
                'average_tension': 55.5,
                'tension_variance': 18.2,
                'recommendations': [...]
            }
        """
        scene_breakdown = blueprint.get('scene_breakdown', {})
        if not scene_breakdown:
            return {'error': 'No scene breakdown', 'scene_tensions': []}

        scene_tensions = []

        for scene_key in sorted(scene_breakdown.keys()):
            scene_content = scene_breakdown.get(scene_key, '')
            if not isinstance(scene_content, str):
                scene_content = str(scene_content)

            # 씬 유형 감지
            scene_type = self._detect_scene_type(scene_content)

            # 긴장도 계산
            tension = self._calculate_scene_tension(scene_content, scene_type, genre)

            scene_tensions.append({
                'scene': scene_key,
                'type': scene_type,
                'tension': tension,
                'content_preview': scene_content[:100]
            })

        # 곡선 형태 분석
        tensions = [s['tension'] for s in scene_tensions]
        curve_shape = self._analyze_curve_shape(tensions)

        # 클라이맥스 찾기
        max_tension = max(tensions) if tensions else 0
        climax_scene = tensions.index(max_tension) + 1 if tensions else 1

        # 통계
        avg_tension = sum(tensions) / len(tensions) if tensions else 0
        variance = sum((t - avg_tension) ** 2 for t in tensions) / len(tensions) if tensions else 0

        # 권장 사항 생성
        recommendations = self._generate_tension_recommendations(
            scene_tensions, curve_shape, genre
        )

        return {
            'scene_tensions': scene_tensions,
            'curve_shape': curve_shape,
            'climax_scene': climax_scene,
            'average_tension': round(avg_tension, 1),
            'tension_variance': round(variance ** 0.5, 1),
            'recommended_pattern': self._get_recommended_pattern(genre, curve_shape),
            'recommendations': recommendations
        }

    def _detect_scene_type(self, content: str) -> str:
        """씬 유형 감지"""
        content_lower = content.lower()

        type_keywords = {
            'cliffhanger': ['cliffhanger', '절벽', '급전환', '돌연', '그때'],
            'core': ['core', '핵심', '중심', '주요', '목표 달성'],
            'buffer': ['buffer', '완충', '분위기', '일상'],
            'action': ['전투', '격돌', '공격', '방어', '결투'],
            'dialogue': ['대화', '협상', '설득', '정보 수집'],
            'discovery': ['발견', '비밀', '진실', '단서'],
            'training': ['수련', '연마', '깨달음', '경지'],
            'crisis': ['위기', '절체절명', '궁지', '함정'],
        }

        for scene_type, keywords in type_keywords.items():
            if any(kw in content_lower for kw in keywords):
                return scene_type

        return 'buffer'  # 기본값

    def _calculate_scene_tension(self, content: str, scene_type: str, genre: str) -> int:
        """씬 긴장도 계산"""
        type_info = self.SCENE_TYPE_TENSION.get(scene_type, self.SCENE_TYPE_TENSION['buffer'])
        base_tension = type_info['base']
        min_t, max_t = type_info['range']

        # 콘텐츠 기반 조정
        adjustments = 0

        # 긴장 키워드
        tension_keywords = ['위기', '급박', '공격', '도망', '추격', '죽음', '피', '부상']
        tension_count = sum(1 for kw in tension_keywords if kw in content)
        adjustments += min(tension_count * 3, 15)

        # 완화 키워드
        calm_keywords = ['평화', '휴식', '안전', '회복', '대화', '설명']
        calm_count = sum(1 for kw in calm_keywords if kw in content)
        adjustments -= min(calm_count * 2, 10)

        # 장르별 조정
        if genre == 'wuxia' and any(kw in content for kw in ['검기', '내공', '살기']):
            adjustments += 5
        elif genre == 'hunter' and any(kw in content for kw in ['보스', '레이드', '던전']):
            adjustments += 5
        elif genre == 'investment' and any(kw in content for kw in ['폭락', '파산', '대박']):
            adjustments += 5

        # 범위 내로 클램핑
        final_tension = max(min_t, min(max_t, base_tension + adjustments))
        return final_tension

    def _analyze_curve_shape(self, tensions: list) -> str:
        """긴장도 곡선 형태 분석"""
        if len(tensions) < 2:
            return 'flat'

        # 전반부와 후반부 평균 비교
        mid = len(tensions) // 2
        first_half = sum(tensions[:mid]) / mid if mid > 0 else 0
        second_half = sum(tensions[mid:]) / (len(tensions) - mid) if len(tensions) > mid else 0

        # 변동성 체크
        differences = [tensions[i+1] - tensions[i] for i in range(len(tensions)-1)]
        ascending_count = sum(1 for d in differences if d > 5)
        descending_count = sum(1 for d in differences if d < -5)

        if second_half > first_half + 10:
            return 'ascending'  # 점진적 상승
        elif first_half > second_half + 10:
            return 'descending'  # 하강형
        elif ascending_count >= 2 and descending_count >= 2:
            return 'wave'  # 파도형 (기복)
        else:
            return 'plateau'  # 평탄형

    def _get_recommended_pattern(self, genre: str, current_shape: str) -> list:
        """장르별 권장 패턴 반환"""
        patterns = self.GENRE_TENSION_PATTERNS.get(genre, self.GENRE_TENSION_PATTERNS['wuxia'])
        return patterns.get('standard', [50, 55, 60, 65, 60, 75])

    def _generate_tension_recommendations(self, scene_tensions: list, curve_shape: str, genre: str) -> list:
        """긴장도 개선 권장 사항 생성"""
        recommendations = []

        if not scene_tensions:
            return ["씬 정보 부족 - 긴장도 분석 불가"]

        tensions = [s['tension'] for s in scene_tensions]
        avg = sum(tensions) / len(tensions)

        # 1. 평균 긴장도 체크
        if avg < 45:
            recommendations.append(
                f"평균 긴장도 {avg:.0f}점으로 낮음 - Core 씬 추가 또는 갈등 강화 필요"
            )
        elif avg > 80:
            recommendations.append(
                f"평균 긴장도 {avg:.0f}점으로 높음 - Buffer 씬 추가로 독자 피로도 관리 필요"
            )

        # 2. 곡선 형태별 권장
        if curve_shape == 'plateau':
            recommendations.append(
                "긴장도 변화가 적음 - 클라이맥스 씬(Scene 4-5)에 긴장 집중 필요"
            )
        elif curve_shape == 'descending':
            recommendations.append(
                "긴장도 하강형 - 마지막 씬(Cliffhanger)에서 긴장 회복 필요"
            )

        # 3. 클리프행어 체크
        if tensions and tensions[-1] < 70:
            recommendations.append(
                f"마지막 씬 긴장도 {tensions[-1]}점 - Cliffhanger 효과 약화, 70점 이상 권장"
            )

        # 4. 연속 저긴장 체크
        low_tension_streak = 0
        for t in tensions:
            if t < 50:
                low_tension_streak += 1
            else:
                low_tension_streak = 0

            if low_tension_streak >= 3:
                recommendations.append(
                    "3개 이상 연속 저긴장 씬 - 독자 이탈 위험, 중간에 갈등 씬 삽입 필요"
                )
                break

        return recommendations[:5]  # 최대 5개

    # ========================================================================
    # [V59] 자동 씬 밸런싱 시스템
    # ========================================================================

    def auto_balance_scenes(self, blueprint: dict, genre: str = 'wuxia') -> dict:
        """
        [V59] 씬 밸런싱 자동 조정

        Args:
            blueprint: 블루프린트
            genre: 장르

        Returns:
            {
                'balanced_breakdown': {...},
                'adjustments_made': [...],
                'balance_score': float (0-100)
            }
        """
        scene_breakdown = blueprint.get('scene_breakdown', {})
        if not scene_breakdown:
            return {'error': 'No scene breakdown', 'balanced_breakdown': {}}

        adjustments = []
        balanced = dict(scene_breakdown)

        # 1. 긴장도 분석
        tension_analysis = self.analyze_tension_curve(blueprint, genre)
        scene_tensions = tension_analysis.get('scene_tensions', [])

        # 2. Core/Buffer 비율 체크
        core_count = sum(1 for s in scene_tensions if s['type'] == 'core')
        total_scenes = len(scene_tensions)

        if total_scenes > 0:
            core_ratio = core_count / total_scenes

            # Core 부족 시 (30% 미만)
            if core_ratio < 0.3 and total_scenes >= 4:
                # 중간 씬을 Core로 전환 제안
                mid_scene = f"scene_{total_scenes // 2}"
                if mid_scene in balanced:
                    adjustments.append({
                        'scene': mid_scene,
                        'action': 'upgrade_to_core',
                        'reason': f'Core 비율 {core_ratio:.0%}로 부족'
                    })

            # Core 과다 시 (50% 초과)
            elif core_ratio > 0.5:
                adjustments.append({
                    'action': 'add_buffer',
                    'reason': f'Core 비율 {core_ratio:.0%}로 과다 - 독자 피로'
                })

        # 3. 긴장도 균형 조정
        if tension_analysis.get('curve_shape') == 'plateau':
            # 클라이맥스 강화 제안
            climax_scene = f"scene_{tension_analysis.get('climax_scene', 4)}"
            adjustments.append({
                'scene': climax_scene,
                'action': 'intensify',
                'reason': '긴장도 변화 부족 - 클라이맥스 강화'
            })

        # 4. 씬 길이 균형 체크
        scene_lengths = {}
        for scene_key, content in scene_breakdown.items():
            if isinstance(content, str):
                scene_lengths[scene_key] = len(content)

        if scene_lengths:
            avg_length = sum(scene_lengths.values()) / len(scene_lengths)
            for scene_key, length in scene_lengths.items():
                if length < avg_length * 0.5:
                    adjustments.append({
                        'scene': scene_key,
                        'action': 'expand',
                        'reason': f'씬 분량 {length}자로 평균({avg_length:.0f}자)의 50% 미만'
                    })
                elif length > avg_length * 1.5:
                    adjustments.append({
                        'scene': scene_key,
                        'action': 'trim',
                        'reason': f'씬 분량 {length}자로 평균({avg_length:.0f}자)의 150% 초과'
                    })

        # 5. 밸런스 점수 계산
        balance_score = self._calculate_balance_score(
            scene_tensions, core_count, total_scenes, tension_analysis.get('curve_shape', 'unknown')
        )

        return {
            'balanced_breakdown': balanced,
            'adjustments_made': adjustments[:10],  # 최대 10개
            'balance_score': round(balance_score, 1),
            'tension_analysis': tension_analysis,
            'metrics': {
                'core_ratio': core_count / total_scenes if total_scenes > 0 else 0,
                'total_scenes': total_scenes,
                'core_scenes': core_count,
                'curve_shape': tension_analysis.get('curve_shape', 'unknown')
            }
        }

    def _calculate_balance_score(self, scene_tensions: list, core_count: int,
                                  total_scenes: int, curve_shape: str) -> float:
        """밸런스 점수 계산"""
        score = 100.0

        if total_scenes == 0:
            return 0

        # Core 비율 점수 (30-50% 이상적)
        core_ratio = core_count / total_scenes
        if core_ratio < 0.3:
            score -= (0.3 - core_ratio) * 50
        elif core_ratio > 0.5:
            score -= (core_ratio - 0.5) * 30

        # 곡선 형태 점수
        shape_scores = {
            'ascending': 0,      # 가장 좋음
            'wave': -5,          # 괜찮음
            'descending': -15,   # 주의
            'plateau': -20,      # 나쁨
            'flat': -25,         # 매우 나쁨
        }
        score += shape_scores.get(curve_shape, -10)

        # 긴장도 분산 점수
        if scene_tensions:
            tensions = [s['tension'] for s in scene_tensions]
            variance = sum((t - sum(tensions)/len(tensions)) ** 2 for t in tensions) / len(tensions)

            # 적정 분산 (150-400)
            if variance < 100:
                score -= 10  # 변화 부족
            elif variance > 500:
                score -= 10  # 변화 과다

        return max(0, min(100, score))

    def build_tension_curve_prompt(self, tension_analysis: dict) -> str:
        """
        [V59] 긴장도 곡선 분석 결과를 프롬프트에 주입할 형태로 변환

        Args:
            tension_analysis: analyze_tension_curve() 결과

        Returns:
            str: 프롬프트 주입용 텍스트
        """
        if not tension_analysis or tension_analysis.get('error'):
            return ""

        lines = [
            "\n📊 [V59 TENSION CURVE ANALYSIS]\n"
        ]

        # 곡선 시각화
        scene_tensions = tension_analysis.get('scene_tensions', [])
        if scene_tensions:
            lines.append("씬별 긴장도:")
            for st in scene_tensions:
                tension = st.get('tension', 50)
                bar = '█' * (tension // 10) + '░' * (10 - tension // 10)
                lines.append(f"  {st['scene']}: [{bar}] {tension}점 ({st['type']})")

        # 요약 정보
        lines.append(f"\n곡선 형태: {tension_analysis.get('curve_shape', '?')}")
        lines.append(f"클라이맥스: 씬 {tension_analysis.get('climax_scene', '?')}")
        lines.append(f"평균 긴장도: {tension_analysis.get('average_tension', 0)}점")

        # 권장 사항
        recommendations = tension_analysis.get('recommendations', [])
        if recommendations:
            lines.append("\n⚠️ 권장 사항:")
            for rec in recommendations[:3]:
                lines.append(f"  - {rec}")

        return "\n".join(lines)