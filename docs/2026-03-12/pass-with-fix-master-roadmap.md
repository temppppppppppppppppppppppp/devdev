# PASS_WITH_FIX 전면 개선 마스터 로드맵

작성일: 2026-03-12  
문서 역할: `PASS_WITH_FIX / inplace / Stage 3·4 semantics / logging·analytics / rerun gate`를 하나의 phase roadmap으로 묶는 최상위 SSOT  
기준 근거: `docs/2026-03-12/pass-with-fix-partial-fix-3pass-audit.md`
Phase 1 실행 스펙: `docs/2026-03-12/pass-with-fix-phase1-execution-spec.md`

참고 문서:

- `docs/2026-03-12/TF-S3-context-contract-audit.md`
  - 사용 목적: `Stage 3 external verdict`, `S3 context contract`, `S3→S4 handoff` 판단을 다시 잠글 때 참조
- `docs/2026-03-12/stage4-context-contract-full-survey-3pass-audit.md`
  - 사용 목적: `CW-Director context contract`, `PASS_WITH_FIX local patch feedback 축약`, `Stage 4 patch provenance` retained finding을 roadmap에 연결할 때 참조

## 0. 문서 위치와 역할

이 문서는 `PASS_WITH_FIX` 전면 개선 initiative의 최상위 로드맵이다.

- 감사 문서: 현재 상태와 증거를 고정한다.
- 상세 실행 메모: phase별 상세 구현 메모와 검증 항목을 보관한다.
- rerun 체크리스트: live 검증 단계에서만 사용한다.

즉, `무엇을 왜 어떤 순서로 바꿀지`는 이 문서가 결정하고, 나머지 문서는 증거/세부실행/운영검증을 담당한다.

## 1. 한 줄 결론

현재 시스템의 핵심 문제는 `CW 일반 글쓰기 방식` 자체가 아니라 `PASS_WITH_FIX`와 `inplace 수정 경로`의 구조적 한계 및 final semantics 불일치다.

따라서 이번 initiative는 아래 원칙을 고정한다.

1. `CW 일반 글쓰기 생성 구조`는 직접 변경 대상이 아니다.
2. 직접 개선 대상은 `PASS_WITH_FIX`, `inplace`, `Stage 3/4 계약`, `logging/analytics`, `rerun readiness`다.
3. `structural inplace`는 가능하며 ROI가 낮지 않다.
4. 다만 `CW 본체 재설계`가 아니라 `patch 경로만 block-aware/scene-aware로 구조 개선`하는 방향을 기본안으로 둔다.

## 2. 현재 문제 목록

이번 initiative에서 닫아야 할 현재 문제는 아래 6개다.

1. `PASS_WITH_FIX` 의미 충돌
- 어떤 문서는 과도 상태로 보고, 어떤 경로는 사실상 soft success처럼 소비한다.

2. Stage 4 final semantics 불일치
- `PASS_WITH_FIX -> patch -> PASS` 후에도 score/label/attempt 기록이 최초 심사 기준으로 남을 수 있다.

3. Stage 3 외부 계약 불안정
- Stage 3는 아직 `PASS_WITH_FIX`를 외부 success verdict로 내보내는 해석이 남아 있다.

4. logging sink 역할 분리 부재
- `director_selections`, `episode_production`, `stage_attempts`, `pass_rate_monitor`가 같은 시도를 서로 다른 의미로 보여 준다.

5. analytics/DB 집계 불일치
- `PASS_WITH_FIX`를 pass-like success로 보는 집계가 남아 있다.

6. Stage 4 whole-text inplace의 구조적 한계
- 현재 inplace는 엄밀한 부분 편집이 아니라 `원본 보존을 강하게 요구한 전체 재생성`에 가깝다.
- 이 때문에 shrink, drift, 불필요한 재작성 위험이 존재한다.

## 3. 명시적 비대상

이번 initiative에서 직접 건드리지 않는 항목은 아래와 같다.

