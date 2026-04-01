# KR Serial Platform Trends Corpus

Status: scaffold draft  
Date: 2026-04-01

이 폴더는 `카카오페이지 / 네이버 시리즈 / 문피아`의 공개 페이지에서 보이는
제목, 카피, 신작면, 랭킹면, 프로모션면 신호를 모으는 코퍼스다.

핵심 목적:

- 플랫폼이 지금 어떤 제목 포장과 소재를 미는지 저장
- `세상 이슈 코퍼스`와 별개로 `팔리는 패키징 코퍼스`를 확보
- 이후 LLM이 `소재`, `엔진`, `제목감`, `플랫폼 핏`으로 다시 해석

원칙:

- Python은 수집과 정규화만 담당
- 어떤 신호가 진짜 트렌드인지, 어떤 제목이 왜 먹히는지는 LLM이 판단
- 공개 페이지에서 보이는 신호만 수집

생성 명령:

```text
python -X utf8 scripts/build_platform_trend_corpus.py ^
  --output-root narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms
```

기본 산출물:

- `surface_registry.json`
- `platform_trend_entries.jsonl`
- `platform_trends.sqlite3`
- `platform_title_token_rollup.json`
- `platform_title_signal_rollup.json`
- `platform_cue_rollup.json`
- `collection_status.json`
- `raw/<platform>/<surface_id>.html`

현재 기본 수집면:

- 카카오페이지 웹소설 메뉴 공개 스크린
- 네이버 시리즈 `recent/top100/recommend/genre/specialFree`
- 문피아 `home/best/event`
