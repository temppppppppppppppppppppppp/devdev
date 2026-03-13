# MLW-T3: Stage4 Real-App Binding Findings

> 작성일: 2026-03-13
> 작성자: Codex GPT-5
> 트랙: Terminal 3 — Stage4 Real-App Binding
> 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
> 상태: `PASS3 재감리 완료`
> 조사 모드: `static / read-only / code-and-test verification / synthetic verification / UTF-8 only`

---

## 재감리 결론

- OPUS 초안이 짚은 `ctx.db`, `audit_event`, `adaptive_manager` 표면은 대체로 유효했다.
- 하지만 가장 큰 blocker인 `Stage4Context` 생성 불가(`P0`)를 놓쳤다. 현재 코드 기준으로 real app Stage 4 진입은 `Stage4Context.from_app(self)`에서 즉시 깨진다.
- 기존 문서에서 이미 닫힌 항목 2건은 재오픈하지 않았다.
  - `stage4_complete` callback source split -> `MFS-T3-02`
  - `_director_mc_parts` dead code -> `T3-stage3-4-pipeline-audit-report`의 `T3-033`

---

## 조사 범위

- `main_a.py`
  - Stage4 entry
  - Stage4 bound callback surface
- `modules/core/stage4_context.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_orchestrator.py`

## 필수 근거

- `tests/test_stage4_context.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_run_stage4_canary.py`
- `docs/2026-03-13/MFS-T3-stage3-stage4-audit-callback-findings.md`
- `docs/2026-03-13/T3-stage3-4-pipeline-audit-report.md`

---

## 추가 검증

### 정적 대조

- `Stage4Context` consumer가 참조하는 `ctx` 속성을 기계적으로 수집해 `__slots__`와 대조했다.
- consumer 참조 속성 중 `Stage4Context.__slots__`에 없는 항목은 아래 6개였다.
  - `_director_mc_parts`
  - `adaptive_manager`
  - `audit_event`
  - `db`
  - `enrich_director_result`
  - `generate_writer_guidance_v60_8`

### synthetic verification

- 최소 `Stage4Context(...)` 인스턴스화
  - 결과: `AttributeError: 'Stage4Context' object has no attribute 'generate_writer_guidance_v60_8'`
- plain ctx 객체에 `current_project.db`만 두고 `ctx.db`는 비운 채 `Stage4ContextBuilder._execute_retrieval_plan()` 실행
  - 결과: `DB_NPC_RELATIONSHIP` slot이 빈 결과 반환
  - 결과: `current_project.db.get_relationship_history()` 호출 0회
- 같은 조건에서 `Stage4ContextBuilder._fetch_manuscript_excerpt()` 실행
  - 결과: 빈 문자열 반환
  - 결과: `current_project.db.get_manuscripts_range()` 호출 0회

### 회귀 테스트 실행

- `pytest tests/test_stage4_context.py -q`
  - 결과: `16 failed, 3 passed, 12 errors`
  - 핵심 실패: `Stage4Context.from_app()` / 직접 생성 모두 `generate_writer_guidance_v60_8` 슬롯 누락으로 붕괴
- `pytest tests/test_stage4_interview_round.py -q`
  - 결과: `1 failed, 69 passed`
  - 핵심 실패: `test_stage4_context_from_app_extracts_pass_rate_monitor`
- `pytest tests/test_stage4_context_builder.py -q`
  - 결과: `46 passed`
- `pytest tests/test_stage4_post_processor.py -q`
  - 결과: `41 passed`

builder / post-processor 계열 초록과 context / from_app 계열 붕괴가 동시에 존재한다는 점이 이번 트랙의 핵심 blind spot이다.

---

## Finding Ledger

### MLW-T3-001 — `Stage4Context` real-app 생성 자체가 깨져 있다

