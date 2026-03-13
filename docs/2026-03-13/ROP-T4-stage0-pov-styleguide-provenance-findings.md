# ROP-T4 Stage0 POV / StyleGuide Provenance Findings

작성일: 2026-03-13  
터미널: `T4`  
상태: `PASS3 complete`  
범위: `modules/core/stage0/__init__.py`, `modules/core/stage0/style_extractor.py`, `modules/core/stage01_helpers.py`, `modules/core/project_support.py`, `style_guide.json`, style cache meta, planning/validation handoff, operator-facing support surface

## Executive Summary

- 현재 코드와 테스트는 `selected_primary_pov / extracted_pov / effective_primary_pov / external_pov_insert_policy` 계약을 갖고 있다.
- 그러나 실제 operator-facing artifact는 아직 그 계약으로 refresh되지 않았다.
- 2026-03-13 04:41:38~05:00:00 KST에 생성된 `projects/기록용/{00,01,03,0w}/stage0_output/style_guide.json`, 동일 시각대 `project_data.db`의 `style_guide` anchor, `config/style_references/investment/style_guide.json` cache는 모두 구형 포맷이다.
- 반면 planning / Stage 4 runtime은 Bible POV 우선 보정으로 `혼합 / 3인칭 / 전지적 / 1인칭`을 실제 prompt에 사용했다.
- 따라서 이번 트랙의 핵심 retained finding은 `생성 품질 결함`이 아니라 `evidence-layer drift`와 `stale artifact refresh proof 부재`다.

## 조사 범위

- 코드
  - `modules/core/stage0/style_extractor.py`
  - `modules/core/stage0/__init__.py`
  - `modules/core/stage01_helpers.py`
  - `modules/core/project_support.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/api/bridge_server.py`
  - `modules/core/quality_sidecar_bootstrap.py`
