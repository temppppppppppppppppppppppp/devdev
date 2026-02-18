"""
[V68] 누적 팩트 원장 (Cumulative Fact Ledger)
— 장기연재 모순 방지의 핵심

매 화 확정 후 state_changes에서 자동으로 사실을 추출/갱신하여,
200화에서도 1화의 사실(증권사명, 가격, 캐릭터 고향 등)을 즉시 조회 가능하게 합니다.

DB anchor 'fact_ledger'에 저장/로드.
LLM 호출 없이 Python만으로 state_changes 기반 자동 갱신 — 비용 0.
"""

import logging

_logger = logging.getLogger(__name__)


class FactLedger:
    """[V68] 누적 팩트 원장 — 장기연재 모순 방지의 핵심"""

    MAX_HISTORY_PER_ENTITY = 10  # 엔티티당 이력 최대 수
    MAX_SUMMARY_CHARS = 20000  # 프롬프트 주입 시 최대 크기

    # ═══════════════════════════════════════════════════════════════
    # 초기화 / 로드 / 저장
    # ═══════════════════════════════════════════════════════════════

    def __init__(self, db) -> None:
        """
        Args:
            db: DBManager 인스턴스 (save_anchor / load_anchor 지원)
        """
        self.db = db
        self._ledger: dict = self._load()

    def _load(self) -> dict:
        """DB anchor에서 팩트 원장 로드. 없으면 빈 스키마 반환."""
        try:  # [V70] DB 오류 시 비차단 (WorldStateManager._load_or_init 패턴)
            raw = self.db.load_anchor("fact_ledger")
            if raw and isinstance(raw, dict):
                # 스키마 보강: 누락된 키가 있으면 추가 (마이그레이션)
                defaults = self._empty_ledger()
                for key, default_val in defaults.items():
                    if key not in raw:
                        raw[key] = default_val
                return raw
        except Exception as e:
            _logger.warning(f"⚠️ [V70] FactLedger DB 로드 실패, 초기화: {e}")
        return self._empty_ledger()

    @staticmethod
    def _empty_ledger() -> dict:
        """빈 팩트 원장 스키마"""
        return {
            "characters": {},  # {name: {status, role, relationship, established_ep, last_ep, history[]}}
            "numbers": {},  # {key: {value, unit, last_ep, history[]}}
            "items": {},  # {name: {owner, status, established_ep, last_ep, history[]}}
            "locations": {},  # {name: {status, current_owner, last_ep, history[]}}
            "organizations": {},  # {name: {status, leader, last_ep, history[]}}
            "last_updated_ep": 0,
        }

    def save(self) -> None:
        """팩트 원장을 DB anchor에 저장."""
        try:
            self.db.save_anchor("fact_ledger", self._ledger)
        except Exception as e:
            _logger.warning(f"[V68] 팩트 원장 저장 실패: {e}")

    @property
    def last_updated_ep(self) -> int:
        return self._ledger.get("last_updated_ep", 0)

    # ═══════════════════════════════════════════════════════════════
    # state_changes 기반 자동 갱신
    # ═══════════════════════════════════════════════════════════════

    def update_from_state_changes(self, ep_num: int, state_changes: dict):
        """
        state_changes에서 자동 갱신 — Python만으로, LLM 불필요.

        Args:
            ep_num: 에피소드 번호
            state_changes: Arc의 state_changes dict
                (npc_deaths, skill_acquisitions, relationship_changes,
                 major_items, entity_destructions, npc_injuries,
                 npc_movements, npc_personality_changes, npc_npc_relationships 등)
        """
        if not state_changes or not isinstance(state_changes, dict):
            return

        # npc_deaths — [Sweep54] WorldState와 동일하게 str/dict 모두 처리
        for death in state_changes.get("npc_deaths") or []:  # [V70] None 방어
            if isinstance(death, dict):
                name = death.get("name", "")
            elif isinstance(death, str):
                name = death
            else:
                continue
            if not name:
                _logger.warning(f"[FactLedger] NPC death entry missing name: {death}")
                continue
            cause = death.get("cause", "불명") if isinstance(death, dict) else "사망"
            self._upsert_character(name, ep_num, status="dead", note=f"사망 (원인: {cause})")

        # relationship_changes
        for rel in state_changes.get("relationship_changes") or []:  # [V70] None 방어
            if not isinstance(rel, dict):
                continue
            npc = rel.get("npc", "")
            if npc:
                self._upsert_character(
                    npc,
                    ep_num,
                    relationship=rel.get("to", ""),
                    note=f"관계 변화: {rel.get('from', '?')} -> {rel.get('to', '?')}",
                )

        # skill_acquisitions — [Sweep55] WorldState와 동일하게 str/dict 모두 처리
        for skill in state_changes.get("skill_acquisitions") or []:  # [V70] None 방어
            if isinstance(skill, dict):
                name = skill.get("name", "")
                source = skill.get("source", "불명")
            elif isinstance(skill, str):
                name = skill
                source = "불명"
            else:
                continue
            if name:
                self._upsert_item(name, ep_num, owner="주인공", status="습득", note=f"습득 (출처: {source})")

        # major_items
        for item in state_changes.get("major_items") or []:  # [V70] None 방어
            if isinstance(item, dict):
                iname = item.get("name", "")
                action = item.get("action", "획득")
            elif isinstance(item, str):
                iname = item
                action = "획득"
            else:
                continue
            if iname:
                self._upsert_item(iname, ep_num, owner="주인공", status=action, note=f"{action}")

        # entity_destructions
        for dest in state_changes.get("entity_destructions") or []:  # [V70] None 방어
            if not isinstance(dest, dict):
                continue
            name = dest.get("name", "")
            dtype = dest.get("type", "unknown")
            if name:
                if dtype == "organization":
                    self._upsert_org(name, ep_num, status="destroyed", note=f"파괴 (원인: {dest.get('cause', '불명')})")
                else:
                    self._upsert_location(
                        name, ep_num, status="destroyed", note=f"파괴 (원인: {dest.get('cause', '불명')})"
                    )

        # npc_injuries
        for injury in state_changes.get("npc_injuries") or []:  # [V70] None 방어
            if not isinstance(injury, dict):
                continue
            name = injury.get("name", "") or injury.get("npc", "")
            if name:
                # [Sweep55] LLM 스키마는 "state" 키 사용 (경상/중상/위독)
                injury_type = injury.get("state", "") or injury.get("type", "") or injury.get("injury", "")
                self._upsert_character(name, ep_num, note=f"부상: {injury_type}" if injury_type else "부상")

        # npc_movements
        for move in state_changes.get("npc_movements") or []:  # [V70] None 방어
            if not isinstance(move, dict):
                continue
            name = move.get("name", "") or move.get("npc", "")
            if name:
                dest = move.get("destination", "") or move.get("to", "")
                if dest:
                    self._upsert_character(name, ep_num, note=f"이동: {dest}")

        # npc_personality_changes
        for pers in state_changes.get("npc_personality_changes") or []:  # [V70] None 방어
            if not isinstance(pers, dict):
                continue
            name = pers.get("name", "") or pers.get("npc", "")
            if name:
                traits = pers.get("traits", "") or pers.get("personality_traits", "")
                motivation = pers.get("motivation", "") or pers.get("primary_motivation", "")
                role_val = pers.get("role", "")
                self._upsert_character(
                    name,
                    ep_num,
                    role=role_val if role_val else None,
                    note=f"성격: {traits}" if traits else (f"동기: {motivation}" if motivation else "정보 갱신"),
                )

        # npc_npc_relationships
        for rel in state_changes.get("npc_npc_relationships") or []:  # [V70] None 방어
            if not isinstance(rel, dict):
                continue
            npc1 = rel.get("npc1", "")
            npc2 = rel.get("npc2", "")
            relation = rel.get("relation", "")
            if npc1 and npc2 and relation:
                self._upsert_character(npc1, ep_num, note=f"{npc2}와 관계: {relation}")
                self._upsert_character(npc2, ep_num, note=f"{npc1}와 관계: {relation}")

        self._ledger["last_updated_ep"] = ep_num

    def update_from_bible_delta(self, ep_num: int, bible_delta: dict):
        """
        Episode Bible delta에서 추가 사실 갱신.
        state_changes와 중복될 수 있지만 upsert 방식이므로 안전.

        Args:
            ep_num: 에피소드 번호
            bible_delta: Episode Bible delta dict
        """
        if not bible_delta or not isinstance(bible_delta, dict):
            return

        # new_npcs
        for npc_name in bible_delta.get("new_npcs") or []:  # [V70] None 방어
            if isinstance(npc_name, str) and npc_name:
                self._upsert_character(npc_name, ep_num, note="신규 등장")
            elif isinstance(npc_name, dict):
                name = npc_name.get("name", "")
                if name:
                    self._upsert_character(name, ep_num, note="신규 등장")

        # npc_deaths
        for npc_name in bible_delta.get("npc_deaths") or []:  # [V70] None 방어
            if isinstance(npc_name, str) and npc_name:
                self._upsert_character(npc_name, ep_num, status="dead", note="사망")

        # new_items
        for item_name in bible_delta.get("new_items") or []:  # [V70] None 방어
            if isinstance(item_name, str) and item_name:
                self._upsert_item(item_name, ep_num, owner="주인공", status="획득", note="신규 획득")

        # lost_items
        for item_name in bible_delta.get("lost_items") or []:  # [V70] None 방어
            if isinstance(item_name, str) and item_name:
                self._upsert_item(item_name, ep_num, status="분실", note="분실/파괴")

    # ═══════════════════════════════════════════════════════════════
    # 숫자/금액 갱신 (향후 LLM 추출 연동 시 사용)
    # ═══════════════════════════════════════════════════════════════

    def update_number(self, key: str, value, unit: str, ep_num: int, note: str = ""):
        """숫자/금액 팩트 갱신 (수동 또는 LLM 추출 시)"""
        nums = self._ledger["numbers"]
        if key not in nums:
            nums[key] = {"value": value, "unit": unit, "last_ep": ep_num, "history": []}
        entry = nums[key]
        old_val = entry.get("value", "")
        entry["value"] = value
        entry["unit"] = unit
        entry["last_ep"] = ep_num
        if note:
            entry["history"].append(f"ep{ep_num}: {note}")
        elif old_val != value:
            entry["history"].append(f"ep{ep_num}: {old_val} -> {value}")
        entry["history"] = entry["history"][-self.MAX_HISTORY_PER_ENTITY :]

    # ═══════════════════════════════════════════════════════════════
    # 내부 upsert 메서드
    # ═══════════════════════════════════════════════════════════════

    def _upsert_character(
        self, name: str, ep_num: int, status: str = None, role: str = None, relationship: str = None, note: str = ""
    ):
        """캐릭터 정보 생성 또는 갱신."""
        chars = self._ledger["characters"]
        if name not in chars:
            chars[name] = {
                "status": "alive",
                "role": "",
                "relationship": "",
                "established_ep": ep_num,
                "last_ep": ep_num,
                "history": [],
            }
        entry = chars[name]
        if status:
            entry["status"] = status
        if role:
            entry["role"] = role
        if relationship:
            entry["relationship"] = relationship
        entry["last_ep"] = ep_num
        if note:
            entry["history"].append(f"ep{ep_num}: {note}")
            entry["history"] = entry["history"][-self.MAX_HISTORY_PER_ENTITY :]

    def _upsert_item(self, name: str, ep_num: int, owner: str = None, status: str = None, note: str = ""):
        """아이템/무공 정보 생성 또는 갱신."""
        items = self._ledger["items"]
        if name not in items:
            items[name] = {
                "owner": owner or "",
                "status": status or "보유",
                "established_ep": ep_num,
                "last_ep": ep_num,
                "history": [],
            }
        entry = items[name]
        if owner:
            entry["owner"] = owner
        if status:
            entry["status"] = status
        entry["last_ep"] = ep_num
        if note:
            entry["history"].append(f"ep{ep_num}: {note}")
            entry["history"] = entry["history"][-self.MAX_HISTORY_PER_ENTITY :]

    def _upsert_location(self, name: str, ep_num: int, status: str = None, current_owner: str = None, note: str = ""):
        """장소 정보 생성 또는 갱신."""
        locs = self._ledger["locations"]
        if name not in locs:
            locs[name] = {
                "status": status or "정상",
                "current_owner": current_owner or "",
                "last_ep": ep_num,
                "history": [],
            }
        entry = locs[name]
        if status:
            entry["status"] = status
        if current_owner:
            entry["current_owner"] = current_owner
        entry["last_ep"] = ep_num
        if note:
            entry["history"].append(f"ep{ep_num}: {note}")
            entry["history"] = entry["history"][-self.MAX_HISTORY_PER_ENTITY :]

    def _upsert_org(self, name: str, ep_num: int, status: str = None, leader: str = None, note: str = ""):
        """조직 정보 생성 또는 갱신."""
        orgs = self._ledger["organizations"]
        if name not in orgs:
            orgs[name] = {"status": status or "활동중", "leader": leader or "", "last_ep": ep_num, "history": []}
        entry = orgs[name]
        if status:
            entry["status"] = status
        if leader:
            entry["leader"] = leader
        entry["last_ep"] = ep_num
        if note:
            entry["history"].append(f"ep{ep_num}: {note}")
            entry["history"] = entry["history"][-self.MAX_HISTORY_PER_ENTITY :]

    # ═══════════════════════════════════════════════════════════════
    # 프롬프트 주입용 요약
    # ═══════════════════════════════════════════════════════════════

    def to_summary(self, max_chars: int = None) -> str:
        """
        프롬프트 주입용 요약 텍스트.
        mandatory_context에 삽입하여 Writer/Director가 참조.

        Args:
            max_chars: 최대 문자 수 (기본: MAX_SUMMARY_CHARS)

        Returns:
            str: 팩트 원장 요약 텍스트
        """
        max_chars = max_chars or self.MAX_SUMMARY_CHARS
        last_ep = self._ledger.get("last_updated_ep", 0)
        if last_ep == 0:
            return ""

        parts = []
        parts.append(f"=== 팩트 원장 (제{last_ep}화 기준) ===")

        # ── 캐릭터 ──
        chars = self._ledger.get("characters", {})
        if chars:
            alive = {
                k: v for k, v in chars.items() if isinstance(v, dict) and v.get("status") == "alive"
            }  # [V70] non-dict 방어
            dead = {k: v for k, v in chars.items() if isinstance(v, dict) and v.get("status") == "dead"}  # [V70]

            if alive:
                parts.append(f"\n[생존 인물 ({len(alive)}명)]")
                for name, info in list(alive.items())[:30]:
                    rel = f", 관계: {info['relationship']}" if info.get("relationship") else ""
                    role_str = info.get("role", "?")
                    parts.append(f"  - {name} ({role_str}{rel}, ep{info.get('established_ep', '?')}~)")

            if dead:
                parts.append(f"\n[사망 인물 ({len(dead)}명)]")
                for name, info in dead.items():
                    cause = ""
                    # 이력에서 사망 원인 추출
                    for h in reversed(info.get("history", [])):
                        if "사망" in h:
                            cause = h.split(": ", 1)[-1] if ": " in h else h
                            break
                    cause_str = f" - {cause}" if cause else ""
                    parts.append(f"  - {name} (ep{info.get('last_ep', '?')}에서 사망{cause_str})")

        # ── 아이템/무공 ──
        items = self._ledger.get("items", {})
        if items:
            active_items = {
                k: v
                for k, v in items.items()
                if isinstance(v, dict) and v.get("status") not in ("분실", "파괴", "소모")
            }  # [V70] dict 방어
            lost_items = {
                k: v for k, v in items.items() if isinstance(v, dict) and v.get("status") in ("분실", "파괴", "소모")
            }  # [V70] dict 방어

            if active_items:
                parts.append(f"\n[보유 아이템/무공 ({len(active_items)}개)]")
                for name, info in list(active_items.items())[:20]:
                    owner = info.get("owner", "")
                    owner_str = f", 소유: {owner}" if owner else ""
                    parts.append(
                        f"  - {name} ({info.get('status', '보유')}{owner_str}, ep{info.get('established_ep', '?')})"
                    )

            if lost_items:
                parts.append(f"\n[분실/파괴된 아이템 ({len(lost_items)}개)]")
                for name, info in list(lost_items.items())[:10]:
                    parts.append(f"  - {name} ({info.get('status', '분실')}, ep{info.get('last_ep', '?')})")

        # ── 장소 ──
        locations = self._ledger.get("locations", {})
        if locations:
            destroyed_locs = {
                k: v for k, v in locations.items() if isinstance(v, dict) and v.get("status") == "destroyed"
            }  # [V70] dict 방어
            active_locs = {
                k: v for k, v in locations.items() if isinstance(v, dict) and v.get("status") != "destroyed"
            }  # [V70] dict 방어

            if destroyed_locs:
                parts.append(f"\n[파괴된 장소 ({len(destroyed_locs)}개)]")
                for name, info in destroyed_locs.items():
                    parts.append(f"  - {name} (ep{info.get('last_ep', '?')}에서 파괴)")

            if active_locs:
                parts.append(f"\n[주요 장소 ({len(active_locs)}개)]")
                for name, info in list(active_locs.items())[:10]:
                    owner = info.get("current_owner", "")
                    owner_str = f", 소유: {owner}" if owner else ""
                    parts.append(f"  - {name} ({info.get('status', '정상')}{owner_str})")

        # ── 조직 ──
        orgs = self._ledger.get("organizations", {})
        if orgs:
            destroyed_orgs = {
                k: v for k, v in orgs.items() if isinstance(v, dict) and v.get("status") == "destroyed"
            }  # [V70] dict 방어
            active_orgs = {
                k: v for k, v in orgs.items() if isinstance(v, dict) and v.get("status") != "destroyed"
            }  # [V70] dict 방어

            if destroyed_orgs:
                parts.append(f"\n[파괴된 조직 ({len(destroyed_orgs)}개)]")
                for name, info in destroyed_orgs.items():
                    parts.append(f"  - {name} (ep{info.get('last_ep', '?')}에서 파괴)")

            if active_orgs:
                parts.append(f"\n[활동 조직 ({len(active_orgs)}개)]")
                for name, info in list(active_orgs.items())[:10]:
                    leader = info.get("leader", "")
                    leader_str = f", 수장: {leader}" if leader else ""
                    parts.append(f"  - {name} ({info.get('status', '활동중')}{leader_str})")

        # ── 숫자/금액 ──
        numbers = self._ledger.get("numbers", {})
        if numbers:
            parts.append(f"\n[주요 수치 ({len(numbers)}개)]")
            for key, info in list(numbers.items())[:15]:
                if not isinstance(info, dict):
                    continue
                unit = info.get("unit", "")
                unit_str = f" {unit}" if unit else ""
                parts.append(f"  - {key}: {info.get('value', '?')}{unit_str} (ep{info.get('last_ep', '?')} 기준)")

        result = "\n".join(parts)
        if len(result) > max_chars:
            result = result[: max_chars - 20] + "\n... (팩트 원장 절삭)"
        return result

    # ═══════════════════════════════════════════════════════════════
    # 조회 유틸리티
    # ═══════════════════════════════════════════════════════════════

    def get_character(self, name: str) -> dict | None:
        """특정 캐릭터 정보 조회."""
        return self._ledger.get("characters", {}).get(name)

    def get_item(self, name: str) -> dict | None:
        """특정 아이템 정보 조회."""
        return self._ledger.get("items", {}).get(name)

    def get_dead_characters(self) -> list[str]:
        """사망한 캐릭터 이름 목록."""
        chars = self._ledger.get("characters", {})
        return [name for name, info in chars.items() if isinstance(info, dict) and info.get("status") == "dead"]

    def get_alive_characters(self) -> list[str]:
        """생존 캐릭터 이름 목록."""
        chars = self._ledger.get("characters", {})
        return [name for name, info in chars.items() if isinstance(info, dict) and info.get("status") == "alive"]

    def get_stats(self) -> dict:
        """팩트 원장 통계."""
        chars = self._ledger.get("characters", {})
        return {
            "last_updated_ep": self._ledger.get("last_updated_ep", 0),
            "characters": len(chars),
            "alive": sum(1 for v in chars.values() if isinstance(v, dict) and v.get("status") == "alive"),
            "dead": sum(1 for v in chars.values() if isinstance(v, dict) and v.get("status") == "dead"),
            "items": len(self._ledger.get("items", {})),
            "locations": len(self._ledger.get("locations", {})),
            "organizations": len(self._ledger.get("organizations", {})),
            "numbers": len(self._ledger.get("numbers", {})),
        }

    def rollback_to(self, target_ep: int) -> None:
        """[D-2] 특정 에피소드 이전 상태로 초기화 후 저장."""
        _logger.warning(
            "[D-2] FactLedger 롤백: ep %d 이후 데이터 초기화 (이전 last_updated_ep=%d)",
            target_ep,
            self._ledger.get("last_updated_ep", 0),
        )
        self._ledger = self._empty_ledger()
        self.save()
