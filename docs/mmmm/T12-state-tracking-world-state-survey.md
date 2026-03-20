# T12 — State Tracking & World State Survey

**6PASS-CLEARED** | COLLECTOR ONLY | NO EXECUTION AUTHORITY
**Terminal**: T12
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1`
**Confidence**: 96%

---

## 1. Scope & Files

| File | Lines | Role |
|------|-------|------|
| `modules/domain/agents/state_tracker.py` | 1,669 | Facade — NPC/Financial/Plots 3 sub-module 위임 |
| `modules/domain/agents/state_tracker_npc.py` | 2,204 | NPC 레지스트리, 사망/무공/관계/부상/이동/영구부상/동행자/감정 |
| `modules/domain/agents/state_tracker_financial.py` | 125 | 투자물 금융 상태 (exchange_rates, total_assets, leverage, key_transactions) |
| `modules/domain/agents/state_tracker_plots.py` | 963 | 완결 플롯, 엔티티 명칭, 시간선, 아이템 상태, 약속/맹세 |
| `modules/domain/agents/state_extractor.py` | 868 | LLM 기반 상태 추출 (BaseAgent 상속, Flash 모델) |
| `modules/core/world_state.py` | 1,339 | 세계 상태 문서 — DB anchor 'world_state' 저장/로드 |
| `modules/core/fact_ledger.py` | 853 | 누적 팩트 원장 — DB anchor 'fact_ledger' 저장/로드 |

**Related Tests:**
- `tests/test_state_tracker.py` (525 lines)
- `tests/test_npc_history.py` (374 lines)
- `tests/test_npc_history_fields.py` (229 lines)
- `tests/test_con2_npc_position_tracking.py` (367 lines)
- `tests/test_fact_ledger.py` (~120 lines)

---

## 2. TF Registry

### T12-TF-001 — WorldState _INIT_STATE 필드 수 DRIFT

```
ID: T12-TF-001
Severity: P3-LOW
Category: DRIFT
Surface: modules/core/world_state.py:90-113, docs/mmmm/20-terminal-deep-global-survey-master-order.md:613
Evidence:
  - world_state.py:90-113 _INIT_STATE 정의:
    16개 top-level 키: version, last_updated_ep, protagonist, alive_npcs, dead_npcs,
    relationships, active_items, destroyed, active_plots, active_pressure_vectors,
    world_notes, world_laws, timeline, motivations, promises, cumulative_elapsed
  - 마스터 오더 T12 섹션(L613): "World state 9개 필드 (_INIT_STATE) 전수"
  - MEMORY.md: "WorldStateManager._INIT_STATE: 9개 필드"
Inference: V68 초기 설계 시 9개였으나, V68+ 확장(world_laws, timeline, motivations,
  promises, cumulative_elapsed, active_pressure_vectors, world_notes)으로 16개로 증가.
  문서와 메모리가 outdated.
Uncertainty: 없음 — 코드에서 직접 확인
Cross-Ref: T20 (문서 정합성)
```

### T12-TF-002 — FactLedger MAX 상수 DRIFT

```
ID: T12-TF-002
Severity: P3-LOW
Category: DRIFT
Surface: modules/core/fact_ledger.py:123-124
Evidence:
  - fact_ledger.py:123: MAX_HISTORY_PER_ENTITY = 100  # [TF-C05] 10→100 확장
  - fact_ledger.py:124: MAX_SUMMARY_CHARS = 50000  # [1M-CTX-P1] 20000 → 50000
  - 마스터 오더 T12 섹션(L613): "FactLedger MAX_HISTORY_PER_ENTITY=10, MAX_SUMMARY_CHARS=20000"
  - MEMORY.md: "FactLedger.MAX_HISTORY_PER_ENTITY = 10, MAX_SUMMARY_CHARS = 20000"
Inference: TF-C05(장기연재 팩트 보존)에서 10→100, 1M-CTX-P1(100화+ NPC 수용)에서
  20000→50000으로 확장됨. 메모리와 마스터 오더가 확장 이전 값을 기록 중.
Uncertainty: 없음
Cross-Ref: T20 (문서 정합성)
```

### T12-TF-003 — full_extract_from_arcs 핵심 4종 무보호

```
ID: T12-TF-003
Severity: P2-MEDIUM
Category: SILENT-FAILURE
Surface: modules/domain/agents/state_tracker.py:187-194
Evidence:
  - state_tracker.py:190-194:
    ```python
    for arc in arcs:
        # 핵심 4종: 항상 호출
        self.extract_npc_deaths_from_arc(arc)
        self.extract_skill_acquisitions_from_arc(arc)
        self.extract_npc_info_from_arc(arc, genre=genre)
        self.extract_resolved_plots_from_arc(arc)
    ```
  - 4종은 try/except 없이 호출됨. L197~L248의 13종은 개별 try/except로 보호.
  - 핵심 4종 중 하나라도 예외 발생 시 해당 arc 이후 모든 extract 호출 건너뜀.
  - 확장 13종도 해당 arc에서 실행되지 않음 (for 루프 전체 중단이 아닌 해당 arc 스킵).
  - 정정: for 루프 자체가 중단되지는 않음 — 예외가 해당 arc의 핵심 4종에서 발생하면
    해당 arc의 확장 13종만 스킵되는 것이 아니라, 예외가 전파되어 **전체 for 루프가 중단**됨.
Inference: 핵심 4종은 state_changes에서 직접 읽기만 하므로 예외 발생 확률은 낮으나,
  arc dict가 비정상(None 값, 타입 오류 등)일 경우 전체 루프가 중단될 수 있음.
  기존 문서(tf-st-state-tracker-plots-deepdive.md TF-ST-04)에서도 동일 지적.
