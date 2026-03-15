# TF-ST: StateTracker + Plots 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | StateTracker: full_extract_from_arcs, snapshot/restore, plot threads, financial data, initialization |
| Source files | state_tracker.py:1668줄, state_tracker_plots.py:963줄 |
| TF Items | 14 (CRITICAL 3 / IMPORTANT 7 / INSIGHT 4) |

## 1. Executive Summary

StateTracker는 23개 이상의 독립 레지스트리(NPC, 플롯, 아이템, 시간선, 약속, 금융 등)를 관리하는 대형 상태 에이전트이다.
Facade 패턴(V64.P3)을 통해 NPC/Financial/Plots 3개 서브모듈로 분리되었으나, 모든 공유 상태는 여전히 메인 StateTracker 인스턴스의 속성으로 존재하며 서브모듈은 `self.tracker`로 back-reference한다.

핵심 발견 사항:
1. **`merge_from_previous_arcs`가 20개 이상의 레지스트리를 누락**하여 `create_tracker_from_arcs` 경로에서 플롯/엔티티/시간선/약속 등 대부분의 상태가 소실된다 (CRITICAL).
2. **`full_extract_from_arcs` 핵심 4종이 예외 시 해당 arc 전체를 건너뛴다** -- 이후 arc의 추출도 중단되지는 않지만, 해당 arc의 13개 확장 추출이 모두 실행되지 않는다 (CRITICAL).
3. **8-thread advisory 체인에서 `state_tracker`의 mutable 컬렉션을 락 없이 동시 읽기/쓰기**한다 (CRITICAL).
4. Snapshot/restore 메커니즘이 존재하지 않아 rollback 시 상태 불일치가 발생할 수 있다.
5. `active_plots`와 `resolved_plots`가 독립적으로 관리되어 이중 상태(resolved인데 active) 가능성이 있다.
6. `_populate_genre_registries_from_arc`이 `full_extract_from_arcs`에서 호출되지 않아 hunter/fantasy 장르 레지스트리가 Stage 2 preflight에서만 채워진다.

## 2. Architecture / Data Flow Diagram (ASCII)

