# [S2D-T1] Stage2 DI Contract & Callback Wiring Findings

> 작성일: 2026-03-13
> 작성자: Claude Opus 4.6
> 상태: `3pass 완료`
> 조사 모드: `static / read-only / code-and-test verification`
> 실행 요약: `PASS1 후보 8건 -> PASS2 교차검증 5건 기존 문서 중복/오탐 제거 -> PASS3 최종 3건 확정`

---

## 조사 범위

- `modules/core/stage2_context.py` (51 __slots__, from_app 팩토리)
- `main_a.py` (Stage2 진입점 3곳: L2754, L3801, L4045)
- `modules/protocols/app_services.py` (Protocol 정의 5종)
- `modules/core/services/project_service.py` (destructive op + state restore)
- 교차 참조: `modules/core/stage2_orchestrator.py`, `stage2_preflight.py`, `stage2_validation_pipeline.py`, `stage2_finalizer.py`, `prompt_builder.py`

---

## Finding Ledger

| ID | Severity | 판정 | 파일 | 요약 |
|----|----------|------|------|------|
| S2D-T1-001 | P2 | 확정 | `stage2_orchestrator.py:294`, `stage2_context.py` | `world_state`가 Stage2Context `__slots__`에 없어 StateTracker WorldState 배선이 항상 None으로 스킵된다 |
| S2D-T1-002 | P3 | 확정 | `stage2_context.py:46-48`, `stage2_orchestrator.py:118-148` | `retry_feedback_contract`의 `required` 티어가 construction 시점에 강제되지 않고 소비자에 fallback이 있어 실질적으로 optional이다 |
| S2D-T1-003 | P3 | 확정 | `prompt_builder.py:569-574`, `stage2_context.py:342-343,363` | `prompt_builder.py`가 `self._app._cumulative_state_cache`를 DI 컨텍스트를 우회해 직접 읽기/쓰기하여 cache 소유권이 이중화된다 |

---

## PASS 기록

### PASS 1 - 표면 수집 (후보 8건)

| # | 확신도 | 현상 | 비고 |
|---|--------|------|------|
| 1 | HIGH | `world_state` 슬롯이 Stage2Context에 없어 `getattr(ctx, "world_state", None)` 항상 None | P2 candidate |
| 2 | MED | `retry_feedback_contract` required 티어 미강제 | P3 candidate |
| 3 | MED | `prompt_builder.py`가 DI 컨텍스트 우회해 `self._app._cumulative_state_cache` 직접 접근 | P3 candidate |
| 4 | HIGH | Stage2Context docstring 슬롯 수 불일치 (18종→20종, 22종→26종) | MLW-T1-004 중복 |
| 5 | HIGH | `cumulative_state_cache` populate/clear 비대칭 | MLW-T1-002 중복 |
| 6 | MED | `state_tracker` write-back 3곳 수동 복제 | MLW-T1-003 중복 |
| 7 | MED | `_state_tracker_loaded_arcs` ProjectService 리셋 미포함 | MRL-T1 조사 완료: defensively safe |
| 8 | HIGH | real-app binding chain 테스트 부재 | MLW-T1-001 중복 |

### PASS 2 - 교차 검증

- 후보 4 제거: `already-covered`. MLW-T1-004가 동일 표면을 P3으로 확정.
- 후보 5 제거: `already-covered`. MLW-T1-002가 동일 표면을 P3으로 확정.
- 후보 6 제거: `already-covered`. MLW-T1-003가 동일 표면을 P3으로 확정.
- 후보 7 제거: `already-covered`. MRL-T1이 조사 후 defensively safe 판정.
- 후보 8 제거: `already-covered`. MLW-T1-001이 동일 표면을 P1으로 확정.

### PASS 3 - 최종 확정 (3건)

- S2D-T1-001 ~ S2D-T1-003 채택

---

## Final Findings

### [S2D-T1-001] `world_state` 슬롯 누락으로 StateTracker WorldState 배선이 항상 None