| 필드 | 내용 |
|------|------|
| **ID** | `MLW-T3-001` |
| **Severity** | `P0` |
| **현상 요약** | `Stage4Context.__slots__`가 `generate_writer_guidance_v60_8`, `enrich_director_result`를 선언하지 않았는데 `__init__()`는 두 속성을 무조건 할당하고 `from_app()`도 두 콜백을 항상 주입한다. 결과적으로 `Stage4Context(...)`와 `Stage4Context.from_app(app)`가 즉시 `AttributeError`로 붕괴한다. |
| **코드 근거** | `modules/core/stage4_context.py:45-80`에는 두 슬롯이 없다. 같은 파일 `115-116`, `148-149`, `195-196`은 두 콜백을 init/from_app 경로에 포함한다. `main_a.py:432-463`, `main_a.py:733-744`에 실제 bound method가 존재하고, `main_a.py:3542-3546`은 real app Stage 4 entry에서 `Stage4Context.from_app(self)`를 호출한다. consumer도 `modules/core/stage4_context_builder.py:2514-2518`, `modules/core/stage4_interview_round.py:839-845`에서 두 콜백을 기대한다. |
| **downstream 영향 경계** | `main_a.py`의 real Stage 4 entry가 `self._stage4_orch.stage_4_v2_chief_writer()`에 도달하기 전에 깨진다. `Stage4Orchestrator.ctx` lazy build (`modules/core/stage4_orchestrator.py:201`)도 같은 방식으로 실패한다. Stage4 writer-guidance / director-result enrichment path는 실행 전 단계에서 차단된다. |
| **현재 테스트 근거 또는 테스트 부재** | `tests/test_stage4_context.py`는 현재 실제로 `16 failed, 12 errors`다. `tests/test_stage4_interview_round.py`도 `Stage4Context.from_app()`를 직접 건드리는 1건이 실패한다. 반면 `tests/test_stage4_context_builder.py`와 `tests/test_stage4_post_processor.py`는 bare `MagicMock` ctx를 써서 초록이다. |
| **기존 문서와의 중복 여부** | `none` |
| **권장 후속 조치** | `Stage4Context.__slots__`와 `__init__`/`from_app()`를 즉시 동기화한다. 최소 회귀 보호막으로 `Stage4Context.from_app(app)`와 `Stage4Orchestrator(app).ctx`를 실제 인스턴스화하는 테스트를 유지한다. |

---

### MLW-T3-002 — Stage4 smart retrieval DB 경로가 `ctx.db`를 바라봐 real app에서 항상 비어 버린다

| 필드 | 내용 |
|------|------|
| **ID** | `MLW-T3-002` |
| **Severity** | `P1` |
| **현상 요약** | `Stage4ContextBuilder._execute_retrieval_plan()`과 `_fetch_manuscript_excerpt()`가 DB를 `self.ctx.db`에서 읽는데 real `Stage4Context`에는 `db` 슬롯이 없다. 정상 DB는 `self.ctx.current_project.db`에만 있다. 그 결과 `DB_NPC_RELATIONSHIP`과 `manuscript_db` retrieval slot이 real app에서 silent no-op가 된다. |
| **코드 근거** | `modules/core/stage4_context_builder.py:1228-1246`, `1308-1317`이 `db = getattr(self.ctx, "db", None)`를 사용한다. `modules/core/stage4_context.py:45-80`의 slots에는 `db`가 없다. 반면 같은 builder의 다른 경로는 `modules/core/stage4_context_builder.py:620-643`처럼 `current_project.db`를 정상 사용한다. synthetic check에서도 `current_project.db`가 살아 있어도 `ctx.db`가 없으면 relationship / manuscript retrieval call이 0회였다. |
| **downstream 영향 경계** | advisor smart retrieval path에서 `[SC:relationship_consistency]`와 `manuscript_db` 기반 연속성 참조가 비어 버린다. Stage 4는 진행되지만 Director / Writer가 관계 변화 이력과 원고 발췌를 받지 못해 real wiring 기준으로 context density가 떨어진다. |
| **현재 테스트 근거 또는 테스트 부재** | `tests/test_stage4_context_builder.py`는 `46 passed`지만 `_execute_retrieval_plan()`에서 `vec_memory` / `db_npc_history`만 직접 검증한다 (`tests/test_stage4_context_builder.py:705-770`). `DB_NPC_RELATIONSHIP` / `manuscript_db`는 이 경로로 검증되지 않는다. `tests/test_stage4_interview_round.py:595-685`는 관계 히스토리를 다른 helper 경로로 확인할 뿐, 이번 `ctx.db` 경로를 잠그지 않는다. |
| **기존 문서와의 중복 여부** | `related-but-new-live-wiring-surface` |
| **권장 후속 조치** | `self.ctx.current_project.db`를 canonical source로 통일하거나, 정말 편의 속성이 필요하면 `Stage4Context`에 read-only `db` property를 명시한다. 회귀 테스트는 `_execute_retrieval_plan()`에 `DB_NPC_RELATIONSHIP` / `manuscript_db` slot을 직접 태워 current-project DB 호출을 검증해야 한다. |

---

### MLW-T3-003 — `adaptive_manager`가 Stage4 real context에 실리지 않아 adaptive retry injection이 죽어 있다

