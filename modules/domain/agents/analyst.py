"""
#레거시 에이전트 - Analyst
=========================
Stage 2 진짜 주인: FourPhaseArcGenerator (four_phase_arc_generator.py)
plan_single_arc_v20은 독립 API로 유지 (오케스트레이터 fallback 호출 제거됨).

여전히 사용되는 기능:
- plan_single_volume_v20: Stage 1 Volume Strategy
- enrich_raw_block_async: Raw block enrichment
- stitch_joints: Arc joints stitching
- get_lack_report: Lack report

#레거시 태그: Arc 생성 관련 코드
"""

import asyncio
import json
import logging
import os
import re

from modules.core.constants import HUDKeys

# [V65] 프롬프트 외부화
from .analyst_prompt_api import (
    get_analyst_self_critic_prompt,
    get_calibration_prompt,
    get_enrich_block_prompt_v30,
    get_plan_arc_prompt_v25,
    get_plan_volume_prompt_v25,
    get_post_stitch_repair_prompt,
    get_recovery_prompt,
    get_surgery_prompt,
    get_volume_strategy_prompt,
)
from .base_agent import BaseAgent

# [V49.4] Structured Output Schema
try:
    from modules.core.response_schemas import ARC_DESIGN_SCHEMA

    SCHEMA_ENABLED = True
except ImportError:
    SCHEMA_ENABLED = False
    ARC_DESIGN_SCHEMA = None

# [V65] 모듈-레벨 프롬프트 상수 5개는 프롬프트 모듈로 이동됨


