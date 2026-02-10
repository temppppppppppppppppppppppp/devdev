"""
[V64.P3] StateTracker Plots & Entity Sub-module
완결된 플롯 추적 + 비-NPC 엔티티 명칭 일관성 관리.
[V66.1] 시간선 추적 + 아이템 regex 폴백 추가.

StateTracker에서 resolved_plots 및 entity_name_registry 관련 메서드만 분리.
모든 공유 상태는 self.tracker를 통해 접근.
"""

import re
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════
# [V66.1] C-2: Module-level compiled regex patterns
#  메서드 내부 re.compile 호출을 모듈 상수로 이동 (~25ms/Arc 절감)
# ═══════════════════════════════════════════════════════════════

# --- check_destroyed_entity_in_manuscript (동적 entity 이름이므로 compile은 유지하되, 고정 접두/접미 부분만 상수화) ---
_RE_DESTROYED_ACTIVITY_SUFFIX = r'[이가은는에서의]?\s*(?:공격|방어|전투|활동|지원|파견|출격|모집|개방)'
_RE_DESTROYED_REVIVE_PREFIX = r'(?:건재|부활|재건)[한된]\s*'

# --- check_time_consistency ---
_RE_RAPID_RECOVERY = re.compile(
    r'중상.{0,100}?(?:다음\s*날|이튿날|하루\s*만에).{0,60}?(?:완치|멀쩡|회복|낫|치유)',
    re.DOTALL
)
_RE_CRITICAL_RECOVERY = re.compile(
    r'위독.{0,100}?(?:다음\s*날|이튿날|하루|사흘).{0,60}?(?:완치|멀쩡|회복|일어서|걸어)',
    re.DOTALL
)
_RE_IMPOSSIBLE_TRAVEL = re.compile(
    r'(\d+)\s*일\s*(?:거리|걸리는|소요).{0,60}?(?:시간\s*만에|순식간|단숨에|눈\s*깜짝할\s*사이)',
    re.DOTALL
)

# --- _regex_extract_major_items ---
_RE_ITEM_ACQUIRE = [
    re.compile(r'([가-힣]{2,10}(?:검|도|창|궁|부|낫|갑|패|환|단|서|전|경|보|인))[을를]?\s*(?:획득|입수|얻|손에\s*넣|전수받|발견)'),
    re.compile(r'(?:획득|입수|발견)[한하]?\s*([가-힣]{2,10}(?:검|도|창|궁|부|낫|갑|패|환|단|서|전|경|보|인))'),
]
_RE_ITEM_LOSE = [
    re.compile(r'([가-힣]{2,10}(?:검|도|창|궁|부|낫|갑|패|환|단|서|전|경|보|인))[을를]?\s*(?:잃|분실|파괴|소모|사용|부서|깨뜨)'),
    re.compile(r'(?:잃어버린|파괴된|소모된)\s*([가-힣]{2,10}(?:검|도|창|궁|부|낫|갑|패|환|단|서|전|경|보|인))'),
]

# --- _regex_extract_commitments ---
_RE_COMMIT = [
    re.compile(r'([가-힣]{2,10})[에와과]게?\s*(?:약속|맹세|서약|다짐)'),
    re.compile(r'(?:반드시|기필코|꼭)\s*(.{2,20}?)(?:하겠|할\s*것|해주겠|갚겠)'),
    re.compile(r'([가-힣]{2,10})[에의]게?\s*(?:빚|은혜|보답|보은)'),
]


