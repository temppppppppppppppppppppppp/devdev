# Modern Business Material Context Handoff

Date: 2026-04-01  
Track: narrative material-side  
Status: handoff snapshot for next login

## 1. Current Frame

- 지금 컨텍스트는 `재료 사이드 하네스` 기준의 `현대판타지 기업물 / 재벌물` 탐색이다.
- 목적은 감으로 소재를 던지는 게 아니라, `플랫폼에서 실제로 노출되는 포장 방식`과 `재료 코퍼스`를 바탕으로 다음 기획안의 방향을 잡는 것이다.
- 현재 메인 판단 축은:
  - `정보 바깥의 정보`가 초반에 있어야 함
  - `주인공 유능함`은 단순 정보 소유가 아니라 `병목 판독 + 권한 회수 + 판 뒤집기`
  - `재벌 스케일`은 살리되 손맛은 `오피스 파워`에서 뽑는 쪽이 유리

## 2. Rejected / Soft-Rejected Directions

- `빚이 보이는 사람` 계열은 현재 보류
  - 이유: 정보 능력 자체는 보이지만, 대리만족 엔진이 약해지기 쉬움
  - 살리려면 `빚`보다 `목줄 / 종속관계 / 권력 회수` 쪽으로 승격해야 했음
- `멋은 없고 돈만 되는 섹터` 리스트는 일단 후순위
  - 폐기물, 장례, 수처리 등은 구조적으로는 좋지만 현재는 `간판 멋`과 `즉시 흡인력`이 약하다고 판단

## 3. Important Creative Conclusions

### 3-1. What makes the idea feel high-quality

- 초반에는 독자가 이미 알고 있는 업종명이 아니라 `그 업계 뒤에 숨어 있는 진짜 돈줄 / 관문 / 병목`이 먼저 나와야 함
- 좋은 초반 정보는:
  - 듣자마자 그럴듯하다
  - 곧바로 돈/권력으로 연결된다
  - 정보 하나로 판 전체가 뒤집힌다

### 3-2. Main protagonist competency direction

- 지금 가장 강한 쪽은 `회랑 설계형`보다 조금 더 실전적인 `병목 판독형 + 오피스 파워형`
- 구체적으로는:
  - 누가 숫자를 숨기는지 먼저 본다
  - 결재가 어디서 막히는지 먼저 본다
  - 프로젝트가 어디서 터질지 먼저 본다
  - 작은 권한으로 큰 판을 뒤집는다

### 3-3. Current recommendation

- 현 시점 원픽은 `오피스 파워 + 재벌 외피 + 특정 산업 병목`
- 즉:
  - 재벌가 막장 승계물 단독보다
  - `대기업 본사 / 전략 / 재무 / 감사 / 프로젝트` 라인의 실무자형 주인공이 더 유리
- 추천 산업 병목 순위:
  - `반도체`
  - `제약`
  - `OTT / 미디어`
  - `데이터센터 / 전력`

## 4. Corpus / Asset State

### 4-1. Platform trend corpus

Public platform trend corpus is already built.

- Script: [build_platform_trend_corpus.py](/Users/wjjo/Desktop/글도비/scripts/build_platform_trend_corpus.py)
- README: [README.md](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/README.md)
- DB: [platform_trends.sqlite3](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/platform_trends.sqlite3)
- Raw entries: [platform_trend_entries.jsonl](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/platform_trend_entries.jsonl)
- Rollups:
  - [platform_cue_rollup.json](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/platform_cue_rollup.json)
  - [platform_title_signal_rollup.json](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/platform_title_signal_rollup.json)

Collection summary:

- surfaces: `61`
- entries: `2106`
- platform split:
  - `naver_series 942`
  - `kakaopage 720`
  - `munpia 444`

Observed top cues from the broad corpus:

- `천재`
- `회귀`
- `탑`
- `귀환`
- `재벌`
- `헌터`
- `돈`
- `미국`

Platform feel:

- 카카오: `천재 / 회귀 + OTT / 디렉터 / 스트리밍`
- 네이버: `천재 / 회귀 + 감정사 / 무당 / 반도체 / 취업`
- 문피아: `천재 / 회귀 / 재벌 / 각성 / 헌터 / 아포칼립스`

### 4-2. Business-only slice

The broad platform corpus has been narrowed into a business-only material slice.

- Script: [build_business_trend_slice.py](/Users/wjjo/Desktop/글도비/scripts/build_business_trend_slice.py)
- Slice README: [README.md](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/README.md)
- Slice DB: [business_trend_slice.sqlite3](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/business_trend_slice.sqlite3)
- Works: [business_trend_works.jsonl](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/business_trend_works.jsonl)
- Entries: [business_trend_entries.jsonl](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/business_trend_entries.jsonl)
- Rollup: [business_trend_rollup.json](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/business_trend_rollup.json)

