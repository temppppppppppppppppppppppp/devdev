# Stage 2 2차 전수 감사 리포트 (2026-02-22)

> 감사 범위: Stage 2 (Arc/Blueprint 설계) 전체 파이프라인 -- 1차 수정 후 재검증 + 미발견 이슈 발굴
> 감사자: Claude Opus 4.6
> 대상 파일: stage2_orchestrator.py, stage2_validation_pipeline.py, stage2_finalizer.py, stage2_preflight.py, stage2_optimizer.py, stage2_context.py, analyst.py, unified_arc_validator.py, constraint_db.py

---

## 요약

- **P0 (차단급 버그)**: 0건
- **P1 (품질 이슈 -- 수정 권장)**: 3건 (신규)
- **P2 (스타일/경미)**: 5건 (신규)
- **1차 수정 검증**: 6건 중 6건 통과
- **개선 아이디어**: 6건 (신규)

---

## 1. 1차 수정 검증

### S2-P1-4 (DraftValidator 플래그) -- PASS

- **파일**: `modules/core/stage2_validation_pipeline.py:83`
- **1차 지적**: `draft_validator_passed = True`가 1차 호출(advisory 수집 전용)에서 설정되어 2차 호출의 REJECT 판정과 충돌 가능.
- **검증 결과**: L83에 `# [S2-P1-4] draft_validator_passed는 2차 호출(L256)에서만 설정 / 1차 호출은 Consensus용 advisory 수집 전용` 주석이 추가되었고, 1차 호출(L65-86) 블록에서 `draft_validator_passed = True` 할당이 제거되어 있음을 확인. 2차 호출(L257+)의 결과에서만 `draft_validator_passed`가 결정되므로 API 할당량 폴백 판단(finalizer L158)과의 정합성이 보장됨.

### S2-P1-5 (ThreadPool Lock) -- PASS

- **파일**: `modules/core/stage2_preflight.py:194`
- **1차 지적**: `_compute_arc_drive()`와 `_compute_preflight()`가 ThreadPoolExecutor에서 `self.ctx.perf_timer`를 직접 접근하여 스레드 안전성 미보장.
- **검증 결과**: L194에 `_perf_lock = threading.Lock()`이 도입되었고, `_compute_arc_drive()`(L199, L219)와 `_compute_preflight()`(L227, L249) 내부의 `perf_timer.start/stop` 호출이 모두 `with _perf_lock:` 블록으로 보호됨을 확인. Lock이 함수 로컬 스코프에서 생성되어 Arc 단위로 독립적이며, `_compute_constraint_block()`은 perf_timer를 사용하지 않으므로 Lock 불필요.

### S2-P2-1 (flow_guard 타입) -- PASS

- **파일**: `modules/core/stage2_validation_pipeline.py:700`
- **1차 지적**: `_stage2_flow_guard_legacy`의 `normalized` 매개변수가 `str` 타입으로 호출될 가능성.
- **검증 결과**: L700-703에 `isinstance(normalized, str)` -> `[normalized]` 변환, `isinstance(normalized, list)` 아닐 시 `list(normalized)` 변환 로직이 추가됨을 확인. `str`을 포함한 모든 iterable 타입에 대해 안전하게 처리.

### S2-P2-5 (max_attempts _threshold) -- PASS

- **파일**: `modules/core/stage2_preflight.py:348`
- **1차 지적**: `max_attempts = 5` 하드코딩.
- **검증 결과**: L348에서 `max_attempts = int(_threshold("retry.analyst_max_attempts", 5))`로 외부화 완료. `_threshold()`의 반환값을 `int()`로 감싸서 타입 안전성도 확보.

### S2-I1 (병렬화) -- PASS

- **파일**: `modules/core/stage2_preflight.py:255-279`
- **1차 제안**: `constraint_db` 수집을 arc_drive/preflight와 병렬 실행.
- **검증 결과**: L255-261에 `_compute_constraint_block()` 함수가 추가되었고, L273-279에서 `ThreadPoolExecutor(max_workers=3)`으로 arc_drive, preflight, constraint_block 세 작업이 병렬 실행됨을 확인. `_fut_constraint`에 별도 timeout(60초)이 설정되어 메인 LLM 호출(300초)과 구분됨.

### S2-I8 (크기 로깅) -- PASS

