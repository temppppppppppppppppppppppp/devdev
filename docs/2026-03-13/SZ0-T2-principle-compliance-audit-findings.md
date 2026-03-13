# SZ0-T2 Principle Compliance Audit Findings

> 작성일: 2026-03-13
> 상태: 3pass complete
> 대상: Stage 0 전체 7개 파일 (4,067줄)
> 감사 기준: 대원칙 4개 (절대 위반 금지)

---

## Executive Summary

Stage 0 모듈 전체(7개 파일)를 대원칙 4개 기준으로 3-pass 전수 검사한 결과:

- **확정 위반: 0건** (P0/P1 없음)
- **경계 판정 → 허용 확정: 6건** (데이터 정규화/구조 변환으로 판정)
- **해당 없음: 2건** (대원칙 3, 4는 Stage 0 범위에서 구조적으로 해당 없음)

Stage 0은 설계상 "초기 데이터 수집 및 포맷팅" 단계이므로, 대원칙 위반이 발생할 구조적 여지가 적다. LLM 호출은 전량 데이터 추출(Bible/NPC/WorldState/스타일) 목적이며, 품질 판단(score→pass/fail)이나 Director 우회는 존재하지 않는다.

---

## 대원칙별 전수 검사 결과

### 대원칙 1: Python은 수집만, 판단은 LLM이

| 파일 | 메서드 | 판정 | 사유 |
|------|--------|------|------|
| `preset_registry.py` | `_enforce_type()` | **허용** | 타입 강제(str→int 등). 데이터 포맷팅이지 판단 아님 |
| `preset_registry.py` | `normalize_hud()` | **허용** | 별칭→정규 필드명 매핑 + 타입 강제. 구조적 후처리 |
| `preset_registry.py` | `normalize_field_name()` | **허용** | 순수 매핑 테이블 조회 |
| `preset_registry.py` | `normalize_npc()` | **허용** | normalize_hud와 동일 패턴 |
| `preset_registry.py` | `_parse_korean_number()` | **허용** | "50억"→5000000000 변환. 데이터 파싱 |
| `preset_registry.py` | `detect_new_genre()` | **경계→허용** | 키워드 3개 이상 매칭 시 장르 감지. 이는 통계적 시그널 수집이며, 실제 장르 결정은 LLM(`detect_genre()`)이 담당. 이 메서드는 "힌트 제공"용 |
| `preset_registry.py` | `build_initial_hud()` | **허용** | 기본값 복사. 팩트 생성 아님 |
| `style_extractor.py` | `_analyze_statistics_v2()` | **경계→허용** | 문장 길이 평균으로 short/medium/long 분류, 1인칭/3인칭 빈도 비교로 POV 감지. 통계적 분류이며 품질 판단 아님 |
| `style_extractor.py` | `_score_sentence()` | **경계→허용** | 감각어/클리셰 키워드 기반 점수. 샘플 큐레이션(어떤 문장을 LLM에 보여줄지)용이며, 원고 합격/불합격 판단이 아님 |
| `style_extractor.py` | `_score_passage()` | **경계→허용** | `_score_sentence()`와 동일 패턴. 모범 문단 선별용 |
| `style_extractor.py` | `_analyze_rhythm()` | **허용** | 문장 길이 통계(trigram 패턴). 순수 데이터 수집 |
| `style_extractor.py` | `_curate_samples()` | **허용** | 점수 기반 정렬 후 상위 N개 선택. 데이터 필터링 |
| `reverse_expander.py` | `_extract_single_episode_bible()` | **허용** | LLM 호출 후 HUD 정규화. Python은 normalize_hud() 호출만 |
| `reverse_expander.py` | `_save_episode_bibles_to_db()` | **경계→허용** | hud→state_changes 자동변환. LLM이 추출한 hud_snapshot에서 capital/location 등을 state_changes 구조로 재배치. 새 데이터를 창조하지 않고 기존 필드를 재구조화만 함 |
| `reverse_expander.py` | `_enrich_arc_stubs_from_episode_bibles()` | **경계→허용** | episode_bibles에서 추출한 데이터로 arc stub 보강. LLM이 추출한 key_events/new_npcs/relationships를 Arc 단위로 집계. 새 데이터 창조 없음, 집계/정규화만 |
| `reverse_expander.py` | `_build_arc_stubs()` | **허용** | ep_num 기반 Arc 범위 계산 + stub 구조 생성. 순수 구조 변환 |
| `reverse_expander.py` | `detect_genre()` | **허용** | LLM 호출로 장르 판별. Python은 프롬프트 구성과 결과 파싱만 |
| `story_expander.py` | 전체 | **허용** | 모든 생성(concept분석/Bible/NPC/Treatment)이 LLM 호출. Python은 프롬프트 구성/JSON 파싱/저장만 |
| `stage01_helpers.py` | `validate_volume_boundaries()` | **경계→허용** | 미래 권 정보 누수 감지(regex + 키워드 카운트). 이는 구조적 검증(미래 참조 감지)이며, 품질 판단이 아님. REJECT/WARNING 반환은 Director에게 전달되어 최종 결정됨 |
| `stage01_helpers.py` | `stage_1_volumes()` | **허용** | retry 루프에서 `doc_len < 2000`으로 분량 부족 판단. 이는 "최소 분량 충족" 게이트이며, 내용 품질 판단이 아님. Director 주권과 무관 (Stage 1은 Analyst 단계) |
| `__init__.py` | 전체 | **허용** | UI 메뉴, 파일 I/O, LLM 호출 위임. 판단 로직 없음 |
| `spinner.py` | 전체 | **해당 없음** | 순수 UI 유틸리티. 데이터 처리 없음 |

