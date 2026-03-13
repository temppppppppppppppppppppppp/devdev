# MLW-T3: Stage4 Real-App Binding Findings

> 작성일: 2026-03-13
> 작성자: Claude Opus 4.6
> 트랙: Terminal 3 — Stage4 Real-App Binding
> 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
> 상태: `PASS3 확정`

---

## 조사 범위

- `main_a.py` — Stage4에 export하는 bound method 전반
- `modules/core/stage4_context.py` — Stage4Context (30 __slots__)
- `modules/core/stage4_context_builder.py` — 에피소드 컨텍스트 수집 (~2,500줄)
- `modules/core/stage4_interview_round.py` — 단일 면담 라운드 (~4,500줄)
- `modules/core/stage4_post_processor.py` — PASS 후처리 (~1,430줄)
- `modules/core/stage4_orchestrator.py` — 오케스트레이터 (~1,560줄)

---

## 확정 Finding 목록

### MLW-T3-001 — Stage4ContextBuilder `self.ctx.db` wiring 누락

| 필드 | 내용 |
|------|------|
| **ID** | MLW-T3-001 |
| **Severity** | **P1** |
| **현상 요약** | `Stage4ContextBuilder`가 `self.ctx.db`를 통해 DB에 접근하나 `db`는 `Stage4Context.__slots__`에 없음. `getattr(self.ctx, "db", None)` → 항상 None 반환. |
| **코드 근거** | `stage4_context_builder.py` L1229: `db = getattr(self.ctx, "db", None)` (NPC 관계 이력 조회 경로), L1309: `db = getattr(self.ctx, "db", None)` (원고 발췌 경로). 정상 경로는 `self.ctx.current_project.db`. |
| **downstream 영향 경계** | (1) `RetrievalSources.DB_NPC_RELATIONSHIP` 슬롯의 관계 이력 조회가 항상 빈 문자열 반환 → Director/CW에 NPC 관계 변화 컨텍스트 미전달. (2) `_fetch_manuscript_excerpt()` 항상 빈 문자열 → 연속성 참조 원고 발췌 미제공. |
| **현재 테스트 근거** | `tests/test_stage4_context_builder.py` — bare `MagicMock()` fixture 사용. `MagicMock().db`는 자동 생성되므로 테스트 초록. Real Stage4Context에서는 `AttributeError` → `getattr` fallback → None. |
| **기존 문서 중복 여부** | `related-but-new-live-wiring-surface` — 기존 T3-034(DB 내부 접근)과 같은 파일이나 `ctx.db` wiring 자체는 신규 표면. |
| **권장 후속 조치** | L1229, L1309의 `getattr(self.ctx, "db", None)`을 `getattr(getattr(self.ctx, "current_project", None), "db", None)`으로 교체. 또는 Stage4Context에 `db` 편의 프로퍼티 추가. |

---

### MLW-T3-002 — `audit_event` 콜백 Stage4Context 미배선

| 필드 | 내용 |
|------|------|
| **ID** | MLW-T3-002 |
| **Severity** | **P2** |
| **현상 요약** | `stage4_post_processor.py`가 `self.ctx.audit_event()`를 호출하나 `audit_event`는 `Stage4Context.__slots__`에 없고 `from_app()`에서도 배선되지 않음. Stage2Context에는 존재 (slot L75, from_app L236). |
| **코드 근거** | `stage4_post_processor.py` L815: `if callable(getattr(self.ctx, "audit_event", None)): self.ctx.audit_event("manager_parse_failure", ...)`, L840: `audit_event("manager_complete_failure", ...)`, L1023: `audit_event("episode_bible_save_failed", ...)`. `main_a.py` L2786: `def _audit_event(self, event_type, message, data=None)` — 실제 메서드 존재. |
| **downstream 영향 경계** | Manager LLM 파싱 실패, Manager 완전 실패, Episode Bible 저장 실패 3가지 audit 이벤트가 감사 로그에 기록되지 않음. `logging.error()`는 별도로 호출되므로 로그 파일에는 남지만, 구조화된 audit trail이 누락. |
| **현재 테스트 근거** | 테스트 부재 — `audit_event` 배선을 검증하는 Stage4 테스트 없음. `_report_soft_failure()` (L38)에서도 `getattr`으로 방어적 접근하여 None 반환 시 skip. |
| **기존 문서 중복 여부** | `related-but-new-live-wiring-surface` — Stage2Context에는 배선되어 있으므로 Stage4만의 wiring gap. |
| **권장 후속 조치** | Stage4Context.__slots__에 `audit_event` 추가 + `from_app()`에서 `audit_event=getattr(app, "_audit_event", None)` 배선. |

---

### MLW-T3-003 — `adaptive_manager` Stage4Context 미배선

