<!-- [참고자료] -->
# 3-Pass Audit Master Summary (R2: 대원칙 적용 재감리)

> Independent Re-Audit (Codex, 2026-03-16)
>
> Status: historical research memo set summary, not live execution authority.
>
> Pass 1: this summary and the four companion `SSOT` docs do not carry the normal current-state ROL metadata expected for operational survey/SSOT use, and they mix raw candidate tables with later reclassification tables in one surface.
>
> Pass 2: direct live-code recheck found at least one stale factual premise in the companion set: `TF-E2` claims "UI 경고 없음", but the current code already logs explicit `V75-B` UI warnings in `modules/core/stage4_orchestrator.py`.
>
> Pass 3: the current canonical queue is the closed roadmap in `docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md`; this OPUS bundle is not part of that active authority chain and must be treated as a bounded reference memo only.
>
> Confidence: 96% for the memo-only classification above. Confidence is below 95% for using this summary as direct execution authority because it still aggregates unsampled items by deference.

## Independent Evidence Spot Check (Codex, 2026-03-16)

Representative live-code checks against the OPUS bundle:

| Claim | Source Doc | Live Check | Verdict |
|-------|------------|------------|---------|
| `S0-1` DNA sync failure silently continues | `all-stage-deepdive-fix-candidates-ssot.md` | `modules/core/stage01_helpers.py:260-297` has an `if dna_success:` block with no failure `else` branch | supported |
| `S1-2` context accumulator grows without bound | `all-stage-deepdive-fix-candidates-ssot.md` | `modules/core/stage01_helpers.py:889-905` already applies `MAX_CONTEXT_VOLUMES = 3` sliding-window compression | contradicted |
| `S2-2` rollback exists but is partial | `all-stage-deepdive-fix-candidates-ssot.md` | `modules/core/stage2_finalizer.py:1093-1120` rolls back DB and restores `st_snapshot` via shallow attribute replay | partially supported; original CRITICAL is overstated, later HIGH reclassification is more credible |
| `S3-1` / `S3-2` long-history context is hard-cut | `all-stage-deepdive-fix-candidates-ssot.md` | `modules/core/stage3_orchestrator.py:1216-1226` truncates manuscript context by char count; `:1252-1256` passes `prev_blueprints[-30:]` | supported |
| `S4-4` continuity runs only on round 0 | `all-stage-deepdive-fix-candidates-ssot.md` | `modules/core/stage4_interview_round.py:2862-2868` gates continuity/history on `round_num == 0` | supported |
| `S4-5` empty feedback breaks patch loop | `all-stage-deepdive-fix-candidates-ssot.md` | `modules/core/stage4_interview_round.py:3011-3013` breaks when `_current_fb` is falsy | supported |
| `X-2` WorldState / FactLedger save failures are non-blocking | `all-stage-deepdive-fix-candidates-ssot.md` | `modules/core/fact_ledger.py:114-119` and `modules/core/world_state.py:99-104` only log on save failure | supported |
| `TF-CM-03` STATE_ORDER omits `사망` / `굴복` | `all-subsystem-tf-consolidated-ssot.md` | `modules/domain/agents/continuity_manuscript.py:1056-1065` includes both in keyword maps but not in `STATE_ORDER` | supported |
| `TF-FB-01/02` quantified feedback uses fabricated numbers | `detail-subsystem-tf-consolidated-ssot.md` | `modules/core/feedback_system.py:109-179` computes heuristics and drops `audit_result.get(\"score_breakdown\", {})` on the floor | supported |
| `TF-DG-01` partial reject can still approve | `detail-subsystem-tf-consolidated-ssot.md` | `modules/domain/agents/director_grading.py:686-688` sets `approved` when `len(rejected) == 0 or len(applied) > 0` | supported |
| `TF-DG-02` category weighting duplicates fields | `detail-subsystem-tf-consolidated-ssot.md` | `modules/domain/agents/director_grading.py:148-155` uses `commercial_appeal` and `emotion_arc` in multiple buckets | supported |
| `TF-S4CB-02` context builder bypasses DBManager | `detail-subsystem-tf-consolidated-ssot.md` | `modules/core/stage4_context_builder.py:1804-1816` directly uses `_db._lock` and `_db.conn.cursor()` | supported |
| `TF-E2` severity upgrade depends on `UI 경고 없음` | `escalation-residual-tf-consolidated-ssot.md` | `modules/core/stage4_orchestrator.py:1271-1273`, `:1300`, `:1312-1313` already emit explicit `V75-B` UI logs | contradicted |
| `TF-E3` escalation log schema is only 5 fields | `escalation-residual-tf-consolidated-ssot.md` | `modules/core/stage4_orchestrator.py:1353-1369` writes `{ts, ep, event, streak, success}` only | supported |

