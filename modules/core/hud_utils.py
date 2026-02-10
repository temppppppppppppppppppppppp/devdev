"""
[V64 P2-7] HUD Context Utility - 공통 HUD 컨텍스트 빌더

Director, ChiefWriter, BlueprintEnsemble에서 중복되던
_build_hud_context 로직을 단일 모듈로 통합.

Usage:
    from modules.core.hud_utils import build_hud_context
    hud_str = build_hud_context(state_tracker, ep_num, variant="writer")
"""

from typing import Optional


def build_hud_context(
    state_tracker,
    ep_num: int,
    variant: str = "writer",
    empty_fallback: str = "",
) -> str:
    """
    [V64 P2-7] StateTracker에서 고밀도 HUD 컨텍스트 구축

    3가지 variant를 하나의 함수로 통합:
    - "director": Director용 (core_fields: name/location/hp/mp/..., extra_fields dict,
                               items 10개, relationships 5개 줄단위, NPC 8명+사망5명)
    - "writer":   ChiefWriter용 (core_fields: location/internal_energy/injuries,
                               extended_fields 13개, weapons+items 8개, relationships inline,
                               alive NPC 10명+사망 inline)
    - "blueprint": BlueprintEnsemble용 (writer와 동일하나 header/fallback 다름)

    Args:
        state_tracker: StateTracker 인스턴스
        ep_num: 현재 에피소드 번호
        variant: "director" | "writer" | "blueprint"
        empty_fallback: state_tracker가 None이거나 내용 없을 때 반환값

    Returns:
        고밀도 HUD 문자열 (프롬프트 주입용)
    """
    if not state_tracker:
        if variant == "director":
            return "(상태 추적기 없음)"
        return empty_fallback

    lines = []

    # ── 1. 주인공 상태 (고밀도 필드) ──
    try:
        prev_state = None
        if ep_num > 1 and hasattr(state_tracker, 'episode_states'):
            prev_state = state_tracker.episode_states.get(ep_num - 1)

        if prev_state:
            state_dict = prev_state.to_dict() if hasattr(prev_state, 'to_dict') else {}

            if variant == "director":
                _build_director_protagonist(lines, state_dict)
            else:
                header = "[주인공 현재 상태 - 고밀도]" if variant == "writer" else "[주인공 현재 상태]"
                _build_writer_protagonist(lines, state_dict, header)
        else:
            if variant == "director":
                lines.append("[주인공 상태: 이전 에피소드 기록 없음]")
            # writer/blueprint: 기록 없으면 섹션 생략

    except Exception as e:
        lines.append(f"  (상태 로드 오류: {str(e)[:30]})")

    # ── 2. NPC 레지스트리 ──
    try:
        if hasattr(state_tracker, 'npc_registry') and state_tracker.npc_registry:
            if variant == "director":
                _build_director_npcs(lines, state_tracker.npc_registry)
            else:
                _build_writer_npcs(lines, state_tracker.npc_registry)
    except Exception:
        pass  # NPC 로드 실패 시 무시

    # ── 결과 반환 ──
    if lines:
        return "\n".join(lines)

    # fallback
    if variant == "director":
        return "(HUD 정보 없음)"
    elif variant == "blueprint":
        return "(상태 정보 없음)"
    return empty_fallback


# ═══════════════════════════════════════════════════════════════════════
# 내부 빌더 함수
# ═══════════════════════════════════════════════════════════════════════

def _build_director_protagonist(lines: list, state_dict: dict):
    """Director variant: core_fields + extra_fields dict + items(10) + relationships(5, 줄단위)"""
    lines.append("[주인공 현재 상태 - 고밀도]")

    core_fields = ['name', 'location', 'hp', 'mp', 'martial_level', 'inner_power', 'status']
    for field in core_fields:
        if field in state_dict and state_dict[field]:
            lines.append(f"  {field}: {state_dict[field]}")

    # Extended fields (extra_fields dict)
    extra = state_dict.get('extra_fields', {})
    if extra:
        lines.append("  [확장 상태]")
        for k, v in extra.items():
            if v:
                lines.append(f"    {k}: {v}")

    # Items
    items = state_dict.get('items', [])
    if items:
        lines.append(f"  보유 아이템: {', '.join(items[:10])}")

    # Relationships (줄 단위)
    relationships = state_dict.get('relationships', {})
    if relationships:
        lines.append("  관계:")
        for name, rel in list(relationships.items())[:5]:
            lines.append(f"    - {name}: {rel}")


