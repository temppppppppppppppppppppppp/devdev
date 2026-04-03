# 로직_리서치 분해 설계안 v0.1

Date: 2026-04-03
Status: realized design baseline
Scope: `로직_리서치`를 `SSOT authority`가 아닌 `legacy runtime note root`로 재정의하고 collector/runtime code를 분리하기 위한 분해 설계
Execution Rule: 본 문서는 분해 기준과 수용 슬롯을 정의한다. same-day follow-up bounded cutover에서는 `output/`, operator note, crawler code relocation까지 반영했다.

## 1. Purpose

`로직_리서치`는 현재 이름만 보면 하나의 연구 루트처럼 보이지만, 실제로는 아래 성격이 섞여 있다.

- 수집 스크립트
- 운영 메모
- raw jsonl ingest
- 날짜별 정리 JSON/CSV snapshot
- 파이썬 캐시

이 상태로는 `material_ssot`의 stage authority와 `runtime collector`가 섞여 보여 운영자가 경로를 직관적으로 판단하기 어렵다.

이번 설계의 목적은:

- `로직_리서치`를 SSOT에서 분리해 `runtime/backend collector area`로 재정의
- 사람이 읽는 canonical research stage root는 계속 `material_ssot/10_research` 하나로 고정
- 이후 bounded cutover 때 무엇을 어디로 보낼지 미리 명확히 분류

## 2. Initial Snapshot

2026-04-03 cutover 직전 `로직_리서치`는 아래 구성이었다.

- top-level scripts:
  - `crawl_new_novels.py`
  - `crawl_syuka.py`
  - `crawl_top100.py`
  - `crawl_youtube.py`
- operator note:
  - `ORDER_youtube_parallel.md`
- raw ingest:
  - `output/_*.jsonl` 10개
- dated snapshots:
  - `output/*.json` 42개
  - `output/*.csv` 42개
- cache:
  - `__pycache__/`

즉, initial state의 `로직_리서치`는 `authority root`가 아니라 `실행기 + 원시수집물 + 파생결과물 + 메모`를 함께 담는 작업장이었다.

## 3. Current Realized State

2026-04-03 same-day follow-up 기준 현재 상태는 아래다.

- collector code:
  - `scripts/research_collectors/`
- canonical runbook:
  - `material_ssot/10_research/00_registry/youtube-parallel-collector-runbook.md`
- canonical raw ingest:
  - `material_ssot/10_research/80_ingest_raw/2026-04-03/`
- canonical derived snapshots:
  - `material_ssot/10_research/40_analysis/market_snapshots/2026-04-03/`
- legacy root:
  - `로직_리서치/README.md`
  - `로직_리서치/ORDER_youtube_parallel.md`
  - `로직_리서치/output/README.md`

## 4. Decision

핵심 결정은 아래다.

- `material_ssot/10_research`만 research stage authority로 유지
- `로직_리서치`는 canonical research root로 취급하지 않음
- `로직_리서치`는 앞으로 `collector/runtime staging area`로만 취급
- 사람이 읽는 research 결과는 `material_ssot` 쪽으로만 승격

한 줄 요약:

`SSOT는 material_ssot가 맡고, 로직_리서치는 수집 런타임과 임시 산출물 작업장으로 내린다.`

## 5. Target Split

권장 목표 구조는 아래다.

```text
material_ssot/10_research/
  00_registry/
    logic-research-source-registry.md
  10_reference_profiles/
  20_fewshot_bank/
  30_work_materials/
  40_analysis/
    market_snapshots/
      YYYY-MM-DD/
  80_ingest_raw/
    YYYY-MM-DD/

scripts/research_collectors/
  crawl_*.py
  runtime_paths.py

로직_리서치/
  legacy notes
  pointer surfaces
```

## 6. Classification Rules

### A. Collector Runtime

대상:

- `crawl_*.py`
- 향후 수집용 보조 스크립트

처리:

- `scripts/research_collectors/`로 이관 완료
- `로직_리서치`에는 collector code를 남기지 않는다
- 결과 sink는 `material_ssot` 날짜 버킷을 직접 사용한다

