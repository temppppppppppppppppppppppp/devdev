"""
[A-1] Writer 유틸리티 독립 모듈

writer.py에서 분리된 프롬프트 빌더 + 헬퍼 함수.
stage4_orchestrator._build_mandatory_context()에서 호출.
"""

from __future__ import annotations

import logging
import re


def build_mandatory_context(db, master_bible, current_ep: int) -> str:
    """[main_a.py line 6307] 강제 맥락 주입."""
    parts = ["[MANDATORY CONTEXT]\n"]

    hud_anomalies = _check_hud_anomalies(db, current_ep)
    if hud_anomalies.get("has_anomalies"):
        parts.append("\n[HUD ANOMALY WARNING]\n")
        for anomaly in hud_anomalies.get("anomalies", []):
            parts.append(f"- {anomaly['type']}: {anomaly['description']}")
            parts.append(f"  -> {anomaly['recommendation']}\n")

    recent_events = _extract_recent_events(db, current_ep, n_episodes=3)
    if recent_events:
        parts.append("\n최근 중요 사건:")
        for event in recent_events:
            parts.append(f"- 제{event['ep_num']}화: {event['description']}")
            if event.get("consequence"):
                parts.append(f"  현재 상태: {event['consequence']}")

    npc_states = _extract_npc_last_states(master_bible, current_ep)
    if npc_states:
        parts.append("\nNPC 마지막 관계 상태:")
        for npc_name, state_info in npc_states.items():
            parts.append(f"- {npc_name}: {state_info['relationship']} (제{state_info['last_ep']}화)")

    if len(parts) == 1:
        parts.append("\n(첫 에피소드이거나 강제 맥락 없음)")
    return "\n".join(parts)


def build_anti_trope_instructions(genre_name: str) -> str:
    """[main_a.py line 6354] 반클리셰 명령."""
    return f"""[ANTI-TROPE PROTOCOL - {genre_name}]
1. "약해 보이는 주인공" 클리셰 금지 - HUD 상태 직접 반영
2. "무시-사이다" 매 화 반복 금지 - 명성 증가하면 무시 감소
3. "조연 영구 생존" 금지 - 모욕/배신한 조연은 청산
4. "순간 회복" 금지 - 부상 지속 영향 또는 치료 과정 명시
5. "NPC 기억상실" 금지 - 관계는 단방향 발전
"""


def build_justification_guidance(hud_report: str, genre_name: str) -> str:
    """[main_a.py line 6360] 정당화 패턴 안내."""
    try:
        from modules.core.justification_patterns import get_justification_guide
    except ImportError:
        return ""

    active_constraints = []
    physical_constraints = ["나약", "중독", "부상", "중상", "쇠약", "기력고갈", "기혈역류"]
    if any(constraint in hud_report for constraint in physical_constraints):
        active_constraints.append("weak_body_strong_action")

    hud_report.lower()
    low_status_keywords = ["하인", "노예", "평민", "무명", "낭인", "거지", "천민"]
    _is_low_status = any(keyword in hud_report for keyword in low_status_keywords)
    rep_match = re.search(r"reputation[:\s]+(\d+)", hud_report, re.IGNORECASE)
    _is_low_rep = rep_match and int(rep_match.group(1)) < 30
    if _is_low_status or _is_low_rep:  # [TF-R2-S4-02] 독립 조건
        active_constraints.append("low_status_high_authority")

    breakthrough_keywords = ["돌파", "깨달음", "체득", "각성", "각오"]
    if any(keyword in hud_report for keyword in breakthrough_keywords):
        active_constraints.append("sudden_power_increase")

    if not active_constraints:
        return ""

    parts = ["[JUSTIFICATION PATTERNS]\n"]
    for constraint_type in active_constraints:
        try:
            parts.append(get_justification_guide(genre_name, constraint_type))
        except Exception as guide_err:
            logging.warning(
                "[Sweep5-D] justification guide load failed (constraint=%s): %s",
                constraint_type,
                guide_err,
            )
    return "\n".join(parts)


