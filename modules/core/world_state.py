"""
[V68] WorldStateManager -- 세계 상태 문서 (World State Document)

매 화 확정 후 "현재 세계의 진실"을 ~5K자 JSON으로 유지/갱신하여,
200화에서도 전체 세계 상태를 파악할 수 있게 합니다.

DB anchor 'world_state'에 저장/로드.
LLM 호출 없이 Python만으로 state_changes 기반 자동 갱신.
"""

import json
import logging

_logger = logging.getLogger(__name__)


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
        "alive_npcs": {},  # name -> {role, relation, personality, location}
        "dead_npcs": {},  # name -> {ep, cause}
        "relationships": {},  # npc_name -> relation_str
        "active_items": {},  # item_name -> {ep_acquired, status}
        "destroyed": [],  # [{name, type, ep, cause}]
        "active_plots": [],  # [{plot, status, since_ep}]
        "world_notes": [],  # 자유형 메모 (최대 10개)
    }

    def __init__(self, db) -> None:
        """
        Args:
            db: DBManager 인스턴스
        """
        self.db = db
        self._state: dict = self._load_or_init()

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

    def save(self) -> None:
        """DB anchor 'world_state'에 저장"""
        try:
            self.db.save_anchor("world_state", self._state)
        except Exception as e:
            _logger.error("[V68] WorldState: DB 저장 실패: %s", e)

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

        try:
            if source == "arc":
                self._state["last_updated_ep"] = ep_num
                self._state["last_updated_source"] = "arc"
            else:
                self._state["last_updated_ep"] = ep_num

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
                # dead_npcs에 추가
                self._state["dead_npcs"][name] = {
                    "ep": death.get("episode", ep_num) if isinstance(death, dict) else ep_num,
                    "cause": death.get("cause", "사망") if isinstance(death, dict) else "사망",
                }
                # alive_npcs에서 제거
                self._state["alive_npcs"].pop(name, None)
                # relationships 유지 (죽은 NPC와의 관계도 기록)

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

            # 3. 관계 변화
            for rel in state_changes.get("relationship_changes") or []:
                if not isinstance(rel, dict):
                    continue
                npc = rel.get("npc", "") or rel.get("target", "")  # [G16] analyst 프롬프트는 "target" 키 사용
                to_rel = rel.get("to", "")
                if npc and to_rel:
                    self._state["relationships"][npc] = to_rel
                    # alive_npcs에 없으면 등록
                    if npc not in self._state["dead_npcs"]:
                        if npc not in self._state["alive_npcs"]:
                            self._state["alive_npcs"][npc] = {}
                        self._state["alive_npcs"][npc]["relation"] = to_rel

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

            # 5. 엔티티 파괴 (조직/장소)
            _existing_destroyed_names = {
                d.get("name") for d in self._state["destroyed"] if isinstance(d, dict)
            }  # [V70] 중복 방지
            for dest in state_changes.get("entity_destructions") or []:
                if not isinstance(dest, dict):
                    continue
                _dest_name = dest.get("name", "")
                if not _dest_name:
                    continue
                if _dest_name in _existing_destroyed_names:  # [V70] 이미 등록됨
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

            # 6. NPC 성격 변화
            for personality in state_changes.get("npc_personality_changes") or []:
                if not isinstance(personality, dict):
                    continue
                npc = personality.get("name", "") or personality.get("npc", "")
                if not npc or npc in self._state["dead_npcs"]:
                    continue
                if npc not in self._state["alive_npcs"]:
                    self._state["alive_npcs"][npc] = {}
                # [V70] 스키마 키 호환: LLM은 'traits'/'motivation' 출력, 레거시 'personality_traits'/'primary_motivation' 폴백
                _traits = personality.get("traits", "") or personality.get("personality_traits", "")
                if _traits:
                    self._state["alive_npcs"][npc]["personality"] = _traits
                _motivation = personality.get("motivation", "") or personality.get("primary_motivation", "")
                if _motivation:
                    self._state["alive_npcs"][npc]["motivation"] = _motivation

            # 7. 완결 플롯
            for plot in state_changes.get("resolved_plots") or []:
                if isinstance(plot, dict):
                    plot_desc = plot.get("plot", "") or plot.get("description", "")
                elif isinstance(plot, str):
                    plot_desc = plot
                else:
                    continue
                if plot_desc:
                    # active_plots에서 제거
                    self._state["active_plots"] = [
                        p for p in self._state["active_plots"] if p.get("plot", "") != plot_desc
                    ]

            # 8. 동행자 변화
            for comp in state_changes.get("companion_changes") or []:
                if not isinstance(comp, dict):
                    continue
                npc = comp.get("name", "")
                action = comp.get("action", "joined")
                if not npc:
                    continue
                if npc not in self._state["dead_npcs"]:
                    if npc not in self._state["alive_npcs"]:
                        self._state["alive_npcs"][npc] = {}
                    self._state["alive_npcs"][npc]["companion"] = action in (
                        "join",
                        "joined",
                        "합류",
                    )  # [V70] LLM 출력값 호환

            # 크기 제한: destroyed 최대 50개, world_notes 최대 10개
            if len(self._state["destroyed"]) > 50:
                self._state["destroyed"] = self._state["destroyed"][-50:]
            if len(self._state.get("world_notes", [])) > 10:
                self._state["world_notes"] = self._state["world_notes"][-10:]

        except Exception as e:
            _logger.error("[V68] WorldState: update_from_state_changes 실패 (비차단): %s", e)

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

    def get_summary(self, max_chars: int = 5000) -> str:
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

            # 주인공
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
                skills_str = ", ".join(prot["skills"][-20:])  # 최근 20개
                prot_lines.append(f"습득 무공/스킬: {skills_str}")
            if prot_lines:
                parts.append("[주인공]\n" + "\n".join(prot_lines))

            # 생존 NPC — [TF-C06] 중요도 기반 정렬 후 truncation
            alive = self._state.get("alive_npcs", {})
            if alive:
                npc_lines = []

                # 중요도: 동행자(3) > 관계있음(2) > 역할있음(1) > 기타(0)
                def _npc_importance(item):
                    _name, _info = item
                    if not isinstance(_info, dict):
                        return 0
                    score = 0
                    if _info.get("companion"):
                        score += 3
                    if _info.get("relation"):
                        score += 2
                    if _info.get("role"):
                        score += 1
                    return score

                sorted_alive = sorted(alive.items(), key=_npc_importance, reverse=True)
                for name, info in sorted_alive[:30]:  # 최대 30명
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
                        if info.get("companion"):
                            desc_parts.append("(동행중)")
                    desc = " / ".join(desc_parts) if desc_parts else ""
                    npc_lines.append(f"- {name}" + (f": {desc}" if desc else ""))
                parts.append(f"[생존 NPC ({len(alive)}명)]\n" + "\n".join(npc_lines))

            # 사망 NPC
            dead = self._state.get("dead_npcs", {})
            if dead:
                dead_lines = []
                for name, info in list(dead.items())[:20]:  # 최대 20명
                    if isinstance(info, dict):
                        ep = info.get("ep", "?")
                        cause = info.get("cause", "")
                        dead_lines.append(f"- {name} (제{ep}화, {cause})")
                    else:
                        dead_lines.append(f"- {name}")
                parts.append(f"[사망 NPC ({len(dead)}명) -- 절대 등장 금지]\n" + "\n".join(dead_lines))

            # 관계
            rels = self._state.get("relationships", {})
            if rels:
                rel_lines = [f"- {npc}: {rel}" for npc, rel in list(rels.items())[:20]]
                parts.append("[주요 관계]\n" + "\n".join(rel_lines))

            # 활성 아이템
            items = self._state.get("active_items", {})
            active_items = {k: v for k, v in items.items() if isinstance(v, dict) and v.get("status", "보유") == "보유"}
            if active_items:
                item_lines = [f"- {name}" for name in list(active_items.keys())[:20]]
                parts.append("[보유 아이템]\n" + "\n".join(item_lines))

            # 파괴된 장소/조직
            destroyed = self._state.get("destroyed", [])
            if destroyed:
                dest_lines = [
                    f"- {d.get('name', '?')} ({d.get('type', '?')}, 제{d.get('ep', '?')}화)"
                    for d in destroyed[-10:]  # 최근 10개
                ]
                parts.append("[파괴된 장소/조직 -- 복구 불가]\n" + "\n".join(dest_lines))

            # 진행 중 플롯
            plots = self._state.get("active_plots", [])
            if plots:
                plot_lines = [f"- {p.get('plot', '?')} (제{p.get('since_ep', '?')}화~)" for p in plots[-10:]]
                parts.append("[진행 중 플롯]\n" + "\n".join(plot_lines))

            result = "\n\n".join(parts)

            # max_chars truncation
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

    def register_alive_npc(self, name: str, role: str = "", relation: str = "", location: str = ""):
        """NPC를 생존 목록에 수동 등록"""
        if name in self._state.get("dead_npcs", {}):
            return  # 이미 죽은 NPC는 등록 불가
        if name not in self._state["alive_npcs"]:
            self._state["alive_npcs"][name] = {}
        if role:
            self._state["alive_npcs"][name]["role"] = role
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
        _MAX_ACTIVE_PLOTS = 30
        active_plots = self._state["active_plots"]
        if len(active_plots) > _MAX_ACTIVE_PLOTS:
            active_plots[:] = active_plots[-_MAX_ACTIVE_PLOTS:]

    def get_state_dict(self) -> dict:
        """내부 상태 dict 반환 (디버깅/대시보드용) — deep copy로 외부 변조 방지"""
        return json.loads(json.dumps(self._state, ensure_ascii=False))

    def rollback_to(self, target_ep: int) -> None:
        """[D-2] 특정 에피소드 이전 상태로 롤백 (episode_bibles 리플레이)."""
        _logger.warning(
            "[D-2] WorldState 롤백: ep %d 이전으로 복원 (이전 last_updated_ep=%d)",
            target_ep,
            self._state.get("last_updated_ep", 0),
        )
        self._state = json.loads(json.dumps(self._INIT_STATE, ensure_ascii=False))
        # [Sweep64] 1~(target_ep-1) 에피소드의 state_changes를 리플레이
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
