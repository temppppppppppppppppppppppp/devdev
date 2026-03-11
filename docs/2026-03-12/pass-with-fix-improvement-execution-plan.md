# PASS_WITH_FIX 상세 실행 메모

작성일: 2026-03-12  
상위 마스터 문서: `docs/2026-03-12/pass-with-fix-master-roadmap.md`  
기준 감사 문서: `docs/2026-03-12/pass-with-fix-partial-fix-3pass-audit.md`  
문서 역할: 마스터 로드맵의 phase를 실제 구현·검증 항목으로 풀어 쓴 하위 실행 메모

## 문서 상태

- 이 문서는 최상위 SSOT가 아니다.
- phase 순서, 용어, 비대상 범위는 `pass-with-fix-master-roadmap.md`를 따른다.
- 특히 `CW 일반 글쓰기 생성 구조는 직접 변경 대상이 아님`이라는 원칙을 전제로 읽는다.

## 0. 실행 결론

현재 우선순위는 아래 순서가 맞다.

1. `P0 Correctness`
2. `P1 Observability`
3. `P2-A Structural Inplace`
4. `P2-B Logging / Analytics Hardening`
5. `live rerun`

이 순서를 뒤집으면 안 된다.

이유:

- 지금 가장 큰 문제는 "부분 수정 기능 부재"가 아니라 `최종 의미 불일치`다
- 먼저 `최종 verdict/score/log semantics`를 잠가야 rerun 결과를 해석할 수 있다
- 그 다음에야 원문 snapshot, 분석 지표, 운영 체크리스트를 안정적으로 붙일 수 있다
- behavior-changing 실험은 마지막이 아니라, `계약 고정` 이후에도 `최소 계측`과 `오프라인 검증`을 앞세워 제한적으로 진행해야 한다

## 1. 목표 상태

개선 완료 후 `PASS_WITH_FIX`는 아래 상태를 만족해야 한다.

### 1.1 기능 목표

- `PASS_WITH_FIX`는 `부분 수정 필요`라는 Director 판단으로만 사용된다
- `fix_scope=inplace`면 국소 patch를 수행한다
- patch 후 재심사 `PASS`가 나오면 최종 verdict와 최종 score가 함께 갱신된다
- patch 실패 또는 소진 시 최종 verdict는 명확히 `REJECT` 또는 retry route로 닫힌다

### 1.2 관측 목표

- 같은 시도에 대해 어떤 sink가 `초기 Director 판단`을 저장하는지, 어떤 sink가 `최종 결과`를 저장하는지 계약이 문서화된다
- 운영자가 `director_selections`, `episode_production`, `stage_attempts`, `pass_rate_monitor`를 혼동하지 않는다
- downstream analytics가 `PASS_WITH_FIX`를 pass-like soft success로 볼지, transient state로 볼지 하나로 통일된다

### 1.3 운영 목표

- live rerun 후 결과 해석이 가능하다
- `PASS_WITH_FIX -> patch -> PASS`와 `PASS_WITH_FIX -> REJECT`가 로그/DB/요약 리포트에서 같은 의미로 추적된다

## 2. 작업 범위

이번 실행 계획의 직접 범위:

- Stage 3 `PASS_WITH_FIX` 외부 계약
- Stage 4 final verdict / final score / final labels 정합성
- logging sink 역할 분리
- analytics / DB query 의미 통일
- 회귀 테스트 보강
- live rerun gate 정의

직접 범위 밖:

- 전면적인 prompt 재설계
- context compression 아키텍처 재작성
- hybrid profile, fanout 전략, firewall routing 같은 behavior change 실험

이들은 `P2` 또는 별도 작업으로 분리한다.

## 3. P0 Correctness

### P0-1. Stage 4 최종 score/label semantics 정합화

문제:

- `PASS_WITH_FIX -> patch -> PASS` 후에도 Stage 4는 최초 score를 최종 score처럼 저장할 가능성이 있다

실행 목표:

- Stage 4 최종 `PASS`는 재심사 score를 최종 state/labels/attempt 기록에 반영해야 한다

완료 기준:

- `director_score`
- `_director_quality_labels.score`
- `stage_attempts.score`
  가 모두 최종 재심사 score와 일치

필수 검증:

- unit test: `PASS_WITH_FIX -> PASS`에서 final score가 재심사 score인지 확인
- unit test: initial score와 re-audit score가 다를 때 stale score가 남지 않는지 확인

우선순위:

- `최우선`

### P0-2. Stage 3 외부 계약 정리

문제:

- Stage 3는 아직 `PASS_WITH_FIX`를 외부 success verdict로 내보낸다

실행 목표:

- Stage 3에서 `PASS_WITH_FIX`가 외부로 노출되는 것이 설계인지, 아니면 반드시 `PASS/REJECT`로 붕괴해야 하는지 SSOT를 확정
- 확정된 계약에 맞게 orchestrator, tests, docs를 정렬

선택지:

- `안 A`: Stage 3도 transient-only 모델 채택
- `안 B`: Stage 3는 soft success 허용, 대신 docs/analytics를 그 의미로 통일

권고:

- 현재 감사 결론 기준으로는 `안 A`가 더 정합적이다

이유:

- Stage 2/4와 해석이 맞아진다
- downstream 혼란이 줄어든다
- "부분 수정은 내부 수렴 루프"라는 개념이 더 명확해진다

완료 기준:

- 문서 SSOT 1개로 수렴
- Stage 3 orchestrator와 tests가 그 계약을 반영

### P0-3. PASS_WITH_FIX SSOT 문서 통합

문제:

- `verdict-logic-spec.md`와 `stage_map/*`가 서로 다른 의미를 말한다

실행 목표:

- `PASS_WITH_FIX`의 정의를 한 문서 세트에서 하나로 통일

최소 통일 항목:

- transient state인지 여부
- QualityGate 적용 시점
- final verdict 노출 가능 여부
- analytics 집계 기준
- logging sink 의미

완료 기준:

- 기존 상충 문서에 수정 또는 deprecate 표시
- stage_map, spec, gotchas가 같은 의미를 사용

## 4. P1 Observability

### P1-1. logging sink 역할 분리 문서화

문제:

- 현재 `director_selections` / `episode_production`은 초기 판단, `stage_attempts` / `pass_rate_monitor`는 최종 결과를 주로 담는다
- 그런데 이 계약이 코드에는 암묵적이고 운영 문서에 고정돼 있지 않다

실행 목표:

- 각 sink의 의미를 명시한다

권장 계약:

- `director_selections`: Director 최초 선택/판정 기록
- `episode_production.jsonl`: round 단위 생산 기록
- `stage_attempts`: stage attempt 최종 결과 기록
- `pass_rate_monitor.json`: 운영용 최종 success/failure 모니터링

완료 기준:

- 문서에 sink별 의미 명시
- live rerun 체크리스트가 그 기준을 사용

### P1-2. Stage 4 finalization observability 보강

문제:

- 현재는 "초기 PWF"와 "최종 PASS/REJECT"가 연결 추적은 가능하지만 읽기 쉽지 않다

실행 목표:

- 운영자가 한 시도의 lifecycle을 한 번에 읽을 수 있어야 한다

권장 개선 항목:

- finalization flag 또는 final verdict field 추가
- `episode_production`에 `initial_verdict` / `final_verdict` 구분 저장
- 또는 `stage_attempts`와 연결되는 stable attempt key 명시

이 항목은 correctness보다는 observability이므로 `P1`로 둔다.

### P1-3. artifact snapshot backlog 정의

문제:

- `REJECT/PASS_WITH_FIX before patch/patched_after_fix` 원문 snapshot 보존이 아직 약하다

실행 목표:

- 원문 보존이 필요한 최소 지점을 backlog로 고정

최소 후보:

- Stage 3 `PASS_WITH_FIX before patch`
- Stage 3 `patched_after_fix`
- Stage 4 `PASS_WITH_FIX before patch`
- Stage 4 `patched_after_fix`
- 최종 `REJECT` manuscript / blueprint

주의:

- 이 항목은 ROI는 높지만 즉시 P0는 아니다

## 5. P2 Behavior Change

