"""
[V60.12] Preflight Checker
생성 전 완벽한 제약 맵 구축 - 모든 이전 Arc를 철저히 분석

목적:
- 생성 전에 모든 제약 조건을 LLM이 완벽히 이해하도록 함
- 단순 목록이 아닌 "왜 금지인지" 맥락까지 제공
- 초기 통과율 극대화

비용: ~$0.03-0.05/Arc (gemini-2.5-pro 사용)
"""

import json
import logging
import re

from modules.core.constants import ContextLimits
from modules.core.prompt_loader import SafeDict

from .base_agent import BaseAgent

PREFLIGHT_ANALYSIS_PROMPT = """
[V60.12 PREFLIGHT CHECKER - 생성 전 완벽 분석]

당신은 Arc 생성 전 모든 제약 조건을 분석하는 전문가입니다.
다음 Arc를 설계하기 위해 이전 Arc들을 철저히 분석하세요.

### 분석 대상: Arc 1 ~ Arc {prev_arc_count}

{prev_arcs_data}

### 분석 지시

1. **아이템 타임라인 완전 분석**
   - 각 Arc에서 획득한 모든 아이템 (언제, 어디서, 어떻게)
   - 현재 주인공이 소지 중인 아이템 전체 목록
   - 소모/분실된 아이템과 그 시점

2. **수여물/권한 타임라인**
   - 누구에게 무엇을 수여받았는지
   - 수여 후 위상 변화
   - 현재 보유 중인 모든 수여물

3. **관계 상태 맵**
   - 주요 NPC별 현재 관계 상태
   - 관계 변화 이력 (언제, 왜 변했는지)

4. **세계 상태**
   - 현재 위치
   - 알려진 정보
   - 진행 중인 갈등/사건 (아직 해결되지 않은 것만)
   - 완결된 갈등/사건 (이미 해결되어 재생성하면 안 되는 것)

5. **다음 Arc 절대 금지 사항**
   - 이미 획득한 아이템 재획득 시도
   - 이미 수여받은 것 재수여
   - 위치 순간이동
   - 이미 완결된 갈등/사건의 동일 반복
   - 부상 무시

### 출력 형식 (JSON)

{{
    "timeline_analysis": {{
        "items": [
            {{"arc": 1, "episode": 2, "item": "대도", "action": "획득", "context": "장로에게서 하사"}}
        ],
        "grants": [
            {{"arc": 2, "episode": 4, "grant": "철혈사자패", "grantor": "단주", "significance": "정식 단원 인정"}}
        ],
        "current_inventory": ["대도", "철혈사자패", "금창약"],
        "consumed_items": []
    }},
    "relationship_map": {{
        "단주": {{"current_state": "경외", "history": ["Arc1: 무시 → Arc2: 인정"]}},
        "장로": {{"current_state": "신뢰", "history": ["Arc1: 의심 → 신뢰"]}}
    }},
    "world_state": {{
        "current_location": "철혈단 본거지",
        "known_information": ["적대 세력의 침입 계획"],
        "ongoing_conflicts": ["현재 진행 중인 갈등만"],
        "resolved_conflicts": ["이미 완결된 갈등 (재생성 금지)"],
        "resolved_plots_from_tracker": ["이전에 완결된 플롯 라인 (절대 반복 금지)"],
        "protagonist_status": {{
            "injuries": "왼팔 경상 (Arc 2에서 부상)",
            "internal_energy": 85,
            "martial_level": "일류 초입"
        }}
    }},
    "absolute_prohibitions": {{
        "items_cannot_acquire": [
            {{"item": "대도", "reason": "Arc 1 제2화에서 이미 획득", "violation_type": "DUPLICATE_ACQUISITION"}}
        ],
        "grants_cannot_receive": [
            {{"grant": "철혈사자패", "reason": "Arc 2 제4화에서 이미 수여받음", "violation_type": "DUPLICATE_GRANT"}}
        ],
        "state_constraints": [
            {{"constraint": "Arc 시작 위치는 '철혈단 본거지'여야 함", "reason": "Arc 2 종료 위치"}},
            {{"constraint": "왼팔 경상 상태로 시작", "reason": "Arc 2 종료 시 부상 상태"}}
        ]
    }},
    "next_arc_guidance": {{
        "must_start_with": "철혈단 본거지에서 왼팔 경상 상태로",
        "recommended_focus": "흑풍문과의 갈등 심화 또는 내부 음모",
        "available_resources": ["대도", "철혈사자패", "금창약"],
        "potential_new_acquisitions": ["새로운 무공 비급", "정보", "동료"],
        "warning": "절대로 이미 가진 것을 다시 획득하지 마세요"
    }}
}}

반드시 유효한 JSON만 출력하세요.
"""


