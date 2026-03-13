# [MPN-T2] Protagonist / Episode Mapping Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 complete`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-persistence-narrative-detail-full-survey-audit-order.md`

코드 직접 수정은 수행하지 않았다. 본 문서는 read-only 조사 결과만 기록한다.

---

## 조사 범위

- `main_a.py`
  - `_get_protagonist_name()`
  - `_fix_entity_registry_protagonist()`
  - `_get_max_episode_from_manuscripts()`
  - `_calculate_arc_from_episode()`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- 직접 downstream 교차 검증
  - `modules/core/stage01_helpers.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/domain/agents/state_extractor.py`
  - `modules/domain/agents/director_continuity.py`

## 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/e2e/test_l3_stage3_smoke.py`
- 추가 교차 검증
  - `tests/test_stage01_helpers.py`
  - `tests/test_stage2_context.py`
  - `tests/test_sweep36.py`
  - `docs/2026-03-13/MCP-T3-menu-stage-entry-findings.md`
  - `docs/2026-02-23/tf11_findings.md`

## PASS 기록

- PASS 1
  - 후보 6건 수집.
  - 주요 후보:
    - `_get_protagonist_name()` source/root drift
    - `_fix_entity_registry_protagonist()` duplicate protagonist 가능성
    - Stage2 smart skip callback guard 불일치
    - `_calculate_arc_from_episode()` 5화 고정 가정
    - `_get_max_episode_from_manuscripts()` file-only head 계산
    - `_get_protagonist_name_safe()` 예외 시 기본값 폴백
- PASS 2
  - 제거 2건.
  - 제거 1: `_get_max_episode_from_manuscripts()` file-only vs hybrid resume source mismatch
    - 사유: `docs/2026-03-13/MCP-T3-menu-stage-entry-findings.md`의 `MCP-T3-01`이 이미 동일 surface를 확정했다.
  - 제거 2: `_get_protagonist_name_safe()` 예외 시 `"주인공"` 폴백
    - 사유: 현재 계약상 graceful degradation으로 일관되며, 신규 contract bug는 source drift 쪽이 본체다.
