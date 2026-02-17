"""
[V49.4] Semantic Item Registry

아이템 이름의 의미적 유사성을 추적하여 중복 획득을 방지하는 시스템

기능:
1. 아이템 등록 및 별칭(alias) 관리
2. 유사도 기반 중복 감지 (예: "대도" vs "녹슨 대도" vs "백근 대도")
3. 정규화된 아이템 이름 매핑
4. Arc별 획득 이력 추적

사용 예:
    registry = SemanticItemRegistry()
    registry.register_item("대도", arc_no=1, aliases=["녹슨 대도", "백근 대도"])

    # 중복 체크
    result = registry.check_duplicate("녹슨 백근 대도", arc_no=3)
    # result: {"is_duplicate": True, "original": "대도", "acquired_in": 1}
"""

import re
import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ItemEvent:
    """[V49.7] 아이템 이벤트 기록"""

    arc: int
    episode: int
    event_type: str  # created, acquired, transferred, used, lost, destroyed
    actor: str  # 행위자
    target: str = ""  # 대상 (이전 대상)
    description: str = ""
    timestamp: str = ""  # 서사 내 시점


@dataclass
class ItemEntry:
    """아이템 엔트리"""

    canonical_name: str  # 정규화된 이름
    aliases: set[str] = field(default_factory=set)
    acquired_arc: int = 0
    category: str = "일반"  # 무기, 복장, 문서, 약물, 기타
    consumed_arc: int = 0  # 소모된 Arc (0이면 미소모)
    # [V49.7] 생애주기 추적 필드
    current_owner: str = ""  # 현재 소유자
    current_state: str = "소지중"  # 소지중, 착용중, 보관중, 분실, 파괴
    event_history: list[Any] = field(default_factory=list)  # ItemEvent 리스트


