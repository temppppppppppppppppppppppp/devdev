# [MPN-T4] Stage4 Summary / Cache Findings

> 작성일: 2026-03-13
> 상태: `PASS3 finalized`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-persistence-narrative-detail-full-survey-audit-order.md`

코드 직접 수정은 수행하지 않았다. 본 문서는 `Terminal 4 - Narrative Summary Generation / Load` 범위의 조사 결과만 기록한다.

---

## 조사 범위

- `main_a.py`
  - `_generate_narrative_summary()`
  - `_load_narrative_summaries()`
- 직접 downstream
  - `modules/core/stage4_context.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/services/project_service.py`
  - `modules/core/db_manager.py`

## 필수 근거

- `tests/test_sweep23.py`
- `tests/test_stage4_context.py`
- `docs/2026-03-10/stage-quality-improvement-audit-3pass.md`
- 보조 교차 검증
  - `tests/test_main_a_rollback.py`
  - `tests/test_project_service.py`
  - `tests/test_stage4_context_builder.py`
  - `tests/test_stage4_post_processor.py`

## 검증 실행

- `pytest tests/test_sweep23.py tests/test_stage4_context.py tests/test_main_a_rollback.py tests/test_project_service.py -q`
  - 결과: `52 passed`
- `pytest tests/test_stage4_context_builder.py tests/test_stage4_post_processor.py -q`
  - 결과: `86 passed`

## PASS 기록

- PASS 1: 후보 4건 수집
  - rollback/wipe 뒤 stale narrative summary 누수 가능성
  - sparse manuscript에서 `ep_range` 보존 범위 오표기
  - Stage4 builder와 loader의 계층형 요약 이중 주입
  - summary 저장 경로의 `safe_commit` 비사용
- PASS 2: 코드/테스트/기존 문서 교차 검증
  - `safe_commit` 비사용은 Stage4 happy path 전반의 direct DB commit 스타일과 분리해도 증거가 약해 확정 finding에서 제외
  - 나머지 3건은 현재 코드와 테스트 부재로 재현 가능성이 높아 유지
- PASS 3: 확정 3건, open question 1건

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| [MPN-T4-001] | P1 | confirmed | `main_a.py::_load_narrative_summaries`, `project_service.py`, `db_manager.py` | rollback/reset/wipe 뒤 삭제된 미래 회차의 narrative summary anchor가 Stage4 재시작 프롬프트에 다시 주입될 수 있다 |
| [MPN-T4-002] | P2 | confirmed | `main_a.py::_generate_narrative_summary`, `db_manager.py::get_recent_manuscripts` | summary 생성기가 실제 회차 집합이 아닌 산술 창을 `ep_range`로 저장해 sparse resume 구간에서 보존 범위를 잘못 표기한다 |
| [MPN-T4-003] | P2 | confirmed | `main_a.py::_load_narrative_summaries`, `stage4_context_builder.py` | Stage4가 series/volume summary를 두 경로에서 중복 적재하며, 기존 stage-quality 문서가 지적한 하드코딩 상한도 그대로 남아 있다 |

---

## [MPN-T4-001] P1

1. ID
   - `MPN-T4-001`
2. Severity
   - `P1`
3. 현상 요약
   - rollback/reset/wipe 이후에도 `narrative_summary_ep_*` anchor가 남고, loader는 현재 회차 경계 없이 모든 요약을 읽는다. 그 결과 삭제된 미래 회차 요약이 Stage4 재개 프롬프트에 다시 섞일 수 있다.
4. 코드 근거
   - `main_a.py:3286`은 5화 단위 요약을 `narrative_summary_ep_XXX` anchor로 저장한다.
   - `main_a.py:3316-3321`은 `range(5, 500, 5)` 전체를 순회하며 존재하는 narrative summary를 모두 수집한다.
   - `modules/core/stage4_context_builder.py:2447-2449`는 loader 결과를 그대로 mandatory context에 붙인다.
   - `modules/core/services/project_service.py:102-103`은 Stage2 summary clear에서 `series_summary`, `volume_summary_*`만 삭제한다.
   - `modules/core/services/project_service.py:162,222,304,369`은 destructive op에서 `reset_after()`를 호출하지만 narrative summary anchor 정리는 없다.
   - `modules/core/db_manager.py:2283-2333`의 `reset_after()`는 episode 계열 테이블만 지우고 `anchors` 전반은 건드리지 않는다.
5. downstream 영향 경계
   - Stage4 재개 시 `modules/core/stage4_context_builder.py`가 오래된 narrative summary를 프롬프트에 주입한다.
   - 이 누수는 rollback/wipe 이후의 Stage4 writer/director 판단에 미래 정보가 섞이는 형태로 나타난다.
   - Stage4Context DI 자체(`modules/core/stage4_context.py:127-129,173-175`)는 단순 배선이므로, 문제는 helper contract와 destructive op 정리 경계에 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_main_a_rollback.py:45,73,103`은 `_narrative_summaries_cache` 메모리 무효화만 본다.
   - `tests/test_project_service.py:64-76,145-198`은 `reset_after()` 호출과 `series_summary`/`volume_summary_*` 정리만 확인한다.
   - `tests/test_stage4_context_builder.py:32`는 `load_narrative_summaries`를 빈 문자열 mock으로 고정한다.
   - narrative summary anchor의 삭제 여부나 rollback 후 loader 필터링을 검증하는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - destructive op에 `narrative_summary_ep_*` 정리를 추가하거나, `_load_narrative_summaries()`에 `current_ep` 인자를 넣어 `ep_marker < next_ep`만 로드하도록 바꾼다.
   - rollback/wipe 후 Stage4 재개 시 미래 요약이 보이지 않는 회귀 테스트를 추가한다.

