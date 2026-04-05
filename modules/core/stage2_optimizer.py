"""
[V60.25] Stage 2 Optimizer
Stage 2 Arc 생성 통과율 최적화 모듈

utf8-hygiene: allow-file -- legacy Korean regex and prompt strings predate this bounded patch; current edits are ASCII-bounded.

Components:
1. StateSnapshotInjector - 이전 Arc 종료 상태를 정확히 주입
2. ArcAutoCorrector - 생성된 Arc 자동 수정
3. NegativeConstraintAmplifier - 금지 항목 강화
4. FocusedFeedbackGenerator - 구체적 피드백 생성
5. SessionFailureMemory - 세션 내 실패 패턴 추적
6. FewShotExampleManager - 성공 예시 관리

예상 효과:
- 첫 시도 PASS율: 70% → 85-90%
- Stage 2 소요 시간: -40~50%
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from modules.core.genre_schema_builder import is_wuxia
from modules.core.stage2_location_contract import collapse_stage2_location_label

# [BUG-I] location 필드에 혼입된 시간/날짜 설명 제거
_LOCATION_TIME_RE = re.compile(
    r"[.,]\s*시계는.+$"
    r"|[.,]\s*\d{4}년\s*\d+월.+$"
    r"|[.,]\s*\d+월\s*\d+일.+$"
    r"|[.,]\s*(?:오전|오후)\s*\d+시.+$",
    re.DOTALL,
)

# [BUG-E] items_consumed 추상 개념 필터 패턴
_ABSTRACT_ITEMS_CONSUMED_RE = re.compile(
    r"(이라는|으로 인한|의 기회비용|의 대가|라는 방패|심리적|정신적|감정적|추상적)"
)

_KOREAN_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _parse_korean_number(value: Any) -> float | None:
    """한국어 금액 문자열을 숫자로 변환한다. 예: 111.7억 -> 11170000000."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    text = value.strip().replace(",", "")
    if not text:
        return None

    match = _KOREAN_NUMBER_RE.search(text)
    if not match:
        return None

    try:
        number = float(match.group())
    except (ValueError, TypeError):
        return None

    if "억" in text:
        return number * 100_000_000
    if "만" in text:
        return number * 10_000
    return number


def _normalize_items(items: Any) -> list[str]:
    """아이템 리스트(str/dict 혼합)를 문자열 리스트로 정규화한다."""
    if isinstance(items, str):
        items = [chunk.strip() for chunk in re.split(r"[,/]", items) if chunk.strip()]
    if not isinstance(items, list):
        return []

    normalized = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name") or item.get("item") or ""
        else:
            name = str(item)
        name = name.strip()
        if name:
            normalized.append(name)
    return normalized


def _location_text_mentions_label(text: Any, label: str) -> bool:
    normalized_text = re.sub(r"\s+", " ", str(text or "")).strip()
    normalized_label = collapse_stage2_location_label(str(label or "").strip()) or str(label or "").strip()
    if not normalized_text or not normalized_label:
        return False
    if normalized_label in normalized_text:
        return True

    compact_text = re.sub(r"[^0-9A-Za-z가-힣]+", "", normalized_text)
    compact_label = re.sub(r"[^0-9A-Za-z가-힣]+", "", normalized_label)
    if not compact_text or not compact_label:
        return False
    return compact_label in compact_text


def _resolve_final_location_authority(tactical_doc: Any, arc_end_location: str, joint_location: str) -> str:
    end_location = collapse_stage2_location_label(str(arc_end_location or "").strip()) or str(arc_end_location or "").strip()
    final_location = collapse_stage2_location_label(str(joint_location or "").strip()) or str(joint_location or "").strip()
    if not end_location:
        return final_location
    if not final_location:
        return end_location
    if end_location == final_location:
        return end_location

    tactical = str(tactical_doc or "")
    end_mentioned = _location_text_mentions_label(tactical, end_location)
    final_mentioned = _location_text_mentions_label(tactical, final_location)
    if end_mentioned and not final_mentioned:
        return end_location
    if final_mentioned and not end_mentioned:
        return final_location
    return final_location

# ═══════════════════════════════════════════════════════════════════════════════
# 1. STATE SNAPSHOT INJECTOR
# ═══════════════════════════════════════════════════════════════════════════════