class SemanticItemRegistry:
    """
    [V49.4] 의미적 아이템 레지스트리

    아이템 이름의 변형(별칭, 수식어)을 추적하여
    동일 아이템의 중복 획득을 방지합니다.
    """

    # 무시할 수식어 패턴
    IGNORABLE_MODIFIERS = [
        # 상태/품질
        r"녹슨",
        r"낡은",
        r"부러진",
        r"깨진",
        r"오래된",
        r"새로운",
        r"빛나는",
        r"날카로운",
        r"무딘",
        r"예리한",
        r"묵직한",
        r"가벼운",
        # 크기
        r"작은",
        r"큰",
        r"거대한",
        r"소형",
        r"대형",
        r"중형",
        # 재질
        r"철제",
        r"강철",
        r"청동",
        r"황금",
        r"은제",
        r"목제",
        r"가죽",
        # 색상
        r"흑색",
        r"백색",
        r"적색",
        r"청색",
        r"금색",
        r"은색",
        # 무게/양
        r"백근",
        r"천근",
        r"십근",
        r"오십근",
        # 등급
        r"상급",
        r"중급",
        r"하급",
        r"최상급",
        r"일품",
        r"이품",
        r"삼품",
    ]

    # 아이템 카테고리별 핵심어
    CATEGORY_KEYWORDS = {
        "무기": ["검", "도", "창", "봉", "편", "곤", "월", "척", "권", "장", "부"],
        "복장": ["의", "포", "갑", "갑옷", "복", "관", "모", "신", "화", "대"],
        "문서": ["서", "첩", "권", "문", "책", "기", "보", "전", "록"],
        "약물": ["단", "환", "약", "주", "고"],
        "패/인장": ["패", "인", "장", "령", "표", "첩"],
    }

    def __init__(self) -> None:
        self.items: dict[str, ItemEntry] = {}
        self._alias_map: dict[str, str] = {}  # alias -> canonical_name
        self._arc_acquisitions: dict[int, list[str]] = {}  # arc_no -> [item names]

    def _normalize_name(self, name: str) -> str:
        """
        아이템 이름 정규화
        - 수식어 제거
        - 공백 정규화
        - 핵심 명사 추출
        """
        if not name:
            return ""

        normalized = name.strip()

        # 수식어 제거
        for modifier in self.IGNORABLE_MODIFIERS:
            normalized = re.sub(rf"\s*{modifier}\s*", " ", normalized)

        # 연속 공백 제거
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def _extract_core_item(self, name: str) -> str:
        """
        핵심 아이템 명사 추출
        예: "녹슨 백근 대도" → "대도"
        """
        normalized = self._normalize_name(name)

        # 카테고리별 핵심어 매칭
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                # 끝나는 경우 (대도, 장검, etc.)
                if normalized.endswith(kw):
                    # 앞부분이 있으면 그것도 포함 (태극검, 철혈사자패)
                    return normalized
                # 포함하는 경우
                match = re.search(rf"([가-힣]*{kw})", normalized)
                if match:
                    return match.group(1)

        return normalized

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        두 아이템 이름의 유사도 계산 (0.0 ~ 1.0)
        """
        core1 = self._extract_core_item(name1)
        core2 = self._extract_core_item(name2)

        # 완전 일치
        if core1 == core2:
            return 1.0

        # 한쪽이 다른 쪽을 포함
        if core1 in core2 or core2 in core1:
            return 0.9

        # 자카드 유사도 (문자 기반)
        set1 = set(core1)
        set2 = set(core2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        jaccard = intersection / union

        # 길이 가중치 (비슷한 길이면 더 유사)
        len_ratio = min(len(core1), len(core2)) / max(len(core1), len(core2))

        return jaccard * 0.7 + len_ratio * 0.3

    def register_item(
        self,
        name: str,
        arc_no: int,
        aliases: list[str] = None,
        category: str = "일반",
        owner: str = "주인공",
        episode: int = 0,
        source: str = "",
    ) -> str:
        """
        아이템 등록

        Args:
            name: 아이템 이름
            arc_no: 획득 Arc 번호
            aliases: 별칭 목록
            category: 카테고리
            owner: 초기 소유자 (기본: 주인공)
            episode: 획득 에피소드 번호
            source: 획득 경위 (하사, 구매, 발견 등)

        Returns:
            정규화된 이름 (canonical_name)
        """
        canonical = self._normalize_name(name)
        core = self._extract_core_item(name)

        # 이미 등록된 유사 아이템 확인
        existing = self._find_similar_item(name)
        if existing:
            # 기존 항목에 별칭 추가
            self.items[existing].aliases.add(name)
            self.items[existing].aliases.add(canonical)
            self._alias_map[name] = existing
            self._alias_map[canonical] = existing
            return existing

        # 카테고리 자동 감지
        if category == "일반":
            category = self._detect_category(name)

        # [V49.7] 초기 이벤트 생성
        initial_event = ItemEvent(
            arc=arc_no,
            episode=episode,
            event_type="acquired",
            actor=owner,
            target="",
            description=source or f"Arc {arc_no}에서 획득",
        )

        # 새 항목 등록
        entry = ItemEntry(
            canonical_name=core,
            aliases={name, canonical},
            acquired_arc=arc_no,
            category=category,
            current_owner=owner,
            current_state="소지중",
            event_history=[initial_event],
        )

        self.items[core] = entry
        self._alias_map[name] = core
        self._alias_map[canonical] = core

        # Arc별 획득 이력
        if arc_no not in self._arc_acquisitions:
            self._arc_acquisitions[arc_no] = []
        self._arc_acquisitions[arc_no].append(core)

        # 별칭 등록
        if aliases:
            for alias in aliases:
                entry.aliases.add(alias)
                self._alias_map[alias] = core

        return core

    def check_duplicate(self, name: str, current_arc: int) -> dict[str, Any]:
        """
        중복 획득 체크

        Args:
            name: 확인할 아이템 이름
            current_arc: 현재 Arc 번호

        Returns:
            {
                "is_duplicate": bool,
                "original": 원본 아이템명 (있으면),
                "acquired_in": 획득 Arc 번호 (있으면),
                "similarity": 유사도 (0.0 ~ 1.0),
                "reason": 중복 판단 사유
            }
        """
        result = {"is_duplicate": False, "original": None, "acquired_in": None, "similarity": 0.0, "reason": ""}

        # 1. 직접 매칭 (alias_map)
        canonical = self._alias_map.get(name)
        if canonical and canonical in self.items:
            entry = self.items[canonical]
            if entry.acquired_arc < current_arc and entry.consumed_arc == 0:
                result["is_duplicate"] = True
                result["original"] = canonical
                result["acquired_in"] = entry.acquired_arc
                result["similarity"] = 1.0
                result["reason"] = f"'{name}'은(는) Arc {entry.acquired_arc}에서 이미 '{canonical}'(으)로 획득됨"
                return result

        # 2. 유사도 기반 매칭
        similar = self._find_similar_item(name, threshold=0.75)
        if similar:
            entry = self.items[similar]
            if entry.acquired_arc < current_arc and entry.consumed_arc == 0:
                similarity = self._calculate_similarity(name, similar)
                result["is_duplicate"] = True
                result["original"] = similar
                result["acquired_in"] = entry.acquired_arc
                result["similarity"] = similarity
                result["reason"] = (
                    f"'{name}'은(는) Arc {entry.acquired_arc}에서 획득한 '{similar}'와(과) 유사 (유사도: {similarity:.0%})"
                )
                return result

        return result

    def _find_similar_item(self, name: str, threshold: float = 0.8) -> str | None:
        """
        유사한 기존 아이템 찾기

        Args:
            name: 검색할 이름
            threshold: 유사도 임계값

        Returns:
            가장 유사한 아이템의 canonical_name 또는 None
        """
        if not self.items:
            return None

        best_match = None
        best_similarity = 0.0

        for canonical, entry in self.items.items():
            # canonical name 비교
            similarity = self._calculate_similarity(name, canonical)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = canonical

            # aliases 비교
            for alias in entry.aliases:
                similarity = self._calculate_similarity(name, alias)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = canonical

        if best_similarity >= threshold:
            return best_match

        return None

    def _detect_category(self, name: str) -> str:
        """아이템 카테고리 자동 감지"""
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in name:
                    return category
        return "일반"

    def mark_consumed(self, name: str, arc_no: int, episode: int = 0) -> bool:
        """
        아이템 소모 처리

        Args:
            name: 아이템 이름
            arc_no: 소모 Arc 번호
            episode: 소모 에피소드 번호

        Returns:
            성공 여부
        """
        canonical = self._alias_map.get(name)
        if not canonical:
            similar = self._find_similar_item(name)
            canonical = similar

        if canonical and canonical in self.items:
            entry = self.items[canonical]
            entry.consumed_arc = arc_no
            entry.current_state = "소모됨"
            # [V49.7] 이벤트 기록
            event = ItemEvent(
                arc=arc_no,
                episode=episode,
                event_type="consumed",
                actor=entry.current_owner,
                description="아이템 소모/사용됨",
            )
            entry.event_history.append(event)
            return True

        return False

    # ═══════════════════════════════════════════════════════════════
    # [V49.7] 아이템 생애주기 추적 메서드
    # ═══════════════════════════════════════════════════════════════

    def transfer_item(
        self, name: str, from_owner: str, to_owner: str, arc: int, episode: int = 0, reason: str = ""
    ) -> bool:
        """
        아이템 소유권 이전

        Args:
            name: 아이템 이름
            from_owner: 이전 소유자
            to_owner: 새 소유자
            arc: Arc 번호
            episode: 에피소드 번호
            reason: 이전 사유

        Returns:
            성공 여부
        """
        canonical = self._alias_map.get(name)
        if not canonical:
            canonical = self._find_similar_item(name)

        if canonical and canonical in self.items:
            entry = self.items[canonical]
            old_owner = entry.current_owner

            # 이벤트 기록
            event = ItemEvent(
                arc=arc,
                episode=episode,
                event_type="transferred",
                actor=from_owner,
                target=to_owner,
                description=reason or f"{from_owner}에서 {to_owner}에게 이전",
            )
            entry.event_history.append(event)
            entry.current_owner = to_owner

            # 주인공이 아닌 타인에게 이전 시 "분배됨" 상태
            if to_owner and to_owner != "주인공" and "팽무진" not in to_owner:
                entry.current_state = "분배됨"
            else:
                entry.current_state = "소지중"

            return True
        return False

    def update_item_state(self, name: str, new_state: str, arc: int, episode: int = 0, description: str = "") -> bool:
        """
        아이템 상태 업데이트

        Args:
            name: 아이템 이름
            new_state: 새 상태 (소지중, 착용중, 보관중, 분실, 파괴, 분배됨)
            arc: Arc 번호
            episode: 에피소드 번호
            description: 상태 변경 설명

        Returns:
            성공 여부
        """
        canonical = self._alias_map.get(name)
        if not canonical:
            canonical = self._find_similar_item(name)

        if canonical and canonical in self.items:
            entry = self.items[canonical]
            old_state = entry.current_state

            event = ItemEvent(
                arc=arc,
                episode=episode,
                event_type="state_change",
                actor=entry.current_owner,
                target=new_state,
                description=description or f"상태 변경: {old_state} → {new_state}",
            )
            entry.event_history.append(event)
            entry.current_state = new_state

            return True
        return False

    def get_item_lifecycle(self, name: str) -> dict | None:
        """
        아이템 생애주기 조회

        Args:
            name: 아이템 이름

        Returns:
            생애주기 정보 또는 None
        """
        canonical = self._alias_map.get(name)
        if not canonical:
            canonical = self._find_similar_item(name)

        if canonical and canonical in self.items:
            entry = self.items[canonical]
            return {
                "canonical_name": entry.canonical_name,
                "category": entry.category,
                "acquired_arc": entry.acquired_arc,
                "consumed_arc": entry.consumed_arc,
                "current_owner": entry.current_owner,
                "current_state": entry.current_state,
                "event_history": [
                    {
                        "arc": e.arc,
                        "episode": e.episode,
                        "type": e.event_type,
                        "actor": e.actor,
                        "target": e.target,
                        "description": e.description,
                    }
                    for e in entry.event_history
                ],
                "aliases": list(entry.aliases),
            }
        return None

    def get_protagonist_items(self, protagonist_name: str = "주인공") -> list[dict]:
        """
        주인공이 현재 소지 중인 아이템 목록

        Args:
            protagonist_name: 주인공 이름

        Returns:
            주인공 소지 아이템 목록
        """
        result = []
        for canonical, entry in self.items.items():
            # 소모되지 않고, 주인공이 소유하며, 분배되지 않은 아이템
            if (
                entry.consumed_arc == 0
                and entry.current_state not in ["분배됨", "분실", "파괴", "소모됨"]
                and (
                    entry.current_owner == protagonist_name
                    or entry.current_owner == ""
                    or "팽무진" in entry.current_owner
                )
            ):
                result.append(
                    {
                        "name": canonical,
                        "category": entry.category,
                        "state": entry.current_state,
                        "acquired_arc": entry.acquired_arc,
                    }
                )
        return result

    def is_protagonist_item(self, name: str, protagonist_name: str = "주인공") -> bool:
        """
        아이템이 주인공 소유인지 확인

        Args:
            name: 아이템 이름
            protagonist_name: 주인공 이름

        Returns:
            주인공 소유 여부
        """
        canonical = self._alias_map.get(name)
        if not canonical:
            canonical = self._find_similar_item(name)

        if canonical and canonical in self.items:
            entry = self.items[canonical]
            # 분배된 것이 아니고, 소모되지 않은 것만
            if entry.current_state in ["분배됨", "분실", "파괴", "소모됨"]:
                return False
            if entry.current_owner and entry.current_owner != protagonist_name:
                if "팽무진" not in entry.current_owner:
                    return False
            return True
        return False

    def get_all_items(self, include_consumed: bool = False) -> dict[str, dict]:
        """모든 아이템 목록 반환 (V49.7 생애주기 포함)"""
        result = {}
        for canonical, entry in self.items.items():
            if not include_consumed and entry.consumed_arc > 0:
                continue
            result[canonical] = {
                "canonical_name": entry.canonical_name,
                "aliases": list(entry.aliases),
                "acquired_arc": entry.acquired_arc,
                "category": entry.category,
                "consumed_arc": entry.consumed_arc,
                # [V49.7] 생애주기 필드
                "current_owner": entry.current_owner,
                "current_state": entry.current_state,
                "event_count": len(entry.event_history),
            }
        return result

    def get_items_by_arc(self, arc_no: int) -> list[str]:
        """특정 Arc에서 획득한 아이템 목록"""
        return self._arc_acquisitions.get(arc_no, [])

    def get_forbidden_items(self, current_arc: int) -> list[dict]:
        """
        현재 Arc에서 획득 금지된 아이템 목록
        (이미 소지 중이며 소모되지 않은 아이템)
        """
        forbidden = []
        for canonical, entry in self.items.items():
            if entry.acquired_arc < current_arc and entry.consumed_arc == 0:
                forbidden.append({"name": canonical, "aliases": list(entry.aliases), "acquired_in": entry.acquired_arc})
        return forbidden

    def validate_arc_items(self, arc_no: int, items_to_acquire: list[str]) -> dict[str, Any]:
        """
        Arc 설계의 획득 아이템 목록 검증

        Args:
            arc_no: Arc 번호
            items_to_acquire: 획득 예정 아이템 목록

        Returns:
            {
                "valid": bool,
                "violations": [위반 목록],
                "warnings": [경고 목록]
            }
        """
        violations = []
        warnings = []

        for item in items_to_acquire:
            result = self.check_duplicate(item, arc_no)
            if result["is_duplicate"]:
                if result["similarity"] >= 0.9:
                    violations.append({"item": item, "severity": "CRITICAL", "message": result["reason"]})
                else:
                    warnings.append(
                        {"item": item, "severity": "WARNING", "message": f"유사 아이템 존재: {result['reason']}"}
                    )

        return {"valid": len(violations) == 0, "violations": violations, "warnings": warnings}

    def load_from_arcs(self, arcs_data: dict, protagonist_name: str = "주인공") -> int:
        """
        기존 Arc 데이터로부터 아이템 레지스트리 복원 (V49.7 확장)

        Args:
            arcs_data: arcs anchor 데이터
            protagonist_name: 주인공 이름

        Returns:
            로드된 아이템 수
        """
        count = 0

        # arcs_data가 리스트인 경우도 처리
        items_iter = arcs_data.items() if isinstance(arcs_data, dict) else enumerate(arcs_data)

        for key, arc in items_iter:
            if not isinstance(arc, dict):
                continue

            arc_no = arc.get("arc_no", 0)
            if not arc_no:
                continue

            state_constraints = arc.get("state_constraints") or {}  # [V70] None 방어

            # [V49.6] protagonist_items 우선, items_acquired 하위 호환
            protagonist_items = state_constraints.get("protagonist_items") or []  # [V70] None 방어
            if not protagonist_items:
                protagonist_items = state_constraints.get("items_acquired") or []  # [V70] None 방어

            if isinstance(protagonist_items, list):
                for item in protagonist_items:
                    if item:
                        self.register_item(item, arc_no, owner=protagonist_name, source="주인공 획득")
                        count += 1

            # [V49.6] distributed_items 처리
            distributed_items = state_constraints.get("distributed_items") or []  # [V70] None 방어
            if isinstance(distributed_items, list):
                for item in distributed_items:
                    if item:
                        # 먼저 등록 후 타인에게 이전 처리
                        self.register_item(item, arc_no, owner="타인", source="타인에게 분배")
                        # 분배됨 상태로 변경
                        canonical = self._alias_map.get(item)
                        if canonical and canonical in self.items:
                            self.items[canonical].current_state = "분배됨"
                        count += 1

            # 소모 아이템 처리
            items_consumed = state_constraints.get("items_consumed") or []  # [V70] None 방어
            if isinstance(items_consumed, list):
                for item in items_consumed:
                    if item:
                        self.mark_consumed(item, arc_no)

            # equipment에서도 추출 (주인공 소지품)
            arc_end_state = state_constraints.get("arc_end_state") or {}  # [V70] None 방어
            equipment = arc_end_state.get("equipment") or []  # [V70] None 방어
            if isinstance(equipment, list):
                for item in equipment:
                    if item and item not in protagonist_items:
                        self.register_item(item, arc_no, owner=protagonist_name, source="장비")
                        count += 1

        return count

    def generate_constraint_text(self, current_arc: int) -> str:
        """
        LLM 프롬프트용 제약 텍스트 생성

        Args:
            current_arc: 현재 Arc 번호

        Returns:
            제약 조건 텍스트
        """
        forbidden = self.get_forbidden_items(current_arc)

        if not forbidden:
            return ""

        lines = [
            "",
            "=" * 50,
            "[SEMANTIC ITEM REGISTRY - 중복 획득 금지 목록]",
            "=" * 50,
        ]

        for i, item in enumerate(forbidden[:10], 1):
            aliases_str = ", ".join(item["aliases"][:3])
            lines.append(f"{i}. '{item['name']}' (Arc {item['acquired_in']}에서 획득)")
            if aliases_str != item["name"]:
                lines.append(f"   - 별칭: {aliases_str}")

        if len(forbidden) > 10:
            lines.append(f"... 외 {len(forbidden) - 10}개")

        lines.append("=" * 50)
        lines.append("[!] 위 아이템 또는 유사한 이름의 아이템을 다시 획득하면 REJECT됩니다.")
        lines.append("")

        return "\n".join(lines)


# 싱글턴 인스턴스
_registry_instance = None
_registry_lock = threading.Lock()


def get_item_registry() -> SemanticItemRegistry:
    """SemanticItemRegistry 싱글턴 인스턴스 반환"""
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = SemanticItemRegistry()
    return _registry_instance


def create_item_registry() -> SemanticItemRegistry:
    """새 SemanticItemRegistry 인스턴스 생성"""
    return SemanticItemRegistry()