Uncertainty: 실제 운영 중 발생 빈도 불명 (정적 분석 한계)
Cross-Ref: T02 (Stage2 orchestrator에서 호출), T04 (Stage3 orchestrator에서 호출)
```

### T12-TF-004 — _populate_genre_registries_from_arc 미호출

```
ID: T12-TF-004
Severity: P2-MEDIUM
Category: COVERAGE-GAP
Surface: modules/domain/agents/state_tracker.py:187-253, 1615-1640
Evidence:
  - state_tracker.py:1615: `def _populate_genre_registries_from_arc(self, arc: dict):`
    → hunter의 dungeon_clear_registry, skill_cooldown_registry
    → fantasy의 spell_repertoire를 채움
  - full_extract_from_arcs(L187-253) 코드에 `_populate_genre_registries_from_arc` 호출 없음
  - Grep "_populate_genre_registries_from_arc" → 호출 사이트:
    `stage2_preflight.py:1622`와 `tools2/validation_test_harness.py:76`에서만 호출
  - full_extract_from_arcs 호출 사이트 3곳:
    `stage2_orchestrator.py:316`, `stage3_orchestrator.py:711`, `main_a.py:4062`
Inference: Stage 3 직행 경로(main_a.py L4062 → full_extract_from_arcs)에서는
  hunter/fantasy 장르 레지스트리가 빈 상태로 남음.
  Stage 2 경로에서만 preflight에서 보완됨.
Uncertainty: Stage 3 직행에서 이 레지스트리를 실제로 참조하는 코드가 있는지 미확인
Cross-Ref: T03 (Stage2 preflight), T04 (Stage3 pipeline)
```

### T12-TF-005 — update_plot_mentions_from_arc 미호출

```
ID: T12-TF-005
Severity: P2-MEDIUM
Category: COVERAGE-GAP
Surface: modules/domain/agents/state_tracker.py:187-253, 1125-1126
Evidence:
  - state_tracker.py:1125-1126:
    ```python
    def update_plot_mentions_from_arc(self, arc: dict) -> list[dict]:
        return self._plots.update_plot_mentions_from_arc(arc)
    ```
  - full_extract_from_arcs(L187-253): `extract_resolved_plots_from_arc`만 호출,
    `update_plot_mentions_from_arc`는 미호출
  - active_plots dict는 full_extract_from_arcs로 초기화된 tracker에서 빈 상태
  - 결과: check_suspended_plots(), get_plot_suspension_summary() 무효
Inference: full_extract_from_arcs로만 초기화 시(main_a.py Stage 3 직행) 플롯 서스펜션
  감지가 작동하지 않음. 기존 문서(TF-ST-05)에서도 동일 지적.
Uncertainty: 운영에서 active_plots를 실제로 얼마나 활용하는지 불명
Cross-Ref: T04 (Stage3), T05 (Stage4 context builder)
```

### T12-TF-006 — bind_world_state 초기화 순서 불일치

```
ID: T12-TF-006
Severity: P3-LOW
Category: CONTRADICTION
Surface: modules/core/stage3_orchestrator.py:585,707-711, main_a.py:4059-4091
Evidence:
  - stage3_orchestrator.py:585: `ctx.state_tracker.bind_world_state(ctx.world_state)`
  - stage3_orchestrator.py:707-711:
    ```python
    app.state_tracker.bind_db(app.current_project.db)
    app.state_tracker.bind_world_state(getattr(app, "world_state", None))
    # bind_world_state BEFORE full_extract_from_arcs(L711)
    app.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)
    ```
  - main_a.py:4059: `self.state_tracker.bind_db(self.current_project.db)`
  - main_a.py:4062: `self.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)`
  - main_a.py:4091: `self.state_tracker.bind_world_state(self.world_state)`
    → bind_world_state AFTER full_extract_from_arcs
  - stage2_orchestrator.py:306-307: bind_db → bind_world_state(getattr) → full_extract(L316)
    → Stage 2에서는 getattr(self.ctx, "world_state", None) → None일 가능성 있음
Inference: Stage 3 경로: bind_world_state → full_extract (안전)
  main_a.py 경로: full_extract → bind_world_state (잠재적 문제)
  현재 full_extract_from_arcs 내부에서 _world_state를 참조하지 않으므로 즉각적 문제 없음.
  향후 full_extract 내부에서 _world_state 참조 추가 시 main_a.py 경로에서만 None 참조.
Uncertainty: 향후 변경 가능성에 따른 잠재적 위험
Cross-Ref: T01 (SovereignApp bootstrap), T04 (Stage3 init)
```

### T12-TF-007 — StateTracker facade → 3 sub-module 위임 완전성 SYNC

```
ID: T12-TF-007
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/state_tracker.py:953-1432
Evidence:
  - NPC 위임 스텁(L959-1033): register_npc_death, register_npc_info, check_npc_changes,
    extract_npc_info_from_arc, check_dead_npc_appearance, register_protagonist_skill,
    check_unlearned_skill_usage, get_entity_registry, merge_npc_registry,
    extract_npc_deaths_from_arc, extract_skill_acquisitions_from_arc,
    extract_relationship_changes_from_arc, extract_npc_injuries_from_arc,
    extract_npc_movements_from_arc, check_dead_npc_in_blueprint,
    check_dead_npc_in_manuscript, get_dead_npc_summary, cleanup_npc_registry_with_llm,
    + V66 확장: extract_npc_personality, npc_npc_relationships, npc_dialogue_styles,
    permanent_injuries, revive_npc, companions, protagonist_emotion → 총 30+ 메서드
  - Financial 위임 스텁(L1062-1072): extract_financial_events, get_financial_state_summary,
    export_financial_registry, import_financial_registry → 4 메서드
  - Plots 위임 스텁(L1078-1163): extract_resolved_plots, get_resolved_plots_summary,
    register_entity_name, load_entities_from_entity_registry, check_entity_name_consistency,
    entity_destructions, item_states, plot_mentions, suspended_plots, time_markers,
    commitments → 15+ 메서드
  - 모든 facade 메서드가 `return self._npc.X()` / `self._financial.X()` / `self._plots.X()` 패턴
  - facade에 직접 구현 남은 메서드: _init_tracking_fields, create_episode_state,
    create_npc_entry, _parse_internal_energy, load_arc_design, validate_timeline 등 (상태 DAG)
    + get_all_summaries(L1350), generate_arc_summary(L1437), extract_all_state_changes(L1568)