class StateSnapshotInjector:
    """
    [V60.25] 이전 Arc 종료 상태를 정확한 JSON으로 주입

    LLM이 시작 상태를 명확히 인식하도록 구조화된 스냅샷 제공
    """

    def __init__(self) -> None:
        self.last_snapshot = None

    def extract_snapshot(self, prev_arc: dict) -> dict:
        """이전 Arc에서 종료 상태 스냅샷 추출"""
        if not prev_arc:
            return self._get_default_snapshot()

        # joint_docs에서 추출
        joint_docs = prev_arc.get("joint_docs", {})
        state_constraints = prev_arc.get("state_constraints", {})
        arc_end = state_constraints.get("arc_end_state", {})
        status_shadow = prev_arc.get("status_shadow", {})

        snapshot = {
            "location": joint_docs.get("final_location") or arc_end.get("location", "알 수 없음"),
            "inventory": joint_docs.get("physical_inventory") or arc_end.get("equipment", []),
            "internal_energy": arc_end.get("internal_energy", 100),
            "injuries": arc_end.get("injuries") or "없음",
            "grants_received": state_constraints.get("grants_received", []),
            "items_acquired_total": self._collect_all_items(prev_arc),
        }

        # 문자열 정규화
        if isinstance(snapshot["inventory"], str):
            snapshot["inventory"] = [i.strip() for i in snapshot["inventory"].split(",") if i.strip()]

        self.last_snapshot = snapshot
        return snapshot

    def _collect_all_items(self, arc: dict) -> list[str]:
        """Arc에서 획득한 모든 아이템 수집"""
        items = []
        state = arc.get("state_constraints", {})
        # [BUG-F] protagonist_items 우선 폴백
        items.extend(state.get("protagonist_items") or state.get("items_acquired", []))

        # joint_docs의 inventory도 포함
        joint = arc.get("joint_docs", {})
        inv = joint.get("physical_inventory", [])
        if isinstance(inv, list):
            items.extend(inv)
        elif isinstance(inv, str):
            items.extend([i.strip() for i in inv.split(",") if i.strip()])

        # [Sweep-Codex] dict 아이템 방어 (unhashable type 방지)
        def _ikey(x):
            return x.get("name", x.get("item", "")) if isinstance(x, dict) else str(x)

        return list({_ikey(i) for i in items if i})

    def _get_default_snapshot(self) -> dict:
        """첫 Arc용 기본 스냅샷"""
        return {
            "location": "서사 시작점",
            "inventory": [],
            "internal_energy": 100,
            "injuries": "없음",
            "grants_received": [],
            "items_acquired_total": [],
        }

    def generate_injection_prompt(self, prev_arcs: list[dict], protagonist_name: str = "주인공") -> str:
        """Arc 생성 프롬프트에 주입할 상태 스냅샷 텍스트 생성"""
        if not prev_arcs:
            return self._generate_first_arc_prompt(protagonist_name)

        # 마지막 Arc에서 스냅샷 추출
        snapshot = self.extract_snapshot(prev_arcs[-1])

        # 전체 Arc에서 획득한 아이템 누적
        # [Sweep-Codex] dict 아이템 방어 (unhashable type 방지)
        def _ikey(x):
            return x.get("name", x.get("item", "")) if isinstance(x, dict) else str(x)

        all_items = set()
        all_grants = set()
        for arc in prev_arcs:
            state = arc.get("state_constraints", {})
            # [BUG-F] protagonist_items 우선 폴백
            _acq = state.get("protagonist_items") or state.get("items_acquired", [])
            all_items.update(_ikey(i) for i in _acq if i)
            all_grants.update(_ikey(i) for i in state.get("grants_received", []) if i)

        prompt = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔒 [V60.25] 필수 시작 상태 - 이 값으로 시작해야 함 (위반 시 즉시 REJECT)      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  주인공: {protagonist_name}
║  ───────────────────────────────────────────────────────────────────────────
║  📍 시작 위치: {snapshot["location"]}
║  📦 소지품: {", ".join(snapshot["inventory"]) if snapshot["inventory"] else "없음"}
║  ⚡ 핵심 수치: {snapshot["internal_energy"]}%
║  💔 부상: {snapshot["injuries"]}
║  🏅 수여물: {", ".join(all_grants) if all_grants else "없음"}
╠══════════════════════════════════════════════════════════════════════════════╣
║  ❌ 이미 획득한 아이템 (재획득 불가):
║     {", ".join(all_items) if all_items else "(없음)"}
╚══════════════════════════════════════════════════════════════════════════════╝

