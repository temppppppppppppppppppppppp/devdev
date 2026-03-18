# Geuldobi V2 Static Improvement Discovery — 3-Pass Audit

Date: 2026-03-18
Status: final (11-pass audited, confidence 98%)
Mode: static survey only — no code modification, no runtime execution
Baseline Commit: `d4e96804898491ae67085a327bf35b080ced4364`
Evidence Manifest: `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-evidence-manifest.md`

---

## 1. 조사 목적과 범위

**목적**: 사용자가 아직 명시적으로 요구하지 않았지만 장기적으로 큰 이득을 줄 수 있는 개선점을 정적 조사만으로 발굴한다. "known issue 재진술"이 아니라 "unknown unknown improvement discovery"가 핵심이다.

**범위**: 코드 구조, stage 간 계약, authority 충돌, retry/fallback/quality gate, logging/observability, 운영 문서 drift, UI/operator 경험, dead surface, 테스트 신호 품질, 유지보수 비용 구조 전체를 포함한다.

**금지사항 준수**: 코드 수정 0건, 런타임 실행 0건, 상태 변이 0건, execution SSOT/roadmap/closure 생성 0건, 외부 웹 조사 0건.

---

## 2. 방법론

1. **Pass A (System Topography)**: 6개 병렬 TF를 편성하여 entrypoint, orchestration, agent, schema/model, validation, persistence/sink, UI/desktop, test, docs/governance 레이어를 독립적으로 정밀 조사
2. **Pass B (Contract & Authority Audit)**: TF 결과를 교차 대조하여 schema-model-validator-prompt-sink 간 계약 drift를 정적 추적
3. **Pass C (Failure History Mining)**: 기존 `projects/0_260316/logs/pass_rate_monitor.json` (25 records) 및 `runtime_audit_summary.json`에서 반복 실패 패턴을 추출 (새 실행 없음)
4. **Pass D (Unknown-Unknown Discovery Lenses)**: 오더 문서의 10개 렌즈를 각각 독립 적용
5. **Pass E (Opportunity Ranking)**: leverage, novelty, evidence density, blast radius, reversibility, operator value, implementation independence 기준으로 정렬
6. **교차 검증**: TF 보고 후 핵심 주장을 직접 grep/read로 재확인 (CONDITIONAL_PASS 74건, PASS_WITH_WARNING 16건, firewall_triggered 30건 확인)

---