| 필드 | 내용 |
|------|------|
| **ID** | `MLW-T3-003` |
| **Severity** | `P2` |
| **현상 요약** | `main_a.py`는 `adaptive_manager`를 초기화하지만 Stage4Context는 이 슬롯을 선언하지도, `from_app()`에서 싣지도 않는다. 그런데 `Stage4InterviewRound` REJECT 경로는 `self.ctx.adaptive_manager`를 기대한다. real Stage4Context에서는 해당 기능이 항상 skip된다. |
| **코드 근거** | `main_a.py:364`에서 속성을 선언하고 `main_a.py:1919-1923`에서 초기화한다. `modules/core/stage4_interview_round.py:3272-3285`는 `self.ctx.adaptive_manager.record_failure()`와 `get_injection_prompt()`를 호출한다. 그러나 `modules/core/stage4_context.py:45-80`, `159-200`에는 `adaptive_manager`가 없다. |
| **downstream 영향 경계** | Director REJECT 후 adaptive failure memory 기록과 다음 라운드 prompt injection이 real app에서 영구적으로 비활성화된다. 실패 패턴 재사용과 후속 라운드 유도 문구가 사라져 retry 품질이 저하될 수 있다. |
| **현재 테스트 근거 또는 테스트 부재** | `tests/test_stage4_interview_round.py`의 helper ctx는 `36`행에서 `ctx.adaptive_manager = None`을 MagicMock에 수동 주입한다. real `Stage4Context`에서는 같은 속성을 가질 수 없다. adaptive-manager wiring 자체를 real context로 잠그는 테스트는 없다. |
| **기존 문서와의 중복 여부** | `none` |
| **권장 후속 조치** | Stage4가 adaptive retry를 계약으로 인정할지 먼저 정한 뒤, 유지할 거면 `Stage4Context.__slots__` / `from_app()`에 싣고 REJECT path regression test를 추가한다. 버릴 거면 consumer 코드를 정리하고 test fixture에서 수동 주입을 제거한다. |

---

### MLW-T3-004 — `audit_event`가 Stage4 real context에 없어 post-processor 구조화 감사를 잃는다

| 필드 | 내용 |
|------|------|
| **ID** | `MLW-T3-004` |
| **Severity** | `P2` |
| **현상 요약** | `Stage4PostProcessor`는 soft-failure와 manager/bible-save 오류를 `self.ctx.audit_event()`로 구조화 기록하려고 하지만, Stage4Context에는 `audit_event` 슬롯이 없고 `from_app()`에서도 배선되지 않는다. real app에서는 해당 감사 이벤트가 조용히 증발한다. |
| **코드 근거** | `main_a.py:2831-2841`에 `_audit_event()` facade가 존재한다. 하지만 `modules/core/stage4_context.py:45-80`, `159-200`에는 `audit_event`가 없다. `modules/core/stage4_post_processor.py:38-52`는 soft-failure reporter에 `audit_event`를 넘기고, `815-816`, `840-841`, `1023-1024`는 `manager_parse_failure`, `manager_complete_failure`, `episode_bible_save_failed`를 ctx callback으로 남기려 한다. |
| **downstream 영향 경계** | 로그 출력은 남더라도 Stage4 post-processor의 구조화 audit trail이 빠진다. 특히 manager 파싱 실패 / 완전 실패 / episode bible 저장 실패는 운영자가 runtime audit 요약이나 후속 분석에서 일관되게 찾기 어려워진다. `stage4_complete` success summary source split은 별도 문서 `MFS-T3-02`에서 이미 다뤘으므로 이번 finding은 post-processor 측 audit slot 누락에 한정한다. |
| **현재 테스트 근거 또는 테스트 부재** | `tests/test_stage4_post_processor.py`는 `858`, `918`행에서 bare `MagicMock` ctx에 `audit_event`를 수동 주입하고도 `41 passed`로 초록이다. `tests/integration/test_patch_wiring.py:167`, `242`도 같은 패턴이다. real `Stage4Context`를 쓰는 audit-event test는 없다. |
| **기존 문서와의 중복 여부** | `related-but-new-live-wiring-surface` |
| **권장 후속 조치** | post-processor가 `ctx.audit_event`를 계약으로 쓸지, `app._audit_event`를 직접 쓸지 하나로 고정한다. 계약으로 유지한다면 Stage4Context에 slot/from_app 배선을 추가하고, real context 기반 post-processor regression test를 붙인다. |

---

### MLW-T3-005 — Stage4 테스트 다수가 real `Stage4Context`가 가질 수 없는 속성을 가짜 ctx에 주입해 false green을 만든다