⚠️ arc_start_state는 반드시 위 값과 동일해야 합니다!
⚠️ items_acquired에 위 '이미 획득한 아이템'이 포함되면 즉시 REJECT!
"""
        return prompt

    def _generate_first_arc_prompt(self, protagonist_name: str) -> str:
        """첫 Arc용 프롬프트"""
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔒 [V60.25] 첫 Arc 시작 상태                                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  주인공: {protagonist_name}
║  📍 시작 위치: 서사 시작점 (Bible에서 지정된 위치)
║  📦 소지품: Bible에서 지정된 초기 아이템만
║  ⚡ 핵심 수치: 100%
║  💔 부상: 없음
╚══════════════════════════════════════════════════════════════════════════════╝
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ARC AUTO-CORRECTOR
# ═══════════════════════════════════════════════════════════════════════════════


class ArcAutoCorrector:
    """
    [V60.25] 생성된 Arc 자동 수정

    REJECT 전에 자동 수정 가능한 오류를 먼저 수정
    """

    def __init__(self) -> None:
        self.corrections_made = []

    def auto_correct(self, arc: dict, prev_arcs: list[dict], *, genre: str = "") -> tuple[dict, list[str]]:
        """
        Arc 자동 수정

        Returns:
            (수정된 Arc, 수정 내역 리스트)
        """
        self.corrections_made = []

        if not arc or not isinstance(arc, dict):
            return arc, []

        # 0. 메타 용어(Arc/Block/Stage) 서사 텍스트 치환
        arc = self._sanitize_tactical_meta_terms(arc)

        # 1. 중복 아이템 제거
        arc = self._remove_duplicate_items(arc, prev_arcs)

        # 2. 소지품 연속성 점검 (advisory-only)
        arc = self._check_equipment_continuity(arc, prev_arcs)

        # 3. 시작 위치 자동 수정
        arc = self._fix_start_location(arc, prev_arcs)

        # 4. 시작 상태 계승
        arc = self._fix_start_state(arc, prev_arcs)

        # 5. joint_docs 자동 추출/수정
        arc = self._fix_joint_docs(arc)

        # 5-1. arc_end_state.location을 joint_docs.final_location으로 동기화
        arc = self._sync_final_location(arc)

        # 5-2. tactical_doc 종료부 ↔ arc_end_state.location 정합성 점검 (advisory-only)
        arc = self._check_tactical_location_consistency(arc)

        # 6. 비무협 장르 무협 필드 제거
        if genre and not is_wuxia(genre):
            arc = self._strip_wuxia_fields(arc)

        # 7. 필수 필드 보장
        arc = self._ensure_required_fields(arc)

        # 8. items_consumed 추상 개념 제거
        arc = self._filter_abstract_items_consumed(arc)

        # 9. 내공 범위 정규화
        arc = self._normalize_internal_energy(arc)

        # 10. Arc 내 자산 성장률 점검 (advisory-only)
        arc = self._check_asset_growth_rate(arc, prev_arcs)

        return arc, self.corrections_made

    def _remove_duplicate_items(self, arc: dict, prev_arcs: list[dict]) -> dict:
        """이전 Arc에서 이미 획득한 아이템 제거"""
        if not prev_arcs:
            return arc

        # 이전에 획득한 모든 아이템 수집
        existing_items = set()
        for prev_arc in prev_arcs:
            state = prev_arc.get("state_constraints", {})
            # [Sweep46] dict 아이템 → 이름 추출 (set 추가 시 unhashable 방지)
            # [BUG-F] protagonist_items 우선 폴백
            for _it in (state.get("protagonist_items") or state.get("items_acquired", [])):
                if isinstance(_it, dict):
                    _n = _it.get("name", _it.get("item", ""))
                    if _n:
                        existing_items.add(_n)
                elif isinstance(_it, str):
                    existing_items.add(_it)
            joint = prev_arc.get("joint_docs", {})
            inv = joint.get("physical_inventory", [])
            if isinstance(inv, list):
                for _it in inv:
                    if isinstance(_it, dict):
                        _n = _it.get("name", _it.get("item", ""))
                        if _n:
                            existing_items.add(_n)
                    elif isinstance(_it, str):
                        existing_items.add(_it)

        # 현재 Arc의 items_acquired에서 중복 제거
        state = arc.get("state_constraints", {})
        # [BUG-F] protagonist_items 우선 폴백
        current_items = state.get("protagonist_items") or state.get("items_acquired", [])
        # [Sweep45] LLM이 dict 리스트 반환 시 문자열 정규화 (AttributeError 방지)
        if current_items and not all(isinstance(x, str) for x in current_items):
            current_items = [
                x.get("name", x.get("item", str(x))) if isinstance(x, dict) else str(x) for x in current_items
            ]
            state["items_acquired"] = current_items

        if current_items:
            original_count = len(current_items)
            filtered_items = [item for item in current_items if not self._is_duplicate(item, existing_items)]

            if len(filtered_items) < original_count:
                removed = set(current_items) - set(filtered_items)
                self.corrections_made.append(f"중복 아이템 제거: {', '.join(removed)}")
                state["items_acquired"] = filtered_items
                arc["state_constraints"] = state

        return arc

    def _is_duplicate(self, item: str, existing_items: set) -> bool:
        """아이템 중복 여부 확인 (유사도 기반)"""
        item_lower = item.lower().strip()
        for existing in existing_items:
            existing_lower = existing.lower().strip()
            # 완전 일치
            if item_lower == existing_lower:
                return True
            # 부분 포함 (3자 이상)
            if len(item_lower) >= 3 and len(existing_lower) >= 3:
                if item_lower in existing_lower or existing_lower in item_lower:
                    # 길이 비율 체크 (2배 이상 차이나면 다른 아이템)
                    ratio = max(len(item_lower), len(existing_lower)) / min(len(item_lower), len(existing_lower))
                    if ratio < 2.0:
                        return True
        return False

    def _fix_start_location(self, arc: dict, prev_arcs: list[dict]) -> dict:
        """시작 위치를 이전 Arc 종료 위치로 수정"""
        if not prev_arcs:
            return arc

        # 이전 Arc 종료 위치
        prev_arc = prev_arcs[-1]
        prev_location = None

        # [BUG-A] arc_end_state.location 우선 (auto_correct 후 최신값)
        end_state = prev_arc.get("state_constraints", {}).get("arc_end_state", {})
        prev_location = end_state.get("location")
        if not prev_location:
            joint = prev_arc.get("joint_docs", {})
            prev_location = joint.get("final_location")

        if not prev_location:
            return arc
        prev_location = collapse_stage2_location_label(prev_location) or str(prev_location).strip()

        # 현재 Arc 시작 위치
        state = arc.get("state_constraints", {})
        start_state = state.get("arc_start_state", {})
        current_location = str(start_state.get("location", "") or "").strip()
        current_location_canonical = collapse_stage2_location_label(current_location) or current_location

        # 위치가 다르면 수정
        if current_location_canonical and current_location_canonical != prev_location:
            self.corrections_made.append(f"시작 위치 수정: '{current_location}' → '{prev_location}'")
            start_state["location"] = prev_location
            state["arc_start_state"] = start_state
            arc["state_constraints"] = state

            # [TF-57-B] tactical_doc 내 "[시작 상태:...]" 텍스트도 동기화 (phantom fix 방지)
            tactical_doc = arc.get("tactical_doc", "")
            if tactical_doc and current_location in tactical_doc:
                # "[시작 상태: <위치>" 패턴에서 위치 문자열만 교체 (조사/공백 무시)
                new_tactical = tactical_doc.replace(current_location, prev_location)
                if new_tactical != tactical_doc:
                    arc["tactical_doc"] = new_tactical
                    self.corrections_made.append(
                        f"tactical_doc 위치 텍스트 동기화: '{current_location}' → '{prev_location}'"
                    )

        return arc

    def _fix_start_state(self, arc: dict, prev_arcs: list[dict]) -> dict:
        """시작 상태를 이전 Arc 종료 상태로 수정"""
        if not prev_arcs:
            return arc

        prev_arc = prev_arcs[-1]
        prev_end = prev_arc.get("state_constraints", {}).get("arc_end_state", {})
        prev_joint = prev_arc.get("joint_docs", {})
        prev_shadow = prev_arc.get("status_shadow", {})

        state = arc.get("state_constraints", {})
        start_state = state.get("arc_start_state", {})

        # 내공 계승
        prev_energy = prev_end.get("internal_energy")
        if prev_energy is not None:
            current_energy = start_state.get("internal_energy")
            if current_energy != prev_energy:
                self.corrections_made.append(f"시작 내공 수정: {current_energy}% → {prev_energy}%")
                start_state["internal_energy"] = prev_energy

        # 부상 계승
        prev_injuries = prev_end.get("injuries")
        if prev_injuries:
            current_injuries = start_state.get("injuries", "")
            if current_injuries != prev_injuries:
                self.corrections_made.append(f"시작 부상 수정: '{current_injuries}' → '{prev_injuries}'")
                start_state["injuries"] = prev_injuries

        # 소지품 계승
        prev_equipment = prev_joint.get("physical_inventory") or prev_end.get("equipment", [])
        if isinstance(prev_equipment, str):
            prev_equipment = [i.strip() for i in prev_equipment.split(",") if i.strip()]
        if prev_equipment:
            start_state["equipment"] = prev_equipment

        # [PATCH-D] Arc 간 시작 자산 vs 이전 종료 자산 차이 advisory
        prev_total = _parse_korean_number(prev_end.get("total_assets") or prev_end.get("capital"))
        curr_total = _parse_korean_number(start_state.get("total_assets") or start_state.get("capital"))
        if prev_total and curr_total and prev_total > 0:
            diff_pct = abs(curr_total - prev_total) / prev_total * 100
            if diff_pct > 5:
                self.corrections_made.append(
                    f"[PATCH-D] Arc 간 총자산 차이 {diff_pct:.1f}%: "
                    f"이전 종료 {prev_total:.0f}→현재 시작 {curr_total:.0f} (사유 확인 필요)"
                )

        state["arc_start_state"] = start_state
        arc["state_constraints"] = state

        return arc

    def _fix_joint_docs(self, arc: dict) -> dict:
        """tactical_doc에서 joint_docs 자동 추출/수정"""
        tactical = arc.get("tactical_doc", "")
        if not tactical:
            return arc

        joint = arc.get("joint_docs", {})

        # final_location이 없으면 tactical_doc에서 추출 시도
        if not joint.get("final_location"):
            # 마지막 화에서 위치 추출
            location_patterns = [
                r"제\s*\d+화[^:]*:[^.]*?(?:에서|으로|로)\s*([가-힣\w\s]+?)(?:에서|으로|를|을|이|가|\.)",
                r"(?:도착|이동|향하|머물)[^.]*?([가-힣]+(?:단|파|궁|부|성|촌|장|관|루|각|전|림|산|곡))",
            ]
            for pattern in location_patterns:
                match = re.search(pattern, tactical[-2000:])  # 마지막 2000자에서 검색
                if match:
                    joint["final_location"] = match.group(1).strip()
                    self.corrections_made.append(f"final_location 자동 추출: '{joint['final_location']}'")
                    break

        arc["joint_docs"] = joint
        return arc

    def _sync_final_location(self, arc: dict) -> dict:
        """joint_docs.final_location → arc_end_state.location 동기화."""
        joint_loc = arc.get("joint_docs", {}).get("final_location", "")
        if not joint_loc:
            return arc

        # [BUG-I] 시간/날짜 텍스트 제거 후 순수 위치만 반영
        cleaned_loc = _LOCATION_TIME_RE.sub("", joint_loc).rstrip("., ").strip()
        if not cleaned_loc:
            cleaned_loc = joint_loc  # 폴백
        cleaned_loc = collapse_stage2_location_label(cleaned_loc) or cleaned_loc

        state = arc.get("state_constraints", {})
        arc_end = state.get("arc_end_state", {})
        current_loc = arc_end.get("location", "")
        current_loc = collapse_stage2_location_label(current_loc) or current_loc
        preferred_loc = _resolve_final_location_authority(
            arc.get("tactical_doc", ""),
            current_loc,
            cleaned_loc,
        )
        if preferred_loc and cleaned_loc != preferred_loc:
            self.corrections_made.append(
                f"joint_docs.final_location synced by authority: '{cleaned_loc}' -> '{preferred_loc}'"
            )
            joint = arc.get("joint_docs", {})
            joint["final_location"] = preferred_loc
            arc["joint_docs"] = joint
        cleaned_loc = preferred_loc or cleaned_loc

        if current_loc != cleaned_loc:
            self.corrections_made.append(
                f"arc_end_state 위치 동기화: '{current_loc}' → '{cleaned_loc}'"
            )
            arc_end["location"] = cleaned_loc
            state["arc_end_state"] = arc_end
            arc["state_constraints"] = state

        return arc

    def _strip_wuxia_fields(self, arc: dict) -> dict:
        """비무협 장르에서 무협 전용 필드를 제거한다."""
        wuxia_only_keys = {"internal_energy", "realm", "qi_nature", "martial_arts"}
        state = arc.get("state_constraints", {})

        for section_key in ("arc_start_state", "arc_end_state"):
            section = state.get(section_key, {})
            if not isinstance(section, dict):
                continue

            removed = [key for key in wuxia_only_keys if key in section]
            for key in removed:
                section.pop(key, None)
            if removed:
                self.corrections_made.append(
                    f"{section_key}에서 무협 전용 필드 제거: {removed}"
                )

        arc["state_constraints"] = state
        return arc

    def _ensure_required_fields(self, arc: dict) -> dict:
        """필수 필드 보장"""
        # state_constraints 구조 보장
        if "state_constraints" not in arc:
            arc["state_constraints"] = {}

        state = arc["state_constraints"]

        if "arc_start_state" not in state:
            state["arc_start_state"] = {}
        if "arc_end_state" not in state:
            state["arc_end_state"] = {}
        # [BUG-F] protagonist_items가 있으면 items_acquired로 복사 (후속 소비자 일관성)
        if "items_acquired" not in state:
            state["items_acquired"] = state.get("protagonist_items", [])
        if "items_consumed" not in state:
            state["items_consumed"] = []

        # joint_docs 구조 보장
        if "joint_docs" not in arc:
            arc["joint_docs"] = {}

        joint = arc["joint_docs"]
        if "final_location" not in joint:
            joint["final_location"] = ""
        if "physical_inventory" not in joint:
            joint["physical_inventory"] = []

        return arc

    def _normalize_internal_energy(self, arc: dict) -> dict:
        """내공 범위 정규화 (0-100%)"""
        state = arc.get("state_constraints", {})

        for state_key in ["arc_start_state", "arc_end_state"]:
            sub_state = state.get(state_key, {})
            energy = sub_state.get("internal_energy")

            if energy is not None:
                try:
                    energy = int(energy)
                    # 범위 클램핑
                    if energy == 0:
                        pass  # 0 = 비무협 해당없음 — 최소값 보정 제외
                    elif energy < 5:
                        self.corrections_made.append(f"{state_key} 내공 하한 적용: {energy}% → 5%")
                        energy = 5
                    elif energy > 100:
                        self.corrections_made.append(f"{state_key} 내공 상한 적용: {energy}% → 100%")
                        energy = 100
                    sub_state["internal_energy"] = energy
                except (ValueError, TypeError):
                    pass

            state[state_key] = sub_state

        arc["state_constraints"] = state
        return arc

    def _filter_abstract_items_consumed(self, arc: dict) -> dict:
        """items_consumed에서 추상 개념 항목을 제거한다."""
        state = arc.get("state_constraints", {})
        items = state.get("items_consumed", [])
        if not isinstance(items, list):
            return arc

        filtered = []
        removed = []
        for item in items:
            if not isinstance(item, str):
                filtered.append(item)
                continue
            if len(item) > 15 or _ABSTRACT_ITEMS_CONSUMED_RE.search(item):
                removed.append(item)
            else:
                filtered.append(item)

        if removed:
            state["items_consumed"] = filtered
            arc["state_constraints"] = state
            self.corrections_made.append(
                f"items_consumed 추상 개념 {len(removed)}건 제거: {removed[:3]}"
            )

        return arc

    def _check_asset_growth_rate(self, arc: dict, prev_arcs: list[dict]) -> dict:
        """[PATCH-A] Arc 내 자산 성장률 상한 advisory."""
        if not prev_arcs:
            return arc

        state = arc.get("state_constraints", {})
        start = state.get("arc_start_state", {})
        end = state.get("arc_end_state", {})
        if not isinstance(start, dict) or not isinstance(end, dict):
            return arc

        start_val = _parse_korean_number(start.get("total_assets") or start.get("capital"))
        end_val = _parse_korean_number(end.get("total_assets") or end.get("capital"))
        if not (start_val and end_val and start_val > 0):
            return arc

        growth_pct = (end_val - start_val) / start_val * 100
        if growth_pct > 200:
            self.corrections_made.append(
                f"[PATCH-A] 자산 성장률 {growth_pct:.0f}% — "
                f"시작 {start_val:.0f}→종료 {end_val:.0f} (200% 상한 초과, 산술 검증 권고)"
            )
        return arc

    def _check_equipment_continuity(self, arc: dict, prev_arcs: list[dict]) -> dict:
        """[PATCH-B] 소지품 출현/소멸 감지 advisory."""
        if not prev_arcs:
            return arc

        prev_arc = prev_arcs[-1]
        prev_state = prev_arc.get("state_constraints", {})
        prev_end = prev_state.get("arc_end_state", {})
        prev_joint = prev_arc.get("joint_docs", {})
        prev_equip = set(_normalize_items(prev_joint.get("physical_inventory") or prev_end.get("equipment", [])))

        state = arc.get("state_constraints", {})
        start_state = state.get("arc_start_state", {})
        end_state = state.get("arc_end_state", {})
        start_equip = set(_normalize_items(start_state.get("equipment", [])))
        # [BUG-F] protagonist_items 우선, items_acquired 폴백 (response_schemas 스키마 정합)
        acquired = set(_normalize_items(
            state.get("protagonist_items") or state.get("items_acquired", [])
        ))
        end_equip = set(_normalize_items(end_state.get("equipment", [])))

        # 1) 출처 불명 등장
        unexplained = sorted(end_equip - start_equip - acquired - prev_equip)
        if unexplained:
            self.corrections_made.append(
                f"[PATCH-B] 출처 불명 소지품: {unexplained[:5]} (items_acquired에 미등록)"
            )

        # 2) 이전 Arc 대비 시작 시점 소멸
        disappeared = sorted(prev_equip - start_equip)
        if disappeared:
            self.corrections_made.append(
                f"[PATCH-B] 이전 Arc 소지품 소멸: {disappeared[:5]} (처분/폐기 사유 미기재)"
            )

        return arc

    def _check_tactical_location_consistency(self, arc: dict) -> dict:
        """[PATCH-C] tactical_doc 종료 위치와 arc_end_state.location 정합성 점검."""
        tactical = arc.get("tactical_doc", "")
        if not isinstance(tactical, str) or len(tactical) < 100:
            return arc

        end_loc = arc.get("state_constraints", {}).get("arc_end_state", {}).get("location", "")
        if not isinstance(end_loc, str) or not end_loc.strip():
            return arc

        tail = tactical[-500:]
        loc_keywords = re.findall(r"[가-힣]{2,}", end_loc)
        if not loc_keywords:
            return arc

        # 지역 접미사 제거 버전도 함께 검사 (강남구 -> 강남)
        reduced_keywords = []
        for kw in loc_keywords[:3]:
            reduced_keywords.append(kw)
            if len(kw) > 2 and kw[-1] in ("시", "도", "구", "군", "동", "로", "길"):
                reduced_keywords.append(kw[:-1])

        matched = [kw for kw in reduced_keywords if kw and kw in tail]
        if not matched:
            self.corrections_made.append(
                f"[PATCH-C] tactical_doc 종료 위치와 arc_end_state.location 불일치 — "
                f"arc_end_state: '{end_loc[:50]}', tactical_doc 말미에 해당 지명 미발견"
            )

        return arc

    def _sanitize_tactical_meta_terms(self, arc: dict) -> dict:
        """[C-1] tactical_doc의 시스템 메타 용어를 서사 용어로 치환."""
        tactical = arc.get("tactical_doc", "")
        if not isinstance(tactical, str) or "Arc" not in tactical:
            return arc

        replaced = tactical
        replacements = [
            (r"이전\s*Arc\s*종료", "이전 시기 종료"),
            (r"이전\s*Arc\s*시작", "이전 시기 시작"),
            (r"다음\s*Arc\s*종료", "다음 시기 종료"),
            (r"다음\s*Arc\s*시작", "다음 시기 시작"),
            (r"이전\s*Arc", "이전 시기"),
            (r"다음\s*Arc", "다음 시기"),
            (r"\bArc\s+\d+(?=\D|$)", "해당 시기"),
            (r"\bArc\b", "시기"),
        ]
        for pattern, repl in replacements:
            replaced = re.sub(pattern, repl, replaced)

        if replaced != tactical:
            arc["tactical_doc"] = replaced
            self.corrections_made.append("[C-1] tactical_doc 메타 용어 'Arc'를 서사 용어로 치환")
        return arc


# ═══════════════════════════════════════════════════════════════════════════════
# 3. NEGATIVE CONSTRAINT AMPLIFIER
# ═══════════════════════════════════════════════════════════════════════════════


class NegativeConstraintAmplifier:
    """
    [V60.25] 금지 항목 강화

    단순 목록이 아닌 "왜 금지인지" 맥락과 증거를 제공
    """

    def __init__(self) -> None:
        pass

    def amplify_constraints(self, prev_arcs: list[dict]) -> str:
        """강화된 제약 조건 프롬프트 생성"""
        if not prev_arcs:
            return ""

        # 아이템 획득 히스토리
        item_history = self._build_item_history(prev_arcs)

        # 수여물 히스토리
        grant_history = self._build_grant_history(prev_arcs)

        prompt = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  🚫 [V60.25] 절대 금지 사항 - 위반 시 즉시 REJECT                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

        if item_history:
            prompt += "\n【아이템 재획득 금지】\n"
            for item_info in item_history:
                prompt += f"  ❌ {item_info['item']}\n"
                prompt += f"     └─ Arc {item_info['arc']} 제{item_info['episode']}화에서 획득\n"
                if item_info.get("context"):
                    prompt += f'     └─ 상황: "{item_info["context"][:50]}..."\n'

        if grant_history:
            prompt += "\n【수여물 재수여 금지】\n"
            for grant_info in grant_history:
                prompt += f"  ❌ {grant_info['grant']}\n"
                prompt += f"     └─ Arc {grant_info['arc']}에서 수여받음\n"
                prompt += f"     └─ 수여자: {grant_info.get('from', '알 수 없음')}\n"

        prompt += """