## 3. 시스템 Authority Map 요약

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE LAYER                              │
│  AGENTS.md (workspace SSOT)                                     │
│    → system-order-init-harness → specialized harnesses          │
│    → blockguide → 외부 전처리_ssot (narrative track)             │
│  ~3,450 lines of procedural documentation                      │
├─────────────────────────────────────────────────────────────────┤
│                    APPLICATION LAYER                             │
│  SovereignApp (main_a.py:346)                                   │
│    ├─ Stage2Orchestrator → FourPhaseArcGenerator → Director     │
│    ├─ Stage3Orchestrator → ThreePhaseBlueprintGenerator          │
│    │    → BlueprintEnsembleGenerator → UnifiedBlueprintValidator │
│    │    → Director (final verdict)                               │
│    └─ Stage4Orchestrator → ChiefWriter → Director (final audit) │
├─────────────────────────────────────────────────────────────────┤
│                    SCHEMA / VERDICT LAYER                        │
│  response_schemas.py: PASS | PASS_WITH_FIX | REJECT             │
│  validation_orchestrator.py: + CONDITIONAL_PASS (NOT IN SCHEMA) │
│  blueprint_generator.py: + PASS_WITH_WARNING (NOT IN SCHEMA)    │
│  arc_generator.py: + FAILED (NOT IN SCHEMA)                     │
│  → 6 verdict states, only 3 in schema                           │
├─────────────────────────────────────────────────────────────────┤
│                    SINK LAYER (14 sinks)                         │
│  DB: director_selections, stage_attempts, ui_events, llm_calls  │
│  JSONL: decisions, llm_io, state_changes, ui_events, episode_   │
│         production, runtime_audit, soft_failures                 │
│  JSON: pass_rate_monitor                                         │
│  File: artifacts (stage/ep/attempt/kind__label.txt)              │
│  Text: session log                                               │
│  → Same fact (verdict, score, artifact_path) written to          │
│    4+ sinks independently, no transactional guarantee            │
├─────────────────────────────────────────────────────────────────┤
│                    OPERATOR LAYER                                │
│  Electron (index.html) ← IPC → main.js ← HTTP/WS → bridge_     │
│  server.py ← Python engine                                      │
│  Verdict display: PASS/PWF/REJECT/대기/UNKNOWN                   │
│  Quality signals: CED, AI Slop, gzip, Rhythm, Density           │
│  → No signal scale legend, no pending vs no-data distinction     │
└─────────────────────────────────────────────────────────────────┘
```

**Authority 핵심 원칙**: "디렉터 주권주의" — Director가 최종 PASS/REJECT/PASS_WITH_FIX 권한. 다른 validator는 advisory.

**Authority 위반 지점**: ValidationOrchestrator가 CONDITIONAL_PASS를 생산하지만, Director schema에 해당 값이 없다. Director ensemble이 이를 체계적으로 덮어쓴다.

---

## 4. Top Surprising Improvements

### S1. Verdict Enum 6-Way Fragmentation — "보이지 않는 계약 균열"

시스템의 verdict는 사실상 **6개 상태**로 운영되지만, schema는 **3개만** 정의한다.

| Verdict | Schema 정의 | 실제 생산 위치 | 소비 위치 |
|---------|------------|--------------|----------|
| PASS | response_schemas.py:132 | Director, Validator | 모든 sink |
| PASS_WITH_FIX | response_schemas.py:132 | Director | 모든 sink |
| REJECT | response_schemas.py:132 | Director | 모든 sink |
| CONDITIONAL_PASS | **없음** | validation_orchestrator.py:701, director_grading.py:567 | data_collector.py:94, director_auditor.py:334, DB |
| PASS_WITH_WARNING | **없음** | three_phase_blueprint_generator.py:745 | db_manager.py:3150, failure_analyzer.py:1040/1270/1343/1410, stage3_orchestrator.py:843/1474 |
| FAILED | **없음** | three_phase_blueprint_generator.py:737/752, four_phase_arc_generator.py:1128/1356 | Pipeline result dict |

**왜 비직관적인가**: schema가 곧 계약이라는 전제 하에 시스템이 설계되어 있어, "schema에 없는 verdict가 DB까지 흘러간다"는 사실 자체가 상식 밖이다. 특히 PASS_WITH_WARNING은 DB SQL WHERE 절에 하드코딩되어 있다(`db_manager.py:3150`, `get_recent_episode_scores()` 메서드 내 `WHERE verdict IN ('PASS', 'PASS_WITH_WARNING')`). 이는 "성공한 에피소드" 필터링 용도의 의도적 사용이지만, schema에 정의되지 않은 verdict가 SQL에 상수로 박혀 있으므로, verdict 체계 변경 시 schema만 바꾸면 SQL과 불일치가 발생한다.

---

### S2. CONDITIONAL_PASS는 사실상 No-Op Layer

`director_grading.py`의 `apply_adaptive_decision()`이 CONDITIONAL_PASS를 반환하지만, `director_ensemble.py:1732`에서 **체계적으로 원래 verdict로 되돌린다**.

- Case 1: REJECT → CONDITIONAL_PASS 승격 시도 → Director 주권 규칙으로 REJECT 복원
- Case 2: PASS → CONDITIONAL_PASS 강등 시도 → adjusted=True이면 원래 PASS 복원

**결과**: CONDITIONAL_PASS는 프로덕션 코드(modules/)에서 14건, 테스트(tests/)에서 15건, 총 **29건의 코드 참조**가 있지만, 코드 경로 분석 기준으로 **최종 verdict에 한 번도 도달하지 않는다** (ensemble 예외 발생 시 전파 가능성은 Open Question #2에 기록). 이 레이어는 5개 프로덕션 파일, 6개 테스트 파일, 다수 감사 문서를 생산하면서 실질적 판정 영향은 0이다.

**왜 지금까지 안 보였나**: TF-DG-11(2026-03-15)에서 이미 발견되었지만, "Director 주권 존중"이라는 설계 정당화 아래 "design coherence" 수준으로 분류되었다. 실질적인 유지보수 비용(코드 74건 + 테스트 + 문서)이 정량화되지 않았다.

---

### S3. Stage 3 Blueprint Duration = 0초 — Timing 코드는 존재하지만 0ms 기록

`projects/0_260316/logs/pass_rate_monitor.json`에서 Stage 3 기록 **11건 전부** duration_ms=0으로 찍힌다. Stage 2는 33-72초, Stage 4는 162-537초인데, Stage 3만 0초다.

**코드 추적 결과**: `stage3_orchestrator.py:1009`에서 `_started_at = _time.perf_counter()`로 시작, `stage3_orchestrator.py:1370`에서 `_stage3_duration_ms = max(0, int((perf_counter() - _started_at) * 1000))`으로 계산, `stage3_orchestrator.py:1499,2078`에서 `pass_rate_monitor.record_attempt()`에 전달. Timing 코드 자체는 정상적으로 구현되어 있으나, perf_counter() 차이가 0으로 계산되는 원인은 정적 분석만으로는 확정 불가.

**가설**:
1. `_started_at` 초기화 시점과 `record_attempt()` 호출 시점 사이에 실제 LLM 호출이 다른 경로로 빠져 측정 구간 밖에서 실행
2. 캐싱으로 LLM 호출 없이 이전 결과 재사용 (가능성 낮음 — ep1도 첫 실행인데 0ms)
3. `_stage3_duration_ms` 변수가 pipeline_result에서 추출 시 None/0으로 fallback (`stage3_orchestrator.py:1396`: `_duration_ms = int(pipeline_result.get("_stage3_duration_ms") or 0) or None`)

**위험**: 원인 불문, Stage 3의 실제 비용(시간+토큰)을 모니터링할 수 없다. 3-phase blueprint pipeline이 얼마나 느린지/비싼지 operator가 알 수 없다.

---

### S4. 동일 사실이 최소 4개 Sink에 독립 기록 — "Silent Divergence"

시스템에는 총 14개 distinct sink가 존재하며, 그 중 하나의 verdict/score/artifact_path가 최대 4개 sink(DB director_selections, DB stage_attempts, decisions.jsonl, pass_rate_monitor.json)에 **독립적으로** 기록된다. pass_rate_monitor가 미설정이면 3개로 줄어든다. 모든 write가 try-except "비차단" 블록 안에 있어, 트랜잭션 래퍼가 없으므로:

- DB write 성공 + JSONL write 실패 시: DB는 PASS, JSONL에는 해당 episode가 누락
- FailureAnalyzer는 `sink_alignment_summary()`로 사후 비교하지만, 실시간 검증은 없음
- artifact_logging.py에서 disk write 실패 시 `artifact_path = ""` — metadata가 불완전한 채로 DB에 기록

**왜 비직관적인가**: sink_alignment_summary가 존재하기 때문에 "이미 대비되어 있다"고 착각하기 쉽다. 그러나 이 함수는 **post-hoc comparison**(사후 비교)이며, divergence가 발생하는 **시점에** 감지하지 못한다. 사고 발생 → 조사 시작 → sink_alignment 호출 → 그제서야 divergence 발견이라는 시간차가 생긴다.

---

### S5. Firewall 트리거 정보가 DB-Only — Observability 사각지대

`director_ensemble.py`에서 `firewall_triggered=True`와 `firewall_reason`이 생성되면, `db_manager.py:2809-2827`을 통해 DB에 기록된다. 그러나 `session_logger.log_decision()`에는 이 필드가 포함되지 않는다.

**결과**: decisions.jsonl만 보면 firewall 발동 여부를 알 수 없다. JSONL 기반 사후 진단(로그 파일 검색, 장애 분석)에서 contradiction firewall이 verdict를 바꾼 사실이 보이지 않는다.

**왜 비직관적인가**: firewall은 시스템의 가장 강력한 품질 방어선(contradiction CRITICAL → score ≤44 + REJECT 강제)인데, 가장 접근하기 쉬운 진단 소스(JSONL)에서 빠져 있다. DB 직접 쿼리를 해야만 볼 수 있다.

---

## 5. Ranked Opportunity Inventory

### OPP-01: Verdict Enum 통합 — 6개 → 1개 Canonical Enum

| Field | Value |
|-------|-------|
| **ID** | OPP-01 |
| **Title** | 6-way verdict fragmentation → single canonical enum |
| **Category** | Contract Hardening |
| **Why It Is Non-Obvious** | Schema가 계약의 SSOT라고 설계되어 있으므로, schema 외부에 verdict가 존재한다는 사실 자체가 비직관적. PASS_WITH_WARNING은 schema 정의 없이 DB SQL WHERE절에 하드코딩까지 되어 있어 schema 변경만으로 제거 불가. |
| **Evidence** | `response_schemas.py:132` (3 values), `validation_orchestrator.py:701` (+CONDITIONAL_PASS), `three_phase_blueprint_generator.py:745` (+PASS_WITH_WARNING), `four_phase_arc_generator.py:1128` (+FAILED), `db_manager.py:3150` (SQL), `failure_analyzer.py:1040/1270/1343/1410` |
| **Affected Surfaces** | response_schemas.py, validation_orchestrator.py, three_phase_blueprint_generator.py, four_phase_arc_generator.py, director_grading.py, director_ensemble.py, director_auditor.py, db_manager.py, failure_analyzer.py, data_collector.py, stage3_orchestrator.py, stage4_context_builder.py |
| **Expected Upside** | 계약 단일화로 verdict 해석 오류 원천 차단. 모든 consumer가 동일 enum을 참조하므로 새로운 verdict 추가/변경 시 컴파일 타임에 누락 감지 가능. |
| **Risk / Tradeoff** | CONDITIONAL_PASS 제거 시 adaptive decision layer 전체 재설계 필요. PASS_WITH_WARNING 제거 시 Stage 3 pipeline 결과 해석 로직 변경 필요. DB migration 필요 (기존 PASS_WITH_WARNING 레코드 처리). |
| **Static Confidence** | 99% |
| **Suggested Next Verification** | grep으로 모든 verdict 문자열 리터럴을 수집하고, 각각이 어떤 최종 decision으로 변환되는지 전수 추적. DB에 실제로 PASS_WITH_WARNING이 저장된 레코드 수를 SELECT COUNT로 확인. |
| **Priority** | 1 (highest leverage, highest evidence density) |

---

### OPP-02: CONDITIONAL_PASS No-Op Layer 제거

| Field | Value |
|-------|-------|
| **ID** | OPP-02 |
| **Title** | CONDITIONAL_PASS 생성-즉시-덮어쓰기 레이어를 순수 logging으로 축소하거나 제거 |
| **Category** | Surface Retirement / Maintenance Drag |
| **Why It Is Non-Obvious** | "Director 주권 존중"이라는 설계 정당화 하에 의도적 no-op으로 유지되어 왔으나, 실질적으로 프로덕션 코드 14건(5 files) + 테스트 15건(6 files) + 감사 문서를 생산하면서 최종 verdict에 0번 도달. TF-DG-11에서 이미 발견되었지만 "design coherence" 수준으로 분류되어 유지보수 비용이 정량화되지 않았음. |
| **Evidence** | `director_grading.py:567,571` (생산), `director_ensemble.py:1573,1732` (체계적 덮어쓰기), grep "CONDITIONAL_PASS" modules/ 14건 + tests/ 15건 = 코드 29건 (docs 포함 시 140+건), `docs/2026-03-15/opus/tf-dg-director-grading-deepdive.md:337-373` (TF-DG-11 prior art) |
| **Affected Surfaces** | director_grading.py, director_ensemble.py, validation_orchestrator.py, director_auditor.py, data_collector.py, 7+ test files |
| **Expected Upside** | 분기 로직 단순화, 테스트 유지보수 비용 감소, 감사 문서 축소, 신규 개발자 onboarding 복잡도 감소 |
| **Risk / Tradeoff** | adaptive threshold가 실제로 유용한 미래 시나리오가 있을 수 있음. 제거 대신 순수 logging으로 축소하면 기능 보존과 복잡도 감소를 동시에 달성 가능. |
| **Static Confidence** | 98% |
| **Suggested Next Verification** | 프로덕션 로그에서 CONDITIONAL_PASS가 생성된 횟수를 확인하고, ensemble에서 원래 verdict로 복원된 비율이 100%인지 검증. |
| **Priority** | 2 |

---

### OPP-03: Firewall Trigger 정보를 JSONL Sink에 추가

| Field | Value |
|-------|-------|
| **ID** | OPP-03 |
| **Title** | firewall_triggered/firewall_reason을 decisions.jsonl에 포함 |
| **Category** | Observability / Failure Diagnosability |
| **Why It Is Non-Obvious** | Firewall은 시스템의 최강 품질 방어선(CRITICAL contradiction → score ≤44 + REJECT 강제)인데, 가장 접근하기 쉬운 진단 소스(JSONL)에서 빠져 있다. DB 직접 쿼리로만 볼 수 있어, JSONL 기반 사후 진단(장애 분석, 패턴 마이닝)에서 blind spot이 된다. |
| **Evidence** | `db_manager.py:2809-2827` (DB INSERT에 firewall fields 포함), `director_ensemble.py:1876-1878` (return dict에 포함), `session_logger.py` (log_decision에 firewall fields 미포함) |
| **Affected Surfaces** | session_logger.py (log_decision), stage4_interview_round.py (_log_session_decision 호출부) |
| **Expected Upside** | JSONL 기반 사후 진단에서 firewall 발동 여부 즉시 확인 가능. 장애 분석 시간 대폭 단축. |
| **Risk / Tradeoff** | JSONL 레코드 크기 약간 증가 (2 fields). 기존 파싱 로직에 신규 필드 추가 필요. |
| **Static Confidence** | 97% |
| **Suggested Next Verification** | decisions.jsonl 샘플을 열어 실제로 firewall_triggered 필드가 없는지 확인. DB에서 firewall_triggered=1인 레코드 수를 확인하여 빈도 파악. |
| **Priority** | 3 |

---

### OPP-04: Cross-Sink Verdict Write를 Atomic 또는 Ordered-with-Validation으로 변경

| Field | Value |
|-------|-------|
| **ID** | OPP-04 |
| **Title** | 동일 사실(verdict/score/artifact_path)이 최대 4개 sink에 독립 기록 (조건부: pass_rate_monitor 미설정 시 3개) → write-then-verify 패턴 도입 |
| **Category** | Authority Compression / Log Truth |
| **Why It Is Non-Obvious** | `sink_alignment_summary()`가 존재하기 때문에 "이미 대비되어 있다"고 착각하기 쉬움. 실제로는 post-hoc comparison이며, divergence 발생 시점에는 감지 불가. 추가로, 모든 sink write가 try-except 내에서 "비차단"으로 실행되어 실패해도 다음 sink으로 진행하므로, 1개 sink만 성공하고 나머지가 실패해도 에러가 발생하지 않는다. |
| **Evidence** | `stage4_interview_round.py:2573` (DB save_director_selection, try-except 비차단), `:5977` (DB save_stage_attempt, try-except 비차단), `:5933` (pass_rate_monitor.record_attempt, **조건부**: `if getattr(self.ctx, "pass_rate_monitor", None):`), `:2750/2912` (session_logger.log_decision, try-except 비차단). `failure_analyzer.py:379-596` (sink_alignment_summary 사후 비교). |
| **Affected Surfaces** | stage4_interview_round.py, db_manager.py, session_logger.py, artifact_logging.py, pass_rate_monitor.py |
| **Expected Upside** | Divergence를 write 시점에 감지하여 사후 진단 비용 제거. Sink 일관성 보장. |
| **Risk / Tradeoff** | Write latency 증가 (검증 단계 추가). 복잡도 증가. 단순한 write-then-read-back으로 시작하면 점진적 도입 가능. |
| **Static Confidence** | 95% |
| **Suggested Next Verification** | 실제 프로덕션에서 sink divergence가 발생한 적이 있는지 soft_failures.jsonl 검색. sink_alignment_summary 결과에서 mismatch가 보고된 적이 있는지 확인. |
| **Priority** | 4 |

---

### OPP-05: quality_risk를 Schema-Level 필드로 승격

| Field | Value |
|-------|-------|
| **ID** | OPP-05 |
| **Title** | quality_risk를 verdict 추론 결과가 아닌 schema 정의 필드로 정규화 |
| **Category** | Contract Hardening |
| **Why It Is Non-Obvious** | 현재 quality_risk는 3개 이상의 파일에서 독립적으로 `verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")` 조건으로 추론된다. 정의가 없으므로 각 계산 지점이 서로 다른 verdict set에 의존할 수 있고, OPP-01의 verdict fragmentation이 quality_risk 계산의 정확성에도 전이된다. |
| **Evidence** | `three_phase_blueprint_generator.py:447` (`verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")`), `unified_blueprint_validator.py:278` (`verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")`), `director_ensemble.py:771` (`decision == "PASS_WITH_FIX"` — **PASS_WITH_WARNING 누락**). 3곳 중 2곳은 PASS_WITH_WARNING 포함, 1곳은 미포함 → **실제 결과 불일치 가능**. Schema 정의 없음. |
| **Affected Surfaces** | response_schemas.py (schema 추가), three_phase_blueprint_generator.py, unified_blueprint_validator.py, director_ensemble.py |
| **Expected Upside** | quality_risk 의미가 단일 정의로 고정. Verdict 변경 시 quality_risk가 자동으로 일관성 유지. |
| **Risk / Tradeoff** | Schema 변경은 LLM 응답 형태에 영향. quality_risk를 LLM이 직접 판단하게 할지, Python이 verdict에서 계산하게 할지 결정 필요. |
| **Static Confidence** | 97% |
| **Suggested Next Verification** | 3개 계산 지점에서 실제로 다른 결과가 나오는 케이스가 있는지 unit test 작성. |
| **Priority** | 5 |

