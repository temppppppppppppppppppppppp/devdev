# narrative_ssot Triage Inventory v0.1

Date: 2026-04-03
Status: triage baseline
Scope: `narrative_ssot`를 즉시 삭제하지 않고, `흡수 / 유지 / freeze / archive` 후보로 분류한다

## 1. Purpose

`material_ssot`가 재료 사이드 오더의 stage SSOT로 올라오면서, `narrative_ssot`는 더 이상 live authority가 아니다.

하지만 이 경로 안에는 아직 아래 성격이 섞여 있다.

- mirror
- scaffold harness
- draft contracts
- pilot vertical stack
- old cutover notes

이 문서는 `narrative_ssot`를 바로 삭제하지 않고, 어떤 자산을 어느 방식으로 처리할지 분류하는 1차 inventory다.

## 2. Current Footprint

| Path | Current contents | Current role | First interpretation |
| --- | --- | --- | --- |
| `narrative_ssot/00_governance` | 2 files | scaffold authority note | historical scaffold note set |
| `narrative_ssot/10_reference_bank` | 49 dirs / 192 files | mirror copy | active mirror only, not authority |
| `narrative_ssot/30_harness` | 7 files | stage harness draft | scaffold runbook set |
| `narrative_ssot/40_contracts` | 6 dirs / 11 files | schema and gate draft | draft contract lane |
| `narrative_ssot/50_projects` | 17 dirs / 27 files | pilot vertical stack | template + pilot residue |
| `narrative_ssot/90_migration` | 2 files | old cutover draft | historical migration note |

## 3. Confirmed Non-Authority Facts

- `narrative_ssot/README.md` states `Status: scaffold draft`.
- `narrative_ssot/00_governance/authority_map.md` explicitly says current live authority is still `material_ssot`, `treatments/`, and `bible/`.
- `narrative_ssot/10_reference_bank/mirror_status.json` says the authoritative few-shot source is `material_ssot/10_research/20_fewshot_bank`.
- `scripts/sync_narrative_reference_bank.py` still actively syncs the mirror.
- `scripts/create_narrative_project_scaffold.py` still supports creating `narrative_ssot/50_projects/{work_id}` pilot scaffolds.

즉, 이 루트는 `dead folder`가 아니라 `active scaffold residue`다.
그래서 지금 정답은 `즉시 삭제`가 아니라 `triage 후 freeze/archive`다.

## 4. Triage Table

| Path | Recommended action | Why |
| --- | --- | --- |
| `00_governance` | `absorb-summary-then-freeze` | 현재 authority 설명은 이미 `material_ssot`와 이 문서군이 대체하고 있다 |
| `10_reference_bank` | `split-keep-and-migrate` | cards/manifest는 mirror지만 `source_corpora`는 아직 active sink라 subtree 분리가 먼저다 |
| `30_harness` | `review-then-archive-candidate` | 일부 stage read order 문구는 이미 `material_ssot`와 `docs/narrative-router`에 흡수됐다 |
| `40_contracts` | `freeze-review` | draft schema/gate지만 live contract replacement로 승격된 상태는 아니다 |
| `50_projects` | `archive-candidate` | `_template`와 `pilot_vertical_stack_001`은 pilot residue이며 live production root가 아니다 |
| `90_migration` | `absorb-note-then-archive` | cutover 초안은 historical reference 가치만 남아 있다 |

## 5. Active Dependency Check

현재 바로 끊으면 안 되는 연결은 아래 둘이다.

1. `scripts/sync_narrative_reference_bank.py`
- canonical few-shot bank를 `narrative_ssot/10_reference_bank/`로 미러링한다
- 이 스크립트를 끊기 전에는 `10_reference_bank`를 archive하면 안 된다

2. `scripts/create_narrative_project_scaffold.py`
- `narrative_ssot/50_projects/_template`를 복제한다
- pilot scaffold workflow를 완전히 버리거나 대체 경로를 만들기 전에는 `_template`를 성급히 지우면 안 된다

또한 `source_corpora`는 아래 builder script들의 active sink다.

- `scripts/build_business_trend_slice.py`
- `scripts/build_platform_trend_corpus.py`
- `scripts/build_youtube_channel_corpus.py`
- `scripts/export_youtube_idea_packets.py`

즉, `10_reference_bank`와 `50_projects/_template`는 지금 당장 삭제 금지다.

## 6. Safe Order

가장 안전한 정리 순서는 아래다.

1. `narrative_ssot` 전체를 `no-new-authority` 상태로 해석한다
2. `10_reference_bank`는 subtree를 나눠 해석한다
   - `cards/manifest`는 mirror-only
   - `source_corpora`는 active sink
3. `30_harness`, `40_contracts`, `90_migration`에서 유효 문구만 문서 레벨로 흡수한다
4. `50_projects/pilot_vertical_stack_001` 같은 pilot residue를 archive 후보로 분리한다
5. scaffold utility와 mirror sync의 대체 여부를 결정한 뒤에만 root freeze 또는 archive를 건다

`10_reference_bank`의 source_corpora cutover baseline은 아래 문서를 따른다.

- `docs/2026-04-03/narrative-source-corpora-bounded-cutover-design.md`

## 7. Practical Decision

현 시점 운영 문장으로는 이렇게 쓰는 게 맞다.

`narrative_ssot는 현재 active SSOT가 아니라 scaffold residue다. 다만 mirror sync와 pilot scaffold utility가 아직 남아 있어 즉시 삭제 대상은 아니다.`

따라서 다음 액션은 `삭제`가 아니라:

- `mirror 유지 범위 확정`
- `pilot scaffold 유지 여부 결정`
- `archive 후보 분리`

이 세 가지다.

## 8. Recommended Immediate Next Step

바로 다음 실작업은 아래 중 하나다.

1. `narrative_ssot freeze note` 작성
- root README를 `scaffold-frozen candidate`로 낮추고 new writes 금지 문구를 추가

2. `pilot scaffold deprecation audit`
- `create_narrative_project_scaffold.py`를 계속 유지할지, 아니면 `material_ssot` 기반 새 scaffold로 바꿀지 결정

3. `mirror necessity audit`
- `10_reference_bank` mirror가 실제로 누가 필요한지 확인한 뒤 keep or retire 결정

현재 우선순위는 `3 -> 2 -> 1`이다.
이유는 `10_reference_bank` 안에서도 cards mirror보다 `source_corpora` active sink가 더 큰 blocker이기 때문이다.

## 9. 3-Pass Audit Note

Pass 1. Scope
- `narrative_ssot`를 하나의 폴더가 아니라 mirror/scaffold/pilot/migration 혼합체로 재정의

Pass 2. Evidence
- root README, authority map, mirror status, script entrypoints, per-folder footprint를 대조

Pass 3. Closure
- delete vs keep의 흑백판정 대신 `keep-as-mirror / freeze-review / archive-candidate`로 분리

Estimated Confidence: 95%