──────────────────────────────────────────────────────────────────────────────
⚠️ 위 아이템/수여물을 items_acquired 또는 grants_received에 포함하면 REJECT!
⚠️ tactical_doc에서 "~를 획득했다/얻었다/받았다" 표현도 금지!
──────────────────────────────────────────────────────────────────────────────
"""
        return prompt

    def _build_item_history(self, prev_arcs: list[dict]) -> list[dict]:
        """아이템 획득 히스토리 구축"""
        history = []

        for arc in prev_arcs:
            arc_no = arc.get("arc_no", "?")
            state = arc.get("state_constraints", {})
            # [BUG-F] protagonist_items 우선 폴백
            items = state.get("protagonist_items") or state.get("items_acquired", [])
            tactical = arc.get("tactical_doc", "")

            for item in items:
                item = str(item) if isinstance(item, dict) else item
                # tactical_doc에서 획득 맥락 추출
                context = ""
                if tactical:
                    # 아이템 언급 주변 텍스트 추출
                    match = re.search(rf".{{0,50}}{re.escape(item)}.{{0,50}}", tactical)
                    if match:
                        context = match.group(0)

                # 화수 추출 시도
                episode = "?"
                if tactical:
                    ep_match = re.search(rf"제\s*(\d+)화[^.]*{re.escape(item)}", tactical)
                    if ep_match:
                        episode = ep_match.group(1)

                history.append({"item": item, "arc": arc_no, "episode": episode, "context": context})

        return history

    def _build_grant_history(self, prev_arcs: list[dict]) -> list[dict]:
        """수여물 히스토리 구축"""
        history = []

        for arc in prev_arcs:
            arc_no = arc.get("arc_no", "?")
            state = arc.get("state_constraints", {})
            grants = state.get("grants_received", [])
            tactical = arc.get("tactical_doc", "")

            for grant in grants:
                # tactical_doc에서 수여자(from) 추출 시도
                grant_from = "알 수 없음"
                if isinstance(grant, str) and tactical and grant in tactical:
                    grant_idx = tactical.find(grant)
                    context = tactical[max(0, grant_idx - 50) : grant_idx]
                    match = re.search(r"([가-힣]{2,6})(?:가|에게|로부터|께서)", context)
                    if match:
                        grant_from = match.group(1)

                history.append(
                    {
                        "grant": grant,
                        "arc": arc_no,
                        "from": grant_from,
                    }
                )

        return history


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FOCUSED FEEDBACK GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════


class FocusedFeedbackGenerator:
    """
    [V60.25] 구체적 피드백 생성

    REJECT 시 구체적 위치 + 수정 방법을 제시
    """

    def __init__(self) -> None:
        pass

    def generate_feedback(self, validation_result: dict, arc: dict, prev_arcs: list[dict]) -> str:
        """구체적 피드백 생성"""
        issues = validation_result.get("issues", [])
        if not issues:
            issues = validation_result.get("critical_issues", [])

        if not issues:
            return "검증 통과"

        feedback_parts = []
        feedback_parts.append("=" * 70)
        feedback_parts.append("🚨 [V60.25] 구체적 수정 가이드 - 아래 사항만 수정하면 PASS!")
        feedback_parts.append("=" * 70)

        for i, issue in enumerate(issues[:5], 1):  # 최대 5개
            issue_text = issue.get("issue", str(issue)) if isinstance(issue, dict) else str(issue)
            category = issue.get("category", "unknown") if isinstance(issue, dict) else "unknown"

            feedback_parts.append(f"\n【문제 {i}】 {issue_text}")

            # 카테고리별 구체적 수정 가이드
            fix_guide = self._get_fix_guide(category, issue, arc, prev_arcs)
            if fix_guide:
                feedback_parts.append(f"   ✅ 수정 방법: {fix_guide}")

        feedback_parts.append("\n" + "=" * 70)

        return "\n".join(feedback_parts)

    def _get_fix_guide(self, category: str, issue: Any, arc: dict, prev_arcs: list[dict]) -> str:
        """카테고리별 수정 가이드"""

        if "중복" in str(issue) or "duplicate" in category.lower():
            return "items_acquired에서 해당 아이템을 제거하고, tactical_doc에서 '획득' 대신 '사용/활용' 표현으로 변경"

        if "위치" in str(issue) or "location" in category.lower():
            if prev_arcs:
                prev_loc = prev_arcs[-1].get("joint_docs", {}).get("final_location", "")
                return f"arc_start_state.location을 '{prev_loc}'으로 수정"
            return "arc_start_state.location을 이전 Arc 종료 위치로 수정"

        if "내공" in str(issue) or "energy" in category.lower():
            if prev_arcs:
                prev_energy = (
                    prev_arcs[-1].get("state_constraints", {}).get("arc_end_state", {}).get("internal_energy", 100)
                )
                return f"arc_start_state.internal_energy를 {prev_energy}%로 수정"
            return "arc_start_state.internal_energy를 이전 Arc 종료 내공으로 수정"

        if "부상" in str(issue) or "injur" in category.lower():
            return "arc_start_state.injuries를 이전 Arc 종료 부상 상태로 수정"

        if "분량" in str(issue) or "length" in category.lower():
            return "tactical_doc을 3000자 이상으로 확장 (각 화당 600자 이상)"

        if "joint_docs" in str(issue).lower():
            return "tactical_doc 마지막 화 내용과 joint_docs.final_location/physical_inventory를 일치시킴"

        return "해당 필드를 이전 Arc 상태와 일치시킴"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SESSION FAILURE MEMORY
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class FailureRecord:
    """실패 기록"""

    arc_no: int
    attempt: int
    reason: str
    category: str
    details: str = ""
    timestamp: str = ""


class SessionFailureMemory:
    """
    [V60.25] 세션 내 실패 패턴 추적

    같은 세션에서 반복되는 실패 패턴을 학습하여 프롬프트에 주입
    """

    def __init__(self) -> None:
        self.failures: list[FailureRecord] = []
        self.pattern_counts: dict[str, int] = defaultdict(int)

    def record_failure(
        self,
        arc_no: int,
        attempt: int = 0,
        reason: str = "",
        category: str = "unknown",
        details: str = "",
        failure_type: str = None,
    ):
        """실패 기록

        Args:
            arc_no: Arc 번호
            attempt: 시도 횟수 (기본값 0)
            reason: 실패 사유
            category: 실패 카테고리 (deprecated, use failure_type)
            details: 추가 상세 정보
            failure_type: 실패 유형 (category 대체)
        """
        # failure_type이 제공되면 category로 사용 (호환성)
        actual_category = failure_type if failure_type else category
        actual_reason = reason if reason else details

        record = FailureRecord(
            arc_no=arc_no, attempt=attempt, reason=actual_reason, category=actual_category, details=details
        )
        self.failures.append(record)
        self.pattern_counts[actual_category] += 1

    def get_top_failure_patterns(self, n: int = 3) -> list[tuple[str, int]]:
        """가장 빈번한 실패 패턴 반환"""
        sorted_patterns = sorted(self.pattern_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_patterns[:n]

    def generate_warning_prompt(self) -> str:
        """경고 프롬프트 생성"""
        if not self.failures:
            return ""

        top_patterns = self.get_top_failure_patterns(3)
        recent_failures = self.failures[-5:]  # 최근 5개

        prompt = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ [V60.25] 세션 실패 이력 - 같은 실수 반복 금지!                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  총 {len(self.failures)}회 REJECT 발생
║
║  【빈번한 실패 원인】
"""
        for pattern, count in top_patterns:
            prompt += f"║    • {pattern}: {count}회\n"

        prompt += "║\n║  【최근 실패 사례】\n"
        for f in recent_failures:
            prompt += f"║    • Arc {f.arc_no} (시도 {f.attempt}): {f.reason[:50]}\n"

        prompt += """╚══════════════════════════════════════════════════════════════════════════════╝
"""
        return prompt

    def clear(self) -> None:
        """메모리 초기화"""
        self.failures.clear()
        self.pattern_counts.clear()

    def clear_arc_failures(self, arc_no: int):
        """특정 Arc의 실패 기록 제거 (해당 Arc가 성공했을 때)"""
        self.failures = [f for f in self.failures if f.arc_no != arc_no]
        # 패턴 카운트도 감소 (이미 처리됨)
        # Note: 패턴 카운트는 세션 전체 학습이므로 감소하지 않음