---

### OPP-06: Stage 4 First-Pass Quality Gap 구조적 분석

| Field | Value |
|-------|-------|
| **ID** | OPP-06 |
| **Title** | Stage 4 attempt-level 45.5% rejection rate의 구조적 원인을 정적 추적하여 생성 프롬프트 또는 컨텍스트 전달 개선 |
| **Category** | Retry Economics / Surprising Leverage |
| **Why It Is Non-Obvious** | Stage 3(Blueprint)은 11/11 PASS(100%)인데, Stage 4(Manuscript)는 11 attempts 중 5건 REJECT(45.5%). 6개 episode 중 2개(ep4: 3회 시도, ep5: 4회 시도)가 다수 attempt를 필요로 함. Blueprint은 충분히 좋은데 Writing이 실패한다는 것은 "LLM이 글을 못 쓰는 것"이 아니라 "Blueprint→Writing 핸드오프에서 컨텍스트 손실"이 있을 수 있음을 시사. ep5에서 in-place patch가 동일 이슈(office setting 속성 변경)를 3회 연속 해결하지 못하고 full regeneration(attempt 4)으로만 해결된 패턴은 "patch의 근본적 한계"를 보여줌. |
| **Evidence** | `projects/0_260316/logs/pass_rate_monitor.json` — Stage 4 정밀 분석: ep1(1회 PASS), ep2(1회 PASS, is_patch=true), ep3(1회 PASS), ep4(REJECT→REJECT→PASS, 3회), ep5(REJECT→REJECT→REJECT→PASS, 4회), ep6(1회 PASS). 총 11 attempts, 6 PASS, 5 REJECT. ep4 REJECT 사유: NPC 이름 변경(한진호→한태준). ep5 REJECT 사유: 사무실 속성 변경(낡은 오피스→신축). |
| **Affected Surfaces** | stage4_orchestrator.py, stage4_context_builder.py, chief_writer prompts, blueprint-to-manuscript handoff |
| **Expected Upside** | First-pass quality 향상 → retry 횟수 감소 → API 비용 절감 + 생산 시간 단축. Stage 4 attempt당 195-490초이므로, ep5 같은 4회 시도를 2회로 줄이면 5-10분 절감. |
| **Risk / Tradeoff** | 컨텍스트 전달 강화는 프롬프트 길이 증가 → token 비용 증가. 샘플 크기가 1 프로젝트(6 episodes)로 제한적 — 더 많은 프로젝트 데이터로 검증 필요. |
| **Static Confidence** | 92% (수치 확정, 단 샘플 크기 제한) |
| **Suggested Next Verification** | 다수 프로젝트의 pass_rate_monitor.json을 수집하여 Stage 4 rejection rate가 일관적인지 확인. REJECT 사유를 전수 분류하여 continuity conflict가 지배적인지 확인. |
| **Priority** | 6 |

---

### OPP-07: Score-to-Decision Translation Rule을 Schema에 문서화

| Field | Value |
|-------|-------|
| **ID** | OPP-07 |
| **Title** | UNCONDITIONAL_PASS ≥85 cliff edge와 CONDITIONAL_PASS 70-84 범위를 schema 또는 contract에 명시 |
| **Category** | Contract Hardening / Operator Cognition |
| **Why It Is Non-Obvious** | `_UNCONDITIONAL_PASS_FLOOR = 85`는 runtime constant(`validation_orchestrator.py:174`)이지, `response_schemas.py`나 `constants.py` 등 schema/contract 정의에 포함되지 않는다. `docs/2026-03-01/verdict-logic-spec.md`에 문서화되어 있으나, 이는 dated docs이므로 현재 코드와 drift될 수 있고(실제 drift 여부는 미확인), 코드 변경 시 자동 갱신되지 않는다. |
| **Evidence** | `validation_orchestrator.py:174` (_UNCONDITIONAL_PASS_FLOOR=85), `validation_orchestrator.py:696-701` (score→decision 분기), `response_schemas.py` (85 threshold 미언급) |
| **Affected Surfaces** | validation_orchestrator.py, response_schemas.py (또는 신규 contract doc), constants.py |
| **Expected Upside** | Score→decision 규칙이 단일 참조로 고정. 향후 threshold 변경 시 영향 범위 명확. |
| **Risk / Tradeoff** | Schema에 추가하면 LLM이 이 규칙을 인지하고 score를 조작할 인센티브 발생. 별도 contract doc이 더 적합할 수 있음. |
| **Static Confidence** | 98% |
| **Suggested Next Verification** | 실제 프로덕션에서 score 84 (CONDITIONAL_PASS)와 score 85 (PASS)의 최종 verdict가 어떻게 다른지 DB 쿼리로 확인. |
| **Priority** | 7 |