```
                         ┌─────────────────────────────────────┐
                         │          StateTracker (main)         │
                         │                                     │
                         │  23+ mutable registries:            │
                         │  - states: Dict[int, EpisodeState]  │
                         │  - transitions: List[StateTransition]│
                         │  - npc_registry: Dict               │
                         │  - resolved_plots: List             │
                         │  - active_plots: Dict               │
                         │  - entity_name_registry: OrderedDict│
                         │  - entity_destructions: List        │
                         │  - item_state_registry: Dict        │
                         │  - in_world_timeline: List          │
                         │  - pending_commitments: List        │
                         │  - protagonist_emotion: Dict        │
                         │  - current_companions: List         │
                         │  - financial_number_registry: Dict  │
                         │  - npc_npc_relationships: Dict      │
                         │  - npc_dialogue_profiles: Dict      │
                         │  - protagonist_skills: Set          │
                         │  - skill_acquisitions: Dict         │
                         │  - skill_cooldown_registry: Dict    │
                         │  - dungeon_clear_registry: Dict     │
                         │  - spell_repertoire: Dict           │
                         │  - blessing_curse_registry: Dict    │
                         │  - filmography_registry: Dict       │
                         │  - tracking_fields: Dict            │
                         │  - _db: Optional[DBManager]         │
                         │  - _world_state: Optional[WSM]      │
                         └───┬──────────┬──────────┬───────────┘
                             │          │          │
                    ┌────────┘          │          └────────┐
                    v                   v                   v
          ┌─────────────────┐ ┌────────────────┐ ┌──────────────────┐
          │ StateTrackerNPC │ │ StateTracker    │ │ StateTracker     │
          │ (self.tracker   │ │ Financial       │ │ Plots            │
          │  = main)        │ │ (self.tracker   │ │ (self.tracker    │
          │                 │ │  = main)        │ │  = main)         │
          │ Methods:        │ │ Methods:        │ │ Methods:         │
          │ - extract_npc_* │ │ - extract_fin_* │ │ - extract_plots  │
          │ - register_npc_*│ │ - get_fin_sum   │ │ - entity_name_*  │
          │ - check_dead_*  │ │ - export/import │ │ - time_markers   │
          │ - merge_npc_reg │ │                 │ │ - commitments    │
          │ - companions    │ │                 │ │ - item_states    │
          │ - perm_injuries │ │                 │ │ - destructions   │
          │ - emotion       │ │                 │ │ - plot_suspension│
          └─────────────────┘ └────────────────┘ └──────────────────┘


  ┌────────────────────────────────────────────────────────────────────┐
  │             full_extract_from_arcs  (17 operations per arc)       │
  │                                                                    │
  │  for arc in arcs:                                                  │
  │    ┌──[핵심 4종: 예외 전파 → arc 전체 건너뜀]──────────────────┐   │
  │    │ 1. extract_npc_deaths_from_arc(arc)                       │   │
  │    │ 2. extract_skill_acquisitions_from_arc(arc)               │   │
  │    │ 3. extract_npc_info_from_arc(arc, genre=genre)            │   │
  │    │ 4. extract_resolved_plots_from_arc(arc)                   │   │
  │    └───────────────────────────────────────────────────────────┘   │
  │    ┌──[확장 13종: 개별 try/except, 비차단]─────────────────────┐   │
  │    │ 5.  extract_time_markers_from_arc(arc)                    │   │
  │    │ 6.  extract_permanent_injuries_from_arc(arc)              │   │
  │    │ 7.  update_companions_from_arc(arc)                       │   │
  │    │ 8.  extract_commitments_from_arc(arc)                     │   │
  │    │ 9.  extract_protagonist_emotion_from_arc(arc)             │   │
  │    │ 10. extract_item_states_from_arc(arc)                     │   │
  │    │ 11. extract_entity_destructions_from_arc(arc)             │   │
  │    │ 12. extract_npc_personality_from_arc(arc)                 │   │
  │    │ 13. extract_npc_npc_relationships_from_arc(arc)           │   │
  │    │ 14. extract_npc_dialogue_styles_from_arc(arc)             │   │
  │    │ 15. extract_relationship_changes_from_arc(arc)            │   │
  │    │ 16. extract_npc_injuries_from_arc(arc)                    │   │
  │    │ 17. extract_npc_movements_from_arc(arc)                   │   │
  │    └───────────────────────────────────────────────────────────┘   │
  │    ┌──[조건부: genre=="investment"]─────────────────────────────┐  │
  │    │ 18. extract_financial_events_from_arc(arc)                 │  │
  │    └───────────────────────────────────────────────────────────┘   │
  │                                                                    │
  │  ** NOT CALLED: **                                                 │
  │    - _populate_genre_registries_from_arc (hunter/fantasy 전용)     │
  │    - update_plot_mentions_from_arc (active_plots 갱신)             │
  │    - load_entities_from_entity_registry (엔티티 레지스트리)        │
  └────────────────────────────────────────────────────────────────────┘


  ┌────────────────────────────────────────────────────────────────────┐
  │             Initialization Order (main_a.py L4013-4050)            │
  │                                                                    │
  │  1. StateTracker() 생성                                            │
  │  2. bind_db(db_manager)           ← NPC 이력 DB 배선              │
  │  3. full_extract_from_arcs(arcs)  ← 17개 추출 실행                │
  │  4. WorldStateManager() 생성                                      │
  │  5. bind_world_state(wsm)         ← 3 이후에 호출!                │
  │                                                                    │
  │  stage3_orchestrator.py L638: bind_world_state BEFORE full_extract │
  │  main_a.py L4018-4050: bind_world_state AFTER full_extract         │
  │  → 초기화 순서 불일치                                              │
  └────────────────────────────────────────────────────────────────────┘
```

## 3. TF Items

### TF-ST-01: `merge_from_previous_arcs` 20+ 레지스트리 누락 -- CRITICAL

- **Location**: `state_tracker.py:L938-L950`
- **Description**: `merge_from_previous_arcs()`는 `acquired_items`, `consumed_items`, `global_items` 3가지만 병합한다. `create_tracker_from_arcs()`(L1641-1668)에서 이 메서드를 사용하는데, 결과적으로 다음 20개 이상의 레지스트리가 전혀 병합되지 않는다:
  - `resolved_plots`, `active_plots`, `entity_name_registry`, `entity_destructions`
  - `item_state_registry`, `in_world_timeline`, `pending_commitments`
  - `protagonist_emotion`, `current_companions`, `protagonist_skills`
  - `skill_acquisitions`, `npc_npc_relationships`, `npc_dialogue_profiles`
  - `skill_cooldown_registry`, `dungeon_clear_registry`, `spell_repertoire`
  - `blessing_curse_registry`, `filmography_registry`, `financial_number_registry`