# ═══════════════════════════════════════════════════════════════════════════════
# 6. FEW-SHOT EXAMPLE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════


class FewShotExampleManager:
    """
    [V60.25] 성공 예시 관리

    PASS된 Arc를 저장하고 프롬프트에 주입
    """

    def __init__(self, max_examples: int = 3):
        self.examples: list[dict] = []
        self.max_examples = max_examples

    def add_successful_arc(self, arc: dict):
        """성공한 Arc 저장"""
        # 간소화된 버전만 저장
        simplified = {
            "arc_no": arc.get("arc_no"),
            "tactical_doc_length": len(arc.get("tactical_doc", "")),
            # [BUG-F] protagonist_items 우선 폴백
            "items_acquired": (
                arc.get("state_constraints", {}).get("protagonist_items")
                or arc.get("state_constraints", {}).get("items_acquired", [])
            ),
            "state_constraints_sample": {
                "arc_start_state": arc.get("state_constraints", {}).get("arc_start_state", {}),
                "arc_end_state": arc.get("state_constraints", {}).get("arc_end_state", {}),
            },
            "joint_docs": arc.get("joint_docs", {}),
        }

        self.examples.append(simplified)

        # 최대 개수 유지
        if len(self.examples) > self.max_examples:
            self.examples.pop(0)

    def generate_example_prompt(self) -> str:
        """예시 프롬프트 생성"""
        if not self.examples:
            return ""

        prompt = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ [V60.25] 성공 예시 - 이런 형식으로 작성하면 PASS!                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        for i, ex in enumerate(self.examples[-2:], 1):  # 최근 2개만
            prompt += f"""
【성공 예시 {i}】 Arc {ex["arc_no"]}
  • tactical_doc 분량: {ex["tactical_doc_length"]}자
  • 신규 획득 아이템: {len(ex["items_acquired"])}개
  • state_constraints 구조: arc_start_state → arc_end_state 명확히 구분
  • joint_docs: final_location, physical_inventory 포함
"""
        return prompt

    def get_average_tactical_length(self) -> int:
        """평균 tactical_doc 길이"""
        if not self.examples:
            return 3500
        lengths = [ex["tactical_doc_length"] for ex in self.examples]
        return sum(lengths) // len(lengths)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. INTEGRATED OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════════