- **파일**: `modules/core/stage2_preflight.py:523-530`
- **1차 제안**: `enhanced_context` 크기 로깅 + Gemini context window 초과 경고.
- **검증 결과**: L523-530에 `_ec_size = len(enhanced_context)` 로깅과 `_CONTEXT_WARNING_THRESHOLD = 100_000` 초과 시 경고 로그가 추가됨을 확인. `constraint_block` 크기도 별도로 로깅됨.

---

## 2. 신규 P1 이슈 (수정 권장)

### P1-NEW-1: `n_results` 타입 불일치 -- `_threshold()` 반환값이 float일 수 있음

- **파일**: `modules/core/stage2_preflight.py:684`
- **코드**:
  ```python
  _s2_vector_ctx = self.ctx.memory.retrieve_high_res_context(
      enriched_block.get("block_theme", ""),
      current_ep_start,
      n_results=_threshold("context.vector_max_results_s2", 8),  # L684
  )
  ```
- **문제**: `_threshold()`는 `Any` 타입을 반환한다. YAML 설정에서 `8.0` (float)이 지정되면 `n_results`에 float이 전달된다. `vec_memory.py:411`의 `retrieve_high_res_context()`는 `n_results: int = 3` 시그니처이지만, 내부에서 SQL `LIMIT` 절에 직접 사용할 경우 SQLite가 float를 거부할 수 있다.
- **비교**: 같은 파일 L111에서는 `int(_threshold("context.vector_max_results_s2", 8))`로 올바르게 `int()` 래핑을 하고 있어 패턴이 일관되지 않음.
- **위험도**: YAML에서 정수로 설정하면 문제없으나, `8.0`이나 `"8"` 등의 값이 들어오면 SQLite 레벨에서 에러 가능. `try/except` 내부이므로 크래시는 아니나 벡터 검색이 무음 실패하여 컨텍스트 누락.
- **수정안**: `n_results=int(_threshold("context.vector_max_results_s2", 8))`로 래핑.

### P1-NEW-2: Orchestrator 실패 핸들러의 `user_choice`/`manual_input` 변수 스코프 누출

- **파일**: `modules/core/stage2_orchestrator.py:670-746`
- **코드**:
  ```python
  while True:  # L670 -- 실패 옵션 루프
      ...
      user_choice = (await asyncio.to_thread(input, ...)).strip()  # L676
      ...
      if user_choice == "4":
          ...
          manual_input = (await asyncio.to_thread(input, ...)).strip()  # L704-713
          ...
          break
      else:
          ...
          return  # L741

  if user_choice == "3":  # L743
      continue
  if user_choice == "4" and manual_input not in ("skip",):  # L745
      continue
  ```
- **문제**: L743-746에서 `user_choice`와 `manual_input`을 참조하는데, 이 변수들은 내부 `while True` 루프에서만 할당된다. Python에서 로컬 스코프 규칙상 `while`/`if` 블록이 새 스코프를 만들지 않으므로 기술적으로는 문제없다. 그러나 `user_choice`가 "2"(기본값, L678)이거나 다른 값으로 `else` 분기를 타고 `return`하면 L743에 도달하지 않는다. 문제는 `user_choice == "4"`이면서 `manual_input`이 빈 문자열("")인 경우인데, 이때 `manual_input`이 "skip"도 "quit"도 아니므로 L732-736의 `else` 분기를 타고 `break`되며, L745에서 `manual_input not in ("skip",)`이 True가 되어 `continue` -- 즉, 동일 Arc를 재시도한다. 이 경로 자체는 의도된 동작이지만, `manual_input` 변수가 `user_choice != "4"`인 경우 미정의(unbound) 상태로 L745에 도달할 수 있는지가 관건이다.
- **분석**: `user_choice`가 "4"인 경우에만 `manual_input`이 할당되고, L745의 조건에도 `user_choice == "4"`가 필수이므로 `NameError`는 발생하지 않는다. **그러나** 만약 `user_choice == "1"`에서 `break`하면 L743을 통과하고 L745의 `user_choice == "4"` 조건이 False이므로 `manual_input`이 평가되지 않아 안전하다.
- **위험도**: 현재 코드에서 실제 `NameError`가 발생하는 경로는 없다. 그러나 이 분기 로직이 매우 복잡하여 향후 수정 시 실수할 가능성이 높다.
- **수정안**: L670 이전에 `user_choice = "2"` / `manual_input = ""` 기본값을 선언하여 방어적으로 초기화.