- **Evidence**:
  ```python
  # L938-950
  def merge_from_previous_arcs(self, prev_tracker: "StateTracker"):
      """이전 Arc의 상태를 현재 tracker에 병합"""
      # 아이템 이력 병합
      for item, ep in prev_tracker.acquired_items.items():
          if item not in self.acquired_items:
              self.acquired_items[item] = ep
      for item, ep in prev_tracker.consumed_items.items():
          if item not in self.consumed_items:
              self.consumed_items[item] = ep
      # 전역 아이템 목록 병합
      self.global_items.update(prev_tracker.global_items)
      # ← resolved_plots, active_plots 등 20+ 레지스트리 누락!
  ```
- **Impact**: `create_tracker_from_arcs()`로 생성된 tracker는 아이템/NPC(별도 merge_npc_registry 호출) 외의 모든 상태를 잃는다. Analyst에서 이 함수를 사용(analyst.py:L1838-1840)하므로, 이전 Arc의 완결 플롯/파괴된 엔티티/시간선/약속 등의 연속성 정보가 제약 프롬프트에 반영되지 않는다.
- **Suggested fix direction**: `merge_from_previous_arcs`에 모든 레지스트리 병합 로직 추가. 또는 `create_tracker_from_arcs`에서 `full_extract_from_arcs`를 사용하도록 변경 (현재는 `load_arc_design` 기반).

---

### TF-ST-02: 핵심 4종 예외 시 해당 arc의 확장 13종 전체 미실행 -- CRITICAL

- **Location**: `state_tracker.py:L187-L249`
- **Description**: `full_extract_from_arcs`에서 핵심 4종 (L191-194: `extract_npc_deaths`, `extract_skill_acquisitions`, `extract_npc_info`, `extract_resolved_plots`)은 try/except 없이 호출된다. 이 4종 중 하나라도 예외를 던지면 for 루프 자체가 중단되어:
  1. 해당 arc의 확장 13종 추출이 모두 건너뛰어진다.
  2. **이후 모든 arc의 추출도 중단된다** (for 루프 탈출).
- **Evidence**:
  ```python
  # L187-249
  def full_extract_from_arcs(self, arcs: list[dict], genre: str = "") -> None:
      for arc in arcs:
          # 핵심 4종: 항상 호출 (try/except 없음!)
          self.extract_npc_deaths_from_arc(arc)      # ← 예외 시 arc 전체 + 이후 arc 중단
          self.extract_skill_acquisitions_from_arc(arc)
          self.extract_npc_info_from_arc(arc, genre=genre)
          self.extract_resolved_plots_from_arc(arc)
          # V66 확장: 실패해도 비차단
          try:
              self.extract_time_markers_from_arc(arc)
          except Exception as e:
              ...
  ```
- **Impact**: 잘못된 arc 데이터 1건이 전체 StateTracker 초기화를 절단할 수 있다. 예: `arc.get("state_changes")` 반환값이 예상과 다른 형태일 때 `extract_npc_info_from_arc`가 예외를 던지면, 그 이후의 10+ arc 데이터가 모두 누락된다.
- **Suggested fix direction**: 핵심 4종도 per-arc try/except로 감싸되, 실패 시 해당 arc에 대해 warning 로그를 남기고 다음 arc로 계속 진행하도록 변경. 또는 4종 각각을 개별 try/except로 감싸서 가능한 추출은 수행되도록 변경.

---

### TF-ST-03: Advisory 8-thread 병렬 실행에서 StateTracker 무잠금 동시 접근 -- CRITICAL

- **Location**: `stage4_interview_round.py:L4163-L4205` (호출부), `state_tracker.py` (전체), `state_tracker_plots.py` (전체)
- **Description**: Advisory 체인이 `ThreadPoolExecutor(max_workers=8)`로 8개 advisory를 병렬 실행한다(L4163). 이 advisory들은 `self.ctx.state_tracker`의 컬렉션을 읽고, 일부는 쓰기도 한다:
  - `check_destroyed_entity_in_manuscript` (L2573): `entity_destructions` 읽기
  - `check_time_consistency` (L3330): `in_world_timeline` 읽기
  - 다양한 advisory에서 `npc_registry`, `active_plots` 등 읽기
  - StateTracker의 어떤 컬렉션에도 `threading.Lock`이 사용되지 않는다.
- **Evidence**:
  - `state_tracker.py`: `Lock`, `threading` import 없음
  - `state_tracker_plots.py`: `Lock`, `threading` import 없음
  - `state_tracker_npc.py`: `Lock`, `threading` import 없음