class StateTrackerPlots:
    """[V64.P3] 완결된 플롯 + 엔티티 명칭 서브모듈"""

    # [V66.1] F-1: 한국어 시간 표현 regex 패턴
    _TIME_ELAPSED_PATTERNS = [
        # "며칠", "몇 달", "수 년" 등
        re.compile(r'(며칠|몇\s*[달일년주]|수\s*[달일년주]|하루|이틀|사흘|나흘|닷새)'),
        # "한 달 후", "세 달 뒤", "두 해 후"
        re.compile(r'([한두세네다여일이삼사오육칠팔구십백]\s*[달일년주시개월]\s*(?:후|뒤|전|만에|이\s*지나))'),
        # "3일 후", "7일 뒤", "2개월 후"
        re.compile(r'(\d+\s*(?:일|개월|달|년|주|시간|분)\s*(?:후|뒤|전|만에|이?\s*지나))'),
        # "다음 날", "그 다음날", "이튿날"
        re.compile(r'(다음\s*날|그\s*다음\s*날|이튿날|사흘\s*후|닷새\s*후)'),
    ]

    _TIME_SEASON_PATTERNS = [
        re.compile(r'(봄|여름|가을|겨울|초봄|초여름|초가을|초겨울|늦봄|늦여름|늦가을|늦겨울|한여름|한겨울)'),
    ]

    _TIME_OF_DAY_PATTERNS = [
        re.compile(r'(새벽|아침|오전|정오|오후|저녁|밤|한밤중|자정|해질\s*무렵|해뜰\s*무렵|황혼|동트기\s*전)'),
    ]

    _TIME_SPECIFIC_DATE_PATTERNS = [
        # 장르별 표현: "대회 3일차", "각성 후 15일차", "마왕 부활 후 2년" 등
        re.compile(r'(\S+\s*\d+\s*일차)'),
        re.compile(r'(\d{4}년\s*\d{1,2}월)'),
    ]

    def __init__(self, tracker):
        self.tracker = tracker  # back-reference to main StateTracker

    # ═══════════════════════════════════════════════════════════════
    # [V62.7] 완결된 플롯 추적
    # ═══════════════════════════════════════════════════════════════

    def extract_resolved_plots_from_arc(self, arc: dict) -> List[Dict]:
        """
        [V62.7] Arc에서 resolved_plots 추출 및 누적.
        state_changes.resolved_plots 필드에서 직접 읽기.
        """
        arc_no = arc.get("arc_no", 0)
        plots = []

        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            resolved = state_changes.get("resolved_plots", [])
            if isinstance(resolved, list):
                for plot in resolved:
                    if isinstance(plot, dict) and plot.get("plot"):
                        entry = {
                            "plot": str(plot["plot"]),
                            "resolution": str(plot.get("resolution", "")),
                            "episode": plot.get("episode", 0),
                            "arc_no": arc_no
                        }
                        plots.append(entry)
                        # 누적 (중복 방지: 같은 plot+arc_no 조합)
                        if not any(
                            p.get("plot") == entry["plot"] and p.get("arc_no") == arc_no
                            for p in self.tracker.resolved_plots
                        ):
                            self.tracker.resolved_plots.append(entry)
        return plots

    def get_resolved_plots_summary(self) -> str:
        """[V62.7] 완결된 플롯 목록 -> 프롬프트 주입용 문자열"""
        if not self.tracker.resolved_plots:
            return ""
        lines = ["[V62.7] 완결된 플롯 - 동일/유사 갈등 재생성 금지:"]
        for p in self.tracker.resolved_plots:
            lines.append(
                f"  - [{p.get('plot','')}] "
                f"Arc {p.get('arc_no','?')} Ep{p.get('episode','?')}: "
                f"{p.get('resolution','')}"
            )
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66] 조직/장소 파괴 추적
    # ═══════════════════════════════════════════════════════════════

    def extract_entity_destructions_from_arc(self, arc: dict) -> List[Dict]:
        """[V66] Arc에서 entity_destructions 추출 및 누적."""
        arc_no = arc.get("arc_no", 0)
        results = []

        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            destructions = state_changes.get("entity_destructions", [])
            if isinstance(destructions, list):
                for d in destructions:
                    if isinstance(d, dict) and d.get("name"):
                        entry = {
                            "name": str(d["name"]),
                            "type": str(d.get("type", "unknown")),
                            "cause": str(d.get("cause", "")),
                            "episode": d.get("episode", 0),
                            "arc_no": arc_no,
                        }
                        results.append(entry)
                        # 중복 방지
                        if not any(
                            e.get("name") == entry["name"] and e.get("arc_no") == arc_no
                            for e in self.tracker.entity_destructions
                        ):
                            self.tracker.entity_destructions.append(entry)
        return results

    def register_entity_destruction(self, name: str, entity_type: str, cause: str, arc_no: int):
        """[V66] 수동 파괴 등록."""
        entry = {"name": name, "type": entity_type, "cause": cause, "arc_no": arc_no}
        if not any(e.get("name") == name for e in self.tracker.entity_destructions):
            self.tracker.entity_destructions.append(entry)

    def check_destroyed_entity_in_manuscript(self, content: str) -> List[Dict]:
        """[V66] 파괴된 조직/장소가 원고에서 활동 중으로 등장하는지 검사."""
        warnings = []
        if not self.tracker.entity_destructions or not content:
            return warnings
        for entity in self.tracker.entity_destructions:
            name = entity.get("name", "")
            if not name or len(name) < 2:
                continue
            # 단순 등장은 허용 (회상 등), 활동 표현 패턴 검사
            # [V66.1] C-2: 동적 entity 이름이므로 per-entity compile 불가피하지만,
            #  패턴 문자열 상수는 모듈 레벨에서 정의
            _esc = re.escape(name)
            activity_patterns = [
                re.compile(_esc + _RE_DESTROYED_ACTIVITY_SUFFIX),
                re.compile(_RE_DESTROYED_REVIVE_PREFIX + _esc),
            ]
            for pat in activity_patterns:
                if pat.search(content):
                    warnings.append({
                        "entity": name,
                        "type": entity.get("type", "?"),
                        "destroyed_arc": entity.get("arc_no", "?"),
                        "severity": "WARNING",
                        "message": f"파괴된 {entity.get('type', '엔티티')} '{name}'이(가) 활동 중으로 묘사됨",
                    })
                    break
        return warnings

    def get_entity_destruction_summary(self) -> str:
        """[V66] 파괴된 조직/장소 목록 → 프롬프트 주입용 문자열."""
        if not self.tracker.entity_destructions:
            return ""
        lines = ["[V66] 파괴된 조직/장소 - 활동 상태로 재등장 금지:"]
        for e in self.tracker.entity_destructions:
            lines.append(
                f"  - {e.get('name','')} ({e.get('type','?')}) "
                f"Arc {e.get('arc_no','?')}: {e.get('cause','')}"
            )
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66] 아이템 상태 레지스트리
    # ═══════════════════════════════════════════════════════════════

    def register_item_state(self, item_name: str, arc_no: int, description: str = "",
                           source: str = "", condition: str = "정상"):
        """[V66] 아이템 상태 등록/업데이트."""
        if not item_name or len(item_name) < 2:
            return
        existing = self.tracker.item_state_registry.get(item_name)
        entry = {
            "name": item_name,
            "description": description or (existing or {}).get("description", ""),
            "source": source or (existing or {}).get("source", ""),
            "condition": condition,
            "arc_no": arc_no,
        }
        if existing:
            # 이전 상태 기록
            if existing.get("condition") and existing["condition"] != condition:
                entry["prev_condition"] = existing["condition"]
                entry["prev_arc"] = existing.get("arc_no", 0)
        self.tracker.item_state_registry[item_name] = entry

    def extract_item_states_from_arc(self, arc: dict) -> List[Dict]:
        """
        [V66] Arc의 state_changes.major_items에서 아이템 상태 추출.
        [V66.1] F-3: state_changes가 비어있으면 regex 폴백 사용.
        """
        arc_no = arc.get("arc_no", 0)
        results = []
        state_changes = arc.get("state_changes", {})
        items_from_sc = []
        if isinstance(state_changes, dict):
            items_from_sc = state_changes.get("major_items", [])
            if isinstance(items_from_sc, list):
                for item in items_from_sc:
                    if isinstance(item, dict) and item.get("name"):
                        name = str(item["name"])
                        action = str(item.get("action", ""))
                        condition = "정상"
                        if action in ("분실", "파괴", "소모"):
                            condition = action
                        self.register_item_state(
                            name, arc_no,
                            description=item.get("description", ""),
                            source=item.get("source", ""),
                            condition=condition,
                        )
                        results.append({"name": name, "action": action, "arc_no": arc_no})

        # [V66.1] F-3: regex 폴백 -- state_changes.major_items가 비어있을 때
        if not results:
            tactical = arc.get("tactical_doc", "")
            if isinstance(tactical, dict):
                tactical = "\n".join(str(v) for v in tactical.values() if v)
            if tactical:
                regex_items = self._regex_extract_major_items(tactical)
                for item in regex_items:
                    name = item["name"]
                    action = item["action"]
                    condition = "정상"
                    if action in ("분실", "파괴", "소모"):
                        condition = action
                    self.register_item_state(name, arc_no, condition=condition)
                    results.append({"name": name, "action": action, "arc_no": arc_no})

        return results

    def get_item_state_summary(self) -> str:
        """[V66] 아이템 상태 목록 → 프롬프트 주입용 문자열."""
        if not self.tracker.item_state_registry:
            return ""
        lines = ["[V66] 아이템 상태 (손상/소모 아이템은 멀쩡한 것처럼 사용 금지):"]
        for name, info in self.tracker.item_state_registry.items():
            cond = info.get("condition", "정상")
            desc = info.get("description", "")
            parts = [f"  - {name}: 상태={cond}"]
            if desc:
                parts.append(f"({desc[:30]})")
            lines.append(" ".join(parts))
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66] 플롯 서스펜션 추적
    # ═══════════════════════════════════════════════════════════════

    def register_active_plot(self, plot_name: str, arc_no: int, status: str = "active"):
        """[V66] 활성 플롯 등록. status: active/in_progress/suspended/resolved"""
        if not plot_name:
            return
        existing = self.tracker.active_plots.get(plot_name)
        entry = {
            "plot": plot_name,
            "status": status,
            "first_arc": (existing or {}).get("first_arc", arc_no),
            "last_mention_arc": arc_no,
        }
        if existing and existing.get("status") != status:
            entry["prev_status"] = existing.get("status", "")
        self.tracker.active_plots[plot_name] = entry

    def update_plot_mentions_from_arc(self, arc: dict) -> List[Dict]:
        """[V66] Arc에서 언급된 플롯들의 last_mention_arc 갱신 + 신규 플롯 등록."""
        arc_no = arc.get("arc_no", 0)
        updated = []

        state_changes = arc.get("state_changes", {})
        if not isinstance(state_changes, dict):
            return updated

        # resolved_plots → resolved 상태로 전환
        resolved = state_changes.get("resolved_plots", [])
        if isinstance(resolved, list):
            for rp in resolved:
                if isinstance(rp, dict) and rp.get("plot"):
                    plot_name = str(rp["plot"])
                    self.register_active_plot(plot_name, arc_no, status="resolved")
                    updated.append({"plot": plot_name, "status": "resolved"})

        # tactical_doc에서 활성 플롯 추출 (키워드: 갈등, 계략, 목표, 복수 등)
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = str(tactical)

        # 기존 활성 플롯 중 이번 arc tactical_doc에 언급되면 last_mention 갱신
        for plot_name, info in list(self.tracker.active_plots.items()):
            if info.get("status") == "resolved":
                continue
            if plot_name in tactical:
                info["last_mention_arc"] = arc_no
                updated.append({"plot": plot_name, "status": "mentioned"})

        return updated

    def check_suspended_plots(self, current_arc_no: int, threshold: int = 3) -> List[Dict]:
        """[V66] 3+ Arc 방치된 플롯 감지 → WARNING."""
        warnings = []
        for plot_name, info in self.tracker.active_plots.items():
            if info.get("status") == "resolved":
                continue
            last_mention = info.get("last_mention_arc", 0)
            gap = current_arc_no - last_mention
            if gap >= threshold:
                info["status"] = "suspended"
                warnings.append({
                    "plot": plot_name,
                    "last_mention_arc": last_mention,
                    "gap": gap,
                    "severity": "WARNING",
                    "message": f"플롯 '{plot_name}'이 {gap}개 Arc 동안 미언급 (Arc {last_mention} 이후)",
                })
        return warnings

    def get_plot_suspension_summary(self, current_arc_no: int) -> str:
        """[V66] 플롯 서스펜션 상태 → 프롬프트 주입용 문자열."""
        if not self.tracker.active_plots:
            return ""
        active_lines = []
        suspended_lines = []
        for plot_name, info in self.tracker.active_plots.items():
            status = info.get("status", "active")
            if status == "resolved":
                continue
            last_arc = info.get("last_mention_arc", 0)
            gap = current_arc_no - last_arc
            line = f"  - {plot_name} (마지막 언급: Arc {last_arc}, {gap}개 Arc 전)"
            if status == "suspended" or gap >= 3:
                suspended_lines.append(f"  - {plot_name} -- {gap}개 Arc 방치! 재개/해결 필요")
            else:
                active_lines.append(line)

        if not active_lines and not suspended_lines:
            return ""

        lines = []
        if suspended_lines:
            lines.append("[V66] 방치된 플롯 (재개/해결 필요):")
            lines.extend(suspended_lines)
        if active_lines:
            lines.append("[V66] 진행 중 플롯:")
            lines.extend(active_lines)
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] F-1: 시간선 추적 시스템
    # ═══════════════════════════════════════════════════════════════

    def register_time_marker(self, arc_no: int, episode: int,
                             marker_type: str, description: str):
        """
        [V66.1] 시간 마커 등록.

        Args:
            arc_no: Arc 번호
            episode: 에피소드 번호
            marker_type: "elapsed_time" | "season" | "time_of_day" | "specific_date"
            description: 시간 표현 (예: "3일 경과", "겨울", "새벽")
        """
        if not description or marker_type not in (
            "elapsed_time", "season", "time_of_day", "specific_date"
        ):
            return

        marker = {
            "arc_no": arc_no,
            "episode": episode,
            "type": marker_type,
            "description": description.strip(),
        }

        # 중복 방지: 같은 arc+episode+description 조합
        for existing in self.tracker.in_world_timeline:
            if (existing.get("arc_no") == arc_no
                    and existing.get("episode") == episode
                    and existing.get("description") == marker["description"]):
                return

        self.tracker.in_world_timeline.append(marker)

        # [V66.1] C-3: 최대 100개 마커 유지 (200→100 축소, 메모리 안정화)
        while len(self.tracker.in_world_timeline) > 100:
            self.tracker.in_world_timeline.pop(0)

    def extract_time_markers_from_arc(self, arc_data: dict) -> List[Dict]:
        """
        [V66.1] Arc에서 시간 마커 추출 및 등록.
        우선순위: state_changes["time_markers"] > regex 폴백.

        Args:
            arc_data: Arc 데이터 (state_changes 또는 tactical_doc 포함)

        Returns:
            추출된 시간 마커 목록
        """
        arc_no = arc_data.get("arc_no", 0)
        results = []

        # 1순위: state_changes.time_markers 필드 직접 읽기
        state_changes = arc_data.get("state_changes", {})
        if isinstance(state_changes, dict):
            time_markers = state_changes.get("time_markers", [])
            if isinstance(time_markers, list) and time_markers:
                for tm in time_markers:
                    if isinstance(tm, dict):
                        m_type = tm.get("type", "elapsed_time")
                        desc = tm.get("description", "")
                        episode = tm.get("episode", arc_no)
                        if desc:
                            self.register_time_marker(arc_no, episode, m_type, desc)
                            results.append({
                                "arc_no": arc_no, "episode": episode,
                                "type": m_type, "description": desc
                            })
                if results:
                    return results

        # 2순위: tactical_doc에서 regex 폴백
        tactical = arc_data.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        if not tactical:
            return results

        # elapsed_time 패턴
        for pattern in self._TIME_ELAPSED_PATTERNS:
            for match in pattern.finditer(tactical):
                desc = match.group(1).strip()
                self.register_time_marker(arc_no, arc_no, "elapsed_time", desc)
                results.append({
                    "arc_no": arc_no, "episode": arc_no,
                    "type": "elapsed_time", "description": desc
                })

        # season 패턴
        for pattern in self._TIME_SEASON_PATTERNS:
            for match in pattern.finditer(tactical):
                desc = match.group(1).strip()
                self.register_time_marker(arc_no, arc_no, "season", desc)
                results.append({
                    "arc_no": arc_no, "episode": arc_no,
                    "type": "season", "description": desc
                })

        # time_of_day 패턴
        for pattern in self._TIME_OF_DAY_PATTERNS:
            for match in pattern.finditer(tactical):
                desc = match.group(1).strip()
                self.register_time_marker(arc_no, arc_no, "time_of_day", desc)
                results.append({
                    "arc_no": arc_no, "episode": arc_no,
                    "type": "time_of_day", "description": desc
                })

        # specific_date 패턴
        for pattern in self._TIME_SPECIFIC_DATE_PATTERNS:
            for match in pattern.finditer(tactical):
                desc = match.group(1).strip()
                self.register_time_marker(arc_no, arc_no, "specific_date", desc)
                results.append({
                    "arc_no": arc_no, "episode": arc_no,
                    "type": "specific_date", "description": desc
                })

        return results

    def get_time_timeline_summary(self) -> str:
        """
        [V66.1] 최근 20개 시간 마커를 mandatory_context 주입용 문자열로 반환.

        Returns:
            포맷된 시간선 요약 문자열
        """
        if not self.tracker.in_world_timeline:
            return ""

        recent = self.tracker.in_world_timeline[-20:]

        lines = ["[V66.1] 작중 시간선 (시간 모순 금지):"]
        for m in recent:
            arc = m.get("arc_no", "?")
            ep = m.get("episode", "?")
            m_type = m.get("type", "?")
            desc = m.get("description", "")
            type_label = {
                "elapsed_time": "경과",
                "season": "계절",
                "time_of_day": "시각",
                "specific_date": "날짜",
            }.get(m_type, m_type)
            lines.append(f"  - Arc {arc} Ep{ep}: [{type_label}] {desc}")

        return "\n".join(lines)

    def check_time_consistency(self, manuscript: str,
                               current_timeline: Optional[List[Dict]] = None) -> List[Dict]:
        """
        [V66.1] 원고 내 시간 모순 검사.

        검사 항목:
        - 중상인데 다음 날 완치 (급속 회복)
        - 불가능한 이동 시간 (3일 거리를 1시간에)
        - 계절 모순 (겨울인데 여름 묘사)

        Args:
            manuscript: 검사할 원고 텍스트
            current_timeline: 현재까지의 시간 마커 (None이면 self.tracker.in_world_timeline 사용)

        Returns:
            시간 모순 경고 목록 [{type, severity, description}]
        """
        warnings = []
        if not manuscript:
            return warnings

        timeline = current_timeline or self.tracker.in_world_timeline

        # 1) 급속 회복 검사: "중상" + "다음 날" + "완치/멀쩡/회복" 패턴
        # [V66.1] C-2: module-level compiled pattern
        if _RE_RAPID_RECOVERY.search(manuscript):
            warnings.append({
                "type": "rapid_recovery",
                "severity": "WARNING",
                "description": "중상 상태에서 하루 만에 완치됨 -- 치료 과정 묘사 필요",
            })

        # 위독 + 단기 회복
        # [V66.1] C-2: module-level compiled pattern
        if _RE_CRITICAL_RECOVERY.search(manuscript):
            warnings.append({
                "type": "rapid_recovery",
                "severity": "CRITICAL",
                "description": "위독 상태에서 단기간에 회복됨 -- 비현실적 회복",
            })

        # 2) 계절 모순 검사: 최근 타임라인의 계절과 원고 내 계절 표현 비교
        recent_seasons = set()
        for m in (timeline or []):
            if m.get("type") == "season":
                recent_seasons.add(m.get("description", ""))

        season_contradictions = {
            "겨울": ["한여름", "뜨거운 여름", "무더위"],
            "한겨울": ["한여름", "뜨거운 여름", "무더위", "여름"],
            "여름": ["한겨울", "눈보라", "설한풍"],
            "한여름": ["한겨울", "눈보라", "설한풍", "겨울"],
        }

        for season in recent_seasons:
            contradicting = season_contradictions.get(season, [])
            for contra in contradicting:
                if contra in manuscript:
                    warnings.append({
                        "type": "season_contradiction",
                        "severity": "WARNING",
                        "description": f"시간선에 '{season}'으로 기록되었으나 원고에 '{contra}' 표현 등장",
                    })

        # 3) 불가능한 이동 시간: "N일 거리" + "시간/순식간/단숨" 패턴
        # [V66.1] C-2: module-level compiled pattern
        for match in _RE_IMPOSSIBLE_TRAVEL.finditer(manuscript):
            days = int(match.group(1))
            if days >= 2:
                warnings.append({
                    "type": "impossible_travel",
                    "severity": "WARNING",
                    "description": f"{days}일 거리를 순식간에 이동 -- 이동 수단 설명 필요",
                })

        return warnings

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] F-3: 아이템 regex 폴백
    # ═══════════════════════════════════════════════════════════════

    def _regex_extract_major_items(self, tactical_doc: str) -> List[Dict]:
        """
        [V66.1] tactical_doc에서 주요 아이템 획득/소모를 regex로 추출.
        state_changes.major_items가 비어있을 때 폴백으로 사용.

        Args:
            tactical_doc: Arc 전술 문서 텍스트

        Returns:
            아이템 목록 [{"name": ..., "action": ..., "episode": 0}]
        """
        if not tactical_doc:
            return []

        items = []
        seen = set()

        # [V66.1] C-2: module-level compiled patterns
        acquire_patterns = _RE_ITEM_ACQUIRE
        lose_patterns = _RE_ITEM_LOSE

        exclude_words = {'주인공', '상대방', '자신', '적수', '적', '그', '그녀'}

        for pattern in acquire_patterns:
            for match in pattern.finditer(tactical_doc):
                name = match.group(1).strip()
                if name and len(name) >= 2 and name not in exclude_words and name not in seen:
                    seen.add(name)
                    items.append({"name": name, "action": "획득", "episode": 0})

        for pattern in lose_patterns:
            for match in pattern.finditer(tactical_doc):
                name = match.group(1).strip()
                if name and len(name) >= 2 and name not in exclude_words and name not in seen:
                    seen.add(name)
                    items.append({"name": name, "action": "분실", "episode": 0})

        return items

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] 약속/맹세(Commitment) 추적
    # ═══════════════════════════════════════════════════════════════

    def register_commitment(self, arc_no: int, episode: int, parties: List[str],
                            description: str, deadline_hint: str = ""):
        """
        [V66.1] 약속/맹세 등록.

        Args:
            arc_no: Arc 번호
            episode: 에피소드 번호
            parties: 관련자 목록 (예: ["주인공", "흑도"])
            description: 약속 내용 (예: "3일 후 금 100냥 상환")
            deadline_hint: 이행 기한 힌트 (예: "3일 후", "다음 Arc")
        """
        if not description or not parties:
            return

        # 중복 방지: 같은 description + arc_no 조합
        for existing in self.tracker.pending_commitments:
            if (existing.get("description") == description
                    and existing.get("arc_no") == arc_no):
                return

        entry = {
            "arc_no": arc_no,
            "episode": episode,
            "parties": parties,
            "description": description,
            "deadline_hint": deadline_hint,
            "status": "pending",  # pending | fulfilled | broken
        }
        self.tracker.pending_commitments.append(entry)
        print(f"      [V66.1] 약속 등록: {description} (당사자: {', '.join(parties)}, Arc {arc_no})")

        # [V66.1] C-3: 해결된(fulfilled/broken) 약속 주기적 정리 (50개 초과 시)
        if len(self.tracker.pending_commitments) > 50:
            self.tracker.pending_commitments = [
                c for c in self.tracker.pending_commitments
                if c.get("status") == "pending"
            ]

    def extract_commitments_from_arc(self, arc_data: dict) -> List[Dict]:
        """
        [V66.1] Arc에서 약속/맹세 추출 및 등록.
        우선순위: state_changes["commitments"] > regex 폴백.

        Args:
            arc_data: Arc 데이터

        Returns:
            추출된 약속 목록
        """
        arc_no = arc_data.get("arc_no", 0)
        results = []

        # 1순위: state_changes.commitments
        state_changes = arc_data.get("state_changes", {})
        if isinstance(state_changes, dict):
            commitments = state_changes.get("commitments", [])
            if isinstance(commitments, list) and commitments:
                for c in commitments:
                    if isinstance(c, dict) and c.get("description"):
                        parties = c.get("parties", [])
                        if isinstance(parties, str):
                            parties = [parties]
                        description = str(c["description"])
                        episode = c.get("episode", arc_no)
                        deadline = str(c.get("deadline_hint", ""))
                        self.register_commitment(
                            arc_no, episode, parties, description, deadline
                        )
                        results.append({
                            "parties": parties, "description": description,
                            "episode": episode, "deadline_hint": deadline,
                            "arc_no": arc_no
                        })
                if results:
                    return results

        # 2순위: regex 폴백
        tactical = arc_data.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        if not tactical:
            return results

        regex_commitments = self._regex_extract_commitments(tactical)
        for rc in regex_commitments:
            self.register_commitment(
                arc_no, 0, rc.get("parties", []),
                rc["description"], rc.get("deadline_hint", "")
            )
            rc["arc_no"] = arc_no
            results.append(rc)

        return results

    def _regex_extract_commitments(self, tactical_doc: str) -> List[Dict]:
        """
        [V66.1] tactical_doc에서 약속/맹세를 regex로 추출.
        state_changes.commitments가 비어있을 때 폴백으로 사용.

        Patterns: "약속", "맹세", "빚", "보답", "반드시", "기필코", "꼭.*하겠"
        """
        if not tactical_doc:
            return []

        results = []
        seen = set()

        # [V66.1] C-2: module-level compiled patterns
        commitment_patterns = _RE_COMMIT

        for pattern in commitment_patterns:
            for match in pattern.finditer(tactical_doc):
                desc = match.group(0).strip()
                if len(desc) < 4:
                    continue
                # 길이 제한 + 중복 방지
                desc = desc[:60]
                if desc in seen:
                    continue
                seen.add(desc)

                # 관련자 추출 시도
                npc_match = re.match(r'([가-힣]{2,10})', match.group(1) if match.lastindex else "")
                parties = ["주인공"]
                if npc_match:
                    npc = npc_match.group(1)
                    if npc not in ('주인공', '자신', '적', '상대'):
                        parties.append(npc)

                results.append({
                    "parties": parties,
                    "description": desc,
                    "episode": 0,
                    "deadline_hint": "",
                })

        return results

    def resolve_commitment(self, description: str) -> bool:
        """
        [V66.1] 약속 이행 완료 처리.

        Args:
            description: 이행된 약속 내용 (부분 매칭 지원)

        Returns:
            True: 매칭되는 약속을 찾아 fulfilled로 전환, False: 미발견
        """
        for commitment in self.tracker.pending_commitments:
            if commitment.get("status") != "pending":
                continue
            if description in commitment.get("description", "") or \
               commitment.get("description", "") in description:
                commitment["status"] = "fulfilled"
                print(f"      [V66.1] 약속 이행: {commitment['description']}")
                return True
        return False

    def get_commitment_summary(self) -> str:
        """
        [V66.1] 미이행 약속 목록 -> mandatory_context 주입용 문자열.
        "3일 후 갚겠다"고 했는데 잊어버리는 모순 방지.

        Returns:
            포맷된 미이행 약속 요약 문자열
        """
        pending = [c for c in self.tracker.pending_commitments if c.get("status") == "pending"]
        if not pending:
            return ""

        lines = ["[V66.1] 미이행 약속/맹세 (이행 또는 불이행 결과 반드시 서술):"]
        for c in pending:
            parties = ", ".join(c.get("parties", []))
            desc = c.get("description", "")
            arc = c.get("arc_no", "?")
            deadline = c.get("deadline_hint", "")
            line = f"  - [{parties}] {desc} (Arc {arc})"
            if deadline:
                line += f" 기한: {deadline}"
            lines.append(line)
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V62.7] 비-NPC 엔티티 명칭 일관성
    # ═══════════════════════════════════════════════════════════════

    def register_entity_name(self, name: str, entity_type: str, arc_no: int):
        """[V62.7->V64 P2-4] 비-NPC 엔티티 명칭 등록 (LRU, 최근 접근 우선 보존)"""
        if name and len(name) >= 2:
            if name in self.tracker.entity_name_registry:
                self.tracker.entity_name_registry.move_to_end(name)
                self.tracker.entity_name_registry[name]["last_seen_arc"] = arc_no
            else:
                self.tracker.entity_name_registry[name] = {
                    "type": entity_type,
                    "first_arc": arc_no,
                    "last_seen_arc": arc_no,
                    "aliases": set()
                }
                # [V64 P2-4] LRU eviction
                while len(self.tracker.entity_name_registry) > self.tracker._entity_registry_max_size:
                    self.tracker.entity_name_registry.popitem(last=False)

    def load_entities_from_entity_registry(self, entity_registry: Dict, arc_no: int):
        """[V62.7] StateExtractor의 entity_registry에서 비-NPC 엔티티를 로드"""
        if not entity_registry:
            return

        type_mapping = {
            "organizations": "organization",
            "locations": "location",
            "objects": "object",
        }

        for category, entity_type in type_mapping.items():
            entities = entity_registry.get(category, [])
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict):
                        name = entity.get("name", "")
                    elif isinstance(entity, str):
                        name = entity
                    else:
                        continue
                    if name and len(name) >= 2:
                        self.register_entity_name(name, entity_type, arc_no)

    def check_entity_name_consistency(self, content: str, arc_no: int = 0) -> List[Dict]:
        """
        [V62.7] 비-NPC 엔티티 명칭 일관성 검사.
        등록된 엔티티 이름과 유사하지만 다른 이름이 등장하면 WARNING.
        """
        warnings = []
        if not self.tracker.entity_name_registry or not content:
            return warnings

        checked = set()
        for canonical, info in self.tracker.entity_name_registry.items():
            if len(canonical) < 3:
                continue
            if canonical in content:
                continue  # 정확한 이름 사용 중 - OK

            # 접두어 기반 유사 이름 탐지
            prefix_len = max(2, int(len(canonical) * 0.6))
            prefix = canonical[:prefix_len]
            suffix = canonical[-2:] if len(canonical) >= 4 else ""

            pattern = re.compile(re.escape(prefix) + r'[가-힣]{1,4}')
            matches = pattern.findall(content)
            for match in matches:
                if match == canonical or match in checked:
                    continue
                if match in info.get("aliases", set()):
                    continue
                # 길이 차이 2자 이내
                if abs(len(match) - len(canonical)) <= 2:
                    key = (canonical, match)
                    if key not in checked:
                        checked.add(key)
                        warnings.append({
                            "entity": canonical,
                            "variant": match,
                            "entity_type": info.get("type", "?"),
                            "first_arc": info.get("first_arc", 0),
                            "severity": "WARNING",
                        })
        return warnings