### P1-NEW-3: Finalizer `_rejected_arc` 미초기화 -- PASS 경로에서 참조 불가능

- **파일**: `modules/core/stage2_finalizer.py:475, 526-534`
- **코드**:
  ```python
  if audit.get("decision") == "PASS":  # L190
      ...
      return {"action": "break", ...}  # L465-472
  else:
      _rejected_arc = refined_arc  # L475 -- REJECT 경로에서만 할당
      ...
      return {
          ...
          "rejected_arc": _rejected_arc,  # L534
          ...
      }
  ```
- **문제**: `_rejected_arc`는 `else` 블록(REJECT 경로) 내부에서만 할당된다. PASS 경로에서는 `return` 전에 `_rejected_arc`가 정의되지 않으므로, 만약 PASS 반환값에 `rejected_arc` 키가 추가되는 리팩토링이 발생하면 `NameError`가 발생한다. 현재는 PASS 경로의 반환 dict에 `rejected_arc`가 없으므로 문제없다.
- **위험도**: 현재 문제 없음. 단, REJECT 반환 dict가 L526에서 `else` 블록 바깥에 위치한 것처럼 보이지만 실제로는 `else` 블록의 일부(들여쓰기 확인)이므로 안전.
- **수정안**: 함수 시작부에 `_rejected_arc = None` 초기화를 추가하면 방어적. 또는 현행 유지해도 무방.

---

## 3. 신규 P2 이슈 (스타일/경미)

### P2-NEW-1: `RetryLimits.ANALYST_MAX_ATTEMPTS` vs `_threshold()` 이원화

- **파일**: `modules/core/stage2_preflight.py:391` vs `modules/core/stage2_preflight.py:348`
- **증상**: L391에서 UI 표시용으로 `RetryLimits.ANALYST_MAX_ATTEMPTS` (상수값 5)를 사용하고, L348에서 실제 루프 상한으로 `int(_threshold("retry.analyst_max_attempts", 5))`를 사용한다. YAML 설정에서 값을 변경하면 실제 동작은 바뀌지만 UI 표시는 항상 "시도 N/5"로 고정되어 불일치가 발생한다.
- **수정안**: L391에서도 `max_attempts`를 전달받아 표시하거나, `RetryLimits.ANALYST_MAX_ATTEMPTS` 대신 `_threshold()` 결과를 사용.

### P2-NEW-2: `constraint_db.generate_constraint_block()` 반환값 `""` vs `None` 혼용

- **파일**: `modules/core/constraint_db.py:407-408` vs `modules/core/stage2_preflight.py:258-261`
- **증상**: `generate_constraint_block()`은 `for_arc <= 1`이거나 `arc_states`가 비어 있으면 `""` (빈 문자열)을 반환한다(L408). Preflight의 `_compute_constraint_block()`은 예외 시 `""` 반환(L261). 그러나 Orchestrator L601에서는 `constraint_db.generate_constraint_block(global_arc_no) if constraint_db else "N/A"` 패턴을 사용하며, `"N/A"` 문자열이 실제 constraint 텍스트에 포함될 수 있다.
- **위험도**: 미미. 실패 리포트 출력용이므로 기능 영향 없음.
- **수정안**: 일관되게 `""` 반환으로 통일.

### P2-NEW-3: `ConstraintDB._parse_arc_state` -- `dict` 아이템 비교 시 `in` 연산 오류 가능

- **파일**: `modules/core/constraint_db.py:131-136`
- **코드**:
  ```python
  for item in phys_inv:
      if item and item not in inventory:  # L132-133
          inventory.append(item)
  ```
- **증상**: `phys_inv`가 dict 원소를 포함하는 리스트일 경우(`[{"name": "검", "grade": "S"}]`), `item not in inventory` 비교에서 dict 동등성 비교가 발생한다. dict는 내용 비교이므로 기능적으로는 맞지만, 동일한 아이템이 다른 키를 추가로 포함하면 중복 감지 실패. 반면 `_filter_distributed_items`(L279)에 전달되는 `inventory`에 dict 원소가 포함되면 `_is_distributed_item`(L223)에서 `str(item)` 변환이 발생하여 정규 표현식 매칭 품질이 저하된다.
- **위험도**: LLM이 `physical_inventory`에 dict를 반환하는 경우가 드물지만, Sweep45에서 다른 곳에 dict 방어를 추가한 것으로 보아 발생 가능성 존재.
- **수정안**: `_parse_arc_state` 입구에서 `phys_inv` 원소를 문자열로 정규화 (`item.get("name", str(item)) if isinstance(item, dict) else str(item)`).

