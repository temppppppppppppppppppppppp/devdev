"""
[V60.11] Constraint Compiler
이전 Arc들의 제약 조건을 구조화된 체크리스트로 컴파일

목적:
- Analyst가 명확하게 제약을 파악할 수 있도록 구조화
- LLM이 무시하기 어려운 형식으로 제약 표현
- 중복 제약 통합 및 우선순위 지정

출력 형식:
- MUST DO (필수 사항)
- MUST NOT DO (금지 사항)
- SHOULD DO (권장 사항)
- INHERITED STATE (계승해야 할 상태)
"""

import json
import re

from modules.core.genre_schema_builder import get_item_suffixes


def _normalize_item_list(raw_items) -> list[str]:
    if raw_items is None:
        return []
    if isinstance(raw_items, str):
        raw_items = [item.strip() for item in raw_items.split(",") if item.strip()]
    if not isinstance(raw_items, list):
        return []

    normalized: list[str] = []
    for item in raw_items:
        if isinstance(item, dict):
            value = item.get("name") or item.get("item") or ""
        else:
            value = item
        text = str(value).strip() if value is not None else ""
        if text:
            normalized.append(text)
    return normalized


def _resolve_protagonist_items(state_constraints: dict) -> list[str]:
    if not isinstance(state_constraints, dict):
        return []

    protagonist_items = state_constraints.get("protagonist_items")
    if protagonist_items is not None:
        return _normalize_item_list(protagonist_items)
    return _normalize_item_list(state_constraints.get("items_acquired", []))


