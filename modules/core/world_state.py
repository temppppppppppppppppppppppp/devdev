"""
[V68] WorldStateManager -- 세계 상태 문서 (World State Document)

매 화 확정 후 "현재 세계의 진실"을 ~5K자 JSON으로 유지/갱신하여,
200화에서도 전체 세계 상태를 파악할 수 있게 합니다.

DB anchor 'world_state'에 저장/로드.
LLM 호출 없이 Python만으로 state_changes 기반 자동 갱신.
"""

import json
import logging
import re

_logger = logging.getLogger(__name__)


def _build_truncation_suffix(total: int, shown: int, *, unit: str = "개") -> str:
    if total > shown:
        return f" (총 {total}{unit} 중 {shown}{unit} 표시)"
    return ""


def _normalize_known_attr_value(raw) -> str:
    if isinstance(raw, list):
        return ", ".join(str(item).strip() for item in raw if str(item).strip())
    if isinstance(raw, dict):
        if "value" in raw or "desc" in raw:
            raw = raw.get("value", raw.get("desc", raw))
        elif "public_role" in raw or "secret_role" in raw:
            public_role = str(raw.get("public_role", "") or "").strip()
            secret_role = str(raw.get("secret_role", "") or "").strip()
            known_by = _normalize_known_attr_value(raw.get("known_by") or raw.get("known_by_characters") or [])
            parts = []
            if public_role:
                parts.append(f"공개={public_role}")
            if secret_role:
                parts.append(f"비밀={secret_role}")
            if known_by:
                parts.append(f"인지={known_by}")
            return " / ".join(parts)
        else:
            return json.dumps(raw, ensure_ascii=False, sort_keys=True)
    return str(raw or "").strip()


def _normalize_pressure_vectors(raw_vectors, *, fallback_ep: int = 0) -> list[dict]:
    normalized: list[dict] = []
    seen_texts: set[str] = set()

    if not isinstance(raw_vectors, list):
        return normalized

    for raw in raw_vectors:
        if isinstance(raw, dict):
            text = str(raw.get("text") or raw.get("pressure") or raw.get("label") or "").strip()
            source = str(raw.get("source") or "").strip()
            cue_terms = raw.get("cue_terms", [])
            since_ep = raw.get("since_ep", fallback_ep)
        else:
            text = str(raw or "").strip()
            source = ""
            cue_terms = []
            since_ep = fallback_ep

        if len(text) < 2 or text in seen_texts:
            continue

        normalized_terms = []
        if isinstance(cue_terms, list):
            normalized_terms = [str(term).strip() for term in cue_terms if str(term).strip()]

        normalized.append(
            {
                "text": text[:240],
                "source": source,
                "cue_terms": normalized_terms[:5],
                "since_ep": since_ep if isinstance(since_ep, int) else fallback_ep,
            }
        )
        seen_texts.add(text)

    return normalized


