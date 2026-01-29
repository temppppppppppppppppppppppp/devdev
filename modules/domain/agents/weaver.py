# modules/domain/agents/weaver.py (V37 Desire Engine Standard)

import json
from .base_agent import BaseAgent

class Weaver(BaseAgent):
    """
    [V37 Sovereign Desire-Driven Weaver]
    - 결핍 기반 동력 설계: 주인공의 현 상태를 분석해 단기 목적 하달
    - 셀렉션 로직: DNA(트리트먼트) 부실 시 상업적 욕망 자율 선택
    - 피로도 가드: 아크별 긴장도 예산(Tension Budget) 책정
    """

    def __init__(self, context, client, model_tier="gemini-1.5-pro"):
        super().__init__(context, client, model_tier)
        self.cache_name = None  # main_a.py에서 주입됨

    def generate_arc_drive(self, current_arc_dna, analyst_lack_report, grand_objective):
        """[Phase 2 핵심] 이번 아크의 주인공 욕망(Drive)과 전술적 목적 결정"""
        from google.genai import types

        # 1. 기초 데이터 조립
        lack_info = json.dumps(analyst_lack_report, ensure_ascii=False)
        dna_info = json.dumps(current_arc_dna, ensure_ascii=False)

        # 2. 동적 프롬프트 구성
        dynamic_prompt = f"""
        [🚨 MISSION: GENERATE NARRATIVE DRIVE]
        당신은 주인공의 결핍을 폭발적인 동력으로 바꾸는 '욕망 설계자'입니다.

        ### 🧭 상위 지침 (Bible)
        - [장기 목적성]: {grand_objective}

        ### 📊 현시점 팩트 (Analyst Report)
        - [주인공의 결핍]: {lack_info}

        ### 🧬 원천 설계도 (DNA/Treatment)
        - [내용]: {dna_info}

        [수행 지침]
        1. 만약 DNA 내용이 추상적이거나 부실하다면, 'selection_logic_fallback' 규칙에 따라
           [생존/성장/명분] 중 가장 상업적인 단기 목적을 스스로 결정하십시오.
        2. 이번 아크(5~10화) 내에 반드시 쟁취 가능한 구체적 전리품(Reward)을 설정하십시오.
        3. 서사 피로도를 고려하여 'Core' 장면의 비율을 정하십시오.
        4. [Active Villainy]: 적대 세력은 주인공의 행동에 능동적으로 반응해야 합니다.
           - 단순 대기가 아닌, 주인공을 제거하거나 견제하기 위한 '구체적 반격 계획(Reaction Plan)'을 수립하십시오.
           - 적대 세력은 Bible의 NPC 목록에서 hostile/antagonist로 태그된 인물들을 참조하십시오.
        """

        # 3. [V40 Fix] 캐시 활용 분기 처리
        try:
            if self.cache_name:
                # ✅ Case A: 캐시 활성화 (저비용 모드)
                response = self.client.models.generate_content(
                    model=self.primary_model,
                    contents=dynamic_prompt,
                    config=types.GenerateContentConfig(
                        cached_content=self.cache_name,  # 🔥 weaver 캐시 참조
                        temperature=0.5,
                        max_output_tokens=4096,
                        response_mime_type="application/json"
                    )
                )
                drive_data = self._extract_json_robust(response.text)
            else:
                # ⚠️ Case B: 캐시 없음 (Fallback - 전체 프롬프트 재구성)
                drive_data = self._fallback_full_request(dynamic_prompt)

            # 데이터 검증 및 반환
            if drive_data and isinstance(drive_data, dict):
                drive_data['status'] = "LOCKED"
                return drive_data
            else:
                print("⚠️ [Weaver] 유효한 욕망 데이터를 생성하지 못했습니다. 기본값 사용.")
                return {"short_term_objective": "전술적 흐름 유지", "status": "LOCKED"}

        except Exception as e:
            print(f"      🚨 [Weaver Critical] 욕망 생성 실패: {e}. Fallback 시도.")
            return self._fallback_full_request(dynamic_prompt)

    def _fallback_full_request(self, dynamic_prompt):
        """[V40 Fix] 캐시가 없을 때 weaver_rules.json을 읽어 전체 프롬프트 구성"""
        try:
            rules_path = self.context.paths.config / "prompts" / "weaver_rules.json"
            full_context = "[SYSTEM: WEAVER MANIFESTO - FULL LOAD]\n"

            if rules_path.exists():
                rule_data = json.loads(rules_path.read_text(encoding='utf-8'))
                full_context += f"""
Role: {rule_data.get('role', 'Desire-Driven Weaver')}

Core Logic:
{json.dumps(rule_data.get('core_logic', {}), ensure_ascii=False, indent=2)}

Selection Logic Fallback:
{json.dumps(rule_data.get('selection_logic_fallback', {}), ensure_ascii=False, indent=2)}

---
"""

            full_prompt = f"{full_context}\n{dynamic_prompt}"
            raw_res = self.ask(full_prompt, temperature=0.5)
            drive_data = self._extract_json_robust(raw_res)

            if drive_data and isinstance(drive_data, dict):
                drive_data['status'] = "LOCKED"
                return drive_data
            else:
                return {"short_term_objective": "전술적 흐름 유지", "status": "LOCKED"}

        except Exception as e:
            print(f"      ❌ [Weaver] Fallback 구성 실패: {e}")
            return {"short_term_objective": "전술적 흐름 유지", "status": "ERROR_LOCKED"}

    # [Deprecated] 기존 Seed 로직은 하위 호환성을 위해 유지하거나 제거 가능
    def assign_seeds_to_arcs(self, arcs_data, seeds_library):
        """V37 체제에서는 더 이상 사용하지 않음 (Drive 로직으로 대체됨)"""
        pass