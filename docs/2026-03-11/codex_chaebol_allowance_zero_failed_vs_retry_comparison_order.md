# chaebol_allowance_zero 실패본 vs 재시도본 비교 오더

> 작성일: 2026-03-11
> 목적: 같은 기획안 기준에서 `실패본`과 `재시도본`의 차이를 비교한다.
> 주의: 이번 작업은 **비교/판정 전용**이다. 새 생성이나 수정이 아니라, 이미 만들어진 결과물을 읽고 비교한다.

---

## 1. 작업 목적

`chaebol_allowance_zero`는 같은 기획안에서 한 번 실패했고, 하네스 보강 후 다시 생성되었다.

이번 오더의 목적은 아래 2가지를 분리해서 판정하는 것이다.

1. **같은 기획안인데 결과물이 실제로 달라졌는가**
2. **달라졌다면 실패본보다 재시도본이 구조적으로 우월한가**

즉, "재생성했다"는 사실이 아니라 **비교 가능한 개선이 있었는지**를 검토한다.

---

## 2. 필수 입력 파일

### 2.1 공통 기준 문서

먼저 아래 문서를 UTF-8로 읽는다.

1. `docs/blockguide/SSOT_blockguide-integrated-order.md`
2. `docs/blockguide/treatment-production-harness-v2.md`
3. `docs/blockguide/bi-production-harness-v1.md`

### 2.2 동일 기획안 기준 문서

4. `docs/2026-03-10/opus_재벌3세인데용돈이0원.md`
5. `treatments/chaebol_allowance_zero_phase0_design.json`

### 2.3 비교 대상 파일

TR 비교:

- 실패본: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- 재시도본: `treatments/chaebol_allowance_zero_tr_block_070_draft.json`

BI 비교:

- 실패본: `bible/02_bi_chaebol_allowance_zero.json`
- 재시도본: `bible/0_bi_chaebol_allowance_zero.json`

### 2.4 참고 감리 문서

아래 문서는 참고용이다. 그대로 반복하지 말고, 직접 파일을 읽은 뒤 맞는지 확인한다.

- `treatments/audit_reports/chaebol_allowance_zero_full_retry_vs_failed_audit.md`
- `bible/audit_reports/chaebol_allowance_zero_bi_5pass.md`
- `bible/audit_reports/chaebol_allowance_zero_bi_retry_vs_failed.md`

---

## 3. 작업 범위

이번 오더에서 해야 할 일:

1. 실패본과 재시도본이 **같은 기획안**에서 나왔는지 확인
2. TR 실패본 vs TR 재시도본 비교
3. BI 실패본 vs BI 재시도본 비교
4. 재시도본이 실패본을 **실질적으로 대체할 수준인지** 최종 판정
5. 남아 있는 리스크가 있다면 따로 지적

이번 오더에서 하지 말 일:

- 새 TR 생성
- 새 BI 생성
- 기존 JSON 수정
- 기획안 수정
- 하네스 수정

즉, **분석과 비교만 한다.**

---

## 4. 필수 비교 항목

### 4.1 TR 비교 항목

아래 항목은 반드시 수치나 명시적 판정으로 비교한다.

- `opponent_unique`
- `weakness_unique`
- `deal_unique`
- `method_unique`
- `avg_bundle_chars`
- 상위 opponent 반복도
- 상위 weakness 반복도
- `validate_treatment_structure` 통과 여부
- `70블록 완성 여부`
- `UTF-8 오염 여부`

추가로 아래 서술형 비교도 반드시 한다.

- 초반 10블록이 실패본처럼 2인 로테이션으로 수렴하는지 여부
- 약점 문장이 섹터 단위 복붙인지 여부
- `solution`이 같은 골격 문장을 반복하는지 여부
- 자본 곡선이 단순 상승만 반복하는지 여부
- 재시도본이 실제로 원고 작성 가이드 역할을 할 정도의 밀도를 갖는지 여부

### 4.2 BI 비교 항목

아래 항목은 반드시 비교한다.

- `plot_roadmap_len`
- `plot_roadmap` title sequence 정합성
- `plot_roadmap`가 source TR과 hash 수준으로 동기화되는지 여부
- `FinanceHUD.portfolio_history`가 source TR 자본 곡선을 따르는지 여부
- 최종 자산 수치
- `audit_bi_5pass` PASS 여부
- `UTF-8 오염 여부`

추가로 아래 판정도 반드시 포함한다.

- 실패 BI가 실패 TR의 반복 구조를 그대로 운반했는지 여부
- 재시도 BI가 새 TR 구조를 제대로 운반했는지 여부
- 구조만 맞는 BI인지, 실제 source TR 품질 개선이 반영된 BI인지 여부

---

## 5. 출력 형식

출력은 아래 순서를 따른다.

1. **Findings**
2. **TR Comparison**
3. **BI Comparison**
4. **Final Verdict**

세부 규칙:

- Findings가 있으면 심각도 순으로 먼저 쓴다.
- Findings가 없으면 `심각한 비교상 결함 없음`이라고 명시한다.
- 비교는 감상평이 아니라 **수치 + 구조 판정** 중심으로 쓴다.
- "좋아졌다" 같은 표현만 쓰지 말고, 무엇이 얼마나 달라졌는지 적는다.
- 기존 감리 문서와 다르게 보이는 부분이 있으면 그 차이를 명시한다.

---

## 6. 최종 판정 기준

아래 조건을 대부분 만족하면 `재시도본이 실패본을 대체한다`고 판정한다.

- 같은 기획안 / 같은 제목축 / 같은 주인공축이 유지된다.
- TR에서 opponent/weakness 반복 구조가 명확히 개선된다.
- TR 평균 밀도가 실패본보다 유의미하게 높다.
- TR이 70블록 구조를 정상 완주한다.
- BI가 새 TR을 그대로 운반한다.
- BI 5-pass가 통과한다.
- UTF-8 오염이 없다.

아래 상황이면 `부분 개선` 또는 `대체 불가`로 낮춰 판정한다.

- TR은 개선됐지만 BI가 stale copy다.
- TR은 70블록이지만 반복 구조가 후반에 다시 붕괴한다.
- BI가 구조는 맞지만 source TR 개선이 반영되지 않았다.

---

## 7. 결과 문서 파일명 규칙

비교 결과를 문서로 남길 경우, 파일명 앞에 **모델명을 접두사로 붙인다.**

예시:

- Codex: `docs/2026-03-11/codex_chaebol_allowance_zero_failed_vs_retry_comparison.md`
- Opus: `docs/2026-03-11/opus_chaebol_allowance_zero_failed_vs_retry_comparison.md`

같은 오더를 두 모델에 동시에 줄 수 있도록, **오더 본문은 공통**으로 쓰고 **결과 파일명만 분리**한다.

---

## 8. 최종 요구 문장

아래 요구를 그대로 따른다.

```text
같은 기획안 기준에서 chaebol_allowance_zero 실패본과 재시도본을 비교하라.
TR과 BI를 분리해서 비교하고, 수치와 구조 판정으로 개선 여부를 설명하라.
기존 감리 문서를 참고할 수는 있지만 그대로 반복하지 말고 직접 파일을 읽어 검증하라.
새 생성이나 수정은 하지 말고 비교와 최종 판정만 수행하라.
```