class WorldStateManager:
    """[V68] 세계 상태 문서 -- 장기연재 모순 방지"""

    # 세계 상태 초기 스키마
    _INIT_STATE = {
        "version": 1,
        "last_updated_ep": 0,
        "protagonist": {
            "name": "",
            "location": "",
            "assets": "",
            "injuries": "정상",
            "skills": [],
        },
        "alive_npcs": {},  # name -> {role, relation, personality, location, first_seen_ep, role_at_intro, known_attrs}
        "dead_npcs": {},  # name -> {ep, cause}
        "relationships": {},  # npc_name -> relation_str
        "active_items": {},  # item_name -> {ep_acquired, status}
        "destroyed": [],  # [{name, type, ep, cause}]
        "active_plots": [],  # [{plot, status, since_ep}]
        "active_pressure_vectors": [],  # [{text, source, cue_terms, since_ep}]
        "world_notes": [],  # 자유형 메모 (최대 10개)
        "world_laws": [],  # [{law, established_ep}] — 세계관 절대 법칙 (장기 기억 앵커)
        "timeline": [],  # [{ep, type, description}] — 시간 마커 (경과 시간, 계절, 날짜)
        "motivations": [],  # [{text, status, since_ep, resolved_ep}] — 주인공 핵심 동기
        "promises": [],  # [{text, promiser, promisee, since_ep, status}] — 약속/서약
        "cumulative_elapsed": {"total_days": 0, "history": []},  # [LM-Tier TF-F] 누적 경과 시간
    }

    def __init__(self, db) -> None:
        """
        Args:
            db: DBManager 인스턴스
        """
        self.db = db
        self._state: dict = self._load_or_init()
        self.last_save_ok: bool | None = None
        self.last_save_error: str | None = None

    # ═══════════════════════════════════════════════════════════════
    # 로드 / 저장
    # ═══════════════════════════════════════════════════════════════

    def _load_or_init(self) -> dict:
        """DB anchor 'world_state'에서 로드, 없으면 초기화"""
        try:
            loaded = self.db.load_anchor("world_state")
            if loaded and isinstance(loaded, dict) and loaded.get("version"):
                _logger.info("[V68] WorldState: DB에서 로드 완료 (ep %d)", loaded.get("last_updated_ep", 0))
                return loaded
        except Exception as e:
            _logger.warning("[V68] WorldState: DB 로드 실패, 초기화: %s", e)

        return json.loads(json.dumps(self._INIT_STATE, ensure_ascii=False))  # deep copy

    def save(self) -> bool:
        """DB anchor 'world_state'에 저장"""
        try:
            self.db.save_anchor("world_state", self._state)
            self.last_save_ok = True
            self.last_save_error = None
            return True
        except Exception as e:
            _logger.error("[V68] WorldState: DB 저장 실패: %s", e)
            self.last_save_ok = False
            self.last_save_error = str(e)
            return False

    def _ensure_alive_npc_entry(self, npc_name: str, ep_num: int) -> dict:
        if npc_name not in self._state["alive_npcs"]:
            self._state["alive_npcs"][npc_name] = {
                "first_seen_ep": ep_num,
                "role_at_intro": "",
            }
        return self._state["alive_npcs"][npc_name]

    def _sync_known_attr(self, npc_entry: dict, field: str, value, ep_num: int, *, prev=None):
        if not isinstance(npc_entry, dict) or not field:
            return
        _ka = npc_entry.setdefault("known_attrs", {})
        _prev = _normalize_known_attr_value(_ka.get(field))
        if prev is not None:
            _prev = _normalize_known_attr_value(prev)
        _value = _normalize_known_attr_value(value)
        if not _value:
            return
        _stored_value = value if isinstance(value, (list, dict)) else _value
        _ka[field] = {
            "value": _stored_value,
            "prev": _prev,
            "changed_ep": ep_num,
        }

    def _apply_actor_and_inventory_state_changes(self, ep_num: int, state_changes: dict):
        try:
            # 1. NPC 사망 처리
            for death in state_changes.get("npc_deaths") or []:
                if isinstance(death, dict):
                    name = death.get("name", "")
                elif isinstance(death, str):
                    name = death
                else:
                    continue
                if not name:
                    _logger.warning(f"[WorldState] NPC entry missing name: {death}")
                    continue
                self._state["dead_npcs"][name] = {
                    "ep": death.get("episode", ep_num) if isinstance(death, dict) else ep_num,
                    "cause": death.get("cause", "사망") if isinstance(death, dict) else "사망",
                }
                self._state["alive_npcs"].pop(name, None)

        except Exception as e:
            _logger.error("[WorldState] §1 NPC 사망 처리 실패: %s", e)

        try:
            # 2. 스킬/무공 습득
            for skill in state_changes.get("skill_acquisitions") or []:
                if isinstance(skill, dict):
                    skill_name = skill.get("name", "")
                elif isinstance(skill, str):
                    skill_name = skill
                else:
                    continue
                if skill_name and skill_name not in self._state["protagonist"]["skills"]:
                    self._state["protagonist"]["skills"].append(skill_name)
                    _MAX_SKILLS = 50
                    skills_list = self._state["protagonist"]["skills"]
                    if len(skills_list) > _MAX_SKILLS:
                        skills_list[:] = skills_list[-_MAX_SKILLS:]

        except Exception as e:
            _logger.error("[WorldState] §2 스킬 습득 처리 실패: %s", e)

        try:
            # 3. 관계 변화
            for rel in state_changes.get("relationship_changes") or []:
                if not isinstance(rel, dict):
                    continue
                npc = rel.get("npc", "") or rel.get("target", "")
                to_rel = rel.get("to", "")
                # [IFC] Sink-side guard: scalarize dict actor refs
                if isinstance(npc, dict):
                    npc = str(npc.get("name") or npc.get("npc") or next((v for v in npc.values() if isinstance(v, str)), str(npc)))
                if isinstance(to_rel, dict):
                    to_rel = str(to_rel.get("status") or to_rel.get("value") or next((v for v in to_rel.values() if isinstance(v, str)), str(to_rel)))
                npc = str(npc).strip()
                to_rel = str(to_rel).strip()
                if npc and to_rel:
                    self._state["relationships"][npc] = to_rel
                    if npc not in self._state["dead_npcs"]:
                        npc_entry = self._ensure_alive_npc_entry(npc, ep_num)
                        npc_entry["relation"] = to_rel
                        npc_entry.setdefault("known_attrs", {})["relation_to_protag"] = {
                            "value": to_rel,
                            "prev": rel.get("from", ""),
                            "changed_ep": ep_num,
                        }

        except Exception as e:
            _logger.error("[WorldState] §3 관계 변화 처리 실패: %s", e)

        try:
            # 4. 주요 아이템
            for item in state_changes.get("major_items") or []:
                if not isinstance(item, dict):
                    continue
                item_name = item.get("name", "")
                action = item.get("action", "획득")
                if not item_name:
                    continue
                if action in ("획득", "acquire", "obtained"):
                    self._state["active_items"][item_name] = {
                        "ep_acquired": item.get("episode", ep_num),
                        "status": "보유",
                    }
                elif action in ("소실", "파괴", "소모", "lost", "consumed", "destroyed"):
                    if item_name in self._state["active_items"]:
                        self._state["active_items"][item_name]["status"] = action

        except Exception as e:
            _logger.error("[WorldState] §4 아이템 처리 실패: %s", e)

        try:
            # 4a. count-aware inventory snapshot
            inventory_counts = state_changes.get("inventory_counts") or {}
            if isinstance(inventory_counts, dict):
                for item_name, raw_count in inventory_counts.items():
                    if not item_name:
                        continue
                    try:
                        count = int(raw_count)
                    except (TypeError, ValueError):
                        continue
                    if count <= 0:
                        continue
                    entry = self._state["active_items"].setdefault(
                        item_name,
                        {
                            "ep_acquired": ep_num,
                            "status": "보유",
                        },
                    )
                    entry["status"] = "보유"
                    entry["quantity"] = count
                    entry["last_count_ep"] = ep_num

            for delta in state_changes.get("inventory_count_deltas") or []:
                if not isinstance(delta, dict):
                    continue
                item_name = str(delta.get("name", "") or "").strip()
                if not item_name:
                    continue
                entry = self._state["active_items"].setdefault(
                    item_name,
                    {
                        "ep_acquired": ep_num,
                        "status": "보유",
                    },
                )
                try:
                    to_count = int(delta.get("to", entry.get("quantity", 0)) or 0)
                except (TypeError, ValueError):
                    to_count = 0
                entry["quantity"] = to_count
                entry["last_count_ep"] = ep_num
                entry["status"] = "보유" if to_count > 0 else "소실"

        except Exception as e:
            _logger.error("[WorldState] §4a 수량 인벤토리 처리 실패: %s", e)

    def _apply_entity_and_companion_state_changes(self, ep_num: int, state_changes: dict):
        try:
            # 5. 엔티티 파괴 (조직/장소)
            _existing_destroyed_names = {
                d.get("name") for d in self._state["destroyed"] if isinstance(d, dict)
            }
            for dest in state_changes.get("entity_destructions") or []:
                if not isinstance(dest, dict):
                    continue
                _dest_name = dest.get("name", "")
                if not _dest_name or _dest_name in _existing_destroyed_names:
                    continue
                self._state["destroyed"].append(
                    {
                        "name": _dest_name,
                        "type": dest.get("type", ""),
                        "ep": dest.get("episode", ep_num),
                        "cause": dest.get("cause", ""),
                    }
                )
                _existing_destroyed_names.add(_dest_name)

        except Exception as e:
            _logger.error("[WorldState] §5 엔티티 파괴 처리 실패: %s", e)

        try:
            # 6. NPC 성격 변화
            for personality in state_changes.get("npc_personality_changes") or []:
                if not isinstance(personality, dict):
                    continue
                npc = personality.get("name", "") or personality.get("npc", "")
                if not npc or npc in self._state["dead_npcs"]:
                    continue
                npc_entry = self._ensure_alive_npc_entry(npc, ep_num)
                _traits = (
                    personality.get("traits", "")
                    or personality.get("personality_traits", "")
                    or personality.get("to", "")
                    or personality.get("personality", "")
                )
                if _traits:
                    _prev_traits = (
                        personality.get("from", "")
                        or personality.get("previous", "")
                        or npc_entry.get("personality", "")
                    )
                    npc_entry["personality"] = _traits
                    self._sync_known_attr(npc_entry, "personality", _traits, ep_num, prev=_prev_traits)
                _motivation = personality.get("motivation", "") or personality.get("primary_motivation", "")
                if _motivation:
                    npc_entry["motivation"] = _motivation

        except Exception as e:
            _logger.error("[WorldState] §6 NPC 성격 변화 처리 실패: %s", e)

        try:
            # 7. 완결 플롯
            for plot in state_changes.get("resolved_plots") or []:
                if isinstance(plot, dict):
                    plot_desc = plot.get("plot", "") or plot.get("description", "")
                elif isinstance(plot, str):
                    plot_desc = plot
                else:
                    continue
                if plot_desc:
                    self._state["active_plots"] = [
                        p for p in self._state["active_plots"] if p.get("plot", "") != plot_desc
                    ]

        except Exception as e:
            _logger.error("[WorldState] §7 완결 플롯 처리 실패: %s", e)

        try:
            # 7a. 지속 압박/위협 surface
            if "active_pressure_vectors" in state_changes:
                self._state["active_pressure_vectors"] = _normalize_pressure_vectors(
                    state_changes.get("active_pressure_vectors") or [],
                    fallback_ep=ep_num,
                )[:5]

        except Exception as e:
            _logger.error("[WorldState] §7a 지속 압박/위협 처리 실패: %s", e)

        try:
            # 8. 동행자 변화
            for comp in state_changes.get("companion_changes") or []:
                if not isinstance(comp, dict):
                    continue
                npc = comp.get("name", "")
                action = comp.get("action", "joined")
                if not npc or npc in self._state["dead_npcs"]:
                    continue
                npc_entry = self._ensure_alive_npc_entry(npc, ep_num)
                npc_entry["companion"] = action in ("join", "joined", "합류")

        except Exception as e:
            _logger.error("[WorldState] §8 동행자 변화 처리 실패: %s", e)

    def _apply_timeline_and_goal_state_changes(self, ep_num: int, state_changes: dict):
        try:
            # 12. 시간 마커 추적 (time_markers)
            for marker in state_changes.get("time_markers") or []:
                if not isinstance(marker, dict):
                    continue
                timeline = self._state.setdefault("timeline", [])
                entry = {
                    "ep": marker.get("episode", ep_num),
                    "type": marker.get("type", ""),
                    "description": marker.get("description", ""),
                }
                if not any(t["ep"] == entry["ep"] and t["type"] == entry["type"] for t in timeline):
                    timeline.append(entry)
                if len(timeline) > 20:
                    self._state["timeline"] = timeline[-20:]

                _desc = entry.get("description", "")
                _parsed_days = self._parse_elapsed_days(_desc)
                if _parsed_days and _parsed_days > 0:
                    _elapsed = self._state.setdefault("cumulative_elapsed", {"total_days": 0, "history": []})
                    _elapsed["total_days"] = _elapsed.get("total_days", 0) + _parsed_days
                    _elapsed.setdefault("history", []).append({"ep": ep_num, "days": _parsed_days, "desc": _desc[:60]})
                    if len(_elapsed["history"]) > 20:
                        _elapsed["history"] = _elapsed["history"][-20:]
                    _db_elapsed = _parsed_days
                else:
                    _db_elapsed = None

                if getattr(self, "db", None) and entry.get("description"):
                    try:
                        self.db.upsert_timeline_entry(
                            ep_no=entry["ep"],
                            story_date=entry.get("description", ""),
                            elapsed_days=_db_elapsed,
                            time_note=entry.get("description", ""),
                        )
                    except Exception as _te:
                        _logger.debug("[WorldState] timeline DB sync 실패 (비치명): %s", _te)

        except Exception as e:
            _logger.error("[WorldState] §12 시간 마커 처리 실패: %s", e)

        try:
            # 13. 주인공 동기 추적 (protagonist_motivations)
            for mot in state_changes.get("protagonist_motivations") or []:
                if not isinstance(mot, dict):
                    continue
                text = mot.get("text", "")
                if not text:
                    continue
                motivations = self._state.setdefault("motivations", [])
                existing = next((m for m in motivations if m.get("text") == text), None)
                if existing:
                    new_status = mot.get("status", "")
                    if new_status:
                        existing["status"] = new_status
                    if new_status in ("resolved", "완료") and not existing.get("resolved_ep"):
                        existing["resolved_ep"] = ep_num
                else:
                    motivations.append(
                        {
                            "text": text,
                            "status": mot.get("status", "active"),
                            "since_ep": mot.get("since_ep", ep_num),
                            "resolved_ep": mot.get("resolved_ep"),
                        }
                    )
                if len(motivations) > 20:
                    self._state["motivations"] = motivations[-20:]

        except Exception as e:
            _logger.error("[WorldState] §13 주인공 동기 처리 실패: %s", e)

        try:
            # 14. 약속/서약 추적 (commitments / promises)
            for promise in state_changes.get("commitments") or state_changes.get("promises") or []:
                if not isinstance(promise, dict):
                    continue
                text = promise.get("text", "")
                if not text:
                    continue
                promises = self._state.setdefault("promises", [])
                existing = next((p for p in promises if p.get("text") == text), None)
                if existing:
                    new_status = promise.get("status", "")
                    if new_status:
                        existing["status"] = new_status
                else:
                    promises.append(
                        {
                            "text": text,
                            "promiser": promise.get("promiser", ""),
                            "promisee": promise.get("promisee", ""),
                            "since_ep": promise.get("since_ep", ep_num),
                            "status": promise.get("status", "pending"),
                        }
                    )
                if len(promises) > 30:
                    pending = [p for p in promises if p.get("status") == "pending"]
                    others = [p for p in promises if p.get("status") != "pending"]
                    max_others = max(0, 30 - len(pending))
                    self._state["promises"] = (pending + others[-max_others:]) if max_others else pending[:30]

        except Exception as e:
            _logger.error("[WorldState] §14 약속/서약 처리 실패: %s", e)

    def _apply_physical_known_attr_state_changes(self, ep_num: int, state_changes: dict):
        try:
            # 15. [LM-I] NPC 부상 상태 → known_attrs 반영 (NpcDriftAdvisor 검사 대상)
            for entry in state_changes.get("npc_injuries") or []:
                if not isinstance(entry, dict):
                    continue
                npc = entry.get("name", "")
                state = entry.get("state", "")
                if npc and state and npc not in self._state.get("dead_npcs", {}):
                    npc_entry = self._ensure_alive_npc_entry(npc, ep_num)
                    old_injury = ""
                    known_attrs = npc_entry.get("known_attrs", {})
                    if isinstance(known_attrs.get("injury"), dict):
                        old_injury = known_attrs["injury"].get("value", "")
                    npc_entry.setdefault("known_attrs", {})["injury"] = {
                        "value": state,
                        "prev": old_injury,
                        "changed_ep": ep_num,
                    }

        except Exception as e:
            _logger.error("[WorldState] §15 NPC 부상 known_attrs 반영 실패: %s", e)

        try:
            # 16. [LM-I] NPC 이동 → known_attrs 반영 (NpcDriftAdvisor 검사 대상)
            for entry in state_changes.get("npc_movements") or []:
                if not isinstance(entry, dict):
                    continue
                npc = entry.get("name", "")
                to_loc = entry.get("to", "")
                if npc and to_loc and npc not in self._state.get("dead_npcs", {}):
                    npc_entry = self._ensure_alive_npc_entry(npc, ep_num)
                    old_loc = entry.get("from", "")
                    if not old_loc:
                        known_attrs = npc_entry.get("known_attrs", {})
                        if isinstance(known_attrs.get("location"), dict):
                            old_loc = known_attrs["location"].get("value", "")
                    npc_entry.setdefault("known_attrs", {})["location"] = {
                        "value": to_loc,
                        "prev": old_loc,
                        "changed_ep": ep_num,
                    }

        except Exception as e:
            _logger.error("[WorldState] §16 NPC 이동 known_attrs 반영 실패: %s", e)

        try:
            # 17. [LM-I] NPC 영구 부상 → known_attrs 반영 (NpcDriftAdvisor 검사 대상)
            for entry in state_changes.get("permanent_injuries") or []:
                if not isinstance(entry, dict):
                    continue
                npc = entry.get("name", "")
                desc = entry.get("description", "")
                i_type = entry.get("type", "disfigurement")
                if npc and desc and npc not in self._state.get("dead_npcs", {}):
                    npc_entry = self._ensure_alive_npc_entry(npc, ep_num)
                    known_attrs = npc_entry.setdefault("known_attrs", {})
                    existing = known_attrs.get("permanent_injuries", {})
                    old_val = existing.get("value", "") if isinstance(existing, dict) else ""
                    new_val = f"{i_type}: {desc}" if old_val else f"{i_type}: {desc}"
                    if old_val:
                        new_val = f"{old_val}, {i_type}: {desc}"
                    known_attrs["permanent_injuries"] = {
                        "value": new_val,
                        "prev": old_val,
                        "changed_ep": ep_num,
                    }

        except Exception as e:
            _logger.error("[WorldState] §17 NPC 영구 부상 known_attrs 반영 실패: %s", e)

    def _apply_npc_registry_and_law_state_changes(self, ep_num: int, state_changes: dict):
        try:
            # 9. NPC 속성 변경 — 의도적 직업/나이 등 변경 기록 (장기 기억 추적)
            for attr_change in state_changes.get("npc_attribute_changes") or []:
                if not isinstance(attr_change, dict):
                    continue
                _npc = attr_change.get("name", "")
                _field = attr_change.get("field", "")
                _raw_new_val = attr_change.get("new", "")
                _raw_old_val = attr_change.get("old", "")
                _new_val = _normalize_known_attr_value(_raw_new_val)
                _old_val = _normalize_known_attr_value(_raw_old_val)
                if not _npc or not _field or _npc in self._state["dead_npcs"]:
                    continue
                _npc_entry = self._ensure_alive_npc_entry(_npc, ep_num)
                self._sync_known_attr(_npc_entry, _field, _raw_new_val, ep_num, prev=_raw_old_val)

                if _field in {"personality", "knowledge_era", "knowledge_tags", "expertise_domain", "secrets_known"}:
                    _npc_entry[_field] = _raw_new_val
                elif _field == "dual_identity":
                    _npc_entry["dual_identity"] = _raw_new_val
                elif _field in {"public_facade", "secret_role"}:
                    _dual = _npc_entry.setdefault("dual_identity", {})
                    if isinstance(_dual, dict):
                        _dual["public_role" if _field == "public_facade" else "secret_role"] = _raw_new_val
                        self._sync_known_attr(_npc_entry, "dual_identity", _dual, ep_num)

        except Exception as e:
            _logger.error("[WorldState] §9 NPC 속성 변경 처리 실패: %s", e)

        try:
            # 10. NPC 첫 등장 초기 속성 저장 (npc_introductions)
            for intro in state_changes.get("npc_introductions") or []:
                if not isinstance(intro, dict):
                    continue
                name = intro.get("name", "")
                if not name:
                    continue
                if name in self._state.get("dead_npcs", {}):
                    logging.warning(f" [대원칙4] 사망 NPC '{name}'가 npc_introductions에 포함됨 — 무시")
                    continue
                if name not in self._state["alive_npcs"]:
                    self._state["alive_npcs"][name] = {
                        "role": intro.get("job", ""),
                        "relation": "",
                        "location": "",
                        "first_seen_ep": intro.get("episode", ep_num),
                        "role_at_intro": intro.get("job", ""),
                        "known_attrs": {},
                    }
                attrs = {k: v for k, v in intro.items() if k not in ("name", "episode")}
                _ka = self._state["alive_npcs"][name].setdefault("known_attrs", {})
                _ka.update(attrs)
                _npc_entry = self._state["alive_npcs"][name]
                _pos = intro.get("position", "") or intro.get("job", "")
                if _pos:
                    _ka["position"] = {
                        "value": _pos,
                        "prev": "",
                        "changed_ep": intro.get("episode", ep_num),
                    }
                if intro.get("personality"):
                    _npc_entry["personality"] = intro.get("personality", "")
                    self._sync_known_attr(_npc_entry, "personality", intro.get("personality", ""), ep_num)
                for _field in ("knowledge_era", "knowledge_tags", "expertise_domain", "secrets_known"):
                    if intro.get(_field):
                        _npc_entry[_field] = intro.get(_field)
                        self._sync_known_attr(_npc_entry, _field, intro.get(_field), ep_num)
                _dual_identity = intro.get("dual_identity")
                if _dual_identity:
                    _npc_entry["dual_identity"] = _dual_identity
                    self._sync_known_attr(_npc_entry, "dual_identity", _dual_identity, ep_num)
                else:
                    _public = intro.get("public_facade")
                    _secret = intro.get("secret_role")
                    if _public or _secret:
                        _dual = {
                            "public_role": _public,
                            "secret_role": _secret,
                            "known_by": intro.get("known_by") or intro.get("known_by_characters") or [],
                        }
                        _npc_entry["dual_identity"] = _dual
                        self._sync_known_attr(_npc_entry, "dual_identity", _dual, ep_num)

        except Exception as e:
            _logger.error("[WorldState] §10 NPC 초기 속성 처리 실패: %s", e)

        try:
            # 11. 세계관 법칙 등록
            for law_entry in state_changes.get("world_law_additions") or []:
                if isinstance(law_entry, str) and law_entry.strip():
                    self._add_world_law_internal(law_entry.strip(), ep_num)
                elif isinstance(law_entry, dict):
                    _law_text = law_entry.get("law", "")
                    if _law_text:
                        self._add_world_law_internal(_law_text, ep_num)

        except Exception as e:
            _logger.error("[WorldState] §11 세계관 법칙 처리 실패: %s", e)

    # ═══════════════════════════════════════════════════════════════
    # state_changes 기반 자동 갱신
    # ═══════════════════════════════════════════════════════════════

    def update_from_state_changes(self, ep_num: int, state_changes: dict, *, source: str = "episode"):
        """
        state_changes에서 자동 갱신 -- Python만으로.

        Args:
            ep_num: 에피소드 번호
            state_changes: 상태 변경 dict
            source: "episode" (기본) 또는 "arc" (아크 단위 갱신 시)

        state_changes 스키마:
            npc_deaths, skill_acquisitions, relationship_changes,
            major_items, entity_destructions, npc_personality_changes,
            resolved_plots, companion_changes 등
        """
        if not state_changes or not isinstance(state_changes, dict):
            return

        if source == "arc":
            self._state["last_updated_ep"] = ep_num
            self._state["last_updated_source"] = "arc"
        else:
            self._state["last_updated_ep"] = ep_num

        # [TF-36] 섹션별 try/except — 1개 섹션 실패 시 나머지 섹션 처리 보장
        self._apply_actor_and_inventory_state_changes(ep_num, state_changes)
        self._apply_entity_and_companion_state_changes(ep_num, state_changes)

        self._apply_npc_registry_and_law_state_changes(ep_num, state_changes)
        self._apply_timeline_and_goal_state_changes(ep_num, state_changes)
        self._apply_physical_known_attr_state_changes(ep_num, state_changes)

        # 크기 제한: destroyed 최대 100개, world_notes 최대 10개 (항상 실행)
        try:
            if len(self._state["destroyed"]) > 100:
                self._state["destroyed"] = self._state["destroyed"][-100:]
            if len(self._state.get("active_pressure_vectors", [])) > 5:
                self._state["active_pressure_vectors"] = self._state["active_pressure_vectors"][:5]
            if len(self._state.get("world_notes", [])) > 10:
                self._state["world_notes"] = self._state["world_notes"][-10:]
        except Exception as e:
            _logger.error("[WorldState] 크기 제한 처리 실패: %s", e)

    # ═══════════════════════════════════════════════════════════════
    # 주인공 상태 갱신
    # ═══════════════════════════════════════════════════════════════

    def update_protagonist_state(
        self, ep_num: int, name: str = None, location: str = None, assets: str = None, injuries: str = None
    ):
        """주인공 상태 갱신"""
        try:
            if name:
                self._state["protagonist"]["name"] = name
            if location:
                self._state["protagonist"]["location"] = location
            if assets:
                self._state["protagonist"]["assets"] = assets
            if injuries:
                self._state["protagonist"]["injuries"] = injuries
            self._state["last_updated_ep"] = ep_num
        except Exception as e:
            _logger.error("[V68] WorldState: update_protagonist_state 실패: %s", e)

    # ═══════════════════════════════════════════════════════════════
    # 프롬프트 주입용 요약 생성
    # ═══════════════════════════════════════════════════════════════

    def get_canonical_constraints(self, max_chars: int = 8000) -> str:
        """[Phase1-L0] NPC 고정 속성(role_at_intro + known_attrs) 압축 요약.

        get_summary()에 없는 정보(최초 역할·초기 속성)만 담당.
        세계관 법칙은 get_summary()에 이미 포함되므로 제외.
        """
        try:
            parts = ["[캐릭터 고정 속성 (L0)]"]
            alive = self._state.get("alive_npcs", {})
            for name, data in list(alive.items())[:20]:
                if not isinstance(data, dict):
                    continue
                role_at_intro = data.get("role_at_intro", "")
                first_ep = data.get("first_seen_ep", "?")
                known = data.get("known_attrs", {})
                attr_parts = []
                for k, v in list((known or {}).items())[:5]:
                    val = v.get("value", v) if isinstance(v, dict) else v
                    attr_parts.append(f"{k}={val}")
                attr_str = ", ".join(attr_parts)
                line = f"- {name}: {role_at_intro} (EP{first_ep}~)"
                if attr_str:
                    line += f" / {attr_str}"
                parts.append(line)
            # [Graph-Layer] NPC 간 관계 섹션
            if getattr(self, "db", None):
                try:
                    edges = self.db.get_npc_relationship_edges()[:20]
                    if edges:
                        parts.append("\n[NPC 간 관계 (L0-Graph)]")
                        for e in edges:
                            parts.append(
                                f"- {e['npc1']} ↔ {e['npc2']}: {e.get('relation', '?')} (Arc {e.get('arc_no', '?')})"
                            )
                except Exception as _ge:
                    _logger.debug("[WorldState] npc_relationship_edges 조회 실패: %s", _ge)
            result = "\n".join(parts)
            if len(result) > max_chars:
                result = result[: max_chars - 10] + "\n...(절삭)"
            return result if len(parts) > 1 else ""
        except Exception as e:
            _logger.warning("[WorldState] get_canonical_constraints 실패 (비치명): %s", e)
            return ""

    def get_timeline_summary(self, max_entries: int = 30, max_chars: int = 3000) -> str:
        """[Phase3-Timeline] DB에서 타임라인 조회 (20개 제한 없음).

        DB 없을 때 in-memory fallback 사용.
        """
        try:
            if getattr(self, "db", None):
                entries = self.db.get_timeline_range(limit=max_entries)
                if entries:
                    lines = ["[작중 타임라인]"]
                    for e in entries:
                        note = e.get("time_note") or e.get("story_date") or ""
                        lines.append(f"- EP{e['ep_no']}: {note}")
                    result = "\n".join(lines)
                    return result[:max_chars]
            # fallback: in-memory timeline
            timeline = self._state.get("timeline") or []
            if not timeline:
                return ""
            recent = timeline[-max_entries:]
            lines = ["[작중 타임라인]"]
            for e in recent:
                if isinstance(e, dict):
                    ep = e.get("ep", "?")
                    desc = e.get("description", "")
                    lines.append(f"- EP{ep}: {desc}")
            result = "\n".join(lines)
            return result[:max_chars] if len(lines) > 1 else ""
        except Exception as e:
            _logger.warning("[WorldState] get_timeline_summary 실패 (비치명): %s", e)
            return ""

    def _build_summary_protagonist_sections(self) -> list[str]:
        parts = []
        prot = self._state.get("protagonist", {})
        prot_lines = []
        if prot.get("name"):
            prot_lines.append(f"이름: {prot['name']}")
        if prot.get("location"):
            prot_lines.append(f"위치: {prot['location']}")
        if prot.get("assets"):
            prot_lines.append(f"자산: {prot['assets']}")
        if prot.get("injuries") and prot["injuries"] != "정상":
            prot_lines.append(f"부상: {prot['injuries']}")
        if prot.get("skills"):
            prot_lines.append(f"습득 무공/스킬: {', '.join(prot['skills'][-20:])}")
        if prot_lines:
            parts.append("[주인공]\n" + "\n".join(prot_lines))

        motivations = [
            mot
            for mot in (self._state.get("motivations") or [])
            if isinstance(mot, dict) and mot.get("status") == "active" and mot.get("text")
        ]
        if motivations:
            mot_lines = []
            for mot in motivations[:10]:
                since_ep = mot.get("since_ep")
                text = str(mot.get("text", "") or "").strip()
                if text:
                    mot_lines.append(f"- {text}" + (f" (제{since_ep}화~)" if since_ep else ""))
            if mot_lines:
                parts.append("[주인공 핵심 동기]\n" + "\n".join(mot_lines))

        promises = [
            promise
            for promise in (self._state.get("promises") or [])
            if isinstance(promise, dict)
            and promise.get("text")
            and promise.get("status") in ("pending", None, "")
        ]
        if promises:
            promise_lines = []
            for promise in promises[:10]:
                promiser = str(promise.get("promiser", "") or "").strip()
                promisee = str(promise.get("promisee", "") or "").strip()
                parties = "→".join(x for x in [promiser, promisee] if x)
                label = str(promise.get("text", "") or "").strip()
                if not label:
                    continue
                since_ep = promise.get("since_ep")
                if parties:
                    label = f"{parties}: {label}"
                promise_lines.append(f"- {label}" + (f" (제{since_ep}화~)" if since_ep else ""))
            if promise_lines:
                parts.append("[서약/약속]\n" + "\n".join(promise_lines))

        cumulative_elapsed = self._state.get("cumulative_elapsed", {})
        if isinstance(cumulative_elapsed, dict):
            total_days = cumulative_elapsed.get("total_days", 0)
            if total_days:
                parts.append(f"[누적 경과] 총 {total_days}일")
        return parts

    def _npc_importance(self, item) -> int:
        _name, info = item
        if not isinstance(info, dict):
            return 0
        score = 0
        if info.get("companion"):
            score += 3
        if info.get("relation"):
            score += 2
        if info.get("role"):
            score += 1
        return score

    def _build_summary_npc_sections(self) -> list[str]:
        parts = []
        alive = self._state.get("alive_npcs", {})
        if alive:
            npc_lines = []
            sorted_alive = sorted(alive.items(), key=self._npc_importance, reverse=True)
            for name, info in sorted_alive[:30]:
                desc_parts = []
                if isinstance(info, dict):
                    if info.get("role"):
                        desc_parts.append(info["role"])
                    if info.get("relation"):
                        desc_parts.append(f"관계={info['relation']}")
                    if info.get("personality"):
                        desc_parts.append(info["personality"][:30])
                    if info.get("location"):
                        desc_parts.append(f"위치={info['location']}")
                    if info.get("knowledge_era"):
                        desc_parts.append(f"지식시대={_normalize_known_attr_value(info.get('knowledge_era'))}")
                    if info.get("expertise_domain"):
                        desc_parts.append(f"전문영역={_normalize_known_attr_value(info.get('expertise_domain'))}")
                    known_attrs = info.get("known_attrs", {})
                    if isinstance(known_attrs, dict):
                        known_parts = []
                        personality = _normalize_known_attr_value(known_attrs.get("personality"))
                        if personality:
                            known_parts.append(f"성격기록={personality}")
                        injury = _normalize_known_attr_value(known_attrs.get("injury"))
                        if injury:
                            known_parts.append(f"부상={injury}")
                        known_loc = _normalize_known_attr_value(known_attrs.get("location"))
                        if known_loc:
                            known_parts.append(f"위치기록={known_loc}")
                        permanent = _normalize_known_attr_value(known_attrs.get("permanent_injuries"))
                        if permanent:
                            known_parts.append(f"영구부상={permanent}")
                        knowledge_tags = _normalize_known_attr_value(known_attrs.get("knowledge_tags"))
                        if knowledge_tags:
                            known_parts.append(f"지식태그={knowledge_tags}")
                        secrets_known = _normalize_known_attr_value(known_attrs.get("secrets_known"))
                        if secrets_known:
                            known_parts.append(f"비밀인지={secrets_known}")
                        dual_identity = _normalize_known_attr_value(known_attrs.get("dual_identity"))
                        if dual_identity:
                            known_parts.append(f"이중정체={dual_identity}")
                        if known_parts:
                            desc_parts.append(", ".join(known_parts))
                    if info.get("companion"):
                        desc_parts.append("(동행중)")
                desc = " / ".join(desc_parts) if desc_parts else ""
                npc_lines.append(f"- {name}" + (f": {desc}" if desc else ""))
            shown_alive = len(sorted_alive[:30])
            alive_suffix = _build_truncation_suffix(len(alive), shown_alive, unit="명")
            parts.append(f"[생존 NPC ({shown_alive}명){alive_suffix}]\n" + "\n".join(npc_lines))

        dead = self._state.get("dead_npcs", {})
        if dead:
            dead_lines = []
            shown_dead_rows = list(dead.items())[:20]
            for name, info in shown_dead_rows:
                if isinstance(info, dict):
                    dead_lines.append(f"- {name} (제{info.get('ep', 'unknown')}화, {info.get('cause', '')})")
                else:
                    dead_lines.append(f"- {name}")
            dead_suffix = _build_truncation_suffix(len(dead), len(shown_dead_rows), unit="명")
            parts.append(f"[사망 NPC ({len(shown_dead_rows)}명){dead_suffix} -- 절대 등장 금지]\n" + "\n".join(dead_lines))
        return parts

    def _build_summary_relation_and_inventory_sections(self) -> list[str]:
        parts = []
        rels = self._state.get("relationships", {})
        if rels:
            shown_rels = list(rels.items())[:20]
            rel_lines = [f"- {npc}: {rel}" for npc, rel in shown_rels]
            rel_suffix = _build_truncation_suffix(len(rels), len(shown_rels))
            parts.append(f"[주요 관계{rel_suffix}]\n" + "\n".join(rel_lines))

        items = self._state.get("active_items", {})
        active_items = {k: v for k, v in items.items() if isinstance(v, dict) and v.get("status", "보유") == "보유"}
        if active_items:
            shown_items = list(active_items.keys())[:20]
            item_lines = []
            for name in shown_items:
                info = active_items.get(name, {})
                qty = info.get("quantity") if isinstance(info, dict) else None
                qty_suffix = f" x{qty}" if isinstance(qty, int) and qty > 1 else ""
                item_lines.append(f"- {name}{qty_suffix}")
            item_suffix = _build_truncation_suffix(len(active_items), len(shown_items))
            parts.append(f"[보유 아이템{item_suffix}]\n" + "\n".join(item_lines))
        return parts

    def _build_summary_world_tail_sections(self) -> list[str]:
        parts = []
        destroyed = self._state.get("destroyed", [])
        if destroyed:
            shown_destroyed = destroyed[-10:]
            dest_lines = [
                f"- {entry.get('name', 'unknown')} ({entry.get('type', 'unknown')}, 제{entry.get('ep', 'unknown')}화)"
                for entry in shown_destroyed
            ]
            destroyed_suffix = _build_truncation_suffix(len(destroyed), len(shown_destroyed))
            parts.append(f"[파괴된 장소/조직{destroyed_suffix} -- 복구 불가]\n" + "\n".join(dest_lines))

        plots = self._state.get("active_plots", [])
        if plots:
            shown_plots = plots[-10:]
            plot_lines = [f"- {entry.get('plot', 'unknown')} (제{entry.get('since_ep', 'unknown')}화~)" for entry in shown_plots]
            plot_suffix = _build_truncation_suffix(len(plots), len(shown_plots))
            parts.append(f"[진행 중 플롯{plot_suffix}]\n" + "\n".join(plot_lines))

        pressure_vectors = self._state.get("active_pressure_vectors", [])
        if pressure_vectors:
            shown_vectors = pressure_vectors[:5]
            pressure_lines = []
            for vector in shown_vectors:
                text = str(vector.get("text", "") or "").strip() if isinstance(vector, dict) else str(vector or "").strip()
                if text:
                    pressure_lines.append(f"- {text}")
            if pressure_lines:
                pressure_suffix = _build_truncation_suffix(len(pressure_vectors), len(shown_vectors))
                parts.append(f"[지속 압박/위협{pressure_suffix}]\n" + "\n".join(pressure_lines))

        world_laws = self._state.get("world_laws", [])
        if world_laws:
            law_lines = [
                f"- {entry.get('law', '')} (제{entry.get('established_ep', 'unknown')}화 확립)"
                for entry in world_laws
                if isinstance(entry, dict) and entry.get("law")
            ]
            if law_lines:
                parts.append("[세계관 절대 법칙 -- 위반 금지]\n" + "\n".join(law_lines))

        timeline = self._state.get("timeline") or []
        if timeline:
            recent = timeline[-5:]
            t_lines = [f"- EP{entry['ep']}: {entry['description']}" for entry in recent if entry.get("description")]
            if t_lines:
                timeline_suffix = _build_truncation_suffix(len(timeline), len(recent))
                parts.append(f"[시간 흐름 (최근){timeline_suffix}]\n" + "\n".join(t_lines))
        return parts

    def get_summary(self, max_chars: int = 50000) -> str:  # [1M-CTX-P1: 25K→50K] ep250 NPC 150명 전량 수용
        """
        프롬프트 주입용 요약 텍스트 생성.
        max_chars 이내로 truncation.
        """
        try:
            parts = []
            last_ep = self._state.get("last_updated_ep", 0)
            if last_ep == 0:
                return ""

            parts.append(f"=== 세계 상태 (제{last_ep}화 기준) ===")
            parts.extend(self._build_summary_protagonist_sections())
            parts.extend(self._build_summary_npc_sections())
            parts.extend(self._build_summary_relation_and_inventory_sections())
            parts.extend(self._build_summary_world_tail_sections())

            result = "\n\n".join(parts)

            if len(result) > max_chars:
                result = result[: max_chars - 50] + "\n\n...(세계 상태 요약 일부 생략)"

            return result

        except Exception as e:
            _logger.error("[V68] WorldState: get_summary 실패: %s", e)
            return ""

    # ═══════════════════════════════════════════════════════════════
    # 유틸리티
    # ═══════════════════════════════════════════════════════════════

    @property
    def last_updated_ep(self) -> int:
        """마지막 갱신된 에피소드 번호"""
        return self._state.get("last_updated_ep", 0)

    def register_alive_npc(self, name: str, role: str = "", relation: str = "", location: str = "", first_ep: int = 0):
        """NPC를 생존 목록에 수동 등록"""
        if name in self._state.get("dead_npcs", {}):
            return  # 이미 죽은 NPC는 등록 불가
        if name not in self._state["alive_npcs"]:
            self._state["alive_npcs"][name] = {
                "first_seen_ep": first_ep or 0,
                "role_at_intro": role,  # 최초 등장 역할 — 이후 변경 안 함
            }
        if role:
            self._state["alive_npcs"][name]["role"] = role
            # role_at_intro는 최초 1회만 설정
            if not self._state["alive_npcs"][name].get("role_at_intro"):
                self._state["alive_npcs"][name]["role_at_intro"] = role
        if relation:
            self._state["alive_npcs"][name]["relation"] = relation
        if location:
            self._state["alive_npcs"][name]["location"] = location

    def add_active_plot(self, plot: str, since_ep: int):
        """진행 중 플롯 추가"""
        # 중복 방지
        for p in self._state.get("active_plots", []):
            if p.get("plot") == plot:
                return
        self._state["active_plots"].append(
            {
                "plot": plot,
                "status": "active",
                "since_ep": since_ep,
            }
        )
        _MAX_ACTIVE_PLOTS = 100
        active_plots = self._state["active_plots"]
        if len(active_plots) > _MAX_ACTIVE_PLOTS:
            active_plots[:] = active_plots[-_MAX_ACTIVE_PLOTS:]

    def get_state_dict(self) -> dict:
        """내부 상태 dict 반환 (디버깅/대시보드용) — deep copy로 외부 변조 방지"""
        return json.loads(json.dumps(self._state, ensure_ascii=False))

    # ═══════════════════════════════════════════════════════════════
    # TruthGate 접근자 (D-1) — 4개 검사 활성화
    # ═══════════════════════════════════════════════════════════════

    def get_deceased_npcs(self) -> list[str]:
        """사망 NPC 이름 목록 반환 (TruthGate deceased_npc 검사용)"""
        return list(self._state.get("dead_npcs", {}).keys())

    def get_owned_items(self) -> list[str]:
        """현재 보유 중인 아이템 이름 목록 반환 (TruthGate item_existence 검사용)"""
        items = self._state.get("active_items", {})
        return [name for name, info in items.items() if isinstance(info, dict) and info.get("status", "보유") == "보유"]

    def get_destroyed_locations(self) -> list[str]:
        """파괴된 장소/조직 이름 목록 반환 (TruthGate location_existence 검사용)"""
        return [d.get("name", "") for d in self._state.get("destroyed", []) if isinstance(d, dict) and d.get("name")]

    def get_known_skills(self) -> list[str]:
        """주인공이 습득한 스킬/무공 목록 반환 (TruthGate skill_existence 검사용)"""
        return list(self._state.get("protagonist", {}).get("skills", []))

    # ═══════════════════════════════════════════════════════════════
    # 장기 기억 앵커 (60화+ 모순 방지)
    # ═══════════════════════════════════════════════════════════════

    def _add_world_law_internal(self, law: str, ep: int, priority: str = "NORMAL") -> None:
        """내부용: world_laws에 중복 없이 추가"""
        laws = self._state.setdefault("world_laws", [])
        existing = {e.get("law", "") for e in laws if isinstance(e, dict)}
        if law not in existing:
            laws.append({"law": law, "established_ep": ep, "priority": priority})
            if len(laws) > 50:
                # [LM-A-3] CRITICAL 핀 보호: CRITICAL 법칙은 FIFO 탈락 대상에서 제외
                critical = [e for e in laws if e.get("priority") == "CRITICAL"]
                others = [e for e in laws if e.get("priority") != "CRITICAL"]
                max_others = max(0, 50 - len(critical))
                laws[:] = critical + others[-max_others:] if max_others else critical[:50]

    def add_world_law(self, law: str, ep: int = 0, priority: str = "NORMAL") -> None:
        """세계관 절대 법칙 등록 (Stage 0 Bible 파싱 또는 수동 등록용)."""
        if law and law.strip():
            self._add_world_law_internal(law.strip(), ep, priority)

    def get_world_laws(self) -> list[str]:
        """세계관 절대 법칙 텍스트 목록 반환 (TruthGate 검사용)."""
        return [e.get("law", "") for e in self._state.get("world_laws", []) if isinstance(e, dict) and e.get("law")]

    def get_npc_role_snapshot(self) -> dict:
        """NPC 원본 역할 스냅샷 반환 (TruthGate role 일관성 검사용).

        Returns:
            {npc_name: {"role_at_intro": str, "first_seen_ep": int, "known_attrs": dict}}
        """
        result = {}
        for name, info in self._state.get("alive_npcs", {}).items():
            if not isinstance(info, dict):
                continue
            role_at_intro = info.get("role_at_intro", "")
            known_attrs = info.get("known_attrs", {})
            if role_at_intro or known_attrs:
                result[name] = {
                    "role_at_intro": role_at_intro,
                    "first_seen_ep": info.get("first_seen_ep", 0),
                    "known_attrs": known_attrs,
                }
        return result

    def get_long_term_anchor(self, current_ep: int = 0) -> str:
        """60화+ 장기 기억 앵커 텍스트 생성.

        세계관 법칙 + NPC 원본 역할을 별도 섹션으로 반환.
        Stage4ContextBuilder에서 prev_manuscripts_text 앞에 주입.
        """
        parts = []

        # 세계관 절대 법칙
        laws = self.get_world_laws()
        if laws:
            law_lines = [f"- {law}" for law in laws]
            parts.append("【세계관 절대 법칙 — 위반 즉시 REJECT】\n" + "\n".join(law_lines))

        # NPC 원본 역할 (role_at_intro가 있는 NPC만)
        npc_snap = self.get_npc_role_snapshot()
        if npc_snap:
            npc_lines = []
            for name, snap in sorted(npc_snap.items()):
                role_at_intro = snap.get("role_at_intro", "")
                first_ep = snap.get("first_seen_ep", 0)
                known_attrs = snap.get("known_attrs", {})
                parts_npc = []
                if role_at_intro:
                    parts_npc.append(f"최초 역할={role_at_intro}")
                if first_ep:
                    parts_npc.append(f"첫 등장={first_ep}화")
                for field, attr in (known_attrs or {}).items():
                    val = attr.get("value", "") if isinstance(attr, dict) else str(attr)
                    chg_ep = attr.get("changed_ep", 0) if isinstance(attr, dict) else 0
                    if val:
                        parts_npc.append(f"{field}={val}({chg_ep}화 갱신)")
                if parts_npc:
                    npc_lines.append(f"- {name}: {' / '.join(parts_npc)}")
            if npc_lines:
                parts.append("【NPC 원본 속성 — 변경 시 작중 이유 필수】\n" + "\n".join(npc_lines))

        if not parts:
            return ""
        header = f"=== [장기 설정 앵커: 제{current_ep}화 기준 불변 사실] ==="
        return header + "\n\n" + "\n\n".join(parts)

    def rollback_to(self, target_ep: int) -> None:
        """[D-2] 특정 에피소드 이전 상태로 롤백 (episode_bibles 리플레이).

        [INF-P1-9] 최적화: 개별 get_episode_bible(ep) N회 호출 대신
        get_all_episode_bibles()로 한 번에 로드 후 필터링하여 O(1) DB 호출.
        """
        _logger.warning(
            "[D-2] WorldState 롤백: ep %d 이전으로 복원 (이전 last_updated_ep=%d)",
            target_ep,
            self._state.get("last_updated_ep", 0),
        )
        self._state = json.loads(json.dumps(self._INIT_STATE, ensure_ascii=False))
        # [INF-P1-9] 일괄 로드 후 target_ep 미만만 리플레이
        try:
            all_bibles = self.db.get_all_episode_bibles()
        except Exception as e:
            _logger.warning("[D-2] WorldState 일괄 로드 실패, 개별 조회 폴백: %s", e)
            all_bibles = None

        if all_bibles is not None:
            for bible in all_bibles:
                ep = bible.get("ep_num", 0)
                if ep >= target_ep:
                    break  # ep_num 순 정렬이므로 즉시 중단
                try:
                    sc = bible.get("state_changes", {})
                    if sc:
                        self.update_from_state_changes(ep, sc)
                except Exception as e:
                    _logger.warning("[D-2] WorldState 리플레이 실패 ep %d: %s", ep, e)
        else:
            # 폴백: 개별 조회 (기존 동작)
            for ep in range(1, target_ep):
                try:
                    bible = self.db.get_episode_bible(ep)
                    if bible:
                        sc = bible.get("state_changes", {})
                        if sc:
                            self.update_from_state_changes(ep, sc)
                except Exception as e:
                    _logger.warning("[D-2] WorldState 리플레이 실패 ep %d: %s", ep, e)
        self.save()

    # --- [LM-Tier TF-F] 누적 경과 시간 ---

    @staticmethod
    def _parse_elapsed_days(text: str) -> int | None:
        """한국어 시간 표현 → 일수 변환. 실패 시 None."""
        if not text:
            return None
        text = text.strip()
        # 숫자+단위: "3일", "2주", "3개월"
        m = re.search(r"(\d+)\s*(일|주|개월|달|년)", text)
        if m:
            n, unit = int(m.group(1)), m.group(2)
            return {"일": 1, "주": 7, "개월": 30, "달": 30, "년": 365}.get(unit, 1) * n
        # 한국어 수사
        korean_nums = {"하루": 1, "이틀": 2, "사흘": 3, "나흘": 4, "닷새": 5, "엿새": 6, "이레": 7}
        for k, v in korean_nums.items():
            if k in text:
                return v
        # 복합 표현
        compounds = {
            "일주일": 7, "보름": 15, "한 달": 30, "한달": 30, "반년": 180,
            "반나절": 1, "수일": 3, "며칠": 3, "몇 주": 14, "몇주": 14,
        }
        for k, v in compounds.items():
            if k in text:
                return v
        return None

    def get_cumulative_elapsed(self) -> dict:
        """누적 경과 시간 조회. {"total_days": int, "history": [{"ep", "days", "desc"}]}"""
        import copy

        _raw = self._state.get("cumulative_elapsed", {"total_days": 0, "history": []})
        return copy.deepcopy(_raw)