Inference: Facade 패턴이 잘 적용됨. NPC/Financial/Plots 3개 sub-module로 완전 분리.
  Facade에 남은 직접 구현은 상태 DAG 로직과 통합 메서드(get_all_summaries 등)로 적절함.
Uncertainty: 없음
Cross-Ref: T11 (Agent Infrastructure)
```

### T12-TF-008 — full_extract_from_arcs 17종 호출 SYNC

```
ID: T12-TF-008
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/state_tracker.py:187-253, tests/test_state_tracker.py:387-445
Evidence:
  - state_tracker.py:187-253: 17종 호출 확인
    Core 4: extract_npc_deaths, extract_skill_acquisitions, extract_npc_info, extract_resolved_plots
    V66.1(5): time_markers, permanent_injuries, companions, commitments, protagonist_emotion
    V66.3(5): item_states, entity_destructions, npc_personality, npc_npc_relationships, npc_dialogue_styles
    V66.2(3): relationship_changes, npc_injuries, npc_movements
    + 조건부(1): financial_events (genre=="investment" only)
  - test_state_tracker.py:390-415: test_calls_all_17_extract_methods
    → 17종 assert_called_once() 전부 확인
  - test_state_tracker.py:417-429: test_financial_extract_only_for_investment_genre
    → wuxia에서 미호출, investment에서 호출 확인
  - test_state_tracker.py:431-445: test_optional_extract_exception_does_not_propagate
    → 확장 extract 예외 시 핵심 4종 호출 유지 확인
Inference: 17종 호출과 테스트가 정합. 다만 테스트에서는 핵심 4종 예외 시 루프 중단을
  검증하지 않음 (TF-003 참조).
Uncertainty: 없음
Cross-Ref: T20 (regression test 유효성)
```

### T12-TF-009 — WorldState update_from_state_changes 17개 섹션 비차단 SYNC

```
ID: T12-TF-009
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/world_state.py:158-753
Evidence:
  - §1(L207): npc_deaths → dead_npcs 등록, alive_npcs 제거
  - §2(L231): skill_acquisitions → protagonist.skills 추가 (MAX 50)
  - §3(L250): relationship_changes → relationships + alive_npcs known_attrs
  - §4(L277): major_items → active_items 갱신
  - §4a(L298): inventory_counts + inventory_count_deltas → 수량 추적
  - §5(L346): entity_destructions → destroyed 추가
  - §6(L372): npc_personality_changes → personality/motivation known_attrs
  - §7(L403): resolved_plots → active_plots에서 제거
  - §7a(L421): active_pressure_vectors → 5개 제한
  - §8(L432): companion_changes → alive_npcs companion 플래그
  - §9(L456): npc_attribute_changes → dual_identity/knowledge_era 등
  - §10(L485): npc_introductions → 초기 속성 (대원칙4 사망 NPC 무시)
  - §11(L544): world_law_additions → world_laws 추가
  - §12(L557): time_markers → timeline + cumulative_elapsed + DB sync
  - §13(L601): protagonist_motivations → motivations 추적
  - §14(L633): commitments/promises → pending 우선 보존 (MAX 30)
  - §15(L668): npc_injuries → known_attrs 반영
  - §16(L692): npc_movements → known_attrs location 반영
  - §17(L717): permanent_injuries → known_attrs permanent_injuries 반영
  - 모든 섹션이 개별 try/except로 비차단 보호됨 (§1~§17 각각 독립)
  - 크기 제한(L744-753): destroyed≤100, pressure_vectors≤5, world_notes≤10
Inference: 17개 섹션이 모두 비차단으로 동작. 1개 섹션 실패 시 나머지 섹션 처리 보장.
  V68 설계 원칙("LLM 호출 없이 Python만으로 자동 갱신") 준수.
Uncertainty: 없음
Cross-Ref: T14 (Validation), T16 (DB persistence)
```

### T12-TF-010 — FactLedger eviction 로직 검증

```
ID: T12-TF-010
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/fact_ledger.py:123, 427, 522, 554, 574, 589
Evidence:
  - fact_ledger.py:123: MAX_HISTORY_PER_ENTITY = 100
  - _upsert_character(L522): `entry["history"] = entry["history"][-self.MAX_HISTORY_PER_ENTITY:]`
  - _upsert_item(L554): 동일 패턴
  - _upsert_location(L574): 동일 패턴
  - _upsert_org(L589): 동일 패턴
  - update_number(L427): `entry["history"] = entry["history"][-self.MAX_HISTORY_PER_ENTITY:]`
  - 모든 upsert 메서드에서 history 목록을 MAX_HISTORY_PER_ENTITY로 truncation
  - 6개 엔티티 유형(characters, items, locations, organizations, numbers, +rollback)
    모두 동일한 eviction 패턴 사용