이 묶음은 correctness fix와 분리해야 한다.

이유:

- behavior가 바뀌면 rerun 결과 해석이 어려워진다
- correctness 문제를 덮어버릴 수 있다

### P2 후보

- firewall REJECT patch routing
- reduced fanout retry
- continuity pin guard 추가 조정
- hybrid profile 또는 strategy routing 실험
- context trim 정책 강화

실행 원칙:

- feature flag 뒤에서 검증
- shadow run 또는 limited rerun으로만 확인
- P0/P1 green 후 착수

## 6. 실행 순서

### Phase 1. 계약 고정

작업:

- `PASS_WITH_FIX` 정의 확정
- Stage 3 외부 계약 확정
- sink 역할 정의

산출물:

- SSOT 업데이트 문서
- 개선 설계 메모

Gate:

- 문서 상충 없음

### Phase 2. correctness 수정

작업:

- Stage 4 final score/label semantics 수정
- 필요 시 Stage 3 verdict 붕괴 규칙 수정

산출물:

- 코드 수정
- 회귀 테스트 추가

Gate:

- 기존 관련 테스트 green
- 신규 의미 정합성 테스트 green

### Phase 3. observability 보강

작업:

- sink 역할 분리 반영
- finalization 추적 필드 또는 연결성 강화
- snapshot backlog 최소 구현 또는 명시적 defer

Gate:

- 운영자가 1회 시도 lifecycle을 문서만 보고 해석 가능

### Phase 4. live rerun

작업:

- 기존 체크리스트로 rerun 수행
- `00_test_03` 유형의 `PASS_WITH_FIX` 사례를 우선 점검

필수 확인:

- initial vs final verdict 혼동이 사라졌는지
- final score가 재심사 score와 맞는지
- shrink guard가 실제 rerun에서도 정상 작동하는지

### Phase 5. behavior change 실험

작업:

- P2 후보를 flag 뒤에서 단계적으로 검증

Gate:

- P0/P1 안정화 완료
- rerun 결과 해석 가능

## 7. 필수 테스트 추가 목록

최소 추가 대상:

- Stage 4 `PASS_WITH_FIX -> patch -> PASS` 시 final score 갱신
- Stage 4 `PASS_WITH_FIX -> patch -> PASS` 시 `_director_quality_labels.score` 갱신
- Stage 4 `PASS_WITH_FIX -> patch -> PASS` 시 `stage_attempts.score` 갱신
- Stage 4 `episode_production`과 `stage_attempts`가 의도적으로 다른 의미를 쓸 경우 그 계약을 명시적으로 검증
- Stage 3 `PASS_WITH_FIX` 외부 노출 계약 검증
- failure analyzer / db query가 확정 계약과 같은 의미를 집계하는지 검증

권장 추가:

- live rerun fixture 또는 golden artifact 비교
- `00_test_03` 유형의 shrink failure 재현 회귀

## 8. live rerun 전 Hard Gate

아래가 충족되기 전에는 rerun을 미루는 편이 맞다.

- `PASS_WITH_FIX` SSOT가 문서 1세트에서 정리됨
- Stage 4 final score semantics 수정 완료
- 관련 회귀 테스트 green
- 운영자가 sink별 의미를 헷갈리지 않도록 체크리스트/문서가 갱신됨

예외:

- source-level semantics 검증만 목적인 limited rerun은 가능
- 다만 그 경우도 "현재 로그는 초기/최종 verdict가 분리돼 보일 수 있음"을 명시해야 한다

## 9. 최종 권고

지금 바로 해야 할 것은 새로운 behavior 실험이 아니다.

먼저 해야 할 일:

1. `PASS_WITH_FIX` 정의를 하나로 고정
2. Stage 4 final score/label semantics 수정
3. Stage 3 외부 계약 정리
4. logging/analytics 의미 정렬
5. 그 다음 live rerun

가장 피해야 할 순서:

1. hybrid/profile/fanout 같은 behavior change부터 넣기
2. rerun 결과가 좋아 보이는지로 correctness를 대신 판단하기

이 문서는 실행 계획 문서이며, 코드 수정은 포함하지 않는다.
