# TF-7-B 감사 보고서 — Context Advisor / Smart Retrieval

## 감사 파일 목록
- `modules/core/context_advisor.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/vec_memory.py`
- `main_a.py`

## 발견 이슈 (총 2건)

### [TF-7-B-1] Stage4 NPC 히스토리 토큰화가 일반 한국어 단어를 우선 코어 키로 채워 실제 NPC 매칭 정확도를 떨어뜨림 (HIGH)
**근거 파일/줄**
- `modules/core/context_advisor.py:476`~`modules/core/context_advisor.py:478`  
  `npc_history` 쿼리 포맷이 `"등장 NPC 과거 행적/관계/상태: ..."` 형태.
- `modules/core/stage4_context_builder.py:39`~`modules/core/stage4_context_builder.py:53`  
  stopword 집합이 영어 중심(`npc`, `history`, `context` 등)이고 한국어 일반어 제거 규칙이 없음.
- `modules/core/stage4_context_builder.py:143`~`modules/core/stage4_context_builder.py:149`  
  추출된 토큰을 그대로 `retrieve_npc_context(npc_names=...)`에 전달.
- `modules/core/vec_memory.py:541`~`modules/core/vec_memory.py:543`  
  전달 목록의 앞 5개만 `core_names`로 사용.
- `modules/core/vec_memory.py:549`~`modules/core/vec_memory.py:557`  
  강한 매칭(직접 entity LIKE 검색)은 `core_names`만 사용.

**문제**
- `Stage4ContextBuilder._extract_npc_tokens()`가 `"등장"`, `"과거"`, `"행적"`, `"관계"`, `"상태"` 같은 일반어를 제거하지 못한다.
- 그 결과 실제 NPC명이 `core_names`에서 밀려나거나 overflow로 이동해, 가장 강한 direct-entity 매칭이 약화된다.

**영향**
- Stage4 Writer 경로에서 NPC 연속성 검색 precision이 떨어지고, 회수해야 할 인물 히스토리를 놓칠 수 있다.
- 동일 프로젝트 내 Stage2/Director 경로 대비 Stage4만 상대적으로 잡음이 커진다.

**Caller→Callee 계약 추적**
- Caller: `ContextAdvisor._build_stage4_slots()`가 생성한 `npc_history` 문자열 슬롯
- Callee: `Stage4ContextBuilder._execute_retrieval_plan()` → `VecMemory.retrieve_npc_context()`
- 하위 계약: `retrieve_npc_context`는 입력 앞쪽 토큰을 코어로 취급

**Bug-vs-intent 근거**
- 함수 목적이 “NPC token 추출”인데, 현재 구현은 일반 설명어를 NPC 후보로 취급해 목적과 충돌한다.
- 같은 리포지토리의 Stage2 경로는 `fallback_names`(사전 수집 roster)를 우선 사용해 이 문제를 완화한다 (`modules/core/stage2_preflight.py:116`~`modules/core/stage2_preflight.py:129`).

**권장 수정 방향**
- `_extract_npc_tokens()`에 한국어 일반어 stopword/품사 기반 필터 추가.
- 또는 Stage2처럼 slot query 파싱 대신 사전 수집한 `npc_roster`를 1순위로 전달.

### [TF-7-B-2] Stage4 SC 예산 트림이 `stage4_enabled`를 무시하고 mandatory_context 전체에 적용되어 비-SC 문맥까지 절삭될 수 있음 (MEDIUM)
**근거 파일/줄**
- `modules/core/stage4_context_builder.py:678`~`modules/core/stage4_context_builder.py:680`  
  실제 Stage4 SC retrieval 실행은 `smart_retrieval.stage4_enabled`를 확인.
- `modules/core/stage4_context_builder.py:795`~`modules/core/stage4_context_builder.py:797`  
  하지만 budget 적용은 `smart_retrieval.enabled`만으로 수행(`stage4_enabled` 미확인).
- `modules/core/stage4_context_builder.py:178`~`modules/core/stage4_context_builder.py:180`  
  전달 budget이 0이면 `smart_retrieval.stage4_total_budget` fallback으로 재설정.
- `modules/core/stage4_context_builder.py:185`~`modules/core/stage4_context_builder.py:189`  
  트래커 등록 대상이 `_mc_parts` 전체(팩트원장/월드상태/요약/SC 포함).
- `modules/core/stage4_context_builder.py:203`~`modules/core/stage4_context_builder.py:217`  
  가장 큰 섹션부터 절삭(섹션 타입 구분 없음).

**문제**
- Stage4 SC가 비활성(`stage4_enabled=false`)이어도 전역 플래그만 켜져 있으면 `_apply_context_budget()`가 동작한다.
- 절삭 대상이 SC 섹션에 한정되지 않아, 비-SC 필수 문맥(월드 상태/팩트 원장/장기 요약)까지 잘릴 수 있다.

**영향**
- Stage4 SC 기능을 끈 운영 모드에서도 예기치 않은 mandatory_context 손실이 발생할 수 있다.
- prompt 품질 저하가 “조용히” 발생해 원인 추적이 어려워진다.

