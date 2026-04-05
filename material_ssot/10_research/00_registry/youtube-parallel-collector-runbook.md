# 유튜브 병렬 수집 런북

Date: 2026-04-03
Status: canonical runtime-runbook note
Scope: `crawl_youtube.py` 병렬 실행 시 operator note 정본

## 1. Purpose

이 문서는 유튜브 수집 런타임 실행 절차를 기록하는 canonical runbook이다.

권위 경계는 아래처럼 둔다.

- runtime execution area:
  - `scripts/research_collectors`
- canonical research authority:
  - `material_ssot/10_research`
- raw ingest sink:
  - `material_ssot/10_research/80_ingest_raw/YYYY-MM-DD/`
- derived snapshot sink:
  - `material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/`

즉, 실행 코드는 `scripts/research_collectors`에 두고 결과 인용과 소비는 `material_ssot` 기준으로 한다.

## 2. Preflight

- 작업 디렉토리:
  - workspace root
- main script:
  - `scripts/research_collectors/crawl_youtube.py`
- current note:
  - `pirates`는 완료로 기록돼 있었고, 나머지 채널을 병렬 실행하는 오더였다

## 3. Parallel Launch Commands

### Terminal 1. 지식인미나니

```bash
python -X utf8 scripts/research_collectors/crawl_youtube.py minani
```

### Terminal 2. 보다 BODA

```bash
python -X utf8 scripts/research_collectors/crawl_youtube.py boda
```

### Terminal 3. 테크몽

```bash
python -X utf8 scripts/research_collectors/crawl_youtube.py techmong
```

### Terminal 4. 벌거벗은 세계사

```bash
python -X utf8 scripts/research_collectors/crawl_youtube.py worldhistory
```

### Terminal 5. EO

```bash
python -X utf8 scripts/research_collectors/crawl_youtube.py eo
```

### Terminal 6. 체인지그라운드

```bash
python -X utf8 scripts/research_collectors/crawl_youtube.py changeground
```

### Terminal 7. 유맛

```bash
python -X utf8 scripts/research_collectors/crawl_youtube.py yumat
```

### Terminal 8. EBS 다큐

```bash
python -X utf8 scripts/research_collectors/crawl_youtube.py ebsdocu
```

주의:

- `ebsdocu`는 영상 수가 많아 phase 1이 5~10분 걸릴 수 있다.

## 4. Channel Keys

| 키 | 채널 | 태그 |
| --- | --- | --- |
| `syuka` | 슈카월드 | 경제, 시사, 투자 |
| `pirates` | 지식해적단 | 군사, 방산, 역사 |
| `minani` | 지식인미나니 | 상식, 교양, 지식 |
| `boda` | 보다BODA | 다큐, 시사, 사회 |
| `techmong` | 테크몽 | IT, 기술, 테크 |
| `worldhistory` | 벌거벗은세계사 | 세계사, 역사, 교양 |
| `eo` | EO | 스타트업, 비즈니스 |
| `changeground` | 체인지그라운드 | 자기계발, 동기부여 |
| `yumat` | 유맛 | 경제, 부동산, 재테크 |
| `ebsdocu` | EBS다큐 | 기업, 산업, 패러다임 |

## 5. Output Contract

runtime collectors는 날짜별 `material_ssot` 버킷에 직접 쓴다.

하지만 operator와 stage authority는 아래 승격 경로를 기준으로 본다.

- raw ingest:
  - `material_ssot/10_research/80_ingest_raw/YYYY-MM-DD/`
- derived snapshots:
  - `material_ssot/10_research/40_analysis/market_snapshots/YYYY-MM-DD/`
- `로직_리서치/output`:
  - pointer-only legacy path

예상 산출물 패턴:

- `yt_{key}_all_{date}.json/csv`
- `yt_{key}_detail_{date}.json/csv`
- `yt_{key}_enriched_{date}.json/csv`
- 필요 시 raw companion jsonl

## 6. Operator Rule

- runbook authority는 이 문서가 가진다.
- runtime script execution은 `scripts/research_collectors`에서 한다.
- 결과를 문서나 stage SSOT에서 참조할 때는 반드시 `material_ssot` 승격 경로를 우선한다.
- 옛 `로직_리서치/ORDER_youtube_parallel.md`는 pointer-only legacy note로 유지한다.