- PASS 3
  - 확정 4건 채택.
  - 확정 ID: `MPN-T2-01` ~ `MPN-T2-04`

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MPN-T2-01` | `P1` | confirmed | `main_a.py::_get_protagonist_name` | live `master_bible`를 무시하고 DB anchor만 읽어 주인공명이 stale/default로 드리프트할 수 있다 |
| `MPN-T2-02` | `P1` | confirmed | `main_a.py::_fix_entity_registry_protagonist` | `role="extracted"` registry에 이미 주인공이 있어도 중복 protagonist row를 삽입한다 |
| `MPN-T2-03` | `P2` | confirmed | `stage2_context.py` + `stage2_orchestrator.py` | `calculate_arc_from_episode`는 nullable DI 슬롯인데 manuscript가 있으면 unguarded call로 즉시 크래시한다 |
| `MPN-T2-04` | `P2` | confirmed | `main_a.py::_calculate_arc_from_episode` | helper가 5화 고정 버킷을 강제해 가변 `ep_count` Stage2 계약과 어긋난다 |

---

## Findings

### [MPN-T2-01] P1 | `_get_protagonist_name()`가 live `master_bible` 대신 DB anchor만 읽어 shared consumer에 stale/default 주인공명을 주입한다

- ID
  - `MPN-T2-01`
- Severity
  - `P1`
- 현상 요약
  - helper는 `self.current_project.db.load_anchor("bible")`만 읽고, 이미 메모리에 올라온 `current_project.master_bible`은 전혀 참조하지 않는다.
  - 같은 런타임에서 Stage1/3/4 consumer는 `current_project.master_bible`을 직접 읽는 반면 protagonist helper만 별도 source를 쓰므로, 주인공명 source-of-truth가 분리된다.
  - read-only 재현에서 `current_project.master_bible`에 `Hero`가 있어도 `db.load_anchor("bible")`가 비어 있으면 `_get_protagonist_name()`은 `"주인공"`을 반환했다.
- 코드 근거
  - `main_a.py:2050-2060`
    - `_get_protagonist_name()`는 raw DB anchor를 읽고 legacy fallback도 `bible_root`가 아니라 top-level `bible["characters"]`만 본다.
  - `modules/core/stage01_helpers.py:747-755`
    - Stage1은 `app.current_project.master_bible`을 Analyst 입력으로 넘기면서 protagonist_name만 helper 결과를 따로 주입한다.
  - `modules/core/stage3_orchestrator.py:859-870`
    - Stage3는 protagonist callback 결과를 blueprint 생성 입력으로 사용한다.
  - `modules/core/stage4_context_builder.py:77-82`
    - Stage4ContextBuilder는 동일 callback을 protagonist name resolution의 1순위로 사용한다.
  - `modules/core/stage4_post_processor.py:1334-1339`
    - Stage4 post-process도 protagonist callback과 `current_project.master_bible`을 동시에 소비한다.
- downstream 영향 경계
  - Stage1 `Analyst.plan_single_volume_v20(... protagonist_name=...)`
  - Stage3 blueprint 생성 시 protagonist name labeling
  - Stage4 context builder의 protagonist_name 해석
  - Stage4 post-processor의 protagonist-core exclusion logic
- 현재 테스트 근거 또는 테스트 부재
  - `tests/test_stage01_helpers.py:522-531`은 helper를 mock으로만 대체해 live bible vs DB anchor drift를 전혀 검증하지 않는다.
  - `tests/test_stage3_orchestrator.py:386-391`, `tests/test_stage3_orchestrator.py:896-932`는 Stage3가 callback을 호출하는지만 확인한다.
  - `tests/e2e/test_l3_stage3_smoke.py:120-143`도 `_get_protagonist_name`을 MagicMock으로 고정한다.
  - `tests/test_stage4_context.py:164-176`은 Stage4Context wiring만 보고 callback의 source consistency는 보지 않는다.
- 기존 문서와의 중복 여부
  - `related-but-new-shared-helper-surface`
  - 기존 문서들은 protagonist callback wiring과 Stage4 injection은 다뤘지만, `main_a.py` helper가 live `master_bible`를 우회한다는 shared-helper source drift는 직접 확정하지 않았다.
- 권장 후속 조치
  - `_get_protagonist_name()`의 1순위를 `current_project.master_bible`로 올리고 DB anchor는 fallback으로 내린다.
  - legacy `characters` fallback도 `bible_root` 기준으로 읽도록 정규화한다.
  - Stage1/3/4 공통 회귀 테스트로 "in-memory master_bible만 최신, DB anchor는 stale" 케이스를 추가한다.

### [MPN-T2-02] P1 | `_fix_entity_registry_protagonist()`가 `role="extracted"` protagonist를 발견하지 못해 중복 protagonist row를 삽입한다

- ID
  - `MPN-T2-02`
- Severity
  - `P1`
- 현상 요약
  - helper는 `characters` 목록에서 `role in ("주인공", "protagonist", "주역")`만 protagonist로 인정한다.
  - 그러나 실제 `StateExtractor`는 character entity를 `{"name": ..., "role": "extracted"}` 형태로 만든다.
  - 따라서 registry에 주인공 이름이 이미 있어도 role이 `extracted`면 찾지 못하고 새 protagonist row를 `insert(0, ...)`로 추가한다.
  - read-only 재현에서 `{"name": "Hero", "role": "extracted"}`가 이미 존재하는 registry에 helper를 적용하자 `Hero`가 2건으로 늘어났다.
- 코드 근거
  - `main_a.py:2079-2088`
    - protagonist 판정이 role label 기반으로만 이뤄지고, 이름 동일성은 판정에 쓰이지 않는다.
  - `modules/domain/agents/state_extractor.py:702`
    - extracted character의 기본 role은 `"extracted"`다.
  - `modules/core/stage3_orchestrator.py:820-823`
    - Stage3는 cached entity registry에 helper를 직접 적용한다.
  - `modules/domain/agents/director_continuity.py:199-220`
    - Director formatter는 dedupe 없이 character list를 그대로 문자열화한다.
- downstream 영향 경계
  - Stage3 cached entity registry
  - Stage2 preflight의 Director/Constraint compiler용 entity registry
  - Director continuity prompt에 동일 protagonist가 중복 표기되는 경로
  - entity count / registry summary 로그의 과대 계수
- 현재 테스트 근거 또는 테스트 부재
  - `tests/test_stage3_orchestrator.py`의 entity registry 관련 테스트는 cache hit 여부만 보고 실제 fix helper semantics는 검증하지 않는다.
  - `tests/e2e/test_l3_stage3_smoke.py:142-143`은 `_fix_entity_registry_protagonist`를 identity lambda로 mock 처리한다.
  - `tests/test_stage3_orchestrator.py:923-932`는 callback wiring만 확인한다.
  - 실제 `StateExtractor` 출력(`role="extracted"`)과 helper를 함께 태우는 통합 테스트는 없다.
- 기존 문서와의 중복 여부
  - `none`
- 권장 후속 조치
  - `role`뿐 아니라 `name == protagonist_name`도 existing protagonist 판정에 포함한다.
  - 중복 삽입 대신 기존 extracted row를 protagonist row로 승격하는 최소 보정으로 바꾼다.
  - `state_extractor -> fix_entity_registry_protagonist -> director formatter` 연쇄 회귀 테스트를 추가한다.

### [MPN-T2-03] P2 | Stage2 smart skip는 nullable callback contract를 반쯤만 지켜 manuscript가 있으면 `calculate_arc_from_episode`에서 즉시 크래시한다

- ID
  - `MPN-T2-03`
- Severity
  - `P2`
- 현상 요약
  - `Stage2Context`는 `calculate_arc_from_episode=None`을 허용한다.
  - `stage_2_arcs_async_logic()`는 `get_max_episode_from_manuscripts`에는 `callable` guard를 두지만, `existing_ms_max_ep > 0`이 되면 `self.ctx.calculate_arc_from_episode(existing_ms_max_ep)`를 무조건 호출한다.
  - read-only 재현에서 `get_max_episode_from_manuscripts=lambda: 7`, `calculate_arc_from_episode=None`인 최소 context로 `Stage2Orchestrator.stage_2_arcs_async_logic()`를 실행하자 `TypeError: 'NoneType' object is not callable`이 발생했다.
- 코드 근거
  - `modules/core/stage2_context.py:140-146`
    - 두 callback 모두 nullable DI 슬롯이다.
  - `modules/core/stage2_orchestrator.py:219-225`
    - manuscript head callback은 guarded call인데 arc mapping callback은 unguarded call이다.
  - `tests/test_stage2_context.py:63-84`
    - Stage2Context가 optional attrs/callback을 `None`으로 허용하는 계약을 테스트가 고정한다.
- downstream 영향 경계
  - custom context / partial DI / isolated test harness에서 Stage2 smart skip 경로
  - manuscript가 이미 존재하는 프로젝트에서 Stage2 진입 직후 크래시
  - Stage2 helper contract를 재사용하는 외부 orchestration harness
- 현재 테스트 근거 또는 테스트 부재
  - `tests/e2e/test_l3_stage2_realproject.py`와 `tests/e2e/test_l3_golden_route.py`는 항상 `calculate_arc_from_episode=lambda _ep: 0`을 주입한다.
  - `tests/test_sweep36.py:59-64`는 호출문이 존재하는지만 보는 문자열 회귀 테스트다.
  - `calculate_arc_from_episode is None` + `existing_ms_max_ep > 0` 조합을 실제 실행하는 회귀 테스트는 없다.
- 기존 문서와의 중복 여부
  - `related-but-new-shared-helper-surface`
  - `docs/2026-02-23/tf11_findings.md:37-40`는 nullable callback 전반을 LOW 레벨로 메모했지만, 현재 살아 있는 구체적 surface가 `calculate_arc_from_episode`이며 read-only 재현까지 확인된 점이 신규다.
- 권장 후속 조치
  - `calculate_arc_from_episode`에도 동일한 `callable` guard를 추가한다.
  - callback이 없으면 skip warning을 생략하거나, 이미 설계된 arc의 `ep_start/ep_end`에서 역산하도록 fallback을 둔다.
  - `Stage2Context(optional callback None) + manuscript>0` 회귀 테스트를 추가한다.

### [MPN-T2-04] P2 | `_calculate_arc_from_episode()`의 5화 고정 버킷은 현재 Stage2 가변 `ep_count` 계약과 충돌한다

- ID
  - `MPN-T2-04`
- Severity
  - `P2`
- 현상 요약
  - helper는 `Arc = 5화`를 고정 가정해 `(ep_num - 1) // 5 + 1`로 arc 번호를 계산한다.
  - 그러나 현재 Stage2는 `ep_count`를 3~6 범위에서 가변 결정하고, `arc_ensemble`도 `ep_start + ep_count - 1`로 arc 경계를 만든다.
  - 따라서 manuscript head가 실제 가변 pacing으로 쌓인 상태에서는 smart skip warning의 `skip_arc_no`가 실제 arc 경계와 쉽게 어긋난다.
