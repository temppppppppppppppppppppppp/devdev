# Genre Expansion Family-Native Ingress Normalizer Wave 1 Execution SSOT

Date: 2026-03-26
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-26/genre-expansion-family-native-ingress-normalizer-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/genre-expansion-family-native-ingress-normalizer-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `a8034b1efdbe01a49effabf92cc9f736ebbca991`
- Baseline Dirty Summary: `dirty: 1 untracked doc (docs/2026-03-26/genre-expansion-wuxia-ingress-normalizer-design-memo.md)`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-26/genre-expansion-wuxia-consumer-contract-context.md`
- `docs/2026-03-26/genre-expansion-wuxia-ingress-normalizer-design-memo.md`
Evidence Artifacts:
- `treatments/wuxia_heavenly_physician_tr_block_070_draft.json`
- `bible/0_bi_wuxia_heavenly_physician.json`
- `modules/core/response_schemas.py`
- `modules/core/stage0_handoff.py`
- `modules/core/project_manager.py`
- `modules/core/stage01_helpers.py`
Side-Effect Coverage: covered

## 1. Intent

- family-native raw `BI/TR`를 현재 runtime internal contract로 안전하게 승격시키는 bounded ingress wave를 실현한다.
- 현재 장르 확장 문제를 `무협 downstream 미지원`으로 풀지 않고, `ingress contract mismatch`로 풀도록 고정한다.
- `golden canaria` baseline을 깨지 않으면서, raw pair가 `list[block] + Stage2-ready plot_roadmap + minimally compatible protagonist_config` 경로에 들어오게 만든다.

## 2. Baseline Facts

- 현재 runtime ingress는 사실상 `list` treatment를 기대한다.
  - `validate_treatment_structure()`는 list가 아니면 reject한다. `modules/core/response_schemas.py:827-828`
- Stage 0 handoff는 dict treatment를 받을 때 `treatments`만 풀고 `blocks`는 풀지 않는다. `modules/core/stage0_handoff.py:20-24`
- DNA sync 경로는 treatment를 list처럼 직접 순회한다. `modules/core/project_manager.py:842-845`
- 현재 `protagonist_config` 저장은 merge가 아니라 overwrite다. `modules/core/stage01_helpers.py:307-313`
- Stage 2 payload consumer는 이미 `content.context/event_villain/solution/reward`를 읽을 수 있다. `modules/core/stage0_handoff.py:85-127`
- 따라서 현재 motivating sample의 핵심 blocker는 `무협 payload 자체`보다 `ingress normalization 부재`다.

## 3. Scope

Included:
- `modules/core/response_schemas.py`
- `modules/core/stage0_handoff.py`
- `modules/core/project_manager.py`
- `modules/core/stage01_helpers.py`
- 관련 bounded regression tests
  - `tests/test_stage01_helpers.py`
  - `tests/test_stage2_preflight_helpers.py`
  - 필요 시 ingress 전용 소형 테스트 파일 1개 추가

Excluded:
- `main_a.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- Stage 3/4 prompt or runtime changes
- raw 장르별 schema를 Stage 2/3/4가 직접 다중지원하도록 widening
- `martial_ext`, `realm_before/after`, `martial_event`의 consumer widening
- DB schema
- JSONL/log path 변경
- UI/dashboard/operator flow redesign

## 4. Pass 1. Inventory Summary

- 현재 ingress mismatch family는 4개다.
  - list-only treatment validation
  - `dict.blocks` 미지원
  - DNA sync list 가정
  - protagonist_config overwrite
- Stage 2 readiness 자체는 `plot_roadmap`가 canonical shape로만 들어가면 통과 가능성이 높다.
- 따라서 이번 wave는 `downstream widening`이 아니라 `ingress canonicalization`만 치는 것이 ROI가 가장 높다.

## 5. Pass 2. Semantic Classification

- Class A. Treatment shape admission
  - `list`
  - `dict.blocks`
  - `dict.treatments`
  를 하나의 canonical block list로 정규화

- Class B. Runtime roadmap promotion
  - normalized block list를 `plot_roadmap`로 승격
  - `block_no`를 보장
  - raw payload field는 최대한 보존

- Class C. Merge-safe protagonist config
  - runtime required subset은 보장
  - family-native protagonist field는 보존

- Class D. Explicit defer
  - Stage 2/3/4 raw multi-schema direct consumption은 열지 않음
  - 장르 특화 payload widening은 후속 wave로 defer

## 6. Side-Effect Map

- file writes / artifacts:
  - production code 4파일 내외
  - tests 2~3파일
- DB / schema / transaction boundaries:
  - schema 변경 없음
  - 기존 `save_v20_anchor("bible", ...)` 호출 경로만 유지
- JSONL / log / audit sinks:
  - 신규 sink 없음
- console / UI / operator output:
  - 기존 Stage 0/Phase 0 저장 로그 유지
  - 필요 시 validation reason 문구만 bounded 보강 가능
- rollback / recovery / retry:
  - not applicable
- cache / global state:
  - none
- bootstrap fallback / config-env mutation:
  - none

## 7. Realization Architecture

핵심 구조는 다음 한 줄이다.

`raw BI/TR -> ingress normalizer -> canonical runtime contract -> existing Stage 2/3/4`

권장 realization shape:

1. shared treatment normalizer
- 입력 허용:
  - `list`
  - `dict.blocks`
  - `dict.treatments`
- 출력:
  - `list[dict]`

2. roadmap builder alignment
- normalized block list에서 `plot_roadmap` 생성
- `block_no` 보장 규칙:
  - 기존 `block_no` 우선
  - 없으면 `block`/`block_id`에서 추출 시도
  - 실패 시 enumeration index fallback

