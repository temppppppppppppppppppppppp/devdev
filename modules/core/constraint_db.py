"""
[V49.4] Pre-Generation Constraint DB
생성 전 제약 조건을 관리하여 LLM 재시도율을 낮추는 시스템

역할:
1. 이미 획득한 아이템 추적 (중복 획득 방지)
2. 현재 소지품 상태 관리
3. 수여받은 권한/패 추적
4. LLM 프롬프트에 주입할 제약 블록 생성

사용:
    constraint_db = ConstraintDB(project_context)
    constraint_block = constraint_db.generate_constraint_block(arc_no=2)
    # → 프롬프트에 constraint_block 주입
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

# [V49.4] Semantic Item Registry 통합
try:
    from modules.core.semantic_item_registry import SemanticItemRegistry, create_item_registry

    SEMANTIC_REGISTRY_ENABLED = True
except ImportError:
    SEMANTIC_REGISTRY_ENABLED = False
    SemanticItemRegistry = None


@dataclass
class ArcState:
    """Arc 종료 시점의 상태 스냅샷"""

    arc_no: int
    location: str = ""
    inventory: list[str] = field(default_factory=list)
    injuries: str = "정상"
    internal_energy: int = 100
    grants: list[str] = field(default_factory=list)  # 수여받은 권한/패
    acquired_items: list[str] = field(default_factory=list)  # 이 Arc에서 새로 획득
    consumed_items: list[str] = field(default_factory=list)  # 이 Arc에서 소모


class ConstraintDB:
    """
    [V49.4] Pre-Generation Constraint Database

    Arc 설계 전에 LLM에게 명확한 제약 조건을 주입하여
    중복 획득, 상태 불연속 등의 오류를 사전에 방지합니다.
    """

    def __init__(self, project_context=None) -> None:
        """
        Args:
            project_context: ProjectContext 객체 (DB 접근용)
        """
        self.context = project_context
        self.arc_states: dict[int, ArcState] = {}

        # [V49.4] Semantic Item Registry 초기화
        self.item_registry = None
        if SEMANTIC_REGISTRY_ENABLED:
            self.item_registry = create_item_registry()

        self._load_from_db()

    def _load_from_db(self) -> None:
        """DB에서 기존 Arc 데이터 로드"""
        if not self.context or not hasattr(self.context, "db"):
            return

        try:
            arcs_data = self.context.db.load_anchor("arcs")
            if not arcs_data:
                return

            # arcs_data가 리스트인 경우
            if isinstance(arcs_data, list):
                for arc in arcs_data:
                    if isinstance(arc, dict):
                        self._parse_arc_state(arc)
            # arcs_data가 딕셔너리인 경우 (arc_1, arc_2, ... 키)
            elif isinstance(arcs_data, dict):
                for key, arc in arcs_data.items():
                    if isinstance(arc, dict):
                        self._parse_arc_state(arc)

        except Exception as e:
            logging.warning(f"⚠️ [ConstraintDB] DB 로드 실패: {e}")

    def _parse_arc_state(self, arc_data: dict):
        """Arc 데이터에서 상태 추출"""
        arc_no = arc_data.get("arc_no")
        if not arc_no:
            return
        try:
            arc_no = int(arc_no)
        except (ValueError, TypeError):
            logging.warning(f"[ConstraintDB] arc_no 파싱 실패: {arc_no!r} -> 스킵")
            return

        # state_constraints에서 상태 추출
        state_constraints = arc_data.get("state_constraints") or {}  # [V70] null → {} 방어
        if not isinstance(state_constraints, dict):
            state_constraints = {}  # LLM이 문자열 반환 시 방어
        arc_end_state = state_constraints.get("arc_end_state") or {}  # [V70]
        if not isinstance(arc_end_state, dict):
            arc_end_state = {}

        # joint_docs에서 추가 정보 추출
        joint_docs = arc_data.get("joint_docs", {})
        if not isinstance(joint_docs, dict):
            joint_docs = {}

        # 소지품 추출 (여러 소스에서)
        inventory = []
        tactical_doc_for_filter = arc_data.get("tactical_doc", "")

        # 1. arc_end_state.equipment
        equipment = arc_end_state.get("equipment", [])
        if isinstance(equipment, list):
            inventory.extend(equipment)
        elif isinstance(equipment, str):
            inventory.append(equipment)

        # 2. joint_docs.physical_inventory
        phys_inv = joint_docs.get("physical_inventory", [])
        if isinstance(phys_inv, list):
            for item in phys_inv:
                if item and item not in inventory:
                    inventory.append(item)
        elif isinstance(phys_inv, str) and phys_inv:
            if phys_inv not in inventory:
                inventory.append(phys_inv)

        # [V49.6] 분배된 아이템 필터링
        inventory = self._filter_distributed_items(inventory, tactical_doc_for_filter)

        # [V49.6] protagonist_items 우선, items_acquired 하위 호환
        items_acquired = state_constraints.get("protagonist_items", [])
        if not items_acquired:
            items_acquired = state_constraints.get("items_acquired", [])
        if not isinstance(items_acquired, list):
            items_acquired = []

        # [V49.6] 분배된 아이템 필터링 적용 (이중 안전망)
        tactical_doc = arc_data.get("tactical_doc", "")
        items_acquired = self._filter_distributed_items(items_acquired, tactical_doc)

        # 소모 아이템 추출
        items_consumed = state_constraints.get("items_consumed", [])
        if not isinstance(items_consumed, list):
            items_consumed = []

        # 수여물 추출 (tactical_doc에서 패턴 매칭)
        grants = self._extract_grants_from_tactical(tactical_doc)

        # 내공 파싱
        internal_energy = self._parse_internal_energy(arc_end_state.get("internal_energy", 100))

        state = ArcState(
            arc_no=arc_no,
            location=joint_docs.get("final_location", arc_end_state.get("location", "")),
            inventory=inventory,
            injuries=arc_end_state.get("injuries", "정상"),
            internal_energy=internal_energy,
            grants=grants,
            acquired_items=items_acquired,
            consumed_items=items_consumed,
        )

        self.arc_states[arc_no] = state

        # [V49.4] Semantic Registry에 아이템 등록
        if self.item_registry:
            for item in items_acquired:
                if item:
                    self.item_registry.register_item(item, arc_no)
            for item in items_consumed:
                if item:
                    self.item_registry.mark_consumed(item, arc_no)

    def _extract_grants_from_tactical(self, tactical_doc: str) -> list[str]:
        """tactical_doc에서 수여물 추출"""
        if not tactical_doc:
            return []

        grants = []
        grant_patterns = [
            r"([가-힣]+패)[를을]?\s*(?:하사|수여|받|얻)",
            r"([가-힣]+권)[를을]?\s*(?:위임|부여|받|얻|하사)",
            r"([가-힣]+직|[가-힣]+장)[에으로]?\s*(?:임명|취임|올|받)",
            r"((?:[가-힣]+\s*)?인장)[를을]?\s*(?:받|하사|수여)",
        ]

        for pattern in grant_patterns:
            matches = re.findall(pattern, tactical_doc)
            for match in matches:
                grant = match if isinstance(match, str) else match[0] if match else None
                if grant and grant not in grants:
                    grants.append(grant)

        return grants

    def _parse_internal_energy(self, value) -> int:
        """내공 수치 파싱"""
        if isinstance(value, int):
            return max(0, min(100, value))
        if isinstance(value, float):
            return max(0, min(100, int(value)))
        if isinstance(value, str):
            # 숫자 추출 시도
            clean = value.replace("%", "").strip()
            if clean.isdigit():
                return max(0, min(100, int(clean)))
            match = re.search(r"(\d+)", clean)
            if match:
                return max(0, min(100, int(match.group(1))))
        return 50  # 기본값

    def _is_distributed_item(self, item: str, context: str) -> bool:
        """
        [V49.6] 아이템이 타인에게 분배/지급된 것인지 판단

        Args:
            item: 아이템 이름
            context: 해당 아이템이 언급된 맥락 (tactical_doc)

        Returns:
            True if the item was distributed to others (not protagonist's personal acquisition)
        """
        if not item or not context:
            return False

        # 아이템 주변 맥락 추출 (아이템 언급 전후 100자)
        item_pos = context.find(item)
        if item_pos == -1:
            return False

        start = max(0, item_pos - 100)
        end = min(len(context), item_pos + len(item) + 100)
        local_context = context[start:end]

        # 분배/지급 키워드 확인
        distribution_keywords = [
            "지급",
            "분배",
            "나눠",
            "배분",
            "내려 보내",
            "하사하",
            "수레",
            "마차",
            "도착",
            "배달",
            "전달",
            "병사들",
            "무사들",
            "사병들",
            "부하들",
            "병사에게",
            "무사에게",
            "사병에게",
            "부하에게",
            "막사 앞",
            "연무장에",
            "도착한다",
            "실린",
        ]

        for keyword in distribution_keywords:
            if keyword in local_context:
                return True

        return False

    def _filter_distributed_items(self, items: list[str], context: str) -> list[str]:
        """
        [V49.6] 분배된 아이템을 필터링

        Args:
            items: 아이템 목록
            context: 전체 맥락 텍스트 (tactical_doc)

        Returns:
            분배된 아이템이 제외된 목록
        """
        if not items or not context:
            return items

        filtered = []
        for item in items:
            if item and not self._is_distributed_item(item, context):
                filtered.append(item)

        return filtered

    def get_all_acquired_items(self, before_arc: int = None) -> dict[int, list[str]]:
        """
        전체 획득 아이템 목록 조회

        Args:
            before_arc: 이 Arc 이전까지만 조회 (None이면 전체)

        Returns:
            {arc_no: [아이템 목록]} 딕셔너리
        """
        result = {}
        for arc_no, state in sorted(self.arc_states.items()):
            if before_arc and arc_no >= before_arc:
                break
            if state.acquired_items:
                result[arc_no] = state.acquired_items.copy()
            # inventory에서도 추가 (acquired_items에 없는 것)
            for item in state.inventory:
                if item and arc_no not in result:
                    result[arc_no] = []
                if item and item not in result.get(arc_no, []):
                    result.setdefault(arc_no, []).append(item)
        return result

    def get_all_grants(self, before_arc: int = None) -> dict[int, list[str]]:
        """
        전체 수여물 목록 조회

        Args:
            before_arc: 이 Arc 이전까지만 조회

        Returns:
            {arc_no: [수여물 목록]} 딕셔너리
        """
        result = {}
        for arc_no, state in sorted(self.arc_states.items()):
            if before_arc and arc_no >= before_arc:
                break
            if state.grants:
                result[arc_no] = state.grants.copy()
        return result

    def get_current_inventory(self, at_arc: int) -> list[str]:
        """
        특정 Arc 시점의 소지품 목록

        Args:
            at_arc: 해당 Arc 종료 시점 기준

        Returns:
            현재 소지품 리스트
        """
        if at_arc in self.arc_states:
            return self.arc_states[at_arc].inventory.copy()

        # 해당 Arc가 없으면 직전 Arc의 inventory 반환
        prev_arcs = [n for n in self.arc_states.keys() if n < at_arc]
        if prev_arcs:
            latest = max(prev_arcs)
            return self.arc_states[latest].inventory.copy()

        return []

    def get_current_state(self, at_arc: int) -> ArcState | None:
        """
        특정 Arc의 종료 상태 조회

        Args:
            at_arc: Arc 번호

        Returns:
            ArcState 또는 None
        """
        return self.arc_states.get(at_arc)

    def get_forbidden_items(self, for_arc: int) -> list[str]:
        """
        특정 Arc에서 획득 금지된 아이템 목록
        (이미 이전 Arc에서 획득한 아이템들)

        Args:
            for_arc: 설계할 Arc 번호

        Returns:
            획득 금지 아이템 리스트
        """
        forbidden = []
        all_acquired = self.get_all_acquired_items(before_arc=for_arc)

        for arc_no, items in all_acquired.items():
            for item in items:
                if item and item not in forbidden:
                    forbidden.append(item)

        return forbidden

    def generate_constraint_block(self, for_arc: int) -> str:
        """
        LLM 프롬프트에 주입할 제약 블록 생성

        Args:
            for_arc: 설계할 Arc 번호

        Returns:
            제약 조건 텍스트 블록
        """
        # 이전 Arc가 없으면 빈 블록
        if for_arc <= 1 or not self.arc_states:
            return ""

        # 직전 Arc 상태
        prev_arc_no = for_arc - 1
        prev_state = self.get_current_state(prev_arc_no)

        # 획득 금지 아이템
        forbidden = self.get_forbidden_items(for_arc)

        # 전체 수여물
        all_grants = self.get_all_grants(before_arc=for_arc)
        grants_list = []
        for arc_no, grants in all_grants.items():
            for grant in grants:
                grants_list.append(f"Arc{arc_no}: {grant}")

        # 현재 소지품
        current_inventory = self.get_current_inventory(prev_arc_no)

        # 제약 블록 생성 (ASCII 호환)
        lines = [
            "",
            "+================================================================+",
            "|  [!] PRE-GENERATION CONSTRAINTS (위반 시 즉시 REJECT)          |",
            "+================================================================+",
        ]

        # 1. 획득 금지 목록
        lines.append("|  [X] 획득 금지 - 이미 보유 중인 아이템:                        |")
        if forbidden:
            for item in forbidden[:10]:  # 최대 10개
                lines.append(f"|      - {item[:52]:<52} |")
            if len(forbidden) > 10:
                lines.append(f"|      ... 외 {len(forbidden) - 10}개                                        |")
        else:
            lines.append("|      (없음)                                                  |")

        lines.append("+----------------------------------------------------------------+")

        # 2. 현재 소지품
        lines.append("|  [O] 현재 소지품 - Arc 시작 시 보유 상태로 시작:               |")
        if current_inventory:
            for item in current_inventory[:8]:
                lines.append(f"|      - {item[:52]:<52} |")
            if len(current_inventory) > 8:
                lines.append(f"|      ... 외 {len(current_inventory) - 8}개                                        |")
        else:
            lines.append("|      (없음)                                                  |")

        lines.append("+----------------------------------------------------------------+")

        # 3. 이미 수여받은 권한
        lines.append("|  [*] 이미 수여받은 권한/패 - 재수여 금지:                      |")
        if grants_list:
            for grant in grants_list[:5]:
                lines.append(f"|      - {grant[:52]:<52} |")
        else:
            lines.append("|      (없음)                                                  |")

        lines.append("+----------------------------------------------------------------+")

        # 4. 직전 Arc 상태
        if prev_state:
            lines.append("|  [>] 직전 Arc 종료 상태 - 이 상태에서 시작해야 함:            |")
            lines.append(f"|      위치: {prev_state.location[:49]:<49} |")
            lines.append(f"|      부상: {prev_state.injuries:<49} |")
            lines.append(f"|      내공: {prev_state.internal_energy}%{' ':<47} |")

        lines.append("+================================================================+")
        lines.append("")

        return "\n".join(lines)

    def generate_compact_constraint(self, for_arc: int) -> str:
        """
        간결한 제약 블록 생성 (토큰 절약용)

        Args:
            for_arc: 설계할 Arc 번호

        Returns:
            간결한 제약 조건 텍스트
        """
        if for_arc <= 1 or not self.arc_states:
            return ""

        forbidden = self.get_forbidden_items(for_arc)
        current_inv = self.get_current_inventory(for_arc - 1)
        grants = []
        for arc_no, g_list in self.get_all_grants(before_arc=for_arc).items():
            grants.extend(g_list)

        parts = []

        if forbidden:
            parts.append(f"[획득금지] {', '.join(forbidden[:5])}")

        if current_inv:
            parts.append(f"[현재소지] {', '.join(current_inv[:5])}")

        if grants:
            parts.append(f"[기수여] {', '.join(grants[:3])}")

        if not parts:
            return ""

        return "🚨 " + " | ".join(parts)

    def update_arc_state(self, arc_data: dict):
        """
        Arc 설계 완료 후 상태 업데이트

        Args:
            arc_data: 완료된 Arc 데이터
        """
        self._parse_arc_state(arc_data)

    def validate_arc_design(self, arc_data: dict) -> dict[str, Any]:
        """
        Arc 설계의 제약 조건 준수 여부 사전 검증

        Args:
            arc_data: 검증할 Arc 데이터

        Returns:
            {
                "valid": bool,
                "violations": [위반 목록],
                "warnings": [경고 목록]
            }
        """
        try:
            arc_no = int(arc_data.get("arc_no", 0))
        except (ValueError, TypeError):
            return {"valid": True, "violations": [], "warnings": ["arc_no 파싱 실패"]}
        violations = []
        warnings = []

        # 획득 금지 아이템 검사
        forbidden = set(self.get_forbidden_items(arc_no))

        state_constraints = arc_data.get("state_constraints") or {}  # [V70] null → {} 방어
        if not isinstance(state_constraints, dict):
            state_constraints = {}  # LLM이 문자열 반환 시 방어
        new_acquired = state_constraints.get("items_acquired") or []  # [V70]

        # [V49.4] Semantic Registry를 사용한 고급 중복 감지
        if self.item_registry and new_acquired:
            registry_result = self.item_registry.validate_arc_items(arc_no, new_acquired)
            for v in registry_result.get("violations", []):
                violations.append(f"[{v['severity']}] {v['message']}")
            for w in registry_result.get("warnings", []):
                warnings.append(f"[{w['severity']}] {w['message']}")
        else:
            # Fallback: 기존 검사 로직
            for item in new_acquired:
                # 정확한 매칭
                if item in forbidden:
                    violations.append(f"[CRITICAL] 중복 획득: '{item}'은 이미 이전 Arc에서 획득함")
                # 부분 매칭 (경고)
                elif any(item in f or f in item for f in forbidden):
                    warnings.append(
                        f"[WARNING] 유사 아이템 존재: '{item}' (기존: {[f for f in forbidden if item in f or f in item]})"
                    )

        # tactical_doc에서 획득 패턴 검사
        tactical = arc_data.get("tactical_doc", "")
        for f_item in forbidden:
            # "X를 획득" 패턴 검사
            if re.search(rf"{re.escape(f_item)}[을를]?\s*(?:획득|얻|손에)", tactical):
                violations.append(f"[CRITICAL] tactical_doc에서 '{f_item}' 재획득 시도 감지")

        return {"valid": len(violations) == 0, "violations": violations, "warnings": warnings}


def create_constraint_db(project_context) -> ConstraintDB:
    """ConstraintDB 인스턴스 생성 헬퍼"""
    return ConstraintDB(project_context)