- **Impact**: CPython의 GIL이 단순 읽기에 대해 어느 정도 보호하지만, dict/list iteration 도중 다른 스레드가 해당 컬렉션을 수정하면 `RuntimeError: dictionary changed size during iteration` 또는 데이터 불일치가 발생할 수 있다. 실제로 `check_suspended_plots`(L371-390)는 `active_plots`를 순회하면서 `info["status"] = "suspended"` 쓰기를 수행한다.
- **Suggested fix direction**: Advisory 체인 진입 전에 필요한 상태의 스냅샷을 생성하여 각 advisory에 전달. 또는 advisory에서 state_tracker를 읽기 전용으로만 접근하도록 제한.

---

### TF-ST-04: Snapshot/Restore 메커니즘 부재 -- IMPORTANT

- **Location**: `state_tracker.py` (전체)
- **Description**: StateTracker에는 상태를 스냅샷으로 저장하고 복원하는 메커니즘이 없다. 23개 이상의 mutable 레지스트리가 있지만 `save_state()`/`restore_state()`/`rollback_to()` 같은 메서드가 존재하지 않는다. `project_service.py`의 `rollback_to()` 검증에서도 StateTracker 상태는 고려되지 않는다.
- **Evidence**: `snapshot`, `rollback_to`, `restore`, `save_state`, `deep_copy` 등의 키워드로 검색 시 StateTracker 내부에서 해당 기능 없음 확인.
- **Impact**: Episode/Arc rollback 시 StateTracker의 레지스트리가 이전 상태로 되돌려지지 않는다. 예: Arc 3의 NPC 사망이 등록된 후 Arc 3을 rollback하면, NPC는 여전히 dead로 남아있다. 현재 운영에서는 rollback 후 `full_extract_from_arcs`를 재호출하여 전체 재구축하는 패턴으로 우회하고 있으나, 이는 명시적으로 보장되지 않는다.
- **Suggested fix direction**: `full_extract_from_arcs` 호출 전 레지스트리 초기화(`__init__` 수준 리셋) 메서드를 추가하여, rollback 후 안전한 재구축을 보장.

---

### TF-ST-05: `active_plots`와 `resolved_plots` 이중 상태 가능 -- IMPORTANT

- **Location**: `state_tracker_plots.py:L98-L129` (resolved), `state_tracker_plots.py:L320-L369` (active)
- **Description**: `extract_resolved_plots_from_arc`(L98)은 `resolved_plots` 리스트에 플롯을 추가한다. `update_plot_mentions_from_arc`(L335)는 `active_plots` 딕셔너리의 해당 플롯을 `"resolved"` 상태로 전환한다. 그러나 이 두 메서드는 독립적으로 호출되며:
  1. `full_extract_from_arcs`는 `extract_resolved_plots_from_arc`만 호출하고 `update_plot_mentions_from_arc`는 호출하지 **않는다** (L194 vs 미호출).
  2. `stage2_preflight.py`에서만 `update_plot_mentions_from_arc`가 호출된다 (L1500).
- **Evidence**:
  ```python
  # full_extract_from_arcs L194: resolved_plots에 추가
  self.extract_resolved_plots_from_arc(arc)
  # update_plot_mentions_from_arc는 호출되지 않음!
  # → active_plots에서 해당 플롯이 "resolved"로 전환되지 않음
  ```
- **Impact**: `full_extract_from_arcs`로 초기화된 tracker에서는 `active_plots`가 빈 상태이므로 `check_suspended_plots`와 `get_plot_suspension_summary`가 무효. Stage 3 직행 시(main_a.py L4013)에는 `update_plot_mentions_from_arc`가 호출되지 않아 플롯 서스펜션 감지가 작동하지 않는다.
- **Suggested fix direction**: `full_extract_from_arcs`에 `update_plot_mentions_from_arc` 호출 추가.

---

### TF-ST-06: `_populate_genre_registries_from_arc`가 `full_extract_from_arcs`에서 미호출 -- IMPORTANT

- **Location**: `state_tracker.py:L1615-L1638` (정의), `state_tracker.py:L187-L249` (full_extract)
- **Description**: `_populate_genre_registries_from_arc`는 hunter 장르의 `dungeon_clear_registry`, `skill_cooldown_registry`와 fantasy 장르의 `spell_repertoire`를 채운다. 이 메서드는 `full_extract_from_arcs`에서 호출되지 않으며, `stage2_preflight.py:L1509`에서만 호출된다.
- **Evidence**: `full_extract_from_arcs`(L187-249) 코드에 `_populate_genre_registries_from_arc` 호출 없음. `grep` 결과 `stage2_preflight.py`와 `validation_test_harness.py`에서만 호출됨.
- **Impact**: Stage 3 직행 시(main_a.py L4013) 또는 `create_tracker_from_arcs`(analyst.py:L1840) 사용 시, hunter/fantasy 장르의 던전/스킬쿨다운/마법 레지스트리가 비어 있다.
- **Suggested fix direction**: `full_extract_from_arcs`의 loop 내에 `_populate_genre_registries_from_arc(arc)` 호출 추가 (비차단).

