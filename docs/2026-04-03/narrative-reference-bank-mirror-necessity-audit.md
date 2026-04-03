# narrative reference bank mirror necessity audit v0.1

Date: 2026-04-03
Status: audit baseline
Scope: `narrative_ssot/10_reference_bank`가 지금도 필요한지, 필요하다면 어떤 하위 영역이 왜 필요한지 판정한다

## 1. Purpose

`material_ssot/10_research/20_fewshot_bank`가 canonical few-shot bank로 올라온 뒤에도,
`narrative_ssot/10_reference_bank`가 계속 남아 있다.

하지만 이 경로는 실제로 아래가 섞여 있다.

- few-shot mirror
- source corpora sink
- draft idea engine files
- selection placeholder

그래서 이 문서의 목적은 `keep or delete`를 한 번에 내리는 게 아니라,
`어느 하위 경로가 진짜 active dependency인지`를 분리해서 판단하는 것이다.

## 2. Current Footprint

`narrative_ssot/10_reference_bank` 현재 구성:

- `cards/` - 24 files
- `reference_card_manifest.json`
- `mirror_status.json`
- `reference_card_manifest.mirror.md`
- `source_corpora/` - 45 dirs / 160 files
- `idea_engine_db/` - 3 files
- `selection/` - 1 file

즉 이 경로는 단순 mirror 한 벌이 아니라 `mirror + corpus sink + draft residue` 혼합체다.

## 3. Confirmed Mirror Facts

아래 사실은 확정됐다.

- authoritative few-shot root는 `material_ssot/10_research/20_fewshot_bank`다.
- `scripts/sync_narrative_reference_bank.py`는 canonical few-shot manifest와 cards만 `narrative_ssot/10_reference_bank/`로 복사한다.
- `narrative_ssot/10_reference_bank/mirror_status.json`도 mirror source가 `material_ssot`라고 명시한다.
- active code / tests 범위에서 `narrative_ssot/10_reference_bank/cards/` 또는 `reference_card_manifest.json`을 runtime input으로 읽는 consumer는 이번 audit에서 확인되지 않았다.

즉 `cards + reference_card_manifest`는 현재 `traceability mirror`이지 live authority는 아니다.

## 4. Confirmed Non-Mirror Active Dependencies

반면 `source_corpora`는 mirror가 아니라 active data sink다.

확인된 코드 경로:

- `scripts/build_business_trend_slice.py`
  - input/output default가 `narrative_ssot/10_reference_bank/source_corpora/platform_trends/...`
- `scripts/build_platform_trend_corpus.py`
  - output default가 `narrative_ssot/10_reference_bank/source_corpora/platform_trends/...`
- `scripts/build_youtube_channel_corpus.py`
  - output default가 `narrative_ssot/10_reference_bank/source_corpora/youtube/syukaworld/...`
- `scripts/export_youtube_idea_packets.py`
  - DB input과 output default가 `narrative_ssot/10_reference_bank/source_corpora/youtube/syukaworld/...`

즉, `10_reference_bank` 전체를 지금 당장 retire할 수 없는 이유는 `cards mirror`가 아니라 `source_corpora` 때문이다.

## 5. Reference Surface Check

문서 참조도 나뉜다.

### A. current or near-current docs

- `docs/2026-04-03/modern-business-engine-candidate-bank-100.draft.md`
  - `source_corpora/...`
  - `cards/*.md`

### B. older context docs

- `docs/이전/2026-04-01/modern-business-material-context-handoff.md`
- `docs/이전/2026-04-01/office_checkup_next_day-opus-context-memo.md`
- `docs/이전/2026-04-01/opus-office_checkup_next_day-concept-upgrade-order.md`

이 문서들은 주로 `source_corpora`와 `idea_engine_db`를 가리킨다.

## 6. Triage Result

하위 경로별 판정은 아래가 맞다.

| Path | Current necessity | Recommendation |
| --- | --- | --- |
| `cards/` | low | keep temporarily as mirror until explicit retire call |
| `reference_card_manifest.json` | low | keep temporarily as mirror until explicit retire call |
| `mirror_status.json` | low | keep while mirror exists |
| `reference_card_manifest.mirror.md` | low | keep while mirror exists |
| `source_corpora/` | high | do not retire yet; migrate sinks first |
| `idea_engine_db/` | low to medium | review as archive candidate after source_corpora plan |
| `selection/` | low | archive candidate |

## 7. Practical Conclusion

운영 문장으로는 이렇게 쓰는 게 정확하다.

`narrative_ssot/10_reference_bank`는 전체가 keep 대상이 아니다. cards/manifest는 저우선 mirror이고, 실제 retirement blocker는 source_corpora를 아직 여러 corpus builder script가 output/input root로 쓰고 있다는 점이다.`

즉 현재 권고는:

1. `cards/manifest mirror`는 유지하되 low-priority residue로 취급
2. `source_corpora`는 active sink로 분리 인식
3. `idea_engine_db`, `selection`은 archive 후보로 분리

## 8. Recommended Next Step

바로 다음 안전한 작업은 `source_corpora bounded cutover design`이다.

목표:

- `platform_trends`와 `youtube/syukaworld`를 `material_ssot/10_research` 쪽 canonical analysis/raw buckets로 이관
- builder script들의 default output root를 새 canonical lane으로 전환
- 그 이후에야 `10_reference_bank`를 진짜 mirror-only residue로 축소 가능

권장 순서:

1. `source_corpora`를 `platform_trends`, `youtube`, `nas_serials`로 분해 inventory
2. 새 canonical lane 후보를 `material_ssot/10_research/40_analysis` 또는 `80_ingest_raw` 아래에 설계
3. builder script default root 전환
4. old `source_corpora`를 pointer 또는 archive로 전환
5. 마지막에 cards mirror retire 여부 재판정

현재 설계 초안은 아래에 저장했다.

- `docs/2026-04-03/narrative-source-corpora-bounded-cutover-design.md`

## 9. 3-Pass Audit Note

Pass 1. Scope
- `10_reference_bank`를 mirror-only라고 단정하지 않고 mixed-role subtree로 재판정

Pass 2. Evidence
- sync script, builder scripts, mirror status, doc references를 대조

Pass 3. Closure
- keep/retire를 folder-level black-or-white로 내리지 않고 subtree별 necessity로 분리

Estimated Confidence: 96%