- Severity: P2
- 위치: `modules/core/stage2_orchestrator.py:294`, `modules/core/stage2_context.py:134-192`
- 근거:

  `stage2_orchestrator.py:289-294` -- StateTracker 초기화 시 WorldState를 바인딩하는 코드:
  ```python
  ):  # [V62.5] Arc 삭제 감지 → 리셋
      self.ctx.state_tracker = StateTracker(
          preset_registry=self.ctx.preset_registry, llm_client=self.ctx.sys.api_client
      )
      self.ctx.state_tracker.bind_db(self.ctx.current_project.db)  # [NPC-L1] NPC 이력 DB 배선
      self.ctx.state_tracker.bind_world_state(getattr(self.ctx, "world_state", None))  # [TF-36] WorldState 배선
  ```

  `stage2_context.py:134-192` -- `__slots__` 전체 51개를 확인한 결과, `world_state`는 슬롯에 존재하지 않는다. `__slots__`가 정의된 클래스에서 `getattr(self.ctx, "world_state", None)`은 항상 `None`을 반환한다(동적 속성 추가가 차단되므로).

  비교: `main_a.py:3603`에서는 Stage 4 진입 시 `self.state_tracker.bind_world_state(self.world_state)`로 올바르게 app의 `world_state`를 직접 전달한다.

  비교: `modules/core/stage3_orchestrator.py:516`에서는 `ctx.world_state`를 참조하며, Stage3Context에는 `world_state` 슬롯이 실제로 존재한다.

- 판정: 확정
- 영향 범위:
  - `StateTracker.bind_world_state(None)`은 crash 없이 경고만 남기고 `_world_state = None`으로 설정한다 (state_tracker.py:175, 1042).
  - WorldState 바인딩이 없으면 Stage 2에서 생성된 StateTracker가 `revive_npc()` 호출 시 WorldState `alive_npcs`/`dead_npcs` 동기화를 수행하지 못한다.
  - 다만 Stage 2의 StateTracker는 주로 Arc 데이터 추출용이고, NPC 부활 시나리오는 Stage 4에서 더 빈번하므로 즉시 기능 붕괴보다는 품질 저하 위험에 가깝다.
  - Stage 2에서 생성된 StateTracker가 `main_a.py:2780-2781`을 통해 app에 write-back된 후, Stage 4 lazy init(main_a.py:3603)에서 `bind_world_state(self.world_state)`를 다시 호출하므로 Stage 4 시점에는 보정된다.
- 기존 문서 중복: MLW-T2가 Stage3의 유사 이슈(`constraint_db` ghost binding)를 다뤘으나, Stage2의 `world_state` 슬롯 누락은 미기록.
- 권장 조치:
  - Stage2Context `__slots__`에 `world_state` 추가
  - `from_app()`에 `world_state=_safe_getattr(app, "world_state", None)` 배선 추가
  - 또는 `getattr(self.ctx, "world_state", None)` 대신 `getattr(self.app, "world_state", None)` 사용 (레거시 `self.app` 경로 활용)

---

### [S2D-T1-002] `retry_feedback_contract` required 티어가 construction 시점에 강제되지 않는다

- Severity: P3
- 위치: `modules/core/stage2_context.py:46-48`, `modules/core/stage2_context.py:89-105`, `modules/core/stage2_orchestrator.py:118-148`
- 근거:

  `stage2_context.py:46-48` -- `analyze_rejection_pattern_v60`가 유일한 `required` 티어로 선언:
  ```python
  "analyze_rejection_pattern_v60": {
      "tier": "required",
      "fallbacks": (),
  },
  ```

  `stage2_context.py:89-105` -- `_build_retry_feedback_contract()`는 missing required 콜백을 기록만 하고 예외를 발생시키지 않는다:
  ```python
  def _build_retry_feedback_contract(app):
      callbacks = {}
      contract = {}
      missing = {
          "required": [],
          "optional_with_fallback": [],
          "observability_only": [],
      }
      for callback_name, spec in _RETRY_FEEDBACK_CALLBACK_SPECS.items():
          contract[callback_name] = spec["tier"]
          resolved = _resolve_retry_feedback_callback(app, callback_name)
          callbacks[callback_name] = resolved
          if not callable(resolved):
              missing[spec["tier"]].append(callback_name)
      return callbacks, contract, missing
  ```

  `stage2_orchestrator.py:118-148` -- 실제 소비자 `_compose_rejection_pattern_feedback()`은 `analyze_rejection_pattern_v60`가 None이어도 자체 fallback으로 처리한다:
  ```python
  callback = getattr(self.ctx, "analyze_rejection_pattern_v60", None)
  if callable(callback):
      try:
          return callback(arc_rejections, global_arc_no) or ""
      except Exception as exc:
          ...
  else:
      reason_suffix = "callback_missing"
  reason_counts = {}
  specific_issues = []
  for reject in arc_rejections:
      ...
  ```