---

### TF-ST-07: `main_a.py`에서 `bind_world_state`가 `full_extract_from_arcs` 이후 호출 -- IMPORTANT

- **Location**: `main_a.py:L4018-L4050` vs `stage3_orchestrator.py:L638-L642`
- **Description**: 초기화 순서 불일치:
  - `stage3_orchestrator.py:L639`: `bind_world_state()` → `full_extract_from_arcs()` (WorldState 먼저)
  - `main_a.py:L4018-4050`: `bind_db()` → `full_extract_from_arcs()` → WorldState 생성 → `bind_world_state()` (WorldState 나중)
- **Evidence**:
  ```python
  # stage3_orchestrator.py L638-642
  app.state_tracker.bind_db(app.current_project.db)
  app.state_tracker.bind_world_state(getattr(app, "world_state", None))  # BEFORE extract
  ...
  app.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)

  # main_a.py L4018-4050
  self.state_tracker.bind_db(self.current_project.db)
  ...
  self.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)
  # ... (L4033-4046: WorldStateManager 생성)
  self.state_tracker.bind_world_state(self.world_state)  # AFTER extract
  ```
- **Impact**: 현재 `_world_state`는 `revive_npc()`와 NPC 사망 등록 시에만 참조되므로 즉각적 문제는 없다. 그러나 향후 `full_extract_from_arcs` 내부에서 `_world_state`를 참조하는 로직이 추가되면, `main_a.py` 경로에서만 `None` 참조 문제가 발생한다.
- **Suggested fix direction**: 두 경로의 초기화 순서 통일. 가능하면 `bind_db` → `bind_world_state` → `full_extract_from_arcs` 순서로 표준화.

---

### TF-ST-08: 금융 데이터 문자열 기반 저장 -- 정밀도 문제 없으나 타입 불안정 -- IMPORTANT

- **Location**: `state_tracker_financial.py:L20-L47`, `state_tracker_financial.py:L70-L109`
- **Description**: 금융 이벤트는 `state_changes.financial_events`에서 raw dict를 그대로 저장한다 (L39-46). 값의 타입 검증이나 수치 변환이 없으며, LLM이 반환한 문자열("1,200원", "3억", "150%")이 그대로 `exchange_rates`, `total_assets`, `leverage` 리스트에 들어간다.
- **Evidence**:
  ```python
  # state_tracker_financial.py L39-46
  entry = {
      "exchange_rates": fin_events.get("exchange_rates", []),
      "total_assets": fin_events.get("total_assets", []),
      "leverage": fin_events.get("leverage", []),
      "key_transactions": fin_events.get("key_transactions", []),
  }
  self.tracker.financial_number_registry[arc_no] = entry
  # ← 타입 검증/수치 파싱 없음
  ```
- **Impact**: `get_financial_state_summary`(L70)에서 `latest_rate['value']`를 문자열로 출력할 뿐 수치 비교는 하지 않으므로, 현재 정밀도 손실은 없다. 그러나 향후 수치 비교/계산이 필요하면 타입 불안정 문제가 표면화된다. `_get_latest_financial_value`(L49-68)에서 `"value" in entry` 체크만 하므로, LLM이 `value` 키 없이 응답하면 해당 arc의 금융 데이터가 무시된다.
- **Suggested fix direction**: 현재 운영에서는 프롬프트 주입용 문자열 생성만 하므로 즉각 수정 불필요. 수치 비교가 필요해지면 파싱 레이어 추가.

---

### TF-ST-09: `resolved_plots` O(n) 중복 검사 -- IMPORTANT

- **Location**: `state_tracker_plots.py:L119-L123`
- **Description**: 새 플롯 추가 시 `any(p.get("plot") == entry["plot"] and p.get("arc_no") == arc_no for p in self.tracker.resolved_plots)` 로 O(n) 선형 탐색으로 중복을 검사한다. `resolved_plots`의 상한은 500개(L126-128)이지만, 매 추출마다 전수 비교한다.
- **Evidence**:
  ```python
  # L119-128
  if not any(
      p.get("plot") == entry["plot"] and p.get("arc_no") == arc_no
      for p in self.tracker.resolved_plots
  ):
      self.tracker.resolved_plots.append(entry)
      _max = int(getattr(self.tracker, "_resolved_plots_max", 500))
      if len(self.tracker.resolved_plots) > _max:
          self.tracker.resolved_plots = self.tracker.resolved_plots[-_max:]
  ```