### P2-NEW-4: `stage2_optimizer.py` -- `SessionFailureMemory.record_failure` 시그니처 혼동

- **파일**: `modules/core/stage2_optimizer.py:642-669`
- **증상**: `record_failure()` 메서드가 `failure_type`(신규)과 `category`(deprecated) 두 가지 이름으로 같은 역할의 매개변수를 받는다. 외부 호출부(`stage2_validation_pipeline.py:455`, `stage2_finalizer.py:687`)에서는 `failure_type=` 키워드로 호출하고, `Stage2Optimizer.record_result()`(L862)에서는 `category=`로 호출한다.
- **위험도**: 현재 `actual_category = failure_type if failure_type else category` 로직으로 양쪽 다 작동하지만, 두 인터페이스가 공존하여 혼란 유발.
- **수정안**: `category` 매개변수를 deprecated 경고와 함께 제거하거나, 내부적으로 `failure_type` 하나로 통일.

### P2-NEW-5: `_auto_correct_joint_docs_v60` -- `state_constraints.joint_docs` 이중 구조

- **파일**: `modules/domain/agents/analyst.py:501-523`
- **증상**: `_auto_correct_joint_docs_v60()`이 `arc_data["state_constraints"]["joint_docs"]`에 위치 정보를 기록한 후, L521에서 `arc_data["joint_docs"] = arc_data["state_constraints"]["joint_docs"]`로 상위 레벨에 동기화한다. 이것은 Sweep11에서 추가된 패치인데, Finalizer(`stage2_finalizer.py:204-205`)에서는 `refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})`로 `enriched_block`에서 가져온 값으로 덮어쓴다. 따라서 Analyst의 자동 보정 결과가 Finalizer에서 무효화될 수 있다.
- **위험도**: Analyst의 `plan_single_arc_v20`은 FourPhase 실패 시 fallback으로만 호출되므로 영향 범위가 제한적. FourPhase 경로에서는 Preflight의 `_preflight_enrichment`(L809-810)에서 `enriched_block`의 `joint_docs`를 사용.
- **수정안**: `joint_docs`의 SSOT를 하나로 정하고 동기화 방향을 명확히 문서화. 현재는 "Finalizer가 마지막에 결정"이 사실상 규칙이므로, Analyst 측 자동 보정은 FourPhase 폴백 경로에서만 의미 있음을 주석으로 명시.

---

## 4. 연결성 검증 (Stage 2 -> Stage 3)

### 4-1: Arc 데이터 완전성

Stage 3(`stage3_orchestrator.py`)는 `self.ctx.current_project.arcs`에서 Arc 리스트를 로드하여 Blueprint를 생성한다. Stage 2 Finalizer의 PASS 경로(L308)에서 `validate_arc(refined_arc)` (Pydantic ingress+egress)를 거쳐 `all_refined_arcs.append()`하고 DB에 저장하므로, Arc 데이터의 필수 필드가 Pydantic 스키마에 의해 보장된다.

**검증 항목**:
1. `arc_no`, `ep_start`, `ep_end`, `ep_count` -- Pydantic `validate_arc()`에서 보장. **PASS**
2. `tactical_doc` -- Finalizer L188-189에서 길이 체크, Quality Gate(L191-200)에서 1500자 이상이면 점수 검증. **PASS**
3. `joint_docs` -- Finalizer L218-226에서 누락 시 기본값 주입. **PASS**
4. `status_shadow` -- Finalizer L278-286에서 누락 시 기본값 주입. **PASS**
5. `state_constraints` -- Finalizer L207에서 `validate_arc()` Pydantic 검증. **PASS**
6. `state_changes` -- Analyst `_post_process_arc()` L991-1011에서 13개 하위 키 기본값 보장. 단, FourPhase 경로에서는 이 후처리가 없으므로, FourPhase가 `state_changes`를 생략하면 Stage 3에서 KeyError 가능. **주의 사항** (아래 4-3 참조)