def _check_hud_anomalies(db, current_ep: int) -> dict:
    """HUD 급변 감지."""
    anomalies = []
    if current_ep < 2 or not db or not hasattr(db, "get_manuscript"):
        return {"has_anomalies": False, "anomalies": []}
    try:
        hud_history = []
        for ep in range(max(1, current_ep - 3), current_ep):
            try:
                ms_data = db.get_manuscript(ep)
                if ms_data and isinstance(ms_data, dict):
                    hud_snapshot = ms_data.get("hud_snapshot", {})
                    if hud_snapshot:
                        hud_history.append({"ep": ep, "hud": hud_snapshot})
            except Exception:
                continue
        if not hud_history:
            return {"has_anomalies": False, "anomalies": []}

        if len(hud_history) >= 2:
            latest = hud_history[-1]["hud"]
            prev_hud = hud_history[-2]["hud"]
            curr_energy = _extract_numeric_value(latest.get("internal_energy", 0))
            prev_energy = _extract_numeric_value(prev_hud.get("internal_energy", 0))
            if curr_energy - prev_energy > 500:
                anomalies.append(
                    {
                        "type": "내공 급상승",
                        "description": f"+{curr_energy - prev_energy}",
                        "recommendation": "정당화 필요",
                    }
                )

            curr_realm = latest.get("realm", "")
            prev_realm = prev_hud.get("realm", "")
            realm_tiers = ["하수", "삼류", "이류", "일류", "초일류", "절정", "화경", "현경", "귀환"]
            if curr_realm and prev_realm and curr_realm != prev_realm:
                try:
                    curr_index = realm_tiers.index(curr_realm) if curr_realm in realm_tiers else -1
                    prev_index = realm_tiers.index(prev_realm) if prev_realm in realm_tiers else -1
                    if curr_index - prev_index >= 2:
                        anomalies.append(
                            {
                                "type": "경지 급상승",
                                "description": f"{prev_realm}->{curr_realm}",
                                "recommendation": "특수 기연 정당화 필수",
                            }
                        )
                except ValueError:
                    pass

            curr_injury = str(latest.get("causal_injuries", "")).lower()
            prev_injury = str(prev_hud.get("causal_injuries", "")).lower()
            injury_levels = {
                "정상": 0,
                "경상": 1,
                "중상": 2,
                "중독": 2,
                "내상": 2,
                "빈사": 3,
                "치명상": 3,
            }
            curr_level = max((level for name, level in injury_levels.items() if name in curr_injury), default=0)
            prev_level = max((level for name, level in injury_levels.items() if name in prev_injury), default=0)
            if prev_level >= 2 and curr_level == 0:
                anomalies.append(
                    {
                        "type": "부상 급회복",
                        "description": f"{prev_injury}->{curr_injury}",
                        "recommendation": "치료 과정 필요",
                    }
                )
    except Exception:
        return {"has_anomalies": False, "anomalies": []}

    return {"has_anomalies": len(anomalies) > 0, "anomalies": anomalies}


def _extract_numeric_value(value) -> int:
    """HUD 값에서 숫자 추출."""
    if isinstance(value, int | float):
        return int(value)
    if isinstance(value, str):
        match = re.search(r"[+-]?\d+", value)
        return int(match.group()) if match else 0
    return 0


def _extract_recent_events(db, current_ep: int, n_episodes: int = 3) -> list:
    """최근 N화 핵심 사건 추출."""
    events = []
    if not db or not hasattr(db, "load_state_log"):
        return events
    try:
        for ep in range(max(1, current_ep - n_episodes), current_ep):
            log_data = db.load_state_log(ep)
            if log_data and isinstance(log_data, dict):
                summary = log_data.get("summary", "")
                if summary and len(summary) > 10:
                    events.append({"ep_num": ep, "description": summary[:200], "consequence": ""})
                data = log_data.get("data", {})
                if isinstance(data, dict):
                    for change in (data.get("major_changes", []) or [])[:2]:
                        if isinstance(change, dict):
                            events.append(
                                {
                                    "ep_num": ep,
                                    "description": change.get("event", ""),
                                    "consequence": change.get("consequence", ""),
                                }
                            )
    except Exception as events_err:
        logging.warning(
            "[Sweep5-D] recent events extraction failed (ep=%s): %s",
            current_ep,
            events_err,
        )
    return events[-5:]


def _extract_npc_last_states(master_bible: dict, current_ep: int) -> dict:
    """등장 NPC 마지막 상태."""
    npc_states = {}
    try:
        bible_root = master_bible.get("MasterBible", master_bible) if master_bible else {}
        assets = bible_root.get("AssetLibrary", {})
        key_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])
        for npc in key_npcs:
            if not isinstance(npc, dict):
                continue
            name = npc.get("name") or npc.get("Name", "")
            if not name:
                continue
            relationship = npc.get("relationship_state", "중립")
            last_appearance = npc.get("last_appearance_ep", 0)
            if isinstance(last_appearance, int) and 0 < last_appearance < current_ep:
                npc_states[name] = {"relationship": relationship, "last_ep": last_appearance}
    except Exception as npc_err:
        logging.warning(
            "[Sweep5-D] npc last-state extraction failed (ep=%s): %s",
            current_ep,
            npc_err,
        )
    return npc_states
