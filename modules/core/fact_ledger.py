"""
[V68] 누적 팩트 원장 (Cumulative Fact Ledger)
— 장기연재 모순 방지의 핵심

매 화 확정 후 state_changes에서 자동으로 사실을 추출/갱신하여,
200화에서도 1화의 사실(증권사명, 가격, 캐릭터 고향 등)을 즉시 조회 가능하게 합니다.

DB anchor 'fact_ledger'에 저장/로드.
LLM 호출 없이 Python만으로 state_changes 기반 자동 갱신 — 비용 0.
"""

import logging
import re

_logger = logging.getLogger(__name__)
_DIRECT_FINANCIAL_FACT_KEYS = ("capital", "total_assets", "wealth")
_KOREAN_UNIT_MAP = (
    ("조", 1e12),
    ("억", 1e8),
    ("만", 1e4),
)


def _coerce_direct_financial_scalar(raw: object) -> float | None:
    """Normalize direct financial scalar fields into won-scale floats."""
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if not isinstance(raw, str):
        return None

    text = raw.strip().replace(",", "")
    if not text:
        return None

    sign = 1.0
    if text[0] in "+-":
        if text[0] == "-":
            sign = -1.0
        text = text[1:].strip()
    if not text:
        return None

    total = 0.0
    matched_unit = False
    remaining = text

    for unit, mult in _KOREAN_UNIT_MAP:
        pattern = rf"([0-9]+(?:\.[0-9]+)?)\s*{re.escape(unit)}"
        for value in re.findall(pattern, remaining):
            total += float(value) * mult
            matched_unit = True
        remaining = re.sub(pattern, "", remaining)

    if matched_unit:
        tail = re.search(r"([0-9]+(?:\.[0-9]+)?)", remaining)
        if tail:
            total += float(tail.group(1))
        return sign * total

    plain = re.search(r"([0-9]+(?:\.[0-9]+)?)", remaining)
    if not plain:
        return None
    return sign * float(plain.group(1))


def _build_truncation_suffix(total: int, shown: int, *, unit: str = "개") -> str:
    if total > shown:
        return f" (총 {total}{unit} 중 {shown}{unit} 표시)"
    return ""


def summarize_fact_ledger_numbers_block(
    ledger: dict | None,
    *,
    header: str = "[팩트 원장 핵심 수치]",
    max_items: int = 10,
) -> str:
    """팩트 원장 수치 블록을 Stage 2/3 컨텍스트용 짧은 문자열로 직렬화한다."""
    if not isinstance(ledger, dict):
        return ""

    numbers = ledger.get("numbers", {})
    if not isinstance(numbers, dict) or not numbers:
        return ""

    shown_entries: list[tuple[str, dict]] = []
    for key, info in numbers.items():
        if not isinstance(info, dict):
            continue
        shown_entries.append((str(key), info))
        if len(shown_entries) >= max(1, int(max_items)):
            break

    if not shown_entries:
        return ""

    title = f"{header}{_build_truncation_suffix(len(numbers), len(shown_entries))}"
    lines = [title]
    for key, info in shown_entries:
        value = info.get("value", "?")
        unit = str(info.get("unit", "") or "").strip()
        unit_str = f" {unit}" if unit else ""
        last_ep = info.get("last_ep", "?")
        established_value = info.get("established_value", "")
        established_ep = info.get("established_ep", "?")
        if established_value not in ("", None) and str(established_value) != str(value):
            lines.append(
                f"- {key}: {established_value}{unit_str} (ep{established_ep}) -> {value}{unit_str} (ep{last_ep})"
            )
        else:
            lines.append(f"- {key}: {value}{unit_str} (ep{last_ep} 기준)")
    return "\n".join(lines)