def _build_writer_protagonist(lines: list, state_dict: dict, header: str):
    """Writer/Blueprint variant: core_fields + extended_fields 13개 + weapons+items(8) + relationships inline"""
    lines.append(header)

    # 핵심 필드 (항상 표시)
    core_fields = ['location', 'internal_energy', 'injuries']
    for field in core_fields:
        if field in state_dict:
            lines.append(f"  - {field}: {state_dict[field]}")

    # 확장 필드 (있으면 표시)
    extended_fields = [
        ('realm', '경지'), ('reputation', '평판'), ('mental_state', '정신상태'),
        ('faction', '소속'), ('rank', '지위'), ('gold', '재화'),
        ('awakening_grade', '각성등급'), ('gate_clearance', '클리어 게이트'),
        ('net_worth', '자산'), ('market_reputation', '시장평판'),
        ('mana', '마나'), ('skills', '스킬'), ('titles', '칭호')
    ]

    for field, display in extended_fields:
        if field in state_dict and state_dict[field]:
            value = state_dict[field]
            # 리스트는 쉼표로 연결
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value[:5])  # 최대 5개
            lines.append(f"  - {display}: {value}")

    # 소지품 (weapons + items)
    items = state_dict.get('items', [])
    weapons = state_dict.get('weapons', [])
    if items or weapons:
        all_items = weapons + items
        lines.append(f"  - 소지품: {', '.join(str(i) for i in all_items[:8])}")

    # 관계 (inline)
    relationships = state_dict.get('relationships', {})
    if relationships:
        rel_str = ', '.join(f"{k}:{v}" for k, v in list(relationships.items())[:5])
        lines.append(f"  - 관계: {rel_str}")


def _build_director_npcs(lines: list, npc_registry: dict):
    """Director variant: alive(8명) role/location, dead(5명) death_arc"""
    alive_npcs = [
        name for name, data in npc_registry.items()
        if isinstance(data, dict) and data.get('status') != 'dead'
    ]
    dead_npcs = [
        name for name, data in npc_registry.items()
        if isinstance(data, dict) and data.get('status') == 'dead'
    ]

    if alive_npcs:
        lines.append(f"\n[활성 NPC ({len(alive_npcs)}명)]")
        for name in alive_npcs[:8]:
            npc_data = npc_registry.get(name, {})
            role = npc_data.get('role', '?')
            location = npc_data.get('location', '?')
            lines.append(f"  - {name} ({role}) @ {location}")

    if dead_npcs:
        lines.append(f"\n[사망 NPC ({len(dead_npcs)}명) - 등장 금지!]")
        for name in dead_npcs[:5]:
            npc_data = npc_registry.get(name, {})
            death_arc = npc_data.get('death_arc', '?')
            lines.append(f"  - {name}: Arc {death_arc}에서 사망")


def _build_writer_npcs(lines: list, npc_registry: dict):
    """Writer/Blueprint variant: alive(10명) role/faction/relationship, dead inline"""
    alive_npcs = [
        (name, info) for name, info in npc_registry.items()
        if info.get('status') != 'dead'
    ][:10]  # 최대 10명

    if alive_npcs:
        lines.append("")
        lines.append("[등장 가능 NPC]")
        for name, info in alive_npcs:
            role = info.get('role', '')
            relationship = info.get('relationship', '')
            faction = info.get('faction', '')

            npc_desc = f"  - {name}"
            details = []
            if role:
                details.append(role)
            if faction:
                details.append(faction)
            if relationship:
                details.append(f"관계:{relationship}")
            if details:
                npc_desc += f" ({', '.join(details)})"
            lines.append(npc_desc)

    # 사망 NPC 경고
    dead_npcs = [
        name for name, info in npc_registry.items()
        if info.get('status') == 'dead'
    ]
    if dead_npcs:
        lines.append("")
        lines.append(f"\u26a0\ufe0f [사망 NPC - 등장 금지]: {', '.join(dead_npcs[:5])}")


# ═══════════════════════════════════════════════════════════════════════
# [V64.P4] HUD Trend 안전 호출 — 3중 복사 통합
# ═══════════════════════════════════════════════════════════════════════

def get_hud_trend_safe(context, ep_num: int) -> str:
    """
    [V64.P4] HUD 추세 안전 호출 (공용 유틸리티).

    기존 Architect, ChiefWriter, Writer에 3중 복사되어 있던
    _get_hud_trend_safe 메서드를 단일 함수로 통합.

    Args:
        context: 에이전트의 self.context (ProjectContext 등)
        ep_num: 에피소드 번호

    Returns:
        str: HUD 추세 문자열 또는 폴백 메시지
    """
    try:
        if hasattr(context, 'sys') and hasattr(context.sys, 'hud'):
            return context.sys.hud.get_hud_trend(ep_num, window=5)
        elif hasattr(context, 'martial'):
            return context.martial.get_hud_trend(ep_num, window=5)
        else:
            return "HUD 추세 정보 없음"
    except Exception:
        return "안정적"