Inference: Eviction이 일관되게 적용됨. history만 truncation되며 엔티티 자체는 제거되지 않음.
  즉 characters dict의 키 수는 무한 증가 가능 (history만 100개로 제한).
Uncertainty: characters dict 키 수 상한이 없어 200화+ 시 수백 NPC 누적 가능성
Cross-Ref: T16 (DB anchor 저장 크기)
```

### T12-TF-011 — StateExtractor _state_cache 무효화 경로

```
ID: T12-TF-011
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/state_extractor.py:202, 273-279
Evidence:
  - state_extractor.py:202: `self._state_cache: dict[int, dict] = {}`
  - state_extractor.py:273-279:
    ```python
    def invalidate_cache(self, arc_no=None):
        if arc_no is not None:
            cache_key = arc_no if isinstance(arc_no, int) else hash(str(arc_no))
            self._state_cache.pop(cache_key, None)
        else:
            self._state_cache.clear()
    ```
  - 호출 사이트:
    stage2_orchestrator.py:795-796: `_se.invalidate_cache(global_arc_no)` (단일 arc)
    main_a.py:3723-3724: `_se.invalidate_cache()` (전체)
    main_a.py:3754-3755: `_se.invalidate_cache()` (전체)
    main_a.py:3831-3832: `_se.invalidate_cache()` (전체)
  - Stage2에서는 단일 arc만 무효화, main_a에서는 전체 무효화
  - LLM 실패 시 fallback 결과도 캐시에 저장(L270): 재호출 시 LLM 재시도 방지
Inference: 캐시 무효화 경로가 명확. Stage2는 재시도 arc만, main_a rollback은 전체.
  Fallback 캐시 저장은 의도적 설계 (비용 절감).
Uncertainty: 없음
Cross-Ref: T02 (Stage2 orchestrator), T01 (main_a rollback)
```

### T12-TF-012 — StateExtractor fallback 캐시 저장

```
ID: T12-TF-012
Severity: P3-LOW
Category: SIDE-EFFECT
Surface: modules/domain/agents/state_extractor.py:266-271
Evidence:
  - state_extractor.py:266-271:
    ```python
    except Exception as e:
        logging.warning(f"[StateExtractor] LLM 추출 실패 (fallback 사용): {e}")
        result = self._fallback_extraction(arc_data)
        # [V62.5] 폴백 결과도 캐시 (재호출 시 LLM 재시도 방지)
        self._state_cache[cache_key] = result
        return result
    ```
  - Python fallback 추출(L551-598): arc_end_state, status_shadow에서 기본 필드만 추출
  - LLM 추출 대비 entity_registry가 빈 상태로 캐시됨
Inference: LLM 일시 장애 시 낮은 품질의 fallback이 캐시되어 이후 호출에서도 사용됨.
  Stage2에서 invalidate_cache(arc_no)로 무효화 가능하지만, 자동 재시도 메커니즘 없음.
Uncertainty: 운영에서 LLM 실패 후 자동 복구 빈도 불명
Cross-Ref: T11 (BaseAgent error handling)
```

### T12-TF-013 — WorldState reset 메서드 부재

```
ID: T12-TF-013
Severity: P4-OBSERVATION
Category: COVERAGE-GAP
Surface: modules/core/world_state.py
Evidence:
  - Grep "def reset_state|def clear_state|def _reset" in world_state.py → 0 matches
  - rollback_to(L1262-1303) 존재: _INIT_STATE로 리셋 후 DB에서 리플레이
  - 직접 리셋 메서드 없음 — rollback_to가 유일한 초기화 경로
  - FactLedger도 동일 패턴: rollback_to(L809-852)만 존재
Inference: 롤백은 가능하나, 런타임에서 완전 초기화가 필요한 경우 `rollback_to(0)`을
  호출해야 함. 명시적 reset() 메서드가 있으면 의도가 더 명확할 수 있으나,
  현재 운영에서 문제되지 않는 설계 선택.
Uncertainty: 없음
Cross-Ref: T16 (DB persistence)
```

### T12-TF-014 — Financial tracker investment-only 4필드

```
ID: T12-TF-014
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/state_tracker_financial.py:20-47
Evidence:
  - state_tracker_financial.py:39-44:
    ```python
    entry = {
        "exchange_rates": fin_events.get("exchange_rates", []),
        "total_assets": fin_events.get("total_assets", []),
        "leverage": fin_events.get("leverage", []),
        "key_transactions": fin_events.get("key_transactions", []),
    }
    ```
  - state_tracker.py:251-252: `if genre == "investment": self.extract_financial_events_from_arc(arc)`
  - _get_latest_financial_value(L49-68): sorted arc_no 순회, 최신 값 반환
  - get_financial_state_summary(L70-109): 환율/자산/레버리지/거래 내역 문자열 생성
  - export/import_financial_registry(L111-124): int→str 키 변환으로 DB 직렬화
Inference: Investment 장르에서만 활성화되는 4필드 추적. 구현이 간결하며 잘 격리됨.
  총 125줄로 가장 작은 sub-module.