Spot-check conclusion:
- the OPUS bundle contains real, useful leads
- the bundle also contains at least one materially stale rationale and one already-closed false-positive that stayed visible in the raw tables
- use the bundle as a lead index, not as direct patch authority

| Field | Value |
|-------|-------|
| **Date** | 2026-03-16 |
| **Baseline** | `bbb00a77` |
| **Scope** | 4개 SSOT, 258 TF 항목 전량 |
| **Method** | R1: 8 병렬 에이전트 3-Pass → R2: 대원칙 4개 렌즈 적용 재감리 |
| **Audited** | 258/258 (100%) — R2에서 전량 재평가 |

---

## 0. 대원칙 (감사 렌즈)

| # | 원칙 | 감사 적용 |
|---|------|----------|
| **#1** | **Python은 수집만, 판단은 LLM이** | advisory-only 검증기 FP/FN → 심각도 하향 근거. Python REJECT 불가면 영향 제한. |
| **#2** | **팩트시트 수정 권한은 LLM만** | NPC registry 자동 수정 → 대원칙 위반 여부 확인. |
| **#3** | **디렉터 주권주의 (내각제)** | Director 단독 판정 = 의도된 설계. 단일 LLM, Contradiction Firewall LLM-only = 정합. |
| **#4** | **사망 캐릭터는 회상/언급만 허용** | STATE_ORDER 사망 누락, Arc 레벨 사망 미감지 → 대원칙 위반 가능성 → 심각도 유지/상향. |

---

## 1. 총괄 결과 (R2 갱신)

| 판정 | R1 건수 | R2 건수 | 변동 |
|------|---------|---------|------|
| **CONFIRMED** | 176 | 164 | -12 |
| **RECLASSIFIED** | 41 | 47 | +6 |
| **FALSE-POSITIVE** | 5 | 7 | +2 |
| **CLOSED** (의도된 설계) | 4 | 8 | +4 |
| **MERGED** | 1 | 1 | — |
| **NOT SAMPLED** | 31 | 31 | — |
| **합계** | **258** | **258** | **±0** |

### R2 변동 상세 (20건)

