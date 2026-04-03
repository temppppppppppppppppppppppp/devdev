# Stage 0 Material Collection 하네스 v1

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-12
> 역할: material 수집 우선순위, 좋은/나쁜 수집 방식, stop/go 기준 고정
> 정식 출력 경로: `treatments/preprocess/{work_id}/material_bundle_summary.json`

---

## 0. 이 문서의 목적

이 문서는 `무엇을 먼저 모아야 하는지`를 느슨한 감이 아니라 계약으로 고정한다.

핵심:

- source는 많이 모으는 것이 목적이 아니다
- 작품 전장에 직접 쓸 수 있는 재료만 남기는 것이 목적이다
- 자동화는 허용하지만, 사람이 읽고 버릴 것과 남길 것을 정해야 한다

---

## 1. 소스 우선순위

반드시 아래 순서로 본다.

1. 현재 작품의 기획안, onboarding, 사용자 메모, 기존 `phase0/TR/BI`
2. `test_material/material_bank.db`와 관련 query 도구
3. `test_material/json_outputs/`의 재료 팩
4. repo 내부 유사 장르 샘플
5. `material_ssot/10_research/20_fewshot_bank/`의 카드화된 실물 레퍼런스
6. `docs/실물기반 사각지대 테스트/원고/` 또는 사내 NAS 원고에서 추출한 실물 원고 레퍼런스
7. 부족할 때만 외부 1차/공식 자료

원칙:

- 작품 고유 설정보다 일반 업계 자료를 앞세우지 않는다
- DB 출력은 재료 은행이지 정본이 아니다
- 카드화되지 않은 raw NAS 원고는 참고 재료일 뿐이며 정본이 아니다
- raw 원고를 읽었으면 `Master Reference Card`로 정규화한 뒤에만 다음 단계로 넘긴다
- 외부 자료를 써도 긴 원문 복붙은 금지

---

## 2. 뽑아야 하는 재료

공통:

- 사건 후보
- NPC 후보
- 위기 후보
- 장소/기관 후보
- 용어 후보
- 현장 루틴 후보
- 금지 디테일 후보

프로파일별 핵심:

- `investment_market_profile`
  - 시장 이벤트, 규제, 자산 종류, 지배구조, 회수 구조
- `entertainment_media_profile`
  - 편성, 배급, 팬덤, 레이블 구조, 계약 충돌
- `medical_professional_profile`
  - 병원 위계, 집도권, 레퍼럴, 프로토콜, 증례/연구 라인
- `office_power_profile`
  - KPI, 예산, 결재선, 인사권, 프로젝트 오너십
- `tech_startup_profile`
  - 제품, 고객, 라이선스, 데이터, 배포, 기술 스택
- `urban_power_profile`
  - 능력 체계, 길드 규칙, 권리 구조, 공적 노출 리스크

## 2A. source checkpoint -> block-scale extraction 규칙

Stage 0는 source를 읽는 단계이면서, 동시에 설계 연료를 추출하는 단계다. 이 둘을 같은 말로 쓰면 안 된다.

- `episode checkpoint`
  - `ep1`, `ep5`, `ep10`, `ep20`, `last` 같은 source reading anchor다.
- `block-scale extraction`
  - `opening representative spike`, `first reward retention`, `authority gain route`처럼 설계에 바로 옮기는 추출 단위다.

번역 규칙:

- `ep1`에서 본 강한 장면은 곧바로 `Block 1 전체`가 아니다.
- Stage 0 정본에 옮길 때는 `opening representative spike 후보`, `opening block authority gain route`, `초반 보상 체류 방식`처럼 block-scale 언어로 다시 적는다.
- `TR Block 1 spike`라는 정확한 배치는 downstream planning / production 단계에서만 확정한다.

즉, source는 episode checkpoint로 읽고, 정본 산출물에는 block-scale 언어로 번역해서 적는다.

---

## 3. 실물 원고 / NAS 수집 추가 규칙

실물 원고는 `많이 읽었다`가 아니라 `기획 재료로 정규화했다`가 기준이다.

### 3.1 저장 위치

- raw 사본/메모: `docs/실물기반 사각지대 테스트/원고/`
- 카드화 결과 루트: `material_ssot/10_research/20_fewshot_bank/`
- 카드 sink root: `material_ssot/10_research/20_fewshot_bank/cards/`
- 카드 collection manifest: `material_ssot/10_research/20_fewshot_bank/reference_card_manifest.json`
- Stage 0 정식 출력물: 여전히 `treatments/preprocess/{work_id}/...`

