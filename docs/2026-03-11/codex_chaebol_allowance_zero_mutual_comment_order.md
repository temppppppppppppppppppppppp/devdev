# chaebol_allowance_zero 상호 코멘트 오더

> 작성일: 2026-03-11
> 목적: `실패본 vs 재시도본 비교 문서` 2개를 서로 교차 검토해, 반박이 아니라 **통합 품질 향상용 코멘트**를 만든다.
> 주의: 이번 작업은 **상대 문서 코멘트 전용**이다. 원문 수정, 새 비교 작성, 새 생성은 하지 않는다.

---

## 1. 작업 목적

이번 오더의 목적은 `Codex 비교 문서`와 `Opus 비교 문서`를 서로 읽고,
누가 이기느냐가 아니라 아래 3가지를 분리해서 정리하는 것이다.

1. **상대 문서에서 그대로 채택해도 되는 강점**
2. **맞지만 더 보강하면 좋은 부분**
3. **사실오류, 과장, 누락처럼 실제 수정이 필요한 부분**

즉, 상대 문서를 공격하거나 다시 쓰는 게 아니라,
**최종 통합 문서에 어떤 항목을 채택/보류/수정할지 결정하기 위한 코멘트 문서**를 만든다.

---

## 2. 필수 입력 파일

### 2.1 공통 기준 문서

먼저 아래 문서를 UTF-8로 읽는다.

1. `docs/blockguide/SSOT_blockguide-integrated-order.md`
2. `docs/blockguide/treatment-production-harness-v2.md`
3. `docs/blockguide/bi-production-harness-v1.md`

### 2.2 기획 기준 문서

4. `docs/2026-03-10/opus_재벌3세인데용돈이0원.md`
5. `treatments/chaebol_allowance_zero_phase0_design.json`

### 2.3 원본 비교 대상

- `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- `treatments/chaebol_allowance_zero_tr_block_070_draft.json`
- `bible/02_bi_chaebol_allowance_zero.json`
- `bible/0_bi_chaebol_allowance_zero.json`

### 2.4 비교 문서 2개

- Codex 문서: `docs/2026-03-11/codex_chaebol_allowance_zero_failed_vs_retry_comparison.md`
- Opus 문서: `docs/2026-03-11/opus_chaebol_allowance_zero_failed_vs_retry_comparison.md`

### 2.5 참고 감리 문서

아래는 참고용이다. 직접 원본 파일 검증이 우선이다.

- `treatments/audit_reports/chaebol_allowance_zero_full_retry_vs_failed_audit.md`
- `bible/audit_reports/chaebol_allowance_zero_bi_retry_vs_failed.md`
- `bible/audit_reports/chaebol_allowance_zero_bi_5pass.md`

---

## 3. 작업 범위

이번 오더에서 해야 할 일:

1. 상대 비교 문서의 주장과 수치가 원본 파일 기준으로 맞는지 확인
2. 상대 문서의 장점, 보강점, 수정점, 보류 쟁점을 분리
3. 최종 통합 문서에 **채택 가능한 항목**을 따로 뽑기

이번 오더에서 하지 말 일:

- 상대 문서 직접 수정
- 자기 문서 방어문 작성
- 새 비교 문서 재작성
- 새 TR/BI 생성
- 기존 JSON 수정
- 하네스 수정

즉, **상호 코멘트만 한다.**

---

## 4. 코멘트 원칙

### 4.1 기본 태도

- 목표는 반박이 아니라 **통합 품질 향상**이다.
- 상대 문서가 맞는 부분은 분명히 인정한다.
- 취향 차이와 사실오류를 섞지 않는다.
- 수치와 원문 검증이 가능한 지적만 한다.
- "이 문장은 별로다" 같은 감상평은 금지한다.

### 4.2 구분 규칙

- `Agree`: 그대로 채택 가능
- `Strengthen`: 방향은 맞지만 근거/수치/명시를 더 넣어야 함
- `Correct`: 사실오류, 과장, 누락, 판정 과속
- `Open Issues`: 원본 파일만으로 단정 어려운 보류 쟁점

### 4.3 금지

- 상대 문서를 조롱하거나 논쟁적으로 쓰기
- "내 문서가 더 낫다" 식 비교
- 원본 파일 재검증 없이 상대 주장만 반박
- 최종 통합에서 쓸 수 없는 저신호 코멘트 남발

---

## 5. 필수 점검 항목

상대 문서를 코멘트할 때 아래는 반드시 본다.

### 5.1 TR 관련

- `opponent_unique`
- `weakness_unique`
- `deal_unique`
- `method_unique`
- `avg_bundle_chars`
- 초반 10블록 2인 로테이션 여부
- weakness 반복 진술 여부
- solution 골격 반복 여부
- `validate_treatment_structure`
- 70블록 완성 여부
- `business_sector` / `section_rotation` 기준으로 `sector missing` 재판정이 맞는지

### 5.2 BI 관련

- `plot_roadmap_len`
- title sequence 정합성
- source TR과 roadmap hash 정합성
- `FinanceHUD.portfolio_history` ↔ source TR 자본 곡선 동기화
- 최종 자산
- 5-pass 결과
- 실패 BI와 재시도 BI가 각각 자기 source TR과는 정합적인지
- `BI quality`와 `source TR quality`를 상대 문서가 제대로 분리했는지

### 5.3 최종 판정 관련

- `대체 가능 / 부분 개선 / 대체 불가` 판정이 과하거나 약하지 않은지
- 판정 근거가 수치와 구조 차이에 충분히 묶여 있는지
- "같은 기획안 기준 비교"라는 전제가 문서 안에서 충분히 잠겼는지

---

## 6. 출력 형식

출력은 아래 순서를 정확히 따른다.

1. **Agree**
2. **Strengthen**
3. **Correct**
4. **Open Issues**
5. **Integration Picks**

세부 규칙:

- 각 항목은 짧은 완전문장으로 쓴다.
- 가능하면 파일/수치/근거를 붙인다.
- `Correct`는 사실오류만 적는다.
- `Strengthen`은 추가하면 좋은 근거만 적는다.
- `Integration Picks`는 최종 통합 문서에 반영할 문장 또는 판단만 추린다.

---

## 7. 결과 파일명 규칙

결과 문서는 **자기 모델명이 앞**, **상대 모델명이 뒤**로 간다.

예시:

- Codex가 Opus 문서에 다는 코멘트:
  - `docs/2026-03-11/codex_comment_on_opus_chaebol_allowance_zero_failed_vs_retry_comparison.md`
- Opus가 Codex 문서에 다는 코멘트:
  - `docs/2026-03-11/opus_comment_on_codex_chaebol_allowance_zero_failed_vs_retry_comparison.md`

원문 비교 문서는 그대로 둔다.

---

## 8. 최종 요구 문장

아래 요구를 그대로 따른다.

```text
상대 모델의 chaebol_allowance_zero 실패본 vs 재시도본 비교 문서를 읽고,
원본 JSON과 기획 기준 문서로 직접 재검증한 뒤 상호 코멘트 문서를 작성하라.
목표는 반박이 아니라 최종 통합 품질 향상이다.
원문은 수정하지 말고, Agree / Strengthen / Correct / Open Issues / Integration Picks 형식으로만 정리하라.
새 생성이나 재비교는 하지 말고, 상대 문서에 대한 코멘트만 수행하라.
```