- **Impact**: 500개 기준 O(n) 탐색은 성능 병목이 아니지만, `full_extract_from_arcs`에서 arc 수 * 플롯 수만큼 반복 호출되므로 O(arcs * plots * resolved_plots) 복잡도. 100 arc x 5 plots = 2,500회 탐색이 각각 최대 500개 리스트를 스캔한다.
- **Suggested fix direction**: `set` 기반 seen 캐시로 O(1) 중복 검사. 또는 `(plot, arc_no)` 튜플 set 유지.

---

### TF-ST-10: `check_suspended_plots`가 조회 + 수정을 동시에 수행 -- IMPORTANT

- **Location**: `state_tracker_plots.py:L371-L390`
- **Description**: `check_suspended_plots`는 조회 메서드처럼 보이지만 (이름이 `check_`), 실제로는 `info["status"] = "suspended"` (L380)로 상태를 수정한다. 이는 Command-Query Separation 위반이며, 특히 TF-ST-03의 멀티스레드 환경에서 위험하다.
- **Evidence**:
  ```python
  # L371-390
  def check_suspended_plots(self, current_arc_no: int, threshold: int = 3) -> list[dict]:
      warnings = []
      for plot_name, info in self.tracker.active_plots.items():
          if info.get("status") == "resolved":
              continue
          last_mention = info.get("last_mention_arc", 0)
          gap = current_arc_no - last_mention
          if gap >= threshold:
              info["status"] = "suspended"  # ← 조회 중 수정!
              warnings.append(...)
  ```
- **Impact**: `check_suspended_plots`가 호출될 때마다 side effect로 상태가 변경된다. 동일 조건에서 두 번 호출하면 두 번째는 빈 결과를 반환한다 (이미 suspended로 변경됨).
- **Suggested fix direction**: 상태 변경을 별도 메서드(`mark_suspended_plots`)로 분리. 또는 최소한 메서드명을 `detect_and_mark_suspended_plots`로 변경하여 부작용을 명시.

---

### TF-ST-11: `entity_destructions` 무제한 증가 -- INSIGHT

- **Location**: `state_tracker_plots.py:L156-L181`
- **Description**: `resolved_plots`(최대 500)와 `in_world_timeline`(최대 100)에는 상한이 있지만, `entity_destructions`에는 상한이 없다. `register_entity_destruction`(L183-187)에서도 `name` 기준 중복 방지만 있을 뿐 크기 제한이 없다.
- **Evidence**:
  ```python
  # L183-187
  def register_entity_destruction(self, name: str, entity_type: str, cause: str, arc_no: int):
      entry = {"name": name, "type": entity_type, "cause": cause, "arc_no": arc_no}
      if not any(e.get("name") == name for e in self.tracker.entity_destructions):
          self.tracker.entity_destructions.append(entry)
      # ← 상한 검사 없음
  ```
- **Impact**: 장기 연재(100+ Arc)에서 파괴된 엔티티가 계속 누적. `check_destroyed_entity_in_manuscript`(L189-218)에서 모든 엔티티에 대해 regex 매칭을 수행하므로, 성능 저하 가능성. 현실적으로 파괴 이벤트는 드물어서 (Arc당 0-2건) 심각한 문제는 아님.
- **Suggested fix direction**: `resolved_plots`와 유사한 상한 (예: 200건) 추가.

---

### TF-ST-12: `pending_commitments` 정리가 50개 초과 시에만 발동 -- INSIGHT

- **Location**: `state_tracker_plots.py:L722-L726`
- **Description**: `register_commitment`에서 50개 초과 시 fulfilled/broken 약속을 제거하지만, 정리 후에도 pending만 남기므로 이론적으로 50개 이상의 pending이 남을 수 있다. 또한 정리 시 `self.tracker.pending_commitments` 전체 리스트를 재생성하여 메모리 할당이 발생한다.
- **Evidence**:
  ```python
  # L722-726
  if len(self.tracker.pending_commitments) > 50:
      self.tracker.pending_commitments = [
          c for c in self.tracker.pending_commitments if c.get("status") == "pending"
      ]
  ```
- **Impact**: Minor. 약속 개수가 50을 초과하는 것은 장기 연재에서만 가능하며, 정리 후에는 pending만 남으므로 급격히 줄어든다.
- **Suggested fix direction**: 현행 유지 가능. 필요 시 pending도 상한 적용 (예: 가장 오래된 pending부터 제거).