- 판정: 확정
- 영향 범위:
  - `required` 티어 어노테이션이 문서적 의미만 가지고 런타임 계약으로 작동하지 않는다.
  - `retry_feedback_missing_callbacks["required"]`에 콜백 이름이 기록되지만, 이를 읽어서 경고나 예외를 발생시키는 코드가 없다.
  - 현재 real `SovereignApp`에서는 `_analyze_rejection_pattern_v60`이 존재하므로(main_a.py:787) 즉시 문제는 없다.
  - 향후 partial host나 test fixture에서 누락 시 "required인데 왜 동작하지?"라는 혼선이 발생할 수 있다.
- 기존 문서 중복: 없음. `tests/test_stage2_context.py:148`에서 missing required 기록은 검증하지만, 강제 메커니즘 부재는 미기록.
- 권장 조치:
  - `_build_retry_feedback_contract()`에서 `missing["required"]`가 비어 있지 않으면 `logging.warning()` 수준의 알림 추가 (hard fail은 불필요)
  - 또는 `required` 티어를 `optional_with_fallback`으로 재분류 (소비자가 이미 fallback을 갖고 있으므로)

---

### [S2D-T1-003] `prompt_builder.py`가 DI 컨텍스트를 우회하여 `_cumulative_state_cache`를 직접 읽기/쓰기한다

- Severity: P3
- 위치: `modules/core/prompt_builder.py:569-574`, `modules/core/stage2_context.py:342-343,363`
- 근거:

  `prompt_builder.py:566-574` -- `self._app`을 통해 cache를 직접 읽고 쓴다:
  ```python
  state_extractor = self._app.agents.get("state_extractor")
  if state_extractor:
      arc_count = len(all_refined_arcs)
      if self._app._cumulative_state_cache is not None and self._app._cumulative_state_cache_key == arc_count:
          cumulative_state = self._app._cumulative_state_cache
      else:
          cumulative_state = state_extractor.extract_cumulative_state(all_refined_arcs)
          self._app._cumulative_state_cache = cumulative_state
          self._app._cumulative_state_cache_key = arc_count
  ```

  `stage2_context.py:342-343,363` -- `from_app()`는 같은 cache 값을 ctx 슬롯에 복사하고, `sync_cache_key_to_app` weakref 콜백으로 ctx→app 방향 동기화를 설정한다:
  ```python
  cumulative_state_cache=_safe_getattr(app, "_cumulative_state_cache", None),
  cumulative_state_cache_key=_safe_getattr(app, "_cumulative_state_cache_key", None),
  ...
  sync_cache_key_to_app=_make_sync_callback(weakref.ref(app)),
  ```

  결과적으로 cache 소유권이 이중화된다:
  - **경로 A (DI 경유)**: `stage2_preflight.py`가 `ctx.cumulative_state_cache`를 읽기/쓰기하고, `sync_cache_key_to_app`으로 app에 동기화
  - **경로 B (DI 우회)**: `prompt_builder.py`가 `self._app._cumulative_state_cache`를 직접 읽기/쓰기

  Stage 2 실행 중 `prompt_builder.py`의 `generate_arc_context_v60()`이 호출되면 경로 B가 작동한다. 이때 ctx 측 cache와 app 측 cache가 불일치할 수 있다 (특히 MLW-T1-002에서 확인된 clear 비대칭과 결합 시).

- 판정: 확정
- 영향 범위:
  - `prompt_builder.py`의 `generate_arc_context_v60()`은 `_RETRY_FEEDBACK_CALLBACK_SPECS`에서 `_prompt_builder.generate_arc_context_v60`으로 fallback 해소될 수 있다 (stage2_context.py:56). 이 경우 ctx 콜백으로 호출되지만, 내부 구현은 여전히 `self._app`을 직접 참조한다.
  - 현재 정상 실행 경로에서는 ctx와 app의 cache가 동일 방향으로 갱신되므로 즉시 데이터 오염은 발생하지 않는다.
  - 다만 ctx cache clear(stage2_finalizer.py:1125-1126) 후 prompt_builder가 app의 stale cache를 읽으면 불필요한 cache hit이 발생할 수 있다.