- `generate_ensemble()` 중심의 CW 일반 글쓰기 구조 대수술
- block-native 전체 재작성 파이프라인 도입
- 전면적인 prompt 재설계
- context compression 아키텍처 전면 재작성
- hybrid profile, fanout, firewall routing 등 후속 behavior 실험

위 항목은 별도 initiative 또는 후순위 실험으로 다룬다.

## 4. 목표 상태

개선 완료 후 목표 상태는 아래와 같다.

### 4.1 PASS_WITH_FIX 계약

- 기본값: `PASS_WITH_FIX`는 `transient/internal verdict`
- 외부 최종 verdict 기본안: `PASS` 또는 `REJECT`만 허용
- Stage 3는 예외 허용이 아니라 기본안에 맞춰 재정렬하는 방향을 권고
- 단, `PASS_WITH_WARNING`은 이번 initiative에서 별도 degraded-success verdict로 유지하며 `PASS_WITH_FIX` 정리와 혼합하지 않는다

### 4.2 Stage 4 final semantics

- `PASS_WITH_FIX -> patch -> PASS`가 되면 최종 score/label/attempt 기록은 모두 재심사 결과와 일치해야 한다.
- `director_score`, `_director_quality_labels`, `stage_attempts`는 같은 final semantics를 가져야 한다.

### 4.3 structural inplace

- 목표는 `전체 원고 재생성`이 아니라 `문제 block만 교체 + 나머지 원문 보존`
- `문단별 JSON` 자체가 필수는 아니지만, 내부 편집 구조는 `block-aware`여야 한다.
- local issue는 `inplace`, global issue는 `partial/full`로 보내는 라우팅 규칙을 명시한다.

### 4.4 logging / analytics / rerun

- sink 역할이 문서상 하나로 고정된다.
- structural inplace 직후에는 `full logging overhaul`이 아니라 `최소 계측`부터 붙인다.
- live rerun은 계약 고정과 최소 계측 이후에만 수행한다.

## 5. structural inplace 기본안

이번 문서의 권고안은 `CW 본체 보존 + patch 경로 구조화`다.

### 5.1 기본 방향

- 평시 CW 생성은 현행 유지
- `PASS_WITH_FIX` 발생 시에만 block-aware/scene-aware 수정 경로 사용
- 수정하지 않는 block은 원문 그대로 유지
- 수정 block은 앞/뒤 block context를 함께 보고 국소 수정
- 경계 문장 smoothing pass는 짧고 제한적으로만 허용

### 5.2 재사용 가능한 기존 자산

- `scene_breakdown`
- `writer_template`
- scene-oriented validator 계열
- `tests/test_inplace_reliability.py`

즉, 완전 신설보다 `기존 scene 단위 자산을 활용한 patch 경로 구조화`가 기본 방향이다.

### 5.3 local vs global issue taxonomy

| 분류 | 예시 | 기본 라우팅 |
|---|---|---|
| local | 특정 엔딩 위치 오류, 특정 장면 누락, 대화 비율 보강, 후반 요약화 | `inplace` 우선 |
| boundary-local | 장면 전환 어색함, 직전/직후 장면 연결 흔들림 | `inplace` 가능, 단 boundary smoothing 포함 |
| global | 전역 톤 붕괴, pacing 전면 재배치, 장기 연속성, 구조 재배치 | 즉시 `partial/full` |

### 5.4 향후 내부 계약 후보

이번 initiative에서 runtime public API를 실제로 바꾸지는 않지만, 향후 내부 계약 후보는 문서상 명시한다.

- `block_id`
- `patch_scope`
- `boundary_context`
- `fallback_reason`
- `initial_verdict`
- `final_verdict`

## 6. sink 역할 고정

이번 initiative에서 logging/analytics는 아래 의미를 따르는 것을 기본안으로 둔다.

- `director_selections`: 초기 Director 선택/판정
- `episode_production`: round trace
- `stage_attempts`: 최종 stage attempt 결과
- `pass_rate_monitor`: 운영 모니터용 최종 집계

이 계약을 기준으로 나머지 문서와 운영 체크리스트를 정렬한다.

### 6.1 patch_trace 계약

