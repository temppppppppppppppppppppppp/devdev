"""
[LITE-V1] StateLedger - 파일 기반 상태 추적
=============================================
추가 LLM 호출 0회. 기존 출력물을 Python regex로 파싱하여
NPC 생사/주인공 상태/체인 링크 등을 추적.

저장: projects/{name}/_state.json
"""

import json
import logging
import re
from copy import deepcopy
from pathlib import Path

_logger = logging.getLogger(__name__)

# ── 초기 스키마 ─────────────────────────────────────────────

_INIT_STATE = {
    "version": 1,
    "last_updated_ep": 0,
    "protagonist": {
        "name": "",
        "location": "",
        "level": "",
        "injuries": "정상",
        "skills": [],
    },
    "alive_npcs": {},  # name -> {role, relation, first_ep}
    "dead_npcs": {},  # name -> {ep, cause}
    "relationships": {},  # npc -> relation_str
    "active_items": [],  # [item_name, ...]
    "destroyed": [],  # [{name, type, ep}]
    "chain_link": {  # 마지막 에피소드 종료 상태
        "ep": 0,
        "ending": "",  # 마지막 장면 요약
        "location": "",
        "cliffhanger": "",
    },
    "contradictions_log": [],  # [{ep, issue}]
}


class StateLedger:
    """파일 기반 세계 상태 추적기 (LLM 호출 0회)"""

    def __init__(self, project_dir: Path):
        self._project_dir = Path(project_dir)
        self._state_path = self._project_dir / "_state.json"
        self._state: dict = self._load()

    # ── 로드/저장 ───────────────────────────────────────────

    def _load(self) -> dict:
        """_state.json 로드. 없으면 초기 스키마 반환."""
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text(encoding="utf-8"))
                _logger.info("[LITE-V1] StateLedger 로드: %s", self._state_path)
                return data
            except Exception as e:
                _logger.warning("[LITE-V1] _state.json 파싱 실패, 초기화: %s", e)
        return deepcopy(_INIT_STATE)

    def save(self):
        """현재 상태를 _state.json에 저장."""
        try:
            self._state_path.write_text(
                json.dumps(self._state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            _logger.info("[LITE-V1] StateLedger 저장: ep=%d", self._state.get("last_updated_ep", 0))
        except Exception as e:
            _logger.error("[LITE-V1] StateLedger 저장 실패: %s", e)

    # ── update_from_arc ─────────────────────────────────────

    def update_from_arc(self, arc_no: int, arc_text: str):
        """Arc 분배표의 '## Arc 종료 상태' 섹션을 파싱하여 상태 갱신."""
        try:
            # "## Arc 종료 상태" 이후 텍스트 추출
            m = re.search(r"##\s*Arc\s*종료\s*상태\s*\n([\s\S]+?)(?:\n##|\Z)", arc_text)
            if not m:
                _logger.debug("[LITE-V1] Arc#%d: 종료 상태 섹션 없음", arc_no)
                return

            section = m.group(1)

            # 주인공 능력/레벨
            lm = re.search(r"주인공\s*능력[/／]레벨\s*[:：]\s*(.+)", section)
            if lm:
                self._state["protagonist"]["level"] = lm.group(1).strip()

            # 주인공 상태/위치
            sm = re.search(r"주인공\s*상태[/／]위치\s*[:：]\s*(.+)", section)
            if sm:
                self._state["protagonist"]["location"] = sm.group(1).strip()

            # 주요 변화 (있으면 로그)
            cm = re.search(r"주요\s*변화\s*[:：]\s*(.+)", section)
            if cm:
                _logger.info("[LITE-V1] Arc#%d 주요변화: %s", arc_no, cm.group(1).strip()[:100])

            # 등장인물 섹션에서 NPC 등록
            self._extract_npcs_from_text(arc_text, arc_no)

        except Exception as e:
            _logger.warning("[LITE-V1] Arc#%d update_from_arc 실패: %s", arc_no, e)

    # ── update_from_blueprint ───────────────────────────────

    def update_from_blueprint(self, ep_num: int, bp_text: str):
        """Blueprint의 '## 종료 상태' 섹션을 파싱하여 상태 갱신."""
        try:
            # "## 종료 상태" 이후 텍스트
            m = re.search(r"##\s*종료\s*상태\s*\n([\s\S]+?)(?:\n##|\Z)", bp_text)
            if not m:
                _logger.debug("[LITE-V1] ep%d: 종료 상태 섹션 없음", ep_num)
                # 종료 상태 없어도 등장인물은 추출
                self._extract_npcs_from_text(bp_text, ep_num)
                return

            section = m.group(1)

            # 주인공 능력/상태
            pm = re.search(r"주인공\s*능력[/／]상태\s*[:：]\s*(.+)", section)
            if pm:
                val = pm.group(1).strip()
                # "능력/상태"가 레벨 정보를 포함할 수 있음
                self._state["protagonist"]["level"] = val

            # 주요 변화
            cm = re.search(r"주요\s*변화\s*[:：]\s*(.+)", section)
            if cm:
                _logger.info("[LITE-V1] ep%d 주요변화: %s", ep_num, cm.group(1).strip()[:100])

            # 등장인물 섹션에서 NPC 등록
            self._extract_npcs_from_text(bp_text, ep_num)

            # last_updated_ep 갱신
            if ep_num > self._state.get("last_updated_ep", 0):
                self._state["last_updated_ep"] = ep_num

        except Exception as e:
            _logger.warning("[LITE-V1] ep%d update_from_blueprint 실패: %s", ep_num, e)

    # ── update_from_manuscript ──────────────────────────────

    def update_from_manuscript(self, ep_num: int, ms_text: str):
        """원고 텍스트를 regex로 파싱 — 사망 감지 + 체인 링크 갱신."""
        try:
            # ── 사망 감지 ──
            death_patterns = [
                r"([\w가-힣]+)[이가은는]?\s*(?:죽|사망|숨[을를]?\s*거두|"
                r"최후를?\s*맞|절명|숨지|전사|목숨[을를]?\s*잃|생을?\s*마감)",
                r"([\w가-힣]+)[의]?\s*(?:시체|시신|주검|유해)",
            ]
            protagonist_name = self._state["protagonist"].get("name", "")
            dead_npcs = self._state.setdefault("dead_npcs", {})
            alive_npcs = self._state.setdefault("alive_npcs", {})

            for pattern in death_patterns:
                for match in re.finditer(pattern, ms_text):
                    name = match.group(1).strip()
                    # 조사 제거: 패턴의 [이가은는]?가 greedy로
                    # 이름에 흡수되는 경우 대비
                    name = re.sub(r"[이가은는의]$", "", name)
                    # 너무 짧은 이름 무시 (1글자 이하)
                    if len(name) <= 1:
                        continue
                    # 주인공 제외
                    if protagonist_name and name == protagonist_name:
                        continue
                    # 이미 사망 처리된 NPC 무시
                    if name in dead_npcs:
                        continue

                    dead_npcs[name] = {
                        "ep": ep_num,
                        "cause": match.group(0).strip()[:100],
                    }
                    # alive_npcs에서 제거
                    if name in alive_npcs:
                        del alive_npcs[name]
                    _logger.info("[LITE-V1] ep%d 사망 감지: %s", ep_num, name)

            # ── 체인 링크 갱신 ──
            chain = self._state.setdefault(
                "chain_link",
                {
                    "ep": 0,
                    "ending": "",
                    "location": "",
                    "cliffhanger": "",
                },
            )

            # 마지막 2000자에서 마지막 장면 전환('%%%%') 이후 텍스트
            tail = ms_text[-2000:] if len(ms_text) > 2000 else ms_text
            last_scene_break = tail.rfind("%%%%")
            if last_scene_break >= 0:
                ending_text = tail[last_scene_break + 4 :].strip()
            else:
                # 장면 전환 없으면 마지막 500자
                ending_text = ms_text[-500:].strip()

            chain["ep"] = ep_num
            chain["ending"] = ending_text[:500]

            # last_updated_ep 갱신
            if ep_num > self._state.get("last_updated_ep", 0):
                self._state["last_updated_ep"] = ep_num

        except Exception as e:
            _logger.warning("[LITE-V1] ep%d update_from_manuscript 실패: %s", ep_num, e)

    # ── update_from_director ────────────────────────────────

    def update_from_director(self, director_resp: str, ep_num: int):
        """Director 응답에서 모순/이름오류 파싱 → contradictions_log 추가."""
        try:
            log_list = self._state.setdefault("contradictions_log", [])

            for field in ["모순", "이름오류"]:
                m = re.search(rf"{field}\s*[:：]\s*(.+?)(?:\n|$)", director_resp)
                if m and m.group(1).strip() not in ("없음", "없음."):
                    log_list.append(
                        {
                            "ep": ep_num,
                            "issue": f"[{field}] {m.group(1).strip()[:200]}",
                        }
                    )

            # 최대 50개 유지
            if len(log_list) > 50:
                self._state["contradictions_log"] = log_list[-50:]

        except Exception as e:
            _logger.warning("[LITE-V1] ep%d update_from_director 실패: %s", ep_num, e)

    # ── get_state_summary ───────────────────────────────────

    def get_state_summary(self, max_chars: int = 3000) -> str:
        """프롬프트 주입용 요약 텍스트 생성."""
        s = self._state
        last_ep = s.get("last_updated_ep", 0)
        if last_ep == 0:
            return ""

        parts = []
        parts.append(f"=== 세계 상태 (제{last_ep}화 기준) ===")

        # 주인공
        p = s.get("protagonist", {})
        parts.append("\n[주인공]")
        if p.get("name"):
            parts.append(f"이름: {p['name']}")
        if p.get("location"):
            parts.append(f"위치: {p['location']}")
        if p.get("level"):
            parts.append(f"능력/레벨: {p['level']}")
        if p.get("injuries") and p["injuries"] != "정상":
            parts.append(f"부상: {p['injuries']}")

        # 생존 NPC
        alive = s.get("alive_npcs", {})
        if alive:
            parts.append(f"\n[생존 NPC ({len(alive)}명)]")
            relationships = s.get("relationships", {})
            for name, info in list(alive.items())[:20]:
                rel = relationships.get(name, info.get("relation", ""))
                rel_str = f"관계={rel}" if rel else ""
                parts.append(f"- {name}: {rel_str}".rstrip(": "))

        # 사망 NPC
        dead = s.get("dead_npcs", {})
        if dead:
            parts.append(f"\n[사망 NPC ({len(dead)}명) -- 절대 등장 금지]")
            for name, info in dead.items():
                ep = info.get("ep", "?")
                cause = info.get("cause", "")
                parts.append(f"- {name} (제{ep}화, {cause})")

        # 보유 아이템
        items = s.get("active_items", [])
        if items:
            parts.append("\n[보유 아이템]")
            parts.append(f"- {', '.join(items[:20])}")

        # 최근 모순 기록
        contradictions = s.get("contradictions_log", [])
        if contradictions:
            recent = contradictions[-5:]
            parts.append("\n[최근 모순 기록]")
            for c in recent:
                parts.append(f"- 제{c['ep']}화: {c['issue']}")

        result = "\n".join(parts)

        # max_chars 이내로 truncation
        if len(result) > max_chars:
            result = result[: max_chars - 20] + "\n\n[...이하 생략...]"

        return result

    # ── get_dead_npc_warning ────────────────────────────────

    def get_dead_npc_warning(self) -> str:
        """Director 프롬프트에 주입할 사망 NPC 하드 경고."""
        dead = self._state.get("dead_npcs", {})
        if not dead:
            return ""

        lines = [
            "★★★ [사망 NPC -- 절대 등장 금지] ★★★",
            "다음 NPC들은 이미 사망했습니다. 어떤 형태로든 등장시키면 0점 처리합니다:",
        ]
        for name, info in dead.items():
            ep = info.get("ep", "?")
            lines.append(f"- {name} (제{ep}화 사망)")

        return "\n".join(lines)

    # ── get_chain_link ──────────────────────────────────────

    def get_chain_link(self) -> str:
        """직전 화 종료 상태 요약."""
        chain = self._state.get("chain_link", {})
        if chain.get("ep", 0) == 0:
            return ""

        parts = [f"[직전 화 종료 상태 (제{chain['ep']}화)]"]

        if chain.get("ending"):
            parts.append(f"- 마지막 장면: {chain['ending'][:300]}")
        if chain.get("location"):
            parts.append(f"- 위치: {chain['location']}")
        if chain.get("cliffhanger"):
            parts.append(f"- 클리프행어: {chain['cliffhanger']}")

        parts.append("")
        parts.append("★ 이 상태에서 자연스럽게 이어서 시작할 것")

        return "\n".join(parts)

    # ── property ────────────────────────────────────────────

    @property
    def last_updated_ep(self) -> int:
        return self._state.get("last_updated_ep", 0)

    # ── 내부 헬퍼 ───────────────────────────────────────────

    def _extract_npcs_from_text(self, text: str, ep_num: int):
        """텍스트에서 '등장인물' 섹션의 NPC 이름을 추출하여 alive_npcs에 등록."""
        try:
            alive = self._state.setdefault("alive_npcs", {})
            dead = self._state.get("dead_npcs", {})

            # "등장인물:" 또는 "- 등장인물:" 패턴 검색
            matches = re.finditer(r"등장인물\s*[:：]\s*(.+?)(?:\n|$)", text)
            for m in matches:
                names_str = m.group(1).strip()
                # 쉼표/슬래시/중점으로 분리
                names = re.split(r"[,，/·\s]+", names_str)
                for raw_name in names:
                    name = raw_name.strip().strip("-").strip()
                    # 불필요한 접미사 제거 (예: "주인공(김무명)" → 스킵)
                    name = re.sub(r"\(.+?\)", "", name).strip()
                    if len(name) < 2 or len(name) > 10:
                        continue
                    # 일반 명사 필터
                    if name in ("주인공", "아군", "적군", "부하", "졸개", "기타", "등", "외", "없음", "유지"):
                        continue
                    # 이미 사망한 NPC는 등록하지 않음
                    if name in dead:
                        continue
                    # 신규 등록 (기존 있으면 덮어쓰지 않음)
                    if name not in alive:
                        alive[name] = {
                            "role": "",
                            "relation": "",
                            "first_ep": ep_num,
                        }
        except Exception as e:
            _logger.debug("[LITE-V1] NPC 추출 실패 (ep%d): %s", ep_num, e)