### 대원칙 2: 팩트시트 수정 권한은 LLM만

| 파일 | 메서드 | 판정 | 사유 |
|------|--------|------|------|
| `preset_registry.py` | `build_initial_hud()` | **허용** | 프리셋 기본값으로 초기 HUD 구성. NPC 속성/세계관 설정 수정이 아닌, 빈 슬롯에 default를 채우는 초기화 |
| `preset_registry.py` | `normalize_hud()` | **허용** | LLM 출력의 필드명/타입을 정규화. 값 자체를 변경하지 않음 (enum 미매칭 시 default 복원은 타입 안전성 보장) |
| `reverse_expander.py` | `_save_state_logs_to_db()` | **허용** | LLM이 추출한 hud_snapshot을 DB에 저장. Python은 저장 형식 변환만 |
| `reverse_expander.py` | `_save_episode_bibles_to_db()` | **경계→허용** | LLM이 추출한 hud에서 state_changes 구조를 조립. 새 팩트 창조가 아닌 기존 데이터의 구조 변환 |
| `reverse_expander.py` | `_enrich_arc_stubs_from_episode_bibles()` | **경계→허용** | LLM이 추출한 episode_bible 데이터를 Arc 단위로 집계. 새 팩트 창조 없음. `state_changes.npc_deaths`의 cause가 "역설계 추출"로 하드코딩되어 있으나, 이는 출처 태그이지 팩트 판단이 아님 |
| `reverse_expander.py` | `_ensure_plot_roadmap()` | **허용** | Arc stub 구조를 Bible의 plot_roadmap에 삽입. 구조적 스캐폴딩이며 서사 내용 수정이 아님 |
| `story_expander.py` | `generate_bible()` | **허용** | LLM이 생성한 protagonist/NPC를 Bible 구조에 조립. Python은 dict 구성만 |
| `stage01_helpers.py` | `_s0_save_results()` | **허용** | Bible/Treatment를 DB에 저장하는 I/O 로직 |
| `stage01_helpers.py` | `_s0_handle_block_extension()` | **허용** | plot_roadmap을 Bible에 주입. 구조적 배치이며 서사 내용 수정이 아님 |