- 코드 근거
  - `main_a.py:2524-2529`
    - helper 자체가 5화 고정 버킷을 강제한다.
  - `modules/domain/agents/analyst.py:723-745`
    - Stage2 target `ep_count`는 `VolumeSettings` 범위 안에서 가변 결정된다.
  - `modules/domain/agents/analyst_prompts.py:305-361`
    - prompt contract도 `Blitz/Standard/Epic`, `ep_count 3~6`을 명시한다.
  - `modules/domain/agents/arc_ensemble.py:375-378`
    - 실제 `ep_end`는 `ep_start + ep_count - 1`로 계산된다.
  - `modules/core/stage2_orchestrator.py:223-225`
    - smart skip warning은 이 helper 결과를 그대로 사용한다.
- downstream 영향 경계
  - Stage2 manuscript-detected warning의 arc 번호
  - 운영자가 보는 "Arc X까지 필요" 메시지
  - 수동 복구/재개 시 arc 동기화 판단
- 현재 테스트 근거 또는 테스트 부재
  - `tests/test_sweep36.py:53-56`은 오히려 5화 공식을 문자열 수준으로 고정한다.
  - variable `ep_count` arc를 만든 뒤 `_calculate_arc_from_episode()`와 실제 `ep_start/ep_end`를 대조하는 테스트는 없다.
  - `tests/e2e/test_l3_stage3_smoke.py`는 `_get_max_episode_from_manuscripts=0` 고정이라 이 문제를 밟지 않는다.