class ConstraintCompiler:
    """
    [V60.11] 제약 조건 컴파일러

    이전 Arc들에서 제약 조건을 추출하고 구조화
    """

    def __init__(self, genre: str = "") -> None:
        self._item_suffixes = get_item_suffixes(genre)
        _suffix_group = "|".join(sorted((re.escape(s) for s in self._item_suffixes), key=len, reverse=True))
        _suffix_group = _suffix_group or r"아이템"

        # 아이템 획득 패턴 (장르 동적 접미사)
        self.acquire_patterns = [
            rf"([가-힣A-Za-z0-9]{{0,30}}(?:{_suffix_group}))",
        ]

        # 수여물 패턴
        self.grant_patterns = [
            r"([가-힣A-Za-z0-9]{2,30}패)",
            r"([가-힣A-Za-z0-9]{2,30}권)",
            r"([가-힣A-Za-z0-9]{2,30}인장)",
            r"([가-힣A-Za-z0-9]{2,30}자격)",
            r"([가-힣A-Za-z0-9]{2,30}직위)",
        ]

    def compile(
        self,
        prev_arcs: list[dict],
        state_extractor_result: dict = None,
        resolved_plots: list[dict] = None,  # [V62.7]
    ) -> str:
        """
        제약 조건 컴파일

        Args:
            prev_arcs: 이전 Arc 리스트
            state_extractor_result: StateExtractor 결과 (있으면 활용)
            resolved_plots: [V62.7] 완결된 플롯 리스트

        Returns:
            구조화된 제약 체크리스트 문자열
        """
        if not prev_arcs:
            return self._generate_initial_constraints()

        # 1. 모든 획득 아이템 수집
        all_items = self._collect_all_items(prev_arcs)

        # 2. 모든 수여물 수집
        all_grants = self._collect_all_grants(prev_arcs)

        # 3. 현재 상태 추출
        current_state = self._extract_current_state(prev_arcs[-1], state_extractor_result)

        # 4. 제약 체크리스트 생성
        return self._generate_constraint_checklist(
            all_items=all_items,
            all_grants=all_grants,
            current_state=current_state,
            arc_count=len(prev_arcs),
            resolved_plots=resolved_plots,
        )

    # [V62.3] 윈도잉: regex 스캔은 최근 N개만 (구조화 필드는 전체)
    REGEX_WINDOW = 3

    def _collect_all_items(self, prev_arcs: list[dict]) -> dict[str, int]:
        """모든 획득 아이템과 획득 시점 수집
        [V62.3] 구조화 필드(protagonist_items/items_acquired, inventory)는 전체 Arc 스캔 (O(n), 가벼움)
                regex 스캔(tactical_doc)은 최근 REGEX_WINDOW개만 (비용 절감)
        """
        items = {}  # {아이템명: 획득 Arc 번호}
        regex_start = max(0, len(prev_arcs) - self.REGEX_WINDOW)

        for idx, arc in enumerate(prev_arcs):
            arc_no = arc.get("arc_no", 0)

            # state_constraints.protagonist_items / items_acquired (구조화 → 전체 스캔)
            acquired = _resolve_protagonist_items(arc.get("state_constraints") or {})
            for item in acquired:
                if item and len(item) >= 2:
                    items[item] = arc_no

            # joint_docs.physical_inventory (구조화 → 전체 스캔)
            inventory = _normalize_item_list((arc.get("joint_docs") or {}).get("physical_inventory"))
            for item in inventory:
                if item and len(item) >= 2 and item not in items:
                    items[item] = arc_no

            # tactical_doc regex (비싼 연산 → 최근 REGEX_WINDOW개만)
            if idx >= regex_start:
                tactical = arc.get("tactical_doc", "")
                if isinstance(tactical, dict):  # [V70] dict 타입 방어
                    tactical = json.dumps(tactical, ensure_ascii=False)
                tactical = str(tactical) if tactical else ""
                for pattern in self.acquire_patterns:
                    matches = re.findall(pattern, tactical)
                    for m in matches:
                        item = m.strip() if isinstance(m, str) else m[0].strip() if m else None
                        if item and 2 <= len(item) <= 20 and item not in items:
                            if re.search(rf"{re.escape(item)}[를을]?\s*(?:획득|얻|받|손에)", tactical):
                                items[item] = arc_no

        # [TF-59] 소비된 아이템은 금지 목록에서 제외 (재획득 허용)
        consumed = set()
        for arc in prev_arcs:
            sc = arc.get("state_constraints") or {}
            for item in sc.get("items_consumed") or []:
                item_str = str(item) if isinstance(item, dict) else item
                if item_str:
                    consumed.add(item_str)
        for c in consumed:
            items.pop(c, None)

        return items

    def _collect_all_grants(self, prev_arcs: list[dict]) -> dict[str, tuple[int, str]]:
        """모든 수여물과 수여 시점/수여자 수집
        [V62.3] 구조화 필드는 전체, regex는 최근 REGEX_WINDOW개만
        """
        grants = {}  # {수여물명: (Arc 번호, 수여자)}
        regex_start = max(0, len(prev_arcs) - self.REGEX_WINDOW)

        for idx, arc in enumerate(prev_arcs):
            arc_no = arc.get("arc_no", 0)

            # state_constraints.grants_received (구조화 → 전체)
            received = (arc.get("state_constraints") or {}).get("grants_received", [])  # [V70] None 방어
            if isinstance(received, list):
                for grant in received:
                    grant = str(grant) if isinstance(grant, dict) else grant
                    if grant and len(grant) >= 2:
                        grants[grant] = (arc_no, "알 수 없음")

            # tactical_doc regex (최근 REGEX_WINDOW개만)
            if idx >= regex_start:
                tactical = arc.get("tactical_doc", "")
                if isinstance(tactical, dict):  # [V70] dict 타입 방어 (_collect_all_items과 동일)
                    tactical = json.dumps(tactical, ensure_ascii=False)
                tactical = str(tactical) if tactical else ""
                for pattern in self.grant_patterns:
                    matches = re.findall(pattern, tactical)
                    for m in matches:
                        grant = m.strip() if isinstance(m, str) else m[0].strip() if m else None
                        if grant and 2 <= len(grant) <= 20 and grant not in grants:
                            if re.search(rf"{re.escape(grant)}[를을]?\s*(?:하사|수여|받|얻)", tactical):
                                grantor_match = re.search(
                                    rf"([가-힣]{{2,10}})[이가으로부터]?\s*{re.escape(grant)}", tactical
                                )
                                grantor = grantor_match.group(1) if grantor_match else "알 수 없음"
                                grants[grant] = (arc_no, grantor)

        return grants

    def _extract_current_state(self, last_arc: dict, state_extractor_result: dict = None) -> dict:
        """현재 상태 추출"""
        if state_extractor_result:
            protagonist = state_extractor_result.get("protagonist_state", {})
            inventory = state_extractor_result.get("inventory", {})
            if not isinstance(protagonist, dict):
                protagonist = {}
            if not isinstance(inventory, dict):
                inventory = {}
            _loc = protagonist.get("location", {})
            _energy = protagonist.get("internal_energy", {})

            return {
                "location": (
                    _loc.get("current", "알 수 없음") if isinstance(_loc, dict) else str(_loc) if _loc else "알 수 없음"
                ),
                "injuries": protagonist.get("injuries", []),
                "internal_energy": (
                    _energy.get("current_percent", 100)
                    if isinstance(_energy, dict)
                    else int(_energy)
                    if isinstance(_energy, int | float)
                    else 100
                ),
                "equipment": inventory.get("current_items", []),
                "world_state": state_extractor_result.get("next_arc_constraints", {}).get("must_start_with", ""),
                "capital": protagonist.get("capital"),
                "total_assets": protagonist.get("total_assets"),
                "portfolio_position": protagonist.get("portfolio_position"),
            }

        # [V60.13 FIX] 폴백: arc_end_state 우선 사용
        joint = last_arc.get("joint_docs", {})
        state_constraints = last_arc.get("state_constraints", {})
        arc_end_state = state_constraints.get("arc_end_state", {})

        equipment = []
        if isinstance(arc_end_state, dict) and "equipment" in arc_end_state:
            equipment = _normalize_item_list(arc_end_state.get("equipment"))
        elif isinstance(joint, dict):
            equipment = _normalize_item_list(joint.get("physical_inventory"))

        # [V62.2] 내공 + 부상: 아크 간 자연 회복 → 항상 100% / 없음
        internal_energy = 100
        injuries = ""

        return {
            "location": (
                arc_end_state.get("location")
                if isinstance(arc_end_state, dict) and arc_end_state.get("location")
                else joint.get("final_location", "알 수 없음")
            ),
            "injuries": [injuries] if injuries and injuries != "없음" else [],
            "internal_energy": internal_energy,
            "equipment": equipment,
            "world_state": joint.get("world_joint", ""),
            "capital": arc_end_state.get("capital"),
            "total_assets": arc_end_state.get("total_assets"),
            "portfolio_position": arc_end_state.get("portfolio_position"),
        }

    def _generate_constraint_checklist(
        self,
        all_items: dict[str, int],
        all_grants: dict[str, tuple[int, str]],
        current_state: dict,
        arc_count: int,
        resolved_plots: list[dict] = None,  # [V62.7]
    ) -> str:
        """구조화된 제약 체크리스트 생성"""
        lines = [
            "",
            "█" * 72,
            "█" + " " * 70 + "█",
            "█" + " [V60.28] 절대 금지 - 위반 시 즉시 REJECT ".center(70) + "█",
            "█" + " " * 70 + "█",
            "█" * 72,
            "",
        ]

        # ═══════════════════════════════════════════════════════════════
        # SECTION 0: CRITICAL WARNING - 가장 먼저, 가장 크게
        # ═══════════════════════════════════════════════════════════════
        if all_items:
            lines.append("🚨🚨🚨 다음 아이템은 절대 획득하지 마세요! 🚨🚨🚨")
            lines.append("=" * 72)
            for item, arc_no in sorted(all_items.items(), key=lambda x: x[1]):
                lines.append(f"  ❌ '{item}' - Arc {arc_no}에서 이미 획득함 → 다시 획득 금지!")
            lines.append("=" * 72)
            lines.append("")
            lines.append("⚠️ protagonist_items(legacy alias: items_acquired)에 위 아이템이 포함되면 즉시 REJECT됩니다!")
            lines.append("")

        # ═══════════════════════════════════════════════════════════════
        # SECTION 1: MUST NOT DO (금지 사항) - 상세
        # ═══════════════════════════════════════════════════════════════
        lines.append("┌" + "─" * 70 + "┐")
        lines.append("│ 🚫 MUST NOT DO (절대 금지 - 위반 시 즉시 REJECT)".ljust(71) + "│")
        lines.append("├" + "─" * 70 + "┤")

        # 중복 획득 금지 아이템
        if all_items:
            lines.append("│ [아이템 획득 금지 - 이미 보유 중]".ljust(71) + "│")
            for item, arc_no in sorted(all_items.items(), key=lambda x: x[1]):
                lines.append(f"│   ❌ {item} (Arc {arc_no}에서 획득)".ljust(71) + "│")
        else:
            lines.append("│   (획득 금지 아이템 없음)".ljust(71) + "│")

        lines.append("│".ljust(72) + "│")

        # 중복 수여 금지
        if all_grants:
            lines.append("│ [수여물 재수여 금지 - 이미 수여받음]".ljust(71) + "│")
            for grant, (arc_no, grantor) in sorted(all_grants.items(), key=lambda x: x[1][0]):
                lines.append(f"│   ❌ {grant} (Arc {arc_no}: {grantor}이(가) 수여)".ljust(71) + "│")
        else:
            lines.append("│   (수여물 금지 목록 없음)".ljust(71) + "│")

        # [V62.7] 완결된 플롯 재생성 금지
        if resolved_plots:
            lines.append("│".ljust(72) + "│")
            lines.append("│ [완결된 플롯 재생성 금지 - 동일/유사 갈등 시 REJECT]".ljust(71) + "│")
            for rp in resolved_plots[-10:]:
                plot_name = str(rp.get("plot", "?"))[:35]
                resolution = str(rp.get("resolution", ""))[:20]
                arc = rp.get("arc_no", "?")
                lines.append(f"│   ❌ {plot_name} ({resolution}, Arc {arc})".ljust(71) + "│")

        lines.append("└" + "─" * 70 + "┘")
        lines.append("")

        # ═══════════════════════════════════════════════════════════════
        # SECTION 2: INHERITED STATE (계승 상태) - 시작점 고정
        # ═══════════════════════════════════════════════════════════════
        lines.append("┌" + "─" * 70 + "┐")
        lines.append("│ 📋 INHERITED STATE (반드시 계승할 상태 - Arc 시작점)".ljust(71) + "│")
        lines.append("├" + "─" * 70 + "┤")

        location = current_state.get("location", "알 수 없음")
        lines.append(f"│ 🗺️ 시작 위치: {location[:50]}".ljust(71) + "│")

        equipment = current_state.get("equipment", [])
        if equipment:
            equip_str = ", ".join(str(e) for e in equipment[:5])
            if len(equipment) > 5:
                equip_str += f" 외 {len(equipment) - 5}개"
            lines.append(f"│ 📦 소지품: {equip_str[:55]}".ljust(71) + "│")
        else:
            lines.append("│ 📦 소지품: (목록 없음)".ljust(71) + "│")

        injuries = current_state.get("injuries", [])
        if injuries and injuries != ["없음"]:
            injury_str = ", ".join(str(i)[:20] for i in injuries[:3])
            lines.append(f"│ 💔 부상 상태: {injury_str}".ljust(71) + "│")
        else:
            lines.append("│ 💔 부상 상태: 없음".ljust(71) + "│")

        energy_raw = current_state.get("internal_energy", 100)
        # [V60.75] 문자열/숫자 모두 처리
        try:
            if isinstance(energy_raw, str):
                energy = int("".join(filter(str.isdigit, energy_raw)) or "100")
            else:
                energy = int(energy_raw)
        except (ValueError, TypeError):
            energy = 100
        lines.append(f"│ ⚡ 내공: {energy}%".ljust(71) + "│")

        lines.append("└" + "─" * 70 + "┘")
        lines.append("")

        # ═══════════════════════════════════════════════════════════════
        # SECTION 3: MUST DO (필수 사항)
        # ═══════════════════════════════════════════════════════════════
        lines.append("┌" + "─" * 70 + "┐")
        lines.append("│ ✅ MUST DO (필수 사항)".ljust(71) + "│")
        lines.append("├" + "─" * 70 + "┤")

        lines.append(f"│ □ Arc 시작 위치 = '{location[:40]}' 에서 시작".ljust(71) + "│")

        if equipment:
            lines.append("│ □ 소지품 상태로 시작 (새 획득 없이 기존 아이템 소지)".ljust(71) + "│")

        if injuries and injuries != ["없음"]:
            lines.append("│ □ 부상 상태 계승 (회복 장면 없이 멀쩡하면 안 됨)".ljust(71) + "│")

        if energy < 70:
            lines.append(f"│ □ 내공 {energy}% 상태 유지 (갑자기 100% 불가)".ljust(71) + "│")

        lines.append("│ □ tactical_doc 최소 3000자 이상".ljust(71) + "│")
        lines.append("│ □ 화별 구분 명확히 (제 N화 형식)".ljust(71) + "│")

        lines.append("└" + "─" * 70 + "┘")
        lines.append("")

        # ═══════════════════════════════════════════════════════════════
        # SECTION 4: VERIFICATION CHECKLIST
        # ═══════════════════════════════════════════════════════════════
        lines.append("┌" + "─" * 70 + "┐")
        lines.append("│ 🔍 SELF-CHECK (생성 후 자체 검증)".ljust(71) + "│")
        lines.append("├" + "─" * 70 + "┤")
        lines.append("│ □ protagonist_items(legacy alias: items_acquired)에 금지 목록 아이템 없는가?".ljust(71) + "│")
        lines.append("│ □ arc_start_state.location = 이전 Arc 종료 위치인가?".ljust(71) + "│")
        lines.append("│ □ arc_start_state.equipment = 이전 Arc 종료 소지품인가?".ljust(71) + "│")
        lines.append("│ □ tactical_doc에 '다시 획득' 문구 없는가?".ljust(71) + "│")
        lines.append("│ □ 수여받은 것을 재수여받는 장면 없는가?".ljust(71) + "│")
        lines.append("└" + "─" * 70 + "┘")
        lines.append("")

        return "\n".join(lines)

    def _generate_initial_constraints(self) -> str:
        """첫 Arc용 기본 제약"""
        return """
╔══════════════════════════════════════════════════════════════════════╗
║       [V60.11 CONSTRAINT CHECKLIST - 첫 Arc 설계]                    ║
╚══════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────┐
│ ✅ MUST DO (필수 사항)                                               │
├──────────────────────────────────────────────────────────────────────┤
│ □ 서사 시작점에서 출발                                               │
│ □ 주인공 초기 상태 명확히 설정                                        │
│ □ tactical_doc 최소 3000자 이상                                      │
│ □ 화별 구분 명확히 (제 N화 형식)                                     │
│ □ 첫 Arc답게 세계관/인물 소개 포함                                   │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 🚫 MUST NOT DO (금지 사항)                                           │
├──────────────────────────────────────────────────────────────────────┤
│ □ 급격한 파워업 금지 (첫 Arc에서 절정 경지 도달 등)                   │
│ □ 핵심 아이템 조기 획득 금지 (전체 서사 고려)                         │
│ □ 설명 위주 금지 (갈등과 사건 중심)                                   │
└──────────────────────────────────────────────────────────────────────┘
"""


def create_constraint_compiler(genre: str = "") -> ConstraintCompiler:
    """ConstraintCompiler 생성 헬퍼"""
    return ConstraintCompiler(genre=genre)