### 대원칭 3: 디렉터 주권주의

| 판정 | 사유 |
|------|------|
| **해당 없음** | Stage 0에는 Director 에이전트가 존재하지 않음. Stage 0은 초기 설정/역설계 단계이며, Director의 품질 심사 루프(Stage 4)와 구조적으로 분리됨. Stage 0의 출력물(Bible/Treatment/StyleGuide)은 이후 Stage에서 Director가 검토할 원재료이므로, Director 우회 위험이 없음 |

**StyleGuide→CW Director bypass 검토 (P2-8):**
- `StyleGuide.to_prompt()`는 CW 프롬프트에 문체 규칙을 주입하지만, 이는 "지시사항 전달"이며 Director 판정을 우회하지 않음
- Director는 CW 원고를 심사할 때 StyleGuide 준수 여부를 포함하여 판단하므로, Director 주권이 유지됨
- `to_prompt()`에 "위반 시 즉시 REJECT" 문구가 있으나, 이는 CW에 대한 프롬프트 지시이지 Python의 자동 REJECT가 아님

### 대원칙 4: 사망 캐릭터는 회상/언급만 허용

| 판정 | 사유 |
|------|------|
| **해당 없음** | Stage 0은 원고를 생성하지 않음. 사망 캐릭터 처리는 Stage 4의 TruthGate/Chief Writer/Director가 담당. Stage 0에서 `deceased` 플래그를 설정하거나 검사하는 코드는 없음. NPC 프리셋에 `status` 필드(alive/dead 등)가 존재하지만, 이는 스키마 정의일 뿐 행동 제어가 아님 |

---

## PASS 1 — 후보 수집

전체 7개 파일의 모든 public/private 메서드를 순회하여 대원칙 위반 후보를 수집했다.

### 후보 목록

| ID | 파일 | 메서드 | 대원칙 | 위반 유형 | 심각도(추정) |
|----|------|--------|--------|----------|-------------|
| C-1 | `preset_registry.py` | `normalize_hud()` L506-521 | P1, P2 | 별칭→정규화 + 타입 강제 + enum 미매칭→default | Low |
| C-2 | `preset_registry.py` | `detect_new_genre()` L593-628 | P1 | 키워드 3개 이상 매칭 시 장르 반환 | Low |
| C-3 | `style_extractor.py` | `_analyze_statistics_v2()` L455-503 | P1 | avg문장길이→short/medium/long 분류, POV 빈도→시점 결정 | Medium |
| C-4 | `style_extractor.py` | `_score_sentence()` L628-670 | P1 | 감각어/클리셰 점수 계산 | Low |
| C-5 | `style_extractor.py` | `_score_passage()` L554-570 | P1 | 문단 품질 점수 계산 | Low |
| C-6 | `reverse_expander.py` | `_save_episode_bibles_to_db()` L898-975 | P1, P2 | hud→state_changes 자동변환 | Medium |
| C-7 | `reverse_expander.py` | `_enrich_arc_stubs_from_episode_bibles()` L1046-1187 | P1, P2 | episode_bibles→Arc stub 자동보강 | Medium |
| C-8 | `stage01_helpers.py` | `validate_volume_boundaries()` L39-86 | P1, P3 | regex로 미래 권 누수 감지→REJECT 반환 | Medium |
| C-9 | `stage01_helpers.py` | `stage_1_volumes()` 내 `_vol_on_success()` L810-838 | P1 | `doc_len < 2000` → REJECT 판단 | Medium |
| C-10 | `style_extractor.py` | `_apply_pov_contract()` L352-374 | P1 | selected_pov → guide.pov 덮어쓰기 | Low |

---

## PASS 2 — 교차 검증

### C-1: `normalize_hud()` — 별칭 정규화 + 타입 강제

