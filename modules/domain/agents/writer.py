import json
import re
from pathlib import Path
from google.genai import types
from .base_agent import BaseAgent

class Writer(BaseAgent):
    """[V31 Sovereign Writer] 듀얼 캐시 시스템 대응 및 비용 최적화 집필 엔진
    [V59] 감정선 스켈레톤 시스템 추가
    """

    def __init__(self, context, client, model_tier="gemini-1.5-pro"):
        super().__init__(context, client, model_tier)
        self.cache_name = None # main_a.py에서 주입됨
        self.last_hud_anomalies = None  # [V60] 마지막 HUD 급변 감지 결과 저장 (main_a.py에서 로깅용)

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

    def _check_hud_anomalies_v60(self, current_ep: int) -> dict:
        """
        [V60] HUD 급변 감지 - 내공/경지/부상 상태의 급격한 변화 탐지

        이전 화 대비 비현실적인 HUD 변화를 감지하여 Writer에게 경고

        Args:
            current_ep: 현재 화 번호

        Returns:
            {
                'has_anomalies': bool,
                'anomalies': [
                    {'type': 'internal_energy_spike', 'description': '...', 'recommendation': '...'},
                    ...
                ]
            }
        """
        anomalies = []

        if current_ep < 2:
            return {'has_anomalies': False, 'anomalies': []}

        try:
            # 이전 3화의 HUD 스냅샷 수집
            hud_history = []
            for ep in range(max(1, current_ep - 3), current_ep):
                try:
                    ms_data = self.context.db.get_manuscript(ep)
                    if ms_data and isinstance(ms_data, dict):
                        hud_snapshot = ms_data.get('hud_snapshot', {})
                        if hud_snapshot:
                            hud_history.append({'ep': ep, 'hud': hud_snapshot})
                except Exception:
                    continue

            if not hud_history:
                return {'has_anomalies': False, 'anomalies': []}

            # 가장 최근 HUD
            latest = hud_history[-1]['hud'] if hud_history else {}

            # 1. 내공 급변 감지 (단일 화에서 +500 이상 증가는 비정상)
            if len(hud_history) >= 2:
                prev_hud = hud_history[-2]['hud']

                # 내공 변화
                curr_energy = self._extract_numeric_value(latest.get('internal_energy', 0))
                prev_energy = self._extract_numeric_value(prev_hud.get('internal_energy', 0))

                if curr_energy - prev_energy > 500:
                    anomalies.append({
                        'type': '내공 급상승',
                        'description': f'직전 화 대비 내공 +{curr_energy - prev_energy} 증가 감지 (제{hud_history[-2]["ep"]}화: {prev_energy} → 제{hud_history[-1]["ep"]}화: {curr_energy})',
                        'recommendation': '점진적 성장 또는 특별한 기연(비급 획득, 영약 복용)을 통한 정당화 필요',
                        'severity': 'high'
                    })
                elif curr_energy - prev_energy > 200:
                    anomalies.append({
                        'type': '내공 빠른 성장',
                        'description': f'직전 화 대비 내공 +{curr_energy - prev_energy} 증가 (통상 범위 초과)',
                        'recommendation': '수련 또는 깨달음 장면으로 자연스럽게 정당화 권장',
                        'severity': 'medium'
                    })

                # 2. 경지 급변 감지
                curr_realm = latest.get('realm', '')
                prev_realm = prev_hud.get('realm', '')

                realm_tiers = ['하수', '삼류', '이류', '일류', '초일류', '절정', '화경', '현경', '귀환']

                if curr_realm and prev_realm and curr_realm != prev_realm:
                    try:
                        curr_tier = realm_tiers.index(curr_realm) if curr_realm in realm_tiers else -1
                        prev_tier = realm_tiers.index(prev_realm) if prev_realm in realm_tiers else -1

                        if curr_tier - prev_tier >= 2:
                            anomalies.append({
                                'type': '경지 급상승',
                                'description': f'직전 화 대비 경지 2단계 이상 상승 ({prev_realm} → {curr_realm})',
                                'recommendation': '연속적인 돌파 장면 또는 특수 기연(선천진기, 비급 체득)으로 정당화 필수',
                                'severity': 'critical'
                            })
                    except ValueError:
                        pass

                # 3. 부상 상태 급변 감지
                curr_injury = str(latest.get('causal_injuries', '')).lower()
                prev_injury = str(prev_hud.get('causal_injuries', '')).lower()

                injury_levels = {'정상': 0, '경상': 1, '중상': 2, '중독': 2, '내상': 2, '빈사': 3, '치명상': 3}

                curr_level = 0
                prev_level = 0
                for injury_name, level in injury_levels.items():
                    if injury_name in curr_injury:
                        curr_level = max(curr_level, level)
                    if injury_name in prev_injury:
                        prev_level = max(prev_level, level)

                # 중상/빈사에서 갑자기 정상으로 회복
                if prev_level >= 2 and curr_level == 0:
                    anomalies.append({
                        'type': '부상 급회복',
                        'description': f'직전 화에서 심각한 부상 상태였으나 갑자기 완치됨 ({prev_injury} → {curr_injury})',
                        'recommendation': '치료 과정(의원, 영약, 휴식 기간) 명시적 묘사 필요',
                        'severity': 'high'
                    })

            # 4. 3화 연속 추세 분석 (급격한 성장 곡선)
            if len(hud_history) >= 3:
                energies = [self._extract_numeric_value(h['hud'].get('internal_energy', 0)) for h in hud_history]

                # 3화 동안 총 1000 이상 성장은 비정상
                total_growth = energies[-1] - energies[0]
                if total_growth > 1000:
                    anomalies.append({
                        'type': '연속 급성장',
                        'description': f'최근 3화 동안 내공 +{total_growth} 성장 (과도한 파워 인플레이션)',
                        'recommendation': '성장 속도 조절 또는 장기 수련/비급 습득 스토리라인으로 정당화',
                        'severity': 'medium'
                    })

        except Exception as e:
            print(f"      ⚠️ [V60] HUD 급변 감지 실패: {e}")
            return {'has_anomalies': False, 'anomalies': [], 'error': str(e)}

        return {
            'has_anomalies': len(anomalies) > 0,
            'anomalies': anomalies
        }

    def _extract_numeric_value(self, value) -> int:
        """HUD 값에서 숫자 추출 (문자열/정수 모두 처리)"""
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            # "+100" 또는 "500" 형식 처리
            import re
            match = re.search(r'[+-]?\d+', value)
            if match:
                return int(match.group())
        return 0

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

        ### ⚠️ 출력 형식 (Strict JSON) [V60.22 State Updates Protocol]
        - 제목, 본문, 상태 변화로 구성된 JSON을 출력하라.
        {{
            "title": "에피소드 제목 (한글만)",
            "content": "5,000자 이상의 소설 본문 (줄바꿈은 \\n)",
            "state_updates": {{
                "internal_energy": "70%" (현재 내공 퍼센트, 0~100 사이 숫자),
                "realm": "경지명" 또는 "현상 유지",
                "causal_injuries": "부상 상태 (예: 경상, 중상, 정상)",
                "wealth": "은자 500냥" (현재 총 자산),
                "misunderstanding": 30 (현재 착각 수치, 0~100),
                "obsession": 20 (현재 집착 수치, 0~100),
                "equipment": ["소지 중인 아이템 전체 목록"],
                "martial_arts": ["습득한 무공 전체 목록"]
            }}
        }}

        🔴 [V60.22] internal_energy 필수 규칙:
        - 반드시 0~100 사이 숫자로 작성 (예: "70%", "85%", "50%")
        - 전투 후 소모되면 숫자 감소, 휴식/수련 후 회복되면 증가
        - "현상 유지", "+50" 같은 표현 금지! 반드시 현재 상태를 숫자로!

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

        # [V60] HUD 급변 감지 (내공/경지/부상 상태 급변 경고)
        hud_anomalies = self._check_hud_anomalies_v60(current_ep)
        self.last_hud_anomalies = hud_anomalies  # [V60] 결과 저장 (main_a.py에서 로깅용)
        if hud_anomalies.get('has_anomalies'):
            mandatory_parts.append("\n🚨 [V60 HUD ANOMALY WARNING - 급변 감지]\n")
            for anomaly in hud_anomalies.get('anomalies', []):
                mandatory_parts.append(f"⚠️ {anomaly['type']}: {anomaly['description']}")
                mandatory_parts.append(f"   → 권장: {anomaly['recommendation']}\n")

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
        [Phase 5.2.1 → V49.3 Multi-Round] Self-Critique 적용

        원고에 Self-Critique를 최대 3회 반복 실행하고, 문제가 있으면 수정 후 반환

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
        MAX_CRITIQUE_ROUNDS = 3

        current_manuscript = manuscript
        total_issues_fixed = 0

        for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):
            # Self-Critique 실행 (ep_num 전달)
            critique_result = self._self_critique(current_manuscript, hud_report, encyclopedia, genre_name, ep_num)

            # 문제가 없으면 종료
            if not critique_result['has_issues']:
                if round_num > 1:
                    print(f"      ✅ [Multi-Round] Round {round_num}: 모든 문제 해결됨 (총 {total_issues_fixed}건 수정)")
                break

            # 경미한 문제만 있으면 종료
            if critique_result['severity'] == 'low':
                print(f"      ℹ️ [Multi-Round] Round {round_num}: 경미한 문제만 남음, 수정 스킵")
                break

            # 문제 수정
            print(f"      🔄 [Multi-Round] Round {round_num}/{MAX_CRITIQUE_ROUNDS}: {len(critique_result['issues'])}건 수정 중...")
            current_manuscript = self._fix_manuscript_issues(current_manuscript, critique_result, hud_report)
            total_issues_fixed += len(critique_result['issues'])

            # 마지막 라운드면 루프 종료
            if round_num == MAX_CRITIQUE_ROUNDS:
                print(f"      ⚠️ [Multi-Round] 최대 라운드 도달 (총 {total_issues_fixed}건 수정)")

        # [V49.3] Rubric 기반 최종 품질 평가
        rubric_score = self._evaluate_with_rubric(current_manuscript, genre_name)
        if rubric_score < 3.0:  # 4점 만점 기준 3점 미만이면 경고
            print(f"      ⚠️ [Rubric] 품질 점수 {rubric_score:.1f}/4.0 - 개선 권장")

        return current_manuscript

    def _evaluate_with_rubric(self, manuscript: str, genre_name: str) -> float:
        """
        [V49.3] Rubric 기반 품질 평가

        Args:
            manuscript: 원고 (JSON 문자열)
            genre_name: 장르

        Returns:
            float: 품질 점수 (1.0 ~ 4.0)
        """
        try:
            data = json.loads(manuscript)
            content = data.get('content', '')
        except:
            content = manuscript

        if not content or len(content) < 100:
            return 1.0

        scores = []

        # 1. 감정 표현 평가 (Show vs Tell)
        direct_emotions = ['기뻤다', '슬펐다', '화났다', '놀랐다', '두려웠다', '경악했다', '분노했다']
        direct_count = sum(content.count(e) for e in direct_emotions)
        chars_per_1000 = len(content) / 1000
        direct_rate = direct_count / max(chars_per_1000, 1)

        if direct_rate <= 0.5:
            scores.append(4)  # 거의 Show만 사용
        elif direct_rate <= 1.5:
            scores.append(3)  # Show 위주, 약간 Tell
        elif direct_rate <= 3.0:
            scores.append(2)  # Tell 위주
        else:
            scores.append(1)  # Tell 과다

        # 2. 문장 시작 다양성
        sentences = [s.strip() for s in re.split(r'[.!?]', content) if len(s.strip()) > 5]
        if sentences:
            starters = [s[:2] for s in sentences[:20]]  # 첫 20문장의 시작 2글자
            unique_rate = len(set(starters)) / max(len(starters), 1)
            if unique_rate >= 0.7:
                scores.append(4)
            elif unique_rate >= 0.5:
                scores.append(3)
            elif unique_rate >= 0.3:
                scores.append(2)
            else:
                scores.append(1)
        else:
            scores.append(2)

        # 3. 대화 자연스러움 (대화 비율)
        dialogue_matches = re.findall(r'["\'].*?["\']', content)
        dialogue_chars = sum(len(d) for d in dialogue_matches)
        dialogue_ratio = dialogue_chars / max(len(content), 1)

        if 0.15 <= dialogue_ratio <= 0.40:
            scores.append(4)  # 적정 비율
        elif 0.10 <= dialogue_ratio <= 0.50:
            scores.append(3)
        elif dialogue_ratio > 0:
            scores.append(2)
        else:
            scores.append(1)

        # 4. 오감 묘사 균형
        sensory_keywords = {
            'visual': ['보였다', '빛', '색', '어둠', '그림자'],
            'auditory': ['소리', '울림', '침묵', '들렸다', '속삭'],
            'tactile': ['차가', '뜨거', '거친', '부드러', '통증'],
            'olfactory': ['냄새', '향기', '악취', '피비린']
        }
        sensory_counts = {k: sum(content.count(w) for w in words) for k, words in sensory_keywords.items()}
        active_senses = sum(1 for c in sensory_counts.values() if c > 0)

        if active_senses >= 3:
            scores.append(4)
        elif active_senses >= 2:
            scores.append(3)
        elif active_senses >= 1:
            scores.append(2)
        else:
            scores.append(1)

        # 최종 점수 (평균)
        avg_score = sum(scores) / len(scores) if scores else 2.0
        return round(avg_score, 1)

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
            # [FIX] context.get_anchor() 대신 master_bible 직접 접근
            master_bible = getattr(self.context, 'master_bible', None)
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
                    # [FIX] context.get_manuscript() → context.db.get_manuscript()
                    past_ms = self.context.db.get_manuscript(i)
                    if past_ms:
                        # [FIX] dict에서 content 추출 후 검색
                        content = past_ms.get('content', '') if isinstance(past_ms, dict) else str(past_ms)
                        for name in npc_names:
                            if name in content:
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
                # [FIX] context.get_manuscript() → context.db.get_manuscript()
                past_ms = self.context.db.get_manuscript(i)
                if past_ms:
                    # [FIX] dict에서 content 추출 후 count
                    content = past_ms.get('content', '') if isinstance(past_ms, dict) else str(past_ms)
                    for keyword in cliche_keywords:
                        counts[keyword] += content.count(keyword)
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

    # ========================================================================
    # [V59] 감정선 스켈레톤 시스템
    # ========================================================================

    # [V59] 감정 상태 정의
    EMOTION_STATES = {
        '평온': {'intensity': 0, 'valence': 0},
        '불안': {'intensity': 2, 'valence': -1},
        '긴장': {'intensity': 3, 'valence': -1},
        '분노': {'intensity': 4, 'valence': -2},
        '공포': {'intensity': 4, 'valence': -2},
        '절망': {'intensity': 5, 'valence': -3},
        '기대': {'intensity': 2, 'valence': 1},
        '희열': {'intensity': 4, 'valence': 2},
        '통쾌': {'intensity': 5, 'valence': 3},
        '감동': {'intensity': 4, 'valence': 2},
        '슬픔': {'intensity': 3, 'valence': -2},
        '결의': {'intensity': 4, 'valence': 1},
    }

    # [V59] 장르별 권장 감정 흐름 패턴
    GENRE_EMOTION_PATTERNS = {
        'wuxia': {
            'standard': ['평온', '긴장', '분노', '결의', '통쾌'],
            'training': ['평온', '불안', '긴장', '절망', '결의', '희열'],
            'revenge': ['슬픔', '분노', '결의', '긴장', '통쾌'],
            'crisis': ['평온', '불안', '공포', '절망', '결의'],
        },
        'hunter': {
            'dungeon': ['긴장', '불안', '공포', '결의', '통쾌'],
            'awakening': ['평온', '기대', '긴장', '희열'],
            'boss_fight': ['긴장', '분노', '절망', '결의', '통쾌'],
            'growth': ['평온', '기대', '긴장', '희열', '결의'],
        },
        'investment': {
            'opportunity': ['평온', '기대', '긴장', '희열'],
            'crisis': ['긴장', '불안', '공포', '절망', '결의'],
            'victory': ['긴장', '불안', '결의', '통쾌', '감동'],
            'betrayal': ['평온', '불안', '분노', '결의'],
        }
    }

    def generate_emotion_skeleton(self, blueprint: dict, genre: str = 'wuxia') -> dict:
        """
        [V59] 감정선 스켈레톤 생성 - Blueprint 기반으로 씬별 감정 흐름 설계

        Args:
            blueprint: 에피소드 Blueprint
            genre: 장르

        Returns:
            {
                'scenes': [
                    {'scene_id': 1, 'emotion': '긴장', 'intensity': 3, 'target_emotion': '분노'},
                    ...
                ],
                'overall_arc': '상승형',
                'climax_scene': 4,
                'recommended_pattern': 'revenge'
            }
        """
        scene_breakdown = blueprint.get('scene_breakdown', {})
        if not scene_breakdown:
            return {'scenes': [], 'overall_arc': 'unknown', 'error': 'No scene breakdown'}

        # 1. 씬 유형 분석
        scene_types = self._analyze_scene_types(scene_breakdown, genre)

        # 2. 적합한 감정 패턴 선택
        pattern_name, pattern = self._select_emotion_pattern(scene_types, genre)

        # 3. 씬별 감정 배치
        scenes = []
        num_scenes = len(scene_breakdown)
        pattern_length = len(pattern)

        for i, (scene_name, scene_desc) in enumerate(scene_breakdown.items()):
            # 패턴 인덱스 계산 (씬 수와 패턴 길이가 다를 수 있음)
            pattern_idx = int(i * pattern_length / num_scenes) if num_scenes > 0 else 0
            pattern_idx = min(pattern_idx, pattern_length - 1)

            emotion = pattern[pattern_idx]
            emotion_data = self.EMOTION_STATES.get(emotion, {'intensity': 2, 'valence': 0})

            # 다음 감정 (전환 목표)
            next_idx = min(pattern_idx + 1, pattern_length - 1)
            target_emotion = pattern[next_idx] if next_idx != pattern_idx else None

            scenes.append({
                'scene_id': i + 1,
                'scene_name': scene_name,
                'emotion': emotion,
                'intensity': emotion_data['intensity'],
                'valence': emotion_data['valence'],
                'target_emotion': target_emotion,
                'description': scene_desc[:100] if scene_desc else ''
            })

        # 4. 클라이맥스 씬 식별 (intensity가 가장 높은 씬)
        climax_scene = max(scenes, key=lambda x: x['intensity'])['scene_id'] if scenes else 1

        # 5. 전체 아크 유형 판단
        overall_arc = self._determine_arc_type(scenes)

        return {
            'scenes': scenes,
            'overall_arc': overall_arc,
            'climax_scene': climax_scene,
            'recommended_pattern': pattern_name,
            'pattern_emotions': pattern
        }

    def _analyze_scene_types(self, scene_breakdown: dict, genre: str) -> list:
        """씬 유형 분석"""
        scene_types = []

        # 장르별 키워드
        type_keywords = {
            'wuxia': {
                'battle': ['전투', '대결', '격돌', '검', '공격', '방어'],
                'training': ['수련', '연마', '깨달음', '돌파', '경지'],
                'dialogue': ['대화', '협상', '설득', '정보'],
                'discovery': ['발견', '비밀', '진실', '단서'],
                'revenge': ['복수', '원수', '청산', '응징'],
            },
            'hunter': {
                'battle': ['전투', '몬스터', '보스', '스킬', '공격'],
                'growth': ['레벨업', '성장', '각성', '스킬 획득'],
                'dungeon': ['던전', '게이트', '탐색', '클리어'],
                'social': ['길드', '동료', '대화', '협력'],
            },
            'investment': {
                'analysis': ['분석', '차트', '데이터', '연구'],
                'trade': ['매수', '매도', '거래', '투자'],
                'crisis': ['폭락', '위기', '손실', '공황'],
                'victory': ['수익', '성공', '대박', '승리'],
            }
        }

        genre_keywords = type_keywords.get(genre, type_keywords['wuxia'])

        for scene_name, scene_desc in scene_breakdown.items():
            full_text = f"{scene_name} {scene_desc}".lower()
            detected_type = 'unknown'

            for scene_type, keywords in genre_keywords.items():
                if any(kw in full_text for kw in keywords):
                    detected_type = scene_type
                    break

            scene_types.append(detected_type)

        return scene_types

    def _select_emotion_pattern(self, scene_types: list, genre: str) -> tuple:
        """적합한 감정 패턴 선택"""
        patterns = self.GENRE_EMOTION_PATTERNS.get(genre, self.GENRE_EMOTION_PATTERNS['wuxia'])

        # 씬 유형 빈도 분석
        type_counts = {}
        for t in scene_types:
            type_counts[t] = type_counts.get(t, 0) + 1

        # 가장 빈번한 유형으로 패턴 선택
        dominant_type = max(type_counts, key=type_counts.get) if type_counts else 'standard'

        # 패턴 매칭
        if dominant_type in patterns:
            return dominant_type, patterns[dominant_type]
        else:
            # 기본 패턴
            default_key = list(patterns.keys())[0]
            return default_key, patterns[default_key]

    def _determine_arc_type(self, scenes: list) -> str:
        """전체 감정 아크 유형 판단"""
        if not scenes:
            return 'unknown'

        intensities = [s['intensity'] for s in scenes]

        # 단순 패턴 분석
        first_half = sum(intensities[:len(intensities)//2]) / max(len(intensities)//2, 1)
        second_half = sum(intensities[len(intensities)//2:]) / max(len(intensities) - len(intensities)//2, 1)

        if second_half > first_half + 1:
            return '상승형'  # 후반 긴장 상승
        elif first_half > second_half + 1:
            return '하강형'  # 전반 긴장, 후반 해소
        else:
            return '균형형'  # 전반적으로 균형

    def build_emotion_prompt_injection(self, emotion_skeleton: dict) -> str:
        """
        [V59] 감정 스켈레톤을 프롬프트에 주입할 형태로 변환

        Args:
            emotion_skeleton: generate_emotion_skeleton() 결과

        Returns:
            str: 프롬프트 주입용 텍스트
        """
        if not emotion_skeleton or not emotion_skeleton.get('scenes'):
            return ""

        lines = [
            "\n🎭 [V59 EMOTION SKELETON - 감정선 가이드]\n",
            f"📈 전체 아크: {emotion_skeleton.get('overall_arc', '균형형')}",
            f"🎯 클라이맥스: 씬 {emotion_skeleton.get('climax_scene', '?')}",
            f"📊 추천 패턴: {emotion_skeleton.get('recommended_pattern', 'standard')}\n",
            "씬별 감정 흐름:"
        ]

        for scene in emotion_skeleton.get('scenes', []):
            emotion = scene.get('emotion', '평온')
            intensity = scene.get('intensity', 2)
            target = scene.get('target_emotion')

            # 강도 시각화
            intensity_bar = '▓' * intensity + '░' * (5 - intensity)

            target_str = f" → {target}" if target and target != emotion else ""
            lines.append(f"  씬{scene['scene_id']}: {emotion} [{intensity_bar}]{target_str}")

        lines.append("\n⚠️ 지침:")
        lines.append("- 각 씬에서 지정된 감정을 독자가 느끼도록 묘사하라")
        lines.append("- 감정 전환(→)이 있는 씬은 그 과정을 자연스럽게 표현하라")
        lines.append("- 클라이맥스 씬에서 감정 강도를 최대로 끌어올려라")
        lines.append("- 감정 직접 서술('슬펐다') 대신 행동/묘사로 전달하라")

        return "\n".join(lines)

    def auto_map_emotions_to_manuscript(self, manuscript: str, emotion_skeleton: dict) -> dict:
        """
        [V59] 원고에서 감정 표현 자동 매핑 및 평가

        Args:
            manuscript: 생성된 원고
            emotion_skeleton: 감정 스켈레톤

        Returns:
            {
                'alignment_score': float (0-100),
                'scene_analysis': [...],
                'missing_emotions': [...],
                'suggestions': [...]
            }
        """
        try:
            data = json.loads(manuscript)
            content = data.get('content', '')
        except:
            content = manuscript

        if not content or not emotion_skeleton.get('scenes'):
            return {'alignment_score': 0, 'error': 'No content or skeleton'}

        # 감정 표현 키워드
        emotion_keywords = {
            '평온': ['평화', '고요', '잔잔', '평온', '안정'],
            '불안': ['불안', '초조', '두근', '떨리', '긴장'],
            '긴장': ['긴장', '살기', '위압', '팽팽', '숨막'],
            '분노': ['분노', '화가', '격분', '치밀', '울분'],
            '공포': ['공포', '두려움', '소름', '전율', '무섭'],
            '절망': ['절망', '무력', '좌절', '막막', '암담'],
            '기대': ['기대', '설렘', '희망', '기다'],
            '희열': ['희열', '환희', '황홀', '짜릿', '쾌감'],
            '통쾌': ['통쾌', '시원', '후련', '사이다', '속시원'],
            '감동': ['감동', '뭉클', '눈물', '감격'],
            '슬픔': ['슬픔', '비통', '눈물', '안타', '서러'],
            '결의': ['결의', '각오', '다짐', '결심', '굳건'],
        }

        # 씬별 분석 (원고를 대략적으로 분할)
        num_scenes = len(emotion_skeleton['scenes'])
        chunk_size = len(content) // max(num_scenes, 1)

        scene_analysis = []
        matched_count = 0

        for i, scene_info in enumerate(emotion_skeleton['scenes']):
            # 해당 씬 영역 추출
            start = i * chunk_size
            end = start + chunk_size if i < num_scenes - 1 else len(content)
            scene_text = content[start:end]

            expected_emotion = scene_info['emotion']
            expected_keywords = emotion_keywords.get(expected_emotion, [])

            # 키워드 매칭
            found_keywords = [kw for kw in expected_keywords if kw in scene_text]
            is_matched = len(found_keywords) > 0

            if is_matched:
                matched_count += 1

            # 다른 감정 검출
            detected_emotions = []
            for emotion, keywords in emotion_keywords.items():
                if any(kw in scene_text for kw in keywords):
                    detected_emotions.append(emotion)

            scene_analysis.append({
                'scene_id': scene_info['scene_id'],
                'expected': expected_emotion,
                'detected': detected_emotions,
                'matched': is_matched,
                'found_keywords': found_keywords
            })

        # 정렬 점수 계산
        alignment_score = (matched_count / max(num_scenes, 1)) * 100

        # 누락된 감정 추출
        missing_emotions = [
            s['expected']
            for s in scene_analysis
            if not s['matched']
        ]

        # 개선 제안 생성
        suggestions = []
        for s in scene_analysis:
            if not s['matched']:
                suggestions.append(
                    f"씬{s['scene_id']}: '{s['expected']}' 감정 표현 추가 필요 "
                    f"(키워드 예시: {', '.join(emotion_keywords.get(s['expected'], [])[:3])})"
                )

        return {
            'alignment_score': round(alignment_score, 1),
            'scene_analysis': scene_analysis,
            'missing_emotions': missing_emotions,
            'suggestions': suggestions[:5],  # 최대 5개
            'matched_scenes': matched_count,
            'total_scenes': num_scenes
        }

    def self_review_and_refine(
        self,
        manuscript: str,
        blueprint: dict,
        checklist_feedback: str = "",
        max_refinements: int = 1
    ) -> dict:
        """
        [V60.6] Writer 자가 수정 루프

        생성된 원고를 자가 검토하여 수정본 생성.
        Director 호출 전 품질 향상 목적.

        Args:
            manuscript: 초기 생성된 원고
            blueprint: 블루프린트 (씬 목록 포함)
            checklist_feedback: Pre-Director Checklist 피드백 (있으면)
            max_refinements: 최대 수정 횟수 (기본 1회)

        Returns:
            {
                'refined_manuscript': str,
                'changes_made': list,
                'refinement_count': int,
                'self_review_passed': bool
            }
        """
        result = {
            'refined_manuscript': manuscript,
            'changes_made': [],
            'refinement_count': 0,
            'self_review_passed': False
        }

        if not manuscript or len(manuscript) < 1000:
            return result

        # 씬 정보 추출
        scene_breakdown = blueprint.get('scene_breakdown', {}) if blueprint else {}
        scene_list = list(scene_breakdown.keys()) if scene_breakdown else []

        # 자가 검토 프롬프트 구성
        review_prompt = f"""당신은 무협 소설 원고를 검토하는 편집자입니다.

아래 원고를 검토하고 문제점을 수정한 개선본을 작성하세요.

## 검토 기준
1. **분량**: 4,500자 이상이어야 함 (현재: {len(manuscript)}자)
2. **씬 반영**: Blueprint의 모든 씬이 반영되어야 함 ({len(scene_list)}개 씬: {', '.join(scene_list[:6])})
3. **대화/묘사 균형**: 대화 25-40%, 묘사/서술 60-75%
4. **문장 다양성**: 연속으로 같은 단어로 시작하는 문장 금지
5. **클리셰 회피**: "이를 악물", "눈빛이 날카롭" 등 진부한 표현 최소화
6. **후반부 완성도**: Scene 5-6 (클라이맥스)이 급하게 요약되지 않아야 함

{f"## 사전 체크리스트 피드백{chr(10)}{checklist_feedback}" if checklist_feedback else ""}

## 원본 원고
{manuscript}

## 출력 형식 (JSON)
```json
{{
    "needs_refinement": true/false,
    "issues_found": ["이슈1", "이슈2", ...],
    "refined_manuscript": "수정된 원고 전문 (문제없으면 원본 그대로)"
}}
```

문제가 없으면 needs_refinement: false로 응답하고 refined_manuscript에 원본을 그대로 넣으세요.
문제가 있으면 수정된 원고를 refined_manuscript에 작성하세요.
"""

        current_manuscript = manuscript

        for i in range(max_refinements):
            try:
                # 자가 검토 호출 (빠른 모델 사용)
                response = self.ask(
                    review_prompt.replace(manuscript, current_manuscript) if i > 0 else review_prompt,
                    temperature=0.3  # 낮은 온도로 일관성 확보
                )

                if not response:
                    break

                # JSON 파싱
                review_result = self._extract_json_robust(response)

                if not review_result:
                    break

                needs_refinement = review_result.get('needs_refinement', False)
                issues = review_result.get('issues_found', [])
                refined = review_result.get('refined_manuscript', '')

                if not needs_refinement:
                    result['self_review_passed'] = True
                    break

                if refined and len(refined) >= len(current_manuscript) * 0.8:
                    # 수정본이 원본의 80% 이상이면 채택
                    result['changes_made'].extend(issues)
                    current_manuscript = refined
                    result['refinement_count'] += 1

                    # 수정 후에도 통과 여부 확인
                    if len(issues) <= 1:
                        result['self_review_passed'] = True

            except Exception as e:
                # 자가 검토 실패 시 원본 유지
                break

        result['refined_manuscript'] = current_manuscript
        return result

    def quick_self_check(self, manuscript: str, blueprint: dict) -> dict:
        """
        [V60.6] 빠른 자가 점검 (LLM 없이 Python만)

        LLM 호출 없이 기본적인 품질 지표를 체크.
        self_review_and_refine 호출 여부 결정에 사용.

        Returns:
            {
                'needs_llm_review': bool,
                'quick_issues': list,
                'scores': dict
            }
        """
        issues = []
        scores = {}

        # 1. 분량 체크
        length = len(manuscript)
        scores['length'] = length
        if length < 4000:
            issues.append(f"분량 부족: {length}자 (최소 4000자)")
        elif length < 4500:
            issues.append(f"분량 경계: {length}자")

        # 2. 대화 비율 체크
        dialogue_matches = re.findall(r'"[^"]+?"', manuscript)
        dialogue_chars = sum(len(m) for m in dialogue_matches)
        dialogue_ratio = dialogue_chars / length if length > 0 else 0
        scores['dialogue_ratio'] = dialogue_ratio

        if dialogue_ratio < 0.15:
            issues.append(f"대화 부족: {dialogue_ratio:.0%}")
        elif dialogue_ratio > 0.50:
            issues.append(f"대화 과다: {dialogue_ratio:.0%}")

        # 3. 씬 반영 체크 (키워드 기반)
        scene_breakdown = blueprint.get('scene_breakdown', {}) if blueprint else {}
        if scene_breakdown:
            reflected = 0
            for scene_key, scene_data in scene_breakdown.items():
                if isinstance(scene_data, dict):
                    desc = scene_data.get('description', '') or scene_data.get('title', '')
                else:
                    desc = str(scene_data)

                keywords = re.findall(r'[\w가-힣]{2,}', desc)[:5]
                if any(kw in manuscript for kw in keywords):
                    reflected += 1

            coverage = reflected / len(scene_breakdown) if scene_breakdown else 0
            scores['scene_coverage'] = coverage

            if coverage < 0.5:
                issues.append(f"씬 반영 부족: {coverage:.0%}")

        # 4. 문장 시작어 반복 체크
        sentences = re.split(r'[.?!]\s*', manuscript)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        consecutive_same = 0
        max_consecutive = 0
        for i in range(1, len(sentences)):
            if sentences[i][:2] == sentences[i-1][:2]:
                consecutive_same += 1
                max_consecutive = max(max_consecutive, consecutive_same)
            else:
                consecutive_same = 0

        if max_consecutive >= 4:
            issues.append(f"문장 시작어 {max_consecutive}회 연속 반복")

        # 5. 후반부 분량 체크
        if length > 3000:
            first_half = manuscript[:length // 2]
            second_half = manuscript[length // 2:]
            if len(second_half) < len(first_half) * 0.7:
                issues.append("후반부 분량 부족 (급하게 요약됨)")

        return {
            'needs_llm_review': len(issues) >= 2,
            'quick_issues': issues,
            'scores': scores
        }

    def write_manuscript_by_beats(
        self,
        ep_num: int,
        blueprint: dict,
        master_bible: dict,
        hud_report: str,
        style_guide: str = "",
        feedback: str = "",
        prev_manuscript: str = ""
    ) -> dict:
        """
        [V60.6] Beat 단위 분할 생성

        6개 씬을 한 번에 생성하지 않고 2개 그룹으로 나눠 생성.
        - Phase 1: Scene 1-3 (도입/전개)
        - Phase 2: Scene 4-6 (절정/결말)

        후반부 요약 문제를 해결하고 각 씬에 균등한 분량 배분.

        Args:
            ep_num: 에피소드 번호
            blueprint: 블루프린트 (scene_breakdown 포함)
            master_bible: 설정집
            hud_report: HUD 현황
            style_guide: 스타일 가이드
            feedback: 이전 피드백
            prev_manuscript: 이전 원고

        Returns:
            {
                'title': str,
                'content': str,
                'phase_lengths': [int, int],
                'generation_method': 'beat_split'
            }
        """
        scene_breakdown = blueprint.get('scene_breakdown', {})
        scene_keys = list(scene_breakdown.keys())

        if len(scene_keys) < 4:
            # 씬이 4개 미만이면 일반 생성
            return None

        # 씬 분할
        mid_point = len(scene_keys) // 2
        first_half_scenes = {k: scene_breakdown[k] for k in scene_keys[:mid_point]}
        second_half_scenes = {k: scene_breakdown[k] for k in scene_keys[mid_point:]}

        # 공통 컨텍스트
        bible_root = master_bible.get('MasterBible', master_bible)
        core_identity = bible_root.get('ProjectData', {}).get('CoreIdentity', {})
        protagonist = core_identity.get('protagonist', '주인공')
        desire = core_identity.get('desire', '목표 달성')

        ending_hook = blueprint.get('ending_hook', '') or blueprint.get('cliffhanger', '')
        integrated_scenario = blueprint.get('integrated_scenario', '')

        # Phase 1: 전반부 (Scene 1-3)
        phase1_prompt = f"""당신은 무협 소설 작가입니다. 제 {ep_num} 화의 **전반부**를 집필합니다.

## 설정
- 주인공: {protagonist}
- 핵심 욕망: {desire}
- HUD 현황: {hud_report[:500]}

## 전반부 씬 (반드시 모두 포함)
{json.dumps(first_half_scenes, ensure_ascii=False, indent=2)}

## 전체 시나리오 (참고)
{integrated_scenario[:800]}

## 이전 화 끝 (연결)
{prev_manuscript[-800:] if prev_manuscript else '없음 (첫 화)'}

{f"## 스타일 가이드{chr(10)}{style_guide}" if style_guide else ""}

{f"## 피드백{chr(10)}{feedback}" if feedback else ""}

## 작성 지침
1. 위 씬들을 **모두** 포함하여 약 2,000-2,500자로 작성
2. 각 씬에 대화와 묘사를 균등하게 배분
3. 마지막 문장은 다음 씬으로 자연스럽게 이어지게 작성
4. 문장 시작어를 다양하게 사용

## 출력
원고 본문만 출력하세요. JSON 형식이 아닌 순수 텍스트로."""

        # Phase 2: 후반부 (Scene 4-6)
        phase2_prompt_template = """당신은 무협 소설 작가입니다. 제 {ep_num} 화의 **후반부 (클라이맥스)**를 집필합니다.

## 설정
- 주인공: {protagonist}
- 핵심 욕망: {desire}

## 후반부 씬 (반드시 모두 포함) - 클라이맥스 영역!
{second_half_json}

## 전반부 내용 (이어서 작성)
{phase1_content}

## 엔딩 훅 (반드시 이 방향으로 마무리)
{ending_hook}

## 작성 지침
1. 위 씬들을 **모두** 포함하여 약 2,500-3,000자로 작성
2. 클라이맥스 씬은 더 상세하게! 절대 요약하지 마라
3. 액션 장면은 동작 하나하나를 묘사
4. 마지막은 절벽 걸기(cliffhanger)로 마무리
5. 문장 시작어를 다양하게 사용

## 출력
원고 본문만 출력하세요. JSON 형식이 아닌 순수 텍스트로."""

        try:
            # Phase 1 생성
            phase1_response = self.ask(phase1_prompt, temperature=0.7)
            phase1_content = phase1_response.strip() if phase1_response else ""

            if not phase1_content or len(phase1_content) < 1000:
                return None

            # Phase 2 생성 (Phase 1 결과를 컨텍스트로)
            phase2_prompt = phase2_prompt_template.format(
                ep_num=ep_num,
                protagonist=protagonist,
                desire=desire,
                second_half_json=json.dumps(second_half_scenes, ensure_ascii=False, indent=2),
                phase1_content=phase1_content[-1500:],  # 마지막 1500자만
                ending_hook=ending_hook
            )

            phase2_response = self.ask(phase2_prompt, temperature=0.7)
            phase2_content = phase2_response.strip() if phase2_response else ""

            if not phase2_content or len(phase2_content) < 1000:
                return None

            # 두 파트 결합
            combined_content = f"{phase1_content}\n\n{phase2_content}"

            return {
                'title': f"제 {ep_num} 화",
                'content': combined_content,
                'phase_lengths': [len(phase1_content), len(phase2_content)],
                'generation_method': 'beat_split'
            }

        except Exception as e:
            return None

    def identify_problem_scenes(
        self,
        manuscript: str,
        blueprint: dict,
        reject_reason: str
    ) -> list:
        """
        [V60.6] 문제 씬 식별

        REJECT 사유를 분석하여 어떤 씬에 문제가 있는지 식별.

        Args:
            manuscript: 현재 원고
            blueprint: 블루프린트
            reject_reason: REJECT 사유

        Returns:
            list: 문제 씬 목록 [{'scene_key': str, 'issue': str, 'severity': str}]
        """
        problems = []
        scene_breakdown = blueprint.get('scene_breakdown', {})
        scene_keys = list(scene_breakdown.keys())

        if not scene_keys:
            return problems

        # 원고를 씬 수로 균등 분할
        num_scenes = len(scene_keys)
        section_len = len(manuscript) // num_scenes if num_scenes > 0 else len(manuscript)

        sections = []
        for i in range(num_scenes):
            start = i * section_len
            end = (i + 1) * section_len if i < num_scenes - 1 else len(manuscript)
            sections.append(manuscript[start:end])

        # 문제 패턴 분석
        for i, (scene_key, section) in enumerate(zip(scene_keys, sections)):
            scene_data = scene_breakdown.get(scene_key, {})
            scene_desc = scene_data.get('description', '') if isinstance(scene_data, dict) else str(scene_data)

            issues = []

            # 1. 분량 부족 체크
            avg_section_len = len(manuscript) // num_scenes
            if len(section) < avg_section_len * 0.6:
                issues.append(('분량 부족', 'HIGH'))

            # 2. 키워드 미반영 체크
            keywords = re.findall(r'[\w가-힣]{2,}', scene_desc)[:5]
            matched = sum(1 for kw in keywords if kw in section)
            if keywords and matched / len(keywords) < 0.3:
                issues.append(('씬 내용 미반영', 'HIGH'))

            # 3. REJECT 사유 관련 체크
            if '후반부' in reject_reason and i >= num_scenes - 2:
                issues.append(('후반부 요약 문제', 'CRITICAL'))

            if '폭주' in reject_reason:
                # 해결 키워드가 이 씬에 있는지
                resolution_kw = ['해결', '처치', '승리', '성공', '완료']
                if any(kw in section for kw in resolution_kw):
                    if i < num_scenes // 2:  # 전반부에 해결이 있으면 문제
                        issues.append(('조기 해결 (폭주)', 'CRITICAL'))

            if '정체' in reject_reason:
                # 다음 씬과 키워드 중복도 체크
                if i < len(sections) - 1:
                    next_section = sections[i + 1]
                    words_current = set(re.findall(r'[\w가-힣]{3,}', section))
                    words_next = set(re.findall(r'[\w가-힣]{3,}', next_section))
                    overlap = len(words_current & words_next) / max(len(words_current), 1)
                    if overlap > 0.5:
                        issues.append(('반복 정체', 'HIGH'))

            # 4. 클라이맥스 씬 밀도 체크
            if i >= num_scenes - 2:  # 마지막 2개 씬
                if len(section) < 600:
                    issues.append(('클라이맥스 분량 부족', 'CRITICAL'))

            # 문제 기록
            for issue, severity in issues:
                problems.append({
                    'scene_key': scene_key,
                    'scene_index': i + 1,
                    'issue': issue,
                    'severity': severity,
                    'current_length': len(section)
                })

        # 심각도 순 정렬
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}
        problems.sort(key=lambda x: severity_order.get(x['severity'], 3))

        return problems

    def partial_rewrite(
        self,
        manuscript: str,
        blueprint: dict,
        problem_scenes: list,
        max_scenes_to_rewrite: int = 2
    ) -> dict:
        """
        [V60.6] 부분 수정 (특정 씬만 재작성)

        전체 원고를 재생성하지 않고 문제 씬만 재작성.

        Args:
            manuscript: 현재 원고
            blueprint: 블루프린트
            problem_scenes: identify_problem_scenes() 결과
            max_scenes_to_rewrite: 최대 재작성 씬 수

        Returns:
            {
                'content': str,  # 수정된 원고
                'rewritten_scenes': list,  # 재작성된 씬 목록
                'generation_method': 'partial_rewrite'
            }
        """
        if not problem_scenes:
            return None

        scene_breakdown = blueprint.get('scene_breakdown', {})
        scene_keys = list(scene_breakdown.keys())
        num_scenes = len(scene_keys)

        if num_scenes == 0:
            return None

        # 원고 분할
        section_len = len(manuscript) // num_scenes
        sections = []
        for i in range(num_scenes):
            start = i * section_len
            end = (i + 1) * section_len if i < num_scenes - 1 else len(manuscript)
            sections.append(manuscript[start:end])

        # 재작성할 씬 선택 (심각도 높은 것 우선)
        scenes_to_rewrite = problem_scenes[:max_scenes_to_rewrite]
        rewritten_indices = set()

        for problem in scenes_to_rewrite:
            scene_idx = problem.get('scene_index', 1) - 1
            if scene_idx < 0 or scene_idx >= num_scenes:
                continue

            scene_key = scene_keys[scene_idx]
            scene_data = scene_breakdown.get(scene_key, {})

            # 이전/이후 씬 컨텍스트
            prev_context = sections[scene_idx - 1][-500:] if scene_idx > 0 else ""
            next_context = sections[scene_idx + 1][:300] if scene_idx < num_scenes - 1 else ""

            # 재작성 프롬프트
            rewrite_prompt = f"""현재 씬을 개선하여 재작성하세요.

## 현재 씬 ({scene_key})
{sections[scene_idx]}

## 문제점
{problem.get('issue', '품질 미달')}

## 씬 설계
{json.dumps(scene_data, ensure_ascii=False, indent=2) if isinstance(scene_data, dict) else scene_data}

## 이전 씬 끝 (자연스럽게 연결)
{prev_context if prev_context else '(첫 번째 씬)'}

## 다음 씬 시작 (이 방향으로 마무리)
{next_context if next_context else '(마지막 씬 - 절벽걸기로 마무리)'}

## 개선 지침
1. 분량을 800자 이상으로 확보
2. 씬 설계의 핵심 요소를 모두 반영
3. 이전/다음 씬과 자연스럽게 연결
4. 대화와 묘사의 균형 유지
5. {'절벽걸기로 마무리' if scene_idx == num_scenes - 1 else '다음 씬으로 자연스럽게 연결'}

## 출력
개선된 씬 본문만 출력하세요."""

            try:
                rewritten = self.ask(rewrite_prompt, temperature=0.6)
                if rewritten and len(rewritten.strip()) > len(sections[scene_idx]) * 0.8:
                    sections[scene_idx] = rewritten.strip()
                    rewritten_indices.add(scene_idx)
            except Exception:
                continue

        if not rewritten_indices:
            return None

        # 재조합
        combined = "\n\n".join(sections)

        return {
            'title': f"제 {blueprint.get('ep_num', '?')} 화",
            'content': combined,
            'rewritten_scenes': [scene_keys[i] for i in rewritten_indices],
            'generation_method': 'partial_rewrite'
        }