| 필드 | 내용 |
|------|------|
| **ID** | MLW-T3-003 |
| **Severity** | **P2** |
| **현상 요약** | `stage4_interview_round.py`가 `self.ctx.adaptive_manager`를 통해 적응형 재시도 관리자를 호출하나, `adaptive_manager`는 `Stage4Context.__slots__`에 없고 `from_app()`에서도 배선되지 않음. |
| **코드 근거** | `stage4_interview_round.py` L3221: `_adaptive_mgr = getattr(self.ctx, "adaptive_manager", None)`. `main_a.py` L364: `self.adaptive_manager = None`, L1875: `self.adaptive_manager = _v50["get_adaptive_manager"]()`. |
| **downstream 영향 경계** | REJECT 시 `record_failure()` + `get_injection_prompt()` 호출이 항상 skip. 재시도 시 adaptive prompt injection이 동작하지 않아 동일 실패 패턴 반복 가능성. `failure_learner`는 별도 slot으로 배선되어 동작하지만 `adaptive_manager`의 `get_injection_prompt()`는 누락. |
| **현재 테스트 근거** | 테스트 부재 — adaptive_manager 배선을 검증하는 테스트 없음. getattr 방어로 crash는 미발생. |
| **기존 문서 중복 여부** | `none` — 신규 발견. |
| **권장 후속 조치** | Stage4Context.__slots__에 `adaptive_manager` 추가 + `from_app()`에서 `adaptive_manager=getattr(app, "adaptive_manager", None)` 배선. |

---

### MLW-T3-004 — `_director_mc_parts` dead code (기존 T3-033 확인)

| 필드 | 내용 |
|------|------|
| **ID** | MLW-T3-004 |
| **Severity** | **P2** |
| **현상 요약** | `stage4_post_processor.py` L1082에서 `getattr(self.ctx, "_director_mc_parts", None)` 접근. `_director_mc_parts`는 `Stage4InterviewRound.run()`의 로컬 변수(L1483)이며 ctx에 존재하지 않음. 인과 그래프 Director MC 주입이 dead code. |
| **코드 근거** | `stage4_post_processor.py` L1082-1084: `_director_mc_parts = getattr(self.ctx, "_director_mc_parts", None) / if isinstance(..., list): _director_mc_parts.append(...)`. `stage4_interview_round.py` L1483: `_director_mc_parts = [_mandatory_text] ...` (로컬 변수). |
| **downstream 영향 경계** | `_settle_episode()` 내 causal graph → Director MC 주입 경로가 항상 skip. 인과 관계 컨텍스트가 Director 판정에 미반영. 단, 이 코드는 PASS 후처리 단계에서 실행되므로 해당 라운드의 Director 판정은 이미 완료된 상태. 실질적 영향은 다음 에피소드 Director MC에 대한 것이 아니라 현 에피소드 후처리 내에서의 dead code. |
| **현재 테스트 근거** | `tests/test_ns4_s2_s4.py` L112: source-string assertion `"_director_mc_parts.append" in src` — 코드 존재만 확인, 실제 실행 불가 여부 미검증. |
| **기존 문서 중복 여부** | `already-covered-do-not-reopen` — `T3-stage3-4-pipeline-audit-report.md` L64, L167에서 T3-033으로 이미 진탐 확정. |
| **권장 후속 조치** | 기존 T3-033 remediation에 따라 dead code 제거 또는 설계 의도 재확인. 재오픈 불필요. |

---

### MLW-T3-005 — Stage4 테스트 전량 bare MagicMock, real-app from_app 검증 0건

| 필드 | 내용 |
|------|------|
| **ID** | MLW-T3-005 |
| **Severity** | **P3** |
| **현상 요약** | Stage4 관련 테스트 전체(test_stage4_context.py, test_stage4_orchestrator.py, test_stage4_context_builder.py, test_stage4_interview_round.py, test_stage4_post_processor.py)가 `MagicMock()` (spec 미지정)을 사용. `Stage4Context.from_app(real_app)` 통합 테스트 0건. |
| **코드 근거** | `test_stage4_context.py`: 31개 테스트 중 `spec=[]` 사용 2건(L66, L183)은 의도적 missing-attr 테스트. 나머지 29건 bare MagicMock. `test_stage4_orchestrator.py`: 전량 bare MagicMock ctx. |
| **downstream 영향 경계** | `main_a.py`에서 메서드 이름 변경(예: `_get_int_input` → `_get_integer_input`) 시 테스트 초록 유지, 런타임 실패. `from_app()` 내 `getattr(app, "_get_int_input", None)` → None → callback 미동작. |
| **현재 테스트 근거** | 구조적 부재 — integration 테스트 파일(`test_run_stage4_canary.py` 등)도 실제 SovereignApp 인스턴스 미사용. |
| **기존 문서 중복 여부** | `related-but-new-live-wiring-surface` — T5 터미널의 test realism 범위와 관련되나, T3는 Stage4 한정 wiring drift 위험 식별. |
| **권장 후속 조치** | (1) `MagicMock(spec=SovereignApp)` 또는 `spec=Stage4Context`로 전환 검토. (2) `from_app()` 호출 후 필수 slot None 여부 검증 integration 테스트 1건 추가. |

