# narrative source_corpora bounded cutover design v0.1

Date: 2026-04-03
Status: design baseline
Scope: `narrative_ssot/10_reference_bank/source_corpora`를 `material_ssot` 쪽 canonical research lanes로 옮기기 위한 bounded cutover 설계를 고정한다

## 1. Purpose

`narrative_ssot/10_reference_bank` retirement blocker는 `cards mirror`가 아니라 `source_corpora`다.

현재 여러 builder script가 이 경로를 직접 output/input root로 사용한다.
그래서 이 경로를 갑자기 지우는 대신, `subtree intact` 원칙으로 새 canonical lane을 먼저 정해야 한다.

이 문서의 목적은:

- `source_corpora`를 어떤 canonical lane으로 받을지 정의
- 어떤 subtree를 어떤 순서로 옮길지 고정
- script default root 전환 순서를 저위험 기준으로 정리

## 2. Current Footprint

`narrative_ssot/10_reference_bank/source_corpora` 현재 주요 subtree:

- `platform_trends/kr_serial_platforms`
  - public platform html raw
  - JSONL
  - rollup JSON
  - sqlite3
  - `business_trend_slice/`
- `youtube/syukaworld`
  - video manifest/index
  - transcript JSONL
  - sqlite3
  - raw `info.json` / `json3`
  - `idea_packets_recent.jsonl`
- `nas_serials/medical/magical_surgeon_sample_corpus`
  - bounded title sample corpus
  - manifest
  - README
  - sampled episode txt

핵심 차이:

- `platform_trends` / `youtube`는 active builder script sink
- `nas_serials`는 sample corpus pack

따라서 이 셋을 같은 규칙으로 옮기면 안 된다.

## 3. Cutover Principle

이번 cutover의 원칙은 아래다.

1. `subtree intact`
- raw / normalized / rollup을 억지로 다른 루트로 쪼개지 않는다
- 먼저 canonical subtree root만 바꾼다

2. `script-first safety`
- 파일만 먼저 옮기고 스크립트를 나중에 맞추지 않는다
- 새 canonical root를 정한 뒤 script default를 같이 전환한다

3. `authority before cleanup`
- old path는 pointer shell이 되기 전까지 그대로 읽을 수 있어야 한다
- new root가 정본으로 올라간 뒤에만 old path를 내린다

## 4. Recommended Canonical Lanes

### A. platform trends

권장 새 root:

`material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms`

이유:

- 분석용 rollup, sqlite, jsonl이 주된 가치다
- raw html도 corpus package 일부로 함께 읽히는 편이 안전하다
- `market_snapshots/`는 날짜 버킷 성격이라, 장기 corpus root로 쓰기에는 맞지 않는다

### B. youtube channel corpus

권장 새 root:

`material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld`

이유:

- 이것도 단순 ingest보다 reusable research corpus에 가깝다
- `transcript_documents.jsonl`, `video_lookup.jsonl`, sqlite가 장기 해석 자산이다
- raw video artifacts도 subtree 내부에 그대로 유지하는 쪽이 cutover 리스크가 낮다

### C. NAS serial sample corpus

권장 새 root:

`material_ssot/10_research/50_corpus_curated/reference_samples/medical_magical_surgeon_sample_corpus`

이유:

- 이건 trend corpus가 아니라 bounded representative sample pack이다
- `50_corpus_curated`의 성격에 더 잘 맞는다

## 5. Script Repoint Set

아래 스크립트는 default root를 새 canonical lane으로 바꿔야 한다.

### platform trends family

- `scripts/build_platform_trend_corpus.py`
- `scripts/build_business_trend_slice.py`

새 기준:

- input/output default를 `material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms` 기준으로 전환

### youtube family

- `scripts/build_youtube_channel_corpus.py`
- `scripts/export_youtube_idea_packets.py`

새 기준:

- input/output default를 `material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld` 기준으로 전환

### nas sample family

- immediate script repoint는 없음
- sample corpus는 move 후 pointer만 남기면 된다

## 6. Wave Order

가장 안전한 실행 순서는 아래다.

1. `platform_trends` cutover
- corpus root 생성
- two builder scripts default root 전환
- subtree move
- old path pointer화

2. `youtube/syukaworld` cutover
- corpus root 생성
- two builder scripts default root 전환
- subtree move
- old path pointer화

3. `nas_serials/medical/magical_surgeon_sample_corpus` cutover
- curated reference sample lane 생성
- subtree move
- old path pointer화

4. `idea_engine_db` / `selection` triage
- archive or absorb-note only

5. 마지막에 `10_reference_bank` 재판정
- 이 시점부터는 진짜 `cards mirror residue`만 남는지 확인

## 7. Why Not Split Into 40_analysis + 80_ingest_raw Immediately

이 문서가 `subtree intact`를 고수하는 이유는 아래다.

- `platform_trends`와 `youtube`는 이미 raw + normalized + rollup + sqlite가 함께 읽히는 corpus package다
- 지금 단계에서 raw를 `80_ingest_raw`로, normalized를 `40_analysis`로 다시 쪼개면
  script 수정량과 stale reference risk가 급증한다
- 먼저 canonical subtree root만 옮긴 뒤, 나중에 정말 필요할 때만 내부 재분해하는 편이 안전하다

즉 이번 cutover는 `정리`가 아니라 `authority relocation`이 우선이다.

## 8. Practical Outcome

이 설계가 실행되면:

- `narrative_ssot/10_reference_bank/source_corpora`는 active sink 지위를 잃는다
- `narrative_ssot/10_reference_bank`는 점점 `cards mirror + archive residue`로 축소된다
- 이후 `10_reference_bank` keep/retire 판단이 훨씬 쉬워진다

## 9. Recommended Immediate Execution Doc

바로 다음 실작업 문서는 아래가 맞다.

- `platform_trends source_corpora cutover execution SSOT`

이유:

- active script가 2개뿐이라 가장 bounded하다
- modern business 관련 현재 문서 참조도 이 subtree에 가장 많이 묶여 있다
- 성공하면 `youtube` cutover도 같은 패턴으로 따라갈 수 있다

## 10. 3-Pass Audit Note

Pass 1. Scope
- `source_corpora`를 하나의 폴더가 아니라 `platform_trends / youtube / nas sample` 3갈래로 분리

Pass 2. Evidence
- subtree footprint, README intent, builder script default roots를 대조

Pass 3. Closure
- immediate full move 대신 subtree-intact bounded cutover 순서를 고정

Estimated Confidence: 95%