### 4-2: StateTracker 동기화

Stage 2 완료 후 StateTracker가 app 수준에서 보존되어 Stage 3에서 재사용된다. `stage3_orchestrator.py:76`의 `_init_state_tracker_if_needed()`에서 존재하지 않을 경우 새로 초기화한다. Stage 2에서 StateTracker에 기록된 NPC 사망, 무공 습득, 관계 변화 등이 Stage 3에서도 유효하게 참조된다. **PASS**

### 4-3: FourPhase 경로의 `state_changes` 누락 가능성

- **경로**: Stage 2 Preflight `_preflight_enrichment()`에서 FourPhase PASS 시(L771-982), `refined_arc`에 대해 `state_tracker.extract_*` 시리즈를 호출하여 StateTracker를 업데이트한다. 그러나 `refined_arc` 자체에 `state_changes` dict가 없으면 `extract_npc_deaths_from_arc()`등이 내부적으로 `arc.get("state_changes", {})`로 빈 dict를 사용하여 정상 작동한다.
- **Stage 3 영향**: Stage 3의 Blueprint Ensemble이 Arc의 `state_changes`를 참조하는 경우, 이 키가 없으면 `.get()` 폴백으로 빈 dict가 반환되어 기능적으로는 안전하다. 그러나 NPC 사망 정보 등이 Blueprint에 반영되지 않을 수 있다.
- **위험도**: FourPhase 내부에서 `state_changes`를 생성하는지 여부에 따라 달라짐. FourPhase의 프롬프트가 `state_changes` 생성을 요구하므로 대부분의 경우 포함되지만 보장은 없음.
- **수정안**: Finalizer PASS 경로에서 `state_changes` 기본값 보장 로직을 추가하거나, `validate_arc()` Pydantic 모델에서 `state_changes` 필드를 필수로 지정. (현재 Analyst의 `_post_process_arc`에만 존재하는 로직)

### 4-4: ConstraintDB -> Stage 3 전달

ConstraintDB는 Stage 2 내부에서만 사용되며 Stage 3에 직접 전달되지 않는다. Stage 3는 자체적으로 Arc 데이터의 `state_constraints`와 `joint_docs`를 읽어 제약 조건을 파악한다. 이 설계는 올바르며, Stage 간 결합도를 낮춘다. **PASS**

---

## 5. 1차 미발견 이슈 -- 심층 분석

### 5-1: `_collect_all_items` 순서 불안정 (set 기반 반환)

- **파일**: `modules/core/stage2_optimizer.py:66-84`
- **코드**:
  ```python
  def _collect_all_items(self, arc: dict) -> list[str]:
      ...
      return list({_ikey(i) for i in items if i})  # L84 -- set -> list 변환
  ```
- **증상**: `set` comprehension으로 중복을 제거한 후 `list()`로 변환하므로, 반환 순서가 Python 실행마다 다를 수 있다(Python 3.7+ set은 삽입 순서 미보장). `StateSnapshotInjector.generate_injection_prompt()`에서 이 리스트를 `", ".join(all_items)`로 LLM 프롬프트에 주입하므로, 동일한 Arc 데이터에 대해 다른 프롬프트가 생성되어 LLM 캐시 히트율이 감소한다.
- **위험도**: 기능적 문제 없음. 캐시 효율성에만 미미한 영향.
- **수정안**: `sorted(set(...))` 또는 `dict.fromkeys(...)` 패턴으로 정렬된 순서 보장.

### 5-2: `Analyst.enrich_raw_block_async` -- `run_in_executor`에서 self 캡처

- **파일**: `modules/domain/agents/analyst.py:1157-1159`
- **코드**:
  ```python
  loop = asyncio.get_running_loop()
  raw_res = await loop.run_in_executor(None, lambda: self.ask(prompt, temperature=0.3))
  ```
