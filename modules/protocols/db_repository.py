"""
[Phase 4A] DB Repository Protocol — DBManager 추상화 계층

DBManager(db_manager.py)의 public 메서드/프로퍼티를 구조적 서브타이핑으로 정의.
Phase 4C에서 직접 conn/cursor 접근을 차단할 때 타입 안전성 보장.

시그니처 근거: modules/core/db_manager.py
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DBRepositoryProtocol(Protocol):
    """S등급 무결성 DB 엔진 계약
    """

    # --- 트랜잭션 제어 (db_manager.py:295-297, 299, 310) ---

    def begin(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...

    @property
    def in_transaction(self) -> bool: ...

    # --- 범용 쿼리 (db_manager.py:316, 322) ---

    def execute_query(self, sql: str, params: tuple = ()) -> list: ...
    def execute_update(self, sql: str, params: tuple = ()) -> None: ...

    # --- 원고 (db_manager.py:328-339) ---

    def save_manuscript(self, ep_num: int, title: str, content: str, hud_snapshot: dict | None = None) -> None: ...
    def get_manuscript(self, ep_num: int) -> dict | None: ...
    def get_blueprint(self, ep_num: int) -> dict | None: ...

    # --- 지표 (db_manager.py:352) ---

    def update_martial_tracker(self, ep_num: int, martial_data: Any) -> None: ...

    # --- 에피소드 바이블 (db_manager.py:371-561) ---

    def save_episode_bible(self, ep_num: int, bible_delta: dict) -> None: ...
    def get_episode_bible(self, ep_num: int) -> dict: ...
    def get_cumulative_bible(self, up_to_ep: int) -> dict: ...
    def get_all_episode_bibles(self) -> list: ...
    def get_episode_bibles_before(self, up_to_ep: int) -> list: ...
    def delete_episode_bibles_after(self, ep_num: int) -> None: ...

    # --- 복선/시드 (db_manager.py:588-606) ---

    def sync_seeds(self, seeds_list: list) -> None: ...
    def archive_seed(self, seed_id: int, ep_num: int) -> None: ...

    # --- 백과사전/로어 (db_manager.py:610-674) ---

    def update_lore_item(self, category: str, item: str, description: str) -> None: ...
    def update_lore_items_batch(self, lore_items_list: list) -> None: ...
    def get_lore_list_by_category(self, category: str) -> list: ...

    # --- 앵커 (db_manager.py:684-714) ---

    def save_anchor(self, key: str, data: Any) -> bool: ...
    def load_anchor(self, key: str, default: Any = None) -> Any: ...
    def load_all_anchors(self) -> dict: ...
    def save_context_cache_attempt(
        self,
        *,
        agent_name: str,
        model: str,
        cache_type: str,
        project_name: str = "",
        content_chars: int,
        min_content_chars: int,
        ttl_seconds: int,
        cache_outcome: str,
        cache_reason: str | None = None,
        cache_name: str | None = None,
        content_hash: str | None = None,
        error_msg: str | None = None,
        stage: int | None = None,
        ep_num: int | None = None,
    ) -> None: ...

    # --- 블루프린트 (db_manager.py:726-732) ---

    def save_blueprint(self, ep_num: int, data_dict: dict) -> None: ...
    def get_previous_blueprint(self, current_ep: int) -> dict | None: ...

    # --- 상태 로그 (db_manager.py:743-783) ---

    def save_state_log(self, ep_num: int, data_dict: dict) -> None: ...
    def save_state_log_with_summary(
        self,
        ep_num: int,
        data_dict: dict,
        summary: str,
    ) -> None: ...
    def get_latest_state(self) -> dict: ...
    def load_state_log(self, ep_num: int) -> dict: ...
    def get_causal_summary_chain(self, limit: int = 5) -> list: ...
    def get_recent_causal_links(self, current_ep: int, lookback: int = 30) -> list[dict]: ...
    def get_causal_links_by_entities(
        self,
        entity_names: list[str],
        *,
        before_ep: int,
        lookback: int = 120,
        limit: int = 30,
    ) -> list[dict]: ...

    # --- 카르마/관계 (db_manager.py:789-804) ---

    def update_karma(
        self,
        npc_name: str,
        mis_val: float,
        obs_val: float,
        ep_num: int,
    ) -> None: ...
    def get_all_karma(self) -> list: ...
    def save_causal_links(self, new_links: list, current_ep: int) -> None: ...

    # --- 원자적 팩토리 (db_manager.py:815) ---

    def commit_episode_factory(
        self,
        ep_num: int,
        manuscript_data: dict,
        martial_data: dict,
        state_data: dict,
        causal_links: list,
        karma_data: list,
        lore_data: list,
        recovered_seeds: list | None = None,
    ) -> bool: ...

    # --- 트랜잭션 컨텍스트 매니저 (db_manager.py:967) ---
    # NOTE: @contextmanager는 Protocol에서 직접 표현 불가.
    # 구현체에서 Generator 반환 보장.

    # --- 유틸리티 (db_manager.py:1002-1040) ---

    def get_latest_episode_number(self) -> int: ...
    def get_latest_blueprint_number(self) -> int: ...
    def get_context_manuscripts(self, current_ep: int, limit: int = 3) -> list: ...
    def reset_after(self, target_ep: int) -> None: ...
    def get_sync_status(self, ep_num: int) -> dict | None: ...
    def update_sync_status(self, ep_num: int, status: int) -> None: ...

    # --- 조회 (db_manager.py:1050-1136) ---

    def get_active_seeds(self) -> list: ...
    def get_recent_blueprints(self, before_ep: int, limit: int = 10) -> list: ...
    def get_recent_manuscripts(self, before_ep: int, limit: int = 10) -> list: ...
    def get_recent_manuscript_excerpts(
        self,
        before_ep: int,
        limit: int = 10,
        max_chars: int = 200,
    ) -> list: ...

    # --- 품질/회고 (db_manager.py) ---

    def save_episode_quality_label(self, ep_num: int, labels: dict) -> None: ...
    def get_episode_quality_label(self, ep_num: int) -> dict | None: ...
    def get_recent_episode_quality_labels(self, before_ep: int, lookback: int = 20) -> list[dict]: ...
    def save_episode_quality_signal(self, ep_num: int, signals: dict) -> None: ...
    def get_episode_quality_signal(self, ep_num: int) -> dict | None: ...
    def get_recent_episode_quality_signals(
        self,
        before_ep: int | None = None,
        lookback: int = 20,
    ) -> list[dict]: ...
    def get_quality_signal_summary(self, before_ep: int | None = None, lookback: int = 5) -> dict: ...
    def get_recent_episode_scores(self, before_ep: int, lookback: int = 5) -> list[dict]: ...
    def get_strategy_win_rates(
        self,
        lookback: int = 20,
        *,
        selected_label: str | None = None,
        allowed_strategies: tuple[str, ...] | list[str] | set[str] | None = None,
    ) -> dict: ...
    def get_stage_attempts_for_arc(
        self,
        arc_num: int,
        stages: tuple[int, ...] = (3, 4),
        verdict: str | None = None,
        limit: int = 20,
    ) -> list[dict]: ...
    def save_stage_attempt(
        self,
        stage: int,
        verdict: str,
        attempt_num: int = 1,
        ep_num: int | None = None,
        arc_num: int | None = None,
        score: int | None = None,
        failure_category: str | None = None,
        reject_reason: str | None = None,
        fix_scope: str | None = None,
        model: str | None = None,
        duration_ms: int | None = None,
        advisory_flags: dict | None = None,
        session_id: str | None = None,
        attempt_key: str | None = None,
        generation_method: str | None = None,
        prompt_version: str | None = None,
        candidate_key: str | None = None,
        content_hash: str | None = None,
        artifact_path: str | None = None,
        selection_reason: str | None = None,
        verdict_reason: str | None = None,
        open_review: str | None = None,
        fix_scope_reasoning: str | None = None,
        runtime_advisory: str | None = None,
        retry_directives: str | None = None,
        initial_verdict: str | None = None,
        score_breakdown: dict | str | None = None,
        is_patch: bool = False,
        is_patch_fallback: bool = False,
        patch_strategy: str | None = None,
    ) -> bool: ...
