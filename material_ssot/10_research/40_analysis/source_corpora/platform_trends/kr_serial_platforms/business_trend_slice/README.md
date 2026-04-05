# Business Trend Slice

Status: active bounded slice  
Date: 2026-04-01

이 폴더는 `kr_serial_platforms` 전체 코퍼스에서
`현대판타지 기업물 / 오피스 파워 / 재벌 / 투자 / 산업 운영 / 미디어사업`
쪽에 가까운 작품만 다시 잘라낸 material-side 슬라이스다.

원칙:

- Python은 `exact-match scoring + dedupe + rollup`만 담당
- 어떤 작품이 진짜로 먹히는지, 어떤 결을 source manifest에 올릴지는 LLM이 판단
- `positive_matches / negative_matches / business_buckets`를 그대로 남겨
  나중에 수동 감리와 재해석이 가능하도록 한다

생성 명령:

```text
python -X utf8 scripts/build_business_trend_slice.py ^
  --input-db material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/platform_trends.sqlite3 ^
  --output-root material_ssot/10_research/40_analysis/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice
```

기본 산출물:

- `business_slice_schema.json`
- `business_trend_entries.jsonl`
- `business_trend_works.jsonl`
- `business_trend_rollup.json`
- `business_trend_slice.sqlite3`
- `collection_status.json`

현재 산출 기준:

- broad platform corpus에서 transparent keyword scoring으로 1차 필터
- `작품 단위(work)` dedupe 포함
- `로맨스 / BL / 로판 / 무협 / 헌터 / 탑 / 아포칼립스` 잡음은 penalty 또는 exclusion
- `badge code` 같은 UI 구조 신호는 제거

현재 결과:

- entries: `116`
- deduped works: `98`

바로 다음 사용처:

- `source_manifest`용 현대판타지 기업물 후보군 압축
- 플랫폼별 제목 포장 비교
- modern-business ideation draft bank에 business-power seed 추가

Bounded validation note:

- this slice is machine-checked through `collection_status.json`