- **증상**: `lambda: self.ask(...)` 클로저가 `self`를 캡처한다. `run_in_executor`는 기본적으로 `ThreadPoolExecutor`를 사용하므로, 동일 Analyst 인스턴스에 대해 병렬로 `enrich_raw_block_async`가 호출되면 `self.ask()` 내부 상태(cache_name, token counters 등)가 경합한다. Stage 2 Orchestrator의 L249에서 `asyncio.gather(*enrichment_tasks, return_exceptions=True)`로 병렬 실행하므로 이 경합이 실제로 발생한다.
- **분석**: `BaseAgent.ask()`가 내부적으로 `self.client.models.generate_content()`를 호출하며, Gemini 클라이언트는 thread-safe하다고 문서화되어 있다. `self.cache_name`은 읽기 전용이고, token counter 업데이트는 `MetricsCollector`의 thread-safe 메서드를 통해 이루어진다. 따라서 **현재 구현에서 실질적 경합 문제는 없다**.
- **위험도**: 현재 안전. 향후 `BaseAgent`에 stateful 필드가 추가되면 재검토 필요.

### 5-3: `UnifiedArcValidator._check_duplicate_items` -- dict 아이템의 부분 매칭 누락

- **파일**: `modules/domain/agents/unified_arc_validator.py:364-378`
- **코드**:
  ```python
  for item in current_acquired:
      item_str = item.strip() if isinstance(item, str) else str(item)  # L367
      if item_str in prev_items:  # L368
  ```
- **증상**: LLM이 `items_acquired`에 dict를 반환하면(`{"name": "백근대도", "grade": "S"}`), `str(item)`은 `"{'name': '백근대도', 'grade': 'S'}"`이 되어 `prev_items`의 문자열 `"백근대도"`와 매칭되지 않는다. `ArcAutoCorrector._remove_duplicate_items()`(L232-234)에서는 dict를 정규화하지만 `UnifiedArcValidator`에서는 하지 않는다.
- **위험도**: 중간. dict 아이템이 중복 감지를 우회하여 LLM에서 PASS될 수 있다. 다만 `ArcAutoCorrector`가 사전에 정규화하므로, AutoCorrector를 거친 Arc에서는 문제없다. FourPhase가 직접 반환하는 Arc가 AutoCorrector를 거치지 않는 경우가 위험.
- **수정안**: L367에서 `item_str = item.get("name", item.get("item", "")) if isinstance(item, dict) else item.strip() if isinstance(item, str) else str(item)` 패턴 적용.

### 5-4: Finalizer 볼륨 요약의 Arc 범위 계산 오류

- **파일**: `modules/core/stage2_finalizer.py:388-392`
- **코드**:
  ```python
  if global_arc_no > 0 and global_arc_no % 10 == 0:  # L388
      _vol_no = global_arc_no // 10  # L390
      for _ai in range(global_arc_no - 9, global_arc_no + 1):  # L392
  ```
- **증상**: Arc 번호가 10, 20, 30... 일 때 볼륨 요약을 생성한다. `_vol_no = global_arc_no // 10`이므로 Arc 10 -> Vol 1, Arc 20 -> Vol 2 등이다. 그러나 `range(global_arc_no - 9, global_arc_no + 1)`은 Arc 1~10, 11~20 등을 탐색한다. 이 논리는 "10 Arc = 1 Volume" 가정이 성립할 때만 맞다. `VolumeSettings.ARCS_PER_VOLUME` 상수가 5로 설정되어 있으므로(L364, `vol_no = ((global_arc_no - 1) // VolumeSettings.ARCS_PER_VOLUME) + 1`), 실제 볼륨 구조와 불일치한다. ARCS_PER_VOLUME=5이면 Vol 1 = Arc 1~5, Vol 2 = Arc 6~10인데, 볼륨 요약은 Arc 10에서 Arc 1~10을 하나의 요약으로 생성한다.
- **위험도**: 볼륨 요약은 advisory 기능이므로 Arc 설계 자체에는 영향 없음. 단, 시리즈 요약의 정확도가 떨어질 수 있다.
- **수정안**: `VolumeSettings.ARCS_PER_VOLUME`에 기반한 동적 계산으로 변경. 또는 하드코딩 10을 상수로 외부화.

---

## 6. 데드 코드 점검 (1차 후속)

1차에서 P1-1(passed=True), P1-2(_SUMMARY_MODEL), P1-3(ReflectionTarget import), P2-3(_build_relationship_history), P2-4(should_increase_constraints) 5건의 데드 코드가 지적되었다.

### 6-1: P1-1 (passed=True) 검증

Finalizer 전체를 재검색한 결과 `passed = True`가 Finalizer 내부에 존재하지 않음을 확인. Orchestrator L557에서 `passed = True`가 `_fin["action"] == "break"` 시 설정되므로 올바르게 분리됨. **수정 확인 완료**.

