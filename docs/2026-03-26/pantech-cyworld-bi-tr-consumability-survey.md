# 07_pantech_cyworld_reborn BI/TR Consumability Survey

Date: 2026-03-26
Type: compact artifact-shape survey
Scope: current consumer-contract consumability of:
- `bible/_quarantine/07_pantech_cyworld_reborn_bi.json`
- `treatments/_quarantine/07_pantech_cyworld_reborn_tr_block_070_draft.json`

## Findings

### 1. TR는 현재 하네스에서 바로 소비 가능한 상태다

- TR 경로: `treatments/_quarantine/07_pantech_cyworld_reborn_tr_block_070_draft.json`
- shape: `list` 70 entries
- item shape: `block_id`, `title`, `content`, `stakes`, `power_shift`, `relationship_delta`, `foreshadow`, `callback`, `emotional_beat`, `tension_level`, `pov_character`, `location`, `time_span`, `genre_ext`, `regression_ext`
- `validate_treatment_structure()` 결과: `valid=True`, `errors=0`, `warnings=0`
- `build_plot_roadmap_from_treatment()` 결과:
  - 70 entries
  - `block_no` 70개 모두 보장
  - unique `block_no` 70개
  - `validate_plot_roadmap_entries()` 경고 0개
  - `content` dict 70/70 유지

판정:
- TR 자체는 current ingress/runtime contract에 맞다.
- 현재 하네스가 그대로 소비할 수 있다.

### 2. BI는 구조 자체는 유효하지만, 내장 `plot_roadmap`은 단독 소비 기준으로는 미완이다

- BI 경로: `bible/_quarantine/07_pantech_cyworld_reborn_bi.json`
- shape: top-level `dict`
- wrapper: `MasterBible` 존재
- `MasterBible` 주요 키:
  - `ProjectData`
  - `protagonist_config`
  - `FinanceHUD`
  - `WorldState`
  - `AssetLibrary`
  - `Seeds`
  - `HistoricalEvents`
  - `GenreRules`
  - `plot_roadmap`
- `validate_phase0_files(bi, tr)` 결과:
  - `overall_valid=True`
  - `bible_valid=True`
  - `treatment_valid=True`
  - `block_count=70`

하지만 BI 내부 `MasterBible.plot_roadmap`를 직접 검사하면:
- list 길이 70
- `content` dict 70/70 유지
- `block_no` 존재 0/70
- `validate_plot_roadmap_entries()` 경고 70개
  - 전부 `block_no missing`

판정:
- BI 파일 전체 구조는 유효하다.
- 그러나 BI 안에 들어 있는 기존 `plot_roadmap`만 떼어 Stage 2-ready handoff로 쓰기엔 아직 부족하다.

### 3. 현재 소비 가능성은 `BI+TR pair` 기준으로는 PASS다

현재 runtime 기준 핵심은 BI의 기존 내장 roadmap이 아니라:
- TR을 읽고
- `build_plot_roadmap_from_treatment()`로 canonical roadmap을 다시 만들고
- 그 결과를 handoff/DNA sync에 쓰는 경로다

이 pair에 대해 확인된 사실:
- `validate_phase0_files(bi, tr)` 통과
- TR 기반 canonical roadmap 생성 통과
- Stage 2 readiness warning 0

따라서 현재 하네스 관점에서의 실제 판정은:
- `TR`: 소비 가능
- `BI`: 구조 유효
- `BI+TR pair`: 소비 가능

### 4. `protagonist_config`는 최소 소비는 가능하지만 정보 밀도는 낮다

현재 `protagonist_config` 키:
- `world_origin`
- `incarnation_type`
- `regression_point`

영향:
- Stage 2 compact summary는 `world_origin`, `incarnation_type`를 읽을 수 있다
- 그러나 `pov`, `external_pov_insert_policy`, `name` 등은 비어 있어 일부 상위 컨텍스트는 약해진다
- 즉 shape blocker는 아니고, 품질/가이드 밀도 측면의 약점이다

### 5. 현재 상태는 `active canonical`이 아니라 `_quarantine` 보관 상태다

두 파일 모두 `_quarantine` 아래 있다.

의미:
- 파일 내용/shape 자체는 조사 가능하고, pair 기준 소비도 가능하다
- 하지만 운영상 바로 “현재 활성 정본”으로 간주할 상태는 아니다

## Evidence

- `validate_treatment_structure(tr)` -> PASS
- `validate_phase0_files(bi, tr)` -> PASS
- `build_plot_roadmap_from_treatment(tr)` -> 70 entries, `block_no` 70/70, warnings 0
- `validate_plot_roadmap_entries(bi.MasterBible.plot_roadmap)` -> warnings 70 (`block_no missing`)
- `modules/core/stage2_preflight.py:470-510`
  - `protagonist_config`는 `world_origin`, `incarnation_type`, `pov`, `external_pov_insert_policy`를 읽음
- `modules/core/stage4_orchestrator.py:2161-2180`
  - `protagonist_config`에서 `name`, `world_origin`, `incarnation_type`를 읽음

## Classification

### Already Consumable
- TR list shape
- TR -> canonical `plot_roadmap`
- BI+TR pair through current handoff path

### Weak But Not Blocking
- sparse `protagonist_config`
- `_quarantine` placement

### Not Yet Standalone-Ready
- BI 내부 기존 `plot_roadmap`의 direct Stage 2-ready 사용

## Recommendation

현재 하네스로 쓰려면 이 pair는 다음처럼 취급하는 게 맞다.

- `07_pantech_cyworld_reborn_tr_block_070_draft.json`을 authoritative handoff source로 사용
- BI는 wrapper/asset/state source로 사용
- runtime에서는 BI의 기존 `plot_roadmap`를 그대로 믿지 말고, TR에서 canonical roadmap을 재생성하는 현재 경로를 사용

대량 소비 기준 판정:
- `BI+TR pair`: 가능
- `BI standalone roadmap`: 비권장

---

- TR consumability: pass
- BI standalone roadmap readiness: mixed
- BI+TR pair consumability: pass