class PreflightChecker(BaseAgent):
    """
    [V60.12] Preflight Checker

    생성 전 모든 이전 Arc를 분석하여 완벽한 제약 맵 구축
    """

    def __init__(self, context, client, model_tier: str = None):
        # [V60.24] Flash로 변경 (분석용)
        super().__init__(context, client, model_tier)
        # [V60.37] 스마트 폴백 (BaseAgent에서 자동 설정: gemini-3-flash → gemini-2.5-flash)

    def analyze(self, prev_arcs: list[dict], resolved_plots_summary: str = "") -> dict:
        """
        이전 Arc들을 완전 분석하여 제약 맵 생성

        Args:
            prev_arcs: 이전 Arc 리스트
            resolved_plots_summary: [V66] 완결 플롯 요약 문자열

        Returns:
            완벽한 제약 맵 딕셔너리
        """
        if not prev_arcs:
            return self._get_initial_state()

        # 이전 Arc 데이터 포맷팅
        prev_arcs_data = self._format_prev_arcs(prev_arcs)

        # [V66] 완결 플롯 섹션 주입
        if resolved_plots_summary:
            prev_arcs_data += f"\n\n### 완결 플롯 (절대 재발생 금지)\n{resolved_plots_summary}"

        prompt = PREFLIGHT_ANALYSIS_PROMPT.format_map(
            SafeDict(
                prev_arc_count=len(prev_arcs),
                prev_arcs_data=self._escape_braces(prev_arcs_data),  # [V70] JSON 중괄호 이스케이프
            )
        )

        try:
            result = self.ask(prompt, temperature=0.2)  # 낮은 온도로 정확성 우선

            if isinstance(result, str):
                result = self._extract_json_robust(result)

            # [Sweep55] LLM이 list 반환 시 첫 dict 추출
            if isinstance(result, list):
                result = result[0] if result and isinstance(result[0], dict) else {}
            if not isinstance(result, dict):
                result = {}

            # 필수 필드 보장
            result = self._ensure_required_fields(result)

            return result

        except Exception as e:
            logging.warning(f"⚠️ [Preflight] 분석 오류: {str(e)[:50]}")
            return self._extract_constraints_fallback(prev_arcs)

    # [V63] 윈도잉 상수: 상세 분석할 최근 Arc 수 (3→5 확장)
    DETAIL_WINDOW = 5
    # [V63] 오래된 Arc 요약 최대 개수 (10→20 확장)
    MAX_OLD_SUMMARY = 20

    def _format_prev_arcs(self, prev_arcs: list[dict]) -> str:
        """[V67] 이전 Arc 데이터를 전문 포맷팅 (Gemini 대용량 컨텍스트 활용)
        - 최근 DETAIL_WINDOW개: 최상세 (tactical_doc + state + joint + shadow)
        - 나머지 Arc: tactical_doc 전문 + 핵심 메타데이터
        - 200K자 상한
        """
        lines = []
        window = self.DETAIL_WINDOW
        old_arcs = prev_arcs[:-window] if len(prev_arcs) > window else []
        recent_arcs = prev_arcs[-window:]

        # ── [V67] 오래된 Arc: tactical_doc 전문 + 메타데이터 ──
        if old_arcs:
            lines.append(f"\n[Arc 1~{old_arcs[-1].get('arc_no', '?')} 전문 ({len(old_arcs)}개)]")
            lines.append("-" * 40)
            for arc in old_arcs:
                arc_no = arc.get("arc_no", "?")
                title = (arc.get("title") or "")[:50]
                ep_s = arc.get("ep_start", "?")
                ep_e = arc.get("ep_end", "?")
                end_loc = arc.get("joint_docs", {}).get("final_location", "?")
                items = (arc.get("state_constraints") or {}).get("items_acquired", [])  # [V70] None 방어
                item_str = (
                    ", ".join(str(x) if isinstance(x, dict) else x for x in items[:10])
                    if isinstance(items, list) and items
                    else "없음"
                )
                # 핵심 NPC 추출 (deaths + relationship_changes)
                sc = arc.get("state_changes", {})
                key_npcs = set()
                for d in sc.get("npc_deaths", []) if isinstance(sc, dict) else []:
                    if isinstance(d, dict) and d.get("name"):
                        key_npcs.add(d["name"] + "(사망)")
                for r in sc.get("relationship_changes", []) if isinstance(sc, dict) else []:
                    if isinstance(r, dict) and r.get("npc"):
                        key_npcs.add(r["npc"])
                npc_str = ", ".join(list(key_npcs)[:5]) if key_npcs else "없음"
                world_joint = arc.get("joint_docs", {}).get("world_joint", "")

                lines.append(f"\n{'=' * 50}")
                lines.append(f"[ARC {arc_no}] {title} (제{ep_s}화~제{ep_e}화)")
                lines.append(f"{'=' * 50}")
                lines.append(f"  종료위치: {end_loc}")
                lines.append(f"  획득아이템: {item_str}")
                lines.append(f"  핵심NPC: {npc_str}")
                lines.append(f"  세계변화: {world_joint or '없음'}")

                # [V67] tactical_doc 전문 포함 (절삭 없음)
                tactical = arc.get("tactical_doc", "")
                if isinstance(tactical, dict):
                    tactical = json.dumps(tactical, ensure_ascii=False)
                if tactical:
                    lines.append(f"\n[전술 문서 전문]\n{tactical}")
            lines.append("")

        # ── 최근 Arc: 최상세 ──
        for arc in recent_arcs:
            arc_no = arc.get("arc_no", "?")
            lines.append(f"\n{'=' * 60}")
            lines.append(f"[ARC {arc_no}] (상세)")
            lines.append(f"{'=' * 60}")

            tactical = arc.get("tactical_doc", "")
            if isinstance(tactical, dict):
                tactical = json.dumps(tactical, ensure_ascii=False)
            if tactical:
                lines.append(f"\n[전술 문서]\n{tactical}")

            state = arc.get("state_constraints", {})
            if state:
                lines.append(f"\n[상태 제약]\n{json.dumps(state, ensure_ascii=False, indent=2)}")

            joint = arc.get("joint_docs", {})
            if joint:
                lines.append(f"\n[연결 문서]\n{json.dumps(joint, ensure_ascii=False, indent=2)}")

            shadow = arc.get("status_shadow", {})
            if shadow:
                lines.append(f"\n[상태 그림자]\n{json.dumps(shadow, ensure_ascii=False, indent=2)}")

        total_chars = sum(len(l) for l in lines)
        # [V67] 200K자 상한 적용
        result = "\n".join(lines)
        if len(result) > ContextLimits.MAX_CONTEXT_CHARS:
            result = result[: ContextLimits.MAX_CONTEXT_CHARS] + "\n... (200K자 절삭)"
        logging.info(f"📊 [V67] Preflight 전문: {len(old_arcs)}개 전문 + {len(recent_arcs)}개 상세 ({total_chars:,}자)")
        return result

    def _ensure_required_fields(self, result: dict) -> dict:
        """필수 필드 보장"""
        if "timeline_analysis" not in result:
            result["timeline_analysis"] = {"items": [], "grants": [], "current_inventory": [], "consumed_items": []}

        if "relationship_map" not in result:
            result["relationship_map"] = {}

        if "world_state" not in result:
            result["world_state"] = {
                "current_location": "알 수 없음",
                "known_information": [],
                "ongoing_conflicts": [],
                "resolved_conflicts": [],
                "protagonist_status": {},
            }
        else:
            if "resolved_conflicts" not in result["world_state"]:
                result["world_state"]["resolved_conflicts"] = []

        if "absolute_prohibitions" not in result:
            result["absolute_prohibitions"] = {
                "items_cannot_acquire": [],
                "grants_cannot_receive": [],
                "state_constraints": [],
            }

        if "next_arc_guidance" not in result:
            result["next_arc_guidance"] = {
                "must_start_with": "",
                "recommended_focus": "",
                "available_resources": [],
                "potential_new_acquisitions": [],
                "warning": "",
            }

        return result

    def _get_initial_state(self) -> dict:
        """첫 Arc용 초기 상태"""
        return {
            "timeline_analysis": {"items": [], "grants": [], "current_inventory": [], "consumed_items": []},
            "relationship_map": {},
            "world_state": {
                "current_location": "서사 시작점",
                "known_information": [],
                "ongoing_conflicts": [],
                "resolved_conflicts": [],
                "protagonist_status": {"injuries": "없음", "internal_energy": 100, "martial_level": "초기"},
            },
            "absolute_prohibitions": {"items_cannot_acquire": [], "grants_cannot_receive": [], "state_constraints": []},
            "next_arc_guidance": {
                "must_start_with": "서사 시작점에서 출발",
                "recommended_focus": "세계관 소개 + 주인공 소개 + 첫 갈등",
                "available_resources": [],
                "potential_new_acquisitions": ["첫 무기", "첫 동료", "첫 적"],
                "warning": "첫 Arc이므로 과도한 파워업 금지",
            },
        }

    def _extract_constraints_fallback(self, prev_arcs: list[dict]) -> dict:
        """LLM 실패 시 Python 폴백으로 제약 추출"""
        items = set()
        grants = set()
        last_location = "알 수 없음"
        last_injuries = "없음"
        last_energy = 100

        for arc in prev_arcs:
            # items_acquired
            acquired = (arc.get("state_constraints") or {}).get("items_acquired", [])  # [V70] None 방어
            if isinstance(acquired, list):
                items.update(str(x) if isinstance(x, dict) else x for x in acquired)

            # grants_received
            received = (arc.get("state_constraints") or {}).get("grants_received", [])  # [V70] None 방어
            if isinstance(received, list):
                grants.update(str(x) if isinstance(x, dict) else x for x in received)

            # 마지막 위치
            joint = arc.get("joint_docs") or {}  # [V70] None 방어
            if joint.get("final_location"):
                last_location = joint["final_location"]

            # [V60.13 FIX] arc_end_state 우선 사용
            state_constraints = arc.get("state_constraints") or {}  # [V70] None 방어
            arc_end_state = state_constraints.get("arc_end_state", {})
            shadow = arc.get("status_shadow", {})

            # 내공: arc_end_state 우선
            if arc_end_state.get("internal_energy") is not None:
                last_energy = arc_end_state["internal_energy"]
            elif shadow.get("internal_energy_loss"):
                try:
                    loss = int(re.search(r"(\d+)", str(shadow["internal_energy_loss"])).group(1))
                    last_energy = max(0, last_energy - loss)
                except (ValueError, AttributeError, TypeError):  # [V64.P4] energy parse failure
                    pass

            # 부상: arc_end_state 우선
            if arc_end_state.get("injuries"):
                last_injuries = arc_end_state["injuries"]
            elif shadow.get("expected_injuries"):
                last_injuries = shadow["expected_injuries"]

        return {
            "timeline_analysis": {
                "items": [{"item": i, "action": "획득"} for i in items],
                "grants": [{"grant": g} for g in grants],
                "current_inventory": list(items),
                "consumed_items": [],
            },
            "relationship_map": {},
            "world_state": {
                "current_location": last_location,
                "known_information": [],
                "ongoing_conflicts": [],
                "resolved_conflicts": [],
                "protagonist_status": {"injuries": last_injuries, "internal_energy": last_energy},
            },
            "absolute_prohibitions": {
                "items_cannot_acquire": [
                    {"item": i, "reason": "이미 획득", "violation_type": "DUPLICATE_ACQUISITION"} for i in items
                ],
                "grants_cannot_receive": [
                    {"grant": g, "reason": "이미 수여받음", "violation_type": "DUPLICATE_GRANT"} for g in grants
                ],
                "state_constraints": [
                    {"constraint": f"시작 위치: {last_location}", "reason": "이전 Arc 종료 위치"},
                    {"constraint": f"부상 상태: {last_injuries}", "reason": "이전 Arc 종료 시 상태"},
                ],
            },
            "next_arc_guidance": {
                "must_start_with": f"{last_location}에서 시작",
                "available_resources": list(items),
                "warning": "이미 획득한 아이템 재획득 금지",
            },
        }

    def generate_analyst_injection(self, preflight_result: dict, genre: str = "") -> str:
        """Analyst 프롬프트에 주입할 제약 텍스트 생성"""
        # 절대 금지 사항
        prohibitions = preflight_result.get("absolute_prohibitions", {})
        items_forbidden = prohibitions.get("items_cannot_acquire", [])

        lines = []

        # [V60.28] 금지 아이템이 있으면 최상단에 대형 경고
        if items_forbidden:
            lines.append("")
            lines.append("█" * 72)
            lines.append("█" + " " * 70 + "█")
            lines.append("█" + "  🚨🚨🚨 절대 획득 금지 아이템 🚨🚨🚨  ".center(70) + "█")
            lines.append("█" + " " * 70 + "█")
            lines.append("█" * 72)
            lines.append("")
            for item in items_forbidden:
                item_name = item.get("item", item) if isinstance(item, dict) else item
                lines.append(f"  ❌ '{item_name}' → items_acquired에 포함 시 즉시 REJECT!")
            lines.append("")
            lines.append("█" * 72)
            lines.append("")

        lines.append("╔" + "═" * 70 + "╗")
        lines.append("║" + " [V60.12 PREFLIGHT ANALYSIS - 생성 전 필수 확인] ".center(70) + "║")
        lines.append("╚" + "═" * 70 + "╝")
        lines.append("")

        lines.append("🚫 [절대 금지 - 위반 시 즉시 REJECT]")
        lines.append("-" * 50)

        # 아이템 금지 (상세)
        if items_forbidden:
            lines.append("❌ 다음 아이템 획득 금지 (이미 보유 중):")
            for item in items_forbidden:
                item_name = item.get("item", item) if isinstance(item, dict) else item
                reason = item.get("reason", "") if isinstance(item, dict) else ""
                lines.append(f"   • {item_name} - {reason}")

        # 수여물 금지
        grants_forbidden = prohibitions.get("grants_cannot_receive", [])
        if grants_forbidden:
            lines.append("❌ 다음 수여물 재수여 금지:")
            for grant in grants_forbidden:
                grant_name = grant.get("grant", grant) if isinstance(grant, dict) else grant
                reason = grant.get("reason", "") if isinstance(grant, dict) else ""
                lines.append(f"   • {grant_name} - {reason}")

        lines.append("")

        # 필수 계승 상태
        world = preflight_result.get("world_state", {})
        guidance = preflight_result.get("next_arc_guidance", {})

        lines.append("📋 [필수 계승 상태]")
        lines.append("-" * 50)
        lines.append(f"🗺️ 시작 위치: {world.get('current_location', '알 수 없음')}")

        status = world.get("protagonist_status", {})
        if not isinstance(status, dict):
            status = {}
        _is_wuxia = genre in ("wuxia", "무협", "")  # 기본값은 무협 (하위호환)
        if _is_wuxia:
            if status.get("injuries") and status["injuries"] != "없음":
                lines.append(f"💔 부상 상태: {status['injuries']}")
            lines.append(f"⚡ 내공: {status.get('internal_energy', 100)}%")
        # 비무협: 내공/부상 라인 생략 (LLM 혼동 방지)

        inventory = preflight_result.get("timeline_analysis", {}).get("current_inventory", [])
        if inventory:
            lines.append(f"📦 소지품: {', '.join(str(i) for i in inventory[:10])}")

        lines.append("")

        # 가이드
        lines.append("💡 [다음 Arc 가이드]")
        lines.append("-" * 50)
        if guidance.get("must_start_with"):
            lines.append(f"시작: {guidance['must_start_with']}")
        if guidance.get("recommended_focus"):
            lines.append(f"권장: {guidance['recommended_focus']}")
        if guidance.get("potential_new_acquisitions"):
            lines.append(f"획득 가능: {', '.join(guidance['potential_new_acquisitions'][:5])}")
        if guidance.get("warning"):
            lines.append(f"⚠️ 경고: {guidance['warning']}")

        lines.append("")

        return "\n".join(lines)


def create_preflight_checker(context, client, model_tier: str = "gemini-2.5-pro"):
    """[V62.4] PreflightChecker 생성 헬퍼 - gemini-2.5-pro 사용"""
    return PreflightChecker(context, client, model_tier)
