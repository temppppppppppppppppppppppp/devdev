"""
[V60.14] State-Locked Arc Generator
상태 잠금 기반 Arc 생성 - 구조적으로 모순 불가능

핵심 원칙:
1. 상태 잠금: arc_start_state는 생성하지 않고 복사
2. 관심사 분리: 창작 LLM과 추출 LLM 분리
3. 점진적 생성: 1화씩 생성+검증
4. 템플릿 강제: 구조 이탈 불가
5. 역방향 검증: 필요시 이전 Arc 수정
"""

import logging
import re

from modules.core.constants import AIModels
from modules.core.prompt_loader import SafeDict

from .base_agent import BaseAgent

# [V60.34] 화별 생성 템플릿 - DraftValidator 호환 형식으로 수정
EPISODE_TEMPLATE = """
[V60.34 STATE-LOCKED EPISODE GENERATOR]

🔒 주인공: {protagonist_name} (반드시 이 이름 사용!)
🔒 시작 상태: 위치={start_location}, 내공={start_energy}%, 부상={start_injuries}, 소지품={start_equipment}

### 임무
제 {ep_num}화의 전술 문서를 작성하세요.

### Arc 전체 방향 (Treatment Block 원문)
{arc_direction}

### 이번 화 핵심 비트
{episode_beat}

### 이전 화 요약
{prev_episode_summary}

### 출력 형식 (반드시 준수!)
아래 형식으로 600자 이상 작성하세요:

## 제 {ep_num}화: [제목]

{protagonist_name}은(는) {start_location}에서 [상황 묘사로 시작].

(핵심 비트에 맞는 상세한 전개. 600자 이상.)
- 갈등/위기 상황 묘사
- 주인공의 대응과 행동
- 결과와 상태 변화

【화 종료 상태】
- 위치: [종료 시 위치]
- 내공: [소모 후 %]
- 부상: [부상 상태]
- 획득: [새 아이템 또는 "없음"]
- 소모: [사용 아이템 또는 "없음"]

⚠️ 반드시 "## 제 {ep_num}화:" 형식으로 시작하세요!
⚠️ 본문 600자 이상 필수!
"""


# 상태 추출 프롬프트
STATE_EXTRACTION_PROMPT = """
[V60.14 STATE EXTRACTOR]

아래 에피소드 본문에서 종료 상태를 추출하세요.

### 에피소드 본문
{episode_text}

### 시작 상태 (참고용)
- 내공: {start_energy}%
- 부상: {start_injuries}

### 출력 (JSON)
{{
    "end_location": "종료 위치",
    "end_energy": 숫자(0-100),
    "end_injuries": "부상 상태 또는 '없음'",
    "items_acquired": ["획득 아이템"],
    "items_consumed": ["소모 아이템"],
    "key_events": ["핵심 사건 1줄 요약"]
}}

숫자는 반드시 정수로. 내공 소모가 명시되지 않으면 시작 상태 유지.
"""


# Arc 통합 프롬프트
ARC_SYNTHESIS_PROMPT = """
[V60.14 ARC SYNTHESIZER]

5개 에피소드를 하나의 Arc로 통합하세요.

### 에피소드들
{episodes}

### Arc 정보
- Arc 번호: {arc_no}
- 에피소드 범위: {ep_start} ~ {ep_end}

### 시작 상태 (Arc 전체)
{arc_start_state}

### 종료 상태 (마지막 에피소드 기준)
{arc_end_state}

### 출력 (JSON)
{{
    "arc_no": {arc_no},
    "ep_count": 5,
    "ep_start": {ep_start},
    "ep_end": {ep_end},
    "title": "Arc 제목",
    "tactical_doc": "5개 에피소드 본문 통합 (제 N화: 형식 유지)",
    "beat_sequence": ["제 N화: 핵심 비트", ...],
    "state_constraints": {{
        "arc_start_state": {arc_start_state},
        "arc_end_state": {arc_end_state},
        "items_acquired": ["Arc 전체에서 획득한 아이템"],
        "items_consumed": ["Arc 전체에서 소모한 아이템"]
    }},
    "joint_docs": {{
        "final_location": "Arc 종료 위치",
        "physical_inventory": ["종료 시 전체 소지품"],
        "world_joint": "세계 변화 요약"
    }},
    "status_shadow": {{
        "internal_energy_loss": "총 소모량%",
        "expected_injuries": "최종 부상 상태",
        "item_consumption": ["소모 아이템"]
    }}
}}
"""


