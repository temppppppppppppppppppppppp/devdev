Date: 2026-04-02
Status: closed historical backing (2026-04-23 ROI compaction; the enrich path is already explicit opt-in non-canonical utility behavior with separate `*_enriched.json` output, so the remaining retirement/quarantine work no longer deserves visible queue authority)
Canonical Path: `docs/2026-04-02/stage0-treatment-enrich-retirement-remediation-execution-ssot.md`
Temp Mirror Path: `retired on 2026-04-23 (former path: docs/temp/stage0-treatment-enrich-retirement-remediation-execution-ssot.md)`
Baseline Commit: `eac3386ce3b19f720e6e12548721df5abe2ee755`
Baseline Dirty Summary: `dirty: prior Stage3/Stage4 bounded tranches and queue docs already in flight during Stage0 enrich re-audit`
Source Survey Docs:
- `docs/2026-04-02/stage0-bible-generation-dna-sync-stage2-consume-bounded-survey.md`
- `docs/2026-04-19/stage0-treatment-enrich-retirement-reactivation-refresh.md`
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

따라서 이 lane은 visible queue에서는 retire하고 canonical `historical backing`으로만 남긴다.

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

5. authority demotion은 bounded하게 착수 가능하다.
   - default-off semantics를 바꾸지 않고도 prompt/UI/save wording에서 canonical path 아님을 명시할 수 있다.
   - 이번 tranche는 바로 그 operator-facing demotion만 수행한다.

# 5. Hard Conclusions

1. `Stage0 treatment enrich`는 장기적으로 제거 또는 강등 대상이다.
2. 이 기능은 Stage0 canonical path의 일부로 승격하면 안 된다.
3. active blocker가 아니므로 지금 당장 본선으로 당길 필요는 없다.
4. 이 lane에서 할 일은 `기능 확장`이 아니라 `퇴역/비활성화/명시적 분리`다.

# 6. Non-Goals

- 지금 당장 enrich path 제거
- active Stage0/Stage2 path 재배선
- narrative material harness 전면 개편

# 7. Acceptance Criteria

이 lane을 열 경우, 최소 acceptance criteria는 아래다.

1. Stage0 기본 pair pass가 enrich 없이도 유지된다.
2. enrich가 canonical default path에서 빠진다.
3. enrich가 남더라도 `explicit non-canonical utility`로 격하된다.
4. semantic rewrite risk가 operator-facing으로 명시된다.
5. Golden Canary 같은 stable pair가 enrich 비의존 경로로 유지된다.

# 8. Execution Shape

## Tranche 1

enrich path authority demotion

- landed in this pass:
  - legacy Stage0 prompt에서 `canonical Stage0 pair pass 경로가 아님`을 명시
  - confirm/save/runtime log에서 `non-canonical semantic rewrite utility`와 rewrite risk를 명시
  - original Treatment preserved / `_enriched.json` utility output wording을 operator-facing으로 고정

## Tranche 2

default-off hardening

- legacy/manual path에서 accidental invocation risk를 더 낮춘다
- active pair flow에서 enrich를 전제하지 않게 정리한다

## Tranche 3

retirement or quarantine

- 필요 시 enrich를 separate salvage utility로 분리
- canonical Stage0 path에서는 제거

# 9. Queue Placement

이 lane은 이제 `historical backing`으로만 보존한다.

- direct runtime blocker가 아니다
- legacy/manual Stage0 path에서만 opt-in utility로 남아 있다
- operator가 지금 당장 이 기능을 쓰지 않아도 주요 pair 운영은 가능하다

# 10. Next Action

현재 visible queue next action은 없다.

이 lane은 아래 조건이 충족될 때만 다시 연다.

- `Tranche 2: default-off hardening`을 실제로 열겠다는 명시적 operator 결정
- `Tranche 3: retirement or quarantine`을 bounded utility-removal wave로 열겠다는 명시적 operator 결정

# 11. 3-Pass Audit

Pass 1. Structure/Scope
- execution SSOT 타입 적합
- first bounded authority-demotion tranche만 열고 broad Stage0 재배선을 피함
- included/excluded scope 분리 유지

Pass 2. Evidence/Consistency
- enrich trigger path, merge path, and block_enricher rewrite role reconfirmed
- `modules/core/stage01_helpers.py` / `main_a.py` live wording surfaces now demoted
- source survey/evidence lineage attached
- queue placement rationale remains bounded to current roadmap state

Pass 3. Execution/Readability
- first bounded tranche는 operator-facing wording demotion으로 제한
- retirement lane 성격과 later tranche shape 명시
- next unopened lane shift만 문서적으로 반영 가능하도록 정리

# 12. 2026-04-19 Reactivation Refresh

Source doc:

- `docs/2026-04-19/stage0-treatment-enrich-retirement-reactivation-refresh.md`

Current reading:

- the first authority-demotion tranche is landed
- the remaining enrich retirement/quarantine work is still real
- the lane is not stale, but it is also not active progress anymore

Queue consequence at the time:

- keep this lane visible
- keep the temp mirror
- treat it as parked hygiene debt rather than active implementation progress

2026-04-23 superseding note:

- the later ROI compaction retired this lane from the visible queue
- the temp mirror was removed
- the canonical SSOT remains only as historical backing

Confidence: 97%