Slice summary:

- entries: `116`
- deduped works: `98`

Work-bucket top line:

- `office_operator 37`
- `chaebol_power 30`
- `money_game 26`
- `industry_scale 21`
- `media_ip_business 14`
- `global_scale 9`

Current interpretation:

- `순수 재벌가 신분`보다 `회사 안에서 권한을 먹는 실무형`이 더 안정적
- `재벌`은 외피와 스케일을 주고
- `오피스 파워`가 실제 독자 손맛을 담당

Examples that survived the slice:

- `OTT 씹어먹는 천재 디렉터`
- `대기업 재무본부, 남대리는 계산 중`
- `반도체 대기업이 죽고 못사는 엔지니어가 되었다`
- `말단 사원이 너무 유능함`
- `감사팀장이 일을 너무 잘함`

Examples intentionally filtered out as noise:

- `편집자의 생존수칙`
- `극단적 연애사`
- `윈터 인 써머`
- `데뷔 못 하면 죽는 병 걸림`

## 5. Other Supporting Assets

### 5-1. Idea engine DB drafts

- [modern_business_idea_engine_db.draft.json](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/idea_engine_db/modern_business_idea_engine_db.draft.json)
- [modern_business_engine_selector.draft.json](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/idea_engine_db/modern_business_engine_selector.draft.json)

These are scaffold layers for:

- hidden-information engines
- reader backstab points
- power fantasy translations
- selector presets and concept recipes

### 5-2. Syukaworld corpus

Shukaworld is being treated as a `market radar / issue radar`, not as direct plot source.

- DB: [syukaworld.sqlite3](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/youtube/syukaworld/syukaworld.sqlite3)
- Video index: [video_index.json](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/youtube/syukaworld/video_index.json)
- Recent idea packets: [idea_packets_recent.jsonl](/Users/wjjo/Desktop/글도비/narrative_ssot/10_reference_bank/source_corpora/youtube/syukaworld/idea_packets_recent.jsonl)

Current remembered status:

- indexed videos: `2215`
- captioned videos currently saved in DB: low double digits range, with recent packet export already available

Use rule:

- `슈카 = 지금 세상에서 어디가 이상해지는가`
- `플랫폼 코퍼스 = 그걸 어떤 제목/엔진/포장으로 팔아야 하는가`

## 6. Active Work Candidate

Open file during handoff:

- [0_bi_office_checkup_next_day.json](/Users/wjjo/Desktop/글도비/bible/0_bi_office_checkup_next_day.json)

Current logline in focus:

> 전사 최대 프로젝트를 멈춘 건 3년차 말단 사원이었다. 건강검진 다음 날부터 어떤 프로젝트가 터질지, 누가 숫자를 숨기는지, 결재가 어디서 막히는지가 먼저 읽히기 시작한다.

Current judgment:

- 방향 자체는 살아 있음
- 다만 더 세게 만들려면 `재벌 외피`와 `특정 산업 병목`을 더 분명하게 붙이는 게 좋음

Preferred upgrade direction:

- `그룹 최대 투자 프로젝트를 멈춘 건 본사 전략기획실 3년차였다`
- 또는 `반도체 / 제약 / OTT / 데이터센터` 중 하나의 구체 섹터를 박아서
  숫자 숨김과 결재 병목이 추상 정보가 아니라 현장 권력으로 느껴지게 만들 것

## 7. Recommended Next Step After Return

Best immediate next step:

1. `office_checkup_next_day`를 기준 후보로 계속 밀기
2. business slice에서 살아남은 작품 결만 참고해
3. 아래 셋 중 하나를 바로 만들기

Option A:

- `logline 3종`
- `core engine 1종`
- `Block 1 spike 3종`

Option B:

- `source_manifest candidate pack`
- 기업물/재벌물에 필요한 `sector / role / bottleneck / crisis pool` 정리

Option C:

- 완전히 새 기획안 5개
- 단, 전부 `오피스 파워 + 재벌 외피 + 산업 병목` 조합으로만 제안

## 8. Do-Not-Lose Notes

- 지금은 `빚이 보인다`보다 `조직 병목이 먼저 읽힌다`가 더 낫다.
- 재벌물 독자 대리만족은 `숫자를 안다`가 아니라 `임원/계열사/결재선을 눌러 판을 뒤집는다`에서 나온다.
- `회사 안의 말단`을 주인공으로 두되, `그가 건드리는 판돈`은 그룹급이어야 한다.
- 초반 뒤통수는 `독자도 몰랐던 업계 구조`가 나와야 한다.
- `오피스 파워`는 손맛, `재벌 외피`는 스케일, `산업 병목`은 질감을 준다.