---

### TF-ST-13: `extract_all_state_changes`와 `full_extract_from_arcs`의 중복 추출 위험 -- INSIGHT

- **Location**: `state_tracker.py:L1568-L1613` vs `state_tracker.py:L187-L249`
- **Description**: `extract_all_state_changes`(L1568)는 단일 arc에 대해 15개 추출 + 반환값 dict를 생성한다. `full_extract_from_arcs`(L187)는 arc 리스트에 대해 17개 추출을 수행하되 반환값 없이 내부 상태만 수정한다. 두 메서드가 동일 arc에 대해 순차 호출되면 **중복 등록** 문제가 발생한다:
  - 대부분의 extract 메서드에 중복 방지 로직이 있지만(`not any(...)`), 중복 검사 비용이 누적된다.
  - `extract_all_state_changes`의 반환값은 실제로 사용하는 곳이 없다 (기존 문서에서도 "미호출" 확인 -- `docs/이전/기억 개선 작업.md`의 M-4).
- **Impact**: Dead code는 아니지만 (protocol conformance 테스트에서 존재 확인), 실질적으로 사용되지 않는 메서드가 유지보수 부담을 추가한다.
- **Suggested fix direction**: `extract_all_state_changes`를 deprecation 주석으로 표시하거나, `full_extract_from_arcs`의 단일-arc 버전으로 통합.

---

### TF-ST-14: `in_world_timeline` pop(0) O(n) 비효율 -- INSIGHT

- **Location**: `state_tracker_plots.py:L457-L459`
- **Description**: 시간 마커 상한 유지 시 `while len(...) > 100: .pop(0)` 패턴을 사용한다. `list.pop(0)`는 O(n)이므로, 상한 초과 시 매번 리스트 전체를 시프트한다.
- **Evidence**:
  ```python
  # L457-459
  while len(self.tracker.in_world_timeline) > 100:
      self.tracker.in_world_timeline.pop(0)
  ```
- **Impact**: 상한이 100이고 초과분도 소량이므로 실질적 성능 영향은 미미. 그러나 `collections.deque(maxlen=100)` 사용 시 O(1)로 개선 가능.
- **Suggested fix direction**: `deque(maxlen=100)` 변경. 단, 기존 코드에서 `[-20:]` 슬라이싱(L539)이 deque에서도 지원되므로 호환성 문제 없음.

---

## 4. Summary Matrix

| ID | Title | Severity | Location | Category |
|----|-------|----------|----------|----------|
| TF-ST-01 | `merge_from_previous_arcs` 20+ 레지스트리 누락 | CRITICAL | state_tracker.py:L938-L950 | 데이터 소실 |
| TF-ST-02 | 핵심 4종 예외 시 전체 arc 추출 중단 | CRITICAL | state_tracker.py:L187-L249 | 에러 복원력 |
| TF-ST-03 | Advisory 8-thread 무잠금 동시 접근 | CRITICAL | state_tracker.py (전체) | 스레드 안전성 |
| TF-ST-04 | Snapshot/Restore 메커니즘 부재 | IMPORTANT | state_tracker.py (전체) | 상태 관리 |
| TF-ST-05 | active_plots / resolved_plots 이중 상태 | IMPORTANT | state_tracker_plots.py:L98-L369 | 데이터 일관성 |
| TF-ST-06 | `_populate_genre_registries` full_extract 미호출 | IMPORTANT | state_tracker.py:L1615 | 초기화 누락 |
| TF-ST-07 | bind_world_state 초기화 순서 불일치 | IMPORTANT | main_a.py:L4018 vs stage3:L638 | 초기화 순서 |
| TF-ST-08 | 금융 데이터 타입 검증 부재 | IMPORTANT | state_tracker_financial.py:L39-L46 | 타입 안전성 |
| TF-ST-09 | resolved_plots O(n) 중복 검사 | IMPORTANT | state_tracker_plots.py:L119-L123 | 성능 |
| TF-ST-10 | check_suspended_plots CQS 위반 | IMPORTANT | state_tracker_plots.py:L371-L390 | 설계 원칙 |
| TF-ST-11 | entity_destructions 무제한 증가 | INSIGHT | state_tracker_plots.py:L156-L187 | 메모리 |
| TF-ST-12 | pending_commitments 정리 조건 | INSIGHT | state_tracker_plots.py:L722-L726 | 메모리 |
| TF-ST-13 | extract_all_state_changes 중복/미사용 | INSIGHT | state_tracker.py:L1568-L1613 | 코드 위생 |
| TF-ST-14 | in_world_timeline pop(0) O(n) | INSIGHT | state_tracker_plots.py:L457-L459 | 성능 |

