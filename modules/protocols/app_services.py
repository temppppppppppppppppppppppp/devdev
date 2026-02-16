"""
[Phase 4A] 서비스 Protocol 정의 — God Object 해체 기반

Stage 2/4 오케스트레이터가 self.app을 통해 접근하는 서비스의
구조적 서브타이핑 인터페이스. Phase 4C에서 self.app → 서비스 주입 전환 시
타입 안전성 보장.

시그니처 근거: stage2_orchestrator.py / stage4_orchestrator.py 실제 호출 코드
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

# ──────────────────────────────────────────────────────────────
# 1. UIServiceProtocol
# ──────────────────────────────────────────────────────────────


@runtime_checkable
class UIServiceProtocol(Protocol):
    """UI 로깅/출력 서비스

    근거:
    - stage4_orchestrator.py:260  self.app.ui.log(...)
    - stage4_orchestrator.py:283  self.app.ui.title(...)
    - stage2_orchestrator.py:79   self.app.ui.log(...)
    합계: 209건 (stage2: 99, stage4: 110)
    """

    def log(self, message: str) -> None: ...
    def title(self, title: str, subtitle: str = "") -> None: ...


# ──────────────────────────────────────────────────────────────
# 2. AuditServiceProtocol
# ──────────────────────────────────────────────────────────────


@runtime_checkable
class AuditServiceProtocol(Protocol):
    """감사 이벤트 버퍼링/출력 서비스

    근거:
    - stage2_orchestrator.py 36건  self.app._audit_event(...)
    - stage4_orchestrator.py:1748  self.app._flush_audit_buffer()
    - stage4_orchestrator.py:1748  self.app._write_audit_summary()

    NOTE: 원본은 private(_) 메서드이나 Protocol에서는 public으로 정의.
    Phase 4B에서 AuditService 구현체로 이전 시 public 메서드로 전환.
    """

    def audit_event(
        self,
        category: str,
        message: str,
        extra: dict | None = None,
    ) -> None: ...

    def flush_audit_buffer(self) -> None: ...

    def write_audit_summary(self) -> None: ...


# ──────────────────────────────────────────────────────────────
# 3. ProjectRepositoryProtocol
# ──────────────────────────────────────────────────────────────


@runtime_checkable
class ProjectRepositoryProtocol(Protocol):
    """프로젝트 데이터 저장소 (DB + 파일시스템 + 바이블)

    근거:
    - stage2_orchestrator.py:82-89  master_bible, volumes
    - stage4_orchestrator.py:206    arcs
    - stage4_orchestrator.py:269    paths.drafts
    - stage4_orchestrator.py:1465   name
    합계: 77건 (current_project 접근)
    """

    @property
    def name(self) -> str: ...

    @property
    def master_bible(self) -> dict: ...

    @master_bible.setter
    def master_bible(self, value: dict) -> None: ...

    @property
    def volumes(self) -> list: ...

    @volumes.setter
    def volumes(self, value: list) -> None: ...

    @property
    def arcs(self) -> list: ...

    @property
    def paths(self) -> Any: ...  # ProjectPaths — drafts, config, root 등

    @property
    def db(self) -> Any: ...  # DBRepositoryProtocol 구현체


# ──────────────────────────────────────────────────────────────
# 4. StateServiceProtocol
# ──────────────────────────────────────────────────────────────


@runtime_checkable
class StateServiceProtocol(Protocol):
    """상태 추적 서비스 (StateTracker facade)

    StateTracker 70개 public 메서드 중 오케스트레이터가 실제 호출하는 메서드만 정의.
    근거: stage2_orchestrator.py (60건), stage4_orchestrator.py (47건)
    """

    # --- 아크 상태 추출 (stage2에서 호출) ---

    def extract_npc_deaths_from_arc(self, arc: dict) -> list: ...
    def extract_skill_acquisitions_from_arc(self, arc: dict) -> list: ...
    def extract_npc_info_from_arc(self, arc: dict, genre: str = "") -> list: ...
    def extract_resolved_plots_from_arc(self, arc: dict) -> list: ...
    def extract_time_markers_from_arc(self, arc_data: dict) -> list: ...
    def extract_permanent_injuries_from_arc(self, arc_data: dict) -> list: ...
    def extract_npc_dialogue_styles_from_arc(self, arc: dict) -> list: ...
    def extract_npc_injuries_from_arc(self, arc: dict) -> list: ...
    def extract_npc_movements_from_arc(self, arc: dict) -> list: ...
    def extract_npc_npc_relationships_from_arc(self, arc: dict) -> list: ...
    def extract_npc_personality_from_arc(self, arc: dict) -> list: ...
    def extract_relationship_changes_from_arc(self, arc: dict) -> list: ...
    def extract_commitments_from_arc(self, arc_data: dict) -> list: ...
    def extract_entity_destructions_from_arc(self, arc: dict) -> list: ...
    def extract_financial_events_from_arc(self, arc: dict) -> dict: ...
    def extract_item_states_from_arc(self, arc: dict) -> list: ...
    def extract_protagonist_emotion_from_arc(self, arc_data: dict) -> Any: ...
    def extract_all_state_changes(self, arc: dict) -> dict: ...

    # --- 동반자/플롯 갱신 (stage2에서 호출) ---

    def update_companions_from_arc(self, arc_data: dict) -> list: ...
    def update_plot_mentions_from_arc(self, arc: dict) -> list: ...
    def check_suspended_plots(self, current_arc_no: int, threshold: int = 3) -> list: ...
    def check_and_expand_genre(self, content: str) -> Any: ...

    # --- 요약 (stage4에서 호출) ---

    def get_entity_destruction_summary(self) -> str: ...
    def get_resolved_plots_summary(self) -> str: ...
    def get_npc_personality_summary(self) -> str: ...
    def get_npc_npc_relationship_summary(self) -> str: ...
    def get_permanent_injury_summary(self) -> str: ...
    def get_time_timeline_summary(self) -> str: ...
    def get_companion_summary(self) -> str: ...
    def get_commitment_summary(self) -> str: ...
    def get_protagonist_emotion_summary(self) -> str: ...
    def get_item_state_summary(self) -> str: ...
    def get_plot_suspension_summary(self, current_arc_no: int) -> str: ...
    def get_npc_dialogue_style_summary(self) -> str: ...
    def get_relationship_changes_summary(self) -> str: ...
    def get_npc_injury_summary(self) -> str: ...
    def get_npc_movement_summary(self) -> str: ...
    def get_protagonist_skills_summary(self) -> str: ...
    def get_financial_state_summary(self) -> str: ...
    def get_dead_npc_summary(self) -> str: ...

    # --- 검증 (stage4에서 호출) ---

    def check_destroyed_entity_in_manuscript(self, content: str) -> list: ...
    def check_time_consistency(self, manuscript: str, current_timeline: list | None = None) -> list: ...
    def check_dead_npc_in_manuscript(self, manuscript: str, ep_num: int, arc_no: int = 0) -> list: ...

    # --- 아크 요약/컨텍스트 ---

    def generate_arc_summary(self, arc_no: int, arc: dict | None = None) -> dict: ...
    def format_arc_summary_for_prompt(self, arc_summaries: list) -> str: ...

    # --- 레지스트리 프로퍼티 ---

    @property
    def npc_registry(self) -> dict: ...

    @property
    def item_state_registry(self) -> dict: ...

    @property
    def in_world_timeline(self) -> dict: ...

    # --- 재정/NPC 레지스트리 import/export ---

    def import_financial_registry(self, data: dict) -> None: ...
    def export_financial_registry(self) -> dict: ...

    # --- NPC 레지스트리 정리 ---

    def cleanup_npc_registry_with_llm(self, arc_no: int) -> list: ...


# ──────────────────────────────────────────────────────────────
# 5. ConfigServiceProtocol
# ──────────────────────────────────────────────────────────────


@runtime_checkable
class ConfigServiceProtocol(Protocol):
    """설정/시스템 서비스 (장르, API, 에이전트 등)

    근거:
    - stage2_orchestrator.py:99   self.app.selected_genre
    - stage2_orchestrator.py:125  self.app.sys.api_client
    - stage4_orchestrator.py:216  self.app.selected_genre
    - stage4_orchestrator.py:869  self.app.perf_timer
    """

    @property
    def selected_genre(self) -> dict | None: ...

    @property
    def sys(self) -> Any: ...  # SystemService — api_client, hud, guard

    @property
    def agents(self) -> dict: ...  # {name: agent_instance}

    @property
    def perf_timer(self) -> Any: ...  # PerfTimer — start, stop, log_summary
