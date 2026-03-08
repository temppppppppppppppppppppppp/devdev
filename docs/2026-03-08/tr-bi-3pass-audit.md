# TR/BI 3PASS 정합성 감리 보고서 (2026-03-08)

## 대상
- TR 8종: `treatments/*_tr_block_070_draft.json`
- BI 8종: `bible/a_..._bi.json` ~ `bible/h_..._bi.json`

## 수행 기준
- TR 내부 3PASS
  - PASS1: 구조/필수 필드/블록 수/ID 형식
  - PASS2: 주인공 일관성, 시간 포맷(YYYY년 M월), 긴장도 범위(1~10)
  - PASS3: 회귀/빙의 타입 필드 정합성
- BI 내부 3PASS
  - PASS1: `validate_bible_structure` 통과
  - PASS2: `CoreIdentity.protagonist == FinanceHUD.Protagonist.actual_truth.name`
  - PASS3: `plot_roadmap` 길이/주인공 일관성
- TR↔BI 상호 3PASS
  - PASS1: 주인공/회귀타입 일치
  - PASS2: 길이/첫 블록/마지막 블록 일치
  - PASS3: `TR == BI.plot_roadmap` 전체 해시 동등

## 조치 사항
- 다음 4개 TR 핵심 식별 필드 정규화:
  - `treatments/aegis_city_tr_block_070_draft.json`
  - `treatments/aurora_media_tr_block_070_draft.json`
  - `treatments/northstar_logistics_tr_block_070_draft.json`
  - `treatments/quantum_bio_tr_block_070_draft.json`
- 정규화 항목:
  - `title` (블록 번호 포함)
  - `pov_character`
  - `time_span.in_story_time` (`2006? 1?` → `2006년 1월`)
  - `time_span.duration` (`7?` → `7일`)
  - `regression_ext.regression_type`, `incarnation_type`, `single_heir_policy`
- BI 재생성/동기화:
  - `scripts/generate_tr_bibles.py --include-empire-reborn` 실행

## 결과
- TR 내부 3PASS: **8/8 통과**
- BI 내부 3PASS: **8/8 통과**
- TR↔BI 상호 3PASS: **8/8 통과**
- 최종 판정: **모순/정합성 기준 충족**

## 잔여 리스크(품질)
- 다수 TR 본문에 `???` 플레이스홀더 텍스트가 남아 있음.
- 본 항목은 “구조/정합성” 문제는 아니지만, 이후 원고 품질 단계에서 의미 복원/치환 작업이 필요함.