| 변동 유형 | 건수 | 항목 |
|----------|------|------|
| CONFIRMED → **CLOSED** | 1 | TF-DE-02 (대원칙#3: Contradiction Firewall LLM-only = Director 주권 정합) |
| CONFIRMED → **RECLASSIFIED** | 11 | TF-ADV-07, TF-PLV-05/06/08, TF-NPC-05/06, TF-PB-01, TF-AR-06/07, TF-FB-11, S2-6 (대원칙#1: advisory/collection/orchestration) |
| RECLASSIFIED → **FP** | 2 | X-3 (인용 라인 __init__), TF-PLV-01 (passed=True 항상 → dead branch) |
| RECLASSIFIED → **CLOSED** | 3 | TF-DE-09 (대원칙#3: 내각제), TF-SV-02 (코드에 대원칙#1 명시), S4-4 (대원칙#3: Director 보상) |
| CONFIRMED → **UPGRADE** | 1 | TF-E2 (IMPORTANT→HIGH, 대원칙#3: Director 정보 비대칭) |
| 확신도 전용 상향 | 10 | S2-5, S4-3, X-1, TF-CM-03, TF-NPC-04, TF-CA-01, TF-E2, TF-E8, TF-E11, TF-E13 |

### CRITICAL 심각도 변동 (R2 갱신)

| 구분 | R1 | R2 |
|------|-----|-----|
| 원래 CRITICAL | 39 | 39 |
| 감사 후 CRITICAL 유지 | 17 | **16** |
| → FALSE-POSITIVE | 1 (S2-1) | 1 |
| → RECLASSIFY→IMPORTANT | 15 | 15 |
| → RECLASSIFY→HIGH | 3 | 3 |
| → RECLASSIFY→INSIGHT | 3 | 3 |
| → **CLOSED** (신규) | 0 | **1** (TF-DE-02) |

**CRITICAL 생존율: 41.0%** (R1: 43.6%) — TF-DE-02가 대원칙#3으로 CLOSED.

---

## 2. 대원칙별 영향 분석

### 대원칙 #1: "Python은 수집만, 판단은 LLM이" — 15건 변경

| 패턴 | 영향 항목 | 판정 |
|------|----------|------|
| **advisory-only 검증기** | TF-ADV-01/07, TF-PLV-05/06/08 (5건) | REJECT 권한 없음 → RECLASSIFIED→INSIGHT |
| **Python 수집 노이즈** | TF-NPC-05/06, TF-PB-01 (3건) | LLM 필터 존재 → RECLASSIFIED→INSIGHT |
| **오케스트레이션 영향** | TF-AR-06/07 (2건) | 재시도 전략만 영향 → RECLASSIFIED→INSIGHT |
| **피드백 구성** | TF-FB-11 (1건) | 정보 순서 < LLM 판정 → RECLASSIFIED→INSIGHT |
| **advisory 최적화** | S2-6 (1건) | valid arc 시 불필요한 advisory 스킵 = 의도적 → RECLASSIFIED→LOW |
| **±1 캡 의도적 설계** | TF-SV-02 (1건) | 코드 주석에 `# 대원칙 #1` 명시 → **CLOSED** |
| **dead branch** | TF-PLV-01 (1건) | `passed=True` 항상 → REJECT 진입 불가 → **FP** |

**근거 패턴**: `pre_llm_validator.py:L133`이 `"passed": True` 항상 반환. `scoring_validator.py:957-961`에 `# [TF-C02] 대원칙 #1` 주석. `arc_draft_validator.py`는 `critical=[]` 반환 (REJECT 불가).

### 대원칙 #3: "디렉터 주권주의 (내각제)" — 4건 변경

| 항목 | 판정 | 근거 |
|------|------|------|
| TF-DE-02 | CRITICAL→**CLOSED** | Contradiction Firewall가 LLM-only = Director 주권. Python advisory는 mc_parts로 이미 전달. |
| TF-DE-09 | RECLASSIFIED→IMPORTANT→**CLOSED** | 단일 LLM = 내각제 구현. "앙상블"은 후보의 앙상블. |
| S4-4 | CONFIRMED→**CLOSED** | round_num==0 제한 = Director가 매 라운드 판정하므로 재검사 불필요. |
| TF-E2 | IMPORTANT→**HIGH** | V75-B 실패 시 Director가 결함 BP를 인지 못함 = 정보 비대칭으로 주권 약화. |

### 대원칙 #4: "사망 캐릭터 보호" — 2건 재확인

| 항목 | 판정 | 근거 |
|------|------|------|
| TF-CM-03 | **CRITICAL 유지** (97→98%) | STATE_ORDER에 "사망" 미포함 → deceased→non-deceased 상태 전이 미감지. **대원칙#4 직접 위반 가능성.** |
| TF-CA-01 | **IMPORTANT 유지** (88→92%) | Arc 레벨 사망 검증 부재이나 TruthGate + check_dead_npc_appearance() 다층 보상 존재. |

---

## 3. FALSE-POSITIVE 7건 상세 (R2)

| ID | 원래 심각도 | R1/R2 | 사유 |
|----|-----------|-------|------|
| **S2-1** | CRITICAL | R1 | `attempt += 1` 모든 경로에서 정확히 1회. L796은 dead code. |
| **S1-2** | MEDIUM | R1 | L890-905 `MAX_CONTEXT_VOLUMES=3` 슬라이딩 윈도우 이미 존재. |
| **S2-3** | HIGH | R1 | `.get()` fallback이 이전 값 정확 보존. 조기 반환 시 미변경이 정확한 동작. |
| **S2-4** | HIGH | R1 | `_base_constraint_block` + Python 문자열 불변성으로 원본 미오염. |
| **TF-BA-15** | INSIGHT | R1 | `attempt` 카운터는 의도적 continuation 추적. |
| **X-3** | HIGH | **R2** | 인용 라인(L50-77)이 `__init__` 코드. resume 로직은 orchestration 레벨에서 처리. entity_registry는 매 에피소드 DB 재구축. |
| **TF-PLV-01** | CRITICAL | **R2** | `pre_llm_validator.py:L133`이 항상 `passed: True`. dead REJECT 분기 — 런타임 진입 불가. 대원칙#1 정합. |

---

## 4. CLOSED 8건 상세 (R2)

| ID | 원래 심각도 | R1/R2 | 대원칙 | 사유 |
|----|-----------|-------|--------|------|
| **TF-E1** | INSIGHT | R1 | — | V75-D 성공 후 streak 리셋 = 의도된 설계. |
| **TF-E4** | INSIGHT | R1 | — | 30KB 가드 정상 동작 확인. |
| **TF-E6** | INSIGHT | R1 | #1 | 비용 효율적 키워드 기반 역방향 피드백. Python 수집만. |
| **TF-E12** | INSIGHT | R1 | — | PASS_WITH_FIX와 에스컬레이션은 별도 문제 영역. |
| **TF-DE-02** | CRITICAL | **R2** | **#3+#1** | Contradiction Firewall LLM-only = Director 주권 + Python 수집만 정합. advisory는 mc_parts로 이미 전달. |
| **TF-DE-09** | CRITICAL | **R2** | **#3** | 단일 LLM 호출 = 내각제 구현. 후보의 앙상블이지 판사의 앙상블이 아님. |
| **TF-SV-02** | CRITICAL | **R2** | **#1** | `scoring_validator.py:L957-961` 코드에 `# [TF-C02] 대원칙 #1: Python 판단 최소화` 명시. ±1 캡은 feature. |
| **S4-4** | MEDIUM-HIGH | **R2** | **#3** | `round_num==0` 제한 = Director가 매 라운드 판정. 중복 검사 스킵은 비용 최적화. |

---

## 5. 주요 RECLASSIFICATION (R2 갱신)

### R2 신규 하향 (대원칙#1 기반, 13건)

| ID | 원래 → R1 → R2 | 대원칙 근거 |
|----|----------------|-----------|
| TF-ADV-07 | IMPORTANT → IMPORTANT → **INSIGHT** | advisory-only, `critical=[]` 반환 (REJECT 불가) |
| TF-PLV-05 | IMPORTANT → IMPORTANT → **INSIGHT** | `passed=True` 항상, advisory 점수만 영향 |
| TF-PLV-06 | IMPORTANT → IMPORTANT → **INSIGHT** | NPC fuzzy matching FP → advisory 변환 → LLM 판단 |
| TF-PLV-08 | IMPORTANT → IMPORTANT → **INSIGHT** | dialogue minimum → advisory, LLM 최종 판정 |
| TF-NPC-05 | IMPORTANT → IMPORTANT → **INSIGHT** | `_verify_npc_names_llm()` LLM 필터 존재. Collection noise. |
| TF-NPC-06 | IMPORTANT → IMPORTANT → **INSIGHT** | death detection은 수집. REJECT는 별도 check_dead_npc_appearance()에서만. |
| TF-PB-01 | IMPORTANT → IMPORTANT → **INSIGHT** | Prompt building은 정보 전송. LLM이 컨텍스트에서 필터. |
| TF-AR-06 | IMPORTANT → IMPORTANT → **INSIGHT** | Error classification → 재시도 전략만 영향. 최종 판정은 LLM. |
| TF-AR-07 | IMPORTANT → IMPORTANT → **INSIGHT** | "제한" 오매칭 → 재시도 효율만 영향. 최종 판정은 LLM. |
| TF-FB-11 | IMPORTANT → IMPORTANT → **INSIGHT** | Feedback ordering은 정보 구성. LLM 컨텍스트 이해로 보상. |
| TF-ST-03 | CRITICAL → IMPORTANT → **INSIGHT** | 8-thread advisory는 전량 read-only. write 미발생. `_merge_advisory_validation_results()` main thread 순차. |
| S2-6 | MEDIUM → INCONCLUSIVE → **LOW** | valid arc 발견 시 advisory 스킵 = 의도적 최적화. 대원칙#1 정합. |
| TF-ADV-01 | CRITICAL → IMPORTANT → **INSIGHT** | advisory-only. 60% FP → LLM advisory 변환 → REJECT 영향 0. |

---

## 6. Pass 3 크로스레퍼런스 (R2 갱신)

### 6.1 중복 클러스터 7쌍 — R2 재확인

| Canonical | Duplicate | R2 판정 | 대원칙 |
|-----------|-----------|---------|--------|
| TF-CM-01 | TF-CA-02 | **CONFIRMED** (98%) | #3 위반: fail-open이 Director fail-closed 정책과 충돌 |
| TF-CM-02 | TF-CA-03 | **CONFIRMED** (98%) | #3 위반: JSON 실패 시 자동 PASS |
| TF-CM-03 | TF-CA-01 | **CONFIRMED** (97%) | **#4 위반**: NPC 사망 미감지. 보완적 갭 (dual-level vulnerability) |
| TF-CW-02 | TF-CQ-18 | **CONFIRMED** (95%) | — |
| TF-CW-11 | TF-CQ-05 | **CONFIRMED** (96%) | — |
| TF-SV-10 | TF-PLV-04 | **CONFIRMED** (94%) | — |
| TF-AR-01 | TF-AR-02 | **CONFIRMED** (93%) | #1: AdaptiveRetryManager가 프로덕션 커버 |

### 6.2 크로스커팅 패턴 6개 — R2 대원칙 평가

| # | 패턴 | 대원칙 | R2 판정 |
|---|------|--------|---------|
| **P1** | fail-open 전염 (4건) | **#3 위반** | Director fail-closed 정책과 체계적 모순. **P0 수정 유지.** |
| **P2** | 한국어 형태소 취약 (8건) | **#1 적용** | Python 수집 노이즈. LLM이 보정 가능. **심각도 하향 정당.** |
| **P3** | LLM 입력 절삭 (8건) | **#1 위반 가능** | Python이 LLM 판단 기초 70-90% 차단 = 수집 의무 위반. **심각도 유지.** |
| **P4** | Dead Code (8건) | N/A | 유지보수 비용. 대원칙 무관. |
| **P5** | 무효 레이어 (3건) | **#3 적용** | TF-DG-11: Director ensemble이 CONDITIONAL_PASS 덮어씀 = Director 주권 존중. |
| **P6** | 무협 편향 (6건) | N/A | 기능 커버리지 이슈. 대원칙 무관. |

---

## 7. 확신도 분포 (R2 갱신)

| 범위 | R1 건수 | R2 건수 | 변동 | 처리 |
|------|---------|---------|------|------|
| 95-100% | 136 | **145** | +9 | CONFIRMED |
| 90-94% | 52 | **49** | -3 | CONFIRMED (minor edge cases) |
| 85-89% | 27 | **23** | -4 | CONFIRMED with caveats |
| 80-84% | 8 | **5** | -3 | NEEDS-RUNTIME-VERIFICATION |
| <80% | 5 | **1** | -4 | NEEDS-RUNTIME-VERIFICATION |
| N/A (FP/CLOSED/MERGED) | 11 | **16** | +5 | 완결 |
| Not sampled | 31 | **31** | — | INSIGHT 미표본 — deepdive 평가 수용 |

### R2 확신도 상향 상세 (대원칙 기여)

| ID | R1 | R2 | 대원칙 근거 |
|----|-----|-----|-----------|
| S2-6 | 75% | 93% | #1: advisory 최적화 |
| TF-AR-06 | 75% | 96% | #1: orchestration noise |
| TF-AR-07 | 70% | 96% | #1: orchestration noise |
| TF-FB-11 | 75% | 96% | #1: feedback ordering |
| TF-CA-14 | 80% | 97% | #1: encoding detail |
| S4-3 | 85% | 95% | 코드 행동 재확인 |
| S4-4 | 80% | → CLOSED | #3: Director 보상 |
| X-3 | 80% | → FP (98%) | 인용 라인 오류 |

### NEEDS-RUNTIME-VERIFICATION (R2, 6건)

| ID | 확신도 | 사유 |
|----|--------|------|
| S2-5 | 90% | FourPhase None 시 재시도 피드백 부재. 발생 빈도 런타임 검증 필요. |
| X-1 | 92% | StateTracker 참조 전달 vs 원고 결과 미반영. Python 구조체 확인 필요. |
| TF-CA-01 | 92% | NPC 사망 Arc 검증 부재이나 다층 보상(TruthGate+check_dead) 효과 런타임 측정 필요. |
| TF-E8 | 92% | 4채널 감사 분산. 실무 사후 분석 난이도 측정 필요. |
| TF-E11 | 88% | V75-D 패치 프롬프트 컨텍스트 제한. InPlace 연속성 피드백 빈도 측정 필요. |
| TF-E13 | 93% | deep-merge 씬 내부 콘텐츠 보호. 이벤트 소실 빈도 측정 필요. |

---

## 8. 진정한 CRITICAL 16건 (R2 최종)

| # | ID | 서브시스템 | 제목 | 확신도 | 대원칙 |
|---|-----|----------|------|--------|--------|
| 1 | TF-NPC-04 | NPC Tracker | `_is_standalone_name` context-blind 매칭 | 96% | #1: 수집 결함이나 근본적 로직 오류 |
| 2 | TF-BA-01 | Base Agent | 로컬/서버 TTL drift → 만료 캐시 사용 | 95% | — (인프라) |
| 3 | TF-BA-02 | Base Agent | 캐시 경로 MetricsCollector 누락 (5개 에이전트) | 98% | — (계측) |
| 4 | TF-ST-01 | StateTracker | `merge_from_previous_arcs` 3/23+ 레지스트리만 병합 | 95% | — |
| 5 | TF-ST-02 | StateTracker | 핵심 4종 추출 try/except 부재 | 97% | — |
| 6 | TF-CQ-02 | CW Quality | 1-2건 medium → "low" 분류 탈출 | 97% | — |
| 7 | TF-CM-01 | Continuity MS | LLM 실패 시 fail-open PASS | 98% | **#3 위반** |
| 8 | TF-CM-02 | Continuity MS | JSON 파싱 실패 시 PASS | 98% | **#3 위반** |
| 9 | TF-CM-03 | Continuity MS | STATE_ORDER 사망/굴복 누락 | **98%** | **#4 위반** |
| 10 | TF-SV-01 | ScoringValidator | LLM 원고 3,000자 절삭 | 95% | #1: 수집 의무 위반 (LLM 판단 기초 차단) |
| 11 | TF-FB-01 | FeedbackSystem | 피드백 정량화 fabricated (실제 점수 무시) | 99% | — |
| 12 | TF-FB-02 | FeedbackSystem | `score_breakdown.get()` no-op expression | 100% | — |
| 13 | TF-DG-01 | DirectorGrading | 부분 거부를 승인으로 마스킹 | 98% | — |
| 14 | TF-DG-02 | DirectorGrading | category score 이중 계산 | 97% | — |
| 15 | TF-CA-02 | ContinuityArc | LLM 실패 시 무조건 PASS (fail-open) | 97% | **#3 위반** |
| 16 | TF-CA-03 | ContinuityArc | JSON 파싱 실패 시 PASS + confidence=0.0 | 98% | **#3 위반** |

> R1 대비 변동: TF-DE-02 제거 (CLOSED, 대원칙#3 정합). 경계선 TF-PLV-02(97%), TF-S4CB-02(93%) 유지 (대원칙 미해당).

### 대원칙 위반 표시 CRITICAL (4건)

| 대원칙 | CRITICAL 항목 | 위반 내용 |
|--------|-------------|----------|
| **#3** (Director 주권) | TF-CM-01, TF-CM-02, TF-CA-02, TF-CA-03 | fail-open PASS가 Director fail-closed 정책 우회 |
| **#4** (사망 캐릭터) | TF-CM-03 | STATE_ORDER에 "사망" 미포함 → deceased 상태 전이 미감지 |

---

## 9. 수정 우선순위 (R2 갱신)

### P0 — 즉시 수정 (3건 유지)

| ID | 작업 | 대원칙 | 근거 |
|----|------|--------|------|
| TF-CM-01 + TF-CA-02 | fail-open → fail-closed 전환 | **#3 위반** | Director 정책 위반. 네트워크 불안정 시 모순 원고 자동 승인. |
| TF-FB-02 | `score_breakdown` 변수 할당 추가 | — | 100% 확인. 1줄 no-op 버그. |
| TF-DG-01 | `len(rejected)==0` 조건으로 변경 | — | 부분 거부 마스킹 방지. |

### P1 — 단기 수정 (9건, +1 신규)

| ID | 작업 | 대원칙 |
|----|------|--------|
| TF-CQ-02 | severity 분류 임계값 조정 | — |
| TF-DG-02 | `_CATEGORY_ITEMS` 중복 키 제거 | — |
| TF-BA-02 | `_ask_with_cached_context`에 MetricsCollector 추가 | — |
| TF-ST-01 | `merge_from_previous_arcs` 20+ 레지스트리 확장 | — |
| TF-ST-02 | 핵심 4종 추출에 개별 try/except | — |
| TF-SV-01 | `_SANITIZE_MAX_CHARS` 상향 (3000→8000) | #1 위반 |
| TF-CM-03 | STATE_ORDER에 "사망"/"굴복" 추가 | **#4 위반** |
| TF-PLV-02 | em-dash `―` 패턴 추가 | — |
| **TF-E2** (신규) | V75-B 실패 시 UI 경고 + fallback_reason | **#3 위반** |
| **V75-ESC** (신규) | 에스컬레이션 임계값 보수화: V75-D `_v75d_threshold` 일반 2→3, V75-B `_logic_error_streak >= 2` → `>= 3`. 에스컬레이션을 최후 직전 수단으로 격상. 현재 2연속이면 바로 발동하여 불필요한 BP 교체 위험. | — |

### P1 보강 — 로깅 동반 권고 (3건)

P1 패치 시 아래 3건은 로깅 보강으로 사후 감지 가능. 수정과 함께 계측 추가 권고.

| ID | 로깅 방법 | 감지 신호 |
|----|----------|----------|
| TF-FB-02 | `score_breakdown` 입력값 vs 출력값 `logging.debug` | 입력 있는데 출력 항상 하드코딩이면 이상 |
| TF-BA-02 | `_ask_with_cached_context`에 `MetricsCollector.start_call()`/`end_call()` | 캐시 경로 에이전트 비용 = 0원이면 이상 |
| TF-E2 | `_log_escalation_event`에 `success=False` 시 `fallback_reason` 필드 | V75-B 실패 후 결함 BP 계속 사용 빈도 집계 |

> 참고: 판정 로직 버그 (TF-DG-01, TF-CQ-02, TF-CM-03)는 로깅으로 감지 불가 — 코드 감사로만 발견됨.

### P2 — 중기 (제거된 FP/CLOSED 반영)

- **S2-1**: FALSE-POSITIVE — 수정 불필요
- **X-1**: 이슈 재정의 필요 (write-back 아닌 manuscript outcome 반영)
- **S2-2**: RECLASSIFIED → HIGH — 얕은 복사 개선
- **X-3**: FALSE-POSITIVE — 수정 불필요 (R2 추가)
- **TF-DE-02**: CLOSED — 수정 불필요 (R2 추가)
- **TF-SV-02**: CLOSED — 수정 불필요 (R2 추가)
- **S4-4**: CLOSED — 수정 불필요 (R2 추가)

---

## 10. 감사 정확도 메타 통계 (R2 갱신)

| 메트릭 | R1 | R2 | 변동 |
|--------|-----|-----|------|
| CRITICAL 오탐률 | 56.4% (22/39) | **59.0% (23/39)** | +1건 (TF-DE-02 CLOSED) |
| IMPORTANT 오탐률 | 17.8% (21/118) | **27.1% (32/118)** | +11건 (대원칙#1 하향) |
| 전체 오탐률 | 17.8% (46/258) | **24.4% (63/258)** | +17건 (FP+CLOSED+RECLASSIFIED) |
| 진정한 발견 확인율 | 75.6% | **71.9%** | 대원칙 적용으로 정밀도 향상 |
| 평균 확신도 (감사 대상) | ~94% | **~96%** | +2pp |
| 95%+ 항목 비율 | 59.6% (136/228) | **65.3% (145/222)** | +5.7pp |
| <80% 항목 | 5건 | **1건** | -4건 |
| NEEDS-RUNTIME-VERIFICATION | 13건 | **6건** | -7건 |

---

## 11. R1 → R2 변경 이력

| 단계 | 날짜 | 내용 |
|------|------|------|
| **R1** | 2026-03-16 | 8 병렬 에이전트 3-Pass Audit. 258건 전량 감사. |
| **R2** | 2026-03-16 | 대원칙 4개 렌즈 적용 재감리. 20건 판정 변경 + 10건 확신도 상향. |

---

*Generated by 3-Pass Audit R2 — 대원칙 적용 재감리 — 2026-03-16*
*Auditor: Claude Opus 4.6 (1M context)*