- 테스트
  - `tests/test_stage0_pov.py`
  - `tests/test_stage0_work_guard_style_cache.py`
  - `tests/test_project_support.py`
  - `tests/test_stage01_helpers.py`
  - `tests/test_stage2_preflight.py`
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_stage4_post_processor.py`
  - `tests/test_quality_sidecar_bootstrap.py`
- 실제 artifact / runtime proof
  - `projects/기록용/00`, `01`, `03`, `0w`
  - `config/style_references/investment/style_guide.json`
  - 해당 프로젝트 session log, `llm_io.jsonl`, `project_data.db`

## PASS 1 - 후보 수집

### 후보 A - live Stage 0 artifact와 anchor가 새 POV provenance를 보존하지 않는다

- 확신도: `HIGH`
- 태그: `artifact`, `provenance`, `runtime-proof`

### 후보 B - operator-facing support surface가 raw file POV를 계속 노출한다

- 확신도: `MED`
- 태그: `artifact`, `provenance`, `wiring`

### 후보 C - style cache가 구형 payload를 조용히 재사용할 수 있다

- 확신도: `LOW`
- 태그: `artifact`, `provenance`

### 후보 D - planning / Stage 4 runtime도 stale POV를 그대로 쓸 수 있다

- 확신도: `LOW`
- 태그: `provenance`, `runtime-proof`

## PASS 2 - 교차 검증

### 교차 검증 A - code/test 계약 vs live artifact

- `modules/core/stage0/style_extractor.py:288-350,352-374,921-1015`는 cache meta와 `StyleGuide`에 `selected_primary_pov`, `effective_primary_pov`, `external_pov_insert_policy`, `extracted_pov`를 반영한다.
- `modules/core/stage0/__init__.py:626-669`는 Stage 0 실행 시 `protagonist_config`의 POV 계약을 extractor에 넘기고 project `stage0_output/style_guide.json`을 쓴다.
- `modules/core/stage01_helpers.py:388-398,492-497,625-627`는 같은 `style_guide`를 DB anchor로도 저장한다.
- 테스트도 이를 잠근다.
  - `tests/test_stage0_work_guard_style_cache.py`
  - `tests/test_project_support.py`
  - `tests/test_stage0_pov.py`
  - `tests/test_stage01_helpers.py`
- 하지만 실제 artifact는 그렇지 않다.
  - `projects/기록용/00/stage0_output/style_guide.json` mtime `2026-03-13 04:41:38 KST`
  - `projects/기록용/01/stage0_output/style_guide.json` mtime `2026-03-13 04:46:16 KST`
  - `projects/기록용/03/stage0_output/style_guide.json` mtime `2026-03-13 05:00:00 KST`
  - `projects/기록용/0w/stage0_output/style_guide.json` mtime `2026-03-13 04:47:23 KST`
  - 네 파일 모두 `pov=1인칭`, `selected_primary_pov/effective_primary_pov/external_pov_insert_policy/extracted_pov` 없음
  - 네 프로젝트 `project_data.db`의 `anchors.style_guide`도 같은 구형 키셋만 갖고 `pov=1인칭`
  - `config/style_references/investment/style_guide.json`은 `_cache_meta.cache_meta_version=s0-style-cache-v1`, POV provenance key 없음

### 교차 검증 B - stale artifact vs live runtime handoff

- `modules/core/project_support.py:161-181,185-220`는 planning/summary가 `resolve_project_pov_contract()`로 Bible POV와 style anchor를 조합해 `effective_pov`를 만든다.
- `tests/test_project_support.py:31-81`, `tests/test_stage2_preflight.py:328-355`는 StyleGuide raw POV보다 Bible POV를 우선 쓰는 요약 계약을 검증한다.
- `modules/core/stage4_orchestrator.py:1495-1517`는 `StyleGuide POV != Bible POV`면 `[TF-31-2]` 경고 후 Bible POV를 우선 적용한다.
- 실제 runtime log와 prompt도 이 보정을 증명한다.
  - `projects/기록용/00/logs/session_20260313_043840.log` -> `StyleGuide POV(1인칭) ≠ Bible POV(전지적)`
  - `projects/기록용/01/logs/session_20260313_044504.log` -> `StyleGuide POV(1인칭) ≠ Bible POV(혼합)`
  - `projects/기록용/03/logs/session_20260313_045921.log` -> `StyleGuide POV(1인칭) ≠ Bible POV(3인칭)`
  - 각 프로젝트 `logs/session/llm_io.jsonl`의 `StyleGuide 문체/anti-AI 참고` 블록은 각각 `시점=전지적`, `시점=혼합`, `시점=3인칭`, `시점=1인칭`을 사용했다.
- 따라서 후보 D는 `runtime generation regression`으로는 확정하지 않는다. 문제는 runtime 보정이 artifact drift를 숨긴다는 점이다.

### 교차 검증 C - stale cache silent reuse 여부

- `modules/core/stage0/style_extractor.py:338-350`는 `cache_meta_version`, `prompt_contract_hash`, `selected_primary_pov`, `external_pov_insert_policy`까지 일치해야 cache hit로 본다.
- `tests/test_stage0_work_guard_style_cache.py:37-91`는 prompt hash mismatch와 POV 계약 mismatch에서 재분석이 강제되는지 검증한다.
- 실제 cache는 `s0-style-cache-v1`이므로 현재 코드 기준 다음 rerun에서 그대로 재사용되지 않는다.
- 따라서 후보 C는 제거한다.

### 교차 검증 D - operator-facing support surface

- `modules/core/project_support.py:268-320`는 file 기반 `inspect_project_support_assets()`에서 `effective_pov`를 계산하지만, payload에는 raw `pov`와 `effective_pov`를 병렬로 둔다.
- `modules/api/bridge_server.py:523-536`는 operator detail에 `tone=`와 `pov=`만 노출한다. `effective_pov`, `selected_primary_pov`, `extracted_pov`, `external_pov_insert_policy`는 쓰지 않는다.
- `modules/core/quality_sidecar_bootstrap.py:152-158`는 `style_tone`, `style_pov`만 health payload로 싣고 `effective_pov`를 버린다.
- 테스트는 이 경계를 잠그지 않는다.
  - `tests/test_project_support.py:89-120`는 `inspect_project_support_assets()` 자체의 `effective_pov`를 확인한다.
  - `tests/test_quality_sidecar_bootstrap.py`는 `style_pov` 의미를 검증하지 않는다.
  - `tests/test_process_runner.py`의 bridge 검증은 style detail surface를 보지 않는다.
- 따라서 후보 B는 retained finding으로 승격한다.

## PASS 3 - 최종 확정 Findings

### 1. ID: `ROP-T4-001`
2. Severity: `P1`
3. 현상 요약:
   - live Stage 0 evidence layer가 아직 post-fix POV provenance 계약으로 refresh되지 않았다.
   - 실제 `style_guide.json`, DB `style_guide` anchor, style cache meta가 모두 구형 포맷이라 user-selected POV, extracted POV, effective POV, policy provenance를 보존하지 못한다.
4. 코드 근거:
   - `modules/core/stage0/style_extractor.py:288-350,352-374,921-1015`
   - `modules/core/stage0/__init__.py:626-669`
   - `modules/core/stage01_helpers.py:388-398,492-497,625-627`
   - `modules/core/project_support.py:161-181`
   - counter-evidence:
     - `tests/test_stage0_work_guard_style_cache.py`
     - `tests/test_project_support.py`
     - `tests/test_stage0_pov.py`
     - `tests/test_stage01_helpers.py`
   - runtime proof:
     - `projects/기록용/00`, `01`, `03`, `0w`의 `stage0_output/style_guide.json`
     - 네 프로젝트 `project_data.db`의 `anchors.style_guide`
     - `config/style_references/investment/style_guide.json`
5. downstream 영향 경계:
   - Stage 0 결과물 수동 감사
   - `style_guide` anchor를 직접 읽는 operator 도구
   - stale artifact 기반 회귀 검토
   - rerun/canary 전의 증거 보존 계층
   - 단, current planning / Stage 4 generation은 Bible 우선 보정으로 즉시 오작동하지는 않는다
6. 현재 테스트 근거 또는 테스트 부재:
   - focused regression:
     - `pytest -q tests/test_stage0_pov.py tests/test_stage0_work_guard_style_cache.py tests/test_project_support.py tests/test_stage01_helpers.py tests/test_stage2_preflight.py tests/test_stage3_orchestrator.py tests/test_stage4_post_processor.py tests/test_quality_sidecar_bootstrap.py`
     - 결과: `188 passed`
   - 테스트는 현재 코드 계약을 잠그지만, active project artifact refresh 수행 여부는 잠그지 못한다
7. 기존 문서와의 중복 여부:
   - `related-but-new-evidence-layer-surface`
   - 기존 `viewpoint-mixed-pov-full-survey-3pass-final-audit.md`는 pre-fix drift를 지적했고, `viewpoint-primary-pov-external-insert-remediation-postfix-3pass-closure.md`는 code remediation을 `closed`로 판정했다
   - 이번 finding은 `2026-03-13 04:41~05:00 KST`에 생성된 live artifact가 `2026-03-13 07:56~10:55 KST` 코드 수정 이후에도 refresh proof 없이 남아 있다는 evidence-layer 상태를 다룬다
8. 권장 후속 조치:
   - active project `00`, `01`, `03`, `0w`에 대해 Stage 0 artifact refresh 또는 최소 `style_guide` 재생성/재박제를 수행한다
   - refresh 후 아래 네 필드가 file, DB anchor, cache 모두에 존재하는지 확인한다
     - `selected_primary_pov`
     - `extracted_pov`
     - `effective_primary_pov`
     - `external_pov_insert_policy`
   - refresh 후 `logs/session/*.log`와 `llm_io.jsonl`에서 Stage 0 -> planning -> Stage 3/4 summary 체인을 다시 검증한다

### 1. ID: `ROP-T4-002`
2. Severity: `P2`
3. 현상 요약:
   - operator-facing support surface가 POV provenance를 `effective contract`가 아니라 raw file POV로 계속 표시한다.
   - 따라서 같은 프로젝트에서 runtime은 `혼합/3인칭/전지적`으로 작동해도 dashboard/API detail은 `pov=1인칭`처럼 보일 수 있다.
4. 코드 근거:
   - `modules/core/project_support.py:288-318`
     - `effective_pov`를 계산하지만 raw `pov`도 병렬 보존
   - `modules/api/bridge_server.py:523-536`
     - operator detail에 `pov={support_assets['style_guide']['pov']}` 사용
   - `modules/core/quality_sidecar_bootstrap.py:152-158`
     - `style_pov = support_assets["style_guide"]["pov"]`
   - runtime contrast:
     - `projects/기록용/01/logs/session_20260313_044504.log:1014-1015`
     - `projects/기록용/03/logs/session_20260313_045921.log:1386-1387`
     - `projects/기록용/00/logs/session_20260313_043840.log:1359-1360`
     - 위 로그는 raw StyleGuide POV는 `1인칭`인데 실제 Stage 4 load는 Bible POV를 적용했음을 보여 준다
5. downstream 영향 경계:
   - bridge status/detail
   - quality sidecar health payload
   - support asset readiness view
   - 운영자가 artifact 상태를 눈으로 판단하는 모든 lightweight surface
6. 현재 테스트 근거 또는 테스트 부재:
   - `tests/test_project_support.py:89-120`는 `inspect_project_support_assets()`의 `effective_pov` 계산만 확인한다
   - `tests/test_quality_sidecar_bootstrap.py`는 `style_pov` 의미/정합성을 검증하지 않는다
   - `tests/test_process_runner.py`의 bridge wiring은 style detail payload를 검증하지 않는다
   - focused regression `188 passed`였지만, 이 surface의 semantic drift를 잠그는 테스트는 없다
7. 기존 문서와의 중복 여부:
   - `related-but-new-evidence-layer-surface`
   - 기존 viewpoint 문서들은 Stage 0 / planning / Stage 4 보강을 다뤘지만 bridge/quality sidecar 같은 operator support surface의 raw POV 노출까지는 잠그지 않았다
8. 권장 후속 조치:
   - bridge/quality/support surface는 raw `pov` 대신 `effective_pov`를 기본값으로 사용하고, 가능하면 `selected_primary_pov`, `style_guide_extracted_pov`, `external_pov_insert_policy`를 함께 노출한다
   - file-only surface를 유지할 필요가 있으면 label을 `raw_style_pov`로 바꿔 contract drift를 숨기지 않게 한다
   - 아래 테스트를 추가한다
     - stale file `pov=1인칭`, Bible POV `혼합`일 때 bridge detail이 `effective_pov=혼합`을 보여 주는지
     - quality sidecar health가 `style_pov`가 아니라 `effective_pov` 또는 provenance bundle을 쓰는지

## Open Questions / Coverage Gaps

- `external_pov_insert_policy` live runtime proof는 아직 없다.
  - 현재 조사한 active project run은 `2026-03-13 04:39~04:59 KST`에 시작됐고, 해당 `bible.protagonist_config`에는 `external_pov_insert_policy`가 없다.
  - 관련 코드 수정 시각은 `2026-03-13 10:52~10:55 KST`이므로, post-fix live rerun이 아직 증거로 남아 있지 않다.
- Stage 3 / Stage 4 summary log의 POV provenance 필드도 현재 조사한 live log에는 보이지 않는다.
  - 이는 `tests/test_stage3_orchestrator.py`, `tests/test_stage4_post_processor.py` 기준 current code regression이라기보다 post-fix runtime proof 부재로 분류한다.

## PASS1 -> PASS2 -> PASS3 요약

- PASS1 후보: `4`
  - live artifact stale
  - support surface raw POV drift
  - stale cache silent reuse 가능성
  - planning/runtime stale POV 사용 가능성
- PASS2 제거: `2`
  - stale cache silent reuse:
    - `s0-style-cache-v1`는 current code의 meta guard에 걸려 재분석 대상
  - planning/runtime stale POV 사용:
    - Stage 2 summary, Stage 4 load, `llm_io.jsonl` prompt는 Bible 우선 `effective_pov`를 사용
- PASS3 확정: `2`
  - `ROP-T4-001`
  - `ROP-T4-002`