class FactLedger:
    """[V68] 누적 팩트 원장 — 장기연재 모순 방지의 핵심

    단일 스레드 설계 — DB 쓰기는 pipeline 순차 실행 중 발생. threading.Lock 불필요.
    """

    MAX_HISTORY_PER_ENTITY = 100  # [TF-C05] 10→100 확장 (장기연재 팩트 보존)
    MAX_SUMMARY_CHARS = 50000  # [1M-CTX-P1] 20000 → 50000 (100화 이상 NPC 전량 수용)

    # ═══════════════════════════════════════════════════════════════
    # 초기화 / 로드 / 저장
    # ═══════════════════════════════════════════════════════════════

    def __init__(self, db) -> None:
        """
        Args:
            db: DBManager 인스턴스 (save_anchor / load_anchor 지원)
        """
        self.db = db
        self._degraded = False
        self._degraded_reason = ""
        self._ledger: dict = self._load()
        self.last_save_ok: bool | None = None
        self.last_save_error: str | None = None

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
                self._degraded = False
                self._degraded_reason = ""
                return raw
            self._degraded = False
            self._degraded_reason = ""
        except Exception as e:
            _logger.warning(f"⚠️ [V70] FactLedger DB 로드 실패, 초기화: {e}")
            self._degraded = True
            self._degraded_reason = str(e)
        return self._empty_ledger()

    @staticmethod
    def _empty_ledger() -> dict:
        """빈 팩트 원장 스키마"""
        return {
            "characters": {},  # {name: {status, role, relationship, established_ep, last_ep, history[]}}
            "numbers": {},  # {key: {value, unit, established_ep, established_value, last_ep, history[]}}
            "items": {},  # {name: {owner, status, established_ep, last_ep, history[]}}
            "locations": {},  # {name: {status, current_owner, last_ep, history[]}}
            "organizations": {},  # {name: {status, leader, last_ep, history[]}}
            "last_updated_ep": 0,
        }

    def save(self) -> bool:
        """팩트 원장을 DB anchor에 저장."""
        try:
            self.db.save_anchor("fact_ledger", self._ledger)
            self.last_save_ok = True
            self.last_save_error = None
            return True
        except Exception as e:
            _logger.warning(f"[V68] 팩트 원장 저장 실패: {e}")
            self.last_save_ok = False
            self.last_save_error = str(e)
            return False

    @property
    def degraded(self) -> bool:
        return bool(self._degraded)

    @property
    def degraded_reason(self) -> str:
        return str(self._degraded_reason or "")

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

        # Same-batch deaths must land before later character phases.
        self._apply_character_foundation_state_changes(ep_num, state_changes)
        self._apply_item_state_changes(ep_num, state_changes)
        self._apply_entity_state_changes(ep_num, state_changes)
        self._apply_character_followup_state_changes(ep_num, state_changes)

        # [TF-C07] 수치 팩트 자동 추출 — 기존 update_number() 활용
        self._extract_numerical_facts(ep_num, state_changes)

        self._ledger["last_updated_ep"] = ep_num

    def _apply_character_foundation_state_changes(self, ep_num: int, state_changes: dict):
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
            npc = rel.get("npc", "") or rel.get("target", "")  # [G17] analyst 프롬프트는 "target" 키 사용
            # [IFC] Sink-side guard: scalarize dict actor refs to prevent unhashable-type errors
            if isinstance(npc, dict):
                npc = str(npc.get("name") or npc.get("npc") or next((v for v in npc.values() if isinstance(v, str)), str(npc)))
            npc = str(npc).strip()
            if npc:
                self._upsert_character(
                    npc,
                    ep_num,
                    relationship=rel.get("to", ""),
                    note=f"관계 변화: {rel.get('from', '?')} -> {rel.get('to', '?')}",
                )

    def _apply_item_state_changes(self, ep_num: int, state_changes: dict):
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

        for item_name, raw_count in (state_changes.get("inventory_counts") or {}).items():
            if not item_name:
                continue
            try:
                count = int(raw_count)
            except (TypeError, ValueError):
                continue
            if count <= 0:
                continue
            self._upsert_item(item_name, ep_num, owner="주인공", status="보유", quantity=count, note=f"수량 {count}")

        for delta in state_changes.get("inventory_count_deltas") or []:
            if not isinstance(delta, dict):
                continue
            item_name = delta.get("name", "")
            if not item_name:
                continue
            try:
                to_count = int(delta.get("to", 0) or 0)
            except (TypeError, ValueError):
                to_count = 0
            status = "보유" if to_count > 0 else "분실"
            note = f"수량 {delta.get('from', '?')} -> {to_count}"
            self._upsert_item(item_name, ep_num, owner="주인공", status=status, quantity=to_count, note=note)

    def _apply_entity_state_changes(self, ep_num: int, state_changes: dict):
        # entity_destructions
        for dest in state_changes.get("entity_destructions") or []:  # [V70] None 방어
            if not isinstance(dest, dict):
                continue
            name = dest.get("name", "")
            dtype = dest.get("type", "unknown")
            if name:
                note = f"파괴 (원인: {dest.get('cause', '불명')})"
                if dtype == "organization":
                    self._upsert_org(name, ep_num, status="destroyed", note=note)
                else:
                    self._upsert_location(name, ep_num, status="destroyed", note=note)

    def _apply_character_followup_state_changes(self, ep_num: int, state_changes: dict):
        # npc_injuries
        for injury in state_changes.get("npc_injuries") or []:  # [V70] None 방어
            if not isinstance(injury, dict):
                continue
            name = injury.get("name", "") or injury.get("npc", "")
            if not name or self._is_dead_character(name):
                continue
            # [Sweep55] LLM 스키마는 "state" 키 사용 (경상/중상/위독)
            injury_type = injury.get("state", "") or injury.get("type", "") or injury.get("injury", "")
            self._upsert_character(name, ep_num, note=f"부상: {injury_type}" if injury_type else "부상")

        # npc_movements
        for move in state_changes.get("npc_movements") or []:  # [V70] None 방어
            if not isinstance(move, dict):
                continue
            name = move.get("name", "") or move.get("npc", "")
            if not name or self._is_dead_character(name):
                continue
            dest = move.get("destination", "") or move.get("to", "")
            if dest:
                self._upsert_character(name, ep_num, note=f"이동: {dest}")

        # npc_personality_changes
        for pers in state_changes.get("npc_personality_changes") or []:  # [V70] None 방어
            if not isinstance(pers, dict):
                continue
            name = pers.get("name", "") or pers.get("npc", "")
            if not name or self._is_dead_character(name):
                continue
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
            if self._is_dead_character(npc1) or self._is_dead_character(npc2):
                continue
            if npc1 and npc2 and relation:
                self._upsert_character(npc1, ep_num, note=f"{npc2}와 관계: {relation}")
                self._upsert_character(npc2, ep_num, note=f"{npc1}와 관계: {relation}")

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
        first_ep = entry.get("established_ep", ep_num)
        old_val = entry.get("value", "")
        entry["value"] = value
        entry["unit"] = unit
        entry["last_ep"] = ep_num
        entry.setdefault("established_ep", ep_num)
        entry.setdefault("established_value", value)  # [P0-2] 초기값 영구 보존
        if note:
            entry["history"].append(f"ep{ep_num}: {note}")
        elif old_val != value:
            entry["history"].append(f"ep{ep_num}: {old_val} -> {value}")
        entry["history"] = entry["history"][-self.MAX_HISTORY_PER_ENTITY :]
        # [Phase1-L0] DB sync — canonical_facts 테이블에 수치 팩트 동기화
        if getattr(self, "db", None):
            try:
                self.db.upsert_canonical_fact(
                    fact_key=key,
                    fact_type="numerical",
                    value={"value": value, "unit": unit},
                    first_ep=first_ep,
                    last_ep=ep_num,
                )
            except Exception as _e:
                _logger.debug("[FactLedger] canonical_facts DB sync 실패 (비치명): %s", _e)

    def _extract_numerical_facts(self, ep_num: int, state_changes: dict) -> None:
        """[TF-C07] state_changes에서 수치 팩트 자동 추출 → update_number() 배선."""
        if not state_changes or not isinstance(state_changes, dict):
            return

        # actual_truth/state_changes can carry direct financial scalar fields.
        for fact_key in _DIRECT_FINANCIAL_FACT_KEYS:
            amount = _coerce_direct_financial_scalar(state_changes.get(fact_key))
            if amount is None:
                continue
            self.update_number(fact_key, amount, "won", ep_num, note="direct financial scalar extracted")

        # ── status_shadow (무협: 내공/체력 변동) ──
        shadow = state_changes.get("status_shadow") or {}
        if isinstance(shadow, dict):
            # [TF-21-05] internal_energy_loss(무협)와 key_stat_change(비무협) 분리 처리
            _energy_loss = shadow.get("internal_energy_loss")
            if _energy_loss is not None and isinstance(_energy_loss, int | float):
                self.update_number("내공_소모량", _energy_loss, "단위", ep_num, note="status_shadow 자동 추출")
            energy = _energy_loss
            remaining = shadow.get("internal_energy_remaining")
            if remaining is not None and isinstance(remaining, int | float):
                self.update_number("내공_잔여", remaining, "단위", ep_num, note="status_shadow 자동 추출")

        # ── financial_events (투자 장르) ──
        for fin in state_changes.get("financial_events") or []:
            if not isinstance(fin, dict):
                continue
            asset_name = fin.get("asset") or fin.get("name") or ""
            if not asset_name:
                continue
            for field in ("price", "value", "amount", "leverage", "exchange_rate"):
                val = fin.get(field)
                if val is not None and isinstance(val, int | float):
                    key = f"{asset_name}_{field}"
                    unit = fin.get("currency", "") or fin.get("unit", "")
                    self.update_number(key, val, unit, ep_num, note="financial_events 자동 추출")

        # ── power_level (파워 스케일링) ──
        power = state_changes.get("power_level")
        if power is not None and isinstance(power, int | float):
            self.update_number("주인공_전투력", power, "레벨", ep_num, note="power_level 자동 추출")

        # ── numerical_facts (범용 수치: 연봉/나이/인원/거리 등) ──
        for fact in state_changes.get("numerical_facts") or []:
            if not isinstance(fact, dict):
                continue
            name = fact.get("name", "")
            val = fact.get("value")
            unit = str(fact.get("unit", ""))
            if name and val is not None and isinstance(val, int | float):
                self.update_number(name, val, unit, ep_num, note="numerical_facts 자동 추출")

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

    def _upsert_item(
        self,
        name: str,
        ep_num: int,
        owner: str = None,
        status: str = None,
        note: str = "",
        quantity: int | None = None,
    ):
        """아이템/무공 정보 생성 또는 갱신."""
        items = self._ledger["items"]
        if name not in items:
            items[name] = {
                "owner": owner or "",
                "status": status or "보유",
                "quantity": quantity if isinstance(quantity, int) and quantity >= 0 else None,
                "established_ep": ep_num,
                "last_ep": ep_num,
                "history": [],
            }
        entry = items[name]
        if owner:
            entry["owner"] = owner
        if status:
            entry["status"] = status
        if isinstance(quantity, int) and quantity >= 0:
            entry["quantity"] = quantity
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
                _alive_shown = list(alive.items())[:30]
                _alive_shown_count = len(_alive_shown)
                _alive_suffix = _build_truncation_suffix(len(alive), _alive_shown_count, unit="명")
                parts.append(f"\n[생존 인물 ({_alive_shown_count}명){_alive_suffix}]")
                for name, info in _alive_shown:
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
                    last_ep = info.get("last_ep", "unknown")
                    parts.append(f"  - {name} (ep{last_ep}에서 사망{cause_str})")

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
                _active_item_shown = list(active_items.items())[:20]
                _active_item_suffix = _build_truncation_suffix(len(active_items), len(_active_item_shown))
                parts.append(f"\n[보유 아이템/무공 ({len(_active_item_shown)}개){_active_item_suffix}]")
                for name, info in _active_item_shown:
                    owner = info.get("owner", "")
                    owner_str = f", 소유: {owner}" if owner else ""
                    quantity = info.get("quantity")
                    quantity_str = f" x{quantity}" if isinstance(quantity, int) and quantity > 1 else ""
                    parts.append(
                        f"  - {name}{quantity_str} ({info.get('status', '보유')}{owner_str}, ep{info.get('established_ep', '?')})"
                    )

            if lost_items:
                _lost_item_shown = list(lost_items.items())[:10]
                _lost_item_suffix = _build_truncation_suffix(len(lost_items), len(_lost_item_shown))
                parts.append(f"\n[분실/파괴된 아이템 ({len(_lost_item_shown)}개){_lost_item_suffix}]")
                for name, info in _lost_item_shown:
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
                    last_ep = info.get("last_ep", "unknown")
                    parts.append(f"  - {name} (ep{last_ep}에서 파괴)")

            if active_locs:
                _active_loc_shown = list(active_locs.items())[:10]
                _active_loc_suffix = _build_truncation_suffix(len(active_locs), len(_active_loc_shown))
                parts.append(f"\n[주요 장소 ({len(_active_loc_shown)}개){_active_loc_suffix}]")
                for name, info in _active_loc_shown:
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
                    last_ep = info.get("last_ep", "unknown")
                    parts.append(f"  - {name} (ep{last_ep}에서 파괴)")

            if active_orgs:
                _active_org_shown = list(active_orgs.items())[:10]
                _active_org_suffix = _build_truncation_suffix(len(active_orgs), len(_active_org_shown))
                parts.append(f"\n[활동 조직 ({len(_active_org_shown)}개){_active_org_suffix}]")
                for name, info in _active_org_shown:
                    leader = info.get("leader", "")
                    leader_str = f", 수장: {leader}" if leader else ""
                    parts.append(f"  - {name} ({info.get('status', '활동중')}{leader_str})")

        # ── 숫자/금액 ──
        numbers = self._ledger.get("numbers", {})
        if numbers:
            _number_shown = list(numbers.items())[:15]
            _number_suffix = _build_truncation_suffix(len(numbers), len(_number_shown))
            parts.append(f"\n[주요 수치 ({len(_number_shown)}개){_number_suffix}]")
            for key, info in _number_shown:
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

    def get_number(self, key: str) -> dict | None:
        """특정 수치 팩트 조회."""
        return self._ledger.get("numbers", {}).get(key)

    def get_numbers(self) -> dict:
        """전체 수치 팩트 딕셔너리 반환."""
        return dict(self._ledger.get("numbers", {}))

    def get_canonical_summary(self, max_chars: int = 5000) -> str:
        """[Phase1-L0] 수치 팩트 압축 요약 — L0 고정 주입용."""
        nums = self._ledger.get("numbers", {})
        if not nums:
            return ""
        lines = ["[수치 제약 (L0)]"]
        for k, v in list(nums.items())[:30]:
            if not isinstance(v, dict):
                continue
            val = v.get("value", "?")
            unit = v.get("unit", "")
            ep = v.get("last_ep", "?")
            unit_str = f" {unit}" if unit else ""
            lines.append(f"- {k}: {val}{unit_str} (EP{ep} 기준)")
        return "\n".join(lines)[:max_chars]

    def get_character(self, name: str) -> dict | None:
        """특정 캐릭터 정보 조회."""
        return self._ledger.get("characters", {}).get(name)

    def _is_dead_character(self, name: str) -> bool:
        info = self.get_character(name)
        return isinstance(info, dict) and info.get("status") == "dead"

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
        """[D-2] 특정 에피소드 이전 상태로 롤백 (episode_bibles 리플레이).

        [INF-P1-9] 최적화: 개별 get_episode_bible(ep) N회 호출 대신
        get_all_episode_bibles()로 한 번에 로드 후 필터링하여 O(1) DB 호출.
        """
        _logger.warning(
            "[D-2] FactLedger 롤백: ep %d 이전으로 복원 (이전 last_updated_ep=%d)",
            target_ep,
            self._ledger.get("last_updated_ep", 0),
        )
        self._ledger = self._empty_ledger()
        # [INF-P1-9] 일괄 로드 후 target_ep 미만만 리플레이
        try:
            all_bibles = self.db.get_all_episode_bibles()
        except Exception as e:
            _logger.warning("[D-2] FactLedger 일괄 로드 실패, 개별 조회 폴백: %s", e)
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
                    self.update_from_bible_delta(ep, bible)
                except Exception as e:
                    _logger.warning("[D-2] FactLedger 리플레이 실패 ep %d: %s", ep, e)
        else:
            # 폴백: 개별 조회 (기존 동작)
            for ep in range(1, target_ep):
                try:
                    bible = self.db.get_episode_bible(ep)
                    if bible:
                        sc = bible.get("state_changes", {})
                        if sc:
                            self.update_from_state_changes(ep, sc)
                        self.update_from_bible_delta(ep, bible)
                except Exception as e:
                    _logger.warning("[D-2] FactLedger 리플레이 실패 ep %d: %s", ep, e)
        self.save()