**호출 체인**: `_extract_single_episode_bible()` → LLM 응답 파싱 후 → `normalize_hud()` 호출
**행위**: "내공" → "internal_energy", "삼류" → enum 매칭 확인, str "50억" → int 5000000000
**판정**: **허용 (오탐)**
- 타입 변환과 필드명 정규화는 CLAUDE.md에서 명시적으로 위반이 아님으로 규정됨: "타입 변환, 필드명 정규화, 포맷 변환"
- enum 미매칭 시 default 복원은 타입 안전성 보장이며, LLM의 판단을 덮어쓰는 것이 아님

### C-2: `detect_new_genre()` — 키워드 기반 장르 감지

**호출 체인**: PresetRegistry 외부에서 호출 (현재 Stage 0 내부에서는 미사용)
**행위**: 콘텐츠에서 장르 키워드 3개 이상 매칭 시 새 장르 반환
**판정**: **허용 (오탐)**
- 반환값은 "감지 결과"이지 "결정"이 아님. 호출부에서 `activate_preset()`으로 활성화할지 여부를 결정
- 실제 장르 판별은 LLM(`ReverseExpander.detect_genre()`)이 담당
- CLAUDE.md 기준: "통계적 점수 계산"은 위반 아님

### C-3: `_analyze_statistics_v2()` — 통계적 분류

**행위**: 평균 문장 길이 < 25 → "short", 1인칭 빈도 > 3인칭 * 2 → "1인칭"
**판정**: **허용 (오탐)**
- CLAUDE.md 기준: "통계적 점수 계산"은 위반 아님
- 이 값들은 StyleGuide에 저장되어 CW 프롬프트에 주입됨. 품질 판단(pass/fail)이 아닌 스타일 기술(description)
- LLM Phase 4(`_deep_llm_analysis`)에서 tone/description_style 등이 덮어쓰여 최종값은 LLM이 결정

### C-4, C-5: `_score_sentence()`, `_score_passage()` — 점수 계산

**판정**: **허용 (오탐)**
- 용도: 샘플 큐레이션. "어떤 문장/문단을 LLM 분석용 샘플로 선택할지" 결정
- 원고 품질 판단(합격/불합격)과 무관. 점수는 내부 정렬용이며 외부에 노출되지 않음
- CLAUDE.md 기준: "LLM 응답의 구조적 후처리"에 해당

### C-6: `_save_episode_bibles_to_db()` — hud→state_changes 변환

**행위**: LLM이 추출한 hud_snapshot에서 capital/location/injuries/current_objective를 state_changes 딕셔너리로 재배치
**판정**: **허용 (오탐)**
- 새 데이터를 창조하지 않음. LLM이 추출한 필드값을 다른 구조로 옮기는 것
- `relationship_changes`도 hud의 relationships dict를 list of {"target", "to", "justification"} 형태로 변환할 뿐
- justification = "역설계 추출"은 출처 태그이지 판단이 아님
- 비유: JSON → CSV 변환과 동일한 구조 변환

### C-7: `_enrich_arc_stubs_from_episode_bibles()` — Arc stub 보강

**행위**: episode_bibles의 new_npcs/key_events/relationships를 Arc 범위로 집계하여 stub에 채움
**판정**: **허용 (오탐)**
- 집계(aggregation)이며 판단(judgment)이 아님
- 모든 원천 데이터는 LLM이 `_extract_single_episode_bible()`에서 생성한 것
- Python은 Arc 범위(ep_start~ep_end) 기준으로 그룹핑 + 중복 제거만 수행
- tactical_doc에 reveals 요약을 넣지만, 이는 `key_events`의 문자열 결합이며 새 내용 생성이 아님

### C-8: `validate_volume_boundaries()` — 미래 권 누수 감지

**행위**: regex로 "제N권" 패턴 검색 → N > vol_idx이면 REJECT 반환, 미래 키워드 3개 이상이면 WARNING
**판정**: **허용 (오탐)**
- 구조적 무결성 검증(structural validation)이며 품질 판단이 아님
- "이 텍스트에 미래 권 번호가 언급되었는가?"는 사실 확인(fact check)이지 "이 텍스트가 좋은가?"가 아님
- REJECT 반환은 `retry_with_feedback` 루프에서 재시도 트리거로 사용되며, 최종 결정은 Analyst의 재생성
- Stage 1에는 Director가 없으므로 대원칙 3(Director 주권)과도 무관