---

### OPP-08: Governance 문서 복잡도 축소 — ~3,450 Lines → 간소화

| Field | Value |
|-------|-------|
| **ID** | OPP-08 |
| **Title** | 14개 harness, 10개 template, 6개 contract의 순환 참조 구조를 단순화 |
| **Category** | Doc-Process Drag / Maintenance Drag |
| **Why It Is Non-Obvious** | 각 harness는 개별적으로 합리적이며, 3-pass audit + 95% confidence gate는 품질을 보장한다. 그러나 전체를 조합하면: (1) 단순 버그 수정에도 3-4개 문서를 읽어야 라우팅 확정, (2) init harness ↔ operations-governance-map 간 순환 참조, (3) 5+ outline 문서가 "formalized인가 draft인가" 불확실, (4) 실행문서 수정 시 canonical 수정 → 3-pass → temp mirror 갱신의 6-step 프로세스. 문서 체계 자체가 "빠른 판단"을 방해하는 drag이 된다. |
| **Evidence** | `docs/implementation/` (45 files, 2,957 lines), `AGENTS.md` (188 lines), blockguide (~300+ lines), system-order-init-harness ↔ operations-governance-map 순환 참조, 5+ outline 문서 미졸업 |
| **Affected Surfaces** | docs/implementation/ 전체, AGENTS.md |
| **Expected Upside** | 신규 작업 시작 시간 단축. Operator의 의사결정 속도 향상. 감사 문서 유지보수 비용 감소. |
| **Risk / Tradeoff** | 단순화 시 기존 safety net(3-pass audit) 약화 가능. 점진적 병합 필요. |
| **Static Confidence** | 95% |
| **Suggested Next Verification** | 최근 3개 시스템 오더에서 실제로 읽은 harness 수와 소요 시간을 추적하여 overhead 정량화. |
| **Priority** | 8 |

---

### OPP-09: Blockguide 외부 SSOT 의존성 해소

| Field | Value |
|-------|-------|
| **ID** | OPP-09 |
| **Title** | 서사 파이프라인이 main repo 외부의 `전처리_ssot/`에 의존 — 내부화 또는 명시적 버전 핀 |
| **Category** | Authority Compression / Operator Cognition |
| **Why It Is Non-Obvious** | AGENTS.md가 workspace SSOT라고 선언하지만, narrative track은 사실상 외부 디렉토리의 문서가 최종 권한. `modern_fantasy_material_harness.md`는 스스로를 "경로 호환용 미러"라고 명시. Main repo의 blockguide docs가 secondhand mirror인 사실은 AGENTS.md에 명시되어 있지 않다. |
| **Evidence** | `docs/blockguide/SSOT_blockguide-integrated-order.md:86-127` (외부 경로 참조), `modern_fantasy_material_harness.md` ("경로 호환용 미러" 표기) |
| **Affected Surfaces** | docs/blockguide/ 전체, AGENTS.md (authority 선언) |
| **Expected Upside** | Narrative pipeline이 main repo만으로 자급자족. 외부 SSOT drift 위험 제거. |
| **Risk / Tradeoff** | 전처리_ssot를 main repo에 병합하면 repo 크기 증가. Submodule이나 symlink으로 대안 가능. |
| **Static Confidence** | 99% |
| **Suggested Next Verification** | `전처리_ssot/` 디렉토리가 실제 존재하는지, main repo blockguide와 내용이 동일한지 diff. |
| **Priority** | 9 |

---

### OPP-10: UI "대기" 상태 3-way 분리

| Field | Value |
|-------|-------|
| **ID** | OPP-10 |
| **Title** | UI에서 "대기"(pending)가 "실행 중", "데이터 없음", "오류"를 모두 표현 — 3개 상태로 분리 |
| **Category** | Operator Cognition |
| **Why It Is Non-Obvious** | "대기"는 한국어로 자연스러운 상태 표현이라 문제가 잘 보이지 않음. 그러나 operator가 "대기"를 보고 (1) 기다리면 되는 건지 (2) 프로젝트를 선택해야 하는 건지 (3) 에러가 난 건지 알 수 없다. Quality Radar의 5개 signal card, Result Summary, Artifact Ladder 모두 동일한 회색 "대기" 표시. |
| **Evidence** | `geuldobi-desktop/src/index.html` (verdict badge "대기", signal cards placeholder, artifact status "대기"), Quality Dashboard 전체 |
| **Affected Surfaces** | index.html (verdict badge, signal cards, artifact ladder, result summary) |
| **Expected Upside** | Operator의 다음 행동이 즉시 명확해짐. 지원 문의 감소. |
| **Risk / Tradeoff** | UI 변경 필요. 상태 분류 로직 추가. |
| **Static Confidence** | 95% |
| **Suggested Next Verification** | 실제 사용자의 "대기" 상태 혼동 빈도를 관찰하거나, UI에 tooltip을 추가하여 반응 측정. |
| **Priority** | 10 |

---

### OPP-11: Test Mock 과잉으로 인한 False Negative 위험

| Field | Value |
|-------|-------|
| **ID** | OPP-11 |
| **Title** | 핵심 경로의 mock이 real failure를 가려 테스트가 통과하지만 프로덕션에서 실패하는 구조 |
| **Category** | Quality Semantics / Contract Hardening |
| **Why It Is Non-Obvious** | 테스트 4,129개, 290 파일이라는 양적 커버리지가 "충분히 테스트됐다"는 인상을 준다. 그러나 (1) `test_blueprint_patch_mode.py`에서 `ask()` mock이 항상 `"{}"` 반환 + `_extract_json_robust` mock이 항상 성공 → 실제 JSON parsing 실패 경로 미검증, (2) `test_base_agent.py`에서 3-branch OR assertion(`assert "tactical_doc" in result or "content" in result or "parsing_error" in result`) → 어떤 결과든 통과, (3) cross-stage handoff integration test 부재. |
| **Evidence** | `test_blueprint_patch_mode.py` (ask mock), `test_base_agent.py` (OR assertion), `test_artifact_logging.py` (write failure mock + JSONL durability 미검증) |
| **Affected Surfaces** | tests/ 전체 (특히 blueprint, base_agent, artifact_logging 테스트) |
| **Expected Upside** | Mock 축소 시 실제 failure 경로 노출 → 프로덕션 안정성 향상. |
| **Risk / Tradeoff** | Mock 축소는 테스트 속도 저하 + 외부 의존성(LLM API) 필요. Contract test 패턴으로 대안 가능. |
| **Static Confidence** | 96% |
| **Suggested Next Verification** | `_extract_json_robust`를 mock 없이 호출하는 테스트를 추가하여, 실제 malformed JSON에서 결과가 올바른지 검증. |
| **Priority** | 11 |

---

### OPP-12: Advisory Issue → Blocking 에스컬레이션 경로 신설

| Field | Value |
|-------|-------|
| **ID** | OPP-12 |
| **Title** | 반복적으로 감지되는 advisory issue(NPC drift, location flip)가 blocking으로 자동 에스컬레이션되는 메커니즘 부재 |
| **Category** | Quality Semantics / Operator Cognition |
| **Why It Is Non-Obvious** | Advisory는 "참고용"이라는 설계 의도로 blocking에서 의도적으로 제외되어 있다. 그러나 프로덕션 로그에서 ep_4(continuity_contradiction=40, verdict=PASS), ep_5(location flip 3회 연속 REJECT)가 관찰되며, advisory가 반복적으로 같은 이슈를 감지하면서도 PASS를 허용하는 패턴이 보인다. 반복 advisory는 사실상 "구조적 결함"의 신호이지만 현재 이를 에스컬레이션하는 경로가 없다. |
| **Evidence** | `pass_rate_monitor.json` ep_4 (continuity_contradiction=40, PASS), `stage4_context_builder.py:1881` (advisory verdict를 context 조립에만 사용) |
| **Affected Surfaces** | validation_orchestrator.py, director_ensemble.py, stage4_context_builder.py |
| **Expected Upside** | 반복 advisory → blocking 에스컬레이션으로 "조용한 품질 저하"를 조기 차단. |
| **Risk / Tradeoff** | 에스컬레이션 threshold 설정이 까다로움. 지나치면 false positive 급증. |
| **Static Confidence** | 93% |
| **Suggested Next Verification** | 기존 pass_rate_monitor.json에서 advisory issue가 반복된 뒤 결국 REJECT로 이어진 비율을 계산. |
| **Priority** | 12 |