3. DNA sync alignment
- `force_sync_v25_dna()`도 normalized block list만 보게 정렬

4. protagonist_config merge-safe save
- overwrite 금지
- runtime subset merge
- family-native field 유지

## 8. Execution Tranches

1. Tranche A. Treatment shape normalization
- `response_schemas.py`와 `stage0_handoff.py`에서 canonical block list normalization 경로 추가
- `list`, `dict.blocks`, `dict.treatments` admissive support

2. Tranche B. plot_roadmap / DNA sync alignment
- `build_plot_roadmap_from_treatment()`를 normalized input 기준으로 정렬
- `project_manager.py` DNA sync loop를 normalized list 기준으로 정렬
- `block_no` 보장

3. Tranche C. protagonist_config merge-safe save
- `stage01_helpers.py`에서 runtime subset merge
- 기존 family-native field 보존

4. Tranche D. Bounded regression tests
- golden list treatment path non-regression
- dict.blocks ingress success
- dict.treatments ingress success
- roadmap `block_no` 보장
- protagonist_config overwrite 회귀 방지

## 9. Acceptance Criteria

- raw treatment가 `list`, `dict.blocks`, `dict.treatments` 중 하나면 canonical block list로 정규화된다
- normalized treatment에서 생성된 `plot_roadmap`가 `block_no`를 보장한다
- 기존 golden baseline list path가 깨지지 않는다
- Stage 2 readiness가 title/summary-only warning이 아니라 consumer-backed payload를 읽을 수 있는 shape로 승격된다
- `protagonist_config` 저장 시 기존 family-native field가 불필요하게 소실되지 않는다
- Stage 2/3/4가 raw family schema를 직접 다중지원하도록 widening되지 않는다

## 10. Verification Plan

- `python -m py_compile modules/core/response_schemas.py modules/core/stage0_handoff.py modules/core/project_manager.py modules/core/stage01_helpers.py`
- low-memory targeted pytest:
  - `set PYTHONIOENCODING=utf-8 && pytest tests/test_stage01_helpers.py -q`
  - `set PYTHONIOENCODING=utf-8 && pytest tests/test_stage2_preflight_helpers.py -q`
  - 신규 소형 ingress test가 생기면 해당 파일만 추가 실행
- `python scripts/check_utf8_hygiene.py modules/core/response_schemas.py modules/core/stage0_handoff.py modules/core/project_manager.py modules/core/stage01_helpers.py tests/test_stage01_helpers.py tests/test_stage2_preflight_helpers.py docs/2026-03-26/genre-expansion-family-native-ingress-normalizer-wave1-execution-ssot.md docs/temp/genre-expansion-family-native-ingress-normalizer-wave1-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

후속 bounded canary:

- control canary: `golden canaria`
- adapter canary: `wuxia_heavenly_physician`

## 11. Guardrails

- raw sample 하나에 맞춘 하드코딩 금지
- 무협 전용 field consumer widening 금지
- Stage 2/3/4 prompt 변경 금지
- Stage 3/4 readiness 문제를 ingress wave에 섞지 않기
- `golden canaria` control 경로를 깨면 이 wave는 실패로 본다
- `protagonist_config` merge는 additive/merge-safe만 허용하고 destructive overwrite를 만들지 않는다

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - 구현 완료
  - verification 완료
  - closure audit 완료
  - 이후 temp mirror 삭제
- roadmap dependency:
  - none at open time; single active execution item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- queue-state sync: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: implementation 직전 canonical SSOT를 current workspace 기준으로 다시 3-pass audit하고 confidence 95% 이상을 재확인한 뒤 patch 시작

---

## 3-Pass Audit Notes

- Pass 1: scope를 ingress normalization과 merge-safe save로 제한하고 downstream widening을 명시적으로 제외했다
- Pass 2: consumer-contract memo, 설계 메모, live code spot-check를 대조해 이번 wave가 raw sample hardcoding으로 흐르지 않도록 정리했다
- Pass 3: 바로 구현 가능한 tranche와 검증 계획, control/adapter canary split을 명시했다
- Confidence: 0.97

## Closure Note

Date: 2026-03-26
Closure Status: closed
Closure Basis:
- no blocking mismatch between canonical SSOT, realized code, and bounded test surface
- required tranche behavior exists in:
  - `modules/core/stage0_handoff.py`
  - `modules/core/response_schemas.py`
  - `modules/core/project_manager.py`
  - `modules/core/stage01_helpers.py`
- excluded surfaces remained untouched:
  - `main_a.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_preflight.py`
  - Stage 3/4 runtime and prompt files
  - DB schema / JSONL path naming / UI

Verification Evidence:
- `python -m py_compile modules/core/response_schemas.py modules/core/stage0_handoff.py modules/core/project_manager.py modules/core/stage01_helpers.py`
- `pytest tests/test_stage01_helpers.py tests/test_stage0_handoff_ingress.py tests/test_stage2_preflight_helpers.py -q` -> `101 passed`
- prior split verification also passed cleanly:
  - `pytest tests/test_stage01_helpers.py -q` -> `50 passed`
  - `pytest tests/test_stage0_handoff_ingress.py -q` -> `5 passed`
  - `pytest tests/test_stage2_preflight_helpers.py -q` -> `46 passed`
- `python scripts/check_utf8_hygiene.py ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

Residual Risks:
- `block_id` / `block` numeric parsing still assumes the first positive integer token is the intended `block_no`
- ingress admission remains intentionally bounded to `list`, `dict.blocks`, and `dict.treatments`
- `protagonist_config` save uses shallow merge, not deep nested merge

Follow-up:
- no additional execution SSOT is opened by this closure
- next proof step is control + adapter canary, not further ingress widening