### 6-2: P2-3, P2-4 검증

`stage2_optimizer.py`를 전수 검색한 결과, `_build_relationship_history`와 `should_increase_constraints` 메서드가 여전히 존재함을 확인. **미수정 상태** (위험도 낮음, 향후 정리 가능).

실측 결과, `stage2_optimizer.py`에서 `_build_relationship_history` 메서드가 보이지 않는다. `NegativeConstraintAmplifier` 클래스에는 `_build_item_history`(L476)과 `_build_grant_history`(L507)만 존재하며, `_build_relationship_history`는 1차 감사 시점 이후 이미 삭제된 것으로 판단. `should_increase_constraints`도 `SessionFailureMemory` 클래스에서 발견되지 않음. **양쪽 모두 삭제 완료 확인**.

---

## 7. 개선 아이디어 (신규)

### IDEA-NEW-1: FourPhase 경로에서 `state_changes` 기본값 보장

- **파일**: `modules/core/stage2_finalizer.py` (PASS 경로)
- **현재**: Analyst 폴백 경로에서는 `_post_process_arc()`가 `state_changes`의 13개 하위 키를 보장하지만, FourPhase 경로에서는 이 후처리가 없다.
- **제안**: Finalizer PASS 경로(L202 부근)에서 `state_changes` 기본값 보장 로직을 추가:
  ```python
  if "state_changes" not in refined_arc or not isinstance(refined_arc.get("state_changes"), dict):
      refined_arc["state_changes"] = {}
  for key in ["npc_deaths", "skill_acquisitions", ...]:
      refined_arc["state_changes"].setdefault(key, [])
  ```
- **효과**: Stage 3에서 `state_changes` 하위 키 접근 시 안전성 보장.

### IDEA-NEW-2: `ConstraintDB` dict 아이템 정규화 통합

- **파일**: `modules/core/constraint_db.py:131-136`
- **현재**: `phys_inv`의 dict 아이템이 정규화 없이 inventory에 추가됨.
- **제안**: `_parse_arc_state` 입구에 공통 정규화 함수 적용:
  ```python
  def _normalize_item(item):
      if isinstance(item, dict):
          return item.get("name", item.get("item", str(item)))
      return str(item).strip() if item else ""
  ```
- **효과**: inventory, acquired_items, consumed_items 모두에서 일관된 문자열 비교 가능.

### IDEA-NEW-3: 통합 retry 카운터 도입

- **파일**: `modules/core/stage2_orchestrator.py`, `stage2_preflight.py`
- **현재**: FourPhase 내부 재시도(`max_internal_retries=4`)와 외부 Director 재시도(`max_attempts=5`)가 독립적. 최악의 경우 4 x 5 = 20회 LLM 호출.
- **제안**: `_enrichment` 반환값에 FourPhase 내부 재시도 횟수를 포함시키고, Orchestrator에서 누적 카운터를 관리하여 총 시도 횟수 15회 등의 상한을 설정.
- **효과**: 비용 예측 가능성 향상, API 할당량 고갈 방지.

### IDEA-NEW-4: `_stage2_flow_guard` NarrativeStructureAnalyzer 호출 캐싱

- **파일**: `modules/core/stage2_validation_pipeline.py:657-695`
- **현재**: `_stage2_flow_guard()`가 호출될 때마다 `NarrativeStructureAnalyzer`를 새로 인스턴스화하고 LLM을 호출한다. 같은 Arc에 대한 retry에서 `refined_arc`가 변경되지 않았을 경우 불필요한 중복 호출이 발생한다.
- **제안**: `refined_arc`의 `beat_sequence` 해시를 키로 하는 캐시를 도입. 동일 beat_sequence면 이전 결과를 재사용.
- **효과**: retry 시 Arc당 1회 LLM 호출 절감 (SUMMARY_MODEL 호출이므로 비용 낮지만 지연 시간 절감).

### IDEA-NEW-5: `UnifiedArcValidator` Python 검증과 `ArcDraftValidator` 검증의 역할 중복 정리