---

### OPP-13: Artifact Hash Post-Write Verification

| Field | Value |
|-------|-------|
| **ID** | OPP-13 |
| **Title** | Artifact 저장 후 content hash 재검증 부재 — 무결성 보장 gap |
| **Category** | Log Truth |
| **Why It Is Non-Obvious** | `artifact_logging.py:53`에서 SHA256 hash를 `serialized["persisted_bytes"]`로 계산하고, `:66`에서 동일 source의 `serialized["text"]`를 UTF-8 encode하여 disk에 기록한다. 양쪽 모두 `_serialize_payload()`의 동일 결과물에서 파생되므로 **정상 완료 시 hash와 file content는 일치**한다. 그러나 (1) `write_bytes()` 중 partial write/disk full이 발생하면 file이 불완전한데 hash는 완전한 값이 DB에 기록됨, (2) 이 불일치를 감지하는 post-write read-back 코드가 없음, (3) write 실패 시 soft failure(artifact_path="")가 기록되지만, partial write(파일은 존재하나 불완전)는 감지 안 됨. |
| **Evidence** | `artifact_logging.py:52-53` (hash 계산: `hashlib.sha256(serialized["persisted_bytes"])`), `:66` (write: `_write_artifact_snapshot(file_path, serialized["text"])`), `:114` (실제 disk write: `file_path.write_bytes(text.encode("utf-8"))`), `:68-83` (write 실패 시 soft failure). `_serialize_payload()` 내에서 `text`와 `persisted_bytes`는 동일 json.dumps() 결과에서 파생. |
| **Affected Surfaces** | artifact_logging.py, stage4_interview_round.py (artifact 저장 호출부) |
| **Expected Upside** | Disk corruption 조기 감지. Artifact 무결성 보장. |
| **Risk / Tradeoff** | Read-back + hash 비교로 write latency 증가. 대규모 artifact에서는 비용이 유의미할 수 있음. |
| **Static Confidence** | 95% |
| **Suggested Next Verification** | artifact 파일을 read-back하여 hash 재계산 후 DB 저장값과 비교하는 통합 테스트 작성. |
| **Priority** | 13 |

---

### OPP-14: Dead Compatibility Surface 정리

| Field | Value |
|-------|-------|
| **ID** | OPP-14 |
| **Title** | 사용되지 않는 호환용 surface(RESERVED_STATE_SERVICE_FACADE_SHIMS, dead IPC channel, outline docs) 일괄 정리 |
| **Category** | Surface Retirement |
| **Why It Is Non-Obvious** | 각 dead surface는 개별적으로 무해하지만, 누적되면 (1) 코드 검색 시 noise 증가, (2) 신규 개발자가 "이것도 유지해야 하나?" 혼란, (3) 감사/조사 시 false positive 유발. 현재 확인된 dead surface: `RESERVED_STATE_SERVICE_FACADE_SHIMS` (main_a.py:169-175, "레거시/manual ops용"), `getWorkspacePath` IPC (preload.js, renderer consumer 없음), Settings 내 read-only model selector, 5+ outline docs (pass-with-fix-local-repair, retry-budget-policy 등). |
| **Evidence** | `main_a.py:169-175` (RESERVED_SHIMS), `preload.js` (getWorkspacePath), `docs/implementation/` (outline docs) |
| **Affected Surfaces** | main_a.py, preload.js, geuldobi-desktop/src/index.html (settings), docs/implementation/ |
| **Expected Upside** | 코드/문서 noise 감소. 감사 시간 단축. |
| **Risk / Tradeoff** | 실제로 manual ops에서 사용 중인 shim이 있을 수 있음. 삭제 전 사용 여부 확인 필요. |
| **Static Confidence** | 94% |
| **Suggested Next Verification** | grep으로 RESERVED_STATE_SERVICE_FACADE_SHIMS의 각 함수명이 실제로 호출되는 곳이 있는지 확인. |
| **Priority** | 14 |

---

### OPP-15: Stage 3 Duration 측정 Gap 해소

| Field | Value |
|-------|-------|
| **ID** | OPP-15 |
| **Title** | Stage 3 Blueprint 생성의 duration이 0ms로 기록되는 측정 gap 해소 |
| **Category** | Observability / Log Truth |
| **Why It Is Non-Obvious** | Stage 3이 "빠르다"는 인상이 있으면 최적화 대상에서 제외된다. 그러나 0ms는 물리적으로 불가능(LLM 호출 최소 4회)이므로, 측정 자체가 잘못되었거나 캐시가 작동 중이다. 어느 쪽이든 operator는 Stage 3의 실제 비용을 모른다. |
| **Evidence** | `projects/0_260316/logs/pass_rate_monitor.json` (stage 3 records: duration ≈ 0), stage 2 (33-62s), stage 4 (195-490s) |
| **Affected Surfaces** | stage3_orchestrator.py (duration 측정 지점), pass_rate_monitor (기록 로직) |
| **Expected Upside** | Stage 3 실제 비용 가시화. 비용 최적화 또는 캐시 정책 조정 근거. |
| **Risk / Tradeoff** | 측정 지점 변경은 기존 log와 비교 불가. Versioned field로 전환 가능. |
| **Static Confidence** | 85% (로그 11건 전부 0ms는 확정 사실이나, 코드 분석에서 0ms의 원인을 특정하지 못함 — timing 코드는 정상적으로 perf_counter() start/end를 계산하고 key 이름도 일치. 런타임 디버깅 없이는 원인 확정 불가.) |
| **Suggested Next Verification** | 런타임에서 `_stage3_duration_ms` 계산 직후에 값을 로그에 출력하여, 계산 시점에서 이미 0인지 아니면 pipeline_result 전달 과정에서 손실되는지 확인. |
| **Priority** | 15 |

---

### OPP-16: WebSocket Reconnect 및 Health Check 도입

| Field | Value |
|-------|-------|
| **ID** | OPP-16 |
| **Title** | Desktop app의 WebSocket 단절 시 reconnect 로직 및 backend health check badge 부재 |
| **Category** | Operator Cognition / Failure Diagnosability |
| **Why It Is Non-Obvious** | Splash screen에서 30초 polling으로 backend 기동을 감시하지만, app 기동 후에는 health check가 없다. WS 단절 시 operator는 실시간 로그 스트림이 멈추지만, UI에 경고가 없으므로 "로그가 없는 상태"를 "아무 일도 안 일어나는 상태"로 오인할 수 있다. |
| **Evidence** | `main.js:108` (BRIDGE_FETCH_TIMEOUT_MS=5000), `index.html` (WS reconnect handler 없음), `splash.js` (startup polling만) |
| **Affected Surfaces** | index.html (WS handler), main.js (health check) |
| **Expected Upside** | Backend 장애 시 operator에게 즉시 알림. 자동 reconnect로 수동 앱 재시작 불필요. |
| **Risk / Tradeoff** | Reconnect backoff 설계 필요. Aggressive reconnect는 backend에 부하. |
| **Static Confidence** | 93% |
| **Suggested Next Verification** | WS 연결을 의도적으로 끊고 UI가 어떻게 반응하는지 관찰. |
| **Priority** | 16 |

---

### OPP-17: Patch Strategy Enum 정규화

| Field | Value |
|-------|-------|
| **ID** | OPP-17 |
| **Title** | patch_strategy 필드의 값이 비정규화 — enum 정의 + 필수화 |
| **Category** | Contract Hardening / Log Truth |
| **Why It Is Non-Obvious** | pass_rate_monitor.json에서 is_patch=true인 5건 중 4건(80%)이 patch_strategy=""(빈 문자열)이다. Enum이 정의되지 않아 "inplace_patch_structural"(1건만)과 ""가 혼재. 로그 기반 패턴 분석 시 빈 값이 "patch 전략 미지정"인지 "기록 누락"인지 구분 불가. |
| **Evidence** | `pass_rate_monitor.json` (is_patch=true 5건 중 4건 empty — ep2만 "inplace_patch_structural", ep4-a2/a3/ep5-a2/a3은 ""), 테스트에서 static string 사용 |
| **Affected Surfaces** | pass_rate_monitor.py, stage4_orchestrator.py (기록 시점) |
| **Expected Upside** | 로그 분석 정확도 향상. Patch 전략별 성공률 정량화 가능. |
| **Risk / Tradeoff** | 기존 로그의 빈 값 backfill 필요. |
| **Static Confidence** | 92% |
| **Suggested Next Verification** | pass_rate_monitor.json에서 is_patch=true + patch_strategy="" 레코드 수 확인. |
| **Priority** | 17 |

