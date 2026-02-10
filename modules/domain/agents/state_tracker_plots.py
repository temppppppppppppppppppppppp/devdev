"""
[V64.P3] StateTracker Plots & Entity Sub-module
완결된 플롯 추적 + 비-NPC 엔티티 명칭 일관성 관리.

StateTracker에서 resolved_plots 및 entity_name_registry 관련 메서드만 분리.
모든 공유 상태는 self.tracker를 통해 접근.
"""

import re
from typing import Dict, List


class StateTrackerPlots:
    """[V64.P3] 완결된 플롯 + 엔티티 명칭 서브모듈"""

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
            activity_patterns = [
                re.compile(re.escape(name) + r'[이가은는에서의]?\s*(?:공격|방어|전투|활동|지원|파견|출격|모집|개방)'),
                re.compile(r'(?:건재|부활|재건)[한된]\s*' + re.escape(name)),
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