- **파일**: `unified_arc_validator.py` vs `arc_draft_validator.py`
- **현재**: 두 검증기가 유사한 Python 검증(분량, 필수 필드, 중복 아이템)을 수행한다. `UnifiedArcValidator`는 FourPhase 에이전트 내부에서, `ArcDraftValidator`는 `stage2_validation_pipeline.py`에서 호출된다. 중복 감지 로직의 세부 구현이 다르며(UnifiedArcValidator는 LLM 2차 검증 포함, ArcDraftValidator는 Python only), 유지보수 시 한쪽만 업데이트하면 다른 쪽이 뒤처질 수 있다.
- **제안**: Python 검증 로직을 공통 모듈로 추출하여 양쪽에서 공유. 또는 `ArcDraftValidator`를 `UnifiedArcValidator._python_validate()`의 thin wrapper로 리팩토링.
- **효과**: 검증 로직 일원화로 유지보수성 향상.

### IDEA-NEW-6: `analyst.py` `plan_single_arc_v20`의 legacy 정리

- **파일**: `modules/domain/agents/analyst.py:525-885`
- **현재**: `plan_single_arc_v20`은 360줄에 달하는 대형 메서드로, 파일 상단 주석에 "레거시 - FourPhaseArcGenerator.generate()가 Stage 2 진짜 주인"이라 명시되어 있다. Orchestrator에서 fallback 호출이 제거되었으므로 이 메서드는 외부 API 진입점으로만 유지된다.
- **제안**: `plan_single_arc_v20`을 별도 파일(`analyst_legacy_arc.py`)로 분리하거나, 진짜 외부 호출이 없으면 `@deprecated` 마크와 함께 정리. 현재 `plan_batch_arcs_v25`(L1109)가 내부적으로 `plan_single_arc_v20`을 호출하므로, 이 메서드도 함께 정리 필요.
- **효과**: `analyst.py` 가독성 향상 (현재 1475줄 -> 360줄 절감 가능).

---

## 8. 총평

### 1차 수정 검증 결과

1차 감사에서 지적된 P1 5건 + P2 7건 중 검증 대상 6건 모두 올바르게 수정되었음을 확인했다. 특히:

- `_perf_lock` 도입(S2-P1-5)이 정확한 스코프(함수 로컬)에서 적용되어 불필요한 글로벌 락 오버헤드 없이 스레드 안전성을 확보함.
- `max_attempts` 외부화(S2-P2-5)가 `int()` 래핑과 함께 적용되어 타입 안전성도 동시에 해결함.
- 1차에서 지적된 데드 코드(P2-3, P2-4)도 이미 삭제 완료.

### 2차 신규 발견

- **P1 3건**: `n_results` 타입 불일치(P1-NEW-1), 변수 스코프 방어(P1-NEW-2), `_rejected_arc` 초기화(P1-NEW-3). 모두 현재 동작에는 영향 없으나 방어적 코딩 관점에서 개선 권장.
- **P2 5건**: 스타일 일관성 및 미미한 논리 개선 사항.
- **P0 0건**: 차단급 버그 미발견. Stage 2 파이프라인은 매우 안정적.

### 구조적 강점 재확인

1. **Pydantic ingress/egress** (`validate_arc`): Finalizer에서 DB 저장 직전에 스키마 검증을 수행하여 잘못된 Arc 구조가 저장되는 것을 원천 차단.
2. **StateTracker 스냅샷/롤백**: `copy.deepcopy` 기반 18필드 스냅샷이 Director REJECT 시 팬텀 데이터를 정확히 제거. `_perf_lock`으로 스레드 안전성도 확보.
3. **Patch Mode**: `PatchModeThresholds.REWRITE` 기준으로 전면 재생성/부분 수정을 분기하는 전략이 비용 효율적.
4. **Sweep45 방어 패턴**: `.get()` 폴백, `isinstance` 체크, dict/list/str 타입 방어가 전체 코드베이스에 일관 적용.

### 잔여 리스크

1. **FourPhase 경로의 `state_changes` 미보장**: Stage 3 연결성에 잠재적 영향. IDEA-NEW-1로 해결 가능.
2. **`UnifiedArcValidator` dict 아이템 우회**: 중복 감지 정확도에 영향. P2-NEW-3 + 5-3으로 지적.
3. **프롬프트 토큰 예산**: 1차 I8에서 로깅은 추가되었으나 적극적 절삭 메커니즘은 없음. 50+ Arc 프로젝트에서 context window 초과 가능성 잔존.