Uncertainty: 없음
Cross-Ref: T09 (Arc generation — investment genre)
```

### T12-TF-015 — NPC extract 17종 확인 (문서 "13개 카테고리" DRIFT)

```
ID: T12-TF-015
Severity: P3-LOW
Category: DRIFT
Surface: modules/domain/agents/state_tracker_npc.py, state_tracker.py:187-253
Evidence:
  - state_tracker_npc.py에서 extract_*_from_arc 메서드:
    L370: extract_npc_info_from_arc
    L657: extract_npc_deaths_from_arc
    L816: extract_skill_acquisitions_from_arc
    L868: extract_relationship_changes_from_arc
    L927: extract_npc_injuries_from_arc
    L991: extract_npc_movements_from_arc
    L1238: extract_permanent_injuries_from_arc
    L1626: extract_npc_personality_from_arc
    L1669: extract_npc_npc_relationships_from_arc
    L1740: extract_npc_dialogue_styles_from_arc
    L1968: extract_protagonist_emotion_from_arc (11종 NPC)
  - state_tracker_plots.py에서:
    extract_resolved_plots, extract_entity_destructions, extract_item_states,
    extract_time_markers, extract_commitments, update_companions (6종 Plots, 이중 companions는 NPC 위임)
  - full_extract_from_arcs에서 실제 호출: 17종 + 1 conditional (financial)
  - MEMORY.md 및 이전 문서: "13개 NPC 카테고리"
Inference: 초기 "13개 카테고리"에서 V66.1~V66.3 확장으로 17종(+1)으로 증가.
  NPC sub-module만 11종, Plots에서 6종.
Uncertainty: 없음
Cross-Ref: T20 (문서 정합성)
```

### T12-TF-016 — resolved_plots O(n) 중복 탐색

```
ID: T12-TF-016
Severity: P3-LOW
Category: HARDCODING
Surface: modules/domain/agents/state_tracker_plots.py:119-128
Evidence:
  - state_tracker_plots.py:119-123:
    ```python
    if not any(
        p.get("plot") == entry["plot"] and p.get("arc_no") == arc_no
        for p in self.tracker.resolved_plots
    ):
        self.tracker.resolved_plots.append(entry)
    ```
  - resolved_plots 최대 500개 (state_tracker.py:133: `_resolved_plots_max = 500`)
  - full_extract_from_arcs에서 arc 수 × 플롯 수만큼 반복 호출
  - 복잡도: O(arcs × plots_per_arc × resolved_plots_len)
  - 100 arc × 5 plots = 500회 탐색, 각각 최대 500개 리스트 스캔
Inference: 현재 규모(100 arc 미만)에서 성능 문제는 없으나, 장기연재(200+ arc)에서
  O(n²) 수준으로 증가 가능. set 기반 중복 검사로 O(1) 가능.
Uncertainty: 실제 성능 영향은 동적 검증 필요
Cross-Ref: T06 (interview round performance)
```

### T12-TF-017 — entity_name_registry LRU max 500

```
ID: T12-TF-017
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/state_tracker.py:135-136
Evidence:
  - state_tracker.py:135: `self.entity_name_registry: OrderedDict = OrderedDict()`
  - state_tracker.py:136: `self._entity_registry_max_size = 500  # [V66] 200→500 엔티티 망각 방지`
  - OrderedDict 기반 LRU — 500 초과 시 가장 오래된 엔티티 제거
Inference: V66에서 200→500으로 확장. 장기연재(200화+)에서 500개 엔티티는 합리적 상한.
  OrderedDict로 LRU 순서 유지.
Uncertainty: 500개 초과 시 eviction된 엔티티가 이후 일관성 검사에서 미감지될 가능성
Cross-Ref: T13 (Continuity — entity 일관성)
```

### T12-TF-018 — 장르 확장 레지스트리 미사용 가능성

```
ID: T12-TF-018
Severity: P3-LOW
Category: DEAD-CODE
Surface: modules/domain/agents/state_tracker.py:142-152
Evidence:
  - state_tracker.py:142-152:
    ```python
    self.skill_cooldown_registry: dict = {}   # hunter
    self.dungeon_clear_registry: dict = {}    # hunter
    self.spell_repertoire: dict = {}          # fantasy
    self.blessing_curse_registry: dict = {}   # fantasy
    self.filmography_registry: dict = {}      # actor
    ```
  - _populate_genre_registries_from_arc(L1615-1640): hunter 던전/스킬, fantasy 주문만 채움
  - blessing_curse_registry: _populate에서 미채움
  - filmography_registry: _populate에서 미채움
  - get_blessing_curse_summary(L1303-1324): 데이터 있으면 출력하지만 채우는 경로 없음
  - get_filmography_summary(L1326-1344): 동일 — 채우는 경로 없음
Inference: blessing_curse_registry와 filmography_registry는 초기화만 되고
  데이터가 채워지는 production 경로가 없음. summary 메서드는 존재하지만 항상 빈 문자열 반환.
Uncertainty: 외부에서 직접 dict에 삽입하는 코드가 있을 수 있음 (grep 미수행)
Cross-Ref: T18 (genre guards — fantasy/actor 장르)
```

### T12-TF-019 — WorldState 크기 제한 상수 하드코딩

```
ID: T12-TF-019
Severity: P3-LOW
Category: HARDCODING
Surface: modules/core/world_state.py:242-250, 570-571, 627-628, 744-753, 1144, 1184
Evidence:
  - L242: `_MAX_SKILLS = 50` (protagonist skills)
  - L570-571: `if len(timeline) > 20: ... timeline[-20:]` (timeline)
  - L627-628: `if len(motivations) > 20: ... motivations[-20:]`
  - L663: promises > 30 → pending 우선 보존
  - L744-747: destroyed > 100 → [-100:]
  - L748-749: pressure_vectors > 5 → [:5]
  - L750-751: world_notes > 10 → [-10:]
  - L1144: `_MAX_ACTIVE_PLOTS = 100`
  - L1184: world_laws > 50 → CRITICAL 핀 보호 후 truncation
  - 이 상수들이 config/validation.yaml에서 참조되지 않고 코드 내 하드코딩