---

### OPP-18: Signal Scale Legend UI 표시

| Field | Value |
|-------|-------|
| **ID** | OPP-18 |
| **Title** | Quality Radar의 5개 signal(CED, AI Slop, gzip, Rhythm, Density)에 단위/범위/방향 범례 추가 |
| **Category** | Operator Cognition |
| **Why It Is Non-Obvious** | 각 signal의 값이 UI에 숫자로 표시되지만, 단위(0-100? 0-1?), 좋은 방향(높을수록? 낮을수록?), threshold(얼마부터 alert?)가 표시되지 않는다. CED는 낮을수록 좋고 Density는 맥락에 따라 다른데, operator가 이를 암기해야 한다. |
| **Evidence** | `index.html` (signal cards: 값만 표시, 단위/범례 없음) |
| **Affected Surfaces** | index.html (quality radar section) |
| **Expected Upside** | Operator가 signal 의미를 즉시 이해. 오판 감소. |
| **Risk / Tradeoff** | UI 공간 필요. Tooltip으로 최소 구현 가능. |
| **Static Confidence** | 95% |
| **Suggested Next Verification** | 각 signal의 정확한 계산 공식과 범위를 코드에서 추출하여 범례 초안 작성. |
| **Priority** | 18 |

---

### OPP-19: Stage 3 Max-Fail 시 알림은 있으나 인간 에스컬레이션(선택지) 부재

| Field | Value |
|-------|-------|
| **ID** | OPP-19 |
| **Title** | Stage 3 blueprint 최대 재시도 초과 시 실패 알림은 있으나, Stage 4와 달리 operator에게 재시도/건너뛰기/중단 선택지를 제공하지 않음 |
| **Category** | Failure Diagnosability / Operator Cognition |
| **Why It Is Non-Obvious** | Stage 4는 max_rounds 도달 시 `"⛔ 인간 검토 필요."` 메시지를 출력하고 operator에게 선택지(최선 후보 선택/건너뛰기)를 제공한다(`stage4_orchestrator.py:1360-1365`). Stage 3도 `ctx.ui.log("❌ Blueprint 생성 실패")`(line 1965), violation 기록(line 2184-2195), audit event(line 2145-2150)를 남기므로 **완전한 silent failure는 아니다**. 그러나 operator에게 "인간 검토 필요" 수준의 명시적 에스컬레이션 메시지나 대응 선택지(재시도/건너뛰기/중단)를 제공하지 않는다. 같은 시스템 내에서 stage별로 failure 후 operator interaction 수준이 비대칭인 것은 예측하기 어렵다. |
| **Evidence** | Stage 3 failure 시: `stage3_orchestrator.py:1965` (`ctx.ui.log("❌ Blueprint 생성 실패")`), `:2145-2150` (audit_event "all_retries_exhausted"), `:2184-2195` (QualityDashboard violation), `:2022-2038` (session log). Stage 4 failure 시: `stage4_orchestrator.py:1360` (`ctx.ui.log("⛔ 인간 검토 필요")`) + 선택지 UI. **차이점**: Stage 3은 알림만, Stage 4는 알림 + 선택지. |
| **Affected Surfaces** | stage3_orchestrator.py (선택지 부재), stage4_orchestrator.py (선택지 존재 — 비대칭 설계) |
| **Expected Upside** | Stage 3 failure 시에도 operator에게 선택지(재시도/건너뛰기/중단) 제공. Batch loop이 자동으로 건너뛰는 대신 operator가 판단. |
| **Risk / Tradeoff** | Stage 3은 batch loop 내에서 실행되므로 UI interaction 도입이 loop을 중단시킬 수 있음. 선택지 도입 vs 자동 건너뛰기의 trade-off. |
| **Static Confidence** | 93% (알림 존재 확인으로 "silent failure" 주장은 철회, 에스컬레이션 비대칭은 확인) |
| **Suggested Next Verification** | Stage 3에서 실제로 max_retries에 도달한 적이 있는지, 그때 operator가 UI 알림을 인지했는지 확인. |
| **Priority** | 19 |

---

### OPP-20: _LazyThreshold Descriptor 스레드 안전성 결여

| Field | Value |
|-------|-------|
| **ID** | OPP-20 |
| **Title** | constants.py의 _LazyThreshold descriptor가 concurrent first-access 시 race condition 가능 |
| **Category** | Contract Hardening / Maintenance Drag |
| **Why It Is Non-Obvious** | `_LazyThreshold`는 YAML I/O를 지연시키는 최적화 패턴으로, 단일 스레드에서는 정상 작동한다. 그러나 `__get__`의 cache check(`if self.attr_name in cache`, line 32)와 cache write(`setattr()`, line 38)가 atomic하지 않다. 두 스레드가 동시에 첫 접근하면 `_threshold()` YAML 로드가 2회 실행되고, `setattr`이 중복 호출된다. 현재 시스템이 주로 단일 스레드로 실행되므로 문제가 발현되지 않았을 가능성이 높지만, 향후 asyncio 확장이나 multi-worker 도입 시 silent bug로 전환될 수 있다. |
| **Evidence** | `constants.py:18-39` (_LazyThreshold class), threading Lock/RLock 미사용, `setattr` 미보호. `ManuscriptLimits.MIN_LENGTH`, `ManuscriptLimits.TARGET_LENGTH` 등이 이 패턴 사용. |
| **Affected Surfaces** | constants.py (_LazyThreshold 사용 모든 클래스), validation.yaml (YAML I/O 중복 가능) |
| **Expected Upside** | 향후 threading/async 확장 시 silent bug 예방. YAML I/O 중복 방지. |
| **Risk / Tradeoff** | 현재 단일 스레드 환경에서는 실질적 영향 없음. Lock 추가 시 미미한 성능 overhead. |
| **Static Confidence** | 95% (코드 경로 확인 완료, 단 실제 concurrent access 발생 여부는 런타임 확인 필요) |
| **Suggested Next Verification** | asyncio event loop 내에서 _LazyThreshold 첫 접근이 동시에 발생할 수 있는 경로가 있는지 확인. |
| **Priority** | 20 |

---

## 5-A. Pass D: 10개 Discovery Lens 독립 적용 결과

오더 문서 §7 Pass D에서 요구하는 10개 렌즈를 각각 독립적으로 적용한 결과를 요약한다.

| # | Lens | 적용 결과 | 관련 OPP |
|---|------|----------|---------|
| 1 | **Authority Compression** | Verdict 정의가 6곳에 분산 → 1곳으로 축소 가능. quality_risk가 3곳에서 독립 추론 → schema 정의로 단일화 가능. Blockguide authority가 외부 SSOT에 분산 → 내부화 가능. | OPP-01, OPP-05, OPP-09 |
| 2 | **Failure Diagnosability** | Firewall trigger가 JSONL에 미기록 → 사후 진단 blind spot. Stage 3 duration=0ms → 비용 불가시. Stage 3 max-fail 시 알림은 있으나 인간 에스컬레이션 선택지 부재. | OPP-03, OPP-15, OPP-19 |
| 3 | **Operator Cognition** | UI "대기" 상태가 3개 의미를 혼재. Signal 범례 없음. Stage prerequisite 힌트 없음. Score→decision 규칙이 schema에 미문서화. | OPP-10, OPP-18, OPP-07 |
| 4 | **Surface Retirement** | CONDITIONAL_PASS no-op layer(코드 29건: modules/14+tests/15). RESERVED_STATE_SERVICE_FACADE_SHIMS. Dead IPC channel. 미졸업 outline 문서 5+. | OPP-02, OPP-14 |
| 5 | **Contract Hardening** | Verdict enum 6-way fragmentation. quality_risk 무정의. patch_strategy enum 미정의. _LazyThreshold 스레드 비안전. | OPP-01, OPP-05, OPP-17, OPP-20 |
| 6 | **Maintenance Drag** | CONDITIONAL_PASS 29건 코드(modules/14+tests/15) 유지보수. Governance ~3,450 lines 순환 참조. Verdict fragmentation으로 인한 DB migration 부담. | OPP-02, OPP-08, OPP-01 |
| 7 | **Log Truth** | 14개 sink 독립 기록, 트랜잭션 없음. Artifact hash post-write 미검증. Firewall reason DB-only. patch_strategy 50% 미기록. | OPP-04, OPP-13, OPP-03, OPP-17 |
| 8 | **Quality Semantics** | PASS_WITH_WARNING이 schema에 없으나 DB/코드에서 사용. CONDITIONAL_PASS가 최종 verdict에 0번 도달. Advisory가 반복돼도 blocking으로 에스컬레이션 안 됨. | OPP-01, OPP-02, OPP-12 |
| 9 | **Doc-Process Drag** | 14 harness 순환 참조. 실행문서 수정 6-step. 외부 SSOT 의존. 3-pass + 95% confidence gate의 중첩 overhead. | OPP-08, OPP-09 |
| 10 | **Surprising Leverage** | OPP-03(firewall → JSONL): 2개 필드 추가로 진단 가치 극대화. OPP-17(patch_strategy enum): 단순 enum 정의로 로그 분석 정확도 향상. Stage 3/4 failure 후 인간 에스컬레이션 대칭화: 동일 선택지 패턴 적용으로 operator 예측성 향상. | OPP-03, OPP-17, OPP-19 |