class Analyst(BaseAgent):
    """
    [V37 Sovereign Strategist - 0124 Manifesto]
    - 3대 지표 분석: 무력(Martial), 경제(Economy), 권위(Authority) 결핍 진단
    - 위버 동력 수혈: 주인공의 욕망을 점화할 '결핍 리포트' 생성
    - 서사 수술: ARC_RECONSTRUCTION을 통한 인과율 보정

    #레거시 노트:
    - Stage 2 Arc 생성: FourPhaseArcGenerator가 진짜 주인
    - plan_single_arc_v20: FourPhase 실패 시 fallback으로만 사용
    - Stage 1 Volume (plan_single_volume_v20): 여전히 활성
    """

    # region //volume planning
    def plan_single_volume_v20(
        self,
        vol_no,
        master_bible,
        treatment_raw_part,
        previous_volumes_context="",
        structured_context="",
        protagonist_name: str = None,
    ):
        """[Stage 1] 10권 전략 수립 (가공 데이터 보존 및 슬라이싱 단일화)"""
        bible_root = master_bible.get("MasterBible", master_bible)
        assets = bible_root.get("AssetLibrary", {})

        # [V61.2 Fix] 주인공 이름 추출 - 장르별 HUD 탐색
        if not protagonist_name:
            try:
                genre = getattr(self.context, "genre", "") or ""
                protagonist_name = HUDKeys.get_protagonist_name(bible_root, genre)
            except Exception:
                protagonist_name = "주인공"

        # [V60.88] 주인공 설정 추출 (인지 목적, 제약 최소화)
        protagonist_config = bible_root.get("protagonist_config", {})
        world_origin = protagonist_config.get("world_origin", "원시인")
        incarnation_type = protagonist_config.get("incarnation_type", "회귀자")
        protagonist_config_text = f"- 세계 출신: {world_origin}\n- 환생 유형: {incarnation_type}"
        if world_origin == "원시인":
            protagonist_config_text += "\n⚠️ 현대 용어 사용 금지"
        else:
            protagonist_config_text += "\n📝 주인공은 현대 사회를 알고 있음"
        if incarnation_type == "회귀자":
            protagonist_config_text += "\n🔄 미래를 알고 있음 (합리적 이유 없이는 내면 독백으로 처리)"
        elif incarnation_type == "빙의자":
            protagonist_config_text += "\n👤 원래 인물의 기억/관계를 의식"
        elif incarnation_type == "환생자":
            protagonist_config_text += "\n👶 전생의 기억이 있음"

        # 1. 권역 데이터 통합 추출 (Block 5개 단위)
        # treatment_raw_part가 리스트면 그대로 쓰고, 문자열이면 JSON으로 변환
        if isinstance(treatment_raw_part, str):
            try:
                treatment_data = json.loads(treatment_raw_part)
            except (json.JSONDecodeError, ValueError) as e:
                # [V44] JSON 파싱 실패 경고 추가
                logging.warning(f"⚠️ [Analyst] treatment 데이터 JSON 파싱 실패: {str(e)[:50]}")
                treatment_data = []  # 변환 실패 시 빈 리스트
        else:
            treatment_data = treatment_raw_part

        target_blocks = treatment_data
        target_blocks_str = json.dumps(target_blocks, ensure_ascii=False, indent=2)

        # 2. 프롬프트 데이터 안전화 및 주입
        prompt = get_plan_volume_prompt_v25(
            vol_no=vol_no,
            genre_prompt=self.context.guard.get_v20_purism_prompt(),
            structured_context=self._escape_braces(structured_context),
            previous_context=self._escape_braces(previous_volumes_context),
            target_blocks=self._escape_braces(target_blocks_str),
            treatment_raw_part=self._escape_braces(target_blocks_str),
            assets=self._escape_braces(json.dumps(assets, ensure_ascii=False)),
            protagonist_config=self._escape_braces(protagonist_config_text),  # [V60.88]
            protagonist_name=protagonist_name,  # [V60.93]
        )
        # Guard against prompt-loader contamination returning overly generic text (e.g., "prompt").
        if isinstance(prompt, str) and protagonist_config_text:
            if world_origin not in prompt and incarnation_type not in prompt:
                prompt = f"{prompt}\n\n[PROTAGONIST_CONFIG]\n{protagonist_config_text}"

        response = self.ask(prompt, temperature=0.7)
        # [V60.2] DEBUG → 조건부 로깅 (프로덕션에서는 비활성화)
        if os.getenv("DEBUG_MODE", "").lower() == "true":
            logging.warning(f"\n--- [Vol {vol_no} AI Raw Response] ---\n{response[:500]}...\n")

        # 3. 🚨 결과물 정제 및 안전장치 가동
        result = self._extract_json_robust(response)

        # 🔥 [Vol Safety] AI가 전술(tactical) 키값을 줘도 전략(strategy)으로 강제 변환
        if "tactical_doc" in result and "strategy_doc" not in result:
            result["strategy_doc"] = result["tactical_doc"]

        # [⬇️ 추가할 코드: 필수 키 누락 방지 가드]
        # AI가 cider_score를 누락했을 경우 기본값 0 또는 50을 할당하여 KeyError 방지
        if "cider_score" not in result:
            logging.warning(f"⚠️ [Auto-Repair] Vol {vol_no}: 누락된 'cider_score'를 기본값(0)으로 보정했습니다.")
            result["cider_score"] = 0

        # vol_no가 누락되었을 경우를 대비한 보정
        if "vol_no" not in result:
            result["vol_no"] = vol_no

        # 🚨 [수정 포인트] 가공된 'result' 객체를 그대로 반환해야 합니다!
        return result

    # endregion

    # region //arc planning

    # ═══════════════════════════════════════════════════════════════
    # [V60] Arc 상태 계승 검증 메서드
    # ═══════════════════════════════════════════════════════════════

    def _validate_arc_state_continuity_v60(self, current_arc: dict, prev_arc: dict) -> dict:
        """
        [V60] 이전 Arc의 종료 상태가 현재 Arc의 시작 상태로 정확히 계승되었는지 검증

        Args:
            current_arc: 현재 Arc 설계 데이터
            prev_arc: 이전 Arc 설계 데이터

        Returns:
            {
                "valid": bool,
                "issues": list,
                "severity": "CRITICAL" | "WARNING" | "NONE",
                "auto_corrections": dict
            }
        """
        if not prev_arc or not isinstance(prev_arc, dict):
            return {"valid": True, "issues": [], "severity": "NONE", "auto_corrections": {}}

        issues = []
        auto_corrections = {}

        # 이전 Arc의 종료 상태
        prev_constraints = prev_arc.get("state_constraints", {})
        prev_end = prev_constraints.get("arc_end_state", {})
        prev_joint = prev_constraints.get("joint_docs", {})

        # 현재 Arc의 시작 상태
        curr_constraints = current_arc.get("state_constraints", {})
        curr_start = curr_constraints.get("arc_start_state", {})

        # 1. 위치 검증
        prev_location = prev_joint.get("final_location") or prev_end.get("location", "")
        curr_location = curr_start.get("location", "")
        if prev_location and curr_location and prev_location != curr_location:
            # 자동 보정 시도
            issues.append(f"CRITICAL: 위치 단절 - Arc 끝 '{prev_location}' → Arc 시작 '{curr_location}'")
            auto_corrections["location"] = prev_location

        # 2. 소지품 검증
        prev_inventory = prev_joint.get("physical_inventory", []) or prev_end.get("equipment", [])
        curr_inventory = curr_start.get("equipment", [])

        if isinstance(prev_inventory, str):
            prev_inventory = [prev_inventory] if prev_inventory else []
        if isinstance(curr_inventory, str):
            curr_inventory = [curr_inventory] if curr_inventory else []

        prev_set = set(prev_inventory) if prev_inventory else set()
        curr_set = set(curr_inventory) if curr_inventory else set()

        missing_items = prev_set - curr_set
        if missing_items:
            issues.append(f"CRITICAL: 아이템 손실 - {missing_items} (이전 Arc에서 소지 중이던 아이템)")
            auto_corrections["missing_items"] = list(missing_items)

        # 3. 내공/상태 검증
        prev_energy = prev_end.get("internal_energy", 0)
        curr_energy = curr_start.get("internal_energy", 0)

        try:
            prev_e = int(str(prev_energy).replace("%", "")) if prev_energy else 0
            curr_e = int(str(curr_energy).replace("%", "")) if curr_energy else 0

            # 회복 없이 증가는 위반 (30% 이상 급증)
            if curr_e > prev_e + 30:
                issues.append(f"WARNING: 내공 급증 감지 ({prev_e}% → {curr_e}%) - 회복 근거 필요")
        except (ValueError, TypeError):
            pass

        # 4. 부상 상태 검증
        prev_injuries = str(prev_end.get("injuries", "") or prev_end.get("status", ""))
        curr_injuries = str(curr_start.get("injuries", "") or curr_start.get("status", ""))

        if prev_injuries and not curr_injuries:
            if "중상" in str(prev_injuries) or "부상" in str(prev_injuries):
                issues.append(
                    f"WARNING: 부상 상태 누락 - 이전 Arc 종료 시 '{prev_injuries}' 상태였으나 현재 Arc 시작에 반영 안 됨"
                )

        # 심각도 결정
        critical_count = sum(1 for i in issues if i.startswith("CRITICAL"))
        if critical_count > 0:
            severity = "CRITICAL"
        elif issues:
            severity = "WARNING"
        else:
            severity = "NONE"

        return {
            "valid": critical_count == 0,
            "issues": issues,
            "severity": severity,
            "auto_corrections": auto_corrections,
        }

    def _validate_tactical_doc_continuity_v60(self, tactical_doc: str, ep_count: int) -> dict:
        """
        [V60] Arc 내 화 간 연속성 검증 - 아이템/부상 상태 추적

        Args:
            tactical_doc: 전술 문서 텍스트
            ep_count: 예상 에피소드 수

        Returns:
            {
                "valid": bool,
                "issues": list,
                "item_tracking": dict,
                "injury_tracking": dict
            }
        """
        # [V60.36 FIX] tactical_doc이 dict인 경우 문자열로 변환
        if isinstance(tactical_doc, dict):
            tactical_doc = tactical_doc.get("tactical_doc", "") or json.dumps(tactical_doc, ensure_ascii=False)
        if not isinstance(tactical_doc, str):
            tactical_doc = str(tactical_doc) if tactical_doc else ""

        issues = []
        item_states = {}  # {item: 'acquired' | 'lost'}
        injury_states = {}  # {ep: 'injured' | 'recovered' | 'normal'}

        for i in range(1, ep_count + 1):
            # 각 화 섹션 추출
            pattern = rf"제\s*{i}\s*화.*?(?=제\s*{i + 1}\s*화|$)"
            ep_match = re.search(pattern, tactical_doc, re.DOTALL | re.IGNORECASE)

            if not ep_match:
                continue

            section = ep_match.group(0)

            # 1. 아이템 획득 추적
            acquired_patterns = [
                r"(.+?)(?:을|를)\s*(?:획득|집어\s*들|뽑아\s*들|챙기|주워)",
                r"(.+?)(?:을|를)\s*(?:받|하사받|전달받|넘겨받)",
            ]
            for pattern in acquired_patterns:
                matches = re.findall(pattern, section)
                for item in matches:
                    item = item.strip()
                    if len(item) >= 2 and len(item) <= 15:
                        if item in item_states and item_states[item] == "lost":
                            issues.append(f"EP{i}: 이미 잃어버린 '{item}' 재획득 시도")
                        item_states[item] = "acquired"

            # 2. 아이템 손실 추적
            lost_patterns = [
                r"(.+?)(?:을|를)\s*(?:잃|파괴|손상|부러)",
                r"(.+?)(?:이|가)\s*(?:부러지|망가지|사라지)",
            ]
            for pattern in lost_patterns:
                matches = re.findall(pattern, section)
                for item in matches:
                    item = item.strip()
                    if len(item) >= 2 and len(item) <= 15:
                        if item not in item_states or item_states[item] != "acquired":
                            issues.append(f"EP{i}: 미소지 아이템 '{item}' 손실 시도")
                        item_states[item] = "lost"

            # 3. 부상 상태 추적
            if re.search(r"중상|부상|다치|피를 흘리", section):
                injury_states[i] = "injured"
            elif re.search(r"회복|치료|완치|상처가 아물", section):
                injury_states[i] = "recovered"
            else:
                injury_states[i] = "normal"

            # 4. 부상 상태 연속성 검증
            if i > 1:
                prev_injury = injury_states.get(i - 1, "normal")
                curr_injury = injury_states.get(i, "normal")

                # 부상 상태에서 격렬한 행동
                if prev_injury == "injured" and curr_injury == "normal":
                    intense_actions = re.findall(r"전투|비무|격투|도약|비약|질주", section)
                    if len(intense_actions) >= 2:
                        issues.append(f"EP{i}: 부상 미회복 상태에서 과도한 행동 ({len(intense_actions)}회 격렬 행동)")

        return {
            "valid": len([i for i in issues if "CRITICAL" in i or "재획득" in i or "미소지" in i]) == 0,
            "issues": issues,
            "item_tracking": item_states,
            "injury_tracking": injury_states,
        }

    def _auto_correct_joint_docs_v60(self, tactical_doc: str, arc_data: dict) -> dict:
        """
        [V60] 마지막 화 내용에서 joint_docs 자동 추출하여 보정

        Args:
            tactical_doc: 전술 문서 텍스트
            arc_data: Arc 설계 데이터

        Returns:
            보정된 arc_data
        """
        # [V60.36 FIX] tactical_doc이 dict인 경우 문자열로 변환
        if isinstance(tactical_doc, dict):
            tactical_doc = tactical_doc.get("tactical_doc", "") or json.dumps(tactical_doc, ensure_ascii=False)
        if not isinstance(tactical_doc, str):
            tactical_doc = str(tactical_doc) if tactical_doc else ""

        # 마지막 화 섹션 추출
        ep_sections = re.findall(r"제\s*(\d+)\s*화.*?(?=제\s*\d+\s*화|$)", tactical_doc, re.DOTALL)
        if not ep_sections:
            return arc_data

        # 마지막 화 번호 및 내용 찾기
        last_match = list(re.finditer(r"제\s*(\d+)\s*화", tactical_doc))
        if not last_match:
            return arc_data

        last_ep_start = last_match[-1].start()
        last_section = tactical_doc[last_ep_start:]

        # 1. 최종 위치 추출
        location_patterns = [
            r"(?:도착|도달|들어서|위치한?)\s*(?:곳은?\s*)?([가-힣\w]+(?:전|관|각|루|궁|산|촌|장|성|문)?)",
            r"([가-힣\w]+(?:전|관|각|루|궁|산|촌|장|성|문))(?:에서|에|으로)\s*(?:향하|떠나|이동)",
        ]
        final_location = None
        for pattern in location_patterns:
            match = re.search(pattern, last_section[-500:])  # 마지막 500자에서 검색
            if match:
                final_location = match.group(1)
                break

        # 2. 최종 소지품 추출
        inventory_patterns = [
            r"(?:손에|허리에|품속에|등에)\s*([가-힣\w]+?)(?:을|를|이|가)?\s*(?:들고|쥐고|차고|지니)",
        ]
        final_inventory = []
        for pattern in inventory_patterns:
            matches = re.findall(pattern, last_section)
            for item in matches:
                if len(item) >= 2 and len(item) <= 15 and item not in final_inventory:
                    final_inventory.append(item)

        # 3. arc_data 보정
        if "state_constraints" not in arc_data:
            arc_data["state_constraints"] = {}
        if "joint_docs" not in arc_data["state_constraints"]:
            arc_data["state_constraints"]["joint_docs"] = {}

        joint_docs = arc_data["state_constraints"]["joint_docs"]

        if final_location:
            existing_location = joint_docs.get("final_location", "")
            if not existing_location or existing_location != final_location:
                logging.warning(f"🔧 [V60] joint_docs 위치 보정: '{existing_location}' → '{final_location}'")
                joint_docs["final_location"] = final_location

        if final_inventory:
            existing_inventory = joint_docs.get("physical_inventory", [])
            if not existing_inventory:
                logging.info(f"🔧 [V60] joint_docs 소지품 보정: {final_inventory}")
                joint_docs["physical_inventory"] = final_inventory

        return arc_data

    def plan_single_arc_v20(
        self,
        arc_no,
        vol_strategy,
        prev_block,
        curr_block,
        next_block,
        ep_start,
        prev_arc_context="",
        assets=None,
        full_roadmap="",
        assigned_seeds=None,
        feedback="",
        recent_patterns=None,
        protagonist_name=None,
        state_tracker=None,
    ):  # [V60.32] 주인공 이름, [V60.95] state_tracker 추가
        """
        #레거시 - FourPhaseArcGenerator.generate()가 Stage 2 진짜 주인
        이 메서드는 FourPhase 실패 시 fallback으로만 호출됨.

        [V31 Sovereign] 3중 캐시 대응: 선 압축 후 설계 방식의 고해상도 전략 엔진
        - 캐시 존재 시: 지침 치환 후 서버 캐시 참조 (비용 90% 절감)
        - 호출 실패 시: 즉시 Full-Text로 자동 복구하여 서사 밀도 보존 (Fallback Safety)
        [V60] Arc 상태 계승 검증 + 화 간 모순 탐지 + Joint Docs 자동 보정
        """
        import json

        from google.genai import types

        # 1. [V38] 패턴 고착화 방지 (Negative Constraints)
        # "2번 이상 연속 사용 금지" -> 직전 패턴(Last Pattern) 재사용 원천 차단
        banned_msg = ""
        if recent_patterns and len(recent_patterns) > 0:
            last_pattern = recent_patterns[-1]  # 가장 최근 사용한 패턴
            banned_msg = f"\n[🚨 ABSOLUTE BAN]: 직전에 사용된 서사 패턴 '{last_pattern}'의 재사용을 절대 금지한다. 반드시 다른 아키타입을 선택하여 서사의 변주를 주어라."

            # 만약 3회 이상 같은 계열(예: 전투)이 반복되었다면 추가 경고
            if len(recent_patterns) >= 2 and recent_patterns[-1] == recent_patterns[-2]:
                banned_msg += "\n[🚨 WARNING]: 유사한 전개가 반복되고 있다. 이번 아크에서는 '전투'보다는 '정치', '미스터리', '기연' 등 완전히 다른 장르적 해법을 제시하라."

        # 2. 복선 데이터를 연출 미션 텍스트로 변환 (+ Ban Msg 통합)
        if assigned_seeds:
            mission_list = [
                f"- [{s.get('action', '지정')}] ID: {s.get('seed_id', 'N/A')} | 논리: {s.get('logic', 'N/A')}"
                for s in assigned_seeds
            ]
            seeds_info = "### 🎯 이번 아크 서사 미션:\n" + "\n".join(mission_list) + banned_msg
        else:
            seeds_info = f"### 🎯 이번 아크 서사 미션:\n- 특이사항 없음 (순수 줄거리 전개 집중){banned_msg}"

        # 2. 페이싱 계산 (Pre-Compression 로직 유지)
        try:
            clean_arc_no = int(arc_no)
            vol_no = ((clean_arc_no - 1) // 5) + 1
        except (ValueError, TypeError):
            clean_arc_no, vol_no = arc_no, "Unknown"

        # [V60.31] 페이싱 계산 - Block 구조에 맞게 수정
        # [V60.62] 3가지 구조 모두 대응: flatten, nested content, plot_roadmap
        original_guess = 5
        if isinstance(curr_block, dict):
            content_parts = []

            # [V60.62] 1. 최상위 레벨에서 직접 추출 (LLM이 flatten된 구조로 반환)
            for key in ["context", "event_villain", "solution", "reward"]:
                if curr_block.get(key) and isinstance(curr_block.get(key), str):
                    content_parts.append(str(curr_block[key]))

            # 2. content 객체 내부에서 추출 (nested 구조)
            content_obj = curr_block.get("content", {})
            if isinstance(content_obj, dict):
                for key in ["context", "event_villain", "solution", "reward"]:
                    if content_obj.get(key):
                        content_parts.append(str(content_obj[key]))
            elif isinstance(content_obj, str):
                content_parts.append(content_obj)

            # 3. [V62.2] 레거시 호환: raw_data 래핑 구조 (기존 DB)
            raw_data = curr_block.get("raw_data", {})
            if isinstance(raw_data, dict):
                rd_content = raw_data.get("content", {})
                if isinstance(rd_content, dict):
                    for key in ["context", "event_villain", "solution", "reward"]:
                        if rd_content.get(key):
                            content_parts.append(str(rd_content[key]))
                # raw_data 내 genre_ext도 추출
                rd_ge = raw_data.get("genre_ext", {})
                if isinstance(rd_ge, dict):
                    for v in rd_ge.values():
                        if isinstance(v, str) and v:
                            content_parts.append(v)
                if raw_data.get("title"):
                    content_parts.append(str(raw_data["title"]))

            # 4. [V62.2] genre_ext에서도 추출 (장르 특화 정보)
            genre_ext = curr_block.get("genre_ext", {})
            if isinstance(genre_ext, dict):
                for v in genre_ext.values():
                    if isinstance(v, str) and v:
                        content_parts.append(v)

            # 5. 최상위 title
            if curr_block.get("title"):
                content_parts.append(str(curr_block["title"]))

            content_sample = " ".join(content_parts)
            content_len = len(content_sample)

            # 내용 길이/복잡도에 따라 화수 추정
            # - 500자 미만: 간단한 블록 → 3화
            # - 500~1000자: 표준 블록 → 4화
            # - 1000~1500자: 복잡한 블록 → 5화
            # - 1500자 이상: 매우 복잡 → 6화
            if content_len < 500:
                original_guess = 4  # → 3화
            elif content_len < 1000:
                original_guess = 5  # → 4화
            elif content_len < 1500:
                original_guess = 6  # → 5화
            else:
                original_guess = 7  # → 6화 (max)

        # 실제 타겟 화수는 추정치보다 1화 적게 잡아 긴장감 유도 (3~7화 제한)
        target_ep_count = max(3, min(7, original_guess - 1))

        # [V60.31] Block 빈약 경고 - 화당 200자 이상 권장
        # [V60.59] plot_roadmap 구조 대응: raw_data.content에서 추출
        min_content_per_ep = 200
        if isinstance(curr_block, dict):
            content_parts = []

            # [V60.62] 1. 최상위 레벨에서 직접 추출 (LLM이 flatten된 구조로 반환하는 경우)
            for key in ["context", "event_villain", "solution", "reward"]:
                if curr_block.get(key) and isinstance(curr_block.get(key), str):
                    content_parts.append(str(curr_block[key]))

            # 2. content 객체 내부에서 추출 (nested 구조인 경우)
            content_obj = curr_block.get("content", {})
            if isinstance(content_obj, dict):
                for key in ["context", "event_villain", "solution", "reward"]:
                    if content_obj.get(key):
                        content_parts.append(str(content_obj[key]))
            elif isinstance(content_obj, str):
                content_parts.append(content_obj)

            # 3. [V62.2] 레거시 호환: raw_data 래핑 구조 (기존 DB)
            raw_data = curr_block.get("raw_data", {})
            if isinstance(raw_data, dict):
                rd_content = raw_data.get("content", {})
                if isinstance(rd_content, dict):
                    for key in ["context", "event_villain", "solution", "reward"]:
                        if rd_content.get(key):
                            content_parts.append(str(rd_content[key]))
                rd_ge = raw_data.get("genre_ext", {})
                if isinstance(rd_ge, dict):
                    for v in rd_ge.values():
                        if isinstance(v, str) and v:
                            content_parts.append(v)
                if raw_data.get("title"):
                    content_parts.append(str(raw_data["title"]))

            # 4. [V62.2] genre_ext에서도 추출 (장르 특화 정보)
            genre_ext = curr_block.get("genre_ext", {})
            if isinstance(genre_ext, dict):
                for v in genre_ext.values():
                    if isinstance(v, str) and v:
                        content_parts.append(v)

            # 5. 최상위 title
            if curr_block.get("title"):
                content_parts.append(str(curr_block["title"]))

            content_len = len(" ".join(content_parts))

            if content_len < target_ep_count * min_content_per_ep:
                logging.warning(
                    f"⚠️ [V60.31] Block 빈약 경고: {content_len}자 / {target_ep_count}화 = 화당 {content_len // target_ep_count}자 (권장 200자+)"
                )

        # 3. [V43] 장르별 라이브러리 로드 - 장르에 맞는 서사 패턴 사용
        current_genre = self._get_current_genre()
        lib_path = self._get_genre_library_path(current_genre)

        if lib_path.exists():
            try:
                lib_data = json.loads(lib_path.read_text(encoding="utf-8"))
                intro_lib_full = json.dumps(lib_data.get("intro_patterns", {}), ensure_ascii=False)
                dev_lib_full = json.dumps(lib_data.get("narrative_archetypes", {}), ensure_ascii=False)
                ending_lib_full = json.dumps(lib_data.get("ending_patterns", {}), ensure_ascii=False)
                trans_lib_full = json.dumps(lib_data.get("transition_patterns", {}), ensure_ascii=False)
                archetype_lib_full = dev_lib_full
                logging.warning(f"📚 [Analyst] {current_genre} 장르 라이브러리 로드 완료")
            except Exception as e:
                logging.warning(f"🚨 [Analyst] 라이브러리 파일 파싱 실패: {e}")
                # [V47 Fix] 빈 dict를 JSON 직렬화 - 이중 이스케이프 방지
                empty_json = json.dumps({}, ensure_ascii=False)
                intro_lib_full = dev_lib_full = ending_lib_full = trans_lib_full = archetype_lib_full = empty_json
        else:
            logging.warning(f"⚠️ [Analyst] {current_genre} 라이브러리 없음, 기본 사용")
            # 폴백: 기본 라이브러리 시도 [V45 Fix] 루트 config 경로 사용
            from pathlib import Path

            root_config = Path(__file__).parent.parent.parent.parent / "config"
            fallback_path = root_config / "prompts" / "analyst_libraries.json"
            if fallback_path.exists():
                try:
                    lib_data = json.loads(fallback_path.read_text(encoding="utf-8"))
                    intro_lib_full = json.dumps(lib_data.get("intro_patterns", {}), ensure_ascii=False)
                    dev_lib_full = json.dumps(lib_data.get("narrative_archetypes", {}), ensure_ascii=False)
                    ending_lib_full = json.dumps(lib_data.get("ending_patterns", {}), ensure_ascii=False)
                    trans_lib_full = json.dumps(lib_data.get("transition_patterns", {}), ensure_ascii=False)
                    archetype_lib_full = dev_lib_full
                    logging.warning("📚 [Analyst] 기본 라이브러리 로드 완료")
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    # [V44] JSON 파싱 실패 경고 추가
                    logging.warning(f"🚨 [Analyst] 기본 라이브러리 파싱 실패: {str(e)[:50]}")
                    # [V47 Fix] 빈 dict를 JSON 직렬화 - 이중 이스케이프 방지
                    empty_json = json.dumps({}, ensure_ascii=False)
                    intro_lib_full = dev_lib_full = ending_lib_full = trans_lib_full = archetype_lib_full = empty_json
            else:
                # [V47 Fix] 빈 dict를 JSON 직렬화 - 이중 이스케이프 방지
                empty_json = json.dumps({}, ensure_ascii=False)
                intro_lib_full = dev_lib_full = ending_lib_full = trans_lib_full = archetype_lib_full = empty_json

        # 3-1. [V42 + V60.32] 주인공 이름 결정 (파라미터 우선, 없으면 Bible 추출)
        final_protagonist_name = protagonist_name  # 파라미터로 받은 값 우선
        if not final_protagonist_name or final_protagonist_name == "주인공":
            try:
                bible_data = self.context.db.load_anchor("bible")
                if bible_data:
                    mb = bible_data.get("MasterBible", bible_data)
                    # [V61.2 Fix] 장르별 HUD 탐색
                    genre = getattr(self.context, "genre", "") or ""
                    name = HUDKeys.get_protagonist_name(mb, genre)
                    if name and name != "주인공":
                        final_protagonist_name = name
            except Exception as e:
                logging.warning(f"⚠️ [Analyst] 주인공 이름 추출 실패, 기본값 사용: {e}")
        if not final_protagonist_name:
            final_protagonist_name = "주인공"
        protagonist_name = final_protagonist_name  # 이후 코드 호환

        # [V60.95] 고밀도 HUD 컨텍스트 구축
        hud_context = ""
        if state_tracker and ep_start > 1:
            try:
                prev_ep = ep_start - 1
                prev_state = (
                    state_tracker.get_state_at_episode(prev_ep)
                    if hasattr(state_tracker, "get_state_at_episode")
                    else None
                )
                if prev_state:
                    state_dict = prev_state.to_dict() if hasattr(prev_state, "to_dict") else {}
                    hud_lines = [f"[Arc 시작 전 주인공 상태 - 제{prev_ep}화 종료 시점]"]
                    for k in ["location", "hp", "mp", "martial_level", "status", "injuries"]:
                        if k in state_dict and state_dict[k]:
                            hud_lines.append(f"  {k}: {state_dict[k]}")
                    items = state_dict.get("items", [])
                    if items:
                        hud_lines.append(f"  보유 아이템: {', '.join(items[:8])}")
                    hud_context = "\n".join(hud_lines)
            except Exception as e:
                logging.warning(f"[Analyst] HUD 로드 오류: {e}")
                hud_context = f"(HUD 로드 오류: {str(e)[:50]})"

        # 4. 공통 데이터셋 조립 (데이터 이스케이프 적용)
        safe_data = {
            "genre_prompt": self.context.guard.get_v20_purism_prompt(),
            "protagonist_name": protagonist_name,  # V42 LOCK
            "strategic_compass": self._escape_braces(vol_strategy),
            "prev_arc_context": self._escape_braces(prev_arc_context) or "시작점",
            "prev_block": self._escape_braces(json.dumps(prev_block, ensure_ascii=False)) if prev_block else "시작점",
            "curr_block": self._escape_braces(json.dumps(curr_block, ensure_ascii=False)),
            "next_block": self._escape_braces(json.dumps(next_block, ensure_ascii=False)),
            "assigned_seeds_info": self._escape_braces(seeds_info),
            "arc_no": clean_arc_no,
            "vol_no": vol_no,
            "ep_start": ep_start,
            "ep_end": ep_start + target_ep_count - 1,
            "ep_count": target_ep_count,  # [V60.36 FIX] 템플릿에서 사용하는 ep_count 추가
            "ep_count_suggestion": str(target_ep_count),
            "assets": self._escape_braces(json.dumps(assets, ensure_ascii=False)) if assets else "{}",
            "full_roadmap": self._escape_braces(full_roadmap),
            "protagonist_hud_state": self._escape_braces(hud_context) if hud_context else "",  # [V60.95] 고밀도 HUD
        }

        # 5. [V65] 설계 및 자기 비판 루프 — retry_with_feedback 래퍼 적용
        max_retries = 3
        # [V60.31] 가변 페이싱: 권장값만 제시, LLM이 사건 밀도로 최종 결정
        pacing_guide = (
            f"시스템 권장: {target_ep_count}화 (Blitz:2-3 / Standard:3-4 / Epic:5-6 중 사건 밀도에 맞게 조정 가능)"
        )
        initial_feedback = feedback if feedback else pacing_guide
        final_arc_data = None
        # [V65] 루프 간 공유 상태를 dict로 관리 (클로저 캡처용)
        _arc_loop_state = {"draft_result": None, "actual_ep_count": target_ep_count}

        class _SafeDict(dict):
            def __missing__(self, key):
                return "{" + key + "}"

        def _arc_attempt_func(attempt, retry_feedback):
            """[V65] 단일 시도 로직 — retry_with_feedback에 전달"""
            current_feedback = retry_feedback if retry_feedback else initial_feedback
            # [V60.31] 템플릿의 ep_count_suggestion 변수를 동적으로 치환
            adjusted_prompt_tpl = get_plan_arc_prompt_v25()

            # 6. [API 호출 분기 로직]
            try:
                if self.cache_name:
                    # Case A: 캐시 활성 시에만 지침을 치환하여 전송 (토큰 절약 핵심)
                    cache_safe_data = safe_data.copy()
                    placeholder = "[CACHED: Narrative Patterns Library Active - Refer to system memory]"
                    cache_safe_data.update(
                        {
                            "intro_library": placeholder,
                            "dev_library": placeholder,
                            "ending_library": placeholder,
                            "trans_library": placeholder,
                            "archetype_library": placeholder,
                            "special_instructions": f"\n[🚨 PACING GUIDE]: 권장 {target_ep_count}화 (사건 밀도에 따라 3~7화 범위 내 조정 가능)",
                        }
                    )
                    prompt = adjusted_prompt_tpl.format_map(_SafeDict(**cache_safe_data))
                    if attempt > 0 or feedback:
                        prompt += f"\n\n🚨 [FEEDBACK]: {current_feedback}"

                    # [V49.4] Structured Output Schema 적용
                    # [V49.6] 온도 상향: 0.4 → 0.5 (추론력 강화)
                    config_params = {
                        "cached_content": self.cache_name,
                        "temperature": 0.5,
                        "max_output_tokens": 8192,
                        "response_mime_type": "application/json",
                    }
                    if SCHEMA_ENABLED and ARC_DESIGN_SCHEMA:
                        config_params["response_schema"] = ARC_DESIGN_SCHEMA

                    response = self.client.models.generate_content(
                        model=self.primary_model, contents=prompt, config=types.GenerateContentConfig(**config_params)
                    )
                    draft_result = self._extract_json_robust(response.text)
                else:
                    raise LookupError("No Cache Found")

            except Exception as e:
                # Case B: 캐시가 없거나 호출 실패 시 즉시 Full-Text로 복구 (품질 보존)
                if self.cache_name:
                    logging.warning(f"⚠️ [Analyst] 캐시 호출 실패. 일반 모드 전환: {str(e)[:50]}")

                full_safe_data = safe_data.copy()
                full_safe_data.update(
                    {
                        "intro_library": self._escape_braces(intro_lib_full),
                        "dev_library": self._escape_braces(dev_lib_full),
                        "ending_library": self._escape_braces(ending_lib_full),
                        "trans_library": self._escape_braces(trans_lib_full),
                        "archetype_library": self._escape_braces(archetype_lib_full),
                        "special_instructions": f"\n[🚨 PACING GUIDE]: 권장 {target_ep_count}화 (사건 밀도에 따라 3~7화 범위 내 조정 가능)",
                    }
                )
                prompt = adjusted_prompt_tpl.format_map(_SafeDict(**full_safe_data))
                if attempt > 0:
                    prompt += f"\n\n🚨 [FEEDBACK]: {current_feedback}"

                # [V49.4] 일반 API 호출 (Structured Schema 적용)
                # [V49.7] 온도 점진적 상향: 0.5 → 0.6 → 0.7 (재시도 시 창의적 접근 유도)
                schema = ARC_DESIGN_SCHEMA if SCHEMA_ENABLED else None
                temp = 0.5 if attempt == 0 else (0.6 if attempt == 1 else 0.7)
                draft_result = self._extract_json_robust(self.ask(prompt, temperature=temp, response_schema=schema))

            # 7. [V60.31] 가변 페이싱: LLM이 결정한 ep_count 존중 (3~7 범위 내)
            llm_ep_count = draft_result.get("ep_count")
            if isinstance(llm_ep_count, str):
                match = re.search(r"(\d+)", str(llm_ep_count))
                llm_ep_count = int(match.group(1)) if match else target_ep_count
            elif not isinstance(llm_ep_count, int):
                llm_ep_count = target_ep_count

            # [V60.70] chosen_pacing과 ep_count 강제 동기화 (자기모순 방지)
            pacing_decision = draft_result.get("pacing_decision", {})
            chosen_pacing = pacing_decision.get("chosen_pacing", "") if isinstance(pacing_decision, dict) else ""
            chosen_pacing_lower = chosen_pacing.lower() if isinstance(chosen_pacing, str) else ""

            if "epic" in chosen_pacing_lower:
                pacing_min, pacing_max = 6, 7
            elif "standard" in chosen_pacing_lower:
                pacing_min, pacing_max = 5, 5
            elif "blitz" in chosen_pacing_lower:
                pacing_min, pacing_max = 3, 4
            else:
                pacing_min, pacing_max = 3, 7

            if llm_ep_count < pacing_min or llm_ep_count > pacing_max:
                corrected_ep_count = max(pacing_min, min(pacing_max, llm_ep_count))
                logging.warning(
                    f"🔧 [V60.70] 자기모순 교정: chosen_pacing={chosen_pacing} 인데 ep_count={llm_ep_count} → {corrected_ep_count}화로 강제 조정"
                )
                llm_ep_count = corrected_ep_count

            actual_ep_count = max(3, min(7, llm_ep_count))
            if actual_ep_count != target_ep_count:
                logging.info(f"📊 [V60.31] 가변 페이싱: 권장 {target_ep_count}화 → LLM 결정 {actual_ep_count}화")

            beats = draft_result.get("beat_sequence", [])
            if not isinstance(beats, list):
                beats = []
            if len(beats) != actual_ep_count:
                if len(beats) > actual_ep_count:
                    combined = " / ".join(beats[actual_ep_count - 1 :])
                    beats = beats[: actual_ep_count - 1] + [f"[통합 전개]: {combined}"]
                else:
                    original_count = len(beats)
                    fallback_beats = [
                        "서사적 긴장감 고조 및 빌드업 수행",
                        "캐릭터 내면 갈등 심화 및 선택의 기로",
                        "예상치 못한 전환점 발생",
                        "이해관계자 간 대립 격화",
                        "결정적 사건을 향한 수렴",
                    ]
                    while len(beats) < actual_ep_count:
                        idx = len(beats) % len(fallback_beats)
                        beats.append(fallback_beats[idx])
                    logging.warning(
                        "[Analyst] beat_sequence 부족 (%d/%d) — 폴백 비트 %d개 추가",
                        original_count,
                        actual_ep_count,
                        actual_ep_count - original_count,
                    )
                draft_result["beat_sequence"] = beats

            # 공유 상태 업데이트
            _arc_loop_state["draft_result"] = draft_result
            _arc_loop_state["actual_ep_count"] = actual_ep_count

            # 자기 비판 감사 (Self-Critic) 호출
            critic_input = (
                f"{get_analyst_self_critic_prompt()}\n[Draft to Review]: {json.dumps(draft_result, ensure_ascii=False)}"
            )
            audit_result = self._extract_json_robust(self.ask(critic_input, temperature=0.2))
            return audit_result

        def _arc_on_success(audit_result) -> bool:
            """[V65] Self-Critic PASS 판정"""
            return audit_result.get("status") == "PASS"

        def _arc_on_failure(audit_result, attempt):
            """[V65] Self-Critic REJECT → 피드백 추출"""
            return audit_result.get("feedback", "밀도 및 개연성 보강 필요")

        from modules.core.adaptive_retry import retry_with_feedback

        audit_result, _arc_attempts, _arc_success = retry_with_feedback(
            func=_arc_attempt_func,
            max_attempts=max_retries,
            on_success=_arc_on_success,
            on_failure=_arc_on_failure,
            task_name=f"plan_single_arc(arc={clean_arc_no})",
        )

        # [V65] 루프 결과 반영 — 기존 동작 보존
        draft_result = _arc_loop_state["draft_result"]
        actual_ep_count = _arc_loop_state["actual_ep_count"]
        if _arc_success:
            final_arc_data = draft_result
            final_arc_data["_actual_ep_count"] = actual_ep_count

        # 8. 메타데이터 최종 동기화 및 반환 (인과율 유지)
        if not final_arc_data:
            final_arc_data = draft_result
            final_arc_data["_actual_ep_count"] = actual_ep_count  # [V60.31]

        # [V60.31] 가변 페이싱: LLM 결정 ep_count 사용
        final_ep_count = final_arc_data.get("_actual_ep_count", target_ep_count)
        final_arc_data.update(
            {
                "arc_no": clean_arc_no,
                "vol_no": vol_no,
                "ep_start": ep_start,
                "ep_count": final_ep_count,
                "ep_end": ep_start + final_ep_count - 1,
            }
        )
        if "_actual_ep_count" in final_arc_data:
            del final_arc_data["_actual_ep_count"]  # 임시 키 제거
        self._normalize_arc_output(final_arc_data, ep_start, final_ep_count)

        # 9. [V49.3] StateTracker를 통한 상태 일관성 검증
        state_issues = self._validate_arc_with_state_tracker(final_arc_data)
        if state_issues:
            logging.warning(f"⚠️ [Analyst] StateTracker 검증 이슈 발견: {len(state_issues)}건")
            # 검증 이슈를 Arc 데이터에 첨부 (Director/ContinuityInspector 참조용)
            final_arc_data["state_tracker_issues"] = state_issues
            # Critical 이슈가 있으면 tactical_doc에 경고 주입
            critical_issues = [i for i in state_issues if i.get("severity") in ["critical", "major"]]
            if critical_issues:
                warning_text = "\n\n⚠️ [STATE TRACKER WARNING]:\n"
                for issue in critical_issues[:3]:  # 최대 3개
                    warning_text += f"- [{issue['severity'].upper()}] {issue['description']}\n"
                if "tactical_doc" in final_arc_data and isinstance(final_arc_data["tactical_doc"], str):
                    final_arc_data["tactical_doc"] = warning_text + final_arc_data["tactical_doc"]

        # ═══════════════════════════════════════════════════════════════
        # 10. [V60] Arc 상태 계승 검증 + 화 간 모순 탐지 + Joint Docs 보정
        # ═══════════════════════════════════════════════════════════════

        # 10-1. 이전 Arc 데이터 로드
        prev_arc_data = None
        if clean_arc_no > 1:
            try:
                arcs_anchor = self.context.db.load_anchor("arcs")
                if arcs_anchor and isinstance(arcs_anchor, dict):
                    prev_arc_data = arcs_anchor.get(f"arc_{clean_arc_no - 1}")
            except Exception as e:
                logging.warning(f"⚠️ [V60] 이전 Arc 로드 실패: {e}")

        # 10-2. Arc 상태 계승 검증
        if prev_arc_data:
            continuity_result = self._validate_arc_state_continuity_v60(final_arc_data, prev_arc_data)
            if continuity_result["issues"]:
                logging.warning(f"🔍 [V60] Arc 상태 계승 검증: {continuity_result['severity']}")
                for issue in continuity_result["issues"][:3]:
                    logging.info(f"- {issue}")

                # 자동 보정 적용
                if continuity_result["auto_corrections"]:
                    if "state_constraints" not in final_arc_data:
                        final_arc_data["state_constraints"] = {}
                    if "arc_start_state" not in final_arc_data["state_constraints"]:
                        final_arc_data["state_constraints"]["arc_start_state"] = {}

                    start_state = final_arc_data["state_constraints"]["arc_start_state"]

                    if "location" in continuity_result["auto_corrections"]:
                        start_state["location"] = continuity_result["auto_corrections"]["location"]
                        logging.info(f"🔧 [V60] 시작 위치 자동 보정: {start_state['location']}")

                    if "missing_items" in continuity_result["auto_corrections"]:
                        existing = start_state.get("equipment", [])
                        if isinstance(existing, str):
                            existing = [existing] if existing else []
                        existing.extend(continuity_result["auto_corrections"]["missing_items"])
                        start_state["equipment"] = list(set(existing))
                        logging.info(f"🔧 [V60] 시작 소지품 자동 보정: {start_state['equipment']}")

                # 검증 결과 첨부
                final_arc_data["v60_continuity_check"] = continuity_result

        # 10-3. Arc 내 화 간 모순 탐지
        tactical_doc = final_arc_data.get("tactical_doc", "")
        if tactical_doc:
            doc_continuity = self._validate_tactical_doc_continuity_v60(tactical_doc, final_ep_count)
            if doc_continuity["issues"]:
                logging.info(f"🔍 [V60] 화 간 연속성 검증: {len(doc_continuity['issues'])}건 이슈")
                for issue in doc_continuity["issues"][:3]:
                    logging.info(f"- {issue}")

                # 경고 주입
                warning_text = "\n\n⚠️ [V60 CONTINUITY WARNING]:\n"
                for issue in doc_continuity["issues"][:5]:
                    warning_text += f"- {issue}\n"
                final_arc_data["tactical_doc"] = warning_text + tactical_doc

            final_arc_data["v60_doc_continuity"] = doc_continuity

        # 10-4. Joint Docs 자동 추출 보정
        if tactical_doc:
            final_arc_data = self._auto_correct_joint_docs_v60(tactical_doc, final_arc_data)

        # [V70] state_changes 기본값 보장 (FourPhase의 _ensure_required_fields와 동일 수준)
        if "state_changes" not in final_arc_data or not isinstance(final_arc_data.get("state_changes"), dict):
            final_arc_data["state_changes"] = {}
        _sc = final_arc_data["state_changes"]
        for _sc_key in [
            "npc_deaths",
            "skill_acquisitions",
            "relationship_changes",
            "major_items",
            "entity_destructions",
            "npc_personality_changes",
            "npc_npc_relationships",
            "npc_dialogue_profiles",
            "npc_injuries",
            "npc_movements",
            "time_markers",
            "companion_changes",
            "promises_obligations",
            "protagonist_emotion",
        ]:
            if _sc_key not in _sc:
                _sc[_sc_key] = []

        return final_arc_data

    # endregion

    def _normalize_arc_output(self, arc_data, ep_start, ep_count):
        """아크 출력의 회차 표기 및 분량 메타를 정규화한다."""
        if not isinstance(arc_data, dict):
            return

        # 1) beat_sequence 회차 표기 강제 정규화 (잘못된 한글 서수 오타 방지)
        beats = arc_data.get("beat_sequence", [])
        if isinstance(beats, list):
            normalized = []
            for i, beat in enumerate(beats):
                expected_ep = ep_start + i
                if isinstance(beat, str):
                    # "제 X화" 접두를 제거하고 표준 접두로 재조립
                    m = re.match(r"^\s*제\s*.*?화[: ]\s*(.*)$", beat)
                    rest = m.group(1) if m else beat.strip()
                    normalized.append(f"제 {expected_ep}화: {rest}".strip())
                else:
                    normalized.append(beat)
            arc_data["beat_sequence"] = normalized

        # 1-1) tactical_doc 회차 헤더 정규화 (전술 설계 제목 오타 방지)
        tactical = arc_data.get("tactical_doc")
        if isinstance(tactical, str) and isinstance(ep_start, int) and isinstance(ep_count, int):
            expected_eps = list(range(ep_start, ep_start + ep_count))
            it = iter(expected_eps)

            def _repl(match) -> str:
                try:
                    n = next(it)
                except StopIteration:
                    return match.group(0)
                return f"[제 {n}화 전술 설계]"

            tactical = re.sub(r"\[제\s*.*?화 전술 설계\]", _repl, tactical)
            arc_data["tactical_doc"] = tactical

        # 2) 분량 메타 키를 ep_count로 통일 (중복/불일치 방지)
        length_keys = {"arc_length_chapters", "total_chapters_estimate", "arc_duration_episodes"}

        def _walk(node) -> None:
            if isinstance(node, dict):
                for k in list(node.keys()):
                    if k in length_keys:
                        node[k] = str(ep_count)
                    else:
                        _walk(node[k])
            elif isinstance(node, list):
                for item in node:
                    _walk(item)

        _walk(arc_data)

        # 3) 명칭/아이템 표준화 - Bible의 alias_map 기반 (V43: 하드코딩 제거)
        # 특정 작품에 종속된 하드코딩(팽명→팽무진, 대방도→혼철대도) 제거
        # 필요 시 Bible의 'alias_map' 또는 'name_corrections' 섹션에서 동적으로 로드
        pass  # 명칭 표준화는 Bible 데이터로 처리

    # region // master bible recovery
    def total_absolute_recovery_v20(self, draft_contents, treatment_content=""):
        """[Phase 0] 시점 기반 역사 복구 및 DNA Sync (풀 버전)"""

        # [🔥 중요] 원고가 너무 길 경우: 앞부분(설정) + 뒷부분(최신 상태) 병합
        compact_draft = ""
        if len(draft_contents) > 60000:
            compact_draft = draft_contents[:10000] + "\n\n...[중략: 서사 중간 생략]...\n\n" + draft_contents[-50000:]
        else:
            compact_draft = draft_contents

        template = get_recovery_prompt()  # [V65] 외부화
        # 3. 모든 동적 데이터에 _escape_braces 적용 후 주입
        prompt = template.format(
            draft_data=self._escape_braces(compact_draft), treatment_data=self._escape_braces(treatment_content[:15000])
        )

        response = self.ask(prompt, temperature=0.3)
        return self._extract_json_robust(response)

    # endregion

    def design_volume_strategy(self, bible_context, roadmap_data):
        """[Stage 1] 50개 아크 배분 전략 (f-string 보안 패치 적용)"""

        # 1. [V65] 템플릿 외부화
        template = get_volume_strategy_prompt()

        # 2. 데이터 안전화 및 주입
        prompt = template.format(
            bible_info=self._escape_braces(json.dumps(bible_context, ensure_ascii=False)),
            roadmap_info=self._escape_braces(json.dumps(roadmap_data, ensure_ascii=False)),
        )

        response = self.ask(prompt, temperature=0.5)
        return self._extract_json_robust(response)

    def plan_batch_arcs_v25(self, batch_no, vol_strategy, blueprint_str, prev_context, assets):
        """[V25 Patch] 배치 설계용 파라미터 강제 보정"""
        # 이 메서드는 구형 규격이므로, PLAN_ARC_PROMPT_V25 직접 사용 대신 내부 간이 프롬프트 사용 권장
        # 혹은 필요한 모든 더미 데이터를 생성하여 V25 프롬프트에 주입
        return self.plan_single_arc_v20(
            arc_no=batch_no,
            vol_strategy=vol_strategy,
            prev_block={},
            curr_block={"raw": blueprint_str},
            next_block={},
            ep_start=1,
            prev_arc_context=prev_context,
            assets=assets,
            full_roadmap="Batch Mode",
        )

    async def enrich_raw_block_async(
        self, raw_block, prev_block=None, next_block=None, assigned_seeds=None, transfused_history=""
    ):
        """[V35.5 Phase 2] safe_prev를 effective_prev로 진화시킨 농축 엔진"""

        # 1. 현재 블록 및 주변 블록 이스케이프 (기존 safe_prev 로직 포함)
        safe_curr = self._escape_braces(json.dumps(raw_block, ensure_ascii=False))
        safe_next = self._escape_braces(json.dumps(next_block, ensure_ascii=False)) if next_block else "서사 종결점"
        safe_seeds = self._escape_braces(json.dumps(assigned_seeds, ensure_ascii=False)) if assigned_seeds else "없음"

        # 2. 🚨 safe_prev의 진화: effective_prev (수혈 우선 순위 결정)
        # transfused_history(수혈된 실제 역사)가 있다면 그것을 최우선으로 사용합니다.
        if transfused_history and len(transfused_history) > 10:
            # 수혈 데이터는 이미 가공된 텍스트이므로 그대로 사용하거나 추가 이스케이프 적용
            effective_prev = f"[🚨 확정된 실제 과거 역사]:\n{transfused_history}"
        else:
            # 수혈 데이터가 없을 때만 원본 DNA(prev_block)를 변환하여 사용 (이것이 기존의 safe_prev 역할입니다)
            effective_prev = (
                self._escape_braces(json.dumps(prev_block, ensure_ascii=False)) if prev_block else "서사 시작점"
            )

        # 3. 프롬프트 조립
        # ENRICH_BLOCK_PROMPT_V30의 {prev_context} 자리에 effective_prev를 주입합니다.
        prompt = get_enrich_block_prompt_v30(
            genre_prompt=self.context.guard.get_v20_purism_prompt(),
            curr_block=safe_curr,
            prev_context=effective_prev,  # 👈 safe_prev의 진화형
            next_context=safe_next,
            seeds_context=safe_seeds,
        )

        # 4. 실행 루틴
        loop = asyncio.get_running_loop()
        try:
            raw_res = await loop.run_in_executor(None, lambda: self.ask(prompt, temperature=0.3))
            enriched_result = self._extract_json_robust(raw_res)

            # 메타데이터 보존 가드
            if "block_id" not in enriched_result:
                enriched_result["block_id"] = raw_block.get("block_id")
            if "title" not in enriched_result:
                enriched_result["title"] = raw_block.get("title")

            return enriched_result

        except Exception as e:
            logging.warning(f"🚨 [Enrich Critical Error] {e}")
            return raw_block  # 실패 시 원본 DNA 반환

    def analyze_context(self, mode="GENERAL", **kwargs) -> dict:
        """
        [V35 Manifesto] 에이전트 간 조율 및 아크 긴급 수술 로직 (Surgery Room)
        """
        # 1. [V35] 아크 긴급 수술 모드 발동
        if mode == "ARC_RECONSTRUCTION":
            prev_arc = kwargs.get("prev_arc")
            curr_arc = kwargs.get("curr_arc")
            next_arc = kwargs.get("next_arc")
            feedback = kwargs.get("feedback")

            self.ui_log("👨‍⚕️ [Analyst] 아크 인과관계 수술 및 5배 농축 공정을 시작합니다.")

            # 🔧 [Guard] 이스케이프 누적 방지: tactical_doc만 안전 정규화
            def _normalize_tactical_doc_for_prompt(arc):
                if not arc or not isinstance(arc, dict):
                    return arc
                tactical = arc.get("tactical_doc")
                if isinstance(tactical, str):
                    normalized = tactical
                    # 이중 이스케이프를 단계적으로 완화
                    for _ in range(2):
                        normalized = normalized.replace("\\\\n", "\\n").replace("\\\\t", "\\t")
                    normalized = normalized.replace("\\n", "\n").replace("\\t", "\t")
                    if normalized != tactical:
                        arc = arc.copy()
                        arc["tactical_doc"] = normalized
                return arc

            prev_arc = _normalize_tactical_doc_for_prompt(prev_arc)
            curr_arc = _normalize_tactical_doc_for_prompt(curr_arc)
            next_arc = _normalize_tactical_doc_for_prompt(next_arc)

            # [V65] 수술실 프롬프트 외부화
            surgery_prompt = get_surgery_prompt(
                prev_arc_json=json.dumps(prev_arc, ensure_ascii=False) if prev_arc else "데이터 없음(도입부)",
                curr_arc_json=json.dumps(curr_arc, ensure_ascii=False),
                next_arc_json=json.dumps(next_arc, ensure_ascii=False) if next_arc else "데이터 없음(종결부)",
                feedback=feedback,
            )
            # 3-pro급 모델 호출 (안정적인 수술을 위해 온도를 낮춤)
            raw_response = self.ask(surgery_prompt, temperature=0.3)

            # BaseAgent의 강건한 파싱 엔진 활용
            reconstructed_arc = self._extract_json_robust(raw_response)

            if reconstructed_arc and "tactical_doc" in reconstructed_arc:
                # 🆕 V35 수술 마크 삽입: 아키텍트가 이를 보고 '성경 모드'를 발동합니다.
                # 🔧 [V40.2 Fix] 원본 arc의 모든 필수 필드를 보존하여 데이터 손실 방지
                preserved_fields = [
                    "ep_start",
                    "ep_end",
                    "arc_no",
                    "ep_count",
                    "vol_no",
                    "title",
                    "beat_sequence",
                    "hybrid_composition",
                    "arc_drive",
                    "joint_docs",
                    "status_shadow",
                ]
                for field in preserved_fields:
                    if field not in reconstructed_arc and curr_arc.get(field) is not None:
                        reconstructed_arc[field] = curr_arc.get(field)

                # 필수 필드 강제 보장 (LLM이 생성하지 않은 경우)
                if not reconstructed_arc.get("ep_start"):
                    reconstructed_arc["ep_start"] = curr_arc.get("ep_start")
                if not reconstructed_arc.get("ep_end"):
                    reconstructed_arc["ep_end"] = curr_arc.get("ep_end")
                if not reconstructed_arc.get("arc_no"):
                    reconstructed_arc["arc_no"] = curr_arc.get("arc_no")
                if not reconstructed_arc.get("ep_count"):
                    reconstructed_arc["ep_count"] = curr_arc.get(
                        "ep_count", (reconstructed_arc.get("ep_end", 4) - reconstructed_arc.get("ep_start", 1) + 1)
                    )
                if not reconstructed_arc.get("beat_sequence") and curr_arc.get("beat_sequence"):
                    reconstructed_arc["beat_sequence"] = curr_arc.get("beat_sequence")

                reconstructed_arc["v35_surgery"] = True
                reconstructed_arc["mixing_logic"] = "[V35 Emergency Surgery] 인과관계 용접 및 5배 농축 완료"

                self.ui_log(f"✅ [Analyst] Arc {reconstructed_arc.get('arc_no', '??')} 수술 및 마킹 완료.")
                return reconstructed_arc  # 마킹된 데이터를 리턴
            else:
                self.ui_log("🚨 [Error] 아크 수술 결과 JSON 파싱 실패 또는 키 누락.")
                return None

        # 2. 기존 일반 분석 모드 (필요 시 확장 가능)
        return {"status": "GENERAL_MODE_ACTIVE"}

    def ui_log(self, msg) -> None:
        """ProjectContext를 통한 UI 로그 출력"""
        if hasattr(self.context, "ui") and hasattr(self.context.ui, "log"):
            self.context.ui.log(msg)
        else:
            logging.warning(f"[Analyst] {msg}")

    def perform_v35_calibration(self, current_hud, target_arc):
        """[V35.5] 서사 목적에 맞게 주인공의 물리 수치를 강제 교정 및 개연성 부여"""

        # 1. [🚨 핵심 수술] 파이썬 논리를 문자열 밖으로 탈출시킴
        if isinstance(target_arc, dict):
            arc_title = target_arc.get("title", "알 수 없는 아크")
            arc_tactical = target_arc.get("tactical_doc", "전술 데이터 없음")
        else:
            # target_arc가 문자열(제목)로 넘어왔을 경우를 대비한 방어 로직
            arc_title = str(target_arc)
            arc_tactical = "세부 전술 데이터가 누락되었습니다. 현재 맥락에 맞춰 보정하십시오."

        # 2. 보정 메시지 생성
        calibration_msg = (
            f"현재 주인공의 상태로는 아크의 목표인 '{arc_title}'을(를) 달성하는 것이 물리적으로 불가능합니다."
        )

        # [V65] 캘리브레이션 프롬프트 외부화
        calibration_prompt = get_calibration_prompt(
            calibration_msg=calibration_msg,
            current_hud_json=json.dumps(current_hud, ensure_ascii=False),
            arc_tactical=arc_tactical,
        )
        res = self.ask(calibration_prompt, temperature=0.3)
        return self._extract_json_robust(res)

    def stitch_joints(self, joint_a, joint_b, context_b):
        """[V35.5 Phase 3] 두 아크 사이의 물리적 마디를 검사하고 용접함"""
        prompt = get_post_stitch_repair_prompt(
            arc_a_joint=json.dumps(joint_a, ensure_ascii=False),
            arc_b_joint=json.dumps(joint_b, ensure_ascii=False),
        )

        # 용접은 정밀도가 중요하므로 온도를 0.1로 고정
        raw_res = self.ask(prompt, temperature=0.1)
        return self._extract_json_robust(raw_res)

    def get_lack_report(self, martial_hud) -> dict:
        """
        [V38.2 S-Grade] NoneType 방어막이 적용된 결핍 탐지 엔진
        """
        # 1. 입력 가드: 데이터가 없거나 딕셔너리가 아니면 즉시 기본값 반환
        if not martial_hud or not isinstance(martial_hud, dict):
            return {
                "lack_summary": "1. [무력]: 데이터 로드 실패\n2. [경제]: 분석 불가\n3. [권위]: HUD 누락",
                "raw_analysis": {"Martial": [], "Economy": [], "Authority": []},
            }

        actual = martial_hud.get("actual_truth", {})
        reputation = martial_hud.get("public_reputation", {})

        # 2. 🛡️ [핵심 수술] None 값을 빈 문자열로 강제 치환 (TypeError 방지)
        def safe_str(val):
            return str(val) if val is not None else ""

        # 3. 결핍 판단 기준 정의
        LACK_CRITERIA = {
            "Martial": [
                (safe_str(actual.get("realm")), ["삼류", "하수", "입문", "견습", "초보", "None"], "절대적 무위 부족"),
                (
                    safe_str(actual.get("causal_injuries")),
                    ["부상", "내상", "박살", "뒤엉킨", "독", "불구"],
                    "신체적 기능 저하",
                ),
            ],
            "Economy": [
                (safe_str(actual.get("wealth")), ["0", "없음", "고갈", "빈털터리", "채무"], "사적 활동 자금 전멸"),
                (safe_str(actual.get("equipment")), ["무딘", "연습용", "녹슨", "평범한", "누더기"], "장비 해상도 저하"),
            ],
            "Authority": [
                (
                    safe_str(reputation.get("identity")),
                    ["망나니", "개차반", "무시", "천덕꾸러기", "낙제생"],
                    "사회적 신뢰도 결여",
                )
            ],
        }

        # 4. 루프 분석 (여기서 any() 에러가 발생하던 구간을 안전하게 통과함)
        lack_analysis = {"Martial": [], "Economy": [], "Authority": []}

        for category, criteria_list in LACK_CRITERIA.items():
            for target_value, keywords, message in criteria_list:
                # target_value가 이제 무조건 문자열이므로 에러가 나지 않음
                if any(k in target_value for k in keywords):
                    lack_analysis[category].append(message)

        # 5. 출력 생성
        summary = (
            f"1. [무력]: {', '.join(lack_analysis['Martial']) if lack_analysis['Martial'] else '안정'}\n"
            f"2. [경제]: {', '.join(lack_analysis['Economy']) if lack_analysis['Economy'] else '안정'}\n"
            f"3. [권위]: {', '.join(lack_analysis['Authority']) if lack_analysis['Authority'] else '안정'}"
        )

        return {"lack_summary": summary, "raw_analysis": lack_analysis}

    def _get_current_genre(self) -> str:
        """
        [V43] 현재 장르를 감지하여 반환
        Guard에서 장르 정보를 추출하거나 기본값 반환
        """
        try:
            if hasattr(self.context, "guard") and self.context.guard:
                # Guard의 get_genre_name()에서 장르 추출
                genre_name = self.context.guard.get_genre_name()
                if "hunter" in genre_name.lower() or "헌터" in genre_name:
                    return "hunter"
                elif "invest" in genre_name.lower() or "투자" in genre_name:
                    return "investment"
                elif "wuxia" in genre_name.lower() or "무협" in genre_name:
                    return "wuxia"
                elif "actor" in genre_name.lower() or "배우" in genre_name:
                    return "actor"
                elif "sports" in genre_name.lower() or "스포츠" in genre_name:
                    return "sports"
                elif "medical" in genre_name.lower() or "의학" in genre_name or "의료" in genre_name:
                    return "medical"
                elif "cook" in genre_name.lower() or "요리" in genre_name:
                    return "cooking"
                elif "composer" in genre_name.lower() or "작곡" in genre_name:
                    return "composer"
                elif "alt_history" in genre_name.lower() or "대체역사" in genre_name or "조선" in genre_name:
                    return "alt_history"
        except Exception as e:
            logging.warning(f"⚠️ [Analyst] 장르 감지 실패: {e}")

        return "wuxia"  # 기본값

    def _get_genre_library_path(self, genre: str):
        """
        [V43] 장르에 맞는 라이브러리 파일 경로 반환
        [V45 Fix] 프로젝트 config가 아닌 루트 config 경로 사용
        """
        from pathlib import Path

        # 장르별 라이브러리 파일 매핑
        genre_library_map = {
            "wuxia": "analyst_libraries.json",
            "hunter": "analyst_libraries_hunter.json",
            "investment": "analyst_libraries_investment.json",
            "cooking": "analyst_libraries_cooking.json",
            "actor": "analyst_libraries_actor.json",
            "sports": "analyst_libraries_sports.json",
            "medical": "analyst_libraries_medical.json",
        }

        lib_filename = genre_library_map.get(genre, "analyst_libraries.json")

        # [V45 Fix] 루트 config 경로 사용 (modules/domain/agents/analyst.py -> 3단계 상위)
        root_config = Path(__file__).parent.parent.parent.parent / "config"
        return root_config / "prompts" / lib_filename

    def _validate_arc_with_state_tracker(self, arc_data: dict) -> list:
        """
        [V49.3] StateTracker를 사용하여 Arc 설계의 상태 일관성 검증
        """
        # [V70] StateTracker는 preset_registry/llm_client 없이 의미 있는 검증 불가
        return []

    def get_state_constraint_prompt(self, arc_no: int) -> str:
        """
        [V49.3] 이전 Arc들의 상태를 분석하여 제약 프롬프트 생성

        Architect/Writer에게 전달하여 상태 일관성 유지

        Args:
            arc_no: 현재 Arc 번호

        Returns:
            상태 제약 프롬프트 문자열
        """
        try:
            # DB에서 이전 Arc들 로드
            arcs_anchor = self.context.db.load_anchor("arcs")
            if not arcs_anchor:
                return ""

            prev_arcs = []
            for i in range(1, arc_no):
                arc_key = f"arc_{i}"
                if arc_key in arcs_anchor:
                    prev_arcs.append(arcs_anchor[arc_key])

            if not prev_arcs:
                return ""

            # 통합 StateTracker 생성
            from .state_tracker import create_tracker_from_arcs

            master_tracker = create_tracker_from_arcs(prev_arcs)

            # 제약 프롬프트 생성
            return master_tracker.generate_constraint_prompt()

        except Exception as e:
            logging.warning(f"⚠️ [Analyst] 상태 제약 프롬프트 생성 실패: {e}")
            return ""