### 3.2 Reference Card 저장 계약

실물 원고를 읽고 구조를 뽑았다면, 결과는 채팅에만 머무르면 안 된다.

- 기본 산출물은 `트랙 1개 = 카드 파일 1개`다
- 권장 파일명: `{slug}_{track}.md`
- 권장 track 값: `A`, `B`, `master`
- slug는 ASCII 소문자 + `_`를 권장한다
- 예: `dokshik_jaebeol3se_A.md`, `gim_daerineun_byeorakbuja_B.md`

카드 파일 최소 헤더:

- `# Reference Card :: {work_title} / {track}`
- `source_path: ...`
- `detected_work_title: ...`
- `save_target: ...`

카드 파일 최소 본문 섹션:

1. `SOURCE CHECK`
2. `Findings First`
3. `Master Reference Card v1`
4. `Slim Reference Card v1`
5. `현대 현판 적용 분해`
6. `마지막 3줄`

저장 원칙:

- 채팅 응답만 있고 sink 파일이 없으면 **미수집**으로 본다
- sink 파일이 생기면 `reference_card_manifest.json`의 해당 entry 상태를 갱신한다
- `source_manifest.reference_only_sources`에는 raw 경로가 아니라 저장된 카드 파일 라벨/경로를 넣는다

### 3.2A Manifest 상태 계약

`reference_card_manifest.json`의 상태는 아래 계약으로 고정한다.

- `status`
  - `pending`: 아직 source preflight 전
  - `source_checked`: source preflight PASS
  - `saved`: sink 파일 저장 완료
  - `audited`: Codex audit PASS
  - `rejected`: source drift / 구조 불량 / 오염으로 폐기
  - `synthesized`: `source_manifest` 또는 Director synthesis에 이미 흡수됨
- `audit_status`
  - `pending`: 아직 audit 전
  - `pass`: audit PASS
  - `fail`: audit FAIL
  - `needs_reaudit`: 수정 뒤 재감리 필요

전이 규칙:

- `pending -> source_checked`: source preflight PASS
- `source_checked -> saved`: sink 파일 존재 확인
- `saved -> audited`: Codex audit PASS + `audit_status = pass`
- `saved -> rejected`: 소스 오염, 보간, 구조 불량 확인
- `audited -> synthesized`: `source_manifest` 또는 Director 결과에 흡수
- `audit_status = fail`이면 `status`는 `audited`로 올리지 않는다
- `pending -> audited`, `pending -> synthesized` 직접 점프는 금지

### 3.3 소스 고정 Preflight

카드 작성 전에는 반드시 아래 4개를 먼저 확인한다.

1. 이번 턴에 읽을 정확한 source path
2. 폴더/파일에서 검출한 정확한 작품명
3. `ep1`, `ep5`, `ep10`, `ep20`, `last` 또는 동급 체크포인트 접근 가능 여부
4. 허용 source scope
   - `local_only`
   - `nas_only`
   - `local_plus_nas`

즉시 FAIL 조건:

- 작품명이 오더와 다르다
- 유사 제목 다른 작품으로 대체했다
- `ep1` 같은 opening checkpoint를 직접 못 읽었는데, 그것을 근거로 opening block 추출을 보간했다
- 허용되지 않은 source scope를 썼다

### 3.4 Operator 저장 규칙

가능하면 카드 파일을 sink 경로에 직접 저장한다.

직접 저장 권한이 없으면 아래 wrapper로만 응답한다.

- `=== BEGIN CARD {slug}_{track} ===`
- 카드 본문
- `=== END CARD {slug}_{track} ===`

운영자는 wrapper 응답을 sink 파일에 저장한 뒤에만 수집 완료로 간주한다.

### 3.5 수집 대상

- 현대 현판/기업물/재벌물/현대판타지 business-power 레퍼런스
- 현판 기업물의 `opening humiliation`, `opening representative spike`, `first reward retention`, `초반 30화 확장축`, `100화 이후 거물화 축`이 보이는 원고
- 유사 작품과 실패작을 함께 모아 `왜 먹히는지`와 `왜 버려야 하는지`를 같이 남길 수 있는 세트

### 3.6 최소 작업 단위

원고를 참고 소스로 쓰려면 최소한 아래를 남긴다.