## [MPN-T4-002] P2

1. ID
   - `MPN-T4-002`
2. Severity
   - `P2`
3. 현상 요약
   - summary 생성기는 실제로 DB에서 읽어 온 회차 목록이 아니라 `up_to_ep-4 ~ up_to_ep`라는 산술 창을 `ep_range`로 저장한다. sparse manuscript 또는 partial resume 상황에서는 요약 표기가 실제 커버리지보다 넓어진다.
4. 코드 근거
   - `main_a.py:3194`는 `start_ep = max(1, up_to_ep - 4)`로 범위를 계산한다.
   - `main_a.py:3198`은 `get_recent_manuscripts(before_ep=up_to_ep + 1, limit=5)`로 최근 5개만 읽는다.
   - `modules/core/db_manager.py:2494-2509`의 `get_recent_manuscripts()`는 “최근 N개”를 반환할 뿐 연속 회차를 보장하지 않는다.
   - `main_a.py:3287-3291`은 실제 회차 목록을 보지 않고 `ep_range = f"{start_ep}-{up_to_ep}"`를 저장한다.
   - `main_a.py:3320`은 이 `ep_range`를 그대로 `[제{ep_range}화 요약]` 라벨로 노출한다.
5. downstream 영향 경계
   - Stage4는 “6-10화 요약”으로 보이는 텍스트를 신뢰하지만, 실제 요약 대상이 8/9/10화 같은 부분 집합일 수 있다.
   - partial resume, sparse manuscript 보정, 수동 삭제 후 재생성에서 episode mapping 혼선이 생긴다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_sweep23.py:19-26`은 `None` manuscript 입력에서 `len()` crash가 나지 않는지만 본다.
   - sparse manuscript, 회차 라벨 정확성, 비연속 구간 저장 규약을 검증하는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - `ep_range`를 실제 manuscript의 첫/마지막 `ep_num` 기준으로 저장하거나, 아예 `episode_list`를 정식 필드로 보존한다.
   - 비연속 집합이면 저장을 건너뛰거나 `partial=true` 같은 표식을 넣는 회귀 테스트를 추가한다.

## [MPN-T4-003] P2

1. ID
   - `MPN-T4-003`
2. Severity
   - `P2`
3. 현상 요약
   - Stage4는 계층형 summary를 두 경로에서 중복 적재한다. builder가 이미 시리즈/최근 볼륨 요약을 넣은 뒤, loader가 시리즈/최대 20개 볼륨/5화 요약을 다시 붙인다. 중복 제거가 없어 context budget을 반복 소비한다.
4. 코드 근거
   - `modules/core/stage4_context_builder.py:2142-2153`은 `series_summary`와 현재 기준 최근 3개 볼륨을 직접 적재한다.
   - `main_a.py:3316-3336`의 loader는 5화 요약 전체와 `series_summary`, `volume_summary_1..20`를 다시 모은다.
   - `modules/core/stage4_context_builder.py:2447-2449`는 loader 반환값을 추가로 mandatory context에 붙인다.
   - `modules/core/stage4_context_builder.py:1443-1485`의 compose 단계는 길이 budget만 맞추고 중복 summary를 제거하지 않는다.
   - `docs/2026-03-10/stage-quality-improvement-audit-3pass.md:435-457,637`은 저장/주입 정책 비대칭과 하드코딩 상한 제거를 P2 과제로 남겼다. 현재 코드상 해당 이슈는 닫히지 않았다.
5. downstream 영향 경계
   - mandatory context에서 계층형 요약이 과대표집되며, 그만큼 world state / fact ledger / retrieval slice가 trim될 수 있다.
   - 최근 3볼륨만 붙이는 builder 정책과 최대 20볼륨을 붙이는 loader 정책이 동시에 살아 있어 summary contract가 한 곳에 잠겨 있지 않다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage4_context.py:166-177`은 callback 배선만 본다.
   - `tests/test_stage4_context_builder.py:32`는 loader를 빈 문자열 mock으로 치환해 실제 중복 적재 경로를 덮지 못한다.
   - 중복 summary로 인한 context budget 손실이나 상한 drift를 검증하는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-shared-helper-surface`
   - 기존 문서는 “상한과 정책 비대칭”을 지적했고, 본 finding은 “실제 runtime에서 두 경로가 동시에 살아 있어 중복 주입까지 발생한다”는 현재 contract drift를 추가로 확정한다.
8. 권장 후속 조치
   - series/volume summary 조립 책임을 builder 또는 loader 한 곳으로 단일화한다.
   - 상한을 DB 존재 구간 기반 또는 설정 기반으로 옮기고, compose 전에 summary dedupe를 수행한다.
   - context budget 회귀 테스트에 “series/volume summary가 한 번만 주입되는지”를 추가한다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| rollback/wipe 이후 narrative summary anchor 정리 | 미검증 | destructive op 후 `narrative_summary_ep_*`가 실제로 삭제되거나 필터되는지 확인하는 회귀 테스트 |
| sparse manuscript 구간의 `ep_range` 정확성 | 미검증 | 비연속 회차 `[{8,9,10}]` 또는 `[{1,3,5}]` 케이스에서 저장 라벨을 검증하는 단위 테스트 |
| 계층형 summary 중복 주입 / budget 손실 | 미검증 | Stage4 context builder가 series/volume summary를 한 번만 포함하는지 확인하는 테스트 |
| summary 저장의 commit/audit 경계 | open question | `_generate_narrative_summary()`의 direct commit 실패를 별도 soft-failure/audit로 남길지 정책 결정 필요 |

## PASS1 후보 -> PASS2 제거 -> PASS3 확정

- PASS1 후보 4건
  - stale future summary 누수
  - sparse `ep_range` 오표기
  - hierarchy summary 이중 주입
  - direct commit vs shared commit helper drift
- PASS2 제거 1건
  - direct commit drift는 `_generate_narrative_summary()`만의 고립 문제로 확정하기에는 Stage4 happy path 전반의 DB 저장 방식과 분리 증거가 부족했다. 대신 `Coverage Gap`의 open question으로 남긴다.
- PASS3 확정 3건
  - `MPN-T4-001`
  - `MPN-T4-002`
  - `MPN-T4-003`

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