### C-9: `stage_1_volumes()` 내 `doc_len < 2000` 분량 게이트

**행위**: strategy_doc 길이가 2000자 미만이면 재시도
**판정**: **허용 (오탐)**
- 최소 분량 충족은 "품질"이 아닌 "형식" 검증
- 2000자 미만의 권 전략 문서는 내용이 아닌 분량 부족으로, 형식적 불완전성
- Stage 1에는 Director가 존재하지 않으며, Analyst가 재생성할 뿐

### C-10: `_apply_pov_contract()` — selected_pov 우선 적용

**행위**: 사용자가 선택한 POV(selected_primary_pov)를 LLM이 추출한 POV(extracted_pov)보다 우선 적용
**판정**: **허용 (오탐)**
- 사용자 의도가 LLM 추출 결과보다 우선하는 것은 정상적인 UX 패턴
- Python이 자체 판단을 내린 것이 아닌, 사용자 입력값을 반영한 것
- extracted_pov는 별도 필드에 보존되므로 LLM 결과가 소실되지 않음

---

## PASS 3 — 최종 확정 Findings

### 확정 위반: 0건

3-pass 전수 검사 결과, 대원칙 위반에 해당하는 코드는 Stage 0 전체에서 발견되지 않았다.

### 주의 사항 (INFO, 위반 아님)

| ID | 파일 | 내용 | 수준 |
|----|------|------|------|
| I-1 | `reverse_expander.py` L1152 | `npc_deaths`의 cause를 "역설계 추출"로 하드코딩. 팩트 판단은 아니지만, 실제 사망 원인이 아닌 출처 태그임을 주석으로 명시하면 가독성 향상 | INFO |
| I-2 | `reverse_expander.py` L927-940 | `_save_episode_bibles_to_db()`에서 hud→state_changes 필드 선택 로직이 장르별로 하드코딩됨("capital", "portfolio"). 장르 확장 시 누락 가능성 | INFO |
| I-3 | `preset_registry.py` L543-547 | `_enforce_type()`에서 enum 미매칭 시 default 복원. LLM이 의도적으로 새 enum 값을 출력한 경우 무시됨. 현재로서는 타입 안전성이 우선이므로 허용 | INFO |
| I-4 | `style_extractor.py` L469-490 | `_analyze_statistics_v2()`에서 POV 감지 임계값(first_person > third_person * 2)이 하드코딩. LLM Phase 4에서 덮어쓸 수 있으므로 영향 제한적 | INFO |

---

## 오탐 제거 요약

| 후보 ID | 최초 의심 | 최종 판정 | 제거 근거 |
|---------|----------|----------|----------|
| C-1 | 타입 강제로 LLM 출력 변경 | 허용 | CLAUDE.md "타입 변환, 필드명 정규화" 명시적 허용 |
| C-2 | Python이 장르 판단 | 허용 | 힌트 제공용, 실제 결정은 LLM |
| C-3 | Python이 POV/문장길이 결정 | 허용 | 통계적 분류, LLM Phase 4에서 덮어쓰기 가능 |
| C-4 | Python이 문장 품질 판단 | 허용 | 샘플 큐레이션용 내부 점수, 원고 합불 무관 |
| C-5 | Python이 문단 품질 판단 | 허용 | C-4와 동일 |
| C-6 | Python이 hud→state_changes 자동변환 | 허용 | 구조 변환(데이터 재배치), 새 데이터 창조 없음 |
| C-7 | Python이 Arc stub 자동보강 | 허용 | LLM 추출 데이터의 집계(aggregation), 판단 아님 |
| C-8 | Python이 REJECT 반환 | 허용 | 구조적 무결성 검증(미래 참조 감지), 품질 판단 아님 |
| C-9 | Python이 분량 부족 판단 | 허용 | 형식 검증(최소 분량), 내용 품질 판단 아님 |
| C-10 | Python이 POV 덮어쓰기 | 허용 | 사용자 선택 우선 적용, extracted_pov 보존 |

