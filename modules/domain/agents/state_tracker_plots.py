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
