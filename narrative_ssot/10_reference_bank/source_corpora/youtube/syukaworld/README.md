# Syukaworld YouTube Corpus

Status: scaffold draft  
Date: 2026-04-01

Transition note:
- canonical root now lives at `material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld`
- this `narrative_ssot` path is kept only as transition residue during the bounded cutover
- rerun or refresh the corpus from the `material_ssot` root, not from here

이 폴더는 `@syukaworld` 채널을 내부 아이디어 코퍼스로 다루기 위한 자리다.

목표는 `영상 감상용 북마크`가 아니라 아래 3층을 고정하는 것이다.

- raw: 영상별 info JSON / caption JSON3
- normalized: SQLite / JSONL
- downstream: LLM이 아이디어 엔진으로 다시 증류할 수 있는 검색 기반 코퍼스

중요 원칙:

- Python은 수집과 포맷팅만 담당한다.
- 어떤 영상이 "좋은 아이디어"인지, 어떤 경제 신호를 어떤 재벌물 엔진으로 바꿀지는 LLM이 판단한다.
- 즉 이 코퍼스는 판단기보다 `시대 신호 저장소`다.

생성 스크립트:

```text
python -X utf8 scripts/build_youtube_channel_corpus.py ^
  --channel-url https://www.youtube.com/@syukaworld ^
  --channel-slug syukaworld ^
  --output-root material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld
```

기본 산출물:

- `channel_manifest.json`
- `video_index.json`
- `artifact_results.json`
- `ingest_status.json`
- `syukaworld.sqlite3`
- `video_lookup.jsonl`
- `transcript_documents.jsonl`
- `raw/videos/<video_id>/<video_id>.info.json`
- `raw/videos/<video_id>/<video_id>.ko.json3`

배치 재개 예시:

```text
python -X utf8 scripts/build_youtube_channel_corpus.py ^
  --channel-url https://www.youtube.com/@syukaworld ^
  --channel-slug syukaworld ^
  --output-root material_ssot/10_research/40_analysis/source_corpora/youtube/syukaworld ^
  --use-existing-index ^
  --artifact-batch-size 50
```

이 모드는 기존 `video_index.json`을 다시 쓰지 않고, 아직 자막이 없는 영상부터 50개씩 이어서 채운다.

권장 활용:

- 최근 경제 이슈를 제목/설명/자막 기준으로 키워드 검색
- 특정 이슈가 반복적으로 어떤 업종·국가·병목을 건드리는지 확인
- 이후 LLM이 `소재`, `병목`, `관문`, `회랑`, `대리만족 엔진`으로 다시 추출