# [V60.17] Speculative Refinement 프롬프트
SPECULATIVE_REFINE_PROMPT = """
[V60.17 SPECULATIVE REFINER]

아래 초안을 고품질로 정제하세요.

### 주인공
{protagonist_name}

### 초안
{draft}

### 정제 지침
1. 문장을 더 유려하고 생동감 있게 다듬으세요
2. 감각적 묘사(시각, 청각, 촉각)를 보강하세요
3. 주인공 '{protagonist_name}'의 심리/감정을 깊이 있게 표현하세요
4. 대사를 더 자연스럽고 캐릭터에 맞게 수정하세요
5. [시작 상태]와 [종료 상태]는 그대로 유지하세요

### 출력
정제된 전체 에피소드 (원본 형식 유지)
"""


class StateLockedArcGenerator(BaseAgent):
    """
    [V60.14] 상태 잠금 기반 Arc 생성기

    구조적으로 상태 모순이 불가능한 설계
    """

    def __init__(self, context, client, model_tier: str = None):
        super().__init__(context, client, model_tier)
        # DI 후보: protagonist_name (getattr fallback, L367 — 생성 시마다 조회)
        self.extraction_model = AIModels.STAGE2_EXTRACTION_MODEL  # [SSOT]
        self.draft_model = AIModels.STAGE2_MAIN_MODEL  # [SSOT]
        self.refine_model = self.primary_model  # [V60.17] Speculative: 정제용 고급 모델
        self.use_speculative = True  # [V60.17] Speculative Generation 활성화

    def generate(
        self,
        arc_no: int,
        ep_start: int,
        prev_arc: dict | None,
        arc_direction: str,
        episode_beats: list[str],
        assets: dict = None,
        protagonist_name: str = "주인공",
    ) -> tuple[dict | None, dict]:
        """
        상태 잠금 방식으로 Arc 생성

        Args:
            arc_no: Arc 번호
            ep_start: 시작 화수
            prev_arc: 이전 Arc (없으면 None)
            arc_direction: Arc 전체 방향/목표
            episode_beats: 5개 화별 핵심 비트
            assets: AssetLibrary
            protagonist_name: 주인공 이름 (필수!)

        Returns:
            (generated_arc, generation_log)
        """
        # [V60.16] 주인공 이름 저장
        self.protagonist_name = protagonist_name
        log = {"arc_no": arc_no, "phases": [], "episodes": [], "success": False}

        # ═══════════════════════════════════════════════════════════════
        # Phase A: 시작 상태 잠금 (복사, LLM 개입 없음)
        # ═══════════════════════════════════════════════════════════════
        start_state = self._lock_start_state(prev_arc)
        log["phases"].append({"phase": "A", "name": "State Lock", "result": start_state})
        logging.info(f" [Phase A] 시작 상태 잠금: 내공 {start_state['energy']}%, 부상: {start_state['injuries']}")

        # ═══════════════════════════════════════════════════════════════
        # Phase B: 점진적 에피소드 생성 (1화씩)
        # ═══════════════════════════════════════════════════════════════
        episodes = []
        current_state = start_state.copy()

        for i, beat in enumerate(episode_beats[:5]):  # 최대 5화
            ep_num = ep_start + i
            logging.info(f" [Phase B] 제 {ep_num}화 생성 중...")

            # 에피소드 생성
            episode = self._generate_episode(
                ep_num=ep_num,
                start_state=current_state,
                arc_direction=arc_direction,
                episode_beat=beat,
                prev_episode=episodes[-1] if episodes else None,
            )

            if not episode:
                log["phases"].append({"phase": "B", "error": f"Episode {ep_num} failed"})
                return None, log

            # 상태 추출 (관심사 분리)
            end_state = self._extract_state(episode["text"], current_state)
            episode["start_state"] = current_state.copy()
            episode["end_state"] = end_state

            episodes.append(episode)
            log["episodes"].append(
                {
                    "ep_num": ep_num,
                    "start_energy": current_state["energy"],
                    "end_energy": end_state["energy"],
                    "items_acquired": end_state.get("items_acquired", []),
                }
            )

            # 다음 화의 시작 상태 = 이번 화의 종료 상태
            current_state = {
                "location": end_state["location"],
                "energy": end_state["energy"],
                "injuries": end_state["injuries"],
                "equipment": [
                    str(x) if isinstance(x, dict) else x
                    for x in current_state.get("equipment", []) + end_state.get("items_acquired", [])
                ],
            }
            # 소모 아이템 제거
            for item in end_state.get("items_consumed", []):
                if item in current_state["equipment"]:
                    current_state["equipment"].remove(item)

            logging.info(f"✅ [Phase B] 제 {ep_num}화 완료: 내공 {current_state['energy']}%")

        log["phases"].append({"phase": "B", "name": "Progressive Generation", "episodes_count": len(episodes)})

        # ═══════════════════════════════════════════════════════════════
        # Phase C: Arc 통합 + 최종 상태 확정
        # ═══════════════════════════════════════════════════════════════
        logging.info(" [Phase C] Arc 통합 중...")

        final_arc = self._synthesize_arc(
            arc_no=arc_no,
            ep_start=ep_start,
            ep_end=ep_start + len(episodes) - 1,
            episodes=episodes,
            start_state=start_state,
            end_state=current_state,
        )

        if not final_arc:
            log["phases"].append({"phase": "C", "error": "Synthesis failed"})
            return None, log

        log["phases"].append({"phase": "C", "name": "Arc Synthesis", "success": True})

        # ═══════════════════════════════════════════════════════════════
        # Phase D: 역방향 검증 (선택적)
        # ═══════════════════════════════════════════════════════════════
        if prev_arc:
            mismatch = self._check_reverse_consistency(prev_arc, start_state)
            if mismatch:
                log["phases"].append(
                    {"phase": "D", "name": "Reverse Validation", "mismatch": mismatch, "action": "Would fix prev_arc"}
                )
                logging.info(f" [Phase D] 역방향 불일치 감지: {mismatch}")

        log["success"] = True
        logging.info(f"✅ [V60.14] Arc {arc_no} 생성 완료!")

        return final_arc, log

    def _lock_start_state(self, prev_arc: dict | None) -> dict:
        """
        Phase A: 시작 상태 잠금
        이전 Arc의 종료 상태를 그대로 복사 (LLM 개입 없음)
        """
        if not prev_arc:
            # 첫 Arc - 기본 상태
            return {"location": "서사 시작점", "energy": 100, "injuries": "없음", "equipment": []}

        # 이전 Arc의 arc_end_state에서 복사
        state_constraints = prev_arc.get("state_constraints", {})
        arc_end = state_constraints.get("arc_end_state", {})
        joint_docs = prev_arc.get("joint_docs", {})

        # 내공
        energy = arc_end.get("internal_energy")
        if energy is None:
            shadow = prev_arc.get("status_shadow", {})
            loss_str = shadow.get("internal_energy_loss", "0%")
            try:
                loss = int(re.search(r"(\d+)", str(loss_str)).group(1))
                energy = max(0, 100 - loss)
            except (ValueError, AttributeError, TypeError):  # [V64.P4] energy parse failure
                # [V60.73] 보수적 기본값 50 (파싱 실패 시 만땅 가정 위험)
                logging.warning(f" [V60.73] internal_energy_loss 파싱 실패: '{loss_str}' → 50% 가정")
                energy = 50

        # 부상
        injuries = arc_end.get("injuries")
        if not injuries:
            injuries = prev_arc.get("status_shadow", {}).get("expected_injuries", "없음")

        # 위치
        location = arc_end.get("location") or joint_docs.get("final_location", "알 수 없음")

        # 소지품
        equipment = arc_end.get("equipment")
        if equipment is None:
            equipment = joint_docs.get("physical_inventory", [])
        if isinstance(equipment, str):
            equipment = [e.strip() for e in equipment.split(",") if e.strip()]

        return {"location": location, "energy": energy, "injuries": injuries, "equipment": equipment}

    def _generate_episode(
        self, ep_num: int, start_state: dict, arc_direction: str, episode_beat: str, prev_episode: dict | None
    ) -> dict | None:
        """
        [V60.17] Phase B: Speculative Generation

        1단계: Flash 모델로 빠르게 초안 생성 (~2초)
        2단계: Pro 모델로 정제/보강 (~5초)
        총: ~7초 (기존 ~15초 대비 50% 단축)
        """
        prev_summary = ""
        if prev_episode:
            prev_summary = prev_episode.get("text", "")[:500] + "..."

        equipment_str = (
            ", ".join(str(x) if isinstance(x, dict) else x for x in start_state.get("equipment", [])) or "없음"
        )
        protag_name = getattr(self, "protagonist_name", "주인공")

        prompt = EPISODE_TEMPLATE.format_map(
            SafeDict(
                ep_num=ep_num,
                protagonist_name=protag_name,
                start_location=self._escape_braces(str(start_state["location"])),
                start_energy=start_state["energy"],
                start_injuries=self._escape_braces(str(start_state["injuries"])),
                start_equipment=self._escape_braces(equipment_str),
                arc_direction=self._escape_braces(arc_direction),
                episode_beat=self._escape_braces(episode_beat),
                prev_episode_summary=self._escape_braces(prev_summary) or "(첫 화)",
            )
        )

        try:
            # [V60.17] Speculative Generation
            if self.use_speculative:
                # 1단계: Flash로 빠른 초안 생성
                old_model = self.primary_model
                try:  # [V70] try/finally로 모델 복원 보장
                    self.primary_model = self.draft_model

                    draft_response = self.ask(prompt, temperature=0.8, thinking_level="low")

                    if isinstance(draft_response, dict):
                        draft = draft_response.get("text", str(draft_response))
                    else:
                        draft = str(draft_response)

                    # 2단계: Pro로 정제 (초안이 충분하면)
                    if len(draft) >= 400:
                        self.primary_model = self.refine_model

                        refine_prompt = SPECULATIVE_REFINE_PROMPT.format_map(
                            SafeDict(protagonist_name=protag_name, draft=self._escape_braces(draft))
                        )

                        # [V60.25] Thinking Level 활용 - 정제 단계에서 medium 사용
                        refined_response = self.ask(refine_prompt, temperature=0.5, thinking_level="medium")

                        if isinstance(refined_response, dict):
                            text = refined_response.get("text", str(refined_response))
                        else:
                            text = str(refined_response)

                        # 정제 실패 시 초안 사용
                        if len(text) < len(draft) * 0.5:
                            text = draft
                    else:
                        # 초안 부족 시 그대로 사용
                        text = draft
                finally:
                    self.primary_model = old_model  # [V70] 예외 시에도 모델 복원
            else:
                # 기존 방식: 고급 모델로 직접 생성
                # [V60.25] Thinking Level 활용 - medium으로 추론 품질 향상
                response = self.ask(prompt, temperature=0.7, thinking_level="medium")
                if isinstance(response, dict):
                    text = response.get("text", str(response))
                else:
                    text = str(response)

            return {"ep_num": ep_num, "text": text, "beat": episode_beat}

        except Exception as e:
            logging.warning(f"❌ [Episode] 생성 실패: {e}")
            return None

    def _extract_state(self, episode_text: str, start_state: dict) -> dict:
        """
        Phase B-2: 에피소드에서 종료 상태 추출 (관심사 분리)
        """
        prompt = STATE_EXTRACTION_PROMPT.format_map(
            SafeDict(
                episode_text=self._escape_braces(episode_text[:3000]),
                start_energy=start_state["energy"],
                start_injuries=self._escape_braces(str(start_state["injuries"])),
            )
        )

        try:
            # 추출은 저렴한 모델 (BaseAgent는 primary_model 사용)
            old_model = self.primary_model
            try:  # [V70] 예외 시 primary_model 복원 보장
                self.primary_model = self.extraction_model
                response = self.ask(prompt, temperature=0.1, thinking_level="low")
            finally:
                self.primary_model = old_model

            if isinstance(response, str):
                response = self._extract_json_robust(response)  # [V70] json.loads → robust

            try:
                end_energy = int(response.get("end_energy", start_state.get("energy", 50)))
            except (ValueError, TypeError):
                end_energy = start_state.get("energy", 50)

            return {
                "location": response.get("end_location", start_state["location"]),
                "energy": end_energy,
                "injuries": response.get("end_injuries", start_state["injuries"]),
                "items_acquired": response.get("items_acquired", []),
                "items_consumed": response.get("items_consumed", []),
                "key_events": response.get("key_events", []),
            }

        except Exception as e:
            logging.warning(f" [Extract] 추출 실패, 시작 상태 유지: {e}")
            return {
                "location": start_state["location"],
                "energy": start_state["energy"],
                "injuries": start_state["injuries"],
                "items_acquired": [],
                "items_consumed": [],
                "key_events": [],
            }

    def _synthesize_arc(
        self, arc_no: int, ep_start: int, ep_end: int, episodes: list[dict], start_state: dict, end_state: dict
    ) -> dict | None:
        """
        Phase C: 에피소드들을 Arc로 통합
        """
        # tactical_doc 조립 (이미 생성된 에피소드들 연결)
        tactical_parts = []
        beat_sequence = []
        all_acquired = []
        all_consumed = []

        for ep in episodes:
            tactical_parts.append(ep["text"])
            beat_sequence.append(f"제 {ep['ep_num']}화: {ep['beat'][:50]}")
            all_acquired.extend(ep.get("end_state", {}).get("items_acquired", []))
            all_consumed.extend(ep.get("end_state", {}).get("items_consumed", []))

        tactical_doc = "\n\n".join(tactical_parts)

        # 최종 소지품 계산
        final_equipment = list(start_state.get("equipment", []))
        for item in all_acquired:
            if item not in final_equipment:
                final_equipment.append(item)
        for item in all_consumed:
            if item in final_equipment:
                final_equipment.remove(item)

        # 내공 손실 계산
        energy_loss = start_state["energy"] - end_state["energy"]

        return {
            "arc_no": arc_no,
            "ep_count": len(episodes),
            "ep_start": ep_start,
            "ep_end": ep_end,
            "title": f"Arc {arc_no}",  # 나중에 개선 가능
            "tactical_doc": tactical_doc,
            "beat_sequence": beat_sequence,
            "state_constraints": {
                "arc_start_state": {
                    "location": start_state["location"],
                    "equipment": start_state.get("equipment", []),
                    "injuries": start_state["injuries"],
                    "internal_energy": start_state["energy"],
                },
                "arc_end_state": {
                    "location": end_state["location"],
                    "equipment": final_equipment,
                    "injuries": end_state["injuries"],
                    "internal_energy": end_state["energy"],
                },
                "items_acquired": list({str(x) if isinstance(x, dict) else x for x in all_acquired}),
                "items_consumed": list({str(x) if isinstance(x, dict) else x for x in all_consumed}),
            },
            "joint_docs": {
                "final_location": end_state["location"],
                "physical_inventory": final_equipment,
                "world_joint": "",  # 추후 생성
            },
            "status_shadow": {
                "internal_energy_loss": f"{energy_loss}%",
                "expected_injuries": end_state["injuries"],
                "item_consumption": list({str(x) if isinstance(x, dict) else x for x in all_consumed}),
            },
        }

    def _check_reverse_consistency(self, prev_arc: dict, current_start: dict) -> str | None:
        """
        Phase D: 역방향 일관성 검사
        이전 Arc의 종료 상태와 현재 시작 상태가 일치하는지 확인
        """
        prev_end = prev_arc.get("state_constraints", {}).get("arc_end_state", {})

        mismatches = []

        prev_energy = prev_end.get("internal_energy")
        if prev_energy is not None and prev_energy != current_start["energy"]:
            mismatches.append(f"내공: {prev_energy} vs {current_start['energy']}")

        prev_injuries = prev_end.get("injuries")
        if prev_injuries and prev_injuries != current_start["injuries"]:
            mismatches.append(f"부상: {prev_injuries} vs {current_start['injuries']}")

        return "; ".join(mismatches) if mismatches else None

    def _escape_braces(self, text: str) -> str:
        """중괄호 이스케이프"""
        if not isinstance(text, str):
            return str(text) if text else ""
        return text.replace("{", "{{").replace("}", "}}")


def create_state_locked_generator(context, client, model_tier: str = "gemini-2.5-pro"):
    """[V60.24] StateLockedArcGenerator 생성 헬퍼 - Gemini 3 사용"""
    return StateLockedArcGenerator(context, client, model_tier)
