"""
[V64.P4] Arc Summary Utility — 이전 Arc 요약 생성 공용 함수.

기존 arc_critic, consensus_validator, unified_arc_validator에 3중 복사되던
_generate_prev_summary 메서드를 단일 함수로 통합.

Usage:
    from modules.core.arc_summary_utils import generate_prev_arc_summary
    summary = generate_prev_arc_summary(prev_arcs, include_energy=True)
"""

import re

from modules.core.constants import Stage2Limits


def generate_prev_arc_summary(
    prev_arcs: list[dict],
    include_energy: bool = True,
    max_recent: int = 3,
) -> str:
    """
    [V64.P4] 이전 Arc 요약 생성 (공용 유틸리티).

    3가지 variant를 하나로 통합:
    - include_energy=False: arc_critic 스타일 (간소)
    - include_energy=True:  consensus_validator / unified_arc_validator 스타일 (상세)

    Args:
        prev_arcs: 이전 Arc 리스트
        include_energy: 내공/부상 정보 포함 여부
        max_recent: 최근 N개 Arc만 사용

    Returns:
        str: 이전 Arc 요약 문자열
    """
    if not prev_arcs:
        return "첫 Arc (이전 Arc 없음)"

    lines = []
    for arc in prev_arcs[-max_recent:]:
        arc_no = arc.get("arc_no", "?")
        joint = arc.get("joint_docs", {})
        state = arc.get("state_constraints", {})
        shadow = arc.get("status_shadow", {})

        lines.append(f"[Arc {arc_no}]")

        if include_energy:
            # arc_end_state 우선 탐색
            arc_end = state.get("arc_end_state", {})
            final_energy = arc_end.get("internal_energy")
            final_injuries = arc_end.get("injuries")

            if final_energy is None:
                # [TF-21-04] 비무협 key_stat_change와 무협 internal_energy_loss 분리
                _energy_loss = shadow.get("internal_energy_loss")
                _key_stat = shadow.get("key_stat_change")
                if _energy_loss is not None:
                    loss_str = _energy_loss
                    try:
                        match = re.search(r"(\d+)", str(loss_str))
                        if match:
                            loss = int(match.group(1))
                            final_energy = max(0, 100 - loss)
                        else:
                            final_energy = Stage2Limits.INTERNAL_ENERGY_FALLBACK
                    except Exception:
                        final_energy = Stage2Limits.INTERNAL_ENERGY_FALLBACK
                elif _key_stat is not None:
                    # 비무협 장르: key_stat_change는 에너지가 아님 → 해당없음으로 표시
                    final_energy = 0
                else:
                    final_energy = Stage2Limits.INTERNAL_ENERGY_FALLBACK

            if final_injuries is None:
                final_injuries = "없음"

            final_location = arc_end.get("location") or joint.get("final_location", "?")

            if final_energy == 0:
                lines.append("  최종 내공: 해당없음(비무협)")
            else:
                lines.append(f"  최종 내공: {final_energy}% <- 다음 Arc 시작점")
            lines.append(f"  최종 부상: {final_injuries}")
            lines.append(f"  종료 위치: {final_location}")
        else:
            lines.append(f"  종료 위치: {joint.get('final_location', '?')}")

        lines.append(f"  소지품: {joint.get('physical_inventory', [])}")
        # [BUG-F] protagonist_items 우선 폴백
        lines.append(f"  획득 아이템: {state.get('protagonist_items') or state.get('items_acquired', [])}")
        lines.append(f"  수여물: {state.get('grants_received', [])}")

    return "\n".join(lines)
