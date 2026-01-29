import json
import re
from pathlib import Path
from google.genai import types
from .base_agent import BaseAgent

class Writer(BaseAgent):
    """[V31 Sovereign Writer] 듀얼 캐시 시스템 대응 및 비용 최적화 집필 엔진"""

    def __init__(self, context, client, model_tier="gemini-1.5-pro"):
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

    def write_v20_manuscript(self, ep_num, breakdown_doc, master_bible, hud_report, purism_prompt, 
                             style_mode="", intro_dna="CYNICAL", feedback="", prev_full_manuscript="", 
                             arc_doc="", tactical_references=""):     
        
        # 1. [변동 데이터] Dynamic Payload 구성
        # 매 화 바뀌는 정보만 모아서 가볍게 만듭니다.
        # 프롬프트 조립 구역에 아래 지침 추가
        # 1. [강조 패치 데이터 추출] 🔦
        focus_info = arc_doc if isinstance(arc_doc, dict) else {}
        focus_tag = focus_info.get("MUST_FOCUS_ON", "N/A")
        full_arc_map = focus_info.get("FULL_ARC_MAP", str(arc_doc)) # 전체 지도는 참고용
        pattern_profile = focus_info.get("PATTERN_PROFILE", {})
        pattern_logic = focus_info.get("PATTERN_MIXING_LOGIC", "")
        pattern_primary = pattern_profile.get("primary", "패턴 정보 없음") if isinstance(pattern_profile, dict) else "패턴 정보 없음"
        pattern_secondary = pattern_profile.get("secondary", []) if isinstance(pattern_profile, dict) else []

        # 2. [성경 데이터 정밀 수혈] 💉 (이 부분이 누락되었던 핵심입니다!)
        bible_root = master_bible.get('MasterBible', master_bible)
        core_identity = bible_root.get('ProjectData', {}).get('CoreIdentity', {})
        assets = bible_root.get('AssetLibrary', {})

        # [V45] NPC 장비 현황 추출 (Writer가 NPC 소지품을 명확히 인지하도록)
        npc_equipment_summary = []
        key_npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])
        for npc in key_npcs:
            if isinstance(npc, dict):
                npc_name = npc.get('name') or npc.get('Name', '알 수 없음')
                npc_hud = npc.get('NPC_Martial_HUD', {})
                if isinstance(npc_hud, dict):
                    equip = npc_hud.get('equipment', [])
                    if equip:
                        npc_equipment_summary.append(f"- {npc_name}: {equip}")

        # 3. [데이터 보호/에스케이프]
        safe_desire = self._escape_braces(core_identity.get('desire', '전설적 무인으로의 복귀'))
        safe_assets = self._escape_braces(json.dumps(assets, ensure_ascii=False))
        safe_npc_equipment = self._escape_braces("\n".join(npc_equipment_summary)) if npc_equipment_summary else "NPC 장비 정보 없음"    
        # (A) 피드백 섹션
        feedback_section = f"\n[🚨 REJECTION FEEDBACK]: {feedback}" if feedback else ""
        
        # (B) 스타일 및 DNA 결정 (2화부터는 연속성 모드)
        if int(ep_num) == 1:
            dna_instruction = f"[제1화 특수 DNA 적용]: {intro_dna}"
        else:
            dna_instruction = "[연속 집필 모드]: 이전 화의 마침표에서 단 1초의 공백 없이 사건을 전진시켜라."

        # (C) 전술 참조 기본값 방어
        if not tactical_references:
            tactical_references = "특이 사항 없음. 성경의 무학적 원칙 준수."

        # (D) [V40 Premium] 참조 앵커 추출 (과거 사건 강제 기억)
        reference_anchor_prompt = ""
        try:
            from modules.core.reference_anchor import ReferenceAnchor

            anchor_sys = ReferenceAnchor(self.context)

            # arc_doc 안전성 검증 (None이나 비문자열 처리)
            safe_arc_context = arc_doc if arc_doc else ""

            # 관련 앵커 추출 (최근 10화 내에서 현재 아크와 연관된 것)
            relevant_anchors = anchor_sys.get_relevant_anchors(
                current_ep_num=ep_num,
                arc_context=safe_arc_context,
                n_anchors=5
            )

            # 필수 참조 앵커 (타입별 최신 상태)
            critical_anchors = anchor_sys.get_critical_anchors(
                current_ep_num=ep_num,
                anchor_types=['item', 'injury', 'power', 'location']
            )

            # 참조 프롬프트 생성
            if relevant_anchors or critical_anchors:
                reference_anchor_prompt = anchor_sys.generate_reference_prompt(
                    relevant_anchors=relevant_anchors,
                    critical_anchors=critical_anchors
                )
        except ImportError as ie:
            print(f"      ⚠️ [Writer] ReferenceAnchor 모듈 로드 실패: {ie}")
        except AttributeError as ae:
            print(f"      ⚠️ [Writer] ReferenceAnchor 컨텍스트 오류: {ae}")
        except Exception as e:
            print(f"      ⚠️ [Writer] ReferenceAnchor 실행 실패: {type(e).__name__}: {e}")
            reference_anchor_prompt = ""

        # 2. [Phase 1.1] Pattern Breaking Instructions (반클리셰 명령)
        genre_name = getattr(self.context, 'genre', {}).get('name', '무협')
        anti_trope = self._build_anti_trope_instructions(genre_name)

        # 2. [Phase 1.2] Mandatory Context Injection (맥락 강제 주입)
        mandatory_context = self._build_mandatory_context(ep_num)

        # 2. [Phase 4.3] Justification Pattern Guidance (정당화 패턴 안내)
        justification_guidance = self._build_justification_guidance(hud_report, genre_name)

        # [Phase 5.2.2] Reflexion: 과거 실패 패턴 주입
        reflexion_prompt = ""
        try:
            # 20화 이후부터 활성화 (충분한 데이터 필요)
            if ep_num >= 20:
                from modules.core.reflexion_manager import ReflexionManager
                reflexion = ReflexionManager(self.context)
                reflexion_prompt = reflexion.get_prompt_injection(min_frequency=2)
        except Exception as e:
            print(f"      ⚠️ [Writer] Reflexion 로드 실패: {e}")

        # 2. [프롬프트 조립] Dynamic Context
        # 캐시가 있다면 이 내용만 전송됩니다. (비용 절감 핵심)
        dynamic_prompt = f"""
        {mandatory_context}

        {feedback_section}
        {reference_anchor_prompt}

        {anti_trope}

        {justification_guidance}

        {reflexion_prompt}

        [🚨 WRITER'S FOCUS MISSION]
        1. 당신은 현재 {focus_tag}의 내용을 바탕으로 소설 원고를 집필하고 있다.
        2. 'FULL_ARC_MAP'은 오직 설정 충돌 방지를 위한 참고용일 뿐이다. 절대 미래의 사건을 문장에 미리 노출하지 마라.
        3. 오직 씬 설계도(Blueprint)에 명시된 6개의 장면을 하나하나 4K 해상도로 늘려 쓰는 데에만 집중하라.
        4. 현재 장면에서 해결되지 말아야 할 갈등을 문장에서 서둘러 해결하지 마라.
        5. 에피소드의 마지막 문장은 반드시 독자가 다음 화를 보지 않고는 못 배길 정도의 강렬한 여운(절벽걸기)을 남기며 끝내라.        
        
        
        [CURRENT MISSION: Ep {ep_num}]
        캐시된 [집필 강령], [문체], [세계관]을 바탕으로, 아래 재료를 사용하여 제 {ep_num}화를 집필하라.

        ### 🎨 적용 스타일
        - **플랫폼**: {style_mode}
        - **전개 모드**: {dna_instruction}
        {purism_prompt}

        ### 📚 세계관 성경 (Master Bible) 👈 (추가된 데이터 앵커)
        - **주인공의 근본 동력**: {safe_desire}
        - **가용 자산(NPC/ITEM)**: {safe_assets}

        ### 🗡️ [V45] NPC 현재 장비 현황
        {safe_npc_equipment}
        ⚠️ NPC가 소지한 무기/장비는 반드시 일관되게 묘사하라. 갑자기 없던 무기가 생기거나 사라지면 안 된다.

        👥 [Lightweight] 주요 NPC 등장 빈도 (최근 10화):
        {self._get_npc_frequency_warning(ep_num)}

        ### 📋 1. 씬 설계도 (Blueprint)
        {self._escape_braces(breakdown_doc)}

        ### 🛡️ 2. 실시간 상태 (Dynamic Context)
        [🚨 CRITICAL: 주인공 현재 상태 - 반드시 이 정보를 기반으로 집필하라!]
        {self._escape_braces(hud_report)}

        📈 [Lightweight] 최근 5화 HUD 변화 추세:
        {self._get_hud_trend_safe(ep_num)}
        ⚠️ 갑작스러운 변화가 있다면 반드시 정당화 필요!

        ⚠️ 집필 시 필수 준수 사항:
        1. 주인공의 '경지'와 '내공'을 절대 넘어서는 묘사를 하지 마라
        2. '상태' 항목의 부상/피로는 전투 장면에서 반드시 반영하라
        3. '자금' 상태를 무시하고 함부로 물건을 사거나 뇌물을 쓰지 마라
        4. '착각' 지수가 높다면 주변인들의 오해를 활용한 서사를 전개하라
        5. '목표'는 주인공의 모든 행동 동기가 되어야 한다

        - **직전 원고 엔딩**: ...{self._escape_braces(prev_full_manuscript)[-1500:]} (반드시 연결할 것)
        
        ### ⚔️ 3. 전술 참조 (Reference)
        - **아크 전술**: {self._escape_braces(arc_doc)}
        {self._escape_braces(tactical_references)}
        
        ### 🧩 4. 패턴 설계 (Hybrid Composition)
        - **주 패턴**: {self._escape_braces(str(pattern_primary))}
        - **부 패턴**: {self._escape_braces(str(pattern_secondary))}
        - **조합 논리**: {self._escape_braces(str(pattern_logic))}

        ### ⚠️ 출력 형식 (Strict JSON) [V41 State Updates Protocol]
        - 제목, 본문, 상태 변화로 구성된 JSON을 출력하라.
        {{
            "title": "에피소드 제목 (한글만)",
            "content": "5,000자 이상의 소설 본문 (줄바꿈은 \\n)",
            "state_updates": {{
                "internal_energy": "+50" 또는 "현상 유지",
                "realm": "경지명" 또는 "현상 유지",
                "causal_injuries": "부상 상태 (예: 경상, 중상, 정상)",
                "wealth": "+/-금액" 또는 "현상 유지",
                "misunderstanding": "+10" 또는 "현상 유지",
                "obsession": "+5" 또는 "현상 유지",
                "equipment": "새로 획득한 아이템" 또는 "현상 유지",
                "martial_arts": "새로 습득한 무공" 또는 "현상 유지"
            }}
        }}

        ### 📌 state_updates 작성 지침
        1. 이번 화에서 실제로 발생한 변화만 기록하라
        2. 변화가 없는 항목은 "현상 유지"로 표기하라
        3. 수치 변화는 반드시 +/- 기호와 함께 표기하라 (예: "+100", "-50냥")
        4. 부상 상태는 구체적으로 기술하라 (예: "중상 (좌측 팔뚝 관통상)")
        5. 경지 변화는 신중하게 판단하라 - 원고에 명시적 돌파 장면이 있을 때만 변경
        6. 당신의 state_updates는 '제안'일 뿐이다. Director가 최종 승인/거부 권한을 갖는다.
        """

        # 3. [API 호출] 캐시 유무에 따른 분기 처리
        try:
            if self.cache_name:
                # ✅ Case A: 캐시 활성화 (저비용 고효율)
                # print(f"      ⚡ [Writer] 캐시({self.cache_name})를 사용하여 집필합니다.")
                
                response = self.client.models.generate_content(
                    model=self.primary_model,
                    contents=dynamic_prompt, # 변동 데이터만 전송
                    config=types.GenerateContentConfig(
                        cached_content=self.cache_name, # 🔥 고정 지침(Manifesto)은 여기서 참조
                        temperature=0.8,
                        max_output_tokens=8192,
                        response_mime_type="application/json"
                    )
                )
                manuscript = self._sanitize_leakage(response.text)

                # [Phase 5.2.1] Self-Critique + Fix
                # [FIX] KeyNPCs vs Key_NPCs 키 불일치 처리
                assets = master_bible.get('AssetLibrary', {})
                npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

                manuscript = self._apply_self_critique(
                    manuscript, hud_report, npcs,
                    getattr(self.context, 'genre', {}).get('name', '무협'),
                    ep_num  # Lightweight alternatives: 최근 빈도 추적용
                )

                return manuscript
            
            else:
                # ⚠️ Case B: 캐시 없음 (Fallback - 전체 프롬프트 재구성)
                # print("      ⚠️ [Writer] 캐시가 없습니다. 전체 프롬프트를 전송합니다.")
                return self._fallback_full_request(dynamic_prompt, hud_report, master_bible,
                                                     getattr(self.context, 'genre', {}).get('name', '무협'))

        except Exception as e:
            print(f"      🚨 [Writer Error] 캐시 호출 실패. 일반 모드로 전환합니다: {e}")
            return self._fallback_full_request(dynamic_prompt, hud_report, master_bible,
                                                 getattr(self.context, 'genre', {}).get('name', '무협'), ep_num)

    def _fallback_full_request(self, dynamic_prompt, hud_report="", master_bible=None, genre_name='무협', ep_num=None):
        """[Fallback] 캐시가 없을 때 JSON 파일 및 문체 파일을 읽어 전체 프롬프트를 구성"""
        try:
            # 1. 집필 강령 (JSON) 로드
            rules_path = self.context.paths.config / "prompts" / "writer_rules.json"
            full_context = "[SYSTEM: WRITER MANIFESTO]\n"
            
            if rules_path.exists():
                data = json.loads(rules_path.read_text(encoding='utf-8'))
                manifesto = "\n".join(data.get("common_manifesto", []))
                ep1 = "\n".join(data.get("special_rule_ep1", []))
                full_context += f"{manifesto}\n\n{ep1}\n\n"
            
            # 2. 🔥 [누락 보완] 문체 시드 (TXT) 로드
            # 비상시에도 문체 퀄리티를 유지하기 위해 로드
            seed_path = self.context.paths.config / "cash" / "style_seeds_final.txt"
            if seed_path.exists():
                full_context += f"### [STYLE GENETIC SEEDS]\n{seed_path.read_text(encoding='utf-8')}\n\n"

            # 3. 최종 결합
            full_prompt = f"{full_context}\n{dynamic_prompt}"
            manuscript = self._sanitize_leakage(self.ask(full_prompt, temperature=0.8))

            # [Phase 5.2.1] Self-Critique + Fix (fallback에서도 적용)
            # [FIX] 파라미터로 받은 hud_report, master_bible 직접 사용
            if master_bible is None:
                master_bible = {}

            assets = master_bible.get('AssetLibrary', {})
            npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

            manuscript = self._apply_self_critique(manuscript, hud_report, npcs, genre_name, ep_num)
            return manuscript
            
        except Exception as e:
            print(f"      ❌ Fallback 구성 실패: {e}")
            # 최악의 경우라도 집필은 시도
            manuscript = self._sanitize_leakage(self.ask(dynamic_prompt, temperature=0.8))
            # Self-Critique는 최악의 경우 스킵 (이미 오류 발생 상태)
            return manuscript

    def _sanitize_leakage(self, text):
        """[V35.6] Writer 출력 누수(Leakage) 방지용 사후 필터"""
        if not text: return text

        # 1. JSON 구조적 정제 시도
        try:
            # Markdown 코드 블록 제거
            clean_text = re.sub(r"```json\s*|\s*```", "", text).strip()
            data = json.loads(clean_text)
            
            # 금지된 키 리스트 (누수 주범)
            banned_keys = ["Beat 3", "Beat 4", "continuation_text", "scene_summary"]
            
            if isinstance(data, dict):
                for key in banned_keys:
                    if key in data:
                        del data[key]  # 구조적 삭제
                return json.dumps(data, ensure_ascii=False, indent=4)
        except (json.JSONDecodeError, ValueError):
            pass  # JSON 파싱 실패 시 텍스트 모드로 전환

        # 2. 텍스트 라인 필터링 (비상 대책)
        # "Beat 3": ... 형태의 라인을 강제로 날림
        filtered_lines = []
        for line in text.splitlines():
            # 누수 패턴 감지 regex
            if re.search(r'"(Beat \d+|continuation_text)":', line):
                continue
            filtered_lines.append(line)
            
        return "\n".join(filtered_lines)

    def refine_with_editor(self, ep_num, raw_draft, editor_feedback):
        """[Stage 4.5] 에디터 피드백 기반 최종 문장 교정"""
        safe_draft = self._escape_braces(raw_draft)
        safe_feedback = self._escape_braces(editor_feedback)
        
        prompt = f"""
        [Role] 수석 에디터
        [Task] 제 {ep_num}화 원고를 아래 지침에 맞춰 최종 교정하라.
        [Feedback] {safe_feedback}
        
        [Target Draft] 
        {safe_draft}

        교정된 소설 본문만 출력하라.
        """
        return self.ask(prompt, temperature=0.3)

    def _build_anti_trope_instructions(self, genre_name: str) -> str:
        """[Phase 1.1] 반클리셰 명령 생성"""
        return f"""
🚫 [ANTI-TROPE PROTOCOL - 장르 관습 재정의]

이 작품은 일반적인 {genre_name}물과 다릅니다. 다음 클리셰는 절대 사용하지 마십시오:

1. "약해 보이는 주인공" 클리셰 금지
   - ❌ "허름한 행색", "평범해 보이는", "별 볼일 없어 보이는"
   - ✅ 주인공의 실제 HUD 상태를 직접 반영
   - ✅ "증표를 본 순간 안색이 창백해졌다" (데이터 기반 묘사)

2. "무시-사이다" 공식 과다 사용 금지
   - ❌ 매 에피소드마다 무시당하고 압도하는 반복
   - ✅ 주인공의 명성/권위가 증가하면 무시는 감소해야 함
   - ✅ 무시가 필요하면 반드시 알리바이 (정보 차단, 변장 등)

3. "조연의 영구 생존" 클리셰 금지
   - ❌ 모욕한 하인이 아무 처벌 없이 계속 등장
   - ✅ 모욕/배신한 조연은 반드시 청산 (처단/퇴장/굴복)

4. "순간 회복" 클리셰 금지
   - ❌ 전투 중 부상 → 다음 장면에서 멀쩡함 (설명 없이)
   - ✅ 부상은 지속적으로 영향 주거나, 치료 과정 명시

5. "NPC의 기억상실" 클리셰 금지
   - ❌ 이전 화에서 경외했던 NPC가 이번 화에서 다시 무시
   - ✅ 관계는 단방향 발전 (무시→경외는 가능, 경외→무시는 정당화 필요)

[⚠️ 당신이 쓰려는 문장이 위 클리셰에 해당하는가? YES → 다시 쓰십시오]
"""

    def _build_mandatory_context(self, current_ep: int) -> str:
        """[Phase 1.2] 강제 맥락 주입"""
        mandatory_parts = ["📌 [MANDATORY CONTEXT - 반드시 인지하고 집필할 것]\n"]

        # 1. 최근 3화의 핵심 사건 추출
        recent_events = self._extract_recent_events(current_ep, n_episodes=3)

        if recent_events:
            mandatory_parts.append("\n🔥 최근 중요 사건 (절대 무시 금지):")
            for event in recent_events:
                mandatory_parts.append(f"• 제{event['ep_num']}화: {event['description']}")
                if event.get('consequence'):
                    mandatory_parts.append(f"  현재 상태: {event['consequence']}")
                mandatory_parts.append(f"  ⚠️ 이 사실을 무시하면 논리 모순 발생\n")

        # 2. 등장 NPC의 마지막 상태 추출
        npc_states = self._extract_npc_last_states(current_ep)

        if npc_states:
            mandatory_parts.append("\n👤 NPC 마지막 관계 상태 (일관성 유지 필수):")
            for npc_name, state_info in npc_states.items():
                mandatory_parts.append(f"• {npc_name}: {state_info['relationship']} (제{state_info['last_ep']}화)")
                mandatory_parts.append(f"  → 이 관계가 변경되려면 명시적 사건 필요\n")

        # 3. 빈 경우 기본 메시지
        if len(mandatory_parts) == 1:
            mandatory_parts.append("\n(첫 에피소드이거나 강제 맥락 없음)")

        return "\n".join(mandatory_parts)

    def _extract_recent_events(self, current_ep: int, n_episodes: int = 3) -> list:
        """최근 N화의 핵심 사건 추출"""
        events = []

        try:
            for ep in range(max(1, current_ep - n_episodes), current_ep):
                # DB에서 state_log 로드 시도
                log_data = self.context.db.load_state_log(ep)

                if log_data and isinstance(log_data, dict):
                    # summary에서 주요 변화 추출
                    summary = log_data.get('summary', '')
                    if summary and len(summary) > 10:
                        events.append({
                            'ep_num': ep,
                            'description': summary[:200],  # 200자로 제한
                            'consequence': ''
                        })

                    # data에서 major_changes 추출 (있다면)
                    data = log_data.get('data', {})
                    if isinstance(data, dict):
                        major_changes = data.get('major_changes', [])
                        if major_changes:
                            for change in major_changes[:2]:  # 최대 2개
                                if isinstance(change, dict):
                                    events.append({
                                        'ep_num': ep,
                                        'description': change.get('event', ''),
                                        'consequence': change.get('consequence', '')
                                    })
        except Exception as e:
            # DB 접근 실패 시 조용히 넘어감
            print(f"      ⚠️ [Writer] 최근 사건 추출 실패: {e}")

        return events[-5:] if events else []  # 최대 5개만

    def _extract_npc_last_states(self, current_ep: int) -> dict:
        """등장 NPC의 마지막 상태 추출"""
        npc_states = {}

        try:
            # Bible에서 NPC 정보 로드
            bible = getattr(self.context, 'master_bible', {})
            bible_root = bible.get('MasterBible', bible)
            assets = bible_root.get('AssetLibrary', {})
            key_npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

            for npc in key_npcs:
                if not isinstance(npc, dict):
                    continue

                name = npc.get('name') or npc.get('Name', '')
                if not name:
                    continue

                # 관계 상태
                relationship = npc.get('relationship_state', '중립')
                last_appearance = npc.get('last_appearance_ep', 0)

                # 최근 등장했고, 현재 화 이전이면 추가
                if isinstance(last_appearance, int) and 0 < last_appearance < current_ep:
                    npc_states[name] = {
                        'relationship': relationship,
                        'last_ep': last_appearance
                    }
        except Exception as e:
            # 실패해도 조용히 넘어감
            print(f"      ⚠️ [Writer] NPC 상태 추출 실패: {e}")

        return npc_states

    def _build_justification_guidance(self, hud_report: str, genre_name: str) -> str:
        """
        [Phase 4.3] 정당화 패턴 가이드 생성

        현재 HUD 상태를 분석하여 제약 조건을 파악하고,
        해당 제약을 극복할 때 필요한 정당화 패턴을 제시
        """
        try:
            from modules.core.justification_patterns import get_justification_guide, get_available_patterns
        except ImportError:
            return ""  # 모듈 없으면 조용히 스킵

        guidance_parts = ["🧠 [JUSTIFICATION PATTERNS - 제약 극복 시 필수 참고]\n"]
        active_constraints = []

        # HUD에서 제약 감지
        hud_lower = hud_report.lower()

        # 1. 신체 제약 감지
        physical_constraints = ['나약', '중독', '부상', '중상', '쇠약', '기력고갈', '기혈역류']
        if any(constraint in hud_report for constraint in physical_constraints):
            active_constraints.append('weak_body_strong_action')
            guidance_parts.append("\n⚠️ [신체 제약 감지] 현재 주인공은 신체적 약점이 있습니다.")
            guidance_parts.append("강력한 행동 시 반드시 정당화 필요:")

        # 2. 지위 제약 감지 (reputation 또는 status tags)
        low_status_keywords = ['하인', '노예', '평민', '무명', '낭인', '거지', '천민']
        if any(keyword in hud_report for keyword in low_status_keywords) or 'reputation' in hud_lower:
            # reputation 수치 추출 시도
            import re
            rep_match = re.search(r'reputation[:\s]+(\d+)', hud_report, re.IGNORECASE)
            if rep_match:
                rep_value = int(rep_match.group(1))
                if rep_value < 30:
                    active_constraints.append('low_status_high_authority')
                    guidance_parts.append("\n⚠️ [지위 제약 감지] 현재 주인공은 낮은 명성/지위입니다.")
                    guidance_parts.append("명령/지시 행위 시 반드시 정당화 필요:")

        # 3. 능력 급상승 가능성 (돌파 징조만 감지)
        # "경지" 단독으로는 트리거 안함 - "돌파" 같은 변화 키워드만
        breakthrough_keywords = ['돌파', '깨달음', '체득', '각성', '각오']
        if any(keyword in hud_report for keyword in breakthrough_keywords):
            # 급상승은 항상 정당화 필요
            active_constraints.append('sudden_power_increase')
            guidance_parts.append("\n💡 [능력 상승 가능성] 경지 돌파 시 반드시 정당화 필요:")

        # 패턴 가이드 추가
        for constraint_type in active_constraints:
            try:
                guide = get_justification_guide(genre_name, constraint_type)
                guidance_parts.append(f"\n{guide}")
            except Exception as e:
                print(f"      ⚠️ [Writer] 정당화 패턴 로드 실패 ({constraint_type}): {e}")

        # 제약이 없으면 빈 문자열 반환
        if len(active_constraints) == 0:
            return ""

        # 최종 메시지
        guidance_parts.append("\n")
        guidance_parts.append("📌 중요: 위 패턴은 '영감의 원천'입니다. 정확히 따라할 필요 없이,")
        guidance_parts.append("'논리 구조'를 참고하여 당신만의 창의적인 정당화를 만드십시오.")

        return "\n".join(guidance_parts)

    def _apply_self_critique(self, manuscript: str, hud_report: str, npcs: list, genre_name: str, ep_num: int = None) -> str:
        """
        [Phase 5.2.1] Self-Critique 적용 (헬퍼)

        원고에 Self-Critique를 실행하고, 문제가 있으면 수정 후 반환

        Args:
            manuscript: 원고 (JSON 문자열)
            hud_report: HUD 정보
            npcs: NPC 리스트
            genre_name: 장르
            ep_num: 에피소드 번호 (Lightweight alternatives용, 선택적)

        Returns:
            str: 검토 및 수정된 원고
        """
        encyclopedia = {'npcs': npcs}

        # Self-Critique 실행 (ep_num 전달)
        critique_result = self._self_critique(manuscript, hud_report, encyclopedia, genre_name, ep_num)

        # 문제가 있으면 수정
        if critique_result['has_issues'] and critique_result['severity'] in ['medium', 'high']:
            manuscript = self._fix_manuscript_issues(manuscript, critique_result, hud_report)

        return manuscript

    def _self_critique(self, manuscript: str, hud_report: str, encyclopedia: dict, genre_name: str, ep_num: int = None) -> dict:
        """
        [Phase 5.2.1] Writer Self-Critic

        원고 작성 후 스스로 문제점을 발견

        Args:
            manuscript: 작성한 원고 (JSON 문자열)
            hud_report: 주인공 HUD 정보
            encyclopedia: 세계관 백과사전
            genre_name: 장르
            ep_num: 에피소드 번호 (Lightweight alternatives용, 선택적)

        Returns:
            {
                "has_issues": bool,
                "issues": [
                    {"type": "hud_contradiction", "location": "...", "description": "..."},
                    ...
                ],
                "severity": "low" | "medium" | "high"
            }
        """
        print("      🔍 [Self-Critic] 원고 자체 검토 중...")

        # JSON 파싱
        try:
            data = json.loads(manuscript)
            content = data.get('content', '')
        except:
            content = manuscript

        # 체크리스트
        issues = []

        # 1. HUD 모순 체크
        hud_issues = self._check_hud_consistency(content, hud_report)
        issues.extend(hud_issues)

        # 2. 클리셰 과다 체크 (최근 빈도 추적 추가)
        cliche_issues = self._check_cliche_overuse(content, genre_name, ep_num)
        issues.extend(cliche_issues)

        # 3. 정당화 부족 체크
        justification_issues = self._check_justification_gaps(content, hud_report)
        issues.extend(justification_issues)

        # 4. NPC 관계 일관성 체크
        npc_issues = self._check_npc_relationship(content, encyclopedia)
        issues.extend(npc_issues)

        # 심각도 판단
        severity = "low"
        if len(issues) >= 3:
            severity = "high"
        elif len(issues) >= 1:
            severity = "medium"

        has_issues = len(issues) > 0

        if has_issues:
            print(f"      ⚠️ [Self-Critic] {len(issues)}개 문제 발견 (심각도: {severity})")
            for issue in issues[:3]:  # 상위 3개만 출력
                print(f"         - {issue['type']}: {issue['description'][:50]}...")
        else:
            print(f"      ✅ [Self-Critic] 문제 없음")

        return {
            "has_issues": has_issues,
            "issues": issues,
            "severity": severity
        }

    def _check_hud_consistency(self, content: str, hud_report: str) -> list:
        """HUD 모순 체크"""
        issues = []

        # 신체 제약 키워드
        weak_keywords = ['나약', '중독', '부상', '중상', '쇠약']
        strong_actions = ['일격에', '압도', '박살', '분쇄', '제압']

        is_weak = any(kw in hud_report for kw in weak_keywords)
        has_strong_action = any(kw in content for kw in strong_actions)

        if is_weak and has_strong_action:
            # 정당화 키워드 확인
            justification_kws = ['발경', '기혈', '폭발', '전생', '대가', '고통']
            has_justification = any(kw in content for kw in justification_kws)

            if not has_justification:
                issues.append({
                    "type": "hud_contradiction",
                    "description": "나약한 상태에서 강력한 행동, 정당화 부족",
                    "location": "본문",
                    "severity": "medium"
                })

        return issues

    def _get_npc_frequency(self, ep_num: int, window: int = 10) -> dict:
        """
        [Lightweight Alternative] 최근 N화에서 주요 NPC 등장 횟수

        Args:
            ep_num: 현재 화 번호
            window: 추적할 화 수 (기본 10화)

        Returns:
            dict: {"연홍": 8, "화산장로": 2, ...}
        """
        try:
            master_bible = self.context.get_anchor('bible')
            if not master_bible:
                return {}

            assets = master_bible.get('AssetLibrary', {})
            key_npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

            if not key_npcs:
                return {}

            # NPC 이름 추출
            npc_names = [npc.get('name', '') for npc in key_npcs if isinstance(npc, dict) and npc.get('name')]

            # 빈도 카운트
            frequency = {name: 0 for name in npc_names}

            for i in range(max(1, ep_num - window), ep_num):
                try:
                    past_ms = self.context.get_manuscript(i)
                    if past_ms:
                        for name in npc_names:
                            if name in past_ms:
                                frequency[name] += 1
                except:
                    continue

            return frequency
        except Exception:
            return {}

    def _get_npc_frequency_warning(self, ep_num: int) -> str:
        """
        [Lightweight Alternative] NPC 등장 빈도 경고 메시지 생성

        Args:
            ep_num: 에피소드 번호

        Returns:
            str: NPC 빈도 경고 메시지
        """
        if ep_num < 2:
            return "초반부 - NPC 빈도 추적 없음"

        try:
            npc_freq = self._get_npc_frequency(ep_num, window=10)

            if not npc_freq:
                return "주요 NPC 정보 없음"

            warnings = []
            for name, count in npc_freq.items():
                if count == 0:
                    warnings.append(f"⚠️ {name}: 최근 10화 미등장 → 관계 유지 고려")
                elif count >= 7:
                    warnings.append(f"✅ {name}: 최근 {count}회 등장 → 주연급 일관성 유지")

            if warnings:
                return "\n".join(warnings)
            else:
                return "모든 주요 NPC 적정 빈도 유지 중"

        except Exception:
            return "빈도 추적 실패"

    def _count_recent_cliches(self, ep_num: int, manuscript: str, window: int = 10) -> dict:
        """
        [Lightweight Alternative] 최근 N화에서 클리셰 빈도 카운트

        Args:
            ep_num: 현재 화 번호
            manuscript: 현재 원고
            window: 추적할 화 수 (기본 10화)

        Returns:
            dict: {"피를 토하": 3, "기세": 5, ...}
        """
        # 주요 무협 클리셰 키워드
        cliche_keywords = [
            "피를 토하", "기세", "살기", "냉기", "검기",
            "압도", "전율", "경악", "창백", "경외",
            "무시", "조롱", "비웃", "허름"
        ]

        counts = {keyword: 0 for keyword in cliche_keywords}

        # 최근 화들 검색
        for i in range(max(1, ep_num - window), ep_num):
            try:
                past_ms = self.context.get_manuscript(i)
                if past_ms:
                    for keyword in cliche_keywords:
                        counts[keyword] += past_ms.count(keyword)
            except:
                continue

        # 현재 원고도 체크
        for keyword in cliche_keywords:
            counts[keyword] += manuscript.count(keyword)

        return {k: v for k, v in counts.items() if v > 0}

    def _check_cliche_overuse(self, content: str, genre_name: str, ep_num: int = None) -> list:
        """
        클리셰 과다 사용 체크 (최근 N화 빈도 추적 추가)

        Args:
            content: 현재 원고
            genre_name: 장르
            ep_num: 에피소드 번호 (최근 빈도 체크용, 선택적)
        """
        issues = []

        # [Lightweight Alternative] 최근 빈도 체크 추가
        if ep_num is not None and ep_num > 1:
            recent_counts = self._count_recent_cliches(ep_num, content, window=10)

            overused = [
                f"'{keyword}' ({count}회)"
                for keyword, count in recent_counts.items()
                if count >= 3  # 10화 중 3회 이상이면 과용
            ]

            if overused:
                issues.append({
                    "type": "cliche_overuse_recent",
                    "description": f"최근 클리셰 과용: {', '.join(overused[:3])}",  # 최대 3개만 표시
                    "location": "최근 10화",
                    "severity": "medium",
                    "recommendation": "다른 표현으로 다양화 필요"
                })

        # 무협 클리셰 패턴 (기존 로직 유지)
        if genre_name == '무협':
            cliche_patterns = [
                ('무시', '별 볼일'),
                ('무시', '평범해'),
                ('허름', '행색'),
                ('조롱', '비웃'),
            ]

            cliche_count = 0
            for pattern1, pattern2 in cliche_patterns:
                if pattern1 in content and pattern2 in content:
                    cliche_count += 1

            if cliche_count >= 2:
                issues.append({
                    "type": "cliche_overuse",
                    "description": f"'{pattern1}-{pattern2}' 패턴이 {cliche_count}회 반복",
                    "location": "본문",
                    "severity": "low"
                })

        return issues

    def _check_justification_gaps(self, content: str, hud_report: str) -> list:
        """정당화 누락 체크"""
        issues = []

        # 제약 키워드 추출
        constraints = []
        if '나약' in hud_report or '중독' in hud_report:
            constraints.append('physical')
        if 'reputation' in hud_report.lower():
            import re
            rep_match = re.search(r'reputation[:\s]+(\d+)', hud_report, re.IGNORECASE)
            if rep_match and int(rep_match.group(1)) < 30:
                constraints.append('authority')

        # 제약이 있는데 극복 장면이 있는가?
        if 'physical' in constraints:
            overcome_keywords = ['이루어', '성공', '압도', '제압']
            has_overcome = any(kw in content for kw in overcome_keywords)

            if has_overcome:
                # 정당화 키워드 체크
                just_kws = ['때문에', '덕분에', '활용', '방법', '대가']
                has_just = any(kw in content for kw in just_kws)

                if not has_just:
                    issues.append({
                        "type": "justification_gap",
                        "description": "제약 극복 장면에 정당화 표현 부족",
                        "location": "본문",
                        "severity": "medium"
                    })

        return issues

    def _check_npc_relationship(self, content: str, encyclopedia: dict) -> list:
        """NPC 관계 일관성 체크"""
        issues = []

        npcs = encyclopedia.get('npcs', [])

        for npc in npcs:
            if not isinstance(npc, dict):
                continue

            name = npc.get('name', '')
            if not name or name not in content:
                continue

            # 관계 상태
            relationship = npc.get('relationship_state', '중립')

            # 경외 상태인데 무시 표현이 있는가?
            if relationship == '경외':
                if '무시' in content or '비웃' in content or '조롱' in content:
                    # 해당 NPC 이름 주변에 있는지 체크
                    npc_idx = content.find(name)
                    if npc_idx != -1:
                        context_range = content[max(0, npc_idx-100):min(len(content), npc_idx+100)]
                        if '무시' in context_range or '비웃' in context_range:
                            issues.append({
                                "type": "npc_relationship",
                                "description": f"{name}는 경외 상태인데 무시 표현 발견",
                                "location": f"NPC: {name}",
                                "severity": "high"
                            })

        return issues

    def _fix_manuscript_issues(self, manuscript: str, critique_result: dict, hud_report: str) -> str:
        """
        [Phase 5.2.1] 문제 발견 시 수정

        Args:
            manuscript: 원고 (JSON)
            critique_result: Self-Critique 결과
            hud_report: HUD 정보

        Returns:
            str: 수정된 원고 (JSON)
        """
        if not critique_result['has_issues']:
            return manuscript

        issues = critique_result['issues']
        severity = critique_result['severity']

        # 심각도 낮으면 수정 스킵
        if severity == "low":
            print("      ℹ️ [Self-Fix] 경미한 문제, 수정 스킵")
            return manuscript

        print(f"      🔧 [Self-Fix] 문제 수정 중... ({len(issues)}개)")

        # 문제 요약
        issue_summary = "\n".join([
            f"- {issue['type']}: {issue['description']}"
            for issue in issues[:5]  # 최대 5개
        ])

        # 수정 프롬프트
        fix_prompt = f"""
[Self-Critique 결과 - 문제 발견]
{issue_summary}

[원본 원고]
{manuscript}

[HUD 정보]
{hud_report}

[수정 지침]
위 문제점을 해결하여 원고를 수정하십시오.
- HUD 모순: 정당화 추가 또는 행동 완화
- 클리셰 과다: 표현 다양화
- 정당화 부족: [제약 인정 → 방법 → 대가 → 결과] 구조 추가
- NPC 관계: 관계 상태에 맞게 수정

⚠️ 전체를 다시 쓰지 말고, 문제 부분만 수정하십시오.
⚠️ 출력 형식은 원본과 동일하게 JSON으로 반환하십시오.
"""

        try:
            fixed = self.ask(fix_prompt, temperature=0.5)
            print("      ✅ [Self-Fix] 수정 완료")
            return fixed
        except Exception as e:
            print(f"      ❌ [Self-Fix] 수정 실패: {e}")
            return manuscript

    def _self_refine(self, manuscript: str, target_areas: list = None) -> str:
        """
        [Phase 5.2.3] Self-Refine: 품질 정제

        88-90점대 아쉬운 점수거나 중요 화일 때 호출
        문학적 품질 향상 (감정선, 문장력, 절벽걸기 등)

        Args:
            manuscript: 원고 (JSON)
            target_areas: 개선 영역 리스트 (옵션)
                ['emotion', 'prose', 'cliffhanger', 'sensory']

        Returns:
            str: 정제된 원고 (JSON)
        """
        print("      ✨ [Self-Refine] 품질 정제 시작...")

        if target_areas is None:
            target_areas = ['emotion', 'prose', 'cliffhanger']

        # 영역별 지침
        area_instructions = {
            'emotion': """
            [감정선 강화]
            - 주인공의 내면 독백 추가 (감정의 깊이)
            - 미묘한 감정 변화 묘사 (분노 → 냉소 → 결의)
            - 감정과 행동의 연결 (왜 그렇게 행동하는가?)
            """,
            'prose': """
            [문장력 향상]
            - 반복 표현 다양화
            - 비유/은유 추가 (시적 표현)
            - 리듬감 있는 문장 구성 (짧-짧-긴 패턴)
            """,
            'cliffhanger': """
            [절벽걸기 강화]
            - 마지막 문장을 강렬하게
            - 미해결 긴장감 조성
            - 독자가 다음 화를 궁금해하게 만들기
            """,
            'sensory': """
            [오감 묘사 강화]
            - 시각적 묘사 (색, 형태, 움직임)
            - 청각적 묘사 (소리, 침묵)
            - 촉각/후각 추가 (질감, 냄새)
            """
        }

        selected_instructions = "\n".join([
            area_instructions.get(area, '')
            for area in target_areas
        ])

        refine_prompt = f"""
[Self-Refine: 문학적 품질 향상]

[원본 원고]
{manuscript}

[개선 영역]
{selected_instructions}

[지침]
위 원고를 아래 기준으로 정제하십시오:
1. 스토리/설정은 절대 변경 금지
2. 위 개선 영역의 표현만 향상
3. 전체 길이는 유지 (±10%)
4. JSON 형식 유지

⚠️ 중요:
- "정제"이지 "재작성"이 아닙니다
- 기존 문장의 70%는 유지하고 30%만 향상
- 과도한 수식어 추가는 금물

출력: 정제된 원고 (JSON 형식)
"""

        try:
            refined = self.ask(refine_prompt, temperature=0.7)
            print("      ✅ [Self-Refine] 정제 완료")
            return refined
        except Exception as e:
            print(f"      ❌ [Self-Refine] 정제 실패: {e}")
            return manuscript