Phase 4 이후 `episode_production.jsonl`은 `patch_trace`를 round trace의 최소 계측 필드로 포함한다.

- `patch_strategy`
- `patch_targets`
- `unchanged_ratio`
- `fallback_reason`
- `focus`
- `structural_attempted`

의도는 다음과 같다.

- `director_selections`는 초기 Director 판단을 저장한다.
- `stage_attempts`와 `pass_rate_monitor`는 최종 success/failure semantics를 저장한다.
- `episode_production`은 그 사이 lifecycle을 보존하며, 특히 `PASS_WITH_FIX -> patch -> PASS/REJECT`의 구조적 수정 경로를 `patch_trace`로 노출한다.

`patch_trace`는 full artifact snapshot의 대체재가 아니라, limited rerun과 full rerun에서 structural inplace가 실제로 작동했는지 판단하는 hard gate용 최소 계측이다.

## 7. phase 로드맵

아래 순서는 고정한다.

### Phase 1. 계약 고정

목표:
- `PASS_WITH_FIX` 의미, Stage 3/4 external contract, Stage 4 final semantics를 문서상 먼저 잠근다.

포함:
- Stage 3 external verdict 기본안
- Stage 4 final score/label/attempt 정합성 요구
- sink 역할 정의

비포함:
- structural inplace 구현 상세

선행조건:
- 기존 감사 결과 확정

성공 기준:
- 문서상 계약 충돌이 사라진다.
- `pass-with-fix-phase1-execution-spec.md`만 보고 구현자가 착수 가능하다.

ROI:
- 높음

리스크:
- 기존 soft-success 해석과 충돌 가능

rollback 관점:
- 문서 계약만 먼저 잠그므로 런타임 rollback 필요 없음

### Phase 2. 추가 컨텍스트 수집

목표:
- local/global issue 분류와 block-aware patch 적용 가능 범위를 고정한다.

포함:
- 실제 `PASS_WITH_FIX` 사례 재분류
- structural inplace 적용 가능/불가 사례 목록
- scene/block 경계 후보 점검

비포함:
- 코드 구현

선행조건:
- Phase 1 계약 고정

성공 기준:
- `inplace / partial / full` 라우팅 표가 decision-complete해진다.

ROI:
- 중상

리스크:
- 과도하게 세밀한 설계로 과잉 복잡화 위험

rollback 관점:
- 분류표만 조정 가능

### Phase 3. structural inplace 설계/구현

목표:
- whole-text inplace를 `block-aware patch` 방향으로 구조 개선한다.

포함:
- patch 경로만 구조화
- 문제 block 지정
- 원문 보존 정책
- boundary smoothing
- local/global 라우팅 규칙 반영

비포함:
- CW 일반 생성 경로 변경
- block-native 전체 생성 도입

선행조건:
- Phase 2 분류표

성공 기준:
- `부분 수정`이 실제로 `부분만 고치는 경로`가 된다.

ROI:
- 높음

리스크:
- block 경계에서 인공적 문체 노출 가능

rollback 관점:
- 기존 whole-text inplace로 되돌릴 수 있어야 한다.

### Phase 4. 최소 관측성 보강

목표:
- structural inplace를 디버그 가능한 수준으로만 계측한다.

포함:
- 수정 block id
- unchanged ratio
- boundary merge 결과
- fallback reason
- initial/final verdict linkage

비포함:
- full analytics overhaul

선행조건:
- Phase 3 설계 확정

성공 기준:
- structural inplace의 성공/실패 원인을 추적할 수 있다.
- `episode_production.patch_trace`와 `FailureAnalyzer.patch_trace_summary()`만으로 canary rerun의 go/no-go 판단이 가능하다.

ROI:
- 중상

리스크:
- full overhaul보다 단기 시야만 제공

rollback 관점:
- 최소 계측 필드 제거 가능

### Phase 5. 오프라인 회귀/골든 검증

목표:
- live 전, 의미 정합성과 structural inplace 품질을 오프라인으로 검증한다.