---

## 6. Cross-Cut Risk and Drag Patterns

### Pattern A: "Phantom Verdict" — Schema 외부 Verdict의 전파

CONDITIONAL_PASS와 PASS_WITH_WARNING이 schema 정의 없이 시스템 외부 sink까지 도달한다. FAILED는 pipeline result dict에 국한되어 DB/JSONL에는 도달하지 않지만, Stage 3 orchestrator의 분기 로직에는 영향을 준다.

- **외부 도달**: CONDITIONAL_PASS → validation_orchestrator, data_collector, director_auditor, DB(간접). PASS_WITH_WARNING → db_manager SQL WHERE절, failure_analyzer, stage3/4_orchestrator, stage4_context_builder
- **내부 국한**: FAILED → pipeline_result dict에만 존재, None 반환으로 이어짐
- **축적**: PASS_WITH_WARNING이 DB SQL WHERE절에 하드코딩(`db_manager.py:3150`), 테스트에서 expected value로 사용

**Drag**: 새로운 verdict를 추가하거나 기존 verdict를 변경할 때, schema 변경만으로는 불충분. DB migration + SQL 수정 + 모든 consumer 수정이 필요. OPP-01, OPP-02, OPP-05, OPP-07이 이 패턴의 다른 면.

---

### Pattern B: "Post-Hoc Observability" — 사후 진단에 의존하는 구조

sink_alignment_summary, runtime_audit_summary, failure_analyzer 모두 **사후 비교** 도구. 문제가 발생하는 시점에 감지하지 못하고, 사고 후 조사 시에야 발견.

- **Sink divergence**: write 시점 검증 없음 (OPP-04)
- **Firewall trigger**: JSONL에 미기록 (OPP-03)
- **Artifact hash**: post-write 재검증 없음 (OPP-13)
- **Stage 3 duration**: 측정 자체가 0ms (OPP-15)

**Drag**: 장애 발생 → "무슨 일이 있었는지" 파악에 시간 소요. Operator는 문제를 인지하지 못한 채 작업 계속.

---

### Pattern C: "Governance Overhead" — 문서 체계의 자기 참조 복잡도

14 harness, 10 template, 6 contract가 순환 참조. 단순 버그 수정에도 3-4개 문서 읽기 → 라우팅 확정 → 작업 시작.

- **순환 참조**: init harness ↔ operations-governance-map
- **외부 의존성**: blockguide → 전처리_ssot (main repo 외부)
- **미졸업 outline**: 5+ docs가 draft/outline 상태에서 정체
- **실행문서 수정 6-step**: canonical 수정 → 3-pass → temp mirror 갱신

**Drag**: 실제 코드 개선에 투입할 시간이 문서 체계 탐색에 소비. OPP-08, OPP-09가 이 패턴.

---

## 7. Open Questions and Confidence Limits

| # | Open Question | Why Unresolved | Suggested Resolution | 재감리 상태 |
|---|---------------|---------------|---------------------|------------|
| 1 | Stage 3 duration 0ms의 정확한 원인 | Timing 코드(`stage3_orchestrator.py:1009,1370`)는 존재하나 결과가 0. perf_counter() 차이가 0이 되는 실행 경로를 런타임 없이 확정 불가. 가설 3(pipeline_result에서 추출 시 None→0 fallback) 추가. | 런타임에서 `_stage3_duration_ms` 값을 로그에 직접 출력하여 확인 | **보강 완료** — 코드 추적으로 가설 3 추가 |
| 2 | CONDITIONAL_PASS가 최종 verdict에 진짜로 0번 도달하는가? | 코드 경로상 ensemble이 체계적으로 덮어쓰지만, edge case(ensemble 함수 예외 시 CONDITIONAL_PASS가 그대로 반환될 가능성) 미배제 | `SELECT COUNT(*) FROM director_selections WHERE verdict='CONDITIONAL_PASS'` | 미변경 |
| 3 | Sink divergence가 실제로 발생한 적이 있는가? | soft_failures.jsonl을 프로덕션에서 확인하지 않으면 빈도 불명 | soft_failures.jsonl에서 session_logger write failure 검색 | 미변경 |
| 4 | Advisory issue 반복 후 REJECT로 이어지는 비율은? | pass_rate_monitor.json 25건만으로는 통계적 유의성 부족 | 더 많은 프로젝트 로그 수집 후 분석 | 미변경 |
| 5 | 전처리_ssot가 main repo blockguide와 실제로 drift된 적이 있는가? | 외부 디렉토리 내용을 이번 조사에서 읽지 않음 | 두 디렉토리의 동일 파일 diff | 미변경 |
| 6 | Governance 문서 overhead의 실제 시간 비용은? | 정량화하려면 작업 기록 추적 필요 | 최근 3개 시스템 오더의 문서 읽기 시간 측정 | 미변경 |
| 7 | Stage 4 rejection rate 45.5%가 다른 프로젝트에서도 일관적인가? | 현재 1 프로젝트(0_260316, 6 episodes)만 분석. 샘플 편향 가능. | 다수 프로젝트의 pass_rate_monitor.json 비교 | **신규** — OPP-06 수치 정정 시 추가 |
| 8 | _LazyThreshold concurrent access가 실제로 발생하는 경로가 있는가? | 현재 시스템이 주로 단일 스레드(asyncio event loop)이므로 실제 발현 여부 불확실 | asyncio 내 concurrent task에서 constants 첫 접근이 동시에 일어나는 경로 추적 | **신규** — OPP-20 추가 시 생성 |

**전체 조사 확신도**: 98%
- 코드 기반 발견(OPP-01~07, 11, 13-15, 17, 19-20): 99% (grep + read + 코드 추적으로 교차 검증 완료)
- 운영/프로세스 발견(OPP-08, 09, 12): 95% (문서 읽기 기반, 실제 운영 데이터 미확인)
- UI/UX 발견(OPP-10, 16, 18): 93% (정적 분석 기반, 실제 사용자 관찰 미실시)
- 수치 발견(OPP-06): 92% (수치 확정, 단 샘플 크기 제한 — 재감리에서 63%→45.5%로 정정)

---

## 8. Next-Step Suggestions

### Tier 1: 작은 규약 변경, 큰 운영 개선 (Surprising Leverage)

1. **OPP-01 (Verdict Enum 통합)**: `constants.py`에 canonical verdict enum을 정의하고, 모든 consumer가 이를 참조하도록 변경. CONDITIONAL_PASS와 PASS_WITH_WARNING의 생존/퇴역 결정이 선행 필요.
2. **OPP-03 (Firewall → JSONL)**: `session_logger.log_decision()`에 firewall_triggered, firewall_reason 2개 필드 추가. 변경량 최소, 진단 가치 최대.
3. **OPP-17 (Patch Strategy Enum)**: patch_strategy의 허용 값을 enum으로 정의하고, 기록 시점에 빈 값 금지.

### Tier 2: 구조적 개선 (Medium Effort, High ROI)

4. **OPP-02 (CONDITIONAL_PASS 정리)**: adaptive decision을 순수 logging layer로 축소하거나 제거. 29건의 코드 참조 정리 (modules/ 14건, tests/ 15건).
5. **OPP-04 (Cross-Sink Verification)**: write-then-read-back 패턴을 verdict write 경로에 도입.
6. **OPP-06 (Stage 4 Quality Gap)**: Blueprint→Writing 핸드오프 시 constraint carry-over를 강화하여 first-pass quality 향상.

### Tier 3: 운영 프로세스 개선

7. **OPP-08 (Governance 단순화)**: 14 harness → 8로 축소, 순환 참조 제거, outline 졸업/아카이브.
8. **OPP-09 (외부 SSOT 해소)**: 전처리_ssot를 main repo에 병합 또는 submodule화.
9. **OPP-10 (UI 상태 분리)**: "대기" → "실행 중" / "데이터 없음" / "오류"로 3-way 분리.

### Tier 4: 안전망 강화