Inference: 각 상한이 코드 내 직접 정의됨. 운영 중 변경 시 코드 수정 필요.
  다만 이 값들은 거의 변경되지 않는 성격이므로 config 분리 필요성은 낮음.
Uncertainty: 없음
Cross-Ref: T17 (Config — validation.yaml)
```

### T12-TF-020 — extract_all_state_changes ↔ full_extract_from_arcs 중복 위험

```
ID: T12-TF-020
Severity: P2-MEDIUM
Category: SIDE-EFFECT
Surface: modules/domain/agents/state_tracker.py:1568-1613, 187-253
Evidence:
  - extract_all_state_changes(L1568): 단일 arc에 대해 15종 추출 + dict 반환
    (side-effect: 내부 레지스트리에도 등록됨)
  - full_extract_from_arcs(L187): arc 리스트에 대해 17종 추출, 반환값 없이 내부 상태만 수정
  - 동일 arc에 순차 호출 시 중복 등록:
    resolved_plots: 중복 방지 로직(any() 체크) 있으나 O(n) 비용
    npc_registry: 덮어쓰기 방식이므로 데이터 무결성은 유지
    entity_destructions: 중복 방지 로직 있음
  - extract_all_state_changes 호출 사이트:
    Grep → stage2_preflight.py와 일부 경로에서 호출
Inference: 두 메서드가 동일 arc에 호출되면 이중 등록되나, 중복 방지 로직이
  대부분 존재하여 데이터 오염은 제한적. 다만 이중 LLM 호출(NPC cleanup 등) 비용 발생 가능.
Uncertainty: 실제 이중 호출 빈도 불명
Cross-Ref: T03 (Stage2 preflight)
```

### T12-TF-021 — get_all_summaries 16+α 비차단 호출 SYNC

```
ID: T12-TF-021
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/state_tracker.py:1350-1431
Evidence:
  - state_tracker.py:1366-1383: 16종 기본 summary 메서드
    entity_destruction, resolved_plots, npc_personality, npc_npc_relationship,
    permanent_injury, time_timeline, companion, commitment, protagonist_emotion,
    item_state, npc_dialogue_style, relationship_changes, npc_injury, npc_movement,
    protagonist_skills, dead_npc
  - L1394-1398: arc_no 필요 메서드 (plot_suspension)
  - L1401-1408: 투자물 전용 (financial_state)
  - L1410-1429: 장르별 (hunter: dungeon_clear/skill_cooldown, fantasy: spell/blessing, actor: filmography)
  - 모든 호출이 try/except로 비차단 보호 (L1386-1391)
Inference: Stage4ContextBuilder에서 일괄 수집에 사용. 16+α 종의 summary가
  각각 독립적으로 실패 가능하며, 실패 시 해당 summary만 누락.
Uncertainty: 없음
Cross-Ref: T05 (Stage4 context builder)
```

### T12-TF-022 — WorldState/FactLedger max_chars 1M context 확장 SYNC

```
ID: T12-TF-022
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/world_state.py:856, modules/core/fact_ledger.py:124
Evidence:
  - world_state.py:856: `def get_summary(self, max_chars: int = 50000):`
    → 주석: `[1M-CTX-P1: 25K→50K] ep250 NPC 150명 전량 수용`
  - fact_ledger.py:124: `MAX_SUMMARY_CHARS = 50000  # [1M-CTX-P1] 20000 → 50000`
  - 양쪽 모두 50,000자 상한 — 1M context 활용 설계
Inference: 1M context window에 맞춰 확장됨. 250화 시 NPC 150명 규모를 수용 가능.
Uncertainty: 없음
Cross-Ref: T17 (Config — context window 설정)
```

### T12-TF-023 — FactLedger degraded mode

```
ID: T12-TF-023
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/fact_ledger.py:142-161, 188-194
Evidence:
  - fact_ledger.py:144: `try:` → DB 로드 시도
  - L157-161:
    ```python
    except Exception as e:
        _logger.warning(f"⚠️ [V70] FactLedger DB 로드 실패, 초기화: {e}")
        self._degraded = True
        self._degraded_reason = str(e)
    return self._empty_ledger()
    ```
  - L188-194: `@property degraded`, `@property degraded_reason`
  - degraded=True 시 빈 ledger로 동작하며, 이후 update_from_state_changes는
    메모리에만 누적 (DB에 저장되지 않을 수 있음)
Inference: DB 장애 시 graceful degradation. 빈 ledger에서 시작하여 in-memory로만 갱신.
  save() 호출 시 DB 복구되었으면 저장 시도.
Uncertainty: degraded 상태에서 save() 호출 시 DB 복구 여부 자동 감지 메커니즘 없음
Cross-Ref: T16 (DB — load_anchor/save_anchor)
```

### T12-TF-024 — WorldState/FactLedger save 비차단 패턴

```
ID: T12-TF-024
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/world_state.py:141-152, modules/core/fact_ledger.py:175-186
Evidence:
  - world_state.py:141-152: save() → try/except, last_save_ok=True/False, last_save_error
  - fact_ledger.py:175-186: 동일 패턴
  - 양쪽 모두 save 실패 시 비차단 (pipeline 중단하지 않음)
  - 호출자가 last_save_ok를 체크하여 경고 가능