필수 시나리오:
- `PASS_WITH_FIX -> patch -> PASS`
- `PASS_WITH_FIX -> patch -> REJECT`
- local issue는 patch 유지
- global issue는 partial/full 우회
- unchanged block 보존
- boundary smoothing 실패 감지
- Stage 4 final score/label 정합성

성공 기준:
- live 없이도 핵심 semantics와 structural inplace 실패 모드가 재현 가능하다.

ROI:
- 높음

리스크:
- 골든 케이스가 live 복잡도를 완전히 대체하진 못함

rollback 관점:
- live 진입 전 중단 가능

### Phase 6. logging/analytics 체계 보완

목표:
- 최소 계측 위에 sink 의미와 downstream 집계를 정렬한다.

포함:
- final semantics 반영
- `PASS_WITH_FIX` 집계 기준 통일
- snapshot/원문 보존 정책 정리

성공 기준:
- 운영 문서와 DB 집계가 같은 의미를 사용한다.

ROI:
- 중상

리스크:
- 과거 지표와 비교 해석 비용 발생

rollback 관점:
- 신규 집계 필드는 분리 운용 가능해야 한다.

### Phase 7. limited rerun

목표:
- 작은 scope에서 계약, 계측, 구조 개선이 실제로 맞물리는지 확인한다.

포함:
- 새 project
- 실패 run 보존
- sink 계약 검증
- `patch_trace` hard gate 검증

선행조건:
- Phase 1~6 green

성공 기준:
- 결과 해석이 가능하고, initial/final verdict 의미가 혼동되지 않는다.
- local issue 기반 `PASS_WITH_FIX`가 발생했다면 `patch_strategy=inplace_patch_structural`이 최소 1회는 관측된다.
- `avg_unchanged_ratio >= 0.70`
- `fallback_reason` 중 `missing_patched_blocks`, `no_usable_patched_blocks`, `patched_output_too_short`는 0회이거나, 발생 시 문서상 명시적 사유와 승인 메모가 남는다.
- local issue rerun에서 `top_patch_targets`가 비어 있지 않다.

ROI:
- 높음

리스크:
- small-scope bias

rollback 관점:
- full rerun 진입 전 중단 가능

### Phase 8. full live rerun

목표:
- 운영 환경에서 end-to-end로 닫히는지 최종 확인한다.

성공 기준:
- draft count, audit tag, stage attempts, pass_rate_monitor, episode_production 해석이 일치한다.
- limited rerun에서 확인한 `patch_trace` 기준선이 full rerun에서도 유지되거나, 편차 사유가 운영 메모로 설명된다.
- `patch_trace_summary()`와 raw `episode_production.jsonl`이 서로 모순되지 않는다.

ROI:
- 최종 검증

리스크:
- behavior change의 실제 상호작용

rollback 관점:
- limited rerun 결과 기준으로 go/no-go 결정

## 8. Validation / Acceptance

이 initiative의 문서 완료 기준은 아래다.

1. `CW 일반 글쓰기 구조는 직접 변경 대상이 아님`이 명시돼 있다.
2. `inplace 구조 개선은 가능하며 핵심 ROI 축`이 명시돼 있다.
3. `PASS_WITH_FIX`, `Stage 3/4`, `logging`, `analytics`, `rerun`이 모두 포함돼 있다.
4. `local/global issue taxonomy`와 `rollback`, `limited rerun -> full rerun` 게이트가 포함돼 있다.
5. 다른 구현자가 추가 의사결정 없이 phase별로 착수 가능하다.

## 9. 문서 관계

- 감사 문서: 증거와 현재 상태 판정
- 상세 실행 메모: phase별 상세 실행 항목
- rerun 체크리스트: Phase 7~8 운영 검증

이 문서는 위 세 문서의 상위 문서이며, 용어와 phase 기준은 이 문서를 따른다.

## 10. 기본 가정

- 이번 작업은 문서화만 수행한다.
- 문서는 한국어로 작성한다.
- `CW 본체 개선`은 비대상이다.
- `inplace 수정 경로 구조 개선`은 핵심 대상이다.
- structural inplace는 behavior change지만, 그 전에 `계약 고정`과 `최소 계측`을 선행한다.
