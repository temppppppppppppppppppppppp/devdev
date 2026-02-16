"""
[Phase 2.1] Relationship State Machine
NPC-??? ?? ?? ?? ? ??.

[R5-2b] Split into 2 submodules:
- relationship_tracker_npc.py
- relationship_tracker_factions.py
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.core.relationship_tracker_factions import FactionInfo, FactionRelationshipEvent


@dataclass
class RelationshipEvent:
    """[V49.7] 관계 전이 이벤트 기록"""

    arc: int
    episode: int
    npc_name: str
    from_state: str
    to_state: str
    trigger: str  # 전이를 유발한 사건
    justification: str  # 서사적 근거
    is_valid: bool = True


class RelationshipTracker:
    """Facade delegating NPC/faction logic to dedicated submodules."""

    def __init__(self) -> None:
        """[V49.7] 초기화, [V59] 파벌 추적 추가"""
        self.npc_states: dict[str, str] = {}  # {npc_name: current_state}
        self.transition_history: list[RelationshipEvent] = []

        # [V59] 세력/파벌 관계 추적
        self.factions: dict[str, FactionInfo] = {}  # {faction_name: FactionInfo}
        self.faction_relations: dict[tuple[str, str], str] = {}  # {(faction_a, faction_b): state}
        self.faction_transition_history: list[FactionRelationshipEvent] = []
        self.protagonist_faction: str | None = None  # 주인공 소속 세력

        self._npc = None
        self._factions = None

    @property
    def npc(self):
        if self._npc is None:
            from modules.core.relationship_tracker_npc import RelationshipTrackerNPC

            self._npc = RelationshipTrackerNPC(self)
        return self._npc

    @property
    def factions_module(self):
        if self._factions is None:
            from modules.core.relationship_tracker_factions import RelationshipTrackerFactions

            self._factions = RelationshipTrackerFactions(self)
        return self._factions

    # NPC wrappers
    def validate_transition(self, *args, **kwargs):
        return self.npc.validate_transition(*args, **kwargs)

    def _suggest_transition_path(self, *args, **kwargs):
        return self.npc._suggest_transition_path(*args, **kwargs)

    def infer_state_from_manuscript(self, *args, **kwargs):
        return self.npc.infer_state_from_manuscript(*args, **kwargs)

    def get_relationship_history(self, *args, **kwargs):
        return self.npc.get_relationship_history(*args, **kwargs)

    def record_transition(self, *args, **kwargs):
        return self.npc.record_transition(*args, **kwargs)

    def validate_transition_with_justification(self, *args, **kwargs):
        return self.npc.validate_transition_with_justification(*args, **kwargs)

    def get_npc_current_state(self, *args, **kwargs):
        return self.npc.get_npc_current_state(*args, **kwargs)

    def get_transition_history(self, *args, **kwargs):
        return self.npc.get_transition_history(*args, **kwargs)

    def generate_transition_prompt(self, *args, **kwargs):
        return self.npc.generate_transition_prompt(*args, **kwargs)

    # Faction wrappers
    def register_faction_v59(self, *args, **kwargs):
        return self.factions_module.register_faction_v59(*args, **kwargs)

    def set_faction_relation_v59(self, *args, **kwargs):
        return self.factions_module.set_faction_relation_v59(*args, **kwargs)

    def validate_faction_transition_v59(self, *args, **kwargs):
        return self.factions_module.validate_faction_transition_v59(*args, **kwargs)

    def _suggest_faction_transition_path(self, *args, **kwargs):
        return self.factions_module._suggest_faction_transition_path(*args, **kwargs)

    def record_faction_transition_v59(self, *args, **kwargs):
        return self.factions_module.record_faction_transition_v59(*args, **kwargs)

    def get_faction_relation_v59(self, *args, **kwargs):
        return self.factions_module.get_faction_relation_v59(*args, **kwargs)

    def infer_faction_state_from_manuscript_v59(self, *args, **kwargs):
        return self.factions_module.infer_faction_state_from_manuscript_v59(*args, **kwargs)

    def track_faction_dynamics_v59(self, *args, **kwargs):
        return self.factions_module.track_faction_dynamics_v59(*args, **kwargs)

    def get_faction_power_balance_v59(self, *args, **kwargs):
        return self.factions_module.get_faction_power_balance_v59(*args, **kwargs)

    def generate_faction_dynamics_prompt_v59(self, *args, **kwargs):
        return self.factions_module.generate_faction_dynamics_prompt_v59(*args, **kwargs)

    def get_faction_transition_history_v59(self, *args, **kwargs):
        return self.factions_module.get_faction_transition_history_v59(*args, **kwargs)

    def analyze_protagonist_faction_position_v59(self, *args, **kwargs):
        return self.factions_module.analyze_protagonist_faction_position_v59(*args, **kwargs)

    def generate_faction_report_v59(self, *args, **kwargs):
        return self.factions_module.generate_faction_report_v59(*args, **kwargs)