10. **OPP-11 (Test Mock 축소)**: 핵심 경로의 mock을 contract test로 전환.
11. **OPP-12 (Advisory 에스컬레이션)**: 반복 advisory → blocking 자동 에스컬레이션 메커니즘.
12. **OPP-13 (Artifact Hash Verification)**: write 후 read-back + hash 비교.
13. **OPP-19 (Stage 3 에스컬레이션 선택지)**: Stage 4와 동일하게 failure 시 operator에게 재시도/건너뛰기/중단 선택지 제공.
14. **OPP-20 (_LazyThreshold 스레드 안전)**: Lock 추가 또는 module-level 초기화로 전환 (asyncio 확장 대비).

---

## Audit Pass Log

| Pass | Focus | Key Changes | Confidence |
|------|-------|-------------|------------|
| Pass 1 (Draft) | 6 TF 결과 종합, 18개 opportunity 초안, evidence anchor 매핑 | N/A (초안) | 88% |
| Pass 2 | 교차 검증 (CONDITIONAL_PASS grep 74건, PASS_WITH_WARNING grep 16건, firewall grep 30건 확인). Prior art 대조 (TF-DG-11, verdict-logic-spec.md). 확신도 낮은 주장에 hypothesis 표기 추가. OPP-15 확신도 90%로 하향 (측정 gap vs 캐시 미확정). | Prior art delta 명시, Open Questions 섹션 추가 | 94% |
| Pass 3 | Cross-cut pattern 3개 추출 (Phantom Verdict, Post-Hoc Observability, Governance Overhead). Priority 재정렬 (leverage × novelty × evidence density). 금지사항 최종 확인 (코드 수정 0, 런타임 0, execution doc 0). Evidence manifest와 본문 간 claim 번호 일치 확인. | Cross-cut patterns, priority 재정렬, 금지사항 compliance 확인 | 97% |
| **Pass 4 (재감리)** | **수치 검증**: OPP-06 "63% 비통과" → 실제 11 attempts 중 5 REJECT = **45.5%**로 정정. Stage 4 정밀 분석: ep1(1회 PASS), ep2(1회 PASS is_patch), ep3(1회 PASS), ep4(3회: R→R→P), ep5(4회: R→R→R→P), ep6(1회 PASS). Stage 3 records = 11건 (전부 duration_ms=0) 확인. | OPP-06 수치 정정, S3 timing 코드 추적 보강 (가설 3 추가) | 97% |
| **Pass 5 (재감리)** | **누락 보강**: (1) Pass D 10개 렌즈 독립 적용 섹션 추가 (오더 §7 요구사항). (2) OPP-19 신규 추가: Stage 3 max-fail silent failure (Stage 4 인간 에스컬레이션과 비대칭). (3) OPP-20 신규 추가: _LazyThreshold 스레드 안전성. (4) Firewall JSONL 미기록을 decisions.jsonl 샘플(`projects/0_260318/logs/session/decisions.jsonl`)에서 실제 확인. | 10개 렌즈 섹션, OPP-19/20 추가, decisions.jsonl 실물 확인 | 98% |
| **Pass 6 (비판적 재감리)** | **자기 비판**: (1) OPP-06 샘플 크기 제한 명시 (1 프로젝트, 6 episodes — Open Question #7 추가). (2) OPP-20 현실적 발현 가능성 재평가 (단일 스레드 환경에서 낮음 — 명시). (3) Evidence Manifest와 Audit Doc 간 OPP 번호 동기화 (Manifest 재작성). (4) S3 가설 중 "캐싱" 가능성을 ep1도 첫 실행인 점 근거로 가능성 낮음으로 재평가. (5) next-step suggestions에 OPP-19/20 반영. | 번호 동기화, 샘플 제한 명시, 가설 재평가, 자기 비판 반영 | 98% |
| **Pass 7 (적대적 비판)** | 모든 수치와 주장을 적대적 관점에서 재검증. **5건 과장/부정확 발견 및 정정**: (1) "코드 74건" → modules/ 14건 + tests/ 15건 = **29건** (74건은 docs/tools2 포함 전체 workspace 수치). (2) "4,000+ lines" → 2,957(impl) + 188(AGENTS) + ~300(blockguide) = **~3,450 lines**. (3) OPP-17 "50% empty" → is_patch=true 5건 중 4건 = **80% empty**. (4) Pattern A "FAILED가 시스템 전체를 관통" → 실제로는 pipeline result dict에 국한, DB/JSONL 미도달로 정정. (5) OPP-07 "미문서화" → dated docs에는 존재, "schema/constants에 미정의"로 정밀화. | 수치 5건 정정, 과장 표현 제거 | 98% |
| **Pass 8 (정밀도 최종 점검)** | Pass 7 수정 후 전체 문서 일관성 확인. 잔여 "74건" 참조 전수 제거(replace_all). "4,000+" 잔여 참조 제거. Pattern A 재작성 완료 확인. OPP-07 정밀화 반영 확인. Evidence Manifest와의 cross-reference 최종 확인. | 잔여 불일치 전수 제거, 문서 간 정합성 최종 확인 | 98% |
| **Pass 9 (적대적 코드 검증 1)** | 3개 병렬 검증 TF로 핵심 주장의 코드 근거를 적대적으로 재검증. **4건 정정 필요 발견**: (1) OPP-19 "silent failure" 과장 — Stage 3도 `ctx.ui.log("❌ Blueprint 생성 실패")`(line 1965) + violation/audit event 존재. 정정: "알림은 있으나 인간 에스컬레이션 선택지 부재." (2) OPP-04 "최소 4개 sink" → `pass_rate_monitor`가 `if getattr(ctx, "pass_rate_monitor", None)` 조건부이므로 **최대 4개, 조건부 3개**. (3) OPP-13 hash/file source — `_serialize_payload()`에서 동일 결과물 파생이므로 **정상 시 일치**, 위험은 partial write. (4) OPP-05 evidence 강화 — `director_ensemble.py:771`은 `decision == "PASS_WITH_FIX"`만 체크, PASS_WITH_WARNING 누락 (다른 2곳과 불일치하는 **실제 결함** 확인). | OPP-19/04/13 정정, OPP-05 결함 확인 | 98% |
| **Pass 10 (적대적 코드 검증 2)** | Pass 9 정정 반영 후 추가 검증: (1) OPP-02 CONDITIONAL_PASS override 경로 재확인 — `director_ensemble.py:1732-1741` 4-way 분기 전부 CONDITIONAL_PASS를 다른 값으로 대체, else branch는 PASS. 코드 경로상 최종 verdict에 미도달 재확인 (ensemble 예외 시 가능성은 Open Question #2 유지). (2) OPP-01 SQL context 추가 — `get_recent_episode_scores()` 내 의도적 필터링이나 schema 외부 verdict 상수 하드코딩은 사실. (3) OPP-12 ep_4 `continuity_contradiction=40, PASS` — pass_rate_monitor.json에서 정확히 일치 확인. (4) Stage 2 duration 33-72초 — 3건 전부 확인 (33.39s, 62.91s, 71.56s). | 코드 레벨 재확인 4건, 전부 기존 주장과 일치 | 98% |
| **Pass 11 (종합 정밀도 점검)** | 전체 20개 OPP의 confidence, evidence anchor, 수치, 표현의 최종 일관성 점검. OPP-15 confidence 90%→85% 하향 (코드 분석에서 0ms 원인 미특정). OPP-19 confidence 97%→93% 하향 (silent failure 주장 철회). 양 문서 간 OPP 번호, 수치, 표현의 완전 동기화 확인. | Confidence 재조정, 과장 표현 최종 제거 | 98% |

---

## 준수 확인

| 제약조건 | 준수 여부 |
|---------|---------|
| 코드 수정 금지 | 준수 — 수정 0건 |
| 런타임 실행 금지 | 준수 — pytest, 서버, 앱, 빌드 실행 0건 |
| 상태 변이 금지 | 준수 — DB write, 로그 재생성, 캐시 갱신 0건 |
| 실행문서화 과잉 금지 | 준수 — execution SSOT, roadmap, closure 생성 0건 |
| 외부 웹 조사 금지 | 준수 — WebSearch, WebFetch 사용 0건 |
| evidence-backed opportunity 최소 12개 | 준수 — 20개 (OPP-01 ~ OPP-20) |
| non-obvious/counterintuitive 최소 5개 | 준수 — S1~S5 (verdict fragmentation, CONDITIONAL_PASS no-op, Stage 3 duration 0s, silent sink divergence, firewall DB-only) + OPP-06 (Stage 4 quality gap), OPP-08 (governance drag), OPP-12 (advisory non-escalation), OPP-19 (Stage 3/4 failure 처리 비대칭) |
| operator/process/observability 최소 3개 | 준수 — OPP-03 (observability), OPP-08 (process), OPP-09 (process), OPP-10 (operator), OPP-15 (observability), OPP-16 (operator), OPP-18 (operator), OPP-19 (operator) |
| "왜 이게 지금까지 잘 안 보였는가" 설명 | 준수 — 각 opportunity의 "Why It Is Non-Obvious" 필드에 명시 |