---

## 파일별 메서드 전수 목록

### `__init__.py` (810줄, StageZeroManager 14개 메서드)
- `__init__`, `_project_work_guard_path`, `_list_work_guard_templates`, `_build_default_work_guard_yaml`, `manage_work_guard`: UI/설정 — 해당 없음
- `show_menu`, `show_genre_menu`, `show_protagonist_config_menu`: UI 메뉴 — 해당 없음
- `run_new_project_flow`, `generate_from_concept`: LLM 호출 위임 — 허용
- `run_reverse_engineering_flow`: LLM 호출 위임 — 허용
- `import_bible`: 파일 I/O — 허용
- `manage_presets`: UI — 해당 없음
- `run_reference_analysis`: LLM 호출 위임 — 허용
- `get_active_schema`, `get_style_prompt`, `save_state`, `load_state`: 데이터 I/O — 해당 없음
- `_build_plot_roadmap_from_treatment`, `_ensure_plot_roadmap`: 구조 변환 — 허용

### `preset_registry.py` (739줄, PresetRegistry 16개 메서드)
- 전량 데이터 구조/스키마 관리 — 허용 (C-1, C-2 오탐 확인 완료)

### `story_expander.py` (600줄, StoryExpander 13개 메서드)
- 전량 LLM 호출 + JSON 파싱 + 저장 — 허용

### `reverse_expander.py` (1,212줄, ReverseExpander 24개 메서드)
- LLM 호출(7개): `detect_genre`, `extract_bible`, `_extract_protagonist`, `_extract_npcs`, `_extract_world_state`, `_extract_single_episode_bible`, `extract_style_guide` — 허용
- 데이터 I/O(6개): `load_drafts_*`, `save_all`, `persist_to_vectordb`, `persist_to_db` — 허용
- 구조 변환(5개): `_save_*`, `_build_arc_stubs`, `_ensure_plot_roadmap`, `_enrich_arc_stubs_from_episode_bibles` — 허용 (C-6, C-7 오탐 확인 완료)

### `style_extractor.py` (1,143줄, StyleExtractor 17개 메서드 + StyleGuide)
- LLM 호출(3개): `_deep_llm_analysis`, `_generate_anti_patterns`, `_llm_call` — 허용
- 통계 분석(3개): `_analyze_statistics_v2`, `_analyze_rhythm`, `_curate_samples` — 허용 (C-3~C-5 오탐 확인 완료)
- 스코어링(2개): `_score_sentence`, `_score_passage` — 허용 (샘플 큐레이션용)
- I/O/캐싱(5개): `extract_from_references`, `load_reference_manuscripts`, `_build_cache_meta`, `_cache_meta_matches` 등 — 허용
- StyleGuide: 데이터 클래스 + `to_prompt()` — 허용 (C-10 오탐 확인 완료)

### `spinner.py` (666줄)
- 순수 UI 유틸리티. 대원칙 검사 대상 외 — 해당 없음

### `stage01_helpers.py` (897줄, Stage01Helpers 14개 메서드)
- UI/메뉴(3개): `phase_0_recovery`, `stage_0_extended`, `extend_blocks` — 허용
- 핸들러(6개): `_s0_handle_*` — LLM 호출 위임 + I/O — 허용
- 검증(1개): `validate_volume_boundaries` — 허용 (C-8 오탐 확인 완료)
- Stage 1(1개): `stage_1_volumes` — 허용 (C-9 오탐 확인 완료)
- 구조 변환(3개): `_build_plot_roadmap_*`, `_ensure_plot_roadmap`, `_s0_save_results` — 허용