- 기존 문서와의 중복 여부
  - `related-but-new-shared-helper-surface`
  - 2026-03-13 Stage2 전수 감사에는 다른 5화 하드코딩 사례가 있지만, `main_a.py` shared helper가 Stage2 smart skip에 잘못된 arc 경계를 주입하는 surface는 별도다.
- 권장 후속 조치
  - helper를 5화 공식으로 유지하지 말고, 이미 설계된 `arcs`의 `ep_start/ep_end`를 기준으로 역산하게 바꾼다.
  - 설계 전 단계라서 실제 arc 범위가 아직 없으면 결과를 확정값이 아닌 heuristic warning으로 격하한다.
  - variable `ep_count` 샘플로 smart skip warning arc 번호를 검증하는 회귀 테스트를 추가한다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| live `master_bible` vs DB anchor protagonist source drift | unit/e2e 모두 helper mock 중심 | 실제 `SovereignApp._get_protagonist_name()`를 호출하는 integration test |
| `StateExtractor(role="extracted")`와 protagonist fix 결합 | 개별 컴포넌트만 확인, 연쇄 테스트 없음 | `extract_cumulative_state()` 출력에 helper 적용 후 director formatter까지 검증 |
| Stage2 smart skip nullable callback | context unit test는 `None` 허용, orchestrator runtime test는 없음 | `existing_ms_max_ep > 0` + `calculate_arc_from_episode=None` 실행 회귀 |
| variable `ep_count`와 arc mapping 정합성 | 5화 공식 문자열 회귀만 존재 | non-5-length arc 샘플에서 helper 결과와 실제 `ep_start/ep_end` 비교 테스트 |
| sparse manuscript / partial resume 의미 | max filename heuristic만 존재 | 연속/비연속 draft 파일 세트별 expected policy 명문화 |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- PASS1 후보 -> PASS2 제거 -> PASS3 확정 요약 포함