class Stage2Optimizer:
    """
    [V60.25] Stage 2 통합 최적화기

    모든 최적화 컴포넌트를 통합 관리
    """

    def __init__(self) -> None:
        self.snapshot_injector = StateSnapshotInjector()
        self.auto_corrector = ArcAutoCorrector()
        self.constraint_amplifier = NegativeConstraintAmplifier()
        self.feedback_generator = FocusedFeedbackGenerator()
        self.failure_memory = SessionFailureMemory()
        self.example_manager = FewShotExampleManager()

        # 통계
        self.stats = {
            "total_arcs": 0,
            "first_pass": 0,
            "auto_corrected": 0,
            "total_retries": 0,
        }

    def generate_optimized_prompt(
        self, prev_arcs: list[dict], protagonist_name: str = "주인공", include_examples: bool = True
    ) -> str:
        """최적화된 프롬프트 생성"""
        parts = []

        # 1. State Snapshot
        parts.append(self.snapshot_injector.generate_injection_prompt(prev_arcs, protagonist_name))

        # 2. Negative Constraints
        parts.append(self.constraint_amplifier.amplify_constraints(prev_arcs))

        # 3. Session Failure Warning
        if self.failure_memory.failures:
            parts.append(self.failure_memory.generate_warning_prompt())

        # 4. Few-Shot Examples
        if include_examples and self.example_manager.examples:
            parts.append(self.example_manager.generate_example_prompt())

        return "\n".join(parts)

    def post_process_arc(self, arc: dict, prev_arcs: list[dict], *, genre: str = "") -> tuple[dict, list[str]]:
        """Arc 후처리 (자동 수정)"""
        self.stats["total_arcs"] += 1

        corrected_arc, corrections = self.auto_corrector.auto_correct(arc, prev_arcs, genre=genre)

        if corrections:
            self.stats["auto_corrected"] += 1
            logging.info(f"[V60.25] Auto-correct: {len(corrections)} fixes applied")
            for c in corrections[:3]:
                logging.info(f"- {c}")

        return corrected_arc, corrections

    def record_result(self, arc_no: int, attempt: int, passed: bool, arc: dict = None, validation_result: dict = None):
        """결과 기록"""
        if passed:
            if attempt == 0:
                self.stats["first_pass"] += 1
            if arc:
                self.example_manager.add_successful_arc(arc)
        else:
            self.stats["total_retries"] += 1
            if validation_result:
                issues = validation_result.get("issues", []) or validation_result.get("critical_issues", [])
                if issues:
                    first_issue = issues[0]
                    reason = (
                        first_issue.get("issue", str(first_issue))
                        if isinstance(first_issue, dict)
                        else str(first_issue)
                    )
                    category = first_issue.get("category", "unknown") if isinstance(first_issue, dict) else "unknown"
                    self.failure_memory.record_failure(arc_no, attempt, reason, category)

    def generate_focused_feedback(self, validation_result: dict, arc: dict, prev_arcs: list[dict]) -> str:
        """구체적 피드백 생성"""
        return self.feedback_generator.generate_feedback(validation_result, arc, prev_arcs)

    def get_stats(self) -> dict:
        """통계 반환"""
        total = self.stats["total_arcs"]
        if total == 0:
            return self.stats

        return {
            **self.stats,
            "first_pass_rate": f"{self.stats['first_pass'] / total * 100:.1f}%",
            "auto_correct_rate": f"{self.stats['auto_corrected'] / total * 100:.1f}%",
            "avg_retries": f"{self.stats['total_retries'] / total:.2f}",
        }

    def print_stats(self) -> None:
        """통계 출력"""
        stats = self.get_stats()
        logging.info("\n[V60.25 Stage 2 Optimizer 통계]")
        logging.info(f"총 Arc: {stats['total_arcs']}")
        logging.info(f"첫 시도 PASS: {stats['first_pass']} ({stats.get('first_pass_rate', 'N/A')})")
        logging.info(f"자동 수정: {stats['auto_corrected']} ({stats.get('auto_correct_rate', 'N/A')})")
        logging.info(f"총 재시도: {stats['total_retries']} (평균 {stats.get('avg_retries', 'N/A')})")


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════


def create_stage2_optimizer() -> Stage2Optimizer:
    """Stage2Optimizer 생성 헬퍼"""
    return Stage2Optimizer()