**Caller→Callee 계약 추적**
- Caller: `Stage4Orchestrator` → `Stage4ContextBuilder.build_mandatory_context()`
- Callee: `_apply_context_budget(_mc_parts, _sc_budget)`
- 계약 불일치: Stage4 feature gate와 예산 트림 gate가 다름

**Bug-vs-intent 근거**
- Stage4 retrieval 경로는 stage별 enable 키를 존중하는데, 후속 예산 절삭은 같은 stage gate를 따르지 않는다.
- SC 예산이라는 이름/키를 쓰면서 비-SC 섹션 전체를 절삭하는 동작은 기능 경계와 어긋난다.

**권장 수정 방향**
- `_apply_context_budget` 호출 조건을 `smart_retrieval.enabled && smart_retrieval.stage4_enabled`로 정렬.
- 절삭 대상은 `[SC:*]` 섹션만 우선 적용하거나, 섹션 타입별 보호 우선순위(예: fact/world 고정) 도입.

## Risk (총 2건)

### [TF-7-B-R1] `slot.max_chars` 기본값 적용이 Stage4 소비자 간 불일치 (MEDIUM, Risk)
**근거 파일/줄**
- `modules/core/stage4_interview_round.py:464`~`modules/core/stage4_interview_round.py:465`  
  `_threshold("smart_retrieval.slot_max_chars_default", 1500)`와 `max_npcs_per_slot`을 별도 사용.
- `modules/core/stage4_interview_round.py:477`  
  slot max 미설정 시 `_default_slot_max` fallback.
- `modules/core/stage4_context_builder.py:164`~`modules/core/stage4_context_builder.py:166`  
  builder 경로는 `slot.max_chars > 0`일 때만 trim, 기본 fallback 없음.
- `modules/core/context_advisor.py:113`  
  `RetrievalSlot.max_chars` 기본값은 0.

**Risk 판단 근거**
- 현재 기본 예산이 양수라 당장 드러나지 않을 수 있으나, 슬롯 max가 0인 시나리오(설정/커스텀 enricher)에서 Writer와 Director 경로 동작이 달라질 수 있다.

### [TF-7-B-R2] Stage3 DI 컨텍스트와 실제 SC 소비 경로가 분리되어 테스트/교체 용이성이 낮음 (MEDIUM, Risk)
**근거 파일/줄**
- `modules/core/stage3_context.py:16`~`modules/core/stage3_context.py:40`  
  Stage3Context 슬롯에 `context_advisor`가 없음.
- `modules/core/stage3_orchestrator.py:438`  
  Stage3 SC는 `self.app.context_advisor`를 직접 참조.
- `modules/core/stage3_orchestrator.py:46`  
  DI 컨텍스트를 사용하더라도 실제 SC 의존성은 app 경유.

**Risk 판단 근거**
- 동작 자체는 가능하지만 DI 경로와 런타임 참조 경로가 분리되어, 리팩터링/모킹/회귀검증 시 누락 위험이 있다.

## [FP] 오탐 목록

### [FP-1] ContextAdvisor가 `plan()`에서 `None`을 반환할 수 있다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/context_advisor.py`에는 범용 `plan()`이 없고, stage별 `plan_stage{2,3,4}`/`plan_director_retrieval`만 존재.
  - 각 메서드는 `_build_plan()` 결과 `RetrievalPlan`을 반환 (`modules/core/context_advisor.py:201`~`modules/core/context_advisor.py:273`, `modules/core/context_advisor.py:275`~`modules/core/context_advisor.py:289`).

### [FP-2] ContextAdvisor 내부 `_plan_cache`가 프로젝트 전환 시 stale된다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/context_advisor.py`에 `_plan_cache` 또는 유사 캐시 필드가 없다.
  - 프로젝트 부팅 시 `ContextAdvisor`는 새로 생성된다 (`main_a.py:1805`).

### [FP-3] Stage4에서 SC retrieval은 동일 플랜을 중복 호출한다
- **판정**: 오탐(부분)
- **수동 근거**:
  - Writer 경로: `plan_stage4_retrieval` (`modules/core/stage4_context_builder.py:687`)
  - Director 경로: `plan_director_retrieval` (`modules/core/stage4_interview_round.py:454`)
  - 둘 다 “중복 호출”은 맞지만 목적/프롬프트 대상이 다른 별도 플랜이다.

## TF-6 G-1 패치 확인 결과

| 점검 항목 | 결과 | 근거 |
|---|---|---|
| Director 소비 경로가 `_threshold("smart_retrieval.slot_max_chars_default", 1500)` 사용 | 확인됨 | `modules/core/stage4_interview_round.py:464` |
| Director 소비 경로가 `_threshold("smart_retrieval.max_npcs_per_slot", 5)` 사용 | 확인됨 | `modules/core/stage4_interview_round.py:465` |
| Writer(Stage4ContextBuilder) 소비 경로도 동일 fallback 정책 적용 | 미확인 | `modules/core/stage4_context_builder.py:164`~`modules/core/stage4_context_builder.py:166` |

## 요약 테이블

| 심각도 | 건수 | 항목 |
|---|---:|---|
| HIGH | 1 | `TF-7-B-1` |
| MEDIUM | 1 | `TF-7-B-2` |
| Risk | 2 | `TF-7-B-R1`, `TF-7-B-R2` |
| FP | 3 | `FP-1~3` |