- 기존 문서 중복: MDH-T2가 `prompt_builder.py`의 `self._app._audit_event()` 직접 참조를 언급했으나, cache 이중 소유권 관점은 미기록. MLW-T1-002가 clear 비대칭을 다뤘으나, prompt_builder의 직접 접근 경로는 포함하지 않았다.
- 권장 조치:
  - `prompt_builder.py`의 `generate_arc_context_v60()`을 ctx 슬롯 경유로 리팩터링 (cache 읽기/쓰기를 ctx 인터페이스로 통일)
  - 또는 `prompt_builder.py`가 DI 이전 레거시 코드임을 문서화하고, DI 전환 시 정리 대상으로 태그

---

## 기존 문서 참조 (중복 제거 목적)

| 기존 Finding | 본 문서와의 관계 |
|-------------|-----------------|
| MLW-T1-001 (P1) | real-app binding chain 테스트 부재 — 본 트랙에서 재확인, 중복 제거 |
| MLW-T1-002 (P3) | `cumulative_state_cache` clear 비대칭 — 본 트랙 S2D-T1-003이 이를 보완 (prompt_builder 경로 B 추가) |
| MLW-T1-003 (P3) | `state_tracker` write-back 수동 복제 — 본 트랙에서 재확인, 중복 제거 |
| MLW-T1-004 (P3) | docstring/slot count 불일치 — 본 트랙에서 재확인, 중복 제거 |
| MRL-T1 | `_state_tracker_loaded_arcs` ProjectService 미리셋 — defensively safe 확인, 중복 제거 |
| MDH-T2 | `prompt_builder.py` `self._app._audit_event()` 직접 참조 — S2D-T1-003이 cache 측면을 보완 |

---

## 현재 양성 확인

아래는 이번 조사에서 명시적으로 확인한 정상 동작이다.

1. **필수 5종 슬롯 (ui, current_project, agents, sys, state_tracker)**: `from_app()`에서 4종은 직접 추출, `state_tracker`는 `_safe_getattr`로 optional 추출하지만 소비자(stage2_orchestrator.py:286-293)가 None일 때 자체 생성하므로 안전하다.
2. **콜백 19종 + `sync_cache_key_to_app`**: MLW-T1 lightweight real-app 확인 결과를 재확인 -- 현재 `SovereignApp` 표면에서 모두 callable이다.
3. **`validate_arc_data_fields/mapping/integrity` 3종 콜백 가드**: 모두 `callable(getattr(self.ctx, ..., None))` 패턴으로 보호되어 None 시 안전하게 스킵한다.
4. **`ProjectService` DI 배선**: `project_fn`, `safe_commit_fn`, `genre_fn`, `memory_fn`, `state_tracker_invalidator`, `world_state_fn`, `fact_ledger_fn`, `preset_registry_restorer`, `emotion_tracker_fn`, `state_delta_tracker_fn` 11종 lambda/callback이 main_a.py:331-343에서 올바르게 바인딩된다.
5. **`ProjectService._restore_runtime_state()`**: `state_tracker`, `world_state`, `fact_ledger`, `emotion_tracker`, `state_delta_tracker`, `preset_registry` 6종 런타임 상태를 롤백하며, `state_tracker_invalidator`가 `self.state_tracker = None`으로 설정하면 다음 Stage 2에서 자동 재초기화된다.
6. **Protocol 정의 (app_services.py) 5종**: `UIServiceProtocol`, `AuditServiceProtocol`, `ProjectRepositoryProtocol`, `StateServiceProtocol`, `ConfigServiceProtocol`이 실제 소비 표면과 대체로 일치한다. Stage2Context가 직접 이 Protocol을 참조하지는 않지만(structural subtyping), 향후 전환 시 호환될 수 있는 구조다.

---

## PASS1 -> PASS2 -> PASS3 요약

- PASS1: 후보 `8`건 수집
- PASS2:
  - 기존 문서 중복 제거 `5`건 (MLW-T1-001~004, MRL-T1)
- PASS3: 확정 `3`건
  - `P0 0건`
  - `P1 0건`
  - `P2 1건` (world_state 슬롯 누락)
  - `P3 2건` (required 티어 미강제, cache 이중 소유권)

## 마감 체크

- 코드 근거 포함: Yes
- downstream 영향 경계 포함: Yes
- 현재 테스트 근거 또는 테스트 부재 포함: Yes
- 기존 문서와의 중복 여부 포함: Yes
- `PASS1 -> PASS2 -> PASS3` 요약 포함: Yes