### B. Raw Ingest

대상:

- `output/_*.jsonl`

처리:

- canonical raw ingest root는 `material_ssot/10_research/80_ingest_raw/YYYY-MM-DD/`
- 파일명은 source prefix를 유지
- raw는 사람이 직접 읽는 정본이 아니라 evidence bucket으로 취급

### C. Derived Snapshots

대상:

- `output/*_all_*.json`
- `output/*_detail_*.json`
- `output/*_enriched_*.json`
- 대응하는 CSV 쌍

처리:

- 사람이 보는 canonical stage-side snapshot은 `material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/`
- JSON을 우선 정본으로 보고 CSV는 operator-friendly companion export로 둔다
- 이 결과물은 raw와 분리해 둔다

### D. Operator Notes

대상:

- `ORDER_youtube_parallel.md`

처리:

- canonical note는 `material_ssot/10_research/00_registry/logic-research-source-registry.md` 또는 별도 runbook으로 흡수
- 원본은 당분간 `로직_리서치`에 남겨도 되지만 authority는 `material_ssot` 쪽 문서가 가진다

### E. Cache / Disposable Artifacts

대상:

- `__pycache__/`

처리:

- SSOT 대상 아님
- 이관 대상도 아님
- 필요 시 추후 정리

## 7. Migration Sequence

안전한 순서는 아래다.

1. 설계 문서 저장
2. `material_ssot/10_research` 아래 수용 슬롯 생성
3. registry 문서에 `로직_리서치` 현재 surface 기록
4. 다음 bounded cutover에서 `output/`만 먼저 이동
5. 그 다음 operator note 승격
6. 마지막에 crawler code를 `scripts/research_collectors/`로 재배치

즉, 최초 cutover는 `code`가 아니라 `output`부터였고, 이후 same-day follow-up에서 code를 옮겼다.

## 8. Why Output-First

`로직_리서치`에서 가장 헷갈리는 것은 코드보다도 `결과물`이다.

- 코드가 있어도 runtime이라고 이해할 수 있다
- 하지만 결과 JSON/CSV가 같은 폴더에 쌓이면 사람이 그것을 canonical research asset으로 오인한다

그래서 bounded cutover 우선순위는:

1. dated snapshot outputs
2. raw ingest jsonl
3. operator note
4. crawler code

## 9. Immediate Actions In This Wave

이번 웨이브에서 바로 하는 일은 아래로 제한한다.

- 설계 문서 저장
- `00_registry`, `40_analysis`, `80_ingest_raw` 스켈레톤 생성
- `README`와 registry note 작성
- `source-map.md`와 `10_research/README.md`에 새 분류 반영
- `로직_리서치/output`을 날짜 버킷 기준으로 first bounded cutover
- `ORDER_youtube_parallel.md`를 registry canonical runbook으로 승격
- crawler code를 `scripts/research_collectors/`로 재배치

이번 웨이브에서 하지 않는 일:

- 파일명 변경
- 수집 파이프라인 재실행

## 10. Conclusion

`로직_리서치`는 research SSOT가 아니라 legacy runtime note root로 보는 것이 맞다.

따라서 앞으로는:

- authority: `material_ssot/10_research`
- runtime code: `scripts/research_collectors`
- legacy note root: `로직_리서치`
- canonical human-facing snapshots: `40_analysis/market_snapshots`
- canonical raw ingest bucket: `80_ingest_raw`

이 구도로 분리해 가는 것이 가장 안정적이다.

## 11. 3-Pass Audit Note

Pass 1. Structure and scope
- `로직_리서치` 전체를 옮기지 않고, 분해 기준과 수용 슬롯만 정의하는 문서로 범위 고정

Pass 2. Evidence and consistency
- initial snapshot과 realized state를 구분해 기록
- current realized layout은 `scripts/research_collectors + material_ssot buckets + 로직_리서치 pointer surface`로 재확인

Pass 3. Execution and readability
- 즉시 실행 가능한 순서를 `output first` 원칙으로 제한
- authority와 runtime 경계를 명확히 분리

Estimated Confidence: 97%