1. 읽은 범위: `[1, 5, 10, 20, 50, 100, last]` 기준 체크포인트 또는 동급 근거
2. `Master Reference Card v1`
3. `Slim Reference Card v1`
4. `must_not_copy`와 `contamination_risk`
5. sink 경로에 저장된 카드 파일 또는 wrapper 저장본
6. `source_manifest.reference_only_sources`에 들어갈 요약 라벨
7. opening 관련 재료는 `Block 1` 단정이 아니라 `opening representative spike / first reward retention / authority gain route`로 재서술

### 3.7 금지

- NAS 경로만 적고 내용을 읽지 않은 채 참고 소스라고 주장하기
- raw 전문/epub/html을 그대로 `source_manifest`에 넣기
- 실물 원고를 읽고도 카드화 없이 “감이 왔다” 수준 메모만 남기기
- 채팅창 응답만 남기고 sink 파일 저장 없이 완료 처리하기
- 고유 인명, 대표 장면, 대표 설정을 베끼기 쉬운 형태로 추출하기

---

## 4. Master Reference Card v1

실물 원고/NAS 레퍼런스는 아래 최대 카드 스키마를 상한선으로 삼아 정규화한다.

```yaml
master_reference_card:
  source_meta:
    work_title:
    source_path:
    read_checkpoints: [1, 5, 10, 20, 50, 100, last]
    total_episodes:
    era_setting:
    primary_lane:
    secondary_lane:
    core_sector:
    adjacent_sectors:

  title_market:
    raw_title:
    title_grammar:
    hook_tokens:
    immediate_reader_promise:
    market_position:
    why_clicks_now:

  core_pitch:
    one_line_logline:
    what:
    how:
    core_fantasy:
    genre_positioning:
    endgame_image:

  protagonist_start:
    protagonist_type:
    social_starting_status:
    opening_humiliation:
    starting_deficit:
    timer_or_deadline:
    first_goal:
    why_reader_sides_with_him:

  protagonist_edge:
    edge_summary:
    edge_type:
    exclusivity_reason:
    semi_fantasy_degree:
    activation_trigger:
    cost_or_limit:
    failure_mode:
    concealment_method:
    reveal_payoff_method:

  philosophy_check:
    protagonist_first_evidence:
    dungee_point:
    first_reward:
    reward_stay_method:
    info_gap_owner:
    info_concealment:
    no_romance_compatibility:
    opening_representative_spike_timing:
    opening_representative_spike_type:
    block2_3_role:
    pacing_risk:

  opening_pacing:  # source checkpoint evidence zone; Stage 0 정본으로 넘길 때는 block-scale 언어로 다시 적는다.
    ep1_hook:
    ep1_first_saida:
    ep1_first_recognition:
    ep1_end_hook:
    block1_summary:
    block2_3_expansion:
    block4_5_expectation:

  business_engine:
    money_flow:
    power_flow:
    starting_capital:
    deal_types:
    core_operations:
    key_kpi_or_resource:
    stakeholders:
    realism_anchor:
    adjacent_expansion_logic:

  power_map:
    main_antagonists:
    gatekeepers:
    allies:
    recognition_channels:
    authority_gain_route:
    control_levers:

  escalation_map:
    growth_1_10:
    growth_11_30:
    growth_31_60:
    growth_61_100:
    growth_101_plus:
    sector_expansion_path:
    tycoon_path:

  scene_library:
    signature_spikes:
    negotiation_patterns:
    humiliation_reversal_patterns:
    authority_gain_patterns:
    expansion_scenes:
    money_shots:

  style_rhythm:
    exposition_method:
    dialogue_temperature:
    narration_texture:
    reward_interval:
    setback_rule:
    humor_ratio:
    business_explanation_style:

  reuse_guardrails:
    must_borrow:
    can_remix:
    must_not_copy:
    contamination_risk:
    reuse_score_10:
    director_notes:

  evidence:
    chapter_refs:
    supporting_moments:
    unresolved_questions:
```

운용 규칙:

- 작품당 카드 1개를 기본으로 한다
- 빈칸은 비워 두지 말고 모르면 `unknown`으로 적는다
- 긴 원문 인용보다 구조 요약을 우선한다
- `must_not_copy`와 `chapter_refs`는 비워 두면 안 된다
- `source_manifest`에는 카드 전체를 넣지 말고, 필요한 요약만 옮긴다

## 4A. Slim Reference Card v1

`Master Reference Card v1`은 최대 카드다. 실제 `source_manifest`와 Planning handoff에는 아래 `Slim Reference Card v1`만 넘긴다.

