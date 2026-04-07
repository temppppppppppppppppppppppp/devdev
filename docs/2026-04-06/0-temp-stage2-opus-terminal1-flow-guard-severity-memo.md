# 0 Temp Stage2 Opus Terminal 1 — Flow Guard Severity Memo

Date: 2026-04-06
Status: final
Mode: read-only follow-up memo
Scope: `Flow Guard` / `beat_sequence` severity mismatch classification
Parent Order: `docs/2026-04-06/0-temp-stage2-opus-followup-parallel-order.md` Terminal 1
Canonical Path: `docs/2026-04-06/0-temp-stage2-opus-terminal1-flow-guard-severity-memo.md`
Confidence: `96%`

## Verdict

- classification: **severity inflation** (not false positive, not false data fabrication)
- owner: **bounded** to `stage2_validation_pipeline.py` + Stage2 field policy
- new lane: **no**
- routing: fold into existing `0_0-stage2-contract-normalization-remediation-execution-ssot.md`

## Q1. severity inflation인가, false positive인가?

**severity inflation이 맞다.**

증거 삼각 검증:

| 증거 원천 | 위치 | 내용 |
|---|---|---|
| 런타임 로그 | `0_temp.txt:535` | Flow Guard가 `서사 폭주 위험: 비트 수가 화수보다 부족` 감지 — 메타데이터 부족 자체는 실재 |
| Director 판단 | `0_temp.txt:542-543` | "Python CRITICAL이지만, 전술서에 5화 서사 구조가 이미 있으므로 기각" — semantic 판단 정확 |
| advisory sink | `stage2_validation_pipeline.py:609` | 모든 Flow Guard REJECT를 `severity: "CRITICAL"` 고정 매핑 |

`beat_sequence` 메타데이터가 빈 건 사실이었다. Python 감지는 정확했다. 그러나 `tactical_doc` 본문에 이미 동등한 서사 구조가 있을 때, 메타데이터 공백을 CRITICAL로 올리는 건 과도하다.

### 추가 발견: flat severity 구조

Flow Guard만의 문제가 아니다. `stage2_validation_pipeline.py` 전체에서 **모든 advisory source가 `severity: "CRITICAL"` 고정**이다:

| source | line | severity |
|---|---|---|
| consensus | 397 | CRITICAL |
| flow_guard | 609 | CRITICAL |
| duplicate_guard | 628 | CRITICAL |
| draft_validator | 765 | CRITICAL |
| arc_corrector_uncorrectable | 796 | CRITICAL |
| arc_corrector_fail | 818 | CRITICAL |
| arc_corrector_revalidation | 858 | CRITICAL |
| arc_corrector_error | 872 | CRITICAL |
| continuity_inspector | 1036 | CRITICAL |

Advisory 파이프라인 자체에 severity 분화가 없는 flat 구조. Flow Guard severity mismatch는 이 전체 flat 구조의 한 증상이다.

## Q2. owner가 Stage2 validation + Stage2 field policy로 bounded 되는가?

**Yes.** broader hidden owner 없다.

- **Primary owner**: `modules/core/stage2_validation_pipeline.py` line 606-612 (advisory sink의 고정 CRITICAL 매핑)
- **Secondary owner**: Stage2 contract policy — `beat_sequence`의 keep-or-drop이 미결
  - SSOT line 188: `beat_sequence` 명시적 keep-or-drop 대상
  - SSOT line 219: 완료 조건에 포함
- **Not owner**: Director (정확히 semantic override 역할만 수행), Stage4, non-wuxia lane

`_stage2_flow_guard()` 자체(line 1292-1367)는 4가지 reject 유형을 구분하여 진단한다:

1. `beat_count` — 비트 수 부족 (line 1293-1304)
2. `empty_beats` — 비트 내용 비어 있음 (line 1317-1327)
3. `beat_condensed` — 비트가 제목만 또는 과도 축약 (line 1338-1367)
4. `stagnation` — 반복 정체 (legacy fallback, line 1369+)

문제는 그 구분된 진단이 advisory sink를 통과하면서 전부 동일한 CRITICAL로 평탄화되는 것이다.

## Q3. separate lane이 필요한가?

**No.** 기존 Stage2 SSOT에 접는 게 맞다.

근거:

1. SSOT line 41: `beat_sequence and hybrid_composition are effectively dropped at the Stage2 → Stage3 boundary` — 이미 알려진 사실
2. SSOT line 219: `beat_sequence, hybrid_composition, and semantic_carryover each have an explicit keep-or-drop policy` — 이미 명시적 완료 조건
3. severity mismatch는 그 미결 정책의 자연스러운 증상이지, 별개의 문제 가족이 아님

## 향후 패치 형태 예상

본 메모에서 승인하지 않음. 분류만 기록한다.

1. advisory sink에서 `diagnostics.type`별 severity 분화 (예: beat_count → CRITICAL, beat_condensed → MAJOR)
2. `tactical_doc`/`episode_details`에 동등 서사 구조가 존재할 때 beat 메타데이터 부재의 severity 강등
3. `beat_sequence` keep-or-drop 정책 명시화
4. (선택) 전체 advisory flat severity → tiered severity 정규화 — 이 건은 범위가 넓으므로 별도 판단 필요

## Evidence Index

### Log-side

- `0_temp.txt:535` — Flow Guard REJECT 로그
- `0_temp.txt:539-543` — Director PASS_WITH_FIX, Python CRITICAL 기각 판단

### Code-side

- `modules/core/stage2_validation_pipeline.py:1292-1304` — beat_count reject path
- `modules/core/stage2_validation_pipeline.py:1317-1327` — empty_beats reject path
- `modules/core/stage2_validation_pipeline.py:1338-1367` — beat_condensed reject path
- `modules/core/stage2_validation_pipeline.py:606-612` — advisory sink, 고정 CRITICAL 매핑
- `modules/core/stage2_validation_pipeline.py:397,628,765,796,818,858,872,1036` — 전 advisory source 동일 CRITICAL

### Test-side

- `tests/test_stage2_validation_pipeline.py:123-131` — under-filled/short beats reject 검증
- `tests/test_stage2_validation_pipeline.py:223-232` — Flow Guard REJECT → advisory 전환, proceed 보장
- `tests/test_stage2_preflight_helpers.py:655-673` — preflight 레벨 동일 계약 검증

### 테스트 커버리지 갭

- severity 분화 검증 없음 (CRITICAL vs MAJOR vs WARNING 구분 테스트 부재)
- prose 구조 충분 시 beat 메타데이터 부재 강등 시나리오 미검증
- `tactical_doc` semantic sufficiency가 beat_sequence 구조적 부족을 보상하는 케이스 미검증

## Boundaries

- no code changes
- no `docs/temp` mutation
- no queue mutation
- no roadmap change

## 3-Pass Audit Record

Pass 1, structure and scope:

- Flow Guard severity mismatch만 다룸
- non-wuxia lane, Stage4, Director 쪽 범위 침범 없음

Pass 2, evidence and consistency:

- log/code/test 삼각 검증 완료
- flat severity 구조라는 추가 발견이 기존 survey와 정합
- false positive이 아닌 severity inflation으로 정확 분류됨을 코드 수준에서 확인

Pass 3, execution and readability:

- 3문제 → 3답변 구조 유지
- 향후 패치 형태 분류만, 승인 없음
- 기존 SSOT 흡수 권고 명확

Final confidence: `96%`

Final save approved.