| 필드 | 내용 |
|------|------|
| **ID** | `MLW-T3-005` |
| **Severity** | `P2` |
| **현상 요약** | Stage4 consumer 테스트 다수가 bare `MagicMock` ctx에 real `Stage4Context`에는 없는 속성을 수동 주입한다. 그 결과 production path에서 깨지는 slot contract와 silent no-op wiring이 test green 뒤에 숨는다. |
| **코드 근거** | `tests/test_stage4_context_builder.py:12-36`, `568`은 bare `MagicMock` ctx에 `generate_writer_guidance_v60_8`, `enrich_director_result`를 직접 넣는다. `tests/test_stage4_interview_round.py:16-40`은 `adaptive_manager`, `enrich_director_result`를 직접 넣는다. `tests/test_stage4_post_processor.py:858`, `918`은 `audit_event`를 직접 넣는다. 반면 real context 검증 파일 `tests/test_stage4_context.py`는 현재 대량 붕괴하고, `tests/test_stage4_interview_round.py:2415-2425`의 `from_app` 검증도 같이 깨진다. |
| **downstream 영향 경계** | 이번 재감리에서 확인된 `P0/P1/P2` drift가 test suite 일부 초록 뒤에 가려진다. Stage4 builder / interview-round / post-processor가 실제로는 받을 수 없는 callback을 받는다고 가정한 채 유지될 수 있다. |
| **현재 테스트 근거 또는 테스트 부재** | green 근거는 존재하지만 realism이 부족하다. `tests/test_stage4_context_builder.py` 46건, `tests/test_stage4_post_processor.py` 41건이 green이어도 real `Stage4Context` 계약을 보장하지 않는다. 반대로 real context 계열인 `tests/test_stage4_context.py`는 현재 깨져 있다. |
| **기존 문서와의 중복 여부** | `related-but-new-live-wiring-surface` |
| **권장 후속 조치** | Stage4 consumer fixture를 `Stage4Context` 실인스턴스나 최소 `spec_set=Stage4Context`로 바꾸고, impossible attribute 수동 주입을 금지한다. T5 realism 트랙과 연결하되, Stage4 전용 regression은 이 트랙에서 먼저 잠가야 한다. |

---

## PASS1 -> PASS2 -> PASS3

### PASS 1 — 표면 수집 (8 후보)

| # | 후보 | 확신도 |
|---|------|--------|
| 1 | `Stage4Context.__slots__`와 `__init__`/`from_app()` 불일치 | HIGH |
| 2 | `ctx.db` real-app drift | HIGH |
| 3 | `adaptive_manager` 미배선 | HIGH |
| 4 | `audit_event` 미배선 | HIGH |
| 5 | Stage4-specific MagicMock false green | HIGH |
| 6 | success path `app` / non-success path `ctx` callback source split | HIGH |
| 7 | `_director_mc_parts` dead code | HIGH |
| 8 | `current_project` 접근 스타일 / 주석 불일치 | LOW |

### PASS 2 — 교차 검증 (제거 3건)

| # | 후보 | 판정 | 사유 |
|---|------|------|------|
| 6 | success / non-success callback source split | 제거 | `docs/2026-03-13/MFS-T3-stage3-stage4-audit-callback-findings.md`의 `MFS-T3-02`가 이미 닫은 표면이다. 이번 문서에서는 cross-ref만 유지하고 재오픈하지 않는다. |
| 7 | `_director_mc_parts` dead code | 제거 | `docs/2026-03-13/T3-stage3-4-pipeline-audit-report.md`의 `T3-033`과 동일 표면이다. |
| 8 | `current_project` 접근 스타일 / 주석 불일치 | 제거 | style/document drift는 있으나 live wiring contract defect로 확정할 정도의 downstream 영향이 없다. |

### PASS 3 — 최종 확정 (5건)

| ID | Severity | 핵심 |
|----|----------|------|
| `MLW-T3-001` | `P0` | real app Stage4 entry가 `Stage4Context.from_app()`에서 즉시 붕괴 |
| `MLW-T3-002` | `P1` | smart retrieval의 DB relationship / manuscript slot이 real app에서 silent no-op |
| `MLW-T3-003` | `P2` | adaptive retry manager가 Stage4 real context에 실리지 않음 |
| `MLW-T3-004` | `P2` | post-processor audit_event wiring 누락으로 구조화 감사 누락 |
| `MLW-T3-005` | `P2` | Stage4 tests가 impossible ctx contract를 green으로 가림 |

### Severity 합계

| Severity | 건수 |
|----------|------|
| `P0` | 1 |
| `P1` | 1 |
| `P2` | 3 |
| `P3` | 0 |
| **합계** | **5** |

---

## Coverage Gap / Open Question

1. `MFS-T3-02`가 다룬 `stage4_complete` success-path callback source split은 이번 재감리에서도 여전히 살아 있지만, 기존 문서가 이미 PASS3로 잠근 표면이라 여기서는 중복 재오픈하지 않았다.
2. `Stage4Context` slot mismatch를 실제 코드로 고치기 전에는 runtime canary로 `adaptive_manager`, `audit_event`, `ctx.db` drift를 end-to-end 재현하기 어렵다. 이번 문서는 static + unit/synthetic evidence 기준으로 확정했다.

---

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 테스트 근거 / 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- PASS1 후보 -> PASS2 제거 -> PASS3 확정 요약 포함
- UTF-8 깨짐 패턴 미검출