```yaml
slim_reference_card:
  source_label:
  work_title:
  track:
  usable_lane:
  usable_sector:
  opening_humiliation:
  protagonist_edge:
  what:
  how:
  opening_representative_spike:
  first_reward:
  growth_axis:
  authority_gain_route:
  sector_expansion_path:
  must_borrow:
  must_not_copy:
  contamination_risk:
  source_manifest_ready_label:
```

운용 규칙:

- `Slim Reference Card v1`은 반드시 저장된 `Master Reference Card v1`에서 파생한다
- raw 원고에서 바로 slim만 뽑고 master를 생략하면 안 된다
- `source_manifest.core_materials`, `crisis_pool`, `do_not_fake`는 slim card를 우선 입력으로 쓴다
- Director synthesis나 Phase 0 재료 주입에는 slim card를 우선 사용하고, 세부 근거가 필요할 때만 master card를 다시 연다
- 한 줄 요약이 아니라 `바로 옮겨 넣을 수 있는 필드`만 남겨야 한다

---

## 5. 좋은 수집 예시

```text
작품: 의학물
나쁜 수집: 병원은 정치가 있다 / 의사는 바쁘다 / 수술은 긴장된다
좋은 수집: 응급수술 승인 루프 / 주임교수-전임의-레지던트 위계 / 집도권 박탈 사유 / 증례 발표가 인사에 미치는 영향
```

좋은 이유:

- 추상 감정이 아니라 현장 규칙을 뽑았다
- `TR`에 바로 옮길 수 있다

---

## 6. 나쁜 수집 예시

```text
작품: 엔터물
source set: 유튜브 영상 몇 개, 막연한 업계 감
material bundle: 화제성, 논란, 팬덤, 계약
manual audit: 없음
```

나쁜 이유:

- 현장 구조가 없다
- 정본/참고 소스 구분이 없다
- 수동 감리가 없다

---

## 7. Stop / Go 기준

### Stop

- 재료가 전부 추상 명사
- 작품 전장과 직접 연결되는 사건/용어/관행이 없음
- profile과 재료가 충돌
- `source_manifest`에 바로 옮길 수 없는 재료만 있음
- 소스 고정 preflight가 없거나 FAIL이다
- 실물 원고/NAS를 읽었다고 주장하지만 `Master Reference Card`가 없음
- `Master Reference Card v1`은 있는데 `Slim Reference Card v1`이 없음
- 카드 본문이 채팅에만 있고 sink 파일이 없다
- collection manifest 상태가 `pending`에 머물러 있다
- raw 전문만 쌓여 있고 `must_not_copy`와 `contamination_risk`가 비어 있음

### Go

- 사건/NPC/위기/용어/현장 디테일이 작품 전장과 직접 연결됨
- `material_bundle_summary`로 압축 가능함
- 수동 감리 메모에서 “바로 쓸 수 있는 재료”가 분명함
- 소스 고정 preflight가 PASS다
- 실물 원고를 썼다면 카드화 결과가 `reference_only` 재료로 정규화돼 있음
- 카드화 결과가 sink 경로에 저장돼 있고 collection manifest가 갱신돼 있음
- `Slim Reference Card v1`이 `source_manifest`/Planning handoff에 바로 쓸 수 있는 수준으로 압축돼 있음

---

## 8. 수동 감리 메모 예시

```text
1. 바로 쓸 수 있는 것
- 레이블 계약 구조, 편성 슬롯 선점 규칙, 팬덤 역풍 트리거

2. 아직 비어 있는 것
- 플랫폼 수익 분배 세부치, 해외 판권 회수 루프

3. 상상으로 때우면 안 되는 것
- 방송 편성 승인 구조, 병원 집도권 위계, 본부 KPI 승인 루프
```

---

## 9. 호환 문서

현재 `docs/blockguide/modern_fantasy_material_harness.md`는 경로 호환용 미러 문서다.

현행 진실은 이 문서다.

---

## 10. 3-Pass Self Audit

### Pass 1. 계약 정합성

- material 수집 우선순위와 실물 원고 카드화 규칙을 현재 Stage 0 계약과 충돌 없이 정리했다.

### Pass 2. 실행 가능성

- 좋은/나쁜 예시, 실물 원고 수집 규칙, stop/go 기준을 넣어 낮은 성능 모델도 따라갈 수 있게 했다.

### Pass 3. 무결성

- UTF-8 only
- 정식 출력 경로 명시