---

### MLW-T3-006 — ContextBuilder/PostProcessor `current_project` 접근 방어 불균일

| 필드 | 내용 |
|------|------|
| **ID** | MLW-T3-006 |
| **Severity** | **P3** |
| **현상 요약** | Stage4 consumer들이 `self.ctx.current_project`를 직접 접근(crash 가능)하는 경로와 `getattr(self.ctx, "current_project", None)`으로 방어적 접근하는 경로가 혼재. `current_project`는 `__init__` 필수 파라미터이므로 None일 수 없으나, 접근 스타일 불일치가 contract 불명확성 유발. |
| **코드 근거** | 직접 접근: `stage4_context_builder.py` L99 `self.ctx.current_project.master_bible`, L1517 `self.ctx.current_project.db.load_anchor(...)` 등 50+곳. 방어적 접근: L446 `project = getattr(self.ctx, "current_project", None)`, L546 등 10+곳. |
| **downstream 영향 경계** | 실질 crash 위험 없음 (필수 파라미터). 코드 리뷰 시 "None 가능?" 혼란 유발. |
| **현재 테스트 근거** | 테스트에서 `current_project`는 항상 MagicMock으로 제공 — 실제 None 경로 미검증. |
| **기존 문서 중복 여부** | `none` — 코딩 스타일 불일치, 기존 문서 미다룸. |
| **권장 후속 조치** | P3 이하 — 점진적 통일 가능. 필수 slot은 직접 접근으로 통일 권장. |

---

## PASS1 → PASS2 → PASS3 요약

### PASS 1 — 표면 수집 (8 후보)

| # | 후보 | 확신도 |
|---|------|--------|
| 1 | `self.ctx.db` wiring 누락 | HIGH |
| 2 | `audit_event` 미배선 | HIGH |
| 3 | `adaptive_manager` 미배선 | HIGH |
| 4 | `_director_mc_parts` dead code | HIGH |
| 5 | bare MagicMock 테스트 realism | MED |
| 6 | `current_project` 접근 불균일 | LOW |
| 7 | `from_app()` vs `ContextBuilder` attribute 불일치 | MED |
| 8 | 콜백 signature 미검증 | LOW |

### PASS 2 — 교차 검증 (제거 2건)

| # | 후보 | 판정 | 사유 |
|---|------|------|------|
| 7 | `from_app()` vs `ContextBuilder` 불일치 | **제거** | ContextBuilder는 `from_app()` 제공 slot만 사용 (14/30). `_stage4_context_budget_meta`도 slot에 포함. 불일치 없음. |
| 8 | 콜백 signature 미검증 | **제거** (T5에 위임) | 콜백 signature 검증은 test realism 범위. T5 터미널 조사 범위에 해당. |

### PASS 3 — 최종 확정 (6건)

| ID | Severity | 핵심 |
|----|----------|------|
| MLW-T3-001 | **P1** | `self.ctx.db` 접근 — NPC 관계 이력 + 원고 발췌 silent fail |
| MLW-T3-002 | **P2** | `audit_event` Stage4 미배선 — 3건 audit trail 누락 |
| MLW-T3-003 | **P2** | `adaptive_manager` 미배선 — adaptive retry injection 비활성 |
| MLW-T3-004 | **P2** | `_director_mc_parts` dead code (기존 T3-033, 재오픈 불필요) |
| MLW-T3-005 | **P3** | Stage4 테스트 전량 bare MagicMock, from_app 통합 테스트 0건 |
| MLW-T3-006 | **P3** | `current_project` 접근 방어 스타일 불균일 |

### Severity 합계

| Severity | 건수 |
|----------|------|
| P0 | 0 |
| P1 | 1 |
| P2 | 3 (T3-004는 기존 T3-033 재확인) |
| P3 | 2 |
| **합계** | **6** |

### Coverage Gap / Open Question

1. `Stage4ContextBuilder._smart_context_retrieval()` (L1160+)의 `SemanticQueryBroker` 경유 경로가 real-app에서 `ctx.memory`의 operational 상태에 따라 다른 결과를 내는지 — mock으로만 검증됨.
2. `Stage4PostProcessor._settle_episode()` 내 `self.ctx.agents["manager"]` 호출이 async future → sync fallback 경로에서 동일한 wiring을 사용하는지 — 실제 timeout 시나리오 미검증.

---

## 비고

- 본 조사는 read-only, static 분석이며 코드 수정은 수행하지 않았다.
- 모든 finding은 코드 근거 + 테스트 근거 + downstream 경계를 포함한다.
- MLW-T3-004는 기존 T3-033과 동일 표면이므로 `already-covered-do-not-reopen`으로 분류했다.