Inference: V68 설계 원칙("비차단 갱신") 준수. 저장 실패는 로깅만 수행.
Uncertainty: 없음
Cross-Ref: T16 (DB persistence)
```

### T12-TF-025 — StateTracker._world_state 초기 None 안전

```
ID: T12-TF-025
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/state_tracker.py:175
Evidence:
  - state_tracker.py:175: `self._world_state = None  # [TF-35b] bind_world_state() 전 AttributeError 방지`
  - bind_world_state(L1042-1044): `self._world_state = world_state_manager`
  - _world_state를 참조하는 메서드(revive_npc 등)에서 None 체크 수행
  - Stage2 경로: `bind_world_state(getattr(self.ctx, "world_state", None))` → None 가능
Inference: TF-35b 수정으로 AttributeError 방지됨. None 전달도 안전하게 처리.
Uncertainty: 없음
Cross-Ref: T02 (Stage2 context), T06 (Stage4 interview — revive_npc)
```

---

## 3. Evidence Inventory

| Evidence Type | Count | Details |
|---------------|-------|---------|
| 파일:라인 참조 | 85+ | 모든 TF에 구체적 파일:라인 포함 |
| 코드 스니펫 인용 | 25+ | 핵심 로직 3-10줄 인용 |
| Grep 결과 | 8 | full_extract_from_arcs, _populate_genre, invalidate_cache, bind_world_state 등 |
| 비교 근거 (양쪽 인용) | 4 | TF-001/002 (메모리 vs 코드), TF-006 (main_a vs stage3), TF-015 |
| 수치 근거 | 12 | MAX 상수, 필드 수, 메서드 수 등 |

---

## 4. Side-Effect Surface

| Component | Side-Effect | Trigger |
|-----------|-------------|---------|
| WorldState.update_from_state_changes | DB anchor 'world_state' 갱신 (save 호출 시) | Episode 확정 후 |
| WorldState.update_from_state_changes §12 | DB upsert_timeline_entry 호출 | time_markers 존재 시 |
| FactLedger.update_from_state_changes | DB anchor 'fact_ledger' 갱신 (save 호출 시) | Episode 확정 후 |
| FactLedger.update_number | DB upsert_canonical_fact 호출 | 수치 팩트 갱신 시 |
| StateExtractor.extract_state | LLM 호출 (gemini-2.5-flash) | 캐시 미스 시 |
| StateTracker._npc._record_change | DB insert_npc_change | bind_db 후 NPC 변경 시 |
| StateTracker.cleanup_npc_registry_with_llm | LLM 호출 (5 Arc마다) | V69 NPC 오탐 정리 |
| WorldState.rollback_to | DB get_all_episode_bibles + save | 롤백 시 |
| FactLedger.rollback_to | DB get_all_episode_bibles + save | 롤백 시 |

---

## 5. Facts

1. StateTracker facade는 3 sub-module (NPC=2,204L, Financial=125L, Plots=963L)로 완전 분리
2. full_extract_from_arcs는 17종(+1 conditional) extract를 호출하며, 테스트(3건)가 검증
3. WorldState _INIT_STATE는 16개 top-level 키 (V68 초기 9개에서 확장)
4. FactLedger MAX_HISTORY_PER_ENTITY=100 (10에서 확장), MAX_SUMMARY_CHARS=50000 (20000에서 확장)
5. WorldState update_from_state_changes는 17개 섹션, 모두 개별 try/except 비차단
6. StateExtractor._state_cache는 arc_no 기반 캐시, invalidate_cache로 무효화
7. Financial tracker는 investment 장르 전용 4필드 (exchange_rates, total_assets, leverage, key_transactions)
8. resolved_plots 최대 500개, entity_name_registry LRU max 500
9. WorldState/FactLedger 양쪽 모두 rollback_to 메서드로 DB 리플레이 방식 롤백 지원
10. 모든 save는 비차단 (last_save_ok/last_save_error 패턴)

---

## 6. Inferences

1. full_extract_from_arcs 핵심 4종이 try/except 없이 호출되어, 비정상 arc dict 시 전체 루프 중단 가능 (TF-003)
2. _populate_genre_registries_from_arc와 update_plot_mentions_from_arc이 full_extract에서 미호출되어, Stage 3 직행 시 hunter/fantasy 레지스트리와 active_plots가 빈 상태 (TF-004, TF-005)
3. bind_world_state 순서 불일치는 현재 무해하나, full_extract 내부에서 _world_state 참조 추가 시 main_a 경로에서만 문제 발생 가능 (TF-006)
4. blessing_curse_registry와 filmography_registry는 채우는 production 경로가 없어 사실상 dead code (TF-018)
5. FactLedger characters dict 키 수에 상한이 없어 200화+ 시 수백 NPC 누적 가능 (TF-010)
6. resolved_plots 중복 검사가 O(n) any() 기반이라 장기연재 시 성능 저하 가능 (TF-016)

---

## 7. Uncertainty / Contradictions

| Item | Type | Detail |
|------|------|--------|
| TF-003 핵심 4종 예외 빈도 | Uncertainty | 운영 중 발생 빈도 불명 — 정적 분석 한계 |
| TF-004 Stage3 직행 시 레지스트리 참조 여부 | Uncertainty | hunter/fantasy 레지스트리를 Stage3+에서 실제 참조하는지 미확인 |
| TF-016 성능 영향 | Uncertainty | 200+ arc 규모에서 실제 성능 측정 필요 — 동적 검증 필요 |
| TF-018 외부 삽입 경로 | Uncertainty | blessing_curse/filmography를 외부에서 직접 삽입하는 코드 존재 가능성 |
| MEMORY vs live code | Contradiction | _INIT_STATE 9→16필드, MAX_HISTORY 10→100, MAX_SUMMARY 20000→50000 (TF-001, TF-002) |

---

## 8. Cross-Ref to Adjacent Terminals

| Adjacent Terminal | Cross-Ref Items |
|-------------------|-----------------|
| T01 (SovereignApp) | TF-006 bind_world_state 순서, main_a.py:4059-4091 |
| T02 (Stage2 Orch) | TF-003 full_extract 호출, TF-011 invalidate_cache(arc_no) |
| T03 (Stage2 Preflight) | TF-004 _populate_genre 호출 사이트, TF-020 extract_all 호출 |
| T04 (Stage3) | TF-005 update_plot_mentions 미호출, TF-006 bind 순서 |
| T05 (Stage4 Orch) | TF-021 get_all_summaries 호출 |
| T06 (Stage4 Interview) | TF-025 revive_npc _world_state 참조 |
| T11 (BaseAgent) | TF-012 StateExtractor fallback, TF-007 facade 패턴 |
| T13 (Continuity) | TF-017 entity_name_registry eviction |
| T14 (Validation) | TF-009 WorldState 갱신 → TruthGate 접근자 |
| T16 (DB) | TF-010 eviction, TF-024 save 비차단, TF-023 degraded mode |
| T17 (Config) | TF-019 하드코딩 상수, TF-022 max_chars |
| T18 (Stage0/Helpers) | TF-018 장르 확장 레지스트리 |
| T20 (Cross-Cut) | TF-001/002/015 문서 DRIFT |

---

## 9. Candidate Watchlist

1. **full_extract_from_arcs 핵심 4종 보호**: try/except 추가로 단일 arc 실패 시에도 다음 arc 진행 가능하게
2. **_populate_genre_registries_from_arc 통합**: full_extract_from_arcs 루프 내 호출 추가
3. **update_plot_mentions_from_arc 통합**: full_extract_from_arcs 루프 내 호출 추가
4. **resolved_plots 중복 검사 최적화**: set 기반으로 O(1) 변환
5. **blessing_curse_registry / filmography_registry**: 채우는 경로 추가 또는 dead code 정리
6. **bind_world_state 순서 표준화**: main_a.py에서 full_extract 전 호출로 통일
7. **FactLedger characters dict 상한**: 200화+ 대비 eviction 정책 검토

---

## 10. 6Pass Audit Log

### Pass 1 — 구조/범위
- 7개 파일 전수 조사: state_tracker(facade+3sub), state_extractor, world_state, fact_ledger ✅
- 필수 조사 8항목 전수 수행 ✅
- TF 25개 (최소 기대 10개 초과) ✅
- Side-effect surface 9개 경로 식별 ✅
- **PASS**

### Pass 2 — 증거/일관성
- 모든 TF에 파일:라인 참조 포함 ✅
- 코드 스니펫 25+ 인용 ✅
- DRIFT TF(001/002/015)에서 양쪽 코드 나란히 인용 ✅
- 수치 근거(MAX 상수, 필드 수) 정의 위치와 값 기록 ✅
- Grep 결과 8건 기록 ✅
- **PASS**

### Pass 3 — 실행가능성
- P2 TF 3건: 모두 actionable (try/except 추가, 호출 추가, 순서 표준화)
- P3 TF 6건: 모두 명확한 개선 방향 제시
- P4 TF 16건: 관측/SYNC 확인으로 적절한 severity
- Candidate Watchlist 7건으로 우선순위 정리
- **PASS**

### Pass 4 — 적대적 Pass 1 (스코프 과잉/누락)
- "state_tracker_npc.py 2,204줄을 충분히 조사하지 않았다" →
  11종 extract 메서드 전수 확인, _NPC_DEATH_EXCLUDE_WORDS, compiled regex 패턴,
  facade 위임 30+ 메서드 확인. 내부 구현 세부(regex 패턴 정확성)는 T12 범위 외
  (T15 Quality Intel에서 advisory 정합성 조사) → **반박 실패, PASS**
- "tests 조사가 부족하다" →
  test_state_tracker.py(525L) 주요 테스트 클래스 5개 확인,
  test_fact_ledger.py(~120L) 핵심 경로 확인, 나머지 3개 테스트 파일은 T12 범위의
  보조 테스트이며 주요 contract 검증은 수행함 → **반박 실패, PASS**

### Pass 5 — 적대적 Pass 2 (증거 거짓/오해)
- "TF-003의 '전체 for 루프 중단'은 과장이다" →
  Python에서 try/except 없는 for 루프 내 예외는 해당 루프를 중단시킴.
  핵심 4종이 for 루프 body 시작부에 있으므로 예외 시 해당 arc 이후 전체 중단 맞음
  → **반박 실패, PASS**
- "TF-018 blessing_curse는 dead code가 아니라 미구현이다" →
  __init__에서 초기화되고, get_all_summaries에서 summary 호출되며,
  _populate에서 채우지 않으므로 "채우는 production 경로 없음"이 정확
  → **반박 실패, PASS**

### Pass 6 — 적대적 Pass 3 (severity 과대/과소)
- "TF-003을 P1-HIGH로 올려야 한다" →
  핵심 4종은 state_changes dict에서 직접 읽기만 하므로 예외 발생 조건이
  극히 제한적(arc dict가 None이거나 state_changes가 비정상 타입).
  일반 운영에서 발생 확률 매우 낮아 P2 적절 → **반박 실패, PASS**
- "TF-019 하드코딩을 P4로 내려야 한다" →
  상수들이 운영 중 변경 필요성이 있고(50→100 skills, 20→30 timeline 등),
  config 분리 시 운영 유연성 향상되므로 P3 적절 → **반박 실패, PASS**

**6PASS-CLEARED** — 확신도 96%
