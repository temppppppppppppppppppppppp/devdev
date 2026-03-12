# Blockguide 실패 TR 보강 설계 문서

> 작성일: 2026-03-11
> 목적: `chaebol_allowance_zero` 실패 샘플을 기준으로, 추후 본 SSOT에 반영할 보강안을 결정 완료 상태로 문서화
> 원칙: 이번 문서는 설계만 고정한다. 본 SSOT 본문은 다음 단계에서 수정한다.

---

## 1. Summary

- 보강 대상은 [SSOT_blockguide-integrated-order.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/SSOT_blockguide-integrated-order.md), [treatment-production-harness-v2.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/treatment-production-harness-v2.md), [bi-production-harness-v1.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md)다.
- `treatment-planning-harness.md`는 이번 실패 기준 직접 수정 대상이 아니다.
- 목표는 새 규칙을 무작정 늘리는 것이 아니라, 이미 있는 반복 금지 규칙을 `실패작 triage -> 감리 수치 -> handoff gate`까지 연결하는 것이다.

---

## 2. Integrated Order 보강안

### 2.1 새 모드 추가

[SSOT_blockguide-integrated-order.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/SSOT_blockguide-integrated-order.md)에 `Failure Triage` 모드를 추가한다.

트리거:

- 사용자가 `실패작`, `감리 FAIL`, `평가 메모`, `못 씀`, `왜 이런가`, `하네스 보강` 계열 요청을 주는 경우
- 특정 TR/BI 파일과 함께 구조적 실패 메모를 붙여 주는 경우

핵심 규칙:

- 일반 production auto-run으로 들어가지 않는다.
- 먼저 triage 루프로 들어간다.

### 2.2 Triage 순서 고정

순서를 아래 6단계로 고정한다.

1. 실패 샘플 원본 읽기
2. 현재 운용본 대조
3. relevant harness 재오픈
4. 실패 유형 분류
5. 문서화
6. 3-pass 감리

### 2.3 실패 유형 분류값 고정

- `routing_gap`
- `schema_or_field_drift`
- `production_density_failure`
- `handoff_false_pass`

운영 규칙:

- 실패 분석 문서에는 최소 1개 이상 분류를 붙인다.
- 2개 이상이 동시에 걸리면 주원인과 부원인을 분리한다.

---

## 3. TR Production Harness 보강안

### 3.1 현재 문제 정의

[treatment-production-harness-v2.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/treatment-production-harness-v2.md)에는 반복 금지 규칙이 이미 많다.
하지만 이번 실패 샘플은 그 규칙을 위반하고도 `감리 출력의 핵심 수치`가 부족해 사람 눈으로만 실패를 판정하는 상태다.

따라서 보강 방향은 `프롬프트 규칙 추가`보다 `감리 출력 의무 수치 승격`이다.

### 3.2 새 감리 출력 항목

Phase 4 감리와 출고 게이트에 아래 수치를 필수 출력으로 추가한다.

- `opponent_unique`
- `top_opponent_repetition`
- `top_opponent_weakness_pair_repetition`
- `window_10_opponent_unique_counts`
- `avg_context`
- `avg_event_villain`
- `avg_solution`
- `avg_reward`
- `avg_stakes`
- `avg_bundle_chars`
- `business_sector_missing`
- `section_rotation_missing`

### 3.3 새 FAIL 규칙

아래 판정은 명시적 FAIL로 승격한다.

- `avg_bundle_chars < 350` -> `skeleton draft`
- 동일 `weakness_exploited` 3회 이상 -> FAIL
- 동일 `opponent + weakness` 조합 4회 이상 -> FAIL
- 연속된 2개 이상의 10블록 구간이 사실상 동일한 2인 opponent 로테이션 -> FAIL
- `business_sector`와 `section_rotation`가 둘 다 있으면 `sector missing`으로 판정하지 않음

### 3.4 필드 계약 보강

용어 계약을 문서에 명시한다.

- `business_sector` = sector 의미의 정식 호환 필드
- `section_rotation` = sector progression 보조 필드

의도:

- 이후 감리자가 `sector`라는 이름만 찾다가 false FAIL을 내지 않게 한다.

### 3.5 감리 예시 출력 보강

3-pass 감리 예시 섹션에 아래처럼 실제 수치가 찍히는 샘플을 넣는다.

```text
- opponent_unique: 4
- top_opponent_repetition: 29
- top_opponent_weakness_pair_repetition: 5
- window_10_opponent_unique_counts: [2, 2, 2, 2, 2, 2, 3]
- avg_bundle_chars: 321.29
- business_sector_missing: 0
- section_rotation_missing: 0
- verdict: skeleton draft / repetition FAIL
```

이 예시는 `chaebol_allowance_zero` 실패 패턴 설명용으로만 두고, 실제 golden sample 예시와는 분리한다.

---

## 4. BI Production Harness 보강안

### 4.1 handoff 전제 강화

[bi-production-harness-v1.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md)의 `TR 감리 통과 상태` 문장을 더 명시적으로 바꾼다.

새 전제:

- BI handoff 전에는 source TR이 `density/audit PASS`여야 한다.
- 구조 정합성만 맞는 TR은 handoff 자격이 없다.

### 4.2 BI 감리 보고서 재인용 의무

BI 감리 보고서에 아래 source TR 항목을 재인용하도록 고정한다.

- `production_density_gate`
- `avg_bundle_chars` 또는 `avg_chars`
- `deal_top_repetition`
- `method_top_repetition`
- `opponent_unique` 또는 이에 준하는 opponent diversity metric

### 4.3 새 PASS 차단 규칙

아래 상황이면 BI는 구조가 맞아도 PASS가 불가하다.

- source TR가 `skeleton draft`
- source TR가 반복 FAIL
- source TR가 density FAIL

판정 문구도 고정한다.

- `bi_structure_ok_but_source_tr_failed = true`
- `final_verdict = FAIL`

의도:

- `chaebol_allowance_zero_bi_5pass_audit.md` 같은 문서가 구조 정합성만 보고 PASS처럼 보이는 문제를 차단한다.

---

## 5. 반영 우선순위

1. integrated-order에 `Failure Triage` 오더 추가
2. treatment-production에 감리 수치와 FAIL 규칙 승격
3. bi-production에 source TR gate 추가

이 순서를 유지해야 하는 이유:

- 오더가 없으면 실패작 요청이 다시 일반 production 루프로 들어갈 수 있다.
- TR 감리 수치가 없으면 BI gate가 참조할 근거가 약하다.
- BI gate는 마지막 연결부라 앞의 두 단계가 먼저 고정돼야 한다.

---

## 6. 비대상 판정

- `treatment-planning-harness.md`는 이번 실패의 직접 수정 대상이 아니다.
- JSON 스키마 변경, 기존 실패 JSON 수정, 기존 BI/TR 재생성은 이번 문서 범위 밖이다.
- 이번 문서는 `나중에 SSOT 본문에 반영할 변경안`만 결정 완료 상태로 기록한다.
