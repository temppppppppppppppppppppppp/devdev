Date: 2026-04-02
Status: pending (promoted from parked on 2026-04-07 roadmap reorder; long-horizon Stage0 source-of-truth lane kept below nearer bounded slices)
Canonical Path: `docs/2026-04-02/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md`
Baseline Commit: `aaf495d6`
Baseline Dirty Summary: `dirty: Stage4 consumer-contract edits, demo canary artifacts, and queue docs already in flight during SSOT drafting`
Source Survey Docs:
- `docs/2026-04-02/stage0-bible-generation-dna-sync-stage2-consume-bounded-survey.md`
Evidence Artifacts:
- `docs/2026-04-02/stage0-bible-generation-dna-sync-stage2-consume-evidence.json`
Side-Effect Coverage:
- `scripts/build_bi_from_phase0_and_tr.py` routed BI builder contract
- `scripts/build_wuxia_bi_from_phase0_and_tr.py` family-specific BI builder contract
- `modules/core/project_manager.py` DNA sync and DB bible anchor overwrite path
- `modules/core/stage0_handoff.py` roadmap backfill/handoff path
- `modules/core/stage2_orchestrator.py` and `modules/core/stage2_preflight.py` downstream consume path

# 1. Answer First

`BI/TR 생산 하네스 규격화`는 당장 active blocker는 아니지만, 장기적으로는 분명한 정리 대상이다.

핵심 문제는 `BI`와 `TR`을 둘로 나눴다는 사실 자체보다, 현재 구조가

- raw `BI file`
- `treatment`
- DB `bible` anchor

세 군데에 권위를 분산시키고 있다는 점이다.

따라서 이 lane은 지금 바로 구현할 본선이 아니라, `promoted pending long-horizon lane`으로 유지한다.

장기 방향은 다음 둘 중 하나다.

- `canonical material schema -> BI/TR projection`
- 또는 `BI/TR dual artifact`를 유지하더라도 runtime handoff contract를 분리·고정

# 2. Why This Exists

현재 Stage0 조사에서 드러난 문제는 builder 하나의 고장이 아니다.

- 최신 builder 코드는 `plot_roadmap`와 `protagonist_config`를 생산하도록 설계돼 있다.
- 그런데 legacy Stage0 flow와 handoff는 생성 후 treatment 기반으로 roadmap를 다시 만들고 DB anchor에 덮어쓴다.
- Stage2는 raw BI file보다 DB anchor의 handoff 결과를 더 직접 믿고 진입한다.

즉 지금의 real contract는 `artifact schema` 하나가 아니라 `artifact + sync + handoff + DB anchor` 묶음이다.

이 lane은 이 구조를 나중에 정리하기 위한 장기 normalization wave다.

# 3. Scope

## Included

- Stage0 BI/TR production harness contract inventory
- raw artifact schema vs runtime handoff schema separation
- `plot_roadmap`, `protagonist_config`, treatment block owner 정리
- BI/TR dual artifact 유지 vs projection-only model 판단
- legacy DNA sync/handoff의 권한 축소 또는 명시적 demotion

## Excluded

- 지금 당장 builder rewrite
- Stage4 active remediation stack
- enrich retire lane 구현
- 작품별 narrative material rewrite

# 4. Current Findings

1. 최신 builder만 보면 BI contract는 비교적 보수적이다.
   - `plot_roadmap`
   - `protagonist_config`
   - treatment hash alignment
   를 직접 생산/검증한다.

2. runtime에서는 builder 단독 권위가 아니다.
   - `force_sync_v25_dna()`
   - `ensure_plot_roadmap()`
   - bible DB anchor save
   가 생성 후 truth를 다시 주입한다.

3. Stage2는 raw BI file보다 DB bible anchor 기반 handoff truth를 믿는다.

4. root BI corpus는 heterogeneous하다.
   - 어떤 파일은 `plot_roadmap` / `protagonist_config`가 있고
   - 어떤 파일은 없다.

5. 따라서 현재 문제는 `BI/TR schema 확정 미비`만이 아니라
   `artifact schema`와 `runtime-consumable contract`가 분리돼 있지 않다는 것이다.

# 5. Hard Conclusions

1. `BI/TR 생산 하네스 규격화`는 실재하는 upstream 구조 부채다.
2. 하지만 active runtime blocker는 아니므로 지금 즉시 본선으로 올릴 필요는 없다.
3. Stage0 장기 방향은 `split truth 축소`이지, 단순 field backfill 추가가 아니다.
4. `BI`와 `TR`을 계속 둘 다 둘지 여부는 나중에 결정하되, 먼저 `source-of-truth contract`부터 고정해야 한다.
5. 현재 dual-artifact 운영은 임시방편 성격이 강하며, 장기적으로 `projection model` 검토 가치가 있다.

# 6. Non-Goals

- 지금 당장 `BI`와 `TR`를 하나로 합치기
- builder family 전면 rewrite
- Stage2/3/4 active lane 재우선순위화
- Golden Canary pair ingress 경로 즉시 교체

# 7. Acceptance Criteria

이 pending lane을 나중에 활성화할 경우, 최소 acceptance criteria는 아래다.

1. raw artifact truth와 runtime handoff truth의 owner가 문서와 코드에서 명시된다.
2. `plot_roadmap`와 `protagonist_config`가 어디서 authoritative한지 고정된다.
3. legacy DNA sync/handoff가 `silent overwrite` 대신 명시적 compatibility bridge로 격하된다.
4. `BI/TR dual artifact` 유지 여부가 설계로 결정된다.
5. dual artifact를 유지하더라도 `canonical material schema -> projection` 개념이 명시된다.
6. Stage2 consume contract가 raw file 의존인지 DB anchor 의존인지 혼합되지 않는다.

# 8. Execution Shape

## Tranche 1

source-of-truth declaration

- raw BI file
- treatment
- DB bible anchor

세 owner의 역할과 우선순위를 명시한다.

## Tranche 2

runtime handoff normalization

- `force_sync_v25_dna`
- `ensure_plot_roadmap`
- Stage2-ready handoff

를 compatibility bridge로 낮추거나 bounded owner로 재정의한다.

## Tranche 3

production harness normalization

- `canonical material schema`
- `BI/TR projection`
- 또는 `dual artifact with fixed contract`

중 하나로 정리한다.

# 9. Queue Placement

이 lane은 `promoted pending long-horizon lane`이다.

- active Stage4 remediation 아래
- pending `Stage3` / `Stage2` normalization 아래
- `stage0-treatment-enrich-retirement-remediation` 아래

이유:

- 지금 직접 런을 막는 blocker가 아니다
- 구조적으로는 크지만 위험한 upstream refactor다
- active runtime seams와 데모/운영 안정화보다 우선할 이유가 아직 없다

# 10. Next Action

지금은 구현하지 않는다.

운영상 기억만 한다.

- `dual artifact 운영은 임시방편 성격이 강함`
- `split truth 정리`가 장기 목표
- `BI/TR production harness normalization`은 promoted pending long-horizon lane

# 11. 3-Pass Audit

Pass 1. Structure/Scope
- execution SSOT 형식 적합
- pending queue lane 성격 명시
- included/excluded scope 분리 완료

Pass 2. Evidence/Consistency
- source survey/evidence lineage attached
- builder / sync / handoff / Stage2 consume chain과 정합
- current roadmap placement bounded

Pass 3. Execution/Readability
- active implementation 금지 명시
- long-term direction and non-goals 분리
- next action bounded

Confidence: 96%