## 5. 핵심 코드 참조 (Appendix)

### A. full_extract_from_arcs 17-Extract 순서 맵

| # | Method | Module | 예외 처리 | 의존성 |
|---|--------|--------|-----------|--------|
| 1 | `extract_npc_deaths_from_arc` | NPC | **없음** (propagate) | 없음 |
| 2 | `extract_skill_acquisitions_from_arc` | NPC | **없음** (propagate) | 없음 |
| 3 | `extract_npc_info_from_arc` | NPC | **없음** (propagate) | #1의 death 정보 참조 가능 |
| 4 | `extract_resolved_plots_from_arc` | Plots | **없음** (propagate) | 없음 |
| 5 | `extract_time_markers_from_arc` | Plots | try/except Exception | 없음 |
| 6 | `extract_permanent_injuries_from_arc` | NPC | try/except Exception | 없음 |
| 7 | `update_companions_from_arc` | NPC | try/except Exception | 없음 |
| 8 | `extract_commitments_from_arc` | Plots | try/except Exception | 없음 |
| 9 | `extract_protagonist_emotion_from_arc` | NPC | try/except Exception | 없음 |
| 10 | `extract_item_states_from_arc` | Plots | try/except (K,V,T) | 없음 |
| 11 | `extract_entity_destructions_from_arc` | Plots | try/except (K,V,T) | 없음 |
| 12 | `extract_npc_personality_from_arc` | NPC | try/except (K,V,T) | #3의 NPC 등록 정보 |
| 13 | `extract_npc_npc_relationships_from_arc` | NPC | try/except (K,V,T) | 없음 |
| 14 | `extract_npc_dialogue_styles_from_arc` | NPC | try/except (K,V,T) | 없음 |
| 15 | `extract_relationship_changes_from_arc` | NPC | try/except Exception | 없음 |
| 16 | `extract_npc_injuries_from_arc` | NPC | try/except Exception | 없음 |
| 17 | `extract_npc_movements_from_arc` | NPC | try/except Exception | 없음 |
| 18* | `extract_financial_events_from_arc` | Financial | **없음** (조건부) | genre=="investment" 전용 |

순서 의존성 분석: #1(사망) → #3(NPC info)는 논리적 의존성이 있다. #1에서 사망 등록 후 #3에서 해당 NPC의 `status`가 `dead`로 설정되어 있기를 기대한다. **#1이 실패하면 #3에서 사망 NPC가 alive로 잘못 등록될 수 있다.** 다른 추출 메서드들은 각각 독립적이다.

### B. StateTracker 속성 전수 목록 (23+ mutable registries)

```
__init__에서 초기화되는 mutable 상태:
L119: states: dict[int, EpisodeState]
L120: transitions: list[StateTransition]
L121: global_items: set[str]
L122: acquired_items: dict[str, int]
L123: consumed_items: dict[str, int]
L126: npc_registry: dict[str, dict]
L128: protagonist_skills: set[str]
L129: skill_acquisitions: dict[str, int]
L132: resolved_plots: list[dict]
L135: entity_name_registry: OrderedDict
L138: entity_destructions: list[dict]
L140: npc_npc_relationships: dict
L142: skill_cooldown_registry: dict
L143: dungeon_clear_registry: dict
L144: spell_repertoire: dict
L145: blessing_curse_registry: dict
L146: filmography_registry: dict
L148: item_state_registry: dict
L150: active_plots: dict
L152: npc_dialogue_profiles: dict
L155: in_world_timeline: list
L158: current_companions: list
L161: pending_commitments: list
L164: protagonist_emotion: dict
L167: financial_number_registry: dict[int, dict]
L256: tracking_fields: dict[str, Any]
```

### C. 초기화 호출 사이트 비교

| 호출 사이트 | bind_db | bind_world_state | full_extract | populate_genre |
|------------|---------|-----------------|--------------|----------------|
| main_a.py L4013 | L4018 (1st) | L4050 (3rd, after WS creation) | L4021 (2nd) | 미호출 |
| stage3_orchestrator L630 | L638 (1st) | L639 (2nd) | L642 (3rd) | 미호출 |
| stage2_orchestrator L290 | L293 (1st) | L294 (2nd) | L303 (3rd) | stage2_preflight에서 별도 |
| create_tracker_from_arcs L1641 | 미호출 | 미호출 | 미호출 (load_arc_design 사용) | 미호출 |
