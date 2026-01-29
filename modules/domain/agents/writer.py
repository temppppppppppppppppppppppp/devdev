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

        # 2. [프롬프트 조립] Dynamic Context
        # 캐시가 있다면 이 내용만 전송됩니다. (비용 절감 핵심)
        dynamic_prompt = f"""
        {feedback_section}
        {reference_anchor_prompt}
        
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

        ### 📋 1. 씬 설계도 (Blueprint)
        {self._escape_braces(breakdown_doc)}

        ### 🛡️ 2. 실시간 상태 (Dynamic Context)
        [🚨 CRITICAL: 주인공 현재 상태 - 반드시 이 정보를 기반으로 집필하라!]
        {self._escape_braces(hud_report)}

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
                return self._sanitize_leakage(response.text)
            
            else:
                # ⚠️ Case B: 캐시 없음 (Fallback - 전체 프롬프트 재구성)
                # print("      ⚠️ [Writer] 캐시가 없습니다. 전체 프롬프트를 전송합니다.")
                return self._fallback_full_request(dynamic_prompt)

        except Exception as e:
            print(f"      🚨 [Writer Error] 캐시 호출 실패. 일반 모드로 전환합니다: {e}")
            return self._fallback_full_request(dynamic_prompt)

    def _fallback_full_request(self, dynamic_prompt):
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
            return self._sanitize_leakage(self.ask(full_prompt, temperature=0.8))
            
        except Exception as e:
            print(f"      ❌ Fallback 구성 실패: {e}")
            # 최악의 경우라도 집필은 시도
            return self._sanitize_leakage(self.ask(dynamic_prompt, temperature=0.8))

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