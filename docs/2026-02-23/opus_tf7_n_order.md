# TF-7-N: 크로스컷 시나리오 스윕 (종단간) — 감사 실행 오더

> **Opus TF-7-N** | 2026-02-23
> **담당**: Opus 에이전트 N
> **출력**: `docs/2026-02-23/opus_tf7_n_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / 근거 필수

---

## 개요
모듈 단위 감사(TF-7-A~M)가 끝난 후 **데이터 흐름 축**으로 접근. 경계 시나리오 10개를 파이프라인에 투과시켜 모듈 간 seam(접합부) 버그를 탐지. 시나리오별로 시작 파일을 Read 도구로 읽고, 호출 경로를 따라 다음 파일로 이동하는 수동 추적 방식.

---

## 시나리오별 실행 지침

---

### N-01: Episode 1 초기 진입 — 이전 데이터 전무

**핵심 질문**: Episode 1에서 "이전 에피소드가 없음"이 파이프라인 전체에서 일관되게 처리되는가?

**추적 경로**:
1. `modules/core/stage4_context_builder.py` → `lookback_digest` 메서드 찾기
   - `ep_num=1`일 때 `ep_num - 1 = 0` 조회 → DB 결과 없음 처리
   - None 반환 vs 빈 dict vs 빈 문자열 중 어느 것인가
2. `modules/domain/agents/chief_writer_context.py` → lookback_digest 소비 경로
   - None/빈값을 받을 때 프롬프트 생성 동작
3. `modules/domain/agents/director.py` → Episode 1 판정 특이사항
4. `modules/validation/continuity_validator.py` → 이전 에피소드 없을 때 처리 (TF-7-D Step 6과 연계)

**기록**: 각 파일에서 `ep_num=1` 분기 처리의 일관성

---

### N-02: 에피소드 롤백 후 NPC 상태 재진입

**핵심 질문**: 롤백 후 다음 에피소드 생성 시 롤백된 상태가 파이프라인에 올바르게 반영되는가?

**추적 경로**:
1. `modules/core/services/project_service.py` → `rollback_episode()` (TF-6-A 패치 후 상태)
   - WorldState, FactLedger, StateDelta 롤백 원자성 (TF-7-E 결과 참조)
2. `modules/domain/agents/state_tracker.py` → 롤백 후 NPC 상태 재로드
3. `modules/core/fact_ledger.py` → 롤백 대상 에피소드 이후 팩트 필터링
4. `modules/core/stage4_context_builder.py` → 롤백된 NPC 목록으로 컨텍스트 재구성
5. `modules/core/genre_guards/` → 사망NPC 재등장 방지 가드 (대원칙 4)

**기록**: 롤백 이후 stage4로 다시 진입 시 stale 상태 잔존 경로

---

### N-03: 사망 NPC(`deceased=True`)가 Arc에 등장 시도

**핵심 질문**: `deceased=True` NPC가 Arc에 등장할 때 파이프라인 어느 단계에서 REJECT되는가? 혹시 통과되는 경로가 있는가?

**추적 경로**:
1. `modules/domain/agents/analyst.py` → Arc 생성 프롬프트에 deceased NPC 정보 포함 여부
2. `modules/core/stage2_validation_pipeline.py` → NPC 등장 검증 경로
3. `modules/core/fact_ledger.py` → deceased 팩트 조회
4. `modules/validation/blocking_validator.py` → deceased NPC 행동/대사 감지 규칙
5. `modules/domain/agents/director.py` → Director 최종 판정에서 deceased NPC 탐지

**기록**: REJECT 경로가 없거나 우회 가능한 구간

---

### N-04: 장르 전환 감지 — Block 30에서 [fantasy] 추가

**핵심 질문**: 실행 중 새 장르 프리셋이 활성화될 때 Guard 체인과 StateTracker에 즉시 반영되는가?

**추적 경로**:
1. `modules/core/stage0/preset_registry.py` → 동적 프리셋 추가 메서드
2. `modules/domain/agents/state_tracker.py` → 프리셋 변경 통지 수신 경로
3. `modules/core/genre_guards/fantasy_guard.py` → 새 Guard 초기화
4. `modules/validation/validation_orchestrator.py` → Guard 체인 업데이트 경로

**기록**: 프리셋 추가 시 Guard 체인이 즉시 업데이트되는지, 다음 에피소드부터인지, 전혀 반영 안 되는지

---

### N-05: LLM Arc 응답 빈 dict `{}`

**핵심 질문**: LLM이 Arc 생성에서 `{}`를 반환할 때 파이프라인이 크래시 없이 REJECT하고 재시도하는가?

**추적 경로**:
1. `modules/domain/agents/four_phase_arc_generator.py` → `_extract_json_robust()` 결과가 `{}` 일 때
2. `modules/core/stage2_validation_pipeline.py` → 빈 dict 처리 분기
   - `arc_data.get("ep_count")` = None → `int()` 캐스트 오류 위험
3. `modules/core/stage2_orchestrator.py` → REJECT 후 재시도 루프
4. `modules/core/adaptive_retry.py` → 재시도 횟수 제한

**기록**: `{}` 입력 시 각 스테이지에서의 처리 및 최종 결과

---

### N-06: 모든 Director 전략 REJECT (5라운드)

**핵심 질문**: 5라운드 모두 REJECT 시 폴백이 안전하게 동작하는가?

**추적 경로**:
1. `modules/core/stage4_interview_round.py` → REJECT 카운터 로직
2. `modules/core/stage4_orchestrator.py` → 5회 REJECT 후 폴백 분기
   - 폴백 원고 사용 vs 사용자 입력 대기 vs 예외
3. `modules/core/adaptive_retry.py` → 재시도 전략 소진 처리
4. `modules/core/failure_learning.py` → 실패 패턴 기록

**기록**: 폴백 경로 완결성 및 사용자에게 명확한 피드백 여부

---

### N-07: Blueprint `scenes=None` 관통

**핵심 질문**: `blueprint.get("scenes")=None`이 `stage4_context_builder`를 통해 `blocking_validator_scene_checks`에 도달할 때 silent PASS가 발생하는가?

**추적 경로**:
1. `modules/domain/agents/blueprint_ensemble.py` → `scenes` 필드 없는 Blueprint 반환 경로
2. `modules/core/stage4_context_builder.py` → `_build_scene_context(blueprint)` 분기
   - `blueprint is None` vs `blueprint.get("scenes") is None` 처리
3. `modules/validation/blocking_validator_scene_checks.py` → `scenes=None` 시 동작 (TF-7-D Step 3 결과 참조)

**기록**: None 관통 시 silent PASS 경로 존재 여부

---

### N-08: 상태 누적 1000에피소드 — TF-6 B 패치 검증

**핵심 질문**: TF-6 TF-B 패치(resolved_plots 500상한, all_reveals 500상한, feedback_log deque 200) 후 실제로 상한이 작동하는가?

**검증 대상**:
1. `modules/domain/agents/state_tracker.py` → `_resolved_plots_max = 500` 속성 존재 여부
2. `modules/domain/agents/state_tracker_plots.py` → append 후 에비싱 코드 존재 여부
3. `modules/core/db_manager.py` → `all_reveals[-500:]` 슬라이싱 코드 위치
4. `modules/core/data_collector.py` → `deque(maxlen=200)` 적용 여부

**기록**: 4개 패치 각각 적용 여부 (Yes/No + 줄 번호)

---

### N-09: `ep_count=1` 단일 에피소드 아크 — TF-6 E 패치 검증

**핵심 질문**: TF-6 TF-E-1 패치(`_min_beats = max(1, ep_count)`) 후 `ep_count=1` Arc가 Flow Guard를 통과하는가?

**검증 대상**:
1. `modules/core/stage2_validation_pipeline.py` L626 근처
   - 패치 코드: `_min_beats = max(1, ep_count)` + 변수 `_MIN_BEATS_FLOOR` 존재 여부
2. `config/settings/validation.yaml` → `scope.min_beats_floor: 1` 키 확인

**기록**: 패치 적용 여부 (Yes/No + 줄 번호)

---

### N-10: 멀티스레드 Arc 생성 중 1개 타임아웃

**핵심 질문**: `arc_ensemble`에서 병렬 생성 중 1개 Future가 타임아웃될 때 나머지 결과가 올바르게 수집되고, `stage2_orchestrator`의 recovery_map이 올바르게 동작하는가?

**추적 경로**:
1. `modules/domain/agents/arc_ensemble.py` → Future 타임아웃 처리
   - `concurrent.futures.wait(timeout=...)` 사용 여부
   - 타임아웃 Future에 대한 `future.cancel()` 호출
2. `modules/core/stage2_orchestrator.py` → `_success_indices + recovery_map` 로직
   - 실패 Arc 인덱스 처리: skip vs 재시도 vs 빈 Arc로 채우기
3. `modules/core/stage2_finalizer.py` → 부분 성공 상태에서 finalizer 동작

**기록**: 타임아웃 시 데이터 무결성 보장 경로

---

## 출력 파일 구조
```
# TF-7-N 감사 보고서 — 크로스컷 시나리오 스윕

## 시나리오별 결과 요약 테이블
| 시나리오 | 결과 | 이슈 수 | 심각도 |
|---------|------|---------|--------|
| N-01 Episode 1 초기화 | ... | 0 | - |
...

## 발견 이슈 (총 N건)
### [TF-7-N-01-1] ...

## TF-6 패치 회귀 확인 (N-08, N-09)
| 패치 | 확인 여부 | 증거 |
|------|----------|------|
| TF-B-1 resolved_plots 상한 | ✅/❌ | state_tracker.py:L{n} |
...

## Cross-TF 이슈 (복수 TF 관련)
## [FP] 오탐 목록
## 요약 테이블
```

---

## 참고: 시나리오 선택 근거
- N-01~02: Episode 경계 (가장 흔한 실패 지점)
- N-03: 대원칙 4 (사망 NPC 규칙) 파이프라인 구현 검증
- N-04: 동적 장르 전환 (Stage0 ↔ Stage2 연동, TF-7-K 보완)
- N-05~07: LLM 비정상 응답 관통 (Silent 오류 탐지)
- N-08~09: TF-6 패치 회귀 검증
- N-10: 병렬 처리 복원력
