"""[TF-17] Truth Gate — 메모리 오염 방지 advisory 검증기.

memorize_v20_episode() 직전에 state_updates + manuscript를 교차 검증하여
사실 불일치를 감지한다. Advisory 모드이므로 저장을 차단하지 않는다.
"""

import logging
import re

logger = logging.getLogger(__name__)


class TruthGate:
    """State-update / manuscript 교차 검증기 (advisory only)."""

    def __init__(self, world_state=None, fact_ledger=None, llm_ask=None):
        self._world_state = world_state
        self._fact_ledger = fact_ledger
        self._llm_ask = llm_ask  # Optional callable(prompt: str) -> str

    def validate(
        self,
        manuscript: str,
        state_updates: dict,
        *,
        npc_registry: dict | None = None,
    ) -> dict:
        """모든 검사를 수행하고 결과를 반환.

        Returns:
            {
                "passed": bool,
                "warnings": list[str],           # 하위 호환용
                "structured_warnings": list[dict], # [Phase4] severity 포함
                "blocking": False,
            }
        """
        warnings: list[str] = []
        structured_warnings: list[dict] = []

        if not manuscript and not state_updates:
            return {"passed": True, "warnings": [], "structured_warnings": [], "blocking": False}

        ms = manuscript or ""
        su = state_updates if isinstance(state_updates, dict) else {}

        self._check_deceased_resurrection(ms, su, npc_registry, warnings, structured_warnings)
        self._check_unowned_items(su, warnings, structured_warnings)
        self._check_destroyed_locations(ms, su, warnings, structured_warnings)
        self._check_skill_duplication(su, warnings, structured_warnings)
        self._check_karma_bounds(su, warnings, structured_warnings)
        self._check_npc_role_consistency(su, warnings, structured_warnings)
        self._check_world_law_violation(ms, warnings, structured_warnings)

        return {
            "passed": len(warnings) == 0,
            "warnings": warnings,
            "structured_warnings": structured_warnings,
            "blocking": False,
        }

    # ── 개별 검사 메서드 ──────────────────────────────────────────

    @staticmethod
    def _add_warning(
        warnings: list[str],
        structured_warnings: list[dict],
        text: str,
        severity: str,
        check: str,
    ) -> None:
        """warnings + structured_warnings 동시 추가 헬퍼."""
        warnings.append(text)
        structured_warnings.append({"text": text, "severity": severity, "check": check})

    def _check_deceased_resurrection(
        self,
        manuscript: str,
        state_updates: dict,
        npc_registry: dict | None,
        warnings: list[str],
        structured_warnings: list[dict],
    ) -> None:
        """사망 NPC가 행동/대사로 등장하는지 검사.

        회상/과거 장면/타인 언급은 허용한다.
        """
        deceased_names: list[str] = []

        # 1) npc_registry에서 deceased 목록 수집
        if npc_registry:
            for name, info in npc_registry.items():
                if isinstance(info, dict) and (info.get("status") == "dead" or info.get("deceased")):
                    deceased_names.append(name)

        # 2) world_state에서 deceased 목록 보충
        if self._world_state and hasattr(self._world_state, "get_deceased_npcs"):
            try:
                ws_deceased = self._world_state.get_deceased_npcs()
                if ws_deceased:
                    for n in ws_deceased:
                        if n not in deceased_names:
                            deceased_names.append(n)
            except Exception as e:
                logger.warning("[TruthGate] world_state.get_deceased_npcs() failed: %s", e)

        if not deceased_names:
            return

        # 회상/과거 장면 키워드 — 이 근처에 이름이 나오면 허용
        recall_patterns = ["회상", "과거", "기억", "떠올", "추억", "생전", "살아있을 때", "그때"]

        for name in deceased_names:
            if not name or len(name) < 2:
                continue

            # 원고에서 이름이 포함된 줄 검색
            for line in manuscript.split("\n"):
                if name not in line:
                    continue
                # 회상/과거 문맥인지 확인
                is_recall = any(kw in line for kw in recall_patterns)
                if is_recall:
                    continue

                # [E3-P1-1] 직접 대사/행동 패턴 — (?<![가-힣]) lookbehind로 부분문자열 false positive 방지
                _esc = re.escape(name)
                _lb = r"(?<![가-힣])"  # 한글 선행 문자가 없을 때만 매칭
                action_patterns = [
                    rf"{_lb}{_esc}[이가은는]\s",  # 주어로 등장
                    rf'"{_lb}{_esc}',  # 대사 시작
                    rf"{_lb}{_esc}.*말했다",
                    rf"{_lb}{_esc}.*외쳤다",
                    rf"{_lb}{_esc}.*달려",
                    rf"{_lb}{_esc}.*공격",
                ]
                _found_action = False
                for pat in action_patterns:
                    if re.search(pat, line):
                        self._add_warning(
                            warnings,
                            structured_warnings,
                            f"사망 NPC '{name}'가 행동/대사로 등장: {line[:60]}...",
                            "CRITICAL",
                            "deceased_resurrection",
                        )
                        _found_action = True
                        break
                if _found_action:
                    break  # NPC당 1건만 경고

            # state_updates에서 사망 NPC 갱신 검사
            npc_updates = state_updates.get("npc_updates", {})
            if isinstance(npc_updates, dict) and name in npc_updates:
                npc_upd = npc_updates[name]
                if isinstance(npc_upd, dict):
                    # 부활(deceased=False)이 아닌 상태 변경 감지
                    if npc_upd.get("deceased") is not True:
                        # status 변경이 있고 alive로 바뀌면 경고
                        if "status" in npc_upd and npc_upd["status"] not in ("dead", "deceased"):
                            self._add_warning(
                                warnings,
                                structured_warnings,
                                f"사망 NPC '{name}'의 상태가 갱신됨: {npc_upd}",
                                "CRITICAL",
                                "deceased_resurrection",
                            )

    def _check_unowned_items(self, state_updates: dict, warnings: list[str], structured_warnings: list[dict]) -> None:
        """미보유 아이템이 state_update로 사용/장착되는지 검사."""
        if not self._world_state:
            return

        item_updates = state_updates.get("item_updates", {})
        if not isinstance(item_updates, dict):
            return

        # world_state에서 현재 보유 아이템 목록 조회
        owned_items: set[str] = set()
        if hasattr(self._world_state, "get_owned_items"):
            try:
                owned = self._world_state.get_owned_items()
                if owned:
                    owned_items = set(owned)
            except Exception as e:
                logger.warning("[TruthGate] world_state.get_owned_items() failed: %s", e)
                return  # 조회 실패 시 검사 스킵

        for item_name, update in item_updates.items():
            if not isinstance(update, dict):
                continue
            action = update.get("action", "")
            # 사용/장착이면서 보유하지 않은 아이템
            if action in ("use", "equip", "consume") and item_name not in owned_items:
                self._add_warning(
                    warnings,
                    structured_warnings,
                    f"미보유 아이템 '{item_name}' {action} 시도",
                    "MAJOR",
                    "unowned_items",
                )

    def _check_destroyed_locations(
        self, manuscript: str, state_updates: dict, warnings: list[str], structured_warnings: list[dict]
    ) -> None:
        """파괴된 장소를 방문하는지 검사."""
        if not self._world_state:
            return

        destroyed_locations: list[str] = []
        if hasattr(self._world_state, "get_destroyed_locations"):
            try:
                dl = self._world_state.get_destroyed_locations()
                if dl:
                    destroyed_locations = list(dl)
            except Exception as e:
                logger.warning("[TruthGate] world_state.get_destroyed_locations() failed: %s", e)
                return

        if not destroyed_locations:
            return

        # state_updates에서 장소 이동 검사
        location_update = state_updates.get("location_update", "")
        if isinstance(location_update, str) and location_update:
            for loc in destroyed_locations:
                if loc in location_update:
                    self._add_warning(
                        warnings,
                        structured_warnings,
                        f"파괴된 장소 '{loc}'로 이동 시도",
                        "MAJOR",
                        "destroyed_locations",
                    )

        # 원고에서 파괴된 장소 방문 묘사 검사
        visit_patterns = ["도착했다", "들어섰다", "찾아갔다", "방문했다", "향했다"]
        for loc in destroyed_locations:
            if loc not in manuscript:
                continue
            for line in manuscript.split("\n"):
                if loc in line and any(vp in line for vp in visit_patterns):
                    self._add_warning(
                        warnings,
                        structured_warnings,
                        f"파괴된 장소 '{loc}' 방문 묘사 감지: {line[:60]}...",
                        "MAJOR",
                        "destroyed_locations",
                    )
                    break

    def _check_skill_duplication(
        self, state_updates: dict, warnings: list[str], structured_warnings: list[dict]
    ) -> None:
        """동일 스킬 중복 습득 검사."""
        if not self._world_state:
            return

        skill_updates = state_updates.get("skill_updates", [])
        if not isinstance(skill_updates, list):
            return

        # world_state에서 현재 보유 스킬 조회
        known_skills: set[str] = set()
        if hasattr(self._world_state, "get_known_skills"):
            try:
                ks = self._world_state.get_known_skills()
                if ks:
                    known_skills = set(ks)
            except Exception as e:
                logger.warning("[TruthGate] world_state.get_known_skills() failed: %s", e)
                return

        for skill_entry in skill_updates:
            if not isinstance(skill_entry, dict):
                continue
            skill_name = skill_entry.get("name", "")
            action = skill_entry.get("action", "learn")
            if action == "learn" and skill_name in known_skills:
                self._add_warning(
                    warnings,
                    structured_warnings,
                    f"이미 보유한 스킬 '{skill_name}' 중복 습득 시도",
                    "MINOR",
                    "skill_duplication",
                )

    def _check_karma_bounds(self, state_updates: dict, warnings: list[str], structured_warnings: list[dict]) -> None:
        """카르마 값 범위 검사 (0-100)."""
        karma_value = state_updates.get("karma")
        if karma_value is None:
            # protagonist_updates 안에 있을 수도 있음
            prot = state_updates.get("protagonist_updates", {})
            if isinstance(prot, dict):
                karma_value = prot.get("karma")

        if karma_value is None:
            return

        try:
            karma_num = float(karma_value)
        except (ValueError, TypeError):
            self._add_warning(
                warnings,
                structured_warnings,
                f"카르마 값이 숫자가 아닙니다: {karma_value}",
                "MINOR",
                "karma_bounds",
            )
            return

        if karma_num < 0 or karma_num > 100:
            self._add_warning(
                warnings,
                structured_warnings,
                f"카르마 값 범위 초과: {karma_num} (허용: 0-100)",
                "MINOR",
                "karma_bounds",
            )

    def _check_npc_role_consistency(
        self, state_updates: dict, warnings: list[str], structured_warnings: list[dict]
    ) -> None:
        """[장기 기억] NPC 속성 무단 변경 감지.

        state_updates에 npc_attribute_changes 없이 NPC의 기존 known_attrs 값이
        world_state 기록과 다른 방향으로 갱신되는 경우를 advisory 경고.
        """
        if not self._world_state or not hasattr(self._world_state, "get_npc_role_snapshot"):
            return
        try:
            npc_snapshot = self._world_state.get_npc_role_snapshot() or {}
        except Exception as e:
            logger.warning("[TruthGate] get_npc_role_snapshot() failed: %s", e)
            return
        if not npc_snapshot:
            return

        # state_updates에서 명시적 npc_attribute_changes 목록 수집 (의도적 변경)
        explicit_changes: set[tuple[str, str]] = set()
        for change in state_updates.get("npc_attribute_changes") or []:
            if isinstance(change, dict):
                _n = change.get("name", "")
                _f = change.get("field", "")
                if _n and _f:
                    explicit_changes.add((_n, _f))

        # npc_updates에서 role 직접 덮어쓰기 감지
        npc_updates = state_updates.get("npc_updates", {})
        if not isinstance(npc_updates, dict):
            return
        for npc_name, upd in npc_updates.items():
            if not isinstance(upd, dict) or npc_name not in npc_snapshot:
                continue
            snap = npc_snapshot[npc_name]
            # role 무단 변경 체크
            new_role = upd.get("role", "")
            original_role = snap.get("role_at_intro", "")
            if new_role and original_role and new_role != original_role:
                if (npc_name, "role") not in explicit_changes:
                    self._add_warning(
                        warnings,
                        structured_warnings,
                        (
                            f"[장기 기억] NPC '{npc_name}' 역할 무단 변경 감지: "
                            f"원본='{original_role}' → 변경='{new_role}' "
                            f"(의도적 변경이면 state_changes.npc_attribute_changes 사용)"
                        ),
                        "MAJOR",
                        "npc_role_consistency",
                    )
            # known_attrs 필드 무단 변경 체크
            for field, attr_info in (snap.get("known_attrs") or {}).items():
                known_val = attr_info.get("value", "") if isinstance(attr_info, dict) else str(attr_info)
                upd_val = upd.get(field, "")
                if upd_val and known_val and str(upd_val) != str(known_val):
                    if (npc_name, field) not in explicit_changes:
                        self._add_warning(
                            warnings,
                            structured_warnings,
                            (f"[장기 기억] NPC '{npc_name}'.{field} 무단 변경: 기록='{known_val}' → 현재='{upd_val}'"),
                            "MAJOR",
                            "npc_role_consistency",
                        )

    def _check_world_law_violation(self, manuscript: str, warnings: list[str], structured_warnings: list[dict]) -> None:
        """[LM-A-2] 세계관 절대 법칙 위반 검사 (LLM 기반, advisory only).

        llm_ask 콜백이 없거나 world_laws가 비어있으면 skip.
        """
        if not self._llm_ask:
            return
        if not self._world_state or not hasattr(self._world_state, "get_world_laws"):
            return

        try:
            laws = self._world_state.get_world_laws()
        except Exception as e:
            logger.debug("[TruthGate] get_world_laws() failed: %s", e)
            return

        if not laws:
            return

        try:
            laws_text = "\n".join(f"- {law}" for law in laws)
            ms_snippet = manuscript[:3000] if manuscript else ""
            prompt = (
                "다음은 이 세계의 절대 법칙입니다:\n"
                f"{laws_text}\n\n"
                "다음 원고가 위 법칙을 위반하는지 판단하세요:\n"
                f"{ms_snippet}\n\n"
                '반드시 JSON으로만 답하세요: {"violation": true/false, "reason": "위반 사유 또는 빈 문자열"}'
            )
            response = self._llm_ask(prompt)
            if not response:
                return

            # JSON 파싱
            import json

            resp_text = response
            if "```json" in resp_text:
                resp_text = resp_text.split("```json")[1].split("```")[0]
            elif "```" in resp_text:
                resp_text = resp_text.split("```")[1].split("```")[0]
            parsed = json.loads(resp_text.strip())

            if isinstance(parsed, dict) and parsed.get("violation"):
                reason = parsed.get("reason", "세계관 법칙 위반 감지")
                self._add_warning(
                    warnings,
                    structured_warnings,
                    f"[세계관 법칙 위반] {reason}",
                    "CRITICAL",
                    "world_law_violation",
                )
        except Exception as e:
            logger.debug("[TruthGate] world_law_violation 검사 실패 (비치명): %s", e)
