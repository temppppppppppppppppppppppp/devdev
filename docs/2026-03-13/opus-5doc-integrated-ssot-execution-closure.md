# OPUS 5문서 통합 SSOT 실현 오더 — 실행 Closure

> 작성일: 2026-03-13
> 기준 문서: `docs/2026-03-13/opus-5doc-integrated-ssot-realization-order.md`
> 상태: execution closed

---

## 1. 실행 결과

### Unit 0. 문서 기준선 정정

- 완료
- Stage 0 통합본 산술 오류 정정
- Stage 4 통합본 M-1/M-2 실행 단위 주석 보강
- XC 통합본 raw count 84건 비실행 수치 고정

### Unit 1. 운영 중단/무성 실패 방지

- 완료
- Advisory timeout 후 executor hang 경로 비차단 종료로 수정
- `_safe_commit()` false 경로 rollback 보강
- Stage 2 실패/보정 이력을 Stage 4 mandatory context에 주입

### Unit 2. Stage 2 계약/스키마 정합

- 완료
- `Stage2Context`에 `world_state` 배선 추가
- `ARC_DESIGN_SCHEMA`의 `timeline.start/end`를 object 계약으로 정렬
- `npc_deaths`를 object 배열로 정렬
- `skill_acquisitions` schema 누락 보강
- `physical_inventory` / `arc_start_state.equipment` 자동 계승은 기존 코드 유지, 문서상 설계 규칙으로만 잠금

### Unit 3. Stage 0 상태 위생

- 완료
- `generate_bible()` 실패 시 stale `self.bible` 제거 및 `{}` 반환으로 상태 일치
- `PresetRegistry._enforce_type()`의 list/dict 경로를 deep copy로 보강
- Bible 저장 실패 시 Treatment 단독 저장/리로드를 차단해 partial save 제거
- Stage 0 외부 시점 삽입 정책 메뉴 mojibake 복구

### Unit 4. Stage 3/4 검증 경로

- 완료
- Stage 3 Treatment Block 주입 경로 테스트 추가
- Stage 3 `blueprint_gen_error` 크래시 경로 테스트 추가
- Stage 4 `_threshold()` 기본값을 YAML SSOT와 정렬
- Stage 4 EMPTY 결과를 기록 시점에서도 `EMPTY`로 정규화
- Stage 4 advisory 병렬 실행이 shared `validation_results`를 직접 mutate하지 않도록 local copy + merge 방식으로 변경
- Entity Registry는 Stage 3/4 간 캐시 공유로 통합하지 않고, stage-local extraction 유지로 정책 결정

---

## 2. 보류/비수정 결정

- Unit 5 보류 항목은 그대로 보류한다.
- BaseAgent context cache invalidation 전면 정책
- raw provider response 추상화 계층
- Stage 4 cosmetic 정리
- 원문 P3 전량 정리

보류 이유:
- 이번 실행 범위는 운영 안정성, 계약 정합, 상태 위생, 검증 경로 보강까지다.
- 멀티 프로바이더 계층과 광역 캐시 정책은 별도 tranche가 맞다.

---

## 3. 검증 결과

실행 후 회귀:

```text
pytest tests/test_project_service.py tests/test_stage4_context_builder.py tests/test_stage4_interview_round.py tests/test_stage2_context.py tests/test_llm_schema.py tests/test_stage3_orchestrator.py tests/test_stage4_orchestrator.py tests/test_pydantic_models.py tests/test_opus_tf5_e6_regressions.py tests/test_stage01_helpers.py tests/test_stage0_pov.py tests/test_stage0_fixes.py tests/test_sweep28.py tests/test_sweep39.py tests/test_stage2_preflight.py tests/test_stage2_finalizer.py -q
481 passed in 33.30s
```

---

## 4. 최종 판정

- `P0`: 없음
- `P1`: 원 SSOT 기준 3건 모두 조치 완료
- Unit 0~4: 종료
- 원 SSOT는 감리 기준 문서로 유지
- 본 문서는 실행 결과 closure SSOT다
