Date: 2026-04-02
Status: parked
Canonical Path: `docs/2026-04-02/stage0-treatment-enrich-retirement-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage0-treatment-enrich-retirement-remediation-execution-ssot.md`
Baseline Commit: `aaf495d6`
Baseline Dirty Summary: `dirty: Stage4 consumer-contract edits, demo canary artifacts, and queue docs already in flight during SSOT drafting`
Source Survey Docs:
- `docs/2026-04-02/stage0-bible-generation-dna-sync-stage2-consume-bounded-survey.md`
Evidence Artifacts:
- `docs/2026-04-02/stage0-bible-generation-dna-sync-stage2-consume-evidence.json`
Side-Effect Coverage:
- `main_a.py` treatment enrichment path
- `modules/core/stage01_helpers.py` legacy Stage0 menu path
- `modules/domain/agents/block_enricher.py` treatment block rewrite path

# 1. Answer First

`Stage0 treatment enrich`는 당장 active blocker는 아니지만, 장기적으로는 퇴역 대상이 맞다.

이 기능은 누수 보정보다 `부분 재작성`에 가깝다.

- Stage0 pair pass 자체에 필수도 아니다.
- legacy/manual Stage0 path에서 optional prompt로만 켜진다.
- 켜면 block `title`, `content`, `joint_docs`, `status_shadow`를 다시 쓸 수 있다.

따라서 이 lane은 `active remediation`이 아니라 `parked future wave`로 유지한다.

# 2. Why This Exists

현재 Stage0 enrich 경로는 다음 성격을 가진다.

- `modules/core/stage01_helpers.py`에서 사용자가 opt-in 해야 실행된다.
- `main_a.py`의 `_enrich_treatment_blocks()`는 원본 treatment를 직접 고치지 않고 `_enriched.json` 별도 파일을 만든다.
- 하지만 merge 단계에서 일부 block의 핵심 payload가 새로 교체된다.

즉 enrich는 `schema backfill`이나 `block_no 보정` 같은 bounded normalization이 아니라, `semantic rewrite helper`에 가깝다.

# 3. Scope

## Included

- `main_a.py`
  - `_enrich_treatment_blocks`
  - `_merge_enriched_treatment_blocks`
  - `_save_enriched_treatment_blocks`
- `modules/core/stage01_helpers.py`
  - `_maybe_enrich_phase0_treatment`
- `modules/domain/agents/block_enricher.py`
  - parallel enrich and causal re-enrich path

## Excluded

- Stage0 builder replacement
- BI/TR schema redesign
- Stage2 handoff normalization
- current active Stage4 remediation stack

# 4. Current Findings

1. enrich는 optional이다.
   - Stage0 legacy path에서도 user opt-in 없이는 실행되지 않는다.

2. enrich는 semantic rewrite risk를 가진다.
   - merge path가 `title`, `content`, `joint_docs`, `status_shadow`를 교체할 수 있다.

3. enrich는 pair pass의 필수 계약이 아니다.
   - 골든 카나리아 pair 같은 안정 pair는 enrich 없이도 Stage0 pair-valid 판정을 받을 수 있다.

4. enrich는 태생적으로 임시방편 성격이다.
   - density 부족 block을 Block 1 수준으로 끌어올리는 보조 장치다.
   - canonical source-of-truth를 강화하기보다, treatment를 추가 가공한다.

# 5. Hard Conclusions

1. `Stage0 treatment enrich`는 장기적으로 제거 또는 강등 대상이다.
2. 이 기능은 Stage0 canonical path의 일부로 승격하면 안 된다.
3. active blocker가 아니므로 지금 당장 본선으로 당길 필요는 없다.
4. future wave에서 할 일은 `기능 확장`이 아니라 `퇴역/비활성화/명시적 분리`다.

# 6. Non-Goals

- 지금 당장 enrich path 제거
- active Stage0/Stage2 path 재배선
- narrative material harness 전면 개편

# 7. Acceptance Criteria

이 parked wave를 나중에 열 경우, 최소 acceptance criteria는 아래다.

1. Stage0 기본 pair pass가 enrich 없이도 유지된다.
2. enrich가 canonical default path에서 빠진다.
3. enrich가 남더라도 `explicit non-canonical utility`로 격하된다.
4. semantic rewrite risk가 operator-facing으로 명시된다.
5. Golden Canary 같은 stable pair가 enrich 비의존 경로로 유지된다.

# 8. Execution Shape

## Tranche 1

enrich path authority demotion

- prompt/UI wording에서 canonical Stage0 flow처럼 보이지 않게 낮춘다
- operator에게 `non-canonical semantic rewrite utility`임을 명시한다

## Tranche 2

default-off hardening

- legacy/manual path에서 accidental invocation risk를 더 낮춘다
- active pair flow에서 enrich를 전제하지 않게 정리한다

## Tranche 3

retirement or quarantine

- 필요 시 enrich를 separate salvage utility로 분리
- canonical Stage0 path에서는 제거

# 9. Queue Placement

이 lane은 `parked future wave`다.

- active Stage4 remediation보다 아래
- `Stage3 contract tightening`, `Stage2 contract normalization` 같은 parked wave보다도 아래
- 이유:
  - direct runtime blocker가 아님
  - operator가 지금 당장 이 기능을 쓰지 않아도 주요 pair 운영은 가능함

# 10. Next Action

지금은 구현하지 않는다.

운영상 조치만 기억한다.

- `enrich는 temporary workaround`
- `canonical Stage0 기준으로 보지 않음`
- `추후 retire/deprecate lane으로만 다룸`

# 11. 3-Pass Audit

Pass 1. Structure/Scope
- execution SSOT 타입 적합
- parked future wave임을 명시
- included/excluded scope 분리 완료

Pass 2. Evidence/Consistency
- enrich trigger path, merge path, and block_enricher rewrite role confirmed
- source survey/evidence lineage attached
- queue placement rationale bounded to current roadmap state

Pass 3. Execution/Readability
- active implementation 금지 명시
- retirement lane 성격과 future tranche shape 명시
- next action bounded

Confidence: 96%
